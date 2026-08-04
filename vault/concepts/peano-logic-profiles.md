---
title: Peano logic profiles
tags: [peano-lab, intuitionistic-logic, classical-logic, profiles]
---

# Peano logic profiles

Peano Lab has one object language. The active frozen Hydra profile is the
default [[heyting-arithmetic]] profile: intuitionistic logic, PA1–PA6, and
formula induction. A future separately registered classical profile will use
the existing double-negation-elimination rule and will be labeled `PA+DNE` in
statements, dependencies, prompts, documents, and certificates. That Hydra
profile and its import enforcement are not implemented yet.

Excluded middle, $A \lor \neg A$, may be derived and exposed as a classical
theorem or tactic; it is not a second primitive rule. The target policy permits
constructive results in a classical session and rejects DNE-dependent
artifacts from a constructive [[library-epoch]]. Defined notation must carry a
deterministic conservative expansion into the primitive [[peano-lab]] grammar.

## Related

[[intuitionistic-logic]] · [[trusted-kernel]] · [[peano-hydra]] ·
[[peano-authoring-assistant]]
