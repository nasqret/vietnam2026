---
title: Peano Hydra semantic profile
tags: [peano-lab, peano-hydra, semantics, trust-boundary]
---

# Peano Hydra semantic profile

The **Peano Hydra semantic profile** fixes what later search, data, prompts,
and evaluation results mean. The active profile v2 has format
`peano-hydra-semantic-profile`, ID `peano-lab-ha-intuitionistic-v2`, and
semantic SHA-256
`4f2713e6a21e6261bbefe5991ef545e6356807e7042c6b2c7c07183e142c3b4b`.
Historical profile v1 remains registered at digest
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

Profile v2 closes the result block by content-addressing
[[peano-hydra-result-evidence]] v1. That schema freezes exact types, rejects
additional fields, and defines canonical theorem/kernel/replay/run hash
preimages. Profile v1 keeps its historical `required-field-draft` label rather
than being silently reinterpreted.

The active canonical JSON is
`training/peano_hydra/semantic-profile-v2.json`; the strict version registry is
`training/peano_hydra/profile.py`. A frozen compatibility canonicalizer keeps
v1/v2 interpretation independent of later browser parser and limit changes.
Hydra v3 policy, row, run, replay, and pilot records bind the v2 digest.

## Related

- [[peano-hydra]]
- [[trusted-kernel]]
- [[proof-certificate]]
- [[peano-hydra-result-evidence]]
- [[peano-hydra-conformance-campaign]]
- [[decidable-proof-fragment]]
- [[macro-proof-action]]
