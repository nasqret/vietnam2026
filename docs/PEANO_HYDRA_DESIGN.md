# Peano Hydra — binding design

**Status:** binding campaign architecture; H0 semantic and functional core
completed 2026-08-04, H1 epoch/benchmark freeze still open

**Implementation plan:** [`PLAN/11_peano_hydra.md`](../PLAN/11_peano_hydra.md)

**Parent architecture:** [`docs/PEANO_LAB_DESIGN.md`](PEANO_LAB_DESIGN.md)

Peano Hydra is a falsifiable experiment in neuro-symbolic theorem proving for
the Peano Lab object language. It asks whether an LLM can make a
proof-producing symbolic prover better under matched resources. It is not a
license to weaken Peano Lab's trust boundary, and it is not a claim that full
Heyting arithmetic is decidable.

This document fixes the experiment before implementation. Normative words
(`MUST`, `MUST NOT`, `SHALL`, `SHOULD`) are deliberate. If implementation
experience exposes a defect, change this document visibly before running the
sealed evaluation; do not silently reinterpret it after seeing results.

## 1. Research question and claim boundary

The primary question is:

> At equal inference resources, does an LLM-guided system solve more sealed
> Peano Lab problems than the strongest frozen non-generative symbolic system,
> while every positive answer remains independently kernel checked?

There are three distinct possible products:

1. a **sound theorem prover**, which may answer “unknown”;
2. a **decision procedure for a precisely specified fragment**, which must
   justify both positive and negative answers; and
3. an **experimental search system**, whose relative performance is an
   empirical claim under a declared budget.

Standard first-order Heyting arithmetic has undecidable theoremhood. Peano
Hydra therefore MUST NOT be described as a decider for “Heyting arithmetic” or
“PA” in general. A decidability claim is permitted only for an exact restricted
grammar and semantics frozen at H0, with an implemented terminating procedure
and independently checkable negative evidence or agreement with a separately
implemented trusted reference decision procedure. Without that evidence the
system is called a sound theorem prover, even if the chosen benchmark happens
to be finite.

“Top performing,” “LLM advantage,” and similar claims are also reserved for
the preregistered H5 comparison. Development-set demonstrations, teacher
solutions, and the historical four-goal policy smoke cannot establish them.

## 2. Non-negotiable laws

### 2.1 Kernel law

Only `peano_lab/kernel/checker.py` may admit a positive theorem. Every reported
QED MUST be replayed from an empty or explicitly declared context against the
**original stated formula**, not a tactic-rewritten surrogate. The certificate
MUST be self-contained according to the Peano Lab design; library names,
solver status strings, model confidence, and hashes are provenance, never
proof authority.

The tactic engine, native search, retrievers, learned rankers, Qwen, Codex,
Vampire, E, SMT solvers, translators, proof parsers, and certificate
reconstructors are all untrusted. One false kernel acceptance or one scored
positive that cannot be reproduced by the independent replay path invalidates
the run and blocks advancement. A rejected proposal is an ordinary search
failure, not a theorem.

The kernel MUST retain the import and size disciplines in
`PEANO_LAB_DESIGN.md`. Hydra MUST NOT add a trusted solver rule, a theorem
oracle, a “Vampire proved it” constructor, or a second finalizer.

### 2.2 Fragment law

H0 MUST publish one machine-readable language profile containing:

- the exact term and formula grammar;
- binding, substitution, and alpha-equivalence conventions;
- intuitionistic proof rules and the permitted arithmetic axioms/schemata;
- whether induction is unrestricted, syntactically bounded, or absent;
- the accepted input normal forms and every validity-preserving translation;
- resource bounds that are part of the decision claim, if any; and
- the semantics and evidence format for both `proved` and `not_theorem`.

The profile hash is part of every dataset row, solver run, model prompt,
certificate record, and result table. A formula outside the profile may be
attempted by the sound prover but MUST NOT be counted in a fragment-decision
result. A timeout or exhausted search is `unknown`, never negative evidence.

