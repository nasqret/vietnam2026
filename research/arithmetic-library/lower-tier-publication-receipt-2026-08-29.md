# Lower-tier proof checkpoint deployment receipt

Date: 2026-08-29. Observed result: committed, pushed and deployed to the
existing faculty proof website, with exact remote checksum and HTTPS byte
comparisons. This is publication, not Alpha/Stable promotion.

## Published mathematical scope

The [new checkpoint library](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/lower-tier/)
contains three canonical Quadratic Reciprocity-style chapters:

| Chapter | New proved statements | Principal tag |
| --- | ---: | --- |
| [Divisor sums and Möbius tables](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/lower-tier/divisor-sums/) | 37 | DV0022 |
| [Signed weighted sums](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/lower-tier/signed-weighted-sums/) | 40 | WS0027 |
| [Prime-field coefficient tables and Horner](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/lower-tier/prime-field-polynomials/) | 49 | PP0031 |

All 126 statements differ, as parsed ASTs, from all 3,392 earlier statements
and from each other. Their unchanged complete proof bundles and nine selected
ordinary certificates are documented in the
[mathematical verification receipt](lower-tier-verification-receipt-2026-08-28.md).
The publication builder freshly reran original-HA and actual independently
compiled Lean checks on all three complete bundles. It did not infer proof
validity from the saved receipt or promote the earlier local delivery labels.

Nineteen conservative definitions, ND0262–ND0280, extend the checkpoint
registry to 337 identities and 697 actual expansion arrows. The old Alpha
atlas keeps its original definition/admission data. The exact and readable
proofs, native tactic lines, definition expansions, source modules, literal
bundles and historical receipts remain unchanged in the public adapter.
Only delivery metadata, public prose and navigation change.

There are 84 distinct directly used external prerequisites: 47 Alpha,
34 earlier non-admitted research proofs and three cross-chapter prerequisites.
All 72 available standalone routes are linked by exact expanded statement;
the remaining twelve link to explicit complete-bundle records. This direct
navigation count is distinct from the complete transitive support inventories
inside each bundle. Inherited proofs are not counted among the 126 new results.

Full Möbius inversion G007 and general prime-power fields G091 remain open.
This published batch does not claim rectangular Fubini, divisor cancellation,
polynomial convolution, degree, division, gcd or irreducible construction.
Further work on those components is isolated in the subsequent continuation.

## Source identities and unchanged historical copies

Repository: `nasqret/vietnam2026`; branch
`proof/lower-foundations-v31-20260828`.

- `4fc164a846858045b07e7204575a5687ba64ffce`: the mathematical implementation,
  evidence, tests and 371-file local explorer; committed and pushed first.
- `122feea4f830627cae799ca12c92a3571c1ca9e0`: the public presentation,
  dedicated staging, navigation and delivery checks; the deployed site source.
- This receipt and the system-trust HTTPS checker option are committed after
  successful delivery. They do not change any served website bytes.

```text
126-theorem mathematical audit SHA-256:
c97cb8503e40a0eee2c667a1ab625b71542e2537818c9b73f9cc49fa2bca42ec

unchanged 371-file local snapshot manifest SHA-256:
ac6c7b3f53a27ba3812969031d7a3eea25bc0c2abeb7944c45f240ca5bb59c32

373-file public snapshot manifest SHA-256:
a44222194449c465f9e89915ab07e1a93ad74f61e319d502745a1d4b7dbee152

unchanged earlier 495-file public snapshot manifest SHA-256:
f800d3436d7b053a6ba233e2c1014d7a1b8e7eb613ba3d9c36902ca5ede623ab
```

The earlier public snapshot stays byte-for-byte intact, including both of its
dispatch pages. The new public namespace is additive at
`/proofs/checkpoints/lower-tier/`. The shared library entrance links all three
new chapters; the staged Alpha atlas links both checkpoint generations with
an explicit 170 + 126 count and no altered admission status.

## Verification and local staging

There were **280 distinct passing focused tests** in this publication turn:

