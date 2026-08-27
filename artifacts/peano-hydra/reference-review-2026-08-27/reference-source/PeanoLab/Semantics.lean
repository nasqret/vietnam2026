import Lean.Elab.Tactic.Omega
import PeanoLab.Substitution

/-!
# Standard-natural-number semantics

This file interprets Peano Lab syntax in `Nat` and proves the de Bruijn
lemmas needed by quantifiers, equality substitution, and induction.
-/

namespace PeanoLab

/-- An assignment for free de Bruijn variables. -/
abbrev Valuation := Nat -> Nat

namespace Valuation

/-- Extend a valuation with a new innermost variable. -/
def cons (head : Nat) (tail : Valuation) : Valuation
  | 0     => head
  | i + 1 => tail i

/-- The valuation seen before a syntactic shift. -/
def pullShift (v : Valuation) (amount cutoff : Nat) : Valuation :=
  fun i => if cutoff <= i then v (i + amount) else v i

/-- Insert one semantic value at de Bruijn slot `idx`. -/
def insert (v : Valuation) (idx value : Nat) : Valuation :=
  fun i =>
    if i < idx then v i
    else if i = idx then value
    else v (i - 1)

@[simp] theorem cons_zero (n : Nat) (v : Valuation) : cons n v 0 = n := rfl

@[simp] theorem cons_succ (n : Nat) (v : Valuation) (i : Nat) :
    cons n v (i + 1) = v i := rfl

@[simp] theorem pullShift_zero (n : Nat) (v : Valuation) :
    pullShift (cons n v) 1 0 = v := by
  funext i
  simp [pullShift, cons]

@[simp] theorem pullShift_cons (n : Nat) (v : Valuation) (amount cutoff : Nat) :
    pullShift (cons n v) amount (cutoff + 1) =
      cons n (pullShift v amount cutoff) := by
  funext i
  cases i with
  | zero => simp [pullShift, cons]
  | succ i =>
      by_cases h : cutoff <= i
      · simp [pullShift, cons, h, Nat.succ_add]
      · simp [pullShift, cons, h]

@[simp] theorem insert_zero (v : Valuation) (value : Nat) :
    insert v 0 value = cons value v := by
  funext i
  cases i with
  | zero => simp [insert, cons]
  | succ i => simp [insert, cons]

@[simp] theorem insert_cons (n : Nat) (v : Valuation) (idx value : Nat) :
    insert (cons n v) (idx + 1) value = cons n (insert v idx value) := by
  funext i
  cases i with
  | zero => simp [insert, cons]
  | succ i =>
      by_cases hlt : i < idx
      · simp [insert, cons, hlt]
      · by_cases heq : i = idx
        · subst i
          simp [insert, cons]
        · have hgt : idx < i := by omega
          cases i with
          | zero => omega
          | succ i => simp [insert, cons, hlt, heq]

end Valuation

namespace Term

/-- Standard interpretation of arithmetic terms. -/
def eval (v : Valuation) : Term -> Nat
  | .var i   => v i
  | .zero    => 0
  | .succ t  => Nat.succ (eval v t)
  | .add s t => eval v s + eval v t
  | .mul s t => eval v s * eval v t

/-- Shifting syntax is equivalent to pulling back the valuation. -/
theorem eval_shift (t : Term) (v : Valuation) (amount cutoff : Nat) :
    eval v (shiftTerm t amount cutoff) =
      eval (Valuation.pullShift v amount cutoff) t := by
  induction t with
  | var i =>
      by_cases h : cutoff <= i <;>
        simp [shiftTerm, eval, Valuation.pullShift, h]
  | zero => rfl
  | succ t ih => simp [shiftTerm, eval, ih]
  | add s t ihs iht => simp [shiftTerm, eval, ihs, iht]
  | mul s t ihs iht => simp [shiftTerm, eval, ihs, iht]

@[simp] theorem eval_shift_underBinder (t : Term) (v : Valuation) (n : Nat) :
    eval (Valuation.cons n v) (shiftTerm t 1) = eval v t := by
  rw [eval_shift]
  simp

/-- Semantic substitution lemma for terms. -/
theorem eval_subst (t : Term) (v : Valuation) (idx : Nat) (replacement : Term) :
    eval v (substTerm t idx replacement) =
      eval (Valuation.insert v idx (eval v replacement)) t := by
  induction t with
  | var i =>
      by_cases hlt : i < idx
      · simp [substTerm, eval, Valuation.insert, hlt]
      · by_cases heq : i = idx
        · subst i
          simp [substTerm, eval, Valuation.insert]
        · have hgt : idx < i := by omega
          simp [substTerm, eval, Valuation.insert, hlt, heq]
  | zero => rfl
  | succ t ih => simp [substTerm, eval, ih]
  | add s t ihs iht => simp [substTerm, eval, ihs, iht]
  | mul s t ihs iht => simp [substTerm, eval, ihs, iht]

end Term

namespace Formula

/-- Standard `Nat` semantics for first-order formulas. -/
def Holds (v : Valuation) : Formula -> Prop
  | .eq s t     => s.eval v = t.eval v
  | .bot        => False
  | .imp a b    => Holds v a -> Holds v b
  | .conj a b   => Holds v a ∧ Holds v b
  | .disj a b   => Holds v a ∨ Holds v b
  | .forallE a  => ∀ n : Nat, Holds (Valuation.cons n v) a
  | .existsE a  => ∃ n : Nat, Holds (Valuation.cons n v) a

