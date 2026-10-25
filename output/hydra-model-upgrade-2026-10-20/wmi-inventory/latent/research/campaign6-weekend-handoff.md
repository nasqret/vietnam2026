# Campaign 6: unattended weekend handoff

Launched 2026-10-17 at 13:54 UTC on WMI. Helios login access is administratively
suspended; no alternate entry is used. The Mac is only a viewing/control client.
Closing it does not interrupt the SLURM work.

## Actual submitted work

Fifteen fresh Qwen3-1.7B LoRA runs: ordinary, fixed two-pass, random-depth
uniform on {1,2,4}, and learned stopping at paired seeds 11/29/47, each targeting
8192 updates; three additional ordinary controls target 24576 updates. Training
uses RTX PRO 6000, effective batch16, microbatch1 and context6144.

| Jobs | Purpose |
| --- | --- |
| 285381–285410 | Thirty registered 24h segments, two per logical run |
| 285411 | Live controller, 72h; report every120s, native aggregation every1800s |
| 285412–285413 | Two early RTX3090 inference pools, 48h each |
| 285414 | Bind all eligible checkpoints after training jobs terminate |
| 285415–285416 | Two late RTX3090 pools, 24h each, after binding and early pools |
| 285417 | Final aggregation/report after every inference pool and binder terminates |

At 13:55UTC jobs285381/285383/285385/285387 were running, covering ordinary and
random-depth seeds11/29. First optimizer-update records appeared by13:58UTC.
These observations do not establish model-quality progress. Later live state
comes from the generated dashboard and controller receipts.

Each logical run has cumulative36h training and8h development-evaluation caps.
Its second segment resumes the exact optimizer/sampler/RNG state or skips an
already completed run. Ordinary model/integrity errors stop the branch. There
are no automatic extra allocations. Queueing and shared capacity can extend
execution beyond the weekend; finite limits can leave training or inference
incomplete. The final report preserves that incompleteness.

## Viewing and evidence

[Private live preview](http://127.0.0.1:8769/dashboard/training/weekend/index.html).
Reconnect the transport with `bash scripts/preview_campaign6.sh`. The dashboard
is generated on WMI and distinguishes training, checkpoint-selection eligibility,
inference coverage, time limits and infrastructure failures. Its absence on the
laptop can mean the SSH preview disconnected; it does not imply training stopped.

Canonical ledger: `status/campaign6.json`. Immutable launch rosters:
`artifacts/campaign6/training-submission-wmi.json` and
`artifacts/campaign6/evaluation-submission-wmi.json`. Remote live controller:
`/home/bnaskrecki/latent/artifacts/campaign6/controller.json`.
Remote worker logs: `/home/bnaskrecki/latent/artifacts/campaign6/logs/`.
Remote finalization output: paths in the frozen evaluation launch object.

Current project scheduler observation is read-only:

```sh
ssh -o BatchMode=yes wmicluster 'squeue -u bnaskrecki -o "%.18i %.40j %.12T %.12M %R"'
```

The ceiling remains1280 requested GPUh and256 CPU-only coreh. The launch receipt
records1054.0667 requested GPUh including144h unused inference reserve and170.7
CPU-only coreh. Cancelled/failed/held allocations remain charged. Unused reserve
does not authorize automatic replenishment.

## What a result will mean

The fixed rosters are128development,256previously used diagnostic test and113
previously unexposed test-complement targets. Shared templates remain. Primary
policies and checkpoint selection were frozen before training. Complete paired
seed/target coverage, complete selection opportunities and matched inference
hardware are required for the primary comparison. Missing evidence is not a
model failure; a timeout under the registered600s target budget is a bounded
model outcome. A null or negative recurrence result is retained.

Gate285379 passed106 engineering tests; actual PRO6000 profile285368 and
four-arm/bitwise restart285369 passed. Canary285366 ran actual decoding and
selected-tensor binding, with reference native validation. It replayed zero
model-generated valid prefixes; it is not evidence of a learned proof success.
Independent source/receipt review is in
`research/agents/weekend_eval/LAUNCH-RECEIPTS-REVIEW.md`. All empirical claims
remain T4. Production quality results and human review remain pending.
