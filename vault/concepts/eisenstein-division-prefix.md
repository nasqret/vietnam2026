# Eisenstein division prefix

The native `DivisionPrefix` relation replaces an informal finite list of
floors with three aligned Gödel-beta prefixes. At every bounded position it
decodes a source value `x`, a quotient `q`, and a remainder `r`, and proves

\[
x=pq+r,\qquad r<p.
\]

The relation expands away before kernel checking; it introduces no primitive
division, remainder, floor, list, or choice operation.

Body-green candidate ladder:

- `beta_division_prefix_extend`: `132` nodes, depth `41`, `94` commands;
- `beta_division_prefix_exists`: `71` nodes, depth `30`, `62` commands.

Exact half-range specialization:

- `beta_scaled_successor_prefix_from_pointwise`: `34/24` nodes/depth;
- `prime_scaled_half_division_prefix_exists`: `71/40`;
- `prime_scaled_half_quotient_sum_exists`: `52/28`.

Constructive division threshold:

- `nonzero_remainder_division_positive_multiple_threshold`: `92` nodes,
  depth `30`, `67` commands;
- readable result: from `n=p*q+r`, `r!=0`, and `r<p`, obtain
  `p*S j<n` iff `S j<=q`;
- exact focused audit: `4/4` in 0.30 seconds under the 60-second CPU cap,
  with no `DNE`.

Scaled remainder nonvanishing:

- `prime_nondivisor_bounded_scaled_remainder_nonzero`: `47/21` nodes/depth;
- `distinct_primes_bounded_scaled_remainder_nonzero`: `45/24`;
- `distinct_primes_own_odd_half_scaled_remainder_nonzero`: `45/28`;
- the generic assumptions are `Prime(p)`, `p` not dividing `q`, `S i<p`, and
  `q*S i=p*d+r`; they imply `r!=0` without assuming `r<p`;
- the distinct-prime wrapper derives nondivisibility, while the corrected
  half wrapper derives `S i<p` from `p=2*k+1` and `i<k`;
- exact focused audit: `4/4` in 0.40 seconds, with registry isolation and no
  `DNE`.

The cross-half variant is false: `p=3`, `k=1`, `q=7`, `h=3`, and `i=2<h`
give `q*S i=7*3=3*7+0`. Thus an index for `q*S i` must be bounded by the
divisor `p`'s own half, not merely by `q`'s half. All three corrected results
are dependency-curried body-only candidates, not recursively closed,
registered, or admitted.

Odd-half quotient bound:

- `odd_half_cross_product_gap`: `160/45` nodes/depth, `13` commands;
- `odd_half_division_quotient_bounded`: `67/29`, `62` commands;
- the latter derives `d<=k` from `p=2*h+1`, `q=2*k+1`, `i<h`, and
  `q*S i=p*d+r`; it requires neither primality nor a remainder condition;
- its combined focused run with the remainder-nonzero suite passes `8/8` in
  0.54 seconds.

Exact initial-segment `BitCount`:

- indicator choice, prefix extension/existence, `AllBits`, and decoded
  semantics: `23/12`, `63/25`, `40/19`, `25/14`, `41/21` nodes/depth;
- exact all-one count, threshold-count functionality, and the final exact
  package: `91/28`, `160/37`, `49/21`;
- the final theorem states that a length-`k` beta prefix marking exactly
  `S j<=q` has `BitCount=q` whenever `q<=k`;
- the focused audit passes `11/11` in 2.09 seconds, pins all eight contracts
  and receipts, and finds no `DNE`.

Both ladders are dependency-curried, unregistered, unadmitted, and not yet
recursively WMI-closed.

Exact finite-sum transport:

- `beta_sum_transport_prefix` reuses one relational partial-sum trace when a
  second beta prefix decodes pointwise to the same bounded entries;
- it has no theorem dependencies and measures `59/29` nodes/depth, `59`
  objects, `58` edges, no reuse, and `44` commands;
- its focused audit passes `3/3`; combined with the initial-segment suite the
  result is `14/14` in 2.20 seconds;
