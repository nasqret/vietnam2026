# Lecture 6 — Auto-formalization of mathematics with Lean

```{admonition} Abstract
:class: tip
Where AI meets the kernel. We separate **statement autoformalization** (natural language → a formal
theorem statement) from **proof autoformalization** (finding a machine-checkable proof), and we make
precise the one thing a proof assistant *cannot* guarantee: that the statement means what the
mathematician meant. We then survey the **2024–2026 landscape** (AlphaProof, AlphaGeometry, the open
prover race, LeanDojo, and the benchmarks that grade them), and work through the course's flagship
**case study** — the **EML** project, which formalized a whole research paper, *every elementary
function from a single binary operator*, in Lean 4, sorry-free, across 8062 kernel jobs. The moral is
not "AI proved a theorem" but a division of labour: a human sets the target, AI assists with search
and scaffolding, and **the kernel is the sole referee**.
```

## Learning objectives

- Distinguish **statement** autoformalization from **proof** autoformalization, and state precisely the
  *faithfulness gap*: the kernel certifies $\text{proof} \proves \text{statement}$ but never
  $\text{statement} \models \text{intent}$.
- Describe the generic **LLM + proof-assistant loop** — neural search proposes, the kernel disposes —
  and name its refinements: premise selection, subgoal decomposition, expert iteration / RL-from-verifier,
  and verifier-guided self-correction.
- Situate the **2024–2026 milestones** against the **benchmarks** (miniF2F, PutnamBench, FrontierMath)
  with current numbers, and explain why olympiad scores approach $90\%$ while research-level math stays low.
- Explain **human + AI + kernel collaboration** as a working research mode (Tao's PFR, the Equational
  Theories Project) rather than a demo.
- Reconstruct the **EML case study**: the operator $\mathrm{eml}(x,y)=\exp x-\log y$, its three-line
  grammar, the $\mathsf{F36}\to\mathsf{EL}\to\mathsf{EML}$ pipeline, and what "36/36 primitives sealed"
  does and does not assert.
- Audit a formalization with `#print axioms`: tell a genuine *seal* from a *conditional* theorem, and an
  existential *witness* from a *completeness* result.
- Run and read small autoformalization artifacts across four provers (Lean, Rocq, Agda, Mizar).

## Why this matters

In about two years, machines went from solving essentially nothing at the International Mathematical
Olympiad to olympiad gold. That single fact reframes the whole course: the Curry–Howard slogan of
{doc}`Lecture 2 <l2_lambda_calculus>` — *proofs are objects a machine can check* — is now a live 2026
research programme. But the headline hides the pedagogically decisive subtlety. A proof assistant gives
an *absolute* soundness guarantee relative to a tiny trusted kernel; a natural-language "proof" from a
chatbot gives *none*. Between those poles sits autoformalization, the act of translating human
mathematics into the kernel's language — and that translation step is exactly where a machine-checked
green checkmark can still certify the wrong theorem. Learning to see that gap, and to audit what a seal
actually claims, is the transferable skill of this lecture.

## Two problems, one kernel

Two very different tasks get lumped under "autoformalization".

```{admonition} Autoformalization, split in two
:class: important
- **Statement autoformalization** — turn "$\sqrt 2$ is irrational" into a precise Lean `theorem …`
  statement. The hard part is *faithfulness*: the formal statement must *mean* what the mathematician
  meant. No proof obligation is discharged.
- **Proof autoformalization** (auto-proving) — given a fixed formal statement, *find a proof the kernel
  accepts*. The hard part is *search*: the space of tactic scripts is vast, but every candidate is
  cheaply checkable.
```

The asymmetry between them is the engine of the whole field: **proofs are hard to find but easy to
check**, so a language model can *propose* and the kernel can *dispose* — no hallucinated proof survives.
The inverse map, **informalization** (Lean → prose), is used both to make proofs readable and as a
round-trip faithfulness check.

Now the central caveat, worth ten minutes of any lecture. The Lean kernel guarantees only that the
supplied proof establishes the supplied statement. It says nothing about whether the statement captures
intent. A formalized statement can be:

