# Implementation diary

Short, dated notes on design decisions taken during implementation — the raw material for this
book part. Keep it as you go, not retroactively.

## 2026-07-26 — project start

Branch created; design document and milestone plan written. Decisions D1–D4 (staged logic,
proof terms + independent checker over LCF, trace format designed up front, intuitionistic core
with a classical toggle) recorded in `docs/PEANO_LAB_DESIGN.md` §0.

## 2026-07-27 — M0 representation choices

- The pinned parser API returns only a de Bruijn tree, not the surface free-name table.  Free
  names therefore receive indices in deterministic first-occurrence order; companion parsing
  helpers retain that table for the future UI.  Bound variables still use ordinary de Bruijn
  depth.  The canonical printer uses Unicode logical symbols and fresh deterministic binder names.
- `subst_term` and `subst_formula` mean *binder-opening* substitution: the selected slot is
  replaced, larger indices close the gap, and replacements shift under binders.  An internal/public
  `shift_formula` companion is necessary to express the quantifier and induction rules without
  capture.  Tests include the classic free-variable-under-`forall` counterexample.
- The certificate checker is bidirectional: introduction forms are checked against a target and
  elimination/equality forms synthesize their result.  This preserves the pinned unannotated proof
  constructors and keeps the trusted code small; certificates are kept in checkable normal form.
- Two architecture tensions are recorded rather than silently hidden.  `EqSubst` remains a kernel
  primitive because the API stub explicitly requires it, although design §1 also calls Leibniz
  substitution “derived”.  The required IND certificate for `forall x. x + 0 = x` deliberately
  exercises the schema but is logically redundant because PA3 is exactly that formula.
- **Objection for M3 review:** the binding design requires a classical DNE toggle, but the pinned
  kernel certificate language names only PA1–PA6 and has no DNE constructor.  The tactic layer
  cannot soundly add DNE by itself.  M3 will need an explicit, labeled kernel certificate form (and
  a checker mode or premise) before `classical on` can close any new theorem.
- An adversarial review found that Python subclasses could override an AST node's equality and fool
  an `isinstance`-based trusted recursion.  The checker now admits only the *exact* frozen kernel
  constructor classes at every boundary.  The concrete forged-`Zero`, forged-formula, and
  forged-proof attacks are permanent regression tests; this is a useful Python-specific extension
  of the De Bruijn criterion.

## 2026-07-27 — M1: holes, shared metavariables, and rewrite certificates

- `Hole` and `MetaVar` live in the untrusted engine as distinct subclasses of kernel `Proof` and
  `Term`.  The kernel's exact-constructor boundary therefore rejects either if finalization ever
  leaks one.  Globally unique IDs and copy-on-write substitutions follow the audited Lambda Lab
  pattern; each successful unifier is applied to every goal, context formula, and embedded term in
  the partial certificate, never to the original target or history snapshots.
- A partial certificate is one tree whose left-to-right holes correspond exactly to the goal tuple.
  Tactics replace only the focused hole.  `Step.state_before` stores the exact immutable transaction,
  so `undo` returns that object and a raised `TacticError` has nothing to roll back.
- M1 rewrites the first eligible occurrence in formula-left-to-right, term-preorder order.  The
  motive reserves de Bruijn index zero and capture-safely shifts every untouched variable.  Bodies
  of `forall`/`exists` are recognized but rejected until M3.  Forward rewriting of a goal inserts
  the *reverse* equality transport because the new subgoal must reconstruct the old target.
- Rewriting a hypothesis needs a sound local cut.  The engine derives the rewritten proposition,
  wraps the new hole in implication-introduction/elimination, and retains the old hypothesis under
  a fresh `_before` name so kernel hypothesis indices stay literal.  This exposed a completeness
  gap in M0's bidirectional checker: application of an introduction did not synthesize.  A small
  target-directed `ImpElim` case now validates this ordinary cut without trusting the engine.
- The M1 plan did not spell out how a context-free session could use PA3–PA6 before `specialize`
  arrives in M2.  `rewrite PA3` ... `rewrite PA6` therefore performs deterministic first-order
  pattern matching, emits explicit nested `ForallElim(Axiom(...), term)` certificates, and checks
  each instantiation.  This makes the required `S 0 + S 0` proof possible without a hidden evaluator.
- Trace records use one shared `?t1`, `?t2`, ... display map across sibling goals, stable v1 key
  order, canonical Unicode, no ANSI, and include failures.  Tracing remains an untrusted side effect;
  successful QED emits the specified footer only after the independent checker accepts.