- it contains no `DNE`, does not identify raw beta codes, and remains
  unregistered and unadmitted.

One-dimensional complementary counts:

- `complementary_bit_counts_add_length` proves `n+m=l` for two length-`l`
  `BitCount` prefixes whose decoded pairs are pointwise exactly `(0,1)` or
  `(1,0)`;
- dependencies: [[bit_count_zero]], [[bit_count_succ_decompose]], `le_succ`,
  `le_refl`, and `add_succ_left`;
- receipt: `220/46` nodes/depth, `211` objects, `219` edges, `9` reused
  objects, and `112` commands;
- its focused constructive audit passes `3/3` in 1.47 seconds with no `DNE`;
  it is unregistered and unadmitted.

This handles one matched row only. It does not align the nested row-major and
column-major beta encodings or prove the rectangle transpose/Fubini theorem.

Semantic row equals decoded quotient:

- `eisenstein_row_indicator_prefix_to_initial_segment`: 2 dependencies,
  `78/36` nodes/depth, `55` commands;
- `distinct_odd_prime_row_bit_count_equals_division_quotient`: 5
  dependencies, `95/45`, `79` commands;
- `distinct_odd_prime_row_bit_count_equals_decoded_quotient`: 4 dependencies,
  `111/55`, `96` commands;
- `distinct_odd_prime_semantic_row_equals_decoded_quotient`: 1 dependency,
  `119/72`, `53` commands;
- focused audit: `4/4` in 3.40 seconds; explicit prerequisite integration:
  `27/27` in 5.86 seconds; no `DNE`, `auto`, or `ring`.

This closes the Eisenstein-specific pointwise row-count identification at the
dependency-curried level. All four bodies remain unregistered and unadmitted.

Orientationwise outer-sum equality:

- `distinct_odd_prime_quotient_entry_matches_rectangle`: 1 dependency,
  `104/52` nodes/depth, `58` commands;
- `distinct_odd_prime_quotient_sum_transports_to_rectangle`: 2 dependencies,
  `73/54`, `61` commands;
- `distinct_odd_prime_quotient_sum_equals_rectangle_total`: 2 dependencies,
  `67/51`, `56` commands;
- focused audit: `4/4` in 4.92 seconds; related-stack audit: `19/19` in
  10.71 seconds; no `DNE`, `auto`, or `ring`.

This identifies the quotient `Sum` with the semantic rectangle total. The
uniform theorem can be instantiated again after swapping `p,q` and `h,k`.
All three bodies remain unregistered and unadmitted.

Transposed cell exposure:

- `eisenstein_transposed_decoded_cell_bits_complementary`: 1 dependency,
  `95/33` nodes/depth, `71` commands;
- `eisenstein_transposed_outer_prefix_cell_witness`: 3 dependencies,
  `116/58`, `101` commands;
- their combined focused audit passes `6/6` in 2.08 seconds with no `DNE`.

The first theorem proves decoded `(i,j)` and swapped `(j,i)` bits
complementary. The second opens the existential inner rows from both outer
prefixes and packages those decoded cell witnesses. They are constructive,
unregistered, and unadmitted.

Whole transposed-column construction is now body-green too. Compact receipts
below are `dependencies / commands / nodes / depth / objects / edges / reused`:

- `eisenstein_transposed_outer_column_choices`:
  `2 / 37 / 42 / 26 / 42 / 41 / 0`;
- `eisenstein_transposed_column_prefix_extend`:
  `2 / 55 / 80 / 31 / 80 / 79 / 0`;
- `eisenstein_transposed_column_prefix_exists`:
  `5 / 56 / 64 / 29 / 64 / 63 / 0`;
- `eisenstein_transposed_column_prefix_all_bits`:
  `1 / 48 / 56 / 33 / 56 / 55 / 0`;
- `eisenstein_transposed_column_pointwise_complement`:
  `2 / 64 / 87 / 47 / 87 / 86 / 0`;
- `eisenstein_row_transposed_column_count_partition`:
  `6 / 105 / 117 / 56 / 117 / 116 / 0`.

