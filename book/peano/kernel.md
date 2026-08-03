# The kernel and the De Bruijn criterion

When Peano Lab prints `QED`, it is making a deliberately narrow claim: a small checker has validated
one explicit certificate, from the empty context, against the formula that began this proof session.
The claim does not depend on whether the tactic engine behaved sensibly on the way there.  Search may
choose a terrible route, `simp` may contain a bug, and the terminal may render an unhelpful panel.
None of those components is allowed to manufacture a theorem.

This is the project's first law:

$$
  \text{successful QED}
  \quad\Longrightarrow\quad
  \operatorname{check}((),\,p,\,A)=\mathsf{true},
$$

where $A$ is the **original** stated goal, retained by the proof-session owner, and $p$ is a complete
proof term.  The implementation of that final boundary is the short
[`checked_final`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/tactics.py)
function.  The independent judgment it calls is in
[`kernel/checker.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/checker.py).

A tiny example traverses the whole boundary:

```text
pa> pa prove forall x. x = x
pa> intro x
pa> refl
pa> qed
```

`intro` and `refl` close engine goals, but only the last line licenses the theorem.  Even a state with
no visible goals can fail QED if it contains a hole, an unresolved metavariable, a malformed node, or
a certificate for some easier formula.

## Certificates are data, not authority

The kernel proof language has one inert constructor for each natural-deduction, equality, arithmetic,
or induction rule.  A few representative definitions from
[`proofs.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/proofs.py)
are almost boring:

```python
@dataclass(frozen=True, slots=True)
class ImpIntro(Proof):
    body: Proof

@dataclass(frozen=True, slots=True)
class ForallElim(Proof):
    p: Proof
    t: Term

@dataclass(frozen=True, slots=True)
class Ind(Proof):
    motive: Formula
    base: Proof
    step: Proof
```

Constructing `ImpIntro(...)` does not prove an implication, just as constructing a syntax tree for
`2 + 2 = 5` does not make the equation true.  The checker gives the tree meaning by recursively
matching it against a target formula and context.  An implication introduction is accepted only
when the target is $A\to B$ and its body checks as $B$ in the context extended by $A$.  A universal
elimination first synthesizes a formula $\forall x.\varphi$, then capture-safely substitutes its
term argument into $\varphi$.  An induction node must check both the zero case and the universally
quantified successor step for its stored motive.

The checker is bidirectional.  Elimination and annotated equality forms usually *synthesize* their
conclusion; introduction forms are *checked* against a conclusion already known.  This avoids
stuffing every proof node with redundant formula annotations while keeping the recursion readable.
The whole trusted checker is now 263 physical lines (formerly 234 before the explicit `Cut` sharing
rule), below the project's roughly 300-line design ceiling, and an import-hygiene test forbids it
from importing the engine or UI.

### Delaying a shift without delaying a proof obligation

Large certificates exposed an algorithmic cost hidden in the simple rule for universal
introduction. Entering a term binder used to rebuild *every* formula in the context with
`shift_formula(formula, 1)`, even when the proof never selected most of those hypotheses. Deep
Cut-heavy proofs repeated that work thousands of times.

The checker now stores each internal context entry as `(formula, pending)`, with the invariant that
it denotes `shift_formula(formula, pending)`. Entering a term binder increments the small pending
integer. Only `Hyp(i)` materializes the accumulated shift. A hypothesis introduced by `ImpIntro`,
`Cut`, or an `OrElim` branch starts at pending zero because it is already written at the current
binder depth. `ExistsElim` is the delicate case: old hypotheses acquire one pending shift, while
the opened existential body is prepended at zero because it already lives beneath the fresh witness
binder.

This changes evaluation order, not the judgment. Positive cutoff-zero shifts compose,

$$
  \operatorname{shift}(\operatorname{shift}(A,k),1)
  = \operatorname{shift}(A,k+1),
$$

