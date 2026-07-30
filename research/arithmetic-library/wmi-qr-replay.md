# WMI quadratic-reciprocity replay experiment

Status on **2026-07-31**: full 136-gate job `187187` ran on `cpu_idle`
against the exact approved dirty snapshot
`2bab0898a5bc628a0e1f06b5e6cdf56af86fe39c2fdbeaaa4147ac43d2c7faaa`.
The 338-member archive is 5,374,464 bytes, records base commit
`a549a537cfe3d3d7e8ef292a49250c4308d12c5d` with `local_dirty=true`, and
passed source/extracted transport checks, remote digest verification, and
scheduler validation before submission. It failed after 39 seconds with exit
code `1:0`: four gates passed, gate 5 exposed an unused `succ_ne_zero`
dependency, and 131 gates were unrun. This is a fail-closed hygiene result,
not a mathematical QR rejection or admission receipt. Earlier
focused and held submissions remain documented below; thirteen stale jobs
were cancelled without consuming CPU.

The historical submissions remain below. In particular, Wilson jobs `172855`,
`172899`, `172920`, `172927`, and `172932` were cancelled after zero CPU. The
first replacement batch used exact snapshot
`9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`:
jobs `172964` (`gauss-signed-half`), `172965` (`finite-omission`), and `172966`
(`wilson-square-one`) remain pending and valid; jobs `172967`
(`wilson-inverse-involution`), `172968` (`wilson-inverse-endpoints`), and
`172970` (`wilson-inverse-orbit`) were cancelled after zero CPU when cheap
all-stack replay exposed prerequisite source defects.

The corrected Wilson stack is staged in exact snapshot
`6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`.
Jobs `172975` (`wilson-inverse-prefix`), `172976`
(`wilson-inverse-involution`), `172977` (`wilson-inverse-endpoints`), and
`172978` (`wilson-inverse-orbit`) are pending at submission. All current jobs
had consumed zero CPU at the latest recorded poll. Pending is scheduler state,
not a pass or admission result.

Fermat jobs `172769` (`fermat-reindex`), `172770` (`fermat-balance`), and
`172837` (`fermat-endpoints`) were also cancelled after zero CPU when cheap
body preflight exposed two source defects. Their corrected exact snapshot is
`73d2863a0138c8dce1f8a7f2793bcd96f543e389c0c4af6cce75cc13005ac3d9`.
Replacement jobs `172988` (16 GiB, 2 hours), `172989` (16 GiB, 2 hours), and
`172990` (32 GiB, 4 hours) respectively run reindex, balance, and endpoints;
all were pending at submission.

The current Euler/signed-prefix/PairOrder tranche shares exact snapshot
`8c9c4ae067b0dc202684e410bee563cd592a67080cb7c9939440ae8b44d4bccd`.
Jobs `173015` (`euler-scaled-inverse`), `173016` (`gauss-signed-prefix`), and
`173017` (`wilson-pair-order`) are pending with zero CPU. Their three remote
test-only validations returned exit zero after the transport changed from
`bash -l -s` to `bash -s`: the WMI login-shell logout hook had overwritten an
otherwise successful validation status with local exit 1. Test-only
validation is scheduler/provenance evidence, not proof replay or admission.

The second frozen checkpoint is exact snapshot
`fd129d34bf4a31a131a28d55bc6a16153984e0d37ac24dcefe7c2735cfb058d1`.
Jobs `173021` (`gauss-magnitude-permutation`) and `173022`
(`wilson-pair-order-induction`) are pending with zero CPU. They have no replay
receipt and admit no theorem.

The current full checkpoint is exact snapshot
`2bab0898a5bc628a0e1f06b5e6cdf56af86fe39c2fdbeaaa4147ac43d2c7faaa`.
Job `187187` requests one CPU, 32 GiB and four hours for all 136 selected
non-diagnostic gates. It failed at gate 5/136 as described above.

The corrected upload candidate is locally frozen, but not uploaded, at
SHA-256 `989011c09d82dbbb239df43334e88553e1fb3e0d2f1033f93c5b8b1791851757`.
Two independent archive builds are byte-identical: 338 members and 5,374,464
bytes. A new WMI run requires separate content-specific authorization.

