# Primes and unique factorization

Prime numbers are a major destination of the library, but they are not a
primitive. Their useful theory rests on divisibility, order, induction,
division, and gcd.

## A first-order prime definition

Writing $d\mid p$ for its existential expansion, define

$$
\operatorname{Prime}(p)
\;:\!\Longleftrightarrow\;
p\ne1\land\forall a\,b.\bigl(p=a\cdot b\to a=1\lor b=1\bigr).
$$

This factor-pair definition is stateable in Peano Lab now and is equivalent
over the naturals to the usual divisor formulation. A readable `Prime p`
surface form would be only a macro; the stored theorem and final checker target
contain the expanded quantifiers and multiplication equality.

The first concrete instance is already checked:

```text
prime_two : ~(2 = 1) /\ forall a b. 2 = a * b -> a = 1 \/ b = 1
```

Its proof depends on `two_large_factors_impossible`; neither theorem adds a
trusted primality oracle or a primitive `Prime` atom.

The checked division layer now supplies constructive quotient-remainder
existence and uniqueness. The checked `prime_divisor_eq_one_or_self` theorem
says every divisor of a prime is one or the prime itself. The runtime also
contains `euclid_prime_dvd_product`: a prime dividing $a b$ divides $a$ or
$b$. The complementary constructive search branch is now checked as well.

## The checked constructive prime-search DAG

The new milestone contains twelve entries. It is a dependency DAG rather than
one linear proof:

$$
\begin{aligned}
\texttt{eq\_decidable}
&\to \texttt{multiple\_decidable\_nonzero}
\to \texttt{multiple\_decidable},\\
\texttt{eq\_decidable}+\texttt{multiple\_decidable\_nonzero}
  +\texttt{factor\_property\_succ}
&\to \texttt{factor\_search\_up\_to}
\to \texttt{prime\_or\_composite},\\
\texttt{eq\_decidable}+\texttt{prime\_or\_composite}
  +\texttt{prime\_nonzero}
&\to \texttt{prime\_decidable},\\
\texttt{prime\_or\_composite}+\texttt{proper\_factor\_lt}
&\to \texttt{prime\_divisor\_exists\_up\_to}
\to \texttt{prime\_divisor\_exists}.
\end{aligned}
$$

`factor_nonzero_left` is an independently reusable product boundary lemma;
the current optimized `proper_factor_lt` certificate proves the needed
nonzero-factor subclaim locally instead of importing that whole certificate.
The exact admitted metrics are:

| Checked theorem | Constructive role | Nodes/depth | Cuts |
|---|---|---:|---:|
| `eq_decidable` | decide equality by nested induction | 48 / 20 | 0 |
| `multiple_decidable_nonzero` | decide whether a nonzero divisor divides a number by testing the unique remainder | 1,242 / 61 | 32 |
| `multiple_decidable` | add the explicit zero-divisor case | 1,352 / 64 | 35 |
| `factor_property_succ` | extend a bounded factor property across one new endpoint | 150 / 20 | 5 |
| `factor_search_up_to` | verify all bounded factor pairs or return a nontrivial pair | 1,925 / 69 | 56 |
| `prime_or_composite` | instantiate bounded search at the number itself | 2,038 / 71 | 59 |
| `prime_nonzero` | derive nonzeroness from the expanded prime formula | 49 / 11 | 2 |
| `prime_decidable` | decide the expanded prime formula, including zero and one | 2,194 / 73 | 64 |
| `factor_nonzero_left` | refute a zero left factor of a nonzero product | 37 / 12 | 1 |
| `proper_factor_lt` | turn a nonunit cofactor into strict factor descent | 468 / 26 | 16 |
| `prime_divisor_exists_up_to` | perform strong descent by ordinary induction on an explicit bound | 2,931 / 78 | 91 |
| `prime_divisor_exists` | specialize that bound to the number itself | 2,977 / 80 | 94 |

In particular, the public endpoint proves, in fully expanded syntax, that
every $n\ne0,1$ has a prime $p$ and a witness $k$ with $n=pk$.
`prime_divisor_exists_up_to` does not invoke a polymorphic strong-induction
principle: its concrete motive is proved by ordinary induction on $B$, and a
nontrivial factor is shown smaller before the induction hypothesis is used.
All twelve certificates check in the default intuitionistic kernel and contain
no DNE node. Primes above every bound remain a planned expressible theorem;
prime-divisor existence no longer does.