The historical H0.1a profile is
`training/peano_hydra/semantic-profile-v1.json`. Its identity is format
`peano-hydra-semantic-profile`, version 1, ID
`peano-lab-ha-intuitionistic-v1`, and semantic SHA-256
`058b1644b066967919dae092e5e562b8845e4dd8415fff31d7cd209d51bc9e43`.
It remains immutable and keeps its self-labeled draft evidence block.

H0.1b registers the active successor
`training/peano_hydra/semantic-profile-v2.json`, ID
`peano-lab-ha-intuitionistic-v2`, semantic SHA-256
`4f2713e6a21e6261bbefe5991ef545e6356807e7042c6b2c7c07183e142c3b4b`.
Its object language, logic, arithmetic axioms, induction rule, and no-decision
claim are unchanged. It replaces only the draft evidence block with an exact
content reference to `training/peano_hydra/result-schema-v1.json`, ID
`peano-hydra-result-v1`, semantic SHA-256
`cf1caf1c867ddfbe3c247e42a18b730ea6790269718170a51f9733d5a7a36b26`.
The strict version registry is `training/peano_hydra/profile.py`; historical
canonicalization is implemented by the frozen compatibility module
`training/peano_hydra/profile_theorem_v1.py`, not by whichever browser parser
and limits happen to be current. Semantic digests cover compact sorted-key
UTF-8 JSON, excluding display indentation and the final line feed.

Versions 1 and 2 admit the same closed, structurally well-scoped canonical
Peano formulas. Their `operational_admission` block freezes the complete
pre-parser boundary:
nonempty one-line input with no outer whitespace, Unicode-code-point length
at most 8,192, decimal numerals at most 256, explicit numeral-token boundaries,
forbidden unsafe Unicode categories, and no `#` target syntax. These are
transport/construction safeguards with `decision_claim = false`; the profile
still has no decision-resource bound or negative theoremhood claim.
It freezes de Bruijn binding, capture-avoiding substitution, the complete
intuitionistic kernel calculus, PA1--PA6, and unrestricted formula induction.
It forbids the classical checker and explicit de Bruijn target syntax,
registers no external-solver translation or decidable subfragment, and
supports only `proved` and `unknown`. A `not_theorem` publication is forbidden.

Result schema v1 has exact disjoint field sets and forbids additions. A
`proved` constructor receives an actual kernel `Formula` and `Proof`, checks it
against the original theorem, derives bounded certificate metrics and the
kernel identity, and retains all non-self-referential replay/run hash
preimages. `unknown` carries a bounded reason and run evidence but no
certificate, kernel-acceptance bit, solver-status authority, negative witness,
or negative theoremhood claim. Domain-separated compact JSON defines every
hash preimage. Profile v1's draft is historical; only profile v2 records may
claim this exact `peano-hydra-result` v1 conformance.

### 2.3 Library-epoch law

Hydra does not evaluate against a moving theorem library. H1 freezes an
ordered epoch `L0`, initially the complete independently checked public
catalog available at campaign start (at least the current 384-theorem
entries). Its content root MUST commit to, for every entry:

- stable name and canonical statement;
- ordered direct dependencies;
- authored source or proof-script hash;
- independently checked certificate hash;
- node count and maximum depth; and
- declaration order and logic/profile identity.

Training may use eligible material from `L0`; the final benchmark may not.
New mathematics belongs to `L1`, `L2`, and so on. It cannot enter the active
campaign's prompts, retrieval index, imports, training corpus, or headline
test. Starting a new library epoch requires sealing a new benchmark before
examining outcomes. The current public library is a capability and training
resource, not a hidden test set.

### 2.4 Sealed-test law

The unit of separation is a mathematical **lineage**, not a row or filename.
Before training-row expansion, all statements and artifacts receive stable
lineage IDs and are partitioned by connected components of the declared
dependency, generation, equivalence, and authorship graph.

For every sealed target, training and run-time retrieval/import MUST exclude:

- the target and alpha/notation-normalized equivalents;
- stronger or equivalent reformulations and generated variants;
- its authored proof, certificate, tactic trace, prompt, and generator seed;
- members of the same problem family or shared derivation lineage;
- target descendants and capstones that reveal the result; and
- any retrieval entry whose proof depends on a masked node.

