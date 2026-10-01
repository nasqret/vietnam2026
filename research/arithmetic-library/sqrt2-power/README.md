# Irrationality-first campaign: checked research checkpoint

Active target: positive HA irrationality of `(sqrt2)^(sqrt2)` (IR072 / G121).
Next: full positive transcendence (TR006 / G122). No campaign **parent** theorem
has been proved and no proposed definition has been admitted. Publication is
separate from library admission; see the release status below. The original
eight-leaf pilot is preserved below as a historical
baseline. The shared-proof execution wave adds exact HA and independent Lean
checks; it does not complete the irrationality theorem.

- [Mathematical dossier and execution policy](../../../PLAN/32_sqrt2_power_irrationality_campaign.md)
- [Local campaign landing page](../../../book/_static/constructive-sqrt2-power-campaign/index.html)
- [Lemma/definition planning DAG](../../../book/_static/constructive-sqrt2-power-campaign/map.html)
- [Twelve bounded pilot contracts](../../../book/_static/constructive-sqrt2-power-campaign/pilot.html)
- [Actual pilot results and downloadable certificates](../../../book/_static/constructive-sqrt2-power-campaign/pilot-results.html)
- [Current shared-proof wave and its exact evidence](../../../book/_static/constructive-sqrt2-power-campaign/wave-results.html)
- [Local rational definition DAG](../../../book/_static/constructive-sqrt2-power-campaign/local-definitions.html)
- [Checked arithmetic DAG and open planning parents](../../../book/_static/constructive-sqrt2-power-campaign/arithmetic-frontier.html)
- [Additive combined campaign atlas](../../../book/_static/constructive-sqrt2-power-campaign/grand-campaign/index.html)
- [Machine-readable plan](../../../book/_static/constructive-sqrt2-power-campaign/api/plan.json)

The inventory contains 81 irrationality work packages, 26 proposed definitions,
9 engineering/contingency gates and 6 future transcendence packages. Every
parent contract remains explicitly unproved; the bounded pilot's exact formulas
and checked premises are recorded separately. The existing 120-goal atlas, Alpha, Stable and historical
proof pages remain unchanged.

## Research publication, 2026-10-01

The owner requested an update of the repositories and website. This checkpoint
publishes the planning DAG, conservative local definitions and exact supporting
evidence without promoting the unfinished campaign to Alpha. Alpha v35 stays
at **4,318 checked-use entries**; Stable stays at **432**. In particular,
neither a recorded check nor this website is a checked-use admission token.

The additive release is prepared by `scripts/stage_sqrt2_power_research.py`.
It authenticates the complete sealed v35 delivery inventory and the exact
campaign snapshot, preserves all existing theorem pages and shared assets,
and changes only the proof-library and grand-campaign navigation entrances.
The new campaign is served at `/proofs/sqrt2-power/`; its own combined atlas
adds two **open** goals to the frozen 120-goal parent. The current grand atlas
keeps its original data and links to this 122-goal research extension.

Publication status: **prepared locally; remote verification pending**.
Deployment observations will be recorded here after the public bytes are
verified. This section supersedes the historical local-only status below.

Release preflight: [72 publication/DAG/evidence test executions](observations/research-publication-regressions-v4.json)
and [145 supervisor tests](observations/research-runtime-controller-validation-v1.json)
passed. The [bounded stage audit](observations/research-publication-stage-v1.json)
authenticated all 13,798 registered parent files and produced a 267-file
additive payload, preserving 13,796 parent files exactly. Its
[delivery manifest](observations/research-publication-manifest-v1.json) is
metadata only, never proof authority.

QN001 and QF001 were regenerated and freshly HA-checked again, producing the
exact same certificate hashes as the frozen checkpoint. The
[independent Lean checker was freshly compiled and accepted both exact bundles](observations/research-publication-fresh-lean-v1/report.json),
including successful false-target and forged-body rejection controls.
This does not increase the 33-statement count or enter ordinary checked use.

