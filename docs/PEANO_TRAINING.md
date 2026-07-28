# Peano Lab post-training experiment — M19 research protocol

**Status:** binding experiment protocol, 2026-07-28.  Results are not filled in
until the corresponding artifacts exist and have passed the independent
kernel.  This document extends M9; it does not weaken any Peano Lab trust rule.

## 1. What changed after M9

M9 deliberately stopped at data and an evaluator.  The repository said “no
training” because no model experiment had then been authorized.  The project
owner has now explicitly requested a reproducible post-training experiment on
Helios, using models below ten billion parameters.  M19 is that new scope.

The original priorities remain ordered:

1. soundness;
2. clarity;
3. pedagogy;
4. extensibility;
5. efficiency.

In particular, a model never becomes part of the trusted computing base.  It
may emit only public Peano Lab tactic text.  The engine may construct a
certificate, but only the unchanged independent kernel may accept QED against
the separately retained original theorem and exact logic mode.

## 2. Research questions and stopping rules

The experiment asks four separate questions:

1. Can a small decoder predict useful **next tactics** in Peano Lab?
2. How much does verifier-guided best-first search improve over greedy or
   independent whole-script sampling at the same token and kernel-call budget?
3. Does a formal-prover prior transfer better than a general code/mathematics
   base model of the same size?
4. Can a still smaller policy retain most of the solve rate and become a cheap,
   token-efficient explorer?

The first pilot is not allowed to drift into a ten-billion-parameter run merely
because a smaller run disappoints.  It starts with `Qwen/Qwen3-1.7B-Base`, then
compares two four-billion-parameter models under the same data and LoRA budget:

- `Qwen/Qwen3-4B-Base` for a clean Peano-specific baseline;
- `Pythagoras-LM/Pythagoras-Prover-4B` for a same-family formal-proving prior.

Both model cards identify Apache-2.0 weights.  Pythagoras is a June 2026
preprint/checkpoint, so its reported Lean numbers are treated as authors'
claims, not as established Peano results.  An eight-billion model is a later
ceiling experiment, not a pilot default.  DeepSeek-Prover-V2-7B remains a
scientific reference but its custom model license must be reviewed before it
becomes a released artifact.

Stop or redesign if any of these occurs:

- a positive example cannot be replayed to kernel-checked QED;
- train/test lineage is ambiguous;
- the model can import the held-out target or call an unreported built-in
  solver;
- a run lacks exact model, tokenizer, data, source, configuration, and
  environment hashes;
- a 500-step smoke cannot resume and reproduce its evaluation;
- the random, deterministic-tactic, or pretrained baselines are missing.

## 3. Three tasks, three metrics

M19 does not blur formalization and proving into one score.

### 3.1 `peano-policy` — the primary artifact

Input: a canonical list of current goals and one fixed environment identity.

Output: exactly one complete Peano Lab tactic line and end-of-sequence.  No
analysis, Markdown, certificate syntax, theorem claim, mode change, or `qed` is
accepted.

Primary metrics: independently checked pass@1/4/16 at fixed verifier and token
budgets; solved theorems per generated token, kernel call, and second; proof
nodes/depth; and duplicated search states.

### 3.2 `peano-formalizer` — a later separate adapter

Input: a controlled natural-language arithmetic statement.

Output: one canonical closed Peano Lab formula.

Templated synthetic pairs can be judged by exact formula AST.  Human-written
statements require expert semantic review.  A kernel can prove the emitted
formula; it cannot certify that the formula faithfully means the English
sentence.  Finite testing and round trips are rejection filters, never
faithfulness proofs.

### 3.3 `peano-planner` — optional after the policy baseline

Input: a canonical state at a genuine branch point.

Output: one proposed proposition for `have` or `suffices`.  The ordinary policy
must still prove both resulting obligations.  This isolates invariant/lemma
invention from routine leaf closure and makes the analogy with AlphaGeometry's
learned auxiliary constructions explicit.

## 4. Our prompt, not a vendor prompt

