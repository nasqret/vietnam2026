# Divisibility and subtraction-free congruence

Divisibility is where elementary arithmetic starts to feel like a library
rather than a sequence of isolated calculations.  A useful development should
make it cheap to say that a number is a multiple, transport that fact through
addition and multiplication, and then reuse the same algebra in modular
arguments.  It should do all of this without quietly adding division,
subtraction, integers, or a trusted remainder operation to Peano Lab.

This chapter separates three things that are easy to conflate:

1. **divisibility**, represented by an existential multiplication witness;
2. **exact residue decompositions**, represented by equations such as
   $n=mq+r$;
3. **modular congruence**, represented without subtraction by a balanced
   existential equation.

The first two layers already have checked library entries.  The third is the
next API to build.  Every checked entry mentioned below is an ordinary closed
formula with a replayed certificate accepted by the independent Peano kernel;
none is a new kernel rule.  The general checking architecture is described in
[the checked theorem ladder](../peano/ladder.md).

## Divisibility is an existential equation

For natural numbers $a$ and $b$, define

$$
  a\mid b
  \quad:\!\!\Longleftrightarrow\quad
  \exists q\in\mathbb N,\; b=a\cdot q.
$$

The exact Peano formula is:

```text
exists q. b = a * q
```

The witness $q$ is part of the proof.  There is no primitive `divides`
predicate and no parser notation for `|`; library names therefore use
`multiple`, as in `multiple_refl`.  This is a definitional convention in the
documentation, not an extension of the trusted language.

The orientation $b=a*q$ is deliberate.  It agrees with the multiplication
recursion and with the residue form $b=a*q+r$.  Equality symmetry is available
when a calculation naturally produces the reverse orientation.

:::{admonition} Zero is not a special syntactic case
:class: note

The definition handles it honestly.  Every $a$ divides $0$, with witness
$q=0$.  Conversely, $0\mid b$ says that $b=0*q$, so only $b=0$ can satisfy it.
The forward fact is already named `multiple_zero`; the converse is a useful
future wrapper around the zero-product laws.
:::

Here is a complete proof of the first direction using only PA5 and
reflexivity.  This transcript was replayed through the current Peano driver.

```text
pa> pa prove forall a. exists q. 0 = a * q
pa> intro a
pa> exists 0
pa> rewrite PA5
pa> refl
pa> qed
```

The library entry `multiple_zero` packages exactly this fact, so downstream
proofs normally import it instead of reconstructing it.

## The checked divisibility ladder

The checked API is small, symmetric where the underlying operation is
symmetric, and explicit about witnesses.

| Entry | Closed statement, in readable notation | Direct dependencies |
|---|---|---|
| `multiple_zero` | $\forall a,\;a\mid0$ | none |
| `one_multiple` | $\forall n,\;1\mid n$ | `one_mul` |
| `multiple_refl` | $\forall a,\;a\mid a$ | `mul_one` |
| `multiple_add` | $a\mid n\to a\mid m\to a\mid(n+m)$ | `mul_add` |
| `multiple_mul_right` | $a\mid n\to a\mid(nm)$ | `mul_assoc` |
| `multiple_mul_left` | $a\mid n\to a\mid(mn)$ | `mul_comm`, `multiple_mul_right` |
| `multiple_trans` | $a\mid n\to b\mid a\to b\mid n$ | `mul_assoc` |
| `not_multiple_pointwise` | $\neg\exists q,n=aq\to\forall q,n\ne aq$ | none |
| `not_multiple_from_pointwise` | $(\forall q,n\ne aq)\to\neg\exists q,n=aq$ | none |

The formulas stored in the library do not contain the display notation
$a\mid b$.  For example, `multiple_add` is literally:

```text
forall a n m.
  (exists q. n = a * q) ->
  (exists r. m = a * r) ->
  exists s. n + m = a * s
```

The proof exposes witnesses $q$ and $r$, selects $q+r$, and closes the equation
with distributivity.  This makes the dependency visible:

$$
\bigl(n=aq\bigr)\land\bigl(m=ar\bigr)
\quad\Longrightarrow\quad
n+m=aq+ar=a(q+r).
$$

