# Peano Hydra artifacts

This directory preserves deterministic Hydra plumbing evidence. It contains
no trained-model result, sealed benchmark, decision-procedure result, or
matched-compute comparison.

## A3.2/A4.0 functional assistant preview

The current direct-child Vampire and Qwen-proposal integrations are executable
preview code, not retained campaign artifacts.  The terminal entry point is
`../../scripts/peano_hydra_assistant_repl.py`; it keeps one immutable proof
owner across manual tactics, strict model proposals, and host-configured
Vampire calls.  Solver/model output remains untrusted: reconstructed public
commands run transactionally, and a closed result is reported as QED only when
the independent kernel accepts the resulting certificate against the original
goal.

No runtime trace is retained here. A Vampire trace is canonical per-run
diagnostic evidence, but it includes measured process observations and is not
a deterministic retained campaign artifact.
The preview is not registered in browser or production Dispatch, does not run
the historical trained Qwen adapter, and grants no freeze, training, retrieval,
evaluation, human-review, or capability-comparison authority.

## A2.1 candidate dependency diagnostic

`l0-dependency-audit-candidate-v1.json` is a diagnostic sidecar over exactly
the 384 retained replay rows. It runs each exact tactic recipe against its
dependency-curried target, tries omissions in reverse declaration order to a
fixed point, and removes an edge only after the independent kernel accepts the
reduced target. A failed omission means only that this recipe failed. Resource
limits, malformed source, and unexpected/internal errors are `unknown` and
block construction.

- schema semantic/artifact SHA-256:
  `54d6b5128067b1f93d8f7393e0730d7da3a4ac838a0b55b6b6fe0ce92a0d4bc4` /
  `ee6eb4daf48fbf320e79a54065befed758ff33c5251ec4a2c18b8093c349c0ff`;
- exact artifact size/SHA-256:
  4,188,048 bytes /
  `4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040`;
- document root:
  `12166de8fb0cc028c3b026deb939418a19f001ff8342acab479d433e15d3a83e`;
- ordered theorem-record root:
  `8ae5553e79b15c4e83a76e1eab92cb0983539fa913dfe2bec29d0fb17fb7d784`;
  and
- aggregate: 3 kernel-accepted omissions, 1,057 exact-recipe rejections,
  0 unknowns, 1,035 candidate edges versus 1,038 retained declared edges,
  and 3 immutable predecessor rows carrying the historical
  `requires_certificate_rebuild = true` field.

The candidate omissions are `add_succ_left` from `odd_add_odd`,
`beta_at_unique` from `finite_bounded_injective_surjective`, and `le_refl`
from `beta_product_swap_last_invariant`. None changes an existing certificate
or public graph edge. The readable and submitted-construction receipts are
domain-separated but observe the same retained tactic recipe; there is no
separate optimizer or best-known comparison. Minimality, optimized-best-known,
publication, freeze, training, retrieval, and evaluation flags are all false.
The A2.2 successor below discharges the three rebuild obligations without
rewriting this A2.1 evidence.

Two complete builds were byte-identical, and 26 focused tests passed. Check
the retained artifact without writing:

```console
python3 scripts/build_peano_hydra_library_dependency_audit.py \
  --check \
  --output artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json
```

This closes only the A2.1 diagnostic subgate. Its three changed vectors are
closed separately by the candidate-only A2.2 sidecar below.

## A2.2 candidate construction rebuild

Retained on 2026-08-09, `l0-construction-rebuild-candidate-v1.json` recompiles
the unchanged statement
and tactic recipe for each of A2.1's three reduced direct vectors, resolves the
selected dependencies only from the exact retained replay pack, and packages
them as deterministic nested Cut spines. Every dependency certificate and
every completed theorem certificate passes the independent intuitionistic
kernel from the empty context; each completed certificate is checked against
the original uncurried theorem statement.

