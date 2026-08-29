# Dirichlet convolution and Möbius inversion: 113 new results

Date: 2026-08-29. Starting commit:
`cef66ddf52658ee9f878b9a81ff8eca19f991485`.
This is local mathematical implementation following
[PLAN/18](../../PLAN/18_dirichlet_convolution_and_mobius_inversion.md),
not an Alpha/Stable promotion, commit, push or deployment.

**Integration status: complete.** The corrected combined run passed all 21
fresh proof jobs, all 85 same-live-snapshot explorer tests, and the final
source/integrity checks before exclusively writing its audit. It generated
424 canonical local files. Full finite signed Möbius inversion, including
the reverse implication, is now proved locally as G007. The earlier failed
controller attempt and the unchanged resource boundaries are recorded below.

## Mathematical outcome

Seven modules provide 113 new statements with 354 direct prerequisites and
5,595 tactic commands:

| Chapter | New statements | Direct prerequisites | Tactic commands |
| --- | ---: | ---: | ---: |
| Signed finite support | 8 | 25 | 312 |
| Convolution construction and commutativity | 40 | 102 | 1,754 |
| Constructed grids, finite Fubini and associativity | 32 | 117 | 1,962 |
| Constant-one, delta and divisor-transform identities | 25 | 82 | 1,109 |
| Forward and reverse Möbius inversion | 8 | 28 | 458 |
| Total | 113 | 354 | 5,595 |

The main result is a whole-positive-prefix equivalence for actual finite
signed arithmetic tables:

```text
(∀n. 0<n≤N → G(n)=Σ[d|n] F(d))
  ↔
(∀n. 0<n≤N → F(n)=Σ[d|n] μ(d)*G(n/d)).
```

This notation summarizes genuine first-order graphs and constructed finite
folds. It is not an added summation, quotient or function oracle. In particular,
the hypothesis is required at **every positive input**, not only at one final
target. The precise constructed-output statement is:

```text
∀N F G. ArithTable(N,F) → ArithTable(N,G) → DivisorTransform(N,F,G) →
  ∃M H. MobiusTable(N,M) ∧
        (DirichletTable(N,M,G,H) ∧ ArithPositiveEqual(H,F,N)).
```

`M` uses the already proved, independently defined Möbius values. `H` is an
actual table of actual weighted convolution folds. The fixed-Möbius-table
theorem proves `DirichletTable(N,M,G,F)`; the final theorem proves both
implications between that graph and the divisor transform.

Values at zero in `F`, `G` and `H` are arbitrary. At `N=0`, actual table
witnesses still exist; only the positive-value condition is vacuous. Table
uniqueness means equality of represented positive values, never equality of
arbitrary codes. Signed one is code 2, whereas code 1 represents minus one.

The constructive route is:

1. Construct actual convolution summands, their tables and their signed folds.
   Complementary-divisor reindexing proves commutativity and zero-tail lemmas
   prove padding invariance.
2. Construct a real first/last-factor grid. Identify its rows and columns with
   actual quotient-indexed convolutions and apply proved finite Fubini. This
   supplies associativity without assuming a rearrangement law or a grid.
3. Construct constant-one and delta tables. Prove the identity law and the
   identification of convolution with one and the existing divisor-sum graph.
4. Use prior Möbius cancellation to prove `M*U=E`. From the whole transform
   `U*F=G`, associativity gives `M*G=(M*U)*F=F`. The reverse implication uses
   `U*(M*G)=(U*M)*G=G`. Every weighted fold is constructed before its value is
   identified; choosing the final output `H=F` does not assume the identity.

Exact contracts and the original conditional-body evidence remain in the
unchanged authoring RFCs:

- [Signed finite support](signed-finite-support-rfc-v1.md).
- [Convolution construction](dirichlet-convolution-rfc-v1.md) and
  [complementary-divisor commutativity](dirichlet-commutativity-rfc-v1.md).
- [Constructed grids and associativity](dirichlet-fubini-associativity-rfc-v1.md).
- [One, delta and divisor transforms](dirichlet-units-rfc-v1.md).
- [Full finite signed inversion](mobius-inversion-rfc-v1.md).

