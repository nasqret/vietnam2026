import PeanoLab.Semantics
import PeanoLab.Checker

/-!
# Soundness

The first theorem proves the independent certificate calculus sound in the
standard natural numbers.  The executable checker carries a `Derives` witness on every accepting branch,
so the final checker theorem is a short composition with calculus soundness.
-/

namespace PeanoLab

/-- Each of the six fixed arithmetic axioms is true in `Nat`. -/
theorem axiomFormula_sound (name : AxiomName) (v : Valuation) :
    (axiomFormula name).Holds v := by
  cases name with
  | pa1 => simp [axiomFormula, Formula.Holds, Term.eval, Valuation.cons]
  | pa2 => simp [axiomFormula, Formula.Holds, Term.eval, Valuation.cons]
  | pa3 => simp [axiomFormula, Formula.Holds, Term.eval, Valuation.cons]
  | pa4 =>
      simp only [axiomFormula, Formula.Holds, Term.eval, Valuation.cons]
      intro n m
      simpa only [Nat.succ_eq_add_one] using Nat.add_succ n m
  | pa5 => simp [axiomFormula, Formula.Holds, Term.eval, Valuation.cons]
  | pa6 =>
      simp only [axiomFormula, Formula.Holds, Term.eval, Valuation.cons]
      intro n m
      simpa only [Nat.succ_eq_add_one] using Nat.mul_succ n m

/-- Every derivation represented by a certificate preserves truth of its
formula context. -/
theorem Derives.sound {classical : Bool} {ctx : Context} {proof : Proof}
    {a : Formula} (h : Derives classical ctx proof a) :
    ∀ v : Valuation, HoldsContext v ctx -> a.Holds v := by
  classical
  induction h with
  | hyp hget =>
      intro v hctx
      exact HoldsContext.get? hctx hget
  | impIntro hbody ih =>
      intro v hctx ha
      exact ih v ⟨ha, hctx⟩
  | impElim hfun harg ihfun iharg =>
      intro v hctx
      exact (ihfun v hctx) (iharg v hctx)
  | cut hlemma hbody ihlemma ihbody =>
      intro v hctx
      exact ihbody v ⟨ihlemma v hctx, hctx⟩
  | andIntro hleft hright ihleft ihright =>
      intro v hctx
      exact ⟨ihleft v hctx, ihright v hctx⟩
  | andElimL hpair ih =>
      intro v hctx
      exact (ih v hctx).1
  | andElimR hpair ih =>
      intro v hctx
      exact (ih v hctx).2
  | orIntroL h ih =>
      intro v hctx
      exact Or.inl (ih v hctx)
  | orIntroR h ih =>
      intro v hctx
      exact Or.inr (ih v hctx)
  | orElim hdisj hleft hright ihdisj ihleft ihright =>
      intro v hctx
      cases ihdisj v hctx with
      | inl ha => exact ihleft v ⟨ha, hctx⟩
      | inr hb => exact ihright v ⟨hb, hctx⟩
  | botElim hbot ih =>
      intro v hctx
      exact False.elim (ih v hctx)
  | forallIntro hbody ih =>
      intro v hctx n
      apply ih (Valuation.cons n v)
      exact (HoldsContext.underTermBinder v n _).2 hctx
  | forallElim hall ih =>
      intro v hctx
      apply (Formula.holds_subst_zero _ v _).2
      exact ih v hctx ((Term.eval v _))
  | existsIntro hbody ih =>
      rename_i classical' ctx' p' motive t
      intro v hctx
      refine ⟨Term.eval v t, ?_⟩
      exact (Formula.holds_subst_zero _ v t).1 (ih v hctx)
  | existsElim hex hbody ihe ihbody =>
      intro v hctx
      rcases ihe v hctx with ⟨n, ha⟩
      apply (Formula.holds_shift_underBinder _ v n).1
      apply ihbody (Valuation.cons n v)
      exact ⟨ha, (HoldsContext.underTermBinder v n _).2 hctx⟩
  | eqRefl =>
      intro v hctx
      rfl
  | eqSym heq ih =>
      intro v hctx
      exact (ih v hctx).symm
  | eqTrans h₁ h₂ ih₁ ih₂ =>
      intro v hctx
      exact (ih₁ v hctx).trans (ih₂ v hctx)
  | congS heq ih =>
      intro v hctx
      exact congrArg Nat.succ (ih v hctx)
  | congAdd h₁ h₂ ih₁ ih₂ =>
      intro v hctx
      have hs := ih₁ v hctx
      have ht := ih₂ v hctx
      simp only [Formula.Holds] at hs ht
      have hsum := congr (congrArg (fun x : Nat => fun y : Nat => x + y) hs) ht
      simpa only [Formula.Holds, Term.eval] using hsum
  | congMul h₁ h₂ ih₁ ih₂ =>
      intro v hctx
      have hs := ih₁ v hctx
      have ht := ih₂ v hctx
      simp only [Formula.Holds] at hs ht
      have hproduct := congr (congrArg (fun x : Nat => fun y : Nat => x * y) hs) ht
      simpa only [Formula.Holds, Term.eval] using hproduct
  | eqSubst heq hbody iheq ihbody =>
      intro v hctx
      have hst : Term.eval v _ = Term.eval v _ := iheq v hctx
      have hs := (Formula.holds_subst_zero _ v _).1 (ihbody v hctx)
      apply (Formula.holds_subst_zero _ v _).2
      simpa [hst] using hs
  | dne henabled =>
      intro v hctx hnna
      apply Classical.byContradiction
      intro hna
      exact hnna hna
  | paAxiom =>
      intro v hctx
      exact axiomFormula_sound _ v
  | ind hbase hstep ihbase ihstep =>
      intro v hctx n
      induction n with
      | zero =>
          exact (Formula.holds_subst_zero _ v .zero).1 (ihbase v hctx)
      | succ n ihN =>
          have hstepAt := ihstep v hctx n
          have hsucc : (successorInstance _).Holds (Valuation.cons n v) :=
            hstepAt ihN
          exact (Formula.holds_successorInstance _ v n).1 hsucc

/-- A closed, empty-context intuitionistic derivation is true in the standard
natural numbers under every valuation. -/
theorem closed_derivation_sound {proof : Proof} {a : Formula}
    (h : Derives false [] proof a) :
    ∀ v : Valuation, a.Holds v := by
  intro v
  exact h.sound v trivial

/-- Acceptance by the public empty-context gate implies truth in `Nat`. -/
theorem checkClosed_sound {proof : Proof} {a : Formula}
    (h : checkClosed proof a = true) :
    ∀ v : Valuation, a.Holds v := by
  exact closed_derivation_sound (checkClosed_derives h)

end PeanoLab
