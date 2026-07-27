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
