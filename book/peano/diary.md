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

## 2026-07-28 — M17: a paste is a sequence, not a super-transaction

A saved proof is already a line-oriented replay program, but requiring a learner to paste every
line separately adds friction without teaching anything about proof. The browser surface therefore
has two routes into one operation: a visibly labeled, keyboard-operable multiline dialog
and detection of a multiline terminal paste. Neither route bypasses the existing driver or creates
a second proof-session owner.

The important design decision is failure semantics. Treating the whole paste as one atomic tactic
would make a late typo erase useful progress and would give `undo` a different meaning depending on
how commands were entered. M17 instead preflights only the script envelope and resource bounds,
then executes nonblank lines sequentially. A failure stops the suffix but retains each successful
prefix command as its ordinary undo transaction. This makes pasted and manually typed proofs meet
at the same state transition boundary.

The envelope is intentionally narrow: ignoring blank lines, a replay begins exactly with a
`pa prove ` line and ends with the exact line `qed`. It contains at most 256 nonblank lines and
100,000 characters, and no line may exceed the existing `MAX_INPUT`. Those checks happen before
execution, so a structurally incomplete or oversized paste cannot leave a half-created session.

Browser side effects need a separate rule from proof-state effects. The batch route never honors a
download request from `script download`; otherwise pasted text could cause a file write merely by
being inserted. QED is deliberately less special: it still travels through the normal session
owner to the unchanged independent checker and the original theorem.

The implementation follows that contract through one bounded parser and a structured worker result
that distinguishes success from final English output. Dependency-free event tests exercise direct
paste, dialog bounds and focus, sequential scheduling, interruption races, and download isolation;
the readable parity artifact reaches a normal independently checked QED through the same status
path. The complete gates report 698 Peano tests, 360 Lambda tests plus 36 subtests, a warning-as-error
25-source book, 193 deep links and 170 replayed commands, and a 60-note/335-link vault without an
unresolved or disconnected concept. Exact local staging is build `2026-07-28b`, application
`a-404fdbdb55e4`, vendor `v-85fb3352e49c`. The kernel is unchanged and its checker remains 234
lines. No in-app browser was attached, so a visual click-through is not claimed, and neither
production nor staging was deployed.

After the owner requested publication, the same exact staged tree was uploaded to
`/peano-lab-next/`. Its HTML identifies build `2026-07-28b` and application `a-404fdbdb55e4`; the
remote manifest, worker, and driver are byte-identical to the green local assembly. The mandatory
delivery verifier then stopped at its first HTTP policy check: the LOL-ng response contains no
`Cache-Control: no-store` for HTML, and the immutable worker response likewise has no
`Cache-Control`. Production was therefore not promoted and remains build `2026-07-27h`. This is the
same administrator-managed M14 header boundary, not a proof or paste implementation failure.

## 2026-07-28 — M18 design: compact arithmetic without compact trust

Replaying the recurrence-normal parity proof after `have` and `suffices` made the size problem
concrete. The source has only eighteen proof tactics, but its finalized ordinary certificate has
30,030 structural nodes. The partial tree grows from 35 to 18,651 at the first `ring` and from
18,654 to 30,016 at the second. Both certificates are sound; generic semiring normalization simply
pays for far more algebraic structure than this PA recurrence needs.

The earlier hand-authored experiment remains the useful counterexample. It proves
`exists x. n*n+n=2*x`, uses successor witness `x+S n`, substitutes the induction equality in the
recurrence-normal step, and transports the entire existential proposition to `n*(n+1)` only once.
Its 180-node, depth-34, cut-normal certificate is checked for the original theorem and rejected for
a nearby odd mutation. That number is a current checked upper bound, not a lower-bound theorem.

The M18 surface therefore stays narrower than the mathematical discovery. `compact_arith` closes
one rigid equality; `compact_arith [h, <- k]` makes exactly the listed equality hypotheses available
in exactly those orientations, while the selected proof may use a subset. It neither scans the rest of the context nor chooses an
outer induction invariant, witness, or logical proof structure. In the teaching replay the learner
must still write `have strong`, perform induction and existential elimination, choose `0` and
`x + S n`, list `IH_witness`, and prove the final bridge.

The phase-1 planner memoizes a finite seeded grammar rather than pretending to be a general shortest-
path solver. Its recurrence templates follow PA3--PA6's right-recursive definitions and are ordinary
induction certificates. Exact endpoint-bearing fragments compose by symmetry, transitivity,
congruence, and equality substitution. Fully quantified templates and parameter-specialized
induction instances are checked with an empty proof context before final use; the cut-normal
selected tree is checked in the focused context before publication; QED then checks the whole
original theorem again. The kernel gains no constructor or theorem environment.

Cost language needs the same discipline as proof language. The existing `proof_size` counts expanded
`Proof` occurrences but not term or motive annotations, and shared Python objects are still counted
at every tree occurrence. M18 may report the cheapest candidate in its explicitly finite grammar
and limits. It may not say “absolute minimum.” A genuine claim of that strength would require a fixed
finite costed language and an exhaustive or formally verified lower-bound argument.

Implementation verification is intentionally not recorded in this entry yet. Focused/full test
counts, the final readable-replay metric, browser observation, release identities, and publication
status belong here only after the engine and all project gates are green.

## 2026-07-28 — M18 implementation and adversarial review

