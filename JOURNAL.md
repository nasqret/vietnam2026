# Project Journal — VIASM 2026 "Automatic Theorem Proving in Mathematics"

Dates in ISO format, timezone Europe/Warsaw (UTC+01/+02). Newest entries at the bottom of each day.

---

## 2026-07-23 — Day 1: Foundations and going live

### Context

Asked to build the complete apparatus for a 6-lecture VIASM mini-course: a landing page, a growing
knowledge book, an Obsidian vault, formal artifacts in four provers, and — crucially — the existing
`lambda_lab` made to **run directly in the browser**. Build foundations first, then climb through the
six lectures. Reuse the author's `falenty-2026` and `eml-formalization` projects and the visual style
of `classical-foundations-ann`.

### Decisions (session kickoff)

- **Scope for session 1:** *maximum parallel build* — advance every workstream (docs, research, landing
  page, book, vault, artifacts, browser lab, deploy) at once.
- **Browser lab tech:** *Pyodide + xterm.js* terminal REPL (fully client-side; static-hostable on the
  faculty server, which runs no persistent daemons). Lean-kernel / LLM-judge features degrade gracefully.
- **Deploy strategy:** *go live incrementally* — public GitHub repo `nasqret/vietnam2026` + rsync deploys
  to `~/public_html/{vietnam2026,lab-lambda}` as each piece becomes ready.

### Done

- Reconnaissance: confirmed local toolchain (Lean/lake, jupyter-book, gh as `nasqret`, ssh/rsync to
  `lts-faculty` with key in agent, pandoc). Agda/Rocq/Mizar not installed locally.
- Cloned and studied the three reference repos (`classical-foundations-ann`, `falenty-2026`,
  `eml-formalization`); mapped their structure and style into [`MEMORY.md`](MEMORY.md).
- Initialized git repo (`main`) at `/Users/bnaskrecki/claude/hanoi` and the directory scaffold
  (`book/ vault/ artifacts/{lean,agda,rocq,mizar} lab-lambda/ slides/ research/ PLAN/ docs/`).
- Wrote the documentation spine: `README.md`, `MEMORY.md`, this journal, and the multi-level `PLAN`.
- Launched a background research workflow (`atp-course-research`): 6 lecture dossiers + 2 landscape
  sweeps → adversarial fact-check → synthesis (through-line, prerequisite graph, reading list,
  cross-language artifact plan, current tool versions).

### In progress / next

- Landing page `index.html` (style of `classical-foundations-ann`), then first deploy + repo push.
- Browser Lambda Lab: Pyodide boot + xterm.js terminal + web REPL driver around `lambda_lab`.
- JupyterBook skeleton (intro + 6 lecture chapters), Obsidian vault (MOC + concept notes),
  and first formal artifacts (Lean verified locally; Agda/Rocq/Mizar authored).
- Fold research-workflow output into the book, landing page, and reading lists when it returns.

### Open questions / risks

- **Google Doc:** no direct Docs write tool wired up; plan is to deliver paste-ready lecture titles +
  abstracts and, if desired, attempt the Drive route.
- **Pyodide fidelity:** `lambda_lab` imports `prompt_toolkit` (no TTY in Pyodide) and `openai`; the web
  build must bypass the REPL input loop and stub network/subprocess features. Some commands (`lean`,
  `aristotle`) will be read-only or disabled in the browser.
- **Artifact parity:** without local Agda/Rocq/Mizar, those proofs are authored + CI-checked, not
  kernel-checked here; keep them small and standard so CI is trustworthy.

### End of Day 1 — shipped

- **Landing page** (`index.html`) built in the `classical-foundations-ann` style; six lecture cards, the
  arc stepper, a *verified* "why now" panel (IMO 2024 = 28/42, Mathlib ≈283k theorems, DeepSeek-Prover
  88.9%), theme-aware, self-contained.
- **Knowledge book** — JupyterBook builds clean (8 pages, math + bibliography); intro + all six lecture
  chapters + references appendix.
- **Browser Lambda Lab** — Pyodide 0.28.3 + xterm.js 5.5.0, driving the author's *real* vendored engine
  (`lc`/`parser`/`church`) via a web REPL driver. Verified with local Python: `nf PLUS 2 3 → 5`, etc.
- **Formal artifacts** — Lean project **builds `sorry`-free, no axioms** (kernel-checked here); Agda,
  Rocq, Mizar authored; four-way comparison README.
- **Obsidian vault** — 30 wiki-linked concept notes + 7 MOCs, no dangling links.
- **Research** — the `atp-course-research` workflow (39 agents, 0 errors, ~1.4M tokens) produced 8
  dossiers + 30 fact-checks + a synthesis, materialized into `research/`. Verified versions recorded in
  `MEMORY.md`.
- **Docs/infra** — `README`, `LICENSE` (MIT + CC-BY-SA for prose), `Makefile`, `docs/BUILD.md`,
  `docs/DEPLOY.md`, GitHub Actions CI (book + Lean + lab-engine smoke test).

### Correction folded in from the research pass

- `polyrith` is **retired** in Mathlib (its Sage certificate server was shut down) — not taught.
- Pinned verified current versions: Lean 4.32.0 stable (artifact pins local 4.28.0-rc1), Agda 2.8.0,
  Rocq 9.2.0 (Coq→Rocq rename), Mizar 8.1.15 / MML 5.94.1493.

### Next (Day 2)

- Create the public GitHub repo `nasqret/vietnam2026`, push, and deploy landing + lab (+ book) live.
- Deepen L1–L3 book chapters from the falenty-2026 notebooks; build the six reveal.js decks.
- Extend the shared artifact set (√2 irrational, an EML-flavoured evaluation) across all four provers.
- Wire more lab commands (`tour` variants, `quiz`, `kb`) into the browser build.
