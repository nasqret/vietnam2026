# Peano Hydra — binding design

**Status:** binding campaign and product architecture; H0 semantic and
functional core completed 2026-08-04, H1/A0 contracts and epoch freeze open

**Implementation plan:** [`PLAN/11_peano_hydra.md`](../PLAN/11_peano_hydra.md)

**Parent architecture:** [`docs/PEANO_LAB_DESIGN.md`](PEANO_LAB_DESIGN.md)

Peano Hydra is both a living arithmetic workshop and a falsifiable experiment
in neuro-symbolic theorem proving. Its only object language is Peano Lab. The
workshop grows a reviewed elementary-number-theory library and turns accepted
mathematical prose into precise statements, checked proofs, exact dependency
graphs, and linked documentation. The experiment asks whether sparse Qwen
guidance improves a strong native/Vampire prover under matched resources. No
part of either mission licenses a weaker trust boundary or a claim that full
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

### 1.1 Living-library and authoring mission

The one-shot experiment is not the whole product. Hydra SHALL maintain three
separable lanes:

1. the Peano Lab language, Python authority, Rust acceleration, and Lean
   metatheory;
2. a continuously growing reviewed library plus live proof-document authoring;
3. a frozen Vampire/Qwen research campaign with lineage-safe evaluation.

The first two remain useful if lane 3 reports no demonstrated LLM advantage.
The public authoring surface contains only ordinary mathematical prose,
readable defined PA notation, its exact primitive expansion, Peano Lab proof
states/tactics, dependencies, and certificates. TPTP, Vampire proof objects,
SMT-LIB, Lean syntax, and model protocols are internal and MUST NOT become a
second library language.

`authoring-live` follows the newest reviewed library epoch and may improve
continually. `research-eval` uses exactly one copied, content-addressed epoch,
lineage mask, benchmark, solver configuration, and model configuration. No
artifact from living HEAD may cross that boundary after the research epoch is
sealed.

## 2. Non-negotiable laws

### 2.1 Kernel law

Only `peano_lab/kernel/checker.py` may admit a positive theorem. Every reported
QED MUST be replayed from the empty context against the **original stated
formula**, not a tactic-rewritten surrogate. Declared contexts are permitted
only for intermediate search judgments and never for library admission or a
scored theorem. The certificate
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

The existing native/WASM Rust implementation is a diagnostic and acceleration
shadow, not a second authority. A Lean proof about a handwritten checker plus
finite differential tests does not prove the exact Rust program correct.
Future Rust authority requires the K5--K11 protocol, algorithm-soundness,
source-refinement, and dual-soak gates in
`PLAN/12_peano_kernel_acceleration.md`, followed by a separate binding-design
amendment. Until then, Rust may reject or filter candidates cheaply, but
Python performs the final original-goal check for every published QED.

### 2.2 Fragment law

H0 MUST publish one machine-readable language profile containing:

- the exact term and formula grammar;
- binding, substitution, and alpha-equivalence conventions;
- intuitionistic proof rules and the permitted arithmetic axioms/schemata;
- whether induction is unrestricted, syntactically bounded, or absent;
- the accepted input normal forms and every validity-preserving translation;
- resource bounds that are part of the decision claim, if any; and
- the semantics and evidence format for `proved` and `unknown`; and
- for any separately registered decision profile, the additional semantics
  and independent evidence format for `not_theorem`.

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

Peano Lab remains the sole object language in every future profile. The
constructive profile v2 is immutable and remains the default. A future
classical campaign MUST register a different profile and artifact identity for
the existing `PA+DNE` checker. Excluded middle, `A \/ ~A`, may be exposed as a
derived classical theorem or tactic; it is not casually added as a second
kernel primitive equivalent to DNE. Every theorem, dependency, prompt,
document, and checked result carries its logic mode. Until K5,
`peano-lab-v2` certificate bytes do not carry logic internally; their
owner-held verification request and result receipt bind the mode. Version 3
will place it inside the canonical artifact. Constructive results
may be imported into classical sessions; classical results and DNE nodes MUST
be rejected in constructive sessions.

Readable defined notation is permitted only with deterministic conservative
expansion receipts into the primitive grammar. Neither Vampire translation nor
model syntax enlarges the language.

### 2.3 Library-epoch law

Hydra does not evaluate against a moving theorem library. The living library
may continue at reviewed `authoring-live` HEAD, while H1 physically freezes an
ordered epoch `L0`, initially the complete independently checked public
catalog available at campaign start (at least the current 384-theorem
entries). Its content root MUST commit to, for every entry:

- stable name and canonical statement;
- ordered readable-proof dependencies, ordered optimized-construction
  dependencies, and their deterministic publication union;
- authored source or proof-script hash;
- independently checked certificate hash;
- node count, distinct objects, Cuts, bytes, maximum depth, and replay
  observation;
- readable source proof and best-known optimized certificate identities;
- source prose, explanation, definition-expansion and documentation receipts;
  and
- declaration order and logic/profile identity.

The self-contained certificate has no trusted external theorem names, but its
construction lineage still records which prior theorems were imported before
expansion. Leave-one-out replay checks each declared per-artifact vector. The
public dependency graph and lineage masks use the deterministic union, so an
optimized certificate cannot hide an authored dependency and a readable proof
cannot hide an optimizer dependency.

Training may use eligible material from `L0`; the final benchmark may not.
New mathematics belongs to `L1`, `L2`, and so on. It may immediately improve
`authoring-live`, but cannot enter the active campaign's prompts, retrieval
index, imports, generated documentation context, training corpus, or headline
test. The frozen pack MUST NOT resolve a path back to living catalog files.
Starting a new research epoch requires sealing a new benchmark before
examining outcomes. The current public library is a capability and training
resource, not a hidden test set.

#### Candidate replay transport implemented in H1.1

Replay-pack schema v1 implements the certificate-transport subgate without
pretending to complete the epoch freeze. It is a subordinate format beside the
historical three-file epoch-protocol v1, which remains byte-compatible and
provenance-only. The new pack has exactly four non-certificate files—canonical
schema, source catalog, constructive semantic profile, and manifest—and one
raw canonical `peano-lab-v2` artifact for every theorem. Schema semantic digest
is `d60b07fe68aa4ba023c9bb873e2df4190752f70252caca21da7e76dcd393f02d`;
the exact schema-document SHA-256 is
`cfd0959ec537c9a7e3cdf705bd48ff7f8301fbd43f63623934d4638cb712b2ef`.

The verifier is intentionally separable from candidate construction. It
imports only standard-library code and the Peano kernel/codec; imports of the
theorem library, tactic engine, UI, training package, Torch, and Transformers
are blocked in the retained worker. Before reading any theorem artifact, it
validates the exact canonical manifest, type-exact versions/counts/indexes,
ordered prior-only dependencies, safe content-addressed paths, aggregate byte
and tree-resource ceilings, schema/profile/catalog identities, deterministic
roots, exact directory membership, and the source identity of the package
initializers, kernel, decoder, verifier, and worker CLI. It rejects symlinked
roots and final components, bounds directory enumeration, reads bounded regular
files with `O_NOFOLLOW | O_NONBLOCK`, and rechecks exact directory and
verifier-source identity after replay. The worker requires isolated/no-site
mode plus an explicit fresh repository bytecode-cache subtree. Its report path
is checked before and after replay with conservative Unicode-normalized,
case-folded containment, so it cannot overwrite the pack on case-insensitive
filesystems.

