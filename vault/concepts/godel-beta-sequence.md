---
title: Gödel beta sequence encoding
tags: [peano-arithmetic, sequence, arithmetization, factorization]
---

A finite natural-number sequence can be represented without adding a list sort
to Peano Lab. For code parameters $b,c$, index $i$, and value $x$, define

$$
M(c,i)=1+(i+1)c,
\qquad
\operatorname{At}(b,c,i,x)
\iff x<M(c,i)\land\exists q.\;b=qM(c,i)+x.
$$

All components expand to `0`, `S`, addition, multiplication, equality, and
quantifiers. A second beta sequence records prefix products. Bounded
`[[prime-number]]` conditions and sorted adjacent entries then define a
canonical finite prime factorization.

Codes are not sequence identities: two code pairs may decode the same finite
prefix. Extensional equality therefore compares length and every decoded
bounded entry. Natural [[quotient-and-remainder]] and [[euclids-lemma]] are now
checked. Constructive [[prime_divisor_exists|prime-divisor existence]] is now
checked as well, through [[prime_or_composite]], [[proper_factor_lt]], and
formula-specific bounded descent.

The single-position decoding API is also checked. [[beta_modulus_nonzero]]
records that every modulus is a successor, [[beta_at_self_of_bound]] supplies
the quotient-zero base constructor, and [[beta_at_exists]], [[beta_at_unique]],
and [[beta_at_exists_unique]] prove totality and functionality of the fully
expanded `At` relation. These facts decode one position.
[[beta_at_to_mod_eq]] now connects each directed decoding witness to the
balanced [[arithmetic-congruence]] API. [[mod_eq_bounded_unique]] and
[[mod_eq_to_remainder_decomposition]] prove the reverse direction, exposed for
β values as [[beta_at_of_mod_eq_bound]]. Thus `At(b,c,i,x)` is now equivalent
to the bound on `x` plus congruence of `b` and `x` modulo `M(c,i)`.

The first composition step is now checked. [[binary_crt]] constructs a
solution for two nonzero coprime moduli, and [[binary_crt_beta_pair]]
specializes it to a single code realizing two bounded β values under an
explicit coprimality premise.

Unconditional pairwise coprimality of β moduli is false. With `c=1`,
indices 1 and 4 produce

$$
M(1,1)=3,\qquad M(1,4)=6,
$$

which have common divisor 3. The correct checked theorem is conditional:
[[common_divisor_beta_moduli_divides_gap_times_c]] controls a common divisor
when `j=i+\mathit{gap}`, and [[beta_moduli_coprime_of_gap_dvd]]
proves coprimality when additionally `\mathit{gap}\mid c`.
[[binary_crt_beta_pair_of_gap_dvd]] therefore constructs the two-position code
with no separate coprimality premise.

The other half of the finite-bound strategy is also checked.
[[bounded_common_multiple_step]] and [[bounded_common_multiple_exists]]
construct a nonzero `c` divisible by every positive natural up to a
chosen bound. [[beta_moduli_coprime_of_lt_bounded_common_multiple]] turns this
into ordered coprimality, [[beta_moduli_pairwise_coprime_bounded]] handles both
index orders, and [[bounded_beta_moduli_pairwise_coprime_exists]] packages a
nonzero base for the whole bounded prefix.

The fold algebra is checked as well. [[coprime_mul_left]] and
[[coprime_mul_right]] preserve coprimality under accumulated products,
[[mod_eq_of_mod_eq_multiple]] descends a product-modulus congruence to each
factor, and [[binary_crt_fold_step]] adds one residue while preserving all old
congruences. [[beta_accumulated_product_step]] and
[[beta_crt_prefix_congruence_step]] advance the two invariant components;
[[beta_crt_prefix_invariant_step]] combines them, and
[[bounded_beta_crt_prefix_invariant]] performs the bounded iteration by
ordinary induction. [[bounded_beta_crt_for_existing_code]] then projects a
common witness for residues already decoded from a supplied `BetaAt` code.
Extensionally the supplied code is itself such a witness, so this theorem by
itself is not arbitrary finite-sequence coding or a product trace.

The isolated finite-fold laboratory now also contains
`complementary_bit_counts_add_length`. Given two length-`l` beta prefixes
with native `BitCount` witnesses and pointwise decoded pairs exactly `(0,1)`
or `(1,0)`, it proves `n+m=l`. The constructive body depends on
[[bit_count_zero]], [[bit_count_succ_decompose]], `le_succ`, `le_refl`, and
`add_succ_left`; its 112 commands check at `220/46` nodes/depth, with `211`
objects, `219` edges, and `9` reused objects. Its focused body audit passes
`3/3` in 1.47 seconds with no `DNE`.

This is an unregistered, unadmitted candidate rather than a checked theorem
card. It compares two one-dimensional prefixes at matching indices. It does
not transpose nested beta prefixes or exchange row and column folds.
[Source](../../peano-lab/py/peano_lab/library/finite_bitcount_complement_candidate.py)
· [focused test](../../peano-lab/py/tests/test_finite_bitcount_complement_candidate.py)

