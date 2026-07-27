---
title: Checked commutative-semiring basis
tags: [peano-lab, arithmetic, proof-certificate, theorem-library]
---

Peano Lab's polynomial normalizer may compute a canonical form, but computation alone is never a
proof. Its algebraic steps must be justified by closed certificates from the [[theorem-ladder]].

The M7 core already supplies the zero laws, addition and multiplication associativity and
commutativity, and `mul_add`. M11 adds only the missing orientations: `one_mul`, `mul_one`, and
`add_mul`. Together these form the checked commutative-semiring basis; numerals remain iterated
successors, and closed coefficient arithmetic constructs PA3–PA6 certificates.

All three additions are ordinary library scripts. They replay from the empty context and remain
capture-safe when [[checked-theorem-reuse]] imports and specializes them below term and proposition
binders. M12's [[polynomial-normalization]] rechecks the same closed certificates before using them
to construct an equality proof. The [[trusted-kernel]] knows none of their names.

## Related

[[theorem-ladder]] · [[proof-certificate]] · [[polynomial-normalization]] · [[normal-form]] ·
[[tactic-mode]]
