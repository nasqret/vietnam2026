# Hydra Alpha-v25: first executed post-training experiment

**Result: the pinned pretrained Qwen base proved 0/4 diagnostic goals; its
new Alpha-v25 adapter proved 3/4. All three learned proofs independently
replayed locally. The fixed symbolic control also proved 3/4.**

This completes the first current-epoch training/evaluation milestone. It
does not establish superiority over symbolic search, broad mathematical
reasoning capability, or a publication-grade result. The fourth goal remains
unknown under the declared bounds. The next step is a broader lineage-clean
development benchmark and a stronger frozen symbolic baseline, as recorded
in the [single product roadmap](../../../docs/HYDRA_PRODUCT_ROADMAP.md).

## What actually ran

The cluster used clean source commit
`a4ed24815925adffd45a5fe40423c2df2cf0a665`, Alpha v25's 2,080-theorem epoch,
and `Qwen/Qwen3-1.7B-Base` at revision
`ea980cb0a6c2ae4b936e82123acc929f1cec04c1`. The old 247-theorem WMI adapter
was not changed. No theorem was admitted, source pushed, or website deployed.

| Stage | Helios job | Actual duration | Result |
|---|---:|---:|---|
| Replay and prepare the 192-route curriculum | 21279955 | 3m 03s | Completed, exit 0 |
| Train one BF16 LoRA adapter on one GH200 | 21279969 | 15m 20s | Completed, exit 0 |
| Run actual pretrained and trained inference | 21280018 | 44s | Completed, exit 0 |

The success-dependent jobs used at most one GPU at a time. Their declared
limits were 30 minutes/8 GiB for CPU preparation, two hours/64 GiB for
training, and one hour/64 GiB for evaluation. Scheduler-reported peak host
memory was about 270 MiB, 6.39 GiB, and 8.52 GiB, respectively; these are
host-memory measurements, not GPU-memory measurements.

An earlier CPU preparation, job **21279542**, also completed successfully.
Helios retained its completed controller record for only 10 seconds, so a
later dependent submission could not reference it. The successful run
repeated preparation and immediately queued all three guarded stages.
`scripts/helios_hydra_chain.sh` now automates that immediate submission while
keeping clean-source, explicit-authorization, and `afterok` checks intact.
The [accounting receipt](scheduler-accounting.psv) and
[owned submission rows](submissions.tsv) retain both CPU runs.

## Data and real weight updates

The source contained **192 replay-checked catalog routes**, including
**91 Alpha-only routes**, and **1,798 verified tactic transitions** after
removing 40 duplicates. The separate model handoff contained:

- **1,773 training rows**;
- **12 development rows**, from a distinct theorem component; and
- **13 quarantined rows**, excluded from both model-facing splits.

The quarantined teacher route is a canonical alias of the held-out
`consecutive_product_even` goal. Its proof, tactics, and prompts were not
training or validation inputs. This is an implemented contamination check,
not a claim that a complete semantic/family-equivalence audit is finished.

Training completed exactly **222 expected optimizer steps**. Every update
boundary had finite raw and clipped gradients; all **392 trainable parameter
tensors changed** and remained finite. Recorded training loss was
**1.112894**, and development loss was **1.061417**. The adapter manifest
retains the pinned package lock, runtime, source/scheduler provenance,
token exposure, step/gradient records, and closed adapter/tokenizer hashes.
The complete portable adapter and tokenizer were collected locally (about
96 MB); no base weights or optimizer checkpoints were copied into this
evidence bundle.

## What the model proved without supplied proof scripts

The actual model provider proposed the following successful command tuples.
Each was replayed against its original goal with **zero theorem imports**,
intuitionistic logic, and the same frozen tactic authority.

| Diagnostic goal | Learned commands | Decisions / proof nodes | Fixed symbolic control |
|---|---|---:|---:|
| `closed_arithmetic_seven` | `norm_num` | 1 / 98 | 1 / 98 |
| `existential_subtraction_two`: `exists x. 7 = x + 2` | `exists 5`; `norm_num` | 2 / 29 | 2 / 29 |
| `double_right_zero`: `forall n. (n + 0) + 0 = n` | `induction n`; `simp`; `simp [IH]` | 3 / 21 | 1 / 10 |
| `consecutive_product_even`: `forall n. exists x. n * (n + 1) = 2 * x` | No proof within the search bounds | Unknown | Unknown |

The pretrained model generated **16 candidate sequences**, all rejected as
malformed tactic output; it executed no tactic. The trained model generated
**88 valid candidate lines**. This result demonstrates improved use of
Hydra's strict tactic interface, not general inability of the base model to
do mathematics or general superiority of the adapter.