- A second adversarial pass sharpened “original” into an API boundary.  A frozen state can still be
  replaced wholesale by buggy tactic code, including its cached `target`.  `checked_final` therefore
  requires the session owner's original formula as a separate argument, rejects a mismatching cache,
  and passes only the external original to the kernel.  M5's single-owner router must keep that value
  outside every tactic result.  The exact forged-target exploit is now in `test_soundness.py`.
- “Frozen” also has to be deep enough: a plain `dict` inside a frozen dataclass let callers mutate an
  undo snapshot through an alias.  States now copy substitutions into read-only mapping proxies and
  normalize all state collections to tuples.  Trace review similarly made metavariable aliases
  session-stable across before/after transitions and scrubbed ANSI from tactic/error fields too.

## 2026-07-27 — M2: induction is certificate construction

- `induction n` has two honest readings.  On an outer `forall`, `n` is a fresh surface name for
  that binder and the focused hole becomes `Ind(motive, base, step)`.  After `intro n`, the name is
  instead a rigid context variable: the engine abstracts precisely that de Bruijn slot into the
  motive, builds the same `Ind`, and explicitly specializes the resulting universal certificate at
  the original variable.  Neither path adds an induction oracle to the tactic layer.
- The step goal is displayed with a fresh `IH` as its newest hypothesis.  Its older hypotheses are
  shifted under the new natural-number binder, exactly matching the kernel context beneath
  `ForallIntro(ImpIntro(...))`.  The base goal retains the original context.  Tests exercise both
  entry paths so a display-name shortcut cannot accidentally stand in for binder arithmetic.
- Universal `intro` likewise shifts every hypothesis when it descends under a term binder.
  `specialize h t` derives `h[t]` with `ForallElim` and installs it through the same explicit local
  cut used by hypothesis rewriting; the original universal remains under a deterministic
  `_before` name.  Specialization requires a concrete term in M2—metavariable witnesses remain the
  explicitly scoped M3 existential feature.
- The first genuinely inductive ladder theorem, `forall n. 0 + n = n`, now closes in six primitive
  tactics: induction, the PA3 base rewrite, reflexivity, the PA4 step rewrite, successor congruence,
  and the named induction hypothesis.  The contrast with PA3's immediate `n + 0 = n` is visible in
  the proof state rather than hidden in an evaluator.
- Audit added a small but important UI invariant: term-variable and hypothesis names share one
  visible namespace.  Reserved parser words (`S`, `forall`, `exists`, `bot`, `false`) cannot be
  binders, and generated `IH`, `_before`, and `_parameter` names avoid both kinds of declaration.
  These collisions were not logical unsoundness—the kernel uses indices—but ambiguous or
  non-round-trippable proof states would violate the canonical-display law.

## 2026-07-27 — M3: resolving the classical boundary before coding it

- The M0 objection is real: the binding design simultaneously pinned an intuitionistic
  `check(ctx, proof, formula)` API with no DNE certificate and required an OFF-by-default DNE
  toggle.  An engine-only flag cannot authorize a certificate, while accepting an unlabelled or
  unconditional classical step would make “off” unenforceable at the trusted boundary.
- The smallest explicit amendment keeps `check` exactly intuitionistic and adds one inert
  `DNE(proposition)` certificate plus a sibling `check_classical` entry point over the same
  structural recursion.  `checked_final(..., classical=False)` receives that Boolean from the
  session owner, not from tactic-controlled proof state.  Thus an injected DNE node is rejected in
  HA mode, accepted only in the labeled PA+DNE extension, and remains visible in the artifact.
  This is an implementation of design decision D4, not a silent change to the object logic.
- The v1 trace record has no mode field and its field set is already binding.  Mode changes will be
  recorded as ordinary successful `classical on`/`classical off` events with unchanged goals; a
  replay reconstructs mode sequentially.  Adding a field would require an explicit v2 format, so
  M3 does not mutate v1 under the table.  The future session banner reads the same owner-held mode.
- M3 is also the first point where a witness metavariable can meet a later eigenvariable.  A plain
  global `?t` would allow the bogus route `exists ?; intro y; refl` for formulas such as
  `exists x. forall y. x = y`.  Engine metas therefore carry a de Bruijn protection depth: lifting
  under a binder increments it, and unification may lower a candidate only when that candidate
  contains no locally bound variable.  This keeps proof-wide inference useful without allowing
  witness escape or teaching a knowingly restricted fake version of `exists ?`.
- Rewriting below a quantifier is sound for an equation already available outside that quantifier:
  at depth `d` it matches `shift(source, d)`, inserts `shift(replacement, d)`, and puts the motive
  placeholder at `Var(d)`.  A PA axiom cannot be naively instantiated with the target's locally
  bound `Var(0)` outside the binder; users must `intro x; rewrite PA3` unless a future dedicated
  binder-local transformer is added.  Treating that local variable as outer would be capture, not
  convenience.

