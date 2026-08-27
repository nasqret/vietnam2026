# Hydra: review the reference checks and the next data boundary

This walkthrough prepares evidence for a human decision. It does not approve
a split, create model-facing datasets, train a model, or close H0/H1. The one
path forward is to review the lineage rules and reference evidence, identify
genuinely new eligible lineages, and only then authorize a later data/model
stage. The [product roadmap](HYDRA_PRODUCT_ROADMAP.md) remains authoritative.

## What is known now

| Item | Current evidence |
| --- | --- |
| Catalog partition | 28 components covering all 2,080 theorems |
| Structurally unmasked remainder | 18 components, containing 19 theorems |
| Unexposed DEV candidates in that remainder | **Zero**: all 18 components are exposed under the retained preparation audits |
| Native conformance | 1,024 positive certificates accepted; 280 invalid certificates rejected |
| Lean reference build | Eight modules freshly built with Lean 4.28; axiom audit passed |
| Complete Lean fixture comparison | **1,321/1,321 matched**, then freshly rechecked from frozen source |
| Twice-fresh cold sample | **14/16 checked per pass**; the same two targets hit resource guards |
| Independent archive verification | **Passed**: fresh reference build, all 1,321 cases, all 28 retained positive receipts, repeated lineage audits |
| Pinned Lean 4.31 gate | **Open**: not installed; the configured installation command returned `Unsupported elan command` |

The retained exposure scope covers both preparations. It does not claim that
every model consumed both corpora: `catalog-460` is still prepared, not
trained. “Unmasked” is a structural inventory property, not proof of semantic
novelty, independent authorship, or unseen-model eligibility. The present
answer is therefore **blocked pending review**, not “automatically resplit.”

The [archived execution report](../artifacts/peano-hydra/reference-review-2026-08-27/README.md)
records exact results, source identities, and explicit open gates.
It describes the frozen Alpha-v25 epoch, not the status of concurrent newer
Alpha releases.

The fixture suite has 1,321 cases: **1,024 distinct closed positive formulas**,
**280 invalid-certificate mutations**, and **17 separate wire cases**. The
positive formulas come from **32 authored templates × 32 correlated seeds**,
with an explicit proved reflexive tag conjunct. They are not 1,024 independent
mathematical lineages or autonomous Hydra discoveries. The wire expectations
are 15 decoding errors and two artifact-gate rejections (zero fuel and an open
target); they are not native-checker failures or non-theorem labels.

## 1. Inspect the plan without running the campaign

Run from the repository root:

```console
python3 scripts/check_peano_hydra_review.py --plan \
  --lean-binary /Users/bnaskrecki/.elan/toolchains/leanprover--lean4---v4.28.0/bin/lean
```

Omitting `--plan` also selects the read-only plan mode. It does not compile
Lean, replay the library, write an output campaign, or start a model.

The default starting evidence is the preserved
[development plan](../artifacts/peano-hydra/development-2026-08-27/plan.json).
Keep the original `_deploy/hydra-posttrain` and
`_deploy/hydra-posttrain-next` preparation files available: the review checks
their authenticated bytes, not just an old summary. Read the component
restrictions and exposure conflicts before proposing any allocation.

Optional `--allocations FILE` accepts a strict JSON **array** of whole-component
entries. Every entry has exactly `component_id` and `split`; use exact IDs from
the inventory and one of `train`, `dev`, `quarantine`, or `unassigned`. It is
not a list of individual theorems, rows, families, or seeds. Unknown/duplicate
IDs and extra fields are rejected; missing or unassigned components leave the
proposal blocked. A valid file is still only a proposal, not approval or a
way to make exposed material unseen.

## 2. Produce fresh bounded evidence

Choose a new output directory; preserve existing and interrupted runs. On
this workstation the reviewed installed compiler is the explicit Lean 4.28
binary below, not an `elan` shim:

```console
python3 scripts/check_peano_hydra_review.py --run \
  --output-dir _deploy/hydra-reference-review-v1 \
  --reference-project ../peano-lab-lean \
  --lean-binary /Users/bnaskrecki/.elan/toolchains/leanprover--lean4---v4.28.0/bin/lean \
  --cold-scope sample \
  --cold-batch-size 1
```

This stages and rebuilds the selected reference source, audits its axioms,
and compares the exact fixture bytes with the independent Lean endpoint.
Existing companion build products are not substituted for a fresh build.
Source identity and bounded worker CPU/wall/RSS guards remain active. On
macOS the RSS guard is sampled, not an instantaneous hard allocation cap.
Missing measurements, limits, or interrupted work must remain explicit;
they cannot become an invented pass.

