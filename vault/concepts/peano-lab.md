---
title: Peano Lab
tags: [tool, peano-arithmetic, browser, soundness]
---

**Peano Lab** is a small theorem prover for first-order Peano arithmetic. It runs Python inside a
self-hosted Pyodide Web Worker and presents proofs through a terminal-like browser UI.

Its governing separation is simple: tactics may construct a [[proof-certificate]], but only the
[[trusted-kernel]] may claim QED. The checker receives the session owner's original formula rather
than trusting a goal returned by the tactic engine.

The public learning path is the [[theorem-ladder]]. The lab is intuitionistic by default; use of
double-negation elimination is explicit and checked only in the labeled classical mode.
The current native library exposes 170 closed checked theorems, including
constructive [[binary_crt]] and the conditional two-position constructor
[[binary_crt_beta_pair]].

The static delivery boundary is recorded separately as [[browser-proof-runtime]]: compressed and
versioned bytes may arrive concurrently, but they add no proof authority and do not alter the
certificate checked at QED.

The current undo branch can be inspected or downloaded as a [[replayable-proof-script]]. Active
text remains explicitly unchecked; a final `qed` appears only in the retained artifact produced
after the independent checker succeeds.

The [[multiline-proof-paste]] browser surface accepts a bounded complete replay through an
accessible dialog or direct terminal paste. Lines still pass sequentially through the same session
owner, and the final QED retains exactly the same kernel boundary.

Intermediate propositions can be organized with [[local-reasoning-cut|local reasoning cuts]]:
`have` proves the named fact first, while `suffices` proves first that the fact would finish the old
goal. Both schedules are compiled away before kernel checking.

Checked library dependencies use the distinct [[self-contained-proof-sharing]] rule. Its complete
lemma and body branches are embedded in the certificate and checked directly; theorem names and
hashes never become proof authority. This enlarges the trusted checker without changing Peano Lab's
first-order arithmetic language or its default intuitionistic logic.

The PA-specific `compact_arith` tactic searches for a [[compact-arithmetic-certificate]] for one
rigid equality. It may use only an explicit ordered list of named equalities, while the learner must
still choose any surrounding invariant, induction, and existential witness.

For corpus generation and model evaluation, the [[compact-headless-proof-runner]] reuses this same
proof surface and kernel boundary without starting the browser runtime.

## Related

[[peano-lab-moc|Peano Lab MOC]] · [[natural-deduction]] · [[tactic-mode]] ·
[[checked-numerical-normalization]] · [[browser-proof-runtime]] · [[substitution]]
· [[replayable-proof-script]] · [[multiline-proof-paste]] · [[local-reasoning-cut]] ·
[[self-contained-proof-sharing]] · [[compact-arithmetic-certificate]] ·
[[compact-headless-proof-runner]] ·
[[kernel-guided-policy-training]]
