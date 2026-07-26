# Peano Lab — a little Lean for Peano arithmetic

A lightweight, readable, **sound** theorem prover for PA, in the browser, built to teach how
kernels, tactics, and tactic languages are made. Sibling of the [Lambda Lab](../lab-lambda/)
and sharing its shell (xterm + Pyodide worker, fully self-hosted).

**Start here, in this order:**

1. `docs/PEANO_LAB_DESIGN.md` — the architecture. It is binding.
2. `PLAN/09_peano_lab.md` — milestones M0–M9 with tasks and acceptance criteria.
3. `py/peano_lab/` — docstring stubs pinning the module APIs.

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
```

The first command opens a tactic card whose worked script is replayed in CI;
the last starts an ENTER-driven lesson that cannot complete until its generated
certificate passes the same independent QED path.

Back at the repository root, run both regression suites:

```console
(cd peano-lab/py && python3 -m pytest tests/ -q)
(cd lab-lambda/py && python3 -m pytest tests/ -q)
```
