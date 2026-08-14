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
    - [x] **H1.1b3 — selected page-build source:** render a separate, tagless
          candidate tree for all 384 selected rows and 40 definitions from the
          exact H1.1b1 bundle. Keep the historical 557-row explorer and tag
          registry immutable. This establishes `generated = true` and
          `deployed = false`; only an external host receipt may establish
          deployment.
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

H1.1b3 retains the candidate page source at
`book/_static/pa-selected-library/`: 384 explicit pages, 384 defined pages,
40 definition pages, and one index, for 809 HTML pages and 813 files. The
schema semantic/artifact pair is
`eefb4b1154581f248696de3f81bd90296398e5353c6a42d0d01f35b3ccdb2abb` /
`8cdf0e947ce7156109b7591c99ed28d8ee1f938edd3cddfb414d48d7efacdafd`;
the API artifact/root pair is
`a7a4be8ba895b9e69955e82bda5bbfe7418eeda47632a59899e6ba0896acaaf0` /
`2efbb00a763f120e5cee6271f3d64838b3a54e04e73a4c78c738f4d50f0b83b1`;
and the manifest artifact/root pair is
`751c3eefc99e5b30d612049fd99a0d890cd696b3fda0f426ca64d835c5fe2e6f` /
`94b38f4914853c87315f0bc94d33347164d4cb7c01cd81568b1c4f47cb1b1563`.
The external 3,118-byte readiness receipt has SHA-256
`69b11b858348e3dda9a007b495c7198634822623d45314f6f82f551141bc9357`
and root
`8f7bf0fc18917b92d02d862e13507d28f1bf7d2842fcd93427d3a2879a193b1f`.
All surfaces enforce `candidate`, `deployed = false`, and false freeze,
training, retrieval, and evaluation eligibility. The focused page-core gate
passed 11 tests in 74.53 seconds. WMI now reconstructs the exact candidate in
read-only mode before Sphinx and audits its copied tree separately from the
legacy explorer. This does not create a public URL or deployment receipt, so
the historical 240/144 deployed-page observation and H1.1's open status remain
unchanged. The integration harness passed 11 tests in 2.33 seconds, 17 focused
Book tests passed in 1.77 seconds, the warning-as-error Book build succeeded,
and the version-three integrity gate covered 3,133 HTML pages with zero broken
targets, fragments, escapes, remote runtime assets, or unsafe active links.

A2.1 now retains a candidate-only dependency-audit sidecar at
`artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json`. For each of the
same 384 replay-ordered `TheoremSpec` recipes, it tries dependencies in reverse
declaration order and repeats complete passes to a fixed point. An omission is
accepted only when the reduced dependency-curried target is accepted by the
independent kernel. Resource limits, malformed inputs, and unexpected/internal
failures are `unknown` and abort the build; a failed omission records only that
the exact tactic recipe failed, never that the dependency is mathematically
necessary.

The two complete builds were byte-identical. Schema semantic/artifact
SHA-256s are
`54d6b5128067b1f93d8f7393e0730d7da3a4ac838a0b55b6b6fe0ce92a0d4bc4` /
`ee6eb4daf48fbf320e79a54065befed758ff33c5251ec4a2c18b8093c349c0ff`.
The 4,188,048-byte artifact has SHA-256
`4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040`,
document root
`12166de8fb0cc028c3b026deb939418a19f001ff8342acab479d433e15d3a83e`,
and ordered theorem-record root
`8ae5553e79b15c4e83a76e1eab92cb0983539fa913dfe2bec29d0fb17fb7d784`.
It records 3 kernel-accepted omission observations, 1,057 exact-recipe
rejections, zero unknowns, and a candidate edge count of 1,035 rather than the
retained 1,038. Exactly three immutable A2.1 rows carry the historical
`requires_certificate_rebuild = true` observation. The successor A2.2 sidecar
below now discharges that obligation without rewriting A2.1. The retained
certificates, metadata ledgers, page sources, and public graph are unchanged.
All minimality, best-known, publication, freeze, training, retrieval, and
evaluation flags remain false; A2 and H1.1 remain open.

On 2026-08-09, A2.2 retained the separate candidate-only construction-rebuild
sidecar at
`artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json`. It closes
exactly the three A2.1 carriers with replay-pack dependency certificates, then
checks each result from the empty context against the original uncurried
statement. All three checks passed. Across those three candidate Cut spines,
the direct vectors change from 25 to 22 edges and the canonical artifacts
shrink by 49,483 bytes, 1,176 proof-tree nodes, and 34 Cuts. These are
descriptive predecessor deltas only; schedule-dependent Python object-alias
metrics are explicitly non-comparable. Each omitted direct name remains in
the retained transitive closure, and the public graph remains at 1,038 edges.

The A2.2 schema semantic/artifact SHA-256s are
`a189ad140f5e7093f11a2f433705d4dafb71d474672e822cf39e45dbeb1ca571` /
`d1fc09c035e28f96913cdadd63f17c853901fc8dcd2e17df3a094a919612bf9f`.
The exact 3,106,352-byte sidecar has artifact SHA-256
`6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182`,
document root
`91ecc6b4bb22f4b46cdfa3fcdd2401dce47d8fef38c15101d221c207fd7793b0`,
and ordered theorem-record root
`42d718621f91b52bf55a7909751eab695fefd28da2989863de50470d14397ef5`.
The focused gate passed 23 tests in 44.12 seconds. Authority, minimality,
optimized/best-known, publication, review, freeze, training, retrieval, and
evaluation flags remain false; optimizer/comparison/Pareto evidence,
independently audited readable and optimized vectors, and the verified
publication union remain open, so A2 and H1.1 remain open.

On 2026-08-10, A2.3a froze only a bounded optimizer/comparison **protocol and
program** for the three A2.2 roots. It fixes the exact three-candidate universe
(`retained-replay`, `a2.2-direct-cut-rebuild`, and `layered-closure`), four
canonical comparison axes (artifact bytes, proof-tree nodes, proof depth, and
Cut count), componentwise nondominance, and one deterministic representative
tie-break. The layered construction reuses the existing production compiler;
it does not introduce a second proof optimizer or replay tactics.

This tranche did not execute the real three-root build locally or on WMI. No
result sidecar, fresh layered certificate, candidate metric vector,
nondominated set, representative, Pareto frontier, document root, or theorem-
record root exists yet. Direct vectors and transitive closures remain separate
recorded surfaces, and `optimized_vector_independently_audited` is false. The
broad optimizer/comparison/Pareto checkbox below therefore remains open.

The frozen schema semantic/artifact SHA-256s are
`07e5842c221fe84337e163ce5c858ab03dfbbc93d1477f5661edfdd6f8ba3978` /
`006d38ef781fc022b7b8929be35058038df02a0eee91eb2213128598c66a59ae`.
The program, no-default-write CLI, and focused-test source SHA-256s are
`7ac7d784c3660c1c9b839c906e50e2a88dced6af96ded00b900165e25ec12eee`,
`3acbd3ec0f190699d484ef0c800e4919c7cc8404fbbd50ba6daf90a5deb5d6ee`,
and
`d5ae3e830573c7a561462f5e0e91ef99bff42f6533986106cc65fc34f0e35dc9`.
The protocol-only adversarial gate passed 59 tests in 0.31 seconds. All
best-known, vector-audit, publication, A2, authority, review, freeze, training,
retrieval, and evaluation flags remain false.

On 2026-08-10, **A2.3a external execution infrastructure (no
submission/result)** added the source-to-cluster boundary without running the
optimizer. A clean-Git generator now emits the frozen eight-field producer
source state with `git_verified=false` and a separate domain-separated receipt
for HEAD, tree, stage-zero regular blobs, live-versus-committed bytes, and the
resolved Git executable. A separately loaded verifier imports only the Python
standard library and pinned Peano kernel surface; it treats the producer
document as hostile, checks all nine transported certificates from the empty
context, and independently recomputes canonical bytes, structural metrics,
the three Pareto frontiers, representatives, and rooted records.

