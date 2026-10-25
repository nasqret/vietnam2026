**Hydra practical implementation plan — 2026-09-04**

Status: implementation in progress. P0–P5 and P8–P9 are implemented and checked;
the experimental features are selectable in the website. The P5 ranker lost one
proof in its paired check and remains off by default. P6/P7 training and the P10
final comparison have not yet met their delivery criteria. Evidence and operational state are in
[the progress record](../output/hydra-implementation-2026-09-04/PROGRESS.md).
The starting point is the completed [v6 result](../output/hydra-progress-2026-09-02/RESULT.md)
and its preserved `source-v6-final` snapshot.

Deliver a prover that reuses checked mathematics, constructs cheaper proofs,
plans several steps, learns from search outcomes, and routes suitable problems
to complementary tools. Every feature gets a small working implementation;
default enablement depends on measured usefulness. A mock adapter, a generated
plan, or an external solver's success message is not a completed integration.

**Delivery rules**

- Work in small reviewable changes. Reuse the current search, evaluator, training
  stack and website; do not build a plugin framework, vector database, distributed
  agent service or new training platform.
- Preserve the original model-only mode, saved adapter, frozen execution trees,
  old results and v6 comparison baseline. Add explicit runtime, capability and
  result versions for changed behavior; do not bypass old integrity checks.
- Keep native checking and independent replay of the original theorem mandatory.
  Add no new axioms or trusted external solver results. Treat certificates,
  imported lemmas, model output and algebra proposals as inputs to be checked.
- Each package has a real positive integration example, relevant rejection tests
  and a bounded measurement. A new component need not beat the baseline to be
  delivered, but it must contribute an actual checked step in its integration
  example. Report capability, usefulness and default enablement separately.
- New adapters share time, memory and call allowances. They do not each receive
  another full search budget. Missing dependencies are reported as unavailable.
- Use [standing experiment authority](../HYDRA_EXPERIMENT_AUTHORITY.md); do not
  reintroduce per-upload or per-GPU chat approval. Record exact allocations before
  launch, retain actual exits, and stop at the limits below. No automatic retries,
  training sweeps, publication of weights, or silent checkpoint resumption.

**Ordered implementation backlog**

1. **P0 — Establish the small evaluation and experiment harness.**
   Extend `evaluate_advanced.py` and `evaluate_hybrid.py`, using their current
   source pins, terminal receipts and cleanup checks. Create a fixed development
   slice of at most eight cases; include a recurrence, lemma application,
   parameterized witness, contradiction and false near miss. Prepare a separate
   evaluation set of 12 positive theorems from at least four held-out families and
   four controls. Exclude their templates and intermediate states from training;
   do not use the gallery as unseen evaluation or give search reference scripts.
   Record proof objects/occurrences, checking time, actual component calls and
   winning-step provenance. Compare whole goal obligations, not just goal count.
   **Done:** one baseline result, reusable bounded run configuration, and a
   report that distinguishes proved, unknown, cancelled, infrastructure failure
   and any independently checked counterexample. No fabricated baseline scores.

2. **P1 — Schedule compact arithmetic and measure certificate cost.**
   In `hybrid_search.py`, route supported recurrence shapes to the existing native
   `compact_arith` tactic before expensive expansion. Extend algebra-plan ranking
   in `atom_polynomial.py` / `polynomial_chunks.py` with estimated proof cost;
   preserve repeated compound expressions and retain a fallback candidate.
   **Done:** real compact-arithmetic dispatch and replay; unsupported inputs fall
   back safely; at least one paired case shows the certificate/time effect. Run
   Fermat-7 or Sophie Germain once only when a changed plan addresses a recorded
   failure. Neither theorem is a promised outcome. Do not raise native limits.

3. **P2 — Add a small checked lemma library and retrieval.**
   Add `lemma_library.py` and `lemmas/manifest.json`; use existing native
   `use_checked` and the bounded retrieval infrastructure in
   `training/peano_policy/prompt.py` as references. Start with 12–20 inexpensive
   lemmas covering arithmetic rearrangement, cancellation, parity and divisibility.
   Store exact statements, closed certificates, dependencies, kernel identity,
   hashes and size costs. Retrieve by formula structure and symbols: at most four
   candidates per state, eight imports per proof and 32 actual import attempts
   across the entire search. Every import is rechecked. Add a versioned theorem
   resolver shared by search and independent replay: the current native `use`
   command does not read this new manifest merely because a name is allowlisted.
   Wire the same resolver and new allowlist through worker replay and finalizer.
   Use a non-executable certificate format, never pickle or imported Python code.
   Initially cap each certificate at 512 KiB, 10,000 distinct proof objects,
   50,000 structural occurrences and depth 128; cap catalog payload at 8 MiB and
   dependency depth at eight. Reject cycles before proof checking. Native whole-proof
   limits still apply. Run P2/P3 symbolically until the new provider contract in P4
   exists; the saved model provider requires its original empty theorem allowlist.
   **Done:** at least three statement-only searches use earlier checked lemmas;
   tampered certificates, open assumptions, missing dependencies and disallowed
   names fail. Exclude evaluation targets and their dependent lemmas from retrieval.
   Cache hits and imported certificates still count against their real budgets.

