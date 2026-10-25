# Isolated Hydra decision training package

This is a working copy of the deployed, attested v4 training stack. It does not
replace the historical `training` namespace, saved adapter, or frozen execution
trees. `BASELINE.json` records all 122 copied files, original hashes, and the
sole import-namespace rewrite to `hydra_training_v5`. New admission and pilot
entry points are separate from the preserved historical launch contracts.

Nothing is trained by importing this package or writing its configurations.
Actual data/fit/GPU results belong to their separately observed run receipts.

## Data and authority

`../export_decisions.py` requires an explicit hashed input specification and a
fresh output directory. `configs/decision-inputs-v1.json` selects the two P0
eight-case runs, one existing checked Vampire contradiction, one checked
Pythagorean proof, and six original TRAIN retention families. Its SHA-256 is
`f21200dadbfae992a1fbb4095d724864ee1fefeae7104920aa2275fef14b6c07`.
The files are project-owned exposed diagnostics, not an unseen benchmark.
Website jobs require explicit opt-in and are absent from this specification.

The output separates:

- `primitive-{train,val,test}.jsonl`: only full checked winning continuations
  or preserved checked TRAIN transitions, with the exact primitive-v4 prompt.
- `ranker-{train,val,test}.jsonl`: observed remaining steps along complete
  checked continuations. This is neither a shortest-proof claim nor a theorem
  truth label. Earlier per-state certificate costs are null when not recorded.
- `native-attempts.jsonl` and `action-preferences.jsonl`: native rejections and
  matched whole-state decisions; these never become positive tactic SFT.
- `outcomes.jsonl`: limits, omissions and missing snapshots stay explicit.
  Resource stops and unfinished alternatives are censored, not false theorems.
- `manifest.json`: exact source/result pins, selection, family components,
  exclusions, tactic coverage and file hashes.

The frozen prospective reservation SHA is
`2a57f12ffe55f90c3c4ac896fba3c2bab47e795b6bb5ba5f15b2c6854cddb58e`.
The exporter checks closed native AST identities, whole-goal targets and
assumptions, and declared underscore family/template labels. It reserves whole
statement/template components before splitting and drops states whose exclusion
identity cannot be checked, such as unresolved textual metas. This is bounded
structural exclusion, not exhaustive semantic equivalence or pretraining
independence. The input specification keeps historical DEV/TEST rows out of
future training; newly assigned validation/test families come from original
TRAIN and remain explicitly exposed in historical-model comparisons.

The primitive exporter deliberately refuses structured-planner datasets and
library imports. P4 JSON plans require their own versioned prompt/target rows;
they are never inserted into historical primitive completions. Current SFT
coverage for `suffices`/`ring` comes from the recorded cubic/Pythagorean proofs;
`exfalso` comes from the recorded contradiction proof. Actual selected counts
must be read from the export manifest.

## Optional ranker

`../branch_ranker.py` is a small one-pass linear predictor over all outstanding
goals, depth and available partial-certificate costs. Its features have explicit
missingness flags. It fits at most 4,096 checked training rows, with a 20-second
soft ceiling; no fit runs on import or export. The parent experiment guard owns
hard wall/RSS limits. Native rejection preferences are separate future action
data and are not used to fabricate branch-distance targets.

Load a fitted artifact with `load_ranker(path, expected_sha256=...)`. Its callback
is `callback(all_goals=..., depth=..., proof_cost=None, remaining_budget=None)`.
A smaller scalar is preferred. The search owner keeps continuation priorities,
oldest-first fairness, resource budgets and independent proof replay. Supply
only the current partial state's cost, never a future final-proof cost. This
component is not enabled by importing it; promotion requires a measured paired
search comparison.

## Fresh pilot preparation

Add this directory to Python's module path to import `hydra_training_v5`.
`decision_data.attest_decision_dataset` rehashes the export and its inputs and
regenerates its bytes before admitting examples. This repeats exclusion parsing
and source validation, not historical native proof checks. It reuses the copied
v4 `ProofExample` contract and keeps the old replay-compiler attestor untouched.

The completed P5 export is `output/hydra-implementation-2026-09-04/decisions-v1-02/manifest.json`,
SHA-256 `6ffc5d54678bbe43cdbf7178b4fd6d8493f661ba437526d36d4278111ad8f930`.
It contains 2,047 training rows, 432 validation rows and 624 test rows. The
observed export/fit process receipts are in `p5-data-gate-02`; the separately
fitted ranker has 79 training rows and no held-out distance rows. Neither these
counts nor its training loss establish improved search quality.

`decision_pilot.prepare(config_path, dataset_manifest=..., dataset_sha256=...)`
returns an immutable plan binding the dataset, exact row populations, model,
schedule and source files. `tokenize(plan, ...)` is a separately scheduled local
tokenizer operation that refuses overflow rather than dropping rows. Compare
1.7B/4B token preflights on identical selected row IDs before either training
job. Per-model token counts are recorded; equal examples are not equal FLOPs.

For a scheduled model smoke, `probe_completion_gradients(plan, model=...,
tokenizer=..., model_identity=session.identity, max_examples=8, max_seconds=120,
disposable_model=True)` performs at most eight forward/backward microbatches
from that exact admitted training split. The model must be the authenticated,
unadapted P6 base. This last-use operation adds fresh LoRA and checkpointing;
the caller must discard the session even after failure. It creates no optimizer,
saves no adapter, and verifies unchanged trainable tensor bytes. Results retain
actual examples, completion tokens, gradient checks and timing; exceptions carry
`probe_record` with partial counts. The caller enforces the hard allocation
limit. It is a throughput estimate, not a training run or a quality evaluation.

`decision_pilot.execute` is an explicit future GPU operation with a live
reservation checker, exact token-preflight hash and cancellation boundary. It
reuses v4 completion-only indexed logits, collation, finite-gradient audit,
adapter-update fingerprints and safe artifact publication. Only one complete
epoch counts as trained. A fresh output is mandatory, resumption is disabled,
and a failure leaves an incomplete attempt. P6 must independently admit a saved
adapter reload before inference; a completed training manifest alone does not
claim inference readiness or improved proof success.

The three prepared TOML configurations use fresh pinned 1.7B, 4B and 8B bases,
the same data and optimizer exposure, at most 4,096 rows, LoRA rank16/alpha32,
batch1/accumulation8, BF16/SDPA and no resume. Registry extensions are explicit
in `pilot_config.py`, not mutations of the copied historical allowlist. The 8B
revision was checked against the primary Hugging Face metadata receipt under
`output/p6-prototype/metadata/qwen3-8b-api.json`; no weights were fetched by P5.

Run 1.7B/4B first. 8B training follows its provider smoke and the remaining
campaign budget; its prepared config is not an allocation. Each job is limited
to one GH200, eight CPUs, 64GiB and two hours; all pilots/probes/evaluation and
distillation share the six-GH200-hour campaign ceiling enforced by the job
orchestrator. No automatic retries, sweeps, silent model substitution or
continuous self-training are included.
