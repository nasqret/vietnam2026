# Independently checked quadratic supplementary-laws closure receipt

Date: **2026-08-25**.

Both complete constructive quadratic supplementary-law statements now have
genuine self-contained proof data:

```text
quadratic_supplement_minus_one_complete
quadratic_supplement_two_complete
```

The statements are the exact previously enrolled Alpha-v16 formulas; neither
has been weakened, made conditional, replaced with host computation, or
granted authority on the strength of a theorem name or provenance hash.

Their common dependency closure contains 437 distinct previously enrolled
theorems. Exactly 406 already have independently checked proof bodies in the
complete quadratic-reciprocity proof artifact. The remaining 31 were
`body_checked` in the immutable Alpha-v16 parent: three genuine older
Eisenstein-prefix theorems and 28 supplementary-law campaign theorems.

Every one of those 31 exact bodies has now been reconstructed and checked by
the existing intuitionistic Python kernel. The complete combined proof graph
has then been independently checked both by that unchanged Python kernel and
by the separately compiled Lean proof-bundle verifier.

No classical `DNE`, new kernel rule, new mathematical axiom, external
theorem-name lookup, digest-as-proof shortcut, or `sorry` supplies any proof
authority.

## Immutable parent and exact dependency slice

| Property | Independently checked value |
|---|---|
| Parent Alpha edition | v16 |
| Parent Alpha identity SHA-256 | `3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10` |
| Parent enrollment SHA-256 | `44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175` |
| Exact theorem dependency rows | `437` |
| Existing Stable-closed rows | `226` |
| Existing Alpha-closed rows | `180` |
| Genuine body-only rows requiring closure | `31` |
| Older Eisenstein-prefix body rows | `3` |
| New supplementary-law body rows | `28` |
| Exact theorem dependency edges | `1,427` |
| Ordered theorem-name SHA-256 | `9591f44b6cb8d2edbe1e4242193d28da948ebb61ba8f466377f7ceeae96c5b82` |
| Ordered 31-row promotion-name SHA-256 | `21e141da58e3262e250285ef9d43d78a5911d065e3746a824faea82642f7c8c7` |
| Exact immutable parent-surface SHA-256 | `669f6cbce067830bb0f87a413247866b25c508f11d9ca9df069530bfe9e3d24a` |

The three older dependency-closed Eisenstein-prefix rows are:

```text
eisenstein_initial_segment_indicator_choice
eisenstein_initial_segment_prefix_extend
eisenstein_initial_segment_prefix_exists
```

With those three genuine bodies available, the remaining 28 exact campaign
theorems have seven dependency-ready waves:

```text
11 → 7 → 4 → 2 → 1 → 2 → 1
```

Without preaccounting for the Eisenstein rows the full 31-row ready waves are
`13 → 8 → 4 → 2 → 1 → 2 → 1`. These counts describe dependency scheduling;
wave names and prior receipts are never accepted as actual proof evidence.

## Two actual theorem roots and one constructive combined bundle

The dependency graph uses exactly the existing Alpha-v16 enrollment order,
restricted to the 437 ancestors of the two supplementary-law roots.

| Root | Exact local theorem ID | Exact statement SHA-256 |
|---|---:|---|
| `quadratic_supplement_minus_one_complete` | `415` | `7ea81062b843e7fff4939ffce5b6fa14a87312619f7f49e3abd5993bfa02134e` |
| `quadratic_supplement_two_complete` | `436` | `146a886f8f3a54d358321b54faf68a591362016e86139bd487a5496c7af74034` |

Neither theorem depends on the other. Therefore the self-contained proof graph
has one additional **synthetic constructive conjunction node** with local ID
`437`, dependencies `(415, 436)`, and exact body:

```text
ImpIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0))))
```

Its designated target is precisely:

```text
And(
  _closed_formula(quadratic_supplement_minus_one_complete.statement),
  _closed_formula(quadratic_supplement_two_complete.statement),
)
```

