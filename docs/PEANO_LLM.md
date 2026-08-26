# Peano Lab M9 data and evaluation protocol

> **Historical M9 contract.** This document describes the original trace
> release and evaluator that intentionally stopped before model training.  The
> subsequent M19 headless runner, replay-compiled policy rows, fixed `model-v1`
> authority, pinned sub-10B training experiment, and evaluator v4 are specified
> in [`PEANO_TRAINING.md`](PEANO_TRAINING.md). Where the two differ, the M19
> protocol governs that historical model experiment; the raw binding trace
> format remains version 1.

The current broader product uses immutable **Alpha v25**, with **2,080
independently checked theorems** and an unchanged **432-theorem Stable
default**. The historical 247-theorem model-v3 authority is never widened
automatically. For the one active verifier-backed proof-optimization,
discovery, and post-training sequence, see
[`HYDRA_PRODUCT_ROADMAP.md`](HYDRA_PRODUCT_ROADMAP.md) and
[`HYDRA_POST_TRAINING.md`](HYDRA_POST_TRAINING.md).

Peano Lab M9 prepared data and a reproducible evaluation boundary for a later
small tactic model. It did **not** train, download, serve, or call a model. That
separation was intentional at M9; M19 later added an explicitly authorized,
separate post-training experiment without putting a model in the prover's
trusted computing base or browser release.

The intended first experiment is a decoder-only model in the roughly
**100–300 million parameter** range, with a 125M-class model as the baseline.
That is large enough to test whether state-to-tactic regularities transfer
across the theorem ladder, but small enough to fine-tune and inspect on modest
hardware. Larger models can use the same files and protocol; a larger parameter
count does not change what counts as a proof.

## Prediction task and tokenizer contract

One training example asks for the next surface tactic given the current proof
state:

```text
INPUT
⊢ ∀ x. 0 + x = x

TARGET
induction x
```

The version-1 trace stores `goals_before` as a list because a tactic can act in
a multi-goal state. The output is exactly one command in Peano Lab's public
grammar: a primitive such as `intro n`, `rewrite PA4`, or `refl`; a tactical
such as `all_goals simp`; or bounded `auto 5`. There is no model-only action and
no privileged certificate constructor.

Canonical printing is the tokenizer's friend. Alpha-equivalent surface binder
choices, precedence, multiplication spelling, defined `≤`, metavariable
aliases, and whitespace do not acquire several accidental encodings. The data
pipeline must preserve the emitted UTF-8 strings exactly: Unicode `∀`, `∃`,
`→`, `∧`, `∨`, `¬`, `⊥`, `·`, and `⊢` are syntax, not decoration. Do not
ASCII-rewrite them after export and do not apply a second pretty-printer.

For the proposed small-model baseline:

- normalize source files as UTF-8 without ANSI/control sequences, as the trace
  logger already does, but do not apply a later Unicode compatibility fold;
- train or extend a byte-level BPE/SentencePiece tokenizer on training data
  only, with an 8k–16k vocabulary; byte fallback keeps every PA symbol lossless;
- reserve explicit record separators for `goals_before`, individual goals, and
  `tactic`; do not use theorem names as input features in the held-out test;
- measure both surface-command exact match and kernel-judged proof success.
  Exact match is diagnostic only because several tactics can be valid.

A failed trace record remains valuable negative data: it says that a command
was tried and transactionally left the state unchanged. A first supervised
baseline should train next-action targets from `status: "ok"` records and use
`status: "error"` records only in an explicitly documented contrastive or
preference objective. Silently mixing failed commands into positive
next-token targets changes the task.

## Raw corpus contract

The engine emits contiguous JSONL sessions. Each tactic application has the
binding design format:

```json
{"v":1,"session":"...","step":1,"goals_before":["⊢ ∀ x. 0 + x = x"],"focus":0,"tactic":"induction x","goals_after":["⊢ 0 + 0 = 0","x : ℕ, IH : 0 + x = x ⊢ 0 + S x = S x"],"status":"ok","error":null}
```

The immediately following four-field footer closes that session:

```json
{"qed":true,"theorem":"∀ x. 0 + x = x","proof_size":12,"tactic_count":3}
```

