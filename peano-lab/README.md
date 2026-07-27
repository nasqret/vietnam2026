# Peano Lab — a little Lean for Peano arithmetic

A lightweight, readable, **sound** theorem prover for PA, in the browser, built to teach how
kernels, tactics, and tactic languages are made. Sibling of the [Lambda Lab](../lab-lambda/)
and sharing its shell (xterm + Pyodide worker, fully self-hosted).

**Start here, in this order:**

1. [`../docs/PEANO_LAB_DESIGN.md`](../docs/PEANO_LAB_DESIGN.md) — the architecture. It is binding.
2. [`../PLAN/09_peano_lab.md`](../PLAN/09_peano_lab.md) — milestones M0–M9 with tasks and acceptance criteria.
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

From the repository root, fetch the version-pinned browser runtime once and
serve the static lab:

```console
bash scripts/fetch_vendor.sh
cd peano-lab
python3 -m http.server 8002
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

The teaching surfaces are executable too:

```text
pa tactic induction
kb de-bruijn-criterion
pa tutorial add_comm
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

`pa tactic induction` opens a tactic card whose worked script is replayed in CI;
the tutorial command starts an ENTER-driven lesson that cannot complete until its generated
certificate passes the same independent QED path.

The M7 theorem-library core contains twenty named, scripted entries: the fifteen binding
arithmetic/order rungs plus five explicit helper lemmas, ending at
`forall n m. n * m = 0 -> n = 0 \/ m = 0`. M11 extends the current index to twenty-three with
`one_mul`, `mul_one`, and `add_mul`, the only missing orientations needed by certificate-producing
commutative-semiring normalization. Dependencies are introduced as ordinary hypotheses,
then compiled away by untrusted, capture-avoiding proof-term cut elimination. The resulting closed
certificate is independently checked against the original theorem. `pa lib <name>` shows that exact
replay script; `pa lean <name>` exports the exact statement as a Lean 4 theorem over `Nat`, with one
intentional proof stub and a Live Lean link for cross-checking.

Back at the repository root, run both regression suites:

```console
(cd peano-lab/py && python3 -m pytest tests/ -q)
(cd lab-lambda/py && python3 -m pytest tests/ -q)
```

## Proof-trace corpus and kernel-judged evaluation

M9 ships a deterministic data pipeline, a committed 13,152-transition release, and an evaluation
harness—not a trained model. The release omits all theorem-ladder sessions, so the four fixed tail
theorems used by the evaluator stay held out. Exact version-1 records, hashes, provenance, and the
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
