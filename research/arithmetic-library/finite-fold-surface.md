# β-coded finite folds for quadratic reciprocity

## Scope and trust boundary

Quadratic reciprocity needs finite sums, counts, intervals, and powers, but the
native term language still contains only `0`, `S`, `+`, and `*`. This design
adds no function symbol, list type, sequence type, or trusted predicate.

The authoring module `peano_lab.library.finite_fold_surface` expands every
displayed relation into ordinary first-order PA text. It is not imported by
the theorem registry and grants no theorem authority. Its `BetaAt` and
`Product` output is parser-checked to be exactly alpha-equivalent to the
conventions already used by the checked FTA development.

Throughout, write

$$
\operatorname{At}(b,c,i,x)
\quad\Longleftrightarrow\quad
x<1+(i+1)c\ \land\ \exists q.\ b=q(1+(i+1)c)+x.
$$

All sequence identity remains extensional. Different pairs $(b,c)$ may decode
the same finite prefix and must never be equated merely because their entries
agree.

## Sum

The finite sum relation stores prefix sums in a second β-code:

$$
\begin{aligned}
\operatorname{Sum}(b,c,l,n)\;:\!\Longleftrightarrow\;
\exists u,v.\;&\operatorname{At}(u,v,0,0)\land
\operatorname{At}(u,v,l,n)\\
&\land\forall i<l.\ \exists a,r,s.\
 \operatorname{At}(b,c,i,a)\land
 \operatorname{At}(u,v,i,r)\\
&\hspace{34mm}\land\operatorname{At}(u,v,i+1,s)\land s=r+a.
\end{aligned}
$$

This is the checked `Product` convention with base value one replaced by zero
and multiplication replaced by addition. It records enough information for
existence, functionality, prefix decomposition, append, and transport proofs;
no recursive sum function is added.

The first Sum ladder should be:

1. `beta_prefix_sum_trace_exists` — clone the checked product-trace induction,
   using `beta_prefix_extend` to append each new partial sum;
2. `beta_sum_exists` — decode the trace at position $l$;
3. `beta_sum_functional` — induction on $l$, using exact trace steps and
   `add_congr`;
4. `beta_sum_exists_unique` — package the preceding two results;
5. `beta_sum_zero`, `beta_sum_succ_decompose`, and `beta_sum_succ_append`;
6. `beta_sum_transport_prefix` — the additive analogue of
   `beta_product_transport_prefix`;
7. `beta_sum_append` and `beta_sum_split` for interval decompositions.

The trace-existence proof should reuse only the β encoding infrastructure and
elementary additive/order lemmas. It must not depend on prime factorization or
FTA.

## Bit counts

A reusable first-order `CountWhere` cannot quantify over a predicate. Instead,
the client constructs a β-coded indicator prefix and the generic library
counts its ones:

$$
\begin{aligned}
\operatorname{AllBits}(b,c,l)&:\!\Longleftrightarrow
 \forall i<l.\ \exists z.\operatorname{At}(b,c,i,z)\land(z=0\lor z=1),\\
\operatorname{BitCount}(b,c,l,n)&:\!\Longleftrightarrow
 \operatorname{Sum}(b,c,l,n)\land\operatorname{AllBits}(b,c,l).
\end{aligned}
$$

Because the relation includes decoded bit witnesses, it cannot hold vacuously
at a populated position. Its initial API is:

1. `bit_count_exists`: `AllBits` plus `beta_sum_exists` gives a count;
2. `bit_count_functional`: inherited from `beta_sum_functional`;
3. `bit_count_zero` and `bit_count_succ_decompose`;
4. `bit_count_le_length`: induction using $z=0\lor z=1$;
5. parity lemmas for appending a zero or one;
6. extensional transport between indicator codes.

Two exact sum-composition interfaces are now body-green. In readable
notation, `beta_sum_pointwise_add` states that three common-length prefixes
with exact sums `n,m,q` satisfy `n+m=q` whenever their decoded entries obey
`s_i=a_i+z_i`. Its six-dependency, 127-command constructive body checks at
`195/57` nodes/depth, with 195 objects, 194 edges, and no reuse. The constant
case is supplied by `beta_repeat_sum_exact` and
`beta_repeat_sum_exists_exact`: a length-`l` `Repeat(a)` prefix has exact sum
`l*a`, and a code plus trace with that endpoint always exists. Their bodies
check at `85/32` and `33/21`. The focused sum audits pass `3/3` and `4/4`, and
the combined constant/pointwise run passes `7/7` in 2.18 seconds. All three
are fully expanded, constructive, unregistered, and unadmitted.

