<!-- CURRENT_CHECKPOINT_2026_09_07_BEGIN -->
**Current checkpoint — 2026-09-07: the saved fresh 4B evaluation completed all 16 cases on source07/study06.** Job **22082082**, attempt `p6-paired-fresh-4b-v8-01`, ended **`COMPLETED 0:0`, process 0**, after 560 scheduler seconds and 556.776 controller seconds. All 16 cases had clean exits and confirmed cleanup. **One of 12 positive cases was proved; 11 positives and all four negative controls remained unknown.** The selected arm has complete execution and counter accounting: **165 model calls, 913 forward passes and 3,652 generated token slots**, with zero planner calls. [Actual terminal collection](paired-launchers-v13/prepared/arms/fresh_4b/observation-006/terminal-collection.json), [root completion](paired-launchers-v13/prepared/arms/fresh_4b/observation-006/actual-tool-completion.json), [frozen audit](paired-size-study-06/fresh4b-audit-01/audit.json), [actual audit completion](paired-size-study-06/fresh4b-audit-01/actual-completion.json).

The sole proof, **additive bound transitivity**, passed independent replay of the original theorem. Its winning script has **13 heuristic steps, zero model-origin steps and zero model calls**. The checked certificate has 2,684 distinct proof objects, 3,989 structural occurrences and depth 38. This is the same theorem proved by the separate historical source03 symbolic arm. The result establishes completed saved-adapter loading, inference and evaluation; it does not establish added proof coverage from the trained model. [Checked case and original replay](paired-launchers-v13/prepared/arms/fresh_4b/observation-006/result/case-11/case-result.json).

The frozen auditor returned `incomplete` with actual exit `2/a9db7a` because its other three declared roles were unselected. The selected source07 4B arm itself is complete. This study uses 30-second searches with common native work limits; library retrieval, planner, ranker, Vampire and other external advisers are disabled. It measures primitive model guidance with native heuristics, not the website's full hybrid configuration. [Frozen study](paired-size-study-06/study.json).

The [source07 monitor correction](../p6-paired-child-monitor-fix-03/HANDOFF.md) passed the real Linux CPU prerequisite. **CPU04 job 22080729 completed `0:0`, process 0, with all 64 scheduler queries completed, reaped and accounted for.** The probe observed three authenticated fork startup intervals and one exit interval with missing RSS; all resolved within 60 ms. The startup sequences reached natural terminal states without a sampled exec transition. Probe wall time was 12.454 seconds and aggregate CPU time 1.631 seconds. Independent admission passed (`0/4dd681`). It ran no model or native proof. [Actual CPU completion](../p6-paired-child-linux-probe-04/observation-001/actual-completion.json), [measured probe result](../p6-paired-child-linux-probe-04/observation-001/result.json), [source07 transfer](combined-inference-transfer-07/actual-tool-completion.json).

**Full allocation charges total 20,520 / 21,600 GPU-seconds (5h42m of 6h), leaving 1,080 seconds. No GPU job is active.** The completed 4B allocation is charged all 1,560 seconds. Charges include failed allocations and are not measured GPU busy time. No automatic retry or retraining was performed. [Immutable release charge](paired-launchers-v13/prepared/arms/fresh_4b/release/charge-intent.json), [campaign ledger](campaign.json).

The implemented [tokenizer-only preflight](../../scripts/audit_hydra_decoder_targets.py) measured **2,045/2,047 training targets and 432/432 validation targets compatible** with the current decoder. One training target's gold path was masked; another required 70 tokens including EOS against the 64-token limit. The actual 1.7B and 4B admissions bind identical tokenizer files and library versions. These checks loaded no model, ran no native proof and changed neither data nor weights. [Completed target audit](decoder-target-audit-01/fresh4b.json), [actual completion](decoder-target-audit-01/actual-completion.json), [tokenizer equivalence](decoder-target-audit-01/actual-tokenizer-equivalence.json).

The separate source05 fresh 1.7B run ended `FAILED 2:0` as job 21984652: six clean searches were unknown, case06 hit an infrastructure failure, and nine cases—including all four controls—were unrun. Its **46 model calls, 222 forward passes and 888 generated token slots** are a six-case subtotal. The [source05 partial audit](paired-size-study-04/partial-audit-01/audit.json) preserves incomplete execution and counter accounting. Source03 symbolic **1/12** with four unknown controls remains a historical reference. Only fresh 4B was selected on source07, so these sources do not form a matched model-size comparison. Fresh-model proof-quality improvement has not been established.

