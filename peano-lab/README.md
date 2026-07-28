# Peano Lab — a little Lean for Peano arithmetic

A lightweight, readable, **sound** theorem prover for PA, in the browser, built to teach how
kernels, tactics, and tactic languages are made. Sibling of the [Lambda Lab](../lab-lambda/)
and sharing its shell (xterm + Pyodide worker, fully self-hosted).

**Start here, in this order:**

1. [`../docs/PEANO_LAB_DESIGN.md`](../docs/PEANO_LAB_DESIGN.md) — the architecture. It is binding.
2. [`../PLAN/09_peano_lab.md`](../PLAN/09_peano_lab.md) — milestones M0–M18 with tasks and
   acceptance criteria.
3. [`py/peano_lab/`](py/peano_lab/) — the readable implementation behind the pinned APIs.

**The three laws** (from the 2026-07-24 lambda-lab audit, paid for in full):

1. Every QED passes the independent kernel checker against the *original* goal.
2. A failing tactic raises `TacticError` and leaves the state unchanged.
3. The kernel imports nothing from the engine or UI — and stays small enough to read in one
   sitting.

Reference implementations to copy patterns from (same repo):
`lab-lambda/py/lambda_lab/lab/webport/{stlc_types,proof_builder,prove}.py` and
`lab-lambda/py/driver.py`.

## Run locally

From the repository root, fetch the version-pinned browser runtime once, stage
the content-addressed release, and serve that exact static assembly:

```console
bash scripts/fetch_vendor.sh
make peano-serve
```

Then open <http://127.0.0.1:8002/> and try:

```text
pa prove forall n m. n + m = m + n
auto 5
qed
```

The final line independently checks the generated certificate against the
original formula. The browser driver limits numeral literals to `0..256` so a
short decimal input cannot expand into an unbounded successor tree; this is a
UI resource bound, not a restriction on the PA object language.

## Browser startup and caching

The prover is small, but its CPython/Pyodide runtime is not: the pinned cold-start payload includes
an 8.6 MB WebAssembly file and a 2.4 MB standard-library archive. M14 keeps the privacy and deployment
control of self-hosting while avoiding repeated network transfer for a cached version:

- the vendor URL contains a digest of the canonical source manifest and is cached immutably;
- `worker.js` and every application source live below a separate application-manifest release path;
- `index.html` itself is never stored, so a new `BUILD` is discovered immediately;
- Apache serves compressible WASM/source responses with Brotli or gzip, but leaves ZIP and WOFF2
  alone; and
- all Python sources transfer concurrently while Pyodide initializes, then mount in a fixed order.

These are delivery optimizations, not shortcuts in checking. All execution still occurs in the
disposable Web Worker, and every QED still reaches the same independent kernel. A Stop/restart may
repeat runtime initialization, browser caches may evict data, and guaranteed offline use would need
a future precache/service-worker design. Versioned bytes should normally avoid another transfer.
Every promoted application/page release must use a new human-facing `BUILD` value; worker or served
Python changes must also produce a new application-manifest release path.
Deployment retains old immutable directories, uploads the complete new release first, and publishes
the non-stored HTML pointer last, so an open older page cannot be stranded mid-promotion.

The teaching surfaces are executable too:

```text
pa tactic induction
pa tactic norm_num
kb de-bruijn-criterion
pa tutorial add_comm
pa tutorial norm_num
pa lib mul_eq_zero
pa lib mod5_fourth_power_one
pa lean add_comm
```

Checked library facts can also be composed inside an ordinary live proof:

```text
pa prove forall a b. S a + b = S (b + a)
use add_succ_left
use add_comm
intro a
intro b
simp [add_succ_left, add_comm]
qed
```

`use` does not ask the kernel to trust a theorem name. It embeds the theorem's closed certificate
in a self-contained `Cut` carrying both formulas and both proof branches. Finalization submits that
closed shared certificate to the kernel against the original stated goal.

The upstream public-catalog candidate contains 49 dependency-ordered entries: the 23-entry core and
a 26-entry extension through `mod5_fourth_power_one`. Its immutable source report records the former
fully expanded capstone at 21,515 nodes/depth 66. The current self-contained shared certificate is
2,675 nodes/depth 38 and remains below the 32,768-node/depth-128 import ceiling. A short reuse of
the capstone is:

```text
pa prove forall n. ~(exists x. n = 5 * x) -> exists x. n * n * n * n = 5 * x + 1
intro n
intro h
use mod5_fourth_power_one
apply mod5_fourth_power_one
exact h
qed
```

## Local reasoning with `have` and `suffices`

