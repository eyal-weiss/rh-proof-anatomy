#!/usr/bin/env python3
"""Per-folder view of census_out/branch_scan.json: code share, keyword branch mix, top tokens."""
import json, sys
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "census_out/branch_scan.json"))
n_top = int(sys.argv[2]) if len(sys.argv) > 2 else 45
F = d["folders"]; T = sum(v["code"] for v in F.values())
print(f"{len(F)} folders, {T} code lines, scan {d['seconds']}s, missing {d['missing']}")
cum = 0
for k, v in sorted(F.items(), key=lambda x: -x[1]["code"])[:n_top]:
    cum += v["code"]
    a = v["attr"]; s = sum(a.values()) or 1
    mix = " ".join(f"{b}{a[b]/s*100:.0f}" for b in sorted(a, key=lambda b: -a[b])[:4])
    tok = " ".join(t for t, _ in sorted(v["tok"].items(), key=lambda x: -x[1])[:6])
    print(f"{v['code']/T*100:5.1f}% cum{cum/T*100:5.1f}  {k}\n        mix: {mix}\n        tok: {tok}")
