# Campaign 5: stronger training and controlled recurrent inference

Status: authorized and registered 2026-10-16; main workers submitted. Current
execution state is in `status/campaign5.json`. The immutable main-v1 source
archive retains the protocol bytes used at registration; this header is a
delivery update and does not change its experiment contracts.
Scientific status: hypotheses under test, T4 empirical evidence only.

The user authorized broad execution of the improvement programme. This protocol
starts a new campaign; it does not amend Campaign 4 datasets, checkpoints,
budgets, test selections or outcomes. The goal is to improve complete
constructive proof success and determine whether recurrence contributes beyond
a stronger vanilla Qwen3-1.7B baseline. No improvement is presumed.

## Resources and execution

The finite campaign ceiling is 192 allocated GPU-hours and 32 allocated
CPU-only job hours across WMI and Helios, including profiling, tests, training and
evaluation. Individual workers are at most 24 hours on WMI and 48 hours on
Helios. Each submission is recorded in `artifacts/campaign5/jobs.json` before
interpretation of results. Failed submissions/runs remain in the ledger.
No automatic budget replenishment, other-project cancellation or node
exclusion is permitted. All jobs export ALL. The Mac is a control and preview
machine; all numerical work, tests and generated documentation run in SLURM.

Live resource probe 2026-10-16 01:52 UTC: no user jobs active on either cluster;
Helios GPU account has 20,000 hours allocated and 847.90 consumed. Scratch is
317.13 GiB of 12 TiB and 404,520 of 1,000,000 files. WMI's filesystem has about
17 TiB free, but the user's later home quota probe found only 7.58 GiB of
remaining personal capacity. The preparation job therefore checks exact
serialized output size and the personal quota before writing its new dataset.
These are dated observations, not a reservation or guarantee of scheduling.
Host CPUs accompanying GPU allocations are recorded in those job shapes;
the separate 32-hour limit concerns CPU-only allocations. Requested ceilings,
elapsed allocations and useful model execution are reported separately.

## Ordered experiments

1. Independently replay the completed Campaign 4 main proof trajectories.
   Correct the worker distinction between process exit, completed training,
   budget-limited training, skipped dependencies and unattempted work.
2. Profile actual Qwen3-1.7B gradient steps at microbatches 1, 2 and 4, including
   long contexts. Keep effective batch fixed at 16. Choose a feasible batch
   from measurements; hardware, padding, forward-block calls, tokens and wall
   times remain explicit. Do not equate matched updates with matched compute.
3. Expand constructive structural training coverage, with a target of at least
   2,048 training theorems (common cores counted separately), 192 development and 384 fresh test targets.
   Counts are targets until independently admitted. Retain full checker
   authority and shortcut tests. Exclude all prior Campaign 4 exposure cores
   from every new role, and exclude new test cores from all training and
   development. Separately count naming augmentation; renamed copies are not
   new structural theorems.
4. Compare vanilla depth 1, fixed depth 2, random depths 1/2/4 and adaptive
   recurrence, starting from the same pinned Qwen base and LoRA rank 32.
   Target 2,048 updates per arm, with three paired seeds if measured runtime
   permits within the ceiling. A separately registered 4,096-update extension
   is allowed only after development evidence and resource review. Keep the
   original 512-update results as historical controls; a duration-isolation
   comparison uses the old training data and remains separate from new-data
   effects. Within a seed, arms share hardware and sample ordering.
5. Adaptive training begins with all-depth supervision and zero gate gradient,
   then introduces the learned halt distribution and a delayed ponder cost.
   Separate gate, damping and LoRA learning rates. Record depth use, gradients,
   predictive/auxiliary/ponder losses, and actual full-depth training cost.
6. Select checkpoints by complete autonomous development proof success under
   an explicit per-arm policy. Break ties by inference block calls, then
   development loss, then earliest checkpoint. A fixed online roster is
   repeated at registered milestones. Missing/partial evaluation is ineligible;
   it is never silently treated as a loss-selected checkpoint. Reserve enough
   evaluation time for all milestones. The final test never selects anything.
