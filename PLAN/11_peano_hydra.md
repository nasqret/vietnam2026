# Peano Hydra — L2/L3 campaign plan

## Objective

Build a living, sound arithmetic workshop whose only object language is the
curated Peano Lab language. The permanent product is a growing, reviewed
library of elementary number theory with exact dependencies, readable proofs,
efficient certificates, and documentation generated from the same checked
artifacts. Peano Lab remains the interactive proof-building environment.

On top of that foundation, build and evaluate a focused neuro-symbolic prover.
Native proof search and Vampire perform most routine symbolic work; small
LoRA-post-trained Qwen models are called sparsely for formalization, retrieval,
macro proposals, frontier ranking, and explanation. Every such component is
untrusted. A theorem enters the library only after independent kernel replay
against the exact original Peano Lab statement.

The research experiment is successful only if it survives the frozen,
matched-compute, one-shot comparison in H5. The living library and authoring
assistant remain useful even if that experiment finds no demonstrated LLM
advantage. A working demo, teacher-authored proof, or larger raw `pass@k` is
not a substitute for either checked library quality or experimental evidence.

The binding architecture and claim rules are in
[`docs/PEANO_HYDRA_DESIGN.md`](../docs/PEANO_HYDRA_DESIGN.md). This module is
numbered 11 because [`PLAN/10_arithmetic_library.md`](10_arithmetic_library.md)
already owns module 10.

## Program scope and permanent tracks

### One object language, two explicit logic modes

- Peano Lab syntax, defined notation, tactics, and certificates are the only
  user-facing formal language. TPTP/Vampire, SMT, Lean, and model wire formats
  are internal plumbing and never become library source or proof authority.
- The default mode is the frozen constructive profile: intuitionistic logic,
  PA1--PA6, and unrestricted formula induction.
- Classical arithmetic is a separately versioned and visibly labeled
  `PA+DNE` profile. The surface may offer `A \/ ~A` as a derived classical
  theorem/tactic; the kernel already uses DNE, so no second equivalent axiom
  is added casually. Constructive theorems may be used classically; a
  classical theorem may never enter a constructive proof.
- Defined predicates and readable notation remain conservative, receipt-
  carrying expansions into the primitive Peano Lab language.

### Parallel tracks

- **L — Living library:** reviewed statements, precise direct dependencies,
  readable scripts, best-known certificates, proof metrics, source prose, and
  generated Book/vault/Explorer pages. Library `HEAD` may grow continuously.
- **A — Authoring assistant:** a revisioned manuscript workspace that turns
  accepted prose spans into checked Peano artifacts, reports ambiguity and
  evidenced mistakes, and exports reviewable patches; it never writes the
  public library silently.
- **V — Symbolic/Vampire:** deterministic native closure first, then bounded
  Vampire hints or reconstructable derivations through `Dispatch` and ordinary
  Peano tactics. A solver status has no authority.
- **M — Qwen LoRA:** small, token-efficient task adapters for formalization,
  retrieval, macro policy, value/frontier ranking, and critique. Model output
  may also draft structural explanations from checked artifacts. It is always
  a proposal, never a certificate, truth label, or human-review event.
- **K — Verified fast kernel:** readable Python remains authoritative while
  native/WASM Rust is a shadow. Rust authority requires a source-to-Lean
  refinement result and a separate reviewed amendment; differential agreement
  alone is not such a proof. Detailed work stays in
  [`PLAN/12_peano_kernel_acceleration.md`](12_peano_kernel_acceleration.md).
- **H — Sealed research campaign:** H0--H6 freeze epochs, lineages, systems,
  budgets, and evidence for the Vampire/Qwen comparison.

Two operational modes MUST remain physically and semantically distinct:
`authoring-live` follows the newest reviewed library epoch and makes no causal
performance claim; `research-eval` sees exactly one content-addressed epoch,
mask, benchmark, model, and solver configuration. Growth in the first cannot
leak into the second.

### Checked authoring lifecycle

Every source unit is retained verbatim and classified as `claim`, `definition`,
`proof_step`, `exposition`, or `question`. Formal objects move only through
explicit states such as `prose_only`, `ambiguous`, `formalized_unproved`,
`proved`, `reviewed`, and `admitted`. A formalization candidate binds the
source span/hash, document revision, readable and expanded formulas, binders,
assumptions, logic profile, library epoch, definition receipts, alternatives,
and provenance. A theorem proposal additionally binds lineage, exact direct
dependencies, script/macro roots, certificate and replay receipts, proof
metrics, solver/model transcripts, documentation outputs, and human review.

Diagnostics identify their authority: parser, definition expander, library
graph, bounded evaluator, kernel, untrusted solver, untrusted model, or human
reviewer. A human diagnostic remains weaker than a separately authenticated
acceptance/review lifecycle event. A
timeout or failed search is `unknown`, never “false.” The assistant may report
a checked proof of `~A` or a concrete certified counterexample, but must not
silently repair binders, assumptions, quantifiers, implication direction, or
the target to obtain a nearby theorem.

