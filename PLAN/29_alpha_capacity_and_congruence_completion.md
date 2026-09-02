# Alpha capacity and elementary congruence completion

Authorized request, 2026-09-02: commit, promote and deploy; finish the first
level of the main campaign and check standard congruence arithmetic.

## Starting checkpoint

The verified recursive polynomial gcd/Bézout checkpoint is committed as
`be320ec67696aa16deb7f7221fd025046b685b0d`. The exact 119-row working bundle
and all earlier checkpoints remain unchanged. At the start of this plan,
Alpha was v33 with 4,092 entries; Stable was the same default 432. No v34
promotion or deployment had occurred.

The [readiness audit](../research/arithmetic-library/alpha-v34-readiness-audit-v1.md)
distinguishes literal DAG layers, the thematic elementary layer, execution
waves and families. The current v33 atlas has no open goal in layers 0–5.
That does not close F01, all of F02, or G091.

## Approved capacity design

`scripts/peano_catalog_shards.py` fixes logical catalogue capacity at 4,096.
The v33 codec inherits it. Promoting the complete 119 requires at least
4,211 entries. The user explicitly authorized the reviewed upgrade with
"Yes, proceed" on 2026-09-02. Implement a new v34 logical capacity of 8,192
entries while leaving the historical codecs at 4,096. The three-file,
64-MiB-per-file transport and all kernel/proof-resource limits remain fixed.
Independently test the new count and enrollment-index boundaries; preserve
the exact inherited v33 rows and evidence. Do not split files to bypass
logical counts, skip admissions or publish a partial tranche as complete.

## Execution after the capacity decision

1. Specify and independently test a new bounded catalogue transport/runtime
   capacity design, preserving historical bytes, all first admissions,
   default Stable, original kernel and all per-proof resource limits.
2. Complete the bounded elementary congruence tranche: gcd-reduced
   cancellation; full noncoprime linear solution class; canonical solution
   below the reduced modulus; actual exact bounded enumeration/count;
   verification and admission of the existing all-input Fermat candidate.
   Preserve modulus-zero/one cases and prove every advertised witness.
3. Integrate all 119 verified working polynomial rows and the newly verified
   congruence rows through new canonical ownership/enrollment/provider
   modules. Preserve the exact working archives and their evidence.
4. Run fresh novelty, dependency-complete original HA, same-byte compiled
   Lean, ordinary-principal, catalogue-verifier and same-live reader gates.
   Preserve the Quadratic Reciprocity design and conservative definition DAG
   using the constructive-proof-explorer skill.
5. Commit/push normally to the current proof branch and deploy only accepted
   bytes through established faculty paths. Check exact remote targets,
   retain rollback entrypoints, upload additively and switch the hub last.
   Recheck live bytes. Do not waive the Peano production cache-header gate.

## Implementation and local promotion checkpoint

Steps 1–3 are implemented. The versioned v34 capacity is 8,192; historical
codecs, mathematical artifacts, Stable and all proof-resource limits are
unchanged. The canonical runtime contains the exact 119 polynomial rows and
12 congruence rows, giving 4,223 entries and 13,816 proof dependencies.
The proof library and Peano preview have now been activated with this release;
production Peano remains unchanged under its separate cache-header gate.

The two new readers use the Quadratic Reciprocity model, with exact AST
roundtrips, 407 conservative definitions, 884 expansion edges and 68 family
entrances in the combined presentation. Source-only catalogue and private
rendering preflights passed without creating admission authority or public
release files. Subsequently, the genuine fresh 22-job proof run and all six
same-live publication phases passed (171 mandatory cases). All six readers
and atlas trees are installed locally. The existing six catalogue files
were independently reverified byte-for-byte, not overwritten.

The initial publication attempt passed all 22 proof jobs but correctly stopped
at a stale UI expectation of 4,092 entries. That test alone was corrected to
4,223; the successful second attempt reran all 22 proof jobs before all six
publication phases. Both attempts and the correction remain in the audit
history. All 12 remaining installed-service cases subsequently passed,
completing 1,865 runtime cases plus 198 provider/helper cases (2,063 distinct
cases, 6,189 passed phases). Their [separate observations](../research/arithmetic-library/working/alpha-v34-release-v1/installed-service-observations-v1.json)
preserve the pre-install history unchanged. Complete delivery staging then
passed in 164.79 seconds with the original single 180-second deadline,
CPU 170/175 limits and 1,536 MiB RSS ceiling. It installed 13,549 files and
checked 793,606 local links and 466,223 fragments. The already-installed
CPython 3.11.12 is selected only for this delivery step; the proof/backend
interpreter is unchanged. The two earlier timed-out attempts remain recorded
without success credit. See the [actual successful staging run](../research/arithmetic-library/working/alpha-v34-release-v1/delivery-stage-attempt-3-observations-v1.json).

See the [v34 release procedure](../docs/ALPHA_V34_RELEASE.md) and the
[non-authorizing preflight observations](../research/arithmetic-library/working/alpha-v34-release-v1/publication-preflight-observations-v1.json).
See also the [successful live publication](../research/arithmetic-library/working/alpha-v34-release-v1/live-release-attempt-2-observations-v1.json).
Source release `97a1ed75c3a307eebe872774a82a8822c2c2ffeb` is committed and
pushed. Both authorized faculty destinations were uploaded additively, with
rollback entrypoints retained and activation last. Every active staged file
matches its remote SHA-256: 13,549 proof files and 630 preview files. All 230
proof-site and eight preview HTTPS checks passed. The restored public Lean
service independently compiled the new modulus-one congruence theorem as a
nine-node standalone proof with zero certificate fallbacks. The release
uses the unchanged original limits, including the public worker's 1,024 MiB
ceiling. See the [deployment observations](../research/arithmetic-library/working/alpha-v34-release-v1/deployment-observations-v1.json).

Browser automation was unavailable; no visual check is claimed. Executable
graph/selector tests and exact live HTTPS/remote-byte checks cover the
published surfaces. The unversioned Peano entrypoint still lacks the required
non-storable cache policy, so production promotion remains deferred and its
index and hosting configuration remain unchanged.

Do not claim the additional open F02 contracts G015–G020 or arbitrary
prime-power finite fields G091 complete. The approved capacity, exact
congruence/polynomial tranches, Alpha promotion and proof-site/preview delivery
are complete; those broader mathematical goals and protected production
promotion remain separate future work.
