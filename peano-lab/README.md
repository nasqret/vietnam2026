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
