# Plan — index view

The plan is multi-level. **L0** fixes the goals; **L1** lists the work modules (one file each in
[`PLAN/`](PLAN/)); **L2/L3** live inside those files as concrete tasks with acceptance criteria.
Narrative progress is in [`JOURNAL.md`](JOURNAL.md); durable facts in [`MEMORY.md`](MEMORY.md).

## L0 — Goals

> See [`PLAN/00_goals.md`](PLAN/00_goals.md)

Deliver a coherent, *growing* set of course materials that carry a mathematically-mature but
formal-methods-new audience from the λ-calculus and type theory to the auto-formalization of research
mathematics — with every idea presented **informally (runnable) and formally (machine-checked)**.

## L1 — Work modules

| Module | File | Short description |
|--------|------|-------------------|
| Landing page | [`PLAN/01_landing_page.md`](PLAN/01_landing_page.md) | `/vietnam2026` hero + 6-lecture plan + descriptions + cross-links; style of `classical-foundations-ann`. |
| Knowledge book | [`PLAN/02_knowledge_book.md`](PLAN/02_knowledge_book.md) | JupyterBook: the full text-friendly notes (maths + code + links) — the "learning data". |
| Obsidian vault | [`PLAN/03_obsidian_vault.md`](PLAN/03_obsidian_vault.md) | Atomic wiki-linked knowledge base; MOCs per lecture; source of truth for concepts. |
| Formal artifacts | [`PLAN/04_artifacts.md`](PLAN/04_artifacts.md) | Same statements in Lean / Agda / Rocq / Mizar — the four foundations, side by side. |
| Browser Lambda Lab | [`PLAN/05_browser_lab.md`](PLAN/05_browser_lab.md) | `lambda_lab` running client-side via Pyodide + xterm.js; deployed to `/lab-lambda`. |
| Slides | [`PLAN/06_slides.md`](PLAN/06_slides.md) | One reveal.js deck per lecture, to present live. |
| Research dossier | [`PLAN/07_research.md`](PLAN/07_research.md) | Depth, citations and current-landscape groundwork feeding every lecture. |
| Release & deploy | [`PLAN/08_deploy.md`](PLAN/08_deploy.md) | Git → GitHub → faculty server; incremental go-live; build/link checks. |
| Peano Lab | [`PLAN/09_peano_lab.md`](PLAN/09_peano_lab.md) | Sound browser theorem prover for PA: kernel → checked arithmetic tactics → UI → book/vault/corpus. |
| Foundational arithmetic library | [`PLAN/10_arithmetic_library.md`](PLAN/10_arithmetic_library.md) | Versioned lemma DAG: congruence and divisibility → division/gcd/primes → an honestly represented FTA. |

## L2 / L3

Each `PLAN/*.md` file spells out **objectives**, **subtasks**, and **acceptance criteria**. Tasks are
checkboxes; keep them current as work lands. The through-line and prerequisite graph from the research
synthesis are the backbone the book and vault follow.

## Active Peano Lab milestone

