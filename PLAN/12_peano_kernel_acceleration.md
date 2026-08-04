# Peano kernel acceleration and Rust shadow checker

## Objective

Make large Peano certificates inexpensive to validate without weakening the
project's trust boundary. Optimize the authoritative readable Python checker
first, then build an independent native/WebAssembly Rust implementation in
shadow mode. Rust cannot grant QED unless the prospective K5--K11 gates pass
and the binding design receives a separate reviewed amendment.

## Non-negotiable contracts

- [x] Every published QED still passes `peano_lab/kernel/checker.py` against
      the session owner's original goal.
- [x] Optimizations preserve the intuitionistic/classical mode boundary,
      capture-avoiding substitution, induction, and complete `Cut` checking.
- [x] Caches are per invocation or explicitly untrusted; no stale theorem
      result can cross an independent final check.
- [x] Timing observations never become proof authority or acceptance
      thresholds.
- [x] Native Rust decoding errors, limits, unwinding panics, and disagreements fail
      closed and leave the Python proof session unchanged.
- [x] Rust-only QED requires a later binding-design amendment and independent
      review; it is not authorized here.

## K0 — Measurement contract

- [x] Separate cold library replay, one extra original-goal kernel check, and
      certificate-metric phases.
- [x] Record environment and certificate identity without pass/fail timing
      thresholds.
- [ ] Add representative quick, medium, FTA, and layered-QR benchmark rows.
- [x] Retain before/after measurements and source identities in an artifact.

## K1 — Authoritative Python checker

- [x] Replace eager whole-context binder shifting with per-hypothesis pending
      shifts materialized only by `Hyp`.
- [x] Make trusted constructor dispatch identity-only and reject adversarial
      metaclass equality that can impersonate term, formula, or proof tags.
- [x] Test mixed-age contexts, nested binders, `Cut`, both `OrElim` branches,
      and both sides of the `ExistsElim` scope boundary.
- [x] Keep the checker below the roughly 300-line design ceiling.
- [x] Replay the complete public library twice from cleared caches and compare
      canonical receipts.
- [x] Run all kernel, mutation, original-goal, import-boundary, and malformed
      input tests.

Observed development measurement, arm64 CPython 3.10, unchanged 73,767-node
FTA certificate:

| Phase | Before | Lazy context |
|---|---:|---:|
| Extra final kernel check, median of five | 4.338 s | 0.451 s |
| Cache-cleared library replay | 57.497 s | 29.241 s |

These values are observational and machine-specific.

Two complete cache-cleared public-library passes each reconstructed 384
theorems and produced receipt
`cee5f55c9801b8698a18a0795c06d2ae0455b49dbb7325f71aeb0c7093c20ef3`.
The first runtime-weighted eight-way local suite had a critical path of 504.44
seconds; feeding those observations back into the strict profile gives modeled
shard loads spanning only 420.5--421.5 seconds. Exact before/after checker
hashes, raw timings, certificate metrics, and shard observations are retained in
`artifacts/peano-kernel/performance-baseline-v1.json`.

After the exact-constructor hardening, three fresh complete differential
processes again replayed all 384 theorems and produced the identical canonical
artifact receipt
`4652c103b317ddf3405f74c022d2229be0c7bdb57fa94c9b0cc6e129d5a20b64`.
The retained second report is
`artifacts/peano-kernel/native-differential-v1.json` (file SHA-256
`0aaa968c91d8769c101afd51681090396a31e4885a2629e7ecfb44113cd47e5d`);
it seals 159 implementation sources and the exact native executable.

The final exact-tree eight-shard suite passed 2,707 tests with twelve
intentional skips and zero failures. Shard durations were 475.21, 487.90,
454.08, 448.49, 458.04, 494.88, 459.74, and 435.09 seconds; the 494.88-second
critical path includes the socket-enabled local dashboard-server shard.

## K2 — Replay and CI critical path

- [x] Fuse structural and identity resource metrics where callers currently
      traverse the same certificate twice.
- [x] Measure tactic `_commit` scans and fuse the duplicate traversals with
      transactional equivalence directly tested.
- [x] Replace source-byte shard balancing with a strict, versioned runtime
      weight manifest and deterministic longest-processing-time assignment.
