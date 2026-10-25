**Hydra playground**

The [implementation plan](IMPLEMENTATION_PLAN.md) is in progress. Checked lemma
reuse, compact certificates, deterministic planning, a switchable branch ranker,
and the SymPy/cvc5/egg/E integrations are implemented and checked. Use the
website's Experimental panel to select them. The ranker stays off after losing
one positive proof in its fixed comparison (2/3 to 1/3); E and egg also remain
off because their website checks did not add proofs. See the
[current evidence and experiment status](../output/hydra-implementation-2026-09-04/PROGRESS.md).

For the September implementation plan, fresh-model training, teacher
distillation and the final model comparison have not yet met their delivery
criteria. That plan's 1.7B/4B/8B Torch providers are for separately allocated
Helios experiments; those Torch backends are unavailable in this Mac server.
The separate October WMI adapters use the local MLX path described below.
The previous saved adapter and original model-only mode remain unchanged.

A local interface for entering your own statements about natural numbers, combining native tactics, Vampire and the trained Hydra model, and inspecting proof branches and remaining goals. The default address is `http://127.0.0.1:8767`. From the repository root, start it with:

```sh
./hydra-playground/start.sh
```

The launcher selects the configured Python and starts `server.py`; `HYDRA_PORT` can select another free port. Manual replay and heuristic search work independently of model setup. The local model runtime and pinned Vampire 5.0.1 were prepared on 2026-09-01. Each mode checks its own dependencies before becoming available. Model inference needs host Metal access; run the launcher in a normal Mac terminal.

Choose **Your own theorem**, enter a statement, select a search mode, and click **Find a proof**. Every new search ignores the script editor. A successful search fills it with the independently checked winning commands. Click a trace step to inspect its source, hypotheses and remaining goals, or use **Play steps**. The separate branch explorer shows attempted alternatives, their parent branches, and exact saved goal snapshots; an open or rejected alternative is not a proof. You can also supply your own commands and use **Run next tactic** or **Check entire script**. **Download this run** saves the result only when you request it.

| Mode | Components | When the model runs |
| --- | --- | --- |
| Hybrid, the default | Native heuristics, Vampire, saved trained adapter | Only after an unresolved choice reaches the advice queue |
| Symbolic | Native heuristics and Vampire | Never |
| Heuristics | Native tactic search | Never |
| Model only | The preserved original local model search | At each selected proof state |

Choose **Standard**, **Deep**, or **Research** for Hybrid, Symbolic, or Heuristics. These are finite presets, not arbitrary resource overrides. The original model-only algorithm keeps its original 8/16-call and 1/4-beam choices; advanced profiles do not change it. The model proposes four candidate tactics per call. A branch width selects a retained frontier, not the original model beam, so the modes are not a controlled beam comparison.

| Profile | Worker / search wall ceiling | States / tactic checks | Proof steps | Model call choices | Frontier choices | Vampire attempts × solver time |
| --- | --- | --- | --- | --- | --- | --- |
| Standard | 180s / 150s | 256 / 1,024 | 32 | 8, 16 | 16, 64 | 4 × 1s |
| Deep | 330s / 300s | 2,048 / 12,000 | 96 | 16, 32, 64 | 128, 192 | 12 × 5s |
| Research | 660s / 600s | 8,192 / 40,000 | 160 | 32, 64, 128 | 192, 256 | 24 × 15s |

Limits are ceilings, not work that every request performs. Search reserves time for final replay, source checks and cleanup. Only one computation runs at a time; **Cancel** stops the owned worker and any owned Vampire child before releasing the slot. An unconfirmed cleanup blocks new computation, including a successful shutdown claim.

The hybrid engine first applies checked introductions, exact hypotheses, reflexivity, simplification, conjunction splitting and existential decomposition. It then explores short tactic sequences: equality rewriting, congruence, backward application, universal specialization, existential witnesses, cases, induction, and certificate-producing arithmetic. Unifying hypothesis applications can resolve metavariables left by backward reasoning. A bounded constructor heuristic can synthesize successor witnesses through addition, rather than only copy existing terms. Useful prefixes survive a later failed tactic; equivalent states are deduplicated using the native conservative alpha identity. A bounded mix of best-first and oldest-first exploration prevents one growing family of branches from indefinitely postponing alternatives or advice. This finite search is not a decision procedure, even though the tactic vocabulary is small.