The first implementation reproduced the 180-node certificate, but review found several places
where passing the kernel was not enough to satisfy the stronger engineering contract. Planner
candidates initially carried only proofs and costs; the binding design required exact endpoints.
The engine now represents each equality fragment with its left term, right term, and ordinary proof.
Typed constructors reject non-composing transitivity, mismatched congruence endpoints, and an
equality-substitution motive whose source does not match its body before a candidate reaches the
kernel. The final focused check and original-target QED check remain the actual soundness boundary.

Resource review found the same distinction between safety and a truthful user contract. The
256-node input limit had accidentally reset on each side of each equation; it now counts the goal
and all selected assumptions in one aggregate budget. One outer deadline now starts before live-
proof preflight, is shared with synthesis, and is checked again through hole replacement and
publication. Malformed proof nodes, terms, contexts, substitutions, clocks, and deliberately forged
states now produce final-English `TacticError` or `TacticLimit` results without publishing state.
These bugs could not create a false theorem because the kernel still rejected bad evidence, but
they mattered for determinism, transactionality, and the honesty of documented limits.

The public preview was refined at the same time. It says which explicitly permitted equations the
winning candidate actually used and reports expanded proof nodes, proof depth, annotation nodes,
and synthesis work. The real tactic reconstructs the candidate instead of reusing preview
authority. Tests pin that neither successful nor failed preview consumes a hole or metavariable ID.

The final focused suite reports 46 passes, including typed-composer attacks, empty-context template
checks, capture beneath implication/existential/universal binders, focus and `all_goals`, exact undo
and trace counts, malformed values, every resource path, and the exact readable replay. That replay
has 180 nodes, depth 34, and byte-identical canonical text. The complete Peano suite reports 744
passes; Lambda remains green at 360 tests plus 36 subtests. The warning-as-error book has 26 source
files, while its executable gate checks 193 deep links and 170 commands in 34 blocks. The connected
Obsidian vault has 61 notes and 356 resolved links. Corpus reproduction retains 13,344 unique
transitions from 1,692 checked sessions and now fingerprints all 31 semantic Python sources.

The exact local browser assembly is build `2026-07-28c`, application `a-953fa3777cd4`, with vendor
release `v-85fb3352e49c`. Static browser tests, worker concurrency, multiline paste, manifests, and
every staged application hash are green. No in-app browser was attached, so no live Pyodide click-
through is claimed. Nothing from M18 was deployed: staging remains M17 and production remains build
`2026-07-27h` until the administrator-managed M14 cache-header problem is resolved.

## 2026-07-28 — M18 staging publication

After explicit owner authorization, I published the same committed M18 assembly to
`/peano-lab-next/`. The release protocol first retained and uploaded the immutable application and
vendor namespaces, then changed the HTML pointer. Staging now identifies build `2026-07-28c`,
application `a-953fa3777cd4`, from commit `98ee0dd`. The fetched HTML has the same SHA-256 digest as
the local stage, and a checksum comparison found no changed byte among the 41 application files.
The worker-boot and multiline-paste behavioral harnesses also remain green.

The independent delivery verifier still stops on the known host configuration defect: HTML lacks
the required `Cache-Control: no-store` response header. That failure is evidence against promotion,
not evidence against the proof engine. No in-app browser was attached to this session, so I do not
claim a direct Pyodide click-through. Production was deliberately left untouched at build
`2026-07-27h`.

## 2026-07-28 — M19 design: make data quickly without making a second prover

The owner proposed a compact Peano Lab script for large-scale preparation and synthetic proof
generation. That is the right performance idea, with one dangerous interpretation: a compact
*implementation* of PA would create a second parser, tactic semantics, or checker and let training
success drift away from the browser theorem prover. I therefore made the new component a headless
adapter around the existing implementation. It imports Python once, starts one fresh
`ProofSession` per JSONL request, runs the public `run_surface` grammar, and calls the same
`checked_surface_final` path with an independently retained original theorem and logic mode.

Generation and verification are deliberately different names. `run_proof` keeps the binding v1
transition stream because search data without exact failures and state changes is not auditable.
`verify_proof` is the faster path for scripts that already exist; it omits transition rendering but
does not omit certificate construction or the final independent-kernel check. Raw trace records and
compact result envelopes are separate artifacts so the existing strict exporter never has to guess
which JSON object it is reading.

The first adversarial review found several ways a logically sound result could still become a
scientifically false record. A returned session could try to replace its theorem, logic mode, name
table, trace owner, or proof state. A forbidden theorem could hide in an unused tactical branch. A
mocked surface could execute `refl` while the request said `exact missing`, suppress a transition,
or append unrelated transitions. A finite profile containing `auto` could authorize the search
command without authorizing the primitive plan it replayed. None of these forged a theorem—the
kernel still checked the actual certificate—but each could poison action labels or benchmark
environment claims.

The adapter now keeps all authority in local owner values, checks every returned owner, compiles
command and theorem capabilities at every tactical leaf, fingerprints the complete command/theorem
environment, and binds every trace delta to the submitted command, focus, returned state, and
surviving history. Finite capability profiles exclude `auto` until its replay becomes
capability-aware. Trace records are append-only and exposed as detached copies. File output is
staged and published without overwrite only after a complete durable batch, so an empty, malformed,
fail-fast, or pre-commit interrupted run cannot leave a plausible final corpus.

This review also caught an efficiency mistake in the guard itself. Deep-copying the whole trace
before every tactic made a long session quadratic. Moving append-only ownership into `TraceLogger`
and checkpointing only its record count reduced a 1,000-command continued-failure example from
seconds to about 0.065 seconds with tracing (about 0.008 seconds in quiet verification) on this
machine. The exact numbers are a local microbenchmark, not a Helios throughput claim. An iterative
proof-node counter likewise prevents a long open certificate from crashing while writing its false
QED footer.

