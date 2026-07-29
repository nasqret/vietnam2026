# Peano Lab post-training experiment — M19 research protocol

**Status:** binding experiment protocol with the first accepted WMI model-v1 result, the historical
model-v2 launch stack, and the implemented model-v3 successor recorded, 2026-07-29. Model-v3 binds
the complete 247-theorem ladder and corrects the curriculum and leakage contract described below.
It has not yet produced a trained checkpoint or theorem-proving result; its proof quality is
unknown. Result fields are filled only after the corresponding artifacts exist and successful
scripts have passed the independent kernel.
This document extends M9; it does not weaken any Peano Lab trust rule.

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

The experiment is not allowed to drift into a ten-billion-parameter run merely
because a smaller run disappoints.  Model-v2 starts with the pinned
`Qwen/Qwen3-1.7B-Base` heavy configuration.  Two four-billion-parameter
candidates remain defined for a later controlled comparison:

- `Qwen/Qwen3-4B-Base` for a clean Peano-specific baseline;
- `Pythagoras-LM/Pythagoras-Prover-4B` for a same-family formal-proving prior.

Both model cards identify Apache-2.0 weights.  Pythagoras is a June 2026
preprint/checkpoint, so its reported Lean numbers are treated as authors'
claims, not as established Peano results.  The 4B comparison is explicitly
deferred until the 1.7B model-v2 corpus, training run, and kernel-judged
evaluation establish a baseline.  An eight-billion model is a later ceiling
experiment, not a pilot default.  DeepSeek-Prover-V2-7B remains a scientific
reference but its custom model license must be reviewed before it becomes a
released artifact.

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

The frozen model-v1 completion format is deliberately small and project-owned:

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

Model-v2 keeps the same one-line completion boundary but adds two observation
channels before `<state>`: the exact compact tactic grammar and a deterministic
retrieval block.  Its public source catalog contains 63 ordered entries and has
root `d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0`.
The model-v2 library has two deliberately different identities:

- the **full checked identity** is the authority record for all 56 permitted
  theorems.  For each theorem it binds the canonical statement, dependencies,
  source-spec hash, authored-script hash, independently checked expanded
  certificate hash, proof nodes, and proof depth.  Its SHA-256 is
  `3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439`;
- the **prompt projection** is the sorted name/canonical-statement view used for
  retrieval over those same 56 records.  It has its own statement-projection hash, while each prompt
  contains only eight deterministically retrieved `name : statement` records
  plus the full checked-identity hash.

The prompt projection is useful model context, never an attestation substitute.
Dataset, adapter, evaluator, and interactive inference authority is derived
from the full 56-theorem checked identity.  The four benchmark goals are
`le_trans`, `le_antisymm`, `le_total`, and `mul_eq_zero`.  All four are excluded
from generated targets.  Import sealing additionally follows reverse dependency
edges: `mul_ne_zero` and `two_large_factors_impossible` depend directly on
`mul_eq_zero`, and `prime_two` depends on it transitively through
`two_large_factors_impossible`.  Those seven names are absent from both library
identities and cannot be retrieved or imported.  The evaluation set therefore
still has four goals; the import-exclusion closure has seven entries.

Model-v3 retains the one-line completion boundary but replaces the fixed model-v2
authority with the complete declaration-ordered 247-theorem checked identity. For
the library trajectory targeting theorem $i$, its prompt and executable capability
contain exactly `THEOREMS[:i]`: the current theorem and all later theorems are
unavailable. The trajectory imports declared direct dependencies with ordinary
`use` commands, then executes the theorem's authored script unchanged. Every
certificate is reconstructed and independently checked from the empty context;
the dataset compiler replays each resulting QED before emitting rows.