Two commands let a longer proof name an intermediate proposition. Their exact syntax is
`have h : P` and `suffices h : P`; the colon and a fresh hypothesis name are required. The
proposition may mention rigid arithmetic variables already visible in the focused goal, but it
cannot silently introduce a new free variable.

`have` asks for the intermediate fact first and then returns to the old target with that fact in
the context:

```text
pa prove 0 = 0
have h : 0 = 0
refl
exact h
qed
```

Immediately after `have h : P`, the ordered goals are

```text
Goal 1:  Γ ⊢ P
Goal 2:  h : P, Γ ⊢ previous focused target
```

`suffices` reverses that working order. It first asks how `P` would finish the old goal, and only
then asks for `P` itself:

```text
pa prove 0 = 0
suffices h : 0 = 0
exact h
refl
qed
```

Its ordered goals are

```text
Goal 1:  h : P, Γ ⊢ previous focused target
Goal 2:  Γ ⊢ P
```

The two commands have the same logical meaning; only their teaching order differs. The partial
certificate records that order with engine-only `LocalHave` or `LocalSuffices` nodes. Before QED,
an untrusted capture-avoiding compiler substitutes the proof of `P` for the local hypothesis and
removes every such node. The kernel never accepts either administrative constructor; the compiled
result may contain ordinary constructors and separately introduced self-contained Cuts. It still
checks the certificate from scratch against the **original stated
goal**, not against either intermediate goal. Local names therefore improve proof organization but
grant no theorem authority or proof sharing: if a compiled body uses `h` repeatedly, the proof of
`P` may be copied repeatedly into the final proof tree.

The complete checked consecutive-product parity example uses both commands and is ready to paste
into the browser: [`../artifacts/triangular-even-readable.pa`](../artifacts/triangular-even-readable.pa).

## Inspecting and keeping a proof

During a proof, `script` displays the replay program for the current undo branch. After a successful
QED, the same command displays the last retained checked replay:

```text
script
script download
```

An active artifact is labeled `ACTIVE (not kernel-checked)` and never contains `qed`, even after all
goals close. Only the independent checker can produce `CHECKED QED` and append the final canonical
`qed` line. Failed tactics, failed QED attempts, inspection commands, and `undo` itself are omitted;
undo removes exactly the proof transaction it restored. Explicit tactical and theorem-import lines
retain their replayable surface syntax, while top-level `auto` is exported as its independently
undoable primitive plan.

`script download` saves the exact unindented, LF-only, newline-terminated UTF-8 body as
`peano-lab-proof.pa`. The download is triggered only by typing that exact command directly, not by a
deep link. A replay file is an untrusted program, not a proof certificate or a library declaration.
Replaying it reconstructs a candidate certificate; only `qed` checks the original theorem.

### Paste a complete proof

M17 adds an explicit accessible **Paste multiline proof** dialog and recognizes direct multiline
paste into the terminal. Both entry points accept the same complete replay format. The first
nonblank line must begin exactly `pa prove `, the last nonblank line must be exactly `qed`, and blank
lines are ignored. For example:

```text
pa prove forall n. n + 0 = n
intro n
rewrite PA3
refl
qed
```

The browser first enforces the whole-input bounds: at most 100,000 characters, at most 256
nonblank lines, and at most the existing `MAX_INPUT` characters on any one line. An invalid or
oversized batch does not begin. Once admitted, its nonblank lines run in order through the ordinary
session driver. Execution stops at the first failed line; every earlier successful command remains,
with its normal per-line undo behavior. The batch is deliberately not an all-or-nothing tactic.
By contrast, **Stop**, Escape, or Control-C terminates and restarts the worker, so that explicit
interruption discards the in-memory proof session.

Pasting is not extra authority. In particular, preflight rejects `script` commands and the batch
executor cannot start a browser download, even if a worker response carries download bytes. The
final pasted `qed` still invokes the independent checker against the session owner's original
theorem. The text remains an untrusted replay program, not a proof certificate or a route into the
theorem library. M17 is locally verified as build `2026-07-28b`, application release
`a-404fdbdb55e4`, and is available on `/peano-lab-next/`. Production promotion remains blocked
because the host does not yet emit the required cache headers.

The static browser cannot write to Git or admit a theorem to `library/theorems.py`. Library
admission remains a reviewed source change: bind every free variable, declare earlier checked
dependencies, lower the body to the library's supported script language, replay it, independently
check the closed certificate, add tests, and commit. A downloaded live script—especially one using
`use`, tacticals, `auto`, `ring`, or classical mode—is a handoff artifact, not a paste-ready
`TheoremSpec`.