This is an ordinary intuitionistic implication/conjunction derivation, not a
new enrolled theorem or a new axiom. It makes both independent exact roots and
every actual dependency reachable in one canonical artifact. The existing
unchanged proof-bundle checker requires every reachable local proof body to
check against its exact dependency-curried target.

The ordinary theorem-replay API separately compiles each requested promoted
theorem's own ancestor graph into an existing layered `Cut` certificate and
requires the original kernel judgment:

```text
check((), actual_certificate, _closed_formula(exact_original_statement))
  = True
```

An evidence-only successor edition may expose checked use only after decoding
the genuine artifact, checking every graph body, compiling the requested
theorem's actual empty-context proof, and receiving that original-kernel
acceptance. This receipt alone changes neither Stable nor Alpha authority.

## Durable complete proof artifact

```text
research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json
```

Exact canonical artifact identity and actual proof metrics:

```text
format:                peano-lab-bundle-v1
bytes:                 1732249
SHA256:                79fc4717dbe570bf836cca5ec699492ff3995700ec25336a20d03cc57261054c
theorem nodes:         437
synthetic conjunction: 1
total proof nodes:     438
dependency edges:      1429
body-proof occurrences:33173
original-kernel calls: 438
root local ID:         437
```

The artifact stores every exact closed formula, every dependency edge, and
every complete ordinary dependency-curried proof tree. Each actual body was
constructed in a microbatch of at most 16 rows, with the existing hard limits
of 125,000 structural proof occurrences and 25,000 proof objects per batch.
These limits were not increased or bypassed.

The independently reconstructed canonical checkpoints measured:

| Checkpoint | Actual body rows | Actual structural occurrences | Actual rehydrated proof objects | Actual formula annotations |
|---|---:|---:|---:|---:|
| First deterministic microbatch | `16` | `1,689` | `1,689` | `2,227` |
| Second deterministic microbatch | `15` | `2,060` | `2,060` | `4,842` |

Thus the largest genuine batch uses only 1.648% of the unchanged structural
bound and 8.24% of the unchanged proof-object bound.

Optional deterministic checkpoints contain the complete canonical proof trees,
not just names or receipts. Reloading independently rechecks every proof body.
Because canonical proof-tree decoding creates one distinct proof object for
each structural occurrence, checkpoint export honestly charges the larger
rehydrated object count against the same 25,000-object bound. Existing exact
checkpoint files are safely reused for resumable campaigns and are never
silently overwritten.

## Reproducing the independent checks

From the repository root:

```console
shasum -a 256 \
  research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json
```

Expected:

```text
79fc4717dbe570bf836cca5ec699492ff3995700ec25336a20d03cc57261054c
```

Independently check the full artifact through the separately compiled Lean
proof-bundle verifier:

```console
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json
```

Actual result:

```text
ACCEPT  .../supplementary-laws-proof-bundle-v1.json  nodes=438  root=437
```

Run the dedicated Python evidence-boundary, resource-policy, immutable-parent,
canonical-artifact, mutation, false-proof, and exact-root suite:

```console
cd peano-lab/py
python3 -m pytest -q tests/test_supplementary_laws_closure.py
```

To reconstruct the complete artifact into a new destination using only actual
checked microbatches and the unchanged proof kernels:

```console
cd peano-lab/py
python3 -m peano_lab.library.supplementary_laws_closure \
  --export /private/tmp/supplementary-laws-proof-bundle-v1.json
```

An existing dedicated checkpoint directory may additionally be supplied with
`--checkpoint-dir /private/tmp/supplementary-proof-checkpoints` to persist or
resume exact independently rechecked microbatches. The exporter refuses to
overwrite an existing destination. A changed frozen
statement, missing proof row, altered dependency edge, false proof body,
changed conjunction root, nonexistent artifact, noncanonical bytes, exceeded
resource limit, or changed actual-proof SHA-256 must always fail closed.
