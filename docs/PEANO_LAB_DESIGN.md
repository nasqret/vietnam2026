# Peano Lab — design document

**Mission:** build a lightweight, *readable* theorem prover for Peano arithmetic in the browser —
a "little Lean for PA" — where the point is to **learn how such systems are built**: the kernel,
the tactic engine, the tactic *language*, and eventually the data pipeline for an LLM prover.
Priorities, in order: **soundness → clarity → pedagogy → extensibility → (only then) efficiency.**
Python throughout; clean code over clever code.

This document is the architecture the implementation must follow. The task breakdown with
milestones and acceptance criteria lives in `PLAN/09_peano_lab.md`.

---

## 0. Plan review — decisions taken (and why)

The original idea: "build tactics for something harder than propositional logic, test on Peano
arithmetic, expandable, teach how tactics are made, lambda-lab-style UI, book chapter, later
post-train a small LLM on the solver's traces." All adopted. Four sharpening decisions:

**D1 — The logic is staged, not swallowed whole.** Full first-order PA at once would force
quantifiers, equality, substitution, *and* induction into milestone 1 — exactly how projects
drown. Instead the logic grows in fragments, each unlocking a new *kind* of tactic:

| Stage | Fragment | New tactic kind it forces |
|---|---|---|
| A | Quantifier-free equations over 0, S, +, · | `refl`/`symm`/`trans`/`cong`, `rewrite` |
| B | + structural induction (schema over open formulas) | `induction n` — the star of the show |
| C | + ∀/∃, →, ∧, ∨, ⊥, ¬ (:= → ⊥) | `intro`/`apply` (from prove), `exists_intro`, `forall_elim` |
| D | + automation | tacticals, `simp`-lite, `decide` for closed formulas, `auto` |

**D2 — Proof terms + an independent checker, not LCF theorem values.** There are two classic
architectures: LCF-style (a `Theorem` abstract type only the kernel can construct — Isabelle/HOL)
and proof-*term* style (tactics build a certificate; a small checker validates it — Lean/Coq).
We choose **proof terms**, for three reasons: (1) it continues the course's Curry–Howard story —
students already watched λ-terms grow hole-by-hole in `prove`; (2) it satisfies the **De Bruijn
criterion**: the trusted base is one small, independently-runnable checker, and everything else
(tactics, search, UI) may be arbitrarily wrong without endangering soundness; (3) we learned this
lesson the hard way — the 2026-07-24 lambda-lab audit found a false QED precisely because
finalization trusted the tactic layer. **`qed` re-checks the certificate against the original
goal, always.** The LCF alternative gets a book-chapter *section* (compare!), not an implementation.

**D3 — The LLM corpus format is designed now, not later.** The long-run goal (post-train a small
LM to drive this prover) needs (state, tactic, state′) data. If tracing is bolted on later, the
printer will be ambiguous and the data noisy. So from day one: **deterministic, canonical
pretty-printing** (one string per term, no alternatives), and a **trace logger** that emits one
JSONL record per tactic application. Every interactive session and every automated search run is
already a data-generation run.

**D4 — Intuitionistic core (Heyting arithmetic), classical as a labeled extension.** The
natural-deduction core is intuitionistic — matching Lecture 3's constructive story and keeping
the BHK reading of every rule. A single axiom toggle (`classical on` adds ¬¬φ → φ as a rule)
lets the book demonstrate *exactly* what classicality buys, mirroring the Peirce discussion.
For arithmetic Π₁ statements this loses nothing (Friedman translation — book material, not code).

---

## 1. The object logic

**Signature:** constants `0`; unary `S`; binary `+`, `·`; predicate `=` (binary). Numerals are
sugar: `3` ⇢ `S(S(S(0)))`.

**Terms** `t ::= x | 0 | S t | t + t | t · t` — variables are named at the surface, **de Bruijn
indices in the kernel** (a deliberate teaching moment: implement substitution once, correctly,
and write the chapter section about why capture is the enemy).

