# Plan — index view

The plan is multi-level. **L0** fixes the goals; **L1** lists the work modules (one file each in
[`PLAN/`](PLAN/)); **L2/L3** live inside those files as concrete tasks with acceptance criteria.
Narrative progress is in [`JOURNAL.md`](JOURNAL.md); durable facts in [`MEMORY.md`](MEMORY.md).

## L0 — Goals

> See [`PLAN/00_goals.md`](PLAN/00_goals.md)

Deliver a coherent, *growing* set of course materials that carry a mathematically-mature but
formal-methods-new audience from the λ-calculus and type theory to the auto-formalization of research
mathematics — with every idea presented **informally (runnable) and formally (machine-checked)**.

## L1 — Work modules

| Module | File | Short description |
|--------|------|-------------------|
| Landing page | [`PLAN/01_landing_page.md`](PLAN/01_landing_page.md) | `/vietnam2026` hero + 6-lecture plan + descriptions + cross-links; style of `classical-foundations-ann`. |
| Knowledge book | [`PLAN/02_knowledge_book.md`](PLAN/02_knowledge_book.md) | JupyterBook: the full text-friendly notes (maths + code + links) — the "learning data". |
| Obsidian vault | [`PLAN/03_obsidian_vault.md`](PLAN/03_obsidian_vault.md) | Atomic wiki-linked knowledge base; MOCs per lecture; source of truth for concepts. |
| Formal artifacts | [`PLAN/04_artifacts.md`](PLAN/04_artifacts.md) | Same statements in Lean / Agda / Rocq / Mizar — the four foundations, side by side. |
| Browser Lambda Lab | [`PLAN/05_browser_lab.md`](PLAN/05_browser_lab.md) | `lambda_lab` running client-side via Pyodide + xterm.js; deployed to `/lab-lambda`. |
| Slides | [`PLAN/06_slides.md`](PLAN/06_slides.md) | One reveal.js deck per lecture, to present live. |
| Research dossier | [`PLAN/07_research.md`](PLAN/07_research.md) | Depth, citations and current-landscape groundwork feeding every lecture. |
| Release & deploy | [`PLAN/08_deploy.md`](PLAN/08_deploy.md) | Git → GitHub → faculty server; incremental go-live; build/link checks. |

## L2 / L3

Each `PLAN/*.md` file spells out **objectives**, **subtasks**, and **acceptance criteria**. Tasks are
checkboxes; keep them current as work lands. The through-line and prerequisite graph from the research
synthesis are the backbone the book and vault follow.
