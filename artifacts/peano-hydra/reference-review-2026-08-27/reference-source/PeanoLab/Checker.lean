import PeanoLab.Derivation

/-!
# Verified executable reference checker

This is a fuelled transcription of the Python kernel's mutually recursive
`_infer` and `_check` functions.  The internal functions return not merely a
formula or Boolean, but a proof that the corresponding certificate judgment is
valid.  The ordinary API erases those witnesses.
-/

namespace PeanoLab

/-- A synthesized formula paired with a derivation witness. -/
structure Inferred (classical : Bool) (ctx : Context) (proof : Proof) : Type where
  formula : Formula
  derivation : Derives classical ctx proof formula

/-- A checked target paired with its derivation witness. -/
structure Checked (classical : Bool) (ctx : Context) (proof : Proof)
    (target : Formula) : Type where
  derivation : Derives classical ctx proof target

mutual

  /-- Verified synthesis for eliminations and annotated arithmetic forms. -/
  def inferVerified :
      (fuel : Nat) -> (classical : Bool) -> (ctx : Context) ->
      (proof : Proof) -> Option (Inferred classical ctx proof)
    | 0, _, _, _ => none
    | fuel + 1, classical, ctx, proof =>
      match proof with
      | .hyp i =>
          match hget : ctx[i]? with
          | some a => some ⟨a, .hyp hget⟩
          | none => none
      | .axiom name =>
          some ⟨axiomFormula name, .paAxiom⟩
      | .eqRefl t =>
          some ⟨.eq t t, .eqRefl⟩
      | .dne a =>
          match classical with
          | true =>
              some ⟨.imp (.imp (a.neg) .bot) a,
                .dne (by simp)⟩
          | false => none
      | .cut proposition conclusion lemma body =>
          match checkVerified fuel classical ctx lemma proposition,
              checkVerified fuel classical (proposition :: ctx) body conclusion with
          | some hlemma, some hbody =>
              some ⟨conclusion, .cut hlemma.derivation hbody.derivation⟩
          | _, _ => none
      | .impElim function argument =>
          match inferVerified fuel classical ctx function with
          | some ⟨.imp a b, hfun⟩ =>
              match checkVerified fuel classical ctx argument a with
              | some harg => some ⟨b, .impElim hfun harg.derivation⟩
              | none => none
          | _ => none
      | .andElimL pair =>
          match inferVerified fuel classical ctx pair with
          | some ⟨.conj a b, hpair⟩ => some ⟨a, .andElimL hpair⟩
          | _ => none
      | .andElimR pair =>
          match inferVerified fuel classical ctx pair with
          | some ⟨.conj a b, hpair⟩ => some ⟨b, .andElimR hpair⟩
          | _ => none
      | .forallElim universal term =>
          match inferVerified fuel classical ctx universal with
          | some ⟨.forallE a, hall⟩ =>
              some ⟨substFormula a 0 term, .forallElim hall⟩
          | _ => none
      | .eqSym p =>
          match inferVerified fuel classical ctx p with
          | some ⟨.eq s t, heq⟩ => some ⟨.eq t s, .eqSym heq⟩
          | _ => none
      | .eqTrans first second =>
          match inferVerified fuel classical ctx first,
              inferVerified fuel classical ctx second with
          | some ⟨.eq s t, hfirst⟩, some ⟨.eq t' u, hsecond⟩ =>
              if h : t = t' then
                by
                  subst t'
                  exact some ⟨.eq s u, .eqTrans hfirst hsecond⟩
              else none
          | _, _ => none
      | .congS p =>
          match inferVerified fuel classical ctx p with
          | some ⟨.eq s t, heq⟩ =>
              some ⟨.eq (.succ s) (.succ t), .congS heq⟩
          | _ => none
      | .congAdd left right =>
          match inferVerified fuel classical ctx left,
              inferVerified fuel classical ctx right with
          | some ⟨.eq s₁ t₁, hleft⟩, some ⟨.eq s₂ t₂, hright⟩ =>
              some ⟨.eq (.add s₁ s₂) (.add t₁ t₂), .congAdd hleft hright⟩
          | _, _ => none
      | .congMul left right =>
          match inferVerified fuel classical ctx left,
              inferVerified fuel classical ctx right with
          | some ⟨.eq s₁ t₁, hleft⟩, some ⟨.eq s₂ t₂, hright⟩ =>
              some ⟨.eq (.mul s₁ s₂) (.mul t₁ t₂), .congMul hleft hright⟩
          | _, _ => none
      | .eqSubst motive equation body =>
          match inferVerified fuel classical ctx equation with
          | some ⟨.eq s t, heq⟩ =>
              match checkVerified fuel classical ctx body (substFormula motive 0 s) with
              | some hbody =>
                  some ⟨substFormula motive 0 t, .eqSubst heq hbody.derivation⟩
              | none => none
          | _ => none
      | .ind motive base step =>
          match checkVerified fuel classical ctx base
              (substFormula motive 0 .zero),
              checkVerified fuel classical ctx step
                (.forallE (.imp motive (successorInstance motive))) with
          | some hbase, some hstep =>
              some ⟨.forallE motive, .ind hbase.derivation hstep.derivation⟩
          | _, _ => none
      | _ => none

  /-- Verified checking against a separately retained target formula. -/
  def checkVerified :
      (fuel : Nat) -> (classical : Bool) -> (ctx : Context) ->
      (proof : Proof) -> (target : Formula) ->
      Option (Checked classical ctx proof target)
    | 0, _, _, _, _ => none
    | fuel + 1, classical, ctx, proof, target =>
      match inferVerified fuel classical ctx proof with
      | some ⟨inferred, hderiv⟩ =>
          if h : inferred = target then
            by
              subst target
              exact some ⟨hderiv⟩
          else none
      | none =>
          match proof, target with
          | .impElim function argument, target =>
              match inferVerified fuel classical ctx argument with
              | some ⟨argumentType, _⟩ =>
                  match checkVerified fuel classical ctx function
                      (.imp argumentType target),
                      checkVerified fuel classical ctx argument argumentType with
                  | some hfun, some harg =>
                      some ⟨.impElim hfun.derivation harg.derivation⟩
                  | _, _ => none
              | none => none
          | .impIntro body, .imp a b =>
              match checkVerified fuel classical (a :: ctx) body b with
              | some hbody => some ⟨.impIntro hbody.derivation⟩
              | none => none
          | .andIntro left right, .conj a b =>
              match checkVerified fuel classical ctx left a,
                  checkVerified fuel classical ctx right b with
              | some hleft, some hright =>
                  some ⟨.andIntro hleft.derivation hright.derivation⟩
              | _, _ => none
          | .orIntroL p, .disj a b =>
              match checkVerified fuel classical ctx p a with
              | some hp => some ⟨.orIntroL hp.derivation⟩
              | none => none
          | .orIntroR p, .disj a b =>
              match checkVerified fuel classical ctx p b with
              | some hp => some ⟨.orIntroR hp.derivation⟩
              | none => none
          | .orElim disjunction leftCase rightCase, target =>
              match inferVerified fuel classical ctx disjunction with
              | some ⟨.disj a b, hdisj⟩ =>
                  match checkVerified fuel classical (a :: ctx) leftCase target,
                      checkVerified fuel classical (b :: ctx) rightCase target with
                  | some hleft, some hright =>
                      some ⟨.orElim hdisj hleft.derivation hright.derivation⟩
                  | _, _ => none
              | _ => none
          | .botElim absurdity, target =>
              match checkVerified fuel classical ctx absurdity .bot with
              | some hbot => some ⟨.botElim hbot.derivation⟩
              | none => none
          | .forallIntro body, .forallE a =>
              match checkVerified fuel classical (underTermBinder ctx) body a with
              | some hbody => some ⟨.forallIntro hbody.derivation⟩
              | none => none
          | .existsIntro term p, .existsE a =>
              match checkVerified fuel classical ctx p (substFormula a 0 term) with
              | some hp => some ⟨.existsIntro hp.derivation⟩
              | none => none
          | .existsElim existential body, target =>
              match inferVerified fuel classical ctx existential with
              | some ⟨.existsE a, hex⟩ =>
                  match checkVerified fuel classical
                      (a :: underTermBinder ctx) body (shiftFormula target 1) with
                  | some hbody => some ⟨.existsElim hex hbody.derivation⟩
                  | none => none
              | _ => none
          | _, _ => none

