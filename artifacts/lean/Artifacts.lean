/-
  Course artifacts — Lean 4 (Mathlib-free)
  ========================================
  VIASM mini-course "An Introduction to Automatic Theorem Proving in Mathematics".

  The same small statements are proved here and in Agda, Rocq and Mizar
  (see ../agda, ../rocq, ../mizar and ../README.md). The point is to *see*
  four foundations doing the same job. Lean's foundation is the Calculus of
  Inductive Constructions (CIC); a proof of a proposition IS a term of the
  corresponding type — the Curry–Howard correspondence, made literal.

  Build & check:  `lake build`   (finishes with no `sorry`, no errors).
-/

namespace Artifacts

/-! ## Statement 1 — the S combinator, as logic and as data

The propositional tautology `(p → q → r) → (p → q) → p → r` and the S
combinator `S f g x = f x (g x)` are *the same thing* read through
Curry–Howard: the proof term of the tautology is exactly S. -/

/-- Statement 1 (propositions-as-types): the proof term is the S combinator. -/
theorem s_combinator {p q r : Prop} (f : p → q → r) (g : p → q) (x : p) : r :=
  f x (g x)

/-- The same combinators on data (types instead of propositions). -/
def S {α β γ : Type} (f : α → β → γ) (g : α → β) (x : α) : γ := f x (g x)
def K {α β : Type} (x : α) (_ : β) : α := x
def I {α : Type} (x : α) : α := x

/-- The combinators compute as expected (`K` throws away its second argument,
    `I` is the identity). The classic `S K K = I` holds too, but only once the
    discarded middle type is pinned — a first taste of type inference. -/
example {α β : Type} (x : α) (y : β) : K x y = x := rfl
example {α : Type} (x : α) : I x = x := rfl
example {α : Type} (x : α) : S (K : α → (α → α) → α) (K : α → α → α) x = I x := rfl

/-! ## Statement 2 — Peano addition: which equations are *definitional*?

`Nat` addition recurses on its second argument, so `n + 0 = n` and
`n + (m+1) = (n+m)+1` hold *by definition* (`rfl`), while the mirror
images `0 + n = n` and `(n+1) + m = (n+m)+1` genuinely need induction.
This asymmetry is the first real surprise for newcomers. -/

/-- `n + 0 = n` is true by definition. -/
theorem add_zero' (n : Nat) : n + 0 = n := rfl

/-- `n + (m+1) = (n+m)+1` is also definitional. -/
theorem add_succ' (n m : Nat) : n + (m + 1) = (n + m) + 1 := rfl

/-- `0 + n = n` is NOT definitional — it needs induction on `n`. -/
theorem zero_add' : ∀ n : Nat, 0 + n = n
  | 0     => rfl
  | n + 1 => congrArg (· + 1) (zero_add' n)

/-- `(n+1) + m = (n+m)+1` — induction on `m`. -/
theorem succ_add' : ∀ n m : Nat, (n + 1) + m = (n + m) + 1
  | _, 0     => rfl
  | n, m + 1 => congrArg (· + 1) (succ_add' n m)

/-! ## Statement 3 — commutativity of addition on ℕ, by induction

Now we can prove `n + m = m + n` from the primitives above — the canonical
"first real theorem" in every proof-assistant tutorial. -/

/-- `n + m = m + n`, proved from `zero_add'`/`succ_add'` by induction on `m`. -/
theorem add_comm' (n m : Nat) : n + m = m + n := by
  induction m with
  | zero      => rw [add_zero', zero_add']
  | succ m ih => rw [add_succ', succ_add', ih]

/-- Sanity checks the kernel evaluates on the spot. -/
example : (2 : Nat) + 3 = 3 + 2 := add_comm' 2 3
example : (0 : Nat) + 7 = 7 := zero_add' 7

/-! ## Statement 4 — a tiny expression evaluator (EML in miniature)

A first taste of {doc}`Lecture 6 <l6_autoformalization>`'s EML idea: a syntax tree with a
denotation, and theorems relating syntax to value. Here the grammar is `1`/`+`/`·` over `Nat` and the
denotation is `eval`. In the real EML project the leaves are complex constants and `eval?` is an
`Option ℂ`-valued partial denotation — but the shape is exactly this. -/

/-- A little expression grammar (cf. EML's `EMLTerm`). -/
inductive Tm where
  | lit : Nat → Tm
  | add : Tm → Tm → Tm
  | mul : Tm → Tm → Tm

/-- Its denotation into `Nat` (cf. EML's `eval?`). -/
def eval : Tm → Nat
  | .lit n   => n
  | .add a b => eval a + eval b
  | .mul a b => eval a * eval b

/-- A concrete witness: the tree `1 + 1` evaluates to `2`, checked by the kernel. -/
example : eval (.add (.lit 1) (.lit 1)) = 2 := rfl

/-- Syntax-directed: `add` denotes `+` (definitional). -/
theorem eval_add (a b : Tm) : eval (.add a b) = eval a + eval b := rfl

/-- A structural theorem transported through the denotation: swapping the summands
    does not change the value — because `+` on `ℕ` is commutative (`add_comm'`). -/
theorem eval_add_comm (a b : Tm) : eval (.add a b) = eval (.add b a) := by
  show eval a + eval b = eval b + eval a
  exact add_comm' (eval a) (eval b)

end Artifacts
