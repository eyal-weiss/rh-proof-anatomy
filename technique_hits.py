#!/usr/bin/env python3
"""Files and hits per timeline technique in the Lean archive (stdlib, multiprocessing).

Same clean-up as branch_scan.py: import lines and whole-word directory names are removed first,
so folder labels inside qualified names do not count. A cheap substring pre-filter skips most files.
  python3 technique_hits.py [--procs 5]   -> census_out/technique_hits.json
"""
import argparse, collections, csv, json, os, re, time
from multiprocessing import Pool

ROOT = "lean_src"
# key: (substring prefilter list, regex)
TECH = {
    "Parseval":              (["arseval"], r"[Pp]arseval"),
    "Gauss sums":            (["auss"], r"[Gg]auss_?[Ss]um"),
    "Cauchy-Schwarz":        (["auchy", "inner_mul_le_norm_mul_norm", "inner_mul_inner_self_le", "sum_mul_sq_le_sq_mul_sq"],
                              r"[Cc]auchy_?[Ss]chwarz|inner_mul_le_norm_mul_norm|inner_mul_inner_self_le|sum_mul_sq_le_sq_mul_sq"),
    "Theta functions":       (["heta"], r"jacobiTheta|[Tt]heta_?([Ff]unction|[Ss]eries|[Nn]ull|[Cc]onstant|[Cc]haracteristic)"),
    "Vandiver":              (["andiver"], r"Vandiver"),
    "Complex multiplication":(["omplex", "CM"], r"[Cc]omplex_?[Mm]ultiplication|IsCMField|CMType|IsCM(?![A-Za-z])"),
    "Triangle groups":       (["riangle"], r"[Tt]riangle_?[Gg]roup"),
    "Bertini":               (["ertini"], r"Bertini"),
    "Poincare series":       (["oincar"], r"[Pp]oincar[eé]_?[Ss]eries"),
    "von Mangoldt":          (["angoldt"], r"[Vv]on_?[Mm]angoldt"),
    "Hecke characters":      (["ecke", "ssen"], r"[Hh]ecke_?[Cc]har|IsHeckeChar|[Gg]r[oö]ssen"),
    "Weyl character/dimension": (["eyl"], r"[Ww]eyl_?([Cc]haracter|[Dd]im)|weylDim|WeylChar"),
    "Siegel auxiliary/Siegel lemma": (["iegel", "uxiliary"], r"[Ss]iegel_?s?_?[Ll]emma|[Aa]uxiliary_?([Ff]unction|[Pp]olynomial|[Dd]eterminant)"),
    "Siegel mass formula":   (["ass"], r"[Mm]ass_?[Ff]ormula|[Ss]iegel_?[Mm]ass|GenusMass"),
    "Behrend":               (["ehrend"], r"Behrend"),
    "Weil bound / RH for curves": (["eil", "asse"], r"[Ww]eil_?[Bb]ound|[Hh]asse_?[Ww]eil|[Ww]eil_?[Cc]onjecture"),
    "Chowla-Selberg":        (["howla"], r"Chowla"),
    "Explicit formula / Weil positivity": (["uinand", "xplicit", "ositiv"], r"Guinand|[Ee]xplicit_?[Ff]ormula|[Ww]eil_?[Pp]ositiv"),
    "Turan":                 (["Tur"], r"Tur[aá]n"),
    "Iwasawa theory":        (["wasawa"], r"[Ii]wasawa(?!_?[Dd]ecomp)"),
    "Mehta/Dyson":           (["ehta", "yson"], r"Mehta|Dyson"),
    "Weil representation":   (["eil", "chr", "scillator"], r"[Ww]eil_?[Rr]ep|[Ss]chr[oö]dinger|[Oo]scillator"),
    "Etale":                 (["tale"], r"[EeÉé]tale"),
    "Stepanov":              (["tepanov"], r"Stepanov"),
    "Lichtenbaum / K-theory":(["ichtenbaum", "heory", "uillen"], r"Lichtenbaum|K_?[Tt]heory|Quillen"),
    "Deligne":               (["eligne"], r"Deligne"),
    "Arakelov / Faltings height": (["rakelov", "altings"], r"Arakelov|Faltings"),
    "Howe duality / theta lifts": (["owe", "heta"], r"Howe|[Tt]heta_?[Cc]orrespond|[Tt]heta_?[Ll]ift"),
    "Katz / monodromy":      (["atz", "onodromy", "loosterman"], r"Katz|[Mm]onodromy|[Kk]loosterman"),
    "Seesaw":                (["aw", "udla", "allis"], r"[Ss]ee_?[Ss]aw|Kudla|Rallis"),
    "Kazhdan-Patterson / metaplectic": (["azhdan", "etaplectic"], r"Kazhdan_?Patterson|[Mm]etaplectic"),
    "Relative trace formula":(["elative", "rbital"], r"[Rr]elative_?[Tt]race|[Oo]rbital_?[Ii]ntegral"),
    "Arthur parameters":     (["rthur", "arameter"], r"Arthur|A_?[Pp]arameter"),
    "Gross-Prasad / GGP":    (["rasad", "GGP", "essel"], r"Gross_?Prasad|GGP|[Bb]essel_?[Pp]eriod"),
    "Bost":                  (["Bost"], r"Bost(?![a-z])"),
    "Whittaker":             (["hittaker"], r"[Ww]hittaker"),
    "Satake":                (["atake"], r"[Ss]atake"),
    "Jacquet-Shalika":       (["halika"], r"Jacquet_?Shalika|Shalika"),
    "Casselman-Wallach":     (["asselman"], r"Casselman"),
    "Langlands":             (["anglands"], r"Langlands"),
    "Siegel-Weil":           (["iegel"], r"[Ss]iegel_?Weil"),
    "Poitou-Tate":           (["oitou"], r"Poitou"),
    "Ferrero-Washington":    (["errero"], r"Ferrero"),
    "Kisin":                 (["isin"], r"Kisin"),
    "Rosati":                (["osati"], r"Rosati"),
    "Landherr":              (["andherr"], r"Landherr"),
    "Abelian schemes/varieties": (["belian"], r"[Aa]belian_?([Vv]ariet|[Ss]cheme)"),
    "Riemann zeta / L-functions": (["eta", "LSeries", "LFunction", "irichlet"], r"riemannZeta|LSeries|LFunction|[Dd]irichlet_?[Cc]haracter"),
}
RX = {k: re.compile(v[1]) for k, v in TECH.items()}
IMPORT_LINE = re.compile(r"(?m)^[ \t]*(?:(?:public|private|meta)[ \t]+)*import[ \t].*$")
CAPID = re.compile(r"(?<![\w'])[A-Z][A-Za-z0-9_']+")
with open("census_out/dirnames.txt") as _f:
    DIRS = frozenset(l.strip() for l in _f if l.strip())


