# Formal artifacts — one statement, four foundations

These directories prove the *same* small statements in four proof assistants, so you can
**see** how different foundations do the same job. The pedagogical payload is the comparison,
not the theorems.

| Prover | Foundation | Proof style | Standard library | Status here |
|--------|-----------|-------------|------------------|-------------|
| **[Lean 4](lean/)** | Calculus of Inductive Constructions (CIC) | tactic + term | Mathlib | ✅ kernel-checked locally, `sorry`-free, **no axioms** |
| **[Agda](agda/)** | Martin-Löf Type Theory (MLTT) | dependently-typed functional | built-ins only (here) | ✅ type-checks with **Agda 2.8.0** (statements 1–4) |
| **[Rocq](rocq/)** (ex-Coq) | Calculus of Inductive Constructions (CIC) | tactic (Ltac) | Rocq stdlib · MathComp | ✅ compiled with **Rocq 9.2** (statements 1–5, incl. √2) |
| **[Mizar](mizar/)** | Tarski–Grothendieck **set** theory + classical FOL | declarative (Jaśkowski) | Mizar Mathematical Library | 📝 illustrative of style (not installed here) |

The three type-theoretic systems (Lean, Agda, Rocq) share **propositions-as-types**: a proof of a
proposition *is* a program of the corresponding type. Mizar is the deliberate contrast — a proof is a
declarative argument in classical set theory, not a term.

## The Rosetta stone — Statement 1 (the S combinator)

The propositional tautology `(p → q → r) → (p → q) → p → r` and the combinator `S f g x = f x (g x)`
are the same object under Curry–Howard. In the three type theories, **the proof literally is the
program**:

**Lean 4**
```lean
theorem s_combinator {p q r : Prop} (f : p → q → r) (g : p → q) (x : p) : r := f x (g x)
```
**Agda**
```agda
S-comb : {P Q R : Set} → (P → Q → R) → (P → Q) → P → R
S-comb f g x = f x (g x)
```
**Rocq**
```coq
Definition S_comb {P Q R : Prop} (f : P -> Q -> R) (g : P -> Q) (x : P) : R := f x (g x).
```
**Mizar** (declarative — the proof is an argument, not a term)
```
assume A1: P implies Q implies R;  assume A2: P implies Q;  assume A3: P;
thus R by A1, A3, A2;
```

## Statements 2 & 3 — a definitional-equality surprise

`Nat`/`nat` addition is defined by recursion on **one** argument, and *which* argument differs by
system — so *which* half of `n + 0 = n` / `0 + n = n` is true "for free" (`rfl`/`reflexivity`/`refl`)
flips between them:

| | recurses on | free by definition | needs induction |
|---|---|---|---|
| **Lean** `Nat` | 2nd arg | `n + 0 = n` | `0 + n = n` |
| **Agda / Rocq** `nat` | 1st arg | `0 + n = n` | `n + 0 = n` |

Commutativity `n + m = m + n` (Statement 3) then follows by induction in each — see the source files.
This tiny asymmetry is one of the most useful things a newcomer can internalize early.

## Statement 4 — a tiny expression evaluator (EML in miniature)