- schema semantic/artifact SHA-256:
  `a189ad140f5e7093f11a2f433705d4dafb71d474672e822cf39e45dbeb1ca571` /
  `d1fc09c035e28f96913cdadd63f17c853901fc8dcd2e17df3a094a919612bf9f`;
- exact artifact size/SHA-256:
  3,106,352 bytes /
  `6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182`;
- document root:
  `91ecc6b4bb22f4b46cdfa3fcdd2401dce47d8fef38c15101d221c207fd7793b0`;
- ordered theorem-record root:
  `42d718621f91b52bf55a7909751eab695fefd28da2989863de50470d14397ef5`;
  and
- aggregate: 3 closed empty-context rebuilds, 22 candidate direct edges versus
  25 retained direct edges across those rows, -49,483 canonical artifact
  bytes, -1,176 intrinsic proof-tree nodes, and -34 Cuts.

The deltas are descriptive comparisons with the immediate retained
predecessors, not optimizer, Pareto, minimum, or best-known claims. Python
object-alias metrics are schedule- and assembly-dependent and explicitly
non-comparable. The direct spines omit `add_succ_left`, `beta_at_unique`, and
`le_refl` respectively, but every omitted name remains reachable in that
theorem's retained transitive closure.

Nothing here changes the admitted theorem records, retained certificates,
replay pack, metadata, catalog, pages, or the 1,038-edge public graph. All A2,
authority, dependency-vector, lineage, review, minimality,
optimized-best-known, publication, freeze, training, retrieval, and evaluation
flags remain false. The optimizer/comparison/Pareto program, independent
readable/optimized vector audits, and verified publication union remain open.

Check the retained artifact without writing:

```console
python3 scripts/build_peano_hydra_library_construction_rebuild.py \
  --check \
  --output artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json
```

The focused adversarial gate covers deterministic reconstruction, fresh
empty-context proof checks, exact input and source pins, explicit Cut-spine
shape, semantic and rerooted mutations, strict path handling, and create-only
publication. It passed 23 tests in 44.12 seconds; the exact retained CLI
`--check` passed too.

## A2.3a bounded optimizer/comparison result

Frozen on 2026-08-10, the A2.3a source protocol fixes a bounded experiment for
exactly the three A2.2 theorem roots. Each root has exactly three candidate
constructions: `retained-replay`, `a2.2-direct-cut-rebuild`, and
`layered-closure`. It fixes componentwise nondominance over canonical artifact
bytes, proof-tree nodes, proof depth, and Cut count, plus the deterministic
representative tie-break
`(proof_nodes, proof_depth, cut_nodes, artifact_bytes, candidate_kind_order,
artifact_sha256, candidate_id)`.

The source protocol remains frozen at these identities:

- schema semantic/artifact SHA-256:
  `07e5842c221fe84337e163ce5c858ab03dfbbc93d1477f5661edfdd6f8ba3978` /
  `006d38ef781fc022b7b8929be35058038df02a0eee91eb2213128598c66a59ae`;
- program SHA-256:
  `7ac7d784c3660c1c9b839c906e50e2a88dced6af96ded00b900165e25ec12eee`;
- no-default-write CLI SHA-256:
  `3acbd3ec0f190699d484ef0c800e4919c7cc8404fbbd50ba6daf90a5deb5d6ee`;
- focused-test source SHA-256:
  `d5ae3e830573c7a561462f5e0e91ef99bff42f6533986106cc65fc34f0e35dc9`;
  and
- focused protocol tests: 59 passed in 0.31 seconds.