The provenance design is essential. Each constructed column entry retains
the decoded swapped outer count, an existential inner row code and scale with
the swapped row semantics, that row's `BitCount` witness, and the decoded
inner cell at the fixed `i<h`. Extension preserves this complete package; a
bare beta column cannot satisfy the relation merely by matching bit values.

The strongest endpoint takes an original semantic row with count `n`, the
swapped semantic outer rectangle, and `i<h`; it returns column code/scale
`z,e` and count `m` with the full provenance-carrying prefix,
`BitCount(z,e,k,m)`, and `n+m=k`. Its focused native-PA audit passes `5/5` in
5.05 seconds, pins all contracts, dependencies, hashes, and receipts, and
finds no automation or classical escape. The six bodies are constructive,
dependency-curried, unregistered, unadmitted, and not recursively closed.

Half-rectangle orientation:

- `distinct_odd_prime_half_products_ne`: `72/30`;
- `distinct_odd_prime_half_cell_oriented`: `77/34`;
- `distinct_odd_prime_half_rectangle_oriented`: `53/34`.

Concrete row indicators/counts:

- pointwise bit, append, induction, and specialized choices: `46/29`,
  `71/27`, `58/23`, `53/34`;
- `AllBits`, decoded semantics, and row `BitCount`: `27/16`, `43/23`,
  `63/29`.

Nested outer row-count prefix and rectangle total:

- `distinct_odd_prime_half_row_count_choice`: `39/25`;
- outer append and ordinary-induction existence: `71/27`, `58/23`;
- bounded choices and bounded/full prefix existence: `40/27`, `37/26`,
  `30/23`;
- `eisenstein_rectangle_decoded_row_count`: `43/23`;
- `distinct_odd_prime_half_rectangle_total_exists`: `40/22`.

The outer exact-contract audit passes `4/4` in 2.22 seconds under a strict
60-second process CPU cap. This is dependency-curried candidate evidence, not
recursive WMI closure or admission. The specialization already constructs
exact multiplication-source prefixes and quotient [[beta_sum_exists|sums]],
and distinct primality now orients every lattice cell, constructs each row
count, beta-codes the semantic
row counts over `i<h`, and attaches a native outer `Sum`. Each outer entry
existentially owns an inner row code and `BitCount`; equality of raw beta codes
is not used as equality of represented rows. The separate outer-sum bridge now
identifies this rectangle total with its orientation's quotient/floor sum,
and the transposed-column endpoint proves one fixed row/column partition. The
later Fubini and Gauss--Eisenstein candidates now aggregate these partitions,
identify the two exact quotient sums, and reach the body-green reciprocity
surface.
Nothing in this layer is registered or admitted.

The threshold is also body-only and unregistered. Its scaled-remainder
nonzero premise is discharged when the row index is bounded by the divisor's
own half; the quotient bound and exact initial-segment count are now
body-green as well. Each semantic row count is now pointwise identified with
its decoded division quotient, and outer beta-sum transport plus endpoint
functionality identifies the quotient `Sum` with the semantic total. Swapping
the prime/half parameters gives the other orientation. The transposed-column
ladder now constructs and counts the whole complementary column for each
fixed `i<h`, proving `row_count_i+column_count_i=k`. The nested
two-dimensional transpose/Fubini follow-on is now body-green: it beta-codes
and sums those counts, proves the constructed column sum equals the swapped
outer total, and derives the semantic rectangle identity. The exact quotient
wrapper preserves both decoded systems and proves `Q+U=h*k` at `145/68`
nodes/depth.

Pointwise signed-division parity (`250/61`) and exact finite-sum transport then
prove `Q congruent e (mod 2)` while retaining every beta parameter. The
one-orientation Gauss--Eisenstein package is `5/102/139/67`, the two-prime
package is `4/150/222/77`, and the final same/opposite/combined QR bodies are
`2/46/73/33`, `2/46/73/33`, and `3/65/113/35` in
dependencies/commands/nodes/depth order. See
[[gauss-eisenstein-reciprocity]]. No equality of raw beta codes replaces the
semantic fold argument.

