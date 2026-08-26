# Peano Hydra research execution

Peano Hydra is an **untrusted proof-search orchestrator**, not a second proof
kernel. Symbolic tactics, recorded teachers, language models, and future solver
adapters can suggest candidate moves. A theorem is accepted only after the
existing Peano kernel checks the original statement; `run_hydra` additionally
replays every successful command sequence in a fresh traced session.

The first Alpha-v25 Qwen run is now executed: **222 optimizer steps** on
**1,773 training rows**, followed by an actual pretrained **0/4** versus
trained **3/4** diagnostic comparison. All three learned proofs independently
replay. The fixed symbolic control also scores **3/4**, so this is not an
LLM-advantage result. See the
[run report and replay instructions](../../artifacts/peano-hydra/alpha-v25-posttrain-2026-08-26/README.md).

The subsequent model-free DEV stage measures **16/64 closure** versus **48/64
generic symbolic portfolio** successes. Its separate historical cohort is
**2/4** versus **3/4**. These native-only lanes have narrower authority than
the old Alpha run; the scores are not evidence of model advantage or a
regression against its symbolic control. See the
[DEV guide](../../docs/HYDRA_DEVELOPMENT_EVALUATION.md) and
[archived results](../../artifacts/peano-hydra/development-2026-08-27/README.md).

## One current product workflow

Run the integrated local checks and prepare deterministic proof-development
artifacts from the repository root:

```console
make hydra-check
make hydra-prepare
make hydra-scale
make hydra-posttrain-ready
```

`training.peano_hydra.epoch.freeze_epoch()` selects the current Alpha release
from the canonical campaign, authenticates its exact sealed theorem catalog,
checks the immutable 432-theorem Stable parent, and separately authenticates
the hygienically reviewed conservative definition DAG. Proof dependencies,
definition dependencies, milestone-planning edges, and display-notation edges
remain different evidence types. A new prospective source file or partially
generated release never enlarges the active epoch.

The default Peano surface remains Stable-only. Explicit Alpha access requires
the complete label `hydra-alpha-vN-<64-hex-edition-identity>` together with
finite tactic and theorem allowlists; every imported theorem is independently
replayed against its exact original formula. A proof-improvement route can
import only strict earlier checked theorems, never the target or a descendant.

`training.peano_hydra.development` compares bounded independently checked
routes and checks unadmitted candidate discoveries. The demonstration
shortens a checked `zero_add` proof from five public tactic decisions to three
and independently reconstructs the reviewed 13-decision, 180-node triangular
evenness teacher route. `training.peano_hydra.curriculum` then exports only
complete-QED transitions and separately checked shorter-route preferences:

```text
_deploy/hydra/epoch.json
_deploy/hydra/sft.jsonl
_deploy/hydra/preferences.jsonl
_deploy/hydra/discovery.jsonl
_deploy/hydra/manifest.json
```

Use `python3 scripts/prepare_peano_hydra.py --catalog-limit 32` to extend the
same verified curriculum with bounded, independently replayed checked-catalog
proofs, or repeat `--catalog-theorem NAME` for explicit Stable/Alpha targets.
Each target receives only its strict earlier direct proof prerequisites.

Use `--catalog-all` to census the entire immutable Alpha-v25 DAG and sample
both checked Stable and Alpha-only routes without losing memory bounds:

```console
python3 scripts/prepare_peano_hydra.py \
  --output-dir _deploy/hydra \
  --include-graphs \
  --catalog-all \
  --catalog-limit 192 \
  --catalog-max-decisions 16
```

The full catalog contains **978 decision-eligible routes** (**723 Alpha-only**
and **255 Stable**), **818 statement-safe routes** (**564 Alpha-only** and
**254 Stable**), and **460 replay-safe routes** (**260 Alpha-only** and
**200 Stable**). Whole-catalog selection accepts at most **512 routes** and
only bounded **Stable-only prerequisite closures**; its other explicit limits
are **32 decisions per route**, **256 prerequisite tactic decisions**, **4,096
statement bytes**, **8,192 prerequisite statement bytes**, **8,192 whole-run
tactic decisions**, **512 KiB evidence per route**, and **24 MiB total retained
evidence**. The displayed command actually checks **192 routes**, including
**91 Alpha-only routes**, and yields **1,798 supervised transitions** with
**40 duplicates removed**. The earlier 33-route example remains **279
verified transitions** with **2 duplicates removed**.

