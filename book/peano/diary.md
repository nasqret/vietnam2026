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
- A GPT Pro adversarial review found that Python subclasses could override an AST node's equality and fool
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

## 2026-07-29 — Conditional beta coprimality reaches a checked finite-bound checkpoint

The native runtime now has 176 unique checked theorems: 23 baseline entries,
141 post-baseline foundational entries, and twelve unique modular capstones.
The 183-node research catalog classifies the same authority as 23
`checked_existing`, 153 `checked_m20`, three `planned_expressible`, and four
`blocked_by_language` records. Its ordered snapshot root is
`874779f25de06cebc9d111e76bd183e4a8c514bd0d9da0c52f71c99f887cc3a7`.

Six new certificates make the beta-modulus claim precise instead of stronger
than the arithmetic permits:

| Checked theorem | Nodes/depth | Cuts |
|---|---:|---:|
| `beta_modulus_coprime_base` | 874 / 30 | 24 |
| `common_divisor_beta_moduli_divides_gap_times_c` | 855 / 30 | 24 |
| `beta_moduli_coprime_of_gap_dvd` | 6,007 / 56 | 175 |
| `binary_crt_beta_pair_of_gap_dvd` | 12,980 / 71 | 378 |
| `bounded_common_multiple_step` | 483 / 29 | 15 |
| `bounded_common_multiple_exists` | 640 / 30 | 22 |

Unconditional pairwise coprimality is false: with $c=1$, the beta family
contains $M(1,1)=3$ and $M(1,4)=6$. The checked theorem instead assumes
$j=i+\mathit{gap}$ and $\mathit{gap}\mid c$. A common divisor of the two
moduli divides $\mathit{gap}\,c$; coprimality with the base and Gauss
cancellation reduce it to the gap, and the gap's divisibility into $c$ forces
the divisor to one. The CRT wrapper then realizes two bounded beta values in
one code. Separately, bounded-common-multiple induction constructs a nonzero
$c$ divisible by every positive natural at most $B$.

The complete snapshot has 120,976 structural nodes, 3,331 self-contained
Cuts, and 136 Cut-bearing certificates. The largest certificate is
`binary_crt_beta_pair_of_gap_dvd` at 12,980 nodes, 378 Cuts, and depth 71;
the overall depth maximum remains 80. At that checkpoint the open boundary was:
index-bound finite-prefix glue, product-modulus CRT iteration, prefix-product
traces, factorization existence and uniqueness, and native FTA were open.

The synchronized local browser candidate keeps build `2026-07-29e` and now
has application identity `a-72e034c621a7`; it has not been deployed. The
source-bound corpus fingerprint is
`f44b6eb716116063bd24b849d737345f0c9c23240fa8536d1ed25fdc1ae05d56`.
Its isolated smoke records 352 sessions, 4,729 raw transitions, 4,726 unique
transitions, and all 176 authored QEDs. The full Peano suite passes 1,098
tests in 114.26 seconds, and Lambda remains green at 360 tests plus 36
subtests.

## 2026-07-29 — Bounded-prefix coprimality and CRT fold algebra are checked

The next native checkpoint contains 183 unique checked theorems: 23 baseline
entries, 148 post-baseline foundational entries, and twelve modular capstones.
The 190-node research catalog classifies them as 23 `checked_existing`, 160
`checked_m20`, three `planned_expressible`, and four `blocked_by_language`
records. Its ordered snapshot root is
`09359430226349a7d5fdd1fd67376d345bc1bb5f707e746e8b58c2799086f2d6`.

Seven new certificates close the algebra surrounding a future bounded CRT
fold:

| Checked theorem | Nodes/depth | Cuts |
|---|---:|---:|
| `beta_moduli_coprime_of_lt_bounded_common_multiple` | 6,227 / 57 | 181 |
| `beta_moduli_pairwise_coprime_bounded` | 6,348 / 59 | 183 |
| `bounded_beta_moduli_pairwise_coprime_exists` | 7,019 / 61 | 207 |
| `coprime_mul_left` | 3,975 / 53 | 115 |
| `coprime_mul_right` | 4,017 / 54 | 117 |
| `mod_eq_of_mod_eq_multiple` | 157 / 23 | 3 |
| `binary_crt_fold_step` | 5,501 / 52 | 156 |

The first three turn the bounded common-multiple resource into pairwise
coprimality for every two distinct beta moduli in the bounded prefix. The next
two show that coprimality with a fixed modulus is preserved by accumulated
products. `mod_eq_of_mod_eq_multiple` descends balanced congruence from an
accumulated product modulus to each divisor modulus. Finally,
`binary_crt_fold_step` constructs the next CRT value and proves a universal
preservation invariant: every congruence already held modulo a divisor of the
old product is retained, while the requested congruence at the new modulus is
added.

This was fold algebra, not yet the bounded fold itself. At that checkpoint the library lacked an
encoded accumulated-product trace and the induction that carries its
nonzero, divisor-membership, and coprimality invariants through a finite
prefix. Beta finite-prefix recoding, prefix-product traces, factorization
existence and uniqueness, and native FTA therefore remain open.

The complete snapshot has 154,220 structural nodes, 4,293 self-contained
Cuts, and 143 Cut-bearing certificates. The maximum remains
`binary_crt_beta_pair_of_gap_dvd` at 12,980 nodes and 378 Cuts; the overall
depth maximum remains 80. The synchronized, undeployed local browser candidate
is build `g`, application `a-6b72d4fe4ca4`. Its source-bound corpus fingerprint
is `d0649a05ab1a88396d2d3046bc10a814e374cb3cf5ad8df225c9e15e91ff0df6`;
the isolated smoke records 366 sessions, 4,992 raw transitions, 4,989 unique
transitions, and all 183 authored QEDs. The full Peano suite passes 1,098 tests
in 127.22 seconds, and Lambda remains green at 360 tests plus 36 subtests.

## 2026-07-29 — The bounded existing-code beta CRT prefix invariant is checked

The current native checkpoint contains 189 unique checked theorems: 23
baseline entries, 154 post-baseline foundational entries, and twelve modular
capstones. The 196-node research catalog classifies them as 23
`checked_existing`, 166 `checked_m20`, three `planned_expressible`, and four
`blocked_by_language` records. The ordered snapshot root is
`9650ae53f506c282daf84fca5e9c08d0d48bb36db813b4efc43f54156d25bf6b`;
the theorem-source digest is
`c4b02793df05a634b63cb4eff339c173b628f7646b5fc5788de6e6e8ebf8a737`.

Six new certificates turn the preceding CRT fold algebra into an actual
ordinary-induction prefix invariant:

| Checked theorem | Nodes/depth | Cuts |
|---|---:|---:|
| `right_factor_divides_product` | 229 / 25 | 7 |
| `beta_accumulated_product_step` | 11,174 / 69 | 330 |
| `beta_crt_prefix_congruence_step` | 7,352 / 64 | 213 |
| `beta_crt_prefix_invariant_step` | 18,613 / 70 | 545 |
| `bounded_beta_crt_prefix_invariant` | 25,496 / 78 | 752 |
| `bounded_beta_crt_for_existing_code` | 25,545 / 79 | 755 |

The product successor multiplies the current $P$ by the next beta modulus and
preserves three properties: $P$ stays nonzero, every modulus in the completed
prefix divides it, and it remains coprime to every future bounded modulus.
The congruence successor uses `binary_crt_fold_step` to add the next residue
decoded from the already supplied code $b$ while preserving all earlier
decoded congruences. `beta_crt_prefix_invariant_step` combines those results.

The substantive induction theorem `bounded_beta_crt_prefix_invariant`
constructs $P,z$ at every $k\le N$ and carries four facts simultaneously:

1. $P\ne0$;
2. every beta modulus at a position $i\le k$ divides $P$;
3. $z$ is congruent modulo that modulus to every value already decoded from
   $b$ at such a position; and
4. $P$ is coprime to every future bounded beta modulus.

The name `bounded_beta_crt_for_existing_code` is intentionally literal. Its
conclusion only asks for congruences to residues already decoded from $b$.
Extensionally it is trivial—one may choose $z=b$—and therefore it is not the
generic theorem that recodes or extends an independently specified finite
sequence. The admitted proof projects the genuine induction invariant, but
its conclusion must not be advertised as arbitrary finite-prefix CRT.

The remaining native factorization gates are independent finite-prefix
specification and recoding/extension, exact beta-coded prefix-product
recurrence and trace functionality, bounds placing each exact prefix product
below the selected beta modulus family, the factor-primality and final-product
links, greatest-prime descent, factorization existence and uniqueness, and
FTA.

The complete snapshot has 242,629 structural proof nodes, 6,895
self-contained Cuts, and 149 Cut-bearing certificates. The largest theorem is
`bounded_beta_crt_for_existing_code` at 25,545 nodes and 755 Cuts; its depth is
79, while `prime_divisor_exists` retains the overall depth maximum of 80.
Every declared dependency slot in the six new theorems is mutation-necessary.
The synchronized, undeployed browser candidate is build `2026-07-29h` and has
application identity `a-98b1d8bb8dd7`. Its source-bound corpus fingerprint is
`a3c2f8c5c762b10fc9c1117723c74fecb50348cfb699f73bc76fb3714df3bf1b`;
the isolated smoke records 378 sessions, 5,373 raw transitions, 5,370 unique
transitions, and all 189 authored QEDs. The full Peano suite passes 1,098
tests in 181.34 seconds, and Lambda remains green at 360 tests plus 36
subtests.

## 2026-07-29 — The native beta-coded FTA closes

The local candidate now contains 246 unique checked theorems. The final
finite-factorization tranche constructs independent β-coded prefixes, exact
prefix-product traces, prime and adjacent-sorted invariants, canonical append,
and greatest-prime-divisor descent. These feed factorization existence and
extensional uniqueness; no primitive list, division, remainder, gcd, or
factorization symbol was added.

The exact endpoints are:

| Theorem | Nodes/depth | Cuts |
|---|---:|---:|
| `prime_factorization_existence` | 43,973 / 98 | 1,328 |
| `prime_factorization_uniqueness` | 29,789 / 82 | 854 |
| `fundamental_theorem_of_arithmetic` | 73,767 / 99 | 2,184 |

The FTA certificate SHA-256 is
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It checks from the empty context and through the interactive
`use`/`exact`/`qed` route, uses PA1–PA6 and induction only, and contains no
DNE. Dependency, PA-leaf, hypothesis, and semantic mutations all fail closed.
Because β coding is not canonical, uniqueness compares equal lengths and
decoded entries rather than raw code numbers.

The untrusted import preflight now shares the existing live-proof resource
gate of 100,000 nodes and depth 256. Exact 100,000/256 boundary certificates
pass; 100,001/257 certificates fail transactionally. The synchronized
248-entry catalog has 246 checked entries, one planned `prime_unbounded`
endpoint, and one representation-blocked conventional integer-coefficient
Bézout interface. Balanced four-natural Bézout remains checked.

## 2026-07-29 — A prime above every bound

The final planned arithmetic endpoint is now checked. Given `n`,
`prime_unbounded` first constructs a nonzero common multiple `c` of every
positive natural at most `n`, then takes a prime divisor `p` of `S c`. If
`p <= n`, the common-multiple invariant gives `p | c`; since `p | S c` too,
the consecutive-number remainder lemma gives `p | 1`, forcing `p = 1` and
contradicting primality. Thus `n < p`.

The certificate has 4,595 nodes, depth 82, and 146 self-contained Cuts. Its
SHA-256 is
`8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b`.
It uses PA1–PA6 only, contains no DNE, and passes exact statement replay,
dependency-slot, PA-leaf, authored-hypothesis, and live-use audits.

The runtime is now 247 theorems: 23 baseline, 212 general foundational, and
twelve modular capstones. The 248-entry catalog records 23
`checked_existing`, 224 `checked_m20`, no planned entry, and one
representation-blocked conventional integer-coefficient Bézout interface.
The regenerated snapshot has 982,534 nodes, 28,892 Cuts, 204 Cut-bearing
certificates, root
`eb4775dfd181dc5e45bec463a93f14b0ea9d02501c40c5167b7cae77cd4ff432`,
and source digest
`295ca3b65970324e7d2ed51b57dc4510227b0abbc2d35b68a809dbde26aba868`.
The vault has 327 notes and 3,286 links. The corpus fingerprint is
`6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`;
its smoke has 494 sessions, 9,235 raw/9,232 unique transitions, and all 247
QEDs. Browser build `2026-07-29k`, application `a-77df7c0860bc`, is local and
undeployed.

