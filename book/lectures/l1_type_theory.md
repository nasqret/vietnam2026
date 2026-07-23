# Lecture 1 — A general introduction to type theory

```{admonition} Abstract
:class: tip
What is a *type*, and why do modern proof assistants stand on **type theory** rather than set theory?
We introduce **judgments** $\Gamma \proves t : A$, the **simply-typed $\lam$-calculus** and its typing
rules, the difference between **Church-style** and **Curry-style** typing, the idea that types can *act*
like sets until they can't, and a first look at **dependent types**. This is the gentle-but-rigorous
on-ramp to everything that follows.
```

## Learning objectives

By the end you can:

- read and write a typing judgment $\Gamma \proves t : A$ and apply the three STLC rules (var/abs/app) to
  derive the type of a term **by hand**, as a derivation tree;
- state **subject reduction** and **strong normalization** for STLC and explain why $\Omega$ and the
  $Y$-combinator of {doc}`l2_lambda_calculus` are *untypable*;
- explain the difference between **Church-style** and **Curry-style** typing and say what a **principal
  type** is;
- state the **Curry–Howard** dictionary, read a proof as a program and back, and say why Peirce's law has
  no proof term;
- say *why* a type is not just a set, and pinpoint where the "types-as-sets" picture breaks (proof
  relevance, Girard's paradox, constructive existence);
- describe what **dependent types** ($\Pi$, $\Sigma$, identity) and **Martin-Löf type theory** add, and
  why $\N$-elimination *is* induction;
- name the foundation of each of the four provers we use (Lean, Rocq, Agda, Mizar) and articulate why
  proof assistants are built on type theory in the first place.

## Why this matters

A proof assistant has to answer one question mechanically and without appeal: *is this a proof?* The idea
that makes that question decidable is due to Church, Curry, Howard and de Bruijn, and it is startlingly
economical: **a proof is a term, a theorem is its type, and checking the proof is type-checking the
term.** Everything in this course — Lean, Rocq, Agda, and even the contrast with Mizar — is a working out
of that one sentence. This lecture builds it from the untyped $\lam$-calculus you already know, so that
by the end "the compiler accepted my proof" and "the term had the right type" are literally the same
event.

## Judgments, contexts, and the STLC typing rules

Type theory is a game of **judgments**. The central one is
$$ \Gamma \proves t : A, $$
read "in context $\Gamma$, the term $t$ has type $A$." A **context** $\Gamma = x_1{:}A_1,\dots,x_n{:}A_n$
is a finite list of typing assumptions about distinct free variables. **Types** are built from base types
by a single arrow:
$$ A, B ::= o \mid A \To B, \qquad\text{with } \To \text{ right-associative}, $$
so $A \To B \To C$ means $A \To (B \To C)$. The terms are the ones from {doc}`l2_lambda_calculus`,
$t ::= x \mid \lam x{:}A.\,t \mid t\,u$, now carrying a type annotation on the bound variable (this is the
*Church-style* presentation; more on that below). Three inference rules — premises over a line — say
which judgments are derivable:

```{math}
\frac{(x:A) \in \Gamma}{\Gamma \proves x : A}\ (\textsf{var})
\qquad
\frac{\Gamma, x:A \proves t : B}{\Gamma \proves (\lam x{:}A.\,t) : A \To B}\ (\textsf{abs})
\qquad
\frac{\Gamma \proves t : A \To B \quad \Gamma \proves u : A}{\Gamma \proves t\,u : B}\ (\textsf{app})
```

Read (abs) and (app) once more: **abstraction *builds* a function type; application *eliminates* one.**
A derivation is a finite **tree** whose leaves are (var) instances — remember that shape, because in a few
sections it will turn out that *proofs are trees for exactly the same reason*.

````{admonition} Worked example 1 — a derivation by hand
:class: note
Let us derive $\ \proves\ \lam f{:}o{\To}o.\,\lam x{:}o.\,f\,(f\,x)\ :\ (o \To o) \To o \To o$. Write
$\Gamma = f{:}o{\To}o,\ x{:}o$. The inner application types like this:

```{math}
\frac{
  \dfrac{(f:o{\To}o)\in\Gamma}{\Gamma \proves f : o \To o}\ (\textsf{var})
  \qquad
  \dfrac{
    \dfrac{(f:o{\To}o)\in\Gamma}{\Gamma \proves f : o \To o}\ (\textsf{var})
    \qquad
    \dfrac{(x:o)\in\Gamma}{\Gamma \proves x : o}\ (\textsf{var})
  }{\Gamma \proves f\,x : o}\ (\textsf{app})
}{\Gamma \proves f\,(f\,x) : o}\ (\textsf{app})
```

Now discharge the two assumptions with (abs), innermost first:
$$ f{:}o{\To}o \proves \lam x{:}o.\,f\,(f\,x) : o \To o, \qquad
   \proves \lam f{:}o{\To}o.\,\lam x{:}o.\,f\,(f\,x) : (o \To o) \To o \To o. $$
The term is "apply $f$ twice" — the Church numeral $\overline{2}$ from {doc}`l2_lambda_calculus`, now
wearing a type.
````

```{admonition} Run it — the machine re-derives your tree
:class: seealso
[`ch term \f x. f (f x)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20term%20%5Cf%20x.%20f%20%28f%20x%29) runs type inference on the *unannotated* term and answers $(\alpha \To \alpha) \To \alpha \To \alpha$ — the derivation you just drew, with $o$ generalized to a type variable. Under the hood the algorithm applies nothing but (var), (abs) and (app); why a type *variable* appears is the Church-vs-Curry story two sections ahead.
```

## Metatheory: what typing buys you

The three rules are cheap; their consequences are the whole point. All four statements below are theorems
about STLC (proofs in Pierce, *TAPL*, ch. 9, or Sørensen–Urzyczyn, ch. 3).

```{admonition} Theorem (uniqueness of types, Church style)
:class: important
If $\Gamma \proves t : A$ and $\Gamma \proves t : B$, then $A = B$. *Sketch:* structural induction on
$t$; each term former is the conclusion of exactly one rule, and the annotation on $\lam x{:}A$ pins the
domain. So in the Church world a well-typed term has **one** type, and type-checking is deterministic.
```

The next theorem is what makes types a *safety* discipline and not mere decoration.

```{admonition} Theorem (subject reduction / type preservation)
:class: important
If $\Gamma \proves t : A$ and $t \betared t'$, then $\Gamma \proves t' : A$. Types are invariant under
computation: reduction never turns a well-typed term into a stuck or mistyped one.
```

*Proof sketch.* The only interesting case is a top-level redex $t = (\lam x{:}A.\,s)\,u \betared s[x:=u]$.
By inversion on (app), $\Gamma \proves \lam x{:}A.\,s : A \To B$ and $\Gamma \proves u : A$ with the whole
term at type $B$; by inversion on (abs), $\Gamma, x{:}A \proves s : B$. The engine is the **substitution
lemma** — *if $\Gamma, x{:}A \proves s : B$ and $\Gamma \proves u : A$ then $\Gamma \proves s[x:=u] : B$*
(itself an easy induction on $s$). It gives $\Gamma \proves s[x:=u] : B$, which is what we needed.
Congruence cases (redex inside a subterm) follow by the induction hypothesis. $\qquad\blacksquare$

```{admonition} Theorem (strong normalization, Tait 1967)
:class: important
Every well-typed STLC term is **strongly normalizing**: *no* infinite $\betared$ sequence starts from it.
Proved by Tait's *reducibility* (computability) method — not by a naive induction on term size, which
fails. **Consequences:** the diverging term $\Omega = (\lam x.\,x\,x)(\lam x.\,x\,x)$ and the
$Y$-combinator of {doc}`l2_lambda_calculus` **have no STLC type at all** (a typed term must halt; these do
not), so STLC is *not* Turing-complete. That is the price — and the payoff — of type safety: you trade
universal computation for guaranteed termination.
```

Finally, **type-checking and type-inference for STLC are decidable** — an algorithm reads the term and
either produces its type or rejects it. Decidability of checking is the seed of the whole enterprise: it
is what lets a machine, rather than a referee, certify a proof.

## Church vs Curry: two readings of one system

Church's 1940 simple theory of types can be read in two directions, and the difference confuses everyone
once.

- **Church-style** (intrinsic / *typé à la Church*): variables carry their type in the syntax,
  $\lam x{:}A.\,t$; an untyped term is meaningless, and — by uniqueness above — every term has **at most
  one** type. Typing is a *checking* problem. This is de Bruijn's Automath and every modern kernel.
- **Curry-style** (extrinsic / type *assignment*): the terms are the bare untyped $\lam$-terms of
  {doc}`l2_lambda_calculus`, and a type is *assigned* after the fact by the same three rules with the
  annotation erased. Now a term may have **many** types. Typing is an *inference* problem.

The two are related by the **type-erasure** map $|\cdot|$ that deletes annotations: a Curry term $M$ has
type $A$ iff *some* Church term whose erasure is $M$ has type $A$. What organizes the Curry world is the
**principal type**.

````{admonition} Worked example 2 — many types, one principal type
:class: note
The identity $\lam x.\,x$ is Curry-typable at $A \To A$ for **every** type $A$: $o\To o$,
$(o\To o)\To(o\To o)$, and so on. All of these are *substitution instances* of a single most-general
type,
$$ \alpha \To \alpha \qquad (\alpha \text{ a type variable}), $$
its **principal type**. The K combinator $\lam x.\,\lam y.\,x$ has principal type
$\alpha \To \beta \To \alpha$. The **principal type theorem** (Hindley 1969, Milner 1978) says every
Curry-typable term has such a most-general type, *computable by unification* — the algorithm at the heart
of Hindley–Milner inference in ML, Haskell and Lean's elaborator. So "$\lam x.\,x$ has infinitely many
types" and "$\lam x.\,x$ has one principal type" are both true and not in tension.
````

```{admonition} Run it — Church and Curry side by side
:class: seealso
In the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda), the Curry–Howard command shows both readings of the same term.
Run [`ch term \p. p`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20term%20%5Cp.%20p) for the **Curry-style** principal
type $\alpha \To \alpha$; then run [`ch lean \p. p`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20lean%20%5Cp.%20p) for the
**Church-style** reading — the Lean theorem `theorem ch_proof {α : Prop} : α → α := fun p => p`, with a
Live Lean link to check it. Same object, two philosophies, related by erasure.
```

## Types are not (quite) sets — and the three places it breaks

The most useful intuition for a newcomer is also the most important place to install scepticism. Read a
type as the *set of its closed normal terms*: $\ [\![A \To B]\!]$ is a set of functions,
$[\![A \times B]\!]$ a Cartesian product, $[\![A + B]\!]$ a disjoint union, $\bot$ the empty set
$\varnothing$, $\top$ a singleton. For **STLC this is honest** — the calculus has sound set-theoretic
(Henkin / full type-frame) models, so nothing goes wrong. But the picture breaks three ways, and each
break motivates something later in the course.

1. **Proof relevance / intensionality.** A type's elements are *programs and proofs*, not featureless
   points. Two proofs of one proposition need not be equal, and **definitional equality** $a \equiv b$
   ("both sides compute to a common normal form", checked automatically) is a different thing from
   **propositional equality** $a = b$ (a *theorem*, an inhabitant of an identity type). This is why
   Martin-Löf type theory needs a separate identity type at all.
2. **No set of all sets.** A naive "type of all types" with the rule $\mathsf{Type} : \mathsf{Type}$ is
   **inconsistent** — Girard's paradox — the type-theoretic echo of Russell/Burali-Forti (below).
3. **Constructive existence.** An inhabitant of $\sum_{x:A} B(x)$ carries an *actual witness*: its first
   projection hands you the $x$. A set proved non-empty by classical contradiction gives you no such
   element. "There exists" means something stronger here.

```{admonition} Theorem (Girard's paradox, 1972; Hurkens 1995)
:class: warning
System U — equivalently any type theory admitting $\mathsf{Type} : \mathsf{Type}$ — is **inconsistent**:
it contains a closed term of the empty type and is no longer strongly normalizing. Hurkens (1995) gave a
strikingly short such term. **Design consequence:** consistent systems replace $\mathsf{Type}:\mathsf{Type}$
by a **universe hierarchy** $\ \mathsf{U}_0 : \mathsf{U}_1 : \mathsf{U}_2 : \cdots$, used by
Agda, Rocq and Lean (cumulative in Rocq; Lean and Agda instead lift explicitly between levels, e.g.
via `ULift`/`Lift`). So "the intuition is safe for STLC but must be dropped once universes or
proof-relevant equality enter" is not a slogan — it is a metatheorem.
```

## The Curry–Howard correspondence

Here is the conceptual centre of the lecture. Curry (1934) noticed that the types of the combinators
$K$ and $S$ are exactly Hilbert's implicational axioms; Howard (1969, published 1980) extended this to
*all* of intuitionistic natural deduction and STLC; de Bruijn arrived independently through Automath. The
statement is a dictionary.

| Logic | Type theory |
|-------|-------------|
| proposition $P$ | type $P$ |
| proof of $P$ | term $t : P$ |
| $P \To Q$ (implication) | function type $P \to Q$ |
| $P \land Q$ | product $P \times Q$ |
| $P \lor Q$ | sum $P + Q$ |
| $\top$ / $\bot$ | unit type / empty type |
| $\forall x{:}A.\,P(x)$ | dependent function $\prod_{x:A} P(x)$ |
| $\exists x{:}A.\,P(x)$ | dependent pair $\sum_{x:A} P(x)$ |
| proof normalization (cut elimination) | $\beta$-reduction |

```{admonition} Theorem (Curry–Howard, implicational fragment)
:class: important
A judgment $\Gamma \proves t : A$ is derivable in STLC **iff** the formula $A$ (arrows read as
implications) is derivable from $\Gamma$ in intuitionistic natural deduction. Under this bijection, term
formation *is* proof construction and $\betared$ *is* proof normalization. In particular a proposition is
**intuitionistically provable iff its type is inhabited** (has a closed term).
```

That last equivalence — **provability = inhabitation** — is the engine of every prover in this course.
Two of the dictionary's rows are worth seeing as terms.

````{admonition} Worked example 3 — transitivity of implication *is* composition
:class: note
The tautology $(P \To Q) \To (Q \To R) \To P \To R$ is inhabited, and its proof term is exactly function
composition (the $B$ combinator):
$$ \lam f.\,\lam g.\,\lam p.\,g\,(f\,p)\ :\ (P \To Q) \To (Q \To R) \To P \To R. $$
Given a proof $f$ of $P{\To}Q$, a proof $g$ of $Q{\To}R$, and a proof $p$ of $P$: apply $f$ to $p$ to get
a $Q$, then $g$ to get an $R$. "Chaining implications" and "composing functions" are one operation. In
Lean the same term is a one-liner:
```lean
theorem trans_imp {P Q R : Prop} : (P → Q) → (Q → R) → P → R :=
  fun f g p => g (f p)
```
````

The dictionary also draws a sharp, surprising line between intuitionistic and classical logic.

````{admonition} Worked example 4 — Peirce's law has no proof term
:class: warning
Peirce's law $\ ((P \To Q) \To P) \To P\ $ is a *classical* tautology, yet **no closed STLC term inhabits
it**. Try to build one: a term must be $\lam k.\,(?)$ with $k : (P{\To}Q){\To}P$ and $? : P$. The only
way to produce a $P$ is $k\,m$ for some $m : P \To Q$; and $m = \lam p.\,(?)$ needs a $Q$ from a $p : P$.
With $P, Q$ atomic and distinct there is *no rule* that makes a $Q$ — you are stuck. (A rigorous proof
notes that inhabitation of the implicational fragment is decidable and an exhaustive search of normal
terms finds none.) Constructively, to *prove* $((P{\To}Q){\To}P){\To}P$ you would already need a $P$,
which is what you were trying to build. A proof appears only once you *add* a classical axiom:
```lean
theorem peirce {P Q : Prop} : ((P → Q) → P) → P :=
  fun k => Classical.byContradiction (fun hnp => hnp (k (fun hp => absurd hp hnp)))
```
Delete `Classical` and it fails to type-check — dramatizing that Curry–Howard yields *intuitionistic*
proofs, and that excluded middle is an axiom you opt into, not a theorem.
````

```{admonition} Run it — see the correspondence, don't take it on faith
:class: seealso
In the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda): [`ch type 'P -> P'`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20type%20%27P%20-%3E%20P%27)
returns the identity $\lam p.\,p$; the composition demo
[`ch type '(P -> Q) -> (Q -> R) -> P -> R'`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20type%20%27%28P%20-%3E%20Q%29%20-%3E%20%28Q%20-%3E%20R%29%20-%3E%20P%20-%3E%20R%27)
returns $\lam f\,g\,p.\,g\,(f\,p)$; and
[`ch type '((P -> Q) -> P) -> P'`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20type%20%27%28%28P%20-%3E%20Q%29%20-%3E%20P%29%20-%3E%20P%27)
reports Peirce's law **uninhabited**. Then check the emitted Lean with `ch verify`. The same theorems live
in every prover in the [four-prover artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts).
```

```{admonition} Run it — build the proof yourself, one rule at a time
:class: seealso
`ch type` *searches* for the inhabitant; the Lab's interactive proof builder makes **you** construct it. Run [`prove (P -> Q) -> (Q -> R) -> P -> R`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=prove%20%28P%20-%3E%20Q%29%20-%3E%20%28Q%20-%3E%20R%29%20-%3E%20P%20-%3E%20R) and type `intro f`, `intro g`, `intro p` (three (abs) steps), then `apply g`, `apply f`, `assumption` (the (app) nodes and the (var) leaf); `qed` extracts $\lam f\,g\,p.\,g\,(f\,p)$ *and* its principal type — you have just grown Worked example 3's derivation tree tactic by tactic. Now run [`prove ((P -> Q) -> P) -> P`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=prove%20%28%28P%20-%3E%20Q%29%20-%3E%20P%29%20-%3E%20P): after `intro k` the goal is $P$ and no sequence of tactics will ever close it — Worked example 4's dead end, experienced first-hand (`abort` to leave). This tactic loop is precisely how Lean will feel in {doc}`l4_lean_intro`.
```

## A first look at dependent types

STLC gives a logic of *implications*. One generalization turns it into a logic of *all of mathematics*:
let a type **depend on a value**. The canonical example is the length-indexed vector type $\mathsf{Vec}\,A\,n$,
whose very identity mentions the natural number $n$. Two constructors do the work:

- the **dependent function** ($\Pi$-) type $\prod_{x:A} B(x)$ — a function whose *result type* varies with
  its input; when $B$ is constant it is the ordinary arrow $A \To B$, and in general it realizes the
  universal quantifier $\forall x{:}A.\,B(x)$;
- the **dependent pair** ($\Sigma$-) type $\sum_{x:A} B(x)$ — a pair $\langle a, b\rangle$ with $a : A$ and
  $b : B(a)$; it generalizes the product and realizes the *witness-carrying* existential
  $\exists x{:}A.\,B(x)$, with $\pi_1\langle a,b\rangle = a$ literally extracting the witness.

A theorem like "consing raises the length by one" becomes a *typing*: for
$\mathsf{cons} : A \To \mathsf{Vec}\,A\,n \To \mathsf{Vec}\,A\,(n{+}1)$ the output type is *computed* from
the input length.

````{admonition} Worked example 5 — $\exists$ as a $\Sigma$ with a real witness (Agda)
:class: note
A constructive proof of "there is an $n$ with $n + n = 4$" is a *pair*: the witness $2$, and evidence that
$2 + 2 = 4$ — which here is `refl`, because both sides compute to the same numeral.
```agda
∃-even : Σ ℕ (λ n → n + n ≡ 4)
∃-even = 2 , refl
```
Its first projection returns the number $2$. This is exactly what a classical non-emptiness proof cannot
give you.
````

Barendregt's **$\lambda$-cube** organizes the design space along three independent "dependency" axes:
terms-depending-on-types gives polymorphism (System F), types-depending-on-types gives $\lambda\omega$,
and types-depending-on-terms gives dependent types ($\lambda P$). STLC is the base vertex; the apex
$\lambda C$, the **Calculus of Constructions**, switches on all three and is the direct ancestor of the
CIC that Lean and Rocq run.

## Martin-Löf type theory, in one breath

Martin-Löf (1972 preprint; 1984 Padua lectures, notes by Sambin) proposed a constructive foundation meant
to stand to intuitionistic mathematics as ZFC stands to classical. Its distinctive moves: **four** judgment
forms rather than one — "$A$ type", "$A = B$", "$a : A$", "$a = b : A$" — and a uniform recipe of
**formation / introduction / elimination / computation** rules for each type former. The type formers, in
one sweep: finite types $\mathbf{0}, \mathbf{1}, \mathbf{2}$, the naturals $\N$ with a recursor, $\Pi$,
$\Sigma$, the identity type $\mathsf{Id}_A(a,b)$, $W$-types for well-founded trees, and the predicative
hierarchy $\mathsf{U}_0 : \mathsf{U}_1 : \cdots$.

The most important link back to earlier material: **the elimination rule for $\N$ is mathematical
induction.** To inhabit $\prod_{n:\N} C(n)$ it suffices to give
$$ c_0 : C(0) \qquad\text{and}\qquad c_s : \prod_{n:\N} C(n) \To C(n{+}1), $$
and the recursor then delivers $f : \prod_{n:\N} C(n)$ with the computation rules $f\,0 \equiv c_0$ and
$f\,(n{+}1) \equiv c_s\,n\,(f\,n)$. That is dependent induction as a *primitive typing rule* — the Peano
induction you know, now a term former.

Two facts to carry forward. **Intensional** MLTT (ITT) keeps type-checking decidable and is the practical
choice (Agda); **extensional** MLTT (ETT), via the equality-reflection rule "$p : \mathsf{Id}_A(a,b)$
implies $a \equiv b$", has *undecidable* type-checking. And a deep surprise: in ITT one **cannot** prove
that all proofs of $a = b$ are equal — *uniqueness of identity proofs* fails (Hofmann–Streicher groupoid
model, 1994). That gap is exactly where Homotopy Type Theory and univalence later open up.

```{admonition} Run it — induction you can watch
:class: seealso
The Lab's [`peano`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=peano) demo builds the naturals and their recursor in the untyped
world of {doc}`l2_lambda_calculus`; MLTT's $\N$-elimination is the *typed* version of the very same move.
```

## Why type theory, not ZFC, underlies modern proof assistants

Four reasons a working mathematician should care, each demonstrable.

1. **A small trusted kernel (the de Bruijn criterion).** A proof is a term; checking it is type-checking;
   type-checking is decidable and done by a *tiny* kernel. The other 99% of the system (tactics, automation,
   the editor) may be buggy and proofs are still sound, because everything must pass the kernel.
2. **Computation is native.** Definitional equality means the kernel *runs* the term: the closed numerals
   $2+2$ and $4$ are the *same* type by the conversion rule, no axiom fired. ZFC's first-order engine has
   no built-in reduction; every arithmetic step is a derivation.
3. **Constructive content / extraction.** From a proof of $\prod_{x} \exists y.\,R(x,y)$ one can *extract*
   a program $f$ with $R(x, f\,x)$ for all $x$. The proof *is* the algorithm.
4. **Theorems are types.** You *state* a theorem by writing a type and *prove* it by inhabiting the type.

Be honest, though: this is an engineering choice, not a coronation. **ZFC-style checking is alive and
proves real mathematics** — Mizar (Tarski–Grothendieck set theory) and Isabelle/ZF verify deep results
with no proof terms at all. Lean, Rocq and Agda chose type theory for decidable checking, native
computation and proofs-as-programs; Mizar chose set theory and a declarative vernacular. That contrast —
three type theories and one set theory — is the through-line of the whole mini-course.

| Prover | Foundation | `Prop` sort | Default logic |
|--------|-----------|-------------|---------------|
| **Lean 4** | Calculus of Inductive Constructions (CIC) | impredicative, proof-irrelevant | classical in Mathlib (`Classical.choice`) |
| **Rocq** (ex-Coq) | CIC (pCuIC), plus `SProp` | impredicative, proof-relevant (`SProp` adds definitional proof irrelevance) | constructive core |
| **Agda** | intensional predicative MLTT | none by default (proof-relevant) | constructive |
| **Mizar** | Tarski–Grothendieck set theory + classical FOL | *no proof terms at all* | classical |

Three type theories, one set theory; we prove the *same* elementary statements in all four — see the
[four-prover artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts). As of the course
(July 2026) the current releases are Lean 4.32.0, Rocq 9.2.0, Agda 2.8.0, and Mizar 8.1.15 (MML 5.94.1493,
1493 articles, 65k+ theorems). The de Bruijn criterion is not a slogan here: the course's own Lean
formalization is *pinned* to Lean 4.28.0 + Mathlib v4.28, runs **8062 kernel jobs with 0 `sorry`**, and is
audited with `#print axioms` — the payoff we arrive at in {doc}`l6_autoformalization`.

