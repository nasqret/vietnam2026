# WMI-to-Hydra bridge diagnosis — 21 October 2026

**All 50 saved WMI successes replay through the unchanged Hydra native checker, without theorem imports.** Every one of their 3,753 tactic steps and intermediate goal states matches the saved WMI evaluation. The model's saved proofs are compatible with the checker; the application and search interfaces impose additional restrictions.

This was a CPU-only reproduction of saved development proofs, not fresh model inference or another old-versus-new model benchmark. The deployed model, website limits and proof checker remain unchanged.

## What actually ran

| Execution | Cases | Verified proofs | Exact trajectory matches |
|---|---:|---:|---:|
| Unchanged public Hydra replay worker | All 50 saved successes | 24 | 24 |
| Separate bounded native diagnostic profile | 26 rejected inputs + one accepted control | 27 | 27 |
| Unique saved successes across both | 50 | **50** | **50** |

The other 26 public requests all failed **before the first tactic**, with `formula exceeds the bound/context-variable limit`. None reached a tactic failure. The diagnostic profile uses the same original native source and no-imports capabilities, but explicitly admits larger input formulas and traces. It is separate code under this experiment directory; it does not patch or disable the public worker's limits.

All credited proofs close the original theorem, have empty goals, a checked native certificate and an exact QED footer, and account for every supplied tactic. Independent read-only review matched the stored result and raw-output hashes and all 3,753 transitions against WMI. There were 4,875 certificate nodes across the 50 distinct proofs, with 45–164 nodes per proof. No standalone Lean verification was performed here.

The public replay batch took 14.51 seconds. The additional 27-case batch took 17.63 seconds; its largest observed child RSS was 50,282,496 bytes, and its longest child took 0.813 seconds. No GPU allocation, retraining, model execution, remote job modification or automatic retry occurred.

## Concrete integration differences

1. **Input admission.** The public profile allows 16 bound/context variables. The larger saved cases reach 42 simultaneously bound variables; the diagnostic cases also reach 317 AST nodes, beyond the public profile's 256-node ceiling. The separate test profile has explicit ceilings of 64 binders, 1,024 AST nodes, depth 128, 128 actions, a 2 MiB trace and a 30-second child deadline. The proof checker and theorem authority are unchanged. Some saved traces also exceed the public 512 KiB trace allowance; this is a secondary limit, not the error reported by the public run.

2. **Trajectory length and time.** Every saved success uses more than 32 model actions: minimum 35, median 57.5, maximum 127; 23 need more than 64. Yesterday's integration screen allowed 16 model calls. A verbatim reproduction of these trajectories therefore needs a different budget. In the historical WMI execution, 35/50 successful cases spent over 30 seconds on generation alone. These WMI timings are not GH200 or Mac latency measurements, and the call counts do not establish the shortest possible proofs.

3. **Persistent metavariable names.** Hydra's search normalizes metavariable names separately for each state, while WMI's training/evaluation traces retain names across a trajectory. A real 42-action current-native replay reproduced the difference before step 43 of `c5-0e7a4634564441e09637546d`: the saved model prompt contains `?t2`, but search's canonical rendering calls it `?t1`. A separate persistent name map reproduces every one of the 43 checked WMI prompts exactly. The search's canonical representation can remain useful for deduplication without being the model's input representation.

4. **Who chooses the early steps.** WMI generates its sequence from the original root, including names such as `intro v100`. Hydra normally lets heuristics introduce variables and hypotheses first, with different names. This changes the input distribution seen by the model. It is a confirmed interface difference, not a measured explanation of all failures in yesterday's different test suite.

The compact prompt serializer itself is correct. All 4,672 saved prompts across the 64 WMI attempts match the frozen all-goal, focus-zero serialization. It includes every ordered goal: 1,545 prompts contain multiple goals, with up to six open goals. No first-goal truncation was found.

The library-import hypothesis is not supported for these successes: all 3,753 successful actions are `intro` (1,775), `apply` (713), `exact` (579), `cases` (384) or `have` (302). **No successful script uses `use`.** This narrows the library caveat in the 20 October report; it does not erase that report's actual test results.