The bounded WMI path deposits a content-addressed clean snapshot, requests one
`cpu_idle` CPU, 4,096 MiB, and 15 minutes under pinned x86-64 CPython 3.12.12,
runs producers with hash seeds 0 and 1, requires byte identity, then runs the
independent verifier with seed 2. Its execution receipt is published last.
Resource, timeout, scheduler, missing-evidence, and untyped process failures
remain `unknown`; `failed` is reserved for a complete typed contradiction.
The submission wrapper defaults to `--test-only`, but that mode still writes
or verifies the immutable remote snapshot before calling `sbatch --test-only`;
it does not create a Slurm job. Real submission additionally requires the
literal confirmation `PEANO-HYDRA-A23A-WMI-PILOT`. Both remote wrappers accept
an optional syntax-validated `WMI_SSH_JUMP`, passed only as SSH `-J` beside the
validated target; an observed target/jump route records transport mechanics,
not a successful test-only execution.

The exact source-state generator/test SHA-256s are
`4812314f101ac302f712a87641f37ffb627e4cbaa916605e6c7e1e0b0ed90a26` /
`acdde9367e5fdea7fdfc4e6cef1c3ee4c2bddeb4b9fbe1e025581eb3c7fe8860`.
The independent verifier module/CLI/test SHA-256s are
`683ee529ed4be0e93504846340eeddf47eae1cb3f84967168a971d422ade1dbe` /
`1250d0202236a6aa727509c5270767fe91e48cf34e5a6fd9c13ac1a59722f014` /
`08f838332ffca805c934a6c44cf59148e9f0f9168c784f1b7a9c8b8cf353239a`.
The WMI runner/sbatch/submit/collect/test SHA-256s are
`46c9bea044640ccf057a5113eff2f3c6161206c55521b8fcd7c48e7342ff8632` /
`1f09c62532a0c9f10fc11bb00a420e1eea1967dc70686ad503c1e5207b75538c` /
`ce94c5e5e77ff83998f147fb77d3e698eae41366774867238b16990accc7fbee` /
`ddafef2eab12d18ba766325b5dbb077a0075cc8589bc553a72bd60aff910cb0e` /
`cc75ad16a90c289d07851f7d59cf79f2e960acd86d9257f8155a1cabc532a755`.
The WMI protocol file passed 18 tests in 0.72 seconds. Together the three
focused files passed 52 tests in 8.45 seconds (10 source-state, 24 verifier,
and 18 WMI protocol). The earlier independent threat audit reported no blocker
before the final route refreeze.

That tranche ended at infrastructure readiness. The successor execution below
does not retroactively turn its local tests into result evidence.

On 2026-08-10, **A2.3a fixed-pilot execution and retention** completed on WMI
job `219765`. The job used clean commit
`0f6ca3a0cf5998212e3a0ad508ba77e88a15a17d`, tree
`9051b43aa3f7f75d37ce8d410b9c7a81ba472d94`, and snapshot
`707398a7494482dbcc38c8438582688e01f88b395ab61e64be4a7d6396178824`.
Both producer seeds emitted the same 848,463 bytes, the seed-2 independent
verifier accepted 9/9 kernel artifacts, and the terminal collection records
`COMPLETED`, `0:0`, 60 elapsed seconds, and
`completed-and-independently-verified`. A controlled local CPython 3.12 replay
of the retained verifier reproduced its 18,327 bytes; this checks the retained
document and is not a second local optimizer run.

The retained candidate artifact/document/theorem-record identities are
`3e989784d371c3383fa5e428df8755d1e94d4c3386328746751981a8a77cab5b` /
`90a3d97a466dc7b1c9e6032b1b56b8ede3fcece8d56a4b39f2d4e5f34dbeb770` /
`4cfcbe22312ff2b92022189e65d3742bc096ba989dacaa82b2054e84282928e5`.
The verification artifact/document/theorem-record identities are
`6a7942147b8227c61a0de8a8f533653a6d727efe7843a52f3b524f1c47ac084a` /
`e21290f654c1a30e0bdf79e796a8ca1da6ad3aa6a1cb1d8ba34d3d376de052dc` /
`18f882717346477304285c9336d7b769ccf95cd1b58c32b65d335f3e8caa4188`.
Execution and collection receipt artifact/root pairs are
`779a971237f9ac5efe3a86dca5b5c4d74a6da56ab154b91e106f7fd1dac63a34` /
`7a597563c173cd0cb3d57ff42cd566a8531756e84bf8ba907e7c79ec7295dc0e`
and
`25e616fc9225ab59db6a089e8a53ed2d44915a54b42f073bcaaa020fc2ff609a` /
`52339b926ea8b9650787a3db138185e21144f6cdf83596d224ccc6b23435daf2`.

The exact metric vectors are `(artifact bytes / proof nodes / proof depth /
Cuts)`:

| Root | retained | A2.2 direct | layered closure |
| --- | ---: | ---: | ---: |
| `odd_add_odd` | `14,977 / 302 / 32 / 7` | `13,640 / 274 / 31 / 6` | `12,709 / 269 / 37 / 3` |
| `finite_bounded_injective_surjective` | `1,913,452 / 42,463 / 89 / 1,266` | `1,870,657 / 41,341 / 89 / 1,235` | `297,637 / 8,355 / 95 / 20` |
| `beta_product_swap_last_invariant` | `391,540 / 7,439 / 67 / 205` | `386,189 / 7,413 / 67 / 203` | `118,018 / 2,011 / 79 / 9` |

For every root the fixed-set frontier is exactly
`[a2.2-direct-cut-rebuild, layered-closure]`; the preregistered tie-break
chooses `layered-closure`. This is a fixed three-candidate pilot statement,
not a best-known, global-optimum, or minimality claim.

Nineteen evidence files are retained: the candidate and verifier plus 17
operational source, deposit, submission, execution, collection, scheduler,
and log files under `artifacts/peano-hydra/a23a-wmi-pilot-219765/`. The
277,025,280-byte transfer archive was deleted and was not independently
rehashed; its snapshot identity is only transitively receipt-bound. The
retained `sacct` row is an unauthenticated scheduler observation, `MaxRSS` is
absent, and no peak-memory or memory-ceiling claim follows. Producer stderr
retains identical harmless pre-existing Python 3.12 `SyntaxWarning`s; scheduler
and verifier stderr are empty. The retained-result gate source has SHA-256
`28b251f9ab75bea0012949390923b039e267d4721c09bd9ff9b6a08de89cc602`;
its four tests passed in 3.40 seconds.

This closes only fixed-pilot execution and retention. The result documents
deliberately keep `producer_git_verified=false`; a separate rooted clean-Git
receipt binds the execution boundary. Every minimality, global-best/
`optimized_best_known`, independently audited optimized-vector,
dependency-vector completeness, publication, publication-union, review,
lineage, freeze, A2 completion, proof/admission/publication authority,
training, retrieval, and evaluation flag remains false. No public library,
graph, catalog, or page changed.

On 2026-08-14, **A2.3b froze only the bounded dual-route dependency-vector
audit source protocol**. Its universe is exactly the same three roots, in
indices 256, 376, and 379. Their fixed direct vectors contain 3, 14, and 5
edges. For each edge, the protocol schedules one reverse-order omission on
each of two routes: `readable-direct-closure` and
`proposed-layered-closure-construction`. That is exactly 22 attempts per route
and 44 attempts overall, plus one checked baseline per root and route.

