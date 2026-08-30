# Diagnostic comparison of the completed frontier adapter

The existing `scaling_evaluation` API supports the exact preregistered
`review-candidate-dev` plan without declaring it a reviewed benchmark. This
diagnostic can measure development proof-search behavior while the separate
full-library reference and benchmark gates remain open.

The caller is `frontier_diagnostic_run.py`; the separate one-use launcher is
`frontier_diagnostic_launch.py`. Neither changes the original evaluator,
source-only loader, kernel, model-origin validation, benchmark acceptance
criteria or training admission.

## Exact comparison

- 32 previously selected DEV goals: 16 disjunction and 16 universal routes.
- Historical v25 corrective adapter versus the completed v28 frontier adapter
  from training job 21438102, with the same pinned Qwen3-1.7B base revision.
- Both models run at 8 and 16 model calls per goal under the same optimized
  search: 128 outcomes, at most 1,536 calls, no reserved benchmark goals.
- Original plan raw SHA256:
  `a8084683ea64e4128f4d34eea0753c67fc42a55772e1c698a5dbd62865878c4b`.
- Original canonical plan SHA256:
  `f3875b785182c624abd3ea7b402420a125b38468d4971a1839028ca0ecd7343d`.

The plan is the one preserved in the actual trained candidate's readiness
record. Similarly named earlier recovery plans are not interchangeable.
No goals, budgets or outcomes may be selected after observing model results.

## Resources and inputs

The proposed reservation is one GH200, eight CPUs and 64 GiB for at most
900 seconds. A shared 720-second soft deadline includes earlier allocation
work. The independent run/profile is `frontier-diagnostic-v1`; its ledger,
output and scheduler job are separate from completed training and search runs.
No retry, resume, training or automatic follow-on job is allowed.

Original model-origin receipts, source manifests, preparation/admission
sidecars and actual saved artifact bytes remain mandatory. The two preserved
source/data roots and saved models are explicit read-only external inputs;
the transfer inventory must not claim to contain those bytes. Current input
hashes and original receipts are checked before model loading. Local metadata
checks do not claim to read remote weights or perform model evaluation.

The exact source, request and one-use allocation must be approved separately
before submission. Missing identities remain missing; a draft, completed
training receipt or successful unit test cannot substitute for approval.

## Reading the result

Report the old and new proof counts out of 32 at each budget, paired gains and
losses, model calls, invalid or rejected proposals, and measured resources.
Every claimed positive proof requires fresh independent native replay. Failed
or unfinished searches are not false theorems, and interrupted outcomes remain
unknown rather than being silently omitted.

Independent replay runs as separately bounded CPU work from the fixed Helios
deployment, outside the GPU allocation. The candidate weights remain on Helios;
local metadata admission does not perform or replace that verification.

These are public, correlated DEV diagnostics from two families. They do not
measure unseen theorem generalization, establish a sealed benchmark result,
complete the full reference campaign, or satisfy the separate matched-pilot
acceptance gate. They cannot authorize self-training or another training round.
Training loss and DEV loss remain diagnostics, not substitutes for proof rates.
