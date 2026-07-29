# The dependency ladder

A reusable library is a directed acyclic graph, not a long list sorted by
subject name. Each theorem should depend only on earlier, smaller interfaces,
and every high-level claim should expose the mathematical bridge it still
needs.

## Layer map

| Layer | Core interfaces | Current state |
|---|---|---|
| Equality | symmetry, transitivity, successor/add/multiply congruence, constructive equality decision | checked |
| Addition | identities, associativity, commutativity, cancellation, zero-sum rigidity | checked |
| Multiplication | identities, annihilation, distributivity, associativity, commutativity, zero product | checked core |
| Order | reflexivity, transitivity, trichotomy, incompatibility, addition monotonicity and cancellation | checked |
| Divisibility | units, zero, reflexivity, transitivity, addition/product closure, constructive decision, bounded nonzero common multiples | checked |
| Modular congruence | balanced equivalence laws and additive/multiplicative compatibility | reflexivity, symmetry, transitivity, addition, multiplication, both decomposition bridges, and bounded uniqueness checked; fixed mod-five residue ladder checked |
| Parity | even/odd dichotomy and arithmetic tables | useful future application, outside the closed current catalog |
| Division | quotient-remainder existence, uniqueness, block separation, and zero-remainder/divisibility bridges | checked |
| GCD/coprime | relational symmetry/projections/constructors, uniqueness, zero-right base, Euclidean invariance, existence, balanced Bézout, Gauss cancellation, product closure | checked through `coprime_mul_left` and `coprime_mul_right` |
| Primes | bounded factor search, primality decision, proper-factor descent, prime divisors, Euclid's lemma, infinitely many primes | checked through `prime_divisor_exists`, `euclid_prime_dvd_product`, and `prime_unbounded` |
| Factorization | sorted β-coded existence and canonical extensional uniqueness | finite-prefix recoding, exact Product traces, greatest-prime descent, canonical append, existence, uniqueness, and combined native FTA checked at this integration checkpoint; primitive lists remain absent; Lean list companion checked independently |

The generated `dependency-graph.mmd` is the exact graph for checked entries.
The research catalog is the larger design graph and gives every unproved node
a status and blocker.

## How an edge becomes a checked certificate

A dependency edge is no longer implemented by copying the dependency proof at
every hypothesis use. Replay first checks the dependency as a closed
certificate, then embeds it in a self-contained
`Cut(A, B, lemma, body)`. The kernel checks `lemma : A` once and checks
`body : B` under a new hypothesis `A`. Nested dependency edges become nested
Cuts, so the mathematical DAG remains visible as lexical sharing inside one
closed certificate.

This is not a trusted theorem environment. The Cut contains the complete
lemma proof and body proof; it contains no library name, hash, declaration
identifier, or callback. The object formula at each ladder node is unchanged,
and every final theorem is still checked from the empty context. The trusted
checker is larger by exactly this reviewed rule. The detailed boundary is in
{doc}`Self-contained proof sharing <proof-sharing>`.

## Why congruence comes first

The proof engine already has primitive equality rules such as congruence under
successor, addition, and multiplication. Named theorems such as `add_congr`
make these transformations reusable at the mathematical level:

$$
a=b\;\land\;c=d \quad\Longrightarrow\quad a+c=b+d.
$$

They are small, but they prevent later modular and divisibility proofs from
reconstructing the same transport scaffolding. They also give documentation a
stable name that can link code, artifacts, and concepts.

## Why cancellation precedes canonical residues

An equation $a+m q=b+m r$ can witness congruence without ordering either
$a$ or $b$. To prove uniqueness of canonical remainders, however, one needs
order bounds and cancellation. The intended chain is

$$
\begin{aligned}
&\text{additive cancellation}
\to \text{order monotonicity}
\to \text{division uniqueness}\\
&\to \text{canonical-remainder uniqueness}
\to \text{decidable fixed-modulus residue cases}.
\end{aligned}
$$

Fixed modulus proofs should therefore be downstream clients of generic
division and residue lemmas. They should not be copied into the foundation for
each numeral.

## The prime spine

The important dependency chain is not “define prime, then invoke FTA.” It is

