# Brief: re-estimate the perceived-importance weights of the claimed RH proof

## Goal
Levent Alpöge announced on 2026-11-20 a Claude-assisted proof of the Riemann Hypothesis (unverified; nobody outside
has checked it). We are building a crude, first-order map of which branches of mathematics the proof draws on, and
how important each is *to the argument*. An earlier estimate was made from the note's 20-step outline only. You now
get measurements from a text scan of the released Lean archive that the earlier estimate did not have. Re-estimate
the importance weights in light of them.

Keep two things apart:
- **Importance in the argument**: how much of the logical weight of the proof each branch carries. This is what you estimate.
- **Formalization volume**: how many Lean lines each branch takes. This is what was measured. Foundations Mathlib lacks
  (abelian schemes, hermitian lattices) need lots of code even if they play a supporting role; the RH-specific argument
  on top may be short. Volume is evidence about importance, not a substitute for it.

## Sources you may use
- The note: https://alpo.ge/remark.pdf (four pages; the 20-step outline below paraphrases it).
- The extracted Lean archive, read-only, at `lean_src/lean/src/`.
  Hard cap: at most 15 tool calls in total, and read at most 15 Lean files, each only up to 200 lines. Do not run scans
  over the whole tree (it is 175,187 files, 1.4 GB). Good targets: the main-theorem chain below.
- Do not edit or create any files.

## The outline and the earlier estimate (step: paraphrase · weight · branch split)
1. Stepanov's auxiliary determinant, the template from function fields · 1 · ant .5, agff .5
2. A derivation vanishes mod p on a CM curve; p-divisibility of theta derivatives over the period · 1 · cm 1
3. The quadric qN = Mk + R, and automorphy of μ through thetas on a sixfold cover of GL₅ · 2 (core) · auto .5, agff .25, cm .25
4. Positivity W(1_S) ≥ 0 from a determinant: Stepanov with multiplicity one · 2 (core) · ant .75, four .25
5. Switch to a smoothed von Mangoldt sum; sign from Guinand–Weil, size from Katz-style bounds · 1 · ant .3, agff .4, four .15, comb .15
6. Positivity for a test function concentrated near zero · 1 · ant .6, four .4
7. Determinants whose entries are Gan–Gross–Prasad periods · 1 · auto .8, ant .2
8. Iterated theta lifts U(X₀) → … → U(X_m) with m near √X, to win multiplicity m · 2 (core) · auto 1
9. Norms and levels of the lifts; cancelling the terms of order m · 1 · cm .35, qf .35, auto .3
10. Lower bound on the divisibility of the m-fold lift · 1 · qf .4, cm .3, auto .3
11. An Iwasawa tower standing in for pigeonholing over 𝔽qⁿ/𝔽q · 1 · iwa .8, comb .2
12. Seesaw identity: the period of the iterated lift is a Bessel period · 1 · auto 1
13. Bost's slope inequality (the note does not say where it enters) · 0.5 · cm 1
14. Cost of each lift; move the constant to a function field or twist it away · 1 · auto .5, ant .3, agff .2
15. An integral structure glued across Hecke characters · 1 · qf .5, auto .3, iwa .2
16. Relative trace formula; Cauchy–Schwarz down to the norm of a Poincaré series · 1 · auto .7, four .3
17. A weak form of Vandiver's conjecture for classes that twisting cannot kill · 1 · iwa 1
18. Covolumes, index of the theta series, congruences between lifts and forms · 1 · qf .5, auto .5
19. Precise choice of the tower using Behrend (the note expects this to be removable) · 0.5 · comb .6, iwa .4
20. Conclusion: the Generalized Riemann Hypothesis · 0

Earlier estimate, branch totals: auto 35.2%, ant 16.2%, cm 12.6%, iwa 10.5%, qf 8.3%, agff 7.6%, four 6.4%, comb 3.1%.
Branch keys: auto = automorphic forms & representation theory; ant = analytic number theory; cm = CM curves, periods
& Arakelov geometry; iwa = Iwasawa theory, Galois cohomology & K-theory; qf = quadratic forms, lattices & integral
structures; agff = algebraic geometry over finite fields; four = Fourier & harmonic analysis; comb = combinatorics &
random matrix theory; avag = abelian varieties, schemes & arithmetic geometry (new; not in the earlier estimate).

## New measurements from the Lean archive (text scan, not a build)
- Size: 175,187 files, 15.5M code lines, 818,755 theorem declarations, 234,220 definitions. Trust signals (text
  counts, comments and strings removed): 0 sorry, 0 admit, 0 axiom declarations, 0 opaque, 0 native_decide. Every
  file is reachable by imports from Main, so the scan cannot tell which code the final theorem actually depends on.
- Main-theorem chain: `Main.lean` proves `riemannHypothesis := rhOfAll` and Dirichlet-L versions, stated with Mathlib's
  `riemannZeta` and `DirichletCharacter.LFunction` (in `Statements.lean`). `Supplements/Kernels/MainTheorems.lean`:
  `allChi : UpperTheory.EveryCharacter := UpperTheory.FinalTheorems.everyCharacter`; `rhOfAll := Formalism.VW.rh_of_every allChi`.
  It imports `Formalism.GammaFactorNonvanishing.CritLine`, `Development.AutomorphicArithmetic.CharacterBoxes.ClaimStrip`
  and `…CharacterBoxes.MainConclusion`. `MainTheoremsAll`/`MainTheoremsCritical` also import
  `Development.AutomorphicArithmetic.AutomorphicVarieties.SmallClassNumbers.{CorGKOf, ClassNumberThree, LenEqZeroIff, OnePoint}`.
