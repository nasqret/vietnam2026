# Alpha v16: dependency-closed quadratic-reciprocity promotion

## Scope and immutable parent

Alpha v16 is an evidence-only successor to the sealed Alpha-v15 channel. It
retains all 1,673 theorem specifications in precisely the same order, with the
same statements, scripts, dependencies, source bindings, enrollment origins,
provenance, and release memberships. It admits no new theorem. The 432-theorem
Stable channel, its release order, and its artifacts remain byte-for-byte
unchanged; Stable remains the default channel.

The immutable Alpha-v15 parent artifacts are:

| Artifact | SHA-256 |
| --- | --- |
| `artifacts/peano-library/alpha/catalog-v15.json` | `0123e5938f43cf67833751e2a6102d6598ac24c9be6db9a0d353ec3f55e5f32c` |
| `artifacts/peano-library/alpha/metrics-v15.json` | `583378f0d05c38707dc755b594871b356e4665ec09b9f5cc69ea72501656e77b` |
| `artifacts/peano-library/alpha/dependency-graph-v15.mmd` | `b6e7028f5b24bde498fec5ac44c228a063062096080b1dd3bf2a52aca61aeb92` |
| `artifacts/peano-library/channels-v15.json` | `77fed3c5f32c28cdd91f7095086af1a551e28758d599e8b4ee73ee66aa8905ba` |

The ordered enrollment identity is unchanged:
`44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175`.
The new evidence-sensitive edition identity is
`3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10`.

## Exactly authorized evidence transitions

The independently closed quadratic-reciprocity graph comprises 557 theorem
nodes and 1,787 declared dependency edges. In Alpha v15, 241 of those nodes
were already `stable_closed`, one was already `alpha_closed`, 314 were
`body_checked`, and the exact root `quadratic_reciprocity_combined` was
`pending_layered_closure`.

Only the 315 previously unchecked graph entries transition to `alpha_closed`.
Their newline-joined exact topological names have SHA-256
`aba2d7a192b6f1c11fbafbed1001bf592ca9ed8f5bee7ac3f1de863dd870a80e`.
Every previously checked graph entry preserves its exact parent evidence. Every
other Alpha row preserves its entire parent row byte-for-byte in canonical
JSON representation; no Bertrand, Lucas, Kummer, four-square, two-square, or
supplementary-law body is promoted by analogy.

The resulting evidence partition is:

| Evidence | Alpha v15 | Alpha v16 |
| --- | ---: | ---: |
| `stable_closed` | 432 | 432 |
| `alpha_closed` | 138 | 453 |
| `body_checked` | 1,102 | 788 |
| `pending_layered_closure` | 1 | 0 |
| Checked-use total | 570 | 885 |

The 885 checked-use nodes are dependency-closed and have exactly 2,641 direct
dependency edges. The full 1,673-node graph retains exactly 5,615 declared
edges and 53 layers. Full Alpha promotion remains blocked by its 788 genuinely
unchecked bodies.

## Actual constructive proof authority

The complete self-contained proof artifact is
`research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json`.
Its format is `peano-lab-bundle-v1`, its size is 2,790,229 bytes, and its
SHA-256 is
`3cd040d145f1004d07d277c66a3ffbcb355cd9c4b21938d79a6ec51b4258709c`.
It contains 557 complete ordinary dependency-curried intuitionistic proof
bodies, 1,787 exact edges, and 41,722 structural body proof nodes. Its local
root 556 is the exact original uncurried statement of
`quadratic_reciprocity_combined`, whose statement SHA-256 is
`2a95f83a5a21a5e21e482d5de8a19d55ee1843f676f086438f8a9853b6a97070`.

The independently reproducible complete ordinary unchanged-kernel,
empty-context certificate was also checked: 54,870 structural proof nodes,
35,052 proof objects, depth 129, and 252,961 annotation occurrences. Its
measured peak resident memory was 843,087,872 bytes. Full provenance and
independent compiled Lean-kernel verification are documented in
`research/arithmetic-library/quadratic-reciprocity-closure-receipt.md`.

Release generation and verification must decode the entire actual canonical
artifact, compare every formula and every dependency edge against the frozen
source stack, and invoke the unchanged intuitionistic kernel once for each of
its 557 complete proof bodies. A digest, receipt, browser flag, opaque handle,
or external theorem claim never substitutes for that proof check.

The public versioned runtime is
`peano-lab/py/peano_lab/library/editions_v16.py`. On checked use of any newly
promoted theorem, it rechecks the entire proof bundle, extracts that theorem's
exact dependency-closed subgraph, compiles an ordinary existing-kernel
certificate, and checks that ordinary certificate from the empty context. A
missing artifact, mutation, forward or missing dependency, altered target,
nonconstructive rule, exhausted resource budget, or rejected proof fails
closed. Existing checked-use rows continue through the previous runtime.

The Pyodide browser mounts the exact proof artifact at
`/lab/proof-artifacts/quadratic-reciprocity-proof-bundle-v1.json`; native use
resolves the immutable repository artifact. `set_qr_bundle_source` can select
an explicit source and always invalidates verified-proof caches.

## Reproducible gates

The immutable release publishes only new `catalog-v16.json`,
`metrics-v16.json`, `dependency-graph-v16.mmd`, and `channels-v16.json`
artifacts. Its dedicated generator, independent verifier, verifier mutation
tests, and public-runtime admission tests are all required:

```sh
make peano-library-alpha-v16
make peano-library-alpha-v16-check
```

The channel publication changes the Alpha pointer only. The Stable pointer and
all previous channel artifacts remain untouched.
