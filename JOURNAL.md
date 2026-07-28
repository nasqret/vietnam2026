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

## 2026-07-27 (branch peano-lab) — Peano Lab M3: full first-order tactics

- Added kernel-checkable tactics for implication, conjunction, disjunction, bottom, universal and
  existential quantification: `apply`, `split`, `left`, `right`, `cases`, `exfalso`, `exists`, and
  the `forall_elim` alias. `S n = 0 -> false` closes through PA1; defined order expands `a <= b`
  to `exists k. k + a = b`, and `forall n. n <= n` closes in eight primitive tactics.
- Witness metavariables now carry binder-protection depth. This preserves proof-wide inference but
  rejects eigenvariable escape, including the false `exists x. forall y. x = y` route. Rewriting
  descends through quantifiers with shifted sources, replacements, and motives; every generated
  equality transport is independently checked.
- Resolved the design's classical-mode tension explicitly: `DNE` is a visible certificate node,
  ordinary `check` remains intuitionistic, and only the session owner's exact Boolean selects
  `check_classical` at finalization. Mode commands and banners are labeled, OFF by default, and
  mode changes use unchanged-goal v1 trace events rather than silently changing the trace schema.
- Added pure bounded hints with `found/none/limit/done`, deterministic defined-sugar printing, and
  permanent regressions for capture, non-Boolean classical authority, failed mode traces, and
  vacuous universal/existential instantiation. Three independent adversarial reviews found no
  remaining soundness defect after those fixes. Verification: Peano `187 passed`; existing Lambda
  Lab `360 passed, 36 subtests passed`; checker `234` lines; compile and diff checks clean.

## 2026-07-27 (branch peano-lab) — Peano Lab M4: tacticals and checked automation

- Added pure `then`, `orelse`, `repeat`, `first`, `all_goals`, and one-based `focus` combinators.
  Focused execution splices the exact certificate hole, keeps proof-wide metavariables shared, and
  collapses a compound command into one exact undo transaction. `repeat` stops on failure,
  no-progress, logical cycles, or an explicit resource guard.
- Grew rewriting into deterministic `simp`: PA3–PA6 plus explicit checked/context rules, ordered by
  LPO so even size-growing PA6 terminates. Every step retains its instantiated equality proof and
  `EqSubst` motive; congruence finishing constructs only kernel-visible `CongS`/`CongAdd`/`CongMul`.
  With the two prior ladder lemmas in scope, `induction n; simp` proves `add_comm` through the
  tactical layer.
- Separated computation from theoremhood in `decide.py`. Closed equations can receive generated
  PA normalization certificates only after an independent check; finite quantifier enumeration is
  an explicitly labeled, non-proof bounded verdict. Malformed, open, subclassed, and engine-meta
  inputs are rejected at the public boundary.
- Added depth- and node-bounded `auto`. Search enumerates sibling alternatives (including shared
  metavariable assignments), rejects kernel-invalid complete leaves, and replays only the winning
  primitive plan into a linear v1 trace. Exact external classical authority adds DNE after
  constructive choices; limit exhaustion is always a non-verdict. Cold `auto 5` closes and
  kernel-checks `zero_add`, `add_succ_left`, `add_comm`, and `add_assoc`.
- Independent audits exercised 1,500 random search formulas, 500 simp transports, 4,845 arithmetic
  certificate checks, 10,000 bounded formulas, and 164 tactical/adversarial properties. Found and
  fixed invalid search leaves, sibling-backtracking incompleteness, node/depth mislabeling,
  focus-local metavariable defaulting, and malformed state boundaries. Verification: Peano
  `277 passed`; Lambda Lab `360 passed, 36 subtests passed`; checker `234` lines; compile and diff
  checks clean.

## 2026-07-27 (branch peano-lab) — Peano Lab M5: browser proof lab

- Added a self-hosted xterm/Pyodide worker page with its own BUILD key, exact 21-module Python
  manifest, cancellable/restartable worker, persistent command history, deep links, PA quick actions,
  accessible status reporting, and a `4,000`-character input boundary. The browser driver rejects
  decimal sugar above `256` before successor expansion; that is an interface resource limit, not a
  statement in PA.
- Added the `pa` command family and the audited single-session-owner grammar. The owner keeps the
  original formula, name table, exact classical Boolean, trace logger, and stable display aliases
  outside `ProofState`. Every successful `qed` invokes `checked_final` against those retained values;
  failed tactics and failed finalization preserve the live session exactly.
- Added deterministic goals/context/partial-certificate panels, complete-line aliases, in-proof
  help, and all primitive/tactical/simp/auto routes. Browser output and v1 JSONL records visibly
  escape terminal controls, bidi/format marks, surrogates, and Unicode line/paragraph separators;
  adversarial trace tests preserve exactly one physical line per record.
- Added version-pinned shared-vendor fetching, hash verification, an exact staged artifact, and safe
  `stage-peano`, `deploy-peano`, and `deploy-peano-next` targets. No SSH deployment was performed.
  All 26 served paths returned HTTP 200 locally, source/stage comparison was exact, and the exact
  staged 21-file worker payload loaded under pinned Pyodide 0.28.3 and proved `add_comm` with
  `auto 5; qed`.
- Independent UI, shell, deployment, and tactic fuzz audits closed control injection, cache,
  cancellation, pending-request, trace-focus, footer-authority, alias-stability, numeral-expansion,
  and JSONL framing defects. Verification: Peano `312 passed`; Lambda Lab `360 passed, 36 subtests
  passed`; checker `234` lines; byte-compilation, shell syntax, deploy dry runs, hashes, and diff
  checks clean. The in-app visual browser was unavailable, so DOM/keyboard visual interaction is
  recorded as a manual release check rather than claimed as completed.

## 2026-07-27 (branch peano-lab) — Peano Lab M6: executable curriculum

- Added 28 immutable tactic cards: every 20 operational primitives, all six tacticals, `auto`, and
  read-only `hint`. Each card separates goal-state effect from certificate effect and includes a
  worked script plus common failures. CI replays all 28 scripts from a fresh session through checked
  QED, so the encyclopedia cannot drift into plausible but invalid prose.
- Added 13 deterministic KB cards: PA1–PA6, induction as a schema, de Bruijn indices/capture, LCF
  versus explicit proof terms, the De Bruijn criterion, simplifier termination, Gödel limits, and
  HA versus classical PA. `kb`, `pa kb`, lookup, accent-insensitive search, and terminal-safe
  rendering share the same frozen registry.
- Added two ENTER-driven tutorials. `add_comm` runs a genuine premise-free 12-command nested-
  induction proof with no `auto` or imported lemma; `symm_all` follows a toy tactical through
  semantic composition, grammar, and tests, then executes the equivalent `all_goals symm` specimen.
  Tutorial proof commands use a private nested proof owner, avoiding router deadlock, and completion
  requires the production QED path to close after independent kernel checking.
- Extended the book gate with collision-free dual driver loading, URL/path-aware Peano deep-link
  routing, and `pa>` session blocks while retaining `λ>` behavior. Broken tactics and failed QEDs
  are negative fixtures. The built-book gate checked 17 files, 172 links, and 6 blocks/33 commands
  (168 Lambda links and 5 Lambda commands; 4 Peano links and 28 Peano commands); all replayed clean.
  Jupyter Book built all 17 source pages successfully. Verification after final audit: Peano
  `373 passed`; Lambda Lab `360 passed, 36 subtests passed`; checker unchanged at `234` lines.

## 2026-07-27 (branch peano-lab) — Peano Lab M7: checked theorem library

- Added a deterministic 20-entry theorem library: all 15 binding arithmetic/order rungs plus five
  named helper lemmas, ending at `forall n m. n * m = 0 -> n = 0 \/ m = 0`. Every entry stores a
  closed statement, only earlier dependencies, and an exact tactic script replayed in CI.
- Kept theorem reuse outside the trusted base. Replay first checks a dependency-curried theorem,
  then simultaneously substitutes the earlier closed certificates, contracts capture-safe
  universal/implication beta redexes, and independently checks the resulting certificate from the
  empty context against the original dependency-free statement. An arithmetic-only draft exposed
  both sequential-substitution capture and introduction-form synthesis hazards; permanent tests now
  cover proposition and term shifting, existential binders, multiple dependencies, and mutated
  capstone leaves.
- Added `pa lib`: the card distinguishes the original statement, temporary curried replay target,
  generated dependency prelude, authored body, and final kernel result. Added `pa lean`: exact
  de Bruijn-to-Lean translation over `Nat`, explicit dependency metadata, one intentional `sorry`,
  and an exact URL-encoded Live Lean link. All 20 emitted stubs elaborate under local Lean 4.28;
  associativity regressions ensure Lean's right-associative `∧`/`∨` cannot alter the formula tree.
- Added a theorem-ladder Jupyter Book page and five connected Obsidian notes/MOC entries. The book
  gate now checks 18 files, 175 links, and 6 blocks/33 commands; the vault has 43 notes with zero
  unresolved wiki-links. Warning-as-error Jupyter Book build succeeds.
- Three independent audits checked public semantics, code quality, and cut-elimination soundness.
  All 20 certificates are closed and independently valid; poisoned proof leaves and rotated goals
  are rejected. The exact staged 28-file worker payload loaded in pinned Pyodide and rendered the
  capstone library card plus Lean export. Verification: Peano `433 passed`; Lambda Lab `360 passed,
  36 subtests passed`; checker unchanged at `234` lines. Visual DOM interaction remains the same
  explicit manual release check because the in-app browser runtime is unavailable. No SSH deploy.

## 2026-07-27 (branch peano-lab) — Peano Lab M8: the construction book

- Published the binding six-chapter “Building Peano Lab” part: why staged PA; the kernel and De
  Bruijn criterion; tactic anatomy; tacticals as a language; induction and the checked ladder; and
  Gödel/engineering limits. The 7,881-word narrative is built from the implementation diary and
  links architectural claims to the actual source and tests.
- Added replay fixtures directly to the prose. The six new chapters contain 15 browser deep links
  and 11 real sessions/45 commands; the production Peano driver replays all of them. Three
  independent audits corrected eight precision errors, including the `auto` undo/trace exception,
  ordered-permutative `simp`, trace snapshot sufficiency, and the capstone's unused base premise.
- Replaced the landing-page “in development” card with a live card, an accessible release panel,
  and direct lab/book actions. Added six Peano-specific Obsidian concept notes and connected them
  from the Peano Lab MOC.
- Acceptance is green: warning-as-error Jupyter Book built 24/24 pages; the full book gate replayed
  190 deep links plus 17 blocks/78 commands (22 Peano links and 73 Peano commands); the vault has 49
  notes and zero unresolved wiki-links. Verification: Peano `436 passed`; Lambda `360 passed, 36
  subtests passed`; checker unchanged at `234` lines. Visual DOM interaction remains the explicit
  manual release check because the in-app browser runtime is unavailable. No SSH deployment.

## 2026-07-27 (branch peano-lab) — Peano Lab M9: checked data, untrusted policy

- Added deterministic batch generation through the real proof engine and production `TraceLogger`.
  Every session contains a controlled transactional failure; successful sessions receive a footer
  only after `checked_final` validates the certificate against the owner-held original theorem.
  Full run fingerprints cover configuration, theorem fixtures, generator/checker sources, and the
  Python runtime, preventing seed-only session-ID collisions across collated runs.
- Added a strict standard-library exporter. It validates exact ordered v1 fields, JSON types,
  complete sequential sessions, goal continuity, transactional errors, adjacent footer counts, and
  equality between the footer theorem and the initial rendered goal. It globally deduplicates while
  ignoring only session/step identity, keeps theorem groups together, rejects input/output aliases,
  and stages/rolls back the train, validation, and statistics artifacts as one publication set.