4. **P3 — Preserve sharing when composing native proofs.**
   In a separately versioned native-engine copy, implement and test preservation
   of local `have` / `suffices` composition through the existing checked `Cut`
   representation where its typing and scope conditions permit. Current reduction
   substitutes local proofs into their bodies. `LocalHave` / `LocalSuffices` do not
   store Cut's required conclusion: record the local target or use type-directed
   compilation with the exact context; do not guess it from displayed goals.
   Preserve the old engine. The resulting certificate must pass its unmodified
   kernel, and the new compiler must support independent full-script replay, even
   when the old surface compiler would exceed its own limits. Review binding, weakening,
   substitution and conjunction/existential branches before changing defaults.
   **Done:** a real repeated-lemma proof has lower certificate cost with the same
   theorem and axiom footprint, and the new engine passes targeted soundness and
   replay regressions. Record both distinct objects and structural occurrences.
   Do not add a trusted compressed-proof inference rule in this implementation.

5. **P4 — Add a bounded planning interface and stronger induction.**
   Add `proof_planner.py` with structured actions: select induction/generalization,
   propose an auxiliary lemma, choose a witness template, instantiate a retrieved
   lemma, and route a subgoal. Compile these into existing admitted native commands
   and the current continuation mechanism. Extend `finite_difference.py` to a
   bounded pair of auxiliary invariants and parameter generalization. All generated
   auxiliary statements remain open obligations until proved.
   Implement the experimental prompt/decoder/provider contract here, before using
   an LLM with library authority or structured output; P6 adds the larger models.
   Do not feed new prompts through the historical primitive provider or relax its
   contract checks. Deterministic plans provide the first integration path.
   Give the planner the original goal, current full goals, selected lemmas, recent
   failure reasons, remaining budget and certificate cost. Start with four planner
   calls per theorem, two proposals per call, 4,096 input / 512 output token caps,
   and at most eight commands per executed chunk, within the existing depth limit.
   A whole plan is limited to 32 commands, 16 KiB and 4,096 AST nodes. Compilation
   has a finite work counter and checks cancellation/deadline before execution;
   chunking does not permit unlimited plan generation. All tactic attempts consume
   the search's existing allowance, including rejected prefixes.
   Planner calls consume the selected model-call allowance; they are not extra
   calls beyond it. Keep a finite total generated-token allowance in the new profile
   and record it separately from calls for comparisons with the primitive decoder.
   Reject oversize input explicitly; no silent goal truncation. Namespace caches
   by the actual prompt, provider, capabilities and relevant search context.
   **Done:** real multi-step execution and one generated induction strengthening
   survive final replay; failed plans cannot leak assumptions or skip subgoals.
   Keep the current primitive model interface unchanged as a control.

6. **P5 — Export decision data and train a small branch ranker.**
   Add `export_decisions.py`; derive a new working training package from the
   deployed, attested v4 stack under
   `_deploy/hydra-retention-evaluation-recovery-execution-20260831/training/`.
   Reuse its data, training and manifest/attestation code without modifying that
   frozen source. The root `training/peano_policy/` trainer is legacy v1/v2 and
   cannot be assumed to accept the active v4 prompt contract. Export
   project-owned search states, alternative actions, native errors, successful
   continuations, proof cost and completion within the recorded budget. Include
   missing tactic targets such as `ring`, `suffices` and `exfalso`, and retain old
   primitive examples. Deduplicate and split by whole theorem/template family.
   Only checked successful continuations enter positive tactic SFT; failed actions
   and pairwise comparisons stay in the separate ranking dataset. Version the new
   planner prompt/target schema rather than mixing JSON plans into primitive data.
   Start with a small linear/logistic ranker over native structural/cost features;
   compare it with the existing deterministic score before adding another network.
   Account for every outstanding child obligation when ranking a proof branch.
   **Done:** a reproducible dataset manifest, completion/ranking targets and a
   switchable trained ranker with paired results. Resource stops are censored
   outcomes, not labels of mathematical falsity. Website submissions are excluded
   from training export unless explicitly opted in. No continuous self-training.

