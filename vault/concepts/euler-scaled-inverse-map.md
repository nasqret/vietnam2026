# Euler scaled-inverse map

For prime `p` and a nonzero bounded target `a`, the relation

\[
I_{p,a}(x,y)\;:\Longleftrightarrow\;
0<x,y<p\ \land\ xy\equiv a\pmod p
\]

is functional, symmetric, and involutive. Its fixed points are exactly the
bounded square roots of `a`; therefore `~QRes(p,a)` makes it fixed-point-free
constructively.

The ten pointwise candidates are now followed by a beta-coded full map on
sources `1,...,p-1`:

- `prime_scaled_inverse_prefix_extend`: `105/36` nodes/depth;
- `prime_scaled_inverse_prefix_exists_bounded`: `81/33`;
- `prime_scaled_inverse_prefix_exists`: `40/23`.

Decoded extensional layer:

- `scaled_inverse_prefix_entry_sound`: `58/25`;
- `scaled_inverse_prefix_extensional`: `54/26`;
- `scaled_inverse_prefix_no_fixed_of_not_qres`: `36/27`;
- `scaled_inverse_prefix_mate_predecessor`: `67/36`;
- `scaled_inverse_prefix_involutive`: `91/39`.
- `scaled_inverse_prefix_injective`: `77/36`.

The focused test passes `4/4` under a strict 60-second process CPU cap. These
are isolated dependency-curried bodies, not recursive closure or admission.
Decoded extensionality and involution are now body-green. The generic product
comparison is also body-green:

- `beta_adjacent_target_pairs_product_power`: `171/47` nodes/depth, 118
  commands, `4/4` focused audit in 1.71 seconds.

At that checkpoint the next dependency was fixed-point-free two-cycle
ordering of the scaled prefix; the later iteration and endpoint layers below
now close both the ordering and product comparison. None of these candidates
is recursively closed or admitted.

The quadratic-residue branch is separately body-green:

- `mod_eq_zero_to_dvd_nonzero`: `48/18`;
- `quadratic_residue_half_power_mod_one`: `148/39`, 136 commands.

It proves `QRes(p,a) -> a^h == 1 (mod p)` for `p=2*h+1`, prime `p`, and
`p` not dividing `a`, using only relational powers and Fermat. Its focused
audit passes `4/4` in 2.11 seconds. The nonresidue direction and full Euler
equivalence were still open at that checkpoint; the bounded nonresidue,
bounded equivalence, and arbitrary-representative layers are completed below.

One fixed-point-free orbit can now be appended correctly. Because the scaled
map stores `S j`, the Euler order uses an explicit shifted-closure relation:

- `scaled_orbit_closed_unused_mate`: `34/20`;
- `beta_prefix_append_two_scaled_orbit_closed`: `184/40`;
- `scaled_inverse_prefix_choose_omitted_orbit`: `107/38`;
- `scaled_inverse_pair_order_choose_append`: `190/52`.

The `3/3` no-DNE audit passes in 2.78 seconds. The follow-on balanced
iteration and coverage layer is body-green too:

- zero shifted closure/history and zero state: `23/19`, `19/15`, `49/18`;
- history append and one-orbit state step: `114/31`, `125/40`;
- balance and strict-prefix arithmetic: `80/24`, `40/15`;
- paired iteration, terminal package, and terminal coverage: `155/39`,
  `41/25`, `64/26`.

Its exact dependency-curried audit passes `4/4` in 4.72 seconds with a
60-second CPU cap per body and no `DNE`. All ten candidates remain
unregistered and unadmitted. The endpoint layer now closes successor lifting,
adjacent-history product alignment, and the bounded nonresidue implication;
recursive WMI closure remains.

Bounded nonresidue endpoint:

- `scaled_pair_order_successor_lift_adjacent_targets`: 3 dependencies,
  `132/39` nodes/depth, `115` commands;
- `scaled_pair_order_successor_lift_product_is_factorial`: 5 dependencies,
  `144/45`, `82` commands;
- `scaled_pair_order_terminal_power_mod_predecessor`: 9 dependencies,
  `136/52`, `114` commands;
- `scaled_inverse_nonresidue_half_power_mod_predecessor`: 2 dependencies,
  `61/34`, `46` commands;
- `quadratic_nonresidue_half_power_mod_predecessor`: 2 dependencies,
  `49/30`, `37` commands.

For `p=S n`, prime `p`, `n=h+h`, and reduced `0<a<p`, the last theorem proves

\[
\neg QRes(p,a)\land Pow(a,h,A)\Longrightarrow A\equiv n=p-1\pmod p.
\]

The focused audit passes `4/4` in 4.39 seconds, and the endpoint with its
related prerequisites passes `16/16` in 12.19 seconds. The contracts are
fully expanded constructive PA; the bodies contain no `DNE` and remain
unregistered and unadmitted. The terminal product/sign gap is closed.

