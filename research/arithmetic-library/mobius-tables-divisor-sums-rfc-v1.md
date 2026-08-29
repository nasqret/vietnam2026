# Finite Möbius tables and genuine signed divisor sums

Status: an additive, non-admitting proof-development checkpoint over immutable
Alpha v30 and the previously checked bottom-layer support. This RFC does not
claim full G007, a new Alpha edition, Stable membership, publication, or an
independently compiled Lean certificate for this new tranche.

## Basis and scope

The parent Alpha catalogue remains
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`:
3,222 checked-use entries and 432 Stable entries. The earlier 170 bottom-layer
theorems remain separately proved, non-admitted support. In particular, the
old 21 Möbius-value/prime-step rows and 30 signed-table/algebra/reindex rows
are reused, not copied, renamed, or promoted into Alpha by this work.

Only three new ordinary-HA factories, their dedicated tests, and this RFC are
introduced. No kernel, tactic engine, checker, resource limit, old candidate,
catalogue, definition registry, bundle, renderer, or local/published snapshot
is changed by these files.

The achieved mathematical step is:

1. Construct actual signed-table prefix extensions and appended sums.
2. Construct a real finite table of independently defined Möbius values.
3. Construct actual divisor masks and a unique signed divisor sum for every
   `0<n<=N`, including the exact unit boundary and independence from `F(0)`.

Divisor involution, Möbius divisor-sum cancellation, rectangular Fubini,
Dirichlet convolution, and full finite-table Möbius inversion are not proved
here. None is inserted into a definition or assumed as a construction premise.

## Existing arithmetic representation

`ArithTable(N,F)`, `ArithAt(F,i,z)`, `SignedPrefixSum(F,l,z)`, and
`ArithTableEqual(F,G,l)` are the unchanged frozen relations.

The carrier is the actual nested natural pairing of two beta streams of
positive and negative natural components. Its four-component packing is the
existing `MatrixMinorFourCode` relation, used only as generic injective pairing;
no matrix hypothesis is imported. An entry or sum returns its canonical
`SignedBalance` code. Canonical codes are `0` for zero, `2` for positive one,
and `1` for negative one.

The table domain is inclusive: indices `0<=i<=N`. The sum and prefix-equality
relations use indices `0<=i<l`. The underlying beta streams are total, so a
proved packing also permits a different finite domain; this does not assert
that an arbitrary partially specified function has prescribed values beyond
its original domain.

Neither pointwise equality nor equal sums imply equality of packed table
codes or their non-normalized component streams.

## New conservative relations

Each public builder accepts actual compound arithmetic terms with an explicit
`variables` tuple and a `tag`. Every generated binder is checked against the
entire explicit context. These are ordinary first-order HA abbreviations,
not extra symbols or proof axioms.

### Actual prefix extension

`signed_arithmetic_table_extension_relation(F,G,l,z,*,tag,variables)`:

```text
ArithExtend(F,G,l,z) :=
  ArithTable(l,G)
  /\ ArithTableEqual(F,G,l)
  /\ ArithAt(G,l,z).
```

Only the earlier indices `i<l` are preserved. The entry at `l` is deliberately
replaced by the specified code `z`. Both beta component streams are actually
extended and recoded.

### Finite Möbius table

`mobius_arithmetic_table_relation(N,M,*,tag,variables)`:

```text
MobiusTable(N,M) :=
  ArithTable(N,M)
  /\ ArithAt(M,0,0)
  /\ forall i z.
       i!=0 -> i<=N -> ArithAt(M,i,z) -> Mobius(i,z).
```

`Mobius(i,z)` is the old independent graph based on actual prime-factor lists,
their length parity, squarefreeness and prime-square divisibility. The table's
zero entry is a deliberate convention, not a value of `Mobius(0,z)`; the latter
remains impossible for every `z`. Actual table lookup supplies the entry
existence needed alongside the universal correctness clause.

### Real divisor-mask entry and prefix

`divisor_mask_entry_relation(F,n,d,z,*,tag,variables)`:

```text
DivisorMaskEntry(F,n,d,z) :=
  (d!=0 /\ exists q. n=d*q /\ ArithAt(F,d,z))
  \/ ((d=0 \/ ~Dvd(d,n)) /\ z=0).
```

The quotient is a real natural witness of `n=d*q`. The unweighted input is
read at the divisor `d`, not silently at `q`. Relating those two indexings
requires a later divisor-involution proof.

`divisor_mask_prefix_relation(F,n,l,M,*,tag,variables)`:

```text
DivisorMask(F,n,l,M) :=
  ArithTable(l,M)
  /\ forall d z.
       d<=l -> ArithAt(M,d,z) -> DivisorMaskEntry(F,n,d,z).
