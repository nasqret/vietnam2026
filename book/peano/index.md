# Building Peano Lab

*A little Lean for Peano arithmetic — and a guided tour of how such systems are built.*

Peano Lab is a lightweight, readable theorem prover for Peano arithmetic. It runs entirely in the
browser next to the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/), but its
central lesson is not a flashy tactic: **every QED is checked again by an independent kernel against
the original theorem**. Tactics may search, guess and fail. The kernel sees only an explicit proof
certificate.

This part tells the construction story from the implementation diary. Read it in order:

1. {doc}`Why Peano arithmetic <why-pa>` develops the staged path from computation to induction and
   first-order logic.
2. {doc}`The kernel and the De Bruijn criterion <kernel>` explains the trusted boundary, proof terms,
   capture-safe substitution and the audit that made independent checking non-negotiable.
3. {doc}`Anatomy of a tactic <tactics>` follows one tactic from a goal transformation to a certificate
   with proof-wide metavariable substitution and transactional failure.
4. {doc}`Tacticals: when tactics become a language <tacticals>` builds sequencing, choice, repetition,
   focusing and their rollback laws.
5. {doc}`Induction and the theorem ladder <induction-ladder>` climbs from the defining equations to a
   checked zero-product proof.
6. {doc}`Checked arithmetic automation <arithmetic-automation>` separates numerical computation,
   polynomial normalization, and bounded search from the certificates that justify their results.
7. {doc}`The deliberate limits <limits>` draws the line around PA, Gödel's theorems, bounded search,
   and the facilities that a production prover such as Lean adds.

The working design lives in
[`docs/PEANO_LAB_DESIGN.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_LAB_DESIGN.md),
the task board in
[`PLAN/09_peano_lab.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/PLAN/09_peano_lab.md).

Then use {doc}`Checked tutorials <tutorials>` to replay a premise-free hand proof of addition
commutativity, a source-level `symm_all` tactical walkthrough, and a numerical-normalization proof.
Every `pa>` block and browser deep link in this part is replayed through the real driver during the
book gate; prose examples do not get a private, easier semantics.

The full M7 library is executable too. {doc}`The checked theorem ladder <ladder>` follows twenty
scripted entries through order totality and the zero-product capstone, explains how theorem reuse is
cut-eliminated outside the trusted kernel, and links each statement to the browser and Lean 4
cross-checking surface. M9 then turns the same checked interactions into a reproducible
[proof-trace corpus](https://github.com/nasqret/vietnam2026/tree/peano-lab/peano-lab/corpus) and fixes
a [kernel-judged evaluation protocol](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_LLM.md)
for later small-model experiments; no model is trained in this repository. The dated
{doc}`implementation diary <diary>` preserves the design choices, bugs and objections behind the
polished account.

M11 extends that core with three ordinary checked entries—`one_mul`, `mul_one`, and `add_mul`—to
complete the commutative-semiring basis for certificate-producing arithmetic normalization. M12's
argument-free `ring` turns that basis into checked polynomial identities; the ladder chapter gives
the complete odd-square induction proof and makes its explicit `trans`/`rewrite` boundary visible.
M13 adds bounded `norm_num` for closed numerical islands and arithmetic-aware hints. The new
arithmetic-automation chapter contrasts its exact equality contract with `simp`, `ring`, and `auto`,
and records why general PA, nonlinear hypothesis solving, and Presburger `omega` remain outside it.
M14 then treats browser delivery as another explicit boundary: versioned caching, negotiated WASM
compression, and concurrent source transfer reduce cold network cost without changing one proof rule.
The limits chapter distinguishes that runtime boot from theorem proving. M15 adds a replayable
current-branch artifact: active text remains unchecked, while only a successful kernel QED may
produce the retained script's final `qed`. The tactics and ladder chapters explain why downloading
that program is still separate from checking a certificate or admitting a library theorem.
