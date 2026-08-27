# G072: constructive convergents and full best approximation

Status: additive, non-admitting proof candidates against the immutable Alpha
v28 basis. All 83 dependency-curried bodies have been accepted by the original
intuitionistic HA kernel. Closed dependency reconstruction, compiled Lean
verification, and Alpha enrollment remain distinct release gates. This RFC
does not promote anything to Stable or alter historical evidence.

## Exact goal and the planning correction

The natural-domain endpoint is
`continued_fraction_convergent_best_approximation`:

```text
forall a b s i u v.
  (ContinuedFraction(a,b,s) /\ Convergent(s,i,u,v)) ->
  forall r t C D.
    ~(t = 0) -> Lt(t,v) ->
    Abs(a*v,b*u,C) -> Abs(a*t,b*r,D) -> Le(C,D).
```

Here `Abs(x,y,d)` expands to `x=y+d \/ y=x+d`; `Lt` and `Le` are the
ordinary additive natural order graphs. Thus the conclusion is exactly
`|a*v-b*u| <= |a*t-b*r|` for every natural numerator `r` and `0<t<v`.
The error values are their actual arithmetic differences, not independently
supplied approximation certificates. Their existence and uniqueness already
have checked HA proofs.

The stronger endpoint
`continued_fraction_convergent_best_approximation_signed` replaces the
candidate numerator by **every** natural pair `rp,rn`, and its candidate error
is `Abs(a*t+b*rn,b*rp,D)`. It therefore covers arbitrary signed integers
`rp-rn`, including noncanonical representatives. A raw natural variable is not
silently reinterpreted as a signed code: the first theorem retains the exact
blueprint's natural domain; the second explicitly uses two natural components.

The old planning-only `Convergent` required both numerator and denominator
to be positive. That excludes a genuine initial convergent. For `a=1,b=2`,
the actual quotient list is `[0,2]`, encoded by the existing tagged cells as
`71`; its initial convergent is **0/1**, and its terminal convergent is 1/2.
The new definition permits the natural numerator zero and proves denominator
positivity from the computation. The checked theorem
`continued_fraction_initial_zero_over_one` establishes this boundary for
every actual G071 fraction satisfying `a<b`. No frozen definition or Alpha
v28 file was edited to make this correction.

The restrictions on the competing denominator matter. Dropping `t>0` admits
the zero vector with zero error. Replacing `t<v` by `t<=v` fails already for
the initial 0/1 convergent of 2/3: the candidate 1/1 has smaller error.
Tests preserve these concrete counterexamples.

## Genuine computations and the conservative definition DAG

For a quotient `q`, write `M(q)=[[q,1],[1,0]]`. An actual prefix of the
existing tagged quotient list computes

```text
M(q0) ... M(qi) = [[u,U],[v,V]].
```

The proof certificate is built backwards by prepending quotient cells, in
the same direction as the existing G071 Euclidean history. This reverses the
*construction order*, not the continued fraction's numerical value or the
forward quotient order.

The finite matrix trace starts with the identity matrix at an unconsumed tail
and performs only the following actual transition:

```text
Cell(newList,q,oldList)
newu = q*oldu + oldv     newU = q*oldU + oldV
newv = oldu              newV = oldU.
```

Its state code uses the existing doubled-Cantor pairing polynomial. Three
existential intermediate codes share the nested construction conservatively:
`left=Pair(u,U)`, `right=Pair(v,V)`, `matrix=Pair(left,right)`, and
`state=Pair(list,matrix)`. A beta entry then stores this state. No pairing
function, definition axiom, trusted matrix primitive, or kernel extension is
introduced.

The definition roles form this DAG:

```text
NatPair ────────────────> ConvergentMatrixStateCode
BetaAt + StateCode ─────> ConvergentMatrixStateAt
StateAt + Cell + Lt ────> ConvergentMatrixTrace
MatrixTrace + i+1 + v≠0 -> Convergent

Abs + ordinary order ──> ApproximationError / BestApproximationSecondKind
actual determinant and errors -> derived ConvergentErrorInvariant
```

The final line is a **proved invariant**, never a premise hidden inside
`Convergent`. The latter contains only a genuine `(i+1)`-step matrix
computation and the positive-denominator guard. It contains no determinant,
coprimality, decreasing-error, or best-approximation assertion.

Public builders accept strict compound HA terms with an explicit variable
context. Every generated binder is checked against the entire declared
context, including unused variables and all nested legacy beta binders.
Different valid binder tags give alpha-equivalent formulas. The final tests
exercise every generated binder individually, not only the outer names.

## Proof structure

1. Small arithmetic lemmas preserve the actual determinant and signed errors
   when a Euclidean quotient is prepended. The empty matrix gives the exact
   initial error values `b,a`.
2. A determinant-one matrix represents any signed candidate vector using its
   explicit cofactor coefficients. Constructive natural order produces all
   four sign cases. For `0<t<v`, only the two subtractive sectors remain
   (with the zero-current-coefficient boundary included).
3. Opposite errors in a subtractive sector add as `c*E+d*F`; no cancellation
   is assumed away. The positive coefficient and `E<=F` give the complete
   comparison with the candidate's actual absolute error.
4. G071's beta history has unique decoded dividend/divisor/list coordinates
   and exposes its actual first quotient, strict remainder, and shorter
   history. The new matrix trace independently exposes its actual first
   quotient, tagged tail, and four recurrence equations.
5. Cell injectivity aligns these two genuine computations. Ordinary HA
   induction on the consumed prefix derives determinant `+1` or `-1`, the
   two alternating errors, `E<F`, and `F<=b`. Denominator positivity follows
   from these proved equations. Applying the arithmetic comparison now
   yields the unconditional G072 endpoint.