- Published a reproducible learning release with all ladder sessions disabled: 13,152 unique
  transitions from 1,596 kernel-checked QED sessions, split into 12,540 train and 612 validation
  rows, including 1,596 honestly labeled failures. The manifest retains per-session family/template
  provenance, run/source/checker hashes, and the omitted raw stream's exact size and SHA-256.
- Added the fixed evaluation-v1 protocol for `le_trans`, `le_antisymm`, `le_total`, and
  `mul_eq_zero`. Policies see only canonical goals with rollout-stable metavariable aliases plus a
  visible-goal-derived local RNG; a literal goal-set digest prevents silent benchmark drift. The
  deterministic random baseline ran 32 attempts end to end and scored 0.0 honestly; positive and
  adversarial tests confirm that only independent finalization can produce `proof`.
- Three independent audits exposed and closed case-insensitive input overwrite, footer/split
  misbinding, partial output publication, symlink-loop diagnostics, run-ID collisions,
  metavariable-display drift, hidden-label RNG leakage, nested-auto status drift through every
  tactical (including `repeat`), absent case-only output aliasing, and dynamic benchmark drift.
  Final verification: focused M9 `62 passed`; Peano `498 passed`; Lambda `360
  passed, 36 subtests passed`; all-ladder generation/export 13,417/13,412 rows; warning-as-error
  Jupyter Book green; 190 links and 17 blocks/78 commands replay; vault 52 notes/228 links/0
  unresolved; trusted checker unchanged at 234 lines. No model was trained and no SSH deployment
  was performed.

## 2026-07-27 (branch peano-lab) — Peano Lab M10: live checked-theorem reuse

- Added `use <library-theorem> [as <alias>]` to the live surface without adding a theorem-name rule
  to the kernel. Library/UI code resolves and replays the named rung; the engine independently
  rechecks the exact closed formula/certificate pair and exposes it through an ordinary implication
  cut. Existing `specialize`, `apply`, `rewrite`, `exact`, and `simp` tactics consume the resulting
  local hypothesis unchanged.
- Added one shared browser/evaluator finalization path. It contracts the exposed implication and
  universal cuts in a transient certificate, then calls the existing independent checker with the
  session owner's original target and exact classical authority. The live immutable proof remains
  untouched, so one `undo` restores the exact state even when a tactical collapsed several imports
  into one transaction.
- Hardened the temporary theorem environment with iterative 4,096-node import, 32,768-node live-
  certificate, and 128-level budgets. Exhaustion is a traced transactional `TacticLimit`; remaining
  host recursion exhaustion at QED becomes `InvalidProof` and retains the owner. Unicode aliases
  now follow the same identifier rules as `intro`, and the browser completion list exposes `use`.
- Documented the boundary in the binding design, README, construction book/diary, tactic card, and
  connected Obsidian concept. M10 deliberately does not claim to solve the odd-square induction
  step: checked theorem availability is now present, while proof-producing polynomial
  normalization remains M11–M12 work.
- Acceptance is green: the two-import composition reaches checked QED; focused M10 reports 17
  tests; Peano `520 passed`; Lambda `360 passed, 36 subtests passed`; the warning-as-error book and
  all 190 links/18 blocks/85 commands pass; vault 53 notes/238 links/0 unresolved. The regenerated
  source-bound corpus retains 13,152 transitions from 1,596 checked sessions, and the kernel checker
  remains untouched at 234 lines. No deployment was performed.

## 2026-07-27 (branch peano-lab) — Peano Lab M11: checked semiring basis

- Audited the existing ladder against the exact oriented equations a proof-producing polynomial
  normalizer needs. Only `one_mul`, `mul_one`, and `add_mul` were absent; zero laws, both
  associativity/commutativity pairs, and the opposite distributive orientation were already present.
- Added those three as ordinary scripted entries after `mul_assoc`. Every dependency points to an
  earlier rung, each final certificate checks from the empty context, and generated Lean stubs retain
  the exact statements. No numeral oracle or kernel rule was introduced: numerals remain successor
  terms, with closed coefficient proofs built from PA3–PA6.
- Added deterministic replay and binder-capture regressions. Each new certificate is imported below
  both proposition and term binders and specialized with an outer-variable term before transient
  cut compilation and independent QED checking.
- Acceptance is green: focused M11 `84 passed`; Peano `527 passed`; Lambda `360 passed, 36 subtests
  passed`; all three exact stubs elaborate under Lean 4.28 with only intentional `sorry` warnings;
  the warning-as-error book and 190 links/18 blocks/85 commands pass; vault 54 notes/247 links/0
  unresolved. The regenerated 13,152-row corpus manifest records all 23 rungs and 1,596 checked
  sessions; the trusted checker remains untouched at 234 lines. No deployment was performed.

## 2026-07-27 (branch peano-lab) — Peano Lab M12: certificate-producing `ring`

- Added a deterministic sparse-polynomial normalizer for rigid PA terms built from zero,
  successor, addition, multiplication, numerals, and visible variables. Monomials use a fixed
  total-degree/de-Bruijn order and natural coefficients; equal computed forms merely select the
  proof construction path.
- Every successful normalization constructs a kernel proof from PA3--PA6 and the rechecked M11
  semiring certificates. The engine checks supplied and instantiated laws and checks the generated
  equality certificate before closing the goal; the normal surface QED then checks the complete
  proof against the owner-held original theorem.
- Kept `ring` argument-free and identity-only. It does not search or normalize hypotheses. The
  odd-square induction uses witness `x + S n`, middle term `((2*n+1)*(2*n+1)) + 8*S n`, a first
  `ring`, explicit `rewrite IH_witness`, and a final `ring`. This exposes exactly where induction,
  substitution, and polynomial identity checking meet.
- Added explicit bounds for AST size/depth, variables, degree, monomials, coefficients, work,
  generated proof size/depth, and wall-clock time. The required large normalization used about
  1.4 seconds under native CPython, so the default is five seconds to leave a conservative browser
  margin. The in-app browser was unavailable for a direct Pyodide measurement; that remains a
  deployment check. False identities and unsupported targets are transactional `TacticError`s;
  resource exhaustion is a transactional `TacticLimit`.
- Acceptance is green: the exact odd-square session reaches checked QED against its original goal;
  adversarial tests cover mutated coefficients/constants/witness/middle, conditional misuse,
  forged laws/proof leaves, exact undo/traces, malformed reduction input, and every explicit limit.
  Peano reports `581 passed`; Lambda `360 passed, 36 subtests passed`; the warning-as-error 24-page
  book and 190 links/19 blocks/96 commands pass; vault 55 notes/258 links/0 unresolved. The final
  source-bound corpus remains 13,152 rows from 1,596 checked sessions, local staging assembly is
  green, and the checker remains 234 lines. The in-app browser was unavailable, so direct Pyodide
  timing remains a deployment check. No deployment was performed during this verification pass.

## 2026-07-27 (branch peano-lab) — Peano Lab M13: checked basic arithmetic

- Added `norm_num` as a bounded, argument-free certificate constructor for equality goals,
  optionally below leading universal binders. It finds maximal closed non-numeral islands,
  computes a candidate unary numeral, and constructs PA3--PA6 plus congruence evidence. The low-
  level engine checks every island, both term transports, and the equality bridge; direct tactic
  closure is checked again before commit, and QED still checks the owner-held original theorem.
- Kept the boundary narrow and visible. A true reflexive normal form closes; useful open
  normalization installs one transported residual hole; false closed equations, non-closing
  no-progress requests, unresolved metas, and unsupported goals fail transactionally. Local
  hypotheses are not arithmetic oracles. `simp` rewrites, `norm_num` certifies concrete arithmetic,
  `ring` proves unconditional polynomial identities, and `auto` performs bounded search; general PA,
  nonlinear hypothesis solving, and a future Presburger `omega` remain outside this tactic.
- Hardened both command and pure `hint` preflight against malformed exact states, cyclic
  substitutions, hostile partial certificates, deep universal spines, wrong focused-hole order,
  forged generator metadata/certificates, and pre/post-splice size limits. Hint projects the same
  immutable replacement and commit without allocating a global hole or changing history. The
  public limits are 256 equality-term nodes/depth 64, 64 leading universals, 32 computations,
  value 128, 25,000 work units, a 50,000-node/256-level numerical bridge, a 100,000-node/512-level
  live proof, and five seconds; the Web Worker Stop control remains the hard abort.
- Added the browser card/completion/quick proof, an ENTER-driven checked tutorial, executable book
  chapter, connected Obsidian note, deterministic `norm_num` traces, and evaluator-v2 regressions.
  Generator v2 adds 96 checked closed-coefficient sessions while preserving the v1 row schema. The
  byte-reproduced release has 13,344 unique transitions from 1,692 checked QED sessions (13,326
  train / 18 validation), 1,692 labeled transactional failures, zero duplicates, and exact source,
  runtime, raw-stream, and artifact hashes. The nine validation formula groups are intentionally
  documented as a same-family pipeline check, never a cross-family research claim.
- Local acceptance is green: Peano `641 passed`; Lambda `360 passed, 36 subtests passed`; the
  warning-as-error 25-page book builds and 193 deep links/23 blocks/125 commands replay; vault 56
  notes/271 links/0 unresolved with no orphan concepts; the all-ladder smoke generated 13,636 raw
  and 13,631 unique rows; evaluator v2 ran 32 kernel-judged attempts with the honest random baseline
  at pass@8 `0.0`; local staging and all vendor hashes pass; the trusted checker remains exactly 234
  lines. The in-app browser had no available instance, so direct Pyodide interaction was not
  claimed; browser-shell tests and staged static inspection cover the worker, Stop path, build tag,
  completion, tutorial, packaged module, and displayed bounds.
- Published commit `5166bd2` first to `/peano-lab-next/`, then promoted the same assembly to
  `/peano-lab/`; both returned HTTP 200 as build `2026-07-27h`. The production and staging pages
  share SHA-256 `4ade3a594ee248690919351ea44d4eec2c5960a76100e5197eac42de39e0c7b7`,
  and the fetched worker, `norm_num` source, and Pyodide loader each matched local staging exactly.
  The updated `/vietnam2026/` landing page and `book/peano/arithmetic-automation.html` also returned
  HTTP 200 and matched their built files byte for byte. `main` was not touched.

## 2026-07-27 (branch peano-lab) — Peano Lab M14: browser cold-start delivery

- Investigated the reported slow load as a transport problem rather than a proof-engine problem.
  The live page itself was small, but a cold start pulled an uncompressed 8,645,967-byte WASM file,
  a 2,416,866-byte standard-library ZIP, and then 31 application sources one request at a time. Live
  responses had no explicit cache policy; no server-side Python process was involved.
- Made vendor URLs genuinely immutable by placing the pinned mirror below
  `vendor/v-85fb3352e49c/`, where the identifier is the leading digest of the canonical vendor
  manifest under `LC_ALL=C`; this avoids machine-locale-dependent release IDs. The fetch script
  refuses changed bytes under the old identifier. Review then caught that
  query strings alone did not make overwritten application paths immutable, so worker/Python bytes
  also moved below `releases/a-573bb5060d7b/`, derived from `APP_MANIFEST.sha256`. Deployment retains
  old namespaces and uploads complete assets before publishing `index.html`. Versioned responses
  receive a one-year immutable policy, unversioned files revalidate, errors are non-storable, and
  the page is explicitly non-storable so release `2026-07-27i` is discovered.
- Added guarded Apache Brotli/gzip negotiation for WASM and source-like media while excluding ZIP
  and WOFF2. The fallback works when Brotli is unavailable and never stacks encodings. The policy is
  staged before production because `.htaccess` permissions and loaded modules belong to the host.