def scan(path):
    with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as f:
        raw = f.read()
    cand = [k for k, (pre, _) in TECH.items() if any(p in raw for p in pre)]
    if not cand:
        return {}
    txt = CAPID.sub(lambda m: "" if m.group(0) in DIRS else m.group(0), IMPORT_LINE.sub("", raw))
    out = {}
    for k in cand:
        n = len(RX[k].findall(txt))
        if n: out[k] = n
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--procs", type=int, default=5); a = ap.parse_args()
    csv.field_size_limit(10**9)
    with open("census_out/files.csv") as f:
        paths = [r["path"] for r in csv.DictReader(f)]
    t0 = time.time(); files = collections.Counter(); hits = collections.Counter()
    with Pool(a.procs) as pool:
        for r in pool.imap_unordered(scan, paths, chunksize=512):
            for k, n in r.items(): files[k] += 1; hits[k] += n
    res = {k: {"files": files[k], "hits": hits[k]} for k in TECH}
    json.dump({"seconds": round(time.time() - t0, 1), "n_files": len(paths), "tech": res}, open("census_out/technique_hits.json", "w"), indent=1)
    print(f"{len(paths)} files in {time.time()-t0:.1f}s")
    for k in TECH: print(f"  {files[k]:7d} files {hits[k]:8d} hits  {k}")


if __name__ == "__main__":
    main()
