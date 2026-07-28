# Module 09 — Peano Lab (branch: `peano-lab`)

**Goal:** a lightweight, readable, *sound* theorem prover for Peano arithmetic in the browser —
"a little Lean for PA" — built to teach how kernels, tactics, and tactic languages are made.
Full architecture (read it FIRST — it is binding): **`docs/PEANO_LAB_DESIGN.md`**.
Priorities: soundness → clarity → pedagogy → extensibility → efficiency. Python, clean code.

**House rules for the implementing model (Codex):**
- The kernel (`peano_lab/kernel/`) is the trusted base: small, dependency-free, no imports from
  engine/ui. `checker.py` target ≤ ~300 lines. Every QED must pass the independent checker
  against the ORIGINAL goal (`checked_final` pattern) — no exceptions, ever.
- A tactic that fails must raise `TacticError` (final English text) and leave the state
  unchanged. Transactional history. These are the 2026-07-24 audit's lessons; they are law here.
- Reuse, do not reinvent: clone the lambda-lab shell (worker, xterm, vendor, deep links),
  copy the metavariable discipline from `lab-lambda/py/lambda_lab/lab/webport/stlc_types.py`
  and the state/tactic/finalization patterns from `proof_builder.py`, the UI grammar rules from
  `prove.py`, and the session-owner routing from `driver.py`.
- Deterministic canonical pretty-printing everywhere; the JSONL trace logger (design §4) ships
  with the engine, not after it.
- Tests land in the same commit as the feature. Every milestone ends green.
- Keep a running diary in `book/peano/diary.md` — short dated notes on design decisions taken
  while implementing (this feeds the book chapter; write it as you go, not retroactively).

## Milestones

### M0 — Kernel: terms, formulas, substitution, checker
- [x] `kernel/terms.py` + `kernel/formulas.py`: AST (de Bruijn in kernel, named surface),
      canonical printer, parser for the surface syntax (`0, S, +, ·/*, =, ->, /\, \/, ~, forall,
      exists`, numerals as sugar; ASCII + Unicode aliases).
- [x] `kernel/subst.py`: shift/substitute for terms and formulas, capture-proof, with the
      counterexamples that break naive substitution as tests.
- [x] `kernel/proofs.py`: proof-term constructors — one per ND rule + PA axioms + IND schema +
      equality rules (design §1).
- [x] `kernel/checker.py`: `check(ctx, proof, formula) -> bool`, structural recursion, ≤ ~300
      lines, zero imports outside `kernel/`.
- [x] `tests/test_kernel.py`: round-trip parse/print, substitution/capture suite, hand-built
      certificates for tiny theorems (`0 = 0`, `S 0 + 0 = S 0` via PA3) checked GREEN, and
      hand-built *wrong* certificates checked RED.
- [x] Import-hygiene test: kernel imports nothing from engine/ui.
- **Acceptance:** a hand-written certificate for `∀x. x + 0 = x` (one IND instance) validates;
  mutated variants of it all fail.

### M1 — Engine core + equational tactics (Stage A)
- [x] `engine/state.py`: Goal, ProofState (goals, partial certificate with holes, history,
      original target, metavar substitution), invariants helper.
- [x] Term metavariables with rigid/flexible unification (port the `stlc_types` discipline);
      proof-wide substitution propagation.
- [x] Tactics: `refl`, `symm`, `trans <t>`, `congr`, `exact <hyp>`, `assumption`,
      `rewrite h`, `rewrite <- h`, `rewrite h at h'` (equation orientation, occurrence choice
      documented; rewriting under binders deferred to M3 and *rejected* until then).
- [x] `checked_final` through the kernel checker; failed check keeps the session.
- [x] Trace logger `engine/trace.py` (design §4) wired into tactic application.
- [x] `tests/test_soundness.py` (attack suite, grows every milestone) + `tests/test_tactics.py`.
- **Acceptance:** interactive `S 0 + S 0 = S (S 0)`-style proofs work end-to-end with QED
  checked by the kernel; the attack suite (prove `0 = S 0`, rewrite with a non-equation,
  smuggle an unknown hypothesis) fails entirely.

### M2 — Induction (Stage B)
- [x] `engine/induction.py`: `induction n` (n a context variable of the current ∀-goal or a
      fresh surface variable) → base + step subgoals with named IH; certificate uses the IND
      schema instance.
- [x] `intro x` for ∀-goals (needed to state induction targets), `specialize h t`.
- [x] First ladder theorems interactively provable: `0 + n = n` (the one that NEEDS induction —
      book moment: contrast with `n + 0 = n` being PA3), `add_succ_left`.
- **Acceptance:** `∀n. 0 + n = n` proved interactively in ≤ 8 tactics, QED kernel-checked;
  `induction` on a non-variable and induction-hypothesis misuse both fail cleanly.

