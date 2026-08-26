# Constructive logarithmic Euclidean complexity: full closure of G101

Status: **G101 fully proved by 17 dependency-ordered theorem bodies accepted
by the unchanged first-order Heyting-arithmetic kernel.** The final theorem
constructs every required witness, its actual beta-coded Euclidean execution,
the gcd value physically encoded in its terminal zero-divisor state, and the
exact campaign bound `steps <= 2*BitLen(b)+1`. A separately proved stronger
result gives `steps <= 2*BitLen(b)`.

No new axiom, proof rule, parser symbol, exponentiation term, classical
principle, host-language gcd calculation, or complexity oracle contributes
mathematical authority.

## 1. Exact object-level endpoints

The supplied-bit-length root is the original-kernel proof named
`euclidean_gcd_execution_logarithmic_bound`:

```text
forall a b ell.
  BitLen(b,ell) ->
  exists g k.
    AnchoredEuclidExecution(a,b,g,k)
      /\ (exists gap. gap + k = 2*ell+1).
```

The unconditional constructive root is
`euclidean_gcd_execution_logarithmic_exists`:

```text
forall a b.
  exists ell g k.
    BitLen(b,ell)
      /\ (AnchoredEuclidExecution(a,b,g,k)
          /\ (exists gap. gap + k = 2*ell+1)).
```

Here `BitLen` uses the mandatory campaign convention `BitLen(0,1)`. The
anchored execution is not an abstract termination claim:

```text
AnchoredEuclidExecution(a,b,g,k) :=
  exists quotient_list history scale.
    ContinuedFractionTrace(a,b,quotient_list,history,scale,k)
      /\ (StateAt(history,scale,0,g,0,0) /\ IsGCD(g,a,b)).
```

Its history has `k` genuine exact strictly decreasing division transitions.
Its physically encoded terminal zero-divisor state contains the **same** `g`
that satisfies the complete relational gcd specification for `(a,b)`.

All capitalized names are explanatory abbreviations only. Actual checked
statements expand them into zero, successor, addition, multiplication,
equality, first-order quantification, and intuitionistic connectives.

## 2. Conservative reusable definition surfaces

```python
euclidean_bounded_trace(
    dividend: str,
    divisor: str,
    budget: str,
    *,
    tag: str,
) -> str

euclidean_logarithmic_execution(
    dividend: str,
    divisor: str,
    length: str,
    result: str,
    steps: str,
    *,
    tag: str,
) -> str
```

Schematically:

```text
EuclideanBoundedTrace(a,b,B) :=
  exists s h e k.
    ContinuedFractionTrace(a,b,s,h,e,k)
      /\ (exists gap. gap+k=B).

EuclideanLogarithmicExecution(a,b,ell,g,k) :=
  BitLen(b,ell)
    /\ (AnchoredEuclidExecution(a,b,g,k)
        /\ (exists gap. gap+k=2*ell+1)).
```

Both surfaces validate argument identifiers, reject malicious tags and
generated binder capture, preserve exactly their intended free variables,
and produce alpha-equivalent expanded formulas for different safe tags. They
are conservative authoring abbreviations rather than new kernel predicates.

## 3. The actual logarithmic induction

The central theorem `euclidean_log_trace_below_power` proves the stronger
claim:

```text
forall n p.
  PowTwo(n,p) ->
  forall b. b < p ->
  forall a.
    EuclideanBoundedTrace(a,b,n+n).
```

The kernel checks genuine induction on `n`; `PowTwo(n,p)` is the already
checked fully expanded beta-coded `Pow(2,n,p)` graph.

### Base exponent

For `n=0`, uniqueness of the zeroth power gives `p=1`. The strict hypothesis
`b<1` constructively implies `b=0`. The existing genuine complete Euclidean
history with linear bound `steps<=b` therefore has exactly zero steps and is
within the exact `0+0` budget.

### Successor exponent

For `n+1`, constructive power totality supplies `P=2^n`, and the checked
successor-power theorem proves `p=P+P`.

If `b=0`, the same genuine zero-step history fits every supplied budget.