The training protocol keeps the model outside the trusted base. The primary artifact predicts one
next tactic from canonical goals and an exact capability hash. QED-only sessions must replay under
that declared environment before becoming positive labels, and connected genealogy,
canonical-formula, and exact-policy-prompt components split before transition rows. The first smoke
model is Qwen3-1.7B-Base; a controlled 4B comparison uses Qwen3-4B-Base and
Pythagoras-Prover-4B under the same data and LoRA budget. No model download, training job, or remote
mutation had been launched at the time of this entry; the headless boundary and its hostile tests
come first.

## 2026-07-28 — M19 documentation: write the threat model before the learning curve

The new policy-training chapter records the implemented headless, replay, prompt, dataset,
training-runtime, evaluator, provenance, and Helios contracts before any learned result exists.  In
particular, it preserves three design discoveries that would otherwise look like minor data-cleaning
details: an environment label is not its command/theorem authority, raw trace focus can leak a
goal-selection action, and alpha-equivalent kernel formulas still require an exact executable
surface binder trajectory.  Best-first search, expert iteration, Helios training, model comparisons,
and solve-rate claims remain explicitly pending until their own artifacts exist.

## 2026-07-28 — M19 data release: 10,000 rows must still prove where they came from

The proof-first generator now freezes the first training-scale policy artifact. Its 29 schemas span
logic, equality, PA recurrence, witnesses, and arithmetic. They produced 2,522 independent roots,
2,522 distinct canonical statements, and exactly 10,000 positive tactic transitions; all 2,522
sessions reached the original-target kernel check. The deterministic split is 8,149 train, 926
validation, and 925 test rows. The combined dataset SHA-256 is
`1fa98caa2e0528d39c1b9003c4ee153dfbe633cb1ee4505e8f5b28eb837465dd`.

Adversarial review showed that honest producer genealogy was not a sufficient split boundary.
Two records could claim unrelated families while proving the same formula; two different theorems
could also reach the same rendered model input. The compiler now joins family, lineage, exact
canonical theorem, and exact policy-prompt nodes into connected components before row expansion.
The attestor independently rejects any canonical formula or exact policy prompt shared by two
splits. The released data contain zero occurrences of the four frozen held-out targets.

The attestor does not accept the builder manifest as its own evidence. It verifies the raw trace,
metadata, compiler/source, environment, and held-out contracts, invokes the current compiler in a
fresh directory, and requires all three reconstructed split files to be byte-identical. Model
artifacts receive the same closed-world treatment: every loader-visible file beneath the separate
adapter and tokenizer directories must appear in the hash manifest, with no symlink, extra file, or
silent mutation. Trained evaluation reconstructs its authority from the dataset attestation in the
training manifest instead of selecting a hard-coded lookalike environment.

This closes the first scaled data and provenance gate, not the learning experiment. The catalog
still lacks induction/invariant schemas, negative preference rows, and natural-language pairs, and
the four-goal held-out set is a regression boundary rather than a statistically useful benchmark.
No model training or learned evaluation result is claimed yet.

## 2026-07-28 — M19 second audit: a true theorem can still make a false training row

The next hostile review found no route to a false QED, but it exposed an important distinction:
kernel soundness alone does not prove that a recorded action caused the recorded transition. A
forged surface could execute `refl`, label the trace `symm`, and still return a certificate for a
true reflexive goal. The adapter now binds each success simultaneously to the submitted line, the
returned replay journal, the engine's outer transaction, proof-history prefix, goal transition, and
trace label. A failure record must carry the exact sanitized diagnostic raised by the tactic.
Open-result goals reuse the trace's proof-wide metavariable aliases rather than starting a fresh
printer namespace.

The transport audit found a different class of honesty bugs. Python's default JSON decoder would
construct a huge integer before request-schema validation and would turn `1e9999` into infinity.
The decoder now bounds integer spelling and rejects every JSON float. The CLI is described and
implemented as a finite transaction, not a streaming duplex service: it has aggregate input,
request, result, and trace ceilings; withholds rows until EOF and trace commit; exposes
`--require-proved` for CI; preserves `KeyboardInterrupt`/`SystemExit`; and treats a successful hard
link as the trace commit point. Directory entries are synced and staging cleanup happens after
matching results may be published. These are not new proof rules, but they make the scientific and
operational record say exactly what happened.

## 2026-07-28 — M19 final preflight: make the fast path boring at its boundaries

A final parity audit concentrated on syntax that a normal proof author would rarely type but a
model eventually will. Redundant grouping around top-level `auto` originally took a different
dispatcher path from `auto`, so its trace/history invariant rejected a browser-valid command.
Malformed grouping could also raise while the classifier was deciding whether a command was
`auto`, before the traced dispatcher had emitted its transactional error. The classifier now
removes redundant outer groups, treats grouped `auto` as the same primitive-plan replay, and is
total on malformed input. A small exhaustive probe over 72 grouped variants found identical traced
and quiet statuses, errors, and engine histories.

Two string-boundary bugs carried the same lesson. Python's `str.isdigit()` recognizes characters
such as superscript and circled digits that `int()` does not parse, so trace canonicalization now
guards conversion and preserves an ordinary tactic error. Capability labels are restricted to a
small ASCII token alphabet because an unescaped label is embedded in the repository-owned prompt
environment; punctuation such as `</env>` must never be able to manufacture prompt structure.
Neither issue could make the kernel accept a false theorem, but both could make training and quiet
verification disagree.