| Job | Snapshot prefix | Suite / provenance status |
|---:|---|---|
| `172707` | `e4a0ff3909b9704…` | original 22-gate integration baseline |
| `172716` | `27cf34986f0b7f0…` | first three Fermat product candidates plus integration |
| `172722` | `0d050e5d631a080…` | residue-map rungs 4--5 plus earlier gates |
| `172737` | `08cb916fee48cfd5…` | scale-product rung 7 plus earlier gates |
| `172769` | `c6e6cabbbaf8b617…` | original `fermat-reindex`; cancelled stale, zero CPU |
| `172770` | `c6e6cabbbaf8b617…` | original `fermat-balance`; cancelled stale, zero CPU |
| `172837` | `c7cc39f94b2cb0ae…` | original `fermat-endpoints`; cancelled stale, zero CPU |
| `172855` | `396af02c5aa4fdf6…` | original `wilson-square-one`; cancelled stale, zero CPU |
| `172899` | `1a11442b18dd6c40…` | original `wilson-inverse-prefix`; cancelled stale, zero CPU |
| `172920` | `cfa4eea18d4a746a…` | original `wilson-inverse-involution`; cancelled stale, zero CPU |
| `172927` | `7083e3876cc54daa…` | original `wilson-inverse-endpoints`; cancelled stale, zero CPU |
| `172932` | `5463565294da6d75…` | original `wilson-inverse-orbit`; cancelled stale, zero CPU |
| `172936` | `f8fd8a00f73754b9…` | stale pair-product snapshot; cancelled before start after a missing third rewrite |
| `172943` | `15b073f7a64a3878…` | second stale pair-product snapshot; cancelled before start after a separate missing third rewrite |
| `172946` | `9d890542b964d405…` | authoritative focused `wilson-pair-product` replay for the corrected two-spec graph |
| `172964` | `9a59e7a590223d48…` | `gauss-signed-half`; pending, zero CPU |
| `172965` | `9a59e7a590223d48…` | `finite-omission`; pending, zero CPU |
| `172966` | `9a59e7a590223d48…` | corrected `wilson-square-one`; pending, zero CPU |
| `172967` | `9a59e7a590223d48…` | first replacement `wilson-inverse-involution`; cancelled stale, zero CPU |
| `172968` | `9a59e7a590223d48…` | first replacement `wilson-inverse-endpoints`; cancelled stale, zero CPU |
| `172970` | `9a59e7a590223d48…` | first replacement `wilson-inverse-orbit`; cancelled stale, zero CPU |
| `172975` | `6d32a5ba65b2268d…` | corrected `wilson-inverse-prefix`; pending at submission |
| `172976` | `6d32a5ba65b2268d…` | corrected `wilson-inverse-involution`; pending at submission |
| `172977` | `6d32a5ba65b2268d…` | corrected `wilson-inverse-endpoints`; pending at submission |
| `172978` | `6d32a5ba65b2268d…` | corrected `wilson-inverse-orbit`; pending at submission |
| `172988` | `73d2863a0138c8dc…` | corrected `fermat-reindex`, 16 GiB/2 hours; pending at submission |
| `172989` | `73d2863a0138c8dc…` | corrected `fermat-balance`, 16 GiB/2 hours; pending at submission |
| `172990` | `73d2863a0138c8dc…` | corrected `fermat-endpoints`, 32 GiB/4 hours; pending at submission |
| `173015` | `8c9c4ae067b0dc20…` | `euler-scaled-inverse`; pending, zero CPU |
| `173016` | `8c9c4ae067b0dc20…` | `gauss-signed-prefix`; pending, zero CPU |
| `173017` | `8c9c4ae067b0dc20…` | `wilson-pair-order`; pending, zero CPU |
| `173021` | `fd129d34bf4a31a1…` | `gauss-magnitude-permutation`; pending, zero CPU |
| `173022` | `fd129d34bf4a31a1…` | `wilson-pair-order-induction`; pending, zero CPU |
| `187187` | `2bab0898a5bc628a…` | failed after 39 seconds at gate 5/136 on an unused-dependency mutation; four passed, 131 unrun, no QR result |

Jobs `172707`, `172716`, `172722`, and `172737` are user-held, not cancelled,
to prioritize focused prerequisite jobs. This action is reversible; release
the holds after focused results settle. Cancelled jobs `172855`, `172899`,
`172920`, `172927`, `172932`, `172936`, `172943`, `172967`, `172968`,
`172970`, `172769`, `172770`, and `172837` are retained only for provenance
and provide no proof evidence.

Pending or held is not a WMI test result: this note does not claim that any
active job started, completed, or passed. Complete hashes in the remote `snapshot.tsv` and
`submissions.tsv` records are authoritative; prefixes are only human labels.

## Purpose and boundary

The WMI route is an isolated experiment for the expensive native-PA replay
gates added during the quadratic-reciprocity campaign. It answers a narrow
question: can the exact staged source replay the selected certificates and
survive their contract, capacity, hygiene, mutation, and full-ladder checks on
one reviewed WMI CPU allocation?

It is deliberately **not** the clean deployment path. The archive is made from
the current working files, including relevant tracked modifications and
untracked campaign files. Its recorded Git commit identifies the base of that
working tree; it does not imply that dirty content belongs to that commit. A
successful dirty-snapshot run would therefore be useful engineering evidence,
but it would neither publish those files nor admit a theorem to the native PA
library.

The experiment also does not replace the complete Peano, browser/Pyodide,
Jupyter Book, catalog, vault, or deployment gates. The current acceptance
runner selects 136 gates across 30 test-source modules. It has eighteen
focused five-gate suites for prerequisite replay, a six-gate static/body QR
surface suite, and a nine-gate layered QR admission suite. Three known-heavy
recursive QR gates live only in an explicitly diagnostic suite and are not
part of `full`.

## Resource and local-process policy

The Slurm requests are intentionally conservative. Current focused jobs other
than Fermat endpoints use the original/default profile; Fermat endpoint job
`172990` and the prepared, unsubmitted `full`, QR final, layered, and recursive
diagnostic suites use the reviewed high-memory profile.

| Resource | Default focused profile | Reviewed high-memory profile |
|---|---:|---:|
| partition | `cpu_idle` | `cpu_idle` |
| nodes | 1 | 1 |
| tasks | 1 | 1 |
| CPUs per task | 1 | 1 |
| memory | 16 GiB | 32768 MiB |
| wall time | 2 hours | `04:00:00` |

