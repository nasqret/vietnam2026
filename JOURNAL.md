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

## 2026-07-26 — prove/ch-build soundness overhaul (external audit implemented)

An external audit proved the interactive builders UNSOUND (Peirce's law received a false QED via
four cooperating defects). Full fix, all P0/P1/P2 items:

- **New trusted kernel** `stlc_types.py`: rigid `Atom` vs inference `MetaVar` (globally unique ids),
  one-way instance check, context-aware inhabitation search with found/none/limit verdicts.
- **One sound engine** `proof_builder.py` shared by `prove` AND `ch build` (`ch_builder` is now a
  facade; `ch_stlc` keeps only the Lean bridge): checked finalization (`qed` re-checks the term
  against the original goal and the session survives failure), proof-wide substitution propagated
  to sibling goals, free-variable rejection, validated binders, transactional `intros`.
- **Command grammar** (P1): arguments containing `->` are always propositions (`prove Q -> Q` no
  longer hits the `q` quit alias); meta commands match the complete line case-sensitively; in-proof
  `help`; nested `prove`/`ch build` refused without touching the session; the driver now routes
  every line to the single interactive owner before ordinary handlers.
- **Honesty fixes**: contextual `hint` validated through `exact`, depth-limit vs uninhabited
  distinguished (also in `ch type`); `refine` documented as an `exact` alias; KB "SAT prover" claim
  corrected; broken `prove demorgan1` tutorial step replaced; encyclopedia marked reference-only.
- **New suite** `test_prove_soundness.py`: the audit's soundness oracle + its 21 regression groups,
  parameterized over both front ends (55 tests). Full lab suite 359 green; book gate clean; the
  cookbook prove ladder R1–R5 and showcase transcript replay byte-identically.
- Deployed as build 2026-07-26a to /lab-lambda/ and /lab-lambda-next/; book re-staged.

## 2026-07-26 (later) — cookbook: the connective workshop