For each theorem it hashes the exact artifact bytes, decodes every constructor
under byte/node/depth/integer bounds, and requires byte-for-byte canonical
re-encoding. It independently parses the source statement as a closed formula,
requires equality with the decoded owner target, recomputes formula/proof
hashes and tree nodes/depth/Cuts, and finally calls
`check((), proof, original_target)` in intuitionistic mode. A DNE artifact may
be decoded as inert syntax but cannot pass that final judgment; the adversarial
control is accepted by the separate classical checker and rejected here.

`peano-lab-v2` serializes a proof tree and does not preserve Python object
sharing. Consequently nodes, depth, Cuts, formula/proof hashes, bytes, and
kernel acceptance are freshly reconstructed from packed bytes. Distinct object count,
unique proof edges, and reused references remain catalog-bound source-stage
observations, with explicit graph invariants; they are not presented as
pack-reconstructed facts. The source `repr` hash remains provenance only and
is not an authoritative portability check.

The retained candidate has 384 artifacts totaling 80,088,767 bytes, manifest
root `fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d`,
and theorem replay root
`88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba`.
Its builder publishes atomically only after a new
`python -I -S -X pycache_prefix=<fresh-dir>` process has replayed every theorem
with the forbidden-import guard active. The committed acceptance test repeats
that full replay and requires byte equality with the retained report.

This is precisely a **replay-complete candidate-`L0` pack validated in an
isolated fresh interpreter**. It is not production `L0`: the manifest enforces
`status = candidate` and `evaluation_eligible = false`. H1.1 still needs
separate readable and optimized direct-dependency vectors with leave-one-out
evidence, deterministic publication union, complete definition/document
receipts, lineage controls, reviewed Git-state provenance, independent owner
deposit, and benchmark sealing. Declared dependencies are therefore described
only as publication dependencies, and no certificate is called minimal or
best-known.

#### Candidate epoch-metadata ledger implemented in H1.1a

H1.1a adds a strict, deterministic readiness ledger above the replay transport;
it does not mutate replay-pack v1 or the historical epoch protocol. Metadata
schema v1 has semantic digest
`71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c`
and exact schema-document SHA-256
`9867378c8802501d2120ad4d94a86378815cf90b003eafc92b164685da61c956`.
The canonical candidate is 5,880,054 bytes and has root
`b2f397cec26d5f22bf0806da1f6e219d26bb5e319a503395150d9278efae8279`.
Its schema fixes `status = candidate`, `freeze_ready = false`, and
`evaluation_eligible = false`; there is no field by which the builder can mint
owner authority.

The ledger pins the exact retained replay manifest, verification report,
catalog, replay root, constructive profile, source commit
`32803924d7def862ccf0b738cd1ed494a3165f7e`, and source tree. In replay order it
records all 384 theorems, 1,038 declared publication edges, 384 source
locators with file hashes and declaration lines, statements, scripts, proof
and construction metrics, certificate identities, and explicit unresolved
fields. The submitted artifact is not called best-known or minimal. Readable
and optimized direct-dependency vectors, leave-one-out receipts, and their
publication union remain null rather than being guessed from the declared
publication vector.

Documentation receipts distinguish presence, staleness, and absence. All 384
vault notes and atlas cards join the replay rows, so their missing and stale
counts are zero. The atlas uses immutable commit `32803924…`; all 1,536
source, vault, snapshot, and research links were audited as commit-pinned Git
blobs. The explicit and defined proof-explorer corpora each contain 557 rows,
but only 240 public rows join the 384-theorem candidate. The other 317 names
are disjoint non-`L0` material and are provenance only: the full corpora MUST
NOT be exposed to this epoch's training, retrieval, or evaluation. Explorer
and definition receipts are physically absent for the remaining 144 candidate
names, so their exact counts are 144 missing and zero stale. Consequently
`documentation_complete_count = 240`; completeness requires a source locator,
definition receipt, atlas card, vault note, explicit explorer row, and defined
explorer row for the same theorem.

All 384 rows still record pending human review, lineage, best-known comparison,
readable and optimized dependency-vector evidence, and publication-union
evidence. Thus H1.1 remains open. The next internal repair is to generate and
audit the 144 missing explorer/definition rows and let A2 bind comparison and
optimization evidence. Only after that repair should Hydra create a reviewed
source-state freeze request for an external independent owner; benchmark
activation remains a later, separate authority event.

The H1.1a implementation gate comprises 53 focused adversarial tests. It
rebuilds deterministically, checks the exact retained pins and joins, rejects
fully rerooted and authority-escalating mutations, excludes the 317 non-`L0`
explorer rows, exercises bounded no-follow reads and source/report drift, and
verifies the no-default-write CLI. Passing this gate establishes protocol
behavior only; it grants none of the missing review or owner authority.

#### Isolated selected documentation bundle implemented in H1.1b1

On 2026-08-09, H1.1b1 repairs the selected API generation boundary without
rewriting the historical proof explorers. Reusing the 557-row QR corpus by
filtering its row objects would not have been a sound epoch operation: the
legacy public rows carry `dependents` arrays containing 757 name references
into the 317-row disjoint candidate corpus. Filtering only the top-level rows
would therefore leave foreign names in an apparently 384-row document. Binding either complete
explorer artifact hash would be subtler but still wrong, because a change to a
disjoint theorem would reseal the selected epoch surface.

The replacement is a separate, tagless, replay-ordered candidate bundle. It
starts from the exact retained replay manifest and reconstructs each record
fresh from source-hash-verified `TheoremSpec` values. Dependencies and
references are checked against that selected 384-name namespace. It never
copies legacy row objects, global PA tags, `dependents`, links, scopes, closure
fields, or full-corpus hashes. No theorem name or body from the 317-row
candidate set and no hash of either legacy explorer enter an authoritative
bundle root. The existing 557-row explicit/defined surfaces, tag registry, and
metadata-v1 ledger remain unchanged historical evidence.

This isolation also exposed an import boundary. `defined_edition` formerly
loaded the complete quadratic-reciprocity stack as soon as the per-theorem
compactor was imported. That eager import made a harmless compaction API load
non-selected theorem bodies. The stack import is now local to
`defined_library_edition()`: importing `compact_theorem_spec` loads only the
compactor and its exact term/formula dependencies, while explicitly asking for
the historical 557-row edition still loads the wider stack.

The closed layout has exactly five canonical files in
`artifacts/peano-hydra/l0-documentation-candidate-v1/`:

- `schema.json` fixes closed object shapes, exact source bindings, bounds, and
  the candidate-only claim boundary;
