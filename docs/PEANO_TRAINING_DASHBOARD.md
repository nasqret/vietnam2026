# Peano Lab Training Observatory

The Training Observatory is a small, read-only browser dashboard for one Peano policy training
allocation on the WMI A100 cluster. It shows scheduler state, optimizer progress, measured step
time and ETA, recovery publications, bounded direct log tails, run provenance, GPU telemetry, and
representative rows from the exact sealed corpus used by the run. When exact production loss
records become observable, it plots them and exposes the same points in an accessible table.

## Start it

Connect the WMI VPN and make sure the `wmicluster` SSH alias works, then run from the repository
root:

```bash
make peano-training-dashboard PEANO_TRAIN_JOB=217859
```

The command opens <http://127.0.0.1:8766/>. To keep it from opening a browser automatically, use:

```bash
python3 scripts/serve_wmi_training_dashboard.py --job-id 217859 --port 8766 --no-open
```

For a machine-readable one-shot observation:

```bash
python3 scripts/serve_wmi_training_dashboard.py --job-id 217859 --once
```

The job number is explicit on purpose. The dashboard never discovers a “latest” allocation and
therefore cannot silently switch runs.

## Architecture and trust boundary

The browser cannot and should not hold SSH credentials. The implementation has one narrow bridge:

```text
browser on 127.0.0.1
        │  GET /api/status every 5s visible / 30s hidden
        ▼
loopback Python collector and last-good cache
        │  one serialized, fixed, read-only SSH program
        ▼
WMI: Slurm state + bounded tails + fixed run artifacts
```

The server binds only `127.0.0.1`, accepts only `GET` and `HEAD`, has no scheduler-control or file-
write route, rejects query strings, serves a fixed asset list, and applies response-size and SSH
timeouts. Remote paths are fixed, derived from the requested decimal Slurm job ID, or derived from
the run identity's validated decimal predecessor ID and strictly allowlisted `train_path`.
All remote strings are projected to bounded records, serialized as strict finite JSON, and inserted
into the page with `textContent`, never HTML interpretation. Security headers disable framing,
cross-origin reads, object embedding, caching, and unreviewed scripts.

If VPN or SSH fails, polling continues but the last successful snapshot is retained and visibly
marked cached/stale. A disconnected view is never presented as live evidence.
The Refresh control requests a new serialized WMI collection and remains visibly pending until the
snapshot timestamp advances (or the collector's full SSH deadline has elapsed); a cached response
is not mislabeled as a completed refresh.

The observer is outside the prover's trusted computing base. Model outputs remain proposals; only
Peano Lab's independent kernel can establish a theorem.

## What each panel means

- **Optimizer progress** comes from the last valid carriage-return-delimited `tqdm` record in the
  bounded stderr tail. Recovery manifests provide a conservative lower bound if the progress line
  is temporarily absent.
- **Loss** contains only exact Transformers logging records or terminal training-manifest evidence.
  It is never inferred from step time, GPU load, or the admission smoke.
- **Admission-smoke loss** is a separately labeled one-step infrastructure diagnostic produced by
  the predecessor preparation job. It demonstrates that the training lifecycle ran, not that the
  production policy learned.
- **Corpus preview** shows representative admitted catalog rows: theorem, formula, focused state,
  available-library names, and the supervised next tactic behind a reveal control. It is not the
  current microbatch. The Trainer shuffles rows. Accumulation is configured for up to 32
  microbatches per update; the final partial window contains 29 for this 20,765-row run.
- **Recovery evidence** is adapter-only and intentionally non-resumable. A published recovery tree
  is useful partial evidence, not a final trained model.
- **Run identity** binds the base-model revision, LoRA configuration, sealed preparation, source
  commit, schedule, corpus size, and token exposure.

### Why the current loss plot may initially be empty

Production job `217859` writes live progress to stderr, but its periodic Transformers dictionaries
are block-buffered in redirected stdout. Until Python flushes those records, the honest loss state
is `buffered`; the dashboard says so and leaves the production curve empty. It may display
`2.8299612998962402` only as the explicitly labeled preparation admission-smoke training loss.
After a flush—or after the completed training manifest appears—the exact production points backfill
automatically.

For future runs, a reviewed Trainer callback can write one fsynced or line-buffered JSONL telemetry
record per logging boundary (`global_step`, loss, gradient norm, learning rate, epoch, timestamp).
That is an observability improvement; it must not change the objective or the evidence contract.

## Browser API

`GET /api/status` returns schema `peano-training-dashboard-v1`, version 1. The stable records are:

```text
connection  job  progress  loss  schedule  model  source
snapshots   samples  logs  resources  artifacts
```

The collector reads `squeue`, allocation-only `sacct`, `sstat`, fixed stdout/stderr paths,
`run-identity.json`, `training-manifest.json` when present, the preparation runtime-smoke report,
recovery manifests, and up to four bounded catalog examples. `/healthz` reports only local server
health; it does not assert that WMI is reachable or that training succeeded.

## Verification

The focused contract is exercised by:

```bash
python3 -m pytest \
  peano-lab/py/tests/test_peano_training_dashboard.py \
  peano-lab/py/tests/test_peano_training_dashboard_server.py \
  peano-lab/py/tests/test_peano_training_dashboard_web.py -q
```

The tests cover adversarial parsing, strict job/host validation, bounded output, stale-cache
semantics, loopback binding, fixed routing, prohibited methods, security headers, self-contained
assets, JavaScript syntax, non-overlapping polling, accessible loss fallback, and the explicit
“representative, not current microbatch” label.
