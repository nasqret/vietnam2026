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

## 2026-07-27 — M6: prose that must execute

- A tactic encyclopedia is dangerous if its examples merely look convincing. The registry therefore
  has one card for every real primitive and tactical, and every example is a complete script replayed
  in a fresh `LabSession` through checked QED. Goal effect and certificate effect are separate fields:
  `simp`, for example, may finish a normal equality with explicit `CongS`/`CongAdd`/`CongMul`, not
  only `Refl` or a hypothesis. An independent content audit caught and corrected that distinction.
- KB cards are immutable UI data with no route into the kernel. They state the six rule constants
  exactly, distinguish de Bruijn indices from the De Bruijn criterion, and say what checking cannot
  establish: bounded-search failure is no verdict, derivability is not standard-model truth, and a
  small checker is not a proof of its own correctness or of PA's consistency.
- The tutorial state machine owns raw lines, but its frozen proof commands must not be sent back
  through that same owner. Each chapter therefore keeps a private nested proof-session dictionary
  and calls the production `ui.prove` path directly. ENTER advances only after a command succeeds;
  failed commands remain on the exact step, and a QED-gated chapter cannot complete until the nested
  session has closed through `checked_final`.
- The first draft of the `add_comm` lesson proved an implication from two earlier ladder rungs. That
  was honest but did not meet “prove add_comm by hand.” Replaying `auto`'s winning trace exposed a
  clearer premise-free nested-induction script; the tutorial now executes those primitive/simp steps
  without calling `auto` and checks the actual theorem `∀n m. n + m = m + n` from an empty context.
- The existing book gate had two top-level modules both named `driver`. They are loaded under distinct
  aliases, then links route by `/peano-lab/` path or `pa` command and fenced blocks route by their
  `λ>`/`pa>` prompt. Failure detection is line-oriented so explanatory cards may discuss errors while
  actual tactic errors and rejected QEDs still fail the build. Both source-fallback and built-HTML
  extraction are tested. The page BUILD tag moved to `2026-07-27b` so cached M5 workers cannot omit
  the four new UI modules.
- Browser drivers deliberately catch unexpected Python exceptions and print a one-line class name,
  so searching only for a traceback let a crashed command pass the first dual-driver gate. The gate
  now recognizes line-anchored `*Error:`/`*Exception:` results for both labs while a card may still
  discuss `ValueError:` inside a sentence. The exact staged 25-file worker payload was finally loaded
  under pinned Pyodide; it rendered both registries and completed the ENTER-only `add_comm` tutorial
  through checked QED. M6 closes at 373 Peano tests, 360 Lambda tests plus 36 subtests, a warning-free
  17-page Jupyter Book build, and an unchanged 234-line trusted checker.

## 2026-07-27 — M7: theorem reuse without a trusted theorem oracle

- The M4 objection about reusable introduction-form certificates is real: the binding kernel can
  check a `ForallIntro` proof at a known formula but cannot always synthesize that formula when the
  same proof is placed under `ForallElim`. I am not adding an ascription constructor or a trusted
  theorem environment. Each library script instead proves a curried goal whose earlier rungs are
  ordinary local hypotheses. The untrusted library layer then performs explicit proof-term cut
  elimination, replacing those hypothesis references with the earlier closed certificates and
  adjusting de Bruijn hypothesis indices beneath implication, disjunction, and existential
  binders. The independent kernel finally checks the composed certificate against the original,
  dependency-free theorem statement. A composition bug can therefore only be rejected.
- Library entries remain replayable data: one closed statement, an acyclic list of earlier rungs,
  and a sequence of primitive tactic commands. Generated dependency introductions are displayed
  separately from the authored body so the browser can explain both what theorem was claimed and
  how theorem reuse was compiled away. This keeps the kernel fixed at the binding rule set while
  making the proof dependency graph visible to students.
- The first cut eliminator passed arithmetic but failed at the two-dependency antisymmetry helper.
  Two distinct scope hazards were exposed. Sequential dependency passes could revisit hypotheses
  internal to an already inserted certificate, so dependency slots are now substituted
  simultaneously. The substitution also exposes `ForallElim(ForallIntro(...), t)` and
  `ImpElim(ImpIntro(...), p)` redexes; both must be contracted capture-safely because the
  bidirectional checker rightly refuses to synthesize arbitrary introduction forms. The complete
  helper chain now checks from the empty context, and a permanent regression targets the original
  multi-dependency failure.