```

The prefix bound `l` is independent of the fixed divisibility target `n`.
This is essential for the ordinary beta-prefix induction. Mask prefixes are
defined even at `n=0`, but the divisor-sum graph below excludes that input.
The zero index is always masked to zero; no lookup or constraint on `F(0)`
is needed to choose that output.

### Positive-only equality and actual divisor sum

`positive_arithmetic_table_equality_relation(F,G,N,*,tag,variables)`:

```text
ArithPositiveEqual(F,G,N) :=
  forall d a b.
    d!=0 -> d<=N -> ArithAt(F,d,a) -> ArithAt(G,d,b) -> a=b.
```

This intentionally differs from the existing prefix equality including zero.
In particular, `F(0)` and `G(0)` may be unrelated signed values.

`signed_divisor_sum_relation(F,n,z,*,tag,variables)`:

```text
DivisorSum(F,n,z) :=
  n!=0 /\ exists M.
    DivisorMask(F,n,n,M) /\ SignedPrefixSum(M,S n,z).
```

The fold is over exactly the `S n` indices `0,...,n`. Its zero entry contributes
zero, and every retained positive entry supplies its actual quotient. Both
natural sum traces and their canonical signed balance are genuine witnesses.

## Principal proved statements

The following notation expands to the actual first-order relations above.
Unique existence is represented in the sources by an existential value and
a universally quantified equality clause.

```text
arithmetic_signed_table_extend_at:
  forall N F l z. ArithTable(N,F) -> exists G. ArithExtend(F,G,l,z).

arithmetic_signed_table_append:
  forall N F z. ArithTable(N,F) -> exists G. ArithExtend(F,G,S N,z).

arithmetic_signed_table_singleton:
  forall z. exists F. ArithTable(0,F) /\ ArithAt(F,0,z).

arithmetic_signed_sum_append_transport:
  forall F G l a b c.
    ArithTable(l,G) -> ArithTableEqual(F,G,l) ->
    SignedPrefixSum(F,l,a) -> ArithAt(G,l,b) -> SignedAdd(a,b,c) ->
    SignedPrefixSum(G,S l,c).

mobius_table_exists:
  forall N. exists M. MobiusTable(N,M).

mobius_table_entry_iff:
  forall N M i z. MobiusTable(N,M) -> i!=0 -> i<=N ->
    ((ArithAt(M,i,z) -> Mobius(i,z)) /\
     (Mobius(i,z) -> ArithAt(M,i,z))).

divisor_mask_prefix_exists:
  forall N F n l. ArithTable(N,F) -> l<=N ->
    exists M. DivisorMask(F,n,l,M).

signed_divisor_sum_exists_unique:
  forall N F n. ArithTable(N,F) -> n!=0 -> n<=N ->
    exists z. DivisorSum(F,n,z) /\
      forall w. DivisorSum(F,n,w) -> w=z.

signed_divisor_sum_one:
  forall N F a. ArithTable(N,F) -> 1<=N -> ArithAt(F,1,a) ->
    DivisorSum(F,1,a).

signed_divisor_sum_positive_source_extensional:
  forall F G n a b. ArithPositiveEqual(F,G,n) ->
    DivisorSum(F,n,a) -> DivisorSum(G,n,b) -> a=b.
