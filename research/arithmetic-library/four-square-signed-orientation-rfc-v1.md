# Constructive signed four-square orientation RFC v1

Status: isolated dependency-curried candidate bodies checked by the unchanged
intuitionistic kernel. Generic quotient endpoints retain their actual
modular-coordinate and norm-identity premises. The complete final centered
quaternion endpoint discharges every one of the sixteen sign choices; it has
no additional orientation or representation hypothesis.

Implementation:
[`four_square_signed_orientation_candidate.py`](../../peano-lab/py/peano_lab/library/four_square_signed_orientation_candidate.py).
Focused audit:
[`test_four_square_signed_orientation_candidate.py`](../../peano-lab/py/tests/test_four_square_signed_orientation_candidate.py).

## Exact represented quotient

The first endpoint checks the exact implication

```text
k ≠ 0
  -> (p*k)*(k*r) = m₀²+m₁²+m₂²+m₃²
  -> k|m₀ -> k|m₁ -> k|m₂ -> k|m₃
  -> exists a b c d. p*r = a²+b²+c²+d².

SHA-256: 63289b259e9f5884a825989865f93bdd52ed7791751ccf970ac9442c4ba73674
```

All four divisor witnesses are extracted constructively, and cancellation of
the nonzero common square factor invokes the separately checked quaternion
quotient layer.

The second endpoint replaces each divisor premise by its actual pair of
first-order conditions

```text
Positiveᵢ ≡ Negativeᵢ (mod k)
AbsoluteDifference(Positiveᵢ, Negativeᵢ, mᵢ).
```

Balanced modular congruence and the signed absolute-coordinate witness yield
the divisor constructively. The theorem is valid for either the ordinary
Hamilton blocks or a checked conjugate orientation; no identity or modular
coordinate balance is manufactured or hidden.

```text
four_square_signed_absolute_block_representation

SHA-256: f11a91f19c5fa3bea6a594438a95930adf6678a502145efd4e048c6b3d034f24
```

## Unconditional signed centered representation

Constructive orientation of each actual centered residue yields an explicit
positive-versus-negative disjunction. Exhaustive intuitionistic elimination
of those four disjunctions selects one of sixteen independently checked
signed-quaternion cases. Five canonical modular block configurations reduce
the cases using simultaneous coordinate permutations, the ordinary Euler
identity, and the genuinely different conjugate identity.

The final checked root is

```text
four_square_signed_centered_representation

SHA-256: 58bb112b380e2d614fb63e33d1cd2184abec50bbf6152278105c0796fe539da6
```

It constructs an actual representation of `p*r` from a nonzero odd
multiplier, an original represented `p*k`, four centered signed remainder
witnesses, and the exact centered norm equation `k*r`. Every required
modular balance and quotient coordinate is proved; no sign pattern is
assumed or omitted.

All predicates expand into `{0,S,+,*,=}`. These candidates do not change
sealed Alpha or Stable membership.
