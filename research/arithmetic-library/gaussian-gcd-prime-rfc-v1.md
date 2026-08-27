# Gaussian ring, actual divisibility, gcd and prime divisors

Status: mathematically frozen additive candidates, 2026-08-28. This is the
ring/gcd foundation for G082, not a claim that these three files alone prove
finite Gaussian factorization or permutation uniqueness. No kernel, parser,
trusted checker, replay cap, historical provider or existing Alpha artifact
was changed.

## Exact carrier and conservative graphs

The carrier and operations are the actual G081 canonical signed-pair graphs.
For signed coordinates `a+bi`, encode each coordinate by its historical zigzag
code, then use the historical doubled-Cantor pair. Consequently Gaussian zero
is natural code `0`, Gaussian one is natural code `6`, and natural code `1`
is not a Gaussian carrier value. The four unit codes are `2,4,6,10`.

The following are abbreviations over ordinary Heyting arithmetic, not new
symbols or assumed algebra laws. `Mul` and `Add` below mean the unchanged
actual Gaussian multiplication and shared signed-pair addition graphs.

| Graph | Exact mathematical content |
| --- | --- |
| `GDvd(d,z)` | `∃q. Mul(d,q,z)` |
| `GUnit(z)` | `∃v. Mul(z,v,6)` |
| `GAssociate(a,b)` | `∃u. GUnit(u) ∧ Mul(u,a,b)` |
| `GIrreducible(z)` | Valid `z`, `z≠0`, not a unit, and every actual `z=a·b` has a unit factor |
| `GPrime(z)` | Valid `z`, `z≠0`, not a unit, and every actual product divisible by `z` has a factor divisible by `z` |
| `GBezout(g,a,b,u,v)` | Actual product codes `r,s` satisfy `Mul(a,u,r) ∧ Mul(b,v,s) ∧ Add(r,s,g)` |
| `GGcd(g,a,b)` | `g` actually divides both inputs, and every actual common divisor divides `g` |

All public graph builders require an explicit tuple of distinct free-context
identifiers. They parse legitimate term arguments, support repeats and
constants, reject undeclared variables and formula injection, reject capture
by every nested binder namespace, and reparse the complete ordinary-HA
expansion. The factorization target is not embedded in any graph.

## Principal proved contracts

`gaussian_gcd_bezout_exists` has only the two actual carrier premises:

```text
∀a b. Valid(a) → Valid(b) →
  ∃g u v. GGcd(g,a,b) ∧ GBezout(g,a,b,u,v).
```

There is no supplied gcd, quotient history, norm, Bézout coefficient,
nonzero-input premise or factorization oracle. Ordinary induction on an
explicit natural upper bound for the second input's norm constructs the
witnesses. The successor case constructs G081 Euclidean quotient and
remainder data, invokes the induction hypothesis at the strictly smaller
remainder norm, then constructs the signed coefficient `u−qv` and checks its
actual multiplication/addition equation. The zero-right case chooses gcd
`a` and coefficients `6,0`, including the pair `(0,0)`.

`gaussian_gcd_unique_up_to_associate` proves actual witnessed unit equivalence
of any two gcd values. It does **not** claim literal equality of gcd codes:
codes `6` and `2`, for example, represent distinct associated gcd choices.

`gaussian_irreducible_dvd_product` proves the full prime-divisor property:

```text
∀p a b c. GIrreducible(p) → Mul(a,b,c) → GDvd(p,c) →
  GDvd(p,a) ∨ GDvd(p,b).
```

The proof computes a gcd and Bézout combination for `p,a`. Irreducibility
makes either the gcd or its cofactor in `p` an actual unit. In the first case,
the actual unit inverse and the actual multiplied Bézout sum construct a
quotient for `p|b`; in the second, witnessed association gives `p|a`.
`gaussian_irreducible_iff_prime` proves the converse as well: a prime divisor
of a nonzero product has an actually invertible cofactor.

Additional checked interfaces include:

- Actual zero/one, associativity, commutativity, distribution, subtraction,
  and nonzero multiplication cancellation; no abstract ring-law axiom.
- Unit iff actual norm one, with an actual conjugate inverse construction.
- Divisibility decision by actual Euclidean division, including a separate
  zero-divisor branch.
- Actual divisor norm factorization with both quotient and quotient-norm
  witnesses; the norm bound separately requires a nonzero dividend.