[`pointwise-add source`](../../peano-lab/py/peano_lab/library/finite_sum_pointwise_add_candidate.py)
· [`pointwise-add test`](../../peano-lab/py/tests/test_finite_sum_pointwise_add_candidate.py)
· [`constant-sum source`](../../peano-lab/py/peano_lab/library/finite_repeat_sum_candidate.py)
· [`constant-sum test`](../../peano-lab/py/tests/test_finite_repeat_sum_candidate.py)

The first exact complement-count theorem is now body-green in
[`finite_bitcount_complement_candidate.py`](../../peano-lab/py/peano_lab/library/finite_bitcount_complement_candidate.py).
In readable notation, `complementary_bit_counts_add_length` proves

$$
\begin{gathered}
\operatorname{BitCount}(b,c,l,n)\land
\operatorname{BitCount}(z,e,l,m)\land\\
\Bigl[\forall i,a,d.\ i<l\Longrightarrow
\operatorname{At}(b,c,i,a)\Longrightarrow
\operatorname{At}(z,e,i,d)\Longrightarrow
((a=0\land d=1)\lor(a=1\land d=0))\Bigr]\\
\Longrightarrow n+m=l.
\end{gathered}
$$

Its direct dependencies are `bit_count_zero`,
`bit_count_succ_decompose`, `le_succ`, `le_refl`, and `add_succ_left`.
The 112-command dependency-curried body has `220` nodes at depth `46`,
`211` proof objects, `219` edges, and `9` reused objects. The
[`focused test`](../../peano-lab/py/tests/test_finite_bitcount_complement_candidate.py)
passes `3/3` in 1.47 seconds, finds no `DNE`, and confirms that the theorem is
absent from the public registry. It is not recursively closed or admitted.

This is deliberately a one-dimensional theorem: it compares two prefixes of
the same length at the same bounded index. It does not itself reorder a nested
rectangle or exchange row and column folds; the later provenance-carrying
Fubini layer now performs that composition.

The exact finite-sum permutation API is body-green as well. Replacement
balance and last-swap invariance measure `327/59` and `133/50` nodes/depth;
fixed-last reindexing and the arbitrary bounded permutation theorem measure
`85/33` and `631/88`. The final theorem uses decoded bounded
injectivity/surjectivity plus exact `Sum` traces, so it preserves semantic
content without equating raw beta codes. These four candidates are
dependency-curried, unregistered and unadmitted.
See the exact
[`swap source`](../../peano-lab/py/peano_lab/library/finite_sum_permutation_candidate.py),
[`swap test`](../../peano-lab/py/tests/test_finite_sum_permutation_candidate.py),
[`reindex source`](../../peano-lab/py/peano_lab/library/finite_sum_reindex_candidate.py),
and
[`reindex test`](../../peano-lab/py/tests/test_finite_sum_reindex_candidate.py).

The Eisenstein client now has the complete body-green one-orientation path
from semantic row counts to quotient-sum/rectangle-total equality. Its
four-step row bridge ends at `111/55` and `119/72` nodes/depth; three outer
transport/endpoint bodies then pass at `104/52`, `73/54`, and `67/51`. See
the [`row-quotient source`](../../peano-lab/py/peano_lab/library/eisenstein_row_quotient_candidate.py),
[`outer-sum source`](../../peano-lab/py/peano_lab/library/eisenstein_outer_sum_bridge_candidate.py),
and their
[`row test`](../../peano-lab/py/tests/test_eisenstein_row_quotient_candidate.py)
and [`outer test`](../../peano-lab/py/tests/test_eisenstein_outer_sum_bridge_candidate.py).
The same contracts apply after swapping the two odd primes.

Two further client bodies expose cellwise transpose data at `95/33` and
`116/58`: decoded `(i,j)` and `(j,i)` bits are complementary, and the inner
row witnesses can be opened from both outer prefixes. See the
[`cell source`](../../peano-lab/py/peano_lab/library/eisenstein_transposed_cell_candidate.py),
[`outer-cell source`](../../peano-lab/py/peano_lab/library/eisenstein_transposed_outer_cell_candidate.py),
and their focused
[`cell test`](../../peano-lab/py/tests/test_eisenstein_transposed_cell_candidate.py)
and
[`outer-cell test`](../../peano-lab/py/tests/test_eisenstein_transposed_outer_cell_candidate.py).

