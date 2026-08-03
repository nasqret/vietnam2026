# Peano Hydra — L2/L3 campaign plan

## Objective

Build and evaluate a sound neuro-symbolic prover for Peano Lab. The system
combines a strong non-generative symbolic portfolio with sparse LLM proposals
at critical proof frontiers, but admits a theorem only after independent
kernel replay against the original goal.

The experiment is successful only if it survives the frozen, matched-compute,
one-shot comparison in H5. A working demo, a teacher-authored proof, or a
larger raw `pass@k` is not a substitute.

The binding architecture and claim rules are in
[`docs/PEANO_HYDRA_DESIGN.md`](../docs/PEANO_HYDRA_DESIGN.md). This module is
numbered 11 because [`PLAN/10_arithmetic_library.md`](10_arithmetic_library.md)
already owns module 10.

## Non-negotiable contracts

- [ ] Preserve the Peano Lab trust boundary: every scored QED independently
      kernel-checks against the original target; all search and ML components
      remain untrusted.
- [ ] Freeze and hash the exact language/semantics profile. Do not call full HA
      decidable; do not call the restricted system a decider without sound
      negative evidence.
- [ ] Freeze an ordered library epoch before building the benchmark. Later
      library growth cannot enter an active campaign.
- [ ] Split by mathematical lineage and dependency component before expanding
      traces. Mask targets, equivalents, families, seeds, scripts,
      descendants, and dependent retrieval entries.
- [ ] Retain complete provenance, model/solver calls, resource accounting,
      certificates, and replay results needed to rebuild every table.
- [ ] Keep the final set under an independent evaluation owner and unlock it
      once, only after all systems and budgets are frozen.
- [ ] Record failed gates and negative results. Never tune on the sealed test.

## H0 — Semantic and functional core

### H0.1 Freeze the claimable fragment

- [ ] Write the exact term/formula grammar, binding/substitution rules,
      intuitionistic proof calculus, arithmetic axioms, and induction policy.
- [ ] State which formulas, if any, belong to a decidable subfragment and give
      its decision theorem and terminating algorithm.
- [ ] Specify canonical input normal forms and every translation used by an
      external solver.
- [ ] Specify separate evidence schemas for `proved`, `not_theorem`, and
      `unknown`; a timeout is always `unknown`.
- [ ] Publish one canonical machine-readable profile and bind its digest into
      every downstream artifact.

### H0.2 Establish independent semantic checks

- [ ] Cold-replay the entire initial library epoch twice and compare roots.
- [ ] Assemble at least 1,000 semantic-conformance formulas: at least 400
      theorems and, if a decision claim is retained, at least 400 certified
      non-theorems.
- [ ] Build an independently implemented reference for the claimed fragment
      and compare every in-scope result.
- [ ] Mutate proof constructors, binders, substitutions, translations,
      induction instances, and negative witnesses; require rejection.
- [ ] Re-run kernel import-boundary, original-goal, and transactional-history
      tests.

### H0.3 Freeze the macro protocol

- [ ] Specify canonical typed encodings for `Use`, `Cut`, `Witness`, `Induct`,
      `Rewrite`, `Split`, and bounded `Dispatch`.
- [ ] Compile each action deterministically to existing public Peano commands
      and/or an untrusted bounded solver call.
- [ ] Verify that failure leaves proof state and history byte-for-byte
      unchanged.
- [ ] Reject unknown versions, hidden commands, out-of-profile formulas,
      unavailable lemmas, and solver claims without reconstruction.
- [ ] Log raw proposals, parsing, compilation, state transitions, solver
      transcripts, and replay outcome in a canonical trace.

### H0 acceptance gate

- [ ] Two identical 100%-green cold replays of the frozen library.
- [ ] All conformance/reference checks agree and all required mutations fail.
- [ ] No kernel dependency on engine, UI, ML, or external solver code.
- [ ] Exact fragment and claim boundary reviewed before benchmark generation.

