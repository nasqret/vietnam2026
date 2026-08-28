# Bottom-layer research checkpoint deployment receipt

Date: 2026-08-28. Observed outcome: committed, pushed, deployed to the existing
faculty proof website, and independently compared against the served bytes.
This is a publication receipt, not a new proof rule or an Alpha admission.

## Published scope

The [public checkpoint library](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/)
contains four canonical Quadratic-Reciprocity-style proof explorers:

| Family | New checked theorems | Principal tag | Exact scope |
| --- | ---: | --- | --- |
| [Euler units](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/euler-units/) | 32 | EU0022 | Full guarded G014 endpoint; actual units and independently counted totients |
| [Prime fields](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/prime-fields/) | 87 | FP0057 | Actual prime-order fields, tables, cardinality and characteristic; not general G091 |
| [Möbius values](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/mobius-values/) | 21 | MV0015 | Unique signed values and fresh-prime negation; not full G007 |
| [Signed sums](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/signed-sums/) | 30 | SS001E | Actual signed tables, reindexing and permutation-invariant sums |

All 170 statements are pairwise distinct and differ from every one of the
3,222 parent statements. The 34 new conservative definitions extend the
reviewed registry to 318 identities and 645 genuine expansion edges. The
published Alpha atlas retains its original 284 reviewed definitions and
admission data; the additional checkpoint DAGs are explicitly separate.
Proof dependencies, notation uses and definition-expansion arrows retain
their three distinct meanings.

The unchanged mathematical evidence is recorded in
[`bottom-layer-checkpoints-v2.md`](bottom-layer-checkpoints-v2.md) and its
[literal audit](artifacts/bottom-layer-checkpoints-v2.json). Four complete
bundles passed the original HA checker and the independently compiled Lean
checker. Seven principal roots also passed ordinary empty-context HA checks.
The exact compiled checker identity is the SHA-256
`22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033`;
this receipt does not infer its compiler version from the current toolchain file.

## Recorded source and delivery identities

Repository: `nasqret/vietnam2026`. Branch:
`proof/lower-foundations-v31-20260828`, based on the published
`18ce79d3137616687183d17fcaed0a2c1383fecf`.

- `72f6a4ae`: mathematical implementation, proof evidence, tests and all 493
  local explorer files, including the four previously ignored certificate copies.
- `010bb985`: separate public adapter, 495-file presentation, durable staging,
  truthful navigation, service exclusion and local app inventory integration.
- `f1971ae7c2d240d7581f9bf5216c1e396520ef85`: final deployed source; removes only
  24 spaces on twelve blank metadata lines across four family entrances and
  adds two protected-text regressions. No proof, tactic-script or browser-JavaScript
  bytes change.

This receipt is committed separately after deployment. No branch was
force-pushed, no main-history rewrite or merge was performed, and unrelated
Hydra worktree changes were preserved.

```text
mathematical v2 audit SHA-256:
d1ec9d90f9d102041cce1e67d54268fa7ca3da7be07afba4c8ecc6a4cf214d2a

unchanged local 493-file snapshot manifest SHA-256:
d9bd86fe6860edb19c2adab5455d9ead395b0c3f0828baeb3f1037d4bf4955bb

public 495-file snapshot manifest SHA-256:
f800d3436d7b053a6ba233e2c1014d7a1b8e7eb613ba3d9c36902ca5ede623ab

public checkpoint files:          495
public checkpoint HTML pages:     452
public checkpoint bytes:    17,256,376
```

The public adapter preserves literal bundles, sources, prior receipts,
statements, tactic scripts, definitions, stable tags and all false admission
flags. Its build and check paths freshly invoke both proof verifiers; matching
stored metadata is never substituted for proof checking. Historical local-stage
receipts remain literal, including their original non-public delivery labels.

## Verification before publication

The final focused test groups passed 1,181 tests without double-counting reruns:

| Group | Passed |
| --- | ---: |
| Definitions, notation, checkpoint and hostile ordinary replay | 671 |
| Frozen local explorers | 278 |
| Public checkpoint delivery and protected text | 60 |
| Staged navigation, Lean selector and gateway contracts | 69 |
| General deployment and browser source-inventory contracts | 103 |

