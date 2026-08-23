# Constructive four-square Euler cancellation RFC v1

Status: the complete unconditional eight-variable Euler identity and its
constructive four-square multiplicative closure are independently kernel
checked as isolated, dependency-curried candidate bodies. No candidate is
admitted to Alpha or Stable; the universal Lagrange theorem requires a
separate prime-representation argument and is not asserted by this module.

Implementation:
[`four_square_euler_candidate.py`](../../peano-lab/py/peano_lab/library/four_square_euler_candidate.py).
Focused audit:
[`test_four_square_euler_candidate.py`](../../peano-lab/py/tests/test_four_square_euler_candidate.py).

The frozen signed-coordinate foundation already supplies four absolute
Hamilton-coordinate magnitudes and exact natural balances

```text
P_i*P_i + N_i*N_i = m_i*m_i + (P_i*N_i + N_i*P_i).
```

This isolated continuation proves all twelve genuinely necessary mixed
product cancellations, in six independently checked coordinate-pair blocks;
aggregates all four signed balances; and constructively cancels their common
cross-term correction. It also expands the complete eight-variable norm
product into its sixteen exact squared coordinate products. The formerly
missing global compensation is now an unconditional checked theorem:

```text
four_square_euler_global_compensation:

norm(a,b,c,d)*norm(e,f,g,h) + sum_i(P_i*N_i+N_i*P_i)
  = sum_i(P_i*P_i+N_i*N_i)

SHA-256: 2630c8308d7c3cd5c055381f03903acd00770259dd3a4752459c9bf34a3245d5

therefore

four_square_euler_quaternion:

norm(a,b,c,d)*norm(e,f,g,h) = sum_i(m_i*m_i)

SHA-256: 1ce5e34bebbf29675196c766e27edd972d8d6b151d44f63442cad2441f602a65
```

The additive proof is deliberately factored into bounded six-, nine-,
twelve-, and sixteen-entry permutation lemmas. Their scripts are generated
deterministically as ordinary `trans`, `congr`, associativity, commutativity,
and adjacent-swap steps; no global AC search or ring normalizer is trusted.
Three-term square expansions then separate all sixteen diagonal monomials
from the twelve symmetric mixed blocks. Twelve checked crossed-factor swaps
identify those mixed blocks with the complete signed correction.

Canonical signed-balance totality finally supplies four natural magnitudes,
giving both unconditional existential endpoints:

```text
four_square_euler_four_square_product_total
  SHA-256: edaf2a69b3a80996d5f5a0505639db5607e3fe9d8230cf6375f46fb55e89cecc

four_square_euler_representations_closed_under_multiplication
  SHA-256: e93fd4446e4dcea37220f01a13d55d548456af0c0cfb445b4ce2fe7eebccce52
```

Every statement expands into the unchanged first-order natural language
`{0,S,+,*,=}`. No subtraction, classical axiom, registry modification, or
release-evidence change is used.
