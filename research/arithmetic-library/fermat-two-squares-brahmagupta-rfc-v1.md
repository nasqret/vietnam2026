# Constructive Brahmagupta--Fibonacci two-square multiplication

Status: ten isolated, independently kernel-checked, dependency-curried
intuitionistic proof bodies; not enrolled in Alpha, not admitted to Stable,
and not a complete all-integer classification.

The exact flagship first-order endpoint is:

```text
forall m n.
  (exists a b. m = a*a + b*b) ->
  (exists c d. n = c*c + d*d) ->
  exists x y. m*n = x*x + y*y.
```

Its theorem name is
`two_square_representations_closed_under_multiplication` and its statement
SHA-256 is
`d61118c9dc3c758b428cb70af7d9e920b082f28467776463c20363f0633b468e`.

## Constructive witnesses

For given natural coordinates `a,b,c,d`, the first output coordinate is
explicitly `x = a*c + b*d`. Constructive total natural order supplies a
witnessed magnitude `y` and one of the genuinely decided alternatives:

```text
a*d = b*c + y     or     b*c = a*d + y.
```

The two alternatives separately imply the exact natural identity

```text
(a*a + b*b) * (c*c + d*d) = x*x + y*y.
```

Thus the ordinary notation `y = |a*d-b*c|` describes a real existential
natural witness; subtraction and absolute value are not kernel primitives.
The proof neither imports classical excluded middle nor infers existence
from a host-language example.

## Exact dependency-ordered proof tranche

1. `two_square_add_left_comm`.
2. `two_square_mul_left_comm`.
3. `two_square_cross_products_equal`.
4. `two_square_product_norm_expanded`.
5. `two_square_balanced_difference_identity`.
6. `two_square_product_difference_forward`.
7. `two_square_product_difference_reverse`.
8. `two_square_product_explicit_witness`.
9. `two_square_product_is_two_square`.
10. `two_square_representations_closed_under_multiplication`.

All statements expand into `{0,S,+,*,=}`. The largest dependency-curried
certificate contains 338 structural proof nodes and has depth at most 71.
Focused tests freeze the statement hashes, actual kernel certificates,
proof-envelope receipts, essential dependency mutations, absence of `DNE`,
and 6,561 independent witness examples covering positive, negative, and zero
difference branches.

Implementation:
[`fermat_two_squares_brahmagupta_candidate.py`](../../peano-lab/py/peano_lab/library/fermat_two_squares_brahmagupta_candidate.py).
Audit:
[`test_fermat_two_squares_brahmagupta_candidate.py`](../../peano-lab/py/tests/test_fermat_two_squares_brahmagupta_candidate.py).

Together with the separately checked constructive prime theorem, this closes
the explicit multiplicative-composition gate for the eventual Fermat
two-square classification. The converse for primes congruent to three modulo
four, even valuation transport through factorization, independent
empty-context closure, and versioned release admission remain open.