## 2026-07-29 — Model-v3 binds the 247-theorem curriculum without target leakage

The first Qwen policy's low validation loss concealed a structurally weak
curriculum: all 87 inspected roots began with `intro`, only two rows used
`norm_num`, and the selected data contained no `use`, induction, or IH
transition. Scaling that distribution would train the same shortcut more
confidently. The successor experiment is therefore named `model-v3`; the old
56-theorem model-v2 identity remains frozen for historical artifact replay.

Model-v3 treats declaration order as a learning curriculum. For theorem rung
$i$, the executable and prompt authority is exactly `THEOREMS[:i]`; the target
and every later theorem are unavailable. The trajectory first executes one
ordinary `use` command for each declared direct dependency and then the exact
authored tactic script. Every resulting QED still passes the independent
kernel against the original closed formula. A separate identity module binds
the v2 catalog schema, its ordered root and theorem-source digest, reconstructs
all 247 certificates, and checks them from the empty context. The full release
gate passed all 247 reconstructions. Prefix and prompt tests passed 12 tests
with one opt-in full replay skipped after that separate release run; a
three-rung corpus sample passed six focused tests and yielded 13 independently
replayed transitions: two dependency imports and eleven authored actions.

Synthetic data uses the full checked prefix but no catalog-theorem schemas. It
removes the earlier artificial implication gate from induction candidates and
schedules complete proof sessions by their first tactic head, with `intro`
roots capped at twenty percent. Closed equality, existential, conjunction,
and disjunction roots prevent universal-introduction states from defining the
entire opening distribution. Exact v3 held-out propositions are rejected by
the generator and by dataset attestation.

The prompt exposes the complete one-line tactic grammar and twelve
deterministically retrieved `name : statement` records. Giant statements are
displayed as bounded, content-addressed excerpts; retrieval still scores the
full canonical proposition. Every row binds both its exact prefix identity and
the full 247-theorem identity. A pinned-tokenizer root audit found that 57 of
247 full-prefix theorem prompts exceed the draft 4,096-token budget; the root
maximum is 6,235. The reviewed configuration therefore uses Qwen3-1.7B's
native 32,768-token position limit, microbatch one, and accumulation 32. The
preparation job must still reject the whole run if any selected prompt and
completion exceed that native limit—there is no truncation fallback.

An inherited evaluation leak was found before launch. The model-v2 benchmark
targets are members of the new full library, so testing model-v3 on them would
measure memorization or retrieval. Model-v3 now selects four separately sealed
propositions from its own attested contract; model-v1 and model-v2 retain their
historical targets. The trained evaluator still accepts a result only after
public-surface execution and independent kernel replay.

## 2026-07-29 — The launch audit closes prompt and split leakage

A final adversarial pass delayed the WMI launch for sound reasons. The first
draft displayed only twelve retrieved theorem statements, so many legal
`use NAME` actions had no visible spelling. Model-v3 now carries a compact,
hashed inventory of every name in the exact allowed prefix while retaining the
bounded statement retrieval. This is a v3-only change: the published v2 prompt
and environment identities remain byte-compatible.

The same audit found three places where a dataset could make a stronger claim
than its evidence. A sealed benchmark proposition could occur as an
intermediate transition goal even when the root differed; a missing trajectory
marker could turn arbitrary prefix examples into an apparently exact catalog
schedule; and random validation assignment could expose a held-out library
theorem through a later descendant proof. The corrected contract checks every
transition target structurally, makes catalog and synthetic lane markers
mandatory, and keeps the complete dependency ladder in the training split.
Validation and test rows therefore come from independently grouped synthetic
roots, while final success is measured only on the separately sealed goals by
kernel-checked search.

The training selection ceiling is 80,000 rows, above the complete expected
split (70,000 synthetic rows before holdout assignment plus exactly 8,494
catalog transitions). Thus the deterministic loader retains every one of the
247 theorem trajectories instead of accidentally sampling away small rungs.

WMI also supplied a concrete operational lesson. The 100,000-row v2
preparation generated and built successfully, but its independent rebuild was
killed by a one-hour subprocess watchdog. Independent replay is not removed or
sampled for v3; its watchdog is raised to four hours and the preparation
allocation to twelve hours so the exact 78,000-plus-row rebuild can finish.

## 2026-07-29 — Large library traces use the reviewed-limit escape hatch

Exact model-v3 library generation exposed a resource distinction that the
ordinary pilot never reached: at least one valid, independently checked native
library proof renders more than the normal 16 MB session-trace ceiling. The
ordinary `run_proof` default and JSON request contract remain unchanged. The
library generator instead passes an explicit host-owned trace allowance, capped
by the shared runner at 128 MiB. The JSONL transport independently retains its
512 MiB aggregate default. A request record cannot enlarge its own authority or
resource envelope.

The trace logger retains its fail-stop boundary: it rejects the record that
would cross the selected limit before appending it or writing it to the sink.
The library generator catches that specific resource exception and reports the
name of the theorem that crossed the reviewed ceiling, while transactional
publication leaves no plausible corpus artifact set behind.

## 2026-07-29 — Shared exact state structure replaces a tempting lossy projection

The first complete token audit found a state whose legacy JSON observation was
122,546 tokens, far beyond Qwen's native context. A lossy, hash-marked excerpt design looked
like the obvious repair, but the offending seven goals repeated declarations
and targets extensively. Before discarding information, we measured that
structure. Prompt v3 now puts exact comma-delimited context chunks and exact
targets into deterministic first-occurrence tables, then represents each goal
by declaration indices and one target index. The prompt parser reconstructs
the original canonical one-line goal strings byte-for-byte.

This is deliberately a v3-only lossless structural encoding. The raw trace,
independent replay, dataset-row state, held-out contamination check, and kernel
state remain exact, and the v1/v2 prompt byte hashes do not change. Canonicality
is strict: exactly one correctly spaced turnstile, compact JSON, strict integer
indices, first-use table order, no duplicate or unused entries, and exact
reconstruction. Malformed claims fail rather than falling back to another
interpretation.

The encoded state JSON is capped at 44,000 Unicode characters, with no target,
hypothesis, or name slicing. In all 443 retained before/after states of the
index-230 stress trace, the maximum is 39,423 characters and zero states exceed
the cap. Step 115 changes from 196,457 legacy characters to 37,259 encoded
characters solely by sharing exact strings. The pinned check of the largest
full prompt plus tactic and EOS is 29,111 tokens, leaving 3,657 below the
32,768-token native window. All 222 exact transition prompts for the stress
proof pass: median 17,444, p95 26,662, p99 28,537, and maximum 29,111 tokens.
The complete combined-corpus scan remains the final gate.

## 2026-07-29 — Resource API changes refresh generated provenance

The reviewed trace ceiling adds a keyword to the trusted batch runner even
though ordinary executions retain the same 16 MB behavior. Because the v1
corpus manifest honestly fingerprints the complete Peano Python source tree,
the old generated release could not simply be paired with a new expected hash.
We reproduced all 1,692 sessions under the required CPython 3.10.0 runtime,
re-exported 13,344 unique transitions, and refreshed the manifest, statistics,
README, and browser application identity from the resulting bytes. The new
corpus run fingerprint is
`6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`;
browser build `2026-07-29k` binds application manifest
`a-77df7c0860bc`. Neither artifact has been deployed.

The same full-suite pass exposed two model-v2 assertions that still equated
the live public catalog with its historical 63-entry checkpoint. They now
assert the append-only 247-entry public count while separately checking the
frozen 56-name model-v2 authority and all 191 unavailable names. No model-v2
prompt or environment identity was repinned.

## 2026-07-29 — The first model-v3 preparation failed before training

WMI preparation `172536` validated the pinned environment and completed all 247
predecessor-prefix library trajectories: 8,494 transitions plus 247 independently checked QED
footers. It then failed after 1:02:34 on a synthetic ring instance whose normalized coefficient was
132, above the reviewed limit of 128. The failure was neither an OOM nor a training failure.
Transactional staging published no complete synthetic artifact, and no dependent training or
evaluation job was submitted.

The repair enumerates the 2,396 safe coefficient tuples and combines them with sixteen compact
closed-zero tags, yielding a 38,336-statement ring period. The repaired schema catalog is version
2: version 1 had already been exercised by the failed job and cannot honestly acquire new meaning.
A separate audit found that removing induction gates had collapsed every indexed variant to one
of four statements. Six-digit base-4 zero tags now give each induction schema a period of 4,096
genuinely distinct canonical roots without hiding `induction` behind `intro`.

A model-free full-schedule pass now runs before expensive proof replay. It also exposed an
exact-fill edge case: choosing a one-row head for the final row could leave head imbalance two.
Ties between equally deficient heads now prefer longer minimum sessions, reserving one-row heads
for exact completion. The registered 70,000-row plan contains 32,600 unique roots; every head
occurs 2,328 or 2,329 times, every schema occurs, and the sequence digest is
`79d2704eab6eb73205ff2234f55f0d4a7e034176fe8dc8649c6950ff499d547b`. This is a deterministic
plan, not yet a completed corpus or learned-model result. An intermediate version-1 repair plan had
2,174 benign duplicate skips between two closed-`norm_num` families. Version 2's hash-derived
offsets make the registered ranges disjoint: the final plan has zero duplicate skips, and both
families contribute 1,164 roots. A boundary audit then found that row budget 70,001 would encounter
one numeric candidate exactly equal to a sealed evaluation target. The candidate is valid PA, not
a malformed schema, so a dedicated typed path now counts and excludes it while every other
generation error remains fatal. The maximum 100,000-row preflight succeeds with 46,574 unique
sessions and exactly one such held-out skip. Finally, the WMI job now invokes the synthetic
generator before the library generator. Its whole-schedule prepass therefore runs before either
corpus spends time on proof replay, rather than after another hour of work. The job also refuses a
nonempty model-v3 data directory up front. A stale artifact from a previous partial run can no
longer wait until the second generator to turn a costly retry into an overwrite refusal.

The final local gate for this repair reports 1,298 Peano tests passed with one intentional skip in
1,275.58 seconds. Lambda Lab reports 360 tests plus 36 subtests; the 19 focused generator tests and
23 WMI/config tests pass; all 287 documented commands replay; the 247-note arithmetic vault and
3,286 links verify; and a complete 38-source Jupyter Book build succeeds with warnings as errors.

## 2026-07-30 — A corpus is historical evidence; a trainer is current code

WMI preparation `172729` completed the two expensive source generators before this entry was
written: 32,600 independently checked synthetic sessions supply exactly 70,000 transitions, while
all 247 declaration-ordered library sessions supply 8,494 transitions. The combined builder was
still replaying those sessions, so no transformer optimizer step had started. This distinction is
now reported literally. Reserving an A100 for a CPU-heavy preparation job does not make the job a
training run, and a partial trace directory is not a dataset release.

That long replay also exposed a deployment problem. The generated data belongs to the old clean
source commit that performed the replay, while the trainer has since acquired stricter loss and
selection code. Re-running every proof merely to change the optimizer would be wasteful; trusting
mutable files from an earlier checkout would be unsafe. The chosen bridge is a content-addressed,
closed-tree corpus seal. It copies exactly twelve dataset artifacts and the preparation job's three
reports into an atomic, non-overwriting, read-only directory; binds their hashes, source commit,
Slurm job, authority schedule, tokenizer, and replay identities; and then verifies the copy again.
A current checkout may consume it only after independently matching its present compiler, Peano
source inventory, prompt contract, held-out set, and library identities. This check deliberately
does not replay the proofs a second time: the historical report proves how the bytes were made, and
the current-source eligibility record proves that their semantics have not drifted.

The model-v3 loader no longer means “take the first 80,000 rows.” It retains every one of the 8,494
catalog transitions and chooses whole synthetic proof sessions under an explicit 12,288-row
ceiling. Every one of the fourteen first-tactic heads and all fifty-one synthetic schemas receives
an anchor, head counts differ by at most one complete fill round, and the canonical selection is
independent of input order. A second `max_train_samples` cap is forbidden, because row-level
subsampling could silently sever a proof trajectory or remove a small library rung. The curriculum
seed must equal the training seed so the selection record and stochastic run have one audited
identity.

