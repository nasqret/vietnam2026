# General finite signed Dirichlet inverses toward G009

Date: 2026-08-29. Starting commit:
`cef66ddf52658ee9f878b9a81ff8eca19f991485`.
This is local implementation under
[PLAN/19](../../PLAN/19_general_dirichlet_inverses.md), not a commit, push,
deployment, Alpha/Stable admission, or change to historical proof artifacts.

**Integration status: complete for this local inverse tranche.** All forty
theorems pass complete original HA and same-byte independent compiled-Lean
verification. All nine principal ordinary certificates, the exact statement
novelty comparison and 1,555 distinct new focused tests pass. The final fresh
thirteen-job audit and its same-run 72 explorer tests completed successfully,
producing 173 canonical local files. Full G009 remains open for multiplicative
closure; this is not an Alpha/Stable admission or deployment.

## Exact mathematical scope

The new tranche has forty distinct statements, 132 direct prerequisites and
1,712 tactic commands:

| Chapter | Statements | Direct prerequisites | Commands |
| --- | ---: | ---: | ---: |
| Signed units and affine equations | 9 | 36 | 401 |
| Triangular convolution and input extension | 10 | 43 | 547 |
| General construction, criterion and uniqueness | 21 | 53 | 764 |

Signed code 2 represents +1; code 1 represents -1. The three new definitions
are conservative abbreviations in the unchanged first-order HA signature:

```text
SignedUnit(u) := u=2 or u=1.
DirichletUnitAtOne(F) := ArithAt(F,1,2) or ArithAt(F,1,1).
DirichletInverse(N,F,G) :=
  exists E. KroneckerDeltaTable(N,E) and
    (DirichletTable(N,F,G,E) and DirichletTable(N,G,F,E)).
```

The inverse graph requires an actual delta table and both actual convolution
tables. It does not contain or assume the unit-at-one criterion. The criterion
is proved as two implications:

```text
forall N F. ArithTable(N,F) ->
  ((exists G. DirichletInverse(N,F,G)) <->
   (N=0 or DirichletUnitAtOne(F))).
```

The construction proves a stronger solver for every actual target table T:

```text
forall N F T u w. ArithTable(N,F) -> ArithTable(N,T) ->
  ArithAt(F,1,u) -> SignedUnit(u) ->
  exists G. DirichletTable(N,G,F,T) and ArithAt(G,0,w).
```

This is a genuinely constructed finite solution for each bound N, not one
beta code claimed to realize a global inverse for every bound. At n=S k,
the construction first produces the strict-prefix convolution remainder from
d<n, solves the actual signed equation r+x*u=e, and appends x as G(n).
The last divisor d=n has quotient one and coefficient F(1). Restricted input
transport preserves all earlier convolution entries and the chosen value at
zero. Specialization to an independently constructed delta table, followed by
the already proved commutativity theorem, establishes both inverse laws.

In ordinary integer notation the constructed algorithm is
`g(n)=u*(t(n)-sum(g(d)*f(n/d) : d|n, 0<d<n))`, where u=f(1) is +1 or -1.
For inversion, t is the delta table. This notation describes the proved
finite signed graphs; it does not add a division, summation or function oracle.

For N>0, the actual convolution at one and classification of signed products
equal to +1 prove necessity. For N=0 the constructor still supplies genuine
table witnesses, but no condition at F(1) is needed. Uniqueness compares only
represented values at positive indices; it never equates arbitrary table codes
or values at zero. Restriction, positive overlap compatibility and inversion
of an inverse are also proved. Associativity supplies positive uniqueness
through (G*F)*H=G*(F*H), with actual delta witnesses on both sides.

The exact authoring contracts and conditional-body evidence remain frozen in
[signed units](dirichlet-signed-unit-rfc-v1.md),
[triangular convolution](dirichlet-triangular-rfc-v1.md), and
[general inverses](dirichlet-inverse-rfc-v1.md). Their source SHA-256 pins are:

- Signed units: `263ae0497206cee991e34e08f03df3b1922fc4918e67d4d300887aa1ba7de4df`.
- Triangular convolution: `5b6e585a4b2df25dee069ddec17e26cddc52c329d45ee7c5fcf307314b10f8ef`.
- General inverses: `05347563a82486859a49539e99055504720cc823e14b310389e1d90766a85379`.

## Evidence policy and inherited basis

Exact AST novelty compares all forty rows with one another and all 3,756
earlier statements: 3,222 Alpha statements plus four research generations of
170, 126, 125 and 113. The first two research generations are published; the
last two are local. Inherited research bodies are included and checked, not
assumed or counted as newly proved statements. The forty-row comparison
passed in 46.92 seconds with peak RSS 382,435,328 bytes.

All 716 distinct mathematical tests pass: 215 signed-unit, 220 triangular and
281 independently authored inverse tests. The inverse suite checks every
declared prerequisite both missing and poisoned, all twenty-one independently
expanded target statements and genuine original HA bodies, false conclusions,
invalid strengthenings, binder hygiene and actual beta-coded examples. Its
eighteen bounded windows total 610.801 seconds, with longest window 85.372
seconds and peak RSS 638,533,632 bytes. The twenty-one inverse bodies contain
1,278 proof occurrences and 1,278 measured objects, with maximum body 208
occurrences and depth 67. Their independent test file is frozen at SHA-256
`6f6dcd1bd2340ce30ba25e1b44166eb4ce73016f08ae0185067bdd81077449d1`.

Every proof/authoring window retains CPU limits (170,175) seconds, wall 180
seconds, observed RSS 1,536 MiB, and all unchanged syntax, proof-object, depth,
bundle and payload ceilings. The thirteen-job audit separately schedules one
whole-tranche novelty check, three complete original-HA/same-byte compiled-Lean
family checks and nine ordinary empty-context principal certificates. The
2,585-second controller deadline is only the scheduling allowance for those
bounded jobs. The separately bounded live render/test child adds 185 seconds
of scheduling/cleanup time, not a larger proof window.

No previous success receipt is a proof input. All sixteen historical seed
identities are authenticated, and every supplied seed body is actually checked,
including unused seed nodes. Final worker envelopes bind exact sources,
specifications, parent catalog, bundle bytes, checker, random nonce and limits.
Source changes and malformed, stale, partial or mismatched evidence fail closed.
The final audit write is exclusive and occurs only after all required gates.

The unchanged compiled Lean checker is 106,787,344 bytes, SHA-256
`22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033`.
It is not rebuilt or replaced in this tranche.

### Complete original HA proof bundles

All three final artifacts passed complete original HA checking. Counts below
include inherited support and the packaging root; they are not additional
new theorems or disjoint dependency inventories.

| Bundle | Owned | Nodes | Edges | Body occurrences | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Signed units | 9 | 71 | 146 | 4,704 | 214,864 |
| Triangular convolution | 10 | 219 | 541 | 12,776 | 1,488,366 |
| General inverses | 21 | 401 | 1,150 | 29,441 | 7,257,507 |

Literal artifact SHA-256 pins:

- [Signed units](artifacts/dirichlet-signed-units-proof-bundle-v1.json):
  `5045f1feb2f21a79ecb3cb03f95aaefeb8f01e616a4aa8640cbada3da62ae47b`.
- [Triangular convolution](artifacts/dirichlet-triangular-proof-bundle-v1.json):
  `d2d1b032400b46679658f6b196272df3e0869378a651e711e1b7985778e121e1`.
- [General inverses](artifacts/dirichlet-inverses-proof-bundle-v1.json):
  `420f08dcb5c67a260a28f391bdaa5b1f75464c73dc174fbe5cdcd4d08336c826`.

Their successful canonical authoring windows took 51.907, 104.537 and 148.844
seconds, respectively; peak resident bytes were 725,499,904, 838,270,976 and
800,866,304. These are original-HA authoring metrics, not substitutes for the
separate independent Lean and ordinary-root gates. Independent checks of all
three complete artifacts have now also passed the unchanged compiled Lean
checker. The final thirteen-worker audit also rechecked all three successfully.

