# Hydra development evaluation: broader goals, visible boundaries

This is the completed bounded model-free engineering stage after the
[first Alpha-v25 model experiment](../artifacts/peano-hydra/alpha-v25-posttrain-2026-08-26/README.md).
It compares a deterministic closure component with a state-aware symbolic
portfolio, audits existing training exposure, and retains independently
replayable evidence. It does not train a model, admit a theorem, use an
external solver, or seal a final benchmark.

## What is being evaluated

The fixed generator declares **64 goals across eight families**, plus the
**four historical diagnostic goals** in a separate cohort. Families cover
closed arithmetic, numerical witnesses, implication, conjunction,
disjunction, universal equalities, inductive arithmetic, and variable-dependent
witness composition. No target comes with a proof script or teacher route.
Generators and family declarations are fixed before the new outcomes.

Eight numerical variants are not eight independent mathematical lineages.
The manifest joins declared families, generator seeds, shared proof
derivations, canonical aliases, catalog anchors, and theorem dependencies.
It retains the resulting connected components and conservative masks rather
than cutting a large component into attractive-looking holdouts. The authors
already knew the historical smoke results and catalog families; this is
public development work, not a secret test or mathematical novelty claim.

All evaluated goals use **zero theorem imports and zero retrieval entries**
under the narrower `hydra-development-no-imports-v1` capability. The complete
Alpha-v25 epoch hash is bound separately for lineage/mask metadata; workers
have no Alpha import authority and need not reload its unused theorem catalog.
This is not an authority-matched comparison with the previous model run.
The [frozen development profile and typed actions](HYDRA_DEVELOPMENT_PROTOCOL.md)
binds the grammar, constructive trust boundary, native action transport,
limits, and implementation hashes. The original surface-macro-v0 runner and
previous model/preparation manifests remain unchanged.

## Measured run — 2026-08-27

The [archived experiment](../artifacts/peano-hydra/development-2026-08-27/README.md)
ran from clean source `7f0bdd62` with its full plan frozen before outcomes:

| Cohort | Closure only | Symbolic portfolio |
|---|---:|---:|
| Expanded goals | **16/64** proved | **48/64** proved |
| Historical diagnostics, separate | **2/4** proved | **3/4** proved |

Independent verification passed for **69 successful proof certificates** and
the deterministic policy/typed-action records of **130 completed workers**.
Six of the 136 workers hit the three-second CPU guard and remain unknown,
with unavailable CPU/RSS measurements left null. Both eight-goal families —
inductive arithmetic and existential composition — remain entirely unsolved
under these limits. Implementing their candidate generators is not the same
as solving those benchmarks.

The exposure audit is deliberately unfavorable: all eight families join one
component containing **2,048 catalog theorems**. The original preparation
exposes **175 training roots** in that component; `catalog-460` exposes
**436**. Therefore **8/8 families are blocked for unseen-model comparison**
in both preparations. Of 2,080 catalog statements, 1,340 fit bounded
canonicalization; the remaining 740 and their descendants are masked, not
declared clean. This does not alter either training corpus or model.

The next milestone is one human-reviewed new-lineage/reference readiness
bundle: reviewed model-facing TRAIN/DEV lineage separation and the required
H0 semantic/reference evidence, not another training run on the exposed
component. The [review workflow](HYDRA_REFERENCE_REVIEW.md) is implemented;
these useful public diagnostics do not close H0/H1/H2/H5.

In a separate [archived Alpha-v25 reference execution](../artifacts/peano-hydra/reference-review-2026-08-27/README.md),
Lean 4.28 matched **1,321 authored fixture outcomes** after eight fresh module
builds and a passing axiom audit. Cold replay checked **14/16 sampled targets
per pass**, retaining 28 positive receipts; four resource-limited workers
remain unknown. This does not change the native search scores above or make
any exposed DEV component unseen. The allocation proposal remains
blocked/not-reviewed, and the 4.31 pin and full cold scope remain open.
Fresh frozen-source archive verification passed, rechecking all 1,321
reference cases and reproducing all 28 retained positive cold receipts.

## Run it safely

Inspect the plan without executing any search:

```console
make hydra-dev-plan
```

Also audit both existing preparations without changing either one:

```console
python3 scripts/eval_peano_hydra_development.py --plan \
  --preparation _deploy/hydra-posttrain \
  --preparation _deploy/hydra-posttrain-next
```

The default output is a short summary. Add `--full-plan` when the full JSON
manifest and masks are wanted. Preparation files must exist for an audit;
no weights, GPU, network, or corpus regeneration are needed. The audit
authenticates file hashes, epoch/configuration, canonical historical exclusions,
catalog row lineages, and exposure of declared components. It is not another
proof replay or a complete semantic-equivalence decision. A blocked family
must not be advertised as an unseen evaluation of an already exposed model.

