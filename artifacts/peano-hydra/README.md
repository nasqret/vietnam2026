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

Frozen on 2026-08-14, A2.3b defines a source-frozen, candidate-only audit for
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

The focused gate passed 78 synthetic/adversarial tests in 2.24 seconds. At
this source-freeze checkpoint no real baseline or omission campaign had run.
The later job 220218 remained `unknown`, as recorded below, and still supplied
no accepted result. The corrected job-220220 bounded result is retained in a
separate nested bundle below; it is not a publication artifact. Its per-root
ordered union remains bounded local diagnostic data and cannot update the
public graph.

Only the source protocol is frozen. Vector completeness or necessity,
independent audit/optimizer evidence, minimality, `optimized_best_known`,
publication or publication-union completion, public-graph application, A2,
proof/admission/publication authority, and training/retrieval/evaluation
eligibility remain false.

## A2.3b external execution infrastructure and unknown first attempt

The source-only execution boundary is now frozen. A producer-independent
generator binds the four A2.3b producer files and its own committed stage-zero
blob, emits the eight-field producer source state with `git_verified=false`,
and separately roots the clean-Git receipt and their evidence envelope. The
independent verifier imports only the standard library and pinned Peano
kernel. It joins and empty-context checks six exact baseline artifacts: three
readable artifacts from A2.2 and three layered artifacts retained in A2.3a.

The verifier independently recomputes canonical structure, receipts, roots,
orders, surfaces, and the pairing of 44 producer route records into 22 shared
root-body observations. It does not import or replay the tactic compiler.
Accordingly it keeps `negative_observations_independently_verified`,
`route_rejections_independently_verified`, and
`producer_observations_execution_bound` false. A successful WMI execution
receipt could set only the last field true after two real byte-identical
producer processes; it would not turn the negative records into independent
replays.

The reviewed WMI path uses x86-64 CPython 3.12.12, isolated
`python -B -P -s -S` processes, producer seeds 0/1, a seed-2 verifier, one
`cpu_idle` CPU, 4,096 MiB, and 15 minutes. Child output is bounded and the
execution receipt is create-only and last. Resource, timeout, scheduler,
process, malformed, or missing evidence is `unknown`. The submitter defaults
to `--test-only`; real submission requires
`--submit --confirm PEANO-HYDRA-A23B-WMI-VECTOR-AUDIT`.

The exact frozen source identities are:

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| `../../scripts/build_peano_hydra_a23b_producer_source_state.py` | 38,902 | `bdc8b4f5b55bcfe22594e2eb40c8c51f4e29df9ef75215b2c9bb0bb561243ea3` |
| `../../peano-lab/py/tests/test_peano_hydra_a23b_producer_source_state.py` | 11,630 | `728e939359cf750b6e22607ef118b72953752c02cbaecdec9899c99c4ff63917` |
| `../../training/peano_hydra/library_pilot_dependency_vector_audit_verifier.py` | 109,448 | `b5f5cf39ea7b12d3ed52ee176ed733b28fa2e9224640e89dac77df87b14dfab1` |
| `../../scripts/verify_peano_hydra_library_pilot_dependency_vector_audit.py` | 18,653 | `ed9e234f5af04e5878e6f4fd23aace512c66c0bc249fc33dd19c1fcbcdb908c2` |
| `../../peano-lab/py/tests/test_peano_hydra_library_pilot_dependency_vector_audit_verifier.py` | 21,277 | `43ade850e88d5e7f2ce92ece60857892b79beb2e4b38b0d3a709558352b4d04b` |
| `../../scripts/run_peano_hydra_a23b_wmi.py` | 107,619 | `2332115e988aada771258f861b986486bc40dc05865935ff3a699453acfe96f1` |
| `../../slurm/peano_wmi_hydra_a23b_vector_audit.sbatch` | 5,032 | `611b3081f0b53d76343c2d5c684cd74aa12dbb36e0f44e3029541d476bf25100` |
| `../../scripts/submit_wmi_hydra_a23b_vector_audit.sh` | 14,826 | `9774a8705112c0222d300d9ef89235dbc493eb159b907e0e977337b9042d9fe2` |
| `../../scripts/collect_wmi_hydra_a23b_vector_audit.sh` | 5,638 | `5d006e8c453ae78c70fa880695755f8ddf5b488459bb06ab4dd2738ad281089d` |
| `../../peano-lab/py/tests/test_peano_hydra_a23b_wmi_protocol.py` | 31,983 | `d93b3a12f34829bc56f0729a099dc694f9d42dbe7c36c7ffe92844075cb961ef` |

The source-state, verifier, and WMI files pass 45 focused no-network tests in
15.27 seconds (10 / 13 / 22), and an independent threat audit reported PASS.
One clean-commit test-only invocation failed locally before SSH on the old
empty-array route; the refrozen wrappers pass six fake-SSH/no-network routing
cases.

WMI job 220218 later ran both producer processes successfully. Their outputs
are byte-identical, 3,160,729 bytes, and have SHA-256
`f93e410f64425b31090c933fd7cb7b92bee8f071c3152c79fa55f88001d9841a`.
The independent verifier exited 1 on a layered provenance-receipt mismatch,
and the failed seed-2 run emitted no independent-verifier receipt. Execution
and collection stayed `unknown`. Their roots are respectively
`cd1872d348b201ba1259fa116be43d66555576e30d3dbc9811fa04c85bdda876`
and
`a610f3feaa3b1d5afa6cbb64be34ea743246f02eb56bc1cc3a2b36ad4dedd681`.
Those receipts preserve an infrastructure failure, not a scientific negative
finding about any of the 44 route records.