## Complete proof data and inherited support

All five complete bundles passed the unchanged original HA checker and the
unchanged independently compiled Lean verifier, both individually and in the
final fresh combined run. The independent
adapter authenticates the actual checker and gives it a private exclusive
snapshot of exactly the same bytes checked by HA.

The immutable basis contains 3,222 Alpha statements and three separate research
generations of 170, 126 and 125 statements. The first two research generations
are published; the previous 125 are local. Inherited bodies are included and
checked, not assumed, recounted as new theorems or relabeled as Alpha members.

| Bundle | New owned | Prior 170 | Prior 126 | Prior local 125 | New cross-track | Alpha | Nodes incl. packaging | Edges incl. packaging |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Finite support | 8 | 11 | 1 | 0 | 0 | 149 | 170 | 397 |
| Convolution | 40 | 20 | 7 | 8 | 2 | 192 | 270 | 712 |
| Fubini/associativity | 32 | 24 | 19 | 30 | 31 | 210 | 347 | 971 |
| One/delta | 25 | 21 | 8 | 8 | 22 | 197 | 282 | 760 |
| Möbius inversion | 8 | 45 | 41 | 56 | 78 | 302 | 531 | 1,579 |

The counts are per dependency cone, not disjoint inventories to add together.
The packaging root is not a new mathematical theorem.

Exact artifacts:

- [Finite support](artifacts/dirichlet-finite-support-proof-bundle-v1.json):
  587,407 bytes; 8,697 body-proof occurrences; SHA-256
  `99d889c64fb066f79247afa4310e0143f42bfffbc2cf56e4bd9be3735e0cac47`.
- [Convolution](artifacts/dirichlet-convolution-proof-bundle-v1.json):
  2,756,953 bytes; 18,180 body-proof occurrences; SHA-256
  `313316e788a10dc281dfb0541a447bad9b7b26bbbd68b1030db89d8d28c5a38b`.
- [Fubini/associativity](artifacts/dirichlet-fubini-proof-bundle-v1.json):
  4,455,766 bytes; 25,115 body-proof occurrences; SHA-256
  `05cb102ae5fb423e325223589eb17b8f1dd0aa8d3cb8419425142f9be087d9f3`.
- [One/delta](artifacts/dirichlet-units-proof-bundle-v1.json):
  2,158,014 bytes; 18,734 body-proof occurrences; SHA-256
  `232ddd461eb83d97c1a6255a872be7e970b635ce1d4e958c8bed7706419687b7`.
- [Möbius inversion](artifacts/mobius-inversion-proof-bundle-v1.json):
  6,488,786 bytes; 40,028 body-proof occurrences; SHA-256
  `22e7e61d5d4567df695d67830b465664fbe5a070f0367196e5cfd542ccba5b75`.

The unchanged independent Lean executable is 106,787,344 bytes, SHA-256
`22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033`.
It was not rebuilt. No Lean compiler version is inferred from current sources.

## Fresh audit and ordinary certificates

The completed [machine-readable audit](artifacts/dirichlet-checkpoints-v1.json)
is 38,584 bytes, SHA-256
`6c138b44b94c15a72416c312130bacb37a7ccce1d70e5261d5e497fc7ae18b51`.
It is byte-identical to the explorer's `proof-audit.json`. No saved success
report was consumed as proof authority.

All fifteen principal roots passed actual ordinary empty-context replay.
These are certificate proof-occurrence counts, not packaging-root counts or
numbers of new theorems:

