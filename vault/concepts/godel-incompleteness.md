---
title: Gödel incompleteness
tags: [logic, peano-arithmetic, limits]
---

# Gödel incompleteness

Gödel's first incompleteness theorem implies, under the usual effectiveness, consistency and
arithmetic-strength hypotheses, that no recursively axiomatized system such as PA proves every
arithmetical truth. The second theorem says that a sufficiently strong consistent system cannot
prove its own consistency in the expected internal form.

This matters for [[peano-lab]] in two different ways. No search depth can turn the lab into a
complete prover for PA, and a small [[trusted-kernel]] cannot certify its own correctness merely by
accepting many certificates. A bounded `auto` result of “limit reached” is therefore a resource
report, never evidence that a formula is false or unprovable.

The lesson is restraint: machine checking gives a precise conditional guarantee—this certificate
follows from these rules—not an oracle for all mathematical truth.

## Related

- [[proof-certificate]]
- [[trusted-kernel]]
- [[intuitionistic-logic]]