$$
\begin{aligned}
\text{strong induction}
&\to \text{proper-factor descent}
\to \text{prime-divisor existence},\\
\text{division + gcd + Bézout}
&\to \text{Gauss cancellation}
\to \text{Euclid's lemma},\\
\text{prime-divisor existence + Euclid's lemma}
&\to \text{factorization existence and uniqueness}.
\end{aligned}
$$

Both arithmetic lines are now checked native chains. Constructive equality
decision feeds quotient-remainder-based divisibility decision. Induction on a
concrete bound then gives `factor_search_up_to`, which either verifies the
prime factor-pair condition throughout that bound or returns an explicit
nontrivial factor pair. `prime_or_composite` applies the divisor bound at
$B=n$; `prime_decidable` also handles zero and one explicitly.

Proper-factor descent is separate from that search decision:
`proper_factor_lt` proves that $n=cd$, $n\ne0$, and $d\ne1$ imply $c<n$.
`prime_divisor_exists_up_to` uses ordinary induction on an explicit upper
bound to recurse through such a factor, and `prime_divisor_exists` specializes
the bound to $n$. This implements formula-specific strong descent without a
predicate variable, a least-factor oracle, or classical DNE. All twelve new
certificates are intuitionistic.

The Euclid line uses the bounded theorem
`gcd_balanced_bezout_exists_up_to`, which carries both the full relational gcd
proof and four balanced coefficients through Euclidean descent. Its
unrestricted wrapper gives `coprime_balanced_bezout`; coefficient scaling and
the common-divisor bridge then give `gauss_coprime_cancel`. Finally,
`prime_divisor_eq_one_or_self` applies the prime factor dichotomy to a
relational gcd divisor of $p$, and `euclid_prime_dvd_product` uses its two
branches. Prime-divisor existence was proved independently; Euclid's lemma
does not supply it.

Infinitely many primes can be reached before a general factorial function.
It is enough to construct, for each bound, a common multiple of every number
from two to that bound and then take a prime divisor of one more than that
multiple. The constructive infrastructure for the first half is now checked:
`bounded_common_multiple_step` extends the invariant by one endpoint, and
`bounded_common_multiple_exists` constructs a nonzero common multiple of
every positive natural at most the supplied bound. The checked
`prime_unbounded` client applies prime-divisor existence to the successor of
that multiple. A divisor at or below the bound would divide the multiple as
well, hence divide one by the consecutive-number remainder lemma, contradicting
primality.

For FTA, the selected route uses greatest-prime-divisor descent to construct a
sorted factor sequence. Single-position β-value existence,
functionality, and the equivalence

$$
\operatorname{At}(b,c,i,x)
\quad\Longleftrightarrow\quad
x<M(c,i)\;\land\;b\equiv x\pmod{M(c,i)}
$$

are now checked through fully expanded PA formulas. The checked representation
layer now also includes constructive binary CRT for arbitrary nonzero coprime
moduli. `binary_crt_remainders` recovers the two directed remainder equations,
and `binary_crt_beta_pair` constructs one code realizing two bounded decoded
values. The last theorem assumes the two expanded β moduli are coprime.
The new conditional bridge proves that premise when

$$
j=i+g\qquad\text{and}\qquad g\mid c,
$$

and `binary_crt_beta_pair_of_gap_dvd` applies it directly. The condition is
not cosmetic: $c=1$ produces moduli $M(1,1)=3$ and $M(1,4)=6$, so arbitrary
members of the family are not pairwise coprime. Bounded common-multiple
existence supplies a $c$ divisible by every positive gap through a bound. The
checked bounded-prefix theorems now prove that the whole bounded modulus
family is pairwise coprime. Product coprimality and modulus descent support
`binary_crt_fold_step`, whose universal clause preserves every old congruence
modulo a divisor of the accumulated product while adding one new congruence.
`beta_accumulated_product_step` and `beta_crt_prefix_congruence_step` supply
the two successor halves, and `beta_crt_prefix_invariant_step` combines them.
Ordinary induction in `bounded_beta_crt_prefix_invariant` now constructs, for
each $k\le N$, a nonzero accumulated product divisible by every earlier beta
modulus, a value congruent to every earlier residue already decoded from the
supplied code $b$, and coprimality of that product with every future bounded
beta modulus.

The full-bound projection `bounded_beta_crt_for_existing_code` did not by
itself cross the recoding gate: its premise already said that each residue was
decoded from $b$. The later checked tranche closes that gap with an exclusive
cross-base recoding invariant and `beta_prefix_extend`, then builds exact
β-coded prefix-product traces and proves Product existence, functionality,
zero/successor decomposition, append, and prefix transport. Greatest-prime
descent plus canonical append yields factorization existence. Euclid's lemma,
product membership, sorted last-factor matching, and nonzero cancellation
yield uniqueness by length.

At this integration checkpoint the exact endpoints check as follows:

| Endpoint | Nodes | Depth | Cuts |
|---|---:|---:|---:|
| `prime_factorization_existence` | 43,973 | 98 | 1,328 |
| `prime_factorization_uniqueness` | 29,789 | 82 | 854 |
| `fundamental_theorem_of_arithmetic` | 73,767 | 99 | 2,184 |

The combined certificate has SHA-256
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`,
checks from the empty context, and passes the full live-use path under the
100,000-node/depth-256 cap. It uses PA1–PA6 and induction only, with no DNE.
Runtime integration is complete.

The theorem remains deliberately relational: Peano Lab has no primitive list
or multiset type, and uniqueness compares equal lengths and decoded entries,
not raw β-code equality. The checked `prime_unbounded` theorem is not a
dependency of FTA. Conventional integer-coefficient Bézout is not expressible
with the natural-only terms; the four-natural balanced theorem is checked.

## Admission invariants

Every checked node must satisfy all of these conditions:

- its name is stable, ASCII, lowercase snake case, and unique;
- its statement is closed;
- every dependency names an earlier node;
- the authored script uses the reviewed library-replay surface;
- replay is deterministic;
- every dependency assumption is discharged by a self-contained Cut whose
  formula and certificate are embedded in the final proof;
- the final certificate checks from the empty context;
- its exact node count and depth fit the live import bound;
- its source and documentation links resolve;
- generated artifacts reproduce byte for byte.

Literal Cut erasure is an optional, untrusted audit, not an admission
invariant. Although the formal expansion is `(λh. body) lemma`, the current
bidirectional checker and capture-sensitive beta reducer do not provide a
complete operational erasure path for every large certificate. An erased
artifact has authority only if it independently passes the kernel.

These invariants turn the dependency organization into an executable contract,
not merely a diagram in the documentation.
