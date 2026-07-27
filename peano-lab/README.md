# Peano Lab — a little Lean for Peano arithmetic

A lightweight, readable, **sound** theorem prover for PA, in the browser, built to teach how
kernels, tactics, and tactic languages are made. Sibling of the [Lambda Lab](../lab-lambda/)
and sharing its shell (xterm + Pyodide worker, fully self-hosted).

**Start here, in this order:**

1. [`../docs/PEANO_LAB_DESIGN.md`](../docs/PEANO_LAB_DESIGN.md) — the architecture. It is binding.
2. [`../PLAN/09_peano_lab.md`](../PLAN/09_peano_lab.md) — milestones M0–M14 with tasks and
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

`use` does not ask the kernel to trust a theorem name. It inserts the theorem's closed certificate
as a local cut; surface finalization contracts that cut and independently checks the resulting
closed proof against the original stated goal.

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
is separately capped at 100,000 nodes and depth 512. False closed equations, unsupported goals,
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
commutative-semiring normalization. Dependencies are introduced as ordinary hypotheses,
then compiled away by untrusted, capture-avoiding proof-term cut elimination. The resulting closed
certificate is independently checked against the original theorem. `pa lib <name>` shows that exact
replay script; `pa lean <name>` exports the exact statement as a Lean 4 theorem over `Nat`, with one
intentional proof stub and a Live Lean link for cross-checking.

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

Back at the repository root, run both regression suites:

```console
(cd peano-lab/py && python3 -m pytest tests/ -q)
(cd lab-lambda/py && python3 -m pytest tests/ -q)
```

## Proof-trace corpus and kernel-judged evaluation

The deterministic data pipeline now ships a committed 13,344-transition M15 provenance refresh and an
evaluation harness—not a trained model. Its 1,692 checked sessions include a bounded numerical
normalization tranche while omitting all theorem-ladder sessions, so the four fixed tail theorems
used by the evaluator stay held out. Exact version-1 records, hashes, provenance, and the
reproduction command are documented in [`corpus/README.md`](corpus/README.md); the model and
leakage protocol is [`docs/PEANO_LLM.md`](../docs/PEANO_LLM.md).

From the repository root:

```console
make peano-corpus        # reproduce train.jsonl, val.jsonl, stats, and manifest
make peano-corpus-smoke  # all-ladder auto/script acceptance superset, under /tmp
make peano-eval          # deterministic random-policy plumbing baseline
```

The exported rows are tactic transitions, not proof certificates. Generation labels a successful
session only after `checked_final` validates its certificate against the original theorem, and the
evaluation harness independently repeats that check for every candidate counted as a proof.
