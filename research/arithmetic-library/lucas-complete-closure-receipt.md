# Independently checked complete constructive Lucas-theorem proof

Date: **2026-08-25**.

The exact originally enrolled unrestricted multidigit theorem
`lucas_theorem` now has a complete self-contained constructive proof graph.
Its statement, hypotheses, witnesses, finite base-`p` digit chains, complete
coefficient/product witnesses, and theorem identity have not been weakened or
changed.

Every local ordinary intuitionistic proof body has passed the original Python
kernel. The complete canonical proof bundle has separately passed the
compiled Lean checker, whose existing soundness theorem derives the exact
standard-natural-number semantics of its designated formula.

No theorem-name lookup, provenance hash, host-language computation, classical
`DNE`, new inference rule, unproved axiom, `sorry`, or release-status label is
accepted in place of an actual constructive proof.

## Exact immutable parent and dependency closure

| Property | Independently checked value |
| --- | --- |
| Parent Alpha edition | v17 |
| Parent Alpha identity SHA-256 | `db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4` |
| Parent enrollment SHA-256 | `44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175` |
| Exact theorem nodes | `213` |
| Exact theorem dependency edges | `617` |
| Already checked Stable parent nodes | `138` |
| Already checked Alpha-only parent nodes | `1` |
| Body-only parent nodes requiring closure | `74` |
| Checked proof bodies reused from the quadratic-reciprocity artifact | `136` |
| Checked parent bodies reconstructed from their original scripts | `3` |
| Total freshly reconstructed and kernel-checked theorem bodies | `77` |
| Ordered 213-theorem name SHA-256 | `52d9e8ec5eb1942d5a583cd272b7d26aecae5d8e6d4c78a48b6354a541f7af52` |
| Ordered 74-body-only name SHA-256 | `090793ef1fc8e9130bff47bbf42253dad06d05e4d1ddf3e580f6c3196a0f1b71` |
| Ordered 77-reconstructed-body name SHA-256 | `db97f67f46ce3f81350061d1a755272237e1d9e23604030beeeeee8332783d52` |
| Exact frozen parent-surface SHA-256 | `f443f25090da07f3fe4432f7b75b3de5c15512bf4da6d7771524828d9c2d02cd` |

The three already checked prerequisites absent from the quadratic-reciprocity
proof graph were independently reconstructed as exact ordinary proof bodies:

```text
mul_lt_mul_succ_left_nonzero
beta_factor_divides_product
add_shuffle_middle
```

The 74 body-only obligations consist of 30 older constructive foundations and
44 exact Lucas campaign theorems. Their dependency-ready layer widths are:

```text
31 → 10 → 8 → 5 → 3 → 2 → 2 → 1 → 1 → 1 → 1 → 2
   → 1 → 1 → 1 → 1 → 1 → 1 → 1
```

Actual proof reconstruction was performed in ten independently checked
microbatches of at most eight rows. No microbatch exceeded the existing
sixteen-row, 125,000-structural-node, or 25,000-proof-object limits.

## Exact Lucas root and durable canonical proof

```text
theorem:                lucas_theorem
root local node ID:     212
statement SHA-256:      396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564
artifact format:        peano-lab-bundle-v1
artifact bytes:         1103202
artifact SHA-256:       02b1eef360dce55f0156bda2029e64567b8b83b5d58833d6c4f8695ab8d41832
actual proof nodes:     213
actual dependency edges:617
total body proof nodes: 15103
original kernel calls:  213
ordinary root nodes:    19102
```

The independently retained artifact is:

```text
research/arithmetic-library/artifacts/lucas-proof-bundle-v1.json
```

Every canonical local node stores its complete ordinary proof body and the
exact indices of its dependency formulas. The final local root is precisely
the previously enrolled `lucas_theorem` first-order formula, not a synthetic
conjunction or weaker intermediate result. All 213 nodes are reachable from
that exact theorem root.

The unchanged layered `Cut` compiler also materialized one complete ordinary
empty-context proof of the exact `lucas_theorem` formula. Its certificate has
**19,102 structural proof nodes**, and the original intuitionistic kernel
independently accepted `check((), certificate, exact_lucas_formula)`.

## Independent compiled Lean verification

Using the existing separately compiled, clean Lean companion:

```text
$ peano_lab_bundle_verify research/arithmetic-library/artifacts/lucas-proof-bundle-v1.json
ACCEPT  .../lucas-proof-bundle-v1.json  nodes=213  root=212
```

Lean's existing `checkBundle_sound` theorem supplies the constructive soundness
judgment for this exact designated root. This is a separately compiled checker;
it neither imports the Python checker implementation nor trusts its receipts.
No new WMI receipt is claimed.

## Release boundary

This proof receipt and its genuine artifact **do not mutate Alpha v17 or
Stable**. In immutable Alpha v17, `lucas_theorem` and its 73 other body-only
ancestors remain `body_checked` and have no release checked-use authority.
Any future dependency-closed evidence promotion must be an independent
explicit immutable release, with its own parent, mutation, provenance,
authority, and publication gates.
