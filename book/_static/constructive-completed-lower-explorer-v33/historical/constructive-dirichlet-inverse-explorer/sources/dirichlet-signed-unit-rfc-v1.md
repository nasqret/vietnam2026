# Canonical signed units and constructive affine equations

Date: 2026-08-29. Status: nine original-HA candidate bodies checked; not
Alpha- or Stable-admitted. This is scalar support for a separate finite
Dirichlet inverse construction, not that construction itself.

## Exact representation and public definition

All signed values use the existing canonical natural-number encoding:
`0` represents zero, `2` represents positive one, and `1` represents negative
one. The existing `SignedDecode`, `SignedAdd`, and `SignedMul` graphs are
reused literally, including their actual existential decoder witnesses.
There is no new arithmetic primitive, quotient axiom, or inverse oracle.

The one new proposed conservative notation is:

```text
SignedUnit(u) := u = 2 or u = 1.
```

Its public builder is
`dirichlet_signed_unit_relation(u, *, tag, variables)`; the internal builder
is `_unit(u, tag)`. It accepts compound terms and large numerals in an
explicit, distinct-variable context. Invalid terms, tags, or contexts are
rejected. The expansion has no binders, so it cannot capture even an unused
declared variable. No definition identifier is allocated by this module.
This is distinct from modular units, nonzero residue ranges, and Gaussian
units.

## Exact theorem interfaces

Here `Mul`, `Add`, and `Unit` abbreviate only those exact graphs. Every
variable is a natural number coding a canonical signed value.

```text
dirichlet_signed_unit_self_product:
  forall u. Unit(u) -> Mul(u,u,2).

dirichlet_signed_unit_product_classification:
  forall a b. Mul(a,b,2) ->
    ((a=2 and b=2) or (a=1 and b=1)).

dirichlet_signed_unit_inverse_iff:
  forall u.
    ((exists v. Mul(u,v,2)) -> Unit(u)) and
    (Unit(u) -> exists v. Mul(u,v,2)).

dirichlet_signed_add_cancel_left:
  forall r a b e. Add(r,a,e) -> Add(r,b,e) -> a=b.

dirichlet_signed_add_solve:
  forall r e. exists y. Add(r,y,e).

dirichlet_signed_unit_multiply_involution:
  forall u a b. Unit(u) -> Mul(a,u,b) -> Mul(b,u,a).

dirichlet_signed_unit_multiply_cancel_right:
  forall u a b z. Unit(u) -> Mul(a,u,z) -> Mul(b,u,z) -> a=b.

dirichlet_signed_unit_affine_solve:
  forall r u e. Unit(u) -> exists x y.
    Mul(x,u,y) and Add(r,y,e).

dirichlet_signed_unit_affine_unique:
  forall r u e a b c d. Unit(u) ->
    Mul(a,u,b) -> Add(r,b,e) ->
    Mul(c,u,d) -> Add(r,d,e) -> a=c and b=d.
```

Neither affine endpoint assumes a difference, a product output, or a
solution witness. Its conclusion constructs the canonical input and actual
intermediate product. The uniqueness statement identifies canonical signed
codes, not arbitrary positive/negative representations or arithmetic-table
codes. Cancellation is guarded by the actual signed-unit predicate; the
module does not claim cancellation by signed zero or solvability for a
general nonunit coefficient.

## Proof construction and dependencies

The product classification obtains actual normalized decoder witnesses for
both factors. The old signed-multiplication equation and decoder normality
give four sign cases. In the equal-sign cases the nonzero magnitudes have
natural product one, so `mul_eq_one_components` fixes both magnitudes.
The mixed-sign cases imply a natural successor equals zero. The old decoded
cross-sum extensionality theorem then recovers the actual canonical codes.
All simplification steps emit ordinary HA certificates.

For addition, an actual signed negation and total signed addition construct
the required addend. Associativity and the additive inverse laws prove the
equation and cancellation. Each unit's actual square is positive one;
associativity and signed-multiplication functionality therefore prove that
multiplication by it is an involution. The affine solver constructs its
addend and then multiplies once by the same unit. The final uniqueness
proof uses signed-add cancellation followed by unit-multiplication
cancellation.