Version 3 adds bounded sparse-polynomial reasoning in [arithmetic_search.py](arithmetic_search.py). It can calculate existential witnesses from local equalities, generate intermediate equalities for native rewriting, and prioritize induction branches with complete witness plans. These calculations are untrusted suggestions: they produce ordinary `exists`, `trans`, `ring`, `rewrite`, and other admitted tactic lines. Each line still passes the unchanged native engine, followed by independent replay of the complete proof. No target-theorem lookup or named theorem import was added. The existing native `ring` tactic internally builds certificates from its fixed general semiring laws; its per-tactic 100,000-node ceiling remains unchanged.

Version 4 also proposes a bounded auxiliary induction invariant when a polynomial quotient does not admit a direct successor witness. [finite_difference.py](finite_difference.py) computes the polynomial's finite difference and may suggest one stronger paired statement. Deep and Research admit its seven-line native projection; the stronger statement remains an open obligation until native induction proves it. The search attempts at most one such strengthening and gives it a finite priority window. This generates proof obligations and ordinary tactics, never trusted lemmas or new axioms.

Version 5 adds algebra plans that preserve repeated compound expressions and prove smaller connecting equalities. [atom_polynomial.py](atom_polynomial.py) and [polynomial_chunks.py](polynomial_chunks.py) propose ordinary native commands after a polynomial `ring` attempt fails. Longer plans continue in chunks of at most four or eight steps, according to the selected profile. Each continuation belongs to the exact checked prefix that produced it; rejection or pruning discards its remaining commands. Search may plan decompositions for at most twelve starting states, with two planner variants per state and six executable plans overall. Plans must fit the unchanged depth limit and a 64 KiB script bound. It selects the first proposed decomposition at a prefix; a later depth rejection can therefore miss another, shorter plan. The native arithmetic, live-proof and independent-replay limits remain unchanged.

Version 6 also skips planning a decomposition again when the complete ordered goal tuple has already received a validated plan at the same or a smaller prefix depth. [decomposition_memory.py](decomposition_memory.py) retains at most six states, with 64 KiB per key, 512 KiB of encoded goal payload and 64 diagnostic events; Python object overhead is additional. It records an attempt only after the full plan passes authority and remaining-depth checks. Shallower prefixes, changed contexts and changed goal order remain eligible. No tactics or proofs are cached. This is bounded heuristic pruning, not a completeness guarantee: identical displayed goals can have different accumulated proof objects. Actual planner invocations and skipped repeats are reported separately.

Repeated adviser work is now reported separately from actual calls. A search can remember up to 128 exact, complete ordered model-goal tuples within 512 KiB of encoded goal data and skip decoding the same tuple again. Vampire remembers at most 24 unsuccessful exact exported inputs within 256 KiB, for one fixed runner and profile. A cache hit supplies no tactics or proof evidence. Successful solver advice, transport failures and incomplete output are never cached. Explicit runner failures take precedence over timeout or theorem text in partial solver output. These scheduling choices can conserve work, but neither guarantees a faster search or a proof.

The website's verified gallery contains recorded theorem-only searches, with a second fresh native replay before publication. **Inspect proof** loads the saved trace and labels its counters as recorded. **Load theorem** loads only the statement and settings; **Find a proof** always ignores the script editor. Editing the input clears the old verified state. Gallery files are pinned by digest, and inconsistent or missing proof records prevent the gallery from displaying verified claims. These selected classical examples are demonstrations, not unseen benchmark accuracy or new mathematics.

The gallery now has fourteen examples. Three newly replayed records demonstrate
an actual SymPy witness, a cvc5 affine witness and checked-lemma reuse; their
winning-step attribution is retained. The eleven earlier proof files and their
manifest entries are unchanged. See the
[publication evidence](../output/hydra-implementation-2026-09-04/P10-WEBSITE-RESULT.json).

