# Constructive Gaussian Euclidean division — candidate RFC v1

## Exact scope and trust boundary

This additive candidate implements the full G081 division statement, including
canonical natural codes for both signed coordinates. It does not assume a
quotient, a rounding witness, a norm estimate, a descent oracle, or classical
excluded middle. Its final hypothesis, apart from membership in the canonical
coordinate carrier, is exactly that the divisor code is not zero.

The source is
`peano-lab/py/peano_lab/library/gaussian_euclidean_candidate.py`, factory
`make_gaussian_euclidean_candidate_theorems(TheoremSpec)`. It contains 88 new
ordinary theorem bodies with 303 declared dependency edges and 4,462 tactic
commands. The bodies have 14,416 proof nodes in total; the largest body has 736
nodes, and the greatest body depth is 108. All use the unchanged kernel and its
unchanged 256-depth limit.

The authoring basis is the exact 2,560-row Alpha v27 catalogue:

```text
artifacts/peano-library/alpha/catalog-v27.json
SHA256 481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6
Stable prefix: 432 theorems
```

The only new prerequisite module is the independently checked
`signed_integer_division_candidate.py` substrate. Its five rows precede this
factory. No Gaussian row depends on Eisenstein division, unordered prime
factorization, a new kernel rule, or a new arithmetic function symbol.

Catalogue statements supply only hypotheses for the dependency-curried
authoring checks. Their hashes are identity pins, not proof authority. Release
admission must additionally reconstruct and check the actual complete old/new
proof closure and its Lean translation. This RFC does not substitute its body
receipts, numerical examples, or hashes for that release obligation. No Stable
promotion is requested.

## Conservative definitions and their DAG

Every relation expands into the existing first-order HA language
`{0,S,+,*,=}`. Existential names are hygienic; public APIs accept validated,
distinct variable identifiers and reject inherited/generated binder prefixes.
Different valid tags produce alpha-equivalent formulas.

A raw signed pair `(p,n)` represents the integer `p-n`. Its actual squared
value is the natural `s` satisfying

```text
SignedDifferenceSquare(p,n,s) :
    p*p + n*n = s + (p*n + n*p).
```

Equality of two represented integers is `p+m=q+n`, not equality of their
positive and negative components. The Gaussian norm of raw coordinates
`(p,n,q,m)` is the sum of their two actual signed-difference squares. Existence,
uniqueness, negation invariance, integer-representative invariance, and product
multiplicativity are proved, including overlapping representations such as
`(9,9)` for zero.

The historic signed decoder is reused exactly:

```text
SignedDecode(c,p,n) :
    (c=2*p /\ n=0)
    \/ exists k. ((c=2*k+1 /\ p=0) /\ n=S k).

SignedBalance(c,p,n) :
    exists u v. SignedDecode(c,u,v) /\ p+v=n+u.

Pair(rc,ic) = (rc+ic)*S(rc+ic) + (ic+ic).
```

`Pair` is explanatory notation for an existing polynomial, not a new function.
It is the same injective natural pairing used in the historic library. The
coordinate carrier is neutral between Gaussian and Eisenstein arithmetic:

```text
ZPairDecode(z,p,n,q,m) :
    exists rc ic. z=Pair(rc,ic)
        /\ SignedDecode(rc,p,n) /\ SignedDecode(ic,q,m).

ZPairRep(z,p,n,q,m) :
    exists rc ic. z=Pair(rc,ic)
        /\ SignedBalance(rc,p,n) /\ SignedBalance(ic,q,m).

ZPairValid(z) : exists p n q m. ZPairDecode(z,p,n,q,m).
```

The Python public API retains `gaussian_decode_relation`,
`gaussian_representation_relation`, and `gaussian_integer_relation`; the
reviewed presentation may give the shared carrier the neutral names above.
Only the carrier is shared with Eisenstein arithmetic. The two ring products
are not aliases.

The resulting definition DAG is:

