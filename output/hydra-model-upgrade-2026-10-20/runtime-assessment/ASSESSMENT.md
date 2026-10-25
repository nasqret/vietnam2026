# Hydra runtime integration assessment — 2026-10-20

The installed website still uses the historical **Qwen3-1.7B mixed-retention adapter**, trained as job `21456251` on 2026-08-30, with a locally quantized 4-bit MLX base. Neither the September fresh 1.7B/4B adapters nor the newly reported latent models are installed as its default. The metadata-only readiness check passed without importing a model framework or running a proof. A Hydra server was observed at PID `30367`, port `8767`; no Hydra proof worker appeared in the same process snapshot.

The newly reported **rank-32, possibly recurrent, full-proof models need a separate inference path**. They cannot replace a file under the current rank-16 primitive-tactic loader. The least invasive first integration is to obtain a bounded full-script proposal remotely, then validate that exact proposal through Hydra's existing offline native replay worker. Preserve the existing local provider as the fallback until a candidate demonstrates better checked proof coverage and acceptable end-to-end latency.

This assessment changed no live code, model, configuration or runtime, made no remote calls and performed no inference, native proof execution, downloads or test-suite runs. Exact local file pins and observation tool receipts are in `evidence.json`. The candidate description comes from root's discovery report; its exact prompt syntax, checkpoint format and recurrent loader are still being checked by the evaluation agent.

## Installed model and source bindings

