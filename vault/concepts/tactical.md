---
title: Tactical
tags: [peano-lab, tactics, language]
---

# Tactical

A **tactical** combines tactics into a small program. Peano Lab includes sequencing (`;`),
backtracking choice (`<|>`), `repeat`, `first`, `all_goals`, and one-based `focus`.

Their meaning is inseparable from state discipline. A tactic either returns a complete new proof
state or raises a final `TacticError` without changing the old one. Therefore the failed branch of
`<|>` can be discarded exactly, `repeat` can stop cleanly, and a compound tactical becomes one undo
transaction. This is the point at which a menu of proof commands becomes a little language.

Tacticals remain untrusted: they arrange certificate-producing transformations, but only the
[[trusted-kernel]] can accept the resulting [[proof-certificate]].

## Related

- [[tactic-mode]]
- [[proof-certificate]]
- [[peano-lab]]