/-- Formula shifting is semantically a valuation pullback. -/
theorem holds_shift (a : Formula) (v : Valuation) (amount cutoff : Nat) :
    Holds v (shiftFormula a amount cutoff) ↔
      Holds (Valuation.pullShift v amount cutoff) a := by
  induction a generalizing v cutoff with
  | eq s t => simp [shiftFormula, Holds, Term.eval_shift]
  | bot => simp [shiftFormula, Holds]
  | imp a b iha ihb => simp [shiftFormula, Holds, iha, ihb]
  | conj a b iha ihb => simp [shiftFormula, Holds, iha, ihb]
  | disj a b iha ihb => simp [shiftFormula, Holds, iha, ihb]
  | forallE a ih =>
      simp [shiftFormula, Holds, ih, Valuation.pullShift_cons]
  | existsE a ih =>
      simp [shiftFormula, Holds, ih, Valuation.pullShift_cons]

@[simp] theorem holds_shift_underBinder (a : Formula) (v : Valuation) (n : Nat) :
    Holds (Valuation.cons n v) (shiftFormula a 1) ↔ Holds v a := by
  rw [holds_shift]
  simp

/-- Formula-level semantic substitution. -/
theorem holds_subst (a : Formula) (v : Valuation) (idx : Nat)
    (replacement : Term) :
    Holds v (substFormula a idx replacement) ↔
      Holds (Valuation.insert v idx (replacement.eval v)) a := by
  induction a generalizing v idx replacement with
  | eq s t => simp [substFormula, Holds, Term.eval_subst]
  | bot => simp [substFormula, Holds]
  | imp a b iha ihb => simp [substFormula, Holds, iha, ihb]
  | conj a b iha ihb => simp [substFormula, Holds, iha, ihb]
  | disj a b iha ihb => simp [substFormula, Holds, iha, ihb]
  | forallE a ih =>
      simp [substFormula, Holds, ih, Term.eval_shift_underBinder,
        Valuation.insert_cons]
  | existsE a ih =>
      simp [substFormula, Holds, ih, Term.eval_shift_underBinder,
        Valuation.insert_cons]

/-- Opening slot zero is the familiar extension of a valuation. -/
@[simp] theorem holds_subst_zero (a : Formula) (v : Valuation) (replacement : Term) :
    Holds v (substFormula a 0 replacement) ↔
      Holds (Valuation.cons (replacement.eval v) v) a := by
  rw [holds_subst]
  simp

/-- The special successor instance used by `Ind` has the intended meaning. -/
theorem holds_successorInstance (motive : Formula) (v : Valuation) (n : Nat) :
    Holds (Valuation.cons n v) (successorInstance motive) ↔
      Holds (Valuation.cons (Nat.succ n) v) motive := by
  unfold successorInstance
  rw [holds_subst]
  simp only [Term.eval, Valuation.cons_zero, Valuation.insert_zero]
  rw [holds_shift]
  simp [Valuation.pullShift_cons]

end Formula

/-- Every formula in a context is true under the valuation. -/
def HoldsContext (v : Valuation) : Context -> Prop
  | []      => True
  | a :: xs => a.Holds v ∧ HoldsContext v xs

namespace HoldsContext

@[simp] theorem nil (v : Valuation) : HoldsContext v [] := trivial

@[simp] theorem cons {v : Valuation} {a : Formula} {ctx : Context} :
    HoldsContext v (a :: ctx) ↔ a.Holds v ∧ HoldsContext v ctx := Iff.rfl

/-- Lookup soundness for newest-first formula contexts. -/
theorem get? {v : Valuation} {ctx : Context} {i : Nat} {a : Formula}
    (hctx : HoldsContext v ctx) (hget : ctx[i]? = some a) : a.Holds v := by
  induction ctx generalizing i with
  | nil => simp at hget
  | cons head tail ih =>
      cases i with
      | zero =>
          simp at hget
          subst a
          exact hctx.1
      | succ i =>
          apply ih hctx.2
          simpa using hget

/-- Moving a context under a fresh term binder preserves and reflects truth. -/
theorem underTermBinder (v : Valuation) (n : Nat) (ctx : Context) :
    HoldsContext (Valuation.cons n v) (PeanoLab.underTermBinder ctx) ↔
      HoldsContext v ctx := by
  induction ctx with
  | nil => simp [PeanoLab.underTermBinder, HoldsContext]
  | cons a ctx ih =>
      change
        (Formula.Holds (Valuation.cons n v) (shiftFormula a 1) ∧
          HoldsContext (Valuation.cons n v) (PeanoLab.underTermBinder ctx)) ↔
        (Formula.Holds v a ∧ HoldsContext v ctx)
      constructor
      · intro h
        exact ⟨(Formula.holds_shift_underBinder a v n).mp h.1, ih.mp h.2⟩
      · intro h
        exact ⟨(Formula.holds_shift_underBinder a v n).mpr h.1, ih.mpr h.2⟩

end HoldsContext

end PeanoLab
