# Lean-code analysis tools: landscape (searched 2026-11-20)

## Need a successful build (.olean / Environment)
- LeanDojo (arXiv 2306.15626): traces a repo at a commit; file DAG, constants per file with positions, premises, tactic states.
- jixia (reaslab/frenzymath on Reservoir): static analysis plugins for imports, declarations, symbols + reference graph;
  binary must match target Lean version; no transitive-dependency computation built in.
- import-graph / `lake exe graph`: module import graph (pdf/html/xdot); needs lake build; default output is transitive reduction.
- "The Network Structure of Mathlib" (arXiv 2604.24797, May 2026; code github.com/MathNetwork/mathlib-network,
  data HF MathNetwork/MathlibGraph): Mathlib @534cf0b = 308,129 declarations, 8,436,366 dependency edges, 7,563 modules.
  File layout vs dependency communities NMI 0.34 (layout vs namespaces 0.71). No math-area classifier.
- Astrolabe (github.com/Xinze-Li-Bryan/Astrolabe, v0.1.9 Jan 2026): 3D declaration-dependency viewer; needs lake build + .ilean.
- Trust: `#print axioms`, lean4checker (kernel replay of .olean), comparator / `lake comparator` (sandboxed, nanoda
  external checker), axiom-audit (leanprover-community; allowlist CI), gonzalgo (PyPI; ofReduceBool tracking), sorrydb.

## Area classification
- No MSC tagging of Mathlib found. doc-verification-bridge (nicolasrouquette.github.io) advertises "automatic theorem
  classification across Lean 4 projects"; pages returned 404 to our fetcher, unverified. Zulip 2023 thread
  "Metamathematics: Theorems by Domain Areas" advises the Lean parser over regex.
- Nothing found for the Alpöge RH archive specifically.

## Gaps hit in this project (motivation for a tool)
- Archive: 14 parts, 229 MB -> 1.4 GB, 175,187 files, 15.5M code lines; ~1.05M theorem+def by text (~3x Mathlib decls).
- 0 module docstrings; import closure from Main = 100% of files; 136,003 files `import Mathlib` whole.
- Qualified names embed folder labels -> keyword pollution (galois_cft 4,846 -> 644 hits after stripping).
- Name collisions: IwasawaDecomposition, order Lattice vs Z-lattice, IsTheta, dslope, nonZeroDivisors, Mathlib `zeta`.
- Census 450 s single-threaded; regex branch scan ~16 min on 5 cores.
- Idea: build-free tier resolving project references to Mathlib constants (Mathlib env from cache) and using Mathlib's
  module paths as the area taxonomy; build tier for exact constant-level closure from the main theorem + axioms.