- `explicit.json` contains the fresh replay-ordered tactic/source records;
- `defined.json` contains exact-AST-checked conservative notation receipts;
- `isolation-receipt.json` checks order, membership, fields, and internal
  dependency closure; and
- `manifest.json` binds the other four files and their source identities.

The explicit document has 384 theorem records, 1,038 ordered declared
dependency edges, and 13,862 tactic lines over 20 tactic heads. It records
3,989 theorem-reference occurrences: 1,035 declared edges are explicitly
referenced and three remain implicit declared edges. The selected graph has 22
levels, maximum depth 21, 55 foundations, and 100 terminals. The defined view
serializes 40 definition records while pinning the complete 43-entry parser
registry. Exact compaction changes 321 statements and 624 of 950 local
propositions, records 2,027 definition occurrences, reduces statement text
from 224,948 to 29,098 characters, and reduces local-proposition text from
148,105 to 25,733 characters. These are presentation receipts; exact AST
expansion, not shorter text, is the safety criterion.

The retained identities are:

- schema semantic digest
  `30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d`
  and artifact SHA-256
  `a442e89ac312302dcee777b5741ca7f2d67e10f6ebcc996b8096fc6061c28a9c`;
- explicit root
  `b7942fa5a866ff7cd8a38f30c93787ec0abd2948e69710651e4d3578e64377da`
  and artifact SHA-256
  `f1c9f364db0cb7ae7f4c7fe065b1ef48d5522fc49711667479ec3dc4db723936`;
- defined root
  `897fd5e4bedb44b63853e428ff5bc2e2c273e30a0c239450e0ec8f93d73fc61f`
  and artifact SHA-256
  `164b34dd0cad555baf2164ee3da114fb60a447bd667112481e7225097dd17cea`;
- isolation root
  `64bdc2c52bcaf88d26382bbe514be4a442cc876b8df2a353c272587e1516d919`
  and artifact SHA-256
  `8c8a6882d0d5a82552942fc0c3efe5a900244a9cad02c32b24cabe3d86a0eee6`;
  and
- manifest root
  `8f7ef8fcca69bc6f5f8b39c220293b8414a65fd81576c584f78e59da104d46a4`
  and artifact SHA-256
  `5ded97c27b859cc4725362bc76aba89fac06c5f11843b50529b78050b19348bf`.

The first focused gate passed 36 tests in 126.87 seconds. After final retained
pins were installed, seven targeted retained-artifact tests passed with 36
deselected in 7.10 seconds. Final acceptance then passed all 43 focused tests
in 115.64 seconds and 23 compatibility tests in 18.19 seconds. These gates
establish implementation compatibility, not any broader authority claim.

This is an H1.1b1 **candidate selected-API record bundle**, not deployed proof-
explorer pages, owner freeze, source-state deposit, human review, minimality,
best-known status, readable/optimized dependency evidence, publication union,
A2 output, or permission for training, retrieval, or evaluation. H1.1 remains
open. Metadata v1 must continue to report its historical 240-complete join.
The next sub-slice is H1.1b2: metadata v2 will bind this bundle and report
selected API coverage separately from deployed-page coverage.

#### Additive candidate metadata successor implemented in H1.1b2

H1.1b2 introduces a new ledger rather than resealing metadata v1. The v1
artifact remains the exact historical observation that 240 replay theorems
joined the then-existing explorer surfaces. Version two reads that canonical
artifact as an opaque, byte-pinned predecessor; it never imports or invokes
the v1 builder and never reads the mixed 557-row explorer corpora. It joins
each predecessor row, in replay order, to the exact explicit and defined
records in the isolated H1.1b1 bundle.

The join is semantic, not name-only. It checks statement source and canonical
hashes, formula identity, source locator, catalog layer, readable script,
explanation, declared dependencies, and minimality flag. Defined rows are
also tied to their explicit-row hash. Every definition use binds the stable
definition ID, registered name, canonical registry order, positive occurrence
count, and the retained aggregate of 2,027 occurrences. A per-row predecessor
hash, selected-record hashes, definition-use preimage, v2 theorem-record hash,
ordered 384-row root, and whole-ledger root make those joins independently
addressable.

The three documentation quantities deliberately remain different:

- selected API completeness is 384 rows;
- deployed-page completeness is the exact intersection where both historical
  explicit- and defined-page receipts are present, namely 240 rows; and
- each deployed presentation surface still has 144 pending rows.

Machine documentation therefore closes the selected API gap without
pretending that pages were deployed or reviewed. Human review, lineage,
readable and optimized dependency vectors, deterministic publication unions,
best-known comparison, and owner authority remain pending for all 384 rows.

Schema v2's semantic digest is
`498dde0a3b4f762197d8c371609dfac2eabf7edcfc37a6d3c5cdf6ca21efb38a`
and its exact artifact SHA-256 is
`27af1e5c1ee0e73cb012db3d8b94cb9a6e1be48d08e8158ad48b8edac399973e`.
The retained candidate is 3,732,032 bytes, artifact SHA-256
`dc6a59ce08397eba698651f6ed4faac0533dec55c13d5a8ca49d863d19d7b72d`,
semantic root
`e0c1d3683e111d7f2883cebbc423694159e82d95471d9375866a81ec596dfb9e`,
and ordered theorem-record root
`22330158f52f049ec920992f51f96a0ab0e9939c3eeb893f533616c17b48e98a`.
The 1,891-byte readiness artifact is
`f257646d1ba5b51835c8b1718538b4b21c89ea402ba073a9630842708db0206b`.
It is derived only after full fixed-source reconstruction and binds both the
metadata root and exact metadata artifact hash.

The loader rejects noncanonical, oversized, nonregular, final-symlink, and
symlink-ancestor inputs. The CLI writes nothing by default, supports explicit
read-only checks, and publishes explicit outputs with a same-filesystem
create-if-absent hard link. Inode-checked rollback preserves a destination
created by a racing process and removes only files created by this invocation.
These are transport guarantees, not independent owner or kernel authority.

H1.1 remains open. Metadata v2 is still `candidate`, intuitionistic,
`freeze_ready = false`, and ineligible for training, retrieval, and evaluation.
The later A2.1 slice adds a fixed-point diagnostic for the exact readable
recipe only, and its A2.2 successor now supplies the three changed closed
constructions. Full A2 still requires separately verified readable and
optimized dependency vectors, optimizer/comparison/Pareto evidence, and their
verified publication union.
Deploying the 144 pending page pairs is an independent parallel documentation
workstream. Both must finish before a source-state/freeze request.
The final focused gate passed 46 tests in 101.07 seconds, including exact
retained pins, semantic and reroot attacks, import isolation, public readiness
forgery rejection, the one-build CLI contract, and atomic publication races.
The independently repeated post-optimization threat audit found no blocker.

#### Tagless selected page-build source implemented in H1.1b3

