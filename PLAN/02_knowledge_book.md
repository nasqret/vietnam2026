# Module 02 — Knowledge book (JupyterBook)

**Goal:** the "learning data" — a text-friendly book with mathematics (MathJax), executable code,
and dense cross-links. One part per lecture; grows lecture-by-lecture. Reuses `falenty-2026/book/en`
chapters where they already cover Lectures 1–3.

## Structure
```
book/
  _config.yml  _toc.yml  intro.md  references.bib
  lectures/
    l1_type_theory/       l2_lambda_calculus/   l3_propositional/
    l4_lean_intro/        l5_lean_advanced/     l6_autoformalization/
```

## Subtasks
- [x] `_config.yml` (MathJax macros, myst extensions, bibtex), `_toc.yml` (6 parts), `intro.md`.
- [x] One index chapter per lecture with abstract, objectives, "run it" box, references.
- [ ] Port/adapt λ-calculus chapters from `falenty-2026/book/en/notebooks/*` (L1–L3).
- [ ] Author L4/L5 Lean chapters (term/tactic mode, Mathlib, worked proofs).
- [ ] Author L6 chapter around the EML case study + landscape.
- [ ] Embed the Lambda Lab (iframe) and links to artifacts.
- [ ] `jupyter-book build book/` clean; deploy `book/_build/html` under `/vietnam2026/book`.

## Acceptance criteria
- Book builds without errors; TOC has all 6 lectures.
- Maths renders; internal links resolve; each chapter cites real sources.
