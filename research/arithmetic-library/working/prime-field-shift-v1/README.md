# Actual polynomial shift: working checkpoint

This is new working mathematics toward convolution associativity, then
polynomial gcd/Bézout. It is **not an Alpha admission or public proof release**.
The source contains 15 exact theorem specifications, 46 declared dependency
edges and 1,033 tactic commands. All 15 bodies pass the original conditional
HA checker with only their declared, canonical prerequisite formulas. The
later [combined 25-law checkpoint](../prime-field-associativity-v1/README.md)
also passed current-parent novelty, dependency-complete original HA,
same-byte compiled Lean and all seven ordinary principal replays. The local
conditional and notation records below remain separate kinds of evidence.

## Meaning and mathematical boundary

Highest-degree-first coefficients require a genuine trailing-zero operation:

```
PolynomialShift(b,c,L,d,e)
  := BetaPrefixEqual(b,c,d,e,L) /\ BetaAt(d,e,L,0).
```

Its target length is `S L`. Unlike harmless leading-zero padding, this is
multiplication by `X`. No primality, coefficient bounds, covariance conclusion
or raw beta-code equality is hidden in this definition. The constant
coefficient is zero; the coefficient at power `S k` is the old coefficient
at power `k`. These are formal coefficients, not finite-field evaluations.

The principal right-shift covariance compares an actual product with a
shifted right factor to **every actual shift** of the old product, by formal
coefficient equivalence. It works at any nonzero modulus. For nonempty
factors the new product length is `S N`; for empty factors that uniform
length assertion is false, and the theorem handles the actual product
lengths separately. Primality is used in the additional constructive
existence principal that produces the new product and comparison shift.

## Conservative definition and proof DAGs

`working_shift_notation.py` preserves all 397 canonical definition objects
and adds working-only `ND0341 PolynomialShift`. Its 398-definition registry
has 867 expansion edges. The actual local source map contains 15 theorem
nodes and 20 used definitions, with three explicitly distinct arrow kinds:

- 46 declared proof-dependency edges;
- 47 theorem-to-definition use edges, including local proof formulas;
- 31 expansion edges within the displayed definition closure.

Only proof-dependency edges participate in proof paths. External prerequisite
names remain visibly unresolved in this source-only map. Every compacted
statement and local `have`/`suffices` formula re-expands to its exact core
AST, including compound terms, large binary numerals and colliding binders.
The production Alpha release registry remains 397 definitions; this working
alias is not silently inserted into the public release.

Generate the source-only JSON on stdout with:

```
PYTHONDONTWRITEBYTECODE=1 python3 -B research/arithmetic-library/working/prime-field-shift-v1/working_shift_notation.py
```

`working_shift_scalar_notation.py` joins these 15 specifications with the
10 frozen scalar-convolution specifications without adding a scalar alias.
Its combined source map has 25 theorem nodes, 22 used definitions, 81 declared
proof edges, 86 definition-use edges and 36 local expansion edges. All 1,778
source commands are retained. The additional 33-test combined-notation suite
passed in 4.551 seconds with 109,936,640-byte peak RSS; its sources, scripts,
three edge kinds and explicit non-proof status are independently checked.
Both notation suites also passed together: 105/105 cases, 23.524 seconds,
106,758,144-byte peak RSS, with the original 170/175-second CPU,
180-second wall and 1,536 MiB limits.

## Actual observations and remaining gates

`conditional-observations-v1.json` records the frozen mathematical source and
test identities: 462 distinct source/model/conditional-HA/negative cases
passed in five original-bounded windows. Its `registry_changed: false`
records that mathematical test run, before the separate working notation
registration was added. It is a non-authorizing observation, not a receipt.

The separate notation suite passed **72/72** cases in 21.917 seconds with
93,519,872-byte peak RSS. It checks independent lower-vocabulary contracts,
binder hygiene, all actual statement and local-formula roundtrips, inherited
identities, DAG edge separation and rejection boundaries. No Alpha edition
or proof service was loaded by that suite.

Those complete-checkpoint gates subsequently passed in nine fresh processes;
their [exact observations](../prime-field-associativity-v1/final-verification-observations-v1.json)
cover these unchanged 15 rows and the 10 scalar rows together. No saved
observation authorizes a later admission, and no Alpha row is added here.
Associativity, arbitrary-identity-pair division uniqueness, polynomial
gcd/Bézout and full G091 are not established by this 25-law checkpoint.
