**Hydra hybrid integration — 2026-09-01**

On the final four positive integration probes, heuristics proved **3/4**, heuristics with Vampire proved **4/4**, and the full hybrid proved **4/4**. Vampire supplied native steps for the additional proof. The LLM supplied no additional winning step or solved case in this final set and increased elapsed time. Every accepted proof passed the original Peano kernel; 0 = 1 was never proved. These are deliberately selected, exposed engineering probes, not evidence of unseen theorem accuracy. [Final results](advisers-02/summary.json), [actual exit-0 receipt and source pins](advisers-02/actual-completion.json).

The heuristic mode means native tactic search; symbolic adds Vampire; hybrid adds the trained local LLM as well. The model mode uses the preserved model-only search. Tables sum **server-reported job elapsed seconds over all four provable inputs**, including unsuccessful attempts. They exclude negative or unsupported inputs, whose costs are given separately. Client polling time is not mixed into these figures. Model calls count candidate batches; Vampire calls count actual launches. Raw records retain forward-pass, decode-attempt and tactic counters.

**Initial pilot (pilot-01).** Four positive cases covered reversed congruence, two universal instantiations, existential transport and an induction conjunction. All three modes with heuristics finished without invoking either adviser. The model-only success was the induction conjunction. [Summary](pilot-01/summary.json), [actual exit-0 receipt](pilot-01/actual-completion.json).

| Mode | Positive proofs | Model calls | Vampire launches | Positive set: server s |
|---|---:|---:|---:|---:|
| heuristic | 4/4 | 0 | 0 | 4.32 |
| symbolic | 4/4 | 0 | 0 | 4.04 |
| model | 1/4 | 32 | — | 91.44 |
| hybrid | 4/4 | 0 | 0 | 4.44 |

The unsupported prime predicate was rejected in every mode, adding 0.32–0.34 server seconds per mode. The earlier model-only records have no Vampire counter, hence “—”; that mode does not enable Vampire. This pilot establishes the value of the heuristic layer on these cases, not a gain from invoking the LLM or Vampire.

**First adviser run (advisers-01), preserved with its integration bug.** Vampire returned ContradictoryAxioms on an inconsistent local premise, but the bridge classified that status as providing no refutation guidance. The original outcomes remain unchanged. [Summary](advisers-01/summary.json), [actual exit-0 receipt and recorded finding](advisers-01/actual-completion.json).

| Mode | Positive proofs | Model calls | Vampire launches | Positive set: server s |
|---|---:|---:|---:|---:|
| heuristic | 1/4 | 0 | 0 | 4.30 |
| symbolic | 1/4 | 0 | 16 | 8.72 |
| hybrid | 2/4 | 25 | 16 | 80.21 |

There was a real model contribution in this version: on the successor-zero implication, the fifth model call supplied exfalso. Its accepted proof contained six heuristic steps and one model step. This historical gain is retained; it is not attributed to the final implementation. [Original model-assisted proof](advisers-01/002-successor_zero_explosion-hybrid.json).

The separate false input 0 = 1 returned unknown in all three modes. It added **0.77 s** for heuristics, **5.23 s / 4 Vampire launches** for symbolic search, and **24.63 s / 8 model calls / 4 Vampire launches** for hybrid search.

**Final adviser run (advisers-02).** The bridge now accepts ContradictoryAxioms only as a source of untrusted, reconstructible guidance. Native search also gained a general unification attempt and bounded successor-witness construction. The five input statements were unchanged from advisers-01; this is a tuned integration rerun, not a sealed comparison. [Summary](advisers-02/summary.json), [actual exit-0 receipt and exact changes](advisers-02/actual-completion.json).

| Mode | Positive proofs | Model calls | Vampire launches | Positive set: server s |
|---|---:|---:|---:|---:|
| heuristic | 3/4 | 0 | 0 | 3.26 |
| symbolic | 4/4 | 0 | 5 | 3.82 |
| hybrid | 4/4 | 4 | 5 | 29.58 |

The separate 0 = 1 attempt remained unknown, adding **0.91 s** for heuristics, **5.40 s / 4 Vampire launches** for symbolic search, and **25.60 s / 8 model calls / 4 Vampire launches** for hybrid search. Including this negative test, final hybrid totals were 12 model calls and 9 Vampire launches. Search exhaustion does not itself prove falsity; the input's negation has a separate native reference proof.

The four positive hybrid results contain no model-attributed winning steps. Its four positive-case model calls occurred on local-negation elimination and quantified-implication instantiation, both also solved by the symbolic mode. Calls were therefore real but did not improve this set's proof count; adviser scheduling remains an optimization target.

One complete Vampire-assisted example is:

~~~text
forall a. S a = 0 -> a = 0
~~~

The exact accepted commands were:

~~~text
intro
intro
exfalso
apply PA1
assumption
~~~

The first two steps came from heuristics; the last three came from native reconstruction guided by Vampire's actual refutation. This took **one Vampire launch, zero model calls, seven certificate nodes and 0.81 server seconds** in symbolic mode. S a = 0 is impossible under PA1: this example demonstrates ordinary contradiction elimination and the integration boundary, not a new arithmetic discovery. Vampire's output alone was not accepted as a certificate. [Exact proof, provenance and solver receipt](advisers-02/001-successor_zero_explosion-symbolic.json).

A constructive witness example is:

~~~text
forall a b. (exists w. S w = b) -> exists z. S z = a + b
~~~

Its exact accepted commands were:

~~~text
intro
intro
intro
cases h
exists (n + x)
rewrite <- h_witness
simp
~~~

Here n is the introduced name for a; x is the predecessor obtained from the premise. Choosing z = a + x lets the addition recursion close the equality. All seven steps came from the new heuristic construction, with **zero model or Vampire calls and fourteen certificate nodes**. This is an actual search result, separate from the hand-written reference script. [Exact witness proof and provenance](advisers-02/006-synthesized_successor_witness-heuristic.json).

The [original diagnostic audit](../../hydra-playground/hybrid-evaluation-reference-check.json) and [adviser audit](../../hydra-playground/hybrid-adviser-reference-check.json) checked native reference proofs and found no exact canonical TRAIN/DEV statement matches. The schemas are familiar and the cases were chosen after inspecting implementation behavior; equivalent statements, intermediate-state overlap and base-model exposure are not excluded. No reference scripts were supplied to search.

The model-only control used at most 8 model calls, depth 16, 64 states and four candidates per state. The newer search allowed depth 32, 256 states, 24 candidates per state, a 16-state frontier and up to 1,024 tactic attempts, with advisers capped separately. This is an end-to-end engineering comparison with different search allocations. The local Base is lossy 4-bit quantized and does not numerically reproduce the GH200 evaluation. No training was performed.

Validation completed: the core test run passed **56 tests with actual exit 0** (recorded completion f095d8). Browser QA passed **six grouped checks with actual exit 0** (b4a6b5), covering real heuristic and Vampire proofs, branch snapshots and provenance, stale-state clearing, mobile/dark layout, and a real model invocation followed by cancellation, owned-worker cleanup and successful manual proof replay. All four screenshots were visually inspected. [Browser check record](browser-hybrid-01/browser-hybrid.json), [cancellation record](browser-hybrid-01/hybrid-cancellation-ui.json).

The [delivery verification](verification.json) binds these results, the archived application source, and the unchanged original kernel/model files. Its [externally observed completion](verification-actual-completion.json) is recorded separately from the verifier's own output.
