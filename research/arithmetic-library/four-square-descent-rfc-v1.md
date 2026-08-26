# Constructive quaternion multiplier descent RFC v1

Status: isolated, dependency-curried candidate bodies only. The quotient
arithmetic, explicit centered-quaternion descent step, and terminating
multiplier induction are kernel checked. The final endpoint retains its
modular-seed and strict-step hypotheses and therefore does not prove universal Lagrange unconditionally.

Implementation:
[`four_square_descent_candidate.py`](../../peano-lab/py/peano_lab/library/four_square_descent_candidate.py).
Focused audit:
[`test_four_square_descent_candidate.py`](../../peano-lab/py/tests/test_four_square_descent_candidate.py).

## Exact checked quaternion quotient

For a nonzero multiplier `k`, the elementary product rearrangement and
coordinate-wise square factoring establish

```text
(p·k)(k·r) = k²(p·r),

(k·u)² + (k·v)² + (k·w)² + (k·x)²
  = k²(u² + v² + w² + x²).
```

Nonzero square factors cancel using the already checked constructive
multiplicative-cancellation theorem. Consequently an ordinary quaternion
identity whose four absolute output coordinates are divisible by `k` gives
the exact quotient

```text
four_square_descent_quaternion_quotient:

p·k = a²+b²+c²+d²,
k·r = e²+f²+g²+h²,
|Hamilton_i(a,b,c,d,e,f,g,h)| = k·q_i

    ⇒ p·r = q_0² + q_1² + q_2² + q_3².

SHA-256: 81d988b1cd0dbd5c7532707f9ef48b75fb8192190037ae04406c758e55fbe379.
```

The absolute-coordinate conditions are expanded disjunctions in the
first-order natural language, not trusted signed or quaternion primitives.
If also `r ≠ 0` and `r < k`, the next checked theorem constructs the actual
strictly smaller represented prime multiple:

```text
four_square_descent_strict_step_from_centered_quaternion

SHA-256: 360a0d489f5acec54775453e7d9e94d1af030ae3648be5ae1a74609f6e95811c.
```

The centered-coordinate choices themselves are now also checked. Division by
any nonzero modulus produces a remainder and its complement, constructive
total order chooses the smaller, and the selected magnitude `m` satisfies

```text
m + m ≤ k,

either  n = k·q + m
or      n + m = k·q.
```

`four_square_descent_centered_four_remainders_exist` applies that construction
independently to all four quaternion coordinates. The separate checked lemma
`four_square_descent_norm_bound_forces_smaller_multiplier` proves that
`k·r = centered_norm < k²` necessarily implies `r < k`.

For odd `k = 2h+1`, the sharp half-range estimate is also fully checked:

```text
m + m ≤ 2h+1  ⇒  m ≤ h.
```

Four applications, monotonicity of natural squaring, constructive addition
of weak inequalities, and `(2h)² < (2h+1)²` give the unconditional endpoint

```text
four_square_descent_odd_centered_norm_strict:

e,f,g,j centered modulo k = 2h+1

    ⇒ e² + f² + g² + j² < k².
```

Thus strict decrease for odd multipliers is already proved as soon as the
signed-quaternion integrality certificate supplies `k·r` equal to this norm.

The proper-multiplier invariant is essential: an unrestricted centered
quotient can vanish, for example for the representation `p²=p²+0+0+0` at
`k=p`. For `1 < k < p` the zero case is constructively impossible:

```text
centered_norm = 0
    ⇒ every centered coordinate is zero
    ⇒ k divides each original coordinate
    ⇒ p = k·(u²+v²+w²+x²)
    ⇒ k=1 or p=k,
```

contradicting `1 < k < p`. The exact checked endpoint is

```text
four_square_descent_bounded_centered_quotient_nonzero:

Prime(p), 1 < k < p,
p·k = a²+b²+c²+d²,
four centered signed coordinate witnesses,
k·r = centered_norm

    ⇒ r ≠ 0.

SHA-256: 76e8b2a148cb36d2e456ec59810f93fe0f73d9c34d69ad7de3b8982de30cae9f.
```

Combining this with the sharp odd bound yields a branch interface whose only
remaining mathematical premise is representability of the same quotient:

```text
four_square_descent_odd_centered_strict_step:

Prime(p), 1 < k < p, k=2h+1,
p·k = original_norm,
four centered signed coordinate witnesses,
k·r = centered_norm,
FourSquare(p·r)

    ⇒ ∃ s, 0 < s < k ∧ FourSquare(p·s).

SHA-256: 75e1a1097d08b24c1168513ed20472ff9d9141bb1ef856aee652b3d00114ce4b.
```

## Genuine even-multiplier halving

Matching even/odd witnesses for a coordinate pair construct both an even sum
and an even absolute difference. Applying the already checked six-variable
Euler subclass with the two-square factor `1²+1²` gives

```text
2(a²+b²+c²+d²)
  = (a+b)² + |a-b|² + (c+d)² + |c-d|².
```

When both pairs have matching parity, every displayed right coordinate is
even. Exact square-factor cancellation therefore proves

```text
four_square_descent_even_multiplier_matching_parity_halving:

n·2 = a²+b²+c²+d²,
MatchingParity(a,b),
MatchingParity(c,d)

    ⇒ FourSquare(n).
```

This is an actual strict even-multiplier reduction for `n = p·t`, not an
assumed descent rule. The separate parity-selection candidate completes the
constructive coordinate case split and proves the unconditional endpoint

```text
four_square_parity_represented_additive_double_halving:

FourSquare(n+n) ⇒ FourSquare(n).
```

## Constructive termination and seed integration

The strict-step hypothesis is explicitly

```text
∀ p k, Prime(p) → k ≠ 0 → k ≠ 1 → FourSquare(p·k)
  → ∃ r, r ≠ 0 ∧ r < k ∧ FourSquare(p·r).
```

Bounded induction on `k` proves termination at multiplier one:

```text
four_square_descent_strict_multiplier_bounded

SHA-256: 6929fe9263c7da1673c64be0f5043992de4774210433736a77a4db85b826b54c.
```

Every modular square seed

```text
x² + y² + 1 = p·k
```

automatically has `k ≠ 0`, and the previously checked seed bridge represents
`p·k` as four natural squares. Combining these with multiplier descent and
the exact prime-to-universal Lagrange reduction gives

```text
four_square_lagrange_from_modular_seeds_and_strict_descent

SHA-256: 9ce8baabf8926783a666e0e3a7bc81d45eaa5eadec5fb4d3b6ed0a7308443673.
```

The theorem visibly has two hypotheses:

1. every prime `p ≡ 3 (mod 4)` has a witnessed modular square seed;
2. every represented nonunit prime multiplier has an explicit nonzero,
   strictly decreasing represented successor.

The first premise is now independently established by the modular-seed
candidate; its bounded refinement provides the essential invariant `k<p`.
The centered residue choices, strict odd norm inequality, nonzero proper
quotient, quaternion quotient arithmetic, terminating bounded induction, and
unconditional even halving are constructive. The remaining obligation is a
signed quaternion identity covering every centered sign pattern together
with divisibility of all four output coordinates, yielding
`FourSquare(p·r)` for the same centered quotient. No classical axiom,
subtraction, trusted ring search, or implicit premise is used.
No Alpha or Stable admission is claimed.