The factory is
`make_dirichlet_signed_unit_candidate_theorems`. Its nine rows are ordered
topologically. All external proof dependencies are inherited Alpha-v30
scalar theorems; there are no convolution, arithmetic-table, or new
cross-track theorem premises. Imports of existing formula helpers are not
additional proof premises.

External dependencies:

```text
mul_eq_one_components, mul_one, mul_zero_left, zero_add,
signed_decode_total, signed_decode_normal,
signed_decoded_balance_implies_code_eq,
signed_negate_total,
signed_add_total, signed_add_functional, signed_add_associative,
signed_add_zero_left, signed_add_negate_left_zero,
signed_add_negate_right_zero,
signed_mul_total, signed_mul_functional, signed_mul_associative,
signed_mul_one_right, signed_mul_of_decoded_equation,
signed_mul_to_decoded_equation.
```

## Verification receipt

The unchanged `candidate_validation.replay_candidate_bodies` checked every
actual body against its dependency-curried exact target. The parent data
were authenticated against the literal Alpha-v30 catalog SHA-256
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`
(3,222 Alpha entries, Stable 432). The full exact-FormulaDAG novelty audit
found no duplicate among these nine statements, all 3,756 previous
statements, or new peers. It authenticates the four previous research
generations without admitting them.

Final focused run:

```sh
PYTHONPATH=peano-lab/py PYTHONMALLOC=malloc \
  python3 peano-lab/py/tests/test_dirichlet_signed_unit_candidate.py \
  --pytest-select ''
```

Result: **215 tests passed**, 54.184 seconds, maximum observed RSS
497,631,232 bytes. The unchanged limits were 170/175 seconds soft/hard CPU,
180 seconds wall clock, and 1,536 MiB observed RSS. The final tests cover all
nine independently expanded statements and original-kernel bodies, all
36 dropped and 36 poisoned dependency cases, false/missing bodies,
miscoded and overstrong contracts, explicit-context hygiene and large
numerals, and diagnostic actual signed-witness equations for both units,
zeros, negative values, and nonunit obstructions. Large-term AST comparison
uses the existing iterative structural comparator, not a raised recursion
limit. Numerical diagnostics are not used as proof acceptance.

Inventory: 9 rows, 36 declared dependency edges, 401 tactic commands, 1,174
proof-node occurrences, 1,114 proof objects. Maximum body size is 672
occurrences; maximum depth is 48. Per-row `(occurrences, depth, objects)` in
factory order:

```text
(176,48,165), (672,44,623), (25,11,25),
(57,24,57), (33,20,33), (67,25,67),
(62,28,62), (27,18,27), (55,26,55).
```

Pins:

```text
source SHA-256:
263ae0497206cee991e34e08f03df3b1922fc4918e67d4d300887aa1ba7de4df
ordered full-specification SHA-256:
503e22e4a75aae8b39054144d2d3371f4c8c8f27ac584b18a1383d0e7c9660b7
ordered names SHA-256 (newline join, no trailing newline):
5fa7ad76083b6bd935f66698b4418e6ce85720b134ce19b40696ab87433a116c
product classification statement:
4c6820280f2a7c6e35eb66968d2f4819ea3276baa1af24e495ec1626e963db08
affine existence statement:
3c8f3184a683b282d0ef7f8d9f3671f71a9b9509599ff78b4ff47623c65660e4
affine uniqueness statement:
68b300d496090f0911613338c333747776a606c71fd28d4c82849bfca1c32d11
```

The candidate body receipt is not a complete empty-context proof-bundle
receipt. Complete ancestry replay, independent compiled-Lean verification,
and any later checkpoint packaging remain separate mandatory gates owned
by integration. This RFC makes no publication or admission claim; existing
kernel limits, Alpha membership, and frozen proof sources are unchanged.

Sources:

- [Candidate module](../../peano-lab/py/peano_lab/library/dirichlet_signed_unit_candidate.py)
- [Independent tests](../../peano-lab/py/tests/test_dirichlet_signed_unit_candidate.py)