## GCD without a gcd function

Use the relational specification

$$
\operatorname{IsGCD}(g,a,b)
$$

to say that $g$ divides $a$ and $b$, and every common divisor divides $g$.
The checked API now provides symmetry, both divisibility projections, the
greatest-common-divisor projection, a constructor when one input divides the
other, `is_gcd_unique`, and constructive existence for every pair. The
bounded `gcd_exists_up_to` proof performs formula-specific Euclidean descent;
`gcd_exists_relational` specializes its bound to the second input. Both check
from the empty context. The uniqueness proof uses the checked
`multiple_antisymm`. The unit bridge proves `mul_eq_one_components`, divisors of one,
coprimality with one on both sides, and both directions between expanded
coprimality and `IsGCD(1,a,b)`.

A balanced four-natural Bézout equation now supplies the checked bridge from
gcd existence to Gauss cancellation without extending the kernel language.
The runtime simultaneously constructs a relational gcd and balanced
coefficients, specializes the result to coprime inputs, and proves

$$
\operatorname{Coprime}(a,b)\land a\mid bz\Longrightarrow a\mid z
$$

as `gauss_coprime_cancel`.

The exact checked statements, certificate metrics, bounded-induction
construction, and balanced coefficient transport are developed in
{doc}`GCD and balanced Bézout construction <gcd-and-bezout>`.

The checked proof of Euclid's lemma takes a relational gcd $g$ of $p$ and
$a$. Since $g\mid p$, `prime_divisor_eq_one_or_self` gives $g=1$ or $p=g$:

$$
\begin{array}{rcl}
g=1 &\Longrightarrow& \operatorname{Coprime}(p,a)
  \Longrightarrow p\mid ab\Rightarrow p\mid b,\\
p=g &\Longrightarrow& p\mid a.
\end{array}
$$

The first branch is Gauss cancellation; the second uses the gcd's checked
divisibility projection. This proof is constructive and its closed shared
certificate has 5,382 nodes and depth 55.

## Existence and uniqueness are different theorems

The checked `prime_or_composite`, `proper_factor_lt`, and
`prime_divisor_exists` theorems now supply the basic arithmetic descent needed
for factorization existence. For the selected sorted encoding, the next
critical arithmetic gate is greatest-prime-divisor descent: recursively factor
the complementary quotient and append a greatest prime factor while preserving
sortedness. Uniqueness can use the checked Euclid lemma to match one prime from
one factorization with a prime in the other, cancel it, and continue.

That familiar paper proof quietly quantifies over finite products. An honest
formal statement needs a representation and theorems for:

- finite collections of natural numbers;
- the product of a collection;
- “every entry is prime”;
- permutation or multiplicity equality;
- deletion of a matched prime and product cancellation.

Peano Lab has no primitive data interface for these objects. The project now
has two deliberately separate results:

- a selected conservative Peano representation, using sorted Gödel β-coded
  factor sequences and a β-coded prefix-product trace; and
- an independently checked Lean companion proving the conventional finite-list
  theorem, including uniqueness up to permutation.

The companion closes the mathematical cross-check, but it does not turn the
unfinished Peano encoding lemmas into a `pa lib` theorem.

## The representation milestone

Three designs were compared:

| Design | Advantage | Cost |
|---|---|---|
| Gödel-coded sequences inside first-order arithmetic | No kernel-language extension | Long, opaque interfaces poorly suited to everyday reuse |
| Conservative sequence predicate over encoded naturals | Keeps the term grammar fixed | Still requires a substantial coding library and bounded-index relations |
| Reviewed finite-list/multiset layer | Natural theorem statements and permutation reasoning | Adds data syntax and needs a separate soundness review |

The selected Peano design is the first row: natural codes preserve the kernel
unchanged. For codes $b,c$, index $i$, and value $x$, define

$$
M(c,i)=1+(i+1)c,
\qquad
\operatorname{At}(b,c,i,x)
\;:\!\Longleftrightarrow\;
x<M(c,i)\land\exists q.\;b=qM(c,i)+x.
$$

The stored theorems keep this relation fully expanded and use the prefix
`beta_at`. The first checked decoding chain is:

