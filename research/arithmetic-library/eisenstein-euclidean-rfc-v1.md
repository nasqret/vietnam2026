# G084: constructive Eisenstein Euclidean division

This additive candidate implements the full G084 statement in the grand
campaign, not a conditional correction lemma. It constructs a quotient and
remainder for every canonical Eisenstein dividend and every nonzero canonical
Eisenstein divisor. Neither a norm value, a quotient, a rounding witness nor a
remainder bound is assumed.

The immutable parent is Alpha v27, catalogue SHA-256
`481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6`:
2,560 checked-use theorems and unchanged Stable membership of 432. The only
new prerequisite factories are the independent five-row signed-integer floor
substrate and the already checked Gaussian factory. Gaussian Euclidean
division itself is not used to prove Eisenstein Euclidean division: the shared
dependencies are signed-square arithmetic, coordinate equality, canonical
coding, common addition, and the real components of Gaussian associativity.

## Exact arithmetic and shared definitions

Every formal variable ranges over naturals. A pair `(p,n)` represents the
integer `p−n`; it need not be normalized. The tuple `(p,n,r,s)` represents
`(p−n)+(r−s)ω`, where `ω²+ω+1=0`. Tuple notation here is expositional: the
actual statements quantify each natural separately.

Signed-pair equality is the primitive equation `p+m=q+n`. The norm relation
is the exact subtraction-free equation

```text
ENormCoords(p,n,r,s,N) :=
  ((p*p+n*n)+(r*r+s*s))+(p*s+n*r)
    = (((p*n+n*p)+(r*s+s*r))+(p*r+n*s))+N.
```

Consequently its natural value is exactly `(p−n)²−(p−n)(r−s)+(r−s)²`.
The coordinate product is the actual ring product

```text
(a+bω)(c+dω) = (ac−bd)+(ad+bc−bd)ω.
conjugate(a+bω) = (a−b)−bω.
```

All differences in these descriptions are expanded into positive/negative
natural contributions in the formal language. No integer type, subtraction,
ring operation or norm is added to the kernel.

`ZPairDecode`, `ZPairRep`, `ZPairValid` and `ZPairAdd` are exactly the same
relations as in the Gaussian branch, not second copies of the coding system.
The public Eisenstein addition builder directly calls the shared addition
builder. Canonical coordinates use the historic `SignedDecode` and
`SignedBalance`; their two signed codes are paired by

```text
Pair(rc,ic) = (rc+ic)*S(rc+ic)+(ic+ic).
```

Not every natural is a valid pair code. `ZPairValid` retains that condition;
zero is precisely code zero. The checked shared bridges relate represented
coordinate arithmetic to the old signed addition/multiplication graphs.
Their equivalence is proved, not asserted by an incompatible notation alias.

The new canonical graphs are:

```text
ENorm(a,N) := exists A. ZPairRep(a,A) /\ ENormCoords(A,N).
EMul(a,b,c) := exists A B.
  ZPairRep(a,A) /\ ZPairRep(b,B) /\ ZPairRep(c,A*B).
EDivRem(a,b,q,r) := exists t. EMul(b,q,t) /\ ZPairAdd(t,r,a).
EEuclideanDivision(a,b,q,r,U,V) :=
  EDivRem(a,b,q,r) /\ ENorm(r,U) /\ ENorm(b,V) /\ U<V.
```

`U<V` expands to `exists h. h+S(U)=V`. Membership of the constructed
quotient and remainder follows from their actual representations in the
operation and norm graphs; it is not a supplied premise. All public builders
parse actual Peano terms in an explicit context, support compound and repeated
arguments, and reject malformed terms or binder capture. They take keyword
arguments `tag` and `variables`. The raw eighteen-argument division graph is
also exposed by `eisenstein_signed_division_remainder_relation`.

## Full formal endpoints

The main theorem `eisenstein_euclidean_division_exists` states:

```text
forall a b.
  ZPairValid(a) -> ZPairValid(b) -> ~(b=0) ->
  exists q r U V. EEuclideanDivision(a,b,q,r,U,V).
```