Finally, the loss path now projects vocabulary logits only at completion-token positions. It still
computes the exact ordinary causal cross entropy: completion label at position $i+1$ is scored by
the logit at position $i$, sums are accumulated in FP32, and the accumulation window is divided by
its exact number of supervised tokens. A pinned Qwen3-1.7B LoRA probe matched full-logit loss and
gradients to numerical precision. The optimization is therefore a memory reduction, not a new
learning objective. The A100 smoke gate was strengthened to exercise both the longest total
sequence and the largest projected completion, require gradients on every trainable adapter
parameter, and compare deterministic post-update output with the separately reloaded adapter.

The final manual smoke design uses no redundant third optimizer step. If one natural row has both
maxima, it is the sole probe. Otherwise the natural longest-sequence row is retained and the
longest-completion prompt is extended to the maximum sequence length with attended token ids whose
labels remain masked. They are inserted immediately before the supervised suffix, so the suffix
contract and completion targets are unchanged while all sequence positions remain active. This is
stronger than zero-attention right padding, which an unpadding attention backend could discard and
therefore could not establish a backend-independent memory envelope. The natural rows still supply
the tokenizer round-trip evidence. Each manual probe follows the trainer's fused AdamW grouping,
cosine schedule, warmup, gradient clipping, gradient-checkpointing, and cache settings; every LoRA
parameter must receive a finite gradient and at least one adapter tensor must change.

A second gap was that faithfully reproducing Trainer components did not execute Trainer itself.
The smoke now destroys the manual optimizer and scheduler, runs garbage collection, and empties the
CUDA cache before constructing a real `CompletionOnlyTrainer`; the two optimizer states can never
coexist. It performs exactly one non-warmup optimizer step and one explicit evaluation on the same
active componentwise-maximal envelope, with accumulation fixed to one and logging, periodic
evaluation, and saving disabled to bound runtime and storage. A pre-optimizer callback checks every
raw LoRA gradient, performs the norm-1.0 clip with `error_if_nonfinite=True`, and checks every
post-clip gradient; a separate tensor snapshot proves an adapter update.
The cross-verifier requires the exact step, losses, batch dimensions, active-token count, arguments,
gradient population, update, and CUDA evidence. Both production and smoke TrainingArguments now
pin `gradient_checkpointing_kwargs={"use_reentrant": False}`; otherwise Transformers 4.53.3 would
call `gradient_checkpointing_enable` again without preserving the manually selected mode.

The same review found an environment-sensitive loss-scaling boundary. Transformers 4.53.3 chunks
gradient accumulation itself, and our completion loss has already divided each microbatch sum by
the complete window's supervised-token count. Accelerator's `backward` divisor must therefore stay
one; an `ACCELERATE_GRADIENT_ACCUMULATION_STEPS` override could otherwise divide the loss again.
One shared framework-light checker now guards production and smoke immediately after Trainer
construction: one process, one visible GPU, matching `cuda:0` Trainer and Accelerator devices,
BF16 mixed precision, `DistributedType.NO`, `DynamoBackend.NO`, no DeepSpeed, FSDP, or tensor
parallel plugin, exact configured Trainer accumulation, and Accelerator divisor one. Its normalized
record is saved and cross-verified. Trainer's built-in clip is disabled (`max_grad_norm=0.0`) because
its callback order would clip before our audit and its non-finite mode is permissive. The strict
pre-optimizer callback records the finite pre-clip norm and finite post-clip population. Training
also rejects a missing `num_items_in_batch`: without
that whole-window token count, gradient accumulation would silently change the objective. Evaluation
keeps the local token mean because it runs with the model in evaluation mode. The real paths also
spell out the custom max gradient norm 1.0, AdamW betas $(0.9,0.999)$, epsilon $10^{-8}$, and
`logging_nan_inf_filter=False`; defaults are not evidence.

The operational lesson is to separate four jobs that answer four questions. The historical full
replay asks whether the source proofs generated valid data. The current sealed-preparation job asks
whether newer code may consume those exact bytes and whether the selected token/memory envelope
fits the A100. The training job asks whether one fresh indexed-loss optimization run completed its
predeclared step schedule. The evaluation job asks what bounded search reported. A fifth,
model-free command then independently checks every reported proof against the frozen original goal.
Combining any pair would make a faster status message but a weaker experiment.

The independent replay parser is deliberately narrow: evaluator version 4, the exact four goal
names and formulas, the model-v3 environment digest, search mode, seed, depth 32, beam 16, eight
candidates, 512 model calls, 4,096 states, and 256 generated tokens must all agree before one proof
is executed. Duplicated search payloads and counters are cross-checked rather than trusted. Only
then does each attempt labelled `proof` reach `verify_proof`; a no-proof report may be structurally
valid, but it establishes no proving success.

At 01:46 CEST the first builder pass in WMI job `172729` atomically published the complete split:
64,500 training rows from 26,335 sessions, 6,948 validation rows from 3,217 sessions, and 7,046 test
rows from 3,295 sessions. The training split contains all 247 catalog sessions and all 8,494 exact
catalog transitions; validation and test are synthetic-only. Its canonical manifest records
32,847 accepted kernel-checked sessions, 78,494 positive transitions, zero ignored transactional
errors, dataset digest `2e236384ecb6e7b15ccf986abab53fcfd4ec47fc97c7e00f5cc736dbbb4f224e`,
and split-file digests. The independently copied manifest matched the live WMI SHA-256
`ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983`.
This is a real completed builder milestone, but not yet a corpus release: the same job immediately
entered the independent attestation rebuild, and no attestation, token-audit, or runtime-smoke
report existed at this checkpoint.

At this checkpoint the seal content digest and all successor job/result identities remain pending.
They are not placeholders to fill optimistically: the tracked configuration must remain ineligible
until the historical job ends, the non-replacing seal verifies, and its three external anchors have
been copied from authenticated evidence.

The documentation gate for this design change is green. All 38 Jupyter Book sources rebuild with
warnings treated as errors; the complete executable-book gate replays 194 deep links and 47
sessions containing 287 commands; seventeen focused book tests pass; and the vault generator
verifies all 247 lemma notes inside a connected 327-note graph with 3,286 resolved links. The seal,
eligibility, sealed-preparation verifier, evaluation replay, and guarded submission CLIs all expose
the documented arguments. These checks validate the documentation and static launch contract, not
the still-pending corpus seal or trained-model result.

## 2026-07-30 — A same-authority pretrained control, without identity laundering

The model-v3 evaluation now has a separate pretrained-base entry point and typed-A100 Slurm job.
The completed adapter manifest is used only to pin the Qwen revision, saved tokenizer, full
247-theorem prompt environment, held-out contract, and exact comparison artifact hashes. The
adapter tree is checked before and after the run, but PEFT is never imported or attached. This
matters scientifically: calling the base model through the adapter identity would make a clean
report look comparable while obscuring which weights actually generated it.

The control therefore emits `peano-policy-pretrained-base-v1`, fixes the same seed and
beam-16/candidates-8/depth-32/calls-512/states-4096/tokens-256 envelope, and permits no goal or
budget overrides. Its report lives beside the completed run but outside the closed adapter and
tokenizer subtrees. The trained-adapter replay parser was deliberately left unchanged and rejects
the new identity; a future independent control attestation, if needed, must be a separate narrow
gate. Ten focused baseline tests and twenty-one WMI-control tests pass. No GPU baseline job was
submitted: the comparison adapter does not yet exist.

## 2026-07-30 — Recovery must preserve both bytes and job identity

The completed corpus outlived its first preparation allocation. Job `172729`
spent 5h07m on the first combined build, then entered the attestor's strict
row scan. A live file-descriptor probe showed that the independent rebuild had
not even started with only 4h12m of wall time left. Finishing replay, tokenizer
audit, and A100 smoke was impossible. We cancelled the CPU-bound attestor after
7h58m while it was scanning validation data; the twelve completed artifacts
and manifest SHA-256
`ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983`
remained unchanged, and all three reports remained absent.

The recovery does not rename a report from another job or pretend the cancelled
allocation completed. Commit `c56b7854ad2818257fee55a5c5d60ac7891fb9da`
turns the historical preparation entry point into an exact-corpus continuation:
it permits only the known twelve filenames and manifest hash, never invokes a
generator or first builder, and reruns attestation, token audit, and smoke under
one fresh Slurm identity. The deployment synchronizer protects exactly
`data/peano-policy-v3/***` so publishing that clean source cannot delete the
still-unsealed evidence.

A second timing check caught a subtler deterministic failure before it consumed
the night. The attestor's independent-builder watchdog was four hours, shorter
than the measured 5h07m build it was required to reproduce. Job `173037` was
therefore stopped after 6m30s with no report. Commit
`5faa3d27cbaf522198ffa1bdcd11fa9d57341658` raises only that watchdog to eight
hours and pins the measured rationale in a focused test. Replacement job
`173040` now runs from that clean commit and the same corpus bytes. It is still
preparation, not transformer training: the next honest evidence is a completed
attestation report, not an allocated A100.

## 2026-07-30 — Preserve the optimizer result and bind its judge

A final prelaunch audit found two faults that would not change the loss but
could weaken the experiment around it. First, the one-epoch schedule has fewer
steps than the configured periodic checkpoint interval. The old ordering ran a
full 512-row evaluation before the only explicit adapter save, so a late
timeout could discard every learned tensor. The adapter and tokenizer are now
saved immediately after the exact optimizer-step check and before that final
evaluation. The training manifest is still withheld until evaluation and all
source, deployment, corpus, and report rechecks pass; preserved weights alone
are therefore recoverable evidence, not a falsely completed run.

Second, the evaluation Slurm job previously carried a training dependency but
did not compare it with the producer recorded inside the adapter manifest. A
same-source stale adapter could consequently be judged under the wrong chain.
The evaluator now requires equality of the manifest training job,
`PEANO_TRAIN_JOB_ID`, and the immutable submission-ledger dependency before it
loads the model, repeats the check before publication, records the binding,
and lets the model-free replay parser verify it. Interactive theorem requests
have a separate `slurm-proof-request-bound` status: they bind the completed
manifest but correctly claim no `afterok` dependency. The combined evaluator,
proof-request, replay, trainer, and pretrained-control regression set passes
144 tests.

## 2026-07-30 — The seal bootstrap is code too

The original staging plan pinned the seal CLI and module but left a Python
package marker and cached bytecode in the directory. Invoking the CLI by path
also allowed Python to read it before its own digest check. Those were small
files, but they were executable inputs outside the reviewed two-file claim.

The bootstrap now requires exactly three directories and two single-link
source files: the seal CLI and the standard-library-only module. Package
markers, `__pycache__`, symlinks, specials, aliases, extras, mutations, and
digest drift are fatal. The Slurm script no longer asks Python to execute the
CLI pathname. A launcher embedded in the submitted script stable-reads and
hashes it, compiles those same bytes as `__main__` under `-I -B -S`, and only
then lets the CLI independently verify and compile the module. An adversarial
replacement probe proved that execution retained the reviewed bytes and that
the next launch rejected the replacement. Forty-nine focused seal tests pass;
the remote staging tree is deliberately not changed until preparation
`173040` completes.

## 2026-07-30 — Intermediate weights are evidence, not a resumable run

The end-of-epoch adapter save fixed a late-evaluation failure mode but left a larger gap: the
audited one-pass model-v3 schedule is about 650 optimizer steps, while the ordinary Transformers
checkpoint interval is 1,000. A wall-time, node, or process failure at step 599 would therefore
discard every learned tensor. Lowering `save_steps` was the wrong repair. A Trainer checkpoint also
writes optimizer, scheduler, RNG, trainer-state, and historically pickle-compatible files; loading
that state would contradict the one-shot `resume="never"` experiment and expand the trusted
serialization surface.

The trainer now has a deliberately narrower recovery channel. Its preflight record plans six
adapter-only saves, at optimizer steps 100 through 600. The callback asks PEFT for safe
serialization only, verifies exactly one `adapter_model.safetensors`, and records no continuation
state. It stable-reads `run-identity.json` before and after the save, so each snapshot is bound to
the exact configuration, selected data, source tree, deployment, and Slurm job that began the run.
The recovery manifest explicitly says that training is incomplete, the artifact is not eligible as
a training result, and resumption is unsupported. The final training manifest and evaluator rules
were not widened.

