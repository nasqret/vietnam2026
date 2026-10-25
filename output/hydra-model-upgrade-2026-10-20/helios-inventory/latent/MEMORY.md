# Latent recurrent reasoning for Heyting arithmetic

## Mandate (2026-10-13)

Understand, decompose, reproduce at small scale, and extend arXiv:2502.05171 toward machine-checked Heyting arithmetic proofs. Compare recurrent depth against conventional transformers and investigate transfer from the existing Peano/Qwen work.

All experimental computation, training, model execution, numerical tests and document builds run on Helios or WMI through SLURM. The Mac is a control plane for source inspection, editing, Git and viewing artifacts. Never change another project's files or jobs.

Research is private. The requested deliverables are a local Git repository, a private GitHub repository, this memory, JOURNAL.md, PLAN.md, an Obsidian vault, a Jupyter Book and a genus-one-style labyrinth dashboard.

## Method

Use the installed labyrinth-exploration skill. Keep T1-T6 labels, independent review states, append-only events, source pins, resource receipts, and explicit open questions. Empirical benchmark results are T4, not mathematical theorems. A model-generated proof counts only after the designated constructive proof checker accepts it; standard Lean validity alone does not certify Heyting arithmetic.

## User decisions

First priority: small recurrent and ordinary transformers trained from scratch. The documentation is in English for professional researchers, with the mathematical and empirical standards of a leading ML conference. There is no deadline; access to WMI/Helios is the practical resource constraint.

The user subsequently authorized heavier training on both clusters, including a native entropy-informed stopping policy and a live comparison dashboard. Campaign 2 retains six arms and three paired seeds. The bounded workers reserve at most 36 GPU allocation hours in total; they do not replenish themselves.

## Active campaign 2

WMI **285005** and Helios **24643736** are running immutable `releases/campaign2-v2` sources. WMI executes seeds 11/47 and Helios seed 29, all six arms per seed. The 14.3M parameter arms are conventional pre-norm, sandwich-norm, fixed recurrence, randomized recurrence and native learned halting; the deeper conventional control has 34.2M parameters. Each receives up to 6,000 updates of effective batch 32. Native training evaluates all depths with full BPTT; inference can exit at depths 2–8. Entropy, KL and depth inform the gate; confidence is not a correctness certificate.

Full admission **285001** replayed 29,305 complete synthetic train/validation sessions through the source-bound constructive Python kernel, retaining 56,006 training and 6,948 validation actions. All 8,494 catalog training rows are excluded. No whole-session length or train/validation overlap exclusions were needed. This is not a new native Lean replay. Test bytes were hashed but records were not parsed. Templates overlap across train/validation, so this campaign does not measure template-disjoint generalization.

Independent finite validation passed 62 tests in WMI 285002/285004 and Helios 24642987. Both GPU smokes completed conventional/random/native four-update runs; WMI metadata resume audits and a full-context memory profile also passed. These are T4 checks, not proof of optimizer/RNG-equivalent resume or model superiority. The first native run is learning and shifting mass toward minimum depth two; results remain provisional until the paired comparisons finish.

Live URL: `http://127.0.0.1:8766/dashboard/training/index.html`. `bash scripts/preview_campaign2.sh` reconnects the SSH transport. The WMI aggregator reads localhost metadata services on both clusters; disconnecting the laptop affects preview, not training. Canonical protocol: `research/campaign2-protocol.md`; independent review: `research/agents/referee/campaign2/`. All checkpoints remain remote and ignored by Git.

At 14:59 UTC, six conditions had completed and both workers were still running. The first native and conventional seed11 models each matched 14/16 development actions; native training mass concentrated near minimum depth two. These small shared-template measurements do not establish a recurrence advantage. WMI 285010 passed the complete-history dashboard/service contracts, with separate native Firefox inspection. Candidate action-receipt validation 285011 passed 19 literal decoding/termination checks; native action replay, frozen test generation and the historical Qwen comparison remain pending.

## Current evidence — 2026-10-13

