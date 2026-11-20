# Fable 5.2 re-estimate of perceived-importance weights (2026-11-20; brief: census_out/fable_brief.md)

Weights (sum 100), ranges:
auto 35.6 [28,42] · qf 12.6 [8,18] · iwa 12.0 [8,16] · ant 10.9 [7,16] · cm 9.9 [6,13] · four 6.2 [4,10] ·
avag 6.1 [3,12] · agff 5.1 [3,8] · comb 1.6 [0.5,3]
vs earlier outline estimate: auto 35.2, ant 16.2, cm 12.6, iwa 10.5, qf 8.3, agff 7.6, four 6.4, comb 3.1, avag 0.

Step changes (total step weight 21 -> 24.25):
1 weight 1->0.5 (Stepanov 0 files; template). 2 cm1 -> cm.6 avag.4 (cm_abelian_inputs_from_literature: deformation,
Serre-Tate, dual abelian scheme, Gauss-Manin). 3 + four .1 (footnote 3: iterated Parseval, Gauss sums).
4 weight 2->1.5; ant.6 four.2 auto.2 (determinant "natively automorphic"; top level phrased as divisibility links).
5 ant.4 agff.3 four.2 comb.1 (vonMangoldtClassSum inside LinkG). 8 auto.85 qf.15 (definite unitary groups, hermitian
lattice genera; ThetaPairLifts on main chain). 9 weight 1->1.5; qf.45 auto.3 cm.25 (GenusMassAt, MassRatioUnderVolume,
ClassNumberFormula₂ hypotheses of TopShape). 10 weight 1->1.5; qf.45 auto.3 cm.25 (LinkDIV central). 11 iwa.85 comb.15
(zeroFreeOn_of_tiedWin_cyc over a cyclotomic tower). 13 weight .5->1; qf.4 cm.4 avag.2 (Harder-Narasimhan height map in
LinkDIV; likely where Bost enters). 16 auto.6 four.4 (LinkS near-orthogonality). 17 weight 1->1.5 (LinkN, Sha sums,
hypothesis of plugAll). 19 weight .5->.25. NEW 21 "automorphic window" VWin, weight 2.5: auto.45 avag.35 iwa.1 cm.1
(local Langlands GL_n: Bernstein-Zelevinsky, Moy-Prasad; Jacquet-Shalika, base change, Clozel purity; Caraiani
local-global; p-adic Hodge: de Rham => pst, Bhatt-Scholze, Bloch-Kato; Artin reciprocity, Deligne-Ribet).
Unchanged: 6, 7, 12 (BesselId in LinkDIV confirms 12), 14, 15, 18.

Main-chain structure it found: final theorem plugAll; inputs LinkS, LinkN, LinkDIV, LinkG, LinkMu, VWin; TopShape
hypotheses (genus mass, class number formula, volume ratios, lattice slopes). Opaque identifiers (D7, SizeData₂, what₂).
Unsettled: steps 3-7 invisible (may be superseded by the 15 Nov chain) -> drives ant/agff ranges; agff/four/comb moves
are dilution only; dependency unverified; exceeded 200-line cap on one file (208 import lines + ~120 body lines).

Its folder-name critique, checked by us: cited files (MetaplecticRepresentationHolds, HoweDualityRealHolds,
GlobalArtinReciprocityHolds, LocalLanglandsOfLiterature...) are attributed by CONTENT (auto / iwa), not by folder.
AbelianVarietyTheory folder content mix: avag 24, qf 21, auto 18, none 17, cm 6, four 5. 61% of avag lines lie in that
folder; 47% of auto lines do too. So the measured shares are not inflated by folder names; the critique applies to
reading folder names (and partly to the folder-majority check).