## Non-negotiable contracts

- [ ] Keep Peano Lab as the sole object language and preserve conservative
      expansion receipts for every defined notation used by authors or tools.
- [ ] Preserve the Peano Lab trust boundary: every scored QED independently
      kernel-checks against the original target; all search and ML components
      remain untrusted.
- [ ] Label every artifact constructive or classical. Reject any classical
      dependency, DNE node, or classical solver route in constructive mode.
      Until K5, v2 certificate bytes rely on their owner-held verification
      request/result receipt for this label; v3 will bind it internally.
- [ ] Require explicit human acceptance before a prose candidate becomes a
      theorem proposal and explicit review before any proposal becomes public.
- [ ] Retain readable and best-known optimized proofs separately; both check
      the same original statement. Say “minimal” only with a proved lower
      bound, otherwise report the exact Pareto metrics and “best known.”
- [x] Freeze and hash the exact language/semantics profile. Do not call full HA
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

- [x] Write the exact term/formula grammar, binding/substitution rules,
      intuitionistic proof calculus, arithmetic axioms, and induction policy.
- [x] State whether any formulas belong to a decidable subfragment. Profile v1
      registers none: it has no decision theorem, terminating decision
      algorithm, resource-bound decision claim, or negative theoremhood claim.
- [x] Specify canonical input normal forms and every translation used by an
      external solver.
- [x] Freeze exact evidence schemas for `proved` and `unknown`, including field
      types, additional-field policy, and every non-self-referential hash
      preimage. Profile v2 content-addresses `peano-hydra-result-v1` at semantic
      digest `cf1caf1c867ddfbe3c247e42a18b730ea6790269718170a51f9733d5a7a36b26`;
      historical profile v1 keeps its draft label. `not_theorem` is unsupported
      and forbidden, and a timeout is always `unknown`.
- [x] Publish one canonical machine-readable profile and bind its digest into
      every profile-era Hydra policy, row, run, replay, and pilot artifact.
      Historical pilot v1 remains explicitly pre-profile.

### H0.2 Establish independent semantic checks

- [x] Cold-replay the complete 384-entry H0 candidate-L0 catalog twice; both
      fresh processes produced root
      `fae19fad55c416ae7b695107390c1c733d6740fe63d10cf0efed127f5801b9d2`.
- [x] Assemble at least 1,000 semantic-conformance formulas: at least 400
      theorems and, if a decision claim is retained, at least 400 certified
      non-theorems. The retained corpus has 1,024 distinct positive formulas
      and no negative quota because the profile makes no decision claim.
- [x] Build an independently implemented reference for the claimed fragment
      and compare every in-scope result. The exact reviewed Lean commit,
      source/toolchain manifest, and verifier binary agree on all 2,058
      artifact cases; native Rust and WASM diagnostics record explicit
      out-of-envelope cases rather than semantic disagreements.
- [x] Mutate proof constructors, binders, substitutions, translations,
      induction instances, and negative witnesses; require rejection.
- [x] Re-run kernel import-boundary, original-goal, and transactional-history
      tests.

### H0.3 Freeze the macro protocol

- [x] Specify canonical typed encodings for `Use`, `Cut`, `Witness`, `Induct`,
      `Rewrite`, `Split`, and bounded `Dispatch`.
- [x] Compile each action deterministically to existing public Peano commands
      and/or an untrusted bounded solver call.
- [x] Verify that failure leaves proof state and history byte-for-byte
      unchanged.
- [x] Reject unknown versions, hidden commands, out-of-profile formulas,
      unavailable lemmas, and solver claims without reconstruction.
- [x] Log raw proposals, parsing, compilation, state transitions, solver
      transcripts, and replay outcome in a canonical trace.

### H0 acceptance gate

- [x] Two identical 100%-green cold replays of the H0 candidate-L0 library.
- [x] All conformance/reference checks agree and all required mutations fail.
- [x] No kernel dependency on engine, UI, ML, or external solver code.
- [x] Exact fragment and claim boundary reviewed before benchmark generation.

**No-go:** any false acceptance, unresolved semantics, or unsupported negative
claim. If negative evidence is not available, explicitly relabel the project a
sound theorem prover and continue without a decision claim.

## H1 — Authoring contracts, library epoch, sealed benchmark, and headroom

### H1.0 Freeze native authoring contracts

H1.0 is the campaign-integration gate. It consumes standalone A0's schema
contract plus the adjudicated-corpus and revision-safety portions of A1/A5;
therefore A0 may complete before H1.0, but H1.0 never completes merely because
the schemas exist.

- [ ] Freeze strict canonical schemas for documents, source units,
      formalization candidates, diagnostics, proof attempts, and theorem
      proposals, plus chained authenticated lifecycle and explicit export
      events. Freeze their actor/session-owner and reviewed-registry boundary
      now; A5 implements the asynchronous service later. Checked constructors receive actual kernel `Formula` and
      `Proof` objects; callers cannot supply a trusted `checked` bit.
