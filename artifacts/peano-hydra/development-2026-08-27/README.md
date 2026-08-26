# Hydra native development evaluation — 2026-08-27

The new state-aware symbolic portfolio proves **48/64 expanded development
goals**, compared with **16/64** for its closure-only ablation. This is a
model-free engineering result: no language model, theorem import, retrieval,
external solver, or target-specific proof script was used.

The native development protocol now provides seven typed actions with
deterministic compilation, capability/state receipts, bounded inputs, and
transactional failure. The portfolio uses these actions to propose logical
steps, small witnesses, and induction from the current proof state. The
existing Peano kernel remains the proof authority.

## Measured result

| Cohort | Closure only | Symbolic portfolio |
|---|---:|---:|
| 64 expanded DEV goals | **16/64 proved**, 48 unknown | **48/64 proved**, 16 unknown |
| Four historical diagnostics, reported separately | **2/4 proved**, 2 unknown | **3/4 proved**, 1 unknown |

The expanded portfolio closes all eight variants in each of six families:
closed arithmetic, numerical witnesses, implication transport, conjunction
transport, disjunction transport, and universal equalities. The closure-only
lane closes the arithmetic and universal-equality families. Neither lane
closes the inductive-arithmetic or variable-dependent existential-composition
families under this run's limits. The historical `consecutive_product_even`
goal also remains unknown.

There are **136 goal/lane rows**, **69 successful proof certificates** covering
**51 distinct goals**, and **67 unknown outcomes**. Of those unknowns, six
portfolio workers hit the three-second CPU guard (`worker_returncode: -24`,
SIGXCPU on the recorded Mac): `dev_inductive_arithmetic_03` through `_07` and
`dev_existential_composition_07`. Their proof evidence and unavailable worker
resource counters remain null. A limit is not a disproof.

Independent verification regenerated the deterministic policy proposals and
typed receipts for **all 130 completed workers**, including their unsuccessful
searches. It freshly kernel-replayed **all 69 successful certificates** and
matched their full saved traces. The six CPU-killed workers have no completed
proposal ledger to regenerate and are not counted as replayed proofs.

## The important training-data finding

These **eight families are not independent holdouts**. Their declared family,
generator, canonical-alias, and proof-dependency relations join into **one
connected development component containing 2,048 catalog theorems**. Each
goal conservatively masks 2,061 of the 2,080 catalog names; the actual worker
authority permits no imports at all.

Both existing training preparations expose this component:

| Preparation | Training rows | Exposed training theorem roots | Families blocked for unseen-model comparison |
|---|---:|---:|---:|
| Original Alpha-v25 run | 1,773 | 175 | **8/8** |
| Prepared-only `catalog-460` run | 7,129 | 436 | **8/8** |

The bounded canonicalizer checked 1,340 catalog statements. The remaining 740
out-of-profile statements and their descendants are conservatively masked,
not assumed clean. This is an audit of declared relationships and authenticated
preparation files, not a complete semantic-equivalence procedure or a fresh
replay of the entire training corpus. The authors knew the catalog and the
historical outcomes; the generated seeds are correlated public DEV variants.

**Do not train the prepared `catalog-460` corpus and describe these goals as
unseen.** The next milestone is reviewed model-facing TRAIN/DEV lineage
separation together with the required H0 semantic/reference checks, before
another authorized model comparison. The final benchmark additionally needs
independent ownership and sealing. No existing model or dataset was changed.

## Frozen execution and resource boundaries

The complete plan was flushed before the first search. The source was clean
at commit `7f0bdd62526849cc8ace838da88aa7d53b2c3a4b`; its exact implementation
hashes are in [plan.json](plan.json). The run started at
`2026-08-26T22:26:45.617717+00:00` and finished at
`2026-08-26T22:27:33.990160+00:00` — 27 August in Europe/Warsaw.

Each sequential fresh worker had five wall seconds, three CPU seconds, a
1 GiB memory guard, depth 16, beam width 4, eight candidates per state, 128
states, and 128 policy proposals. macOS uses a sampled 20 ms RSS guard, not an
instantaneous hard allocation cap; Linux additionally limits address space.
The 136-run wall reservation was 680 seconds. No concurrent model workers ran.

| Resource measurement | Closure only | Symbolic portfolio |
|---|---:|---:|
| Cumulative parent-measured child wall seconds, all rows | 12.458 | 35.605 |
| Worker rows with completed CPU/RSS measurements | 68/68 | 62/68 |
| Recorded worker CPU seconds | 2.753 | 8.391, **partial** |
| Largest recorded completed-worker peak RSS | 31.4 MiB | 33.8 MiB, **partial** |
| Actual model / external-solver calls | 0 / 0 | 0 / 0 |

The six killed workers are excluded from recorded CPU/RSS aggregates; these
are not total-CPU or whole-machine peak-memory claims. CPU instructions and
energy were not measured. The legacy search `model_calls` counter denotes
symbolic policy requests here, not actual model invocations. Equal limits do
not mean equal consumed compute or proof-length optimality.

The native `hydra-development-no-imports-v1` authority is narrower than the
previous Alpha model experiment. The full Alpha-v25 epoch is separately bound
for lineage metadata, not granted as an import capability. These two symbolic
lanes are comparable to each other, not an authority-matched rerun of the
[earlier model experiment](../alpha-v25-posttrain-2026-08-26/README.md).

## Reproduce or verify

From the repository root, independently verify this archived run without
models, training preparations, a GPU, or network access:

```console
python3 scripts/eval_peano_hydra_development.py \
  --verify artifacts/peano-hydra/development-2026-08-27
```

The verifier checks exact file bytes, plan/profile/source identities, the
regenerated benchmark and masks, recorded limits, metrics, policy attribution,
and successful original-goal kernel traces. Implementation hashes must match
the recorded source; a later source change is intentionally rejected. The
archived preparation audits are bound by the plan. Repeating those audits
requires the separately preserved preparation files; proof verification does
not re-audit unavailable training files or establish independent authorship.

To repeat the experiment, use a clean checkout and a fresh output directory:

```console
python3 scripts/eval_peano_hydra_development.py --run \
  --preparation _deploy/hydra-posttrain \
  --preparation _deploy/hydra-posttrain-next \
  --output-dir _deploy/hydra-development-repeat
```

The bundle contains the original [plan](plan.json), [report](report.json),
136 exact `row-NNN.json` records, the successful [verification receipt](verification.json),
and a [checksum inventory](SHA256SUMS). The large plan is evidence metadata,
not a model or a generated proof header. Existing results are never overwritten.

This completes the bounded native DEV protocol/evaluation milestone, **not
H0, H1, H2, or H5**. There is no sealed benchmark, negative-decision authority,
mathematical novelty claim, or demonstrated language-model advantage. See the
[development guide](../../../docs/HYDRA_DEVELOPMENT_EVALUATION.md),
[typed action guide](../../../docs/HYDRA_DEVELOPMENT_PROTOCOL.md), and
[single product roadmap](../../../docs/HYDRA_PRODUCT_ROADMAP.md).
