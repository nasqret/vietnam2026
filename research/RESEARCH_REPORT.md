# Research report — master synthesis

From the `atp-course-research` workflow: 8 dossiers → 30 fact-checks → synthesis. See [`dossiers/`](dossiers/README.md), [`fact_checks.md`](fact_checks.md).

## The through-line
The course is one continuous argument: a proof is a mathematical object a machine can check, and the native language for that object is type theory. It opens (L1) by growing Church's untyped λ-calculus into the simply-typed λ-calculus and reading the Curry–Howard correspondence straight off the typing rules — propositions are types, proofs are terms, β-reduction is proof normalization, an inhabited type is a provable proposition — then previews dependent types, Martin-Löf/CIC, and maps the four systems the course uses (Lean = CIC, Rocq = CIC, Agda = MLTT, Mizar = Tarski–Grothendieck set theory). L2 makes the untyped substrate concrete and computational — capture-avoiding substitution, Church–Rosser, Church encodings, the Kleene predecessor, and Y — installing "compute by reducing" as the engine L6 recasts as "prove by type-checking." L3 cashes Curry–Howard out on paper and in Lean through Riehl's game: natural-deduction rules become tactics, BHK meaning becomes proof terms, and the intuitionistic/classical boundary (Peirce, LEM, Glivenko) becomes a visible design choice. L4 is first contact with Lean 4 as a tool — term vs tactic mode over one kernel-checked term (the de Bruijn criterion), Prop vs data, induction on ℕ, and the beginner tactic/automation vocabulary. L5 scales that to a working mathematician's kit — dependent types and typeclasses, Mathlib and how to search it, the tactic zoo, calc, recursion, and a taste of metaprogramming. L6 closes the loop: the same kernel that accepts `fun p => p` accepts research-scale formalizations, so autoformalization (statement vs proof, and the faithfulness gap the kernel cannot close) and the 2024–26 AI+ATP wave (AlphaProof, the open-weight prover race, the benchmark ladder, collaborative formalization) land on a concrete case study — the EML single-operator formalization — under the banner "human-in-charge, kernel-as-arbiter."

## Recommended tool versions (verified)

- **lean**: 4.32.0 (stable, 2026-07-13; latest RC 4.33.0-rc1, 2026-07-15). For the EML case study keep the reproducible pin Lean 4.28.0 (2026-02-17) via lean-toolchain; kernel is CIC-family dependent type theory.
- **mathlib**: Track the Mathlib commit matching your Lean toolchain (v4.32.0 for current stable; the EML artifact is pinned to Mathlib v4.28). Live scale ~283,067 theorems / 134,678 definitions / 772 contributors / >2M lines (leanprover-community mathlib_stats, dated at cite time).
- **agda**: 2.8.0 (stable, 2025-07-05, self-contained single binary); agda-stdlib 2.x (v2.3). Intensional predicative MLTT; use --safe for the artifacts, Cubical Agda for any HoTT aside.
- **rocq**: 9.2.0 (stable, 2026-03-27; renamed from Coq, first Rocq release 9.0.0 on 2025-03-12; 9.3 only branched 2026-07-08, not released). Kernel is CIC; Mathematical Components 2.5.0 (2025-10-13).
- **mizar**: 8.1.15 with MML 5.94.1493 (2025-05-30): 1493 articles, 65,000+ theorems, 13,000+ definitions; classical FOL over Tarski-Grothendieck set theory.

## Per-lecture abstracts & session plans

### Lecture 1 — From lambda-Calculus to Type Theory: The Foundations of Proof Assistants

This on-ramp grows Church's untyped lambda-calculus into the simply-typed lambda-calculus and reads the Curry-Howard correspondence directly off the three typing rules: propositions are types, proofs are terms, beta-reduction is proof normalization, and an inhabited type is a provable proposition. Students distinguish Church-style (intrinsic, unique-typing) from Curry-style (extrinsic, principal-type) typing, wield the types-as-sets intuition, and see exactly where it breaks: proof-relevance, Girard's paradox (System U inconsistent, 1972), and constructive existence. A single-breath tour of dependent types and Martin-Lof type theory shows how forall/exists become Pi/Sigma, how Nat-elimination IS mathematical induction, and why consistency forces a cumulative universe hierarchy. The lecture closes with the map that organizes the whole course: Lean = CIC, Rocq = CIC, Agda = MLTT, and Mizar = classical first-order logic over Tarski-Grothendieck set theory, and why a small kernel, decidable type-checking and native computation make type theory the assistant-builder's choice.