- Replaced the serial source loop with concurrent non-rejecting fetch envelopes overlapped with
  Pyodide startup. Failures are selected in declared order and no file is mounted if any fetch
  fails; successful sources mount deterministically in the same order as before. A Node VM test
  resolves requests backwards and injects multiple failures to pin both properties.
- Added a Peano pytest GitHub Actions job and updated design, deployment, plan, README, book, vault,
  memory, and diary surfaces. Exact inventory checks cover the 32 worker/Python entries and retained
  vendor namespaces; the live gate checks compression negotiation, 200/206/304/error caching, every
  application hash, decoded WASM integrity, and encoded size. The current focused browser/deploy
  gate reports `21 passed`; full and live acceptance is recorded after the sequential release gates
  and staging promotion.
- The frozen local candidate passed Peano `647 passed`; Lambda `360 passed, 36 subtests passed`; a
  clean 25-source warning-as-error book build; 193 deep links and 125 replayed commands; and a
  57-note/281-link vault with no unresolved links or disconnected concept notes. Both exact
  manifests pass, the trusted kernel is unchanged, and `checker.py` remains 234 lines.
- Published candidate commit `a099596` to `peano-lab` and staging. Live gzip succeeds, but the cache
  gate stopped because guarded account-level directives emitted no cache header and an unguarded
  `Header` probe returned 500. This establishes an account-level configuration boundary, not the
  central server's loaded-module inventory. A PHP header probe succeeded, but a body relay would
  amend the binding static-site architecture and may contend for PHP workers during 31 source
  requests plus WASM. All probe/relay files were removed, staging was restored to the pushed static
  commit, and production remains untouched pending administrator-managed host/proxy headers or an
  explicit PHP-relay design exception.

## 2026-07-27 (branch peano-lab) — Peano Lab M15: replayable proof artifacts

- Added a session-owner replay journal aligned one-for-one with the surviving engine history.
  Successful explicit tacticals and `use` commands retain their complete accepted surface line;
  top-level `auto` records the primitive steps that undo actually exposes; required classical-mode
  transitions are reconstructed explicitly. Failed tactics, inspection, export requests, and undo
  itself never become proof steps, while undo removes the exact corresponding replay transaction.
- Added root command `script [download]`. During a proof it labels the replay `ACTIVE (not
  kernel-checked)` and never appends `qed`, even when all goals are closed. Only after the existing
  independent checker validates the certificate against the owner-held original theorem does the
  session retain a `CHECKED QED` artifact with a canonical final `qed`. Export failure is deliberately
  unable to invalidate a successful QED or leave an older artifact misattributed to the new theorem.
- Extended the worker response with a one-shot optional text payload. The page downloads only an
  exact, directly typed `script download`; quick/deep-link injection cannot trigger it. It validates
  LF-only structure, Unicode controls, size, the initial `pa prove`, and final-`qed` placement before
  creating fixed-name `peano-lab-proof.pa`, then removes the anchor and revokes the Blob URL. The
  static browser exports an inert replay program and has no path that mutates the checked library.
- Documented the artifact/library boundary across the binding design, README, construction book,
  vault, plan, diary, memory, and this journal. A replay is neither a certificate nor a library
  declaration: checked reuse still requires a closed reviewed statement, explicit earlier
  dependencies, an authored library script, cut elimination, tests, and independent rechecking.
- Local acceptance is green: Peano `657 passed`; Lambda `360 passed, 36 subtests passed`; the
  acceptance corpus generated 13,636 raw transitions and exported 13,631 unique rows; evaluator v2
  ran 32 kernel-judged attempts with baseline pass@8 `0.0`; release `a-f2054080fdc5` stages with
  exact manifests. The vault has 58 notes/298 resolved links and no disconnected concept notes.
  Browser-shell harnesses cover one-shot routing, direct intent, malformed payload rejection, exact
  bytes, fixed filename, and cleanup. No in-app browser was attached, so no direct click observation
  is claimed. The warning-free full book build covers all 25 sources, and its executable gate
  replays 193 deep links plus 160 commands in 32 session blocks. Publication status is recorded only
  after the staging gate.
- Published milestone commit `f40b2ad` to the public `peano-lab` branch and deployed the identical
  static assembly to `/peano-lab-next/`. Staging returns build `2026-07-27j` with application release
  `a-f2054080fdc5`; the live page (`2d0640fa970e…`), application manifest (`f2054080fdc5…`), worker
  (`bdd011c29ffe…`), and proof UI (`183647c91883…`) match local files byte-for-byte, and WASM
  negotiates gzip. The full delivery gate stops at the inherited M14 condition: HTML still lacks
  `Cache-Control: no-store`, and the versioned manifest still lacks an immutable policy. Production
  was not touched and remains build `2026-07-27h`.

## 2026-07-28 (branch peano-lab) — Peano Lab M16: named local reasoning

- Fixed the user-facing contract at the exact line-oriented forms `have h : P` and
  `suffices h : P`. `have` schedules `Γ ⊢ P` before the old target under `h : P`; `suffices`
  schedules those two obligations in the opposite order. Names must be fresh, and propositions
  may use only rigid term variables already visible in the focused goal.
- Kept the trusted language unchanged. The partial engine certificate may carry
  `LocalHave(P, proof, body)` or `LocalSuffices(P, body, proof)` solely to keep visible goal order
  identical to left-to-right hole order. Before kernel validation, an untrusted capture-avoiding
  pass substitutes the local proof into its body and removes these administrative nodes.
- Recorded the soundness boundary in the binding design, milestone plan, README, construction
  chapter, implementation diary, project memory, journal, and connected Obsidian vault. QED still
  checks an ordinary compiled certificate from the empty context against the independently retained
  original theorem; a compiler defect can only make that check fail.
- M16 is locally green: 29 focused local-reasoning tests; the independently checked readable parity
  replay and mutated-target rejection; Peano 691; Lambda 360 plus 36 subtests; 13,344 regenerated
  corpus transitions from 1,692 checked sessions; a warning-free 25-source book; 193 deep links and
  170 commands in 34 blocks; and 59 vault notes/318 resolved links/0 disconnected concepts. The
  exact local stage is build `2026-07-28a`, application `a-f6c33c7840ad`, with the unchanged vendor
  release `v-85fb3352e49c`; the kernel has no diff and its checker remains 234 lines. No in-app
  browser was attached, so direct clicking is not claimed. Nothing was deployed: production and
  staging remain untouched, and the independent M14 cache-header stop still governs promotion.

## 2026-07-28 (branch peano-lab) — Peano Lab M17: multiline proof paste

- Specified one bounded replay path for both an accessible **Paste multiline proof** dialog and a
  direct multiline paste into the terminal. Ignoring blanks, input must begin with `pa prove ` and
  end with the exact line `qed`; the batch limit is 100,000 characters, 256 nonblank lines, and the
  existing `MAX_INPUT` on every line.
- Chose sequential rather than batch-atomic execution. Each line goes through the existing session
  driver, the first failure stops the suffix, successful prefix commands remain, and ordinary undo
  granularity stays one successful proof command at a time.
- Kept browser authority narrow: pasted `script download` can never initiate a download. A pasted
  final `qed`, however, follows precisely the normal owner-held path to the unchanged independent
  checker and original theorem.
- Implemented one preflight/parser and sequential executor for both routes, plus a Python-to-worker
  structured failure bit so JavaScript does not guess from terminal prose. Unsafe controls,
  malformed envelopes, duplicate/early proof boundaries, resource excess, inspection/rollback,
  stale worker generations, and download payloads are all rejected or rendered powerless.
- Verified synthetic terminal-paste events, dialog bounds and focus restoration, worker status,
  strict one-at-a-time scheduling, failure-stop behavior, repeated undo, and the readable parity
  replay's independently checked QED. Focused coverage reports 23 passed; Peano reports 698; Lambda
  reports 360 plus 36 subtests. The warning-as-error 25-source book, 193 links/34 blocks/170
  commands, and 60-note/335-link vault are green. The 13,344-transition/1,692-session corpus and
  kernel are unchanged; `checker.py` remains 234 lines.
- Refreshed exact local staging to build `2026-07-28b`, application `a-404fdbdb55e4`, vendor
  `v-85fb3352e49c`. No in-app browser was attached, so a visual click-through is not claimed. No
  remote deployment was attempted; production and staging remain untouched.

## 2026-07-28 (branch peano-lab) — M17 staging published; production gate held

- On owner authorization, deployed the exact green M17 assembly to `/peano-lab-next/`. The remote
  HTML reports build `2026-07-28b` and application `a-404fdbdb55e4`; fetched application manifest,
  worker, and driver bytes match the local stage exactly, and the multiline-paste control is present.
- The mandatory delivery verifier failed at the first HTTP policy assertion. LOL-ng returns neither
  `Cache-Control: no-store` on HTML nor the required immutable cache header on the versioned worker,
  despite the deployed `.htaccess`. This confirms the still-open administrator/proxy M14 blocker.
- Did not promote the red delivery to production. `/peano-lab/` remains build `2026-07-27h`; the
  new feature can be tried on staging while the host configuration is corrected.

## 2026-07-28 (branch peano-lab) — Peano Lab M18: compact arithmetic locally complete

- Measured the exact recurrence-normal parity replay after local-cut compilation: its eighteen
  proof tactics produce a 30,030-node ordinary certificate. The first generic `ring` grows the
  partial tree from 35 to 18,651 nodes and the second from 18,654 to 30,016. This is valid evidence,
  but unnecessarily general evidence for the particular PA recurrence.
- Fixed the new surface at `compact_arith` and `compact_arith [h, <- k]`. Version 1 closes only a
  rigid equality and uses only the explicitly listed local equalities, in order and orientation. It
  does not infer the outer parity invariant, induction variable, or witnesses.
- Kept the kernel contract unchanged. The phase-1 engine design memoizes a finite grammar of
  PA3--PA6 equality paths and seeded, independently checked induction templates, measures the
  expanded cut-normal tree, checks the exact focused judgment before commit, and leaves the
  original-target QED check in place.
- Added the construction chapter and connected design/plan/README/vault/memory surfaces. They
  contrast the generic 30,030-node elaboration with the existing checked 180-node/depth-34 artifact
  and state the honest result: 180 is a best-known upper bound, not a global-minimality proof.
- Implemented endpoint-bearing equality fragments and locally checked composition for symmetry,
  transitivity, congruence, and equality substitution. The review pass also made the 256-node input
  cap aggregate, extended the five-second deadline across state preflight/publication, and converted
  malformed state, proof, term, clock, and host-recursion paths into typed transactional failures.
- Local acceptance is green: focused M18 `46 passed`; Peano `744 passed`; Lambda `360 passed, 36
  subtests passed`; exact parity QED at 180 nodes/depth 34 and byte identity; warning-as-error
  26-source book; 193 links/170 replayed commands in 34 blocks; 61-note/356-link connected vault;
  and a reproducible 13,344-transition corpus from 1,692 checked sessions fingerprinting 31 sources.
  Application/vendor manifests and exact local staging are green at `a-953fa3777cd4`/
  `v-85fb3352e49c`, build `2026-07-28c`; the kernel is unchanged at 234 checker lines. Worker and
  multiline-paste behavioral harnesses pass. No in-app browser was attached, so live Pyodide
  behavior is not claimed. M18 was not deployed; staging remains M17 and production remains
  `2026-07-27h` behind the M14 cache-header blocker.

## 2026-07-28 (branch peano-lab) — M18 staging published