The following live use of the checked theorem was replayed exactly as shown.

```text
pa> pa prove forall a n m. (exists q. n = a * q) -> (exists r. m = a * r) -> exists s. n + m = a * s
pa> intro a
pa> intro n
pa> intro m
pa> intro hn
pa> intro hm
pa> use multiple_add
pa> specialize multiple_add a
pa> specialize multiple_add n
pa> specialize multiple_add m
pa> apply multiple_add
pa> exact hn
pa> exact hm
pa> qed
```

### Negating an existential cleanly

A common modular hypothesis has the form

$$
  \neg\exists q,\;n=a q.
$$

It does not provide a witness to introduce.  It is a function from any alleged
existential witness to contradiction.  The checked
`not_multiple_pointwise` lemma turns it into the reusable pointwise form

$$
  \forall q,\;n\ne aq.
$$

This is the precise transformation needed in a residue case split:

```text
pa> pa prove forall a n. ~(exists q. n = a * q) -> forall q. ~(n = a * q)
pa> intro a
pa> intro n
pa> intro h
pa> use not_multiple_pointwise
pa> specialize not_multiple_pointwise a
pa> specialize not_multiple_pointwise n
pa> apply not_multiple_pointwise
pa> exact h
pa> qed
```

Its converse, `not_multiple_from_pointwise`, is checked separately.  Neither
direction uses classical logic: each simply packages or unpacks an
existential witness.

## Exact residue equations come before congruence

Suppose

$$
  z=a q+r.
$$

This is stronger data than a bare modular-congruence assertion: it names both
the quotient and the residue and fixes an exact equality in $\mathbb N$.  Such
equations are particularly useful in constructive proofs because their
witnesses can be substituted directly.

The current checked residue layer contains the following modulus-independent
helpers.

| Entry | Exact purpose | Direct dependencies |
|---|---|---|
| `add_residue` | Absorb $r=ac+s$ into $au+r=a(u+c)+s$ | `add_assoc`, `mul_add` |
| `add_residue_lift` | Combine two quotient-and-residue summands and normalize their residue | `add_comm`, `add_assoc`, `mul_add` |
| `square_decomp` | Expand $z=aq+r$ to $z^2=a(qz+rq)+r^2$ | `add_assoc`, `mul_comm`, `mul_add`, `add_mul`, `mul_assoc` |
| `square_residue_lift` | Combine `square_decomp` with $r^2=ac+s$ | `square_decomp`, `add_residue` |
| `square_residue_witness` | Hide the resulting quotient behind an existential witness | `square_residue_lift` |

Here $z^2$ is only mathematical typography.  The checked Peano statements use
`z * z`; exponentiation has not been added to the term language.

The central exact statement is `square_residue_witness`:

```text
forall a z q r c s.
  z = a * q + r ->
  r * r = a * c + s ->
  exists w. z * z = a * w + s
```

It says that a residue calculation on the small value $r$ can be lifted to
the large value $z$.  It neither defines `%` nor asks an untrusted evaluator
for a remainder.  The quotient witness is constructed algebraically and the
closed certificate is checked.

This exact use also replays in the current driver:

```text
pa> pa prove forall a z q r c s. z = a * q + r -> r * r = a * c + s -> exists w. z * z = a * w + s
pa> intro a
pa> intro z
pa> intro q
pa> intro r
pa> intro c
pa> intro s
pa> intro hz
pa> intro hrs
pa> use square_residue_witness
pa> specialize square_residue_witness a
pa> specialize square_residue_witness z
pa> specialize square_residue_witness q
pa> specialize square_residue_witness r
pa> specialize square_residue_witness c
pa> specialize square_residue_witness s
pa> apply square_residue_witness
pa> exact hz
pa> exact hrs
pa> qed
```

The dependency ladder can be read compactly as

$$
\begin{array}{c}
\texttt{add\_assoc},\texttt{mul\_add}
   \longrightarrow \texttt{add\_residue}\\[2mm]
\text{commutative-semiring basis}
   \longrightarrow \texttt{square\_decomp}\\[2mm]