The paper v2, official code and Peano sources are pinned in `sources/manifest.json`. The official code is a later reference tree, not a recovered historical training tree. The book derives shared-depth recurrence, truncated gradients, parameter/depth accounting and the constructive proof boundary. Source and implementation reports received independent agent review; human review remains pending.

WMI pilot **284986** completed six models (three architectures, seeds 11 and 29) on one RTX 4090 in an allocation lasting **89 seconds**. Models have 115,072 recurrent, 114,944 parameter-control and 212,480 depth-control parameters. Training is equal-token/equal-update, not equal-FLOP. The task is a single closed-addition certificate template, not general HA proof search.

For the 35 IID targets per seed, recurrent acceptance is 12/70 pooled at one step and 10/70 at each of 2, 4, 8 and 16 steps. The parameter and depth controls obtain 7/70 and 8/70 respectively. All configurations obtain 0/64 per seed on the held-out right-operand split b=8..11, which also requires longer certificates. Neither a general recurrent advantage nor pure proof-length extrapolation has been established. Higher-depth predictions still differ despite equal acceptance counts; no convergence claim follows.

Validation **284987** preserves 79 passing tests (no skips), 64 accepted fixture certificates and 128 rejected mutations, source/executable hashes and native transcripts. Independent audit **284990** passed over all 1,834 predictions, replaying 1,826 well-formed certificates and recounting 81 accepted instances across configurations. It checks saved outputs and certificates, not checkpoint regeneration or retraining. Inputs were unchanged during the audit. Results remain T4.

Strict Jupyter Book build **284989** passed with both notebooks executed and structural artifact checks. A first build **284988** failed because an Agg backend suppressed notebook plot output; the corrected inline backend is retained. Final documentation refresh and delivery state are recorded in `status/project_status.json` and the journal.

## Operational state

- Local root: `/Users/airbartek/codex/latent`; local Git metadata: `.local-git`, via `scripts/git.sh`.
- Private remote: `https://github.com/nasqret/latent`; never enable public Pages or deployment implicitly.
- Initial package commit `50b369236c9da22847040ac0f6f4ec636e15a5d7` was pushed and read back from `main`; private visibility was verified live. Later delivery receipts are in the Git history and status file.
- WMI root: `/home/bnaskrecki/latent`; `.venv` inherits the central PyTorch environment read-only. Lean is pinned to v4.31.0.
- Pilot checkpoints: `artifacts/runs/284986/<model>-seed<seed>/model.pt` on WMI; hashes are tracked, weights are ignored by Git.
- The initial Helios probe was blocked by 999,998 / 1,000,000 scratch files. The later 2026-10-13 probe found 774,916 files and 396.18 GiB / 12 TiB, allowing campaign 2. Its root is `/net/scratch/hscra/plgrid/plgnasqret/latent`, grant `plgccaiautore2026-gpu-gh200`; the GH200 site container is used read-only. Never delete other projects' data.
- Main records: `artifacts/runs/284986/summary.json`, `artifacts/reviews/284990/audit.json`, `artifacts/receipts/sacct-through-audit.psv`, `research/REVIEW_INTEGRATION.md`.
- Generated views: `labyrinth/dashboard/index.html`, `obsidian-vault/Home.md`, `artifacts/site/book/index.html`. Rebuild only through SLURM.

## Next research decision

Finish campaign 2, freeze checkpoints and stopping policies, then independently validate held-out evaluation. Candidate freezer, generated-action replay and historical Qwen comparison tools are under `research/agents/peano/campaign2/`; do not present unexecuted candidates as measurements. Historical Qwen used different prompts/tokenization/capacity and part of the validation corpus, so it is a reference rather than a fresh holdout baseline. Full autonomous proof search, a native Lean bridge for these tactics, template-disjoint studies, warmed repeated timings and human review remain open. Keep Qwen distillation, Huginn adaptation and weight conversion as distinct paths.

## Qwen campaign 3 — 2026-10-14

