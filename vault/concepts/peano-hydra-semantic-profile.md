---
title: Peano Hydra semantic profile
tags: [peano-lab, peano-hydra, semantics, trust-boundary]
---

# Peano Hydra semantic profile

The **Peano Hydra semantic profile** fixes what later search, data, prompts,
and evaluation results mean. Profile v1 has format
`peano-hydra-semantic-profile`, ID `peano-lab-ha-intuitionistic-v1`, and
semantic SHA-256
`058b1644b066967919dae092e5e562b8845e4dd8415fff31d7cd209d51bc9e43`.

It records the term/formula grammar, de Bruijn binding, capture-avoiding
substitution, every intuitionistic [[trusted-kernel]] proof rule, PA1--PA6,
unrestricted formula induction, canonical target syntax, surface
desugarings, and result-evidence boundary. Targets must be closed and
structurally well scoped; diagnostic `#k` syntax is not admitted.

The semantic value also freezes the operational source preflight: nonempty
one-line input, no outer whitespace or unsafe Unicode category, at most 8,192
Unicode code points, and decimal numerals at most 256. These protect transport,
parsing, and certificate construction. They are marked `decision_claim =
false` and do not supply negative theoremhood evidence.

The profile is theorem-prover-only. It registers no classical checker,
external solver translation, decidable subfragment, negative witness, or
`not_theorem` result. Kernel-checked certificates yield `proved`; every
unsuccessful bounded search yields `unknown`.

The result block is explicitly `required-field-draft`. It freezes the legal
claim kinds and required-field direction, but exact types, additional-field
policy, and canonical theorem/kernel/replay/run hash preimages remain H0.1b.

The canonical JSON is `training/peano_hydra/semantic-profile-v1.json`; the
strict loader is `training/peano_hydra/profile.py`. Hydra v2 policy, row, run,
replay, and pilot records bind its semantic digest. This completes the H0.1a
semantic/claim substep, not H0.1b exact evidence or the H0
conformance/reference and structured [[macro-proof-action]] gates.

## Related

- [[peano-hydra]]
- [[trusted-kernel]]
- [[proof-certificate]]
- [[decidable-proof-fragment]]
- [[macro-proof-action]]