WMI job `219765` then ran the fixed three-root, three-candidate comparison from
clean source commit `0f6ca3a0cf5998212e3a0ad508ba77e88a15a17d`, tree
`9051b43aa3f7f75d37ce8d410b9c7a81ba472d94`, and snapshot
`707398a7494482dbcc38c8438582688e01f88b395ab61e64be4a7d6396178824`.
The requested envelope was one `cpu_idle` CPU, 4,096 MiB, and 15 minutes under
x86-64 CPython 3.12.12. Hash-seed-0 and hash-seed-1 producers emitted
byte-identical 848,463-byte candidate documents, and the separately loaded
hash-seed-2 verifier accepted all nine artifacts from the empty context and
recomputed the comparison. The terminal collector records `COMPLETED`, exit
`0:0`, node `c2n1`, 60 elapsed seconds, and classification
`completed-and-independently-verified`.

The retained candidate has SHA-256
`3e989784d371c3383fa5e428df8755d1e94d4c3386328746751981a8a77cab5b`,
document root
`90a3d97a466dc7b1c9e6032b1b56b8ede3fcece8d56a4b39f2d4e5f34dbeb770`,
and theorem-record root
`4cfcbe22312ff2b92022189e65d3742bc096ba989dacaa82b2054e84282928e5`.
The 18,327-byte independent-verification receipt has SHA-256
`6a7942147b8227c61a0de8a8f533653a6d727efe7843a52f3b524f1c47ac084a`,
document root
`e21290f654c1a30e0bdf79e796a8ca1da6ad3aa6a1cb1d8ba34d3d376de052dc`,
and theorem-record root
`18f882717346477304285c9336d7b769ccf95cd1b58c32b65d335f3e8caa4188`.
The same verifier was replayed locally under CPython 3.12 and reproduced the
retained verification bytes while accepting 9/9 artifacts; this is a bounded
replay of the retained candidate, not a claim that another optimizer run was
reproduced locally.

Metrics below are `(artifact bytes / proof nodes / proof depth / Cuts)`. Every
frontier is exactly `[a2.2-direct-cut-rebuild, layered-closure]`, and the
preregistered node-first tie-break selects `layered-closure` as display
representative for all three roots.

| Theorem | `retained-replay` | `a2.2-direct-cut-rebuild` | `layered-closure` |
| --- | ---: | ---: | ---: |
| `odd_add_odd` | `14,977 / 302 / 32 / 7` | `13,640 / 274 / 31 / 6` | `12,709 / 269 / 37 / 3` |
| `finite_bounded_injective_surjective` | `1,913,452 / 42,463 / 89 / 1,266` | `1,870,657 / 41,341 / 89 / 1,235` | `297,637 / 8,355 / 95 / 20` |
| `beta_product_swap_last_invariant` | `391,540 / 7,439 / 67 / 205` | `386,189 / 7,413 / 67 / 203` | `118,018 / 2,011 / 79 / 9` |

The retained replay member is dominated in this exact fixed comparison set.
The two frontier members trade depth against the other axes; the selected
representative is a deterministic display choice, not a globally best or
minimal proof.

## A2.3a retained WMI evidence

The create-only operational evidence lives under
`a23a-wmi-pilot-219765/`. Its key rooted receipts are:

- producer source state: artifact SHA-256
  `3b6658ea8fae6c9430714781398232dd91a4d9c5edc756bd734a28cdb1734c82`,
  semantic source-state SHA-256
  `64ceb310fb0030ac0a1c040d5a15076a53ac1882dd17d725ea92e404f66d942b`,
  and root
  `b8517b9d10868a3942cf5a42ceb8c61e34b317647ddac19da0a8cef998438029`;
- separate clean-Git receipt: artifact SHA-256
  `04158535ba4d920190f63e8a4cc48effcc33ccc162d8a7472265862149dc907e`
  and root
  `332fdc27d3a427d00bf7fa1ac4877c7c1fa73cf408413aedea179ae6846a7c6c`;
- infrastructure manifest: artifact SHA-256
  `5b4e740afa2af94a154185b9b7e8200f25c683b93f73e5aa92335f33e002d87b`
  and root
  `d0a299cd7b83c3584df36f7ae680613136f662c123768c871e8ba74806cf3a6b`;
