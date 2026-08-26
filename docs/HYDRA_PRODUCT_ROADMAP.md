# Hydra product roadmap: one verified development line

Hydra is the proof-search, proof-improvement, and post-training layer of the
existing Peano theorem library. It is not another prover kernel, another
theorem collection, another definition registry, or another campaign website.
Every accepted result remains an independently checked derivation of its
original first-order Heyting-arithmetic statement.

This document is the current product roadmap. The historical Peano Lab
milestones remain in [`PLAN/09_peano_lab.md`](../PLAN/09_peano_lab.md), the
binding experimental gates remain in
[`PLAN/11_peano_hydra.md`](../PLAN/11_peano_hydra.md) and
[`PEANO_HYDRA_DESIGN.md`](PEANO_HYDRA_DESIGN.md), and the mathematical
frontier remains in
[`PLAN/14_constructive_number_theory_grand_campaign.md`](../PLAN/14_constructive_number_theory_grand_campaign.md).
These are complementary records, not competing product roadmaps.

## Current authoritative baseline

The frozen working release is **Alpha v25**. Its original catalog is
[`catalog-v25.json`](../artifacts/peano-library/alpha/catalog-v25.json);
historical catalogs are immutable.

| Surface | Current state | Authority |
|---|---:|---|
| Theorem proof DAG | **2,080 theorems**, **6,633 proof-dependency edges**, **53 layers** | Independently kernel-checked Alpha v25 proofs. |
| Stable default | **432 theorems** | Unchanged default public proof authority. |
| Explicit Alpha-only extension | **1,648 theorems** | Available only through the explicitly requested, digest-bound Alpha v25 authority. |
| Reviewed definition DAG | **120 definitions**, **214 definition-dependency edges** | Hygienic, conservative, expansion-checked first-order abbreviations. |
| Blueprint notation projection | **179 names**, **165 conceptual edges** | Planning vocabulary only; no definition, proof, or theorem authority. |
| Milestone planning DAG | **144 vertices**, **303 planning edges** | Research scheduling only; open nodes are not proved theorems. |
| Milestone-to-notation links | **395 references** | Presentation links only; never proof prerequisites. |

Alpha v25 preserves every historical v24 proof and adds **29** signed
cofactor/alternating-fold theorems, **19** exact Taylor/formal-derivative and
qualified one-step Hensel theorems, and **24** noncoprime CRT
compatibility/gcd-LCM lattice theorems. Their stronger parent milestones
**T13**, **G095**, and **G011** remain **OPEN**: these 72 checked components
do not establish arbitrary-dimensional determinant/rank/lattice theory,
unrestricted prime-power Hensel lifting, or the full arbitrary
pairwise-compatible noncoprime CRT statement.

Prospective Alpha-v26 candidate, enrollment, or edition source files do not
change this baseline. They become theorem authority only after an independently
checked, dependency-closed, separately sealed release; until then, every Hydra
epoch, browser projection, and model capability remains bound to Alpha v25.

## One theorem DAG and one definition DAG

There are exactly two mathematical graphs that can grow:

1. The **theorem DAG** grows when a new exact statement, its real proof
   prerequisites, and its complete independently kernel-checked certificate
   are admitted through a reviewed immutable Alpha release. Stable promotion
   is a separate explicit decision.
2. The **reviewed definition DAG** grows when a genuinely new abbreviation
   receives a stable identity, checked arity, hygienic exact first-order
   expansion, and acyclic prerequisites in the shared global registry.

The 179-name research blueprint and 144-vertex milestone DAG are derived
planning/presentation surfaces. They are not parallel mathematical
registries, and a blueprint name becomes reusable formal notation only after
its reviewed definition has been admitted or an explicitly compatible alias
has been checked.

Every campaign browser, theorem page, Lean strand, and Hydra dataset must use
those same frozen graphs. Mixed explorers keep their three edge types distinct:

- `proof_dependency`: actual theorem-proof prerequisite;
- `uses_definition`: statement/presentation notation reference; and
- `definition_uses_definition`: conservative-abbreviation prerequisite.