**Formulas** `φ ::= t = t | ⊥ | φ → φ | φ ∧ φ | φ ∨ φ | ∀x. φ | ∃x. φ` with `¬φ := φ → ⊥`.

**Axioms of PA (as rule constants the checker knows):**
- `PA1: ∀x. ¬(S x = 0)`
- `PA2: ∀x y. S x = S y → x = y`
- `PA3: ∀x. x + 0 = x`
- `PA4: ∀x y. x + S y = S (x + y)`
- `PA5: ∀x. x · 0 = 0`
- `PA6: ∀x y. x · S y = x · y + x`
- `IND φ`: from `φ(0)` and `∀n. φ(n) → φ(S n)` conclude `∀n. φ(n)` — a **schema**, instantiated
  by the checker per formula (this is where students see why PA is not finitely axiomatizable —
  book sidebar).
- Equality: `refl`, plus congruence for `S`, `+`, `·` and substitution into formulas
  (Leibniz as a derived rule from congruences — keep the primitive set minimal and documented).

**Proof terms** — one constructor per natural-deduction rule (λ for →-intro, application for
→-elim, pairing for ∧, injections for ∨, `(t, p)` for ∃-intro, `λx.` for ∀-intro, plus the axiom
constants above). The checker is a single structural recursion `check(ctx, proof, formula) -> bool`
of target size **≤ ~300 lines** — that number is a design constraint, not an aspiration: if the
checker grows past it, the rule set is wrong.

## 2. The engine (untrusted, where all the fun lives)

Everything mirrors the post-audit `proof_builder` design, generalized:

- `Goal = (context: hypotheses (name, formula), target: formula)`
- `ProofState = (goals, partial proof term with holes, history, original target, metavar subst)`
- **Term-level metavariables** `?t1, ?t2 …` for to-be-determined witnesses (e.g. `exists 3` vs
  `exists ?` resolved by later unification) — rigid/flexible discipline exactly as in
  `stlc_types`: PA function symbols and bound variables are rigid; only metavariables unify;
  substitutions are proof-wide and propagate to sibling goals.
- `Tactic = Callable[[ProofState, str], ProofState]`, raising `TacticError` (final English text)
  with the state **guaranteed unchanged** on failure. Transactional history; `undo` restores.
- **`checked_final`** builds the complete certificate and runs the *kernel checker* on it against
  the original goal. A tactic-layer bug can never produce a false QED. The session survives a
  failed check.

**Primitive tactics (Stage A–C):** `intro`, `apply`, `exact`, `assumption`, `split`, `left`,
`right`, `cases`, `exfalso`, `refl`, `symm`, `trans t`, `congr`, `rewrite h [at h']`,
`rewrite <- h`, `induction n [with base step]`, `exists t`, `intro x` (∀), `specialize h t`.

**Tacticals (Stage D — the "how tactic languages work" lesson):**
`t1; t2` (then), `t1 <|> t2` (orelse), `repeat t`, `first [..]`, `all_goals t`, `focus n t`.
Implemented as *combinators over the Tactic type* — pure functions returning functions. This
milestone is deliberately separate: it is the moment the tactic *language* appears, and the book
chapter narrates it (LCF's great idea, surviving into Lean's `<;>` and `try`).

**Automation (Stage D):**
- `simp` — an ordered rewrite engine driven by a small, explicit simp-set (PA3–PA6 oriented
  left→right + proved lemmas the user tags). Termination by a measure, documented.
- `decide` — closed-formula evaluation (compute both sides of a closed equation; decide closed
  quantified statements only up to a bound with an honest "bounded check" label).
- `auto [depth]` — backtracking search over the primitive tactics + assumption + simp. This is
  also the **corpus generator** for the LLM stage.

### Checked theorem reuse and arithmetic automation (post-M9)