- Code-line share by top folder: Development 71.1%, Formalism 18.0%, GroundTheory 6.2%, ReciprocityTheory 3.2%,
  CompanionTheory 1.1%, PositivityTheory 0.3%. Largest subfolders: Development/AbelianVarietyTheory 47.2% (its Proofs/
  DivisorProofs alone 16.7%), Development/AutomorphicArithmetic 10.6%, Development/AutomorphicSpectrum 7.0%,
  Formalism/LocalToGlobal 5.3% (SiegelLatticeTheory), Development/WeilBound 4.8% (CoreStatements, RepresentationTheoryGL,
  ThetaLifts), Formalism/SharpRestriction 4.0%, GroundTheory/HeightsAndTheta 3.6%, Formalism/HermitianCurvature 2.6%,
  Formalism/PeriodIntegrals 2.5% (UnitaryGroupMassFormula).
- Branch shares of code lines (47 name patterns; per-file split, damped counts):
  folder fill (files with no branch name take their folder's mix; shown on the page): auto 24.3, avag 23.8, qf 23.5,
  four 9.9, cm 6.3, agff 5.5, iwa 5.3, ant 1.4, comb 0.04.
  matched files only: avag 24.4, auto 24.0, qf 23.6, four 10.3, cm 6.4, agff 5.0, iwa 4.9, ant 1.4, comb 0.03.
  import fill (unmatched files take the mix of their importers): auto 24.4, avag 23.9, qf 22.8, four 9.1, cm 6.2,
  iwa 6.2, agff 5.9, ant 1.4, comb 0.03.
  folder-majority (each of 793 folders wholly to its dominant branch): avag 35.7, auto 28.7, qf 27.1, four 4.9, cm 0.7,
  agff 1.0, iwa 1.4, ant 0.5, comb 0.
  Infrastructure: 23% of code lines sit in small helper files with no branch-specific name (generic Mathlib vocabulary:
  Finset, Nat, Module, Ideal, Matrix).
- How often outline techniques are named (files of 175,187): Stepanov 0, Vandiver 0, Lichtenbaum/K-theory 0, Bost 0,
  Mehta/Dyson 0, triangle groups 0, Siegel's lemma/auxiliary functions 2, Behrend 2, Weil bound/RH for curves 2
  (but a 0.75M-line folder is called WeilBound), Chowla 3, Turán 8, Arakelov/Faltings 8, explicit formula/Guinand/Weil
  positivity 41, Poincaré series 78, Parseval 113, Kazhdan–Patterson/metaplectic 119, von Mangoldt 129, Weyl char/dim 149,
  Gauss sums 183, Cauchy–Schwarz 198, relative trace formula 224, Gross–Prasad/GGP 330, Katz/monodromy 774, Iwasawa
  (not the decomposition) 974, theta functions 1,059, Howe/theta lifts 1,346, Weil representation 1,473, riemannZeta/
  L-functions 1,514, Deligne 2,538, Hecke characters 2,565, seesaw 3,466, étale 4,137 (includes étale algebras),
  complex multiplication 16,454 (mostly Mathlib's IsCMField), Siegel mass formula 28,672 (mostly the name GenusMassVolumes).
  Not in the outline but frequent: Langlands 3,088, abelian schemes/varieties 3,693, Siegel–Weil 1,462, Satake 908,
  Whittaker 1,024, Kisin 331, Jacquet–Shalika 190, Rosati 153.
- 1,070 files sit in `PublishedTheorems` folders (4,993 theorem declarations), named after classical results:
  CasselmanWallach, ClozelPurity, FerreroWashington, GelfandKazhdanReal, JacquetShalikaBound, JacquetShalikaRigidity,
  LanglandsClassification, PoitouTateDuality, SiegelWeil, Landherr, WeberRayClassFields, RosatiTraces,
  NadelVanishingPairs, KisinCrTrivial, PotentialSemistability, SemiabelianTori, CyclicBaseChangeC,
  SegmentRepresentations, RepNewform, CuspidalMultiplicityOne, TwistedTraceFormula, PolarizedGaloisRepresentations,
  GlobalEulerCharacteristic, ThetaCharacteristics, PoincareDeRhamDuality, HeckeLAdicCharacters.

## What to return
1. A JSON object with your re-estimated importance weights over the nine branch keys (auto, ant, cm, iwa, qf, agff,
   four, comb, avag), summing to 100, plus a low–high range for each.
2. Steps whose branch split or weight you would change, as "step: old → new, one-line reason". Say which changes come
   from Lean evidence and which from re-reading the note.
3. For each branch whose weight moved by more than 3 points, two or three sentences on why.
4. What you looked at (note pages, Lean files) and anything you could not settle. Say plainly where the evidence is
   too weak to move the estimate. Do not simply copy the code-volume shares.