Prompt v3 includes a compact inventory of every allowed theorem name in that exact
prefix and retrieves at most twelve detailed `name : statement` records. Retrieval
scores full canonical propositions deterministically, while a large displayed
statement is replaced by a bounded canonical excerpt carrying a content marker. A
coverage audit explains the two layers: $K=12$ statement retrieval alone exposed
only 242 of 640 direct-dependency `use` labels. The complete name inventory keeps
all legal dependencies selectable without placing every full proposition in every
prompt. The environment still binds both the full 247-theorem identity and the
exact prefix digest, so a compact observation cannot weaken or disguise proof
authority.

The tokenizer vocabulary is not modified.  The historical model-v2 token-audit gate
loads the exact pinned tokenizer revision and checks every selected train and
validation example with the configured 2,048-token budget.  It rejects rather
than truncates, requires an EOS token and exact resolved revision, hashes the
tokenizer/config/input files, and reports minimum, median, p95, p99, maximum,
mean, and remaining headroom.  Both Helios and WMI preparation paths run this
gate offline before a training job may consume GPU time.  ASCII aliases may be
studied as an ablation, but one run never silently mixes two printers.

Model-v3 applies the same no-truncation rule at Qwen3-1.7B's pinned native
32,768-token position limit over every selected train and validation sequence.
An exact root-probe audit already found 57 of 247 full-prefix theorem prompts
above 4,096 tokens (maximum 6,235), so the smaller draft ceiling was invalid.
Any native-limit violation aborts preparation; no prefix, state, retrieval
record, or completion may be silently clipped.

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
reviewed limits. Ordinary proofs retain the binding 16 MB per-session trace
ceiling. The exact model-v3 library generator uses the documented reviewed-limit
escape hatch: a host-owned Python keyword raises that one session ceiling to a
hard maximum of 128 MiB. This does not change the JSONL transport's independent
512 MiB aggregate default, and the JSON request schema cannot select the
override. Generation/search mode retains the binding v1 success and failure
trace. A separately named
verification-only mode may omit transition
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

The implemented model-v2 generator raises the checked positive ceiling to
exactly 100,000 transition rows.  It schedules complete proof sessions in
three deficit-balanced lanes with a row ratio of
**foundation : induction : library = 2 : 1 : 1**.  A session is accepted
atomically only after the ordinary public surface reaches independently
kernel-checked QED; no proof is cut merely to hit a lane quota.  The generated
curriculum expands coverage rather than merely repeating the first 10,000-row
checkpoint:

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
- explicit coverage of every one of the 25 permitted tactic heads and every
  one of the 56 allowed theorem imports.

For any run of at least 10,000 rows, publication fails if even one tactic head
or permitted theorem import is absent.  The four held-out theorem names and
canonical statements are excluded before target generation; the complete
seven-name reverse-dependency closure is excluded from retrieval and imports.
A deterministic pre-reconciliation capacity exercise under the former
45-import authority filled 100,000 rows with 50,002 foundation, 25,000 induction,
and 24,998 library rows from 22,706 distinct checked roots.  That historical
exercise demonstrates the scheduler mechanics, not capacity under the current
63-entry catalog and 56-import identity.  The current corpus must be regenerated
and re-attested before the heavy run, and its exact lane/root counts must come
from that new attestation.
Actually executed failures remain a separate future ranking/value corpus and
are never relabelled as positive SFT examples.

Difficulty is a vector, not proof length alone: accepted tactic count, search
expansions, verifier calls, certificate nodes/depth, automation used, formula
AST size/depth, and whether an invariant/witness/local lemma was required.

## 8. Leakage-safe benchmark

Protocol v4 keeps four literal library-tail goals (`le_trans`, `le_antisymm`,
`le_total`, and `mul_eq_zero`) but fixes a capability-scoped environment.  The
target theorem itself is never importable; `auto` is unavailable; a single
reported foundation set is shared by all four goals.  The goal-set hash covers
the statements, exact logic modes, surface profile, and allowed theorem names. Version 4 also
binds the evaluator's semantic source set and complete runtime identity into every report.

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

### Stage 2 — bounded verifier-guided search; expert iteration later

