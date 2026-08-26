# Readable, independently checked Peano-to-Lean theorems

The current shared Alpha-v25 product boundary and next Hydra engineering
milestone are summarized in
[`HYDRA_PRODUCT_ROADMAP.md`](HYDRA_PRODUCT_ROADMAP.md).

Peano Lab's Lean exporter has two audiences. Mathematicians need a short
theorem, useful names, ordinary number-theoretic concepts, and a quick way to
reuse the result. Independent proof auditors additionally need the complete
constructive certificate, every dependency, and Lean's own checker-soundness
judgment. The presentation package separates these audiences without changing
the proved statement or weakening either checker.

## Start with a small real proof

Run the following command from the arithmetic project root:

```bash
python3 scripts/export_peano_lean.py add_comm \
  --format compact \
  --package-dir /private/tmp/peano-lean-addition \
  --verify
```

The ordinary Lean theorem is written to a short, human-facing `Theorem.lean`.
Its separately imported `Certificate.lean` retains the complete independently
checked Peano certificate. `--verify` elaborates the generated modules in
dependency order using the existing, Mathlib-free Lean companion.

For a more interesting number-theoretic example:

```bash
python3 scripts/export_peano_lean.py prime_unbounded \
  --format compact \
  --package-dir /private/tmp/peano-lean-primes \
  --verify
```

The readable statement uses conservative aliases such as:

```lean
∀ n : Nat, ∃ p : Nat, Lt n p ∧ Prime p
```

`Lt` and `Prime` are not new axioms. The generated `Presentation.lean` defines
them by the exact witness-bearing formulas accepted by the unchanged Peano
kernel, and Lean unfolds those definitions when checking the public theorem.

The same conservative prelude exposes exact finite-coding names such as
`BetaAt`, `Product`, `AllPrime`, and `Sorted`. Consequently the native
fundamental theorem of arithmetic can be inspected as a short factorization
statement without pretending that its first-order proof already has primitive
Lean lists:

```bash
python3 scripts/export_peano_lean.py fundamental_theorem_of_arithmetic \
  --format pretty
```

## Deterministic file and module names

A generated package has this logical shape:

```text
manifest.json
manifests/
  PrimeUnbounded_<content-digest>.json
PeanoLab/
  Presentation.lean
  Generated/
    PrimeUnbounded_<content-digest>/
      Certificate.lean
      Theorem.lean
```

The theorem name is converted to a recognizable Lean module component; its
content digest distinguishes different editions, exact statements, or proof
certificates. The same inputs generate the same names. Different evidence never
silently reuses an existing theorem's certificate module.

The root manifest is an additive catalog, while each theorem keeps its own
content-addressed receipt. Repeated exports to the same package reuse the
shared notation and retain every earlier theorem. Manifests record exact and
human-facing statement identities, generated module names and paths, content
hashes, certificate sizes, proof-node counts, and the current edition. Treat
them as an inventory, not as proof authority: Lean's kernel still checks the
certificate and theorem.

Typical module components include:

```text
AddComm_<digest>
PrimeUnbounded_<digest>
FundamentalTheoremOfArithmetic_<digest>
QuadraticReciprocityCombined_<digest>
```

## Pick the amount of detail

```bash
# Small, reusable theorem module and its separately checked certificate.
python3 scripts/export_peano_lean.py prime_unbounded \
  --format compact --package-dir /private/tmp/peano-lean-primes

# Mathematical preview with safe, exact abbreviations.
python3 scripts/export_peano_lean.py prime_unbounded --format pretty

# Fully expanded original Lean proposition when inspecting equivalence.
python3 scripts/export_peano_lean.py prime_unbounded --format exact

# Historical single-file, fully self-contained certificate audit.
python3 scripts/export_peano_lean.py prime_unbounded \
  --format full --output /private/tmp/prime-unbounded-full.lean
```

Omitting `--format` preserves the original full-export command and its
compatibility guarantees. Use `--force` only when intentionally replacing a
specific previously generated output.