7. Evaluate both raw autoregressive proof generation and separately labelled
   checker-assisted inference. Deterministic fresh binder allocation and
   bounded rejection feedback apply equally to every arm. Retain raw tokens,
   transformed actions, exact transformations, rejected candidates and budgets.
   Gold actions are unavailable to inference. Success requires explicit proof
   object acceptance by the pinned constructive checker.
8. Collect failures only on training targets. Admit corrective trajectories
   only after constructive replay, and compare continuation with/without the
   correction data. Keep these outcomes separate from the initial four-arm
   comparison. Development and test traces never become training examples.

## Freeze and reporting gates

Exact configurations, rosters, source manifests, data pins, policies, milestones
and task budgets are frozen before each stage. Capacity targets above may be
reduced only explicitly with the reason recorded; no result-driven silent
replacement. Reserve an untouched confirmation roster for the final chosen
comparison. Depth/entropy/KL/learned-stop sweeps are development diagnostics;
the final policy and inference budget are fixed before opening its test results.

The dashboard reports submitted, queued, running, budget-limited, completed,
validated and skipped states distinctly; complete proof numerator/denominator,
coverage, loss, measured cost, recurrence use and source freshness accompany
each result. Canonical records generate book, vault and dashboard projections.

Independent review is required before integrating empirical reports as
established evidence. Agent authorship and review are separate. Human review,
native Lean replay, unrestricted Heyting-arithmetic capability and statistical
significance remain separate questions. Three small seeds or a nominal
percentage increase alone do not establish a general recurrence advantage.

Assigned initial work: `c5_data` (corpus, <=8 CPUh), `c5_model` (trainer and
inference, <=4 CPUh), `c5_audit` (independent replay/admission, <=8 CPUh).
The coordinator owns orchestration, profiles, integration and canonical records;
the remaining CPU allocation is reserved for integration checks and publication.

## Registered duration control v1

`configs/campaign5-duration.json` and the WMI duration worker retain the old
Campaign4 corpus, permutation sampler, loss selector, rank32 adapters and
fixed recurrence4. Two fresh seed11 arms (vanilla/fixed) target2,048updates;
32old development proofs are monitored every512updates. This measures a longer
cosine training schedule on the old data and is separate from expanded-data,
proof-selected Campaign5 comparisons. It never opens the new test set and
does not alter historical checkpoints. Maximum worker allocation12GPUh;
individual training limits30,000s, worker42,900s, all omissions recorded.


## Objective and selection mathematics

Let $\ell_r(\theta)$ be masked next-action cross entropy after $r$ core passes,
for $r\in\{1,\ldots,R\}$. The additional shared passes use bounded residual
scales, $u\mapsto u+\alpha_j(L_j(u)-u)$, with
$0<\alpha_j<0.25$. Parameter storage and executed transformer depth are
therefore different quantities. The current Qwen retrofit uses a frozen
1.7B base plus rank-32 LoRA adapters, trainable recurrence damping and (for the
adaptive arm) a halt gate; it is not full-parameter recurrent pretraining.

During the adaptive warmup the loss is

$$
\mathcal L_{\mathrm{warm}}(\theta)=\frac1R\sum_{r=1}^{R}\ell_r(\theta).
$$

After warmup the gate hazards define an exit distribution $q_r$; the final
hazard is forced to consume the remaining survival mass. The registered
objective is

$$
\mathcal L(\theta,\phi)=(1-a)\sum_{r=1}^{R}q_r(\phi)\ell_r(\theta)
 +\frac aR\sum_{r=1}^{R}\ell_r(\theta)
 +\lambda(t)\sum_{r=1}^{R}r q_r(\phi).
$$

Entropy, inter-pass KL divergence and depth enter the halt gate through detached
features. Hence gate training and differentiation through the recurrent state
have distinct paths. Every depth still executes during this training objective;
$\mathbb E_q[r]$ is not a measurement of saved training FLOPs. Inference may exit
early under a frozen quantile rule. A low-entropy incorrect action is still
incorrect, and only original-target kernel acceptance counts as proof success.

For a fixed online development roster $D$, define $S_t$ as the number of
complete accepted proofs at checkpoint $t$ and $C_t$ as actual logical forward
block calls summed over all its attempts, including failures. Among complete
eligible evaluations, select lexicographically by