## 2026-07-27 — M3: connective certificates and adversarial closure

- `apply` peels leading universal binders into scoped metavariables and implication binders into
  ordinary premise goals; it never treats a successful unification as a proof. Every branch still
  installs an explicit `ForallElim`/`ImpElim` certificate. If a vacuous universal leaves an
  implicit term only in the certificate and in no open obligation, the engine chooses the
  canonical closed witness `0`. This is deterministic elaboration, not a logical rule, and the
  resulting certificate must still pass the kernel.
- `cases` mirrors each eliminator rather than destructively editing the context. Disjunction and
  existential elimination create branch/eigenvariable obligations directly; conjunction
  projections and rewritten hypotheses enter through explicit local cuts. Thus context names are
  UI conveniences while kernel hypothesis indices and eigenvariable conditions remain literal.
- `<=`/`≤` is parser and printer sugar only: `a ≤ b` is exactly `∃k. k + a = b`; there is no trusted
  `Le` node. The same canonical recognizer is used by rigid trace goals and theorem footers so
  training data cannot alternate between sugared and expanded spellings.
- The PA hint routine is deliberately observational. It has a caller-supplied check budget,
  allocates no holes or metavariables, and suggests only a primitive command that can be replayed.
  Failed mode changes likewise emit transactional error records; neither tracing nor hints can
  change proof authority.
- Adversarial review exercised 5,625 generated scoped unifications, nested binder shifting,
  witness/case ordering, 30,000 rewrite cases, 1,000 complete rewrite certificates, 20,000 printer
  round trips, and 10,000 hint states. It found four contract gaps, all made permanent tests:
  proof-only vacuous instantiations needed deterministic grounding, truthy non-Booleans could
  impersonate classical authority, rigid `≤` traces used the expanded spelling, and rejected mode
  commands were not logged. After repair the full Peano suite has 187 passing tests, the Lambda
  Lab regression suite remains 360 passing with 36 subtests, and the independent checker is 234
  lines.

## 2026-07-27 — M4: automation must remain untrusted and replayable

- Tacticals will be ordinary functions from tactics to tactics, but a compound invocation is one
  user transaction: if any required branch fails, the caller still holds the exact input state;
  on success one `undo` restores that input. `then` and `all_goals` snapshot the goals they mean to
  visit so a tactic cannot accidentally iterate forever over subgoals it just created.
- Closed computation has two deliberately separate products. A semantic evaluator may report that
  a closed equation is true or that a bounded quantifier search found no counterexample; only a
  proof-producing path may close a goal, and its output is still checked by the kernel. A bounded
  check is labeled with its finite range and is never promoted into a universal certificate.
- Backtracking search will explore immutable states without logging speculative successes. Once it
  finds a complete plan, it replays only that winning primitive sequence through the normal tactic
  dispatcher and v1 logger. This keeps traces sequentially replayable while search remains free to
  be wrong; final QED still uses the externally owned original theorem and independent checker.
- **Objection for M7 review:** the pinned proof language is bidirectional but has no formula
  ascription/cut node. The kernel can *check* an arbitrary closed proof of `∀x. φ`, yet
  `ForallElim` can reuse it only when that proof also synthesizes its universal formula. M4 `simp`
  therefore accepts PA constants, inferable checked rule certificates, and explicitly selected
  context hypotheses, but rejects a tagged closed certificate it cannot transport. Adding a small
  checked ascription node would be logically conservative, but doing so silently would violate the
  binding constructor list; revisit explicitly when M7's theorem-library reuse makes the tradeoff
  concrete.

## 2026-07-27 — M4: termination orders, backtracking, and audit lessons

- Tree size cannot justify simp termination because PA6 turns `x · S y` into the larger
  `x · y + x`. The rule gate therefore uses lexicographic path ordering with
  `· > + > S > 0`; PA3/PA5 descend to a subterm, while PA4/PA6 decrease a recursive argument under
  a lower-precedence head. Pure permutations use a deterministic total extension and fire only in
  its decreasing direction. An optional step cap is labeled as a resource limit, never presented
  as the termination proof.
- A simp result is a normal formula plus an ordered list of equation proofs and motives. Closing a
  normal form uses only reflexivity, an exact hypothesis, or structural congruence; transport back
  nests explicit `EqSubst` nodes. This separation made 500 randomized generated transports easy to
  submit directly to the independent checker.
