# Hydra local model integration — 21 October 2026

**The website now defaults to WMI C6 long vanilla11, step 16,384, with Model + symbolic search.** Both local comparison arms completed, the promotion gate passed, production was restarted, and real HTTP checks exercised both a model-generated proof and a separate symbolic fallback. The gallery now contains 15 proofs, preserving all 14 historical records. [Promotion decision](PROMOTION_DECISION.json), [final live verification](FINAL_SERVER_VERIFICATION.json).

**The measured improvement is 4/12 positive proofs versus 0/12 for the old adapter on this small selected panel.** This supports replacing the adapter for this workflow; it does not establish a broadly “much better” theorem prover. Neither model proved any of the four regression positives, and the selected/exposed cases do not establish held-out accuracy.

| Completed paired comparison | Historical adapter | New WMI adapter |
|---|---:|---:|
| Primary positives proved | 0 / 8 | **4 / 8** |
| Regression positives proved | 0 / 4 | 0 / 4 |
| Total positive proofs | 0 / 12 | **4 / 12** |
| False controls accepted | 0 / 6 | 0 / 6 |
| Cases completed with final custody | 18 / 18 | 18 / 18 |
| Actual model calls / decision tokens | 266 / 851 | 369 / 2,121 |
| Whole-arm time, including load/custody | 850.298 s | 1,495.766 s |

The four gains were `primary-05`, `primary-07`, `primary-08`, and `primary-12`. They comprise **3/4 newly authored composition positives and 1/4 checkpoint-development positives**, with no historical-only primary or regression success. Every credited proof passed an independent original-theorem native replay. The pinned verifier passed (`0/e5796b`); its report SHA-256 is `408c8a9f0ee89710fa9390dba5796bb0af0bf2ff83883dd44deb3d6a3e4b65e7`. [Paired verification](evaluation/CACHED_LENGTH_V3_VERIFICATION_01.json), [independent terminal/source audit](evaluation/CACHED_LENGTH_V3_TERMINAL_AUDIT_01.json).

The frozen comparison is [v3 spec `aba7b837…`](evaluation/EXECUTION_SPEC_CACHED_LENGTH_V3.json): the same 12 primary and six regression inputs for both adapters, one loaded model at a time, greedy width one, at most 128 tactics/model calls, 128 generated tokens per tactic, 16,384 total decision tokens, 6,144 context tokens, 30 seconds per tactic, and 300 seconds per case. Both arms used the cached tokenizer length and unchanged full-prefix numerical backend, without heuristic proof steps, Vampire, theorem imports, or automatic retry. Loading was measured separately; both arms passed their external supervision and final custody checks. This is a small exposed development comparison, not a held-out benchmark or statistical-significance result. Training overlap for the newly authored templates has not been measured.

The interrupted preceding uncached newest run is preserved as [incomplete diagnostic evidence](evaluation/newest-01/supervisor.json): four completed cases, interrupted during the fifth, exit −9. It cannot substitute for a completed v3 arm. The uncached historical run is used only for the performance comparison below, not as the v3 quality baseline.

## What changed, and what the model actually is

The promoted adapter is **`wmi-c6-long-vanilla11`**, checkpoint step **16,384**, a rank-32 LoRA adapter with alpha 64, dropout zero, and one ordinary transformer pass. It uses the same **Qwen3-1.7B Base**, not a larger base model and not a recurrent inference configuration. The local preview uses the authenticated four-bit base under the existing 6 GiB MLX limit; numerical equivalence to the original remote training precision is not claimed. The old adapter remains available explicitly, and the legacy Hybrid/original Model routes retain their historical decoder and model identity.

| Identity | Exact SHA-256 |
|---|---|
| Selected training checkpoint | `177501bf7b662a210b6cf6887844a282365437c781e53138ad5495f02c620a06` |
| Exported adapter tensors | `659f71892bacdafc7488d8b683dd8dda051dfa4b054f74ba340db4da59fd07a3` |
| Preserved historical adapter | `7b86fc09aafa5bbb7b443119384e6b83f1f5a5f51a44340c0ca8b2e7a3b4d7c5` |