$$
(-S_t,\ C_t,\ \ell^{\mathrm{dev}}_t,\ t).
$$

The ordered task roster, checker authority, inference policy and action/token
budgets are fixed across these comparisons. This ranks saved checkpoints; it
does not provide a significance test. Final analysis must retain paired
success/failure outcomes at the common-core level, family strata, hardware and
seed variation, and quality versus measured compute. Assisted inference has a
separate success measure and must retain its additional calls and interventions.

## Main comparison and admission record

The raw corpus contains 2,048 base training theorem sessions over 1,024 common
dependency cores, plus 532 pure naming augmentations. Development has 192
sessions over 96 cores; test has 384 sessions over 192 cores. The paired
propositional and existential realizations of a core stay in one split. All
282 old exposure cores and six old overbudget descriptors are excluded.
The action-row counts are 202,917 / 15,151 / 30,427 for train / dev / test.
These remain structured constructive dependency and branching tasks; larger
counts do not establish general arithmetic or induction capability.

Generation job 285219 accepted every explicit gold proof. Independent audit
285246 checked all 3,156 stored proof/trace/target bindings, the structural
partition, 43,446 premise-deletion witnesses and 532 naming pairs, then freshly
replayed a deterministic stratified sample of 128 gold proofs and 192 finite
cheap-closer attempts. No sampled closer solved its target. This is T4 corpus
evidence, not learned-model success or a shortest-proof guarantee. The scope
and source pins are in `research/agents/c5_audit/corpus-review.md`.

The failed 4,096-token preparation is preserved. Exact tokenizer scan 285248
found maximum reference sequence lengths 5,546 / 5,368 / 5,522; a common
6,144-token limit retains every gold session. All main training and inference
conditions use this limit. Autonomous states may exceed reference lengths;
the generation context guard remains active and its failures count explicitly.
Preparation v2 preserves the original selection quotas and requires zero
excluded sessions before registration.

The main design registers seeds 11, 29 and 47 on Helios GH200 hardware. Each
seed compares vanilla, fixed two-pass, randomized 1/2/4-pass, and adaptive
recurrence for 2,048 optimizer updates at effective batch 16 and microbatch 4.
The first 512 adaptive updates supervise all four depths without gate training;
gate and damping learning rates are respectively ten and five times the LoRA
rate. Family and setup/reasoning buckets receive equal sampling weight. A
fixed 64-task development prefix selects checkpoints at updates 512, 1024 and
2048; its full 128-task development roster and a separate 256-task test roster
are evaluated only after weights and primary policies are locked.

Each seed has a 32-hour training worker and a dependent 24-hour inference
worker, for a main maximum of 168 allocated GPU-hours. Outer training task
caps are 20,000 / 26,000 / 28,000 / 39,000 seconds for vanilla / fixed / random /
adaptive. They reserve each task plus cleanup within the worker allocation.
They are operational safety ceilings, not equal-compute conditions or a
guarantee that 2,048 updates finish. Only completed matched runs enter the
primary comparison; every partial or omitted run remains visible. Worker arm
order rotates by seed. A failed or partial training dependency cannot be
reported as a completed evaluation.

Raw posttraining evaluation fixes one primary policy per arm: depth 1 for
vanilla, depth 2 for fixed and random, and learned exit quantile 0.5 for adaptive.
The per-policy wall ceiling is 5,400 seconds. Separately, every arm receives
the same fresh-name repair and one checker-feedback retry on the full 128-task
development roster (3,600-second native ceiling), followed by up to 32
deterministically chosen training-only rollouts (900 seconds). Raw and assisted
proof counts are separate; compare coverage and token/block costs and disclose
their different wall-time scopes. All conditions have at most 128 actions,
128 tokens per action and 16,384 total decision tokens. No reference action is
available to inference. Collected training encounters are not automatically
admitted correction labels or evidence that correction training has happened.

Actual Qwen validation 24729578 passed exact interrupted/resumed tensor,
optimizer, sampler, RNG and objective-history comparisons. The independent
source review and CPU/native controls cover narrower implementation contracts;
they do not establish improved proof quality. The main generator also requires
a matching-source gradient capacity receipt for the chosen context and batch.
All configuration and source digests are retained with the registered jobs.