A later callback audit found that merely choosing `save_steps` beyond the 650-step run was still
insufficient: Transformers' default flow sets its save flag at the final `max_steps`. Production now
uses `save_strategy="no"` and `eval_strategy="no"`. The six recovery artifacts and final save remain
explicit adapter-only safetensors operations, and the validation pass is called explicitly after the
adapter is secured. That stock validation metric averages per-batch token means; it is runtime
evidence, not a corpus-global completion-token NLL.

Publication uses the same lesson as the corpus seal but preserves failed evidence rather than
cleaning it up. Adapter bytes and the manifest are written under a private `.partial-…` sibling;
the manifest is last, all files and directories are fsynced and made read-only, the closed tree is
verified, and an operating-system no-replace rename installs the canonical step/run/job name.
After publication the read-only tree is verified again. A crash leaves a visibly partial staging
directory, a race leaves both the staging bytes and prior target untouched, and a repeated callback
cannot replace a completed snapshot. Focused adversarial tests cover interrupted serialization,
unsafe weight suffixes, run-identity replacement during a stable read, manifest laundering,
publication races, duplicate callbacks, permissions, and absence of every optimizer/resume file.

## 2026-07-30 — A completed run is an evidence object, not a step counter

The prelaunch review then followed the exact Transformers 4.53.3 callback order. Built-in gradient
clipping happens before `on_pre_optimizer_step` and does not request an exception for a non-finite
global norm. Inspecting gradients only in our callback would therefore inspect already modified
values. Model-v3 now sets Trainer's built-in norm to zero, requires every raw LoRA gradient to exist
and be finite, calls one strict max-norm-1 clip with `error_if_nonfinite=True`, checks every
optimizer-visible gradient again, and records the pre-clip norm at all expected optimizer
boundaries. The callback interprets Trainer's still-unincremented `global_step` as boundary
`global_step + 1`; finalization requires the exact sequence 1 through 650. Legacy training retains
its old built-in clipping and cannot accidentally claim this record.

`global_step == 650` is still not sufficient evidence. The final manifest now binds five agreeing
step counts, the one-CUDA-process/no-plugin/Accelerator-divisor-one runtime, observed Trainer
arguments, all raw and post-clip gradient boundaries, the complete finite norm curve, the exact
periodic/train-summary/evaluation-summary log history, finite metrics with honest loss semantics,
and the closed adapter/tokenizer hashes. A raw-byte tensor-population fingerprint is taken before
and after optimization; names, dtypes, shapes, and each tensor's content hash are canonicalized.
An unchanged or non-finite adapter cannot be published. Model-v3 loaders and the same-authority
pretrained control reject a missing, partial, stale, or internally inconsistent completion record
before importing Torch, Transformers, or PEFT. The manifest reader also rejects duplicate keys,
NaN/Infinity, symlinks, hard links, and a changing file snapshot. The stock `train_loss` remains a
mean of optimizer-window token means, while `eval_loss` is a mean of per-example token means at the
pinned evaluation batch size one; neither is described as corpus-global token NLL.

The recovery rename itself also gained an executable filesystem premise. A model-free preflight
creates an unpredictable exclusive parent on the exact output filesystem, writes and fsyncs a
sentinel, protects the tree, invokes the production no-replace rename, and verifies preserved
bytes, modes, inodes, device, and source disappearance. The protected probe and an exclusive
canonical report are deliberately retained. Scheduled WMI training runs this check on `/work`
before model allocation and passes the live report into the trainer, which binds it into the run
identity and re-verifies both report and probe before publishing the final manifest. Local macOS
tests establish the `renamex_np(RENAME_EXCL)` branch; the Linux
`renameat2(RENAME_NOREPLACE)` fact remains explicitly pending until WMI connectivity returns and
the real `/work` probe runs.

These are local launch safeguards, not training results. Focused completion/evidence/loader tests
and live callback tensor tests pass, as do the recovery publication race and tamper tests. Job
`173040` remains historical preparation, FortiClient is disconnected at this checkpoint, and no
model-v3 optimizer step or loss has been observed.

## 2026-07-30 — Admit the saved policy, not the Python object

The last completion contract still trusted an awkward handoff. It proved that the live LoRA
tensors changed, then asked PEFT and the tokenizer to serialize them, but it did not prove that a
fresh process would reconstruct the same policy from those files. A successful `save_pretrained`
call is not that proof: a wrong adapter name, missing tensor, dtype conversion, stale tokenizer, or
loader-visible extra file could leave a plausible directory whose behavior differs from the
terminal optimizer state.

Model-v3 now performs a bounded semantic admission after training. Before releasing the live
model, it chooses three SHA-ranked probes from the *admitted* train and validation populations;
selection is independent of input order and binds the complete candidate population to the run
identity. For each probe it records the exact tokenization, indexed completion loss, and raw bytes
of the projected logits. It also hashes the canonical PEFT save-format tensor population: sorted
names, dtypes, shapes, and content digests. Frozen evaluation goals are intentionally absent. This
stage asks whether the saved artifact is the learned policy, not whether the policy already solves
the benchmark.

The Trainer, optimizer, tokenizer, and original model references are then released and CUDA memory
is cleared. One fresh local-only load reconstructs the pinned Qwen base, saved tokenizer, and
single `default` PEFT adapter. Admission independently reads `adapter_model.safetensors`, requires
the saved and reloaded canonical tensor populations to equal the terminal in-memory population,
retokenizes all probes, and requires byte-exact projected logits and exact finite losses. Disabling
the adapter must change at least one probe, which catches a loaded-but-inert LoRA path. The final
evidence joins the base commit/configuration, run-identity digest, `cuda:0` Trainer runtime,
individual adapter files, complete adapter/tokenizer tree hashes, and completed-training hashes.
Inference and the same-base control reject model-v3 manifests without that join before importing
the heavy framework.

Pinned Transformers 4.53.3 exposed a related lifecycle trap. `bf16_full_eval=True` performs a
destructive `model.to(dtype=bfloat16)` before full evaluation, while PEFT 0.16 normally keeps LoRA
parameters in FP32. That would mutate the learned adapter after its final fingerprint and save.
Production therefore keeps BF16 autocast but sets `bf16_full_eval=False`; tensor populations are
checked again after serialization and after explicit evaluation. Any change withholds the final
manifest.

Final publication is now one-shot as well. The output directory is claimed by exclusive `mkdir`
and its path, parent, device, inode, and mode are rechecked at the end. Adapter and tokenizer trees
are written into private partial siblings, fsynced, protected read-only, and installed with the
operating system's atomic no-replace rename. `run-identity.json` and the final training manifest
use the same non-replacing publication rule. A crash leaves named partial evidence; a competing or
repeated run cannot replace an existing result. The planned 650-step schedule must also divide
exactly by its logging interval, preventing a late evidence-shape failure after expensive training.

Auditing that “closed-tree” check found another quiet filesystem trap: `Path.rglob()` combined with
`is_file()` can simply omit a symlinked directory or special node. The artifact scanner now walks
without following links, rejects symlinks in every path component, FIFOs/devices/sockets,
cross-filesystem nodes, and every hard link, and hashes each regular file through an `O_NOFOLLOW`
descriptor. Device, inode, mode, link count, size, mtime, and ctime must agree before opening,
through the read, and at the pathname afterward; a second complete inventory catches insertion or
removal during hashing. Model-v3 callers additionally require exact directory `0555` and file
`0444` modes, while historical v1/v2 adapters retain their compatible default contract.

The wiring audit then asked a different question: could correct primitives still be bypassed by a
mislabelled caller or by mutation between two correctly placed checks? Prompt-v3 attestation and
the model-v3 curriculum must now either appear together or be absent together, and that alignment
is checked before importing Torch, Transformers, or PEFT. Training repeats the strict protected
tree check after semantic admission and all slow source/report validation, immediately before the
non-replacing manifest write. The generator and same-base control check their adapter/tokenizer
inputs both before and after heavy loading, and recovery requires exact `0555` directories and
`0444` files rather than merely testing that write bits are absent. The focused wiring audit passed
89 tests. These modes and repeated observations are provenance and accidental-corruption gates;
they are deliberately not described as security against a hostile process running as the same
filesystem owner, which could change permissions and race any pathname-based verifier.

The frozen-tree verification now reports 540 focused model-v3 tests and 1,707 complete Peano tests
passing (with one intentional skip), followed by all 360 Lambda tests and 36 subtests. The
warning-as-error book builds all 38 sources; 194 deep links and 287 commands replay; and the
327-note vault resolves all 3,288 links. The real Linux `/work` publication probe, A100 admission
smoke, optimizer steps, losses, and independent kernel-judged evaluation remain pending. This
section records why the launch contract changed; it records no transformer-training result.

## 2026-07-30 — Make the claimed seal launcher real

A repository audit found that the preceding bootstrap prose had outrun the implementation. The
two-file CLI/module inventory was enforced, but every executable test still invoked the CLI by
pathname; Python could therefore execute its top-level code before the CLI checked its own hash.
There was no seal-publication Slurm job containing the launcher described in the diary. That was a
real execute-before-self-hash gap, so the earlier claim was not accepted as evidence.

The missing operational artifact is now tracked as the CPU-only one-time job
`slurm/peano_wmi_seal_v3_corpus.sbatch`. It pins historical commit
`5faa3d27cbaf522198ffa1bdcd11fa9d57341658`, preparation `173040`, the fixed destination, and the
two reviewed source digests. After checking that the historical root job is uniquely completed and
that its three reports are regular single-link files, it creates and retains a fresh read-only
`mktemp` bootstrap with exactly three directories and two files. The inline launcher is part of
the submission-hashed Slurm bytes. Under `python3 -I -B -S -` it stable-reads the staged CLI through
`O_NOFOLLOW`, checks full descriptor/path identity and its pinned digest, and compiles and executes
those same bytes as `__main__`. The CLI then independently verifies both sources and the exact
inventory, creates by no-replace publication, and a fresh process verifies the result again.

An executable adversarial test lets reviewed CLI bytes replace their own pathname: the already
read bytes finish, while the next invocation rejects the replacement before it executes. Missing
isolation, digest drift, symlink/hard-link aliases, and an extra inventory entry also fail. Twelve
new launcher/job tests and the 69-test WMI control plus sealed-preparation set pass locally. The job
has not been submitted; publication still waits for authoritative confirmation that `173040`
completed.

## 2026-07-30 — The first launcher repair was still not launchable evidence

Adversarial review found that closing execute-before-self-hash was necessary but not sufficient.
The first tracked job knew the historical manifest hash, yet did not independently anchor every
corpus file or any of the three reports. It treated an already published destination as a fatal
collision, so a crash after the irreversible seal rename but before the one-line report could not
recover. That report used shell noclobber rather than the reviewed staged no-replace primitive.
The job also selected ambient `python3` and had not exercised the target filesystem's actual
no-replace syscall. Those were blockers; the job remained unsubmitted.

Authoritative inspection supplied exact hashes for all twelve historical artifacts. They and the
known manifest are now literal job inputs and are rechecked before sealing and again through the
standalone module's copied-file inventory. The first authenticated report then arrived: the
1,254,810-byte, single-link dataset attestation has SHA-256
`4e1cf0d00725a739d6f371062ff2079cfb9bc3e36daf4f4219cbbe1399a68a12`, format
`peano-policy-dataset-attestation` v2, the expected manifest, independent replay, and prompt v3.
That digest is now pinned. At 09:13:57 elapsed the 1,350-byte, single-link token audit also arrived
with SHA-256 `c290b285eabcf9d39ab13b4d6f0f194588541484390d35c00681041979e2f8d8`.
It checked all 64,500 train rows and 6,000 capped validation rows; their maxima were 29,111 and
4,882 under the 32,768-token limit. That digest is pinned too. The runtime-smoke hash remains the
deliberately non-hex `PENDING_AFTER_173040_RUNTIME_SMOKE_SHA256` value. A validator reaches and
rejects that placeholder before `cd`, `sacct`, `mktemp`, the filesystem probe, or publication.
This is intentional executable evidence that the current tree cannot seal anything until the
remaining completed report is inspected; no digest was guessed.