- On owner authorization, published the unchanged, pushed M18 candidate `98ee0dd` to
  `/peano-lab-next/`. The live pointer now reports build `2026-07-28c`, application
  `a-953fa3777cd4`; its HTML SHA-256 is byte-identical to local staging and an rsync checksum audit
  found no difference across all 41 application files. Worker-boot and multiline-paste behavioral
  harnesses remain green after publication.
- The full delivery verifier stopped at the pre-existing M14 policy failure: the host returned no
  `Cache-Control: no-store` header for HTML. No in-app browser was attached, so no live Pyodide
  click-through is claimed. Production was not touched and remains build `2026-07-27h`.

## 2026-07-28 (branch peano-lab) — Peano Lab M19: compact checked runner and training groundwork

- Chose a compact adapter rather than a compact replacement prover. `peano_lab.batch` starts fresh
  proof owners in one warm Python process but reuses the browser formula parser, public tactic
  compiler, immutable proof state, theorem replay, binding trace logger, checked finalizer, and
  independent kernel. The finite transactional JSONL wrapper separates raw trace bytes from compact
  result envelopes and withholds them until EOF and complete trace commit; it has explicit
  aggregate input, request, result, and trace ceilings and is not a duplex service.
- Added runner-owned capability profiles. The first model environment has one fixed command/theorem
  preimage, rejects `auto`, `undo`, session commands, and held-out target imports, and fingerprints
  the complete authority in data and evaluation. Capability checking compiles every tactical leaf,
  including dead alternatives, so a nested tactic cannot smuggle a forbidden theorem or command.
- Added strict resource and transaction boundaries: bounded UTF-8/JSONL requests, formula numerals,
  tactical compilation, live certificates, and a 16 MB per-proof encoded trace ceiling. Traced and
  quiet modes retain identical kernel acceptance and proof size; quiet verification is explicitly
  barred from producing training data.
- Built the first proof-first policy pipeline. Eighteen authored public-surface scripts produce 58
  positive transitions across 11 pedagogical families. The compiler retains only complete QED
  sessions, replays every exact action/state under its declared environment, assigns genealogy
  components before row expansion, renders input focus zero to avoid action leakage, and binds the
  complete semantic Python source tree and runtime.
- Added repository-owned prompt/training/evaluation code for pinned Qwen3 1.7B and controlled 4B
  comparisons, completion-only BF16 LoRA, streaming hash-checked samples, immutable run/resume
  identity, trained-adapter provenance, and authority-preflighted kernel evaluation. Guarded Helios
  sync/probe/prepare/train/evaluate wrappers default to scheduler test-only; a real submission needs
  an explicit confirmation token.
- At this groundwork checkpoint the focused headless/trace/surface/dataset/evaluator/training/Helios
  suite reported 316 passes. This was infrastructure evidence only: no checkpoint had been
  downloaded or trained, no Slurm job had been submitted, and the scaled curriculum recorded in
  the next entry had not yet landed. M19 was not complete or deployed.

## 2026-07-28 (branch peano-lab) — Peano Lab M19: first attested 10,000-row release

- Expanded the proof-first corpus from the 18-session fixture to 2,522 independently
  kernel-checked sessions, roots, and unique canonical statements. Twenty-nine schemas cover five
  domains—logic, equality, PA recurrence, witnesses, and arithmetic—and stop on exactly 10,000
  positive next-tactic rows.
- Froze deterministic train/validation/test splits of 8,149/926/925 rows. The aggregate dataset
  SHA-256 is
  `1fa98caa2e0528d39c1b9003c4ee153dfbe633cb1ee4505e8f5b28eb837465dd`, and the frozen held-out
  contamination scan reports zero target occurrences.
- Hardened splitting against dishonest or accidentally incomplete genealogy. Sessions sharing a
  family, lineage, exact canonical theorem formula, or exact rendered policy prompt now occupy one
  connected component before transitions become rows. The prompt edge prevents two different
  theorems that reach the same model input from crossing the boundary; the independent attestor
  rejects both formula and prompt intersections across splits.
- Added an independent pre-training rebuild gate. It verifies raw trace/metadata hashes, the current
  compiler and semantic source inventory, the fixed `model-v1` environment, split hashes, and the
  held-out contract, then recompiles in a fresh directory. The released train, validation, and test
  files reproduce byte-for-byte.
- Closed the model-loader provenance boundary. Adapter and tokenizer outputs use separate closed
  directories whose manifests cover every loader-visible regular file; loading rejects symlinks,
  additions, omissions, or mutations. Trained evaluation derives the exact policy environment from
  the embedded dataset attestation instead of substituting a hard-coded capability set.
- A second adapter/transport audit found no false-QED route but did find false-row and operational
  ambiguities. Success is now bound to replay and engine-history transactions, failure diagnostics
  must match the raised error, and result goals reuse trace metavariable aliases. JSON integers and
  total batch storage are bounded, floats are rejected, the CLI is explicitly finite rather than
  duplex, cancellation propagates, directory entries are synced, and `--require-proved` supplies
  strict CI exit semantics.
- This completes the first scaled data/provenance gate only. No model has been trained or evaluated,
  no learned pass rate is available, and no Helios result is claimed.
- Final pre-training infrastructure gates after the final audit: 363 focused tests, 912 complete
  Peano tests, 360 Lambda tests plus 36 subtests, a clean Jupyter Book build, and successful replay
  of 193 documented links / 34 command sessions. Local browser staging is
  `2026-07-28f` / `a-69aa3b753965`; it is not deployed. Refreshing the historical M9 corpus source
  fingerprint regenerated the same 13,344-transition/1,692-QED shape under the current source.

## 2026-07-28 (branch peano-lab) — M19: first Helios environment correction

- Synced and submitted the initial guarded prepare/train/evaluate dependency chain. Preparation job
  `20029189` failed in 21 seconds before model loading because `torch` was absent from the isolated
  environment. Slurm correctly prevented both downstream jobs from running; canceled exact stale
  jobs `20029217` and `20029237`.
- Read-only module inspection established the distinction the first recipe missed:
  `ML-bundle/25.10` loads CUDA 12.9.1 and advertises an ARM wheel repository, but does not install a
  Torch distribution. The repository contains the CPython-3.13/aarch64 wheel
  `torch-2.9.1+cu129`.
- Corrected preparation to recreate an isolated venv, install Torch and a fully pinned transitive
  closure with binary-only/no-resolution flags, and run `pip check` before the costly LoRA smoke.
  PyPI metadata inspection confirmed every non-Torch pin has a Python-3.13 ARM wheel. A new Helios
  job result is still pending; no checkpoint or solve rate is claimed. Scheduled jobs now replace
  inherited `PYTHONPATH`, disable the user site, and assert the exact Torch/CUDA build as well.
- Corrected local gates: 41 focused tests; Peano 912; Lambda 360 plus 36 subtests; warning-as-error
  27-source book; 193 links and 170 replayed commands in 34 sessions. Independent replay retained
  the exact split/dataset hashes and refreshed only the source-bound attestation to
  `5a3b172627d15a1f5dfa303c3acdcf02e9673039a239385ef8c5d8d57b238e0a`.

## 2026-07-28 (branch peano-lab) — M19: Helios smoke passed; WMI A100 path opened

- Replacement preparation job `20029964` completed in 1m31s from exact clean commit `41683e2`.
  It loaded Python 3.13.5 and `torch==2.9.1+cu129` on one GH200, matched the pinned Qwen3-1.7B
  model/tokenizer revision, completed a BF16 LoRA update, saved and hashed the adapter/tokenizer,
  reloaded them, and reported finite training/reload losses. Training `20029970` remains queued and
  evaluation `20029980` remains dependency-blocked; no learned solve rate is claimed.
- Restored VPN access made WMI live inspection possible. The owner belongs to `hw_csi`; partition
  `gpu_csi` exposes node `g3n1` with four A100 80GB GPUs, 880GB RAM, and non-preemptible jobs up to
  three days. Its lower-tier spot work is scheduler-requeueable.
- Added a read-only five-minute probe requesting one typed A100. It installs nothing and asserts
  the site's central x86-64 Python-3.12/PyTorch-2.5.1/CUDA-12.4 runtime, exactly one visible A100,
  at least 75 GiB VRAM, BF16 support, and a finite matrix forward/backward pass. The Helios ARM lock
  is explicitly not portable to WMI; a separate pinned overlay follows only after this gate passes.
- First execution `171366` reached the correct A100 and failed safely after nine seconds during
  Conda activation: the central MKL hook reads an unset `MKL_INTERFACE_LAYER` while the caller has
  Bash `nounset` enabled. The probe now suspends `nounset` only while sourcing and activating the
  administrator-owned Conda hooks, then immediately restores strict mode. No package or model was
  installed by the failed diagnostic.

## 2026-07-28 (branch peano-lab) — M19: WMI A100 probe passed and training boundary closed

- Corrected WMI probe `171369` completed in 13 seconds on one A100-SXM4-80GB. It verified Python
  3.12.12, Torch 2.5.1/CUDA 12.4, driver 610.43.02, 80GB VRAM, BF16, one visible device, finite
  forward/backward work, outbound model/package access, and 18 TB free storage.
- Added a canonical central-base manifest (including `ensurepip==25.0.1` and 23 package versions)
  plus a separate 12-wheel SHA-256 overlay. Content-addressed WMI releases verify all central and
  overlay install roots and refuse a stale current pointer.
- Reworked sync/submission as one fail-closed deployment protocol: clean tracked Git archives,
  remote Git-tree reconstruction, shared/exclusive source locks, provenance invalidation before
  mutation, chain-wide scheduler checks, predecessor/report validation, helper+job composite
  hashes, held submission until ledger durability, and pointer publication only after the full
  model smoke.
- WMI's Torch 2.5.1 path is one-shot. Base and adapter loading and Trainer weight saving are
  safetensors-only; PEFT pickle fallbacks are rejected; any earlier run output prevents a retry
  before data attestation. Python optimization cannot erase runtime checks, and failures inside
  environment-ID command substitutions propagate explicitly.
- The combined WMI/runtime/training focused gate reports 96 passes. No WMI LoRA preparation,
  training, or evaluation job has yet been submitted from this code, and no learned solve-rate
  claim is made.

## 2026-07-28 (branch peano-lab) — M19: a trained policy can attempt a new theorem without becoming an oracle

- Extended the trained evaluator from four frozen goal names to one caller-supplied bounded closed
  PA formula. The formula is rejected before model loading if it is open, malformed, multiline,
  control-bearing, numerically excessive, or structurally too deep. Its original parsed meaning is
  retained; canonical printer output must round-trip to the same AST.
- A rollout still reaches `proof` only through original-target kernel finalization. Publication
  then selects the smallest checked attempt and replays its exact tactics from a fresh state under
  the attested intuitionistic `model-v1` authority. Only matching theorem, environment, command
  count, proof nodes, and a second kernel QED can emit pasteable `.pa`.
- Closed the operational boundaries exposed by arbitrary input: finite decode values, composed
  call/token budgets, manifest-byte and closed adapter/tokenizer rechecks before publication,
  source/job identity rechecks, exclusive non-overwriting outputs below `results/`, and no writes
  into source or model artifact trees.
- Added the actual WMI user route. A local wrapper creates nonce-bearing canonical request JSON,
  streams it under the deployment lock, and submits only its SHA-256 ID. The guarded controller
  validates the request and durably joins request/job hashes before releasing an allowlisted A100
  job. Digest-named report, optional proof, and terminal summary distinguish `no-proof` from an
  infrastructure failure.
- Current gates: 139 focused policy/request/WMI/runtime tests and 1,029 complete Peano tests pass;
  Lambda Lab remains 360 tests plus 36 subtests. No WMI model preparation/training/evaluation or
  arbitrary theorem inference has yet run from this source, so no learned result is claimed.

