#!/usr/bin/env python3
"""Branch fingerprint of the Lean archive (stdlib only, multiprocessing).

For every .lean file listed in census_out/files.csv: drop `import` lines, count technique tokens,
and split the file's code lines among branches in proportion to its damped branch hits (sum of log(1+n) per token) (no double counting;
files with no branch hit go to "unattributed"). Aggregates per folder and overall.

  python3 branch_scan.py [--sample 0.02] [--procs 5]
Writes census_out/branch_scan.json and prints a compact summary.
"""
import argparse, collections, csv, json, math, os, random, re, sys, time
from multiprocessing import Pool

ROOT = "lean_src"
# (token id, branch or None for tracked-but-unassigned, regex). Order matters: specific before generic.
TOKENS = [
    ("iwasawa_decomp", "auto", r"[Ii]wasawa_?[Dd]ecomp"),
    ("theta_lift",     "auto", r"[Tt]heta_?[Ll]ift|[Tt]heta_?[Cc]orrespond|Howe"),
    ("weil_rep",       "auto", r"[Ww]eil_?[Rr]ep|[Ss]chr[oö]dinger|[Oo]scillator"),
    ("seesaw",         "auto", r"[Ss]ee_?[Ss]aw|Rallis|Kudla"),
    ("ggp_bessel",     "auto", r"Gross_?Prasad|GGP|[Bb]essel"),
    ("whittaker",      "auto", r"[Ww]hittaker"),
    ("trace_formula",  "auto", r"[Rr]elative_?[Tt]race|Jacquet|[Tt]race_?[Ff]ormula|[Oo]rbital_?[Ii]ntegral"),
    ("poincare_ser",   "auto", r"[Pp]oincar[eé]_?[Ss]eries"),
    ("metaplectic",    "auto", r"[Mm]etaplectic|Kazhdan|Patterson"),
    ("unitary_group",  "auto", r"[Uu]nitary_?[Gg]roup"),
    ("cusp",           "auto", r"[Cc]usp"),
    ("automorphic",    "auto", r"[Aa]utomorphic"),
    ("hecke",          "auto", r"[Hh]ecke"),
    ("satake",         "auto", r"[Ss]atake"),
    ("real_groups",    "auto", r"[Hh]arish_?[Cc]handra|[Dd]iscrete_?[Ss]eries|Casselman|[Ww]eyl|[Rr]oot_?[Ss]ystem|[Ll]ie_?[Aa]lgebra|[Cc]artan"),
    ("langlands",      "auto", r"Langlands|Arthur|Clozel|[Ss]iegel_?Weil"),
    ("zeta_L",         "ant",  r"riemannZeta|hurwitzZeta|[Zz]eta_?[Ff]unction|LSeries|LFunction|[Dd]irichlet_?[Cc]haracter"),
    ("von_mangoldt",   "ant",  r"[Vv]on_?[Mm]angoldt"),
    ("explicit_form",  "ant",  r"[Ee]xplicit_?[Ff]ormula|Guinand|[Ww]eil_?[Pp]ositiv|[Ww]eil_?[Cc]riterion"),
    ("stepanov",       "ant",  r"Stepanov|[Aa]uxiliary_?([Pp]olynomial|[Dd]eterminant)|[Ss]iegel_?s?_?[Ll]emma"),
    ("gauss_jacobi",   "ant",  r"[Gg]auss_?[Ss]um|[Jj]acobi_?[Ss]um"),
    ("turan",          "ant",  r"Tur[aá]n"),
    ("primes",         "ant",  r"[Pp]rime_?[Cc]ounting|Mertens|Perron|[Pp]rime_?[Nn]umber_?[Tt]heorem"),
    ("cm",             "cm",   r"[Cc]omplex_?[Mm]ultiplication|IsCMField|CMField|IsCM|isCM|[Ii]maginary_?[Qq]uadratic|CMType"),
    ("chowla_selberg", "cm",   r"Chowla"),
    ("arakelov",       "cm",   r"Arakelov|Bost|Faltings|[Mm]etri[sz]ed|[Hh]ermitian_?([Ll]ine|[Vv]ector)|[Aa]rithmetic_?[Dd]egree|[Hh]arder_?[Nn]arasimhan|N[eé]ron_?[Tt]ate"),
    ("theta_fn",       "cm",   r"jacobiTheta|[Tt]heta_?([Ff]unction|[Nn]ull|[Cc]onstant|[Cc]haracteristic)|[Rr]iemann_?[Tt]heta"),
    ("abelian_var",    "avag", r"[Aa]belian_?([Vv]ariet|[Ss]cheme)|[Jj]acobian(?!_?[Ss]um)|[Pp]olari[sz]|Rosati|[Ii]sogen|N[eé]ron|[Ll]ine_?[Bb]undle|[Ii]nvertible_?[Ss]heaf|[Aa]mple|[Ss]emi_?[Aa]belian|[Tt]ate_?([Cc]urve|[Mm]odule)|[Ee]lliptic_?[Cc]urve|[Tt]orsion_?[Pp]oint"),
    ("degen_moduli",   "avag", r"[Dd]egenerat|[Ss]emi_?[Ss]table|[Mm]oduli|[Uu]niformi[sz]|Mumford|Raynaud"),
    ("schemes",        "avag", r"Scheme|[Bb]low_?[Uu]p|[Ss]heaf|[Cc]oherent|[Pp]icard|Hodge|[Cc]rystalline|Fontaine|[Ww]ach|[Rr]esolution_?[Oo]f|[Ee]mbedded_?[Rr]esol|[Tt]oric|[Ss]mooth_?[Pp]roper|[Pp]rojective_?[Ss]pace"),
    ("iwasawa",        "iwa",  r"[Ii]wasawa|Z_?p_?[Ee]xtension|[Cc]yclotomic_?[Tt]ower|[Ll]ambda_?[Ii]nvariant|[Mm]u_?[Ii]nvariant"),
    ("vandiver",       "iwa",  r"Vandiver|Kummer|[Rr]egular_?[Pp]rime|[Bb]ernoulli"),
    ("k_theory",       "iwa",  r"Lichtenbaum|K_?[Tt]heory|Quillen|[Kk]_?[Gg]roup"),
    ("galois_cft",     "iwa",  r"[Gg]alois_?[Cc]ohomolog|[Gg]roup_?[Cc]ohomolog|[Cc]lass_?[Gg]roup|[Cc]lass_?[Nn]umber|Selmer|Poitou|[Cc]lass_?[Ff]ield|[Rr]eciprocity|[Rr]ay_?[Cc]lass|[Gg]alois_?[Rr]ep|[Ii]nertia|[Rr]amif|[Dd]ecomposition_?[Gg]roup"),
    ("mass_formula",   "qf",   r"[Mm]ass_?[Ff]ormula|[Ss]iegel_?[Mm]ass"),
    ("forms",          "qf",   r"[Qq]uadratic_?([Ff]orm|[Mm]ap)|[Hh]ermitian_?[Ff]orm|[Bb]ilinear_?[Ff]orm|[Ss]esquilinear|(?<![A-Za-z])gram|Gram|[Gg]enus|[Ss]pinor"),
    ("lattice",        "qf",   r"ZLattice|[Cc]ovolume|[Uu]nimodular|(?<![Cc]omplete)(?<![Ss]emi)(?<!Distrib)(?<![Ss]ub)(?<!Conditionally)[Ll]attice"),
    ("deligne_weil",   "agff", r"Deligne|[Ww]eil_?([Cc]onjecture|II)|Hasse"),
    ("katz_expsum",    "agff", r"Katz|[Ee]xponential_?[Ss]um|[Kk]loosterman|[Mm]onodromy|Gabber|[Cc]haracter_?[Ss]um"),
    ("etale",          "agff", r"[EeÉé]tale|Bertini|[Ll]efschetz|[Ll]_?[Aa]dic|ℓ_?[Aa]dic"),
    ("frob_fq",        "agff", r"[Ff]robenius|[Ff]inite_?[Ff]ield|GaloisField|[Ff]unction_?[Ff]ield"),
    ("fourier",        "four", r"[Ff]ourier|Parseval|Plancherel|[Pp]oisson_?[Ss]um|[Ss]chwartz|[Tt]est_?[Ff]unction|[Mm]ellin|[Cc]onvolution|[Hh]aar|[Cc]auchy_?[Ss]chwarz|inner_mul_le_norm_mul_norm|[Ss]obolev"),
    ("comb",           "comb", r"[Pp]igeonhole|exists_ne_map_eq_of_card_lt|Behrend|[Aa]rithmetic_?[Pp]rogression|Mehta|Dyson|[Rr]andom_?[Mm]atri|[Ss]elberg_?[Ii]ntegral|Ramsey|Szemer"),
    # tracked, not attributed
    ("theta_generic",  None,   r"[Tt]heta"),
    ("divisor",        None,   r"[Dd]ivisor"),
    ("integral_sign",  None,   r"∫"),
    ("adelic",         None,   r"[Aa]del(?:e|ic)"),
    ("period",         None,   r"[Pp]eriod"),
]
BIG = re.compile("|".join(f"(?P<{t}>{rx})" for t, _, rx in TOKENS))
BRANCH = {t: b for t, b, _ in TOKENS}
IMPORT_LINE = re.compile(r"(?m)^[ \t]*(?:(?:public|private|meta)[ \t]+)*import[ \t].*$")
IMPORT_NAME = re.compile(r"(?m)^[ \t]*(?:(?:public|private|meta)[ \t]+)*import[ \t]+(?:all[ \t]+)?([A-Za-z_«][\w.«»']*)")
CAPID = re.compile(r"(?<![\w'])[A-Z][A-Za-z0-9_']+")
# whole-word directory names are folder labels (namespaces in qualified names), not content: drop them
with open("census_out/dirnames.txt") as _f:
    DIRS = frozenset(l.strip() for l in _f if l.strip())
