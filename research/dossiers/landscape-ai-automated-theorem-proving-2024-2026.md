# Landscape: AI + automated theorem proving (2024–2026)

> A current-as-of-July-2026 map of the AI-for-formal-mathematics landscape — DeepMind's AlphaProof/AlphaGeometry, the open-weight prover race (DeepSeek, Goedel, Seed, Aleph), the Lean/Mathlib infrastructure, the benchmark ladder (miniF2F → PutnamBench → ProofNet → FrontierMath), and the collaboration wave (Equational Theories Project, Tao's PFR) — with the concrete numbers, dates and URLs Lecture 6 and the "why now" landing page need.

## Learning objectives

- Distinguish the two paradigms that both peaked in 2024–2025: neuro-symbolic/formal provers that emit Lean or Coq the kernel checks (AlphaProof, DeepSeek-Prover, Seed-Prover) versus natural-language reasoners that write prose proofs (Gemini Deep Think, OpenAI at IMO 2025) — and explain why the first gives a soundness guarantee the second does not.
- State precisely what AlphaProof achieved at IMO 2024: 28/42 (silver, one point short of gold), 4 of 6 problems, AlphaProof solving 3 of the 5 non-geometry problems in Lean and AlphaGeometry 2 the geometry problem — and that it took minutes to days of test-time search per problem.
- Read a theorem-prover benchmark result correctly: know that miniF2F pass rates near 90–99%+ mean the benchmark is nearly saturated, that PutnamBench (672 Lean problems) went from ~10 solved to 668/672 in two years, and that FrontierMath sits at the opposite extreme (research-level, <2% at launch).
- Explain the moving-target nature of the substrate: current Lean toolchain (4.32.0, July 2026) and Mathlib size (283,067 theorems, 134,678 definitions, ~2M+ lines), and why a formalization pins an exact toolchain (the author's own EML repo is pinned to Lean/Mathlib 4.28).
- Describe autoformalization as two distinct tasks — statement autoformalization and proof autoformalization — and why a well-typed formal statement can still be an unfaithful translation of the informal claim (the key correctness risk in the whole pipeline).
- Situate the collaboration story: how the Equational Theories Project resolved all 22,028,942 implications among 4,694 magma laws with Lean-verified proofs, and how Tao's PFR formalization (3 weeks, Blueprint-driven) modeled distributed human+AI formal mathematics.

## Prerequisites

- Comfort with the idea of a formal proof as a checkable object (the course's Curry–Howard / lambda-calculus thread — proofs are programs, types are propositions)
- First contact with a proof assistant: what a tactic state, a goal, and the trusted kernel are (the book's Lean 4 chapter / Natural Number Game)
- Basic ML literacy: what a language model is, what reinforcement learning and pass@k mean — enough to read a benchmark table without over-reading it
- Awareness of the difference between a numeric-answer benchmark and a proof benchmark

## AlphaProof (Google DeepMind) — RL theorem proving in Lean

The headline system for the 'why now' section. An AlphaZero-style agent: a pretrained language model proposes Lean 4 tactic/proof candidates, wrapped in a reinforcement-learning loop grounded by the Lean kernel (the kernel is the ground-truth reward — a proof either checks or it does not). Bootstrapped by autoformalizing on the order of a million informal competition problems into Lean with a Gemini-based formalizer, then self-improving. Crucial mechanism for hard problems: TEST-TIME RL — at inference it generates and trains on millions of variants of the specific target problem. At IMO 2024 the combined system scored 28/42 (silver medal, one point below the 29-point gold cutoff); AlphaProof solved 3 of the 5 non-geometry problems including P6, the hardest (only a handful of humans solved it), taking from minutes up to ~3 days of compute per problem. Peer-reviewed in Nature on 12 Nov 2025. Not open-weight — contrast with DeepSeek/Goedel. Follow-up: a separate DeepMind system (Gemini Deep Think) reached genuine gold at IMO 2025 in NATURAL language, a paradigm contrast worth flagging.

**Key definitions**

- Test-time reinforcement learning: generating and learning from many auto-generated variants of the single target problem at inference time
- Neuro-symbolic loop: LLM proposal + formal-kernel verification as reward
- Autoformalization bootstrap: translating ~1M informal problems into Lean to create training signal

**Key results**

- IMO 2024: 28/42, silver, one point short of gold; 4/6 problems solved (AlphaProof 3 non-geometry incl. hardest P6, AlphaGeometry 2 the geometry P4)
- Every emitted proof is Lean-kernel-checked, so the soundness guarantee is absolute conditional on Lean's small trusted core
- Published Nature 636/641 series, 12 Nov 2025, doi:10.1038/s41586-025-09833-y

## AlphaGeometry 1 & 2 — neuro-symbolic olympiad geometry

The purest illustration of neuro-symbolic ATP for a lecture. AlphaGeometry 1 (Trinh, Luong et al., Nature 625:476–482, Jan 2024): a language model proposes AUXILIARY CONSTRUCTIONS (the creative 'draw this extra line' step) while a fast symbolic deduction engine (deductive database + algebraic reasoning, DD+AR) closes the logical gaps; trained on ~100 million synthetically generated theorems with NO human proof demonstrations. It solved 25 of 30 recent olympiad geometry problems, approaching the average human gold medalist. AlphaGeometry 2 (Chervonyi et al., arXiv:2502.03544, Feb 2025): Gemini-based language model, a broadened domain-specific language (now handles object motion and linear equations of angles/ratios/distances — coverage of the formalization language rose from 66% to 88% of 2000–2024 IMO geometry), and a faster symbolic engine (DDAR2). Solve rate over the last 25 years of IMO geometry jumped from 54% to 84%, surpassing the average gold medalist; it cracked IMO 2024 P4 in 19 seconds once formalized. This is the 'geometry' component of the 28/42 IMO 2024 result.

**Key definitions**

- Auxiliary construction: an added point/line/circle not in the problem statement, the step requiring 'insight'
- DD+AR / DDAR2: symbolic deduction database plus algebraic reasoning that exhaustively derives consequences
- Synthetic theorem generation: sampling random geometric premises and running the deduction engine backward to manufacture training data

**Key results**

- AG1: 25/30 recent olympiad geometry problems, near gold-medalist average, zero human demonstrations, Nature 2024
- AG2: 84% solve rate on 2000–2024 IMO geometry (up from 54%), formalization coverage 66%→88%
- IMO 2024 P4 solved in 19 seconds; component of the silver-medal combined system

## DeepSeek-Prover (V1 / V1.5 / V2) — open-weight Lean provers

The open-weight answer to AlphaProof and the reference point for the whole open community. V1 (arXiv:2405.14333, May 2024): large-scale synthetic proof data (~8M statements) via expert iteration. V1.5 (arXiv:2408.08152, Aug 2024): adds RL from proof-assistant feedback plus Monte-Carlo tree search (RMaxTS), reaching 63.5% on miniF2F-test. V2 (arXiv:2504.21801, released 30 Apr 2025) is the current flagship: a 671B-parameter Mixture-of-Experts model built on the DeepSeek-V3 base (also a 7B variant), trained with RL for SUBGOAL DECOMPOSITION — a chain-of-thought reasoner breaks a theorem into subgoals, a prover discharges each, and the results are recomposed and RL-refined. It reaches 88.9% on miniF2F-test (pass@8192) and solves 49/658 PutnamBench problems. Open weights on Hugging Face under MIT — a fully open alternative to AlphaProof, and the model most likely to be reproducible in a classroom. Superseded on the leaderboards within months by Goedel-Prover-V2 and Seed-Prover, illustrating the pace.

**Key definitions**

- Mixture-of-Experts (MoE): only a subset of parameters (here ~37B of 671B) activates per token
- Subgoal decomposition: recursively splitting a goal into lemmas proved separately then recombined
- Expert iteration: alternately generating proofs with the model and retraining on the successful ones

**Key results**

- V1.5: 63.5% miniF2F-test with RL+MCTS (RMaxTS)
- V2: 88.9% miniF2F-test (pass@8192); 49/658 PutnamBench; 671B MoE, open weights (MIT)
- Context window up to 163,840 tokens for full-length theorems

## Goedel-Prover (V1 / V2) — open-source SOTA prover

Shows that small open models overtook the 671B behemoth within a year. Goedel-Prover V1 (arXiv:2502.07640, Feb 2025): supervised fine-tuning only on 1.64M auto-formalized Lean 4 statements from NuminaMath, reaching 57.6% miniF2F pass@32 (then SOTA open-source) with just 7 PutnamBench problems. Goedel-Prover-V2 (arXiv:2508.03613, Aug 2025): a 32B model using SCAFFOLDED DATA SYNTHESIS (curriculum of progressively harder synthetic problems), VERIFIER-GUIDED SELF-CORRECTION (the model reads Lean's error and revises), and model averaging. It hits 88.0% miniF2F pass@32 (90.4% in self-correction mode) and solves 86 PutnamBench problems at pass@184 — beating DeepSeek-Prover-V2-671B's 47/49 with a model ~20x smaller. Its 8B variant matches the 671B DeepSeek-V2 (84.6% miniF2F) at ~100x smaller. The efficiency-frontier story for the lecture.

**Key definitions**

- Scaffolded data synthesis: generating a difficulty-graded curriculum of training problems
- Verifier-guided self-correction: feeding the Lean compiler error back to the model for a revised attempt
- pass@k: probability of a correct proof within k independent sampled attempts

**Key results**

- V2-32B: 88.0% miniF2F pass@32; 90.4% with self-correction; 86 PutnamBench @ pass@184
- V2-8B matches DeepSeek-Prover-V2-671B on miniF2F at ~100x smaller
- Strongest open-source prover at its Aug 2025 release, open weights on Hugging Face

## Seed-Prover & Aleph-Prover — the 2025–26 frontier

The systems that pushed formal ATP to near-saturation and to gold-level IMO in Lean. Seed-Prover (ByteDance, arXiv:2507.23726, July 2025): a lemma-style WHOLE-PROOF model on Lean that iteratively refines using Lean feedback, previously proved lemmas, and self-summarization, with 'deep' and 'broad' test-time strategies; paired with a Seed-Geometry engine. It SATURATES miniF2F, proves 78.1% of past formalized IMO problems, and formally proved 5 of 6 IMO 2025 problems (gold-level) in Lean — the formal counterpart to Gemini's natural-language gold. Seed-Prover 1.5 (arXiv:2512.17260, Dec 2025) adds agentic RL and solves 581/672 PutnamBench. Aleph-Prover (Logical Intelligence, Jan 2026) tops the PutnamBench Lean leaderboard at 668/672 (~99.4%), essentially solving the benchmark. Also worth a name-check: Kimina-Prover (Numina/Moonshot) and Harmonic's Aristotle (which the author's own repo uses for proof search). Together these mark 2026 as the year competition-level formal proving became a solved-ish problem, redirecting attention to research-level mathematics.

**Key definitions**

- Whole-proof (vs step/tactic) generation: emit the entire proof term then check, rather than one tactic at a time
- Lemma-style reasoning: conjecture and prove reusable intermediate lemmas, refining against Lean feedback
- Benchmark saturation: solve rate approaching 100%, so the benchmark no longer discriminates systems

**Key results**

- Seed-Prover: saturates miniF2F; 5/6 IMO 2025 problems proved formally in Lean (gold-level)
- Aleph-Prover: 668/672 PutnamBench Lean (~99.4%), leaderboard leader Jan 2026
- Seed-Prover 1.5: 581/672 PutnamBench with a fixed compute budget

## LeanDojo + ReProver — retrieval-augmented proving and the open toolchain

The academic open-source foundation most usable for teaching, and the origin of premise-retrieval as a technique. LeanDojo (Yang et al., NeurIPS 2023 Datasets & Benchmarks, arXiv:2306.15626, Caltech/NVIDIA/MIT): (1) a toolkit that turns Lean into an interactive Gym-like environment a program can drive to enter tactic states and receive feedback; (2) a benchmark of 98,734 theorems/proofs extracted from Mathlib with a deliberately hard split that forces generalization to NOVEL PREMISES never seen in training. ReProver is the first RETRIEVAL-AUGMENTED LLM prover: a dense retriever selects relevant Mathlib lemmas (premise selection) to condition an encoder-decoder tactic generator, addressing the fact that a proof usually needs a handful of the >280k available lemmas. Trainable on a single GPU-week and released under MIT with no proprietary data — the reproducibility baseline the whole field cites, and a natural hands-on target for students.

**Key definitions**

- Premise selection: choosing which of the library's lemmas are relevant to the current goal
- Retrieval-augmented generation for proofs: retrieve lemmas, then generate the tactic conditioned on them
- Interactive proving environment: programmatic access to Lean tactic states and error feedback (the 'Dojo')

**Key results**

- Benchmark: 98,734 Mathlib theorem/proof pairs with a novel-premise generalization split
- ReProver: first retrieval-augmented LLM prover; trainable in ~1 GPU-week; MIT-licensed, fully open
- Established premise retrieval as a core component now used across the field

## Lean FRO & the Lean 4 toolchain — the substrate

Why the infrastructure is a story in itself. Lean 4 is the dependently-typed proof assistant + programming language (Leonardo de Moura, later Sebastian Ullrich) underpinning AlphaProof, DeepSeek/Goedel/Seed provers, PutnamBench, ProofNet and the Equational Theories Project. The Lean FRO (Focused Research Organization, launched July 2023 under Convergent Research) is a nonprofit with a 5-year mission (through 2028) charged with scalability, usability and proof automation. Funders include the Alfred P. Sloan Foundation, Simons Foundation International, the Richard Merkin Foundation, Convergent Research, and Alex Gerko (XTX Markets) — with a fresh $10M from Gerko announced July 2025. Its Year-3 roadmap (Aug 2025–July 2026) drives Std toward a verified 1.0 (containers, async I/O, an HTTP server), launched the Mathlib Initiative (Sept 2025) and CSLib, a computer-science library (Aug 2025). The toolchain moves fast: latest stable is Lean 4.32.0 (13 July 2026), with 4.33.0-rc1 already out (15 July 2026) — a monthly cadence. Teaching point: a formalization must pin an exact toolchain (the author's EML repo is pinned to Lean/Mathlib 4.28).

**Key definitions**

- Focused Research Organization (FRO): a time-boxed nonprofit built to deliver scientific infrastructure a lab or company would not
- elan/lake: Lean's toolchain manager and build system; a project pins one toolchain version
- Std / Batteries: the standard library layer beneath Mathlib

**Key results**

- Latest stable Lean 4.32.0 (2026-07-13); 4.33.0-rc1 (2026-07-15) — ~monthly releases
- Lean FRO funded by Sloan, Simons Intl, Merkin, Convergent Research, Alex Gerko; +$10M from Gerko (July 2025)
- Year-3 roadmap 2025–26: Std 1.0 push, Mathlib Initiative (Sept 2025), CSLib (Aug 2025)

## Mathlib — the unified formal mathematics library

The single largest coherent body of machine-checked mathematics and the shared dependency of nearly every system above. One monolithic, continuously integrated Lean 4 library covering undergraduate through research mathematics (analysis, algebra, topology, measure theory, category theory, number theory). Current size (leanprover-community mathlib_stats, July 2026): 283,067 theorems, 134,678 definitions, 772 contributors, well over 2 million lines. It is both the training corpus (LeanDojo, DeepSeek, Goedel all mine it) and the ambient library a prover must search for premises. Growth is gated by human PR review — a standing backlog of ~300 PRs with roughly two-week median waits, which the new Mathlib Initiative (Lean FRO, Sept 2025) exists to relieve. Concrete continuity hook: the author's own EML formalization builds against Mathlib v4.28 and finishes 8,062 lake jobs sorry-free — a tangible sense of scale.

**Key definitions**

- Monorepo library: one versioned repository all downstream projects depend on and bump together
- Definitional unfolding / instance resolution: why a huge type-class hierarchy makes search hard
- sorry: Lean's placeholder that admits a goal without proof — a 'sorry-free' build has none

**Key results**

- 283,067 theorems, 134,678 definitions, 772 contributors, ~2M+ lines (mathlib_stats, July 2026)
- Growth throttle: ~300-PR review backlog, ~2-week median wait; Mathlib Initiative launched to address it
- Author's EML repo: Mathlib v4.28, 8,062 lake jobs, zero sorry — a worked example of library-scale proof

## miniF2F — the entry-level olympiad benchmark

The benchmark whose saturation defines the current moment. miniF2F (Zheng, Han, Polu, ICLR 2022, arXiv:2109.00110): 488 formal statements (244 test + 244 validation) drawn from IMO/AIME/AMC and the MATH dataset, spanning algebra, number theory, inequalities and basic calculus. Its defining feature is CROSS-SYSTEM formalization — the same problems exist in Lean, Isabelle, Metamath and (partially) HOL Light — enabling apples-to-apples prover comparison. The trajectory is the lesson: GPT-f baselines were ~25–30%; by 2024 DeepSeek-Prover-V1.5 reached 63.5%; by 2025 DeepSeek-V2 88.9%, Goedel-V2 90.4%, and Seed-Prover 'saturates' it. Because it is now nearly solved (and has known formalization/label errors that spurred cleaned re-releases), miniF2F has largely served its purpose and attention has shifted up the ladder to PutnamBench and FrontierMath.

**Key definitions**

- Cross-system benchmark: identical problems formalized in multiple proof assistants
- Validation vs test split: 244 problems each, to tune and then report honestly
- Label/formalization error: a formal statement that does not faithfully capture the informal problem

**Key results**

- 488 problems (244 test/244 valid); Lean, Isabelle, Metamath, HOL Light
- Pass rates climbed ~25% (2021) → 63.5% (2024) → ~90%+ / saturated (2025)
- Now effectively saturated; superseded as the discriminating benchmark

## PutnamBench — the next rung

The benchmark that measures the current frontier of competition-level formal proving. PutnamBench (Tsoukalas et al., NeurIPS 2024, arXiv:2407.11214): formalizations of William Lowell Putnam problems (1962–2024), MULTILINGUAL across Lean 4, Isabelle, and Coq/Rocq — as of Jan 2026, 672 problems in Lean, 640 in Isabelle, 412 in Coq. Putnam problems are undergraduate but genuinely hard, so it was far from saturated at launch: the first neural provers solved only single digits (Goedel-Prover V1 solved 7). The two-year climb is dramatic — DeepSeek-Prover-V2 49, Goedel-Prover-V2 86, Seed-Prover 1.5 581, and Aleph-Prover 668/672 (~99.4%) topping the Jan 2026 leaderboard. Watching this benchmark go from ~1% to ~99% in about eighteen months is the single most vivid 'why now' data point for the landing page, and its three-language design maps directly onto the course's proof-assistant coverage.

**Key definitions**

- Multilingual benchmark: the same problems maintained in Lean, Isabelle and Coq/Rocq
- Compute-budgeted leaderboard: entries report a dollar/GPU budget per problem, not just pass@k
- Undergraduate-competition difficulty: harder than miniF2F, easier than research-level

**Key results**

- 672 Lean / 640 Isabelle / 412 Coq problems (Putnam 1962–2024)
- Jan 2026 leaderboard: Aleph-Prover 668/672 (~99.4%), Seed-Prover 1.5 581, Goedel-V2 86, DeepSeek-V2 49
- Went from ~7 solved (early 2025) to near-complete in ~18 months

## FrontierMath — the research-level ceiling

The counterweight that keeps hype honest. FrontierMath (Glazer et al., Epoch AI, arXiv:2411.04872, first published 8 Nov 2024): hundreds of ORIGINAL, UNPUBLISHED, research-level problems with automatically verifiable numeric/symbolic answers (so it resists data contamination), authored and vetted by 60+ mathematicians including Fields medalists Tao, Gowers and Borcherds; a typical problem takes a specialist hours, the hardest days. A Tier 4 expansion (~50 problems, June 2025) sits far above the rest. At launch every frontier model scored under 2%. Note this is an ANSWER benchmark (final-answer, natural-language reasoning), NOT a formal-proof benchmark — a different measurement axis from miniF2F/PutnamBench. Two 2026 caveats to teach source-criticism: an AI-assisted audit (finalized ~June 2026) found errors in ~42% of problems, yielding a corrected 338-problem set (295 Tiers 1–3 + 43 Tier 4); and reported SOTA varies wildly by source and dataset version, so cite Epoch's own figures. The takeaway: even as competition math saturates, research-level math remains largely out of reach.

**Key definitions**

- Answer (auto-verifiable) benchmark vs proof benchmark: checks a final value, not a machine-checked proof
- Data contamination: leakage of test problems into training data, which unpublished problems mitigate
- Tiered difficulty: Tiers 1–3 (base) plus an exceptionally hard Tier 4 expansion

**Key results**

- Research-level, unpublished; <2% solved by any model at Nov 2024 launch
- Co-designed by 60+ mathematicians incl. Fields medalists Tao, Gowers, Borcherds
- June 2026 correction: ~42% of problems had errors; corrected set = 338 problems (295 T1–3 + 43 T4)

## ProofNet — the autoformalization benchmark

The bridge topic between informal and formal, and the natural entry point for the autoformalization discussion. ProofNet (Azerbayev et al., arXiv:2302.12433, 2023): 371 undergraduate pure-mathematics problems (from standard texts — Rudin, Dummit & Foote, Herstein, etc.) spanning real/complex analysis, linear algebra, abstract algebra and topology. Each item is a TRIPLE: a natural-language statement, a natural-language proof, and a formal Lean statement (originally Lean 3; since ported to Lean 4). This supports two distinct tasks — STATEMENT autoformalization (NL → Lean statement) and full formal proving — making it the canonical testbed for translating human mathematics into Lean. Baselines were low (GPT-4-era in-context autoformalization typechecked only a modest fraction and faithfulness was worse); modern fine-tuned formalizers do far better but faithfulness (semantic correctness, not just typechecking) remains the hard part. It also introduced influential techniques: prompt retrieval and distilled backtranslation.

**Key definitions**

- Statement autoformalization: translating a natural-language theorem into a well-typed formal statement
- Distilled backtranslation: training a formalizer by round-tripping formal↔informal to generate data
- Faithfulness vs typecorrectness: a statement can compile yet mean something other than the original

**Key results**

- 371 undergraduate problems as (NL statement, NL proof, Lean statement) triples
- Canonical benchmark for statement autoformalization; drawn from standard textbooks
- Introduced prompt-retrieval and distilled-backtranslation autoformalization methods

## Autoformalization (statement + proof) — the pipeline's weak link and frontier

The conceptual glue linking every system above and the place where errors actually enter. Autoformalization = automatically translating informal mathematics into a formal language; it splits into STATEMENT autoformalization (get the theorem statement right) and PROOF autoformalization (get a machine-checkable proof). It is load-bearing everywhere: AlphaProof autoformalized ~1M problems to bootstrap training; Goedel-Prover formalized 1.64M NuminaMath statements; every prover depends on faithful statements. The central risk — a formal statement can typecheck yet be an UNFAITHFUL rendering of the informal claim, so a 'proof' proves the wrong thing (a subtle bug the Lean kernel cannot catch, because the kernel only checks the proof against the stated goal). This motivates the 2024–26 wave of evaluation work: 'Reliable Evaluation and Benchmarks for Statement Autoformalization' (arXiv:2406.07222), Process-Driven Autoformalization using Lean compiler feedback (arXiv:2406.01940), and newer benchmarks (RLM25, FORML4, IndiMathBench, CAM-Bench, MSC-180). For the course this is where students should feel the tension between 'the kernel guarantees correctness' and '…correctness of what exactly?'

**Key definitions**

- Statement autoformalization vs proof autoformalization: translating the claim vs producing the checked proof
- Faithfulness / adequacy: the formal statement provably captures the intended informal meaning
- Process-driven autoformalization: iteratively using proof-assistant compiler feedback to repair a translation

**Key results**

- Underpins AlphaProof (~1M problems) and Goedel-Prover (1.64M statements) training pipelines
- Statement autoformalization on ProofNet-style tasks now exceeds ~50% with agentic/fine-tuned systems, but faithfulness lags typechecking
- The unfaithful-but-well-typed statement is the pipeline's core, kernel-invisible failure mode

## Equational Theories Project — mass collaboration, Lean-verified

The template for AI-era collaborative mathematics and a perfect lecture case study. Launched by Terence Tao on 25 Sept 2024, the ETP set out to resolve every implication between the 4,694 simplest equational laws on MAGMAS (a set with one binary operation, no axioms) using at most four applications of the operation. That means deciding, for all 4,694 × 4,694 = 22,028,942 ordered pairs, whether law A implies law B — proving each implication or exhibiting a finite counterexample magma. The work combined human insight, automated theorem provers (Vampire and friends) and SAT/finite-model search, with EVERY result formally verified in Lean, orchestrated over GitHub/Zulip by dozens of contributors (the write-up lists ~34 authors). It finished its main phase by early 2025; the retrospective 'Advancing Collaborative Mathematical Research at Scale' appeared on Tao's blog (9 Dec 2025). The explicit historical echo is McCune's EQP settling the Robbins conjecture (that Robbins algebras are Boolean) in 1996 — automated proof of a genuine open problem — now scaled to 22 million interlocking questions with a formal-verification backbone.

**Key definitions**

- Magma: a set with a single closed binary operation and no further axioms
- Equational law / implication graph: laws as nodes, 'law A entails law B' as directed edges
- Finite counterexample model: a small magma satisfying A but violating B, refuting the implication

**Key results**

- All 22,028,942 implications among 4,694 magma laws resolved, every proof Lean-verified
- Human + ATP (Vampire) + SAT/model-search, coordinated via GitHub/Zulip, ~34 authors
- Modern-scale analogue of McCune's EQP/Robbins-conjecture result (1996)

## Terence Tao's public formalization work — PFR and AI evangelism

The most credible human champion of this shift, useful for the 'why should a working mathematician care' framing. Two concrete threads. (1) The Polynomial Freiman–Ruzsa (PFR) formalization (teorth/pfr, Nov–Dec 2023, with Yaël Dillies, Bhavik Mehta and community): starting from Tao et al.'s new proof, a distributed team formalized PFR — 'if A ⊆ F_2^n with |A+A| ≤ K|A| then A is covered by ≤ 2K^12 cosets of a subspace' — in Lean 4 in about THREE WEEKS, using Patrick Massot's BLUEPRINT tool to split the proof into a human-readable dependency graph of Lean-linked sublemmas; later stages tightened the exponent (12 → 11 → 9) and generalized to bounded-torsion groups. This is the reference model for organizing a large formalization. (2) Public AI-for-math advocacy: co-designing FrontierMath, launching the ETP, testing AlphaProof ('Mathematicians put AI model AlphaProof to the test', Nature news d41586-025-03585-5, Nov 2025), and profiles like Quanta's 'How Terry Tao Became an Evangelist for AI in Math' (June 2026). For the course, PFR + Blueprint is the concrete 'how a real research proof gets formalized' artifact.

**Key definitions**

- Blueprint (Massot): a tool decomposing a proof into a navigable graph of statements each linked to its Lean formalization
- Polynomial Freiman–Ruzsa conjecture: an additive-combinatorics structure theorem for sets of small doubling
- Distributed formalization: many contributors claiming and closing blueprint nodes in parallel

**Key results**

- PFR formalized in Lean 4 in ~3 weeks (late 2023); exponent later improved 12→11→9
- Blueprint-driven workflow now standard for large community formalizations
- Tao co-designed FrontierMath, launched the ETP, and publicly stress-tested AlphaProof (Nature, Nov 2025)

## IMO 2025 — the natural-language gold and the paradigm split

Essential context so the 'why now' section is not a year out of date. In July 2025 two systems reached genuine GOLD at IMO 2025 — Google DeepMind's Gemini Deep Think (officially graded) and an experimental OpenAI model — each scoring 35/42 by solving 5 of 6 problems (all but P6) under contest conditions (two 4.5-hour sessions, no tools). Crucially they wrote NATURAL-LANGUAGE proofs, not formal Lean — a paradigm shift from AlphaProof's 2024 formal, kernel-checked silver. Simultaneously, ByteDance's Seed-Prover proved 5/6 of the same IMO 2025 problems FORMALLY in Lean. This three-way snapshot (natural-language gold, formal gold-level, formal verification available) is the sharpest possible framing of the course's central question: prose proofs are more flexible and human-legible but carry no soundness guarantee; formal proofs are kernel-certified but costlier — and 2025–26 is exactly when both crossed the olympiad threshold. The tension between the two is the pedagogical payload.

**Key definitions**

- Natural-language reasoning proof: a prose argument graded by humans, with no machine verification
- Formal (kernel-checked) proof: a Lean/Coq proof term mechanically certified against its statement
- Contest conditions: fixed time, no external tools — matching human competitors

**Key results**

- Gemini Deep Think and an OpenAI model each scored 35/42 (gold, 5/6) at IMO 2025 in natural language
- Seed-Prover proved 5/6 of IMO 2025 formally in Lean
- Marks the coexistence of the natural-language and formal paradigms at gold level — the course's framing device

## Pedagogical arc
Open Lecture 6 with the single most vivid fact — competition mathematics went from AI solving essentially nothing to olympiad gold in about two years — and immediately split the room into the two paradigms that both crossed the line: kernel-checked FORMAL proofs (AlphaProof, Seed-Prover, the open provers) versus prose NATURAL-LANGUAGE proofs (Gemini Deep Think, OpenAI at IMO 2025). This restates the course's Curry–Howard thesis ('proofs are objects a machine can check') as a live 2026 research question. Then descend the stack. First the flagship story: AlphaProof and AlphaGeometry as the neuro-symbolic template (LM proposes, kernel/symbolic-engine disposes), with the exact IMO 2024 silver claim. Next, democratization: the open-weight prover race (DeepSeek → Goedel → Seed → Aleph), where students can see numbers move month by month and a 32B model beat a 671B one — proof that this is a fast, participatory field, not a two-lab monopoly. Then reveal the substrate that makes it all real and checkable: Lean 4, the Lean FRO, and Mathlib's 283k theorems — and pin the point that formalization targets a moving toolchain (tie to the author's own EML repo at Mathlib 4.28, 8,062 sorry-free jobs). Now teach benchmark literacy as a ladder: miniF2F (saturated) → PutnamBench (~1%→99% in 18 months) → ProofNet (autoformalization) → FrontierMath (research-level, still <a few percent) — the ladder simultaneously narrates progress AND its limits, inoculating against hype. Use ProofNet to open the autoformalization discussion and land the course's subtlest point: the Lean kernel guarantees the proof matches the statement, but nothing guarantees the statement matches the mathematician's intent — the unfaithful-but-well-typed statement is where errors hide. Finally, zoom out from competition to research with the two human-scale stories — the Equational Theories Project (22 million Lean-verified implications, mass collaboration, echoing McCune/Robbins) and Tao's PFR-via-Blueprint — to answer 'why should a working mathematician care'. Close by returning to the IMO 2025 three-way snapshot (natural-language gold, formal gold, formal verification) as the unresolved tension the students now own. Throughout, prefer one concrete number with a URL over adjectives, and let students run a real system (ReProver / lambda_lab's Lean server / Aristotle workflow) so the landscape is felt, not just surveyed.

## Connections to existing material
"This dossier extends the falenty-2026 lambda-calculus book directly: its chapter 8 (Lean 4), chapter 9 (AlphaGeometry story, notebooks 10_alphageometry_story / 10b_aristotle_and_ai_math / 10c_aristotle_workflow), and chapter 11 (industry: Amazon/Dafny/CompCert) already name AlphaProof, AlphaGeometry, and Lean — Lecture 6 turns those one-liners into a sourced, quantified landscape. The Further Reading list (Lean 4, Coq/Rocq, Agda, Idris 2) supplies the course's proof-assistant span, matching PutnamBench's Lean/Isabelle/Coq multilingual design and grounding the artifact ideas across the four target languages. The strongest continuity asset is the author's own eml-formalization repo: a real Lean 4 + Mathlib v4.28 formalization finishing 8,062 lake jobs sorry-free (with Aristotle/GPT-Pro/Claude in the loop) — a concrete, in-house worked example of exactly the autoformalization-and-verification pipeline this dossier surveys, and living proof of the 'formalization pins an exact toolchain' point (it is at 4.28 while HEAD is 4.32). lambda_lab already ships the machinery to make the survey hands-on: a lean_server, a prover backend, curry_howard/kb/peano commands, and archived Aristotle proof jobs (including demo-demorgan) — ideal hooks for the proposed `landscape`/benchmark and faithfulness artifacts. Finally, classical-foundations-ann is the depth-and-structure template: mirror its part-by-part build-up, its RESEARCH_REPORT-style sourcing, and its blend of narrative Markdown with runnable notebooks so Lecture 6 reads at the same scholarly altitude."

## Artifact ideas

- **Lean 4** (intermediate): A 'benchmark ladder' notebook that loads five real miniF2F/PutnamBench-style statements in Lean 4 and asks students to prove the two easy ones by hand, watch a small model (or ReProver) attempt the middle one, and stare at a FrontierMath-flavored problem no system solves — making the difficulty gradient tactile. Reuses lambda_lab's lean_server and the existing 15x_tutorial notebooks.
- **Lean 4** (intermediate): An 'autoformalization faithfulness' exercise: give students an informal theorem plus THREE candidate Lean statements that all typecheck, exactly one faithful, and have them (and then an LLM) pick the right one — dramatizing that the kernel checks proof-against-statement, not statement-against-intent. Directly extends the course's Curry–Howard chapter and the ProofNet idea.
- **Python (lambda_lab)** (beginner): Extend lambda_lab with a `landscape` (or `benchmarks`) command that pretty-prints a live-updatable table of the systems in this dossier (system, paradigm, miniF2F%, PutnamBench, year, open/closed) with source URLs — a terminal companion to the landing page's 'why now' section, in the style of the existing tour/kb commands.
- **Python (lambda_lab)** (beginner): A small `curry_howard`/`kb` add-on that runs the same tiny propositional-logic goal (e.g. a De Morgan law, mirroring the existing demo-demorgan Aristotle job) and shows it (a) as a lambda-term proof, (b) shipped to a real prover backend — connecting the toy lambda calculus to the industrial Lean pipeline in one screen.
- **Isabelle/HOL** (advanced): A cross-system 'same theorem, three assistants' handout: take one PutnamBench problem formalized in Lean 4, Isabelle/HOL and Coq/Rocq (PutnamBench ships all three) and have students compare the statement syntax and one proof, making concrete why multilingual benchmarks matter and how proof assistants differ in feel.
- **Coq/Rocq** (advanced): A short historical bridge lab: replicate a Robbins-algebra-style equational fact (the McCune/EQP lineage behind the Equational Theories Project) as a small magma-implication exercise, showing an automated-proof success from 1996 and its 2024 mass-collaboration descendant side by side.
- **Lean 4** (intermediate): A Blueprint mini-project: take a two-page theorem (e.g. irrationality of sqrt 2 or a pigeonhole result already in the tutorials) and have students build a Massot-style Blueprint dependency graph linking each node to its Lean proof — a scaled-down reenactment of Tao's PFR workflow they can finish in one session.

## Pitfalls / misconceptions

- Conflating IMO 2024 (formal, Lean-checked, silver) with IMO 2025 (natural-language, ungraded prose, gold) — they are different systems, years, and paradigms; state which is which.
- Reading a high miniF2F score as 'AI can do research mathematics'. miniF2F is saturated high-school/olympiad material; FrontierMath (<a few percent) is the research-level reality — always pair the two.
- Treating 'the Lean kernel verified it' as end-to-end correctness. The kernel only certifies proof-against-statement; an unfaithful autoformalized statement can be 'proved' while meaning the wrong thing.
- Quoting a single benchmark number without its qualifiers — pass@k, compute/dollar budget, dataset version, and self-correction mode all move the number by tens of points (e.g. Goedel-V2 88.0% standard vs 90.4% self-correction).
- Citing FrontierMath scores uncritically: a June 2026 audit found errors in ~42% of problems and third-party leaderboards disagree wildly — prefer Epoch AI's own figures and note the dataset version.
- Presenting benchmarks as static. PutnamBench, miniF2F and FrontierMath are all under active correction/versioning and leaderboards change monthly; date every claim.
- Implying only DeepMind matters. The open-weight race (DeepSeek, Goedel, Seed, Aleph, Kimina) and academic tooling (LeanDojo/ReProver) are where reproducible, teachable progress lives.

## Canonical references

- Hubert, T., Mehta, H., et al. (Google DeepMind AlphaProof team), "Olympiad-level formal mathematical reasoning with reinforcement learning", Nature, published 12 Nov 2025, doi:10.1038/s41586-025-09833-y. — <https://www.nature.com/articles/s41586-025-09833-y>  
  _The peer-reviewed source of record for AlphaProof; use for the exact IMO 2024 claim (silver, 28/42) and the test-time RL mechanism._
- DeepMind, "AI achieves silver-medal standard solving International Mathematical Olympiad problems", Google DeepMind blog, 25 July 2024. — <https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/>  
  _Primary announcement with the per-problem breakdown (which problems AlphaProof vs AlphaGeometry 2 solved) and the one-point-short-of-gold framing._
- Trinh, T. H., Wu, Y., Le, Q. V., He, H., Luong, T., "Solving olympiad geometry without human demonstrations" (AlphaGeometry), Nature 625, 476–482 (2024), doi:10.1038/s41586-023-06747-5. — <https://doi.org/10.1038/s41586-023-06747-5>  
  _The AlphaGeometry 1 paper — canonical neuro-symbolic example (LM proposes constructions, symbolic engine deduces); already cited in the author's Further Reading._
- Chervonyi, Y., Trinh, T. H., et al., "Gold-medalist Performance in Solving Olympiad Geometry with AlphaGeometry2", arXiv:2502.03544 (Feb 2025). — <https://arxiv.org/abs/2502.03544>  
  _AlphaGeometry 2 numbers: 54%→84% solve rate, 66%→88% language coverage, IMO 2024 P4 in 19s._
- Ren, Z. Z., et al. (DeepSeek-AI), "DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via Reinforcement Learning for Subgoal Decomposition", arXiv:2504.21801 (30 Apr 2025). — <https://arxiv.org/abs/2504.21801>  
  _The flagship open-weight prover; source for 88.9% miniF2F, 49/658 PutnamBench, 671B MoE architecture._
- Lin, Y., et al., "Goedel-Prover-V2: Scaling Formal Theorem Proving with Scaffolded Data Synthesis and Self-Correction", arXiv:2508.03613 (Aug 2025); and Goedel-Prover (V1), arXiv:2502.07640 (Feb 2025). — <https://arxiv.org/abs/2508.03613>  
  _Open-source SOTA at release; 88.0/90.4% miniF2F, 86 PutnamBench, 8B matching the 671B model — the efficiency-frontier story._
- Seed-Prover team (ByteDance), "Seed-Prover: Deep and Broad Reasoning for Automated Theorem Proving", arXiv:2507.23726 (July 2025); Seed-Prover 1.5, arXiv:2512.17260 (Dec 2025). — <https://arxiv.org/abs/2507.23726>  
  _Frontier formal prover: saturates miniF2F, 5/6 IMO 2025 in Lean, PutnamBench progression._
- Yang, K., et al., "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models", NeurIPS 2023 (Datasets & Benchmarks), arXiv:2306.15626. — <https://arxiv.org/abs/2306.15626>  
  _The open, teachable baseline: interactive Lean environment, 98,734-theorem benchmark, ReProver premise retrieval; MIT-licensed._
- Zheng, K., Han, J. M., Polu, S., "miniF2F: a cross-system benchmark for formal Olympiad-level mathematics", ICLR 2022, arXiv:2109.00110. — <https://arxiv.org/abs/2109.00110>  
  _Defines the entry-level benchmark (488 problems, cross-system) whose saturation anchors the 'why now' narrative._
- Tsoukalas, G., et al., "PutnamBench: Evaluating Neural Theorem-Provers on the Putnam Mathematical Competition", NeurIPS 2024, arXiv:2407.11214; live leaderboard at trishullab.github.io/PutnamBench. — <https://trishullab.github.io/PutnamBench/leaderboard.html>  
  _The current frontier benchmark; multilingual (Lean/Isabelle/Coq) design maps to the course, and the leaderboard supplies the ~1%→99% climb._
- Glazer, E., et al. (Epoch AI), "FrontierMath: A Benchmark for Evaluating Advanced Mathematical Reasoning in AI", arXiv:2411.04872 (Nov 2024); benchmark pages at epoch.ai/frontiermath. — <https://epoch.ai/frontiermath>  
  _The research-level ceiling (<2% at launch), Fields-medalist authorship, and the June 2026 error-correction caveat for teaching source-criticism._
- Azerbayev, Z., Piotrowski, B., et al., "ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics", arXiv:2302.12433 (2023). — <https://arxiv.org/abs/2302.12433>  
  _Canonical statement+proof autoformalization benchmark (371 problems from standard texts), the bridge from informal to formal mathematics._
- Tao, T., et al., "The Equational Theories Project: Advancing Collaborative Mathematical Research at Scale", Terence Tao's blog (What's new), 9 Dec 2025; project at github.com/teorth/equational_theories. — <https://terrytao.wordpress.com/2025/12/09/the-equational-theories-project-advancing-collaborative-mathematical-research-at-scale/>  
  _The mass-collaboration, Lean-verified case study: 22,028,942 implications among 4,694 magma laws; historical link to McCune/Robbins._
- Tao, T., "Formalizing the proof of PFR in Lean4 using Blueprint: a short tour", What's new, 18 Nov 2023; project at teorth.github.io/pfr. — <https://teorth.github.io/pfr/>  
  _Model workflow for a real research-level formalization (3 weeks, Blueprint dependency graph); the 'how it's actually done' artifact for the course._
- Lean FRO, "The Lean FRO Year 3 Roadmap" and "About", lean-lang.org/fro; Lean 4.32.0 release notes (13 July 2026), lean-lang.org. — <https://lean-lang.org/fro/roadmap/1900-1-1-the-lean-fro-year-3-roadmap>  
  _Current funding/governance of the substrate ($10M Gerko July 2025, Sloan/Simons/Merkin/Convergent) and the July-2026 toolchain version._
- Mathlib community, live statistics, leanprover-community.github.io/mathlib_stats.html (accessed July 2026); background: The mathlib Community, "The Lean mathematical library", CPP 2020. — <https://leanprover-community.github.io/mathlib_stats.html>  
  _Authoritative current Mathlib size (283,067 theorems, 134,678 definitions, 772 contributors) — the substrate-scale numbers._
- DeepMind, "Advanced version of Gemini with Deep Think officially achieves gold-medal standard at the IMO", Google DeepMind blog, 21 July 2025. — <https://deepmind.google/blog/advanced-version-of-gemini-with-deep-think-officially-achieves-gold-medal-standard-at-the-international-mathematical-olympiad/>  
  _IMO 2025 natural-language gold (35/42, 5/6) — the paradigm-contrast data point that keeps the 'why now' section current._

## Volatile facts (sent to fact-check)

- At IMO 2024 the combined AlphaProof + AlphaGeometry 2 system scored 28/42 (silver-medal level, one point short of the gold cutoff), solving 4 of 6 problems; AlphaProof solved 3 of the 5 non-geometry problems including the hardest (P6). Peer-reviewed in Nature, 12 Nov 2025. (src: https://www.nature.com/articles/s41586-025-09833-y)
- Mathlib currently contains 283,067 theorems and 134,678 definitions from 772 contributors (well over 2 million lines), per the live leanprover-community statistics page (accessed July 2026). (src: https://leanprover-community.github.io/mathlib_stats.html)
- The latest stable Lean toolchain is Lean 4.32.0 (released 2026-07-13), with 4.33.0-rc1 out on 2026-07-15 — an approximately monthly release cadence. (src: https://lean-lang.org/doc/reference/latest/releases/)
- On PutnamBench (672 Lean problems as of Jan 2026) the field climbed from single digits in early 2025 to Aleph-Prover solving 668/672 (~99.4%) atop the leaderboard; DeepSeek-Prover-V2 reaches 88.9% on miniF2F and Goedel-Prover-V2-32B reaches 90.4% (self-correction). (src: https://trishullab.github.io/PutnamBench/leaderboard.html)
- The Equational Theories Project (launched by Terence Tao, 25 Sept 2024) resolved all 22,028,942 implications among the 4,694 magma laws of ≤4 operations, with every proof formally verified in Lean. (src: https://terrytao.wordpress.com/2025/12/09/the-equational-theories-project-advancing-collaborative-mathematical-research-at-scale/)
