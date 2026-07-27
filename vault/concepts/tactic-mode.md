---
title: Term mode vs tactic mode
tags: [l4]
---

A proof term and a tactic script build the *same* kernel object. Starter tactics: `rfl exact intro apply rw simp induction rcases omega decide`.

Peano Lab's [[local-reasoning-cut]] makes this distinction visible: `have` and `suffices` schedule
open goals with engine-only nodes, but those nodes are compiled away before the kernel checks the
ordinary proof term.

See also: [[lean]], [[peano-lab]], [[proof-certificate]].
