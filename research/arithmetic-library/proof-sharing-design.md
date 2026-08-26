# Self-contained proof-sharing design

## Decision

Peano Lab admits one trusted certificate constructor:

```text
Cut(A, B, lemma, body)
```

with judgment

$$
\frac{\Gamma\vdash\mathit{lemma}:A\qquad
      A,\Gamma\vdash\mathit{body}:B}
     {\Gamma\vdash\operatorname{Cut}(A,B,\mathit{lemma},\mathit{body}):B}.
$$

The checker validates `lemma : A` once in the ambient context and validates
`body : B` with `A` inserted at hypothesis index zero. It uses the same
classical-mode flag for both branches. `A` and `B` are validated formula
annotations; neither is accepted merely because the caller supplied it.

This is a deliberate enlargement of the trusted proof grammar and checker.
It is not described as “kernel unchanged.” The object language and logic are
unchanged: no term former, predicate, axiom, induction principle, or classical
rule has been added.

## Authority boundary

A Cut is self-contained. It stores the proposition, conclusion, lemma proof,
and body proof. It stores no theorem name, content hash, catalog key,
declaration identifier, callback, or external proof-table reference. Library
lookup and artifact hashing remain untrusted preprocessing and provenance.

The conclusion annotation is required by the bidirectional checker. Without
it, a body beginning with `ImpIntro`, `ForallIntro`, or another checking-only
form need not synthesize a conclusion. The checker still compares the body
against the annotation, so the annotation grants no authority.

The node is lexical sharing, not a general content-addressed DAG. Hypothesis
uses in `body` share the one checked `lemma` branch. Two distinct Cuts still
store and count two branch occurrences.

## Integration contract

- Library replay proves a dependency-curried body, removes the generated
  dependency introductions, and wraps the body in nested Cuts containing the
  already checked dependency certificates.
- Live `use` resolves a name outside the kernel, rechecks the selected closed
  formula/certificate pair, and places it in a Cut around the focused goal.
- QED checks the final self-contained certificate against the owner-retained
  original target and exact logic mode.
- Term substitution transforms both Cut annotations and both proof children.
- Proof-hypothesis shifting and opening increase their cutoff only for
  `body`, because only that branch extends the proof context.
- Term binders in `ForallIntro` and `ExistsElim`, and proof binders in
  implication, disjunction, existential elimination, and nested Cuts, remain
  capture-safe.
- Structural node/depth metrics traverse both branches.

Engine-only `LocalHave` and `LocalSuffices` are unchanged. They express the
two pedagogical schedules for a new local claim and still compile away by
untrusted capture-avoiding substitution. They are never accepted by the
kernel and are not aliases for Cut.

The existing normalization pass now means administrative normalization: it
eliminates `LocalHave`/`LocalSuffices` and contracts exposed implication and
universal beta redexes, while preserving trusted Cuts.

## Conservativity and erasure

The mathematical erasure equation is

```text
Cut(A, B, lemma, body)
  ↦ ImpElim(ImpIntro(body), lemma)
```

The untrusted `erase_trusted_cuts` utility applies this expansion recursively
and deliberately does not normalize the created redex. It rejects partial
certificates containing holes. It is a compatibility and audit tool, not an
acceptance path and not a source of proof authority.

Operational erasure is incomplete for two independent reasons:

1. The bidirectional checker cannot synthesize every introduction-shaped
   `lemma` when the erased term places it in implication-argument position.
2. The capture-sensitive reducer can normalize many erased terms, but its
   limitations around large induction-bearing dependency substitutions were
   part of the motivation for Cut.

Therefore the project makes no claim that every accepted Cut certificate is
currently converted by these untrusted utilities into an accepted expanded
tree. Whenever an erased or normalized artifact is used for comparison, it
must pass a fresh kernel check. The checked Cut certificate remains the
authoritative artifact.

## Required audit surface

The trusted audit covers:

- exact constructor matching and rejection of subclasses;
- validation and independent mutation of `A`, `B`, `lemma`, and `body`;
- ambient versus body-only hypothesis scope;
- identical intuitionistic/classical authority in both branches;
- malformed terms, formulas, proof nodes, and hostile recursion depth;
- nested Cut and capture tests under all proof and term binders;
- direct checking of replayed library entries from the empty context;
- deterministic structural metrics and representation-version changes.

The untrusted audit separately covers live `use`, dependency packaging,
rendering, substitution traversal, administrative normalization, erasure,
resource limits, and failure transactions. Passing those tests is important
for reliability, but only the trusted checker determines soundness.

## Arithmetic consequence

This design removes proof duplication and reducer correctness as the immediate
composition gate for bounded gcd existence. It does not prove that theorem by
itself. The arithmetic script, its dependencies, and its final closed Cut
certificate must still replay and check. The same distinction applies later
to Bézout, Euclid's lemma, Gödel-β products, and FTA.

Related documentation:

- [binding Peano Lab design](../../docs/PEANO_LAB_DESIGN.md);
- [book chapter on proof sharing](../../book/arithmetic-library/proof-sharing.md);
- [gcd/Bézout roadmap](gcd-bezout-roadmap.md).