**Session plan:** 90 min, six movements. (0-8) Hook: Omega = (lambda x.x x)(lambda x.x x) never halts -- can we rule it out mechanically? (8-28) STLC: judgment Gamma |- t : sigma, the Var/Abs/App rules on the board, derive lambda f.lambda x. f(f x); subject reduction, strong normalization, Y and Omega untypable. (28-38) Church vs Curry typing via a live lambda-lab `ch` demo (Curry-style alpha->alpha vs emitted Church-style Lean term). (38-58) The Curry-Howard dictionary as a table + three live `ch type` demos (P->P = identity, transitivity = composition, Peirce refused). (58-78) Dependent types + MLTT in one breath: Vec A n, Pi/Sigma as quantifiers, the identity type, Nat-elimination = induction, Girard's paradox -> universes. (78-90) Foundations map (Lean/Rocq/Agda/Mizar) and the de Bruijn criterion; assign Wadler as the evening read.

### Lecture 2 — Computing with the Untyped lambda-Calculus: Church Encodings, Confluence, and Recursion

A hands-on lecture that turns the three-rule grammar of the untyped lambda-calculus into a working programming language. Students perform capture-avoiding substitution and beta/eta-reduction by hand, meet the Church-Rosser (confluence) theorem and its corollary that beta-normal forms are unique up to alpha-equivalence, and exhibit Omega to see that normal forms need not exist and that evaluation strategy (normal vs applicative order) genuinely matters. They then build everything from functions alone -- booleans, pairs, Church numerals, SUCC/PLUS/MULT/POW, and Kleene's pair-shifting predecessor -- reproducing each calculation live in the lambda_lab REPL, before recovering recursion without names via the Y combinator. The finale ties lambda-definability to Turing-completeness and the undecidability of beta-convertibility (Church 1936), planting 'compute by reducing' as the engine later lectures recast as 'prove by type-checking.'

**Session plan:** 90 min, five movements. (0-10) Bridge from the Alligator-Eggs metaphor to t ::= x | lambda x.t | t t; run `lam` for the AST and free vars. (10-30) Substitution done right: the capture trap (lambda y.x)[x:=y], alpha-equivalence, beta-redex; trace (lambda x.x x)(lambda y.y). (30-45) Non-termination and strategy: Omega, normal vs applicative order on (lambda x.y)Omega; state Church-Rosser + uniqueness + leftmost-reduction (Curry-Feys 1958); eta as extensionality (REPL is beta-only). (45-70) Programming with functions: booleans, pairs, numerals, PLUS/MULT/POW live; the Kleene predecessor 'wisdom-teeth' story and pair-shift, then SUB/LEQ/EQ. (70-90) Recursion without names: Y traced two steps, Z for eager order; meta-payoff -- lambda-definable = general recursive, beta-convertibility undecidable.

### Lecture 3 — Propositional Logic as Programs: Natural Deduction, Curry-Howard, and a Reintroduction to Proofs in Lean

A reintroduction to proofs through Gentzen's natural deduction and Emily Riehl's Lean 4 game 'A Reintroduction to Proofs.' Students state the introduction/elimination rules for ->, and, or, and falsum, give the connectives their constructive BHK meaning, and read each rule twice: as a proof tree and as a typed term (-> a function, and a pair, or a sum, falsum the empty type, not-P as P->falsum). Every Lean tactic they use (intro, exact, apply, constructor, rcases/obtain, left/right, exfalso, by_contra) is mapped back to the exact rule or term-former it performs and to its effect on the underlying partial proof term. The lecture marks precisely where intuitionistic reasoning ends and classical logic begins -- excluded middle, double-negation elimination and Peirce's law, which the game quarantines in its own ClassicalWorld -- and states Glivenko's theorem as the measure of the gap.