Three stopped preflight records are retained: a new absent-marker test fixture
accidentally contained its marker ([v1](observations/research-publication-regressions-v1.json));
legacy smoke workers requested the production 30-second default inside a
25-second test guard ([v2](observations/research-publication-regressions-v2.json));
and the proof-leaf harness correctly rejected the supervisor suite's intentional
process-accounting child ([v3](observations/research-publication-regressions-v3.json)).
The fixture was corrected, smoke reservations reduced, and supervisor tests
run as a separately bounded controller. All original assertions and proof-worker
restrictions remain intact; no proof, resource ceiling or kernel rule was relaxed.
An initial sandbox invocation could not run `/bin/ps`; explicit permission for
process accounting was obtained rather than disabling the memory guard.

## Quadratic product extension, 2026-10-01

The wave now has **33 distinct exact HA/Lean-checked supporting statements**.
The full positive irrationality theorem IR072 remains open.

| Lemma | Exact scope | Bundle nodes / ordinary proof nodes |
| --- | --- | --- |
| QN001 | Two nonzero signed quadratic integers have a nonzero product, with arbitrary input and output representatives. | 221 / 81,273 |
| QF001 | A supplied finite β-table product trace beginning at one has a nonzero terminal value when every decoded factor is nonzero. | 224 / 81,603 |

QN001 reuses complete SN001/SN003/SI001 proof bodies with lossless sharing;
59 duplicate rows are shared, and the parent generators are not rerun. QF001
adds actual HA induction and exact β-decoding uniqueness. Neither a source
hash, solver answer nor previous receipt is a mathematical premise. The work
uses agent-designed decomposition and deterministic ordinary proof assembly
and checking, not a claim of solver-discovered universal induction.

Both passed their first generation and fresh HA replay in a combined 11.17
seconds. Fresh compilation of the nine-module independent Lean checker and
same-byte checks, including false-target/forged-body rejections, took 14.51
seconds. Timings exclude planning, implementation and regression testing.
The largest proof process peaked at 441,991,168 bytes; no limits were raised.

- [QN001 ordinary HA observation](observations/shared-wave-quadratic-nonzero-v1/report.json)
- [QF001 ordinary HA observation](observations/shared-wave-quadratic-product-trace-v1/report.json)
- [Fresh independent Lean checks](observations/fresh-lean-quadratic-products-v1/report.json)
- [Exact v5 evidence index](observations/shared-wave-index-v5.json)
- [Finite trace definition DAG](../../../book/_static/constructive-sqrt2-power-campaign/quadratic-trace-definitions.html)

Four conservative local definitions ND0390–ND0393 separate actual execution
from the nonzero-factor assumption. The constructive-proof-explorer template
keeps the established Quadratic Reciprocity presentation, exact named statements,
and separately typed proof/definition/planning edges. The new actual proof
dependencies are SN001/SN003/SI001 → QN001 → QF001. All historical evidence
is retained: 42 attempts, eleven fresh-Lean reports and eight earlier failures.

Validation finished with **134 passing test executions**: [QN001](observations/shared-wave-quadratic-nonzero-validation-v1.json)
(20), [QF001](observations/shared-wave-quadratic-trace-validation-v2.json) (18),
[controller/evidence/Lean-intake guards](observations/shared-wave-quadratic-controller-validation-v1.json)
(46), and [presentation, DAG and site regressions](observations/shared-wave-quadratic-products-presentation-v2.json)
(50). The largest successful test process used 522,141,696 bytes, below the
unchanged 512 MiB ceiling. All [264 generated files match an independent
bounded rebuild](observations/shared-wave-quadratic-products-site-build-v1.json),
and all [23 browser routes passed](observations/shared-wave-quadratic-products-browser-v1.json)
in 25.54 seconds. New theorem/definition pages and the checked arithmetic map
were visually inspected with disposable browser profiles.