The footer theorem is the canonical formula, not a library display name.
Adjacency associates it with the preceding records. Importers must reject
interleaved session IDs, skipped/duplicate step numbers, records after a
footer, malformed fields, a changed state on failure, a footer theorem that
does not equal the target of the one original rendered goal, an initial
context other than free-variable declarations, non-canonical JSON types, and
unterminated sessions. A `qed: true` footer is provenance metadata,
not authority: generation obtains it only after `checked_final`, while later
policy evaluation checks a newly produced certificate again.

`scripts/generate_peano_traces.py` produces two artifacts:

1. the raw v1 JSONL stream above; and
2. a deterministic generation manifest with format
   `peano-lab-trace-generation-manifest`, version 1.

The manifest's top-level keys are `format`, `version`, `generator_version`,
`trace_version`, `run_fingerprint`, `seed`, `config`, `provenance`,
`theorem_ladder`, `counts`, `raw`, and `sessions`. `provenance` fingerprints
the generator and trusted checker individually, hashes the complete
`peano_lab/**/*.py` semantic source tree, and records the Python runtime. Each
session records `session`, `kind`, `family`, `theorem`,
`template`, `variant`, `source`, `target_mode`, `surface_names`, `result`,
`kernel_checked`, `proof_nodes`, `transition_records`, `failure_records`,
`controlled_failures`, and `error`. `target_mode` says
`original_statement`, `dependency_curried_statement`, or
`generated_statement`. Current generation kinds are:

- `ladder_auto`: honest bounded-`auto` attempts over the checked theorem ladder;
- `ladder_script`: replay of authored ladder scripts, independently finalized;
- `variant_renamed`: alpha-renamed instances in the
  `generated_reflexive_arithmetic` family; and
- `variant_commuted`: provable instances in the `add_comm` family; and
- `variant_numeric`: bounded `norm_num` examples in the
  `generated_closed_coefficients` family. Each theorem reduces a closed
  coefficient inside an otherwise open term. Variant
  sessions also include deliberate, transactionally checked failed attempts.

The `run_fingerprint` hashes the complete semantic configuration, theorem
fixtures, generator/checker and full Peano source fingerprints, and Python
runtime. Its prefix is part of every session ID, so raw files from different
configurations or generator versions can be collated without seed-only ID
collisions.

The generation CLI requires `--output`; `--manifest` defaults to
`OUTPUT.manifest.json`. Defaults are seed 0, 1,500 renamed variants, 96 commuted
variants, up to 96 numeric variants (default 96), `auto` depth 5, and 5,000 search nodes. Ladder
auto and script sessions are enabled for the acceptance/smoke corpus. Named raw
and manifest outputs are durably staged and the previous pair is restored on an
ordinary publication failure; the CLI rejects path collisions and non-file
destinations. Generator semantics are version 2 after adding numeric variants;
the binding trace and manifest formats remain version 1. A typical command is:

```bash
python3 scripts/generate_peano_traces.py \
  --output /tmp/peano-raw.jsonl \
  --seed 0 --renamed 1500 --commuted 96 --numeric 96 \
  --auto-depth 5 --auto-max-nodes 5000
```

For release input, explicitly disable both ladder sources:

```bash
python3 scripts/generate_peano_traces.py \
  --output /tmp/peano-release-raw.jsonl \
  --no-ladder-auto --no-ladder-scripts
```

Randomization uses an explicit seed. The manifest, repository commit, Python
version, and command line belong with every released corpus. A raw generated
file is a provenance-bearing **superset**, not automatically a leakage-safe
training split.

## Deduplication and train/validation splits

`scripts/export_traces.py` validates raw sessions, collates them, deduplicates
canonical transitions, and writes deterministic train/validation JSONL plus a
JSON statistics report. Every exported row retains the binding nine-field v1
transition schema and field order (`v` through `error`); it does not invent a
model-specific row format. Footers, theorem formulas, and QED metadata drive
grouping and statistics but are not copied into transition rows. The unit of
splitting is a theorem family identified by its canonical footer formula, so
records from one exact theorem cannot be scattered between train and
validation. A stable seeded SHA-256 rank chooses the split; filesystem
discovery order and Python's randomized `hash()` never do. The semantic
deduplication fingerprint ignores representative-specific `session` and
`step`, keeps one deterministic original row, and prevents the same transition
from appearing in both outputs.

