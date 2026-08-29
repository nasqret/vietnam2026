# Actual signed rectangular sums and finite Fubini

This additive mathematical checkpoint proves finite signed Fubini, with actual
row and column extraction and actual sum tables. It uses the unchanged
Heyting-arithmetic kernel, the existing natural-coded signed integers, and
the established packed two-beta arithmetic tables. It does not admit new
theorems to Alpha or Stable and does not close full Möbius inversion (G007).

The immutable basis is Alpha v30 (3,222 entries, Stable 432), the earlier 170
research theorems, and the subsequently completed 126 lower-tier theorems:
3,518 prior statements in total. The parent catalogue remains
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
The old 126-theorem mathematical tranche was committed as
`4fc164a846858045b07e7204575a5687ba64ffce`; none of those sources is changed.

## Exact conservative graphs

The explanatory names below denote the literal public builders, not new
kernel symbols or axioms. `ArithTable`, `ArithAt`, `ArithTableEqual`,
`SignedPrefixSum`, `SignedAdd`, and `Lt` are the unchanged inherited graphs.

An affine slice has five parameters:

```text
Slice(F,G,o,s,l) :=
  ArithTable(0,F) ∧ ArithTable(l,G) ∧
  ∀i. Lt(i,l) → ∃z. ArithAt(F,o+s*i,z) ∧ ArithAt(G,i,z).

SliceSum(F,o,s,l,z) :=
  ∃G. Slice(F,G,o,s,l) ∧ SignedPrefixSum(G,l,z).
```

The source packing is genuine. The previously proved total beta lookup and
domain-resizing theorems derive every requested source entry from it; no
function, finite-choice principle, supplied slice, or sum oracle is assumed.
Every output is constructed by actual extension of both beta streams.

Actual row sums and the rectangular total have seven parameters:

```text
RectRows(F,R,o,s,t,m,n) :=
  ArithTable(0,F) ∧ ArithTable(m,R) ∧
  ∀i. Lt(i,m) → ∃z.
    ArithAt(R,i,z) ∧ SliceSum(F,o+s*i,t,n,z).

RectSum(F,o,s,t,m,n,z) :=
  ∃R. RectRows(F,R,o,s,t,m,n) ∧ SignedPrefixSum(R,m,z).
```

Thus the entry at grid position `(i,j)` is the actual source lookup at
`(o+s*i)+t*j`, with `i<m` and `j<n`. Swapping the two dimensions and strides
gives column sums of the same entries. The equality of the two coordinate
expressions is proved with the inherited addition-permutation theorem;
it is not built into `RectSum` as an assumed Fubini identity.

The public builder interfaces are:

```text
signed_rectangular_slice_relation(F,G,o,s,l,*,tag,variables)
signed_rectangular_slice_sum_relation(F,o,s,l,z,*,tag,variables)
signed_rectangular_row_sums_relation(F,R,o,s,t,m,n,*,tag,variables)
signed_rectangular_sum_relation(F,o,s,t,m,n,z,*,tag,variables)
```

Each accepts compound terms and large double-and-add numerals in an explicit
declared context. Generated binders are checked against the whole context,
including unused declared variables. Malformed terms, duplicate or incomplete
contexts, reserved tags, and binder capture are rejected. Definitions and
their future display IDs are to be registered additively; this candidate
allocates no IDs and changes no existing definition identity.

The exact dependency structure is:

```text
ArithTable, Lt, ArithAt ──> Slice ──> SliceSum
SignedPrefixSum ───────────────────> SliceSum
ArithTable, Lt, ArithAt, SliceSum ──> RectRows
RectRows, SignedPrefixSum ─────────> RectSum
```

`ArithTable(N,F)` has an inclusive domain certificate through `N`. The slice
and fold windows are strictly `i<l`, and the row window is strictly `i<m`.
Their separately certified final endpoints are unused, not extra summands.
All uniqueness statements for tables use represented-value equality; no
arbitrary table code or positive/negative component representation is equated.

## Completed principal contracts

Actual affine extraction is constructed and extensionally unique:

```text
∀F o s l. ArithTable(0,F) → ∃G.
  Slice(F,G,o,s,l) ∧
  ∀H. Slice(F,H,o,s,l) → ArithTableEqual(G,H,l).
```

The generic finite signed Fubini theorem is:

```text
∀m F o s t n a b.
  RectSum(F,o,s,t,m,n,a) →
  RectSum(F,o,t,s,n,m,b) → a=b.
```

The constructive row-major endpoint supplies all output tables and the sum:

```text
∀F m n. ArithTable(m*n,F) → ∃R C z.
  RectRows(F,R,0,n,1,m,n) ∧
  RectRows(F,C,0,1,n,n,m) ∧
  SignedPrefixSum(R,m,z) ∧ SignedPrefixSum(C,n,z).
```

Here `0+n*i+1*j` is the ordinary row-major index `n*i+j`. The full affine
constructor `signed_rectangular_fubini_exists` also constructs `R,C,z` for
arbitrary `o,s,t,m,n` from `ArithTable(0,F)`. The generic and row-major roots
permit zero dimensions. Separate proved outer-zero and inner-zero lemmas
establish total zero in each case; a positive number of empty rows is not
mistaken for an absent row-table witness. Zero strides, hence repeated source
entries, are likewise permitted without a distinctness assumption.

Recommended principal roots for subsequent ordinary empty-context replay:

| Root | Exact statement SHA-256 |
| --- | --- |
| `signed_rectangular_slice_exists_extensionally_unique` | `d0fbe7f70725333cc208f00e860d04886fafdc5fef4a36bc6e811dd88391ddd4` |
| `signed_rectangular_fubini` | `74787482d51c759b2472790323be3c54494bbf97fab08de48afce458898fd14d` |
| `signed_rectangular_row_major_fubini` | `df286640d573e43c4ce8fc84ed9a405eb4568577f4f683001adb7ae8324ff3ec` |

The stronger affine constructor statement has SHA-256
`438e430f2b7689b3318149e7112187f3611e7eb3c0147e76479fb5aec365f819`.

## Proof route

1. **Actual slices.** Induct on the strict slice length. The base is an
   explicit packed table. At each step, obtain the real canonical source
   lookup and extend both output beta streams, preserving exactly the earlier
   signed values. Lookup functionality gives extensional uniqueness.
2. **Actual slice sums.** Apply the inherited signed-prefix-sum existence
   theorem to the constructed table. Extensionality makes the result
   independent of the table encoding. The successor lemmas construct a new
   slice and signed sum from the actual next source entry.
3. **Actual row-sum tables.** Induct on the row count, construct the next
   finite slice sum, and append its value to the row table. This supplies
   both row and column tables when their parameter orders are exchanged.
4. **Finite Fubini.** Induct on the outer dimension. In the successor step,
   actually construct the missing prefix column-sum table. The new row is a
   real slice; its entries add pointwise to the prefix column sums. The
   already proved signed pointwise-sum linearity and signed-add functionality
   identify the two totals. The zero-outer and zero-inner lemmas prove the
   base case without a nonempty-dimension premise.

The proof uses existing append, signed addition, sum extensionality and
linearity bodies. It does not assume the conclusion as a definition or use a
finite permutation, enumeration, numerical result, or choice oracle.

## Inventory and original-kernel evidence

| Source/factory suffix | New rows | Direct edges | Tactic commands | Body nodes |
| --- | ---: | ---: | ---: | ---: |
| `signed_rectangular_slice_candidate` | 15 | 37 | 523 | 858 |
| `signed_rectangular_sums_candidate` | 17 | 55 | 870 | 1,401 |
| Total | 32 | 92 | 1,393 | 2,259 |

Each factory is named `make_<module>_theorems` and receives `TheoremSpec`.
Every one of the 32 bodies has passed `replay_candidate_bodies` with the
unchanged original kernel. The maximum body has 213 nodes; maximum depth is
54. Body node occurrences equal distinct proof objects in these authoring
certificates. No kernel, parser, tactic, engine, catalogue, or proof bound is
changed.

The ordered-name SHA-256 (`"\n".join(names)`, no trailing newline) is
`83e70a5b157fded2c2ec78b7c2dbc57779b622ace39eff51c6e09d34c12024c8`.
Per-module ordered-name hashes are
`5508e204355d5687ac5d980bf7697dd5cbeafef5101d1e2ccde7bcc3163ddced`
and `fe63f731aa38ac09a0fe5144a7394a58e8e2193a0d8003ca63f12015867ee948`.

The mathematical source hashes are:

| File | SHA-256 |
| --- | --- |
| `signed_rectangular_slice_candidate.py` | `d676600c931936ff00996209c7d744c269427eaf08611fb625e471f608861e5e` |
| `signed_rectangular_sums_candidate.py` | `0ce96c5155bb7bf47f5ae2b8151631bd981263f7d05c25f6ec8b3cd365d7a26e` |

The focused regressions independently reconstruct the new expanded formulas,
check every generated binder against the full declared context, compare all
32 statement ASTs with all 3,518 prior statements, reject a false target for
every body, and drop and poison every declared dependency. Numerical
diagnostics construct real beta-coded source, slice, row and column tables
and both natural cumulative traces. They include negative values, unrelated
component representations, unused endpoints, zero dimensions, zero strides,
and nonsquare grids. These examples are diagnostics, not the proof authority.

All **356 distinct focused tests passed**: 139 slice tests and 217 rectangular
tests. This comprises 32 original-kernel bodies, 32 false targets, all 184
single-dependency drop/poison mutations, and 108 independent contract, hygiene,
topology and actual-beta-trace checks. Earlier body preflights and repeat runs
are not added to this count. The exact-AST comparison found no duplicate
among the 32 new statements or against any of the 3,518 prior statements.

The largest final regression batch took 123.17 seconds; maximum peak RSS
across final regression batches was 467,779,584 bytes. Earlier original-body
microbatches reached at most 567,558,144 bytes. All processes completed within
the unchanged bounds. The frozen test source hashes are:

| File | SHA-256 |
| --- | --- |
| `test_signed_rectangular_slice_candidate.py` | `bf0cf5ff4b9196e75a0e3f750e7b6758efbf15c5f8a71c2797f2582c8cb102ec` |
| `test_signed_rectangular_sums_candidate.py` | `ed046aaf5aa98b2d38f044071c3dd1852d4534cb11d9a7b74fac436fded27651` |

Authoring and test processes retain CPU limits 170/175 seconds, a 180-second
wall alarm, and the 1,536 MiB peak-RSS gate. Large mutation suites are divided
into fresh sequential subprocesses; no limit is raised or bypassed. A complete
dependency-closed bundle, independently compiled Lean verification, and
ordinary empty-context principal-root receipts are separate integration gates;
the individual-body results here are not represented as those later receipts.

## Scope deliberately not claimed

This is full finite signed rectangular Fubini and actual table construction,
not an infinite-sum interchange or convergence theorem. It is reusable input
to future divisor/convolution proofs, but proves neither Möbius inversion nor
an arbitrary convolution identity on its own. It adds no Alpha or Stable
membership, alters no published proof or definition, and performs no commit,
push, deployment, or live-service operation.