The readable route freshly compiles the dependency-curried body and then the
closed direct-Cut candidate. The proposed-layered route must instead
regenerate the omitted root body, recompute its single-root vector-override
closure over the fixed A2.2 vectors, recover every exact modular body and
provenance row, and invoke the existing layered compiler. A shared root-body
rejection is explicitly recorded as one shared preassembly observation, not
as independent corroboration by two algorithms. Only an allowlisted,
route-exact rejection is negative evidence; an accepted omission, unknown,
malformed, unsupported, internal, resource, or unclassified outcome aborts
the candidate document.

This tranche did **not** run the six baselines or 44 real omission attempts on
this Mac or on WMI. It produced no candidate result, audit sidecar, route
receipt, theorem-record root, execution receipt, or publication artifact. Its
per-root ordered union is only a bounded local diagnostic and is never applied
to the retained 1,038-edge graph. The 78 focused tests are synthetic protocol
and adversarial tests; they passed in 2.24 seconds and are not vector-audit
observations.

The schema is 21,875 bytes with semantic/artifact SHA-256s
`6782197c9925f5552aab030a11b996c157e2d06344a2d136d8babc1ee1fdc3df` /
`c4af0d2f850ad16fa7d4a3c086ad13356020a4ccb9a15e0d612babb8db690283`.
The 44-file implementation-source vector root is
`4260928ce3d4243c548e3beda3d6bf823aa9f480dbf58367cab64cad8bf3cdb0`.
The producer, no-default-write controlled-worker CLI, and focused-test sources
are respectively 120,990 / 24,509 / 94,869 bytes with SHA-256s
`3f2c9df051ce4271466b70bdf21ffd59d7ffc298905302d8b42946ca2c87804e`,
`29f56547e6f228cf812df6c013670977de2088d2fccbb7da2fb64cda0ad7737a`,
and
`6c3a0490b86ac2ae7aef3206c480fa14f6e15994106153788d79633fc3025d06`.
The CLI requires an externally supplied four-file producer source state,
authenticates the 44 pinned implementation sources before imports, bypasses
the eager Hydra package initializer in a fresh sanitized
`python -B -P -s -S` worker, writes nothing by default, and publishes only to
an absent explicit destination.

`bounded_three_root_protocol_frozen` is true, but
`bounded_three_root_vector_audit_complete` remains false. No readable or
proposed-layered vector is independently audited yet. Dependency-vector
completeness or necessity, independent optimizer evidence, minimality,
`optimized_best_known`, publication or publication-union completion,
public-graph application, review, lineage, freeze readiness, A2 completion,
proof/admission/publication authority, and training/retrieval/evaluation
eligibility all remain false.

On 2026-08-14, **A2.3b external execution infrastructure** froze the boundary
needed to run that exact protocol without widening its evidence. A producer-
independent clean-Git generator
binds the four frozen producer sources plus its own committed stage-zero blob,
emits the required eight-field source state with `git_verified=false`, and
publishes a separate domain-separated Git receipt and evidence envelope. It
imports no audit producer.

The separately loaded verifier imports only the standard library and the
pinned Peano kernel. It authenticates, decodes, canonically re-encodes, and
empty-context checks six baseline artifacts: three readable baselines joined
to the exact A2.2 embedded artifacts and three layered baselines joined to the
exact retained A2.3a artifacts. It independently recomputes the structural
receipts, roots, order, surfaces, and the `44 route records / 22 shared
observations` pairing. It does **not** rerun the tactic compiler and therefore
keeps `negative_observations_independently_verified`,
`route_rejections_independently_verified`, and
`producer_observations_execution_bound` false in its receipt. Only a future
successful execution receipt may set the last field true.

The source-only WMI path pins x86-64 CPython 3.12.12, isolated
`python -B -P -s -S` workers, producer hash seeds 0 and 1 with required byte
identity, and a seed-2 verifier. It requests one `cpu_idle` CPU, 4,096 MiB,
and 15 minutes, publishes bounded child logs and a create-only execution
receipt last, and treats timeout, resource, scheduler, process, malformed, or
missing evidence as `unknown`. The guarded submitter defaults to
`--test-only`; real submission requires
`--submit --confirm PEANO-HYDRA-A23B-WMI-VECTOR-AUDIT`. One clean-commit
`--test-only` invocation exposed an empty optional-SSH-array bug and stopped
locally before SSH. The refrozen wrappers are covered for unset, explicit-
empty, and exact `-J jump.example` routing by fake-SSH/no-network tests. No
successful real test-only transport, SSH, snapshot deposit, `sbatch`, real
submission, producer campaign, or collector operation occurred.

Source-state generator/test SHA-256s are
`bdc8b4f5b55bcfe22594e2eb40c8c51f4e29df9ef75215b2c9bb0bb561243ea3` /
`728e939359cf750b6e22607ef118b72953752c02cbaecdec9899c99c4ff63917`.
Verifier module/CLI/test SHA-256s are
`b5f5cf39ea7b12d3ed52ee176ed733b28fa2e9224640e89dac77df87b14dfab1` /
`ed9e234f5af04e5878e6f4fd23aace512c66c0bc249fc33dd19c1fcbcdb908c2` /
`43ade850e88d5e7f2ce92ece60857892b79beb2e4b38b0d3a709558352b4d04b`.
WMI runner/sbatch/submit/collect/test SHA-256s are
`2332115e988aada771258f861b986486bc40dc05865935ff3a699453acfe96f1` /
`611b3081f0b53d76343c2d5c684cd74aa12dbb36e0f44e3029541d476bf25100` /
`9774a8705112c0222d300d9ef89235dbc493eb159b907e0e977337b9042d9fe2` /
`5d006e8c453ae78c70fa880695755f8ddf5b488459bb06ab4dd2738ad281089d` /
`d93b3a12f34829bc56f0729a099dc694f9d42dbe7c36c7ffe92844075cb961ef`.
The three focused files pass 45 tests in 15.27 seconds (10 source-state, 13
verifier, 22 WMI protocol), and the independent execution-boundary threat
audit reported PASS. These are infrastructure tests only.

The first real attempt, WMI job 220218, is deliberately **not** the unchecked
execution milestone below. Its seed-0 and seed-1 producers both exited 0 and
emitted byte-identical 3,160,729-byte candidates at SHA-256
`f93e410f64425b31090c933fd7cb7b92bee8f071c3152c79fa55f88001d9841a`.
The independent verifier then exited 1 because its layered-baseline
expectation reused retained A2.3a modular provenance instead of independently
reconstructing the fresh A2.3b provenance. The failed seed-2 run emitted no
independent-verifier receipt. Execution and terminal collection therefore
remained `unknown`, at roots
`cd1872d348b201ba1259fa116be43d66555576e30d3dbc9811fa04c85bdda876`
and
`a610f3feaa3b1d5afa6cbb64be34ea743246f02eb56bc1cc3a2b36ad4dedd681`.
No route rejection, dependency necessity, or other scientific negative
conclusion follows from that failed verification boundary.

The refrozen verifier reconstructs the exact A2.1/A2.2 receipt routes and
replay provenance. A local, two-hash-seed postmortem against the preserved job
candidate produced an identical passing 16,925-byte diagnostic receipt at
SHA-256
`707942bb93d5ad9d26ddf3bbd6733e5b5d403508146a70981c2b507b5a01aad7`
and root
`efe9643d7b3b99f40b9bef6042285efeaa9e5f03d145a09a580a615cd15efa4a`.
That local postmortem diagnostic is not the missing WMI verifier receipt and
has no result/execution authority. No job-220218 candidate or postmortem bytes
are promoted into the corrected result below, and all vector, publication,
A2, authority, and eligibility flags remain false.

