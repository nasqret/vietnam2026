# Prime simple-root Hensel criterion and all positive precisions

This additive four-theorem bridge exposes the ordinary full G095 hypothesis:
an actual integer polynomial has a root modulo a prime, and its actual signed
derivative is nonzero modulo that prime. Neither a derivative inverse nor a
prime-power witness is supplied by the caller. The inverse, the actual target
modulus, and the unique bounded lift are all constructed.

The implementation is
`peano-lab/py/peano_lab/library/hensel_simple_root_criterion_candidate.py`, with
factory `make_hensel_simple_root_criterion_candidate_theorems`. It reuses the
immutable Alpha-v26 parent and the frozen 19-row natural and 17-row signed
Hensel families unchanged. In particular, the historical unit-based
`SignedSimpleHornerRoot` definition is preserved rather than silently weakened
to a nonzero-residue test.

## Exact definitions and endpoint

The integer polynomial is a pair of actual natural coefficient prefixes,
with four codes `(pb,pc,nb,nc)` and finite length `l`. The positive and negative
coefficient streams are interpreted by their difference. The actual Horner
value/derivative pairs are `(vp,dp)` and `(vn,dn)` at the input point `a`.
Their integer value and derivative are `vp-vn` and `dp-dn`; subtraction remains
notation, not a new kernel operation.

```
SignedDerivativeNonzero(p,dp,dn) := not ModEq(p,dp,dn).

SignedNonsingularHornerRoot(poly,a,l,m,p) :=
  exists vp dp vn dn.
    SignedHornerValueDerivative(poly,a,l,vp,dp,vn,dn) /\
    ModEq(m,vp,vn) /\ SignedDerivativeNonzero(p,dp,dn).
```

The two moduli remain separate in the reusable definition: the polynomial
may be a root modulo `m`, while nonsingularity is tested modulo `p`. The full
public endpoint initializes both to the same prime:

```
integer_polynomial_prime_simple_root_lifts_all_positive_powers:
  forall pb pc nb nc a l p k.
    Prime(p) -> k != 0 ->
    SignedNonsingularHornerRoot(pb,pc,nb,nc,a,l,p,p) ->
    exists M.
      Pow(p,k,M) /\
      exists r.
        CanonicalSignedHornerLift(poly,l,p,a,M,r) /\
        forall z. CanonicalSignedHornerLift(poly,l,p,a,M,z) -> z=r.
```

The existing canonical lift means exactly

```
r<M /\ ModEq(p,r,a) /\ SignedHornerRoot(poly,r,l,M).
```

Thus uniqueness is among **all** bounded roots in the original residue class,
not merely among correction witnesses or successful executions of a proposed
solver. The input representative `a` need not be bounded by `p`. Every positive
precision is included, particularly `k=1`; the target modulus `M` is an actual
constructed natural satisfying the checked finite-product power relation.

## Constructing the derivative inverse

The unit-based signed lifting family expects

```
SignedDerivativeUnit(p,dp,dn) :=
  exists u. u<p /\ ModEq(p,dp*u,1+dn*u).
```

The new `hensel_prime_signed_nonzero_derivative_is_unit` proves this relation
from only primality and `not ModEq(p,dp,dn)`.

First construct the predecessor `h` with `p=S h`, using prime positivity.
Use the actual natural derivative blend

```
D=dp+h*dn.
```

The frozen signed-blend theorem proves
`ModEq(p,D,0)` if and only if `ModEq(p,dp,dn)`. Thus `p` does not divide `D`.
The checked prime-coprimality theorem and symmetry give `Coprime(D,p)`, and
the checked bounded inverse constructor yields `u<p` and `ModEq(p,D*u,1)`.

Ordinary distributivity proves

```
D*u = dp*u + h*(dn*u).
```

The frozen signed-blend residue theorem now transports the same inverse to
`ModEq(p,dp*u,1+dn*u)`. It is therefore a genuine inverse of the integer
derivative, including cases where its negative component exceeds its positive
component. No external integer solver, normalization assumption, choice axiom,
or inverse oracle is introduced.

The reusable root adapter `hensel_prime_nonsingular_root_is_simple` preserves
the actual Horner value and derivative witnesses and adds this constructed
unit witness. It satisfies the existing signed simple-root interface exactly.

## Constructing every positive precision