`pa tactic induction` opens a tactic card whose worked script is replayed in CI;
the tutorial command starts an ENTER-driven lesson that cannot complete until its generated
certificate passes the same independent QED path.

## Basic arithmetic with checked certificates

`norm_num` normalizes maximal closed numerical islands in an equality, optionally beneath leading
universal binders, in deterministic left-to-right order. Python computation chooses a canonical numeral, but ordinary PA3--PA6 and
congruence proof terms justify every result. A closed equation is accepted only when the generated
certificate checks; an open equality may instead be reduced to one transported residual goal. QED
still checks the complete certificate against the original theorem.

```text
pa prove (2 * 3 = 6) /\ (forall n. n + (2 * 3) = n + 6)
split
hint
norm_num
intro n
hint
norm_num
qed
```

The tactic takes no arguments and never treats local hypotheses as arithmetic rewrite rules. A
single call allows at most 256 equality-term AST nodes at depth 64, at most 64 leading universal
binders, 32 closed computations, intermediate values up to 128, 25,000 work units, a
50,000-node/256-level generated numerical bridge, and five seconds. The complete live partial proof
is separately capped at 100,000 nodes and depth 256. False closed equations, unsupported goals,
non-closing no-progress calls, and every limit fail transactionally; reflexive equality can close
without performing a numerical computation.

The arithmetic toolbox keeps four separate jobs visible: `simp` performs ordered rewriting;
`norm_num` certifies concrete arithmetic; `ring` proves unconditional polynomial identities; and
`auto` explores a bounded tactic tree. Neither normalizer decides general PA or solves nonlinear
consequences of hypotheses. A certificate-producing Presburger `omega` belongs to a later plan and
is not hidden in these tactics.

The M7 theorem-library core contains twenty named, scripted entries: the fifteen binding
arithmetic/order rungs plus five explicit helper lemmas, ending at
`forall n m. n * m = 0 -> n = 0 \/ m = 0`. M11 extends the current index to twenty-three with
`one_mul`, `mul_one`, and `add_mul`, the only missing orientations needed by certificate-producing
commutative-semiring normalization. The current local runtime extends that
reconciled foundation to 149 unique checked entries: 23 baseline theorems, 114
general foundational theorems, and twelve unique modular capstones. The
complete 26-record modular provenance catalog ends at
`mod5_fourth_power_one`; fourteen of those records coincide exactly with
foundational entries and are exposed once.
Dependencies are introduced as ordinary hypotheses, then packaged in nested self-contained Cuts.
Each Cut embeds and checks its dependency proof once; it carries no theorem name or hash. The
resulting closed certificate is independently checked from the empty context against the original theorem. `pa lib <name>` shows that exact
replay script; `pa lean <name>` exports the exact statement as a Lean 4 theorem over `Nat`, with one
intentional proof stub and a Live Lean link for cross-checking.

The constructive prime-search layer contributes twelve checked rungs:
`eq_decidable`, `multiple_decidable_nonzero`, `multiple_decidable`,
`factor_property_succ`, `factor_search_up_to`, `prime_or_composite`,
`prime_nonzero`, `prime_decidable`, `factor_nonzero_left`, `proper_factor_lt`,
`prime_divisor_exists_up_to`, and `prime_divisor_exists`. Thus equality and
divisibility decisions, bounded factor search, primality decision, proper-factor
descent, and prime-divisor existence are native expanded PA theorems rather
than hidden predicates or axioms. The shared ladder totals 67,844 structural
nodes and 1,800 Cuts across 109 Cut-bearing entries. Euclid remains largest at
5,382 nodes and has the maximum 159 Cuts; `prime_divisor_exists` reaches the
maximum depth of 80.

## Polynomial identities with checked certificates

`ring` proves equalities in the commutative semiring generated by `0`, successor, `+`, `·`,
numerals, and the visible natural-number variables. It computes a sparse normal form only to choose
a certificate assembled from PA3--PA6 and the independently checked M11 laws. The generated
certificate is checked before the tactic closes its goal, and QED checks the original theorem
again.

Here is the complete odd-square induction proof. The explicit middle term separates the polynomial
identity from the use of the induction hypothesis:

```text
pa prove forall n. exists x. (2 * n + 1) * (2 * n + 1) = 8 * x + 1
induction n
exists 0
ring
cases IH
exists x + S n
trans ((2 * n + 1) * (2 * n + 1)) + (8 * S n)
ring
rewrite IH_witness
ring
qed
```

`ring` takes no arguments and does not silently use local hypotheses. Use ordinary `trans` and
`rewrite` to turn conditional algebra into identity goals, as above. It rejects non-equalities and
unresolved witness metavariables, and its AST, variable, degree, monomial, coefficient, work,
certificate-size, and wall-clock limits fail transactionally. The wall-clock default is five
seconds: the required large step used about 1.4 seconds under native CPython, while a real Pyodide
measurement remains part of deployment verification.