The base-model completion format is deliberately small and project-owned:

```text
<task>next_tactic</task>
<env>peano-lab-v1;surface=model-v1;logic=intuitionistic;capability_sha256=ENVIRONMENT_SHA256</env>
<state>{"focus":0,"goals":["n : ℕ, IH : 0 + n = n ⊢ 0 + S n = S n"]}</state>
<tactic>
```

The stored supervised completion is one physical tactic line followed by the
literal delimiter `</tactic>`, for example `simp [IH]</tactic>`.  The training
loader checks that envelope, strips the delimiter, and supervises exactly the
tactic tokens plus the tokenizer EOS token; prompt tokens are masked from the
causal-language-model loss.  Multiple goals occupy the JSON `goals` array in
their exact canonical order.  Version 1 always renders input `focus` as zero:
the trace focus is derived from the submitted action, so feeding it back would
leak part of the label.  The theorem's hidden family name, source spelling,
certificate, and held-out label never enter the policy prompt.

The tokenizer vocabulary is not modified in the first run.  Before training,
each candidate tokenizer is audited on exact UTF-8 round trips and token
fertility for Peano states, theorem formulas, and tactics.  ASCII aliases may
be studied as an ablation, but one run never silently mixes two printers.

## 5. The headless verifier boundary

`peano_lab.batch` and `scripts/peano_batch.py` are a compact adapter around the
existing prover, not a compact replacement prover.  They import and reuse:

- `parse_formula_with_names`;
- `ProofState.start` and the production `ProofSession` owner;
- the public `run_surface` tactic grammar;
- checked library replay and capability checks; and
- `checked_surface_final`, which submits the completed certificate to the
  independent kernel with the owner-retained original theorem.

The JSONL process imports Python once and starts one fresh proof owner per
request.  Browser panels, DOM/Pyodide routing, and certificate pretty-printing
are absent.  It is a finite file transaction rather than a duplex service:
results appear only after EOF and, in generation mode, after the trace commits.
Default aggregate limits are 10,000 requests, 256 MiB input, 128 MiB results,
and 512 MiB trace, so larger jobs must be deliberately sharded or opt into
reviewed limits.  Generation/search mode retains the binding v1 success and
failure trace.  A separately named verification-only mode may omit transition
rendering when checking already-authored scripts; it does not define training
data.

Raw traces and result envelopes are separate streams.  This is essential:
`scripts/export_traces.py` accepts only contiguous nine-field tactic records
followed by one four-field footer.  A successful response is issued only after
the same original-target kernel check as the browser.  A kernel rejection is a
fail-stop soundness alarm.

The trace hard link is the transport's commit point.  Cancellation before it
publishes no final trace.  Cancellation after it may preserve the complete
committed trace even when stdout is absent or partial; the trace remains a
valid replay artifact, while the caller must discard or reconstruct the result
stream.  Redirect stdout through a caller-owned temporary file when atomic
publication of `results.jsonl` is also required.

The compact transport consumes one strict request per input line, so a single
Python process can check a long stream without paying interpreter or browser
startup for each proof:

```json
{"v":1,"id":"zero-add","theorem":"forall n. 0 + n = n","tactics":["induction n","simp","simp [IH]"]}
```

```console
python3 scripts/peano_batch.py --environment model-v1 \
  --trace-output /tmp/peano-run.trace.jsonl \
  < requests.jsonl > results.jsonl
```

Use `--verify-only` only for fast filtering or regression of already-authored
scripts; it produces no training trace.  Python generators can avoid even the
JSON transport and call `peano_lab.batch.run_proof(...)` directly.  That
function is still the same traced public-surface and final-kernel path.
By default, exit zero means the finite protocol completed; individual proof
statuses remain in their result rows.  Add `--require-proved` for CI or replay
jobs that must return exit one when any executed proof remains open or fails.

