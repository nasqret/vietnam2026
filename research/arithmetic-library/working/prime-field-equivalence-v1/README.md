# Formal polynomial equivalence and operation congruence

Working continuation of the verified
[113-row Euclidean checkpoint](../prime-field-euclidean-v1/README.md).
That directory, its theorem sources and its proof artifacts are unchanged.
Alpha remains v32 with 3,971 checked-use theorems; Stable remains 432.

The combined checkpoint contains 121 working rows: the preserved 113 plus
eight new lemmas. All eight actual conditional HA bodies and all 898 cases
in the final joint test suite passed. Dependency-closed HA and independent
same-byte compiled Lean passed again under the corrected test-only input
identities, as did all four ordinary-principal replays. No new Alpha
admission or public deployment was performed.

## The new mathematical bridge

The four principals derive actual left-padding witnesses from formal
coefficient equivalence, then prove that actual addition, subtraction and
convolution respect that equivalence across representation lengths:

- Equivalence at lengths `L` and `t+L` implies the actual `t`-entry left-pad
  relation, without a primality or canonical-encoding premise.
- Actual aligned addition and subtraction over a prime field respect
  equivalent inputs when the two operations use different lengths.
- Actual convolution respects equivalent inputs in both factors, with all
  four input lengths independent. A nonzero modulus is sufficient here.

Two additive padding-output lemmas and two one-factor convolution lemmas
support these four endpoints. Intermediate outputs are genuinely
constructed, not assumed equal to the desired result. Empty representations,
mixed length directions and characteristic two are covered. Conclusions are
formal coefficient equivalence, never raw beta-code equality or equality
merely of evaluation functions over a finite field.

The proof idea is short even though the expanded arithmetic formulas are
large. First construct a padded copy of the shorter representation. Formal
equivalence and equal-length coefficient uniqueness identify its prefix
with the supplied longer representation. For addition/subtraction, construct
the padded old output and use operation functionality to identify it with
the supplied new output. Constructive comparison of the two lengths then
handles either padding direction.

For convolution, the same argument handles one factor at a time using the
previously proved padding laws. The two-factor result constructs a genuine
mixed product, relates the first output to that product, and then relates
it to the second output by transitivity. It does not require associativity.

## Conservative definitions and evidence

The identical 397-definition registry and its 865 expansion arrows are
reused. All eight statements compact and re-expand to their exact closed
core ASTs; four independent named principal contracts also pass outer-binder
hygiene checks. The final 43 notation/DAG tests passed.

The [source-only notation map](source-notation-dag-v1.json) contains eight
theorem nodes and 21 existing definitions, with three separate arrow kinds:
37 declared proof dependencies, 20 definition-use edges and 35 definition
expansions. Its paths cover supplied theorems only; external proof
prerequisites are explicitly unresolved. This syntax map is not a proof
receipt or a deployed interactive explorer.

The [final joint test record](combined-verification-observations-v1.json)
contains 898 passing cases: 368 representation/additive, 353 convolution,
134 integration/ownership and 43 notation/DAG cases. It includes actual
conditional HA, independent contracts, beta models, missing/poisoned
dependencies and rejected stronger conclusions. It passed in 114.61 seconds
at 168,738,816 bytes RSS under the original limits.

The joint run exposed and then resolved an import-scope alias leak in the
two focused test modules. All 898 ordered test IDs, all original assertions,
all mathematical source bytes and the proof artifact were preserved. The
[initial failure](combined-test-isolation-failure-observation-v1.json) and
[two-order cleanup checks](import-isolation-smoke-observations-v1.json) are
retained. Earlier [individual focused](focused-proof-observations-v1.json)
and [notation observations](notation-verification-observations-v1.json)
retain their historical test hashes, not the final test identity. The latter
also records the unchanged map-generation command. These saved observations
never replace actual proof checking.

The source-binding and complete-proof rules are in the
[working RFC](working-polynomial-equivalence-rfc-v1.md); the roadmap is in
[the continuation plan](../../../../PLAN/24_polynomial_equivalence_and_gcd_bridges.md).

## Complete proof artifact

The [actual proof bundle](artifacts/working-equivalence-proof-bundle-v1.json)
has 377 nodes: 255 inherited Alpha theorems, 121 working theorems and one
packaging node. It has 1,071 dependency edges and 30,527 body nodes. The
2,449,379-byte file has SHA-256
`6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf`.

Authoring freshly checked all 368 nodes in the old seed, retained 367
mathematical bodies, rebuilt one inherited addition-functionality body and
the eight new bodies, and checked the entire resulting bundle. This passed
in 69.98 seconds at 1,053,179,904 bytes RSS under the unchanged limits.
The final whole-bundle HA/same-byte compiled Lean gate passed under the
corrected test identities in 42.17 seconds at 1,277,902,848 bytes RSS. Its
before/after source binding is
`33af357c30aca8f5bb6f2d838ef6cb4dd3f608dd90e6443e06d69a45f7a2a0c0`.
All four ordinary endpoint replays also passed with actual empty-context
certificates: 8,711 nodes for equivalence-to-padding, 10,075 for addition,
10,163 for subtraction and 17,731 for convolution. Each run first checked
the complete bundle, then replayed and checked the exact principal. The five
final windows shared this same source binding and artifact; their largest
single window was 48.33 seconds and 1,288,896,512 bytes RSS.

The [complete verification record](working-121-verification-observations-v1.json)
retains exact commands, source/artifact identities and measured results.
These are observations, not an alternative proof checker. To rerun the full
HA/same-byte Lean gate from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONMALLOC=malloc PYTHONPATH=peano-lab/py:scripts python3 -B research/arithmetic-library/working/prime-field-equivalence-v1/check_working_equivalence.py --task bundle
```

Use `--task root --name THEOREM_NAME` for a separate ordinary window; the
four exact names are listed in the working RFC. The checker retains the
original CPU, wall, memory, codec, kernel and compiler limits.

## Remaining work

Convolution associativity, scalar/unit laws, full polynomial gcd/Bézout,
arbitrary formal-identity division-pair uniqueness and G091 remain open.
Neither the old 113-row checkpoint nor this overlapping 121-row checkpoint
is added to Alpha by these working files.