The user authorized proceeding with the pretrained Qwen recurrence plan. Main
initialization is Qwen3-1.7B-Base revision
`ea980cb0a6c2ae4b936e82123acc929f1cec04c1`, not the historically exposed Peano
adapter. Four arms at paired seeds 11/29: ordinary LoRA, fixed four-pass,
random depth 1/2/4, and native entropy/KL/depth stopping. Retain the original
8/12/8 layer partition and one-pass function. Extra core-layer calls use learned
bounded damping initialized at 0.1; this is a retrofit, not Huginn pretraining.
Rank32 LoRA trains 34,865,152 parameters; recurrence adds 12 damping scalars and
adaptive stopping adds 81 gate parameters. All training is remote SLURM.

Data: WMI285064 retained all56,006 train/6,948 validation actions; new Qwen BPE,
no target truncation, no BOS, exactly one terminal EOS and one label shift.
Prepared data reside at `data/processed/campaign3-285064` on both clusters.
Maximum sequence/action-with-EOS lengths are450/45. Online128 teacher-forced,
32 generated-action and16 autonomous proof-target selections are fixed; test
labels remain unopened. Python-kernel proof acceptance and native Lean replay
are separate. Reference-oracle fixtures never count as model successes.

Preflight: Helios24675907 passed56 model tests and actual1.7B gradient/profile
checks; WMI285064 passed75 tests. WMI285065 passed106 tests and four real trainer
smokes, but exact resume audit285067 failed after the second backward/update.
Strict deterministic mode exposed an unsupported cumprod-backward cumsum in
WMI PyTorch2.5.1; halting weights now use explicit survival products. Preserve
failed receipts and use the latest validated release. WMI285066 passed the full
native constructive evaluator fixture, with independent source/receipt review.
See `research/campaign3-protocol.md` and `status/project_status.json` for the
latest launch gates, immutable release, live worker IDs and completed evidence.

Campaign2: all18 runs completed6,000 updates (workers285005 and24643736 completed).
This is training completion, not a completed held-out or model-advantage claim.

Final release: `releases/campaign3-v2`, manifest SHA256
`79c1f07a80bd7e946654f269c7821b00dcab70ddbffe8adf3560e17b428aa9a8`.
WMI285072 andHelios24676117 each passed116 final-source GPU tests, exact
2-update resume (2,781 tensors,maxerror0), native-kernel fixtures and real
generated action/proof integration with explicit20-second partial coverage.
The bounded workers are running: WMI starts adaptive, Helios vanilla; four arms
per cluster,2,000 target updates each,16-hour allocations (32GPUh reserved).
The20-second fixtures are not learned proof results. Added phase tests285073
passed4/4. The actual dashboard and browser learning curve were inspected.

The independent reviewer accepted v2 for bounded development only. CPU 285074 additionally confirmed exact objective/auxiliary/ponder histories. Actual generated preflight outputs timed out without EOS: no model proof success. Both main workers passed step 150 by 13:59 UTC; use live metadata for current progress.

Snapshot 2026-10-14 19:15 UTC: WMI 285072 completed all four runs; Helios completed vanilla/random and continued fixed/adaptive. Six completed runs reached 2,000 updates. Each recorded final development suite reports 32 valid actions and 16 accepted autonomous Python-kernel proofs, with fixed depth 1 selected. Treat this tiny shared-template validation result separately from sealed-test improvement. Exact frozen source is archived in `artifacts/campaign3/campaign3-v2-source.zip`. Strict documentation job 285076 passed 31 checks and both executed notebooks.

Campaign4 authorized: replace the saturated easy validation condition with genuine dependency/branch/witness composition, audited structural splits and measured automation shortcuts. Preserve full model-v3 authority initially; no inference that long gold scripts are hard. Evaluate prior frozen Qwen checkpoints before matched harder training. Protocol and execution budget: research/campaign4-protocol.md. All numerical work remains remote SLURM.

