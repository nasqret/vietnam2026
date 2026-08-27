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
- A GPT Pro adversarial review found and closed a Python subclass/equality forgery: the trusted checker now
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

## 2026-07-29 — Bounded β-CRT prefix invariant for an existing code

- Added six closed native theorems. `right_factor_divides_product` supplies the
  explicit divisibility witness needed by the product invariant.
  `beta_accumulated_product_step` advances nonzeroness, earlier-modulus
  divisibility, and future coprimality;
  `beta_crt_prefix_congruence_step` advances congruence with values already
  decoded from a supplied β code; and `beta_crt_prefix_invariant_step`
  combines the two successor steps. `bounded_beta_crt_prefix_invariant` folds
  that invariant by ordinary induction, while
  `bounded_beta_crt_for_existing_code` projects its congruence witness.
- Their audited nodes/depth/Cuts are respectively 229/25/7,
  11,174/69/330, 7,352/64/213, 18,613/70/545, 25,496/78/752, and
  25,545/79/755. Two cache-cleared empty-context replays were deterministic;
  all 31 individual dependency-slot mutations, every first-PA mutation, and
  every authored-body hypothesis mutation failed closed. No DNE occurs, only
  PA1–PA6 are used, and all six live `use`/`exact`/`qed` checks pass.
- The runtime now contains 189 unique checked theorems: 23 baseline, 154
  general foundational, and twelve fixed modular capstones. The synchronized
  196-node catalog contains 23 `checked_existing`, 166 `checked_m20`, three
  planned, and four language-blocked entries. Shared certificates total
  242,629 structural nodes and 6,895 Cuts across 149 Cut-bearing entries.
  `bounded_beta_crt_for_existing_code` sets both maxima at 25,545 nodes and
  755 Cuts; `prime_divisor_exists` retains maximum depth 80. The ordered root
  is `9650ae53f506c282daf84fca5e9c08d0d48bb36db813b4efc43f54156d25bf6b`.
- The complete current Peano suite passes 1,098 tests on CPython 3.10 in
  181.34 seconds. The synchronized source-bound corpus has fingerprint
  `a3c2f8c5c762b10fc9c1117723c74fecb50348cfb699f73bc76fb3714df3bf1b`;
  its isolated smoke records 378 sessions, 5,373 raw transitions, 5,370 unique
  transitions, and all 189 authored QEDs. Local browser build `2026-07-29h`
  packages application `a-98b1d8bb8dd7` without claiming deployment. The
  Obsidian graph verifies all 189 generated lemma notes within 268 notes and
  2,513 resolved links.
- Honesty boundary: the wrapper begins with values already represented by an
  existing expanded `BetaAt` code. Extensionally that code itself is already a
  common congruence witness, so this is proof of the bounded fold invariant,
  not a theorem coding arbitrary finite sequences. Genuine prefix-product
  recurrence and bounds are the next representation gate, followed by the
  remaining recoding, factorization, and native FTA spine.

## 2026-07-29 — Native Gödel-β factorization and FTA

- Closed the former representation gate without changing Peano Lab's term or
  formula language. Thirteen recoding/product theorems establish bounded β
  finite-prefix recoding and exact prefix-product trace existence. The next
  layers prove Product functionality, zero/successor decomposition, transport,
  factor-prefix append, bounded `AllPrime`, adjacent sortedness, and their
  extension laws.
- Added canonical append, greatest-prime-divisor descent,
  factor-divides-Product, canonical-last-factor bounds, and the matching and
  cancellation prerequisites needed for uniqueness. Multiple β codes can
  decode the same finite prefix, so the final uniqueness statement compares
  lengths and decoded entries extensionally; it never asserts raw code
  equality.