Within the interactive Peano Lab:

```text
pa lean add_comm
pa lean prime_unbounded
pa lean exact prime_unbounded
pa lean tactics prime_unbounded
pa lean full prime_unbounded
pa lean alpha quadratic_reciprocity_combined
pa lean alpha linear_congruence_solvable_iff_gcd_divides
pa proof alpha infinitely_many_primes_one_mod_four
```

The default output is bounded and theorem-first. Full machine-generated source
is requested explicitly; the original Peano tactic script is labeled honestly
and is not misrepresented as an executable Lean tactic proof. Certified
modules depend on the locally installed Lean companion, so they are not sent
to the public Live Lean editor in a multi-megabyte URL.

Browser previews and the CLI `pretty` / `exact` views inspect the authenticated
release statement only: they perform **no fresh Peano proof replay and no Lean
compilation**. Use an explicit package `--verify` when an independently
compiler-checked certificate is required. This distinction keeps even the
large Alpha quadratic-reciprocity statement safe to inspect interactively.
The browser's explicit `full` view additionally refuses theorem dependency
closures above its small fixed limit before loading a proof; use the
deliberately bounded terminal exporter for large certificates instead.

## Readable dependency proof strands

The separate proof-strand views retain original theorem names, exact
first-order statements, genuine authored Peano tactic lines, and the
authenticated topological dependency graph:

```bash
python3 scripts/export_peano_lean.py infinitely_many_primes_one_mod_four \
  --edition alpha --format outline

python3 scripts/export_peano_lean.py linear_congruence_solvable_iff_gcd_divides \
  --edition alpha --format strand \
  --package-dir /private/tmp/peano-lean-linear-congruence
```

An `outline` uses release metadata only: it never opens a proof artifact,
replays an empty-context theorem, or invokes Lean. For
`infinitely_many_primes_one_mod_four`, the exact Alpha-v19 outline records
**385 named theorems**, **1,204 real dependency edges**, and maximum
dependency depth **47**. The browser command
`pa proof alpha infinitely_many_primes_one_mod_four` stops graph expansion
after 128 entries while still showing the exact root, source, original proof
decisions, and bounded terminal-export command.

A `strand` package constructs and checks each dependency-relative proof in
topological order; it does not reconstruct a redundant, potentially enormous
closed root certificate. Authored readable steps are identified as Peano
tactics, not silently claimed to be executable Lean tactics. When readable
translation is unavailable, the package retains its actual independently
checked local constructive certificate. Add `--verify` only when the reviewed
Lean source-size, memory, and wall-clock limits can accommodate the generated
modules. Neither an outline nor an unverified strand claims independent Lean
compilation.

## Alpha and complete dependency bundles

Alpha is a separately authorized theorem edition. A checked Alpha theorem does
not become Stable just because it can be exported:

```bash
python3 scripts/export_peano_lean.py quadratic_reciprocity_combined \
  --edition alpha --format pretty

python3 scripts/export_peano_lean.py add_comm \
  --edition alpha \
  --format compact \
  --package-dir /private/tmp/peano-lean-alpha-addition
```

An authenticated complete proof DAG can also be supplied explicitly:

```bash
python3 scripts/export_peano_lean.py quadratic_reciprocity_combined \
  --edition alpha \
  --proof-bundle research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json \
  --format compact \
  --package-dir /private/tmp/peano-lean-quadratic-reciprocity
```

Historical immutable Alpha v18 admitted multidigit Lucas, both Kummer
endpoints, strict Bertrand, universal four squares, and the all-natural
two-square classification. Historical immutable **Alpha v19** additionally
closes its **84** remaining body-only obligations and adds **64** independently
checked Pythagorean, prime-two-square, linear-congruence, and one-modulo-four
prime results. Its exact historical edition identity is
`905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7`.
Historical immutable **Alpha v20** preserves all those exact rows and adds
**39** independently proved polynomial, finite matrix-component, strict
Bertrand-prime, and finite continued-fraction theorems. Its **1,776 checked
statements** comprise **432 unchanged Stable** theorems and **1,344 Alpha-only**
theorems, with no unchecked or pending rows. Its historical edition identity is
`ee0f596150d8609ab302303ade44c4413290675398a1d6999a47b3ba046ac38b`.