The CPU job now activates the content-derived reviewed WMI environment, verifies its Python
identity, and runs the existing retained recovery-publication preflight directly inside
`checkpoints/corpora`. It first proves that this seal parent and the report parent under `logs`
share one filesystem device; a requeue then verifies the same report and live probe. Destination
classification precedes any read of the mutable historical corpus and reports. Those paths are
required only when creation is necessary. Otherwise a fresh isolated process verifies every
protected sealed file, all fifteen external anchors, the historical commit, and preparation job,
then enters a strictly verify-only report-recovery lane that still works after the originals are
retired. The canonical report is written and fsynced in a unique sibling stage, made `0444`,
fsynced again after the mode change, and atomically renamed without replacement. An existing report
succeeds only when it is protected, canonical, bound to the same Slurm job, and exactly recomputed
from the verified seal.

The underlying corpus module now rejects external hard links for every source and sealed regular
file, not merely duplicate inodes inside one directory. Executable tests create a complete minimal
corpus through the in-memory launcher, stop in the post-seal/pre-report crash window, and use a
second process/job identity to verify the existing seal and publish its report. Separate tests
cover same-job report replay, wrong-job rejection, retained-stage evidence after rename failure, and
external hard links. This remains local prelaunch work: one report anchor is still pending and
no WMI seal job has been submitted.

A second fresh review then caught a durability ordering mistake before launch. Payload bytes and
directory entries were fsynced while their staging modes were still `0600`/`0700`; `_protect_tree`
changed them to `0444`/`0555`, but those final inode metadata changes were not flushed before the
no-replace rename. The seal now fsyncs every protected regular file, both protected child
directories, the protected manifest, and the protected root before publication. The macOS test
path additionally fsyncs the root after its unavoidable post-rename re-protection. New tests prove
the protect → fsync → rename order, prove that a protected-tree fsync failure prevents publication,
and exercise the macOS post-rename target-before-parent order. The focused corpus/launcher set is
52 green after this repair; the production WMI path remains Linux and still unsubmitted.

The report-specific review found four more cases where a type annotation or an earlier read was
doing more rhetorical work than the runtime contract. A direct Python caller could pass `None` for
anchors described as mandatory; an existing exact report returned without freshly flushing its
inode and parent; its `0444` check was not bound to the inode later opened; and failure cleanup
could race a replacement or hide the primary error. Publication now validates commit, both job
IDs, the manifest digest, all twelve artifact digests, and all three report digests before touching
the seal. Existing reports follow verify → file-fsync → parent-fsync → fresh verify. The mode is
checked on the same stable-open inode whose canonical bytes are decoded. A stage is identity-
checked immediately before rename and the published inode is compared with the original stage
identity. Failed stages remain read-only evidence rather than being deleted by an inherently non-
conditional pathname cleanup. Tests cover missing runtime anchors, retry flush order, the old
mode-check replacement window, and stage replacement before rename. These remain prelaunch
corrections, not evidence that the transformer trained.

The same cleanup and late-path rules now cover seal creation itself. The final source-path check
compares mode and link count in addition to device, inode, size, mtime, and ctime; a hard-link or
permission transition after the descriptor was opened is therefore rejected even when the bytes
and timestamps are unchanged. If creation fails, its partial stage is retained instead of removed
through an unguarded pathname. New regression tests force the late link-count change and each
post-protection failure boundary. The focused corpus module is 43 green, and its exact reviewed
bytes are pinned in the Slurm launcher. This is still a fail-closed prelaunch state: the
runtime-smoke anchor remains pending, so the seal job cannot run.

At 07:55 elapsed, historical job `173040` was still healthy: the attestation had completed and the
token audit was active, with no token or smoke report yet. The final model output and seal
destination remain absent, while the pinned local Qwen snapshot is present. Because the replay had
already consumed more than seven hours, I tried to extend only its 12-hour Slurm ceiling to 18
hours; WMI rejected that operation with `Access/permission denied`, and no second attempt or
privilege workaround was made. The job remains unchanged and is being monitored. This is an
operational safeguard record, not transformer training evidence.

The post-seal readiness pass also exposed that the tracked v3 TOML is intentionally unfinished,
not merely conservative: its v3 run name has no `[curriculum]`, so the strict loader rejects it.
After the real seal exists, the only required source transition is the genuine seal digest plus the
already reviewed one-epoch, 70-million-token curriculum configuration and a static test that
actually calls `load_config`. No fake digest is being staged meanwhile. The downstream REPL,
proof-request, search, and trained-policy integration surface is 122 tests green; this verifies the
interface contract only, not a model artifact.

The token audit was authenticated and pinned while the historical job moved into its A100 runtime
smoke. Downstream jobs were deliberately not pre-submitted: the seal has no trustworthy runtime
report hash yet, the tracked training config cannot name a genuine seal digest yet, and the WMI
predecessor verifier is designed to reject such a chain. The safe preparation is complete instead:
only the final runtime hash remains to patch before focused/full gates, clean publication, and the
one-time seal job. At 10:39:58 elapsed the smoke was still active with 1:20:02 remaining. This
records staging readiness, not optimizer training.

Historical preparation `173040` completed at 10:54:30 with exit `0:0`. Its final single-link,
7,241-byte A100 report has SHA-256
`86cc35bfcf2d5ff51931c140f3eb7168e3f641e1f80d54a3984dba9e49e40749`, format
`peano-policy-wmi-a100-v3-smoke` v1, and `passed` status. It binds the historical clean source,
pinned Qwen revision, A100-80GB BF16 runtime, rank-32 LoRA, 34,865,152 trainable parameters, and
closed adapter/tokenizer save-reload evidence. The hash is now literal in the seal launcher, so no
report placeholder remains. The next evidence boundary is the immutable seal and its independently
read `content_sha256`; actual transformer training still has not started.

The fully anchored seal milestone is green before publication: 134 focused seal/WMI tests, 1,738
complete Peano tests with one intentional skip, and 360 Lambda tests plus 36 subtests pass. The
warning-as-error Jupyter Book build succeeds, and all 194 deep links, 47 sessions, and 287 commands
replay. Shell syntax, Python compilation, diff hygiene, and the standalone module's exact pinned
SHA-256 also pass. These gates authorize committing and deploying the one-time seal job; they do
not claim that the seal or trained adapter exists yet.

## 2026-07-31 — Ceph rejected `RENAME_NOREPLACE`; publication failed closed

The authenticated-seal milestone was committed as
`1757f1c38e54e86473757753c6d7ad4eac9f8da2` and pushed to `peano-lab`. Its clean tree was synced
to WMI and passed submission admission. Real CPU seal job `210942` then stopped after 26 seconds,
before copying or publishing the corpus. Ceph device 44 returned `EINVAL` for Linux
`renameat2(RENAME_NOREPLACE)` while the retained filesystem preflight tried to publish its
protected directory. The intended seal destination, seal report, and preflight report remained
absent. The protected source and sentinel remain under
`.recovery-publication-preflight-5c86ec1ac59ecf1f9c78066f63f4359c`; no cleanup or retry adopted
that evidence. This was the desired failure mode. It is not a seal and it is not model training.

A narrow live probe on the same Ceph filesystem established the missing fact: an exclusive empty
directory claim can be replaced by descriptor-relative plain `rename`, and the published path then
has the original staging inode. That result does not justify a directory-only patch. The seal
report, run identity, final training manifest, adapter/tokenizer trees, and recovery snapshots use
the same publication boundary, so both regular files and directories must be exercised and bound.

The replacement contract is publication-preflight v2. It probes both node types and selects one
profile for the whole run. Native `renamex_np(RENAME_EXCL)` or
`renameat2(RENAME_NOREPLACE)` remains preferred. On Linux only, and only when the native call
returns `EINVAL`, `EOPNOTSUPP`/`ENOTSUP`, or `ENOSYS`, the fallback exclusively creates a
type-matched canonical claim: `mkdirat` mode `0700` for a directory or
`openat(O_CREAT|O_EXCL)` mode `0600` for a file. It holds the parent and claim descriptors,
records and rechecks device/inode/type/owner/mode, requires an empty directory or zero-length
single-link file, fsyncs claim and parent, rechecks source and claim, and atomically renames the
complete protected stage over only that owned claim. The final canonical inode must equal the
staging inode and differ from the claim; the source must be absent; the parent is fsynced again.

This fallback is deliberately described more narrowly than native no-replace rename. The empty
claim is briefly visible, so existence is never completion evidence; all readers still require the
complete protected tree or canonical report. A crash can leave a durable empty claim and private
stage that require manual audit. Neither is deleted or automatically adopted. The final rename is
atomic, but the claim protocol is not a hostile-same-UID security boundary: a malicious process
with the same filesystem identity could swap the claim after its final check. Peano's documented
non-hostile-same-owner premise excludes that actor.

The verified profile is now threaded rather than renegotiated: the WMI seal job extracts it from
the retained v2 report and passes it to both seal and report publication; scheduled training binds
the same report into its run identity and passes the profile to run-identity, recovery-snapshot,
adapter, tokenizer, and final-manifest publication. A forced native profile fails if its syscall is
unsupported; it never silently changes protocol. The local macOS suite exercises native behavior
and the regular-file claim state machine. Linux-only directory-claim tests run in Linux CI and the
next live Ceph preflight, because APFS refuses plain rename of the protected `0555` staging root.
No new seal job is submitted until this repair is reviewed, fully green, committed, synced, and
accepted by the test-only WMI gate. Actual optimizer training remains unstarted.

A final semantic audit found one inaccurate sentence encoded as data rather than prose: seal-report
v1 always claimed `atomic_no_replace: true`, even when the selected Ceph profile atomically renamed
the stage over its own exclusive empty claim. The report is now v2. It binds the admitted profile,
both exercised node types, native destination-no-replace versus type-matched claim semantics, the
claim's transient visibility, and the same-owner threat model. Report publication requires the
profile, selects its exact low-level branch before any namespace mutation, forbids renegotiation,
and rejects an existing report under a different profile. Tests cover native and claim records,
both retry directions, forged profile/boolean fields, JSON numeric type aliases, and forced-native
failure without fallback. Strict v2 validation is necessary because Python otherwise equates
JSON `1` with `true` and `2.0` with `2` during ordinary dictionary comparison.
This correction happened before a second live seal attempt; optimizer training is still unstarted.

The repaired publication boundary closes its local gate with 203 focused tests passing and four
intentional Linux/Ceph-only skips. The complete Peano suite is 1,761 passed with five skips; the
Lambda sibling remains 360 passed plus 36 subtests. A forced warning-as-error rebuild covers all 38
book sources, and the executable-book audit replays 194 deep links plus 287 commands in 47 sessions.
Shell syntax, Python compilation, and diff hygiene pass. The standalone seal CLI SHA-256 is
`0b391513878c5fa333505a4e01049611fabbd091f11384c08462d6241604cc5d`; the reviewed corpus
module SHA-256 is `751a759bc7916a72b26f03b8c32502cc802de78565ec149b1136f9c1562711d7`, and the WMI
launcher pins both literally. These are predeployment results; the fresh live Ceph preflight and
the authenticated seal are still pending, so optimizer training remains unstarted.

## 2026-07-31 — Genuine model-v3 corpus seal published

The Ceph repair was committed as `84943ca1a5653542f117d519dddf1fa2906259a0`, pushed to
`peano-lab`, and deployed as the same clean Git tree. Test-only admission succeeded, and real CPU
seal job `213641` completed `0:0` in 7m01s. Its live publication-preflight v2 exercised both a
protected directory and regular file on Ceph, selected
`exclusive-type-matched-claim-rename-v1`, and retained the passing probe. The canonical preflight
report SHA-256 is `c29c1b4b742621dc45e469f9c2f586e2cc3e431a9d378f455ddded985994decc`.

The published 15-file seal is
`checkpoints/corpora/peano-policy-v3-173040`. Its content SHA-256 is
`7b22bdf083894e3d87b84fc463ff537a75eeecba8e34098429db215592ec6b5b`; its `seal.json`
SHA-256 is `22ecb4ad16f06abc39d6aac553052be9fa08b195d9250216fa1195db0a7e49e6`. The
profile-bound v2 verification report has SHA-256
`218d3a16f582c460dd93a01eb809d157dc9a55a09357d6c24f16f74cda9b1c3e` and truthfully records
`atomic_destination_no_replace: false`, an exclusive type-matched claim, and transient destination
visibility. A separate current-source verifier reproduced the exact content digest after Slurm
reported completion; stderr was empty.

This real digest, never a placeholder, now enters the reviewed one-epoch model-v3 configuration.
The run removes row-level train subsampling, uses the sealed train/validation paths, caps the
deterministically selected curriculum at 70 million train tokens and 2 million evaluation tokens,
keeps the 32,768-token context, raises proof generation to 1,024 tokens, and forbids resume into an
old output. This is the single planned post-seal source transition. It still is not transformer
training: sealed A100 preparation and the real optimizer job remain subsequent evidence boundaries.