Two stopped regression attempts remain archived: an [expanded archive-case
batch reached its 25-second CPU guard](observations/shared-wave-quadratic-products-presentation-v1.json),
and an [ancestor-preservation test reached its 512 MiB RSS guard](observations/shared-wave-quadratic-trace-validation-v1.json)
while retaining two expanded archive copies. Isolating archive parameters and
retaining exact compact row bytes before proof reconstruction repaired the
test scheduling/storage. No assertion, resource ceiling, producer or kernel
rule was weakened; neither stop was a failed universal proof.

**Next:** construct finite product traces for arbitrary factor tables using
actual β-prefix extension, then extract a terminal witness and combine with
QF001. Trace totality is not a premise smuggled into a definition and is not
yet proved. Rational interpretation, conjugate-height bounds, moment-polynomial
identities and the analytic bridges remain open. This extension does not close
IR046 or IR072. All changes are local; no commit, promotion, push or deployment.

## Rational norm extension, 2026-09-30 (historical checkpoint)

Three new universal supporting lemmas passed fresh ordinary HA replay and the
independently freshly compiled Lean checker. That checkpoint contained **31
distinct checked statements**, not a completed irrationality proof.

| Lemma | Exact scope | Bundle nodes / ordinary proof nodes |
| --- | --- | --- |
| RN001 | Equal rational quadratic coordinates give equal rational norms, with arbitrary signed representatives and nonzero denominators. | 29 / 2,630 |
| RN002 | The norm of a quadratic product satisfies the existing rational multiplication relation, with output denominator `(u*v)*(u*v)`. | 46 / 42,483 |
| SI001 | Nonzero signed integers have a nonzero binary product, including arbitrary output representatives. | 34 / 2,400 |

RN001 reuses actual signed-square scaling, representative transport and
uniqueness bodies. RN002 includes the complete SN003 certificate and explicit
semiring-law transport; it does not silently replace the squared denominator
by `u*v`. SI001 uses actual square-existence and natural no-zero-divisor proofs.
All new proof construction is deterministic ordinary-inference composition;
agent work planned the decomposition and implementation. No new definition,
kernel change, solver axiom or global-registry mutation was introduced.

Z3 independently returned `unsat` for each exact negated conjecture. These logs
are cross-checks, not trusted HA proof imports. Generation, solver checks and
fresh HA replay took 11.17 seconds in total across three sequential bounded
observations; the fresh nine-module Lean compilation/check wave took 12.13
seconds. These timings exclude agent planning, engineering and regression tests.
The largest proof producer peaked at 508,788,736 bytes, below the unchanged
768 MiB proof ceiling. No resource cap was raised.

- [RN001 exact HA/Z3 observation](observations/shared-wave-rational-norm-transport-v1/report.json)
- [RN002 exact HA/Z3 observation](observations/shared-wave-rational-norm-product-v1/report.json)
- [SI001 exact HA/Z3 observation](observations/shared-wave-signed-product-nonzero-v1/report.json)
- [Independent Lean wave, including rejection controls](observations/fresh-lean-rational-norm-wave-v1/report.json)
- [RN001 hostile-input tests](observations/shared-wave-rational-norm-transport-validation-v1.json)
- [RN002 hostile-input tests](observations/shared-wave-rational-norm-product-validation-v1.json)
- [SI001 hostile-input tests](observations/shared-wave-signed-product-nonzero-validation-v1.json)

The [v4 evidence index](observations/shared-wave-index-v4.json) pins 40 attempts
and ten fresh-Lean reports; all eight historical failed attempts are retained.
The established Quadratic Reciprocity presentation and conservative definition
DAG are preserved. The checked DAG adds the actual SN003 → RN002 dependency;
links to IR031/IR046 remain explicitly planned support, not parent closure.

Final validation records **133 passing test executions**: the three proof suites
linked above (40), [exact presentation/controller regressions](observations/shared-wave-rational-norm-presentation-v3.json)
(28), and [site/evidence-reader/Lean-intake regressions](observations/shared-wave-rational-norm-site-regressions-v2.json)
(65). These are test executions, not additional theorem counts. All **255
generated local files** match the [separate bounded build and byte check](observations/shared-wave-rational-norm-site-build-v2.json).
All [20 browser routes passed](observations/shared-wave-rational-norm-browser-v1.json)
in 22.18 seconds; the new rational theorem pages and full checked DAG were
visually inspected using disposable profiles.

