---
title: Replayable proof script
tags: [peano-lab, tactics, artifact, soundness]
---

A **replayable proof script** is an inert UTF-8 surface program exported by [[peano-lab]]. It begins
with a canonical `pa prove` command and records only the successful transactions on the current
undo branch. Failures and inspection commands remain useful elsewhere, especially in the
[[proof-trace-corpus]], but are not part of this replay.

An active script is explicitly unchecked and omits `qed`, even when every goal is closed. Only a
successful check by the [[trusted-kernel]] produces a retained `CHECKED QED` artifact with a final
`qed`. The separate owner journal is needed because [[tactic-mode]] authority is not stored in proof
history, tacticals collapse internal steps, theorem imports need their lookup names, and top-level
automation exposes individually undoable primitives.

The file is not a [[proof-certificate]] and does not enter the [[theorem-ladder]]. Replaying it asks
the tactic layer to reconstruct a candidate certificate; QED must check the original theorem again.
Library admission remains a source-reviewed declaration with a closed statement, earlier
dependencies, compatible script, tests, commit, and deployment.

## Related

[[peano-lab]] · [[proof-certificate]] · [[theorem-ladder]] · [[trusted-kernel]] ·
[[tactic-mode]] · [[checked-theorem-reuse]]
