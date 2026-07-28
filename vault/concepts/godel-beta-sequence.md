---
title: Gödel beta sequence encoding
tags: [peano-arithmetic, sequence, arithmetization, factorization]
---

A finite natural-number sequence can be represented without adding a list sort
to Peano Lab. For code parameters $b,c$, index $i$, and value $x$, define

$$
M(c,i)=1+(i+1)c,
\qquad
\operatorname{At}(b,c,i,x)
\iff x<M(c,i)\land\exists q.\;b=qM(c,i)+x.
$$

All components expand to `0`, `S`, addition, multiplication, equality, and
quantifiers. A second beta sequence records prefix products. Bounded
`[[prime-number]]` conditions and sorted adjacent entries then define a
canonical finite prime factorization.

Codes are not sequence identities: two code pairs may decode the same finite
prefix. Extensional equality therefore compares length and every decoded
bounded entry. Natural [[quotient-and-remainder]] and [[euclids-lemma]] are now
checked. The remaining spine includes constructive prime-divisor existence,
binary and bounded CRT, β-value and finite-prefix extension/restriction
laws, prefix-product trace existence and composition, and finite-product
Euclid/cancellation results.

## Related

[[fundamental-theorem-of-arithmetic]] · [[trusted-kernel]] ·
[[arithmetic-library-moc]]