The first expanded presentation batch hit its [25-second CPU guard](observations/shared-wave-rational-norm-presentation-v1.json),
and the in-process double-build test hit its [512 MiB RSS guard](observations/shared-wave-rational-norm-site-regressions-v1.json).
Both stopped records remain intact. Smaller presentation batches and one fresh
regeneration compared byte-for-byte against the separately built disk snapshot
passed without raising any ceiling. The largest successful test process peaked
at 522,616,832 bytes. An [initial site build](observations/shared-wave-rational-norm-site-build-v1.json)
also rejected the new definition users until its explicit allowlist and hostile
regression tests were extended; this was a presentation integration issue,
not a failed mathematical proof. No worker was left running.

**IR072 remains open.** Next: lift SI001 through SN001/SN003 to quadratic binary
nonvanishing and then actual finite-product traces; prove conjugate-height
bounds and combine them with integer norm separation for the rational lower
bound; continue coefficientwise rational-series and analytic remainder bridges.
No commit, Alpha promotion, push, or deployment occurred in this extension.

## Universal arithmetic extension, 2026-09-19 (historical checkpoint)

Four more universal statements now pass **fresh ordinary HA and independently
compiled Lean**, bringing the wave to **28 distinct checked statements**:

- NG001: a constructive positive gap between unequal naturals (3 bundle
  nodes / 192 ordinary proof nodes). Z3 independently confirmed the same target.
- SN002: witnessed integer norm separation for arbitrary nonzero signed
  coefficient pairs (210 / 40,625).
- SN003: norm multiplicativity in Z[√2], with arbitrary signed output
  representatives and all eight premises explicit (37 / 41,346).
- CV001: universal vanishing of an actually executed natural antidiagonal
  convolution below the sum of the input vanishing orders (28 / 1,400).

The [quadratic arithmetic review](quadratic-arithmetic-review.md) records the
first three exact decompositions. Two local aliases, ND0388/ND0389, abbreviate
separate quadratic-product component equations; they do not hide a norm law.
CV001 reuses eight existing definition identities and argument orders.
Its [proof and annotation-repair review](convolution-review.md) records the
exact universal statement and the remaining coefficient-order bridge.
The small [checked DAG](../../../book/_static/constructive-sqrt2-power-campaign/arithmetic-frontier.html)
extracts solid edges from actual root dependencies. Dashed planning support
does not close a parent. Named theorem pages and larger parent pages link in
both directions, using the established Quadratic Reciprocity presentation.

CV001's first two failed attempts remain visible. A
[versioned diagnostic](observations/shared-wave-convolution-diagnostic-v1.json)
observed the unchanged checker rejecting an elimination-headed equality after
local-cut compilation had erased its synthesis annotation. The corrected
producer preserves the eleven actual local lemmas with ordinary typed identity
Cuts; every lemma body is still checked, and no kernel or global engine source
was changed. The [same original target then passed HA](observations/shared-wave-convolution-vanishing-v3/report.json)
in 1.70 seconds (91 MB peak), and
[fresh Lean](observations/fresh-lean-convolution-vanishing-v1/report.json)
in 9.70 seconds. Failed-attempt records are not retroactively relabeled.

**IR072 remains open.** SN002 supplies the integer-discreteness component of
IR032, not its real-algebraic lower bound. SN003 does not yet supply the
rational-denominator version of IR031. CV001 is an arbitrary natural-index
convolution theorem, not ascending rational power-table execution, formal
exp/log composition, or an analytic remainder estimate. The next work is
denominator/conjugate-height transport and coefficientwise series execution.
All execution remains single-worker and capped; agent planning/engineering
cost is unmeasured, not zero. No commit, promotion, push or deployment occurred.