| Group | Passed |
| --- | ---: |
| Fresh public proof checks, exact text, routes and actual canonical JavaScript | 57 |
| New/old checkpoint staging and Alpha-only service selector contracts | 91 |
| General deployment, gateway and browser-shell contracts | 116 |
| Delivery read bounds and certificate-verifying transport contracts | 16 |

An initial new layout test compared the number of release notes, although the
research chapters deliberately have two additional evidence/scope notes.
The final test compares identical hero/navigation/actions/three-card structure
and explicitly requires all four research release notes. All literal proof
and definition text tests passed throughout. This is a focused test result,
not a repository-wide or remote-CI green claim.

`make -j1 stage-proofs` passed the original flagship checks, historical-family
generators, current 904-proof historical publication, Gaussian family and
atlas checks, and fresh checks for both research generations. The final
126-proof public gate used 697,204,736 peak resident bytes, below the unchanged
1,536 MiB authoring ceiling. CPU/wall, kernel, formula, proof, replay, bundle,
catalog and service limits were not increased.

Read-only delivery checks then confirmed:

- 10,440 staged files, 537,177,611 bytes, with no symlinks.
- All 373 new files and all 495 earlier checkpoint files match their literal
  source manifests exactly.
- Every one of 22,631 local HTML references across the 338 new pages resolves,
  including its static fragment where present.
- Alpha campaign and definition JSON are unchanged. The final staged atlas
  HTML exactly matches its explicit navigation-only overlay.
- All 6,238 historical graph/detail pages retain their existing Lean controls;
  neither research generation acquires access to the Alpha-only service.
- Actual canonical JavaScript passes getter-only SVG `href`, graph selection,
  dashboard filtering, hash navigation and 129 exact-reader navigation cases.

No browser was connected after the prescribed discovery checks. These are
structural, actual-JavaScript and byte-comparison checks, not visual-browser QA.

The local immutable Peano app was regenerated as `a-2501572d3333`, covering
491 Python files and 513 manifest entries. Source and staged manifests both
have SHA-256
`2501572d3333ba237e582f4786082f33516f93b62a02af785b1737ee9eb17e14`.
Only the dedicated generated app staging directory was replaced; its contents
are reproducible from the committed source. No user data was removed.

## Actual remote upload and independent public-byte audit

Read-only faculty SSH preflight resolved the exact destination to
`/home/faculty/bnaskrecki/public_html/proofs`, an ordinary directory with no
symlinks below it. The checksum preview showed 373 new files, changes only
to `index.html` and `grand-campaign/index.html`, and **zero deletions**.

The proof-only deployment succeeded:

```sh
rsync -azc --delete --exclude '.DS_Store' --stats _deploy/proofs/ \
  lts-faculty.wmi.amu.edu.pl:/home/faculty/bnaskrecki/public_html/proofs/
```

Exactly 375 files were transferred. A second recursive, read-only checksum
comparison reported no content or metadata differences and no extra remote
files, apart from explicitly excluded Finder metadata.

The independent public audit compared **908 of 908 HTTPS objects**, totaling
**50,737,154 bytes**, exactly against staging, with four read-only requests at
most in parallel. All 373 new files, all 495 earlier files, five shared hub/
atlas objects and 35 additional historical prerequisite pages were covered.
There were zero differences and no proof-service jobs.

The initial Python HTTPS attempt correctly refused an untrusted certificate
chain: that Python installation has no configured default CA bundle. The
system client uses its configured macOS trust store and successfully verifies
the same HTTPS connection. The completed audit uses `--transport curl` with
certificate verification enabled, HTTPS-only requests, exact status/URL/byte
checks and size/time limits. No insecure flag, certificate-store modification
or authentication bypass was used.

## Authority and production boundary

Alpha stays v30 with 3,222 checked-use entries, catalog SHA-256
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
Stable stays 432. The 64 MiB catalog/service ceiling is unchanged.
Neither `/peano-lab/` nor `/peano-lab-next/` was deployed. Production cache
headers, the public Lean gateway, mailbox broker and running worker were not
changed or restarted. No force push or history rewrite was performed, and
unrelated Hydra worktrees were not modified.
