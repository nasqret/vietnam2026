# Constructive Lucas one-digit foundations RFC v1

Status: nineteen isolated, independently kernel-checked, dependency-curried
intuitionistic candidate bodies. They are not enrolled in Alpha, admitted to
Stable, independently closed, or a proof of full multi-digit Lucas.

Date: 2026-08-23.

Implementation:
[`lucas_digit_candidate.py`](../../peano-lab/py/peano_lab/library/lucas_digit_candidate.py).
Focused audit:
[`test_lucas_digit_candidate.py`](../../peano-lab/py/tests/test_lucas_digit_candidate.py).

## Exact mathematical boundary

For a prime `p` and genuine base-`p` digits `a,b<p`, the full one-column
carry/divisibility classification is:

```text
Prime(p) -> a<p -> b<p -> Choose(a+b,a,C) ->
  ((p <= a+b) <-> p|C).

Prime(p) -> a<p -> b<p -> Choose(a+b,a,C) ->
  ((a+b < p) <-> ~(p|C)).
```

The complementary prime-row boundary is:

```text
Prime(p) -> k+j=p -> k<p -> j<p -> Choose(p,k,C) -> p|C.

Choose(p,0,C0) -> C0=1.
Choose(p,p,Cp) -> Cp=1.

Prime(p) -> k+j=p -> k<p -> j<p ->
  Choose(p,0,C0) -> Choose(p,p,Cp) -> Choose(p,k,C) ->
  (C0=1 and Cp=1 and p|C).
```

Thus the entire prime Pascal row is constructively sparse modulo its base:
its boundary coefficients are exactly one, while every interior coefficient
is divisible by the prime.

Every relation shown here is only explanatory notation: the actual statements
fully expand into the unchanged first-order language `{0,S,+,*,=}`. The
negative branch is an intuitionistic nondivisibility proof, not classical
double-negation elimination.

## Constructive proof architecture

The exact ordered candidate tranche is:

1. `lucas_digit_carry_implies_prime_divides` specializes the existing
   `choose_prime_divides_between` theorem to `n=a+b`, using the two exact
   digit bounds and the witnessed carry `p<=a+b`.
2. `lucas_prime_row_interior_divisible` applies that same checked theorem to
   the prime Pascal row `n=p` and uses constructive reflexivity `p<=p`.
3. `lucas_choose_prime_divisor_bound` proves the stronger reusable fact that
   every prime divisor of any relational `Choose(n,k,C)` is at most `n`.
   Constructive factorial existence and the exact factorial/Choose bridge
   transport `p|C` to `p|n!`; the existing prime-factorial bound then yields
   `p<=n`.
4. `lucas_digit_carry_iff_prime_divides` combines the first and third rows
   into the exact two-way one-digit carry characterization.
5. `lucas_digit_no_carry_iff_not_divides` uses constructive natural-order
   comparison and strict-order exclusion to prove the complementary
   no-carry iff nondivisibility characterization.
6. `lucas_base_p_digit_total` derives an actual quotient and strictly bounded
   least-significant digit for every nonzero base and natural input.
7. `lucas_prime_base_digit_total` specializes total digit extraction to all
   prime bases without assuming nonzeroness as an external premise.
8. `lucas_base_p_digit_functional` proves that both extracted coordinates,
   the quotient and bounded digit, are uniquely determined.
9. `lucas_base_p_digit_of_small_value` proves that inputs strictly below the
   base have quotient zero and themselves as canonical digits.
10. `lucas_base_p_zero_digit_iff_divides` proves exactly that a canonical
    least-significant digit is zero if and only if its input is divisible by
    the base, including the constructive negative branch.
11. `lucas_base_p_digit_prefix_exists` constructs genuine beta-coded
    quotient and digit prefixes for every beta-coded source prefix and every
    nonzero base.
12. `lucas_prime_base_digit_prefix_exists` constructs those two coded
    prefixes for arbitrary prime bases.
13. `lucas_base_p_digit_prefix_point` recovers the actual quotient/digit
    witnesses at any requested source index and proves their exact alignment
    using functionality of the existing beta decoder.
14. `lucas_base_p_two_digit_total` constructs two genuinely consecutive
    digits: the second digit is extracted from exactly the first quotient.
15. `lucas_prime_base_two_digit_total` specializes coherent two-digit
    extraction to every prime base.
16. `lucas_base_p_two_digit_reconstruction` proves exact natural-number
    reconstruction `n = (p*p)*q1 + (p*d1+d0)` from those two digits and the
    final quotient.
17. `lucas_prime_row_initial_coefficient_one` proves that the initial
    coefficient of the relational Pascal row is exactly one.