The search layer is implemented.  At each immutable canonical state the policy
returns a bounded ranked tuple of complete tactic lines.  Each candidate edge
is replayed from the original theorem in a fresh `ProofSession`; a rejected
sibling therefore cannot mutate the parent or another branch.  Successful
successors are rendered canonically, hashed from their ordered goal tuple, and
deduplicated before a bounded beam is retained.  The deterministic initial
priority prefers fewer and smaller remaining obligations, then policy rank and
stable path order.

Depth has a hard host-owned maximum of 32.  Beam width, candidates per state,
model calls, discovered states, and generated text are independently bounded;
the trained-policy adapter can generate several sibling candidates in one
physical model call.  Multiline, malformed, session-command, and failing
outputs are rejected without repair.  A search result becomes a proof only
after `checked_surface_final` checks the certificate against the separately
retained original target.  The persistent client then performs a second fresh
kernel replay before displaying or saving the script.

Deterministic closers may run at compatible arithmetic leaves.  The model
spends probability on branching choices such as induction variables,
invariants, witnesses, rewrite direction, theorem specialization, and local
lemmas.  This division of labour is the transferable AlphaGeometry lesson.

Only final-kernel-checked trajectories may enter a future expert-iteration
round.  Prefer
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
not a trained-policy result. Training job `20029970` later completed all 100
steps in 9m51s with train loss `0.78446` and final teacher-forced validation
loss `0.13518`. Evaluator `20029980` failed after three seconds, before model
generation: canonical manifest JSON sorts nested mapping keys, while the loader
incorrectly reused the construction-order check intended for dataset rows. The
loader now reconstructs the exact three capability fields from the sorted
manifest representation before checking their values, environment preimage
hash, and fixed `model-v1` authority. No kernel-judged theorem solve rate is
available from that run.

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
parser. The fix changed source identity, so a fresh preparation job was required
before training; at that point no WMI trained-policy result was claimed. Preparation `171404`
was canceled after 1m56s when the manifest-loader defect was discovered, rather
than spending A100 time on a chain whose evaluator would necessarily reject its
manifest.

The first accepted terminal WMI chain then ran from clean commit `0c84fc3`.
Preparation `171414` completed in 7m28s and reproduced dataset digest
`1fa98caa…`; dependent training `171421` completed 100 optimizer steps in
11m40s. The immutable training manifest has SHA-256 `ad16e60d…`, binds final
adapter `ff187542…`, and records 2,048 selected training examples, 256
validation examples, train loss `0.78301`, and final teacher-forced validation
loss `0.13615`. The optimizer saw only 1,600 examples—0.78125 of the selected
subset—because the registered smoke stopped at 100 effective-batch-16 updates.

Evaluator `171423` completed successfully on the same A100/runtime/source
chain. Its result was 0/4 goals at pass@4: all sixteen rollouts ended on a
failing tactic before QED. That is the first trained-policy theorem result, and
it is negative. It must not be replaced by the attractive validation loss.

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
  --sample --max-new-tokens 96 --max-steps 24 \
  --search-beam-width 8 \
  --search-candidates-per-state 16 \
  --search-max-model-calls 512 \
  --search-max-states 4096
