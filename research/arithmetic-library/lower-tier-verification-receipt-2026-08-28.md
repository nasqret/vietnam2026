# Lower-tier continuation: exact local verification receipt

This is an implementation checkpoint, **not** a publication or Alpha/Stable
promotion. It continues the frozen `c9490761` baseline according to
[PLAN/16](../../PLAN/16_divisor_sums_and_prime_field_polynomials.md).
Work began on 2026-08-28 and final integration checks finished on 2026-08-29.

## Mathematical outcome

There are **126 genuinely new theorems** in eight ordinary-HA source modules:

| New chapter | New results | Direct declared dependencies | Tactic commands |
| --- | ---: | ---: | ---: |
| Actual divisor sums and Möbius tables | 37 | 92 | 1,380 |
| Signed weighted sums and linearity | 40 | 121 | 2,117 |
| Prime-field coefficient data and modular Horner evaluation | 49 | 131 | 2,829 |
| Total | 126 | 344 | 6,326 |

Every new statement was parsed and compared as an exact canonical formula DAG
against all 3,392 earlier statements and all other new statements. There were
no duplicates. Binder spelling and source length did not filter that audit;
hashes were only an index and exact canonical DAG bytes confirmed matches.

The mathematical contracts and independently checked authoring tests are in:

- [Möbius tables and divisor sums](mobius-tables-divisor-sums-rfc-v1.md).
- [Signed weighted sums](signed-weighted-sums-rfc-v1.md).
- [Prime-field polynomials](prime-field-polynomials-rfc-v1.md).

## Actual complete checks, not conditional-body receipts

`python3 scripts/check_constructive_lower_tier.py --write` completed
successfully. It freshly checked all three complete bundles in the original
HA kernel, submitted the same authenticated payload bytes to the independently
compiled Lean checker through private snapshots, and compiled and rechecked
ordinary empty-context certificates for all nine selected principal roots.

The deterministic [machine-readable audit](artifacts/lower-tier-checkpoints-v1.json)
has SHA-256
`c97cb8503e40a0eee2c667a1ab625b71542e2537818c9b73f9cc49fa2bca42ec`.
Stored success flags are never used as proof authority. The separate verifier
pins each source file and its complete ordered theorem specifications, so an
already imported but altered factory cannot pass by retaining a filename/hash.

The independently compiled checker was not rebuilt in this tranche. Its exact
binary size is 106,787,344 bytes and SHA-256 is
`22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033`.
No toolchain version is inferred from a current working-tree configuration.

| Complete bundle | Owned new | Prior non-admitted support | New cross-track support | Alpha support | Nodes incl. packaging | Edges incl. packaging |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Divisor sums | 37 | 24 | 0 | 253 | 315 | 875 |
| Weighted sums | 40 | 12 | 4 | 170 | 227 | 584 |
| Prime-field polynomials | 49 | 23 | 0 | 129 | 202 | 519 |

All support bodies are really present and checked. The four shared append/sum
prerequisites of weighted sums are owned by the divisor-sum chapter, and are
not counted again among its 40 results. The previous 170 research theorems
are not silently admitted to Alpha by being used as support.

Exact complete artifacts:

- [Divisor sums](artifacts/lower-tier-divisor-sums-proof-bundle-v1.json):
  1,841,261 bytes; 20,685 body-proof occurrences; SHA-256
  `96740bcedad194ebed5066ae03fa20cd922e702ae925b2c85f4ed45649aa0307`.
- [Weighted sums](artifacts/lower-tier-signed-weighted-sums-proof-bundle-v1.json):
  2,293,317 bytes; 13,692 body-proof occurrences; SHA-256
  `e88ddec495a71d673e670299ea3943a5a996eecb1296fb746e107c8e0b81c967`.
- [Prime-field polynomials](artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json):
  688,987 bytes; 11,889 body-proof occurrences; SHA-256
  `6e3a08c73b8a45de127e6d50a771f95b52fd54894b1c2e43468751421488a01a`.

The ordinary empty-context certificates were additionally checked against
their exact specification and formula by the original HA checker:

| Principal theorem | Ordinary certificate occurrences |
| --- | ---: |
| `mobius_table_exists` | 14,044 |
| `signed_divisor_sum_positive_source_extensional` | 9,955 |
| `signed_divisor_sum_exists_unique` | 13,081 |
| `signed_weighted_sum_exists_unique` | 13,146 |
| `signed_weighted_sum_scalar_linearity` | 8,505 |
| `signed_weighted_sum_add_linearity` | 8,241 |
| `prime_field_polynomial_horner_exists_unique` | 10,310 |
| `prime_field_polynomial_normalized_horner_iff` | 10,228 |
| `prime_field_polynomial_reduce_and_evaluate_exists` | 10,192 |

The authoring jobs retained the existing 170/175-second CPU, 180-second wall
and 1,536 MiB memory policy. The initial weighted closure, the largest observed
closure job, peaked at 905,510,912 bytes. The complete nine-root audit peaked
at 398,262,272 bytes. No kernel, formula, catalog, bundle, replay or service
limit was raised.

The final direct proof-audit `--check` repeated all three HA/Lean checks, all
nine ordinary root replays and the complete novelty audit, then matched the
saved audit byte-for-byte. It passed with a peak of 448,217,088 bytes.

