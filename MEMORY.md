# Project Memory — VIASM 2026 "Automatic Theorem Proving in Mathematics"

> Durable facts about this project. One fact per bullet; update in place rather than duplicating.
> This is the human-and-agent-readable ground truth; the dated narrative lives in [`JOURNAL.md`](JOURNAL.md),
> the actionable breakdown in [`PLAN.md`](PLAN.md).

## Identity

- **What:** A 6-lecture mini-course *An introduction to automatic theorem proving in mathematics* for
  **VIASM** (Vietnam Institute for Advanced Study in Mathematics, Hanoi), 2026.
- **Author:** dr Bartosz Naskręcki — Faculty of Mathematics and Computer Science, Adam Mickiewicz
  University in Poznań (WMI UAM); also Centre for Trustworthy AI (CCAI), Warsaw University of Technology.
- **Local repo root:** `/Users/bnaskrecki/claude/hanoi` (git `main`).
- **Public GitHub repo:** `nasqret/vietnam2026`.
- **VIASM course page:** <https://viasm.edu.vn/en/hdkh/Mini-Course_AIATPM>
- **Lecture-title doc (Google Docs):** `1w08zKuLrq3XLFEWS_jNN4ZZv6lkXJWHKgVUSBWYSI7A`.

## Deployment targets (faculty server)

- **Host / SSH:** `bnaskrecki@lts-faculty.wmi.amu.edu.pl` (key `~/.ssh/id_ed25519`, already in agent).
- **Landing page + book + slides:** `~/public_html/vietnam2026/` → <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026>
- **Browser Lambda Lab:** `~/public_html/lab-lambda/` → <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda>
- **Server tooling:** Apache static hosting + PHP; Python 3.8, Node present. **No persistent daemons** →
  the lab must be **fully client-side** (this is why the browser lab uses Pyodide, not a server kernel).
- **Deploy verb:** `rsync -avz --delete <local>/ lts-faculty.wmi.amu.edu.pl:~/public_html/<target>/`.

## The six lectures (working titles)

1. A general introduction to type theory
2. Simple calculations with the Church (λ-)calculus
3. Propositional logic proofs (via Emily Riehl's *A Reintroduction to Proofs*)
4. Introduction to Lean
5. Advanced Lean
6. Auto-formalization of mathematics with Lean (the **EML** project as flagship case study)

## Source projects reused (author's own)

- **`nasqret/falenty-2026`** — existing λ-calculus JupyterBook (`book/en/`, EN) + the Python
  **`lambda_lab`** (Typer CLI + prompt_toolkit REPL + Rich): commands `church reduce lam tour quiz kb
  peano curry_howard eml aristotle games tutorial`. Covers Lectures 1–3 material already. Uses the same
  MEMORY/JOURNAL/PLAN + JupyterBook documentation pattern this project mirrors.
- **`nasqret/eml-formalization`** — Lean 4 + Mathlib formalization of `arXiv:2603.21852`
  (Odrzywołek, *All elementary functions from a single binary operator*). 36/36 primitives, 100 public
  theorems, sorry-free, 8062 `lake` jobs; live **EML Tree Builder** demo at
  <https://nasqret.github.io/eml-formalization/>. This is the Lecture 6 case study.
- **`nasqret/classical-foundations-ann`** — **style/layout template**: JupyterBook (`_config.yml`/`_toc.yml`)
  + self-contained `index.html` hero landing page (Inter font, CSS-variable design system, EN/PL toggle,
  card grid) + per-part reveal.js `slides_*.html` + in-browser `applets/*.html`.

## Key architecture decisions

- **Browser lab = Pyodide + xterm.js** (static, client-side). The lab's `prompt_toolkit` input loop is
  replaced by an xterm.js-driven driver; command dispatch + Rich (ANSI) output are reused. Features that
  need a subprocess (`lake`/`lean` verification) or network (`openai` LLM-judge, Aristotle) degrade
  gracefully / are stubbed in the web build.
- **Four formal foundations, on purpose:** Lean 4 = CIC, Agda = MLTT, Rocq (ex-Coq) = CIC, Mizar =
  Tarski–Grothendieck set theory. The same statements are proved in all four to *show* the foundations.
- **Local tooling present:** Lean/`elan`/`lake` ✓ (proofs verifiable here), `jupyter-book` ✓, `gh` (as
  `nasqret`) ✓, `pandoc` ✓. **Missing locally:** Agda, Rocq/Coq, Mizar, GHC → those artifacts are authored
  and CI-checked, not kernel-checked on this machine.

## Verified tool versions (research pass, 2026-07)

- **Lean:** current stable **4.32.0** (2026-07-13); latest RC 4.33.0-rc1. This repo's Lean artifact is
  pinned to the locally-installed **v4.28.0-rc1** (builds here, sorry-free, no axioms); EML pins Lean 4.28.
- **Mathlib:** ≈ **283,067 theorems / 134,678 definitions**, **> 2 million lines**, ~772 contributors.
  Note: `polyrith` is **retired** (its Sage certificate server was shut down) — do not teach it; search
  via **Loogle / LeanSearch / Moogle**.
- **Agda:** **2.8.0** (2025-07-05), agda-stdlib 2.x (v2.3); intensional predicative MLTT.
- **Rocq:** **9.2.0** (2026-03-27). Coq was renamed *The Rocq Prover*; first Rocq release 9.0.0
  (2025-03-12). MathComp 2.5.0.
- **Mizar:** **8.1.15** with MML **5.94.1493** (2025-05-30): 1493 articles, 65,000+ theorems.
- **Verified landscape numbers:** IMO 2024 AlphaProof+AlphaGeometry 2 = **28/42** (silver);
  DeepSeek-Prover-V2 **88.9%** miniF2F; Goedel-Prover-V2 **88.1%** (pass@32). Full log in
  `research/fact_checks.md`.

## Conventions

- **Documentation set:** `MEMORY.md` (this), `JOURNAL.md` (ISO dates, Europe/Warsaw), `PLAN.md` + `PLAN/*.md`
  (L0 goals → L1 modules → L2/L3 tasks), the Obsidian `vault/`, and the JupyterBook `book/`.
- **Language:** the course is delivered in **English** (audience is international at VIASM).
- **Growing notes:** the book/vault are expected to grow lecture-by-lecture; build foundations first.

## Status pointers

- Build/deploy strategy chosen: **go live incrementally** (public GitHub + faculty URLs as pieces land).
- Session-1 scope chosen: **maximum parallel build** across all workstreams.
- See [`JOURNAL.md`](JOURNAL.md) for the current day's state and [`PLAN.md`](PLAN.md) for what's next.
