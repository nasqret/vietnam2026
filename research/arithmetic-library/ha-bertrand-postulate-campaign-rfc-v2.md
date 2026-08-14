# RFC HA-R6-BERTRAND-2: factorized-threshold amendment

**Status:** binding representation amendment to RFC HA-R6-BERTRAND-1; no
Bertrand theorem is admitted by this document

**Campaign goal:** unchanged: prove Bertrand's postulate completely in the
repository's native arithmetic system

**Object language:** unchanged: first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

**Amended document:**
[`RFC HA-R6-BERTRAND-1`](ha-bertrand-postulate-campaign-rfc-v1.md), whose
preserved SHA-256 is
`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`

This RFC is a narrow, versioned successor amendment. It changes only the
native representation of the large-input cutoff and the required checked
transport between the public doubling surface and internal doubling helpers.
Every endpoint, mathematical inequality, dependency prohibition, trust rule,
evidence meaning, B0--B8 gate, and release requirement not explicitly
amended below remains binding exactly as specified by RFC v1. In a conflict
within this narrow scope, this document controls.

## 1. Factorized native carrier for the cutoff

The mathematical cutoff remains **512**. Its sole canonical production
carrier in theorem sources and proof scripts is the native term

```text
16 * 32
```

Accordingly, a large-input premise must be authored as

```text
Le(16 * 32,n)
```

and not with an evaluated numeral. The order and association of this carrier
are frozen: `16 * 32` is canonical even though other natural-number terms
have the same value.

No accepted production theorem specification, local `have` proposition,
proof-script term, generated logical-spec source, or enrollment statement may
contain the object-language numeral token `512`. In particular, the campaign
must not add a theorem equating a literal-`512` term with `16 * 32`, and it
must not use parser expansion, trusted normalization, or a host calculation
of the literal numeral as a proof step. Prose, theorem names, reports, and
negative mutation fixtures may say “512” to identify or test the mathematical
boundary; none of them is logical authority.

This factorization changes representation only. In the standard natural
numbers, `16 * 32` denotes the same cutoff called 512 in RFC v1. The B6
inequality, the B7 domain, the B8 finite/large split, BP01, and BP02 retain
their mathematical meanings.

## 2. Public `n + n` surfaces and checked internal transport

All public Bertrand interval and main-inequality surfaces remain in the
additive spelling `n + n`. This includes:

- the BP01 and BP02 upper endpoints;
- `BertrandClosed`, `BertrandStrict`, and `NoBertrandClosed`;
- bounded-search specialization at `n,n + n`;
- the B5 premises `FloorSqrt(n + n,s)`, `DivRem(n + n,3,q,r)`, and
  `Pow(n + n,s,A)`; and
- the corresponding public B6 premises.

The amended public B6 source contract is therefore

```text
forall n s q r A B F.
Le(16 * 32,n) ->
FloorSqrt(n + n,s) ->
DivRem(n + n,3,q,r) ->
Pow(n + n,s,A) ->
Pow(4,q,B) ->
Pow(4,n,F) ->
Le(n * A * B,F)
```

The displayed multiplication associations remain subject to the subordinate
statement freeze required by RFC v1.

Internal arithmetic helpers may use `2 * n`. A public `n + n` premise may
reach such a helper only through an explicit checked equality transport using
the existing theorem

```text
two_mul_eq_add_self : forall n. 2 * n = n + n
```

The proof body must instantiate this theorem and use checked equality
symmetry/substitution to rewrite the public `n + n` argument to `2 * n`.
The theorem must be an exact, live direct dependency of every row whose body
performs that transport. Textual replacement, host simplification, or
definitional treatment of `n + n` and `2 * n` as identical is forbidden.
Internal helper statements may retain `2 * n`; they do not replace the public
surface.

The B7 deliverable remains `bertrand_eventually_closed_upper`, now with the
production threshold carried by `Le(16 * 32,n)`. B8 must likewise express its
finite/large split with the factorized carrier. The frozen BP01 and BP02
defined and base-language sources do not contain the threshold and remain
byte-for-byte unchanged, including their RFC-v1 source hashes.

## 3. Required exact-source and mutation gates

Before a B6, B7, B8, BP01, or BP02 client using this boundary can be accepted,
the focused audit must establish all of the following:

1. exact-source tests pin `16 * 32` in every production cutoff premise and
   reject literalization to the numeral token `512`;
2. carrier mutations to `16 * 31`, `15 * 32`, or the reordered `32 * 16`
   are rejected;
3. boundary mutations replacing `Le(16 * 32,n)` by a strict bound, deleting
   one factor, or shifting either factor are rejected;
4. public-surface mutations replacing any required `n + n` by `2 * n` are
   rejected even though the terms are provably equal;
5. removal of `two_mul_eq_add_self` from a transporting row's declared
   dependencies, or deletion of its body use, fails the dependency-liveness
   audit;
6. corruption of the equality direction, rewrite target, or transported
   `FloorSqrt`, `DivRem`, or `Pow` argument fails kernel replay; and
7. a production-source scan finds no object-language literal-`512` theorem or
   script term while excluding prose and deliberately rejected mutation
   fixtures from the acceptance set.

These are additional fail-closed representation gates. They do not replace
RFC v1's dependency-removal tests, boundary mutations, semantic oracles,
zero-`DNE` traversal, empty-context closure, or release checks.

## 4. Authority and evidence boundary

This amendment adds no axiom, inference rule, conservative definition,
primitive numeral, normalization oracle, theorem-name trust, or external
solver result. Multiplication in `16 * 32` and equality transport from
`n + n` to `2 * n` must be certified by the same ordinary intuitionistic
checker as every other proof step.

The amendment changes no evidence state and promotes no row. Existing
dependency-curried bodies remain body evidence until they separately satisfy
the RFC-v1 empty-context and Alpha-to-Stable gates. A host assertion that
`16 * 32` evaluates to 512 is useful only as a regression oracle and cannot
appear in an endpoint's trusted dependency closure.

## 5. Supersession map

| RFC-v1 location | RFC-v2 ruling |
|---|---|
| Section 6, mathematical steps 6--8 | Mathematical cutoff 512 is unchanged; every production logical carrier is exactly `16 * 32`. |
| Section 7, B7/B8 edges | DAG and dependencies are unchanged; threshold-bearing statements use the factorized carrier. |
| B6 `bertrand_main_inequality_nat` | Replace only the production premise formerly written with an evaluated cutoff; retain the public `n + n` relational premises. |
| B7 `bertrand_eventually_closed_upper` | Retain the theorem meaning and constructive bounded-search proof; use `Le(16 * 32,n)`. |
| B8 finite coverage and split | Retain coverage of the same mathematical inputs; use the factorized carrier in theorem sources and scripts. |
| BP01 and BP02 | No change: names, formulas, endpoint hashes, constructive meaning, and release obligations remain frozen. |

RFC v1 remains the complete base contract and provenance record. This file is
the only amendment needed to read its threshold-bearing clauses as the
factorized native representation required for subsequent campaign work.
