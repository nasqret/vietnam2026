# Constructive parity-complete four-square multiplier descent RFC v1

Status: isolated, dependency-curried constructive candidates. The even
multiplier branch is unconditional. The odd branch has exactly one visible
remaining premise: representation of its odd signed centered quaternion
quotient.

Implementation:
[`four_square_branch_descent_candidate.py`](../../peano-lab/py/peano_lab/library/four_square_branch_descent_candidate.py).
Focused audit:
[`test_four_square_branch_descent_candidate.py`](../../peano-lab/py/tests/test_four_square_branch_descent_candidate.py).

## Complete even branch

If `k=2h` and `k≠0`, then `h≠0` and `h<k`. The independently checked
unconditional four-square parity-halving theorem gives

```text
FourSquare(p·k) = FourSquare((p·h)·2)
    ⇒ FourSquare(p·h).
```

Consequently every nonzero even represented multiplier has a genuinely
represented, nonzero, strictly smaller successor.

## Precise odd obligation

For `k=2h+1`, constructive division chooses four signed centered magnitudes.
Their squares always produce an actual quotient `k·r=centered_norm`, for all
sixteen sign patterns. The sharp odd half-range estimate proves `r<k`, and
the prime proper-multiplier invariant `1<k<p` proves `r≠0`.

The only additional hypothesis is therefore exactly

```text
odd_signed_centered_representation:

k≠0, k=2h+1,
p·k = a²+b²+c²+d²,
four witnessed signed centered coordinates e,f,g,j,
k·r = e²+f²+g²+j²

    ⇒ FourSquare(p·r).
```

No modular-seed premise, parity-selection premise, strict-inequality premise,
nonzero-quotient premise, or termination premise is hidden in this condition.

## Exact bounded descent

Constructive parity cases combine the two branches into

```text
four_square_bounded_strict_descent_from_odd_signed_quaternion:

odd_signed_centered_representation
    ⇒ ∀ p k,
       Prime(p) → k≠0 → k≠1 → k<p → FourSquare(p·k)
       → ∃ r, r≠0 ∧ r<k ∧ FourSquare(p·r).

SHA-256: 89a33c3a5e637a028493cc776b7fc8e3f8d29558218bf2a5b9de69157dfeb851.
```

The bounded seed and bounded strong multiplier induction are already checked
in separate candidates. Closing the displayed odd signed centered quaternion
representation implication is therefore the exact outstanding step before
unconditional all-natural Lagrange. No Alpha or Stable admission is claimed.