The clean corrected rerun, WMI job `220220`, completed from commit
`720021aec7afff0463ef8dd1180db2702b415301`, tree
`03383d9b3c5850edfeb8f3401d55116fa4cdd5a2`, and snapshot
`64266e107ee03fe6833af74f7a8d4d5b645886c064f361acd49e416f72c99ae4`.
Two hash-seed producers exited 0 with byte-identical output, and the separate
seed-2 verifier exited 0. Slurm retained
`220220|COMPLETED|0:0|0:0|237||4G|1|c3n1`. Execution and collection
classifications are
`two-producer-byte-identity-and-independent-baseline-verification` and
`completed-dual-producer-and-independent-baselines-verified`.

The 3,160,729-byte candidate's artifact/document/theorem-record identities
are `4f4965508b63d852697c94fe0e7707759b39c5cf456ec2db8aa5a5afe719f2ad` /
`21f4c7a06dd8b1abf01d8eddd8c1942733f0955141ba682d53229078e15d5e85` /
`6a90eee2d8a306e41b944735940044b142cf1c4f02441133c25c94111e11d336`.
The 16,925-byte verifier's identities are
`50c207c4de0cabe8a50518da4d20e83925f0e1df29ffd78df05e249ea18d4396` /
`ef0dfac8552789bb4dc0e6694a1704c63a8781a93a1f0d9117c6e5c6babcfbd1` /
`87bef2a0d30c789424a15bb257e1bc743f74f4bfa27fb899ab59a44f4d522585`.
Execution artifact/root identities are
`dc3cb3d4dc7dae5f842358b1649f131d019742ebeb732d4cad6e92c827b4f318` /
`c010a79955e93b29651557977001f6f6abff7cd63ba7f1fa1b9deb2a5bc3c08b`;
collection artifact/root identities are
`d1602e23f7736482b039c3d32537fa012d91302f42d62f75ccab9c11583542a9` /
`9f58b68b2fe811cfa82a25395e53b08c01cdd145b57f234d2cde0ca287cf42e5`.

The verifier independently authenticated and empty-context checked all six
baseline artifacts. Artifact SHA-256 and `(bytes / nodes / depth / Cuts)` are:
`odd_add_odd`, readable
`8064d28bd99adbaa1cde42c7ebd0f94880b345c889d6afc18e4b607749310ecc`
`(13,640 / 274 / 31 / 6)` and layered
`3fe6ba0a5ab6ca95a159ddb2d8fa44fd674a0eab4376069b3cc2db9f6c3c2962`
`(12,709 / 269 / 37 / 3)`; `finite_bounded_injective_surjective`, readable
`623865d90504af44cddca3d76ac4f009be8aa289e80d2785b72b121a52954504`
`(1,870,657 / 41,341 / 89 / 1,235)` and layered
`af1410f83a9ab66080a80311d9262341f4cbd4b136a64e889b94c7f12fc342e1`
`(297,637 / 8,355 / 95 / 20)`; and
`beta_product_swap_last_invariant`, readable
`507940a3e456122fadb3b43d34891a70c91baa87615be80c1fca059e9ebd82df`
`(386,189 / 7,413 / 67 / 203)` and layered
`fc08873008eea245be7b8b2961e1a00bf659c25dd257785d2e2345ff29fde9a1`
`(118,018 / 2,011 / 79 / 9)`.

The execution binds 44 route-labeled rejection records from the real
producers. The verifier structurally validates and pairs them into 22 unique
shared compiler observations, but it does not rerun the tactic compiler.
Hence the execution receipt records them as execution-bound, while the
verifier document keeps `producer_observations_execution_bound=false`; its two
independent-negative flags also remain false. These are producer-observed
exact-recipe failures, not independent proofs of dependency necessity.

Exactly 19 nested files are retained under
`artifacts/peano-hydra/a23b-wmi-vector-audit-220220/`, totaling 3,248,650
bytes. The two canonical result files are below `results/`; 17 operational
files retain source, deposit, submission, execution, scheduler, collection,
and bounded logs. Their C-sorted
`<sha256>\t<bytes>\t<relative-path>\n` inventory root is
`e9eec4b239d3f9b870695b51ace1ee8f5667071e52b3d30378ebb056d839476f`.
No top-level result copy, transfer archive, full snapshot, global ledger, job
pointer, or raw job-220218 evidence is retained. The snapshot digest is thus
receipt-bound rather than independently rehashed from a retained archive.
The unauthenticated scheduler row has empty `MaxRSS`, so it supports no peak-
memory or memory-ceiling claim.

The exact retained-result test source is 51,450 bytes at SHA-256
`6a5031239729474a91bb4e1a14d1ebd4639c126e35a307e76805751df0501de4`;
its four tests passed in 2.63 seconds. The CI-sharder file passed 32 tests in
0.25 seconds. The combined bounded source-state, corrected-verifier, WMI-
protocol, retained-result, and sharder release gate passed 81 tests in 17.92
seconds. The 103-entry CI profile gives the result test 3,500 ms and models
eight loads of 541,000 / 541,000 / 540,800 / 541,000 / 541,000 / 541,000 /
541,000 / 541,000 ms.

This completes only the bounded job-220220 execution/retention subgate.
`bounded_three_root_vector_audit_complete` remains false. Independent replay
or certification of the 22 negatives, a genuine optimized-construction
vector and its independent audit, vector/global completeness, minimality,
best-known, publication and publication-union work, graph application, and A2
remain open. Every authority, review, freeze, lineage, and eligibility flag
remains false, and the public graph remains 1,038 edges.

On 2026-08-14, **A2.3c froze only the source protocol and infrastructure for
independent negative replay**. The exact registered campaign contains three
full-vector baselines and 22 unique reverse-order single-omission observations,
then joins each observation to two retained route rows for an exact 44-to-22
mapping. Default CLI operation emits only the canonical source protocol: no
campaign executes, no result exists, and no file is written. At that source
freeze, a real local or WMI replay had not occurred.

The wrapper implementation is separate and runs in a fresh controlled process.
It imports no A2.3b producer, does not call `compile_candidate_body`, and does
not invoke either route-specific assembler. It deliberately shares the pinned
theorem parser, tactic engine, and intuitionistic kernel. Thus wrapper/process
independence can support future independent observation of the 22 exact
script/omission failures, but it does not make those observations independent
route-assembler rejections or prove logical dependency necessity.

The 26,551-byte schema has artifact/semantic SHA-256
`be38f796e9d8923024514962f7cc5a5a4f19c828cf502e2912f1ea5094d12ce4` /
`a0d84c3168a9b779bfb5fdc483a2ec847e4cc34f85bcf8aee4c7351a6363ccb0`.
The replayer module, controlled CLI, and focused test are 91,304 / 49,259 /
87,120 bytes at SHA-256
`f5b5dd45c0ce4e2ed5587fd41b7ea206e92ee05526aebf7be96d80f5bb591aa4` /
`524ced1b5ca78040ddccc3030f2d5eee9f10c8bdf455ea96efb625595c72759b` /
`dc5591dcc9d1e48028d1fbaf31971e65bc10c69377167b50317d4558596e6e82`.
The controlled synthetic/adversarial source gate passed 54 tests in 5.57
seconds. The later execution-infrastructure freeze adds a standard-library-
only, tactic-free structural verifier without running the campaign. Its module,
CLI, and focused test are 85,510 / 16,309 / 23,256 bytes at SHA-256
`33f197045cabe95bda3b7ae0ff871b08cb1b186a861827ea08ad0f76cf7908d8` /
`ab013184633e3ef2b92d8ca9521d39a95646576ea7ede8e53e8b74f6f86ffd05` /
`5edcb9d22d30de7e0e6a7db6be0e4d470ae344634f2141a02652fa1f9b88615c`.
The verifier checks the exact three-baseline, 22-observation, and 44-route-join
structure but executes no tactic, baseline, or negative replay; its focused
gate has 26 tests.