```{admonition} Run it — the kernel at work
:class: seealso
Install nothing yet, but note: Lean's `#check (fun (x : Nat) => x)` reports `Nat → Nat` — that is
(var)/(abs)/(app) from this lecture — and `#eval 2 + 2` prints `4` because the kernel *computed* it, not
because an axiom said so. We meet Lean properly in {doc}`l4_lean_intro`.
```

## Common pitfalls

- **"A type is just the set of its values."** Safe for STLC, dangerous when over-generalized: it fails
  once equality is proof-relevant (two proofs of $a = b$ need not be equal) and collapses entirely at a
  type-of-all-types (Girard's paradox). Install the caveat the same hour as the intuition.
- **Confusing definitional and propositional equality.** $a \equiv b$ ("computes to", checked
  automatically) is not $a = b$ (a theorem, an inhabitant of $\mathsf{Id}_A(a,b)$). This is the single
  most common MLTT stumbling block.
- **Expecting a proof term for every classical tautology.** Peirce's law and double-negation elimination
  are inhabited only with a classical axiom. Curry–Howard yields *intuitionistic* proofs; there is no
  $\lam$-term for excluded middle.
- **Treating Church- and Curry-style as rival theories.** They are two readings of one system related by
  erasure. Do not expect a unique type in the Curry world ($\lam x.\,x$ has infinitely many) or many types
  in the Church world (annotations force uniqueness).
- **Assuming the $Y$-combinator "obviously" still type-checks.** In STLC it does not — strong
  normalization forbids it — which is exactly why STLC is a *logic*, not a Turing-complete language.
  Recursion returns only with inductive types and their recursors.
- **Reading $\forall$ as a decorated $\To$ and $\exists$ as a decorated $\times$.** The *dependency* is the
  whole point: in $\prod_{x:A} B(x)$ the codomain varies with the input, and in $\sum_{x:A} B(x)$ the
  second component's type depends on the first.
- **"Proof assistant" $\Rightarrow$ "type theory".** Mizar is classical first-order logic over
  Tarski–Grothendieck set theory; its "types" are a soft convenience layer, not the foundation. Type
  theory did not *replace* ZFC — it is one design choice among several that verify real mathematics.

## Exercises

1. **(pen-and-paper)** Give a full derivation tree for $\proves \lam x{:}o.\,\lam y{:}o{\To}o.\,y\,x : o
   \To (o \To o) \To o$. Label every rule.
2. **(pen-and-paper)** Write the principal type of each Curry term: $\lam x.\,\lam y.\,y$,
   $\lam f.\,\lam x.\,f\,x$, and $\lam f.\,\lam g.\,\lam x.\,f\,(g\,x)$. For the last, name the combinator.
3. **(lab)** In the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda) run `ch type 'P -> Q -> P'` and `ch type '(P -> Q -> R) ->
   (P -> Q) -> P -> R'`. Confirm the returned terms are the $K$ and $S$ combinators, and check by hand
   that their types are Hilbert's two implicational axioms.
