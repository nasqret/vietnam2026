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

[`peano-library/`](peano-library/) is the deterministic snapshot of all 170
checked Peano library entries. Its internal snapshot-v2 schema contains
statement/script/certificate hashes, exact node/depth and structural Cut
metrics, an ordered root digest, and the dependency DAG in Mermaid form.
The current snapshot totals 99,137 structural nodes and 2,693 Cuts across 130
Cut-bearing entries. `binary_crt_beta_pair` is largest at 6,941 nodes
and 201 Cuts; `prime_divisor_exists` reaches the maximum depth of 80.
The latest checked tranches add the full additive/multiplicative compatibility
layer for balanced congruence, the five expanded decoded-value theorems from
`beta_modulus_nonzero` through `beta_at_exists_unique`, and the directed
remainder/congruence bridges. Bounded representative uniqueness and the
reverse β bridge now make expanded β decoding equivalent to a bound plus
balanced congruence. The subtraction-free binary CRT tranche also contains
the two modular Bézout projections, predecessor cancellation, constructive
binary CRT, its bounded-residue form, and a conditional two-position β-code
constructor. The snapshot does not claim β-modulus coprimality, bounded CRT
iteration, finite prefixes, encoded products, greatest-prime descent, or
native FTA.
Rebuild or verify it with
`python3 scripts/build_peano_library_snapshot.py [--check]`.

The snapshot is evidence about replayed certificates, not a theorem database
trusted by the kernel. The broader checked/planned/blocked research graph lives
in `research/arithmetic-library/catalog.json`; it currently has 177 nodes: 23
`checked_existing`, 147 `checked_m20`, three planned, and four
language-blocked.

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
snapshot is its 170-theorem successor. Incompatible same-name records fail
closed.