The post-seal launch-contract selection passed 152 focused tests with one expected skip. The final
complete Peano suite passed 1,761 tests with five expected skips in 24m16s. The earlier clean Ceph
repair commit also passed all 360 Lambda Lab tests plus 36 parametrized subtests; this post-seal
transition changes no Lambda Lab source.

## 2026-07-31 — The measured curriculum exceeded the linear token ceiling

Current-source sealed-preparation job `214264` ran on one A100-SXM4-80GB and first accepted the
immutable corpus eligibility gate. Its exact selected-curriculum scan then counted 73,446,475 train
tokens and failed closed against the reviewed 70,000,000-token ceiling after 1h58m16s. Because
linear exposure is the first aggregate check, no accepted token-audit report was published; the
runtime smoke, model load, optimizer, adapter publication, evaluation, and replay did not run. The
job-specific eligibility report and terminal logs remain evidence of the rejected attempt and are
not valid predecessors for a retry.

The selector itself is independently reproducible without tokenization: it admits 20,765 rows,
comprising 8,494 catalog rows and 12,271 synthetic rows across 5,712 synthetic sessions. Seventeen
synthetic row slots remain unused because the next balanced whole-session round does not fit. With
microbatch one and gradient accumulation 32, this fixes the planned one-epoch schedule at 649
optimizer updates; it does not show that any update has occurred.

The correction is intentionally smaller than changing the curriculum or broadly relaxing its
compute contract. `max_train_tokens` becomes 74,000,000, leaving 553,525 tokens (about 0.754%)
above the deterministic observation. The 12,288 synthetic-row ceiling, 32,768-token context,
2.3-trillion train squared-token ceiling, evaluation ceilings, 1,024-token completion ceiling, and
single epoch remain fixed. This is enough without changing the quadratic limit: the historical
full-population audit used the same immutable rows and tokenizer, `data.py` is unchanged, and its
maximum was 29,111 tokens. Thus the selected schedule satisfies the conservative upper bound
`29,111 * 73,446,475 = 2,138,100,333,725`, still below 2.3 trillion. A new clean commit, one fresh
deployment, and a new preparation job must repeat all gates and publish all three reports before
training can be submitted. The proof is in the new artifacts, not in this calculation.

The reviewed 74-million transition is green locally. The focused curriculum, token-audit, sealed-
preparation, and WMI-control set passes 123 tests; the documentation subset passes 36; the
warning-as-error Jupyter Book build, executable-book audit, and 248-lemma knowledge-base/vault
checks pass. The complete Peano suite reports 1,761 passed with five expected skips in 23m39s, and
the unchanged Lambda sibling reports 360 passed plus 36 subtests. No kernel or tactic semantics
changed, and no replacement WMI job had been submitted when these results were recorded.

## 2026-07-31 — A correct adapter was compared through two different forwards

The 74-million-token retry, WMI job `217123`, established that the ceiling correction was enough.
It published a passing audit for the exact 20,765-row selection: 73,446,475 train tokens,
415,247,631,205 squared tokens, a 29,111-token longest sequence, and a 936-token longest
completion. It then exercised the extremal LoRA updates and one real `CompletionOnlyTrainer`
optimizer step and evaluation. The run nevertheless failed closed after 3h58m16s, before the
runtime-smoke report was written, with “fresh adapter changed indexed loss or projected logits.”
No production training job was authorized.

The placement of that exception was decisive. Admission had already compared every canonical
LoRA tensor in three places: the terminal in-memory PEFT state, the saved safetensors, and the
freshly populated PEFT model. Names, dtypes, shapes, and raw bytes all agreed. The failure was not
evidence of a lost or corrupted adapter; it was evidence that identical weights had been executed
under different wrappers.

Transformers delegates BF16 preparation to Accelerate. In the pinned Accelerate 1.8.1 runtime,
`prepare_model` mutates the same model object: it stores `_original_forward`, installs an autocast
forward, and converts returned BF16 tensors to FP32. The smoke's real-Trainer probe deleted its
Trainer but never unwrapped that forward. The in-memory admission snapshot therefore hashed FP32-
converted outputs from the prepared path. The newly loaded PEFT model had the ordinary bare
inference forward and returned native BF16 indexed logits. Because the admission fingerprint
deliberately includes dtype and every raw projected-logit byte, rejection was inevitable.

The tempting response would have been to weaken exact equality to `allclose`, argmax agreement, or
a loss tolerance. That would hide the lifecycle error and make it harder to distinguish a genuine
semantic drift later. Instead, smoke and production now call Accelerate's public `unwrap_model`
with `keep_fp32_wrapper=False` and `keep_torch_compile=False`. The helper requires the same model
object, verifies removal of `_original_forward`, and verifies restoration of the original forward
function. Snapshot capture independently refuses a retained wrapper. Tests simulate the mutation,
prove the explicit flags and identity checks, and keep all existing exact tensor/output and
adapter-effect gates unchanged. The canonical comparison is now bare trained inference versus
bare freshly loaded inference---the same path used by the proof service.

The repair is green locally. The direct adapter/smoke regression set reports 73 passed with one
expected skip; the wider sealed-preparation and documentation selection reports 140 passed with
one skip. The complete Peano suite reports 1,764 passed and five expected skips in 24m09s, while
the unchanged Lambda sibling reports 360 passed plus 36 subtests. The warning-as-error Jupyter
Book, all 194 deep links and 47 executable sessions (287 commands), the 248-entry arithmetic
knowledge base, and the 327-note/3,288-link vault pass. The next claim must come from a fresh WMI
smoke report, not from these CPU tests.

## 2026-08-01 — A completed proof obligation is not a live scheduler edge

Fresh sealed-preparation job `217768` supplied the missing machine evidence. It completed in
3h53m05s on an A100 and passed eligibility, the exact token audit, representative LoRA updates, a
real Trainer step and evaluation, restored-bare-forward admission, and a fresh local-only reload.
The independent verifier accepted all three terminal reports. The smoke losses were finite
(`2.7942631244659424` for training and `0.8226498961448669` for evaluation), but they are only
one-step lifecycle diagnostics. They say nothing yet about the production adapter's proof ability.

The next dry-run failed before allocation with Slurm's “Job dependency problem.” That initially
looked surprising: persistent accounting still said exactly
`217768|COMPLETED|0:0|0:0`. The important distinction is that WMI's controller retains a completed
job for only `MinJobAge=300` seconds. Slurm permits a new `afterok` attachment only while the job is
active or remains in that controller window. `sacct` is durable evidence of successful completion;
it is not evidence that the controller can still construct a dependency edge.

I chose to make the distinction explicit rather than retry after failure or silently reinterpret a
flag. `--afterok JOB` now means a live scheduler dependency and accepts only `PENDING`,
`CONFIGURING`, `RUNNING`, or `COMPLETING`. `--completed-predecessor JOB` means a durable completed
handoff. It accepts only one exact allocation row for that numeric `JobIDRaw`, state `COMPLETED`,
ordinary exit `0:0`, and derived exit `0:0`; duplicate rows, steps, arrays, truncation, malformed
fields, missing accounting, and every unsuccessful state fail closed. Training requires completed
mode. Evaluation can use live mode while its producer runs or completed mode afterward.

The new mode changes the scheduler argument and strengthens accounting admission; it does not change
the logical producer identity. That predecessor remains in `PEANO_PREPARE_JOB_ID` or
`PEANO_TRAIN_JOB_ID`, the historical `dependency_job_id` ledger column, the same-source predecessor
row, the composite job/helper digest, and every report/runtime cross-check. Real submission re-reads
accounting immediately before `sbatch --hold`, appends and fsyncs the new ledger row, and only then
releases the held job. This is a small but useful systems lesson for students: a durable proof that
an event happened and a live mechanism that waits for the event are different objects, even when
an early prototype calls both a “dependency.”

There is one intentionally expensive consequence. The guarded predecessor verifier joins both jobs
to the exact clean deployed commit and synchronization timestamp. Committing this control fix changes
that identity. Therefore I cannot use `217768` after deployment merely because the training payload
looks unchanged; doing so would silently weaken the chain we built. The next run must be another
sealed preparation from the fix commit, followed by training without an intervening source sync.
Four hours of repeated machine evidence is cheaper than teaching that provenance may be waived when
it becomes inconvenient.

The audit also caught a completely separate arithmetic error in the launch contract. Early tests
used a synthetic 20,782-row fixture, which gives 650 updates at accumulation 32. The sealed selector
actually admits 20,765 rows, so production gives
$\lceil 20{,}765 / 32 \rceil = 649$. The old preflight would reject 649 because its ten-step logging
interval did not divide the schedule. Removing that invariant would lose the dedicated periodic
loss record at the terminal optimizer update. Instead, production logging moves from 10 to 11:
$649 = 11 \times 59$. There are now exactly 59 periodic records ending at step 649, followed by the
training and evaluation summaries at the same step. The 33-step warmup, six recovery snapshots at
100 through 600, batching, objective, and optimizer remain unchanged. A regression runs the real
production config against the measured row count so the pleasant 20,782-row fixture cannot hide this
boundary again.

The final local gate passed 1,769 Peano tests with five expected skips and all 360 Lambda tests plus
36 subtests. The warning-as-error book rebuilt all 38 sources; 194 links, 47 executable sessions,
and 287 commands replayed; the 248-entry arithmetic knowledge base and 327-note/3,288-link vault
verified. A copied-root fake-Slurm harness executes the real guarded submitter without weakening its
fixed production root. It proves both predecessor modes, exact environment/ledger binding, two
accounting reads, rejection of bad or changing state, and held-submit → durable append → release
ordering. These gates authorize one clean deployment and a fresh preparation, not a claim about a
trained policy.

## 2026-08-01 — A training window should be a window, not a control panel

Fresh sealed preparation `217851` completed the post-submission-fix proof obligation under clean
source `4d44609e`, so same-source production job `217859` could finally begin the 649-update
Qwen3-1.7B LoRA run. I wanted a live browser view, but “direct log fetching” contains an important
authority trap: JavaScript cannot read SSH logs without either receiving credentials or being
given a general remote-command proxy. Neither belongs in an observational teaching tool.

The implemented boundary is intentionally narrow. A standard-library Python server listens only
on `127.0.0.1`. One background thread executes one reviewed read-only SSH program at a time. That
program knows a fixed WMI root, fixed Slurm queries, fixed artifact names, byte ceilings, and a
validated decimal job ID. The browser receives only a sanitized JSON projection and fixed local
assets. There are no write, upload, cancel, submit, signal, arbitrary-command, or arbitrary-path
routes. A last-good cache means a lost VPN produces an honest stale view instead of a blank screen
or a false live badge.

Two missing values forced better interface language. First, Transformers progress uses stderr and
arrives immediately, whereas its Python dictionary logs are block-buffered in redirected stdout
for this already-running job. A tempting chart could interpolate loss from progress or display the
preparation smoke as if it came from production. Both would be lies. The chart accepts only exact
flushed logging records or final-manifest evidence. Until then it says “awaiting,” while the
one-step preparation loss is named *admission smoke* and described as an infrastructure diagnostic.

Second, the Trainer shuffles the corpus and is configured to aggregate up to 32 microbatches per
optimizer update; this run's final partial window contains 29. From
the files we can show representative admitted examples, but not the exact current row. The corpus
inspector therefore says precisely that. It previews theorem, formula, focused proof state,
available-library names, and hides the supervised next tactic behind an explicit reveal button.
This is pedagogically nicer too: a student can predict the next action before comparing it with the
training target.

The visual language follows Peano Lab itself: deep navy instrument panels, cyan structure,
emerald verified/live states, monospace proof surfaces, a phase rail, native progress, an SVG loss
plot with an accessible table, recovery evidence, run provenance, GPU telemetry, and bounded live
logs. Polling slows when the tab is hidden, overlapping reads are forbidden, remote values use
`textContent`, and reduced-motion/high-contrast/mobile layouts are explicit.

The focused contract currently reports 25 passes. It covers adversarial parser inputs, strict host
and job validation, bounded response sizes, stale-cache preservation, loopback and GET-only HTTP,
fixed routing, security headers, self-contained assets, JavaScript syntax, accessibility, and the
two honesty labels above. The dashboard makes training legible; it does not move the soundness
boundary. The model may later suggest proofs, but only independent kernel replay can turn one into
a theorem.