**Session plan:** 90 min, chalk -> dictionary -> keyboard. (0-12) Callback to `fun p => p`; 'what IS a proof?' -> a construction (BHK). (12-28) Chalk natural deduction: intro/elim for ->,and,or,falsum; and-commutativity by hand, hypothesis discharge in ->-intro. (28-40) The Curry-Howard table + the tactic<->rule<->term table; live `ch build P -> P` filling a hole. (40-72) Keyboard: play TypeWorld->FunctionWorld->ImplicationWorld->Conjunction/DisjunctionWorld->Empty/NegationWorld, instructor narrating each tactic to its rule. (72-84) The classical boundary: ClassicalWorld, `ch type '((P->Q)->P)->P'` reported uninhabited, Glivenko, and the honest cost of classical existence proofs. (84-90) One-slide tactic<->rule recap; homework: finish NegationWorld and one De Morgan law.

### Lecture 4 — First Contact with Lean 4: Proofs as Terms, Tactics, and Induction over the Naturals

First contact with Lean 4 as a working proof assistant. Students write the same theorem in term mode (a pure lambda-term) and tactic mode (a `by` script), see both elaborate to one term that the small trusted kernel checks (the de Bruijn criterion, audited by #print axioms), and read Prop vs data through the Curry-Howard dictionary -- with exists as a dependent pair whose proof is literally a pair of witness and evidence. They prove statements about the naturals by structural induction, close goals with rfl/rw/simp, and feel why add_zero is rfl but zero_add needs induction (Nat.add recurses on its second argument). A beginner tactic and automation vocabulary (intro, exact, apply, rcases, constructor, induction; decide, omega, and a peek at ring/linarith), the elan/lake/Mathlib toolchain, and one honest end-to-end proof (Gauss's sum) plus the library-driven-corollary idiom send students onward to NNG4 and Macbeth.

**Session plan:** 90 min. (0-15) Two modes, one term: and_comm in term and tactic mode; #print / #print axioms show the same kernel-checked term; the de Bruijn criterion. (15-30) Prop vs data and the Curry-Howard dictionary; exists as a dependent pair, the proof <2, rfl>. (30-52) Naturals by induction: inductive Nat, why add recurses on its second argument, add_zero = rfl vs zero_add by induction, rebuild add_comm (NNG4 Addition World -- note add_comm is the L3 'level boss', followed by add_assoc (L4) and add_right_comm (L5)). (52-66) rfl/rw/simp mechanics (including rw reverse) and the beginner tactic set. (66-78) Automation scope: decide, omega, a peek at ring/linarith and their failure modes. (78-86) Tooling: elan, lake, `lake exe cache get`, lean-toolchain pinning, #check/#eval/InfoView. (86-90) Gauss's sum end-to-end + a Mathlib one-liner (Nat.exists_infinite_primes); point to NNG4/Macbeth.

### Lecture 5 — Lean 4 for Working Mathematicians: Dependent Types, Mathlib, and the Tactic Zoo

A tour of Lean 4 as a mathematician's tool. Students read dependent function types (forall n, P n as the Pi-type (n : Nat) -> P n), distinguish Prop from Type and understand proof irrelevance and the large-elimination restriction, and use structure and class to read Mathlib's algebraic hierarchy (Monoid -> Group -> Ring -> Field) together with instance resolution and the diamond problem. They learn to search a library of roughly 283,000 theorems with exact?/apply?/rw?, Loogle and LeanSearch, and to match each automation tactic to the goal it owns -- ring, linarith/nlinarith, omega, norm_num, field_simp, positivity, gcongr, decide, simp -- plus the new SMT-style grind (with the honest note that polyrith is retired). calc blocks, structural versus well-founded recursion (termination_by/decreasing_by), one analysis/algebra theorem carried end to end, and a minimal macro/elab expose the parse -> macro-expand -> elaborate -> kernel pipeline and the fact that both proof modes produce the same Expr.

**Session plan:** 90 min, roughly 60% live coding. (0-10) Recap: Lean = lambda-calculus + dependent types; and_comm both modes, #print axioms. (10-25) Pi-types, Prop vs Type, proof irrelevance and large elimination, Sigma/Subtype. (25-40) structure/class, instance resolution, Mathlib's Monoid->Group->Ring->Field tower and the diamond problem. (40-52) Mathlib scale (~283k theorems), naming as a decoder, and live search hunting Nat.Prime.irrational_sqrt via exact?/Loogle. (52-68) Tactic zoo: Cauchy-Schwarz and AM-GM via nlinarith [sq_nonneg ...], then ring/omega/norm_num/field_simp/positivity/gcongr/decide; polyrith retired -> grind/grobner on a polynomial goal. (68-78) calc (Macbeth have/calc) + structural EMLTerm.size vs well-founded Nat.gcd. (78-88) sqrt2 irrational end-to-end (Mathlib one-liner + by_contra sketch) and a 3-line tactic macro. (88-90) Bridge to the EML case study.

### Lecture 6 — Autoformalizing Mathematics: AI + Lean and the EML Case Study

The capstone: how large language models and Lean 4 are being wired together to translate mathematics into machine-checked form. Students separate statement autoformalization from proof autoformalization and confront the faithfulness gap -- the kernel certifies proof |- statement but never statement |= intent, so a statement can type-check yet be vacuous, over- or under-constrained. They survey the 2024-26 milestones (AlphaProof's IMO-2024 silver at 28/42, the open-weight prover race from DeepSeek-Prover-V2 to Goedel-Prover-V2, LeanDojo/ReProver) against the benchmark ladder that grades them (miniF2F near-saturated, PutnamBench near-complete, FrontierMath still low at roughly 25%) and the collaborative wave (the Equational Theories Project, Tao's PFR-via-Blueprint). A full case study of the EML formalization -- the single operator eml(x,y) = exp x - log y, its three-line grammar, the human+AI+kernel division of labour, and what 'sealed / sorry-free' does and does not guarantee (classical axioms still assumed; witness != completeness) -- lands the course on 'human-in-charge, kernel-as-arbiter.'

**Session plan:** 90 min, five movements. (0-10) Hook: competition math went from ~nothing to olympiad gold in two years; split formal (kernel-checked) vs natural-language proofs. (10-25) The autoformalization problem: statement vs proof; a compiling-but-vacuous statement dramatizes the faithfulness gap. (25-45) Landscape + benchmarks: AlphaProof/AlphaGeometry, the DeepSeek->Goedel open-weight race, miniF2F/PutnamBench/FrontierMath with current (July-2026-frozen) numbers and the pass@k caveat; collaborative formalization (ETP, PFR). (45-75) EML case study -- math first (eml, grammar, e = eml(1,1), Euler-bridge trig), then engineering (Option-valued eval?, the section-G junk-value collision, Path C' range-reduction, witness-family quantifier flips) and the who-did-what collaboration diagram. (75-85) Epistemics: run #print axioms live, distinguish a seal from a conditional theorem, and a witness from a completeness result. (85-90) Close: human-in-charge, not human-out-of-loop; hands-on assignment (e = eml(1,1) in Lean, or NAND completeness in Rocq).

## Prerequisite graph

- Untyped lambda calculus (grammar, free/bound vars) → Beta-reduction and evaluation strategies
- Beta-reduction and evaluation strategies → Church encodings (booleans, numerals, pairs)
- Church encodings (booleans, numerals, pairs) → Recursion via the Y combinator
- Beta-reduction and evaluation strategies → Confluence / Church-Rosser
- Untyped lambda calculus (grammar, free/bound vars) → Simply-typed lambda calculus
- Beta-reduction and evaluation strategies → Simply-typed lambda calculus
- Simply-typed lambda calculus → Curry-Howard correspondence
- Natural deduction (intro/elim rules) → Curry-Howard correspondence
- BHK interpretation → Curry-Howard correspondence
- BHK interpretation → Intuitionistic vs classical logic
- Curry-Howard correspondence → Dependent types (Pi/Sigma, identity type)
- Simply-typed lambda calculus → Dependent types (Pi/Sigma, identity type)
- Dependent types (Pi/Sigma, identity type) → Martin-Lof type theory (MLTT)
- Dependent types (Pi/Sigma, identity type) → Calculus of Inductive Constructions (CIC)
- Martin-Lof type theory (MLTT) → Calculus of Inductive Constructions (CIC)
- Calculus of Inductive Constructions (CIC) → Prop vs Type / proof irrelevance
- Curry-Howard correspondence → Lean term mode vs tactic mode
- Calculus of Inductive Constructions (CIC) → Lean term mode vs tactic mode
- Lean term mode vs tactic mode → Kernel / de Bruijn criterion
- Natural deduction (intro/elim rules) → Lean tactics (intro/apply/rcases/constructor)
- Intuitionistic vs classical logic → Classical tactics (by_contra, Classical.em)
- Lean term mode vs tactic mode → Structural induction on Nat
- Structural induction on Nat → Rewriting (rfl/rw/simp)
- Rewriting (rfl/rw/simp) → Mathlib and lemma search
- Prop vs Type / proof irrelevance → Structures and typeclasses
- Dependent types (Pi/Sigma, identity type) → Structures and typeclasses
- Rewriting (rfl/rw/simp) → Automation tactics (ring/omega/linarith/grind)
- Automation tactics (ring/omega/linarith/grind) → calc blocks
- Structural induction on Nat → Structural vs well-founded recursion
- Lean term mode vs tactic mode → Metaprogramming (macro/elab)
- Kernel / de Bruijn criterion → Autoformalization and the faithfulness gap
- Curry-Howard correspondence → Autoformalization and the faithfulness gap
- Autoformalization and the faithfulness gap → LLM + proof-assistant pipelines
- LLM + proof-assistant pipelines → Benchmarks (miniF2F/PutnamBench/FrontierMath)
- Mathlib and lemma search → EML case study
- Structures and typeclasses → EML case study
- Structural vs well-founded recursion → EML case study
- Autoformalization and the faithfulness gap → EML case study

## Reading list (tiered)

- _core_ · Philip Wadler, "Propositions as Types," Communications of the ACM 58(12):75-84, 2015. — <https://homepages.inf.ed.ac.uk/wadler/papers/propositions-as-types/propositions-as-types.pdf>
- _core_ · Benjamin C. Pierce, Types and Programming Languages, MIT Press, 2002 (ISBN 0-262-16209-1). — <https://www.cis.upenn.edu/~bcpierce/tapl/>
- _core_ · Jean-Yves Girard, Yves Lafont, Paul Taylor, Proofs and Types, Cambridge Tracts in TCS 7, CUP, 1989 (free PDF). — <http://www.paultaylor.eu/stable/prot.pdf>
- _core_ · H. P. Barendregt & E. Barendsen, Introduction to Lambda Calculus (revised, 2000), free lecture notes. — <https://www.cse.chalmers.se/research/group/logic/TypesSS05/Extra/geuvers.pdf>
- _core_ · J. Avigad, L. de Moura, S. Kong, S. Ullrich, Theorem Proving in Lean 4 (official online textbook). — <https://leanprover.github.io/theorem_proving_in_lean4/>
- _core_ · J. Avigad, K. Buzzard, R. Y. Lewis, P. Massot, Mathematics in Lean (MIL). — <https://leanprover-community.github.io/mathematics_in_lean/>
- _core_ · Heather Macbeth, The Mechanics of Proof (Fordham Math 2001), online book + github.com/hrmacbeth/math2001. — <https://hrmacbeth.github.io/math2001/>
- _core_ · Natural Number Game 4 (NNG4), leanprover-community, on the Lean 4 Game engine (in-browser, no install). — <https://adam.math.hhu.de/#/g/leanprover-community/NNG4>
- _core_ · Emily Riehl, "A Reintroduction to Proofs" — Lean 4 game (17 worlds, pinned to Lean v4.23.0, MIT), JHU Fall 2025 seminar; repo github.com/emilyriehl/ReintroductionToProofs. — <https://adam.math.hhu.de/#/g/emilyriehl/ReintroductionToProofs>
- _core_ · Joan Moschovakis, "Intuitionistic Logic," Stanford Encyclopedia of Philosophy (BHK, Heyting rules, Glivenko). — <https://plato.stanford.edu/entries/logic-intuitionistic/>
- _supplementary_ · M. H. Sorensen & P. Urzyczyn, Lectures on the Curry-Howard Isomorphism, Studies in Logic 149, Elsevier, 2006. — <https://disi.unitn.it/~bernardi/RSISE11/Papers/curry-howard.pdf>
- _supplementary_ · Peter Selinger, Lecture Notes on the Lambda Calculus, arXiv:0804.3434 (2008/2013) — source for the Kleene predecessor 'wisdom-teeth' history (note: it poses PRED as an exercise and gives no term). — <https://arxiv.org/abs/0804.3434>
- _supplementary_ · Raul Rojas, A Tutorial Introduction to the Lambda Calculus, arXiv:1503.09060 (2015). — <https://arxiv.org/abs/1503.09060>
- _supplementary_ · E. Barendsen et al., "The Lambda Calculus," Stanford Encyclopedia of Philosophy (Church-Rosser, uniqueness of normal forms). — <https://plato.stanford.edu/entries/lambda-calculus/>
- _supplementary_ · Per Martin-Lof, Intuitionistic Type Theory (Padova lectures, notes by G. Sambin), Bibliopolis, 1984. — <https://archive-pml.github.io/martin-lof/pdfs/Bibliopolis-Book-retypeset-1984.pdf>
- _supplementary_ · The Univalent Foundations Program, Homotopy Type Theory: Univalent Foundations of Mathematics, IAS, 2013. — <https://homotopytypetheory.org/book/>
- _supplementary_ · R. Nederpelt & H. Geuvers, Type Theory and Formal Proof: An Introduction, CUP, 2014. — <https://doi.org/10.1017/CBO9781139567725>
- _supplementary_ · A. Baanen, A. Bentkamp, J. Holzl, J. Limperg et al., Metaprogramming in Lean 4 (syntax/macro/elab, Expr, MetaM/TacticM). — <https://leanprover-community.github.io/lean4-metaprogramming-book/>
- _supplementary_ · Lean community blog, "Searching for theorems in Mathlib" (exact?/apply?/rw?, Loogle, LeanSearch, Moogle, LeanExplore). — <https://leanprover-community.github.io/blog/posts/searching-for-theorems-in-mathlib/>
- _supplementary_ · Dag Prawitz, Natural Deduction: A Proof-Theoretical Study, Almqvist & Wiksell, 1965 (Dover reprint 2006). — <https://store.doverpublications.com/products/9780486446554>
- _advanced_ · Alonzo Church, "An Unsolvable Problem of Elementary Number Theory," Amer. J. Math. 58, 345-363, 1936. — <https://ics.uci.edu/~lopes/teaching/inf212W12/readings/church.pdf>
- _advanced_ · W. A. Howard, "The formulae-as-types notion of construction" (1969 ms.), in To H. B. Curry, Academic Press, 1980, 479-490. — <https://www.cs.cmu.edu/~crary/819-f09/Howard80.pdf>
- _advanced_ · H. P. Barendregt, The Lambda Calculus: Its Syntax and Semantics, revised ed., Studies in Logic 103, North-Holland, 1984. — <https://philpapers.org/rec/BARTLC>
- _advanced_ · Alonzo Church, "A Formulation of the Simple Theory of Types," Journal of Symbolic Logic 5(2):56-68, 1940. — <https://www.jstor.org/stable/2266170>
- _advanced_ · AlphaProof team (T. Hubert, H. Mehta et al.), "Olympiad-level formal mathematical reasoning with reinforcement learning," Nature, 12 Nov 2025, doi:10.1038/s41586-025-09833-y. — <https://www.nature.com/articles/s41586-025-09833-y>
- _advanced_ · T. H. Trinh, Y. Wu, Q. V. Le, H. He, T. Luong, "Solving olympiad geometry without human demonstrations" (AlphaGeometry), Nature 625:476-482, 2024. — <https://doi.org/10.1038/s41586-023-06747-5>
- _advanced_ · DeepSeek-AI, "DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via RL for Subgoal Decomposition," arXiv:2504.21801 (Apr 2025) — 88.9% miniF2F, 49/658 PutnamBench. — <https://arxiv.org/abs/2504.21801>
- _advanced_ · Goedel-Prover team, "Goedel-Prover-V2: Scaling Formal Theorem Proving with Scaffolded Data Synthesis and Self-Correction," arXiv:2508.03613 (Aug 2025) — 88.1%/90.4% miniF2F, 86 PutnamBench. — <https://arxiv.org/abs/2508.03613>
- _advanced_ · K. Yang et al., "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models," NeurIPS 2023, arXiv:2306.15626. — <https://arxiv.org/abs/2306.15626>
- _advanced_ · K. Zheng, J. M. Han, S. Polu, "miniF2F: a cross-system benchmark for formal Olympiad-level mathematics," ICLR 2022, arXiv:2109.00110. — <https://arxiv.org/abs/2109.00110>
- _advanced_ · G. Tsoukalas et al., "PutnamBench: A Multilingual Competition-Mathematics Benchmark for Formal Theorem-Proving," NeurIPS 2024, arXiv:2407.11214; leaderboard trishullab.github.io/PutnamBench. — <https://github.com/trishullab/PutnamBench>
- _advanced_ · E. Glazer et al. (Epoch AI), "FrontierMath: A Benchmark for Evaluating Advanced Mathematical Reasoning in AI," arXiv:2411.04872 (Nov 2024) — research-level; o3 ~25%. — <https://epoch.ai/frontiermath>
- _advanced_ · T. Tao et al., "The Equational Theories Project: Advancing Collaborative Mathematical Research at Scale," arXiv:2512.07087 (2025); project teorth.github.io/equational_theories. — <https://terrytao.wordpress.com/2025/12/09/the-equational-theories-project-advancing-collaborative-mathematical-research-at-scale/>
- _advanced_ · A. Odrzywolek, "All elementary functions from a single binary operator," arXiv:2603.21852 (2026) — the EML case-study paper. — <https://arxiv.org/abs/2603.21852>

## Cross-language artifact plan

- **Lean 4** (L1): theorem id_proof {P : Prop} : P -> P := fun p => p; and theorem s_comb {P Q R : Prop} : (P -> Q -> R) -> (P -> Q) -> P -> R := fun f g p => f p (g p) -- the K/S combinators are exactly their Hilbert axioms; confirm with lambda-lab `ch verify`.
- **Agda** (L1): id : {A : Set} -> A -> A ; id x = x -- plus data Bottom : Set (no constructors) and bottom-elim : {A : Set} -> Bottom -> A ; bottom-elim () -- Agda as literal MLTT, the empty type = False.
- **Mizar** (L1): for X being set holds X = X -- proved inside an environ importing TARSKI: classical first-order logic over Tarski-Grothendieck set theory, no Curry-Howard proof term; the course's one non-type-theoretic foundation.
- **Lean 4** (L2): Typed Church numerals: def CNat := (a : Type) -> (a -> a) -> a -> a ; czero, csucc, cplus, cmult; prove cplus ctwo cthree = cfive by rfl and toNat (fromNat n) = n by induction -- the encoding computes and is faithful.
- **Agda** (L2): iterate : {A : Set} -> (A -> A) -> Nat -> A -> A ; prove iterate f (m + n) x == iterate f m (iterate f n x) by induction -- the semantic content of Church PLUS (why the encodings are correct, not just checked on small cases).
- **Rocq (Rocq/Coq)** (L2): Define SKI combinators and combinatory reduction; prove S K K x = x (SKK behaves as identity) by simpl/reflexivity -- combinatory completeness, a name-free counterpart to lambda-abstraction.
- **Lean 4** (L3): example {P Q : Prop} : P /\ Q -> Q /\ P := fun (p, q) => (q, p); example {P : Prop} : P -> not (not P) := fun p f => f p; example {P : Prop} : not (not (not P)) -> not P := fun h p => h (fun f => f p) -- all constructive, whereas ((P->Q)->P)->P needs by_contra.
- **Agda** (L3): Define _uplus_ (sum), Bottom (empty), and not A = A -> Bottom; prove uplus-comm : A uplus B -> B uplus A and dni : A -> not (not A) constructively, and show not (not A) -> A only via postulate -- the classical axiom made explicit.
- **Rocq (Rocq/Coq)** (L3): Lemma or_comm : forall P Q : Prop, P \/ Q -> Q \/ P (intros; destruct; left/right); then Lemma peirce needs Require Import Classical and destruct (classic P) -- the same constructive/classical split in a default-constructive assistant.
- **Lean 4** (L4): On inductive MyNat, define add by recursion on the second argument and prove zero_add, succ_add, add_comm by induction + rw (reproduces NNG4 Addition World; add_comm is that world's L3 'level boss', not its final level).
- **Agda** (L4): +-comm : (m n : Nat) -> m + n == n + m, proved by induction -- the Lean add_comm rendered in a second type theory, a clean Curry-Howard mirror.
- **Rocq (Rocq/Coq)** (L4): Theorem add_comm : forall n m : nat, n + m = m + n, by induction n + simpl/rewrite/lia -- contrasts tactic vocabularies (lia ~ omega, reflexivity ~ rfl).
- **Lean 4** (L5): Tactic-and-typeclass drill: prove (a*x+b*y)^2 <= (a^2+b^2)*(x^2+y^2) by nlinarith [sq_nonneg (a*y - b*x)]; build class MyAddMonoid with a Nat instance and prove a lemma from the interface only; define well-founded mygcd with termination_by/decreasing_by and prove mygcd_dvd_left.
- **Agda** (L5): data Vec (A : Set) : Nat -> Set with _++_ : Vec A m -> Vec A n -> Vec A (m + n); optionally prove length (xs ++ ys) == length xs + length ys by definitional computation -- dependent types made visible (the phenomenon Lean's Pi-types encode).
- **Lean 4** (L6): inductive EMLTerm | one | var (n : Nat) | eml (a b : EMLTerm); EMLTerm.eval? : (Nat -> Real) -> EMLTerm -> Option Real with guard 'if 0 < vb then some (Real.exp va - Real.log vb) else none'; prove exists t, forall env, EMLTerm.eval? env t = some (Real.exp 1), witnessed by eml one one (e = eml(1,1)).
- **Rocq (Rocq/Coq)** (L6): Definition nand p q := negb (p && q); prove forall p, negb p = nand p p, forall p q, andb p q = nand (nand p q) (nand p q), and forall p q, orb p q = nand (nand p p) (nand q q) -- the Boolean analogue of EML's functional completeness.
- **Mizar** (L6): Functional completeness of the Sheffer stroke: derive not, and, or from a single NAND connective in Mizar's declarative propositional apparatus -- the same completeness idea as EML in a classical, set-theoretic prover.

## Open questions

- EML artifact provenance: the repo pins (Lean 4.28.0 + Mathlib v4.28), the 8062-lake-job count, the 0-sorry/#print-axioms audit, and the '100 public theorems / 36 primitives' figures are course-internal claims flagged as not independently verifiable by fact-check. Confirm each against the live repository before putting numbers on slides, and decide whether to keep the 4.28 pin (reproducibility) or bump to 4.32.
- FrontierMath number to quote: use ~25% (OpenAI o3), NOT ~30%; and decide whether to add the caveat that Epoch AI disclosed OpenAI funding and pre-evaluation access to most problems/solutions.
- NNG4 demo script: add_comm is the Addition World L3 'level boss', followed by add_assoc (L4) and add_right_comm (L5); adjust any slide that calls add_comm the 'culmination' of the world.
- Kleene predecessor attribution: present the specific PRED lambda-term as the lambda_lab repo's construction (and verify its reduction live), attributing only the 'wisdom-teeth' anecdote to Selinger arXiv:0804.3434, which poses PRED as an unsolved exercise and gives no term.
- Live multi-prover coverage: Agda/Rocq/Mizar artifacts are pedagogically valuable but carry install friction (especially Mizar). Decide per artifact whether to run live or present as read-only contrast, and whether lambda_lab ships saved traces for offline play.
- Benchmark volatility: PutnamBench/miniF2F/FrontierMath numbers move monthly (e.g. Aleph-Prover reportedly ~668/672 PutnamBench Jan 2026). Freeze a 'facts current as of July 2026' date on the slides and cite primary sources for every figure.
- Rocq version for any live demo: use 9.2.0 (2026-03-27); Rocq 9.3 had only branched (2026-07-08) and was not released, so do not assume it is available.
- Mathlib scale figures: quote 283,067 theorems / 134,678 definitions / 772 contributors / >2M lines from the live leanprover-community stats page (the 351k-declaration and 230k/115k figures were refuted); note that live counts drift, so date the citation.
- Time budget: L5 and L6 are the densest sessions. Decide whether to trim the tactic zoo (L5) or the landscape survey (L6), or to push some artifacts to homework, to protect the live-coding and epistemics segments.
- Faithfulness emphasis: how strongly to foreground the 'kernel checks proof-against-statement, not statement-against-intent' caveat as the course's central intellectual payload versus the mechanics of proving -- and whether to run a dedicated 'three candidate statements, one faithful' exercise in L6.