The verifier fix reconstructs fresh A2.1/A2.2/replay provenance rather than
transporting retained A2.3a provenance. A two-seed local postmortem against
the preserved candidate produced the same passing 16,925-byte diagnostic
receipt, SHA-256
`707942bb93d5ad9d26ddf3bbd6733e5b5d403508146a70981c2b507b5a01aad7`,
root
`efe9643d7b3b99f40b9bef6042285efeaa9e5f03d145a09a580a615cd15efa4a`.
This local postmortem diagnostic is not the missing WMI verifier receipt and
has no result/execution authority. Neither the job-220218 candidate nor its
postmortem diagnostic is promoted into this artifact tree. The corrected
job-220220 result is retained separately below. Vector completeness/necessity,
independent negative replay, minimality, `optimized_best_known`, publication
or its union, public-graph application, A2, authority, and all eligibility
flags remain false.

## A2.3b corrected WMI execution and retained bounded result

WMI job `220220` ran from clean commit
`720021aec7afff0463ef8dd1180db2702b415301`, tree
`03383d9b3c5850edfeb8f3401d55116fa4cdd5a2`, and snapshot
`64266e107ee03fe6833af74f7a8d4d5b645886c064f361acd49e416f72c99ae4`.
Both producer processes exited 0 and emitted identical bytes under hash seeds
0 and 1; the separately loaded seed-2 verifier exited 0. Slurm's retained row
is `220220|COMPLETED|0:0|0:0|237||4G|1|c3n1`. The execution classification is
`two-producer-byte-identity-and-independent-baseline-verification`; terminal
collection is `completed-dual-producer-and-independent-baselines-verified`.

The primary artifact / document-root pairs are:

| Evidence | Bytes | Artifact SHA-256 | Document root |
| --- | ---: | --- | --- |
| Candidate | 3,160,729 | `4f4965508b63d852697c94fe0e7707759b39c5cf456ec2db8aa5a5afe719f2ad` | `21f4c7a06dd8b1abf01d8eddd8c1942733f0955141ba682d53229078e15d5e85` |
| Independent verifier | 16,925 | `50c207c4de0cabe8a50518da4d20e83925f0e1df29ffd78df05e249ea18d4396` | `ef0dfac8552789bb4dc0e6694a1704c63a8781a93a1f0d9117c6e5c6babcfbd1` |
| Execution receipt | 19,990 | `dc3cb3d4dc7dae5f842358b1649f131d019742ebeb732d4cad6e92c827b4f318` | `c010a79955e93b29651557977001f6f6abff7cd63ba7f1fa1b9deb2a5bc3c08b` |
| Collection receipt | 8,841 | `d1602e23f7736482b039c3d32537fa012d91302f42d62f75ccab9c11583542a9` | `9f58b68b2fe811cfa82a25395e53b08c01cdd145b57f234d2cde0ca287cf42e5` |

Candidate and verifier theorem-record roots are respectively
`6a90eee2d8a306e41b944735940044b142cf1c4f02441133c25c94111e11d336`
and
`87bef2a0d30c789424a15bb257e1bc743f74f4bfa27fb899ab59a44f4d522585`.
The verifier independently authenticated and empty-context kernel-checked the
following six full-vector baseline artifacts:

| Root / route | Artifact SHA-256 | Bytes / nodes / depth / Cuts |
| --- | --- | ---: |
| `odd_add_odd` / readable | `8064d28bd99adbaa1cde42c7ebd0f94880b345c889d6afc18e4b607749310ecc` | 13,640 / 274 / 31 / 6 |
| `odd_add_odd` / layered | `3fe6ba0a5ab6ca95a159ddb2d8fa44fd674a0eab4376069b3cc2db9f6c3c2962` | 12,709 / 269 / 37 / 3 |
| `finite_bounded_injective_surjective` / readable | `623865d90504af44cddca3d76ac4f009be8aa289e80d2785b72b121a52954504` | 1,870,657 / 41,341 / 89 / 1,235 |
| `finite_bounded_injective_surjective` / layered | `af1410f83a9ab66080a80311d9262341f4cbd4b136a64e889b94c7f12fc342e1` | 297,637 / 8,355 / 95 / 20 |
| `beta_product_swap_last_invariant` / readable | `507940a3e456122fadb3b43d34891a70c91baa87615be80c1fca059e9ebd82df` | 386,189 / 7,413 / 67 / 203 |
| `beta_product_swap_last_invariant` / layered | `fc08873008eea245be7b8b2961e1a00bf659c25dd257785d2e2345ff29fde9a1` | 118,018 / 2,011 / 79 / 9 |

The real dual-producer execution binds 44 route-labeled exact-recipe
rejections. The verifier independently validates their canonical structure
and pairing into 22 unique shared root-body compiler observations, but never
runs the tactic compiler. Consequently the execution receipt records
`producer_observations_execution_bound=true`, while the separately generated
verifier document conservatively keeps that field false. It also keeps
`negative_observations_independently_verified=false` and
`route_rejections_independently_verified=false`. The 44 rows are execution-
bound producer observations, not 44 independent proofs and not independent
replays of the 22 negative compiler observations.

The retained bundle is exactly
`a23b-wmi-vector-audit-220220/`, containing 19 nested regular files: the two
canonical result documents in `results/` plus 17 source, deposit, submission,
execution, scheduler, collection, and bounded-log records. They total
3,248,650 bytes. Its C-sorted
`<sha256>\t<bytes>\t<relative-path>\n` inventory root is
`e9eec4b239d3f9b870695b51ace1ee8f5667071e52b3d30378ebb056d839476f`.
There is deliberately no top-level result copy, transfer archive, full source
snapshot, global ledger, or job pointer. The snapshot digest is receipt-bound,
not independently rehashed from a retained archive. The unauthenticated
`sacct` observation has empty `MaxRSS`, so it establishes no peak-memory or
memory-ceiling claim. Raw job-220218 evidence is not retained here; its dated
`unknown` roots and mismatch regressions preserve the history without
contaminating the successful bundle.

