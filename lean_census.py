#!/usr/bin/env python3
"""
lean_census.py - measure what a Lean 4 project is made of, without building it.

Pure Python 3.8+ standard library. No Lean, no LLM, no network unless --download.

  python3 lean_census.py --download            # fetch the 14 parts from alpo.ge, extract sources, analyse
  python3 lean_census.py --parts DIR           # analyse lean.tar.gz.part* already downloaded into DIR
  python3 lean_census.py --root PROJECT_DIR    # analyse an already extracted project

Outputs (in --out, default ./census_out):
  digest.md     small human/LLM-readable summary (bounded size)  <- send this back
  census.json   all aggregate numbers behind the digest           <- and this
  files.csv     one row per project file (can be large; keep locally)

What it measures
  1. Size and shape: files, lines, declarations per directory of the project.
  2. Trust signals: counts of `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by`.
  3. Imports: the project's internal import graph (what the main theorem actually reaches)
     and its external imports grouped by library area (Mathlib.NumberTheory.LSeries, ...).
  4. Namespace usage: which namespaces the code actually refers to. This still works when
     every file just says `import Mathlib`.
  5. Technique keywords: how often each named technique appears, grouped into branches.
  6. Dated references found in comments (lines that mention a year).
"""
import argparse, collections, csv, io, json, os, re, sys, tarfile, time, urllib.request

BASE_URL = "https://alpo.ge/lean.tar.gz.part%02d"
N_PARTS = 14
KEEP_EXT = (".lean", ".toml", ".json", ".md", ".txt")
KEEP_NAMES = ("lean-toolchain",)
MAX_KEEP_BYTES = 20 * 1024 * 1024  # skip any single non-.lean file above this

