# Working map through actual left units and reflexive divisibility

This source-only map extends the exact 44 predecessor by eight native
left-unit/reflexivity candidates. It has 52 statements, 5,256 commands,
234 actual declared proof arrows, 238 definition-use arrows and 46
definition-expansion arrows among the 26 definitions used here. The full
working registry is still 399 definitions and 870 expansion arrows: every
predecessor object is reused and no new alias is introduced. In particular,
self-divisibility uses the existing `ND0342 FpPolynomialRightDivides`.

The graph has ten supplied-proof layers and 83 explicitly unresolved external
prerequisites. Only proof-dependency arrows determine paths. Definition
expansion never grants a proof, and a source node never closes gcd/Bézout.

Generate the source map on stdout with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B research/arithmetic-library/working/prime-field-left-unit-v1/working_left_unit_notation.py
```

All 26 source/test/prior-map pins are required before and after generation.
The ordered-specification SHA-256 is
`c6c4b0610b911d1f17a8b0ef2b6fa4b8f7b79e73e7f1f85f0fe2d6b1a42edc63`.
Generated stdout has 3,472,374 bytes, SHA-256
`0ff055011baf37f0a2dc1b2175a56cedab99c4cf0f61c1e0f331da097487274b`.

All 91 independent notation cases passed, including all 52 statements and
compacted local formulas, unchanged 399 identities, all 26 pin mutations,
invalid/forward graphs, and separation of the three arrow meanings. The run
took 10.179 seconds with 92,585,984-byte peak RSS under the original limits.
Exact invocations and 273 passed phases are in
`notation-observations-v1.json`. Independent read-only review also passed
on the exact helper/test bytes; it did not rerun tests or confer proof authority.
Proof acceptance, admission, publication, left-unit, reflexivity and
gcd/Bézout proof flags remain false in this syntax artifact by design.
