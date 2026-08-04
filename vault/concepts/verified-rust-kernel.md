---
title: Verified Rust kernel
tags: [peano-lab, rust, lean, refinement, kernel]
---

# Verified Rust kernel

A **verified Rust kernel** needs more than a Lean reimplementation and
differential tests. Lean must prove the checker specification sound, and the
exact committed safe-Rust accepted path must refine that specification:

$$
\operatorname{RustAccept}(b) \Longrightarrow
\operatorname{LeanSpecAccept}(b).
$$

The K5–K11 route freezes a logic-carrying wire format and typed outcomes,
measures the implementation, hardens Rust resource accounting, proves the
algorithm and codec in Lean, establishes source refinement, performs a
cross-platform Python/Rust soak, and makes a separate authority decision.
`ResourceExhausted` is not `InvalidCertificate` and neither is a theoremhood
judgment.

Until those gates pass, the [[rust-wasm-shadow-checker]] may accelerate Hydra
candidate filtering and browser diagnostics, but the readable Python
[[trusted-kernel]] remains the final original-goal authority. If source
refinement fails, Python or dual authority is the honest endpoint.

## Related

[[de-bruijn-criterion]] · [[proof-certificate]] · [[browser-proof-runtime]] ·
[[peano-hydra]]