All nine principals have passed actual ordinary replay and original
empty-context HA checking, with rejection of a false conclusion:

| Principal | Bundle node | Ordinary certificate nodes |
| --- | ---: | ---: |
| `dirichlet_signed_unit_product_classification` | 62 | 2,126 |
| `dirichlet_signed_unit_affine_solve` | 68 | 4,634 |
| `dirichlet_signed_unit_affine_unique` | 69 | 4,908 |
| `dirichlet_convolution_first_input_append_step` | 215 | 15,194 |
| `dirichlet_convolution_at_one_iff` | 217 | 16,711 |
| `dirichlet_convolution_strict_prefix_exists` | 213 | 11,272 |
| `dirichlet_unit_equation_construct` | 387 | 18,965 |
| `dirichlet_inverse_criterion` | 397 | 29,862 |
| `dirichlet_inverse_exists_positive_unique` | 399 | 38,832 |

The three main inverse principals passed in separate registry-test windows
of 92.584, 114.684 and 160.012 seconds, with peak RSS 742,817,792, 717,242,368
and 615,645,184 bytes, respectively. Each includes a fresh complete original-HA
and same-byte Lean family fixture, the replay helper's complete HA recheck,
and the final exact-target empty-context check. These completed windows do
not replace the final fresh audit of the same complete nine-root inventory.

The larger positive-uniqueness root was additionally tested through the actual
bounded audit worker, including both full semantic source bindings. It again
accepted the exact 38,832-node certificate with peak worker RSS 433,569,792
bytes. Parent metadata preparation took 53.800 seconds; the complete one-job
controller took 216.489 seconds, so worker and transport together took 162.688
seconds, inside the actual 180-second worker deadline. Parent peak RSS was
646,168,576 bytes. The controller's 365-second scheduling allowance is one
180-second preparation allowance plus one 185-second worker/cleanup slot; it
does not enlarge a proof window. This extra diagnostic is not counted as an
additional pytest case or substituted for the final thirteen-job audit.

### Bounded authoring and the historical prerequisite gap

The first complete signed-unit assembly was rejected by the unchanged
pre-write RSS ceiling after scanning twenty historical proof providers for
three missing Alpha prerequisites. No artifact was written. Its exact peak
and elapsed time were not captured; only the measured threshold violation
above 1,610,612,736 bytes is known, and no estimate is substituted.

An independent exact-target/ordered-premise scan of all sixteen research
bundles found none of these three missing bodies: `signed_decode_normal`,
`signed_add_negate_right_zero`, `signed_add_negate_left_zero`. This diagnostic
took 7.916 seconds and 675,168,256 peak resident bytes, and made no proof claim.

A private proof-data seed freshly checked all 531 nodes of the frozen Möbius
bundle, reconstructed the three exact Alpha bodies with the unchanged tactic
engine and body-envelope limits, and packaged them with the old root. The
first draft omitted that old root from the new packaging, and the original
unreachable-node guard correctly rejected it before any write: 49.914 seconds,
727,711,744 peak resident bytes. Including the genuine old root made all 535
nodes reachable; the unchanged complete checker then accepted all 535 nodes
in 62.602 seconds with peak RSS 783,876,096 bytes. No guard was relaxed.

The resulting private proof data has 1,587 edges, 40,136 body occurrences and
6,652,362 bytes, SHA-256
`bc422b2483f139021a9f355618fb3a17121e3c1c84f2f357eaf59d9229ad642f`.
It is neither a new theorem inventory nor an admission or Lean receipt.
The canonical exporter checks every seed node again. All sixteen prior-seed
and twenty historical-provider byte identities remain authenticated normally;
only unnecessary provider decoding is avoided. The final local proof-data
bundles are self-contained, so verification needs no private seed path.

