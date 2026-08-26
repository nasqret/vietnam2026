import Mathlib.Data.Nat.Factors

/-!
# Fundamental theorem of arithmetic

This companion artifact states both halves of the theorem directly: every
nonzero natural has a finite list of prime factors, and every other such list
is a permutation of it.  The canonical witness is `Nat.primeFactorsList`.

This file is deliberately separate from the Mathlib-free course artifact.
It cross-checks the target mathematics while Peano Lab develops its
conservative Goedel-coded finite-sequence layer.  It is not imported as a
Peano axiom or theorem.
-/

namespace ArithmeticFTA

/-- `factors` is a finite prime factorization of `n`. -/
def IsPrimeFactorization (n : ℕ) (factors : List ℕ) : Prop :=
  factors.prod = n ∧ ∀ p ∈ factors, Nat.Prime p

/-- Existence: the canonical list is a prime factorization of every nonzero natural. -/
theorem prime_factorization_exists (n : ℕ) (hn : n ≠ 0) :
    IsPrimeFactorization n n.primeFactorsList := by
  constructor
  · exact Nat.prod_primeFactorsList hn
  · intro p hp
    exact Nat.prime_of_mem_primeFactorsList hp

/-- Uniqueness: every prime factorization is the canonical one up to permutation. -/
theorem prime_factorization_unique {n : ℕ} {factors : List ℕ}
    (h : IsPrimeFactorization n factors) :
    factors.Perm n.primeFactorsList := by
  exact Nat.primeFactorsList_unique h.1 h.2

/--
The Fundamental Theorem of Arithmetic: existence and uniqueness, up to the
order of factors, of a finite prime factorization of every nonzero natural.

The case `n = 1` is represented by the empty factor list.
-/
theorem fundamental_theorem_of_arithmetic (n : ℕ) (hn : n ≠ 0) :
    ∃ factors : List ℕ,
      IsPrimeFactorization n factors ∧
      ∀ other : List ℕ, IsPrimeFactorization n other → other.Perm factors := by
  refine ⟨n.primeFactorsList, prime_factorization_exists n hn, ?_⟩
  intro other hother
  exact prime_factorization_unique hother

end ArithmeticFTA
