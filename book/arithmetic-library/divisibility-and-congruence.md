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

All three layers now have checked library entries. The balanced modular API is
checked through transitivity and additive and multiplicative compatibility;
both directions of the bounded decomposition/congruence bridge and uniqueness
of bounded congruent representatives are checked too. Constructive binary CRT,
its bounded-remainder client, and a two-position β-code client are checked as
well. Bounded-prefix pairwise β-modulus coprimality, product coprimality,
modulus descent, a generic CRT fold-preservation step, and ordinary induction
carrying the full prefix invariant for values already decoded from a supplied
code are checked too. Independent finite-prefix recoding and the exact
beta-coded prefix-product trace remain open.
Every checked entry mentioned below
is an ordinary closed formula with a replayed certificate accepted by the
independent Peano kernel; none is a new kernel rule. The general checking
architecture is described in
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

All 212 entries in the current post-baseline general foundational layer replay
to closed kernel-accepted certificates and fit the live `use` limits of
500,000 structural occurrences, 100,000 distinct proof objects, and depth 256.
Together with the 23-entry base and twelve unique
modular capstones, the 137-entry quadratic-residue foundation, and 25
strict-HA canonical/gcd/LCM interfaces, and 23 generalized-CRT interfaces, the
runtime has 432 checked theorems. The native
`fundamental_theorem_of_arithmetic` certificate has 73,767 nodes, depth 99,
and 2,184 self-contained Cuts. These are build metrics, not new soundness
assumptions; the exact certificate checks from the empty context using PA1–PA6
and induction, with no DNE. The broader research catalog has 433 nodes: 432
checked entries, no planned endpoint, and one representation-blocked
conventional integer-coefficient Bézout interface.

## The division algorithm is now native

For a nonzero divisor $m$, the checked theorem `division_remainder_exists`
constructs $q$ and $r$ satisfying

$$
n=mq+r,\qquad r<m.
$$

The strict bound is not a primitive relation. Its stored expansion is

```text
exists k. k + S r = m
```

so the complete theorem is still a formula over zero, successor, addition,
multiplication, equality, quantifiers, and connectives. Existence is proved by
ordinary induction on the dividend. At each successor step, the checked proof
performs the zero-or-successor gap split inline: either the current remainder
reaches the divisor, or its successor remains strictly bounded.

Uniqueness is a separate checked theorem:

```text
division_remainder_unique :
  forall m n q r q2 r2.
    n = m * q + r -> S r <= m ->
    n = m * q2 + r2 -> S r2 <= m ->
    q = q2 /\ r = r2
```

It compares the two quotients with `le_total`. A zero additive gap gives equal
quotients, after which `add_left_cancel` gives equal remainders. A successor
gap would place one bounded remainder beyond the next divisor block; the
checked `positive_quotient_gap_impossible` lemma rules that out. No classical
logic, subtraction, `/`, or `%` is used. The explicit nonzero premise is not
needed in the uniqueness statement: either strict remainder bound already
excludes a zero divisor.

The live library can reuse existence directly:

```text
pa> pa prove forall m n. ~(m = 0) -> exists q r. n = m * q + r /\ S r <= m
pa> use division_remainder_exists
pa> exact division_remainder_exists
pa> qed
```

Two checked bridges connect the theorem to divisibility:

- `zero_remainder_implies_multiple` turns $n=mq+0$ into $m\mid n$;
- `multiple_has_zero_remainder` packages a multiple of a nonzero divisor as a
  bounded division result with remainder zero.

The new decision layer closes the constructive loop. `eq_decidable` first
decides whether the unique remainder is zero. For a nonzero divisor,
`multiple_decidable_nonzero` combines that test with division existence,
zero-remainder existence for known multiples, and remainder uniqueness to
produce either a quotient witness or a refutation of every quotient witness.
`multiple_decidable` then handles a zero divisor by deciding whether the
dividend itself is zero. These are disjunction-producing certificates, not a
host-language divisibility oracle, and neither contains DNE.