- [ ] Bind every object to its exact document revision, source span/hash,
      logic/profile, library epoch, lineage state, and training-consent value;
      consent defaults to deny.
- [ ] Reject stale asynchronous responses, duplicate/extra/noncanonical JSON,
      unsafe text, prompt-to-command injection, and provenance escalation.
- [ ] Create a manually adjudicated 200-unit TRAIN/DEV authoring corpus that
      covers missing assumptions, binder ambiguity, quantifier swaps, reversed
      implications/equalities, out-of-language text, questions, and exposition.
- [ ] Keep the browser workspace append-only and revisioned. Only an explicit
      export action may create a patch or PR; browser/model/solver code never
      mutates the public catalog directly.

### H1.1 Freeze `L0`

- [ ] Snapshot the complete checked public catalog available at freeze time
      (at least the current 384-theorem runtime).
  - [x] Build the subordinate replay-complete **candidate** transport: 384
        canonical `peano-lab-v2` artifacts, exact original statements, a
        strict bounded decoder, deterministic manifest/replay roots, and an
        import-guarded fresh
        `python -I -S -X pycache_prefix=<fresh-dir>` kernel replay. This closes only the
        certificate-transport/replay subgate; `status = candidate` and
        `evaluation_eligible = false` are enforced by schema.
  - [x] Build the H1.1a candidate epoch-metadata readiness ledger without
        mutating either earlier format. It binds the exact replay
        manifest/report/catalog, 384-row order, 1,038 declared publication
        edges, all 384 source locators, proof/profile/script metadata, and
        present/stale/missing documentation receipts. Its schema enforces
        `status = candidate`, `freeze_ready = false`, and
        `evaluation_eligible = false`; it cannot create an owner deposit.
  - [ ] Repair and audit the 144 missing deployed explicit-explorer,
        defined-explorer, and definition receipts. Keep the 317 disjoint
        non-`L0` explorer rows as provenance only and exclude the full
        557-row corpora from epoch training, retrieval, and evaluation.
    - [x] **H1.1b1 — selected API records:** build a separate, tagless,
          replay-ordered candidate documentation bundle directly from the 384
          retained replay rows. Filtering the 557-row explorer is forbidden:
          its legacy public `dependents` fields leak 757 name references into
          the 317-row disjoint candidate corpus. Its fresh explicit and
          defined records contain
          exactly 1,038 internal declared edges, 13,862 tactic lines, 40
          serialized definition records from the 43-entry parser registry,
          and no names, bodies, tags, `dependents`, or artifact hashes from the
          317 disjoint rows. This closes the isolated selected-API generation
          subgate only; it does not repair the deployed explorer pages or
          change metadata-v1's historical 240-complete report. The compactor's
          wider QR-stack import is lazy so importing the selected per-theorem
          API does not itself load non-selected theorem bodies.
    - [x] **H1.1b2 — selected metadata join:** add metadata v2 that binds the
          isolated bundle and reports selected API coverage separately from
          deployed-page coverage. Preserve metadata v1 exactly as historical
          evidence.
  - [ ] Register the reviewed source commit/dirty-state receipt, independent
        owner deposit, and immutable `research-eval` freeze before calling the
        result production `L0`.
- [ ] For each theorem bind name, canonical statement, ordered dependency vectors,
      source/script/certificate hashes, node count, depth, declaration order,
      language profile/mode, definition receipts, readable explanation, and
      generated-document identities.
- [ ] Record readable-proof and optimized-construction direct dependency
      vectors separately, derive a deterministic publication union, verify
      each by leave-one-out replay, and use the union for graph/lineage masks.
- [ ] Compute an ordered epoch root and independently verify every certificate.
- [ ] Separate living `authoring-live` HEAD from the physically copied,
      content-addressed `research-eval` pack. Record all later theorems under
      `L1` or later and prevent them from entering this campaign's training,
      retrieval, imports, documentation context, or evaluation.
- [ ] Enforce monotone logic visibility: constructive rows are eligible in
      both modes; classical rows require a separately frozen classical profile
      and are never visible to a constructive epoch.

The implemented candidate subgate is pinned by replay-pack schema v1,
semantic digest
`d60b07fe68aa4ba023c9bb873e2df4190752f70252caca21da7e76dcd393f02d`.
The retained pack contains 384 certificate files and 80,088,767 artifact
bytes. Its manifest root is
`fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d`;
its fresh-worker recomputed theorem replay root is
`88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba`.
The fresh-worker report records that the theorem library, tactic engine, UI,
training package, Torch, and Transformers were absent and import-blocked. This
evidence says neither that declared dependencies are minimal nor that the
certificates are best-known.