The first one-window twenty-one-result assembly then reached the unchanged
CPU ceiling (SIGXCPU, exit 152) after reconstructing all 23 required bodies
(21 new, two inherited), but before the final complete-bundle check and write.
No final artifact or full-check success was recorded. Exact peak/time metrics
were not available after that signal. The remedy again changes proof-data
batching, not a theorem or limit: the first nine theorem rows were assembled
and completely HA-checked in their own original window. This means nine
**theorems**, not a restriction to mathematical bounds N<=9; the strong
constructor is still universally quantified over every finite N.

That genuine intermediate bundle contains 285 nodes, 766 edges, 19,143 body
occurrences and 2,701,919 bytes, SHA-256
`bfa1935232673e0f426ddaf1dbbf7ed2d6f58c779add3ee043c4edbbcbdceca0`.
It passed in 100.507 seconds with peak RSS 787,234,816 bytes. It remains
private staging proof data, not the full twenty-one-result checkpoint or a
Lean/admission receipt. The final exporter rechecks the whole intermediate
bundle before using its actual bodies.

### Additive verification controls

All 76 support-selection tests pass. They distinguish all four inherited
research generations from current cross-track support, authenticate sixteen
historical seeds, and keep exact novelty separate from proof acceptance. All
35 exporter tests pass, including genuine prefix construction, corrupt unused
seed rejection and original-HA checking followed by a deliberately triggered
pre-write RSS rejection. They neither change a historical source nor accept
a stored success report.

All 104 new render-process transport tests pass. After the presentation-only
binding optimization and final source freeze, the affected suite was freshly
rerun in 5.778 seconds with peak RSS 86,310,912 bytes. They exercise fail-closed process
messages, original resource bounds, source changes, live handoff ownership and
exclusive publication gates. The new renderer initially failed to copy the
keyword-only defaults when reusing a pure historical rendering function; the
new module now preserves those defaults, with an actual function-signature
regression test. No historical renderer or old 102-case test file was edited.

All 154 new audit protocol cases pass. Its 147 non-live cases passed in
101.162 seconds with peak RSS 422,019,072 bytes. Three separate
non-vacuous support-role cases also passed in 30.368, 31.911 and 37.120 seconds,
with peaks 408,338,432, 453,263,360 and 670,990,336 bytes. Four separate real
worker cases then checked the signed-unit family with HA and compiled Lean,
and its three ordinary principal roots. These passed in 111.219, 116.534,
118.788 and 114.217 seconds, with outer-window peaks 442,859,520, 434,454,528,
455,737,344 and 441,696,256 bytes.

All 192 registry cases also pass in distinct original-bounded windows. They
include complete HA/Lean checks, all nine exact ordinary principals, thirty
actual bundle-corruption cases, every inherited support role, incorrect
returned formulas/specifications with genuine certificates, and failure
propagation before later checks or success labels. Two oversized regression
batches reached SIGXCPU (exit 152): an early sixteen-case metadata/support
batch and a later constructor-plus-ten-mutations batch. Neither produced a
final resource receipt or changed an artifact. Exact peak/time after those
signals are unknown. Every assigned case was rerun successfully in smaller
windows with unchanged assertions and limits; partial runs and repeated setup
checks are not counted as additional passing cases. The longest successful
registry window was 160.012 seconds; maximum peak RSS was 742,817,792 bytes.
The 31 successful windows total 2,316.997 seconds. They executed 193 cases,
including one known repeated invalid-record case counted only once; the final
192 distinct node IDs exactly match all 192 collected cases, with no omissions.

Frozen additive control identities:

- Support source: `000e3e7541eb8747a6df6c319ba6169119049ae8acb30fd4c0521c1e8f3e8939`.
- Exporter source: `0ee0d99faef8ca0882f1342832a651408e887c877dcb23fa7d5cda940b6aa3d1`.
- Registry source: `9f1808cb6b6e65f1612e0538da68c1df83106447df29a053db27c91734fe14e2`.
- Registry tests: `d8f2fcfa5e67ce0453b818f2bc16f9f8cd31ba04f9d044bc24f58511fbc266b0`.
- Audit source: `c1146fc92211da6aade3bc527939faee52c9af455a7293d1cef7f6b35d05e8d1`.
- Audit tests: `130a20de9c11f7c0e237d3c3c4e9215e45d3839dcd0be9e782688316dd451a7c`.
- Render-process tests: `400c617125592d631d57ef68304e612c5eedbeed4452361ffbb4f5872e343ba1`.

## Definitions, maps and local application

The additive definition DAG contains ND0313 SignedUnit, ND0314
DirichletUnitAtOne and ND0315 DirichletInverse. The 369 historical definition
objects are retained. The direct UnitAtOne graph uses ArithAt, not SignedUnit;
the bridge between them is a theorem, not an invented definition edge. The
inverse graph depends directly on KroneckerDeltaTable and DirichletTable.

The complete conservative definition DAG has 372 nodes, 787 actual expansion
edges and maximum zero-based layer 12. All 96 definition/adapter tests pass
in 30.27 seconds, peak RSS 94,846,976 bytes. They check every historical record,
new parameter alignment, binder capture, compound/large/zero/repeated terms,
hostile identities and cycles, and exact AST round trips for all forty
statements and all 1,712 local tactic commands. Definition expansion,
theorem-use of notation and theorem prerequisites remain distinct edge kinds;
only theorem prerequisites determine proof paths.

Before launching the combined audit, a presentation-only resource preflight
hit the unchanged 170-second CPU soft limit (SIGXCPU, exit 152) during its
last render-source binding check. Completed phase measurements totaled
151.482603 CPU seconds before that final call; the last observed RSS was
551,813,120 bytes. Final elapsed time and peak RSS were not recorded, and are
not inferred from the partial samples. This diagnostic did not run proof
workers, render pages or write a receipt. Repeated parsing of the same frozen
statement inventories at presentation boundaries caused the excess. The new
builder now freshly fingerprints exact source bytes and registered metadata
at those boundaries, while leaving every semantic audit binding and actual
proof job unchanged. It uses the same live selected syntax for display lookup,
with exact plan, target, prerequisite, role-partition, topology, reachability,
coverage and duplicate-conflict checks. No success receipt, timestamp or prior
hash is used as a shortcut for checking current bytes.

All 110 new presentation-binding tests pass: 77 byte/metadata/path tests in
10.48 seconds, peak RSS 704,921,600 bytes; 33 actual-retained-syntax tests in
106.275 seconds, peak RSS 668,631,040 bytes. The byte tests caught a new-reader
format mismatch between the worker protocol's compact JSON and the frozen
snapshot's pretty JSON. The new reader now checks the original pretty
canonical bytes under their unchanged literal size and SHA-256 pin. The tests
exercise actual source, artifact, checker, old-snapshot and asset mutations;
they do not replace a proof checker with an accepting mock. Independent review
of both the implementation and the tests passed.

The final parent resource profile passed in 135.678 CPU / 141.839 wall seconds,
peak RSS 496,910,336 bytes. It includes all three source-selected expected
metadata plans, both unchanged semantic audit bindings, both fresh byte
boundaries and the 486 historical-input checks. The actual pure render
components took 31.304 CPU / 31.607 wall seconds. Even including their separate
syntax-only preparation in the same diagnostic process, the complete window
passed in 132.209 CPU / 133.151 wall seconds, peak RSS 823,083,008 bytes. It
checked all nine presentation boundaries, the independent comparison table,
all forty statement and 1,712 script compactions, and actual bundle metrics.
Neither resource profile emits a proof-acceptance report or verified pages.
The subsequent combined thirteen-job audit and all 72 live explorer tests
passed on the frozen sources below.

Frozen presentation source identities:

