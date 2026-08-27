# Full finite-list generalized Chinese remainder theorem

This additive campaign closes the exact missing mathematical implication for
G011: pairwise gcd compatibility implies every predecessor-LCM merge condition
for an arbitrary finite list. It uses the unchanged first-order Heyting
arithmetic kernel and the immutable, checked Alpha v26 parent (2,138 theorems).
It changes neither a historical theorem nor any existing definition, certificate,
catalogue, axiom, Stable membership, or trusted checker.

The implementation is
`peano-lab/py/peano_lab/library/generalized_crt_full_candidate.py`, with factory
`make_generalized_crt_full_candidate_theorems`. Its 24 new theorem bodies are
dependency ordered. All dependencies are either earlier rows in this factory
or checked Alpha-v26 theorems.

## Exact full statements and boundary conventions

The data tuple is `(r,s,b,c,l)`: the first two naturals code the residue list by
the existing total, functional beta relation, the next two code the modulus
list, and `l` is its arbitrary natural length. Every list condition quantifies
over actual decoded values at indices strictly below `l`. No list enumeration,
modulus bound, supplied solution, supplied LCM, dominating modulus, or pairwise
coprimality is an implicit premise.

`CRTPairwiseCompatiblePrefix(r,s,b,c,l)` is exactly the existing relation:
each pair of decoded residues is congruent modulo the relational gcd of its
two decoded moduli. Balanced congruence means

```
ModEq(m,u,v) := exists p q. u + m*p = v + m*q.
```

In particular, `ModEq(0,u,v)` means `u=v`. The exact list LCM is characterized
by divisibility, not by a product shortcut. The empty list has LCM one; any
zero modulus forces its list LCM to zero.

The unrestricted solvability endpoint is:

```
crt_pairwise_compatible_prefix_solution_exists:
  forall r s b c l.
    CRTPairwiseCompatiblePrefix(r,s,b,c,l) ->
    exists x. CRTPrefixSolution(r,s,b,c,l,x).
```

The original positive-modulus canonical definition is retained byte-for-byte:

```
CRTCanonicalPrefixSolution(data,x,M) :=
  CRTPrefixLCM(b,c,l,M) /\
  (x < M /\ CRTPrefixSolution(data,x)).
```

Its full constructor is now proved from positivity and actual pairwise
compatibility alone:

```
crt_pairwise_compatible_prefix_canonical_exists_unique:
  forall r s b c l.
    CRTPositiveModuliPrefix(b,c,l) ->
    CRTPairwiseCompatiblePrefix(r,s,b,c,l) ->
    exists x M.
      CRTCanonicalPrefixSolution(r,s,b,c,l,x,M) /\
      forall y. CRTCanonicalPrefixSolution(r,s,b,c,l,y,M) -> y=x.
```

A bound `x<M` is impossible when `M=0`. Therefore the zero-inclusive full
blueprint endpoint uses a separate conservative normalization definition:

```
CRTNormalizedPrefixSolution(data,x,M) :=
  CRTPrefixLCM(b,c,l,M) /\
  ((M=0 \/ x<M) /\ CRTPrefixSolution(data,x)).

crt_pairwise_compatible_prefix_normalized_exists_unique:
  forall r s b c l.
    CRTPairwiseCompatiblePrefix(r,s,b,c,l) ->
    exists x M.
      CRTNormalizedPrefixSolution(r,s,b,c,l,x,M) /\
      forall y. CRTNormalizedPrefixSolution(r,s,b,c,l,y,M) -> y=x.
```

The zero branch does **not** discard simultaneous congruence or assume
uniqueness. Uniqueness is proved from the existing theorem that congruence
modulo the zero list LCM is equality. At a positive list LCM, normalization
is the unique bounded representative. The new
`crt_positive_normalized_prefix_iff_canonical` formally proves that on positive
modulus lists this new definition is equivalent to the unchanged old one.

The complete solution class is also identified: for a normalized solution
`x` and its exact LCM `M`, a natural `y` is any simultaneous solution if and
only if `ModEq(M,y,x)`. Thus literal uniqueness is asserted only for normalized
representatives, or for all solutions when `M=0`, never for every unbounded
solution at positive `M`.

## Constructive proof

The central new arithmetic theorem is unconditional:

```
IsLCM(L,a,b) -> IsGCD(ga,a,n) -> IsGCD(gb,b,n) -> IsGCD(g,L,n)
  -> IsLCM(g,ga,gb).
```

Equivalently, gcd distributes over binary LCM. There is no hypothesis that
one input divides another. If `a` and `n` are nonzero, choose

```
d=gcd(a,b),     a=d*A, b=d*B,       Coprime(A,B),
e=gcd(d,n),     d=e*D, n=e*N,       Coprime(D,N),
u=gcd(A,N),     v=gcd(B,N).
```

All choices come from already proved constructive gcd totality and explicit
quotient witnesses. Nonzero gcd and cofactor facts are proved before any
cancellation. The checked gcd–LCM product theorem gives `L=d*(A*B)`.
The existing scaled-coprime-component and coprime-product gcd theorems give

```
ga=e*u,       gb=e*v,       g=e*(u*v),       Coprime(u,v).
```

The product of coprime naturals is their LCM, and the checked nonzero LCM
scaling theorem yields `IsLCM(g,ga,gb)`. The `a=0` branch uses the exact
zero-divisibility case, and the `n=0` branch uses `gcd(t,0)=t`. Natural equality
is decidable constructively. Thus the final theorem includes all zero cases
without classical excluded middle, prime factorization, valuation assumptions,
choice, or an external arithmetic oracle.

