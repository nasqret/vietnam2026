# Constructed signed Dirichlet units and constant-one divisor transforms

Status: local, non-admitting constructive proof candidates, 2026-08-29.
The mathematical module is frozen after all 25 dependency-curried bodies
passed the original intuitionistic HA kernel. No Stable or Alpha membership,
publication, deployment, full G007 inversion, or G009 inverse criterion is
conferred by this document.

## Scope and exact data graphs

The source is
`peano-lab/py/peano_lab/library/dirichlet_units_candidate.py`.
Its only new public relation builders are:

```text
dirichlet_constant_one_table_relation(N,U,*,tag,variables)
dirichlet_kronecker_delta_table_relation(N,E,*,tag,variables)
```

Both accept strict HA terms in an explicit context and reject capture by
every generated binder. They reuse the existing actual paired-beta signed
table, signed lookup, and natural order graphs. Writing those existing
relations as `Table(N,F)`, `At(F,n,z)`, and `n<=N`, their exact meanings are:

```text
One(N,U) :=
  Table(N,U) /\
  forall n z. n!=0 -> n<=N -> At(U,n,z) -> z=2

Delta(N,E) :=
  Table(N,E) /\
  forall n z. n!=0 -> n<=N -> At(E,n,z) ->
    ((n=1 -> z=2) /\ (n!=1 -> z=0))
```

The natural codes `2` and `0` denote the signed integers one and zero. In
particular, the unit is not the Gaussian-integer code `6`. Only actual
canonical signed values are constrained; neither table codes nor their
positive/negative component representatives are asserted to be unique.

Index zero is unrestricted in both definitions. At `N=0`, the positive
domain is empty but a genuine represented table is still required. Neither
definition includes a convolution, sum identity, inverse, or desired theorem.

## Constructive endpoints

`Conv(F,G,n,z)` below is the separately defined convolution: an actual
product-or-zero summand table followed by an actual signed fold of its `S n`
entries. It explicitly requires `n!=0`. `CT(N,F,G,H)` is the actual
whole-table convolution graph. `DivisorSum(F,n,z)` is the existing, separately
defined divisor-mask fold, not a new synonym for convolution with one.

The constructors retain any requested signed code at zero:

```text
dirichlet_constant_one_table_exists:
  forall N w. exists U. One(N,U) /\ At(U,0,w)

dirichlet_kronecker_delta_table_exists:
  forall N w. exists E. Delta(N,E) /\ At(E,0,w)
```

The scalar and whole-table unit conclusions are:

```text
dirichlet_delta_right_sum:
  forall N F E n a.
    Table(N,F) -> Delta(N,E) -> n!=0 -> n<=N -> At(F,n,a) ->
    Conv(F,E,n,a)

dirichlet_delta_right_table:
  forall N F E. Table(N,F) -> Delta(N,E) -> CT(N,F,E,F)

dirichlet_delta_left_table:
  forall N F E. Table(N,F) -> Delta(N,E) -> CT(N,E,F,F)

dirichlet_delta_unit_exists:
  forall N F w. Table(N,F) -> exists E.
    Delta(N,E) /\ At(E,0,w) /\ CT(N,F,E,F) /\ CT(N,E,F,F)
```

The constant-one bridge preserves the existing divisor-sum definition:

```text
dirichlet_constant_one_sum_iff:
  forall N F U n z.
    Table(N,F) -> One(N,U) -> n!=0 -> n<=N ->
    ((Conv(F,U,n,z) -> DivisorSum(F,n,z)) /\
     (DivisorSum(F,n,z) -> Conv(F,U,n,z)))

dirichlet_constant_one_realizes_divisor_sum:
  forall N F w. Table(N,F) -> exists U.
    One(N,U) /\ At(U,0,w) /\
    forall n z. n!=0 -> n<=N ->
      ((Conv(F,U,n,z) -> DivisorSum(F,n,z)) /\
       (DivisorSum(F,n,z) -> Conv(F,U,n,z)))
```

Further rows prove actual entry lookups, append operations, positive
extensional uniqueness, and transport to different valid table encodings.
Positive extensionality deliberately does not compare zero entries.

## Proof construction

1. Start with the existing genuine signed singleton holding the chosen
   zeroth value. Ordinary finite induction appends signed one, or the
   constructively decided delta value. Both beta component streams are
   actually recoded, and the old signed prefix is preserved.
2. In a retained convolution summand, extract the actual equation `n=d*q`.
   For positive `n`, the quotient is positive and bounded by `n`, hence by
   `N`. If `d<n`, then `q=1` would imply `n=d`, a contradiction. Its delta
   value is consequently zero. Omitted summands are already zero.
3. At the final index `d=n`, construct the quotient `1`, read the actual
   delta entry `2`, and use checked signed multiplication by one.
