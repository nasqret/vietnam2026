---
title: Multiline proof paste
tags: [peano-lab, browser, tactics, replay, accessibility]
---

**Multiline proof paste** is the M17 browser convenience for feeding a complete
[[replayable-proof-script]] to [[peano-lab]]. An accessible dialog and direct multiline terminal
paste share one bounded path. Ignoring blank lines, the first line begins exactly `pa prove ` and
the last line is exactly `qed`; limits apply to total characters, nonblank lines, and each line.

After whole-input preflight, commands run sequentially through the existing proof-session owner.
The first failed command stops the remaining suffix, but successful prefix commands remain and keep
ordinary per-command undo. Paste is therefore neither one giant [[tactic-mode|tactic]] transaction
nor an alternate session authority.

Preflight rejects `script` commands and batch replay has no authority to initiate a browser
download. Its final `qed` still asks the unchanged [[trusted-kernel]] to check a reconstructed
[[proof-certificate]] against the owner-retained original theorem. The surface is input ergonomics,
not evidence or [[theorem-ladder|library admission]]. It is locally verified in build
`2026-07-28b`; no deployment is implied.

## Related

[[peano-lab-moc|Peano Lab MOC]] · [[peano-lab]] · [[replayable-proof-script]] ·
[[browser-proof-runtime]] · [[tactic-mode]] · [[trusted-kernel]]