The proof replay is CPU-bound, so this route must not reserve a GPU merely to
reduce queue time. `cpu_idle` permits the scheduler to place the long audit on
otherwise idle CPU capacity. A pending job is normal scheduler state and is
not grounds for launching a duplicate locally.

The laptop is restricted to source/document editing, static syntax and
collection checks, bounded contract/helper/graph-isolation gates, and
dependency-curried body preflight under a hard 60-second OS cap. Such body
preflight leaves dependencies as hypotheses and is explicitly non-admitting.
Recursive Cut closure, real 557-body replay, cold full compilation,
certificate/RSS/capacity profiling, adversarial full-certificate mutations,
full-suite replay, and Jupyter Book builds run only inside the WMI allocation.
Laptop checks may compile the exact graph with deliberately trivial dummy
bodies: one scaffold preserves all expanded targets and must be kernel
rejected, while one preserves all 1,791 dependency edges using 557 distinct
shallow reflexive marker formulas and must be accepted. This checks every
real projection direction and local ID without replaying QR mathematics. The
separation avoids competing multi-hour processes on the workstation and
prevents a local exploratory run from being mistaken for the snapshot-bound
receipt chain.

The separate WMI Jupyter Book harness has completed an independent static
audit and remediation covering canonical immutable packaging, worktree-drift
guards, non-login environment isolation, source/output separation and
relative-link escape rejection. Default test-only scheduler validation
succeeded for frozen snapshot
`6feb5ebcdb9f59e6d94b71acd3fb2bce06d45b3a3885ad95aa8e9c02d61a3bcb`
with content-manifest SHA-256
`c09064eb67906761c357626df4ee9e0cf387a89b7593654c8c5bf74baf836c24`.
Real Book job `173024` was last observed `PENDING (Priority)` with zero CPU;
there is no Book-build or integrity result yet.

## Content-addressed snapshot and provenance

[`scripts/submit_wmi_qr_replay.sh`](../../scripts/submit_wmi_qr_replay.sh)
implements the transport boundary.

1. It resolves the repository root, records the exact 40-hex Git `HEAD`, and
   records whether `git status --porcelain --untracked-files=all` is nonempty.
2. It archives only the Peano Python library, Peano tests, the capacity
   profiler, WMI runner, submission wrapper, and Slurm script. Python bytecode,
   `__pycache__` directories, and macOS `.DS_Store` metadata are excluded.
3. The SHA-256 of that tar archive becomes the snapshot identity and remote
   run-directory name. The upload first lands at a nonce-bearing incoming
   path.
4. WMI recomputes the archive hash before extraction. Under an exclusive
   lock, it stages a new run directory or verifies that an existing directory
   carries the same snapshot/commit/dirty tuple. A mismatch fails closed.
5. The run's `snapshot.tsv` binds three independent facts:

   ```text
   snapshot_sha256<TAB>local_commit<TAB>local_dirty
   ```

6. Submission exports the same three values plus the selected suite into the
   Slurm environment. It appends timestamp, job ID, snapshot hash, base
   commit, and suite to `submissions.tsv`; the first four historical columns
   retain their original meanings.

This gives the experiment two identities with different meanings:

- `local_commit` names the clean Git base;
- `snapshot_sha256` names the exact staged archive;
- `local_dirty=true` says explicitly that the archive must not be represented
  as the contents of that commit.

The snapshot hash is provenance, not proof authority. The PA kernel still has
to check every closed certificate exercised by the selected gates.

Submission defaults to Slurm `--test-only`. A real job additionally requires
the explicit `PEANO-QR-WMI-REPLAY` confirmation token, so validation cannot
silently turn into resource use.

The remote command intentionally uses non-login `bash -s`. Earlier
`bash -l -s` invocations completed `sbatch --test-only` successfully but a WMI
logout hook overwrote the local status with exit 1. With `bash -s`, all three
test-only validations for snapshot `8c9c4ae0...` returned exit zero. This fix
changes transport status propagation only; it does not weaken snapshot,
resource, or proof checks.

## Selected suites and 136-gate full audit

[`scripts/run_qr_wmi_replay.py`](../../scripts/run_qr_wmi_replay.py) uses a
literal allowlist. A suite name chooses a subset of those exact functions; an
unknown or accidentally empty named suite fails closed.