- A named `mul_succ_left` helper is intentionally included even though it is not one of the binding
  headline rungs. It turns multiplication commutativity from a 21-command, 266-node nested proof
  into a six-command proof whose algebraic idea is visible. The same rule applies to the order
  helpers: naming the genuine mathematical obstruction is clearer than hiding it inside a giant
  tactic script, and every helper remains an ordinary kernel-checked theorem.
- M7 closes with all twenty entries checked from the empty context, 1,300 certificate nodes across
  the library, and all twenty generated Lean statements accepted by Lean 4.28 (the only warning is
  the deliberately visible proof stub). Three audits mutated every certificate, shifted goals,
  attacked proposition/term capture, and checked the browser/Lean presentation. The final suites
  report 433 Peano tests and 360 Lambda tests plus 36 subtests; the trusted checker remains 234
  lines. The exact staged 28-file payload also replayed the whole ladder in pinned Pyodide.

## 2026-07-27 — M8: turn the implementation record into a course

- The binding outline becomes six narrative chapters rather than one long retrospective: motivation
  and staging; the kernel boundary; a tactic's anatomy; tacticals as a language; induction and the
  ladder; and deliberate limits. The executable tutorials and theorem reference stay as companion
  pages. This keeps the main argument readable while preserving the exact commands and full scripts
  where students need them.
- The chapters are built from this diary, but diary claims are not treated as evidence. Commands and
  browser links use the production grammar and pass through the dual-driver book gate; source claims
  link to the implementation or tests that enforce them. A polished explanation may compress an
  incident, but it must not invent a proof or silently improve the running system.
- The landing page now says “live” and makes the trust story the announcement: tactics construct,
  the independent 234-line kernel checks. It links both the browser surface and this construction
  account, and names the twenty-entry checked ladder rather than promising an unspecified future
  prover.
- Three independent prose audits compared the chapters line by line with the implementation. They
  caught eight small but meaningful overstatements: `auto` preserves primitive undo entries, a trace
  row's rendered goals are not a full replay snapshot, permutative `simp` rules are ordered at each
  instance, traced programmatic calls require a logger, and the capstone base proof ignores its PA5
  premise. After correction, the six chapters contain 15 live links and 45 replayed commands.
- M8 closes with a warning-as-error 24-page book build and a full gate over 190 links plus 78 session
  commands. The vault has 49 notes with no unresolved wiki-links; the suites report 436 Peano tests
  and 360 Lambda tests plus 36 subtests; the trusted checker remains 234 lines. The in-app browser
  runtime is still unavailable, so the visible landing panel remains an explicit manual DOM check.

## 2026-07-27 — M9: data without a second meaning of proof

- The logger's binding v1 rows remain immutable. Exported `train.jsonl` and `val.jsonl` contain the
  same nine ordered transition fields; theorem text and QED metadata belong to footers and aggregate
  statistics, not an invented v2 training row. Deduplication ignores only session identity and step
  number, while keeping every field that changes the learning problem—including failure text.
- Input continuity and output use are different contracts. The exporter must validate each complete
  contiguous session, sequential steps, transactional errors, and exactly one adjacent footer. After
  validation, train/validation files are independent transition examples, so removing duplicate rows
  is allowed to leave gaps in their original step numbers. The theorem/session group is nevertheless
  the split unit, and a semantic duplicate may never leak into both sides.
- Synthetic generation is not permission to fabricate JSON. Every row must come from the production
  `TraceLogger` while the real engine attempts a real tactic. Successful sessions finish only through
  `checked_final` against their owner-held original goal; honest failed ladder sweeps and deliberately
  inapplicable tactics remain useful negative records.
- The evaluator follows the same rule. A policy may stop, exhaust its budget, or produce an apparently
  closed state; an attempt counts only when the independent checker accepts the final certificate for
  the original theorem. A deterministic random policy is therefore a plumbing baseline for the whole
  proposal-to-kernel path, not a miniature theorem-proving result.
