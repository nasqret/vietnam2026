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

`--catalog-limit` independently replays up to 128 bounded authored proofs
from the current checked theorem DAG. Repeat `--catalog-theorem NAME` to
select particular checked Stable or Alpha results. Every selected theorem
receives exactly its strict earlier direct prerequisites, a fresh bounded
Hydra policy, a newly checked source replay, and a second original-goal kernel
replay. Routes above the current 32-decision search ceiling fail explicitly;
the command never silently truncates a proof or widens theorem authority.

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
