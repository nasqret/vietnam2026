# An Introduction to Automatic Theorem Proving in Mathematics

> A six-lecture VIASM mini-course taking you from the **λ-calculus and type theory** through
> **Lean** all the way to the **auto-formalization of research mathematics** — building the
> foundations first, then climbing.

**Course page (VIASM):** <https://viasm.edu.vn/en/hdkh/Mini-Course_AIATPM>
**Landing page (notes hub):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026>
**Live Lambda Lab (runs in your browser):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda>
**Live Peano Lab (kernel-checked PA proofs):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/>
**Author:** dr Bartosz Naskręcki — Faculty of Mathematics and Computer Science, Adam Mickiewicz University in Poznań · Centre for Trustworthy AI (CCAI), Warsaw University of Technology

---

## The six lectures

| # | Title | One line |
|---|-------|----------|
| 1 | **A general introduction to type theory** | Judgments, simply-typed λ-calculus, Church vs Curry, and why proof assistants stand on type theory rather than set theory. |
| 2 | **Simple calculations with the Church (λ-)calculus** | Untyped λ-calculus, β/η-reduction, Church booleans & numerals, the predecessor, and the Y-combinator — every β-step reproducible in the Lambda Lab. |
| 3 | **Propositional logic proofs** | Natural deduction and the BHK / Curry–Howard reading of the connectives, taught through Emily Riehl's *A Reintroduction to Proofs* Lean game. |
| 4 | **Introduction to Lean** | Term vs tactic mode, `Nat` and induction, the Natural Number Game and Macbeth's *Mechanics of Proof* — a first honest end-to-end proof. |
| 5 | **Advanced Lean** | Dependent types in practice, typeclasses, `simp`/`ring`/`linarith`/`omega`, `calc`, Mathlib search, and a real analysis/algebra proof. |
| 6 | **Auto-formalization of mathematics with Lean** | The 2024–2026 AI-for-proof landscape and the **EML project** (`arXiv:2603.21852`) as a worked human + AI + kernel case study. |

The exact abstracts, session plans and reading lists live on the [landing page](book/) and in the
[knowledge book](book/); this README is the map.

---

## What is in this repository

| Path | What it is |
|------|------------|
| `index.html` | The **landing page** — hero, the six-lecture plan, descriptions, and cross-links. Deployed to `/vietnam2026`. |
| `book/` | The **knowledge book** — a [JupyterBook](https://jupyterbook.org/) with the full text-friendly notes: mathematics, code, and links. This is the "learning data". |
| `slides/` | **Presentations** — one reveal.js deck per lecture, to follow along live. |
| `vault/` | The **Obsidian vault** — the atomic, wiki-linked knowledge base behind the book. |
| `artifacts/` | **Formal proofs** in four systems, plus `lean-fta/`: a pinned, sorry-free Lean proof of prime-factorization existence and uniqueness up to permutation. |
| `lab-lambda/` | The **Lambda Lab**, repackaged to run **directly in the browser** (Pyodide + xterm.js). Deployed to `/lab-lambda`. |
| `peano-lab/` | The **Peano Lab** browser prover, its independent PA kernel, 189-entry checked arithmetic ladder, and reproducible proof-trace corpus. |
| `research/` | The **research dossier** — including the 196-node foundational arithmetic catalog (23 baseline checked, 166 post-baseline checked, three planned expressible, four language-blocked), one checked FTA companion, and source/license maps. |
| `scripts/` | Book replay gate plus the deterministic Peano trace generation, export, and kernel-judged evaluation pipeline. |
| `docs/` | Lecturer-facing docs: how to build, deploy, and run each piece. |
| `MEMORY.md` · `JOURNAL.md` · `PLAN.md` + `PLAN/` | Project **memory**, dated **journal**, and the multi-level **plan**. |

The 189-entry native ladder now checks full addition/multiplication
compatibility for balanced congruence and proves that expanded Gödel-β
decoding is equivalent to a bound plus balanced congruence. Constructive binary
CRT and a two-position β-code constructor are checked. A new conditional chain
proves the β moduli coprime when the ordered index gap divides `c`,
discharges the constructor's premise, and constructs a nonzero `c`
divisible by every positive gap through a fixed bound. Unconditional pairwise
coprimality is false: `c=1` at indices 1 and 4 gives moduli 3 and 6.
The bounded-prefix glue is now checked: it constructs a suitable base with
pairwise-coprime β moduli through a chosen bound. Coprime-product closure,
modulus descent, and an ordinary-induction CRT prefix invariant are checked
too. The public wrapper applies only to residues already decoded from an
existing `BetaAt` code; it is not an arbitrary finite-sequence coding theorem.
Genuine prefix-product recurrence and bounds, β finite-prefix recoding,
greatest-prime descent, and native FTA remain open.
The shared snapshot totals 242,629 structural proof nodes and 6,895 Cuts
across 149 Cut-bearing entries; `bounded_beta_crt_for_existing_code` is largest
at 25,545 nodes and 755 Cuts.
The synchronized source-bound corpus has fingerprint
`a3c2f8c5c762b10fc9c1117723c74fecb50348cfb699f73bc76fb3714df3bf1b`;
its all-ladder smoke closes all 189 authored proofs. Local browser build
`2026-07-29h` packages the same library as application
`a-98b1d8bb8dd7`; it is not a deployment claim.

---

## Design principle

Every idea is introduced **twice**: once informally (a picture, a calculation you can run in the
Lambda Lab, a game level) and once formally (a definition, a theorem, a machine-checked proof). The
course reuses and extends the author's earlier material — the *Falenty 2026* λ-calculus book and lab
(`nasqret/falenty-2026`) and the EML formalization (`nasqret/eml-formalization`) — so the notes are
continuous with work that already exists.

## Quick start (local build)

```bash
# 1. Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Build the knowledge book
jupyter-book build book/

# 3. Serve the landing page + lab locally
python3 -m http.server 8000   # then open http://localhost:8000/

# 4. Check the Lean artifacts
cd artifacts/lean && lake build
```

See [`docs/BUILD.md`](docs/BUILD.md) and [`docs/DEPLOY.md`](docs/DEPLOY.md) for the full pipeline.

## License

Code and associated documentation are released under the MIT License; prose in `book/`, `vault/`,
and `research/` is additionally available under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). See [`LICENSE`](LICENSE).

*Course notes co-developed with Claude (Anthropic) as a writing and formalization assistant.*
