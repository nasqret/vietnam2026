# October measured-results fragment

`october-results.draft.html` is an additive draft, not a live edit. Insert its finalized section immediately before the existing unique `<section id="study-results" ...>` in `hydra-playground/index.html`. Keep that entire September section, its `study-evidence-json` content, all 14 gallery records, CSS and JavaScript unchanged. The new section uses only existing study/badge/quiet-note classes and distinct `october-*` IDs. No script or framework is added.

All pending values are visible text, not guessed scores. After the completed paired verification arrives, populate the `data-october-field` spans and the matching JSON snapshot together. Remove `study-pending` only from finalized cells. Primary and regression denominator counts deliberately remain pending until the actual verifier supplies them.

| Draft field | Source in completed v3 verification/evidence |
|---|---|
| `primary_positive_total` | `primary_positive.total` |
| `regression_positive_total` | `regression_positive.total` |
| `false_control_total` | `primary_false.total + regression_false.total` |
| `historical_primary_proved` | primary `both_proved + historical_only` |
| `newest_primary_proved` | primary `both_proved + wmi_only` |
| `historical_regression_proved` | regression `both_proved + historical_only` |
| `newest_regression_proved` | regression `both_proved + wmi_only` |
| `historical_false_accepted` | count false-labelled paired cases with `historical.proved` |
| `newest_false_accepted` | count false-labelled paired cases with `wmi.proved` |
| arm model calls | sum that arm's `paired_cases[*].historical/wmi.actual_model_calls` |
| execution text | matching completed supervisor, all 18 cases, final custody |
| comparison status/conclusion | actual verification status; no promotion claim from partial cases |
| JSON `verification_sha256` | hash of the genuine completed verifier output |
| JSON promotion/HTTP/deployment fields | separate actual promotion and HTTP receipts; never infer from model-quality eligibility |

The already populated historical zeros/266 calls come from `evaluation/CACHED_HISTORICAL_TERMINAL_AUDIT_01.json`. The 3.216× result comes from its `first17_same_work`; do not describe all 18 cases as identical work or present the raw tokenizer microcheck as a full-inference speedup. Both source and adapter identities remain separate from September evidence.

At finalization, change the JSON schema from draft to a final results version, replace the pending badge and conclusion with the verified outcome, and preserve the selected/exposed-panel caveat. No default-model or method edit belongs to this fragment. Root owns insertion/defaults and served-page verification after the promotion gate.

No tests, inference, browser requests, publication or live app edits were performed to prepare this draft.
