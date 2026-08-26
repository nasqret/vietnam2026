# Constructive prime square-residue intersection and modular seed

The isolated twenty-row candidate factory proves the complete finite counting
and modular-seed prerequisite for the remaining prime case of Lagrange's
four-square theorem. Its strongest unconditional, independently kernel-checked
endpoint is

```text
four_square_prime_modular_seed:
  forall p.
    Prime(p) -> exists a b k. a*a + b*b + 1 = p*k.
```

The exact expanded statement has SHA-256
`41b3138912bebce6b45a92e266f018ae7d5cae16d20c817ed20a8decbf14c833`;
its dependency-curried certificate has 95 proof nodes and depth 21.

For an odd prime `p = 2h + 1`, the genuinely unbounded route is as follows:

1. Squaring is injective modulo `p` on the entire inclusive half interval
   `0,...,h`. This uses subtraction-free difference-of-squares factorization,
   Euclid's prime divisor lemma, and the strict bounds on both a coordinate
   difference and a coordinate sum.
2. The already checked beta range, pointwise multiplication, and quotient/
   remainder prefix theorems construct an actual beta code for the canonical
   square residues at every requested finite length.
3. Ordinary constructive induction and beta-prefix extension construct a
   second actual code whose decoded values satisfy `w + S r = p`; these are
   exactly the residue complements `p - 1 - r`. This operation preserves
   boundedness and injectivity.
4. The separately checked constructive cross-pigeonhole theorem interleaves
   both length-`h+1` codes and produces an actual common decoded value,
   because `p < (h+1) + (h+1)`.
5. The two canonical square-remainder equations and their complement equation
   construct an explicit multiplier `k` for `a*a + b*b + 1 = p*k`.

The odd-prime endpoint is

```text
four_square_odd_prime_modular_seed:
  forall p h.
    p = 2*h + 1 -> Prime(p) ->
    exists a b k. a*a + b*b + 1 = p*k.
```

Its expanded statement has SHA-256
`3e55824a272594c24c76d9044a4877bb3a75c10d101318dde5d6d928961bfeb2`;
its checked certificate has 193 proof nodes and depth 39. The intermediate
all-non-two-prime endpoint has SHA-256
`79e165ce9e984729b5e131898679e59a04391124a61da10d3c9cb2e9339d691e`.
The exceptional prime `2` is handled by the explicit witnesses `(1,0,1)`.

All candidate statements expand into the original first-order language; they
are dependency-curried and neither Alpha-enrolled nor Stable-admitted. This
factory proves the complete square-residue intersection and prime modular
seed, not by itself the centered quaternion descent or universal four-square
theorem. Those stronger endpoints require their own independently checked
proof bodies.

Focused verification:

```bash
cd peano-lab/py
python3 -m pytest -q --tb=line tests/test_four_square_residue_intersection_candidate.py
```