6. Separate finite constructions prove every valid prefix exists. Induction
   proves every actual prefix is in range and its entries are unique.
   Another induction identifies the second column with the actual previous
   prefix of the **same original list**. Thus the adjacent determinant is a
   theorem about two real indexed convergents, not an arbitrary auxiliary
   vector.
7. The initial matrix is exactly `[[q,1],[1,0]]`, including `q=0`. Induction
   through the complete history proves the terminal cross-product equality
   `a*v=b*u`; a terminal convergent is constructed explicitly. Every actual
   convergent is reduced by the checked determinant-to-coprimality lemma.

The intermediate unimodular comparison theorem explicitly has determinant
and error premises. It is **not** presented as the final G072 theorem. The
public endpoints derive all those premises from G071 and the actual prefix
computation.

## Principal checked endpoints

- `continued_fraction_convergent_best_approximation`
- `continued_fraction_convergent_best_approximation_signed`
- `continued_fraction_convergent_exists_unique_at_history_index`
- `continued_fraction_convergent_index_is_valid`
- `continued_fraction_adjacent_convergent_determinant`
- `continued_fraction_convergent_coprime`
- `continued_fraction_initial_zero_over_one`
- `continued_fraction_has_exact_terminal_convergent`

Supporting roots include
`cf_convergent_actual_prefix_error_invariant`,
`cf_convergent_every_valid_matrix_prefix_exists`,
`cf_convergent_matrix_prefix_functional`,
`cf_convergent_second_column_is_previous_prefix`, and
`cf_convergent_full_matrix_is_exact`.

These results concern the finite rational continued fractions of G071, whose
public inputs are positive naturals. They do not claim irrational infinite
continued fractions, periodicity, Pell's theorem, Legendre's converse, or
first-kind error minimization `|a/b-r/t|`. The public G071 input guards remain
unchanged; zero *numerators of convergents*, zero *terminal error*, the empty
auxiliary prefix, and excluded zero competing denominators are handled
explicitly rather than confused with an extension of that input domain.

## Files, exact inventory, and verification

Factory order is significant:

1. `peano_lab.library.continued_fraction_approximation_candidate`
   exposes `make_continued_fraction_approximation_candidate_theorems`:
   39 rows, 140 dependency edges, 1,461 commands.
2. `peano_lab.library.continued_fraction_convergents_candidate`
   exposes `make_continued_fraction_convergents_candidate_theorems`:
   44 rows, 107 dependency edges, 2,542 commands.

Combined: **83 rows, 247 edges, 4,003 commands**. Inspection of the actual
checked certificates found and removed 37 redundant dependency hypotheses;
the final audit found no unused declared dependency. The checked bodies have
9,468 proof-node occurrences, 9,203 actual proof objects, and maximum depth
96. The largest expanded statement is 28,715 UTF-8 bytes. No proof limits,
arithmetic rules, kernel, proof engine, historical provider, or old evidence
were changed.

The final fresh-process body/usage audit completed in 72.99 seconds with
291,389,440 bytes peak RSS. Authoring used the unchanged proof limits and
bounded processes (170 CPU seconds, 180 wall seconds, and the existing
1,536 MiB owned-process RSS guard), never relaxed caps or an admission bypass.

The pinned parent catalogue is
`artifacts/peano-library/alpha/catalog-v28.json`, SHA-256
`897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`:
2,764 checked entries with Stable 432 unchanged. Tests reconstruct the exact
parent `TheoremSpec` hypotheses from those bytes without importing historical
edition/provider snapshots. This lightweight authoring basis does **not**
confer closed-use authority; full release reconstruction is a separate gate.

The two mathematical source SHA-256 values are respectively:

```text
a9074eacabc922aaf57dd7ef7eb5210ca23fe70679db334a8a283dfe2ad33e59
f97eb7e8e34ad04b5c7089cdbf44641fe4ee00608371ea509b5fd07104d78aa9
```

The newline-terminated ordered 83-name inventory has SHA-256
`837683363179ce24056cd96e6a313df8f96aee1dddb8378addd934ea79de6e44`.
Seven principal statement literals are pinned independently in the focused
tests, alongside explicit AST reconstructions of both full G072 contracts.

The focused suites are
`peano-lab/py/tests/test_continued_fraction_approximation_candidate.py` and
`peano-lab/py/tests/test_continued_fraction_convergents_candidate.py`.
They cover every original-kernel body, every poisoned body, source inventory,
strict HA ASTs and exact endpoints, all generated-binder/context collisions,
guard/computation mutations, signed representatives, all positive input pairs
up to 16, large and long-history cases, and independently constructed concrete
beta witnesses for the actual old and new computation equations.
Numerical model tests are supplementary checks, not proof oracles.

Final complete focused run: **660 passed in 79.75 seconds**, peak RSS
299,778,048 bytes, including all 83 original-kernel body checks. All seven
principal statement pins, both independently reconstructed G072 AST contracts,
and every binder/context mutation were checked in that same run.

```sh
PYTHONPATH=peano-lab/py PYTHONMALLOC=malloc python3 -m pytest -q \
  peano-lab/py/tests/test_continued_fraction_approximation_candidate.py \
  peano-lab/py/tests/test_continued_fraction_convergents_candidate.py
```

The complete closed HA/Lean bundle, release receipt, conservative definition
registry, planning erratum, Alpha snapshot, and any website publication belong
to the subsequent additive release integration, not these candidate files.