Live proofs may reuse a named theorem only by importing its already closed certificate as an
ordinary local cut. The surface command is `use <library-theorem> [as <alias>]`. Name resolution belongs
to `library/` and `ui/`; the engine receives an exact formula and proof, rechecks
`check((), certificate, formula)`, and adds that formula to the focused context. The kernel never
learns theorem names and gains no trusted declaration environment.

At surface finalization, exposed implication/forall cuts are contracted by an untrusted,
capture-avoiding proof transformation. Its output is placed in a transient proof state and passed
to the ordinary `checked_final` path with the session owner's **original** target and exact logic
mode. A faulty import, cut compiler, or library entry can therefore cause only rejection.
Imported and live partial certificates have explicit node/depth budgets. Exceeding either raises
an honest transactional `TacticLimit`; QED also translates host recursion exhaustion into a typed
rejection while preserving the session.

Arithmetic automation follows the same certificate discipline. The argument-free `ring` tactic
applies only to a focused equality whose rigid terms use `0`, successor, `+`, and `·`. It reifies
both sides as sparse polynomials over the visible de Bruijn variables and sorts monomials by the
fixed key `(total degree, variable/exponent tuple)`. This computation chooses a proof path; it is
not evidence. Every successor-to-plus-one step, identity, permutation, reassociation,
distribution, coefficient collection, and closed coefficient calculation contributes an ordinary
proof fragment built from PA3--PA6 and the checked M11 semiring certificates. The engine rechecks
the supplied closed laws, their instantiated forms, and the finished equality certificate before
publishing a closed goal. QED independently checks the whole theorem again against the session
owner's original target. No normalization oracle or new kernel proof rule is permitted.

`ring` deliberately has **no hypothesis magic**. It neither rewrites with local equations nor
solves implications, existentials, inequalities, or arbitrary consequences of the context. A
conditional calculation must first expose polynomial identities with ordinary proof structure,
for example `trans <middle>` followed by `rewrite h`; each resulting identity is then a separate
`ring` call. This keeps the tactic's claim auditable: equal sparse normal forms certify an identity,
while different normal forms produce a transactional `TacticError`.

One browser attempt is bounded by 256 input AST nodes, depth 64, 16 variables, degree 16, 64
monomials, natural coefficients at most 128, 25,000 work units, a 100,000-node/256-level generated
proof, and a five-second wall-clock budget. That conservative browser margin was chosen after the
largest required normalization used about 1.4 seconds under native CPython; it must still be
measured under Pyodide when an in-app browser is available. Unresolved term metavariables are
rejected rather than guessed. Any resource or host-recursion exhaustion is an honest transactional
`TacticLimit`. The deadline is checked before normalization, throughout proof construction, and
after synchronous replay, cut reduction, and kernel validation; those synchronous calls are not
preempted mid-call. The browser's Stop control remains the hard abort because all Python runs in a
disposable worker.

## 3. UI: the `peano-lab` page

Clone the lambda-lab shell (xterm + Pyodide worker + fully self-hosted vendor + `?cmd=` deep
links + localStorage history + Stop button). New Python package `peano_lab`, new static page
`/peano-lab/`. Command family:

- `pa prove <formula>` — interactive session (the `prove` UX: goals/context/term panels,
  complete-line `qed`/`abort`, in-proof `help`, `hint`)
- `pa tactic [name]`, `pa lib [name]` — tactic encyclopedia + proved-theorem library
- `pa axioms`, `pa eval <term>`, `pa simp <term>`
- `kb`-style knowledge base entries for PA, induction, De Bruijn, LCF vs proof terms, Gödel
  (a "limits" card — honest about what this prover can never do)
- tutorials: at minimum "prove add_comm by hand" and "build your own tactic"

