# Actual signed table arithmetic and weighted-sum linearity

This additive, non-admitting G007 foundation consists of 40 new ordinary
Heyting-arithmetic theorems. It constructs actual finite pointwise arithmetic
tables, proves signed prefix-sum linearity, and constructs and uniquely
identifies signed weighted sums. It does **not** prove divisor-sum cancellation,
Möbius inversion, or rectangular Fubini.

The 3222-theorem Alpha v30 parent, Stable 432, and all 170 previously completed
research-checkpoint theorems remain unchanged. The parent catalogue is pinned
to SHA-256
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
No kernel, proof checker, admission rule, resource ceiling, catalogue, public
snapshot, or service is changed by these mathematical modules.

## Exact representation and window boundaries

`ArithTable(N,F)`, `ArithAt(F,i,z)`, `ArithTableEqual(F,G,l)`,
`SignedPrefixSum(F,l,z)`, `SignedAdd`, and `SignedMul` retain their existing
conservative definitions. A table code packs two actual beta sequences of
natural positive and negative components. A lookup and a sum return the
canonical signed code of the corresponding difference. Zero has code 0,
positive one has code 2, and negative one has code 1.

The table certificate uses the inclusive domain `i ≤ N`. The new operation
and sum windows are **strictly `i < l`**. Thus `ArithTable(l,F)` also certifies
one unused endpoint, `i=l`; this does not turn the sum into an `l+1`-term sum.
The empty-window relations still require actual packed tables. They do not
make arbitrary invalid natural codes into tables by vacuity.

Different beta codes and different overlapping component pairs can represent
the same values. Output uniqueness below is `ArithTableEqual`, not equality of
the raw table codes or of the positive and negative components. Weighted-sum
output codes themselves are canonical and literally unique.

## Four conservative graphs

The displayed names are abbreviations only; every public builder emits strict
first-order HA and checks the complete declared variable context, including
unused declared variables, for binder capture. Compound arguments and large
decimal numerals are supported. Stable definition identifiers are allocated by
the separate integration registry, not by these proof modules.

`ArithAdd(F,G,H,l)` means:

```text
ArithTable(l,F) ∧ ArithTable(l,G) ∧ ArithTable(l,H) ∧
∀i<l. ∃a b c.
  ArithAt(F,i,a) ∧ ArithAt(G,i,b) ∧ ArithAt(H,i,c) ∧ SignedAdd(a,b,c).
```

`ArithMul(F,G,H,l)` has exactly the same table and entry witnesses, with
`SignedMul(a,b,c)` in the last position.

`ArithScale(a,F,G,l)` means:

```text
ArithTable(l,F) ∧ ArithTable(l,G) ∧
∀i<l. ∃b c. ArithAt(F,i,b) ∧ ArithAt(G,i,c) ∧ SignedMul(a,b,c).
```

Finally:

```text
SignedWeightedSum(W,F,l,z) ↔
  ∃H. ArithMul(W,F,H,l) ∧ SignedPrefixSum(H,l,z).
```

The weighted-sum definition contains an actual product table and actual sum
traces. It contains no linearity law, divisor identity, or requested target
formula.

Public builder signatures are:

```python
signed_table_pointwise_add_relation(F, G, H, l, *, tag, variables)
signed_table_pointwise_multiply_relation(F, G, H, l, *, tag, variables)
signed_table_scalar_multiply_relation(a, F, G, l, *, tag, variables)
signed_weighted_sum_relation(W, F, l, z, *, tag, variables)
```

## Principal proved statements

For each binary operation, the output table is constructed rather than
supplied:

```text
∀l F G. ArithTable(l,F) → ArithTable(l,G) →
  ∃H. ArithAdd(F,G,H,l) ∧
      ∀K. ArithAdd(F,G,K,l) → ArithTableEqual(H,K,l).
```

The corresponding statement holds for `ArithMul`. The scalar version requires
only `ArithTable(l,F)` and constructs an extensionally unique `G` satisfying
`ArithScale(a,F,G,l)` for every canonical signed scalar `a`.

The actual signed sum laws are:

```text
ArithAdd(F,G,H,l) ∧ SignedPrefixSum(F,l,a) ∧
  SignedPrefixSum(G,l,b) ∧ SignedPrefixSum(H,l,c)
  → SignedAdd(a,b,c).

ArithScale(a,F,G,l) ∧ SignedPrefixSum(F,l,b) ∧
  SignedPrefixSum(G,l,c)
  → SignedMul(a,b,c).
```

Separate `_values_exist` corollaries construct all the sum values in these
statements. Negative values, negative scalars, zero scalars, and the empty
prefix are included; no positivity assumption is hidden.

Every two valid tables have a unique actual weighted-sum value:

```text
∀l W F. ArithTable(l,W) → ArithTable(l,F) →
  ∃z. SignedWeightedSum(W,F,l,z) ∧
      ∀u. SignedWeightedSum(W,F,l,u) → u=z.
```

The proved weighted laws are:

```text
ArithAdd(F,G,H,l) ∧ SignedWeightedSum(W,F,l,a) ∧
  SignedWeightedSum(W,G,l,b) ∧ SignedWeightedSum(W,H,l,c)
  → SignedAdd(a,b,c).

ArithScale(a,F,G,l) ∧ SignedWeightedSum(W,F,l,b) ∧
  SignedWeightedSum(W,G,l,c)
  → SignedMul(a,b,c).
```

