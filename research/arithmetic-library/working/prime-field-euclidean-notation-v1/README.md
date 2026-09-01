# Source-only Euclidean algebra notation

This map extends the exact 68-row alignment map to 95 working source rows.
The order matches the separate staged integration plan: prior 68, aligned
algebra 4, identity 2, distributivity 2, left-constant 6, normalization 5,
Euclidean transport 5, and backward Bézout 3. There are 436 declared direct
prerequisites and 10,067 proof-script commands.

All 402 prior definition objects and 876 expansion arrows are preserved.
Only two conservative aliases are added:

- ND0346 FpPolynomialCommonRightDivisor, arity 10: the literal conjunction
  of two actual FpPolynomialRightDivides graphs.
- ND0347 FpPolynomialBezoutRepresentation, arity 16: two existentially
  witnessed proper products and their actual aligned sum.

The resulting registry has 404 definitions and 879 expansion arrows.
Neither alias asserts a greatest divisor, existence of a gcd, a divisibility
law, or a completed Euclidean algorithm. Formal coefficient equivalence is
not replaced by evaluation equality or equality of beta codes.

The original compactor is reused. Proof dependencies, actual definition uses,
and conservative definition expansions are distinct arrow kinds; displayed
proof paths use only supplied proof-dependency edges. External prerequisites
remain explicitly unresolved. The literal subtraction permutation remains
visible without fabricated usage edges when the unchanged compactor chooses
its older addition spelling.

All 257 independent syntax/AST/ownership/rejection cases passed, including
exact statement and local-formula round-trips for all 95 rows. The
[observation](source-notation-observations-v1.json) records 771 passed phases,
48 unchanged source pins, preservation of the sealed archives/runtime, and
the exact commands. Ordered specifications:
8475015338684d25c6dbbe3bd384f46a6fec25663dbdd1d668e211bd9059208b.

This module and test suite call no proof checker or Alpha catalogue. Their
output is source syntax only, never proof, admission or publication authority.
G091 and the completed polynomial gcd/Euclidean algorithm remain open.
