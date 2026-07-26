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
- [ ] Clone the shell: `peano-lab/index.html` + `worker.js` + `.htaccess` + own BUILD tag,
      shared vendor via `scripts/fetch_vendor.sh`; quick buttons for the PA world.
- [ ] `peano-lab/py/driver.py`: `pa` command family (design §3), session-owner routing,
      complete-line aliases, in-proof `help` — the audit UI rules verbatim.
- [ ] `pa prove` panels: goals/context/partial-certificate display in the prove style.
- [ ] `make deploy-peano` + `deploy-peano-next` staging channel targets in the Makefile.
- **Acceptance:** the ladder through `add_comm` provable in the browser; existing lab-lambda
  tests still green (zero regressions in the shared repo).

### M6 — Content: KB, tactic encyclopedia, tutorials
- [ ] `ui/data_tactics.py`: a card per tactic AND per tactical — syntax, what it does to the
      goal, what it does to the certificate, worked example, common errors.
- [ ] `ui/data_kb.py`: PA axioms, induction-as-schema, de Bruijn & capture, LCF vs proof terms,
      De Bruijn criterion, simp termination, Gödel/limits card, Heyting vs classical PA.
- [ ] Two tutorials min.: "prove add_comm by hand" (gated, ENTER-driven) and "build your own
      tactic" (walks through adding a toy `symm_all` tactical to the source).
- [ ] Extend `scripts/verify_book_commands.py` to replay `pa` deep links + session blocks.
- **Acceptance:** book gate green over the new content; tutorials walk ENTER-only to completion.

### M7 — The theorem library + ladder regression
- [ ] `library/theorems.py`: the full ladder (design §6) as named, scripted proofs replayed in
      CI (`tests/test_ladder.py`); `pa lib` browses them with statements + tactic scripts.
- [ ] `pa lean <thm>`: export statement (+ proof stub) as Lean 4 `theorem` over `Nat` with a
      Live Lean link, for cross-checking.
- **Acceptance:** ladder complete through the `n·m = 0 → n = 0 ∨ m = 0` capstone, all
  kernel-checked in CI.

### M8 — Book part: "Building Peano Lab"
- [ ] New book part (chapters under `book/peano/`): 1. why PA and the staged logic; 2. the
      kernel and the De Bruijn criterion (with the audit story as motivation); 3. anatomy of a
      tactic; 4. tacticals — the tactic language; 5. induction and the ladder; 6. limits
      (Gödel, what Lean has that we don't). Built from the `diary.md` kept since M0.
- [ ] Landing page card flips from "in development" to live; announcement paragraph.
- **Acceptance:** book builds clean; every command in the chapters replays via the gate.

### M9 — LLM corpus (prep for post-training; design only executes after M7)
- [ ] `scripts/export_traces.py`: collate JSONL sessions → deduplicated train/val split;
      stats report (theorems covered, tactic distribution, failure ratio).
- [ ] Batch generation: `auto` sweeps over the ladder + randomized provable variants
      (commuted/renamed instances) to grow the corpus; document generation provenance.
- [ ] A short `docs/PEANO_LLM.md`: target model size, tokenization notes (canonical printer =
      the tokenizer's friend), eval protocol (held-out ladder theorems, pass@k with the kernel
      as judge). **No training in this repo** — data + protocol only.
- **Acceptance:** ≥ 10k clean trace records exportable; eval harness runs against a dummy
  policy (random tactic) end-to-end with the kernel as judge.

## Explicitly out of scope
Dependent types, definitional reduction, elaboration, typeclasses, performance tuning beyond
"the browser doesn't freeze". See design §8.

## Working agreement
Work happens on this branch (`peano-lab`); merge to `main` at milestone boundaries only, with
the full existing suite green. Deploy `/peano-lab-next/` (staging) freely from M5 on; promote
to `/peano-lab/` only after M6. Journal entries in `JOURNAL.md` at each milestone.