The runner configuration, not model-generated JSON, fixes the tactic and
theorem capability set.  Benchmark environment `model-v1` excludes `auto`,
`undo`, session commands, and every held-out target theorem.  All held-out
goals expose the same fixed foundation library, so theorem availability is not
a hidden per-problem variable.  Nested tacticals are compiled under the same
capability object and cannot smuggle a forbidden leaf.

## 6. Positive data must survive replay

The raw v1 stream is retained unchanged.  A separate versioned training
envelope adds research metadata:

```json
{
  "v": 1,
  "task": "next_tactic",
  "env": "peano-lab-v1;surface=model-v1;logic=intuitionistic;capability_sha256=...",
  "environment_sha256": "...",
  "session": "...",
  "family": "addition_induction",
  "lineage": "addition_induction/zero_left/seed-17",
  "split": "train",
  "formula": "∀ x. 0 + x = x",
  "state": ["⊢ ∀ x. 0 + x = x"],
  "focus": 0,
  "prompt": "...<state>{...}</state>\n<tactic>",
  "completion": "induction x</tactic>"
}
```

The actual version-1 row also redundantly records the exact capability
preimage, logic mode, surface, authored theorem label, and extra generator
metadata.  The builder validates canonical field order and re-renders every
stored prompt from those fields before training accepts it.

An example is positive only if all of the following hold:

1. its raw session ends in `qed: true`;
2. the complete ordered successful tactic sequence replays through the current
   public surface;
3. finalization independently checks the rebuilt certificate against the raw
   footer theorem;
4. every replayed before/after state equals the raw canonical state;
5. its family and lineage metadata are complete; and
6. its entire lineage was assigned to one split before transition rows were
   expanded; and
7. every session with the same canonical theorem formula was joined to the
   same split component, even if generator metadata accidentally named a
   different family or lineage; and
8. every pair of sessions sharing an exact rendered policy prompt was joined
   to the same component, even if their original theorems and genealogy differ.

`qed: false` sessions and successful prefixes of unfinished sessions never
become positive cross-entropy targets.  Failed tactic records are retained for
later ranking/DPO data only.  The current 13,344-row M18 release is a pipeline
bootstrap, not a sufficient training corpus: it has only three families, an
18-row validation split, and heavy tactic imbalance.  Its 1,500 randomized
surface binder names can assign different invisible introduction names to the
same canonical state.  M19 preserves the exact authored action and permits a
row only when executing that exact action recreates the stored successor
state.  Scalable schemas prefer bare `intro` where naming is irrelevant and
standardized visible names where later lines refer to them; they do not create
alpha-renaming augmentation at an otherwise identical invisible-binder state.

### 6.1 First frozen M19 release

The committed `data/peano-policy-v1/` release is the first scale checkpoint,
not a claim that the curriculum is complete.  A proof-first generator created
2,522 distinct checked sessions from 29 schemas in five domains: logic,
equality, PA recurrence, witnesses, and arithmetic.  Replay compilation yields
exactly 10,000 positive next-tactic rows:

| Split | Rows |
|---|---:|
| train | 8,149 |
| validation | 926 |
| test | 925 |

Its dataset SHA-256 is
`1fa98caa2e0528d39c1b9003c4ee153dfbe633cb1ee4505e8f5b28eb837465dd`.
The independent attestor checks raw artifact hashes, the current Peano source
inventory, the fixed capability preimage, canonical-formula and exact-prompt
split separation, and held-out-target exclusion.  It then runs the current
replay compiler from the raw traces in a fresh directory and requires
byte-identical split files.
The release passes that replay and contains zero instances of the four frozen
held-out targets.

This remains a deliberately modest smoke dataset.  It does not yet provide a
large induction curriculum, natural-language formalization examples, negative
preference pairs, or a statistically useful whole-family out-of-distribution
benchmark.  Those limitations must not be hidden by the exact row count.

## 7. Synthetic curriculum and genealogy

Generation is schema-driven.  Every seed theorem receives a stable
`family`, `template`, `lineage`, generator version, and parent list before any
renaming, commutation, substitution, paraphrase, or alternative proof is made.
All descendants stay in the seed's split.