H1.1b3 turns the exact H1.1b1 API records into a deterministic static teaching
surface without consulting or changing either legacy 557-row explorer. Its
only theorem input is the strict-loaded, byte-pinned five-file selected bundle.
The output lives separately at `book/_static/pa-selected-library/` and has no
tags, aliases, JavaScript, `dependents` field, or reference to any of the 317
disjoint explorer names.

The tree contains 384 explicit proof pages, 384 defined-notation pages, 40
definition pages, one index, one body-scoped stylesheet, a closed API, schema,
and manifest: 809 HTML pages and 813 files. The manifest receipts cover the
other 812 members byte-for-byte. The API preserves the 384 replay order, 1,038
declared dependency edges, 13,862 tactic lines, 755 theorem-definition
relationships, 2,027 definition occurrences, and 58 conceptual definition
edges. Every page is static escaped text with resolved local links and a
candidate/non-authority banner.

The evidence boundary is deliberately asymmetric: `generated = true`, but
`deployed = false`. The retained source proves that exact files can be built;
it does not prove that a public host serves them. API, manifest, and readiness
therefore fix `status = candidate`, `deployed = false`, and all freeze,
training, retrieval, and evaluation flags to false. A later deployment claim
requires an external URL/host receipt and a successor metadata record. The
historical metadata-v2 count remains 240 deployed page pairs with 144 pending
on each presentation surface.

Exact identities are: schema semantic/artifact
`eefb4b1154581f248696de3f81bd90296398e5353c6a42d0d01f35b3ccdb2abb` /
`8cdf0e947ce7156109b7591c99ed28d8ee1f938edd3cddfb414d48d7efacdafd`;
API artifact/root
`a7a4be8ba895b9e69955e82bda5bbfe7418eeda47632a59899e6ba0896acaaf0` /
`2efbb00a763f120e5cee6271f3d64838b3a54e04e73a4c78c738f4d50f0b83b1`;
manifest artifact/root
`751c3eefc99e5b30d612049fd99a0d890cd696b3fda0f426ca64d835c5fe2e6f` /
`94b38f4914853c87315f0bc94d33347164d4cb7c01cd81568b1c4f47cb1b1563`;
and readiness artifact/root
`69b11b858348e3dda9a007b495c7198634822623d45314f6f82f551141bc9357` /
`8f7bf0fc18917b92d02d862e13507d28f1bf7d2842fcd93427d3a2879a193b1f`.
The page core passed 11 focused tests in 74.53 seconds. WMI snapshots now carry
the exact generator, source bundle, retained tree, and readiness receipt; the
runner checks deterministic reconstruction before Sphinx, and the structural
checker audits the selected tree independently from the historical explorer.
The focused WMI harness passed 11 tests; the warning-as-error Book build and
its 3,133-page integrity check passed with zero link, fragment, escape,
remote-runtime, or unsafe-link findings.

#### Candidate dependency diagnostic implemented in A2.1

A2.1 adds a diagnostic compiler without adding an admission path. Given a
theorem target `T` and ordered declared dependencies `D1, ..., Dk`, the
candidate-body compiler executes the exact retained tactic recipe against the
curried target `D1 -> ... -> Dk -> T`. It returns the real formula and proof
objects only after the independent kernel accepts that target from the empty
context. This carrier MUST NOT be cited as a closed proof of `T`: it neither
resolves nor checks the named dependency theorems.

The selected-library audit SHALL process exactly the retained 384 rows in
replay order. Within one row it SHALL try omissions in reverse declaration
order, retain every kernel-accepted reduction immediately, and repeat complete
passes until one pass accepts no omission. This ordering is part of the
evidence. Every positive omission MUST include an independently checked proof
receipt. A tactic/finalization rejection may describe only failure of that
exact recipe. A resource limit, malformed source, unexpected exception, or
internal failure is `unknown` and MUST abort construction rather than become
negative evidence.

The retained A2.1 schema has semantic/artifact SHA-256s
`54d6b5128067b1f93d8f7393e0730d7da3a4ac838a0b55b6b6fe0ce92a0d4bc4` /
`ee6eb4daf48fbf320e79a54065befed758ff33c5251ec4a2c18b8093c349c0ff`.
The sidecar is
`artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json`; its exact
4,188,048 bytes have SHA-256
`4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040`;
its document and ordered theorem-record roots are
`12166de8fb0cc028c3b026deb939418a19f001ff8342acab479d433e15d3a83e`
and
`8ae5553e79b15c4e83a76e1eab92cb0983539fa913dfe2bec29d0fb17fb7d784`.
Two full builds were byte-identical. The aggregate records three positive
omission observations, 1,057 exact-recipe rejections, zero unknowns, and 1,035
candidate edges versus 1,038 retained declared edges.

Those three observations do not mutate the admitted library. Because retained
A2.1 evidence is immutable, the affected rows MUST retain the historical
`requires_certificate_rebuild = true` field. A2.2 discharges that obligation
in a successor sidecar containing new closed certificates independently
checked against their original goals; it MUST NOT rewrite the A2.1 rows. The
readable and submitted-construction receipts are domain-separated,
but in A2.1 they both observe the same retained `TheoremSpec` recipe; neither
is a separately optimized construction. Therefore the public graph SHALL keep
the retained 1,038 edges, and `minimality_claim`, `optimized_best_known`,
`publication_ready`, `freeze_ready`, `training_eligible`,
`retrieval_eligible`, and `evaluation_eligible` SHALL remain false. A2 closes
only after separate readable and optimized construction evidence, a declared
comparison/Pareto procedure, and the verified ordered publication union exist.

#### Candidate construction rebuild implemented in A2.2

The 2026-08-09 A2.2 slice discharges only A2.1's closed-certificate
obligation for the three rows whose proposed direct vectors changed. For each
row, the builder runs the unchanged statement and tactic recipe with the exact
reduced direct vector,
peels the generated dependency introductions, and closes the body with
canonical dependency certificates from the byte-pinned replay pack. Each
dependency certificate is checked from the empty context before use. The
completed nested-Cut certificate is then checked independently from the empty
context against the theorem's original uncurried statement.

The result SHALL remain a candidate sidecar. It SHALL NOT rewrite
`TheoremSpec`, a retained certificate, the replay pack, either metadata ledger,
the catalog, or the public dependency graph. In the three rebuilt Cut spines,
the direct vectors contain 22 edges rather than 25. The public graph still has
1,038 edges. Moreover, `add_succ_left`, `beta_at_unique`, and `le_refl`, the
three names absent from the respective direct spines, are all still reachable
in those theorems' retained transitive dependency closures. A2.2 therefore
makes no lemma-free or dependency-necessity claim.

The retained schema's semantic/artifact SHA-256s are
`a189ad140f5e7093f11a2f433705d4dafb71d474672e822cf39e45dbeb1ca571` /
`d1fc09c035e28f96913cdadd63f17c853901fc8dcd2e17df3a094a919612bf9f`.
The canonical sidecar is
`artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json`. Its exact
3,106,352 bytes have artifact SHA-256
`6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182`;
its document and ordered theorem-record roots are
`91ecc6b4bb22f4b46cdfa3fcdd2401dce47d8fef38c15101d221c207fd7793b0`
and
`42d718621f91b52bf55a7909751eab695fefd28da2989863de50470d14397ef5`.