Both model lanes had the same maximum depth 16, beam width 4, four candidates
per state, 128 states per goal, 32 model calls per goal, 64 new tokens per
generation, and seed 20260826. Actual generation calls differed: **4 for the
base**, **22 for the adapter**. Matching limits is not matching consumed
compute. The symbolic result is a separate model-free control, not another
model lane or the full frozen research-grade symbolic portfolio.

No optimality claim follows: the learned right-zero proof is longer than the
symbolic route. No discovery claim follows: these are four historical
diagnostic goals, not a newly sealed unseen benchmark. **H0 and H1 remain
incomplete; no H5 or language-model-advantage claim is available.**

## Inspect and independently verify

The small committed evidence files are:

- [Actual matched model evaluation](matched-evaluation.json), including
  commands, proposal evidence, call counts, complete successful replay
  traces, and their digests.
- [Completed training manifest](training-manifest.json), with all weight
  update, dataset, runtime, and model-file bindings.
- [Separate symbolic control](symbolic-control.json). Its model comparison
  correctly remains unmeasured: it was a model-free preparation check, not
  the subsequent executed GPU report.
- [Original source manifest](source-manifest.json),
  [model handoff](preparation-manifest.json), and
  [training configuration](preparation-config.toml).
- [Independent local replay result](independent-replay.json) and its
  [verifier](verify.py).
- [Source provenance](source-provenance.tsv),
  [scheduler accounting](scheduler-accounting.psv), and
  [submission ledger excerpt](submissions.tsv).

From this directory, check the archived file identities:

```console
shasum -a 256 -c SHA256SUMS
```

From the repository root, authenticate the collected model files and freshly
replay every successful model proof without a GPU, network, or model library:

```console
PYTHONDONTWRITEBYTECODE=1 python3 \
  artifacts/peano-hydra/alpha-v25-posttrain-2026-08-26/verify.py
```

This command needs the original `_deploy/hydra-posttrain` preparation and
the locally collected `results/peano-hydra/helios-21279969` directory. Those
disposable data/model directories are not committed. A fresh clone containing
only this small report cannot authenticate absent weight files. The verifier
checks complete adapter/tokenizer file trees, the original evaluation plan,
authorities and budgets, then reproduces the three saved kernel traces and
node counts exactly. It refuses to import Torch. The existing
`independent-replay.json` records that successful verification.

If the original preparation is absent, regenerate its exact bytes before
running the verifier; do not replace another experiment's preparation:

```console
python3 scripts/prepare_peano_hydra.py \
  --output-dir _deploy/hydra --include-graphs --catalog-all \
  --catalog-limit 192 --catalog-max-decisions 16
python3 scripts/prepare_peano_hydra_posttrain.py \
  --source-dir _deploy/hydra --output-dir _deploy/hydra-posttrain
```

The collected model came from
`/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/results/peano-hydra/qwen3-1.7b-alpha-v25-a96223a021ed`
on the configured Helios account. Its exact evaluation is remote
`results/peano-hydra/evaluations/matched-alpha-21280018.json`.
Only the adapter/tokenizer and evidence need collection, not the base model.

## Next corpus: prepared, not trained

The separately checked **460-route** curriculum contains **260 Alpha-only
and 200 Stable routes**, **7,154 verified transitions**, and **90 removed
duplicates**. Its isolated **`catalog-460`** handoff has **7,129 training**,
**12 development**, and **13 quarantined rows**. The CPU-only preflight
passed with **892 planned optimizer steps** and `cuda_initialized: false`.
No second model run was submitted.

The [next source manifest](next-source-manifest.json),
[named preparation](next-preparation-manifest.json),
[configuration](next-preparation-config.toml), and
[preflight receipt](next-preflight.json) preserve these distinct inputs.
Their current local directories are `_deploy/hydra-scale-next` and
`_deploy/hydra-posttrain-next`; the adapter target ends in `-catalog-460`.
Named preparation publication cannot overwrite another run identity or
changed manifest evidence. Only byte-identical regeneration is allowed;
a changed curriculum requires a fresh run ID and output directory.

The training set is larger, but the 12-row development theorem is unchanged.
Broader lineage-clean development coverage, H0 conformance, a stronger frozen
symbolic baseline, and independently owned final-set sealing are still
required. This corpus is also below H3's 100,000-transition / 20,000-proof-root
threshold. The [preparation guide](../../../docs/HYDRA_POST_TRAINING.md#completed-model-run-and-the-next-isolated-curriculum)
gives the exact bounded commands; the standard Helios chain still selects
the original 192-route default and does not silently select this larger run.
