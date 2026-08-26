# Sixteen constructive signed quaternion orientation cases RFC v1

Status: isolated dependency-curried constructive candidates. Every signed
orientation has its own independently kernel-checked four-square quotient.

Implementation:
[`four_square_signed_cases_candidate.py`](../../peano-lab/py/peano_lab/library/four_square_signed_cases_candidate.py).
Focused audit:
[`test_four_square_signed_cases_candidate.py`](../../peano-lab/py/tests/test_four_square_signed_cases_candidate.py).

The four centered coordinates independently satisfy one of two balanced
natural congruences:

```text
positive: a ≡ e (mod k),
negative: a+e ≡ 0 (mod k).
```

Bit `i` of a mask records the negative orientation of coordinate `i`.
Simultaneous permutations of original coordinates and their paired centers
reduce all sixteen masks to five exact canonical modular-block surfaces:

1. no negative signs: conjugate all-positive identity;
2. four negative signs: conjugate all-negative identity;
3. two negative signs: conjugate mixed identity with reversed centers;
4. one negative sign: natural Hamilton identity with the negative first;
5. three negative signs: natural Hamilton identity with the positive first.

The exact case endpoints range from
`four_square_signed_orientation_mask_00` to
`four_square_signed_orientation_mask_15`. Each states

```text
k≠0,
k=2h+1,
p·k = a²+b²+c²+d²,
the four congruences selected by its mask,
k·r = e²+f²+g²+j²

    ⇒ ∃ u v w x, p·r=u²+v²+w²+x².
```

All coordinate absolute values are constructed, each modular block supplies
actual divisibility, and the exact common square factor is constructively
canceled. No Alpha or Stable admission is claimed.
