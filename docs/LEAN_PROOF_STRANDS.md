# Readable proof strands: from Peano arithmetic to Lean

A proof strand tells the complete mathematical story behind a theorem: its
axiomatic foundations, its named intermediate lemmas, their authored proof
steps, and the final root theorem. Peano Lab can expose that story either as a
small, safe browser preview or as an explicitly generated Lean package.

The two views have deliberately different authority. A preview reads the
authenticated release inventory and original Peano proof scripts. It does not
replay a proof, read a proof artifact, run Lean, or independently establish a
new theorem. An exported strand becomes an independently Lean-checked artifact
only when its generated modules are actually compiled successfully.

The commands below are implemented and tested in the local Peano driver. The
public faculty explorer now uses the same checked service through an isolated
same-origin PHP gateway, an owner-only shared-home mailbox outside
`public_html`, and a faculty-loopback SSH reverse tunnel. The Python
worker and Lean compiler still bind only to the operator's local machine; no
persistent daemon, private companion, or repository checkout runs on faculty
hosting. Publishing the proof website and starting the tunnel remain explicit
operator actions.

## Publish the complete interactive proof builder

From the repository root:

```bash
make deploy-proofs
make lean-public
```

The first command publishes every exact and definition-aware campaign explorer,
its shared selected-theorem controls, and the isolated PHP API gateway. Keep
the second command running while public visitors build proofs: it starts or
reuses the existing bounded local Lean worker and opens a remote-loopback-only
SSH tunnel to the faculty gateway.

Open the public theorem graph at
<https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/quadratic-reciprocity/explorer/defined/graph.html?target=PA000F>,
select a checked theorem, and choose **Build Lean proof**. Progress, compiler
verification, source/ZIP downloads, and genuinely self-contained Lean Live
handoff use the same evidence checks as the local browser. A separate terminal
can independently check the complete deployed path:

```bash
make lean-public-check
```

When the tunnel is stopped, the public gateway reports that the checked proof
worker is offline; it never substitutes an unverified proof.

## Build a proof directly from the theorem browser

From the repository root, start the combined static theorem browser and proof
service:

```bash
make lean-browser
```

Visit the exact theorem graph at
<http://127.0.0.1:8787/book/_static/pa-proof-explorer/graph.html?target=PA000F> or the
definition-aware graph at
<http://127.0.0.1:8787/book/_static/pa-proof-explorer/defined/graph.html?target=PA000F>.

1. Search for or select a checked theorem on the graph.
2. Choose **Build Lean proof** in the right-hand selected-theorem panel.
3. Follow actual dependency translation, module generation, and compiler
   verification through the progress display. Cancel at any time.
4. Download the generated Lean source or the complete independently checked
   module-and-manifest ZIP after a successful build.
5. When the entire strand has readable Lean proofs, choose **Open in Lean
   Live** to inspect and compile its exact self-contained source. Hydra uses
   Lean Live's exact unpadded Base64 compression format whenever it produces a
   shorter safe link; its reserved characters are canonically percent-escaped
   before the link is authenticated.

Campaign-scale jobs default to 1,024 named theorem nodes, 1 MiB of standalone
Lean source, and a 512 KiB fully escaped Lean Live URL. These node limits cover
every current Alpha-v22 dependency tree; the largest contains 557 theorems.
The service still runs just one independently bounded 1,024 MiB Lean worker,
and excessive source size, link size, verification time, or genuine proof
fallbacks never produce an unauthenticated Lean Live link.

Selecting a conservative definition does not start a theorem proof. Alpha-only
nodes explicitly use the checked Alpha edition; Stable nodes remain Stable.
Every offered Lean Live proof has already been independently compiled locally
and contains every named prerequisite in dependency order. It has **no import
statements whatsoever**: no Mathlib, no `PeanoLab` module, no private checker,
and no separate Lean tactic-module import. Exact-source decoding,
the recorded source hash, zero fallback nodes, zero external imports, and the
absence of `sorry` are all checked before the link appears. Statement-only
legacy scaffolds containing placeholders never receive a Lean Live link.
Complete packages, including any honest remaining checked certificate
fallbacks, remain available through the ZIP export.

Both links intentionally start with the small three-theorem `add_comm` strand,
not a heavyweight quadratic-reciprocity root. Selecting a theorem does not
start proof replay; only the explicit build button starts the single bounded
Lean worker.

The six modern constructive campaign graphs use the identical selector. For
example, the checked Alpha-v19 theorem `pythagorean_double_product` has just
nine named prerequisite nodes and can be selected at
<http://127.0.0.1:8787/book/_static/constructive-frontier-explorer/pythagorean-fermat-four/explorer/defined/graph.html?target=PF0000>.
Its entire nine-theorem strand now reconstructs as ordinary readable Lean
proofs, with no certificate fallback and a genuinely self-contained Lean Live
source. It keeps its explicit **Alpha** badge; exporting it never promotes the
theorem into the 432-entry Stable edition.