A final review found that the same honesty rule applies to the Refresh button. The HTTP response to
a refresh request may still contain the previous cached snapshot while the serialized SSH read is
running. The interface now waits for `fetched_at` to advance instead of flashing “Live” immediately,
allows sixty seconds because a requested twenty-five-second read may queue behind another such
read, and queues a click that arrives during an automatic browser poll. This small state machine is
preferable to pretending that a request and its eventual observation are the same event.

## 2026-08-02 — Three checked scripts do not make an incomplete report identity complete

The production adapter from job `217859` was ready, so I ran the frozen trained/base comparison
without bypassing the evaluator's single-owner rule. Trained job `218171` completed in 3m51s. Only
after it finished did the guarded watcher submit revision/configuration-pinned pretrained job
`218172`, whose report declares no PEFT adapter and which completed in 4m20s. The two GPU stages
therefore took 8m11s sequentially.

Both reports are bound to source `4d44609ee32d5d28726c082ef7b5649c0a1107a6`. The untouched
trained report has SHA-256
`f134f8c2d8c173e2ebcee0ebd3b8dfbc59805619bd7e79706c11e51732e0956c`; the untouched base report
has SHA-256 `410be8f224d2dac6d28c4e0f55f125e95d5bc1f725b9c20851b00c15394d97b9`.

At first glance the result was exciting. With `k=1`, the trained report claimed three of four
goals, while the pretrained comparison claimed none. The successful trained routes were small
tactic programs:

- `norm_num` for the closed arithmetic formula, producing a 98-node certificate;
- `exists 5` followed by `norm_num`, producing 29 nodes; and
- `intro n`, `rewrite PA3`, `simp`, producing 10 nodes.

I replayed each route independently through `verify_proof` under the actual model-v3
`SurfaceCapabilities`; all three certificates check against their original goals. The fourth
formula, `forall x. exists y. x * (x + 1) = 2 * y`, was the only genuinely induction-heavy item and
remained unsolved. The base produced 32 malformed candidate strings and executed no tactics. The
defensible pedagogical hint is therefore much narrower than “the model proves PA”: in this tiny
raw comparison the adapter emitted executable syntax and shallow compositions, but it did not
demonstrate induction planning or establish a stable causal effect.

Then the independent report replay rejected the trained JSON. The evaluator really had rendered
prompts with the full 247-theorem environment, and the report separately recorded all 247 allowed
names. However, `PeanoPolicyAdapter.evaluation_identity` placed the older reduced
`policy_environment` object inside `base_policy_identity.environment`. That projection contains
only the common surface fields. It omitted the four model-v3 library-prefix fields required by the
exact authority: `library_identity_sha256`, `library_full_identity_sha256`,
`library_prefix_length`, and `library_size`.

This distinction matters. Kernel replay answers “are these three scripts proofs?”—yes. Canonical
report replay also asks “is this entire measured condition exactly the registered condition?”—not
from the serialized identity. A sound kernel result cannot repair missing scientific provenance.
The correct response is to keep both original reports immutable, keep the ordinary verifier
strict, and quarantine the raw 3/4-versus-0/4 comparison.

The planned recovery is a separate compatibility attestation, not a permissive branch in the main
replayer. It must accept only this exact historical report/source/job, require the recorded legacy
environment to equal the exact projection of today's trusted full authority, pin the four omitted
values and historical source inventories, independently replay every claimed proof, and publish a
distinct non-replacing attestation that hashes the untouched input. Until that artifact exists, I
record only the raw score and the three independently kernel-valid scripts. I do not record an
accepted pass rate, a causal theorem-proving result, or induction capability.

## 2026-08-02 — The narrow bridge passed without teaching the ordinary verifier an exception

The recovery described above is now complete. It was deliberately implemented as a distinct,
version-pinned historical admission rather than a conditional inside the canonical replayer. The
ordinary trained-report replay still rejects the missing environment fields, the immutable report
bytes are unchanged, and future reports must serialize the full authority.

`trained-compatibility-replay.json` accepts only the exact job-`218171` report and historical
source identity. It proves that the recorded four-field object is exactly the legacy projection of
the pinned complete model-v3 authority, reconstructs the four omitted library fields, binds the
historical evaluator inventories, and independently replays every reported proof. The admission
passed with 3/3 proof claims replayed. Its embedded attestation SHA-256 is
`e900a10241db0451992313eb2a7b0341911a7a71cd8af91e831a279874afda56`.

The zero-proof control needed its own evidence rather than inheriting credibility from the trained
bridge. `pretrained-base-replay.json` validates the declared pretrained identity, comparison
provenance, goal and search budgets, duplicated accounting, and the absence of any proof claim. It
passed with embedded attestation SHA-256
`056519bc3598a390526fdf9054aa38090d499f7f837af0a2ace7af8caaa560e7`.

I can therefore admit one carefully scoped result: on the frozen four-goal launch smoke at `k=1`,
the trained adapter solved 3/4 and the revision/configuration-pinned pretrained comparison,
reporting no PEFT adapter, solved 0/4. That sentence must travel with its limits. Three proofs are
shallow; the only induction-heavy goal is still unsolved; four
problems cannot support a statistically useful pass rate; and a single paired run does not prove
general PA ability, induction skill, or causal superiority. The deterministic baseline, larger
hidden induction-rich suite, and repeated measurements remain the next scientific work.

## 2026-08-02 — Pairing the producers exposed the last missing kinds of evidence

The two producer admissions were necessary but did not by themselves prove that their conditions
formed one comparison. The final paired attestor therefore consumes both reports and both producer
attestations together with the exact training manifest. That manifest has SHA-256
`caa5569c98ed9ea048d413301b803c39011957d1c97307e5b109846989e18569` and records 649 expected and
649 actual optimizer steps. The paired layer also equates source commit, training and evaluation
jobs, goal set, seed, and every search limit.

Historical source attribution is now explicit Git-object verification rather than trust in copied
path/hash maps. The attestor checked 36 trained-semantic entries, 36 pretrained-semantic entries,
61 trained-evaluation entries, and 62 pretrained-evaluation entries. Their union contains 62 unique
source blobs, and every overlap agrees. The resulting
`paired-launch-smoke-attestation.json` passed with literal result
`paired_launch_smoke_admitted`. Its embedded attestation SHA-256 is
`9b33b4e488f14e38fc7c5a122410d53e9e1123409dcccafdc73e0a8ab1a14bae`; the complete file SHA-256 is
`cdd20cc6e97ff442cff1c476135963f726b740372223f6eac72335543f6c11ba`.

This extra scrutiny also corrected an overly strong phrase: “exact pretrained base.” What the
records establish is a revision/configuration-pinned pretrained comparison whose report declares
that no PEFT adapter was attached. They did not hash the resolved base weight shards before and
after loading, so they do not establish bit-for-bit base-weight identity. That is a concrete future
gate: bind the repository/LFS identity and ordered shard hashes, then stable-hash every weight file
on both sides of model execution.

The second missing object is the raw generation transcript. The immutable reports retain outcomes,
commands, search counters, and certificates, but not every model call's raw text, deterministic
extraction result, attempted action, and executed edge. The paired layer therefore cannot replay
the whole model-output-to-search-frontier derivation. It attributes candidates through
byte-pinned historical producer/source/job records, while the consumed trained attestation
independently kernel-checks the three published certificates. A stronger benchmark should retain
and hash the complete per-call transcript.

Finally, the retained `sacct` and WMI log bundle observe successful completion of jobs
`217859`, `218171`, and `218172`, but the scheduler does not cryptographically authenticate those
records. They are useful operational evidence, not a signature. None of these limits revoke the
narrow `k=1` observation, 3/4 versus 0/4. They do forbid stronger language: no bit-for-bit base,
causal effect, statistical solve rate, broad PA ability, or induction capability has been shown.

## 2026-08-03 — Design the experiment before admiring the hybrid

The next idea is genuinely exciting: give Peano Lab several exploratory heads.
A native prover can perform dense, reliable closure. Vampire or an SMT solver
can expose useful clauses or instantiations. A cheap learned ranker can guide
the inner loop. Qwen can propose witnesses, induction motives, cuts, and
premise bundles. Codex can help author and inspect development data. Yet none
of these components should acquire even a sliver of theorem authority. Every
route must return to the same original-goal kernel check.

The first useful correction was logical, not computational. Full standard
Heyting arithmetic is undecidable. We may isolate and justify a restricted
decidable fragment, but a bounded search over a friendly exercise collection
does not make HA decidable. The binding Hydra design therefore distinguishes
`proved`, certified `not_theorem`, and `unknown`. If we cannot independently
justify negative answers, we will build a sound semi-decision theorem prover
and say exactly that.

The second correction was experimental. Our 247 checked theorems are wonderful
training material and terrible hidden tests of themselves. Hydra freezes them
as an ordered library epoch, then seals evaluation by mathematical lineage
before tactic rows are generated. A new quadratic-reciprocity development
would enter a later epoch. If reciprocity is to be a test, its statement must
be deposited before the proof is written, and the complete route—definitions,
intermediate lemmas, variants, scripts, teacher sketches, descendants, and
dependent retrieval entries—must be masked. A name mismatch is not
independence.

The architectural bet is the critical frontier. Deterministic closure runs
until it stalls; only then may a model make one sparse semantic choice through
a typed macro that compiles back to ordinary Peano commands. This gives the
student a learnable interface without inventing a second proof language. It
also gives us honest ablations: retrieval, clause ranking, a pretrained model,
SFT, value search, and expert iteration must each earn their place.

Finally, we preregistered how enthusiasm can be falsified. A teacher solving
DEV problems shows interface headroom, not student ability. The old four-goal
Qwen smoke remains a smoke. The final set opens once, after the strongest
symbolic baseline and all resources are frozen. Full Hydra must beat both that
baseline and the strongest non-generative learned system by the registered
margin at adjacent budgets with paired statistical support. If it does not,
the result is “no demonstrated LLM advantage under these budgets.” That
sentence would still be a worthwhile scientific outcome.

## 2026-08-03 — Make one known route cross every boundary

The first implementation question was intentionally smaller than “can the
model prove arithmetic?” We needed to know whether several fallible explorers
could share a state, propose bounded actions, and still return to one original-
goal authority without acquiring hidden proof privileges.

The resulting Hydra core lives beside the training code, not in the kernel or
tactic engine. Each head declares the same logic and exact tactic/theorem
capabilities. Quotas are fixed before search; results are merged in stable
order without borrowing an unused slot. Expensive heads can be gated by the
hash of the complete canonical goal tuple, but the full tuple is retained and
compared, so the hash is only an index. A recorded script, Qwen adapter, future
Codex client, or external prover wrapper is therefore just an untrusted source
of ordinary surface lines.

I resisted the tempting shortcut of trusting the first successful search.
Search already checks a terminal certificate, but Hydra starts once more from
the original formula through the traced headless runner. Publication requires
agreement on the canonical theorem, every physical command, classical mode,
surface authority, and proof size. This second path also gives the experiment
a durable transcript. A failed provider is scientifically important but not a
new logical failure mode: another head may still find a sound checked proof,
while the row is marked degraded and removed from matched comparisons.

For the first end-to-end example I reused the readable proof that consecutive
products are even. The symbolic head is genuinely state-independent, but one
candidate was not enough. Plain `compact_arith` closes the base and final
equalities; the induction-step equality needs the visible premise, so the
fixed tuple also enumerates `compact_arith [IH_witness]` at every state. That
detail is pedagogically valuable: even “symbolic closure” needs a premise-
selection policy. It is also why the experiment remains an oracle plumbing
test—the contextual choice was selected with the known proof in view.

Both lanes receive those two candidates and one further slot. In the control,
that slot is an identified null head. In the hybrid, a checked transcript
provides only the ten structural actions (`have`, induction, witnesses, cases,
specialization, a local sufficiency cut, rewrite, and exact) at their exact
states. The control exhausts at the root. The hybrid reconstructs all thirteen
commands and the independent replay checks the same 180-node certificate. A
mutated statement with an odd right-hand side activates no structural state;
its exhaustion is recorded only as transcript non-reuse and `unknown`, never
as a non-theorem proof.

