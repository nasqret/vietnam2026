# Recursive normalized polynomial gcd and Bézout

Verified local extension of the 95-row Euclidean checkpoint. The source
contains nine ordinary Heyting-arithmetic proof scripts, now included in the
dependency-complete [119-row gcd checkpoint](../prime-field-gcd-closure-v1/README.md).
Its exact bundle passed original HA and the independent same-byte Lean check;
all 14 principal roots passed ordinary empty-context HA. This family's 86
focused cases also passed: 53 source/model, nine positive native bodies, and
24 rejection cases.

## Exact scope

For every prime `p` and two canonical coefficient representations `A,B`,
construct actual representations `G,U,V` satisfying

```text
FpPolynomialNormalizedGcd(p,G,A,B)
and FpPolynomialBezoutRepresentation(p,A,B,G,U,V).
```

Here `A`, `B`, and every other polynomial abbreviate three actual natural
arguments: beta code, beta scale, and length. The named statements expand
conservatively to the same core arithmetic formulas as the existing library.
No external gcd, division procedure, irreducibility oracle, or termination
certificate is an assumption.

`NormalizedGcd` means that `G` is empty or monic, divides both inputs, and is
divided by every common divisor of them. Bézout means that there are actual
products `U*A`, `V*B`, and an aligned sum formally equivalent to `G`.
Uniqueness, in the adjoining uniqueness family, is equality of all formal
coefficients. It is not equality of beta encodings, nor uniqueness of `U,V`.

## Constructive argument

Induct on a bound for the length of the second representation, with **both**
inputs universally quantified inside the induction predicate.

1. Trim the second input. A nonempty stored prefix can still represent zero,
   so a nonempty list alone does not justify dividing by its leading entry.
2. If it trims to empty, construct a zero-or-monic associate of the first
   input. Its actual mutual-divisibility witnesses supply the terminal Bézout
   coefficient; the other coefficient is empty. This includes `(0,0)`.
3. Otherwise its represented degree is `d`, its length is `d+1`, and actual
   division constructs `A=Q*T+R` with remainder length at most `d`. This proves
   the bound required by the recursive call on `(T,R)`.
4. If that call supplies `G=U*T+V*R`, carry the same normalized `G` back using
   the actual products and difference `G=V*A+(U-V*Q)*T`. Transport from the
   trimmed second representation to the original one by formal equivalence.
5. Every common divisor of the inputs divides the two products and their
   aligned sum. This supplies the universal greatestness clause.

For example, in `F_5[X]`, the two Euclidean steps for `X^3-1, X^2-1`
produce the normalized gcd `X-1`; the explicit Bézout identity is
`(X^3-1)-X*(X^2-1)=X-1`. Tests construct the actual beta-coded divisions,
products, remainders, and aligned sums for this example.

## Files and evidence

- `prime_field_polynomial_gcd_existence_candidate.py`: exact expanded
  contracts, hygienic public relation builders, and ordinary proof scripts.
- `test_prime_field_polynomial_gcd_existence_candidate.py`: independently
  expanded contracts, encoded recursive examples, and original-checker tests.
- `source-observations-v1.json`: historical source/model observations with
  commands and input byte identities; these do not grant proof authority.
- The separate [complete verification record](../prime-field-gcd-closure-v1/final-verification-observations-v1.json)
  records the dependency cone, same-byte independent Lean check and all 14
  ordinary HA roots. The normalized existence certificate has 56,067 nodes;
  the explicit Bézout greatestness certificate has 36,635 nodes.

No promotion, commit, push, or deployment is performed by this extension.
G091, arbitrary prime-power field construction, remains a later goal.