Splitting occurs before state/action rows, negative samples, paraphrases, or
augmentations are generated. The mask compiler and its output are hashed.
The evaluation owner alone holds the final target payload until H5. Search
logs from the final run never flow back into the active model or heuristics.

### 2.5 Evidence law

Every number in a result table MUST be reproducible from a closed evidence
bundle. The bundle binds at least:

- Git source and dirty-state assertion;
- kernel, language profile, and logic-mode identities;
- library epoch and lineage mask;
- training data, benchmark, generators, and exact split manifests;
- external solver binaries, versions, options, translators, and proof parsers;
- base model revision, ordered weight-shard hashes, tokenizer, adapters,
  checkpoints, prompts, and decoding parameters;
- search algorithm, budgets, seeds, process topology, and stop conditions;
- CPU/GPU model, software environment, wall time, CPU instructions where
  available, peak memory, GPU energy, and monetary accounting convention;
- complete raw model calls, extracted actions, solver calls, executed edges,
  certificates, failures, and replay results; and
- scripts that rebuild the tables from those immutable records.

Missing evidence narrows the claim; it is never filled by inference. The
historical four-goal Qwen smoke remains a regression observation only: trained
3/4 versus a revision/configuration-pinned pretrained comparison at `k=1`,
with three shallow checked scripts and the induction goal unsolved. It is not
a teacher-oracle result, statistical benchmark, broad PA capability result, or
causal LLM advantage result.

## 3. Trust and system architecture

```text
formula + library epoch + budget
                |
                v
     deterministic symbolic closure
       | solved                 | stalled at critical frontier
       v                        v
 certificate             macro proposal policy
       |               (Qwen; Codex on DEV only)
       |                        |
       |       +----------------+----------------+
       |       |                |                |
       |   native search   retriever/ranker  Vampire/E/SMT
       |       |                |            hints only
       +-------+----------------+----------------+
                               |
                    ordinary Peano commands
                               |
                    transactional proof engine
                               |
                    independent original-goal
                         kernel replay
                               |
                    checked QED or rejection
```

The **critical frontier** is the first deterministic fixed point at which
cheap symbolic closure cannot choose a uniquely justified continuation within
its bound. The LLM is called only there. It proposes sparse, open-ended
decisions—witnesses, cuts, induction motives, case splits, premise bundles,
and solver strategies—not every rewrite or resolution clause. After a valid
proposal, deterministic closure resumes to the next QED or frontier.

This division is both an efficiency hypothesis and an ablation target. A
cheap learned clause ranker or retriever belongs in the high-frequency inner
loop; an autoregressive model does not unless matched-compute evidence says it
helps.

### 3.1 Roles are untrusted and separable

- **Peano kernel:** sole positive theorem authority.
- **Native symbolic portfolio:** normalization, focused intuitionistic search,
  connection/tableau-style search, rewriting, arithmetic closure, and bounded
  enumeration; it emits ordinary certificates.
- **Retriever:** selects eligible `name : statement` records under the active
  lineage mask. It never imports a masked theorem.
- **Clause/state ranker:** cheap non-generative scoring for the symbolic inner
  loop. Its scores confer no validity.
- **Qwen policy/value models:** student components that propose macro actions
  or rank frontier states.
- **Codex:** optional teacher, formalizer, and dataset generator on TRAIN/DEV.
  It may measure action-interface headroom and generate tagged candidates,
  all of which require replay. It MUST NOT see or act on the sealed final set.
- **Vampire, E, and SMT solvers:** optional hint or side-condition engines.
  They are classical systems, not intuitionistic HA kernels. Their outputs
  must be reconstructed into Peano certificates, and their translations must
  be restricted to a proved validity-preserving class. A raw `SZS Theorem`,
  unsat result, or translated proof is never scored directly.

The symbolic baseline MUST be useful without any LLM or teacher service. Every
component can be disabled independently from a frozen configuration.

### 3.2 Macro action DSL

The Hydra action format is a typed transport protocol for existing proof
operations, not a new proof language. Version 1 contains only:

```text
Use(name, specializations*)
Cut(kind = have | suffices, name, formula)
Witness(term)
Induct(variable, motive)
Rewrite(source, direction, location)
Split(kind)
Dispatch(solver, premises, bounds)
```

Retrieval is an observation/selection operation, not a proof action. Each
macro MUST compile deterministically to documented public Peano Lab commands
and/or a bounded untrusted solver call. The resulting public commands execute
transactionally: a failing macro leaves the proof state and history unchanged.
`Dispatch` may return clauses, candidate instantiations, rewrite hints, or a
reconstructable derivation; it cannot close a goal by status alone. There is
no macro-only certificate constructor and no macro-specific kernel rule.

Action serialization is canonical and versioned. The trace records the state
before proposal, allowed actions, raw proposal, parse result, compiled public
commands, intermediate states, solver transcript, resource use, and final
kernel outcome.

The frozen H0.3 implementation is
`training/peano_hydra/macro-protocol-v1.json`, ID
`peano-hydra-macro-v1`, semantic SHA-256
`b5fef1ea1b85251ab7f0b8c111cb37e789f96f20771665b4f0dc8b746400552c`.
`training/peano_hydra/macros.py` provides exact typed parsing/serialization and
deterministic compilation; `training/peano_hydra/macro_runner.py` owns the
transactional untrusted executor and replay-aware trace validator.

`Dispatch` MUST NOT accept an in-process callback. Its adapter registration is
a reconstructed, content-addressed executable plus canonical configuration.
The host prepares one exact canonical child-call preimage, executes a copied
artifact without a shell in a fresh process, and retains the configuration,
call hash, raw bounded stdout, and host observations. Solver status has no
authority; at least one reconstructed command must pass the same capability-
checked public surface. Malformed or over-limit output still produces bounded
canonical rejection evidence and exact rollback.

Resource descriptions MUST distinguish enforcement from reporting.
`steps_used` is untrusted adapter self-reporting constrained between the number
of returned commands and the requested maximum; it is not a host instruction
counter or campaign usage metric. Linux non-root `RLIMIT_AS`/`RLIMIT_DATA`
execution is the campaign-eligible hard-memory mode. Darwin leader-RSS
sampling is diagnostic and campaign-ineligible, and its observed maximum is
not called an exact peak. Provider/host attestation remains required before a
later campaign may consume any host-eligibility claim.

The H0 bootstrap intentionally precedes that structured version-1 protocol.
Its compatibility action, `MacroAction(line)`, carries exactly one canonical
public surface line whose head is restricted to explicit proof-structuring
operations (`have`, `suffices`, `exists`, `induction`, `cases`, `apply`,
`rewrite`, and their small structural companions). It rejects automation,
tactical wrappers, session commands, and multiline programs. This lets us test
portfolio quotas, critical-state gating, transactional execution, provenance,
and fresh kernel replay without inventing a second interpreter. It is
`surface-macro-v0`; it did not constitute H0.3. The structured schema above
remains the gate before model training or a campaign benchmark.

The bootstrap implementation lives outside the trusted prover in
`training/peano_hydra/`. A portfolio is only an untrusted
`CandidatePolicy`: fixed symbolic heads, recorded Qwen/Codex transcripts, or a
live identified provider all return public tactic lines under fixed quotas and
one exact capability identity. Recorded teacher policies require a complete
kernel-checked QED trace by default; partial traces must be admitted explicitly
and remain labeled search evidence. `training/peano_policy/search.py` replays each
edge through the real surface, then `training/peano_hydra/runner.py` performs a
second retained-trace replay from the original theorem. Search and replay must
agree on the canonical theorem, physical commands, logic/capabilities, and
certificate node count. Provider failure may leave a proof sound if another
head succeeds, but marks the run degraded and ineligible for a matched
comparison. Missing identity, environment, proposal ledger, or replay
agreement blocks publication.