The selected checkpoint's recorded source development result is **60/64**. That evaluation was exposed during checkpoint selection; it is neither a fresh local score nor evidence of unseen-theorem accuracy. The training run stopped at its budget limit after 20,352 of 24,576 planned updates; the selected artifact is the locked, evaluated step-16,384 checkpoint. No new training was performed for this local integration. [Selection](newest-wmi/selection.json), [training receipt](newest-wmi/receipt.json), [actual CPU export receipt](newest-wmi/export-receipt.json), [provider manifest](newest-wmi/PROVIDER_MANIFEST.json).

## Measured performance correction

For the first **17 historical-adapter cases with exactly matching work**, total case time fell from **1,731.301 seconds to 538.308 seconds: 3.216× faster**, saving 1,192.994 seconds. Both runs made the same 149 model calls and emitted the same 500 decision tokens, with the same prompts, literal actions, statuses, native transitions, and forward counts. Only elapsed-time fields and their derived receipt hashes differ. This is one serial run per condition, not a controlled statistical benchmark. [Same-work terminal audit](evaluation/CACHED_HISTORICAL_TERMINAL_AUDIT_01.json).

The eighteenth case reached its 300-second deadline in both conditions and is deliberately excluded from that ratio: the faster version performed 117 calls/351 tokens instead of 33 calls/99 tokens. All 18 cached historical cases together took 850.298 seconds including loading/finalization, made 266 calls and emitted 851 tokens, and proved none. All tokenizer boundary checks passed; their separately recorded total overhead was 2.469 seconds.

The cause was repeated CPU vocabulary counting: the installed tokenizer's full-length query cost about **13 ms**, and validation called it once per prompt token. The fix captures the authenticated tokenizer's immutable length once. Encoding, decoding, vocabulary contents, special tokens, EOS, authority masks, model parameters, and the numerical decoder are unchanged. Both actual tokenizers passed CPU parity and mutation-detection checks. This is **not KV caching** and does not change proof authority. [CPU parity](performance-v2/TOKENIZER_CPU_TEST.stdout.json), [microcheck](performance-v2/TOKENIZER_MICROCHECK.json), [independent source/custody review](performance-v2/INDEPENDENT_TOKENIZER_REVIEW.md).

## Proof-state compatibility

All **50 saved successes** from the earlier C6 vanilla47 step-8,192 WMI development evaluation replay through Hydra's unchanged native checker without imports. All **3,753 tactic steps and intermediate states** match. These are saved-proof compatibility results from the earlier adapter, not 50 newly generated proofs from the selected long11 adapter. The original evaluation was 50/64; validating only its successes is not 100% solving accuracy. [Native bridge report](../hydra-wmi-bridge-2026-10-21/RESULTS.md).

The practical bridge preserves the exact trained compact prompt, every ordered open goal, persistent printed variable/metavariable names, and the complete tactic prefix. The model owns the sequential proof from its original goal, with room for up to 128 actions; heuristic introductions no longer preempt that lane. The saved WMI proofs often require 35–127 actions, so the earlier 16-call hybrid budget did not reproduce their protocol. Expanded sequential admission supports their larger formulas while retaining the same no-import checker and independent original-theorem replay. The separate model-then-symbolic portfolio never joins incomplete proof scripts; each winning proof must be checked in full.

The web lane additionally stops when the complete ordered printed goal state repeats, allowing the portfolio to move on without spending more model calls on that loop. This is a bounded search heuristic, never a disproof. An offline audit found no repeated state or prompt in **any of the four completed winning trajectories**, so it would not remove those recorded successes. The guard was not used in the sealed paired comparison. Eight focused guard checks passed (`0/15adea`) and 16 portfolio checks passed (`0/323902`); these are engineering checks, not additional model-quality cases. [Completed-proof/source audit](evaluation/CACHED_LENGTH_V3_TERMINAL_AUDIT_01.json).

Limitations remain concrete: the WMI arm ended with four proofs, eleven tactic errors and three deadline stops. In `primary-11`, 39 native actions were accepted, but decode 40 exhausted the separate **30-second per-tactic limit** at 31.927 seconds, emitting 15 partial tokens without EOS. The whole case ended at 221.502 seconds, before its 300-second case ceiling. The partial action was not accepted or credited as a proof. Raising only the whole-case limit would not remove that particular cap, and no longer-limit success is claimed. KV acceleration remains an unactivated proposal. [Deadline diagnosis](evaluation/CACHED_LENGTH_V3_TERMINAL_AUDIT_01.json).

## Actual HTTP behavior and gallery publication

