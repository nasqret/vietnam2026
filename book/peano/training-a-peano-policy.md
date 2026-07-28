# Training a Peano policy without trusting it

Can a small language model learn to help with Peano Lab proofs?  Yes—but the interesting part is
not merely fine-tuning a decoder on tactic strings.  The interesting part is arranging the
experiment so that a useful model can never become a source of mathematical authority, and so
that a high score cannot be manufactured by data leakage, an accidentally stronger tactic
environment, or a stale checkpoint.

M19 turns that problem into an explicit research pipeline.  It adds a compact headless runner,
a replay-validating dataset compiler, a repository-owned next-tactic prompt, a BF16 LoRA training
runtime, a kernel-judged evaluator, and guarded Helios job controls.  These pieces are deliberately
outside the kernel.  They can make proof search faster; they cannot make an invalid certificate
valid.

```{admonition} Experiment status, 2026-07-28
:class: important
The local execution, prompt, training-runtime, evaluation, provenance, and cluster control paths are
implemented, and the first attested training-scale data release is complete: 2,522 independently
kernel-checked roots compile to exactly 10,000 positive rows. WMI completed the first accepted
100-step train/evaluate chain. The result is mixed and deliberately narrow: 0/4 frozen goals at
pass@4, zero successful parity rollouts in 16 samples (pass@16 = 0.0), and one kernel-checked proof
among eight samples for a fresh direct-witness theorem. That success is consistent with a represented
pattern, but attribution to fine-tuning awaits the pretrained-base baseline; the adapter is not yet
a useful induction/order prover. Since that model-v1 result, the model-v2 library identity,
retrieval prompt, balanced 100,000-row generator, tokenizer gate, depth-32 verifier-guided search,
heavy 1.7B configuration, and persistent local/WMI/Helios REPL have been implemented. No model-v2 heavy
checkpoint has yet been trained or evaluated, so its proof quality and search gain remain unknown.
The reconciled authority is now 63 public entries, seven dependency-closed import exclusions, and
56 permitted records; pre-reconciliation datasets and capacity reports must be regenerated and
re-attested before training.
The 4B comparison and expert iteration are still deferred.
```