Against each row's immediate retained predecessor, the three canonical
artifacts together contain 49,483 fewer bytes, 1,176 fewer intrinsic
proof-tree nodes, and 34 fewer Cuts. Those are descriptive predecessor deltas,
not optimizer or Pareto results. Python proof-object identity and sharing
counts are schedule- and assembly-dependent, are marked non-comparable, and do
not enter the deltas. The focused gate passed 23 tests in 44.12 seconds; the
exact retained CLI `--check` passed as well.

All A2, dependency-vector, lineage, review, minimality, optimized-best-known,
publication, publication-union, freeze, training, retrieval, and evaluation
flags remain false. A2.2 grants no admission or authority. The optimizer
program, comparison set, Pareto evidence, independent readable/optimized
vector audits, and verified ordered publication union remain later A2 gates.

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

### 2.6 Authoring and admission law

The live assistant is a revisioned proposal system, not an autonomous editor
or theorem authority. It MUST retain every source unit verbatim and classify
it as `claim`, `definition`, `proof_step`, `exposition`, or `question` before
formalization. Its persistent objects use strict, canonical, versioned schemas
for documents, source units, formalization candidates, diagnostics, proof
attempts, theorem proposals, authenticated lifecycle events, and explicit
export events. The lifecycle schema fixes append-only transitions, previous-
event chaining, actor/authority classes, and the reviewed host-registry
identity before A5 supplies the service. Unknown versions, duplicate keys,
additional fields, unsafe text, and noncanonical encodings fail closed.

A formalization candidate MUST bind the exact source span and hash, document
revision, logic profile, library epoch, readable formula, deterministic
primitive expansion, free-variable/binder table, assumptions, alternative
readings, definition receipts, provenance, and training-consent state.
The receipt binds the existing Peano Lab defined-syntax registry ID/version/
digest, exact definition uses, readable source, expanded formula, and a
successful expansion round trip; Hydra MUST NOT invent a parallel definition
registry.
Training consent defaults to deny. A background response whose document or
source-unit precondition is stale is retained only as rejected audit evidence;
it cannot update the current document.

Every diagnostic carries an explicit authority class: parser, definition
expander, library graph, bounded evaluator, kernel, untrusted solver,
untrusted model, or human reviewer. The UI MUST distinguish a syntax error, a
proved contradiction, a concrete checked counterexample, a missing dependency,
an ambiguous reading, and search exhaustion. Solver/model opinion and timeout
are never displayed as mathematical falsehood. The assistant MUST NOT repair
binders, assumptions, quantifier order, implication direction, equality
direction, or the target silently merely because a nearby statement is easier
to prove.

An accepted candidate becomes only a theorem *proposal*. A checked proposal is
constructed from actual kernel `Formula` and `Proof` objects, freshly replayed
against the exact original formula under its declared logic. It MUST retain
lineage, exact ordered direct dependencies, readable source proof, best-known
optimized certificate, proof metrics, mutation results, solver/model
transcripts, explanation, and deterministic Book/vault/Explorer outputs.
Direct dependencies are checked and minimized independently; “minimal” is
reserved for a proved lower bound, while ordinary optimization reports exact
Pareto metrics and “best known.”

Human acceptance of the statement and human review of the complete proposal
are separate, explicit events. Neither may be forged by a client, solver, or
model field. Only an explicit export action may produce a patch or pull
request. The browser workspace, background workers, and prompt content MUST
NOT mutate the public catalog, proof session, Git tree, or history directly.
Authoring events are append-only, carry revision preconditions, survive
restart/reload, and preserve the existing single proof-session owner.

### 2.7 First H1 implementation boundary

The first executable slice deliberately implements less than the complete H1
gate. Canonical authoring schema v1 has semantic digest
`31a344bbc0b22cfacf5803c85d25a80a0234cf7387395283c5e1ab25ada80553`.
Its public builders and loaders bind exact document/unit revisions, default-
deny training consent, the exact existing defined-syntax registry, real
kernel objects for checked proposals, and ordered lifecycle/export deposits
whose rolling roots include actor, session owner, sequence, predecessor, and
evidence. Generic model/solver diagnostics remain explicitly untrusted;
parser, expansion, graph, evaluator, kernel, and human labels require a
dedicated evidence path. Production lifecycle/export registries are empty.
The core labels a freshly replayed certificate `submitted`; only A2 may call
one `best-known` after binding the comparison set and optimization evidence.

This module treats serialized prose, model output, solver output, and network
responses as hostile data. It treats the installed Peano Lab host package and
source-reviewed registry deposits as administrative trusted inputs. Python
private names are not a security sandbox against arbitrary code already
executing in the same process; such plugins are outside the A0 public-API
threat model and MUST NOT be loaded into the authoring service.

Library-epoch schema v1 has semantic digest
`f4695013ee4aeb660abf3a1e57a6334d86c990a8904c4435d94628694a2e875b`.
Its candidate path freshly binds living HEAD, relevant dirtiness, the active
constructive profile, retained H0 evidence, and a live replay of the complete
384-theorem catalog. JSON versions and root preimages compare with exact JSON
types, reads are bounded and reject final symlinks, packed paths are checked
lexically without consulting the living tree, and a source revision observed
after import forces a process restart rather than pairing new hashes with
stale Python objects.

The historical epoch-v1 three-file pack still contains only the catalog,
semantic profile, and retained H0 report and remains a transition-protocol
fixture. A separate replay-pack-v1 candidate now supplies the previously
missing canonical formula/certificate bytes for all 384 theorems and replays
them in an import-guarded fresh interpreter. Its exact identities and claim
boundary are specified in §2.3. This closes the replay-transport subgate, not
the freeze: the reviewed owner-receipt registry is empty, the candidate is
explicitly evaluation-ineligible, and H1.1a's metadata ledger now makes the
remaining gaps machine-readable. Definition and explorer receipts cover 240
of 384 rows; direct readable/optimized dependency evidence, the deterministic
publication union, best-known comparison, human review, lineage, independent
source-state deposit, and benchmark artifacts remain unresolved. H1.0 and
H1.1 therefore remain open.

## 3. Trust and system architecture