Campaign 4 admission and headroom, 2026-10-14: final corpus has 393 targets,
21470 action rows and 274 distinct common dependency cores. Full model-v3
constructive authority remains available. WMI 285093 independently replayed
all 393 gold proofs; BPE 285092 retained every session, context 4096. Thirty-two
development targets represent 21 common cores; final test 48 is sealed during
training. Prior selected vanilla/adaptive checkpoints each proved 0/32, with
complete coverage and no deadlines; independent learned-output audit 285101
passed, including 64 accepted autonomous prefixes. Pilot 285098 completed 128
updates: vanilla 2/32 and adaptive 3/32, both fixed-depth-one inference;
independent native audits 285105/285118 passed. Paired analysis 285119 finds
one shared, one vanilla-only and two adaptive-only successes, all logic
dependencies. Neither pilot solves a branching or existential target.
Training seconds: 427.7/1352.6; development CE: 0.2522/0.2566.
Main 512-update comparison: WMI 285117 running; Helios 24682069 queued after
24676117. Four arms, two seeds and at most 32 allocated GPU-hours. Frozen
posttraining depth sweeps and the 48-target final test remain pending. All
reported outcomes are T4; no recurrence benefit, causal curriculum effect or
native Lean replay is established.

Latest operational observation, 2026-10-15 22:52 UTC (October 16 in Warsaw):
WMI 285117 completed all four 512-update runs and frozen final evaluations.
On 48 test targets: vanilla6; fixed6/7/4 at depths1/2/4; random5/5/5;
adaptive6/6/6 and learned stopping5. Selected adaptive checkpoint is448,
other WMI checkpoints512. These main outcomes await independent saved-proof
replay; no recurrence advantage is established. Helios24682069 failed after
the finalizer refused budget-limited fixed training. Vanilla/random completed
512 updates; fixed/adaptive stopped at385/290 under the7200-second training
limit. Helios vanilla selected448 scored8/48 test; remaining finalization
did not execute. No active training jobs. Preserve the stopped outcomes and
register recovery separately. Latest receipt and next steps are in
status/project_status.json and PLAN.md; local dashboard transport was restored.

Campaign5 now authorized for broad execution (2026-10-16). Protocol
research/campaign5-protocol.md records192GPUh/32CPUh finite ceiling, expanded
structurally fresh corpus, longer paired training, proof-based selection,
all-depth warmup, balanced sampling and separately labelled assisted inference.
GPU profiles285220(WMI)/24729089(Helios); live state belongs in status JSON and
the job ledger. No new model improvement or recurrence advantage established.

Campaign4 main WMI saved-output audit nowpassed285215(2026-10-16): all22
model/policy/dev/test suites, includingfull failedtrajectories, source/token and
checkpoint bindings. Countsunchanged; no modelregeneration orLeanreplay.
Review research/agents/c5_audit/campaign4-review.md. Helios remainspartial;
itsvanilla8/48 is receipt-verified only inthisaudit.

Campaign5 main launched2026-10-16: immutable campaign5-main-v1, manifest
858f8a7d23eafb83e08038028263dbc5bf9442e2c57238992251d9068cdac87a;
registration285255 and freeze285256. Helios training24730085/24730087/24730089
and dependent inference24730086/24730088/24730090 cover seeds11/29/47.
Each seed has32h training plus24h inference,1GH200/4CPU/96GiB. Twelve main
Qwen3-1.7B rank32-LoRA runs target2048 updates. Adaptive training starts with
512 all-depth updates, then learns entropy/KL/depth stopping. No full-parameter
pretraining or model advantage is claimed. Main caps168GPUh; total registered
campaign ceiling184/192GPUh, no automatic replenishment or scheduler requeue.

Prepared data are data/processed/campaign5-bpe-v2 on both clusters,6144context,
zero exclusions. Train2580 sessions(2048 base plus532 naming variants),
dev192/test384. Independent285246 checked all3156 saved bindings and freshly
replayed128 gold proofs. Preparation285252; actual-Qwen exact-resume24729578;
matching-source capacity24729889; independent registration review accepted.
Raw128dev/256test, assisted128dev and32train-only encounters are separate
queued phases. Corrections are not yet admitted or trained. WMI285228 remains
the old-C4-data2048-update duration control. Live state, exact pins, budgets
and job accounting are canonical in status/campaign5.json and its linked
artifacts. Never infer completion from a queued worker or a successful fixture.