Only `proof_dependency` contributes to theorem reachability, proof critical
paths, or theorem retrieval authority. A notation edge, milestone edge, browser
node, or model suggestion is never a proof premise.

## One explicit proof-authority boundary

Ordinary Peano sessions retain the unchanged 432-theorem Stable default. Hydra
can use the larger checked library only by explicitly requesting the exact
`hydra-alpha-v25-` digest-bound authority. That authority is tied to the sealed
Alpha v25 edition identity and a finite allowed-theorem set; each imported
Alpha theorem is independently replayed against its exact original statement.
Unknown editions, changed digests, nonmembers, unchecked rows, and silently
widened defaults fail closed.

The complete current authority label is:

```text
hydra-alpha-v25-3516d4730428c79fc73aa6fbdbabc43d93921471941bb2f144ea3d29e0af5b28
```

A shortened digest or version name by itself does not grant Alpha access.

The existing WMI Qwen3-1.7B adapter was frozen against its historical
247-theorem authority. It cannot inherit the 2,080-theorem Alpha v25 catalog
merely because that catalog now exists. A model trained for the larger epoch
must receive a newly frozen compatible authority, separately verified data,
and its own independent evaluation.

## Current implemented product

- Provider-neutral symbolic, macro, and control heads have explicit immutable
  identities, fixed quotas, and auditable proposal ledgers.
- Each successful Hydra search is freshly replayed against its original goal
  through the existing independent Peano kernel.
- Dependency-aware campaigns run in bounded deterministic waves; optional
  owner-private checkpoints are replayed, not trusted, when resumed.
- Alpha v25 theorem and reviewed-definition identities are frozen together
  before optimization, discovery preparation, or post-training export.
- Checked traces support three outputs from the same epoch: proof-optimization
  examples, proof-discovery candidates, and replay-verified
  supervised/preference training records.
- All campaign theorem browsers reuse the established proof-explorer design
  and expose the same bounded Lean-strand workflow across **27 proof
  families**, **29 canonical theorem graphs**, and **3,937 eligible staged
  graph/theorem pages**. All **764 checked Alpha exact-edition theorem
  pages** use their paired original checked-use receipts. An import-free
  Lean Live link is shown only after the exact standalone source independently
  compiles; companion-dependent fallback proofs remain honestly labeled
  package exports.

The reproducible entry points are:

```console
make hydra-check
make hydra-prepare
make hydra-scale
make hydra-posttrain-ready
python3 scripts/eval_peano_hydra.py --compact
make lean-public-status
```

`hydra-check` validates the shared Hydra contracts. The original
`make hydra-prepare` freezes the reviewed current epoch and produces the
bounded, verifier-backed initial
training/discovery evidence through
[`scripts/prepare_peano_hydra.py`](../scripts/prepare_peano_hydra.py). Its
local disposable output is:

```text
_deploy/hydra/epoch.json
_deploy/hydra/sft.jsonl
_deploy/hydra/preferences.jsonl
_deploy/hydra/discovery.jsonl
_deploy/hydra/manifest.json
```

Scale the verified catalog-backed curriculum explicitly while preserving the
same epoch and authority:

```console
python3 scripts/prepare_peano_hydra.py \
  --output-dir _deploy/hydra \
  --include-graphs \
  --catalog-limit 32 \
  --catalog-theorem crt_product_witness
```

`--catalog-limit` selects a bounded checked catalog prefix;
`--catalog-theorem NAME` adds an explicitly selected checked theorem. Every
route imports only its exact strict earlier checked prerequisites under the
finite full-digest Alpha allowlist, replays its original source proof, and
independently rechecks the newly produced original-goal proof. At most 128
additional theorem routes were accepted by the earlier prefix-only collector;
the current reviewed limit is **512 additional theorem routes**, each subject to the
32-decision ceiling. The default preparation currently produces **16 verified
supervised transitions** and **one checked preference pair**; these are a
working pilot, not a large-corpus claim.