H1.1a metadata schema v1 has semantic digest
`71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c`
and exact document SHA-256
`9867378c8802501d2120ad4d94a86378815cf90b003eafc92b164685da61c956`.
The 5,880,054-byte canonical candidate has root
`b2f397cec26d5f22bf0806da1f6e219d26bb5e319a503395150d9278efae8279`.
It records 384 source locators, 1,038 declared edges, and 240
documentation-complete theorem rows. Atlas and vault missing/stale counts are
zero; the atlas is pinned to commit `32803924…`, and all 1,536 commit-pinned
blob links were audited. Each explorer has 557 rows: 240 join this candidate,
while 317 disjoint names are non-`L0` provenance. The remaining 144 candidate
names have no explorer or definition row, hence 144 missing and zero stale in
each such receipt class. All 384 rows still have pending review, lineage,
best-known comparison, readable/optimized dependency-vector, and publication-
union evidence. Repairing those 144 receipts and completing A2 precede a
source-state request to an external independent owner.

H1.1b1 adds a closed five-file candidate bundle under
`artifacts/peano-hydra/l0-documentation-candidate-v1/`: `schema.json`,
`explicit.json`, `defined.json`, `isolation-receipt.json`, and
`manifest.json`. Schema semantic digest is
`30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d`
and its exact artifact SHA-256 is
`a442e89ac312302dcee777b5741ca7f2d67e10f6ebcc996b8096fc6061c28a9c`.
The explicit document root/artifact pair is
`b7942fa5a866ff7cd8a38f30c93787ec0abd2948e69710651e4d3578e64377da` /
`f1c9f364db0cb7ae7f4c7fe065b1ef48d5522fc49711667479ec3dc4db723936`;
the defined pair is
`897fd5e4bedb44b63853e428ff5bc2e2c273e30a0c239450e0ec8f93d73fc61f` /
`164b34dd0cad555baf2164ee3da114fb60a447bd667112481e7225097dd17cea`;
the isolation pair is
`64bdc2c52bcaf88d26382bbe514be4a442cc876b8df2a353c272587e1516d919` /
`8c8a6882d0d5a82552942fc0c3efe5a900244a9cad02c32b24cabe3d86a0eee6`;
and the manifest pair is
`8f7ef8fcca69bc6f5f8b39c220293b8414a65fd81576c584f78e59da104d46a4` /
`5ded97c27b859cc4725362bc76aba89fac06c5f11843b50529b78050b19348bf`.
The focused implementation gate passed 36 tests in 126.87 seconds; after the
final pin update, the seven targeted retained-artifact tests passed with 36
deselected in 7.10 seconds. Final acceptance then passed all 43 focused tests
in 115.64 seconds and 23 compatibility tests in 18.19 seconds.

H1.1b2 preserves metadata v1 byte-for-byte and adds a full candidate successor
ledger. Schema v2 has semantic digest
`498dde0a3b4f762197d8c371609dfac2eabf7edcfc37a6d3c5cdf6ca21efb38a`
and exact artifact SHA-256
`27af1e5c1ee0e73cb012db3d8b94cb9a6e1be48d08e8158ad48b8edac399973e`.
The 3,732,032-byte retained ledger has exact artifact SHA-256
`dc6a59ce08397eba698651f6ed4faac0533dec55c13d5a8ca49d863d19d7b72d`,
semantic root
`e0c1d3683e111d7f2883cebbc423694159e82d95471d9375866a81ec596dfb9e`,
and ordered theorem-record root
`22330158f52f049ec920992f51f96a0ab0e9939c3eeb893f533616c17b48e98a`.
Its 1,891-byte readiness report has artifact SHA-256
`f257646d1ba5b51835c8b1718538b4b21c89ea402ba073a9630842708db0206b`
and binds the ledger's exact transport hash as well as its semantic root.

The successor reports 384 selected explicit/defined API and definition-use
receipts, but separately preserves the historical deployed-page intersection
of 240 rows and two 144-row presentation gaps. It adds no page, owner, review,
lineage, minimality, best-known, dependency-vector, publication-union, A2,
freeze, training, retrieval, or evaluation authority. All 384 rows retain
those unresolved fields. H1.1 therefore remains open. A2 dependency
minimization/publication-union construction and deployed-page repair are the
next two independent workstreams; both precede lineage and an independently
owned source-state/freeze request.
Final H1.1b2 acceptance passed 46 focused tests in 101.07 seconds; the
standalone retained `--check` passed in 30.4 seconds, and the independent
post-optimization threat audit found no blocker.
Historical Hydra compatibility passed 119 tests in 204.71 seconds, the sibling
Lambda suite passed 360 tests plus 36 subtests, and the warning-as-error Book
plus its 2,324-page structural integrity gate remained green.

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
      statements. The current positive-only profile has no non-theorem quota;
      a later negative stratum requires a new profile and independent decision
      authority.
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

- [ ] Authoring schemas are canonical, mutation-tested, revision-safe, and
      incapable of forging kernel or human-review authority.
- [ ] The 200-unit gold corpus is human adjudicated and lineage-separated
      before any paraphrase or proof-state expansion.
- [ ] Zero detected contamination.
- [ ] Living-library growth cannot alter the frozen epoch pack, retrieval
      surface, documentation context, or replay root.