Historical immutable **Alpha v21** preserves every historical v20 row and adds
**54** independently checked theorems: 23 arbitrary natural/signed
matrix-product and determinant results, 15 Euclidean execution/halving
results, and 16 binary modular-exponentiation results. All **1,830 enrolled
statements have checked-use authority**: **432 unchanged Stable** and **1,398
Alpha-only**, with no unchecked or pending rows. Its exact edition identity
is `aee42cc37e4a4073eb4892e81e4f26d957b3b4b42675c1ed4e67c90dc89602e6`.
Its complete 209-node advanced-layer proof artifact has been separately
accepted by the unchanged intuitionistic kernel and the independently
compiled Lean checker.

Historical immutable **Alpha v22** preserves all 1,830 historical v21 rows and
adds **60** independently checked theorems: **21** total and unique
first-order binary-length theorems, **20** genuine Euclidean gcd-invariant
and terminal-state identification theorems, and **19** complete
supplied-digit binary modular-execution and power-invariant theorems. All
**1,890 enrolled statements have checked-use authority**: **432 unchanged
Stable** and **1,458 Alpha-only**, with no unchecked or pending rows. Its
exact edition identity is
`2750384264856ad10910c1e9369746da886f4760d41e356bfc9e7f8f4563c7db`.
The complete **240-node**, **597-edge** transport-layer proof artifact is
independently accepted by both the original intuitionistic kernel and the
compiled Lean checker. At that historical v22 checkpoint, G101 and G102
remained open for their formal logarithmic bounds.

Historical immutable **Alpha v23** then adds **59** independently checked
theorems: **17** exact logarithmic Euclidean-GCD results, **24** canonical
arbitrary-exponent digit/execution results, and **18** constructive
three-modulo-four prime-infinitude results. All **1,949** enrolled statements
have checked-use authority; its independently checked **617-node**,
**1,871-edge** proof artifact has SHA-256
`cc0051da2cac31e382c79223999d448a1119f62aa448f1c7f68a6b9c3edf9d11`.
Consequently G101, G102, and G025 are genuinely proved, not open.

Historical immutable **Alpha v24** preserves that complete v23 catalog and adds
**59** independently checked theorems: **17** arbitrary signed cofactor-minor
and four-dimensional determinant results, **15** exact natural Horner/formal
derivative results, and **27** pairwise-coprime finite-CRT/arbitrary-list-LCM
results. All **2,008 enrolled statements have checked-use authority**:
**432 unchanged Stable** and **1,576 Alpha-only**, with **6,423 actual proof
edges** and no unchecked or pending rows. Its edition identity is
`1f4390b8ca5784ece54857fa666007f884b79e2670ef8bb32b2710c10f298a1b`.
Its **203-node**, **502-edge**, **738,923-byte** research-layer proof artifact
has SHA-256
`627e39ed29b10db48bf37d5bef8750d48009a7524c822a7c5e7c83e96a8e9cf9`
and is independently accepted by the unchanged original kernel and Lean
checker.

Current immutable **Alpha v25** preserves every historical v24 proof and adds
**72** independently checked theorems: **29** signed cofactor and alternating
fold results, **19** exact Taylor/formal-derivative and qualified one-step
Hensel results, and **24** noncoprime CRT compatibility/gcd-LCM results. All
**2,080 enrolled statements have checked-use authority**: **432 unchanged
Stable** and **1,648 Alpha-only**, with **6,633 actual proof edges** and no
unchecked or pending rows. Its exact edition identity is
`3516d4730428c79fc73aa6fbdbabc43d93921471941bb2f144ea3d29e0af5b28`.
Its **302-node**, **820-edge**, **1,041,166-byte** breakthrough-layer proof
artifact has SHA-256
`d4532076049be869e4e397d0fcee81b668bd3fd5c7d9173028bb1bdb80b9793a`
and is independently accepted by the unchanged original kernel and Lean
checker. The stronger T13, G095, and G011 milestones remain open: checked
component export never certifies an unproved broader goal.