- A seed is not a run identity. Two batches can share a seed while differing in configuration,
  theorem fixtures, source, checker, or Python runtime. The generator now hashes all of those inputs
  into a run fingerprint and prefixes every session ID with it, so honest multi-file collation does
  not turn distinct traces into apparent duplicate sessions.
- The exporter must bind metadata back to state, not merely validate its shape. A footer claiming a
  different theorem could evade exclusions and poison theorem-group splits even though every JSON
  field looked valid. The strict importer therefore requires exactly one initial goal and equality
  between its canonical post-turnstile target and the footer theorem. It also recognizes
  case-insensitive/hard-link input aliases and publishes all three output files with rollback.
- “The policy does not see the theorem name” includes indirect channels. The first evaluator seeded
  its policy-visible RNG from that hidden name, and it recreated metavariable aliases each turn;
  both made evaluation differ from the promised trace input. Seeds now derive from the visible
  canonical goal, aliases live for the full rollout, and the four literal held-out statements carry
  a fixed SHA-256 checked against the theorem library.
- Error categories are control flow, not prose. Ordinary `TacticError` remains recoverable inside
  tacticals, malformed surface input is a non-recoverable `TacticSyntaxError`, and resource exhaustion
  is `TacticLimit`: `repeat` propagates it while `first`/`orelse` retain it when no alternative
  succeeds. That distinction now survives bounded `auto`, bounded `simp`, planning, and replay, so
  hostile tactic arguments cannot spoof evaluation status through English substrings. The final audit
  also reproduced absent case-only and Unicode-normalization output aliases on this Mac, plus an
  ancestor/child output topology; all are rejected before either artifact path is created.
- M9 closes with a 13,152-row committed release (12,540 train / 612 validation), produced by 1,596
  independently finalized synthetic sessions with all ladder sources disabled. The separate
  all-ladder smoke generated 13,417 raw and 13,412 unique exported transitions, including 20 honest
  bounded-auto attempts and 20 checked authored replays. The random baseline ran 32 pinned held-out
  attempts through the production grammar and kernel judge; its 0.0 pass@8 is an honest plumbing
  result, not a theorem-proving claim. Focused M9 reports 62 tests, the full Peano suite 498, Lambda
  360 plus 36 subtests, the book/gate and 52-note vault are clean, and the checker remains 234 lines.

## 2026-07-27 — M10: a theorem environment compiled away

- The odd-square induction exercise exposed a precise usability gap: the witness and induction
  hypothesis were correct, but live proofs could browse checked associativity, commutativity, and
  distributivity without being able to use them. Re-running those lemmas by nested induction inside
  every theorem would be sound but pedagogically perverse.
- `use <library-theorem> [as <alias>]` is intentionally a surface bridge, not a new kernel proof source.
  The UI resolves a replayed theorem; the engine rechecks the closed formula/certificate pair and
  inserts `ImpElim(ImpIntro(hole), certificate)`. Existing tactics then see an ordinary hypothesis.
- Tactical history cannot identify imports: `use add_comm; exact add_comm` becomes one outer `then`
  transaction. Surface finalization therefore examines a completed certificate, contracts its
  exposed implication/forall cuts in a transient state, and calls `checked_final` again with the
  owner's original target and logic mode. The raw immutable state remains available to exact undo.
- A final resource audit found that distinct aliases could otherwise grow this temporary cut tree
  until Python recursion failed outside the tactic error path. `use` now measures theorem and live
  certificates iteratively, applies explicit node/depth limits transactionally, and QED maps any
  remaining host recursion exhaustion to an `InvalidProof` while retaining the session.
- `use` solves availability, not symbolic polynomial normalization. A two-lemma additive example
  now closes in milliseconds, while bounded trials of the odd-square step still make `simp` expand
  impractically. That evidence fixes the next boundary: M11 supplies a checked semiring basis and
  M12 builds a certificate-producing `ring`; the kernel remains unchanged.
- M10 closes with the two-import theorem independently checked, 520 Peano tests and all 360 Lambda
  tests plus 36 subtests green, 190 links/18 blocks/85 commands replayed, the warning-as-error book
  green, and 53 vault notes/238 links/0 unresolved. The source-bound 13,152-row corpus was
  regenerated from 1,596 checked sessions; the trusted checker is still exactly 234 lines.