```

The primary divisor-sum statement SHA-256 is
`c148a766390471cd871ca467503a9a7c380142964aff8830ca412a20f743ba6d`.
The actual Möbius-table existence statement SHA-256 is
`9d90a11bd987bfe516272671293b30a0d264fe613d2632c628b5701634cf5dd3`.
The positive-only divisor-sum extensionality statement SHA-256 is
`5db775338790a36cdffa83a65f52f26d244827ba90942feb09600b9f5a202672`.

## Exact new inventory and dependency order

Factory order is extension, Möbius table, divisor mask. The last two are
independent branches over the shared extension substrate: divisor masks do
not assume any new Möbius-table statement, and no divisor-sum proof depends
on a cancellation or inversion theorem.

| Factory | Rows | Declared dependency edges | Tactic commands | Body-node occurrences | Maximum body / depth |
| --- | ---: | ---: | ---: | ---: | ---: |
| `make_arithmetic_table_extension_candidate_theorems` | 7 | 19 | 270 | 371 | 105 / 42 |
| `make_mobius_table_candidate_theorems` | 8 | 24 | 329 | 561 | 209 / 42 |
| `make_divisor_mask_candidate_theorems` | 22 | 49 | 781 | 1,477 | 175 / 55 |
| Total | 37 | 92 | 1,380 | 2,409 | 209 / 55 |

Every declared dependency is used by an actual command. Per-body object counts
equal per-body occurrence counts for all 37 bodies; this is not a claim about
cross-body object identity in a later shared certificate.

Ordered names, extension:

```text
arithmetic_signed_table_component_prefix_preserved
arithmetic_signed_table_equal_entry_transport
arithmetic_signed_table_extend_at
arithmetic_signed_table_append
arithmetic_signed_table_singleton
arithmetic_signed_sum_exists
arithmetic_signed_sum_append_transport
```

Ordered names, Möbius table:

```text
mobius_table_zero_constructor
mobius_table_append
mobius_table_exists
mobius_table_lookup
mobius_table_entry_iff
mobius_table_one_entry
mobius_table_extensional
mobius_table_restrict
```

Ordered names, divisor mask:

```text
divisor_mask_entry_zero
divisor_mask_entry_from_quotient
divisor_mask_entry_from_nondivisor
divisor_mask_entry_exists
divisor_mask_entry_functional
divisor_mask_entry_quotient_input
divisor_mask_entry_omitted_value
divisor_mask_prefix_zero_constructor
divisor_mask_prefix_append
divisor_mask_prefix_exists
divisor_mask_prefix_extensional
divisor_mask_prefix_restrict
divisor_mask_positive_quotient_entry
divisor_mask_omitted_entry
divisor_mask_entry_positive_source_extensional
divisor_mask_positive_source_extensional
signed_divisor_sum_exists
signed_divisor_sum_functional
signed_divisor_sum_exists_unique
signed_divisor_sum_zero_excluded
signed_divisor_sum_one
signed_divisor_sum_positive_source_extensional
```

Ordered-name SHA-256 values, hashing newline-separated names with a final newline:

- Extension: `259fc99deb7f06675d2abf167524782e26ae214f100bf9bf83cb0110f7b32e35`.
- Möbius table: `c2e7708e239031463ab6452127ac64a009e64c363c026c5abb8a75b8aa2e8b65`.
- Divisor mask: `43838944c65fb6ed295a904036f72aa45039e3e212735b637c3b1aadc476b7e2`.

## Actual verification and boundary tests

Each factory's full dedicated suite ran in a fresh process with unchanged
170/175 CPU-second limits, a 180-second wall alarm, and a 1,536 MiB peak-memory
assertion. The original `candidate_validation.replay_candidate_bodies`
checked every actual ordinary HA body.

| Dedicated suite | Tests passed | Pytest time | Whole runner time | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: |
| `test_arithmetic_table_extension_candidate.py` | 41 | 5.09 s | 5.3258 s | 367,427,584 |
| `test_mobius_table_candidate.py` | 34 | 10.20 s | 10.4390 s | 370,393,088 |
| `test_divisor_mask_candidate.py` | 110 | 21.03 s | 21.2957 s | 341,917,696 |

All 185 tests passed. They include exact independent AST contracts; compound
terms and large numerals; all nested generated-binder/context collisions;
ordered dependency checks; poisoned conclusions; omitted declared dependencies;
changed public hypotheses and fold lengths; and actual CRT-encoded beta models.

The semantic models construct the positive/negative streams and both natural
prefix-sum histories. They cover negative, zero and positive values; `N=0`;
the Möbius unit and prime-square boundaries; extension at `l>N`; different
non-normalized component representations; the explicit zero-mask branch;
quotient/index orientation; and unrelated `F(0)` values. They are regression
models, never mathematical proof authority.

The reported acceptance is body acceptance with the exact ordered theorem
premises, not by itself a full empty-context reconstruction of all inherited
dependencies. A subsequent complete original-HA closure and independent Lean
check must be recorded separately; stored hashes or receipts cannot replace
either verifier. No such later evidence is silently inferred in this RFC.

## Frozen source and test hashes

All candidate paths below are relative to
`peano-lab/py/peano_lab/library/`; test paths are relative to
`peano-lab/py/tests/`.

| File | SHA-256 |
| --- | --- |
| `arithmetic_table_extension_candidate.py` | `d39d08f7178b526daad51aaf4a75c325f567424bb8ae74906c030f4d72e9e294` |
| `test_arithmetic_table_extension_candidate.py` | `664d0e9a7986814c282213e0fe8d3c79e99a7e0320bef869758a63524c8978c7` |
| `mobius_table_candidate.py` | `7631337dd93f4a65e6f74ce9a5129d6701a496aa49969764c0945f4248676fc4` |
| `test_mobius_table_candidate.py` | `d7dfa93bf033fd83c03c2bbcd2ceda1347752c51c9a23b7eaf33ea574df0a096` |
| `divisor_mask_candidate.py` | `740efabb5cbf6e0c804e901dae423e319c52c86f605ebe2a4ad0bffb033d9543` |
| `test_divisor_mask_candidate.py` | `693ad1a5100c164f894eb86c747252771de006a6c3e5a11d47bd05a412a38e80` |

## Next genuine G007 work

The next construction must combine actual positive-divisor membership and
quotient witnesses with a proved finite involution/reindexing. From that one
can prove the Möbius cancellation identity, build the required weighted
convolution and finite Fubini transformations, and only then prove inversion.
The eventual input hypothesis must hold at every positive `m<=N`; positive-only
output equality must not accidentally impose an extra value at index zero.