All these later candidates remain dependency-curried, unregistered and
unadmitted; recursive WMI closure and receipt-pinned admission are still
required.

## Links

- [[gauss-eisenstein-reciprocity]]
- [Research design](../../research/arithmetic-library/eisenstein-division-prefix.md)
- [Candidate source](../../peano-lab/py/peano_lab/library/finite_division_prefix_candidate.py)
- [Focused test](../../peano-lab/py/tests/test_finite_division_prefix_candidate.py)
- [Scaled source](../../peano-lab/py/peano_lab/library/eisenstein_scaled_division_candidate.py)
- [Scaled focused test](../../peano-lab/py/tests/test_eisenstein_scaled_division_candidate.py)
- [Division-threshold source](../../peano-lab/py/peano_lab/library/eisenstein_division_threshold_candidate.py)
- [Division-threshold test](../../peano-lab/py/tests/test_eisenstein_division_threshold_candidate.py)
- [Remainder-nonzero source](../../peano-lab/py/peano_lab/library/eisenstein_remainder_nonzero_candidate.py)
- [Remainder-nonzero test](../../peano-lab/py/tests/test_eisenstein_remainder_nonzero_candidate.py)
- [Quotient-bound source](../../peano-lab/py/peano_lab/library/eisenstein_quotient_bound_candidate.py)
- [Quotient-bound test](../../peano-lab/py/tests/test_eisenstein_quotient_bound_candidate.py)
- [Initial-segment count source](../../peano-lab/py/peano_lab/library/eisenstein_initial_segment_count_candidate.py)
- [Initial-segment count test](../../peano-lab/py/tests/test_eisenstein_initial_segment_count_candidate.py)
- [Finite-sum transport source](../../peano-lab/py/peano_lab/library/finite_sum_transport_candidate.py)
- [Finite-sum transport test](../../peano-lab/py/tests/test_finite_sum_transport_candidate.py)
- [Complementary BitCount source](../../peano-lab/py/peano_lab/library/finite_bitcount_complement_candidate.py)
- [Complementary BitCount test](../../peano-lab/py/tests/test_finite_bitcount_complement_candidate.py)
- [Row-quotient bridge source](../../peano-lab/py/peano_lab/library/eisenstein_row_quotient_candidate.py)
- [Row-quotient bridge test](../../peano-lab/py/tests/test_eisenstein_row_quotient_candidate.py)
- [Outer-sum bridge source](../../peano-lab/py/peano_lab/library/eisenstein_outer_sum_bridge_candidate.py)
- [Outer-sum bridge test](../../peano-lab/py/tests/test_eisenstein_outer_sum_bridge_candidate.py)
- [Transposed-cell source](../../peano-lab/py/peano_lab/library/eisenstein_transposed_cell_candidate.py)
- [Transposed-cell test](../../peano-lab/py/tests/test_eisenstein_transposed_cell_candidate.py)
- [Transposed outer-cell source](../../peano-lab/py/peano_lab/library/eisenstein_transposed_outer_cell_candidate.py)
- [Transposed outer-cell test](../../peano-lab/py/tests/test_eisenstein_transposed_outer_cell_candidate.py)
- [Transposed-column source](../../peano-lab/py/peano_lab/library/eisenstein_transposed_column_candidate.py)
- [Transposed-column test](../../peano-lab/py/tests/test_eisenstein_transposed_column_candidate.py)
- [Lattice orientation source](../../peano-lab/py/peano_lab/library/eisenstein_lattice_orientation_candidate.py)
- [Lattice orientation test](../../peano-lab/py/tests/test_eisenstein_lattice_orientation_candidate.py)
- [Row indicator source](../../peano-lab/py/peano_lab/library/eisenstein_row_indicator_candidate.py)
- [Row indicator test](../../peano-lab/py/tests/test_eisenstein_row_indicator_candidate.py)
- [Rectangle-count source](../../peano-lab/py/peano_lab/library/eisenstein_rectangle_count_candidate.py)
- [Rectangle-count test](../../peano-lab/py/tests/test_eisenstein_rectangle_count_candidate.py)
- [[quadratic-reciprocity-moc]]