| Suite | Scope | Gates |
|---|---|---:|
| `euler-scaled-inverse` | ten pointwise scaled-inverse contracts: bounded existence/uniqueness, symmetry, involution, fixed-point/square equivalence and fixed-point freedom, with body preflight, two cold closures, metrics/no-DNE and every-edge mutations | 5 |
| `fermat-reindex` | contracts, hygiene, dependency boundary, two cold replays, metrics, DNE and mutation checks for rung 6 | 5 |
| `fermat-balance` | the corresponding isolated audit for rung 8, recursively closing rung 6, scale transport, and general product reindexing | 5 |
| `fermat-endpoints` | contracts, helper hygiene, dependency topology, two cold profiled replays, Cut spines, and contract/dependency mutations for both Fermat endpoints | 5 |
| `wilson-square-one` | exact expanded contract, helper hygiene, 16-dependency boundary, two cold profiled replays, full Cut spine, no-DNE/capacity checks, and contract/every-edge mutations | 5 |
| `wilson-inverse-prefix` | exact zero-based helpers/contracts, seven-node recursive closure, two cold profiled replays, metrics/Cut/no-DNE checks, and contract/every-edge mutations | 5 |
| `wilson-inverse-involution` | six extensional-map contracts, prime-free scope audit for the first five, fixed-case audit, two cold profiled replays over a 14-spec recursive closure, and Cut/no-DNE/mutation gates | 5 |
| `wilson-inverse-endpoints` | three endpoint contracts including coincident prime-two semantics, hygienic helpers, exact 17-spec recursive graph, two cold profiled replays, Cut/no-DNE/capacity metadata, and false-contract/every-edge mutations | 5 |
| `wilson-inverse-orbit` | two constructive nonendpoint-orbit contracts including honest prime-two scope, hygienic helpers, exact 19-spec recursive graph, two cold profiled replays, Cut/no-DNE/capacity metadata, and false-contract/every-edge mutations | 5 |
| `wilson-pair-product` | two generic adjacent-pair product contracts, hygienic/canonical helper checks, exact two-spec source graph, two cold profiled replays, Cut/no-DNE/capacity metadata, and false-contract/every-edge mutations | 5 |
| `wilson-pair-order` | nine append/reflection, omission, inverse-orbit choice and invariant-preservation contracts, exact recursive graph, two cold profiled closures, Cut/no-DNE/capacity metadata, and false-contract/every-edge mutations | 5 |
| `wilson-pair-order-induction` | fifteen bounded-state, base, pair-step and terminal-coverage contracts, exact ordered graph, two cold profiled closures, no-DNE/capacity metadata, and false-contract/direct-Cut mutations | 5 |
| `wilson-pair-order-iteration` | full pair-count iteration and terminal specialization contracts, exact ordered graph, two cold profiled closures, no-DNE/capacity metadata, and false-contract/direct-Cut mutations | 5 |
| `gauss-signed-half` | two signed-half contracts, hygienic native helper and witness checks, exact source graph, two cold profiled replays, Cut/no-DNE/capacity metadata, and false-contract/every-edge mutations | 5 |
| `gauss-signed-prefix` | nine signed-half and aligned-prefix contracts, exact body metrics/helpers/graph, two cold recursive closures with capacity/no-DNE metadata, and strengthened-contract/every-edge mutations | 5 |
| `gauss-magnitude-permutation` | eleven magnitude-range, collision, injectivity, predecessor-recoding and finite-surjectivity contracts, exact graph, two cold profiled closures, no-DNE/capacity metadata, and false-contract/direct-Cut mutations | 5 |
| `gauss-sign-factor-recode` | three constructive bit-to-sign-factor recoding/product-power contracts, exact graph, two cold profiled closures, no-DNE/capacity metadata, and false-contract/direct-Cut mutations | 5 |
| `finite-omission` | eight constructive finite cover/choice/omission contracts, hygienic helper checks, exact source graph, two cold profiled replays, Cut/no-DNE/capacity metadata, and false-contract/every-edge mutations | 5 |
| `quadratic-reciprocity-final` | four exact endpoint/body gates plus the source-manifest and dependency-graph static audits; no recursive closure or known-failing recursive capacity gate | 6 |
| `quadratic-reciprocity-layered` | exact 557-node/45-layer adapter statics; expanded-target rejecting and 1,791-edge accepting scaffolds; exactly-once modular-body construction; two cold layered compiles and unchanged-kernel checks; package/layer/body/target mutations; and unchanged 500k/100k/256 capacity gate | 9 |
| `quadratic-reciprocity-recursive-diagnostic` | two cold recursive closures, direct-Cut mutations, and the deliberately fail-closed recursive capacity comparison; excluded from `full` because the recursive certificate has a proven 731,482-node lower bound | 3 |
| `full` | every current Fermat candidate; Wilson square-one, inverse, orbit, pair-product, PairOrder, bounded induction and iteration candidates; Euler scaled inverse; Gauss signed-half/prefix/magnitude/sign-recode candidates; finite omission; exact QR endpoints/static graph; the layered unchanged-kernel admission experiment; and integration/capacity/ladder gates across 30 test sources | 136 |

The full suite consists of 5 Euler scaled-inverse gates, 5 finite-omission
gates, 5 Gauss signed-half gates, 5 Gauss signed-prefix gates, 5 Gauss
magnitude-permutation gates, 5 Gauss sign-factor-recode gates, 5 Wilson
pair-product gates, 5 Wilson PairOrder gates, 5 Wilson PairOrder-induction
gates, 5 Wilson PairOrder-iteration gates, 5 Wilson inverse-orbit gates, 5
Wilson inverse-endpoint gates, 5 Wilson inverse-involution gates, 5 Wilson
inverse-prefix gates, 5 Wilson square-one gates, 5 Fermat endpoint gates, 5
residue-reindex gates, 5 product-balance gates, 3 scale-product gates, 3
residue-map gates, 3 residue-product gates, 4 reindex-support gates, 4
general product-reindex gates, 4 bounded-unit gates, 2 capacity gates, and 8
full-ladder gates, plus 4 exact quadratic-reciprocity endpoint/body gates, 2
recursive-graph statics, and 9 layered-admission gates. The runner source is
the authoritative ordered list. The 3 recursive diagnostics are deliberately
outside this count.

### Prepared layered acceptance and recursive diagnostic suites, not submitted

