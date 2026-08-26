# Euclidean execution and complexity: constructive G101 prerequisite tranche

Status: **15 original-kernel theorems proved; campaign goal G101 remains
PARTIAL.** No checked binary-length relation or logarithmic induction is
introduced, and no theorem below claims the missing asymptotic result.

## 1. Exact campaign target and truthful frontier

The unchanged number-theory blueprint requests

```text
G101:
  forall a b ell.
    b > 0 /\ BitLen(b, ell) ->
    exists g steps t.
      Execution(Euclid, (a, b), g, steps, t)
        /\ Gcd(a, b, g)
        /\ steps <= 2 * ell + 1.
```

`BitLen` and the generic blueprint `Execution` relation remain planning
vocabulary: neither has a checked conservative definition in the Alpha-v20
parent. Consequently **G101 is not proved, not complete, and not promoted as
a completed campaign goal**.

This tranche proves two strong independent prerequisites in the unchanged
intuitionistic Peano kernel:

```text
forall a b.
  exists g l.
    EuclidExecution(a,b,g,l) /\ l <= b

forall a b q r Q t.
  EuclidDivision(a,b,q,r) -> EuclidDivision(b,r,Q,t) ->
  t + t < b.
```

The first result supplies an authentic, complete, beta-coded Euclidean
division history and an independently certified relational gcd, with the
strong linear budget `l <= b`. The second gives precisely the strict
two-division halving inequality needed by the eventual logarithmic argument.

Both formulas are schematic display notation only. Their actual checked
statements contain no named relation constants, no division or gcd function,
no beta primitive, no list type, no logarithm, and no additional axiom.

## 2. Hygienic conservative definitions

All three authoring helpers reject numerals, compound fragments, reserved
words, invalid tags, and generated-binder capture. Different safe tags
produce alpha-equivalent kernel formulas.

### EuclidDivision

```text
EuclidDivision(a,b,q,r) :=
  a = b*q + r /\ exists k. k + S r = b.
```

API:

```python
euclidean_division(
    dividend: str,
    divisor: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
) -> str
```

This is exact quotient/remainder division with a genuinely strict remainder
bound. The bound precludes a zero divisor without any opaque positive-divisor
primitive.

### EuclidHalving

```text
EuclidHalving(b,t) := exists k. k + S (t + t) = b.
```

API:

```python
euclidean_halving(divisor: str, remainder: str, *, tag: str) -> str
```

Thus the checked conclusion is strict: `2*t < b`, not the weaker `t <= b/2`.

### EuclidExecution

```text
EuclidExecution(a,b,g,l) :=
  exists s h e.
    ContinuedFractionTrace(a,b,s,h,e,l)
      /\ IsGCD(g,a,b).
```

API:

```python
euclidean_execution(
    dividend: str,
    divisor: str,
    result: str,
    steps: str,
    *,
    tag: str,
) -> str
```

`ContinuedFractionTrace` is the already checked, fully expanded G071
beta-history relation. Its zeroth state has shape `(d,0,nil)`, its terminal
state has shape `(a,b,s)`, and each adjacent state contains an exact
strict-remainder Euclidean division plus the corresponding tagged quotient
cell. `IsGCD` expands to the original two-divisibility and greatest-common-
divisor universal properties.

An important boundary is explicit: the trace existentially hides its
zeroth-state value `d`, whereas the relation separately certifies `g` as a
relational gcd of the input. **This tranche does not prove the missing
identification `d = g`.** The underlying trace and gcd are both genuine
kernel-certified witnesses, but the family does not yet formalize extraction
of the output specifically from the terminal beta state. That identification
is listed among the G101 residuals; neither the concrete executable verifier
nor the checked parent uniqueness theorem silently replaces it.

## 3. Dependency DAG and theorem inventory

