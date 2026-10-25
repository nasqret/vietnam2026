# Local historical baseline runner

`local_baseline_check.py` evaluates the preserved deployed adapter without changing its implementation or selecting a new website default. It loads the existing `LazyModelPolicy` once, then creates a fresh old wrapper and `_MLXCandidatePolicy` per selected case, sharing only the loaded model/tokenizer/MLX environment. The original beam width 4, output limit 64 and prompt limit 1,536 remain unchanged.

It uses the same frozen 32-case panel and native search limits as `local_candidate_check.py`. Choose the same explicit case IDs in the same order for both runs. Both runners require proof search and independent original-target replay to finish within 30 seconds; a 45-second signal ceiling aborts the remaining batch if a worker cannot return promptly. Model loading has a separate 120-second ceiling. The final source/artifact custody check has a separate 60-second ceiling and does not perform model or proof work. A case's provisional proof observation is admissible only with its completed run receipt.

The two runners share stdlib-only validation, source-exception, timing and replay helpers from the explicitly pinned `local_candidate_check.py`. Importing that helper does not invoke its candidate loader or `main`. The baseline CLI requires `--helper-sha256` in addition to the study and panel pins. All native/model admission checks remain those of the existing runtime.

Example invocation after the parent chooses the actual cases and pins:

```sh
hydra-playground/.runtime/venv/bin/python3 -I -B \
  output/hydra-model-upgrade-2026-10-20/runtime-assessment/proposed-provider/local_baseline_check.py \
  --study path/to/study.json --study-sha256 ACTUAL_STUDY_SHA256 \
  --inputs path/to/inputs.json --inputs-sha256 ACTUAL_INPUTS_SHA256 \
  --helper-sha256 ACTUAL_LOCAL_CANDIDATE_CHECK_SHA256 \
  --case-id ACTUAL_FROZEN_CASE_ID \
  --output path/to/new-baseline-output
```

The receipt schema is `hydra-local-upgrade-arm-v1`, with arm `historical_local_mlx`. Each case saves its theorem, native search result, genuine replay result, proof observation, elapsed time and actual provider counters. Baseline `generated_token_steps` is retained as reported by the old beam decoder; `generated_token_slots` is explicitly null because that decoder does not expose actual beam-slot accounting. It must not be compared to the candidate's real token decisions as if it counted the same thing.

The old provider's explicit 1,536-token prompt refusal is a baseline coverage limit and remains in the diagnostics. Other model-provider infrastructure errors fail the run instead of becoming negative quality scores. There are no automatic retries, hidden fallback models, simultaneous model loads, downloads, training or live source edits. No model or runner execution was performed while preparing this file; only Python syntax was parsed.