- New puzzles section "The connective workshop ★→★★★ — ∧ and ∨ without ∧ and ∨": seven `prove`
  rungs building conjunction, disjunction and negation from arrows alone (R-relative Church
  encodings) — pairing, projections-via-observer, ∧/∨ commutativity, P → ¬¬P, and modus ponens
  from an encoded pair. Every transcript captured from the real engine; principal-type gaps used
  as teaching beats (inl visible in the type; ∨-comm's proof term is C/flip; W7's continuation is
  W6's term). Honest footnotes: weak vs impredicative encodings (System F), handoff to Lean's
  real And/Or. Book gate now 168 deep links, all clean; site redeployed.

## 2026-07-26 (evening) — PLAN reconciliation

- All module checklists (00–07) reconciled against verified reality: live URLs, CI, artifacts,
  vault MOCs, research files each checked before ticking. Two items remain open by choice:
  service-worker offline precache for the lab, and a decktape PDF export of the slides as a
  travel backup. The 中文/Tiếng-Việt landing toggle is recorded as dropped (EN authoritative).

## 2026-07-26 (night) — tutorials: ENTER was dead in the browser

- Root cause: the driver's empty-line shortcut (`if not line: return ""`) predates the session-owner
  routing and swallowed ENTER before an active tutorial could see it — but ENTER is the tutorial's
  primary control ("ENTER = next", and gated steps run on it). The browser terminal always sent the
  empty line; the driver dropped it.
- Fix: empty input now routes to an active tutorial; everywhere else it stays a no-op. Verified a
  full ENTER-only walk of chapter 1 through every step kind (command, Lean walk, quiz checkpoint,
  exercise, reading, narrative) to "Chapter complete", plus mid-tutorial `?`/`s`/`q` and ordinary
  lab commands. Regression test added (suite: 360). Deployed as build 2026-07-26b to both channels.

## 2026-07-26 (late night) — full-lab glitch sweep

Systematic pass over the whole lab surface: all 31 commands + their help topics; all 6 tutorial
chapters walked ENTER-only to "Chapter complete"; quiz full flow (bundles, wrong/skip/score/stop);
both games; every kb card (17 topics, 28 concepts, 7 bundles, 121 resources); all ch explore (16),
tactic (27+27) and library (12+12) cards; the 12 quick buttons; tab-completion list; edge inputs
(Ω, 50-deep nesting, zero-width space, 60-antecedent proposition). Found and fixed four things:
a Polish-language quiz question (mc_lambda_05) and the owl combinator's Polish Lean comment
(translated); `commands` missing from tab-completion (added); bare `?` at the main prompt gave a
parse error (now a pointer to help — placed after owner routing so in-proof/tutorial `?` behavior
is untouched, verified in all five contexts). Suite 360 green; deployed as 2026-07-26c.

## 2026-07-26 (branch peano-lab) — Phase 2 designed: the Peano Lab

- Reviewed and sharpened the plan for a PA theorem prover ("a little Lean for Peano"): staged
  logic (equations → induction → quantifiers → automation), proof terms + an independent ≤300-line
  kernel checker (De Bruijn criterion — the audit lesson made law), intuitionistic core with a
  classical toggle, and the LLM trace format designed up front so every session generates corpus.
- Authored `docs/PEANO_LAB_DESIGN.md` (binding architecture), `PLAN/09_peano_lab.md` (M0–M9 with
  acceptance criteria, house rules for the implementing model), 18 API-pinning module stubs under
  `peano-lab/py/peano_lab/`, the "Building Peano Lab" book part stub + implementation diary, and
  the landing-page card (in development). Handing implementation to Codex from M0.

## 2026-07-27 (branch peano-lab) — Peano Lab M0: the trusted kernel

- Implemented frozen de Bruijn term/formula ASTs, ASCII+Unicode surface parsing, numeral sugar,
  deterministic canonical printing, capture-proof shift/substitution, inert proof certificates for
  the intuitionistic ND/equality/PA/IND rules, and a 196-line independent structural checker with no
  engine/UI imports.
- The acceptance certificate intentionally proves `forall x. x + 0 = x` through an IND instance;
  mutated motive/base/step/target/axiom/hypothesis variants are rejected. Further tests cover every
  rule family, eigenvariable escape, capture under quantifiers, malformed certificates, and all six
  exact PA axiom types.
- Adversarial review found and closed a Python subclass/equality forgery: the trusted checker now
  accepts exact kernel constructors only. Verification: Peano `42 passed`; existing Lambda Lab
  `360 passed, 36 subtests passed`; import hygiene, byte-compilation, and diff checks clean.

## 2026-07-27 (branch peano-lab) — Peano Lab M1: equational engine

- Added frozen goal/hole proof states, exact history snapshots, engine-only term metavariables,
  rigid/flexible copy-on-write unification with occurs check, and proof-wide substitution through
  sibling goals, contexts, and partial certificates. Substitutions are read-only mapping proxies;
  `undo` returns the exact saved state.
- Added `refl`, `symm`, `trans`, `congr`, `exact`, `assumption`, directed first-occurrence `rewrite`
  (including reverse and hypothesis forms), deterministic PA3–PA6 instantiation, and central tactic
  dispatch. `S 0 + S 0 = S (S 0)` closes as `rewrite PA4; rewrite PA3; refl` and its explicit
  certificate passes the kernel.
- `checked_final` requires the session owner's original formula separately from the untrusted state;
  replacing a state's cached target cannot forge QED. The v1 logger records successes and failures,
  keeps metavariable aliases stable across transitions, scrubs ANSI everywhere, and emits its footer
  only after kernel acceptance.
- Three adversarial reviews found and closed mutable history aliases, target-replacement QED, and
  transition trace-identity defects. Verification: Peano `95 passed`; the M1 attack suite rejects
  `0 = S 0`, non-equation rewrites, unknown hypotheses, unresolved metas, and forged targets.

## 2026-07-27 (branch peano-lab) — Peano Lab M2: induction

- Added `intro x`, `specialize h t`, and `induction n`. Universal introduction shifts the entire
  hypothesis context beneath its eigenvariable; specialization uses capture-proof opening and an
  explicit kernel-checkable local cut. Induction supports both a fresh binder on a `forall` goal
  and abstraction of an already named rigid context variable, including beneath inner quantifiers.
- `forall n. 0 + n = n` closes interactively in six tactics and `add_succ_left` closes in nine;
  both generated certificates pass the independent checker against their original statements.
  The attack suite confirms that the IH is absent from the base, cannot close a mismatched step,
  and cannot turn an unfinished induction into QED.
- Three independent reviews exercised multiple de Bruijn indices, nested binders, shifted
  hypotheses, outer-variable capture attempts, transactionality, and random reflexive motives.
  Review found only display-namespace collisions; reserved parser words and generated binder/IH/
  `_before`/`_parameter` names are now collision-free across term variables and hypotheses.
  Verification: Peano `118 passed`; existing Lambda Lab `360 passed, 36 subtests passed`.
