# Hydra post-training and proof-development pipeline

Hydra is an untrusted search and orchestration layer around the existing
constructive Peano proof kernel. Its next product track is one bounded,
digest-bound workflow: freeze the current independently checked Alpha theorem
DAG and the separately reviewed conservative definition DAG, compare
independently replayed proof routes, check candidate discoveries against their
original statements, and export only kernel-verified transitions for future
language-model post-training.

Run the complete local development workflow from the repository root:

```console
make hydra-check
make hydra-prepare
make hydra-scale
make hydra-posttrain-ready
```

The preparation command writes its deterministic, development-only epoch,
supervised transitions, checked route preferences, candidate-discovery
receipts, and manifest under `_deploy/hydra/`. No model is trained, no theorem
is admitted to Alpha, and no public deployment is performed by this command.

The complete command without Make is:

```console
python3 scripts/prepare_peano_hydra.py \
  --output-dir _deploy/hydra \
  --include-graphs
```

Add `--check` to replay the whole pipeline without creating or modifying any
artifact. Repeated generation is byte-identical when the frozen release and
the checked source routes have not changed. The output directory contains:

- `epoch.json`: the exact selected release, full edition identity, separate
  theorem and reviewed-definition DAG identities, and optional complete DAGs.
- `sft.jsonl`: successful original-goal replay states, canonical complete
  tactic actions, parsed prompt/completion pairs, and checked lineage.
- `preferences.jsonl`: shorter-route preference pairs only when both complete
  alternatives have independently reached checked QED.
- `discovery.jsonl`: candidate proofs or honest `unknown` outcomes; checked
  candidates remain outside the admitted theorem catalog.
- `manifest.json`: exact file sizes and SHA-256 identities, lineage-separated
  train/development splits, proof-route evidence, and still-open claim gates.

Expand the post-training corpus deliberately without changing its authority:

```console
python3 scripts/prepare_peano_hydra.py \
  --output-dir _deploy/hydra \
  --include-graphs \
  --catalog-limit 32 \
  --catalog-theorem crt_product_witness
```

`--catalog-limit` independently replays up to **512** bounded authored proofs
from the current checked theorem DAG. Repeat `--catalog-theorem NAME` to
select particular checked Stable or Alpha results. Every selected theorem
receives exactly its strict earlier direct prerequisites, a fresh bounded
Hydra policy, a newly checked source replay, and a second original-goal kernel
replay. Routes above the current 32-decision search ceiling fail explicitly;
the command never silently truncates a proof or widens theorem authority.

For wider coverage, scan the entire frozen catalog while explicitly bounding
the number and size of routes:

```console
python3 scripts/prepare_peano_hydra.py \
  --output-dir _deploy/hydra \
  --include-graphs \
  --catalog-all \
  --catalog-limit 192 \
  --catalog-max-decisions 16
```

The complete Alpha-v25 census distinguishes **978 decision-eligible routes**
(**723 Alpha-only**, **255 Stable**), **818 statement-safe routes**
(**564 Alpha-only**, **254 Stable**), and **460 import-replay-safe routes**
(**260 Alpha-only**, **200 Stable**). Short tactic scripts alone are not
sufficient: automatic selection permits only memory-safe **Stable-only
prerequisite closures** of at most **256 tactic decisions** and **8,192
statement bytes**. It rejects expensive or Alpha-only prerequisites before
replay, bounds theorem statements to **4,096 bytes**, and enforces a
whole-run maximum of **512 routes**, **8,192 tactic decisions**, **512 KiB
retained evidence per route**, and **24 MiB aggregate retained evidence**.
Every excluded theorem receives an explicit reason; exclusion is not a
negative mathematical result.

The displayed 192-route, 16-decision command independently checks **192
catalog routes**, including **91 Alpha-only routes**, emits **1,798 verified
supervised transitions**, retains **one preference pair** and **one discovery
receipt**, and removes **40 duplicate transitions**. `make hydra-scale` uses
these same bounded defaults. These are verified corpus measurements, not a
claim that a language model has been trained or has solved these theorems.

The recorded-script policy first looks up the complete exact proof state. If
that state differs only because the engine compacted its internal `?tN`
metavariable numbers, it alpha-normalizes those identifiers by first visible
occurrence across the complete ordered goal tuple and retries. User variable
names, formulas, goal order, tactic text, theorem names, and checked
capability authority remain unchanged. The suggested tactic remains
untrusted, and the independent original-goal replay still decides whether the
proof is valid. This cosmetic proof-state normalization is not a theorem
equivalence or mathematical novelty claim.

