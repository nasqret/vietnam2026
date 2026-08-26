# Constructive two-square factor folds and explicit prime pairing

This isolated tranche contributes **13 independently kernel-checked,
dependency-curried first-order Heyting-arithmetic candidate bodies**.  It
closes the represented-factor folding step, proves a genuine adjacent-pair
collapse for raw beta-coded products, and derives an unconditional sufficient
condition using canonical prime factorization.  It does not establish the
full valuation criterion or modify Alpha, Stable, or the theorem registry.

## 1. Generic represented-factor product

Write `BetaAt`, `Product`, and `TwoSquare` as conservative display
abbreviations; all candidate statements expand them into `{0,S,+,*,=}`.
The main induction theorem is exactly

```text
beta_two_square_represented_factor_product:
  forall b c l n.
    Product(b,c,l,n) ->
    (forall i a. i < l -> BetaAt(b,c,i,a) ->
      exists x y. a = x*x + y*y) ->
    exists x y. n = x*x + y*y.
```

Its SHA-256 statement identity is
`66d4cf4c158802e854386ea6f68e565c64d34c1e3e0be7185c3d95782c833929`.
The checked body has five dependencies, **106 proof nodes**, and proof depth
**26**.  The zero-length case constructs `1 = 1²+0²`.  The successor case
uses the existing checked beta-product decomposition, restricts the prefix,
extracts the final factor representation, and invokes the constructive
Brahmagupta multiplicative-closure theorem.

The companion `beta_witnessed_two_square_factor_product` accepts the more
direct premise

```text
forall i < l. exists a x y.
  BetaAt(b,c,i,a) and a = x*x+y*y.
```

Beta-decoding uniqueness aligns its existentially selected factor with the
factor supplied by the actual product decomposition.

## 2. Actual adjacent equal-factor pairing

The raw-prefix bridge is not merely an arithmetic analogy.  It is an
independently kernel-checked exact beta-product theorem:

```text
beta_product_adjacent_equal_pair_decomposes_as_square:
  forall b c l n q.
    Product(b,c,S(S l),n) ->
    BetaAt(b,c,l,q) ->
    BetaAt(b,c,S l,q) ->
    exists r. Product(b,c,l,r) and n = r*(q*q).
```

Its SHA-256 statement identity is
`764f04f04f5e218f9ecbd4a11821fa06fa22877dc00dc5d533f2ab72099cf0bb`.
It has three dependencies, **78 proof nodes**, and proof depth **30**.
Successive checked product decompositions expose the last two factors; beta
uniqueness identifies both with `q`, and multiplication associativity gives
the exact square cofactor.

`beta_two_square_prefix_append_equal_pair` then proves that any already
represented shorter prefix remains represented after adjoining the equal raw
pair.  Its SHA-256 statement identity is
`3424623feb8013a0d62b80f2f4f05e60f826c94685584f45fb74be0d52b8dd69`.
The result does not require `q` to be prime and therefore includes the
classical repeated-prime case.

The additional theorem
`beta_grouped_prime_square_factor_product_is_two_square` folds a separate
beta-coded list of blocks where each block is explicitly either

```text
Prime(p) and (p=2 or p=1 mod 4),
```

or

```text
p=q*q,  Prime(q),  q=3 mod 4.
```

Its statement identity is
`01d0e9f98fa4f55a8b1ff4958ce1c5436c756be7e1e3b29dedf7705a85eeb20f`.
The block list and any conversion to it must be explicitly witnessed.

## 3. Canonical factorization corollary

The strongest premise-free factorization assembly in this tranche is

```text
positive_number_with_admissible_prime_divisors_is_two_square:
  forall n.
    n != 0 ->
    (forall p.
      Prime(p) -> (exists k. n=p*k) ->
      (p=2 or exists t. p=4*t+1)) ->
    exists x y. n=x*x+y*y.
```

Its statement SHA-256 is
`4f1877c55982623acfdc8c10d6244f00d0c97073e3701854c9f1243ce665fce1`.
The checked body has four dependencies, **76 proof nodes**, and depth **27**.
The existing checked canonical prime-factorization existence theorem
supplies the actual beta-coded product and prime prefix; uniqueness of beta
decoding identifies each concrete factor as prime, and checked factor
divisibility applies the hypothesis on prime divisors.

The separate theorem `represented_factor_product_times_square_is_two_square`
allows an arbitrary explicitly witnessed square cofactor.  Thus a supplied
decomposition into an admissible represented core and a square already gives
constructive witnesses for the complete number.

## 4. Relationship to the completed classification and release boundary

This tranche does **not** prove that even power valuations of every
three-modulo-four prime imply a canonical adjacent-pair partition, a grouped
square-block beta list, or a square-times-admissible-core decomposition.
The separate valuation tranche proves the necessity direction by iterated
constructive descent in
`three_mod_four_prime_represented_nonzero_valuation_even`.  The subsequent
pairing-and-descent tranche closes sufficiency by bounded induction directly
on the natural value, so a canonical adjacent-pair partition is not required
for the full classification.  Its checked endpoints are
`nonzero_two_square_iff_even_three_mod_four_prime_valuations` and
`two_square_iff_zero_or_even_three_mod_four_prime_valuations`.  The optional
factorization-to-canonical-pairing route remains separate; the all-natural
two-square iff itself is complete at the dependency-curried body level.

All 13 bodies are dependency-curried and individually kernel checked.  The
largest proof has **106 nodes**; maximum proof depth is **30**.  Focused
verification is:

```bash
cd peano-lab/py
python3 -m pytest -q --tb=line \
  tests/test_fermat_two_squares_factor_fold_candidate.py
```

Independent empty-context closure, cold replay, Alpha enrollment, Stable
promotion, and publication remain separate gates.