```

The wrapper validates the formula and total call budget locally, creates a version-2 canonical JSON
request with a fresh nonce, and identity-binds kernel-guided-search mode, generated tokens per
candidate, depth, beam width, candidates per state, model calls, and discovered states. It streams that request under the WMI
deployment lock and exports only its 64-hex SHA-256 ID to Slurm. The guarded submitter revalidates
and hashes the request, appends both the ordinary job row and an immutable request/job ledger row
before releasing one typed-A100 job. The compute job rechecks the central base, overlay, source,
scheduler row, request bytes, adapter, search report, and kernel path. Version-1 request artifacts
remain replayable with their original bounded-rollout semantics; new requests cannot silently fall
back to rollout mode. A version-2 request additionally requires the exact sealed model-v2
environment, verifies the closed adapter/tokenizer snapshot before and after the run, and checks
every per-goal, decoder, and aggregate search counter. The `--k` rollout flag is therefore rejected
by this wrapper.
It writes digest-named report, optional `.pa`, and terminal run-summary files under
`results/peano-policy/user-proofs/`; a sound but unsolved request finishes with `status=no-proof`
rather than masquerading as an infrastructure crash. The wrapper prints the request ID used in
those filenames.

The guarded one-shot job now targets the attested model-v2 heavy adapter and
defaults to 96 generated tokens per candidate, depth 32, beam width 4, four candidates per state,
128 model calls, and 2,048 states; before that adapter exists it fails closed. Model-v2 also adds
a persistent terminal client so an interactive WMI allocation pays model loading
cost once and can try many theorems in one session. Local inference, when the
machine can load the adapter, uses:

```console
python3 scripts/peano_policy_repl.py \
  --adapter results/peano-policy/qwen3-1.7b-lora-v2-heavy
```

The prompt accepts either a bare closed formula or `pa prove FORMULA`.  Default
search bounds are depth 32, beam width 4, four candidates per state, 128 model
calls, and 2,048 states.  A successful path is replayed independently before
the ordinary `.pa` proof and structured JSON report are written under
`results/peano-policy/interactive/`; existing artifacts are never overwritten.
On WMI, the guarded interactive allocation is:

```console
scripts/wmi_peano_policy_repl.sh \
  --connect --confirm PEANO-LAB-WMI-TRAINING
```

The WMI wrapper requests one typed A100, validates the fixed deployment and
runtime, and keeps the policy resident while theorem lines arrive on standard
input.  A Helios-trained adapter is immediately available through the matching
GH200 launcher, without first copying its closed artifact tree to WMI:

```console
scripts/helios_peano_policy_repl.sh \
  --connect --confirm PEANO-LAB-TRAINING
