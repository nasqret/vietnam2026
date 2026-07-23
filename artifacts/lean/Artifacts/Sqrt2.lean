/-
  Statement 5 — √2 is irrational (Mathlib-free), by Fermat's infinite descent.
  =========================================================================
  We prove there is no *positive* natural solution to p² = 2·q²: every
  solution forces q = 0. Equivalently, √2 is irrational — if √2 = p/q in
  lowest terms then p² = 2q² with q ≠ 0, impossible.

  The whole argument lives in Lean 4 core (no Mathlib), so it stays in the
  fast `lake build`. The engine is `even_sq_iff`: a square is even iff its
  root is, which drives the descent p → r → s → …
-/

namespace Artifacts.Sqrt2

/-- `n²` is even **iff** `n` is even. The `→` direction is the crux. -/
theorem even_sq_iff (n : Nat) : n * n % 2 = 0 ↔ n % 2 = 0 := by
  constructor
  · intro h
    rw [Nat.mul_mod] at h
    rcases Nat.mod_two_eq_zero_or_one n with h0 | h1
    · exact h0
    · rw [h1] at h; exact absurd h (by decide)
  · intro h
    simp [Nat.mul_mod, h]

/-- An even natural is twice something. -/
theorem even_two_mul {n : Nat} (h : n % 2 = 0) : ∃ r, n = 2 * r :=
  ⟨n / 2, by omega⟩

/-- `(2a)² = 2·(2·a²)` — squaring an even number, pure `Nat` bookkeeping. -/
private theorem sq_two_mul (a : Nat) : (2 * a) * (2 * a) = 2 * (2 * (a * a)) := by
  calc (2 * a) * (2 * a) = 2 * (a * (2 * a)) := by rw [Nat.mul_assoc]
    _ = 2 * ((2 * a) * a) := by rw [Nat.mul_comm a (2 * a)]
    _ = 2 * (2 * (a * a)) := by rw [Nat.mul_assoc]

/-- **No positive solution to `p² = 2·q²`**: any solution has `q = 0`. -/
theorem no_sqrt2 : ∀ p q : Nat, p * p = 2 * (q * q) → q = 0 := by
  intro p
  induction p using Nat.strongRecOn with
  | ind p ih =>
    intro q hpq
    -- p² is even, so p is even: p = 2r
    have hpe : p * p % 2 = 0 := by rw [hpq]; omega
    obtain ⟨r, rfl⟩ := even_two_mul ((even_sq_iff p).mp hpe)
    -- cancel a factor of 2:  q² = 2·r²
    rw [sq_two_mul] at hpq
    have hq2 : q * q = 2 * (r * r) := (Nat.eq_of_mul_eq_mul_left (by decide) hpq).symm
    -- q² is even, so q is even: q = 2s
    have hqe : q * q % 2 = 0 := by rw [hq2]; omega
    obtain ⟨s, rfl⟩ := even_two_mul ((even_sq_iff q).mp hqe)
    -- cancel again:  r² = 2·s²  — a strictly smaller instance
    rw [sq_two_mul] at hq2
    have hr2 : r * r = 2 * (s * s) := (Nat.eq_of_mul_eq_mul_left (by decide) hq2).symm
    -- descent: conclude s = 0, hence q = 2s = 0
    rcases Nat.eq_zero_or_pos r with hr0 | hrpos
    · subst hr0
      have hss : s * s = 0 := by omega
      rcases Nat.mul_eq_zero.mp hss with h | h <;> omega
    · have : s = 0 := ih r (by omega) s hr2
      omega

/-- Repackaged: there is **no** pair of positive naturals with `p² = 2·q²`. -/
theorem no_pos_sqrt2 (p q : Nat) (hq : q ≠ 0) : p * p ≠ 2 * (q * q) := by
  intro h; exact hq (no_sqrt2 p q h)

end Artifacts.Sqrt2