```text
checked Alpha-v20 exact division
    |
    +--> euclidean_division_step_exists
    |       |
    |       +--> euclidean_next_division_step_exists
    |
    +--> euclidean_division_step_functional
    |
checked strict order + additive monotonicity
    |
    +--> euclidean_add_right_preserves_lt
    |
    +--> euclidean_two_step_quotient_nonzero
              |
              +--> euclidean_two_step_halving

checked G071 beta-history extension + bounded natural induction
    |
    +--> euclidean_trace_bound_weaken
              |
              +--> euclidean_trace_exists_up_to_linear
                        |
                        +--> euclidean_trace_exists_linear
                                  |
checked relational gcd -----------+--> euclidean_gcd_execution_linear_bound

checked G071 beta history + checked relational gcd
    |
    +--> euclidean_execution_zero_divisor
    +--> euclidean_execution_gcd_correct
    +--> euclidean_execution_trace_correct
    +--> euclidean_execution_exists
    +--> euclidean_nonzero_execution_exists
```

| # | Checked theorem | Original proof nodes | Depth | Exact contribution |
|---|---|---:|---:|---|
| 1 | `euclidean_division_step_exists` | 15 | 10 | Nonzero divisor yields an exact strictly bounded division. |
| 2 | `euclidean_division_step_functional` | 58 | 34 | Quotient and remainder are jointly unique. |
| 3 | `euclidean_next_division_step_exists` | 18 | 13 | A nonzero remainder yields the next division. |
| 4 | `euclidean_add_right_preserves_lt` | 19 | 12 | Strict natural order survives right addition. |
| 5 | `euclidean_two_step_quotient_nonzero` | 37 | 21 | The second quotient after a strict decrease is nonzero. |
| 6 | `euclidean_two_step_halving` | 57 | 30 | Two exact consecutive steps imply `2*t < b`. |
| 7 | `euclidean_trace_bound_weaken` | 38 | 24 | A checked history budget may be enlarged by one. |
| 8 | `euclidean_trace_exists_up_to_linear` | 219 | 42 | If `b <= B`, build an actual complete beta-history in at most `B` divisions. |
| 9 | `euclidean_trace_exists_linear` | 11 | 9 | Instantiate the exact history budget with `B=b`. |
| 10 | `euclidean_execution_zero_divisor` | 21 | 14 | Exact zero-step boundary, with gcd output `a`. |
| 11 | `euclidean_execution_gcd_correct` | 20 | 13 | Every expanded execution certifies the full relational gcd. |
| 12 | `euclidean_execution_trace_correct` | 23 | 16 | Every expanded execution contains an actual complete beta history. |
| 13 | `euclidean_execution_exists` | 38 | 24 | Total beta-history and relational gcd for all input naturals. |
| 14 | `euclidean_nonzero_execution_exists` | 30 | 18 | Every nonzero divisor has a genuinely nonempty execution. |
| 15 | `euclidean_gcd_execution_linear_bound` | 48 | 29 | Complete beta-history, certified relational gcd, and `steps <= b`. |

Frozen family totals:

```text
theorems                         15
tactic commands                 372
declared direct dependencies     34
external checked dependencies    22
original kernel proof nodes     652
maximum single proof nodes      219
maximum proof depth              42
DNE/classical proof nodes         0
new axioms/rules/primitives       0
```

Every one of the 22 external prerequisites is already inside the immutable
590-node Alpha-v20 proof-artifact dependency cone:

```text
add_le_add_right
add_succ_left
continued_fraction_empty_trace_exists
continued_fraction_nonzero_divisor_exists
continued_fraction_trace_exists
continued_fraction_trace_extend
division_remainder_exists
division_remainder_unique
gcd_exists_relational
is_gcd_zero_right
le_eq_or_lt
le_mul_of_one_le_right
le_of_succ_le_succ
le_refl
le_succ
le_zero
lt_irrefl_expanded
lt_of_lt_of_le
lt_trans
one_le_of_ne_zero
succ_le_succ
zero_add
```

## 4. Constructive two-step argument

Write the consecutive divisions as

```text
a = b*q + r,    r < b,
b = r*Q + t,    t < r.
```