- [x] Keep two cold admission passes and every semantic mutation; do not hide
      them behind a persistent result cache.
- [ ] Use the existing layered-replay compiler for repeated dependency
      scaffolds where it produces the same ordinary kernel certificate.

## K3 — Native Rust shadow checker

- [x] Add a dependency-free crate with `#![forbid(unsafe_code)]`.
- [x] Implement terms, formulas, proof constructors, shifting, substitution,
      PA1--PA6, induction, `Cut`, and explicitly gated DNE independently.
- [x] Strictly decode the canonical Cut-aware `peano-lab-v2` artifact format;
      reject noncanonical bytes, unknown tags, cycles/references, overflow,
      excessive depth/nodes, and trailing input.
- [x] Export the session owner's original goal, never a final tactic-state
      target or trusted theorem name.
- [x] Differentially check all 384 public theorems plus focused examples,
      malformed input, wrong-target, and zero-fuel mutations between the
      authoritative Python kernel and native Rust.
- [x] Replay representative canonical artifacts through the pinned Lean
      verifier as a third implementation boundary. H0 later covered all 2,058
      registered conformance artifacts with no Lean disagreement.
- [ ] Benchmark encoding, decoding, checking, and complete shadow latency
      separately.

## K4 — Browser WebAssembly shadow

- [x] Pin a Rust toolchain and `wasm32-unknown-unknown` target reproducibly.
- [x] Build the same core as native Rust and deterministic integer-only WASM.
- [x] Run it in a separate worker over transferable bounded certificate bytes.
- [x] Initialize concurrently with Pyodide; do not add thread/COOP/COEP
      requirements.
- [x] Include JS/WASM bytes in `APP_MANIFEST.sha256`, immutable release paths,
      MIME/compression checks, and browser/deployment contracts.
- [x] Require Python acceptance; record Rust agreement or shadow failure
      without letting Rust publish QED.

K4 candidate build `2026-08-04f` is application
`a-d9bd305e4cad`. Its path-remapped 52,890-byte module has SHA-256
`2ba86a22a01602a504df792830e25d743a7038876f47b2b6effa50fe00099063`,
no imports, unshared memory capped at 256 MiB, and a one-shot ABI. Two clean
Rust 1.95.0 builds are byte-identical. Native wrapper debug/release suites
each pass 14 tests; the real module passes HA/classical acceptance, wrong
target, zero fuel, malformed input, one-shot, resource, portable-index, and
memory-cap fixtures. A complete real-WASM run accepted all 384 originals and
rejected all 1,152 wrong-target/zero-fuel/malformed mutations. Its 1,536-case
artifact receipt exactly matches native Rust:
`4652c103b317ddf3405f74c022d2229be0c7bdb57fa94c9b0cc6e129d5a20b64`.
The retained report additionally seals all 1,536 per-case artifact hashes, its
Python/Node runner sources, and all-case receipt
`2e6e5df23ec90555bb754b7297d87b75f37a1e6f9fcd5a6d9da6facbf1ad1f68`.
Worker and main-page harnesses pin result-before-artifact
ordering, transfer, timeout, trap, restart, generation suppression, and the
rule that only Python publishes QED. This is a sealed local candidate, not a
staging or production deployment claim. The machine-readable K4 receipt is
`artifacts/peano-kernel/browser-wasm-v1.json`.

## K5 — Authority and protocol freeze

- [ ] Amend the binding design only prospectively; current Python authority
      and all version-2 evidence remain unchanged.
- [ ] Freeze `peano-lab-v3` canonical bytes with the exact logic mode inside
      the artifact. Preserve v2 as immutable archival input.
- [ ] Freeze typed outcomes: `Accept`, `InvalidCertificate`,
      `ResourceExhausted`, `MalformedInput`, and `InternalError`. Only
      `Accept` may grant QED; every other result carries no theoremhood claim.
- [ ] Bind original target, certificate, logic, wire format, verifier build,
      and resource-profile identities into every verification receipt.
- [ ] Define the supported production envelope and an explicit Python fallback
      outside it.
- [ ] Obtain independent review of grammar, classical policy, target ownership,
      result meanings, and every hash preimage.