The checked Euclidean bridge is also subtraction-free. `factor_difference`
removes a common multiple prefix, `divides_remainder` carries common divisors
from $(a,b)$ to a remainder $r$ in $a=bq+r$, and `divides_linear_step` carries
them back. Together with the base theorem `is_gcd_zero_right`, these yield the
checked pair `is_gcd_euclid_forward` and `is_gcd_euclid_backward`. They prove
gcd invariance for one division step. Downstream checked constructions now
provide relational gcd existence, balanced Bézout coefficients, Gauss
cancellation, Euclid's lemma, bounded factor search, and prime-divisor
existence.

These results are the foundation used by the now-checked bounded factor search
and Euclidean gcd layers; they are not a primitive computation service.

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

The relation's reflexivity, symmetry, and transitivity and its compatibility
with addition and multiplication are now named checked entries:
`mod_eq_refl`, `mod_eq_symm`, `mod_eq_trans`, `mod_eq_add`,
`mod_eq_mul_right`, `mod_eq_mul_left`, and `mod_eq_mul`. Reflexivity has the
short proof:

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

## Exact decompositions give congruence

An exact decomposition immediately gives a balanced congruence:

$$
  a=mq+r
  \quad\Longrightarrow\quad
  a\equiv_m r.
$$

For the zero residue, `dvd_to_mod_zero` is a checked library theorem. It
chooses balanced witnesses directly from the divisibility witness. The general
wrapper `remainder_decomposition_to_mod_eq` is now checked as well. Its stored
orientation is $b=qm+x\to b\equiv_m x$; the following replay proves the same
interface with the multiplication factors written in the opposite order:

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

The current status distinction is:

| Checked now | Still-open modular API |
|---|---|
| `mod_eq_refl`, `mod_eq_symm`, `mod_eq_trans` | equality transport into balanced congruence |
| `mod_eq_add`, `mod_eq_mul_right`, `mod_eq_mul_left`, `mod_eq_mul` | equality transport into balanced congruence |
| `remainder_decomposition_to_mod_eq`, `mod_eq_to_remainder_decomposition` | shared residue implies congruence |
| `mod_eq_bounded_unique` | finite-prefix restriction and functionality |
| `dvd_to_mod_zero` | reverse congruence-zero-to-divisibility |
| `binary_crt`, `binary_crt_remainders`, `binary_crt_fold_step` | independent finite-prefix specification and recoding |
| `binary_crt_beta_pair`, `beta_moduli_coprime_of_gap_dvd`, `binary_crt_beta_pair_of_gap_dvd` | arbitrary finite-prefix recoding and assembly |
| `bounded_common_multiple_step`, `bounded_common_multiple_exists`, `beta_moduli_pairwise_coprime_bounded` | prime-above-bound client and encoded finite-prefix use |
| `coprime_mul_left`, `coprime_mul_right`, `mod_eq_of_mod_eq_multiple` | exact beta-coded prefix-product trace and product bounds |
| `beta_accumulated_product_step`, `beta_crt_prefix_congruence_step`, `beta_crt_prefix_invariant_step`, `bounded_beta_crt_prefix_invariant` | factor-primality and final-product links |
| `bounded_beta_crt_for_existing_code` | arbitrary sequence recoding; its current residues already come from the input code |
| Closure of multiples under addition and multiplication | shared residue implies congruence |
| Exact quotient-and-residue addition | finite-product congruence clients |
| Exact square decomposition and square residue lifting | generated fixed-modulus clients |
| Pointwise forms of non-divisibility | parity-as-congruence clients |
| No `%` or primitive congruence predicate | finite-prefix β-code clients |

The transitivity and addition statements from the preceding tranche remain
ordinary expanded formulas:

```text
forall m a b c.
  (exists u v. a + m * u = b + m * v) ->
  (exists r s. b + m * r = c + m * s) ->
  exists x y. a + m * x = c + m * y

forall m a b c d.
  (exists u v. a + m * u = b + m * v) ->
  (exists r s. c + m * r = d + m * s) ->
  exists x y. (a + c) + m * x = (b + d) + m * y
```

