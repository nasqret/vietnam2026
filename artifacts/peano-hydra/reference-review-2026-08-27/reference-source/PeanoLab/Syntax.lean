/-!
# Peano Lab kernel syntax

A faithful algebraic model of the inert Python ASTs in `terms.py`,
`formulas.py`, and `proofs.py`.
-/

namespace PeanoLab

inductive Term where
  | var  : Nat -> Term
  | zero : Term
  | succ : Term -> Term
  | add  : Term -> Term -> Term
  | mul  : Term -> Term -> Term
  deriving Repr, DecidableEq

inductive Formula where
  | eq      : Term -> Term -> Formula
  | bot     : Formula
  | imp     : Formula -> Formula -> Formula
  | conj    : Formula -> Formula -> Formula
  | disj    : Formula -> Formula -> Formula
  | forallE : Formula -> Formula
  | existsE : Formula -> Formula
  deriving Repr, DecidableEq

abbrev Context := List Formula

namespace Term

def size : Term -> Nat
  | .var _   => 1
  | .zero    => 1
  | .succ t  => t.size + 1
  | .add s t => s.size + t.size + 1
  | .mul s t => s.size + t.size + 1

def wellScoped (depth : Nat) : Term -> Bool
  | .var i   => decide (i < depth)
  | .zero    => true
  | .succ t  => t.wellScoped depth
  | .add s t => s.wellScoped depth && t.wellScoped depth
  | .mul s t => s.wellScoped depth && t.wellScoped depth

end Term

namespace Formula

def size : Formula -> Nat
  | .eq s t     => s.size + t.size + 1
  | .bot        => 1
  | .imp a b    => a.size + b.size + 1
  | .conj a b   => a.size + b.size + 1
  | .disj a b   => a.size + b.size + 1
  | .forallE a  => a.size + 1
  | .existsE a  => a.size + 1

def wellScoped (depth : Nat) : Formula -> Bool
  | .eq s t     => s.wellScoped depth && t.wellScoped depth
  | .bot        => true
  | .imp a b    => a.wellScoped depth && b.wellScoped depth
  | .conj a b   => a.wellScoped depth && b.wellScoped depth
  | .disj a b   => a.wellScoped depth && b.wellScoped depth
  | .forallE a  => a.wellScoped (depth + 1)
  | .existsE a  => a.wellScoped (depth + 1)

end Formula

inductive AxiomName where
  | pa1 | pa2 | pa3 | pa4 | pa5 | pa6
  deriving Repr, DecidableEq

def axiomFormula : AxiomName -> Formula
  | .pa1 =>
      .forallE (.imp (.eq (.succ (.var 0)) .zero) .bot)
  | .pa2 =>
      .forallE (.forallE
        (.imp (.eq (.succ (.var 1)) (.succ (.var 0)))
              (.eq (.var 1) (.var 0))))
  | .pa3 =>
      .forallE (.eq (.add (.var 0) .zero) (.var 0))
  | .pa4 =>
      .forallE (.forallE
        (.eq (.add (.var 1) (.succ (.var 0)))
             (.succ (.add (.var 1) (.var 0)))))
  | .pa5 =>
      .forallE (.eq (.mul (.var 0) .zero) .zero)
  | .pa6 =>
      .forallE (.forallE
        (.eq (.mul (.var 1) (.succ (.var 0)))
             (.add (.mul (.var 1) (.var 0)) (.var 1))))

inductive Proof where
  | hyp          : Nat -> Proof
  | impIntro     : Proof -> Proof
  | impElim      : Proof -> Proof -> Proof
  | cut          : Formula -> Formula -> Proof -> Proof -> Proof
  | andIntro     : Proof -> Proof -> Proof
  | andElimL     : Proof -> Proof
  | andElimR     : Proof -> Proof
  | orIntroL     : Proof -> Proof
  | orIntroR     : Proof -> Proof
  | orElim       : Proof -> Proof -> Proof -> Proof
  | botElim      : Proof -> Proof
  | forallIntro  : Proof -> Proof
  | forallElim   : Proof -> Term -> Proof
  | existsIntro  : Term -> Proof -> Proof
  | existsElim   : Proof -> Proof -> Proof
  | eqRefl       : Term -> Proof
  | eqSym        : Proof -> Proof
  | eqTrans      : Proof -> Proof -> Proof
  | congS        : Proof -> Proof
  | congAdd      : Proof -> Proof -> Proof
  | congMul      : Proof -> Proof -> Proof
  | eqSubst      : Formula -> Proof -> Proof -> Proof
  | dne          : Formula -> Proof
  | axiom        : AxiomName -> Proof
  | ind          : Formula -> Proof -> Proof -> Proof
  deriving Repr, DecidableEq

namespace Proof

def size : Proof -> Nat
  | .hyp _             => 1
  | .impIntro p        => p.size + 1
  | .impElim f a       => f.size + a.size + 1
  | .cut _ _ lemma body => lemma.size + body.size + 1
  | .andIntro p q      => p.size + q.size + 1
  | .andElimL p        => p.size + 1
  | .andElimR p        => p.size + 1
  | .orIntroL p        => p.size + 1
  | .orIntroR p        => p.size + 1
  | .orElim p l r      => p.size + l.size + r.size + 1
  | .botElim p         => p.size + 1
  | .forallIntro p     => p.size + 1
  | .forallElim p _    => p.size + 1
  | .existsIntro _ p   => p.size + 1
  | .existsElim p q    => p.size + q.size + 1
  | .eqRefl _          => 1
  | .eqSym p           => p.size + 1
  | .eqTrans p q       => p.size + q.size + 1
  | .congS p           => p.size + 1
  | .congAdd p q       => p.size + q.size + 1
  | .congMul p q       => p.size + q.size + 1
  | .eqSubst _ p q     => p.size + q.size + 1
  | .dne _             => 1
  | .axiom _           => 1
  | .ind _ p q         => p.size + q.size + 1

def defaultFuel (p : Proof) : Nat := 8 * p.size + 16

end Proof

end PeanoLab