Next, genuine induction on `l` proves:

```
CRTPrefixLCM(b,c,l,L) ->
CRTPrefixGCDCongruences(b,c,l,n,u,v) -> IsGCD(g,L,n) -> ModEq(g,u,v).
```

The empty LCM is one. At a successor, obtain the predecessor LCM and the
actual next modulus, construct their binary LCM, and identify it with the
given successor-prefix LCM by uniqueness. Apply the induction hypothesis to
the preceding gcd congruences, then the new binary distributivity theorem
and the existing congruence-LCM merge theorem.

For each actual next residue `a`, pairwise compatibility and any actual
prefix solution `x` imply the pointwise gcd congruences between `x` and `a`.
The induction theorem therefore discharges the exact predecessor-LCM merge
invariant. The historical generalized fold now applies without assuming that
invariant. The following mathematical proof arrows are genuine theorem
dependencies; definition arrows are separate abbreviation dependencies.

```
gcd totality + coprime quotients + gcd scaling + coprime-product gcd
                  + gcd–LCM product + nonzero LCM scaling
                              |
                unrestricted binary gcd–LCM distributivity
                              |
           actual prefix-LCM induction + congruence-LCM merge
                              |
       pairwise compatibility -> every predecessor-LCM merge
                              |
                   actual finite solution construction
                         /                  \
        positive canonical uniqueness       zero-safe normalized uniqueness
                         \                  /
                 full solution-class characterization
```

## Conservative definition DAG

Only two new relation names are requested. Their public builders validate
identifier arguments and tags, reject duplicates and generated-name capture,
and produce alpha-equivalent native ASTs when binder tags change.

| New relation | Arguments | Exact direct abbreviation dependencies |
|---|---|---|
| `CRTPrefixGCDCongruences` | `(b,c,l,n,u,v)` | `Beta`, `Lt`, `IsGCD`, `ModEq` |
| `CRTNormalizedPrefixSolution` | `(r,s,b,c,l,x,M)` | `CRTPrefixLCM`, `Lt`, `CRTPrefixSolution` |

`CRTPrefixGCDCongruences` universally quantifies an actual index, decoded
modulus, and relational gcd; it does not supply any proof or solver oracle.
`CRTNormalizedPrefixSolution` adds exactly the zero-or-bounded normalization
condition. Equality and logical connectives are existing syntax, not new
definitions. Stable IDs and publication metadata are assigned by the additive
release integration, not by this proof candidate.

## Inventory and verification

The 24 ordered names are pinned in
`peano-lab/py/tests/test_generalized_crt_full_candidate.py`. They comprise:

- four gcd boundary/cofactor helpers;
- five unrestricted binary gcd–LCM distributivity steps;
- two finite-prefix gcd-congruence steps;
- four pairwise-to-merge, actual-solution, and positive-canonical steps;
- nine zero-safe normalization, uniqueness, and exact-characterization steps.

The ordered-name SHA-256 is
`e22d05834c251753c184f3153dc86eb5c73c736993cdd01ed6776c4e81194a81`.
There are 72 declared dependency edges, 1,099 tactic commands, and 2,104
original-kernel body proof nodes. Maximum body size is 351 nodes; maximum
depth is 62. The largest fully expanded statement is 24,030 bytes.

Important exact statement hashes:

| Theorem | SHA-256 |
|---|---|
| `crt_gcd_lcm_distributes` | `50a7f6d6073fce97824cccfd6af82f692b2840298b8b8e73067d051f33f64233` |
| `crt_prefix_gcd_congruences_lcm` | `6ca30daf96706a4f4f193a1e305703edf35008320aedb0b742ad07a5c64af48a` |
| `crt_pairwise_compatible_prefix_implies_merge_compatible` | `d582dfb54082a0620f6476a37dc52d9e759bb4d86631708aa890249d5af8d98c` |
| `crt_pairwise_compatible_prefix_solution_exists` | `48a05bffa7e68939a732d71d5cb72ac423b78e014dbfada69a78fcfcf2bd667a` |
| `crt_pairwise_compatible_prefix_canonical_exists_unique` | `ac5e941743de53a1954904f99231acf74a38f59c15ed7887d3896cf3b8fe65b8` |
| `crt_pairwise_compatible_prefix_normalized_exists_unique` | `f333d811cf04309d630382e2c049885d0de6e2cf4f26a218faf0e6039b002587` |
| `crt_pairwise_compatible_prefix_solvable_iff` | `bbaf5b097637ebfb6178b95ff37f6fed77776532c4058ece4f2f79a94e65ba64` |

Validation command:

```
PYTHONPATH=peano-lab/py python3 -m pytest -q \
  peano-lab/py/tests/test_generalized_crt_full_candidate.py
```

Result: **144 tests pass**. Every body is independently checked in a
one-theorem microbatch with declared dependencies as ordinary hypotheses.
False conclusions, truncated scripts, and removed dependencies are rejected.
Exact AST tests rule out a hidden merge, dominating-last, positivity, or
coprimality premise in the unrestricted endpoints. Definition hygiene, unchanged
positive canonical semantics, zero/empty/repeated-modulus boundaries, and
small non-dominating-list examples are also checked.

These are original-kernel body receipts, not a claim of release admission or
independent Lean verification. Dependency-closed bundle assembly and both
release verifiers remain mandatory before publication or Alpha promotion.
This candidate does not edit those workflows or write to any remote service.