| Tag | Exact principal theorem | Certificate occurrences |
| --- | --- | ---: |
| ZS0004 | `signed_prefix_sum_zero_tail` | 5,755 |
| ZS0007 | `signed_prefix_sum_last_value` | 12,421 |
| ZS0008 | `signed_prefix_sum_zero_padding_iff` | 11,846 |
| DC001D | `dirichlet_convolution_table_exists_extensionally_unique` | 14,437 |
| DC0024 | `dirichlet_convolution_table_commutative` | 21,266 |
| DC0028 | `dirichlet_convolution_padded_prefix_iff` | 15,043 |
| DF001D | `dirichlet_convolution_fubini_interchange` | 27,262 |
| DF001E | `dirichlet_convolution_associative` | 34,386 |
| DF0020 | `dirichlet_convolution_associative_tables_exists` | 35,039 |
| DU0013 | `dirichlet_delta_unit_exists` | 25,065 |
| DU0018 | `dirichlet_constant_one_sum_iff` | 3,389 |
| DU0019 | `dirichlet_constant_one_realizes_divisor_sum` | 12,003 |
| MI0005 | `mobius_inversion_for_actual_mobius_table` | 55,381 |
| MI0006 | `mobius_inversion_arithmetic_tables` | 56,221 |
| MI0008 | `mobius_inversion_iff` | 55,727 |

The production audit schedules one exact-AST novelty comparison against all
3,643 earlier statements, five complete HA/same-byte Lean checks, and fifteen
separate ordinary-root checks. Every ordinary worker rechecks its complete
source-bound bundle, obtains an empty-context certificate, compares the
returned specification and formula with the exact requested theorem, and
checks that certificate again with the original kernel.

All 21 jobs retain 170/175 CPU seconds, 180 wall seconds and 1,536 MiB observed
RSS. Parent cleanup is bounded at 185 seconds per child. The derived
4,065-second controller deadline schedules those separate jobs; it is not a
larger proof window. The controller retains the same CPU and RSS ceilings.
A three-principal Fubini aggregate exceeded one original CPU window, whereas
the individual certificates fit. No larger proof, formula, object or replay
limit was introduced to accommodate it.

The first integrated attempt completed all 21 actual proof jobs, with maximum
proof-worker RSS 780,009,472 bytes, then the combined controller hit its CPU
ceiling while repeating display-only metadata computations. It saved neither
a final audit nor an explorer snapshot. The revised audit retains the
source-selected support plans and immutable expected metadata while checking,
and releases them to rendering only after all proof gates pass. These objects
contain syntax, not checked proof certificates.
A separate forked render/test process inherits that live run's report and
plans. It accepts no receipt-file input or standalone render CLI and retains
170/175 CPU seconds, 180 wall seconds and 1,536 MiB RSS. The parent's scheduling
deadline adds its 185-second render/cleanup window, giving 4,250 seconds; its
CPU/RSS limits do not change. Clean child exit, nonce and source bindings,
exact snapshot hashes and the requested UI tests precede the parent-only,
exclusive final audit write.

The corrected combined run exited successfully after **1,698.658 seconds**,
including all 21 proof jobs and the separately bounded render/test phase.
The 85 explorer tests took 84.65 seconds within that phase. Observed peak RSS
was 777,666,560 bytes for proof workers, 692,912,128 for the pure-render child,
and 752,615,424 for the controller. These are separate processes and windows;
the total elapsed time is not the duration or allowance of any single proof.

Before that fresh run, a bounded profile of the parent's actual metadata and
source-binding work took 150.431 CPU seconds with peak RSS 728,678,400 bytes.
A separate profile of the child's actual table/routes, all five pinned bundle
decodes, all 113 statement and 5,595 command compactions, and nine complete
source-binding calls took 103.951 CPU seconds with peak RSS 732,348,416 bytes.
These profiles exercised real syntax and literal artifacts, but did not
invent accepting reports or render successful-proof labels. They are resource
diagnostics, not additional mathematical verification receipts.

Fresh bounded messages bind random nonces, exact sources, specifications,
inventory, parent catalog, bundle bytes and the actual checker. Source changes
between the start and end fail closed. Progress messages are controller-only
diagnostics, never worker reports or evidence. `--write` is exclusive;
`--check` performs fresh verification before comparing the saved bytes.

Authoring can reuse an actual HA-checked prefix as a seed for a later bounded
construction window. Such prefixes remain proof data, not complete campaign
receipts. Every reused seed body, including unused seed nodes, is genuinely
checked. Final registry matching rejects a prefix presented as a full family.
The mandatory whole-tranche novelty and Lean gates are separate from authoring.

## Conservative definitions and proof maps

