---
title: Vampire reconstruction
tags: [peano-lab, vampire, symbolic-search, proof-reconstruction]
---

# Vampire reconstruction

**Vampire reconstruction** is the planned A3 use of the classical first-order
prover as an untrusted search head inside [[peano-hydra]]; the adapter is not
implemented in the current A0/H1 slice. Native deterministic closure will run
first. Vampire may then suggest bounded premise bundles, instantiations,
witnesses, cuts, rewrites, or proof skeletons. In constructive mode those
hints must be reconstructed through ordinary [[macro-proof-action|Peano macro
actions]] and public tactics.

A raw SZS status, unsatisfiability result, clausified proof, or foreign symbol
has no theorem authority. Counted success requires a complete
[[proof-certificate]] checked against the original Peano formula by the
[[trusted-kernel]]. Exact translator, symbol map, binary, options, transcript,
premises, limits, and reconstruction trace belong to the evidence bundle.

## Related

[[critical-proof-frontier]] · [[peano-logic-profiles]] ·
[[matched-compute-proof-evaluation]] · [[peano-authoring-assistant]]