## Definition structure and exact boundaries

The additive registry introduces **19 definitions, ND0262–ND0280**, preserving
all 318 earlier definition objects and graph records literally. The resulting
337-definition DAG has 697 actual expansion edges and maximum zero-based
layer 12. Every declared edge occurs in the exact expansion; definitions do
not contribute proof-dependency arrows or grant proof authority.

The generic beta-prefix bound/equality graphs are named once. Existing
`Horner`, `CanonicalModularResidue`, signed arithmetic, pairing, table and sum
identities are reused, not reintroduced as renamed mathematical concepts.
Key boundary tests preserve:

- Inclusive table domains versus strict prefix-sum lengths.
- Positive divisor witnesses, an explicitly zeroed mask index zero, and no
  restriction on the input value `F(0)`.
- Positive-only `Mobius` values versus a separate finite-table zero convention.
- Unique represented signed values, not unique arbitrary beta encodings or
  positive/negative component pairs.
- Highest-degree-first coefficients, leading zeros and the empty polynomial;
  the modular argument guard `x<p` remains present in the empty case.
- Modular Horner execution defined by actual multiplication/addition steps,
  with its natural-Horner residue invariant proved separately.

## Reproduction and unchanged authority

The additive [local explorer](../../book/_static/constructive-lower-tier-explorer/index.html)
contains 371 files and 338 HTML pages. Its manifest has SHA-256
`ac6c7b3f53a27ba3812969031d7a3eea25bc0c2abeb7944c45f240ca5bb59c32`
and checkpoint-inventory digest
`fc8f85092b7a4ae03f3614e940c4ca4ab5cdf4da63710ea692cb10ca8be5bca9`.
The 370 payload files excluding that manifest total 30,367,033 bytes.
The principal root tags remain `DV000A`/`DV0025`/`DV0022`,
`WS0021`/`WS0028`/`WS0027`, and `PP002A`/`PP002F`/`PP0031`.

All five CSS/JavaScript assets are byte-identical to the established model.
The three displayed definition DAGs contain 30, 18 and 21 definitions with
52, 34 and 36 genuine expansion edges, respectively. Those shared definitions
are not summed as distinct new concepts. The full registry count remains 337.

Distinct focused regressions passed:

| Verification group | Passed |
| --- | ---: |
| Table extension, Möbius tables and divisor masks | 185 |
| Signed table operations, linearity and weighted sums | 419 |
| Coefficients and modular Horner evaluation | 703 |
| New support, definition and checkpoint controls | 143 |
| Canonical local explorers and actual JavaScript | 44 |
| Browser-shell source/package contract | 20 |
| Unchanged kernel, syntax, cut, formula DAG, bundle, layered and hostile replay | 233 |
| Total distinct focused tests | 1,747 |

The explorer suite freshly ran the original HA and compiled-Lean checks,
matched the entire generated snapshot byte-for-byte, round-tripped every exact
statement/tactic/local proposition, and checked all local routes and three
graph-edge kinds. Actual canonical JavaScript ran in the established hostile
SVG DOM harness, including getter-only `href`, filtering, hash highlighting
and exact navigation. This is not visual browser or full remote-CI evidence.

The initial explorer build peaked at 479,920,128 bytes. Its 44-test suite
peaked at 532,676,608 bytes; the final direct explorer `--check` also passed
with 478,281,728 bytes. The 143 integration tests passed in 107.60 seconds
with 393,347,072 bytes. Eight separate unchanged-foundation regression
processes passed all 233 cases; their maximum peak was 458,014,720 bytes.
Repeated runs are not added to the distinct test total.

The local browser inventory and content manifest were regenerated and checked:
491 Python files, 513 manifest entries, application identity `a-2501572d3333`,
and the build label assigned during implementation, `2026-08-28c`.
`APP_ROOT` and `PEANOAPPID` agree. No old app staging tree was erased and no
application channel was staged or deployed by this checkpoint.

Recheck the exact evidence with:

```sh
python3 scripts/check_constructive_lower_tier.py --check
python3 scripts/build_constructive_lower_tier_explorer.py --check
```

The separate `scripts/export_constructive_lower_tier.py` command can rebuild
an authoring bundle at a new destination. It validates complete support cones
and freshly checks every explicit seed before reuse. It refuses existing
destinations and does not itself claim compiled-Lean acceptance or admission.

Alpha remains v30, with 3,222 checked-use entries and the unchanged
66,503,303-byte catalog
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
Stable remains 432. The catalog still lies below the unchanged 64 MiB ceiling;
this tranche does not attempt a new Alpha catalog or truncate its evidence.

Full G007 remains open: divisor involution/prime-toggle cancellation,
rectangular Fubini, convolution and Möbius inversion require further proofs.
Full G091 remains open: representation length is not degree, and polynomial
convolution, division, gcd, irreducibles and general extension fields are not
claimed by these coefficient and evaluation results.

No commit, push, deployment, cache-header change, production channel change,
Hydra worktree cleanup, gateway/mailbox change or Lean-worker restart is part
of this implementation checkpoint. Visual browser QA is unavailable because
the supported browser runtime reported no connected browser; automated
renderer/link/JavaScript checks are a distinct gate, not visual inspection.