Exact outer-sum arithmetic is now available without flattening a nested
encoding. `beta_sum_pointwise_add` proves `n+m=q` for three equal-length
prefixes whose third entries are pointwise sums; its 127-command body is
`195/57` with no reused proof objects. `beta_repeat_sum_exact` evaluates a
length-`l` constant `Repeat(a)` sum as `l*a` at `85/32`, while
`beta_repeat_sum_exists_exact` packages the code and exact trace at `33/21`.
These are body-green, constructive, unregistered candidates.
[Pointwise-add source](../../peano-lab/py/peano_lab/library/finite_sum_pointwise_add_candidate.py)
· [pointwise-add test](../../peano-lab/py/tests/test_finite_sum_pointwise_add_candidate.py)
· [constant-sum source](../../peano-lab/py/peano_lab/library/finite_repeat_sum_candidate.py)
· [constant-sum test](../../peano-lab/py/tests/test_finite_repeat_sum_candidate.py)

The [[eisenstein-division-prefix|Eisenstein client]] now has a separate
four-body row-quotient bridge: semantic row `BitCount` witnesses are
identified pointwise with quotients decoded by the aligned division prefix.
The final two receipts are `111/55` and `119/72` nodes/depth. Three follow-on
bodies at `104/52`, `73/54`, and `67/51` now instantiate exact beta-sum
transport and identify the quotient-sum and semantic rectangle-total
endpoints; the same theorem applies under the swapped orientation.
[Source](../../peano-lab/py/peano_lab/library/eisenstein_row_quotient_candidate.py)
· [focused test](../../peano-lab/py/tests/test_eisenstein_row_quotient_candidate.py)
· [outer-sum source](../../peano-lab/py/peano_lab/library/eisenstein_outer_sum_bridge_candidate.py)
· [outer-sum test](../../peano-lab/py/tests/test_eisenstein_outer_sum_bridge_candidate.py)

Cellwise transpose exposure is body-green too: one body at `95/33` proves
decoded `(i,j)` and `(j,i)` bits complementary, and a second at `116/58`
opens the inner rows from two outer prefixes and packages that fact. These
are still one-cell witnesses, not a nested two-dimensional Fubini theorem.
[Cell source](../../peano-lab/py/peano_lab/library/eisenstein_transposed_cell_candidate.py)
· [cell test](../../peano-lab/py/tests/test_eisenstein_transposed_cell_candidate.py)
· [outer-cell source](../../peano-lab/py/peano_lab/library/eisenstein_transposed_outer_cell_candidate.py)
· [outer-cell test](../../peano-lab/py/tests/test_eisenstein_transposed_outer_cell_candidate.py)

A six-body client ladder now beta-codes a complete fixed-index column from
the swapped outer rectangle while retaining semantic provenance. The receipts
`dependencies / commands / nodes / depth / objects / edges / reused` are:

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

Every decoded column entry retains the swapped outer decode, the existential
inner row code/scale and row semantics, that row's `BitCount`, and the inner
cell decode. The strongest endpoint therefore returns an actual semantic
column code `z,e`, its `BitCount m`, and `n+m=k` for an original semantic row
of count `n`; it is not a provenance-free beta-code existence claim. The
focused constructive audit passes `5/5` in 5.05 seconds and pins contracts,
dependencies, hashes and receipts. The candidates remain unregistered and
unadmitted.
[Column source](../../peano-lab/py/peano_lab/library/eisenstein_transposed_column_candidate.py)
· [column test](../../peano-lab/py/tests/test_eisenstein_transposed_column_candidate.py)

The follow-on now closes the nested Fubini gate at the body-green level. It
encodes and sums these column counts over all `i<h`, retargets their semantic
provenance through the width induction, identifies the resulting sum
extensionally with the swapped outer total, and folds `n_i+m_i=k` to obtain
the semantic rectangle identity. The universal body is `264/65` nodes/depth
and the final rectangle identity is `65/37`.

An exact quotient wrapper preserves both division and outer-count beta
systems and concludes `Q+U=h*k` at `145/68`. This is the intended use of beta
codes here: witnesses and decoded semantics remain visible until the final
natural equality. The new candidates are dependency-curried, unregistered
and unadmitted; recursive WMI closure remains separate.

Separately, the later checked factorization tranche closes the finite-product
infrastructure gap described earlier on this page. An exclusive-prefix
cross-base invariant supports finite recoding and one-value append; an exact
second β code records prefix products; Product existence and functionality,
zero/successor decomposition, append, and prefix transport form the finite
product API. Greatest-prime-divisor descent and canonical append preserve
`AllPrime` and `Sorted`. Existence then follows by strengthened descent, and
uniqueness follows by sorted last-factor matching and cancellation.

At this integration checkpoint, factorization existence checks at 43,973
nodes/depth 98, uniqueness at 29,789/depth 82, and the combined
[[fundamental-theorem-of-arithmetic|FTA]] at 73,767 nodes/depth 99 with 2,184
self-contained Cuts. The exact FTA certificate SHA-256 is
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It passes the 500,000-occurrence/100,000-object/depth-256 live/use gate using
only PA1–PA6 and
induction and no DNE. Runtime integration is complete.

None of these relations is a trusted primitive. Peano Lab still has no list
type, and uniqueness compares decoded bounded entries rather than raw β-code
identity. [[constructive-prime-unboundedness|Prime unboundedness]] is checked
independently of this encoding.

## Related

[[fundamental-theorem-of-arithmetic]] · [[trusted-kernel]] ·
[[arithmetic-library-moc]]