4. **(Lean)** Prove both in **term mode**, then re-run through `ch verify`:
   ```lean
   theorem mp   {P Q : Prop} : (P → Q) → P → Q := fun f p => f p
   theorem swap {P Q : Prop} : P ∧ Q → Q ∧ P := fun ⟨hp, hq⟩ => ⟨hq, hp⟩
   ```
   State which dictionary row each one witnesses.
5. **(pen-and-paper, hard)** Prove **subject reduction** in full for the congruence case $t\,u \betared
   t'\,u$ (given $t \betared t'$), citing the substitution lemma where used. Then explain in one sentence
   why the *converse* ("if $t'$ is typable and $t \betared t'$ then $t$ is typable") can fail.
6. **(Lean / conceptual, hard)** Take the Peirce proof from Worked example 4, delete `Classical`, and read
   the error. Then argue on paper — by attempting to construct a closed normal term — why *no*
   intuitionistic proof term exists. Contrast with your working classical proof.
7. **(Agda, hard)** Define the empty type `data ⊥ : Set` (no constructors) and its eliminator
   `⊥-elim : {A : Set} → ⊥ → A`. Explain how this realizes *ex falso quodlibet* and why $\bot$ has no
   introduction rule.
8. **(cross-prover, hard)** Prove $P \land Q \to Q \land P$ in **all four** provers using the
   [artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts): Lean (`fun ⟨hp,hq⟩ =>
   ⟨hq,hp⟩`), Agda (pattern-matching function), Rocq (an Ltac script), and Mizar (an `assume … hence`
   block). Write one paragraph on how the Mizar proof differs *in kind* — no proof term — from the other
   three.

