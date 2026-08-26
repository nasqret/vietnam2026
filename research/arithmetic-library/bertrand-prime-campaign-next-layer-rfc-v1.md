# Prime-distribution campaign: the first two strict-Bertrand extensions

Status: thirteen independently kernel-checked, dependency-curried theorem
bodies above immutable **Alpha v19**. These results are not part of v19; any
new enrollment, independently checked empty-context proof bundle, and
checked-use promotion require their own reviewed release gate.

Grand-campaign family: **F03**, “Prime distribution, primitive divisors,
PNT, and Dirichlet.” This tranche closes the mathematical candidate bodies for
its two previously ready objectives **G023** and **G024**, in actual
prerequisite order. It does not claim a proof of either goal until its exact
root has also passed the separate release-admission procedure.

The implementation is
`peano-lab/py/peano_lab/library/bertrand_prime_campaign_candidate.py`;
the exhaustive original-kernel, definition-hygiene, adversarial-mutation, and
witness tests are
`peano-lab/py/tests/test_bertrand_prime_campaign_candidate.py`.

## 1. Conservative mathematical definitions

The trusted language remains exactly the unchanged first-order
Heyting-arithmetic signature `{0, S, +, *, =}`. The names below are display
abbreviations, not trusted predicates, axioms, sorts, implicit Lean facts,
or externally supplied computational oracles.

```text
Lt(a,b) := ∃g. g + S(a) = b

Prime(p) := p ≠ 1 ∧ ∀x y. p = x*y → x = 1 ∨ y = 1

BetaAt(b,c,i,a) :=
  (∃h. h + S(a) = S(S(i)*c)) ∧
  (∃q. b = q*S(S(i)*c) + a)

BertrandWindow(n,p) :=
  Prime(p) ∧ Lt(n,p) ∧ Lt(p,n+n)

PowerValuationOne(p,C) := PowerValuation(p,C,1)

BertrandChain(b,c,n,k) :=
  BetaAt(b,c,0,n) ∧
  ∀i. Lt(i,k) → ∃a p.
    BetaAt(b,c,i,a) ∧
    BetaAt(b,c,S(i),p) ∧
    BertrandWindow(a,p)
```

`PowerValuation` is the existing witnessed finite power-divisor maximum,
expanded through its already checked beta-coded multiplication trace. The
literal exponent `1` replaces exactly the six known occurrences of a fresh,
capture-checked exponent marker. The resulting formula does not contain a
new valuation symbol.

`b,c` are two explicit natural witnesses for the standard Gödel-beta sequence
code. Thus the represented sequence has exactly `k+1` relevant entries; no
infinite sequence, dependent-choice axiom, or implicit list type is present.

The definition graph is acyclic:

```text
                         first-order HA
                         /      |      \
                       Lt     Prime    BetaAt
                         \      /         |
                        BertrandWindow    |
                               \          |
                                BertrandChain

                    beta-coded finite products
                               |
                         PowerValuation
                               |
                       PowerValuationOne
```

Every public definition builder validates all caller identifiers and tag
names, rejects reserved words, interpolation, compound caller terms, and
collisions with generated binders. Different safe tags produce syntactically
different text but exactly the same alpha-equivalent kernel formula.

## 2. G023: exact prime divisors in central-binomial windows

The exact new root is
`central_binom_prime_divisor_multiplicity_one_exists`:

```text
∀n. 1<n → ∃p C.
  Prime(p) ∧ n<p ∧ p<n+n ∧
  CentralBinom(n,C) ∧ PowerValuation(p,C,1).
```

`CentralBinom(n,C)` expands to the existing complete witnessed Pascal-table
relation `Choose(n+n,n,C)`. Both interval bounds are strict. In particular,
the result is stronger than the checked strict Bertrand theorem: it supplies
the actual binomial value and certifies that the selected prime divides it
**exactly once**, not merely that some prime exists in the interval.

The proof has seven genuine constructive layers:

1. A prime `n<p<2n` divides `Choose(2n,n)` by the checked two-sided
   binomial prime-divisibility theorem.
2. `n<p` and `2≤p` imply `2n<2p≤p²`, entirely through witnessed order
   and multiplication laws.
3. The checked central-binomial square-tail theorem bounds the valuation by
   one.
4. Divisibility and positivity of the central coefficient make that
   valuation nonzero.
5. Antisymmetry of witnessed natural order gives the exact exponent `1`.
6. Totality of prime-power valuation supplies its actual witness and
   transports all six exponent occurrences to the literal `1`.