The `quadratic-reciprocity-final` selector is now a literal six-function
allowlist: the exact public surfaces and bodies plus the two static
source/graph audits. The old recursive construction has a rigorous structural
lower bound of 731,482 nodes against the unchanged 500,000-node policy. Its
three heavy gates therefore moved to
`quadratic-reciprocity-recursive-diagnostic`; that suite remains useful for
comparison but its capacity failure is not an acceptance failure and it is
not included in `full`.

The actual admission experiment is `quadratic-reciprocity-layered`. It builds
each of the 557 dependency-curried ordinary proof bodies exactly once per cold
pass by executing its declared tactic script under its declared hypotheses.
No theorem name, source hash, or graph hash supplies proof authority. The
untrusted compiler groups the resulting ordinary proofs into 45 balanced
conjunction packages and returns one ordinary `Cut` certificate. On each of
two cold passes, the unchanged constructive kernel must check that certificate
from the empty context against the exact expanded
`QUADRATIC_RECIPROCITY_COMBINED` formula.

Its strict-JSON receipt includes body counts and aggregate body digest; wall,
body-build, compile, and kernel-check time; peak RSS; proof
nodes/objects/edges/depth; package-formula structural occurrences and maximum
depth; proof-annotation occurrences and combined proof-envelope depth;
layer/package/proof hashes; and the unchanged 500,000-node,
100,000-object, depth-256 proof policy plus the five-million-annotation and
depth-256 envelope result. False-target, swapped-layer,
dependency-cycle, package-proof, and root-body mutations must all fail closed.
The package metrics are capacity evidence only; the unchanged kernel check is
the sole proof authority.

Two laptop-safe full-topology receipts pin the integration before any real
body replay. With the 557 exact expanded targets and deliberately invalid
`EqRefl(0)` bodies, compilation has 45 layers, 144,197 package-formula
occurrences at depth 68, a 13,715-node/depth-56 certificate, and
157,579 annotation occurrences at envelope depth 92; the unchanged kernel
rejects it. With 557 distinct shallow reflexive marker targets and
type-pinning bodies that consume every one of the 1,791 declared dependency
hypotheses, compilation has 19,297 package-formula occurrences at depth 18
and a 19,088-node/depth-74 certificate with 142,346 annotations at envelope
depth 84; the unchanged kernel accepts it.
Swapping the two dependency IDs of `beta_range_empty` preserves an acyclic
compilable graph but makes that second certificate kernel-invalid. Thus the
safe surrogate tests the real projection IDs, order, and context indices, not
merely the graph shape.

The archive stages the complete `peano_lab` and `tests` directories, so
dirty-worktree candidate modules and the new closure test are included. The
earlier candidate-file quarantine exclusions were removed because several of
those files are genuine ancestors of the final 84-factory source manifest.
The `full`, QR final, layered, and recursive diagnostic suites request one
`cpu_idle` CPU, 32768 MiB and four hours. When a selected gate fails, the
runner preserves its original traceback and attempts the source's strict-JSON
metadata hook before returning; a broken hook becomes an additional failed
row and cannot turn the suite green. Neither QR hook repeats failed heavy
work. Layered discovery records its current body-build, compile, kernel-check,
wall-time and RSS phase incrementally in a non-authoritative JSON-only partial
receipt; the hook returns that state when no completed discovery is cached.
The recursive hook likewise returns static failure state rather than starting
another recursive closure. For `full` and `quadratic-reciprocity-final`, that
recursive hook is statically gated and reports `not_selected`; only the
explicit recursive diagnostic suite may consult cached recursive evidence.
This is transport preparation only: no archive was uploaded, no Slurm
validation ran, and no job was submitted.

### Prepared two-suite upload, not submitted

A local-only archive was prepared for exactly `gauss-sign-factor-recode` and
`wilson-pair-order-iteration`. It contains 197 regular files, is 3,552,256
bytes, and has SHA-256
`938b212fb594708f7cee05c12a10e7c709110619b70d71b3200a27e6e85ede1b`.
The payload explicitly excludes the six newer, not-yet-WMI-audited modules for
magnitude product, generic pointwise product/recode, signed pointwise product,
paired PairOrder iteration, and successor lifting. Both intended jobs request
`cpu_idle`, one node, one task, one CPU, 16384 MiB, and `02:00:00`.

Under a 60-second local CPU cap, shell syntax, Python AST parsing, exact
five-gate selection, wrapper help, resource assertions, and quarantine checks
all pass. No bytes have been transferred to WMI and neither job has been
submitted. Uploading this exact dirty-worktree snapshot still requires
explicit authorization; preparation is not a scheduler result or proof
receipt.

### Fermat body and structural preflight

The finite-product plus Fermat preflight now passes all 21 candidate bodies.
It caught and fixed a missing second rewrite in
`beta_successor_range_reindex_aligned` and removed an invalid locally
repackaged `hprojection` from `prime_mul_residue_product_balance`.

The reusable
`peano_lab.library.candidate_validation.replay_candidate_bodies` helper
kernel-checks dependency-curried scripts without replaying or closing their
dependencies and returns exact structural/identity metrics. Its three unit
tests pass. It is explicitly non-admitting and must never be treated as an
admission receipt. Key body-only nodes/depth are:

| candidate | body nodes/depth |
|---|---:|
| `beta_successor_range_reindex_aligned` | `86/34` |
| `beta_successor_range_scale_mod` | `62/32` |
| `prime_mul_residue_reindex_exists` | `106/40` |
| `prime_mul_residue_product_balance` | `93/39` |
| `fermat_predecessor_exponent_mod_one` | `93/34` |
| `fermat_little_all_inputs` | `104/30` |

Nine bounded structural gates pass across `fermat-reindex`, `fermat-balance`,
and `fermat-endpoints`—three per suite. These body and structural receipts are
not closed recursive replay or closed-certificate admission and admit no
theorem. The corrected WMI jobs are `172988`, `172989`, and `172990` from
snapshot `73d2863a0138c8dce1f8a7f2793bcd96f543e389c0c4af6cce75cc13005ac3d9`;
all remain pending at submission.

### Bounded local body and structural receipts

A cheap all-stack body replay now succeeds for all 19 Wilson candidates. It
caught and fixed two existential-binder errors in
`wilson_inverse_prefix_candidate.py` and one apply-to-negation error in
`wilson_inverse_orbit_candidate.py`. The body-only nodes/depth measurements
are:

| layer | candidates in source order | body nodes/depth |
|---|---|---|
| square one | `prime_bounded_square_one_cases` | `182/48` |
| pointwise inverse | four candidates | `55/22`, `70/28`, `50/21`, `20/12` |
| inverse prefix | three candidates | `76/29`, `64/25`, `29/16` |
| inverse involution | six candidates | `44/23`, `49/25`, `80/29`, `55/29`, `31/22`, `83/31` |
| inverse endpoints | three candidates | `76/23`, `54/23`, `104/32` |
| inverse orbit | two candidates | `45/26`, `206/40` |

The square-one candidate no longer invokes the UI-only `ring` tactic. Its
normalization is an explicit native equality/rewrite derivation, and its direct
boundary is 16 dependencies, including `mul_succ_left`.

The signed-half bodies measure `125/34` for
`odd_upper_remainder_reflection` and `116/38` for
`gauss_pointwise_signed_half_representative`. The eight finite-omission bodies,
in theorem order, measure `73/22`, `69/27`, `58/23`, `21/15`, `89/31`,
`149/43`, `24/16`, and `27/18`.

The ten-spec
[Euler scaled-inverse ladder](euler-scaled-inverse.md) constructs the bounded
scaled inverse, proves functionality, symmetry and involution, and identifies
fixed points with square roots. Its body-only nodes/depth, in source order,
are `36/17`, `30/19`, `58/25`, `126/34`, `74/24`, `31/12`, `28/19`,
`38/15`, `17/15`, and `24/15`.

The nine-spec Wilson [PairOrder extension](pair-order-encoding.md) appends two
β entries, extracts a fresh nonendpoint inverse orbit constructively, and
preserves orbit closure, nonendpoint range and injectivity. Its body-only
nodes/depth are `63/27`, `115/32`, `113/30`, `138/43`, `34/20`, `167/38`,
`63/31`, `202/36`, and `191/53`. Fifteen corrected follow-on bodies add
boundedness to the state and prove base/step arithmetic and terminal coverage:
`95/40`, `19/12`, `69/27`, `90/42`, `23/19`, `18/14`, `20/16`, `22/18`,
`64/19`, `8/8`, `12/9`, `266/44`, `33/20`, `72/37`, and `51/36`. At the
historical checkpoint described by the pending-job notes below, full
iteration, successor lift and product transport were still unauthored. The
current suite table above records the later PairOrder-iteration tranche.

The eleven magnitude-permutation bodies measure `39/25`, `48/24`, `96/34`,
`169/50`, `626/70`, `157/45`, `31/25`, `87/30`, `48/20`, `60/31`, and
`39/21`. Three later product-alignment bodies are green at `51/28`, `127/39`,
`72/34`; two sign-product/power bodies at `35/24`, `259/46`. At that same
checkpoint those five had no focused closed-replay suite, and β sign-factor
recoding plus the final product bridge were open. Later work produced the
five-gate sign-factor-recode suite and the exact QR stack listed above.

Both lists were checked only as dependency-curried bodies under the hard
60-second laptop cap. Their focused recursive, profile and mutation gates are
pending as jobs `173015` and `173017`; signed-prefix job `173016` shares exact
snapshot `8c9c4ae067b0dc202684e410bee563cd592a67080cb7c9939440ae8b44d4bccd`.
All three had zero CPU at the latest recorded poll and admit nothing.

Three bounded structural gates passed for each of square one, signed half, and
finite omission. Twelve more passed across inverse prefix, involution,
endpoints, and orbit—three per suite. These are the contract/dependency,
hygiene/native/witness, and graph/core/source-isolation surfaces. Body-only
replay and bounded structural gates do not recursively close dependencies,
are not closed-certificate admission, and admit no new theorem.