Explicitly execute the two symbolic lanes into a **fresh** directory:

```console
python3 scripts/eval_peano_hydra_development.py --run \
  --preparation _deploy/hydra-posttrain \
  --preparation _deploy/hydra-posttrain-next \
  --output-dir _deploy/hydra-development-v1
```

Alternatively `make hydra-dev-evaluate` runs the same symbolic experiment
without preparation-exposure audits. Use
`HYDRA_DEV_DIR=_deploy/a-new-development-run` to select a fresh directory.
Neither path authorizes a model comparison. Existing output directories are
refused, including interrupted partial runs; keep their evidence and choose a
new name.

The plan, benchmark, masks, configurations, and source identity are written
and flushed **before the first outcome**. Execution is sequential with one
fresh child per goal/lane, capped by default at **five wall-clock seconds**,
**three CPU seconds**, and **1 GiB memory**. Linux enforces an address-space
limit; macOS uses a sampled 20 ms RSS guard because reserved virtual memory
is not a meaningful resident-memory limit there. The macOS guard is not a
hard instantaneous allocation cap. Parent timeouts terminate only their own
child. No cluster job or model process is involved.

The complete two-lane run reserves **136 child runs / 680 seconds of worker
wall time**, excluding planning and publication overhead. Search additionally
bounds depth, beam width, proposals, states, terms, candidates, and retained
evidence. A timeout, memory limit, invalid output, or interrupted process is
**unknown**, never a disproof or an inferred success. Unavailable resource
counters stay null; they are not filled with zeros.

## What the symbolic portfolio does

The closure lane proposes existing checked reflexivity, assumption,
simplification, and small closed arithmetic steps. The portfolio additionally
inspects the current goal and hypotheses to propose logical introductions and
eliminations, bounded witnesses, and induction candidates. Arithmetic used to
rank witness proposals is untrusted; the kernel still decides every proof.
There are no target-name lookups, recorded transcripts, or model-generated
actions in either lane.

Closure, structural, witness, and induction proposal components can each be
disabled in the immutable `SymbolicConfig`; the configuration and its source
hash are retained in every result. The runner's legacy `model_calls` field
counts policy requests, even for a symbolic policy. Here it is symbolic
proposal/state work: actual model and external-solver calls are explicitly
**zero**. Typed proposal receipts, public tactic ledgers, successful full
traces, proof-node counts, and actual CPU/wall/RSS measurements are retained.
CPU instructions and energy are not measured and remain explicitly absent.

Equal resource limits do not imply equal consumed compute. A stronger set of
candidate generators does not automatically prove portfolio dominance: beam
competition can alter which paths survive. Compare the measured rows, and
keep timeouts separate from genuine exhausted finite frontiers.

## Independently check the evidence

```console
make hydra-dev-verify
```

Or select the actual directory directly:

```console
python3 scripts/eval_peano_hydra_development.py \
  --verify _deploy/hydra-development-v1
```

Verification authenticates the report, exact row bytes, original source/profile
and predeclared benchmark/masks, rebuilds metrics, and starts fresh bounded
kernel replays for every positive. It also regenerates deterministic policy
proposals and typed action receipts from every completed worker's recorded
states, so a portfolio proof cannot be relabeled as a closure-only proof.
The complete saved traces must match.
It never starts a model or rewrites the recorded run. `plan.json` alone is
only planning/partial-run evidence; only a completed `report.json` contains
the final table.

The archived run can be verified directly without the original preparations:

```console
python3 scripts/eval_peano_hydra_development.py \
  --verify artifacts/peano-hydra/development-2026-08-27
```

The recorded implementation hashes must match. The preparation audit receipts
are authenticated as part of the frozen plan; repeating those exposure audits
requires the original preparations. Physical resource measurements and killed
worker exits are historical observations, not independently hardware-attested
measurements.

## What remains open

The bounded native development protocol is not the entire H0 conformance or
structured-solver protocol. The separate
[reference/lineage workflow](HYDRA_REFERENCE_REVIEW.md) now implements bounded
certificate comparisons and cold-replay evidence. Full semantic/reference
acceptance in the pinned Lean 4.31 environment, two complete cold library
replays, broader macro/solver attestation, and human fragment review remain
separate gates. Lean 4.28 checks are compatibility evidence only, and a cold
sample is not a full-library pass. This DEV generator is not an
independently owned, sealed H1 set, and a component exposure audit is not a
complete semantic-novelty or equivalence audit.

Any overlap with existing training must be resolved before a new model-facing
split is prepared. Do not train `catalog-460` and relabel these diagnostics as
unseen. The [single product roadmap](HYDRA_PRODUCT_ROADMAP.md) controls the
next milestone; the [binding experimental design](PEANO_HYDRA_DESIGN.md)
continues to govern H0/H1/H2/H5 acceptance.