- Search depth measures one proof-tree branch, so sibling goals reuse the same allowance. The first
  implementation nevertheless chose only the first solution of each sibling: if a later sibling
  contradicted a shared metavariable assignment, it never resumed the earlier choice. Turning
  child solving into a generator restored genuine backtracking. Complete leaves receive an
  advisory kernel check so a locally plausible but non-synthesizing certificate becomes another
  failed branch, not a misleading goals-closed result; external-original finalization remains the
  actual QED authority.
- Focused tacticals exposed a second proof-wide metavariable lesson. A child run on one isolated
  goal made `_commit` think an older shared meta was proof-only and default it to zero, hiding the
  sibling that would later infer one. Canonical grounding is now restricted to metas freshly
  introduced by the current tactic. Older metas remain flexible across `focus`, `then`, and
  `all_goals`; the exact counterexample is a permanent kernel-checked regression.
- The plan's “~100 lines” for tacticals proved incompatible with simultaneously making arbitrary
  goal focus certificate-hole-safe, validating child contracts, propagating substitutions, and
  collapsing compound history into one undo transaction. The file is intentionally about 270
  comment-rich physical lines rather than hiding that machinery or deleting the pedagogical
  invariants. This is a deliberate clarity/soundness objection to the estimate, not a change to the
  tactical API.
- Final adversarial passes covered 1,500 random search formulas (401 successful plans, all checked),
  4,845 generated arithmetic decisions/certificates, 10,000 bounded formulas, certificate
  mutations, malformed states, nonzero focus under every binder/eliminator family, and huge search
  depths. The milestone closes at 277 Peano tests, 360 Lambda tests plus 36 subtests, and an
  unchanged 234-line trusted checker.

## 2026-07-27 — M5: the browser is a session owner, never a proof authority

- The UI copies Lambda Lab's audited routing law: once `pa prove` starts, that proof session owns
  each complete input line before ordinary command dispatch. Thus `qed`, `abort`, `help`, `?`, and
  tactic lines have one unambiguous interpreter, while a nested `pa prove ...` can be refused
  without touching the active state. Aliases are exact, case-sensitive whole-line matches; a token
  appearing inside a proposition or an argument cannot become a control command by accident.
- The owner retains the originally parsed formula, its free-variable name table, the trace logger,
  and the classical-mode Boolean outside the untrusted `ProofState`. QED supplies those retained
  values to `checked_final`; it never accepts a theorem or mode back from a tactic result. A failed
  kernel finalization leaves the owner and state live so the learner can inspect, undo, or abort.
- The static page remains a worker shell: Pyodide and every Python source run off the main thread,
  Stop terminates that worker, and restart creates a fresh proof owner. The Peano and Lambda pages
  use one version-pinned vendor payload but keep distinct BUILD tags and browser-history keys, so
  cache invalidation and sessions cannot bleed across the sibling labs.
- A browser-shell audit found that worker isolation alone is not enough. Deep-link and stored-history
  text must be stripped of C0/C1 controls before xterm echoes it; the worker URL needs the BUILD key
  just like its Python fetches; fatal worker errors must settle pending promises; and Stop needs an
  Escape/Ctrl-C path while xterm owns keyboard focus. Those are now static contracts, alongside an
  exact equality check between the worker manifest and every Python module on disk.
- Corpus integrity is also an owner responsibility. Compound `focus 2 ...` steps now record focus
  index one, JSONL renders C1/bidirectional controls as visible escapes, panel metavariable aliases
  persist for the whole session, and QED/abort footers use the owner's original name table. The
  independent checker was already sound; these repairs ensure the pedagogical display and training
  records cannot tell a different story from the theorem that was checked.
- Decimal sugar is capped at `256` by the browser driver before parsing. Without this UI boundary,
  the nine-character input `100000000` asks the surface parser to allocate one hundred million
  successors. This is a recoverability limit for an interactive page, not a new axiom or a bound in
  the PA object language; explicit symbolic terms remain governed by the ordinary input-size guard.
- The final local artifact mounted the exact 21-file worker payload in pinned Pyodide and proved
  `add_comm` via `auto 5` followed by `qed`; every staged HTTP path and vendor hash also passed. The
  session's in-app visual browser surface was unavailable, so DOM interaction is recorded as an
  outstanding manual release check rather than silently claimed. No staging or production SSH
  deployment was performed in M5.
- Final audit also treated U+2028 and U+2029 as record delimiters, not merely printable Unicode.
  Escaping the `Zl`/`Zp` categories in both the trace and browser boundaries preserves the v1 law
  that one JSON object is one physical line. M5 closes at 312 Peano tests, 360 Lambda tests plus 36
  subtests, and an unchanged 234-line trusted checker.
