# Shared working map: shift, scalar and append laws

`working_append_notation.py` joins the exact frozen 15 shift, 10 scalar and
6 append specifications. It is a **source-only research map**, not an Alpha
reader, a proof-verification receipt or an associativity theorem.

The map retains all 2,656 native tactic commands and 31 exact statements.
Its three arrow kinds remain separate:

- 123 declared proof-dependency arrows;
- 141 theorem-to-definition use arrows, including local proof formulas;
- 43 expansion arrows among the 25 definitions used by this source map.

Proof paths use only declared proof dependencies among the supplied nodes.
External prerequisites are listed explicitly and are not marked resolved.
Every readable statement and local formula expands to the identical core AST.

The 398-definition/867-expansion working registry is unchanged. The original
397 public definitions remain identical objects, and the existing working
`ND0341 PolynomialShift` is reused. Scalar multiplication uses `ND0271`, left
padding uses `ND0334`, and formal equivalence uses `ND0336`. Append itself is
the existing conjunction of decoded-prefix equality and a witnessed next
entry; it does not introduce `ND0342` or any other new alias.

Generate the research-only JSON on stdout:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B research/arithmetic-library/working/prime-field-append-v1/working_append_notation.py
```

The source-order specification SHA-256 is
`9ae49cdf4c7d76b59171fcf3bfe099f8f20990a6b78ea1fc2c3d72f33c2a66e2`.
The generated stdout has 1,663,995 bytes and SHA-256
`8b29dc9878de6cbfddaab1c411dbabfd53347c6c21cb1cfaca0ac4224b6f3878`.
The generator pins all six mathematical source/test files and the two
inherited working-notation helpers; none is imported under a canonical
`peano_lab.library` alias.

The independent notation suite passed **43/43** cases in 4.938 seconds with
107,479,040-byte peak RSS, under the original 170/175-second CPU,
180-second wall and 1,536-MiB resource limits. It checks all actual statements
and local formulas, original definition identity, exact inventories, the
three arrow meanings, source mutations and absence of proof/admission claims.
These checks do not replace full-cone original HA, compiled Lean, ordinary
principal replay or current-catalogue novelty. Associativity and gcd/Bézout
remain open.
