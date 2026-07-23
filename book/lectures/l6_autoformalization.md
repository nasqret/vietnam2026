# Lecture 6 — Auto-formalization of mathematics with Lean

```{admonition} Abstract
:class: tip
Where AI meets the kernel. We separate **statement autoformalization** (natural language → a formal
theorem statement) from **proof autoformalization** (finding a machine-checkable proof), survey the
**2024–2026 landscape** (AlphaProof, AlphaGeometry, DeepSeek-Prover, LeanDojo, and the benchmarks that
measure them), and then work through the course's flagship **case study**: the **EML** project, which
formalized a whole research paper — *every elementary function from a single binary operator* — in Lean
4, sorry-free.
```

## Learning objectives

- Distinguish statement- from proof-autoformalization and describe an LLM + proof-assistant loop.
- Situate the main 2024–2026 systems and benchmarks and what each actually demonstrated.
- Explain, at the level of its architecture, how the EML formalization is structured and *why the kernel
  is the only acceptance criterion*.
- Articulate what "human + AI + kernel" collaboration looks like in practice.

## Two different problems

```{admonition} Autoformalization, split in two
:class: important
- **Statement autoformalization** — turn "$\sqrt 2$ is irrational" into a precise Lean `theorem …`
  statement. The hard part is *faithfulness*: the formal statement must mean what the mathematician
  meant.
- **Proof autoformalization** — given a formal statement, *find a proof the kernel accepts*. The hard
  part is *search*: the space of tactic scripts is vast, but every candidate is cheaply checkable.
```
The asymmetry is the whole game: proofs are hard to find but easy to check, so a language model can
propose and a kernel can dispose — no hallucinated proof survives.

## The 2024–2026 landscape (in brief)

Formal mathematics moved from niche to frontier: neural systems reached medal-level performance on
olympiad problems, LLM-based provers climbed the standard benchmarks, and working mathematicians began
formalizing results as they proved them. The systems to know: **AlphaProof** and **AlphaGeometry** (the
geometry/olympiad line from DeepMind), **DeepSeek-Prover** and **Goedel-Prover** (open LLM provers for
Lean), and **LeanDojo/ReProver** (retrieval-augmented proving + the tooling to train on Mathlib).
Progress is tracked on **miniF2F**, **ProofNet**, **PutnamBench** and **FrontierMath**.

```{admonition} By the numbers (verified 2026)
:class: note
- **IMO 2024:** AlphaProof + AlphaGeometry 2 scored **28/42** — silver-medal level, one point short of
  gold.
- **miniF2F:** DeepSeek-Prover-V2-671B reaches **88.9%**; Goedel-Prover-V2-32B **88.1%** (pass@32).
- **PutnamBench:** the best open provers solve of order tens of problems (DeepSeek-Prover-V2 solves 49).
- **FrontierMath** (launched Nov 2024) started with **< 2%** solved — a reminder of how far the frontier
  still is.
- **Mathlib** now holds **≈ 283,000 theorems** across **> 2 million lines** — the substrate all of this
  runs on.

Each figure traces to a source in [`research/fact_checks.md`](https://github.com/nasqret/vietnam2026/blob/main/research/fact_checks.md).
```

## Case study: the EML project

The capstone is a real, completed formalization: [**EML**](https://github.com/nasqret/eml-formalization)
(Lean 4 + Mathlib) of **arXiv:2603.21852**, Odrzywołek's *All elementary functions from a single binary
operator*. Its shape is exactly the "two problems" above, done for a whole paper:

- **The claim.** Every one of the paper's 36 elementary-function primitives is realized by a concrete
  **`EMLTerm`** — a syntax tree in a single-binary-operator grammar $T ::= 1 \mid x_n \mid \mathrm{eml}(T,T)$ —
  whose partial evaluation `eval?` (an `Option ℂ`-valued denotation) provably equals the paper's stated
  value on the right domain.
- **The acceptance criterion.** *The Lean kernel, and nothing else.* Each witness is a literal syntax
  tree; the theorem says its `eval?` equals `Real.sin x`, `Real.exp x`, … There is no `sorry`, no axiom
  abuse (checked by `#print axioms`), across **8062** `lake` build jobs.
- **The hard corners.** The three boundary points the paper itself flags ($\sqrt 0$, $\operatorname{arcosh} 1$,
  $\mathrm{hypot}(0,0)$) are sealed by witness-*family* theorems ($\forall\,\mathrm{env},\ \dots \to \exists t,\dots$),
  and full-domain trig needed a range-reduction argument ("Path C′"). These are precisely the places
  where human insight, AI assistance, and kernel checking had to meet.

There is even a live **[EML Tree Builder](https://nasqret.github.io/eml-formalization/)** to explore the
witness trees interactively.

```{admonition} The lesson
:class: seealso
EML is not "AI proved a theorem." It is a workflow: a human sets the target and the architecture, AI
assists with search and boilerplate, and the **kernel is the referee**. That division of labour — not
full automation — is what makes formalized research mathematics practical today.
```

## References

The EML repository (`README.md`, `DASHBOARD.md`) and arXiv:2603.21852; the landscape citations collected
in [`research/`](https://github.com/nasqret/vietnam2026/tree/main/research); Mathlib and the Lean
community pages.
```{note}
This chapter is enriched directly from the EML `DASHBOARD.md` and the verified landscape dossier as the
course runs.
```