```text
formula + library epoch + budget
                |
                v
     deterministic native closure
       | solved                 | stalled at critical frontier
       v                        v
 certificate             macro proposal policy
       |              (Qwen; Codex on TRAIN/DEV only)
       |                        |
       |       +----------------+----------------+
       |       |                |                |
       |   bounded search  retriever/ranker     Vampire
       |       |                |          reconstructable hints
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
- **Qwen LoRA models:** separately identified student components for prose
  classification/formalization, ambiguity critique, theorem retrieval, macro
  actions, frontier/value ranking, or explanation drafting from already
  checked artifacts. A response from one role cannot assert authority
  belonging to another.
- **Codex:** optional teacher, formalizer, critic, and dataset generator on
  TRAIN/DEV.
  It may measure action-interface headroom and generate tagged candidates,
  all of which require replay. It MUST NOT see or act on the sealed final set.
- **Vampire:** the only first-class external prover in the initial portfolio.
  It is a classical first-order engine, not an intuitionistic HA kernel. In
  constructive mode it proposes bounded premise bundles, instantiations,
  witnesses, cuts, rewrites, or proof skeletons that are reconstructed through
  ordinary Peano operations. Direct reconstruction is permitted only for an
  explicitly proved translation class. A raw `SZS Theorem`, unsat result, or
  proof object is never scored. E and SMT remain deferred comparisons and need
  separately reviewed adapters.

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

The first A3 executable slice, added on 2026-08-09, is intentionally smaller
than a Vampire integration. `training/peano_hydra/vampire_adapter.py` converts
one closed primitive-PA formula and an explicitly requested subset of an
explicit premise allow-list into deterministic classical TPTP FOF bytes and a
source-symbol map. Its direct executable boundary copies and rehashes the
binary, invokes it without a shell, and bounds wall time and combined output.
Fake executables exercise that OS boundary, timeout, output, parser, and
rollback behavior reproducibly without depending on a solver installation.

Raw output and every `SZS` status remain inert. Reconstruction class v3 reads
only the original checked Peano problem. It recognizes top-level closed
reflexivity as `refl`; exactly one explicitly selected PA axiom as
`apply NAME`; exactly one explicitly selected public theorem as
`use NAME; apply NAME`; and a top-level conjunction with exactly two selected
PA axioms in branch order as `split; apply NAME1; apply NAME2`. Every other
multi-premise case is commandless. Swapped or irrelevant axiom plans fail on
the ordinary public surface and roll back. Frozen `Dispatch` rejects status
without commands, executes every reconstructed command transactionally, and
admits QED only after a fresh original-goal kernel replay. A forced final-
kernel rejection also rolls back.

A3.1 then exercised the real direct boundary diagnostically. The official
Vampire 5.0.1 macOS ARM64 release ZIP was downloaded only to a temporary
directory; its SHA-256 was
`8c92e649fe7bc622a70000afbdf5a5c51007b384e2d8b8235c95474cc7a68f35`,
and the extracted executable SHA-256 was
`b5168c690e0293cdac78f16d8418d7eeabcd6708f90a60cd2bf45313b6d98699`.
Neither was vendored or installed. For `0 + 0 = 0` with the single disclosed
premise `PA3`, a real direct `run_vampire` invocation returned theorem-like
evidence (`SZS Theorem`). Offline deterministic reconstruction proposed
`apply PA3`; ordinary
execution plus fresh kernel replay accepted a 2-node, depth-2 certificate whose
canonical `encode_proof` SHA-256 was
`25b6f555180e9737fe4aeb0e51f1f9e97911ed9ffc41c6a80ef97088930711cd`
and whose complete `peano-lab-v2` artifact SHA-256 was
`3c65761490733d3382932780f26ff2fb382f82eb536a45af41840b172be7efca`.

The ordered `PA3`, `PA5` conjunction problem had exact TPTP SHA-256
`60b2666d452d253bd982170cc8c3d586c2be836ee72355a4fc108d313d403f96`.
The real solver returned inert `SZS Theorem` and reconstructed only
`split; apply PA3; apply PA5`; fresh kernel replay accepted the resulting
5-node, depth-3 certificate. Its canonical `encode_proof` SHA-256 was
`3d47f7636f578cbcaf638006942e19c8ff9c565359967d44b32d20668ef5f812`;
its complete `peano-lab-v2` artifact SHA-256 was
`cc520fd2f72148dc05450c414151a55cca4a18ce528e15bb150d9ea89e493d68`.
WMI separately pinned the official x86-64 executable with SHA-256
`81532e088c4ee1238d7ea1d8e868a2dccf8d358ad4d2126d257b4dda7f2e6bd9`.
A real `--mode vampire` run on the same conjunction returned `SZS Theorem`,
with Vampire reporting 0.001 seconds and 8 MB. Those solver-reported numbers
are diagnostic observations, not host-attested campaign resource measurements.

The one-shot preview is `scripts/peano_hydra_vampire_assist.py`. It accepts a
closed canonical goal, an ordered list of explicit PA-axiom/public-theorem
names, an exact executable path, and resource limits. It emits one canonical
JSON result and writes no file by default. A successful result has passed two
fresh public-command executions followed by `checked_surface_final` and an
explicit independent kernel check against the original goal. Its evidence
still states `authority = none`, `h0_host_contained = false`,
`live_dispatch_registered = false`, and all training/retrieval/evaluation and
publication flags false.

### A3.2/A4.0 — a functional interactive join, still outside H0

The next preview makes one human-owned session usable without adding a proof
rule or changing frozen H0.3. `training/peano_hydra/interactive_assistant.py`
owns an immutable `HydraAssistantSession`, whose proof component is the
existing `MacroOwner`. Its principal entry points are:

- `start_hydra_assistant(theorem)` for one closed intuitionistic PA theorem;
- `run_manual_tactic(session, command)` for one ordinary public Peano tactic;
- `prepare_qwen_request`, `qwen_prompt`, and `attach_qwen_response` for inert,
  request-bound proposal data;
- `apply_qwen_macros` for explicit all-or-nothing execution of a validated
  typed-macro sequence;
- `run_vampire_assistance` for an explicit premise list; and
- `resolve_qwen_premises` for the same path with a validated Qwen-selected
  premise list.

An attempted proof-state transition that fails returns
`HydraAssistantRejected` with the identical input session. Boundary validation
and host-transport errors may instead raise before a transition exists; they
also leave the immutable proof owner untouched, and the terminal catches them
without extending history. Proposal preparation or attachment may create a new
wrapper carrying pending data, but it preserves the identical proof owner and
executes nothing.
Manual progress invalidates pending data. A stale request cannot be rebound to
a changed owner, goal, retrieval set, or authority. Pending proposals retain
their exact response bytes and are re-parsed at the execution boundary.
Successful open progress contains only ordinary checked public commands and no
certificate; a closed successor is accepted only after fresh replay and an
independent kernel check against the original theorem. The resulting session
carries that checked-certificate receipt; an empty goal list without the
receipt renders neutrally and cannot print `qed`.

`training/peano_hydra/qwen_hydra_bridge.py` is proposal-only. The interactive
contract binds a canonical goal, retrieved `name : statement` pairs, and exact
finite authority in `QwenHydraRequest`. A terminal response is one strict JSON
object with exactly `format`, `v`, `premises`, and `macros`. The Python bridge
additionally accepts one bounded canonical line protocol consisting only of
`premises:` and `macro:` lines; the terminal `:model` command does not.
Additional or duplicate JSON keys, Markdown, unselected premises, masked
action tags, unavailable public commands, and malformed typed macros fail
closed. The resulting
`QwenHydraProposal` says `authority = none`, `session_mutated = false`, and
`qed_authority = false`. The bridge's `propose_with_transport` bounds prompt
and response bytes only. Because an arbitrary callable cannot be preempted by
this parser, the application supplying `ModelTransport` MUST own and enforce
wall-time, memory, process, and network limits. Model output MUST NOT supply
that transport or any solver configuration.

`training/peano_hydra/vampire_live.py` is the complementary host-owned A3.2
path. `run_vampire_live(owner, premise_names, solver)` receives one exact
`VampireLiveSolver` containing an absolute executable path, expected SHA-256,
exact arguments beginning `--mode vampire`, and explicit
`VampireLiveBounds`. The host copies and rehashes the executable, creates a
fresh restricted working directory and environment, invokes it without a
shell as the sole child, and retains bounded process evidence. The preview
accepts only one focused closed goal with empty variables and context. It
resolves only explicitly named PA axioms or capability-visible public
theorems. SZS bytes remain inert. The v3 reconstructor proposes ordinary
public commands on a temporary owner; any premise, process, reconstruction,
or kernel failure returns `VampireLiveFailure` with the identical original
owner. Closed results require fresh original-goal kernel replay. Platform-
specific resource claims retain the enforcement/reporting distinctions above.

The functional composition is therefore:

```text
human tactic -------------------------------> public Peano surface
                                                    |
