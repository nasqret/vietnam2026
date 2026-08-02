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
| Native quadratic reciprocity | [`PLAN/11_quadratic_reciprocity.md`](PLAN/11_quadratic_reciprocity.md) | Parity and finite folds → Euler/Gauss/Eisenstein → a checked reciprocity certificate. |

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
Subsequent native arithmetic and quadratic-residue campaign passes extend that
same runtime to 384 checked theorems, including discrete order, multiplication cancellation and
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
language and logic unchanged. The earlier public-catalog full-surface audit yields 474
prospective model-v2 transitions. They are valuable curriculum seeds, but only one is an
`induction` label, so balanced generation and
sampling remain necessary. See
[`PLAN/09_peano_lab.md`](PLAN/09_peano_lab.md). M18 remains the latest completed and staged
milestone; production remains untouched behind the M14 cache-header blocker.

## Parallel foundational arithmetic and quadratic-reciprocity milestones

M20 generalizes the theorem ladder into a structured arithmetic corpus. The
current 384 checked runtime entries comprise the original 23-theorem base, 212
post-baseline foundational theorems, twelve unique upstream mod-five
capstones, and 137 checked M21–M23 quadratic-residue foundations. The
constructive dependency graph now runs from equality, order,
cancellation, division and relational gcd through balanced-natural Bézout,
Gauss cancellation, primality decision, prime-divisor existence and Euclid's
lemma. Its conservative finite-sequence layer uses expanded Gödel-β relations
and prefix-product traces—without adding lists or arithmetic functions to the
object language—and proves CRT recoding, canonical sorted factorization
existence, extensional uniqueness, and the native Fundamental Theorem of
Arithmetic. The exact FTA certificate checks from the empty context at 73,767
nodes, depth 99 and 2,184 self-contained Cuts, with no DNE. The synchronized
381-entry catalog has 23 `checked_existing`, 357 `checked_m20`, no remaining
planned theorem, and one representation-blocked
conventional integer-coefficient Bézout interface. A pinned Lean companion
independently checks conventional list-based FTA up to permutation. Remaining
M20's native arithmetic and synchronized release artifacts are complete. The
main Jupyter Book now includes a guided zero-to-FTA route, a quadratic
reciprocity campaign chapter, and a generated interactive 380-proof atlas;
direct attached-browser UI inspection remains
explicitly unclaimed, and
model-v2 curriculum expansion is a separate milestone—not mathematical
admission of FTA or prime unboundedness. See
[`PLAN/10_arithmetic_library.md`](PLAN/10_arithmetic_library.md).

M21–M25 continue systematically toward a native sign-free quadratic
reciprocity theorem. M21 and M22 are checked through constructive residue
membership, finite folds and fold congruence. The dependency-curried campaign
is now body-green through general product permutation, Fermat and Wilson,
both bounded branches of Euler's criterion, and the power-congruence form of
Gauss's lemma. The complete bounded Gauss classification is now body-green as
an actual quadratic-residue/count-parity equivalence, and the supporting
modulo-two plus odd-division parity interfaces are body-green as well. The
complete odd-prime Euler equivalence is now body-green in
both directions for arbitrary unit representatives, using canonical-remainder
reduction and congruence transport. On the Eisenstein route, quotient
prefixes/sums, exact row counts, quotient-sum-to-rectangle transport, generic
exact pointwise sum addition, transposed-cell complementarity, and coherent
whole-column count partitions are body-green. The entire column-count outer
prefix is now summed as well, giving `N+M=h*k`. The genuine Fubini induction
now identifies `M` with the swapped total `T`, yielding `N+T=h*k`, and the
decoded two-orientation quotient endpoint proves `Q+U=h*k`. These are not admissions:
recursive closure, mutations and receipt-pinned admission remain WMI gates,
and the final two-orientation existential composition is now body-green. The
actual-QRes Gauss endpoint
also accepts arbitrary unit representatives, so both prime orientations can
reuse it directly in the completed count/floor-sum parity bridge. Its
generic pointwise arithmetic core is now body-green as
`x == q+m+s (mod 2)` for aligned odd scaled-division/sign data; exact prefix
alignment is now body-green as well, including the exact `r=m`/`r+m=p`
branch and the common-index β-prefix theorem. Exact finite-sum permutation
invariance is also available. Terminal summation and magnitude-sum
cancellation are now body-green, preserving all beta-code provenance and
proving each orientation's Gauss sign count congruent modulo two to its
quotient sum. The constructive final modulo-four/QRes truth tables are
body-green and feed exact same-status and opposite-status QR bodies; the predeclared
combined sign-free quadratic-reciprocity surface is now body-green. Its
sharing-optimized direct wrapper checks at 113 nodes/depth 35 and constructs
the two-orientation package only once. A 20-test downstream replay passes in
27.25 seconds. This is
the mathematical certificate body, not yet a library admission: layered
closure, mutation checks, capacity profiling, and pinned admission remain WMI
gates. The dual availability policy is 500,000 structural occurrences,
100,000 distinct
proof objects, and depth 256; the kernel and PA language are unchanged. See
[`PLAN/11_quadratic_reciprocity.md`](PLAN/11_quadratic_reciprocity.md).