Policy, runner, and teacher-pilot record schemas version 3 carry the active
profile-v2/result-schema identity directly in environments, head identities,
proposal and recorded-state rows, run records, source artifacts, and result
tables. Replay identifiers also bind it. A legacy model prompt that does not
expose this identity is rejected before generation; Hydra needs a future
profile-aware prompt contract before admitting such a model head. Historical
pilot v1 is preserved as pre-profile evidence, pilot v2 is the profile-v1
regression, and pilot v3 is the profile-v2/result-schema-bound regression.
These bindings do not promote `surface-macro-v0` to the structured H0.3
protocol or make any row comparison-eligible. The pilot v3 run records also
say explicitly that they are not complete `peano-hydra-result` v1 evidence
bundles: certificate hashes/depths, kernel identity, and closed run/replay
evidence hashes are deliberately absent from that historical pilot. The
separate H0 result-schema and retained conformance artifacts supply those
fields; pilot v3 itself remains comparison-ineligible.

Every `surface-macro-v0` result is explicitly **ineligible for campaign
comparison**, even when execution is complete and non-degraded. The bootstrap
retains extracted tactic lines, not the complete raw decoder response,
token/latency/resource record, or a versioned provider attestation. Static
exact-state allowlists also test routing, not symbolic fixed-point detection.
Those omissions are acceptable for plumbing and must be closed before a real
Qwen/Codex row can count as H1–H5 evidence.

## 4. Data and benchmark protocol

### 4.1 Dataset classes

Hydra distinguishes:

- **authored checked trajectories** from the public library;
- **symbolic discoveries** found by frozen solvers;
- **teacher proposals** generated by Codex or another model;
- **student rollouts** from Qwen checkpoints;
- **failed/partial searches**, retained only as labeled search evidence; and
- **sealed evaluation targets**, which never become training examples in the
  active epoch.

Only complete original-goal kernel QEDs may become positive policy examples.
Failed, truncated, merely type-correct, solver-asserted, or partial paths MUST
NOT be positive labels. Duplicate and near-duplicate accounting is by canonical
state/action and lineage, not textual spelling. Every row carries its source
class, theorem lineage, library prefix, capability profile, and replay root.

### 4.2 Quadratic-reciprocity growth rule

Quadratic reciprocity is a valuable future stress domain, but it is not in the
current 384-theorem library. Any new definitions, residue theory, Legendre-like
encoding, reciprocity lemmas, or capstone proofs added after `L0` belong to a
later library epoch. They MUST NOT silently enlarge the active Hydra campaign.

If quadratic reciprocity or a reformulation becomes an evaluation target, the
entire development lineage is masked: definitions introduced solely for that
route, intermediate lemmas, generated variants, authored scripts and traces,
equivalent statements, stronger downstream capstones, and retrieval entries
whose certificates depend on them. Names and string hashes are insufficient;
the split uses declared lineage IDs and dependency components.

For a chronological “future theorem” study, statements are deposited and
sealed before their proofs or scripts enter any public/training library.
Teacher-generated formalizations and proof sketches are tagged at creation and
excluded whenever their lineage intersects the final target.

### 4.3 Difficulty and negative cases

The benchmark is stratified before outcomes by quantifier/connective depth,
term size, witness branching, induction requirement, cut requirement, premise
composition novelty, and symbolic-baseline difficulty. If H0 supports certified
negative decisions, non-theorems form a separate stratum and are scored for
both correctness and resource use. Otherwise all unsolved cases remain
`unknown` and the primary metric is positive theorem solving.

## 5. Matched-compute evaluation

The final systems are:

- `S`: strongest frozen purely symbolic portfolio;
- `S+R`: strongest frozen non-generative learned system (retrieval and/or
  clause/state ranking); and
- `H`: full Hydra with the generative LLM available at critical frontiers.

All systems receive the same formula, eligible library view, hardware class,
wall-clock envelope, and evidence requirements. Primary budgets are 1, 10, 60,
and 300 seconds per problem. The campaign also reports matched CPU
instructions/activations where meaningful, GPU/CPU energy, peak memory, and
monetary cost. Training cost is reported separately and as an amortized
break-even curve; it is never hidden inside “free” inference.

