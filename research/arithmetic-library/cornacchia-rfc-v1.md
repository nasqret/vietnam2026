# Cornacchia's complete prime two-square algorithm in constructive arithmetic

This additive family proves the actual algorithmic statement of G107, not a
two-square representation accompanied by an unrelated Euclidean trace. It
constructs a root of minus one, follows the quotient/remainder and absolute
coefficient recurrences from that root, stops at the first positive remainder
whose square is below the prime, and proves that the returned remainder and
coefficient are the two-square representation.

The implementation is
`peano-lab/py/peano_lab/library/cornacchia_candidate.py`, with factory
`make_cornacchia_candidate_theorems`. Its 30 dependency-ordered, ordinary HA
proof bodies use only earlier rows and the immutable Alpha-v26 parent of
2,138 checked theorems. No historical definition, theorem, certificate,
catalogue, kernel, tactic implementation, Stable membership, or publication
workflow is changed.

## Exact endpoints

All variables range over naturals. Strict order is the existing gap relation
`a<b := exists k. k+S a=b`. Congruence is the existing balanced relation
`ModEq(p,a,b) := exists k l. a+p*k=b+p*l`. Integer subtraction is not added.

```
CornacchiaRoot(p,z) :=
  Prime(p) /\ z != 0 /\ z < p /\ exists k. z*z+1=p*k.

cornacchia_prime_two_squares_complete:
  forall p.
    Prime(p) -> (exists k. p=4*k+1) ->
    exists z R T h e l.
      CornacchiaTrace(p,z,R,T,h,e,l) /\ p=R*R+T*T.
```

The quantified `z` is the root that initializes this same trace. The
quantified `R,T` are the decoded coordinates of its actual terminal state.
They are not independent representation witnesses. The stronger root-input
endpoint is:

```
cornacchia_from_any_bounded_negative_one_root:
  forall p z.
    CornacchiaRoot(p,z) ->
    exists R T h e l.
      CornacchiaTrace(p,z,R,T,h,e,l) /\ p=R*R+T*T.
```

Thus the construction works from every positive bounded root of minus one,
not only from a root preselected for successful termination. It also covers
`p=2,z=1`. The prime-one-modulo-four root constructor uses the already checked
bounded root-of-minus-one theorem, not the already checked two-square
representation theorem.

## A genuine finite execution certificate

A state is `(a,r,u,t,q)`: two consecutive Euclidean remainders, their
absolute coefficients, and the actual next quotient. The conservative
state relation stores all five components in one beta value. It uses the
same doubled-Cantor polynomial already used by the continued-fraction
campaign:

```
Pair(x,y) = (x+y)*(x+y+1)+2*y
Pack(a,r,u,t,q) = Pair(Pair(a,r),Pair(Pair(u,t),q))
StateAt(h,e,i,a,r,u,t,q) := Beta(h,e,i,Pack(a,r,u,t,q)).
```

`Pair` and `Pack` here describe pure natural arithmetic terms, not added
kernel symbols or opaque encoders. The frozen beta relation is the actual
bounded remainder relation for modulus `1+(i+1)*e`.

As in the existing continued-fraction history, chronological time runs from
index `l` down to zero. Each adjacent transition has full decoded states
`(a,r,u,t,q)` at `S i` and `(A,R,U,T,Q)` at `i`, satisfying exactly:

```
A=r,       U=t,
a=r*q+R,   R<r,
T=q*t+u,   p<r*r.
```

Both quotients are stored in their respective states. `Q` is the following
step's quotient; at the terminal state it is zero, a sentinel rather than
an additional division. The initial state is exactly `(p,z,0,1,q)`. The
terminal state is `(A,R,U,T,0)` with `R != 0`, `T != 0`, and `R*R<p`.

Every index `i<l` has the displayed adjacent transition. Hence there is no
gap in the history, and no skipped quotient or coefficient update. Every
preterminal current remainder is strictly above the square-root threshold;
the terminal remainder is below it. This is a first-stop certificate, not
merely an arbitrary later small remainder. A prime is not a natural square,
so no equality case is silently discarded.

