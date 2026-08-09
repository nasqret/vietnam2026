# Bertrand's postulate campaign

This campaign aims to prove Bertrand's postulate completely inside the
unchanged intuitionistic arithmetic kernel. Its primary endpoint is

$$
\forall n\ne0\;\exists p\,
\bigl(\operatorname{Prime}(p)\land n<p\land p\le 2n\bigr),
$$

followed by the traditional strict corollary for $1<n$:

$$
\exists p\,
\bigl(\operatorname{Prime}(p)\land n<p<2n\bigr).
$$

```{admonition} Current evidence boundary
:class: warning
Bertrand's postulate is **not yet proved** in this repository. Alpha v3
contains twenty-one first-round specifications whose dependency-curried
bodies check, but they remain `body_checked` and unavailable through checked
theorem replay. The valuation multiplication law, binomial coefficients,
central-binomial bounds, primorial bound, exact main inequality, finite
coverage, and both endpoints remain open.
```

The binding statement, logic, representation, validation, and release rules
are frozen in
[`RFC HA-R6-BERTRAND-1`](https://github.com/nasqret/vietnam2026/blob/9efc5cd95ae7698a092c922d83e29f9d2dedea24/research/arithmetic-library/ha-bertrand-postulate-campaign-rfc-v1.md).
It selects an integer-only Erdős--Tochiori central-binomial proof. No real
numbers, logarithms, primitive binomial operation, classical axiom, or new
kernel rule is permitted.

## Why the proof remains constructive

The finite interval is decided before the contradiction argument begins:

```text
bounded_prime_interval_search(l,u)
  |
  |-- witness p with Prime(p), l<p, p<=u  ---> return p
  `-- pointwise certificate excluding every such p
                                                |
                                                `-- refute by integer bounds
                                                    and use false.elim
```

Consequently, the negative branch is explicit data. The proof never turns
$\neg\neg\exists p$ into $\exists p$.

## Current Alpha v3 layer

Alpha v3 is an additive child of the sealed 902-row Alpha v2 ledger.

| Quantity | Exact value |
|---|---:|
| Alpha v3 specifications | 923 |
| Stable rows | 432 |
| Alpha-only rows | 491 |
| checked-use rows | 570 |
| direct dependency edges | 2,730 |
| dependency layers | 45 |
| first-round Bertrand rows | 21 |

All twenty-one additions are `body_checked`; checked use remains unchanged at
570. The enrollment root is
`4507736cde37301ecf3369540d6cc686de860b07b101f2afb60f850f86aeebd4`.
The deterministic channel pointer is
[`channels-v3.json`](https://github.com/nasqret/vietnam2026/blob/9efc5cd95ae7698a092c922d83e29f9d2dedea24/artifacts/peano-library/channels-v3.json).

### B0 — constructive interval search

- `prime_strictly_above_decidable`;
- `bounded_prime_interval_search`;
- `prime_interval_exclusion_refutes_witness`;
- `bounded_prime_interval_decidable`.

The interval orientation is exactly $(l,u]$. The largest local closed
certificate in this group has 2,896 structural nodes and depth 78.

### B1 — quantitative powers and order

- `mul_le_mul`;
- `le_mul_of_one_le_right` and `le_mul_of_one_le_left`;
- `pow_base_monotone`;
- `one_le_pow`;
- `pow_nonzero_of_one_le`;
- `pow_exponent_monotone`.

The largest local closure is `pow_exponent_monotone`, at 70,898 nodes and
depth 89.

### B2 — bounded prime-power valuation

- `power_divides_decidable` and `power_divides_zero`;
- `bounded_power_valuation_search` and
  `bounded_power_valuation_exists`;
- `power_valuation_exists` and `power_valuation_functional`;
- the divisibility and maximality projections;
- `prime_power_valuation_exists` and
  `prime_power_valuation_functional`.

The relation chooses the greatest $e\le a$ for which $p^e$ divides $a$.
The prime/nonzero wrapper excludes the intentionally degenerate $p=0,1$ and
$a=0$ cases. The largest local closure is 125,485 nodes and depth 93.

Every direct dependency has a removal or Cut-mutation test, every displayed
statement has an exact hash, and complete proof traversals find zero `DNE`.
These local closures establish feasibility; the Alpha evidence remains
body-only until the versioned two-process cold receipt is accepted.

## Post-v3 checked candidates

Two further isolated tranches are pushed but are not yet enrolled in Alpha.

The valuation bridge proves, under `Prime(p)` and $a\ne0$, that the selected
canonical exponent satisfies

$$
p^e\mid a\quad\text{and}\quad p^{e+1}\nmid a.
$$

Its capstone `power_valuation_selected_and_successor_not_divides` closes at
7,632 nodes and depth 75. It deliberately does not claim the converse or the
still-open multiplication law $v_p(ab)=v_p(a)+v_p(b)$.

The integer-envelope spike proves five reusable facts, culminating in

$$
(s+7)^{12}\le4^{s+5}
\Longrightarrow
(s+13)^{12}\le4^{s+11}.
$$

That guard closes at 213,731 nodes and depth 100. It validates the key
six-step mechanism but is not the complete B6 inequality.

## Dependency roadmap

```text
B0 interval decision ------------------------------------------+
                                                               |
B1 order, powers, FloorSqrt, floor/ceiling arithmetic ----+    |
                                                          |    |
B2 valuations + Legendre ----------+                      |    |
                                    |                      |    |
B3 Choose/CentralBinom -------------+----> B5 factor ranges|    |
              |                     |          and upper bound |
              `----> B4 primorial --+                      |    |
                                                          v    v
                                                   B6 main inequality
                                                          |
                                          B7 n >= 512 theorem
                                                          |
                                      B8 finite coverage + BP01/BP02
```

The central lower bound will prove $4^n<n\binom{2n}{n}$. Under an explicit
no-prime certificate for $(n,2n]$, valuations and the primorial will give

$$
\binom{2n}{n}
\le
(2n)^{\lfloor\sqrt{2n}\rfloor}
4^{\lfloor2n/3\rfloor}.
$$

The exact natural-number B6 target is

$$
n(2n)^{\lfloor\sqrt{2n}\rfloor}
4^{\lfloor2n/3\rfloor}\le4^n
\qquad(n\ge512).
$$

The current spike reduces its difficult growth component to six residue
classes using

$$
H(s)=(s+1)^{2s+2},\qquad
E(s)=\left\lceil\frac{s^2}{6}\right\rceil,
$$

and the exact identity $E(s+6)=E(s)+2s+6$. `FloorSqrt`, ceiling-by-six,
the six base cases, the $H$ transport, and the final bridge back to $n$ remain
formal obligations.

## Durable checkpoints

| Commit | Content |
|---|---|
| `10dc017` | multiplicative order and base-power monotonicity |
| `6739532` | campaign RFC, constructive interval search, power growth |
| `be5b735` | bounded valuation existence and functionality |
| `941ad70` | selected valuation and successor nondivisibility |
| `3ce8a90` | additive, fail-closed Alpha v3 channel |
| `9efc5cd` | integer-envelope feasibility spike |

All six commits are pushed to `nasqret/vietnam2026` on
`agent/new-theorems-tranche-01`.

## Reproduce the current gates

```bash
make peano-library-alpha-v3-check

PYTHONPATH=peano-lab/py python3 -m pytest -q \
  peano-lab/py/tests/test_bertrand_prime_interval_candidate.py \
  peano-lab/py/tests/test_bertrand_power_order_candidate.py \
  peano-lab/py/tests/test_bertrand_power_growth_candidate.py \
  peano-lab/py/tests/test_bertrand_power_valuation_candidate.py \
  peano-lab/py/tests/test_bertrand_power_valuation_laws_candidate.py \
  peano-lab/py/tests/test_bertrand_integer_envelope_candidate.py
```

The first command validates the published Alpha-v3 evidence boundary. The
second includes expensive local empty-context feasibility checks; it does not
upgrade Alpha evidence or promote anything to Stable.
