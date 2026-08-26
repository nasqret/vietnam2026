---
title: Compact headless proof runner
tags: [peano-lab, architecture, jsonl, soundness, performance]
---

# Compact headless proof runner

The **compact headless proof runner** is a fast adapter around [[peano-lab]], not a second prover.
It imports the same formula parser, proof-session owner, public tactic grammar, theorem library,
engine, and checked finalization path as the browser. It omits Pyodide, DOM panels, and routine
certificate rendering, so one Python process can import the prover once and execute many fresh
proof sessions from a finite transactional JSONL interface. It keeps one warm interpreter but
withholds results until EOF and matching trace commit, so it is not a duplex request/response
service.

Each request keeps its original theorem and logic mode in a new production `ProofSession`. The
caller supplies tactic text but cannot choose more authority than the runner's fixed
command-and-theorem capability profile. A reported QED still requires the independent
[[trusted-kernel]] to check the completed [[proof-certificate]] against that owner-retained
original theorem.

Generation uses mandatory trace mode and emits the binding version-1 transition stream separately
from compact result envelopes. An explicitly named verification mode can skip transition
rendering when replaying an already-authored script, but it does not produce training data. Strict
request limits, transactional tactic failures, checked trace continuity, and fail-stop trace writes
keep speedups outside the trust boundary.

The implementation lives in `peano-lab/py/peano_lab/batch.py` with the finite batch process in
`scripts/peano_batch.py`.

## Related

[[kernel-guided-policy-training]] · [[proof-trace-corpus]] · [[kernel-judged-evaluation]] ·
[[browser-proof-runtime]] · [[peano-lab-moc|Peano Lab MOC]]
