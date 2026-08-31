# Working definition map including the full induction source

`working_induction_notation.py` extends the frozen 35-row append-step map
with the actual empty-right base and the universal rightmost-length
induction. Including their source is not proof acceptance.

The map retains 37 exact statements and 4,303 native tactic commands:

- 179 declared theorem-dependency arrows;
- 182 theorem-to-definition uses;
- 43 expansion arrows among 25 used definitions.

Seventy-one external proof prerequisites are listed but not marked resolved.
Paths use only declared proof-dependency arrows between supplied nodes.
The induction's base and append-step dependencies are actual source edges,
not inferred from names, shared definitions or an informal diagram.

The unchanged working registry has 398 definitions and 867 expansion edges.
The 397 public definitions remain identical objects, and the sole working
shift abbreviation `ND0341` is reused. No induction or associativity alias
is introduced. The readable statements and every compacted local formula
expand to exactly the original core AST, including binder scopes.

Generate the research-only JSON on stdout:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B research/arithmetic-library/working/prime-field-associativity-induction-v1/working_induction_notation.py
```

The exact source-order specification SHA-256 is
`de95fea3806bc6c227c032bf2c29095ce191e27624c2196bd417df6c77c31491`.
Generated stdout is 2,746,804 bytes with SHA-256
`330b830e13a7d7b84e19216230166a95dd1b09df8f3e83bb09f2546b610a8758`.
Eighteen exact source/test/helper pins are checked before and after use.

The independent notation suite passed 58/58 distinct cases and all 174
setup/call/teardown phases. The retained final run took 5.670 seconds with
90,750,976-byte peak RSS under the original 170/175-second CPU,
180-second wall and 1,536-MiB bounds. Repeated runs add no case credit.
The exact invocation, case inventory and hashes are recorded in
`notation-observations-v1.json`.

`full_induction_included` is true while all proof-acceptance, admission and
publication flags remain false. This separation is intentional even when
a separate proof bundle subsequently passes its kernel and Lean checks.
This syntax map cannot establish associativity or gcd/Bézout by itself.