A later 100k–300k positive state/action release should expand coverage, rather
than merely repeat the first 10,000-row checkpoint:

- logic and context management: `intro`, `exact`, `apply`, conjunction,
  disjunction, cases, quantifiers, and explicit witnesses;
- equality and capture-safe rewriting in both orientations;
- PA3–PA6 instances and congruence;
- induction with base/step states, strengthened invariants, and induction
  hypotheses;
- addition/multiplication identities, order, parity, divisibility, and
  existential witness families;
- polynomial and closed-numeral leaves for `ring`, `norm_num`, and
  `compact_arith`;
- explicit theorem reuse, specialization, `have`, and `suffices`; and
- deliberately failed nearby actions for preference/ranking data.

Difficulty is a vector, not proof length alone: accepted tactic count, search
expansions, verifier calls, certificate nodes/depth, automation used, formula
AST size/depth, and whether an invariant/witness/local lemma was required.

## 8. Leakage-safe benchmark

Protocol v3 keeps four literal library-tail goals (`le_trans`, `le_antisymm`,
`le_total`, and `mul_eq_zero`) but fixes a capability-scoped environment.  The
target theorem itself is never importable; `auto` is unavailable; a single
reported foundation set is shared by all four goals.  The goal-set hash covers
the statements, exact logic modes, surface profile, and allowed theorem names.

That four-goal set remains a regression benchmark, not a statistically useful
final test.  M19 also freezes 300–1,000 generated problems before serious
training, with separate views for:

- IID held-out lineages;
- held-out theorem families;
- larger formula/proof depth;
- unseen lemma compositions and witnesses; and
- a small human-authored statement set.

No training, prompt, retrieval index, tokenizer fit, checkpoint choice,
temperature, search width, or stopping budget is tuned on the final test.
Report bootstrap confidence intervals and all per-family outcomes.

Baselines and ablations are mandatory:

- deterministic Peano tactics alone;
- untrained/pretrained model;
- SFT greedy and sampled pass@k;
- SFT plus best-first search;
- one or more expert-iteration rounds;
- with/without deterministic arithmetic closers;
- 1.7B versus 4B under fixed verifier/token budgets; and
- general base versus same-size prover prior.

## 9. Training and search stages

### Stage 0 — infrastructure smoke

Audit tokenizer round trips; run 100–500 optimizer steps on a tiny checked
dataset; save, reload, resume, and generate one tactic; then evaluate the
checkpoint through the real kernel boundary.  This stage exists to find data,
ARM, dependency, masking, and checkpoint bugs—not to produce a headline.

### Stage 1 — supervised policy

Use BF16 LoRA, PyTorch SDPA, completion-only loss, deterministic seeds, packed
1–2k-token sequences, and one to three epochs chosen by validation kernel
success rather than training loss.  On a 96GB GH200, ordinary BF16 adapters are
preferred to QLoRA so the initial run does not depend on quantization-specific
ARM wheels.  Full fine-tuning is reserved for the 1.7B scaling check.

### Stage 2 — verifier-guided expert iteration

The policy proposes complete tactic lines.  Peano Lab executes each line
transactionally, hashes the canonical successor state, and deduplicates the
frontier.  The initial best-first priority is accumulated negative log
probability plus a documented depth penalty.  Every run has hard caps on model
tokens, tactic proposals, unique states, kernel calls, wall time, and generated
certificate size.

Deterministic closers may run at compatible arithmetic leaves.  The model
spends probability on branching choices such as induction variables,
invariants, witnesses, rewrite direction, theorem specialization, and local
lemmas.  This division of labour is the transferable AlphaGeometry lesson.

Only final-kernel-checked trajectories enter the next positive round.  Prefer
smaller certificates while retaining a bounded number of structurally diverse
proofs.  Rebuild a clean adapter from the accumulated verified set as an
ablation against continual training.

### Stage 3 — preference or RL, only if justified

