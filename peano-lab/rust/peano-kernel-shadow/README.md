# Peano kernel shadow

This dependency-free crate independently mirrors the Peano Lab certificate
calculus. It is a **shadow checker**: its answer may detect a disagreement, but
it never replaces the authoritative Python check against the session owner's
original goal.

The logical core contains immutable terms, formulas, proof certificates,
capture-avoiding de Bruijn operations, PA1--PA6, induction, checked `Cut`, and
an explicitly separate classical `DNE` gate. The default `check` and
`check_closed` entry points are intuitionistic.

`codec.rs` implements the canonical Cut-aware `peano-lab-v2` artifact format
without a general JSON parser. It accepts only exact-arity tagged arrays,
unescaped fixed ASCII tags, portable non-negative decimal integers, and one
terminal LF. Whitespace, escapes, objects, unknown tags, references, alternate
number spellings, overflow, excessive bytes/nodes/depth, and trailing input
fail closed. `check_canonical_ha` additionally checks the decoded original
target for closure and consumes the artifact's explicit `fuel` with the same
path semantics as the verified Lean checker. A separate global step budget
bounds repeated checking work; insufficient fuel or work rejects.

Run the native checks with:

```sh
cargo fmt --all -- --check
cargo clippy --all-targets --all-features --locked -- -D warnings
cargo test --all-targets --all-features --locked
cargo test --release --all-targets --all-features --locked
```

The native process boundary reads one artifact from standard input:

```sh
cargo run --quiet --bin peano-kernel-shadow < artifact.json
```

For well-formed artifact input it writes exactly `ACCEPT` or `REJECT` to
standard output. Exit status `0` means shadow acceptance and `1` means a
well-formed logical rejection. Malformed or resource-rejected bytes produce no
standard output, a concise `ERROR: ...` diagnostic on standard error, and exit
status `2`. This result remains diagnostic; it cannot grant QED.

The native CLI is intentionally a subprocess boundary. Its byte, decoder-node,
depth, path-fuel, and checker-step limits make acceptance bounded, but the
checker does not yet charge every formula clone, equality comparison, shift,
or substitution by AST size. A hostile artifact can therefore consume more
memory or time than the headline node/step counters suggest before the
process rejects or is externally terminated. Do not embed this native shadow
in an authoritative or long-lived process. K4 must retain worker/process
memory and time isolation (and preferably charge AST work more precisely)
before exposing the checker through the browser.