## References

- B. C. Pierce, [*Types and Programming Languages*](https://www.cis.upenn.edu/~bcpierce/tapl/), MIT Press,
  2002 — the standard source for STLC (the var/abs/app rules, Church vs Curry, preservation, normalization).
- M. H. Sørensen & P. Urzyczyn,
  [*Lectures on the Curry–Howard Isomorphism*](https://disi.unitn.it/~bernardi/RSISE11/Papers/curry-howard.pdf),
  Elsevier, 2006 — the most complete single account tying STLC, intuitionistic logic, the $\lambda$-cube
  and inhabitation together.
- J.-Y. Girard, Y. Lafont, P. Taylor, [*Proofs and Types*](http://www.paultaylor.eu/stable/prot.pdf),
  Cambridge University Press, 1989 (free PDF) — Curry–Howard, System F, and the
  $\beta$-reduction $\leftrightarrow$ cut-elimination story.
- P. Wadler, [*Propositions as Types*](https://homepages.inf.ed.ac.uk/wadler/papers/propositions-as-types/propositions-as-types.pdf),
  CACM 58(12), 2015 — the best high-level, historically rich exposition; read this one tonight.
- P. Martin-Löf, [*Intuitionistic Type Theory*](https://archive-pml.github.io/martin-lof/pdfs/Bibliopolis-Book-retypeset-1984.pdf)
  (Padua lectures, notes by G. Sambin), Bibliopolis, 1984 — the primary source for MLTT.
- The Univalent Foundations Program, [*Homotopy Type Theory*](https://homotopytypetheory.org/book/), IAS,
  2013 — dependent types, identity types, universes, and where UIP fails.
- P. Dybjer & E. Palmgren,
  [*Intuitionistic Type Theory*](https://plato.stanford.edu/entries/type-theory-intuitionistic/) (Stanford
  Encyclopedia of Philosophy) — a citable, continuously updated conceptual reference.
- J. Avigad, L. de Moura, S. Kong, S. Ullrich,
  [*Theorem Proving in Lean 4*](https://leanprover.github.io/theorem_proving_in_lean4/) — grounds
  "Lean = CIC", the kernel/de Bruijn discussion, and the bridge to {doc}`l4_lean_intro` and
  {doc}`l6_autoformalization`.
