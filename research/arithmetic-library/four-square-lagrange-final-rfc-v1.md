# Final constructive Lagrange four-square reduction RFC v1

Status: isolated, dependency-curried candidate proofs. Both prime
representation and the full all-natural Lagrange four-square theorem are
unconditional and independently kernel checked. Intermediate conditional
roots preserve an auditable exact proof decomposition.

Implementation:
[`four_square_lagrange_final_candidate.py`](../../peano-lab/py/peano_lab/library/four_square_lagrange_final_candidate.py).
Focused audit:
[`test_four_square_lagrange_final_candidate.py`](../../peano-lab/py/tests/test_four_square_lagrange_final_candidate.py).

Every prior construction is now discharged:

1. every prime has an actual bounded modular square seed `0<k<p`;
2. quaternion norms multiply constructively for arbitrary coordinates;
3. represented even multipliers descend unconditionally by parity halving;
4. all sixteen centered sign patterns have an integral centered norm quotient;
5. proper prime-bounded odd quotients are nonzero and strictly decreasing;
6. bounded strong multiplier induction constructs a representation of a prime;
7. constructive prime-factor induction passes from all primes to all naturals.

The formerly sole remaining premise, now independently proved for all sixteen
orientation masks, is the odd signed centered quaternion representation
identity:

```text
k≠0, k=2h+1,
p·k = a²+b²+c²+d²,
four witnessed signed centered coordinates e,f,g,j,
k·r = e²+f²+g²+j²

    ⇒ ∃ u v w x, p·r = u²+v²+w²+x².
```

The exact checked endpoints are

```text
four_square_prime_from_odd_signed_quaternion:

odd_signed_centered_representation
    ⇒ ∀ p, Prime(p) → FourSquare(p),

SHA-256: 52fe02b94dec63cb023e60f00c5a6d3d7fd1cfc014a37227dd3cd91090442a04.

four_square_lagrange_from_odd_signed_quaternion:

odd_signed_centered_representation
    ⇒ ∀ n, FourSquare(n).

SHA-256: fbad3ff6a69377d2b3131db1066b174c89fb2e0b23dbeb64c8fc8893a4339241.
```

The independently checked orientation theorem
`four_square_signed_centered_representation` discharges the displayed
premise, yielding the actual unconditional endpoints:

```text
four_square_signed_centered_representation

SHA-256: 58bb112b380e2d614fb63e33d1cd2184abec50bbf6152278105c0796fe539da6.
```

```text
four_square_prime_representation:

∀ p, Prime(p) → ∃ a b c d, p=a²+b²+c²+d²,

SHA-256: 561b591ea074bf6a2d715665afde074b2c6a90f86c08bdbfa4b6b94553a92240.

four_square_lagrange:

∀ n, ∃ a b c d, n=a²+b²+c²+d².

SHA-256: fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5.
```

No premise remains on the universal theorem. Every representation is
constructive, and every proof edge is independently checked in the existing
first-order Heyting arithmetic kernel.
No Alpha or Stable admission is claimed.