- Checked `prime_factorization_existence` at 43,973 nodes/depth 98/1,328 Cuts
  and `prime_factorization_uniqueness` at 29,789/82/854. Their exact native
  conjunction, `fundamental_theorem_of_arithmetic`, checks at
  73,767/99/2,184 with certificate SHA-256
  `fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
  Empty-context replay, live `use`/`exact`/`qed`, semantic checks, all thirty
  dependency-slot mutations, PA-leaf mutation, and authored-hypothesis
  mutation pass. Only PA1–PA6 and induction occur; DNE does not.
- Aligned the untrusted `use` preflight with the existing live-proof ceiling:
  100,000 nodes and depth 256. Real 33,000-node composition and exact
  100,000/256 admission tests pass; 100,001/257 and repeated transactional
  failure tests reject. This changes resource policy, not the kernel or logic.
- Added checked `prime_three` and `two_prime_product_uniqueness`. The runtime
  now has 246 unique theorems; the 248-entry catalog contains 23 baseline
  checked, 223 M20 checked, one planned `prime_unbounded`, and one
  representation-blocked conventional integer-coefficient Bézout endpoint.
  Production remains untouched and the work stays on draft PR #1.
- Regenerated the source-bound snapshot: 977,939 structural nodes, 28,746
  Cuts, 203 Cut-bearing certificates, ordered root
  `ec31ca0a6eb822e00dc2f334b66b0878bf997ea0601068cc8d0639bfbb90d877`,
  and theorem-source digest
  `fde7888f2c8e66bd92ccc7cae05cfd146eacb873b830d1abaf2ca75e8063f56d`.
  Both snapshot and vault drift checks pass; the vault has 325 notes, 3,245
  resolved links, and all 246 generated lemma notes.
- Regenerated the 1,692-session/13,344-transition training corpus under run
  fingerprint
  `7b98ddcdb5220df4130b00ae79954ef3b45c6fa37f6a16e213bc2a73613c347b`.
  The isolated acceptance smoke has 492 sessions, 9,138 raw and 9,135 unique
  transitions, and all 246 authored-script QEDs. Local browser build
  `2026-07-29i` has manifest identity `a-0ec541ed8d13`; it is not staged,
  deployed, or promoted.
- Built the Jupyter Book strictly across all 36 sources with zero warnings or
  errors. The documentation gate verifies 234 deep links and 45 executable
  session blocks containing 264 commands; all ten static documentation tests
  pass.

## 2026-07-29 — Constructive prime unboundedness

- Added the native theorem `prime_unbounded`:
  `forall n. exists p. (exists k. k + S n = p) /\ Prime(p)`, with `Prime`
  fully expanded into the nonunit factor-pair formula. The proof first uses
  `bounded_common_multiple_exists` to obtain a nonzero `c` divisible by every
  positive natural at most `n`, then applies `prime_divisor_exists` to `S c`.
  If the resulting prime `p` were at most `n`, it would divide both `c` and
  `S c`; `divides_remainder` would make it divide one, and `divisor_one`
  would force `p = 1`, contradicting primality. Thus `n < p`.
- The exact certificate has 4,595 structural nodes, depth 82, 146
  self-contained Cuts, and SHA-256
  `8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b`.
  It checks from the exact catalog statement using PA1–PA6 only and no DNE.
  Every dependency-slot mutation, the PA-leaf mutation, and the authored-body
  hypothesis mutation fail closed; the live `use`/`exact`/`qed` route passes.
- The runtime now has 247 unique theorems: 23 baseline, 212 general
  foundational, and twelve fixed modular capstones. The 248-entry catalog has
  23 `checked_existing`, 224 `checked_m20`, no planned entries, and one
  representation-blocked conventional integer-coefficient Bézout interface.
  Balanced four-natural Bézout remains checked.
- Regenerated the 247-theorem snapshot at 982,534 nodes, 28,892 Cuts, and 204
  Cut-bearing certificates. Its ordered root is
  `eb4775dfd181dc5e45bec463a93f14b0ea9d02501c40c5167b7cae77cd4ff432`;
  the source digest is
  `295ca3b65970324e7d2ed51b57dc4510227b0abbc2d35b68a809dbde26aba868`.
  The synchronized vault has 327 notes, 3,287 resolved links, and all 247
  generated lemma notes.
- Regenerated the 1,692-session/13,344-transition corpus under fingerprint
  `5b41aae76a1980c768fdf815f1ffc531fa86ebcdecf9bfae39de2dceb608f81c`.
  Its isolated smoke has 494 sessions, 9,235 raw/9,232 unique transitions, and
  all 247 authored QEDs. Browser build `2026-07-29j` packages application
  `a-c983d7c60450`; it is not staged, deployed, or promoted. The strict book
  rebuild passes all 36 sources with zero warnings; 234 deep links and 45
  session blocks containing 264 commands verify.
- Closed the synchronized release gate with all 1,101 Peano tests passing on
  Python 3.10 in 1,050.08 seconds, with no failures or reported warnings.
  Snapshot, vault, corpus, documentation, and deployment-manifest drift checks
  are green. No in-app browser was attached, so direct Pyodide UI smoke is
  explicitly unclaimed; nothing was staged, deployed, promoted, or merged.

## 2026-07-29 — Interactive arithmetic Jupyter Book

- Replaced the arithmetic landing page's historical-first status report with
  a current 247-theorem dashboard, clickable ten-stage dependency metro map,
  role-specific reading routes, native FTA receipt, constructive
  `prime_unbounded` explanation, trust pipeline, and synchronized artifact
  links. The course introduction and Peano construction chapter now route
  readers directly into this part.
- Added a guided route from equality and discrete order through division,
  relational gcd, balanced Bézout, Gauss, Euclid, constructive prime search,
  bounded CRT, Gödel-β finite-prefix recoding, exact prefix-product traces,
  factorization existence/uniqueness, and FTA. It includes responsive HTML/CSS
  diagrams, two kernel-replayed proof sessions, expandable proof anatomy, and
  a browser-local progress checklist.
- Added `scripts/build_arithmetic_book_atlas.py`. It joins the checked snapshot
  and research catalog and deterministically generates a text-friendly atlas
  with all 247 exact statements and complete dependency-import/authored-script
  recipes, plus the one honest representation-boundary card. Each theorem has
  prerequisite and dependent links, certificate metrics/hash, copy controls,
  live Peano action, and source/vault/artifact links. Search, domain/status
  filters and a 1–4-hop neighborhood navigator use local zero-dependency JS;
  cards remain readable without JavaScript.
- Corrected two stale chapters that still described greatest-prime descent,
  prefix products and native FTA as missing, and aligned the mathematical TOC
  so gcd/Bézout precedes primes/Euclid.
- Jupyter Book 1.0 builds all 38 sources with warnings as errors and zero
  warnings. The real command gate verifies 194 deep links and 47 sessions with
  287 commands. Seventeen book tests, the atlas drift check, JavaScript syntax,
  built-HTML card/asset/anchor contracts and `git diff --check` pass. No in-app
  browser was attached, so a live visual/click interaction audit is explicitly
  unclaimed rather than substituted with another browser backend.

## 2026-07-29 — Constructive finite permutation completeness

- Added nineteen native β-prefix permutation theorems. The tranche proves
  finite occurrence decision, one-position recoding, interior/last swap,
  reverse pointwise reflection, and transport of boundedness, injectivity and
  surjectivity. Its endpoint `finite_bounded_injective_surjective` proves that
  every bounded injective decoded prefix is surjective onto the same finite
  interval by ordinary induction; no finite-set or function primitive was
  added.
- Two cold isolated replays and empty-context kernel checks pass for all
  nineteen theorems (`3 passed in 62.65s`). The swap constructor reaches
  31,742 structural occurrences, 4,832 distinct objects and depth 87. The
  finite-pigeonhole endpoint reaches 42,463 occurrences, 6,399 objects and
  depth 89. Neither contains `DNE`; both remain well below the
  500,000-occurrence/100,000-object/depth-256 policy, so no resource limit was
  raised.
- Canonical registry replay reproduces the endpoint metrics exactly, and the
  full stable-order/dependency test passes in 123.85 seconds. The runtime now
  contains 377 checked theorems. The synchronized research graph contains 378
  records: 23 baseline checked, 354 post-baseline checked, no planned record,
  and one language-blocked conventional integer-coefficient interface.
- Regenerated the deterministic snapshot at 1,780,721 structural occurrences,
  51,883 Cuts and 322 Cut-bearing certificates. Its ordered root is
  `6a489a2bfab7722d357bea5744d2d4f08faad1a00cf833e0b6c0ae93208f413a`.
  The global certificate maxima remain the earlier FTA endpoint, confirming
  that the existing resource policy has adequate measured headroom.
- Regenerated 377 Obsidian lemma notes; the full vault has 458 notes and 4,626
  resolved links. Regenerated the 377-card Jupyter Book theorem atlas and
  taught its source locator to recognize the reviewed dynamic small-modulus
  spec families without weakening literal-name checks for other modules.
  Product invariance under finite permutations is the next mathematical gate;
  Wilson, Fermat, Euler, Gauss and Eisenstein remain explicitly unproved.
- The strict Jupyter Book build passes all 39 sources with warnings as errors.
  The command verifier checks 194 deep links and 47 session blocks containing
  287 commands; every command replays cleanly. Atlas drift, catalog drift,
  dashboard counts, synchronized 8,192-character input bounds, and
  `git diff --check` are green.

## 2026-07-29 — Product replacement balance and swap invariance

- Added three native PA theorems in the isolated
  `finite_product_permutation_theorems.py` tranche. The reflection lemma
  classifies entries of a one-position replacement; the balance theorem proves
  `q * x = p * y` when one decoded factor changes from `x` to `y`; and
  `beta_product_swap_last_invariant` proves exact product equality after an
  interior/final transposition. These are expanded β and Product relations,
  not new list, product, or permutation primitives.
- Added the hygienic authoring helper `product_successor_relation`. It permits
  exactly the audited successor-length Product surface while retaining the
  identifier-only contract of `product_relation`; the helper and rejection
  boundary have dedicated tests.
- Two cold isolated replays pass for all three certificates, together with
  exact statement/dependency/hash receipts, empty-context kernel checks,
  no-`DNE` checks, capacity gates, and false-contract/Cut mutations. Exact
  metrics are 1,735 nodes/depth 62/1,011 objects for replacement reflection,
  4,780/66/1,552 for replacement balance, and 7,439/67/1,685 for swap-last
  invariance. No capacity limit was raised.
- Integrated the tranche after constructive finite permutation completeness.
  The runtime now contains 380 checked theorems and 1,017 dependency edges;
  the synchronized research graph has 381 records: 23 baseline checked, 357
  post-baseline checked, no planned catalog record, and one language-blocked
  conventional interface.
- Regenerated the deterministic snapshot at 1,794,675 structural occurrences,
  405,807 aggregate distinct objects, 52,266 Cuts, and 325 Cut-bearing
  certificates. The ordered root is
  `cd492e79c0dd69f65108653423c6df3ccc6efc2756306a14e1b3743afb83ba0e`;
  FTA remains the global maximum at 73,767 nodes, 8,701 objects and depth 99.
- Regenerated 380 lemma notes and the 380-card theorem atlas. The full Obsidian
  vault now has 461 notes and 4,693 resolved links. General invariance under an
  arbitrary bounded injective reindexing is still a separate unchecked gate;
  Wilson, Fermat, Euler, Gauss, Eisenstein, and quadratic reciprocity remain
  explicitly unproved.

## 2026-07-30 — WMI-only QR replay campaign

- Moved every heavy QR proof replay, capacity profile, mutation audit, and
  full-ladder regression off the authoring Mac. No QR replay process remains
  local; source inspection and text authoring are the only local activities.
- Submitted baseline WMI job `172707` on `cpu_idle` from immutable archive
  `e4a0ff3909b970438aba4dfbc952220c02a7be5d74232ca3af98aad2fcd3e10c`.
  It selects 22 gates covering the checked reindex-support and bounded-unit
  tranches, both isolated general-reindex candidates, dual capacity policy,
  adversarial mutations, and the complete public theorem ladder.
- Added an isolated three-rung Fermat candidate: range-entry normalization,
  pointwise product coprimality, and coprimality of the product
  `1*...*(p-1)` with `p`. The source is not registered and carries no theorem
  claim. Submitted WMI discovery job `172716` from immutable archive
  `27cf34986f0b7f0fd2f70d4c840c9fc4f7f5a8e49889c71a54db662327ede823`;
  its three candidate gates run before the broader integration suite.
- Both jobs were still `PENDING (Priority)` with zero CPU time at the latest
  check. Consequently there is no pass receipt to record and neither
  candidate tranche is admitted. If discovery passes, exact statement hashes,
  lengths, occurrences, depth, object/edge/reuse counts, and Cuts will be
  pinned before a distinct admission snapshot is submitted.
- Added isolated rungs 4 and 5, `beta_successor_lift_exists` and
  `prime_mul_index_map_exists_up_to`. The latter constructively divides each
  `a*S i` by the prime, excludes zero remainder with Euclid's lemma and the
  strict bound, stores the predecessor of the remainder, and extends the
  β-coded map. WMI discovery job `172722` uses snapshot
  `0d050e5d631a080bec41753438636047c257ca146c43be4f9382e8752a6caccd`.
  It too was `PENDING (Priority)` with zero CPU time; the two new theorems are
  isolated and unverified.
- Added the cluster workflow, honest status vocabulary, first readable
  candidate proof, and the eight-rung Fermat dependency table to the Jupyter
  Book and Obsidian MOC. No Book build was run locally; its build and link
  validation belong to a later WMI-backed integration gate.
- Added isolated rung 7, `beta_product_pointwise_scale_mod`, by simultaneous
  induction over two exact products and a relational power. Its successor
  step multiplies the prefix congruence by the final pointwise congruence and
  uses only checked semiring reassociation/commutation. Static review found no
  proof-shape error.
- Reworked its public authoring helper to allocate every pointwise bound,
  decoded-entry, and congruence binder in one capture-avoiding scope; product
  and power decomposition witnesses are generated hygienically as well.
  Superseded pending job `172734` was cancelled before using CPU. Replacement
  WMI job `172737` uses snapshot
  `08cb916fee48cfd5b2f4882052e5812c99f496f1f34e502dac61ea97d1c6c1c4`.
- Authored rung 6 as five isolated theorems rather than one brittle proof:
  `fermat_index_map_bounded`, `prime_mul_index_map_injective`,
  `beta_successor_range_reindex_aligned`,
  `beta_successor_range_scale_mod`, and the existential package
  `prime_mul_residue_reindex_exists`. Two independent static audits found and
  corrected malformed free-variable annotations before execution, then
  confirmed the cancellation and bounded-uniqueness route.
- Authored isolated rung 8, `prime_mul_residue_product_balance`. It constructs
  one exact target product, identifies it with the source product through the
  general bounded-injective reindex theorem, applies pointwise scale-product
  transport, and performs one reverse rewrite. Static audit found and fixed a
  missing conjunction destructuring; the patched alias flow was re-audited.
- Added named WMI suites so expensive discovery does not have to repeat the
  full integration ladder. Snapshot
  `c6e6cabbbaf8b617e8d42576828d8c10d75d166e59c3bd2c09dd27aab4328632`
  was scheduler-validated and submitted as focused jobs `172769`
  (`fermat-reindex`) and `172770` (`fermat-balance`). Both were pending at the
  recorded checkpoint. The source archive is shared and content-addressed;
  suite and job ID remain distinct receipt fields. No local Python or replay
  was run.
- Authored two isolated Fermat endpoint candidates. The predecessor-exponent
  theorem `fermat_predecessor_exponent_mod_one` obtains an exact factorial
  witness, invokes rung 8, proves the residue product coprime to the prime,
  normalizes the two products, and applies checked coprime modular
  cancellation. Its exact direct dependencies are `factorial_exists`, rung
  8 (`prime_mul_residue_product_balance`),
  `prime_range_product_coprime`, `prime_nonzero`,
  `mod_eq_cancel_coprime`, `mul_comm`, and `mul_one`.
- Authored the constructive all-input wrapper `fermat_little_all_inputs`.
  It derives a successor presentation of the prime, decomposes the successor
  power, and uses `prime_coprime_or_divides`: the coprime branch applies the
  predecessor endpoint and scales its congruence, while the divisible branch
  constructs divisibility witnesses for both sides. It has no classical
  case split and remains an isolated candidate.
- Added a dedicated five-gate `fermat-endpoints` WMI suite for exact contracts,
  helper hygiene, dependency topology, two cold replays with profiles, Cut
  spines, and false-contract/dependency mutations. Submitted discovery job
  `172837` from immutable snapshot
  `c7cc39f94b2cb0ae5542f89b3ddec947d84c55627168e07851c62da36f51bd34`
  on `cpu_idle` with 1 CPU, 32768 MiB, and `04:00:00`. It is queued/pending:
  there is no endpoint pass receipt or admission claim. At that
  endpoint-submission checkpoint, all seven submitted QR discovery jobs
  remained pending; no heavy work or Book build was run locally.
- Authored the isolated Wilson fixed-point candidate
  `prime_bounded_square_one_cases`. For positive `x`, it writes `x = S t`,
  normalizes `x*x = 1 + t*(t+2)`, cancels the balanced congruence witnesses to
  obtain `p | t*(t+2)`, and invokes `euclid_prime_dvd_product`. Divisor bounds
  then force `t=0` or `p=t+2`, yielding `x=1` or the prime predecessor. This
  uses no subtraction, integer type, classical case split, or `DNE`.
- Fixed its ordered direct boundary at exactly 16 checked dependencies:
  `ne_zero_of_one_le`, `nonzero_is_succ`, `mul_succ_left`, `add_assoc`, `add_comm`,
  `add_left_cancel`, `factor_difference`, `euclid_prime_dvd_product`,
  `le_succ_self`, `lt_of_le_of_lt`, `zero_or_succ`,
  `divisor_le_nonzero`, `lt_not_le`, `succ_ne_zero`, `le_antisymm`, and
  `succ_injective`.
- Added the focused five-gate `wilson-square-one` WMI suite for the expanded
  contract, helper hygiene, isolated dependency boundary, two cold profiled
  full-Cut replays, no-DNE/capacity checks, and contract/every-edge mutations.
  Submitted discovery job `172855` from immutable snapshot
  `396af02c5aa4fdf62d4c3484f8a2c711b03c489cad498c121d0402ce3ee79981`
  on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. It is queued/pending;
  no pass, pinned metrics, or admission is claimed, and no heavy work or Book
  build was run locally.
- Authored four isolated pointwise Wilson-inverse candidates. The zero-based
  relation `InvIdx(p,n,i,j)` stores `i<n`, `j<n`, and a balanced witness that
  residues `S i` and `S j` multiply to one modulo `p`. The dependency
  decomposition is: `prime_inverse_index_exists` from bounded prime inverse
  existence and successor-bound conversion; `bounded_mod_inverse_unique` from
  modular scaling/transitivity and bounded representative uniqueness;
  `bounded_inverse_index_unique` from raw uniqueness plus successor
  injectivity; and `inverse_index_symmetric` from multiplication commutativity.
- Authored three isolated β-prefix candidates. `prime_inverse_prefix_extend`
  appends the mate at `l` with `beta_prefix_extend` and splits `i<S l` into
  the last/old cases; `prime_inverse_prefix_exists_bounded` inducts over any
  `l≤n`; `prime_inverse_prefix_exists` specializes to the full length `n`.
  Their sources preserve the exact ordered dependency tuples recorded in the
  Fermat/Wilson design note and remain outside the public registry.
- Wired the five-gate `wilson-inverse-prefix` WMI suite. Its recursive source
  graph closes all seven candidates, and its gates cover exact helpers and
  contracts, dependency topology, two cold profiled full-Cut replays,
  no-DNE/capacity checks, and contract/every-live-edge mutations. Submitted
  discovery job `172899` from immutable snapshot
  `1a11442b18dd6c40b49975e16f0b2062be57fade347acca20d87dba27e6adffc`
  on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. It is queued/pending;
  no replay result, pinned metrics, pass, or admission is claimed.
- At that inverse-prefix checkpoint, the next Wilson blockers were an
  extensional involution theorem from β functionality/uniqueness/symmetry,
  treatment of the fixed residues `1` and
  `p-1` (including prime `2`), a β-coded deletion/reindex or exactly-two-fixed-
  points pairing theorem, and the final factorial-product bridge. No tests,
  proof replay, profiling, or Book build ran locally.
- Authored six isolated extensional inverse-map candidates:
  `inverse_prefix_entry_sound`, `inverse_prefix_extensional`,
  `inverse_prefix_involutive`, `inverse_prefix_injective`,
  `inverse_prefix_surjective`, and `prime_inverse_prefix_fixed_cases`.
  Soundness uses β uniqueness; extensionality uses bounded inverse-index
  uniqueness; symmetry and extensionality give involution; injection and
  surjection follow constructively. The first five theorems are prime-free.
  Only the fixed theorem assumes primality, and its exact zero-based conclusion
  is `i = 0 \/ S i = n`.
- Wired the five-gate `wilson-inverse-involution` suite, whose recursive source
  graph closes 14 isolated specs. Submitted discovery job `172920` from
  immutable snapshot
  `cfa4eea18d4a746a49a2d7579f217dbd65a27a79df61c76e8dba49079ba1aaa4`
  on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. It is queued/pending;
  no report, pinned metric set, pass, or admission is claimed. The remaining
  Wilson blockers are endpoint removal/exactly-two-fixed-points pairing,
  prime `2`, paired products, and the final factorial bridge. No local build,
  proof replay, profiling, or tests ran.
- Authored three isolated fixed-endpoint candidates for the full zero-based
  inverse prefix. `inverse_prefix_zero_fixed` builds the fixed entry for
  residue one; `inverse_prefix_last_fixed` uses
  `predecessor_square_mod_one` to fix the last index; and
  `prime_inverse_prefix_exact_endpoints` combines both entries with
  `prime_inverse_prefix_fixed_cases` to conclude that every fixed index is
  `0` or the last index. The contract is honest at prime `2`: its witness is
  `k=0`, so the two endpoint descriptions coincide and no distinctness is
  asserted.
- Added the focused five-gate `wilson-inverse-endpoints` WMI suite. Its
  recursive graph closes 17 isolated specs and audits exact contracts and
  ordered dependencies, helper/formula hygiene, graph/core isolation, two
  cold closed replays with hashes/RSS/no-DNE/capacity metadata, and a unique
  false contract plus every direct Cut-edge mutation. Local bounded checks
  were limited to syntax and the first three cheap gates, all of which passed;
  the heavy replay and mutation gates remain WMI-only.
- Submitted discovery job `172927` from exact snapshot
  `7083e3876cc54daa782153aa6e1a2554aa75fa5a40cce3d6cf6b5971979dc35d`
  on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. It is queued/pending
  only: there is no replay report, pass, pinned metric set, or admission. The
  runner now has seven focused suites and a 66-gate full audit. No local heavy
  Python, proof replay, mutation run, or Book build was started.
- Authored the first two isolated nonendpoint inverse-orbit candidates.
  `prime_inverse_prefix_nonendpoint_not_fixed` uses the existing fixed-case
  classification to show that a decoded mate of an explicitly nonendpoint
  source cannot equal that source. `prime_inverse_prefix_nonendpoint_mate`
  uses involution, prime successor shape, both decoded fixed endpoint entries,
  successor injectivity, and β uniqueness to show that the mate is also a
  nonendpoint. Both proofs are constructive. Their contracts make no endpoint-
  distinctness claim and do not manufacture a nonendpoint index at prime `2`,
  where the endpoint descriptions coincide.
- Added the focused five-gate `wilson-inverse-orbit` WMI suite. It recursively
  closes the square-one, point, prefix, involution, endpoint, and orbit layers:
  `1+4+3+6+3+2 = 19` isolated specs. The gates audit exact contracts and
  helper hygiene, the ordered dependency/core/source boundary, two cold closed
  replays with proof metrics/hashes/RSS/no-DNE/capacity receipts, and a unique
  false contract plus every direct Cut-edge mutation. Local work was limited
  to syntax and the first three cheap gates, all passing; both cold replays and
  adversarial mutations remain WMI-only.
- Submitted discovery job `172932` from exact snapshot
  `5463565294da6d757356985a0e8d353ad2e0e16ca1b21b99d2aa5cfa6bb5c6f6`
  on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. It is queued/pending
  only: there is no replay report, pass, pinned metric set, or admission. The
  runner now has eight focused suites and a 71-gate full audit. No local heavy
  Python, proof replay, profiling, mutation run, or Book build was started.
- Authored two isolated generic Wilson pair-product candidates.
  `beta_product_double_succ_decompose` derives a terminal two-factor
  decomposition from the checked one-step β-product decomposition.
  `beta_adjacent_unit_pairs_product_one` inducts over `m`: if every adjacent
  pair of a β-coded factor prefix is congruent to one modulo `p`, the exact
  product of its first `m+m` factors is congruent to one. Reindexing the
  nonendpoint inverse orbits into that adjacent layout and restoring the fixed
  endpoint factors remain separate.
- Two bounded replay corrections were made before the authoritative WMI
  submission. Snapshots for jobs `172936` and `172943` each exposed a separate
  missing third length rewrite; both jobs were cancelled before start as
  superseded known-broken snapshots and provide no evidence.
- The corrected focused `wilson-pair-product` suite has two specs and five
  gates: exact contracts, hygienic/canonical helper expansions, the ordered
  dependency/core/source boundary, two cold closed replays with hashes/RSS/
  no-DNE/capacity receipts, and false-contract plus every direct Cut mutation.
  All five gates passed locally in 5.4 seconds. Exact metrics were 1,317 nodes,
  depth 63, and 844 objects for `beta_product_double_succ_decompose`; and 4,372
  nodes, depth 64, and 1,290 objects for
  `beta_adjacent_unit_pairs_product_one`. The deterministic graph hash is
  `622496753bd474f9f64d5d3001424d3c4513d43d6a5256022cd5a172167959ec`;
  the source hash is
  `193fe015b32ffde4d93e00720c9fef510a804228e24f19f5cc6c97e8ad5fa724`.
- Submitted authoritative replacement job `172946` from exact snapshot
  `9d890542b964d40580ad2f8f77fa83455de3b9af0f8ca905a37f6a6ee278e296`
  on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. It is queued/pending.
  The local pass does not substitute for an independent WMI admission receipt:
  no WMI pass, pinned remote receipt, or theorem admission is claimed. The
  runner now has nine focused suites and a 76-gate full audit.
- To prioritize the focused prerequisite jobs, superseded full jobs `172707`,
  `172716`, `172722`, and `172737` were placed in a reversible user-held state.
  They were not cancelled and are to be released after focused results settle.

## 2026-07-30 — Native body receipts and a common WMI QR batch

- Removed the UI-only `ring` call from
  `prime_bounded_square_one_cases`. Its normalization is now an explicit
  native equality/rewrite derivation, which explains the corrected 16-item
  dependency boundary including `mul_succ_left`. A body-only laptop replay
  measured 182 nodes at depth 48.
- Authored the signed-half candidate pair
  `odd_upper_remainder_reflection` and
  `gauss_pointwise_signed_half_representative`. Their body-only laptop
  receipts are respectively 125 nodes/depth 34 and 116 nodes/depth 38.
- Authored the eight-candidate finite-omission stack. In theorem/dependency
  order, the body-only nodes/depth receipts are `73/22`, `69/27`, `58/23`,
  `21/15`, `89/31`, `149/43`, `24/16`, and `27/18` for
  `finite_covers_into_or_omits`, `finite_inverse_choice_prefix_extend`,
  `finite_inverse_choice_prefix_exists`,
  `finite_inverse_choice_bounded_into`, `finite_inverse_choice_injective`,
  `finite_short_cover_impossible`, `finite_short_prefix_omits`, and
  `finite_bounded_into_injective_omits`.
- For each of `wilson-square-one`, `gauss-signed-half`, and
  `finite-omission`, the three bounded local structural gates passed: exact
  contract/dependency checks; helper hygiene/native/witness checks; and
  graph/core/source isolation. These receipts exercise theorem bodies or
  bounded structure only. They are not closed recursive replay, are not
  closed-certificate admission, and admit no new theorem.
- Ran the cheap all-stack body replay and fixed two existential-binder errors
  in `wilson_inverse_prefix_candidate.py` and an apply-to-negation error in
  `wilson_inverse_orbit_candidate.py`. All 19 Wilson bodies now pass. Layered
  nodes/depth are square `182/48`; point `55/22`, `70/28`, `50/21`, `20/12`;
  prefix `76/29`, `64/25`, `29/16`; involution `44/23`, `49/25`, `80/29`,
  `55/29`, `31/22`, `83/31`; endpoints `76/23`, `54/23`, `104/32`; and orbit
  `45/26`, `206/40`. Twelve bounded structural gates pass across prefix,
  involution, endpoints, and orbit—three for each suite. These remain body-
  only/structural evidence, not closed-certificate admission.
- Cancelled stale zero-CPU jobs `172855`, `172899`, `172920`, `172927`, and
  `172932`; their historical submissions remain recorded above. Snapshot
  `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`
  produced valid pending jobs `172964` (`gauss-signed-half`), `172965`
  (`finite-omission`), and `172966` (`wilson-square-one`). Its first dependent
  replacements `172967` (`wilson-inverse-involution`), `172968`
  (`wilson-inverse-endpoints`), and `172970` (`wilson-inverse-orbit`) were
  cancelled after zero CPU when the prefix errors made them stale.
- Staged the corrected Wilson stack as exact snapshot
  `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`
  and submitted `172975` (`wilson-inverse-prefix`), `172976`
  (`wilson-inverse-involution`), `172977` (`wilson-inverse-endpoints`), and
  `172978` (`wilson-inverse-orbit`). They were pending at submission. No
  current job had consumed CPU at the latest recorded poll, so there is no WMI
  pass or admission result.
- The WMI runner now selects 86 gates across 19 source modules and exposes 11
  focused five-gate suites. Full recursive replay, profiling, capacity/no-DNE
  checks, and adversarial mutation for this batch remain cluster-only.
- Ran the cheap finite-product plus Fermat body preflight. It caught and fixed
  a missing second rewrite in `beta_successor_range_reindex_aligned` and
  eliminated an invalid locally repackaged `hprojection` in
  `prime_mul_residue_product_balance`. All 21 bodies now pass. Key nodes/depth
  are reindex aligned `86/34`, scale `62/32`, reindex exists `106/40`, balance
  `93/39`, predecessor Fermat `93/34`, and all-input Fermat `104/30`.
- Added reusable
  `peano_lab.library.candidate_validation.replay_candidate_bodies`. It
  kernel-checks dependency-curried candidate scripts without replaying or
  closing dependencies and returns exact structural/identity metrics. Its
  three unit tests pass. It is a defect-finding preflight, never an admission
  receipt.
- Passed nine bounded structural gates across `fermat-reindex`,
  `fermat-balance`, and `fermat-endpoints`, three per suite. These are body-
  only/structural receipts, not closed recursive replay or closed-certificate
  admission, and they admit no theorem.
- Cancelled stale jobs `172769`, `172770`, and `172837` after zero CPU. Staged
  their corrected sources as exact snapshot
  `73d2863a0138c8dce1f8a7f2793bcd96f543e389c0c4af6cce75cc13005ac3d9`
  and submitted `172988` (`fermat-reindex`, 16 GiB/2 hours), `172989`
  (`fermat-balance`, 16 GiB/2 hours), and `172990` (`fermat-endpoints`,
  32 GiB/4 hours). All three were pending at submission; no WMI pass or
  admission is claimed.
- Authored the seven-candidate signed-half prefix tranche. It adds an explicit
  pointwise magnitude/sign choice, full-half-range choices, simultaneous
  magnitude/sign beta-prefix extension, generic and specialized prefix
  existence, an `AllBits` projection, and relational `BitCount` existence.
  The new bodies measured `73/27`, `133/39`, `164/47`, `70/31`, `33/22`,
  `35/25`, and `31/26` nodes/depth.
- Ran the requested 60-second-capped dependency-curried preflight for the two
  earlier and seven new signed-half candidates. It caught one missing explicit
  `intro hpzero`/`exact hpzero` pair in the prime-nonzero subproof. After that
  correction all nine bodies passed in about 1.8 seconds. This replay closes
  no dependencies and admits no theorem.
- Added the focused `gauss-signed-prefix` WMI audit and wired it through the
  runner, submission wrapper, and Slurm allowlist. Its five gates cover exact
  native contracts/body metrics, hygiene and alpha-equivalence, the exact
  local/core/source boundary, two cold recursive closures with capacity/no-DNE
  receipts, and contract plus every-direct-Cut mutations. The runner now has
  91 gates across 20 source modules and 12 focused suites. Heavy replay remains
  cluster-only and has not yet produced a receipt.
- Recorded the representation, dependency graph, validation policy, and exact
  next boundary in `gauss-signed-prefix-design.md`. Work stops here before the
  magnitude-permutation tranche; no Gauss-lemma claim is made.
- Authored the ten-candidate Euler scaled-inverse entrance ladder. It proves
  pointwise existence and uniqueness of the bounded relation
  `x*y == a (mod p)`, symmetry, involution, the fixed-point/square-root
  equivalence, and fixed-point freedom under `~QRes`. Dependency-curried body
  nodes/depth are `36/17`, `30/19`, `59/26`, `126/34`, `74/24`, `31/12`,
  `28/19`, `38/15`, `17/15`, and `24/15`. See
  `research/arithmetic-library/euler-scaled-inverse.md`; these scripts remain
  isolated and unadmitted.
- Authored the nine-candidate Wilson PairOrder extension layer: append and
  reflect two β entries, choose an unused nonendpoint constructively, extract
  its unused inverse mate, preserve orbit closure/nonendpoint range/
  injectivity, and package one choose-and-append step. Body nodes/depth are
  `63/27`, `115/32`, `113/30`, `138/43`, `34/20`, `167/38`, `63/31`,
  `202/36`, and `191/53`. The exact representation and remaining iteration,
  coverage, lift and product obligations are in
  `research/arithmetic-library/pair-order-encoding.md`.
- Staged both ladders and the signed-prefix audit in exact snapshot
  `8c9c4ae067b0dc202684e410bee563cd592a67080cb7c9939440ae8b44d4bccd`.
  All three remote test-only validations returned exit zero after replacing
  WMI `bash -l -s` with `bash -s`; a login-shell logout hook had previously
  overwritten successful validation status with local exit 1. Submitted jobs
  `173015` (`euler-scaled-inverse`), `173016` (`gauss-signed-prefix`), and
  `173017` (`wilson-pair-order`); each is pending with zero CPU and supplies no
  proof or admission result. The live runner now contains 101 gates across 22
  test sources and 14 focused five-gate suites plus `full`. Only static checks
  and hard-60-second dependency-curried body preflights run on the laptop;
  recursive closure, profiles, mutations and book builds remain WMI-only.
- Completed the eleven-spec magnitude-permutation endpoint: range,
  prime-scaled uniqueness, same/mixed-sign collision analysis, magnitude
  injectivity, predecessor recoding, boundedness, injectivity and surjectivity.
  Body nodes/depth are `39/25`, `48/24`, `96/34`, `169/50`, `626/70`,
  `157/45`, `31/25`, `87/30`, `48/20`, `60/31`, and `39/21`. Three follow-on
  magnitude-product alignment bodies pass at `51/28`, `127/39`, `72/34`; two
  sign-product/power bodies pass at `35/24`, `259/46`. The latter five remain
  body-only; β sign-factor recoding and the combined product bridge are open.
- Corrected PairOrder's maintained state by adding decoded boundedness, then
  authored fifteen candidates for state-preserving append, empty state,
  remaining-pair arithmetic and terminal nonendpoint coverage. Body
  nodes/depth are `95/40`, `19/12`, `69/27`, `90/42`, `23/19`, `18/14`,
  `20/16`, `22/18`, `64/19`, `8/8`, `12/9`, `266/44`, `33/20`, `72/37`,
  and `51/36`. Full iteration, successor lift and product transport remain.
- Froze snapshot
  `fd129d34bf4a31a131a28d55bc6a16153984e0d37ac24dcefe7c2735cfb058d1`
  and submitted pending zero-CPU jobs `173021`
  (`gauss-magnitude-permutation`) and `173022`
  (`wilson-pair-order-induction`). The live WMI surface is 111 gates across 24
  test sources and 16 focused five-gate suites plus `full`; no result or
  admission is claimed.
- Independently audited and remediated the WMI Jupyter Book harness: immutable
  canonical packaging, worktree-drift guards, non-login environment isolation,
  source/output separation and path-escape checks are now explicit. It is
  ready for test-only scheduler validation. No transfer, build submission or
  Book build has run.
- The audited WMI Jupyter Book test-only scheduler validation succeeded. The
  frozen archive contains 125 files, has SHA-256
  `6feb5ebcdb9f59e6d94b71acd3fb2bce06d45b3a3885ad95aa8e9c02d61a3bcb`,
  and content-manifest SHA-256
  `c09064eb67906761c357626df4ee9e0cf387a89b7593654c8c5bf74baf836c24`.
  Submitted job `173024` was `PENDING (Priority)` with zero CPU at the last
  observation. This is submission provenance only: no Book-build or integrity
  result exists yet.

## 2026-07-30 — Laptop-safe Gauss composition and paired Wilson iteration

- Kept every laptop proof replay under a hard 60-second CPU limit. Recursive
  dependency closure, mutation campaigns, full profiles, and the Jupyter Book
  build remained WMI-only. A read-only scheduler query found jobs `173015`,
  `173016`, `173017`, `173021`, `173022`, and `173024` still pending with zero
  CPU; this is not a result.
- Completed the five-body plain PairOrder iteration and terminal specialization
  at `95/37`, `78/24`, `68/22`, `148/37`, and `52/26` nodes/depth. A soundness
  audit then exposed that the four-part state did not remember adjacency
  history. Added `PairedInverseWitness` and seven corrected history/iteration
  bodies at `34/16`, `38/17`, `19/15`, `114/31`, `122/40`, `169/39`, and
  `52/26`.
- Authored the successor lift from zero-based inverse indices to actual
  residues. Its four bodies construct the lifted code, prove every adjacent
  pair is a unit pair, package the factor code, and obtain an exact product
  congruent to one. Metrics are `17/11`, `124/38`, `41/31`, and `65/32`.
  A packaging failure was real but local: the product theorem expected the
  full existential trace relation rather than its bare trace body. Restoring
  the two trace witnesses fixed it.
- Completed sign-factor recoding, generic pointwise-product recoding and exact
  multiplication, and the signed pointwise modular product bridge. The latter
  three bodies measure `165/46`, `80/53`, and `70/51`.
- Added the reusable theorem that a finite product of positive residues below
  a prime is coprime to that prime (`64/31`). Its Gauss specializations prove
  the odd half bound, pointwise magnitude bounds, and magnitude-product
  coprimality at `45/20`, `69/29`, and `31/20`.
- Composed the magnitude, sign, pointwise-product, and scaling layers. The
  resulting bodies prove `A*P == P*R (mod p)` and then constructively cancel
  the half-range product using balanced Bézout, at `148/70` and `156/87`.
  The focused test traversed all six new coprimality/composition certificates,
  found no DNE, and reported three passes in 24.58 seconds. This is the
  algebraic heart of Gauss's lemma under explicit witness premises; it is not
  recursive closure, an existence-packaged endpoint, or admission.
- Added focused successor-lift and generic prime-product tests. Six tests
  passed in 1.24 seconds, covering five specs, 251 tactic commands, and 311
  body proof nodes. All candidates remain outside the public registry.
- Prepared, but did not upload, a 197-file WMI archive for exactly
  `gauss-sign-factor-recode` and `wilson-pair-order-iteration`. It is
  3,552,256 bytes with SHA-256
  `938b212fb594708f7cee05c12a10e7c709110619b70d71b3200a27e6e85ede1b`.
  Each intended job requests one CPU, 16384 MiB, and two hours. Local static
  and dry-run checks passed; explicit authorization of this exact upload is
  still required, so no transfer or submission occurred.
- Packaged the entire Gauss witness chain in the isolated theorem
  `gauss_lemma_power_congruence_exists`. From `p=2*h+1`, primality,
  `p` not dividing `a`, and a canonical half-range code, it returns `e,A,R`,
  both relational powers, hidden signed-prefix/`BitCount` evidence, and
  `A == R (mod p)`. The 193-command body checks at 258 nodes/depth 83, with no
  DNE; three focused tests passed in 31.29 seconds under the CPU cap.
- Completed the terminal Wilson product transport in four isolated bodies.
  Terminal state gives the positive magnitude range (`80/30`), predecessor
  recoding aligns the canonical range `2,...,l+1` with the successor lift
  (`152/42`), product permutation gives exact equality (`79/39`), and the
  terminal package combines state, pair history, coverage, lifted product
  congruent to one, canonical product, and equality at `188/65`. Endpoint
  restoration remains.
- Completed endpoint restoration and the full native Wilson capstone. The
  seven-body ladder supplies the leading factor `1`, restores the last factor,
  transports the modular product, splits prime `2` from the odd shape, and
  concludes `Factorial(n,F) -> F == n (mod p)` for `p=S n`. Nodes/depth are
  `30/15`, `258/45`, `63/29`, `21/16`, `104/30`, `94/35`, and `110/31`;
  three focused tests pass in 4.00 seconds. The prime-two proof does not call
  Range2 or PairOrder. This is body-green evidence, not WMI closure or
  admission.
- Opened M25 with a generic beta-coded quotient/remainder prefix. One-step
  extension and full finite-prefix existence check at `132/41` and `71/30`.
  This is the native first-order replacement for a floor-sequence function;
  no division operator or list type was added.
- Added the exact Eisenstein scaling bridge rather than reusing a merely
  modular Fermat representative. A constant prefix and canonical half range
  are pointwise-multiplied into literal entries `a*(1+i)`; relational division
  then constructs quotient/remainder prefixes and `Sum` supplies the floor-sum
  witness. The three bodies check at `34/24`, `71/40`, and `52/28`; four
  focused tests passed in 0.66 seconds under the laptop CPU cap. The remaining
  boundary is the two-orientation lattice partition, not sequence existence.
- Re-ran the two terminal-Wilson/division-prefix focused suites together:
  seven tests passed in 6.26 seconds. A read-only scheduler query again found
  all six existing WMI jobs pending at zero CPU.
- Lifted Euler's pointwise scaled-inverse relation to a beta-coded map on the
  whole predecessor interval. The extension, bounded-induction, and full-map
  bodies check at `105/36`, `81/33`, and `40/23`; four focused tests pass in
  0.76 seconds. This closes map existence, but not decoded extensionality,
  fixed-point-free two-cycle enumeration, Euler's criterion, recursive WMI
  closure, or admission.
- Completed the first Euler prefix extensional tranche. Entry soundness,
  pointwise extensionality, nonresidue fixed-point freedom, positive-mate
  predecessor extraction and decoded involution pass at `58/25`, `54/26`,
  `36/27`, `67/36`, and `91/39`; four focused tests pass in 0.82 seconds.
  The witness-scope failure encountered while authoring involution was only a
  local existential-name mismatch; rebuilding the local formulas with the
  actual eliminated witness fixed it without changing the statement.
- Added decoded Euler-prefix injectivity at `77/36`. The proof is smaller than
  a finite-cardinality route: soundness gives two scaled relations with the
  same decoded mate, symmetry turns the mate into their common source, and
  pointwise uniqueness plus successor injectivity identifies the indices.
- Proved the constructive arithmetic boundary for Eisenstein's half rectangle.
  Distinct odd primes cannot have `q*(1+i)=p*(1+j)` inside the two half
  ranges; every cell therefore has exactly one strict orientation. The three
  bodies check at `72/30`, `77/34`, and `53/34`, and four focused tests pass
  in 0.54 seconds. The honest remaining representation gap is a reviewed
  rectangular indicator/double-count fold, because current `Sum` and
  `BitCount` relations are one-dimensional.
- Resolved the first half of that representation gap with one beta code per
  fixed row. Exact zero/one cell semantics, append/induction, `AllBits`,
  decoded semantics, and the native row `BitCount` package pass in seven
  bodies at `46/29`, `71/27`, `58/23`, `53/34`, `27/16`, `43/23`, and
  `63/29`; four focused tests pass in 1.11 seconds. A second beta prefix over
  the row counts will conservatively provide the rectangle total.
- Added that second, nested beta prefix without flattening or a pairing
  function. Eight bodies choose semantic row counts, append and construct the
  outer prefix, recover the inner row/`BitCount` witness from every decoded
  entry, and attach a native outer `Sum`. Their metrics are `39/25`, `71/27`,
  `58/23`, `40/27`, `37/26`, `30/23`, `43/23`, and `40/22`; four focused
  tests pass in 2.22 seconds. This constructs a rectangle-total witness but
  proves no quotient/floor-sum equality, transposed partition, or reciprocity.
- Generalized Wilson's adjacent-unit fold into
  `beta_adjacent_target_pairs_product_power`. If every adjacent pair has
  product congruent to `a`, the exact product of `m+m` entries is congruent to
  any relational `Pow(a,m,A)` witness. The constructive 118-command body
  checks at `171/47` with two shared proof objects; its exact-contract,
  hygiene, native-syntax and no-DNE audit passes `4/4` in 1.71 seconds. This
  closes the generic product comparison, not the Euler scaled-prefix
  reordering, recursive WMI closure, registration, or admission.
- Closed the constructive quadratic-residue branch of Euler's criterion at
  the candidate-body level. First, `mod_eq_zero_to_dvd_nonzero` turns a
  balanced zero congruence into an explicit divisibility witness (`48/18`).
  Then `quadratic_residue_half_power_mod_one` proves that for
  `p=2*h+1`, prime `p`, `p` not dividing `a`, a square witness for `a` forces
  every relational half-power witness `A` to satisfy `A == 1 (mod p)`.
  It derives nondivisibility of the square root constructively, identifies
  `(r^2)^h` with `r^(2h)` via `pow_mul_exp`, applies the Fermat predecessor
  endpoint, and transports the base congruence. The 136-command body checks
  at `148/39`; the two-spec exact-contract/native/no-DNE audit passes `4/4`
  in 2.11 seconds. The nonresidue direction and full equivalence remain.
- Added the generic Eisenstein division threshold. From `n=p*q+r`, nonzero
  `r`, and `r<p`, it proves constructively that `p*S(j)<n` iff `S(j)<=q`.
  The 67-command body checks at `92/30` with no DNE; four focused tests pass
  in 0.30 seconds. Distinct-prime remainder nonzeroness, quotient bounds and
  the initial-segment `BitCount` evaluation remain before row-count equality.
- Added the correct structural entrance for Euler's fixed-point-free pairing.
  The raw scaled prefix stores actual mates `S j`, so reusing Wilson's
  zero-based `OrbitClosed` relation unchanged would be unsound. The new
  shifted closure tracks `At(scaled,i,S j)`. Four bodies prove omission
  transfer across a back edge, append preservation of shifted closure,
  constructive selection of an omitted distinct two-cycle under `~QRes`, and
  the full choose-and-append step preserving closure and order injectivity.
  Metrics are `34/20`, `184/40`, `107/38`, and `190/52`; three focused tests
  pass in 2.78 seconds with no DNE. This is one orbit only: balanced
  iteration, explicit adjacent history, terminal coverage, recursive WMI
  closure and admission remain.
- Audited the Eisenstein remainder specialization before proving it and found
  a real orientation error: `p=3`, `q=7`, `i=2` satisfies the proposed
  cross-half bounds but gives remainder zero. Replaced that false claim with
  a generic prime/nondivisor theorem requiring `S i<p`, a distinct-prime
  wrapper, and the correctly oriented own-half wrapper `p=2*k+1`, `i<k`.
  Their body metrics are `47/21`, `45/24`, and `45/28`; the pinned regression,
  exact contracts and no-DNE certificates pass `4/4` in 0.40 seconds. No
  remainder-bound premise is needed.
- Closed the quotient-bound arithmetic independently of primality. The
  explicit gap `(2*k+1)*h < (2*h+1)*S k` has a native no-ring body at
  `160/45`. From `i<h` and
  `(2*k+1)*S i=(2*h+1)*d+r`, the second theorem uses monotonicity and that
  gap to force `d<=k` at `67/29`. The quotient and remainder suites pass
  together `8/8` in 0.54 seconds. Only the generic initial-segment
  `BitCount=quotient` bridge remains before one-row identification.
- Closed that generic exact-initial-segment bridge at the dependency-curried
  body level. Eight constructive bodies build the threshold bit choice and
  beta prefix, project `AllBits`, recover decoded semantics, count an all-one
  prefix, and prove functional and exact `BitCount=q`. Their metrics are
  `23/12`, `63/25`, `40/19`, `25/14`, `41/21`, `91/28`, `160/37`, and
  `49/21`; all eight bodies plus hygiene/native-contract checks pass `11/11`
  in 2.09 seconds with no `DNE`. Complete replay exposed and fixed stale
  induction-variable names, over-rewrites, and missing conjunction cases in
  the draft scripts without changing the theorem contracts. The next exact
  step is to turn a decoded division row into this initial-segment relation
  and transport `BitCount` equality into the nested outer sum.
- Added the general exact fold transport needed immediately after that
  pointwise identification. `beta_sum_transport_prefix` reuses an existing
  beta-coded sum trace when a target prefix decodes the same bounded entries;
  it compares semantic entries rather than raw beta-code identities. The
  dependency-free 44-command body checks at `59/29`, with 59 proof objects,
  58 edges, no reuse and no `DNE`; its focused test passes `3/3`, and the
  combined initial-segment/transport audit passes `14/14` in 2.20 seconds.
- Replayed the full laptop-safe Eisenstein stack together after these changes:
  scaled division, lattice orientation, row indicators, nested rectangle
  counts, division threshold, remainder nonvanishing, quotient bounds, exact
  initial-segment counting, and exact sum transport pass `42/42` in 6.48
  seconds under one 60-second wall alarm. This remains body-only evidence;
  recursive closure, mutations, registration and admission stay WMI gates.
- Completed and audited Euler's terminal scaled PairOrder iteration. Ten
  dependency-curried bodies cover empty shifted closure/history, adjacent
  history append, empty state, the invariant-preserving pair step, the two
  length-balance facts, full paired iteration, terminal packaging, and
  terminal coverage. Their nodes/depth are `23/19`, `19/15`, `114/31`,
  `49/18`, `125/40`, `80/24`, `40/15`, `155/39`, `41/25`, and `64/26`.
  The focused exact-contract, dependency, hygiene, native-syntax,
  registry-isolation and no-DNE audit passes `4/4` in 4.72 seconds.
- The terminal-iteration replay exposed only authoring defects, not a change
  in theorem content: composite-length parenthesization, simplification
  order, typed terminal specialization, both injectivity-bound rewrites, and
  hygienic formula generation were corrected. The candidates remain outside
  the public registry and are not admitted. The next Euler work is
  successor-lift/product alignment and the nonresidue endpoint, followed by
  recursive WMI closure, mutation audits, and a separate admission replay.
- Added the exact one-dimensional cardinality identity needed by the later
  rectangle partition. `complementary_bit_counts_add_length` inducts through
  two relational `BitCount` witnesses and proves their values add to the
  common prefix length when every decoded pair is `(0,1)` or `(1,0)`. The
  five-dependency, 112-command body checks at `220/46` (211 objects, 219
  edges, nine reused), contains no `DNE`, and passes its focused `3/3` audit
  in 1.47 seconds. This does not yet prove the nested row/column transpose.
- Closed the Eisenstein-specific pointwise row identification. The four new
  bodies convert a semantic row prefix to the quotient's exact initial
  segment (`78/36`), prove its `BitCount` equals the bounded division quotient
  (`95/45`), connect that value to the decoded quotient beta entry (`111/55`),
  and consume the nested rectangle layer's existing semantic row witness
  directly (`119/72`). The focused kernel/no-DNE/no-auto/no-ring audit passes
  `4/4` in 3.40 seconds; the author's prerequisite-integrated run passed
  `27/27` in 5.86 seconds. All remain dependency-curried and unregistered.
  The immediate next theorem must instantiate exact sum transport between the
  quotient prefix and outer row-count prefix before the transposed partition.
- Closed Euler's bounded nonresidue product/sign endpoint. Five constructive
  bodies prove adjacent lifted pairs have target product `a`, identify the
  lifted order product with the exact factorial, combine the generic power
  fold with Wilson at the terminal state, package the nonresidue iteration,
  and expose the bounded public theorem. Their nodes/depth are `132/39`,
  `144/45`, `136/52`, `61/34`, and `49/30`; focused tests pass `4/4` in 4.39
  seconds and the related body-only Euler stack passes `16/16` in 12.19
  seconds. The endpoint proves `A == n (mod p)` from `p=S n`, `n=h+h`, prime
  `p`, `0<a<p`, `~QRes(p,a)`, and `Pow(a,h,A)`. It remains unregistered and
  unadmitted; bounded equivalence packaging, unreduced representatives, and
  WMI closure/mutations/admission remain.
- Closed the first-orientation quotient-sum/rectangle-total identification.
  Pointwise decoded quotient entries now match the semantic outer row-count
  entries (`104/52`), the exact quotient `Sum` transports to that outer prefix
  (`73/54`), and functionality equates it with any independently supplied
  rectangle total (`67/51`). The focused audit passes `4/4` in 4.92 seconds;
  five related body-only suites pass `19/19` in 10.71 seconds. The theorem is
  parameter-symmetric, so the remaining obstruction is not the second floor
  sum but the equality of the two transposed semantic totals with `h*k`.
- Opened that obstruction at the exact semantic-cell boundary. A decoded cell
  bit and its swapped-row transpose are constructively complementary at
  `95/33`. A second theorem opens decoded entries from both outer count
  prefixes, recovers their existential inner row codes and `BitCount`
  witnesses, decodes the transposed bits, and packages complementarity at
  `116/58`. Their focused tests pass together `6/6` in 2.08 seconds. This is
  deliberately not claimed as nested Fubini: summing the pointwise witnesses
  across differently shaped existential row codes remains the exact gap.
- Corrected two stale mutation-harness metadata keywords from the removed
  `description` field to `TheoremSpec.summary`. A combined local mutation
  attempt reached the strict 60-second alarm and was terminated without a
  result; no further closure/mutation replay will run on the laptop. Those
  gates remain explicitly WMI-only.
- Added generic exact addition for relational beta sums.
  `beta_sum_pointwise_add` inducts over three equal-length prefixes, uses the
  existing exact successor decompositions, and derives `n+m=q` from decoded
  equations `s=a+z`. Its six-dependency, 127-command body checks at 195 nodes,
  depth 57, 195 objects, 194 edges, no reuse and no `DNE`; the exact-contract,
  native-expansion and isolation audit passes `3/3`.
- Added exact evaluation and existence for constant-prefix sums.
  `beta_repeat_sum_exact` proves that a length-`l` `Repeat(a)` prefix with
  terminal `Sum` value `n` satisfies `n=l*a`; its 64-command body checks at
  `85/32`. `beta_repeat_sum_exists_exact` packages the beta code, sum trace,
  and exact endpoint at `33/21`. Their focused tests pass `4/4`, and the two
  constant-sum bodies plus pointwise addition pass `7/7` in 2.18 seconds.
- Lifted transposed-cell complementarity from independently chosen cells to a
  coherent whole-column encoding. Six new bodies retain, at every decoded
  column entry, the swapped outer entry, one exact inner row, its `BitCount`,
  and the corresponding cell. Their receipts are `42/26`, `80/31`, `64/29`,
  `56/33`, `87/47`, and `117/56`; the endpoint proves that an original row
  count plus the constructed transposed-column count is exactly `k`. Focused
  tests pass `5/5` in 5.21 seconds and five related suites pass `18/18` in
  10.39 seconds. Raw beta-code equality is never used.
- Replayed the new exact-sum theorem with sum transport, complementary counts,
  both transposed-cell layers and the coherent-column stack: all 20 focused
  tests passed in 9.75 seconds under the laptop boundary. This is body-only
  evidence, not recursive closure, mutation validation, or admission.
- Packaged the complete bounded odd-prime Euler criterion. Seven constructive
  bodies derive bounded nondivisibility, rule out `1 == p-1`, establish the
  residue/nonresidue dichotomy, prove both iff directions, and expose one
  theorem containing
  `QRes(p,a) <-> A == 1 (mod p)` and
  `~QRes(p,a) <-> A == p-1 (mod p)`. Their nodes/depth are `20/13`, `65/19`,
  `56/25`, `120/39`, `92/30`, `91/37`, and `80/31`; focused tests pass `4/4`
  in 1.67 seconds and the combined bounded Euler suites pass `12/12` in 7.62
  seconds. The arbitrary-representative reduction and all WMI gates remain.
- Completed the arbitrary-unit Euler interface. Six isolated bodies use
  quotient/remainder existence to choose a nonzero bounded representative,
  prove `QRes` invariant under balanced congruence, transport a relational
  power witness with `pow_mod_congruent`, and derive both arbitrary residue
  and nonresidue iff statements plus one combined endpoint. Their
  dependencies/commands/nodes/depth receipts are `3/39/49/20`,
  `2/31/38/17`, `2/25/29/22`, `7/92/140/36`, `7/98/146/37`, and
  `2/33/75/29`. Focused tests pass `4/4` in 2.04 seconds; all four Euler suites
  pass `16/16` in 9.96 seconds. The theorem no longer assumes a reduced `a`,
  only `p` not dividing `a`.
- Completed the outer aggregation of coherent transposed-column counts. Eight
  bodies construct a provenance-carrying prefix over all original row indices,
  attach its exact `Sum M`, recover the decoded equations `n_i+m_i=k`, align
  them with a constant beta prefix, and compose exact pointwise addition with
  the constant-prefix sum to prove `N+M=h*k`. Their receipts are `70/32`,
  `88/35`, `68/33`, `59/28`, `51/26`, `60/36`, `61/43`, and `116/61`.
  Focused tests pass `5/5` in 13.29 seconds and five related suites pass
  `21/21` in 23.05 seconds. The remaining Fubini theorem is isolated exactly
  as `M=T`, with `T` the swapped rectangle's native outer `Sum`.
- Independently replayed the new column-count outer tranche, both generic
  exact sum tranches, and bounded/arbitrary Euler packaging together: all 20
  focused tests passed in 18.04 seconds under the laptop-safe limit. This is
  still dependency-curried body evidence rather than WMI closure or admission.
- Added the constructive converse parity API needed after the lattice-count
  identity. `even_sum_parity_cases` and `odd_sum_parity_cases` split explicit
  parity witnesses and reject the impossible branches; the two iff wrappers
  add the already checked forward closure laws. Their dependency-curried body
  receipts are `61/18`, `61/18`, `63/19`, and `63/19`, with no object reuse,
  `DNE`, `auto`, or `ring`. The focused audit passes `4/4` in 0.40 seconds.
- Added the native modulo-two parity interface. Four conversion bodies prove
  `Even(n) -> n == 0`, `n == 0 -> Even(n)`, `Odd(n) -> n == 1`, and
  `n == 1 -> Odd(n)` modulo two; a fifth proves that balanced congruence
  transports both parity predicates. Receipts are `14/9`, `20/13`, `42/18`,
  `50/16`, and `86/20` nodes/depth. The tests pin expanded statements,
  dependencies and identity metrics and rule out registration, automation,
  classical escape and `DNE`.
- Independently replayed the six-body odd-multiplier/division parity tranche.
  It proves exact parity reflection under an odd multiplier and across
  `n=p*q+r`, without a remainder bound. Together with sum classification and
  modulo-two transport, all three focused suites pass `12/12` in 1.27
  seconds under the laptop cap.
- Added the fixed-odd-half/modulo-four bridge needed by the final reciprocity
  split. Two exact bodies use `odd_half_unique` to derive `h=2*a` or
  `h=2*a+1`; two wrappers prove the corresponding constructive iff packages.
  Their receipts are `20/13`, `78/27`, `42/18`, and `100/30`. With the other
  parity candidates, all four suites pass `16/16` in 1.24 seconds.
- Completed and independently replayed the first actual-QRes Gauss endpoint.
  `bounded_gauss_lemma_complete` retains the signed-prefix/count provenance
  and proves `QRes(p,a) <-> Even(e)` and `~QRes(p,a) <-> Odd(e)` for prime
  `p=2*h+1` and `0<a<p`. Its receipt is 11 dependencies, 204 commands,
  597 nodes/depth 53, 559 objects, 596 edges and 38 reused objects; the
  focused audit passes `5/5` in 7.88 seconds. It is dependency-curried and
  unadmitted.
- Removed the canonical-representative restriction from actual Gauss's lemma.
  `arbitrary_gauss_lemma_complete` replaces `0<a<p` by the exact native
  premise `~exists k. a=p*k`, invokes the arbitrary Euler package, and retains
  the original signed prefix plus `BitCount e`. Its 188-command body checks
  at 547 nodes/depth 49, 513 objects, 546 edges and 34 reused objects. The
  focused audit passes, and the bounded/arbitrary pair passes `9/9` in 13.64
  seconds. Neither theorem is registered or admitted.
- Independently replayed the generic signed-division parity bridge. Its five
  bodies constructively derive modulo-two congruence from matching parity,
  transport odd scaled division, handle an odd reflected remainder, align the
  two sign branches, and conclude `x == q+m+s (mod 2)`. Nodes/depth are
  `53/15`, `77/27`, `87/27`, `64/22`, and `43/25`; all `5/5` focused checks
  pass in 0.56 seconds. The theorem is exact pointwise arithmetic; it does not
  yet assert that independently beta-coded Gauss signs and division remainders
  satisfy the required exact branch.
- Added exact signed-remainder representation alignment. Four constructive
  bodies derive the positive odd-half complement, the reflected predecessor
  congruence, uniqueness of the canonical remainder, and finally
  `(s=0 /\ r=m) \/ (s=1 /\ r+m=p)`. Their nodes/depth are `238/39`,
  `53/22`, `49/24`, and `115/35`; dependencies, hashes and identity metrics
  are pinned in an isolated focused audit.
- Added the common-index Gauss--Eisenstein β-prefix join. The generic
  composition checks at `58/34`; the prefix theorem opens the canonical half
  range, exact scaled values, quotient/remainder trace and signed
  magnitude/bit trace and proves `x_i == q_i+m_i+s_i (mod 2)` at `250/61`.
  Its expanded native statement has length 5,440 and SHA-256
  `84b039612f162c0c0935ebf49e1ffadf0cdf8e660914f583b7f490744175884e`.
  Five related suites pass `21/21` in 3.07 seconds. The candidates are
  unregistered and unadmitted.
- Completed the exact finite-sum permutation ladder. Replacement balance,
  swap-last invariance, fixed-last reindexing and arbitrary bounded-injective
  reindexing check at `327/59`, `133/50`, `85/33`, and `631/88`; the two
  focused suites pass `8/8` in 22.67 seconds. This gives the constructive
  magnitude-sum cancellation tool without treating different β codes as
  equal. Aggregation of the pointwise congruence remains the next local gate.
- Closed the native Eisenstein transpose/Fubini gap. Sixteen recovered row-
  decomposition bodies and nine total-level bodies prove the universal
  transposed-column identity `M=T` (`264/65`), specialize it to the campaign's
  constructed column prefix (`49/33`), and compose with `N+M=h*k` to obtain
  `N+T=h*k` (`65/37`). The decoded endpoint
  `distinct_odd_prime_eisenstein_quotient_sum_identity` then proves the actual
  two-orientation quotient/floor-sum identity `Q+U=h*k` at `145/68`, with
  SHA-256
  `d10467b948c749bcf5727127213b5337583b3bba415da7d30a1589ede66116ae`.
  An independent 60-second-capped run passes all three focused suites
  `12/12` in 45.25 seconds. No theorem is registered or admitted.
- Added the final constructive parity truth-table layer in isolation. Six
  bodies turn an even/odd Gauss-count sum into equal/opposite cross-residue
  status, transfer that result from congruence modulo two with `h*k`, and
  prove the one-mod-four and both-three-mod-four cases. Nodes/depth are
  `48/17`, `48/17`, `31/20`, `31/20`, `56/27`, and `52/26`; focused tests
  pass `4/4` in 0.93 seconds. This deliberately assumes the missing
  count-sum congruence and therefore is not yet quadratic reciprocity.
- Closed the terminal Gauss--Eisenstein finite-sum parity gate. The reusable
  `beta_sum_pointwise_mod_three_add` induction checks at `328/66`; exact
  magnitude-prefix recoding and sum-permutation transport then identify the
  common half-range/magnitude sum, and constructive modulo-two cancellation
  yields `gauss_eisenstein_sign_count_mod_quotient_sum` at `89/65`. Its
  statement retains the scaled, division, signed, `BitCount`, and quotient
  `Sum` codes and proves `Q == E (mod 2)`. An independent pointwise plus sum
  replay passes `12/12` in 17.47 seconds. This is still an isolated,
  dependency-curried and unadmitted endpoint; the next gate is composing both
  prime orientations with `Q+U=h*k` and the final QRes parity truth tables.
- Constructed the final provenance-hiding two-prime package. The orientation
  theorem checks at 5 dependencies, 102 commands, 139 nodes/depth 67; the
  pair theorem checks at 4 dependencies, 150 commands, 222 nodes/depth 77.
  For distinct `p=2h+1` and `q=2k+1`, it exposes exactly `e,f,Q,U`, both full
  QRes/parity classifications, `e == Q` and `f == U` modulo two, and the
  native Fubini identity `Q+U=h*k`.
- Proved all three exact sign-free QR authoring surfaces. The same-status and
  opposite-status bodies each check at 2 dependencies, 46 commands, 73
  nodes/depth 33. An initial 2-dependency, 54-node combined wrapper proved the
  predeclared surface, then a direct 3-dependency, 65-command, 113-node/depth
  35 body replaced it so the common two-prime data is constructed only once.
  The statements are byte-for-byte the
  formulas pinned by `quadratic_residue_surface.py`, with no hidden auxiliary
  premise or surviving beta-code variable. The focused terminal integration
  run passes `20/20` in 27.25 seconds. This is the first complete native PA
  quadratic-reciprocity body, but it remains isolated and unadmitted pending
  WMI recursive closure, adversarial mutation, resource and admission gates.
- Audited the optimized final dependency graph without replaying it on the
  laptop. It contains 557 unique specifications, has longest dependency depth
  45, and unfolds to 191,672 theorem occurrences before body nodes—almost
  exactly half the first wrapper's 382,882. This remains strong
  evidence that structural tree expansion—not PA expressibility or the final
  proof body—is now the limiting resource. The WMI discovery suite will keep
  the existing 500,000-occurrence/100,000-object policy and report both sides;
  no limit was raised from an estimate alone.
- Finished the content-addressed WMI transport for the exact final stack.
  `quadratic-reciprocity-final` selects nine gates and requests a fail-closed
  single-CPU, 32-GiB, four-hour allocation. Failure-path JSON metadata now
  survives an expected capacity assertion while the original failure and
  traceback remain authoritative. The transport harness passes `5/5`, the
  safe closure manifest/graph tests pass `2/2`, and the exact downstream proof
  slice still passes `20/20`.
- Attempted one Slurm test-only transport after freezing those files. SSH to
  `access.cluster.wmi.amu.edu.pl:22` timed out before upload. No remote
  snapshot directory, scheduler validation or job was created, so the heavy
  gates and WMI Book build remain pending without a fabricated receipt.
- Proved statically that the naive recursive QR closure cannot satisfy the
  current structural policy. Its 191,672 theorem occurrences force 191,671
  Cuts, 348,145 dependency-introduction constructors and at least 191,672
  terminal body nodes, already 731,488 nodes before real proof work. This
  rules out both wishful WMI admission and an arbitrary small limit bump.
- Selected an unchanged-kernel sharing compiler. The 557-spec, 1,792-edge DAG
  has 45 dependency layers and maximum layer width 63. Each layer becomes a
  balanced conjunction proved from projections of earlier packages and is
  introduced by one ordinary contextual Cut. The final object remains one
  standard `Proof` checked at the original QR formula; `ClosedCut` or theorem
  references are now fallback architecture rather than the first trust change.

## 2026-07-30 — Layered unchanged-kernel QR closure is locally ready

- Implemented the production-isolated generic layered Cut compiler and the
  thin exact QR-stack adapter. No production kernel, proof grammar, tactic or
  theorem-registry module imports the experiment. The compiler replaces 557
  sequential or recursively duplicated Cuts by 45 balanced conjunction
  packages and ordinary `AndElim` projections, then returns one existing
  `Proof` for the unchanged empty-context checker.
- The generic/fallback/adapter experiment passes `25/25`. On a reused 20-node
  synthetic DAG the unchanged kernel accepts both constructions, with the
  layered proof at 274 nodes/depth 16 versus 3,643/depth 20 recursively.
- Exercised the full real QR topology without replaying heavy mathematics.
  Actual QR targets with distinct false one-node bodies give exactly 13,723
  proof nodes/depth 56 and 144,197 package-formula occurrences/depth 68; the
  kernel rejects the certificate. A second surrogate assigns a distinct
  shallow reflexive marker to each node and consumes every declared premise
  through a formula-annotated Cut. It preserves all 1,792 ordered edges and
  checks at 19,099 nodes/depth 74; swapping dependencies 3 and 4 at
  `beta_range_empty` makes the kernel reject. This validates compilation, not
  quadratic reciprocity.
- Split WMI meanings cleanly: six exact body/source/graph gates remain in
  `quadratic-reciprocity-final`; nine layered compile/check/determinism/
  mutation/capacity gates form the real admission suite; three recursive
  gates are diagnostic-only and excluded from `full` because the 731,488-node
  lower bound already proves policy failure. Strict JSON records body, proof,
  package-formula, timing, RSS, source and mutation evidence.
- Independent laptop validation passes `49` tests with four WMI-only functions
  skipped in 6.64 seconds. Shell syntax and suite manifests are clean and pin
  9 layered, 6 exact-body/static and 3 recursive-diagnostic selectors. Book
  statics pass `14/14`; the new closure comparison diagram and linked research
  and vault notes preserve the unadmitted boundary.
- Attempted one content-addressed scheduler validation for
  `quadratic-reciprocity-layered`. SSH to
  `access.cluster.wmi.amu.edu.pl:22` timed out before upload. No remote
  snapshot, scheduler validation, Slurm job or proof receipt was created, and
  no retry was made in this laptop batch.
- Audited the later public migration before changing production code. The
  existing QR stack imports the theorem registry and would become cyclic and
  self-conflicting if appended directly. The reviewed route makes stack
  assembly injection-based over a frozen pre-QR table, promotes the layered
  compiler only as an untrusted ordinary-proof builder, and pins replay
  strategy before release. The 317 candidate count already includes the root
  (`316+1`). Public release additionally requires stable legacy receipts,
  all 317 on-demand replays, catalog regeneration, list-without-replay UI,
  and exact Pyodide `use`/QED/Stop gates; see
  `research/arithmetic-library/quadratic-reciprocity-admission-path.md`.

## 2026-07-30 — QR admission architecture hardened without enrollment

- Refactored the exact QR collector into a registry-neutral builder over an
  explicitly injected, copied pre-QR mapping. A separate cached runtime
  adapter preserves the no-argument campaign API without creating an import
  cycle. Fresh-process import-order, snapshot, conflict, and cache tests pass;
  the unchanged receipt is `84/346/317/240/557/45` factories, outputs,
  candidate ancestors, public ancestors, closure nodes, and layers. The graph
  and source hashes remain `2b312887...bbc39` and `141bfb8d...d58b5`.
- Promoted layered replay into the production-neutral
  `peano_lab.library.layered_replay` module. It compiles local-ID modular
  bodies into balanced conjunction packages and ordinary existing `Cut`,
  `And`, `Imp`, and `Hyp` proof constructors. It imports no theorem registry,
  human theorem name, receipt hash, or checker and grants no authority; the
  unchanged empty-context kernel remains the admission boundary.
- An independent resource audit found that proof-node counting alone ignored
  formula and term annotations hidden inside constructors. The compiler now
  scans all 25 kernel proof constructors iteratively, rejects `DNE`, engine
  holes/metavariables, custom proof subclasses and malformed fields, charges
  every repeated annotation and the separately supplied target, bounds both
  annotation and combined proof-envelope depth, and validates malformed graph
  topology before scanning bodies. No kernel, proof grammar, tactic, or PA
  language rule changed.
- The real-formula false-body scaffold retains `13,723` proof nodes/depth `56`
  and package cost `144,197/68`; its new annotation/envelope receipt is
  `157,579/92` and the kernel rejects it. The exact 557-node/1,792-edge
  dependency-consuming surrogate retains `19,099` nodes/depth `74` and
  package cost `19,297/18`; it now records `142,396` annotations/envelope
  depth `84`, is kernel-green, and its dependency-order mutation is rejected.
  These remain compiler evidence, not a quadratic-reciprocity proof.
- Bare `pa lib` now parses and pretty-prints closed statements without replay;
  theorem detail, Lean export, and `use` remain on-demand replay/check paths.
  The browser worker now lists the complete 147-file Python surface, maintained
  by the deterministic `scripts/update_peano_worker_sources.py --check` gate.
  The content-addressed `APP_MANIFEST`, release ID, and browser publication
  remain deliberately stale/pending until admission.
- Audited the future public-test migration. There are 125 blanket absence
  assumptions in 79 tests and 113 unified-registry candidate-core seeds in
  74 tests. The new migration note pins the exact 317-enrolled/29-omitted
  partition and the omitted-set digest `1b08f341...ded85`; no assertion was
  prematurely converted and no candidate was enrolled.
- The root bounded integration run passes `42` tests with four WMI-only tests
  skipped. Independent review found 25/25 kernel proof constructors covered
  and no remaining layered-compiler defect. No heavy real-body replay ran on
  the laptop.
- One post-hardening WMI test-only attempt did not execute: the managed
  approval reviewer requires payload-specific permission before the wrapper
  uploads the Peano source/test/script archive to the external cluster. No
  archive, snapshot, scheduler validation, job ID, or proof receipt was
  created, and no retry or real submission was made.

## 2026-07-30 — QR admission preflight and WMI payload freeze

- Revalidated the exact unadmitted endpoint locally. Its three modular bodies
  pass `4/4` in 2.80 seconds, the two static 557-node closure tests pass `2/2`
  in 2.76 seconds, and the production-neutral layered stack/compiler suite
  passes `37` tests with four WMI-only gates skipped in 12.21 seconds. Five
  targeted no-replay library/browser inventory tests pass in 0.38 seconds.
  No real 557-body closure was executed on the laptop.
- Python compilation, shell and worker JavaScript syntax, deterministic
  147-file worker inventory, and `git diff --check` are clean. Documentation
  statics pass `12/12`; a nine-document local-link audit has no unresolved
  targets. The admission guide now describes the old registry cycle as
  historical and records the implemented injected-stack boundary.
- Removed macOS `.DS_Store` metadata from the WMI archive and added a transport
  regression. Two independent local builds of the exact upload were
  byte-identical: SHA-256
  `13f279cf2390104009825abac01c17e8b96d56bb764719964e36949ea3345a43`,
  5,343,232 bytes, 337 tar members, base commit
  `a549a537cfe3d3d7e8ef292a49250c4308d12c5d`, dirty worktree. The source-tree
  and extracted-archive transport harnesses pass `9/9`.
- The archive contains only `peano-lab/py/peano_lab/`,
  `peano-lab/py/tests/`, `scripts/profile_peano_certificate_capacity.py`,
  `scripts/run_qr_wmi_replay.py`, `scripts/submit_wmi_qr_replay.sh`, and
  `slurm/peano_wmi_qr_replay.sbatch`; it excludes `__pycache__`, `*.pyc`, and
  `.DS_Store`. No cluster contact occurred. Upload, scheduler validation, and
  real submission still require content-specific approval for this exact
  hash; any payload-changing edit invalidates that approval request.

## 2026-07-30 — Native PA Proof Explorer and Book integration

- Built a deterministic Stacks-style reading interface for the exact
  `quadratic_reciprocity_combined` closure. It contains 557 canonical
  `PAxxxx` tag pages, 557 theorem-name aliases, 1,792 forward/reverse edges
  over 45 layers, and all 27,491 authored tactic commands. The permanent QR
  endpoint is `PA00FW`; its 65-line wrapper links to its three direct
  ingredients and onward through the complete closure.
- Linked 8,557 syntax-classified direct-theorem occurrences in `specialize`,
  `apply`, `exact`, `simp`, `cases`, and `rewrite`, plus 140 explicit PA-axiom
  occurrences. The eight declared packaging edges without literal body
  tokens remain visible in the dependency panels rather than being
  fabricated as proof-line references. Every command has a numbered anchor,
  and every tactic links to the native tactic/foundation reference.
- Preserved the admission boundary in both JSON and HTML: 240 nodes are
  public, 316 are `candidate_body_checked`, and only the root is
  `pending_layered_closure`. A tag, source hash, generated page, or informal
  explanation grants no theorem authority.
- Added a persistent append-only tag registry and a separate informal-proof
  sidecar. All 557 pages have an explicitly labelled explanation: 553
  deterministic structural guides and four curated QR endpoint/bridge
  proofs. Informal references are structured, validated, and clickable.
- Added the Book explorer chapter, embedded dashboard, PA language reference,
  axioms/rules page, foundations microsite, responsive local CSS/JavaScript,
  TOC/landing/QR links, and `make book-proof-explorer`. The static explorer is
  dependency-free and readable without JavaScript; search, status/layer
  filters, copy controls, and line-target focus are progressive enhancements.
- The generator owns 1,119 deterministic files. Its aggregate receipt is
  `669b978fff47fe7a6e9b55ddcffb4f12082872bbed1657ff35ff839b873ec13e`.
  Combined explorer, Book-static, and WMI-harness tests pass `24/24`; Python,
  shell, JavaScript, scoped-CSS, YAML, DOM, and diff checks are clean.
- Extended the WMI Book snapshot/build/integrity harness to carry the exact
  theorem stack, tag/informal registries, generator, APIs, and complete static
  explorer, and to reject drift, broken links/fragments, remote runtime
  assets, or an inexact built copy. No new WMI upload, allocation, full Book
  build, or built-HTML receipt was performed. The new manifest-only Book
  boundary is 1,359 files / 42,263,297 bytes at
  `8a6378db...970fe8b`. The previously frozen QR upload hash is now stale
  because the repository payload has changed; a new
  content-specific approval and snapshot are required before transport.
- The in-app browser surface was unavailable, so no visual/click-through
  browser result is claimed. Static DOM, reference-resolution, security, and
  interaction-contract tests are green; attached-browser smoke testing
  remains a publication gate.

## 2026-07-30 — Dependency graph v2 and premise paths

- Added the generated graph-v2 view for the exact 557-theorem QR closure:
  1,792 direct edges over 45 layers, with arrows oriented from prerequisite to
  dependent. Its 48 theorem roots are corpus roots, not additions to PA1–PA6
  or to the kernel foundations.
- For `PA00FW`, the graph records 101,296 distinct theorem-root-to-target
  paths. It exposes both a deterministic shortest witness (4 vertices / 3
  edges) and a critical dependency-depth witness (45 vertices / 44 edges),
  while the complete prerequisite cone contains all other 556 theorems.
- Integrated the reading page at
  `book/arithmetic-library/dependency-graph.md` and the static explorer at
  `book/_static/pa-proof-explorer/graph.html?target=PA00FW`; the latter links
  to the exact `tag/PA00FW.html` proof page. This is a navigation milestone,
  not an admission: `PA00FW` remains `pending_layered_closure`. No attached-
  browser validation is claimed here.
- Hardened the release surface after review. The generator now owns and
  hashes all 1,123 explorer files, rejects or prunes unexpected files anywhere
  in the subtree, and embeds the compact file-protocol graph payload only in
  `graph.html` rather than allowing Jupyter Book to inject it into every
  chapter. The final aggregate is
  `7f7d4ec08902ce3d3991aa6c4dc38cd32715a2145fc3486b6314b6dd063e2477`.
  Eleven explorer tests and sixteen Book/WMI harness tests pass; a full local
  Book build succeeds, and its integrity receipt reports identical 1,123-file
  source/built explorer trees with no broken relative links or fragments.

## 2026-07-30 — Approved full QR snapshot submitted to WMI

- Received content-specific authorization for dirty snapshot SHA-256
  `2bab0898a5bc628a0e1f06b5e6cdf56af86fe39c2fdbeaaa4147ac43d2c7faaa`.
  The deterministic archive contains 338 files, is 5,374,464 bytes, and binds
  its contents to base commit
  `a549a537cfe3d3d7e8ef292a49250c4308d12c5d` with `local_dirty=true`.
- Uploaded the frozen archive to WMI, verified its digest after transfer, and
  passed the source/extracted 9-test transport harness and Slurm test-only
  validation. Submitted job `187187`, suite `full`, selecting 136 gates on
  `cpu_idle` with one CPU, 32 GiB and a four-hour limit.
- The latest scheduler observation is `PENDING (Priority)`. This checkpoint
  records transport and submission provenance only: it does not report a
  replay pass, a pinned admission receipt, or an admitted quadratic-
  reciprocity theorem.

## 2026-07-31 — WMI fail-closed diagnosis and corrected QR payload

- Retrieved the final accounting and immutable logs for job `187187`.
  Slurm reports `FAILED`, elapsed `00:00:39`, exit code `1:0`. Gates 1--4 of
  the 136-gate full suite passed, including two full cut-closure replays of
  the scaled-inverse ladder. Gate 5 rejected the dependency audit because a
  mutation replacing the declared `succ_ne_zero` cut still checked; the
  remaining 131 gates were not run. This is an early hygiene failure, not a
  quadratic-reciprocity result.
- Confirmed that `prime_scaled_inverse_target_nonzero` never referenced
  `succ_ne_zero`. Removed only that redundant dependency and the matching
  expected-boundary entries; the theorem statement and tactic body are
  unchanged. The complete five-test scaled-inverse candidate suite now
  passes locally, including every-direct-cut mutation.
- Refreshed every affected exact receipt. The closure remains 557 nodes and
  45 layers, with 1,791 edges; graph SHA-256 is
  `2231ca4cde6931fad296513fb0c419e19beb7c37989d31fbf6cf01771597cb46`
  and candidate-source SHA-256 is
  `457327e29134e08fd8802a18b9e1a9e0e23fa84bb44f2934f1fcba466f6e6cb5`.
  Recursive expansion is 191,669 theorem occurrences with a 731,482-node
  lower bound. The rejected actual-target scaffold is `13,715/56`; the
  accepted dependency-consuming surrogate is `19,088/74` with
  `142,346/84` annotations/envelope depth.
- Regenerated all 1,123 Proof Explorer files at aggregate
  `6c47124a4a86c764d0e9af274cba9dfbc6df8a89c7327fe4744f49f097b93dd2`.
  The graph now has seven implicit packaging edges and 101,293 root-to-QR
  paths; all 8,557 explicit tactic references remain unchanged. Twenty-three
  focused topology, scaffold and Explorer tests pass, and the generator's
  byte-current check is green.
- Regenerated `peano-lab/APP_MANIFEST.sha256` and synchronized the local
  packaging identity to `a-279f7fd6f2b9`, build `2026-07-31a`. This is not an
  external deployment or theorem admission.
- Built the corrected WMI archive twice, byte-identically: SHA-256
  `989011c09d82dbbb239df43334e88553e1fb3e0d2f1033f93c5b8b1791851757`,
  338 members, 5,374,464 bytes, with exactly 136 selected gates. After new
  hash-specific authorization, uploaded it to its separate content-addressed
  WMI directory, verified snapshot provenance
  `b73f8e5d91e82d0c3d9fbb1acf846f699680f4f3 / local_dirty=false`, and passed
  Slurm test-only validation. Submitted full job `210714` on `cpu_idle` with
  one CPU, 32 GiB and four hours; its initial state was `PENDING (Priority)`.
  Submission and pending state are not proof receipts.

## 2026-07-31 — Unified native/model Peano terminal

- Added a model-free terminal host over the current `driver.LabSession`. It
  exposes all 384 theorem specifications, preserves proof/tutorial raw-input
  ownership, supports interactive and fail-fast repeated `-c` commands, and
  treats unfinished batch EOF as a non-result.
- Extended the already installed model launcher with a first-token selector:
  `pa native` dispatches to this worktree before model setup, while `pa model`
  and legacy bare `pa` retain the frozen 247-theorem diagnostic. The two
  `peano_lab` trees execute in separate processes and import paths.
- Replayed a complete native theorem-reuse example using `use mul_one`,
  `specialize`, `rewrite`, and `simp`; QED passed the unchanged independent
  kernel. No model artifact was verified or loaded on that route.
- Hardened automation boundaries: Python older than 3.10 is rejected before
  imports, Ctrl-C during replay returns 130 without a traceback, a closed
  output pipe is quiet but nonzero (141), and `--version` cannot suppress a
  repeated `-c` command stream. Seven focused terminal tests pass.

## 2026-08-02 — Conservative defined-notation Proof Explorer

- Completed the parallel definition-aware reading edition over the exact
  557-specification quadratic-reciprocity closure. Its persistent inventory
  contains 40 display definitions (`PD0001`–`PD0040`), 38 of which occur in
  the closure; `AllPrime` and `Sorted` have zero whole-schema matches. The
  edition covers 557 theorem pages and all 27,491 authored tactic lines. Of
  557 statements, 506 use at least one selected definition; 1,275 of 1,839
  proposition-bearing `have` or `suffices` commands are compacted.
- Measured aggregate theorem-statement text at 2,457,096 expanded characters
  versus 107,386 defined characters (95.63% reduction), and local proposition
  text at 1,971,403 versus 111,519 (94.34%). The longest statement falls from
  82,377 to 1,759 characters; the `PA00FE` line-15 `have` command falls from
  36,497 to 642.
- Kept the trust boundary explicit: the definition compiler, registry,
  persistent `PD` tags, expansion hashes, and generated pages are untrusted.
  Every changed formula is checked to expand to the same parsed native PA AST,
  and every changed local command exposes its exact replay line. The mixed
  graph adds 40 definition nodes and 1,725 notation edges, but proof paths
  retain the exact 557 theorem nodes, 1,791 proof edges, and 45 layers.
- Preserved evidence-level status from the explicit corpus: 240 nodes are
  public, 316 are `candidate_body_checked`, and only `PA00FW` is
  `pending_layered_closure`. The readable endpoint and definition pages do not
  admit quadratic reciprocity or change the kernel language.

## 2026-08-02 — Lean kernel synchronization and curation charter

- Corrected the trust account to include the independent
  `nasqret/peano-lab-lean` semantic soundness formalization. Its immutable Lean
  4.31/WMI job `211445` verifies the historical cut-free kernel; finite
  Python/Lean differential testing is recorded as correspondence evidence, not
  an exhaustive CPython equivalence proof.
- Recorded the GPT Pro adversarial finding precisely: malicious Python AST
  subclasses could override equality. The repaired checker accepts exact
  constructors and recursively validates terms and formulas; the permanent
  subclass mutation regressions remain green.
- Compared the old Lean mirror with this branch and found one material logical
  delta: production `Cut`, used by 329 of 384 published certificates. Extended
  the Lean syntax, `Derives` calculus, proof-producing checker, semantic
  induction, and canonical codec with that ordinary cut rule. Mirrored the
  current Python sources byte-for-byte and introduced `peano-lab-v2` artifacts.
- Local verifier matrix passes: 22 Lean 4.28 build jobs, 11 codec/mutation
  tests, 154 Python/Lean cases with zero mismatches or decode errors, both
  standalone sample acceptances, clean static audit, and unchanged axiom
  report. Exact source commit
  `ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2` subsequently passed pinned Lean
  4.31/WMI job `218358` in `00:03:03` with exit `0:0`; the collected receipts
  are preserved by evidence commit
  `8515336ab3b89ca6f0c8ab521d01745a220b5211`.
- Added `research/arithmetic-library/curation-policy.md` and M20G. The next
  edition freezes eleven P0 AST-first definitions, eliminates duplicate string
  builders, records relation API completeness, compiles readable statements
  and typed intermediate propositions immediately to ordinary formulas, and
  publishes paired expanded/readable receipts. Definition names remain
  untrusted syntax and never enter the object language or kernel.

## 2026-08-02 — Terminal QR replay audit and publication seal

- Re-queried Slurm rather than carrying the submission-time state forward.
  Corrected full job `210714` is terminal `FAILED`, elapsed `00:08:29`, exit
  `1:0`, on host `c4n2.cluster.wmi.amu.edu.pl`.
- Inspected the immutable stdout, stderr and JSON result in the
  content-addressed WMI directory for snapshot
  `989011c09d82dbbb239df43334e88553e1fb3e0d2f1033f93c5b8b1791851757`.
  Gates 1--14 passed. Gate 15 rejected the direct-edge mutation audit because
  replacing `odd_upper_remainder_reflection -> add_succ_left` still produced
  a checking certificate; the remaining 121 gates were not run.
- Classified the result narrowly: it exposes a non-minimal declared
  dependency and blocks admission. It does not show a kernel-soundness bug,
  does not complete the 136-gate suite, and does not admit quadratic
  reciprocity.

> **Parallel-history chronology.** The following model-v3 stream was merged
> intact from the parallel `peano-lab` line. Its dates deliberately restart at
> 2026-07-29 and advance through a separate 2026-08-02 terminal record. The
> restart is document ordering, not a rollback of the QR/curation state above;
> the last dated entry in each stream is authoritative for that stream.

## 2026-07-29 — Complete-library model-v3 launch candidate

- Replaced the narrow model-v2 curriculum with a distinct, content-bound
  model-v3 authority over all 247 kernel-checked theorems. Each authored
  trajectory sees exactly its declaration-order predecessor prefix, producing
  8,494 exact replay transitions. A separate deterministic 70,000-row
  synthetic lane covers 51 schemas and balances 14 root tactic heads with an
  `intro` ceiling of 20%. Catalog material is forced into training; validation
  and test remain synthetic-only, and target formulas are checked for leakage
  in every intermediate goal rather than only at session boundaries.
- Added a lossless v3-only `shared-declarations-v1` state representation after
  the largest exact proof produced a 122,546-token legacy prompt. The compact
  form factors repeated exact context declarations and targets into canonical
  first-occurrence tables and reconstructs the original one-line goals
  byte-for-byte. Strict JSON canonicality, index/focus checks, table-use checks,
  reserved-marker rejection, and a 44,000-character fail-closed bound preserve
  the replay and attestation boundary. V1/v2 prompt bytes remain frozen. The
  pinned Qwen tokenizer audit over all 222 transitions in the stress proof has
  median 17,444, p95 26,662, p99 28,537, and maximum 29,111 tokens including
  tactic and EOS, leaving 3,657 tokens below the native 32,768 limit.
- Kept the ordinary batch trace limit at 16 MB. A host-only reviewed override,
  capped at 128 MiB and unavailable in JSON requests, is granted solely to the
  exact model-v3 catalog generator and to builder replay after strict catalog
  trajectory validation. Limit failures remain transactional and concise.
- Registered the WMI Qwen3-1.7B Base experiment at a pinned model revision,
  rank-32/alpha-64 LoRA, effective batch 32, two epochs, 80,000 maximum train
  rows, 6,000 maximum evaluation rows, and native 32,768-token contexts. The
  guarded prepare/train/evaluate jobs have 12/20/6-hour limits; preparation
  performs exact generation, replay, independent attestation, full tokenizer
  audit, and an A100 smoke before training can start. No model-v3 job or result
  is claimed at this checkpoint.
- Regenerated the committed v1 corpus with its required CPython 3.10.0 after
  the batch source changed. Its 1,692 sessions and 13,344 transitions now have
  run fingerprint
  `6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`;
  train, validation, statistics, manifest, semantic-tree, and raw-stream
  SHA-256 values are respectively
  `4e0053e1da89a32043cdfad98e6e6924ce19a6748a914c55095308f48dd2ad54`,
  `abe0aa84de861aae9a72a173fd1114cf0a99114a8f4f9a6d6019fb3433d94e69`,
  `68affad0cd91e0ad4fadda28901b083b6e45f4694791aa1d24b42a82183c04ca`,
  `a89a2d2bdbe6362c17ece6b886ab5eba1dbd7af2b04ddd32d86d2fcccdde3d95`,
  `55a6e70ce5a3ffe855866beb04b7441a85c58d6ac7c7bb9de727d1fefe14d250`,
  and `c88a05343d27ded77ba871bd3552ddd099817ef78e6fbfa2a959b8a2e2aea306`.
  Browser build `2026-07-29k` packages application `a-77df7c0860bc`; it has not
  been deployed.
- Final local gates: Peano Lab 1,288 passed/one skipped in 1,259.11 seconds;
  Lambda Lab 360 passed plus 36 subtests; all 287 documented commands replay;
  the vault verifies 247 lemma notes within 327 notes and 3,286 resolved links;
  the manifest and atlas drift checks pass; and a clean 38-source Jupyter Book
  render succeeds without warnings. Remote synchronization, training, and
  evaluation remain subsequent steps rather than inferred successes.

## 2026-07-29 — Model-v3 preparation fails closed and gains a schedule prepass

- WMI job `172536` validated the pinned A100 environment and completed the exact library lane:
  8,494 transitions and 247 independently checked QED footers. Synthetic generation then stopped
  after 1:02:34 with exit 2 because one ring root normalized to coefficient 132, above the tactic's
  reviewed limit of 128. No partial synthetic corpus was published and no training or evaluation
  job was submitted.
- The repaired ring domain contains exactly 2,396 safe base-7 coefficient tuples. Sixteen compact
  closed-zero tags extend it to 38,336 distinct safe statements. The four gate-free induction
  schemas now each use a 4,096-value closed-zero tag, correcting their unintended collapse to only
  four canonical roots. The repaired schema catalog is version 2, distinct from the failed job's
  version-1 identity.
- A model-free prepass now plans and canonicalizes the entire schedule before proof execution or
  output creation. It rejects duplicates, exhausted domains, inexact filling, `intro` overflow,
  and head imbalance; execution must reproduce its counts and digest exactly. For the registered
  seed, 70,000 rows form 32,600 distinct roots across all 51 schemas, with each of 14 heads used
  2,328 or 2,329 times. The ordered schedule SHA-256 is
  `79d2704eab6eb73205ff2234f55f0d4a7e034176fe8dc8649c6950ff499d547b`; it requires no duplicate
  or overlong-session skips.
- A maximum-budget audit found one numeric candidate exactly equal to a sealed evaluation target.
  A dedicated typed and counted exclusion now skips only that valid collision; malformed schema
  output still fails. The 100,000-row preflight completes with 46,574 unique sessions, balanced
  heads, and exactly one held-out skip.
- WMI preparation now starts with the synthetic generator, whose whole-schedule prepass runs before
  either corpus begins expensive proof replay. A future schedule-contract failure therefore stops
  in seconds instead of following the hour-long library phase. An upfront empty-data-directory gate
  also rejects every stale artifact before either generator starts.
- Final local gates: Peano Lab 1,298 passed/one skipped in 1,275.58 seconds; Lambda Lab 360 plus 36
  subtests; 19 focused generator tests and 23 WMI/config tests; 287 documented commands; 247 vault
  lemma notes and 3,286 links; and a warning-free 38-source Jupyter Book rebuild.
- Full WMI preparation, training, and independent kernel evaluation remain pending. The balanced
  object currently established is the deterministic plan, not a published corpus or trained
  model.

## 2026-07-30 — Model-v3 separates replay, selection, optimization, and judgment

- WMI retry `172729` generated the two expensive proof sources: 32,600 independently checked
  synthetic sessions with 70,000 transitions and 247 declaration-prefix library sessions with
  8,494 transitions. The combined builder and historical attestation were still running at this
  checkpoint. The job had an A100 allocation because it shares the registered preparation script,
  but the GPU was idle and no transformer optimizer step had run.
- Replaced the draft row-prefix curriculum with a deterministic whole-session selector. Every one
  of the 8,494 catalog transitions is mandatory. Synthetic selection has a 12,288-row ceiling,
  anchors all 51 schemas, adds balanced complete rounds across all 14 root heads, and is stable
  under input reordering. Model-v3 rejects `run.max_train_samples` and requires the selection seed
  to equal the training seed.
- Added exact token-exposure accounting for the selected curriculum. The pinned tokenizer binds
  every row's token IDs and reports linear and squared sequence exposure, sequence extrema, and
  supervised-completion extrema; all receive explicit fail-closed limits. This replaces row count
  as the only compute gate.
- Implemented the exact completion-only objective with indexed vocabulary logits. A causal logit at
  position $i$ scores the supervised label at $i+1$; only that union of shifted positions is
  requested from Qwen. FP32 summed cross entropy is normalized by the exact supervised-token count
  across the accumulation window. The code rejects malformed suffix masks, unsupported model
  forwards, ambiguous multi-device execution, and incorrect token accounting.
- Added an immutable historical corpus seal and current-source eligibility record. The seal accepts
  exactly twelve data artifacts and three same-job reports, rejects filesystem aliasing and mixed
  provenance, publishes atomically without replacement, becomes read-only, and binds all bytes to
  the historical clean commit and Slurm job. A newer trainer must independently verify the seal and
  match its current compiler, kernel, prompt, held-out, and 247-theorem identities before reuse.
- Split the new WMI path into a sealed-preparation job, a one-shot training job, a fixed-budget
  four-goal search job, and a model-free independent replay. Preparation performs no proof replay;
  it checks eligibility and all selected tokens, then exercises the longest sequence and largest
  completion through a real indexed-loss LoRA update/save/reload smoke. Training repeats the report
  cross-check and must match a precomputed one-GPU step schedule. Independent replay accepts only
  the exact evaluator-v4 goal/search authority and reruns every claimed proof through Peano Lab's
  kernel.
- Result-dependent identities remain deliberately blank until artifacts exist: the corpus content
  digest, sealed-preparation/train/evaluation job IDs, selected token totals, optimizer steps and
  losses, adapter hashes, solve results, and replay-attestation digest. The next honest status
  transition is “optimizer stepping,” not “an A100 is allocated.”
- Documentation verification is green: 38 Jupyter Book sources build with warnings as errors; 194
  deep links and 47 sessions containing 287 commands replay; 17 focused book tests pass; the vault
  verifies 247 generated lemma notes in a connected 327-note/3,286-link graph; the new seal,
  eligibility, sealed-preparation, replay, and submit command-line help surfaces match the text; and
  `git diff --check` reports no whitespace errors. None of these static checks is reported as a GPU
  training result.

## 2026-07-30 — Exact-corpus preparation recovery

- Job `172729` completed and published the 78,494-row split, but its attestor
  was still in the pre-replay validation scan after 7h58m. With the measured
  5h07m independent builder entirely ahead, the remaining allocation could not
  produce all three required reports. It was cancelled without changing the
  twelve corpus files; no report or optimizer step existed.
- The continuation entry point now accepts only the exact twelve-file set and
  manifest SHA-256
  `ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983`.
  It does not regenerate data. WMI synchronization explicitly preserves that
  unsealed directory.
- A four-hour subprocess watchdog was shorter than the measured first build.
  Job `173037` was stopped after 6m30s before it could reach that deterministic
  failure. Commit `5faa3d27cbaf522198ffa1bdcd11fa9d57341658`
  sets the replay watchdog to eight hours and tests the bound.
- Replacement preparation job `173040` is running from that clean commit. Its
  purpose is independent replay, tokenizer audit, and runtime smoke; transformer
  optimization has not started.

## 2026-07-30 — Prelaunch optimizer and evaluation-chain safeguards

- The one-shot trainer now saves the completed adapter and tokenizer before
  its explicit full validation pass. The final manifest is still withheld
  until evaluation and every immutable-input recheck passes, but a late
  validation timeout can no longer erase the only learned tensors.
- Scheduled model-v3 evaluation now equates the adapter manifest's producer
  job, `PEANO_TRAIN_JOB_ID`, and the recorded submission-ledger predecessor before loading
  weights. The report carries that binding and independent replay checks it.
  Interactive proof-request jobs use a distinct completed-manifest binding and
  do not pretend to have an evaluation-chain dependency.
- The combined evaluator, proof-request, replay, trainer, and same-base-control
  regression set passes 144 tests.

## 2026-07-30 — Closed two-source seal bootstrap

- The historical seal bootstrap now admits only its CLI and standard-library
  module in an exact cache-free inventory; package markers, `.pyc`, aliases,
  extras, and mutations fail closed.
- A launcher embedded in the Slurm script stable-reads, hashes, compiles, and
  executes the same CLI bytes under isolated Python. The CLI then repeats the
  module/inventory check, closing the execute-before-self-hash gap.
- Forty-nine focused seal tests, shell syntax, an adversarial pathname
  replacement probe, and the exact standalone pipeline pass locally. Remote
  staging remains untouched until job `173040` finishes.

## 2026-07-30 — Fail-closed Trainer completion and recovery filesystem proof

- Pinned Transformers source review showed that accumulation is already
  normalized by the whole window's supervised-token count, while an inherited
  Accelerate accumulation divisor could divide it again. Production and smoke
  now require one CUDA process, BF16, no distributed/Dynamo plugin, Trainer's
  configured accumulation, and Accelerator divisor one. Training fails if
  `num_items_in_batch` is missing.
- Trainer's terminal callback would save optimizer/scheduler/RNG state even
  with `save_steps` beyond the 650-step run. Model-v3 now uses
  `save_strategy="no"` and `eval_strategy="no"`; only explicit adapter
  safetensors, six non-resumable recovery snapshots, and the explicit final
  validation remain.
- Built-in clipping happens before `on_pre_optimizer_step`, so model-v3
  disables it. The first callback checks every raw gradient, strictly clips at
  norm 1.0 with non-finite errors enabled, checks post-clip gradients, and
  records all expected boundaries and norms.
- A v3 `training_evidence` record now binds step agreement, runtime and actual
  Trainer arguments, exact finite history/metrics, initial-versus-final
  trainable tensor fingerprints, adapter changes, and closed artifact hashes.
  V3 inference and same-base comparison reject missing or inconsistent
  evidence before importing the model framework; strict JSON rejects duplicate
  keys, links, changing files, and NaN/Infinity.
- Scheduled training now runs a retained atomic no-replace probe on the exact
  recovery output filesystem and passes its canonical report into the trainer.
  Local `renamex_np(RENAME_EXCL)` tests pass; the real WMI
  `renameat2(RENAME_NOREPLACE)` `/work` probe remains pending because the VPN
  is disconnected. No transformer optimizer step has started.

## 2026-07-30 — Saved-policy admission and one-shot final publication

- Model-v3 no longer treats a successful PEFT save as proof that the saved
  directory is the terminal learned policy. Three deterministic probes are
  selected from the admitted train/validation populations and bound to the run
  identity. The live policy records canonical PEFT tensor and exact indexed
  loss/projected-logit fingerprints; after Trainer/model release, one fresh
  local-only base/tokenizer/adapter load must reproduce them exactly and must
  differ from its disabled-adapter base on at least one probe.
- The admission object joins the pinned base commit and pristine configuration,
  individual adapter files, complete adapter/tokenizer tree digests, `cuda:0`
  runtime, run identity, and completed-training artifact hashes. Model-v3
  inference and the same-base control require it before heavy framework import.
- A pinned-framework audit found that `bf16_full_eval=true` casts the whole
  model to BF16, including PEFT's normally FP32 LoRA tensors. Production and
  smoke now keep BF16 autocast but set full-eval casting to false, and compare
  tensor populations after serialization and explicit evaluation.
- Final output is claimed by exclusive directory creation. Adapter/tokenizer
  partial trees, run identity, and final manifest are fsynced, protected, and
  atomically published without replacement; output and parent inode/device/mode
  identities are rechecked before completion. The expected optimizer-step
  count must be divisible by the logging interval before allocation.
- Artifact closure now enumerates every filesystem node rather than filtering a
  glob. It rejects symlink components/directories, specials, cross-device nodes,
  and hard links; hashes through stable `O_NOFOLLOW` descriptors; compares a
  second inventory; and requires exact 0555/0444 protection for v3 callers.
  The protection option is intentionally off for historical v1/v2 adapters.
- The focused admission/completion suite passes 81 tests, and the smoke plus
  admission suite passes 59 tests. The preparation report verifier, full suite,
  real WMI `/work` probe, A100 smoke, and optimizer training remain pending at
  this checkpoint; no loss or trained-model claim is made.

## 2026-07-30 — Model-v3 launch-contract wiring audit

- Prompt-v3 attestation and the model-v3 curriculum are now an equivalence:
  either both are present or both are absent. The trainer checks this before
  importing Torch, PEFT, or Transformers, so a v3 prompt cannot enter the
  legacy training lane by omitting its curriculum.
- After saved-policy admission and all slower source/report checks, the trainer
  verifies both protected artifact trees once more immediately before the
  exclusive no-replace manifest publication. The direct generation and
  pretrained-base comparison loaders likewise verify their adapter/tokenizer
  trees both before and after heavy model loading.
- Recovery publication now accepts exactly mode `0555` for directories and
  `0444` for regular files. These mode checks are provenance and
  accidental-corruption gates, not security against a hostile process running
  as the same filesystem owner.
- The focused wiring-audit suite passes 89 tests. This closes local launch
  contract gaps only: no model-v3 optimizer step, trained adapter, loss, or
  proof-quality result is claimed.
- The frozen-tree local gate then passed 540 focused model-v3 tests, all 1,707
  Peano tests with one intentional skip, and all 360 Lambda tests plus 36
  subtests. The warning-as-error 38-source book, 194 deep links/47 sessions/287
  commands, and the 327-note/3,288-link vault are green. The WMI `/work` probe,
  A100 smoke, optimizer training, and kernel-judged model evaluation remain
  pending rather than inferred from these local results.

## 2026-07-31 — The selected-token ceiling failed closed before model loading

- Historical continuation `173040` completed independent replay, full-population
  tokenizer audit, and A100 runtime smoke. Seal job `213641` then published and
  independently verified the immutable 15-file corpus at
  `checkpoints/corpora/peano-policy-v3-173040`, with content SHA-256
  `7b22bdf083894e3d87b84fc463ff537a75eeecba8e34098429db215592ec6b5b`.
- The first current-source sealed-preparation attempt, WMI job `214264`, reached
  the selected-curriculum token audit and failed closed at its first budget
  comparison: 73,446,475 train tokens exceeded the reviewed 70,000,000-token
  ceiling. The batch stopped before the indexed-loss runtime smoke or model
  loading. It produced no accepted token-audit/runtime-smoke chain and no
  optimizer step, checkpoint, loss, adapter, evaluation, or proof-quality result.
- Passing row-count and historical full-population audits did not imply that the
  whole-session selected curriculum fit its current linear budget. Because the
  linear comparison failed first, this run does not establish the quadratic or
  supervised-completion gates either. The reviewed retry raises only
  `max_train_tokens` to 74,000,000, leaving 553,525 tokens (about 0.754%) above
  the measured exposure; every other compute, context, evaluation, and runtime
  gate remains unchanged and must pass afresh.
- The configuration change creates a new current-source identity. Any
  job-`214264` eligibility evidence is bound to the rejected configuration and
  cannot authorize training. The immutable historical corpus seal remains
  unchanged, but a fresh clean deployment and new sealed-preparation job are
  required before the one-epoch Qwen3-1.7B optimizer run may be submitted.

## 2026-07-31 — Exact admission exposed a retained Accelerate forward wrapper

- Reviewed-ceiling retry `217123` passed corpus eligibility and published a
  complete token audit for 20,765 train rows: 73,446,475 total tokens,
  415,247,631,205 squared-token exposure, 29,111 maximum sequence tokens, and
  936 maximum supervised tokens. The unchanged 74-million, 2.3-trillion,
  32,768, and 1,024 gates all passed.
- The job then performed its representative LoRA updates and one real
  `CompletionOnlyTrainer` step/evaluation, but failed before publishing the
  smoke report. Byte-exact comparison had already proved equality of the live
  PEFT population, saved safetensors, and freshly loaded PEFT population. The
  next semantic comparison rejected the fresh outputs.
- The mismatch was structural. Accelerate 1.8.1 prepares a BF16 Trainer model
  by replacing `model.forward` with autocast plus FP32 output conversion and
  retaining `_original_forward`. Deleting Trainer does not undo that mutation.
  The live snapshot therefore used the prepared forward, while the fresh PEFT
  reload used the bare inference forward; exact dtype/raw-byte fingerprints
  were guaranteed to disagree.
- The repair uses Accelerate's public `unwrap_model` with both
  `keep_fp32_wrapper=False` and `keep_torch_compile=False`, requires the exact
  same single-process model object and original forward, and makes snapshot
  capture reject any retained wrapper. Smoke and production share this path.
  No tolerance was introduced: exact tensors, tokenization, loss/logit bytes,
  and adapter-versus-disabled-base checks remain intact. A new sealed-
  preparation job is required; no production training job has run.
- Local verification is green: 73 focused admission/smoke tests passed with
  one expected skip; the wider preparation/documentation selection reports
  140 passed with one skip; the complete Peano suite reports 1,764 passed with
  five skips; Lambda Lab reports 360 passed plus 36 subtests. The warning-as-
  error book, all 287 documented commands, the 248-entry knowledge base, and
  the 327-note/3,288-link vault also pass.

## 2026-08-01 — Repaired preparation passed; completed predecessor made explicit

- Fresh WMI job `217768` completed in 3h53m05s on one A100 with scheduler state
  `COMPLETED`, ordinary exit `0:0`, and derived exit `0:0`. It passed sealed-corpus eligibility,
  reproduced the accepted 20,765-row/73,446,475-token curriculum, completed representative LoRA
  updates plus a real Trainer step/evaluation, restored the bare forward, and passed exact
  saved-policy admission and fresh reload. Independent verification accepts all three terminal
  reports. Smoke train/evaluation losses were `2.7942631244659424` and `0.8226498961448669`; they
  are infrastructure diagnostics, not a production learning result.
- The first production dry-run then exposed a scheduler/API mismatch rather than a model failure.
  WMI's Slurm controller has `MinJobAge=300`: persistent `sacct` still retained the successful
  allocation row, but the controller had purged it, so a newly attached
  `--dependency=afterok:217768` was rejected with “Job dependency problem.”
- Submission now distinguishes the two authorities. `--afterok` is only for a live producer and
  emits an edge whose dependent job may run only if that producer succeeds. `--completed-predecessor` requires exactly one
  canonical `JobIDRaw|State|ExitCode|DerivedExitCode` row with `COMPLETED|0:0|0:0`, preserves the
  job ID in the environment and append-only ledger, rechecks the exact same-source predecessor and,
  where required for preparation-to-training, its terminal reports, and emits no impossible
  scheduler edge. Accounting is re-read immediately
  before held submission; every failed, missing, duplicate, malformed, nonzero, or mismatched row
  fails closed.
- Production optimization is still unstarted at this checkpoint. The next legitimate event is a
  clean deployment followed by one fresh sealed preparation under that exact source. The guarded
  training submission may use only that new job; exact provenance deliberately forbids relabelling
  `217768` across the submission-fix commit.
- The same final audit corrected a latent schedule mismatch. Exact selection admits 20,765 rows,
  so microbatch one with accumulation 32 yields 649 optimizer updates, unlike the old 20,782-row
  fixture that yielded 650.
  Logging every 10 steps would have failed the reviewed terminal-boundary preflight before model
  allocation. Production now changes only the observation interval to 11 because
  `649 = 11 × 59`; batching, warmup (33 steps), recovery snapshots, objective, and optimizer are
  unchanged. The evidence contract still requires a periodic finite-loss record at the final
  update rather than accepting a partial last logging interval.
- Final local admission is green: 1,769 Peano tests passed with five expected skips; Lambda Lab
  passed 360 tests plus 36 subtests; all 38 book sources built with warnings as errors; 194 links,
  47 sessions, and 287 commands replayed; and the 248-entry knowledge base plus
  327-note/3,288-link vault verified. The executed fake-Slurm harness covers completed/live modes,
  the second accounting read, ledger preservation, and held-submit ordering. No production or
  preparation job was active when these gates completed.

## 2026-08-01 — Same-source training is live; observation remains read-only

- Fresh post-fix sealed preparation `217851` completed in 4h01m09s under clean source
  `4d44609ee32d5d28726c082ef7b5649c0a1107a6`. It passed the exact eligibility and token audits,
  representative LoRA and Trainer smoke, restored-bare-forward admission, fresh reload, and the
  independent terminal-report verifier. Its smoke losses (`2.8299612998962402` train and
  `0.8195649981498718` evaluation) remain lifecycle diagnostics only.
- Guarded same-source production successor `217859` is running on one A100-SXM4-80GB. The audited
  schedule has 649 optimizer updates, 20,765 selected rows, 73,446,475 train tokens, effective
  batch 32, and non-resumable recovery publications every 100 steps. A live observation during
  dashboard validation reached step 196/649 with one step-100 recovery tree. This observation is
  not a terminal result and will naturally become stale.
- Added the Peano Lab Training Observatory: a dependency-free browser UI backed by a standard-
  library server bound only to `127.0.0.1`. One serialized collector runs a fixed read-only SSH
  program, projects bounded Slurm/log/artifact evidence, and keeps the last good snapshot visibly
  stale across VPN failures. The browser has no SSH credential, arbitrary command/path, scheduler
  mutation, or remote write surface.
- The UI deliberately refuses two seductive false claims. Shuffling plus accumulation means no
  exact “current dataset row” is observable, so it shows representative admitted catalog samples.
  Redirected stdout has not flushed the production Trainer dictionaries, so the loss curve is
  empty and status is `buffered`; the predecessor's one-step loss is separately labeled admission
  smoke. Exact flushed points or terminal-manifest evidence will backfill without inference.
- The focused parser/server/web contract reports 25 passes, covering hostile parsing, bounds,
  stale-cache semantics, loopback routing, prohibited methods, security headers, self-contained
  assets, JavaScript syntax, accessible loss fallback, and honest sample labeling.

## 2026-08-02 — Paired model-v3 smoke completed, then failed closed at report replay

- Production job `217859` completed, and the admitted rank-32 Qwen3-1.7B adapter was available to
  the frozen evaluator. The single-evaluation-owner guard was preserved: trained job `218171` ran
  first and completed in 3m51s; a watcher then submitted revision/configuration-pinned pretrained
  comparison `218172`, whose report declares no PEFT adapter and which completed in 4m20s. Total
  sequential GPU evaluation time was 8m11s.
- The immutable raw `k=1` reports say 3/4 for the adapter and 0/4 for the base. The adapter found
  `norm_num` (98 nodes), `exists 5; norm_num` (29 nodes), and
  `intro n; rewrite PA3; simp` (10 nodes). Each script independently replayed through the kernel
  against its original formula and the actual model-v3 capabilities. The only genuinely
  induction-heavy target, `forall x. exists y. x * (x + 1) = 2 * y`, was not solved. The base
  produced 32 malformed sequences and executed no tactics.
- Canonical replay of the trained report refused to publish an attestation. Prompt rendering and
  the report's separate library record used the full 247-theorem authority, but the nested
  `base_policy_identity.environment` serialized the legacy four-field projection. It omitted
  `library_identity_sha256`, `library_full_identity_sha256`, `library_prefix_length`, and
  `library_size`, so it was not byte-for-byte the exact model-v3 authority required by the replay
  gate.
- This is a reporting/identity defect, not evidence that an invalid proof passed: all three scripts
  are independently kernel-valid. It is nevertheless scientifically fatal to the whole-report
  attestation. The raw reports remain immutable, the ordinary verifier remains strict, and the
  3/4-versus-0/4 score is quarantined. A separate, versioned compatibility replay must pin the
  exact historical report hash, source commit, evaluation job, source inventories, legacy
  projection, reconstructed full-library values, and every claimed proof. No accepted pass rate,
  broad PA capability, or induction capability is claimed before that attestation exists.

## 2026-08-02 — Separate immutable admissions completed

- The historical recovery did not modify the trained report or weaken the ordinary replay gate.
  Version-pinned `trained-compatibility-replay.json` requires the exact report hash, source commit,
  evaluation job, legacy projection, reconstructed complete environment, and historical source
  identities. It passed and independently replayed all 3/3 proof claims. Its embedded attestation
  SHA-256 is `e900a10241db0451992313eb2a7b0341911a7a71cd8af91e831a279874afda56`.
- A distinct `pretrained-base-replay.json` also passed. It validated the declared pretrained-policy
  identity, comparison provenance, goal/search budgets and accounting, and correctly observed zero
  proof claims. Its embedded attestation SHA-256 is
  `056519bc3598a390526fdf9054aa38090d499f7f837af0a2ace7af8caaa560e7`.
- These separately scoped immutable admissions release only the narrow frozen four-goal `k=1`
  launch-smoke result: trained 3/4 versus the revision/configuration-pinned, no-PEFT-reported
  pretrained comparison's 0/4. The ordinary trained-report replay still
  rejects the historical incomplete nested environment, by design. The suite is too small for a
  statistical or broad capability claim; all three proofs are shallow, the induction goal remains
  unsolved, and no causal superiority conclusion is recorded. A deterministic baseline, larger
  hidden induction-rich suite, and repeated controlled runs remain pending.

## 2026-08-02 — The paired layer fixes the admissible wording

- Final `paired-launch-smoke-attestation.json` cross-binds the exact training manifest (SHA-256
  `caa5569c98ed9ea048d413301b803c39011957d1c97307e5b109846989e18569`, expected/actual 649
  optimizer steps), both reports, both producer attestations, source commit, and jobs
  `217859`/`218171`/`218172` under the same goals, seed, and search limits. Historical Git lookup
  verified 36 trained-semantic, 36 pretrained-semantic, 61 trained-evaluation, and 62
  pretrained-evaluation entries, comprising 62 unique source blobs with all overlaps equal.
- The paired artifact passed with result `paired_launch_smoke_admitted`. Its embedded attestation
  SHA-256 is `9b33b4e488f14e38fc7c5a122410d53e9e1123409dcccafdc73e0a8ab1a14bae`; its file SHA-256 is
  `cdd20cc6e97ff442cff1c476135963f726b740372223f6eac72335543f6c11ba`. Strengthened producer
  embedded hashes are `e900a10241db0451992313eb2a7b0341911a7a71cd8af91e831a279874afda56`
  (trained) and `056519bc3598a390526fdf9054aa38090d499f7f837af0a2ace7af8caaa560e7`
  (pretrained comparison).
- The admitted wording is intentionally narrower than “exact base.” Job `218172` is a
  revision/configuration-pinned pretrained comparison whose report declares no PEFT adapter. Its
  base weight shards were not content-hashed before and after loading, so bit-for-bit base identity
  is not attested. The reports also omit complete per-call raw generation, extraction, and executed-
  edge transcripts; candidate attribution relies on byte-pinned historical producer/source/job
  records. WMI completion is additionally observed in retained `sacct` and log-bundle artifacts,
  but Slurm does not cryptographically authenticate those scheduler observations.
- The result remains the narrow frozen four-goal `k=1` smoke, 3/4 versus 0/4. Three proofs are
  shallow and kernel-replayed; the induction theorem is unsolved. This does not establish a
  bit-for-bit base comparison, causal training effect, statistical result, broad PA ability, or
  induction capability.

## 2026-08-02 — Current base merged and conservative authorities sealed

- Merged the current `peano-lab` base into the quadratic-reciprocity campaign
  while retaining the 384-theorem native runtime and the historical training
  boundaries. Model-v2 remains frozen at its exact 56-theorem authority;
  model-v3 remains frozen at the first 247 declaration-order theorems. Live
  catalog schema-v3 rows are accepted only as an append-only superset whose
  projected first 247 rows reproduce ordered root
  `eb4775dfd181dc5e45bec463a93f14b0ea9d02501c40c5167b7cae77cd4ff432`.
  Dataset loaders and generators now reject native theorem index 247 as a
  model-v3 catalog target.
- The selected merged integration matrix passed 1,177 tests with five expected
  skips in 348.53 seconds inside the sandbox. The six loopback dashboard-server
  tests passed separately with socket access, for a combined 1,183 passes and
  five skips. Full 56-theorem model-v2 replay, all 247 strict model-v3 prefix
  environments, historical identity digests, catalog corruption, appended-row
  rejection, browser/corpus/deployment contracts, and the incoming training
  and evaluation stack are covered.
- The 45-source Jupyter Book rebuilt successfully. Its deterministic integrity
  report covers 2,323 HTML pages, 2,285 copied explorer files, 557 theorem tags,
  40 definition pages, and zero broken, escaping, unsafe, or remote-runtime
  links; both explorer trees are byte-identical to source. The 385-record
  arithmetic catalog, explicit and defined explorer hashes, 149-source Peano
  application manifest, historical corpus release, and all model-v3 evaluation
  evidence checksums pass. The pinned browser vendor mirror also rehashed and
  the application assembled successfully in `_deploy/peano-lab` under release
  `a-cd3e54b68949`; no deployment was performed. The vault verifies 384
  generated lemma notes, 475 total notes, and 4,825 resolved links.
- These are repository-integration and provenance results. They do not change
  the QR status: jobs `187187` and `210714` failed closed at dependency-
  minimality gates, so the 557-spec closure still has no complete 136-gate WMI
  receipt and quadratic reciprocity is not admitted as a public native theorem.
- The first GitHub merge-ref CI run exposed one optional-dependency boundary:
  core CI installs `pytest` but not PyTorch, while three newly merged training
  test modules imported `torch` unconditionally during collection. They now
  use the repository's existing `pytest.importorskip("torch")` convention.
  With PyTorch present all 96 affected tests pass; with its import deliberately
  blocked, the three modules skip cleanly instead of aborting collection.

## 2026-08-03 — Dependency hygiene and Linux CI repair

- The failed full GitHub run ended with 11 failures after 2,401 passes and 12
  skips. The failures separated into three stale structural/catalog contracts,
  four useful dependency-minimality mutations, and four Linux/provenance
  portability failures; no kernel-soundness failure or QR admission occurred.
- Four unused dependency edges were removed without changing a theorem
  statement: `gauss_signed_half_magnitude_injective -> add_assoc`,
  `odd_upper_remainder_reflection -> add_succ_left`, and the two
  `pair_order_iteration_* -> add_comm` edges. The full Wilson adversarial
  mutation gate passed in 416.14 seconds; Gauss mutation gates, theorem-body
  contracts, QR topology checks, and explorer contracts are green.
- The live closure is now 557 nodes, 1,787 direct edges, and 45 layers. Its
  graph/source SHA-256 values are respectively
  `98a36450cfe1de29c20be67a1c5f65c8064e9f9eec5368ab769065f910008698`
  and
  `23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1`.
  Recursive expansion has 191,648 theorem occurrences and a 731,423-node
  lower bound. The exact-marker surrogate checks at `19,066/74` nodes/depth.
  Earlier 1,791-edge WMI records remain immutable descriptions of their
  submitted payloads.
- Both proof explorers were regenerated and checked. The explicit explorer's
  1,123-file aggregate is
  `50c1d143cf6008d3bce737c2e7c0f84fc4ff6eff33978f7690fa22409db3be8b`;
  the defined explorer's 1,162-file aggregate is
  `f77c63e101f8cdf47182160633585a7a522210805d8f239a357fb2fdc94c72a1`.
- Linux CI now checks out complete Git history for pinned provenance rehashes,
  rejects staged-report replacement with stable metadata checks, and uses
  portable symlink-safe test cleanup. The formerly monolithic Peano suite is
  deterministically partitioned into eight source-byte-balanced pytest shards;
  the original required check name remains as a fail-closed aggregate job.

## 2026-08-03 — Peano Hydra was preregistered as a falsifiable campaign

- Added the binding `docs/PEANO_HYDRA_DESIGN.md` and H0–H6
  `PLAN/11_peano_hydra.md`. The kernel remains the only positive authority;
  native search, retrieval/ranking, Qwen, Codex, Vampire/E/SMT, translations,
  and reconstruction are explicitly untrusted.
- Corrected the scope claim before implementation: standard Heyting arithmetic
  is not decidable. A Hydra decision claim requires a frozen restricted
  fragment and independently justified negative evidence; otherwise the result
  is a sound theorem prover that may return `unknown`.
- Froze the experimental laws in advance: ordered library epochs,
  whole-lineage test sealing, complete evidence bundles, symbolic critical
  frontiers, typed macros that compile to public Peano commands, and a
  one-shot matched-compute `S`/`S+R`/`H` comparison.
- The historical four-goal Qwen smoke and any Codex teacher pilot remain
  regression/interface-headroom evidence only. Neither can support the final
  model claim. Future quadratic-reciprocity work belongs to a new epoch and
  requires complete development-lineage masking if evaluated.
- Added the explanatory Jupyter Book chapter and connected Obsidian notes. No
  Hydra code, benchmark, training run, or capability result was created in
  this documentation milestone.

## 2026-08-03 — The pre-H0 Hydra core closed its first checked loop

- Added `training/peano_hydra` outside the trusted package. Identified heads
  must share one exact execution authority and fixed quotas; stable first-wins
  merging never reallocates quota. Macro heads accept only one explicit
  structural surface line. Fixed, null, recorded-trace, and existing Qwen
  adapters all cross the same untrusted candidate protocol; a future Codex or
  solver adapter must do the same.
- Every proposal records the complete canonical goals, state digest, provider
  identity, gate decision, requested quota, head-returned and admitted tactic
  lines, duplicate suppression, and sanitized failure. It does not retain raw
  decoder text; surface-macro-v0 is therefore comparison-ineligible. Search
  still replays each edge through Peano Lab. The separate Hydra runner then
  starts again from the original
  theorem with binding traces and refuses disagreement in theorem, commands,
  logic/capabilities, or certificate size. A provider outage does not corrupt
  a separately checked proof, but it makes the experimental row degraded.
- The paired teacher-oracle pilot gives both lanes the same fixed symbolic
  candidates and depth-13/beam-1/three-candidate budget. The control exhausts;
  the structural teacher reproduces the known 13-command, 180-node proof and
  its fresh kernel replay succeeds. The structural head is invoked at ten
  exact states and gated elsewhere. A mutated odd-right-hand-side statement
  does not activate the transcript and remains unknown.
- Committed the full deterministic proposal and replay evidence under
  `artifacts/peano-hydra/teacher-oracle-pilot-v1.json` (SHA-256
  `3b709f70eb910e327880fefb0fb54b0770e5a8662c995205412f261b27b7580d`).
  This is a plumbing regression, not Qwen/Codex capability, symbolic-baseline
  strength, sealed evaluation, or an LLM-advantage result. The structured macro
  DSL and all H0 semantic/conformance gates remain open.

## 2026-08-03 — Strict HA number-theory campaign tranche 01 closed locally

- Imported the requested 1,308-line campaign blueprint byte-for-byte and bound
  it by SHA-256. Parallel audits separated three questions before proof work:
  the actual intuitionistic logic and definition mechanism, the reusable public
  theorem frontier, and the validation/admission boundary. The result corrected
  the starting assumption: the 384-theorem public library already contains much
  of the arithmetic core, so this campaign begins with canonical interfaces and
  bridges rather than duplicating division, gcd, Bezout, primes, FTA, or CRT.
- Added the dependency-ordered HA0--HA4/M1--M5 plan and a machine-readable
  12-layer campaign manifest. The validator rejects unknown or duplicate IDs,
  forward/cyclic dependencies, bad source paths, unrecognized evidence states,
  and any use of beta/CRT material in the foundational K3 data layer. K3 remains
  deliberately unspecified until a representation RFC selects a primitive-
  recursive encoding independent of CRT and Goedel-beta coding.
- Froze 11 definition expansions and a 45-row relation API in synchronized
  Markdown and JSON. Replay checked all 44 referenced public theorems. Existing
  `Le`, `Lt`, `Dvd`, `DivRem`, `IsGCD`, and `Coprime` are compatible; `ModEq`,
  `Prime`, and balanced Bezout require explicit bridges; `BetaAt` and `Product`
  remain late interoperability surfaces.
- Constructed four canonical-remainder candidates, including explicit
  zero-modulus behavior; one bridge characterizing balanced congruence by equal
  supplied canonical remainders; and four bounded modular-inverse candidates.
  The M1 root states that, for positive modulus, coprimality is equivalent to a
  unique bounded inverse. All nine candidates have complete dependency closures
  accepted from the empty context by the intuitionistic checker, and none is
  silently registered as public.
- The exact M1 root receipt is 9,512 structural nodes, depth 70, 2,538 distinct
  proof objects, 2,679 DAG edges, 142 reused objects, and 126 unique `Cut` nodes;
  its stable DAG digest is
  `c3ed07e7caef52895001332d066ae9e4ce25167c7a0cd7189f8957c9aa7dc9f3`.
  The admission test pins analogous metrics and digests for every candidate,
  repeats each cold closure twice, bans DNE, rejects selected nearby false
  statements, and asserts public-registry absence.
- `make ha-number-theory-check` passed both validators, 22 validator tests, and
  15 focused proof/admission tests. The machine campaign manifest is
  cross-checked against the fresh statements and closure receipts. The
  152-source browser inventory and
  application manifest check as release `a-02903b96cc83`. Staging and deployment
  remain unclaimed; this worktree has no `peano-lab/vendor/MANIFEST.sha256` with
  which to satisfy the separate stage gate. The next controlled action is public
  admission of tranche 01, followed by the canonical gcd/sign layer and linear
  congruences—not premature beta-coded finite data.

## 2026-08-03 — Strict HA tranche 01 admitted; canonical gcd and signed RFC closed

- Admitted the exact nine previously closed canonical remainder, congruence,
  and bounded modular-inverse specifications at registry tail positions
  384--392. Their isolated factory specifications, statements, scripts,
  dependencies, proof metrics, and certificate digests are unchanged. Direct
  public replay succeeds for every entry.
- Migrated the QR stack's sole public/candidate collision,
  `bounded_mod_inverse_unique`, by exact specification equality. Candidate
  factory provenance is retained, incompatible collisions still fail, and the
  reachable QR graph remains 557 nodes, 1,787 edges, and 45 layers. Its new
  scope split is 241 public/316 candidate and graph SHA-256 is
  `26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253`;
  source and layer-profile hashes are unchanged.
- Built the next isolated gcd layer:
  `canonical_gcd_exists` (1,280 nodes/depth 47/36 Cuts),
  `canonical_gcd_functional` (708/depth 35/20 Cuts), and
  `canonical_gcd_exists_unique` (2,010/depth 48/55 Cuts). All three close from
  the empty context under the intuitionistic checker, contain no DNE, reject
  nearby false mutations, and remain deliberately nonpublic.
- Selected `HA-K3-SIGNED-1`, a parity-interleaved canonical signed-natural
  code: `2*p` denotes `+p`, while `2*k+1` denotes `-(k+1)`. The 613-line RFC
  freezes eight exact base-language templates, statement hashes, boundary
  conventions, forbidden dependencies, and a staged proof DAG. It makes no
  theorem claim. A dependency audit showed that foundational parity separation
  must be reproved from K0/K1 rather than imported through division uniqueness.
- The campaign manifest now records 12 layers, 56 public references, three
  candidate references, and twelve exact receipts. `make
  ha-number-theory-check` passes 22 validator tests and 20 focused proof tests;
  the definition freeze still replays 44 public API theorems.
- Regenerated the public snapshot and vault. The 393-theorem/1,070-edge
  snapshot has 1,830,078 structural occurrences, 53,293 Cuts, 338 Cut-bearing
  certificates, and ordered root
  `539a1195df131ed3e202efa15f48bef76a8b8c757789119e2265172453aaf566`.
  The vault now has 492 notes and 4,991 resolved links, including all 393
  generated theorem notes and a campaign concept page.
- Regenerated both QR proof explorers and the browser source seal. The explicit
  and defined explorers pass their focused tests at 241 public/316 candidate;
  the browser inventory has 153 sources and checks as build `2026-08-03c`,
  application `a-9fe3f597bf8d`. No staging, deployment, push, or WMI closure is
  claimed. The theorem atlas is intentionally regenerated only after an
  immutable source commit exists, so new source links cannot point falsely at
  the older 384-theorem commit.
- Created immutable source checkpoint
  `07932576c3d00d7911acd158d81d9a21167ed2dd`, rebound the theorem-atlas source
  resolver to that commit, and regenerated all 393 checked cards plus the one
  explicit language-boundary card. The strict 47-source Jupyter Book build then
  completed without warnings. Its non-executing integrity gate found 2,325 HTML
  pages, zero broken or escaping relative targets, zero broken fragments, and
  byte-identical 2,285-file explicit/defined Proof Explorer trees.

## 2026-08-03 — Strict HA signed decoder candidate layer closed

- Reproved even/odd separation without the historical division-uniqueness
  dependency. `even_odd_exclusive_k1` closes at 80 nodes/depth 20/one Cut from
  `zero_or_succ`; `even_half_unique` closes at 245/depth 24/seven Cuts from
  multiplication cancellation. Their complete public dependency union is
  exactly seven elementary arithmetic theorems and contains no division,
  remainder, beta, CRT, or classical edge.
- Implemented the first seven `HA-K3-SIGNED-1` decoder obligations: the two
  constructors, totality, normality, functionality, zero characterization,
  and universal validity. Every statement expands to the frozen D01/D02
  formulas before checking. The largest certificate,
  `signed_decode_functional`, is 709 nodes, depth 27, 397 distinct objects,
  399 DAG edges, three reused objects, and 13 Cuts; its stable digest is
  `50818b66647097dee0680f1dacbcb62368049dcc95f66532cd36b63306ab3c0b`.
- The focused tests perform two cold closures, pin all nine statement and
  certificate hashes, ban DNE and proof automation in the new scripts, reject
  nearby false statements, check hygienic RFC expansion, and validate unique
  decoding for codes 0 through 20. The combined parity/decoder suite passed
  13 tests; the broader existing parity suite brought the observed total to
  16 passing tests.
- Hardened the campaign validator so K3 rejects direct or transitive division
  and remainder dependencies in addition to beta and CRT. Its mutation tests
  pin the hidden route `double_predecessor_ne_one ->
  even_odd_exclusive_pointwise -> division_remainder_unique`.
- The campaign manifest now records 56 public references, twelve closed
  candidate references, and 21 exact theorem receipts. The nine new signed
  results remain deliberately absent from the 393-theorem public registry.
  `SignedBalance` totality and unique normalization are the next proof layer;
  signed addition, multiplication, and Bezout packaging remain unclaimed.

## 2026-08-03 — Signed code extensionality and SignedBalance normalization closed

- Added three decoded-code extensionality candidates. The forward theorem
  proves that decoded cross-sum equality forces literal canonical-code
  equality by four constructive sign cases; the reverse theorem uses decoder
  functionality. Their package `signed_code_eq_iff_balance` closes at 1,181
  structural nodes, depth 32, 25 Cuts, and certificate SHA-256
  `26dbecbb46fef4d1eda7a208dbdce26f924aabde0a4317092821b8a3f2833728`.
- Added the first three `SignedBalance` candidates. Totality constructs code
  zero, an odd negative code, or an even positive code from natural
  trichotomy; decoder transport and an additive cross-sum helper supply the
  normalization spine. Their closed receipts are respectively 236, 91, and
  410 nodes. An independent read-only audit checked every branch and the
  exact RFC D03 expansion.
- Completed the balance API with extensionality, functionality, and the exact
  zero criterion. Their closed receipts are 736/depth 33/16 Cuts,
  850/depth 34/18 Cuts, and 1,660/depth 36/33 Cuts. The zero theorem's stable
  DAG digest is
  `d54bade5be975a27fc08a189ac552110ed8e85878137bc2e8e5268469c46b419`.
- All nine new statements have pinned SHA-256 identities, dependency-curried
  body receipts, two cold empty-context closures, no-DNE audits, nearby false
  mutations, semantic fixtures, and public-registry isolation. Their exact
  transitive closures contain no division, remainder, CRT, beta, or classical
  theorem. The public registry remains unchanged at 393 entries.
- Integrated the five signed candidate modules into K3 in topological order.
  The campaign manifest now records 56 public references, 21 closed candidate
  references, and 30 exact receipts. The next conservative proof layer is
  `SignedNegate`; addition, multiplication, natural scaling, and signed Bezout
  packaging remain unclaimed.

## 2026-08-03 — Canonical SignedNegate graph closed

- Implemented RFC D04 directly as an existential decoder graph: an input
  decoding `(pos,neg)` is paired with an output decoding `(neg,pos)`. A
  constructive helper produces the swapped decoder without division or
  `SignedBalance`; the two decoder/spec bridges expose both directions.
- Closed totality and literal-output functionality, plus zero, graph symmetry,
  and involution. Exact endpoint receipts are 1,160 nodes/depth 33/25 Cuts for
  `signed_negate_functional` and 1,199/depth 35/27 Cuts for
  `signed_negate_involutive`; the latter has certificate SHA-256
  `7aec997db1ea6393ff1192eea1b16a73b4a7424349b7670e1541fa34029c882b`.
- The focused suite pins all eight statement hashes, body metrics, two cold
  closure passes, RFC D04 text and hash, hygienic binders, exact transitive
  closure, registry isolation, concrete false mutations, and unique semantic
  outputs for codes 0 through 40. An independent read-only audit found no
  defect; 42 combined signed tests pass. The full 26-theorem signed-stack DAG
  digest is
  `89d806311b58860f130cabf862a17bd4e310710a9069b401b293609a0885ce3c`.
- Integrated the negation module in topological order without public
  admission. The campaign manifest now has 56 public references, 29 closed
  candidates, and 38 exact receipts. No new public theorem was added; the
  registry stays at 393. The next graph is `SignedAdd`, whose decoded natural
  contribution sums must pass through canonical `SignedBalance` normalization.
- Final local integration passed 26 manifest/definition tests and 62 focused
  proof/admission tests. A cold snapshot check independently replayed all 393
  public theorems; the vault retained 492 notes and 4,991 resolved links. The
  warning-free 47-source Jupyter Book build retained 2,325 HTML pages, zero
  broken, escaping, fragment, unsafe, or remote-runtime links, and byte-equal
  2,285-file explicit/defined Proof Explorer trees. No WMI, deployment, public
  admission, or push receipt is claimed by this local checkpoint.
- Created immutable local source checkpoint
  `d5a734292b11e516a86606c65653be38d2faa7f1` and rebound only the
  campaign-specific manifest/RFC links in the Book to that source. The public
  theorem atlas remains intentionally pinned to its unchanged 393-theorem
  source checkpoint.

## 2026-08-03 — Canonical SignedAdd core closed

- Implemented RFC D05 as the exact three-decoder contribution equation
  `(lp + rp) + on = (ln + rn) + op`, without subtraction, host-integer proof
  steps, or a new kernel symbol. Introduction and elimination expose the
  equation in both directions; a third row packages their equivalence.
- Proved totality by decoding both inputs and normalizing their positive and
  negative contribution sums with `signed_balance_total`. Proved literal
  output functionality by transporting two graphs to a common balance problem
  and applying `signed_balance_functional`.
- Closed all five candidates twice from a cold public replay. Their exact
  nodes/depths are 26/23, 823/35, 956/39, 411/27, and 1,754/38. The functional
  endpoint has 1,103 distinct proof objects, 1,136 DAG edges, 34 reused
  objects, 34 Cuts, and certificate SHA-256
  `63eb78997ade1da36271de19138643f20e5e48666a1318d6a4982e616a6b9b87`.
  The complete 31-theorem signed-stack digest is
  `11f41d395be9597892e2d5577ff80b54d04a61a57c81e50d02bc335c7e6012da`.
- The focused seven-test audit pins RFC D05 and all five statement hashes,
  checks hygienic expansion and registry isolation, rejects false certificate
  mutations, bans automation and DNE, and exhaustively checks unique canonical
  outputs for 17 by 17 bounded input pairs. Independent review approved the
  semantics and exact 17-public/eleven-candidate dependency closure.
- Integrated the module after SignedNegate in K3 without public admission. The
  campaign manifest now reports 12 layers, 56 public references, 34 candidate
  references, 43 theorem receipts, and seven gates. The registry stays at 393.
  The complete local campaign gate passes 26 validator/definition tests and
  69 focused proof/admission tests. Algebraic laws remain deliberately
  unclaimed and form the next tranche.
- Sealed the exact source as
  `ce2f865389013ab2ad16cb2c351f735972330554`, rebound the campaign Book links
  to it, and rebuilt all 47 Jupyter Book sources without warnings. The
  non-executing integrity gate reports 2,325 HTML pages, zero broken,
  escaping, fragment, unsafe, or remote-runtime links, and byte-identical
  2,285-file explicit/defined Proof Explorer trees. The vault generation
  check passes. No public admission, push, deployment, or WMI receipt is
  claimed.

## 2026-08-03 — Elementary SignedAdd laws closed

- Added graph commutativity, both zero identities, and both orientations of
  adding a code to its canonical negation. The zero-slot statements use
  private hygienic D05 expanders rather than weakening the identifier-only
  core expander or adding a trusted literal-term API.
- Closed the five candidates twice from the empty context. Exact nodes/depths
  are 139/38 for `signed_add_commutative`, 266/25 for
  `signed_add_zero_left`, 427/40 for `signed_add_zero_right`, 145/24 for
  `signed_add_negate_right_zero`, and 299/40 for
  `signed_add_negate_left_zero`. Their 36-theorem stack digest is
  `a5fdad35078f386ccb42fd6e17f942f83f504aaaf748c40259b68a2798ab28c7`.
- The eight-test focused audit pins all hashes, receipts, strict dependencies,
  exact RFC zero instantiations, registry isolation, no-DNE/no-automation
  checks, nearby false mutations, and bounded zero/commutative/inverse
  semantics. Independent review approved the proof semantics and found the
  exact closure to contain four public and five earlier/local facts only.
- Integrated the laws as the eighth K3 candidate module. The campaign now has
  56 public references, 39 candidate references, and 48 exact receipts; the
  registry remains at 393. The full local gate passes 26
  manifest/definition tests and 77 proof/admission tests. Associativity is
  still open and will be attempted only through a separately checked
  cross-sum composition helper.
- Sealed the law source as
  `a1fa4162f92d4ce6c5501cebceadd75403d7a563`, rebound the manifest, RFC, law
  source, and law-audit Book links to immutable checkpoints, and rebuilt the
  47-source Jupyter Book without warnings. The 2,325-page integrity audit has
  zero broken, escaping, fragment, unsafe, or remote-runtime links and the
  explicit/defined explorer trees remain byte-identical. No public admission,
  push, deployment, or WMI result is claimed.

## 2026-08-03 — SignedAdd associativity closed

- Added the general constructive helper `add_cross_sum_chain`, which composes
  `a+x=b+y` and `y+c=x+d` by prefixing and cancelling the shared natural
  contribution. Added `signed_add_equations_associate`, which combines the
  three D05 contribution equations through that helper and a proved
  four-summand shuffle.
- Proved graph associativity by destructing the three input graphs, using the
  D05 elimination theorem to align independently chosen decoders, applying
  the equation associator, and rebuilding exactly `SignedAdd(a,bc,abc)`.
  Independent review verified the complete `x` through `x17` witness map.
- Two cold closures pin exact nodes/depths/Cuts at 315/29/7, 703/35/13, and
  1,695/47/30. The endpoint certificate SHA-256 is
  `dbac676cc5650d6f0d884dd2e4f9426d17342327cdf0abb59e71c40cc0a8a4cc`;
  the complete 39-theorem stack digest is
  `39ac0f7083ed54d2762289c7417b57a21c6dc97971b57efe2649ecb1cb7ec895`.
- The focused seven-test audit checks both arithmetic helpers exhaustively on
  small naturals and graph associativity on all 4,913 triples of the first 17
  codes, while pinning statements, bodies, closures, mutations, no-DNE, strict
  dependencies, and registry isolation. The full campaign gate now passes 26
  manifest/definition tests and 84 proof/admission tests.
- Integrated the associativity module as the ninth K3 candidate module. The
  campaign has 56 public references, 42 candidates, and 51 exact receipts;
  the public registry remains 393. SignedAdd now meets every RFC arithmetic
  acceptance law at closed-candidate status. `SignedMul` is the next graph.
- Sealed the complete additive source as
  `883febe3fcf3b8a29707f34780c457f8fcd8edc6`, rebound the campaign manifest,
  RFC, associativity source, and audit links, and rebuilt all 47 Book sources
  without warnings. The 2,325-page integrity gate reports no broken,
  escaping, fragment, unsafe, or remote-runtime link and byte-identical
  explicit/defined explorer trees. No public admission, push, deployment, or
  WMI receipt is claimed.

## 2026-08-03 — Canonical SignedMul core closed

- Implemented RFC D06 as three exact signed decoders plus the subtraction-free
  product equation `(lp * rp + ln * rn) + on = (lp * rn + ln * rp) + op`.
  The five rows provide introduction, elimination, their packaged iff,
  totality, and literal-output functionality.
- Totality normalizes the positive and negative product contributions through
  `signed_balance_total`; functionality reduces both outputs to one
  `signed_balance_functional` problem. No SignedAdd theorem or multiplication
  algebra law is a dependency of the core.
- Two cold closures pin nodes/depths at 26/23, 877/39, 1,010/41, 411/27, and
  1,808/40. The functional endpoint has 1,157 distinct proof objects, 1,190
  DAG edges, 34 reused objects, 34 Cuts, and certificate SHA-256
  `632bd740e1f6a5a00497205379dd64f3cdc3e45d75a33c8c02d46f727f05f410`.
  The complete 44-theorem signed-stack digest is
  `2230cd2b67196ccec58ab5259052b08f9ef3f43275ef0b717fc35cf581cd0f6c`.
- The focused seven-test audit pins RFC D06, statements, bodies, closures,
  mutations, strict dependencies, and registry isolation. Its bounded oracle
  checks unique canonical outputs for all 289 pairs of the first 17 codes and
  explicitly rejects raw multiplication of parity codes.
- Integrated D06 as the tenth K3 candidate module. The campaign now has 56
  public references, 47 candidates, and 56 exact receipts; the public registry
  remains 393. The next proof tranche is D06 zero, one, and commutativity.
  Public admission remains separate and unclaimed.
- The parallel K3 representation audit selected doubled-Cantor pair codes
  `s*S(s)+2*right` and successor-tagged cells. The new `HA-K3-PAIR-1` RFC
  freezes eight expanded templates and a K0--K2-only injectivity/cell-descent
  ladder, but makes no theorem claim.
- The audit also exposed a missing dependency in the original roadmap:
  pairing alone cannot expand variable tail iteration into one finite formula.
  Uniform lists remain blocked on an independently selected computation-trace
  encoding or a proved conservative primitive-recursive definition compiler.
  No recursive macro is being hidden as syntactic sugar.
- A separate admission audit found the preceding 42 candidates
  certificate-ready, collision-free, and DNE-free, while confirming that bulk
  public migration still requires registry-test migration, generated
  integration, and heavy closure. No candidate was promoted in this tranche.
- The integrated local gate passes 29 manifest, definition, and pair-RFC tests
  plus 91 focused proof/admission tests. Independent knowledge-base validation
  still reports 393 checked public theorems and the frozen public-library
  snapshot replays all 393 unchanged.
- Rebuilt all 47 Jupyter Book sources without warnings. The structural audit
  reports 2,325 HTML pages, zero broken, escaping, fragment, unsafe, or remote
  runtime links, and byte-identical 2,285-file explicit/defined explorer
  trees. The 492-note vault retains 4,991 resolved links. No public admission,
  push, deployment, or WMI receipt is claimed.
- Sealed the exact D06 and pair/cell RFC source checkpoint as
  `01fb459bc2ef797ca1e1e76b353c219dcc1eecb6`; the Book links are rebound to
  that immutable commit in the following documentation-only checkpoint.

## 2026-08-04 — Elementary SignedMul laws closed

- Added five exact D06 graph-law candidates: multiplication commutativity,
  left and right zero annihilation, and left and right identity for signed
  positive-one code `2`. Code `1` remains negative one; no statement confuses
  the parity-interleaved representation with raw natural-code multiplication.
- Commutativity swaps the two input decoder pairs and uses `mul_comm` on all
  four monomials plus `add_comm` on the cross-term order. Left zero and left
  one construct reviewed literal decoders and reuse the arbitrary input
  decoder through `signed_mul_of_decoded_equation`; the right laws follow from
  their left counterparts and graph commutativity.
- Two cold empty-context replays pin exact nodes/depths/Cuts at 376/41/8,
  209/25/4, 607/43/14, 347/25/10, and 745/43/18. The endpoint certificate
  SHA-256 is
  `fe3977029e00057909e7204631ce6f66b5ce2aff10a4132872ce011a899ef378`,
  and the complete 49-theorem signed-stack digest is
  `be074dfe1b79e3f27b2d48851c64f58360ee86fc3776ae681c451d38f67d25b2`.
- The eight-test focused audit pins statements, bodies, closures, literal D06
  alpha-identity, strict dependency closure, registry isolation, false target
  mutations, and the multiplication laws on every pair of the first 33 codes.
  No DNE, division, remainder, CRT, beta, SignedAdd law, or forbidden tactic is
  reachable.
- Integrated the laws as the eleventh K3 candidate module. The campaign now
  has 56 public references, 52 candidates, and 61 exact receipts; the public
  registry remains 393. The integrated local gate passes 29 manifest,
  definition, and pair-RFC tests plus 99 proof/admission tests. Public
  admission, push, deployment, and WMI work remain separate and unclaimed.
- D06 associativity and distributivity are next. Their proofs must use
  independently audited decoded-equation composition lemmas before D07
  natural scaling begins.
- Sealed the exact source checkpoint as
  `37bd997ac9890be9f040b94e8e713f19246d9186` and bound the Book's manifest,
  RFC, tactic-source, and focused-audit links to it. The warning-free
  47-source rebuild retains 2,325 HTML pages. Its structural audit reports
  zero broken, escaping, fragment, unsafe, or remote-runtime links and
  byte-identical 2,285-file explicit/defined explorer trees. The 492-note
  vault still has 4,991 resolved links. No push or deployment is claimed.

## 2026-08-04 — SignedMul associativity and distributivity closed

- Added eleven isolated, nonpublic candidates. The four-row associativity
  ladder consists of two reusable natural pair lemmas, the decoded D06
  equation associator, and exact graph associativity. The seven-row
  distributivity ladder provides additive shuffle and pairwise-composition
  helpers, componentwise product distribution, balanced-output composition,
  fixed-left cross-sum distribution, and exact left and right graph laws.
  Every non-endpoint distributivity row is reachable from a graph endpoint.
- Closed all eleven rows from the empty context without DNE, classical
  reasoning, forbidden automation, division, remainder, CRT, or beta coding.
  The graph endpoints are `signed_mul_associative` at 3,196 nodes/depth 47
  with DAG SHA-256
  `c6a9694ced9e0d4cb1426112b7b717dd9b60cf049ea89e71223f906512271775`,
  `signed_mul_left_distributive` at 3,297 nodes/depth 58 with digest
  `c02d8258cce2e4cbd6a16aa731c9ce3424f1cc4726f48c0bc55d80e9c19f6633`,
  and `signed_mul_right_distributive` at 3,717 nodes/depth 60 with digest
  `63d17772d42432a58c75064ff05ded34490519639625151c90c6cc591f7cf7d1`.
  Two independent cold closures agree on the complete 60-row signed-stack
  digest
  `7befb7ae830b866a606e47f674730959e76599ded863aadd9868b850bcb190cd`.
- The focused associativity suite passes eight tests and the focused
  distributivity suite passes eight tests. They pin exact statements,
  dependencies, body and closed receipts, false-target mutations, registry
  isolation, and strict transitive closures. Exhaustive semantic audits cover
  the bounded natural helpers, all binary `2^12` associativity and `2^14`
  distributivity equation assignments, and every `17^3` triple of the first
  seventeen canonical signed codes for associativity and both distributive
  orientations.
- The isolated checkpoint contains 60 signed candidates, 63 campaign
  candidates overall, and 72 exact receipts. The public theorem registry is
  unchanged at 393. D07 natural scaling is next; public admission, shared
  deployment, commit, and push remain separate and unclaimed by the proof
  receipt.
- Sealed the 14-file source checkpoint as
  `497d0fc3327e6fa2564aad8b44c4ce151e20269c`, then bound the strict-HA book
  chapter to that immutable source. A clean 47-source build passed the WMI
  integrity checker with 2,325 HTML pages, zero broken or escaping relative
  targets, zero unsafe or remote-runtime links, and byte-identical 2,285-file
  explicit/defined explorer trees. The 2,493-file HTML tree contains
  87,143,000 bytes and has SHA-256
  `2eaf9bc60642a29f101a472553c1f21bb5dc30baab3c8bf76665550d9135f59f`.
  No browser was attached, so a visual click-through is not claimed. No push,
  deployment, or public theorem admission is claimed.

## 2026-08-04 — D07 SignedNatScale closed in isolation

- Added ten isolated, nonpublic candidates: five core rows for the decoded
  scaling equation in both directions, its iff, totality, and literal-code
  functionality; and five law rows for natural cross-sum transport,
  decoded-equation composition, zero, one, and graph composition.
- The core suite passes all eight focused tests and the law suite passes all
  nine. Exact closed receipts use the schema `(nodes, depth, DAG objects, DAG
  edges, reused references, Cuts, DAG SHA-256)`. The principal endpoints are
  `signed_nat_scale_total = (431, 39, 416, 430, 15, 8,
  e1ee2921a7e967369bd70cd70564ef340ad643926c15c62dba394ae535e76947)`,
  `signed_nat_scale_functional = (1698, 36, 1047, 1080, 34, 34,
  59f948b0d2c8335cd3cd0098fb4acec9f895d8db2f930393d4dad33375ee2727)`,
  and `signed_nat_scale_compose = (1453, 34, 897, 923, 27, 30,
  7548acf6871b7db3db4ba2cdaf89b9544e2d641c881a9f27e47dc4c77448b49e)`.
  Repeated cold closure pins the 65-row core stack digest to
  `511aa0ba4a6dac1a22f52db740f539c675307b5b77b6b1a7d9ef2e00dd8a5331`
  and the 70-row complete signed-stack digest to
  `81a18daf55e564c11dee83ce7465bc91876109a5e6bc092f75e0f31f46e27d8d`.
- The core oracle exhaustively checks every one of the `17 * 17` scale/input
  pairs against all 257 candidate outputs. The law oracle covers exactly 425
  satisfying cross-sum-helper premises and 477 satisfying equation-compose
  premises, checks zero and one over the first 33 codes, and checks the graph
  composition law over all `17^3` triples. The pinned raw-code trap records
  that `2 * 1 = 2` as naturals although scaling signed code `1` (negative one)
  by two produces canonical code `3`, not code `2`.
- Both dependency closures remain strictly intuitionistic arithmetic: no DNE,
  forbidden automation, division, remainder, CRT, beta, or classical theorem
  is reachable. With D07, the isolated campaign has 70 signed candidates, 73
  candidates overall, and 82 exact receipts; the public registry remains 393.
  The D08 `SignedBezout` bridge is next.
- This is a proof checkpoint only. Public admission, push, and deployment are
  separate and unclaimed by the proof receipt.
- The integrated local gate passes 29 manifest, definition-freeze, and
  pair-RFC tests plus 132 proof/admission tests. The 394-row research
  knowledge base, the independently replayed 393-theorem public snapshot,
  and the 492-note/4,991-link vault remain green and unchanged, confirming
  that the ten D07 rows are isolated evidence rather than public admissions.
- Sealed the 14-file D07 source checkpoint as
  `bc45de0da2ff60ca65d81d4b8cef612f0b935892` and bound the strict-HA Book
  chapter to that immutable source. The clean 47-source build passed the WMI
  integrity checker with 2,325 HTML pages, zero broken/escaping/fragment/
  unsafe/remote-runtime links, and byte-identical 2,285-file source/built
  explorer trees. The 2,493-file HTML tree contains 87,162,964 bytes and has
  SHA-256
  `7be58cd44aa4b2a8b4e1a233fc9db6101dc478b097f0a22f028d2391b7b194e6`.
  No browser was attached, so visual QA is not claimed. No push, deployment,
  or public theorem admission was performed.

## 2026-08-04 — D08 SignedBezout bridge closed in isolation

- Added four isolated, nonpublic candidates in dependency order:
  `balanced_bezout_equation_transport`,
  `balanced_bezout_to_signed_bezout`,
  `signed_bezout_to_balanced_bezout`, and
  `balanced_bezout_iff_signed_bezout_exists`. The forward proof normalizes
  `(xp,xn)` and `(yp,yn)` independently with `SignedBalance`, lifts the two
  cross sums through multiplication, and transports the subtraction-free
  Bezout equation. The reverse proof exposes the decoder witnesses in the
  legacy balanced order `xp,yp,xn,yn` rather than the D08 order
  `xp,xn,yp,yn`.
- Exact empty-context receipts `(nodes, depth, DAG objects, DAG edges, reused,
  Cuts, digest)` are `(943,34,497,518,22,20,9e3f3b98...)`,
  `(1241,39,722,744,23,24,f39a7907...)`,
  `(35,23,35,34,0,0,f0fb3fa8...)`, and
  `(1326,40,807,829,23,26,1bc7e284...)`. Two cold closures agree on the
  complete 74-row signed-stack digest
  `b7949148236ab243830a2bfebd80ddafeb31a63c5e70ace1c032de8bd2415f15`.
- The ten-test focused audit pins all statements, hashes, ordered
  dependencies, body receipts, RFC D08 hygiene, witness ordering, false
  mutations, registry isolation, strict dependency closure, and lack of
  orphan rows. Its semantic oracle checks 2,185 satisfying transport tuples,
  5,736 raw normalization witnesses, and 1,600 bounded direct graph cases,
  including two distinct canonical coefficient pairs for `2X+3Y=1`, the
  zero-coefficient edge, and a raw-code-order trap.
- No DNE, forbidden automation, division, remainder, CRT, beta, or classical
  theorem is reachable. The integrated campaign has 74 signed candidates,
  77 candidates overall, 86 exact receipts, 16 K3 candidate modules, and 18
  focused tests. The public registry remains 393, with 56 public references;
  the definition freeze remains 45 rows over 44 theorems and the catalog
  remains 394. This is not a public admission.
- The integrated source gate passes 29 manifest/definition/pair-RFC tests and
  all 142 proof/admission tests. The arithmetic knowledge base validates 394
  entries, the independent snapshot replays 393 public theorems without
  drift, and the vault verifies 492 notes with 4,991 resolved links.
- `gcd_signed_bezout_exists` remains a deliberate K4 client because its
  public gcd source reaches division. It is not smuggled into the strict K3
  closure.
- Sealed the D08 source checkpoint as
  `bb02ee5a767f6c4c585916269de688e7068b3716` and bound the strict-HA Book
  chapter to that immutable source. The warning-free 47-source rebuild passes
  the structural integrity checker with 2,325 HTML pages, zero broken,
  escaping, fragment, unsafe, or remote-runtime links, and byte-identical
  2,285-file source/built explorer trees. The 2,493-file HTML tree contains
  87,178,354 bytes and has SHA-256
  `ee4f046d54b019e780d05dfcf2fd75af7f1c481c930cea3de219a6c1c0870a8b`.
  No browser is attached, so visual QA is not claimed. Push, deployment, and
  public theorem admission remain separate and unperformed.

## 2026-08-04 — K4 signed gcd/Bezout client closed in isolation

- Added the one-row `gcd_signed_bezout_exists` client. It specializes public
  `gcd_balanced_bezout_exists`, retains the complete relational-gcd witness,
  and feeds the balanced coefficient conjunct to D08
  `balanced_bezout_to_signed_bezout`. The result simultaneously returns
  `d,x,y` with the expanded `IsGCD(d,a,b)` and
  `SignedBezout(d,a,b,x,y)` relations.
- The 592-byte statement has SHA-256
  `2e729fe9d25b8afda315489713f0a4cd7980371bf621e8af9e557f4ffca7496e`.
  Its 20-command dependency-curried body receipt is
  `(2,20,25,13,25,24,0)`. Two empty-context closures reproduce
  `(3535,48,1734,1824,91,74,
  4edeb4ffc7de0b9aa0a870d2125f7640f2447a7358ba454abba3db003f9044a3)`.
- The transitive audit identifies eight local K3 dependencies and 33 public
  dependencies. It contains zero DNE and no CRT, beta, or classical theorem;
  `divides_remainder`, `division_remainder_exists`, and
  `division_remainder_succ` are expected K4 dependencies. The campaign
  manifest now records `K3` explicitly in K4's layer dependencies rather than
  contaminating the strict-K3 stack.
- This raises the isolated corpus to 78 candidates and 87 receipts across 18
  candidate modules and 19 focused tests. The strict signed stack remains 74
  rows with digest `b7949148...`; registry/public-reference/definition/catalog
  counts remain 393/56/45-over-44/394. The integrated source gate passes 29
  campaign-structure tests and all 148 proof/admission tests. The arithmetic
  knowledge base validates 394 rows, the independent snapshot replays all 393
  public theorems, and the vault verifies 492 notes with 4,991 resolved links.
  No admission is made.
- Sealed the K4 source checkpoint as
  `1d10c37535d829280398c2522ff3fd9d5f059e6c` and bound a separate Book panel
  to its immutable manifest, tactic source, and six-test audit. The
  warning-free 47-source rebuild passes integrity with 2,325 HTML pages, zero
  broken, escaping, fragment, unsafe, or remote-runtime links, and
  byte-identical 2,285-file source/built explorer trees. The 2,493-file HTML
  tree contains 87,187,069 bytes and has SHA-256
  `647d12228514a9ad11ea227ac5ef436d18382cf0d8664e2cc3ea44fd0ab9ac07`.
  No browser is attached, so visual QA is not claimed. Push, deployment, and
  public theorem admission remain unperformed.

## 2026-08-04 — K4 canonical gcd and relational lcm closed in isolation

- Added five canonical-gcd edge candidates: zero on either side, one on
  either side, and swap functionality. Added a 17-row universal-property
  `IsLCM` API covering projections, leastness, symmetry, uniqueness,
  divisibility constructors, product common-multiple, and zero/one edge and
  unique-existence packages.
- Added the nine-row constructive totality ladder A--I. Its internal route is
  balanced-Bezout result one to coprimality; coprime product to `IsLCM`;
  nonzero scaling; cancellation of a nonzero gcd from balanced Bezout; the
  zero-gcd input edge; compatible gcd/lcm existence; relational lcm
  existence; unique lcm existence; and finally `gcd_lcm_product`.
- The zero convention is forced by the relation, not selected as an auxiliary
  definition: a multiple of zero has the form `0*q` and is therefore zero,
  so an `IsLCM` witness for `(0,b)` or `(a,0)` must be zero. Likewise,
  `g*l=a*b` is proved from the independently stated `IsGCD` and universal
  `IsLCM` predicates. It does not define lcm as a quotient of the product by
  gcd.
- Exact dependency-curried body receipts use
  `(dependencies, commands, nodes, depth, objects, edges, reused)`. Rows F--I
  are respectively `(10,108,209,45,209,208,0)`,
  `(1,10,33,19,33,32,0)`, `(2,17,40,24,40,39,0)`, and
  `(3,31,43,21,43,42,0)`.
- Exact empty-context receipts use
  `(nodes, depth, objects, edges, reused, Cuts, DNE, digest)`: F
  `gcd_lcm_compatible_exists = (9038,60,2390,2510,121,101,0,
  dfe0e69fb172e48b6aa785c0c088ebf1a7cdf09c95ae436305d51d6224e90bc3)`;
  G `lcm_exists_relational = (9071,61,2423,2543,121,102,0,
  f4e764738627255eb885d78b5cefd74663d68be022370a8036ee450b116a7220)`;
  H `canonical_lcm_exists_unique = (9791,62,2565,2691,127,111,0,
  3ab4c410a0e4c6717e77d7f951d26304a35b5e9451df299167bb42cadf227747)`;
  and I `gcd_lcm_product = (10441,61,2569,2696,128,112,0,
  c0829496624e993a4c437aa98c32355605109e728acd03d6b5d857fcb5350d0a)`.
- The isolated campaign now contains 109 candidates, 118 exact receipts, 21
  candidate modules, and 22 focused test files. Public counts remain exactly
  393 registry theorems, 56 public references, 45 definition rows over 44
  theorems, and 394 catalog entries. The new closures contain zero DNE.
- The integrated source gate passes all 29 campaign-structure tests and all
  175 proof/admission tests. Independent checks validate the 394-entry
  arithmetic knowledge base, replay all 393 public theorems in the frozen
  snapshot, and verify 492 vault notes with 4,991 resolved links. This remains
  a focused candidate checkpoint: no public admission, push, or deployment is
  claimed.
- Sealed the source checkpoint as
  `9b2feb66b5fcc2530394f5b6bcce5e63dfea627f` and bound a new Book section to
  its immutable manifest, RFC, three tactic modules, and three focused audits.
  The warnings-as-errors rebuild covers all 47 sources. The integrity checker
  passes 2,325 HTML pages with zero broken, escaping, fragment, unsafe, or
  remote-runtime links and byte-identical 2,285-file source/built explorer
  trees. The 2,493-file HTML tree contains 87,206,047 bytes and has SHA-256
  `1468972f63c3c9122fb0341559ac31f31e602589801381e60cb94e3b5d916472`.
  No visual click-through, public admission, push, or deployment is claimed.

## 2026-08-04 — Selective K4 admission and generalized-CRT foundation

- Deliberately admitted the exact seven-row universal LCM surface
  `is_lcm_multiple_left`, `is_lcm_multiple_right`, `is_lcm_least`,
  `is_lcm_symm`, `is_lcm_unique`, `is_lcm_zero_right`, and
  `is_lcm_zero_left`, followed by all nine bridge rows
  `balanced_bezout_one_implies_coprime`, `coprime_product_is_lcm`,
  `is_lcm_scale_nonzero`, `balanced_bezout_cancel_gcd`, `gcd_zero_inputs`,
  `gcd_lcm_compatible_exists`, `lcm_exists_relational`,
  `canonical_lcm_exists_unique`, and `gcd_lcm_product`.
- Public replay preserves all 16 isolated factory specifications and frozen
  proof-DAG receipts. Two cold passes agree, nearby false endpoints are
  rejected, and every admitted certificate contains zero DNE. The focused
  tranche/admission/LCM suite passes 27 tests. The append-only registry now
  has 409 entries; the catalog has 410, including 386 `checked_m20` rows.
- Retained exactly 19 private K4 candidates: three canonical-gcd package
  rows, five canonical-gcd edge rows, LCM row L08 plus convenience rows
  C01--C09, and `gcd_signed_bezout_exists`. Their closed receipts remain
  evidence, not admission.
- Closed the first generalized-CRT foundation as eight isolated candidates.
  `mod_eq_add_cancel_left` is reused byte-for-byte from its existing factory;
  the seven new rows are `mod_eq_zero_iff_eq`,
  `mod_eq_add_cancel_right`, `mod_eq_scale`,
  `mod_eq_unscale_nonzero`, `crt_solution_pair_congruent`,
  `crt_common_solution_implies_gcd_compatible`, and
  `crt_incompatibility_obstructs_solution`.
- The last two rows prove respectively that any common solution forces
  compatibility modulo a relational gcd and that incompatibility obstructs
  every solution. All eight close constructively with zero DNE, and the
  focused six-test audit passes. The converse construction, full solution
  class modulo relational LCM, canonical representative, finite lifting,
  admission, commit, push, and deployment remain separate and unclaimed.

## 2026-08-04 — Generalized-CRT M5a sufficiency closed in isolation

- Added the seven-row
  `ha_generalized_crt_sufficiency_candidate.py` ladder. It separates right
  factor nonzeroness, gcd-cofactor coprimality, a packaged nonzero cofactor
  decomposition, compatible common remainders, the coprime-CRT scale/add
  lift, the main existence construction, and the solvability criterion.
- The cofactor proof is the direct universal-property argument
  `d|M,N -> gd|m,n -> gd|g -> g=g*(d*w) -> 1=d*w -> d=1`; it needs no new
  Bézout interface. Compatibility supplies `a=g*A+r`, `b=g*B+r`, `r<g`.
  Public `binary_crt` solves for `A,B` modulo the coprime cofactors; scaling
  and adding `r` constructs the original solution.
- Dependency-curried bodies contain 31, 75, 91, 73, 91, 120, and 73 nodes.
  Exact capstone closure is `(10073,76,3316,3476,161,149,0,
  8956a66d8f72d512f840464d2749e43258a2b74b3828dde58f2c206d53af0234)`.
  The five-test focused audit pins statements, script hashes, dependency
  order, bodies, two cold closures, false mutations, native syntax, and
  bounded semantics. Every row has zero DNE.
- Updated the executable campaign to 108 candidate references and 133 exact
  theorem receipts, extended the RFC and Book with the mathematical proof
  and dependency diagram, and added the focused audit to the integrated gate.
  The complete source gate passes 30 campaign-structure tests and 189
  proof/admission tests. Independent checks validate the 410-row knowledge
  base, replay the 409-theorem snapshot, and verify 508 vault notes with 5,119
  resolved links. The public registry remains 409 and no
  kernel/formula/proof limit changed.
- Rebuilt all 47 Jupyter Book sources. The structural audit passes 2,325 HTML
  pages with no broken/escaping/unsafe links, no broken fragments, no remote
  runtime assets, and byte-identical 2,285-file source/built proof explorers.
  The 2,493-file HTML tree contains 87,466,493 bytes and has SHA-256
  `b322fe004bee4cfcd511973b74365f9d0c4b798d0b0c5711d352ba7046c1d579`.
  The browser worker inventory now has 175 sources and release seal
  `a-ed049a6d3d2c` (`BUILD=2026-08-04c`).
- This is M5a only. Zero-modulus wrappers, solution classification modulo
  relational LCM, bounded canonical representatives, explicit decision or
  obstruction output, finite generalized CRT, admission, push, and deployment
  remain distinct gates.

## 2026-08-04 — Generalized-CRT M5b all-modulus criterion closed

- Added four isolated rows in
  `ha_generalized_crt_zero_boundary_candidate.py`:
  `generalized_binary_crt_sufficient_zero_left`,
  `generalized_binary_crt_sufficient_zero_right`,
  `generalized_binary_crt_sufficient`, and
  `generalized_binary_crt_solvable_iff`.
- The left boundary turns `IsGCD(g,0,n)` into `g=n` using public gcd symmetry,
  `is_gcd_zero_right`, and `is_gcd_unique`, then chooses `x=a`. The right
  boundary similarly obtains `g=m` and chooses `x=b`, using congruence
  symmetry for the remaining modulus. This avoids both division at modulus
  zero and every residual private canonical-gcd edge theorem. The left row
  already handles `(m,n)=(0,0)`.
- Total sufficiency uses the constructive theorem `eq_decidable` first on
  `m=0`, then on `n=0`. The three branches invoke the left boundary, right
  boundary, or the already closed M5a nonzero theorem. Combining this result
  with `crt_common_solution_implies_gcd_compatible` proves, for arbitrary
  natural moduli, that a common solution exists exactly when the residues are
  congruent modulo a supplied relational gcd.
- Dependency-curried body receipts
  `(dependencies,commands,nodes,depth,objects,edges,reused)` are
  `(4,31,48,21,48,47,0)`, `(4,29,43,22,43,42,0)`,
  `(4,49,71,23,71,70,0)`, and `(2,27,67,26,67,66,0)`.
  Empty-context receipts
  `(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` are respectively
  `(834,37,682,717,36,26,0,074f07df173308477693b6e3bbfd3a3a4123078d8f7f5eaac9077666d3cbc763)`,
  `(805,36,653,688,36,26,0,da2d830f65077816dfeecd1503a787cf8ba0f5ec99e93d13b5456e4ba772e2f6)`,
  `(11240,78,3495,3662,168,160,0,931fbcc775154507996c768cb1de1cc8479c3ed805ce0d1a95fffb530e8b56c4)`,
  and
  `(11825,80,3658,3830,173,168,0,3f1d82f0f06df9e0d2a5c746405ee46406db71c57e4bbf32f68792be07af8b0c)`.
- Every certificate passes the ordinary intuitionistic checker with zero DNE.
  The largest is 11,825 occurrences at depth 80, well inside the existing
  bounds; no kernel, grammar, formula, proof-DAG, depth, or live-proof limit
  was changed.
- The four rows remain candidate evidence. They bring the campaign to 112
  private candidate references and 137 exact receipts, but do not alter the
  409-theorem public registry or 410-row research catalog. The remaining M5
  gates are solution classification modulo relational LCM, the correctly
  bounded canonical representative, executable compatibility/obstruction
  output, finite-system lifting, and deliberate public admission.
- The integrated source gate passes 30 campaign-structure tests and 194
  proof/admission tests. Independent checks retain the 410-row arithmetic
  knowledge base, replay the unchanged 409-theorem public snapshot, and
  verify the unchanged 508-note/5,119-link vault. The browser worker inventory
  now has 176 sources and immutable application seal `a-4286adc4e7f3`
  (`BUILD=2026-08-04d`).
- The warning-free 47-source Jupyter Book rebuild passes structural integrity
  across 2,325 HTML pages. It reports no broken, escaping, fragment, unsafe,
  or remote-runtime links and byte-identical 2,285-file source/built proof
  explorers. The 2,493-file HTML tree contains 87,475,314 bytes and has
  SHA-256
  `df5eb6326836ce5d1f7ba8ce780dc24dcf6f2878cc1aff6a836e0b3790ada009`.
  No visual click-through, public admission, or deployment is claimed.

## 2026-08-04 — Generalized-CRT M5c relational-LCM classification closed

- Added the four-row isolated
  `ha_generalized_crt_classification_candidate.py` ladder. Its exact
  interfaces and ordered proof route are:
  `mod_eq_ordered_gap_multiple`, proving
  `k+x=y -> ModEq(d,x,y) -> Dvd(d,k)` from `add_comm`, `add_assoc`,
  `add_left_cancel`, and `factor_difference`;
  `mod_eq_lcm_merge`, using `le_total`, congruence symmetry, the gap theorem,
  `is_lcm_least`, `mul_comm`, and `remainder_decomposition_to_mod_eq`;
  `mod_eq_lcm_iff_pair`, using both public LCM projections,
  `mod_eq_of_mod_eq_multiple`, and the merge theorem; and
  `crt_solution_class_iff_lcm`, using `crt_solution_pair_congruent`, the pair
  equivalence, and `mod_eq_trans` to prove
  `CRTSolution(y,m,n,a,b) iff ModEq(l,y,x)` relative to a fixed solution `x`.
  The forward capstone branch deliberately compares `y` to `x`; the reverse
  branch composes `y == x` with the congruences carried by `x`.
- Dependency-curried body receipts
  `(dependencies,commands,nodes,depth,objects,edges,reused)` are
  `(4,31,44,21,44,43,0)`, `(6,113,127,26,127,126,0)`,
  `(4,46,56,21,56,55,0)`, and `(3,62,79,27,79,78,0)` in row order.
  Empty-context receipts
  `(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` are
  `(558,30,310,325,16,13,0,
  6a30012cfc1213bf167be2de794e05cdae2893ab075cfc24abf9b181bde9be67)`,
  `(1315,33,653,685,33,25,0,
  46cd67f69ccf0c669de283fca6a74a0a85cf18d54f248f1a6f428122196a331b)`,
  `(1570,37,864,908,45,32,0,
  855d5745c1613304fc0a5f26c70fe9f795ed3ebcff4a7276e3745681d41fc91a)`,
  and `(2208,39,1055,1104,50,40,0,
  305a913aaca1c3e307d8ca77bb90c063dd67f3fa9f9bdd69e28cf4064cdff7b3)`.
- The retained bounded semantic audit passes 1,296 LCM-iff cases, 4,692
  fixed-solution class comparisons, and 678 class comparisons with `l=0`.
  At zero LCM,
  `ModEq(0,y,x)` is exact equality, so the same classification theorem gives
  uniqueness uniformly without division and without asserting a remainder
  below zero. Two cold closures, statement/dependency/script pins, and false
  mutations pass. Every row checks through the intuitionistic entry point
  with zero DNE and within the unchanged limits.
- M5c raises the private evidence to 116 candidate references and 141 exact
  receipts. It does not admit a theorem: the public registry and research
  catalog remain 409 and 410, and no kernel or resource limit changed.
- Froze the immediate M5d boundary to exactly three rows:
  `crt_solution_unique_lcm_zero` (exact uniqueness when `l=0`),
  `crt_solution_canonical_remainder_nonzero` (the unique solution `r<l` when
  `l!=0`, with `Below(r,l) := exists h. h+S r=l`), and
  `generalized_binary_crt_canonical_boundary` (constructive zero/nonzero
  disjunction from relational gcd/lcm data and compatibility). The third row
  depends on `eq_decidable`, total M5b sufficiency, and the first two M5d
  rows; no theorem may claim a remainder below zero.
- The integrated source gate passes 30 campaign-structure tests and 200
  proof/admission tests. Independent checks retain the 410-row arithmetic
  knowledge base, replay the unchanged 409-theorem public snapshot, and
  verify the unchanged 508-note/5,119-link vault. The browser worker inventory
  now has 177 sources and immutable application seal `a-6353222cdacb`
  (`BUILD=2026-08-04e`).
- The warning-free 47-source Jupyter Book rebuild passes structural integrity
  across 2,325 HTML pages. It reports no broken, escaping, fragment, unsafe,
  or remote-runtime links and byte-identical 2,285-file source/built proof
  explorers. The 2,493-file HTML tree contains 87,491,052 bytes and has
  SHA-256
  `a034d5c96b3aa7a108526b013edbcf21e326701b8241d6e97f49b2f7c36a8cd5`.
  No visual click-through, public admission, or deployment is claimed.

## 2026-08-04 — Generalized-CRT M5d canonical boundary closed

- Added the three-row isolated
  `ha_generalized_crt_canonical_boundary_candidate.py` layer. Its first row,
  `crt_solution_unique_lcm_zero`, uses `crt_solution_class_iff_lcm` and
  `mod_eq_zero_iff_eq` to prove pointwise exact uniqueness at `l=0`. Its
  second row, `crt_solution_canonical_remainder_nonzero`, uses division,
  multiplication commutativity, remainder-to-congruence, congruence symmetry,
  M5c classification, and bounded uniqueness to produce a unique solution
  below nonzero `l`; the reusable row also retains `ModEq(l,r,x)`. The
  capstone `generalized_binary_crt_canonical_boundary` constructs a fixed
  solution with total M5b sufficiency, decides `l=0` with `eq_decidable`, and
  returns either exact zero-LCM uniqueness or a unique bounded nonzero-LCM
  representative. The latter is expressed by the hygienic expansion
  `Below(r,l) := exists h. h+S r=l`; no zero branch asserts `Below(_,0)`.
- Dependency-curried body receipts
  `(dependencies,commands,nodes,depth,objects,edges,reused)` are
  `(2,33,37,28,37,36,0)`, `(6,83,141,39,141,140,0)`, and
  `(4,66,76,33,76,75,0)`. Empty-context receipts
  `(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` are
  `(2300,40,1126,1176,51,43,0,
  2afc46ac88613c95400eb37f80b1fbda095b18a7f6a774255426b48c35aed9ac)`,
  `(4086,65,1668,1746,79,64,0,
  091e8f2b1ba7e4665b87071fcd924ea1098880d65a97bcdd264ed544e33ff0e4)`,
  and `(17750,80,4239,4426,188,193,0,
  c704a17f6feed83142b160bbeafcc14764d5ae6590999187eed5455c3ad03bd7)`.
  Two cold passes agree, all certificates check through the intuitionistic
  entry point with zero DNE, false endpoint mutations fail, and no formula,
  proof, depth, DAG, or kernel limit changed.
- Retained bounded semantics cover 4,021 compatible systems with `m,n<7` and
  `a,b<11`: 611 have zero LCM and satisfy exact uniqueness, while 3,410 have
  nonzero LCM and exactly one solution below it. This explicitly covers every
  one-zero modulus case, not only `(0,0)`.
- The campaign now records 119 private candidate references and 144 exact
  receipts without public admission; registry/catalog counts remain 409/410.
  The integrated source gate passes 30 campaign-structure and 206
  proof/admission tests. Independent knowledge-base, snapshot, and vault gates
  confirm 410 catalog rows, 409 public theorems, and 508 notes with 5,119
  resolved links. Browser/deployment contracts pass 25 tests; the regenerated
  178-source application is sealed as `a-1963d4a52744`
  (`BUILD=2026-08-04f`).
- The warning-free 47-source Jupyter Book rebuild passes non-executing
  integrity over 2,325 HTML pages. The source and built proof explorers are
  byte-identical 2,285-file trees, with no broken, escaping, fragment, unsafe,
  or remote-runtime links. The 2,493-file HTML tree contains 87,499,779 bytes
  and has SHA-256
  `3d2acf4edad4774379b3d618fcd16612e9bb9d855638e20f8936b862599a4fac`.
  No deployment or public admission is claimed.

## 2026-08-04 — Generalized-CRT M5e executable boundary closed

- Added the two-row isolated `ha_generalized_crt_decision_candidate.py`
  layer. `mod_eq_decidable` proves
  `ModEq(d,a,b) \/ ~ModEq(d,a,b)` for every natural modulus. It constructively
  decides `d=0`; the zero branch decides `a=b` and uses both halves of
  `mod_eq_zero_iff_eq`, while the nonzero branch calls public
  `mod_eq_decidable_nonzero`. No host `%` operation reaches the statement or
  proof.
- `generalized_binary_crt_solution_or_obstruction` assumes supplied
  `IsGCD(g,m,n)` and returns the strong paired output
  `(ModEq(g,a,b) /\ exists x. CRTSolution(x)) \/
  (~ModEq(g,a,b) /\ ~(exists x. CRTSolution(x)))`. Its positive branch uses
  total M5b sufficiency; its negative branch uses the direct
  `crt_incompatibility_obstructs_solution` theorem. The compatibility or
  incompatibility certificate is retained alongside existence or
  unsolvability, and M5d canonicalization remains a separate composable API.
- Body receipts `(dependencies,commands,nodes,depth,objects,edges,reused)` are
  `(3,35,47,16,47,46,0)` and `(3,36,43,22,43,42,0)`. Empty-context receipts
  `(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` are
  `(2339,70,1217,1278,62,44,0,
  298e2b18fff84bcf3a2ec69dbc464454f958d4155b7afb687f0bab2fd95efe7e)`
  and `(14182,80,3909,4090,182,182,0,
  16e7cb1c430fa4e17ea878adc72d34c92e0bc3f135c4a3cf24cb2a296b38e525)`.
  Two cold passes agree, false endpoint mutations fail, both certificates
  contain zero DNE, and no kernel or resource limit changed.
- Retained bounded semantics cover 847 congruence decisions with `d<7` and
  `a,b<11`: 311 positive and 536 negative. They also cover all 5,929 CRT
  systems with `m,n<7`, `a,b<11`: 4,021 return compatibility plus a solution,
  and 1,908 return incompatibility plus unsolvability. The `(m,n)=(0,0)`
  boundary contributes 11 compatible and 110 incompatible residue pairs.
- The campaign now records 121 private candidates and 146 exact receipts,
  without admitting a theorem; public registry/catalog counts remain 409/410.
  The integrated source gate passes 30 campaign-structure and 212
  proof/admission tests. Independent knowledge-base, snapshot, and vault gates
  confirm 410 catalog rows, 409 public theorems, and 508 notes with 5,119
  resolved links. Browser/deployment contracts pass 25 tests; the regenerated
  179-source app is sealed as `a-ef0683604e9b` (`BUILD=2026-08-04g`).
- The warning-free 47-source Jupyter Book rebuild passes integrity over 2,325
  HTML pages. The explicit and defined proof explorers remain byte-identical
  2,285-file source/built trees, with no broken, escaping, fragment, unsafe,
  or remote-runtime links. The 2,493-file HTML tree contains 87,508,603 bytes
  and has SHA-256
  `ff252854e07935c02016e79b44d831e440aa91c308875181427a72cc90ab3941`.
  No deployment or public admission is claimed. M5f below adds the raw-input
  wrapper that constructs its own relational gcd; minimal admission review
  remains separate.

## 2026-08-04 — Generalized-CRT M5f raw-input total decision closed

- Added the one-row isolated
  `ha_generalized_crt_total_decision_candidate.py` layer. Its theorem
  `generalized_binary_crt_total_decision` accepts arbitrary `m,n,a,b` with no
  supplied gcd witness. It obtains `g` from `gcd_exists_relational`, retains
  `IsGCD(g,m,n)` in the output, and applies
  `generalized_binary_crt_solution_or_obstruction` to return either
  compatibility with a CRT solution or incompatibility with a proof that no
  CRT solution exists. Its only direct dependencies are those two theorems.
- The exact statement SHA-256 is
  `42d29bf501421be60c1a2b14fa858a14abf230eee2f7669503db019d6b014151`.
  The dependency-curried body receipt
  `(dependencies,commands,nodes,depth,objects,edges,reused)` is
  `(2,17,42,25,42,41,0)`. The empty-context receipt
  `(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` is
  `(15492,82,4052,4240,189,192,0,
  c2d915d2eb60ccbb2dac9f31e9e1f9c310c28264b74483ec97ae33a1a0d965ee)`.
  The closed certificate contains zero DNE and stays within the unchanged
  kernel and resource limits.
- Retained raw-input semantics cover all 5,929 bounded systems with
  `m,n<7` and `a,b<11`: 4,021 return a relational gcd, compatibility, and a
  solution; 1,908 return a relational gcd, incompatibility, and
  unsolvability. The gcd-zero boundary contributes 11 compatible and 110
  incompatible residue pairs.
- Campaign evidence now contains 122 private candidates and 147 exact
  receipts across 27 candidate modules and 30 focused test paths. The
  generalized-CRT tranche has 29 rows in total: 28 new rows and one reused
  support row. This endpoint does not add a primitive gcd function and does
  not choose a canonical bounded solution; the M5d canonicalization layer
  remains separate. Deliberate public admission and finite lifting remain.
- The integrated source gate passes 30 campaign-structure and 217
  proof/admission tests. Independent knowledge-base, snapshot, and vault gates
  confirm 410 catalog rows, 409 public theorems, and 508 notes with 5,119
  resolved links. Browser/deployment contracts pass 25 tests; the regenerated
  180-source app is sealed as `a-5f816312f00a` (`BUILD=2026-08-04h`).
- The warning-free 47-source Jupyter Book rebuild passes integrity over 2,325
  HTML pages. The explicit and defined proof explorers remain byte-identical
  2,285-file source/built trees, with no broken, escaping, fragment, unsafe,
  or remote-runtime links. The 2,493-file HTML tree contains 87,516,482 bytes
  and has SHA-256
  `59d566a0af7a86a36cca7cd02958f27ba244e10871a222c5a4dcf2ccbf94efe4`.
  No deployment or public admission is claimed.

## 2026-08-04 — Generalized-CRT M5 selectively admitted

- Admitted the exact 23-row candidate-factory closure of the three durable M5
  endpoints: `generalized_binary_crt_solvable_iff`,
  `generalized_binary_crt_canonical_boundary`, and
  `generalized_binary_crt_total_decision`. The rows occupy public runtime
  indices 409--431 in dependency order. This is a selective interface, not a
  wholesale promotion of every convenience candidate.
- The retained public surface covers congruence transport and necessity,
  constructive compatibility sufficiency for all natural moduli, the
  solvability equivalence, classification modulo relational LCM, the honest
  zero/nonzero canonical boundary, compatibility decision, supplied-gcd
  solution-or-obstruction, and the raw-input wrapper that constructs an
  existential relational gcd. The dedicated admission gate binds every row
  to its isolated factory and statement digest, checks append order after K4,
  performs two cold public replays with frozen receipts and zero DNE, and
  rejects false endpoint mutations.
- Exactly six rows remain private: `mod_eq_add_cancel_left`,
  `mod_eq_add_cancel_right`, `mod_eq_unscale_nonzero`,
  `factor_nonzero_right`, `is_gcd_nonzero_coprime_quotients`, and
  `generalized_binary_crt_solvable_iff_nonzero`. Thus the campaign now records
  95 public references, 99 private candidates, 147 exact receipts, 22
  candidate modules, and 31 focused test paths.
- The synchronized runtime contains 432 checked theorems. The 433-row catalog
  consists of 23 `checked_existing`, 409 `checked_m20`, and one
  `blocked_by_language` row. The regenerated snapshot contains 1,982,360
  structural nodes, 468,010 proof objects, 57,692 structural Cut occurrences,
  373 Cut-bearing theorems, and 1,185 dependency edges. Its ordered root is
  `4d02dc439d53533e8992a471b26ee34059fb6001f822041e42c56b2cc0a7a079`.
- The synchronized knowledge vault contains 432 theorem notes, 531 total
  notes, and 5,377 resolved links.
- The integrated admission gate passes 30 structural and 220
  proof/admission tests. All 25 browser/deployment contracts pass. The
  regenerated 180-source local browser app is sealed as `a-b544a04993a1`
  (`BUILD=2026-08-04i`); it has not been deployed.
- The warning-free 47-source Jupyter Book rebuild passes 26
  source/explorer tests and its integrity gate over 2,325 HTML pages. The
  explicit and defined explorer source/built trees are byte-identical at
  2,285 files and 72,886,197 bytes, with SHA-256
  `b2085d2c1d2445e78cd216b88cc5162ae7d67c3292d36ec87900856574cda5ea`.
  The 2,493-file, 88,026,160-byte HTML tree has SHA-256
  `d9eddd01a0dcc228ceb17b75c8595f743c7e2b6bdcb1ba44e9c260e98b33f558`
  and zero broken, escaping, fragment, unsafe, or remote-runtime links.

## 2026-08-04 — First HA-K3-PAIR-1 proof round closed

- Added the seven-row literal constructor seed in
  `ha_pair_cell_seed_candidate.py`. It proves D01 pair construction,
  fixed-component output functionality, D02 validity of the literal
  constructor, D06 cell construction and nonzeroness, D05/D06 disjointness,
  and construction of one D08 map entry. The last statement is deliberately
  not described as a finite-map representation.
- Added the six-row doubled-triangular shell layer in
  `ha_pair_shell_candidate.py`: shell successor arithmetic, monotonicity, the
  doubled-right offset bound, pair-code shell lower and strict upper bounds,
  and strict code separation for strictly ordered shells. Its largest row,
  `pair_code_shell_separated`, closes at 1,600 structural nodes, depth 30,
  636 proof objects, 692 edges, 57 reused references, and 38 Cuts, with
  certificate SHA-256
  `302d87068774ecbbe5bc6883ace27243e755627e6129d276938f31dd25dad72d`.
- Added `double_add_injective` and exact D01 `pair_code_injective` in
  `ha_pair_injective_candidate.py`. The final proof uses shell trichotomy:
  either strict branch and shell separation would make the common code
  strictly below itself, so the shell sums agree; additive cancellation then
  isolates the doubled right offsets, self-doubling injectivity recovers the
  right components, and a final cancellation recovers the left components.
  Their exact closed receipts are
  `(493,25,408,430,23,15,0,
  b0905453455317eb8e7bb8e7835fd049ad6afb98dabbf865719c02e2cc5b33ec)`
  and
  `(2525,32,1121,1186,66,59,0,
  7dc47f845a11797827e8682f4223af1e083afd48af60e0e22cd56862c44d06d8)`.
- The three focused suites pass 7, 4, and 5 tests. Every row closes twice
  cold with the same DAG digest, contains zero DNE, stays within unchanged
  limits, rejects a nearby false statement or representation mutation, and
  passes bounded semantic checks. Its transitive dependency closure remains
  within K0--K2 and excludes division, remainder, beta coding, CRT,
  factorization, and classical logic.
- Bound all 15 rows into the campaign manifest as
  `closed_checked_candidate` evidence, with exact statement hashes and closed
  receipts copied from the focused audits. Accounting is now 95 public
  references, 114 private candidates, 162 theorem receipts, 25 candidate
  modules, and 34 focused test paths. The runtime and catalog remain 432 and
  433: no pair theorem has been admitted.
- The regenerated 183-source local browser app is sealed as
  `a-86a703f70af4` (`BUILD=2026-08-04j`). This is a local reproducibility
  receipt; no deployment is claimed.
- This checkpoint closes literal pair construction and component injectivity,
  not the entire pair/cell or finite-data package. Cell functionality, strict
  head/tail descent, valid-code decision, an independently justified uniform
  computation trace, variable-length lists, and finite maps remain open.
- The warning-free 47-source Book rebuild replaces the obsolete design-only
  pair paragraph with the 15-proof checkpoint and passes integrity over 2,325
  HTML pages. Its 2,493-file HTML tree contains 88,029,634 bytes and has
  SHA-256
  `11b88b5d21c4c28d13aede8976b99b8b438812d738b2a7d69e8a20e20378fb38`;
  all relative, fragment, escaping, unsafe, and remote-runtime link counts are
  zero.

## 2026-08-04 — HA-K3-PAIR-1 functionality and strict descent closed privately

- Added the three-row exact-D06 functionality factory. `cell_functional`
  strips the shared successor tag with PA2 and invokes private exact-D01
  `pair_code_injective`; `cell_head_functional` and `cell_tail_functional`
  project the resulting component equalities. Their twice-cold receipts are
  `(2550,33,1146,1211,66,60,e1cfdfcfbe2b1bfb70f51cc724280d3bc7ac046c4bd14865bf390952b412a45c)`,
  `(2569,34,1165,1230,66,61,289cb3b6a42ca39e424e40712e44a24e4b7d4c7b355c4c0bd697d75ae42dfc9f)`,
  and
  `(2569,34,1165,1230,66,61,e03fdd8affeba3e1c0c1cb6f6e496c6ac53b13469db8c9c5b517f0df9de72d5c)`.
- Added the four-row component-bound factory. `pair_left_le_code` and
  `pair_right_le_code` expose native existential-order bounds for exact D01;
  `cell_head_lt_code` and `cell_tail_lt_code` lift them through the D06
  successor to strict descent. Their twice-cold receipts are
  `(257,18,173,184,12,8,2216484e9a09321c065b6fbac742ff1763b28f799720fb4b729468cdeaa8ce3c)`,
  `(181,18,170,180,11,7,48ae46ea34331fc1cdadc03a0e510681748aeade658cf1d9783ab6e7a6740601)`,
  `(304,20,220,231,12,10,4cbccb9c232ff1ee40d05a3ee0520e5a99beeeebb645f3e5142a5c40681d1d3d)`,
  and
  `(228,20,217,227,11,9,145f2c4c0c00c4b7145a6f847e90af1dd72e500b1d88b03e7ed4fdd267d2867b)`.
- Both focused suites pass all ten checks. Every certificate is deterministic
  across two cold closures, contains zero DNE, remains under unchanged limits,
  rejects theorem and encoding mutations, and has a transitive K0--K2 closure
  excluding division, remainder, beta coding, CRT, factorization, and
  classical logic.
- Recorded all seven rows as `closed_checked_candidate` evidence in two new K3
  module records. The campaign now has 95 public references, 121 private
  candidates, 169 exact receipts, 27 candidate modules, and 36 focused test
  paths. Strict K3 contains 96 rows across 21 modules: 74 signed rows and 22
  pair/cell rows. Runtime/catalog remain 432/433 and no cell theorem is public.
- This completes the private pair/cell proof API through component
  functionality and strict descent, not the full finite-data substrate.
  Valid-code decision, an independently justified uniform computation
  history, lists, finite maps, and deliberate public admission remain open.
- The regenerated 185-source local browser app is sealed as
  `a-0d9a06f601cf` (`BUILD=2026-08-04k`). This is a local reproducibility
  receipt; no deployment is claimed. Book artifacts were deliberately left for
  the separately bound documentation stage.

## 2026-08-04 — K3B reverse cell-history bodies checked locally

- Froze `HA-K3B-CELLHISTORY-1` and the exact reverse `CellHistory` plus
  existential `CellListLen` surface definitions as a post-K4/M3 bridge. This
  work is outside the strict-K3 division/CRT quarantine and does not alter its
  evidence ledger.
- Completed all eight theorem rows in the first-ten ladder as
  dependency-curried bodies checked by the ordinary intuitionistic kernel.
  Exact
  `(dependencies,commands,nodes,depth,objects,edges,reused)` receipts are
  `cell_history_nil = (2,24,135,18,135,134,0)`,
  `cell_history_extend = (5,86,122,36,122,121,0)`,
  `cell_history_succ_elim = (3,43,59,23,59,58,0)`,
  `cell_list_zero_iff_nil = (2,24,33,16,33,32,0)`, and
  `cell_list_succ_iff_cell = (2,38,51,19,51,50,0)`,
  `cell_list_length_functional = (5,119,163,42,163,162,0)`,
  `cell_list_length_le_code = (5,43,49,22,49,48,0)`, and
  `cell_list_length_total = (3,22,58,32,58,57,0)`.
- Classified that checkpoint as **BODY-CHECKED only**. At that point only
  `cell_history_nil` had a known prior empty-context receipt; job `219203`,
  recorded in the next entry, later cold-closed all eight theorem rows.
- Expanded `make ha-k3b-cell-history-check` as the deliberately separate light
  structural/body gate for the RFC and all five focused candidate suites. It
  is not part of `ha-number-theory-check` yet. No
  theorem is claimed closed or admitted, and the campaign JSON is untouched:
  strict K3 remains 96 rows across 21 modules and accounting remains
  95 public references, 121 private candidates, and 169 receipts.

## 2026-08-04 — K3B first-ten empty-context closure completed on WMI

- WMI job `219203` completed two deterministic empty-context closure passes
  for all eight theorem rows in `HA-K3B-CELLHISTORY-1`. Scheduler evidence is
  `COMPLETED 0:0`, node `c3n1`, elapsed `00:04:46`, and `MaxRSS=82428K`.
- Exact closed receipts in order
  `(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)` are
  `cell_history_nil = (155,18,155,154,0,2,a3038bd67616f11f8e97727c98f03af09aacde863a70637d9575e2ff9d337ff8)`,
  `cell_history_extend = (29352,81,4651,4879,229,241,370de792b2c3fed8b3d36f90147c426b846d15578cac8c66520a59df81750c78)`,
  `cell_history_succ_elim = (1245,60,772,810,39,27,e8aee67cfef618fde3b08d48dffb4a6b31cdd22a578e38206d4e5a20a96c338c)`,
  `cell_list_zero_iff_nil = (1309,60,880,916,37,26,f7fdef58a28a86bd70b133bf839f6b49526817e020da6c698b85b3cd369f2f73)`,
  `cell_list_succ_iff_cell = (30648,83,4761,4992,232,246,a64ad8e5095d50afe10b47b1036ad9b680ab82462b41beb115d23956f9fa5699)`,
  `cell_list_length_functional = (34732,85,5700,5976,277,299,5dd0e4b8f585990ec826ba5ef02960cb6817f0aec5edcb86c9bb1e22d44c5a6c)`,
  `cell_list_length_le_code = (31002,84,4891,5129,239,257,50fe47364958e1a506315935796e517f41ddd947a1792fcdb134956ba05290a9)`, and
  `cell_list_length_total = (29569,84,4848,5078,231,246,2d6063d54e16c0f093aab270329bdd4ca5a7c02aa68b528c2c7c771945ccba17)`.
- Every certificate contains zero DNE. The collected report
  `artifacts/peano-library/ha-k3b-cell-history-closure-219203.json` has
  SHA-256
  `6ef49fcb5edb2b1c5478ff592c97dc9af56ed2f79ec03308c5ebf341833b825c`
  and binds clean commit `0b33b6675481a93d0e330987b22d9ef91564a0a0` to payload
  `edf77bff5cf824cbfd549179f8cef2a18ac65904d473ce3bbd2bd5e5f1c95620`
  (3,911,680 bytes, 201 entries).
- Gates G1--G6 pass, as does G7's quarantine/closure portion. Public
  admission remains deliberately open: all eight rows are private,
  unregistered, unadmitted `closed_checked_candidate` evidence. The campaign
  JSON is unchanged at 95 public references, 121 private candidates, and 169
  receipts; strict K3 remains 96 rows across 21 modules.

## 2026-08-04 — K3B outer-head lookup surface frozen

- Added `HA-K3B-LISTAT-1` with the canonical reverse-history lookup equation
  `j + S i = l`, so index zero denotes the outermost head. The exact witness
  order is `l b c j t u` and raw beta-code equality remains hidden.
- The fully expanded unchanged-PA surface is 3,331 characters, 54 formula
  constructors, and 210 AST nodes with SHA-256
  `b83d91b6ec8e6b83fe637e1533c72beef54c7e7a4b41f1518bce8785cc9f11ce`;
  all seven focused hygiene and small-model checks pass.
- Froze a ten-deliverable ladder through equations, existence, functionality,
  representation independence, and extensionality. The dependency review
  found one necessary first lemma: `cell_history_extend_preserves_prefix`.
  The old extension result proves existence of a new history but intentionally
  hides the pointwise map needed to lift an old lookup.
- Implemented that support row with a dependency-curried body receipt
  `(5,99,139,37,139,138,0)`. Four focused tests pin its 3,799-character
  surface, 104-row closure, constructive body, mutations, and the exact
  `4,1` to `96,2` recoding boundary.
- WMI job `219209` completed two deterministic cold passes in `00:02:14` on
  `c3n1`, `MaxRSS=85664K`. Its exact closed receipt is
  `(29369,81,4668,4896,229,241,7fd7734ab34d90a869c637e76e138db692ba21d4f2bbec41af9817c38ef36498)`;
  the 1,333-byte report SHA-256 is
  `0d51baf93121da4071d0bb3ebd2b4a2818a7658fa92510fd707620bc2dba6560`.
  The result remains private, unregistered, and unadmitted; registry,
  campaign JSON, and public counts are unchanged.
- Completed the dependency-free `list_at_domain` projection. Its statement
  has 5,903 characters, SHA-256
  `065291362205b70ef41fff597d1d8762bff06ce7d3a5bead5dbcd8b97ea8a240`,
  and its exact body/closed certificate receipt is `(0,19,39,23,39,38,0)`.
  Three focused tests pin witness order, a false strengthened bound, zero
  Cut/DNE, registry isolation, and a distinct-head two-cell model. It remains
  private pending the next repeated cold lookup batch.
- Checked the private `list_at_head_iff` body against its four direct
  dependency hypotheses: `cell_history_succ_elim`,
  `cell_history_extend_preserves_prefix`, `beta_at_unique`, and `le_refl`.
  The expanded statement receipt is
  `(12530,9f0b3e7496f79b7cc6f4833edc14431dd614081b6f02b2d384aa80c521e2f8ed)`;
  its exact body receipt is `(4,119,265,36,255,264,10)`. In the forward
  implication, beta uniqueness first aligns the selected successor with the
  history terminal at `S j`, then aligns the selected tail with the
  predecessor-history terminal at `j`. This removes the initially proposed
  `cell_tail_functional` dependency. Prefix preservation supplies the reverse
  implication. At this body checkpoint, cold closure had not yet run;
  admission, registration, catalogs, JSON accounting, and public snapshots
  were unchanged.
- Checked the private `list_at_succ_iff` body with exact direct dependencies
  `cell_history_succ_elim`, `cell_history_extend_preserves_prefix`, and
  `add_comm`. Its expanded statement receipt is
  `(14716,004ef041acbcfbaaeda594f5f47fbea75ac6f8df87ca8bcf49774cfcbc3a978c)`
  and body receipt is `(3,124,198,38,196,197,2)`, with zero DNE. The forward
  implication keeps the original `b,c` trace after successor elimination and
  repackages the selected edge in the predecessor history. The reverse
  implication preserves both beta endpoints: `S i` witnesses the bound for
  `j`, while `i` witnesses the bound for `S j` after PA4 and `add_comm`.
  This replaces the provisional rung-4/PA2 dependency route. At this body
  checkpoint, cold closure had not yet run; registration, admission, catalogs,
  JSON accounting, and public snapshots were unchanged.
- Checked private `list_at_external_bound` with direct dependencies
  `list_at_domain`, `cell_list_length_functional`. Its statement receipt is
  `(7481,a86efefaf31c9bfce0cd146f6aab932f22962b688fdc7f6bc4dd0beeb40bc9f8)`
  and body receipt is `(2,23,28,17,28,27,0)`. The hidden-length witness is
  compared to the declared length in orientation `l=m`, then the lookup bound
  is rewritten forward.
- Checked private `list_at_exists` with sole direct dependency `add_comm`. Its
  statement receipt is
  `(6883,aeb4f15d9a96492b096f869e9361db6a31bce9a59041b1dd9f87fe221df2278c)`
  and body receipt is `(1,45,60,26,60,59,0)`. From `j+S i=l`, PA4 and
  commutativity derive `i+S j=l`, and the universal history edge clause
  constructively supplies the returned head. Both new bodies have zero DNE.
  This remains body-level evidence only; cold closure, registration,
  admission, catalogs, JSON accounting, and public snapshots are unchanged.
- Checked private `list_at_functional` with exact direct dependency order
  `list_at_head_iff`, `list_at_succ_iff`, `cell_functional`. Its statement
  receipt is
  `(8895,1eba38bb47901319d41e681ed77f218b437e4d2ff1d55f519fff82e7dc8f2361)`
  and body receipt is `(3,95,119,40,119,118,0)`. The generalized induction
  motive ranges over the code and both candidate values. The base case takes
  the head component of joint cell functionality; the successor case takes
  its tail component, aligns the recursive lookups, and applies the induction
  hypothesis.
- Checked private `list_at_history_independent` with exact direct dependency
  order `list_at_functional`, `add_comm`. Its statement receipt is
  `(7581,d0a1ac158e6e0552a8e762b69b602da0157183c832ec0cf4c270586dffcc914d)`
  and body receipt is `(2,92,171,38,171,170,0)`. The proof selects the same
  edge in the second history, converts its bound through PA4/commutativity,
  constructs the two client lookups, and rewrites only their decoded heads.
  This removes the provisional T07/`beta_at_unique` route and never compares
  raw beta codes. Both T08 and T09 bodies have zero DNE. These are body-level
  checkpoints only: cold closure, registration, admission, catalogs, JSON
  accounting, and public snapshots remain unchanged.
- Checked private `cell_list_extensional` with exact direct dependency order
  `cell_list_zero_iff_nil`, `cell_list_succ_iff_cell`, `list_at_head_iff`,
  `list_at_succ_iff`. Its statement receipt is
  `(15451,7033fcdf4c96a866e9d9e0b8381efbbd7b48ab060bcc4adad695ead30ff19831)`,
  PA AST receipt `(707 total nodes,192 formula nodes)`, and body receipt
  `(4,152,386,50,369,385,17)`. The generalized induction proves nil equality
  at zero. At a successor, the two length decompositions expose heads and
  tails; pointwise equality handles index zero, while PA4/congruence lifts
  each tail bound so the successor lookup equation and induction hypothesis
  identify the tails. Two head and four tail rewrites normalize exact D06.
  The body has zero DNE.
- The ten-deliverable ladder now has checked evidence throughout: T01 is its
  frozen definition surface and T02--T10 have checked theorem bodies. This is
  not admission evidence. The subsequent full cold seal is recorded below;
  registry, catalogs, campaign JSON, public snapshots, and public theorem
  counts remain unchanged.

## 2026-08-04 — K3B full history/lookup cold seal completed on WMI

- WMI job `219217` closed all 17 selected history and lookup targets twice
  from the empty context. It completed `0:0` in `00:15:25` with
  `MaxRSS=54,496 KiB`; the two passes are deterministic and every certificate
  has zero DNE.
- Exact T03--T10 receipts in order
  `(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)` are
  `list_at_domain = (39,23,39,38,0,0,09c7d6d2bb9d7cd09597285eae31355cf76b8bc54d7c370f8c9507ca0377a701)`,
  `list_at_head_iff = (32025,83,4982,5225,244,248,52bb6c215c7123e58374d23935490c71eccd3a8704de193612dacb57dd33cba7)`,
  `list_at_succ_iff = (30885,83,4923,5157,235,247,908364a06285830d2cc6b53919b4399203b12d08c89b9bb98de3cdd4efa5b8fa)`,
  `list_at_external_bound = (34799,87,5767,6043,277,301,7c49ab5ac74468bf1537d510be4d0837bc97d2432727a3c25f00c80026a38663)`,
  `list_at_exists = (133,26,127,132,6,3,6778f7b507370cb1bcd95d2bd90b0fbaea317f5ac262565152dc5eabf759698c)`,
  `list_at_functional = (65579,85,5851,6140,290,296,00fc80f2b18c79f8e45a41682651c32c0fbe8b34bc39c8ca2186067c184d0a4a)`,
  `list_at_history_independent = (65823,86,6022,6312,291,298,8868aaef643ffe84c4b5fb885d2f16c7b4872f071ce5de92149369d60c3dc20b)`, and
  `cell_list_extensional = (95253,87,5888,6162,275,266,8558cf1c4c39c0d0d8b363e7304a6c5732cee0593548a4137d1407de58f479ec)`.
- The authoritative 10,550-byte report
  `artifacts/peano-library/ha-k3b-listat-full-closure-219217.json` has SHA-256
  `c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8`.
  It binds clean commit `cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e` to payload
  SHA-256
  `78e0c3d04b98ba1788edce0cd227dae3f7fe36f391a3a80b962da632a1970835`.
- This is closure evidence, not admission evidence. All 17 targets remain
  private, unregistered, and unadmitted. No registry, catalog, snapshot,
  campaign-JSON, or public-count change follows from this seal.

## 2026-08-09 — Alpha v1 and Stable became explicit library editions

The campaign's release model is now explicit and supersedes the older binary
wording in which a reviewed row was either in the public registry or described
as private/unregistered. Every reviewed building-library row belongs to
**Alpha** as soon as it is incorporated; only a separately audited promotion
makes it part of **Stable**. Stable remains the default checked-use edition and
is a subset of Alpha. Edition membership does not imply proof evidence, and
neither fact implies hosted deployment.

- The unchanged Stable edition contains 432 theorems, 1,185 declared direct
  dependencies, and 22 layers.
- The sealed Alpha v1 edition contains 885 theorems, 2,641 declared direct
  dependencies, and 45 layers: 432 Stable plus 453 Alpha-only rows.
- Alpha evidence is exactly 432 `stable_closed`, 138 `alpha_closed`, 314
  `body_checked`, and one `pending_layered_closure`. Thus 570 rows are
  checked-use facts and 315 still lack an empty-context closure metric.
- Canonical Alpha order is Stable, QR candidate order, unique strict-HA rows,
  then K3B; its ordered-enrollment root is
  `7371461aa930071f00007f766f899cef88c4126a5ddf576f93d79e336bc65c49`.
- `peano_lab.library.editions` now exposes `edition`, `entry`, and `replay`
  with explicit `stable`/`alpha` selection. Stable is the default. Alpha
  `replay` accepts only `stable_closed` or `alpha_closed` rows and fails closed
  for body-only and pending rows.
- Deterministic channel state lives in
  `artifacts/peano-library/channels.json`; Alpha's catalog, metrics, and
  display dependency graph live under `artifacts/peano-library/alpha/`. The
  pre-existing Stable snapshot was not rewritten.
- Alpha's reachability reduction reports graph structure for review and
  display. A reachability-redundant declared dependency may still be used
  directly by the tactic body, so the report is not proof-semantic minimality.

At the v1 boundary, promotion remained deliberately open. Whole-Alpha-v1 cold
closure was missing for 315 rows, and the WMI cluster was down for the
weekend. No Stable promotion or WMI
seal is claimed by this edition enrollment. Earlier dated passages calling
the affected rows private or unregistered remain valid historical checkpoint
records; their current interpretation is **Alpha-only, not Stable**.

## 2026-08-09 — K3C appended as Alpha v2 body evidence

The next finite-data layer adds conservative `CellListValid` and `ListMember`
notation and seventeen theorem rows. The exact append occupies Alpha indices
885--901 in the frozen order documented by
`research/arithmetic-library/ha-cell-list-validity-membership-rfc-v1.md`.
All expanded statements parse in the unchanged PA language; all
dependency-curried tactic bodies check in the intuitionistic kernel; declared
direct dependencies survive removal tests; and false-conclusion mutations are
rejected. This is body evidence, not empty-context closure evidence.

- Alpha v1 remains sealed at 885 specifications. Alpha v2 preserves all 885
  parent entries exactly and appends only the 17 K3C rows.
- Alpha v2 contains 902 specifications, 2,674 declared direct edges, 45
  layers, and 470 Alpha-only rows. Its origins are 432 Stable, 316 QR, 120
  strict-HA, 17 K3B, and 17 K3C.
- Evidence is 432 `stable_closed`, 138 `alpha_closed`, 331 `body_checked`, and
  one `pending_layered_closure`. Checked use is unchanged at 570; 332 rows
  remain unavailable as empty-context facts.
- The v2 ordered-enrollment root is
  `00f1a70a0911c44acd6b784f2b121b2c351ae626a0f18bb08b5a829496ad40fe`;
  its full edition identity is
  `aadf99c0e411fcefe34285c8396ff0652f590e6990f0d55c3e6c7b728f9b43a4`.
- `artifacts/peano-library/channels-v2.json` records the additive channel
  pointer without rewriting `channels.json`, Alpha v1, or the 432-row Stable
  snapshot.
- The exact v2 artifact hashes are catalog
  `90ac4942df043e59ade7a62a87627ef3b29d9b1d7d251c8fa6aadefe77590bd7`,
  metrics `85907aea9e6fece33c8f4d0d40d167945f3118190654a32423dc815df8fc69eb`,
  reduced graph
  `01ca3e6b58e55cfefd4a0df3f8ce229f5382c26a02f4960ceb7773205c9177a3`,
  and channel pointer
  `c2af6774ea7c787532d79a5f8fd41087ae5f31a0e828e25571adaed2853aa968`.
- K3B's seventeen selected roots are now correctly described as Alpha-only
  `alpha_closed` rows, not current private rows. K3C's seventeen rows are
  Alpha-only `body_checked` rows and fail closed through the checked-use API.
- A non-submitting closure harness and reviewed `cpu_idle` Slurm wrapper are
  ready at `scripts/run_wmi_k3c_cell_list_closure.py` and
  `slurm/peano_wmi_k3c_cell_list_closure.sbatch`. They pin the exact 17-row
  surface, Alpha-v2 parent identity, two deterministic passes, zero DNE,
  resource/provenance fields, and fail-closed atomic report creation.

WMI is unavailable for the weekend, so the repeated isolated K3C
empty-context closure receipt remains pending. No K3C row has been promoted
to Stable, and no cold-closure metric or artifact hash is inferred from the
local body checks.

## 2026-08-09 — Bertrand campaign round 1 and Alpha v3

The new flagship campaign was frozen as “prove Bertrand's postulate
completely in our arithmetic system.” The exact native endpoint and an
integer-only Erdős/Tochiori route are recorded in
`research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md`.
The campaign is constructive: bounded interval search returns either an
actual prime or a finite pointwise exclusion certificate, so the final proof
does not obtain an existential by double-negation elimination.

Six small, reviewable commits were sealed locally and pushed:

| Commit | Tranche |
|---|---|
| `10dc017` | quantitative order and power-base foundations |
| `6739532` | binding RFC plus constructive bounded prime-interval search |
| `be5b735` | bounded greatest-exponent power valuation |
| `941ad70` | selected valuation power and successor nondivisibility |
| `3ce8a90` | additive, fail-closed Alpha v3 channel |
| `9efc5cd` | native six-step integer-envelope feasibility tranche |

Alpha v3 preserves the exact 902-row Alpha v2 prefix and appends 21
body-checked Bertrand specifications at indices 902--922. It has 923 rows,
2,730 declared edges, 45 layers, 432 Stable rows, 491 Alpha-only rows, and
570 checked-use rows. Evidence is 432 `stable_closed`, 138 `alpha_closed`,
352 `body_checked`, and one `pending_layered_closure`. Enrollment and edition
identities are respectively
`4507736cde37301ecf3369540d6cc686de860b07b101f2afb60f850f86aeebd4`
and
`e20eefac839fb2bcd3e696989c091a5f6837de04824f94e1073723851a471a2f`.

Independent audits replayed the bodies intuitionistically, removed each
declared dependency, replaced direct Cuts, attacked false conclusions, and
checked local recursive closures. Representative closure maxima are 125,485
nodes for prime valuation existence, 70,898 for exponent monotonicity, 7,632
for the successor-nondivisibility bridge, and 213,731 for the six-step
integer guard. Every maximum is below the unchanged 500,000-node,
depth-256, 100,000-object policy, so no limit increase is justified.

The first 21 Alpha-v3 rows remain `body_checked`; the repeated fresh-process
cold closure receipt is pending and checked use therefore stays 570. The six
post-v3 valuation laws and five integer-envelope lemmas have local closure
evidence but are not yet enrolled. Bertrand's postulate, binomial
coefficients, Legendre's formula, prime-product bounds, and the final large-n
inequality are not claimed complete.

## 2026-08-09 — Bertrand Round 2 sealed as Alpha v4

Round 2 closed the valuation-multiplication and discrete floor/ceiling
infrastructure needed by the Erdős route. The following commits were pushed
after the Alpha-v3 documentation checkpoint:

| Commit | Content |
|---|---|
| `d6dac45` | ceiling-by-six and floor-square relation laws |
| `3cc6994` | constructive FloorSqrt totality, uniqueness, monotonicity |
| `654aab2` | two-fresh-process Alpha-v3 closure infrastructure |
| `bdb9cf7` | retained safe root-level Slurm failure diagnostics |
| `88d9e92` | exact prime-power valuation multiplication |
| `139b6ce` | quotient complement and $q+e\le n$ budget |
| `e605faa` | additive, fail-closed Alpha v4 artifacts/runtime |

The exact multiplication theorem proves $v_p(ab)=v_p(a)+v_p(b)$ for prime
$p$ and nonzero $a,b$. Its tightened empty-context certificate contains
297,211 nodes at depth 98 and 7,438 objects; all 39 declared dependencies and
all 39 direct Cuts reject mutation. The floor/ceiling bridge constructs
$c$ from $2n=3q+r$ and proves $q+c=n$, $2n\le6c$,
$\lceil s^2/6\rceil\le c$, and $q+\lceil s^2/6\rceil\le n$.

Alpha v4 preserves all 923 v3 rows and appends the 42 reviewed Round-2 bodies
in source blocks of 6, 11, 5, 9, 4, and 7 rows. The resulting edition has 965
specifications, 2,891 edges, 45 layers, 533 Alpha-only rows, and 570
checked-use rows. Evidence is 432 `stable_closed`, 138 `alpha_closed`, 394
`body_checked`, and one `pending_layered_closure`. Enrollment and edition
roots are respectively
`e4c83174c1800c135d0fe9ac03b5cdfcc5f11e5517f871b3f198586973a20c31`
and
`e0324009614f755f2251a5b27d29587b0c43015385a78d567b328776b92239a5`.

The full v4 gate passed deterministic build and independent verification,
15 artifact/mutation tests, 37 runtime/candidate tests, and all historical
v1--v3 gates. Every new row remains body-only and replay fails closed. WMI is
still unavailable, so no admission-eligible cold receipt or Stable promotion
is claimed.

## 2026-08-09 — FactorialVal sealed as Alpha v5; next candidates pushed

Four further checkpoints were pushed in dependency order:

| Commit | Content |
|---|---|
| `05cb3ff` | seven recursive factorial-valuation proofs |
| `f35b8ed` | eight $n\ge2048$ threshold and residue-window inequalities |
| `4df44c9` | five-row finite Legendre-sum interface |
| `85625d6` | additive, fail-closed Alpha-v5 artifacts/runtime |

The FactorialVal tranche proves factorial nonvanishing, valuation of one,
general graph existence and functionality, and the prime zero, successor, and
successor-inversion laws. Its maximum local recursive certificate is 432,090
nodes at depth 105. Those checks establish feasibility and mutation
resistance; the seven enrolled rows remain `body_checked` and are not exposed
as empty-context facts.

Alpha v5 preserves the exact 965-row v4 prefix and appends those seven rows at
indices 965--971. The resulting edition has 972 specifications, 2,912 edges,
45 layers, 540 Alpha-only rows, and 570 checked-use rows. Evidence is 432
`stable_closed`, 138 `alpha_closed`, 401 `body_checked`, and one
`pending_layered_closure`. Enrollment, specification, and edition roots are
respectively
`46e1a08c6bc18bbc057aa7541420580b43aec75d5f30af500ba3ce12bec09473`,
`4592f0abba7b9f592d4f94780ced57c3e7e0b935444155f76276f1fd2b4d8ae4`,
and
`bccf7d8fc01dbcd1cd2efd9d5d8e5189d80b79cfb7e5e30df999d270a9fd13af`.
Artifact hashes are catalog
`94efc0f7022f31677619e842f7d6f1d0d0f8959efc54cd64cf346c3b5e8c4892`,
metrics
`b560373c8cb4879f47e46083d5b9925cd29ebee1af4856cfc93e74017555acc2`,
graph
`4e8f1ea73b3ecfd51cf80d216dfc9171dabbe12f38d9c8392185ea1c610112ab`,
and channels
`946682733744d6969e89059df9165cc2782510101d4ee43a6a861aa7570a3f31`.

The threshold tranche and finite Legendre-sum interface passed their focused
body, closure, semantic, dependency-removal, and direct-Cut audits and are
pushed candidates only. They are not members of Alpha v5 and cannot be used
through its replay API. In particular, the Legendre interface constructs and
uniquely transports the encoded quotient sum; it does not yet identify that
sum with the factorial valuation. The relational-power bridge remains under
audit. Legendre's equality and Bertrand's postulate remain open.

## 2026-08-09 — Twenty-one reviewed bridge rows sealed as Alpha v6

The next additive channel was published at commit `5b189f0`. Alpha v6 keeps
the sealed 972-row Alpha-v5 catalog byte-for-byte as its parent and appends
exactly twenty-one reviewed Bertrand rows at indices 972--992. Their frozen
dependency-topological split is eight threshold-base inequalities, five
finite Legendre-sum interface rows, five relational-power bridge rows, and
three Legendre-valuation bridge rows. The author gates rebuilt the artifacts
deterministically, independently replayed all twenty-one bodies, and passed
the fail-closed verifier and mutation suite.

The edition now has 993 specifications, 2,977 declared direct edges, 45
layers, 432 Stable rows, 561 Alpha-only rows, and 570 checked-use rows.
Evidence is 432 `stable_closed`, 138 `alpha_closed`, 422 `body_checked`, and
one `pending_layered_closure`. Every appended row has `checked_use=false`, a
null proof tag, and null empty-context closure metadata. Thus the successful
body and local-closure checks do not advertise any of these rows as an
empty-context admitted theorem.

Enrollment, specification, edition, membership, evidence, and channel-pointer
roots are respectively
`dc25a3dc0ab7346f9188eee1262700b40bb09efdacfa849f3a27475ed870b5a7`,
`50f395c30e4f21a7b7602bc56451bf2363d1a23d811bba62a33c08e2defc1da1`,
`7e46b80c4799e51da32cedf21a130274200fa14b21e0fec3b42f74d1523ab23b`,
`bd8faa84d1ef0c090fb07aa21ecd966d4f4356999fcd12cf4f74d0e5ae8572b8`,
`c1fcedbd7bbc5e8655dbce3b00ab0bd9296489a3b4358fb548eeb32d081e8682`,
and
`4dc0f9411227e041dbbbcc2626a04d995a6ceeedb91fe9c2d246f377596693b7`.
The suffix-depth root is
`d103de2054a0bd4de3b2faa9d98435a4f705594f8a69968e9ca956c455cb61d3`;
the fresh body-receipt root is
`c23b2fc58fabd3803a0ded5f02d4ea348d67a00b25f5b28b35f3d6bcb00ff2f1`.
Artifact hashes are catalog
`c72d6e1234aa6521b0c524720cd64912f7e9b0bc58f31b6964bbb1a99c5a071d`,
metrics
`f2a6c22b9fe50581a4cfe8d3b1b494fa274d26d0b51b60e92735650a09391be7`,
graph
`532c2482a3b1c371026bd80b1b7297faffc4a1b1ee3e53031e499f1611b3ae16`,
and channels
`6ef8bb93b2e24bdfe45389ca9417b6333ce83ae249ee49a957959a6b3471b86c`.

Two proof commits pushed before the v6 release remain deliberately outside
its manifest. Commit `5b9433a` contains five Legendre-successor ingredients;
their largest local closure measures 81,828 nodes at depth 95, with 6,931
objects and 7,226 edges. Commit `b2035ce` contains four shared-`PowTotal`
candidates. Their closures measure 5,327, 10,630, 11,062, and 13,336 nodes,
saving 59,836, 59,833, 59,836, and 119,652 nodes respectively against the
frozen historical comparisons. These are capacity and feasibility results,
not enrollment or admission.

Work on the $H/J$ base window is in progress. The finite Legendre recurrence,
Legendre's equality with factorial valuation, binomial and primorial bounds,
the final large-$n$ inequality, finite coverage, and Bertrand's postulate
remain open.

## 2026-08-10 — Bertrand proof recovery and Alpha v7

The apparent proof-run crashes were diagnosed before work resumed. macOS
jetsam reports showed two concurrent Python proof builders, each retaining
roughly 15 GB on a 16 GB host; additional Python resource reports recorded
large file-backed write volumes. This was host memory pressure, not a kernel
rejection or a failed theorem. All subsequent proof work used a single heavy
worker, explicit RSS observation, and fresh Python processes for separate
modules. The Alpha-v7 Make gate now preserves that discipline by splitting
mutation groups and heavyweight proof suites rather than accumulating all
proof DAGs in one pytest process.

Five proof checkpoints were completed and pushed before publication:

- `985a773` proves the compact three-row $H/J$ six-step transport;
- `158d87c` proves factorial valuation equals the finite Legendre sum;
- `00e8361` supplies the optimized three-row constructive initial-segment
  interface; and
- the earlier `70c5b16` and `de58034` checkpoints provide the compact $H/J$
  base window and finite Legendre recurrence used by the release.

Commit `874e81e` publishes Alpha v7 over the exact sealed 993-row Alpha-v6
parent. It appends twenty-four rows at indices 993--1016 in the frozen split
3 constructors + 5 Legendre-successor + 4 shared `PowTotal` + 2 $H/J$ base +
5 Legendre-recurrence + 3 $H/J$ transport + 2 factorial--Legendre agreement.
The resulting edition has 1,017 specifications, 3,072 declared direct edges,
45 layers, 432 Stable rows, 585 Alpha-only rows, and 570 checked-use rows.
Evidence is 432 `stable_closed`, 138 `alpha_closed`, 446 `body_checked`, and
one `pending_layered_closure`.

The deterministic builder check, independent verifier with all twenty-four
body replays, five runtime edition tests, and all thirty release-verifier
cases passed: two positive checks and twenty-eight mutation cases. The cases
were deliberately run in fresh-process groups; cases 1--26 completed before
the execution-session ceiling and cases 27--30 passed separately. Every new
row remains `body_checked` with
`checked_use=false`, null proof tag, and null empty-context closure metadata.
No theorem was promoted to Stable.

The enrollment, specification, edition, membership, evidence, and
channel-pointer roots are respectively
`aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c`,
`838c8f48f81eddcdf3e9de0f9557cee1c25eb78015513d99cfe8ab76975edc65`,
`9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff`,
`e6d22473986c7e4ec1e4566f156c3dad710a4a9be2ae7b830490546da48cb703`,
`a3709e040891b7c180c5c35876ec0e033b58ad12ce5179c3b0215ed11c1a93b6`,
and
`e868088b8abf7b98e1a3976058adfca5ed542a1d9b29c275ebd16c070cd810c3`.
Artifact SHA-256 values are catalog
`7676fc944b695d02a3aec05b428c012933258cb6cd9b465599318e690e0f6df4`,
metrics
`c40f18bda0ec8feb9294cf445d08b51daf868e46b3931daf55bad91413d39e0d`,
graph
`85a53bd719e227a31d5cff15fc25ff66abaa82d498030f5a918a7c40271abc9e`,
and channels
`fe9c11ec8a622eb759053a42ee6acb7c2bcb1d454fe0dc5fa4b729a07ffbbd30`.

The finite Legendre recurrence, the `FactorialVal` equality, and compact
$H/J$ transport are now complete at the dependency-curried body-evidence
level. Bertrand's postulate itself remains open: the all-$s$ exponential
envelope, binomial and prime-product bounds, the final large-$n$ inequality,
finite coverage, and the constructive endpoint still require proof.

## 2026-08-27 — Lower-layer saturation and additive Alpha v28

The previously completed first/second waves were sealed and pushed in
`ea90d1080a4ef59c4bd399c21097e9643aa786df`: 58 first-wave and 422 second-wave
proofs. All 34 then-current proof families were deployed from a clean detached
release checkout; the full remote checksum dry run reported zero differences.
The separate `45cb35cb` documentation repair fixed MyST query-link navigation
and passed the warning-as-error book build.

The next additive tranche contains 204 actual new proofs and closes the exact
G001–G005, G021–G022, G081, and G084 targets. Six focused mathematical suites
pass 1,412 tests. Its complete 862-node bundle is independently accepted by the
original intuitionistic kernel and compiled Lean verifier; SHA-256:
`e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1`.
The artifact has 3,090 edges, 230,464 structural body occurrences, and
18,977,050 bytes. Proof assembly uses bounded microbatches, retaining the
unchanged proof/resource guards rather than attempting one enormous replay.

Alpha v28 has 2,764 checked rows, 8,984 direct edges, and 53 layers; the 432
Stable rows and all 2,560 v27 records remain unchanged. The four new canonical
explorers expose 27 arithmetic-foundation, 19 prime-enumeration, 93 Gaussian,
and 65 Eisenstein theorem pages. Thirty-five additive hygienic definitions
bring the reviewed registry to 233 objects and 441 definition edges, sharing
the exact same signed-pair carrier and addition between the two rings.
The atlas retains open Gaussian/Eisenstein factorization and classification
goals instead of conflating them with the completed Euclidean divisions.

Historical v27 explorer inputs are preserved as hash-authenticated exact byte
snapshots; the live v28 successor uses the same public routes and unchanged
Quadratic Reciprocity design. Ongoing unrelated Hydra capacity work is not
part of this proof release and must not be staged or overwritten. Peano
production remains governed by its mandatory cache-header checks; the faculty
response observed today lacked the required Cache-Control headers. Publication
must report that blocker, not silently bypass the gate.

Final local v28 release gates accepted all 29 principal runtime proofs in
1,529.68 seconds with peak RSS 844,414,976 bytes (about 805 MiB), clearing
caches between independent roots. The final catalogue digest is
`897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`;
the edition identity is
`4936d155e8d2a39409a4e83beb4ac5cb2481948d8b6eeecf1c7571161786646b`.
The 492 admission/closure/verifier regressions, 525 definition tests, 45 new
explorer tests, 33 current-v28 historical-publication tests, and all 73
unchanged frozen-v27 explorer tests pass. The warning-as-error book build and
all 287 documented command replays pass. Public graph tests exercise actual
new-family data with getter-only SVG `href` properties; browser visual QA
cannot be claimed because no browser is connected in this session.

The seven historical publishers and their current-site regressions pass all
977 cases, including the eight real-family graph cases and both original SVG
fixtures. Current atlas/book/deployment contracts pass another 382 tests;
the UI, worker, CLI, and Lean strand integration passes 693. Four representative
Stable/v26/v27/v28 CLI exports also compile in Lean. These checks preserve the
historical first-admission evidence and do not promote any Alpha row to Stable.

The separate delivery integration authenticates the explicit v28 explorer
publication paths while retaining v27 first-admission hashes. All 216 Lean
service tests pass, including real read-only publication checks and rejection
of forged versioned paths; the live operator-owned process was not restarted.
CI is configured to check out the private Lean companion at
`d2903c8bd507b7e4458b1249f840a4e274befdbf`, provision its pinned Lean 4.31.0,
and check both verifier executables. A narrowly scoped pytest ID hook avoids
decimal conversion of huge integer parameters without changing their values,
Python's guard, proof limits, or the eight full test shards. The 30 environment
regressions and all 200 frozen binary-execution tests pass on Python 3.12;
four existing sharding tests pass. Remote CI and the exact CI toolchain build
remain separate, not-yet-observed gates at this checkpoint.

### Published release and remaining operational gates

The proof release `c4383b2d` and delivery integration `5297ae12` were pushed
normally to `origin/main`. The exact deployed candidate is
`5297ae12bf551f0e01adcc1a0ef6a6119606c2e7`, assembled in the clean detached
`vietnam2026-release-v28` checkout. `make deploy-proofs` succeeded for all 38
families and 5,316 enhanced theorem/graph pages. The full remote checksum dry
run reported **zero differences**; the preceding dry run proposed no removals.
Independent HTTPS downloads of the hub, all four new corpora, graph JavaScript,
campaign DAG, and complete v28 bundle matched their staged SHA-256 hashes.
The proof-site byte total is 402,442,162.

The managed faculty connection was restored while reusing the existing
operator-owned worker: its recorded owned worker PID is null. No existing
worker was stopped. The actual public `gaussian_equal_reflexive` v28 smoke test
passed: one Lean-verified theorem node, zero certificate fallbacks, 648 bytes
of import-free standalone Lean, a checked 632-byte compressed Lean Live URL,
and a verified seven-file download package. This is a representative live
build check, not a claim that every large root fits the browser service caps.

`make deploy-peano-next` succeeded for application `a-dea2621afe2c`, build
`2026-08-27c`; the staging file-byte comparison reported zero differences.
The mandatory delivery verifier stopped on the missing HTML
`Cache-Control: no-store` response header. **No Peano production promotion was
performed.** The clean candidate remains unchanged; the faculty hosting
administrator must restore the required cache guarantees.

[GitHub CI run 33094506741](https://github.com/nasqret/vietnam2026/actions/runs/33094506741)
passed the book and standalone Lean jobs, but all eight Peano shards stopped
before proof testing: the default Actions token cannot check out the private
`nasqret/peano-lab-lean` repository. The exact pinned companion commit exists;
it is not a missing-source or theorem failure. Dedicated read-only CI access
requires the owner's authorization. No credential was extracted or copied,
and no repository visibility or permission was changed.

The next audited dispatch is G072, G006, G010, G036, then G082, with missing
internal lemmas and exceptional cases recorded in PLAN/14. A stale G095 prose
sentence was corrected to match its actual v27 completion. All 81 affected
atlas/book tests pass. This receipt and planning correction do not change the
deployed proof bytes. Unrelated in-progress Hydra work remains untouched.

## 2026-08-27 — Authorized read-only CI access and the next five goals

The owner authorized a dedicated read-only deploy key for the private Lean
companion and an encrypted Actions secret in `vietnam2026`. A new Ed25519 key
was created for this purpose alone; the GitHub deploy-key metadata confirms
`read_only=true`. The matching `PEANO_LEAN_READONLY_DEPLOY_KEY` secret was
installed without printing its value, reusing an account/faculty key, granting
write access, or changing either repository's visibility.

The workflow retains the exact companion commit/toolchain pins and all eight
full proof-test shards. The normal Actions token is now `contents: read`, both
checkouts disable credential persistence, and companion SSH host verification
is strict. Only the presence check and companion checkout receive the new key;
missing secrets fail closed, including on fork pull requests. No privileged
fork workflow was introduced. All 35 focused CI environment/security tests
pass locally. An actual remote checkout/build remains to be observed after
this configuration is pushed.

Peano production promotion is deferred, not waived: the unchanged cache-header
gate still applies. Independent proof development and static proof-site
publication can continue. G072, G006, and G010 are being developed with shared
finite-factor/counting substrates, followed by G036 and G082. The first G072
audit identified the genuine initial `0/1` convergent for positive rationals
below one; the new recurrence definition will admit a zero numerator and
retain a positive denominator, without modifying sealed v28 evidence.