Their shared certificates have 252 nodes/depth 29 with six Cuts and 370
nodes/depth 30 with ten Cuts, respectively. Both check constructively and
contain no DNE.

The next four checked formulas close multiplication compatibility and the
direct decomposition bridge:

```text
forall m a b c.
  (exists u v. a + m * u = b + m * v) ->
  exists r s. (a * c) + m * r = (b * c) + m * s

forall m a b c.
  (exists u v. a + m * u = b + m * v) ->
  exists r s. (c * a) + m * r = (c * b) + m * s

forall m a b c d.
  (exists u v. a + m * u = b + m * v) ->
  (exists r s. c + m * r = d + m * s) ->
  exists x y. (a * c) + m * x = (b * d) + m * y

forall m b q x.
  b = q * m + x ->
  exists u v. b + m * u = x + m * v
```

| Checked theorem | Role | Nodes/depth | Cuts |
|---|---|---:|---:|
| `mod_eq_mul_right` | scale a balanced congruence on the right | 484 / 26 | 13 |
| `mod_eq_mul_left` | derive left scaling using commutativity | 738 / 27 | 21 |
| `mod_eq_mul` | multiply two balanced congruences | 1,505 / 32 | 43 |
| `remainder_decomposition_to_mod_eq` | turn $b=qm+x$ into $b\equiv_m x$ | 323 / 26 | 10 |

All four certificates are intuitionistic and contain no DNE.

The reverse bridge first proves that two balanced-congruent values below the
same modulus are equal, then obtains the canonical remainder of $b$ from the
division theorem and identifies it with the proposed bounded representative.
The exact statements are:

```text
forall m a b.
  (exists ha. ha + S a = m) ->
  (exists hb. hb + S b = m) ->
  (exists u v. a + m * u = b + m * v) ->
  a = b

forall m b x.
  ~(m = 0) ->
  (exists h. h + S x = m) ->
  (exists u v. b + m * u = x + m * v) ->
  exists q. b = q * m + x
```

| Checked theorem | Role | Nodes/depth | Cuts |
|---|---|---:|---:|
| `mod_eq_bounded_unique` | identify bounded congruent representatives | 961 / 59 | 26 |
| `mod_eq_to_remainder_decomposition` | reconstruct a directed remainder witness | 1,793 / 64 | 50 |

Both certificates are intuitionistic and contain no DNE. Together with
`remainder_decomposition_to_mod_eq`, they give both directions between a
bounded directed remainder and balanced congruence.

## Constructive binary CRT

For nonzero coprime moduli, the checked `binary_crt` theorem now constructs a
single balanced-congruence witness for two arbitrary residues:

$$
m\ne0\land n\ne0\land\operatorname{Coprime}(m,n)
\Longrightarrow
\forall a\,b\;\exists x,\quad
x\equiv_m a\land x\equiv_n b.
$$

The exact stored statement expands coprimality and both congruences into
quantifiers over natural-number witnesses. Its construction starts from the
four-natural balanced Bézout equation. Two projection lemmas select the
appropriate coefficient modulo each modulus, and
`mod_eq_predecessor_cancel` represents the negative contribution modulo a
successor. No subtraction, signed coefficient, `/`, `%`, or CRT primitive is
added to the term language.

