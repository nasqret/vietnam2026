# Constructive Euclidean gcd transport and actual terminal-state identification

Status: **20 dependency-curried theorems independently accepted by the original
intuitionistic Peano kernel. The previously disclosed Euclidean terminal-state
identification gap is closed.** Campaign G101 remains PARTIAL only because
checked `BitLen` formalization and its global logarithmic induction remain
absent.

## 1. Previously open semantic gap

The immutable Alpha-v21 Euclidean-complexity family proved

```text
forall a b. exists g l.
  (exists s h e.
     ContinuedFractionTrace(a,b,s,h,e,l) /\ IsGCD(g,a,b))
  /\ l <= b.
```

The beta-coded history existentially hides its zeroth state `(d,0,nil)`.
Although the same execution separately certifies `g` as the relational gcd,
the old theorem did **not** prove `d=g` inside the kernel. Thus its two
genuine witnesses were adjacent rather than formally identified.

This tranche now proves, entirely in unchanged first-order Heyting
arithmetic,

```text
forall a b s h e l d.
  ContinuedFractionTrace(a,b,s,h,e,l) ->
  StateAt(h,e,0,d,0,0) ->
  IsGCD(d,a,b).

forall a b g l.
  EuclidExecution(a,b,g,l) ->
  exists s h e.
    ContinuedFractionTrace(a,b,s,h,e,l)
      /\ StateAt(h,e,0,g,0,0).
```

The output `g` is therefore exactly the natural physically encoded in the
actual zero-divisor terminal beta state. No host-language gcd calculation,
test oracle, opaque trace claim, classical principle, or new kernel rule
supplies this conclusion.

## 2. Conservative hygienic relations

All public helpers accept only validated identifiers, require a safe tag,
reject generated binder capture, and produce alpha-equivalent fully expanded
first-order formulas for different safe tags.

```python
euclidean_common_divisor(
    common: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str

euclidean_state_at(
    history: str,
    scale: str,
    index: str,
    dividend: str,
    divisor: str,
    quotient_list: str,
    *,
    tag: str,
) -> str

euclidean_anchored_execution(
    dividend: str,
    divisor: str,
    result: str,
    steps: str,
    *,
    tag: str,
) -> str
```

Their schematic meanings are

```text
CommonDivisor(d,a,b) :=
  (exists x. a=d*x) /\ (exists y. b=d*y).

StateAt(h,e,i,a,b,s) :=
  BetaAt(h,e,i,Pair(a,Pair(b,s))).

AnchoredEuclidExecution(a,b,g,l) :=
  exists s h e.
    ContinuedFractionTrace(a,b,s,h,e,l)
      /\ (StateAt(h,e,0,g,0,0) /\ IsGCD(g,a,b)).
```

`BetaAt`, `Pair`, `StateAt`, `CommonDivisor`, `ContinuedFractionTrace`,
`AnchoredEuclidExecution`, and `IsGCD` above are display abbreviations only.
Every actual checked formula is expanded into zero, successor, addition,
multiplication, equality, first-order quantifiers, and intuitionistic
connectives.

## 3. Constructive invariant DAG

```text
checked exact division
  |
  +--> divisor transport to remainder
  +--> divisor transport to dividend
          |
          +--> common-divisor forward + backward
                    |
                    +--> full common-divisor iff

checked relational gcd + exact division
  |
  +--> gcd forward + backward
          |
          +--> full gcd iff
          +--> equal gcd outputs across one step
          +--> unique zero-terminal gcd
          +--> unique existing EuclidExecution output

checked beta uniqueness + doubled-Cantor pair injectivity
  |
  +--> all three beta-state coordinates are unique
          |
          +--> induction over every real history transition
                    |
                    +--> terminal zero-state value is a gcd
                              |
                              +--> every history exposes that terminal gcd
                                        |
existing execution + checked gcd uniqueness
                                        |
                                        +--> actual terminal state = reported output
                                                  |
                                                  +--> anchored total execution
                                                  +--> anchored exact linear bound
                                                  +--> anchored gcd correctness
                                                  +--> anchored terminal-state correctness
```

## 4. Full frozen theorem inventory

| # | Theorem | Original nodes | Depth | Checked claim |
|---|---|---:|---:|---|
| 1 | `euclidean_divisor_remainder_transport` | 44 | 27 | A common divisor of `a,b` divides the exact remainder. |
| 2 | `euclidean_divisor_dividend_transport` | 41 | 25 | A common divisor of `b,r` divides the exact dividend. |
| 3 | `euclidean_common_divisor_forward` | 45 | 27 | Transport common divisors from `(a,b)` to `(b,r)`. |
| 4 | `euclidean_common_divisor_backward` | 45 | 27 | Transport common divisors from `(b,r)` to `(a,b)`. |
| 5 | `euclidean_common_divisor_iff` | 61 | 23 | Preserve the whole witnessed common-divisor relation in both directions. |
| 6 | `euclidean_gcd_step_forward` | 41 | 25 | A gcd of `(b,r)` is a gcd of `(a,b)`. |
| 7 | `euclidean_gcd_step_backward` | 41 | 25 | A gcd of `(a,b)` is a gcd of `(b,r)`. |
| 8 | `euclidean_gcd_step_iff` | 61 | 23 | Preserve the exact fully expanded gcd specification in both directions. |
| 9 | `euclidean_gcd_step_output_unique` | 29 | 20 | Independently witnessed gcd outputs before/after a step coincide. |
| 10 | `euclidean_gcd_zero_terminal_unique` | 30 | 17 | Every gcd of `(a,0)` equals `a`, including `a=0`. |
| 11 | `euclidean_execution_output_unique` | 32 | 18 | All existing executions for fixed inputs report the same gcd. |
| 12 | `euclidean_beta_state_functional` | 63 | 25 | One beta-history index uniquely determines all three packed state coordinates. |
| 13 | `euclidean_trace_prefix_gcd_invariant` | 168 | 54 | Every actual beta-history prefix preserves its zeroth-state gcd. |
| 14 | `euclidean_trace_initial_state_is_gcd` | 115 | 33 | The encoded zero-divisor state is the gcd of the complete history inputs. |
| 15 | `euclidean_trace_terminal_gcd_exists` | 27 | 21 | Every complete history exposes its actual encoded terminal gcd. |
| 16 | `euclidean_execution_terminal_identified` | 80 | 26 | The existing execution output equals its actual beta terminal state. |
| 17 | `euclidean_anchored_execution_exists` | 41 | 21 | A genuine output-anchored execution exists for all natural inputs. |
| 18 | `euclidean_anchored_execution_linear_bound` | 46 | 22 | Such an execution exists with exact constructive budget `steps<=b`. |
| 19 | `euclidean_anchored_execution_gcd_correct` | 28 | 17 | Every anchored execution satisfies the full relational gcd specification. |
| 20 | `euclidean_anchored_execution_state_correct` | 33 | 21 | Every anchored execution contains a history whose actual terminal state equals its output. |

