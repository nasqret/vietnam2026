The hybrid search now proves a Pythagorean triple family that the previous
version could not finish under the same limits, and avoids repeated adviser
and algebra-planning work. Eleven independently replayed examples are published
in the local gallery. The final artifact authentication is recorded separately. The saved trained weights and the frozen native kernel have
not changed. The improvements so far are in the hybrid search and its symbolic
planning, not evidence of increased learned-model accuracy.

The completed matched five-case comparison improved from **2/5 proved on v4 to
3/5 on v5**, with the same literal statements and Deep / Hybrid / 32 model calls /
beam 4 settings. These are selected, previously exposed development examples,
not an unseen benchmark or a statistical accuracy estimate. Search receives
only a statement and settings, never a reference script or saved proof.

| Selected theorem | v4 | v5 | v5 server seconds |
| --- | --- | --- | ---: |
| Fermat's little theorem for the fixed prime 7 | Unknown at limit | Unknown at limit | 303.74 |
| Sophie Germain identity in nonnegative coordinates | Unknown at limit | Unknown at limit | 302.74 |
| Balanced Brahmagupta identity | Proved | Proved | 6.36 |
| Pythagorean triple family | Unknown at limit | Proved | 13.24 |
| Every natural number is even or odd | Proved | Proved | 68.15 |

The new Pythagorean proof establishes, for every pair of natural numbers a,b,

```text
(a² + 2ab)² + (2b(a+b))² = (a² + 2ab + 2b²)².
```

It contains 17 ordinary native commands and 56,356 proof nodes. A generic
planner preserves repeated compound expressions and proves smaller connecting
equalities before finishing the original equation. Search checked every
command, finalized the original theorem and independently replayed the full
script. Both advisers had zero actual calls. Zero and degenerate triples are
included; primitivity and classification of all triples are not asserted.
The exact parser input uses repeated multiplication, not a new exponentiation
primitive. The balanced Brahmagupta result includes its essential 4abcd term;
it is not by itself a proof that sums of two squares are closed under products.

Parity retained the same 20-step / 11,061-node native heuristic proof while
actual model batches fell from 20 to 10 and actual Vampire launches from 12 to
9. The v5 trace explicitly records 10 skipped repeated full-goal model prompts
and three reused unsuccessful exact solver inputs. Its server time was 68.15
seconds versus 95.35 on v4. These are single-run engineering observations;
timing differences are not isolated causal estimates. Sophie Germain also
recorded three model skips and three solver cache hits. Lower F7 adviser counts
do not establish a cache saving: it recorded no cache hits and spent its budget
on repeated algebra attempts.

The initial v5 plans for F7 and Sophie Germain still hit the unchanged native
100,000-live-proof-object limit. Smaller local obligations did not solve that
cumulative proof-size problem. The v5 F7 run attempted the identical 75-command
plan six times, each stopping after 19 accepted steps. The separate
[prospective v6 refinement](evaluation-design/V6_REFINEMENT.md) adds bounded
memory of an attempted decomposition at an exact full-goals tuple and prefix
depth. Equal/deeper repeats can be skipped; shallower paths and changed contexts
remain eligible. It caches neither tactics nor proofs and makes no completeness
claim. The five-case table remains a v4/v5 comparison; it must not be presented
as a complete v6 rerun.

The one planned v6 Fermat-7 follow-up also finished unknown at its limit
(304.40 server seconds), with worker exit 0 and confirmed cleanup. It attempted
the 75-command plan once, compared with six times on v5, and recorded 15 skipped
equal/deeper decomposition attempts. It discovered 1,210 states versus 271 on
v5; actual model calls were 12, with 42 repeated prompts skipped, and actual
Vampire launches were six, with six cache hits. This shows the duplicate work
was suppressed and the budget reached more alternatives; it does not establish
a proof, completeness or a latency reduction. The native proof-size bottleneck
remains. See the [single v6 follow-up](followup-v6-01/000-fermat_7-hybrid.json).

Two separate v6 positive checks also passed. The existing cubic congruence
`forall n. exists k. n*n*n = n + 6*k` retained its 30-step / 58,884-node proof
with no adviser calls (12.94 seconds). The new parameterized divisibility
challenge `forall n m. exists k. m*n*(n+1) = 2*k` produced an 11-step /
40,344-node proof (35.89 seconds). It constructs the quotient by induction while
keeping m arbitrary. The search made three model calls and three Vampire
launches, all off its entirely heuristic winning path. The latter has no fresh
v4 baseline and is not added to the paired comparison denominator. See the
[cubic regression](regression-v6-01/000-cubic_mod_6-hybrid.json) and
[multivariate challenge](multivariate-v6-01/000-multivariate_consecutive_product_even-hybrid.json).

