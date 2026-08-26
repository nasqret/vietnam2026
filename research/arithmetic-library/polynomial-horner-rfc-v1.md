# T12: conservative coded polynomials and certified Horner evaluation

This campaign supplies actual constructive polynomial evaluation in the
unchanged first-order language of Heyting arithmetic. A polynomial is an
existing Gödel-β coefficient prefix. Its value is a second β-coded trace with
initial entry zero and exact successor equation

```
h[0] = 0
h[i + 1] = h[i] * x + coefficient[i]
```

`Horner(b, c, x, length, value)` is solely hygienic authoring notation. Its
expansion contains only equality, successor, addition, multiplication,
bounded witnessed order, quantifiers, conjunction, and implication. It adds
no parser primitive, predicate constant, function symbol, classical axiom,
proof rule, or kernel exemption.

The seven dependency-ordered propositions establish:

1. Existence of a complete β-coded Horner trace for every coefficient prefix.
2. Existence of its actual natural evaluation witness.
3. Functional equality of arbitrary complete traces.
4. Functional uniqueness of the evaluation relation.
5. Existence of a unique evaluation value.
6. The zero value of the empty polynomial.
7. Exact decomposition at a successor coefficient.

Existence proceeds by induction on coefficient-prefix length. Each successor
decodes its final coefficient and prior trace endpoint, computes the natural
term `previous * x + coefficient`, and extends the existing finite β-prefix.
Functionality is proved independently by induction using exact β-value
uniqueness and congruence of addition and multiplication. Every script is
checked against its fully expanded dependency-curried proposition by the
original intuitionistic kernel.

An additional deterministic `evaluate_horner` interface constructs immutable
step-by-step certificates for concrete numerical exploration;
`verify_horner_evaluation` rejects altered, omitted, or reordered transitions.
These executable traces are useful scientific computations but never confer
formal theorem authority or Alpha admission.

Implementation:
[`polynomial_horner_candidate.py`](../../peano-lab/py/peano_lab/library/polynomial_horner_candidate.py).

Independent exact-formula, dependency, classical-rule-exclusion, adversarial
proof, hygienic-definition, numerical, and forged-trace audit:
[`test_polynomial_horner_candidate.py`](../../peano-lab/py/tests/test_polynomial_horner_candidate.py).
