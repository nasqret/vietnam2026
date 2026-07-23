# An Introduction to Automatic Theorem Proving in Mathematics

> A six-lecture VIASM mini-course taking you from the **λ-calculus and type theory** through
> **Lean** all the way to the **auto-formalization of research mathematics** — building the
> foundations first, then climbing.

**Course page (VIASM):** <https://viasm.edu.vn/en/hdkh/Mini-Course_AIATPM>
**Landing page (notes hub):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026>
**Live Lambda Lab (runs in your browser):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda>
**Author:** dr Bartosz Naskręcki — Faculty of Mathematics and Computer Science, Adam Mickiewicz University in Poznań · Centre for Trustworthy AI (CCAI), Warsaw University of Technology

---

## The six lectures

| # | Title | One line |
|---|-------|----------|
| 1 | **A general introduction to type theory** | Judgments, simply-typed λ-calculus, Church vs Curry, and why proof assistants stand on type theory rather than set theory. |
| 2 | **Simple calculations with the Church (λ-)calculus** | Untyped λ-calculus, β/η-reduction, Church booleans & numerals, the predecessor, and the Y-combinator — every step reproducible in the Lambda Lab. |
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
| `artifacts/` | **Formal proofs** of the same statements in four systems: `lean/`, `agda/`, `rocq/`, `mizar/`. |
| `lab-lambda/` | The **Lambda Lab**, repackaged to run **directly in the browser** (Pyodide + xterm.js). Deployed to `/lab-lambda`. |
| `research/` | The **research dossier** — the depth/citation groundwork behind every lecture. |
| `docs/` | Lecturer-facing docs: how to build, deploy, and run each piece. |
| `MEMORY.md` · `JOURNAL.md` · `PLAN.md` + `PLAN/` | Project **memory**, dated **journal**, and the multi-level **plan**. |

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

Code is released under the MIT License; prose and lecture notes under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). See [`LICENSE`](LICENSE).

*Course notes co-developed with Claude (Anthropic) as a writing and formalization assistant.*