All three outputs are staged before publication. Existing regular files are
backed up during the short replacement window and restored if an ordinary
publish operation fails; directories, filesystem aliases of an input, and
case-folded aliases are rejected before any output changes. `stats.json` is
published last. If restoration itself fails, the exporter preserves and names
the remaining backup rather than deleting the only recoverable old copy.

The statistics report is part of the artifact, not console decoration. It
has top-level keys `v`, `split`, `source`, `exclusions`, `deduplication`,
`theorem_coverage`, `splits`, `outcomes`, and `tactic_distribution`; together
they record input/session/record counts, exclusions, duplicates,
train/validation sizes, theorem coverage, status counts, tactic frequencies,
and the failure ratio. Preserve it beside the split files.

The exporter accepts one or more raw files. Its default validation fraction is
0.1 and its stable split seed is `peano-lab-v1`. With at least two theorem
groups and a nonzero requested fraction, both train and validation receive at
least one group. For example:

```bash
python3 scripts/export_traces.py /tmp/peano-release-raw.jsonl \
  --output-dir /tmp/peano-corpus \
  --val-fraction 0.1 --seed peano-lab-v1
```

`--exclude-theorem 'EXACT CANONICAL FORMULA'` is repeatable and removes whole
sessions before splitting, with counts under `exclusions`. Use it as a second
line of defence when collating mixed raw inputs; family/template exclusions
still belong upstream in the generation-manifest selection because an exact
formula flag cannot recognize every transformed relative.

Splitting by exact footer formula is necessary but not sufficient for a public
generalization claim. Renamed, commuted, or closed-coefficient numeric instances
can be mathematically the same family while having a different formula string.
The released learning corpus therefore omits every session whose manifest kind
is `ladder_auto` or
`ladder_script`, not merely the four test formulas. The remaining synthetic
families must also be checked against the held-out templates below before
export. Confirm that none of their canonical footer formulas occurs in train
or validation. Generating all ladder entries is useful for the M9 pipeline
smoke test; training on that raw superset and calling the following score
"held out" would be leakage.

## Fixed held-out evaluation

The version-4 test families are fixed in `scripts/eval_peano_policy.py`:

| Family | Closed goal |
|---|---|
| `le_trans` | `forall n m k. n <= m -> m <= k -> n <= k` |
| `le_antisymm` | `forall n m. n <= m -> m <= n -> n = m` |
| `le_total` | `forall n m. n <= m \/ m <= n` |
| `mul_eq_zero` | `forall n m. n * m = 0 -> n = 0 \/ m = 0` |

These four literal statements define evaluation protocol v4; the evaluator
checks their parsed formulas against the library at import time rather than
silently inheriting later library edits. Their canonical goal-set fingerprint
is `7099c0a4df7e6f9a8a011124207967c5676871819a42e78e2787c62cd3bc4194`
and appears in every report. They are outside the generator's
renamed-reflexive, commuted-addition, and closed-coefficient template families;
they also cannot be closed by the known cold-`auto` smoke set. Freeze the list,
grammar,
pretty-printer, kernel, logic mode, `k`, step budget, and seed before comparing
policies. Any change creates a new protocol version.

For each family and each sample index `0 .. k-1`, the harness:

1. parses the closed original goal and retains it outside the policy;
2. derives a local RNG seed by SHA-256 from the protocol version, root seed,
   canonical visible goal, and sample index (never the hidden family label or
   logic mode);
3. starts a fresh immutable `ProofState`;
4. renders only its canonical `goals_before` tuple—with metavariable aliases
   retained for the whole rollout exactly as in trace sessions—and asks the
   policy for one tactic line at a time, up to `max_steps`;
5. runs that line through the production interactive grammar; and
6. if the engine closes all holes, calls
   `checked_final(state, original_target, classical=exact_mode)`.

Only step 6 can produce status `proof`. The other terminal statuses remain
separate:

- `invalid`: non-text/multiline model output, a typed `TacticSyntaxError` from
  the surface grammar, an adapter exception, or a closed engine certificate
  rejected by the independent kernel;
- `failing`: a well-formed proposed line raises an ordinary final `TacticError`
  and leaves the state unchanged;
