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
new, giving 63 unique checked runtime theorems without changing the kernel. A
subsequent native arithmetic passes extend that same runtime to 127 checked
theorems, including discrete order, multiplication cancellation and
monotonicity, constructive quotient-remainder existence, and full
quotient-remainder uniqueness, mutual-divisibility antisymmetry, relational
gcd uniqueness, both directions of Euclidean gcd invariance, and constructive
relational gcd existence. The runtime
now also has audited self-contained dependency sharing: a Cut embeds
the full lemma and body proofs and is checked without external theorem names or
hashes. This enlarges the trusted certificate checker but leaves the PA object
language and logic unchanged. The earlier public-catalog full-surface audit yields 474
prospective model-v2 transitions. They are valuable curriculum seeds, but only one is an
`induction` label, so balanced generation and
sampling remain necessary. See
[`PLAN/09_peano_lab.md`](PLAN/09_peano_lab.md). M18 remains the latest completed and staged
milestone; production remains untouched behind the M14 cache-header blocker.

## Parallel foundational arithmetic milestone

M20 generalizes the theorem ladder into a structured arithmetic corpus. Its
checked layers now add 90 reusable equality, cancellation, order,
multiplication, divisibility, residue, division, and small-prime lemmas, including the
first checked fully expanded prime instance `prime_two`. The catalog maps the
exact route to division, gcd, the general prime spine, and factorization. A
sorted Gödel-β sequence/product encoding is now selected, and a pinned Lean
companion checks full list-based FTA existence and uniqueness up to
permutation. The reconciled runtime also includes twelve unique upstream
mod-five capstones for 127 checked Peano theorems in total. Division,
relational gcd existence and uniqueness, Euclidean-step invariance, and
self-contained proof sharing are now native; Peano admission of FTA still
awaits Bézout, Euclid, and the encoded finite-product spine. See
[`PLAN/10_arithmetic_library.md`](PLAN/10_arithmetic_library.md).