For example, an actual newly enrolled v20 theorem can be automatically
translated and independently typechecked using the existing bounded exporter:

```bash
python3 scripts/export_peano_lean.py signed_matrix_two_determinant_exists \
  --edition alpha \
  --format compact \
  --package-dir /private/tmp/peano-lean-signed-determinant \
  --verify \
  --lean-project ../peano-lab-lean \
  --max-memory-mib 768 \
  --max-verify-seconds 60
```

The verified translated proposition is exactly
`∀ a b c d : Nat, ∃ p n : Nat, p = a*d ∧ n = b*c`. The generated package
records exact original-AST equivalence and a real certificate proof. Runtime
verification does not silently upgrade conservative manifest-authority flags
or grant Stable membership.

An exact matching historical single-root flagship proof bundle can still be
translated directly without reconstructing a second ordinary root certificate:

```bash
python3 scripts/export_peano_lean.py bertrand_strict \
  --edition alpha \
  --proof-bundle research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json \
  --format compact \
  --package-dir /private/tmp/peano-lean-bertrand

python3 scripts/export_peano_lean.py lucas_theorem \
  --edition alpha \
  --proof-bundle research/arithmetic-library/artifacts/lucas-proof-bundle-v1.json \
  --format compact \
  --package-dir /private/tmp/peano-lean-lucas
```

The exporter first authenticates the named theorem's Alpha checked-use
authority, compares the bundle target directly with its exact original
first-order statement, and independently checks every constructive dependency
proof before generating Lean. No redundant full empty-context replay is
needed. Kummer's shared artifact has a conjunction of its two endpoints as
its root. Likewise, the **475-node Alpha-v19 residual artifact** ends at a
balanced conjunction of 40 exact theorem roots, the **545-node v19 campaign
artifact** ends at a balanced conjunction of 17 exact new roots, and the
**590-node v20 next-layer artifact** ends at a balanced conjunction of 12
exact roots, the **209-node v21 advanced-layer artifact** ends at a balanced
conjunction of 27 exact roots, and the **240-node v22 transport-layer
artifact** ends at a balanced conjunction of 17 exact roots, the
**617-node v23 milestone-closure artifact** closes its historical tranche,
the **203-node v24 research-layer artifact** contains its historical three
partial-frontier campaigns, and the **302-node v25 breakthrough-layer
artifact** advances all three without closing their stronger milestone
statements. None of
those synthetic conjunctions is itself the statement of an individually named
theorem. Therefore never pass a multi-root artifact as `--proof-bundle` for
an individual Kummer, residual, or new campaign endpoint: the exporter
correctly rejects the mismatched target. Use its authenticated named-theorem
path, a readable dependency strand, or a separately extracted exact matching
rooted sub-bundle.

The complete historical Alpha-v19/v20/v21/v22/v23/v24 and current Alpha-v25 proof
DAGs can instead be audited directly with the existing independently compiled
Lean verifier:

```bash
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v19-residual-proof-bundle-v1.json
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v20-next-layer-proof-bundle-v1.json
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v22-transport-layer-proof-bundle-v1.json
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v24-research-layer-proof-bundle-v1.json
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json
```

