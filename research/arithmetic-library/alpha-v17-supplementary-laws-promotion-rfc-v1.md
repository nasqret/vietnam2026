# Alpha v17: constructive supplementary-law evidence promotion

## Immutable parent and release boundary

Alpha v17 is an evidence-only successor to the byte-sealed Alpha-v16 edition.
It does not enroll, delete, rename, reorder, or alter any theorem statement,
tactic script, dependency edge, provenance record, or release membership. The
432-entry Stable edition remains the unchanged default public theorem library.

The exact parent bindings are:

| Parent artifact | SHA-256 |
| --- | --- |
| Alpha v16 catalog | `58838161106b118b12f2a99c0de280ed223980dd92ec9b0f842358b9d5e43a09` |
| Alpha v16 metrics | `da0b82e0a9c7c29c0b338d2bf7f7fd27e7843963a1a962a09ca9009eae6f0a7d` |
| Alpha v16 dependency graph | `eb056011b0a46ad2cb17847aaaab99d4ab8246751e1639b78f3a3f59d92e0c28` |
| Alpha v16 channels | `833f08cbf42c41f7ed0feedf20bdaafcd52e7ddb171f62f68c44fc8d7741e403` |

The preserved 1,673-row ordered enrollment identity is
`44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175`.
The complete unchanged dependency graph retains 5,615 edges and 53 layers.

## Exact constructive roots and dependency slice

The two original first-order constructive theorem surfaces are:

1. `quadratic_supplement_minus_one_complete`, classifying the quadratic
   character of minus one for odd primes using the witnessed classes modulo
   four.
2. `quadratic_supplement_two_complete`, classifying the quadratic character of
   two for odd primes using the witnessed classes modulo eight.

Their joint exact dependency closure contains 437 theorem nodes: 226 Stable
theorems, 180 already Alpha-closed theorems, and exactly 31 Alpha-v16
`body_checked` rows. Three of the latter are historical Bertrand/Eisenstein
support rows; the other 28 are the exact supplementary-law campaign rows.
The ordered SHA-256 digest of those 31 newline-separated names is
`21e141da58e3262e250285ef9d43d78a5911d065e3746a824faea82642f7c8c7`.

Only these 31 names may transition from `body_checked` to `alpha_closed`.
No Lucas, Kummer, Bertrand endpoint, Lagrange four-square, all-natural
two-square, or Pythagorean/Fermat result obtains checked-use authority through
this promotion.

## Genuine proof evidence and fail-closed replay

The self-contained artifact
`research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json`
contains the 437 complete ordinary dependency-curried theorem proof bodies and
one synthetic constructive conjunction root. The synthetic root is exactly the
conjunction of the unchanged two endpoint formulas; it has no enrollment,
release membership, axiom authority, or user-visible theorem identity.

All 406 prerequisite bodies originate in the already independently checked
quadratic-reciprocity proof bundle. The remaining 31 bodies are reconstructed
from their unchanged sealed scripts and are checked independently by the
original intuitionistic kernel. Every dependency edge, exact target formula,
and complete proof body is retained in canonical proof-bundle bytes; a file
digest, provenance receipt, or displayed theorem name never substitutes for an
actual proof.

Checked use of a newly promoted theorem extracts its dependency-closed bundle
slice, constructs an ordinary layered proof using the unchanged conservative
`Cut` rule, and checks the exact original formula from the empty context. The
existing Hydra limits remain unchanged: no closure microbatch exceeds 16
theorem rows, 125,000 structural proof nodes, or 25,000 distinct proof objects.
The default Stable registry never changes.

## Expected release partition

| Evidence | Alpha v16 | Alpha v17 |
| --- | ---: | ---: |
| `stable_closed` | 432 | 432 |
| `alpha_closed` | 453 | 484 |
| `body_checked` | 788 | 757 |
| Total checked-use | 885 | 916 |
| Enrolled theorem statements | 1,673 | 1,673 |

The resulting immutable Alpha-v17 evidence identity must be
`db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4`.
Its checked-use subgraph has exactly 2,743 dependency edges and must itself be
dependency closed.

## Independent gates

```text
make peano-library-alpha-v17
make peano-library-alpha-v17-check
```

Generation and verification must reject mutated Stable pointers, changed
Alpha-v16 parent artifacts, changed enrollment topology, fabricated checked-use
rows, missing actual proof data, modified proof bodies, altered target
formulas, incorrect dependency edges, and either missing supplementary root.
Historical Alpha v1–v16 and Stable artifacts remain byte-exact.