Three initial browser-inventory failures identified the twelve newly added
Python modules missing from the generated source list. The original inventory
and manifest generators repaired this; the final 103-test group passed.
The 60-test publication suite includes the two final whitespace regressions.
This is not a claim of a repository-wide green CI run.

Fresh verification of all four bundles and seven ordinary roots passed at
369,541,120 peak resident bytes. The final public make gate passed at
443,219,968 bytes. The existing 170/175-second CPU, 180-second wall and
1,536 MiB checkpoint-authoring limits remained unchanged, as did every
kernel, formula, proof, bundle and service guard.

`make -j1 stage-proofs` completed all four immutable flagship checks, the
current historical-family builds, the 904-theorem historical publication,
Gaussian explorer, actual checkpoint verification, atlas checks and selector
staging. After the final head-only formatting cleanup, the ordinary public
make gate was rerun and only its owned checkpoint subtree was recopied using
the exact Makefile staging command. Both staging overlays passed read-only
checks. All 6,238 eligible historical graph/detail pages retain their Lean
controls; non-admitted checkpoint pages receive none.

Four independent audits of the final staged site passed:

- 10,067 files, 506,322,672 bytes and 9,861 HTML pages; no symlinks.
- 615,944 local references, including 54,126 cross-section links, resolve.
  All static fragments, 29 legacy book fragments and 15 redirect-script cases pass.
- All 48 typed graphs pass. There are 98 historical graph-runtime cases and
  45 checkpoint graph/dashboard/reader/dispatch cases, including getter-only SVG
  property tests. Only proof-dependency edges determine proof paths.
- All 4,912 inline JavaScript occurrences, 1,175 distinct inline scripts,
  11 JavaScript asset paths and eight inert JSON blocks validate.
- The exact-reader audit covers 3,315 pages and 263 whole-script runtime cases,
  including all 174 new exact-reader/index navigation cases.
- All 452 new pages preserve protected mathematical text. Their 25,698 local
  references include 13,268 fragments and 1,063 outward references. All 92
  available inherited proof-page routes match exact statements; 15 prerequisites
  without standalone historical pages link to explicit complete-bundle records.

No browser connection was available. These are executable structural and
JavaScript-runtime checks, not a visual-browser or screenshot test.

## Actual proof-only upload and live verification

Read-only preflight checked the exact faculty directory for symlinks and
compared content checksums. It found zero deletions: 495 new checkpoint files
and content changes only to the existing hub and atlas HTML entrances.
The deployment command completed successfully:

```sh
rsync -azc --delete --exclude '.DS_Store' _deploy/proofs/ \
  lts-faculty.wmi.amu.edu.pl:~/public_html/proofs/
```

A second recursive, read-only checksum comparison found zero content
differences or extra remote files, excluding Finder metadata. Remote SHA-256
checks separately confirmed the exact final checkpoint manifest and the
unchanged Alpha campaign and definition JSON files.

Independent TLS-verified HTTPS requests compared **617 of 617 public objects,
39,066,732 bytes**, exactly against staging in 23.558 seconds. This includes
all 495 new files and 122 historical site objects. Four requests at most ran
in parallel; response sizes and request times were bounded. All five legacy
documentation routes returned their expected actual HTTP 302 destinations,
preserved query strings, and reached the live book chapters. There were zero
errors. No on-demand proof-service job was submitted by this publication.

## Unchanged authority and production boundary

Alpha remains v30 with 3,222 checked-use theorems, catalog SHA-256
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
Default Stable remains the same 432 entries. The 64 MiB catalog/service ceiling
was not increased. Full G007 inversion and general G091 prime-power fields
remain open, despite the complete checked prerequisite proofs published here.

The local browser app was reproducibly staged as `a-86993f944ca2`: 483 Python
source files and 505 manifest entries, all hashes checked. This only synchronizes
local packaging with the new source modules. Neither `/peano-lab/` nor
`/peano-lab-next/` was deployed. Production cache headers, the public Lean
gateway, mailbox broker and running worker were not modified or restarted.