The exact retained-result test is 51,450 bytes at SHA-256
`6a5031239729474a91bb4e1a14d1ebd4639c126e35a307e76805751df0501de4`;
its four tests passed in 2.63 seconds. The CI-sharder tests passed 32 in 0.25
seconds. The combined bounded producer-source-state, corrected-verifier, WMI-
protocol, retained-result, and sharder gate passed 81 tests in 17.92 seconds.
The CI profile now contains 103 weights, assigns 3,500 ms to the result test,
and models loads of 541,000 / 541,000 / 540,800 / 541,000 / 541,000 /
541,000 / 541,000 / 541,000 ms across its eight shards.

This retained result closes only corrected job-220220 bounded execution,
independent verification of the six baselines and structural receipts, and
the exact 19-file retention subgate. It does not close the vector audit:
`bounded_three_root_vector_audit_complete=false`. Independent replay or
certification of the 22 negative observations, a genuine optimized-
construction vector and its audit, dependency-vector/global completeness,
minimality, best-known, publication/publication union, public-graph
application, and A2 completion remain open. Every authority, review, freeze,
lineage, and training/retrieval/evaluation eligibility flag remains false.
The public graph remains exactly 1,038 edges.

## A2.3c negative-replay source protocol (pre-execution checkpoint)

The A2.3c source-only checkpoint freezes the controlled protocol and
infrastructure for replaying A2.3b's shared compiler observations. Its exact
registered shape is three full-vector baselines and 22 unique reverse-order
single-omission observations, joined two-to-one to the 44 retained route rows.
The default CLI emits only a source-protocol description to stdout: it runs no
campaign, creates no result, and writes no file. At this source checkpoint no
local or WMI replay had been accepted and no A2.3c result artifact existed.

The implementation is independent at its wrapper and fresh-process boundary.
It does not import the A2.3b producer, call `compile_candidate_body`, or invoke
either route-specific assembler. It still shares A2.3b's pinned theorem
parser, tactic engine, and intuitionistic kernel. Consequently even a future
successful campaign would establish only the 22 exact script/omission
failures at this shared lower layer; `route_rejections_independently_verified`
and logical dependency-necessity claims would remain false.

The exact frozen source identities are:

- schema: 26,551 bytes; artifact SHA-256
  `be38f796e9d8923024514962f7cc5a5a4f19c828cf502e2912f1ea5094d12ce4`;
  semantic SHA-256
  `a0d84c3168a9b779bfb5fdc483a2ec847e4cc34f85bcf8aee4c7351a6363ccb0`;
- replayer module: 91,304 bytes; SHA-256
  `f5b5dd45c0ce4e2ed5587fd41b7ea206e92ee05526aebf7be96d80f5bb591aa4`;
- controlled CLI: 49,259 bytes; SHA-256
  `524ced1b5ca78040ddccc3030f2d5eee9f10c8bdf455ea96efb625595c72759b`;
- focused test: 87,120 bytes; SHA-256
  `dc5591dcc9d1e48028d1fbaf31971e65bc10c69377167b50317d4558596e6e82`.

The controlled synthetic/adversarial gate passed 54 tests in 5.57 seconds.

The frozen result consumer is standard-library-only and tactic-free. It checks
canonical structure, pinned provenance and retained-evidence identities, the
three baseline receipts, all 22 observation records, and their exact 44-route
join without executing the tactic engine, a baseline, or a negative replay.
Its module, CLI, and 26-test focused file are:

| source | bytes | SHA-256 |
|---|---:|---|
| `../../training/peano_hydra/library_pilot_dependency_vector_negative_replay_verifier.py` | 85,510 | `33f197045cabe95bda3b7ae0ff871b08cb1b186a861827ea08ad0f76cf7908d8` |
| `../../scripts/verify_peano_hydra_library_pilot_dependency_vector_negative_replay_result.py` | 16,309 | `ab013184633e3ef2b92d8ca9521d39a95646576ea7ede8e53e8b74f6f86ffd05` |
| `../../peano-lab/py/tests/test_peano_hydra_library_pilot_dependency_vector_negative_replay_verifier.py` | 23,256 | `5edcb9d22d30de7e0e6a7db6be0e4d470ae344634f2141a02652fa1f9b88615c` |

The clean-Git evidence and bounded WMI transport sources are:

| source | bytes | SHA-256 |
|---|---:|---|
| `../../scripts/build_peano_hydra_a23c_replayer_source_state.py` | 40,801 | `cfe1db8b7a35ca254b135b0c1b55e88c18c8e91b72385594ffed5892a5f964f9` |
| `../../peano-lab/py/tests/test_peano_hydra_a23c_replayer_source_state.py` | 12,372 | `aceb80d04294ad1c87007594187e3b89e9ea553185902bd44ddde6b5db26ab55` |
| `../../scripts/run_peano_hydra_a23c_negative_replay_wmi.py` | 109,511 | `3db7ed105c016fa58a567d2fc8d8a66a9957f6856133195872d2c8fa455a8306` |
| `../../slurm/peano_wmi_hydra_a23c_negative_replay.sbatch` | 5,055 | `f2b2cd1879147d5dbf234a5dc7cd49aefd92152a0cd1b02bf67c02d6feb4fc29` |
| `../../scripts/submit_wmi_hydra_a23c_negative_replay.sh` | 14,904 | `b8301b661a36b54446038759d3d7f421e52b0dee352a335facd32e77693f78cc` |
| `../../scripts/collect_wmi_hydra_a23c_negative_replay.sh` | 5,710 | `dee7801fbd7e21e94d483156f5eca52d57b8ec58fa3ba6e108dd7c657fcd99b7` |
| `../../peano-lab/py/tests/test_peano_hydra_a23c_wmi_protocol.py` | 34,542 | `98f35727e1ec22f5c50318acf3a63e5cde094cbb03a9bbfcece2758ac86d6d7b` |