The transport contract now names the hard link as its exact commit point. Cancellation before it
removes the hidden stage and publishes no final trace. Cancellation after it may leave the complete,
data-fsynced trace while redirected stdout is absent or partial; callers that require an atomic
result filename use their own temporary output and rename after process success. A regression
injects interruption immediately after the link and verifies that only a complete QED trace remains,
with no hidden staging alias.

The Helios preflight was tightened before any GPU job was allowed. Training manifests now join the
source-sync record, exact Slurm script, scheduler job and submission-ledger row, dependency, module
stack, package inventory, requirements hash, and accelerator identity. Evaluation hashes its model
decoder, evaluator, public surface, library, and kernel sources. The preparation job performs an
actual BF16 LoRA forward/backward/AdamW update, saves and hashes adapter/tokenizer artifacts, reloads
them, and runs another forward pass. Training and evaluation submissions require explicit
`afterok` dependencies, and sampled `k=4` really uses four seeded samples. These gates cost a little
setup time and save much more expensive ambiguity after a cluster result exists.

The frozen local gate now reports 363 focused M19 tests and 912 complete Peano tests; Lambda Lab
reports 360 tests plus 36 subtests, and the book/command replay gates are clean. The scaled dataset
attestor independently rebuilt 8,149/926/925 rows with aggregate SHA-256
`1fa98caa2e0528d39c1b9003c4ee153dfbe633cb1ee4505e8f5b28eb837465dd`. These are pre-training
facts only: at this point no model result or Helios job outcome is claimed.

## 2026-07-28 — M19 first Helios failure: a bundle can expose a wheel without importing it

The first real preparation job, `20029189`, failed after 21 seconds and before model loading.  The
failure was useful and cheap: importing Torch from the new virtual environment raised
`ModuleNotFoundError`.  Dependency safety then left training job `20029217` and evaluation job
`20029237` pending rather than consuming a GPU; both stale jobs were canceled explicitly.

The original environment comment was wrong.  `ML-bundle/25.10` loads the CUDA 12.9.1 stack and
sets `PIP_FIND_LINKS` to a reviewed ARM wheel directory, but it does not install a Torch Python
distribution.  That directory contains `torch-2.9.1+cu129` for CPython 3.13/aarch64.  The fix is
not to weaken the smoke or borrow unknown system site packages.  Preparation now recreates an
isolated venv, installs that exact wheel plus an explicit pinned transitive closure with binary-only
and no-dependency-resolution flags, and requires `pip check` before downloading the model or
running the BF16 LoRA forward/backward/save/reload test.  The standalone GPU smoke uses the same
prepared venv and cannot be submitted as a real job without an `afterok` dependency.  A final
review also caught inherited `PYTHONPATH` as a route around venv isolation; scheduled jobs now set
only the reviewed repository paths, disable the user site, and assert the exact Torch/CUDA build.
The requirements and resolved runtime inventory pin `pip` and `setuptools` too.  This is a
version-pinned environment, not yet a claim that every downloaded wheel byte is bound by
`--require-hashes`; that remaining supply-chain refinement must not be described as bit-for-bit
environment reproduction.

The corrected preflight gate reports 41 focused Helios/runtime/data tests, 912 complete Peano
tests, and 360 Lambda tests plus 36 subtests.  The warning-as-error 27-source book and all 193 deep
links / 34 sessions / 170 commands are green.  Independent dataset replay preserved the exact
8,149/926/925 split hashes and aggregate digest while refreshing the attestation to SHA-256
`5a3b172627d15a1f5dfa303c3acdcf02e9673039a239385ef8c5d8d57b238e0a` for the new runtime-source
inventory.  These are corrected preflight facts, not a successful model smoke.

## 2026-07-28 — M19 cluster portability: a second GPU site is a new experiment boundary

The corrected Helios preparation finally passed. Job `20029964` did more than import Torch: it
matched the exact Qwen revision, ran a BF16 LoRA optimizer step, saved and hashed the adapter and
tokenizer, reloaded them, and produced another finite loss. This proves the environment/save path,
not the policy's mathematical ability; the registered training and evaluator are still pending.

When VPN access to WMI returned, the tempting shortcut was to call any NVIDIA node equivalent and
copy the Helios virtual environment. Live inspection showed why that would be false provenance.
WMI's A100 node is x86-64, while Helios's GH200 is aarch64; WMI supplies PyTorch 2.5.1/CUDA 12.4 in
a central Conda environment, while Helios uses the pinned 2.9.1/CUDA-12.9 ARM wheel closure.

The first WMI artifact is therefore only a five-minute, typed-A100, read-only probe. It verifies one
visible 80GB A100, BF16 matrix forward/backward, exact central Torch/CUDA versions, modules,
storage, and public package/model reachability. Only a passing report licenses a separate Peano
overlay and full LoRA save/reload smoke. Cluster portability means reproducing the boundary with
new evidence, not relabeling old evidence.

The first execution, job `171366`, demonstrated another small portability boundary. It acquired
the intended A100, then the central Conda environment's MKL activation hook read
`MKL_INTERFACE_LAYER` without guarding the unset case. Our strict `set -u` correctly made that an
error. The fix does not weaken the probe body: it disables `nounset` only while executing the
administrator-owned Conda activation hooks and restores it before any Peano assertion. The job
failed after nine seconds and installed nothing.