A body-green six-body follow-on now turns those local witnesses into a whole semantic
transposed column. Its compact receipts are
`dependencies / commands / nodes / depth / objects / edges / reused`:

| Candidate | Exact role | Receipt |
|---|---|---:|
| `eisenstein_transposed_outer_column_choices` | choose the fixed cell from every swapped row while retaining its outer and inner witnesses | `2 / 37 / 42 / 26 / 42 / 41 / 0` |
| `eisenstein_transposed_column_prefix_extend` | append one provenance-carrying column entry | `2 / 55 / 80 / 31 / 80 / 79 / 0` |
| `eisenstein_transposed_column_prefix_exists` | beta-code the complete bounded column | `5 / 56 / 64 / 29 / 64 / 63 / 0` |
| `eisenstein_transposed_column_prefix_all_bits` | project the constructed column to `AllBits` | `1 / 48 / 56 / 33 / 56 / 55 / 0` |
| `eisenstein_transposed_column_pointwise_complement` | align each original-row bit with its constructed-column complement | `2 / 64 / 87 / 47 / 87 / 86 / 0` |
| `eisenstein_row_transposed_column_count_partition` | construct the column `BitCount m` and prove `n+m=k` | `6 / 105 / 117 / 56 / 117 / 116 / 0` |

The last theorem is the strongest current endpoint: from an original
semantic row and count `n`, the swapped semantic outer prefix, and `i<h`, it
returns column code/scale `z,e` and count `m` with the full semantic column
prefix, `BitCount(z,e,k,m)`, and `n+m=k`. Each stored column bit deliberately
retains the decoded swapped outer count, an existential inner row code and
scale with row semantics and its own `BitCount`, and the decoded inner cell.
Thus no bare provenance-free beta code is being treated as a column.

The
[`column source`](../../peano-lab/py/peano_lab/library/eisenstein_transposed_column_candidate.py)
and
[`focused test`](../../peano-lab/py/tests/test_eisenstein_transposed_column_candidate.py)
pass `5/5` in 5.05 seconds under the 60-second laptop cap. The test pins all
contracts, dependencies, hashes and receipts, checks native PA expansion and
alpha-hygiene, and excludes automation and classical escape. These bodies
remain dependency-curried, unregistered and unadmitted.

The subsequent nine-body client now closes that nested fold at the body-green
level. It beta-codes and sums the column counts over all `i<h`, retargets the
provenance-preserving column witnesses during induction, folds
`row_count_i+column_count_i=k`, and proves that the constructed column total
is the swapped row total. `eisenstein_fubini_universal` is `264/65`
nodes/depth and `eisenstein_rectangle_floor_sum_identity` is `65/37`.

The quotient-sum wrapper then keeps both scaled/division prefixes, both
semantic outer prefixes, and both exact sums and proves `Q+U=h*k` at
`145/68`. All these are dependency-curried, unregistered, and unadmitted;
recursive WMI closure remains separate.

Gauss's lemma will construct a concrete indicator whose $i$th bit says that
the canonical residue of $a(i+1)$ lies in the upper half of the nonzero
residues. That construction is formula-specific bounded induction, not an
illicit polymorphic predicate argument.

## Intervals and constant prefixes

For a start value $a$, define

$$
\operatorname{Range}(b,c,a,l)
\;:\!\Longleftrightarrow\;
\forall i<l.\ \operatorname{At}(b,c,i,a+i).
$$

Thus `Range(b,c,0,l)` encodes $0,\ldots,l-1$, while
`Range(b,c,1,l)` encodes $1,\ldots,l$. The general start value avoids
separate zero-based and one-based relations.

Similarly,

$$
\operatorname{Repeat}(b,c,a,l)
\;:\!\Longleftrightarrow\;
\forall i<l.\ \operatorname{At}(b,c,i,a).
$$

Both existence proofs use an empty-prefix base and `beta_prefix_extend` in the
successor step. The Range step appends $a+l$; the Repeat step appends $a$.
Planned checked names are `beta_range_exists`, `beta_repeat_exists`, their
successor elimination lemmas, and one-way extensional transport facts.

Range is not meant to replace bounded quantification. Its purpose is to give
finite folds an explicit enumerated input sequence, for example the
$1,\ldots,(p-1)/2$ half-system in Gauss's lemma.