The future execution path launches fresh replayers under hash seeds 0 and 1,
requires byte-identical candidate files, and only then runs the separate seed-2
structural verifier. The reviewed WMI envelope is one CPU, 4 GiB, and 15
minutes. Replayers are capped at 360 seconds each, the verifier at 90 seconds,
JSON at 16,000,000 bytes, and each child log at 16 MiB. Timeout, output-limit,
nonzero-exit, absent-evidence, and accounting conflicts remain `unknown`;
receipt publication is create-only and rejects replacement and symlink paths.

The new 11 source-state, 26 verifier, and 28 WMI tests passed as 65 bounded
no-network tests in an independent 18.40-second run. Conservative measured CI
weights are 6,000 / 9,000 / 6,000 ms respectively; the source-protocol test
retains its 6,000 ms weight. The 107-entry profile models eight loads of
544,500 / 544,000 / 544,800 / 544,500 / 545,000 / 544,000 / 544,000 /
544,000 ms.

This source checkpoint completed only A2.3c protocol and infrastructure
readiness; the later job-220227 execution and retention are recorded below.
`bounded_three_root_vector_audit_complete`,
`dependency_necessity_established`, `route_rejections_independently_verified`,
and `vector_optimizer_executed` remain false, as do vector completeness,
minimality, optimized-vector audit, best-known status, publication and
publication union, public-graph application, A2, proof/admission/publication
authority, and all eligibility flags.

## A2.3c job-220227 bounded replay result

WMI job `220227` ran from clean commit
`a1830b8d019baaec72d1d2b3cc8046c72d22a336`, tree
`2bed15ee16c4c6b3360f4d6a711246e9020cfd9c`, and receipt-bound snapshot
`b8e30114001162ef4a189d702f55844bda4f401abd452d7e212f2aeecdfc3719`.
The exact retained accounting row is
`220227|COMPLETED|0:0|0:0|89||4G|1|c3n1`. Hash-seed-0 and hash-seed-1 fresh
runs of the same replayer implementation exited 0 after 43.924 and 43.784
seconds and emitted byte-identical output. This is a determinism check, not
two independent implementations. The separate seed-2 tactic-free verifier
exited 0 after 0.608 seconds. Execution is classified
`two-replayer-byte-identity-and-independent-structural-verification` and
collection is
`completed-dual-replayer-and-independent-structural-verification`.

The canonical evidence identities are:

| evidence | bytes | artifact SHA-256 | document root SHA-256 |
|---|---:|---|---|
| candidate | 322,779 | `46989ea781e1f66b585c5e0817fdf4e76ba24ff34feec71e9cea2162289f2dba` | `f17e8c4a2b8080401376ab04f96d771b466946b87b816cb99be54299cbd6a02f` |
| tactic-free verification | 27,484 | `48884600840c37044e099683b832659aec1fb22e4068637ad7212c104fe10293` | `364d4ee4099856c44ee1633439f2e5b1c57ae24cc90d9178cdf7445008504733` |
| execution receipt | 20,492 | `f5c051493fac987a4010043b2bc0b5ef85a8cf37976aff36b331a3c57c93c5b1` | `60513353afa2539f82568ae4360d98192584920af4bfd530d930e97e94efacdf` |
| collection receipt | 8,967 | `2f187bde83cdd2bba97cacb0af0a6dcc4c204e6d0eb224ff5732e2433ed6266d` | `17421fa3ebdf15020acc2bafad9ce100641d3403b2ce938a9c0b02fc42286814` |
| source state | 2,500 | `4fbcb219cf746da206fb07b99f6149922b761fff551fafd0b28f557bc53bf0b0` | `832372c5838b2cf3230f5d305ba6b4c9350d165e3c68debe1667f7fa6653722b` |
| Git verification | 29,334 | `42ebb8a353b205916a167de74bf3adc8412f9e16ad2bae8dab9213a7a37b8b8d` | `85825e1ac8a9e7255fc64afd305bee99d93dac44382dd64e1723483388eeb7b7` |
| WMI infrastructure | 5,858 | `2057bc1ab33e2cd863062bc370bb16b6d8f7022592b7ca73be5b05850282ecce` | `5fb4363d47b5d0bc55ab68186f158087c3750e0a512361acf9c2d711e0f41f43` |

The candidate theorem-record root is
`823b26485a1e345aca8b925974641301fd122097c52c05ff842e34b09d44787d`;
the verifier theorem-record root is
`fb67221ddc8163cf3c62cabc3d79d0d63d544a485a020c18272cf8af3c605274`.
The replay accepted one full-vector baseline for each of roots 256, 376, and
379, at aggregate root
`768aa4b5edd9eb44615b62d505944eafd57cdf8fc3f106a43d6168c9be4fc415`.
The independent wrapper then reproduced exactly 3 / 14 / 5 reverse-order
single-omission observations. Their 22-record root is
`6db464c56b52449144f3934214c292dff485910e43421a1763b7203515c0f304`.
Each fresh observation is structurally joined to its readable and proposed-
layered A2.3b rows, giving 44 labels at join root
`db60c479b5a0c3b621f958e5ef01c98ef095df975a1d51893309ec0cac730ebf`.

