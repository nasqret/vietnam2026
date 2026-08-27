import PeanoLab.Substitution

/-!
# Certificate calculus
-/

namespace PeanoLab

def Formula.neg (a : Formula) : Formula := .imp a .bot

inductive Derives : Bool -> Context -> Proof -> Formula -> Prop where
  | hyp (hget : ctx[i]? = some a) :
      Derives classical ctx (.hyp i) a
  | impIntro (hbody : Derives classical (a :: ctx) body b) :
      Derives classical ctx (.impIntro body) (.imp a b)
  | impElim (hfun : Derives classical ctx f (.imp a b))
      (harg : Derives classical ctx x a) :
      Derives classical ctx (.impElim f x) b
  | cut (hlemma : Derives classical ctx lemma proposition)
      (hbody : Derives classical (proposition :: ctx) body conclusion) :
      Derives classical ctx (.cut proposition conclusion lemma body) conclusion
  | andIntro (hleft : Derives classical ctx p a)
      (hright : Derives classical ctx q b) :
      Derives classical ctx (.andIntro p q) (.conj a b)
  | andElimL (hpair : Derives classical ctx p (.conj a b)) :
      Derives classical ctx (.andElimL p) a
  | andElimR (hpair : Derives classical ctx p (.conj a b)) :
      Derives classical ctx (.andElimR p) b
  | orIntroL (h : Derives classical ctx p a) :
      Derives classical ctx (.orIntroL p) (.disj a b)
  | orIntroR (h : Derives classical ctx p b) :
      Derives classical ctx (.orIntroR p) (.disj a b)
  | orElim (hdisj : Derives classical ctx p (.disj a b))
      (hleft : Derives classical (a :: ctx) leftCase target)
      (hright : Derives classical (b :: ctx) rightCase target) :
      Derives classical ctx (.orElim p leftCase rightCase) target
  | botElim (hbot : Derives classical ctx p .bot) :
      Derives classical ctx (.botElim p) target
  | forallIntro (hbody : Derives classical (underTermBinder ctx) body a) :
      Derives classical ctx (.forallIntro body) (.forallE a)
  | forallElim (hall : Derives classical ctx p (.forallE a)) :
      Derives classical ctx (.forallElim p t) (substFormula a 0 t)
  | existsIntro (hbody : Derives classical ctx p (substFormula a 0 t)) :
      Derives classical ctx (.existsIntro t p) (.existsE a)
  | existsElim (hex : Derives classical ctx p (.existsE a))
      (hbody : Derives classical (a :: underTermBinder ctx) body
        (shiftFormula target 1)) :
      Derives classical ctx (.existsElim p body) target
  | eqRefl : Derives classical ctx (.eqRefl t) (.eq t t)
  | eqSym (heq : Derives classical ctx p (.eq s t)) :
      Derives classical ctx (.eqSym p) (.eq t s)
  | eqTrans (h1 : Derives classical ctx p (.eq s t))
      (h2 : Derives classical ctx q (.eq t u)) :
      Derives classical ctx (.eqTrans p q) (.eq s u)
  | congS (heq : Derives classical ctx p (.eq s t)) :
      Derives classical ctx (.congS p) (.eq (.succ s) (.succ t))
  | congAdd (h1 : Derives classical ctx p (.eq s1 t1))
      (h2 : Derives classical ctx q (.eq s2 t2)) :
      Derives classical ctx (.congAdd p q)
        (.eq (.add s1 s2) (.add t1 t2))
  | congMul (h1 : Derives classical ctx p (.eq s1 t1))
      (h2 : Derives classical ctx q (.eq s2 t2)) :
      Derives classical ctx (.congMul p q)
        (.eq (.mul s1 s2) (.mul t1 t2))
  | eqSubst (heq : Derives classical ctx eqProof (.eq s t))
      (hbody : Derives classical ctx bodyProof (substFormula motive 0 s)) :
      Derives classical ctx (.eqSubst motive eqProof bodyProof)
        (substFormula motive 0 t)
  | dne (henabled : classical = true) :
      Derives classical ctx (.dne a) (.imp (.imp (a.neg) .bot) a)
  | paAxiom : Derives classical ctx (.axiom name) (axiomFormula name)
  | ind (hbase : Derives classical ctx base (substFormula motive 0 .zero))
      (hstep : Derives classical ctx step
        (.forallE (.imp motive (successorInstance motive)))) :
      Derives classical ctx (.ind motive base step) (.forallE motive)

end PeanoLab
