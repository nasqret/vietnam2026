# G071 — total finite simple continued fractions in constructive arithmetic

Status: **nine actual, independently kernel-checked dependency-curried proof
bodies**, including the full positive-input G071 endpoint. Every external
prerequisite already has checked-use authority in immutable Alpha v19. This
isolated candidate neither enrolls nor promotes a theorem, changes Stable or
Alpha authority, installs a division/list function, extends the parser/kernel,
or assumes a classical principle.

## Exact major theorem

The final theorem `continued_fraction_positive_exists` has the surface shape

```text
forall a b.
  ~(a = 0) -> ~(b = 0) ->
  exists s. ContinuedFraction(a,b,s).
```

`ContinuedFraction` is **not** a new predicate. Its readable name abbreviates
the following hygienically expanded first-order formula:

```text
exists ap bp h e k.
  a = S ap /\
  b = S bp /\
  ReverseEuclidTrace(a,b,s,h,e,S k).
```

Thus both inputs have actual positive-predecessor witnesses, the quotient
certificate has a strictly positive length, and `s` is an actual tagged-cell
encoding of the entire forward simple-continued-fraction quotient list. The
stronger independently checked theorem
`continued_fraction_positive_nonempty_exists` additionally states `~(s = 0)`.

The exact final expanded statement has SHA-256
`d3b12766820bb64d9b1437e0ef96a9068c84d6d3176e066fe70f5a4f2d9e087d`.
Its only object-language symbols are `{0, S, +, *, =}` with first-order
quantifiers and intuitionistic logical connectives.

## Conservative definition stack

The already verified doubled-Cantor and tagged-cell encodings are

```text
Pair(x,y) = (x+y) * S(x+y) + (y+y)
Cell(q,t) = S(Pair(q,t))
Nil       = 0.
```

All three expressions are macros for displayed base-language terms or
equations, not added kernel constructors. A history state packs the dividend,
divisor, and complete quotient-list-so-far into one existing natural:

```text
Pack(a,b,s) = Pair(a, Pair(b,s)).
```

The existing conservative beta relation reads a history value:

```text
BetaAt(h,e,i,v) =
  (exists gap. gap + S v = S(S(i) * e)) /\
  (exists quotient. h = quotient * S(S(i) * e) + v).

StateAt(h,e,i,a,b,s) = BetaAt(h,e,i,Pack(a,b,s)).
```

Again both names expand completely; no beta or state symbol reaches the
kernel. Strict inequality is always the witnessed relation

```text
r < b  :=  exists gap. gap + S r = b.
```

The complete history relation is exactly

```text
ReverseEuclidTrace(a,b,s,h,e,l) :=
  exists g.
    StateAt(h,e,0,g,0,0) /\
    StateAt(h,e,l,a,b,s) /\
    forall i. i < l ->
      exists A B t C D u q.
        StateAt(h,e,i,A,B,t) /\
        StateAt(h,e,S i,C,D,u) /\
        D = A /\
        C = D*q + B /\
        B < D /\
        u = Cell(q,t).
```

The local `g` is the actual terminal Euclidean value. Its identification with
the already defined relational gcd is a useful future theorem, not an
additional claim silently assumed by G071.

One beta stream suffices: the list is bundled into each packed state, so every
transition checks both a genuine strictly bounded Euclidean division and the
exact tagged-cell constructor. The reverse history begins at terminal divisor
zero with the empty list. Moving outward prepends each quotient; therefore its
terminal list `s` has the ordinary **forward**, not reversed, continued-
fraction order.

For example,

```text
415 = 93*4 + 43
 93 = 43*2 +  7
 43 =  7*6 +  1
  7 =  1*7 +  0

reverse states:
  (1,   0, [])
  (7,   1, [7])
  (43,  7, [6,7])
  (93, 43, [2,6,7])
  (415,93, [4,2,6,7]).
```

The numeric examples in the focused audit build actual pairwise-coprime beta
moduli and actual Chinese-remainder history codes. They are semantic
regression fixtures only; the original independent intuitionistic kernel is
the sole proof authority.

## Constructive termination argument

1. Existing `beta_prefix_extend` initializes a real beta stream whose zeroth
   entry is `Pack(a,0,0)`. Zero length gives the complete divisor-zero trace.