Independence is still layer-specific. The replayer's fresh wrapper does not
import the A2.3b producer, call `compile_candidate_body`, or run either route
assembler, but it shares the pinned parser, tactic engine, and intuitionistic
kernel. It therefore independently reproduces the 22 exact wrapper-level
script/omission observations without independently rejecting either route or
proving dependency necessity. The standard-library-only verifier is tactic-
free: it authenticates and reconstructs the candidate and its receipts, but
does not rerun a baseline or omission, bind tactics to runtime semantics, or
bind the later execution receipt. Its corresponding four flags remain false.
An isolated post-run audit under hash seed 31337 reproduced the retained
27,484-byte structural receipt byte-for-byte; that is independent structural
reproducibility, not another tactic execution.

The nested bundle at `a23c-wmi-negative-replay-220227/` contains exactly 17
regular files: two canonical results under `results/`, the source-state, Git,
infrastructure, source-provenance, deposit, submission, accounting, execution,
collection, and bounded log records. Their total is 419,166 bytes. All files
are mode 0644,
directories are 0755, and no symlink is retained. The C-sorted
`<sha256>\t<bytes>\t<relative-path>\n` inventory root is
`05d80cae1648769a377d3d5fc429f0edac0f484bd526b2607e236930baf282d0`.
There is no top-level result copy, transfer archive, full source snapshot,
global ledger, or job pointer. The 282,733,056-byte archive is omitted, so the
snapshot SHA-256 is receipt-bound rather than independently rehashed from
retained archive bytes. The duplicate seed-1 candidate and both candidate-
valued replayer stdout files are omitted; the retained candidate is their
normalized representative, so post-retention dual-output identity is
execution-receipt-bound. A live scheduler batch observation reported
`136692K`, but the retained `sacct.psv` row has blank `MaxRSS`; this bundle
supports no retained peak-memory or memory-ceiling claim.

The exact retained-result test source is 36,808 bytes at SHA-256
`624cefad17d2a419958a5334459121f344c1f941ef229f0bb3db3ef867309ec8`;
its four tests passed in 0.52 seconds. The CI sharder passed 32 tests in
0.11 seconds. The combined bounded A2.3c gate passed 155 tests in 25.20 seconds.
The 108-entry CI profile assigns the result test 3,500 ms and models eight
loads of 544,500 / 544,500 / 544,800 / 545,000 / 545,000 / 545,000 /
545,000 / 544,500 ms.

This completes only the bounded job-220227 execution-and-retention subgate:
three unique baseline records executed in each seed-0/seed-1 run, 22
independently reproduced exact wrapper observations, and their structural join
to 44 route labels. It does not complete the vector
audit. `route_rejections_independently_verified`,
`dependency_necessity_established`,
`bounded_three_root_vector_audit_complete`, and `vector_optimizer_executed`
remain false. A genuine optimized-construction vector and its independent
audit, vector/global completeness, minimality, best-known status, publication
and publication union, public-graph application, A2, all authority, and every
training/retrieval/evaluation eligibility claim remain open. The public graph
is unchanged at exactly 1,038 edges.

## A2.3d one-root Cut-liveness source protocol (source checkpoint)

Frozen on 2026-08-14, A2.3d is source-only readiness for one exact
proof-producing transformation. It authenticates retained `odd_add_odd`
(index 256, artifact prefix `7ecd5c3f…`) and the exact artifacts behind its
declared outer Cut spine `mul_add`, `add_succ_left`, `add_assoc`, `add_comm`.
The producer keeps those lemma certificates opaque and processes the spine
inner-first with binder-aware proposition-hypothesis indexing. It retains
`add_comm`, deletes vacuous `add_assoc`, deletes vacuous `add_succ_left`, and
retains `mul_add`, deriving this proof's direct vector
`[mul_add, add_comm]`.

The empty-context kernel-checked proof has SHA-256
`5c480eb51b7bd0f1f0f8b3485cc071dc1f78aea2baace449533cad27d6dcf6b4`.
Its 11,958-byte canonical carrier has SHA-256
`c606af87e62b2e4d94303a0c8313efa9033d91c26321f7392351f471927ddc22`,
240 proof nodes, depth 30, five Cuts, and deterministic replay fuel 1,936.
Initial and derived vector LF roots are
`9bb59dbdeb07badb9f8ca9d0cc951b71f38dbf7c3edcb1b189d53efcba1708cc`
and `ca9176e5c542ed28309d630ef0cb06e69f4edad391a3505e498207b83ac830c4`.
The retained-graph descriptive closure stays
`zero_add`, `add_succ_left`, `add_comm`, `add_assoc`, `mul_add` at LF root
`a4abec5d9eb955ed95f6eea761c96c3de0166b3df3c64fe8e898d8766ed5c5f2`;
the two dropped direct names remain reachable. Closure is context computed
independently from the retained manifest, not an input dependency vector.

The exact six-file source freeze is:

| source | bytes | SHA-256 |
|---|---:|---|
| [`../../training/peano_hydra/library-pilot-dependency-vector-cut-liveness-schema-v1.json`](../../training/peano_hydra/library-pilot-dependency-vector-cut-liveness-schema-v1.json) | 12,566 | `388190b4235b9892b38193714b0331a35b6c533c0605072c5d0663ad9cd9c0aa` |
| [`../../training/peano_hydra/library_pilot_dependency_vector_cut_liveness.py`](../../training/peano_hydra/library_pilot_dependency_vector_cut_liveness.py) | 55,485 | `9d657c7698faf89bc83d43aff9116493492eed4d854a8ef21968d10b91574abe` |
| [`../../scripts/build_peano_hydra_library_pilot_dependency_vector_cut_liveness.py`](../../scripts/build_peano_hydra_library_pilot_dependency_vector_cut_liveness.py) | 38,965 | `03b160f5515027dc5ea8dac58d9f1225ec87a363b079386d23498c38fc6cfb16` |
| [`../../training/peano_hydra/library_pilot_dependency_vector_cut_liveness_verifier.py`](../../training/peano_hydra/library_pilot_dependency_vector_cut_liveness_verifier.py) | 81,450 | `63ab7b96cee903f3ea2af4bda64d52409b656ea700a725332c0c569c9f3b3108` |
| [`../../scripts/verify_peano_hydra_library_pilot_dependency_vector_cut_liveness.py`](../../scripts/verify_peano_hydra_library_pilot_dependency_vector_cut_liveness.py) | 35,415 | `a71bc1a2a802e130b4688ffb702659d15c6ea94120090ee00df3e4a23fda9523` |
| [`../../peano-lab/py/tests/test_peano_hydra_library_pilot_dependency_vector_cut_liveness.py`](../../peano-lab/py/tests/test_peano_hydra_library_pilot_dependency_vector_cut_liveness.py) | 56,843 | `6f5686484596328d1f64bd6bed7e109f3459a54aaf6b3754c546e96e4a74e725` |

The schema semantic SHA-256 is
`9e8887072cc6051cf9cb9177609ab31aed35ca305a42c7d9c22d4ac339b6f5c5f`.
The no-default-write CLI is pinned to CPython 3.12 and runs captured,
authenticated source bytes in a fresh bounded child. The independent verifier
reconstructs the exact transform and exact evidence shape. Its 85 focused
synthetic/adversarial tests passed in 16.18 seconds. The conservative 20,000 ms
weight makes 109 explicit CI profile entries and eight modeled loads of
547,000 / 547,500 / 547,300 / 547,500 / 547,000 / 547,000 / 547,500 /
547,500 ms.

This source checkpoint created no result artifact and ran no real campaign,
network call, WMI job, execution receipt, or retention. The later bounded run
and retained evidence are recorded below. The
two-name vector is only the output of exact vacuous-root-Cut normalization,
not dependency necessity, global minimality, best-known or independently
audited optimized-vector evidence. Vector/global completeness, publication
and its union, graph application, A2, authority, review/lineage/freeze, and
all eligibility claims remain false. The public graph stays exactly 1,038
edges.


## A2.3d clean-Git/WMI execution infrastructure (pre-execution checkpoint)

At this checkpoint the execution boundary was frozen, but no job had run. A
detached clean-Git derivation authenticates the exact six A2.3d protocol
sources, `HEAD`, tree,
stage-0 blobs, modes, and clean status. The source-state document keeps
`git_verified=false`; its separate Git receipt is the clean-source evidence.
An immutable content-addressed deposit then binds that source state, Git
receipt, infrastructure manifest, and provenance row.

The runner is pinned to one CPU, 4,096 MiB, 15 minutes, and Linux x86_64
CPython 3.12.12. It will run two fresh copies of the same deterministic
producer at required seed 0 and require byte-identical 74,579-byte candidate
documents at artifact/root `a9077a7b…` / `fd0497da…`. A third process runs
the separately authored reconstructing verifier and requires its exact
12,737-byte artifact/root `8f6531d3…` / `b3c25367…`. The repeated producer
is a determinism check, not implementation or seed independence. The verifier
shares the authenticated codec and kernel and does not independently establish
kernel semantics.

| source | bytes | SHA-256 |
|---|---:|---|
| `../../scripts/build_peano_hydra_a23d_cut_liveness_source_state.py` | 43,334 | `1161c123a96158123107f452b22692ad9c516431e2bb71848d7e051994faf6f1` |
| `../../scripts/run_peano_hydra_a23d_cut_liveness_wmi.py` | 95,659 | `c737d05b74e39c6956bae9eaa97dd7bb606e98e718c6f06430ee05522fc523b8` |
| `../../scripts/submit_wmi_hydra_a23d_cut_liveness.sh` | 14,920 | `0f9552a739a1ba64e25e958498d22a6025ad8b83d7b1b1671c9fe421e06cf1d3` |
| `../../scripts/collect_wmi_hydra_a23d_cut_liveness.sh` | 5,692 | `6c570194a672c4f48aa0f4214e2918469214fe6ac57c4671a150fc621ec6e509` |
| `../../slurm/peano_wmi_hydra_a23d_cut_liveness.sbatch` | 5,057 | `de5463e13d626cd0e7c34c1ce96e0e3e7b5aaf5e6304453f794ac41f06c629d9` |
| `../../peano-lab/py/tests/test_peano_hydra_a23d_cut_liveness_source_state.py` | 13,797 | `3b3f90e687f7fdf71783480cfee5fb5c94085d2f7853f9e332c00cf1b7b31901` |
| `../../peano-lab/py/tests/test_peano_hydra_a23d_wmi_protocol.py` | 32,420 | `0927e477f321bed217bcac531057d68dc03658bc0bd5cba3743ea911a5d104ce` |

Descriptor/post-path source checks, bounded process groups, 16 MiB stream
caps, 60/60/90-second children, unknown-on-failure classification, held
submission, and descriptor-bound create-only receipts are all covered. The
source-state and WMI suites passed 12 tests in 5.86 seconds and 30 in 6.17
seconds; together they passed 42 in 12.25 seconds. The full bounded gate
passed 159 tests in 28.66 seconds, including 32 sharder tests in 0.28 seconds.
CI now has 111 profiles with 7,500/8,000 ms new weights and modeled loads
549,000 / 549,500 / 549,300 / 549,500 / 549,000 / 549,500 / 549,000 /
549,000 ms.

That infrastructure checkpoint retained no A2.3d candidate, verifier,
execution, collection, or result artifact and performed no network or WMI
action. Job 220246 and its retained result are recorded below. Dependency
necessity, route rejection, minimality,
optimized/best-known or completeness claims, publication/union, graph
application, A2, authority, review/lineage/freeze, and eligibility remain
false. The public graph remains 1,038 edges.