- execution receipt: artifact SHA-256
  `779a971237f9ac5efe3a86dca5b5c4d74a6da56ab154b91e106f7fd1dac63a34`
  and root
  `7a597563c173cd0cb3d57ff42cd566a8531756e84bf8ba907e7c79ec7295dc0e`;
  and
- collection receipt: artifact SHA-256
  `25e616fc9225ab59db6a089e8a53ed2d44915a54b42f073bcaaa020fc2ff609a`
  and root
  `52339b926ea8b9650787a3db138185e21144f6cdf83596d224ccc6b23435daf2`.

The exact 19-file retention set is the two top-level result documents plus
these 17 operational files:

| Operational path below `a23a-wmi-pilot-219765/` | Bytes | SHA-256 |
| --- | ---: | --- |
| `collections/job-219765.json` | 8,707 | `25e616fc9225ab59db6a089e8a53ed2d44915a54b42f073bcaaa020fc2ff609a` |
| `deposit.tsv` | 438 | `31a194c1469efd8f58d5c473fd28ae2675b7947d49212001ff0776a8bb01e14e` |
| `inputs/.peano-source-provenance.tsv` | 68 | `7862d7916c8b13ce26fe5540c6f901c22e6db55089aa9bfa1c2344d707129301` |
| `inputs/producer-git-verification-receipt.json` | 28,400 | `04158535ba4d920190f63e8a4cc48effcc33ccc162d8a7472265862149dc907e` |
| `inputs/producer-source-state.json` | 2,377 | `3b6658ea8fae6c9430714781398232dd91a4d9c5edc756bd734a28cdb1734c82` |
| `inputs/wmi-infrastructure-manifest.json` | 5,618 | `5b4e740afa2af94a154185b9b7e8200f25c683b93f73e5aa92335f33e002d87b` |
| `logs/peano-hydra-a23a-219765.err` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `logs/peano-hydra-a23a-219765.out` | 422 | `88c0e3278fbf2a1b68f1e56db45595f5f47bbd12a55dc085d628ad681dec15b3` |
| `runs/219765/execution-receipt.json` | 18,088 | `779a971237f9ac5efe3a86dca5b5c4d74a6da56ab154b91e106f7fd1dac63a34` |
| `runs/219765/independent-verifier.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/219765/independent-verifier.stdout.log` | 144 | `ea0b95150724f498b785f52ec7cfc870523005f3e80417007796335a07ab78c7` |
| `runs/219765/producer-0.stderr.log` | 1,447 | `6e0581b6b3a3f4b0ccd7bd102bb79825b641d7470ff15e8579e231caab5b51af` |
| `runs/219765/producer-0.stdout.log` | 117 | `6ea76700dc04a8d0e0a83b1d4a53b3afa5186ffe716d14d44d6b92303e6b7acd` |
| `runs/219765/producer-1.stderr.log` | 1,447 | `6e0581b6b3a3f4b0ccd7bd102bb79825b641d7470ff15e8579e231caab5b51af` |
| `runs/219765/producer-1.stdout.log` | 117 | `6ea76700dc04a8d0e0a83b1d4a53b3afa5186ffe716d14d44d6b92303e6b7acd` |
| `sacct.psv` | 39 | `26eec8cb84f436121c29698eef456e582055493f246697ff84a80615df935023` |
| `submission.tsv` | 553 | `053a0cf2fa7b4d0b5c688724e903cbe57c8d699f22c45fa0d580564060042602` |

The submitted 277,025,280-byte transfer archive was deleted after collection
and is neither retained nor independently rehashed here. Its snapshot hash is
bound transitively through the deposit, submission, execution, collection,
commit, tree, and source receipts; this is not an independent archive-hash
claim. The retained `sacct` row is an unauthenticated scheduler observation.
It contains no `MaxRSS`, so neither it nor the 4 GiB request establishes a
peak-memory measurement or memory ceiling. Scheduler and verifier stderr are
empty. The two identical producer stderr logs retain harmless pre-existing
Python 3.12 `SyntaxWarning`s for `\/`; they are not proof failures.