- [ ] No classical-to-constructive import path exists.
- [ ] At 60 seconds the symbolic baseline leaves at least 100 targets or ten
      percentage points unsolved.
- [ ] The teacher closes at least 20% of the symbolic DEV frontier through the
      frozen macro interface.

**Pivot rules:** if symbolic solves at least 99.5% at 60 seconds, study
latency/proof size rather than claim a solve-rate opportunity. If the teacher
closes below 10%, repair the action interface before training. A successful
teacher pilot establishes interface headroom only—never Qwen capability or an
LLM win.

## H2 — Strong frozen native/Vampire symbolic portfolio

- [ ] Implement proof-producing deterministic normalization, rewriting, and
      arithmetic closure.
- [ ] Implement an intuitionistically valid focused/connection/tableau search
      for the frozen fragment.
- [ ] Add bounded witness/instantiation and induction-candidate enumeration.
- [ ] Make Vampire the only first-class external prover in the initial
      portfolio. E/SMT remain deferred comparison tools and require their own
      reviewed adapters before use.
- [ ] Keep TPTP/clausification/Skolem symbols internal. In constructive mode,
      use Vampire first for premise bundles, instantiations, witnesses, cuts,
      rewrites, or proof skeletons; direct proof reconstruction is admitted
      only for an explicitly proved translation class. Classical use requires
      the separately frozen classical profile.
- [ ] Reconstruct all external-solver successes into ordinary Peano
      certificates; never score status strings or untranslated proof objects.
- [ ] Minimize reconstructed direct dependencies by deterministic leave-one-
      out replay and retain a proof Pareto report over nodes, distinct objects,
      depth, Cuts, bytes, replay time, and readable-script length.
- [ ] Tune portfolio scheduling on DEV only.
- [ ] Freeze the Vampire binary, options, translator, parser, raw transcript,
      source-symbol map, schedules, and hard bounds.
- [ ] Make every component independently disableable.

### H2 acceptance gate

- [ ] Every counted positive passes kernel replay. Negative results are counted
      only if a separately registered negative-decision profile is active and
      each passes that profile's independent authority.
- [ ] Forged `SZS` status, malformed proof, wrong target, masked premise,
      foreign symbol, timeout, and resource exhaustion all fail closed and
      leave the proof state unchanged.
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
- [ ] Keep prose classification/formalization/critique rows separate from
      proof-policy rows. Human-approved source-to-statement pairs may train
      formalization; kernel QED roots train proof actions. Neither authority
      substitutes for the other.
- [ ] Admit only complete replayed QEDs as positive labels. Retain failures and
      partial paths only as labeled search evidence.
- [ ] Deduplicate by canonical state/action and lineage, not surface spelling.
- [ ] Audit state/action balance, theorem-use coverage, induction/cut/witness
      coverage, natural-language provenance, ambiguity classes, sequence
      lengths, and tokenizer round trips.
- [ ] Reject over-length examples instead of truncating them silently.
- [ ] Rebuild twice from clean inputs and compare bytes and Merkle roots.

### H3 acceptance gate

- [ ] Thresholds above are met, every positive root replays, clean builds are
      byte-identical, and contamination count is zero.
- [ ] Dataset/model cards disclose generators, licenses, filters, duplicates,
      failure data, lineage construction, and known blind spots.

## H4 — Model ladder, search, and causal ablations

The primary learned family is small LoRA-post-trained Qwen, kept below 10B
parameters. Separate tagged tasks/adapters cover prose classification,
prose-to-PA candidates, ambiguity critique, theorem retrieval, macro proposal,
frontier/value ranking, and explanation drafting from checked artifacts; one
decoder response is never allowed to smuggle authority from one role into
another.

Run each rung under registered DEV budgets:

- [ ] `S`: frozen symbolic portfolio.
- [ ] `S+BM25`: deterministic lexical theorem retrieval.
- [ ] `S+R`: learned retrieval.
- [ ] `S+C`: cheap learned clause/state ranking.
- [ ] `S+P0`: identical pretrained Qwen macro policy.
- [ ] `S+P1`: 1.7–3B Qwen supervised macro policy.
- [ ] `S+F1`: LoRA formalization/critique adapter evaluated only on adjudicated
      authoring DEV units.
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
- [ ] Formalizer: report parser-valid rate, top-1/top-3 human-approved semantic
      accuracy, critical binder/quantifier/assumption error rate, ambiguity
      abstention quality, and median edits/turns to acceptance. Kernel validity
      of a nearby statement is not semantic formalization accuracy.
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
- [ ] Independently replay all counted proofs and, only if a separately
      registered negative-decision profile is active, all claimed negative
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
- [ ] Generate a source-controlled LaTeX report and reproducible PDF covering
      data preparation, Vampire/native search, Qwen LoRA training, evaluation,
      inference, authoring infrastructure, trust limits, and results.