**No-go:** any false acceptance, unresolved semantics, or unsupported negative
claim. If negative evidence is not available, explicitly relabel the project a
sound theorem prover and continue without a decision claim.

## H1 — Library epoch, sealed benchmark, and interface headroom

### H1.1 Freeze `L0`

- [ ] Snapshot the complete checked public catalog available at freeze time
      (at least the current 247-theorem runtime).
- [ ] For each theorem bind name, canonical statement, ordered dependencies,
      source/script/certificate hashes, node count, depth, declaration order,
      and language profile.
- [ ] Compute an ordered epoch root and independently verify every certificate.
- [ ] Record all later theorems under `L1` or later; prevent them from entering
      this campaign's training, retrieval, imports, or evaluation.

### H1.2 Build lineage before rows

- [ ] Assign stable lineage IDs to authored, generated, translated, and
      reformulated problems.
- [ ] Build dependency, equivalence, family, generator-seed, and authorship
      edges; split connected components before expanding proof-state rows.
- [ ] Compile per-target reverse-dependency masks, including stronger
      capstones and retrieval entries whose certificates use masked nodes.
- [ ] Run adversarial contamination checks over normalized statements,
      certificates, prompts, traces, and generator provenance.

### H1.3 Seal the benchmark

- [ ] Prepare TRAIN/DEV plus an independently held final set of at least 1,000
      targets.
- [ ] Include at least 200 human-authored or chronologically future-library
      statements and, if H0 permits, at least 300 certified non-theorems.
- [ ] Stratify before outcomes by syntax, induction, witness/cut demand,
      premise-composition novelty, and symbolic difficulty.
- [ ] Deposit encrypted/hash-committed final manifests with an independent
      evaluation owner; developers see aggregate schema only.

### H1.4 Measure headroom on DEV only

- [ ] Run the initial symbolic system at 1, 10, 60, and 300 seconds and record
      wall time, CPU instructions, energy, memory, clauses/states, and proof
      size.
- [ ] Mark deterministic fixed points and extract the critical frontier.
- [ ] Let Codex or another strong teacher propose macros on that DEV frontier;
      independently replay every candidate.
- [ ] Tag teacher artifacts and exclude any intersecting final lineage.

### H1 acceptance gate

- [ ] Zero detected contamination.
- [ ] At 60 seconds the symbolic baseline leaves at least 100 targets or ten
      percentage points unsolved.
- [ ] The teacher closes at least 20% of the symbolic DEV frontier through the
      frozen macro interface.

**Pivot rules:** if symbolic solves at least 99.5% at 60 seconds, study
latency/proof size rather than claim a solve-rate opportunity. If the teacher
closes below 10%, repair the action interface before training. A successful
teacher pilot establishes interface headroom only—never Qwen capability or an
LLM win.

## H2 — Strong frozen symbolic portfolio

- [ ] Implement proof-producing deterministic normalization, rewriting, and
      arithmetic closure.
- [ ] Implement an intuitionistically valid focused/connection/tableau search
      for the frozen fragment.
- [ ] Add bounded witness/instantiation and induction-candidate enumeration.
- [ ] Add optional Vampire, E, and SMT adapters only for proved
      validity-preserving subtranslations or stable/classical side goals.
- [ ] Reconstruct all external-solver successes into ordinary Peano
      certificates; never score status strings or untranslated proof objects.
- [ ] Tune portfolio scheduling on DEV only.
- [ ] Freeze component binaries, options, translators, parsers, schedules, and
      budgets.
- [ ] Make every component independently disableable.

### H2 acceptance gate

- [ ] Every counted positive and negative result passes its independent replay
      authority.
- [ ] The portfolio weakly dominates each component on DEV
      solved-versus-resource AUC.
- [ ] The exact frozen portfolio is registered as baseline `S` before any
      final-set access.

## H3 — Checked macro curriculum

- [ ] Generate at least 100,000 unique positive macro transitions from at
      least 20,000 complete original-goal kernel QED roots.
