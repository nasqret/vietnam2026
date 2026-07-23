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
  agda/   (authored; CI-checked)
  rocq/   (authored; CI-checked)
  mizar/  (authored; MML-style; CI-checked)
  README.md  (the four-way comparison table)
```

## Subtasks
- [x] Lean lake project with statements 1–3; `lake build` green locally.
- [x] Agda / Rocq / Mizar versions of statement 1 (the S combinator) as the Rosetta stone.
- [ ] Extend statements 2–5 across all provers; add per-file prose linking to the book.
- [ ] CI workflow to check Lean (and Agda/Rocq if runners allow).

## Acceptance criteria
- Lean builds locally with zero `sorry`.
- `artifacts/README.md` renders the four proofs of statement 1 side by side.