The dated [results snapshot](paired-size-study-06/website-update-01/render-01/snapshot.json) is [published](paired-size-study-06/website-update-01/render-01/publication.json) (`0/f45d28`) on the [local website](http://127.0.0.1:8767/). It reports the genuine audit and attributes the sole proof to native heuristics. The missing local server was restored using its existing startup script. A [single HTTP verification](paired-size-study-06/website-update-01/render-01/http-actual-completion.json) (`0/567cbb`) returned HTTP 200 with `no-store`; the served bytes match the published candidate and the embedded evidence matches the snapshot. Only the results section changed; all 21 protected files and 14 gallery proofs remain intact. The preserved local verification harness failures were corrected without another HTTP request. Publication and verification performed no model or native proof execution; visual QA remains unperformed.
<!-- CURRENT_CHECKPOINT_2026_09_07_END -->

**Historical checkpoint and evidence — 2026-09-05.** The original text below is preserved. Its status, budget and statements about selected jobs describe that earlier checkpoint; the current state is recorded above.

**Current status — 2026-09-05: CPU probe passed; the first fresh 4B evaluation ended FAILED 2:0; the completed audit records an incomplete evaluation.** The [recorded packet05 approval](p6-upload-review-05/USER_APPROVAL.json) remains valid. [Repair02](p6-source04-repair-02/attempt-01/actual-tool-completion.json) succeeded (`0/c97aae`): all 1,325 files / 112,082,345 bytes were verified, with the 821 existing files and source03 preserved. [Actual source admission](p6-source04-repair-02/ACTUAL_ADMISSION.json) passed (`0/03de3b`). The original stage `255/add706` and repair01 preflight `1/908edc` remain failed attempts.

**CPU probe02 job 21982369 passed**: Slurm `COMPLETED 0:0`, process 0, one scheduler second; probe wall time 0.957679 seconds and CPU time 0.342045 seconds. Both fixtures exited 0, were reaped and had confirmed quiescence. The probe actually observed a pre-zombie interval with missing RSS, then natural exit after about 51 ms, without zero-filling. It ran no model or native proof. [Genuine root completion](../p6-paired-linux-monitor-probe-02/observation-001/actual-completion.json), SHA `c112391409cc97f25cc0379b32e361816d3576aa2544d16f8cb514ca7d0c519d`; actual collection `0/81fbd8`.

The earlier CPU package01 stage `0/44f43a` and rejected held submission `1/b3a18d` remain preserved; that rejection created no allocation. The active `plgcredibleai2026-cpu` grant identified by [diagnosis `0/1966cc`](p6-cpu-account-diagnosis-01/actual-tool-completion.json) was used for the same first 1-CPU / 1-GiB / 60-second prerequisite, with all six payload files unchanged. Unrelated user CPU job `21982100` (`bruck1-build`) was untouched.

Paired-v9 preparation passed (`0/807968`); [the prepared record](paired-launchers-v9/prepared/prepared.json) has SHA `aa2de3c6a195be836535a8f5e295a269789653020cf1150961a19bc736e6c70f`. Fresh 4B job **21982562** was submitted held (`0/557789`) and released (`0/cb9830`) on source04/study03: one GH200, eight CPUs, 64 GiB and 1,560 seconds. It ended **FAILED 2:0** after 118 scheduler seconds and 114.6982745 controller seconds. [Observation003](paired-launchers-v9/prepared/arms/fresh_4b/observation-003/response.json) was collected successfully (`0/44cb64`).

Cases 00, 01 and 02 returned `unknown`, each with child exit 0, reaping and confirmed quiescence. Their saved-model reloads and inference worked. These three worker records report a **subtotal of 14 model calls, 106 forward passes and 424 generated token slots**; these are not complete audited arm totals. Case 03 stopped after 0.7147 seconds in the scheduler-child sampler, with exit -9 and the leader reaped, but quiescence unconfirmed. The retained diagnostic shows a child in D state with stable identity, matching UID, no RSS and empty command line. It does not establish the executable as `scontrol` or prove `PF_EXITING`. The corrected leader path handled the first three exits; this failure arose in the child sampler. Twelve cases, including all four controls, did not run.

The [source04 partial audit](paired-size-study-03/partial-audit-01/audit.json) completed with exit `2/a45b63`: `execution_complete=false` and `counter_accounting_complete=false`; the other three source04 arms are missing. Audit SHA: `8918d7dc725686ac7a14359656ed4395589b3dcaa68d791b758731cc564d63eb`. No full proof, final replay, accuracy score or model win was produced by this arm. The separate source03 symbolic result remains a descriptive reference.

The full 1,560-second charge is already reconciled: **17,400 / 21,600 GPU-seconds (4h50m of 6h), with 4,200 seconds remaining** and no refunds. The grant remains `plgccaiautore2026-gpu-gh200`. No GPU job is active. No further GPU run, retraining, retry or additional arm is selected. Source03 symbolic 1/12 and the earlier incomplete 1.7B arms remain separate results; no fresh-model improvement is established. Root alone owns remote phases and ledger updates.

The [results page](../../hydra-playground/index.html) now shows the [dated study03 snapshot](paired-size-study-03/website-interim-01/snapshot.json): three clean unknowns, the 14-call worker subtotal and twelve cases not run, with source03 references labelled separately. [Actual HTTP verification](paired-size-study-03/website-interim-01/actual-completion.json) (`0/0f8267`) used one GET: HTTP 200, `no-store`, exact served bytes and matching embedded snapshot. All 21 protected CSS, JavaScript, runtime and gallery files were unchanged. There was no restart, proof/model/native execution or visual QA. The [execution outcome](p6-upload-review-05/EXECUTION_OUTCOME.json) records the approved actions as executed with the evaluation incomplete; the [fresh 4B diagnosis](paired-size-study-03/fresh4b-diagnosis-01/REPORT.md) explains the remaining child-accounting failure. The [local child-monitor candidate](../p6-paired-child-monitor-fix-01/HANDOFF.md) passed 36 pure checks (20 child checks and all 16 leader behavior fixtures), actual `0/350c0a`, and independent read-only review found no remaining blocker. Frozen source04 is unchanged. The candidate is not integrated, uploaded or validated on real Linux; the recorded failure lacked flags and executable identity, so these checks do not establish that it repairs case03. No additional CPU/GPU job or retry is selected.

Hydra has working checked-lemma reuse, smaller native certificates, bounded
multi-step planning and complementary symbolic advisers. P0–P5 and P8–P9 have
implementation evidence. **P6/P7 and the final model comparison remain
incomplete.** Demonstrated gains concern native capabilities and costs on
exposed diagnostics; improved accuracy from a newly trained language model has
not yet been established. The original kernel, saved adapter and historical
model-only provider remain preserved.

The saved-model, smoke, failed-comparison and teacher-preflight outcomes
are described in [the measured results](MEASURED_RESULTS_2026-09-05.md).
Fresh 4B completed all 256 updates, validation and saving; validation loss was
1.266391. The recovered fresh 1.7B adapter passed an independent reload without
retraining. The first three fresh 4B evaluation workers also completed real
saved-model loading and inference, but all returned unknown. The arm failed
during the next startup and its audit remains incomplete. Neither training
loss nor operational inference establishes proof quality.

The unadapted 8B smoke completed in 45 scheduler seconds: two decoder calls,
eight finite gradient examples, zero optimizer updates and no changed trainable
tensors. It produced zero native-accepted primitive proposals and no executable
structured plan. This is runtime evidence only; 8B training has not been selected.

The initial symbolic comparison stopped after nine clean unknown cases, one
process-accounting failure and six cases not run. Its failed evidence remains
preserved. The separately reviewed monitor and summary corrections are now
staged as combined03, with only the two intended source changes. The user's
[explicit packet04 approval](p6-upload-review-04/USER_APPROVAL.json) resolved the
transfer/control-code review block for this exact four-arm workflow.

Actual paired-v5 preparation passed. Symbolic job 21978966 completed all 16
cases: one of 12 positives proved, and all four controls remained unknown.
Historical 1.7B job 21979201 failed before inference, leaving fourteen cases
unrun. Fresh 1.7B job 21980166 passed saved-adapter reload and made five model
calls in one bounded search, which remained unknown. The monitor then failed
during worker exit and stopped the remaining fifteen cases. All three source03 Slurm
jobs are terminal. Source04 fresh 4B job 21982562 ended FAILED 2:0 after three clean unknown
results and a scheduler-child accounting failure; its completed audit records
incomplete execution and counter accounting. None of these incomplete model arms is
a completed accuracy measurement; missing results are not zeros.

The teacher trial failed in dataset preflight before loading the model. Its
input copy omitted 20 baseline dependencies; exact originals already exist in
source07. [The local packaging correction](../p7-teacher-admission-fix-01/HANDOFF.md)
passed three focused closure checks, but has not been staged or run remotely.
No teacher continuation, measured teacher yield, admitted distillation dataset
or student update exists. Positive independently checked teacher yield remains
mandatory before student training.

**Budget charged: 17,400 of 21,600 GPU-seconds; 4,200 seconds remain.**
These are full allocation ceilings, including failed attempts, not measured
busy time. The failed fresh 4B allocation is already charged all 1,560 seconds.
Source04 admission and the actual Linux CPU prerequisite passed before release.
No GPU job is active. The 4B job is terminal FAILED 2:0; its evaluation remains incomplete. No budget expansion, unused-time
refund, automatic retry, retraining, teacher follow-up or 8B training is selected.

**Preserved review history:** automatic approval review rejected source04 twice
before process creation, including normal reconsideration with an exact data-scope
audit. The later explicit [packet05 approval](p6-upload-review-05/USER_APPROVAL.json)
resolved that blocker and remains valid. The original failed stage and repair01
remain failed; separate repair02 and source admission now succeeded. The first CPU
submission was rejected before allocation; probe02 subsequently passed. No
failed model arm is selected for repetition.

The earlier source03 partial audit returned incomplete (2/894fd1): all three
terminal arms are included and 4B is missing. Four historical read-only HTTP requests
confirmed the earlier source03 snapshot, an idle server, four modes and 14
gallery cases, all HTTP 200 (0/c12658). These existing native-verified proofs
are not attributable to the freshly trained models. No in-app browser is
connected, so visual QA remains incomplete. See [the full progress history](PROGRESS.md)
for preserved failed attempts and exact terminal evidence.

| Package | Demonstrated outcome and practical limit | Evidence |
| --- | --- | --- |
| P0: evaluation harness | Fixed eight-case baseline, source pins and actual terminal receipts: six of seven positives proved; the false control stayed unknown. These are development cases. | [Paired baseline](P0-P1-RESULT.md) |
| P1: compact arithmetic | Both offset-recurrence certificates fell from 5,024 to 54 structural occurrences, with unchanged proof coverage and no model/adviser calls. Unsupported inputs retain the fallback. | [Cost comparison](P0-P1-RESULT.md) |
| P2: checked library | Eighteen certificates with bounded decoding and rechecked imports. Three statement-only HTTP searches used earlier lemmas and passed independent replay; the false successor control remained unknown. | [Library results](P2-RESULT.json) |
| P3: proof sharing | Existing `Cut` preserves local composition in the versioned engine. A repeated-lemma proof fell from 33,751 to 4,043 distinct objects and 40,499 to 5,081 occurrences, with the same axiom footprint. | [Paired certificate measurement](P3-RESULT.json) |
| P4: structured planning | Bounded native actions and deterministic induction strengthening work. The cubic-mod-6 HTTP proof used 30 commands, including nine generated-plan commands. This is not a learned-planner success. | [Planning and replay](P4-RESULT.json) |
| P5: decision data/ranker | Reproducible 2,047/432/624 train/validation/test primitive examples. At identical limits, ranker-on lost the even-product proof: positives fell from 2/3 to 1/3. **Ranker stays off by default.** | [Gain/loss comparison](P5-RESULT.json), [portable data](p5-data-gate-03/PORTABILITY.md) |
| P8: shared advisers | SymPy and cvc5 contributed native-replayed proofs; Vampire scheduling also passed. Selected advisers share twelve requests, sixty external seconds and one child. External success alone never proves a theorem. | [Actual contributions and cleanup](P8-RESULT.json) |
| P9: E and egg | Both real standalone adapters contributed independently replayed proofs and rejected false variants. Both HTTP examples proved entirely through native heuristics: no additional HTTP proof power was demonstrated. **Both remain off by default.** | [Standalone versus HTTP evidence](P9-RESULT.json) |
| Website | Experimental controls, provenance, branch inspection, certificate costs, custom tests, manual replay and downloads are implemented. HTTP cancellation released the worker slot; manual proof then succeeded. Three freshly replayed examples brought the gallery to fourteen, preserving all eleven originals. Visual browser QA remains incomplete. | [Website checks](P10-WEBSITE-RESULT.json), [controls](../../hydra-playground/index.html) |