Otherwise exact constructive division supplies a real first transition

```text
a = b*q+r,   r<b.
```

If `r=0`, a genuine zero-step history for `(b,r)` is extended through this
actual division once; weakening the resulting bound by one gives the exact
successor budget `S(S(n+n)) = S(n)+S(n)`.

If `r` is nonzero, exact division supplies a real second transition

```text
b = r*Q+t,   t<r.
```

The immutable Alpha-v21 theorem `euclidean_two_step_halving` applies to
**those exact two transitions** and derives

```text
t+t < b.
```

The outer hypothesis and successor-power identity give

```text
b < P+P.
```

Transitivity yields `t+t < P+P`; the newly checked constructive strict
doubling cancellation theorem proves `t<P` without excluded middle for
arbitrary propositions. The induction hypothesis therefore constructs an
actual complete beta history for `(r,t)` within `n+n` steps.

Two applications of the checked beta-history extension theorem prepend the
two exact divisions and increase the budget by exactly two:

```text
steps <= S(S(n+n)) = S(n)+S(n).
```

The conclusion is consequently a constructed terminating history, not a
host-language inequality imposed on an assumed execution.

## 4. From bit length to the exact campaign endpoint

`euclidean_log_binary_length_upper_power` proves that every supplied
`BitLen(b,ell)` yields a beta-coded witness `p=2^ell` with `b<p`.

For positive `b`, this is the genuine upper-power inequality already present
inside the expanded bit-length relation. For `b=0`, constructive power
totality and nonvanishing give `0<2^ell`, honoring the explicit
`BitLen(0,1)` convention.

The power induction then proves:

```text
BitLen(b,ell) ->
exists s h e k.
  ContinuedFractionTrace(a,b,s,h,e,k) /\ k <= ell+ell.
```

The immutable Alpha-v22 terminal-invariant theorem
`euclidean_trace_terminal_gcd_exists` extracts the **actual** encoded
terminal value `g` and proves `IsGCD(g,a,b)`. Reassembling the same trace,
same terminal state, and same step witness proves the stronger anchored
result:

```text
BitLen(b,ell) ->
exists g k. AnchoredEuclidExecution(a,b,g,k) /\ k <= ell+ell.
```

Finally, witnessed-order successor weakening and the checked equality
`2*ell=ell+ell` give exactly `k<=2*ell+1`. Existing totality of `BitLen`
eliminates the supplied witness and produces the unconditional all-input
endpoint.

## 5. Complete checked theorem DAG

```text
constructive order
  |
  +--> euclidean_log_double_monotone
          |
          +--> euclidean_log_strict_half_cancel
                  |
                  +--> euclidean_log_halving_power_drop

genuine beta-history extension
  |
  +--> euclidean_log_budget_extend
  |       |
  |       +--> euclidean_log_budget_extend_twice
  |
  +--> euclidean_log_budget_weaken
  +--> euclidean_log_budget_zero_divisor

exact exponent arithmetic
  |
  +--> euclidean_log_double_successor
  |       |
  |       +--> euclidean_log_budget_successor_power
  |
  +--> euclidean_log_zero_below_power
  +--> euclidean_log_power_zero_divisor

all preceding tools + actual strict two-step halving
  |
  +--> euclidean_log_trace_below_power
          |
BitLen strict upper power --------+
          |                       |
          +--> euclidean_log_trace_bound
                  |
actual encoded terminal=gcd ------+
                  |
                  +--> euclidean_log_execution_strong
                          |
                          +--> euclidean_gcd_execution_logarithmic_bound
                                  |
total canonical BitLen -----------+
                                  |
                                  +--> euclidean_gcd_execution_logarithmic_exists
```

## 6. Frozen theorem inventory and receipts