7. Strict Bertrand and central-binomial totality jointly construct the two
   existential witnesses `p,C`.

No factorial valuation, square-root oracle, analytic estimate, or
nonconstructive prime selection is assumed.

## 3. G024: arbitrary finite witnessed prime chains

The exact new root is `iterated_bertrand_prime_chain_exists`:

```text
∀n k. 1<n → ∃b c. BertrandChain(b,c,n,k).
```

Its proof establishes a stronger induction invariant:

```text
∀n k. 1<n → ∃b c a.
  BertrandChain(b,c,n,k) ∧ BetaAt(b,c,k,a) ∧ 1<a.
```

The zero-step case builds an actual singleton beta code. At each successor:

1. Extract the guarded terminal value `a` from the induction invariant.
2. Apply the independently checked **strict** Bertrand root to obtain
   `Prime(p) ∧ a<p ∧ p<2a`.
3. Apply the checked beta-prefix-extension theorem to append `p`, producing a
   new code and scale together with transport proofs for all old entries.
4. Split any new step index constructively into the new last index or a prior
   index; preserve every old source entry, target entry, primality proof, and
   strict bound.
5. Transport `1<a` across `a<p` to establish `1<p` for the next induction
   step.

The proof uses genuine object-level HA induction over **arbitrary** `k`.
Numerical examples only illustrate the witness; a finite set of computed
chains is never substituted for the universally quantified derivation.

## 4. Exact dependency-ordered proof-body receipt

| Layer | Theorem | Dependencies | Commands | Proof nodes | Depth |
|---:|---|---:|---:|---:|---:|
| 1 | `bertrand_window_prime_divides_central_binom` | 2 | 22 | 52 | 27 |
| 1 | `bertrand_window_prime_square_exceeds_double` | 6 | 42 | 54 | 20 |
| 2 | `bertrand_window_central_valuation_at_most_one` | 5 | 45 | 56 | 27 |
| 2 | `bertrand_window_central_valuation_nonzero` | 3 | 39 | 50 | 24 |
| 3 | `bertrand_window_central_valuation_equals_one` | 4 | 41 | 55 | 28 |
| 4 | `bertrand_window_central_valuation_one` | 3 | 46 | 147 | 30 |
| 5 | `central_binom_prime_divisor_multiplicity_one_exists` | 3 | 32 | 47 | 22 |
| 1 | `bertrand_chain_singleton_code_exists` | 1 | 11 | 33 | 19 |
| 2 | `bertrand_chain_singleton_exists` | 2 | 19 | 25 | 17 |
| 1 | `bertrand_chain_successor_preserves_guard` | 1 | 12 | 38 | 22 |
| 1 | `bertrand_chain_prefix_extend` | 5 | 83 | 116 | 35 |
| 3 | `bertrand_chain_prefix_terminal_exists` | 4 | 55 | 76 | 25 |
| 4 | `iterated_bertrand_prime_chain_exists` | 1 | 15 | 18 | 11 |

```text
New isolated theorem specifications: 13
Actual direct dependency edges: 40
Checked Alpha-v19 external prerequisites: 25 distinct names
Primitive intuitionistic tactic commands: 462
Original-kernel dependency-curried proof nodes: 767
Maximum proof-body nodes: 147
Maximum proof-body depth: 35
Double-negation-elimination steps: 0
Trusted-language or kernel changes: 0

Ordered theorem-name SHA-256:
184855ae530d73c6f6067b88c306fe6b64fc471b659cecf66eaeaea20ba62021

G023 exact statement SHA-256:
d0899600b713e85d0cb20997ada171ce02b6a6e8316364ed4ab603389724f5a8

G024 exact statement SHA-256:
02c52d46368ec2320c8d316b41d37ef7c1dbb5de32dbd15247325a17382650d2
```

The focused suite independently checks all thirteen real proofs; rejects a
false conclusion, a truncated proof script, and a missing declared dependency
for **every** theorem; audits definition capture/injection and
alpha-equivalence; checks exact root quantifier structure; verifies central
prime multiplicity for twelve nontrivial examples; constructs actual
CRT-derived beta codes for eight arbitrary-length prime-chain examples; and
rejects eight invalid, composite, or non-strict boundary cases.

```text
python3 -m pytest -q \
  peano-lab/py/tests/test_bertrand_prime_campaign_candidate.py

91 passed
```

These are dependency-curried body receipts, not empty-context release
certificates. The unchanged immutable Alpha-v19 catalog, Stable edition,
historical proof bundles, and old theorem statements are never modified by
this candidate tranche.