## 2026-07-28 (branch peano-lab) — WMI preparation fails closed on a readonly export collision

- Clean commit `0ad12bc` was published to WMI with its reconstructed Git tree. Preparation job
  `171391` acquired the intended A100 and failed in 12 seconds before dependency installation,
  model loading, or training.
- The fixed central-prefix constant was readonly in Bash, but two child-process invocations tried
  to assign that same shell name in their temporary environment. Bash rejected the assignment;
  the Python verifier consequently saw no exported value and aborted.
- The child processes now receive `PEANO_WMI_EXPECTED_CENTRAL_PREFIX`, derived only from the same
  readonly constant. An executable shell regression covers both manifest and overlay-runtime
  verifier invocations. The corrected gate reports 139 focused and 1,029 complete Peano tests.

## 2026-07-28 (branch peano-lab) — WMI preparation passes; empty TSV fields become explicit data

- Replacement preparation `171395` completed in 8m39s on A100 node `g3n1`. It reproduced dataset
  digest `1fa98caa…` with 8,149/926/925 rows, verified Python 3.12.12 and Torch 2.5.1/CUDA 12.4,
  and saved/reloaded a 3,211,264-parameter LoRA adapter with finite losses 6.06434 and 5.53506.
- The guarded training dry-run passed, but real submission stopped before `sbatch` with a chain
  mismatch. Diagnosis found Bash's whitespace `IFS` collapsing the preparation row's empty
  `dependency_job_id`, shifting every later field. The hash and literal ledger row were correct.
- Replaced that parse with a size-bounded, strict UTF-8, exactly-nine-field TSV verifier that
  preserves empty data and rejects duplicate, malformed, or differently sourced predecessors.
  Because this changes the source commit, `171395` cannot be reused under the fix: a new prepare
  must establish the next chain. Current gates are 140 focused and 1,030 complete Peano tests.

## 2026-07-28 (branch peano-lab) — Helios trained; proof quality still unmeasured

- Accounting showed that queued Helios training `20029970` completed all 100 steps in 9m51s on a
  GH200. The immutable manifest records train loss 0.78446 and final teacher-forced validation loss
  0.13518 over 2,048/256 examples. This is evidence of distribution fitting, not theorem solving.
- Evaluator `20029980` failed after three seconds before generation. `write_manifest(sort_keys=True)`
  correctly serialized nested capability keys lexically, but `attested_training_environment`
  incorrectly reused the construction-order parser required for raw policy rows.
- The manifest boundary now validates the exact three-key set, reconstructs its semantic record,
  and retains all value sorting, uniqueness, environment-preimage/hash, fixed-authority, and raw-row
  order checks. WMI preparation `171404` was canceled after 1m56s once this universal evaluator
  defect was known. Independent CPython-3.10 replay preserved every dataset/split/source-artifact
  hash and changed only the attestor source identity; the refreshed attestation is
  `e4b319a0…`. A fresh safe chain is required; no kernel-judged solve rate is claimed.

## 2026-07-28 (branch peano-lab) — WMI gives the first honest trained-policy result

- Fresh preparation `171414` completed in 7m28s from exact clean commit `0c84fc3`. It reproduced
  dataset digest `1fa98caa…`, revalidated the content-addressed Python 3.12/Torch 2.5.1/CUDA 12.4
  runtime, and passed the A100 BF16 LoRA save/reload gate.
- Dependent job `171421` completed 100 optimizer steps in 11m40s. Training itself took 246.38s;
  the immutable manifest `ad16e60d…` binds adapter `ff187542…`, 2,048/256 examples, train loss
  0.78301, and final teacher-forced validation loss 0.13615. The final loader-visible adapter
  contains only safetensors, JSON, and README files; Trainer resume checkpoints remain outside that
  closed inference root and are never loaded by the WMI prover.
- Kernel-judged evaluator `171423` then ran successfully rather than failing at infrastructure.
  All 16 sampled trajectories failed before QED: 0/4 held-out goals, pass@4 0.0. The model often
  chose the right opening `intro` sequence but then invented unavailable Lean tactics, malformed
  multi-name commands, or selected a tactic for the wrong goal shape.
- Arbitrary request `171428` found no proof of `∀ x. ∃ y. x · (x + 1) = 2 · y` in 16 samples;
  fifteen samples proposed unsupported division as the witness. A second, exact-formula-unseen
  direct-witness theorem succeeded once in eight samples under `171430`. Its exported four-line
  proof was replayed independently to a seven-node kernel-checked certificate.
- The immediate known experimental deficiency is the curriculum, not an established parameter-count
  limit. The 8,149-row train split
  has zero actions headed by `induction`, `simp`, `have`, `suffices`, `specialize`, or `use`, while
  the frozen benchmark includes induction-requiring goals and otherwise needs missing lemma-use and
  composition patterns along known model-v1 routes of 10–23 lines. This stops the conditional 4B
  comparison. The next experiment will be a separately hashed `model-v2` with a frozen lemma
  snapshot, balanced induction/lemma-use curricula, and a sealed evaluation library; model-v1 is
  preserved as the negative baseline.
- Compatibility-checked a separately maintained candidate library against the current Peano source
  and import boundary. Its detailed identifiers and validation record remain outside this public
  checkout. No source or metadata was copied; publication versus a content-addressed external
  snapshot remains an explicit owner decision.
- Result-recording gate: 1,033 Peano tests passed; Lambda passed 360 tests plus 36 subtests; the
  clean 27-source Jupyter Book build passed with warnings as errors; 193 deep links and 170 commands
  replayed; the 66-note vault resolved all 412 wikilinks. `checker.py` remains unchanged at 234
  lines, and no Peano training, evaluator, or deployment job remains active.

## 2026-07-28 (branch agent/general-arithmetic-library) — M20 foundational corpus begins

- Isolated the work in a clean clone based on `origin/peano-lab` because the owner's active Peano
  checkout contains unrelated M19 changes. The publication target is a draft pull request back to
  `peano-lab`; no merge or deployment is authorized by this milestone.
- Reframed the modulus-five exercise as one client of a general dependency graph. Added 28 reusable
  theorem entries—equality congruence, additive cancellation and zero-sum, basic order endpoints,
  zero-product/nonzero-product and small-factor reasoning, divisibility witness algebra,
  constructive non-divisibility, and modulus-independent residue transport—for a total of 51.
  The last four additions are `add_eq_zero_left`, `mul_ne_zero`,
  `two_large_factors_impossible`, and `prime_two`; the last is the first checked instance of the
  fully expanded prime predicate. All replay to closed certificates under the unchanged kernel;
  the largest new entry is 1,601 nodes/depth 59 and fits the live import budget.
- Built a strict 75-node research catalog spanning equality, addition, multiplication, order,
  divisibility, congruence, relational gcd/coprimality, primes, and factorization: 23
  `checked_existing`, 28 `checked_m20`, 20 `planned_expressible`, and four
  `blocked_by_language`. Its validator enforces exact runtime coverage for all checked claims,
  closed production-parser formulas, ordered dependencies, source references, and explicit
  representation blockers.
- Audited the requested NNG4, Macbeth, and Weissman resources at pinned revisions. NNG4 has no
  active prime corpus; Macbeth's arithmetic sources are all-rights-reserved/reference-only; the
  Weissman notebooks are GPL-3.0 and stay external. The TeX search additionally pinned Open Logic,
  Newstead's open proof/number-theory text, and Stein's unlicensed Springer-associated source tree.
  No external prose, code, notebook, or TeX was copied; Peano proofs were constructed independently.
- Added deterministic catalog/metrics/dependency artifacts, a dedicated seven-chapter Jupyter Book
  part, an arithmetic Obsidian MOC and concept graph, and 51 generated per-lemma notes carrying exact
  dependencies, dependents, and proof metrics. Memory, plan, root maps, and reproduction commands
  now point to the same canonical theorem names.