The existing post-training handoff is separate from proof-curriculum generation:

```console
make hydra-posttrain-prepare
make hydra-posttrain-preflight
make hydra-eval-plan
make hydra-eval-control
```

`make hydra-posttrain-ready` first generates the scaled source and then runs
the preparation, preflight, and `--check --symbolic-controls` stages; it
never starts CUDA or submits a job. The runner reads only
`_deploy/hydra-posttrain/train.jsonl`
and `_deploy/hydra-posttrain/dev.jsonl`. It canonicalizes all four historical
held-out goals and quarantines a matching **entire lineage from both training
and development**. In particular,
`triangular_product_even_hydra_candidate` is the same formula as the held-out
`consecutive_product_even`: its 13 rows cannot enter either model-facing
split. Relative to that original quarantine, the verified 192-route source
yields **1,773 training rows**, **12 development rows**, and **13 quarantined
rows** from its **1,798 total rows**; preflight derives **222 bounded optimizer steps** without
initializing CUDA. The older 279-row source therefore yields **261 training**, **5
development**, and **13 quarantined rows**. The isolated quarantine receipt
has no proof statement, prompt, completion, tactic, or trace. The default
16-row pilot correctly fails because only one clean lineage remains.

`--preflight` and evaluation `--check` do not train a model or invent a
pretrained-versus-trained result. Actual CUDA training requires the separately
requested `make hydra-posttrain-execute`, which sets `PYTHONHASHSEED=20260826`
before starting the interpreter and invokes the runner's explicit `--execute`
mode. Missing adapter/provider evidence
leaves the matched evaluation **planned/not-run**; H0 and H1 remain open.

The actual `make hydra-eval-control` result is **3 of 4 checked goals**:
the first three require **98**, **29**, and **10 proof nodes**; the fourth,
induction-dependent goal remains **unknown**. All lanes use **zero theorem
imports** and **zero model calls**, so none is language-model evidence.

Optional Helios execution is separated into
`slurm/peano_hydra_alpha_prepare.sbatch` (**30-minute CPU**),
`slurm/peano_hydra_alpha_train.sbatch` (**2-hour GH200**), and
`slurm/peano_hydra_alpha_evaluate.sbatch` (**1-hour GH200**). Training and
evaluation demand the exact clean-source `--afterok` predecessor; every stage
requires clean committed source, and GPU stages require the pinned offline
model cache. Real
submission needs a separately authorized `--submit --confirm` operation.
No local preparation or readiness command submits these jobs automatically.
`bash scripts/helios_hydra_chain.sh --test-only` checks the three requests;
its explicit `--submit --confirm PEANO-LAB-TRAINING` mode checks matching
clean local/remote source and immediately queues the success-dependent chain.
This avoids losing predecessor IDs under Helios's short controller retention.

These reproducible development artifacts do not train a model, admit a
theorem, assert semantic novelty or globally minimal proofs, or establish an
LLM advantage. The single current development track is documented in
[`docs/HYDRA_PRODUCT_ROADMAP.md`](../../docs/HYDRA_PRODUCT_ROADMAP.md) and
[`docs/HYDRA_POST_TRAINING.md`](../../docs/HYDRA_POST_TRAINING.md).

## Completed experiment and larger named preparation

Helios jobs **21279955 → 21279969 → 21280018** completed preparation,
training, and matched evaluation from clean commit `a4ed2481`. All **222**
update boundaries had finite gradients; **392 trainable tensors** changed.
Local kernel replay reproduced the model's three successful traces and their
**98**, **29**, and **21 proof nodes** exactly, without importing Torch.
The base rejected all 16 candidate sequences as malformed; the trained model
emitted 88 valid candidate lines. Its improvement therefore measures use of
the strict tactic interface, not broad mathematical superiority. Actual
model calls were **4** versus **22**, despite identical search limits.
`consecutive_product_even` remains unknown; the symbolic control is still
as successful and proves `double_right_zero` more cheaply.