- Association reflexivity, symmetry, transitivity and norm preservation,
  and constructive association from mutual divisibility.
- An actual irreducible divisor of an irreducible value is associated to it
  by a genuine unit witness.

## Dependency-ordered inventory

Factories, all in `peano_lab.library`, are ordered as follows:

| Module / factory suffix | Rows | Direct edges | Commands | Body occurrences | Body objects | Max depth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gaussian_ring_candidate` | 65 | 204 | 2162 | 5232 | 5070 | 83 |
| `gaussian_divisibility_candidate` | 29 | 92 | 787 | 1345 | 1345 | 38 |
| `gaussian_gcd_candidate` | 14 | 76 | 777 | 1275 | 1275 | 50 |
| Total | 108 | 372 | 3726 | 7852 | 7690 | 83 |

Each factory is named `make_<module>_theorems`. The largest body has 203
occurrences. Product distribution is deliberately split into four guided
natural-coordinate identities and their assembly; the resource caps are
unchanged.

The ordered-name SHA-256, joining names with `\n` and no trailing newline, is
`9eec0687e7536f131556afe4b6db1a613a7ccadc6bb713399ae1c2bcf123f319`.

Principal exact statement SHA-256 values:

| Theorem | SHA-256 |
| --- | --- |
| `gaussian_gcd_bezout_exists` | `67d09aa8ff5c895839b29eb5f9f44d9d91087f8f2316698b47530795b800f981` |
| `gaussian_gcd_unique_up_to_associate` | `2ea8e4c57a49cecb2aee00f5611ef247500d39fe0f1fc1b239b478a49bd3a7c5` |
| `gaussian_irreducible_dvd_product` | `e2fb26736c7080feea9c73498dc0609b2e08cfdd89bdf16857afd0e6a9eb7620` |
| `gaussian_irreducible_iff_prime` | `aa8c5f0706fbabf6c9069ae0fd2a7f7b3ecf9651b30bad9d7b4483fbd6d2689e` |

## Verification receipt and authority boundary

The exact immutable test parent is Alpha v28: 2764 checked rows, Stable432,
catalog SHA-256
`897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`.
Tests reconstruct the parent's exact `TheoremSpec` fields from this pinned
catalog instead of importing a memory-heavy edition chain.

The complete expanded regression run passed **919/919 tests in 546.82s**:

```text
env PYTHONPATH=peano-lab/py:scripts python3 -m pytest -q \
  peano-lab/py/tests/test_gaussian_ring_candidate.py \
  peano-lab/py/tests/test_gaussian_divisibility_candidate.py \
  peano-lab/py/tests/test_gaussian_gcd_candidate.py
```

Every one of the 108 positive bodies is checked in a fresh process by the
unchanged original HA kernel, with a 45-second CPU soft limit, 50-second hard
limit and 60-second subprocess wall limit. Every body has false-conclusion
and truncated-script rejection tests; every nonempty dependency list has
removed and corrupted dependency rejection tests. Per-body node/object/depth
profiles and all inventory/statement pins are literal regression assertions.
Independent AST contracts check the complete graph and root semantics;
all local `have` formulae are parsed. Additional mutations target the actual
carrier, Gaussian identity code, nonzero cancellation, divisor norm boundary,
unit ambiguity of gcd values and disjunctive prime conclusion. Integer-pair
microaudits cover code round trips, norm multiplication, zero, units,
division, genuine Euclidean Bézout equations and finite prime-divisor
examples; these numerical audits are not mathematical admission evidence.

These are curried candidate-body checks, not independent admission of their
dependency assumptions. Any Alpha promotion still requires an exact
dependency-closed empty-context HA bundle and the independently compiled
Lean checker, with their own immutable receipt. This RFC does not promote
Stable, grant checked-use authority or close G082 by itself. The actual
finite product, factor search, factorization and witnessed-permutation
theorems belong to their separate additive modules.

Frozen source SHA-256 values:

```text
gaussian_ring_candidate.py
  7e6d4a3ba15f7190047e656d91a2a0f781e6a24ab055ebcf7bc0efc6d15d3e44
gaussian_divisibility_candidate.py
  ce5d6fd7d38504d2d6cd050e38bccef4b6a504f8ecb49f8ca86e78aaace48747
gaussian_gcd_candidate.py
  da72285e399ece582e3ececadf660cb71936e293627b75849410f6022946ef33
```