strict Qwen JSON -> checked premise/macro proposal -+
          |                                         |
          +-> selected premises -> direct Vampire child
                                      | inert SZS
                                      v
                              public reconstruction
                                                    |
                                                    v
                                      immutable temporary owner
                                                    |
                                  closed? -> fresh original-goal kernel
```

`scripts/peano_hydra_assistant_repl.py` is the first terminal host. Its
commands are `:goals`, `:script`, `:qwen NAME...`, `:model STRICT_JSON`,
`:accept`, `:resolve`, `:vampire NAME...`, `:discard`, `:undo`, `:help`, and
`:quit`; every other non-empty line is one manual Peano tactic. The console
does not load a model and has no network path. A host may paste a model result
or provide a separately contained transport through the Python API.

An unretained diagnostic experiment with the official Vampire 5.0.1
conjunction binary exercised the real path: inert theorem status reconstructed
exactly `split`, `apply PA3`, and `apply PA5`, and the resulting closed
successor passed fresh original-goal kernel replay. This is an observed smoke
test, not a deterministic retained campaign artifact. No trained-Qwen live
inference was part of this run. The
retained model-v3 checkpoint uses the historical next-tactic interface, not
the new premise-plus-typed-macro proposal contract, and WMI was unreachable during
this integration session. This says nothing negative about eventual model
capability; it means only that a compatible adapter or newly trained role is
still required.

A3.2/A4.0 are functional previews, not the asynchronous A5 product. They are
not browser code, not deployed, not registered behind frozen H0 `Dispatch`,
not a production service, not H2 portfolio evidence, and not a native versus
Vampire versus Qwen capability comparison. H0 remains byte-for-byte frozen.

The two disjoint focused acceptance commands passed 59 tests for the
terminal/Qwen/session/CI boundary and 91 tests for direct-child
Vampire/reconstruction/frozen-macro behavior. Ten focused Book tests and the
Book command-replay gate passed as well.

One integration boundary remains explicit. H0.3's frozen dispatch host permits
exactly one adapter process. A Python/source broker cannot both occupy that
slot and spawn a separate Vampire binary. Registered live-Vampire execution
therefore still requires a separately reviewed host-protocol amendment or one
self-contained linked adapter executable. The real runs above used
`run_vampire` directly and then offline reconstruction; they did not register
a live solver behind frozen `Dispatch`. The vertical slice MUST NOT be
described as production integration, H2 or A3 completion, a Vampire-portfolio
result, or evidence of a capability advantage.

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

### 3.3 Live authoring pipeline

The authoring product has a separate, typed flow whose stages cannot be
collapsed by a model response:

```text
verbatim prose + revision
          |
          v
 classify source unit -----> exposition/question (document only)
          |
          v
 propose one or more PA readings
          |
          +---- ambiguity/diagnostic evidence ----> author edit or reject
          |
     explicit author acceptance
          |
          v
 proof workspace: native closure -> Vampire hints -> sparse Qwen/Codex help
          |
          v
 original-goal Python kernel replay
          |
          v
 theorem proposal + dependency/Pareto/docs receipts
          |
     explicit human review and export
          v
 reviewable patch / pull request / next immutable library epoch