The clean-Git source-state builder/test are 40,801 / 12,372 bytes at SHA-256
`cfe1db8b7a35ca254b135b0c1b55e88c18c8e91b72385594ffed5892a5f964f9` /
`aceb80d04294ad1c87007594187e3b89e9ea553185902bd44ddde6b5db26ab55`.
The WMI runner, Slurm file, submitter, collector, and no-network test are
109,511 / 5,055 / 14,904 / 5,710 / 34,542 bytes at SHA-256
`3db7ed105c016fa58a567d2fc8d8a66a9957f6856133195872d2c8fa455a8306` /
`f2b2cd1879147d5dbf234a5dc7cd49aefd92152a0cd1b02bf67c02d6feb4fc29` /
`b8301b661a36b54446038759d3d7f421e52b0dee352a335facd32e77693f78cc` /
`dee7801fbd7e21e94d483156f5eca52d57b8ec58fa3ba6e108dd7c657fcd99b7` /
`98f35727e1ec22f5c50318acf3a63e5cde094cbb03a9bbfcece2758ac86d6d7b`.
The future execution path must run fresh hash-seed-0 and hash-seed-1 replayers,
require byte-identical candidates, and then invoke the separate seed-2,
standard-library-only tactic-free verifier. It is bounded to one CPU, 4 GiB,
and 15 minutes, with 360-second replayer, 90-second verifier, 16,000,000-byte
JSON, and 16-MiB child-log caps. Timeout, output exhaustion, nonzero exit,
missing evidence, or accounting disagreement is `unknown`; receipts are
published create-only without replacement or symlink acceptance.

The new 11 source-state, 26 verifier, and 28 WMI tests passed as 65 bounded
no-network tests in an independent 18.40-second run. Their conservative
measured CI weights are 6,000 / 9,000 / 6,000 ms; the original source-protocol
test remains 6,000 ms. The 107-entry profile models eight loads of 544,500 /
544,000 / 544,800 / 544,500 / 545,000 / 544,000 / 544,000 / 544,000 ms.

At that source freeze, only source-protocol and execution-infrastructure
readiness was complete; no replay or result yet existed. The later bounded
job-220227 execution and retained-result checkpoint is recorded below.
`bounded_three_root_vector_audit_complete`, `dependency_necessity_established`,
`route_rejections_independently_verified`, and `vector_optimizer_executed`
remain false, as do vector completeness, minimality, optimized-vector audit,
best-known status, publication/publication union, public-graph application, A2
completion, proof/admission/publication authority, and all eligibility claims.

#### A2.3c job 220227 bounded execution and retention

WMI job `220227` ran from clean commit
`a1830b8d019baaec72d1d2b3cc8046c72d22a336`, tree
`2bed15ee16c4c6b3360f4d6a711246e9020cfd9c`, and receipt-bound snapshot
`b8e30114001162ef4a189d702f55844bda4f401abd452d7e212f2aeecdfc3719`.
The retained accounting row is
`220227|COMPLETED|0:0|0:0|89||4G|1|c3n1`. Fresh hash-seed-0 and hash-seed-1
runs of the same replayer exited 0 in 43.924 and 43.784 seconds and emitted
byte-identical candidates; this checks determinism, not implementation
independence. The separate hash-seed-2 structural verifier exited 0 in 0.608
seconds. Execution/collection classifications are
`two-replayer-byte-identity-and-independent-structural-verification` and
`completed-dual-replayer-and-independent-structural-verification`.

The 322,779-byte candidate has artifact/document/theorem-record SHA-256s
`46989ea781e1f66b585c5e0817fdf4e76ba24ff34feec71e9cea2162289f2dba` /
`f17e8c4a2b8080401376ab04f96d771b466946b87b816cb99be54299cbd6a02f` /
`823b26485a1e345aca8b925974641301fd122097c52c05ff842e34b09d44787d`.
Its three full-vector-baseline, 22 independently reproduced wrapper-
observation, and exact 44-route structural-join roots are
`768aa4b5edd9eb44615b62d505944eafd57cdf8fc3f106a43d6168c9be4fc415` /
`6db464c56b52449144f3934214c292dff485910e43421a1763b7203515c0f304` /
`db60c479b5a0c3b621f958e5ef01c98ef095df975a1d51893309ec0cac730ebf`.
The theorem split is exactly 3 / 14 / 5 observations for roots 256 / 376 /
379. Because the independently implemented wrapper calls the shared pinned
parser, tactic engine, and intuitionistic kernel but neither route assembler,
these are independent exact wrapper-level script/omission observations—not
independent rejection of either route and not logical dependency necessity.

The 27,484-byte tactic-free structural receipt has artifact/document/theorem-
record SHA-256s
`48884600840c37044e099683b832659aec1fb22e4068637ad7212c104fe10293` /
`364d4ee4099856c44ee1633439f2e5b1c57ae24cc90d9178cdf7445008504733` /
`fb67221ddc8163cf3c62cabc3d79d0d63d544a485a020c18272cf8af3c605274`.
Execution and collection artifact/root pairs are
`f5c051493fac987a4010043b2bc0b5ef85a8cf37976aff36b331a3c57c93c5b1` /
`60513353afa2539f82568ae4360d98192584920af4bfd530d930e97e94efacdf`
and `2f187bde83cdd2bba97cacb0af0a6dcc4c204e6d0eb224ff5732e2433ed6266d` /
`17421fa3ebdf15020acc2bafad9ce100641d3403b2ce938a9c0b02fc42286814`.
Source-state, Git-receipt, and infrastructure artifact/root pairs are
`4fbcb219cf746da206fb07b99f6149922b761fff551fafd0b28f557bc53bf0b0` /
`832372c5838b2cf3230f5d305ba6b4c9350d165e3c68debe1667f7fa6653722b`,
`42ebb8a353b205916a167de74bf3adc8412f9e16ad2bae8dab9213a7a37b8b8d` /
`85825e1ac8a9e7255fc64afd305bee99d93dac44382dd64e1723483388eeb7b7`,
and `2057bc1ab33e2cd863062bc370bb16b6d8f7022592b7ca73be5b05850282ecce` /
`5fb4363d47b5d0bc55ab68186f158087c3750e0a512361acf9c2d711e0f41f43`.
An isolated hash-seed-31337 audit reran this frozen tactic-free verifier and
reproduced its retained bytes exactly. The verifier still does not execute
tactics, rerun baselines or omissions, bind tactic semantics, or bind the
later execution receipt; those flags remain false.

Exactly 17 nested regular files totaling 419,166 bytes are retained under
`artifacts/peano-hydra/a23c-wmi-negative-replay-220227/`. Their C-sorted
`<sha256>\t<bytes>\t<relative-path>\n` inventory root is
`05d80cae1648769a377d3d5fc429f0edac0f484bd526b2607e236930baf282d0`.
The 282,733,056-byte transfer archive and full snapshot are omitted, making the
snapshot digest receipt-bound. The duplicate seed-1 candidate and both
candidate-valued stdout files are omitted; the retained candidate is their
normalized representative, so post-retention dual-output identity is
execution-receipt-bound. A live batch observation reported `136692K`, but the
retained `sacct` row has blank `MaxRSS`; no retained peak-memory or ceiling
claim is made. The 36,808-byte result gate at SHA-256
`624cefad17d2a419958a5334459121f344c1f941ef229f0bb3db3ef867309ec8`
passed four tests in 0.52 seconds; the 108-entry CI profile assigns it 3,500 ms
and models loads of 544,500 / 544,500 / 544,800 / 545,000 / 545,000 /
545,000 / 545,000 / 544,500 ms. The combined bounded gate passed 155 tests in
25.20 seconds; the CI sharder contributed 32 tests in 0.11 seconds.

