#!/usr/bin/env bash
# A human runs this interactively; never pipe or synthesize its decision.
set -euo pipefail
if [ "$#" -ne 1 ]; then
  printf '%s\n' 'usage: bash review-pilot.sh YOUR_REVIEWER_REFERENCE' >&2
  exit 2
fi
exec /opt/homebrew/bin/python3.11 -I -B \
  /Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-execution-20260830/scripts/review_peano_hydra_scaling.py \
  --bundle /Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-execution-20260830/_deploy/hydra-frontier-candidate-v1 \
  --expected-readiness-sha256 f5bf419b74d10f8dab70ec97c79303e5b22764988e718cfcd29f7f631d386f50 \
  --reviewer-reference "$1" \
  --output /Users/bnaskrecki/codex/peano/artifacts/frontier-experiment-2026-08-30/lineage-review.json