A first taste of Lecture 6's EML idea: a syntax tree with a denotation, plus a theorem relating syntax
to value. The grammar is `1`/`+`/`·` over ℕ with an `eval` denotation; we prove `eval (1+1) = 2` (by
`rfl`), that `eval` is syntax-directed on `add`, and that swapping summands preserves the value
(transporting `add_comm` through the denotation). In the real
[EML project](https://github.com/nasqret/eml-formalization) the leaves are complex constants and the
denotation `eval?` is `Option ℂ`-valued — but the shape is exactly this.

Verified in Lean (`sorry`-free, no axioms); authored in Agda and Rocq. This is the artifact that most
directly foreshadows the capstone.

## Statement 5 — $\sqrt 2$ is irrational (the "real theorem")

The one genuine piece of mathematics in the set, and the payoff for Lecture 5. We prove — **in Lean 4
core, with no Mathlib** — that there is no *positive* natural solution to $p^2 = 2q^2$:

```lean
theorem no_sqrt2 : ∀ p q : Nat, p * p = 2 * (q * q) → q = 0
theorem no_pos_sqrt2 (p q : Nat) (hq : q ≠ 0) : p * p ≠ 2 * (q * q)
```

The proof is **Fermat's infinite descent**, driven by one lemma — a square is even iff its root is
(`even_sq_iff`) — so $p$ even $\Rightarrow$ $q$ even $\Rightarrow$ a strictly smaller solution, and
strong induction closes it. It lives in [`lean/Artifacts/Sqrt2.lean`](lean/Artifacts/Sqrt2.lean), builds
in the fast default `lake build`, and is `sorry`-free — `#print axioms no_sqrt2` reports only `propext`
and `Quot.sound` (Lean's two standard kernel axioms; no `Classical`, no `sorryAx`).

√2 is **machine-verified in two provers**: the Lean 4 core proof above, and a Rocq 9.2 version in
[`rocq/Sqrt2.v`](rocq/Sqrt2.v) (`Sqrt2Descent.no_sqrt2`), where `nia` discharges the nonlinear algebra so
the descent is tighter. Same theorem, same infinite-descent idea, CIC both times — the parity lemma and
the strong-induction skeleton are the only prover-specific parts. A third proof in **Agda** (MLTT) is
left as future work: without agda-stdlib registered here, a from-scratch descent (well-founded recursion +
parity + arithmetic, all by hand) is disproportionately long — statements 1–4 already exercise Agda's
MLTT, and the two CIC proofs establish √2 itself.

## Reproduce

```bash
# Lean (verified locally):
cd lean && lake build            # → Built Artifacts; #print axioms shows none

# Agda (if installed):
cd agda && agda Artifacts.agda

# Rocq (verified with Rocq 9.2):
cd rocq && coqc Artifacts.v && coqc Sqrt2.v      # or: rocq compile Artifacts.v Sqrt2.v

# Mizar: see mizar/artifact.miz — illustrative; run under a Mizar install against the MML.
```

Each artifact maps back to a lecture: Statement 1 → Lectures 1 & 3 (Curry–Howard); Statements 2–3 →
Lectures 2 & 4 (Peano, induction). More statements (√2 irrational, an EML-flavoured evaluation) grow
here as the course proceeds.

## Peano Lab certificate-size experiment

[`triangular-even-readable.pa`](triangular-even-readable.pa) is an executable Peano Lab
surface proof of `forall n. exists x. n * (n + 1) = 2 * x`. It uses `suffices` to state
the final normalization step and `have` to prove the stronger induction invariant
`n * n + n = 2 * x` first. Three equality leaves use `compact_arith`, with the induction
hypothesis named explicitly at the successor leaf. The invariant, induction, witnesses, hypothesis
use, and final bridge remain visible while the finalized replay is byte-identical to the retained
180-node certificate. The historical version with two generic `ring` calls finalized to 30,030
proof-tree nodes.

[`triangular-even-180.certificate.txt`](triangular-even-180.certificate.txt) is the canonical
cut-normal certificate for the current best-found proof of
`forall n. exists x. n * (n + 1) = 2 * x`. It has 180 proof-tree nodes and is independently checked
against that original statement. The deliberately retained
[`triangular-even-373.certificate.txt`](triangular-even-373.certificate.txt) records an earlier proof
shape for comparison; smaller here means less certificate scaffolding, not a stronger theorem.

Rebuild and check the 180-node result with:

```bash
cd ..
python3 scripts/minimize_parity_certificate.py
cd peano-lab/py && python3 -m pytest \
  tests/test_parity_superoptimization.py tests/test_readable_parity_artifact.py -q
```

The result is a verified upper bound, not a claimed proof of global minimality. The hand constructor
and the independently replayed browser-tactic script now reach the same canonical ordinary proof;
neither adds a trusted arithmetic shortcut.

## First trained-policy result

[`peano-policy/qwen3-1.7b-wmi-smoke-summary.json`](peano-policy/qwen3-1.7b-wmi-smoke-summary.json)
records the exact hashes and kernel-judged outcomes of the first WMI Qwen3-1.7B LoRA smoke. The
four-goal held-out run proved 0/4 at pass@4, and the harder triangular-number parity request proved
0/1 at pass@16. A fresh direct-witness theorem absent as an exact formula from train, validation,
and test succeeded once in eight samples.

The immutable source reports are published beside that index:

- [`qwen3-1.7b-wmi-training-manifest.json`](peano-policy/qwen3-1.7b-wmi-training-manifest.json)
  is the complete training manifest;
- [`qwen3-1.7b-wmi-heldout-k4.json`](peano-policy/qwen3-1.7b-wmi-heldout-k4.json) is the complete
  four-goal evaluator report; and
- [`qwen3-1.7b-wmi-parity-k16.json`](peano-policy/qwen3-1.7b-wmi-parity-k16.json) and
  [`qwen3-1.7b-wmi-easy-witness-k8.json`](peano-policy/qwen3-1.7b-wmi-easy-witness-k8.json) are the
  complete arbitrary-theorem reports.

[`peano-policy/qwen3-1.7b-wmi-easy-witness.pa`](peano-policy/qwen3-1.7b-wmi-easy-witness.pa) is that
ordinary exported proof. It is not trusted model output: repository tests replay it under the exact
`model-v1` authority and require another independent original-target kernel check. The artifact
therefore records a limited in-distribution success, not a broad PA prover; attribution to
fine-tuning awaits the pretrained-base baseline.

## Peano foundational arithmetic snapshot

[`peano-library/`](peano-library/) is the deterministic snapshot of all 432
checked Peano library entries. Its internal snapshot-v3 schema contains
statement/script/certificate hashes, exact structural, depth, distinct-object,
and Cut metrics, an ordered root digest, and the dependency DAG in Mermaid
form. The current snapshot totals 1,982,360 structural occurrences, 468,010
distinct proof objects, and 57,692 structural Cut occurrences across 373
Cut-bearing entries, with 1,185 dependency edges and ordered root
`4d02dc439d53533e8992a471b26ee34059fb6001f822041e42c56b2cc0a7a079`.
`fundamental_theorem_of_arithmetic` is
largest at 73,767 occurrences and reaches depth 99; its shared in-memory graph
contains 8,701 distinct proof objects.
The 137-entry quadratic-residue foundation adds parity and modulo-four algebra,
constructive residue decision, finite folds, factorial and power algebra,
modular units, small-modulus classifications, sign and half-range bridges,
β-prefix swap/reindex, constructive finite pigeonhole, replacement balance,
and exact swap-last product invariance. It is a checked campaign checkpoint,
not yet a proof of quadratic reciprocity.
The separate unregistered campaign sources now contain a dependency-curried
kernel-checked body for the exact combined law, documented in the Jupyter Book.
It is intentionally absent from this 432-theorem artifact until its recursive
WMI closure, mutation, capacity, and receipt-pinned admission gates pass.
The 23-entry selective M5 tranche is present at indices 409--431. It exposes
the unrestricted generalized-CRT solvability criterion, relational-LCM
solution classification, the correct zero/nonzero canonical boundary, and the
raw-input solution-or-obstruction endpoint. Six reviewed M5 convenience rows
remain outside the public snapshot.
The latest checked tranches add the full additive/multiplicative compatibility
layer for balanced congruence, the five expanded decoded-value theorems from
`beta_modulus_nonzero` through `beta_at_exists_unique`, and the directed
remainder/congruence bridges. Bounded representative uniqueness and the
reverse β bridge now make expanded β decoding equivalent to a bound plus
balanced congruence. The subtraction-free binary CRT tranche also contains
the two modular Bézout projections, predecessor cancellation, constructive
binary CRT, its bounded-residue form, and a conditional two-position β-code
constructor. The newest tranche proves β-modulus coprimality when the ordered
index gap divides `c`, applies that fact to the β-pair constructor, and
constructs a nonzero `c` divisible by every positive natural through a
fixed bound. The newest seven records prove bounded-prefix pairwise
coprimality, coprime-product closure, congruence descent from an accumulated
product modulus, and one invariant-preserving binary CRT extension. The
newest six records advance the accumulated-product and decoded-congruence
invariants together and fold them through every bounded prefix of values
already decoded from a supplied `BetaAt` code. Later checked layers provide
genuine finite-prefix recoding, exact prefix-product traces,
greatest-prime-divisor descent, canonical factorization, and the native
β-coded FTA. The snapshot does not claim false unconditional pairwise
β-modulus coprimality, raw-code uniqueness, or a primitive list theorem.
Rebuild or verify it with
`python3 scripts/build_peano_library_snapshot.py [--check]`.

The snapshot is evidence about replayed certificates, not a theorem database
trusted by the kernel. The broader checked/planned/blocked research graph lives
in `research/arithmetic-library/catalog.json`; it currently has 433 nodes: 23
`checked_existing`, 409 `checked_m20`, no planned entries, and one
language-blocked conventional interface.

## Quadratic-reciprocity reading artifact

[`quadratic-reciprocity/pa00fg-gauss-eisenstein-data.tex`](quadratic-reciprocity/pa00fg-gauss-eisenstein-data.tex)
and its compiled
[`PDF`](quadratic-reciprocity/pa00fg-gauss-eisenstein-data.pdf) give a
standalone standard-mathematical restatement of Proof Explorer theorem
`PA00FG`, `distinct_odd_primes_gauss_eisenstein_data_exists`. The document
keeps the formal status visible: the native tactic body is checked relative
to its declared dependencies, but the theorem is not yet a publicly admitted
closed certificate. The canonical interactive source remains the Proof
Explorer page at
`book/_static/pa-proof-explorer/tag/PA00FG.html`.

## Fundamental theorem of arithmetic companion

[`lean-fta/`](lean-fta/) is a separate Lean 4.23.0 + Mathlib artifact for the
full natural-number Fundamental Theorem of Arithmetic. It proves that every
nonzero natural has a finite list of prime factors and that every other such
list is a permutation of the canonical one. This is existence plus uniqueness
up to factor order, including the empty factorization of one.

The project pins Mathlib commit
`37df177aaa770670452312393d4e84aaad56e7b6`. Its verifier rejects `sorryAx`
and requires the exact declared axiom footprint `propext`,
`Classical.choice`, and `Quot.sound`. It is an independent mathematical
cross-check and is never imported as a Peano Lab axiom.

```bash
cd lean-fta
lake update
lake exe cache get
lake build
cd ../..
python3 scripts/verify_lean_fta.py
```

## Public modular-arithmetic catalog

[`peano-library/mod5-source-validation-report.json`](peano-library/mod5-source-validation-report.json)
is the unaltered validation report for the 26 theorem specifications imported into Peano Lab's
public checked catalog. It records source catalog hash
`91c88c1f3311cc0dc540671b169c270758ff6211e77716ed07bd3dd4f55c8380`, deterministic replay,
empty-context kernel acceptance, certificate hashes, and a 21,515-node/depth-66 maximum. The source
revision and exact MIT notice are preserved in [`peano-library/NOTICE.md`](peano-library/NOTICE.md).

The report predates the public integration and therefore marks three certificates as exceeding the
then-current 4,096-node `use` ceiling. The public-catalog integration raised only that untrusted
resource limit to 32,768 and changed no kernel rule. A later separately reviewed milestone added
self-contained Cut sharing; the source report remains immutable legacy provenance. Repository
regressions reproduce its cut-free hashes where supported, separately replay the current shared
certificates twice, reject a mutated capstone target, and exercise the short live
`use`/`apply`/`exact` route.

The reconciled runtime keeps all 26 source records for provenance. Fourteen are
identical to independently developed M20 records, so a guarded union exposes
those once and adds the twelve genuinely new modular capstones. That initial
reconciliation produced a historical 63-theorem release; the current generated
snapshot is its 189-theorem successor. Incompatible same-name records fail
closed.

## Peano Alpha v2 and Stable channel artifacts (2026-08-09)

The current Peano arithmetic release model has two explicit editions:

- **Stable** is unchanged at 432 theorems, 1,185 declared direct dependency
  edges, and 22 layers. Its checked snapshot remains
  [`peano-library/catalog-v1.json`](peano-library/catalog-v1.json).
- **Alpha v1** remains the sealed 885-theorem parent edition.
- **Alpha v2** is the current cumulative building library at 902 theorems,
  2,674 declared direct dependency edges, and 45 layers, including 470
  Alpha-only rows. It preserves all 885 v1 entries and appends the 17 K3C
  rows at indices 885--901.

[`peano-library/channels-v2.json`](peano-library/channels-v2.json) is the
current deterministic channel pointer. It binds the unchanged Stable snapshot
and the additive Alpha v2 catalog, metrics, and dependency graph under
[`peano-library/alpha/`](peano-library/alpha/). The v1 pointer
[`peano-library/channels.json`](peano-library/channels.json) and its Alpha v1
artifacts remain sealed parents; v2 does not rewrite them.

The exact Alpha-v2 artifact SHA-256 values are:

- catalog: `90ac4942df043e59ade7a62a87627ef3b29d9b1d7d251c8fa6aadefe77590bd7`;
- metrics: `85907aea9e6fece33c8f4d0d40d167945f3118190654a32423dc815df8fc69eb`;
- reduced graph: `01ca3e6b58e55cfefd4a0df3f8ce229f5382c26a02f4960ceb7773205c9177a3`;
  and
- channel pointer: `c2af6774ea7c787532d79a5f8fd41087ae5f31a0e828e25571adaed2853aa968`.

Alpha v2 evidence is exactly 432 `stable_closed`, 138 `alpha_closed`, 331
`body_checked`, and one `pending_layered_closure`. Only the first two statuses,
570 rows total, are checked-use facts; 332 rows still lack whole-Alpha-v2
empty-context closure. Runtime selection and fail-closed replay are provided
by `peano_lab.library.editions_v2` through `edition`, `entry`, and `replay`,
with Stable as the default. All 17 K3C rows are `body_checked` and fail closed;
their repeated isolated WMI closure receipt is pending.

The v1 artifact happens to place all 432 Stable rows first. This is a sealed
initial condition, not a requirement that future Stable releases be prefixes
of Alpha. Promotion creates a new channel version, preserves Alpha's enrollment
origin/provenance, and checks Stable as an exact keyed subset with its own
append-only dependency-topological order.

Rebuild or check the current structural channel artifacts with:

```bash
python3 scripts/build_peano_library_channels_v2.py
python3 scripts/build_peano_library_channels_v2.py --check
python3 scripts/verify_peano_library_channels_v2.py
make peano-library-alpha-v2-check
```

These gates replay the seventeen dependency-curried K3C bodies but do not
replace their missing empty-context closure. WMI is down for the
weekend, so the K3C receipt, the 332 closures needed for a whole-Alpha-v2
promotion, and any new batch-promotion receipt remain pending. A smaller
dependency-closed batch does not wait for unrelated Alpha rows. The 717
reachability-redundant direct links reported in Alpha v2 metrics require
review, but that analysis concerns graph reachability/display: it neither
proves that a tactic body can discard an edge nor claims proof-semantic or
global dependency minimality. Earlier artifact prose using “private” or
“unregistered” is historical; K3B is now Alpha-only with `alpha_closed`
evidence, while K3C is Alpha-only with `body_checked` evidence. Neither is
Stable unless separately promoted.

## Peano Alpha v3 — Bertrand round 1 (2026-08-09)

Alpha v3 is the current additive building channel. It preserves the complete
902-row Alpha v2 ledger and appends exactly 21 first-round Bertrand campaign
specifications at indices 902--922. Stable remains byte-for-byte unchanged at
432 rows, and the sealed Alpha v1/v2 families remain immutable parents.

Current topology and evidence:

- 923 theorem specifications, 2,730 declared direct edges, and 45 layers;
- 432 Stable rows and 491 Alpha-only rows;
- 432 `stable_closed`, 138 `alpha_closed`, 352 `body_checked`, and one
  `pending_layered_closure` row;
- 570 checked-use rows; every new Bertrand row fails closed because it has
  body evidence only.

The deterministic pointer is
[`peano-library/channels-v3.json`](peano-library/channels-v3.json). Its exact
artifact SHA-256 values are:

- catalog: `1cd6b31379737efb3d889318e1c40beffcc14f77432a1b18cb74e80a5d29d199`;
- metrics: `50f5a2dab17fffa6b2ad0e936138bc197297caf066218e4054f8bc8b0e5ccd73`;
- reduced graph: `180ff8ddeccc9fafbc3607aa10b0587cbe2144cf4943621df52c2da5f26dbec7`;
  and
- channel pointer: `cd1618b8056abd22348dfac70d8a1686eecd5c6f875319c803d487c414f656ab`.

The ordered-enrollment root is
`4507736cde37301ecf3369540d6cc686de860b07b101f2afb60f850f86aeebd4`,
and the full edition identity is
`e20eefac839fb2bcd3e696989c091a5f6837de04824f94e1073723851a471a2f`.
The 21 appended rows cover quantitative order, power growth, constructive
prime-interval search, and bounded power valuations. The verifier replays
their dependency-curried bodies and cross-binds exact source, test, RFC,
statement, dependency, and parent bytes. It does not fabricate an
empty-context closure receipt.

Rebuild or verify this channel with:

```bash
python3 scripts/build_peano_library_channels_v3.py
python3 scripts/build_peano_library_channels_v3.py --check
python3 scripts/verify_peano_library_channels_v3.py
make peano-library-alpha-v3-check
```

The exact two-fresh-process cold-closure receipt for the 21 additions remains
pending. Until it passes, the additions cannot become `alpha_closed`, enter
checked use, or be considered for Stable promotion. Later valuation-law and
integer-envelope candidates are not part of these v3 artifacts.

## Peano Alpha v4 — Bertrand round 2 (2026-08-09)

Alpha v4 is the additive Round-2 building channel. It preserves all 923 Alpha
v3 rows and appends exactly 42 specifications at indices 923--964, ordered as
6 valuation laws, 11 valuation-multiplication laws, 5 integer-envelope laws,
9 ceiling/floor-square relations, 4 floor-square totality laws, and 7
quotient-budget laws. All v1/v2/v3 artifacts remain immutable, and Stable is
unchanged at 432 rows.

Current topology and evidence:

- 965 theorem specifications, 2,891 declared direct edges, and 45 layers;
- 432 Stable rows and 533 Alpha-only rows;
- 432 `stable_closed`, 138 `alpha_closed`, 394 `body_checked`, and one
  `pending_layered_closure` row;
- 570 checked-use rows; all 42 additions fail closed with null proof tags and
  null empty-context closure evidence.

The deterministic pointer is
[`peano-library/channels-v4.json`](peano-library/channels-v4.json). Its exact
artifact SHA-256 values are:

- catalog: `16e2b99de69487e7439521b25ee070b208d6a7436df48f60801d5628a3678f1a`;
- metrics: `bec61a932dbcf92715dcaac7440687e7310b8f380f5578746999c3007e1d6dac`;
- reduced graph: `9dc4c9531418b3de3def3c827a6b5fac54b12f78661d5a6860c84c08f748d28c`;
  and
- channel pointer: `cf3cdc6ead4d616b15bcf28b84fca586bc5df84b30125c807fb36a74985bdb76`.

The ordered-enrollment root is
`e4c83174c1800c135d0fe9ac03b5cdfcc5f11e5517f871b3f198586973a20c31`,
and the full edition identity is
`e0324009614f755f2251a5b27d29587b0c43015385a78d567b328776b92239a5`.
Each appended row cross-binds its exact source, executable test, campaign RFC,
and sealed Alpha-v3 parent catalog bytes. The verifier independently replays
all 42 dependency-curried bodies; this does not upgrade them to checked use.

Rebuild or verify this channel with:

```bash
python3 scripts/build_peano_library_channels_v4.py
python3 scripts/build_peano_library_channels_v4.py --check
python3 scripts/verify_peano_library_channels_v4.py
make peano-library-alpha-v4-check
```

## Peano Alpha v5 — factorial valuations (2026-08-09)

Alpha v5 is the additive `FactorialVal` building channel. It preserves the
exact 965-row Alpha-v4 ledger and appends seven specifications at indices
965--971: factorial nonvanishing, valuation of one, general `FactorialVal`
existence and functionality, and the prime-specific zero, successor, and
successor-inversion laws. Alpha v4 and all earlier artifact families remain
immutable; Stable is unchanged at 432 rows.

Current topology and evidence:

- 972 theorem specifications, 2,912 declared direct edges, and 45 layers;
- 432 Stable rows and 540 Alpha-only rows;
- 432 `stable_closed`, 138 `alpha_closed`, 401 `body_checked`, and one
  `pending_layered_closure` row;
- 570 checked-use rows; all seven additions fail closed with null proof tags
  and null empty-context closure evidence.

The deterministic pointer is
[`peano-library/channels-v5.json`](peano-library/channels-v5.json). Its exact
artifact SHA-256 values are:

- catalog: `94efc0f7022f31677619e842f7d6f1d0d0f8959efc54cd64cf346c3b5e8c4892`;
- metrics: `b560373c8cb4879f47e46083d5b9925cd29ebee1af4856cfc93e74017555acc2`;
- reduced graph: `4e8f1ea73b3ecfd51cf80d216dfc9171dabbe12f38d9c8392185ea1c610112ab`;
  and
- channel pointer: `946682733744d6969e89059df9165cc2782510101d4ee43a6a861aa7570a3f31`.

The ordered-enrollment root is
`46e1a08c6bc18bbc057aa7541420580b43aec75d5f30af500ba3ce12bec09473`,
the ordered-specification root is
`4592f0abba7b9f592d4f94780ced57c3e7e0b935444155f76276f1fd2b4d8ae4`,
and the full edition identity is
`bccf7d8fc01dbcd1cd2efd9d5d8e5189d80b79cfb7e5e30df999d270a9fd13af`.
The membership, evidence, and channel-pointer roots are respectively
`b3b71470fd6519b227e2353b818935f673a9d50dab6d59474f0f5f241ee20277`,
`a36ce30e7f95cde8fcb8bf73413d46a0b851eb52694387ba1fcc7327a08d4abb`,
and
`fa8cc554a6aa8eeab1aa396cbfc4f8019d16fa97d91aa09daa3e9ea4839db7f4`.
Each appended row cross-binds its exact source, executable test, campaign RFC,
and sealed Alpha-v4 parent catalog bytes. The verifier independently replays
all seven dependency-curried bodies. Local recursive closure and direct-Cut
mutation results are feasibility evidence only and do not upgrade these rows
to empty-context checked use.

Rebuild or verify this channel with:

```bash
python3 scripts/build_peano_library_channels_v5.py
python3 scripts/build_peano_library_channels_v5.py --check
python3 scripts/verify_peano_library_channels_v5.py
make peano-library-alpha-v5-check
```

The eight threshold-base rows from `f35b8ed` and five finite Legendre-sum rows
from `4df44c9` are pushed candidate tranches, not Alpha-v5 rows. The
relational-power bridge is still under audit, and neither Legendre's equality
nor Bertrand's postulate is claimed proved.

## Peano Alpha v6 — threshold, finite-sum, and bridge layer (2026-08-09)

Alpha v6, published in commit `5b189f0`, preserves the exact sealed 972-row
Alpha-v5 ledger and appends twenty-one specifications at indices 972--992.
Their frozen dependency-topological split is 8 threshold-base + 5 finite
Legendre-sum + 5 relational-power + 3 Legendre-valuation bridge rows. Alpha v5
and every earlier artifact family remain immutable; Stable is unchanged at
432 rows.

Current topology and evidence:

- 993 theorem specifications, 2,977 declared direct edges, and 45 layers;
- 432 Stable rows and 561 Alpha-only rows;
- 432 `stable_closed`, 138 `alpha_closed`, 422 `body_checked`, and one
  `pending_layered_closure` row;
- 570 checked-use rows; all twenty-one additions fail closed with
  `checked_use=false`, null proof tags, and null empty-context closure
  evidence.

The deterministic pointer is
[`peano-library/channels-v6.json`](peano-library/channels-v6.json). Its exact
artifact SHA-256 values are:

- catalog: `c72d6e1234aa6521b0c524720cd64912f7e9b0bc58f31b6964bbb1a99c5a071d`;
- metrics: `f2a6c22b9fe50581a4cfe8d3b1b494fa274d26d0b51b60e92735650a09391be7`;
- reduced graph: `532c2482a3b1c371026bd80b1b7297faffc4a1b1ee3e53031e499f1611b3ae16`;
  and
- channel pointer: `6ef8bb93b2e24bdfe45389ca9417b6333ce83ae249ee49a957959a6b3471b86c`.

The ordered-enrollment, ordered-specification, edition, membership, evidence,
and channel-pointer roots are respectively
`dc25a3dc0ab7346f9188eee1262700b40bb09efdacfa849f3a27475ed870b5a7`,
`50f395c30e4f21a7b7602bc56451bf2363d1a23d811bba62a33c08e2defc1da1`,
`7e46b80c4799e51da32cedf21a130274200fa14b21e0fec3b42f74d1523ab23b`,
`bd8faa84d1ef0c090fb07aa21ecd966d4f4356999fcd12cf4f74d0e5ae8572b8`,
`c1fcedbd7bbc5e8655dbce3b00ab0bd9296489a3b4358fb548eeb32d081e8682`,
and
`4dc0f9411227e041dbbbcc2626a04d995a6ceeedb91fe9c2d246f377596693b7`.
The exact suffix-depth and fresh 21-body receipt roots are
`d103de2054a0bd4de3b2faa9d98435a4f705594f8a69968e9ca956c455cb61d3`
and
`c23b2fc58fabd3803a0ded5f02d4ea348d67a00b25f5b28b35f3d6bcb00ff2f1`.
The v6 pointer binds the sealed v5 catalog SHA-256
`94efc0f7022f31677619e842f7d6f1d0d0f8959efc54cd64cf346c3b5e8c4892`.

Each appended row cross-binds its exact source, executable test, campaign RFC,
and sealed Alpha-v5 parent catalog bytes. The verifier independently replays
all twenty-one dependency-curried bodies and fails closed under evidence and
binding mutations. This body evidence is not an empty-context admission.

Rebuild or verify this channel with:

```bash
python3 scripts/build_peano_library_channels_v6.py
python3 scripts/build_peano_library_channels_v6.py --check
python3 scripts/verify_peano_library_channels_v6.py
make peano-library-alpha-v6-check
```

The five Legendre-successor rows in commit `5b9433a` and the four
capacity-shared `PowTotal` rows in `b2035ce` are reviewed candidates outside
Alpha v6. The successor suite's largest local closure is 81,828 nodes at depth
95, with 6,931 objects and 7,226 edges. The shared-power closures use 5,327,
10,630, 11,062, and 13,336 nodes and save exactly 59,836, 59,833, 59,836, and
119,652 nodes against their frozen historical comparisons. These measurements
do not enroll or admit the rows. The $H/J$ base-window layer is in progress;
the finite Legendre recurrence, Legendre's equality, and Bertrand's postulate
remain open.

## Peano Alpha v7 — Bertrand recurrence, equality, and transport (2026-08-10)

Alpha v7, published in commit `874e81e`, preserves the sealed 993-row Alpha-v6
ledger byte-for-byte and appends twenty-four specifications at indices
993--1016. Their frozen dependency-topological split is 3 initial-segment
constructors, 5 Legendre-successor facts, 4 capacity-shared `PowTotal` facts,
2 compact $H/J$ base-window facts, 5 finite Legendre-recurrence facts, 3
compact $H/J$ transport facts, and 2 factorial--Legendre agreement facts. Every
earlier artifact family remains immutable; Stable is unchanged at 432 rows.

Current topology and evidence:

- 1,017 theorem specifications, 3,072 declared direct edges, and 45 layers;
- 432 Stable rows and 585 Alpha-only rows;
- 432 `stable_closed`, 138 `alpha_closed`, 446 `body_checked`, and one
  `pending_layered_closure` row; and
- 570 checked-use rows; all twenty-four additions fail closed with
  `checked_use=false`, null proof tags, and null empty-context closure
  evidence.

The deterministic pointer is
[`peano-library/channels-v7.json`](peano-library/channels-v7.json). Its exact
artifact SHA-256 values are:

- catalog: `7676fc944b695d02a3aec05b428c012933258cb6cd9b465599318e690e0f6df4`;
- metrics: `c40f18bda0ec8feb9294cf445d08b51daf868e46b3931daf55bad91413d39e0d`;
- reduced graph: `85a53bd719e227a31d5cff15fc25ff66abaa82d498030f5a918a7c40271abc9e`;
  and
- channel pointer: `fe9c11ec8a622eb759053a42ee6acb7c2bcb1d454fe0dc5fa4b729a07ffbbd30`.

The ordered-enrollment, ordered-specification, edition, membership, evidence,
and channel-pointer roots are respectively
`aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c`,
`838c8f48f81eddcdf3e9de0f9557cee1c25eb78015513d99cfe8ab76975edc65`,
`9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff`,
`e6d22473986c7e4ec1e4566f156c3dad710a4a9be2ae7b830490546da48cb703`,
`a3709e040891b7c180c5c35876ec0e033b58ad12ce5179c3b0215ed11c1a93b6`,
and
`e868088b8abf7b98e1a3976058adfca5ed542a1d9b29c275ebd16c070cd810c3`.
The v7 pointer binds the sealed v6 catalog SHA-256
`c72d6e1234aa6521b0c524720cd64912f7e9b0bc58f31b6964bbb1a99c5a071d`.

The verifier independently replays every dependency-curried suffix body and
fails closed under binding, evidence, topology, artifact, and body mutations.
This completes body evidence for finite Legendre recurrence,
`prime_factorial_valuation_eq_legendre_sum`, and compact $H/J$ six-step
transport; it is not empty-context admission or Stable promotion. Bertrand's
postulate remains open.

Rebuild or verify this channel with:

```bash
python3 scripts/build_peano_library_channels_v7.py
python3 scripts/build_peano_library_channels_v7.py --check
python3 scripts/verify_peano_library_channels_v7.py
make peano-library-alpha-v7-check
```

Heavy proof validation is deliberately serial. Each proof module and mutation
group runs in a fresh Python process, with no concurrent proof worker, so
retained proof DAGs cannot accumulate across the entire gate on a
memory-constrained laptop.

## Peano Alpha v8 — Choose and central-binomial lower bound (2026-08-15)

Alpha v8 preserves the sealed 1,017-row Alpha-v7 ledger byte-for-byte and
appends thirty-eight reviewed Bertrand specifications at indices 1017--1054.
The binding 24+14 microbatches first build recurrence-defined `Choose` and
baseline `CentralBinom`, then add the central recurrence, weighted and
factorial bridges, strict growth, the fourth-row seed, and
`four_pow_lt_mul_central_binom`. Stable remains unchanged at 432 rows.

Current topology and evidence:

- 1,055 theorem specifications, 3,224 declared direct edges, and 45 layers;
- 432 Stable rows and 623 Alpha-only rows;
- 432 `stable_closed`, 138 `alpha_closed`, 484 `body_checked`, and one
  `pending_layered_closure` row; and
- 570 checked-use rows; all thirty-eight additions fail closed with
  `checked_use=false`, null proof tags, and null empty-context closure
  evidence.

The deterministic pointer is
[`peano-library/channels-v8.json`](peano-library/channels-v8.json). Its exact
artifact SHA-256 values are:

- catalog: `c06c5fde7b84b4a8524dd408a2b046d06c7a88ccb5814877b7ccfec0d20b1370`;
- metrics: `90c14911ef50391dd9fd99865a83a6e0886911253504096a30e497d30c1a6813`;
- reduced graph: `ff194534f1efd56dd771237b6a44279a705309df21c1fa319b6669f3e1cab008`;
  and
- channel pointer: `dec01b10ee9359b1f7057187725016d343bfb7f3176d8779c85da7f26983234d`.

The ordered-enrollment, ordered-specification, edition, membership, evidence,
and channel-pointer roots are respectively
`a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2`,
`fe49d664e5a88f6637c7790b104e9b0aa3c583e48f9a4a1405d5b098f7f61df9`,
`2101b7b384ec9791c41d07d8115123d6842729615a0084ce87cead619bc8c123`,
`4471bdcf06a2d3af866850b39f394a436ad608b4c0b166c0449620e5dd3c9ee3`,
`4230c17701be2c604ea413be90c26bad41889d593dcaaeff311217b4e26367b4`,
and
`1fd2216e0448fbeb0d8da60dea3b89fca4d4f7192371fc87a8c5cd35dccf3c70`.
The append is controlled by
[`RFC HA-R6-BERTRAND-CB-1`](../research/arithmetic-library/ha-bertrand-choose-central-binomial-tranche-rfc-v1.md).

The verifier independently replays every suffix body and cross-binds each row
to its exact source, focused test, RFC, and sealed Alpha-v7 catalog. This is
body evidence, not empty-context admission or Stable promotion. The primorial,
no-prime central upper bound, large-input integration, finite coverage, and
Bertrand endpoints remain open.

Rebuild or verify this channel with:

```bash
python3 scripts/build_peano_library_channels_v8.py
python3 scripts/build_peano_library_channels_v8.py --check
python3 scripts/verify_peano_library_channels_v8.py
make peano-library-alpha-v8-check
```

## Peano Alpha v9 — Primorial foundation and membership (2026-08-15)

Alpha v9 preserves the sealed 1,055-row Alpha-v8 ledger byte-for-byte and
appends twenty-one reviewed Bertrand specifications at indices 1055--1075.
The binding 10+11 microbatches first freeze the conservative inclusive
`Primorial` relation and its recursive laws, then prove exact prime
membership, divisibility, positive-quotient, and monotonicity laws. Stable
remains unchanged at 432 rows.

Current topology and evidence:

- 1,076 theorem specifications, 3,276 declared direct edges, and 45 layers;
- 432 Stable rows and 644 Alpha-only rows;
- 432 `stable_closed`, 138 `alpha_closed`, 505 `body_checked`, and one
  `pending_layered_closure` row; and
- 570 checked-use rows; all twenty-one additions fail closed with
  `checked_use=false`, null proof tags, and null empty-context closure
  evidence.

The deterministic pointer is
[`peano-library/channels-v9.json`](peano-library/channels-v9.json). Its exact
artifact SHA-256 values are:

- catalog: `74ab887e9eef3e3fc583b103f392f4e06125cb14a561765373677eb57f830eda`;
- metrics: `7397959a4dad4e1d42e6a108156c84666b4cd4f95e07e573d1fcf402f83c2d65`;
- reduced graph: `03b803080cd082642adeb2a89b62ab369c7e69aca4c4dfe90b327ef94c389ab9`;
  and
- channel pointer: `77fd0ba0ad1ba461432384c3330041a3dfc641dc84121982eb08456ee2de9a34`.

The ordered-enrollment, ordered-specification, edition, membership, evidence,
and channel-pointer roots are respectively
`fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f`,
`762d1310c41ed92da066701cf7529551324b09f7b501c5a29c530f443afeb998`,
`b74d7479d749500dbbd737f7cf5e7ea97a7998f8079233ed87b11c84823e2f80`,
`4c87c40b5a260d67b5582447cfabb7e3ce62e80303aa4f4d33b1b952995ec356`,
`108593843459a69d81c333305a50b5368294c3c722437f425b92c942391fe9be`,
and
`edfb0eacecbd9419b1b303098915e28e45643379b65ab7d807ffcd4d7bd4b3e7`.
The suffix-depth and fresh 21-body receipt roots are
`61f33ba9e49219ff4a199d082722d9582ac6d87f825851173ac7fdb6931bb52d`
and
`1a9bac74069a495d6ce17b906f46821731d6fad4e97d07e7272cf57da72593ab`.
The append is controlled per source by the
[`Primorial foundation RFC`](../research/arithmetic-library/ha-bertrand-primorial-foundation-tranche-rfc-v1.md)
and
[`Primorial membership RFC`](../research/arithmetic-library/ha-bertrand-primorial-membership-tranche-rfc-v1.md).

The verifier independently replays every suffix body and cross-binds each row
to its exact source, focused test, source-specific RFC, and sealed Alpha-v8
catalog. This is body evidence, not empty-context admission or Stable
promotion. Filtered interval splitting, duplicate-free external-product
comparison, `primorial_le_four_pow`, the no-prime central upper bound,
large-input integration, finite coverage, and Bertrand endpoints remain open.

Rebuild or verify this channel with:

```bash
python3 scripts/build_peano_library_channels_v9.py
python3 scripts/build_peano_library_channels_v9.py --check
python3 scripts/verify_peano_library_channels_v9.py
make peano-library-alpha-v9-check
```

## Peano Alpha v10 — Primorial interval splitting (2026-08-15)

Alpha v10 preserves the sealed 1,076-row Alpha-v9 ledger byte-for-byte and
appends nine reviewed Bertrand specifications at indices 1076--1084. The
exact 1+8 order pins only the reviewed Product prefix/suffix split, then adds
offset selector products and the exact Primorial prefix/interval split. The
provider's concat converse remains excluded. Stable remains unchanged at 432
rows.

Current topology and evidence:

- 1,085 theorem specifications, 3,306 declared direct edges, and 45 layers;
- 432 Stable rows and 653 Alpha-only rows;
- 432 `stable_closed`, 138 `alpha_closed`, 514 `body_checked`, and one
  `pending_layered_closure` row; and
- 570 checked-use rows; all nine additions fail closed with
  `checked_use=false`, null proof tags, and null empty-context closure
  evidence.

The deterministic pointer is
[`peano-library/channels-v10.json`](peano-library/channels-v10.json). Its exact
artifact SHA-256 values are:

- catalog: `46bd50c19b694470542f53f1ef7f61d1ee8fab1f08ad5573ca3534da29053dc3`;
- metrics: `63044f59aeb6fd84fbe57e26f8358676e679e15ef7456f1823db68bc255703de`;
- reduced graph: `fdee73e6ea045c90afb7c024e8a209fbea8b03189538611c93678e4fa923aa76`;
  and
- channel pointer: `644fb72833d66f30b2194a5d493935f31bae716edb4c76afcb8c6e272399eca2`.

The ordered-enrollment, ordered-specification, edition, membership, evidence,
and channel-pointer roots are respectively
`c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f`,
`6ab70321b61bea288df325ffa433c992d0559e9546324583066b4f767249df46`,
`1e4376021508ac6913770ac18eca8c1406c7b298d7e381f994510c6854baa98d`,
`01ec76832d511806302056f2f823b2d8c45c477cf92d826bfae28197f1656013`,
`a00e426172d93e9c9254d97ec2295031873dd02fc97a003eb4824cc22b64e81a`,
and
`f2c2760dd275b94572e0ab5a5cc4837fc1e884ea26ea00a55074caa84a4d8f6e`.
The suffix-depth and fresh nine-body receipt roots are
`446f6c9d07c3f9e22fa0fbb41a46c95d27804a088d708b13aea0ddd7159c45dd`
and
`fdac645cbc070b5a1cdfe71b19e98afe095a183d4cfa0ad4256fa42857ca736c`.
The append is controlled by the
[`Primorial interval-split RFC`](../research/arithmetic-library/ha-bertrand-primorial-interval-split-tranche-rfc-v1.md).

The verifier independently replays every suffix body and cross-binds each row
to its exact source, focused test, RFC, and sealed Alpha-v9 catalog. This is
body evidence, not empty-context admission or Stable promotion.
Duplicate-free external-product comparison, `primorial_le_four_pow`, the
no-prime central upper bound, large-input integration, finite coverage, and
Bertrand endpoints remain open.

Rebuild or verify this channel with:

```bash
python3 scripts/build_peano_library_channels_v10.py
python3 scripts/build_peano_library_channels_v10.py --check
python3 scripts/verify_peano_library_channels_v10.py
make peano-library-alpha-v10-check
```

## Peano Alpha v11 — Primorial capstone and B5 support (2026-08-16)

Alpha v11 preserves the sealed 1,085-row Alpha-v10 ledger byte-for-byte and
appends thirty-eight reviewed Bertrand specifications at indices 1085--1122.
The exact 20+18 microbatches enroll the dependency-closed chain from
duplicate-free prime products and Primorial/Choose interval bounds through
the public `primorial_le_four_pow` capstone and the first B5 central
prime-divisor support rows. Stable remains unchanged at 432 rows.

Current topology and evidence:

- 1,123 theorem specifications, 3,482 declared direct edges, and 45 layers;
- 432 Stable rows and 691 Alpha-only rows;
- 432 `stable_closed`, 138 `alpha_closed`, 552 `body_checked`, and one
  `pending_layered_closure` row; and
- 570 checked-use rows; all thirty-eight additions fail closed with
  `checked_use=false`, null proof tags, and null empty-context closure
  evidence.

The deterministic pointer is
[`peano-library/channels-v11.json`](peano-library/channels-v11.json). Its exact
artifact SHA-256 values are:

- catalog: `d992c4aeb37829838cefd668679c513c5d45f6304f9842dcbe825bb25563182c`;
- metrics: `92cb654431a1b631cede3a0957993b41b8ad0fb0a0175d1587413dbf54c14300`;
- reduced graph: `c020f3207b0408cf446200b2c91f0767874c50466eebda830c3faeeef08aeae1`;
  and
- channel pointer: `039712b6a1db739738f49b5cec20afdc0582ffae477bc43c52f96c00687b066f`.

The ordered-enrollment, ordered-specification, edition, membership, evidence,
and channel-pointer roots are respectively
`c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36`,
`4a1f4302b0a4ede3bf5123ec021b4f2f5f98c2a7e22eadc6f13a446422ad9450`,
`46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3`,
`2f0be30e7de93bcf89235700c419f46656cb638be85ca153154684845e8dabdb`,
`b82b567e59cabeda6f90fdfedaceb628ca2e7c4b7423be643b8f22865e7599bd`,
and
`ecce457947650ae7ddf2a638d8b1f2c8757daea6a95ea9c927ebaef3995d4ccd`.
The suffix-depth and fresh thirty-eight-body receipt roots are
`cf5d550d5a3aa4af1debf9268eca578c30ca408058dcdeb35892bc705287214e`
and
`6c314d36cd7bb1e6cb5b213fec9bf9e04ab118e84121830b00c885ede2abac2a`.

The verifier independently replays every suffix body and cross-binds each row
to its exact source, focused test, source-specific RFC, and sealed Alpha-v10
catalog. This is body evidence, not empty-context admission or Stable
promotion. The five-range no-prime central upper bound, large-input
integration, finite coverage, and Bertrand endpoints remain open.

Rebuild or verify this channel with:

```bash
python3 scripts/build_peano_library_channels_v11.py
python3 scripts/build_peano_library_channels_v11.py --check
python3 scripts/verify_peano_library_channels_v11.py
make peano-library-alpha-v11-check
```