### M3 — Full connectives and quantifiers (Stage C)
- [x] Propositional layer: `intro`, `apply`, `split`, `left`, `right`, `cases h`, `exfalso`
      (port the prove engine's shapes; certificates per design §1).
- [x] `exists <t>` (with `?` metavariable witness allowed, resolved by unification),
      `forall_elim`/`specialize`, α-safe rewriting under binders (now, with tests from M1's
      deferred cases).
- [x] `classical on|off` toggle adding ¬¬φ → φ; OFF by default; session banner shows the mode.
- [x] `hint` for the PA setting: assumption/refl/available-rewrite/induction suggestions —
      honest statuses as in prove (`found/none/limit`).
- **Acceptance:** `S n ≠ 0` (i.e. `S n = 0 → ⊥` via PA1), `le_refl` with `≤` as defined sugar,
  and an ∃-witness proof all pass; the soundness attack suite extended with capture attacks
  through binders stays fully red.

### M4 — Tacticals + automation (Stage D)
- [x] `engine/tacticals.py`: `;`(then), `<|>`(orelse), `repeat`, `first`, `all_goals`,
      `focus n` — combinators over the Tactic type, ~100 lines, heavily commented (book source).
- [x] `engine/rewrite.py` grows into `simp`: ordered rewriting with an explicit simp-set
      (PA3–PA6 + user-tagged lemmas), termination measure documented.
- [x] `engine/decide.py`: closed-term evaluation, closed-equation decision, bounded quantifier
      check with an honest label.
- [x] `engine/search.py`: `auto [depth]` — backtracking over primitives + simp; every run
      emits traces.
- **Acceptance:** `add_comm` provable as `induction n; simp` (or comparably short); `auto 5`
  closes at least the first four ladder theorems from cold; tactical laws tested
  (`repeat` terminates, `orelse` restores state on first-branch failure).

### M5 — The `/peano-lab/` page
- [x] Clone the shell: `peano-lab/index.html` + `worker.js` + `.htaccess` + own BUILD tag,
      shared vendor via `scripts/fetch_vendor.sh`; quick buttons for the PA world.
- [x] `peano-lab/py/driver.py`: `pa` command family (design §3), session-owner routing,
      complete-line aliases, in-proof `help` — the audit UI rules verbatim.
- [x] `pa prove` panels: goals/context/partial-certificate display in the prove style.
- [x] `make deploy-peano` + `deploy-peano-next` staging channel targets in the Makefile.
- **Acceptance:** the ladder through `add_comm` provable in the browser; existing lab-lambda
  tests still green (zero regressions in the shared repo).

### M6 — Content: KB, tactic encyclopedia, tutorials
- [x] `ui/data_tactics.py`: a card per tactic AND per tactical — syntax, what it does to the
      goal, what it does to the certificate, worked example, common errors.
- [x] `ui/data_kb.py`: PA axioms, induction-as-schema, de Bruijn & capture, LCF vs proof terms,
      De Bruijn criterion, simp termination, Gödel/limits card, Heyting vs classical PA.
- [x] Two tutorials min.: "prove add_comm by hand" (gated, ENTER-driven) and "build your own
      tactic" (walks through adding a toy `symm_all` tactical to the source).
- [x] Extend `scripts/verify_book_commands.py` to replay `pa` deep links + session blocks.
- **Acceptance:** book gate green over the new content; tutorials walk ENTER-only to completion.

### M7 — The theorem library + ladder regression
- [x] `library/theorems.py`: the full ladder (design §6) as named, scripted proofs replayed in
      CI (`tests/test_ladder.py`); `pa lib` browses them with statements + tactic scripts.
- [x] `pa lean <thm>`: export statement (+ proof stub) as Lean 4 `theorem` over `Nat` with a
      Live Lean link, for cross-checking.
- **Acceptance:** ladder complete through the `n·m = 0 → n = 0 ∨ m = 0` capstone, all
  kernel-checked in CI.
- **Verified:** 20 closed scripted entries (15 binding rungs + 5 named helpers) replay and check
  against their original statements; all 20 Lean stubs elaborate under Lean 4.28 with only the
  intentional `sorry` warning. Peano `433 passed`; Lambda `360 passed, 36 subtests passed`.

### M8 — Book part: "Building Peano Lab"
- [x] New book part (chapters under `book/peano/`): 1. why PA and the staged logic; 2. the
      kernel and the De Bruijn criterion (with the audit story as motivation); 3. anatomy of a
      tactic; 4. tacticals — the tactic language; 5. induction and the ladder; 6. limits
      (Gödel, what Lean has that we don't). Built from the `diary.md` kept since M0.
- [x] Landing page card flips from "in development" to live; announcement paragraph.
- **Acceptance:** book builds clean; every command in the chapters replays via the gate.
- **Verified:** warning-as-error Jupyter Book build succeeds for all 24 pages; the full gate checks
  190 deep links and 17 session blocks/78 commands, including 15 links and 45 commands in the six
  new chapters. Peano `436 passed`; Lambda `360 passed, 36 subtests passed`; vault 49 notes with
  zero unresolved wiki-links; trusted checker unchanged at 234 lines.

### M9 — LLM corpus (prep for post-training; design only executes after M7)
- [x] `scripts/export_traces.py`: collate JSONL sessions → deduplicated train/val split;
      stats report (theorems covered, tactic distribution, failure ratio).
- [x] Batch generation: `auto` sweeps over the ladder + randomized provable variants
      (commuted/renamed instances) to grow the corpus; document generation provenance.
- [x] A short `docs/PEANO_LLM.md`: target model size, tokenization notes (canonical printer =
      the tokenizer's friend), eval protocol (held-out ladder theorems, pass@k with the kernel
      as judge). **No training in this repo** — data + protocol only.
- **Acceptance:** ≥ 10k clean trace records exportable; eval harness runs against a dummy
  policy (random tactic) end-to-end with the kernel as judge.
- **Verified:** the all-ladder acceptance superset generated 13,417 transitions in 1,636 sessions
  (20 honest bounded-auto attempts, 20 checked authored replays, and 1,596 randomized variants),
  with 1,624 kernel-checked QEDs and 12 honest search failures; strict export retained 13,412
  unique rows. The committed leakage-separated release contains 13,152 unique v1 rows (12,540
  train / 612 validation), 1,596 labeled transactional failures, source/checker fingerprints, and
  no ladder sessions. The deterministic random policy completed 32 attempts over four pinned
  held-out families through the production grammar and kernel judge. Peano `498 passed`; focused
  M9 `62 passed`; Lambda `360 passed, 36 subtests passed`; the warning-as-error book build and all
  190 links/17 blocks/78 commands are green; vault 52 notes/228 links/0 unresolved; checker 234
  lines.

### M10 — Live checked-theorem reuse
- [x] Add `use <library-theorem> [as <alias>]` as a surface-level atomic tactic; library lookup
      stays outside the engine and kernel.
- [x] Recheck every supplied closed theorem certificate before publishing a local-cut state;
      collisions, malformed syntax, unknown names, and bad certificates fail transactionally.
- [x] Compile exposed implication/forall cuts in a transient final state, then run the existing
      independent checker against the owner-held original target and exact classical mode.
- [x] Route browser sessions and the M9 policy evaluator through the same surface finalization;
      support tacticals, tracing, exact undo, aliases, specialization, rewriting, and `simp`.
- [x] Add executable tactic-card, book, vault, README, diary, journal, and memory documentation.
- **Acceptance:** two imported library facts compose into a new theorem in a live session; raw
  introduction-form cuts require compilation, the compiled certificate checks from the empty
  context, forged imports and false original goals remain rejected, and both full regression suites
  stay green without any kernel change.
- **Verified:** `add_succ_left` and `add_comm` compose interactively into
  `forall a b. S a + b = S (b + a)` and reach checked QED. Tests pin raw-cut rejection, compiled
  empty-context checking, forged/false-goal rejection, Unicode aliases, exact rollback/undo, and
  typed node/depth exhaustion. Peano `520 passed`; Lambda `360 passed, 36 subtests passed`; the
  warning-as-error 24-page book and all 190 links/18 blocks/85 commands are green; vault 53
  notes/238 links/0 unresolved; the deterministic release remains 13,152 rows from 1,596 checked
  sessions; trusted checker unchanged at 234 lines.

### M11 — Checked commutative-semiring basis
- [x] Audit the current ladder against the exact lemma basis needed by proof-producing polynomial
      normalization; add only missing identity/distributivity/numeral lemmas as ordinary entries.
- [x] Keep dependencies acyclic, scripts readable, generated Lean stubs valid, and every final
      certificate checked from the empty context.
- **Acceptance:** the complete semiring basis replays deterministically and its certificates can be
  instantiated below proposition and term binders without capture.
- **Verified:** the only missing orientations are `one_mul` (26 nodes/depth 9), `mul_one` (31/14),
  and `add_mul` (748/45); all replay twice identically, check from the empty context, elaborate as
  exact Lean 4.28 stubs, and import/specialize below nested `forall`/implication binders before
  checked QED. Focused M11 `84 passed`; Peano `527 passed`; Lambda `360 passed, 36 subtests passed`;
  warning-as-error book and 190 links/18 blocks/85 commands green; vault 54 notes/247 links/0
  unresolved; regenerated corpus 13,152 rows/1,596 checked sessions with all 23 rungs recorded;
  checker unchanged at 234 lines.

### M12 — Certificate-producing `ring`
- [x] Reify `0`, numerals, variables, `+`, and `·` into a deterministic sparse polynomial form.
- [x] Normalize both equality sides with a fixed monomial order while constructing a proof from the
      M11 certificates; add explicit AST/coefficient/proof-size/browser-time limits.
- [x] Keep `ring` argument-free and identity-only: conditional algebra uses an explicit
      `trans`/`rewrite` workflow, and computation alone is never treated as a certificate.
- **Acceptance:** the odd-square induction theorem closes interactively with witness `x + S n`,
  middle term `((2*n+1)*(2*n+1)) + 8*S n`, and an explicit forward rewrite by `IH_witness`; QED
  checks the resulting certificate against the original goal. Mutated coefficients, constants,
  witnesses, and middle terms fail transactionally, as do non-equality goals, unresolved
  metavariables, unsupported conditional uses, and every explicit resource limit.
- **Verified:** the exact 11-command odd-square session reaches independently checked QED; its two
  large step certificates are 36,004 nodes/depth 61 and 13,156/depth 55. Tests pin coefficient
  `7`, constant `+2`, witness `x+n`, a bad middle term, post-intro hypothesis misuse, proof
  mutation, malformed/forged laws, exact undo/traces, and every structural/work/proof/time limit.
  Peano `581 passed`; Lambda `360 passed, 36 subtests passed`; the warning-as-error 24-page book and
  all 190 links/19 blocks/96 commands are green; vault 55 notes/258 links/0 unresolved; regenerated
  corpus 13,152 rows/1,596 checked sessions; local staging assembly green; checker unchanged at 234
  lines. Direct Pyodide timing remains a deployment check because no in-app browser was available.

### M13 — Basic arithmetic teaching surface
- [x] Add bounded, certificate-producing `norm_num` for closed numerical subterms and equations.
- [x] Add arithmetic-aware hints, tactic cards, tutorial, book chapter, vault concepts, deterministic
      traces, and corpus/evaluator coverage.
- [x] Document the boundary: polynomial identities and bounded numerals are supported; general PA
      and nonlinear hypothesis solving are not decided. A Presburger `omega` belongs to a later plan.
- **Acceptance:** browser examples remain responsive under explicit limits; all documentation
  commands replay; corpus provenance is regenerated; Peano, Lambda, book, vault, and staging gates
  are green.
- **Verified:** closed equations and maximal closed numerical islands under open terms or at most 64
  leading universals produce checked PA3--PA6/congruence certificates; false equations, malformed
  states, unresolved metas, no-progress requests, forged proof leaves, and all structural/work/time/
  live-proof limits fail transactionally. Pure `hint` mirrors the tactic's exact projected commit
  without allocating a hole. Peano `641 passed`; Lambda `360 passed, 36 subtests passed`; the
  warning-as-error 25-page book and all 193 links/23 blocks/125 commands are green; vault 56
  notes/271 links/0 unresolved; the generator-v2 release reproducibly contains 13,344 unique v1
  transitions from 1,692 checked sessions (13,326 train / 18 pipeline-validation); the all-ladder
  smoke exported 13,631 unique rows; evaluator v2 ran 32 kernel-judged attempts; local staging and
  vendor hashes are green; checker unchanged at 234 lines. Browser-shell tests and staged assets pin
  the worker/Stop path and explicit limits. No in-app browser instance was available for a direct
  Pyodide interaction, so that limitation is recorded rather than reported as a measured run. Both
  staging and production build `2026-07-27h` subsequently returned HTTP 200 with page, worker,
  `norm_num`, and Pyodide hashes matching local staging; the landing page and arithmetic book
  chapter were likewise published and byte-verified.

### M14 — Browser cold-start delivery

- [x] Put the pinned vendor tree below a manifest-derived URL namespace and give only genuinely
      versioned application/vendor responses a one-year immutable cache policy.
- [x] Keep `index.html` non-storable, require unversioned responses to revalidate, and negotiate
      Brotli or gzip for WASM/source media types without recompressing ZIP or WOFF2.
- [x] Start all Python source requests concurrently while Pyodide initializes, then select failures
      and mount files deterministically in the worker's declared `PY_FILES` order.
- [x] Add behavioral worker tests, static Apache/cache contracts, CI coverage, deployment recipes,
      book/vault explanation, and a new build identifier.
- **Acceptance:** staging serves build `2026-07-27i`; HTML is `no-store`; versioned worker, Python,
  and vendor URLs are immutable; WASM is delivered with Brotli or gzip and decodes to the pinned
  local hash, with an encoded transfer below 3.0 MB rather than the 8.6 MB identity baseline;
  concurrent/reverse-completion and multiple-failure tests preserve deterministic
  mounting and atomic failure; cold and warm starts reach ready; checked QED and Stop/restart still
  work; all Peano, Lambda, book, vault, vendor, and staging gates are green before production.
- **Staging gate (2026-07-27):** candidate `a099596` serves build `2026-07-27i` and gzip works, but
  promotion is stopped: guarded account-level directives emitted no cache headers, while an
  unguarded `Header` probe returned HTTP 500. That establishes that this account cannot supply the
  required policy from static `.htaccess`; it does not establish which modules are loaded in the
  central Apache/proxy tier. Experimental PHP probes were removed and production remains on M13
  pending administrator-managed cache headers or a documented design exception for a narrow PHP
  relay.

### M15 — Replayable proof artifacts

- [x] Add a proof-owner replay journal that follows the surviving undo branch without changing
      `ProofState`, the v1 trace, tactic transactions, or kernel authority.
- [x] Add `script` for active and last-checked previews. Active scripts remain explicitly
      unchecked and omit `qed`; only a successful independent-kernel QED retains a checked script.
- [x] Add `script download` with exact LF/UTF-8 replay bytes, one-shot worker routing, a fixed safe
      filename, payload validation, direct-terminal intent, and object-URL cleanup.
- [x] Document the replay/library boundary in the binding design, README, Jupyter Book, vault,
      memory, journal, and diary; update the browser application release identity.
- [x] Run the focused contracts, complete Peano and Lambda suites, warning-as-error book build,
      executable book/deep-link gate, vault-link audit, manifest/staging checks, then publish the
      milestone commit to `peano-lab`.
- **Acceptance:** failed tactics, inspection, failed QED, and `undo` itself never enter the replay;
  undo removes its exact surviving transaction; tactical syntax, theorem imports, classical
  authority, and top-level `auto` primitives replay deterministically; a goals-closed active proof
  is never labeled checked; downloaded bytes reproduce a kernel-accepted QED; malformed or
  unsolicited payloads cannot download; the static browser cannot mutate the theorem library; the
  trusted kernel is byte-unchanged and every project gate is green. M14 production promotion
  remains independently blocked until WMI enables the requested cache headers.
- **Verified locally (2026-07-27):** focused replay/corpus/browser/book contracts report 32 passed;
  Peano reports 657 passed; Lambda reports 360 passed plus 36 subtests; the source-bound release
  reproduces 13,344 transitions from 1,692 checked sessions and the acceptance superset exports
  13,631 unique rows; evaluator v2 completes 32 kernel-judged baseline attempts; the warning-free
  25-source book and all 193 deep links/32 blocks/160 commands are green; all 298 vault links across
  58 notes resolve with no disconnected concept; application/vendor manifests and local staging
  are exact at `a-f2054080fdc5`/`v-85fb3352e49c`; the kernel has no diff and `checker.py` remains
  234 lines. No in-app browser was attached, so direct clicking is not claimed; the dependency-free
  worker/download harnesses cover those protocol and DOM lifecycle contracts.
- **Published to staging (2026-07-27):** commit `f40b2ad` is pushed to `peano-lab`; staging serves
  build `2026-07-27j` from `releases/a-f2054080fdc5/`. The live page, application manifest,
  worker, and proof UI are byte-identical to local staging, and WASM negotiates gzip. The full M14
  delivery gate still stops at the known host boundary because HTML has no `Cache-Control: no-store`
  and versioned assets have no immutable policy. Production remains untouched on build
  `2026-07-27h`; M15 functionality is therefore available on staging but is not promoted.

### M16 — Named local reasoning with `have` and `suffices`

- [x] Add exact surface forms `have h : P` and `suffices h : P`, parsing `P` only in the focused
      goal's existing rigid term-variable scope and requiring a fresh hypothesis name.
- [x] Preserve the positional goal/hole law with engine-only `LocalHave` and `LocalSuffices`
      schedulers: `have` exposes the proof of `P` first, while `suffices` exposes the old target
      under `h : P` first.
- [x] Compile both schedulers away by capture-avoiding proof-hypothesis substitution before the
      unchanged kernel runs; do not add a kernel cut, annotation, theorem-name, or local-lemma rule.
- [x] Keep failures transactional, one successful command equal to one undo step and one trace
      transition, and preserve exact behavior under `focus`, `all_goals`, `;`, and `<|>`.
- [x] Add executable tactic cards, browser completion/help, replay coverage, construction-book and
      vault explanations, and deterministic release artifacts without changing the v1 trace schema.

**Acceptance checklist:**

- [x] `have h : P` produces, in order, `Γ ⊢ P` and `h : P, Γ ⊢ B`; `suffices h : P` produces,
      in order, `h : P, Γ ⊢ B` and `Γ ⊢ P`, with left-to-right holes in the same order.
- [x] Completed examples for both commands compile to ordinary proof terms and pass the independent
      checker from the empty context against the session owner's original target.
- [x] Malformed syntax, malformed propositions, undeclared free variables, reused names, compiler
      failure, and nearby false or mutated certificates all fail without changing the input state.
- [x] Capture regressions pass below nested proposition, universal, and existential binders; exact
      undo, focus, tactical rollback, JSONL trace, replay export, and resource-failure behavior are
      pinned.
- [x] The trusted kernel has no diff and retains its engine/UI import boundary; Peano and Lambda
      suites, warning-as-error Jupyter Book build, executable prose/deep-link gate, vault audit,
      manifest, and local staging gates are green.
- [x] Publication, if authorized, uses a new immutable application release and human-facing build;
      production remains untouched until all preceding checks and the independent M14 host-cache
      requirement pass.

- **Verified locally (2026-07-28):** focused local-reasoning coverage reports 29 passed, including
  scheduling, capture, tactical, replay, compiler-failure, and kernel-boundary attacks; the readable
  parity artifact replays to a checked QED and fails a mutated target. Peano reports 691 passed;
  Lambda reports 360 passed plus 36 subtests. The deterministic corpus remains 13,344 transitions
  from 1,692 checked sessions with refreshed source provenance. The warning-as-error 25-source book
  builds; 193 deep links and 170 commands in 34 session blocks replay; all 318 vault links across
  59 notes resolve with no disconnected concept. Application/vendor manifests and local staging
  are exact at `a-f6c33c7840ad`/`v-85fb3352e49c`; the kernel has no diff and `checker.py` remains
  234 lines. No in-app browser was attached, so a visual click-through is not claimed; the browser
  shell/session harnesses and exact staged-byte assembly are green. Production and staging were not
  deployed, preserving the independent M14 cache-header stop.

### M17 — Browser multiline proof paste

- [x] Add an explicit, keyboard-operable **Paste multiline proof** dialog with proper dialog
      semantics, a programmatically named multiline input, deliberate Run/Cancel actions, and
      predictable focus entry and restoration.
- [x] Recognize a direct multiline paste into the terminal and route it through the same bounded
      replay path; preserve all existing behavior for ordinary one-line input.
- [x] Accept only a complete replay whose first nonblank line begins exactly `pa prove ` and whose
      last nonblank line is exactly `qed`; ignore blank lines without turning them into commands.
- [x] Reject a batch before execution when it exceeds 100,000 characters, 256 nonblank lines, or
      the existing `MAX_INPUT` limit on any individual line.
- [x] Execute accepted lines sequentially through the existing single-session-owner driver, stop
      at the first failed line, preserve the successful prefix, and retain one ordinary undo step
      per successful proof command.
- [x] Suppress browser-download side effects during batch replay: preflight rejects pasted
      `script` commands, and the batch executor has no file-download authority even if a worker
      response contains a download payload.
- [x] Document that multiline input is an untrusted convenience for replay, not a certificate,
      transaction wrapper, library-admission path, or new kernel rule.

**Acceptance checklist:**

- [x] Dialog submission and direct terminal paste replay the same complete script, including CRLF
      input and ignored blank lines, and reach the same independently checked QED as manual entry.
- [x] Missing/incorrect `pa prove ` opening, a non-`qed` final nonblank line, excessive total
      characters, excessive nonblank lines, and an overlong individual line are rejected before
      the first command changes browser or proof-session state.
- [x] A tactic, parser, session-routing, or QED failure stops later lines; the successful prefix
      remains visible and usable, and repeated `undo` restores it one successful command at a time.
- [x] A batch containing `script download` triggers no browser download, including when it arrives
      through the dialog, terminal paste, synthetic input event, or replay immediately after QED.
- [x] Accessibility checks cover dialog naming, textarea labeling, keyboard operation, initial
      focus, cancellation, and focus restoration; terminal-only users retain direct paste.
- [x] QED still reaches the unchanged independent checker against the owner-retained original goal;
      browser, worker-protocol, resource-boundary, replay, Peano, Lambda, book, vault, manifest, and
      exact local-staging gates are green before any publication claim.

- **Verified locally (2026-07-28):** the focused browser/driver/readable-replay gate reports 23
  passed, including synthetic paste events, CRLF and blank-line normalization, all resource bounds,
  unsafe controls, strict scheduling, worker failure propagation, interruption races, download
  isolation, owner routing, repeated undo, and an independently checked readable parity QED. Peano
  reports 698 passed; Lambda reports 360 passed plus 36 subtests. The warning-as-error 25-source
  book builds; 193 deep links and 170 commands in 34 session blocks replay; all 335 vault links
  across 60 notes resolve with no disconnected concept. The unchanged corpus remains 13,344
  transitions from 1,692 checked sessions. Application/vendor manifests and exact local staging
  are green at `a-404fdbdb55e4`/`v-85fb3352e49c`, build `2026-07-28b`; the kernel has no diff and
  `checker.py` remains 234 lines. No in-app browser was attached, so a visual click-through is not
  claimed; the event/worker harnesses test the interaction contract. After owner authorization,
  exact M17 HTML/manifest/worker/driver bytes were deployed to `/peano-lab-next/`. The remote
  delivery gate stopped production promotion because the LOL-ng host still omits `Cache-Control`
  from HTML and immutable assets. Production therefore remains build `2026-07-27h`.

### M18 — Small PA recurrence certificates with `compact_arith`

- [x] Add the exact equality-tactic forms `compact_arith` and
      `compact_arith [h, <- k]`. Parse an ordered explicit list of named equality hypotheses and
      orientations; never mine an unlisted hypothesis.
- [x] Restrict version 1 to focused rigid equality goals with no unresolved term metavariables.
      Do not introduce binders, choose induction variables or invariants, invent existential
      witnesses, solve logical connectives, or present the tactic as a PA decision procedure.
- [x] Build only ordinary kernel certificates from PA3--PA6, equality rules, and independently
      checked/capture-safely specialized induction templates. Add no kernel constructor, theorem
      environment, arithmetic oracle, or trusted cost claim.
- [x] Search a fixed deterministic set of PA-oriented recurrence paths, carrying exact equality
      endpoints with every candidate and comparing expanded cut-normal proof-tree costs rather than
      high-level template-call counts.
- [x] Check the selected certificate against the focused context and exact target before publishing
      one immutable tactic transaction. Keep the final QED check against the owner-held original
      theorem unchanged.
- [x] Expose `compact_arith?` as a pure inspection command: no goal, history,
      hole, metavariable-allocation, replay-journal, trace, or authority change, and no reuse of an
      unchecked preview result by the real tactic.
- [x] Pin the version-1 defaults: 256 aggregate input-term nodes/depth 64, 16 selected equalities,
      64 seed/template instances, 512 memo/search states, 512 generated candidates, 100,000
      annotation nodes/depth 256, 20,000 work units, 10,000 generated proof nodes/depth 256,
      100,000 complete partial-proof nodes/depth 256, and five seconds. Every malformed request,
      unsupported shape, exhausted search, host recursion failure, and kernel rejection must be a
      final-English transactional failure.
- [x] Add the substantial Jupyter Book chapter, binding design, README, diary, memory/journal/plan,
      and connected Obsidian explanation of the 30,030-node readable elaboration, the 180-node
      checked record, the tree cost model, and the limits of every minimality claim.

**Acceptance checklist:**

- [x] The readable consecutive-product proof states the stronger invariant, induction variable,
      base and successor witnesses, explicit induction-hypothesis use, and final normalization
      bridge itself; `compact_arith` closes only its rigid arithmetic equality subgoals.
- [x] The complete replay reaches ordinary checked QED for
      `forall n. exists x. n * (n + 1) = 2 * x`, and its finalized expanded certificate meets the
      180-node/depth-34 bound with canonical bytes identical to the retained hand-authored artifact.
      The result is described as a checked upper bound, not an absolute minimum.
- [x] Empty-list and explicitly oriented hypothesis cases are deterministic; order and direction
      are pinned, omitted hypotheses are not consulted, and unknown/non-equality/duplicate or
      malformed entries fail without changing the input state.
- [x] Every recurrence template checks from the empty context; specialization is capture-safe below
      extra universal, existential, and implication binders; the selected focused certificate checks
      in its exact context; nearby mutated goals and mutated certificates fail.
- [x] Preview purity, exact undo, one trace transition for real success/failure, replay export,
      tactical/focus behavior, state invariants, and all resource-failure paths are tested.
- [x] The trusted kernel has no semantic diff and keeps its engine/UI import boundary and checker
      size. Peano, Lambda, warning-as-error book, executable prose, vault, corpus/provenance,
      manifest, and exact local-staging gates are green before publication.

- **Verified locally (2026-07-28):** focused M18 coverage reports 46 passed; the complete Peano suite
  reports 744 passed, and Lambda reports 360 passed plus 36 subtests. The readable thirteen-tactic
  replay reaches checked QED at exactly 180 nodes/depth 34 with canonical bytes identical to the
  retained certificate and rejection of nearby mutations. The warning-as-error 26-source book and
  all 193 deep links/170 commands in 34 session blocks are green; the vault has 61 notes/356 links,
  no unresolved edge, and no disconnected concept. The CPython-3.10 corpus reproducibly retains
  13,344 unique transitions from 1,692 checked sessions with a 31-file semantic-source fingerprint.
  Application/vendor manifests and exact local staging are green at `a-953fa3777cd4`/
  `v-85fb3352e49c`, build `2026-07-28c`; the kernel has no diff and `checker.py` remains 234 lines.
  Worker and multiline-paste behavioral harnesses pass. On owner authorization, commit `98ee0dd`
  was deployed to staging as the identical build `2026-07-28c`/application `a-953fa3777cd4`:
  the public HTML hash and all 41 application checksums match the staged tree. No in-app browser was
  attached, so a real Pyodide click-through is not claimed. The delivery verifier still stops at
  the administrator-managed M14 cache-header blocker; production remains `2026-07-27h`.

### M19 — Compact headless prover and kernel-guided policy training

- [x] Add a browser-free adapter over the production formula parser, `ProofSession`, public tactic
      grammar, theorem library, trace logger, checked surface finalizer, and unchanged independent
      kernel. It must define no second proof language or trusted shortcut.
- [x] Add a warm finite-transaction JSONL CLI with runner-owned capabilities, strict per-request
      and aggregate bounds, deterministic
      session identities, a 16 MB per-proof trace ceiling, separate raw/result streams, durable
      trace staging, and suppression of successful result rows unless the trace publishes.
- [x] Compile positive next-tactic rows only from complete `qed:true` sessions that replay under
      their exact declared logic/capability preimage to another kernel-checked QED. Preserve exact
      authored binder actions, use input focus 0 rather than action-derived trace focus, and split
      connected family/lineage/canonical-formula/exact-policy-prompt components before row
      expansion.
- [x] Freeze one common `model-v1` command/theorem authority for generation and held-out evaluation.
      Exclude `auto`, `undo`, session commands, and held-out target theorems; bind the full preimage
      by SHA-256 in every row and report.
- [x] Add a small deterministic pilot generator covering logic, equality, quantifiers, induction,
      addition, multiplication, witnesses, local reasoning, checked theorem reuse, `norm_num`,
      `ring`, and `compact_arith`; bind IDs to the complete Peano Python source tree and runtime.
- [x] Add BF16 LoRA training/inference code for pinned Qwen3 1.7B and controlled 4B/Pythagoras
      comparisons. Mask prompt tokens, supervise one tactic plus EOS, stream and hash-validate
      capped dataset samples, and bind resume checkpoints to a pre-run identity and exact hash.
- [x] Add evaluator-side authority preflight and cryptographic policy/decode provenance. Only the
      ordinary public surface followed by original-target kernel finalization can score a proof.
- [x] Expose a trained adapter on arbitrary bounded closed PA formulas without widening its
      attested authority. Publish pasteable `.pa` only after a second exact-capability kernel
      replay; provide an immutable request-file, ledgered typed-A100 WMI job for actual use.
- [x] Add guarded Helios sync, environment, training, evaluation, queue, and submission controls;
      test-only is the default and real submission requires the explicit confirmation token.
- [x] Pass the corrected isolated Helios environment and one-step BF16 LoRA save/reload smoke on
      job `20029964`, with exact source/model/runtime/artifact provenance.
- [x] Pass the tracked WMI A100 runtime probe and build a separate reviewed central-base manifest,
      pinned x86-64 overlay, and transactional deployment path. Probe `171369` passed on one
      A100-SXM4-80GB; the 96-test local WMI/runtime/training gate is green.
- [ ] Repeat the complete LoRA save/reload gate on WMI before submitting WMI training.
- [x] Expand the checked synthetic curriculum beyond the 18-session pilot, keeping genealogy and
      capability metadata complete, and freeze the first training/validation/test release.
- [ ] Run the registered Qwen3-1.7B 100-step pilot on an accepted site, publish the complete
      training and held-out evaluator manifests, and compare against pretrained/random/deterministic
      baselines. Helios supports checked resume; WMI's first pilot is explicitly one-shot.
- [ ] If the smoke gates pass, run the pre-registered Qwen3-4B versus Pythagoras-Prover-4B
      comparison at identical data, LoRA, decode, token, step, and kernel-call budgets.
- [ ] Finish the full Peano/Lambda/book/vault/release gates, record measured results without
      extrapolation, commit and push M19 on `peano-lab`; do not merge or promote production.

**Acceptance checklist:**

- [x] Traced and quiet execution agree on status, independent kernel acceptance, proof nodes, and
      engine steps across the pilot; quiet mode is explicitly ineligible as training data.
- [x] Adversarial tests cover forged owners, capability smuggling through tacticals, trace mutation,
      broken/short sinks, invalid UTF-8/JSON, oversized numerals, host recursion, live proof depth,
      trace bytes, session collisions, action-focus leakage, unreachable binder trajectories,
      mismatched policy authority, training-environment laundering, exact-formula and exact-prompt
      split leakage, held-out data contamination, incomplete loader artifact hashes, forged
      replay/history labels, mismatched failure diagnostics, unbounded JSON integers/floats and
      batch totals, interrupted transports, post-commit cleanup failures, partial multi-file
      publication, stale one-shot output, PEFT pickle fallback, Python optimization bypass, and
      command-substitution failure swallowing, unsafe/open arbitrary theorem input, composed model
      call/token budgets, forged proof publication, adapter/source mutation, nested/aliased output
      paths, closed-artifact corruption, and request/job ledger mismatch.
- [x] The pilot currently yields 18 independently checked sessions and 58 positive transitions in
      11 families; replay compilation produces genealogy-separated train/validation/test files.
- [x] The first scaled release yields 2,522 kernel-checked roots and exactly 10,000 positive rows
      across 29 proof-first schemas/five domains. It splits 8,149/926/925, independently rebuilds
      byte-identical outputs from raw traces, and reports zero frozen-target contamination.
- [ ] The model smoke reaches a reproducible terminal report on the frozen held-out set; a report
      without model/data/source/decode/environment/checkpoint hashes is not an accepted result.
- [ ] All milestone-wide tests and documentation gates are green, the kernel has no semantic diff,
      and no heavy local or remote job remains running before the milestone is called complete.

- **Current verification (2026-07-28, in progress):** the current focused trained-policy,
  arbitrary-proof, WMI request/control, and runtime set reports 140 passes; the complete Peano
  suite reports 1,030 passes, Lambda Lab reports 360 tests plus 36 subtests, the book builds, all 193 documented
  links and 34 command sessions replay, and local application staging is green as
  `2026-07-28f` / `a-69aa3b753965`. A lightweight arm64 audit measured approximately
  12,538 quiet and 5,537 traced trivial proofs/second before the latest trace-copy optimization;
  all 18 pilot scripts had traced/quiet parity. The fixed scaled dataset digest is
  `1fa98caa2e0528d39c1b9003c4ee153dfbe633cb1ee4505e8f5b28eb837465dd`.
  The historical 13,344-transition release was provenance-refreshed under the same current source;
  all 1,692 sessions again reached kernel-checked QED. A policy training artifact now exists, but
  no kernel-judged theorem-solving result exists yet.
  Slurm preparation job `20029189` was submitted but failed safely before model loading because the
  first environment recipe incorrectly assumed the ML module made Torch importable. Its dependent
  train/evaluation jobs were canceled without running. The corrected recipe pins Helios's
  `torch==2.9.1+cu129` ARM wheel, isolates the venv, enumerates transitive dependencies, and runs
  `pip check`. Replacement preparation job `20029964` completed in 1m31s: exact commit/model
  revisions matched, GH200 BF16 was active, train/reload losses were finite, and closed adapter and
  tokenizer hashes were emitted. Training job `20029970` completed 100 steps in 9m51s with train
  loss 0.78446 and final teacher-forced validation loss 0.13518. Evaluator `20029980` failed in
  three seconds before generation because canonical `sort_keys=True` JSON reordered the nested
  capability keys while a row-oriented parser required construction order; no learned-policy
  solve rate is claimed. Typed-A100 WMI probe `171369` passed in 13 seconds. Its distinct
  x86-64 base/overlay, deployment, serialization, and one-shot guards now pass 96 focused local
  tests. The arbitrary-theorem path adds immutable request transport, a request/job ledger, a
  typed-A100 proof job, exact adapter/source rechecks, and second kernel replay before `.pa`
  publication. After diagnostic `171391`, WMI preparation `171395` passed in 8m39s with dataset
  digest `1fa98caa…`, exact A100/Python/Torch provenance, and finite LoRA losses before and after
  safetensors reload. The first dependent training submission failed closed before `sbatch`:
  Bash's whitespace `IFS` collapsed the predecessor row's deliberately empty dependency column.
  A strict bounded UTF-8 nine-field parser now owns that boundary. Because source identity changed,
  a fresh preparation job must precede training; no chain is silently relabeled. Preparation
  `171404` was canceled after 1m56s when the manifest-loader defect was discovered. The fixed
  loader reconstructs the exact three semantic fields from sorted manifest JSON, then retains the
  same capability-value, environment-hash, fixed-authority, and strict dataset-row checks.

### M20 — General foundational arithmetic library

The theorem-ladder extension is tracked independently in
[`PLAN/10_arithmetic_library.md`](10_arithmetic_library.md). Its first release
keeps the kernel and object language fixed, expands divisibility and residue
notions into ordinary formulas, and labels prime/factorization targets by
their real dependencies. A future finite-sequence or multiset milestone is a
prerequisite for exposing the full Fundamental Theorem of Arithmetic.

## Explicitly out of scope
Dependent types, definitional reduction, elaboration, typeclasses, and speculative proof-search
performance work beyond the explicit tactic limits remain outside this plan. M14 is the
owner-authorized static-delivery exception: it changes how identical browser bytes arrive, not the
kernel, engine semantics, or proof language. See design §8.

## Working agreement
Work happens on this branch (`peano-lab`); merge to `main` at milestone boundaries only, with
the full existing suite green. Deploy `/peano-lab-next/` only from a green current milestone;
promote to `/peano-lab/` only with the same gates and the milestone owner's authority. Journal
entries belong in `JOURNAL.md` at each milestone; merging to `main` remains the owner's decision.