DIAG = False


def folder(path):
    p = path.split("/")[2:]          # drop lean/src
    if len(p) >= 4 and p[2] == "Proofs" and p[1] in ("AbelianVarietyTheory", "AutomorphicSpectrum"):
        return "/".join(p[:4]) if len(p) > 4 else "/".join(p[:3]) + "/(files)"
    return "/".join(p[:3]) if len(p) > 3 else "/".join(p[:-1]) + "/(files)"


def scan(job):
    path, cl = job
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except OSError:
        return path, cl, None, []
    imps = IMPORT_NAME.findall(raw)
    txt = IMPORT_LINE.sub("", raw)
    txt = CAPID.sub(lambda m: "" if m.group(0) in DIRS else m.group(0), txt)
    if DIAG:
        c = collections.Counter((m.lastgroup, m.group(0)) for m in BIG.finditer(txt))
        return path, cl, c, imps
    c = collections.Counter(m.lastgroup for m in BIG.finditer(txt))
    return path, cl, c, imps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=float, default=1.0)
    ap.add_argument("--procs", type=int, default=5)
    ap.add_argument("--out", default="census_out/branch_scan.json")
    ap.add_argument("--per-file", help="also write one JSON line per file: path, code lines, branch split, imports")
    ap.add_argument("--diag", action="store_true", help="print the literal strings behind each token (sample runs)")
    a = ap.parse_args()
    if a.diag:
        return diag(a)
    csv.field_size_limit(10**9)
    with open("census_out/files.csv") as f:
        jobs = [(r["path"], int(r["code_lines"])) for r in csv.DictReader(f)]
    if a.sample < 1:
        random.seed(0); jobs = random.sample(jobs, int(len(jobs) * a.sample))
    t0 = time.time()
    F = collections.defaultdict(lambda: {"files": 0, "code": 0, "attr": collections.Counter(), "tok": collections.Counter()})
    tot_tok = collections.Counter(); attr = collections.Counter(); missing = 0
    pf = open(a.per_file, "w") if a.per_file else None
    with Pool(a.procs) as pool:
        for path, cl, c, imps in pool.imap_unordered(scan, jobs, chunksize=256):
            if c is None: missing += 1; continue
            d = F[folder(path)]; d["files"] += 1; d["code"] += cl; d["tok"].update(c); tot_tok.update(c)
            bh = collections.Counter()
            for t, n in c.items():   # damped: one heavily repeated name cannot dominate a file
                if BRANCH[t]: bh[BRANCH[t]] += math.log1p(n)
            s = sum(bh.values())
            share = {b: cl * n / s for b, n in bh.items()} if s else {"unattributed": cl}
            for b, v in share.items(): d["attr"][b] += v; attr[b] += v
            if pf: pf.write(json.dumps({"p": path, "c": cl, "a": share, "i": imps}, ensure_ascii=False) + "\n")
    if pf: pf.close()
    dt = time.time() - t0
    out = {"seconds": round(dt, 1), "files": len(jobs), "missing": missing, "sample": a.sample,
           "branch_lines": dict(attr), "tokens": dict(tot_tok),
           "folders": {k: {"files": v["files"], "code": v["code"], "attr": dict(v["attr"]), "tok": dict(v["tok"])} for k, v in F.items()}}
    with open(a.out, "w") as f: json.dump(out, f)
    T = sum(attr.values())
    print(f"{len(jobs)} files in {dt:.1f}s ({a.procs} procs), missing {missing}")
    print("branch shares (all code lines, incl. unattributed):")
    for b, v in attr.most_common(): print(f"  {b:13s} {v/T*100:5.1f}%  {v:11.0f}")
    print("tokens:", ", ".join(f"{t} {n}" for t, n in tot_tok.most_common()))


def _diag_init():
    global DIAG
    DIAG = True


def diag(a):
    csv.field_size_limit(10**9)
    with open("census_out/files.csv") as f:
        jobs = [(r["path"], int(r["code_lines"])) for r in csv.DictReader(f)]
    random.seed(0); jobs = random.sample(jobs, int(len(jobs) * a.sample))
    lit = collections.Counter()
    with Pool(a.procs, initializer=_diag_init) as pool:
        for _, _, c, _ in pool.imap_unordered(scan, jobs, chunksize=256):
            if c: lit.update(c)
    by = collections.defaultdict(collections.Counter)
    for (t, s_), n in lit.items(): by[t][s_] += n
    for t, cc in sorted(by.items(), key=lambda x: -sum(x[1].values())):
        print(f"{t:15s} {sum(cc.values()):6d}  " + ", ".join(f"{s_} {n}" for s_, n in cc.most_common(7)))


if __name__ == "__main__":
    main()