Thirteen conservative definitions, ND0300–ND0312, preserve all 356 previous
definition identities and records. The complete registry now has **369
definitions, 784 actual expansion edges, and maximum zero-based layer 12**.
The new definitions cover signed zero windows; convolution entries, prefixes,
sums and tables; actual factor grids and flattened folds; one and delta tables;
and the whole-positive-prefix divisor transform.

Definition expansion, theorem use of a definition, and theorem prerequisites
remain three distinct edge kinds. Critical proof paths follow only theorem
prerequisites. A flattened prefix used to construct a grid is not falsely
shown as part of the grid's defining formula.

All 113 statements and the local propositions in all 5,595 tactic commands
have passed exact-AST compaction preflight: 7.24 seconds and 68,239,360 peak
resident bytes. This includes free-variable contexts and binders, not just
matching pretty-printed strings. The check is presentation evidence, not a
substitute for the proof checks above.

The renderer uses the unchanged original Quadratic Reciprocity renderer and
all five canonical assets. Five local branches use stable ZS/DC/DF/DU/MI tags,
exact and defined readers, mixed dependency graphs, individual definition
pages, source downloads and complete proof bundles. The shared dispatch
connects small chapters with the larger campaign and all three earlier
research generations without rewriting their published or local snapshots.

The completed [local proof map](../../book/_static/constructive-dirichlet-explorer/index.html)
contains **424 files, 378 HTML pages and 60,243,272 bytes**, including its
72,102-byte manifest. All literal files match that manifest. Each branch
includes just its required conservative definition closure:

| Branch | New theorems | Displayed definitions | Actual expansion edges |
| --- | ---: | ---: | ---: |
| [Finite support](../../book/_static/constructive-dirichlet-explorer/finite-support/index.html) | 8 | 12 | 17 |
| [Convolution](../../book/_static/constructive-dirichlet-explorer/dirichlet-convolution/index.html) | 40 | 26 | 50 |
| [Fubini and associativity](../../book/_static/constructive-dirichlet-explorer/dirichlet-fubini/index.html) | 32 | 29 | 65 |
| [One and delta](../../book/_static/constructive-dirichlet-explorer/dirichlet-units/index.html) | 25 | 23 | 45 |
| [Möbius inversion](../../book/_static/constructive-dirichlet-explorer/mobius-inversion/index.html) | 8 | 35 | 68 |

The definition closures overlap; they are not additional new definitions.
Seven mathematical source modules and all six unchanged authoring RFCs are
included, along with the five complete proof bundles.

Final snapshot pins:

- Manifest SHA-256:
  `9755ca72a5e0341e6f42aa8f05253009d36e0950678a917a400961201b36f921`.
- `checkpoints.json`: 38,667 bytes; SHA-256
  `0f4be803ba179c90b3f80a281bb3c1143d187317736514cb443b036bb35175c2`.
- Logical checkpoint digest:
  `c649bb3bab89d30db671ac698578290ba813297f98d3a508ce7fa60e888ee593`.
- Render/source binding:
  `529d5731e0dde836eee71dfb1c759b37a78c4bbe280946e68ff361e564c2721a`.

Actual canonical JavaScript passed the hostile getter-only SVG-`href` tests,
all three filters, fragment highlighting, all 118 exact-reader/index graph
navigation checks, the two campaign-scale dispatches, and parsing of all 17
inline scripts. Every generated HTML link and fragment was checked, including
routes into all three inherited research generations and the unchanged atlas.
No browser connection was available: these executable runtime checks are not
visual-browser inspection.

## Focused regressions

Completed distinct tests (reruns are not counted again):

| Group | Passed |
| --- | ---: |
| Signed finite support | 113 |
| Convolution construction and commutativity | 486 |
| Constructed grids, finite Fubini and associativity | 472 |
| Constant-one and delta identities | 400 |
| Independent Möbius-inversion contracts and proofs | 143 |
| Exact support selection and conservative definition DAGs | 174 |
| Complete checkpoints, exact ordinary roots and hostile proof data | 236 |
| Fresh bounded audit protocol, syntax retention and actual isolated workers | 155 |
| Authoring exporter, actual seeds and corrupt-seed rejection | 31 |
| Separately bounded render transport, literal outputs and fail-closed cleanup | 102 |
| Same-live-snapshot canonical explorers, exact definitions and JavaScript | 85 |
| Unchanged kernel, syntax, cut, formula DAG, bundle, replay and browser shell | 167 |
| Unchanged defined syntax, formula compaction and double-and-add numerals | 214 |
| Total distinct focused tests | 2,778 |

