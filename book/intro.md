# Automatic Theorem Proving in Mathematics

```{admonition} A six-lecture VIASM mini-course · Hanoi 2026
:class: tip
**dr Bartosz Naskręcki** — Faculty of Mathematics and Computer Science, Adam Mickiewicz University in
Poznań · Centre for Trustworthy AI (CCAI), Warsaw University of Technology.
[Landing page](https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026) ·
[Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda) ·
[Source](https://github.com/nasqret/vietnam2026)
```

This is the **knowledge book** of the course — the text-friendly notes, with the mathematics, the code,
and the links in one place. It grows lecture by lecture; we build the foundations first, then climb.

## The through-line

The whole course rests on a single idea, stated four ways:

> A **term** is a **proof**. A **type** is a **proposition**. **Computation** is **proof
> normalization**. A **proof assistant** is a machine that checks this correspondence without ever
> getting tired.

We start where computation itself starts — a variable-binding rule you can write on a napkin, the
$\lam$-calculus — and end at a genuine research paper checked, line by line, by a kernel.

## How to read this book

Every idea appears **twice**:

- **Informally**, as something you can *run*: a reduction in the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda),
  a level in a Lean game, a small notebook.
- **Formally**, as something a machine *checks*: a definition, a theorem, a proof term. The shared
  [artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts) prove the same statements in
  Lean, Agda, Rocq and Mizar.

```{admonition} Try it now
:class: seealso
Open the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda) in another tab and type
`reduce AND TRUE FALSE`. It runs entirely in your browser — no install. We will use it constantly in
Lecture 2.
```

## The six lectures

1. **[A general introduction to type theory](lectures/l1_type_theory.md)** — judgments, the simply-typed
   $\lam$-calculus, Church vs Curry, and why proof assistants stand on type theory.
2. **[Simple calculations with the Church $\lam$-calculus](lectures/l2_lambda_calculus.md)** — $\beta/\eta$-reduction,
   Church booleans and numerals, the predecessor, the $Y$-combinator.
3. **[Propositional logic proofs](lectures/l3_propositional.md)** — natural deduction and Curry–Howard,
   taught through Emily Riehl's *A Reintroduction to Proofs*.
4. **[Introduction to Lean](lectures/l4_lean_intro.md)** — term vs tactic mode, `Nat`, induction, the
   Natural Number Game, a first real proof.
5. **[Advanced Lean](lectures/l5_lean_advanced.md)** — dependent types, typeclasses, `simp`/`ring`/`linarith`,
   Mathlib, a genuine analysis/algebra proof.
6. **[Auto-formalization of mathematics with Lean](lectures/l6_autoformalization.md)** — the 2024–2026 AI
   landscape and the **EML** project as a worked case study.

```{note}
These notes are being actively written during the course. Chapters deepen as we go, and each lecture's
current state is marked at its top.
```