7. **P6 — Implement 4B/8B providers and bounded fine-tuning.**
   Add a versioned provider interface and model-specific manifests outside the
   hard-coded 1.7B path in `model_runtime.py`. Retain exact model revisions,
   tokenizer/quantization identity and adapter shape checks. Start from the existing
   `training/peano_policy/configs/qwen3_4b_pilot.toml`, but create a new config with
   the new data/output paths, one bounded pass, and resumption disabled; its old
   two-epoch, v1-data, auto-resume settings are not this experiment.
   Add 8B support to the new training package's finite model allowlist as well as
   the inference provider; do not merely change a checkpoint string. First compare
   fresh 1.7B and 4B adapters trained on identical examples and step exposure;
   retain the saved adapter as a historical control. Then implement and
   smoke-test 8B with a separate pinned base and adapter. Test the planner role
   separately from the size comparison so their effects are not conflated.
   **Done:** 4B and 8B can make real validated proposals through the new provider,
   model-specific training configurations run within declared limits, and paired
   results include cold load, warm decoding, peak memory and invalid proposals.
   A model that does not fit local limits remains remote-only/unavailable locally;
   never relax the memory guard or silently substitute another model.

8. **P7 — Use a stronger teacher to improve the local student.**
   Reuse the P4/P6 provider contract for one pinned teacher: Qwen3.5-4B as an
   alternative planner, or a formal model such as DeepSeek-Prover-V2-7B. Generate
   bounded plans or auxiliary statements for 32 training-only frontier states,
   at most 128 proposals and 512 output tokens per proposal;
   attempt them with native search, retain only independently checked successful
   continuations, then distill them into a student adapter through P5/P6.
   **Done:** one complete teacher-proposal → native-proof → dataset → student
   update → held-out comparison cycle. Lean text and informal explanations are
   never imported as Peano certificates. No requirement to train both alternative
   teachers, no 14B+ local commitment, and no unbounded reinforcement-learning loop.

   Prepare the teacher provider only after verifying its actual architecture and
   tokenizer support. Use the same finite native planning contract even when the
   teacher has a different inference backend; do not port a full Lean ecosystem.

9. **P8 — Add one common bounded adviser runner, SymPy and cvc5.**
   Extend the existing `vampire_process.py` lifecycle pattern with pinned helpers;
   retain strict subprocess authority, cancellation and owned-child cleanup. Add
   `adviser_protocol.py`, `sympy_bridge.py` and `smt_bridge.py`. A response binds
   backend/version/profile and exact input to its status, bounded suggestions,
   evidence and actual resource use. Count launches separately from cache hits;
   cache only within matching input, backend and semantic contexts.
   SymPy: exact integer-polynomial factorization/reduction, at most four variables,
   degree eight and 256 intermediate monomials. Return witness expressions or
   identities reconstructible with native rewriting and arithmetic. Exclude floats,
   unrestricted simplification and unproved cancellation side conditions.
   cvc5: affine arithmetic after native introductions, explicit nonnegative natural
   variables, bounded witness templates and equality consequences supported by
   reconstructible linear combinations. A sampled assignment is not a universal
   witness. Reject nonlinear/quantified fragments and unsupported proof steps.
   **Done:** each real backend contributes to a native-replayed integration proof;
   malformed evidence, negative witnesses, scope errors, timeout and cancellation
   fail safely. `unsat` alone never closes a goal. Z3 is an alternative implementation
   of the same SMT contract, not a mandatory duplicate solver in this first pass.

10. **P9 — Add bounded e-graph rewriting and E.**
    Add `egraph_bridge.py` with a small pinned `egg` helper over binder-free
    arithmetic terms. Use only instantiated, natively justified semiring rules;
    cap it at 4,096 graph nodes and eight iterations. Extract named rewrite and
    congruence steps, choosing an estimate of native proof cost rather than just
    expression length. Reject unproved side conditions and untranslatable steps.
    Add `e_bridge.py` using the existing scoped FOF export and an E-specific proof
    dependency parser. Reconstruct bounded equality/contradiction fragments through
    native tactics. Supply only explicitly checked lemmas available to this state;
    do not silently add induction or launch E's own parallel portfolio.
    **Done:** both real adapters have checked positive examples and failure/cleanup
    tests. E and egg ship selectable and initially disabled by default; measured
    usefulness determines promotion. Shared limits apply even when all are selected.

