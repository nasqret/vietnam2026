# Peano Lab — design document

**Mission:** build a lightweight, *readable* theorem prover for Peano arithmetic in the browser —
a "little Lean for PA" — where the point is to **learn how such systems are built**: the kernel,
the tactic engine, the tactic *language*, and eventually the data pipeline for an LLM prover.
Priorities, in order: **soundness → clarity → pedagogy → extensibility → (only then) efficiency.**
Python throughout; clean code over clever code.

This document is the architecture the implementation must follow. The task breakdown with
milestones and acceptance criteria lives in `PLAN/09_peano_lab.md`.

**Current product boundary:** immutable Alpha v25 contains **2,080
independently checked theorems** and **6,633 proof-dependency edges**; the
ordinary public tactic surface retains its unchanged **432-theorem Stable
default**. Hydra may import a checked Alpha lemma only under an explicitly
requested complete-edition-digest authority and finite theorem allowlist. The
one current engineering path is
[`HYDRA_PRODUCT_ROADMAP.md`](HYDRA_PRODUCT_ROADMAP.md).

---

## 0. Plan review — decisions taken (and why)

The original idea: "build tactics for something harder than propositional logic, test on Peano
arithmetic, expandable, teach how tactics are made, lambda-lab-style UI, book chapter, later
post-train a small LLM on the solver's traces." All adopted. Five sharpening decisions:

**D1 — The logic is staged, not swallowed whole.** Full first-order PA at once would force
quantifiers, equality, substitution, *and* induction into milestone 1 — exactly how projects
drown. Instead the logic grows in fragments, each unlocking a new *kind* of tactic:

| Stage | Fragment | New tactic kind it forces |
|---|---|---|
| A | Quantifier-free equations over 0, S, +, · | `refl`/`symm`/`trans`/`cong`, `rewrite` |
| B | + structural induction (schema over open formulas) | `induction n` — the star of the show |
| C | + ∀/∃, →, ∧, ∨, ⊥, ¬ (:= → ⊥) | `intro`/`apply` (from prove), `exists_intro`, `forall_elim` |
| D | + automation | tacticals, `simp`-lite, bounded `norm_num`/`decide`, `auto` |

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

**D5 — Headless training is an adapter, never a second prover.** Data preparation and
verifier-guided search need not pay the browser/DOM startup cost, but speed does not justify a
second interpretation of Peano Lab. The compact runner imports the production formula parser,
proof-state owner, public tactic grammar, theorem replay, trace logger, finalizer, and independent
kernel. It starts a fresh owner for every request and retains the original closed target and exact
logic mode outside all model-controlled data. Generation always records the binding v1 trace;
quiet verification is a separately named mode for already-authored scripts. A model supplies only
tactic lines. It cannot choose its execution mode, capability set, theorem allow-list, session
identity, QED meaning, or checker.

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
constants above), together with the reviewed self-contained `Cut` sharing node described below.
`Cut` changes the certificate grammar and enlarges the trusted checker; it does **not** add a term,
formula, axiom, theorem constant, or classical principle to the object logic. The checker remains a
single structural recursion `check(ctx, proof, formula) -> bool` of target size **≤ ~300 lines** —
that number is a design constraint, not an aspiration: if the checker grows past it, the rule set
is wrong.

