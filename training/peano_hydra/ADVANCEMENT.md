# Hydra after the completed frontier pilot

The first v28 frontier training job, Helios **21438102**, completed one fresh
Qwen3-1.7B-Base LoRA epoch and all **1,597 optimizer updates**. The final adapter
manifest SHA256 is
`5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68`.
The original training source and consumed reservation remain immutable.
Training completion does not establish improved proof-search performance.

This continuation adds three separate paths without changing the historical
candidate, native proof checker, training objective, or benchmark acceptance
criteria:

| Path | Entry points | Scope |
| --- | --- | --- |
| Current reference calibration | `review_v28.py`, `cold_replay_v28.py`, `scripts/check_peano_hydra_review_v28.py` | All 2,764 declarations remain in the pinned inventory; bounded native hotspots and exact Lean 4.31 reference fixtures are separate modes. |
| Saved-adapter comparison | `frontier_saved_benchmark_run.py`, `frontier_evaluation_launch.py`, `scripts/eval_peano_hydra_frontier_saved_benchmark.py` | Compare the completed v28 adapter against the historical v25 corrective adapter without repeating training. |
| TRAIN-only proposals | `self_training_proposals.py`, `scripts/propose_peano_hydra_self_training.py` | Select at most 64 reviewed TRAIN goals, generate bounded proof proposals, then independently replay and deduplicate verified material. |

## Measure the saved adapter before expanding training

The evaluation-only profile `peano-hydra-frontier-evaluation-v1` has its own
one-use ledger and one proposed 1,800-second GH200 / eight CPU / 64 GiB job.
It preserves the old/new comparison at 8 and 16 calls on both candidate PRIMARY32
and historical regression PRIMARY32: at most 256 outcomes and 3,072 model calls.
The other 32 benchmark variants stay reserved and unscored.

Actual benchmark/reference review, source/data provenance, original-validator
receipts, and separately supplied resource approval are required. The final
adapter and existing baseline are external read-only dependencies, not imaginary
files in a closed upload bundle. Both are rehashed through the original bridge
before inference. A draft cannot submit, retrain, resume, retry, or reuse the
spent `frontier-training-v1` ledger.

The login gate supports installed Python 3.9 by checking the exact approved
source/input bytes and a separately bound local semantic result. Full semantic
checking runs in Python 3.11 or newer locally and again on the compute node.
This byte gate is not described as rerunning the newer semantic engine on 3.9.

## Reference work remains a real prerequisite

See [REFERENCE_V28.md](REFERENCE_V28.md) for exact modes, source inventories,
resource limits and commands. Native hotspot calibration needs an external
process-tree supervisor as well as the unchanged child guards. It is not Lean
evidence or a full-library result.

The first native calibration exposed missing historical proof data in the
code-only snapshot. The v2 controller now declares the two exact Bertrand and
v23 milestone JSON bundles (16,887,078 bytes), checks their repository-relative
paths and hashes before workers, and rechecks them inside and after workers.
They are separate committed calibration inputs, not additions to the historical
origin code scope. This closure covers the two selected hotspots only.

The reference mode requires actual Lean 4.31.0 compiler/runtime bytes; older
Lean results are not relabelled. Full readiness additionally needs two complete
2,764-target cold passes, no failures or unknowns, matching complete roots,
separate fresh reproduction and real human review. Seventeen current statements
exceed the inherited 128 KiB worker field cap. They remain in the full inventory;
their serialization profile and full-campaign resource envelope remain open.

## Proposals remain outside admitted training data

Proposal generation uses the existing optimized context-alpha search, with
depth 16, beam four, four candidates per state, 64 states and up to 16 model
calls per goal. It reserves all benchmark roots/templates/states and every
non-TRAIN parent route before policy access. Only a complete proof of the
original input goal can proceed to independent native harvesting.

The actual accepted saved-adapter pilot must match the proposal's model and
benchmark identities. Generation also requires a caller-owned one-use resource
reservation; the standalone CLI refuses to invent one. Harvest runs in a fresh
model-free interpreter and checks every full replay state before deduplication.
Partial or resource-limited attempts are not negative theorem labels.

Verified material still needs a new immutable curriculum, lineage review,
data admission, production token preflight and explicit training reservation.
No model-generated rows, new GPU authorization or research readiness are
created merely by implementing or testing these paths.

Detailed evidence for this continuation is retained in the parent workspace's
`artifacts/hydra-advancement-2026-08-30` archive. The authoritative recovery
entrypoint is the parent workspace's `RECOVERY.md`.
