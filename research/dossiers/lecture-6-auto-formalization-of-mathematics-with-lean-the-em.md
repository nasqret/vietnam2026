# Lecture 6 — Auto-formalization of Mathematics with Lean (the EML Case Study)

> How large language models and the Lean 4 proof assistant are being wired together to translate mathematics into machine-checked form — the 2024–2026 milestones, the benchmarks that measure them, and a full case study of the EML project that sealed all 36 primitives of Odrzywołek's single-operator elementary-function paper in Lean.

## Learning objectives

- Distinguish statement autoformalization (prose → formal `theorem` statement) from proof autoformalization (formal statement → machine-checked proof), and explain the faithfulness gap: a statement can type-check yet fail to mean what the mathematician intended, because the kernel certifies proof ⊢ statement but never statement ⊨ intent.
- Describe the generic LLM + proof-assistant architecture — neural search proposes tactics/terms, the Lean kernel disposes, and the compiler's accept/reject becomes an RL reward — and name the roles of premise retrieval, subgoal decomposition, expert iteration, and self-correction.
- Situate the 2024–2026 milestones (AlphaGeometry/AG2, AlphaProof IMO-2024 silver, DeepSeek-Prover-V2, Goedel-Prover-V2, LeanDojo/ReProver, the Equational Theories Project, Tao's PFR formalization) against the benchmarks that grade them (miniF2F, PutnamBench, FrontierMath) with their current numbers, and articulate why olympiad scores near 90% while research-level math stays far lower.
- Explain the EML case study end to end: the operator eml(x,y)=exp x − log y with constant 1, the three-line grammar T ::= 1 | xₙ | eml(T,T), the F36 → EL → EML compilation pipeline, and precisely what the claim '36/36 primitives sealed, 100 theorems, 8062 lake jobs, sorry-free' does and does not assert.
- Analyze the human + AI + kernel division of labour in EML — Aristotle for chunk proof search, GPT Pro for architecture, Claude for orchestration, Codex for informalization, Mathematica for witness enumeration, the human for scope and sign-off, the Lean kernel as sole acceptance criterion — and the engineering ideas that made it tractable (Option-valued eval?, §G junk-value avoidance, Path C' range-reduction, witness-family quantifier flips).
- Read the epistemic fine print of a formalization: use #print axioms, recognise that 'sorry-free' still assumes classical logic, tell a genuine seal from a conditional theorem gated on an unprovided typeclass, and distinguish an existential witness (representability) from a completeness or uniqueness result — then write and attempt to check a small autoformalization artifact in Lean (and optionally Agda/Rocq/Mizar).

## Prerequisites

- Lambda calculus and the Curry-Howard correspondence (propositions-as-types, terms-as-proofs) from the earlier lectures/notebooks 08_curry_howard and 10d_curry_howard_playground
- Basic Lean 4 fluency: term vs tactic mode, `theorem`, `by`, a handful of tactics — from notebook 09_lean_first_steps, plus Natural Number Game (09b) and Macbeth's Mechanics of Proof (09c)
- The idea of a trusted kernel and the de Bruijn criterion (why ~2,000 lines of kernel, not the LLM, are what you trust)
- Inductive types and structural recursion (needed to read the EMLTerm grammar and eval? function)
- Elementary complex analysis: the complex exponential, Euler's formula exp(ix)=cos x + i sin x, and the principal branch cut of Complex.log at arg = π (needed for the trig witnesses and the Path C' story)
- Comfort with elementary functions and their natural domains (log needs argument > 0, sqrt needs ≥ 0, etc.)

## The autoformalization problem: statement vs proof, and the faithfulness gap

Open the lecture by cleanly separating the two tasks that get lumped under 'autoformalization'. Statement autoformalization turns a sentence of prose/LaTeX into a formal `theorem foo : P` with no proof obligation discharged; proof autoformalization (auto-proving) takes a fixed formal statement and produces a kernel-checkable proof. These are different problems with different failure modes. The decisive teaching point — worth ten minutes of the lecture — is that the Lean kernel guarantees only that the supplied proof establishes the supplied statement; it says nothing about whether the statement faithfully captures the mathematician's intent. A formalized statement can be vacuously true (a hypothesis is never satisfiable), over-constrained (proves less than claimed), or under-constrained (proves more than is true of the intended object) and still compile. So the trust chain has a soft link exactly where the LLM operates. The inverse map, informalization (Lean → prose), is used both to make proofs readable and as a round-trip faithfulness check — in the EML pipeline Codex/GPT does exactly this. Autoformalization is also a data engine, not merely a convenience: AlphaProof auto-formalized ~80 million statements to manufacture its RL curriculum.

**Key definitions**

- Autoformalization: translating informal mathematics (natural language / LaTeX) into a formal proof-assistant language (here Lean 4 + Mathlib).
- Statement autoformalization: producing a formal theorem statement faithful to an informal claim, with no proof.
- Proof autoformalization (auto-proving): given a formal statement, producing a machine-checkable proof term or tactic script.
- Faithfulness / alignment problem: a formalized statement may type-check yet not capture the informal intent (vacuous, over- or under-constrained).
- Informalization: the inverse map Lean → prose, used for readability and as a round-trip faithfulness check.

**Key results**

- The Lean kernel certifies proof ⊢ statement, never statement ⊨ intent — faithfulness must be secured by a human or by round-trip informalization; this is the field's central unsolved problem.
- AlphaProof auto-formalized roughly 80 million problem statements to build the reinforcement-learning curriculum behind its IMO-2024 result, demonstrating statement autoformalization at data-generation scale rather than as a UI feature.

## LLM + proof-assistant pipelines: the neural-symbolic loop

Give the students the architecture that every current system shares. An LLM proposes a next tactic or a whole proof term; the proof assistant executes it and returns either the resulting goal state or an error; a search procedure (best-first, MCTS, or RL-guided) uses that feedback to decide what to try next. Trust rests on the de Bruijn criterion: only the small kernel re-checks the final proof term, so the LLM and the search harness are untrusted and may be buggy without endangering soundness. Layer in the refinements that distinguish systems: premise selection / retrieval (choosing relevant Mathlib lemmas for the current goal, as in ReProver), subgoal decomposition / blueprinting (splitting a hard theorem into lemmas — DeepSeek-Prover-V2's recursive pipeline, Massot's Blueprint), expert iteration and RL-from-verifier (the compiler's accept/reject is the reward), and verifier-guided self-correction (feeding the Lean error message back to the model — Goedel-Prover-V2). Contrast the two families the students will meet in the EML case study: a hosted end-to-end prover (Aristotle/Harmonic returns a .lean file only when it passes the kernel) versus an open-weights research prover (DeepSeek/Goedel) you sample pass@k times.

**Key definitions**

- Neural-symbolic loop: LLM proposes tactics/terms, the proof assistant executes and returns the goal state or an error, and search is guided by that feedback.
- de Bruijn criterion: trust concentrated in a small kernel that re-checks every proof term; the model and search code are untrusted.
- Premise selection / retrieval augmentation: retrieving the relevant Mathlib lemmas for the current goal (ReProver).
- Expert iteration / RL-from-verifier: using the Lean compiler's accept/reject as the reward signal (AlphaProof, DeepSeek-Prover-V2, Goedel-Prover-V2).
- Subgoal decomposition / blueprint: splitting a theorem into lemmas with a dependency graph (DeepSeek-Prover-V2; Patrick Massot's Blueprint tool).

**Key results**

- ReProver (LeanDojo, NeurIPS 2023): retrieval-augmented tactic generation reaches 26.5% pass@1 on miniF2F-test with no reinforcement learning, and it discovered 33 proofs of Mathlib theorems that had no prior Lean proof.
- DeepSeek-Prover-V2 couples a DeepSeek-V3 subgoal decomposer with RL against the Lean verifier and a self-play loop, reaching 88.9% on miniF2F-test — a demonstration that the accept/reject signal alone, at scale, drives olympiad-level proving.

## The 2024–2026 milestones and the benchmarks that grade them

Walk a timeline and pin each claim to a number and a source. January 2024: AlphaGeometry (DeepMind + NTU Singapore, Nature) solves 25/30 recent olympiad geometry problems with an LLM proposing auxiliary constructions and a symbolic DD+AR engine closing the proof. July 2024: AlphaProof (Lean 4) + AlphaGeometry 2 reach IMO-2024 silver. April 2025: DeepSeek-Prover-V2 (671B) sets an open-source record. Aug 2025: Goedel-Prover-V2 leapfrogs it at a fraction of the size. Then the benchmark taxonomy — what each actually measures — and the crucial calibration lesson: olympiad benchmarks (miniF2F, PutnamBench) are approaching 90% while FrontierMath (research-level) stays low, so 'AI can do math' is a category error unless you say which benchmark. Note the pass@k caveat: many headline figures allow hundreds of samples. Keep the numbers current (July 2026) and flag that they move monthly.

**Key definitions**

- miniF2F: 488 olympiad/high-school statements (AIME, AMC, IMO plus course material), cross-system across Lean, Metamath, Isabelle and HOL Light (Zheng–Han–Polu, 2021).
- PutnamBench: a multilingual benchmark of Putnam competition problems — 672 formalized in Lean 4, 640 in Isabelle, 412 in Coq.
- FrontierMath (Epoch AI): 300 base problems (Tiers 1–3) plus 50 exceptionally hard Tier-4 problems, written by professional mathematicians, spanning IMO-level to research-level.
- pass@k: a problem counts as solved if any of k sampled attempts is accepted by the kernel.
- AlphaGeometry DD+AR: a Deductive-Database + Algebraic-Reasoning symbolic engine that an LLM feeds with auxiliary constructions.

**Key results**

- AlphaProof + AlphaGeometry 2 scored 28/42 at IMO 2024 (silver, one point below the gold line): AlphaProof solved P1, P2 and P6 (P6 was solved by only 5 of 609 human contestants) and AlphaGeometry 2 solved P4 (in 19 seconds after formalization).
- Goedel-Prover-V2-32B reaches 88.1% on miniF2F pass@32 (90.4% with self-correction) and solves 86 PutnamBench problems at pass@184 — first among open-source provers — while its 8B variant already beats DeepSeek-Prover-V2-671B at roughly 1/80 the size (Aug 2025).
- FrontierMath: no public model exceeded ~2% at the November 2024 launch, rising to roughly 30% for OpenAI's o3 — a live gauge that research-level mathematics remains far from saturated even as olympiad benchmarks near 90%.

## Human + AI collaborative formalization at scale

Before the flagship case study, show that machine-checked collaboration is already a working mode of research mathematics, not a demo. Two exemplars. (1) The Polynomial Freiman–Ruzsa conjecture: within days of the Gowers–Green–Manners–Tao 2023 preprint, Tao with Yaël Dillies and Bhavik Mehta formalized the full argument in Lean 4, coordinated through Massot's Blueprint, in about three weeks — a research result verified almost as fast as it was written. (2) The Equational Theories Project: Tao's crowd-plus-machines effort to resolve the entire implication graph among the 4694 magma laws expressible with ≤4 operations, mixing human formalizations with automated provers, all validated in Lean. This is where students should feel the shift: Lean + Mathlib as a shared substrate that lets amateurs, professionals and ATP systems contribute interchangeably because the kernel adjudicates. Connect to the author's own commentary with Ken Ono (Nature Physics 21, 1504–1506, 2025) framing the whole mathematical cycle — intuition, convention, formalization, verification, publication — as now augmented by LLMs at every stage.

**Key definitions**

- Blueprint (Patrick Massot): a human-readable proof skeleton with a dependency graph, each node linked to its Lean formalization — the coordination layer for crowd formalization.
- Mathlib: the monolithic community Lean 4 library (~5M lines) supplying the ambient definitions and lemmas every prover builds on.
- Magma / equational law: a set with one binary operation; a law is an identity such as x∘y = y∘x expressible with a bounded number of operations.

**Key results**

- Polynomial Freiman–Ruzsa: A ⊆ F₂ⁿ with |A+A| ≤ K|A| implies A is covered by at most 2K¹² cosets of a subgroup H with |H| ≤ |A| — formalized in Lean 4 (Tao–Dillies–Mehta, Nov 2023) in about three weeks via Blueprint.
- Equational Theories Project: the implication graph over the 4694 laws was fully determined — all 22,028,942 possible implications proved or refuted and formalized in Lean — with the project reaching its primary goal on 14 April 2025 after ~200 days.

## EML case study I — the mathematics: one operator for all elementary functions

This is the flagship. Odrzywołek (arXiv:2603.21852) proposes a single binary operator eml(x,y) = exp(x) − log(y) and shows that, with the sole constant 1, it generates the entire scientific-calculator repertoire — constants e and π, arithmetic, and the transcendental functions — via a grammar of just three productions. This is the analytic analogue of the NAND gate's functional completeness in Boolean logic: a single primitive from which everything follows. Teach the grammar concretely and let students build trees in the live in-browser EML Tree Builder (type a function, watch the fixed-shape subtree assemble). The formalization mirrors the paper's own construction as a three-language pipeline: 36 named paper primitives (F36) → an elementary intermediate language EL {exp, log, neg, inv, +, −, ·, /, …} → the single-operator EML, with a complex-coefficient extension EMLℂ carrying the same syntax under ℂ semantics. The trig family is where the mathematics gets pretty: cos is realized straight from Euler's formula (a witness that evaluates to exp(i·x) and projects its real part), and the harder trig functions are reached by identity manipulation rather than brute force.

**Key definitions**

- EML operator: eml(x,y) := exp(x) − log(y), with distinguished constant 1 (Odrzywołek, arXiv:2603.21852).
- EML grammar: T ::= 1 | xₙ | eml(T,T) — every elementary function is one fixed-shape binary tree over this single node.
- Sheffer/functional-completeness analogy: {eml, 1} is to elementary analysis what NAND is to Boolean logic — a single functionally complete primitive.
- F36 → EL → EML pipeline: the 36 paper primitives F36, an elementary intermediate language EL, the single-operator target EML, and its complex extension EMLℂ (identical syntax, ℂ semantics).
- Witness term: a closed EMLTerm / EMLTermℂ whose partial evaluation equals a given elementary function's value on a stated subdomain.

**Key results**

- Simplest constant witness: e = eml(1,1) (since exp 1 − log 1 = e − 0), a tree of size K = 3.
- Derived logarithm identity used by the compiler: log(z) = eml(1, eml(eml(1,z), 1)) for z > 0 — the identity that lets a subtraction-shaped operator recover log.
- cosTermℂ = mkExpℂ(mkExpℂ(eml cosLhsℂ cosRhsℂ)) evaluates to exp(i·x) for x > 0, so paper_claim_cos recovers cos x as its real part (K = 1273, smallest trig witness); the other trig functions follow by identities such as arcsin x = π/2 − arccos x.

## EML case study II — proof engineering and the human+AI+kernel collaboration

Now the how, and the collaboration story the lecture is really about. Three architectural ideas made the artefact tractable. (1) Partial evaluation: instead of fighting Mathlib's total junk values (Real.log 0 = 0, x/0 = 0), eval? is Option-valued and returns none the moment an inner log sees a non-positive argument — so a claim is stated only where the witness genuinely has a value, exactly as the paper does. (2) The §G boundary points (√0, arcosh 1, hypot(0,0)) defeat any single environment-independent witness, because the natural witness exp(½·log 0) evaluates to 1, not 0; they are sealed instead by a witness-family quantifier flip (∀ env, hyp → ∃ t, …) where the term may depend on the environment and picks mkZero at the boundary. (3) Path C' range-reduction (GPT Pro's recommendation): widen the narrow trig witnesses to full domain by substituting a real-valued shift into an existing witness, staying inside the real fragment so the arg = π branch cut is never crossed. Then the division of labour, which is the pedagogical heart: Aristotle (Harmonic) did per-chunk proof search (84/88 chunk wins); GPT Pro, with no shared context, recommended the structural-compiler architecture, the Cayley quotient for tan, and Path C'; Claude did orchestration, scaffolding and the post-submission trig widenings; Codex did informalization; Mathematica's VerifyBaseSet enumerated and numerically pre-filtered witness candidates; the human held scope, taste and commit authority; and the Lean kernel was the only acceptance criterion. Humans did NOT hand-write Lean proofs or mechanically extract chunks; the AI did NOT decide scope or sign off. Build reality: 8062 lake jobs, sorry-free, no project-specific axioms.

**Key definitions**

- Partial-evaluation kernel: EMLTerm.eval? : (ℕ→ℝ) → EMLTerm → Option ℝ, returning none whenever an inner log receives argument ≤ 0 — avoiding Mathlib's junk value log 0 = 0.
- Witness-family (quantifier flip): a theorem ∀ env, [hyp] → ∃ t : EMLTerm, t.eval? env = some v, where t may depend on env; used to seal §G boundaries and to widen trig domains.
- Path C' range-reduction: widening a narrow trig witness to full domain via EMLTermℂ.subst0, substituting a real-valued shift term for var 0 so the computation stays in the real fragment (arg = π never crossed).
- K-count: the rfl-checked node count of a witness tree — a machine-checked measure of syntactic size.
- VerifyBaseSet: the Mathematica/Rust enumeration-and-numeric-dedup procedure used to search for and validate candidate witnesses before Lean composes the proof.

**Key results**

- paper_claim_pi : ∃ t : EMLTermℂ, ∀ env : ℕ → ℂ, EMLTermℂ.eval? env t = some ((Real.pi : ℝ) : ℂ) — the shape of every seal: one literal tree (here K = 233) plus a kernel-checked equality, no extra axioms.
- The §G collision: the natural √ witness exp(½·log x) gives 1 at x = 0 (because log 0 = 0), not 0, so a single environment-independent witness is impossible; GFullFix.lean seals √0, arcosh 1 and hypot(0,0) via witness families choosing mkZero at the boundary.
- tanCoreTermℂ (GPT Pro's Cayley quotient): (e^{2ix} − 1)/(1 + e^{2ix}) = i·tan x compresses the tan witness to K = 2817, side-stepping the e^{ix}+e^{−ix} constraint explosion; arcsinTermℂ_open uses arcsin x = π/2 − arccos x to compress arcsin from K = 1,704,019 to 569,297 (3×) while widening its domain to full open (−1,1).
- Collaboration outcome: 36/36 primitives sealed, 100 public theorems, 8062 lake jobs, sorry-free, clean #print axioms — with Aristotle winning 84/88 proof-search chunks and the human never hand-writing a Lean proof.

## What 'sealed / verified' actually guarantees — reading the fine print

Close the intellectual loop by teaching students to audit a formalization rather than take a green checkmark on faith. #print axioms enumerates exactly which axioms a theorem depends on; EML's audit shows only Lean/Mathlib defaults (Classical.choice, propositional and functional extensionality) — so 'sorry-free' is not 'assumption-free', it is 'assumes classical logic and nothing project-specific'. Next, the difference between a genuine seal and a conditional theorem: EML's EDL/−EML 'closure' corollaries are gated on an EDLTranscendenceBarrier typeclass for which no instance is provided — logically sound, but potentially vacuous, and honestly labelled as such. Finally, a witness (∃ t, eval? t = v) proves representability on the stated domain; it is not a completeness theorem, not uniqueness, and not minimality — the K-counts are actual sizes of the exhibited trees, which the paper's hand-tuned figures merely upper-bound. This is the transferable skill: a machine-checked artefact means precisely what its statements say under its axioms, and the human's job moves upstream to judging whether those statements are the right ones and whether the result is interesting.

**Key definitions**

- #print axioms audit: Lean command enumerating the axioms a theorem transitively depends on.
- Conditional theorem: a result gated on a hypothesis or an unprovided typeclass instance — sound but possibly vacuous (e.g. EML's EDLTranscendenceBarrier).
- Representability vs completeness: an existential witness proves a value is expressible on a domain; it does not prove uniqueness, minimality, or that the grammar captures all functions.

**Key results**

- Sorry-free + clean axiom print ≠ assumption-free: EML depends only on Classical.choice, propext and funext — classical logic is used, as everywhere in Mathlib.
- The kernel certifies that the exhibited tree partially evaluates to the claimed value under Mathlib's definitions — nothing about the paper's prose beyond that translation; and EML's conditional EDL/−EML corollaries remain genuinely open pending an instance, a worked lesson in distinguishing a seal from a scaffold.

## Pedagogical arc
"A ~90-minute session in five movements. (0–10 min) Hook and framing: recap Curry-Howard and the de Bruijn criterion from earlier lectures, then pose the two questions — can a machine write the statement? can it write the proof? — and run a live 4-minute demo of idea → machine-checked PDF using the `arist demo` De Morgan flow (notebook 10c) so students see the loop before the theory. (10–25 min) The autoformalization problem: separate statement from proof autoformalization; drive home the faithfulness gap with a deliberately vacuous or over-constrained compiling statement, so students internalize that the kernel certifies proof ⊢ statement, not statement ⊨ intent. (25–45 min) Landscape and benchmarks: a tight timeline (AlphaGeometry 2024 → AlphaProof/AG2 IMO silver → DeepSeek-Prover-V2 → Goedel-Prover-V2), the retrieval and RL mechanics via LeanDojo/ReProver, then miniF2F / PutnamBench / FrontierMath with current numbers and the pass@k caveat, closing on the calibration lesson (olympiad ≈90%, research math ≪) and the collaborative mode (PFR, Equational Theories Project, Tao). (45–75 min) The flagship EML case study, math first: eml(x,y)=exp x − log y, the three-line grammar, e = eml(1,1), the log identity, and the Euler-bridge trig witnesses — build a couple of trees live in the web EML Tree Builder — then the engineering (Option-valued eval?, §G junk values, Path C', witness families, K-counts) and the collaboration diagram naming who did what (Aristotle / GPT Pro / Claude / Codex / Mathematica / human / kernel), landing on 8062 lake jobs, sorry-free. (75–85 min) Epistemics: audit the artefact live with #print axioms, distinguish a seal from a conditional theorem, and separate a witness from a completeness result. (85–90 min) Close with a hands-on assignment (e = eml(1,1) in Lean, or NAND functional completeness in Rocq), pointers to Natural Number Game, Mechanics of Proof, the repo and live demo, and the forecast: human-in-charge, not human-out-of-loop."

## Connections to existing material
"This lecture is the capstone that pulls together the whole falenty-2026 book/en arc and promotes the EML repository from a slide deck to a taught case study. Direct reuse from /private/tmp/.../falenty-2026/book/en/notebooks/: 08_curry_howard.md and 09_lean_first_steps.md (the propositions-as-types + kernel foundation the whole lecture assumes), 09b_natural_number_game.md and 09c_macbeth_mechanics_of_proof.md (where students should have first-touched Lean), 10_alphageometry_story.md (AlphaGeometry/AlphaProof narrative — extend its 'Successor: AlphaProof' section with the Nature-2025 numbers), 10b_aristotle_and_ai_math.md (the ecosystem table AlphaGeometry/AlphaProof/Aristotle/Kimina/LeanDojo, Erdős #728, and the author's own Nature Physics 21:1504–1506 commentary with Ken Ono — the framing this lecture generalizes), and especially 10c_aristotle_workflow.md (the `arist submit/watch/fetch/compile/informal/pdf` five-step flow that IS the EML per-chunk pipeline in miniature — reuse it as the live opener). 11_industry_impact.md and 12_further_reading.md close the arc. Lambda Lab commands (falenty-2026/lambda_lab, run as `python -m lambda_lab <cmd>`): `tour`, `reduce`, `church`, `peano`, `lean`, `ag`, `quiz`, `kb`, and — most relevant — the `eml` command (lambda_lab/lab/commands/eml.py, eml_witnesses.py; tests in test_eml_command.py) which orchestrates the chunk manifest and Aristotle submit/watch/verify loop against the paper 2603_21852, plus the Mathematica tooling in lambda_lab/proofs/eml/tools/ (mma_eml_search_v2.wls, mma_compose_lean.py, build_site.py). For L6 specifically the case study is the eml-formalization repo: read README.md and DASHBOARD.md, then the Lean sources under lambda_lab/proofs/eml/2603_21852/lean_workspace/EML/Framework/ — PaperClaims.lean (the 48+3 paper_claim scoreboard), EMLPartial.lean (the eval? kernel), KCounting.lean (rfl K-counts), StructuralLimits.lean and GFullFix.lean (§G boundaries and the witness-family flip), Complex/Builders/Trig.lean and Complex/Periodicity.lean (Cayley tan, arcsin_open, Path C'), ELToEML.lean and F36ToEL.lean (the compiler) — plus report/REPORT.pdf and notes/proof_structure.pdf for exposition, the live web/eml-tree-builder demo (nasqret.github.io/eml-formalization), and slides/ghostday_post_submission. The lecture's own slide scaffolding already exists as falenty-2026/PLAN_EML_PRESENTATION.md and PLAN_EML_FULL_CLOSURE.md. Style/structure reference: classical-foundations-ann (_toc.yml, intro.md, the interactive_papers/ pattern of pairing prose with checkable artifacts) for depth and layout."

## Artifact ideas

- **Lean 4** (introductory — the 'hello world' of the EML grammar; reproduces the simplest real seal.): Define `inductive EMLTerm | one | var (n : ℕ) | eml (a b : EMLTerm)` and `EMLTerm.eval? : (ℕ → ℝ) → EMLTerm → Option ℝ` with the guard `if 0 < vb then some (Real.exp va - Real.log vb) else none`, then prove `∃ t : EMLTerm, ∀ env, EMLTerm.eval? env t = some (Real.exp 1)`, witnessed by `eml one one` (i.e. e = eml(1,1)).
- **Lean 4** (intermediate — forces careful tracking of the Option guards through nested eml nodes and the exp/log cancellations.): Prove the compiler's logarithm identity: `∀ z : ℝ, 0 < z → EMLTerm.eval? (fun _ => z) (eml one (eml (eml one (var 0)) one)) = some (Real.log z)`, i.e. log z = eml(1, eml(eml(1,z), 1)).
- **Lean 4** (intermediate — makes the abstract 'partial evaluation vs junk values' point concrete and motivates the witness-family flip.): Exhibit the §G junk-value collision: prove that the natural square-root witness t = exp(½·log x) satisfies `EMLTerm.eval? (fun _ => 0) t = some 1`, hence `≠ some 0`, so no single environment-independent EMLTerm can witness √0.
- **Lean 4** (advanced — the term genuinely depends on the environment; teaches why ∀∃ beats ∃∀ here.): Witness-family exercise: prove `∀ x : ℝ, 0 ≤ x → ∃ t : EMLTerm, EMLTerm.eval? (fun _ => x) t = some (Real.sqrt x)` by case-splitting on x = 0 (choose the constant-0 term) versus x > 0 (choose the exp(½·log) witness) — the exact quantifier-flip GFullFix.lean uses to seal §G.
- **Lean 4** (advanced — real complex-analysis manipulation (Euler, non-vanishing denominator) that shows why the Cayley route compresses the witness.): Prove the Cayley/Möbius trig identity underlying tanCoreTermℂ: `∀ x : ℝ, x ∈ Set.Ioo 0 (Real.pi/2) → (Complex.exp (2*Complex.I*x) - 1)/(1 + Complex.exp (2*Complex.I*x)) = Complex.I * (Real.tan x : ℂ)`.
- **Lean 4** (intermediate — the point is the faithfulness gap, so `sorry` is allowed and the deliverable is the critique.): Statement-autoformalization drill (no proof required): informally state a miniF2F-style AMC problem, produce a faithful `theorem ... : P := by sorry`, then compare two candidate formalizations and identify which is vacuous or over-constrained — grading faithfulness, not provability.
- **Agda** (intermediate — reuses the same partiality idea in a different type theory, reinforcing that the design is language-agnostic.): Model the grammar abstractly: `data EML : Set where one : EML ; eml : EML → EML → EML`, a denotation `⟦_⟧ : EML → Maybe ℝ` with postulated exp/log, and a proof `⟦ eml one one ⟧ ≡ just e`; then contrast total vs partial (Maybe) semantics in a short paragraph.
- **Rocq (Coq)** (introductory — the Boolean analogue that makes 'one operator generates everything' intuitive before the analytic case.): Discrete warm-up for functional completeness: define `nand p q := negb (p && q)` and prove `forall p, negb p = nand p p`, `forall p q, andb p q = nand (nand p q) (nand p q)`, and `forall p q, orb p q = nand (nand p p) (nand q q)` — NAND generates ¬, ∧, ∨.
- **Mizar** (advanced — an optional cross-system demonstration for students curious how the same completeness idea looks in a declarative, set-theoretic prover.): State and prove functional completeness of the Sheffer stroke for propositional logic: derive `not`, `and`, `or` from a single `|` (NAND) connective, using Mizar's propositional apparatus.

## Pitfalls / misconceptions

- Believing that if the LLM's Lean output compiles, the mathematics is correct. The kernel checks that the proof matches the stated theorem, not that the theorem matches the informal intent — a compiling statement can be vacuous, over- or under-constrained. This is the single most important misconception to break.
- Conflating statement autoformalization with proof autoformalization. Producing a faithful `theorem P` (hard, judgement-laden) and producing a proof of a fixed P (search-heavy) are different tasks with different tools and failure modes.
- Reading benchmark scores as 'AI has solved mathematics'. miniF2F at ~89% is olympiad/high-school and often pass@k with large k; FrontierMath (research-level) sits far lower. Always ask which benchmark, which k, which difficulty tier.
- Assuming Lean's total functions behave like partial mathematical functions. Real.log 0 = 0 and x/0 = 0 are junk values; the EML §G boundary points (√0, arcosh 1, hypot(0,0)) exist precisely because exp(½·log 0) = 1 ≠ 0. Total ≠ mathematically defined everywhere.
- Treating 'sorry-free' as 'assumption-free'. A clean build still assumes classical logic (Classical.choice, propext, funext). Read #print axioms to know what a theorem actually rests on.
- Mistaking a conditional theorem for a genuine seal. EML's EDL/−EML closure corollaries are gated on an EDLTranscendenceBarrier typeclass with no instance provided — sound but potentially vacuous. Always check whether the hypotheses are ever discharged.
- Confusing a witness with a completeness or uniqueness result. ∃ t, eval? t = v proves representability on a domain; it says nothing about minimality (the K-counts are actual sizes, which the paper's hand-tuned figures only upper-bound) or that the grammar captures all functions.
- Believing the AI proved the theorems autonomously. In EML the human held scope, taste and sign-off; Aristotle/GPT Pro/Claude/Codex/Mathematica handled search, architecture, scaffolding and enumeration; the kernel alone accepted. It is human-in-charge collaboration, not human-out-of-loop automation.
- Thinking the kernel judges whether a result is interesting or elegant. It certifies logical soundness relative to the axioms only; interestingness, taste and the choice of what to formalize remain human.

## Canonical references

- A. Odrzywołek, "All elementary functions from a single binary operator," arXiv:2603.21852 (2026). — <https://arxiv.org/abs/2603.21852>  
  _The source paper for the flagship case study: introduces eml(x,y)=exp x − log y, the grammar S → 1 | eml(S,S), the 36 primitives, and the §G boundary caveat (paper line 342) that the formalization must handle. Read the abstract and Table 1 before class._
- Google DeepMind, "AI achieves silver-medal standard solving International Mathematical Olympiad problems" (blog, July 2024); AlphaProof team, "Olympiad-level formal mathematical reasoning with reinforcement learning," Nature (2025), s41586-025-09833-y. — <https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/>  
  _Primary source for the AlphaProof + AlphaGeometry 2 IMO-2024 silver result (28/42, P1/P2/P6 + P4) and the ~80M auto-formalized statements — the single most cited milestone of the lecture._
- DeepSeek-AI, "DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via Reinforcement Learning for Subgoal Decomposition," arXiv:2504.21801 (2025). — <https://arxiv.org/abs/2504.21801>  
  _Canonical open-weights prover paper: subgoal decomposition + RL-from-verifier, 88.9% miniF2F-test and 49/658 PutnamBench — the reference point for 'state of the art open source' that Goedel-Prover-V2 then overtakes._
- Goedel-Prover team, "Goedel-Prover-V2: Scaling Formal Theorem Proving with Scaffolded Data Synthesis and Self-Correction," arXiv:2508.03613 (2025). — <https://arxiv.org/abs/2508.03613>  
  _Current open-source leader as of the lecture: 88.1% miniF2F pass@32 (90.4% self-correction), 86 PutnamBench pass@184, and the striking 8B-beats-671B result that dramatizes how fast the frontier moves._
- K. Yang et al., "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models," NeurIPS 2023, arXiv:2306.15626. — <https://arxiv.org/abs/2306.15626>  
  _The reference for the retrieval-augmented paradigm (ReProver) and the open toolkit/benchmark used across the field; 26.5% miniF2F pass@1 with no RL and 33 newly discovered Mathlib proofs make the neural-symbolic loop concrete for students._
- K. Zheng, J. M. Han, S. Polu, "MiniF2F: a cross-system benchmark for formal Olympiad-level mathematics," ICLR 2022, arXiv:2109.00110. — <https://arxiv.org/abs/2109.00110>  
  _Defines the 488-problem cross-system benchmark every prover number in the lecture is measured against; essential for teaching what '88.9%' actually refers to and its olympiad (not research) scope._
- G. Tsoukalas et al., "PutnamBench: A Multilingual Competition-Mathematics Benchmark for Formal Theorem-Proving," NeurIPS 2024 (Datasets & Benchmarks); repository trishullab/PutnamBench. — <https://github.com/trishullab/PutnamBench>  
  _The undergraduate-competition benchmark (672 Lean 4 / 640 Isabelle / 412 Coq); its low absolute solve counts calibrate the gap between miniF2F saturation and genuinely hard problems._
- T. Tao et al., "The Equational Theories Project: Advancing Collaborative Mathematical Research at Scale," arXiv:2512.07087 (2025); project site teorth.github.io/equational_theories. — <https://terrytao.wordpress.com/2025/12/09/the-equational-theories-project-advancing-collaborative-mathematical-research-at-scale/>  
  _The exemplar of human + ATP + Lean collaboration at scale — 4694 laws, 22,028,942 implications, completed 14 April 2025 — and the natural bridge (with Tao's PFR blueprint work) from 'AI proves olympiad problems' to 'formalization is a working research mode'._

## Volatile facts (sent to fact-check)

- AlphaProof + AlphaGeometry 2 scored 28/42 at IMO 2024 — silver-medal level, one point below the gold line — with AlphaProof solving P1, P2 and P6 (P6 solved by only 5 of 609 human contestants) and AlphaGeometry 2 solving P4. (src: https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/)
- DeepSeek-Prover-V2-671B reaches 88.9% on miniF2F-test and solves 49 of 658 PutnamBench problems, via subgoal decomposition plus RL against the Lean verifier (released April 2025). (src: https://arxiv.org/abs/2504.21801)
- Goedel-Prover-V2-32B reaches 88.1% on miniF2F pass@32 (90.4% with self-correction) and solves 86 PutnamBench problems at pass@184 — first among open-source provers — while its 8B variant beats DeepSeek-Prover-V2-671B at roughly 1/80 the size (Aug 2025). (src: https://arxiv.org/abs/2508.03613)
- The Equational Theories Project completely determined the implication graph among the 4694 magma laws (≤4 operations) — all 22,028,942 implications proved or refuted and formalized in Lean — reaching its primary goal on 14 April 2025. (src: https://terrytao.wordpress.com/2025/12/09/the-equational-theories-project-advancing-collaborative-mathematical-research-at-scale/)
- FrontierMath (Epoch AI): no publicly available model exceeded ~2% at the November 2024 launch, rising to roughly 30% (OpenAI o3) — research-level mathematics remains far from saturated even as olympiad benchmarks approach 90%. (src: https://epoch.ai/frontiermath)