## 2026-07-28 — M19 WMI preflight: reproducibility starts before `Trainer`

Corrected probe job `171369` passed in thirteen seconds on one A100-SXM4-80GB. It saw Python
3.12.12, PyTorch 2.5.1 with CUDA 12.4, driver 610.43.02, BF16 support, one CUDA-visible device,
and a finite backward pass. That licensed construction of the WMI environment; it did not license
training.

The central Conda environment is read-only but not ours, so naming it is not enough provenance. We
recorded a canonical base manifest covering Python, `ensurepip`, the numeric stack, and every
central package delegated by the overlay. Live preparation must reproduce all versions and prove
their metadata resolves under the fixed central prefix. The overlay then adds exactly twelve
hash-pinned x86-64 wheels under a content-addressed virtual-environment release. Its identity is the
hash of both contracts. A pointer whose identity no longer matches the live reviewed base is an
error, not an invitation to reuse yesterday's environment.

Two audits changed the control design before submission. First, direct `rsync` into a live root
could leave mixed source with stale provenance after interruption. Sync now streams only a clean
`git archive`, reconstructs its Git tree remotely, takes an exclusive deployment lock, invalidates
provenance, and publishes only after verification. Every source-dependent WMI model job holds the
matching shared lock.
Second, preparation used to move the environment pointer before the expensive LoRA smoke. The
pointer now moves last; a newly created release is removed if package, data, accelerator,
save/reload, or loss validation fails.

Torch 2.5.1 also sharpens the serialization boundary. Transformers 4.53.3 refuses unsafe optimizer
state loading below Torch 2.6, so the pilot is deliberately one-shot and cannot resume. It refuses
any pre-existing output before data attestation, forces safetensors for base loading and Trainer
weights, and rejects PEFT's `adapter_model.bin` pickle fallback even when file hashes match. The
final adapter bypasses `Trainer.save_model`, because that method unconditionally writes a
`training_args.bin` pickle beside otherwise safe weights. This is stricter than merely “do not
resume”: a failed attempt must be archived or assigned a new run identity before another launch.
The local WMI/runtime/training gate reports 96 passes; the full A100 LoRA save/reload gate is still
pending and no learned result is claimed.

## 2026-07-28 — M19 usability: proving a new theorem is another authority boundary

The evaluator originally knew how to run any `EvalGoal`, but its trained-model command exposed only
four frozen benchmark names. That was scientifically adequate and pedagogically frustrating: a
student could train a policy yet could not simply ask it to try a new theorem. The small-looking
`--theorem` flag forced us to decide which parts of a proof request belong to the caller and which
belong to the experiment.

The caller owns only the formula and a bounded search budget. Logic mode, tactic grammar, and
importable theorems come from the adapter's independently replayed training attestation. Version 1
therefore cannot be widened beyond intuitionistic `model-v1`, even by a command-line option. The
formula is checked before loading model weights: one control-free line, at most 4,000 characters,
bounded numerals and structural recursion markers, successful parse, and no free names. We retain
the raw original statement for evaluator ownership. The printer's canonical rendering is parsed
again and required to produce the same AST before it can become downloadable source. This makes the
original-goal law explicit instead of assuming that parser/printer round trips are harmless.

A model success flag is still not a proof artifact. Every rollout first closes through the ordinary
surface and independent original-target kernel check. The publisher chooses the least proof nodes,
then tactic lines, then sample index, and replays those tactics from a fresh state with exactly the
same capability object. It compares canonical theorem, environment hash, applied command count,
failure count, and proof nodes. Only the second kernel-checked QED produces a `.pa` script. The JSON
report contains that complete script and its SHA-256, so the optional file is a convenience copy,
not an unrecorded authority.

Arbitrary input also turns vague resource settings into a denial-of-service interface. Separate
maxima for samples, steps, and generated tokens multiplied into hundreds of millions of tokens, so
the command now bounds both total model calls and their token product. It rejects non-finite decode
floats, validates explicit mistakes and unknown benchmark names before model loading, rechecks the
exact manifest bytes plus closed adapter/tokenizer trees after evaluation and replay, and confines
repository-local output to `results/`. Nested aliases cannot turn an output filename into another
output's directory or corrupt source/model inputs.

Finally, a bare Python example was not enough on WMI. Login Python is not the accepted GPU runtime,
and an ad-hoc allocation has no submission-ledger identity. The supported wrapper therefore sends
the theorem as canonical JSON data under the deployment lock. A fresh nonce makes the request
unique; its complete SHA-256 ID is the only value exported through Slurm. Before releasing the held
A100 job, the controller records the job/request/hash association alongside the ordinary source
ledger. The compute job repeats runtime, request, adapter, evaluator, and kernel checks, then writes
digest-named report, optional proof, and terminal summary. `No proof found` is an honest completed
search result; missing provenance is a failed job.

The new path has 139 focused policy/request/WMI/runtime tests, and the complete Peano suite reports
1,029 passes. It makes a future trained adapter usable; it does not claim that the pending adapter
has learned to solve anything. That distinction is exactly the lesson: language models suggest
tactics, execution constructs certificates, the kernel proves the theorem, and provenance tells us
which model actually made the suggestion.

## 2026-07-28 — The first full WMI preparation found a shell boundary, not a model result

Clean commit `0ad12bc` reached WMI as a reconstructed and hash-checked Git tree. Preparation job
`171391` acquired the requested A100, but stopped after twelve seconds—before installing the
overlay, loading Qwen, or training. A constant naming the administrator-owned central Conda prefix
was deliberately readonly. Two Python verifier calls also used that same name for a temporary
command environment assignment. Bash rejects assignments to readonly variables even when the new
value is identical, so the first verifier received no exported prefix and failed closed.