- Builder: `5a99d2721e914ba8916821deb79adfffc724073ec217439bf9cdd5da1968468f`.
- Binding tests: `4de81c6da2d203de272a1e6e67fe8d61a02ca4820203afffa700a1f5a1d6b77d`.
- Live explorer tests: `8da3b1adc8ccadec2ed258b4fbb5700d836d75dc4e3c007052b54cf937a9aa18`.

### Final live audit and canonical readers

The actual command was:

```sh
PYTHONPATH=peano-lab/py:scripts PYTHONMALLOC=malloc \
  python3 -u scripts/build_constructive_dirichlet_inverse_explorer.py --test --write-audit
```

It exited successfully after 1,280.000 seconds, including all thirteen fresh
proof jobs and the separate original-bounded renderer. All 72 live reader
tests passed in 37.06 seconds against the same source-bound in-memory handoff;
no earlier success report supplied proof authority. The true maximum observed
proof-worker RSS was 691,306,496 bytes, the render child's was 590,692,352 bytes,
and the controller's was 426,541,056 bytes. Every proof and render window kept
the original CPU, wall, RSS and proof-object limits. The standalone audit was
written exclusively only after the child, tests, output hashes and final
source checks all passed.

The [local reader library](../../book/_static/constructive-dirichlet-inverse-explorer/index.html)
contains 173 files, including 144 HTML pages, totaling 33,274,839 bytes.
Its [inverse graph](../../book/_static/constructive-dirichlet-inverse-explorer/dirichlet-inverses/explorer/defined/graph.html)
opens on criterion IV0013. The signed-unit, triangular and inverse readers
use respectively 4, 19 and 24 definitions, with 2, 33 and 41 actual expansion
edges. The full additive library registry remains the 372-node, 787-edge DAG
described above. All three readers preserve the Quadratic Reciprocity layout
and five literal assets, with exact/defined views, three distinct edge kinds,
proof-only paths and working navigation to all four inherited generations.

Literal output identities:

| Output | Bytes | SHA-256 |
| --- | ---: | --- |
| [Standalone audit](artifacts/dirichlet-inverse-checkpoints-v1.json) | 21,031 | `6fc666c053658a7781619d8812b4c1beb62d016ce7ee8d5915b5e573e0142ad7` |
| [Reader manifest](../../book/_static/constructive-dirichlet-inverse-explorer/manifest.json) | 29,643 | `0ca7c37be32f0f956b4727d60a8876d29c7b4eb97ca8a4d6c9a8195c25218568` |
| [Reader inventory](../../book/_static/constructive-dirichlet-inverse-explorer/checkpoints.json) | 21,114 | `d72918c65345094734031dfc8eb39b76f253581c94606206f5ce977adc5a4285` |

The snapshot's `proof-audit.json` is byte-identical to the standalone audit.
Logical checkpoint digest:
`893fb32701bf85235cc15825357cdfed30b5f1bf168e2df669d1525336680ac3`.
Render/source binding:
`e45349066639e43ca70eebf6d64865105b9645f94f8c33da1e3cd68c6d30b775`.
An independent final read-only scan checked every manifest member's bytes and
hash, the exact file inventory with no extras or symlinks, all nine saved
certificate counts, non-admission flags, and equality of the two audit copies.

### Distinct focused test totals

| New suite | Passing cases |
| --- | ---: |
| Signed-unit mathematics | 215 |
| Triangular-convolution mathematics | 220 |
| General-inverse mathematics | 281 |
| Support selection | 76 |
| Exporter | 35 |
| Complete-checkpoint registry | 192 |
| Fresh audit protocol | 154 |
| Definitions, DAG and adapter | 96 |
| Render-process transport | 104 |
| Presentation binding and retained syntax | 110 |
| Same-live-run readers and graphs | 72 |
| **Total distinct new cases** | **1,555** |

Repeated preflights, setup checks and the extra critical-worker diagnostic do
not increase this total. The unchanged focused controls below add 743 passing
cases and one independently identified pre-existing website-test failure:
2,298 passing cases overall in this focused campaign, not a claim that the
entire repository test suite was run or is green.