| Checked theorem | Role | Nodes/depth | Cuts |
|---|---|---:|---:|
| `beta_modulus_nonzero` | the modulus $M(c,i)$ is a successor | 9 / 6 | 1 |
| `beta_at_self_of_bound` | a value below $M(c,i)$ decodes from itself with quotient zero | 62 / 16 | 2 |
| `beta_at_exists` | every code and index has a bounded decoded residue | 479 / 31 | 15 |
| `beta_at_unique` | two decoded residues at one code and index are equal | 1,121 / 59 | 30 |
| `beta_at_exists_unique` | package decoded-value totality and functionality | 1,625 / 61 | 47 |
| `beta_at_to_mod_eq` | project an `At` witness into balanced congruence | 358 / 27 | 11 |
| `beta_at_of_mod_eq_bound` | recover `At` from a bound and balanced congruence | 1,839 / 66 | 53 |

All seven certificates are intuitionistic and contain no DNE. The forward bridge
forgets the bound component of `At` and feeds its quotient-remainder equation
to `remainder_decomposition_to_mod_eq`, proving the readable relation

```text
At(b,c,i,x) -> b ≡ x (mod S ((S i) * c)).
```

Here `At` and the displayed congruence are documentation abbreviations. The
stored theorem contains only their existential PA expansions:

```text
forall b c i x.
  ((exists h. h + S x = S ((S i) * c)) /\
   exists q. b = q * S ((S i) * c) + x) ->
  exists u v.
    b + S ((S i) * c) * u = x + S ((S i) * c) * v
```

Conversely, `beta_at_of_mod_eq_bound` supplies the same strict bound and a
balanced-congruence witness to the checked reverse remainder bridge. Its exact
expanded statement is:

```text
forall b c i x.
  (exists h. h + S x = S ((S i) * c)) ->
  (exists u v.
    b + S ((S i) * c) * u = x + S ((S i) * c) * v) ->
  ((exists h. h + S x = S ((S i) * c)) /\
   exists q. b = q * S ((S i) * c) + x)
```

Thus the native library now checks the bidirectional characterization

$$
\operatorname{At}(b,c,i,x)
\quad\Longleftrightarrow\quad
x<M(c,i)\;\land\;b\equiv x\pmod{M(c,i)}.
$$

This establishes single-position decoding as a bounded congruence interface.
It does not construct one code realizing an arbitrary finite prefix.

A second code stores the prefix products, beginning at one and multiplying by
the decoded factor at each step. `AllPrime` expands the factor-pair prime
formula at every bounded index, and `Sorted` makes the representation
canonical by decoded values. Codes themselves are never equated because one
finite prefix can have more than one β-code.

The selected formula schemas and dependency spine are recorded in
`research/arithmetic-library/finite-factorization-encoding.md`.

## The checked Lean theorem

The separate `artifacts/lean-fta/FTA.lean` project now proves:

```lean
theorem fundamental_theorem_of_arithmetic (n : ℕ) (hn : n ≠ 0) :
    ∃ factors : List ℕ,
      IsPrimeFactorization n factors ∧
      ∀ other : List ℕ,
        IsPrimeFactorization n other → other.Perm factors
```

The witness is `n.primeFactorsList`. Existence checks that its entries are
prime and its product is $n$; uniqueness proves that any other prime list with
product $n$ is a permutation of it. For $n=1$, the witness is the empty list.

The project pins Lean 4.23.0 and Mathlib commit
`37df177aaa770670452312393d4e84aaad56e7b6`. Its audit rejects `sorryAx` and
requires exactly the declared standard axioms `propext`, `Classical.choice`,
and `Quot.sound`. This makes the dependency footprint visible rather than
calling a library import “axiom-free.”

## What “include FTA” means in this release

This release keeps two deliberately separate FTA tracks:

- the Lean companion is a checked existence-and-uniqueness proof up to
  permutation, with no admission;
- the conservative Peano representation design and formula schemas are
  documented;
- source curricula are mapped to the missing lemmas;
- no external theorem is smuggled into `pa lib` as a Peano certificate.

The gcd/Bézout/Gauss/Euclid chain, constructive prime-divisor existence, and
single-position Gödel-β decoded-value existence, uniqueness, and its
bidirectional bounded-congruence characterization are now checked in native
PA. The next critical gates are greatest-prime descent, binary and bounded
CRT, finite-prefix extension/restriction, and prefix-product traces.
Only after those interfaces have checked native certificates can factorization
existence, uniqueness, and FTA enter `pa lib`. FTA therefore remains unproved
in the native library.