The repair keeps the authoritative constant readonly and exports its value under a distinct,
purpose-specific child name. Both Python verifiers consume the child name; neither can alter the
shell constant. A regression executes both call shapes under `set -euo pipefail`, rather than only
searching their source text. The focused gate now reports 139 passes and the complete Peano suite
1,029. This is exactly why preparation is a separate milestone: it turns cluster-specific shell
semantics into a small reproducible failure before any expensive or scientifically meaningful run.

## 2026-07-28 — Empty fields are still fields

Replacement preparation job `171395` passed in 8m39s. It independently replayed the exact
8,149/926/925 dataset split and digest `1fa98caa…`, verified Python 3.12.12, Torch 2.5.1/CUDA 12.4,
driver 610.43.02, and one A100-SXM4-80GB, then exercised a 3,211,264-parameter LoRA adapter. The
training loss was 6.06434; after safetensors save and reload, the measured loss was 5.53506. Only
after all of this did preparation publish the content-addressed environment pointer.

The training scheduler preflight passed, but the guarded real submission correctly refused to
call `sbatch`: it could not match `171395` to the current provenance chain. The ledger bytes and
composite script/helper hash were right. The bug was more prosaic and more instructive: Bash treats
a tab in `IFS` as whitespace, so consecutive tabs collapse. The intentionally empty
`dependency_job_id` column vanished during `read`, and every later field shifted left.

The controller now uses a small strict parser for this data boundary. It bounds total bytes and
field lengths, requires complete UTF-8 with no carriage returns or NULs, requires exactly nine TSV
columns, preserves the empty column, validates field shapes, rejects duplicate job IDs, and matches
script, worktree, commit, cleanliness, sync time, and composite hash. A regression starts with the
literal empty-column shape that failed remotely. The focused gate reports 140 passes and the full
Peano suite 1,030.

There is one deliberately inconvenient consequence. Fixing the controller changes the source
commit and sync timestamp, so the passed `171395` report cannot become the predecessor of a job
submitted from the fix. Weakening that comparison would erase the provenance guarantee precisely
when it became useful. We instead run a fresh preparation and preserve `171395` as honest evidence
for the earlier source.

## 2026-07-28 — A low validation loss is not a proved theorem

While the WMI controller work was underway, the older Helios dependency chain left the queue.
Training job `20029970` completed 100 steps in 9m51s on a GH200. Its immutable manifest records
2,048 training examples, 256 validation examples, train loss 0.78446, and final teacher-forced
validation loss 0.13518. The step logs fell from losses near 4.9 to roughly 0.1–0.16. This is
encouraging evidence that a 1.7B model can fit our next-tactic language cheaply. It is not evidence
that it can finish a previously unseen proof: teacher forcing scores the next token while a proof
requires a long sequence of valid state-dependent choices.

The dependent evaluator `20029980` failed after three seconds, before loading the adapter or
generating a tactic. The reason was a representation mismatch hiding in plain sight. Policy dataset
rows deliberately preserve construction order, and their parser rejects reordered capability
fields. Training manifests are canonical JSON written with `sort_keys=True`, so the same nested
mapping is necessarily read back in lexical order. Reusing the row parser for the manifest made
every honestly written adapter unevaluable.

The fix does not make capabilities order-insensitive everywhere. At the manifest boundary it first
requires exactly `label`, `allowed_commands`, and `allowed_theorems`, reconstructs that semantic
record in the row parser's expected order, and then performs the existing sorted-value,
no-duplicates, environment-preimage/hash, and exact `model-v1` checks. Raw dataset rows remain
strictly ordered. A regression round-trips the environment through the actual sorted JSON shape
that failed on Helios.

The old Helios adapter also predates the present safetensors-only closed-directory rule and contains
Trainer's `training_args.bin`; we will not weaken the current loader or silently delete that file to
manufacture a result. WMI preparation `171404` was canceled after 1m56s when the manifest bug was
found. The honest next step is a fresh same-source run that produces the current safe artifact and
then reaches kernel-judged evaluation. Until then the answer to “does it prove PA well?” is: we have
promising imitation loss, but no measured proof success.

Because `contract.py` belongs to the attestor's recorded source set, even this representation-only
fix invalidated the old attestor digest. A fresh CPython-3.10 independent replay reproduced the
same 10,000 rows, 8,149/926/925 split hashes, raw source artifacts, environment, holdout contract,
and dataset digest. Only the `contract.py` hash and aggregate attestor-source hash changed; the new
canonical attestation file has SHA-256 `e4b319a0be94b4f0ec6584ddbcc1e9386104b249d660bc8d033d757ab11c66f8`.

## 2026-07-28 — The first trained-policy result is a curriculum map, not a victory banner

The corrected WMI chain finally separated infrastructure success from mathematical success.
Preparation `171414` passed in 7m28s from exact commit `0c84fc3`; training `171421` completed 100
steps in 11m40s; evaluator `171423` completed normally. The training manifest binds dataset
`1fa98caa…`, adapter `ff187542…`, and itself as `ad16e60d…`. Train loss 0.78301 and validation
loss 0.13615 look excellent. The theorem result does not: all sixteen sampled trajectories failed,
so the four frozen goals scored pass@4 0.0.

