# Peano Hydra artifacts

This directory preserves deterministic Hydra plumbing evidence. It contains
no trained-model result, sealed benchmark, decision-procedure result, or
matched-compute comparison.

## H1.1b2 candidate metadata successor

`library-epoch-metadata-candidate-v2.json` is an additive successor to the
exact H1.1a ledger below. It does not rewrite that historical artifact and
does not load its mixed explorer inputs. Instead, it preserves each pinned v1
theorem row and joins it, in replay order, to the isolated H1.1b1 selected API
bundle.

- schema semantic digest:
  `498dde0a3b4f762197d8c371609dfac2eabf7edcfc37a6d3c5cdf6ca21efb38a`;
- schema document SHA-256:
  `27af1e5c1ee0e73cb012db3d8b94cb9a6e1be48d08e8158ad48b8edac399973e`;
- ordered 384-row theorem-record root:
  `22330158f52f049ec920992f51f96a0ab0e9939c3eeb893f533616c17b48e98a`;
- metadata root:
  `e0c1d3683e111d7f2883cebbc423694159e82d95471d9375866a81ec596dfb9e`;
- exact 3,732,032-byte metadata document SHA-256:
  `dc6a59ce08397eba698651f6ed4faac0533dec55c13d5a8ca49d863d19d7b72d`;
  and
- exact 1,891-byte readiness-report SHA-256:
  `f257646d1ba5b51835c8b1718538b4b21c89ea402ba073a9630842708db0206b`.

The successor records 384 complete selected explicit/defined API and
definition-use receipts. It separately preserves the historical fact that
only 240 rows have both deployed-page receipts; 144 explicit and 144 defined
pages remain pending. Human review, lineage, readable/optimized dependency
vectors, leave-one-out evidence, publication union, and best-known comparison
remain pending for all 384 rows. All freeze, training, retrieval, and
evaluation flags remain false.

The CLI writes nothing by default. Rebuild and compare both retained files:

```console
python3 scripts/build_peano_hydra_epoch_metadata_v2.py \
  --check \
  --output artifacts/peano-hydra/library-epoch-metadata-candidate-v2.json \
  --report artifacts/peano-hydra/library-epoch-metadata-candidate-v2-readiness.json
```

The final optimized exact retained check passed in 30.4 seconds on this
constrained local run. Its structural contract performs one fixed-source
construction; absolute timing is diagnostic rather than a regression limit.
The publication primitive uses atomic create-if-absent links and inode-checked
rollback, so it cannot overwrite a destination introduced by a racing process.
The final focused acceptance suite passed 46 tests in 101.07 seconds, and the
independent post-optimization threat audit found no blocker.

## H1.1b1 isolated selected documentation bundle

`l0-documentation-candidate-v1/` is a tagless five-file bundle rebuilt from
the exact 384 replay rows. It is not a filtered view of the 557-row proof
explorer and contains no global tags, `dependents`, or bodies or names from the
317 disjoint candidates.

- schema semantic/document SHA-256:
  `30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d` /
  `a442e89ac312302dcee777b5741ca7f2d67e10f6ebcc996b8096fc6061c28a9c`;
- explicit root/artifact SHA-256:
  `b7942fa5a866ff7cd8a38f30c93787ec0abd2948e69710651e4d3578e64377da` /
  `f1c9f364db0cb7ae7f4c7fe065b1ef48d5522fc49711667479ec3dc4db723936`;
- defined root/artifact SHA-256:
  `897fd5e4bedb44b63853e428ff5bc2e2c273e30a0c239450e0ec8f93d73fc61f` /
  `164b34dd0cad555baf2164ee3da114fb60a447bd667112481e7225097dd17cea`;
- isolation root/artifact SHA-256:
  `64bdc2c52bcaf88d26382bbe514be4a442cc876b8df2a353c272587e1516d919` /
  `8c8a6882d0d5a82552942fc0c3efe5a900244a9cad02c32b24cabe3d86a0eee6`;
  and
- manifest root/artifact SHA-256:
  `8f7ef8fcca69bc6f5f8b39c220293b8414a65fd81576c584f78e59da104d46a4` /
  `5ded97c27b859cc4725362bc76aba89fac06c5f11843b50529b78050b19348bf`.

