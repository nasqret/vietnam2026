import PeanoLab.Syntax

/-!
# Capture-avoiding de Bruijn operations
-/

namespace PeanoLab

def shiftTerm (t : Term) (amount : Nat) (cutoff : Nat := 0) : Term :=
  match t with
  | .var i   => if cutoff <= i then .var (i + amount) else .var i
  | .zero    => .zero
  | .succ u  => .succ (shiftTerm u amount cutoff)
  | .add s u => .add (shiftTerm s amount cutoff) (shiftTerm u amount cutoff)
  | .mul s u => .mul (shiftTerm s amount cutoff) (shiftTerm u amount cutoff)

def shiftFormula (a : Formula) (amount : Nat) (cutoff : Nat := 0) : Formula :=
  match a with
  | .eq s t     => .eq (shiftTerm s amount cutoff) (shiftTerm t amount cutoff)
  | .bot        => .bot
  | .imp p q    => .imp (shiftFormula p amount cutoff) (shiftFormula q amount cutoff)
  | .conj p q   => .conj (shiftFormula p amount cutoff) (shiftFormula q amount cutoff)
  | .disj p q   => .disj (shiftFormula p amount cutoff) (shiftFormula q amount cutoff)
  | .forallE p  => .forallE (shiftFormula p amount (cutoff + 1))
  | .existsE p  => .existsE (shiftFormula p amount (cutoff + 1))

def substTerm (t : Term) (idx : Nat) (replacement : Term) : Term :=
  match t with
  | .var i =>
      if i < idx then .var i
      else if i = idx then replacement
      else .var (i - 1)
  | .zero    => .zero
  | .succ u  => .succ (substTerm u idx replacement)
  | .add s u => .add (substTerm s idx replacement) (substTerm u idx replacement)
  | .mul s u => .mul (substTerm s idx replacement) (substTerm u idx replacement)

def substFormula (a : Formula) (idx : Nat) (replacement : Term) : Formula :=
  match a with
  | .eq s t     => .eq (substTerm s idx replacement) (substTerm t idx replacement)
  | .bot        => .bot
  | .imp p q    => .imp (substFormula p idx replacement) (substFormula q idx replacement)
  | .conj p q   => .conj (substFormula p idx replacement) (substFormula q idx replacement)
  | .disj p q   => .disj (substFormula p idx replacement) (substFormula q idx replacement)
  | .forallE p  =>
      .forallE (substFormula p (idx + 1) (shiftTerm replacement 1))
  | .existsE p  =>
      .existsE (substFormula p (idx + 1) (shiftTerm replacement 1))

def underTermBinder (ctx : Context) : Context :=
  ctx.map (fun a => shiftFormula a 1)

def successorInstance (motive : Formula) : Formula :=
  substFormula (shiftFormula motive 1 1) 0 (.succ (.var 0))

end PeanoLab