```

The UI may stream partial proposals, search progress, and diagnostics, but the
persistent event log is authoritative about ordering. Every asynchronous
result carries a precondition over document revision, source-unit identity,
logic mode, library epoch, and proof-state identity. A precondition mismatch
is `stale`, never an instruction to rebase automatically. Cancellation and
provider failure append observations and leave accepted text and proof state
unchanged. An offline mode MUST still support deterministic parsing,
expansion, local library use, proof execution, kernel replay, and export.

The assistant presents two linked proof views: the readable authored script
used for teaching and review, and one or more checked optimized certificates
used for storage or replay. Optimizers are untrusted proof-to-proof search:
they may replace a certificate only after a fresh check against the same
original statement and after retaining both identities and comparative
metrics.

### 3.4 Fast-checker boundary

The Rust native/WASM checker may run early and often in authoring, solver
reconstruction, model rollouts, and corpus generation. Its verdict is a fast
filter until K5--K11 complete. The version-3 protocol SHALL carry logic mode
inside canonical bytes and use distinct outcomes for acceptance, malformed
input, invalid certificate, resource exhaustion, and internal failure.
Resource exhaustion makes no theoremhood claim.

Lean work has two separate obligations: prove the mathematical checker
specification sound, then prove that the exact committed Rust accepted path
refines that specification. Reimplementing an analogous checker in Lean and
running finite differential tests establish neither source refinement nor
binary correctness. If exact source refinement cannot be completed, Python
authority or mandatory dual checking remains; the project does not relabel
testing evidence as a proof.

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

Prose classification, formalization, and critique rows are a separate dataset
class from proof-policy transitions. Human acceptance determines whether a
source-to-formula pair is a positive formalization example; kernel acceptance
determines whether a proof path is a positive proof example. Neither authority
substitutes for the other, and denied-consent authoring units enter no corpus.

### 4.2 Quadratic-reciprocity growth rule

Quadratic reciprocity is a valuable future stress domain, but it is not in the
current 384-theorem library. Any new definitions, residue theory, Legendre-like
encoding, reciprocity lemmas, or capstone proofs added after `L0` belong to a
later library epoch. They MUST NOT silently enlarge the active Hydra campaign.

Every parallel formalization PR enters through an intake manifest binding its
source commit, statement/proof exposure dates, logic, checked status,
dependencies, license, and destination live epoch. A target whose proof or
substantive sketch was already visible to developers/models is classified as
TRAIN/DEV/library material, never as an unseen target in the active final set.

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
reference semantics, and proof-producing reconstruction plumbing. The strong
native/Vampire symbolic portfolio is H2 and is not an H0 completion claim.

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

### H1 — Authoring contracts, frozen epoch, benchmark, and headroom

First freeze the canonical authoring schemas and their authority boundaries.
Build a manually adjudicated 200-unit TRAIN/DEV authoring corpus covering
binder and quantifier ambiguity, missing assumptions, reversed relations,
out-of-language material, questions, and exposition. Then freeze `L0`,
TRAIN/DEV, and a separately held sealed final set. The final set contains at
least 1,000 positive targets, including at least 200 human-authored or
chronologically future-library statements. The active profile has no negative
theoremhood authority, so it has no non-theorem quota. Run the symbolic
baseline at every registered budget.

On DEV only, a strong teacher may try the macro interface at symbolic critical
frontiers. Advance if there is zero contamination, the 60-second symbolic
baseline leaves at least 100 targets or ten percentage points unsolved, and
the macro teacher closes at least 20% of that frontier. If the symbolic system
already solves at least 99.5% at 60 seconds, pivot to latency/proof-size rather
than manufacture a solve-rate problem. If teacher closure is below 10%, fix
the action interface before training. A teacher success demonstrates only
interface/oracle headroom; it is not evidence about Qwen or final performance.

### H2 — Strong native/Vampire symbolic portfolio

Implement and tune, on DEV only, native normalization/rewrite/arithmetic
closure, focused intuitionistic or connection search, and bounded enumeration.
Vampire is the only initial first-class external prover. Its exact TPTP
translation, source-symbol map, binary, options, raw transcript, and resource
bounds are retained; every useful result is reconstructed through ordinary
Peano operations. Premise minimization and proof optimization retain a Pareto
report, not an unsupported minimality claim. Forged solver status, masked
premises, foreign symbols, malformed output, timeout, and exhaustion fail
closed. The frozen portfolio must weakly dominate each component on DEV
solved-versus-resource AUC and becomes `S` before model evaluation.

### H3 — Checked macro curriculum

Build at least 100,000 unique positive macro transitions from at least 20,000
complete kernel-checked QED roots. Cover every public macro head, with at least
2,000 examples for each critical open-ended head. Each eligible `L0` theorem
must have at least eight independent positive-use lineages or be explicitly
marked ineligible/held out. Two clean builds must be byte-identical; every
positive root must replay; contamination must be zero; and tokenizer audits
must reject, not silently truncate, over-length examples.

Classification/formalization/critique examples remain in a separate corpus.
They require adjudicated source-to-statement acceptance, explicit consent, and
the same lineage split before paraphrase expansion. A checked proof of a
nearby formula does not turn a semantically wrong formalization into a
positive example.

### H4 — Small-Qwen model ladder and ablations

Evaluate, in order, `S`, `S+BM25`, learned retrieval, cheap clause/state
ranking, pretrained Qwen, 1.7–3B Qwen SFT, SFT plus value-guided
best-first/PUCT search, a separately evaluated formalization/critique adapter,
and then checked expert iteration. The primary family is LoRA-post-trained
Qwen below 10B parameters. Roles remain tagged and separable; one generic
decoder response does not silently combine formalization, retrieval, proof,
critique, explanation, or authority. Also run shuffled scores, random-valid actions, no
retrieval, no value, no clause ranker, no symbolic closure, and LLM-only
controls.

Advance components only when:

- learned retrieval reaches recall@8 of at least 75% and improves at least ten
  points over BM25, or matches recall at materially lower declared cost;
- the clause ranker has a positive lower 95% paired solve-difference bound at
  equal instructions, or saves at least 20% activations with under one point
  solve loss;
- SFT beats the identical pretrained system by at least five DEV points,
  solves at least 25 registered frontier cases, and has a positive lower 95%
  paired interval;
- the formalizer reports top-1/top-3 human-approved semantic accuracy,
  critical binder/quantifier/assumption error, ambiguity abstention quality,
  and median edits to acceptance independently of parser or kernel validity;
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
Obsidian notes. Release a source-controlled LaTeX report and reproducible PDF
covering data, training, search, inference, authoring, trust limits, and
results; keep the project memory, dated journal, and implementation diary in
sync. A fresh machine must reproduce certificate judgments and paper tables.
Full tests, strict Book and LaTeX/PDF builds with visual/text verification,
link/vault checks, license checks, and an independent leakage/compute/claim
review must pass.

## 7. Continuous authoring-product gates

The A-track proceeds beside, and is not blocked by, the sealed H experiment:

1. **A0 — contract:** canonical revisioned schemas and checked builders;
2. **A1 — sentence workbench:** verbatim units, alternative PA readings,
   structural read-back, and explicit accept/edit/reject;
3. **A2 — artifact compiler:** checked theorem proposals and deterministic
   Book/vault/Explorer previews, exported only on request;
4. **A3 — native/Vampire help:** deterministic closure first, then bounded
   reconstructable Vampire hints;
5. **A4 — Qwen LoRA help:** separate formalization, retrieval, macro, value,
   critique, and checked-artifact explanation adapters trained only on
   eligible evidence;
6. **A5 — live assistant:** asynchronous append-only events, cancellation,
   recovery, stale-response rejection, and an offline proof mode; and
7. **A6 — admission:** human review, dependency hygiene, empty-context replay,
   mutations, proof Pareto report, reproducible documentation, and a new
   immutable library epoch.

A representative prose-to-formula-to-proof-to-document session must replay
identically after export, reload, and a clean build. Tests MUST reject stale
responses, prompt injection, forged human/kernel authority, dependency cycles,
classical-to-constructive imports, mislabeled prose, and denied-consent corpus
inclusion.

## 8. Verified fast-kernel gates

The K-track continues the existing native/WASM shadow in
`PLAN/12_peano_kernel_acceleration.md`: K5 freezes a logic-carrying protocol
and typed outcomes; K6 completes measurements; K7 hardens Rust; K8 proves the
algorithm/codec specification in Lean; K9 connects the exact safe-Rust source
to that specification; K10 performs a cross-platform dual-check soak; and K11
makes a separately reviewed authority decision. Failure of K9 forbids a
Rust-only QED path. Completion of H0 or good differential results does not
waive any K gate.

## 9. Change control

All changes that affect grammar, trust, library visibility, lineage,
benchmark membership, solver translations, model inputs, search resources, or
metrics require a new versioned protocol record. Before H5 they require a
documented rationale and complete DEV rerun. After final-set unlock they end
the campaign; they do not patch the result.

Quadratic-reciprocity growth, additional public theorems, a larger Qwen model,
and a new external solver are legitimate next-epoch experiments. They are not
retroactive improvements to a frozen comparison.

Authoring schemas, logic profiles, conservative notation, classical-mode
policy, library-admission requirements, and Rust authority are included in
this rule. A classical profile or checker-authority change requires its own
reviewed protocol identity; it is never an in-place reinterpretation.

## 10. Research lineage

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
