#!/usr/bin/env python3
"""Branch weights from census_out/branch_scan.json -> census_out/measured_weights.json.

Computes, as % of code lines:
  per_file_split_pct      matched files only (files with no branch name left out)
  folder_fill_pct         files with no branch name take the branch mix of their folder (the page's bars);
                          folders with no matched file fall back to their top-level folder's mix
  folder_majority_pct     each folder wholly to its dominant branch (a coarse check)
  infrastructure_view_pct_of_all_code   unmatched lines shown as their own "infra" bar
Run import_fill.py afterwards to add import_fill_pct (needs branch_scan.py --per-file output).
"""
import collections, json, os

BR = ["avag", "auto", "qf", "four", "cm", "agff", "iwa", "ant", "comb"]
F = json.load(open("census_out/branch_scan.json"))["folders"]
T = sum(v["code"] for v in F.values())
top = collections.defaultdict(collections.Counter)
for k, v in F.items():
    for b in BR: top[k.split("/")[0]][b] += v["attr"].get(b, 0)

raw, fill, maj = collections.Counter(), collections.Counter(), collections.Counter()
un = 0
for k, v in F.items():
    a = v["attr"]; att = {b: a.get(b, 0) for b in BR}; s = sum(att.values()); u = a.get("unattributed", 0); un += u
    mix = att if s else top[k.split("/")[0]]; ms = sum(mix.values())
    for b in BR:
        raw[b] += att[b]; fill[b] += att[b] + u * mix[b] / ms
    if s: maj[max(att, key=att.get)] += v["code"]
sr, sm = sum(raw.values()), sum(maj.values())

path = "census_out/measured_weights.json"
mw = json.load(open(path)) if os.path.exists(path) else {}
mw.update({
    "per_file_split_pct": {b: round(raw[b] / sr * 100, 1) for b in BR},
    "folder_majority_pct": {b: round(maj[b] / sm * 100, 1) for b in BR},
    "unattributed_pct": round(un / T * 100, 1),
    "total_code": T,
    "folder_fill_pct": {b: round(fill[b] / T * 100, 2) for b in BR},
    "infrastructure_view_pct_of_all_code": {**{b: round(raw[b] / T * 100, 2) for b in BR}, "infra": round(un / T * 100, 2)},
})
json.dump(mw, open(path, "w"), indent=1)
for key in ("folder_fill_pct", "per_file_split_pct", "folder_majority_pct"):
    print(key, mw[key])
print("infrastructure view", mw["infrastructure_view_pct_of_all_code"])
