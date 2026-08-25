# Readable, independently checked Peano-to-Lean theorems

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
two-square classification. Current immutable **Alpha v19** additionally
closes its **84** remaining body-only obligations and adds **64** independently
checked Pythagorean, prime-two-square, linear-congruence, and one-modulo-four
prime results. All **1,737 enrolled statements now have checked-use
authority**: **432 unchanged Stable** theorems and **1,305 Alpha-only**
theorems, with no unchecked or pending rows. Its exact edition identity is
`905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7`.

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
balanced conjunction of 40 exact theorem roots, and the **545-node campaign
artifact** ends at a balanced conjunction of 17 exact new roots. None of
those synthetic conjunctions is itself the statement of an individually named
theorem. Therefore never pass a multi-root artifact as `--proof-bundle` for
an individual Kummer, residual, or new campaign endpoint: the exporter
correctly rejects the mismatched target. Use its authenticated named-theorem
path, a readable dependency strand, or a separately extracted exact matching
rooted sub-bundle.

Both complete Alpha-v19 proof DAGs can instead be audited directly with the
existing independently compiled Lean verifier:

```bash
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v19-residual-proof-bundle-v1.json
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json
```

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