On the current sealed Alpha-v25 epoch, the explicit 32-prefix-plus-CRT command
above independently checks **33 catalog routes**, exports **279 verified
supervised transitions**, and removes **2 identical transitions**. These are
reproducible bounded preparation counts, not model-training or benchmark
results.

The new whole-catalog mode audits all **2,080** frozen Alpha-v25 theorems and
records distinct eligibility stages instead of treating every short script as
safe to import:

- **978 decision-eligible routes:** **723 Alpha-only** and **255 Stable**
  satisfy the complete 32-decision direct-import-plus-script bound.
- **818 statement-safe routes:** **564 Alpha-only** and **254 Stable** also
  fit the 4,096-byte theorem-statement limit.
- **460 import-replay-safe routes:** **260 Alpha-only** and **200 Stable**
  additionally have bounded, immutable **Stable-only prerequisite closures**.

Automatic whole-catalog selection rejects an Alpha prerequisite before replay
and bounds each Stable prerequisite closure to **256 tactic decisions** and
**8,192 statement bytes**. The complete run reserves no more than **512
routes**, **8,192 tactic decisions**, **512 KiB of retained evidence per
route**, or **24 MiB of aggregate retained route evidence**. Failed attempts
consume their reservation; a skipped route remains classified, not silently
counted as proved. These are deliberate memory-safety boundaries, not claims
that excluded Alpha theorems are unprovable.

Reproduce the larger checked development run with:

```console
python3 scripts/prepare_peano_hydra.py \
  --output-dir _deploy/hydra \
  --include-graphs \
  --catalog-all \
  --catalog-limit 192 \
  --catalog-max-decisions 16
```

This exact Alpha-v25 example independently checks **192 catalog routes**,
including **91 Alpha-only routes**, exports **1,798 verified supervised
transitions**, retains **one checked preference pair** and **one checked
candidate receipt**, and removes **40 duplicate transitions**. The older
**33-route / 279-transition / 2-duplicate** prefix result remains valid
historical evidence; neither collection demonstrates model training or a
measured language-model advantage. `make hydra-scale` selects this same
192-route, 16-decision configuration by default.

Recorded routes first match the entire exact proof state. Their narrowly
scoped fallback alpha-normalizes only engine-generated `?tN` metavariables in
first-visible-occurrence order across the complete ordered goal tuple. It
never renames user variables, changes statements or goal order, alters tactic
or theorem allowlists, or upgrades an unchecked suggestion into proof
evidence; every resulting action and final original goal still pass the same
independent kernel checks. This internal proof-state normalization is not a
mathematical theorem-equivalence or semantic-novelty claim.

These files bind their current theorem/definition epoch and replay evidence;
they neither seal a final benchmark nor admit a new theorem. The teacher-oracle
command is an interface pilot, not a language-model capability measurement.
The Lean command only reports the already-configured public worker's state; it
does not publish a service.

## Proof optimization contract

An optimization begins with an existing checked theorem and its original
certificate. Hydra may propose another tactic route only under the same
canonical goal, frozen theorem epoch, logic mode, and declared resource
envelope. Both routes must independently replay to checked QED.

Rank improvements lexicographically by:

1. fewer public tactic decisions;
2. fewer checked proof nodes;
3. fewer expanded proof-search states; and
4. the exact public command tuple as a deterministic final tie-breaker.

The result is the best **observed independently checked route** within its
declared finite portfolio. It is not a proof of global tactic-decision
optimality. Certificate depth, wall time, and other resource diagnostics may
be recorded separately when actually measured; they are not silently inserted
into the implemented route-ranking key.

A shorter-looking script that changes authority, imports the target theorem,
uses a descendant, hides work in an unrecorded model call, or fails fresh
replay is not an optimization. Existing released proof evidence is never
mutated; an accepted improvement is new reviewed evidence.

## Proof-discovery contract

A discovery candidate must parse as a closed canonical first-order statement,
declare an explicit lineage, and have an **exact source-statement SHA-256**
absent from the frozen theorem epoch. Hydra must construct an acyclic proof
using only earlier admitted theorems, then independently replay that proof
against the exact proposed statement.