For example, the root `z=8` at `p=13` produces the chronological states

```
(13,8,0,1,1) -> (8,5,1,1,1) -> (5,3,1,2,0).
```

The output is `R=3,T=2`, with `13=3^2+2^2`. Returning `(2,3)` would still be
a representation of 13 but would not be the output recorded by this trace.
The tests explicitly distinguish these claims. The zero-step boundary is
also real: `p=5,z=2` starts already below the threshold and returns `(2,1)`.

## Constructive arithmetic invariant and termination

The invariant for a current state `(a,r,u,t)` contains:

```
CornacchiaRoot(p,z),   r != 0,   r<a,   t != 0,
p<a*a,                p=a*t+r*u,      Coprime(a,r),

(ModEq(p,a,z*u) /\ ModEq(p,r+z*t,0))
  \/
(ModEq(p,a+z*u,0) /\ ModEq(p,r,z*t)).
```

The disjunction is the two explicit alternating coefficient signs in
natural balanced congruence. The initial state `(p,z,0,1)` satisfies the
second branch. A real division `a=r*q+s`, together with `T=q*t+u`, toggles
the branches. Both sign transports are proved by ordinary congruence
addition, multiplication, symmetry, and transitivity.

The same actual recurrences preserve the exact identity
`p=r*T+s*t`. Positivity is proved before cancellation: `r<a` makes the
quotient positive, and positive `q,t` make `T` positive. Gcd transport makes
`r,s` coprime. Above the threshold, a zero next remainder would force `r=1`,
contradicting `p<r*r` and the positivity of the prime. Thus the next current
remainder is positive and strictly smaller.

At a stopping state, the previous square bound and cross identity give
`t<a`: otherwise `a*a<=a*t<=p`, contradicting `p<a*a`. Consequently
`t*t<a*t<=p`. The alternating congruence and `z*z+1` being a multiple of `p`
make `r*r+t*t` a multiple of `p`. The norm is positive and strictly below
`2*p`, so the already checked bounded-multiple theorem yields exactly
`p=r*r+t*t`.

Totality is a genuine natural induction on an arbitrary upper bound `B`
for the current remainder:

```
forall B r. r<=B -> forall p z a u t.
  CornacchiaStateInvariant(p,z,a,r,u,t) ->
  exists R T h e l.
    CornacchiaEuclideanRun(p,a,r,u,t,R,T,h,e,l) /\ p=R*R+T*T.
```

At `B=0`, the positive remainder contradicts its bound. At the successor,
the constructive prime-square dichotomy either gives a stopped state or
gives an actual Euclidean division. The successor remainder is at most
`B`, so the induction hypothesis supplies its entire stopped history.
`beta_prefix_extend` then appends the actual predecessor state to that same
reverse-indexed history, preserving all old decoded entries and transitions.
The final history therefore comes from the induction, not from a supplied
successful trace. Specializing `B=r` proves termination from any invariant
state; the root constructor and initial invariant prove the full endpoint.

```
checked bounded root of minus one + prime square dichotomy
                           |
        initial rooted arithmetic/sign/gcd invariant
                           |
 actual division + coefficient recurrence + invariant transport
                           |
 positive decreasing remainder + bounded natural induction
                           |
     actual beta-history extension + guarded first stop
                           |
           returned norm positive, divisible by p, <2p
                           |
              actual complete trace with p=R^2+T^2
```

## Conservative definition DAG

Seven public relation builders expose the reusable layers below. Arguments
and binder tags are validated, duplicate arguments and generated-name
capture are rejected, and changing a binder tag preserves the native AST
up to bound-name erasure. The fully expanded statements use only the
existing first-order arithmetic syntax.