**Single-owner routing, complete-line aliases, arrow-args-are-propositions** — all the audit's
UI rules apply from day one (they are already implemented patterns; copy them, don't rediscover).

## 4. The trace format (LLM stage, designed now)

One JSONL record per tactic application, appended by the engine (behind a flag in the browser,
always-on in batch/search runs):

```json
{"v": 1, "session": "uuid", "step": 7,
 "goals_before": ["⊢ ∀ n. n + 0 = n"], "focus": 0,
 "tactic": "induction n",
 "goals_after": ["⊢ 0 + 0 = 0", "n : ℕ, IH : n + 0 = n ⊢ S n + 0 = S n"],
 "status": "ok", "error": null}
```

plus a session footer `{"qed": true, "theorem": "...", "proof_size": 12, "tactic_count": 9}`.
Rules: canonical printing only; no ANSI; stable field order; failures are recorded too (an LLM
must learn what *doesn't* work). A `scripts/export_traces.py` collates sessions into a train file.
Success metric for later: a small fine-tuned model, given `goals_before`, proposes `tactic`.

## 5. Testing (non-negotiable, learned from the audit)

1. **Soundness oracle**: every QED in every test re-runs the independent checker; a fuzz suite
   tries scripted attacks (`0 = 1`, `∀n. n = 0`, S-injectivity abuse, capture attacks through
   rewrite-under-binder) that must all fail.
2. **Tactic contract tests**: failure leaves state unchanged; invariants
   `len(goals) == holes(partial)` after every step.
3. **The theorem ladder as regression** (§6): every library theorem's script replays in CI.
4. **Book gate**: extend `verify_book_commands.py` to replay `pa`-family deep links and session
   blocks against the peano-lab driver.
5. Cross-check: `pa lean <thm>` exports the statement (and, for the library, a Lean proof stub)
   so any library theorem can be spot-checked in Live Lean / Mathlib's `Nat`.

## 6. The theorem ladder (acceptance ladder for the whole project)

`0 + n = n` → `add_succ_left` → **`add_comm`** → `add_assoc` → `mul_zero_left` → `mul_comm` →
`mul_add` (distributivity) → `mul_assoc` → `one_mul`, `mul_one`, `add_mul` (the M11 semiring
basis) → `S n ≠ 0`, injectivity as lemmas → order: `n ≤ m :=
∃k. k + n = m`, `le_refl`, `le_trans`, `le_antisymm` → `n ≤ m ∨ m ≤ n` (totality — needs ∨ and
induction working together) → capstone: `∀n m. n·m = 0 → n = 0 ∨ m = 0`.
Each proved **interactively first** (the tutorial), then scripted into the library, then
re-proved by `auto` where feasible (the corpus).

## 7. Module layout

```
peano-lab/
  index.html  worker.js  .htaccess          (cloned shell, own BUILD tag)
  py/
    driver.py                                (dispatch, session-owner routing)
    peano_lab/
      kernel/     terms.py formulas.py subst.py proofs.py checker.py   ← TRUSTED, small
      engine/     state.py tactics.py tacticals.py rewrite.py
                  induction.py decide.py proof_reduction.py ring.py
                  search.py trace.py                                  ← untrusted
      ui/         prove.py panels.py data_tactics.py data_kb.py
                  data_tutorials.py data_library.py
      library/    theorems.py                (scripted ladder proofs)
    tests/        test_kernel.py test_soundness.py test_tactics.py
                  test_tacticals.py test_ladder.py test_ui.py
  vendor/                                    (shared fetch via scripts/fetch_vendor.sh)
scripts/export_traces.py
book/peano/*.md                              (the new book part)
```

Kernel modules import **nothing** from `engine/` or `ui/` — enforce with a test.

## 8. What we are explicitly NOT building

No dependent types, no definitional equality/reduction engine, no term elaborator, no typeclass
resolution, no proof irrelevance puzzles. PA over a fixed signature keeps every one of those
out of scope — that is *why* it is the right testing ground. When the book chapter compares us
to Lean, these absences are the comparison.