All groups passed. The 19 pure explorer cases and other repeated diagnostic
runs are included in their respective groups, not counted again.

The mathematical tests independently expand the target statements, check the
actual original bodies, reject false conclusions, and drop and poison every
declared prerequisite. Independently constructed beta-coded examples cover
negative values, empty prefixes, arbitrary zeroth values, noncanonical table
representatives, endpoint contributions and the invalid final-input-only
transform hypothesis. Examples are diagnostics, never proof authority.

All 236 checkpoint tests passed in 28 separate bounded windows. They include
actual HA and same-byte compiled Lean positives for all five families, all
fifteen ordinary principals, and fifty actual corrupted-bundle rejections.
Wrong returned specifications/formulas and genuinely valid conditional bodies
presented as complete theorems are rejected. The largest successful window
took 141.878 seconds; maximum observed checkpoint-test RSS was 780,615,680
bytes. Oversized initial groupings hit the unchanged CPU ceiling and were
replaced by disjoint bounded windows, not skipped cases or enlarged limits.

The 155 audit tests include actual fresh family and separate ordinary-root
workers, exact nonce/source/specification protocol binding, process cleanup,
oversized and malformed output, and preservation of existing receipts on
failure. A single test grouping four separate proof workers exceeded its
outer 180-second scheduling window; four isolated live tests then passed in
63.34, 64.73, 65.58 and 65.18 seconds on the revised collector implementation.
No individual proof limit changed. The final 151 non-live protocol cases
passed in 62.46 seconds; they cover failure at each of the 21 jobs, source
binding, aggregation, RSS and callback failure boundaries. Largest observed
RSS in the final four live windows was 432,996,352 bytes; the non-live window
used 425,279,488 bytes.

The 102 render-process tests passed in 4.85 seconds with peak RSS 82,968,576
bytes. They exercise real forked failure and timeout paths, bounded malformed
messages, nonce/source/mode mismatches, literal manifest and file hashes,
symlink rejection, and parent-only final-write ordering. Synthetic transport
fixtures explicitly have `proofs_verified=False`; they do not simulate a
successful mathematical audit. A denied process-group cleanup signal is an
explicit failure with bounded reaping of the owned child, not a reason to
retry with wider authority. The proof-positive final-write path then passed
in the actual integrated run with all 85 explorer tests.

The 167 core/browser-shell controls passed in 2.05 seconds with peak RSS
133,070,848 bytes. The additional 214 notation/numeral regressions passed in
17.93 seconds with peak RSS 1,132,969,984 bytes, below the unchanged 1,536 MiB
ceiling. These are focused local regressions, not a repository-wide or remote
green-CI claim.

## Integration and reproduction

For an initial build with no existing final audit, the single combined command
performs the fresh audit, builds the pages, runs the explorer tests against
that same live in-memory snapshot, and only then
exclusively writes its audit output:

```sh
PYTHONPATH=peano-lab/py:scripts PYTHONMALLOC=malloc \
  python3 scripts/build_constructive_dirichlet_explorer.py --test --write-audit
```

Once the audit and snapshot exist, use the deterministic follow-up checks
rather than trying to overwrite the exclusive audit output:

```sh
make -j1 check-constructive-dirichlet
make -j1 book-constructive-dirichlet-explorer
```

These targets are deliberately not dependencies of `stage-proofs`. This
change adds no publication or Alpha-admission recipe for the local batch.