If `Q=0`, then `b=t`; the inequalities would give `r<t<r`, contradicting
the existing intuitionistically checked irreflexivity of strict order.
Hence `Q != 0`, constructively, and the checked natural-order theorem gives
`1 <= Q`. Multiplicative monotonicity therefore yields

```text
r <= r*Q,
r+t <= r*Q+t = b.
```

Strict right-additive monotonicity applied to `t<r` gives `t+t<r+t`.
Composing strict and weak order proves `t+t<b`. No case-free classical
contrapositive, excluded middle, real logarithm, division function, or
double-negation elimination appears in the original kernel body.

## 5. Constructive linear bound

The induction invariant is the stronger statement

```text
forall B b. b <= B -> forall a.
  exists s h e l.
    ContinuedFractionTrace(a,b,s,h,e,l) /\ l <= B.
```

- For `B=0`, `b=0`; the checked empty beta-history has length zero.
- For `B=S B'` and `b=S B'`, bounded division gives `a=b*q+r` with
  `r<=B'`. The induction hypothesis supplies a real reverse beta-history
  for `(b,r)` in at most `B'` steps. The checked history-extension theorem
  prepends the exact quotient, producing length `S l <= S B'`.
- For `b<S B'`, the induction hypothesis already constructs a history in
  `B'` steps; checked bound weakening gives the successor budget.

Taking `B=b` proves the exact `steps<=b` claim. The family then pairs that
history with checked relational gcd existence. The zero-divisor case is
therefore also exact: zero divisions, no spurious `+1` slack.

## 6. Untrusted executable examples and allocation caps

The module also exposes immutable concrete dataclasses and an executable
demonstrator:

```python
certify_euclidean_execution(a, b) -> EuclideanExecutionCertificate
verify_euclidean_execution(certificate) -> bool
```

The implementation performs genuine integer Euclidean divisions; constructs
the exact doubled-Cantor/tagged-cell quotient list; packs the reversed
states; and builds a real Gödel beta history using pairwise-coprime moduli.
The verifier recomputes the entire witness, rejects any tampered field,
checks every beta residue, and checks both the proved linear bound and the
numerical bit-length inequality for the supplied example.

**The numerical bit-length check is not a kernel proof and does not close
G101.** All demonstration inputs have hard fail-closed caps:

```text
input natural width          128 bits
actual Euclidean divisions     14
packed state width         32,768 bits
beta-history/CRT budget   262,144 bits
```

The caps are enforced before dangerous packed-state and CRT allocations.
Fibonacci worst cases independently exercise the beta-history, packed-state,
and step-limit failure paths. Booleans, negative integers, non-integers,
oversized naturals, malformed witnesses, and forged quotient/remainder/history
fields are rejected.

## 7. Remaining work before G101 can close

1. Introduce a hygienic conservative `BitLen(b,ell)` relation, including an
   explicit zero convention and fully checked existence/functionality.
2. Relate bit length to strict doubling/halving inside unchanged HA.
3. Prove that the hidden zeroth-state value of a complete beta-coded
   Euclidean history equals its certified relational gcd output.
4. Formalize induction over pairs of beta-history transitions, using
   `euclidean_two_step_halving` rather than a host-language complexity claim.
5. Derive the exact blueprint bound `steps <= 2*ell+1` with every boundary
   case and endpoint witness original-kernel checked.

Until all five items have genuine conservative definitions and original-
kernel proof bodies, the campaign status remains **G101 PARTIAL**.

## 8. Source and focused regression

```text
peano-lab/py/peano_lab/library/euclidean_complexity_candidate.py
peano-lab/py/tests/test_euclidean_complexity_candidate.py
```

```sh
cd peano-lab/py
python3 -m pytest -q --tb=short tests/test_euclidean_complexity_candidate.py
```

The regression independently freezes all 15 exact statement hashes, scripts,
proof-node counts, dependency DAGs, and depth receipts; replays every
dependency-curried body through the unchanged kernel; rejects forged false
conclusions, truncated scripts, undeclared dependencies, and mutated local
proof obligations; checks conservative binder hygiene; and audits boundary,
Fibonacci, malicious-witness, and allocation-cap examples.