## 2026-07-27 — M11: only the missing algebraic orientations

- The semiring audit began from the normalizer's proof obligations rather than a wish list of
  familiar lemma names. PA3 and PA5 already give the right zero laws; `zero_add`, `mul_zero_left`,
  both commutativity and associativity laws, and `mul_add` were already checked rungs. Adding
  `add_zero`, `mul_zero`, successor-as-plus-one, or numeral-specific laws would duplicate that base.
- Exactly three entries were missing: `one_mul`, `mul_one`, and left distributivity `add_mul`.
  Their authored scripts use the existing induction and simplifier surface; dependencies remain
  earlier and acyclic. Their final certificates have 26, 31, and 748 nodes and all check from the
  empty context. The largest has depth 45, well below M10's 128-level import limit.
- Capture tests import each certificate below both a universal binder and an implication binder,
  then specialize it with terms containing the outer variable (`x`, `S x`, and `x + 1`). QED cut
  compilation and the independent checker accept the exact wrapped statements. This tests the
  representation boundary that M12 will rely on, not merely three top-level equations.
- M11 closes with 84 focused and 527 full Peano tests green, all 360 Lambda tests plus 36 subtests,
  the three Lean 4.28 stubs elaborated, and all 190 links/18 blocks/85 commands replayed. The
  warning-as-error book and 54-note/247-link vault are clean; the regenerated 13,152-row corpus
  records all 23 rungs; the checker remains exactly 234 lines.

## 2026-07-27 — M12: computation chooses, certificates justify

- The odd-square exercise fixed the user-facing boundary. The witness is `x + S n`, but asking
  `simp` to discover and replay the polynomial rearrangement is both opaque and impractical.
  `ring` instead has one narrow job: close a focused equality when its two sparse
  commutative-semiring normal forms are identical.
- The sparse calculation is not trusted. Successor is certified as addition by one from PA3/PA4;
  identities, AC permutations, and distribution use the closed M11 law certificates; coefficient
  arithmetic produces PA3--PA6 proof terms. Supplied laws, instantiated laws, and the finished
  certificate are checked before the state is published, and ordinary QED checks the original
  theorem once more.
- `ring` takes no arguments and never mines the local context. The readable induction step uses
  `trans ((2*n+1)*(2*n+1)) + 8*S n`, proves that identity with `ring`, rewrites forward by
  `IH_witness`, and calls `ring` again. This explicit proof structure was preferable to a
  hypothesis-aware mini-solver hidden behind `ring [IH_witness]`.
- Browser predictability is part of the contract: 256 AST nodes/depth 64, 16 variables, degree 16,
  64 monomials, coefficient 128, 25,000 work units, 100,000 proof nodes/depth 256, and a five-second
  wall-clock budget. The required large normalization measured about 1.4 seconds under native
  CPython; the in-app browser was unavailable, so a direct Pyodide timing remains a deployment
  check. Metavariables and non-equality goals are rejected;
  differing normal forms are a transactional `TacticError`, while exhausted budgets are a
  transactional `TacticLimit`.
- The integrated gates are green. The exact odd-square transcript reaches checked QED; mutations of
  its coefficient, constant, witness, middle expression, proof leaves, or context discipline are
  rejected transactionally, as are forged basis laws and every explicit resource limit. Peano has
  581 passing tests; Lambda has 360 tests plus 36 subtests; the warning-as-error 24-page book replays
  190 links/19 blocks/96 commands; the vault has 55 notes/258 links/0 unresolved. The regenerated
  source-bound corpus keeps 13,152 rows from 1,596 checked sessions, local staging is green, and the
  trusted checker is still 234 lines.

## 2026-07-27 — M13: calculate narrowly, justify completely

- `norm_num` deliberately computes less than Python could. It sees only closed numerical islands in
  an equality (optionally below a bounded leading universal spine), chooses a unary numeral, and
  builds the PA3--PA6 and congruence proof that the kernel expects. A computed Boolean or integer is
  never proof authority; the bridge is checked before commit and the original theorem is checked at
  QED.