Its exact statement SHA-256 is
`160d72250ab01db0ed32ca57bc472fd22d5ea307e4042815397cc771c3e102a9`.

The underlying `eisenstein_signed_euclidean_division_exists` works for all
arbitrary, possibly overlapping signed representatives. Its only premise is
that the divisor's two represented integer coordinates are not both zero.
Its exact statement SHA-256 is
`481e8a8d2b7dc8431901e86b902b578a144c8aa72133a5e5e6b4b6c8c5e44725`.

The canonical branch also proves norm existence, functionality and unique
existence; actual addition and multiplication existence and functionality;
and `ENorm(a,N) -> ENorm(b,M) -> EMul(a,b,c) -> ENorm(c,N*M)`.
Canonical functionality means equality of the literal natural output codes,
not merely equivalence of raw signed representatives.

## Constructive algorithm and proof layers

1. Normalize arbitrary signed representatives using the existing signed
   encoding. For same-sign natural coordinates, compare their order and
   construct `a²+ad+d²` when the larger coordinate is `a+d`. Opposite signs
   give a sum of squares and a nonnegative cross term. This proves norm
   existence without assuming a norm oracle.
2. Prove `4N(a,b)=(2a−b)²+3b²` by actual signed-square equations. A zero norm
   therefore forces both represented coordinates to vanish. The independent
   weight-three square norm and its multiplicativity are also proved.
3. Prove actual multiplication congruence, associativity, conjugation and
   commutativity. Real associativity is factored through already checked
   Gaussian real associativity and scalar triple products. The rotation
   `T(a,b)=(-b,a-b)` recovers imaginary associativity from real associativity.
   This avoids a large sixty-four-monomial normalization.
4. From `conjugate(z)*z=N(z)`, multiplicativity of conjugation and checked
   four-factor interchange, deduce actual Eisenstein norm multiplicativity.
   No quartic polynomial oracle or extra arithmetic axiom is used.
5. For divisor `b≠0`, construct `M=N(b)>0` and the actual signed numerator
   `conjugate(b)*a`. Apply the shared signed floor theorem separately to its
   two coordinates, obtaining an actual quotient `q` and natural residues
   `0≤s,t<M`. One signed floor call uses only one ordinary natural division:
   divide `xp+(M−1)*xn` by `M` and choose the quotient pair `(q,xn)`.
6. Define the actual signed remainder `r=a-bq`. The checked adjugate identity
   gives `conjugate(b)*r=(s,t)`. Hence `M*N(r)=N(s,t)`.
7. If `s≤t`, then `s²−st+t²≤t²<M²`; otherwise use the symmetric inequality.
   The strict gap is constructed in natural arithmetic. Thus `M*N(r)<M²`,
   and the checked multiplication/order cancellation gives `N(r)<M`.
8. Normalize the quotient and remainder to canonical codes and construct
   the actual multiplication-and-addition graph `a=bq+r`. Representative
   invariance transports the exact norms and their strict gap.

The parallelogram lemma includes zero residues and the corner `s=t=M−1`.
For `M>1`, that latter corner need not be attainable as an actual adjugate
residue pair; it is deliberately covered by the stronger rectangular bound.
Unit divisors have `M=1` and give zero remainder. No prime, oddness, positive
dividend or positive-remainder restriction occurs. This construction need not
choose an optimally nearest quotient; floor coordinates in the fundamental
parallelogram suffice for the exact Euclidean property requested by G084.

## Inventory and dependency structure

The factory `make_eisenstein_euclidean_candidate_theorems` has 65 rows,
308 declared dependency edges and 5,414 ordinary tactic commands. The exact
ordered inventory is:

```text
eisenstein_natural_norm_symmetric
eisenstein_natural_norm_gap_value
eisenstein_natural_norm_exists
eisenstein_natural_norm_zero
eisenstein_natural_norm_le_larger_square
eisenstein_parallelogram_norm_strict
eisenstein_coordinate_norm_functional
eisenstein_coordinate_norm_negation
eisenstein_normal_coordinate_norm_exists
eisenstein_pair_natural_value_transport
eisenstein_coordinate_norm_transport
eisenstein_coordinate_norm_exists
eisenstein_norm_square_balance
eisenstein_weighted_embedding_compensation
eisenstein_norm_weighted_square_identity
eisenstein_weighted_norm_exists
eisenstein_weighted_norm_functional
eisenstein_norm_to_weighted_norm
eisenstein_weighted_norm_transport
eisenstein_weighted_norm_scaled
eisenstein_signed_product_scaled_right
eisenstein_weighted_lagrange_compensation
eisenstein_weighted_square_lagrange
eisenstein_weighted_norm_product
eisenstein_real_associate_left_positive
eisenstein_real_associate_left_negative
eisenstein_real_associate_right_positive
eisenstein_real_associate_right_negative
eisenstein_product_associate_real
eisenstein_product_difference_real_positive
eisenstein_product_difference_real_negative
eisenstein_product_difference_imaginary_positive
eisenstein_product_difference_imaginary_negative
eisenstein_product_difference
eisenstein_product_integer_congruence
eisenstein_omega_product_covariance
eisenstein_product_associate_imaginary
eisenstein_product_associate
eisenstein_coordinate_norm_conjugate
eisenstein_conjugate_product_is_norm
eisenstein_natural_scalar_product
eisenstein_adjoint_product_is_norm_scale
eisenstein_residual_conjugate_identity
eisenstein_product_commute
eisenstein_product_conjugate
eisenstein_product_shuffle
eisenstein_coordinate_norm_product
eisenstein_coordinate_norm_zero
eisenstein_coordinate_norm_nonzero
eisenstein_natural_norm_coordinates
eisenstein_signed_euclidean_division_exists
eisenstein_norm_of_representation
eisenstein_norm_for_representation
eisenstein_norm_exists
eisenstein_norm_functional
eisenstein_norm_exists_unique
eisenstein_add_exists
eisenstein_add_functional
eisenstein_multiply_of_representations
eisenstein_multiply_for_representations
eisenstein_multiply_exists
eisenstein_multiply_functional
eisenstein_norm_multiply
eisenstein_division_remainder_of_representations
eisenstein_euclidean_division_exists
```

The source records every dependency by exact checked theorem name. The six
immediate dependencies of the main canonical endpoint are
`gaussian_decode_representation`, `gaussian_representation_zero_iff`,
`eisenstein_signed_euclidean_division_exists`,
`gaussian_representation_exists`,
`eisenstein_division_remainder_of_representations` and
`eisenstein_norm_of_representation`. The raw endpoint depends on actual norm
construction, nonvanishing, two signed floors, the parallelogram bound,
the residual/adjugate identity, conjugation and norm multiplicativity,
representative transport, actual reconstruction, and strict natural
multiplication cancellation. All new dependencies are earlier in factory
order, and the independent signed floor substrate has no ring dependency.

## Verification and non-claims

The ordinary dependency-curried main bodies are original-kernel accepted:
281 nodes / depth 71 for unrestricted signed division and 180 nodes / depth
62 for canonical division. The dedicated tests independently reconstruct
primitive AST meanings, check exact root hypotheses and witnesses, reject
forged proofs and missing guards, audit the actual dependency DAG and
definition hygiene, and execute the described algorithm at sign, zero,
unit, asymmetric and large-numeral boundaries. Numerical examples test
implementation semantics; they are not the formal proof.

The finite polynomial authoring guides emit only ordinary equality,
congruence, distributivity and permutation commands. Every emitted step is
checked; no guide result is accepted as a theorem. The original 256-depth
limit and all original kernel/tactic trust boundaries remain unchanged.
The last scalar compensation was split into three small guided identities,
reducing its checked depth from 181 to 75 and local replay time from about
52 seconds to about 5 seconds without changing its statement or raising a
resource cap.

These body checks use the pinned catalogue only as a source of dependency
statements. They are not dependency-closed admission receipts. The integrating
Alpha v28 release separately closes the entire original-kernel dependency
cone and checks the compiled Peano-to-Lean bundle. No old theorem, kernel,
edition, Stable membership, site or deployment is modified by this candidate.
G085 Eisenstein unique factorization, G086 prime classification, and the
later cubic/Fermat campaigns are not claimed here.