| Checked theorem | Role | Nodes/depth | Cuts |
|---|---|---:|---:|
| `bezout_mod_left` | Bézout projection modulo the left modulus | 134 / 19 | 4 |
| `bezout_mod_right` | Bézout projection modulo the right modulus | 50 / 16 | 1 |
| `mod_eq_predecessor_cancel` | predecessor cancellation modulo a successor | 315 / 25 | 9 |
| `binary_crt` | balanced binary CRT | 5,044 / 51 | 144 |
| `binary_crt_remainders` | two bounded directed remainder equations | 6,890 / 66 | 196 |
| `binary_crt_beta_pair` | one code with two expanded `At` facts | 6,941 / 69 | 201 |
| `beta_modulus_coprime_base` | each beta modulus is coprime to $c$ | 874 / 30 | 24 |
| `common_divisor_beta_moduli_divides_gap_times_c` | a common divisor divides $\mathit{gap}\,c$ | 855 / 30 | 24 |
| `beta_moduli_coprime_of_gap_dvd` | gap divisibility implies pairwise beta-modulus coprimality | 6,007 / 56 | 175 |
| `binary_crt_beta_pair_of_gap_dvd` | apply two-position CRT under the gap hypothesis | 12,980 / 71 | 378 |
| `beta_moduli_coprime_of_lt_bounded_common_multiple` | ordered bounded indices inherit gap divisibility | 6,227 / 57 | 181 |
| `beta_moduli_pairwise_coprime_bounded` | all distinct bounded beta moduli are pairwise coprime | 6,348 / 59 | 183 |
| `bounded_beta_moduli_pairwise_coprime_exists` | choose one nonzero base for a pairwise-coprime bounded family | 7,019 / 61 | 207 |
| `coprime_mul_left` | preserve coprimality under an accumulated product | 3,975 / 53 | 115 |
| `coprime_mul_right` | symmetric accumulated-product closure | 4,017 / 54 | 117 |
| `mod_eq_of_mod_eq_multiple` | descend congruence from a multiple modulus | 157 / 23 | 3 |
| `binary_crt_fold_step` | preserve all old divisor-modulus congruences and add one new congruence | 5,501 / 52 | 156 |
| `right_factor_divides_product` | expose the newly multiplied right factor as a divisor | 229 / 25 | 7 |
| `beta_accumulated_product_step` | preserve nonzero, prefix-divisibility, and future-coprimality product invariants | 11,174 / 69 | 330 |
| `beta_crt_prefix_congruence_step` | extend congruence to the next value decoded from the supplied code | 7,352 / 64 | 213 |
| `beta_crt_prefix_invariant_step` | combine the product and congruence successor steps | 18,613 / 70 | 545 |
| `bounded_beta_crt_prefix_invariant` | fold the full four-part invariant by ordinary induction | 25,496 / 78 | 752 |
| `bounded_beta_crt_for_existing_code` | project full-bound congruences for an already supplied code | 25,545 / 79 | 755 |

If $a<m$ and $b<n$, `binary_crt_remainders` feeds the result through
`mod_eq_to_remainder_decomposition` twice and obtains

$$
\exists x\,q\,r,\quad x=qm+a\land x=rn+b.
$$

`binary_crt_beta_pair` specializes the two moduli to $M(c,i)$ and $M(c,j)$
and uses `beta_at_of_mod_eq_bound` twice. It assumes, rather than proves, that
those two expanded β moduli are coprime. The new conditional theorem proves
that premise from

$$
j=i+\mathit{gap},\qquad \mathit{gap}\mid c,
$$

and `binary_crt_beta_pair_of_gap_dvd` applies it. The conditions cannot be
erased: $c=1$ gives beta moduli $M(1,1)=3$ and $M(1,4)=6$, which are not
coprime.

For a bounded common-multiple base, the new ordered theorem extracts the
positive gap between $i<j$ and proves that it lies within the common-multiple
bound. Trichotomy then yields pairwise coprimality for all distinct positions.
The product lemmas fold those pairwise facts into coprimality of an accumulated
product with the next modulus. If $m\mid P$, `mod_eq_of_mod_eq_multiple`
turns $z\equiv x\pmod P$ into $z\equiv x\pmod m$.
`binary_crt_fold_step` combines these facts into the preservation invariant

$$
\forall m\mid P,\quad x\equiv a\pmod m\Longrightarrow z\equiv a\pmod m,
$$

while also proving $z\equiv b\pmod n$ for the new modulus.