M19 adds a compact headless adapter and a kernel-guided post-training experiment without changing
the prover's trust boundary. The JSONL runner reuses the production parser, surface tactics,
theorem library, proof engine, traces, and independent original-target finalizer. The pilot data,
replay compiler, fixed capability profile, BF16 LoRA runtime, evaluator provenance, guarded
Helios controls, and the first independently replay-attested 10,000-row synthetic release are
implemented. Helios training `20029970` completed 100 steps, but evaluator `20029980` failed before
generation on a manifest key-order bug. WMI typed-A100 probe `171369` also passed, and its independent
x86-64 base manifest, hash-locked overlay, transactional source controls, and one-shot safetensors
model-weight path are locally green. A trained adapter can now be used on an arbitrary bounded
closed PA formula through a second-kernel-replayed CLI and a ledgered immutable-request WMI A100
job. The corrected same-source WMI chain then passed preparation (`171414`), 100-step training
(`171421`), and held-out evaluation (`171423`). Its manifest records train/validation losses
0.7830/0.1362, but the kernel-judged result is 0/4 goals at pass@4. The earlier parity theorem also
failed at pass@16 (`171428`), while one fresh direct-witness theorem succeeded once in eight samples
and replayed to a seven-node kernel-checked proof (`171430`). This is a real within-template success,
but attribution to LoRA training awaits the pretrained-base baseline; the adapter is not yet a
dependable induction/order prover. The current dataset has
no positive rows for nine tactic heads, including `induction`, `simp`, and `specialize`;
the next registered iteration is a library-snapshot-bound `model-v2`, not a 4B scale-up on the same
curriculum. The owner authorized the compatibility-validated 26-record modular extension for the
public catalog. After reconciliation with M20, fourteen records overlap exactly and twelve are
new, giving 63 unique checked runtime theorems without changing the kernel.
Subsequent native arithmetic passes extend that same runtime to 247 checked
theorems, including discrete order, multiplication cancellation and
monotonicity, constructive quotient-remainder existence, and full
quotient-remainder uniqueness, mutual-divisibility antisymmetry, relational
gcd uniqueness, both directions of Euclidean gcd invariance, constructive
relational gcd existence, balanced-natural Bézout, Gauss cancellation, and
Euclid's lemma. Constructive equality/divisibility decisions, bounded factor
search, prime/composite decision, proper-factor descent, and prime-divisor
existence are now checked as well. Balanced congruence is transitive and fully
compatible with addition and multiplication; bounded representatives are
unique, and for a nonzero modulus a directed remainder is equivalent to a
bounded congruence witness.
Expanded Gödel-β decoding is therefore equivalent to a bound plus balanced
congruence, while remaining total and functional. Constructive binary CRT and
a conditional two-position β-code constructor are now checked. The latest
tranche proves coprimality when an ordered index gap divides `c`,
applies it to the β-pair constructor, and builds nonzero common multiples for
every positive gap through a bound. The latest passes close bounded-prefix
pairwise coprimality, add coprime-product closure and modulus descent, and fold
an accumulated-product/decoded-congruence invariant through every bounded
prefix by ordinary induction. Later checked layers supply genuine β
finite-prefix recoding, exact prefix-product traces, prime and sortedness
predicates, greatest-prime-divisor descent, and canonical factorization
existence and extensional uniqueness. Their native FTA conjunction checks at
73,767 nodes/depth 99 with 2,184 self-contained Cuts. Unconditional pairwise
β-modulus coprimality remains false; it is handled by the bounded-base
construction rather than assumed.
The same constructive spine now proves `prime_unbounded`: take a prime divisor
of the successor of a nonzero common multiple through `n`; if that prime were
at most `n`, it would divide both consecutive numbers and hence one. Its exact
certificate checks at 4,595 nodes/depth 82 with 146 Cuts, uses PA1–PA6 only,
and contains no DNE.
The
runtime now also has audited self-contained dependency sharing: a Cut embeds
the full lemma and body proofs and is checked without external theorem names or
hashes. This enlarges the trusted certificate checker but leaves the PA object
language and logic unchanged. The earlier public-catalog full-surface audit
yielded 474 prospective model-v2 transitions. It is retained as design
history: only one is an `induction` label, so it cannot support the intended
explorer by itself. The implemented successor is a distinct model-v3
curriculum bound to the complete 247-theorem declaration order. It contributes
8,494 exact authored predecessor-prefix transitions plus 70,000 deterministic
synthetic rows over 51 schemas and 14 balanced root tactic heads. Catalog data
is train-only; validation/test are synthetic-only, target formulas are
rejected from every intermediate state, and a lossless v3-only prompt codec
keeps the audited stress-proof maximum at 29,111 of 32,768 Qwen tokens. The
pinned WMI Qwen3-1.7B Base rank-32/alpha-64 one-epoch run is registered. Exact-
corpus continuation `173040` completed its independent gates and seal job
`213641` published the verified immutable corpus. Current-source preparation
`214264` failed closed before runtime smoke or model loading because the
selected train curriculum exposed 73,446,475 tokens against the reviewed
70,000,000-token ceiling. A retry with only that ceiling raised to 74,000,000
is pending; the run remains untrained and unevaluated. See
[`PLAN/09_peano_lab.md`](PLAN/09_peano_lab.md). M18 remains the latest completed
and staged milestone; production remains untouched behind the M14 cache-header
blocker.

## Parallel foundational arithmetic milestone

M20 generalizes the theorem ladder into a structured arithmetic corpus. Its
247 checked runtime entries comprise the original 23-theorem base, 212
post-baseline foundational theorems, and twelve unique upstream mod-five
capstones. The constructive dependency graph now runs from equality, order,
cancellation, division and relational gcd through balanced-natural Bézout,
Gauss cancellation, primality decision, prime-divisor existence and Euclid's
lemma. Its conservative finite-sequence layer uses expanded Gödel-β relations
and prefix-product traces—without adding lists or arithmetic functions to the
object language—and proves CRT recoding, canonical sorted factorization
existence, extensional uniqueness, and the native Fundamental Theorem of
Arithmetic. The exact FTA certificate checks from the empty context at 73,767
nodes, depth 99 and 2,184 self-contained Cuts, with no DNE. The synchronized
248-entry catalog has 23 `checked_existing`, 224 `checked_m20`, no remaining
planned theorem, and one representation-blocked
conventional integer-coefficient Bézout interface. A pinned Lean companion
independently checks conventional list-based FTA up to permutation. Remaining
M20's native arithmetic and synchronized release artifacts are complete. The
main Jupyter Book now includes a guided zero-to-FTA route and a generated
interactive 247-proof atlas; direct attached-browser UI inspection remains
explicitly unclaimed, and
model-v3 curriculum training is a separate milestone—not mathematical
admission of FTA or prime unboundedness. See
[`PLAN/10_arithmetic_library.md`](PLAN/10_arithmetic_library.md).