- After integrating upstream result-recording commit `5576f99`, the combined gate passed 1,045
  Peano tests under both Python 3.10 and Python 3.12, a warning-as-error Jupyter Book build over 34
  sources, 197 deep links, 43 documentation blocks with 253 replayed commands, and the
  128-note/874-link vault check. Draft pull request
  [#1](https://github.com/nasqret/vietnam2026/pull/1) targets `peano-lab`; nothing was merged or
  deployed. FTA remains honestly `blocked_by_language` until a finite-factorization representation
  is reviewed and checked.
- Closed an inherited Python-version gap in the batch CLI by replacing recursion-limit-dependent
  JSON behavior with an explicit iterative 256-container nesting check shared by decoding and
  deterministic session hashing. The exact boundary and first rejected depth have regression
  coverage; the complete 1,045-test suite passes on both locally available runtimes.
- Added the requested full FTA as a separately trusted Lean companion rather than disguising an
  external theorem as a Peano axiom. `ArithmeticFTA.fundamental_theorem_of_arithmetic` constructs a
  finite prime list for every nonzero natural and proves every other prime list with the same
  product is a permutation. Lean 4.23.0 and Mathlib commit
  `37df177aaa770670452312393d4e84aaad56e7b6` are pinned; the verifier rejects `sorryAx` and requires
  exactly `propext`, `Classical.choice`, and `Quot.sound`.
- Completed the Peano representation decision: sorted Gödel-β factor codes, a β-coded prefix-product
  trace, the cataloged factor-pair primality schema, and extensional decoded-value uniqueness
  preserve the unchanged PA kernel. The research catalog now binds one checked companion artifact
  while keeping all 51 Peano
  claims under their existing certificate authority; the still-missing division/CRT/prime/Euclid
  proof spine is not mislabeled as checked.
- Post-FTA integration validation passed 1,049 Peano tests under both Python 3.10 and Python 3.12,
  the warning-as-error 34-source Jupyter Book, 197 deep links and 253 replayed commands, the
  75-node catalog plus one companion artifact, all 51 generated Peano snapshots, the exact Lean FTA
  theorem-type and axiom audit, and the 129-note/884-link Obsidian graph.

  These totals describe the M20 branch snapshot, not a post-merge catalog count.

## 2026-07-28 (branch peano-lab) — public modular catalog and model-v1 failure diagnosis

- The owner authorized publication of the previously external catalog. Integrated its 26 exact
  dependency-ordered `TheoremSpec` records after the existing 23 entries, with source commit
  `d2ba05dca952e2e33479923433f8d2fcd3409493`, catalog SHA-256 `91c88c1f…`, retained source
  validation report, and exact MIT notice.
- All 26 entries replay to deterministic closed certificates and pass the independent kernel in the
  empty context. The maximum is `mod5_fourth_power_one` at 21,515 nodes/depth 66. Raised only the
  untrusted import-certificate ceiling from 4,096 to 32,768; kernel code and proof rules are
  unchanged, and two capstone imports still exceed the separate live-partial bound.
- The exact short live route `intro n; intro h; use ...; apply ...; exact h; qed` passes. Its open
  cut reaches 21,523 nodes/depth 69 and normalizes back to the 21,515-node certificate; a mutated
  `+ 2` target is rejected.
- Audited why model-v1 scored 0/4 despite low validation loss. It consumed only 1,600/8,149 rows,
  has no induction/IH/order/lemma-use support, learns from 1--7-step scripts while reference routes
  need 10--23, sees every validation schema in train, and receives no grammar or lemma statements.
  Sixty percent of 40 attempts died on surface-incompatible text, and the evaluator has no retry or
  frontier.
- An explicit-import full-surface audit yields 474 prospective model-v2 checked transitions but
  only one induction label. Naive append-and-rerun would expose that label with only about 18.6%
  probability under the old sampler.
  Model-v2 therefore requires balanced 100k--150k checked transitions, content-bound retrieval,
  sealed family splits, 32-step oracle coverage, pretrained baselines, and bounded best-first
  search before any larger-model comparison.
- Local integration gates: 1,036 Peano tests; Lambda 360 tests plus 36 subtests; 27/27 book sources
  under warning-as-error; 193 deep links and 170 commands replayed; 414/414 wikilinks across 67
  vault notes; immutable browser candidate `2026-07-28g`/`a-3ea7b7142aa0`. Automated worker boot
  passes, but no in-app browser was attached, so direct Pyodide capstone latency is not claimed.
  `checker.py` has no diff and remains 234 lines.
- Split the optional all-ladder corpus smoke from generated variants and bound each ladder `auto`
  plumbing attempt to depth/node one. The former shared depth-five/5,000-node configuration was
  impractical on the new long statements and was stopped. The corrected target finishes in about
  three seconds: 803 unique transitions, 98 sessions, and 49 kernel-checked authored-script QEDs.

  These totals describe the upstream public-catalog snapshot; the resolved catalog and refreshed
  gates own any later combined count.

## 2026-07-28 — M20 and public modular catalog reconciled

- Merged the advanced `peano-lab` base at `567d9ae` into draft PR #1.
  Exact structural comparison found fourteen post-core `TheoremSpec` records
  common to both branches; every statement, dependency list, tactic script,
  and summary matched. A guarded union preserves all 26 imported records for
  provenance, exposes 63 unique runtime theorems, and rejects incompatible
  same-name definitions.
- Extended the arithmetic research DAG to 87 nodes: 23 baseline checked, 40
  post-baseline checked, 20 planned expressible, and four language-blocked.
  The published modular catalog now has its own immutable MIT source-register
  entry, while the Lean FTA companion remains separately checked and grants no
  Peano theorem authority.
- Regenerated the 63-certificate snapshot, 63 generated lemma notes,
  deterministic 13,344-transition proof corpus, and application manifest from
  the reconciled source tree. The vault now has 141 notes and 988 resolved
  links; local browser build `2026-07-28i` has content identity
  `a-8bbb61d1e7ba`. Nothing was deployed.
- The combined validation passes 1,054 Peano tests on both Python 3.10 and
  Python 3.12, all 360 Lambda tests, the warning-as-error 34-source Jupyter
  Book, 198 deep links and 44 sessions/260 replayed commands, the exact
  87-node catalog/runtime contract, all artifact and vault drift checks, and
  the Lean FTA theorem-type/axiom audit.

## 2026-07-28 — Native order and division milestone

- Extended the runtime from 63 to 104 independently checked theorems without
  changing the term language, formula language, kernel, or logic mode. The 41
  new entries fill discrete order, additive and multiplicative monotonicity,
  nonzero multiplication cancellation, and the constructive division layer.
- Proved `division_remainder_exists` by ordinary induction on the dividend.
  Its checked certificate has 196 nodes/depth 37 and constructs explicit
  quotient, remainder, equality, and strict-bound witnesses for every nonzero
  divisor.
- Proved the separate `division_remainder_unique` theorem. Totality splits the
  quotient gap into zero/successor cases; the zero case cancels the common
  block and the successor case contradicts the smaller strict remainder bound.
  The certificate has 1,442 nodes/depth 47 and needs no redundant nonzero
  premise because a strict bound already excludes a zero divisor.
- Added zero-remainder/divisibility bridges and reusable block-bound helpers.
  The accepted uniqueness proof directly uses `add_left_cancel` and
  `positive_quotient_gap_impossible`; the latter transitively uses
  `lt_not_eq_add_middle`. `remainder_bound_step`, `division_block_upper`, and
  `remainder_unique_same_quotient` remain checked leaf helpers for later APIs.
  This route avoided a roughly 30,000-node algebraic prototype.
- Expanded the research DAG to 120 nodes: 23 baseline checked, 81
  post-baseline checked, 12 planned expressible, and four language-blocked.
  Regenerated the 104-certificate snapshot and 104 lemma pages; the Obsidian
  graph now has 182 notes and 1,281 resolved links. The largest certificate
  remains the prior modulo-five capstone at 21,515 nodes/depth 66.
- The complete Peano suite passes 1,054 tests on Python 3.10. The 34-source
  Jupyter Book builds without warnings; 199 deep links and 45 session blocks
  containing 264 commands replay cleanly. Catalog/runtime equality, generated
  artifact drift, corpus provenance, application identity, and all 1,281 vault
  links are current. Cross-runtime and wider repository gates remain before
  publication.

## 2026-07-28 — Relational gcd and coprimality foundation

- Extended the unchanged-kernel runtime from 104 to 119 checked theorems. The
  fifteen new entries prove factor-one rigidity, divisors of one, divisor
  bounds, mutual-divisibility antisymmetry, the relational `IsGCD` symmetry and
  projection API, a constructor for the one-input-divides-the-other case,
  coprimality/unit bridges, and `is_gcd_unique`.
- Made the left-associated `IsGCD` representation explicit as
  `(g|a /\ g|b) /\ forall c ...` in every checked statement and catalog
  endpoint. This preserves the parsed formulas while removing an ambiguity
  for readers and proof-generating models.
- Fresh-process replay, empty-context checking, dependency-removal trials, and
  PA6-to-PA5 mutation tests all pass. Every new theorem is constructive. The
  largest is `is_gcd_unique` at 600 nodes/depth 51; the overall maximum remains
  `mod5_fourth_power_one` at 21,515/depth 66.
- Expanded the research catalog to 132 nodes: 23 baseline checked, 96
  post-baseline checked, nine planned expressible, and four interface-blocked.
  Regenerated 119 certificate records and 119 theorem notes; the Obsidian graph
  now has 197 notes and 1,409 resolved links.
- Recorded the next clean-room arithmetic construction in
  `research/arithmetic-library/gcd-bezout-roadmap.md`. Prototype certificates
  already validate subtraction-free remainder divisibility, both directions
  of Euclidean gcd invariance, and the balanced-combination maximality bridge.
  The bounded gcd-existence script checks in dependency-curried form (90
  nodes), but the current capture-sensitive dependency inliner corrupts the
  closed tree; gcd existence is therefore not admitted.
- The full Peano suite remains green at 1,054 tests on Python 3.10. The
  35-source Jupyter Book and 264 documented commands remain green. The
  deterministic 13,344-transition/1,692-session corpus was provenance-refreshed,
  and local browser candidate `2026-07-28k` has immutable application identity
  `a-c62e02aa4600`. Nothing was deployed.

## 2026-07-28 — Native Euclidean gcd invariance

- Extended the unchanged-kernel runtime from 119 to 125 checked theorems. The
  six additions prove a subtraction-free factor-difference lemma, both
  directions of divisibility transport across `a = b*q+r`, the `gcd(a,0)`
  base case, and both directions of relational Euclidean gcd invariance.
- Fresh replay and empty-context kernel checking pass for all six certificates,
  with no classical `DNE`. Dependency-removal trials show every declared edge
  is used; PA6-to-PA5 and hypothesis-index mutations are rejected. The two
  Euclidean invariance certificates each have 586 nodes/depth 51 and require
  neither a remainder bound nor a nonzero-divisor premise.
- Expanded the synchronized research catalog to 138 nodes: 23 baseline
  checked, 102 post-baseline checked, nine planned expressible, and four
  language-blocked. The planned gcd-existence node now records the actual
  bounded-induction route through division, the zero base case, and checked
  Euclidean invariance rather than its obsolete divisibility-only sketch.
- Relational gcd existence remains deliberately unadmitted. Its 90-node
  dependency-curried prototype closes, but dependency substitution currently
  corrupts the closed induction certificate. That engineering gate motivates
  the next separately reviewed, conservatively erasable proof-sharing
  milestone; it is not a new axiom and is not part of this arithmetic commit.
- Regenerated the deterministic 13,344-transition/1,692-session corpus against
  the 125-theorem source authority. Local browser candidate `2026-07-28l` has
  immutable application identity `a-baf4cc52dad6`; nothing was deployed.
- The complete Peano suite passes 1,054 tests on Python 3.10. A clean
  warning-as-error Jupyter Book build passes over 35 sources, and 199 deep
  links plus 45 session blocks containing 264 commands replay successfully.
  Snapshot, catalog, corpus, vault, and application-manifest drift checks are
  all green.

## 2026-07-28 — Self-contained proof sharing removes the gcd composition gate

- Added the reviewed certificate constructor `Cut(A,B,lemma,body)`. The
  independent checker verifies `lemma : A` in the ambient context and verifies
  `body : B` with `A` as hypothesis zero, using the same intuitionistic or
  explicitly classical mode in both branches. The node contains both formulas
  and both proof branches; it contains no theorem name, hash, declaration
  environment, or callback.
- This is an explicit enlargement of the trusted proof grammar and checker,
  from 234 to 247 lines. It does not add a term former, predicate, axiom,
  induction principle, or classical rule. Exact-constructor, malformed-node,
  annotation, branch-mutation, context-order, binder-capture, metavariable,
  focused-goal, and transactional-limit tests cover the new boundary.
- Library replay now wraps dependency-curried bodies in nested Cuts, and live
  `use` embeds the rechecked closed certificate in a Cut around the focused
  goal. Engine-only `LocalHave` and `LocalSuffices` still compile away. The
  untrusted `erase_trusted_cuts` diagnostic expands the mathematical
  `(lambda h. body) lemma` form, but is deliberately non-authoritative and
  cannot operationally round-trip every introduction-headed or
  induction-bearing certificate through the current bidirectional
  checker/reducer.
- All 125 theorems replay deterministically and check from the empty context.
  The shared snapshot has 31,479 structural proof nodes and 741 Cuts across 86
  entries. `mod5_fourth_power_one` is largest by nodes at 2,675/depth 38;
  `division_remainder_unique` supplies the ladder's maximum depth of 57. The
  immutable upstream modulo-five report remains unchanged at the former fully
  expanded 21,515-node/depth-66 capstone.
- The previously rejected bounded gcd-existence prototype now passes at 1,232
  nodes/depth 44, and its general `forall a b` wrapper passes at 1,268/depth
  46. Neither is admitted in this trust-boundary commit; they are the next
  separately reviewed arithmetic milestone.
- Acceptance is green at 1,081 Peano tests, 360 Lambda tests plus 36 subtests,
  a warning-as-error 36-source Jupyter Book, 199 deep links and 45 sessions/264
  replayed commands, and a 204-note/1,511-link Obsidian graph. Snapshot-v2,
  the 138-node research catalog, the refreshed 13,344-transition/1,692-session
  corpus, the 2,446-transition/250-session all-ladder smoke with 125 checked
  authored QEDs, the Lean FTA audit, and application manifest
  `2026-07-28m`/`a-396c35f357b4` are current. The clean clone lacks the large
  untracked vendor mirror, so a full static stage assembly was not claimed.
  Nothing was deployed.

## 2026-07-28 — Constructive relational gcd existence

- Admitted `gcd_exists_up_to` by ordinary induction on an explicit bound for
  the second input. The zero branch constructs `IsGCD(a,a,0)` directly; the
  equality branch obtains `a = b*q+r` from checked division, recursively finds
  a gcd of `(b,r)`, and transports it through `is_gcd_euclid_forward`; the
  strictly smaller branch reuses the induction hypothesis unchanged.
- Derived `gcd_exists_relational` by specializing the bounded theorem at
  `B=b` and discharging `b <= b` with `le_refl`. Both statements are ordinary
  expanded first-order PA formulas. They add no gcd function, choice
  principle, classical `DNE`, new axiom, or new induction rule.
- Independent admission tests fix the exact formulas and ordered dependencies,
  replay twice from a cold cache, check the closed certificates from the empty
  context, reject PA-axiom and hypothesis-index mutations, remove each of the
  eight dependency slots in turn, and complete a public live `use` session.
  The bounded theorem is 1,232 nodes/depth 44; the unrestricted theorem is
  1,268/depth 46.
- The runtime now has 127 theorems: 23 baseline, 92 general foundational, and
  twelve unique modular capstones. Its shared certificates total 33,979 nodes
  and 814 Cuts across 88 entries. The largest and deepest entries remain
  unchanged (`mod5_fourth_power_one`, 2,675 nodes; maximum depth 57).
- Synchronized the research DAG at 139 nodes: 23 baseline checked, 104 M20
  checked, eight planned expressible, and four language-blocked. Regenerated
  the 127-record snapshot, 127 generated lemma notes, 206-note/1,547-link
  Obsidian graph, source-bound 13,344-transition corpus, and browser candidate
  `2026-07-28n` / `a-2099b556a7d3`. The all-ladder smoke exported 2,545 unique
  transitions from 254 sessions and obtained all 127 authored kernel QEDs.
- Acceptance passes 1,086 Peano tests on CPython 3.10, Lambda's 360 tests plus
  36 subtests, the warning-as-error 36-source book, 199 deep links and 45
  sessions/264 commands, generated-artifact and application-manifest drift,
  corpus provenance, and the pinned Lean FTA exact-axiom audit. Nothing was
  merged or deployed. The next mathematical gate is subtraction-free balanced
  Bézout, followed by Gauss cancellation and the general prime spine.

## 2026-07-28 — Balanced Bézout, Gauss cancellation, and Euclid's lemma

- Added ten closed native theorems that carry the relational-gcd construction
  through four-natural balanced Bézout witnesses, scale those witnesses,
  extract divisibility of the balanced result, specialize to coprime inputs,
  prove Gauss cancellation, characterize a divisor of a prime as one or the
  prime, and conclude Euclid's lemma. Every relation remains a fully expanded
  first-order PA formula; no integer type, gcd function, prime predicate,
  choice principle, classical `DNE`, or hidden theorem authority was added.
- The bounded simultaneous construction proves, by ordinary induction on an
  explicit upper bound, both `IsGCD(d,a,b)` and
  `a*xp + b*yp = d + (a*xn + b*yn)`. Across a Euclidean step
  `a=b*q+r`, it transports coefficients by
  `(xp',yp',xn',yn')=(yp,xp+q*yn,yn,xn+q*yp)`. The greatest-divisor clause is
  transported separately with `is_gcd_euclid_forward`; it is not inferred
  from the balanced equation.
- `gauss_coprime_cancel` scales a result-one equation and applies the checked
  common-divisor bridge. `euclid_prime_dvd_product` takes a relational gcd of
  `p` and `a`, uses `prime_divisor_eq_one_or_self` to split that gcd into the
  unit or prime case, then invokes Gauss or the gcd divisibility projection.
  The final certificates are 3,800 nodes/depth 51 for Gauss, 57/depth 12 for
  the prime-divisor API, and 5,382/depth 55 for Euclid.
- Independent admission tests pin all ten statements, scripts, dependency
  orders, certificate hashes, metrics, and Cut counts; cold replay is
  deterministic, every dependency slot is necessary, PA/hypothesis mutations
  are rejected, all certificates check from the empty context, and live
  theorem use closes. The runtime is now 137 theorems and the catalog 148
  nodes: 23 baseline checked, 114 post-baseline checked, seven planned, and
  four language-blocked.
- Regenerated the 137-record certificate snapshot (52,433 structural nodes,
  1,345 Cuts across 98 entries), 137 lemma pages, 216-note/1,696-link Obsidian
  graph, 13,344-transition/1,692-session leakage-safe corpus, and the isolated
  3,007-transition/274-session ladder smoke with all 137 authored kernel QEDs.
  Local browser candidate `2026-07-28p` has content identity
  `a-48059fcca9d3`; the clean checkout lacks the untracked vendor mirror, so no
  static staging or deployment is claimed.
- Acceptance passes 1,090 Peano tests on CPython 3.10, Lambda's 360 tests plus
  36 subtests, the warning-as-error 36-source Jupyter Book, 199 deep links and
  45 session blocks containing 264 replayed commands, catalog/snapshot/vault/
  corpus/application drift checks, and the arithmetic knowledge-base audit.
  Native Peano FTA remains unclaimed: the next arithmetic gate is constructive
  prime-divisor existence, followed by β-coded finite prefixes and products.

## 2026-07-29 — Constructive prime search and prime-divisor existence

- Added twelve closed native rungs: `eq_decidable`,
  `multiple_decidable_nonzero`, `multiple_decidable`,
  `factor_property_succ`, `factor_search_up_to`, `prime_or_composite`,
  `prime_nonzero`, `prime_decidable`, `factor_nonzero_left`,
  `proper_factor_lt`, `prime_divisor_exists_up_to`, and
  `prime_divisor_exists`. All statements remain fully expanded formulas over
  the existing PA term language; no primitive divisibility or prime predicate,
  choice rule, or hidden theorem authority was introduced.
- The constructive route decides equality first, decides nonzero-divisor
  divisibility through quotient/remainder existence and uniqueness, and then
  performs ordinary induction on an explicit factor bound. The bounded search
  either proves every factorization below the bound has a unit factor or
  returns a nonunit factor pair. This yields prime/composite and prime
  decisions without converting double negation into a witness.
- `proper_factor_lt` turns a nontrivial factorization into strict descent.
  `prime_divisor_exists_up_to` inducts on an explicit upper bound: a prime
  input is its own divisor; a composite input descends to a proper factor,
  recursively obtains its prime divisor, and lifts divisibility by
  transitivity. `prime_divisor_exists` specializes that theorem at the
  reflexive bound. Constructive prime search and prime-divisor existence are
  therefore complete native milestones.
- The runtime now contains 149 unique checked theorems: 23 baseline, 114
  general foundational, and twelve unique modulo-five capstones. The
  synchronized catalog has 158 nodes: 23 `checked_existing`, 126
  `checked_m20`, five planned, and four language-blocked. Shared certificates
  total 67,844 structural nodes and 1,800 Cuts across 109 Cut-bearing entries.
  `euclid_prime_dvd_product` remains largest at 5,382 nodes and has the maximum
  159 Cuts; `prime_divisor_exists` reaches the maximum depth of 80.
- Regenerated the leakage-safe corpus with unchanged semantic counts: 13,344
  transitions from 1,692 sessions, split 13,326/18 train/validation. Its new
  source-bound run fingerprint is
  `a470b1b751a1d291462da9249713713bd7430922c1002a77dfd64ae8e3072d0e`.
  The isolated ladder smoke has 298 sessions, 3,549 raw and 3,546 unique
  transitions, and all 149 authored-script kernel QEDs.
- The full Peano suite passes 1,094 tests on CPython 3.10; Lambda passes 360
  tests plus 36 subtests; all 36 book sources build with warnings as errors;
  201 deep links and 45 session blocks containing 264 commands verify. The
  arithmetic knowledge base, 228-note/1,890-link vault, snapshot, corpus,
  application-manifest, and pinned Lean FTA exact-axiom gates are green.
  Local browser build `2026-07-29a` has immutable content identity
  `a-d0758315633d`; it is not staged, deployed, or promoted.
- Native Peano FTA remains absent: the next mathematical and representation
  gates are greatest-prime descent and the β/CRT/finite-product spine needed
  for canonical encoded factorizations.

## 2026-07-29 — Balanced congruence and functional Gödel-β decoding

- Added seven closed native theorems. `mod_eq_trans` composes the balanced
  witness relation `a + m*u = b + m*v`; `mod_eq_add` combines two such
  relations under addition. Neither theorem introduces subtraction, integers,
  or a primitive congruence predicate.
- Added the first five checked Gödel-β rungs:
  `beta_modulus_nonzero`, `beta_at_self_of_bound`, `beta_at_exists`,
  `beta_at_unique`, and `beta_at_exists_unique`. The decoding relation remains
  fully expanded as a bound plus quotient witness for the remainder of `b`
  modulo `S ((S i) * c)`, namely `1 + (i + 1)c`. Its modulus is
  constructively nonzero because it is a successor; checked division supplies
  a decoded value and quotient/remainder uniqueness supplies functionality.
- The runtime now contains 156 unique checked theorems: 23 baseline, 121
  general foundational, and twelve unique modulo-five capstones. The
  synchronized catalog has 163 nodes: 23 `checked_existing`, 133
  `checked_m20`, three planned, and four language-blocked. Shared certificates
  total 71,762 structural nodes and 1,911 Cuts across 116 Cut-bearing entries.
  `euclid_prime_dvd_product` remains largest at 5,382 nodes and has the maximum
  159 Cuts; `prime_divisor_exists` retains the maximum depth of 80.
- This closes β-value totality and functionality, not finite-sequence coding.
  Binary and bounded CRT, finite-prefix extension/restriction, prefix-product
  traces, and finite-product laws remain open, as does greatest-prime descent.
  Native Peano FTA therefore remains absent.
- Regenerated the source-bound corpus without changing its semantic shape:
  13,344 transitions from 1,692 sessions under run fingerprint
  `40f8380b27d38f93b8f965ea13ebe22d89dcd16cdf18f364f162b806f1fb5f38`.
  The isolated acceptance smoke has 312 sessions, 3,769 raw and 3,766 unique
  transitions, and all 156 authored-script kernel QEDs.
- The complete Peano suite passes 1,098 tests on CPython 3.10. The generated
  vault has 235 notes and 1,979 resolved links, including all 156 lemma notes.
  The warning-as-error 36-source book has 203 checked deep links and 45 session
  blocks whose 264 commands replay cleanly.
  Local browser build `2026-07-29b` has immutable application identity
  `a-e2678d4819b0`; it is not staged, deployed, or promoted.

## 2026-07-29 — Multiplicative congruence and the pre-CRT bridge

- Added five closed native theorems. `mod_eq_mul_right` and
  `mod_eq_mul_left` preserve balanced natural congruence under one-sided
  scaling; `mod_eq_mul` combines two congruences into a product congruence.
  Together with the preceding transitivity and addition theorems, the balanced
  relation now has its full additive/multiplicative compatibility layer.
- `remainder_decomposition_to_mod_eq` converts a directed equation
  `b = q*m + x` into the subtraction-free balanced relation between `b` and
  `x` modulo `m`. `beta_at_to_mod_eq` projects the quotient witness from the
  fully expanded β-decoding relation and applies that bridge. No primitive
  modulus, quotient, remainder, congruence, or β function was introduced.
- The runtime now contains 161 unique checked theorems: 23 baseline, 126
  general foundational, and twelve unique modulo-five capstones. The
  synchronized catalog has 168 nodes: 23 `checked_existing`, 138
  `checked_m20`, three planned, and four language-blocked. Shared certificates
  total 75,170 structural nodes and 2,009 Cuts across 121 Cut-bearing entries.
  The maxima remain 5,382 nodes and 159 Cuts at
  `euclid_prime_dvd_product`, and depth 80 at `prime_divisor_exists`.
- This is a pre-CRT interface, not CRT itself. Bounded representative
  uniqueness, binary/bounded CRT, finite-prefix extension, prefix-product
  traces, greatest-prime descent, and native FTA remain open.
- Regenerated the source-bound corpus with the same 13,344-transition/
  1,692-session semantic shape under run fingerprint
  `4e864236c001f37cc93c3e12208afd9072829a4e0a4b7fa008908e48f1e23e5c`.
  The isolated smoke has 322 sessions, 3,902 raw and 3,899 unique transitions,
  and all 161 authored-script kernel QEDs. The generated vault has 240 notes
  and 2,037 resolved links, including all 161 lemma notes.
- The complete Peano suite passes 1,098 tests on CPython 3.10, including the
  28-test focused pre-CRT gate; Lambda passes 360 tests plus 36 subtests. The
  warning-as-error 36-source book
  has 205 checked deep links and 45 session blocks whose 264 commands replay
  cleanly. Local browser build `2026-07-29c`
  has immutable application identity `a-b71812244ce0`; it is not staged,
  deployed, or promoted.

## 2026-07-29 — Bounded congruence uniqueness and the reverse β bridge

- Added three closed native theorems. `mod_eq_bounded_unique` proves that two
  balanced-congruent representatives below the same modulus are equal.
  `mod_eq_to_remainder_decomposition` uses nonzeroness, the proposed value's
  bound, division, and that uniqueness result to reconstruct a directed
  equation `b = q*m + x`. This is the converse of the preceding
  `remainder_decomposition_to_mod_eq` bridge under exactly the conditions
  required of a remainder.
- `beta_at_of_mod_eq_bound` specializes the reverse bridge to the successor β
  modulus. Together with `beta_at_to_mod_eq`, it proves that the fully expanded
  `BetaAt(b,c,i,x)` relation is equivalent to the bound
  `x < 1 + (i+1)c` plus balanced congruence between `b` and `x` at that
  modulus. No quotient, remainder, modulus, congruence, or β primitive was
  added to the PA object language.
- The runtime now contains 164 unique checked theorems: 23 baseline, 129
  general foundational, and twelve unique modulo-five capstones. The
  synchronized catalog has 171 nodes: 23 `checked_existing`, 141
  `checked_m20`, three planned, and four language-blocked. Shared certificates
  total 79,763 structural nodes and 2,138 Cuts across 124 Cut-bearing entries.
  The maxima remain 5,382 nodes and 159 Cuts at
  `euclid_prime_dvd_product`, and depth 80 at `prime_divisor_exists`.
- This closes bounded representative uniqueness and the two-way decoding
  interface, not CRT or finite sequences. β-modulus coprimality,
  binary/bounded CRT, finite-prefix extension, prefix-product traces,
  greatest-prime descent, and native FTA remain open.
- Regenerated the source-bound corpus with the same 13,344-transition/
  1,692-session semantic shape under run fingerprint
  `6393629a4b2b1a6c51457d606e4cc73c8245d368f62ccfe1e8387291be9503d1`.
  The isolated smoke has 328 sessions, 4,016 raw and 4,013 unique transitions,
  and all 164 authored-script kernel QEDs. The generated vault has 243 notes
  and 2,082 resolved links, including all 164 lemma notes.
- The complete Peano suite passes 1,098 tests on CPython 3.10, including the
  28-test focused pre-CRT gate; Lambda passes 360 tests plus 36 subtests. The
  warning-as-error 36-source book has 207 checked deep links and 45 session
  blocks whose 264 commands replay cleanly. Local browser build
  `2026-07-29d` has immutable application identity `a-5cef5a9c3b7d`; it is not
  staged, deployed, or promoted.

## 2026-07-29 — Constructive binary CRT and the two-position β bridge

- Added six closed native theorems. `bezout_mod_left` and
  `bezout_mod_right` project the checked balanced-natural Bézout identity
  into its two modular inverse equations.
  `mod_eq_predecessor_cancel` implements subtraction of one modulo a
  successor using only natural addition and multiplication.
- `binary_crt` constructively produces one natural satisfying two
  balanced congruences for nonzero coprime moduli.
  `binary_crt_remainders` converts bounded requested residues to directed
  quotient/remainder equations. `binary_crt_beta_pair` specializes the
  result to one code realizing two bounded β values. The last theorem assumes
  pairwise coprimality of its two β moduli; it does not prove that premise or
  iterate over a finite prefix.
- The runtime now contains 170 unique checked theorems: 23 baseline, 135
  general foundational, and twelve unique modulo-five capstones. The
  synchronized 177-node catalog contains 23 `checked_existing`, 147
  `checked_m20`, three planned, and four language-blocked entries.
  Shared certificates total 99,137 structural nodes and 2,693 Cuts across 130
  Cut-bearing entries. `binary_crt_beta_pair` is largest at 6,941 nodes
  and 201 Cuts; `prime_divisor_exists` retains the maximum depth of 80.
  The ordered snapshot root is
  `51fbc86c80feb458dd6adcf1e08ee378e62f2f55e82fb8c6c5c9e9e0ab41a227`.
- This closes binary CRT and the two-position construction, not bounded CRT
  iteration or finite sequences. Greatest-prime descent, β-modulus
  coprimality, bounded CRT iteration, finite-prefix extension, prefix-product
  traces, finite-product laws, and native Peano FTA remain open.
- Regenerated the source-bound corpus without changing its semantic shape:
  13,344 transitions from 1,692 sessions under run fingerprint
  `53305cfb39ddbd6fb6e02280caf594b1937f95790539a2df6b713244f975445c`.
  The isolated smoke has 340 sessions, 4,474 raw and 4,471 unique transitions,
  and all 170 authored-script kernel QEDs.
- The complete Peano suite passes 1,098 tests on CPython 3.10; Lambda passes
  360 tests plus 36 subtests. The strict 36-source Jupyter Book has 213 checked
  deep links and 45 session blocks whose 264 commands replay cleanly. The
  generated vault has 249 notes and 2,194 resolved links, including all 170
  lemma notes. Local browser build `2026-07-29e` has immutable application
  identity `a-ac494e524f2f`; it is not staged, deployed, or promoted.

## 2026-07-29 — Conditional β-modulus coprimality and bounded common multiples

- Corrected the finite-prefix strategy: arbitrary Gödel-β moduli are not
  pairwise coprime. For `c=1`, indices 1 and 4 yield moduli 3 and 6,
  sharing divisor 3. No theorem or roadmap now treats that false statement as
  an open goal.
- Added six closed native theorems.
  `beta_modulus_coprime_base` proves every β-shaped successor modulus
  coprime to `c`.
  `common_divisor_beta_moduli_divides_gap_times_c` controls a common
  divisor at ordered indices `j=i+gap`.
  `beta_moduli_coprime_of_gap_dvd` derives coprimality when
  `gap | c`, and `binary_crt_beta_pair_of_gap_dvd` discharges
  the existing two-position CRT premise.
  `bounded_common_multiple_step` and
  `bounded_common_multiple_exists` construct a nonzero `c`
  divisible by every positive natural through a fixed bound.
- The six shared certificates have respectively 874/24/depth 30,
  855/24/depth 30, 6,007/175/depth 56, 12,980/378/depth 71,
  483/15/depth 29, and 640/22/depth 30 nodes/Cuts/depth.
  Deterministic replay, empty-context checking, PA1–PA6-only axiom audits,
  dependency necessity, mutation rejection, and live/edge checks are green.
- The runtime now contains 176 unique checked theorems: 23 baseline, 141
  general foundational, and twelve fixed modular capstones. The synchronized
  183-node catalog contains 23 `checked_existing`, 153
  `checked_m20`, three planned, and four language-blocked entries.
  Shared certificates total 120,976 structural nodes and 3,331 Cuts across 136
  Cut-bearing entries. `binary_crt_beta_pair_of_gap_dvd` is largest at
  12,980 nodes/378 Cuts; `prime_divisor_exists` retains maximum depth
  80. The ordered root is
  `874779f25de06cebc9d111e76bd183e4a8c514bd0d9da0c52f71c99f887cc3a7`.
- Regenerated the 13,344-transition/1,692-session corpus under run fingerprint
  `f44b6eb716116063bd24b849d737345f0c9c23240fa8536d1ed25fdc1ae05d56`.
  The isolated smoke has 352 sessions, 4,729 raw and 4,726 unique transitions,
  and all 176 authored-script QEDs. The complete Peano suite passes 1,098 tests
  on CPython 3.10.
- Local browser build `2026-07-29f` has immutable application identity
  `a-72e034c621a7`. It is not staged, deployed, or promoted.
  The remaining native FTA path requires greatest-prime descent, index-bound
  finite-prefix glue, product-modulus CRT iteration, prefix products,
  factorization existence/uniqueness, and the final native FTA theorem.

## 2026-07-29 — Bounded-prefix β coprimality and CRT fold algebra

- Added seven closed native theorems.
  `beta_moduli_coprime_of_lt_bounded_common_multiple` handles ordered
  bounded indices; `beta_moduli_pairwise_coprime_bounded` handles both
  orders; and `bounded_beta_moduli_pairwise_coprime_exists` packages a
  nonzero base whose distinct β moduli through a chosen bound are pairwise
  coprime.
  `coprime_mul_left` and `coprime_mul_right` preserve that
  invariant under products. `mod_eq_of_mod_eq_multiple` descends
  congruence from an accumulated product modulus, and
  `binary_crt_fold_step` proves one binary CRT extension preserves all
  old congruences whose moduli divide that product.
- Their audited nodes/depth/Cuts are respectively 6,227/57/181,
  6,348/59/183, 7,019/61/207, 3,975/53/115, 4,017/54/117,
  157/23/3, and 5,501/52/156. Cold replay is deterministic and checks from the
  empty context; all fifteen dependency-slot mutations, PA-leaf mutations,
  and authored-hypothesis mutations fail closed. No DNE occurs, only PA1–PA6
  are used, and the runtime records exactly match both temporary prototypes
  after erasing `_proto`.
- The runtime now contains 183 unique checked theorems: 23 baseline, 148
  general foundational, and twelve fixed modular capstones. The synchronized
  190-node catalog contains 23 `checked_existing`, 160
  `checked_m20`, three planned, and four language-blocked entries.
  Shared certificates total 154,220 structural nodes and 4,293 Cuts across 143
  Cut-bearing entries. `binary_crt_beta_pair_of_gap_dvd` remains
  largest at 12,980 nodes/378 Cuts; `prime_divisor_exists` retains
  maximum depth 80. The ordered root is
  `09359430226349a7d5fdd1fd67376d345bc1bb5f707e746e8b58c2799086f2d6`.
- Regenerated the 13,344-transition/1,692-session corpus under run fingerprint
  `d0649a05ab1a88396d2d3046bc10a814e374cb3cf5ad8df225c9e15e91ff0df6`.
  Train, validation, statistics, manifest, and raw-stream SHA-256 values are
  respectively
  `d39720bfeeeb159d0f8ca9f331294b6c6135ea36f0585b46efa0768945f953bb`,
  `d8986e2b260907c909ed1c2b0926fd02a9aa0df748a37656bcdf820c591299fd`,
  `2bfd4d68ed205d67e0aedf6acb349cfdc7880adcc3b0cf2f41be557b2cee6c58`,
  `5c50e4afd0e41272ed8781e7d43bf6d4c985a2eee11b1c33953f016b8f808211`,
  and `ee804b6a6ff0b497df192806a99bc6d975d775a84879189aa1251178aa865556`.
  The isolated smoke has 366 sessions, 4,992 raw and 4,989 unique transitions,
  and all 183 authored-script QEDs. The complete Peano suite passes 1,098 tests
  on CPython 3.10 in 127.22 seconds; Lambda passes 360 tests plus 36 subtests.
- The generated Obsidian graph verifies at 262 notes and 2,397 resolved links,
  including all 183 lemma notes.
- Local browser build `2026-07-29g` has immutable application identity
  `a-6b72d4fe4ca4`. It is not staged, deployed, or promoted.
  The next representation gate is the actual bounded fold with an encoded
  accumulated-product/solution invariant, followed by β finite-prefix
  recoding, prefix products, factorization, and native FTA.