## Implementation

- [Literal replay diagnostic](replay/replay_saved_successes.py) exercises the unchanged public worker and records the first state/prompt divergence or input rejection.
- [Larger-input diagnostic](replay/direct_native_replay.py) admits only the exact authenticated saved requests, verifies all 470 current native Python files, and runs isolated sequential children under explicit resource limits. It adds no library theorem or trusted proof rule.
- [Sequential runner prototype](provider-audit/sequential_lane.py) follows one candidate trajectory from the original theorem, preserves all ordered goals and prefix-persistent names, and leaves heuristic search unchanged. It has ceilings of 128 actions, 128 tokens per action, 16,384 total decision tokens, 6,144 context tokens and 300 seconds. The host must provide an external watchdog and authenticated native/model adapters. A fresh proof requires native closure plus independent replay; a saved prediction fixture can never claim fresh inference or a new proof.

The sequential runner remains isolated, not installed in the website. Its saved-record wiring tests are distinct from the actual CPU proof replays above. Fresh checkpoint-backed inference, host integration and an equal-budget comparison remain necessary before replacement. The current model stays the default; this diagnostic does not establish that it is better or worse than WMI.

The final saved-record tests passed for 35-, 94- and 127-action trajectories, including multiple goals and persistent metavariables; a 16-action limit stops the sequence and a truncated goal array is rejected. A separate check accepts different replay request/session IDs while rejecting changed goals, tactics or certificate-node counts. These tests report zero model calls, zero native executions and zero new proofs. The actual native proof replays are the separate batches above.

## Provenance and reproduction

The retrieved 31,855,858-byte WMI report has SHA-256 `0bfad5647672fd4c45f40ab76a1e204dc801f1500a50ae3840dcc2184aa40ec2`, matching the locked C6 vanilla47 step-8192 selection. It contains 64 completed development attempts: 50 saved proofs and 14 tactic errors. Only the 50 successful scripts were replayed here; do not report this as 100% theorem-solving accuracy.

The historical generations bind evaluation-snapshot SHA `d6c346d466af504fd5ec102d5d17ba9a64352472b0333130ee8fc4201f6f878e`. The selected saved `best.pt` binds SHA `c6c5c90b27499f5f908d1a45f37d17087774e93e4e07db223fadf669f771c731`. The locked selection links both at step 8192. Neither checkpoint was loaded in this diagnostic; tensor equality is not inferred merely from those different file hashes.

- [WMI collection receipt](wmi-evidence/COLLECTION_RECEIPT.json), [saved proof report](wmi-evidence/proofs.jsonl), [selection](wmi-evidence/selection.json).
- [Public-worker results](replay/noimports-01/SUMMARY.json), actual completion `6ce120`, exit 0.
- [Larger-profile results](replay/direct-native-01/SUMMARY.json), actual completion `89b4d6`, exit 0; independent review `1b2180`.
- [Combined proof inventory](REPLAY_UNION.json), with exact accepted IDs and diagnostic resource measurements.
- [Saved prompt audit](provider-audit/SAVED_PROMPT_AUDIT.json) and [actual state-rendering fixture](provider-audit/STATE_RENDER_FIXTURE.json), completion `28b029`, exit 0.
- [Sequential wiring fixture](provider-audit/SAVED_SEQUENTIAL_FIXTURE_V2.json), completion `a86700`, and [replay metadata checks](provider-audit/REPLAY_METADATA_FIXTURE.json), completion `d86d5e`, both exit 0.
- [Diagnostic scope](SCOPE.json), [public replay action](replay/ACTION.json), and [larger-profile action](replay/DIRECT_NATIVE_ACTION.json).
- [Final completion and preservation check](COMPLETION.json): exact code/result hashes and confirmation that the original live runtime and selection files are unchanged.

The next model comparison should use the authenticated selected weights in the state-preserving sequential runner, with the same theorem authority, explicit adequate budgets and an equally bounded baseline. Keep development reproduction separate from a fresh held-out evaluation and from website deployment.