```

Both cluster wrappers are dry-run by default, allocate one fixed GPU, keep
theorem text out of shell arguments, and deliberately refuse a model-v1 or
unattested adapter. They are implemented and model-free tested, but the
expected model-v2 adapter path does not yet contain a completed heavy-run
result.

### 10.3 What the first adapter can and cannot do

Two registered arbitrary-theorem requests make the boundary concrete. Job
`171428` tried the earlier parity theorem

```text
∀ x. ∃ y. x · (x + 1) = 2 · y
```

sixteen times and found no proof. Fifteen trajectories introduced `x` and then
proposed a quotient witness containing `/`, which is not a PA term. In contrast,
job `171430` proved a fresh direct-witness formula absent exactly from train,
validation, and test:

```text
∀ x. ∃ y. (x + 17) · 19 + 23 + y = (x + 17) · 19 + 23
```

One of eight samples produced `intro n; exists 0; rewrite PA3; refl`. The
ordinary exported script replayed independently to a seven-node checked
certificate. This is one real success in a represented schema, but attributing it to fine-tuning
requires the still-pending pretrained-base baseline. The adapter did not demonstrate
induction-level proof planning.

The post-result audit explains why. The full 8,149-row train split represents
only sixteen of the twenty-five permitted tactic heads. It has no IH states,
no use of any of the seven allowed foundation lemmas, and zero actions headed
by `assumption`, `exfalso`, `forall_elim`, `have`, `induction`, `simp`,
`specialize`, `suffices`, or `use`. Every source proof is one to seven tactics
long. All 513 comparable existential goals are labelled immediately with
`exists`; the adapter's parity behavior is consistent with that supervised support.
Known checked routes under the precise model-v1 authority take 10, 10, 23, and
13 commands for the four held-out goals. The registered 16-step budget is
therefore below the known `le_total` route and must rise to at least 24 in the
next protocol.

The run directly exposes curriculum and search failures. It also rules out sequence truncation and
a train/inference template mismatch, but it does not establish that prompt v1 is adequate: grammar
and lemma semantics remain hidden behind an opaque capability hash. No selected training sequence was truncated; the largest complete
example used 595 of 1,024 tokens, and the one-line training/inference contract
agrees exactly. The evaluator is closed-loop at the state level, but each
rollout is one path: it stops at its first transactional tactic failure and has
no retry, sibling frontier, or backtracking.

The separately maintained candidate lemma library has now been authorized for publication. Its 26
entries are appended to the public theorem ladder at source commit
`d2ba05dca952e2e33479923433f8d2fcd3409493`, catalog SHA-256
`91c88c1f3311cc0dc540671b169c270758ff6211e77716ed07bd3dd4f55c8380`.
All replay deterministically and pass the empty-context kernel check. The largest certificate has
21,515 nodes at depth 66 in the immutable upstream, fully expanded validation report. The current
snapshot-v2 representation packages dependency proofs in self-contained kernel Cuts and records a
maximum node count of 25,545 (`bounded_beta_crt_for_existing_code`) and a
maximum depth of 80 (`prime_divisor_exists`) across the current
189-theorem ladder. It contains 242,629 structural nodes and 6,895
self-contained Cuts across 149 Cut-bearing
entries. The new premise surface includes the full `mod_eq_add`/`mod_eq_mul`
compatibility layer, `mod_eq_bounded_unique`, both directed
remainder/congruence bridges, and all expanded β-value theorems through
`beta_at_of_mod_eq_bound`. Thus expanded β decoding is equivalent to a bound
plus balanced congruence. Constructive `binary_crt`, its bounded-residue
wrapper, and the premise-bearing two-position `binary_crt_beta_pair` are
checked. The newer `beta_moduli_coprime_of_gap_dvd` proves the
coprimality premise when an ordered index gap divides `c`,
`binary_crt_beta_pair_of_gap_dvd` applies it, and
`bounded_common_multiple_exists` supplies a nonzero common multiple for
all positive gaps through a bound. The new bounded-prefix layer proves all
distinct selected β moduli pairwise coprime, closes coprimality under products,
descends congruence from product moduli, and checks one CRT fold step. The
new six-theorem layer folds accumulated-product and decoded-congruence
invariants through every bounded prefix of values already represented by a
supplied `BetaAt` code. Its public wrapper is not arbitrary finite-sequence
coding. The library still does not include genuine prefix-product recurrence
and bounds, β finite-prefix recoding, finite products, greatest-prime descent,
or native FTA. Unconditional pairwise β-modulus coprimality is false.
Model provenance must bind the representation version as
well as the certificate hashes and metrics.
The corresponding 189-entry deterministic corpus refresh retains 13,344 transitions
from 1,692 sessions and has run fingerprint
`a3c2f8c5c762b10fc9c1117723c74fecb50348cfb699f73bc76fb3714df3bf1b`.
Its isolated all-ladder smoke has 378 sessions, 5,373 raw transitions, 5,370
unique transitions, and all 189 authored QEDs.

The pack now enters model-v2 through a distinct scientific contract. Its
content-addressed checked identity binds each name, canonical statement,
dependencies, authored-script hash, checked expanded-certificate hash, nodes,
and depth into dataset, training, evaluator, search, and request provenance.
The model sees the compact grammar and eight deterministic retrieved
name/statement records rather than only an opaque capability hash. Balanced
checked generation supplies downstream theorem-import and composition traces;
the full identity, not the retrieval excerpt, remains the authority.

Importing an exact capstone theorem can make its motivating goal a three-line
library application. That is excellent usability evidence, but it is no longer
a held-out proving benchmark. Model-v2 must retain separate sealed theorem
families whose statements, proofs, descendants, and retrieval entries never
enter training or development. The exact public capstone is therefore excluded from discovery
claims unless its library entry is masked. It remains useful as a retrieval/application and
end-to-end kernel-replay regression.

A later reconciliation with the public general-arithmetic work brings the
ordered catalog to 63 entries, with public root
`d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0`.
Model-v2 does not obtain 59 imports by subtracting only the four goal names.
It excludes their complete seven-name reverse-dependency closure and binds the
remaining 56 records under full identity
`3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439`.

### 10.4 Model-v2 correction stack: implemented, training pending

The first run consumed 1,600 examples—19.6% of the full train split and less than one epoch of its
selected subset. The full split covers only 16/25 tactic heads, contains no induction-hypothesis or
order states, and has no foundation-lemma uses. All 27 validation schemas also occur in the
29-schema train corpus. The low validation loss therefore measures short-template imitation, while
held-out reference routes require 10--23 actions and induction/lemma-use decisions unseen in
training.

In the pre-reconciliation full-surface audit, the 49-entry public catalog contributed 474 prospective model-v2
transitions when each dependency becomes an explicit `use`: 427 authored commands plus 47 imports.
This seed has longer proofs and richer contexts, but only one `induction` label. Naive concatenation under the old sampler would expose the
optimizer to about 88 catalog rows in expectation and gives the singleton induction row only about
an 18.6% chance of being seen. The implemented model-v2 stack therefore uses a balanced generator,
not merely a larger concatenated file. That audit remains useful historical
evidence for the sampler diagnosis, but its transition count is not the current
63-entry authority's capacity result.

The correction stack now present in the repository is:

1. a 56-theorem checked identity, SHA-256
   `3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439`, that independently
   replays every permitted public theorem and binds statement, dependency, source, script,
   expanded certificate, node, and depth data;
2. a separate prompt projection with compact grammar and eight deterministic retrieved
   name/statement records, while the full checked identity remains the authority hash;
3. a proof-first 100,000-row generator balanced by emitted rows at 2:1:1 across foundation,
   induction, and library lanes, with hard coverage gates for all 25 tactic heads and all 56
   imports;
4. a no-truncation tokenizer audit over every example selected by the exact training config;
5. depth-32 transactional canonical-state beam search with bounded sibling generation and an
   independent publication replay;
6. one shared heavy configuration for Helios and WMI: pinned Qwen3-1.7B Base, BF16 SDPA,
   rank-16/alpha-32 LoRA, effective batch 32, learning rate $10^{-4}$, 2,048-token inputs, and three
   full epochs over the model-v2 data; and
7. a persistent local/WMI/Helios REPL that loads that attested adapter once and publishes only
   twice-kernel-checked ordinary Peano Lab scripts.

Implementation did not turn these items into an experimental result. No model-v2 checkpoint
established pass rate, search gain, or induction/lemma-use quality. The 247-theorem library then
made the fixed 56-theorem authority and its old held-outs obsolete, so the unrun model-v2 heavy
path is retained as design history and superseded by model-v3 below. Pretrained and deterministic
baselines, a separate executed-failure ranking corpus, and expert iteration still remain to be
run. The 4B comparison is deferred until the model-v3 1.7B baseline exists; current evidence does
not identify parameter count as the limiting factor.

The immutable training manifest, held-out report, two arbitrary-request reports, compact index, and
checked positive script are published under [`artifacts/peano-policy/`](../artifacts/peano-policy/).

### 10.5 Model-v3 successor: implemented, WMI run pending

Model-v3 replaces the undersized model-v2 authority with all 247 declaration-ordered public
theorems. Its checked identity binds each canonical statement, dependency list, source
specification, authored script, reconstructed certificate, proof-node count, and proof depth.
Identity construction replays every authored proof and asks the independent kernel to validate the
certificate from the empty context against the original proposition. The catalog is an input to
that check, not a trusted proof database.

The model-v3 positive curriculum has two complementary sources:

1. **Exact library trajectories.** The trajectory for theorem $i$ runs under exactly
   `THEOREMS[:i]`, imports its declared direct dependencies with `use`, and executes the authored
   script unchanged. The target theorem and every later theorem are absent from execution and from
   retrieval.
2. **Root-balanced synthetic trajectories.** Fifty-one proof-first schemas are scheduled across
   fourteen genuine first-tactic heads. Complete checked sessions are the indivisible scheduling
   unit, first-head counts remain balanced, and `intro` is capped at 20% of root sessions. The four
   inherited induction schemas have their artificial implication gates removed, so their root
   action is `induction`, not `intro gate`. Library schemas are omitted because the exact prefix
   corpus owns theorem-reuse supervision.

Prompt v3 carries the complete compact allowed-name inventory plus at most twelve deterministically
retrieved statement records from the current prefix. The latter are detailed semantic context, not
the only names the policy may select. Its proof-state field uses the v3-only
`shared-declarations-v1` lossless structural encoding. From each canonical one-line goal it stores
exact comma-delimited context chunks and the exact target in deterministic first-occurrence tables;
each goal is then a declaration-index vector plus a target index. Parsing rejects alternate JSON,
non-first-use or unused table entries, non-integer or out-of-range indices, and any reconstruction
that differs from the original goal string. Raw traces, replay states, dataset-row `state` values,
held-out checks, and kernel inputs remain exact. Model-v1 and model-v2 prompt bytes are unchanged.

The compact state JSON has a 44,000-Unicode-character fail-closed bound. It never slices a target,
abbreviates a hypothesis, or drops a name. Across all 443 before/after states retained for the
index-230 stress proof, the largest encoded state is 39,423 characters and none crosses that bound;
step 115 falls from 196,457 legacy-state characters to 37,259 by sharing exact repeated structure.
The exact pinned check of the largest state is 53,901 full-prompt characters and 29,111 tokens
including tactic and EOS, leaving 3,657 tokens below Qwen's 32,768 native limit. All 222 exact
transition prompts for that stress proof pass: median 17,444, p95 26,662, p99 28,537, and maximum
29,111 tokens. The complete combined-corpus scan remains the final authority.

Attestation reconstructs all 248 environments—prefixes 0 through 247—requires the exact
`catalog-predecessor-prefix-v1+full-synthetic-v1` schedule, independently rebuilds the compiled
splits from raw traces, and requires zero held-out contamination. Preparation then tokenizes every
selected train and validation example with the pinned tokenizer and rejects the release if any
sequence exceeds Qwen's 32,768-token native context. Truncation is forbidden; a failed audit
requires a reviewed representation change.

The model-v2 goals `le_trans`, `le_antisymm`, `le_total`, and `mul_eq_zero` are now theorem-ladder
training material, so they cannot remain model-v3 discovery tests. The separately sealed v3 set is:

| Name | Exact source formula |
|---|---|
| `closed_arithmetic_seven` | `0 * 0 + 3 + (0 * 1 + 1) + (3 + 0) = 7` |
| `existential_subtraction_two` | `exists x. 7 = x + 2` |
| `double_right_zero` | `forall n. (n + 0) + 0 = n` |
| `consecutive_product_even` | `forall n. exists x. n * (n + 1) = 2 * x` |

This four-goal set is the launch smoke, not evidence for broad proving ability. Three goals calibrate
short arithmetic behavior; only `consecutive_product_even` exercises multistep induction. Any broad
quality claim must use a larger hidden kernel-checked suite spanning induction, theorem composition,
order, divisibility, and quantified witnesses under fixed budgets.

The registered WMI configuration uses the pinned `Qwen/Qwen3-1.7B-Base` revision, BF16 SDPA,
rank-32/alpha-64 LoRA, effective batch 32, learning rate $10^{-4}$, two epochs, and caps of 80,000
training and 6,000 validation rows. Microbatch one with gradient accumulation 32 preserves the
effective batch while avoiding long-state padding pairs. The CPU preparation, independent
attestation, and 32,768-token native-context gate must pass before the A100 job is eligible to train.
No model-v3 training submission,
checkpoint, evaluation score, or model-quality claim is recorded yet.

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