- [ ] Keep `MEMORY.md`, `JOURNAL.md`, and `book/peano/diary.md` synchronized;
      validate their named artifact identities against the plan/design.
- [ ] Reproduce certificate judgments and paper tables on a fresh machine.
- [ ] Pass the complete Peano and Lambda suites, strict book build, executable
      command replay, vault/link checks, LaTeX/PDF build and visual/text
      verification, artifact drift checks, and license audit.
- [ ] Obtain independent sign-off on leakage, matched compute, replay, and
      admissible wording.
- [ ] Publish/merge only at an authorized milestone boundary.

## A0–A6 — Continuous native-PA authoring product

This track ships incrementally alongside H1--H6. It is not postponed until the
research release and it does not consume the sealed final benchmark.

### A0 — Native authoring contract

A0 ends at the canonical transport and authority boundary. The gold corpus and
interactive/recovery behavior belong to A1/A5 and are additional H1.0 gates.

- [ ] Freeze canonical document, source-unit, candidate, diagnostic, attempt,
      theorem-proposal, lifecycle, and export-event schemas with content roots,
      actor/session-owner authentication, and mutation tests.
- [ ] Require exact revisions, profile/logic/epoch identities, default-deny
      training consent, and real kernel objects for checked evidence.
- [ ] Bind the existing Peano Lab defined-syntax registry identity and freeze
      readable-to-primitive expansion receipts, exact definition uses,
      round-trip checks, mutation rejection, and final replay against the
      expanded original target. Do not create a second definition registry.

### A1 — Sentence workbench

- [ ] Preserve every prose revision and classify units before formalizing.
- [ ] Show readable PA, expanded PA, binder/assumption/conclusion tables,
      alternative readings, and deterministic structural read-back.
- [ ] Verify every displayed defined formula through the A0 registry/expansion
      receipt and reject registry, definition-use, or expanded-target drift.
- [ ] Require explicit Accept/Edit/Reject; never silently choose a reading.

### A2 — Checked artifact compiler

- [ ] Compile accepted units into reviewable theorem proposals containing
      lineage, dependencies, explanations, scripts, traces, certificates,
      metrics, provenance, and Book/vault/Explorer previews.
- [ ] Produce a patch/PR only on explicit export. No unreviewed theorem enters
      `TheoremSpec` or a public catalog.
- [ ] Require deterministic documentation and leave-one-out checks for both
      readable-proof and optimized-construction dependency vectors; publish
      their ordered union as the theorem graph edge set.

### A3 — Hybrid native/Vampire assistance

- [ ] Run deterministic native closure before bounded Vampire `Dispatch`.
- [ ] Reconstruct every useful hint through ordinary Peano macros, record all
      calls, and compare solve/resource AUC against native-only search.

### A4 — Qwen LoRA assistance

- [ ] Train/evaluate separate formalization, retrieval, macro, value, and
      critique/explanation adapters on lineage-safe checked/adjudicated data.
- [ ] Keep the historical model-v3 next-tactic checkpoint as a baseline, not a
      prose formalizer or evidence of current-library capability.

### A5 — Live assistant

- [ ] Add an asynchronous service behind Peano Lab with append-only events,
      document-revision preconditions, cancellation, restart/reload recovery,
      stale-response rejection, and an offline mode that still provides
      deterministic parsing, defined expansion, local-library use, proof
      execution, original-goal kernel replay, and explicit export.
- [ ] Preserve the existing single proof-session owner. Prompt text cannot
      execute commands, and failed background work cannot mutate a document,
      proof state, history, library, or Git tree.

### A6 — Library admission and release

- [ ] Require human-approved statement/explanation, logic label, dependency
      hygiene, empty-context replay, mutation checks, proof Pareto report,
      reproducible documentation, and a new immutable library epoch.
- [ ] Retain the readable, optimized, and publication-union dependency vectors;
      lineage masks follow the union.
- [ ] Retain both the readable authored script and best-known optimized
      certificate against the same original goal.

### Authoring acceptance gate

- [ ] Representative prose-to-formula-to-proof-to-document sessions replay
      exactly after export, reload, and clean rebuild.
- [ ] Stale replies, prompt injection, forged review/kernel authority,
      classical-to-constructive imports, dependency cycles, mislabeled human
      prose, and denied-consent corpus inclusion are rejected.
- [ ] Every displayed mistake or inaccuracy names its authority and evidence;
      search exhaustion remains `unknown`.

## K5–K11 — Rust authority and Lean refinement continuation

The implemented native/WASM Rust checker is already a useful, fast shadow.
The remaining problem is not “write Rust”; it is proving a connection from the
exact Rust accepted path to the Lean specification. The binding details and
acceptance checklists live in
[`PLAN/12_peano_kernel_acceleration.md`](12_peano_kernel_acceleration.md):

