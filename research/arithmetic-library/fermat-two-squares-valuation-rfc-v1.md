# RFC FTSV01: constructive two-square valuation and square extraction

**Status:** isolated, dependency-curried candidate bodies;
not Alpha or Stable admission and not the full all-integer iff classification.

## Zero is an explicit separate boundary

The natural number zero is represented by `0*0+0*0`, but
zero has no asserted prime valuation in this tranche. The independently
checked rows

1. `two_square_self_square_zero_reflects`;
2. `two_square_norm_zero_iff_coordinates_zero`;

establish exactly that a two-square norm vanishes if and only if both
coordinates vanish. Every theorem about prime valuations or their descent
therefore states the relevant nonzero assumptions explicitly.

## Exact square valuations and constructive parity transport

`prime_power_valuation_square_even` derives, for every prime `p` and every
nonzero natural `z`,

```text
v_p(z*z) = v_p(z) + v_p(z).
```

The formula uses the existing beta-expanded `PowerVal` graph, not an oracle or
an additional object-language valuation symbol. It is a direct,
dependency-curried use of the already checked `prime_power_valuation_mul`
theorem.

`prime_power_valuation_square_factor_shift` proves the stronger exact
nonzero square-factor transport

```text
v_p((z*z)*n) = (v_p(z)+v_p(z)) + v_p(n),  z != 0, n != 0.
```

`prime_power_valuation_square_factor_preserves_evenness` then constructs an
explicit half-witness for the new exponent whenever the quotient exponent is
already witnessed even.

## Coordinate division and exact prime-square extraction

The following bounded checked rows provide ordinary native factor witnesses:

3. `two_square_common_factor_norm_identity` proves
   `(p*u)^2+(p*v)^2 = p^2*(u^2+v^2)`;
4. `two_square_common_divisor_extracts_squared_factor` constructs both
   coordinate quotients and their exact represented norm;
5. `two_square_common_squared_factor_divides_norm` gives the corresponding
   explicit `p^2` divisibility witness;
6. `two_square_representation_preserved_by_square_factor` proves that
   multiplying a represented natural by any square preserves representation;
7. `three_mod_four_prime_two_square_norm_extracts_squared_factor` combines the
   independently checked three-modulo-four coordinate-divisibility theorem
   with the exact represented `p^2` quotient;
8. `three_mod_four_prime_nonzero_two_square_norm_extracts_nonzero_quotient`
   preserves the nonzero domain through that extraction.

For a prime `p = 4*k+3`, the resulting checked constructive bridge is

```text
p | a*a+b*b
  => exists u v.
       a = p*u /\ b = p*v /\
       a*a+b*b = (p*p)*(u*u+v*v).
```

On the separately stated nonzero domain, `u*u+v*v` is nonzero as well.

`three_mod_four_prime_nonzero_norm_positive_valuation_extracts` also starts
directly from a witnessed positive valuation, deriving prime divisibility and
then the same nonzero represented prime-square quotient.
`prime_square_times_nonzero_strictly_increases` proves that this quotient is
strictly smaller than the original norm, giving an explicit well-founded
descent measure without silently assuming it.

## Full constructive necessity direction

`three_mod_four_prime_two_square_norm_valuation_even_bounded` performs
ordinary natural induction on an explicit bound for the represented norm.
For a zero valuation it constructs the half-witness zero. For a positive
valuation it extracts the represented nonzero prime-square quotient, proves
that the quotient lies below the predecessor bound, invokes the induction
hypothesis there, and transports its evenness through the exact square-factor
valuation identity.

`three_mod_four_prime_two_square_norm_valuation_even` removes the artificial
induction bound by instantiating it with the norm itself.
`three_mod_four_prime_represented_nonzero_valuation_even` then states the
actual all-represented-integers necessity direction:

```text
n != 0 /\ n = a*a+b*b /\ Prime(p) /\ p = 4*k+3 /\ PowerVal(p,n,e)
  => exists h. e = h+h.
```

The existential half is a native constructive witness; no classical parity
argument, unbounded search, or external valuation oracle is used.

## Integration with the completed classification

The necessity direction in this tranche is fully checked, including its
well-founded iteration for each individual three-modulo-four prime. The
separate pairing-and-descent tranche now proves sufficiency by direct bounded
induction on the natural value, avoiding any need for a
prime-factorization-to-valuation equivalence. Combining the two gives the
exact nonzero and zero-inclusive complete classification endpoints

```text
nonzero_two_square_iff_even_three_mod_four_prime_valuations
two_square_iff_zero_or_even_three_mod_four_prime_valuations
```

This valuation module by itself is not the full all-integer iff
classification; the combined theorem is complete at the candidate-body
layer. No Alpha or Stable admission is claimed.

Run the focused checks with:

```text
cd peano-lab/py
python3 -m pytest -q --tb=line tests/test_fermat_two_squares_valuation_candidate.py
```
