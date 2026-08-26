# Constructive four-square prime reduction RFC v1

Status: isolated, dependency-curried candidate bodies only. The complete
eight-variable Euler identity and four-square multiplicative closure are
available from the separate checked Euler tranche. This tranche proves the
exact reduction of universal Lagrange to a single missing prime family; it is
not an unconditional proof of universal Lagrange.

Implementation:
[`four_square_lagrange_candidate.py`](../../peano-lab/py/peano_lab/library/four_square_lagrange_candidate.py).
Focused audit:
[`test_four_square_lagrange_candidate.py`](../../peano-lab/py/tests/test_four_square_lagrange_candidate.py).

## Checked constructive seeds

The module supplies independently checked witnesses for

```text
0  = 0² + 0² + 0² + 0²
1  = 1² + 0² + 0² + 0²
2  = 1² + 1² + 0² + 0²
3  = 1² + 1² + 1² + 0²
7  = 2² + 1² + 1² + 1²
11 = 3² + 1² + 1² + 0².
```

Every already-constructed two-square representation embeds into four squares
by adjoining two zeros. Consequently the exceptional prime two and every
prime congruent to one modulo four already have explicit witnesses. The
modular seed bridge additionally proves that every witnessed equation

```text
x² + y² + 1 = p·k
```

represents the multiple `p·k` as four squares; the special case `k = 1`
represents the prime itself. The separate
[`four-square-residue-intersection-rfc-v1.md`](four-square-residue-intersection-rfc-v1.md)
tranche now constructively supplies such seeds for every prime. The bounded
strict descent and complete unconditional universal theorem are supplied by
[`four-square-lagrange-final-rfc-v1.md`](four-square-lagrange-final-rfc-v1.md);
they are not silently asserted by this earlier reduction tranche.

## Kernel-checked prime-factor descent

The theorem

```text
four_square_lagrange_bounded_from_primes

SHA-256: efd0f14a1f72b0fc99e177cf2d85119277ef11f5d7e3ba787a05b68aba4bd049
```

proves, by bounded natural induction, that a nonzero `n` below a bound is a
sum of four natural squares whenever every prime has such a representation.
The successor step selects an actual prime divisor, proves that its quotient
is nonzero and strictly smaller, applies the induction hypothesis, and then
uses the unconditional checked Euler multiplicative-closure theorem.

Zero is handled separately and constructively in

```text
four_square_lagrange_from_all_primes

SHA-256: d373edd2a0775d7a1c37579e03decd1b958bc1c0337d17e255c752552c1a9a31.
```

Constructive prime residue trichotomy removes the already solved `p = 2` and
`p ≡ 1 (mod 4)` cases. The exact remaining implication and equivalence are

```text
four_square_lagrange_from_three_mod_four_primes

SHA-256: 3fd036aef0aeaeee2a01875484a2071f47c484538e3e37907398b410e6222d47

four_square_lagrange_iff_three_mod_four_primes

SHA-256: 67c703fb011e9abe5c79cb74d1eef56d754da9f9313053675e8f783f79dc238c.
```

Thus the remaining mathematical task is precisely

```text
∀ p, Prime(p) ∧ p ≡ 3 (mod 4)
  → ∃ a b c d, p = a² + b² + c² + d².
```

All relation notation expands into the unchanged first-order natural
language `{0,S,+,*,=}`. Every conditional premise remains explicit in the
checked formula; no classical axiom, subtraction, ring tactic, or trusted
search is used. No Alpha or Stable admission is claimed.