## A2.3d job 220246 bounded execution and retained result

The canonical evidence bundle is
[`a23d-wmi-cut-liveness-220246/`](a23d-wmi-cut-liveness-220246/). It binds
clean commit `25228180c956456145eba64601e829103731e903`, tree
`528ca1d3c0e697048479acdd690b54a9d13fa469`, and snapshot
`52480a731e184565a0f6627d62d6b034d9c4f2a66fa5e508335def68998c9a7d`.
Job `220246` completed `0:0` on `c3n1` in three seconds with one CPU and 4 GiB
requested. Its exact accounting row has blank `MaxRSS`; the bundle therefore
makes no peak-memory or memory-ceiling claim.

Both fresh seed-0 executions of the same producer emitted an identical
74,579-byte candidate at artifact/root
`a9077a7b272930477b93c48baef8b14fe0e443627c52177efa863ed0c18375e0` /
`fd0497da5ea0c12ecb14fa168637ea6d54006ce9b9295010e879df37f5dcd835`.
This establishes deterministic repeatability only. The theorem-record root is
`a90eef83d3344369496a6d54254aa38cba4fb082ab3ba399742f36babfaad803`.
The construction keeps `[mul_add, add_comm]` and the exact 11,958-byte
kernel-accepted artifact `c606af87…`, proof `5c480eb5…`, fuel 1,936, and
240/30/5 nodes/depth/Cuts.

The separate verifier independently reconstructed the step ledger, vector,
proof, and artifact while sharing the authenticated codec/kernel. Its
12,737-byte artifact/root is
`8f6531d3a0544a6d308ebd0abf7e41ed2436984758e76e66797ff1023e0a2821` /
`b3c253674f488eeed1e5a14e4be6632b0fe6ed946cf611ee0b3fde66f79acad7`;
a fresh local seed-31337 replay reproduced it byte-for-byte. The 19,383-byte
execution receipt has artifact/root `46922d976e00925a62bef9792bdeaa50c6e6800d9d034c132fae6b952be35bc7` / `28e660ea1b9f455c2cbb9022b045fc9ef57922c0bf007d413de2ca106d31ead1`; the 8,942-byte
collection receipt has `1f8907520cc2e7508a841719f43111538245a6c640de042b422213da0dc5de3a` / `fe9d57683008f8b61768a133d8ba453d2819e337c31fd1afe4ee397a7b880fb1` and accepts the exact
terminal scheduler, source, process, and log joins.

Source state, Git receipt, and infrastructure manifest are retained at
artifact/root pairs `1e0315e75364721408799db01db3b7f39896d84c26b83c50bcd103994533a421` / `7db294f75a67cd6252c2831dd8ae11ba5ba0d185a736328031e0724602b38363`, `3a207d46b9142ca951705cac066221e1d2b6b54005d542b9275b4585360e6876` /
`3194cbf1ff2041fe448ac4c3781356c8e28d79acd43c22dbd4b5c597e2beb7da`, and `afcf38c94167814123950b47aa38cb97d8564c89adf2ecc976a320a7525a585f` / `09a05076bc8e57174790575d59e41a0b4c0090602f8305465e84339b172fc01e`. The source state correctly keeps
`git_verified=false`; clean-Git evidence belongs to the separate receipt. The
closed bundle has exactly 17 regular 0644 files, 174,231 bytes, 0755
directories, no symlinks, and C-sorted inventory root
`db3914f58b1ab4019fbe447c6454a261ec9a32e74b7a25772e0483bfbad2ac81`.
Four byte-identical candidate/stdout blobs are normalized to one canonical
candidate. The 283,796,480-byte transfer archive, full source tree, duplicate
run-local outputs, global ledger, and job pointer are intentionally omitted.

The 33,018-byte result gate at SHA-256
`ba6e9e1f96b214582cb8201a1207b7f6954e227aa78525a9c8a0f5f7f0009ae7`
passed four tests in 0.63 seconds. The sharder passed 32 in 0.09 seconds; the
bounded combined gate passed 163 in 29.27 seconds. The 112-entry profile gives
this test 2,500 ms and models 549,500 / 549,500 / 549,800 / 549,500 /
549,500 / 549,500 / 549,500 / 549,500 ms.

This is one theorem's proof-liveness normalization, not dependency necessity,
route rejection, logical/cardinality minimality, a global optimizer, or
best-known evidence. Global `optimized_vector_independently_audited`, vector
completeness, publication and union, graph application, A2, authority,
review/lineage/freeze, and eligibility remain false. The public graph remains
exactly 1,038 edges.

## A2.3e one-root optimized-construction comparison (source checkpoint)

A2.3e is a tactic-free source protocol over four already retained and
independently checked `odd_add_odd` artifacts. It authenticates the exact
A2.3a and A2.3d candidate/verification pairs and reconstructs the following
fixed universe:

| candidate | bytes | nodes | depth | Cuts |
|---|---:|---:|---:|---:|
| retained replay | 14,977 | 302 | 32 | 7 |
| A2.2 direct-Cut rebuild | 13,640 | 274 | 31 | 6 |
| layered closure | 12,709 | 269 | 37 | 3 |
| Cut-liveness | 11,958 | 240 | 30 | 5 |

The componentwise frontier is `layered-closure` plus `cut-liveness`; the
registered fixed-set tie-break selects `cut-liveness`. The layered artifact
still has two fewer Cuts, so this is neither componentwise dominance nor a
global/best-known comparison. The exact `[mul_add, add_comm]` vector is
theorem-scoped and construction-derived from the independently reproduced
A2.3d transform. It is not dependency necessity or cardinality minimality,
and the layered package remains packaging rather than a vector optimizer.

