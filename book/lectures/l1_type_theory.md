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
- read and write a typing judgment $\Gamma \proves t : A$ and apply the three STLC rules;
- explain the difference between Church- and Curry-style typing;
- say *why* a type is not just a set, and where the "types-as-sets" picture breaks;
- name the foundation of each of the four provers we use (Lean, Agda, Rocq, Mizar).

## Judgments and contexts

Type theory is a game of **judgments**. The central one is
$$ \Gamma \proves t : A, $$
read "in context $\Gamma$, the term $t$ has type $A$." A **context** $\Gamma = x_1:A_1, \dots, x_n:A_n$
records typing assumptions about free variables. Everything is a rule for deriving new judgments from
old ones.

## The simply-typed $\lam$-calculus (STLC)

Types are built from base types by a single arrow:
$$ A, B ::= o \mid A \To B. $$
Terms are variables, abstractions and applications, and three rules type them:

```{math}
\frac{x:A \in \Gamma}{\Gamma \proves x : A}\ (\textsf{var})
\qquad
\frac{\Gamma, x:A \proves t : B}{\Gamma \proves (\lam x{:}A.\,t) : A \To B}\ (\textsf{abs})
\qquad
\frac{\Gamma \proves t : A \To B \quad \Gamma \proves u : A}{\Gamma \proves t\,u : B}\ (\textsf{app})
```

Read (abs) and (app) again: **abstraction builds a function type; application eliminates it.** Already
here is the seed of Curry–Howard — $A \To B$ will double as "$A$ implies $B$".

## Church vs Curry

- **Church-style** (typed) — variables carry their type in the syntax, $\lam x{:}A.\,t$. Each term has
  at most one type; typing is a *checking* problem.
- **Curry-style** (untyped terms, assigned types) — terms are the raw $\lam$-terms of
  {doc}`Lecture 2 <l2_lambda_calculus>`, and typing *assigns* types after the fact; a term may have many
  types (e.g. $\lam x.\,x : A \To A$ for every $A$). Typing becomes an *inference* problem.

Lean and Rocq are essentially Church-style with powerful inference; understanding both views explains a
lot of proof-assistant behaviour.

## Types are not (quite) sets

The intuition "a type is a set, a term is an element" carries you far: $A \To B$ is (roughly) the
function set $B^A$, a product type is a Cartesian product. But it breaks in instructive ways:
- **proof relevance** — in type theory a proof of $A$ is a *term* $p : A$, and *which* proof can matter;
  in set theory all proofs of a true proposition are the same (there is only "true");
- **computation** — terms *reduce*; sets don't;
- **impredicativity & size** — naïve "set of all sets" paradoxes are avoided by a stratified universe
  hierarchy $\mathsf{Type}_0 : \mathsf{Type}_1 : \cdots$, not by comprehension axioms.

## A first look at dependent types

The real power comes when a type may *depend on a term*. Two constructors generalize $\To$ and $\times$:
- the **dependent function** (Π-type) $\prod_{x:A} B(x)$ — functions whose result type varies with the
  input; it doubles as the universal quantifier $\forall x{:}A.\,B(x)$;
- the **dependent pair** (Σ-type) $\sum_{x:A} B(x)$ — pairs where the second component's type depends on
  the first; it doubles as $\exists$.

Martin-Löf type theory (MLTT) takes these, plus identity types $\mathsf{Id}_A(a,b)$, as the foundation.
This is Lecture 5's world; today we just meet it.

## The four foundations we will use

| Prover | Foundation |
|--------|-----------|
| **Lean 4** | Calculus of Inductive Constructions (CIC) |
| **Rocq** (ex-Coq) | Calculus of Inductive Constructions (CIC) |
| **Agda** | Martin-Löf Type Theory (MLTT) |
| **Mizar** | Tarski–Grothendieck **set** theory + classical FOL |

Three are type theories; Mizar is our deliberate set-theoretic contrast. We prove the *same* statements
in all four — see the [artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts).

```{admonition} Run it
:class: seealso
Install nothing yet — but notice that Lean's `#check (fun x => x)` reports a *type*, and
`#check (fun (x : Nat) => x)` reports `Nat → Nat`. That is (var)/(abs)/(app) at work.
```

## References

Sørensen–Urzyczyn, *Lectures on the Curry–Howard Isomorphism* (Ch. 1–3); Pierce, *TAPL* (Ch. 9);
Nederpelt–Geuvers, *Type Theory and Formal Proof*; Martin-Löf, *Intuitionistic Type Theory*.
```{note}
This chapter will be deepened with worked derivations and figures as the course's research pass lands.
```