The primary outcome is kernel-checked solved fraction versus resource. Report
PAR-2/time-to-proof survival, proof nodes/depth, invalid-action rate,
solver/model calls, hybrid-only and baseline-only solves, and negative-decision
errors where applicable. Use paired stratified bootstrap intervals and an
exact paired test with the preregistered multiplicity correction.

A headline LLM advantage requires, at two adjacent time budgets:

- `H - max(S, S+R) >= 3` percentage points;
- the lower bound of the paired stratified 95% interval is above zero;
- the corrected exact paired test rejects equality;
- all counted proofs replay independently; and
- no soundness or certified-negative regression.

If this gate fails, the conclusion is: **no demonstrated LLM advantage under
these budgets**. The benchmark is not reopened, tuned, or redefined; `pass@k`,
extra sampling, or teacher intervention cannot replace the registered metric.

## 6. H0–H6 campaign gates

### H0 — Semantic and functional core

Freeze the exact fragment profile, decision-claim boundary, macro protocol,
reference semantics, and proof-producing symbolic core.

Acceptance:

- the H0 candidate-`L0` catalog cold-replays twice with identical roots and 100% kernel
  acceptance;
- at least 1,000 semantic-conformance formulas are tested, including at least
  400 theorems and, for any decision claim, at least 400 certified
  non-theorems;
- an independently implemented reference agrees on every in-scope result;
- certificate, substitution, translation, and negative-evidence mutations are
  rejected; and
- kernel import, original-goal, and transactional-state laws remain green.

Any false acceptance, unresolved fragment semantics, or unsupported negative
claim is a no-go. If negative evidence is unavailable, pivot explicitly to a
sound semi-decision theorem prover.

H0 completed on 2026-08-04. The retained evidence is
`artifacts/peano-hydra/h0-validation-v2.json`, SHA-256
`55c60502b2229f4420bd4557058842bebb582f491739e82a6dae06de5b803fdb`,
produced from clean commit
`26c2503b36c6884bfbfa6dabd1494bbda49d8926`. It records two identical
100%-green fresh-process replays of the 384-entry candidate catalog at root
`fae19fad55c416ae7b695107390c1c733d6740fe63d10cf0efed127f5801b9d2`;
1,024 distinct positives and 1,024 wrong-target certificate rejections; ten
artifact mutations plus three profile/schema boundary mutations; agreement
with the exactly registered independent Lean reference on all 2,058 artifact
cases; and green kernel-import, original-goal, and transactional-state
regressions. It also retains the seven typed macro fixtures, deterministic
accepted/rollback traces, exact Dispatch preimages with fresh original-goal
kernel replay, and the 110-test macro transcript required by H0.3. Rust and
WASM out-of-envelope cases are pre-registered diagnostic resource
classifications, not semantic disagreements. Dispatch resource observations
and pytest duration are not stable semantic identities. Report v1 is retained
only as provisional H0.1/H0.2 evidence and is superseded for complete-H0 use.

This closes the semantic and functional core only. The 384-entry catalog is an
H0 candidate-L0 replay corpus, not H1's frozen library epoch. H1 still must
seal exact theorem metadata, genealogy, dependency masks, benchmark partitions,
and the interface-headroom experiment before training or comparison claims.

### H1 — Frozen epoch, benchmark, and interface headroom

Freeze `L0`, TRAIN/DEV, and a separately held sealed final set. The final set
contains at least 1,000 targets, including at least 200 human-authored or
chronologically future-library statements and, if supported, at least 300
certified non-theorems. Run the symbolic baseline at every registered budget.

On DEV only, a strong teacher may try the macro interface at symbolic critical
frontiers. Advance if there is zero contamination, the 60-second symbolic
baseline leaves at least 100 targets or ten percentage points unsolved, and
the macro teacher closes at least 20% of that frontier. If the symbolic system
already solves at least 99.5% at 60 seconds, pivot to latency/proof-size rather
than manufacture a solve-rate problem. If teacher closure is below 10%, fix
the action interface before training. A teacher success demonstrates only
interface/oracle headroom; it is not evidence about Qwen or final performance.

### H2 — Strong symbolic portfolio