The extension's final bounded suites record **158 passing test executions**
(including rechecks of existing security tests, not 158 new theorems):
[separation](observations/shared-wave-norm-separation-validation-v1.json),
[norm product](observations/shared-wave-norm-product-validation-v1.json),
[convolution](observations/shared-wave-convolution-validation-v1.json),
[controller bindings](observations/shared-wave-arithmetic-presentation-v2.json),
[reader/Lean-intake regressions](observations/shared-wave-reader-lean-regressions-v3.json),
and [final exact-presentation/page/link/DAG/determinism regressions](observations/shared-wave-final-presentation-v3.json).
All **245 generated local files** match the
[final fresh bounded build and independent byte comparison](observations/shared-wave-final-site-build-v3.json).
The [final browser smoke](observations/shared-wave-final-browser-v3.json)
passed all **17 routes** in 27.97 seconds, including the checked-proof DAG and
the clickable eight-definition convolution DAG. The final convolution DAG
screenshot was visually inspected; disposable browser process groups were
cleaned up without touching the user's browser profile. Browser validation is
presentation evidence only, not proof authority.
The largest focused test process peaked at 532,414,464 bytes, below the
unchanged 512 MiB test ceiling; no resource limit was increased.

## Shared-proof wave, 2026-09-19

The per-operation proof DAG now proves the **original exact P10 statement**
within the unchanged arithmetic/size limits: 1,486 local nodes, 19,539 ordinary
proof-body nodes. Generation and fresh HA replay took 6.85 seconds, with a
306 MB measured peak. A freshly compiled nine-module Lean checker independently
accepted the same bytes. The earlier failed adapter and its failure records
remain unchanged; its strict expected-failure test is not used as P10 evidence.

Six named rational-equivalence facts pass both HA and independent Lean:
reflexivity, symmetry, transitivity, nonzero scaling, numerator-pair shifts,
and negation compatibility. Their six local `IRat` definition templates use
capture-safe conservative expansion and do not mutate the global registry.

Live E and Vampire logs each select `mul_assoc` and `mul_comm` for the exact
P08 supporting statement. This now drives a narrow native reconstruction, not
the old full-ring fallback. It is **premise-guided reconstruction, not TSTP
proof-log translation**. Z3 separately checks the six rational conjectures.

The fixed degree-seven composition has a checked universal trace-soundness
lemma and **13/16 exact trace chunks** checked in both HA and fresh Lean.
The final three chunks hit the canonical payload cap. Neither the whole trace
nor the variable-degree IR079–081 claims is complete. Both full-trace attempts
are preserved; no limit was silently increased.

The natural twice-square statement `a*a=2*b*b -> a=0 /\ b=0` also passes
fresh HA and independent Lean. Its 182-node bundle includes the entire
180-node ancestor cone of the existing Fermat-four theorem. This supplies
the natural-number core needed by IR016/norm separation.

SN001 now extends the zero-norm criterion to **arbitrary signed-pair integer
coefficients**: `(ap-an)^2=2*(bp-bn)^2 -> ap=an and bp=bn`, with explicit natural
square witnesses. It reuses unchanged ND0157 `SignedDifferenceSquare`, plus
22 actual v28 proof nodes and the complete IR016 bundle. The final 206-node,
40,402-body-node proof passed fresh HA in 5.08 seconds and independently
compiled Lean in 11.08 seconds, including logical negative controls. No claim
that all four raw components vanish is made. See the
[reviewed decomposition and scope](signed-norm-review.md).
The rational/real quantitative norm bounds, denominator/analytic bridges and
IR072 remain open; integer separation and multiplicativity were added above.

The [September 19 v3 wave index](observations/shared-wave-index-v3.json) pins
37 proof attempts and nine fresh-Lean observations: 28 distinct statements
checked in both HA and fresh Lean, with eight failed attempts retained.
The [previous v2 index](observations/shared-wave-index-v2.json) preserves
31 attempts and six fresh-Lean observations. After deduplication of
the E/V P08 demonstrations, that checkpoint contained 24 distinct HA/Lean-checked
statements: six named rational foundations, the twice-square natural core,
the signed zero-norm bridge, P10, two supporting lemmas, and thirteen composition
pieces. These categories must not be presented as 24 major irrationality
milestones. The [previous v1 index](observations/shared-wave-index-v1.json)
remains unchanged.