The next corpus has already independently checked **460** routes, including
**260 Alpha-only**, yielding **7,154 transitions** with **90 duplicates
removed**. The separate `catalog-460` handoff under
`_deploy/hydra-posttrain-next` has **7,129 training / 12 development / 13
quarantined rows** and **892 planned optimizer steps**. It is **prepared,
not trained**; the validation theorem has not grown with the training set.
Use the [named-run preparation commands](../../docs/HYDRA_POST_TRAINING.md#completed-model-run-and-the-next-isolated-curriculum)
to reproduce it without replacing the completed run.

An explicit `--run-id` selects a distinct adapter name and, when no output
directory is given, `_deploy/hydra-posttrain-<run-id>`. The publisher refuses
to replace another preparation identity or changed manifest evidence; only
byte-identical regeneration is allowed. Training and evaluation select a
run through its authenticated `--preparation-dir`. The standard Slurm chain
still selects the 192-route default; it does not implicitly consume a named
local handoff. Neither preparation is an unseen training counterpart to the
new DEV goals: the exposure audit below blocks both.

## Model-free development evidence

The completed `_deploy/hydra-development-v1` run uses the bounded native
`hydra-development-no-imports-v1` authority. It makes **zero model/solver
calls, theorem imports, and retrieval requests**. The Alpha-v25 epoch is
bound separately for catalog/lineage metadata, not granted as worker import
authority.

| Cohort | Closure | Generic symbolic portfolio |
| --- | --- | --- |
| 64 expanded DEV goals | 16/64 | 48/64 |
| Four historical diagnostics, separate | 2/4 | 3/4 |

Independent verification checked the deterministic proposals in **130
completed worker rows** and freshly kernel-replayed **69 positive proofs**
(18 closure, 51 portfolio). Six of the 136 workers, all in the portfolio,
exited at the **three-CPU-second guard** (`SIGXCPU`); they remain unknown,
not failures of the mathematical statement. Their unavailable resource
counters stay null, so completed-worker measurements are not whole-run CPU
or peak-memory totals. The hard consecutive-product goal remains unknown.

The eight declared families all join **one declared lineage component with 2,048
catalog members**. The original preparation's **175 exposed training roots**
and `catalog-460`'s **436** intersect that component: all eight families are
**blocked for unseen-model comparison**. These 64 goals are not 64 independent
lineages. The
[DEV guide](../../docs/HYDRA_DEVELOPMENT_EVALUATION.md) explains planning,
bounded execution, and independent verification; the
[archive](../../artifacts/peano-hydra/development-2026-08-27/README.md) preserves
the measured evidence.

The [native DEV protocol](../../docs/HYDRA_DEVELOPMENT_PROTOCOL.md) now
implements typed `Use`, `Cut`, `Witness`, `Induct`, `Rewrite`, `Split`, and
`Dispatch`, with source-bound limits and atomic public-tactic execution.
This does not close the full H0.3 protocol or its reference/conformance gates.
The **single next milestone** is reviewed model-facing **TRAIN/DEV lineage
separation together with the required H0 semantic/reference checks, before
any further GPU comparison**. Do not train `catalog-460` and label this DEV
cohort unseen. The historical 247-theorem adapter remains unchanged.

## Historical teacher-oracle regression

Run the provider-neutral teacher-oracle regression from the repository root:

```console
python3 scripts/eval_peano_hydra.py --compact
```

The fixed symbolic control exhausts; a recorded structural teacher reconstructs
a 13-command, 180-node independently checked proof. A related altered theorem
does not activate the recorded transcript. This demonstrates checked routing,
not Qwen capability, a strong-symbolic-baseline comparison, or an LLM advantage.

Persistent prefix snapshots reduce this three-lane regression from 240
root-replayed tactic executions to 39 single-edge executions. Snapshots retain
only immutable proof state, replay steps, and metavariable aliases. Each new
edge receives its own fresh session and trace logger; theorem, command prefix,
canonical goals, logic mode, and surface capabilities are checked before reuse.

## Dependency-aware bounded execution

`training.peano_hydra.scheduler.run_campaign` evaluates independent theorem
goals concurrently and releases later goals only after every prerequisite has
an independently kernel-checked proof. Each goal receives a fresh policy
instance and its own exact execution authority.

```python
from peano_lab.ui.prove import SurfaceCapabilities
from training.peano_hydra.policy import (
    FixedCandidatePolicy,
    HydraCandidatePolicy,
    PolicyHead,
)
from training.peano_hydra.runner import policy_environment
from training.peano_hydra.scheduler import CampaignGoal, CampaignLimits, run_campaign
from training.peano_policy.search import SearchLimits

capabilities = SurfaceCapabilities(
    label="constructive-campaign-example",
    allowed_commands=frozenset({"refl"}),
    allowed_theorems=frozenset(),
)


def fresh_symbolic_policy():
    symbolic = FixedCandidatePolicy(
        ("refl",),
        name="bounded-reflexivity",
        policy_environment=policy_environment(capabilities),
        provider_identity={"kind": "fixed-symbolic-reflexivity"},
    )
    return HydraCandidatePolicy(
        (PolicyHead("symbolic", "symbolic", 1, symbolic),),
        name="constructive-campaign-reflexivity",
    )


goal_limits = SearchLimits(
    max_depth=1,
    beam_width=1,
    candidates_per_state=1,
    max_model_calls=1,
    max_states=1,
)
goals = (
    CampaignGoal("foundation_a", "0 = 0", capabilities, fresh_symbolic_policy,
                 limits=goal_limits),
    CampaignGoal("foundation_b", "1 = 1", capabilities, fresh_symbolic_policy,
                 limits=goal_limits),
    CampaignGoal("summit", "2 = 2", capabilities, fresh_symbolic_policy,
                 dependencies=("foundation_a", "foundation_b"),
                 limits=goal_limits),
)
result = run_campaign(goals, limits=CampaignLimits(max_workers=2))
assert result.proved_goals == 3
assert result.waves == 2
```

Before creating any worker, the scheduler rejects duplicate or missing goal
identifiers, cyclic dependencies, unsafe or open formulas, and campaigns whose
combined worst-case model-call, proof-state, or tactic-candidate reservations
exceed their declared global budgets. A failed prerequisite blocks its
descendants without invoking their policy factories. Reports preserve goal
declaration order regardless of thread completion order and expose both
reserved and actually consumed resources.

Policy providers are retained only until their dependency wave completes. A
single mutable provider cannot be shared across concurrent goals; reuse in a
later wave is independently rejected by the runner's fresh proposal-ledger
contract. Every successful worker must retain an independently checked replay
of its original goal with matching proof-node counts.

## Durable interruption and restart

Long campaigns can optionally persist already verified proofs:

```python
from pathlib import Path

checkpoint = Path("constructive-campaign.checkpoint.json")
first_run = run_campaign(goals, limits=CampaignLimits(max_workers=2),
                         checkpoint=checkpoint)

# After an interrupted process, provide the same graph and exact resource limits.
resumed = run_campaign(goals, limits=CampaignLimits(max_workers=2),
                       checkpoint=checkpoint, resume=True)
assert resumed.restored_goals == first_run.proved_goals
```

A saved file is never accepted as mathematical authority. It binds the exact
ordered goal DAG, canonical and original statements, prerequisite edges,
capability preimages, logic modes, historic/modern numeral profiles, and both
per-goal and global resource envelopes. Each proof receipt contains the
original commands, their digest, and the checked certificate size. Before a
restored goal can release a dependent, the unchanged traced batch runner
replays its complete command sequence against the original formula and the
existing kernel verifies the resulting certificate again.

Checkpoint creation refuses an existing file unless resume is explicitly
requested. Updates are directory-descriptor-relative, no-follow, mode-0600,
atomically replaced, and flushed to durable storage. Symlinks, malformed or
duplicate JSON fields, files above the 8 MiB bound, changed authorities,
reordered prerequisites, altered commands, and inconsistent certificate sizes
all fail closed. A failed atomic update leaves the preceding valid checkpoint
intact. Restored proofs are labeled separately from newly executed model runs;
resumption never manufactures historical search or comparison evidence.

## Model and evidence boundaries

The historical trained Qwen3-1.7B adapter lives on WMI and is frozen to its
historical 247-theorem authority. Newer library theorems cannot silently enter
that adapter's prompts or imports. The new Helios adapter is separately
attested to Alpha v25 and cannot silently inherit a later release either.
A broader model-assisted campaign requires a reviewed library epoch and
compatible model/provider authority.

The exact historical surface labels `model-v1`, `model-v2`, and `model-v3`
also retain their attested numeral bound of 256, both for theorem statements
and every proposed tactic or witness. Modern named campaign authorities can
use the conservative compact representation up to the current 1,000,000
surface limit. Goal scheduling, direct Hydra execution, and underlying
candidate search all enforce the same profile-aware boundary.

Ordinary proof-development work may use checked Hydra suggestions before the
publication-grade H0–H5 experiment gates are complete. Such runs remain
explicitly **ineligible for claims of a measured LLM advantage**. The binding
experimental protocol is `docs/PEANO_HYDRA_DESIGN.md`.
