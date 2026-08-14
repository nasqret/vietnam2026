---
title: Peano authoring assistant
tags: [peano-lab, authoring, documentation, provenance]
---

# Peano authoring assistant

The **Peano authoring assistant** is a revisioned proposal workspace for the
living [[peano-hydra]] library. It retains verbatim prose units, proposes one
or more readings in the sole Peano Lab language, shows binders, assumptions,
readable notation and primitive expansions, and requires explicit author
acceptance before proof search.

Meaning, derivation, and publication use separate authorities. A human accepts
the intended statement; the [[trusted-kernel]] accepts a certificate against
that exact statement; a human reviewer admits the complete artifact. A model
or solver may do none of these by setting a field.

Every asynchronous response binds the document revision, unit, logic profile,
[[library-epoch]], and proof state it observed. A mismatch is stale evidence,
not permission to rebase. Training consent defaults to deny. Only explicit
export may create a reviewable patch; browser workers and prompt text cannot
mutate the public catalog or Git tree.

The first A0 protocol slice is canonical authoring schema v1, digest
`31a344bbc0b22cfacf5803c85d25a80a0234cf7387395283c5e1ab25ada80553`.
It pins the existing defined-syntax registry, permits generic diagnostics only
from explicitly untrusted solver/model authorities, requires real kernel
objects for checked proposals, and validates ordered actor/session-owned event
roots. Its production review/export registries are empty. The 28 focused tests
establish this public data/API boundary; arbitrary private same-process Python
execution is outside it, and the live service/gold corpus remain future work.

## Related

[[peano-logic-profiles]] · [[vampire-reconstruction]] ·
[[replayable-proof-script]] · [[arithmetic-library-moc]]
