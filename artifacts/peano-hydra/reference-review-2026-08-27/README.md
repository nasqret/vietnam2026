# Hydra reference and lineage review — 2026-08-27

The bounded review pipeline is implemented and its first execution is complete.
It does **not** close H0/H1, approve a training split, or authorize a model run.

- **1,321 exact conformance cases matched** the separately implemented Lean
  checker, rebuilt from source with an audited axiom footprint.
- **14/16 existing theorems replayed in each sampled cold pass**: 28 positive
  receipts, with identical partial roots. Two targets exceeded their guards
  in each pass and remain unverified by this run.
- The complete **28-component / 2,080-theorem** lineage inventory supplies
  **zero unexposed structural DEV components** under the retained rules.
- Lean **4.28.0** supplies compatibility evidence only. The companion's
  **4.31.0 pin remains unsatisfied**; human review is still pending.

**Independent archive re-verification passed** from the frozen source:
all 1,321 reference cases and all 28 retained positive replay receipts were
rechecked, the compiled reference bytes matched, and live lineage audits
were repeated. The exact [verification receipt](verification.json) is retained.
The first attempt from the primary checkout failed while concurrent Alpha
work was changing recorded source. The subsequent byte check rejected
`lean_proof_strand.py`; successful re-verification used the unchanged archive
and isolated frozen checkout. The [failed-attempt note](verification-attempt-1.json)
and [exact console log](verification-attempt-1.log) are retained, not erased.

## What was actually checked

| Fixture class | Count | Observation |
| --- | ---: | --- |
| Distinct closed positive formulas | 1,024 | Native acceptance and Lean `ACCEPT` |
| Invalid certificate mutations | 280 | Native rejection and Lean `REJECT` |
| Wire/artifact boundary cases | 17 | Lean: 15 `DECODE_ERROR`, two `REJECT`; native wire checks deliberately not claimed |
| Total independent Lean decisions | **1,321** | **1,024 accepts, 282 rejections, 15 decoding errors; no mismatches** |

The positives are **32 authored templates × 32 correlated seeds**, each with
an explicit proved reflexive tag conjunct. They are not 1,024 independent
mathematical lineages or autonomous discoveries. The authored bodies cover
all **24 constructive proof constructors** and **six arithmetic axioms**.
Mutations exercise constructor, binding, eigenvariable, substitution,
induction, and classical-boundary failures. A rejected certificate is not
a certified non-theorem; this is not a decision procedure for HA.

Eight reference modules were freshly compiled. The four audited declarations
are `PeanoLab.check_derives`, `PeanoLab.checkClosed_sound`,
`PeanoLab.Artifact.check_derives`, and `PeanoLab.Artifact.check_sound`.
The derivation bridges use `propext`; the Nat-soundness results additionally
use `Classical.choice` and `Quot.sound`. No `sorryAx`, extra axiom, or prebuilt
companion module was accepted. Nat soundness does not establish intuitionistic
completeness or independently validate the surface parser.

## Cold replay: useful calibration, not a full-library gate

The frozen selection is 16 fixed enrollment-order quantiles of Alpha v25,
each in its own fresh process, repeated twice. Native public replay can load
ordinary checked proof bundles or regenerate historical scripts; this is
**not** an all-script-regeneration claim or a new theorem-search experiment.

Both passes check the same 14 original theorems. Examples include
`beta_repeat_exists` (29,322 structural proof nodes, depth 83),
`lucas_pascal_congruence_step` (3,851 nodes, depth 92), and
`crt_pairwise_compatible_dominating_last_canonical_exists_unique`
(10,086 nodes, depth 77). Their complete identities and certificates'
structural fingerprints are in [cold.json](cold.json).

| Uncompleted target, in both passes | Observed limit | Outcome |
| --- | --- | --- |
| `central_binom_upper_support_package` | 1 GiB sampled RSS guard | Worker stopped with signal 9; no positive receipt |
| `three_mod_four_good_prime_exclusive` | 30 CPU seconds | Worker stopped with signal 24; no positive receipt |

The 32 workers took **422.49 seconds** within the frozen 900-second cold-stage
budget. Each reserved 45 wall seconds, 30 CPU seconds, and 1 GiB RSS; no retry
or limit increase occurred. On macOS the RSS guard is sampled at 100 ms, not
instantaneous: the maximum observed worker RSS was **1,104,101,376 bytes**
(about 1,053 MiB) before termination. Actual killed-worker CPU/RSS observations
are retained; unmeasured instructions and energy remain null.

Both **partial**, not full, ordered roots are:

