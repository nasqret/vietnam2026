P0/P1 completed with unchanged proof coverage: six of seven positive diagnostics,
and the false control remained unknown. Both versions used zero model/Vampire calls.

| Case | v6 occurrences | v7 occurrences | v6 / v7 server seconds |
|---|---:|---:|---:|
| dev_compact_offset_swap | 5024 | 54 | 1.381 / 0.792 |
| dev_compact_offset_swap_renamed_reverse | 5024 | 54 | 1.405 / 0.715 |
| dev_parameterized_even_product | 40344 | 40344 | 6.748 / 6.678 |
| dev_local_quantified_implication | 9 | 9 | 0.675 / 0.675 |
| dev_successor_zero_contradiction | unknown | unknown | 2.520 / 2.540 |
| dev_binomial_square | 14862 | 14862 | 1.953 / 1.935 |
| dev_cubic_mod_6 | 58884 | 58884 | 13.714 / 14.251 |
| dev_negative_cubic_mod_4 | unknown | unknown | 6.295 / 6.199 |

The offset recurrence uses `compact_arith` in the changed search: 5,024 → 54
structural occurrences (98.9% fewer). Its final certificate also has 54 distinct
objects. The baseline did not measure distinct objects; these are not invented.

Algebra plans receive advisory cost scores; both existing variants remain available.
A native integration regression confirms a cheaper failed plan falls back at the
original checked prefix. Failure of the first test exposed a scheduler return issue;
the fix and passing rerun are recorded in `targeted-gates.json`.

The exact source archives, requests, final HTTP jobs, timings and actual terminal
receipts are beside this report. Both evaluations verified stable source pins.
Each version ran once. These are exposed diagnostics, not unseen accuracy estimates.
The 12+4 evaluation reservation remains prospective pending enforced exclusions.
The original kernel, saved model and old model-only provider remain unchanged.