### Local application and unchanged controls

The local browser source inventory now contains 507 Python files. Its
529-entry content manifest has 508 Python records, twenty unchanged historical
proof artifacts and the worker. The application identity is
`a-3c18234f975c`, build `2026-08-29c`; manifest SHA-256 is
`3c18234f975c9dcd626e7a0d63d371c72a7b2bab947542b58188aba32f9aa472`.
Inventory and manifest checks pass. No application release was uploaded.

The new local Make targets are `check-constructive-dirichlet-inverse` and
`book-constructive-dirichlet-inverse-explorer`; neither is a stage-proofs input.
Original HA/kernel, syntax, cut, formula-DAG, bundle, replay and browser-shell
controls passed 182 tests in 2.47 seconds, peak RSS 133,382,144 bytes. The
unchanged defined syntax, defined edition, formula compaction and compact
double-and-add numeral controls passed 220 tests in 25.84 seconds, peak RSS
1,179,172,864 bytes. These are focused local regressions, not remote CI claims.

Additional unchanged global-definition, deployment-contract and current-site
checks passed 310 cases in 63.17 seconds, peak RSS 253,100,032 bytes, with one
**pre-existing failure**:
`test_public_hub_publishes_every_current_independently_versioned_family_route`.
That test expects only the 44 Alpha-family routes, but the committed hub
already contains nine primary actions for the published research checkpoints.
The hub, test, all eleven inspected family manifests, channel metadata and
atlas input are byte-identical to HEAD. Hub/test Git blob identities are
`8308ed96341086e84560a91c9dee4aeba56918de` and
`3ce612cb2c71ebccc8ebd100bb4603923e15b2b8`. These historical files were not
changed to hide the baseline failure. Separately, all 31 selected structural
and interactive grand-campaign cases passed in 3.05 seconds, peak RSS
106,905,600 bytes, without replaying historical proof bundles.

Browser connection discovery returned no available browser. Executable graph
and navigation tests can therefore provide runtime evidence, but no visual
browser inspection will be claimed without an actual connection.

## Unchanged milestones

Alpha remains v30 with 3,222 checked-use entries; Stable remains 432. The
earlier finite signed Möbius inversion result G007 remains proved locally.
**Full G009 remains open against the original blueprint:**
[PLAN/14, G009](../../PLAN/14_constructive_number_theory_grand_campaign.md)
also requires `Multiplicative(f) and Multiplicative(g) -> Multiplicative(f*g)`.
That needs its own coprime-divisor reindexing proof. The atlas's condensed
finite-algebra statement is not used to drop this broader obligation.
Preservation of multiplicativity by inversion is a useful subsequent
corollary, not an extra claim made here. General prime-power fields G091 are
also outside this tranche.

The final independent scan confirms that the earlier 113-row audit and all
424 reader files remain byte-identical (378 HTML pages; 60,243,272 bytes):
audit SHA-256 `6c138b44b94c15a72416c312130bacb37a7ccce1d70e5261d5e497fc7ae18b51`;
reader manifest SHA-256
`9755ca72a5e0341e6f42aa8f05253009d36e0950678a917a400961201b36f921`.
All complete bundle pins, ordinary certificate counts, distinct focused test
totals and final local reader identities are recorded above. The starting
commit and branch are unchanged; no files were staged, committed or deployed.

## Rechecking the completed checkpoint

These commands independently recompute the actual proof checks before
comparing the saved output:

```sh
make check-constructive-dirichlet-inverse
PYTHONPATH=peano-lab/py:scripts PYTHONMALLOC=malloc \
  python3 scripts/build_constructive_dirichlet_inverse_explorer.py --check --test
```

The first command checks the standalone audit bytes; the second also runs the
live reader tests and compares the generated snapshot. Both run fresh proofs.
Neither grants admission, deploys files or accepts a saved success receipt as
authority. The one-time `--write-audit` build refuses to overwrite an existing
audit, including a symlink; it is not the command for ordinary rechecking.