- Open normalization remains honest. If the two normalized terms are not identical, the tactic
  transports one explicit residual goal back to the original equality. It does not read hypotheses
  as rewrite rules. This keeps the teaching distinction sharp: `simp` rewrites, `norm_num` certifies
  concrete arithmetic, `ring` certifies unconditional polynomial identities, and `auto` searches.
  General PA and nonlinear consequences of assumptions are outside all four; a future `omega`
  requires its own certificate language and limits.
- Browser safety is part of the semantics exposed to students: term shape, leading binders,
  computations, values, work, generated bridge, complete live proof, and wall time are all bounded.
  Every ordinary failure or exhausted limit is transactional. The pure hint path uses the same
  focused hole and projected immutable commit, but consumes no hole ID and publishes no history.
- The teaching surface now includes a tactic card, checked tutorial, this executable chapter, a
  connected vault concept, controlled failure/success traces, and a generator-v2 numerical corpus
  tranche. The reproduced v1 release has 13,344 unique rows from 1,692 checked QED sessions; its
  18-row validation split is explicitly only a same-family pipeline check.
- M13 closes locally with 641 Peano tests, 360 Lambda tests plus 36 subtests, a warning-free 25-page
  book whose 193 links and 125 commands replay, 56 vault notes/271 links/0 unresolved, green corpus
  smoke and evaluator-v2 plumbing, green staging/vendor hashes, and the unchanged 234-line kernel.
  No in-app browser instance was available, so direct Pyodide interaction is left as an explicit
  publication limitation rather than an invented measurement.

## 2026-07-27 — M14: bytes may race; proof meaning may not

The word “lightweight” had hidden two different quantities. Peano Lab's checker and tactic code are
small enough to read, but the browser must still acquire and instantiate CPython through Pyodide.
The live audit made the distinction concrete: the largest 8.6 MB WASM response was uncompressed,
and the worker awaited thirty-one source fetches in series. That latency was delivery overhead, not
the cost of checking a proof and not a Python service running on the host.

Caching required more care than adding a long `max-age`. Pyodide constructs the URLs of its own WASM
and standard-library files from `indexURL`; their old vendor paths could be overwritten by a later
dependency refresh. An early M14 draft fixed that namespace but still treated `worker.js?v=BUILD`
as immutable while deployment overwrote `worker.js`. Review caught the mixed-release race before
staging. The final topology places vendor bytes below a digest of the canonical source manifest and
worker/Python bytes below a digest of their own application manifest. Old release directories stay
available, complete new directories upload first, and non-stored HTML is published last as the small
release pointer. The fetch script refuses to reuse a vendor namespace if its canonical manifest
changes; tests similarly bind every application file to its release ID.

Review found that “canonical” also has to specify a locale: a bare `sort` gave identical vendor
bytes different manifest IDs on macOS and Linux. Both manifest builders now use `LC_ALL=C`; the
current vendor namespace is `v-85fb3352e49c` and the worker/Python namespace is
`a-573bb5060d7b`. Staging regenerates and compares the complete inventories, copies only the 31
non-test Python files named by the application manifest, and rejects an extra or missing byte. A
repeatable delivery gate then compares all 32 worker/Python hashes, exercises normal, partial, and
conditional cache responses, checks source and WASM compression negotiation, decodes the pinned
WASM, and enforces the three-megabyte encoded bound before production promotion.

The local candidate closes with 647 Peano tests, 360 Lambda tests plus 36 subtests, a clean
warning-as-error 25-source book, 193 checked links, 125 replayed commands, and a 57-note/281-link
vault with no unresolved edges. The kernel directory is byte-unchanged and its checker remains 234
lines. The in-app browser was not attached in this session, so interactive cold/warm-ready, QED,
and Stop/restart observations remain an explicit publication limitation; transport behavior is
instead pinned by the deterministic worker harness and the live HTTP delivery gate.