That discrepancy is pedagogically better than an ambiguous partial success. The validation rows
are shallow interpolation within familiar schemas. Training consumed 1,600 effective examples,
0.78125 of the selected 2,048. The full train split has no induction-hypothesis state, no use of any
allowed foundation lemma, and no action headed by `assumption`, `exfalso`, `forall_elim`, `have`,
`induction`, `simp`, `specialize`, `suffices`, or `use`. All source proofs are one to seven lines.
The observed behavior lies squarely inside that support: after a universal existential goal the
adapter introduced the variable, and all 513 comparable training states label the next action with
an immediate witness. Whether fine-tuning caused that behavior still requires an unadapted-base
comparison.

On the parity theorem this became a vivid failure. Fifteen of sixteen runs proposed
`(n * (n + 1)) / 2`: mathematically suggestive, syntactically outside PA, and structurally unable to
replace induction. By contrast, a fresh direct-witness theorem absent exactly from all dataset
splits succeeded once in eight samples. Its ordinary four-line script replayed to a seven-node
kernel-checked certificate. The honest claim is neither “the adapter emitted nothing useful” nor
“the adapter proves PA”. One success is consistent with within-template learning, but causal
attribution awaits the pretrained-base baseline; the missing planning frontier plainly remains.

The evaluator is already state-conditional: after every successful tactic it renders the new
canonical state and asks again. But a rollout dies on its first failed tactic. It has no same-state
retry, frontier, or backtracking. The next search layer should sample several complete tactic lines,
execute each transactionally, discard failures, deduplicate successor states, and preserve siblings
under explicit token/model-call/state/kernel budgets. That is where Peano's immutable state and
cheap checker become algorithmic assets rather than only safety guards.

The frozen benchmark exposed its own useful flaw. Known checked model-v1 routes require
10/10/23/13 actions, while the registered budget was 16. The score remains correct for the declared
budget, but `le_total` lacks a known route that fits it. Model-v2 must use at least 24 steps and test
budget adequacy by replaying reference scripts before spending GPU time.

## 2026-07-28 — An external lemma pack exposes a new visibility boundary

The owner supplied a separately maintained candidate theorem library. Reading its integration
contract before copying anything was essential. Its private compatibility gate passed against the
current checkout, including deterministic replay, empty-context kernel checks, and bounded import
tests. This public diary intentionally records neither its identifiers nor its detailed validation
profile until the owner chooses a visibility boundary. No kernel or proof-rule change was made.

Such a library can address several missing data modes at once: induction, `simp`, `specialize`, named
local facts, existential witnesses, long proofs, and multi-lemma composition. But theorem names
alone are not enough. Model-v1's capability hash binds a list of names, while the prompt shows only
that opaque hash; it does not bind or reveal the lemmas' statements and certificates. Model-v2
therefore needs a first-class library snapshot containing stable name, canonical formula,
dependencies, source commit, authored-script hash, final certificate hash, nodes, and depth. That
snapshot hash must enter every prompt, dataset row, attestation, training manifest, evaluator
report, and WMI request.

There is also a clean distinction between utility and evaluation. Once an exact capstone theorem is
importable, a short `use`/`apply`/`exact` closure is a successful library-retrieval/application
exercise, not evidence that the model discovered the underlying proof. A sealed test set must use
different root families and must never enter training, retrieval, or tuning. Because the source pack
is non-public while Peano Lab is public, neither its catalog nor identifying metadata enters this
commit. That boundary requires an explicit integration decision.

The result-recording gate then passed without changing the kernel: 1,033 Peano tests, Lambda's 360
tests plus 36 subtests, a clean warning-as-error build of all 27 book sources, replay of 193 deep
links and 170 session commands, and resolution of all 412 wikilinks in the 66-note Obsidian vault.
`checker.py` remains 234 lines. These checks preserve a small positive result and the larger negative
one with equal care; neither a low loss nor a non-public theorem name is allowed to substitute for a
checked public experiment.

## 2026-07-28 — Publication turns a private candidate into public theorem data

The owner chose the public visibility boundary. I imported the 26 records exactly from source
commit `d2ba05dca952e2e33479923433f8d2fcd3409493` and retained catalog hash
`91c88c1f3311cc0dc540671b169c270758ff6211e77716ed07bd3dd4f55c8380`, the original validation
report, and its exact MIT notice. A field-by-field audit found no name, case-folding, statement, or
dependency-order collision with the 23 existing entries.

The kernel did not change. The only resource change is the untrusted live-`use` certificate limit,
4,096 to 32,768 nodes. That admits the 21,515-node/depth-66 capstone while the separate 32,768-node
live-partial limit still rejects two simultaneous imports. Cold replay reconstructs all 26 proof
trees twice, matches their source hashes and metrics, checks each in the empty context, and rejects
a mutated capstone target. The short user proof reaches 21,523 temporary nodes/depth 69 before cut
normalization returns the original 21,515-node certificate for QED.

Publication also changes the scientific interpretation. The exact fourth-power theorem is now a
retrieval/application exercise, not a novel-discovery benchmark. Model-v1 remains frozen and cannot
see the new entries. Model-v2 must bind a new content-addressed 49-theorem snapshot and seal other
families before generating training data.

## 2026-07-28 — The failed policy run was trained for a different task

A quantitative audit explains the 0/4 result without blaming parameter count. The optimizer saw
1,600 examples, only 19.6% of the 8,149-row train split. That split covers 16/25 tactic heads, no
induction-hypothesis or order states, no foundation-lemma use, and only 1--7-step scripts. Every
validation template also occurs in training, whereas the benchmark reference paths take 10--23
actions and require missing decisions. The low token loss therefore measures template imitation.

