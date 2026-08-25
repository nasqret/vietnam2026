# Peano Hydra research execution

Peano Hydra is an **untrusted proof-search orchestrator**, not a second proof
kernel. Symbolic tactics, recorded teachers, language models, and future solver
adapters can suggest candidate moves. A theorem is accepted only after the
existing Peano kernel checks the original statement; `run_hydra` additionally
replays every successful command sequence in a fresh traced session.

## Current executable evidence

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

The existing trained Qwen3-1.7B adapter lives on WMI and is frozen to its
historical 247-theorem authority. Newer library theorems cannot silently enter
that adapter's prompts or imports. A broader model-assisted campaign requires
a newly reviewed library epoch and compatible model/provider authority.

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
