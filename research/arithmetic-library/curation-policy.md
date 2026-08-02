# Conservative arithmetic-library curation policy

This document governs the next edition of the native Peano Lab library. Its
purpose is to make statements and intermediate propositions read like
mathematics while preserving exactly the existing first-order PA language and
certificate checker.

## Non-negotiable invariant

Every named relation is an untrusted authoring macro:

```text
defined source
    ↓ hygienic expansion
ordinary Term / Formula AST
    ↓ exact AST identity check
ordinary TheoremSpec and tactic commands
    ↓ certificate construction
ordinary kernel or canonical Lean verification
```

No definition name, persistent `PD` tag, theorem name, registry hash, or
documentation page may survive as logical authority in a checked certificate.
The trusted term language remains `0`, `S`, `+`, and `*`; the trusted formula
language remains equality, falsity, first-order connectives, and quantifiers.
The only proof-grammar extension in the current library is the independently
checked self-contained `Cut` sharing rule.

## Definition tiers

### P0: canonical general-purpose facade

Freeze these eleven relations first:

| ID | Relation | Required role |
|---|---|---|
| `PD0001` | `Le(a,b)` | order witness |
| `PD0002` | `Lt(a,b)` | strict-order witness |
| `PD0003` | `Dvd(d,n)` | divisibility witness |
| `PD0004` | `Prime(p)` | expanded factor-pair primality |
| `PD0005` | `Coprime(a,b)` | common-divisor relation |
| `PD0006` | `IsGCD(g,a,b)` | relational gcd |
| `PD0007` | `DivRem(n,d,q,r)` | quotient/remainder graph |
| `PD0008` | `ModEq(m,a,b)` | balanced natural congruence |
| `PD0013` | `BetaAt(b,c,i,x)` | finite-prefix decoding |
| `PD0014` | `Product(b,c,n,p)` | prefix-product trace |
| `PD0015` | `Sum(b,c,n,s)` | prefix-sum trace |

Each receives one canonical AST-first builder and one reviewed template owner.
Private string builders are migrated in this order: `Lt`, `Dvd`, `Prime`,
`Coprime`, `IsGCD`, `DivRem`, `ModEq`, then `BetaAt`. Existing expanded
statements remain the comparison oracle during migration.

### P1: reusable finite arithmetic and number theory

After P0 stabilizes, consolidate parity, small residues, finite folds,
quadratic residue, factorial, bounded-map, and factorization relations. These
definitions may depend only on earlier P0/P1 entries, and their graph must be
acyclic.

### P2: campaign-specific surfaces

Inverse-prefix and division-prefix relations remain visibly namespaced to the
quadratic-reciprocity campaign. A P2 relation is promoted only when a second
independent theorem family uses it or when it captures a mathematically stable
interface with a complete API.

The adjacent composites `BalancedBezout`, `PermutationPrefix`, and
`CanonicalPF` receive new persistent IDs only after occurrence and API review.
Existing `PD0001`–`PD0040` identifiers are never recycled.

## Relation API matrix

A relation is curated only when its row records the following, using
`not_applicable` rather than silence where necessary:

| API family | Typical contents |
|---|---|
| Introduction | constructors and canonical witnesses |
| Elimination | projections, bounds, nonzero consequences |
| Boundary | zero, one, successor, empty-prefix cases |
| Characterization | equivalence, uniqueness, or functionality |
| Transport | equality, congruence, addition, multiplication, recoding |
| Decision/search | constructive bounded decision or explicit blocker |
| Composition | transitivity, append, restriction, extension, Euclidean step |

The matrix distinguishes a definition from a useful library. For example,
adding `Prime(p)` is not complete until its nonzero, divisor, decision,
prime-divisor, and Euclid interfaces have reviewed dependencies.

## Theorem curation rules

1. State the theorem at the most general native level already supported by its
   proof. Fixed numerals belong in generated clients unless they express an
   irreducibly small boundary theorem.
2. Prefer one canonical orientation and derive symmetric variants through
   named transport lemmas.
3. Give every public theorem a stable name, persistent proof-explorer tag,
   informal statement, dependency list, constructive/classical label, source
   provenance, and exact expanded formula.
4. Defined theorem statements and typed `have`/`suffices` propositions must
   expand immediately to ordinary formulas. Unannotated tactic commands are
   unchanged.
5. Reject duplicate theorems modulo alpha-renaming, obvious symmetry, or a
   registered definition expansion unless the duplicate is a deliberate API
   alias documented as such.
6. Keep generated families separate from curated general lemmas. Record the
   generator and parameters for every generated row.
7. A theorem is `public_checked` only after empty-context replay and mutation
   gates. Body-checked campaign nodes retain their candidate status in the
   readable edition.

## Paired-edition equality gates

For every readable/expanded pair require:

- identical parsed expanded statement AST;
- identical dependencies and status;
- identical expanded proposition AST for each rewritten `have` or
  `suffices` command;
- identical authored command after expansion;
- identical final certificate where construction is deterministic, otherwise
  separate valid certificates with recorded hashes;
- no definition node in the proof-dependency DAG;
- definition nodes and notation edges shown only in the mixed reading graph,
  with a distinct shape and color;
- round-trip, capture, shadowing, wrong-arity, unknown-name, dependency-cycle,
  and registry-drift tests.

## Release artifacts

Each curated edition ships together:

- the explicit and readable theorem corpora;
- the persistent definition registry and definition DAG;
- the relation API-completeness matrix;
- expansion receipts and source/certificate hashes;
- proof-only and mixed dependency graphs;
- linked Proof Explorer definition/theorem pages;
- paired training rows (`defined_source`, `expanded_source`, feedback,
  certificate identity);
- Jupyter Book chapters and Obsidian notes;
- a kernel/Lean-verifier identity receipt that is separate from presentation
  and corpus-generation receipts.

## Immediate next tranche

The verifier prerequisite is closed: Cut-aware source
[`ab966fd1`](https://github.com/nasqret/peano-lab-lean/commit/ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2)
passed pinned Lean 4.31/WMI job
[`218358`](https://github.com/nasqret/peano-lab-lean/tree/8515336ab3b89ca6f0c8ab521d01745a220b5211/artifacts/wmi/218358).

1. Centralize the eleven P0 builders without changing any theorem statement.
2. Complete parity (`Even`, `Odd`, dichotomy, exclusivity, arithmetic and
   modulo-two bridges).
3. Add the round-tripping `Prime` authoring surface with capture tests.
4. Generate fixed-residue classifications only as clients of generic
   division/remainder and congruence results.
5. Publish the first API matrix and duplicate-builder report before adding new
   campaign-specific definitions.

This order makes the next expansion conservative in both senses: no increase
in logical strength, and no loss of the exact explicit corpus that already
serves as the regression oracle.