# technique -> (branch, regex). Edit freely, or pass --keywords my.json with the same shape.
KEYWORDS = {
    "Theta lifts / theta correspondence": ("Automorphic forms", r"theta[ _]?(lift|corresp)|thetaLift|Howe\b|dual pair"),
    "Weil representation":               ("Automorphic forms", r"Weil[ _]?rep|WeilRep|oscillator rep"),
    "Seesaw identity":                   ("Automorphic forms", r"see-?saw|Rallis|Kudla"),
    "Gan-Gross-Prasad / Bessel periods": ("Automorphic forms", r"Gross.?Prasad|\bGGP\b|Bessel[ _]?(period|model)|BesselPeriod"),
    "Relative trace formula":            ("Automorphic forms", r"relative[ _]trace|RelativeTrace|Jacquet"),
    "Poincare series":                   ("Automorphic forms", r"Poincar[eé][ _]?[Ss]eries|PoincareSeries"),
    "Covering groups (metaplectic)":     ("Automorphic forms", r"metaplectic|sixfold|six-fold|Kazhdan|Patterson|covering group"),
    "Unitary groups / automorphic reps": ("Automorphic forms", r"unitary group|UnitaryGroup|automorphic|Automorphic|Arthur\b|A-?parameter"),
    "Hecke characters":                  ("Automorphic forms", r"Hecke[ _]?[Cc]har|Gr[oö]ssenchar"),
    "Explicit formula / Weil positivity":("Analytic number theory", r"explicit[ _]formula|ExplicitFormula|Guinand|Weil[ _]?(positiv|criterion)"),
    "von Mangoldt sums":                 ("Analytic number theory", r"[vV]on ?[mM]angoldt|vonMangoldt|Chebyshev"),
    "Stepanov / auxiliary determinants": ("Analytic number theory", r"Stepanov|auxiliary (polynomial|determinant|function)|Siegel'?s? lemma"),
    "Zeta and L-functions":              ("Analytic number theory", r"riemannZeta|LSeries|LFunction|L-function|Dirichlet[ _]?[Cc]har"),
    "Gauss sums":                        ("Analytic number theory", r"[gG]auss[ _]?[sS]um"),
    "Turan power sums":                  ("Analytic number theory", r"Tur[aá]n"),
    "Complex multiplication":            ("CM & Arakelov", r"complex multiplication|\bCM\b|ComplexMultiplication|imaginary quadratic"),
    "Chowla-Selberg / periods":          ("CM & Arakelov", r"Chowla|Selberg|\bCM period|period lattice"),
    "Theta functions":                   ("CM & Arakelov", r"jacobiTheta|theta[ _]?(function|series|null)|ThetaFunction|ThetaSeries"),
    "Arakelov / Bost slopes":            ("CM & Arakelov", r"Arakelov|\bBost\b|slope inequal|hermitian (vector|line) bundle"),
    "Iwasawa towers":                    ("Iwasawa & K-theory", r"Iwasawa|Z_?p-?extension|cyclotomic tower"),
    "Vandiver":                          ("Iwasawa & K-theory", r"Vandiver|Kummer"),
    "K-theory / Lichtenbaum":            ("Iwasawa & K-theory", r"Lichtenbaum|K-?theory|KTheory|K-?group|Quillen"),
    "Galois cohomology / class groups":  ("Iwasawa & K-theory", r"Galois[ _]?cohomology|GaloisCohomology|ClassGroup|class group|Selmer"),
    "Siegel mass formula":               ("Lattices & forms", r"mass[ _]formula|MassFormula|Siegel[ _]?mass"),
    "Quadratic / hermitian forms":       ("Lattices & forms", r"QuadraticForm|quadratic form|hermitian form|HermitianForm"),
    "Lattices and covolumes":            ("Lattices & forms", r"covolume|ZLattice|Zlattice|Z-lattice|\bgenus of\b|integral structure"),
    "Weil / Deligne":                    ("Geometry over Fq", r"Deligne|Weil conjecture|WeilConjecture|Weil II"),
    "Katz / exponential sums":           ("Geometry over Fq", r"\bKatz\b|exponential sum|ExponentialSum|monodromy|Kloosterman|Gabber"),
    "Etale cohomology / Bertini":        ("Geometry over Fq", r"[eéEÉ]tale|Bertini|Frobenius|function field|FunctionField"),
    "Fourier / Parseval / Plancherel":   ("Fourier analysis", r"Fourier|Parseval|Plancherel|Poisson[ _]?summ"),
    "Cauchy-Schwarz / test functions":   ("Fourier analysis", r"Cauchy.?Schwarz|test[ _]function|TestFunction|SchwartzMap|Schwartz function"),
    "Pigeonhole / Behrend":              ("Combinatorics", r"pigeonhole|Pigeonhole|Behrend"),
    "Random matrices / Mehta":           ("Combinatorics", r"\bMehta\b|random matri|Dyson|Selberg integral"),
}

DECL = re.compile(
    r"(?m)^[ \t]*(?:@\[[^\]\n]*\][ \t\n]*)*(?:(?:private|protected|noncomputable|unsafe|partial|nonrec|public|scoped|local)[ \t]+)*"
    r"(theorem|lemma|def|abbrev|structure|class|inductive|instance|axiom|opaque)\b[ \t]*([^\s:({\[⦃]*)")
IMPORT = re.compile(r"(?m)^[ \t]*(?:(?:public|private|meta)[ \t]+)*import[ \t]+(?:all[ \t]+)?([A-Za-z_«][\w.«»']*)")
NAMESPACE = re.compile(r"(?m)^[ \t]*namespace[ \t]+([A-Za-z_][\w.']*)")
OPEN = re.compile(r"(?m)^[ \t]*open[ \t]+((?:[A-Z][\w.']*[ \t]*)+)")
DOTTED = re.compile(r"(?<![\w.])([A-Z][A-Za-z0-9_']*)\.[A-Za-z_]")
TRUST = {"sorry": re.compile(r"\bsorry\b"), "admit": re.compile(r"\badmit\b"),
         "native_decide": re.compile(r"\bnative_decide\b"), "implemented_by": re.compile(r"implemented_by"),
         "sorryAx": re.compile(r"\bsorryAx\b")}