This closes only bounded job-220227 execution and exact retention: three unique
baseline records executed in each seed-0/seed-1 run, 22 independent wrapper-
level omission observations, and their structural two-to-one join to 44 route
labels. Route rejection, dependency
necessity, a genuine optimized vector and its independent audit, vector/global
completeness, minimality, best-known status, publication and publication
union, graph application, and A2 remain open. All authority and eligibility
flags stay false; the public graph remains 1,038 edges.

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

- [x] **A2.1 — candidate dependency diagnostic:** expose a non-admitting
      candidate-body compiler that returns the exact dependency-curried target
      and independently checked proof carrier. Over the selected 384-row pack,
      retain a deterministic reverse-order fixed-point leave-one-out audit for
      the exact readable tactic recipe. Block retention on every unknown.
      Domain-separate readable and submitted-construction candidate receipts,
      but do not call either optimized, minimal, best-known, or published.
- [x] **A2.2 — candidate construction rebuild:** rebuild and empty-context
      check the three candidate constructions whose proposed vectors differ
      from their retained declared vectors. Retain them only in a
      candidate-only sidecar: the public library, retained certificates, and
      1,038 construction/publication edges remain unchanged, and the immutable
      A2.1 predecessor keeps its historical rebuild-required field.
- [x] **A2.3a — bounded optimizer protocol only:** freeze a versioned,
      no-default-write program for exactly the three A2.2 roots and exactly
      three constructions per root, with canonical four-axis componentwise
      comparison and a deterministic representative. This checkbox records
      the source/protocol freeze only; it did not itself produce the later
      retained result, frontier, independently audited optimized vector, or
      authority.
- [x] **A2.3a external execution infrastructure (no submission/result):**
      freeze the clean-Git source-state/receipt generator, independently loaded
      kernel verifier, content-addressed one-CPU WMI runner, guarded submitter,
      terminal collector, and their local adversarial contracts. This records
      executable transport readiness only. Test-only writes a remote immutable
      snapshot but creates no job. At the end of this infrastructure tranche
      no test-only outcome or real submission was claimed; the successor item
      records the later job and still grants no authority.
- [x] **A2.3a fixed-pilot execution and retention:** run the frozen three-root,
      three-candidate comparison through two byte-compared producers, a
      separately loaded kernel verifier, and terminal WMI collection; retain
      the exact candidate, verifier, source, Git, infrastructure, execution,
      scheduler, and collection evidence. This checks only the bounded pilot
      comparison set and does not assign `best-known`, minimality, dependency-
      vector, publication, graph, or authority status.
- [x] **A2.3b — bounded dual-route vector-audit source protocol only:** freeze
      exact reverse-order single-omission algorithms for the 22 readable and
      22 proposed-layered route edges across roots 256, 376, and 379, including
      route-specific baselines, shared-preassembly labeling, abort-on-unknown
      semantics, controlled-worker/source identities, and a no-default-write
      CLI. This checkbox records source and synthetic adversarial tests only;
      it does not claim the separately tracked later execution result.
- [x] **A2.3b external execution infrastructure:**
      freeze the producer-independent clean-Git source-state/Git-receipt
      generator, separately loaded six-baseline kernel verifier,
      content-addressed dual-producer WMI runner, guarded submitter, terminal
      collector, and their no-network adversarial contracts. This records
      executable transport readiness only. The later first real attempt is
      tracked separately because it terminated `unknown`, not as a result.
- [x] **A2.3b job 220218 unknown and verifier rerun boundary refrozen:** retain
      the exact fact that both producer bytes matched, preserve the verifier
      provenance mismatch and unknown execution/collection roots, correct the
      independently reconstructed layered provenance expectation, and pin the
      corrected module/CLI in the runner. This grants no scientific negative
      conclusion or result authority.
- [x] **A2.3b job 220220 bounded execution and retention:** execute the fixed
      readable-recipe and proposed layered-construction routes through the
      frozen byte-compared dual-producer path; independently kernel-check all
      six full-vector baselines and verify the structural receipts; bind 44
      routed producer records into 22 shared observations; and retain the
      exact nested 19-file evidence bundle. This closes execution and
      retention only. The negative records are execution-bound producer
      observations, not independently replayed rejections, and
      `bounded_three_root_vector_audit_complete` remains false.
- [x] **A2.3c source-only negative-replay protocol and infrastructure
      readiness:** freeze exactly three baselines, 22 unique reverse-order
      omission replays, and their two-to-one join to 44 retained route rows;
      require an independently implemented wrapper in a fresh controlled
      process without importing the A2.3b producer, calling
      `compile_candidate_body`, or invoking route assemblers; and freeze the
      clean-Git source-state boundary, dual-seed byte-identity runner,
      standard-library-only tactic-free structural verifier, bounded WMI
      transport, fail-closed collector, and create-only receipts. This
      checkbox records only source/synthetic/adversarial and execution-
      infrastructure readiness; the pinned parser, tactic engine, and
      intuitionistic kernel remain shared by the future replayers.
- [x] **A2.3c job 220227 bounded replay execution and retained result:** run
      the frozen three-baseline/22-observation campaign through two fresh
      byte-compared executions of the same replayer, pass the separate tactic-
      free structural verifier, independently reproduce that verifier receipt,
      and retain the exact nested 17-file bundle. This closes only the exact
      wrapper-level observations and structural 44-row join; it does not
      establish route rejection, dependency/vector necessity, minimality,
      vector completeness, optimized/best-known status, publication, A2, or
      authority.
- [ ] Define and independently audit any future true optimized-construction
      direct vector; the A2.3a layered package is not a dependency-selection
      optimizer.
- [ ] Complete the comparison evidence required for any `best-known` or global
      A2 claim beyond the fixed three-candidate pilot.
- [ ] Compile accepted units into reviewable theorem proposals containing
      lineage, dependencies, explanations, scripts, traces, certificates,
      metrics, provenance, and Book/vault/Explorer previews.
- [ ] Produce a patch/PR only on explicit export. No unreviewed theorem enters
      `TheoremSpec` or a public catalog.
- [ ] Require deterministic documentation and leave-one-out checks for both
      readable-proof and optimized-construction dependency vectors; verify and
      publish their ordered union as the theorem graph edge set.
- [ ] Complete the remaining A2 review, lineage, freeze, publication,
      authority, and eligibility gates only after the vector and comparison
      evidence above is independently complete.

### A3 — Hybrid native/Vampire assistance

- [x] **A3.0 — untrusted executable vertical slice:** deterministically emit
      classical TPTP FOF from one closed primitive-PA goal and an explicit
      premise allow-list, retain a source-symbol map, and parse bounded SZS
      output as inert evidence. Reconstruction v3 emits only ordinary checked
      public commands for three fixed shapes: top-level reflexivity gives
      `refl`; one explicitly selected PA axiom gives `apply NAME`; one
      explicitly selected public theorem gives `use NAME; apply NAME`; and a
      top-level conjunction with exactly two selected PA axioms in branch order
      gives `split; apply NAME1; apply NAME2`. Every other multi-premise case is
      commandless. Fake executables continue to test the copied-and-rehashed
      direct-binary boundary, problem bytes, arguments, wall timeout, rollback,
      and output ceiling independently of a solver installation.