Same-state accepted productive tactics and executed failures/dominated
successors form ranking pairs.  DPO/ranking precedes online RL.  A later GRPO
run receives terminal reward one only for independent QED against the original
goal and zero otherwise.  Any compactness reward is conditional on QED and
small enough not to reward goal-count tricks.  Seed SFT replay prevents policy
collapse.

## 10. Helios execution contract

The selectively adapted SAIR Helios tools provide operational patterns only;
that repository contains no `SKILL.md` or prompt package.  Peano Lab uses its
own prompts above and current project settings:

- SSH: `plgnasqret@helios.cyfronet.pl`;
- grant: `plgccaiautore2026`;
- GPU account/partition: `plgccaiautore2026-gpu-gh200` /
  `plgrid-gpu-gh200`;
- fixed project root: `$SCRATCH/codex-control/projects/peano-lab-training`;
- current module baseline: `ML-bundle/25.10`, whose pinned ARM wheel directory
  supplies `torch==2.9.1+cu129` but whose module alone does not install Torch; and
- one GH200 job at a time during the pilot.

Preparation clears and recreates an isolated `.venv-helios/`, installs the
complete version-pinned Python lock with `--no-deps --only-binary=:all:`, and runs
`pip check` before model download or a LoRA step.  This deliberately avoids
leaking cluster or failed-run site packages into the experiment.  Scheduled
runs also replace, rather than extend, inherited `PYTHONPATH`, disable the user
site, and assert the exact Torch/CUDA build.  Versions and the resolved runtime
inventory are recorded; without `--require-hashes`, this is not yet a
byte-identical wheel-reproduction claim.  Sync protects
`.venv-helios/`, the Hugging Face cache, `checkpoints/`,
`results/`, and all scheduler logs including the submission ledger.  Local and
remote wrappers default to `sbatch --test-only`; real submission requires the
explicit `PEANO-LAB-TRAINING` confirmation token.  Every submission records
job ID, timestamp, local git commit, dirty-worktree flag, sync timestamp,
job-script hash, and work directory.  The remote mirror intentionally omits
`.git`; a small validated sync-provenance record supplies those source facts.
No result
is reported until the corresponding scheduler log, manifest, checkpoint, and
kernel evaluation artifact have been collected.

The trainer performs the independent dataset attestation before importing a
model or creating the output directory.  A completed adapter stores every
loader-visible weight/config file and tokenizer file in separate closed
directories and hashes the complete directory contents.  Evaluation verifies
those closed sets and reconstructs its surface authority from the training
attestation; it does not substitute a hard-coded allowlist that could conceal
training under a more powerful environment.

The first correctness stack is the Helios/NVIDIA ARM PyTorch environment plus
Transformers, PEFT, TRL/Accelerate, BF16, and SDPA.  FlashAttention, vLLM,
DeepSpeed, and bitsandbytes are optional measured optimizations, never smoke
dependencies.  A job must first confirm `aarch64`, CUDA availability, BF16,
one forward/backward step, adapter reload, tokenizer round trip, and Peano
kernel multiprocessing.

Preparation job `20029964` passed that full gate on 2026-07-28 from clean commit
`41683e24358f5ce42e357ff3be6300aa233620e4`. Its attested runtime was Python
3.13.5, `torch==2.9.1+cu129`, CUDA 12.9, and one NVIDIA GH200 120GB. The exact
Qwen3-1.7B model/tokenizer revision resolved to the requested commit, both the
training and reloaded losses were finite, and the closed adapter/tokenizer
artifact hashes were recorded. This is an environment and one-step LoRA smoke,
not a trained-policy result; the 100-step training job remains scheduler work.

### 10.1 WMI A100 replication path