- K5 freezes a logic-carrying `peano-lab-v3` wire protocol and typed outcomes;
- K6 completes representative measurement;
- K7 hardens the production Rust candidate and resource accounting;
- K8 proves the version-3 algorithm and codec sound in Lean;
- K9 attempts exact safe-Rust-source refinement into Lean;
- K10 requires a cross-platform dual-check soak; and
- K11 makes a separate reviewed authority decision.

Until K9--K11 pass, Rust may accelerate candidate filtering, Vampire
reconstruction, model rollouts, corpus generation, and browser diagnostics,
but Python still performs the mandatory final original-goal QED check.

## Quadratic-reciprocity expansion track

This is future library growth, not part of `L0` unless completed before H1.

- [ ] Intake every parallel campaign/PR through an explicit review manifest:
      source commit, statement/proof exposure dates, checked status,
      dependencies, logic mode, license, and intended `authoring-live` epoch.
      Any statement whose proof or substantive sketch was already visible is
      ineligible for the active sealed test and is marked TRAIN/DEV/library.
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

The sealed H campaign remains a four-to-six-month research program. The living
authoring product and source-refined Rust authority are longer parallel tracks;
their gates, not a calendar promise, control release. A first H0--H4 DEV
prototype is expected to take eight to ten weeks if epoch, authoring-contract,
and benchmark work precede GPU training.

| Weeks | Work | Exit artifact |
|---:|---|---|
| 1–2 | H0 semantics, macro schema, reference checks | reviewed profile and conformance report |
| 2–4 | H1/A0 epoch, lineage, authoring schemas, sealed benchmark | `L0` root, authoring contract, independent deposit |
| 3–7 | H2/A1–A3 native + Vampire and sentence/artifact workbench | frozen `S`, checked proposal pipeline |
| 5–8 | H3/A4 checked macro and formalization corpora | deterministic replayed releases |
| 7–10 | H4/A5 Qwen LoRA ladder, ablations, live assistant | frozen `S+R`, candidate `H`, usable DEV workbench |
| 11 | H5 one-shot evaluation | closed evidence bundle |
| 12–16+ | H6/A6 replication, admission, release | reproducible report, assistant, and artifacts |
| parallel | K5–K11 protocol, Rust hardening, Lean/source refinement, soak | separately reviewed authority decision |

## Current status

- [x] Expanded mission adopted on 2026-08-04: one native Peano Lab object
      language, continuously reviewed library, live proof-document authoring,
      Vampire-first symbolic assistance, small Qwen LoRA roles, and a separate
      Rust-to-Lean refinement track. H0 artifacts remain unchanged.
- [x] Binding design and campaign gates documented.
- [x] Historical model-v3 four-goal result classified as a regression smoke,
      not campaign evidence.
- [x] Current 384-theorem library identified as the minimum candidate `L0`;
      exact H1 freeze is still pending.
- [x] H0.1a semantic profile v1 is frozen at digest
      `058b1644b066967919dae092e5e562b8845e4dd8415fff31d7cd209d51bc9e43`.
      It is intuitionistic theorem-prover-only: no decision fragment,
      `not_theorem`, classical checker, or external translation is registered.
      Its operational target preflight is frozen at 8,192 Unicode code points
      and decimal numerals at most 256, without turning either ceiling into a
      decision-resource claim.
      Hydra policy/runner/pilot v2 carriers bind the digest; historical pilot
      v1 is preserved as pre-profile evidence. The profile labels its result
      contract `required-field-draft`; exact evidence schemas remain H0.1b.
- [x] A pre-H0 `surface-macro-v0` portfolio/replay bootstrap exists for
      teacher-oracle plumbing. It is deliberately narrower than the structured
      H0.3 macro protocol and did not by itself complete H0. All its rows are
      comparison-ineligible until raw-call/resource evidence, provider
      attestations, and genuine critical-frontier detection exist.
- [x] H0 completed on 2026-08-04. Profile v2/result-schema v1 freeze exact
      positive/unknown evidence; macro protocol v1 has semantic digest
      `b5fef1ea1b85251ab7f0b8c111cb37e789f96f20771665b4f0dc8b746400552c`;
      and the retained campaign artifact
      `artifacts/peano-hydra/h0-validation-v2.json` passed from clean commit
      `26c2503b36c6884bfbfa6dabd1494bbda49d8926`. It records 1,024 positives,
      1,024 wrong-target certificate rejections, ten artifact mutations, three
      profile/schema boundary mutations, exact Lean agreement, two identical
      384-theorem cold roots, and complete typed-macro trace/reconstruction/
      rollback evidence backed by 110 focused tests. Report v1 is provisional
      H0.1/H0.2 evidence only. This candidate-L0 semantic replay does not
      perform H1's epoch/lineage/benchmark freeze.
- [ ] No H1 benchmark is sealed and no H5 claim is available; experimental
      scaffolds or earlier policy checkpoints do not change that status.