| Item | Current binding |
| --- | --- |
| Model | `Qwen/Qwen3-1.7B-Base`, revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1` |
| Adapter root | `artifacts/hydra-retention-pilot-2026-08-30/trained-model-collected-01/model` |
| Adapter manifest | `cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca` |
| LoRA weights | `adapter/adapter_model.safetensors`, 69,782,384 bytes; declared SHA `7b86fc09aafa5bbb7b443119384e6b83f1f5a5f51a44340c0ca8b2e7a3b4d7c5` |
| Quantized base | `hydra-playground/.runtime/model`; 318 listed files totaling 979,633,140 bytes |
| Quantized manifest | `fc9ebb9841ecf36243f99ee408c71cd8bf6c4df968130c96af281a82fd55809c` |
| Quantization | MLX affine 4-bit, group size 64; explicitly not numerically equivalent to training |
| Native source | `_deploy/hydra-retention-evaluation-recovery-execution-20260831`, commit `dca88930b59e3147a95d0234d804076ccf757a74` |
| Model API | `propose(goals_before, *, max_candidates)` returning a tuple of untrusted primitive tactic strings |
| Current decoder | Full ordered primitive-v4 state, focus 0, authority token mask; 1,536 input tokens, 64 output tokens |

`model_runtime.py` pins the original source catalogue, admission inputs, training job, artifact manifest, adapter bytes, tokenizer and quantized-base conversion receipt. It checks the complete original adapter population: 392 F32 LoRA matrices, rank 16, alpha 32, seven projections across 28 layers. These are deliberate identity and shape checks. A rank-32 replacement must receive its own validated specification; changing one path or hash cannot make it compatible.

The current readiness observation checks metadata, dependency versions and listed file sizes. It is not a fresh full-weight rehash, model reload or numerical smoke. Each real old-provider search performs its fuller authentication independently.

## Concrete routing points

| Boundary | Current behavior | Candidate integration consequence |
| --- | --- | --- |
| `worker.py:validate_request` | Allows theorem, finite search settings and explicit experimental native options; no arbitrary model path or remote URL. | Add a finite, host-selected candidate key only after its format and evaluation are known. |
| `worker.py:main` | Model-only routes to `model_runtime.run_search`; other search modes route to `hybrid_runtime.run_search`. | Keep both existing paths intact for rollback. |
| `hybrid_runtime.py:LazyModelPolicy` | Lazily loads the same pinned historical MLX adapter on the first unresolved choice. | A future primitive-policy factory could select another compatible primitive provider. Full-script models need a different orchestration path. |
| `experimental_runtime.py:selection` | Explicitly refuses model/hybrid use with sharing-v1; its status reports no installed learned provider. | Do not remove this restriction merely to make a new checkpoint load. A new path needs its own prompt/authority compatibility. |
| `experimental_model.py:load_torch_model` | Supports only registered Qwen3 Base models and exact pilot/historical contracts, rank-16 adapters, Linux/aarch64 Python 3.13.5 and one BF16 CUDA device under a real scheduler reservation. | Useful existing identity and counter logic, but not a generic local/WMI or latent/recurrent loader. Never replace its live reservation check with a dummy callback. |
| `worker.py:install_guard` | Denies all sockets, writes and arbitrary child processes; manual replay also forbids framework imports. | Keep remote network/allocation work outside the proof worker. |
| `server.py:JobManager` / `run_worker` | One active computation, cancellation, sampled RSS and bounded output, fresh isolated workers, confirmed cleanup before releasing the slot. | Reuse this control boundary for a host-owned remote-proposal phase followed by a fresh native replay phase. |
| `server.py` / `app.js` | Loopback host/origin and CSRF checks; model status and availability derive from the historical local provider. | A future full-script mode must expose its own availability and provenance, not claim the remote candidate is the existing local MLX model. |

## Practical path for the reported latent checkpoints

Root reports vanilla and fixed/random/adaptive recurrent Qwen3-1.7B-Base variants, rank-32 LoRA, up to four shared-core passes, and a campaign targeting 2,048 updates with 6,144-token contexts. These are provisional discovery facts, not verified load contracts. Recurrent execution adds computation without necessarily increasing parameter count. Its exact graph, attention/KV-cache semantics, stopping rule and checkpoint selection must come from the actual loader; repeating the ordinary MLX model forward pass is not an established equivalent.

1. **Compare in the candidate's native inference environment first.** Pin the actual checkpoint, Base revision/tokenizer, prompt, generation settings and recurrent execution policy. Record real generated tokens, forward/core passes, elapsed time and any timeout. Keep scheduler waiting separate from inference time.
2. **Receive data only.** A host-owned proposal process returns the original request identity, exact generated text/script, candidate identity and execution measurements. Enforce fixed output and time bounds. Do not execute generated Python, shell commands or custom loader code inside the proof worker. Use only the exact extraction grammar established by the candidate's evaluator; reject unsupported syntax instead of silently rewriting the theorem or proof.
3. **Replay against the original target.** Pass the script as `{"theorem": original_theorem, "tactics": [...]}` to the existing replay worker. Its current limits are 64 KiB request, 4,096-byte theorem, 160 tactic lines, 512 UTF-8 bytes per line, numerals at most 64, 120 seconds and 2 GiB sampled RSS. `run_proof` runs with `classical=False`, `on_error="stop"`, the finite native command set and no imported theorems by default. Unsupported or over-limit proposals are failures under this profile; do not silently raise limits for the winner.
4. **Require complete local acceptance.** The outer proposal orchestrator must require the canonical original target, `status="proved"`, `kernel_checked=true`, no remaining goals, no error, successful worker exit and confirmed cleanup. Remote claims, a valid prefix, a parser success or an open final state do not suffice. If the candidate uses a different native source or tactic vocabulary, the evaluation agent must establish compatibility before this replay profile is selected.
5. **Preserve provenance and fallback.** A replay result presently has `kind="manual"` and `model_used=false` because replay itself does not use a model. Wrap it in a separate model-proposal record identifying the generation source and local verification; do not relabel it as a model-free discovery. Keep the existing hybrid path available. Switch the default only after the selected deployed representation passes the quality decision.

For the first rollout, this can be an explicit full-script mode backed by one bounded remote job and one local replay. It does not require moving the search tree to the server or reopening the offline proof worker's network access. Remote Slurm queue latency may make it suitable for asynchronous experiments rather than immediate local interaction; actual measurements should decide.

## Local resource feasibility

The actual host reports **16 GiB RAM**, `MacBookPro18,3`, eight CPUs (`0/397d58`). The VM snapshot had about 6.19 GiB occupied by the compressor, 4.23 GiB wired and only about 70 MiB free; inactive/file-backed memory is reclaimable, so these numbers are not a precise available-memory estimate. They do not justify loading a new model into the user's current workload without a bounded memory measurement.

The existing MLX provider limits model allocation to 6 GiB and its cache to 256 MiB; local search workers use an 8 GiB sampled RSS ceiling. The old 1.7B quantized files occupy about 0.91 GiB plus roughly 67 MiB of F32 LoRA weights. A compatible ordinary rank-32 1.7B adapter may be practical in a separate MLX profile, but its actual target modules and recurrent execution must be established first. A recurrence-aware MLX port is additional implementation work, not a path change.

The registered BF16 4B base alone is 8,044,982,000 bytes; 8B is 16,381,516,776 bytes. Neither is a drop-in for this Mac's current loader or memory policy. If a vanilla 4B candidate wins, use a separately derived and evaluated quantized local package or keep remote inference. The existing shape helper already records the important 4B distinction: hidden size 2,560, query width 4,096, 36 layers and 504 rank-16 LoRA matrices. Quantization or a recurrent port changes the deployed representation and needs its own checked evaluation before replacing the default.

## Minimal validation and rollback

Do not build another campaign release framework. The integration needs a small candidate descriptor, a host-owned proposal adapter, the existing replay acceptance boundary, and an explicit selector that retains the historical default.

Before any default switch, use the existing focused tests appropriate to the chosen path: `tests/test_worker.py` for request limits/replay; `tests/test_server.py` for one computation, cancellation and cleanup; `tests/test_hybrid_runtime.py` for actual model-work accounting; `test_model_runtime.py` if the old provider boundary is touched. `tests/test_experimental_model.py` and `tests/test_experimental_decoder.py` apply to a new compatible primitive provider, not automatically to a full-script recurrent model. These suites were inspected, not run during this assessment.

Add only the missing boundary cases: a remote forged-success claim, changed target, truncated script, disallowed import/command, valid but unfinished prefix, and cancellation before local replay; none may receive a proved result. A genuine successful candidate then needs exact-script local replay and a small representation-specific regression comparison with the existing model on the same theorems and limits. Keep generation attempts/tokens/latency distinct from native replay time. Existing exposed September cases may be diagnostics but cannot become a fresh unseen benchmark by relabeling them.

Keep the existing adapter, quantized base, readiness record, provider file and default selector unchanged while testing the new mode. Put new weights and conversions in a separate versioned directory. Capture the old selector and server command. Once the candidate is demonstrably better, switch only that explicit selector while idle and restart only if required by module caching; a failed load or regression rolls the selector back to the retained historical profile. A new local package should never overwrite `.runtime/model` or the archived adapter, and a remote option should never silently fall back while claiming the selected model ran.