2. Suppose the tail pair `(b,r)` already has a length-`l` trace and a real
   division witnesses `a = b*q+r` with `r < b`. Existing `cell_constructor`
   constructs `s = Cell(q,t)`. One application of `beta_prefix_extend` writes
   `Pack(a,b,s)` at index `S l` while preserving the entire previous prefix.
   Constructive bounded-index splitting checks the new final transition and
   preserves every previous transition, including both adjacent beta states.
3. Induction on a natural bound `B` proves that every `b <= B` has a complete
   trace for every `a`. At bound zero, constructive `le_zero` reduces to the
   empty case. At successor bound, constructive `le_eq_or_lt` either lowers
   the bound directly or identifies `b = S B`. In the latter case the already
   checked division theorem produces `q,r` with `r < b`; constructive
   successor cancellation yields `r <= B`. The induction hypothesis builds
   the tail trace, and the previous extension lemma prepends `q`.
4. Reflexivity supplies the bound `B=b`, establishing total traces for **all**
   natural inputs, including `(0,0)`, `(a,0)`, and `(0,b)`.
5. For nonzero `b`, one first division plus the total tail constructor yields
   an explicit successor trace length. Existing `cell_nonzero` proves the
   resulting forward list is not nil. Existing `nonzero_is_succ` supplies the
   actual positive predecessors demanded by the exact G071 endpoint.

No well-founded recursion rule, minimization axiom, Markov principle,
excluded-middle schema, classical contradiction rule, or host arithmetic
oracle appears in this argument.

## Independently checked proof microsteps

| Exact candidate theorem | Direct dependencies | Commands | Kernel proof nodes | Depth |
| --- | ---: | ---: | ---: | ---: |
| `continued_fraction_initial_state_exists` | 1 | 11 | 33 | 19 |
| `continued_fraction_empty_trace` | 0 | 16 | 25 | 16 |
| `continued_fraction_empty_trace_exists` | 2 | 8 | 19 | 14 |
| `continued_fraction_trace_extend` | 7 | 133 | 194 | 57 |
| `continued_fraction_trace_exists_up_to` | 6 | 100 | 200 | 38 |
| `continued_fraction_trace_exists` | 2 | 11 | 11 | 9 |
| `continued_fraction_nonzero_divisor_exists` | 4 | 49 | 64 | 28 |
| `continued_fraction_positive_nonempty_exists` | 2 | 39 | 43 | 23 |
| `continued_fraction_positive_exists` | 1 | 14 | 16 | 11 |

The complete candidate stack has **nine theorems**, **25 exact direct
dependency edges**, **381 actual tactic commands**, and **605 checked kernel
proof-body nodes**. Its largest proof has **200 nodes**; maximum proof depth
is **57**. The ordered theorem-name SHA-256 is
`3e573dc07284357171fe7781f575d3a8939331ae15b6f96011f292efae4a34eb`.

The complete preexisting checked Alpha-v19 authority is

```text
beta_prefix_extend
cell_constructor
cell_nonzero
division_remainder_exists
finite_lt_succ_eq_or_lt
le_eq_or_lt
le_of_succ_le_succ
le_refl
le_succ_self
le_zero
lt_of_lt_of_le
nonzero_is_succ
succ_le_succ
zero_add
```

`cell_constructor` and `cell_nonzero` are already checked Alpha-only results;
the other twelve inputs are already Stable. Every declared dependency is
either one of these preexisting checked theorems or a strictly earlier
candidate row. No new theorem is admitted merely by importing this module.

The implementation factory is
`peano_lab.library.continued_fraction_candidate.make_continued_fraction_candidate_theorems`.
The focused audit `tests/test_continued_fraction_candidate.py` checks frozen
expanded formulas, dependency order and trust boundaries, every original-
kernel proof, first-order definition hygiene and alpha-equivalence, exact
positive-input and successor-length witnesses, absence of `DNE`, independent
rejection of false conclusions/truncated scripts/missing dependencies,
adversarial division/remainder/cell mutations, actual beta-coded histories,
correct forward quotient order, rational reconstruction, and every zero-input
boundary.
