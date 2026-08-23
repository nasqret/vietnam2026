# Constructive full prime-block Lucas division congruence

Status: isolated, dependency-curried independently kernel-checked
Heyting-arithmetic proof bodies; no Alpha or Stable admission.

This tranche closes the complete one-step Lucas theorem for **arbitrary upper
and lower quotients**. The exact canonical endpoint is

```text
lucas_prime_block_digit_congruence:

Prime(p) -> d < p -> e < p ->
Choose(p*q+d, p*r+e, C) -> Choose(q,r,A) -> Choose(d,e,B) ->
ModEq(p, C, A*B).

Statement SHA-256:
fa40deb1530339b670f83de1cd151ea2d50e625cb9dbb931478e67405188aa81
```

Its equivalent division-witness interface is

```text
lucas_one_step_division_congruence:

Prime(p) -> n=p*q+d -> k=p*r+e -> d<p -> e<p ->
Choose(n,k,C) -> Choose(q,r,A) -> Choose(d,e,B) ->
ModEq(p,C,A*B).

Statement SHA-256:
6869973f7b42c48c4a298a4716e19bc4949c5a6a0aae9e41ded9a110ac7be71e
```

The proof is genuine induction on the upper quotient `q` with constructive
case analysis on whether the lower quotient `r` vanishes:

1. At `q=0,r=0`, the independently proved unrestricted low-digit theorem
   supplies the whole result.
2. At `q=0,r>0`, a checked order theorem proves `d < p*r+e`, forcing both
   the whole binomial and the upper quotient coefficient to be zero.
3. At `q=S(q'),r=0`, the same low-digit theorem handles all upper quotients.
4. At `q=S(q'),r=S(r')`, the independently checked high-column prime shift
   splits the coefficient into two predecessor coefficients. Both induction
   hypotheses apply; modular addition, exact Pascal recurrence, additive
   commutativity, and distributivity combine them into the quotient-times-
   digit product.

All relations expand into the original first-order natural language
`{0,S,+,*,=}`. No polynomial primitive, subtraction, classical axiom,
unverified computation, or release-evidence change is introduced.

Focused verification:

```bash
cd peano-lab/py
python3 -m pytest -q --tb=line tests/test_lucas_block_digit_candidate.py
```
