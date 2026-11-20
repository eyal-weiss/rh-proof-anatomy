#!/usr/bin/env python3
"""Build social-media images from rh_anatomy.html's own data (single source of truth).

Outputs in social/: x_branches.png, x_timeline.png (1200x675 @2x), linkedin_p1..p5.png (1080x1350 @2x),
linkedin_carousel.pdf (5 pages, 1080x1350 px).  Run from the project directory:  python3 social/make_cards.py
"""
import json, os, re, subprocess, html

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = open(os.path.join(HERE, "..", "rh_anatomy.html"), encoding="utf-8").read()

def js_obj(name):  # simple {k:v,...} literal -> dict
    m = re.search(r"const %s = (\{.*?\});" % name, PAGE, re.S)
    return json.loads(re.sub(r"(\w+):", r'"\1":', m.group(1)))
LEAN = js_obj("LEAN"); FABLE = js_obj("FABLE"); FABLE_R = js_obj("FABLE_R")
T = json.loads("[" + PAGE.split("const T = [", 1)[1].split("\n];", 1)[0] + "]")

COL = {"auto": "#2a78d6", "ant": "#eb6834", "cm": "#1baf7a", "iwa": "#eda100", "qf": "#e87ba4",
       "agff": "#008300", "four": "#6250d6", "avag": "#e34948", "comb": "#7b7a75", "x": "#0b0b0b"}
NAME = {"auto": "Automorphic forms", "avag": "Abelian varieties & schemes", "qf": "Lattices & quadratic forms",
        "four": "Fourier analysis", "cm": "CM & Arakelov geometry", "agff": "Geometry over finite fields",
        "iwa": "Iwasawa & Galois cohomology", "ant": "Analytic number theory", "comb": "Combinatorics"}
SHORT = {"Guinand–Weil explicit formula, Weil positivity": "Guinand–Weil explicit formula",
         "Weyl character and dimension formulas": "Weyl character formula",
         "Siegel's auxiliary-function method": "Siegel's auxiliary functions",
         "Local–global classification of hermitian forms": "Landherr: hermitian forms",
         "RH for curves over finite fields": "RH for curves over 𝔽q",
         "Abelian varieties over any field": "Abstract abelian varieties",
         "Semistable reduction of abelian varieties": "Semistable reduction (SGA 7)",
         "Lichtenbaum's conjecture on K-groups": "Lichtenbaum's conjecture",
         "Monodromy bounds for exponential sums": "Katz: exponential sums",
         "Jacquet–Shalika bounds and rigidity": "Jacquet–Shalika",
         "Theta functions on covers of GL_r": "Kazhdan–Patterson covers",
         "Arthur parameters and Adams' conjecture": "Arthur parameters",
         "Casselman–Wallach globalization": "Casselman–Wallach",
         "Kisin modules for crystalline representations": "Kisin modules",
         "Ferrero–Washington theorem (μ = 0)": "Ferrero–Washington (μ = 0)",
         "The Riemann Hypothesis is posed": "Riemann poses the hypothesis",
         "Lean 4, the proof language": "Lean 4", "Multiplicity from iterated theta lifts": "The claimed new mechanism",
         "Ray class groups and class fields": "Weber's ray class fields", "Howe duality for theta lifts": "Howe duality",
         "Proof of the Weil conjectures": "Deligne: Weil conjectures", "von Mangoldt's explicit formula": "von Mangoldt's formula"}
ORDER = sorted(LEAN, key=lambda k: -LEAN[k])
esc = html.escape
FOOT = ("Unverified claim, announced 20 Nov 2026 by Levent Alpöge (Claude-assisted). Lean figures: text scan of "
        "175,187 files, not a build. Importance: AI-assisted estimate.")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap');