`wilson-square-one` was submitted as discovery job `172855` from exact
snapshot
`396af02c5aa4fdf62d4c3484f8a2c711b03c489cad498c121d0402ce3ee79981`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. It was cancelled stale
after zero CPU. Corrected replacement job `172966`, from exact snapshot
`9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
is pending with zero CPU and therefore has no report, pass, pinned metrics, or
admission effect. Its heavy replay and profiling run on WMI, not on the
authoring Mac.

Seven later Wilson inverse candidates remain isolated from the public registry.
The pointwise source provides
`prime_inverse_index_exists`, `bounded_mod_inverse_unique`,
`bounded_inverse_index_unique`, and `inverse_index_symmetric`; the prefix
source provides `prime_inverse_prefix_extend`,
`prime_inverse_prefix_exists_bounded`, and `prime_inverse_prefix_exists`.
They use a zero-based `InvIdx`: index `i` and decoded mate `j` denote residues
`S i` and `S j`, carry the bounds `i<n` and `j<n`, and carry a balanced witness
for `(S i)*(S j) ≡ 1 (mod p)`. `InvPrefix` says every position below its
length β-decodes such a mate.

The dedicated five-gate `wilson-inverse-prefix` suite closes the seven-node
candidate stack recursively and checks both helper surfaces, exact statements
and ordered dependency tuples, isolation from the registry, two cold recursive
replays, structural/object/depth/Cut metrics, no-DNE, full Cut spines, and
false-contract plus every-live-edge mutations. It was submitted as discovery
job `172899` from snapshot
`1a11442b18dd6c40b49975e16f0b2062be57fade347acca20d87dba27e6adffc`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. Cheap body replay later
exposed two existential-binder errors, so the zero-CPU job was cancelled stale.
The fixed prefix source is staged in snapshot
`6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`;
replacement job `172975` is pending. There is no report, pass, pinned metric
set, or admission to record. No heavy replay, profiling, or mutation work for
this tranche runs locally.

Six further isolated candidates turn the full inverse prefix into soundness,
extensionality, involution, injectivity, surjectivity, and fixed-point
classification. The first five are deliberately prime-free: entry soundness
has no condition, while the next four need only `p = S n`. Only
`prime_inverse_prefix_fixed_cases` assumes `Prime(p)`; its exact zero-based
conclusion is `i = 0 \/ S i = n`. The five-gate
`wilson-inverse-involution` suite recursively closes 14 isolated specs and was
submitted as job `172920` from snapshot
`cfa4eea18d4a746a49a2d7579f217dbd65a27a79df61c76e8dba49079ba1aaa4`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. That job and its first
replacement `172967` were cancelled after zero CPU; the latter shared snapshot
`9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`
and became stale when the prefix dependency was corrected. Job `172976`, from
corrected snapshot
`6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
is pending. There is no report, pass, pinned metric set, or admission effect.

Three endpoint candidates remain isolated on top of that 14-spec stack.
`inverse_prefix_zero_fixed` decodes `At(b,c,0,0)`;
`inverse_prefix_last_fixed` decodes `At(b,c,k,k)` using
`predecessor_square_mod_one`; and `prime_inverse_prefix_exact_endpoints`
packages `n=S k`, both entries, and the converse fixed-index classification
`i<n -> At(b,c,i,i) -> i=0 \/ i=k`. The statement deliberately permits
`k=0`, so the endpoint descriptions coincide at prime `2`.

The focused `wilson-inverse-endpoints` suite recursively closes all 17 specs.
Job `172927` was submitted from exact snapshot
`7083e3876cc54daa782153aa6e1a2554aa75fa5a40cce3d6cf6b5971979dc35d`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. That job and first
replacement `172968` from snapshot `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`
were cancelled after zero CPU when the prefix stack changed. The three bounded
structural gates passed locally. The heavy two-pass closed replay, proof/RSS
profiling, no-DNE/capacity checks, and adversarial mutations remain WMI-only.
Replacement job `172977`, from corrected snapshot
`6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
is pending discovery only, so there is no report, pass, pinned metric set, or
admission effect.

Two nonendpoint-orbit candidates remain isolated on top of the 17-spec stack.
`prime_inverse_prefix_nonendpoint_not_fixed` proves that a decoded mate cannot
equal an explicitly nonendpoint source. `prime_inverse_prefix_nonendpoint_mate`
uses involution, prime successor shape, the two fixed endpoint entries,
successor injectivity, and β uniqueness to prove that the mate is nonendpoint
as well. The contracts explicitly require `~(i=0) /\ ~(S i=n)` and neither
assert endpoint distinctness nor manufacture a nonendpoint at prime `2`.

The focused `wilson-inverse-orbit` suite recursively closes all 19 specs and
has five gates for exact contracts/helpers, dependency/core/source isolation,
two cold profiled closed replays with deterministic hashes/RSS/no-DNE/capacity
metadata, and false-contract plus every direct Cut-edge mutation. Job `172932`
was submitted from exact snapshot
`5463565294da6d757356985a0e8d353ad2e0e16ca1b21b99d2aa5cfa6bb5c6f6`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. Cheap body replay later
exposed and fixed an apply-to-negation error. That job and first replacement
`172970`, from snapshot
`9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
were cancelled after zero CPU. The three bounded structural gates passed, but
heavy replay, profiling, and mutation remain WMI-only. Replacement job
`172978`, from corrected snapshot
`6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
is pending discovery only, so there is no report, pass, pinned metric set, or
admission effect.

Two generic pair-product candidates remain isolated from the registry.
`beta_product_double_succ_decompose` splits an exact product of length
`S(S k)` into its `k`-prefix and final two factors.
`beta_adjacent_unit_pairs_product_one` inducts over `m` to show that an exact
product of `m+m` decoded factors is congruent to one modulo `p` whenever every
adjacent pair is. This is the generic arithmetic fold only; Wilson still needs
the nonendpoint inverse entries reindexed into that adjacent layout.

Bounded replay found two distinct missing third-occurrence length rewrites in
successive snapshots. Jobs `172936` and `172943` were cancelled before start
as known broken and superseded; they supply no evidence. After correction, all
five `wilson-pair-product` gates passed locally in 5.4 seconds, including two
cold passes. The decomposition measured 1,317 nodes/depth 63/844 objects; the
capstone measured 4,372 nodes/depth 64/1,290 objects. Graph SHA-256 is
`622496753bd474f9f64d5d3001424d3c4513d43d6a5256022cd5a172167959ec`;
source SHA-256 is
`193fe015b32ffde4d93e00720c9fef510a804228e24f19f5cc6c97e8ad5fa724`.

Authoritative job `172946` was submitted from exact snapshot
`9d890542b964d40580ad2f8f77fa83455de3b9af0f8ca905a37f6a6ee278e296`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. It remains queued/pending.
The local pass does not replace the independent WMI admission receipt, so
there is no WMI pass or theorem admission yet.

The two signed-half candidates remain isolated from the registry. Focused job
`172964`, from snapshot
`9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
is pending with zero CPU. The eight finite-omission candidates are likewise
isolated; focused job `172965` from the same snapshot is pending with zero CPU.
For each suite, the body-only measurements and three structural checks above
are preliminary local evidence only. Closed recursive replay, capacity/no-DNE
checks, adversarial mutation, and any later receipt-pinned admission remain
WMI work.