- `limit`: the policy stops, any tactic raises structured `TacticLimit`, or the
  rollout reaches the step budget. This includes bounded `auto` or `simp`, and
  `auto` nested inside a tactical such as `first [auto 1]` or `repeat auto 1`;
  tacticals may not reinterpret an exhausted resource budget as an ordinary
  recoverable failure.

The harness terminates a sample after a failing tactic. Thus a sample is one
candidate proof interaction, not an unbounded conversation that can erase bad
choices. Policies may propose only real Peano Lab surface text; `qed`, mode
changes, certificate objects, theorem claims, and mutations of the original
target are not policy actions. The `Policy.propose` input is only
`tuple[str, ...]` canonical goals plus the zero-based sample/step and a local
RNG. It deliberately withholds `ProofState`, theorem/library name, original
source spelling, certificate holes, and logic-mode authority.

The Python protocol is an adapter contract, not a hostile-code sandbox. A
compliant model adapter uses only those arguments; arbitrary in-process Python
could inspect frames or globals and must not be treated as a scientifically
blind policy. Put untrusted or contest submissions behind a process boundary.

For exactly `k` rollouts per family, empirical **pass@k** is the fraction of
families with at least one `proof` attempt. The report also includes all four
attempt-status counts, commands, deterministic per-attempt seeds, the
canonical goal-set SHA-256, and proof node counts. Report the whole JSON, not
only the headline float. If a later
experiment samples `n > k` candidates and estimates pass@k combinatorially,
label that estimator separately; it is not the version-4 metric.

Run the in-repository random baseline end to end with:

```bash
python3 scripts/eval_peano_policy.py --k 8 --max-steps 16 --seed 20260727
```

`RandomPolicy` samples from a fixed list of actual primitive tactics and
tacticals. Its menu deliberately excludes `auto`: a random plumbing baseline
must not delegate to the strong built-in search procedure. It is not a
meaningful theorem-proving baseline. Identical inputs produce byte-identical
JSON. The evaluator's checked scripted regressions separately pin the arithmetic
surface: `norm_num` proves closed arithmetic and reduces closed coefficients in
open terms (using a coefficient shape deliberately outside the generated numeric grid), while a genuinely polynomial identity fails under `norm_num` and
succeeds under `ring`. M13 first bumped the evaluator protocol to version 2 because
`norm_num` expanded the production grammar. M19's capability-scoped authority and complete
evaluator source/runtime identity subsequently create the current version 4, even though the
deliberately weak `random-tactic-v1` menu itself is unchanged. To integrate a future local model,
implement the importable
`Policy.propose(goals_before, *, sample, step, rng)` interface and call
`evaluate(policy, goals, k=..., max_steps=..., seed=...)`; the judge and report
stay unchanged.

## Threats, leakage, and reporting checklist

The kernel prevents a false certificate from scoring, but it cannot make an
evaluation scientifically valid. Check all of the following:

- **Exact and structural leakage:** remove held-out authored scripts, `auto`
  traces, renamed binders, commuted equations, or generated numeric variants
  derived from or structurally overlapping a held-out family; also remove
  dependencies whose transcript contains the same target and hand-written examples copied into
  prompts.
- **Deduplication scope:** identical transitions are removed, but near
  duplicates and logically equivalent formulas require family provenance from
  the manifest, not string hashing alone.
- **Tokenizer leakage:** learn vocabulary/merges on training only. A fixed
  byte fallback is fine; fitting subwords on held-out formulas is not.
- **Search-budget leakage:** do not tune seed, `k`, temperature, step count,
  `auto` depth, or tactic menu after inspecting held-out outcomes.
- **Mode leakage:** intuitionistic and classical attempts are different tasks.
  The exact Boolean mode is fixed by the benchmark and passed independently to
  final checking.
- **Kernel/version drift:** record the Git commit. A printer, parser, tactic,
  axiom, or checker change invalidates direct comparison even when the report
  schema number itself is unchanged.
- **Sampling independence:** seed each family/sample independently as the
  harness does. Batch order, worker count, and an earlier model failure must not
  perturb later samples.
- **Metric selection:** publish per-family attempts and status counts. A high
  command exact-match score can still yield no proof; a proof reached through a
  different valid command is still a proof.

Finally, retain the foundational distinction: policies and automation are
untrusted search. Corpus footers, model confidence, theorem names, and tactic
success are never substitutes for checking a complete certificate against the
original stated goal.