Frozen totals:

```text
theorems                         20
tactic commands                 550
declared direct dependencies     32
external checked dependencies    13
original kernel proof nodes    1071
maximum single proof nodes      168
maximum proof depth              54
classical DNE proof nodes         0
new axioms/rules/primitives       0
ordered-name SHA-256             723fe350c223cc4b22dbe0f786ab64f72e16e3998fd4314f9ebe6ec84be2b3c0
anchored-root statement SHA-256  f14b30ffeb6b2ead02fb92f6518e57b9049e14fe03646208de9819ff84e1675f
```

## 5. Why the encoded-state induction is genuine

For a complete history of length `l`, assume the zeroth beta entry is exactly
`Pair(g,Pair(0,0))`. The induction invariant for every `i<=l` is

```text
exists A B T.
  StateAt(h,e,i,A,B,T) /\ IsGCD(g,A,B).
```

At index zero, the explicit state hypothesis and the already checked theorem
`is_gcd_zero_right` establish the invariant without computing a gcd.

For the successor case, `S i<=l` is exactly the strict index bound `i<l`.
The complete history relation itself supplies the genuine adjacent states

```text
StateAt(h,e,i,A,B,T),
StateAt(h,e,S i,C,D,U),
D=A,
C=D*Q+B,
B<D,
Cell(U,Q,T).
```

The induction hypothesis gives another state `(A',B',T')` at the same index.
`beta_at_unique` equates the packed codes; two applications of the already
checked `pair_code_injective` then prove `A'=A`, `B'=B`, and `T'=T`.
The existing gcd is rewritten along those equalities and transported through
the **actual transition equation** by `is_gcd_euclid_forward`. Thus it is a
gcd of `(C,D)` at `S i`.

At `i=l`, beta-state uniqueness identifies the invariant state with the
history's actual endpoint `(a,b,s)`. Therefore `IsGCD(g,a,b)` holds for the
*same* `g` encoded in the zeroth state.

Finally, the existing `EuclidExecution` separately certifies an output `G`.
Checked `is_gcd_unique` proves the encoded terminal value equals `G`, and the
state witness is rewritten accordingly. This is a genuine kernel proof of
terminal-state/output equality; host gcd computation never participates.

## 6. Exact immutable parent dependencies

All 13 external dependencies are independently checked members of immutable
Alpha v21:

```text
beta_at_unique
divides_linear_step
divides_remainder
euclidean_execution_exists
euclidean_execution_gcd_correct
euclidean_gcd_execution_linear_bound
is_gcd_euclid_backward
is_gcd_euclid_forward
is_gcd_unique
is_gcd_zero_right
le_refl
lt_to_le
pair_code_injective
```

Ten already occur in the frozen Alpha-v21 209-node advanced proof bundle.
Three checked parent theorems do not occur in that particular bundle:

```text
is_gcd_euclid_backward
is_gcd_unique
pair_code_injective
```

A future independently self-contained closure must source or rebuild their
genuine ordinary proof bodies; their inventory membership alone grants no
proof-bundle authority.

## 7. Remaining boundary

The previous semantic residual **terminal state equals reported gcd** is now
fully discharged. The campaign G101 target nevertheless remains **PARTIAL**:

```text
forall a b ell.
  b > 0 /\ BitLen(b,ell) ->
  exists g steps t.
    Execution(Euclid,(a,b),g,steps,t)
      /\ Gcd(a,b,g)
      /\ steps <= 2*ell+1.
```

No checked conservative `BitLen` relation currently exists. No theorem here
asserts the global logarithmic bound. The previously proved strict two-step
halving inequality and the now-anchored genuine execution provide the needed
structural substrate, but binary-length existence, functionality, halving
transport, and full logarithmic induction still require new original-kernel
proofs.

## 8. Sources and focused verification

```text
peano-lab/py/peano_lab/library/euclidean_gcd_transport_candidate.py
peano-lab/py/tests/test_euclidean_gcd_transport_candidate.py
```

```sh
cd peano-lab/py
python3 -m pytest -q --tb=short tests/test_euclidean_gcd_transport_candidate.py
```

The focused regression freezes every statement digest, authored tactic count,
proof-node receipt, depth, and dependency edge; replays all 20 bodies through
the unchanged original kernel; audits the exact anchored expanded AST; tests
every generated binder and malicious identifier; proves the crucial bodies
contain no classical `DNE`; rejects false conclusions, truncated scripts,
missing premises, and forged beta-state/transition/gcd/budget witnesses; and
explicitly checks the three honest out-of-artifact checked prerequisites.