*{box-sizing:border-box;margin:0}
body{background:#fcfcfb;color:#0b0b0b;font-family:'IBM Plex Sans',system-ui,sans-serif}
.card{width:var(--w);height:var(--h);padding:var(--pad);display:flex;flex-direction:column;overflow:hidden;background:#fcfcfb;position:relative}
h1{font-family:'Source Serif 4',Georgia,serif;font-weight:600;letter-spacing:-.01em;line-height:1.12}
.sub{color:#52514e}
.foot{margin-top:auto;color:#7b7a75;font-size:var(--fs-foot);line-height:1.35;border-top:1px solid #dddcd6;padding-top:10px}
.key{display:flex;flex-wrap:wrap;gap:4px 18px;color:#52514e}
.key span{display:inline-flex;align-items:center;gap:6px}
.sw{display:inline-block;width:22px;height:11px;border-radius:0 3px 3px 0;background:#52514e}
.sw.est{background:transparent;border:1.5px solid #52514e;border-left:none}
.rngsw{display:inline-block;width:22px;height:9px;position:relative}
.rngsw:before{content:"";position:absolute;left:0;right:0;top:4px;border-top:1.5px solid #7b7a75}
.rngsw:after{content:"";position:absolute;inset:0;border-left:1.5px solid #7b7a75;border-right:1.5px solid #7b7a75}
.rows{display:flex;flex-direction:column;justify-content:space-around;flex:1}
.row{display:grid;grid-template-columns:var(--lab) 1fr;align-items:center;gap:0 18px}
.lab{font-weight:500;line-height:1.2}
.trk{display:flex;flex-direction:column;gap:4px}
.ln{display:flex;align-items:center;gap:8px;position:relative}
.fill{border-radius:0 4px 4px 0;min-width:2px}
.fill.est{background:transparent;border:1.5px solid;border-left:none}
.val{font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap}
.val.est{font-weight:400;color:#52514e}
.rng{position:absolute;top:50%;border-top:1.5px solid #7b7a75}
.rng:before,.rng:after{content:"";position:absolute;top:-5px;height:9px;border-left:1.5px solid #7b7a75}
.rng:before{left:0}.rng:after{right:0}
.eras{display:grid;gap:14px 26px}
.era h3{font-size:var(--fs-era);font-weight:600;color:#52514e;border-bottom:1px solid #dddcd6;padding-bottom:4px;margin-bottom:6px;letter-spacing:.02em}
.it{display:flex;align-items:center;gap:7px;line-height:var(--lh-it);font-size:var(--fs-it);white-space:nowrap}
.it b{font-weight:600;font-variant-numeric:tabular-nums;min-width:2.6em}
.d{width:10px;height:10px;border-radius:50%;flex:none}
.d.sq{border-radius:2px}
.d.dia{border-radius:0;transform:rotate(45deg);width:8px;height:8px;margin:0 1px}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.stat{background:#f3f3f0;border-radius:8px;padding:22px 24px}
.stat b{display:block;font-family:'Source Serif 4',Georgia,serif;font-size:54px;line-height:1.05}
.stat span{color:#52514e;font-size:22px}
.status{border-left:4px solid #0b0b0b;background:#f3f3f0;padding:16px 20px;color:#52514e}
ul.b{padding-left:26px;display:flex;flex-direction:column;gap:16px;color:#2b2b29}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:28px}
.cols h3{font-size:24px;font-weight:600;margin-bottom:12px}
.li{display:flex;align-items:center;gap:10px;font-size:21px;line-height:1.75}
.li b{font-variant-numeric:tabular-nums;min-width:3.2em;font-weight:600}
.li em{font-style:normal;color:#7b7a75;margin-left:auto;font-variant-numeric:tabular-nums}
.chips{display:flex;flex-wrap:wrap;gap:10px}
.chips span{background:#f3f3f0;border-radius:6px;padding:7px 12px;font-size:19px;color:#2b2b29}
"""

def doc(body, w, h, title="The mathematics inside the claimed RH proof"):
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>"

def marker(k, lean_only=False, faded=False):
    if k == "x": return "<i class='d dia' style='background:#0b0b0b'></i>"
    op = ";opacity:.35" if faded else ""
    return f"<i class='d{' sq' if lean_only else ''}' style='background:{COL[k]}{op}'></i>"

def branch_rows(fs_lab, fs_val, h_solid, h_est):
    mx = max(max(LEAN.values()), max(r[1] for r in FABLE_R.values()))
    wd = lambda v: v / mx * 82
    out = []
    for k in ORDER:
        lo, hi = FABLE_R[k]
        lv = LEAN[k]; fv = FABLE[k]
        lt = "<0.1%" if lv < 0.1 else (f"{lv:.1f}%" if lv < 10 else f"{lv:.0f}%")
        ft = f"{fv:.1f}%" if fv < 10 else f"{fv:.0f}%"
        out.append(f"""<div class='row'><div class='lab' style='font-size:{fs_lab}px'>{esc(NAME[k])}</div><div class='trk'>
<div class='ln'><div class='fill' style='background:{COL[k]};height:{h_solid}px;width:{wd(lv):.1f}%'></div><span class='val' style='font-size:{fs_val}px'>{lt}</span></div>
<div class='ln'><div class='fill est' style='border-color:{COL[k]};height:{h_est}px;width:{wd(fv):.1f}%'></div><span class='val est' style='font-size:{fs_val-1}px;margin-left:{max(0, wd(hi)-wd(fv)):.1f}%'>{ft}</span><i class='rng' style='left:{wd(lo):.1f}%;width:{wd(hi)-wd(lo):.1f}%'></i></div>
</div></div>""")
    return "".join(out)

def key_bars(fs):
    return (f"<div class='key' style='font-size:{fs}px'><span><i class='sw'></i>Share of the Lean code, measured</span>"
            f"<span><i class='sw est'></i>Importance in the argument, estimated</span><span><i class='rngsw'></i>Range of the estimate</span></div>")

def strip(width, height=46):
    x = lambda y: 10 + (y - 1790) / (2030 - 1790) * (width - 20)
    s = f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' style='display:block'>"
    s += f"<line x1='10' x2='{width-10}' y1='20' y2='20' stroke='#dddcd6'/>"
    for y in range(1800, 2030, 50):
        s += f"<line x1='{x(y):.1f}' x2='{x(y):.1f}' y1='12' y2='28' stroke='#dddcd6'/><text x='{x(y):.1f}' y='{height-2}' font-size='13' fill='#7b7a75' text-anchor='middle' font-family='IBM Plex Sans'>{y}</text>"
    for t in T:
        yr, k, lo = t[0], t[3], (t[7] if len(t) > 7 else 0)
        cx = x(yr)
        if k == "x": s += f"<rect x='{cx-4.5:.1f}' y='15.5' width='9' height='9' transform='rotate(45 {cx:.1f} 20)' fill='#0b0b0b' stroke='#fcfcfb' stroke-width='1.5'/>"
        elif lo: s += f"<rect x='{cx-5:.1f}' y='15' width='10' height='10' rx='2' fill='{COL[k]}' stroke='#fcfcfb' stroke-width='1.5'/>"
        else: s += f"<circle cx='{cx:.1f}' cy='20' r='5.5' fill='{COL[k]}' stroke='#fcfcfb' stroke-width='1.5'/>"
    return s + "</svg>"

ERAS = [("1799–1899", 0, 1900), ("1900–1949", 1900, 1950), ("1950–1979", 1950, 1980), ("1980–2026", 1980, 2100)]
def eras(cols):
    out = [f"<div class='eras' style='grid-template-columns:repeat({cols},1fr)'>"]
    for title, a, b in ERAS:
        items = [t for t in T if a <= t[0] < b]
        out.append(f"<div class='era'><h3>{title}</h3>")
        for t in items:
            lo = t[7] if len(t) > 7 else 0
            out.append(f"<div class='it'>{marker(t[3], lo)}<b>{t[0]}</b>{esc(SHORT.get(t[1], t[1]))}</div>")
        out.append("</div>")
    return "".join(out) + "</div>"

def key_branches(fs, extra=True):
    s = "".join(f"<span><i class='d' style='background:{COL[k]}'></i>{esc(NAME[k])}</span>" for k in ORDER)
    if extra:
        s += "<span><i class='d sq' style='background:#52514e'></i>Found only in the Lean code</span><span><i class='d dia' style='background:#0b0b0b'></i>Problem, medium, new idea</span>"
    return f"<div class='key' style='font-size:{fs}px'>{s}</div>"

def card(inner, w, h, pad, fs_foot):
    return f"<div class='card' style='--w:{w}px;--h:{h}px;--pad:{pad}px;--fs-foot:{fs_foot}px'>{inner}</div>"

n_tech = len([t for t in T if t[3] != "x"]); yrs = sorted(t[0] for t in T if t[3] != "x")
MED = yrs[len(yrs)//2] if len(yrs) % 2 else round((yrs[len(yrs)//2 - 1] + yrs[len(yrs)//2]) / 2)

# ---------------- X cards (1200 x 675) ----------------
x_branches = card(f"""<h1 style='font-size:34px'>Two ways to weigh the claimed proof of the Riemann Hypothesis</h1>
<p class='sub' style='font-size:17px;margin:6px 0 10px'>How much of the Lean code each branch of mathematics accounts for, and how much of the argument it carries</p>
{key_bars(14)}<div class='rows' style='--lab:280px;margin-top:6px'>{branch_rows(16, 15, 15, 9)}</div>
<p class='foot'>{esc(FOOT)}</p>""", 1200, 675, 40, 12.5)

x_timeline = card(f"""<h1 style='font-size:34px'>More than two centuries of mathematics in one claimed proof</h1>
<p class='sub' style='font-size:17px;margin:6px 0 8px'>{n_tech} established techniques it draws on, by year of first appearance: {yrs[0]} to {yrs[-1]}</p>
{strip(1120)}<div style='height:8px'></div>
<div style='--fs-era:14px;--fs-it:13px;--lh-it:1.58'>{eras(4)}</div>
<div style='margin-top:8px'>{key_branches(11.5)}</div>
<p class='foot' style='margin-top:6px'>{esc(FOOT)}</p>""", 1200, 675, 40, 12)

# ---------------- LinkedIn carousel (1080 x 1350) ----------------
p1 = card(f"""<h1 style='font-size:64px;margin-top:20px'>What does it take to claim a proof of the Riemann Hypothesis?</h1>
<p class='sub' style='font-size:28px;margin:22px 0 36px;line-height:1.35'>A map of the mathematics inside the Lean archive released with Levent Alpöge's Claude-assisted proof</p>
<div class='stats'><div class='stat'><b>175,187</b><span>Lean files</span></div><div class='stat'><b>15.5 M</b><span>lines of code</span></div>
<div class='stat'><b>9</b><span>branches of mathematics</span></div><div class='stat'><b>{n_tech}</b><span>techniques, from {yrs[0]} to {yrs[-1]}</span></div></div>
<p class='status' style='font-size:22px;margin-top:36px;line-height:1.4'><b style='color:#0b0b0b'>Not yet verified.</b> Announced 20 November 2026. A text scan finds no sorry, axiom or native_decide, but only a full build can check the proof.</p>
<p style='margin-top:auto;font-size:24px;color:#52514e;text-align:right'>Swipe →</p>""", 1080, 1350, 64, 18)

p2 = card(f"""<h1 style='font-size:46px'>Two ways to weigh it</h1>
<p class='sub' style='font-size:23px;margin:12px 0 18px;line-height:1.35'>Code volume and importance tell different stories. Foundations Lean's library lacks take lots of code; the decisive steps can be short.</p>
{key_bars(18)}<div class='rows' style='--lab:330px;margin-top:10px'>{branch_rows(22, 20, 20, 12)}</div>
<p class='foot'>Code share: names used in each file, measured. Importance: AI-assisted estimate (Claude Fable 5.2) from the author's outline and the Lean findings.</p>""", 1080, 1350, 56, 17)

p3 = card(f"""<h1 style='font-size:46px'>More than two centuries of tools</h1>
<p class='sub' style='font-size:23px;margin:12px 0 16px'>{n_tech} techniques by year of first appearance; median about {MED}</p>
{strip(968, 50)}<div style='height:14px'></div>
<div style='--fs-era:19px;--fs-it:17.5px;--lh-it:1.62'>{eras(2)}</div>
<div style='margin-top:14px'>{key_branches(15)}</div>""", 1080, 1350, 56, 17)

PUB = ["Casselman–Wallach", "Clozel's purity", "Ferrero–Washington", "Gelfand–Kazhdan (real groups)", "Jacquet–Shalika bound",
       "Jacquet–Shalika rigidity", "Langlands classification", "Poitou–Tate duality", "Siegel–Weil", "Landherr",
       "Weber's ray class fields", "Rosati traces", "Nadel vanishing", "Kisin modules", "Potential semistability",
       "Semiabelian tori", "Cyclic base change", "Segment representations", "Newforms", "Cuspidal multiplicity one",
       "Twisted trace formula", "Polarized Galois representations", "Global Euler characteristic", "Theta characteristics",
       "Poincaré–de Rham duality", "Hecke ℓ-adic characters"]
lean_only = [t for t in T if len(t) > 7 and t[7]]
rare = sorted([t for t in T if t[3] != "x" and not (len(t) > 7 and t[7]) and t[6] is not None and t[6] < 10], key=lambda t: t[6])
p4 = card(f"""<h1 style='font-size:46px'>What the code adds, and what it barely names</h1>
<p class='sub' style='font-size:22px;margin:12px 0 24px;line-height:1.35'>1,070 files sit in folders named after classical theorems, holding about 5,000 theorem statements. Names show what the code invokes, not whether each result is proved in full.</p>
<div class='cols'><div><h3>In the code, not in the note</h3>{''.join(f"<div class='li'>{marker(t[3], True)}<b>{t[0]}</b>{esc(SHORT.get(t[1], t[1]))}</div>" for t in lean_only)}</div>
<div><h3>In the note, rare in the code</h3>{''.join(f"<div class='li'>{marker(t[3])}<b>{t[0]}</b>{esc(SHORT.get(t[1], t[1]))}<em>{t[6]}</em></div>" for t in rare)}
<p style='font-size:17px;color:#7b7a75;margin-top:10px'>Right column: Lean files naming it, of 175,187</p></div></div>
<h3 style='font-size:24px;font-weight:600;margin:34px 0 14px'>All 26 published results the code's folders are named after</h3>
<div class='chips'>{''.join(f"<span>{esc(n)}</span>" for n in PUB)}</div>""", 1080, 1350, 56, 17)

p5 = card(f"""<h1 style='font-size:46px'>How this was made, and what it can't tell you</h1>
<ul class='b' style='font-size:27px;line-height:1.45;margin-top:40px;gap:26px'>
<li><b>Code shares</b> come from 47 name patterns counted in every file, after removing imports and folder labels. Helper files with generic names take their folder's mix; two alternative methods agree within a point on every branch.</li>
<li><b>Importance</b> is an AI-assisted judgment by Claude Fable 5.2, from the note's outline and 15 Lean files on the main-theorem chain. Ranges run 4 to 7 points either way.</li>
<li><b>This is not a verification.</b> Nothing was built. A clean text scan is necessary for a complete proof, not sufficient.</li>
<li><b>Years</b> mark first appearances; most tools kept developing for decades. A name in the code is evidence of use, not proof of it.</li>
<li><b>Going further</b> needs a full build: <code>#print axioms</code> on the main theorem, an independent kernel check, and a trace of which declarations the proof actually depends on.</li></ul>
<p style='margin-top:auto;font-size:26px;line-height:1.4'>Full charts, method and data: <b>linked in the post</b></p>
<p style='font-size:20px;color:#7b7a75;margin-top:10px'>Made with Claude Code</p>""", 1080, 1350, 64, 17)

CHROME = "google-chrome"
def shot(name, body, w, h):
    f = os.path.join(HERE, f"_{name}.html"); open(f, "w", encoding="utf-8").write(doc(body, w, h))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--force-device-scale-factor=2",
                    "--virtual-time-budget=6000", f"--window-size={w},{h}", f"--screenshot={os.path.join(HERE, name + '.png')}", "file://" + f],
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True)

shot("x_branches", x_branches, 1200, 675)
shot("x_timeline", x_timeline, 1200, 675)
for i, p in enumerate([p1, p2, p3, p4, p5], 1): shot(f"linkedin_p{i}", p, 1080, 1350)
pdf_html = os.path.join(HERE, "_carousel.html")
open(pdf_html, "w", encoding="utf-8").write(doc("<style>@page{size:1080px 1350px;margin:0}.card{break-after:page}</style>" + "".join([p1, p2, p3, p4, p5]), 1080, 1350))
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=6000", "--no-pdf-header-footer",
                f"--print-to-pdf={os.path.join(HERE, 'linkedin_carousel.pdf')}", "file://" + pdf_html], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True)
print("done:", sorted(f for f in os.listdir(HERE) if f.endswith((".png", ".pdf"))))
