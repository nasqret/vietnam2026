# Module 04 — Formal artifacts (Lean / Agda / Rocq / Mizar)

**Goal:** prove a small, shared set of statements in **four** systems so students *see* the foundations:
Lean 4 (CIC), Agda (MLTT), Rocq/ex-Coq (CIC), Mizar (Tarski–Grothendieck set theory). The comparison is
the lesson — same theorem, four idioms.

## Shared statement set (grows)
1. **Propositional:** `(p → q → r) → (p → q) → p → r` (the `S` combinator / Curry–Howard). — L1/L3
2. **Church/Peano:** `n + 0 = n` and `0 + n = n` (why one is `rfl` and one needs induction). — L2/L4
3. **`add_comm` on ℕ** by induction. — L4
4. **√2 is irrational** (or `Nat` infinitude of primes) — a "real" proof. — L5
5. **A tiny EML-flavoured witness** (evaluate a term tree to a value). — L6

## Layout
```
artifacts/
  lean/   (lake project — VERIFIED locally: `lake build`)
  lean-fta/ (separate pinned Mathlib companion — full FTA)
  agda/   (verified locally — Agda 2.8.0, statements 1-4 — + CI)
  rocq/   (verified locally — Rocq 9.2, statements 1-5 incl. √2 — + CI)
  mizar/  (authored, illustrative — MML-style; no CI, not installed)
  README.md  (the four-way comparison table)
```

## Subtasks
- [x] Lean lake project with statements 1–3; `lake build` green locally.
- [x] Agda / Rocq / Mizar versions of statement 1 (the S combinator) as the Rosetta stone.
- [x] Extend statements 2–5 across the provers (Lean/Rocq 1–5 incl. √2; Agda 1–4 by documented choice; Mizar statement 1) with per-file prose linking to the book.
- [x] CI workflow to check Lean (and Agda/Rocq if runners allow).
- [x] Add a separate Lean 4/Mathlib FTA companion proving finite-list
      existence and uniqueness up to permutation, with exact revision and
      axiom auditing and no authority over Peano Lab.

## Acceptance criteria
- Lean builds locally with zero `sorry`.
- Lean FTA companion rejects `sorryAx` and reports only its three declared
  standard axioms.
- `artifacts/README.md` renders the four proofs of statement 1 side by side.