The explicit side has 384 rows, 1,038 declared edges, and 13,862 tactic lines.
The defined side has 2,027 definition occurrences, 40 serialized definitions,
and a pinned 43-entry parser registry. Check it without writing:

```console
python3 scripts/build_peano_hydra_library_documentation_bundle.py \
  --check \
  --output-dir artifacts/peano-hydra/l0-documentation-candidate-v1
```

## H1.1a candidate epoch-metadata readiness ledger

`library-epoch-metadata-candidate-v1.json` is a candidate-only inventory over
the exact replay pack below. It is not a frozen epoch or an independent owner
deposit. Its schema fixes `status = candidate`, `freeze_ready = false`, and
`evaluation_eligible = false`.

- schema semantic digest:
  `71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c`;
- schema document SHA-256:
  `9867378c8802501d2120ad4d94a86378815cf90b003eafc92b164685da61c956`;
- metadata root:
  `b2f397cec26d5f22bf0806da1f6e219d26bb5e319a503395150d9278efae8279`;
- exact 5,880,054-byte metadata document SHA-256:
  `e719dd526d0aa07e2521fb2e499f2ee6810506d32a912298f11dbac60a2c0289`;
- exact 1,195-byte readiness-report SHA-256:
  `386be7eb475980a373122d769a496220319d34090463e0a3bc870cfece3e4c25`.

The ledger records 384 replay-ordered theorems, 1,038 declared publication
edges, 384 source locators, and 240 documentation-complete rows. Atlas and
vault gaps are zero. Explicit-explorer, defined-explorer, and theorem-level
definition receipts each have 144 missing and zero stale rows. Every theorem
still has unresolved human review, lineage, best-known comparison,
readable/optimized dependency-vector, leave-one-out, and publication-union
evidence. The explorer artifacts contain 317 additional names disjoint from
this candidate; their complete corpora are provenance only and must not enter
this epoch's training, retrieval, or evaluation context.

The focused metadata/CLI suite passed 53 adversarial tests in 78.89 seconds.
Two temporary builds were byte-identical before retention, and the retained
ledger and report pass the same read-only `--check` shown below.

Rebuild and compare without any implicit output path:

```console
python3 scripts/build_peano_hydra_epoch_metadata.py \
  --check \
  --output artifacts/peano-hydra/library-epoch-metadata-candidate-v1.json \
  --report artifacts/peano-hydra/library-epoch-metadata-candidate-v1-readiness.json
```

H1.1 remains open. H1.1b1 and H1.1b2 above later add isolated selected API
receipts without rewriting this historical count; they do not deploy the 144
pending page pairs. Deployed-page repair and A2's dependency/comparison
evidence are independent parallel workstreams; both precede a reviewed
source-state request for an external independent owner.

## H1.1 replay-complete candidate pack

`l0-replay-candidate-v1/` is the subordinate certificate-transport candidate,
not a frozen production library epoch. Its schema enforces `status = candidate`
and `evaluation_eligible = false`.

- schema semantic digest:
  `d60b07fe68aa4ba023c9bb873e2df4190752f70252caca21da7e76dcd393f02d`;
- schema document SHA-256:
  `cfd0959ec537c9a7e3cdf705bd48ff7f8301fbd43f63623934d4638cb712b2ef`;
- 384 canonical `peano-lab-v2` artifacts totaling 80,088,767 bytes;
- manifest root:
  `fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d`;
- fresh-worker recomputed theorem replay root:
  `88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba`;
- retained 828-byte report SHA-256:
  `35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10`.

The report was produced in a fresh
`python -I -S -X pycache_prefix=<fresh-dir>` worker. Its import guard forbids
the living theorem library, tactic engine, UI, training package, Torch, and
Transformers. Every artifact is decoded under explicit resource limits, bound
to the separately parsed original closed statement, and checked by the
intuitionistic kernel from the empty context. The standard acceptance test
repeats all 384 checks and requires the generated report to be byte-identical
to the retained report. The corrected replay-pack and bounded-decoder selection
passed 145 tests in 47.56 seconds.

Reproduce the replay without importing the living builder:

```console
PEANO_REPLAY_PYCACHE="$(mktemp -d)"
python3 -I -S -X "pycache_prefix=${PEANO_REPLAY_PYCACHE}" \
  scripts/build_peano_hydra_replay_pack.py \
  --verify \
  --output artifacts/peano-hydra/l0-replay-candidate-v1 \
  --report /tmp/peano-hydra-l0-replay-report.json
cmp /tmp/peano-hydra-l0-replay-report.json \
  artifacts/peano-hydra/l0-replay-candidate-v1-report.json
```

H1.1 remains open: the pack retains declared publication dependencies rather
than separately verified readable/optimized vectors, and lacks leave-one-out,
definition/document, lineage, source-state/owner-deposit, and sealed-benchmark
receipts.

## Retained H0 validation

`h0-validation-v2.json` is the canonical complete H0 semantic/conformance
report. It was produced from clean commit
`26c2503b36c6884bfbfa6dabd1494bbda49d8926` and has:

- file SHA-256:
  `55c60502b2229f4420bd4557058842bebb582f491739e82a6dae06de5b803fdb`;
- size: 3,484,230 bytes;
- 187 implementation-source files at manifest root
  `186a35116fedd424c6144e662211304e775663b12cda6ce4582bc182db3f5d25`;
- `validation_passed = true` and `campaign_eligible = true`;
- two identical 384-theorem cold replays at root
  `fae19fad55c416ae7b695107390c1c733d6740fe63d10cf0efed127f5801b9d2`;
- 1,024 distinct positives, 1,024 wrong-target certificate rejections, ten
  artifact mutations, and three profile/schema boundary mutations;
- exact agreement with the pre-registered Lean reference on all 2,058
  artifact cases;
- green kernel-import, original-goal, and transactional-history regressions;
  and
- complete H0.3 evidence: seven content-rooted typed actions, pinned accepted
  and rollback traces, a reconstructed Dispatch call with all hash preimages
  and a fresh original-goal kernel check, plus an exact 110-test transcript.

Rust reports 2,047 portable and eleven registered out-of-envelope cases. WASM
reports 1,790 portable and 268 registered out-of-envelope cases. These are
diagnostic resource classifications, not semantic disagreements. The report
contains no certified non-theorem because Hydra retains no decision claim.
Dispatch RSS/wall-time fields and the pytest duration embedded in its raw
stdout are exact observations from this run, not stable semantic identities.

The earlier `h0-validation-v1.json`, SHA-256
`6a6f30bc3797b1434af081d6515cbc25f433274d7cf0a94f073998ec3a884f57`,
is retained as provisional H0.1/H0.2 evidence from clean commit
`0bd8da9beb6cb506800da884547f8da3b86c4867`. It predates the required
`macro_protocol_controls` field and is superseded for any complete-H0 claim.
The schema version was advanced rather than silently assigning two shapes to
version 1.

From a clean checkout with the registered Lean verifier and built Rust shadow,
reproduce v2 with:

```console
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_peano_hydra_h0.py \
  --output artifacts/peano-hydra/h0-validation-v2.json \
  --lean-source-root ../peano-lab-lean-integration \
  --lean-verifier ../peano-lab-lean-integration/.lake/build/bin/peano_lab_verify \
  --rust-cli peano-lab/rust/peano-kernel-shadow/target/release/peano-kernel-shadow \
  --node /opt/homebrew/bin/node \
  --wasm peano-lab/peano_kernel_shadow.wasm \
  --timeout-seconds 120 \
  --campaign-timeout-seconds 14400
```

## Active H0 contracts

The active semantic profile is
[`semantic-profile-v2.json`](../../training/peano_hydra/semantic-profile-v2.json):

- ID: `peano-lab-ha-intuitionistic-v2`;
- semantic SHA-256:
  `4f2713e6a21e6261bbefe5991ef545e6356807e7042c6b2c7c07183e142c3b4b`;
- document SHA-256:
  `e19162d0e78779d34e5e02166eeb109c5a75091b4692fe37577a7fa47ff29287`.

Its exact result contract is
[`result-schema-v1.json`](../../training/peano_hydra/result-schema-v1.json):

- ID: `peano-hydra-result-v1`;
- semantic SHA-256:
  `cf1caf1c867ddfbe3c247e42a18b730ea6790269718170a51f9733d5a7a36b26`;
- document SHA-256:
  `d3a402f3bee847a8bfbee8b9bcbe49dc68bf99ba495cff60006fec5ed65364a0`.