When separately checked routes yield an identical training transition,
deduplication uses exactly this authority-preserving ordered key:

```text
(epoch_sha256, lineage_sha256, state_sha256, action, environment_sha256)
```

The first occurrence is retained deterministically. A matching key with
different before/after goals, focus, prompt, or completion fails closed
instead of silently merging conflicting evidence. Different frozen epochs,
lineages, proof states, actions, or execution authorities are never conflated.
The manifest exposes `duplicate_transitions_removed`; only complete,
independently checked original-goal proofs can contribute positive rows.

For current immutable Alpha v25, the exact `--catalog-limit 32`
`--catalog-theorem crt_product_witness` example independently checks **33
catalog routes**, emits **279 verified supervised transitions**, and reports
**2 duplicate transitions removed**. The built-in default remains a
**16-transition**, one-preference development pilot; neither run trains a
model, admits a theorem, or establishes a research claim.

## Quarantine frozen benchmark lineages before any model exposure

The historical model-v3 held-out contract remains binding even though the new
training surface is Alpha v25. Its four canonical goals are:

```text
closed_arithmetic_seven
existential_subtraction_two
double_right_zero
consecutive_product_even
```

The checked teacher example `triangular_product_even_hydra_candidate` is the
same canonical formula as `consecutive_product_even`; changing bound-variable
names or relabeling it as a discovery cannot turn it into training data.
The post-training handoff therefore matches theorem names **and canonical
first-order formulas**, then quarantines every matching proof lineage from
**both training and development**. Training-time evaluation, checkpoint
selection, and model-facing validation cannot see a held-out proof either.

The current full-scale **1,798-transition** source yields exactly **1,773
clean training rows**, **12 clean development rows**, and **13 quarantined
rows**. Its independent preflight derives **222 bounded optimizer steps**;
this is a checked potential schedule, not executed optimization. The
reproducible older **279-transition** source yields exactly **261 training
rows**, **5 development rows**, and **13 quarantined rows**. A
16-transition default pilot has only one clean remaining lineage and fails
closed because it cannot supply an independent clean development split.

The handoff's `quarantine.jsonl` contains only a theorem name, lineage digest,
statement digest, excluded-row count, and reason. It contains **no proof
statement, tactic, trace, prompt, or completion**. `preferences.jsonl` and
`discovery.jsonl` remain separately identified provenance; the supervised
training runner reads **only** `train.jsonl` and `dev.jsonl`.

## Prepare an Alpha-specific model handoff without starting training

After scaling the verified source, produce a separate bounded handoff:

```console
python3 scripts/prepare_peano_hydra_posttrain.py \
  --source-dir _deploy/hydra \
  --output-dir _deploy/hydra-posttrain

python3 -m training.peano_hydra.posttrain \
  --preflight \
  --preparation-dir _deploy/hydra-posttrain

python3 scripts/eval_peano_hydra_posttrain.py \
  --preparation-dir _deploy/hydra-posttrain \
  --check

python3 scripts/eval_peano_hydra_posttrain.py \
  --preparation-dir _deploy/hydra-posttrain \
  --check --symbolic-controls
```

The equivalent individual targets are `make hydra-posttrain-prepare`,
`make hydra-posttrain-preflight`, `make hydra-eval-plan`, and
`make hydra-eval-control`;
`make hydra-posttrain-ready` first scales the source and then performs all
three preparation checks followed by the model-free symbolic control in the
required order. Adding `--check` to the preparation script verifies its
evidence without publishing a handoff.

The independently replayed fixed symbolic control currently proves **3 of 4
held-out goals**: `closed_arithmetic_seven` uses **98 proof nodes**,
`existential_subtraction_two` uses **29 proof nodes**, and
`double_right_zero` uses **10 proof nodes**. The induction-dependent
`consecutive_product_even` remains **unknown**, not disproved. All four runs
have **zero theorem imports** and **zero model calls**. They are never
reported as pretrained or Alpha-trained inference results.

The post-training manifest binds the exact Alpha epoch and edition, both
mathematical DAG hashes, source file hashes, canonical benchmark contract,
separate clean lineage splits, and the pinned
`Qwen/Qwen3-1.7B-Base` model revision. Its preparation status remains
`model_trained: false`, `research_claim_eligible: false`,
`sealed_benchmark: false`, and `alpha_admitted: false`. Neither preflight nor
the evaluation plan loads model weights, schedules a remote job, trains a
model, admits a theorem, or deploys a website.

