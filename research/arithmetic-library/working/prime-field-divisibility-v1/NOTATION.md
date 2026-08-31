# Combined working map through right-factor divisibility

`working_divisibility_notation.py` combines the exact 37 shift/scalar,
append and associativity specifications with seven right-divisibility
specifications. The 44-row map retains all 4,790 native tactic commands.
It is research syntax, not a public reader or proof-acceptance mechanism.

The three arrow meanings remain separate:

- 199 actual declared proof dependencies;
- 206 theorem-to-definition uses, including local proof formulas;
- 46 definition-expansion arrows among the 26 definitions used here.

The supplied theorem graph has ten layers. Its 73 external proof
prerequisites remain explicitly unresolved by this syntax map. Proof paths
use only declared theorem-dependency arrows among the supplied statements.

All 398 predecessor definition objects are preserved. The only addition,
working `ND0342 FpPolynomialRightDivides`, expands through canonical target
coefficients (`BetaPrefixInto`), actual multiplication (`FpPolyProduct`)
and formal all-power equality (`PolynomialEquivalent`). It witnesses
`A ≃ Q*D`; the divisor is the right factor. The combined working registry
has 399 definitions and 870 expansion arrows. The public registry is unchanged.

Generate the source-only JSON on stdout:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B research/arithmetic-library/working/prime-field-divisibility-v1/working_divisibility_notation.py
```

Its ordered-specification SHA-256 is
`6ecade7114e2d718b6a564a19d98c981b0236e1e6c6e622caaa0dff43fc95129`.
Generated stdout has 3,213,917 bytes and SHA-256
`e83d486e06a9b13b1b3dceab1fd3f6982354feb87733cb257ca69752bfa4f925`.
All 22 mathematical source/test/prior-map pins are required before and after
use. Public and working definition identities are not replaced or shadowed.

The independent suite passed 81/81 distinct cases and all 243 phases in
9.935 seconds, with 94,617,600-byte peak RSS, under the original limits.
It independently expands every theorem and compacted local formula back
to its exact core AST, checks the new definition's three real parents,
and rejects changed pins, cycles, forward edges and definitions passed as
proof prerequisites. Exact observations are in `notation-observations-v1.json`.

The map includes the induction and the divisibility sources while every
proof-acceptance, admission and publication flag remains false. It cannot
close associativity, divisibility, gcd/Bézout or G091 by rendering a node.
