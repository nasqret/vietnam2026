---
name: constructive-proof-explorer
description: Build or update constructive number-theory campaign websites and interactive proof explorers using the established Quadratic Reciprocity design, exact theorem evidence, conservative definition DAGs, and the existing Peano proof-library infrastructure.
---

# Constructive Proof Explorer

Use this skill whenever a new theorem campaign, proof family, proof-library
branch, definition-aware graph, or campaign landing page is added to the Peano
constructive number-theory project. Preserve the user's established Quadratic
Reciprocity experience; a different visual framework is not an equivalent
implementation.

Read [references/quadratic-reciprocity-model.md](references/quadratic-reciprocity-model.md)
before building or substantially changing a proof family. It records the actual
reference files, reusable renderer, required page topology, graph semantics,
definition hygiene, evidence boundaries, and regression checks.

Follow these invariants:

1. Render every public family entrance with the shared canonical Quadratic
   Reciprocity-style renderer and the existing `proofs.css`; reuse the original
   exact and definition-aware explorer assets byte for byte.
2. Provide exact and definition-aware theorem directories, an interactive mixed
   DAG, individual theorem and definition pages, stable tags, and bidirectional
   links to the global campaign atlas.
3. Separate proof-dependency arrows, theorem-uses-definition arrows, and
   definition-dependency arrows. Named definitions must be hygienic,
   conservative first-order abbreviations with exact AST-equivalence checks.
4. Distinguish Stable membership, current Alpha checked-use authority, first
   Alpha admission, original-kernel proof evidence, independent Lean
   verification, and any broader milestone that remains open.
5. Extend generators and executable regression tests before regenerating their
   deterministic snapshots. Preserve immutable historical release artifacts and
   unrelated user edits; use bounded proof replay when mathematical verification
   is needed.

Stage, publish, deploy, commit, or push only when the user's current request
authorizes that action. For a design-only request, verify the local generated
surfaces without changing a live service.