The first staging gate stopped before production exactly where it should. Gzip worked for static
WASM and source, but neither HTML nor content-addressed assets received `Cache-Control`. A guarded
`mod_expires` fallback likewise emitted nothing, while an unguarded `Header` probe returned HTTP
500. This proves only that the account's static `.htaccess` cannot provide the policy; it does not
identify which modules are loaded in the central Apache/proxy tier. A tiny PHP probe proved that PHP
headers would survive the front proxy, but routing thirty-one sources and the 8.6 MB WASM through
PHP would amend the binding “static site” contract and could add shared-host contention. That is not
a choice to hide inside a transport patch. The probe and experimental relays were removed, staging
was restored to commit `a099596`, and production was left on M13 pending owner review: enable cache
headers at the host/proxy (preferred), or explicitly authorize and document a narrow PHP relay.

The concurrency rule mirrors the proof-state rule: observable outcomes must not depend on a race.
Every source request starts together while Pyodide initializes, but each returns a success/failure
envelope. Only after all finish do we choose the earliest declared failure or mount every source in
the original list order. A network race may change elapsed time; it cannot change the displayed
error, installed module set, or proof semantics. Compression and caching similarly sit outside the
trusted base. The kernel sees the same imported Python and the same final certificate.

## 2026-07-27 — M15: saved text is not a theorem environment

The browser already had three histories, and none meant “the proof I can replay.” The terminal's
localStorage includes failed commands and unrelated sessions. The v1 trace intentionally preserves
failures and later-undone attempts for learning. `ProofState.history` is the exact rollback stack,
but it collapses a tactical to an internal combinator name, remembers only the visible alias of a
`use`, and expands top-level `auto` because each winning primitive is separately undoable. Classical
authority lives outside that state altogether. Treating any one of these as an export would produce
plausible-looking scripts that fail to reproduce the current branch.

M15 therefore gives the session owner a parallel, untrusted replay journal aligned with surviving
history steps. A successful explicit tactical keeps its accepted complete line; top-level `auto`
keeps the primitive sequence that `undo` actually sees; theorem imports retain lookup and alias
syntax; necessary classical-mode transitions are reconstructed from owner-held authority. Failure,
inspection, download, and undo commands do not become proof steps. Preview and download are pure
observers, and an active script omits `qed` even after the final goal closes.

The strongest label is deliberately delayed. Only after the existing independent checker accepts
the original theorem may the owner retain a `CHECKED QED` replay with a canonical final `qed`. The
download contains only that LF-terminated surface program. It is not a certificate, and it is not a
`TheoremSpec`: the checked library additionally needs a closed statement, reviewed earlier
dependencies, a compatible authored body, cut elimination, tests, and a source commit. Keeping this
boundary visible avoids quietly inventing a mutable theorem environment or a new trusted rule.

The frozen local M15 candidate passes 657 Peano tests and the sibling Lambda regression of 360
tests plus 36 subtests. The acceptance corpus produces 13,636 raw transitions and exports 13,631
unique rows; the deterministic evaluator runs all 32 kernel-judged attempts with the intentionally
weak random baseline at pass@8 `0.0`. The warning-free full book rebuild covers 25 sources, and its
executable gate replays 193 deep links plus 160 commands in 32 session blocks. The vault audit
resolves all 298 links across 58 notes and finds no concept without both an inbound and an outbound
edge. The application manifest stages as
`a-f2054080fdc5`, the checker remains 234 lines, and the trusted kernel directory is byte-unchanged.
No in-app browser was attached, so direct clicking and download observation are not claimed; the
worker protocol, direct-keyboard intent, payload validation, exact Blob bytes, and URL cleanup are
instead exercised by dependency-free browser-shell harnesses.

Commit `f40b2ad` was then pushed and the same content-addressed assembly published to staging as
build `2026-07-27j`. The live page, application manifest, worker, and proof UI match their local
bytes; WASM negotiates gzip. The delivery gate nevertheless stops at the inherited M14 boundary:
HTML still has no `Cache-Control: no-store`, and versioned responses still have no immutable cache
policy. That transport failure does not weaken a proof result, but it prevents production promotion.
Production was left untouched on build `2026-07-27h`; the new `script` surface is available only on
the staging channel until administrators supply the required headers.

## 2026-07-27 — Consecutive-product parity: proof size is not proof truth

