# Constructive Lucas theorem for an arbitrary upper quotient and one lower digit

Status: isolated, dependency-curried kernel candidates only; no Alpha or
Stable admission.

The first prime-block convolution tranche proves that for every unrestricted
natural row index `a` and bounded index `b < p`,

```text
Choose(p+a,b,C) -> Choose(a,b,D) -> C = D (mod p).
```

This tranche performs genuine natural induction on an arbitrary quotient
`q`, repeatedly applying that prime-block congruence. Its exact theorem is

```text
Prime(p) -> b < p ->
Choose(p*q+a,b,C) -> Choose(a,b,D) -> ModEq(p,C,D).
```

Specializing `a=d<p` gives the full Lucas formula whenever the lower integer
has only one digit, while its upper integer may have arbitrarily many digits:

```text
Prime(p) -> d<p -> e<p ->
Choose(p*q+d,e,C) -> Choose(q,0,A) -> Choose(d,e,B) ->
ModEq(p,C,A*B).
```

The factor `A` is constructively shown to equal one. There is no bounded
sampling assumption on `q`, no polynomial primitive, and no classical axiom.
The stronger arbitrary-lower-quotient case is separately completed by
`lucas_prime_block_digit_congruence` in the full prime-block tranche, using
the independently checked high-column prime-block congruence. This low-digit
factory itself proves exactly its advertised quotient-zero case.

Focused verification:

```bash
cd peano-lab/py
python3 -m pytest -q --tb=line tests/test_lucas_low_digit_candidate.py
```
