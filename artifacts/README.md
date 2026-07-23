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
