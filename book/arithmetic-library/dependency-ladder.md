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
| Order | reflexivity, transitivity, trichotomy, incompatibility, addition monotonicity and cancellation | checked |
| Divisibility | units, zero, reflexivity, transitivity, addition and product closure | checked |
| Modular congruence | balanced reflexivity and symmetry; additive and multiplicative compatibility | first two checked; transitivity/compatibility planned; fixed mod-five residue ladder checked |
| Parity | even/odd dichotomy and arithmetic tables | planned and expressible |
| Division | quotient-remainder existence, uniqueness, block separation, and zero-remainder/divisibility bridges | checked |
| GCD/coprime | relational symmetry/projections/constructors, uniqueness, zero-right base, Euclidean invariance, existence, balanced Bézout, Gauss cancellation | checked through `gauss_coprime_cancel` |
| Primes | characterization, prime divisors, Euclid's lemma, infinitely many primes | `prime_two`, `prime_divisor_eq_one_or_self`, and `euclid_prime_dvd_product` checked; prime-divisor existence and the remaining spine planned |
| Factorization | existence and uniqueness up to permutation | β representation selected; Peano proof spine pending; Lean companion checked |

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

The middle line is now a checked native chain. The bounded theorem
`gcd_balanced_bezout_exists_up_to` carries both the full relational gcd proof
and four balanced coefficients through Euclidean descent. Its unrestricted
wrapper gives `coprime_balanced_bezout`; coefficient scaling and the
common-divisor bridge then give `gauss_coprime_cancel`. Finally,
`prime_divisor_eq_one_or_self` applies the prime factor dichotomy to a
relational gcd divisor of $p$, and `euclid_prime_dvd_product` uses its two
branches. Prime-divisor existence remains an
independent bounded-search milestone; Euclid's lemma does not supply it.

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
