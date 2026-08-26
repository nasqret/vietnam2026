# RFC FTSP01: constructive canonical prime-pairing predecessors

**Status:** isolated dependency-curried kernel candidates;
not Alpha or Stable admission. The complete two-square iff criterion is
proved constructively below, including an explicit zero boundary.

## Checked prime and valuation predecessors

1. `prime_divisor_of_prime_forces_equality` proves that a prime divisor of
   another prime is the same natural prime.
2. `distinct_prime_power_valuation_zero` proves that the valuation of a
   distinct prime factor is exactly zero.
3. `positive_double_at_least_two` supplies the explicit witness that a
   positive doubled exponent is at least two.
4. `even_positive_prime_valuation_has_square_divisor` turns a witnessed even
   valuation together with prime divisibility into an actual prime-square
   divisor of the nonzero number.
5. `prime_square_divisibility_forces_suffix_prime_divisor` proves that if
   `n = r*p` and `p*p` divides `n`, then `p` also divides the remaining
   decoded-prefix product `r`.
6. `beta_sorted_prime_prefix_divisor_equals_bounded_last` combines the
   canonical prime-occurrence and sorted-maximum theorems to identify the
   final decoded factor when it is bounded by a prime divisor.
7. `even_valuation_sorted_terminal_prime_has_equal_predecessor` proves the
   actual canonical adjacency bridge: in a sorted all-prime beta product,
   a terminal prime with witnessed even valuation must have the same prime
   as its immediately preceding decoded factor.
8. `pairing_double_equals_two_mul` converts additive half-witnesses to the
   existing native multiplicative parity surface.
9. `even_double_sum_reflects_even_tail` proves constructive reverse parity
   transport: if an even block plus a tail is even, the tail is even.
10. `distinct_prime_factor_even_valuation_reflects_prefix` shows that
    stripping a distinct prime singleton preserves an even prime valuation.
11. `square_factor_even_valuation_reflects_cofactor` proves the corresponding
    parity inheritance when an arbitrary nonzero natural square is removed.
12. `three_mod_four_number_not_equal_represented` separates every bad
    residue-class number from every explicitly represented number.
13. `all_bad_prime_even_valuations_strip_represented_prime` transports the
    entire universally quantified bad-prime parity invariant through removal
    of one represented prime singleton.
14. `all_bad_prime_even_valuations_strip_square_factor` transports the same
    universal invariant through removal of an arbitrary nonzero square block.
15. `all_bad_prime_even_valuation_value_eq_transport` preserves the complete
    universally quantified invariant under equality of its valued natural.
16. `prime_mod_four_good_or_three` groups constructive prime residue
    trichotomy into the represented-prime and bad-prime alternatives.
17. `all_bad_prime_even_two_square_sufficiency_bounded` proves the missing
    sufficiency direction by ordinary constructive induction on an explicit
    natural bound: good represented primes are removed singly, and bad primes
    with even valuation are removed as witnessed prime-square blocks.
18. `positive_number_with_even_bad_prime_valuations_is_two_square` removes
    the auxiliary induction bound and constructs the actual representation.
19. `nonzero_two_square_iff_even_three_mod_four_prime_valuations` combines
    sufficiency with the independently checked necessity direction.
20. `two_square_iff_zero_or_even_three_mod_four_prime_valuations` handles
    zero separately and states the full all-natural classification.

All valuation, power, divisibility, primality, and beta-list surfaces are
expanded before parsing into the unchanged first-order language
`{0,S,+,*,=}`. Each statement is checked as an intuitionistic proof with
only its exact explicitly curried dependencies.

## Complete constructive classification and evidence boundary

The final proof takes the shorter route of bounded induction directly on the
natural value; it therefore needs neither a beta-list recoding operation nor
the uniqueness of a prime factorization. For a nonzero nonunit value, the
checked prime-divisor theorem supplies a prime factor. A represented prime
factor is removed singly, while a three-modulo-four prime with even valuation
supplies an actual prime-square divisor. In both cases the quotient is
strictly smaller and retains the full bad-prime even-valuation invariant.

The resulting exact criterion is:

```text
n = a*a+b*b
  iff
n = 0, or n != 0 and every three-modulo-four prime has even valuation at n.
```

The zero case is explicit because zero has no asserted prime valuation.
This is a complete two-square iff criterion at the isolated candidate-body
evidence level; it is still not Alpha or Stable admission.

The nonzero criterion has exact statement SHA-256
`025b1283e41d88b9def44672ffdd033d1055b84ccf43bc6af06c093dc90dceac`.
The complete zero-inclusive all-natural criterion has exact statement
SHA-256
`4c39da833a313bab5ae810215dae5bbc9cc78ea951fe97fb177c36a5347cecd5`.

Run the bounded focused checks with:

```text
cd peano-lab/py
python3 -m pytest -q --tb=line tests/test_fermat_two_squares_pairing_candidate.py
```