so materializing once gives the formula produced by the former eager sequence. Focused tests cover
mixed-age contexts, both disjunction branches, cuts, witness scope, off-by-one mutations, and the
important observation that an unused hypothesis causes no shift at all.

On one arm64 CPython 3.10 run, the unchanged 73,767-node FTA certificate moved from a median
4.338-second final check to 0.451 seconds, while its complete cold library replay moved from 57.497
to 29.241 seconds. These are observational benchmark results, never acceptance thresholds. They
also illustrate Amdahl's law: accelerating the trusted check cannot remove tactic construction,
dependency replay, or diagnostic traversals around it.

### A second checker is a witness, not a promotion

Peano Lab now also has a dependency-free Rust *shadow* checker. It independently defines the same
terms, formulas, proof constructors, capture-avoiding operations, PA axioms, induction rule, `Cut`,
and explicit HA-versus-DNE boundary. The crate forbids unsafe Rust. Its answer is useful
cross-implementation evidence, but the browser session still grants QED only after the small Python
checker accepts the owner's original goal.

The boundary between implementations is the verified Cut-aware `peano-lab-v2` artifact grammar.
Python's inert encoder writes exact-arity tagged arrays, canonical natural-number decimals, and one
terminal line feed. It deliberately does **not** check proofs. Rust parses a strict bounded subset of
those bytes without a generic JSON normalizer: whitespace, escapes, objects, references, unknown
tags, alternate integer spellings, excessive resources, and trailing bytes all fail closed. The
decoded artifact contains the original target itself—never a theorem name or a target copied from a
possibly corrupted final tactic state.

The artifact also carries fuel. Rust consumes it with the same mutually recursive `check`/`infer`
path convention as the Lean verifier, then applies a separate global work budget. Thus fuel zero,
an open target, malformed bytes, exhausted work, or an unwinding panic cannot become `ACCEPT`. The
native command-line boundary makes the status explicit: `ACCEPT`, `REJECT`, and malformed-input
failure are distinct, and its help text says that it never grants QED. Process isolation is also the
model used by the browser worker, where an abort or WebAssembly trap remains an unavailable shadow
result rather than freezing or authorizing the Python session.

The browser runs the same Rust core through a small raw WebAssembly ABI in a *second* worker. The
Pyodide worker and Rust worker initialize concurrently, but only Python readiness unlocks the
terminal. On successful QED, Python first posts the authoritative result. It then serializes the
already-checked certificate and transfers its `ArrayBuffer` to the main page, which transfers it
again—without JSON or base64—to the one-shot Rust worker. This ordering matters: an encoder bug,
allocation failure, worker trap, or timeout occurs after QED and cannot retroactively change it.

| Browser shadow boundary | Fixed value |
|---|---:|
| Canonical input | 16 MiB |
| Decoded syntax/proof nodes | 1,000,000 |
| Codec depth | 192 |
| Checker invocations | 64,000,000 |
| Linear-memory maximum | 256 MiB, unshared |
| Main-page watchdog | 30 seconds |

The dependency-free wrapper owns one exact-length Rust `Vec<u8>` and exposes allocation, check,
and reset functions. JavaScript receives only a temporary offset into exported linear memory; Rust
never reconstructs a slice from a caller-controlled raw pointer. The core still has
`#![forbid(unsafe_code)]`; the wrapper contains no unsafe block or pointer dereference. Rust 2024's
`#[unsafe(no_mangle)]` linkage annotation is isolated in that wrapper and is reviewed as ABI
surface, not proof authority.

One portability boundary required care. Wire naturals fit in `u32`, while native Rust uses a
64-bit `usize` and `wasm32` uses 32 bits. The wrapper rejects term-variable and hypothesis indices
above $2^{32}-1-256$ before checking, reserving enough fixed-width room for every binder shift
allowed by the depth limit. Boundary fixtures run in both native tests and the real WASM module.
The committed 52,966-byte module has no imports, no threads or shared memory, and is rebuilt twice
in CI before exact comparison with the checked-in bytes.