**Independent metaverification.** The separate
[`nasqret/peano-lab-lean`](https://github.com/nasqret/peano-lab-lean) project
models this certificate grammar and checker in Lean and proves semantic
soundness over standard natural numbers. Its historical Lean 4.31/WMI receipt
`211445` covers the cut-free v1 kernel. The explicit `Cut` rule and
`peano-lab-v2` codec at source
[`ab966fd1`](https://github.com/nasqret/peano-lab-lean/commit/ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2)
passed pinned Lean 4.31/WMI job
[`218358`](https://github.com/nasqret/peano-lab-lean/tree/8515336ab3b89ca6f0c8ab521d01745a220b5211/artifacts/wmi/218358)
and form the verified Cut-aware v2 baseline. Named mathematical
definitions remain hygienic untrusted expansions into ordinary `Formula` ASTs
and are deliberately absent from this trusted grammar.

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

The browser owner also keeps a replay journal, separate from both `ProofState.history` and the v1
trace. It is untrusted presentation data: each surviving proof transaction is paired with enough
accepted surface syntax and classical-mode authority to replay the current undo branch. Failed
tactics and inspection commands never enter it; `undo` removes precisely the transaction it
restores. Explicit tacticals retain their complete surface line, while top-level `auto` records its
winning primitive steps because those are independently undoable. This journal never enters the
kernel or changes a certificate.

### Local reasoning is an engine schedule, not a kernel rule (M16)

The original live surface admits two named local-reasoning schedules:

- `have h : P` first opens `Γ ⊢ P`, then opens the previous focused target under `h : P`;
- `suffices h : P` first opens the previous focused target under `h : P`, then opens `Γ ⊢ P`.

The name must be fresh, and `P` is parsed in the focused goal's existing rigid term-variable
scope. An undeclared free term variable is an error rather than an implicitly generalized name.
Both commands therefore express the same natural-deduction cut—prove `P`, then use it—but choose
opposite pedagogical schedules for its two obligations.

The untrusted engine may temporarily place `LocalHave(P, proof-hole, body-hole)` or
`LocalSuffices(P, body-hole, proof-hole)` in a partial certificate. Their child order is deliberate:
left-to-right proof holes remain in exactly the order of the displayed goals. These two classes are
engine-only administrative nodes; they are absent from `kernel/proofs.py`, and the kernel checker
has no case for either one.

Before the checker is called, untrusted finalization compiles every such node by
capture-avoiding proof-hypothesis substitution. Informally, both become
`(λh. body) proof` and then beta-reduce to `body[proof/h]`. The compiler shifts proposition
hypothesis indices and term variables beneath implication, disjunction, existential, and universal
binders, so a local proof cannot be captured while it is inserted. Its result, which contains
neither `LocalHave` nor `LocalSuffices`, is checked from the empty context against the session owner's
**original stated goal** and exact logic mode. A faulty scheduler or compiler can therefore cause
only rejection. Failure while parsing or constructing either tactic is transactional, and one
successful command remains one exact `undo` step.

This administrative compilation is deliberately distinct from trusted proof sharing. `have` and
`suffices` still compile away; neither surface command grants a user direct way to manufacture a
kernel `Cut` node.

The 2026-09-05 authoring extension also accepts `have h := fact explicit_arguments`.
It infers only the result of explicitly applying an existing named hypothesis to
the supplied natural-number terms and named premise proofs. It performs no theorem
search, implicit premise synthesis, or induction-invariant guessing. The local name
must be fresh, and partial applications retain every remaining quantifier and
implication. Elaboration constructs ordinary elimination terms and the same
engine-only `LocalHave`; finalization and the independent kernel are unchanged.
The exact syntax, bounds, reading policy, and verification scope are recorded in
[`PROOF_READABILITY_POLICY.md`](PROOF_READABILITY_POLICY.md).

### Self-contained proof sharing (post-M20)

The arithmetic dependency ladder exposed a different problem: substituting a large closed proof at
every use duplicates it, and the capture-sensitive reducer was not reliable enough around all
induction shapes. Peano Lab therefore admits one reviewed proof-certificate constructor:

```text
Cut(A, B, lemma, body)
```

Its exact checking rule is

$$
\frac{\Gamma\vdash\mathit{lemma}:A\qquad
      A,\Gamma\vdash\mathit{body}:B}
     {\Gamma\vdash\operatorname{Cut}(A,B,\mathit{lemma},\mathit{body}):B}.
$$

The checker validates the embedded `lemma` branch once in the ambient context, then validates the
embedded `body` branch with `A` as hypothesis zero. Both branches use the same intuitionistic or
explicitly classical mode. The conclusion annotation `B` lets the bidirectional checker validate a
body beginning with an introduction form; it is checked, not trusted.

This is lexical proof sharing, not a theorem oracle. A `Cut` contains both formulas and both proof
branches. It contains no theorem name, content hash, declaration identifier, callback, or external
environment lookup. Library names and artifact hashes remain untrusted metadata resolved before
checking. The trusted base has nevertheless grown: `Cut` is an inert constructor in
`kernel/proofs.py`, and its rule is a new case in `kernel/checker.py`. The object language, PA
axioms, induction schema, and default intuitionistic logic are unchanged.

Mathematically the rule is the ordinary derivation `(λh. body) lemma`. The untrusted
`erase_trusted_cuts` utility expands a checked node to that implication form, without normalizing it,
for compatibility and audits. This utility is not proof authority and is not a completeness
theorem. The current bidirectional checker cannot synthesize every introduction-shaped erased
argument, and the capture-sensitive reducer cannot normalize every large induction-bearing
expansion reliably. An erased or reduced result counts only if the kernel separately accepts it.
Normal replay and QED therefore check the self-contained `Cut` certificate directly.

**Primitive tactics (Stage A–C):** `intro`, `apply`, `exact`, `assumption`, `split`, `left`,
`right`, `cases`, `exfalso`, `refl`, `symm`, `trans t`, `congr`, `rewrite h [at h']`,
`rewrite <- h`, `induction n [with base step]`, `exists t`, `intro x` (∀), `specialize h t`,
`have h : P`, and `suffices h : P`.

**Tacticals (Stage D — the "how tactic languages work" lesson):**
`t1; t2` (then), `t1 <|> t2` (orelse), `repeat t`, `first [..]`, `all_goals t`, `focus n t`.
Implemented as *combinators over the Tactic type* — pure functions returning functions. This
milestone is deliberately separate: it is the moment the tactic *language* appears, and the book
chapter narrates it (LCF's great idea, surviving into Lean's `<;>` and `try`).

**Automation (Stage D):**
- `simp` — an ordered rewrite engine driven by a small, explicit simp-set (PA3–PA6 oriented
  left→right + proved lemmas the user tags). Termination by a measure, documented.
- `norm_num` — bounded, certificate-producing normalization of closed numerical subterms in an
  equality, optionally beneath leading universal binders. Computed values choose PA3–PA6 proofs;
  they are never accepted as evidence.
- `decide` — closed-formula evaluation (compute both sides of a closed equation; decide closed
  quantified statements only up to a bound with an honest "bounded check" label).
- `auto [depth]` — backtracking search over the primitive tactics + assumption + simp. This is
  also the **corpus generator** for the LLM stage.

### Checked theorem reuse and arithmetic automation (post-M9)

Live proofs may reuse a named theorem only by importing its already closed certificate. The surface
command is `use <library-theorem> [as <alias>]`. Name resolution belongs to `library/` and `ui/`;
the engine receives an exact formula and proof, rechecks `check((), certificate, formula)`, and
places them in a self-contained `Cut(formula, target, certificate, body)` around the focused goal.
The kernel never learns the theorem name and has no trusted declaration environment.

At surface finalization, the untrusted reducer still compiles `LocalHave`/`LocalSuffices` and
contracts exposed implication and universal beta redexes. It preserves trusted `Cut` nodes. The
result is passed to `checked_final` with the session owner's **original** target and exact logic
mode, so the kernel checks every embedded lemma and body itself. A faulty import, scheduler,
reducer, or library entry can therefore cause only rejection.
Imported and live partial certificates have explicit node/depth budgets. Exceeding either raises
an honest transactional `TacticLimit`; QED also translates host recursion exhaustion into a typed
rejection while preserving the session.

Arithmetic automation follows the same certificate discipline. The argument-free `norm_num`
tactic applies to an equality, optionally beneath leading universal binders, without unresolved
term metavariables. It visits maximal variable-free, non-canonical-numeral subterms in deterministic left-to-right order, computes a
candidate numeral, and constructs a checked PA3--PA6 proof that the subterm equals that numeral.
`CongS`, `CongAdd`, and `CongMul` lift those proofs through open parents. Identical normalized sides
close with a checked equality certificate; useful normalization that leaves different open sides
publishes one transported residual goal. A wholly closed unequal equation, unsupported goal shape,
or non-closing no-progress request fails transactionally; a reflexive equality may close without a
numerical computation.

`norm_num` takes no arguments, mines no hypotheses, and does not decide inequalities, disequalities,
or arbitrary quantified formulas. It may structurally open leading universal binders when their body
is an equality, then wrap the result in ordinary `ForallIntro` certificates. One attempt is bounded
by 256 equality-term AST nodes at depth 64, at most 64 such leading binders, 32 closed computations,
intermediate values at most 128, 25,000 work units, a 50,000-node/256-level generated numerical
bridge, and five seconds. The complete live partial certificate is separately capped at 500,000
structural occurrences, 100,000 distinct proof objects, and depth 256. Multiplication tests the
value bound before forming the product. Resource or
host-recursion exhaustion raises `TacticLimit` and preserves the exact proof state and history.
Arithmetic-aware `hint` uses the same pure bounded preflight; it never runs a speculative state
tactic or allocates proof holes.

The argument-free `ring` tactic applies only to a focused equality whose rigid terms use `0`,
successor, `+`, and `·`. It reifies
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

One `ring` attempt is bounded by 256 input AST nodes, depth 64, 16 variables, degree 16, 64
monomials, natural coefficients at most 128, 25,000 work units, a 100,000-node/256-level generated
proof, and a five-second wall-clock budget. That conservative browser margin was chosen after the
largest required normalization used about 1.4 seconds under native CPython; it must still be
measured under Pyodide when an in-app browser is available. Unresolved term metavariables are
rejected rather than guessed. Any resource or host-recursion exhaustion is an honest transactional
`TacticLimit`. The deadline is checked before normalization, throughout proof construction, and
after synchronous replay, cut reduction, and kernel validation; those synchronous calls are not
preempted mid-call. The browser's Stop control remains the hard abort because all Python runs in a
disposable worker.

### Compact PA recurrence certificates (M18)

`compact_arith` is a second, deliberately narrower arithmetic tactic. Its exact surface forms are
`compact_arith` and `compact_arith [h, <- k]`; the bracketed list contains an ordered, explicit set
of named equality hypotheses, with `<-` selecting right-to-left orientation. It applies only to the
focused **rigid equality**. It does not introduce binders, select an induction variable, invent an
induction invariant or existential witness, solve a logical connective, or mine unlisted context
hypotheses. Malformed lists, missing or non-equality names, unresolved term metavariables, and
unsupported goals fail transactionally.

The purpose is certificate size, not a broader theorem set. `ring` obtains predictable breadth by
reducing all supported polynomials to one commutative-semiring normal form. `compact_arith` instead
searches a small, fixed family of PA-oriented equality paths and recurrence templates whose shapes
follow PA3--PA6's recursion on the second argument. Initial templates may include checked
derivations of `S a + b = S (a + b)`, `S a * b = a * b + b`, the exact successor-addition swap
needed by the parity experiment, and the zero-offset doubling recurrence
`(2 * w + j) + j = 2 * (w + j)`. Direct seeds include the 6-node `a+1=S a`, 10-node
`a+2=S(S a)`, and 11-node `a*(b+1)=a*b+a` bridges. Template names and computed costs are untrusted
planner data.
Every recurrence template instance is an ordinary `ForallIntro`/`ImpIntro`/`Ind` certificate over
PA3--PA6, checked with an empty proof context before final use and capture-safely eliminated. A
fully quantified addition-successor template is checked once before specialization; other
recurrence instances may already contain the rigid parameter terms selected from the goal.

The engine carries every candidate as an exact `(left, right, proof)` triple. Smart constructors
may create PA instances, symmetry, transitivity, congruence, and equality-motive `EqSubst`
transports only when their recorded endpoints compose syntactically. A bounded deterministic search
compares orientations and paths, retaining one winner for each exact endpoint pair and assumption-
permission mode. Its deterministic key is certificate nodes, proof depth, annotation nodes, then
generation ordinal. Its primary cost is measured on the exact administratively normalized
certificate that the current kernel will inspect. A self-contained `Cut` counts once together with
its two stored branches; reusing one Python object at two separate certificate positions still
counts twice.
Annotation-node count is the third tie-breaker; annotation depth, work, and wall time are resource
bounds rather than optimization objectives.
Candidate generation carries a deterministic ordinal, so equal-cost selected hypotheses preserve
the explicit surface-list order rather than depending on set, mapping, or host traversal order.

`compact_arith` must never add another kernel constructor, arithmetic oracle, trusted theorem
reference, or declaration environment. Before publishing success it normalizes administrative
cuts while preserving self-contained sharing, checks the
candidate in the focused goal's exact context with the independent kernel, enforces the complete
partial-certificate budget, and only then replaces the hole and records one transaction. Ordinary
QED independently checks the final compiled certificate against the session owner's original target
and exact classical mode. A planner, template, cost, specialization, or reduction bug cannot
produce a false QED; non-soundness contracts such as explicit-hypothesis use, determinism, bounds,
and cost reporting remain obligations enforced by engine tests.

The intended parity lesson deliberately keeps the mathematics outside the tactic. The surface proof
must state the stronger invariant `exists x. n*n+n = 2*x`, choose the base and successor witnesses,
perform induction and existential elimination, explicitly list the induction equality when it may be
used, and prove the final `n*(n+1)=n*n+n` bridge. `compact_arith` may close the resulting equality
subgoals compactly; it may not synthesize the whole theorem in one opaque command. The retained
hand-authored 180-node certificate is the current checked record and an implementation target, not
a new axiom and not evidence of a global lower bound.

The golden replay therefore uses bare `compact_arith` for the closed base equality,
`compact_arith [IH_witness]` for the successor equality, and bare `compact_arith` for the explicitly
stated final normalization bridge. After capture-safe local-cut compilation, its canonical
180-node/depth-34 certificate is byte-identical to the retained hand-authored artifact. This exact
regression is a success criterion, not permission to describe 180 as globally minimal.

A pure `compact_arith?` inspection command previews the deterministic selected route, explicitly
used hypotheses, and cost. Preview must not run a state tactic speculatively,
allocate holes or metavariables, append history or JSONL trace transitions, or cache authority for a
later run. The real tactic rebuilds and checks its candidate. Both preview and execution have pinned
AST, selected-hypothesis, annotation, work, proof-node/depth, complete-partial-proof, and wall-clock
limits. The M18 defaults are 256 aggregate input-term nodes at depth 64, 16 selected equations, 64
seed/template instances, 512 memo/search states, 512 generated candidates, 100,000 term/formula
annotation nodes at depth 256, 20,000 work units, a 10,000-node/256-level generated fragment, a
100,000-node/256-level complete partial certificate, and five seconds. Exhaustion means only that
this bounded search stopped.

The public metric must be named honestly. `proof_size` counts structural `Proof` occurrences while
ignoring the sizes of `Term` and `Formula` annotations stored by nodes such as `EqSubst`, `Ind`, and
`Cut`.
The implementation may claim “smallest among the finite candidates generated by template set T
under limits B” only if it exhausts that set and charges post-expansion cost. It may call the
180-node artifact a best-known checked upper bound. It may not claim an absolute minimum without a
fixed finite candidate language and an exhaustive or formally verified lower-bound argument.

## 3. UI: the `peano-lab` page

Clone the lambda-lab shell (xterm + Pyodide worker + fully self-hosted vendor + `?cmd=` deep
links + localStorage history + Stop button). New Python package `peano_lab`, new static page
`/peano-lab/`. Command family:

- `pa prove <formula>` — interactive session (the `prove` UX: goals/context/term panels,
  complete-line `qed`/`abort`, in-proof `help`, `hint`)
- `pa tactic [name]`, `pa lib [name]` — tactic encyclopedia + proved-theorem library;
  `pa lib alpha [name]` is an opt-in research-evidence inventory, while
  `pa lib alpha check <name>` independently verifies one admitted Alpha proof
- `pa axioms`, `pa eval <term>`, `pa simp <term>`
- proof-producing arithmetic tactics `norm_num`, `ring`, and the narrower `compact_arith`, each
  with an executable tactic card; `compact_arith?` is a pure preview
- `kb`-style knowledge base entries for PA, induction, De Bruijn, LCF vs proof terms, Gödel
  (a "limits" card — honest about what this prover can never do)
- tutorials: "prove add_comm by hand", "build your own tactic", and checked numerical normalization

**Single-owner routing, complete-line aliases, arrow-args-are-propositions** — all the audit's
UI rules apply from day one (they are already implemented patterns; copy them, don't rediscover).

### Runtime delivery contract (M14 owner-authorized extension)

The browser runtime remains static and fully self-hosted, but “client-side” must not mean “download
the same Python runtime on every visit.” The transport layer therefore has four explicit rules:

1. `index.html` is never reused without contacting the server, so a promoted `BUILD` is visible.
2. Worker/Python files live below a release path derived from their application manifest; vendor
   files live below a namespace derived from the canonical source-vendor manifest. Those paths are
   immutable, retained after later deployments, and uploaded before `index.html` points at them.
   Neither identifier is reused; the human-facing `BUILD` also changes for every application release.
3. Apache negotiates Brotli when available and gzip otherwise for WASM, JavaScript, Python source,
   JSON, HTML, CSS, and plain text. It does not recompress ZIP or WOFF2 data.
4. The worker starts Pyodide first, fetches all application sources concurrently while the runtime
   initializes, then checks failures and mounts sources in one deterministic declared order.

Concurrent delivery changes no proof rule and introduces no proof authority. The same Python
modules are mounted byte-for-byte; the independent kernel still checks every QED against the
session owner's original goal. Terminating the disposable worker remains the hard Stop operation.

#### Read-only PHP transport exception (owner authorized 2026-09-05)

The owner approved implementing and testing a Peano-only PHP adapter on preview
because account-level static header directives have no effect on WMI, while
PHP-generated `Cache-Control` reaches clients. The web FPM runtime is PHP 7.0,
distinct from the hosting account's PHP 7.4 command-line interpreter; the
adapter must remain compatible with both. This is not a proof service:
the browser still executes the unchanged worker, Python checker and proof code.
The adapter cannot run commands, perform network requests, accept uploads,
write files, create sessions, or execute a supplied proof.

Only `/peano-lab-next/` and `/peano-lab/` are valid mounts. Immutable application
files must be listed in the exact manifest whose SHA-256 determines their
application namespace. Canonical vendor inventories provide the corresponding
allowlist. The historical `v-2eaf25dc3894` alias and flat vendor paths retain
their original bytes, checked against the same canonical `v-85fb3352e49c`
inventory. All 15 retained preview application manifests and both 18-file
vendor namespaces were independently inspected before implementing this adapter.

Every served file is a regular, same-owner, non-shared-writable file, with no
symlink component. A descriptor is hashed before it is streamed in 64 KiB
chunks. Files are bounded by 64 MiB, manifests/HTML by 1 MiB, relevant request
headers by 8 KiB and URLs by 4 KiB. The same descriptor supplies the response.
HTML remains `no-store`; only versioned successful/304/206 asset responses are
immutable; errors are `no-store`. GET/HEAD, conditional validators, single byte
ranges, and q=0-aware gzip negotiation are implemented explicitly. Unsupported
multipart range requests fall back to the complete representation. ZIP and
WOFF2 are never recompressed.

Gzip representations are deterministically prepared and decoded back to exact
source bytes during staging, outside public application/vendor namespaces.
Their transport metadata is not mathematical authority. Existing immutable
directories and gzip representations are retained; the HTML and routing
entrypoints are activated after their dependencies. No daemon is introduced.
The original static configuration remains an exact rollback. The unchanged
full HTTP delivery gate still decides whether preview delivery succeeds;
production promotion and real-browser visual testing remain separate gates.
See [the transport runbook](PEANO_PHP_DELIVERY.md).

The owner subsequently approved the same verified stage for production on
2026-09-05. Its [production receipt](PEANO_PHP_PRODUCTION_2026-09-05.md) records
the unchanged full HTTP gate and exact current/retained file checks. Browser
cold/warm-start, checked-QED and Stop/restart acceptance remain explicitly
unperformed without a connected browser; publication does not certify them.

### Replayable proof artifact contract (M15 owner-authorized extension)

`script` renders the active journal as a canonical program beginning with `pa prove`.
`script download` saves exactly the same LF-only, newline-terminated UTF-8 command body. A live
artifact is always labeled **ACTIVE (not kernel-checked)** and omits `qed`, even if every engine
goal is closed. Only after `checked_final` accepts the owner-held original theorem and exact logic
mode may the UI retain a **CHECKED QED** artifact with a final canonical `qed` line. A failed QED or
abort cannot create or overwrite that retained artifact.

The main thread accepts download bytes only for an exact command entered directly at the terminal,
never from a deep link or quick-command injection. It validates the fixed-size plain-text payload,
uses a fixed filename, and releases its temporary object URL. Downloading is an observation, not a
tactic, trace step, certificate constructor, or server write.

A replay file is an untrusted program, not a proof certificate or a library declaration. Replaying
it reconstructs a candidate certificate; only `qed` checks the original theorem. Admission to the
checked theorem ladder remains a source-reviewed `TheoremSpec` change with a closed statement,
explicit earlier dependencies, compatible authored script, fresh replay, tests, and commit. The
static browser never mutates that library.

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

### Headless execution and post-training envelopes (M19)

`peano_lab.batch` is the one warm-process execution boundary for corpus generation, model search,
and fast replay checks. `scripts/peano_batch.py` provides a finite transactional JSONL transport
around it. It is deliberately not a duplex service: result rows are withheld until EOF and, in
trace mode, until the matching trace artifact commits.
Neither module defines a term, formula, proof constructor, tactic, theorem, or checking rule. Every
`proved` result is issued only after `checked_surface_final` submits the completed certificate to
the same reviewed kernel against the adapter-owned original target and exact classical mode.

The request schema contains only a version, caller label, closed theorem, tactic lines, classical
Boolean, and stop/continue-on-tactic-error policy. Execution mode and `SurfaceCapabilities` are
runner-owned arguments. A capability fingerprint hashes its label, complete primitive-command
allow-list, and complete checked-theorem allow-list; the result records that digest and logic mode.
The same capability object compiles every tactical leaf, including dead alternatives. A finite
capability profile cannot expose `auto` until search and winning-plan replay themselves become
capability-aware.

Trace mode is mandatory for generation and search. The adapter checks that each submitted command
adds the exact expected replay and engine-history transaction(s), preserves step and goal
continuity, binds non-`auto` trace text and focus to the submitted line, binds `auto` transitions to
its surviving primitive history, and gives every failed command exactly one unchanged-state error
transition whose diagnostic matches the raised `TacticError`. Trace records are
append-only and returned as detached copies. One request is bounded to 1,024 tactic lines, 500,000
tactic characters, the ordinary formula/line/numeral/live-certificate limits, and 16 MB of encoded
trace records; a bound is checked before the offending record is appended or sent to a sink. The
CLI additionally defaults to at most 10,000 requests, 256 MiB input, 128 MiB result envelopes, and
512 MiB raw trace per finite transaction; larger workloads must use explicit reviewed limits or
shards. The exact model-v3 library-corpus runner exercises that escape hatch with an explicit,
host-owned 128 MiB per-session ceiling because a reviewed valid certificate exceeds the ordinary
limit. The override is capped in the Python API and absent from the request JSON schema; it does not
change the JSONL transport's independent 512 MiB aggregate default.
Raw v1 records and compact result envelopes are
separate streams; the raw artifact is written to a same-directory staging file and appears at its
requested final name only after a complete, durable batch. Empty, all-invalid, fail-fast, or
unexpectedly interrupted runs never publish a plausible final trace. Compact success rows are also
staged and withheld until that trace publishes, so a downstream pipeline cannot observe a claimed
success paired with a missing final trace artifact.

Quiet `verify_proof` omits transition rendering only for high-throughput checks of scripts that
already exist. It retains the same parser, tactics, state transactions, certificate construction,
original-target ownership, and independent final kernel check. It cannot accept a trace sink, and
its output is not training data.

Raw traces remain the binding v1 artifact. Research metadata lives in a strict sidecar: exact
logic, capability object and digest, family, lineage, generator version, and provenance. The
dataset compiler accepts positive next-tactic labels only from `qed: true` sessions whose
successful sequence exactly replays under that declared environment to a second kernel-checked
QED with identical states and proof size. It preserves the exact executable authored tactic; the
policy input focus is always zero because trace focus is derived from the action and would leak the
label. Connected genealogy, canonical-formula, and exact-rendered-prompt components are assigned to
train/validation/test before tactic rows are expanded; an independent attestor rejects both formula
and prompt overlap across splits.
The manifest fingerprints the compiler, runtime, and complete `peano_lab/**/*.py` semantic source
tree. Training and held-out evaluation use one fixed `model-v1` command/theorem preimage, and every
checkpoint/report binds its model revision, data and source digests, capability digest, decoding
settings, evaluator source, and resume parent identity. Model text is never evidence; evaluation
reports a success only after the same owner-and-kernel path closes a frozen held-out statement.

## 5. Testing (non-negotiable, learned from the audit)

1. **Soundness oracle**: every QED in every test re-runs the independent checker; a fuzz suite
   tries scripted attacks (`0 = 1`, `∀n. n = 0`, S-injectivity abuse, capture attacks through
   rewrite-under-binder) that must all fail.
2. **Tactic contract tests**: failure leaves state unchanged; invariants
   `len(goals) == holes(partial)` after every step.
   Local-reasoning tests additionally pin the two opposite goal orders, exact undo, and
   capture-avoiding compilation beneath both proposition and term binders.
   Self-contained-sharing tests mutate both annotations and both proof branches, distinguish the
   ambient context from the body-only hypothesis, preserve classical-mode authority, reject
   subclasses and malformed nodes, and exercise capture beneath implication, disjunction,
   existential, and universal binders.
   Compact-arithmetic tests additionally check exact hypothesis order/orientation, template
   soundness and capture, preview purity, deterministic post-expansion costs, adversarial mutations,
   and transactional exhaustion of every search/certificate bound.
3. **The theorem ladder as regression** (§6): every library theorem's script replays in CI.
4. **Book gate**: extend `verify_book_commands.py` to replay `pa`-family deep links and session
   blocks against the peano-lab driver.
5. Independent cross-check: `pa lean <thm>` exports the exact statement and its complete
   constructive proof certificate as an ordinary Lean theorem over `Nat`. The Mathlib-free
   sibling checker reconstructs and checks every proof constructor before its formally proved
   soundness theorem supplies the result; no proof placeholder, theorem-name trust, or
   compiler-reflection axiom is introduced. Explicit `pa lean alpha <thm>` applies the same
   independently checked conversion only to closed theorems admitted by the explicitly
   selected immutable Alpha release, currently Alpha v25. Quadratic reciprocity first
   acquired that authority in historical Alpha v16; body-only rows and unsealed candidates
   still fail closed, and the default Stable/public surface remains unchanged.

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
      batch.py                               (headless adapter; no new proof semantics)
      kernel/     terms.py formulas.py subst.py proofs.py checker.py   ← TRUSTED, small
      engine/     state.py tactics.py tacticals.py rewrite.py
                  induction.py decide.py norm_num.py proof_reduction.py ring.py compact_arith.py
                  search.py trace.py                                  ← untrusted
      ui/         prove.py panels.py data_tactics.py data_kb.py
                  data_tutorials.py data_library.py
      library/    theorems.py                (scripted ladder proofs)
    tests/        test_kernel.py test_soundness.py test_tactics.py
                  test_tacticals.py test_ladder.py test_ui.py
  vendor/                                    (shared fetch via scripts/fetch_vendor.sh)
scripts/export_traces.py
scripts/peano_batch.py                       (finite transactional JSONL transport)
scripts/build_peano_policy_dataset.py        (QED-only replay compiler)
book/peano/*.md                              (the new book part)
```

Kernel modules import **nothing** from `engine/` or `ui/` — enforce with a test.

## 8. What we are explicitly NOT building

No dependent types, no definitional equality/reduction engine, no term elaborator, no typeclass
resolution, no proof irrelevance puzzles. PA over a fixed signature keeps every one of those
out of scope — that is *why* it is the right testing ground. When the book chapter compares us
to Lean, these absences are the comparison.

The arithmetic tactics are not a decision procedure for PA. `norm_num` covers bounded closed
numerical islands in equalities; `ring` covers unconditional polynomial identities. Neither solves
nonlinear consequences of hypotheses. There is no Presburger `omega` in this plan: adding one later
would require a separate certificate-producing design and would still decide only that fragment,
not general Peano arithmetic. `compact_arith` does not change this boundary: its finite seeded
recurrence grammar is intentionally incomplete, and “cheapest candidate found” is not an absolute
proof-minimality result. A post-trained policy does not change this boundary either: the model is
an untrusted tactic proposer, not a theorem oracle, semantic judge, kernel extension, or source of
axioms.