For the public theorem, `Pow(p,1,p)` is constructed from `pow_exists` and the
already checked exponent-one theorem; it is not an input premise. Since
`k != 0`, construct `j` with `k=S j`. The frozen full signed Hensel iteration
starts at modulus `p` and exponent one, and constructs the unique canonical
lift at exponent `1+j`. Ordinary addition proves `1+j=k`, and this equality
transports the actual power witness to the requested precision.

```
Prime(p) + actual derivative nonzero modulo p
                          |
       actual natural blend + prime coprimality
                          |
           constructed bounded signed inverse
                          |
     unchanged signed simple-root lifting interface
                          |
   constructed Pow(p,1,p) + positive exponent predecessor
                          |
     actual Pow(p,k,M) + unique canonical root modulo M
```

Primality is essential for this particular criterion: for example, `2` is
nonzero modulo `4` but has no inverse modulo `4`. Nonsingularity is also
essential to uniqueness: the root zero of `x^2` modulo `5` has five roots in
its residue class modulo `25`. The restriction `k>0` retains the original
modulo-`p` residue class; arbitrary such classes do not survive a requested
bound below modulus one.

## Conservative definition DAG

Two additive builders are exposed, each validating identifier arguments and
binder tags and rejecting duplicate or capturing arguments:

| Relation | Arguments | Direct abbreviation dependencies |
|---|---|---|
| `SignedDerivativeNonzero` | `(p,dp,dn)` | `ModEq` |
| `SignedNonsingularHornerRoot` | `(pb,pc,nb,nc,a,l,m,p)` | `SignedHornerValueDerivative`, `ModEq`, `SignedDerivativeNonzero` |

Their Python names are `signed_derivative_nonzero_relation` and
`signed_nonsingular_horner_root_relation`, with keyword `tag`. The criterion
does not modify `SignedDerivativeUnit`, `SignedSimpleHornerRoot`, `Pow`, or
`CanonicalSignedHornerLift`. Stable IDs and the mixed campaign DAG are release
integration work, separate from these conservative authoring definitions.

## Inventory and verification

There are four new rows, 20 dependency edges, 205 tactic commands, and 350
original-kernel body proof nodes. Body sizes are `(106,33,60,151)`, maximum
depth is 38, and the largest expanded statement is 44,068 bytes.

The ordered-name SHA-256 is
`335afa7e23c8259fb2e5bf170b0a5f1d132bacd911d9f73404e48f4d07d02d8b`.
Exact statement hashes are:

| Theorem | SHA-256 |
|---|---|
| `hensel_prime_blended_nonzero_derivative_is_unit` | `bf018263a6830d1fdd38d1f33c8a532c13ee229a7c6e6fcce49ebe6d7c11d6fa` |
| `hensel_prime_signed_nonzero_derivative_is_unit` | `87891b4b911500f2331988d2bc0d98ec188a6ce554d7fa1c8fafce44a51161e5` |
| `hensel_prime_nonsingular_root_is_simple` | `b6ce01164048acad568d8748760326a4d3fbf2cbb1b63715924924c887f8f9e9` |
| `integer_polynomial_prime_simple_root_lifts_all_positive_powers` | `158b28822061f364d34a4badf84986d5f02301b58c555b1e67ec758c786709e8` |

The test harness pins the immutable Alpha-v26 catalogue to SHA-256
`969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534`
and includes the frozen natural/signed Hensel rows in dependency order. Each
new body is checked in a one-theorem microbatch with dependencies as ordinary
hypotheses, without rebuilding every historical edition registry.

```
PYTHONPATH=peano-lab/py python3 -m pytest -q \
  peano-lab/py/tests/test_hensel_simple_root_criterion_candidate.py
```

Tests pin exact endpoint ASTs and theorem hashes, reject false conclusions,
truncated scripts and removed dependencies, check both definitions' hygiene,
and test actual signed-polynomial examples at small primes and positive
precisions. These examples include negative coefficients and noncanonical
coefficient pairs, unrestricted input representatives, precision one, and
prime two. They are regression checks, not proof authority.
Result: **85 tests pass**.

The scope is ordinary nonsingular Hensel lifting for arbitrary finite
integer-coefficient polynomials, not singular lifting or a general criterion
for composite moduli. Dependency-closed original-kernel and independent Lean
checks remain release gates. These local body receipts alone do not claim
Alpha admission or deployment, and no frozen source or release state is
modified by this bridge.
