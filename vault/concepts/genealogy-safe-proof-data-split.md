---
title: Genealogy-safe proof-data split
tags: [peano-lab, llm, dataset, leakage, evaluation]
---

# Genealogy-safe proof-data split

A **genealogy-safe proof-data split** assigns related proof sessions before expanding them into
state-to-tactic rows. Splitting individual transitions would place nearly identical states from one
proof in both training and evaluation; splitting only by literal theorem text would still leak
renamings and generated variants.

Peano Lab's replay compiler requires each positive session to carry a `family` and `lineage`. It
builds connected components among family, lineage, exact canonical-formula, and exact rendered
policy-prompt nodes: if two sessions share any one, transitive closure keeps the whole component
together. The formula edge is an independent guard against accidentally or dishonestly unrelated
metadata for the same theorem. The prompt edge prevents different theorems that reach the same
model input from appearing on opposite sides of the split. Components are ranked by a stable
SHA-256 function of the split seed and component members, then assigned to train, validation, or
test. The manifest records each split's components, session and row counts, and content hash.

Only `qed: true` sessions enter positive cross-entropy data, and every such session is first replayed
through the current [[compact-headless-proof-runner]]. Before/after goals, focus, tactic text,
environment identity, original theorem, and proof size must match the source trace, ending in a new
independently checked QED. Failed actions remain candidates for later ranking data, not positive
next-tactic targets.

The exact-formula edge cannot discover non-identical relatives. New descendants, paraphrases,
renamings, and alternative proofs must still inherit a connected family or lineage identifier
before splitting; a hash cannot recover semantic genealogy that was never recorded. An independent
pre-training attestor rejects any canonical formula or exact policy prompt crossing splits and
byte-rebuilds every split from the raw sessions under the current compiler.

Model-v3 adds a second, later boundary: **curriculum selection also preserves whole sessions**.
Every catalog-prefix transition is retained, while synthetic sessions are ranked independently of
input order and admitted only in complete schema-anchoring and root-head-balanced rounds. A row
ceiling may leave unused capacity; it never cuts a proof trajectory. The selection attestation
binds the full candidate population and chosen rows, and the trainer rejects a subsequent row-level
sample cap. Genealogy splitting answers “which release split owns this proof family?”; whole-session
selection answers “which complete training proofs from the already validated train population are
optimized?” Neither can substitute for the other.

## Related

[[kernel-guided-policy-training]] · [[proof-trace-corpus]] ·
[[verifier-guided-policy-evaluation-and-search]] · [[kernel-judged-evaluation]] ·
[[peano-lab-moc|Peano Lab MOC]]
