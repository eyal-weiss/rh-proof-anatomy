# Step 3 notes (2026-11-20) — measured from census_out/files.csv

- Trust signals (text scan, comments/strings stripped): sorry 0, admit 0, axiom decl 0, opaque 0,
  native_decide 0, implemented_by 0, sorryAx 0. Not a verification.
- Size: 175,187 files, 15.53M code lines, 818,755 theorems, 234,220 defs. 136,003 files do bare `import Mathlib`.
- Main.lean proves riemannHypothesis := rhOfAll (from Supplements.Kernels.MainTheoremsAll), plus
  Dirichlet-L GRH variants. Statements.lean defines them with Mathlib's riemannZeta / DirichletCharacter.LFunction.
- Import closure from Main = all 175,187 files (so "in main closure" is uninformative).

## Code-line share by top folder (lean/src/...)
Development 71.1% | Formalism 18.0% | GroundTheory 6.2% | ReciprocityTheory 3.2% | CompanionTheory 1.1%
| PositivityTheory 0.3% | Lemmata 0.1%

## Depth 2 (top)
Development/AbelianVarietyTheory 47.2% (Proofs 92%, Definitions 5.6%, BlockTheory, PublishedTheorems, Counterexamples)
Development/AutomorphicArithmetic 10.6% (AutomorphicVarieties 48%, Foundations 23%, ThetaCorrespondence 10%)
Development/AutomorphicSpectrum 7.0%
Formalism/LocalToGlobal 5.3% (SiegelLatticeTheory 36%, lattices/forms throughout)
Development/WeilBound 4.8% (CoreStatements 54%, RepresentationTheoryGL 32%, ThetaLifts 14%)
Formalism/SharpRestriction 4.0% (GrowthBounds, LevelLetterCocycles, CuspSpanNormBounds)
GroundTheory/HeightsAndTheta 3.6% (Heights 98%)
Formalism/HermitianCurvature 2.6%
Formalism/PeriodIntegrals 2.5% (UnitaryGroupMassFormula 96%)
ReciprocityTheory/ReductiveGroups 2.3% (ArithmeticGeometry 58%, DiscreteSeries 38%)

## Keyword table problem
Old KEYWORDS has no abelian-variety entry; "Unitary groups / automorphic reps" regex matches 'automorphic'
anywhere (53k files) -> 47% Automorphic share is an artefact. Need folder-based mapping instead.

## Keyword scan redesign (branch_scan.py)
- Old census keyword shares were polluted by import lines and fully-qualified names containing folder labels
  (e.g. galois_cft 4846 -> 644 hits on a 2% sample once whole-word directory names are dropped).
- branch_scan.py: drops import lines + whole-word dir names, 47 tokens -> 9 branches (added `avag`:
  abelian varieties, schemes, moduli, degenerations, p-adic Hodge, resolution), per-file split of code lines
  by log(1+n)-damped hits; unattributed files reported. Full run: census_out/branch_scan.json.
- Ambiguity checks: "Slope" mostly project name SlopeTestRemainingChoices (dropped from Arakelov);
  "gram" fixed to not match 'diagram'; "Hecke" 64% from IndefiniteRowSideFullHecke; "Genus" mostly GenusMassVolumes.

## PublishedTheorems folders (1,070 files, ~92k code lines, 4,993 thm, 2,250 def, 92 struct)
60 names incl.: CasselmanWallach, ClozelPurity, FerreroWashington, GelfandKazhdanReal, JacquetShalikaBound,
JacquetShalikaRigidity, LanglandsClassification, PoitouTateDuality, SiegelWeil, Landherr, WeberRayClassFields,
RosatiTraces, NadelVanishingPairs, KisinCrTrivial, PotentialSemistability, SemiabelianTori, CyclicBaseChangeC,
SegmentRepresentations, RepNewform, CuspidalMultiplicityOne, TwistedTraceFormula, PolarizedGaloisRepresentations,
GlobalEulerCharacteristic, Hilbert, ThetaCharacteristics, PoincareDeRhamDuality, HeckeLAdicCharacters.
Candidate timeline years (standard literature): Weber 1897, Hilbert 90 1897, Rosati 1918, Landherr 1936,
Siegel-Weil 1965 (Siegel 1951), Poitou-Tate 1962, Grothendieck semistable reduction 1972, Mumford degenerations 1972,
Langlands classification 1973, Gelfand-Kazhdan 1975, Bernstein-Zelevinsky 1977, Ferrero-Washington 1979,
Jacquet-Shalika 1981, Arthur-Clozel 1989, Casselman-Wallach 1989, Clozel purity 1990, Nadel 1990, Kisin 2006.

## MEASURED branch weights (branch_scan.json, 1239 s, 5 procs) — saved also in census_out/measured_weights.json
unattributed 23.0% of code lines. Shares of attributed lines, per-file split | folder-majority (793 folders):
avag 24.4|35.7, auto 24.0|28.7, qf 23.6|27.1, four 10.3|4.9, cm 6.4|0.7, agff 5.0|1.0, iwa 4.9|1.4, ant 1.4|0.5, comb 0.03|0.0
Outline estimate for comparison: auto 35, ant 16, cm 13, iwa 10, qf 8, agff 8, four 6, comb 3, avag (not a branch) 0.
Signature outline techniques are rare by name: stepanov 2 hits, chowla 10, turan 43, k_theory 64, explicit_form 103,
poincare_ser 159, arakelov 239, mass_formula 254, metaplectic 414, von_mangoldt 757; seesaw 6093, ggp_bessel 9156.
Backup of estimate-only page: rh_anatomy_estimate_only.html

## The 23% unattributed lines (probe on 3,500-file sample + folder fill, 2026-11-20)
- 28% of files, 21.6% of lines in sample; smaller files (median 40 code lines vs 58 for attributed).
- 83% of their lines contain no tracked token at all; vocabulary is generic Mathlib: Finset, Function, Nat, Module,
  Set, Ideal, Matrix, Submodule, Algebra, LinearMap, Fintype, RingHom (general algebra & bookkeeping).
- Spread over all top folders roughly in proportion to code (Development 60%, Formalism 20%, GroundTheory 11%).
- Folder-sibling fill (each unmatched file takes its folder's attributed mix): covers 99.74% of code; shares move
  at most 0.6 points: avag 23.8, auto 24.3, qf 23.5, four 9.9, cm 6.3, agff 5.5, iwa 5.3, ant 1.4, comb 0.0.

## Option 2: import-graph fill (import_fill.py, 2026-11-20)
- Rescan with per-file output (branch_perfile.jsonl) reproduced branch totals exactly (diff 5e-10); 887 s on 5 procs.
- 753,569 project import edges; all 50,235 unmatched files (23.0% of lines) got a mix from importers, none needed fallback.
- Shares: auto 24.36, avag 23.93, qf 22.82, four 9.14, cm 6.21, iwa 6.16, agff 5.92, ant 1.42, comb 0.03
  (vs folder fill: max shift 0.83 points, iwa up, four down).