| New relation | Arguments | Direct abbreviation dependencies |
|---|---|---|
| `CornacchiaRoot` | `(p,z)` | `Prime`, `Lt`, `Divides` |
| `CornacchiaAlternatingCongruences` | `(p,z,a,r,u,t)` | `ModEq` |
| `CornacchiaStateInvariant` | `(p,z,a,r,u,t)` | `CornacchiaRoot`, `Lt`, `Coprime`, `CornacchiaAlternatingCongruences` |
| `CornacchiaStateAt` | `(h,e,i,a,r,u,t,q)` | `Beta`, with the displayed pure arithmetic tuple term |
| `CornacchiaTransitionAt` | `(p,h,e,i)` | `CornacchiaStateAt`, `Lt` |
| `CornacchiaEuclideanRun` | `(p,a,r,u,t,R,T,h,e,l)` | `CornacchiaStateAt`, `CornacchiaTransitionAt`, `Lt` |
| `CornacchiaTrace` | `(p,z,R,T,h,e,l)` | `CornacchiaRoot`, `CornacchiaEuclideanRun` |

The implementation's names are the corresponding snake-case builders, all
with keyword `tag`. Stable definition IDs belong to additive release
integration. No old relation is redefined. In particular, the termination
certificate does not alter the frozen continued-fraction or gcd trace.

## Inventory, checks, and exact boundary

The 30 ordered theorem names are pinned in
`peano-lab/py/tests/test_cornacchia_candidate.py`. Their ordered-name SHA-256
is `8c7bb874131422c19eadc54046271bccfe638d138dddaaf971cb8683791abd02`.
There are 112 declared dependency edges, 1,190 tactic commands, and 2,326
original-kernel body proof nodes. The largest body has 210 nodes, maximum
depth is 69, and the largest expanded statement is 31,110 bytes.

Important exact statement hashes:

| Theorem | SHA-256 |
|---|---|
| `cornacchia_root_exists` | `f49a5afb5955e03851ca818a143cf6958d3f5826d797cf5a7f8af0c3f35ca834` |
| `cornacchia_invariant_euclidean_step` | `59ad5af0d1727b7794bcba6f4b1f426063d8360a2f29a3f92813b59cfd3d0c0f` |
| `cornacchia_trace_extend` | `78e38912134bd98c5e7317551e9a44631ff824bb573daea139bf3b2d3940a5b0` |
| `cornacchia_complete_from_invariant_up_to` | `948b1f1dd0e1b07d862ac03d20234143e5aeb47a5ef4ac62402a9bd9192bdbfe` |
| `cornacchia_from_any_bounded_negative_one_root` | `b473b37393a7202423d12f928eacdeda26ce6c851793864e2431eab1fa713195` |
| `cornacchia_prime_two_squares_complete` | `becd01e6f073d37e512d385ffbc5e4e929ea3113f9d900fcc189718fc83eefc7` |

The body-check harness authenticates the immutable Alpha-v26 catalogue
bytes against SHA-256
`969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534`.
It reconstructs the exact parent formulas and scripts without importing
all historical release registries. This reduces authoring memory, not
the logical checking standard. Every new row is checked in a separate
one-theorem microbatch, with declared dependencies as ordinary hypotheses.

```
PYTHONPATH=peano-lab/py python3 -m pytest -q \
  peano-lab/py/tests/test_cornacchia_candidate.py
```

Tests cover original-kernel replay, false-conclusion/truncation/missing-
dependency mutations, exact endpoint ASTs, all seven definitions' hygiene,
the actual five-component encoding, adjacent history topology, first-stop
guards, genuine induction and beta extension, and both roots at every small
prime where a root exists. Examples are supplementary regression checks,
not mathematical authority. Result: **260 tests pass**.

The scope is the complete prime two-square algorithm and its actual
constructed executions. It does not claim general Cornacchia for arbitrary
`x^2+D*y^2`, composite-modulus completeness, asymptotic running-time bounds,
or uniqueness of an externally supplied trace as a separate formal theorem.
Dependency-closed bundle assembly and independent Lean replay are still
release integration gates. The local body receipts are not themselves
Alpha admission, Lean verification, or deployment.
