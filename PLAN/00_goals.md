# L0 — Goals

## Who this is for

Mathematically mature students and researchers at VIASM who are **new to formal methods**. They know
what a proof is; they have (mostly) never written one a machine checks.

## What they should leave with

1. **A mental model of type theory** — judgments, terms-as-proofs, why proof assistants rest on type
   theory rather than raw set theory, and how four real systems (Lean, Agda, Rocq, Mizar) instantiate it.
2. **Fluency with the λ-calculus as a computational substrate** — able to hand-reduce Church encodings
   and reproduce every calculation in the Lambda Lab.
3. **The Curry–Howard reflex** — reading a proof as a program and a proposition as a type, first for
   propositional logic, then in Lean.
4. **A first real Lean skill** — writing and reading honest tactic proofs, using Mathlib and its search.
5. **A grounded view of auto-formalization** — what today's AI + proof-assistant pipelines can and cannot
   do, seen through one fully worked research formalization (EML).

## Emotional/experiential goals

- "I can *run* this" — every abstract idea has a button to press (lab, game, notebook).
- "The machine agrees" — the satisfaction of a green checkmark on a proof they wrote.
- "This is real mathematics" — the capstone is a genuine research paper, formalized.

## Non-goals

- Not a complete course in dependent type theory or in Lean metaprogramming.
- Not training frontier-scale provers; the AI story is understood, not reproduced.
- The formal artifacts are *illustrative*, chosen to expose foundations — not a library.

## Success criteria (project level)

- [ ] `/vietnam2026` is live, styled, and links every artifact.
- [ ] The Lambda Lab runs in a browser with no install.
- [ ] Book builds clean; the first chapters of Lectures 1–3 are readable end-to-end.
- [ ] At least one shared statement is proved in all four provers.
- [ ] Everything is on GitHub (`nasqret/vietnam2026`) with a reproducible build.
