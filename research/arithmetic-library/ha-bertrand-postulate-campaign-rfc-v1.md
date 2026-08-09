# RFC HA-R6-BERTRAND-1: native Bertrand-postulate campaign

**Status:** binding statement, logic, architecture, and B0--B8 tranche gates
frozen; no Bertrand theorem is admitted by this document

**Campaign goal:** prove Bertrand's postulate completely in the repository's
native arithmetic system

**Object language:** first-order HA over \(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

**Controlling baseline:** Alpha v2 at repository commit
`f4cb0bc4862c75f3cecc52a7a6467f205834c6c7`, with
[`catalog-v2.json`](../../artifacts/peano-library/alpha/catalog-v2.json)
SHA-256
`90ac4942df043e59ade7a62a87627ef3b29d9b1d7d251c8fa6aadefe77590bd7`

This RFC refines the A6/R6 objective in the
[`HA number-theory campaign blueprint`](ha-number-theory-formalization-campaign-blueprint.md#A6-bertrands-postulate).
It is the binding design contract for the campaign. The words **must**,
**must not**, **should**, and **may** are normative. Helper theorem names and
the internal decomposition of a tranche may be refined in a subordinate RFC,
but the endpoint formulas, logical boundary, B0--B8 gates, evidence meanings,
and promotion rules below may change only through a versioned successor to
this RFC.

## 1. Decision and completion boundary

The campaign will formalize an integer-only Erdős--Tochiori central-binomial
proof. It will first prove the positive, closed-upper form and then derive the
traditional strict form.

The campaign is **complete** only when:

1. both frozen endpoints in Section 2 have deterministic empty-context
   certificates accepted by the ordinary intuitionistic checker;
2. their exact dependency closure has zero `DNE` nodes and no unapproved
   axiom, host theorem, or external-solver oracle;
3. all conservative definitions used by their readable statements and local
   `have` propositions have exact expansion receipts;
4. the dependency-closed release batch has passed the Alpha-to-Stable gates
   in Section 11;
5. the human proof, dependency graph, source ledger, certificate receipts,
   resource report, and reproducible commands have been published in the
   repository and pushed to GitHub.

A host proof, a tested finite range, a dependency-curried body, a model-found
tactic script, or a proof of double negation is not completion.

## 2. Frozen native endpoints

The definitions `Le`, `Lt`, and `Prime` below are the already reviewed
conservative surfaces `PD0001`, `PD0002`, and `PD0004` from the
[`definition freeze`](ha-definition-representation-freeze-v1.md). They expand
hygienically before the ordinary formula parser and add no formula
constructor.

### BP01 `bertrand_closed_upper`

Stable campaign identifier: `HA-R6-BERTRAND-BP01`.

Mathematical statement:

\[
  \forall n\ne 0\;\exists p\,
  \bigl(\operatorname{Prime}(p)\land n<p\land p\le n+n\bigr).
\]

Frozen defined source:

```text
forall n. ~(n = 0) -> exists p. (Prime(p) /\ (Lt(n,p) /\ Le(p,n + n)))
```

Frozen base-language source:

```text
forall n. ~(n = 0) -> exists p. ((~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) /\ ((exists u. u + S n = p) /\ (exists v. v + p = n + n)))
```

The defined source has SHA-256
`611a8a261dbbc6e3d3447c8a8abf2be22d57302cbef645b38b29656539efc3c9`;
the exact base source has SHA-256
`7131d5cb2f6264600646df6ae949e9bb2b69a927458ce5b39682e9e284f9ad2c`.
The two sources parse to the same de Bruijn formula under defined-syntax
registry version 2.

This is the primary endpoint. It includes \(n=1\), with witness \(p=2\), and
matches the strongest convenient computational boundary: the search interval
is finite and its right endpoint is included.

### BP02 `bertrand_strict`

Stable campaign identifier: `HA-R6-BERTRAND-BP02`.

Mathematical statement:

\[
  \forall n\;\bigl(1<n\to\exists p\,
  (\operatorname{Prime}(p)\land n<p\land p<n+n)\bigr).
\]

Frozen defined source:

```text
forall n. Lt(1,n) -> exists p. (Prime(p) /\ (Lt(n,p) /\ Lt(p,n + n)))
```

Frozen base-language source:

```text
forall n. (exists h. h + S 1 = n) -> exists p. ((~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) /\ ((exists u. u + S n = p) /\ (exists v. v + S p = n + n)))
```

The defined source has SHA-256
`1f4177d423caeba0af7a1f443f007599632e1eb1cb4e27dc2720fcdb25c86cca`;
the exact base source has SHA-256
`6c55889276eb7ad2577191ad7b7e46cae45a6c1437a0275db44801b54ee7ad39`.
The two sources likewise parse to the same de Bruijn formula.

BP02 must be a corollary of BP01. In the only additional boundary case,
`p = n + n`, the assumptions `1<n` and `Prime(p)` contradict the displayed
factorization of `n+n` as `2*n`; no classical inference is needed.

### 2.1 Frozen readable interval surfaces

The following campaign-local identifiers are reserved. They may be added to a
future version of the conservative authoring registry before endpoint
admission, but only after hygiene and exact-AST tests pass. The generic B0
search does not depend on registering them.

```text
BertrandClosed(n,p) := Prime(p) /\ (Lt(n,p) /\ Le(p,n+n))
BertrandStrict(n,p) := Prime(p) /\ (Lt(n,p) /\ Lt(p,n+n))
NoBertrandClosed(n) := forall p. (Lt(n,p) /\ Le(p,n+n)) -> ~Prime(p)
```

Their stable RFC identifiers are respectively
`HA-R6-BERTRAND-D01`, `HA-R6-BERTRAND-D02`, and
`HA-R6-BERTRAND-D03`. They are notation, not predicates added to the kernel.

## 3. Constructive search semantics

The proof must not begin with an undecidable-looking `not exists` and later
extract a witness from its double negation. B0 must close the generic explicit
search theorem

```text
bounded_prime_interval_search :
forall l u.
  (exists p. Prime(p) /\ (Lt(l,p) /\ Le(p,u))) \/
  (forall p. (Lt(l,p) /\ Le(p,u)) -> ~Prime(p))
```

after expanding `Prime`, `Lt`, and `Le`. The positive branch contains the
witness. The negative branch is an explicit pointwise certificate excluding
every prime in the finite interval. The Bertrand proof specializes this
general theorem at `l=n` and `u=n+n`; B0 must not add a redundant named
specialization.

B0 must also close the two generic consequences

```text
prime_interval_exclusion_refutes_witness :
forall l u.
  (forall p. (Lt(l,p) /\ Le(p,u)) -> ~Prime(p)) ->
  ~(exists p. Prime(p) /\ (Lt(l,p) /\ Le(p,u)))

bounded_prime_interval_decidable :
forall l u.
  (exists p. Prime(p) /\ (Lt(l,p) /\ Le(p,u))) \/
  ~(exists p. Prime(p) /\ (Lt(l,p) /\ Le(p,u)))
```

The last row is obtained from the explicit search branch and refutation row;
it is not an excluded-middle instance.

For large `n`, the central-binomial inequalities refute the second branch.
The target then follows by `false.elim` inside that already-decided branch.
This is intuitionistically valid. The following replacement is forbidden:

```text
~NoBertrandClosed(n) -> exists p. BertrandClosed(n,p)
```

unless it is derived through the displayed search theorem. In particular,
neither `~~exists p` nor an appeal to the classical decidability of all
propositions counts as a witness-producing proof.

The executable companion must enumerate only the bounded interval and call
the native checked primality decision procedure. Host computation may be a
regression oracle, but the theorem certificate must contain the object-level
bounded-search argument.

## 4. Frozen trust and representation boundary

No step in this campaign may add or silently assume:

- a kernel rule, arithmetic axiom, excluded middle, `DNE`, Markov's
  principle, or choice;
- primitive binomial coefficients, valuations, primorials, square roots,
  exponentiation, division, remainder, finite sets, lists, sums, or products;
- real numbers, logarithms, derivatives, limits, or an ordered-field oracle;
- a trusted theorem-name lookup, external SMT result, or host-language
  primality result.

Readable `Choose`, `CentralBinom`, `PVal`, `Primorial`, `FloorSqrt`, `Pow`,
`DivRem`, `Product`, and `Sum` calls may be used only as conservative graph
relations whose expansions are checked before kernel replay. Existing `Cut`
proof sharing is permitted because the checker validates the lemma and body;
it is not an arithmetic axiom.

The campaign starts with the existing live policy of 500,000 structural proof
occurrences, 100,000 distinct proof objects, and depth 256. These are resource
limits, not logical rules. They must not be raised pre-emptively. A theorem
that misses a limit must first be split, have its direct dependencies reduced,
or use reviewed conservative definitions. Any proposed limit or proof-DAG
change requires a separate architecture RFC, mutation suite, and independent
review; Bertrand must not depend on such a change.

The stable beta-coded `Product`, `Sum`, `Range`, `Pow`, and `Factorial`
relations are the initial finite-data substrate. The K3C cell-list rows at
Alpha v2 indices 885--901 are `body_checked`, not checked-use facts, and lack
the complete append/restriction/fold API needed here. No Bertrand row may
depend on them until the relevant K3C dependency closure is independently
promoted. A later readable K3 port is welcome but cannot block the proof.

## 5. Inherited checked baseline

Alpha v2 contains 902 enrolled specifications, 2,674 direct edges, and 45
layers. Exactly 570 rows are currently checked-use facts: 432
`stable_closed` and 138 `alpha_closed`. The remaining 331 `body_checked` rows
and one `pending_layered_closure` row are visible specifications but cannot be
used as empty-context hypotheses.

The campaign may reuse checked-use facts including:

- order, strict order, cancellation, monotonicity, and multiplication bounds;
- division/remainder existence and uniqueness;
- equality, divisibility, congruence, and primality decisions;
- prime-divisor existence, Euclid's lemma, greatest-prime-divisor search,
  prime unboundedness, and the fundamental factorization stack;
- beta-coded finite `Product`, `Sum`, and `Range` existence/functionality;
- relational `Pow` and `Factorial` existence, functionality, and successor
  laws;
- finite containment, bounded enumeration, and the checked arithmetic
  normalization lemmas already in the closure.

Every actual theorem specification must list its exact direct dependencies.
"Depends on the arithmetic library" is never an acceptable manifest entry.
Before authoring a row, its proposed dependencies must be checked against the
selected edition's `checked_use` field. A Stable Bertrand release may include
Alpha-closed prerequisites in the same dependency-closed promotion batch, but
it may not refer to an unpromoted Alpha fact.

## 6. Integerized Erdős--Tochiori proof route

Write \(C_n=\binom{2n}{n}\). The proof route is frozen at the level of the
following mathematical spine:

1. construct and characterize prime-power valuations;
2. construct binomial coefficients and prove the central recurrence and
   factorial bridge;
3. prove, for \(n\ge4\),
   \[
     4^n<nC_n;
   \]
4. construct the primorial and prove the entirely discrete bound
   \[
     \prod_{p\le m}p\le4^m;
   \]
5. under `NoBertrandClosed(n)`, partition the prime-power contribution to
   \(C_n\) at \(\lfloor\sqrt{2n}\rfloor\),
   \(\lfloor2n/3\rfloor\), \(n\), and \(2n\), obtaining
   \[
     C_n\le
     (2n)^{\lfloor\sqrt{2n}\rfloor}
     4^{\lfloor2n/3\rfloor};
   \]
6. prove in natural-number arithmetic that, for \(n\ge512\),
   \[
     n(2n)^{\lfloor\sqrt{2n}\rfloor}
     4^{\lfloor2n/3\rfloor}\le4^n;
   \]
7. contradict steps 3, 5, and 6 in the negative branch of the bounded search;
8. cover the remaining positive inputs with a checked finite prime chain.

`FloorSqrt(t,s)` must be a relational integer boundary equivalent to

\[
  s^2\le t<(s+1)^2.
\]

The quotient \(\lfloor2n/3\rfloor\) must be supplied by `DivRem(n+n,3,q,r)`.
No proof certificate may pass through a real square root or logarithm and then
claim that the resulting natural inequality was merely "reified."

The prime-factor upper-bound proof must expose the five ranges:

1. primes at most \(\sqrt{2n}\), each with its complete prime-power
   contribution bounded by \(2n\);
2. primes between \(\sqrt{2n}\) and \(2n/3\), whose exponent is at most one
   and whose product is bounded by the primorial;
3. primes between \(2n/3\) and \(n\), which do not divide \(C_n\);
4. primes between \(n\) and \(2n\), excluded by
   `NoBertrandClosed(n)`;
5. primes above \(2n\), which cannot divide \(C_n\).

This partition is part of the human and formal proof architecture. A single
opaque arithmetic assertion replacing it will not pass review.

## 7. Exact dependency DAG

```text
checked Alpha-v2 baseline
  |-- B0 bounded interval decision
  `-- B1 discrete inequality/fold API
        |-- B2 prime-power valuations and Legendre
        |-- B3 Choose/CentralBinom
        `-- B4 Primorial (also depends on B3)

B2 + B3 + B4 --------------------> B5 central factor upper bound
B1 --------------------------------> B6 native main inequality
B0 + B3 + B5 + B6 ----------------> B7 n >= 512
B0 + B7 + certified prime chain ---> B8 endpoints BP01 and BP02
```

B2 and the definition-independent part of B3 may be developed in parallel.
B4 must not use B7 or either Bertrand endpoint: doing so would make the
primorial bound circular. B6 may be prototyped early, but its release edge is
from B1 only. B8 may use B7 and checked small-prime facts, never a host
enumeration result.

## 8. Binding B0--B8 tranche gates

Each tranche may contain more helper rows than those named here. The named
deliverables and their mathematical content are mandatory.

### B0 — statement, surfaces, and bounded decision

Required deliverables:

- exact expansion, alpha-equivalence, capture-rejection, and native-syntax
  receipts for the generic open-closed interval helpers;
- the support row `prime_strictly_above_decidable`;
- `bounded_prime_interval_search`,
  `prime_interval_exclusion_refutes_witness`, and
  `bounded_prime_interval_decidable` with the exact generic semantics in
  Section 3;
- an executable bounded-search companion whose positive and negative outputs
  agree with the two theorem branches;
- mutation tests rejecting a missing lower bound, a missing upper bound, an
  open upper bound in BP01, and a non-prime witness.

Gate B0 passes only when the expanded statement is parser-pinned, the proof
body checks with zero `DNE`, bounded models cover the interval endpoints, and
the rows are enrolled in Alpha with honest evidence. No headline theorem is
claimed at B0.

### B1 — discrete order, powers, folds, and floor boundaries

Required deliverables:

- relational power monotonicity in base and exponent, multiplication and
  comparison transport, and the concrete powers of 2 and 4 used later;
- finite-product monotonicity, range splitting, uniform-factor bounds, and
  prime-filter product comparison over the stable beta folds;
- quotient-by-3 floor bounds from `DivRem`;
- `FloorSqrt` totality, functionality, square bounds, monotonicity, and the
  counting consequence that at most `s` positive integers are at most `s`.

Gate B1 passes only when no host `pow`, division, square-root, or list theorem
is proof authority and the general fold comparison lemmas close independently
of Bertrand.

### B2 — prime-power valuation and Legendre

Required deliverables:

- a frozen conservative `PVal(p,a,e)` relation with explicit nonzero-domain
  behavior;
- valuation existence and functionality for prime `p` and nonzero `a`;
- valuation laws for one, prime powers, products, and exact division by a
  known prime power;
- Legendre's factorial-valuation formula as a finite relational sum of the
  quotients \(\lfloor n/p^i\rfloor\), with an explicit finite stopping bound.

The risk-gate theorem `prime_power_valuation_mul` must receive an
empty-context certificate before the bulk Legendre script is accepted. Gate
B2 passes only after Legendre's formula is closed for arbitrary natural input
under its exact prime/nonzero premises; a finite table of valuations is not a
substitute.

### B3 — binomial and central-binomial arithmetic

Required deliverables:

- frozen conservative `Choose(n,k,c)` and `CentralBinom(n,c)` relations;
- existence and functionality, zero/boundary laws, Pascal recurrence,
  symmetry, and the factorial bridge;
- central recurrence and positivity;
- `four_pow_lt_mul_central_binom`, stating relationally that
  \(4^n<nC_n\) whenever \(4\le n\);
- the elementary central upper bounds needed by the primorial proof.

Gate B3 passes only when the factorial and recurrence presentations are shown
equivalent on their shared domain and the lower bound is a general induction
theorem, not reflected verification up to a fixed ceiling.

### B4 — filtered prime products and the primorial

Required deliverables:

- frozen conservative `Primorial(m,z)` with totality and functionality;
- prime membership/divisibility characterization, positivity, monotonicity,
  and interval splitting;
- comparison of any duplicate-free bounded prime product with the primorial;
- `primorial_le_four_pow`, relationally proving \(m\#\le4^m\).

Gate B4 passes only if the primorial proof depends on B3 and earlier rows but
not on B7, BP01, BP02, or any theorem equivalent to Bertrand. The dependency
liveness test must reject an injected Bertrand edge.

### B5 — factor ranges and the central-binomial upper bound

Required deliverables:

- every prime divisor of `CentralBinom(n,C)` is at most `n+n`;
- each complete prime-power contribution is at most `n+n`;
- if \(p^2>2n\), the valuation contribution of `p` is at most one;
- primes with \(2n/3<p\le n\) have zero contribution;
- the explicit no-interval-prime assumption eliminates \(n<p\le2n\);
- `central_binom_factorization_small` and
  `central_binom_le_of_no_bertrand_prime` implementing the five-range split
  in Section 6.

In relational form, the final row must say that if `2<n`,
`NoBertrandClosed(n)`, `CentralBinom(n,C)`, `FloorSqrt(n+n,s)`,
`DivRem(n+n,3,q,r)`, `Pow(n+n,s,A)`, and `Pow(4,q,B)`, then
`Le(C,A*B)`.

Gate B5 passes only with a prime-by-prime valuation audit and a second bounded
semantic oracle on small inputs. A proof that assumes unique raw beta codes,
rather than extensional finite-product values, is rejected.

### B6 — native main inequality

Required deliverable: `bertrand_main_inequality_nat`.

It must state relationally that if `Le(512,n)`, `FloorSqrt(n+n,s)`,
`DivRem(n+n,3,q,r)`, `Pow(n+n,s,A)`, `Pow(4,q,B)`, and `Pow(4,n,F)`, then

```text
Le(n * A * B,F)
```

with the displayed associations frozen by the subordinate statement RFC.
The certificate must use only natural-number inequalities, relational floors,
and ordinary induction. Discrete block or dyadic induction is permitted.
Real logarithms, real square roots, calculus, numerical floating-point
verification, and a finite check of arbitrarily many values are not proofs of
this row.

B6 is the second campaign risk gate. Before B4/B5 proof volume grows large,
the team must close either this exact row or a general induction invariant
from which it follows by a short checked body. Failure triggers route review;
it does not authorize silently increasing kernel limits.

### B7 — the large-input theorem

Required deliverable: `bertrand_eventually_closed_upper`:

\[
  \forall n\ge512\;\exists p\,\operatorname{BertrandClosed}(n,p).
\]

The proof must specialize `bounded_prime_interval_search` at `n,n+n`. Its
witness branch returns the supplied prime. Its explicit no-prime branch
combines B3, B5, and B6 to derive false. Gate B7 passes only if deleting the
bounded-search dependency or replacing the negative branch by `~~exists`
makes the audit fail.

### B8 — finite coverage and the two capstones

The finite covering chain is frozen initially as

```text
2, 3, 5, 7, 13, 23, 43, 83, 163, 317, 521
```

Each entry must have a native primality certificate. Each consecutive
covering inequality must be a checked natural-number theorem. A general
covering lemma must show that these facts provide `BertrandClosed(n,p)` for
every `0<n<512`; an external loop or a host assertion that all 511 cases
passed is not enough.

Required deliverables:

- `bertrand_small_closed_upper` for `0<n<512`;
- BP01 `bertrand_closed_upper`, by the constructive split at 512;
- the factorization boundary excluding `p=n+n` when `1<n`;
- BP02 `bertrand_strict` as a corollary of BP01.

Gate B8 and the campaign pass only after the complete dependency closure of
BP01 and BP02 satisfies Sections 10 and 11.

## 9. Early go/no-go and risk policy

Two experiments dominate feasibility and must be attempted early:

| Gate | Required evidence | Failure response |
|---|---|---|
| RG-V | general `PVal` existence/functionality and closed multiplication law within current limits | redesign the valuation relation or factorization route before building Legendre/Choose clients |
| RG-I | exact B6 inequality, or a closed general invariant with a short exact specialization | redesign the integer inequality and threshold; do not import analysis or raise limits silently |

Additional monitored risks are:

| Risk | Required mitigation |
|---|---|
| dependency explosion | profile every 10--25 row microbatch; minimize direct edges before closure |
| formula expansion | use only reviewed hygienic definitions with exact AST receipts and bounded expansion |
| circular primorial proof | machine-reject dependencies from B4 to B7/B8/BP01/BP02 |
| off-by-one drift | mutate every `<`/`<=`, threshold, floor, and endpoint boundary |
| constructive leakage | scan every body and closed certificate for `DNE`; keep the explicit search disjunction live |
| false finite confidence | separate semantic testing from the general induction certificate |
| K3C availability | remain on stable beta folds until K3C is independently promoted |
| remote loss | enforce the commit/push seal in Section 12 after every accepted microbatch |

The initial planning envelope is approximately 120--220 reusable lemmas over
six to ten promotion microbatches, with roughly a factor-of-two uncertainty.
This is a capacity estimate, not a theorem-count target and not a deadline.
Quality and a small trustworthy dependency closure take priority over count.

## 10. Validation contract for every theorem row

Every candidate row must have:

1. one exact expanded first-order statement and its SHA-256;
2. a defined statement, when used, with an exact AST-equivalence receipt;
3. an ordered direct-dependency list and dependency digest;
4. a dependency-curried tactic body accepted by the ordinary intuitionistic
   checker;
5. at least one nearby false mutation rejected by the parser, tactic engine,
   checker, or semantic gate as appropriate;
6. bounded semantic tests for boundary-heavy arithmetic statements;
7. a proof-node/depth/object/edge/reuse/`Cut`/`DNE` receipt;
8. source path, line, source SHA, summary, and informal proof note;
9. deterministic replay in a clean process.

Each 10--25 theorem microbatch must additionally run:

- dependency acyclicity and link-liveness checks;
- unused and reachability-redundant dependency review;
- two independent cold empty-context closures for the proposed checked-use
  batch, preferably on WMI when available;
- equality of theorem formula, certificate digest, and structural receipt
  across the two passes;
- current resource-policy checks and zero-`DNE` scans;
- negative tests for fabricated evidence links and evidence-status upgrades.

External computer algebra or another proof assistant may cross-check
arithmetic identities. Its result is never certificate authority. A reflected
finite calculation counts only when the reflection theorem and the concrete
certificate replay in native HA.

## 11. Alpha and Stable evidence/promotion policy

This campaign inherits the additive edition policy in
[`PLAN/12_ha_number_theory_campaign.md`](../../PLAN/12_ha_number_theory_campaign.md#2026-08-09--current-additive-alpha-v2--stable-release-pipeline).
The meanings are fixed:

| Evidence | Meaning | Checked-use fact? |
|---|---|---|
| `body_checked` | the dependency-curried body checks | no |
| `pending_layered_closure` | the body checks but the selected closure is not sealed | no |
| `alpha_closed` | an Alpha-only row has a sealed empty-context certificate | yes |
| `stable_closed` | a Stable member has a sealed empty-context certificate | yes |

The promotion sequence is binding:

1. review and freeze the subordinate tranche RFC;
2. author isolated candidate rows and focused tests;
3. enroll a reviewed checked body in the next additive Alpha version with its
   immutable statement, origin, provenance, source, script, and evidence;
4. keep all body-only rows fail-closed in theorem lookup and replay;
5. obtain repeated cold empty-context receipts for an exact
   dependency-closed batch;
6. run kernel, capacity, determinism, zero-`DNE`, mutation,
   dependency-liveness, identity, and evidence-link gates;
7. upgrade the qualifying Alpha rows to checked-use evidence without changing
   their logical identity or enrollment origin;
8. promote only a dependency-closed keyed subset into a new append-only
   Stable channel;
9. rebuild and verify the Book, defined edition, proof explorer, dependency
   graph, Obsidian notes, and release metadata.

Promotion changes membership and evidence, never the logical specification,
canonical Alpha position, enrollment origin, primary source, or provenance.
The BP01/BP02 release may leave unrelated Alpha rows unpromoted. No
documentation may describe a `body_checked` Bertrand row as proved, public,
closed, or available to later proofs.

## 12. Git, GitHub, WMI, and loss-prevention seal

The authoritative repository is the local clone of
[`nasqret/vietnam2026`](https://github.com/nasqret/vietnam2026), and every
accepted campaign microbatch must be preserved in both local Git and the
configured GitHub remote before the next microbatch begins.

For each microbatch:

1. start from a recorded commit and inspect the dirty tree;
2. preserve unrelated user/agent changes and stage only reviewed campaign
   paths;
3. run the tranche's fast local gates and record their commands;
4. commit source, tests, RFC/status documentation, and deterministic small
   artifacts together, or in an explicitly linked sequence;
5. push the commit and verify that the remote branch resolves to it;
6. record the commit SHA in the campaign journal and any WMI manifest;
7. for remote closure, bind the clean commit, payload SHA-256, entry count,
   byte count, job ID, environment, two-pass receipts, and output artifact;
8. after receipt review, commit and push the immutable report before changing
   evidence status.

Temporary caches, virtual environments, raw model checkpoints, and unreviewed
logs must not be committed. A Git commit or JSON hash does not make a proof
valid; the kernel certificate does. Conversely, an uncommitted successful
experiment is not a durable campaign result.

Stable release candidates must build from a clean clone of the pushed commit.
Force-pushing a sealed campaign branch, replacing an artifact in place, or
editing a historical Alpha/Stable snapshot is forbidden.

## 13. Source and prior-art ledger

Snapshot date: **9 August 2026**. This ledger is evidence for route selection
and cross-validation, not proof authority and not an unconditional novelty
claim.

| ID | Source | Classification | Campaign use | Status |
|---|---|---|---|---|
| BP-S01 | [A6 in the controlling HA campaign blueprint](ha-number-theory-formalization-campaign-blueprint.md#A6-bertrands-postulate), SHA-256 `8fd25fc3e68259e1a16c935d35dacccefa20a473cdec35f8771cb1d5d806f205` | local binding predecessor | strict-HA target, route, risk, acceptance boundary | archived locally |
| BP-S02 | P. Erdős, [*Beweis eines Satzes von Tschebyschef*](https://acta.bibl.u-szeged.hu/13396/), Acta Litt. Sci. Szeged 5 (1932), 194--198 | historical mathematical proof | original elementary central-binomial route | metadata inspected 2026-08-09; archive before quotation |
| BP-S03 | M. Aigner and G. Ziegler, *Proofs from THE BOOK*, Bertrand chapter | textbook mathematical proof | human proof architecture and inequality comparison | route reference only |
| BP-S04 | [Mathlib Bertrand formalization](https://leanprover-community.github.io/mathlib_docs/number_theory/bertrand.html) | classical/rich-host formalization | five prime ranges, threshold 512, covering theorem, regression oracle | inspected 2026-08-09 |
| BP-S05 | [Mathlib central-binomial API](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Choose/Central.html) | rich-host formalization | central recurrence and Tochiori lower bound \(4^n<nC_n\) for \(n\ge4\) | inspected 2026-08-09 |
| BP-S06 | [Mathlib primorial API](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Primorial.html) | rich-host formalization | primorial definitions, splits, and \(m\#\le4^m\) oracle | inspected 2026-08-09 |
| BP-S07 | M. Carneiro, [*Arithmetic in Metamath, Case Study: Bertrand's Postulate*](https://arxiv.org/abs/1503.02349), 2015 | first-order-style formalization in a different foundation | proof decomposition, certificate-size comparison, mutation ideas | identified; foundation differs from strict HA target |
| BP-S08 | [Rocq-community Bertrand project](https://github.com/rocq-community/bertrand), Laurent Théry | constructive/rich-host formalization with extracted application | alternate proof organization and executable cross-check | inspected 2026-08-09; not an object-level HA certificate |
| BP-S09 | J. Biendarra and M. Eberl, [*Bertrand's postulate*](https://isa-afp.org/entries/Bertrands_Postulate.html), Archive of Formal Proofs, 2017 | Isabelle/HOL formalization ported from John Harrison's HOL Light proof | alternate threshold and finite-coverage organization | inspected 2026-08-09; classical higher-order foundation |

The Mathlib proof explicitly uses real analysis to establish its main
inequality and then reifies a natural statement. That code is valuable prior
art but cannot be transplanted as the native B6 certificate. The Rocq project
is likewise a formal proof in another host foundation, not evidence that the
frozen Peano Lab formulas have native HA certificates.

No public broad library exporting this exact theorem as a checked derivation
in the repository's strict object-level HA calculus was identified in the
controlling audit. The permissible novelty wording remains:

> To the best of our knowledge under the documented search protocol, this is
> a candidate first publicly available machine-checked object-level HA
> derivation.

That wording may be used only after BP01/BP02 close and the prior-art audit is
refreshed. Discovery of prior work changes the scholarship ledger, not the
validity of a native proof.

## 14. Immediate execution order

The first campaign round is deliberately narrow:

1. B0 statement/decision candidate and its exact surface tests;
2. the RG-V valuation multiplication microcapstone;
3. the B1 power/order subset needed to state RG-I;
4. an early RG-I/B6 invariant prototype;
5. only after both risk gates are credible, expand B2 and B3 in parallel.

This order tests the two genuinely new difficulties before the repository
accumulates a large body of dependent scripts. It does not weaken the B0--B8
release order or permit a later theorem to use body-only evidence.

## 15. Current conclusion

The campaign is authorized to begin. The existing arithmetic system is
mathematically expressive enough and has a strong checked substrate. The
missing work is a new quantitative-combinatorics and integer-inequality
library, not a new logic.

This RFC proves nothing by itself. Its first proof-bearing milestone is B0;
its first feasibility checkpoint is the pair RG-V/RG-I; and its completion
criterion is the Stable, empty-context, zero-`DNE` closure of BP01 and BP02
with the full publication and remote seal.