\texttt{square\_decomp}+\texttt{add\_residue}
   \longrightarrow \texttt{square\_residue\_lift}
   \longrightarrow \texttt{square\_residue\_witness}.
\end{array}
$$

All 28 entries in the original M20 foundational subset replay to
closed kernel-accepted certificates and fit the live `use` limits of 32,768
nodes and depth 128.  That subset's maximum is 1,601 nodes and depth 59; the
reconciled 63-entry snapshot reaches 21,515 nodes and depth 66 at the modular
capstone.  These numbers are build artifacts, not new soundness assumptions.

## Why ordinary one-sided congruence is wrong over naturals

Over integers one often writes

$$
  a\equiv b\pmod m
  \quad\Longleftrightarrow\quad
  m\mid(a-b).
$$

Peano Lab has neither integer terms nor subtraction.  A tempting replacement
is

$$
  \exists k,\;a=b+mk.
$$

That relation is not symmetric over naturals.  It describes only the branch
where $a$ lies above $b$ by a multiple of $m$.  Reversing $a$ and $b$ may
require a negative witness, which is unavailable.

The subtraction-free target should instead be the **balanced** relation

$$
  a\equiv_m b
  \quad:\!\!\Longleftrightarrow\quad
  \exists u\,v,\;a+m u=b+m v.
$$

Its exact Peano expansion is:

```text
exists u v. a + m * u = b + m * v
```

The two witnesses place both sides in a common additive-multiple extension.
Symmetry swaps $u$ and $v$.  Transitivity combines two pairs of witnesses.
No subtraction and no signed number is hidden in the notation.

This definition also gives sensible edge cases:

- for $m=0$, balanced congruence reduces to equality;
- for $m=1$, every pair of naturals is congruent;
- no positivity assumption on $m$ is required merely to define the relation.

The relation's reflexivity already has a short Peano proof, although it is not
yet a named library entry:

```text
pa> pa prove forall m a. exists u v. a + m * u = a + m * v
pa> intro m
pa> intro a
pa> exists 0
pa> exists 0
pa> refl
pa> qed
```

:::{admonition} Two meanings of congruence
:class: important

`add_congr` and `mul_congr` in the checked library are **equality
congruence** lemmas: equal inputs give equal compound terms.  The balanced
formula above is **modular congruence**.  The latter will use the former in its
compatibility proofs, but the two notions should not share ambiguous names.
:::

## A checked prototype bridge, but not yet a catalog theorem

An exact decomposition immediately gives a balanced congruence:

$$
  a=mq+r
  \quad\Longrightarrow\quad
  a\equiv_m r.
$$

Choose $u=0$ and $v=q$; after zero simplification the remaining equality is
$mq+r=r+mq$, which is addition commutativity.  The following proof replays
today, but the result has not yet been admitted as a named checked library
entry.  It is therefore a prototype for review, not a fact available through
`use`.

```text
pa> pa prove forall m a q r. a = m * q + r -> exists u v. a + m * u = r + m * v
pa> intro m
pa> intro a
pa> intro q
pa> intro r
pa> intro h
pa> exists 0
pa> exists q
pa> rewrite PA5
pa> rewrite PA3
pa> rewrite h
pa> use add_comm
pa> apply add_comm
pa> qed
```

That status distinction matters:

| Checked now | Planned modular API |
|---|---|
| Exact divisibility witnesses | `balanced_congr_refl` |
| Closure of multiples under addition and multiplication | `balanced_congr_symm` |
| Transitivity of the multiple relation | `balanced_congr_trans` |
| Exact quotient-and-residue addition | `balanced_congr_add` |
| Exact square decomposition and square residue lifting | `balanced_congr_mul` and square compatibility |
| Pointwise forms of non-divisibility | decomposition implies congruence |
| No `%` or primitive congruence predicate | shared residue implies congruence |
| No congruence-zero theorem | divisibility iff congruent to zero |

The planned entries remain ordinary expanded formulas.  Representative target
shapes are:

```text
forall m a b.
  (exists u v. a + m * u = b + m * v) ->
  exists u v. b + m * u = a + m * v

forall m a b c.
  (exists u v. a + m * u = b + m * v) ->
  (exists x y. b + m * x = c + m * y) ->
  exists p q. a + m * p = c + m * q

forall m a b c d.
  (exists u v. a + m * u = b + m * v) ->
  (exists x y. c + m * x = d + m * y) ->
  exists p q. (a + c) + m * p = (b + d) + m * q
```