end

/-- Erased formula synthesis. -/
def infer (fuel : Nat) (classical : Bool) (ctx : Context) (proof : Proof) :
    Option Formula :=
  match inferVerified fuel classical ctx proof with
  | some ⟨a, _⟩ => some a
  | none => none

/-- Erased Boolean checking. -/
def check (fuel : Nat) (classical : Bool) (ctx : Context)
    (proof : Proof) (target : Formula) : Bool :=
  (checkVerified fuel classical ctx proof target).isSome

/-- Boolean acceptance always carries a derivation witness internally. -/
theorem check_derives {fuel : Nat} {classical : Bool} {ctx : Context}
    {proof : Proof} {target : Formula}
    (h : check fuel classical ctx proof target = true) :
    Derives classical ctx proof target := by
  unfold check at h
  cases hverified : checkVerified fuel classical ctx proof target with
  | none => simp [hverified] at h
  | some checked => exact checked.derivation

/-- Intuitionistic checking with explicitly supplied fuel. -/
def checkIntuitionisticWithFuel (fuel : Nat) (ctx : Context)
    (proof : Proof) (target : Formula) : Bool :=
  check fuel false ctx proof target

/-- Classical PA+DNE checking with explicitly supplied fuel. -/
def checkClassicalWithFuel (fuel : Nat) (ctx : Context)
    (proof : Proof) (target : Formula) : Bool :=
  check fuel true ctx proof target

/-- Intuitionistic checker with a certificate-size-derived fuel allowance. -/
def checkIntuitionistic (ctx : Context) (proof : Proof) (target : Formula) : Bool :=
  check proof.defaultFuel false ctx proof target

/-- Explicitly classical checker with a certificate-size-derived fuel allowance. -/
def checkClassical (ctx : Context) (proof : Proof) (target : Formula) : Bool :=
  check proof.defaultFuel true ctx proof target

/-- Public empty-context admission gate, including syntactic closure. -/
def checkClosed (proof : Proof) (target : Formula) : Bool :=
  target.wellScoped 0 && checkIntuitionistic [] proof target

/-- The public gate explicitly certifies syntactic closure of the target. -/
theorem checkClosed_wellScoped {proof : Proof} {target : Formula}
    (h : checkClosed proof target = true) :
    target.wellScoped 0 = true := by
  have hparts :
      target.wellScoped 0 = true ∧ checkIntuitionistic [] proof target = true := by
    simpa [checkClosed] using h
  exact hparts.1

/-- The public gate yields an empty-context intuitionistic derivation. -/
theorem checkClosed_derives {proof : Proof} {target : Formula}
    (h : checkClosed proof target = true) :
    Derives false [] proof target := by
  have hparts :
      target.wellScoped 0 = true ∧ checkIntuitionistic [] proof target = true := by
    simpa [checkClosed] using h
  apply check_derives
  simpa [checkIntuitionistic] using hparts.2

end PeanoLab
