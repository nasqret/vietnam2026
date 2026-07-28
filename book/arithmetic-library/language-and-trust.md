# Language, notation, and trust

Peano Lab intentionally has a small object language. Natural-number terms are
built from

$$
0,\qquad S(n),\qquad n+m,\qquad n\cdot m,
$$

and formulas use equality, first-order connectives, and quantifiers. The
surface notation $n\le m$ is already conservative sugar for an existential
equality. There is no trusted remainder operation, primality oracle, power
function, list, multiset, or theorem database.

This is a useful constraint. It forces every library abstraction to answer a
precise question: is it merely readable notation that expands to the old
language, or is it genuinely new expressive power?

## Conservative definitions

Divisibility needs no kernel change. We read

$$
a\mid b \quad:\!\Longleftrightarrow\quad \exists q.\ b=a\cdot q.
$$

The current library stores the right-hand formula literally. For example,
`multiple_trans` says that witnesses for $a\mid n$ and $b\mid a$ compose to a
witness for $b\mid n$.

A subtraction-free definition of modular congruence over naturals is

$$
a\equiv b\pmod m
\quad:\!\Longleftrightarrow\quad
\exists u\,v.\ a+m\cdot u=b+m\cdot v.
$$

Unlike the asymmetric claim that one number is the other plus a multiple,
this formula is symmetric even when $a<b$. It is also meaningful at modulus
zero: then it reduces to equality. A future pretty notation may expand to this
formula before proof checking, exactly as `<=` expands today.

Primality can also be expanded:

$$
\operatorname{Prime}(p) \quad:\!\Longleftrightarrow\quad
p\ne1\;\land\;
\forall a\,b.\bigl(p=a\cdot b\to(a=1\lor b=1)\bigr).
$$

This factor-pair form is the catalog's current convention; it is equivalent to
the familiar assertion that every divisor is either one or the number itself.
Over the naturals it also rules out zero, since zero has nontrivial factors.
The catalog records completely expanded Peano targets rather than asking the
checker to trust `Prime` as a new atom. In particular, the checked theorem
`prime_two` is stored as

```text
~(2 = 1) /\ forall a b. 2 = a * b -> a = 1 \/ b = 1
```

and introduces no primitive predicate.

## Relational definitions before functions

The current term grammar cannot add a gcd function without changing the
language. It can state a graph relation instead:

$$
\begin{aligned}
\operatorname{IsGCD}(g,a,b) :\!\Longleftrightarrow {} &
g\mid a\land g\mid b\\
&{}\land\forall d.\bigl(d\mid a\land d\mid b\to d\mid g\bigr).
\end{aligned}
$$

Existence and uniqueness of such a $g$ are ordinary first-order claims. A
subtraction-free Bézout statement can represent signed coefficients by
positive and negative parts:

$$
a x_+ + b y_+ = g + a x_- + b y_-.
$$

This is less convenient than integer notation, but it remains honest about
the underlying language.

## Where conservative expansion stops

The Fundamental Theorem of Arithmetic quantifies over an arbitrary finite
collection of primes and compares factorizations up to permutation or
multiplicity. Today's Peano surface has no primitive finite-sequence,
multiset, finite-map, generic power, or recursive factorization relation.

The representation review selected a Gödel-β encoding because it elaborates
entirely to existing PA formulas and therefore leaves the trusted kernel
unchanged. A factor sequence uses natural codes `(b,c,l)`; a second code stores
prefix products; bounded formulas express decoded values, primality, and
sortedness. This is intentionally an untrusted authoring facade rather than a
new kernel atom.

The planned route is therefore explicit:

1. add untrusted named-predicate expansion for the formulas already
   expressible;
2. build on the now-checked division theorem to prove concrete strong
   induction clients, gcd, prime-divisor existence, and Euclid's lemma in
   expanded first-order form;
3. implement and prove the selected β-sequence and prefix-product relations;
4. state and check factorization existence and extensional uniqueness.

A separate Lean companion already checks the conventional finite-list FTA,
including uniqueness up to permutation and an exact axiom audit. It fixes the
target statement but grants no Peano authority. Until steps 3–4 produce closed
PA certificates, FTA remains absent from `pa lib` rather than becoming a
pretend `TheoremSpec`.

## The trust path

For a checked entry the path is always

$$
\text{statement + dependencies + script}
\longrightarrow \text{replayed proof}
\longrightarrow \text{cut elimination}
\longrightarrow \operatorname{check}(\varnothing,p,T).
$$

Notation expansion, tactic execution, catalog generation, dependency graphs,
and hash generation are all untrusted. Any of them may cause a true proof to
be rejected or an artifact to become stale. None may make the independent
kernel accept a false closed formula.