- **vacuous** — a hypothesis is never satisfiable, so *anything* follows;
- **over-constrained** — it proves *less* than the mathematician claims;
- **under-constrained** — it proves *more* than is true of the intended object,

and still type-check and still be "proved". So the trust chain has one soft link, precisely where the
LLM operates.

:::{admonition} Worked example — a compiling lie
:class: note
Consider the informal claim "every prime $>2$ is odd". A *faithful* formalization is
`∀ p : ℕ, p.Prime → 2 < p → Odd p`. But the following also type-checks and is trivially provable:

```lean
theorem primes_are_odd (p : ℕ) (hp : p.Prime) (h : p = 4) : Odd p := by subst h; norm_num at hp
```

The hypothesis `p = 4` together with `p.Prime` is *never* satisfiable, so the theorem is **vacuously
true** — the kernel is perfectly happy, and it means nothing. The bug is invisible to the kernel because
the kernel is checking the proof against *this* statement, not against the mathematician's sentence.
:::

This is not a toy worry. AlphaProof auto-formalized on the order of a million competition problems (and
generated tens of millions of proof variants at test time) to build its training curriculum; Goedel-Prover
formalized $1.64$ million NuminaMath statements. When statements are manufactured at that scale, an
unfaithful-but-well-typed statement is the pipeline's core, kernel-invisible failure mode. This is why
the ProofNet benchmark measures faithfulness, not just type-correctness, and why the 2024–26 literature is
full of evaluation papers on the subject.

## The neural–symbolic loop

Every current system shares one architecture. A language model proposes a next tactic or a whole proof
term; the proof assistant executes it and returns either the new goal state or an error; a search
procedure (best-first, MCTS, or RL-guided) uses that feedback to choose what to try next. Trust rests on
the **de Bruijn criterion**: only the small kernel (in Lean, on the order of a couple of thousand lines)
re-checks the final proof term, so the model and the search harness are *untrusted* and may be arbitrarily
buggy without endangering soundness.

Layer in the refinements that distinguish systems:

- **Premise selection / retrieval augmentation** — a proof usually needs a handful of the $>280{,}000$
  Mathlib lemmas; a retriever picks the relevant ones to condition the generator (ReProver, from LeanDojo).
- **Subgoal decomposition / blueprint** — split a hard theorem into lemmas with a dependency graph
  (DeepSeek-Prover-V2's recursive pipeline; Patrick Massot's Blueprint tool).
- **Expert iteration / RL-from-verifier** — the compiler's accept/reject *is* the reward signal
  (AlphaProof, DeepSeek-Prover-V2, Goedel-Prover-V2).
- **Verifier-guided self-correction** — feed the Lean error message back to the model for a revised
  attempt (Goedel-Prover-V2: $88.1\%$ standard vs $90.4\%$ in self-correction mode).