The typed macro contract is
[`macro-protocol-v1.json`](../../training/peano_hydra/macro-protocol-v1.json):

- ID: `peano-hydra-macro-v1`;
- semantic SHA-256:
  `b5fef1ea1b85251ab7f0b8c111cb37e789f96f20771665b4f0dc8b746400552c`;
- document SHA-256:
  `6f6920d2d952251170733674a3af8da09926f4faf19215317a32bc0317d4a482`.

The current deterministic bootstrap is `teacher-oracle-pilot-v3.json`, file
SHA-256
`508a6ead5434b4340779f8e4888204cf75c4dcadb31ae7733cc19802623fe432`.
It binds profile v2/result-schema v1 but remains a teacher-oracle plumbing
regression and comparison-ineligible.

It is regenerated without overwriting retained evidence by:

```console
python3 scripts/eval_peano_hydra.py \
  --include-trace \
  --output /tmp/teacher-oracle-pilot-v3.json
cmp /tmp/teacher-oracle-pilot-v3.json \
  artifacts/peano-hydra/teacher-oracle-pilot-v3.json
```

## Historical semantic profile v1

The canonical machine-readable profile is
[`training/peano_hydra/semantic-profile-v1.json`](../../training/peano_hydra/semantic-profile-v1.json),
and its strict loader is
[`training/peano_hydra/profile.py`](../../training/peano_hydra/profile.py).
Its identity is:

- format: `peano-hydra-semantic-profile`;
- version: `1`;
- ID: `peano-lab-ha-intuitionistic-v1`;
- semantic value SHA-256:
  `058b1644b066967919dae092e5e562b8845e4dd8415fff31d7cd209d51bc9e43`;
- pretty JSON file SHA-256:
  `7defa4113b3d64909f48ce7717f06c163014c5ae910c8643797ab308798ea5ac`.

The two hashes are intentionally different. The semantic hash covers compact,
sorted-key UTF-8 JSON; the file hash also covers indentation and its final line
feed.

The profile-bound input is operationally exact: at most 8,192 Unicode code
points and decimal numerals at most 256, with the one-line, whitespace,
unsafe-character, and explicit-`#` preflight rules recorded in the semantic
value. Those ceilings protect parsing and certificate construction; they are
explicitly not a decision procedure or a negative-result resource bound.

## Historical profile-v1 pilot

`teacher-oracle-pilot-v2.json` is immutable historical evidence from the
profile-v1 carrier. The current v3 CLI does not claim to reproduce this older
wire format. The reviewed v2 file has SHA-256
`d1588420eaf121db84f6cb1a5168645c82e736a8700a5f1a0a2da3c21f7ff74a`.
Its policy, recorded-state, proposal, run, replay, source-artifact, and outcome
records bind the semantic-profile digest. Successful run serialization also
performs another fresh original-goal replay.

The experiment replays the existing 13-command, 180-node consecutive-product
proof. Both lanes receive the same fixed symbolic candidates and search
budgets. The hybrid lane additionally receives structural actions copied from
the checked script at their exact canonical states; the control receives an
identified null head with the same quota. A related mutated theorem is also
attempted to verify that the state-keyed transcript is not reused.

The result establishes only that the untrusted portfolio, exact-state gate,
surface tactics, profile binding, retained traces, and fresh original-goal
kernel replay compose correctly. Because the structural route is a teacher
oracle and the contextual symbolic candidate was human-selected for this
example, it is not evidence of Qwen or Codex capability, an LLM advantage, a
general symbolic baseline, or a negative decision for the mutated formula.

Every lane remains comparison-ineligible. `surface-macro-v0` does not retain
raw decoder calls or complete resource records, validate a campaign provider
attestation, discover critical frontiers independently, or conform to the
active result schema. H0's later completion does not retroactively promote this
historical bootstrap into campaign evidence.

## Historical pre-profile pilot

`teacher-oracle-pilot-v1.json` is immutable historical plumbing evidence from
before the semantic profile was registered. Its SHA-256 remains
`3b709f70eb910e327880fefb0fb54b0770e5a8662c995205412f261b27b7580d`.
It contains no semantic-profile field. The current v3 CLI is not claimed to
reproduce that historical format; the file is retained for provenance and a
test pins its bytes and version.
