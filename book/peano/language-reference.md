# Native PA language reference

This page states the object language accepted by Peano Lab. It is deliberately
small: natural-number terms, first-order formulas, and no primitive division,
remainder, exponentiation, lists, sets, primes, or quadratic residues. Every
larger mathematical notion in the library expands to this grammar before the
kernel sees it.

The interactive {doc}`PA Proof Explorer <../arithmetic-library/proof-explorer>`
uses this reference for every linked formal-proof line.

## Terms

The kernel term grammar is

$$
t ::= x \mid 0 \mid S(t) \mid t+t \mid t*t.
$$

| Surface form | Meaning |
|---|---|
| `x` | a named free or bound variable at the surface |
| `0` | zero |
| `S t` | successor of `t` |
| `t + u` | addition |
| `t * u` | multiplication |
| `1`, `2`, ... | notation expanded to successor numerals |

Bound variables are converted to de Bruijn indices internally. Names are a
parser and pretty-printer convenience; alpha-renaming does not change the
kernel term.

Multiplication binds more tightly than addition. Parentheses are always
available and should be used liberally in generated statements.

## Formulas

The kernel formula grammar is

$$
\varphi ::= t=u \mid \bot \mid
\varphi\to\varphi \mid \varphi\land\varphi \mid
\varphi\lor\varphi \mid \forall x.\varphi \mid \exists x.\varphi.
$$

The ASCII surface spellings are:

```text
t = u
false
A -> B
A /\ B
A \/ B
forall x. A
exists x. A
```

Negation is notation, not another formula constructor:

$$
\neg A \;:=\; A\to\bot,
$$

written `~A`. Chained quantifiers such as `forall x y. A` expand to nested
single binders.

## Conservative mathematical relations

Familiar arithmetic vocabulary is expressed relationally and expanded before
checking. Examples include:

| Informal notion | Native relational shape |
|---|---|
| $a\le b$ | `exists k. b = a + k` |
| $a<b$ | `exists k. b = a + S k` |
| $a\mid b$ | `exists k. b = a * k` |
| $a\equiv b\pmod m$ | balanced additive witnesses for a common multiple of `m` |
| quotient and remainder | `n = d*q + r` together with the expanded bound $r<d$ |
| finite sequence entry | a Gödel-$\beta$ relation |
| finite sum or product | a coded prefix trace with a functional endpoint |
| quadratic residue | existence of a square congruent to the value modulo the modulus |

These are not new kernel symbols. The generated theorem pages show the exact
fully expanded formula that is actually parsed and checked.

## What the language intentionally lacks

There are no primitive terms for `/`, `%`, subtraction, powers, `gcd`, lists,
finite products, primality, or Legendre symbols. There are also no predicate
variables, so a single polymorphic object-language theorem quantifying over an
arbitrary predicate is unavailable. Induction is instantiated for each
concrete formula by the proof language.

This distinction matters when reading the quadratic-reciprocity theorem. Its
surface page may explain residues, parity, quotient sums, and finite prefixes,
but its exact statement contains only the grammar above.

## Parser examples

```text
forall n. n + 0 = n
forall a b. (exists k. b = a + k) -> (exists k. S b = a + k)
forall p a. ~(p = 0) ->
  (exists x u v. x * x + p * u = a + p * v) \/
  ~(exists x u v. x * x + p * u = a + p * v)
```

The final example illustrates an expanded decidability statement for a
quadratic-residue relation. It adds no Boolean or classical oracle.

## Source of truth

The executable definitions live in `kernel/terms.py` and
`kernel/formulas.py`. The {doc}`kernel chapter <kernel>` explains how formulas
and certificates meet; {doc}`axioms and rules <axioms-and-rules>` lists the
only arithmetic axiom constants and the proof constructors that can use them.