Across 40 reported attempts, 24 ended on grammar/surface incompatibilities such as division,
subtraction, unavailable commands or tactics, or malformed arity. The prompt exposes neither PA grammar nor
lemma statements, and a rollout dies at its first rejected action. An explicit-import full-surface
audit of the public catalog yields 474 prospective model-v2 transitions, but only one `induction`
label; under the old sampler it would have about an 18.6% chance of being seen. The next honest
experiment is balanced model-v2 data,
grammar-grounded retrieval, a pretrained-base comparison, and bounded best-first search. A 4B
scale-up comes only after those corrections.

The local publication gate reports 1,036 Peano tests, Lambda's 360 tests plus 36 subtests, a clean
warning-as-error build of all 27 book sources, replay of 193 deep links and 170 commands, and 414
resolved wikilinks across 67 vault notes. The browser assembly is
`2026-07-28g`/`a-3ea7b7142aa0`; automated worker boot passes. No in-app browser was attached, so
direct Pyodide latency for the capstone remains an explicit unclaimed check. The independent kernel
file has no diff and remains 234 lines.

The old acceptance-data command also taught a scaling lesson. Its default depth-five, 5,000-node
`auto` sweep over every ladder statement became impractical on the long modular formulas, so I
stopped that optional `/tmp` run rather than confuse search cost with theorem admission. The smoke
now isolates the ladder: one-node/depth-one `auto` plumbing attempts plus every complete authored
script, while the release corpus separately covers generated variants. It finishes with 803 unique
transitions in 98 sessions and 49 kernel-checked QEDs.

## 2026-07-28 — Model-v2 is an overnight systems experiment, not a longer smoke run

The first temptation was simply to turn 100 optimizer steps into several thousand. The failure
audit rules that out: repeating the old 29 shallow schemas would make the loss curve prettier while
leaving induction, library selection, and recovery outside the training distribution. The new run
therefore gets a new authority and artifact identity. Its 49-theorem public snapshot seals the four
evaluation targets, shows an explicit complete-line tactic grammar, and retrieves at most eight
permitted `name : statement` records deterministically. Model-v1 remains loadable as the negative
baseline.

The curriculum target is 100,000 independently replayed positive transitions in three explicit
lanes: 50% foundational state/action work, 25% induction/IH work, and 25% checked-library retrieval
and composition. The proportions are properties of transition rows, not merely theorem counts.
Previously unseen heads such as `assumption`, `exfalso`, `forall_elim`, `have`, `specialize`,
`suffices`, and `use` must occur in actual successful public-surface traces. Every session still
ends at the original formula through the independent kernel; generated volume grants no new trust.

The overnight optimizer is deliberately conservative: pinned Qwen3-1.7B-Base, BF16 SDPA, rank-16
LoRA on attention and MLP projections, three epochs, effective batch 32, cosine decay, and a 2,048
token refusal boundary. WMI's measured A100 run suggests roughly 9--13 hours, while Helios offers a
larger currently available GH200 pool. Separate guarded prepare/train/evaluate chains reserve 20
hours on either system. Preparation regenerates and attests all 100,000 rows before the GPU smoke;
the training job cannot silently consume the old v1 dataset.

The second systems correction is decoding. A theorem prover should not discard the whole attempt
because one sampled line fails transactionally. The intended interface keeps the model untrusted,
executes several candidate lines through the real surface, deduplicates surviving proof states,
and explores a bounded frontier to depth 32. Only an independently replayed QED is publishable.
This turns Peano Lab's transactional states and cheap kernel from passive safeguards into the
search algorithm's verifier.

Before this work began, the public branch's Python-3.12.13 CI failure was also closed. A lexical
JSON scanner now bounds container nesting at 256 while respecting quoted brackets and escapes; an
iterative structural check enforces the same bound before request hashing. The complete local Peano
suite passed with 1,038 tests, Lambda passed 360 tests plus 36 subtests, and GitHub Actions run 62
completed successfully. The public catalog and its soundness tests are therefore green before any
new training artifact is introduced.

## 2026-07-28 — A prompt hash and a training-authority hash answer different questions

The first model-v2 draft hashed the 45 displayed theorem names and statements. That was enough to
make prompt retrieval deterministic, but not enough to identify the experiment: a proof script,
dependency edge, or expanded certificate could change while the visible prompt stayed identical.
The replacement identity replays every permitted theorem, checks its closed certificate again, and
hashes its canonical statement, dependencies, source-spec and script digests, certificate digest,
node count, and depth. Its current digest is
`a6c13cdc36115f8407d4932b22f022d0c3c012d8a64cbe41c1f0a158006ced5c`.

A second audit found that merely putting this digest in the generated source manifest was still
insufficient. The dataset compiler consumes raw traces plus per-session metadata, not that source
manifest, so a later library with the same names could have laundered the origin of otherwise valid
rows. Model-v2 metadata and every compiled row now carry the full identity; builder, loader, and
independent attestor all reject a missing or different value. Their source inventories include the
prompt contract, identity implementation, and retained modular-library validation report. Sealing
also rejects a renamed copy of a held-out formula or any permitted theorem whose dependency escapes
the allowed authority.

This does not add a proof rule. A stale row would still fail or prove a true theorem under the
current kernel. The correction protects the scientific statement “which library trained this
policy?” The smaller name/statement projection remains useful model input; the full checked identity
is the authority. Keeping those roles separate makes the prompt compact without making provenance
vague.
