# Constructive multidigit Lucas digit-chain RFC v1

Status: **full constructive multidigit Lucas theorem kernel checked** as
twenty-three isolated, dependency-curried intuitionistic candidate bodies;
not admitted to Alpha or Stable. Every beta, bound, digit, coefficient, and
product abbreviation expands to the unchanged first-order language
`{0,S,+,*,=}`.

Implementation:
[`lucas_multidigit_candidate.py`](../../peano-lab/py/peano_lab/library/lucas_multidigit_candidate.py).
Focused audit:
[`test_lucas_multidigit_candidate.py`](../../peano-lab/py/tests/test_lucas_multidigit_candidate.py).

## Actual coherent finite base-p expansion

The central constructive relation is the actual beta-coded successive trace

```text
DigitChain(p,n,Qb,Qc,Db,Dc,l) :=
  BetaAt(Qb,Qc,0,n) and
  forall i<l. exists q q' d.
    BetaAt(Qb,Qc,i,q) and BetaAt(Qb,Qc,S(i),q') and
    BetaAt(Db,Dc,i,d) and q=p*q'+d and d<p.
```

Unlike pointwise division of an arbitrary unrelated source prefix, the next
source here is exactly the preceding quotient. Initial encoding, empty
chains, successor extension, and arbitrary finite existence are constructed
with existing beta-prefix extension and relational division. Prime-base
existence follows without a new sequence or digit primitive:

```text
lucas_digit_chain_exists:
  p != 0 -> exists Qb Qc Db Dc. DigitChain(p,n,Qb,Qc,Db,Dc,l).

lucas_prime_digit_chain_exists:
  Prime(p) -> exists Qb Qc Db Dc. DigitChain(p,n,Qb,Qc,Db,Dc,l).
```

Actual termination is proved, not postulated. Every nonzero next quotient is
strictly below its predecessor; induction on the digit index yields

```text
BetaAt(Qb,Qc,i,q) -> q != 0 -> q+i <= n.
```

Consequently any prime-base chain of length `l>n` has terminal quotient zero,
and `lucas_terminating_prime_digit_chain_exists` produces actual beta witnesses
for every such length. For two inputs `n,k`, the universal endpoint chooses
the explicit common length `S(n+k)`.

## Actual coefficient prefixes and modular finite-product fold

`lucas_choose_prefix_exists` constructs an actual beta-coded stream of
relational `Choose(a_i,b_i,D_i)` coefficients from any two beta-coded source
streams. Decoder functionality proves `lucas_choose_prefix_point`; this
connects independently supplied decoded inputs to their exact coefficient.

`lucas_modular_backward_product_fold` proves the complete constructive
finite-product principle

```text
Product(Db,Dc,l,P) ->
BetaAt(Cb,Cc,0,C) -> BetaAt(Cb,Cc,l,T) ->
(forall i<l. C_i == C_(i+1)*D_i (mod p)) ->
C == T*P (mod p).
```

The proof is ordinary induction on `l`, using checked beta-product successor
decomposition, congruence transitivity, and multiplication compatibility.

## Full unconditional Lucas theorem

The separately kernel-checked prime-block foundation
`lucas_one_step_division_congruence` establishes

```text
Prime(p) -> n=p*q+a -> k=p*r+b -> a<p -> b<p ->
Choose(n,k,C) -> Choose(q,r,A) -> Choose(a,b,D) ->
C == A*D (mod p).
```

This is a real checked dependency, not an axiom or open mathematical premise.
Combining it with both coherent quotient traces and both coefficient streams
proves `lucas_multidigit_congruence` for arbitrary finite prefixes, including
the exact residual terminal binomial. When both quotient traces terminate,
`Choose(0,0,T)` forces `T=1`, and
`lucas_terminating_multidigit_theorem` yields exactly

```text
Choose(n,k,C) == product_{i<l} Choose(n_i,k_i) (mod p).
```

The flagship is the genuinely universally quantified, unconditional theorem

```text
lucas_theorem:
  forall p n k C.
    Prime(p) -> Choose(n,k,C) ->
    exists l Qn_b Qn_c Dn_b Dn_c Qk_b Qk_c Dk_b Dk_c
             Coef_b Coef_c DigitCoef_b DigitCoef_c P.
      n<l and k<l and
      DigitChain(p,n,Qn_b,Qn_c,Dn_b,Dn_c,l) and
      DigitChain(p,k,Qk_b,Qk_c,Dk_b,Dk_c,l) and
      BetaAt(Qn_b,Qn_c,l,0) and BetaAt(Qk_b,Qk_c,l,0) and
      ChoosePrefix(Qn,Qk,Coef,S(l)) and
      ChoosePrefix(Dn,Dk,DigitCoef,l) and
      Product(DigitCoef_b,DigitCoef_c,l,P) and
      BetaAt(Coef_b,Coef_c,0,C) and C == P (mod p).
```

All displayed relation names above are explanatory only. The actual checked
root is a closed first-order formula with 38,430 characters and SHA-256
`396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564`.
Its proof has 149 structural nodes and depth 40. The common-length
constructor `lucas_theorem_for_length` has SHA-256
`855e865592946ebe0bd8f0856edb73bc521c2db254a730ccc3e4851384d21ebb`,
401 nodes, and depth 83. The unconditional terminating-stream theorem has
SHA-256
`89c221df26cc91d9a6de17522d2abf137bb1c11601fddf3fe212ab19b6c4b395`.

The focused audit freezes these flagship hashes, rejects false conclusions,
checks every independent body in the intuitionistic kernel with no `DNE`,
and verifies complete multidigit examples including out-of-range digits.
There is **no remaining mathematical gap in the full constructive Lucas
theorem**. Its evidence status remains isolated checked candidate bodies;
Alpha/Stable admission or closed-certificate promotion is separate release
engineering and is not implied.