## K6 — Complete measurement before optimization

- [ ] Add fixed quick, medium, FTA, and layered-QR artifacts to K0.
- [ ] Measure encoding, decoding, core checking, process/worker overhead,
      peak RSS, and WASM memory separately for Python eager/lazy, Rust native,
      Rust WASM, and the pinned Lean verifier.
- [ ] Retain cold/warm raw reports, exact artifact/source/binary hashes, and
      reproducible build receipts before registering performance thresholds.

Timing remains irrelevant to soundness.

## K7 — Production Rust candidate

- [ ] Separate the pure checker, canonical codec, and native/WASM wrappers.
- [ ] Make accepted-path arithmetic checked and total; distinguish resource
      exhaustion from logical rejection.
- [ ] Charge or conservatively bound AST-sized shift, substitution, clone, and
      equality work. Preserve process/worker isolation and `forbid(unsafe_code)`
      in the logical core.
- [ ] Adopt arena or lazy-context representation only if K6 justifies it; if
      used, prove refinement to eager materialized contexts.
- [ ] Run debug/release native and WASM tests, Miri, decoder fuzzing,
      exhaustive bounded-AST enumeration, every public certificate and
      semantic mutation, panic/trap rejection, and deterministic builds.

No theorem names, trusted library, tactics, Vampire, or ML enter the kernel.

## K8 — Lean version-3 specification and soundness

- [ ] Add explicit artifact logic, typed verdicts, exact production envelope,
      and the chosen context representation to the Lean specification.
- [ ] Prove HA/classical gates, v2-read/v3-write migration, codec round trip,
      and that resource exhaustion yields no logical conclusion.
- [ ] Prove the core implications:

      ```text
      rustSpecAccept -> Derives logic [] proof target
      Derives logic [] proof target -> target.Holds valuation
      rustSpecVerify bytes = Accept -> decodedTarget.Holds valuation
      lazyCheck = eagerCheck  -- inside the registered envelope
      decodeV3 (encodeV3 artifact) = artifact
      ```

- [ ] Pin Lean/toolchain/source manifests, reject placeholders, audit axioms,
      mutate the codec, and reproduce cleanly on WMI.

This proves the mathematical algorithm specification, not yet the Rust source.

## K9 — Exact Rust-source refinement

- [ ] Run a pinned feasibility spike translating the exact pure safe-Rust core
      into Lean, initially with Aeneas/Charon or another reviewed source-level
      route.
- [ ] Require automated deterministic translation from committed Rust sources,
      no opaque accepted-path functions, and explicit compiler/runtime TCB.
- [ ] Prove one-way soundness refinement:

      ```text
      exactRustSource returns Accept -> Lean specification returns Accept
      ```

- [ ] Prove reverse refinement inside the supported envelope for compatibility.
- [ ] If the tool cannot cover the accepted path, either reduce the core to a
      supported verified Rust subset or retain Python/dual authority. A second
      handwritten Lean checker is not a substitute.

## K10 — Mandatory dual-check soak

- [ ] Run Rust and Python before every published in-envelope QED and require
      agreement; record explicit Python fallback outside the Rust envelope.
- [ ] Fail library/release admission on any disagreement and leave session
      state/history unchanged on either checker failure.
- [ ] Replay every library epoch, training positive, Hydra evaluation proof,
      semantic mutation, and future QR artifact on x86-64, arm64, and browser
      WASM, with sustained fuzz/resource-exhaustion campaigns.

Python remains authoritative throughout the soak.

## K11 — Reviewed cutover decision

- [ ] Choose explicitly among Python sole authority, mandatory dual authority,
      Rust authority inside the refined envelope with Python fallback, or Rust
      sole authority.
- [ ] Retain the readable Python checker permanently as pedagogical reference,
      independent conformance oracle, and at least first-epoch fallback.
- [ ] Repeat K8--K10 for every semantic, logic, or kernel-format revision.

The recommended first cutover, if K9 succeeds, is Rust authority only inside
the formally refined envelope with Python fallback. No Rust-only QED is
permitted if K9 fails. Completing K0--K4 implies no K5--K11 outcome.