| # | Original-kernel theorem | Nodes | Mathematical content |
|---|---|---:|---|
| 1 | `euclidean_log_double_monotone` | 24 | Witnessed non-strict order survives doubling. |
| 2 | `euclidean_log_strict_half_cancel` | 40 | `t+t<p+p` constructively implies `t<p`. |
| 3 | `euclidean_log_halving_power_drop` | 34 | `2t<b<2p` constructively implies `t<p`. |
| 4 | `euclidean_log_double_successor` | 19 | `S n+S n=S(S(n+n))`. |
| 5 | `euclidean_log_budget_weaken` | 38 | An actual beta history survives successor-budget weakening. |
| 6 | `euclidean_log_budget_extend` | 53 | One genuine division extends an actual history and its exact budget. |
| 7 | `euclidean_log_budget_extend_twice` | 30 | Two actual divisions extend a history and its budget by two. |
| 8 | `euclidean_log_budget_zero_divisor` | 38 | Every zero divisor has an actual zero-step history within any budget. |
| 9 | `euclidean_log_budget_successor_power` | 13 | The two-step budget equals the doubled successor exponent. |
| 10 | `euclidean_log_zero_below_power` | 24 | Zero lies strictly below every witnessed power of two. |
| 11 | `euclidean_log_power_zero_divisor` | 20 | A natural strictly below `2^0` is zero. |
| 12 | `euclidean_log_trace_below_power` | 157 | Genuine power-of-two induction constructs a complete history in at most twice the exponent. |
| 13 | `euclidean_log_binary_length_upper_power` | 91 | Every `BitLen` witness supplies a genuine strict upper power, including zero. |
| 14 | `euclidean_log_trace_bound` | 23 | An actual complete Euclidean history has `steps<=2*BitLen(b)`. |
| 15 | `euclidean_log_execution_strong` | 46 | The actual terminal-gcd anchored execution satisfies the stronger bound. |
| 16 | `euclidean_gcd_execution_logarithmic_bound` | 43 | The exact supplied-witness G101 blueprint bound `steps<=2*BitLen(b)+1`. |
| 17 | `euclidean_gcd_execution_logarithmic_exists` | 26 | Unconditional total construction of all G101 witnesses for every input pair. |

Frozen totals:

```text
theorem bodies                      17
declared direct dependencies        48
authored primitive commands        499
original-kernel proof nodes        719
maximum individual proof nodes     157
maximum proof depth                 45
new axioms, rules, or primitives     0
classical DNE proof commands         0

ordered-name SHA-256
  2f160f96931e8ff4262238d6b54d1e39406bbd232afd505078fe9faaf07aace4

power-induction statement SHA-256
  915f2b77f40e08f8ed00cf72485d98432cab710e9b90415252c2b72573a028e3

strong actual-terminal execution statement SHA-256
  61e7a009a62e18fb46a29979815fa05ae53ac68cc1d054bff89b940e9ed76baf

exact supplied-witness G101 statement SHA-256
  decf1f8be3a9dcaf2e8bdf7bebd59e46d08e9f91fee375ca325c6b53847c8d6e

unconditional all-witness G101 statement SHA-256
  c9fd69a20e1ef3f4b71cb4fc58a8fb001f37d08fc1d8c51f541409070f016523
```

## 7. Trust boundary and adversarial checks

Each body is independently checked as an ordinary dependency-curried
first-order intuitionistic derivation by the original kernel. Parent facts
are taken only from the immutable fully checked Alpha-v22 edition; local
dependencies are explicitly ordered. Full additive admission, an independent
Lean certificate, and release promotion remain separate mandatory gates.

The focused suite rejects:

- a forged `false` conjunction appended to every one of the 17 statements;
- every one of the 17 truncated proof scripts;
- removal of the final direct dependency from every major root;
- malicious/non-identifier arguments and binder tags;
- generated binder capture in both conservative definition surfaces;
- non-alpha-invariant surface expansion;
- altered root statement hashes, proof-node counts, or dependency ordering.

Tiny bounded numerical executions, including Fibonacci worst-case examples,
are regression demonstrations only and are never cited as proof authority.

```sh
cd peano-lab/py
python3 -m pytest -q tests/test_euclidean_logarithmic_bound_candidate.py
```

At candidate freeze the complete focused suite reports **72 passed**.