18. `lucas_prime_row_terminal_coefficient_one` proves that its terminal
    coefficient is exactly one.
19. `lucas_prime_row_sparse_complete` combines both exact boundary values
    with interior divisibility to prove the complete sparse prime-row
    package, rather than only a sampled computational example.

The original five proof bodies have respectively 43, 48, 57, 69, and 61
structural nodes; the eight new digit-extraction bodies have respectively
15, 25, 58, 57, 76, 25, 35, and 57 nodes, followed by coherent two-digit
bodies with 27, 25, and 55 nodes and sparse prime-row bodies with 15, 15,
and 67 nodes. The largest complete body has 76 nodes and maximum depth 34.
The exact carry endpoint statement has
SHA-256 `f2a21464f86d511c8d99ac535cb4029fa135d2bd3b6374493fdffbd347dd0f50`;
the no-carry endpoint has SHA-256
`9a74ff6b08f258fd917297aa5bc1f2f04d419554b0f5896e5f7ea363a8c61d30`.
The exact zero-digit/divisibility endpoint has SHA-256
`6cdd9024b8eaa32e34721d770a94d73fad56bb1a4afa39b8dd1f31893ce6a538`;
the exact pointwise beta-prefix digit alignment endpoint has SHA-256
`4217c5f9ca75041c820053c41665d23687ad3a48f588cd7e05abfa719d8f1ff0`.
The coherent two-digit reconstruction endpoint has SHA-256
`c81452d56a730c9291f6bcb1f8e4eb39f45e8aead52c465c9ac54249e440ed2d`.
The complete sparse prime Pascal-row endpoint has SHA-256
`f0804ab6b8a14d05793a9d026a4ffe360d205f67312476099e22e02a7b3c5e8c`.

The focused audit freezes all nineteen formulas, direct dependencies, proof
receipts, and intuitionistic certificates. It rejects false targets and
individually deleted dependency edges, audits for absence of `DNE`, and
independently checks every digit pair for several prime moduli. Additional
examples check total quotient/digit extraction, both coordinate uniqueness,
small-input normalization, zero-digit divisibility, aligned finite quotient
and digit prefixes, coherent two-digit reconstruction, and the sparse prime
Pascal row. Composite-base
counterexamples confirm the prime premise is essential.

## Exact first-order digit and beta-prefix surfaces

The native digit graph is conservative authoring notation only:

```text
Digit(p,n,q,d) := (n = p*q+d) and (exists h. h+S(d)=p).
```

The nineteen checked rows prove, in particular:

```text
p != 0 -> exists q d. Digit(p,n,q,d).

Digit(p,n,q,d) -> Digit(p,n,Q,D) -> q=Q and d=D.

Digit(p,n,q,d) -> (d=0 <-> exists k. n=p*k).

p != 0 -> exists qb qc db dc.
  forall i. i<l -> exists n q d.
    BetaAt(b,c,i,n) and BetaAt(qb,qc,i,q) and
    BetaAt(db,dc,i,d) and Digit(p,n,q,d).

p != 0 -> exists q0 d0 q1 d1.
  Digit(p,n,q0,d0) and Digit(p,q0,q1,d1).

Digit(p,n,q0,d0) -> Digit(p,q0,q1,d1) ->
  n = (p*p)*q1 + (p*d1+d0).
```

The beta-coded prefixes are real existing first-order witnesses, not
host-language arrays. Pointwise source functionality transports a supplied
decoded source value to its exact quotient and bounded digit.

## Integration with the completed Lucas theorem and release boundary

The exact general Lucas endpoint is:

```text
Choose(n,k,C) -> Digits_p(n,N) -> Digits_p(k,K) ->
  C congruent modulo p to the product of Choose(N_i,K_i).
```

Single-step digit extraction, functionality, beta-coded aligned digit
prefixes, coherent two-step extraction/reconstruction, and complete sparse
prime Pascal rows form the foundation. Subsequent independently checked
tranches now construct *arbitrarily long* coherent beta-coded quotient/digit
chains, prove their actual finite termination, construct aligned binomial
coefficient streams, prove both prime-block Pascal congruences and the full
unrestricted one-step Lucas identity, and fold the digit coefficients into
the complete unconditional multidigit congruence. No polynomial primitive is
required.

This foundation module by itself proves the full one-digit vanishing/carry
boundary and its exact digit substrate, not the full multi-digit Lucas
theorem; the combined campaign proves the latter at the dependency-curried
candidate-body layer. Neither candidate proof bodies nor this document
change sealed Alpha-v12 or Stable evidence.