```text
SignedDecode ──→ SignedBalance ──→ ZPairRep ───────┬─→ GAdd ──┐
      │                                         ├─→ GMul ──┤
      └────────→ ZPairDecode ──→ ZPairValid       │          └─→ GDivRem
                                                └─→ GNorm        │
SignedDifferenceSquare ──→ RawGaussianNorm ──────────→ GNorm       │
                                                                  ▼
        ZPairValid(quotient,remainder) + GNorm + strict order → GEuclideanDivision
```

`GAdd(a,b,c)` uses actual componentwise sums of arbitrary represented input
coordinates and the canonical code representing the resulting two integers.
`GMul(a,b,c)` uses exactly `(ac-bd)+(ad+bc)i`; its signed-pair polynomial
accounts for each negative contribution. Both operations are total on valid
inputs and have unique literal output codes. Their graphs agree with arithmetic
on every equivalent raw representative.

The four checked bridge rows
`gaussian_signed_add_of_balances`, `gaussian_signed_add_to_balance`,
`gaussian_signed_mul_of_balances`, and `gaussian_signed_mul_to_balance` prove
both directions between the raw contribution balances and the **unchanged**
historic `SignedAdd`/`SignedMul` graphs. This is a proved connection to existing
integer arithmetic, not an asserted AST alias.

`GNorm(z,N)` witnesses a representation of `z` and its actual raw squared norm.
`GDivRem(a,b,q,r)` is `exists p. GMul(b,q,p) /\ GAdd(p,r,a)`. Finally:

```text
GEuclideanDivision(a,b,q,r,U,V) :
    ZPairValid(q) /\ ZPairValid(r)
    /\ GDivRem(a,b,q,r)
    /\ GNorm(r,U) /\ GNorm(b,V)
    /\ exists gap. gap+S U=V.
```

No division bound is hidden in `ZPairValid`, `ZPairRep`, `GAdd`, or `GMul`.

## Principal statements

The full canonical endpoint is exactly:

```text
gaussian_euclidean_division_exists:
    forall a b.
      ZPairValid(a) -> ZPairValid(b) -> ~(b=0) ->
      exists q r U V. GEuclideanDivision(a,b,q,r,U,V).
```

Its body has 149 commands, 199 proof nodes, and depth 65. The earlier raw
endpoint, `gaussian_signed_euclidean_division_exists`, quantifies over all eight
arbitrary natural input components; its sole premise is that the divisor's two
integer differences do not both vanish. It constructs eight natural quotient
and remainder components and two actual norm witnesses. That body has 187
commands, 242 nodes, and depth 70.

Additional public roots are:

- `gaussian_norm_exists_unique`: every valid code has exactly one actual natural
  squared norm, including zero.
- `gaussian_add_exists` and `gaussian_multiply_exists`: construct actual
  canonical outputs; their companion functionality rows prove output uniqueness.
- `gaussian_norm_multiply`: the norm of an actual canonical product is the
  product of the actual input norms.
- `gaussian_representation_zero_iff`: a represented code is zero exactly when
  its two integer-coordinate differences vanish.

The quotient/remainder pair is **not** claimed unique: nearest-coordinate
rounding can have ties. Nothing here asserts Gaussian unique factorization,
classification of Gaussian primes, or the later G082 milestone. Those require
separate proofs. The shared raw arithmetic is likewise not a proof of the
different Eisenstein Euclidean bound.

## Constructive proof layers

1. Construct signed-difference squares by the existing absolute-difference
   theorem and natural compensation identity. Prove their functionality and
   transport under actual integer equality.
2. Prove the signed Lagrange identity by four product squares and checked
   cross-term cancellation. Deduce genuine multiplicativity of the Gaussian
   squared norm for arbitrary, possibly overlapping signed representatives.
3. Prove actual Gaussian product association, subtraction distribution,
   conjugate-product/norm identities, and the adjoint remainder identity.
4. Given positive natural modulus `N`, use the shared signed floor constructor
   and the historic centered-remainder constructor. They produce an actual
   signed quotient, signed error, and natural magnitude `t` with `2*t <= N`.
   No rounding premise is supplied by the caller.
5. For `a` and nonzero `b`, construct `N=Norm(b)` and round the two coordinates
   of `conjugate(b)*a` divided by `N`. Set `r=a-b*q` by actual signed arithmetic.