## Smaller PA-oriented equality certificates

`compact_arith` has a narrower contract than `ring`: it searches a finite, memoized grammar of
PA3--PA6-oriented equality paths and seeded induction-recurrence templates, preferring the smallest
expanded proof tree it finds. Its exact forms are:

```text
compact_arith
compact_arith [h, <- k]
```

The bracketed form makes exactly the named equality hypotheses available, in the written order and
direction; the winning candidate may use a subset. There is no implicit context mining. Version 1
accepts only a focused rigid equality with no
unresolved term metavariables. It does not introduce a binder, invent an induction invariant or an
existential witness, solve a logical connective, or act as a decision procedure for PA.

That restriction keeps the mathematics visible in the consecutive-product example. The learner
states the stronger invariant, chooses both witnesses, and explicitly permits the induction
hypothesis; compact arithmetic handles only the resulting equalities:

```text
pa prove forall n. exists x. n * (n + 1) = 2 * x
have strong : forall n. exists x. n * n + n = 2 * x
induction n
exists 0
compact_arith
cases IH
exists x + S n
compact_arith [IH_witness]
intro n
specialize strong n
suffices normalize : n * (n + 1) = n * n + n
rewrite normalize
exact strong
compact_arith
qed
```

After local-cut compilation this thirteen-tactic replay produces the same 180-node, depth-34
canonical certificate as the retained hand-authored artifact.

There is no trusted `compact_arith` proof constructor. Seeded recurrence instances are ordinary
induction certificates built from existing kernel rules and checked with an empty proof context
before final use; the fully quantified addition-successor template is checked once before any
specialization. The selected
cut-normal candidate is measured at its expanded tree cost, independently checked against the exact
focused context and target before commit, and checked again as part of the complete original theorem
at QED. A planner or cost bug cannot produce a false QED; explicit-input, determinism, resource,
and cost-reporting contracts remain independently tested engine obligations.

The motivating generic readable replay elaborates to 30,030 structural proof-tree nodes, mostly in
its two `ring` calls. A separate hand-authored construction demonstrates a checked 180-node,
depth-34 certificate; see
[`../artifacts/triangular-even-180.certificate.txt`](../artifacts/triangular-even-180.certificate.txt)
and the full [book chapter](../book/peano/compact-arith.md).
That 180 is a best-known checked upper bound, not a proven global minimum. The current metric counts
expanded `Proof` occurrences but not term or induction-motive size, and DAG sharing would be a
different representation and cost model. `compact_arith` may report the cheapest candidate in its
fixed bounded grammar; it cannot turn bounded search into an absolute minimality theorem.

`compact_arith?` is a pure preview of the selected path, equations actually used, expanded nodes,
depth, annotation nodes, and work. It changes no
goal, history, hole, metavariable allocation, replay journal, or trace. Running the real tactic still
reconstructs and checks the candidate. Unsupported input and every AST, hypothesis, annotation,
work, time, proof-size, proof-depth, or complete-partial-proof limit fail transactionally.

The default bounds are 256 aggregate input-term nodes at depth 64, 16 selected equations, 64
seed/template instances, 512 memo/search states, 512 generated candidates, 100,000 annotation nodes at
depth 256, 20,000 work units, a 10,000-node/256-level generated fragment, a 100,000-node/256-level
complete partial certificate, and five seconds.

M18 is verified as build `2026-07-28c`, application release `a-953fa3777cd4`: the focused
suite reports 46 passes and the complete Peano suite 744. Exact local staging, manifests, worker and
multiline-paste harnesses are green. The same commit `98ee0dd` is deployed at
`/peano-lab-next/`; its HTML and all 41 application files match the staged checksums. No in-app
browser was attached, so a live Pyodide click-through is not claimed. Production remains build
`2026-07-27h` behind the administrator-managed cache-header blocker.

The locally staged M19 candidate is build `2026-07-28f`, immutable application release
`a-69aa3b753965`. Its compact runner, transport, dataset, training-runtime, evaluator, and Helios
controls are covered by a 363-test focused set; the complete Peano suite reports 912 passes. The
existing Lambda Lab suite reports 360 tests plus 36 subtests, and the Jupyter Book plus documented
command replay gates are green. This candidate has not been deployed or promoted, and no learned
model result is claimed.