- [x] **A3.1 — real-solver diagnostic reconstruction:** temporarily download
      the official Vampire 5.0.1 macOS ARM64 release, verify the ZIP and
      executable identities, run the direct untrusted boundary, reconstruct
      public commands offline, and require fresh original-goal kernel replay.
      The ZIP/executable SHA-256 values are
      `8c92e649fe7bc622a70000afbdf5a5c51007b384e2d8b8235c95474cc7a68f35` /
      `b5168c690e0293cdac78f16d8418d7eeabcd6708f90a60cd2bf45313b6d98699`;
      neither file was vendored or installed.
      The `0 + 0 = 0` / `PA3` diagnostic returned inert `SZS Theorem`,
      reconstructed `apply PA3`, and produced a checked 2-node, depth-2 proof.
      Its canonical `encode_proof` SHA-256 is
      `25b6f555180e9737fe4aeb0e51f1f9e97911ed9ffc41c6a80ef97088930711cd`;
      its complete `peano-lab-v2` artifact SHA-256 is
      `3c65761490733d3382932780f26ff2fb382f82eb536a45af41840b172be7efca`.
      The ordered `PA3`, `PA5` conjunction TPTP SHA-256 is
      `60b2666d452d253bd982170cc8c3d586c2be836ee72355a4fc108d313d403f96`;
      the diagnostic returned inert `SZS Theorem`, reconstructed
      `split; apply PA3; apply PA5`, and produced a checked 5-node, depth-3
      proof. Its canonical `encode_proof` SHA-256 is
      `3d47f7636f578cbcaf638006942e19c8ff9c565359967d44b32d20668ef5f812`;
      its complete `peano-lab-v2` artifact SHA-256 is
      `cc520fd2f72148dc05450c414151a55cca4a18ce528e15bb150d9ea89e493d68`.
      A pinned x86-64 binary on WMI (SHA-256
      `81532e088c4ee1238d7ea1d8e868a2dccf8d358ad4d2126d257b4dda7f2e6bd9`)
      independently returned `SZS Theorem` for the same conjunction under
      `--mode vampire`, reporting 0.001 seconds and 8 MB.
      `scripts/peano_hydra_vampire_assist.py` now exposes this as a one-shot
      JSON preview: it resolves only explicitly named PA/public premises,
      runs the bounded direct diagnostic, replays reconstructed public
      commands twice from the original goal, and accepts only an independent
      kernel-checked certificate. It writes no artifact by default and marks
      H0 containment, live registration, and every eligibility flag false.
      These are direct/offline diagnostics, not a registered live `Dispatch`,
      production integration, portfolio result, or capability advantage.
- [x] **A3.2 — transactional live-session preview outside frozen H0:** add
      `training/peano_hydra/vampire_live.py` as a host API which accepts an
      immutable `MacroOwner`, an explicit ordered premise tuple, and one exact
      host-owned `VampireLiveSolver`. The host copies and rehashes that pinned
      executable and starts Vampire as its sole bounded child, without a
      source/JSON broker or shell. `run_vampire_live` accepts only a focused
      closed goal with no variables or context in this preview. Raw SZS output
      remains inert; only the v3 reconstructor's ordinary public commands may
      advance a temporary owner. Every rejected phase returns the identical
      owner, and every closed successor passes a fresh replay and independent
      kernel check against the owner-held original theorem. Open checked
      progress may commit without being called QED.
      `training/peano_hydra/interactive_assistant.py` joins this path with
      manual public tactics and proposal-only Qwen data through
      `start_hydra_assistant`, `run_manual_tactic`,
      `run_vampire_assistance`, and `resolve_qwen_premises`. The terminal host
      `scripts/peano_hydra_assistant_repl.py` exposes `:goals`, `:script`,
      `:qwen`, `:model`, `:accept`, `:resolve`, `:vampire`, `:discard`,
      `:undo`, `:help`, and `:quit`; it deliberately loads neither a model nor
      a network client. An unretained diagnostic run with the official
      Vampire 5.0.1 conjunction binary returned inert theorem status and
      reconstructed exactly
      `split; apply PA3; apply PA5`, which fresh original-goal replay accepted.
      This is a functional A3.2 preview, not production/browser integration,
      a registered H0 `Dispatch` adapter, or evidence of a solver advantage.
- [ ] Resolve the frozen H0 `Dispatch` one-process topology before registering
      a source broker plus a separate Vampire process, or supply one reviewed
      self-contained executable. Do not weaken or silently reseal H0.3.
- [ ] Run deterministic native closure before bounded Vampire `Dispatch`.
- [ ] Reconstruct every useful hint through ordinary Peano macros, record all
      calls, and compare solve/resource AUC against native-only search.

### A4 — Qwen LoRA assistance

- [x] **A4.0 — bounded proposal bridge preview:** add
      `training/peano_hydra/qwen_hydra_bridge.py` with exact
      `QwenHydraRequest`, `QwenHydraAuthority`, and `QwenHydraProposal` values,
      a canonical prompt, an exact-field strict-JSON terminal response
      contract, finite premise/action/command/theorem allow-lists, typed-macro
      compilation, and stale request binding. The Python bridge also accepts
      one bounded canonical `premises:`/`macro:` line protocol; the terminal
      `:model` command accepts strict JSON only. The interactive owner retains
      the exact response
      bytes and re-parses them before execution, so a caller-forged proposal
      object cannot acquire premise-selection provenance. Model output has
      `authority = none`, cannot mutate
      a proof session, and can reach proof execution only after explicit host
      acceptance. `propose_with_transport` bounds prompt and response bytes;
      the supplying host must separately enforce wall time, memory, network,
      and process containment. A validated Qwen premise selection may be
      handed to the A3.2 direct-child Vampire path, whose status is still inert
      and whose reconstructed commands retain transactional and kernel gates.
      No trained-Qwen live inference was run: model-v3 speaks the historical
      next-tactic contract rather than this premise-plus-typed-macro proposal
      contract, and WMI was unreachable during the integration session. This
      is interface plumbing, not current Qwen capability evidence.
- [x] **A3.2/A4.0 focused verification:** the disjoint terminal/Qwen/session/CI
      gate passed 59 tests in 11.75 seconds, and the direct-child
      Vampire/reconstructor/frozen-macro gate passed 91 tests in 14.98
      seconds. Ten focused Book tests and the command-replay gate also passed.
      The real-binary terminal smoke exported
      `split; apply PA3; apply PA5; qed`; this was an unretained diagnostic
      observation, not a deterministic campaign artifact.
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
- [x] A2.1's candidate dependency diagnostic is retained without changing any
      admitted theorem or graph edge. Two complete 384-row builds were
      byte-identical. The sidecar records 3 kernel-accepted exact-recipe
      omissions, 1,057 exact-recipe rejections, 0 unknowns, and 3 rows marked
      by its immutable historical rebuild-required field; the A2.2 successor
      below now discharges that obligation without rewriting A2.1. The
      candidate vector has 1,035 edges while the retained vector remains
      1,038. Its artifact/document/theorem-
      record identities are `4b867bb1ce0161e6…` /
      `12166de8fb0cc028…` / `8ae5553e79b15c4e…`. Twenty-six focused tests
      passed. This is diagnostic evidence only: minimality, best-known,
      publication, freeze, training, retrieval, and evaluation remain false.
- [x] A2.2's candidate-only sidecar closes all three changed direct vectors
      with pinned replay-pack certificates and checks every rebuilt theorem
      from the empty context against its original statement. Its three direct
      candidate vectors contain 22 rather than 25 edges; descriptive deltas
      are -49,483 canonical artifact bytes, -1,176 proof-tree nodes, and -34
      Cuts. The exact sidecar/artifact roots are `6176c44a63f791bc…` /
      `91ecc6b4bb22f4b4…`, and its theorem-record root is
      `42d718621f91b52b…`; 23 focused tests passed in 44.12 seconds. This does
      not alter the 1,038-edge public graph, each omitted direct name remains
      transitively reachable, Python alias metrics are non-comparable, and all
      authority/minimality/optimized/best-known/publication/eligibility flags
      remain false.