The binding research protocol is
[`docs/PEANO_TRAINING.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_TRAINING.md).
This chapter explains why that protocol has its present shape.

## The useful interpretation of “a compact Peano Lab”

Starting a browser, loading Pyodide, importing thirty-odd Python modules, and rendering terminal
panels for every generated proof would be a poor data-generation loop.  A long-lived Python process
can import the prover once and execute many JSONL requests much faster.

There are two ways to obtain such a process:

1. write a second, reduced parser, tactic interpreter, and checker; or
2. remove the browser while retaining the production parser, tactic surface, proof engine, and
   checker.

Only the second is Peano Lab.  The first would create a *shadow prover*.  A generated proof could
succeed under the shadow semantics and fail on the website; worse, a bug in the shadow checker
could label false training examples as proved.  Testing two implementations against one another
would reduce the risk, but it would not remove the duplicated source of truth.

The implemented runner is therefore an **adapter**, not a miniature prover:

```text
JSONL request
    │
    ▼
strict request validation
    │
    ▼
production formula parser ── original target and logic mode retained by owner
    │
    ▼
production run_surface grammar ── immutable ProofState transactions
    │
    ├── raw version-1 transition trace
    │
    ▼
checked_surface_final
    │
    ▼
independent kernel checker(original target, exact logic mode)
    │
    └── only here may the result say kernel_checked=true
```

The browser and the batch runner differ in transport and presentation.  They do not differ in
proof rules.  The headless path omits the DOM, terminal panels, Pyodide routing, and routine
certificate rendering.  It reuses `parse_formula_with_names`, `ProofSession`, `run_surface`, the
checked theorem library, certificate finalization, and the independent checker.

This gives a useful engineering principle:

> Optimize around the trusted boundary before optimizing through it.

Keeping one Python interpreter warm removes avoidable startup work.  Omitting display rendering
removes avoidable formatting work.  Omitting the final kernel call would change the meaning of the
result, so it is never a performance option.

## Two modes, only one data mode

The Python API makes the distinction visible in its names:

- `run_proof(...)` executes a proof with binding version-1 transition tracing;
- `verify_proof(...)` checks an already-authored script without retaining transition data.

Both build the certificate and perform the same final kernel check.  The quiet path is useful for
filtering known scripts and regression checks.  Synthetic generation and policy search use the
traced path, because the desired training object is not just a Boolean QED.  It is an auditable
sequence

$$
  (s_0,a_0,s_1), (s_1,a_1,s_2),\ldots,(s_{r-1},a_{r-1},s_r)
$$

whose last state is closed and whose complete certificate checks for the original theorem.

The command-line process reads one strict request per physical line.  For example, a request file
may contain:

```json
{"v":1,"id":"add-zero","theorem":"forall n. n + 0 = n","tactics":["intro n","rewrite PA3","refl"]}
```

The generation form is:

```bash
python3 scripts/peano_batch.py --environment model-v1 \
  --trace-output run.trace.jsonl < requests.jsonl > results.jsonl
```

This is a finite transactional file interface, not an interactive duplex protocol.  Results are
withheld until EOF and, in trace mode, until the trace name has committed.  The default transaction
ceilings are 10,000 requests, 256 MiB input, 128 MiB result envelopes, and 512 MiB raw trace;
larger corpora are sharded or use an explicitly reviewed limit.  Exit zero means the transport
completed, while each row carries its proof status.  Verification jobs add `--require-proved` when
every executed request must close.

`run.trace.jsonl` contains only the binding raw trace stream.  `results.jsonl` contains compact
per-request outcomes.  They are separate on purpose: the trace exporter must never have to guess
whether a JSON object is a transition, a footer, or a convenience response.

The command owns the execution mode and tactic environment.  A request cannot ask for a more
powerful surface.  Inputs have bounded physical lines, strict UTF-8, strict JSON with no duplicate
keys, bounded integers, or floating-point values, closed one-line theorems, and complete one-line
tactics.  Output is
staged before publication.  An empty, all-invalid, fail-fast, or unexpectedly interrupted batch
before the hard-link commit does not leave a final trace at the requested path.  The hard link is
the explicit commit point: an interruption after it may leave the complete, already-fsynced trace
while stdout is absent or incomplete.  That trace is valid; discard the result redirection and
reconstruct or rerun it.  A caller that needs an atomic result file redirects stdout to its own
temporary name and renames it only after a successful process exit.

The status vocabulary also refuses to blur distinct events:

| Status | Meaning | A proved theorem? |
|---|---|---:|
| `proved` | all goals closed and the final kernel check accepted | yes |
| `open` | the supplied tactics ended with goals remaining | no |
| `tactic_error` | a legal execution attempt failed transactionally | no |
| `tactic_limit` | an explicit resource bound stopped the attempt | no |
| `kernel_rejection` | final evidence failed independent checking | no; fail stop |
| `request_error` | the JSON request never entered a proof session | no |

A failing tactic must emit one error transition with identical before and after goals and the same
diagnostic as the raised tactic error, and must
leave the entire immutable state unchanged.  A successful command must produce the transition or
transitions, replay journal, and engine transaction that its real execution produced.  In
particular, top-level `auto` is not allowed to
claim one opaque transition after secretly replaying a different primitive history.  The finite
model surface currently excludes `auto` until that replay can itself be capability-scoped.

## Where soundness lives

It is tempting to call the whole pipeline “verified” because it ends in a checker.  That is too
coarse.  Different components justify different claims.

| Component | May choose | May certify |
|---|---|---|
| generator | theorem templates, proof scripts, mutations | nothing |
| language model | one candidate tactic line | nothing |
| tactic engine | proof-state transformation and certificate candidate | nothing globally |
| dataset compiler | whether a trace satisfies the data contract | replay integrity, not PA truth by itself |
| independent kernel | whether a certificate derives a formula in the selected logic | the exact PA judgment it checks |

For every QED the session owner retains four pieces of authority independently of the tactic layer:
the parsed original theorem, its display-name table, the exact intuitionistic/classical mode, and
the trace owner.  The adapter rejects a returned session that replaces any of them.  Finalization
submits the finished certificate against that retained theorem—not against the tactic layer's last
rendered goal.

The model does not emit certificate constructors, Python, theorem declarations, mode changes, or
`qed`.  It emits text in the same public tactic language a student uses.  This is not enough by
itself to guarantee a proof: a buggy tactic could still build malformed evidence.  It is enough to
keep model inference outside the trusted computing base because malformed evidence still reaches
the independent checker.

There is also a narrower scientific boundary.  The checker establishes

$$
  \Gamma \vdash_{\mathrm{PA}} p : P.
$$

It does not establish that an English sentence was faithfully translated as $P$, that the dataset
split was fair, or that a benchmark environment matched training.  Those are separate contracts
with separate evidence.

## A trace is not positive data until it survives replay

The raw trace is retained unchanged.  A sidecar supplies research metadata such as theorem family,
lineage, logic mode, and the exact tactic capabilities.  The dataset compiler then accepts positive
cross-entropy rows only from sessions satisfying all of these conditions:

1. the raw footer says `qed: true`;
2. the ordered successful tactic sequence replays through the current public surface;
3. the replay closes and the independent kernel accepts the rebuilt certificate;
4. each canonical before state, focus, tactic, after state, status, and error agrees with the raw
   transition;
5. the replayed proof-tree size agrees with the raw footer; and
6. family and lineage metadata permit a split assignment before transition expansion; and
7. sessions with the same canonical theorem formula belong to the same connected split component,
   even if their genealogy labels disagree; and
8. sessions sharing any exact rendered policy prompt belong to the same component, even when their
   original theorems and genealogy differ.

This is stricter than checking each transition locally.  A prefix can contain many correct steps
without proving its theorem.  Such a prefix is useful search telemetry, but training it as if QED
were guaranteed would teach survival rather than proving.  Similarly, failed tactics are useful
future ranking data; they are not positive completion targets.

The compiler publishes `train.jsonl`, `val.jsonl`, `test.jsonl`, and one manifest as a coherent
artifact set.  The trainer refuses raw trace files and accepts only rows whose byte digest, row
count, prompt contract, environment preimage, and replay counts agree with that adjacent manifest.
This deliberately duplicates some fields.  Redundancy is useful when disagreement is treated as an
error rather than silently resolved in favor of whichever copy is convenient.

### Attestation recompiles the data instead of trusting the manifest

A self-description is not independent evidence.  A malicious or stale builder could write matching
hash fields for the wrong bytes, or a later code change could make an old split impossible to
reproduce.  Before model import or output-directory creation, the training attestor therefore starts
again from the committed raw trace and metadata artifacts.

It checks their hashes, requires the recorded compiler inventory to match the current compiler and
Peano source tree, reconstructs the fixed `model-v1` capability preimage, scans every split for the
four frozen held-out formulas, and confirms that canonical theorem formulas and exact rendered
policy prompts are both disjoint across train, validation, and test.  It then invokes the current
replay compiler in a fresh temporary directory.  The rebuilt `train.jsonl`, `val.jsonl`, and
`test.jsonl` must have exactly the same sizes and SHA-256 digests as the release files.  For the
first M19 release this independent rebuild is byte-identical and the held-out contamination count
is zero.

This attestation is stronger than loading and rehashing the final rows: it demonstrates that the raw
kernel-checked sessions, current code, fixed environment, split algorithm, and prompt compiler lead
back to those exact bytes.  It is still not a proof of broad mathematical coverage or good model
performance.  It certifies the identity and replay contract of one dataset.

## Three prompt-design bugs that looked harmless

The final prompt is short:

```text
<task>next_tactic</task>
<env>peano-lab-v1;surface=model-v1;logic=intuitionistic;capability_sha256=…</env>
<state>{"focus":0,"goals":["⊢ ∀ n. n + 0 = n"]}</state>
<tactic>
```

The completion is one tactic line.  The stored dataset envelope adds the terminal delimiter
`</tactic>` so malformed records are easy to reject.  The loader strips that delimiter and
supervises exactly the tactic tokens followed by the tokenizer's EOS token; every prompt token is
masked from the causal loss.  At inference time the adapter returns the bare tactic, not XML and
not an explanation.

Arriving at this small format exposed three surprisingly general lessons.

### 1. A surface label is not an authority description

Suppose both training and evaluation say `surface=model-v1`.  One process might allow theorem
`add_comm`; another might accidentally allow the held-out target itself.  The strings match, but
the proof problems do not.

Peano Lab therefore canonically serializes the capability preimage

$$
  C=(\text{label},\text{allowed commands},\text{allowed theorems})
$$

and computes $h=\operatorname{SHA256}(C)$.  The prompt carries $h$; the row and manifest retain the
complete $C$; the trainer recomputes the digest; and evaluation checks that the adapter's preimage
equals the goal's actual execution environment.  The logic mode is displayed separately in the
prompt and is also owner-held.  Thus the full authority is the pair of exact logic mode and exact
capability object, not the friendly label and not the hash alone.

This fixed a real class of *authority-hash mismatch*: it is not sufficient to hash a name for an
environment, nor to record a digest without retaining and validating its preimage.  The same rule
applies recursively to tacticals.  A forbidden theorem inside an unselected `first [...]` or
`orelse` branch is still forbidden; syntax hidden in a dead branch must not smuggle capabilities.

### 2. Raw trace focus can leak the action

Version-1 `ProofState` has no persistent cursor.  A raw trace's `focus` is computed from the
submitted command.  If the action is

```text
focus 2 refl
```

then the trace records zero-based focus `1`.  Feeding that `1` into the policy input while asking
the model to predict `focus 2 refl` reveals part of the answer.  The feature looks like state, but
it was produced by the label.

Policy rows therefore render the runner-owned default focus `0` and preserve all goals in their
canonical order.  Goal selection remains part of the tactic action.  A future prover with a genuine
persistent user cursor may expose that cursor, but it must come from the pre-action state rather
than from parsing the target completion.

This is a useful causal test for every proposed feature:

> Could this field be known before the action was chosen?

If not, it belongs in the label, the successor state, or evaluation metadata—not in the input.

### 3. Kernel alpha-equivalence does not erase surface trajectories

The kernel represents bound variables by De Bruijn index, so renaming a binder changes no kernel
formula.  The interactive language, however, lets later tactics mention visible names:

```text
intro n
induction n
```

Changing the first line to `intro k` while retaining the second line does not preserve an
executable script.  Likewise, generated names such as `IH`, `h_witness`, and renamed collision
variants influence later tactic text even when the underlying certificate is alpha-equivalent.

The version-1 dataset consequently declares an **exact authored binder trajectory**.  It preserves
the visible names in each state and the exact successful tactic line that reaches the stored next
state.  Replay verifies the whole trajectory.  Synthetic generators must choose their binder names
deterministically within a lineage; they may not independently alpha-rename states and actions.

This choice solves executability, not every statistical problem.  Two independently generated
proofs can still present the same mathematical state with different arbitrary naming actions.  A
later prompt version may canonicalize binder-introducing actions or expose an explicit name-binding
map, but such a change must be versioned and replayed.  “Names do not matter to the kernel” is not a
license to make the policy's input/output pairs inconsistent.

## Synthetic data needs a family tree

Randomly splitting transition rows is almost guaranteed to leak.  Adjacent rows from one proof
would appear on both sides of the split.  Renamed copies, commuted equations, altered numerals, and
alternative proofs of the same generated theorem can be only marginally less obvious duplicates.

The compiler therefore splits *before* expanding sessions into rows.  It connects family, lineage,
canonical theorem-formula, and exact rendered policy-prompt nodes:

```text
family ── lineage
   ├── canonical theorem formula
   └── exact rendered policy prompt(s)
```

Sessions sharing a family or lineage belong to one connected component.  The canonical-formula
edge provides an independent defense against false genealogy metadata: two sessions proving the
same printed kernel formula cannot cross splits merely because a producer assigned different
labels.  The policy-prompt edge handles a different leak: proofs of different original theorems can
reach the same model input, which must not appear in both training and evaluation.  Components are
ranked by a SHA-256 value derived from a declared split seed, then assigned deterministically to
train, validation, or test while reserving a training component.  Every transition from every
member of a component follows that assignment.

The consequence can look inconvenient: a small, highly connected corpus may yield a tiny or empty
validation split.  That is more honest than manufacturing validation rows by cutting a proof family
in half.  Scaling the generator should create genuinely distinct components, not weaken the split.

The initial 18-session catalog remains a useful end-to-end smoke fixture.  The first frozen
training-scale release is now larger and exact:

| Property | Released value |
|---|---:|
| kernel-checked sessions / independent roots | 2,522 |
| unique canonical statements | 2,522 |
| positive next-tactic rows | 10,000 |
| train / validation / test rows | 8,149 / 926 / 925 |
| proof-first schemas | 29 |
| domains | 5 |
| frozen held-out target occurrences | 0 |

The five domains are logic, equality, PA recurrence, witnesses, and arithmetic.  The combined split
digest is
`1fa98caa2e0528d39c1b9003c4ee153dfbe633cb1ee4505e8f5b28eb837465dd`.
All 2,522 source statements are distinct canonical formulas, and every session reaches QED through
the ordinary headless surface and independent kernel before contributing rows.
The raw traces, sidecar, source manifest, compiled splits, attestation, and concise reproduction
instructions live together in
[`data/peano-policy-v1/`](https://github.com/nasqret/vietnam2026/tree/peano-lab/data/peano-policy-v1).

This is a supervised-policy baseline, not unrestricted PA conjecture generation.  Its 29 schemas
do not include induction or planner-generated invariants, negative preference examples, or
natural-language formalization pairs.  Schema similarity also remains across IID roots; a genuine
family-OOD evaluation must withhold whole templates.

The implemented model-v2 generator addresses the most damaging coverage failure without weakening
genealogy.  It schedules complete, checked roots by *emitted transition rows* in three lanes:
foundation, induction, and library, with weights $2:1:1$.  A pre-reconciliation capacity exercise
under the former 45-import authority produced 50,002 foundation, 25,000 induction, and 24,998
library rows from 22,706 distinct roots.  That historical result establishes the scheduler's
100,000-row mechanics, not the current authority's capacity.  At 10,000 rows or more the current
publication contract refuses a corpus unless all 25 public tactic heads and all 56 permitted
theorem imports occur.  The four benchmark roots are excluded by name and canonical formula from
generated targets, while their seven-name reverse-dependency closure is excluded from imports and
retrieval.  Every accepted root still reaches independent kernel-checked QED
before it contributes even one row, and a session is never cut to repair a quota.  This is an
implemented generation capability, not yet an attested final model-v2 release or a training
result.  Executed failures will remain a separate ranking/value corpus.

A useful curriculum measures more than source length.  Relevant coordinates include formula AST
size and depth, tactic steps, certificate nodes and depth, verifier calls, automation used, branch
factor, and whether a witness, induction invariant, or local lemma had to be invented.  These
measurements let us ask whether a model learned a new proof pattern rather than memorized another
spelling of an easy one.

## Supervised learning: one decision at a time

The primary artifact is a next-tactic policy, not a whole-script chatbot.  Given canonical open
goals and a fixed environment, it predicts one complete public tactic line.  Peano Lab executes the
line and supplies the next real state.  This choice has several advantages:

- every decision can be checked immediately and transactionally;
- search can branch at a proof state without regenerating a long common prefix;
- deterministic tactics can handle routine arithmetic leaves;
- failures have a precise state/action interpretation; and
- token cost can be attributed to individual search choices.

The first smoke configuration used `Qwen/Qwen3-1.7B-Base` with BF16 rank-8 LoRA for 100 optimizer
steps.  Model-v2 has a separate heavy configuration for the same pinned 1.7B base: BF16 SDPA,
rank-16/alpha-32 LoRA over the attention and MLP projections, effective batch 32, learning rate
$10^{-4}$, a 2,048-token input budget, and three full epochs over the 100,000-row curriculum.  The
same configuration is consumed by the Helios GH200 and WMI A100 launch paths.  It has not yet
produced a trained model-v2 adapter.  Comparisons with `Qwen/Qwen3-4B-Base` and
`Pythagoras-LM/Pythagoras-Prover-4B` are deferred until the 1.7B baseline is evaluated.

The runtime uses a repository-owned non-chat prompt, right padding, completion-only loss, PyTorch
SDPA, deterministic seeds, and no tokenizer vocabulary modification.  It rejects an over-length
example rather than truncating the environment header or the start of a proof state.  The model-v2
preparation gate tokenizes every selected train and validation row with the exact pinned tokenizer
and 2,048-token limit, checks the resolved revision and EOS token, and records minimum, median,
p95, p99, maximum, mean, and headroom together with config and input hashes.  Both cluster paths
run this audit offline before training.
`PYTHONHASHSEED` must be set before interpreter startup; Python, NumPy when present, PyTorch, CUDA,
Transformers, and dataset shuffle seeds are recorded or derived deterministically.

Training loss is useful for debugging optimization.  It is not the primary model-selection
metric.  A policy that predicts common easy tactics can have a pleasant loss and still solve no new
theorem.  Checkpoint selection must ultimately be based on kernel-judged validation under frozen
budgets.

## Evaluation and transactional verifier-guided search

The implemented evaluator performs independent bounded rollouts.  At each step it renders the
canonical goals, asks the policy for one line, validates the text, executes it under the goal's
capability object, and classifies the outcome as proof, invalid output, failing tactic, or resource
limit.  A rollout counts only when `checked_surface_final` accepts the full certificate for the
externally retained theorem and logic mode.

The small protocol regression set contains `le_trans`, `le_antisymm`, `le_total`, and
`mul_eq_zero`.  All four run under one reported foundation theorem set; their own target names and
canonical formulas are absent from the attested 10,000-row release, their theorem names are not
importable, and `auto` is unavailable.  Four problems are not a credible final benchmark.  Before
any broad generalization claim, M19 must additionally freeze a larger set covering held-out
lineages, held-out whole templates, larger depths, unseen lemma/witness compositions, and a small
human-authored set.

Verifier-guided search is now an implemented host layer.  Its basic shape is:

1. place the initial real proof session in a frontier;
2. ask the policy for several complete tactic lines;
3. execute each line transactionally through the production surface;
4. discard invalid or failing actions, and retain successful successor sessions;
5. prioritize fewer and smaller remaining obligations, then proposal rank and stable path order;
6. hash the ordered canonical goal tuple and deduplicate canonical successors;
7. retain only a bounded beam and stop at host-owned model-call, candidate, state, text, and depth
   limits; and
8. count success only after the final independent kernel check against the original target.

Every candidate edge is reconstructed by replaying its entire command prefix in a fresh
`ProofSession`.  That choice is less memory-efficient than cloning engine internals, but makes the
transactional guarantee obvious: a malformed or failing sibling cannot damage its parent or
another branch.  The policy may return several ranked tactic lines in one physical model call;
multiline text, envelopes, session commands, and tactic failures are discarded without repair.
Search depth has a hard maximum of 32.  Canonical-goal deduplication is an efficiency heuristic: a
mistake there could lose a useful route, but it cannot manufacture QED because publication still
passes the independent checker.  The interactive client adds a second fresh replay before showing
or saving the ordinary proof script.

Once a trained model-v2 search finds new checked proofs, expert iteration may add their
trajectories to the positive set.  Failed actions and dominated successful successors can support
a separate ranking objective.
They should not be mixed into SFT labels merely because they were produced by the same run.  Any
later reward optimization receives terminal proof reward only from independent QED; a certificate
size bonus is conditional on QED and cannot compensate for an invalid theorem.

## What to measure

One scalar cannot describe this experiment.  At minimum every model/search condition should report:

| Question | Measurement |
|---|---|
| Does it solve problems? | independently checked pass@1, pass@4, and pass@16 |
| Is it cheap? | solved goals per generated token, kernel call, and second |
| Is search wasteful? | proposals, unique states, duplicate states, frontier peak |
| Are proofs compact? | certificate nodes and depth, conditional on QED |
| How does it fail? | invalid text, tactic failure, explicit limit, kernel rejection |
| Does it generalize? | per-family and per-difficulty outcomes on frozen splits |
| Is the estimate stable? | exact counts and bootstrap confidence intervals |

The budgets are part of the metric.  “Pass@16” is ambiguous unless sampling temperature, maximum
tactic steps, maximum generated tokens, theorem capabilities, deterministic closers, and verifier
calls are all fixed.  Wall time should be reported alongside hardware and batching because it is
not portable by itself.

Mandatory baselines include deterministic Peano tactics, the untrained base model, SFT greedy
decoding, SFT sampled pass@$k$, and SFT plus the now-implemented bounded beam search.  Comparisons
between 1.7B and 4B models must use the same data and verifier/token budgets, but the 4B run remains
deferred until the 1.7B model-v2 baseline exists.  A formal-prover prior and a general base model of
similar size should be compared as model families, not under selectively tuned settings.

Formalization remains a separate experiment.  The kernel can decide whether a proof derives the
formula a model emitted.  It cannot decide whether that formula faithfully expresses an English
sentence.  Exact AST checks work for templated synthetic pairs; human language requires semantic
review and must never be folded invisibly into the proof success rate.

## Helios: guarded operations, not a magic benchmark

The cluster workflow selectively adapts operational patterns from the SAIR Helios repository, but
Peano Lab owns its prompt and experiment contract.  The current target is the
`plgccaiautore2026` grant, the `plgrid-gpu-gh200` partition, one GH200 GPU job at a time during the
pilot, and the `ML-bundle/25.10` module baseline.  The fixed project root is
`$SCRATCH/codex-control/projects/peano-lab-training`.

The historical model-v1 progression was deliberately staged:

1. verify the committed 10,000-row release from its raw traces with the independent attestor;
2. inspect the source, dataset, and attestation manifests;
3. run the read-only Helios probe;
4. synchronize source while preserving remote checkpoints, results, caches, and the submission
   ledger;
5. test each Slurm script with `sbatch --test-only`;
6. run the CPU environment smoke;
7. prepare the pinned isolated Python environment and run its full GH200 smoke;
8. run the 1.7B, 100-step adapter smoke;
9. reload/resume it and run kernel-judged evaluation; and
10. use that result to decide whether the next controlled experiment should change data, search,
    or model scale.

The negative induction/order result selected data and search: model-v2 is the next experiment.
The 4B comparison was therefore not scheduled and remains deferred until the heavy 1.7B v2
baseline is evaluated.

The wrappers default to test-only.  A real submission requires both `--submit` and the explicit
confirmation token `PEANO-LAB-TRAINING`.  Every accepted submission appends timestamp, job ID,
script path, work directory, git commit, and script SHA-256 to `logs/submissions.tsv`.  Scheduler
logs are evidence that a job ran; they are not a substitute for the dataset, training, and
evaluation manifests.

The GH200 is an ARM machine.  `ML-bundle/25.10` loads CUDA libraries and advertises an immutable
ARM wheel directory through `PIP_FIND_LINKS`; it does not itself make `torch` importable.  The
preparation job therefore clears an isolated venv, installs the exact `torch==2.9.1+cu129` wheel
and a fully version-pinned Python dependency closure using binary wheels and no resolver freedom,
then requires `pip check`.  Scheduled jobs replace inherited `PYTHONPATH` with the two reviewed
repository roots, disable the user site, and assert the exact Torch/CUDA build.  The standalone
short GPU job consumes that prepared environment and therefore requires an `afterok` preparation
dependency.  It checks `aarch64`, CUDA visibility, the loaded PyTorch build, and Peano kernel
execution.  Versions and the resolved runtime inventory are recorded, but the current lock does not
use `--require-hashes`; this is not yet a claim of byte-identical wheel reproduction.  Before a
longer job is trusted, the full smoke sequence must also demonstrate BF16 forward/backward
execution, the relevant Python packages, adapter save/reload, tokenizer round trips, and evaluation
through the Peano kernel.  FlashAttention, vLLM, DeepSpeed, bitsandbytes, and QLoRA may later be
measured optimizations; none is a prerequisite for the first correctness run.

The corrected preparation job `20029964` subsequently passed this entire gate from clean commit
`41683e2`. It resolved the pinned Qwen3-1.7B model and tokenizer revision, performed a finite BF16
LoRA optimizer step on a GH200, saved and hashed the adapter and tokenizer, reloaded them, and
obtained another finite loss. That is evidence for the runtime boundary, not evidence that a useful
policy has been trained. Job `20029970` then completed the registered 100 steps in 9m51s. Its
teacher-forced train loss was 0.78446 and final validation loss 0.13518. Those figures show that the
adapter fit the next-tactic distribution; they do not measure complete proof success.

Evaluator `20029980` stopped after three seconds, before generation. Canonical manifest JSON uses
`sort_keys=True`, whereas the loader accidentally applied the construction-order rule designed for
raw dataset rows to the nested capability mapping. The repair reconstructs the exact three semantic
fields from sorted JSON and still checks their values, the environment preimage/hash, and equality
with the fixed `model-v1` authority.

## WMI A100: reproduce the gate, do not rename the environment

The WMI cluster provides a useful second path when Helios queues are long. Its
[published resource table](https://cluster.wmi.amu.edu.pl/02_02_zasoby_klastra.html) lists a node
with four NVIDIA A100 80GB GPUs. Live scheduler inspection confirmed that the owner belongs to
`hw_csi` and can use the non-preemptible `gpu_csi` partition. The lower-priority `gpu_spot` and
`gpu_idle` partitions can be requeued; they are inappropriate until the training loop explicitly
handles that lifecycle.

The important lesson is that “NVIDIA cluster” is not one environment. Helios is ARM with the
CUDA-12.9 wheel lock described above. WMI is x86-64 and exposes an official
`anaconda/2025.12-1` module whose `pytorch-gpu` environment contains Python 3.12, PyTorch 2.5.1,
and CUDA 12.4. Reusing the Helios lock would be both technically wrong and provenance laundering.

The corrected WMI probe `171369` requested one *typed* A100 and installed nothing. In thirteen
seconds it verified exactly one visible A100-SXM4-80GB, BF16, a finite backward pass, Python
3.12.12, Torch 2.5.1/CUDA 12.4, driver 610.43.02, outbound access, and 18 TB free storage.

The resulting environment is a two-layer contract. A canonical manifest names the central Python,
`ensurepip`, Torch/CUDA, numeric stack, and delegated dependency versions; live preparation proves
each distribution still resolves below the fixed central prefix. A twelve-wheel overlay then pins
Transformers, PEFT, Accelerate, safetensors, and their missing or incompatible dependencies by
exact x86-64 wheel SHA-256. The content-addressed environment ID hashes both records. Every overlay
distribution must resolve below that release, and a `current` pointer is rejected when its ID no
longer matches the freshly revalidated base.

Source deployment follows the same idea. A clean `git archive` excludes ignored and uncommitted
files. WMI reconstructs its Git tree, then publishes under an exclusive deployment lock only after
the tree matches; source-dependent preparation, training, and evaluation jobs hold the shared lock,
and sync removes valid provenance before it touches the live tree. Preparation moves the
environment pointer last, after package checks,
independent dataset attestation, a real LoRA optimizer step, adapter/tokenizer save and reload, and
finite losses. Replacement job `171395` passed that complete A100 gate in 8m39s. It reproduced
dataset digest `1fa98caa…`, recorded the exact commit and A100/Python/Torch environment, and saw
finite losses `6.06434` before save and `5.53506` after reload.

The next failure was deliberately cheaper. The training controller refused to call `sbatch`
because its Bash `IFS` reader collapsed the preparation row's empty dependency field, shifting the
remaining TSV columns. Empty fields are data, so a bounded strict UTF-8 parser now validates nine
columns exactly and rejects malformed or duplicate job rows. Since that repair changes source
identity, the passed preparation report could not be relabeled as its predecessor; a fresh
same-source chain was required. Moving the computation does not move the trust boundary: every generated proof
is still replayed by Peano Lab and every QED is checked against its original theorem.

Fresh preparation `171414` then passed from clean commit `0c84fc3`; dependent training `171421`
completed 100 steps, and evaluator `171423` reached a terminal kernel-judged report. The training
manifest binds adapter `ff187542…`, 2,048/256 selected examples, and train/validation losses
0.78301/0.13615. The attractive second number is teacher-forced next-token loss. The theorem result
is 0/4 at pass@4: all sixteen rollouts failed before QED.

Two arbitrary requests sharpen the diagnosis. The parity goal failed sixteen times; fifteen runs
proposed division as a direct existential witness. A new direct-witness theorem absent exactly from
all three splits succeeded once in eight samples and replayed to a seven-node checked proof. The
adapter therefore demonstrated one within-template success, but not the missing induction frontier.
Whether fine-tuning caused that success remains open until the pretrained base is evaluated.

That behavior is predicted by the corpus. Its 8,149 train rows use only sixteen of twenty-five
allowed tactic heads, contain no IH state or foundation-lemma use, and contain no `induction`,
`simp`, `have`, `suffices`, `specialize`, or `use` action. Every source proof is at most seven
steps. Under exact model-v1 authority, known checked held-out routes require 10, 10, 23, and 13
commands; the old 16-step evaluation cap does not even fit the known `le_total` route. More
parameters alone do not address absent actions and proof shapes; scaling now would confound the
intended curriculum experiment.

A separately maintained candidate lemma library has now been authorized for publication. Its 26
dependency-ordered entries extend the public catalog from 23 to 49 theorems. All replay
deterministically, their expanded certificates pass the empty-context kernel check, and the largest
has 21,515 nodes at depth 66. Publication changes theorem data and one untrusted import ceiling; the
kernel and proof rules remain unchanged.

A later reconciliation with the public general-arithmetic work brings that ordered catalog to 63
entries. Its public ordered root is
`d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0`.

For training, this is now a new content-addressed `model-v2` library authority, not a silent
extension of model-v1. The prompt exposes retrieved lemma names and canonical statements, and the
balanced data generator creates downstream `use` and composition trajectories. Once the exact
capstone theorem is importable, its three-line application is a usability test rather than an
unseen proving test; different theorem families remain sealed.

## Why the first run failed

The 0/4 result initially looks surprising beside validation loss 0.13615. It stops being surprising
once the two measurements are aligned. Validation asked, roughly, “can the model continue a tactic
line from another instantiation of a familiar short template?” The benchmark asked, “can it plan a
10--23-step proof using induction and named lemmas, sustain one error-free trajectory, and remain inside
Peano Lab's language?” Those are different tasks.

The exact audit is:

| Quantity | First model-v1 run | Evaluation contrast |
|---|---:|---|
| Train rows available | 8,149 | diverse proof states |
| Rows actually consumed | 1,600 (19.6%) | multiple full balanced epochs |
| Permitted tactic heads represented | 16/25 | all relevant heads |
| `induction`, `simp`, `have`, `specialize`, `use` labels | 0 | required by reference routes |
| IH states / order states / foundation-lemma uses | 0 / 0 / 0 | each occurs somewhere in the suite or its reference routes |
| Authored proof length | 1--7, mean 3.97 | known checked routes use 10, 10, 23, and 13 actions |
| Distinct generator schemas | 29 | whole-family OOD diversity |
| Validation schemas also present in train | 27/27 | held-out theorem families |

The labels are sharply imbalanced too. `intro` accounts for 40.52% of training rows; `intro`,
`exact`, and `refl` together account for 66.76%. Every one of 513 comparable context-free
existential states says to choose a witness immediately. The parity model's repeated attempt to use
the mathematically suggestive but syntactically unavailable witness `n * (n + 1) / 2` is therefore
not mysterious: the corpus taught “introduce, then witness”, but never taught the induction that
constructs a legal recursive witness.

The raw action interface compounds the curriculum problem. The prompt contains a capability hash,
not the PA grammar or the statements of the available lemmas. Of the 40 recorded evaluation
attempts, 24 stopped on language-interface mistakes: division or subtraction in a PA term,
unavailable commands or tactics, or malformed tactic arity. Only 84 of 123 proposed prefix actions were accepted
by the surface at all, and acceptance still does not mean progress.

Finally, each rollout is a brittle path. It dies on its first rejected action even though Peano Lab
already guarantees transactional failure. If the right action probability were 90% at every step,
a 23-step route would survive with probability only $0.9^{23}\approx0.089$; at 80% it falls below
0.006. The 16-step cap made the known 23-step `le_total` route impossible regardless of model
quality. These facts strongly explain the failure. They do **not** yet prove that 1.7B parameters or
rank-8 LoRA are sufficient; those are later controlled ablations, as is causal attribution of the
one shallow success to fine-tuning rather than the pretrained base.

## What the public catalog contributes—and what it does not

A reproducible local audit replayed the new 26 entries over the full tactic surface with each
dependency made into an explicit `use`. It produced 474 distinct checked state-to-tactic rows: 427
authored commands plus 47 imports. The authored bodies average 16.4 commands and reach 52. In
442/474 transitions (93.3%) the focused goal has a nonempty context; the replay also exposes IH
states, witness contexts, multiple goals, and lemma composition. These are candidate model-v2 rows,
not data available to the frozen seven-theorem model-v1 environment.

It is not a complete curriculum. The 474 labels contain only one `induction`, one `suffices`, four
`have`, eight `simp`, and 47 `use` decisions; `assumption` and `forall_elim` are still absent. If we
simply appended these rows and kept the old 2,048-row/100-step sampler, only about 113 catalog rows
would enter the selected subset and about 88 would actually be consumed. The lone induction row
would have only about an 18.6% chance of being seen. A larger theorem catalog without a balanced
sampler is not a learning algorithm.

The catalog also changes the leakage boundary. A training replay for a rung may see only the 23
core facts and earlier extension entries, never its own theorem or a later one. Its 47 dependency
edges are positive retrieval examples. Other earlier lemmas are not automatically negatives:
transitive ancestors and alternative proofs may still be useful. Negative ranking data must come
from actual transactional attempts whose failure is recorded separately. Since
`mod5_fourth_power_one` is now public, applying it to its exact statement measures retrieval and
application, not discovery of the fourth-power theorem.

Some audited full states are also substantially longer than model-v1 data: median 323 characters
and maximum 4,869. Much of the excess repeats context across sibling goals. Model-v2 currently
retains the complete canonical goal array, adds the grammar, and retrieves only eight
name/statement records. A later observation ablation may compact sibling descriptions, but policy
sufficiency of that representation must be measured rather than assumed.

## Model-v2: the experiment that tests the intended hypothesis

The design correction is now code, although the heavy experiment has not run.  Its most important
idea is that **what identifies the theorem authority is not what must fit in every prompt**.

The public catalog contains exactly 63 ordered theorem records and has root
`d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0`.
The four benchmark goals are `le_trans`, `le_antisymm`, `le_total`, and
`mul_eq_zero`. Merely subtracting those names would be unsound experimental
bookkeeping: `mul_ne_zero` and `two_large_factors_impossible` depend directly on
`mul_eq_zero`, while `prime_two` depends on it transitively through
`two_large_factors_impossible`. Model-v2 therefore excludes that complete
seven-name reverse-dependency closure from imports and retains exactly 56 records.

Constructing the complete checked identity replays every permitted theorem,
independently checks the resulting closed certificate, and binds the canonical
statement, dependency tuple, source-spec hash, exact tactic-script hash,
expanded-certificate hash, and proof node/depth metrics. That versioned document's
SHA-256 is `3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439`;
it is the library authority consumed by dataset attestation, training manifests,
evaluation, search, and the REPL.

The model does not need certificate hashes and node counts to choose `use add_assoc`. Its prompt
view is therefore a separate sorted projection of the same 56 names and canonical statements, with
its own statement-projection digest. For each proof state, a small deterministic weighted
token/ngram retriever selects eight records. The prompt contains those records, the repository-owned
25-head complete-line grammar, and the full checked-identity hash. This separation gives the model
useful lemma semantics without pretending that a prompt-sized list is the scientific authority.

The rest of the implemented stack closes the corresponding engineering gaps:

1. the proof-first generator fills at most 100,000 checked rows with a 2:1:1
   foundation/induction/library lane target and publication gates for every tactic head and import;
2. the tokenizer audit checks every selected example under the pinned Qwen revision and refuses
   any truncation at the 2,048-token boundary;
3. the search host asks for ranked sibling tactics, replays each path in a fresh transactional
   session, deduplicates canonical goal states, and enforces a hard depth ceiling of 32; and
4. the heavy Qwen3-1.7B BF16 rank-16 LoRA configuration and persistent local/WMI/Helios REPL use the same
   attested model-v2 authority. The REPL loads one adapter once and performs a second kernel replay
   before printing or saving a proof.

What remains is experimental rather than architectural. A final corpus must be generated and
attested under the current identity; a larger family-disjoint benchmark and its oracle routes must
be frozen; deterministic and pretrained baselines must run under the same bounds; and the heavy
1.7B adapter must be trained and evaluated. Actual transactional failures still need a separate
ranking/value release, and no expert-iteration round has run. Consequently there is no model-v2
solve rate, no evidence yet that beam search improves it, and no basis for calling the 1.7B model a
useful PA prover. LoRA-rank ablations and all 4B comparisons remain deferred until that baseline
exists.

The highest-leverage interface ablation is raw free-form tactic generation versus a hierarchical
legal-action policy: first choose one of the 25 heads, then point to an in-scope hypothesis,
variable, or retrieved lemma, and generate free PA terms only where a witness or intermediate
formula genuinely requires it. That design should reduce `/`, `lia`, and arity hallucinations while
remaining a tactic policy whose final product is an ordinary portable Peano Lab script.

## Reproduction and honest resume

A checkpoint name such as `checkpoint-100` is not an identity.  M19 binds a run to:

- the resolved TOML configuration and its digest;
- train and validation bytes plus their replay manifests;
- prompt version and prompt-contract digest;
- training source-tree digest;
- base model ID and requested revision;
- LoRA and optimizer settings; and
- the declared seed.

That identity is written before training.  Automatic resume locates the newest Transformers
checkpoint only inside the output directory and accepts it only when its adjacent run identity has
the expected digest.  It records the checkpoint artifact hash and global step.  This prevents
“resume” from quietly becoming warm-starting different code, data, or hyperparameters.

WMI's managed Torch 2.5.1 cannot safely load the Trainer optimizer pickle under the selected
Transformers release, so its first pilot is deliberately one-shot. It rejects a nonempty output
directory before dataset attestation, forces safetensors for base and model-weight files, and
refuses checkpoint resume entirely. Trainer checkpoints may still contain optimizer/scheduler
`.pt` state, but WMI never loads it. The final PEFT adapter is saved directly as
`adapter_model.safetensors`; loader-visible `.bin`, `.pt`, or pickle files in that final adapter are
rejected before PEFT is imported. A failed attempt is archived or given a new run identity; it is
never silently restarted into the same directory.

After training, `training-manifest.json` records the resolved model and tokenizer snapshots, base
configuration digest, replay attestation, source and input manifests, package versions,
attention/dtype choices, resume decision, example counts, and optimization metrics.  Adapter and
tokenizer outputs live in separate **closed directories**: the manifest lists and hashes every
regular loader-visible file, and loading rejects symlinks, missing files, mutations, or an extra
unattested file.  Hashing only a familiar weight filename would not be sufficient because model
loaders also interpret configuration and tokenizer files.

Trained evaluation derives its exact `PromptEnvironment` from the dataset attestation embedded in
that training manifest.  It checks the frozen held-out contract, zero-contamination statement,
train/validation hashes, capability preimage, and versioned prompt authority before loading or
executing the adapter; it does not replace those facts with a convenient hard-coded environment.
For the historical run that means the fixed `model-v1` authority. For model-v2 it additionally
means the full checked 56-theorem identity and the separate prompt-visible statement projection;
neither may be reconstructed from an adapter label. The evaluation report then embeds the
training-manifest identity, exact decode policy, evaluator source hash, goal-set hash, seed,
budgets, complete attempted tactic sequences, and per-attempt outcomes.

### From an adapter to a new checked theorem

A benchmark-only evaluator would leave the most interesting classroom question unanswered: after
post-training, can we ask the policy to try a theorem that was not named in the frozen four-goal
report? The underlying evaluator could already accept any closed `EvalGoal`; what was missing was a
careful command-line publication boundary. The new arbitrary-theorem mode is:

```console
python3 scripts/eval_trained_peano_policy.py \
  --adapter results/peano-policy/qwen3-1.7b-lora-wmi-smoke \
  --theorem 'forall n. exists x. n * (n + 1) = 2 * x' \
  --sample --k 16 --max-steps 24 \
  --output results/peano-policy/manual-proofs/even-product.json \
  --proof-output results/peano-policy/manual-proofs/even-product.pa
```

This interface was designed by following the authority backwards. The theorem comes from the user,
but the logic mode and tactic/library capabilities come only from the adapter's attested training
environment. Version 1 therefore remains intuitionistic `model-v1`; a caller cannot make a weak
policy look stronger by enabling the full surface, importing the target, or adding `auto`. Before
loading a billion-parameter model, the command also applies the ordinary one-line, control-character,
length, numeral, parser-depth, and closed-formula checks. A default custom run makes one greedy
attempt. Asking for `k > 1` requires sampling explicitly, because repeated deterministic decoding
would consume tokens without exploring anything new.

The publication path deliberately checks more than the in-memory success flag:

1. each rollout executes one generated tactic at a time through the production surface;
2. a rollout is labelled `proof` only after the independent kernel checks its certificate against
   the owner-retained original formula;
3. among checked rollouts, the exporter deterministically chooses the least proof nodes, then the
   fewest tactic lines, then the lowest sample index;
4. those commands are replayed from a fresh state under the same exact capabilities; and
5. only matching theorem, environment, command count, proof size, and a second kernel-checked QED
   permit creation of the `.pa` file.

The result is ordinary Peano Lab source beginning with `pa prove` and ending with `qed`. Pasting it
into the lab does not trust the previous run; it reconstructs and checks the proof once again. The
JSON sidecar records the adapter, decoder, sources, scheduler identity, every failed and successful
attempt, selected sample, proof nodes, exact replay authority, and SHA-256 of the emitted script.
Existing output paths are never replaced, and repository-local output must stay under `results/`
rather than source or a closed adapter/tokenizer directory. If search finds nothing, the command
exits one and emits no proof file. Dedicated model-free regressions exercise successful replay,
forged-success rejection,
unsafe/open formula preflight, capability widening, resource bounds, source mutation, no-proof
semantics, and output non-overwrite.

WMI adds one more boundary. An ad-hoc interactive allocation would not have the required immutable
source and submission-ledger identity, while a login-node Python lacks the accepted GPU runtime.
The repository therefore transports a theorem as data, never as shell code:

```console
scripts/wmi_prove_theorem.sh \
  --submit --confirm PEANO-LAB-WMI-TRAINING \
  --theorem 'forall n. exists x. n * (n + 1) = 2 * x' \
  --sample --k 16 --max-steps 24
```

This creates a bounded canonical JSON request with a fresh nonce, hashes its complete bytes, and
streams it under the deployment lock. Only the 64-hex request ID enters `sbatch --export`. Before
the held job is released, the controller has durably joined that ID and request hash to its Slurm
job in a second ledger. The A100 job then repeats request, runtime, adapter, evaluator, and kernel
checks. Digest-named evaluation, optional proof, and terminal summary artifacts live under
`results/peano-policy/user-proofs/`. No-proof is a valid checked search outcome; malformed
provenance remains a failed job.

#### Keeping model-v2 loaded for an interactive session

The guarded one-shot command now targets the attested model-v2 heavy adapter and uses bounded
kernel-guided search; it fails closed until that adapter exists. Model-v2 also has a persistent
client that loads one adapter once and reuses it across theorem queries:

```console
python3 scripts/peano_policy_repl.py \
  --adapter results/peano-policy/qwen3-1.7b-lora-v2-heavy
```

The user may enter either a bare closed formula or `pa prove FORMULA`. For each theorem the host
runs the transactional canonical-state beam search, by default to depth 32 with beam width 4, four
candidates per state, 128 model calls, and 2,048 discovered states. A failed candidate leaves its
siblings intact. A successful search is replayed through the headless verifier from scratch, and
only that second kernel-checked result is printed and saved as an ordinary `.pa` script beside a
structured report. Unique result names and no-overwrite publication preserve previous classroom
experiments.

When local hardware cannot hold the adapter, the same persistent loop can occupy one guarded WMI
A100 allocation:

```console
scripts/wmi_peano_policy_repl.sh \
  --connect --confirm PEANO-LAB-WMI-TRAINING
```

The wrapper validates the fixed deployment/runtime before starting a four-hour interactive
allocation, and theorem text enters only after the model is resident. A model trained on Helios can
be used in place before any cross-site artifact transfer:

```console
scripts/helios_peano_policy_repl.sh \
  --connect --confirm PEANO-LAB-TRAINING
```

That wrapper requests one GH200 under the fixed account and otherwise enters the same Python
client. All clients reject an unattested adapter or the wrong surface profile. The interfaces and
their model-free tests exist; the expected v2-heavy adapter does not yet, so this is not a
demonstration of model-v2 proof quality.
Neither interface translates English into PA, changes logic mode, or enlarges the adapter's theorem
authority.

Reproducible does not necessarily mean bit-identical floating-point training on every platform.
It means that any remaining nondeterminism is bounded and visible, and that nobody can mistake a
different model, environment, dataset, or checkpoint for the same experiment.

## Limitations and the next honest claims

The current work establishes that one small trained adapter can emit a shallow checked proof, but
not that fine-tuning caused the success or that the adapter is broadly useful for PA. Important
limitations remain:

- the only trained result is still the narrow 10,000-row model-v1 smoke; no model-v2 heavy adapter
  or quality measurement exists;
- the 100,000-row balanced generator is implemented and capacity-tested, but its final corpus must
  be generated, split, replay-attested, and passed through the tokenizer gate under the current
  56-theorem identity
  (`3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439`);
- the four-goal protocol set is a regression fixture, not a statistically useful final test, and
  hard whole-template OOD sets plus human-authored problems still need to be sealed;
- depth-32 verifier-guided beam search is implemented, but its gain with a trained model-v2 policy
  has not been measured and no expert-iteration round exists;
- no preference-training or reinforcement-learning result exists;
- no English-to-PA formalizer has been trained or semantically evaluated;
- the full content-bound library identity, prompt projection, and retrieval are implemented, but
  their usefulness remains an empirical question; and
- pretrained/deterministic baselines must precede the heavy evaluation, while all LoRA-rank and 4B
  comparisons remain deferred until the 1.7B model-v2 baseline exists.

The valid statement is therefore not “Peano Lab has a theorem-proving model.” It is narrower: one
exact 1.7B adapter, after training on the easy next-tactic distribution, failed the frozen
induction/order smoke and produced one independently checked proof for a new theorem from a
represented direct-witness schema. Peano Lab now also has the implemented infrastructure for a much
stronger model-v2 experiment, but no trained v2 result. Causal attribution and larger conclusions
must be earned by the pretrained baseline, model-v2 family splits, tokenizer-attested heavy run,
search comparison, and repeated measurements described above.

That restraint is the main pedagogical result.  A learned explorer can be cheap, fast, and
surprisingly inventive.  Its suggestions remain suggestions.  Peano Lab's kernel decides theorems,
and the experiment's manifests decide what scientific comparison was actually made.