| source | bytes | SHA-256 |
|---|---:|---|
| [`../../training/peano_hydra/library-pilot-optimized-construction-comparison-schema-v1.json`](../../training/peano_hydra/library-pilot-optimized-construction-comparison-schema-v1.json) | 9,702 | `f927f2c0590a82495498230a7b6c159e63c8670162540fdd5283f86cccb35d54` |
| [`../../training/peano_hydra/library_pilot_optimized_construction_comparison.py`](../../training/peano_hydra/library_pilot_optimized_construction_comparison.py) | 33,466 | `b7242039928552c1a38b23ac555d8998caa74bf4e9c7d68830cc53a8001acfd4` |
| [`../../training/peano_hydra/library_pilot_optimized_construction_comparison_verifier.py`](../../training/peano_hydra/library_pilot_optimized_construction_comparison_verifier.py) | 35,352 | `552be2d82cda8d4b0c8c5131196e45b1904b249b2c648ddbce71b13bd11d565c` |
| [`../../scripts/build_peano_hydra_library_pilot_optimized_construction_comparison.py`](../../scripts/build_peano_hydra_library_pilot_optimized_construction_comparison.py) | 11,136 | `0e4d228eeb4f53458226cc5e20d8dfd2249719e271021aa8fc299286f339aa0f` |
| [`../../scripts/verify_peano_hydra_library_pilot_optimized_construction_comparison.py`](../../scripts/verify_peano_hydra_library_pilot_optimized_construction_comparison.py) | 11,633 | `c3627ce6e22b493766c72f4f5eae1085f60240487303480f8271d00d5bd8c765` |
| [`../../peano-lab/py/tests/test_peano_hydra_library_pilot_optimized_construction_comparison.py`](../../peano-lab/py/tests/test_peano_hydra_library_pilot_optimized_construction_comparison.py) | 18,213 | `551ef130eb9029582467100ef5348ab6efc6cb9890249e672aac83f0b5495689` |

The focused test passed 27 cases in 0.54 seconds; the sharder passed 32 in
0.18 seconds; the combined gate passed 59 in 0.68 seconds. At that source
checkpoint CI had 113
profiles, a 1,500 ms weight, and loads 549,500 / 550,000 / 549,800 / 549,500
/ 549,500 / 550,000 / 550,000 / 549,500 ms.

This was the source checkpoint. The bounded local execution below now retains
the aggregate and receipt without adding a job, tactic/kernel execution,
publication, graph change, or broader authority.

### A2.3e retained local aggregate

The exact source commit is
`7e0c24ee917f859551452b0a2a41f73dd18e51d7` with tree
`64c25f1801630eb7a4864034cf6cbac7b8cd2378`. Controlled CPython 3.12
`-B -P -s -S` builds and separately authored stdlib-verifier runs reproduced
the retained documents byte-for-byte across repeat launches:

| retained document | bytes | artifact SHA-256 | root SHA-256 |
|---|---:|---|---|
| [`a23e-local-fixed-comparison-7e0c24e/results/l0-pilot-optimized-construction-comparison-candidate-v1.json`](a23e-local-fixed-comparison-7e0c24e/results/l0-pilot-optimized-construction-comparison-candidate-v1.json) | 14,953 | `213107ea9d940f3cbd998e3deb22bdae3e6a1a9aaa4ab945bfbea9899e25cd08` | `054a1f78ca16647f5a6b003570b20791295a4b5e9f7b127de170f4e6e1e7de03` |
| [`a23e-local-fixed-comparison-7e0c24e/results/l0-pilot-optimized-construction-comparison-independent-verification-v1.json`](a23e-local-fixed-comparison-7e0c24e/results/l0-pilot-optimized-construction-comparison-independent-verification-v1.json) | 11,247 | `1c1075c469550c5aef4e4500819a548ade66ca5166a811bc0dc391c6fecd23bb` | `d62c417f1eb5cf8597c7ee8492e2b3610fdfd834c0f9ef474f110d2f9d963c8c` |

The bundle is exactly two regular 0644 files / 26,200 bytes under 0755
directories, has no symlinks, and has C-sorted inventory root
`b70e6c34c7954551cd21a812ef12a21668718261a31e8c0f255487eff54b37ad`.
The 13,347-byte four-test result gate has SHA-256
`5b0a424bdb06e6dcfbab3ae3cf210ed151779da34d38c0c67562cf992f4a436a`
and remains a four-test artifact gate. The Linux CI portability follow-up
changes no retained artifact or frozen A2.3c/A2.3d source: it selects the
active CPython 3.12 for A2.3e and replaces five nonportable unlink/recreate
fixtures at shard invocation with five deterministic preallocated-inode tests.
That new test is 5,475 bytes at SHA-256
`01f3af8ae0e4ea20cebe5e13758cca2b205a4998bbcd2086b9d10d2a84e71154`.
The bounded source/result/portability/sharder gate passed 68 tests in 0.91
seconds; the protected A2.3c/A2.3d retained-result gates passed 8 in 1.06
seconds. CI has 115 profiles, assigns 1,000 ms to the portability test, and
models loads 550,000 / 550,000 / 549,800 / 550,500 / 550,500 / 550,000 /
550,000 / 549,500 ms.

There was no WMI job, network access, tactic execution, fresh kernel execution,
or execution-authority receipt. Repeat runs show determinism, not independent
implementations. Global `optimized_vector_independently_audited`, best-known
or global comparison, necessity, minimality, vector completeness,
publication/union, graph application, A2, authority, review/lineage/freeze,
and eligibility remain false. The graph remains 1,038 edges.

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