For `forall n. exists x. n * (n + 1) = 2 * x`, the submitted `ring` proof produced a checked
963-node certificate. A copy-pasteable proof in the current tactic surface reached 343 nodes by
choosing the successor witness `S (x + n)`, orienting the base toward PA3--PA6, and doing the
remaining arithmetic by a nested induction. Replaying that route with experimental 23-, 50-, and
87-node certificates for its additive and multiplicative helper lemmas reached 252 nodes. That is a
checked library-optimization counterfactual, not the certificate currently produced by the shipped
browser tactics.

The more interesting improvement came from changing the mathematics. Instead of inducting directly
on the displayed product, a hand-authored experiment proves the recurrence-normal statement
`exists x. n * n + n = 2 * x`. Its induction hypothesis can be substituted into the step without
normalizing `n * (n + 1)` on every iteration. One final whole-proposition `EqSubst` converts the
existential theorem back to the original statement without opening and rebuilding its witness. The
result is a 180-node, depth-34, cut-normal certificate whose canonical rendering has 2,946
characters. The independent kernel accepts it against the original goal and rejects the same
certificate against a nearby mutated goal.

Two attractive alternatives explain why the final shape is less obvious than it looks. Keeping the
successor witness as `S (x + n)` makes the arithmetic finish 69 nodes instead of 65. Replacing
`2 * x` by `x + x` gives a clean additive invariant, but its checked conversion back to multiplication
depends on the existential witness and cannot be hoisted outside witness elimination; the complete
variant is 245 nodes. Failed proof shapes are useful data here, not failed mathematics.

Every number here is a structural `Proof`-tree count, not a measure of truth or readability. The
180-node result is the best checked upper bound found in this experiment, not a proof of global
minimality: terms and induction motives are annotations outside this node count, so a genuine lower
bound needs a precisely fixed search language and an exhaustive or formally verified argument. The
experiment supports optimizing checked library certificates and adding an untrusted post-tactic
compiler; it does not support a trusted arithmetic shortcut or any change to the kernel.

## 2026-07-28 — M16: a local lemma is scheduling, not authority

Adding `have h : P` exposed a constraint that a goal-list-only prover could easily hide. The
obvious natural-deduction term `(λh. body) proof` stores the body hole before the proof hole, while
the familiar `have` interaction asks the learner to prove `P` first. Peano Lab's goals are ordered
by the left-to-right holes in one partial certificate, so swapping only the visible list would make
`focus`, tacticals, and certificate splicing act on different obligations.

The design therefore records the two teaching schedules explicitly outside the trusted language.
`LocalHave(P, proof, body)` places the lemma goal first;
`LocalSuffices(P, body, proof)` places the continuation goal first. Both mean the same cut. They are
engine-only nodes, not additions to `kernel/proofs.py`, and their proposition field is not accepted
as a theorem annotation by the checker.

Finalization removes the scheduler by the existing capture-avoiding proof-hypothesis substitution.
That detail matters below nested implication, universal, and existential binders: inserting a
proof must shift both hypothesis indices and term variables instead of capturing whichever binder
happens to be nearest. Only the compiled ordinary certificate reaches the unchanged kernel, which
still receives the session owner's original theorem. Thus `have` and `suffices` can make an
arithmetic argument readable without making a local claim trusted.

The surface contract is intentionally small: the exact forms are `have h : P` and
`suffices h : P`; `h` must be fresh, and free term names in `P` must already belong to the focused
goal. Parsing and construction remain one immutable transaction, and undo restores the exact state
before either two-goal schedule.

The completed local candidate has 29 focused scheduling, capture, tactical, replay, failure, and
kernel-boundary tests. The full Peano suite reports 691 passed and the sibling Lambda suite reports
360 passed plus 36 subtests. A readable parity script using both commands reaches independently
checked QED and its certificate fails a mutated odd target. The source-bound corpus was regenerated
without changing its 13,344-transition/1,692-session semantics. The warning-as-error 25-source book,
193 deep links, 170 replayed commands, 318 links across 59 vault notes, manifests, and exact local
stage are green. The local immutable identity is `a-f6c33c7840ad`, build `2026-07-28a`; no in-app
browser was attached and no remote deployment was attempted. Production remains untouched behind
the separate M14 cache-header stop.
