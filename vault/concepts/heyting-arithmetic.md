---
title: Heyting arithmetic
tags: [logic, arithmetic, intuitionistic]
---

# Heyting arithmetic

**Heyting arithmetic (HA)** uses the language and nonlogical axioms of Peano arithmetic with
intuitionistic logic. Classical PA adds classical reasoning, for example double-negation
elimination.

Peano Lab runs constructively by default. Its ordinary checker accepts natural-deduction
certificates without a classical rule. A visible session switch may authorize an explicit DNE
certificate, which is checked only by the classical entry point. The mode is owned outside the
untrusted proof state, so a tactic cannot grant itself stronger logic.

HA and PA prove the same quantifier-free equations but differ on general formulas. The distinction
is pedagogically useful because it makes the logical substrate visible instead of treating
“classical” as an invisible global setting.

## Related

- [[intuitionistic-logic]]
- [[natural-deduction]]
- [[peano-lab]]
- [[trusted-kernel]]