The implemented collision policy is `exact_source_statement_sha256_only` and
each candidate explicitly records `semantic_novelty_claim: false`. Therefore
this development pipeline does **not** prove alpha-renaming, definitional,
logical, or mathematical novelty. A stronger canonical-equivalence audit and
independent mathematical review are required before any genuine discovery
claim.

Unsolved attempts remain labeled search evidence. Model prose, an unchecked
candidate file, a graph placeholder, a Lean preview, or a stronger unproved
milestone is not a proof. A renamed/equivalent existing theorem may not be
advertised as mathematically new merely because its source hash differs. Even
a fresh checked proof is only a **reviewed candidate** until its ordinary
dependency-closed Alpha-admission procedure succeeds.

## Post-training contract

Optimization and discovery generate one lineage-aware training stream rather
than separate incompatible products:

- **Supervised transitions:** derive public tactic actions only from complete
  independently replayed original-goal proofs.
- **Preference pairs:** compare two independently checked routes for the same
  goal and exact authority; prefer the genuinely cheaper route.
- **Discovery labels:** mark exact-source-disjoint checked candidate attempts,
  existing-theorem optimizations, partial searches, and failures separately;
  none of these labels establishes semantic mathematical novelty.

Split theorem families, proof dependency components, descendants, normalized
equivalents, and generated variants before expanding tactic rows. Preserve
epoch hashes, model/provider identity, raw-call provenance where available,
and explicit search budgets. Never promote an unfinished trace, failed tactic,
teacher suggestion, or unverified solver result into a positive label.

Deduplicate only identical checked transitions with the same complete key:
`epoch_sha256`, `lineage_sha256`, `state_sha256`, `action`, and
`environment_sha256`. The environment identity preserves the exact logic,
edition, tactic authority, and finite theorem allowlist. Retain the first
deterministically; reject conflicting before/after goals, focus, prompts, or
completions instead of merging them. Record the exact number removed as
`duplicate_transitions_removed` in the manifest. Separate epochs, proof
lineages, states, actions, or authorities never collapse into one example.

Before any model sees a prompt, the Alpha-specific handoff additionally
canonicalizes all four historical model-v3 held-out formulas and quarantines
their **entire proof lineage from both training and development**. In
particular, `triangular_product_even_hydra_candidate` is exactly the
alpha-renamed held-out `consecutive_product_even`; a different theorem name
or source spelling does not make it eligible. The quarantine receipt records
only theorem names, lineage and statement digests, row counts, and exclusion
reasons; it never contains a proof, tactic, prompt, completion, or model
input. Preferences and discovery receipts also remain provenance, not model
inputs. For the historical **279-transition** source, this produces **261
training rows**, **5 development rows**, and **13 quarantined rows**.
For the actual complete **1,798-transition** whole-catalog run, the checked
handoff produces **1,773 clean training rows**, **12 clean development
rows**, and **13 quarantined rows**. Its model-free preflight derives exactly
**222 bounded optimizer steps** without loading model weights or starting
CUDA.

Prepare and inspect the separate Alpha-compatible Qwen handoff locally:

```console
make hydra-scale
make hydra-posttrain-prepare
make hydra-posttrain-preflight
make hydra-eval-plan
make hydra-eval-control
```

`make hydra-posttrain-ready` performs the same ordered scale, handoff,
preflight, and matched-evaluation planning stages, then runs
`--check --symbolic-controls` without starting a model. The genuine fixed
symbolic control independently proves **3 of 4 historical goals** with
**98**, **29**, and **10 proof nodes**, respectively; the induction-dependent
`consecutive_product_even` remains **unknown**. Every control uses **zero
theorem imports** and **zero model calls**. These controls demonstrate
checked model-free plumbing, never pretrained or post-trained model scores.
A default 16-transition
teacher pilot has no second clean lineage after held-out quarantine and is
correctly rejected rather than fabricating a development split. The model
runner consumes only `train.jsonl` and `dev.jsonl`; it updates weights only
through the separately requested `--execute` mode on a verified CUDA host.
A matched pretrained-versus-Alpha-trained evaluation must bind the same model
family and revision, frozen epoch, theorem/tactic authority, held-out goals,
provider evidence, and search budgets. Missing adapter or provider evidence
means **planned/not-run**, never fabricated model scores.