New regression validation passed **188 tests and 138 subtests**, in fresh
bounded batches. A combined reader/proof-test process had previously reached
the 512 MiB RSS guard and was stopped; splitting test lifetimes reduced the
largest batch peak to 424 MB. No unchanged oversized batch was retried.

The existing regression modules were then rerun in bounded fresh processes:
**165 tests and 131 subtests passed**, with the old P10 adapter's one strict
expected failure preserved. Combined with the new tests, that is 353 passing
tests and 269 subtests, not 353 proof certificates. The 216 generated local
files match a fresh deterministic build. All nine browser routes passed in
disposable Chrome profiles, including the definition DAG, named transitivity
theorem, planning cones and grand atlas; the screenshots were inspected.
The user's normal browser profile and the production website were untouched.

Validation records: [new proof/infrastructure tests](observations/shared-wave-validation-v1.json),
[existing regressions](observations/shared-wave-baseline-regressions-v1.json),
[deterministic site build](observations/shared-wave-site-validation-v1.json),
[new evidence pages](observations/shared-wave-browser-v1.json), and
[planning-map navigation](observations/shared-wave-map-browser-v1.json).

The signed-norm extension adds 21 proof/hostile-case tests and four exact
archive/presentation tests; all passed. The shared reader, protocol and Lean
intake were rechecked in the same run: [70 passing checks](observations/shared-wave-signed-norm-validation-v2.json).
Across the three suites this is **378 distinct passing tests and 269 subtests**,
plus the preserved expected failure of the old P10 adapter. That checkpoint's
222-file site passed [fresh build/check](observations/shared-wave-site-validation-v2.json),
[page/link/DAG regressions](observations/shared-wave-final-site-regressions-v2.json),
and [all ten isolated browser routes](observations/shared-wave-browser-v2.json).
The new signed-theorem and updated definition-network pages were visually inspected in
the established Quadratic Reciprocity design. An earlier combined
signed-norm test process reached its 512 MiB guard; its [stopped record](observations/shared-wave-signed-norm-validation-v1.json)
is preserved. Separate archive-heavy test processes reduced the peak to 453 MB,
with no cap increase. The signed-norm proof producer and fresh replay succeeded
on their first run under the original 768 MiB proof-worker envelope.

The Lean intake now checks case/schema/source agreement across both original
processes, rebinds the exact frozen target, and verifies archived source bytes.
Its fixed axiom-audit source must print the two actual endpoint reports;
empty output does not pass. Structurally valid false-goal/forged-body controls
must produce logical `REJECT`, not merely a decoding error.

All execution is sequential and bounded. The scripts and evidence are local,
uncommitted and unpromoted. Rebuilding Lean means fresh compilation of the
existing checker source closure followed by `lean --run`, not a new standalone
C binary and not a claim that arbitrary Lean mathematics translates to HA.

### Current mathematical frontier (not the historical pilot queue)

1. Complete the **quantitative** signed-norm branch: witnessed integer
   discreteness, the fully signed multiplicative norm identity, conjugate
   height bounds and explicit positive-denominator transport (IR030–032/035/046).
   SN001 supplies the zero-norm obstruction, not those inequalities.
2. Replace the fixed-degree composition experiments by **variable-degree**
   coefficient/recurrence theorems (IR079/080), reusing the existing polynomial
   infrastructure. The three size-limited trace pieces remain recorded; more
   fixed instances alone cannot close this universal goal.
3. Prove the explicit composition and Taylor tails (IR081/058), including the
   identification `exp(L)=2` for the specified logarithm series.
4. Assemble the universal auxiliary-vector, moment-polynomial and confluent
   interpolation arguments, then the perturbation/precision bridge to IR072.