- source-state generator/test SHA-256:
  `4812314f101ac302f712a87641f37ffb627e4cbaa916605e6c7e1e0b0ed90a26` /
  `acdde9367e5fdea7fdfc4e6cef1c3ee4c2bddeb4b9fbe1e025581eb3c7fe8860`;
- independent verifier module/CLI/test SHA-256:
  `683ee529ed4be0e93504846340eeddf47eae1cb3f84967168a971d422ade1dbe` /
  `1250d0202236a6aa727509c5270767fe91e48cf34e5a6fd9c13ac1a59722f014` /
  `08f838332ffca805c934a6c44cf59148e9f0f9168c784f1b7a9c8b8cf353239a`;
  and
- WMI runner/sbatch/submit/collect/test SHA-256:
  `46c9bea044640ccf057a5113eff2f3c6161206c55521b8fcd7c48e7342ff8632` /
  `1f09c62532a0c9f10fc11bb00a420e1eea1967dc70686ad503c1e5207b75538c` /
  `ce94c5e5e77ff83998f147fb77d3e698eae41366774867238b16990accc7fbee` /
  `ddafef2eab12d18ba766325b5dbb077a0075cc8589bc553a72bd60aff910cb0e` /
  `cc75ad16a90c289d07851f7d59cf79f2e960acd86d9257f8155a1cabc532a755`.

The WMI protocol file passed 18 tests in 0.72 seconds. The 10 source-state, 24
verifier, and 18 WMI-protocol tests then passed together: 52 passed in 8.45
seconds. The 33,374-byte retained-result gate has SHA-256
`28b251f9ab75bea0012949390923b039e267d4721c09bd9ff9b6a08de89cc602`
and passed 4 tests in 3.40 seconds. The result closes only the fixed
three-root/three-candidate A2.3a
execution-and-retention subgate. Direct and transitive dependency surfaces
remain distinct, and no readable or optimized dependency vector has been
independently approved for publication. `producer_git_verified` remains false
inside both result documents; the separate Git receipt proves the clean
execution boundary without turning that field or any mathematical authority
on.

All minimality, global-best/`optimized_best_known`, independently audited
optimized-vector, dependency-vector completeness, publication,
publication-union, review, lineage, freeze, A2 completion, proof/admission/
publication authority, training, retrieval, and evaluation eligibility flags
remain false. The public library, replay pack, 1,038-edge graph, catalog, page
sources, and deployed pages are unchanged.

## A2.3b dependency-vector audit source protocol (no artifact)

Frozen on 2026-08-14, A2.3b defines an unexecuted, candidate-only audit for
exactly roots 256, 376, and 379. Their ordered direct vectors have 3, 14, and 5
edges. Each edge receives one reverse-order omission attempt through
`readable-direct-closure` and one through
`proposed-layered-closure-construction`: 22 attempts per route and 44 total,
after six full-vector baselines.

The readable route freshly compiles the root body and closed direct-Cut
candidate. The proposed-layered route freshly regenerates the root body,
recomputes the single-root override closure over fixed A2.2 vectors, recovers
all modular bodies and provenance rows, and invokes the existing layered
compiler. Both routes share the pinned body compiler and kernel, so a body
rejection before assembly is one shared observation rather than independent
corroboration. Only exact structured route rejection is negative evidence;
accepted omissions and every unknown or resource/internal/malformed outcome
abort the candidate document.

The frozen identities are:

- schema semantic/artifact SHA-256:
  `6782197c9925f5552aab030a11b996c157e2d06344a2d136d8babc1ee1fdc3df` /
  `c4af0d2f850ad16fa7d4a3c086ad13356020a4ccb9a15e0d612babb8db690283`
  (21,875 bytes);