The empty weighted sum is proved equal to canonical zero, and its actual
zero-length product table and sum witnesses are separately constructed.

## Proof architecture and shared support

The operation constructors use ordinary finite induction. At each successor
they obtain genuine canonical input values, construct their `SignedAdd` or
`SignedMul` value using the existing scalar totality proof, and extend the two
actual beta output streams while preserving the preceding strict prefix.
They use the new, separately owned `arithmetic_table_extension_candidate`
substrate. Its seven theorems are **not** copied into, renamed, or counted as
new rows of this 40-theorem family.

The direct shared interfaces used here are
`arithmetic_signed_table_extend_at`,
`arithmetic_signed_table_equal_entry_transport`, and
`arithmetic_signed_sum_exists`. Complete dependency closure also includes
their genuine prerequisites. Their exact accepted targets are checked by
the separate checkpoint-composition gate.

The prefix-sum laws are ordinary induction on `l`, using the original signed
successor decomposition. Addition uses proved signed associativity,
commutativity, and a constructed intermediate sum. Scalar linearity uses the
proved scalar distributivity graph and literal signed-value functionality.
The weighted laws then establish pointwise distributivity or scalar
commutation for the real product tables and apply those prefix-sum laws.

No finite-choice axiom, sum oracle, host arithmetic certificate, new logical
axiom, or equation between arbitrary raw representatives is used.

## Frozen mathematical inventory

Factories are ordered as follows:

| Module and factory suffix | New rows | Direct dependencies | Tactic commands | Body nodes | Maximum body depth |
| --- | ---: | ---: | ---: | ---: | ---: |
| `signed_table_operations_candidate` | 23 | 68 | 1150 | 1758 | 46 |
| `signed_sum_linearity_candidate` | 7 | 28 | 442 | 609 | 42 |
| `signed_weighted_sum_candidate` | 10 | 25 | 525 | 834 | 68 |
| Total | 40 | 121 | 2117 | 3201 | 68 |

Each module exposes `make_<module>_theorems(TheoremSpec)`. The largest individual
body has 195 proof nodes. All reported body node occurrences are also distinct
proof objects in these authoring certificates.

Source SHA-256 pins:

```text
signed_table_operations_candidate.py
465e623dbe3fcac0eb70ca72e890d1cc8046b3a476014dc65d187b3f30f4893f
signed_sum_linearity_candidate.py
8da9d92ec3e204583e7539fc2ff6ca7af5677a909a59831951e978deab9d69c0
signed_weighted_sum_candidate.py
2cbbb6486f0a75bbf97165018ef7539dd90c8a06317d0ed037ed95afcc72db07
```

Ordered-name SHA-256, joining names with `\n` and no trailing newline:
`508f9c9dfde41f64ade7fa5fd2a6ca673fd7c8ca226655e1aa4dea98c4f3439c`.
Literal principal-statement hashes and per-body node/depth metrics are pinned
in the matching three test files.

## Verification boundary and reproducibility

Every one of the 40 actual authoring bodies has passed
`candidate_validation.replay_candidate_bodies` and the unchanged original
kernel. These are dependency-curried body checks; they are not on their own a
new Alpha admission or a claim that stored receipts replace proof checking.
Complete empty-context HA certificates and independent compiled Lean checks
are the responsibility of the separate lower-tier checkpoint compositor.

The regression suites include independently expanded public definitions and
principal endpoints, all generated-binder collision cases, explicit compound,
large-numeral, zero and repeated arguments, actual finite CRT beta-table models,
all 40 false targets, and every dropped and poisoned direct dependency.
Numerical models are tests of the representation and boundary contracts, not
substitutes for the HA proofs.

The final focused regression inventory is **419 passing tests**: 250 table
operation tests, 72 prefix-linearity tests, and 97 weighted-sum tests. The three
positive-body groups and three remaining-regression groups ran in fresh
bounded processes. The longest group took 105.13 seconds; the largest recorded
RSS was 380,960,768 bytes. These totals count each test once, not the earlier
authoring reruns. They include all 40 real bodies and all 242 dropped/poisoned
direct-dependency mutations.

Run small fresh-process body batches, for example:

```sh
PYTHONPATH=peano-lab/py python3 peano-lab/py/tests/test_signed_table_operations_candidate.py --start 0 --count 4
PYTHONPATH=peano-lab/py python3 peano-lab/py/tests/test_signed_sum_linearity_candidate.py --start 3 --count 2
PYTHONPATH=peano-lab/py python3 peano-lab/py/tests/test_signed_weighted_sum_candidate.py --start 8 --count 2
```

The same drivers accept `--pytest-select` for focused test subsets. Every
driver installs the original 170/175-second CPU and 180-second wall ceilings
and checks the original 1536 MiB RSS ceiling before reporting success. None of
the kernel, proof-node, parser, independent-checker, or process limits is raised.

## Deliberately open work

There is no rectangular row/column family or Fubini theorem here. A future
tranche must construct real affine slices, row and column sum tables, and
their zero-dimensional boundaries before proving the rearrangement law.
Likewise these weighted-sum laws do not imply, or purport to prove, the
divisor-mask cancellation identity or full G007 Möbius inversion. This work is
local mathematical development; it performs no commit, deployment, or Alpha or
Stable promotion.