6. The checked adjoint identity and norm multiplicativity give
   `N*Norm(r)=t*t+u*u`. The two half-bounds prove
   `t*t+u*u < N*N`, including zero errors and `N=1`. The existing natural
   cancellation/order theorem gives `Norm(r)<N`.
7. Normalize the constructed raw quotient and remainder to canonical codes,
   transport the exact arithmetic equation, and preserve both actual norm
   witnesses. The final statement retains only validity and `b!=0` premises.

For example, `(7+5i)=(3+2i)*2+(1+i)` has remainder norm `2<13`. In the
canonical pairing above the four codes are respectively `620`, `118`, `20`,
and `24`. This example illustrates the construction; it is not used as evidence
for the universal theorem.

## Checking and resource discipline

`peano-lab/py/tests/test_gaussian_euclidean_candidate.py` contains 439 checks:
all 88 actual ordinary kernel bodies, forged-conclusion rejection for every
row, missing-dependency rejection, exact endpoint statement pins, independent
AST reconstruction of both division endpoints and the conservative relation
graphs, removal of the essential nonzero guard, inherited binder/capture and
argument validation, and numerical boundary/representative regressions.

The numerical tests exhaust all coordinate dividends and nonzero divisors in
`[-5,5]^2`, including zero dividends, units, all four sign quadrants, and
deliberately overlapping numerator representatives. They also check half-ties,
signed floor arithmetic, zero norm, and rejection of invalid odd pair codes.
Numerical tests complement but never replace the universal kernel checks.

The polynomial expansion guide is untrusted source-generation code. It emits
ordinary distribution, congruence, associativity, commutativity, and permutation
steps. Each emitted equality is independently checked. Its explicit authoring
budget is 64 monomials and degree eight; these limits restrict the proof-guide
input, **not** the naturals quantified by any theorem. No new `ring` tactic or
unchecked equality certificate is admitted. Small-coefficient and false/
over-budget guide regressions are checked separately.

The final mathematical body run passed all 88 rows in 118.73 seconds with peak
RSS 299,204,608 bytes, under a 1,536 MiB RSS guard, 170-second soft CPU limit,
175-second hard CPU limit, and 180-second wall alarm. The new non-body contract
suite passed its 351 checks in 3.70 seconds. The final combined suite then
passed all 439 checks in 121.05 seconds, with peak RSS 301,662,208 bytes.
These bounds were not increased to
accommodate failed proof search; explicit small arithmetic certificates
replaced unnecessarily expensive AC normalization.

Ordered-name SHA256:

```text
1d25a21b70918e4de3586fb7a12ad23ab66cf1b14779a6d11097171c1c10b9a8
```

Principal statement SHA256 identities:

| Theorem | Exact statement SHA256 |
| --- | --- |
| `gaussian_signed_euclidean_division_exists` | `b74e03b044aac9c837f2098ad4e3d75a977fddf0d331ae84e02d440d422c91d8` |
| `gaussian_euclidean_division_exists` | `7c20ce64493b15888f961ece2d86e97171370aee53e8517ee21db8d53d82fd10` |
| `gaussian_norm_exists_unique` | `452d832311908cb4fca7139b9147039b0a05331967073d0b1743117f510599fd` |
| `gaussian_add_exists` | `af126fdb2cc45f1f1b2620570ac6e6759b4e3118a25acaa96862b53971ec255d` |
| `gaussian_multiply_exists` | `3ded8b89b9624cb91cd7a7eb23ea6a2921aa912aba4dc6a8c35d8d308d3971d0` |
| `gaussian_norm_multiply` | `b9f32039576506c3cabe3efcb762725f554089562b866d504fb0f92187159c64` |
| `gaussian_representation_zero_iff` | `7fa8a228116bfb6de5d50cd5782c6e33cc4e659ff2a2c4725d0979e77f0d6a08` |

The entire v27 source/evidence tree remains byte-exact. The RFC, candidate
source, and tests are additive; final Alpha v28 admission and publication are
separate coordinated integration steps.