Keep the same authority boundary throughout: Z3/E/Vampire output is untrusted
guidance or an independent conjecture test. Induction and domain-specific
identities need actual ordinary HA proof bodies, with fresh same-byte Lean
checks. No unchanged oversized retry, automatic memory increase, theorem
admission from a solver status, or claim of measured end-to-end LLM savings.

## Original verified pilot execution, 2026-09-19

The [post-hardening observation archive](observations/validated-pilot-v2/manifest.json)
contains exact source snapshots, frozen contracts, all solver exports and logs,
ordinary proof bundles, and fresh-process replay receipts. Gzip preserves the
original bytes; both compressed and uncompressed hashes are recorded.

The final run took **72.49 wall seconds** with one proof/solver worker. This
excludes earlier integration runs, agent engineering and the regression/UI tests:

| Result | Count / scope |
| --- | --- |
| HA-checked full pilot contracts | 3: P01, P05, P07 |
| HA-checked supporting subleaves | 5: P02, P03, P06, P08, P11 |
| Classical solver hits, two CPU seconds per call | Z3 8/8; E 3/8; Vampire 1/8 |
| Universal IR parents closed / new library admissions | 0 / 0 |
| SMT or TSTP proof logs translated / independent Lean rebuilds | 0 / 0 |

P01 is signed-rational addition compatibility with actual denominator guards.
P05 verifies the recurrence step, not its base cases or uniqueness. P07 is the
signed-integer two-frequency identity; it does **not** provide the quadratic-field
domain lift. Supporting targets are never silently substituted for their parents.

All 15 arithmetic premises supplied to the solvers were regenerated from the
literal source and freshly HA-checked, without importing the full theorem
registry. Fresh replay checks the original formula, closed context, canonical
bytes, forged-body rejection and false-root rejection. Contract-specific
mathematical mutation witnesses still need their own validation campaign.

The comparison is **native-only versus solver-gated independent native reproof**.
Both arms use the same native factory. Solver hits are not translated proof logs
and this run does not establish solver acceleration. Measured child CPU: native
20.20 s, solver-gated native 20.31 s, solver/probe 25.83 s, basis setup 0.39 s.
Proof workers made zero model calls; agent-authored contracts, code and review
are LLM engineering work whose token cost is not measured here.

E 3.2 is now installed through Homebrew. Z3 4.15.4 was already available.
The official Vampire 5.1.0 macOS ARM64 release was checksum-verified and used
from a temporary configured path, not installed globally. A missing future
Vampire path must be reported unavailable, never silently replaced.

### Historical resource boundary and then-remaining work

An initial test-filter typo included the P10 large-number case; it was stopped
by the 512 MiB memory guard. The corrected filter excludes that open benchmark.
After early copy-work/serialization checks and shared squaring were added, its
one changed-strategy retry failed closed in 0.52 CPU seconds at 58.3 MB peak RSS.
**P10 was not certified in this baseline.** Twenty small/adverse binary tests passed; the full P10
test remains an explicit strict expected failure, not a passing proof claim.

The controller now pins the canonical codec, enforces nested wall alarms, and
preserves supervisor output measurements. A real forced-alarm handoff smoke
confirmed owned-child cleanup and restoration of the caller's signal state.

Then-planned work (historical; item 1 is completed by the shared-proof wave):

1. Replace repeated whole-body Cut copying with topologically shared operation
   bundles; then certify the already elaborated P10 closed inequality.
2. Connect P04's finite composition and P09's exact confluent coefficients to
   their actual HA trace predicates.
3. Certify all steps of P12's fixed approximation trace; a final host comparison
   alone must not be counted as P12.
4. Lift P02/P07 to the required signed/quadratic domains, then finish the rational
   denominator and power/fold bridges in P03/P06/P08/P11.
5. Add contract-specific hostile witnesses and a deliberately small,
   fail-closed proof-log reconstruction subset before claiming solver speedups.

The original integration runs are retained in `observations/integration-*-v1`.
They predate the source-pin, deadline and root-mutation harness repairs; the v2
run is the final post-hardening observation. No failed experiment was erased.

