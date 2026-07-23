# Lecture 5 — Advanced Lean

```{admonition} Abstract
:class: tip
The tools that make formalizing *real* mathematics tractable: **dependent types** in practice,
**structures** and **typeclasses**, the architecture of **Mathlib** and how to search it, the heavy-duty
tactics (`simp`, `ring`, `linarith`, `omega`, `norm_num`, `decide`, `positivity`), **`calc`** blocks, and
**well-founded recursion** — closing on a genuine analysis/algebra proof.
```

## Learning objectives

- Use dependent types, `structure`, and `class`/`instance` to state general theorems.
- Search Mathlib effectively (`exact?`, `apply?`, `rw?`, Loogle, LeanSearch).
- Choose the right automation tactic for a goal and chain steps with `calc`.
- Read a nontrivial Mathlib-style proof and know where each lemma comes from.

## Dependent types, structures, typeclasses

A **structure** bundles data with the proofs of its axioms; a **typeclass** lets Lean *find* the right
structure automatically. This is how `+`, `0`, `≤` mean the right thing on `Nat`, `Int`, `ℝ`, matrices,
polynomials… all at once:

```lean
class Group (G : Type*) extends Mul G, One G, Inv G where
  mul_assoc : ∀ a b c : G, a * b * c = a * (b * c)
  one_mul   : ∀ a : G, 1 * a = a
  mul_left_inv : ∀ a : G, a⁻¹ * a = 1
```

A theorem stated `[Group G]` then applies to *every* group Mathlib knows about. Dependent types make the
*statement* itself precise: `Matrix (Fin m) (Fin n) ℝ` is a type whose shape is part of its type.

## Automation you will actually use

| Tactic | Discharges |
|--------|-----------|
| `ring` / `ring_nf` | identities in commutative (semi)rings |
| `linarith` / `nlinarith` | linear (and some nonlinear) arithmetic over ordered fields |
| `omega` | linear integer/natural arithmetic |
| `norm_num` | concrete numerical (in)equalities |
| `field_simp` | clear denominators |
| `positivity` | prove `0 < e` / `0 ≤ e` |
| `simp [lemmas]` | rewrite to a normal form |
| `decide` | decidable propositions by computation |

## Reading, and searching, Mathlib

Mathlib is a single coherent library of formalized mathematics with well over a million lines — the
reason "real maths in Lean" is possible at all. The skill is *finding the lemma*:
- `exact?` / `apply?` — "is my goal already a lemma (or one apply away)?"
- `rw?` — "what can I rewrite with here?"
- **Loogle** and **LeanSearch/Moogle** — search by shape or by natural language.

## `calc` — proofs that read like blackboard mathematics

```lean
example (a b : ℝ) : (a + b)^2 = a^2 + 2*a*b + b^2 := by
  calc (a + b)^2 = a^2 + 2*a*b + b^2 := by ring
```

`calc` chains equalities/inequalities transitively; each step names its own justification.

## A genuine theorem: $\sqrt{2}$ is irrational

The classical proof formalizes cleanly. In Mathlib it is essentially one line —
`Nat.Prime.irrational_sqrt` / `irrational_sqrt_two` — but the *instructive* version reconstructs it: if
$\sqrt 2 = p/q$ in lowest terms then $2q^2 = p^2$, so $2 \mid p$, so $4 \mid p^2 = 2q^2$, so $2 \mid q$,
contradicting lowest terms. Every step above is a `omega`/`ring`/divisibility lemma.

```{admonition} Run it
:class: seealso
Open a Lean web editor, `import Mathlib`, and try `example : Irrational (Real.sqrt 2) := by exact?`.
Watch `exact?` *find the proof for you* — then open the lemma it names and read how it was built.
```

## References

Mathlib documentation and source; *Theorem Proving in Lean 4* (typeclasses, structures); *Mathematics in
Lean*; Avigad, *Mathematical Logic and Computation*.
```{note}
Grows with a fully worked `calc` proof and a guided Mathlib lemma-hunt.
```
