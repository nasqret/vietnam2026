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
checked. Constructive [[prime_divisor_exists|prime-divisor existence]] is now
checked as well, through [[prime_or_composite]], [[proper_factor_lt]], and
formula-specific bounded descent.

The remaining spine begins with greatest-prime-divisor descent for the sorted
factor order. The encoding layer then needs binary and bounded CRT, β-value
existence/functionality, finite-prefix extension/restriction, prefix-product
trace existence/functionality/composition, preservation of bounded primality
and sorting, and finite-product Euclid/cancellation. None of those relations is
a trusted primitive, and the checked arithmetic prefix does not by itself
constitute [[fundamental-theorem-of-arithmetic|FTA]].

## Related

[[fundamental-theorem-of-arithmetic]] · [[trusted-kernel]] ·
[[arithmetic-library-moc]]