The model branch passed a genuine HTTP integration request (`0/0e839e`, job `30ec5320ef84447c8cd10e9f00b54a9f`) for two implication chains converging on a shared conclusion. The selected new adapter generated **all 19 winning tactics**, using **19 model calls, 95 decision tokens/forwards**, and a **25-node native certificate**. Server portfolio supervision took **43.344 seconds**; the sequential model phase won, so no symbolic fallback or Vampire call was needed. Independent replay and cleanup passed. This was an exposed integration example, not another held-out benchmark. [HTTP summary](http-model-proof-01/SUMMARY.json), [independent HTTP audit](HTTP_MODEL_PROOF_AUDIT_01.json).

The publisher then performed a separate CPU native replay and appended **“Two implication chains converge: 19 model-generated steps”**, labelled MODEL, to the gallery (`0/146765`). It preserved the 14 historical proof files and backed up their manifest; there are now **15 gallery entries**. Publication did not run the model again. [Publication receipt](publication-newest-01/published-01/SUMMARY.json), [publication replay](publication-newest-01/published-01/PUBLICATION_REPLAY.json).

Production was initially restarted on local port **8767** (launch `0c7a63`, session `53404`). Its recorded readiness response confirmed the newest model and portfolio defaults, original legacy model identity, and 15 gallery entries. [Production readiness](PRODUCTION_PROMOTED_READY.json).

A second genuine HTTP request on production proved that fallback works (`0/e3e2d6`, job `54486b1fc91d44dab2c2dab054af7c19`). The model made **4 calls and emitted 21 tokens**, accepted three partial steps, then produced a rejected tactic. A **fresh Symbolic search from the original theorem** completed the proof with **10 heuristic steps and 1,473 certificate nodes**. Total server time was **13.418 seconds**: 12.454 seconds for the model phase and 0.962 seconds for Symbolic. There were zero Vampire calls. **The winning proof is credited entirely to Symbolic/native heuristics, not to the model.** The incomplete model script was not combined with it; both phases exited cleanly and no computation remained active. [Production fallback summary](http-production-fallback-01/SUMMARY.json).

An independent audit found a reporting inconsistency in that fallback receipt: nested `search.model_used` inherited `false` from the Symbolic winner, despite the correctly aggregated four model calls. The top-level `model_used: true` and the ten heuristic winning steps were already correct. The original HTTP receipt is preserved. A metadata-only correction now reports aggregate model use separately from winner-local diagnostics; 16 CPU tests passed (`0/8a50f2`), followed by an independent source review. This changed reporting, not the accepted proof or its attribution. **The model was not rerun after this correction.**

The corrected server was gracefully restarted (`50d276` / `b33bdf`, session `38906`, PID `59554`). Final read-only live verification passed (`0/973927`): port 8767 serves the newest/portfolio defaults, matching HTML and JavaScript bytes, the deployed October evidence, and all 15 valid gallery entries, including the 19-step MODEL record. The server was idle and the temporary test server on port 8768 was closed. These final checks performed no new model or native proof execution. [Final server verification](FINAL_SERVER_VERIFICATION.json).

## Historical evidence stays separate

The September campaign is archived separately from this October WMI integration. Its final source07 4B arm completed 16 cases: **1/12 positive proofs**, eleven positive unknowns, and four unknown controls. Its only proof was obtained by native heuristics with **zero model calls on that proof**. Its complete run counters were 165 model calls, 913 forwards and 3,652 generated slots; those numbers are not October performance or proof-quality results. The incomplete fresh 1.7B arm and source03 symbolic result did not form a matched size comparison. [September measured results](../hydra-implementation-2026-09-04/MEASURED_RESULTS_2026-09-05.md).

The website's **14 historical verified gallery examples** remain their own evidence, produced under their recorded configurations. They are not credited to the new WMI adapter; only the separately published fifteenth record carries the new model's proof provenance. Likewise, the old adapter's zero proofs in this matched greedy sequential panel do not erase its legacy beam-search/hybrid results or measure the full symbolic/Vampire system. [Preserved historical manifest](publication-newest-01/published-01/previous-manifest.json), [current gallery](../../hydra-playground/showcase/manifest.json).

The website default has changed, the old adapter remains recoverable, and both model-success and symbolic-fallback HTTP paths have real checked evidence. The strength claim remains limited to the completed selected panel: **four additional positive proofs, not established general theorem-proving superiority**. No additional model or native tests were run to write this report.
