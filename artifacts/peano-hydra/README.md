# Peano Hydra artifacts

This directory preserves deterministic Hydra plumbing evidence. It contains
no trained-model result, sealed benchmark, decision-procedure result, or
matched-compute comparison.

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