Actual GPU training is a separately authorized operation:

```console
PYTHONHASHSEED=20260826 python3 -m training.peano_hydra.posttrain \
  --execute \
  --preparation-dir _deploy/hydra-posttrain
```

The hash seed must be set before the Python interpreter starts; the Makefile
and scheduled job entry points set it automatically. The executor must reject
a missing CUDA device, unavailable pinned weights,
changed source bytes, held-out leakage, incompatible epoch, unbounded
examples, or an existing result it cannot safely authenticate. It never
retrofits the historical 247-theorem adapter with undeclared Alpha authority.

A fair eventual evaluation compares the exact pretrained base with the new
Alpha-trained adapter under identical theorem statements, frozen Alpha
authority, allowed tactics/theorems, generation settings, search budgets, and
authenticated provider evidence. Without the trained adapter and actual
provider/model-call receipts the report is **planned/not-run**; deterministic
symbolic controls prove the plumbing only and never become model scores.

## Optional guarded Helios execution requires explicit authorization

The prepared cluster chain has three separate, resource-bounded jobs:

```text
slurm/peano_hydra_alpha_prepare.sbatch    CPU, 30 minutes
slurm/peano_hydra_alpha_train.sbatch      one GH200, 2 hours
slurm/peano_hydra_alpha_evaluate.sbatch   one GH200, 1 hour
```

The CPU job uses native `Python/3.11.5` on the x86-64 CPU partition and creates
and rechecks the isolated Alpha source/handoff before any GPU allocation. It
does not use the ARM-only `.venv-helios` environment reserved for GH200 jobs.
The training job can be submitted only with `--afterok` on
that exact successful preparation job. The evaluation job, in turn, requires
`--afterok` on that exact successful training job and invokes actual models
only through `--execute-models --trained-adapter`.

Every stage independently refuses dirty or uncommitted source provenance.
The GPU stages require the reviewed pinned offline model cache. Training
verifies the installed package versions against the selected site lock before
loading weights and records the runtime, source commit, and scheduler ledger
entry with the completed adapter. A real Slurm submission
additionally requires both `--submit` and the independently checked
`--confirm` authorization. `make hydra-posttrain-ready`, preflight, symbolic
controls, and this documentation **do not submit any job, start training, or
allocate a GPU**.

Source synchronization refuses to run while jobs use the Peano project. It
preserves the installed GPU environment, cached model weights, historical
results, logs, and browser vendor assets, and excludes local Git metadata
(including linked-worktree pointer files), agent state, and Python caches.

The built-in optimization independently checks a five-tactic `zero_add` route
and a three-tactic route to the same original theorem. It records the two
saved tactic decisions without asserting global optimality. The candidate
demonstration independently replays the existing 13-tactic, 180-node
triangular-evenness teacher artifact and clearly identifies it as
`teacher_oracle_plumbing`, not as a model-generated mathematical discovery.

Whole-run model-call, proof-state, candidate, route, prompt, and output bounds
are checked before work can exceed their reviewed reservations. Optimization
may import only strictly earlier checked theorems, so importing its own target
or a descendant cannot masquerade as an improved proof. Candidate dependencies
must exactly match their finite theorem allowlist. Unsuccessful search states
never become positive training rows, and related theorem-DAG components never
straddle the train/development split.

The default public tactic surface and the historical frozen 247-theorem Qwen
adapter remain unchanged. An Alpha-aware Hydra run must explicitly identify
the exact sealed release with its complete SHA-256 edition identity and must
declare finite tactic and theorem allowlists. Every accepted candidate is
replayed independently by the original kernel. An exhausted search is
`unknown`, not a disproof.

These artifacts are preparation evidence rather than a sealed benchmark.
They do not establish optimal proof lengths, semantic mathematical novelty,
model capability, or an LLM advantage; the experimental H0/H1 gates remain
open until their separate reviewed protocols and evidence are complete.

The intended next implementation remains a single line: collect more bounded
independently checked proof routes under a freshly sealed epoch, expand this
verified curriculum, post-train a separately attested model against that
exact authority, and only then compare it with matched symbolic/model-free
controls on an independently sealed unseen benchmark. Any future Alpha
admission, public publication, or research claim remains its own reviewed
operation.

See the single active [Hydra product roadmap](HYDRA_PRODUCT_ROADMAP.md) for
sequencing and the
[formal experimental design](PEANO_HYDRA_DESIGN.md) for research-claim gates.