Early duration development result independently replayed by WMI285260:
vanilla 7/32 at512 updates to11/32 at1024, with5 gained and1 lost target.
All32 were attempted at both checkpoints; all18 successful observations,
46 open prefixes and46 failed trajectories replayed. This is within-run,
old-data development progress under a2048-update cosine schedule, not a
recurrent or held-out advantage. Receipt and final scope are in
research/agents/c5_audit/duration-development-review.md. New main comparison
results remain pending. Reviewer requested CPU allowance is exhausted at8h.

First main worker24730085 started03:33:28UTC on2026-10-16; vanilla seed11
reached110/2048 at03:40UTC. Startup plan/release pins match registration.
Other main workers were still queued in that observation; use the live
dashboard for later progress. This is execution evidence, not model validation.

Status at 2026-10-16 06:25 UTC: all three main Helios workers run; raw and
assisted final inference jobs await dependencies. WMI duration vanilla has
completed 2048 updates; fixed control is running. New development counts
are provisional T4, not independently replayed: WMI vanilla14/32, main
random seed29 7/64 at512, main fixed seed47 7/64 at1024; main vanilla
seed11 2/64 at512 then0/64 at1024. Different seeds/checkpoints and corpora
preclude a recurrence advantage claim. See the dated observation and journal.

Status2026-10-16 08:28UTC: main vanilla seed11 complete at2048,9/64dev.
Fixed seed11 now715/2048 (4/64 at512); random seed29 final-checkpoint
evaluation active (14/64 at1024); fixed seed47 final-checkpoint evaluation
active (7/64 at1024). New results remain T4 under review. Main held-out
evaluations and adaptive arms pending. Both live feeds restored; active
WMI reverse relay is18769, preview PID150531. WMI duration fixed control
1745/2048,12/32 at1536 with selected inference depth1. See dated observation.

Random-depth methodological note: canonical LaTeX docs/latex/random-depth-recurrence.tex,
clean3-page and annotated4-page PDFs in output/pdf/. Independent source review
accepted final source0e8b29c38a6b673602cf20aca1170b4eb1d4c6b535671061ca3597f1983f43aa.
Helios24758437 compiled and checked both; every rendered page visually inspected.
Receipt status/random-depth-note.json. First build24741262 rejected an appendix
filename overflow; corrected outputs passed. This is source documentation,
not new empirical evidence. The annotation retains provisional T4 scope.

Latest results snapshot: 2026-10-17 08:09--08:11 UTC. All12 main runs and
both old-corpus duration controls completed2048updates. Main32/36online
probes complete;6primary evaluation suites available, only2complete(dev).
Available test V11=19/256,R29=24/256,F47=12/256 all hit5400s ceilings,
with142/117/145attempted. They do not form a paired comparison. Main random
beats vanilla at1024 in all3seeds; terminal complete results are mixed.
Independent Helios24771779 checks344frozen files and saved verdict/roster/
selection/cost consistency,1,880,897checks passed. No fresh native checker
replay, model regeneration, checkpoint tensor comparison or full-corpus rehash
in this audit. T4 remains; general recurrence advantage and human review open.
WMI fixed4training final16/32dev uses variable entropy0.15 inference, unlike
its first3depth1probes. Keep the two corpus/selection protocols separate.
Canonical report research/results-appendix.md; status/results-appendix.json
tracks the five-figure LaTeX appendix and its PDF build/delivery receipts.
Current PDFs contain7clean/8annotated pages. Helios24772007 passed all
automated and15page visual checks. WMI285329 completed the strict book,
vault and labyrinth projection with54artifact checks;285330 is registered
for the final canonical-record refresh. Native proof replay remains separate.
