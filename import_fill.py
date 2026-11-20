#!/usr/bin/env python3
"""Option 2: give each file with no branch-specific name the average branch mix of the files that import it.

Input: census_out/branch_perfile.jsonl (from branch_scan.py --per-file) and census_out/branch_scan.json (folder mixes
for the fallback). Files are processed top-down through the import DAG (Kahn's algorithm on importer -> imported),
so every importer has its mix before the files it imports. Matched files keep their own mix; unmatched files take
the unweighted mean of their importers' mixes; files with no importer that has a mix fall back to their folder mix.
  python3 import_fill.py   -> prints shares, updates census_out/measured_weights.json ("import_fill_pct")
"""
import collections, json

BR = ["avag", "auto", "qf", "four", "cm", "agff", "iwa", "ant", "comb"]
rows = {}
with open("census_out/branch_perfile.jsonl") as f:
    for line in f:
        r = json.loads(line); rows[r["p"]] = r
mod2path = lambda m: "lean/src/" + m.replace(".", "/") + ".lean"

imports = {p: [g for g in (mod2path(m) for m in r["i"]) if g in rows and g != p] for p, r in rows.items()}
importers = collections.defaultdict(list)
for p, gs in imports.items():
    for g in gs: importers[g].append(p)

# folder fallback mixes (same folder keys as branch_scan.folder)
import branch_scan as bs
F = json.load(open("census_out/branch_scan.json"))["folders"]
top = collections.defaultdict(collections.Counter)
for k, v in F.items():
    for b in BR: top[k.split("/")[0]][b] += v["attr"].get(b, 0)
def norm(d):
    s = sum(d.get(b, 0) for b in BR)
    return {b: d.get(b, 0) / s for b in BR} if s else None
def folder_mix(p):
    k = bs.folder(p)
    return norm(F[k]["attr"]) if k in F and norm(F[k]["attr"]) else norm(top[k.split("/")[0]])

indeg = {p: len(importers[p]) for p in rows}
queue = collections.deque(p for p, n in indeg.items() if n == 0)
mix = {}; how = collections.Counter(); how_lines = collections.Counter()
while queue:
    p = queue.popleft(); r = rows[p]
    own = norm(r["a"])
    if own: mix[p] = own; how["matched"] += 1; how_lines["matched"] += r["c"]
    else:
        ms = [mix[q] for q in importers[p] if mix.get(q)]
        if ms: mix[p] = {b: sum(m[b] for m in ms) / len(ms) for b in BR}; how["importers"] += 1; how_lines["importers"] += r["c"]
        else: mix[p] = folder_mix(p); how["folder"] += 1; how_lines["folder"] += r["c"]
    for g in imports[p]:
        indeg[g] -= 1
        if indeg[g] == 0: queue.append(g)
left = [p for p in rows if p not in mix]          # only if the import graph had a cycle
for p in left:
    mix[p] = norm(rows[p]["a"]) or folder_mix(p); how["cycle-fallback"] += 1; how_lines["cycle-fallback"] += rows[p]["c"]

T = sum(r["c"] for r in rows.values())
tot = collections.Counter()
for p, r in rows.items():
    for b in BR: tot[b] += r["c"] * mix[p][b]
pct = {b: round(tot[b] / T * 100, 2) for b in BR}
edges = sum(len(v) for v in imports.values())
print(f"{len(rows)} files, {edges} project import edges, {T} code lines")
print("how each file got its mix (files / share of code lines):",
      ", ".join(f"{k} {how[k]} / {how_lines[k]/T*100:.1f}%" for k in how))
mw = json.load(open("census_out/measured_weights.json"))
print("branch   import fill   folder fill")
for b in sorted(BR, key=lambda b: -pct[b]): print(f"  {b:5s} {pct[b]:6.2f}%   {mw['folder_fill_pct'][b]:6.2f}%")
mw["import_fill_pct"] = pct
mw["import_fill_how_lines_pct"] = {k: round(v / T * 100, 2) for k, v in how_lines.items()}
json.dump(mw, open("census_out/measured_weights.json", "w"), indent=1)
