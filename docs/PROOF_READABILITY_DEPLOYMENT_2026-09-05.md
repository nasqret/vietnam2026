# Proof readability release — 2026-09-05

The library-wide reading layer is published at
<https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/>. Its coverage and remaining
exposition priorities are at <https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/reading/>.
The updated authoring runtime is at
<https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next/>.

Peano production is **not promoted**: its required hosting cache policy still
fails. Browser-visual QA is also unavailable because no browser is connected.
Neither limitation is described as a successful validation.

## Source and mathematical scope

Source commit `f5b338d83e160eaeca03ad8ff85318e24307972b` was pushed to
`nasqret/vietnam2026`, branch `fix/proof-explorer-layout-20260904`. The
candidate worktree was clean and its HEAD unchanged throughout staging,
upload, and the preview gate. This subsequent record changes documentation
only; it is not another application build or an authorization to promote.
Merging the milestone branch to `main` remains the repository owner's decision.
The existing workflow runs automatically only on `main`, `peano-lab`, or pull
requests, so no automatic GitHub Actions run is claimed for this branch push.

The independent `nasqret/peano-lab-lean` worktree is clean and already matches
its remote branch at `d2903c8bd507b7e4458b1249f840a4e274befdbf`; no source
commit or push was necessary there. Its generated import cache was rebuilt
with the pinned Lean 4.31.0 compiler, retaining the old cache locally. Its
original bundle-checker executable remains byte-identical.

Alpha v34 still has 4,223 checked-use entries and Stable still has 432.
No theorem, definition, proof bundle, mathematical admission, or historical
first-admission record changed. This release includes the previously deployed
layout repair and hidden-public-Lean policy in source control, plus the new
reading layer and explicit inferred-claim authoring support.

## Final targeted regression coverage

| Group | Passing cases |
|---|---:|
| Reading layer, conservative notation, native inferred claims, reconstruction | 201 |
| Deployment contracts and public gateway | 123 |
| Layout, public policy, selectors, and export UI | 308 |
| Kernel, engine, tactics, proof strands, browser shell, worker | 438 |
| Local reasoning, reduction, traces, arithmetic surfaces | 86 |
| New pinned-Lean syntax and conditional-body compilations | 15 |
| Total distinct cases across these groups | 1,171 |

The 438-case group includes all six previously unavailable independent
full-strand compiler checks. Its first combined run had 437 passes and one
35-second subprocess timeout in
`test_stable_and_alpha_strands_have_separate_content_bound_modules`.
That exact test passed unchanged when rerun in isolation; no timeout, memory
bound, assertion, or admission check was weakened.

The 15 new compiler cases cover seven inferred applications, five legacy
local-claim/scope patterns, and three large library bodies with their exact
original dependencies supplied as explicit theorem parameters. All have empty
axiom dependency lists. The three conditional-body checks do not claim a fresh
compilation of those theorems' entire transitive dependency closures.
Their harness uses the same import-free setup as the production standalone
exporter; an initial harness importing all of Lean exhausted the existing
memory limit and was corrected. The final complete compiler suite passed in
7.55 seconds, retaining the 1,024 MiB and 90-second per-process bounds.

Worker inventory (563 Python sources), vendor and application manifests,
shell syntax, and `git diff --check` also passed. The full proof-stage check
reproduced its exact manifest in 71.47 seconds at 368,033,792 bytes peak RSS,
within the unchanged original limits.

## Proof website delivery

- All 13,551 previous live files matched the preserved public parent before
  upload.
- The checksum preview identified exactly 8,786 changed theorem pages and
  five additions: reader CSS/JavaScript, the audit HTML/JSON, and the
  presentation manifest. No unexpected files or deletions were present.
- The additive upload retained all prior files. The presentation manifest and
  root entrypoint were processed last; the root's content is unchanged.
- All 13,556 final remote files match their exact staged SHA-256 hashes.
- All 247 public HTTPS checks pass: 238 revision-bound requests across all
  68 families and the new surfaces, plus nine original unversioned links.
- The published reader covers 8,786 theorem pages. Defined local claims over
  600 characters decrease from 279 to 85, with original ledgers preserved.

Final presentation manifest SHA-256:
`10471f7ace1719110af485479052a87dca4cda5a410515d556ebce5473adefc9`.
The preserved `_deploy/proofs-public-v1` tree remains an exact rollback.

## Peano preview and production boundary

Preview now serves app `a-4de50afd4366`, build `2026-09-05a`.
The 631-file stage was assembled from the clean source candidate. The
application namespace did not previously exist. All 630 non-entrypoint files
were checked remotely before activating the new index; all 631 files were
checked again afterward. All 14 critical HTTPS checks pass, including the
unversioned entrypoint, new authoring modules, proof bundles, and WASM.

Application manifest SHA-256:
`4de50afd43668a17443edb0e1f630080c9eb5a8eef561aabc5f863998e34936f`.
Preview entrypoint SHA-256:
`a4b3f770cfab53434a875a86de0b5a840388db21c271e636d80ebb6c93a74318`.

The unchanged `verify_peano_delivery.sh` fails with exit 1 after confirming
the preview entrypoint bytes, reporting **Missing non-storable HTML policy**.
The observed HTTP 200 response at `2026-09-05 10:29:17 GMT` has no
`Cache-Control: no-store`. Successful payload checks do not waive that gate.
WMI hosting must supply the required headers before production promotion can
be attempted; the complete unchanged verifier must then pass.

Production's index remains
`c90b831890d9c08282406b6e73b00a478a4fbb688117b6d1681b869f453d2b1c`,
identical before and after this release. Both Peano `.htaccess` files retain
SHA-256 `79c0b096871720420a26097d4e20c71c7169f85f264b195d89ca713187ce7059`.
No hosting-header configuration was changed. Old immutable application and
vendor namespaces are retained. The previous preview index is also retained
locally as `_deploy/peano-preview-rollback-20260905.html`, SHA-256
`a05d5520e6acdefa391dc5be5f0556355a687668f467e9579360b6acafb1e752`.

Public on-demand Lean controls remain hidden. No gateway deployment,
worker/tunnel start, or production activation was performed. Unrelated research
worktrees were not staged, committed, cleaned, or deployed.

The [structured delivery observations](../research/arithmetic-library/working/proof-readability-release-v1/deployment-observations-v1.json)
bind these results and the complete local observation logs. They are delivery
observations, not mathematical proof authority.
