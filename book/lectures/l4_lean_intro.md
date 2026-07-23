# Lecture 4 — Introduction to Lean

```{admonition} Abstract
:class: tip
From paper to kernel. We meet **Lean 4**: the difference between **term mode** and **tactic mode**,
between **propositions** and **data**, the natural numbers and **induction**, and the handful of tactics
that get you to a first honest end-to-end proof. We anchor the practice in the **Natural Number Game**
and Heather Macbeth's **Mechanics of Proof**.
```

## Learning objectives

- Read a Lean `theorem` and tell term mode from tactic mode.
- Use `rfl`, `exact`, `intro`, `apply`, `rw`, `simp`, `induction`, `rcases`, `omega`, `decide`.
- Prove a statement by induction on `Nat` and understand each goal transformation.
- Install and run Lean with `elan`/`lake`, and use `#check` / `#eval`.

## Two modes, one meaning

A proof term and a tactic script produce the *same* kernel-checked object.

```lean
-- term mode: the proof IS the program
theorem imp_self (p : Prop) : p → p := fun h => h

-- tactic mode: a recipe that builds the same term
theorem imp_self' (p : Prop) : p → p := by
  intro h
  exact h
```

`Prop` is the universe of propositions (proof-irrelevant); `Type` is the universe of data. A `theorem`
lives in `Prop`; a `def` usually builds data in `Type`.

## Nat and induction

`Nat` is an inductive type with constructors `zero` and `succ`. Addition recurses on the **second**
argument, so `n + 0 = n` holds by `rfl` while `0 + n = n` needs induction — the asymmetry from
{doc}`Lecture 2 <l2_lambda_calculus>`, now inside a proof assistant:

```lean
theorem zero_add (n : Nat) : 0 + n = n := by
  induction n with
  | zero => rfl
  | succ n ih => rw [Nat.add_succ, ih]
```

The capstone of the day is commutativity, proved from the primitives — exactly our
[Lean artifact](https://github.com/nasqret/vietnam2026/blob/main/artifacts/lean/Artifacts.lean):

```lean
theorem add_comm' (n m : Nat) : n + m = m + n := by
  induction m with
  | zero      => rw [add_zero', zero_add']
  | succ m ih => rw [add_succ', succ_add', ih]
```

## A tactic starter kit

| Tactic | Use it to… |
|--------|-----------|
| `rfl` | close a goal true by computation |
| `exact e` / `apply f` | give the term / apply a function, leaving its arguments as goals |
| `intro h` | move a hypothesis of a `→`/`∀` into context |
| `rw [h]` | rewrite with an equation |
| `simp` | simplify with the simp set |
| `induction n` | do induction on `n` |
| `rcases h with ...` | destructure `∧`, `∨`, `∃` |
| `omega` | discharge linear arithmetic over `Nat`/`Int` |
| `decide` | close a decidable goal by computation |

## Getting Lean running

```bash
# one-time: install the version manager and toolchain
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh   # installs elan + lean + lake
# a Mathlib-backed project, or just open the games in a browser (no install):
#   Natural Number Game:  https://adam.math.hhu.de/#/g/leanprover-community/nng4
```

```{admonition} Run it
:class: seealso
Play the [Natural Number Game](https://adam.math.hhu.de/#/g/leanprover-community/nng4) through the
Addition world, then read `add_comm'` above and recognize the moves. Nothing to install — it runs in
the browser.
```

## References

Macbeth, *The Mechanics of Proof*; the *Natural Number Game*; *Theorem Proving in Lean 4*; Mathlib
documentation; the course's [Lean artifact](https://github.com/nasqret/vietnam2026/tree/main/artifacts/lean).
```{note}
This chapter grows with a full first-project walkthrough (`lake new`, importing Mathlib, `#check`/`#eval`).
```