Implement and tune, on DEV only, native normalization/rewrite/arithmetic
closure, focused intuitionistic or connection search, bounded enumeration,
and validity-controlled external-solver adapters. Every counted positive and
negative result must replay through its independent authority. The frozen
portfolio must weakly dominate each component on DEV solved-versus-resource
AUC and becomes `S` before model evaluation.

### H3 — Checked macro curriculum

Build at least 100,000 unique positive macro transitions from at least 20,000
complete kernel-checked QED roots. Cover every public macro head, with at least
2,000 examples for each critical open-ended head. Each eligible `L0` theorem
must have at least eight independent positive-use lineages or be explicitly
marked ineligible/held out. Two clean builds must be byte-identical; every
positive root must replay; contamination must be zero; and tokenizer audits
must reject, not silently truncate, over-length examples.

### H4 — Model ladder and ablations

Evaluate, in order, `S`, `S+BM25`, learned retrieval, cheap clause/state
ranking, pretrained Qwen, 1.7–3B Qwen SFT, SFT plus value-guided
best-first/PUCT search, and then checked expert iteration. Also run shuffled
scores, random-valid actions, no retrieval, no value, no clause ranker, no
symbolic closure, and LLM-only controls.

Advance components only when:

- learned retrieval reaches recall@8 of at least 75% and improves at least ten
  points over BM25, or matches recall at materially lower declared cost;
- the clause ranker has a positive lower 95% paired solve-difference bound at
  equal instructions, or saves at least 20% activations with under one point
  solve loss;
- SFT beats the identical pretrained system by at least five DEV points,
  solves at least 25 registered frontier cases, and has a positive lower 95%
  paired interval;
- value search improves solved-versus-resource AUC by at least 5% relative;
  and
- expert iteration consumes only checked QEDs, includes clean-rebuild versus
  continual controls, and stops after two rounds below one point improvement.

Do not scale the generative model if cheap guidance captures the gain. Stop or
redesign after two preregistered SFT attempts fail their gate.

### H5 — One-shot sealed comparison

An independent evaluation owner unlocks the final set once, under frozen
source, `L0`, solver/model checkpoints, search configs, budgets, and seeds.
Compare `S`, `S+R`, and `H` under the matched-compute protocol in section 5.
No tuning or training follows unlock. Publish all successes, failures, raw
transcripts, replay results, and resource accounting. Apply the exact claim
rule in section 5 without exceptions.

### H6 — Reproducible release

Release source, containers and SBOM, data/model cards, the `L0` manifest,
benchmark construction and public non-secret split material, lineage masks,
solver adapters, configs, checkpoints where licensing permits, certificates,
replay tools, raw evaluation records, tables, dashboard, Jupyter Book, and
Obsidian notes. A fresh machine must reproduce certificate judgments and
paper tables. Full tests, strict documentation builds, link/vault checks,
license checks, and an independent leakage/compute/claim review must pass.

## 7. Change control

All changes that affect grammar, trust, library visibility, lineage,
benchmark membership, solver translations, model inputs, search resources, or
metrics require a new versioned protocol record. Before H5 they require a
documented rationale and complete DEV rerun. After final-set unlock they end
the campaign; they do not patch the result.

Quadratic-reciprocity growth, additional public theorems, a larger Qwen model,
and a new external solver are legitimate next-epoch experiments. They are not
retroactive improvements to a frozen comparison.

## 8. Research lineage

The architecture borrows the useful separation seen in proof-producing
neuro-symbolic systems while keeping Peano Lab's independent kernel as the
authority. Relevant primary references include
[AlphaGeometry](https://www.nature.com/articles/s41586-023-06747-5),
[AlphaProof](https://www.nature.com/articles/s41586-025-09833-y),
[Thor](https://proceedings.neurips.cc/paper_files/paper/2022/hash/377c25312668e48f2e531e2f2c422483-Abstract-Conference.html),
[Efficient Neural Clause-Selection Reinforcement](https://arxiv.org/abs/2503.07792),
which is evaluated inside Vampire, and the
[Intuitionistic Logic Theorem Proving library](https://www.iltp.de/).
These systems motivate hypotheses; none supplies evidence for Peano Hydra's
headline claim. That evidence can only come from H5.
