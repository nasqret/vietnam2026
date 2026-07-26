---
title: De Bruijn criterion
tags: [peano-lab, trust, kernel]
---

# De Bruijn criterion

The **De Bruijn criterion** says that a proof system should emit a proof object that a small,
independent checker can verify. It is an architectural criterion, not the same thing as using
de Bruijn *indices* to represent bound variables.

Peano Lab follows it literally. The tactic engine may perform search, mutate a temporary goal
state and use metavariables. At QED, however, the session owner gives the kernel three things:
the empty hypothesis context, the completed [[proof-certificate]], and the original stated
formula. Acceptance depends only on the small [[trusted-kernel]], never on the tactic's opinion
that no goals remain.

This boundary narrows what must be trusted, but it does not prove the checker correct or establish
the consistency of Peano arithmetic. Those are separate mathematical and engineering questions.

## Related

- [[peano-lab]]
- [[proof-certificate]]
- [[trusted-kernel]]
- [[substitution]]