These are proposed statements, not replay transcripts and not current theorem
names.  Before admission they need small authored scripts, explicit earlier
dependencies, certificate metrics, live-`use` checks, and independent kernel
replay.  Multiplicative compatibility and the reverse direction of
"congruent to zero iff divisible" deserve particular care; the balanced
witnesses must be rearranged constructively rather than cancelled by an
unavailable subtraction operation.

## From a general library to the old modulo-five exercise

Consider the earlier target

$$
\forall n,\quad
\neg\exists q,\;n=5q
\quad\Longrightarrow\quad
\exists w,\;n^4=5w+1.
$$

In the exact current Peano syntax, the intended statement is

```text
forall n.
  ~(exists q. n = 5 * q) ->
  exists w. n * n * n * n = 5 * w + 1
```

This should not drive the foundational API.  Once the general layers exist,
it becomes a small downstream application with five finite residue branches.

The missing finite completeness lemma has the shape

$$
\forall n\;\exists q,\quad
\begin{aligned}
n={}&5q\;\lor\;n=5q+1\;\lor\;n=5q+2\\
   &\lor\;n=5q+3\;\lor\;n=5q+4.
\end{aligned}
$$

That theorem is not currently in the checked foundational catalog.  It should
be proved either as a fixed-modulus induction lemma or as a corollary of a
later constructive division algorithm.  The hypothesis and
`not_multiple_pointwise` eliminate the $r=0$ branch.  The remaining arithmetic
is the small table

| $r$ | First square $r^2=5c+s$ | Second square $s^2=5d+1$ |
|---:|---:|---:|
| $1$ | $1=5\cdot0+1$ | $1=5\cdot0+1$ |
| $2$ | $4=5\cdot0+4$ | $16=5\cdot3+1$ |
| $3$ | $9=5\cdot1+4$ | $16=5\cdot3+1$ |
| $4$ | $16=5\cdot3+1$ | $1=5\cdot0+1$ |

For each row, `square_residue_witness` lifts the first small calculation from
$r$ to $n^2$, and a second application lifts the second calculation from $s$
to $(n^2)^2$.  One small checked associativity bridge then identifies

$$
  (n\cdot n)(n\cdot n)
  = n\cdot n\cdot n\cdot n.
$$

Thus the eventual dependency route is

$$
\begin{array}{c}
\text{PA commutative-semiring facts}\\
\downarrow\\
\text{generic exact residue helpers}\\
\downarrow\\
\text{fixed residue completeness and finite numeral identities}\\
\downarrow\\
\text{two square lifts plus a product-regrouping bridge}\\
\downarrow\\
n\not\equiv0\pmod5\Longrightarrow n^4\equiv1\pmod5.
\end{array}
$$

The full modulo-five proof is intentionally not presented as a current `pa>`
transcript: its residue-completeness and fourth-power bridge entries have not
yet been admitted to this checked catalog.  Showing imaginary `use` commands
would erase exactly the checked-versus-planned boundary this library is meant
to preserve.

## Admission checklist for the next congruence lemmas

Before a planned modular theorem becomes part of the library:

1. Keep its public statement expanded into `exists`, `+`, `*`, and equality.
2. Choose a name that distinguishes modular congruence from equality
   congruence.
3. List only earlier checked dependencies.
4. Replay the authored primitive tactic script.
5. Eliminate dependency cuts outside the trusted kernel.
6. Check the resulting closed certificate against the original formula.
7. Record node count, depth, script hash, statement hash, and dependency edges.
8. Verify that `use` accepts the certificate under the live resource limits.
9. Add positive, symmetric, zero-modulus, and deliberately malformed tests.
10. Update the generated catalog and dependency graph rather than hand-editing
    generated artifacts.

This discipline gives modular arithmetic a pleasant surface without granting
it any extra authority.  A congruence lemma is reusable because its witnesses
and certificate have been checked, not because the notation looks familiar.