The local browser worker loads 504 Python source files. Its 526-entry manifest
contains 505 Python records (including the unchanged CI-only `py/ci_shard.py`),
20 unchanged proof artifacts and the worker itself. The application identity
is `a-95b336b35c9e`, build `2026-08-29b`. The manifest SHA-256 is
`95b336b35c9e224e650b8d335d3923b90ee004a62c3fdc0b127e483ca9ff2cf4`.
Worker inventory, content manifest, `APP_ROOT` and `PEANOAPPID` checks pass.
Both new CLI help commands also run without a preset `PYTHONPATH`. The only
tracked changes are the two local Make targets and application identity,
worker source inventory, content manifest and shell build identity. The
worker outside its source list and the shell outside its two identity fields
are byte-identical to the starting commit. No application release was uploaded.

## Scope and next work

The exact finite signed inversion statement **G007 is now proved locally**,
with actual constructed witnesses and the stronger forward/reverse
equivalence. Its completion label follows the successful fresh HA, compiled
Lean and ordinary-certificate checks, not a count or an RFC title. This does
not change the published campaign atlas or grant Alpha/Stable admission.

G009 remains open: arbitrary convolution inverses require the exact signed
unit-at-one criterion `f(1)=+1 or f(1)=-1` for `N>0`; the broader arithmetic
function campaign also requests multiplicative-function closure. General
prime-power fields G091 still require evaluation/product compatibility,
polynomial division and gcd, irreducible construction and extension fields.
A separate worked arithmetic-function corollary, such as totient recovery,
is also useful follow-up beyond the generic inversion theorem.

For G009, the next concrete proof sequence is:

1. Classify actual signed factors of one and construct a solver for
   `r+x*u=e` when `u` is signed one or minus one. Specialize actual convolution
   at `n=1` to prove the necessary unit-at-one condition.
2. Construct the inverse in the orientation `G*F=delta`, isolating the **last**
   divisor `d=n`. Only that term uses the new `G(n)` and its coefficient is
   `F(1)`; earlier terms use already constructed `G(d)`, with `d<n`.
   Prove the missing input-append/prefix-preservation lemma, then use
   `arithmetic_signed_table_append`, `dirichlet_convolution_prefix_append`
   and `arithmetic_signed_sum_append_transport`. Existing output-table
   append alone does not construct an inverse input. The old
   `proper_factor_lt` already provides strict quotient bounds where needed.
   At `n=S k`, the existing constructor can build
   `DirichletPrefix(G,F,n,k,M)` from zero-domain table guards obtained by
   `signed_table_domain_resize`. A fold of length `n` then sums only `d<n`.
   The new transport lemma must preserve this restricted prefix after
   appending `G(n)`; existing full-prefix extensionality asks for equality at
   that newly changed index and cannot be used directly. Keep `n≤N` explicit
   for the actual quotient lookups in `F`. A full inclusive prefix through
   `n` would wrongly include the old arbitrary value of `G(n)` in the remainder.
3. Use commutativity for the other inverse identity, and associativity plus
   delta units for positive-value uniqueness and prefix compatibility.
   Handle `N=0` separately: actual zero-window tables have inverses without
   any condition at one, while the zeroth output value remains arbitrary.
4. Prove general multiplicative-function closure separately, using an actual
   coprime-divisor bijection and finite Fubini. A specific totient law or the
   inverse criterion alone does not close that part of G009.

This is a future proof plan, not a claimed inverse construction. Its new
statements must be compared against all 3,756 prior statements, including
the present 113, rather than the earlier 3,643-row novelty basis.

Alpha remains v30 with 3,222 checked-use entries and catalog SHA-256
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
Stable remains 432. All previous mathematical sources, proof/kernel/replay
implementations, catalogs, proof snapshots, renderer assets and unrelated
worktrees are preserved. No service, production cache header, running worker,
proof limit, repository history or remote state was changed.

An independent read-only scope audit recomputed all 526 application manifest
records and all 395 literal files in the previous local explorer. Its unchanged
manifest SHA-256 is
`98d78a16815e40281ebf9ef0f4b8b9d183109e5c25960576189e3f5d0c0735a3`;
the previous 125-theorem audit remains
`c665db9d1edb12670c1719c00c645eb5eec388e381fb87d9cf4723cbc99314ee`.
The six kernel modules, thirteen engine modules, four shared renderers, all
five canonical assets and twenty prior browser proof artifacts are unchanged.