- 44-file implementation-source vector root:
  `4260928ce3d4243c548e3beda3d6bf823aa9f480dbf58367cab64cad8bf3cdb0`;
- producer SHA-256:
  `3f2c9df051ce4271466b70bdf21ffd59d7ffc298905302d8b42946ca2c87804e`
  (120,990 bytes);
- no-default-write controlled-worker CLI SHA-256:
  `29f56547e6f228cf812df6c013670977de2088d2fccbb7da2fb64cda0ad7737a`
  (24,509 bytes); and
- focused synthetic-test SHA-256:
  `6c3a0490b86ac2ae7aef3206c480fa14f6e15994106153788d79633fc3025d06`
  (94,869 bytes).

The focused gate passed 78 synthetic/adversarial tests in 2.24 seconds. No
real baseline or omission campaign ran locally or on WMI, and this directory
contains no A2.3b result sidecar, route receipt, result root, execution receipt,
or publication artifact. The future per-root ordered union is bounded local
diagnostic data only and cannot update the public graph.

Only the source protocol is frozen. Vector completeness or necessity,
independent audit/optimizer evidence, minimality, `optimized_best_known`,
publication or publication-union completion, public-graph application, A2,
proof/admission/publication authority, and training/retrieval/evaluation
eligibility remain false.

## H1.1b3 selected candidate page source

The retained tagless source tree is
`../../book/_static/pa-selected-library/`. It is derived only from the exact
H1.1b1 five-file bundle and contains 384 explicit theorem pages, 384 defined-
notation pages, 40 definition pages, and one index: 809 HTML pages and 813
files. Its manifest has exact receipts for the other 812 members.

Integration status is **`generated = true`, `deployed = false`**. No public
URL, host observation, or deployment receipt is present. The API, manifest,
and external readiness receipt are candidate-only and keep freeze, training,
retrieval, and evaluation eligibility false. This new surface is separate
from the immutable 557-row explorer and does not change metadata-v2's
historical 240 complete deployed-page pairs or either 144-row gap.

- schema semantic/artifact SHA-256:
  `eefb4b1154581f248696de3f81bd90296398e5353c6a42d0d01f35b3ccdb2abb` /
  `8cdf0e947ce7156109b7591c99ed28d8ee1f938edd3cddfb414d48d7efacdafd`;
- API artifact/root SHA-256:
  `a7a4be8ba895b9e69955e82bda5bbfe7418eeda47632a59899e6ba0896acaaf0` /
  `2efbb00a763f120e5cee6271f3d64838b3a54e04e73a4c78c738f4d50f0b83b1`;
- manifest artifact/root SHA-256:
  `751c3eefc99e5b30d612049fd99a0d890cd696b3fda0f426ca64d835c5fe2e6f` /
  `94b38f4914853c87315f0bc94d33347164d4cb7c01cd81568b1c4f47cb1b1563`;
- readiness artifact/root SHA-256:
  `69b11b858348e3dda9a007b495c7198634822623d45314f6f82f551141bc9357` /
  `8f7bf0fc18917b92d02d862e13507d28f1bf7d2842fcd93427d3a2879a193b1f`.

The page core passed 11 focused tests in 74.53 seconds. WMI snapshots carry
the exact generator, source bundle, page tree, and readiness file. The runner
checks deterministic reconstruction before Sphinx, and the Book integrity
gate checks exact copying, local links/fragments, receipts, candidate flags,
and CSS isolation independently from the legacy explorer. The integration
harness passed 11 tests, 17 focused Book tests passed, and the warning-as-error
Book plus its 3,133-page integrity gate passed without link or runtime-asset
findings.

```console
python3 scripts/build_peano_hydra_library_pages.py \
  --output-dir book/_static/pa-selected-library \
  --report artifacts/peano-hydra/library-page-deployment-candidate-v1-readiness.json \
  --check
```

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
