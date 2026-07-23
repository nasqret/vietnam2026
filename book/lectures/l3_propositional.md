# Lecture 3 — Propositional logic proofs

```{admonition} Abstract
:class: tip
We learn to *prove* — and to see a proof as a program. Natural deduction for propositional logic, the
**BHK interpretation**, and the **Curry–Howard** reading of the connectives: implication is a function,
conjunction a product, disjunction a sum, negation a function into the empty type. We do it hands-on
through Emily Riehl's Lean game **[A Reintroduction to Proofs](https://adam.math.hhu.de/#/g/emilyriehl/ReintroductionToProofs)**,
mapping each level to an inference rule.
```

## Learning objectives

- State the introduction/elimination rules for $\To, \land, \lor, \neg, \bot$.
- Explain the BHK / Curry–Howard meaning of each connective.
- Distinguish **intuitionistic** from **classical** propositional logic.
- Drive a Lean proof with `intro`, `apply`, `exact`, `constructor`, `rcases`, `left/right`, `exfalso`,
  `by_contra`.

## Natural deduction, and the proofs-as-programs dictionary

Each connective comes with **introduction** rules (how to build a proof) and **elimination** rules (how
to use one). Under Curry–Howard these are exactly the term formers of a type:

| Logic | Type theory | Introduce | Eliminate |
|-------|-------------|-----------|-----------|
| $A \To B$ | function $A \to B$ | $\lam$-abstraction | application |
| $A \land B$ | product $A \times B$ | pairing $\langle a,b\rangle$ | projections $\pi_1,\pi_2$ |
| $A \lor B$ | sum $A + B$ | injections $\mathsf{inl},\mathsf{inr}$ | case analysis |
| $\bot$ | empty type $\varnothing$ | — (no intro) | $\mathsf{absurd}$ / `exfalso` |
| $\neg A$ | $A \to \bot$ | assume $A$, derive $\bot$ | apply to a proof of $A$ |
| $A \Leftrightarrow B$ | $(A\to B)\times(B\to A)$ | pair the two directions | project a direction |

The slogan: **to prove an implication, write a function**; to use a disjunction, **pattern-match**.

## BHK: what a proof *is*

The Brouwer–Heyting–Kolmogorov interpretation says a proof is a construction:
- a proof of $A \land B$ is a pair (proof of $A$, proof of $B$);
- a proof of $A \lor B$ is a tag saying "left" or "right" **plus** a proof of that side;
- a proof of $A \To B$ is a method turning any proof of $A$ into a proof of $B$;
- there is no proof of $\bot$.

## Intuitionistic vs classical

Intuitionistic logic **omits** the law of excluded middle $A \lor \neg A$ and double-negation
elimination $\neg\neg A \To A$. These are not provable constructively — you cannot produce a tag
("left" or "right") for an arbitrary $A$. Classical logic adds one of them as an axiom. Lean lets you
work either way; Mathlib is classical, but the *core* moves in this lecture are constructive.

```{admonition} The game IS the syllabus
:class: important
Riehl's *A Reintroduction to Proofs* introduces the tactics in exactly the order above. Each "world"
isolates one connective; each level is one introduction or elimination rule. Play it — then reread this
table and the two will click together.
```

## A worked pair

The tautology $(p \To q \To r) \To (p \To q) \To p \To r$ has as its proof term the **S combinator**
$\lam f\,g\,x.\,f\,x\,(g\,x)$ — the same object we prove in every language in the
[artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts). In Lean:

```lean
theorem s_comb {p q r : Prop} (f : p → q → r) (g : p → q) (x : p) : r := f x (g x)
```

That the *proof* and the *program* are one expression is the entire point of the course, appearing here
for the first time in a logic you already know.

```{admonition} Run it
:class: seealso
Play [A Reintroduction to Proofs](https://adam.math.hhu.de/#/g/emilyriehl/ReintroductionToProofs). After
each world, come back and identify which row of the table you just used.
```

## References

Riehl, *A Reintroduction to Proofs*; Sørensen–Urzyczyn (Ch. 2, 4); Girard–Lafont–Taylor, *Proofs and
Types* (Ch. 1–3); the falenty-2026 chapter `08_curry_howard`.
```{note}
Full derivation trees and the intuitionistic/classical boundary get worked examples as the chapter grows.
```