- [ ] Cover all macro heads; collect at least 2,000 examples for every
      open-ended critical-frontier head.
- [ ] Give every eligible `L0` theorem at least eight independent positive-use
      lineages or mark it ineligible/held out with a reason.
- [ ] Keep authored, symbolic, Codex-teacher, Qwen-rollout, failed, and partial
      sources separately tagged.
- [ ] Admit only complete replayed QEDs as positive labels. Retain failures and
      partial paths only as labeled search evidence.
- [ ] Deduplicate by canonical state/action and lineage, not surface spelling.
- [ ] Audit state/action balance, theorem-use coverage, induction/cut/witness
      coverage, sequence lengths, and tokenizer round trips.
- [ ] Reject over-length examples instead of truncating them silently.
- [ ] Rebuild twice from clean inputs and compare bytes and Merkle roots.

### H3 acceptance gate

- [ ] Thresholds above are met, every positive root replays, clean builds are
      byte-identical, and contamination count is zero.
- [ ] Dataset/model cards disclose generators, licenses, filters, duplicates,
      failure data, lineage construction, and known blind spots.

## H4 — Model ladder, search, and causal ablations

Run each rung under registered DEV budgets:

- [ ] `S`: frozen symbolic portfolio.
- [ ] `S+BM25`: deterministic lexical theorem retrieval.
- [ ] `S+R`: learned retrieval.
- [ ] `S+C`: cheap learned clause/state ranking.
- [ ] `S+P0`: identical pretrained Qwen macro policy.
- [ ] `S+P1`: 1.7–3B Qwen supervised macro policy.
- [ ] `S+P1+V`: value-guided best-first or PUCT search.
- [ ] `H`: checked expert iteration, only if earlier gates pass.

Required controls:

- [ ] shuffled learned scores;
- [ ] random valid macro actions;
- [ ] no retrieval;
- [ ] no value model;
- [ ] no clause ranker;
- [ ] no symbolic closure; and
- [ ] LLM-only generation.

### H4 component gates

- [ ] Retriever: recall@8 at least 75% and at least ten points above BM25, or
      equal recall at materially lower declared cost.
- [ ] Clause ranker: positive lower 95% paired solve-difference bound at equal
      instructions, or at least 20% fewer activations with under one point
      solve loss.
- [ ] SFT: at least five DEV points over the identical pretrained model, at
      least 25 registered frontier solves, and a positive lower 95% paired
      interval.
- [ ] Value search: at least 5% relative gain in solved-versus-resource AUC.
- [ ] Expert iteration: only checked QEDs enter; clean-rebuild and continual
      variants are compared; stop after two rounds below one point gain.
- [ ] Do not scale the model if retrieval/ranking captures the improvement.
      Stop or redesign after two preregistered SFT attempts miss the gate.

## H5 — One-shot matched-compute final evaluation

### H5.1 Freeze

- [ ] Register source commit, clean tree, `L0`, language profile, lineage mask,
      benchmark commitment, solver binaries/configs, models/weight hashes,
      tokenizer, prompts, search code/configs, seeds, hardware, budgets,
      metrics, tests, and claim template.
- [ ] Name the independent evaluation owner and verify that no developer has
      access to final payloads.
- [ ] Freeze `S`, strongest non-generative `S+R`, and full `H`.

### H5.2 Execute once

- [ ] Unlock once; run all three systems at 1, 10, 60, and 300 seconds on the
      same targets and hardware class.
- [ ] Retain every raw model call, action extraction, executed edge, solver
      call, certificate, failure, and resource sample.
- [ ] Independently replay all counted proofs and all claimed negative
      certificates.
- [ ] Rebuild tables without model or solver access from the closed evidence
      bundle.

### H5.3 Decide the claim

- [ ] Report solved fraction, PAR-2/survival, proof nodes/depth, invalid
      actions, calls, memory, energy, cost, hybrid-only, and baseline-only
      solves, both overall and by preregistered stratum.