Those earlier records include a Pythagorean triple family (17 steps / 56,356 nodes), the balanced four-variable Brahmagupta identity (5 / 77,608), and `m*n*(n+1) = 2*k` with a constructed natural quotient for every n,m (11 / 40,344). Each passed a fresh independent publication replay. The first two records came from v5 and the parameterized induction from v6; their actual source versions are retained. Earlier examples include Fermat's little theorem for the fixed primes 3 and 5, the cubic congruence modulo 6, and divisibility of three consecutive factors by 6. All winning steps for these older arithmetic examples are native heuristics. Model and Vampire calls on other branches are shown separately.

The matched five-case development comparison improved from 2/5 proofs on v4 to 3/5 on v5 at the same Deep settings. The new Pythagorean proof finished in 13.24 server seconds; parity kept its checked proof while model calls fell from 20 to 10. These are selected exposed cases and single-run observations, not unseen accuracy or an isolated timing experiment. A separate v6 Fermat-7 follow-up skipped 15 repeated algebra attempts, 42 repeated model prompts and six unsuccessful solver launches, but still produced no proof. Sophie Germain and the general Fermat theorem also remain unproved by this system. The trained weights have not changed. See the [current experiment report](../output/hydra-progress-2026-09-02/RESULT.md) and [earlier advanced campaign](../output/hydra-advanced-2026-09-02/RESULT.md).

Vampire receives the focused native first-order state and the exact six Peano axioms PA1–PA6. Eigenvariables remain rigid, unresolved metavariables are not exported, and no induction schema or extra theorem library is supplied. The bridge extracts premises reachable in the returned refutation and tries native rewrites, applications, specializations or contradiction macros. **A Vampire refutation never directly closes a Peano goal.** Every accepted tactic must execute in the native engine, and the complete original theorem must pass both the final kernel check and an independent full script replay. Classical advice therefore cannot silently enable classical logic in the constructive checker.

The model loads lazily on the first needed hybrid call and is released when its worker exits. Model calls count batches with at least one completed forward pass; prompt-preflight failures are separate decode attempts. The interface also shows actual Vampire launches, explored native states, attempted tactics, and the source of each winning step. A proof obtained entirely by heuristics is labelled that way even when Hybrid was selected.