The M20 foundational-arithmetic candidate is build `2026-07-28h`, immutable
application release `a-265ffb1c28af`. It expands the checked browser library
from 23 to 51 theorems without changing the kernel or adding a trusted
predicate. The 28 M20 additions include `prime_two`, the first checked
instance of the fully expanded prime predicate. Its source snapshot and dependency metrics live under
`../artifacts/peano-library/`; this candidate has not been deployed or
promoted.

The public-catalog integration candidate is build `2026-07-28g`, immutable application release
`a-3ea7b7142aa0`. Its complete Peano suite reports 1,036 passes; Lambda remains green at 360 tests
plus 36 subtests; all 27 book sources build with warnings as errors; and 193 deep links plus 170
session commands replay. Automated worker boot is green. A direct in-app Pyodide latency smoke is
still pending because no browser was attached to this session. This candidate is staged locally
only; production is untouched.

The last fully synchronized local browser candidate is build `2026-07-28p`, immutable application
release `a-48059fcca9d3`. It exposes 137 unique checked theorems, including
constructive relational gcd existence, balanced-natural Bézout, Gauss
cancellation, and Euclid's lemma, together with the reviewed self-contained
Cut rule. It preserves both parent snapshots as provenance and binds a freshly
regenerated proof-trace corpus and application manifest. Its complete suite
passes 1,090 tests on Python 3.10; the 36-source warning-as-error book and all
264 documented commands are green. It has not been deployed or promoted;
production remains untouched.

The current fully synchronized local browser candidate is build `2026-07-29a`,
immutable application release `a-d0758315633d`. It exposes all 149 checked
theorems, including constructive equality and divisibility decisions,
prime/composite decision, primality decision, proper-factor descent, and
prime-divisor existence. Its complete Peano suite passes 1,094 tests on
CPython 3.10; Lambda's 360 tests plus 36 subtests, the warning-as-error
36-source book, 201 checked deep links, 45 session blocks with 264 commands,
and application-manifest drift are green. It has not been staged, deployed, or
promoted; production remains untouched.

Back at the repository root, run both regression suites:

```console
(cd peano-lab/py && python3 -m pytest tests/ -q)
(cd lab-lambda/py && python3 -m pytest tests/ -q)
```

## Proof-trace corpus and kernel-judged evaluation

The compact M19 runner uses the production parser, public tactic grammar, proof engine, theorem
library, and independent final kernel without loading Pyodide or the browser UI. Feed it one finite
strict-JSONL batch to keep a warm Python process alive across many independent proofs:

```console
python3 scripts/peano_batch.py --environment model-v1 \
  --trace-output /tmp/peano-run.trace.jsonl \
  < requests.jsonl > results.jsonl
```

Each request contains `v`, `id`, one closed `theorem`, and an array of complete `tactics`; optional
`classical` and `on_error` fields are runner-validated. Generation mode always writes the binding
version-1 trace and reports `proved` only after original-target kernel checking. `--verify-only` is
the faster, trace-free regression path and is deliberately ineligible as training data. Results
are withheld until EOF (and trace commit), so this is not a duplex service. Aggregate defaults cap
the batch at 10,000 requests, 256 MiB input, 128 MiB results, and 512 MiB trace; shard larger work.
The hard link is the trace commit point; after it, cancellation can leave a complete trace even if
redirected stdout is incomplete, so use a caller-owned temporary result file when both names must
publish atomically.
Exit zero means the protocol completed; add `--require-proved` when CI must reject any open or
failed proof. See the
[M19 training protocol](../docs/PEANO_TRAINING.md) for the exact request, prompt, capability,
provenance, and replay contracts.

The deterministic M9/M15 data pipeline also ships a committed 13,344-transition provenance refresh and an
evaluation harness. Its 1,692 checked sessions include a bounded numerical
normalization tranche while omitting all theorem-ladder sessions, so the four fixed tail theorems
used by the evaluator stay held out. Exact version-1 records, hashes, provenance, and the
reproduction command are documented in [`corpus/README.md`](corpus/README.md); the model and
historical leakage protocol is [`docs/PEANO_LLM.md`](../docs/PEANO_LLM.md).

From the repository root:

```console
make peano-corpus        # reproduce train.jsonl, val.jsonl, stats, and manifest
make peano-corpus-smoke  # all-ladder auto/script acceptance superset, under /tmp
make peano-policy-pilot  # 18 checked sessions -> replay-validated M19 policy rows
make peano-policy-data   # 10k proof-first rows -> splits + independent attestation
make peano-eval          # deterministic random-policy plumbing baseline
```

The exported rows are tactic transitions, not proof certificates. Generation labels a successful
session only after `checked_final` validates its certificate against the original theorem, and the
evaluation harness independently repeats that check for every candidate counted as a proof.