## Relational powers

Power is deliberately a wrapper around existing finite products:

$$
\operatorname{Pow}(a,e,n)
\;:\!\Longleftrightarrow\;
\exists b,c.\ \operatorname{Repeat}(b,c,a,e)\land
\operatorname{Product}(b,c,e,n).
$$

This choice makes $a^e$ available without changing the term grammar and
reuses the audited product trace, append, decomposition, functionality, and
transport theorems. It also ensures $a^0=1$ through the existing empty-product
endpoint.

The power ladder is:

1. `pow_exists`: combine `beta_repeat_exists` with `beta_product_exists`;
2. `pow_functional`: use the two Repeat hypotheses to prove extensional
   equality of their factors, transport one Product with
   `beta_product_transport_prefix`, then apply `beta_product_functional`;
3. `pow_zero`: apply `beta_product_zero`;
4. `pow_succ_decompose`: apply `beta_product_succ_decompose`, identify the
   last factor with $a$ using Repeat and `beta_at_unique`, and restrict Repeat
   to the shorter prefix;
5. `pow_succ_append`: use `beta_factor_prefix_product_append` to append one
   more copy of $a$ and prove the extended code still satisfies Repeat;
6. addition and multiplication laws for exponents;
7. congruence preservation by induction on the exponent.

The use of two existential code parameters means functionality is not a
direct call to `beta_product_functional`, which assumes one factor code. The
transport step is logically essential.

## Dependency architecture

```text
                  checked BetaAt / prefix extension
                               |
                 +-------------+-------------+
                 |                           |
          Sum trace/existence            Range / Repeat
                 |                           |
          Sum functionality       checked Product + transport
                 |                           |
      +----------+----------+                Pow
      |                     |                 |
  AllBits              Sum append       Pow recursion
      |                     |                 |
  BitCount           quotient sums      modular powers
      |                     |                 |
 complement counts      Eisenstein         Euler criterion
      |                     |                 |
 one-dimensional       nested transpose     |
 row partitions        / Fubini [body-green] |
      +---------------------+-----------------+
                            |
                  quadratic reciprocity
```

The critical reusable order is Sum before BitCount, and Repeat before Pow.
Euler's criterion can begin once Pow has congruence transport and the finite
nonzero-residue permutation/product layer is available. Eisenstein's identity
needs Sum append/split and interval encodings but does not need FTA.

## Parser and size audit

The contract test parses every planned endpoint as a closed formula,
round-trips it through the canonical printer, rejects unsafe term
interpolation and binder capture, and compares `BetaAt` and `Product` against
the checked catalog conventions.

| Expanded endpoint | source characters | canonical characters | formula nodes | term nodes |
|---|---:|---:|---:|---:|
| `beta_sum_exists` | 1,020 | 340 | 44 | 106 |
| `beta_sum_functional` | 2,023 | 692 | 88 | 214 |
| `bit_count_bounded` | 1,630 | 443 | 62 | 139 |
| `bit_count_exists` | 1,907 | 528 | 74 | 164 |
| `bit_count_functional` | 3,213 | 878 | 118 | 272 |
| `range_exists` | 263 | 97 | 13 | 28 |
| `repeat_exists` | 245 | 85 | 13 | 24 |
| `power_exists` | 1,813 | 423 | 55 | 132 |
| `power_functional` | 3,611 | 859 | 111 | 266 |
| `power_zero` | 1,823 | 441 | 59 | 137 |
| `power_successor_decompose` | 3,642 | 882 | 114 | 271 |

All initial relation endpoints fit the former 4,000-character interactive
limit. The later checked successor-pair, power-congruence, exponent-addition,
and exponent-multiplication contracts occupy 5,706, 4,274, 7,131, and 7,127
characters, so the synchronized Python/browser ceiling is now 8,192.
Canonical printing remains much smaller, showing that hygienic
descriptive binder names—not proposition complexity—consume most source
space. The ceiling change affects source transport only; certificate objects,
occurrences and depth retain independent limits.

These counts measure target syntax, not certificates. Sum trace existence is
expected to be comparable to the checked product-trace theorem and must be
profiled before adding Count or Pow certificates to a final closure. If proof
nodes become limiting, raise the live ceiling only after time, memory,
recursion, browser replay, and mutation audits; a higher numeric limit does
not repair duplicated dependency subtrees.