To reproduce the complete real HTTP, independent Lean, standalone-source, Lean
Live, and generated-package checks with one command:

```bash
make lean-browser-check
```

The checker reuses an existing local service or starts and cleans up a
temporary loopback-only service automatically.

## Start with an interactive proof

Inside the Peano Lab terminal:

```text
pa proof zero_add
pa proof add_comm
pa proof prime_mod_inverse
pa proof prime_unbounded
```

The same bounded view is available through:

```text
pa lean strand prime_unbounded
```

A typical number-theoretic root has the readable statement:

```lean
theorem prime_unbounded :
  ∀ n : Nat, ∃ p : Nat, Lt n p ∧ Prime p
```

The interface uses Lean's actual mathematical symbols when rendering this
statement. `Lt` and `Prime` name exact constructive Peano formulas; they are
neither additional axioms nor unproved substitutions for Mathlib predicates.
The same presentation can use all 40 reviewed conservative arithmetic
definitions whenever their exact expansions match the original formula.

Each proof-strand card shows:

- The readable theorem and its mathematical summary.
- The Stable or Alpha release, exact evidence classification, and checked-use
  authority.
- The original declaration source and every displayed direct dependency.
- The size of the authenticated transitive dependency closure.
- The original root proof script, numbered and labeled as **Peano tactics**.
- A bounded topological outline of foundation and intermediate lemmas.
- The exact terminal command for generating and verifying a complete strand.
- Explicit `NOT RUN` notices for fresh Peano replay and independent Lean
  compilation.

Original Peano commands are useful proof explanations, but they are not
executable Lean tactics. Translating a supported command into a checked Lean
proof step is a separate, explicit export operation.

## Review large Alpha theorems without a system crash

Alpha v22 currently has 1,890 checked-use theorems, including the following
independently established mathematical roots:

```text
pa proof alpha quadratic_reciprocity_combined
pa proof alpha lucas_theorem
pa proof alpha bertrand_strict
pa proof alpha four_square_lagrange
pa proof alpha doubled_square_plus_one_nonzero
pa proof alpha linear_congruence_solvable_iff_gcd_divides
pa proof alpha beta_horner_eval_exists
pa proof alpha beta_dot_product_exists_unique
pa proof alpha iterated_bertrand_prime_chain_exists
pa proof alpha continued_fraction_positive_exists
pa proof alpha beta_matrix_product_exists
pa proof alpha beta_signed_matrix_product_exists
pa proof alpha euclidean_two_step_halving
pa proof alpha euclidean_gcd_execution_linear_bound
pa proof alpha binary_modular_exponentiation_result_exists_unique
pa proof alpha binary_length_exists_unique
pa proof alpha euclidean_execution_terminal_identified
pa proof alpha euclidean_anchored_execution_linear_bound
pa proof alpha binary_modular_execution_power_correct
pa proof alpha binary_modular_execution_result_exists_unique
```

For a root with a very large prerequisite graph, the browser still shows the
root statement, source, release evidence, original authored proof, and named
direct dependencies. It stops traversing the graph after 128 authenticated
theorem entries and reports that the remaining strand was not expanded.

This protection is important. Quadratic reciprocity has a 557-theorem proof
graph, strict Bertrand has 544, the all-natural two-square root has 517, and
four-square existence has 390. An ordinary recursive proof replay can consume
far more memory than the readable root statement suggests. Browsing a strand
must never trigger that replay merely to display its proof.

The complete browser response is capped at 15 KiB. Root scripts and direct
dependency listings are visibly truncated when they exceed the review budget;
omitted lines are not silently presented as nonexistent. Historical Alpha
entries with only `body_checked` evidence remain inadmissible unless the exact
current release promotes them with closed checked-use evidence.

## Export the complete dependency-ordered strand

From the arithmetic repository root:

```bash
python3 scripts/export_peano_lean.py add_comm \
  --format strand \
  --package-dir /private/tmp/peano-proof-strands/add_comm \
  --verify

python3 scripts/export_peano_lean.py prime_unbounded \
  --format strand \
  --package-dir /private/tmp/peano-proof-strands/prime_unbounded \
  --verify
```

An Alpha theorem always requires its explicit edition:

```bash
python3 scripts/export_peano_lean.py lucas_theorem \
  --edition alpha \
  --format strand \
  --package-dir /private/tmp/peano-proof-strands/lucas_theorem \
  --verify
```

The generated strand is organized from axioms and prerequisite lemmas toward
the requested root. Each local theorem is reconstructed from its own authored
body and earlier named dependencies. When a particular tactic cannot yet be
translated directly, the export records that fact and can use its independently
checked local certificate; a fallback is never disguised as a readable Lean
tactic proof.

To require fully readable reconstruction with no local certificate fallbacks,
add:

```bash
--strict-readable
```

Unsupported proof steps then fail closed instead of generating a misleading
partial proof. Neither mode inserts `sorry`, adds a new axiom, grants a solver
special kernel authority, or silently changes the original theorem.