4. Apply the separately proved signed zero-prefix/last-entry fold theorem.
   Then actually construct a convolution fold and identify its value with
   `F(n)`. Assemble its whole-table graph and use actual divisor-complement
   commutativity for the opposite multiplication order.
5. For a constant-one table, prove both directions between the actual
   convolution entry and the old divisor-mask entry. The same table code,
   component representation, prefix length, and signed-fold witnesses then
   give the two sum implications. No sum existence oracle is introduced.

The dependency order is the old authenticated 3,643-row basis, the current
convolution/finite-support/commutativity proofs, and these 25 rows. Current
cross-track prerequisites are ordinary authoring hypotheses until the
separate complete dependency closure is checked. The 125 latest inherited
research rows remain local and non-admitted; they are not reclassified as
published prerequisites or counted as new results.

## Original-kernel evidence and regression boundaries

One fresh job accepted every body with unchanged limits: CPU soft/hard
170/175 seconds, wall alarm 180 seconds, and peak RSS below 1,536 MiB.
The actual run took 37.45 seconds and peaked at 427,556,864 bytes.

```text
new rows                         25
declared dependency edges        82
tactic commands                1109
ordinary body-node occurrences  2037
distinct body objects           2031
largest individual body          257
maximum proof depth               43
```

The focused tests independently assemble the table graphs and eleven key
endpoint formulas; check all generated binder names, compound terms and
96-bit numerals; check actual beta-coded examples with signed values,
noncanonical component pairs, unrelated zero entries and re-encodings; and
reject altered bodies, missing/forged dependencies and false strengthened
domain or output contracts. Finite examples are diagnostics, not proof
authority. Exact formula comparison is iterative where shared large numeral
terms make recursive host-language equality unsuitable; no recursion or
kernel bound is raised.

The exact FormulaDAG novelty audit against all 3,643 prior statements and
the current dependency rows passed in 32.47 seconds, peaking at 391,725,056
bytes. None of these 25 rows duplicates an earlier statement, a current
prerequisite statement, or another row in this family.
The definition/model/contract window passed all 180 cases in 7.54 seconds,
peaking at 389,791,744 bytes.

The final complete focused suite passed **400/400 tests**: 25 original-body
checks, 194 hostile body/dependency/contract probes, 180 independent
graph/hygiene/model/contract tests, and one exhaustive novelty audit. Every
one of the 82 declared dependency edges is tested both by removal and by
replacement with the unrelated tautology `0=0`. The complete suite is split
into three disjoint fresh-process windows, with no skipped cases:

| Window | Cases | Seconds | Peak RSS, bytes |
| --- | ---: | ---: | ---: |
| Every edge removed | 82 | 73.93 | 431,308,800 |
| Every edge's statement replaced | 82 | 75.04 | 432,160,768 |
| All remaining checks | 236 | 74.82 | 460,570,624 |

Every process retains the same 170/175-second CPU limits, 180-second wall
alarm and 1,536-MiB ceiling. Run the focused test file with these exhaustive
selectors in separate bounded processes:

```text
actual_body_rejects_missing_or_forged_dependency and remove
actual_body_rejects_missing_or_forged_dependency and change_statement
not actual_body_rejects_missing_or_forged_dependency
```

The shared command prefix is
`PYTHONPATH=peano-lab/py:scripts PYTHONMALLOC=malloc python3 -m pytest -q
peano-lab/py/tests/test_dirichlet_units_candidate.py -k`.

These candidate-body checks validate ordered dependencies as hypotheses.
They are not a substitute for a self-contained original-HA proof bundle,
fresh empty-context principal-root replay, or independent compiled Lean
verification. Those integration gates remain separate and no result from
them is claimed here before it is obtained.

## Frozen mathematical identity

```text
source SHA256
4821a0e7a8ecac28080db207dd96abf4d02a285a85da6d1173b6a1349a82b77c

ordered complete theorem-spec digest
954a654694207db14acb799d843520fb12b3ff2233153b07cadb7bb5c7940911

ordered theorem-name digest
78e42e601e98fd7dbfbe51cb5b0c87672fbababdc4b5d07134f39b9af406d86d

dirichlet_delta_unit_exists statement SHA256
6924256ebdc7a4a8b46c532d5808e5794dea1430b6d1892c764a826191b4d710

dirichlet_constant_one_sum_iff statement SHA256
f502d0a59a4eb50a35be7b76d39904729a96e3d6d5c91d4e019a6aad9639908f

dirichlet_constant_one_realizes_divisor_sum statement SHA256
5aafb1de83c084f4d86aef3f3649ebc962a43b64c55c7356c45500c8db072d09
```

These hashes identify syntax and source bytes; they do not replace proof
checking. Existing mathematics, kernels, evidence, enrollment, limits and
published surfaces are unchanged. This family provides the actual unit and
constant-one ingredients for G007. Associativity and Möbius cancellation
must still be combined in a separate inversion proof, and the broader G009
classification of invertibility is not asserted.