Both false near-miss controls returned unknown/limit, with no checked proof:
seventh powers modulo 8 (98.37 seconds, nine model calls/four Vampire launches)
and the altered Sophie Germain coefficient (84.65 seconds, twelve/three).
Their mathematical counterexamples are external expectations; the search did
not produce native refutations. The final symbolic reconstruction control,
`forall a. S a = 0 -> a = 0`, did prove its implication in five steps / seven
nodes (0.72 seconds). Its contradictory premise supports native contradiction
elimination: two steps came from heuristics and three from one actual Vampire
launch; the model did not run. This is an integration check, not advanced
arithmetic. All seven batches / sixteen case records passed the
[read-only artifact audit](final-audit-01/AUDIT.md), with actual evaluator exits,
unchanged source pins and confirmed worker cleanup.

The native kernel, saved adapter, original model-only search, public profiles,
arithmetic bounds and Vampire runtime policy remain unchanged. Model memory is
local to one search/provider and matches the full ordered goals exactly. Solver
memory matches exact exported bytes and a fixed runner/profile, caches only
fully recorded unsuccessful attempts, and supplies no tactics on a hit. Explicit
runner failures now take precedence over misleading timeout/theorem text in
partial solver output. The real solver diagnostic made one actual launch and
skipped one exact repeat after a recorded resource stop; it was not a theorem
proof or a Hybrid timing benchmark.

The first full v5 gate ran 162 tests and failed with nine failure entries in five
worker-test methods. Its parent harness imposed a hard CPU ceiling below the
worker's unchanged initial limit, causing worker startup failures. The complete
record remains failed. A corrected harness reran all ten worker tests and
passed with exactly the same app/test bytes; the other native/search checks,
including statement-only Pythagorean discovery, had passed in the first attempt.
These are separate checks, not one claimed all-green 162-test execution.

The separate final-v6 gate passed all 48 focused tests, with zero failures,
errors or skips and unchanged source pins (94.430 seconds, actual exit 0).
It covers exact-goal memory bounds, real recurring native states, changed
contexts, shallower prefixes, authority/depth rejection, original search
regressions and a new statement-only Pythagorean discovery. See the
[focused v6 gate](refinement-gate-v6-01/result.json).

Evidence already complete: [v4 baseline](baseline-v4-01/summary.json),
[frozen v5 comparison](comparison-v5-01/summary.json),
[baseline audit](evaluation-design/BASELINE_AUDIT.md),
[first full gate](full-gate-01/result.json),
[worker harness correction](worker-gate-02/result.json), and
[real solver cache diagnostic](vampire-cache-diagnostic-01/result.json).
Every completed evaluation retains its exact requests, source pins, job IDs,
actual terminal receipt, native trace and cleanup evidence. Unknown within
bounds is neither a proof nor a mathematical refutation. General Fermat remains
unproved by this system; no additional general-Fermat run is scheduled.

The [local gallery](http://127.0.0.1:8767/#showcase) now contains eleven examples.
Three were added in this task: the v5 Pythagorean and balanced Brahmagupta
records, and the v6 parameterized even-product proof. All three exact original
theorems and returned scripts passed fresh offline native replay before the
manifest was published; the publisher made no model or Vampire calls. The old
eight proof files remain unchanged. The
[publication receipt](showcase-stage-01/summary.json) retains each replay and
its actual child exit. Editorial titles do not replace the exact formulas,
source versions, invocation counts or winning-step provenance.

The [browser check](browser-advanced-01/browser-advanced.json) passed all six
grouped checks, using the new Pythagorean record for proof inspection and fresh
manual replay. All eleven cards loaded, and eight screenshots cover desktop,
mobile and dark layouts; the new cards and proof controls were also inspected
visually. One additional blank-script Deep cubic search succeeded. A separate
Research test was deliberately cancelled after actual worker progress, then a
manual proof succeeded after cleanup. Those two UI jobs are functionality
checks, not additions to the sixteen-case experimental denominator. The fresh
isolated browser exited, both owned jobs were terminal and the computation slot
was released. No existing browser profile or session was used.

The final source archive is `source-v6-final`; the comparison archives remain
`source-v5` and `source-v6`. The frozen kernel, model/adapter/tokenizer package,
compact runtime and Vampire binary are authenticated by the separate
`verification.json` completion record. The live address remains
http://127.0.0.1:8767/; the final idle observation is saved separately in
`final-server-status.json`. No new training or remote GPU allocation was made.
The next unresolved obstacle for Fermat-7 and Sophie Germain is cumulative
native proof size, not simply a need to repeat the same plan with more calls.