Each Vampire child uses profile-bound fixed arguments and offline generated input, with 64 KiB input and 256 KiB output ceilings. Standard solver/CPU/wall limits are 1/2/3 seconds and 256 MiB sampled RSS; Deep uses 5/6/8 seconds and 512 MiB; Research uses 15/16/18 seconds and 512 MiB. The whole worker retains an 8 GiB sampled RSS ceiling. RSS observations are not instantaneous hard memory caps. Ordinary solver timeouts and resource stops preserve bounded termination evidence and their actual exit code; none authorizes a proof. The official [Vampire 5.0.1 release](https://github.com/vprover/vampire/releases/tag/v5.0.1) archive and installed binary are pinned by digest. The installer, binary and original readiness record remain unchanged. That old smoke test attests the Standard configuration only; advanced profiles use the explicitly recorded runtime policy.

Vampire runtime policy v3 adds a macOS RSS watchdog because the [pinned release documents its internal memory limit as ineffective on macOS](https://github.com/vprover/vampire/blob/v5.0.1/Shell/Options.cpp#L81-L88). The runner samples only its own unreaped solver child every 20 ms and stops/reaps it above 192 MiB for Standard or 384 MiB for Deep/Research. A stopped solver supplies no advice; the rest of the search can continue. The parent's separate 256/512 MiB ceilings remain a backstop, and both checks can overshoot between samples. The unchanged `-m 256` argument is explicitly best effort. Failed jobs retain worker exits, memory peaks, and cleanup status even if final adviser counters are unavailable; partial progress counters are not final totals.

Statements are limited to 4,096 UTF-8 bytes and numerals up to 64; manual scripts allow 160 commands, each at most 512 bytes, within the joint 64 KiB request limit. Manual checks have a 120-second wall/CPU limit and 2 GiB sampled RSS ceiling. Powers in the gallery display use familiar mathematical notation; the exact submitted fixed-power formulas use repeated multiplication. Arbitrary exponentiation is still not a primitive parser operator.

Enter a **closed theorem**: bind every variable with `forall` or `exists`. For example:

```text
forall n m. n = m -> m = n
```

Use `S n` for the successor of `n`, `+` and `*` for arithmetic, `->` for implication, `/\` for conjunction, and `\/` for disjunction. Put one proof command on each line. A simple manual script is:

```text
intro n
intro m
intro h
symm
exact h
```

The playground keeps the sources of evidence distinct:

- **Model search** asks the local trained adapter for new candidate tactics, subject to finite search and process limits. Inspect the returned steps and native verification status; generated text alone is not a proof.
- **Hybrid or symbolic search** can combine heuristic and Vampire-guided steps with model suggestions when enabled. Actual invocation counts and winning-step provenance are separate: consulting a component does not mean its advice appears in the final proof.
- **Manual replay** checks the commands you supplied with the native proof engine. A successful manual script is not evidence that the model generated it.
- **Recorded model example** loads the actual eight-command proof of `hydra_teacher_frontier_universal_diagnostic_057` from the completed retention experiment. It took 16 model calls, produced nine proof nodes, and was independently replayed. Loading or replaying it is not a fresh model search.

The recorded theorem deliberately includes a universal hypothesis. With `T(k) = S(S(k + 4)) + 0`, it says that assuming `0 + T(z) = T(z)` for every natural `z`, we can establish that equality at one argument and its symmetric form at another. Do not remove that premise when describing what the model proved. The goal came from a fixed, exposed DEV template, not random theorem generation or new mathematics.

[examples.json](examples.json) contains that recorded example plus four explicitly authored entries: equality symmetry, addition with right zero, an existential witness, and the false statement `0 = 1`. Only the first has provenance `saved-model`. Its `source_record` retains the original proof-record path and raw SHA256; the other entries are labelled `illustrative` or `negative` and must not be presented as model outputs.

A result such as **not proved within the budget**, **exhausted**, **cancelled**, or **limit reached** does not mean the theorem is false. The model may choose unsuitable tactics or spend its allowance exploring branches. The negative example is known to be false in Peano arithmetic; failure to prove other statements does not establish their negation. Rejected tactics and remaining goals are useful diagnostics, not successful proofs.

The local model setup uses the exact pinned Qwen3-1.7B-Base checkpoint, converts its matrices to affine 4-bit weights with groups of 64, and loads the saved Hydra adapter. This lossy conversion is not numerically equivalent to the original training or evaluation runtime. Historical benchmark scores therefore do not measure this local version; each new successful proof still needs native checking.

The original 2026-09-01 browser smoke test proved `forall n. n = n` with model-generated commands `intro a`, `refl`: two model calls, two proof nodes, and 14.347 seconds including initialization and integrity checks. It also cancelled an active model request and successfully checked a manual script afterward. Separate browser checks covered the recorded eight-step proof, custom multiline input, false-statement rejection, parsing errors, trace navigation, and desktop/mobile layouts. These are functionality checks, not a model-quality benchmark. The [verification record](../output/hydra-playground-2026-09-01/verification.json) retains the actual successful tool exits and the earlier compatibility failure.

The first [four-mode hybrid comparison](../output/hydra-hybrid-2026-09-01/pilot-01/summary.json) completed all 20 requests: four positive statements and one unsupported input in each mode. Heuristics, symbolic and hybrid each proved 4/4; model-only proved 1/4 with eight calls available per statement. All four positive hybrid proofs used heuristics alone, so this comparison establishes no extra benefit from Vampire or the model. These deliberately authored, exposed engineering diagnostics are not unseen-test accuracy. Their exact statements have no matches in the saved TRAIN or DEV records, but they share familiar mathematical schemas. The independently checked reference scripts were never supplied to search. The earlier benchmark records and model-only implementation remain unchanged.

The final [adviser integration probes](../output/hydra-hybrid-2026-09-01/RESULT.md) tested four harder positive statements and the false statement `0 = 1`. Heuristics proved 3/4 positives; symbolic and hybrid each proved 4/4. No mode proved the negative. Vampire supplied three winning native steps in the remaining case. The model ran on unresolved choices but added no further wins in this final suite, and hybrid took longer than symbolic. An earlier preserved run did show a model-suggested `exfalso` completing a proof the then-current symbolic code missed. These observations justify the integration, not a claim that the learned component already improves the final prover's accuracy.

For an example of the new witness synthesis, enter:

```text
forall a b. (exists w. S w = b) -> exists z. S z = a + b
```

The native search unpacks a predecessor `x` of `b`, constructs the witness `a+x`, and checks the required equality using the addition recursion. For actual Vampire reconstruction, try `forall a. S a = 0 -> a = 0` in Symbolic mode. Its premise contradicts PA1; this is a contradiction-elimination diagnostic, not new mathematics.

The previous v2 implementation passed 56 integration tests and live browser checks for heuristic search, real Vampire reconstruction, per-step sources, exact branch snapshots, responsive layouts, and cancellation after a real model invocation followed by successful manual replay. The [v2 verification record](../output/hydra-hybrid-2026-09-01/verification.json) binds that historical implementation and its retained results.

The v4 arithmetic changes passed 111 integration tests. Subsequent worker telemetry and memory-watchdog changes passed separate focused gates of 40 and 43 tests. The new browser checks passed recorded-proof inspection, fresh replay, exact profile controls, a fresh Deep proof, Research cancellation, and desktop/mobile/dark layouts. Two false-statement controls returned no proof; a fresh model-only sanity check again used two calls, and a separate symbolic control reconstructed three Vampire-guided native steps. The installer, original model implementation, compact-model manifest, saved adapter and frozen kernel remain unchanged.

The final v6 refinement passed 48 focused native-search, memory, runtime and evaluator tests. Both false near-miss HTTP controls returned no proof, and the real Vampire reconstruction control still contributed three native proof steps with one solver launch. A read-only audit authenticated all sixteen versioned evaluation records. The earlier full v5 test attempt remains recorded as failed because its enclosing CPU limit blocked worker startup; all ten affected worker tests passed in a separate corrected harness with unchanged app/test source. These separate gates are not one claimed full-suite pass.

The historical v6 browser check passed all six grouped checks using the then-new Pythagorean proof: saved provenance and exact goals, fresh manual replay, input clearing, profile controls, a new Deep proof, and an owned Research cancellation followed by another manual proof. All eleven gallery records loaded; desktop, mobile and dark layouts were checked. The isolated browser exited and released the computation slot. See the [browser record](../output/hydra-progress-2026-09-02/browser-advanced-01/browser-advanced.json). The September 4 additions passed native replay, HTTP delivery and owned cancellation checks, but no connected browser was available for new visual verification.

The playground does not automatically train models or upload submitted theorems to a remote service. Setup may download public dependencies and stream the pinned base weights, without saving the full original checkpoint. Historical execution trees, datasets, model artifacts and proof receipts remain read-only. New playground runs do not overwrite or extend the archived experiment's scientific claims. Keep the HTTP server bound to the loopback interface; this is a local development tool, not a public service.

## October 21: explicit WMI sequential inference

The selected default is now **WMI C6 long vanilla11, step 16,384**, using
**Model + symbolic**. In the completed paired local comparison it proved
4/8 primary positives and 0/4 regression positives, versus 0/8 and 0/4 for
the historical adapter. Neither accepted any of the six false controls.
The four gains include three newly composed cases and one exposed WMI
development case. Every successful script passed independent native replay.
This small selected panel supports the replacement; it does not establish
general theorem-proving accuracy. The original adapter remains explicitly
selectable, and legacy Hybrid/Model retain it. See the
[comparison and integration report](../output/hydra-wmi-integration-2026-10-21/RESULTS.md).

The **Sequential** method supports explicit selection of three providers: the
previous mixed-retention adapter, WMI C6 vanilla47 (selected step 8,192), and
WMI C6 long vanilla11 (selected step 16,384).
This is a separate model-first path; the older Hybrid, Symbolic, Heuristic and
Model methods retain their existing behavior. Selecting a candidate never
silently substitutes another model. Model availability is not a quality claim.

Every step uses all outstanding goals, with persistent metavariable names and the selected model’s trained prompt. The WMI path uses its compact model-v3 prompt; the historical comparison path uses its primitive-v4 authority prompt/mask. All three sequential providers use greedy decoding and the same finite token limits. These decoding settings differ from the historical website’s beam-four model provider.

The sequential profile admits up to 64 binders, 1,024 formula AST nodes and
128 AST depth within the existing 4,096-byte theorem bound. It permits
32/64/128 model actions, 128 new tokens per action, 6,144 context tokens,
16,384 decision-token slots and 300 seconds for the request’s model/native work.

The web worker has a 360-second ceiling including final custody checks and
cleanup, 8 GiB sampled total RSS, a 6 GiB MLX allocation limit and one CPU-only
replay child with a 30-second limit. Trace bytes are bounded at 2 MiB and the
final result at 8 MiB. Limits are ceilings, not proof guarantees.

A model tactic is only a proposal. The unchanged native checker executes every literal prefix; no imported theorem is authorized. A successful original-theorem certificate must be independently replayed in a fresh offline child. Invalid tactics, timeouts and open goals remain unproved. Manual checks of sequential proofs use the same extended admission profile without loading a model. Frozen kernel sources, saved proofs and previous model artifacts are unchanged.

The vanilla47 export is authenticated to checkpoint `c6c5c90b27499f5f908d1a45f37d17087774e93e4e07db223fadf669f771c731`; export SHA `cabc8994cdc3a98295706041694bd0daa12d858ad5ea9d41027e5990ab7600c1`. All three local providers use the pinned quantized Qwen3-1.7B Base. Local MLX behavior is not asserted numerically equivalent to the original BF16 WMI run. The precommitted comparison and actual terminal receipts live in [the October integration directory](../output/hydra-wmi-integration-2026-10-21/).

The latest locked WMI checkpoint found in the October 21 metadata check is
**long vanilla11, step 16,384**, with checkpoint SHA-256
`177501bf7b662a210b6cf6887844a282365437c781e53138ad5495f02c620a06`.
Its training run stopped at its budget limit after 20,352 of 24,576 planned
updates; the locked checkpoint was selected from the completed evaluations.
Its recorded development selection score is 60/64; this is not a fresh local
or unseen benchmark result. Its bitwise-checked CPU safetensors export SHA-256 is
`659f71892bacdafc7488d8b683dd8dda051dfa4b054f74ba340db4da59fd07a3`.
Website selection lives in `deployment_models.py`, separate from the sealed
comparison selector.

The default **Model + symbolic** method first runs the selected model using
Sequential’s fixed 128-call/300-second search budget. After a clean bounded
unknown, a separate Standard Symbolic worker starts again from the original
theorem, with native heuristics and Vampire and no model. Each phase must finish
with confirmed process cleanup before the next starts. The two worker ceilings
are 360 and 180 seconds within a 550-second total ceiling.

The app retains both phases’ actual work, but displays only the winning script
and its proof sources. It never combines partial scripts or treats
cancellation/internal errors as proofs. The legacy Symbolic admission is
unchanged; expanded-only formulas retain the model result when that fallback is
unavailable. Legacy Hybrid and Model methods still use the original saved adapter.

The sequential providers now cache the authenticated tokenizer's immutable vocabulary length. The previous implementation queried the full vocabulary once per prompt token (about 13 ms per query in the measured CPU check). The read-only view delegates encoding, decoding, special tokens and authority masks unchanged, checks tokenizer integrity at case boundaries and finalization, and retains the exact full-prefix model backend. It does not enable KV caching. Both actual tokenizers passed CPU equivalence checks, and the deployment facade passed seven lifecycle checks. On 17 historical cases with identical prompts, outputs and actual work, case time fell from 1,731.301 to 538.308 seconds (3.216×); the deadline case is excluded from this ratio. The corrected paired comparison completed fresh runs of both models; the interrupted older candidate run is retained as incomplete diagnostic evidence and is not used for promotion.

The status API reports `default_model_id` and `default_search_mode` explicitly. Its historical `model` field continues to describe the adapter actually used by the legacy Model/Hybrid routes; selectable Sequential/Model + symbolic models are listed in `models`. A user's explicit model or method selection is preserved when status refreshes.

The web Sequential lane stops before another model call when the complete ordered printed goal state repeats. This catches cycles such as alternating `symm` steps without merging different branches or renaming variables. It is a bounded-search heuristic, not a claim that the theorem is false or that hidden native state is identical. In Model + symbolic mode, a clean stop permits the independent symbolic fallback. Both phase records retain the guard's telemetry. This web guard was not part of the matched V3 model comparison.