- [x] A2.3a froze the bounded three-root, three-candidate optimizer and
      comparison protocol before execution. The exact schema
      semantic/artifact pair is `07e5842c221fe843…` / `006d38ef781fc022…`;
      the program/CLI/focused-test source identities are
      `7ac7d784c3660c1…` / `3acbd3ec0f190699…` /
      `d5ae3e830573c7a5…`, and 59 focused tests passed in 0.31 seconds. This
      source/protocol subgate is distinct from the later retained result.
- [x] A2.3a's external execution infrastructure now binds a clean committed
      producer source state, an independent kernel-only verifier, deterministic
      dual-producer execution, and terminal WMI collection. Its source-state,
      verifier, and WMI protocol gates pass 52 tests in 8.45 seconds; the WMI
      file alone passes 18 in 0.72 seconds. The earlier independent threat
      audit reported no blocker before the final route refreeze. That tranche
      records infrastructure readiness only; its successor below records the
      real bounded execution.
- [x] WMI job `219765` executed and retained the frozen three-root,
      three-candidate A2.3a pilot. The dual producers were byte-identical, the
      independent verifier accepted 9/9 artifacts, and terminal collection
      classified it `completed-and-independently-verified`. Candidate,
      verifier, execution, and collection artifact/root identities begin
      `3e989784…` / `90a3d97a…`, `6a794214…` / `e21290f6…`,
      `779a9712…` / `7a597563…`, and `25e616fc…` / `52339b92…`.
      All three fixed frontiers contain the A2.2 direct and layered members;
      the deterministic representative is layered. This closes only bounded
      execution and its 19-file evidence retention. The transfer archive is
      absent and not independently rehashed; `sacct` is unauthenticated,
      `MaxRSS` is absent, and no memory ceiling is claimed. Every global-best,
      minimality, vector-audit/completeness, publication/union, A2, authority,
      review/freeze, and eligibility flag remains false. Its exact retained-
      result gate passed 4 tests in 3.40 seconds (source SHA-256
      `28b251f9ab75bea…`).
- [x] A2.3b froze the next bounded source protocol before executing it. It
      fixes roots 256/376/379, two separately domain-labeled construction
      routes, 22 ordered direct edges per route, and 44 reverse-order
      single-omission attempts. The schema semantic/artifact identities begin
      `6782197c…` / `c4af0d2f…`; its 44-file implementation-source root begins
      `4260928c…`; and the producer/CLI/test identities begin `3f2c9df0…` /
      `29f56547…` / `6c3a0490…`. Seventy-eight synthetic tests passed in 2.24
      seconds. That source-only checkpoint granted no result, publication
      union, graph change, or authority; the later job 220218 remained unknown
      at independent verification. All vector-audit/completeness,
      independence, best-known, A2, and eligibility flags remain false.
- [x] A2.3b external execution infrastructure is frozen. The independent
      verifier kernel-checks all six
      full-vector baselines and recomputes structure, while labeling the 44
      producer route records as 22 shared compiler observations that it does
      not independently replay. Job 220218 produced byte-identical producer
      candidates but stopped at a verifier provenance mismatch, so its
      execution/collection receipts are `unknown` and imply no negative
      scientific result. The corrected rerun boundary passes 10 source-state,
      13 verifier, and 22 WMI tests: 45 in 15.27 seconds. The corrected rerun
      result is tracked separately below; no vector/A2/authority claim follows
      from infrastructure or job 220218.
- [x] A2.3b job `220220` completed the bounded execution-and-retention
      subgate from clean commit `720021ae…`, tree `03383d9b…`, and snapshot
      `64266e10…`. Two producers were byte-identical and the separate verifier
      independently checked all six kernel baselines and the structural
      receipts. Candidate/verifier artifact-root pairs begin
      `4f496550…` / `21f4c7a0…` and `50c207c4…` / `ef0dfac8…`;
      execution/collection pairs begin `dc3cb3d4…` / `c010a799…` and
      `d1602e23…` / `9f58b68b…`. Exactly 19 nested files totaling 3,248,650
      bytes are retained at inventory root `e9eec4b2…`. The 44 route records
      are paired into 22 shared execution-bound producer observations, not
      independently replayed negatives. The public graph remains 1,038 and
      `bounded_three_root_vector_audit_complete` remains false.
- [x] A2.3c source-protocol and execution-infrastructure readiness is frozen
      for exactly three baselines, 22 unique observations, and the two-to-one
      44-route join. The independent wrapper/fresh-process boundary imports no
      A2.3b producer and calls neither `compile_candidate_body` nor a route
      assembler, while explicitly sharing the pinned parser, tactic engine,
      and intuitionistic kernel. Schema artifact/semantic identities begin
      `be38f796…` / `a0d84c31…`; module/CLI/test identities begin
      `f5b5dd45…` / `524ced1b…` / `dc5591dc…`. Its 54 controlled tests passed
      in 5.57 seconds. The separate verifier identities begin `33f19704…` /
      `ab013184…` / `5edcb9d2…`; source-state identities begin `cfe1db8b…` /
      `aceb80d0…`; and runner/Slurm/submit/collect/WMI-test identities begin
      `3db7ed10…` / `f2b2cd18…` / `b8301b66…` / `dee7801f…` / `98f35727…`.
      The 65-test no-network infrastructure gate passed in 18.40 seconds. This
      is a source-and-infrastructure-only, no-network/no-job/no-result
      checkpoint.
- [x] A2.3c job `220227` completed the bounded replay-and-retention subgate
      from commit `a1830b8d…`, tree `2bed15ee…`, and receipt-bound snapshot
      `b8e30114…`. The same replayer under seeds 0/1 emitted byte-identical
      322,779-byte candidates at artifact/root `46989ea7…` / `f17e8c4a…`;
      the tactic-free structural receipt is 27,484 bytes at artifact/root
      `48884600…` / `364d4ee4…`. The run accepted three baselines and
      independently reproduced 22 exact wrapper-level omissions, then joined
      them structurally to 44 retained route labels. Exactly 17 nested files,
      419,166 bytes, are retained at inventory root `05d80cae…`. Route/vector
      necessity, completeness, minimality, optimized/best-known status,
      publication, A2, authority, and eligibility flags stay false.
- [ ] A0/H1.0 and H1.1 remain open. The candidate pack deliberately records
      declared publication dependencies and source-stage sharing observations,
      not separately completed readable/optimized construction vectors,
      best-known certificates, complete deployed-page/document receipts, lineage
      masks, source-state/owner freeze receipts, or a sealed benchmark. All
      384 rows retain pending review, lineage, best-known, dependency-vector,
      and publication-union gaps. H1.1b2 reports selected API coverage
      separately from deployed-page coverage while preserving metadata v1;
      H1.1b3 retains page source without claiming deployment; A2.1 adds only a
      readable-recipe dependency diagnostic; A2.2 adds only three checked
      candidate construction rebuilds; A2.3a retains only the bounded
      fixed-set comparison with layered closures; and A2.3b freezes the three-
      root/two-route/44-attempt vector-audit protocol. Its first attempt
      remained unknown; job 220220 later completed only corrected bounded
      execution, six-baseline verification, structural checking, and
      retention; A2.3c froze the independent-negative-replay source boundary;
      and job 220227 later completed only its bounded three-baseline,
      22-wrapper-observation, 44-row-join execution and retention.
      The immediate A2 work is to define and independently audit a genuine
      optimized-construction vector, establish any separately claimed route or
      dependency necessity, complete the evidence needed for a best-known/
      global comparison, and derive the
      verified publication union before a
      source-state request to an external owner. No 200-unit gold corpus,
      registered live-Vampire
      `Dispatch` route, production Vampire integration, capability comparison,
      new Qwen training, classical Hydra profile, or Rust authority claim is
      yet complete. A3.1 records direct/offline real-binary diagnostics;
      A3.2/A4.0 add only a non-H0 functional terminal preview and proposal
      boundary.