## Observed non-LLM calibration, 2026-09-19

The recorded [automation baseline](automation-baseline.json) took approximately
0.42 seconds before report serialization, under a 30-second aggregate ceiling.
It regenerated three elementary arithmetic certificates with existing native
compact arithmetic and checked their universal closures in ordinary HA, in
empty context. It also checked rejection of a false target. These demonstrate
the existing proof-producing infrastructure, not new irrationality lemmas.

Z3 4.15.4 produced `unsat` and a proof-shaped log for a guarded parity example.
That earlier result is recorded as unchecked external evidence: no Z3 proof was
translated or admitted. At baseline time Vampire and E were unavailable on PATH;
they were configured later for the pilot above. Native and Z3 baseline workers
used approximately 24 MB peak RSS each.
The deterministic proof workers made zero model calls; agent planning/review
was separate LLM work, and its token cost is not being represented as zero.

Exact-integer/Fraction calibration separately checked:

- 441 small confluent monomial identities, 21 selected-coefficient identities,
  315 coefficient-bound checks and 315 denominator-clearing checks;
- 26 quadratic moment-polynomial identities and 42 nonzero frequency norms;
- 17 finite approximation precisions, 136 pairwise finite-coherence checks,
  and certificates for 12 specified rational candidates (largest precision 13);
- the symbolic exponent ledger and small arithmetic boundary cases.

These are bounded experiments. They do not prove the analytic accuracy of the
approximation sequence, any variable-degree interpolation theorem, universal
irrationality, a practical extracted running time, or the total campaign cost.
No enormous auxiliary matrix was allocated.

## Reproduction and validation

Original baseline validation: **165 tests and 131 subtests passed**, with the known-unresolved
P10 benchmark explicitly excluded. The 147 generated files match a deterministic
rebuild; graph/link/mutation checks and JavaScript syntax checks pass. Landing
and results pages rendered successfully in isolated Chrome profiles (8.29 s),
and both screenshots were inspected. Temporary headless helpers were closed
after rendering; the user's normal browser profile was not used.

From the repository root:

```sh
python3 scripts/build_sqrt2_power_campaign.py --check
python3 -B -m pytest -p no:cacheprovider -q scripts/test_sqrt2_power_campaign.py scripts/test_sqrt2_power_exact_pilots.py scripts/test_sqrt2_power_automation_baseline.py
python3 scripts/sqrt2_power_exact_pilots.py
node --check scripts/assets/campaign-plan.js
python3 scripts/check_sqrt2_power_browser.py
```

The website generator checks graph acyclicity, typed edges, definition arities,
immutable parent hashes, exact output hashes and byte-deterministic rebuilds.
Mutation tests reject forged proof status, fake definition authority, changed
pilot scope and a pilot instance being presented as its universal parent.

Five browser routes were rendered: landing, overview, the irrationality cone
including definitions, the future transcendence neighborhood, and combined-atlas
G121. The browser checker uses fresh isolated profiles and validates emitted
DOM; on this Mac, lingering headless Chrome processes required explicit cleanup
after rendering. This is reported separately from page correctness.

To repeat the native/Z3 smoke, use `scripts/sqrt2_power_automation_baseline.py
--run --output <new-report-path>`. Existing reports are never overwritten.
Its source/binary pins and subprocess transcripts belong to that individual
observation. A baseline result is not a campaign proof-admission receipt.

To reproduce the bounded pilot, run `scripts/run_sqrt2_power_pilot.py --run
--output <new-directory> --vampire <configured-absolute-binary-path>`. Its
supervisor needs read-only process accounting. Source changes produce a new
observation, never an overwritten historical receipt. For the green structural
suite, include the `test_sqrt2_power_external`, `pilot_instances`, `pilot`,
`binary_certificates` and `alarm_handoff` files, with
`-k 'not test_p10_actual_closed_certificate'`; keep the excluded P10 failure
explicit. Do not launch an unbounded proof grind or promote planning artifacts.