An explicitly authorized Helios execution, if independently requested later,
is split into three separately guarded Slurm jobs:

- `slurm/peano_hydra_alpha_prepare.sbatch`: one **30-minute CPU** preparation
  and evidence-validation job.
- `slurm/peano_hydra_alpha_train.sbatch`: one **2-hour GH200** training job;
  it requires `--afterok` on the exact clean-source preparation predecessor.
- `slurm/peano_hydra_alpha_evaluate.sbatch`: one **1-hour GH200** matched
  evaluation job; it requires `--afterok` on the exact clean-source training
  predecessor.

Each job refuses a dirty or uncommitted source and requires the pinned
offline model cache. Submission itself requires a separate explicit
`--submit --confirm` operation; no local readiness target submits a job,
allocates a GPU, or claims that training has occurred.

The initial replay-verified preparation run is intentionally small. It does
not satisfy the H3 requirement of 100,000 positive transitions from 20,000
checked proof roots, does not seal an H1 benchmark, and does not establish
that Qwen improves proof search or that its teacher-oracle labels represent a
previously unknown mathematical theorem. See
[`HYDRA_POST_TRAINING.md`](HYDRA_POST_TRAINING.md) for the executable data
schema and training boundary.

## The one next engineering milestone

**Scale the replay-verified Alpha-v25 optimization/discovery curriculum under
the explicit digest-bound Alpha authority, then train and compare a new
epoch-compatible policy against its identical pretrained baseline.**

Execute this milestone in order:

1. Run `make hydra-check`, then `make hydra-scale` to freeze the exact
   theorem/definition epoch and expand only bounded independently replayed
   proof traces across both Stable and Alpha membership.
2. Run `make hydra-posttrain-prepare`; quarantine complete held-out lineages
   before creating separate training and development rows, and reject
   contamination, unsafe prerequisites, or an empty clean split.
3. Run `make hydra-posttrain-preflight` and `make hydra-eval-plan`; verify the
   Alpha-compatible model family, exact source lineage, provider requirements,
   identical goal/authority/budget plan, and every still-open research gate.
4. Only when an authorized CUDA host and reviewed pinned model are available,
   explicitly execute Alpha-v25-compatible supervised training; compare any
   resulting attested adapter with the identical pretrained baseline without
   interpreting symbolic controls as model evidence.
5. Admit newly discovered theorems only through the normal reviewed immutable
   Alpha-release procedure; regenerate every browser/Lean projection from the
   same newly sealed theorem and definition DAGs.

The mathematical queue remains dependency-first: unrestricted-dimensional
determinants/rank (**T13**), unrestricted simple-root Hensel lifting
(**G095**), arbitrary pairwise-compatible noncoprime CRT (**G011**), and the
other already-declared ready milestones are targets for the same Hydra
workflow, not alternative product architectures.

## Explicitly unfinished research gates

The production proof-search boundary can be useful before the separate
publication-grade experiment is complete. The full frozen structured macro
protocol, independent semantic/reference conformance campaign, final-set
ownership and sealing, model raw-call/provider attestation, sufficiently large
lineage-clean curriculum, strong frozen symbolic portfolio, and matched-compute
causal evaluation still require their recorded H0–H5 gates.

**H0 is not complete. H1 is not complete. No H5 claim is available. No
language-model advantage has been demonstrated.** A teacher-oracle pilot,
historical four-goal launch smoke, successful public Lean compilation, or
single new checked theorem cannot change those statements.

Operational details remain in
[`training/peano_hydra/README.md`](../training/peano_hydra/README.md),
[`LEAN_PROOF_STRANDS.md`](LEAN_PROOF_STRANDS.md),
[`LEAN_LIVE_INTEGRATION.md`](LEAN_LIVE_INTEGRATION.md), and
[`PUBLIC_LEAN_SERVICE.md`](PUBLIC_LEAN_SERVICE.md).