This tiny loop tells us the plumbing is real. It says nothing yet about Qwen,
Codex, Vampire, a strong symbolic portfolio, or unseen mathematics. The next
honest step is to freeze the semantic profile and library epoch, build a real
symbolic DEV frontier, and ask whether a teacher can close enough of that
frontier through the structured macro schema to justify training.

The independent implementation review caught one label that was too
permissive: a clean bootstrap run had been marked comparison-eligible. That
was stronger than its evidence. I separated runtime degradation from campaign
eligibility, rejected omitted provider identities, and made every
surface-macro-v0 row explicitly ineligible. The current ledger sees extracted
tactic lines, not raw decoder text and resource records, while its state gate
comes from the teacher transcript rather than an independently detected
symbolic fixed point. These are now recorded requirements, not hidden debts.

## 2026-08-03 — Freeze the meaning before scaling Hydra

H0.1a forced us to name the object that every later experiment will share.
The new `peano-lab-ha-intuitionistic-v1` profile records the exact syntax,
de Bruijn binding, capture-avoiding substitution, intuitionistic proof rules,
PA1--PA6, unrestricted induction, canonical target form, translations, and
evidence boundary. Its semantic digest is
`058b1644b066967919dae092e5e562b8845e4dd8415fff31d7cd209d51bc9e43`.
The loader rejects duplicate keys, non-canonical bytes, any mutation of the
registered value, and drift between its axioms/constructor inventory and the
live kernel.

The most useful bug came from asking what “closed” really meant. Parsing
`#0 = #0` creates no *named* free variable, so the old names-only check let it
reach reflexivity. The kernel's open-variable reading was sound, but Hydra had
promised closed top-level targets. We now traverse the term tree at binder
depth zero and reject explicit de Bruijn target syntax. This is a good example
of why a semantic profile must constrain representations, not merely list
connectives.

Policy, runner, and pilot carriers moved to version 2. Profile identity is
separate from tactic/library capability identity. It is present in heads,
proposal records, recorded states, provider identities, runs, replay IDs, and
the pilot outcome. A legacy checked batch is replayed again under a
profile-bound identity before it can become a recorded policy; it is never
merely relabeled. A successful run is replayed once during search finalization
and again when serialized, so mutating its retained request, commands, or
trace fails closed.

I initially let the phrase `evidence_kind = proved` suggest more than the
pilot retains. Worse, I called a list of required field names a frozen schema
without defining types, additional fields, or non-self-referential hash
preimages. The profile now labels this honestly as `required-field-draft`.
Pilot v2 declares conformance false and remains comparison-ineligible.
Historical pilot v1 is byte-pinned and explicitly pre-profile; pilot v2 is the
profile-bound regression. Exact evidence syntax is H0.1b.

The final adversarial review found another distinction worth teaching:
`@dataclass(frozen=True)` freezes attribute assignment, not dictionaries stored
inside the object. Provider metadata, proposal rows, and limits could be edited
after a run, and the serializer would detach and bless the edited values. Even
the comparison flag could be flipped. Runner v2 now retains a canonical binding
of the original publication fields, validates every head and proposal against
the declared portfolio, reconstructs `SearchLimits` and degradation, restricts
statuses to `proof | exhausted | limit`, and requires the exact fixed
surface-macro-v0 ineligibility reason. Head identities now include the complete
declaration and capability environment. We also moved the existing input-size
and numeral guards before semantic parsing. These are provenance fixes rather
than kernel rules, but without them an honest theorem could be attached to a
dishonest experiment row.

One final Python 3.12 probe exposed a subtler preflight bug. Converting a
5,000-digit decimal literal to `int` hits Python's defensive digit limit before
our own numeral ceiling can report the input. The numeral guard now compares
normalized decimal strings lexically, so it is total across the complete
8,192-character transport envelope and still runs before parsing. At the same
boundary we made proposal ledgers state the only histories the implementation
can actually produce: a successful or failed call requests its full fixed
quota, a contract error happens either before that call or during it, and an
unsuccessful row cannot invent returned candidates or suppressed duplicates.
These cases now have direct regression tests rather than relying on the pilot
to happen not to exercise them.

Because the numeral guard is shipped to the browser, this small source change
correctly invalidated Peano Lab's application manifest. The failing integrity
test prevented an easy mistake: serving new Python below an old immutable URL.
I regenerated the complete manifest, advanced the application namespace to
`a-4f03b6fb429b`, and advanced the visible build label to `2026-08-03c`.
No deployment is implied by this branch; it simply keeps the release tree
content-addressed and ready for the normal promotion process.

A later parallel review found that merely *running* the input guards before
parsing was not enough. Their values still lived outside the semantic object,
so changing 8,192 or 256 could change the admitted theorem set while leaving
the profile digest untouched. The final profile therefore includes an
`operational_admission` record for every preflight rule and checks its numeric
ceilings against the live browser surface. It labels those limits
`decision_claim = false`: they bound transport and construction, not the
mathematics. The same review made the shift cutoff under `∀` and `∃` explicit,
removing an ambiguity from the prose substitution rule. Regenerating the
profile-bound pilot after this correction was mandatory; attaching its old
hash would have recreated exactly the relabeling error the profile is meant to
prevent.

This completes the H0.1a semantic/claim substep only. H0.1b exact evidence
schemas remain open. There is still no decidable fragment or `not_theorem`
result, no independent reference implementation, no 1,000-case conformance
set, no double cold replay of a frozen library epoch, and no typed H0.3 macro
protocol. The old Qwen prompt is rejected by Hydra because it does not expose
the new profile digest; adding a real profile-aware prompt is future work, not
a hash pasted onto an unseen model input.

## 2026-08-04 — Make the checker do less, not trust less

The four-hour validation session was not blocked on agents or a GPU. A few
Cut-heavy arithmetic tests repeatedly reconstructed and checked enormous
dependency closures, while the byte-balanced CI sharder accidentally grouped
several slow files together. Before translating the kernel to Rust, I profiled
the existing small Python checker. The largest hot path was surprisingly
mundane: every term binder eagerly shifted every formula in its context.

The replacement keeps a per-hypothesis pending-shift count. Entering a binder
increments integers; selecting `Hyp(i)` performs the one composed shift that
the eager checker would eventually have produced. New logical hypotheses
start at the current depth. In particular, `ExistsElim` shifts the old context
but not the newly opened existential body. Seven focused tests exercise this
invariant and reject the corresponding capture, swapped-index, and off-by-one
mutations.

For the unchanged 73,767-node FTA certificate, five baseline final checks had
median 4.338 seconds. After the final exact-dispatch hardening, five
lazy-context checks had median 0.451 seconds, a 9.6-fold improvement. A
cache-cleared FTA library replay fell from 57.497 to 29.241 seconds. The
smaller end-to-end gain is useful evidence: kernel
checking is important, but certificate construction and repeated surrounding
passes remain real costs. The new benchmark harness therefore reports cold
replay, one extra original-goal check, and proof metrics as separate
observational phases; it never turns wall time into proof authority.

Rust remains worthwhile as an independent native/WASM shadow checker, but it
will begin behind the Python authority. A language rewrite must not disguise
an algorithmic mistake, and no Rust `ACCEPT` may grant QED until the binding
design is explicitly amended after differential Python/Rust/Lean validation.

The semantic acceptance check was deliberately stronger than a fast smoke.
Two same-process cold passes cleared both theorem caches, reconstructed all
384 public certificates, and produced the identical receipt
`cee5f55c9801b8698a18a0795c06d2ae0455b49dbb7325f71aeb0c7093c20ef3`.
The fused structural/identity traversal also matched the old two traversals on
1,000 generated shared proof DAGs. This let us optimize the tactic commit gate
without changing its node, depth, object, edge, or reuse policy.

The first runtime-weighted eight-shard local run completed in 8 minutes 24
seconds of wall time. Six shards were green immediately. One source failure
was an honest stale seal: the immutable browser manifest still named the
pre-optimization checker and therefore required a new content address. The
other exposed a mistaken test assumption. The frozen trace corpus correctly
named the checker from its producing commit, but its test had compared that
historical hash to the live tree. The corpus did not receive a new identity:
its README already says that it is a frozen 247-theorem release made at commit
`64893e13bd25bd9169f41f118a6483b426e1a962`. Its test now verifies the recorded
source blobs at that producing commit instead of incorrectly requiring those
historical hashes to equal the live tree. Rewriting the corpus provenance
would have been easier and false. The remaining loopback-server failure was a
sandbox socket prohibition and passed unchanged when run with permission to
bind `127.0.0.1`.

The Rust experiment then became concrete. A Python encoder and a zero-
dependency, unsafe-forbidden Rust crate implement the exact Cut-aware
`peano-lab-v2` tags. An adversarial review caught two useful boundary bugs
before integration. Python constructor dispatch originally used containers
whose membership invokes metaclass equality; a malicious subclass could claim
to equal a real constructor. Dispatch is now identity-only. Separately, the
first Rust artifact API preserved the wire fuel but did not consume it. The
native gate now mirrors Lean's path-fuel convention, adds a global work cap,
and rejects fuel zero. Lean independently confirmed the smallest forall-refl
fixture rejects at fuel 2 and accepts at fuel 3.

The final red-team pass found that the same Python idiom predated this work in
the authoritative checker itself. Expressions such as `type(term) in (Add,
Mul)` look like exact-constructor checks, but tuple membership may call an
attacker-controlled metaclass `__eq__`. A forged `Term` could impersonate
`Add`, override instance equality, and make `EqRefl` appear to prove the false
closed target `0 = S 0`. This was a genuine trusted-boundary soundness bug.
Every such dispatch in the checker now uses `is`, axiom names must be exact
strings, and the exact exploit is a permanent rejection regression. The lazy
context optimization was not the cause, but refusing to treat the performance
branch as “just an optimization” is what made the audit find it.

The native shadow CLI distinguishes accepted, semantic rejection, malformed
input, I/O failure, and usage error. It still has no vote in QED. Debug and
release Rust suites each pass 27 tests, including strict-codec mutations and
subprocess protocol checks. The differential harness then replayed all 384
public theorems, checked every certificate against its original goal in
Python, and sent four cases per theorem to the native process. All 1,536 Rust
cases agreed with the expected result: the original artifact was accepted,
while a wrong target, zero fuel, and a missing terminal newline were rejected.
The aggregate canonical-artifact receipt is
`4652c103b317ddf3405f74c022d2229be0c7bdb57fa94c9b0cc6e129d5a20b64`.
The largest artifact was the 73,767-node FTA certificate at 3,608,301 bytes.
After the checker hardening, three fresh complete processes reproduced that
receipt. The retained 384-row report is
`artifacts/peano-kernel/native-differential-v1.json`, SHA-256
`0aaa968c91d8769c101afd51681090396a31e4885a2629e7ecfb44113cd47e5d`.
Its own provenance manifest seals all 159 relevant Python/Rust sources and the
exact native executable; a cheap CI test re-hashes the seal without rebuilding
all certificates.

This is strong native differential evidence, not a new trust decision. A
representative third-way replay through the pinned Lean verifier, browser
WASM, and trap-isolated worker integration remain follow-on work; recording
those gaps is part of keeping a shadow checker honest.

Because the new inert encoder is a shipped Python source, the worker inventory
now contains 150 files. The regenerated immutable application namespace is
`a-f30eccf3c47a`, with visible candidate build `2026-08-04a`. This is a local
release identity, not a deployment claim.

The later trusted-boundary hardening necessarily invalidated that candidate:
the checker bytes are part of the immutable browser seal. After the
metaclass regression landed, the current local candidate advanced to build
`2026-08-04b`, application `a-903a05e31da9`, still with 150 worker sources.
Neither candidate was deployed by this work.

The final acceptance run used the exact hardened and resealed tree. Eight
runtime-weighted pytest shards finished green: 2,707 passed, twelve intentional
skips, and no failures. Their durations were 475.21, 487.90, 454.08, 448.49,
458.04, 494.88, 459.74, and 435.09 seconds, so the critical path was 8 minutes
15 seconds. The shard containing the dashboard-server contract was allowed to
bind only local `127.0.0.1`; all others ran in the ordinary restricted
sandbox. The Lambda Lab regression remained a separate compatibility gate,
and the strict Jupyter Book build plus all 287 documented commands also passed.

This closes the authoritative-Python and native-shadow milestone, not K4. The
browser WASM worker and the representative pinned-Lean third-way replay remain
explicitly open, and Rust remains unable to publish QED.
