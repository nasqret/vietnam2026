---
title: Peano Hydra result evidence
tags: [peano-lab, peano-hydra, evidence, trust-boundary]
---

# Peano Hydra result evidence

**Peano Hydra result evidence** is the exact versioned contract for publishing
one prover outcome. `peano-hydra-result-v1` has semantic SHA-256
`cf1caf1c867ddfbe3c247e42a18b730ea6790269718170a51f9733d5a7a36b26`.

There are exactly two disjoint result kinds:

- `proved` contains a bounded canonical certificate, derived node/depth
  metrics, exact intuitionistic-kernel identity, replay evidence, run evidence,
  and `kernel_accepted = true`;
- `unknown` contains a bounded reason enum and run evidence, with no
  certificate, kernel claim, or negative witness.

Both variants reject extra fields. Hashes use domain-separated compact JSON
preimages that cannot contain their own output key. A checked positive builder
accepts an actual kernel `Formula` and `Proof`, checks against the original
target, derives every field, and only then serializes the record. A caller
cannot publish `proved` by supplying theorem text and a Boolean.

The schema forbids `not_theorem` and separator-equivalent negative vocabulary.
A timeout, exhausted search, malformed certificate, or wrong-target
certificate is `unknown` or `certificate_rejected`; none proves non-theoremhood.

The machine schema is `training/peano_hydra/result-schema-v1.json`, implemented
by `training/peano_hydra/result_schema.py` and referenced by
[[peano-hydra-semantic-profile]] v2.

## Related

- [[peano-hydra]]
- [[trusted-kernel]]
- [[proof-certificate]]
- [[peano-hydra-conformance-campaign]]
- [[macro-proof-action]]