The next six theorems perform the bounded induction around that algebra.
`right_factor_divides_product` provides the explicit divisibility witness for
the new right factor. `beta_accumulated_product_step` multiplies the current
product by the next beta modulus while preserving its nonzeroness,
divisibility by all prefix moduli, and coprimality with all future bounded
moduli. `beta_crt_prefix_congruence_step` uses the generic CRT fold to add the
next residue decoded from the supplied code $b$ and preserve every earlier
decoded congruence. `beta_crt_prefix_invariant_step` packages those two
successor results.

The ordinary-induction theorem `bounded_beta_crt_prefix_invariant` is the
substantive endpoint. Given the bounded common-multiple hypothesis, for every
$k\le N$ it constructs naturals $P,z$ satisfying all four components:

1. $P\ne0$;
2. every beta modulus at a prefix position $i\le k$ divides $P$;
3. $z$ is congruent at that modulus to every value $a$ already decoded from
   the supplied code $b$ at such a position; and
4. $P$ is coprime to every future beta modulus between the successor of $k$
   and $N$.

This is a real bounded fold, but it is not yet beta finite-prefix recoding.
The wrapper `bounded_beta_crt_for_existing_code` projects component 3 at
$k=N$. Because its premise already decodes every residue from $b$, its
conclusion is extensionally satisfied by choosing $z=b$. The large certificate
records one path through the invariant; it does not construct a code for an
independently specified sequence.

The companion divisibility pair constructs the shared resource needed for a
finite bound:

| Checked theorem | Role | Nodes/depth | Cuts |
|---|---|---:|---:|
| `bounded_common_multiple_step` | extend a nonzero common multiple across one endpoint | 483 / 29 | 15 |
| `bounded_common_multiple_exists` | obtain nonzero $c$ divisible by every positive natural at most $B$ | 640 / 30 | 22 |

What remains is to specify an independent finite prefix and recode or extend
it, construct an exact beta-coded prefix-product recurrence/trace, prove the
bounds placing every exact prefix product below the chosen beta moduli, and
connect decoded factors to primality and the final product. Thus the bounded
induction invariant is checked, while arbitrary finite-prefix assembly and
the product trace remain explicit later gates.

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

The checked `mod5_residue_complete` theorem has the shape

$$
\forall n\;\exists q,\quad
\begin{aligned}
n={}&5q\;\lor\;n=5q+1\;\lor\;n=5q+2\\
   &\lor\;n=5q+3\;\lor\;n=5q+4.
\end{aligned}
$$

The existing certificate proves it as a fixed-modulus induction lemma. The new
general division theorem now supplies the reusable route for future moduli.
The hypothesis and `not_multiple_pointwise` eliminate the $r=0$ branch. The
remaining arithmetic is the small table

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

Thus the checked dependency route is

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

Every rung in this route is now admitted and independently checked, culminating
in `mod5_fourth_power_one`. Its current closed certificate uses 2,675
structural nodes because dependency proofs are embedded once per lexical Cut
rather than copied at every use. The short transcript in {doc}`Using and
extending the library <using-the-library>` still imports the complete
self-contained evidence and does not bypass kernel checking.

## Admission checklist for the next congruence lemmas

Before a planned modular theorem becomes part of the library:

1. Keep its public statement expanded into `exists`, `+`, `*`, and equality.
2. Choose a name that distinguishes modular congruence from equality
   congruence.
3. List only earlier checked dependencies.
4. Replay the authored primitive tactic script.
5. Package each checked dependency in a self-contained Cut with no external
   name or hash authority.
6. Check the resulting closed certificate from the empty context against the
   original formula.
7. Record node count, depth, script hash, statement hash, and dependency edges.
8. Verify that `use` accepts the certificate under the live resource limits.
9. Add positive, symmetric, zero-modulus, and deliberately malformed tests.
10. Update the generated catalog and dependency graph rather than hand-editing
    generated artifacts.

This discipline gives modular arithmetic a pleasant surface without granting
it any extra authority.  A congruence lemma is reusable because its witnesses
and certificate have been checked, not because the notation looks familiar.
