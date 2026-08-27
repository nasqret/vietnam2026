# Complete positive primitive Pythagorean classification

This additive candidate closes the exact mathematical content of grand-campaign
G077. It extends the historical forward constructor without changing its source,
the kernel, any axiom, Stable membership, or the immutable Alpha v25 release.

The positive definition is deliberately stronger than the old
`primitive_pythagorean(a,b,c)`, which also permits `(0,1,1)` and `(1,0,1)`:

```
PositivePrimitiveTriple(a,b,c) :=
  a != 0 /\ b != 0 /\ c != 0 /\
  a*a + b*b = c*c /\ Coprime(a,b).
```

`Coprime` is the already checked common-divisor definition, and opposite parity
is the disjunction of two explicit even/odd witness pairs. The new public
helpers validate identifiers and reject generated-binder capture; changing the
binder tag leaves the parsed first-order formula exactly alpha-equivalent.

The full endpoint `pythagorean_positive_primitive_classification` proves the
constructive equivalence, with subtraction replaced by exact natural gaps:

```
forall a b c.
  PositivePrimitiveTriple(a,b,c) <->
  exists m n.
    n != 0 /\ n < m /\ Coprime(m,n) /\ OppositeParity(m,n) /\
    c = m*m + n*n /\
    ((m*m = n*n + a /\ b = 2*(m*n)) \/
     (m*m = n*n + b /\ a = 2*(m*n))).
```

The original language expands `<` to `exists gap. gap + S n = m`; the
equivalence is a conjunction of both implications. The formal theorem is
unconditional. It does not assume the inverse classification, termination of a
host search, factorization oracle, or classical choice.

The oriented endpoint `pythagorean_primitive_odd_even_inverse` takes the old
primitive relation, positivity of both legs, an odd first-leg witness and an
even second-leg witness. It returns every parameter condition and coordinate
equation. This smaller interface is used twice by the constructive Fermat-four
descent campaign.

## Proof and definition DAG

The mathematical dependency chain is:

```
positive other leg + square-order reflection -> a < c
odd a + odd c + a <= c -> exists t. c = a + 2*t
ordered square-difference identity + b = 2*h
  -> (a+t)*t = h*h
coprime a c -> coprime (a+t) t
constructive coprime square-factor extraction
  -> a+t = m*m, t = n*n
natural square-root uniqueness -> b = 2*(m*n)
positive legs + odd c -> n>0, n<m, coprime m n, opposite parity
constructive parity choice -> both leg orientations
checked positive Euclidean constructor -> full equivalence
```

The definition graph reuses the old Pythagorean equation, common-divisor
coprimality, even and odd witnesses, and opposite parity. It adds precisely
the positive-triple relation, an oriented Euclidean parameter witness, and the
existential two-orientation parametrization. Those are conservative formulas;
definition edges never replace proof dependencies.

The source factory contains **23 theorem bodies**, **77 actual declared
dependency edges**, **733 tactic commands**, and **1,335 structural original
kernel proof nodes** under dependency-curried replay. Every body is checked;
the largest is the positive forward constructor with 187 proof nodes. Candidate
body replay leaves prerequisites as hypotheses, so release-level dependency
closure and independently compiled Lean checking are separate publication gates.

Pinned theorem statement SHA-256 values:

| Theorem | SHA-256 |
| --- | --- |
| `pythagorean_primitive_odd_even_inverse` | `b926982a720ad0f6cba2184dbb851f072f4f5c69a152b7c0c5e40f448313646f` |
| `pythagorean_positive_primitive_inverse` | `52637d9c57c28d1875f272b93a815aa22ba1d05c066be0642d44721f1903ae85` |
| `pythagorean_positive_primitive_classification` | `df3bd4829643a3900cee8f78fc7b4b242a0fb935f8e29e1b4d2b7e18bdac387f` |

Focused tests replay all 23 bodies and reject false strengthened conclusions,
truncated scripts, and missing dependencies. They also pin the exact positive
definition and the two-direction/two-orientation AST, check binder hygiene,
exercise both orders of familiar primitive triples, and compare construction
with inversion for all coprime opposite-parity parameter pairs below 25. The
small numerical checks are examples only; they supply no proof authority.
