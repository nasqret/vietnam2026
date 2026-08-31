# Working definition map through the associativity append step

`working_associativity_notation.py` joins the frozen 15 shift, 10 scalar,
6 append, 1 shift-equivalence and 3 append-step specifications. It is a
source-only research map, not a proof-acceptance mechanism or public reader.

The final scoped step source contributes to 35 exact statements and 3,916
native tactic commands. The three arrow kinds are kept separate:

- 166 declared theorem-dependency arrows;
- 173 theorem-to-definition uses, including local proof formulas;
- 43 expansion arrows among the 25 definitions used here.

The map lists 69 external proof prerequisites without marking them resolved.
Paths traverse only declared proof-dependency arrows between supplied nodes.
Neither a definition-expansion edge nor a theorem's use of a definition is
treated as evidence that a theorem has been proved.

All 397 inherited public definitions remain identical objects. The existing
working `ND0341 PolynomialShift` is reused; there is no additional alias.
Scalar multiplication, left padding and formal equivalence continue to use
`ND0271`, `ND0334` and `ND0336`. Every readable theorem and local formula is
independently expanded and compared with its original core AST.

Generate the research-only JSON on stdout:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B research/arithmetic-library/working/prime-field-associativity-step-v1/working_associativity_notation.py
```

The exact source-order specification SHA-256 is
`60a14dc8aecb17f7a2e5f43ccb11d05f520e0277e6604e51c8440974640dbba9`.
Generated stdout is 2,440,077 bytes with SHA-256
`10c24f73e9a25d39eed08019879a47e3ac35a4893561f782de332cb430067987`.
Fourteen exact source/test/helper pins are mandatory before and after use.

The final independent notation suite passed 52/52 distinct cases and all
156 setup/call/teardown phases in 5.448 seconds, with 90,521,600-byte peak
RSS. This is a fresh run against the final scoped step, not credit reused
from the earlier provisional map. The unchanged 170/175-second CPU,
180-second wall and 1,536-MiB bounds apply. Exact invocation, cases, hashes
and observations are in `notation-observations-v1.json`.

This map includes the induction step but not the universal induction. See
`../prime-field-associativity-induction-v1/NOTATION.md` for that extension.
Neither map accepts HA/Lean proofs, admits Alpha entries, publishes a page,
or declares associativity or gcd/Bézout complete. Those statuses belong to
the separately checked dependency-complete proof checkpoint.
