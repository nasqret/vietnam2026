# The dependency ladder

A reusable library is a directed acyclic graph, not a long list sorted by
subject name. Each theorem should depend only on earlier, smaller interfaces,
and every high-level claim should expose the mathematical bridge it still
needs.

## Layer map

| Layer | Core interfaces | Current state |
|---|---|---|
| Equality | symmetry, transitivity, successor/add/multiply congruence | checked |
| Addition | identities, associativity, commutativity, cancellation, zero-sum rigidity | checked core; more orientations planned |
| Multiplication | identities, annihilation, distributivity, associativity, commutativity, zero product | checked core |
| Order | reflexivity, transitivity, antisymmetry, totality, zero least, successor bound | checked core; monotonicity planned |
| Divisibility | units, zero, reflexivity, transitivity, addition and product closure | checked |
| Modular congruence | equivalence relation, additive and multiplicative compatibility | definition and proof plan recorded |
| Parity | even/odd dichotomy and arithmetic tables | planned and expressible |
| Division | quotient-remainder existence and uniqueness | planned and expressible |
| GCD/coprime | relational gcd, uniqueness, Bézout, Gauss cancellation | planned; signed-pair encoding required |
| Primes | characterization, prime divisors, Euclid's lemma, infinitely many primes | `prime_two` checked; general spine planned and expressible |
| Factorization | existence and uniqueness up to permutation | blocked on finite-factorization representation |

The generated `dependency-graph.mmd` is the exact graph for checked entries.
The research catalog is the larger design graph and gives every unproved node
a status and blocker.

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

Infinitely many primes can be reached before a general factorial function.
It is enough to construct, for each bound, a common multiple of every number
from two to that bound and then take a prime divisor of one more than that
multiple. This remains a first-order existence argument.

## Admission invariants

Every checked node must satisfy all of these conditions:

- its name is stable, ASCII, lowercase snake case, and unique;
- its statement is closed;
- every dependency names an earlier node;
- the authored script uses the reviewed library-replay surface;
- replay is deterministic;
- dependency assumptions are eliminated;
- the final certificate checks from the empty context;
- its exact node count and depth fit the live import bound;
- its source and documentation links resolve;
- generated artifacts reproduce byte for byte.

These invariants turn the dependency organization into an executable contract,
not merely a diagram in the documentation.
