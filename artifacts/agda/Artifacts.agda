------------------------------------------------------------------------
-- Course artifacts — Agda (Martin-Löf Type Theory)
--
-- VIASM mini-course "An Introduction to Automatic Theorem Proving".
-- Same statements as ../lean/Artifacts.lean, in Agda's MLTT foundation.
--
-- Note the mirror image of Lean: Agda's `_+_` recurses on its FIRST
-- argument, so here `zero + n = n` is definitional and `n + zero` needs
-- induction — exactly the opposite of Lean's `Nat`. Same maths, different
-- definitional equalities.
--
-- Check:  agda Artifacts.agda   (authored; verified in CI, MLTT).
------------------------------------------------------------------------

module Artifacts where

open import Agda.Builtin.Equality using (_≡_; refl)

-- ── Statement 1: the S combinator (propositions-as-types) ──────────────

S-comb : {P Q R : Set} → (P → Q → R) → (P → Q) → P → R
S-comb f g x = f x (g x)

S : {A B C : Set} → (A → B → C) → (A → B) → A → C
S f g x = f x (g x)

K : {A B : Set} → A → B → A
K x _ = x

I : {A : Set} → A → A
I x = x

-- ── a little equality plumbing (would come from the stdlib) ────────────

sym : {A : Set} {x y : A} → x ≡ y → y ≡ x
sym refl = refl

trans : {A : Set} {x y z : A} → x ≡ y → y ≡ z → x ≡ z
trans refl q = q

-- ── Statement 2/3: Peano naturals ──────────────────────────────────────

data Nat : Set where
  zero : Nat
  suc  : Nat → Nat

_+_ : Nat → Nat → Nat
zero  + n = n
suc m + n = suc (m + n)

congS : {m n : Nat} → m ≡ n → suc m ≡ suc n
congS refl = refl

-- 0 + n = n is definitional here:
zero-add : (n : Nat) → (zero + n) ≡ n
zero-add n = refl

-- n + 0 = n needs induction (the mirror of Lean):
add-zero : (n : Nat) → (n + zero) ≡ n
add-zero zero    = refl
add-zero (suc n) = congS (add-zero n)

add-suc : (m n : Nat) → (m + suc n) ≡ suc (m + n)
add-suc zero    n = refl
add-suc (suc m) n = congS (add-suc m n)

+-comm : (m n : Nat) → (m + n) ≡ (n + m)
+-comm zero    n = sym (add-zero n)
+-comm (suc m) n = trans (congS (+-comm m n)) (sym (add-suc n m))

-- ── Statement 4: a tiny expression evaluator (EML in miniature) ─────────

_*_ : Nat → Nat → Nat
zero  * _ = zero
suc m * n = n + (m * n)

data Tm : Set where
  lit : Nat → Tm
  add : Tm → Tm → Tm
  mul : Tm → Tm → Tm

eval : Tm → Nat
eval (lit n)   = n
eval (add a b) = eval a + eval b
eval (mul a b) = eval a * eval b

eval-add : (a b : Tm) → eval (add a b) ≡ (eval a + eval b)
eval-add a b = refl

-- swapping summands preserves the value, via commutativity of +
eval-add-comm : (a b : Tm) → eval (add a b) ≡ eval (add b a)
eval-add-comm a b = +-comm (eval a) (eval b)