The historical v20 command independently returned
`ACCEPT ... nodes=590 root=589` for the frozen 14,775,673-byte artifact.
The historical v21 command independently returns
`ACCEPT ... nodes=209 root=208` for the frozen 1,005,317-byte artifact with
SHA-256 `65ecae7cb6b3e102790efa281451db3da5ab83868afcf9d57e6656f7a3eafda0`.
The historical v22 command independently returns
`ACCEPT ... nodes=240 root=239` for the frozen 1,099,541-byte artifact with
SHA-256 `95e5f8a3baef113721d748f9d7071864b4bf9511737a27a1272d2695428fb938`.
The historical v24 receipt independently binds the 738,923-byte research artifact
to 203 checked theorem-bundle nodes, root 202, and SHA-256
`627e39ed29b10db48bf37d5bef8750d48009a7524c822a7c5e7c83e96a8e9cf9`.
The current v25 receipt independently binds the 1,041,166-byte breakthrough
artifact to 302 checked theorem-bundle nodes, root 301, and SHA-256
`d4532076049be869e4e397d0fcee81b668bd3fd5c7d9173028bb1bdb80b9793a`.

An independently supplied bundle for a theorem outside Stable is identified
as external bundle evidence; it does not promote that theorem into Stable or
authorize publication.

Very large certificates remain mathematically large even when their public
theorem is short. The known quadratic-reciprocity certificate has hundreds of
dependency nodes, and compiling its generated Lean module may exceed the
standard bounded worker. The existing independent standalone bundle verifier
remains the fast audit route for that artifact; do not claim that a smaller
human-facing file makes the underlying Lean checking cost disappear.
The complete strict-Bertrand artifact is approximately **14.4 MB**; its
544 constructive dependency nodes can be verified directly by the independently
compiled bundle verifier. Add `--verify` to a generated Lean package only when
its explicit existing memory and wall-clock limits are appropriate.

Lean's `-M` option limits an internal allocator; it is **not an
operating-system resident-memory limit**. In particular, elaborating a
1.75 MB generated certificate can exceed 2.5 GB of actual resident memory even
when `-M 1536` is requested. Before starting **any** compiler, `--verify`
therefore checks every generated module against a conservative 2,048:1
source-to-memory allowance:

```text
maximum source bytes = floor(max-memory-mib × 1,048,576 / 2,048)
default 1,536 MiB allowance = 786,432 source bytes per module
```

An oversized certificate fails closed before Lake or Lean starts, including
before a package's smaller shared prelude is compiled. The allowance reduces
the risk from known-dangerous certificate sizes; it is deliberately **not**
claimed to be a universal operating-system RSS guarantee for all Lean inputs.
Large flagship packages can still be generated without `--verify`, and their
canonical constructive proof DAGs remain independently checked by the existing
compiled Lean bundle verifier. Any increased verifier budget is an explicit,
bounded user choice.

## Trust and resource boundaries

- The original Python Peano kernel checks the exact closed original goal.
- Lean independently reconstructs and checks the same constructive
  certificate or complete topological dependency bundle.
- The public theorem follows from the existing proved Lean checker-soundness
  theorem; the presentation aliases are unfolded and checked by Lean.
- No `sorry`, new project axiom, external-verifier status, hash, Python
  success flag, or compiler-trusting `native_decide` substitutes for a proof.
- The default path requires no Mathlib, downloads, additional model, network,
  theorem admission, publication, or training permission.
- Verification uses one Lean worker, an explicit internal Lean memory limit,
  a conservative prelaunch source-size guard, and the existing complete-
  process-group wall-clock policy. The source-size guard is not a universal
  host RSS limit. Larger bounds are explicit choices, never automatic.
- The Mathlib-free presentation includes genuinely Lean-proved bridges from
  Peano's witness-defined `Lt` to standard `<`, and from `Dvd` to standard
  `∣`. A Mathlib-specific predicate such as `Nat.Prime` still requires its own
  separately checked bridge and is never silently substituted.
- Constructive quadratic reciprocity keeps its exact disjunctive evidence;
  replacing it with a merely equivalent-looking classical statement is not a
  presentation-only change.
- Checked primitive Pythagorean forward construction does not imply its
  still-open inverse classification or unconditional Fermat exponent-four
  strict descent. Infinitude of primes one modulo four does not silently
  establish the separately open three-modulo-four prime goal.

The short theorem is the intended reading surface; the complete imported
certificate remains available whenever an independent auditor needs it.
