# Alpha v20: additive constructive campaign layer

Alpha v20 preserves every one of the 1,737 independently checked Alpha-v19
theorem entries, every historical release artifact, and all 432 Stable
theorems. It appends exactly 39 new dependency-ordered first-order results:

| Constructive campaign | New theorems | Blueprint meaning |
| --- | ---: | --- |
| Polynomial Horner evaluation | 7 | Full coded natural evaluation, existence, uniqueness, and execution traces |
| Finite matrix and dot-product foundations | 10 | Exact cells, finite products, and signed 2-by-2 determinant components |
| Bertrand prime windows and chains | 13 | Full G023 multiplicity-one windows and G024 arbitrary finite prime chains |
| Constructive continued fractions | 9 | Full G071 finite Euclidean quotient lists and termination witnesses |

The resulting release has exactly 1,776 independently checked theorem rows,
5,882 real dependency edges, and 53 dependency layers. Stable remains
unchanged. The parent is pinned by all four immutable Alpha-v19 artifact
digests and the exact Alpha-v19 statement/evidence identities.

Every newly enrolled theorem is justified by a self-contained ordinary
intuitionistic proof bundle containing the entire real prerequisite cone. Its
590 graph nodes comprise 550 immutable parent theorems, all 39 new theorems,
and a balanced synthetic conjunction root. The original unchanged kernel
checks every graph node; the root is not enrolled as an additional theorem.

No script uses double-negation elimination, an oracle, an admitted lemma, a
new parser predicate, a new kernel constructor, or an unchecked theorem
reference. Named mathematical definitions remain hygienic conservative
expansions into the original arithmetic language.

The T13 matrix/lattice milestone remains **open**: its new ten checked
foundation theorems do not establish arbitrary signed matrix operations,
general determinants, rank, or lattice reduction. Likewise natural Horner
evaluation does not silently claim differentiation or general presented-ring
polynomial infrastructure.

Exact admission and adversarial replay audit:
[`test_library_editions_v20_admission.py`](../../peano-lab/py/tests/test_library_editions_v20_admission.py).