WMI's reviewed central interpreter does not provide pytest. The runner supplies
only the small `pytest.raises` context-manager surface needed by several
hygiene checks; it does not emulate discovery, fixtures, plugins,
parametrization, or the rest of pytest. A missing allowlisted function is an
error. Execution stops after the first failed gate while retaining a traceback
in the report.

## Slurm, JSON, and hash receipts

[`slurm/peano_wmi_qr_replay.sbatch`](../../slurm/peano_wmi_qr_replay.sbatch)
fixes `PYTHONHASHSEED`, disables user-site imports and bytecode writes, and uses
the reviewed central Python executable. For Slurm job `J`, the durable outputs
inside the content-addressed run directory are:

- `logs/peano-qr-replay-J.out` and `.err`, containing the per-gate start/pass/
  fail stream and environment identity;
- `logs/peano-qr-replay-J.json`, containing format/version, job ID, snapshot
  hash, base commit, dirty flag, selected suite, host/platform/Python identity,
  peak RSS, total duration, and one status/duration/error/traceback row per
  attempted gate;
- the SHA-256 of that JSON report, printed to Slurm stdout after a successful
  runner exit;
- `snapshot.tsv` and `submissions.tsv`, which connect the report back to the
  staged archive and scheduler submission.

A valid success receipt requires all of the following, not merely a Slurm
`COMPLETED` label:

1. the process exits zero and the JSON top-level status is `passed`;
2. the JSON contains exactly the gates selected by its recorded suite, in
   order, each marked `passed`;
3. JSON job ID, full snapshot hash, commit, and dirty flag match the Slurm
   environment and TSV provenance;
4. the report file's recomputed SHA-256 matches the digest printed in stdout;
5. stdout and stderr show no unaccounted alternate runner or source path.

Of the twenty noncancelled jobs listed above, `187187` is resolved as a
fail-closed hygiene failure; the other nineteen remain unresolved—fifteen
queued/pending and four user-held. None has established the full WMI success
conditions for its snapshot. All thirteen cancelled rows are
provenance only. Current Fermat jobs `172988`--`172990` have no pass receipt,
pinned-metric admission replay, or theorem-admission consequence. Current
Wilson discovery jobs are `172966` and `172975`--`172978`; signed-half and
finite-omission jobs are `172964` and `172965`. Each has the same strictly
discovery-only status. Pair-product job `172946` likewise has no WMI receipt
yet, despite the complete local gate pass. Euler, signed-prefix and PairOrder
jobs `173015`--`173017` are also pending with zero CPU and have no replay
receipt. Magnitude and PairOrder-induction jobs `173021`--`173022` are pending
with zero CPU and likewise have no replay receipt. User-held full jobs
`172707`, `172716`, `172722`, and `172737` were not cancelled and are to be
released after focused results settle.

## Admission rule

The dirty-worktree experiment can produce only one of three conclusions:

- **pending/running:** no result;
- **failed:** diagnose against the exact snapshot, then create a new snapshot
  for any correction rather than altering the old run directory;
- **passed:** evidence that this exact dirty snapshot clears the selected WMI
  gates, and nothing stronger.

Native-library admission requires a separate clean chain. The reviewed source
must first be committed so `local_dirty=false` and the commit identifies its
actual contents. The selected gates must then be reproduced from that clean
source with matching exact statements, dependencies, metrics, hashes, empty-
context kernel checks, constructive/no-DNE audits, and adversarial mutations.
The complete repository, browser, book, catalog, vault, and deployment gates
must also pass. Only then may registry and catalog records say `checked` and a
clean deployment be published.

Neither a snapshot hash, a WMI JSON field, nor an external theorem name grants
PA authority. Admission continues to rest on the self-contained certificate
accepted by the unchanged independent kernel.