The recursive QR tree is no longer a capacity uncertainty: source recurrence
forces at least 731,482 proof nodes. The preferred replacement is implemented
as an isolated 45-layer balanced-conjunction compiler whose output is one
ordinary existing `Proof` checked by the unchanged kernel. Its focused tests
pass `25/25`; an exact 557-node/1,791-edge dependency-consuming surrogate is
kernel-green at 19,088 nodes/depth 74, while false bodies against the actual
QR formulas are rejected. The real 557-body compile/check, resource receipt,
mutations, public migration and Pyodide gate remain WMI-dependent. The
content-addressed nine-gate job is ready. A historical second
scheduler-validation attempt timed out before upload and created no remote
snapshot or job; the newer approval boundary is recorded below.

The admission implementation is now prepared but deliberately not activated.
The QR stack is injection-based over a frozen pre-QR table, and the generic
layered compiler is a production-neutral constructive ordinary-proof builder.
Its exact proof-envelope scanner covers all 25 kernel constructors, rejects
classical and engine-only nodes, and separately bounds embedded annotations.
Static exact-topology evidence preserves the `19,088/74` proof receipt and now
adds `142,346/84` annotations/envelope depth; the actual-formula false scaffold
adds `157,579/92`. Bare `pa lib` no longer replays the ladder, and the browser
worker inventory deterministically covers 147 Python files. A migration audit
identifies 125 pre-admission absence assertions and the exact 317/29 public
partition. Full 136-gate WMI job `187187`, bound to approved dirty snapshot
`2bab0898a5bc628a0e1f06b5e6cdf56af86fe39c2fdbeaaa4147ac43d2c7faaa`,
failed closed after 39 seconds at gate 5. Four scaled-inverse gates passed;
the fifth exposed the unused `succ_ne_zero` dependency, and 131 gates did not
run. The corrected focused suite and refreshed topology receipts pass locally.
Full replacement job `210714`, from exact clean snapshot `989011c0…1757`,
failed closed at gate 15/136 after 14 passes because replacing the declared
edge `odd_upper_remainder_reflection -> add_succ_left` did not invalidate the
certificate; 121 gates were unrun. This blocks enrollment but is neither a
kernel-soundness failure nor a quadratic-reciprocity result.

The native PA Proof Explorer now makes that exact evidence boundary
navigable. Its persistent 557-page tag corpus has 1,791 dependency edges,
27,491 line-addressable tactic commands, 8,557 explicit theorem links, and a
separate foundations view for PA grammar, PA1–PA6, proof constructors, and
tactics. The permanent QR endpoint is `PA00FW`. The interface labels 240
public theorems, 316 body-checked candidates, and the one root awaiting
layered closure; it does not enroll any candidate. Source integration and 24
bounded explorer/Book/WMI-harness checks are complete. A fresh WMI Jupyter
Book build/integrity receipt and attached-browser interaction pass remain
publication gates, and the former frozen QR upload hash is stale after these
payload-changing additions.

Graph v2 now exposes the same closure as navigable premise paths: 557 theorem
nodes, 1,791 direct edges, 45 layers, and 48 theorem roots (corpus roots, not
PA axioms or kernel foundations). For `PA00FW` it records 101,293 distinct
root-to-target paths, a 4-vertex shortest witness, and a 45-vertex critical
depth witness. The Book endpoint is
`book/arithmetic-library/dependency-graph.md`, and the static explorer opens at
`book/_static/pa-proof-explorer/graph.html?target=PA00FW` with the exact proof
page one click away. This completes the static dependency-path presentation;
the generator owns all 1,123 files under a pinned aggregate, and the full
local Book build/integrity check is green. `PA00FW` remains pending layered
closure after WMI job `187187` failed at its early dependency-hygiene gate;
attached-browser validation also remains a publication gate.
