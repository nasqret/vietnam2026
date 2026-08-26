# RFC FS01: constructive four-square identity foundations

**Status:** isolated Stage-4 preparation; dependency-curried candidate bodies
only, not Alpha admission, a closed Euler identity, or Lagrange's theorem.

## Representation and exact quaternion coordinates

For natural inputs `(a,b,c,d)` and `(e,f,g,h)`, Hamilton multiplication has
four possibly signed coordinates with the following positive/negative
contributions:

```text
u = a*e - (b*f + c*g + d*h)
v = (a*f + b*e + c*h) - d*g
w = (a*g + c*e + d*f) - b*h
x = (a*h + b*g + d*e) - c*f
```

Subtraction is not an object-language operation. Each coordinate is instead
represented by the existing conservative `SignedBalance(code,P,N)` graph,
expanded into `{0,S,+,*,=}` using the canonical parity-interleaved decoder.
The already established `signed_balance_total` theorem constructs all four
codes, and decoder normalization supplies natural absolute magnitudes with
the explicit disjunction `P = N + magnitude \/ N = P + magnitude`.

The isolated factory
`peano-lab/py/peano_lab/library/four_square_identity_candidate.py` develops:

1. `signed_square_cross_term_zero`: normalized decoded sign components have
   product zero;
2. `signed_square_magnitude_expands`: their natural magnitude squared is the
   sum of their component squares;
3. `signed_balance_absolute_exists`: a balanced signed coordinate has a
   constructive absolute magnitude and sign choice;
4. `four_square_norm_distributes`: the product of two four-square norms
   expands to four independently bounded square-times-norm blocks;
5. `quaternion_coordinate_balance_total`: all four Hamilton coordinates have
   canonical signed-natural witnesses;
6. `quaternion_coordinate_absolute_total`: all four Hamilton coordinates have
   natural absolute-magnitude witnesses.
7. `four_square_add_swap_right_tail`: adjacent summands swap while preserving
   their shared tail;
8. `four_square_additive_gap_reorder`: the five square-gap contributions are
   reordered by small certified additive steps;
9. `four_square_sum_expansion`: `(a+b)^2` expands into its two diagonal and
   two ordered cross terms;
10. `four_square_gap_balance_right`: the larger-first signed gap satisfies its
    exact square/cross-term correction;
11. `four_square_gap_balance_left`: the smaller-first orientation satisfies
    the same constructive correction;
12. `four_square_absolute_square_balance`: both absolute-difference cases
    satisfy `P*P+N*N=m*m+(P*N+N*P)`;
13. `signed_balance_square_transport`: canonical signed balance yields an
    explicit magnitude, a sign decision, and that exact square correction;
14. `four_square_product_shuffle`: `(a*b)*(c*d)=(a*c)*(b*d)` exchanges the
    middle factors needed by Euler cross-term cancellation;
15. `four_square_product_square`: `(a*b)^2=(a*a)*(b*b)`;
16. `quaternion_coordinate_square_transport`: each of the four Hamilton
    coordinates satisfies its individual square/cross-term correction;
17. `quaternion_coordinate_square_balance_total`: all four absolute
    magnitudes and all four exact square/cross-term corrections exist
    together.
18. `four_square_absolute_difference_total`: canonical signed-coordinate
    totality constructively supplies an absolute-difference witness for every
    pair of naturals;
19. `four_square_two_square_factor_identity`: two independent checked
    Brahmagupta compositions prove the exact six-variable Euler subclass
    whose right factor is a two-square norm;
20. `four_square_two_square_factor_total`: constructive absolute differences
    produce all four natural coordinate witnesses for that subclass.

All statements are fully expanded first-order formulas. Candidate validation
checks ordinary intuitionistic proof certificates for dependency-curried
statements; neither theorem names nor host arithmetic are trusted. The
two-square-factor subclass explicitly curries the independently checked,
still-isolated `brahmagupta_fibonacci_two_square_identity` candidate: it does
not treat that external candidate as an admitted Alpha or Stable theorem.

## Checked six-variable Euler subclass and explicit witnesses

For natural inputs `(a,b,c,d)` and `(e,f)`, the following proper subclass of
Euler's identity is now fully checked in the first-order kernel:

```text
(a*a+b*b+c*c+d*d) * (e*e+f*f)
  = (a*e+b*f)^2 + |a*f-b*e|^2
    + (c*e+d*f)^2 + |c*f-d*e|^2.
```

Object-language subtraction, absolute value, and exponentiation do not
occur: each absolute difference is an explicitly constructed natural witness
for its two-branch addition equation, and every square is ordinary
multiplication. Distribution first splits the left four-square norm into two
two-square blocks; the separately kernel-checked Brahmagupta identity proves
each block. The total theorem constructs the four coordinates

```text
a*e+b*f,
|a*f-b*e|,
c*e+d*f,
|c*f-d*e|.
```

Thus a four-square representation is constructively preserved under
multiplication by any represented two-square number. This is not the full
eight-variable Euler identity: both right-hand input coordinates `g,h` must
still be zero for this special case.

## Checked signed-square transport and exact remaining identity gap

The entire per-coordinate transport is now proved constructively.  For every
canonical signed coordinate with positive/negative contributions `P,N`, an
explicit natural `m` satisfies one of the witnessed branches

```text
P = N + m  \/  N = P + m
```

and, in either case, the exact subtraction-free equation

```text
P*P + N*N = m*m + (P*N + N*P).
```

The four-coordinate endpoint packages these eight obligations simultaneously.
All algebra is split into small separately checked associativity,
distributivity, and commutativity lemmas; no monolithic polynomial
normalizer is used.

The missing theorem is now the **global quaternion cross-term cancellation**
linking the four already transported coordinates to the norm product:

```text
(a*a+b*b+c*c+d*d) * (e*e+f*f+g*g+h*h)
  = m0*m0 + m1*m1 + m2*m2 + m3*m3.
```

Its remaining subtraction-free intermediate is the natural polynomial identity

```text
norm(a,b,c,d) * norm(e,f,g,h) + 2 * sum(P_i * N_i)
  = sum(P_i * P_i + N_i * N_i),
```

followed by ordinary additive cancellation against the four already checked
coordinate-square equations. A monolithic polynomial normalizer exceeds the
intentionally bounded local work envelope; the proper continuation is a
factored sequence of independently checked four-coordinate contribution
identities using `four_square_product_shuffle`.

Even after that identity closes, Lagrange's theorem still requires a bounded
four-square multiple for every prime, strictly decreasing constructive
descent, and composition through prime factorization. None of those results
is claimed by this preparation tranche.

Run the focused, isolated checks with:

```text
cd peano-lab/py
python3 -m pytest -q tests/test_four_square_identity_candidate.py
```
