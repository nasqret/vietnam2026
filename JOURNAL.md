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

### Day 1 (cont.) — lecture notes, slides, and second-wave artifacts (all live)

- **Six full lecture notes.** Expanded every book chapter into a rigorous 3.5k–4.4k-word lecture note
  (definitions, theorem statements + proofs/sketches, 3–4 worked examples, "run it" boxes, exercises,
  references), grounded in the research dossiers + falenty-2026 + the EML repo — via a 12-agent
  `atp-notes-and-slides` pipeline (0 errors). Book builds with **0 warnings**; all lab deep-links
  absolutized; `artifacts/coq`→`rocq` fixed.
- **Six reveal.js decks** (`slides/lecture1–6.html`, 15–16 slides each) built from each note off a
  shared template; MathJax macros added to every deck.
- **Artifacts, Statement 4** — a tiny EML-flavoured expression evaluator (`Tm`+`eval`, `eval_add`,
  `eval_add_comm`) in Lean (kernel-checked, no axioms), Agda, Rocq.
- **Lab commands** `peano`, `alpha`, `lean`, plus a graceful "desktop-only" responder (ch/kb/tutorial/…),
  so every `?cmd=` deep-link in the notes resolves.
- **Live:** landing cards wired to chapters + decks; slides picker clickable; site + lab redeployed;
  all URLs 200. Repo `nasqret/vietnam2026` fully pushed and in sync.

### Still open (Day 2+)

- √2-irrational artifact across provers (Lean needs Mathlib — keep it out of the fast default build).
- Deepen the browser lab (`quiz`/`kb` data), or link the desktop lab where those are referenced.
- Visual browser QA pass of the live lab (Pyodide boot) once the Chrome extension is connected.
- The Google Doc lecture titles (delivered as paste-ready text; no Docs write tool available).

## 2026-07-23 (evening) — the lab reaches feature-parity with the desktop (where feasible)

- **Quality pass:** 55 book-rendering glitches → 0 (dollar-pairing + math-in-headings root causes);
  40 adversarially-verified review findings applied (incl. two Lean proofs in notes/slides that never
  compiled — fixed and compile-checked); hero artwork on the landing page; vendor bundle (Pyodide,
  xterm, fonts — 14 MB) self-hosted for the worker preview.
- **Desktop ports (6 agents):** `ch` (Algorithm W + Wajsberg inhabitation — Peirce demo restored),
  `prove` (interactive Curry–Howard builder with ?ₙ holes and λ-term extraction), `tutorial` (all 12
  chapters), `alligators`, `ag` replays, full `kb` (145 entries, search) and `quiz` (9 bundles, ~290
  questions, 4 stray PL items translated).
- **New commands from the improvement review:** `eta`, `debruijn`, `let`/`defs`/`undef`, redex
  highlighting in `reduce`, `help <command>` topic pages; front-end TAB completion + localStorage
  history. Builds 2026-07-23k / k-worker, both deployed. 279 unit tests + 18/18 e2e under real Pyodide.
- **Still desktop-only by design:** games, eml compile, aristotle, acorn, lang.
- **Open:** promote the worker preview to stable after a browser check; service-worker offline after
  that; Playwright CI; real assistive-tech testing.

## 2026-07-23 (night) — pedagogy pass: the notes learn to use their own laboratory

- 13-reviewer teaching-quality fleet (102 raw → 44 confirmed findings; every proposed lab command
  validated against the real driver) + 12 appliers. 22 new "Run it" moments weave prove/ch/eta/
  debruijn/alligators/let/equiv into the exact teaching spots; one incorrect lab claim fixed
  (`ch term` vs `ch lean`); intuition boxes added at the classic stall points.
- Speaker notes on all 93 slides across the six decks (spoken lecturer script, drawn from the notes).
- New: λ-calculus cheatsheet appendix (every definition + encoding + a runnable command per row);
  intro.md "How to work with this course" workflow; landing lab card now names the prover/inference/
  tutorials.
- Verified: 0 warnings, 0 glitches on 9 pages, 93/93 slides with notes, 279 lab tests, live deploy.

## 2026-07-23 (late) — box typography + the Lambda Lab cookbook

- Typography pass: 33 dense admonition walls restructured to the house style (bulleted Run-it boxes,
  labeled worked-example steps, statement-first theorems); link parity byte-identical; dense 33 → 0.
- NEW book part: **The Lambda Lab cookbook** — 19,700 words across four chapters (grand calculations,
  puzzles with dropdown solutions, curiosities & lore, feature showcase), every printed output produced
  by the real engine. Highlights: Ackermann to A(3,2)=29, a terminating Y-combinator factorial, a
  derived-and-fitted step law for POW predicting the budget cliff, Böhm–Berarducci trees, the growing Ω₃.
- New quality gate `scripts/verify_book_commands.py` (also in CI): replays every ?cmd= deep link and
  session block in the book against the engine — 162 links, all clean.

## 2026-07-24 — release-readiness audit

Full battery green: repo clean/in-sync; GitHub Actions green 5/5 runs (book+gate, lean, lab 304
tests, rocq, agda); 11/11 live URLs 200; book command gate 162 links clean; artifacts compile in
all three installed provers. Tagged v1.0.0-rc1. Open by choice: worker-preview promotion (awaits a
browser check), service-worker offline, assistive-tech testing, Mizar kernel-check.