The complete bounded Euler package is body-green too. Its seven candidates
are `bounded_nonzero_not_divides` (`20/13`),
`double_predecessor_ne_one` (`65/19`),
`odd_prime_one_not_mod_predecessor` (`56/25`),
`bounded_euler_criterion_dichotomy` (`120/39`),
`bounded_euler_criterion_residue_iff` (`92/30`),
`bounded_euler_criterion_nonresidue_iff` (`91/37`), and
`bounded_euler_criterion_complete` (`80/31`). For reduced `0<a<p`, they prove
both `QRes(p,a) <-> A == 1` and `~QRes(p,a) <-> A == p-1`. The focused audit
passes `4/4` in 1.67 seconds and the combined bounded stack passes `12/12` in
7.62 seconds, constructively and without registration or admission.

The arbitrary-representative package is body-green too. It first proves the
three reusable bridges

- `nondivisor_canonical_remainder_exists`: `p!=0` and `p` not dividing `a`
  give `r!=0`, `r<p`, and `a==r (mod p)`; receipt
  `3/39/49/20/49/48/0` (dependencies/commands/nodes/depth/objects/edges/reuse);
- `quadratic_residue_mod_equiv`: congruent representatives have equivalent
  `QRes` status; receipt `2/31/38/17/38/37/0`;
- `pow_congruent_base_witness`: a congruent base has a relational power `R`
  with `A==R (mod p)`; receipt `2/25/29/22/29/28/0`.

The endpoint bodies `arbitrary_euler_criterion_residue_iff`,
`arbitrary_euler_criterion_nonresidue_iff`, and
`arbitrary_euler_criterion_complete` have receipts
`7/92/140/36/140/139/0`, `7/98/146/37/146/145/0`, and
`2/33/75/29/75/74/0`. Thus for `p=S n`, prime `p`, `p` not dividing arbitrary
`a`, `n=h+h`, and `Pow(a,h,A)`, native PA proves

\[
QRes(p,a)\Longleftrightarrow A\equiv1\pmod p,
\qquad
\neg QRes(p,a)\Longleftrightarrow A\equiv n=p-1\pmod p.
\]

The focused audit pins six statement hashes and passes `4/4` in 2.04 seconds;
the combined Euler selection passes `16/16` in 9.96 seconds. The scripts use
no `DNE`, classical reasoning, `sorry`, `auto`, or `ring`. They remain
dependency-curried, unregistered, recursively unclosed, and unadmitted.

The remaining Euler gates are recursive WMI closure, mutations, and a
separate receipt-pinned admission replay.

## Links

- [Research design](../../research/arithmetic-library/euler-scaled-inverse.md)
- [Pointwise source](../../peano-lab/py/peano_lab/library/euler_scaled_inverse_candidate.py)
- [Prefix source](../../peano-lab/py/peano_lab/library/euler_scaled_inverse_prefix_candidate.py)
- [Focused prefix test](../../peano-lab/py/tests/test_euler_scaled_inverse_prefix_candidate.py)
- [Extensional source](../../peano-lab/py/peano_lab/library/euler_scaled_inverse_prefix_extensional_candidate.py)
- [Extensional test](../../peano-lab/py/tests/test_euler_scaled_inverse_prefix_extensional_candidate.py)
- [Pair-product source](../../peano-lab/py/peano_lab/library/euler_pair_product_candidate.py)
- [Pair-product test](../../peano-lab/py/tests/test_euler_pair_product_candidate.py)
- [Residue-branch source](../../peano-lab/py/peano_lab/library/euler_criterion_residue_candidate.py)
- [Residue-branch test](../../peano-lab/py/tests/test_euler_criterion_residue_candidate.py)
- [Complete bounded Euler source](../../peano-lab/py/peano_lab/library/euler_criterion_bounded_candidate.py)
- [Complete bounded Euler test](../../peano-lab/py/tests/test_euler_criterion_bounded_candidate.py)
- [Arbitrary-representative Euler source](../../peano-lab/py/peano_lab/library/euler_criterion_arbitrary_candidate.py)
- [Arbitrary-representative Euler test](../../peano-lab/py/tests/test_euler_criterion_arbitrary_candidate.py)
- [Shifted PairOrder source](../../peano-lab/py/peano_lab/library/euler_scaled_pair_order_entrance_candidate.py)
- [Shifted PairOrder test](../../peano-lab/py/tests/test_euler_scaled_pair_order_entrance_candidate.py)
- [PairOrder iteration source](../../peano-lab/py/peano_lab/library/euler_scaled_pair_order_iteration_candidate.py)
- [PairOrder iteration test](../../peano-lab/py/tests/test_euler_scaled_pair_order_iteration_candidate.py)
- [Nonresidue endpoint source](../../peano-lab/py/peano_lab/library/euler_nonresidue_endpoint_candidate.py)
- [Nonresidue endpoint test](../../peano-lab/py/tests/test_euler_nonresidue_endpoint_candidate.py)
- [[quadratic-reciprocity-moc]]