The visible outcomes deliberately say **shadow agreement**, **shadow disagreement**, or **shadow
unavailable**—never “Rust QED.” Classical artifacts carry a separate logic label and reach only the
explicit PA+DNE checker. Each check consumes its input and the worker is replaced afterward, so
allocator state cannot leak from one theorem to the next.

The committed module was also exercised on the complete 384-theorem library,
not only toy ABI fixtures. For every theorem it received the original artifact,
a wrong-target mutation, zero fuel, and a missing terminal line feed. All 1,536
verdicts matched expectation, and the receipt over original artifact hashes was
`4652c103b317ddf3405f74c022d2229be0c7bdb57fa94c9b0cc6e129d5a20b64`—the
same receipt produced by native Rust. This is strong conformance evidence, but
it is still evidence *after* the Python judgment rather than an authority vote.

Python adds an unusual adversarial wrinkle.  A GPT Pro adversarial review found that a subclass can
override equality and pretend to equal any target.  The trusted recursion therefore accepts exact
frozen kernel constructors at rule
boundaries—`type(node) is EqRefl`, for example—rather than granting meaning to arbitrary subclasses.
Engine-only `Hole` and `MetaVar` nodes consequently cannot slip across QED merely because they share
a marker base class.

## Why proof terms rather than an LCF theorem type?

There are two classic ways to isolate a prover's trusted core.

In an **LCF-style** architecture, the implementation hides the constructor of an abstract `Theorem`
type.  Client code can obtain theorem values only by calling a small collection of trusted inference
functions.  Tactics are programs that compose those functions.  This is a powerful design, and its
central idea—untrusted proof search over a tiny trusted base—survives in modern systems.

In a **proof-term** architecture, tactics construct ordinary certificate syntax.  An independent
checker later validates that syntax.  Lean and Coq follow this broad pattern, and Peano Lab chooses
it for three practical reasons.  First, the certificate continues the Curry–Howard story: students
can watch a tree of holes become a proof.  Second, certificates can be printed, stored, mutated in
tests, and replayed without preserving privileged runtime values.  Third, final checking is a clean
second opinion: the tactic engine proposes; the kernel disposes.

Neither architecture is automatically sound.  An incorrect primitive inference function breaks an
LCF kernel; an incorrect certificate checker breaks a proof-term kernel.  An inconsistent axiom set
also proves too much no matter how elegant the software is.  The engineering goal is not to abolish
trust, but to concentrate it in code and rules small enough to inspect.

The live
[`LCF versus proof terms`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20kb%20lcf-vs-proof-terms)
card keeps this comparison beside the prover rather than presenting the chosen design as the only
possible one.

## Two De Bruijn ideas, both about trust

Nicolaas de Bruijn's name appears here in two distinct ideas.  **De Bruijn indices** represent bound
variables by distance to their binder.  The **De Bruijn criterion** says that formal proofs should be
checkable by a small, independently inspectable program.  The former helps us implement binding
correctly; the latter tells us why the resulting checker, rather than the tactic UI, is the source of
proof authority.

Consider

$$
  \forall x.\;\exists y.\;x+y=y+x.
$$

Inside the equation, $y$ is index $0$ because its binder is nearest, while $x$ is index $1$.
Renaming either surface binder changes no kernel object.  Alpha-equivalent formulas are therefore
literally the same representation, and hypothesis lookup never depends on a user's favorite letter.

Names disappear easily; substitution is the difficult part.  Suppose the internal formula
$\forall y.\;x=y$ contains a free outer variable $x$, and we substitute another free variable $z$
for it.  Before descending beneath $\forall y$, $z$ is index $0$.  Beneath that binder it must be
shifted to index $1$:

$$
  \forall y.\;\#1=\#0.
$$

