# Peano Hydra: where symbolic search should end and learned search begin

```{admonition} Current verified product baseline
:class: important
The current immutable Alpha v25 release contains **2,080 independently
checked theorems**, **6,633 real theorem-proof dependency edges**, and an
unchanged **432-theorem Stable default**. The separate conservative-definition
DAG contains **120 reviewed definitions** and **214 reviewed definition
edges**. Blueprint notation and open research milestones do not grant proof
authority.

Hydra already runs bounded, independently replayed proof search under an
explicit complete-digest Alpha authority. Its one next product milestone is
to scale checked proof optimization, candidate discovery, and
supervised/preference post-training from that single frozen epoch. The older
247-theorem Qwen adapter remains bound to its historical release. The full
H0/H1 experiment gates are not complete, and no language-model advantage or
new mathematical-discovery claim follows from the initial preparation run.
```

Peano Hydra is an experiment, not a new trust assumption. We want to combine a
proof-producing arithmetic prover with a small language model and ask a narrow,
measurable question:

> Under the same inference budget, can the language model help solve more new
> problems than the strongest system that does not generate language-model
> actions?

The adjective *new* matters. The phrase *same budget* matters. Most of all,
*solve* means that Peano Lab's independent kernel checks a complete certificate
against the original formula. A model, a tactic, and an external prover may
suggest a route; none may declare the theorem.