11. **P10 — Integrate the website and run the final comparison.**
    Extend `server.py`, `worker.py`, `app.js`, `index.html`, existing tests and
    `publish_showcase.py`. Add one compact Experimental panel for model/planner,
    lemma retrieval and available advisers; keep existing simple controls and modes.
    Show actual components used, retrieved lemmas, planner actions, branch rankings,
    certificate size and separately labelled counterexample diagnostics. Preserve
    custom tests, manual replay, download, cancellation and honest unavailable states.
    **Done:** an end-to-end custom theorem uses the new path, cancellation releases
    the owned computation, and new gallery entries come only from independently
    replayed discoveries with exact provenance. Publish paired gains and losses;
    do not advertise component calls as component-created proofs.

Implementation order: **P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10**.
After P2, adviser work P8/P9 can run alongside planning/training when it does not
compete for the same files or local computation. Do not wait until P10 to expose
basic diagnostics or run a package's integration checks. Stop each package at its
specified first working version; optimization follows evidence, not speculation.

**Experiment ceilings for this implementation campaign**

These are maximum allocations, not instructions to consume them. Prepare an exact
smaller run configuration for each experiment. A limit or infrastructure failure
ends that attempt; a revised attempt needs a concrete diagnosis and a new record.

| Work | Initial ceiling and stop rule |
| --- | --- |
| Local diagnostics | One active computation; at most eight cases and 30 minutes per package. One documented follow-up only to resolve a concrete failure, not to fish for a success. |
| External advisers in the new Deep profile | Twelve total external requests, one child at a time and 60 seconds cumulative external wall time across Vampire, SymPy, cvc5, egg and E. Retain 300-second search / 330-second worker ceilings and existing tactic/state limits. |
| Each external process | SymPy/egg: 1 CPU second / 2 wall seconds. ATP/SMT: 6 CPU seconds / 8 wall seconds. Start with the existing 384 MiB sampled stop, 512 MiB parent ceiling, 64 KiB input and 256 KiB output caps. Refuse dispatch without enough time for the child and completion/replay reserve. Sampled memory checks can overshoot. |
| Local model | One loaded model; 4-bit first. Keep the existing 8 GiB worker ceiling on the 16 GiB M1 Pro. Run a short memory/latency smoke before a comparison. A memory failure is a result, not authorization to increase the cap. |
| Training/teacher pilots | One GH200 at a time; no multi-GPU job. Start with a fixed subset of at most 4,096 training rows, including retention data, and one pass. Reserve at most six GH200-hours for the whole first campaign, including probes, evaluation and distillation; individual jobs at most two hours. Count failed allocations and teacher time too. |
| Final evaluation | At most four hours local wall time total, split into bounded batches accepted by the existing evaluator. No implicit reruns or enlargement. Incomplete arms stay incomplete. |

Run the 1.7B/4B pilots before allocating 8B training. Use a short throughput probe
to choose an identical subset/step budget that fits both models; do not compare a
completed small-model run with an unfinished large-model run as a fair size trial.
An 8B training pilot follows its provider smoke and remaining campaign budget.
Implementing that provider is still required if training is deferred; report the
unrun training task explicitly rather than marking P6 complete. A teacher trial
uses only the remaining declared allowance. Do not expand the allowance silently.

For the final model comparison, hold search, library, arithmetic tools and input
information constant: symbolic baseline; saved 1.7B; fresh 1.7B; fresh 4B. Score
the 12 positive cases separately from controls. Evaluate 8B or a teacher-distilled
student on a predeclared smaller paired slice within the same total ceiling.
Use a fixed proposal/native-work comparison and a separately labelled fixed-wall
comparison on that slice; neither a model-call count nor token accuracy alone is
the success metric. Report family holdout relative to our data, not unknowable
absence from a pretrained model's training corpus. Once evaluation cases inform
changes, they become development cases; new generalization claims need a new split.

Promote a component to defaults only after native safety checks pass and it adds
checked proofs or a material cost reduction on the declared comparison without
unexplained losses. Otherwise keep its completed implementation selectable with
the observed limitation. Success for the project is useful checked proofs within
the same resource budget, not the number of tools installed.

The first implementation change was **P0 + P1**: a small reproducible baseline,
actual `compact_arith` scheduling, and certificate-cost telemetry. It needs no new
model download or GPU allocation. Current completion claims and live allocations
are recorded in the progress record above, with preserved per-attempt evidence.