Execution requires a clean committed source tree. If Alpha authoring is
happening concurrently, use a clean detached worktree at the recorded source
commit; do not remove or commit unrelated work to satisfy this guard. Copy
the seven unchanged inputs from each original preparation into the same
`_deploy/hydra-posttrain` and `_deploy/hydra-posttrain-next` relative paths:
`manifest.json`, `train.jsonl`, `dev.jsonl`, `preferences.jsonl`,
`discovery.jsonl`, `quarantine.jsonl`, and `config.toml`. These are about
38.5 MiB in total; no weights, checkpoints, or new dataset generation are
needed. In a nested worktree, explicitly select the original Lean reference
project's absolute path with `--reference-project`.

The default `sample` cold scope selects **16 ordinal-spread catalog targets**
and replays them in **two passes**. It is a smoke sample, not two full-library
replays. The sample always uses one target per fresh worker. For `full`,
`--cold-batch-size` permits 1–16 targets per fresh batch; caches may be shared
inside that batch only. `--cold-scope none` skips that evidence, while
`full` requests both passes over the full frozen catalog and needs a separate
resource/time review before use. Selecting `full` is not itself a passing gate.

The recorded sample checked 14 targets in both passes (28 positive receipts).
`central_binom_upper_support_package` hit the 1 GiB RSS guard and
`three_mod_four_good_prime_exclusive` hit the 30-second CPU guard in each
pass. Both partial roots match, but the full roots remain null. This does not
refute those sealed theorems or establish that a leak caused either limit.
The remaining full double pass needs resource-reviewed replay work; the
pipeline does not automatically raise limits after observing failures.

The installed 4.28 build is **compatibility evidence only**. It does not
satisfy the companion's 4.31 pin. The failed configured installation is a
recorded limitation; this workflow neither downloads an alternative nor
bypasses that boundary.

## 3. Verify the saved run independently

```console
python3 scripts/check_peano_hydra_review.py \
  --verify artifacts/peano-hydra/reference-review-2026-08-27
```

If the primary checkout has moved on to other Alpha work, the retained
frozen checkout can run the same verification from the repository root:

```console
python3 _deploy/hydra-review-source-a69e2e9b/scripts/check_peano_hydra_review.py \
  --verify artifacts/peano-hydra/reference-review-2026-08-27
```

Verification freshly rebuilds and replays the recorded checks. Keep the
original preparation files and reference Git objects available for its live
provenance and exposure audit. A saved
plan, successful build probe, or native-only fixture pass is not a substitute
for the completed verified run report. The
[retained verification receipt](../artifacts/peano-hydra/reference-review-2026-08-27/verification.json)
records successful fresh checking of all 1,321 cases and 28 positive receipts.
The recorded execution checkout may differ from the current matching-source
checkout: saved command locations are validated, not executed. Every fresh
worker uses the current checkout and its independently authenticated source.
This does not make the archive portable between Python environments: live
verification currently requires the **same Python executable path** as the
recorded workers, `/Library/Frameworks/Python.framework/Versions/3.10/bin/python3`.
Use that full path instead of `python3` above if a virtual environment or PATH
selects another interpreter. Keep the recorded Lean binary/runtime and
reference-project locations available as well. Portable static archive tests
are not a substitute for this environment-bound live re-verification.
The first primary-checkout verification failed after source drift; its log
and follow-up source-check note remain in the archive. It was not relabeled
as a pass or used to change the frozen resource limits.

Lean's certificate checker and soundness proofs are the independent endpoint;
the companion's mirrored Python kernel is not an independent reference.
Acceptance checks a particular certificate for its exact target. Rejection
does **not** establish that no proof exists. Standard-natural-number
soundness also does not establish intuitionistic completeness. This stage
does not independently verify the surface parser or complete all H0 semantic,
reference, cold-replay, and full-protocol obligations.

## 4. Give focused human feedback

Review these three decisions together:

1. **Lineage and authorship:** are the retained dependencies, aliases,
   generator relationships, exposure scope, and authored-fixture labels
   adequate? Name any missing relationship; do not cut a component merely to
   obtain a convenient holdout.
2. **New eligible material:** which genuinely new lineages should be authored
   or independently sourced next, with their ownership and provenance
   recorded before model-facing preparation? The current inventory supplies
   no unexposed DEV component under the retained rules.
3. **Proof environment:** review the exact source/compiler identities,
   standard Lean axioms, compatibility-only status, resource limits, and
   unresolved pinned-toolchain obligation.

A useful response is: “I accept/change these lineage rules; propose these new
lineages and their owner; accept the recorded 4.28 result as compatibility
evidence only / request additional environment evidence.” This is feedback
for a later reviewed decision, not permission inferred by a script.

Hashes bind evidence, not a human identity or cryptographic approval token.
Neither running the commands nor supplying allocations records that you have
approved the project. Human acknowledgment, an approved TRAIN/DEV boundary,
independent H1 ownership, and authorization for later data/model execution
remain separate explicit steps. See the
[native action protocol](HYDRA_DEVELOPMENT_PROTOCOL.md) and
[binding H0 gates](../PLAN/11_peano_hydra.md#h0--semantic-and-functional-core).