## Inspect bounded Lean chunks and transparent local repairs

Larger strands are automatically split into dependency-topological Lean
modules of at most 192 KiB each. Together, the shared prelude and first proof
module expose all 40 reviewed, exactly expanded conservative arithmetic
definitions. Each successive proof chunk imports the preceding chunk before
introducing its own named lemmas:

```text
PeanoLab/Presentation.lean
PeanoLab/Generated/<theorem>_<identity>/Chunks/C000.lean
PeanoLab/Generated/<theorem>_<identity>/Chunks/C001.lean
PeanoLab/Generated/<theorem>_<identity>/Strand.lean
```

Small strands do not need intermediate `Chunks` modules. The manifest records
the exact SHA-256 digest and byte count of every generated file; each theorem
node additionally records its generated module, repository-relative Lean path,
and precise start and end source lines. The same module-by-module source map
lets a reviewer distinguish readable Lean proof steps from an honestly labeled
dependency-curried, independently checked local certificate fallback.

To exercise tighter segmentation and explicitly bound automatic local repairs:

```bash
python3 scripts/export_peano_lean.py add_comm \
  --format strand \
  --package-dir /private/tmp/peano-proof-strands/chunk-smoke \
  --max-chunk-kib 13 \
  --max-proof-repairs 16 \
  --verify
```

If Lean rejects a candidate readable proof, a repair can replace only that
specific local theorem body with its kernel-checked certificate and retry the
bounded compilation. The fallback remains explicit in the source and manifest.
Repairs never assert that a failed candidate succeeded, replay the entire
recursive theorem, or run multiple Lean workers. `--max-proof-repairs 0`
disables this recovery; `--strict-readable` forbids every certificate fallback.

## Measured independent verification: unboundedly many primes

The following bounded command has independently compiled the complete
`prime_unbounded` dependency strand with the separately built Lean checker:

```bash
python3 scripts/export_peano_lean.py prime_unbounded \
  --format strand \
  --package-dir /private/tmp/peano-proof-strands/prime_unbounded-verified \
  --max-chunk-kib 64 \
  --max-memory-mib 1024 \
  --max-verify-seconds 240 \
  --max-proof-repairs 16 \
  --verify
```

The successful, compiler-audited package contained:

- 57 named theorem nodes, 110 prerequisite edges, and 1,238 original authored
  Peano tactic decisions.
- 48 independently accepted readable Lean theorem proofs and 9 explicitly
  labeled, dependency-relative checked-certificate fallbacks.
- Three dependency-ordered proof chunks below 64 KiB each, plus the shared
  notation prelude and the final compiled root-audit module.
- The standard certificate-backed semantic axiom footprint: `propext`,
  `Classical.choice`, and `Quot.sound`; neither `sorryAx` nor
  `Lean.trustCompiler` is accepted.

All 57 local bodies initially produced readable proof *candidates*. This does
not mean that Lean accepted 57 readable proofs: the final checked result
contains 48 readable proofs and 9 transparent local fallbacks. In particular,
`prime_unbounded` itself is one of those checked fallbacks. Its root theorem
was independently accepted by Lean through the verified local certificate;
claiming that the root has a fully readable native Lean tactic proof would be
incorrect.

## Choose metadata-only or bounded export modes

For a terminal-only outline that should not replay proofs or run Lean:

```bash
python3 scripts/export_peano_lean.py prime_unbounded --format outline

python3 scripts/export_peano_lean.py quadratic_reciprocity_combined \
  --edition alpha --format outline
```

Full strand generation has explicit, reviewed limits:

```text
--max-strand-nodes   2048
--max-strand-edges   8192
--max-strand-depth    128
--max-proof-steps    4096
--max-chunk-kib       192
--max-proof-repairs    16
```

These are ceilings, not claims that every theorem can be translated or checked
within available memory. Increasing a limit requires an explicit user choice.
The normal Lean verifier still uses one compiler worker, its existing
wall-clock and allocator settings, complete-process-group cleanup, and the
prelaunch source-to-memory guard described in
[`LEAN_CERTIFIED_PRESENTATION.md`](LEAN_CERTIFIED_PRESENTATION.md).

Lean's `-M` option is not an operating-system resident-memory guarantee. Large
flagship strands may therefore need a separately reviewed machine or the
existing independently compiled proof-bundle verifier; a browser preview is
never an excuse to start a dangerous local compiler.

## Read the trust boundary correctly

The unchanged Peano kernel remains the only authority for Peano theorem
acceptance. The independent Lean checker establishes only the specific Lean
modules it actually verifies. A source path, dependency hash, release label,
proof outline, authored script, or generated manifest is useful provenance but
is not itself a proof.

Stable remains a 432-theorem public release. Alpha v22 contains additional
checked-use theorems, but viewing or exporting an Alpha strand does not promote
it into Stable. No strand export authorizes publication, model training,
external deployment, protected FINAL evaluation, or any other release action.