The campaign's normative protocol is
[the binding design](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_HYDRA_DESIGN.md), and the executable
milestone gates are in
[the campaign plan](https://github.com/nasqret/vietnam2026/blob/peano-lab/PLAN/11_peano_hydra.md). This chapter explains
why those rules exist. The single current implementation sequence is the
[Hydra product roadmap](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/HYDRA_PRODUCT_ROADMAP.md),
with the verified data boundary in the
[post-training pipeline](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/HYDRA_POST_TRAINING.md).

## First correct the logical claim

Peano Lab uses an intuitionistic proof calculus for first-order arithmetic.
Standard first-order Heyting arithmetic is not a decidable theory: there is no
terminating algorithm that correctly labels every sentence theorem or
non-theorem. A finite website, a bounded search, or a decidable collection of
exercises does not change that fact.

There are therefore two honest goals:

1. build a **sound theorem prover** that returns a checked proof or `unknown`;
2. separately identify a **restricted decidable fragment**, state its exact
   grammar and semantics, and supply evidence for both positive and negative
   answers.

The second claim is stronger. Positive proof certificates are already natural:

\[
  K(\Gamma, p, A)=\mathsf{accept}
\]

says that the small kernel checked certificate $p$ as a derivation of $A$ from
$\Gamma$. A timeout cannot play the corresponding role for non-theorems. To
call a fragment decidable we need a terminating procedure and either
independently checkable negative certificates or agreement with a genuinely
independent reference decision procedure. Until then Hydra is a sound prover,
not a decider.

## One authority, many fallible explorers

Hydra deliberately has many ways to be clever and one way to be right.

```text
original goal -> deterministic symbolic closure -> certificate -> kernel
                         |
                         | critical frontier
                         v
                  typed macro proposal
                   /      |      \
          native search   Qwen   Vampire/E/SMT hints
                   \      |      /
                    transactional engine
                         |
                  symbolic closure resumes
                         |
              original-goal kernel replay
                    /             \
            checked theorem     rejection
```

The kernel is the sole positive authority. Everything else is untrusted:

- native normalization, rewriting, connection or focused search;
- theorem retrieval and clause ranking;
- Qwen as a student policy or value model;
- Codex as a teacher and data generator;
- Vampire, E, or an SMT solver as an external search assistant; and
- translators and proof reconstruction code.

This is especially important for Vampire. Vampire is a powerful classical
first-order prover, while Peano Lab's default logic is intuitionistic. A raw
Vampire success is not automatically a proof in Heyting arithmetic. We may use
it on a separately justified validity-preserving translation or on a stable
arithmetic side goal, and we may mine its derivation for instantiations or
lemmas. The final result still has to be reconstructed into ordinary Peano
proof terms and replayed. There is no trusted `vampire_proved` rule.

## The critical frontier

Calling a transformer for every tiny rewrite would be slow and scientifically
uninteresting. Symbolic code is excellent when the next move follows from a
dense local calculation. Language models are most plausible where search must
make a sparse semantic choice.

Hydra therefore runs cheap deterministic closure until it reaches a fixed
point. The **critical frontier** is a stalled state at which there is no
uniquely justified cheap continuation within the current bounds. Examples are:

- choosing an existential witness;
- inventing an intermediate lemma;
- selecting an induction variable and motive;
- selecting a useful case split;
- retrieving a small premise bundle from hundreds of theorems; or
- deciding which bounded solver should explore which subgoal.

Only then is the generative model called. After one valid high-level choice,
symbolic closure resumes. This leads to the testable decomposition

\[
  \text{proof search}
  = \text{cheap closure}^{*}
    ;\ \text{sparse macro choice}
    ;\ \text{cheap closure}^{*}.
\]

A cheap graph or state ranker may score the high-frequency inner loop. Qwen
should earn its more expensive call by resolving ambiguity that the cheaper
systems do not.

## A macro protocol, not a second proof language

The model does not emit kernel constructors. It proposes a small typed action:

```text
Use(name, specializations*)
Cut(kind = have | suffices, name, formula)
Witness(term)
Induct(variable, motive)
Rewrite(source, direction, location)
Split(kind)
Dispatch(solver, premises, bounds)
```

In the target, not-yet-completed H0.3 protocol, each action will have one
canonical serialization and compile deterministically to
existing Peano Lab commands. For example, `Witness(t)` becomes the public
`exists t` action; a `Cut` becomes ordinary `have` or `suffices`. `Dispatch`
starts a bounded untrusted search and may return hints or a reconstructable
derivation, but never closes a goal merely because a solver printed “theorem.”

Compilation and execution are transactional. If parsing, specialization,
rewriting, or reconstruction fails, the proof state and undo history remain
exactly unchanged. The trace retains the raw model text, parsed action,
compiled commands, intermediate states, solver transcript, resource use, and
kernel result. This makes it possible to distinguish model failure, interface
failure, search failure, and certificate failure.

The first executable plumbing test uses a deliberately smaller compatibility
format: one complete public Peano line with a structural head. It accepts such
actions as `have`, `induction`, `exists`, `cases`, and `rewrite`, while
rejecting `simp`, `ring`, `compact_arith`, tactical wrappers, session commands,
and multiline scripts. This is enough to test the trust boundary and the
symbolic/model hand-off. It is not yet the structured version-1 action schema
above, and it is not training evidence. Recorded teacher routes require a
complete kernel-checked QED by default; an open trace can enter only through an
explicit partial-evidence option and never becomes a positive proof label.

## Why the library must have epochs

The historical source-bound model-v3 training epoch contains 247 independently
checked runtime theorems, including a constructive, conservatively encoded
Fundamental Theorem of Arithmetic. The current separately sealed Alpha v25
release instead contains 2,080 independently checked theorems and its
conservative-definition registry contains 120 reviewed nodes. The old adapter
cannot silently inherit that larger authority. Hydra gains current Alpha
access only under the exact complete-digest surface label and an explicitly
finite theorem allowlist; the ordinary public proof surface remains the
unchanged 432-theorem Stable default.

Either epoch can be a useful training source. Neither is a fair test of whether
a model can prove the same theorems after reading their proofs.

At the start of a campaign we freeze an ordered epoch $L_0$. Its content root
commits to each theorem's canonical statement, dependencies, source and script,
certificate, proof size and depth, and declaration order. A model can train on
eligible $L_0$ material. The final benchmark is lineage-disjoint from it.

If the mathematical library later grows, those theorems enter $L_1$. They
cannot silently appear in retrieval or prompts for the $L_0$ experiment. A
new epoch needs a newly sealed benchmark. This rule avoids a surprisingly easy
mistake: improving the prover by adding the answer to its library and then
reporting the improvement as search intelligence.

## Leakage follows mathematical ancestry

Randomly splitting tactic rows is not enough. One authored proof can produce
hundreds of state/action rows, and two differently worded statements can be
the same mathematical problem. Hydra partitions *before* row expansion.

Every target and artifact receives a lineage identity. The separation graph
contains at least:

- proof dependencies and reverse dependencies;
- equivalent or stronger reformulations;
- shared problem-family and generator ancestry;
- generator seed and template relationships; and
- authored, symbolic, teacher, and student provenance.

For a sealed theorem $T$, training and run-time retrieval mask $T$, equivalent
forms, its family, proof and trace, generator seed, stronger capstones,
descendants that reveal it, and any theorem whose certificate depends on a
masked node. The connected components are split first; only then are prompts,
actions, negatives, or paraphrases produced.

This is stricter than matching statement strings. It should be. A theorem
prover that retrieves a disguised copy of the target is demonstrating lookup,
not discovery.

## Reciprocity is existing proof evidence, not a new discovery

Quadratic reciprocity is a demanding stress test because its formal development
requires a long dependency chain and several useful choices of representation.
At a much older 384-theorem historical checkpoint, the library contained 137
checked reciprocity-infrastructure certificates without an admitted
reciprocity endpoint. That is no longer the current state: the exact
`quadratic_reciprocity_combined` theorem was independently closed in Alpha v16,
its complete original proof graph has 557 checked theorem nodes, and it
remains checked in current Alpha v25.

Consequently the existing endpoint cannot honestly count as a novel Alpha-v25
discovery. To use a genuinely future stronger statement $Q$ as an experimental
test, we must deposit it before its proof enters the library. We then mask
the whole $Q$ lineage: definitions introduced only for the route,
residue-theory lemmas, generated variants, equivalent formulations, authored
scripts, teacher sketches, stronger consequences, and retrieval records whose
proofs use them. The split must use lineage IDs and the dependency graph,
not theorem names.

The already published development is excellent training data for the *next*
questions, but it can no longer be clean headline evidence for discovering
quadratic reciprocity itself. Existing-theorem optimization and genuinely
future-theorem discovery are different evidence categories.

## The teacher experiment is only an interface test

Before spending GPU time, a strong teacher such as Codex may attempt the
symbolic system's unsolved DEV frontier using only the frozen macro interface.
This answers:

> Does the interface expose actions that could bridge the symbolic gaps?

If the teacher cannot solve even 10% of those cases, the likely bottleneck is
the action space, observation, or symbolic backend—not the size of Qwen. If it
solves at least 20%, we have useful headroom for distillation.

But the teacher's score is not a student score. Its outputs may seed tagged
training examples after kernel replay, provided their lineages do not intersect
the final set. It must never see the final benchmark. A spectacular teacher
pilot still does not show that Qwen learned the behavior or that Hydra beats a
symbolic baseline.

The earlier model-v3 four-goal run illustrates the same restraint. The trained
adapter solved three shallow goals at $k=1$, while a revision/configuration-
pinned pretrained comparison solved none; the induction-heavy goal remained
unsolved. Those three scripts kernel-check. Four goals, however, are a launch
smoke, not a statistically defensible capability result and not evidence for
Hydra's new architecture.

### The first functional plumbing test

The repository now contains a provider-neutral bootstrap in
`training/peano_hydra/` and a runnable pilot:

```console
python3 scripts/eval_peano_hydra.py --include-trace
```

It uses the checked consecutive-product script
`forall n. exists x. n * (n + 1) = 2 * x`. Both lanes receive the same fixed,
state-independent symbolic candidates, `compact_arith` and
`compact_arith [IH_witness]`, and the same three-slot, depth-13, beam-1 search
budget. The control's third slot is an identified null head. The hybrid's third
slot supplies the script's ten structural actions only at their ten exact
canonical states.

The control exhausts at the root. The hybrid reproduces the 13-command route,
then a fresh retained-trace replay checks its 180-node certificate against the
original formula. A related mutated statement activates none of the recorded
macro states and remains `unknown`; that is transcript non-reuse, not a
non-theorem certificate. The complete deterministic evidence is committed as
`artifacts/peano-hydra/teacher-oracle-pilot-v1.json`.

This result is useful and deliberately modest. It proves that portfolio
quotas, exact-state gating, public tactics, proposal provenance, independent
replay, and the kernel compose. The structural route came from the answer, and
the contextual symbolic candidate was human-selected for this example. No
Qwen or Codex was called, so the pilot measures neither model capability nor a
hybrid advantage.

The report also marks every lane comparison-ineligible. At this bootstrap
stage the ledger retains extracted tactic lines but not raw decoder text,
token and latency measurements, or a campaign provider attestation, and the
critical-state allowlist is copied from the teacher route rather than detected
as a symbolic fixed point. Clean execution therefore means “the plumbing ran
as specified,” not “this row may enter a model comparison.”

### One verified Alpha-v25 preparation workflow

The production-development entry points are:

```console
make hydra-check
make hydra-prepare
```

The first command checks the shared execution and DAG contracts. The second
freezes the exact current theorem/definition epoch and writes:

```text
_deploy/hydra/epoch.json
_deploy/hydra/sft.jsonl
_deploy/hydra/preferences.jsonl
_deploy/hydra/discovery.jsonl
_deploy/hydra/manifest.json
```

Supervised rows come only from complete original-goal kernel-checked proofs.
Preference rows compare independently replayed routes for the same theorem and
exact authority. Discovery rows label checked candidate attempts without
claiming semantic mathematical novelty or automatically admitting a theorem.
The current candidate collision test excludes only an identical original
statement SHA-256; it does not decide equivalence under renaming, conservative
definitions, or mathematical reformulation. Route optimization likewise
selects the best observed checked path by tactic count, proof nodes, expanded
states, and an exact-command tie-breaker; it does not prove global
proof-length optimality.
Later Alpha releases still require their ordinary dependency-closed review.

These bounded local artifacts are development evidence, not a sealed final
benchmark or an H3-scale training corpus. They neither train Qwen by
themselves nor claim that any model improves proof search.

## Build the strongest baseline first

The LLM should not receive credit for work that a good algorithm already does.
Before model training, Hydra freezes a symbolic portfolio containing as much
of the following as the fragment permits:

- canonical normalization and equality rewriting;
- arithmetic closure and bounded witness enumeration;
- focused intuitionistic or connection/tableau search;
- induction-candidate enumeration;
- deterministic theorem retrieval; and
- reconstructed hints from external first-order or SMT solvers.

Each component is measured alone and in portfolio. Development-only scheduling
chooses the strongest solved-versus-resource envelope. That frozen system is
$S$, the real baseline.

Then we add increasingly expensive learned components:

\[
S \subset S+\mathrm{BM25} \subset S+R \subset S+C
  \subset S+P \subset S+P+V,
\]

where $R$ is learned retrieval, $C$ a cheap clause/state ranker, $P$ the macro
policy, and $V$ a value model for best-first or PUCT search. Shuffled scores,
random valid actions, no-retrieval, no-value, no-symbolic, and LLM-only runs
show which component caused an improvement. If cheap retrieval or ranking
captures the gain, increasing the transformer is the wrong engineering move.

## Training data must end in QED

A positive policy row is admissible only when it lies on a complete trajectory
whose final certificate checks against the original goal. Partial progress,
an attractive lemma, a solver assertion, and a syntactically valid tactic are
useful diagnostic or negative data but not positive proof labels.

The first curriculum target is deliberately large and balanced: at least
100,000 unique macro transitions from at least 20,000 checked QED roots, every
macro head represented, and at least 2,000 examples for each open-ended
frontier choice. Clean generation must be byte-for-byte reproducible. The
tokenizer must reject examples that do not fit; silent truncation changes the
task and can remove the answer.

The initial student stays modest—roughly 1.7–3 billion Qwen parameters—until
the data and search design pass causal gates. Supervised training must beat the
identical pretrained model on DEV, solve a meaningful number of registered
frontier cases, and have a positive paired confidence bound. Value search and
expert iteration have their own incremental gates. Only newly discovered,
independently checked QEDs enter expert iteration.

## What “matched compute” means

We compare three frozen systems on the same sealed targets:

- $S$: strongest purely symbolic portfolio;
- $S+R$: strongest non-generative learned system; and
- $H$: full Hydra with the generative model at critical frontiers.

Each is measured at 1, 10, 60, and 300 seconds per problem on the same hardware
class. Wall time alone can hide very different work, so the report also gives
CPU instructions or symbolic activations where possible, GPU/CPU energy, peak
memory, and cost. Training cost is reported separately and as an amortized
break-even curve.

The main curve is independently checked solved fraction versus resource. We
also report time-to-proof, PAR-2, proof size, invalid actions, calls, and the
asymmetric sets

\[
  H\setminus(S\cup(S+R))
  \quad\text{and}\quad
  (S\cup(S+R))\setminus H.
\]

The first shows genuinely hybrid-only solves; the second prevents an average
score from hiding regressions.

The preregistered headline gate is intentionally hard. At two adjacent time
budgets, Hydra must beat the better baseline by at least three percentage
points, the lower paired stratified 95% interval must remain above zero, and a
corrected exact paired test must reject equality. Every counted proof must
replay, with no negative-decision regression. Otherwise the result is simply:

> No demonstrated LLM advantage under these budgets.

That is a useful result. We do not rescue a miss by reopening the benchmark,
tuning after inspection, changing to `pass@k`, or asking the teacher.

## The seven gates

The campaign proceeds in order:

| Gate | Question | Required evidence |
|---|---|---|
| H0 | Is the logic and fragment exact? | conformance, reference agreement, mutation rejection |
| H1 | Is there clean headroom? | frozen $L_0$, sealed lineage split, symbolic and teacher DEV probes |
| H2 | Is the non-LLM baseline strong? | proof-producing portfolio and replayed resource curves |
| H3 | Is the curriculum real proof data? | deterministic corpus, complete QED roots, zero leakage |
| H4 | Which learned component helps? | model ladder and matched causal ablations |
| H5 | Does the LLM win once, fairly? | one-shot sealed matched-compute comparison |
| H6 | Can another group reproduce it? | source, environments, raw traces, certificates, tables, review |

These are ordered evidence gates, not promised calendar dates. GPU training
follows checked epoch preparation, independent replay, leakage control, and a
strong baseline; the useful current Hydra product does not by itself complete
the separate H0/H1 research gates.

## What would be novel

The novelty would not be “an LLM printed a Peano proof.” The stronger result
would be a clean demonstration that sparse learned semantic decisions improve
a sound, proof-producing intuitionistic arithmetic prover over strong symbolic
and cheap learned baselines under equal resources. A negative result with the
same controls would also teach us where language models are unnecessary.

That is why the Hydra metaphor fits. The system has many exploratory heads,
but every path returns to one small kernel. More heads may find more routes;
none gets a vote on truth.

## Further reading

- [Peano Lab binding design](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_LAB_DESIGN.md)
- [Peano Hydra binding design](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_HYDRA_DESIGN.md)
- [Hydra product roadmap](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/HYDRA_PRODUCT_ROADMAP.md)
- [Hydra post-training pipeline](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/HYDRA_POST_TRAINING.md)
- [Training a Peano policy](training-a-peano-policy.md)
- [AlphaGeometry](https://www.nature.com/articles/s41586-023-06747-5)
- [AlphaProof](https://www.nature.com/articles/s41586-025-09833-y)
- [Thor](https://proceedings.neurips.cc/paper_files/paper/2022/hash/377c25312668e48f2e531e2f2c422483-Abstract-Conference.html)
- [Efficient Neural Clause-Selection Reinforcement](https://arxiv.org/abs/2503.07792)
  (evaluated inside Vampire)
- [Intuitionistic Logic Theorem Proving library](https://www.iltp.de/)
