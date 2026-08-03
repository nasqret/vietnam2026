---
title: Decidable proof fragment
tags: [logic, decidability, heyting-arithmetic, peano-lab]
---

# Decidable proof fragment

A **decidable proof fragment** has a frozen grammar and semantics together with
a terminating procedure that correctly returns both theorem and non-theorem
answers. A finite benchmark or bounded proof search is not by itself such a
procedure.

For [[peano-hydra]], the fragment profile binds syntax, substitution,
intuitionistic rules, arithmetic axioms, induction policy, normal forms,
translations, and positive/negative evidence formats. A timeout is `unknown`.
Without independently checkable negative evidence or agreement with a
separately implemented reference decision procedure, the correct description
is a sound theorem prover rather than a decider.

This distinction prevents a result for a custom decidable language from being
misreported as decidability of standard [[heyting-arithmetic]].

## Related

- [[trusted-kernel]]
- [[intuitionistic-logic]]
- [[kernel-judged-evaluation]]
- [[peano-lab-moc]]