- [x] The first A0 protocol slice is executable. Authoring schema v1 has
      semantic digest
      `31a344bbc0b22cfacf5803c85d25a80a0234cf7387395283c5e1ab25ada80553`;
      its public builders/loaders bind exact revisions, default-deny consent,
      the pinned existing defined-syntax registry, untrusted diagnostic
      labels, real kernel objects for checked proposals, and ordered
      actor/session-owned lifecycle/export deposits. The production event
      registries remain empty. Fresh proof metrics say `submitted`, not the
      unproved `best-known`; A2 owns that comparison. This is a public-API/data boundary, not a
      sandbox against arbitrary private same-process Python access.
- [x] The first H1.1 epoch-protocol slice is executable. Schema v1 has digest
      `f4695013ee4aeb660abf3a1e57a6334d86c990a8904c4435d94628694a2e875b`;
      candidates revalidate live HEAD and the 384-theorem catalog, version and
      root comparisons are type-exact, file reads are bounded/no-follow, and
      changed source inputs require a fresh interpreter. The owner-receipt
      registry is immutable and empty. The integrated Hydra regression passed
      325 tests; the focused authoring and epoch files passed 28 and 38 tests.
- [x] The subordinate H1.1 replay-pack subgate is executable. Replay-pack
      schema v1 has semantic digest
      `d60b07fe68aa4ba023c9bb873e2df4190752f70252caca21da7e76dcd393f02d`;
      the 384-file candidate pack has manifest root
      `fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d`
      and theorem replay root
      `88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba`.
      Its retained fresh `-I -S -X pycache_prefix=<fresh-dir>` worker report is
      byte-for-byte reproduced by the 384-theorem acceptance test. The
      historical three-file epoch fixture remains unchanged as v1 transition
      evidence.
      The decoder/replay boundary passes 108 and 37 focused tests; deterministic
      full-tree sharding plus the two required environment-specific reruns cover
      3,050 passing Peano cases with 12 registered skips. Lambda Lab remains
      green at 360 tests plus 36 subtests.
- [x] The H1.1a candidate metadata ledger is executable. Metadata schema v1
      has semantic digest
      `71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c`
      and document SHA-256
      `9867378c8802501d2120ad4d94a86378815cf90b003eafc92b164685da61c956`;
      the canonical 5,880,054-byte ledger has root
      `b2f397cec26d5f22bf0806da1f6e219d26bb5e319a503395150d9278efae8279`.
      It binds all 384 replay rows, 1,038 declared edges, 384 source locators,
      and 240 fully joined documentation records while preserving every
      unresolved field. Atlas/vault gaps are zero. Explorer and definition
      gaps are 144 missing and zero stale; the 317 additional explorer names
      are disjoint non-`L0` provenance and are excluded from epoch surfaces.
      Fifty-three focused adversarial tests passed in 78.89 seconds; two clean
      CLI builds were byte-identical, retained `--check` passed, the 32-test CI
      shard contract passed, and atlas plus all seven arithmetic-Book tests
      passed. Replay-pack and unchanged epoch-v1 suites passed 37 and 38 tests;
      3,115 Peano tests collect cleanly and Lambda remains 360 plus 36
      subtests. The warning-as-error 46-source Book, 2,324-page structural
      integrity gate, all 194 links/287 commands, and the 490-note/4,981-link
      vault are green. This is implementation acceptance, not owner review.
- [x] H1.1b1's isolated selected-API bundle is retained as five canonical
      files. It reconstructs all 384 rows in replay order without global PA
      tags, records 1,038 internal declared edges and 13,862 tactic lines, and
      compacts 321 statements plus 624 of 950 local propositions through the
      exact-AST checker. The defined view contains 2,027 definition
      occurrences and 40 serialized definitions while pinning the complete
      43-entry parser registry; statement text contracts from 224,948 to
      29,098 characters and local propositions from 148,105 to 25,733. Its
      isolation receipt rejects foreign names,
      disallowed `dependents`, and any dependency outside the selected set.
      No candidate body/name or legacy-explorer artifact hash enters an
      authoritative bundle root; the old 557-row surfaces, their tag registry,
      and metadata v1 remain byte-for-byte historical evidence. Focused tests
      passed 36/36 in 126.87 seconds, then the seven retained-pin tests passed
      with 36 deselected in 7.10 seconds. Final acceptance passed 43 focused
      tests in 115.64 seconds and 23 compatibility tests in 18.19 seconds.
- [ ] A0/H1.0 and H1.1 remain open. The candidate pack deliberately records
      declared publication dependencies and source-stage sharing observations,
      not separately leave-one-out-verified readable/optimized vectors,
      best-known certificates, complete deployed-page/document receipts, lineage
      masks, source-state/owner freeze receipts, or a sealed benchmark. All
      384 rows retain pending review, lineage, best-known, dependency-vector,
      and publication-union gaps. H1.1b2 now reports selected API coverage
      separately from deployed-page coverage while preserving metadata v1.
      The immediate work is parallel deployed-page repair and A2; both must
      finish before a source-state request to an external owner. No 200-unit gold
      corpus, Vampire adapter, new Qwen training, classical Hydra profile, or
      Rust authority claim is yet complete.
