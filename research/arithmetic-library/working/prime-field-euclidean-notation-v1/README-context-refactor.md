# Context-refactor source-check addendum

This addendum records the current source-only checks after the root-owned Bézout constructor was changed to keep only small coefficient bounds in its local proof context. Its statements, ordered dependencies, summaries, definition clauses and the other two rows are unchanged. The previous stage94 CPU-limit failure remains a failed attempt; it produced no stage94 artifact.

The current mathematical source is 18,747 bytes, SHA256 `c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702`. The three script lengths are 354, 299 and 76. The 95-row map retains 436 proof prerequisites, 404 reviewed definitions and 879 definition-expansion arrows; its script-command count is now 10,062. Its final stage-ordered specification SHA256 is `b2b381d67064401d3325b464396c6d156b5fc27a56639f3909dacaa60ae83994`.

Exactly the existing checks were rerun under the unchanged CPU 170/175 s, wall 180 s and RSS 1,536 MiB bounds:

- 329 independent contract/native-beta-model cases passed, 987 phases, 2.881109417 s and 62,324,736 bytes peak RSS.
- 257 conservative-notation cases passed, 771 phases, 31.094230709 s and 125,583,360 bytes peak RSS.

These are 586 distinct existing cases under the current binding, not 586 new tests. Each suite has one parameterized case ID changed solely by the new source/specification literal. Normalizing that metadata recovers the exact earlier ordered ID hashes. A separate collection-only reconciliation adds no test or proof credit.

The three owned Python files changed only in their expected source/specification digests, source byte count, and command counts. Exact old Python bytes are preserved in [pre-context-refactor-source-snapshot-v1.json](pre-context-refactor-source-snapshot-v1.json); the old mathematical source is preserved as inert UTF-8 in [context-refactor-observations-v1.json](context-refactor-observations-v1.json). That observation also records the exact commands, captured reports, resource measurements and final pins. [context-refactor-reconciliation-v1.json](context-refactor-reconciliation-v1.json) independently checks the literal-only deltas and the stored evidence.

All 48 source pins, the old 25/37/44/52 complete archives and all 536 runtime Python files were unchanged during the notation run. The older [README](README.md), model/notation observations and focused-proof ledgers retain their historical bindings; none was rewritten or used as acceptance authority.

No HA/Lean checks, Alpha import, admission, publication, new definition or new mathematical claim occurred in these reruns. Complete-cone export and its fresh original proof gates remain the separate controller's responsibility; G091 and general gcd construction are not claimed complete.