```text
83a85cb70bb0ba3b4474ae8feec0f755ef9ff499b792d63f5223ed57c3515ecf
```

Full roots are null and `full_epoch_replayed_twice` is false. No full
2,080-theorem double pass was attempted after this calibration exposed the
two resource hot spots. Their failures do not refute the already sealed
theorems and do not diagnose a memory leak.

## The data boundary

The original eight DEV families still join one declared component containing
2,048 catalog theorems. Its original masks and all 740 unresolved canonical
statements remain conservative. The full inventory adds 27 other components;
only 18 components / 19 theorems lie outside the structural restrictions.
Every one of those candidates is exposed in the authenticated preparations,
including their closed-row aliases. There is no established disjoint
model-facing TRAIN/DEV allocation under the current contract.

The default proposal retains the exposed DEV component in quarantine and
leaves the other 27 components unassigned: **30 explicit conflicts**,
`not-reviewed`, no human acknowledgment, and no training authorization.
Both original preparations were authenticated against their retained files;
the prepared `catalog-460` corpus was **not trained**. This review does not
replay all historical training-source proofs or claim semantic novelty.

## Reproduction and retained evidence

Implementation source: `a69e2e9bfdaf4de3b567727a214367c193478cea`.
Reference Git source: `d2903c8bd507b7e4458b1249f840a4e274befdbf`.
Alpha-v25 epoch: `a96223a021edc556ed7620a87b4c00e5817ba169af4a1db093fa7a81847e082e`.
The exact compiler, runtime-library hashes, profile, fixtures, resource
reservations, and source inventories are in [plan.json](plan.json).

The run used a clean detached checkout while unrelated Alpha authoring
continued in the primary checkout. Existing files were not removed or
committed to make the tree appear clean. Its 14 copied preparation inputs
were byte-identical originals; no weights or checkpoints were copied.
These results describe the frozen Alpha-v25 review epoch, not the admission
status or capabilities of concurrent newer Alpha releases.

From a checkout matching the recorded implementation source and installed
compiler environment, with both original preparation directories and the
reference Git objects available:

```console
python3 scripts/check_peano_hydra_review.py \
  --verify artifacts/peano-hydra/reference-review-2026-08-27
```

On this workstation, the retained frozen checkout also permits verification
while Alpha work continues in the primary directory:

```console
python3 _deploy/hydra-review-source-a69e2e9b/scripts/check_peano_hydra_review.py \
  --verify artifacts/peano-hydra/reference-review-2026-08-27
```

Verification checks saved evidence before execution, rebuilds the Lean
reference in a fresh temporary directory, compares all fixture outcomes and
compiled bytes, replays every retained positive, and repeats the live lineage
audits. Historical worker paths are validated as metadata; fresh workers use
the current checkout. A changed source file, duplicate target, altered
receipt, overstated summary, or failed positive reproduction fails closed.
Live verification still requires the same Python executable path as the
recorded workers: `/Library/Frameworks/Python.framework/Versions/3.10/bin/python3`.
If `python3` resolves elsewhere, use that absolute executable above. The
recorded Lean binary/runtime and reference-project locations must also remain
available; the static archive tests do not demonstrate live portability to a
different Python or Lean environment.

The archive retains eight original JSON/JSONL evidence files, nine small Lean
source/audit files, and explicitly labeled verification records. Compiled
`.olean` files and per-case build directories are
not archived. No model, solver, GPU job, public deployment, or theorem
admission occurred in this stage.

## Post-run repository checks

The complete `make hydra-check` passed from the unchanged frozen source:
**1,984 tests**, followed by the preparation check. The new archive and
Hydra-specific documentation/link checks also passed: **32 tests**.

A broader documentation check was additionally attempted in the actively
edited primary checkout: **66 passed, 23 failed, one setup error**. Its
release-wide checks encountered the concurrent Alpha-v26 catalog/definition
migration while guides and some explorer manifests still named v25. Those
changes were preserved for their owning release workflow, not rewritten to
make this review appear green. This archive certifies neither that mixed
working checkout nor a completed Alpha-v26 integration.

## The one next gate

Complete one **human-reviewed new-lineage/reference readiness bundle**:
review genuinely eligible lineages and their ownership, satisfy the pinned
Lean environment, and profile/reduce the two bounded native replay hot spots
before a resource-reviewed full double pass. Do not turn the present exposed
DEV diagnostics into an unseen-model claim or launch another GPU comparison.

Follow the [human review guide](../../../docs/HYDRA_REFERENCE_REVIEW.md) and
the [single product roadmap](../../../docs/HYDRA_PRODUCT_ROADMAP.md).
