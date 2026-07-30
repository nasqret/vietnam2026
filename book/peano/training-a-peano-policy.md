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

```{admonition} Experiment status, 2026-07-30
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
checkpoint was trained or evaluated. It is retained as an auditable design stage, while model-v3
now supersedes it with the complete 247-theorem checked ladder, leakage-safe prefix trajectories,
a whole-session root-balanced synthetic curriculum, indexed completion logits, an immutable corpus
seal, and a native 32,768-token no-truncation gate. The first model-v3 preparation failed closed;
retry `172729` generated both source lanes and published the complete split, but its combined
allocation could not also finish independent replay and runtime gates. Exact-corpus continuation
`173040` now performs those checks from clean commit `5faa3d27`. No model-v3 optimizer step has run
and no adapter exists, so its proof quality and search gain remain unknown.
The historical reconciled model-v2 authority is 63 public entries, seven dependency-closed import
exclusions, and 56 permitted records. Model-v3 binds the later 247-entry ladder independently.
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

The normal per-proof trace ceiling remains 16 MB. The exact model-v3 library generator is one
reviewed exception: it selects a host-owned 128 MiB ceiling because a valid large certificate
crosses the ordinary bound. The Python API caps this override; it does not change the JSONL
transport's separate 512 MiB aggregate default, and an input JSON record cannot request it.

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
deferred until the 1.7B model-v3 baseline exists.  A formal-prover prior and a general base model of
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

A separately maintained candidate lemma library was authorized for publication. Its 26
dependency-ordered entries extend the public-catalog source from 23 to 49 theorems. All replayed
deterministically; the immutable pre-integration report records a largest fully expanded
certificate of 21,515 nodes at depth 66. Reconciliation with the first M20 branch then yielded the
historical 63-entry local snapshot because fourteen post-core records overlapped exactly. Later
native arithmetic passes and self-contained Cut packaging extend the current local candidate to
247 unique checked theorems: 23 baseline entries, 212 general foundational entries, and twelve
unique modular capstones. A twelve-rung tranche adds constructive equality, divisibility,
and primality decisions, bounded factor-pair search, proper-factor descent, and prime-divisor
existence. The next seven add modular-congruence transitivity and addition plus
functional single-position Gödel-β decoding. Five pre-CRT successors add
modular multiplication, decomposition-to-congruence transport, and the bridge
from a decoded β value to balanced congruence. Three reverse bridges add
bounded congruence uniqueness, reconstruction of the directed remainder, and
the converse β interface. The result is a checked equivalence between `At`
and bounded balanced congruence. Six CRT successors add the two modular
consequences of balanced Bézout, successor-modulus predecessor cancellation,
constructive binary CRT, its bounded-remainder form, and one code realizing
two bounded β positions under an explicit modulus-coprimality premise. Their
certificates contain no DNE. Six more checked entries prove each beta modulus
coprime to its base, reduce a common divisor of two beta moduli to the scaled
index gap, derive pairwise coprimality when $j=i+\mathit{gap}$ and
$\mathit{gap}\mid c$, apply that theorem to the two-position CRT client, and
construct bounded nonzero common multiples. The condition is essential:
$c=1$ gives moduli $3$ and $6$. Seven further entries convert the bounded
common-multiple invariant into bounded-prefix pairwise coprimality, close
coprimality under accumulated products, descend congruence from a product
modulus, and check the universal preservation step for a future bounded CRT
fold. Six more certificates add right-factor divisibility, the product and
decoded-congruence successor steps, their combined prefix step, and an
ordinary-induction theorem carrying the four-part invariant through every
bounded prefix. Its full-bound wrapper concerns residues already decoded from
the input code and is extensionally satisfied by choosing that code itself;
it was not yet an arbitrary finite-sequence recoding theorem. Later checked
layers add independent β finite-prefix recoding, exact Product traces,
greatest-prime-divisor descent, and canonical factorization existence and
extensional uniqueness. The native FTA certificate has 73,767 nodes, depth 99,
and 2,184 Cuts. The checked `prime_unbounded` client then closes the last
planned prime endpoint constructively from a bounded common multiple and a
prime divisor of its successor. None of those local snapshot counts claims that
production has already
been promoted.

The 247-theorem source-bound corpus has fingerprint
`6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`.
Its full-library smoke has 494 sessions, 9,235 raw/9,232 unique transitions,
and all 247 authored QEDs. Browser build `2026-07-29k`, application
`a-77df7c0860bc`, records the local candidate and does not claim deployment.

For training, the current 247-theorem catalog is registered as the distinct content-addressed
`model-v3` successor authority, not as a silent extension of model-v1 or model-v2. The prompt
exposes bounded retrieved lemma names and canonical statements, and the library corpus contains
downstream `use` and authored proof trajectories. Once an exact capstone theorem is importable,
its three-line application is a usability test rather than an unseen proving test; different
theorem families must remain sealed.

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
`mod5_fourth_power_one` belongs to the authorized public catalog and the current local candidate,
applying it in an environment that exposes it measures retrieval and application, not discovery
of the fourth-power theorem.

Some audited full states are also substantially longer than model-v1 data: median 323 characters
and maximum 4,869. Much of the excess repeats context across sibling goals. The model-v2 representation
retains the complete canonical goal array, adds the grammar, and retrieves only eight
name/statement records. A later observation ablation may compact sibling descriptions, but policy
sufficiency of that representation must be measured rather than assumed.

## Model-v2: the historical correction design

This design correction was implemented, although its heavy experiment did not run. Its most important
idea is that **what identifies the theorem authority is not what must fit in every prompt**.

1. Freeze 50--100 or more sealed roots across induction, order, divisibility, residues, lemma
   composition, and human-authored problems. Replay every reference within a 32-step oracle budget.
2. Run the pretrained Qwen3-1.7B base, current adapter, deterministic tactics, and a simple
   state-shape baseline under identical token, model-call, and kernel-call budgets.
3. Bind a content-addressed successor snapshot under a new prompt version. Show compact PA syntax
   and retrieved lemma names with canonical statements instead of only an opaque hash.
4. Generate 100,000--150,000 positive transitions from at least 10,000 checked roots, with every
   tactic head represented, 20--30% induction/IH trajectories, 20--30% lemma retrieval and
   composition, and proof-length strata 1--7, 8--15, and 16--32.
5. Store two to four actually executed rejected candidates per positive state in a separate
   ranking/value corpus. Never relabel them as successful SFT examples.
6. Train the 1.7B model for two or three complete balanced epochs and select checkpoints by
   kernel-judged development QED, not token loss alone.
7. At each immutable state, sample 8--16 candidates, execute them transactionally, discard failures,
   deduplicate canonical successor states, and retain siblings in a bounded best-first frontier.
8. Only then compare LoRA ranks or a 4B model under fixed data, seeds, update counts, and search
   budgets.

The highest-leverage interface ablation is raw free-form tactic generation versus a hierarchical
legal-action policy: first choose one of the 25 heads, then point to an in-scope hypothesis,
variable, or retrieved lemma, and generate free PA terms only where a witness or intermediate
formula genuinely requires it. That design should reduce `/`, `lia`, and arity hallucinations while
remaining a tactic policy whose final product is an ordinary portable Peano Lab script.

## Model-v3: checked prefixes and balanced roots

Model-v2 identified the right ingredients but was designed around a much smaller library. Model-v3
turns the complete declaration-ordered 247-theorem ladder into the training authority. The identity
gate binds every theorem's canonical statement, direct dependencies, source specification, authored
script, reconstructed certificate, node count, and depth. It then reconstructs every certificate
from the authored tactics and asks the independent kernel to check it from the empty context against
the original closed proposition. A catalog row is therefore evidence to be verified, not an oracle
that can attest itself.

Library supervision follows a strict predecessor-prefix rule. For theorem number $i$, both the
executable capability and prompt library are exactly the declaration prefix
$\mathrm{THEOREMS}[:i]$. The target and all later theorems are unavailable. Its trajectory first
imports only its declared direct dependencies with ordinary `use` commands and then executes the
authored tactic script unchanged. The dataset compiler replays that complete QED again before
emitting next-tactic rows. This produces useful theorem-composition examples without letting the
policy retrieve the answer it is being taught to prove.

The observation remains compact. Prompt v3 includes a compact inventory of every allowed theorem
name in the current prefix, then deterministically scores the full propositions and displays at
most twelve detailed `name : statement` records. This distinction matters: an audit of statement
retrieval alone exposed only 242 of 640 direct-dependency `use` labels at $K=12$. The name inventory
keeps every legal dependency selectable without copying every large proposition into every prompt.
Very large displayed statements use a bounded canonical excerpt with a content marker; the full
checked identity and prefix digest remain in the environment record. Thus the prompt can be small
without weakening the authority that the dataset, adapter, evaluator, and replay attestation bind.

Large proof states needed a different kind of sharing. Prompt v3 encodes canonical one-line goals
with `shared-declarations-v1`: one deterministic first-occurrence table contains every exact
comma-delimited context chunk, a second contains every exact target, and each visible goal contains
only a vector of declaration indices and a target index. The parser reconstructs every original
goal byte-for-byte and rejects duplicate, unused, reordered, non-integer, or out-of-range table
claims. This is a lossless structural encoding, not target truncation and not a lossy model
observation. Raw trace states, row `state` fields, held-out structural checks, replay, and kernel
inputs remain unchanged; prompt versions 1 and 2 remain byte-identical.

The encoded state JSON must fit 44,000 Unicode characters or prompt construction fails. No exact
target, hypothesis, or visible name is shortened to satisfy this limit. A retained audit of all 443
states around the index-230 stress theorem measured a maximum of 39,423 encoded characters; its
step-115 state shrank structurally from 196,457 legacy characters to 37,259. The exact largest-state
check is 29,111 tokens including tactic and EOS, leaving 3,657 tokens below Qwen's 32,768 native
window. All 222 exact transition prompts for this stress proof pass (median 17,444, p95 26,662,
p99 28,537, maximum 29,111). The complete pinned-tokenizer combined-corpus scan remains the final
acceptance gate.

The synthetic half corrects a subtler model-v2 failure. Artificial implications had wrapped many
otherwise different roots, making `intro gate` the first label far too often and even hiding real
induction roots. Model-v3 removes those induction gates by one checked immutable transformation and
schedules complete kernel-checked sessions by their genuine first tactic head. The catalog has 51
proof-first schemas across 14 root heads; root-session imbalance is bounded and `intro` may account
for at most 20% of emitted sessions. Library schemas are deliberately absent here because the exact
247 predecessor-prefix trajectories provide that supervision separately.

That gate removal exposed a useful generator-design trap. The implication was not only a proof
obstacle: it was also the sole index-varying text in each inherited induction statement. Deleting
it therefore collapsed thousands of intended examples to four canonical roots. The repair adds a
six-digit base-4 expression made entirely from terms `d * 0`. It has 4,096 syntactically distinct
values per induction schema, remains arithmetically zero, and leaves `induction` as the first
tactic. Closed-zero syntax creates statement diversity here without pretending to add new
mathematical difficulty.

The first WMI preparation run, job `172536`, found a separate finite-domain defect. It completed
all 247 checked library trajectories—8,494 transitions and 247 QED footers—then failed after
1:02:34 when `root-equality-ring` generated a product with normalized coefficient 132. The `ring`
tactic correctly rejected it because its reviewed limit is 128. The corrected domain enumerates
the 2,396 safe base-7 tuples, excluding the four coefficient-132 tuples and the one
coefficient-144 tuple. Pairing those tuples with sixteen compact two-digit base-4 zero tags yields
38,336 distinct safe ring statements. Because the failed run had already exercised schema catalog
version 1, this repaired catalog is explicitly version 2 rather than silently changing the meaning
of an old identity.

The deeper repair treats scheduling like a compiler prepass. Before executing any proof or
creating output files, a model-free planner canonicalizes every proposed statement, enforces
uniqueness and finite-domain capacity, checks the exact row total, the `intro` cap, and root-head
balance, and hashes the ordered schedule. A valid candidate that exactly equals a sealed evaluation
formula follows one narrow typed exclusion path and is counted; malformed candidates still abort.
The expensive execution must reproduce the planned counts, skip counts, and digest exactly. A
final-row edge case required one more rule: among equally deficient heads, prefer the
heads whose shortest sessions are longer, reserving one-row heads for exact completion. For seed
`peano-policy-v3-balanced-wmi-20260729`, this prepass gives exactly 70,000 rows in 32,600 distinct
sessions, covers all 51 schemas, and assigns 2,328 or 2,329 sessions to every one of the fourteen
heads. The pinned sequence digest is
`79d2704eab6eb73205ff2234f55f0d4a7e034176fe8dc8649c6950ff499d547b`. The registered version-2
plan needs no duplicate or overlong-session skips; both closed-`norm_num` schema families contribute
1,164 distinct roots. At the advertised 100,000-row maximum, the same prepass produces 46,574
unique sessions and safely counts and omits the one numeric candidate equal to a sealed target.
WMI now invokes the synthetic generator before the library generator, allowing this seconds-long
prepass to reject a bad launch before either corpus begins expensive proof replay. An upfront
empty-data-directory gate likewise rejects stale partial-run artifacts before either generator
starts.

Job `172536` exited with status 2 before dataset construction, attestation, tokenization, A100
smoke, training, or evaluation. Transactional staging published no partial synthetic corpus. The
figures above describe the corrected deterministic plan, not a completed corpus or learned-model
result.

Attestation accepts the combined release only if it reconstructs every prefix from 0 through 247,
finds the exact predecessor-prefix plus full-synthetic schedule, rebuilds the dataset from raw
traces, and observes zero held-out contamination. Tokenization is another fail-closed gate: every
selected train and validation sequence must fit the pinned Qwen tokenizer under its native
32,768-token position limit. A root-probe audit already found 57 of 247 full-prefix theorem prompts
above the invalid 4,096-token draft ceiling, with a maximum of 6,235. The complete-data audit may
still reject the native limit; there is no truncation path.

The old model-v2 regression targets now occur in the training ladder, so reusing them would measure
library retrieval rather than theorem discovery. Model-v3 therefore seals four different formulas:
one closed arithmetic equality, one existential subtraction witness, a doubled right-zero identity,
and the consecutive-product-even theorem. Their exact names and canonical formulas are bound in the
attestation, and the generator rejects them before execution.

These four are a launch smoke, not a comprehensive benchmark: three deliberately calibrate short
arithmetic behavior and only consecutive-product-even requires multistep induction. General proof
quality requires a larger hidden post-training suite covering induction, theorem composition,
order, divisibility, and quantified witnesses under the same kernel-checked search budget.

The original draft registered two epochs over a row-prefix-capped population. The implementation
audit rejected both choices for the first model-v3 run. A row prefix can cut a proof session or
discard a small theorem rung, and a second traversal doubles the dominant long-context cost before
one exact pass has established a baseline. The successor protocol below retains every library
transition, selects synthetic data by whole proof sessions, derives one pass from the selected row
count, and records the exact optimizer-step total before loading the model. This is still a run
specification, not a result: no model-v3 optimizer step, adapter, solve rate, or comparison is
claimed here.

## From a checked population to one auditable training run

The long model-v3 build revealed that “the dataset” names three different objects:

1. a **historical replay population**, whose proofs and transitions were produced under one clean
   source commit;
2. a **selected curriculum**, which admits all library rows and a balanced subset of complete
   synthetic sessions; and
3. a **tokenized optimization schedule**, whose linear and quadratic costs depend on one pinned
   tokenizer.

Conflating these objects creates subtle scientific errors. Replaying 78,494 transition rows does
not mean all of them should be trained equally; choosing the first $N$ rows is not neutral; and a
row count is a poor compute measure when sequence lengths range over orders of magnitude. Model-v3
therefore gives each object its own canonical, self-digested attestation.

### Whole-session selection

All 8,494 exact catalog-prefix transitions are mandatory. Synthetic data is selected under a
12,288-row ceiling, but a session is indivisible: either every one of its tactic transitions is
present or none is. The selector first places one complete anchor for each of the 51 schemas. It
then adds complete rounds across all 14 genuine root heads, using a seed-derived content rank and
stopping before the next round would exceed the ceiling. The algorithm is independent of input
file order and binds both the entire candidate population and the chosen rows.

This means the final number of synthetic rows need not equal 12,288 exactly. A few unused slots are
evidence that the proof boundary was respected, not wasted data. A second `max_train_samples` cap
would be dangerous because it could slice the already audited selection; model-v3 configurations
reject it. The selection seed must also equal the training seed, so there is one declared source of
randomness rather than two identities that happen to agree in a particular run.

The tokenizer pass then records, for every selected row, its token IDs, sequence length $L_i$, and
number of supervised completion tokens $C_i$. It enforces explicit ceilings on

$$
  \sum_i L_i, \qquad \sum_i L_i^2, \qquad \max_i L_i,
  \qquad \text{and} \qquad \max_i C_i.
$$

The squared term is a deliberately conservative proxy for attention work. These bounds prevent a
small-looking row budget from hiding an accidental long-context explosion. No tokenizer result may
be truncated to pass the gate.

### Indexed completion logits preserve the objective

Each example is still the repository-owned prompt followed by one tactic line and EOS. Prompt
labels use the ignore index, and the completion is one contiguous suffix. In a causal language
model, the logit vector $z_i$ predicts token $y_{i+1}$. If $S$ is the set of supervised labels,
ordinary completion-only cross entropy is

$$
  \mathcal{L}
  = \frac{1}{|S|}
    \sum_{(b,j)\in S}
      \operatorname{CE}\!\left(z_{b,j-1}, y_{b,j}\right).
$$

Most model-v3 prompt positions are masked, yet a conventional forward pass materializes a
vocabulary-sized logit vector at every one of them. Qwen3 exposes `logits_to_keep`; Peano Lab asks
for only the union of positions $j-1$ appearing in the sum above. Targets for shorter rows remain
ignored after right padding. Cross-entropy numerators are accumulated in FP32 and divided by the
exact number of supervised tokens across the whole gradient-accumulation window.

Nothing in the equation changes. This is the same loss and the same gradient with a smaller final
activation tensor. The implementation fails closed if the model does not explicitly advertise the
indexed-logit argument, a row violates the suffix/right-padding contract, multiple GPUs are hidden
behind `DataParallel`, or distributed token accounting is ambiguous. A pinned Qwen3-1.7B LoRA
probe compared the full and projected forms and found matching loss and gradients to numerical
precision.

### Why a historical corpus needs a seal

Proof generation and independent replay can take hours. Trainer code may improve while that job is
running. Two tempting responses are both wrong: mutating the old deployment destroys provenance,
while copying an untracked `data/` directory into new code asks the new trainer to trust anonymous
bytes.

The model-v3 corpus seal preserves the useful separation. It accepts exactly twelve dataset files
and the historical preparation's three reports, validates their internal source/job/authority
relations, copies them into a private directory, fsyncs and re-hashes them, publishes with a
non-replacing rename, and makes the closed tree read-only. Symlinks, hard-link aliases, non-regular
files, unexpected names, malformed JSON, mixed Slurm jobs, or a changed source during copying are
fatal. The last source-path comparison includes mode and link count as well as identity, size, and
timestamps. A failed creation retains its visibly partial stage: pathname-based cleanup could both
mask the original I/O failure and delete a replacement installed after inspection. One
`content_sha256` binds the complete result.

There is a bootstrapping wrinkle: the first seal must preserve the old unsealed corpus and reports
while using the newer sealing code. Deployment explicitly protects those historical paths. The
tracked one-time CPU job `peano_wmi_seal_v3_corpus.sbatch` pins job `173040`, its clean source
commit, destination, manifest, all twelve artifacts, and both reviewed source hashes. The
authenticated dataset-attestation report is now pinned at
`4e1cf0d00725a739d6f371062ff2079cfb9bc3e36daf4f4219cbbe1399a68a12`;
the token audit is now pinned at
`c290b285eabcf9d39ab13b4d6f0f194588541484390d35c00681041979e2f8d8` after checking all 64,500
train and 6,000 validation rows. The A100 runtime smoke is pinned at
`86cc35bfcf2d5ff51931c140f3eb7168e3f641e1f80d54a3984dba9e49e40749`; it passed on the immutable
Qwen3-1.7B revision with rank-32 LoRA and 34,865,152 trainable parameters. All three report anchors
are therefore installed. A reviewed WMI Python verifies all inputs and retains a no-replace probe
on the target filesystem.
The job then makes and retains a fresh private bootstrap containing only the CLI and standard-
library seal module; its staged inventory forbids package markers and bytecode caches. A launcher
embedded in the submission-hashed job stable-reads and hashes the CLI, then compiles exactly those
verified bytes with isolated Python; the CLI performs the same closed-tree and external-anchor
checks on the module and corpus. Thus neither `__init__.py`, `.pyc`, nor a replaced pathname
silently joins the trusted program. Seal recovery verifies an existing destination and atomically
publishes only a canonical same-job report, closing the crash window without replacing the seal.
The destination is classified before the mutable historical paths are inspected, so recovery reads
only sealed copies and literal anchors even if the originals have since been retired. The retained
no-replace probe covers both atomic publications only after the seal and report parents are proven
to share one filesystem device. Existing reports are freshly verified, fsynced with their parent,
and verified again; a failed publication retains its read-only sibling stage rather than risking
deletion of a pathname that changed after inspection.

A seal is not a signature. The expected historical commit, job ID, and content digest must be
obtained independently. Current code first verifies those external anchors and every sealed byte,
then compares its compiler/kernel source inventory, prompt contract, held-out formulas, and
247-theorem authority against the historical manifest. The old attestation proves how the corpus
was produced; the new eligibility record proves that current code assigns the same meaning. This
avoids a second multi-hour proof replay without turning mutable artifacts into authority.

### The four-stage WMI chain

The new GPU path is intentionally split:

1. **Sealed preparation** performs no theorem generation. It verifies current-source eligibility,
   tokenizes every selected row, and runs a real BF16 LoRA optimizer/save/reload smoke. The smoke
   exercises the longest active sequence and the largest supervised completion together: when no
   natural row realizes both maxima, it inserts attended, label-masked prompt tokens immediately
   before the longest completion's supervised suffix. This reaches the maximum active length even
   for attention implementations that discard zero-attention padding. After freeing the manual
   optimizer state, the smoke also executes one real `CompletionOnlyTrainer` optimizer step and one
   explicit evaluation on the same envelope. Every trainable LoRA parameter must receive a finite
   gradient, adapter tensors must change, and deterministic post-update logits/loss must equal those
   from the reloaded adapter. A shared runtime gate also rejects every distributed/plugin path:
   exactly one process and visible GPU, matching `cuda:0` Trainer and Accelerator devices, BF16,
   `DistributedType.NO`, `DynamoBackend.NO`, no DeepSpeed/FSDP/tensor parallelism, exact Trainer
   accumulation, and Accelerator backward divisor one. The last condition prevents a second
   environment-driven division of an objective already normalized over its complete token
   accumulation window. Training rejects a missing whole-window `num_items_in_batch`, while
   evaluation uses the local supervised-token mean. Non-reentrant checkpointing, AdamW constants,
   and unfiltered non-finite logging are explicit arguments rather than inherited defaults.
   Trainer's built-in clip is disabled because it precedes `on_pre_optimizer_step` and permits a
   non-finite norm; the callback audits raw gradients, clips to norm 1.0 with
   `error_if_nonfinite=True`, and audits the post-clip population before optimization.
2. **Training** depends on that exact preparation job and verifies its three reports again. It
   requires one visible A100, one process, fresh output, no resume, and one row-count-derived pass.
   Trainer checkpointing and periodic evaluation are disabled outright; intervals beyond the run
   are insufficient because the default callback can still request a terminal checkpoint at
   `max_steps`. The trainer's actual optimizer-step count must equal the precomputed count. The
   adapter and tokenizer are
   saved before the explicit full validation pass, preserving the learned tensors if that late
   pass reaches a wall-time or runtime failure. Stock Trainer evaluation averages per-batch token
   means, so this pass is finite lifecycle evidence rather than a corpus-global completion-token
   NLL. The final manifest remains stricter: it appears
   only after validation and all identity rechecks succeed.
3. **Evaluation** depends on that exact training job. Four frozen goals use sampled
   kernel-guided search with depth 32, beam width 16, eight candidates per state, 512 model calls,
   4,096 states, and 256 generated tokens per candidate. Before loading weights, the evaluator
   equates the manifest's training-job ID, the exported predecessor ID, and the submission-ledger
   dependency; independent replay checks the recorded binding. Later interactive proof requests
   are labelled separately because they consume an already completed adapter and have no false
   `afterok` edge.
4. **Independent replay** loads no model. It accepts only the exact evaluator-v4 authority and
   search budget, checks all duplicated counters and proof payloads, and sends every attempt marked
   `proof` through a fresh `verify_proof` call against its original goal. It emits a canonical
   non-overwriting attestation.

### What “training completed” means

A Trainer return value is not itself an admissible model. In the one-pass model-v3 run, the final
manifest requires five copies of the optimizer-step count to agree: the preflight schedule,
top-level result, `TrainOutput`, `TrainerState.global_step`, and `TrainerState.max_steps`. Its
gradient callback observes the still-unincremented state at every boundary, so event $k$ must see
state $k-1$. Every raw trainable gradient must exist and be finite. Trainer's earlier permissive
clip is disabled; the callback performs the only clip with max norm $1$ and
`error_if_nonfinite=True`, checks the post-clip tensors, and retains all finite pre-clip norms.

The adapter itself supplies a second independent completion test. Before the first update and after
the last, the runner sorts the trainable names and hashes canonical records containing each name,
dtype, shape, and raw-content SHA-256. The population must remain identical, every final tensor must
be finite, and at least one tensor record must change. Thus 650 callback events around a no-op or
miswired optimizer do not become a usable adapter.

That still identifies a Python object, not the directory students will later load. Model-v3 adds a
third test: **saved-policy admission**. Before releasing the live model it chooses three
deterministic SHA-ranked probes from the admitted train and validation populations. The selection
binds the complete candidate population and the run identity, but never sees the four frozen
theorem-discovery goals. For each probe the runner stores compact fingerprints of the exact
tokenization, indexed completion loss, and projected-logit tensor. It also fingerprints PEFT's
canonical save-format tensor map, including every sorted name, dtype, shape, and raw-content hash.

The Trainer, optimizer, original tokenizer, and original model are then released. One fresh,
local-only load reconstructs the pinned Qwen commit, saved tokenizer, and single `default` adapter.
The admission gate reads the actual safetensors directly and requires three identities to agree:
the terminal in-memory PEFT population, the persisted tensor population, and the freshly populated
PEFT model. It retokenizes every probe and requires byte-exact projected logits and exact finite
losses. Finally it disables the adapter and requires at least one probe to change. This last check
distinguishes “LoRA files were attached” from “LoRA participates in the policy.” The compact result
is joined to the base configuration, run identity, `cuda:0` runtime, individual adapter files,
closed adapter/tokenizer trees, and completed-training hashes. A v3 manifest lacking any join is
not loadable.

The lifecycle audit found why these comparisons must surround evaluation as well as saving. In the
[pinned Transformers 4.53.3 implementation](https://github.com/huggingface/transformers/blob/v4.53.3/src/transformers/trainer.py),
`bf16_full_eval=True` calls
`model.to(dtype=bfloat16)` before the full evaluation loop. PEFT 0.16 normally keeps LoRA weights in
FP32, so that flag would mutate the learned policy after its terminal fingerprint and
serialization. Production keeps BF16 autocast but pins `bf16_full_eval=False`, then fingerprints
the trainable population after serialization and again after explicit evaluation. Equality is
required at both boundaries.

The exact Trainer history has 65 periodic records at steps 10 through 650, followed by one final
training summary and one explicit validation summary, both at step 650. Extra, reordered,
non-finite, or inconsistent records are rejected. The reported `train_loss` is a mean of
optimizer-window completion-token means; with evaluation batch size one, `eval_loss` is a mean of
per-example completion-token means. These are useful diagnostics, but neither is mislabeled as the
corpus-global token NLL.

All this evidence, the observed single-GPU runtime and Trainer arguments, and the closed adapter
and tokenizer hashes enter one canonical `training_evidence` object. Model-v3 inference and the
same-base comparison validate it before importing a model framework. The strict manifest reader
rejects duplicate keys, NaN/Infinity, links, and a file that changes while being read. Earlier
prompt-v1/v2 artifacts preserve their historical contract; they cannot manufacture a v3
completion record.

Recovery publication has an environmental premise as well as a code proof. Immediately before
scheduled training, publication-preflight v2 exercises both a protected directory and a protected
regular file on the exact output filesystem. Its retained tree and exclusive report bind modes,
inodes, device, byte hashes, the attempted native syscall, and one profile selected for both node
types. The trainer includes that record in its run identity, threads the selected profile through
every authoritative publication, and checks the live probes again before final publication. This
turns “the shared filesystem probably supports our publication rule” into a tested precondition.

The preferred profile remains `renamex_np(RENAME_EXCL)` on macOS or
`renameat2(RENAME_NOREPLACE)` on Linux. WMI's Ceph filesystem returns `EINVAL` for the Linux flag.
Only `EINVAL`, `EOPNOTSUPP`/`ENOTSUP`, or `ENOSYS` permits the Linux fallback. It atomically claims
the absent final name with a type-matched empty object: an owned `0700` directory or a zero-length,
single-link `0600` regular file. Parent and claim descriptors stay open while device, inode, type,
owner, mode, and emptiness are checked, fsynced, and checked again. A descriptor-relative plain
rename then atomically replaces only that owned claim with the complete stage. Success requires
source disappearance, staging-inode continuity at the canonical name, claim-inode displacement,
and a final parent fsync.

That fallback is not mislabeled as atomic no-replace. Its claim is briefly visible, and a crash
may leave a permanent empty canonical reservation plus a complete private stage. Existence alone
is therefore never authority; all readers require the complete protected tree or canonical
manifest. Failures remain for manual audit and are never cleaned up or automatically adopted. The
last identity-check-to-rename interval is not secure against a malicious same-UID process, so the
contract explicitly retains the project's non-hostile-same-owner premise. The preflight-selected
profile is passed to run identity, recovery snapshots, adapter, tokenizer, and final manifest; a
production call never silently renegotiates it.

The corpus seal's canonical verification report uses schema v2 to make the distinction
machine-readable. It binds the admitted profile, both exercised source types, whether the final
operation had true atomic destination-no-replace semantics, and whether a transient exclusive
claim was used. Existing-report recovery recomputes that exact record from the requested profile,
so a retry cannot reinterpret claim publication as native publication (or the reverse).

Final artifacts use the same primitive rather than an overwriting library rename. The runner first
claims a fresh output directory with exclusive `mkdir` and records the output and parent devices,
inodes, and modes. Adapter and tokenizer are serialized into private `.partial-…` siblings, made
read-only, fsynced, closed-tree checked, and atomically installed without replacement. The run
identity and final manifest are exclusive read-only files; the output identity is checked again
immediately before the manifest is published. A crash may leave conspicuously partial bytes, but a
retry or competing writer cannot silently turn them into a different completed run.

“Closed tree” includes filesystem objects, not merely the files returned by a convenient glob. The
hash pass rejects symlinked components and directories, special nodes, cross-device children, and
hard links. Every file is opened with `O_NOFOLLOW` and its device, inode, mode, link count, size,
mtime, and ctime must remain equal before, during, and after descriptor-bound hashing; a second tree
inventory detects concurrent insertion. Model-v3 finalization and loading additionally require
directories to be `0555` and files `0444`. The opt-in protection rule leaves historical v1/v2
artifacts loadable under their original contract.

The mode switch is tied to semantics, not to an optional filename convention. A prompt-v3 dataset
is accepted if and only if the model-v3 curriculum is configured, and this relation is checked
before framework imports. After saved-policy admission, training repeats the protected-tree
verification at the last possible boundary before the no-replace manifest publication. Direct
inference and the pretrained-base control likewise verify the adapter and tokenizer snapshots both
before and after loading them. Recovery uses the same exact `0555`/`0444` contract. These checks
close accidental mutation and provenance gaps; they do not create a hostile-same-owner security
boundary, because such an owner can chmod and race path observations.

The relevant entry points are
[`scripts/seal_peano_v3_corpus.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/scripts/seal_peano_v3_corpus.py),
[`scripts/verify_peano_v3_corpus_eligibility.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/scripts/verify_peano_v3_corpus_eligibility.py),
[`slurm/peano_wmi_prepare_v3_sealed_training.sbatch`](https://github.com/nasqret/vietnam2026/blob/peano-lab/slurm/peano_wmi_prepare_v3_sealed_training.sbatch),
and
[`scripts/replay_peano_v3_evaluation.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/scripts/replay_peano_v3_evaluation.py).
The binding command sequence and pending-result ledger live in
[`docs/PEANO_TRAINING.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_TRAINING.md#106-model-v3-sealed-curriculum-indexed-objective-and-launch-chain).

At this documentation checkpoint, WMI job `172729` has generated both source lanes and published
the complete split. Exact-corpus continuation `173040` is still performing independent attestation,
so the corpus seal digest, new sealed-preparation job, selected token counts, optimizer-step count,
adapter hashes, losses, evaluation job, solve results, and independent replay digest are all
explicitly **pending**. An A100 reserved by CPU preparation is not evidence that transformer
training has begun.

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
attention/dtype choices, resume decision, example counts, optimization metrics, every strict
gradient boundary, adapter-change fingerprints, exact log history, and live recovery-filesystem
evidence. Adapter and
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
  --sample --max-new-tokens 96 --max-steps 24 \
  --search-beam-width 8 \
  --search-candidates-per-state 16 \
  --search-max-model-calls 512 \
  --search-max-states 4096
```

This creates a version-2 canonical JSON request with a fresh nonce. Its hash commits to
kernel-guided-search mode and all six host-owned bounds: generated tokens per candidate, depth,
beam width, candidates per state, model calls, and discovered states. The wrapper streams its complete bytes under the deployment
lock; only the 64-hex request ID enters `sbatch --export`. Before the held job is released, the
controller has durably joined that ID and request hash to its Slurm job in a second ledger. The A100
job then repeats request, runtime, adapter, search-report, and kernel checks. Older version-1 request
files retain their original rollout semantics, while the new wrapper rejects the old `--k` rollout
flag instead of giving it a different meaning. Version 2 names the immutable request/search
protocol rather than a prompt version: it accepts only the exact sealed model-v2 or exact sealed
model-v3 authority recovered from the chosen adapter manifest, verifies the complete adapter and
tokenizer snapshots before and after evaluation, and
requires exact per-goal, decoder, and aggregate search accounting. Digest-named evaluation,
optional proof, and terminal summary artifacts live under `results/peano-policy/user-proofs/`.
No-proof is a valid checked search outcome; malformed provenance remains a failed job.

#### Keeping model-v3 loaded for an interactive session

The guarded one-shot WMI command targets the attested model-v3 247-theorem adapter and uses bounded
kernel-guided search. Its defaults are 96 generated tokens per candidate, depth 32, beam width 4,
four candidates per state, 128 model calls, and 2,048 states; it fails closed until that adapter
exists. The Python client remains compatible with an exact attested model-v2 adapter. A persistent
client loads one adapter once and reuses it across theorem queries:

```console
python3 scripts/peano_policy_repl.py \
  --adapter results/peano-policy/qwen3-1.7b-lora-v3-library \
  --max-new-tokens 256
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
allocation, and theorem text enters only after the model is resident. The earlier model-v2-heavy
adapter remains usable in place on Helios through its separate launcher, without a cross-site
artifact transfer:

```console
scripts/helios_peano_policy_repl.sh \
  --connect --confirm PEANO-LAB-TRAINING
```

That historical wrapper requests one GH200 under the fixed account and enters the same Python
client with its model-v2-heavy path; the WMI wrapper is pinned to model-v3. Both reject an
unattested adapter or the wrong surface profile. The interfaces and their model-free tests exist;
the model-v3 result remains pending until real optimizer training and evaluation finish, so this is
not yet a demonstration of model-v3 proof quality.
Neither interface translates English into PA, changes logic mode, or enlarges the adapter's theorem
authority.

The causal control is now a different program, not an evaluator flag. Once the model-v3 adapter
has completed, `eval_pretrained_peano_policy.py` verifies that final manifest and its closed
adapter/tokenizer trees, loads the saved tokenizer and pinned Qwen base revision, and deliberately
does not import or attach PEFT. It then runs the same four goals at seed 20260728 with depth 32,
beam 16, eight candidates per state, 512 model calls, 4,096 states, and 256 generated tokens. The
report says `peano-policy-pretrained-base-v1` and binds the comparison manifest plus both closed
tree hashes. Keeping this identity and WMI job separate prevents base-model behavior from being
misreported as adapter behavior. The trained-adapter independent replay gate remains narrow and
does not accept the control identity; a control replay attestation would be a separate protocol.
The implementation and model-free tests are complete, but no control result is claimed before the
comparison adapter itself exists.

Reproducible does not necessarily mean bit-identical floating-point training on every platform.
It means that any remaining nondeterminism is bounded and visible, and that nobody can mistake a
different model, environment, dataset, or checkpoint for the same experiment.

## Limitations and the next honest claims

The current work establishes that one small trained adapter can emit a shallow checked proof, but
not that fine-tuning caused the success or that the adapter is broadly useful for PA. Important
limitations remain:

- the only trained result is still the narrow 10,000-row model-v1 smoke; no model-v2 or model-v3
  heavy adapter or quality measurement exists;
- model-v3's 247-theorem identity, strict predecessor-prefix generator, 51-schema root-balanced
  generator, whole-session selector, indexed completion objective, immutable-seal/current-source
  eligibility gate, and independent evaluation replay are implemented; retry `172729` produced
  both source lanes and the complete split, while exact-corpus continuation `173040`, historical
  reports, seal, selected token audit, and the new sealed-preparation gate must all finish before
  the registered WMI training run;
- the four-goal protocol set is a regression fixture, not a statistically useful final test, and
  hard whole-template OOD sets plus human-authored problems still need to be sealed;
- depth-32 verifier-guided beam search is implemented, but its gain with a trained model-v3 policy
  has not been measured and no expert-iteration round exists;
- no preference-training or reinforcement-learning result exists;
- no English-to-PA formalizer has been trained or semantically evaluated;
- the full content-bound library identity, prompt projection, and retrieval are implemented, but
  their usefulness remains an empirical question; and
- pretrained/deterministic baselines must accompany the heavy evaluation, while all LoRA-rank and
  4B comparisons remain deferred until the 1.7B model-v3 baseline exists.

The valid statement is therefore not “Peano Lab has a theorem-proving model.” It is narrower: one
exact 1.7B adapter, after training on the easy next-tactic distribution, failed the frozen
induction/order smoke and produced one independently checked proof for a new theorem from a
represented direct-witness schema. Peano Lab now also has the implemented infrastructure for a much
stronger model-v3 experiment, but no trained v3 result. Causal attribution and larger conclusions
must be earned by the pretrained baseline, model-v3 family splits, tokenizer-attested heavy run,
search comparison, and repeated measurements described above.

That restraint is the main pedagogical result.  A learned explorer can be cheap, fast, and
surprisingly inventive.  Its suggestions remain suggestions.  Peano Lab's kernel decides theorems,
and the experiment's manifests decide what scientific comparison was actually made.