A naive substitution would insert `#0` unchanged and silently turn the result into
$\forall y.\;y=y$.  That is variable capture: a free occurrence has acquired a binder and the
meaning has changed.  Peano Lab's
[`subst.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/subst.py)
separates **shifting** indices from **opening** one variable slot.  When opening descends through a
quantifier, it increases the binder depth and lifts the replacement.  Induction motives,
universal elimination, existential elimination, rewriting beneath binders, and theorem-library cut
elimination all ultimately rely on this small operation.

The distinction has a useful slogan: indices remove alpha-renaming accidents, but they do not make
capture avoidance automatic.  Correct shifting is part of the proof rule.

## The audit that made QED a hard boundary

The independent final check is not decorative architecture.  A 2026 audit of the sibling Lambda Lab
found that four cooperating defects let its interactive builder report a false QED for Peirce's law.
The details involved metavariable discipline, proof-wide substitutions, and finalization, but the
larger failure was simpler: the tactic layer's account of success was treated as authoritative.
The repair introduced a checked finalization path and a single session owner, then made those lessons
binding for Peano Lab.  The project history records the incident in the
[`JOURNAL`](https://github.com/nasqret/vietnam2026/blob/peano-lab/JOURNAL.md), while the original broader
Lambda Lab review remains in
[`docs/lambda-lab-audit.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/lambda-lab-audit.md).

Peano Lab therefore treats its own engine state as untrusted input.  `ProofState.target` is frozen,
but a buggy tactic could replace the entire frozen object.  The browser session separately retains
the original parsed formula and passes it into `checked_final`; finalization also rejects a state
whose cached target differs.  Classical mode is retained by that same owner as an exact Boolean.
The ordinary `check` rejects every double-negation-elimination node, while the explicitly selected
`check_classical` accepts such a node and leaves it visible in the certificate.

The tests attack this boundary directly.  They replace the cached goal, forge a goal-free state for
$0=S(0)$, leak unresolved metavariables, mutate induction motives and branches, attempt eigenvariable
escape, subclass AST nodes with dishonest equality, and perform naive capture under binders.  Passing
happy-path examples would show that the prover can work; rejecting these mutations is evidence that
its claimed boundary is real.

## What the checker does—and does not—establish

If the checker accepts $p:A$, we have evidence that $A$ is derivable from the encoded natural-
deduction rules, PA1–PA6, and the selected induction instances (plus explicit DNE only in classical
mode).  This is the lab's operational meaning of sound proof checking.

The certificate calculus and reference checker have an independent Lean formalization in
[`nasqret/peano-lab-lean`](https://github.com/nasqret/peano-lab-lean). Lean proves that checker
acceptance yields a `Derives` judgment and that every such judgment is true in the standard natural
numbers. This result is relative to Lean's kernel and reported standard axioms. Canonical inert
decoding and differential tests support correspondence with the retained Python sources; they are
not an exhaustive program-equivalence theorem for CPython. Historical pinned Lean 4.31/WMI job
`211445` covers the cut-free kernel. Cut-aware v2 source
[`ab966fd1`](https://github.com/nasqret/peano-lab-lean/commit/ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2)
passed pinned Lean 4.31/WMI job
[`218358`](https://github.com/nasqret/peano-lab-lean/tree/8515336ab3b89ca6f0c8ab521d01745a220b5211/artifacts/wmi/218358).

This metaverification does not establish that PA is consistent, that every true arithmetic sentence
is derivable, that the intended natural-number model is the only model of the first-order axioms, or
that Lean's own implementation and hardware are infallible. The De Bruijn criterion and the Lean
proof reduce the trusted computing base; they do not erase metamathematics or platform trust.

That modesty is a strength.  The tactic engine can grow new search procedures, simplifiers, and even
learned tactic proposers without enlarging the logical authority they possess.  Every proposed QED
still has to fit through the same small door: a closed certificate, the owner's original statement,
and an independent structural check.
