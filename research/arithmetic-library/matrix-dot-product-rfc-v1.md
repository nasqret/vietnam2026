# T13 first layer: witnessed finite matrix entries and dot products

This is a rigorously checked **first layer**, not a claim that arbitrary signed
matrix multiplication, determinant formalization, or lattice reduction has
already been completed.

A finite natural matrix is flattened into its existing Gödel-β prefix. Its
entry at row `i`, column `j`, and width `w` is the existing decoded value at
natural position `i*w+j`. Exact entry existence, functionality, and unique
existence therefore follow constructively from established β decoding.

The finite dot product of two coefficient prefixes is defined by an existential
third β prefix whose entries are the exact pointwise natural products together
with an independent β-coded finite-sum trace. The original Heyting kernel
checks existence, functionality, unique existence, the empty case, and
commutativity. Functionality transports the existing sum trace between two
potential product-prefix witnesses without trusting equality of their raw
codes.

Two additional propositions construct the positive and negative natural
components `a*d` and `b*c` of a signed 2-by-2 determinant, and prove these
components unique.

For scientific experiments, bounded executable certificates additionally
support arbitrary signed integer matrix multiplication and signed permutation
expansions of square determinants. These computational certificates are not
misrepresented as proofs of the still-open arbitrary-dimension first-order
matrix or lattice milestone.

Implementation:
[`matrix_dot_product_candidate.py`](../../peano-lab/py/peano_lab/library/matrix_dot_product_candidate.py).

Exact constructive, dependency, forged-proof, hygienic-definition,
signed-integer, and adversarial-certificate audit:
[`test_matrix_dot_product_candidate.py`](../../peano-lab/py/tests/test_matrix_dot_product_candidate.py).