YEAR = re.compile(r"(?<!\d)(1[6-9]\d\d|20[0-2]\d)(?!\d)")
CAPWORD = re.compile(r"\b[A-Z][a-zà-ÿ]{2,}")
SCAN = re.compile(r'/-|--|"')


def split_code_comments(text):
    """Return (code, comments). Handles nested /- -/ blocks, -- lines and string literals."""
    code, com, i, n = [], [], 0, len(text)
    while i < n:
        m = SCAN.search(text, i)
        if not m:
            code.append(text[i:]); break
        code.append(text[i:m.start()])
        tok = m.group()
        if tok == "--":
            j = text.find("\n", m.end()); j = n if j < 0 else j
            com.append(text[m.end():j]); com.append("\n"); i = j
        elif tok == '"':
            j = m.end()
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            code.append('""'); i = min(j + 1, n)
        else:
            depth, j = 1, m.end()
            while depth and j < n:
                a, b = text.find("/-", j), text.find("-/", j)
                if b < 0: j = n; break
                if 0 <= a < b: depth += 1; j = a + 2
                else: depth -= 1; j = b + 2
            body = text[m.end():max(m.end(), j - 2)]
            com.append(body); com.append("\n")
            code.append("\n" * body.count("\n")); i = j
    return "".join(code), "".join(com)


def module_title(text):
    m = re.search(r"/-!(.*?)-/", text, re.S)
    if not m: return ""
    for line in m.group(1).splitlines():
        line = line.strip().lstrip("#").strip()
        if line: return line[:110]
    return ""


# ---------------------------------------------------------------- download / extract
class Chain(io.RawIOBase):
    def __init__(self, paths): self.paths, self.f = list(paths), None
    def readable(self): return True
    def readinto(self, b):
        while True:
            if self.f is None:
                if not self.paths: return 0
                self.f = open(self.paths.pop(0), "rb")
            k = self.f.readinto(b)
            if k: return k
            self.f.close(); self.f = None