Two families recur. A **hosted end-to-end prover** (Harmonic's Aristotle) returns a `.lean` file *only*
when it passes the kernel — zero tolerance for hallucination. An **open-weights research prover**
(DeepSeek, Goedel) you sample `pass@k` times and check yourself. Always read a benchmark number with its
$k$: a "solved" problem at `pass@8192` is not the same claim as at `pass@1`.

## The 2024–2026 landscape, by the numbers

Pin every claim to a number and a date; the numbers move monthly.

| Milestone | What / when | Number |
|---|---|---|
| **AlphaGeometry** (DeepMind+NYU, *Nature* Jan 2024) | LM proposes auxiliary constructions, a symbolic DD+AR engine closes the proof | $25/30$ recent olympiad geometry |
| **AlphaProof + AlphaGeometry 2** (IMO 2024) | Lean-checked; peer-reviewed *Nature*, 12 Nov 2025 | $28/42$ **silver**, $4/6$ problems |
| **DeepSeek-Prover-V2-671B** (Apr 2025) | open-weights; subgoal decomposition + RL-from-verifier | $88.9\%$ miniF2F, $49/658$ Putnam |
| **Goedel-Prover-V2-32B** (Aug 2025) | scaffolded data + self-correction; $8$B beats the $671$B model | $88.1\%$ ($90.4\%$ self-corr.), $86$ Putnam |
| **Seed-Prover / Aleph-Prover** (2025–26) | miniF2F saturated; Putnam nearly solved | Aleph $668/672$ Putnam (Jan 2026) |

AlphaProof solved P1, P2 and **P6** — a problem only $5$ of $609$ human contestants cracked — while
AlphaGeometry 2 dispatched the geometry P4 in $19$ seconds once formalized. The substrate underneath all
of this is **Mathlib**: $283{,}067$ theorems, $134{,}678$ definitions, $772$ contributors, well over two
million lines (July 2026), built on a fast-moving toolchain (Lean $4.32.0$, released 2026-07-13). A
formalization therefore *pins* an exact toolchain — the EML case study below is frozen at Lean/Mathlib
$4.28$.

The calibration lesson is the point. **miniF2F** ($488$ olympiad/high-school statements, cross-system
across Lean/Isabelle/Metamath/HOL Light) is essentially *saturated*. **PutnamBench** ($672$ Lean problems)
went from single digits in early 2025 to $\sim 99\%$ in eighteen months. But **FrontierMath** — hundreds
of *original, research-level* problems co-designed by Fields medalists — sat below $2\%$ at its November
2024 launch and remains far from saturated. "AI can do mathematics" is a category error unless you say
*which benchmark, which $k$, which difficulty tier*.

```{admonition} The paradigm split (IMO 2025)
:class: warning
In July 2025 two systems reached genuine **gold** at IMO 2025 — Gemini Deep Think and an OpenAI model,
each $35/42$ — but they wrote **natural-language** proofs graded by humans, with *no* machine
verification. Simultaneously, ByteDance's Seed-Prover proved $5/6$ of the same problems **formally in
Lean**. Prose proofs are flexible and legible but carry no soundness guarantee; formal proofs are
kernel-certified but costlier. Do not conflate the two — they are different systems, and only one is
checkable.
```

```{admonition} Run it — feel the loop
:class: seealso
The Boolean shadow of everything below is **functional completeness**: from the single NAND connective
you can rebuild $\lnot$, $\land$, $\lor$. Watch a language model's "propose" step made concrete in the
λ-calculus playground:
[`reduce NAND TRUE FALSE`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=reduce%20NAND%20TRUE%20FALSE) ·
[`church NAND`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=church%20NAND) ·
[`nf AND (NAND p q) r`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=nf%20AND%20%28NAND%20p%20q%29%20r).
Then compare the *proof* side across four foundations in the course's
[four-prover artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts): the same statements
in [Lean](https://github.com/nasqret/vietnam2026/tree/main/artifacts/lean),
[Rocq](https://github.com/nasqret/vietnam2026/tree/main/artifacts/rocq),
[Agda](https://github.com/nasqret/vietnam2026/tree/main/artifacts/agda) and
[Mizar](https://github.com/nasqret/vietnam2026/tree/main/artifacts/mizar).
```

## Human + AI + kernel: a working research mode

Machine-checked collaboration is already a mode of research mathematics, not a demo. Two exemplars.

**Polynomial Freiman–Ruzsa.** Within days of the 2023 Gowers–Green–Manners–Tao preprint, Tao with Yaël
Dillies and Bhavik Mehta formalized the full argument in Lean 4 in about **three weeks**, coordinated
through Massot's Blueprint. The formal statement: if $A \subseteq \mathbb{F}_2^{\,n}$ has
$|A+A| \le K|A|$, then $A$ is covered by at most $2K^{12}$ cosets of a subgroup $H$ with $|H| \le |A|$
(the exponent was later tightened $12 \to 11 \to 9$). A research result verified almost as fast as it was
written.

**The Equational Theories Project.** Tao's crowd-plus-machines effort resolved the *entire* implication
graph among the $4{,}694$ magma laws expressible with at most four operations — all $22{,}028{,}942$
ordered implications proved or refuted, every result Lean-verified — reaching its primary goal on 14 April
2025. Human insight, automated provers (Vampire), and SAT/finite-model search all contributed
interchangeably, because the kernel adjudicates. This is the modern-scale descendant of McCune's EQP
settling the Robbins conjecture by automated proof in 1996.

The lesson to carry into the case study: **Lean + Mathlib is a shared substrate** that lets amateurs,
professionals and ATP systems contribute on equal footing, since acceptance is decided by a program, not
a referee's taste.

## Case study: EML — every elementary function from one operator

The capstone is a real, completed formalization:
[**EML**](https://github.com/nasqret/eml-formalization) (Lean 4 + Mathlib $4.28$) of
**arXiv:2603.21852**, Odrzywołek's *All elementary functions from a single binary operator*.

### The mathematics

Define the single binary operator

$$
\mathrm{eml}(x,y) \;:=\; \exp(x) - \log(y),
$$

with the sole distinguished constant $1$. The claim of the paper is that $\{\mathrm{eml},\,1\}$ generates
the *entire* scientific-calculator repertoire — the constants $e$ and $\pi$, arithmetic, and every
transcendental function — through a grammar of just three productions:

$$
T \;::=\; 1 \;\mid\; x_n \;\mid\; \mathrm{eml}(T,T).
$$

Every elementary function is one fixed-shape binary tree over this single node. This is the analytic
analogue of the **Sheffer stroke** (NAND) in Boolean logic: a single functionally complete primitive from
which everything follows. The formalization mirrors the paper's own construction as a three-language
pipeline

$$
\underbrace{\mathsf{F36}}_{\text{36 named primitives}} \;\longrightarrow\;
\underbrace{\mathsf{EL}}_{\{\exp,\log,\mathrm{neg},\mathrm{inv},+,-,\cdot,/\}} \;\longrightarrow\;
\underbrace{\mathsf{EML}}_{T::=1\mid x_n\mid\mathrm{eml}(T,T)}
\;\xrightarrow{\;\iota\;}\;
\underbrace{\mathsf{EML}_{\mathbb{C}}}_{\text{same syntax, }\C\text{ semantics}},
$$

where each arrow is a total function modulo partial evaluation at the leaves, and the complex extension
$\mathsf{EML}_{\mathbb{C}}$ carries identical syntax under $\C$ semantics (needed for the trigonometric
Euler bridges).

```{admonition} Worked example 1 — the simplest constant
:class: note
$$
\mathrm{eml}(1,1) = \exp(1) - \log(1) = e - 0 = e.
$$
So $e$ is a witness tree of size $K=3$ (two leaves `1` and one `eml` node). This is the EML analogue of
"$\lnot p = \mathrm{NAND}(p,p)$": the first nontrivial thing a single operator gives you for free.
```

```{admonition} Worked example 2 — recovering log from a subtraction
:class: note
How does a *subtraction*-shaped operator produce $\log$? By the identity (for $z>0$)
$$
\log z \;=\; \mathrm{eml}\bigl(1,\ \mathrm{eml}(\mathrm{eml}(1,z),\,1)\bigr).
$$
Evaluate inside-out, writing $e=\exp 1$:
$$
\mathrm{eml}(1,z)=e-\log z,\qquad
\mathrm{eml}(e-\log z,\,1)=\exp(e-\log z)-\log 1=\exp(e-\log z),
$$
$$
\mathrm{eml}\bigl(1,\ \exp(e-\log z)\bigr)=e-\log\!\bigl(\exp(e-\log z)\bigr)=e-(e-\log z)=\log z.
$$
The tree has size $K=7$. Notice the domain constraint $z>0$ is *forced* by the innermost $\log z$: outside
it, the term has no value.
```

```{admonition} Worked example 3 — trigonometry through Euler
:class: note
Trigonometry is where the construction gets pretty. The cosine witness `cosTermℂ` evaluates to
$\exp(i\,x)$, so by Euler's formula $\exp(i x)=\cos x + i\sin x$ its **real part** is $\cos x$. This is the
smallest trig witness, $K=1273$, precisely because it stays close to Euler without algebraic detours.

The tangent uses a Cayley/Möbius quotient (recommended by an independent GPT Pro review). Writing
$w=e^{2ix}$ and multiplying numerator and denominator of $\tfrac{e^{ix}-e^{-ix}}{e^{ix}+e^{-ix}}$ by
$e^{ix}$:
$$
\frac{e^{2ix}-1}{1+e^{2ix}}
=\frac{e^{ix}-e^{-ix}}{e^{ix}+e^{-ix}}
=\frac{2i\sin x}{2\cos x}
= i\,\tan x .
$$
So the imaginary part of the witness *is* $\tan x$. This compresses the tan tree to $K=2817$,
side-stepping an $e^{ix}+e^{-ix}$ constraint explosion that had stalled progress for days. The harder
inverse functions then follow by identities such as $\arcsin x = \tfrac{\pi}{2}-\arccos x$.
```

### The engineering

Three architectural ideas made the artefact tractable.

**1. Partial evaluation.** Mathlib's real functions are *total*: `Real.log 0 = 0` and `x / 0 = 0` are
"junk values". Instead of fighting them, the denotation is `Option`-valued and returns `none` the moment
an inner $\log$ sees a non-positive argument:

```lean
noncomputable def EMLTerm.eval? (env : Nat → ℝ) : EMLTerm → Option ℝ
  | .one     => some 1
  | .var n   => some (env n)
  | .eml a b =>
      match EMLTerm.eval? env a, EMLTerm.eval? env b with
      | some va, some vb =>
          if 0 < vb then some (Real.exp va - Real.log vb) else none
      | _, _ => none
```

A claim is then stated only where the witness genuinely *has* a value — exactly as the paper does. Bridge
theorems read "*if* `F36Expr.eval? env e = some v`, *then* $\exists\,t$, `t.eval? env = some v`", never
asserting equality at a boundary point.

```{admonition} Worked example 4 — why total ≠ defined-everywhere (the §G collision)
:class: note
The natural square-root witness is $t=\exp(\tfrac12\log x)$, since $\exp(\tfrac12\log x)=\sqrt x$ for
$x>0$. But at $x=0$, using Mathlib's junk value $\log 0 = 0$,
$$
\exp\!\bigl(\tfrac12\cdot\log 0\bigr)=\exp\!\bigl(\tfrac12\cdot 0\bigr)=\exp(0)=1 \;\neq\; 0=\sqrt 0 .
$$
So **no single environment-independent term** can witness $\sqrt{\cdot}$ at the boundary — this is the
paper's own §G caveat (line 342), now a concrete Lean fact. The fix is a **quantifier flip**: prove the
*witness-family* statement
$$
\forall x\ge 0,\ \exists\,t:\mathsf{EMLTerm},\ \ t.\mathtt{eval?}\,(\lambda\_.\,x)=\mathrm{some}\,(\sqrt x),
$$
where $t$ may *depend on* $x$: at $x=0$ pick the constant-$0$ term `mkZero`; for $x>0$ pick
$\exp(\tfrac12\log x)$. The same $\forall\exists$ pattern (in `GFullFix.lean`) seals all three §G points
$\sqrt 0$, $\operatorname{arcosh}1$, $\mathrm{hypot}(0,0)$, and — as *Path C′* — widens the narrow trig
witnesses to full domain by substituting a real-valued shift so the $\arg=\pi$ branch cut is never crossed.
```

**2. K-counts.** Each witness carries an `rfl`-checked node count $K$ — a machine-checked measure of
syntactic size. They span *seven orders of magnitude*: from $K=1$ (the constant $1$) to $K=9{,}929{,}087$
($\log_b$, compiler-produced). The gap between small hand-tuned and large compiler-produced witnesses is
informative: the paper's Table 4 lists hand figures as *upper bounds*, while the artefact's compiler
figures are *actual sizes* of mechanically uniform trees.

**3. The division of labour** — the pedagogical heart. No single agent did the whole job:

| Agent | Role | Not their job |
|---|---|---|
| **Aristotle** (Harmonic) | per-chunk Lean proof search ($84/88$ chunks won) | deciding scope |
| **GPT Pro** (no shared context) | recommended the structural-compiler architecture, the Cayley tan route, and Path C′ | writing Lean |
| **Claude** (Anthropic) | orchestration, scaffolding, post-submission trig widenings | sign-off |
| **Codex** (OpenAI) | informalization (Lean → prose faithfulness check) | proof search |
| **Mathematica** (`VerifyBaseSet`) | enumerate + numerically pre-filter witness candidates | acceptance |
| **The human** | scope, taste, commit authority | hand-writing Lean proofs |
| **The Lean kernel** | the *only* acceptance criterion | judging interest |

Build reality: $36/36$ primitives sealed, $100$ public theorems, $8062$ `lake` jobs, sorry-free, no
project-specific axioms.

:::{admonition} Run it — the "hello world" of EML
:class: seealso
Reproduce Worked Example 1 yourself. Open a Lean web editor and paste:

```lean
inductive EMLTerm | one | var (n : ℕ) | eml (a b : EMLTerm)

noncomputable def EMLTerm.eval? (env : ℕ → ℝ) : EMLTerm → Option ℝ
  | .one     => some 1
  | .var n   => some (env n)
  | .eml a b => match EMLTerm.eval? env a, EMLTerm.eval? env b with
      | some va, some vb => if 0 < vb then some (Real.exp va - Real.log vb) else none
      | _, _ => none

-- e = eml(1,1):  exp 1 − log 1 = e − 0 = e
theorem e_witness : ∃ t : EMLTerm, ∀ env, EMLTerm.eval? env t = some (Real.exp 1) := by
  refine ⟨.eml .one .one, fun env => ?_⟩
  simp [EMLTerm.eval?, Real.log_one]
```

Then explore the same trees in the browser with the live
[**EML Tree Builder**](https://nasqret.github.io/eml-formalization/) — type a function, watch its
fixed-shape subtree assemble — and read the public scoreboard `PaperClaims.lean` in the
[EML repository](https://github.com/nasqret/eml-formalization).
:::

## Reading the fine print: what "sealed" guarantees

Close the loop by learning to *audit* a formalization rather than trust a checkmark.

**`#print axioms`.** This command enumerates exactly which axioms a theorem transitively depends on. EML's
audit shows only Lean/Mathlib defaults — `Classical.choice`, `propext`, `Quot.sound`. So **"sorry-free" is not
"assumption-free"**: it is "assumes classical logic and *nothing project-specific*". Every theorem in
Mathlib rests on the same three.

**Seal vs conditional theorem.** EML's EDL and $-$EML "closure" corollaries are gated on a typeclass
`EDLTranscendenceBarrier` for which *no instance is provided*. Logically sound, but potentially vacuous —
and honestly labelled as such. A genuine seal discharges its hypotheses; a scaffold leaves them open.
Always ask whether the hypotheses are ever satisfiable.

**Witness vs completeness.** A statement $\exists\,t,\ t.\mathtt{eval?}=v$ proves *representability* on the
stated domain. It is *not* a completeness theorem (the grammar captures *all* functions), *not* uniqueness,
and *not* minimality — the $K$-counts are the actual sizes of the *exhibited* trees, which the paper's
hand-tuned figures merely upper-bound. The shape of every EML seal is exactly:

$$
\text{paper\_claim\_}\pi:\quad
\exists\,t:\mathsf{EML}_{\mathbb{C}},\ \forall\,\mathrm{env}:\N\to\C,\quad
\mathsf{EML}_{\mathbb{C}}.\mathtt{eval?}\ \mathrm{env}\ t = \mathrm{some}\,\bigl((\pi:\R):\C\bigr).
$$

One literal tree (here $K=233$) plus a kernel-checked equality, under the standard axioms — no more, no
less. The human's job moves *upstream*: judging whether these are the right statements, and whether the
result is interesting. The kernel never does that.

## Common pitfalls

- **"If the Lean output compiles, the mathematics is correct."** The kernel checks proof-against-statement,
  not statement-against-intent. A compiling statement can be vacuous, over- or under-constrained. This is
  the single most important misconception to break.
- **Conflating statement and proof autoformalization.** Producing a faithful `theorem P` (judgement-laden)
  and proving a fixed `P` (search-heavy) are different tasks with different tools and failure modes.
- **Reading benchmark scores as "AI has solved mathematics."** miniF2F ($\sim 90\%$) is olympiad-level and
  often `pass@k` with large $k$; FrontierMath (research-level) sits far lower. Always ask which benchmark,
  which $k$, which tier — and date the claim, because leaderboards move monthly.
- **Assuming Lean's total functions are mathematical partial functions.** `Real.log 0 = 0` and `x/0 = 0`
  are junk values; the §G boundary points exist precisely because $\exp(\tfrac12\log 0)=1\ne 0$.
- **Treating "sorry-free" as "assumption-free."** A clean build still assumes classical logic. Read
  `#print axioms`.
- **Mistaking a conditional theorem for a seal.** A result gated on an unprovided typeclass instance is
  sound but possibly vacuous.
- **Confusing a witness with a completeness or uniqueness result.** $\exists\,t$ proves representability on
  a domain — nothing about minimality or coverage of *all* functions.
- **"The AI proved it autonomously."** In EML the human held scope and sign-off; the AIs handled search,
  architecture, scaffolding and enumeration; the kernel alone accepted. It is human-*in-charge*
  collaboration, not human-out-of-loop automation.

## Exercises

1. **(Pen & paper.)** Verify by hand that $\mathrm{eml}(1,1)=e$ and that
   $\mathrm{eml}(\mathrm{eml}(1,1),1)=\exp(e)$. What is the $K$-count of each tree?

2. **(Pen & paper.)** Confirm the log identity of Worked Example 2 by re-deriving
   $\log z=\mathrm{eml}\bigl(1,\mathrm{eml}(\mathrm{eml}(1,z),1)\bigr)$ from scratch, and state the exact
   domain of $z$ on which every intermediate $\log$ is defined.

3. **(Lab.)** Using the [four-prover artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts),
   prove NAND functional completeness in Rocq: define `nand p q := negb (p && q)` and show
   `negb p = nand p p`, `andb p q = nand (nand p q) (nand p q)`, and
   `orb p q = nand (nand p p) (nand q q)`. Then confirm the first identity on both truth values in the
   λ-lab with
   [`equiv NAND TRUE TRUE = NOT TRUE`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=equiv%20NAND%20TRUE%20TRUE%20%3D%20NOT%20TRUE) and
   [`equiv NAND FALSE FALSE = NOT FALSE`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=equiv%20NAND%20FALSE%20FALSE%20%3D%20NOT%20FALSE).

4. **(Lean.)** Complete the `e_witness` proof from the "Run it" box, then add and prove `log_witness`:
   $\forall z>0,\ $ `EMLTerm.eval? (fun _ => z) (…) = some (Real.log z)` for the tree of Worked Example 2.

5. **(Statement autoformalization — faithfulness drill.)** Take one miniF2F-style AMC problem. Write a
   faithful `theorem … : P := by sorry`, then write *two* alternative formalizations, one vacuous and one
   over-constrained, that both type-check. Explain in a sentence each why they fail to capture the intent.
   *Grade faithfulness, not provability.*

6. **(Lean — hard.)** Prove the §G collision directly: for $t=\exp(\tfrac12\log x)$ built as an `EMLTerm`,
   show `EMLTerm.eval? (fun _ => 0) t = none` (the Option semantics rejects `Real.log 0` via the `0 < vb`
   guard), hence $\neq$ `some (Real.sqrt 0)` — and contrast this with the total-function computation
   $\exp(\tfrac12\cdot\log 0)=1$ of Worked Example 4. Then prove the witness-family
   statement $\forall x\ge 0,\ \exists t,\ $`t.eval? (fun _ => x) = some (Real.sqrt x)` by case-splitting on
   $x=0$ (constant-$0$ term) versus $x>0$.

7. **(Lean — hard.)** Prove the Cayley identity underlying `tanCoreTermℂ`: for
   $x\in\left(0,\tfrac{\pi}{2}\right)$,
   $$
   \frac{\exp(2ix)-1}{1+\exp(2ix)} = i\,\tan x .
   $$
   (Hint: rewrite with `Complex.exp` and multiply through by $e^{-ix}$; you will need non-vanishing of the
   denominator on this interval.)

8. **(Audit — hard.)** Clone the [EML repo](https://github.com/nasqret/eml-formalization), run
   `#print axioms paper_claim_pi`, and confirm only `Classical.choice`, `propext`, `Quot.sound` appear. Then
   locate one of the `EDLTranscendenceBarrier`-gated corollaries and explain, in three sentences, why it is
   a *scaffold* rather than a *seal*.

## References

- A. Odrzywołek, *All elementary functions from a single binary operator*, arXiv:2603.21852 (2026). <https://arxiv.org/abs/2603.21852>
- B. Naskręcki (lead), *EML — a Lean 4 formalization of arXiv:2603.21852* (repository + `DASHBOARD.md`). <https://github.com/nasqret/eml-formalization> · live demo <https://nasqret.github.io/eml-formalization/>
- Google DeepMind AlphaProof team, *Olympiad-level formal mathematical reasoning with reinforcement learning*, Nature (12 Nov 2025), doi:10.1038/s41586-025-09833-y. <https://www.nature.com/articles/s41586-025-09833-y>
- DeepMind, *AI achieves silver-medal standard solving IMO problems* (blog, 25 Jul 2024). <https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/>
- T. H. Trinh et al., *Solving olympiad geometry without human demonstrations* (AlphaGeometry), Nature 625, 476–482 (2024). <https://doi.org/10.1038/s41586-023-06747-5>
- DeepSeek-AI, *DeepSeek-Prover-V2*, arXiv:2504.21801 (2025). <https://arxiv.org/abs/2504.21801>
- Goedel-Prover team, *Goedel-Prover-V2*, arXiv:2508.03613 (2025). <https://arxiv.org/abs/2508.03613>
- K. Yang et al., *LeanDojo: Theorem Proving with Retrieval-Augmented Language Models*, NeurIPS 2023, arXiv:2306.15626. <https://arxiv.org/abs/2306.15626>
- K. Zheng, J. M. Han, S. Polu, *miniF2F: a cross-system benchmark for formal Olympiad-level mathematics*, ICLR 2022, arXiv:2109.00110. <https://arxiv.org/abs/2109.00110>
- G. Tsoukalas et al., *PutnamBench*, NeurIPS 2024, arXiv:2407.11214; leaderboard <https://trishullab.github.io/PutnamBench/leaderboard.html>
- Z. Azerbayev et al., *ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics*, arXiv:2302.12433 (2023). <https://arxiv.org/abs/2302.12433>
- E. Glazer et al. (Epoch AI), *FrontierMath*, arXiv:2411.04872 (2024); <https://epoch.ai/frontiermath>
- T. Tao et al., *The Equational Theories Project: Advancing Collaborative Mathematical Research at Scale*, arXiv:2512.07087 (2025); retrospective <https://terrytao.wordpress.com/2025/12/09/the-equational-theories-project-advancing-collaborative-mathematical-research-at-scale/>
- T. Tao, *Formalizing the proof of PFR in Lean4 using Blueprint* (2023); project <https://teorth.github.io/pfr/>
- B. Naskręcki, K. Ono, *Mathematical discovery in the age of artificial intelligence*, Nature Physics 21, 1504–1506 (2025).
- Mathlib live statistics (accessed July 2026). <https://leanprover-community.github.io/mathlib_stats.html>

```{note}
This chapter is enriched directly from the EML `README.md`/`DASHBOARD.md` and the verified landscape
dossier as the course runs; benchmark numbers are dated July 2026 and move monthly.
```
