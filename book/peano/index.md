# Building Peano Lab (in progress)

*A little Lean for Peano arithmetic — and a guided tour of how such systems are built.*

This part of the book is being written **alongside the implementation** on the `peano-lab`
branch. The plan: a lightweight, readable theorem prover for Peano arithmetic running in the
browser next to the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/) —
with a small trusted kernel, an untrusted tactic engine, a genuine tactic *language*
(tacticals), an induction tactic, a `simp`, and, eventually, a machine-readable proof-trace
corpus for training a small language-model prover.

Planned chapters:

1. **Why Peano arithmetic** — the staged logic: equations → induction → quantifiers.
2. **The kernel and the De Bruijn criterion** — proof terms, an independent checker, and why
   we never again trust the tactic layer (a war story from the Lambda Lab audit).
3. **Anatomy of a tactic** — goals, metavariables, and the contract every tactic obeys.
4. **Tacticals** — the moment tactics become a language.
5. **Induction and the theorem ladder** — from `0 + n = n` to `n·m = 0 → n = 0 ∨ m = 0`.
6. **Limits** — Gödel, and what Lean has that we deliberately don't.

The working design lives in
[`docs/PEANO_LAB_DESIGN.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_LAB_DESIGN.md),
the task board in
[`PLAN/09_peano_lab.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/PLAN/09_peano_lab.md).

The first executable chapter is live: {doc}`Checked tutorials <tutorials>` replays a premise-free
hand proof of addition commutativity and a source-level `symm_all` tactical walkthrough. Every
`pa>` block on that page is checked against the browser driver's real command grammar during the
book build gate.

The full M7 library is executable too. {doc}`The checked theorem ladder <ladder>` follows twenty
scripted entries through order totality and the zero-product capstone, explains how theorem reuse
is cut-eliminated outside the trusted kernel, and links each statement to the browser and Lean 4
cross-checking surface.
