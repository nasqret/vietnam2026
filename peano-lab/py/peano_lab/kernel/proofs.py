"""Proof terms (certificates): one constructor per ND rule + PA axioms + IND.

Constructors (design §1): Hyp(i), ImpIntro(body), ImpElim(f, a), AndIntro/Elim,
OrIntroL/R, OrElim, BotElim, ForallIntro(body), ForallElim(p, t),
ExistsIntro(t, p), ExistsElim(p, body), EqRefl(t), EqSym, EqTrans, CongS/Add/Mul,
EqSubst(motive, eq_proof, body_proof), Axiom(name in PA1..PA6), Ind(motive, base, step).
"""

raise NotImplementedError("M0")