def download(dest, base=BASE_URL, n=N_PARTS):
    os.makedirs(dest, exist_ok=True)
    for i in range(1, n + 1):
        url = base % i; path = os.path.join(dest, os.path.basename(url))
        req = urllib.request.Request(url, headers={"User-Agent": "lean-census/1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            size = int(r.headers.get("Content-Length") or 0)
            if size and os.path.exists(path) and os.path.getsize(path) == size:
                print(f"  have {os.path.basename(path)}"); continue
            print(f"  get  {os.path.basename(path)}  {size/1e6:.0f} MB", flush=True)
            with open(path + ".tmp", "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk: break
                    f.write(chunk)
        os.replace(path + ".tmp", path)


def extract(parts_dir, dest):
    """Stream the concatenated parts; keep only source and config text. Never follows links."""
    parts = sorted(os.path.join(parts_dir, p) for p in os.listdir(parts_dir) if re.search(r"\.part\d+$", p))
    if not parts: sys.exit(f"no *.partNN files in {parts_dir}")
    os.makedirs(dest, exist_ok=True); root = os.path.realpath(dest); kept = skipped = 0
    with tarfile.open(fileobj=io.BufferedReader(Chain(parts), 1 << 20), mode="r|gz") as tf:
        for m in tf:
            name = m.name.replace("\\", "/")
            base = name.rsplit("/", 1)[-1]
            ok = m.isfile() and (base.endswith(KEEP_EXT) or base in KEEP_NAMES or base.startswith("lakefile"))
            if ok and not base.endswith(".lean") and m.size > MAX_KEEP_BYTES: ok = False
            if ok and "/.lake/build/" in "/" + name: ok = False
            target = os.path.realpath(os.path.join(root, name))
            if not ok or not target.startswith(root + os.sep):
                skipped += 1; continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            src = tf.extractfile(m)
            with open(target, "wb") as f:
                while True:
                    chunk = src.read(1 << 20)
                    if not chunk: break
                    f.write(chunk)
            kept += 1
            if kept % 2000 == 0: print(f"  extracted {kept} files", flush=True)
    print(f"  kept {kept} files, skipped {skipped} other entries")


# ---------------------------------------------------------------- analysis
def lean_files(root):
    for d, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [x for x in dirs if x not in (".git", "build") and not os.path.islink(os.path.join(d, x))]
        for f in files:
            if f.endswith(".lean"): yield os.path.join(d, f)


def is_dep(rel):
    p = "/" + rel.replace(os.sep, "/")
    return "/.lake/" in p or "/lake-packages/" in p


def area(mod, depth):
    return ".".join(mod.split(".")[:depth])


def analyse(root, out, kw, top_dirs=70):
    t0 = time.time()
    kwc = {k: re.compile(v[1]) for k, v in kw.items()}
    proj, deps = [], []
    for p in lean_files(root):
        (deps if is_dep(os.path.relpath(p, root)) else proj).append(p)
    if not proj: sys.exit(f"no project .lean files under {root}")
    print(f"  {len(proj)} project files, {len(deps)} dependency files", flush=True)

    # module name candidates: every path suffix, so imports resolve whatever the source dir is
    suffix = collections.defaultdict(list)
    def parts_of(p): return os.path.relpath(p, root)[:-5].replace(os.sep, "/").split("/")
    for idx, p in enumerate(proj):
        ps = parts_of(p)
        for k in range(len(ps)): suffix[".".join(ps[k:])].append(idx)

    rows, imports_of, ext_imports = [], [], []
    ns_defined, ns_used, opens = collections.Counter(), collections.Counter(), collections.Counter()
    year_lines, kw_files, kw_hits, kw_lines = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    axioms = []
    for idx, p in enumerate(proj):
        try: text = open(p, encoding="utf-8", errors="replace").read()
        except OSError: text = ""
        code, com = split_code_comments(text)
        imps = IMPORT.findall(code)
        internal, external = [], []
        for im in imps:
            im = im.replace("«", "").replace("»", "")
            cand = [j for j in suffix.get(im, []) if j != idx]
            (internal.append(cand[0]) if cand else external.append(im))
        imports_of.append(internal); ext_imports.append(external)
        kinds = collections.Counter()
        for kind, name in DECL.findall(code):
            kinds[kind] += 1
            if kind == "axiom" and len(axioms) < 400: axioms.append((os.path.relpath(p, root), name))
        trust = {k: len(r.findall(code)) for k, r in TRUST.items()}
        for nsn in NAMESPACE.findall(code): ns_defined[nsn.split(".")[0]] += 1
        for grp in OPEN.findall(code):
            for nsn in grp.split(): opens[nsn.split(".")[0]] += 1
        for r0 in DOTTED.findall(code): ns_used[r0] += 1
        loc = sum(1 for ln in code.splitlines() if ln.strip())
        hits = {}
        for k, r in kwc.items():
            c = len(r.findall(text))
            if c: hits[k] = c; kw_files[k] += 1; kw_hits[k] += c
        tot = sum(hits.values())
        for k, c in hits.items(): kw_lines[k] += loc * c / tot      # split the file's code among techniques
        for ln in com.splitlines():
            if YEAR.search(ln) and CAPWORD.search(ln) and not re.search(r"[Cc]opyright|Released under|Authors?:", ln):
                year_lines[" ".join(ln.split())[:170]] += 1
        ps = parts_of(p)
        rows.append(dict(path=os.path.relpath(p, root), module=".".join(ps), d1=ps[0] if len(ps) > 1 else "(root)",
                         d2="/".join(ps[:2]) if len(ps) > 2 else (ps[0] if len(ps) > 1 else "(root)"),
                         lines=text.count("\n") + 1, code_lines=loc, title=module_title(text),
                         theorems=kinds["theorem"] + kinds["lemma"], defs=kinds["def"] + kinds["abbrev"] + kinds["instance"],
                         structures=kinds["structure"] + kinds["class"] + kinds["inductive"], axioms=kinds["axiom"],
                         opaque=kinds["opaque"], n_int=len(internal), n_ext=len(external), **trust))
        if (idx + 1) % 2000 == 0: print(f"  parsed {idx+1}/{len(proj)}", flush=True)

    # internal graph: in-degree, roots, what the biggest root reaches
    n = len(proj); indeg = [0] * n
    for i in range(n):
        for j in set(imports_of[i]): indeg[j] += 1
    def closure(r):
        seen, st = {r}, [r]
        while st:
            for j in imports_of[st.pop()]:
                if j not in seen: seen.add(j); st.append(j)
        return seen
    roots = [i for i in range(n) if indeg[i] == 0]
    cl = sorted(((len(c), r, c) for r in roots for c in [closure(r)]), key=lambda t: -t[0])[:400] if len(roots) <= 5000 else []
    main = cl[0][2] if cl else set(range(n))
    for i, r in enumerate(rows): r["indeg"] = indeg[i]; r["in_main"] = int(i in main)

    def agg(key, only_main=False):
        d = collections.defaultdict(lambda: collections.Counter())
        for i, r in enumerate(rows):
            if only_main and i not in main: continue
            a = d[r[key]]; a["files"] += 1
            for f in ("lines", "code_lines", "theorems", "defs", "structures", "axioms", "opaque", "sorry", "admit", "native_decide", "implemented_by", "sorryAx", "in_main"):
                a[f] += r[f]
        return {k: dict(v) for k, v in sorted(d.items(), key=lambda kv: -kv[1]["code_lines"])}
    dirs1, dirs2 = agg("d1"), agg("d2")

    dir_edges = collections.Counter()
    for i in range(n):
        for j in set(imports_of[i]):
            if rows[i]["d2"] != rows[j]["d2"]: dir_edges[(rows[i]["d2"], rows[j]["d2"])] += 1

    # external imports, weighted by importing files (and by their code lines), main closure only
    ext = {d: collections.Counter() for d in (1, 2, 3)}; ext_loc = collections.Counter(); bare = collections.Counter()
    for i in main:
        mods = set(ext_imports[i])
        for d in (1, 2, 3):
            for a_ in set(area(m, d) for m in mods): ext[d][a_] += 1       # each file counts once per area
        for a_ in set(area(m, 2) for m in mods): ext_loc[a_] += rows[i]["code_lines"]
        for m in mods:
            if "." not in m: bare[m] += 1

    # optional: where does each namespace live in the dependencies? (lets us map usage to library areas)
    ns_home = collections.defaultdict(collections.Counter)
    for p in deps:
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        m = re.search(r"(?:\.lake/packages|lake-packages)/[^/]+/(.*)\.lean$", rel)
        if not m: continue
        mod = m.group(1).replace("/", ".")
        try: text = open(p, encoding="utf-8", errors="replace").read()
        except OSError: continue
        for nsn in set(x.split(".")[0] for x in NAMESPACE.findall(text)): ns_home[nsn][area(mod, 2)] += 1
    usage_area = collections.Counter(); ns_rows = []
    for nsn, c in ns_used.most_common():
        own = nsn in ns_defined and nsn not in ns_home
        home = ns_home[nsn].most_common(1)[0][0] if nsn in ns_home else ""
        if home and not own: usage_area[home] += c
        ns_rows.append(dict(namespace=nsn, refs=c, project_defined=own, library_home=home))

    branch_lines = collections.Counter(); branch_hits = collections.Counter()
    for k in kw: branch_lines[kw[k][0]] += kw_lines[k]; branch_hits[kw[k][0]] += kw_hits[k]
    tot_kw = sum(branch_lines.values()) or 1
    T = lambda f: sum(r[f] for r in rows)
    census = dict(
        generated=time.strftime("%Y-%m-%d %H:%M:%S"), root=os.path.abspath(root), seconds=round(time.time() - t0, 1),
        totals=dict(project_files=n, dependency_files=len(deps), lines=T("lines"), code_lines=T("code_lines"), theorems=T("theorems"),
                    defs=T("defs"), structures=T("structures"), axioms=T("axioms"), opaque=T("opaque"), sorry=T("sorry"), admit=T("admit"),
                    native_decide=T("native_decide"), implemented_by=T("implemented_by"), sorryAx=T("sorryAx"),
                    roots=len(roots), main_root=rows[cl[0][1]]["module"] if cl else "", main_closure_files=len(main),
                    main_closure_code_lines=sum(rows[i]["code_lines"] for i in main)),
        top_roots=[dict(module=rows[r]["module"], reaches=k) for k, r, _ in cl[:15]],
        axioms=[dict(file=f, name=nm) for f, nm in axioms],
        dirs_depth1=dirs1, dirs_depth2=dict(list(dirs2.items())[:400]),
        dir_edges=[dict(src=a, dst=b, imports=c) for (a, b), c in dir_edges.most_common(300)],
        external_imports=dict(by_library=dict(ext[1].most_common()), by_area=dict(ext[2].most_common(200)),
                              by_subarea=dict(ext[3].most_common(400)), code_lines_by_area=dict(ext_loc.most_common(200)),
                              bare_whole_library_imports=dict(bare)),
        namespaces=ns_rows[:400], opens=dict(opens.most_common(150)), usage_by_library_area=dict(usage_area.most_common(200)),
        keywords={k: dict(branch=kw[k][0], files=kw_files[k], hits=kw_hits[k], code_lines=round(kw_lines[k])) for k in kw},
        branches={b: dict(share=round(100 * v / tot_kw, 1), code_lines=round(v), hits=branch_hits[b]) for b, v in branch_lines.most_common()},
        dated_comment_lines=[dict(text=t, count=c) for t, c in year_lines.most_common(400)],
    )
    os.makedirs(out, exist_ok=True)
    json.dump(census, open(os.path.join(out, "census.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(out, "files.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    # ---- digest
    L = []; A = L.append; t = census["totals"]
    A(f"# Lean census digest\n\nroot: `{census['root']}` · generated {census['generated']} · {census['seconds']} s\n")
    A("## Totals\n"); A("| metric | value |\n|---|---|"); [A(f"| {k} | {v} |") for k, v in t.items()]
    A("\n## Trust signals\n")
    A(f"sorry {t['sorry']} · admit {t['admit']} · axiom declarations {t['axioms']} · opaque {t['opaque']} · native_decide {t['native_decide']} · implemented_by {t['implemented_by']} · sorryAx {t['sorryAx']}")
    A("(text counts in code with comments and strings removed; only a real build plus `#print axioms` is conclusive)\n")
    if axioms: A("Axioms declared: " + ", ".join(f"`{nm}` ({f})" for f, nm in axioms[:40]) + "\n")
    A("## Largest import roots (files nothing else imports)\n"); [A(f"- `{r['module']}` reaches {r['reaches']} of {n} files") for r in census["top_roots"][:8]]
    A("\n## Project directories, depth 2 (by code lines)\n"); A("| dir | files | code lines | thm | def | sorry | axiom | in main closure | sample titles |\n|---|---|---|---|---|---|---|---|---|")
    titles = collections.defaultdict(list)
    for r in sorted(rows, key=lambda r: -r["code_lines"]):
        if r["title"] and len(titles[r["d2"]]) < 4: titles[r["d2"]].append(r["title"][:60])
    for k, v in list(dirs2.items())[:top_dirs]:
        A(f"| {k} | {v['files']} | {v['code_lines']} | {v['theorems']} | {v['defs']} | {v['sorry']} | {v['axioms']} | {v['in_main']} | {' ; '.join(titles[k]).replace('|', '/')} |")
    if len(dirs2) > top_dirs: A(f"\n({len(dirs2) - top_dirs} smaller directories omitted; see census.json)")
    A("\n## Strongest directory-to-directory dependencies\n"); [A(f"- {e['src']} -> {e['dst']}: {e['imports']}") for e in census["dir_edges"][:40]]
    A("\n## External imports by area (files in the main closure that import it directly)\n")
    A("Whole-library imports such as bare `import Mathlib`: " + (", ".join(f"{k} x{v}" for k, v in bare.items()) or "none"))
    A("\n| area | importing files | their code lines |\n|---|---|---|"); [A(f"| {k} | {v} | {ext_loc[k]} |") for k, v in ext[2].most_common(60)]
    A("\n### Sub-areas\n"); A(", ".join(f"{k} {v}" for k, v in ext[3].most_common(120)))
    A("\n## Namespace usage (references like `Foo.bar` in code)\n")
    if usage_area:
        A("Mapped to the library area where the namespace is mostly declared:\n"); A(", ".join(f"{k} {v}" for k, v in usage_area.most_common(60)) + "\n")
    A("| namespace | refs | project-defined | library home |\n|---|---|---|---|"); [A(f"| {r['namespace']} | {r['refs']} | {'yes' if r['project_defined'] else ''} | {r['library_home']} |") for r in ns_rows[:150]]
    A("\n## Technique keywords\n"); A("| technique | branch | files | hits | attributed code lines |\n|---|---|---|---|---|")
    for k, v in sorted(census["keywords"].items(), key=lambda kv: -kv[1]["code_lines"]): A(f"| {k} | {v['branch']} | {v['files']} | {v['hits']} | {v['code_lines']} |")
    A("\n### Branch shares from keywords\n"); [A(f"- {b}: {v['share']}% ({v['code_lines']} code lines, {v['hits']} hits)") for b, v in census["branches"].items()]
    A("\n## Comment lines that mention a year (most repeated first)\n"); [A(f"- x{d['count']}: {d['text']}") for d in census["dated_comment_lines"][:150]]
    open(os.path.join(out, "digest.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"  wrote {out}/digest.md ({os.path.getsize(os.path.join(out, 'digest.md'))//1024} KB), census.json, files.csv in {census['seconds']} s")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--download", action="store_true", help="download the 14 archive parts into --parts first")
    ap.add_argument("--parts", help="directory holding lean.tar.gz.partNN (default ./lean_parts with --download)")
    ap.add_argument("--root", help="extracted project directory (default ./lean_src)")
    ap.add_argument("--out", default="census_out")
    ap.add_argument("--keywords", help="JSON file {technique: [branch, regex]} replacing the built-in table")
    ap.add_argument("--base-url", default=BASE_URL, help=argparse.SUPPRESS)
    ap.add_argument("--n-parts", type=int, default=N_PARTS, help=argparse.SUPPRESS)
    a = ap.parse_args()
    kw = KEYWORDS
    if a.keywords: kw = {k: tuple(v) for k, v in json.load(open(a.keywords, encoding="utf-8")).items()}
    root = a.root or "lean_src"
    if a.download or a.parts:
        parts = a.parts or "lean_parts"
        if a.download: print("downloading"); download(parts, a.base_url, a.n_parts)
        print("extracting source files"); extract(parts, root)
    elif not a.root:
        ap.error("give --download, --parts DIR or --root DIR")
    print("analysing"); analyse(root, a.out, kw)


if __name__ == "__main__":
    main()