WMI is a second execution site, not a substitute provenance label for Helios.
The [official WMI resource table](https://cluster.wmi.amu.edu.pl/02_02_zasoby_klastra.html)
documents one four-GPU NVIDIA A100 80GB node. Live Slurm inspection on 2026-07-28
confirmed node `g3n1`, partition `gpu_csi`, feature `vram80g`, and the owner's
`hw_csi` access. `gpu_csi` is the preferred non-preemptible route; `gpu_spot`
and `gpu_idle` are not used for the initial run because the current trainer does
not yet implement the site's requeue/checkpoint signal contract.

WMI is x86-64 and its documented runtime differs from Helios. The read-only
probe requested exactly one typed `nvidia_a100` GPU for five minutes, loaded
`anaconda/2025.12-1`, activated the central `pytorch-gpu` environment, and
required Python 3.12, PyTorch 2.5.1, CUDA 12.4, one visible A100, at least 75
GiB VRAM, BF16 support, and a finite BF16 matrix forward/backward pass. Job
`171369` passed in 13 seconds on an A100-SXM4-80GB with driver `610.43.02` and
reported 18 TB free under `/work`. The diagnostic installed nothing.

The follow-on runtime is site-specific and closed in two layers. A reviewed
central-base manifest pins Python, `ensurepip`, Torch/CUDA, NumPy, Triton,
vision/audio, and their exact dependency versions. A separate 12-distribution
overlay pins every accepted CPython-3.12 x86-64 wheel by SHA-256 without
replacing central Torch, NumPy, Triton, CUDA, torchvision, or torchaudio. The
environment identity hashes both contracts, every overlay distribution must
resolve under the immutable release, and the active pointer must match the
currently revalidated base.

WMI source publication is transactional. `git archive` excludes ignored and
uncommitted files; the receiver reconstructs and compares the exact Git tree
before publishing. Source-dependent preparation, training, and evaluation jobs
hold a shared deployment lock; sync holds the exclusive lock, and provenance is
invalidated before any live-tree change.
Preparation publishes the environment pointer only after package checks,
independent data attestation, a real BF16 LoRA step, safetensors save/reload,
and finite losses all pass. The ARM Helios lock and `.venv-helios` are never
reused or relabeled. Preparation job `171395` passed this complete gate in
8m39s from commit `95197e9`: dataset digest `1fa98caa…` replayed exactly, the
runtime report recorded finite losses `6.06434` and `5.53506` before and after
reload, and only then did the environment pointer move. Its first dependent
training submission was refused before `sbatch` because Bash whitespace
splitting collapsed the empty dependency column in the TSV ledger. The
controller now delegates that boundary to a bounded strict UTF-8 nine-field
parser. The fix changes source identity, so a fresh preparation job is required
before training; no WMI learned result is claimed yet.

### 10.2 Proving a new theorem with a trained adapter

After a training manifest and final adapter have passed their artifact checks, the same evaluator
can search one user-supplied closed PA formula:

```console
python3 scripts/eval_trained_peano_policy.py \
  --adapter results/peano-policy/qwen3-1.7b-lora-wmi-smoke \
  --theorem 'forall n. exists x. n * (n + 1) = 2 * x' \
  --sample --k 16 --max-steps 24 \
  --output results/peano-policy/manual-proofs/even-product.json \
  --proof-output results/peano-policy/manual-proofs/even-product.pa
```

Custom-theorem mode is intentionally narrower than the browser's complete teaching surface. It
reconstructs the exact intuitionistic `model-v1` command and seven-theorem authority from the
adapter's independently replayed dataset attestation. The caller cannot enable `auto`, classical
logic, another theorem library, or a wider command set. The formula must be one closed,
control-free line within the same parser and numeral bounds as the headless prover; this preflight
happens before the model is loaded. More than one rollout requires `--sample`, so `--k 16` cannot
silently repeat the same greedy trajectory sixteen times.

The generated model remains untrusted twice over. Each rollout reaches `proof` only after the
evaluator checks its certificate against the externally retained original formula. The smallest
successful rollout is then replayed from scratch under the same capability object through the
headless verifier. Only a second `status=proved`, `kernel_checked=true` result may create
`result.pa`. The script is ordinary pasteable Peano Lab input, not a privileged certificate:

```text
pa prove <canonical closed formula>
<generated tactic 1>
...
qed
```

The JSON report retains every attempt, adapter/decode/source/job provenance, the chosen sample,
proof-node count, exact commands, replay environment hash, script text, and script SHA-256. Neither
output path is overwritten. Repository-local outputs are confined to `results/`, outside source
and the adapter's closed weight/tokenizer trees. No checked proof means exit status 1, a report with
`proof_publication.status = "no-proof"`, and no `.pa` file. At present this command runs where the
adapter and PyTorch GPU environment live; it is not yet a browser inference service or an
English-to-PA formalizer.

On WMI, do not paste the bare Python command into the login node or an ad-hoc `srun`: accepted
runtime and submission-ledger provenance exist only inside an allowlisted job. From the local clean
checkout, create and submit a request with:

```console
scripts/wmi_prove_theorem.sh \
  --submit --confirm PEANO-LAB-WMI-TRAINING \
  --theorem 'forall n. exists x. n * (n + 1) = 2 * x' \
  --sample --k 16 --max-steps 24
```

The wrapper validates the formula and total call budget locally, creates a nonce-bearing canonical
JSON request, streams it under the WMI deployment lock, and exports only its 64-hex SHA-256 ID to
Slurm. The guarded submitter revalidates and hashes the request, appends both the ordinary job row
and an immutable request/job ledger row before releasing one typed-A100 job. The compute job
rechecks the central base, overlay, source, scheduler row, request bytes, adapter, and kernel path.
It writes digest-named report, optional `.pa`, and terminal run-summary files under
`results/peano-policy/user-proofs/`; a sound but unsolved request finishes with `status=no-proof`
rather than masquerading as an infrastructure crash. The wrapper prints the request ID used in
those filenames.

## 11. Provenance and result ledger

Each published run records:

- git commit and dirty-tree status;
- kernel checker and full semantic-source-tree SHA-256;
- raw trace, metadata, split, prompt, and tokenizer hashes;
- model repository/revision, weight/config/tokenizer hashes, and license;
- complete hyperparameters, seeds, package versions, architecture, CUDA, GPU,
  Slurm job ID, elapsed time, and resource accounting;
- checkpoint and generation-adapter hashes; and
- fixed-budget evaluation JSON with every attempted tactic sequence.

Training loss is not a theorem-proving result.  The result chapter must state
exactly which stages ran, which were only designed, and which claims are
inferences.  A model checkpoint is useful only insofar as fresh executions
produce certificates that the independent kernel accepts for their original
goals.

## 12. Research precedents

The design borrows principles, not prompts or unreported infrastructure:

- [AlphaGeometry](https://www.nature.com/articles/s41586-023-06747-5): a
  learned auxiliary-construction policy paired with deterministic deduction
  and large synthetic data;
- [AlphaGeometry 2](https://www.jmlr.org/papers/volume26/25-1654/25-1654.pdf):
  heterogeneous searches and shared proved facts;
- [AlphaProof](https://www.nature.com/articles/s41586-025-09833-y): formal
  verifier feedback, a policy/value loop, and frontier curricula, but at a
  compute scale and release level this experiment does not claim to reproduce;
- [DeepSeek-Prover](https://arxiv.org/abs/2405.14333) and
  [V1.5](https://arxiv.org/abs/2408.08152): synthetic formal statements,
  verifier feedback, and search/expert iteration;
- [LeanDojo/ReProver](https://proceedings.neurips.cc/paper_files/paper/2023/file/4441469427094f8873d0fecb0c4e1cee-Paper-Datasets_and_Benchmarks.pdf):
  canonical state-to-tactic prediction and best-first proof search; and
- [DeepSeek-Prover-V2](https://arxiv.org/abs/2504.21801): separating lemma
  planning from a smaller prover and measuring the token cost of long
  reasoning traces.

Peano arithmetic is much narrower than Lean/Mathlib.  The experiment therefore
tests whether data lineage, capability-scoped search, and a cheap kernel matter
more than parameter count.  That is the pedagogical point as well as the
engineering hypothesis.