- [ ] Compute paired stratified bootstrap intervals and the corrected exact
      paired test.
- [ ] Claim an LLM advantage only if, at two adjacent budgets,
      `H - max(S, S+R) >= 3` percentage points, the lower paired 95% bound is
      positive, the corrected exact test rejects equality, all proofs replay,
      and no soundness/negative-decision regression occurs.
- [ ] Otherwise publish exactly: “no demonstrated LLM advantage under these
      budgets.” Do not reopen, tune, add samples, or switch to `pass@k`.

## H6 — Release and independent reproduction

- [ ] Release source, containers, lockfiles, SBOM, licenses, model/data cards,
      `L0`, public benchmark construction materials, lineage/mask manifests,
      solvers/adapters, frozen configs, permitted checkpoints, certificates,
      raw transcripts, resource logs, replay scripts, and table builders.
- [ ] Publish a dashboard that distinguishes live observations, cached data,
      final attested results, and unavailable evidence.
- [ ] Publish the full method and negative findings in the Jupyter Book and
      Obsidian vault.
- [ ] Reproduce certificate judgments and paper tables on a fresh machine.
- [ ] Pass the complete Peano and Lambda suites, strict book build, executable
      command replay, vault/link checks, artifact drift checks, and license
      audit.
- [ ] Obtain independent sign-off on leakage, matched compute, replay, and
      admissible wording.
- [ ] Publish/merge only at an authorized milestone boundary.

## Quadratic-reciprocity expansion track

This is future library growth, not part of `L0` unless completed before H1.

- [ ] Define a separate epoch for the required residue, primality, and
      reciprocity statements.
- [ ] Deposit candidate evaluation statements before any proof scripts,
      traces, or teacher sketches are created.
- [ ] Give the complete development one lineage family with explicit
      sub-lineages and dependency edges.
- [ ] When reciprocity is a target, mask its definitions introduced solely for
      the route, intermediate lemmas, generated variants, equivalent/stronger
      statements, scripts, traces, teacher material, descendants, and
      dependent retrieval records.
- [ ] Re-run H1 with a new library epoch and new sealed benchmark. Never append
      the tranche to an already opened campaign.

## Planned schedule

The realistic end-to-end campaign is four to six months. A first H0–H4 DEV
prototype is expected to take eight to ten weeks if the fragment and benchmark
work begin before GPU training.

| Weeks | Work | Exit artifact |
|---:|---|---|
| 1–2 | H0 semantics, macro schema, reference checks | reviewed profile and conformance report |
| 2–4 | H1 epoch, lineage graph, sealed benchmark | `L0` root and independent deposit |
| 3–7 | H2 symbolic portfolio and adapters | frozen `S` baseline |
| 5–8 | H3 checked macro corpus | deterministic replayed release |
| 7–10 | H4 model ladder and ablations | frozen `S+R` and candidate `H` |
| 11 | H5 one-shot evaluation | closed evidence bundle |
| 12–16+ | H6 replication, analysis, release | reproducible report and artifacts |

## Current status

- [x] Binding design and campaign gates documented.
- [x] Historical model-v3 four-goal result classified as a regression smoke,
      not campaign evidence.
- [x] Current 247-theorem library identified as the minimum candidate `L0`;
      exact H1 freeze is still pending.
- [x] A pre-H0 `surface-macro-v0` portfolio/replay bootstrap exists for
      teacher-oracle plumbing. It is deliberately narrower than the structured
      H0.3 macro protocol and does not complete H0. All its rows are
      comparison-ineligible until raw-call/resource evidence, provider
      attestations, and genuine critical-frontier detection exist.
- [ ] H0 has not passed its semantic, conformance, structured-macro, or
      evidence gates.
- [ ] No H1 benchmark is sealed and no H5 claim is available; experimental
      scaffolds or earlier policy checkpoints do not change that status.
