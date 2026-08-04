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
| Peano Hydra | [`PLAN/11_peano_hydra.md`](PLAN/11_peano_hydra.md) | Living native-PA library and prose authoring assistant plus a frozen Vampire/Qwen matched-compute campaign. |
| Kernel acceleration | [`PLAN/12_peano_kernel_acceleration.md`](PLAN/12_peano_kernel_acceleration.md) | Python authority, native/WASM Rust acceleration, and staged Lean algorithm/source-refinement gates before any authority change. |

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
but at that model-v1 checkpoint attribution to LoRA training still awaited its
own pretrained-base baseline, and that adapter was not a dependable
induction/order prover. The then-current dataset had
no positive rows for nine tactic heads, including `induction`, `simp`, and `specialize`;
the next registered iteration was a library-snapshot-bound `model-v2`, not a 4B scale-up on the same
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
language and logic unchanged. The earlier public-catalog full-surface audit
yielded 474 prospective model-v2 transitions. It is retained as design
history: only one is an `induction` label, so it cannot support the intended
explorer by itself. The implemented successor is a distinct model-v3
curriculum bound to the frozen first-247 declaration-order prefix of the
current 384-theorem native ladder. It contributes
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
70,000,000-token ceiling. Retry `217123`, with only that ceiling raised to
74,000,000, passed the exact token audit and reached saved-policy admission.
It then failed closed because the in-memory model retained Accelerate's
mixed-precision forward wrapper while the fresh reload used the bare inference
forward. The shared admission path now unwraps and verifies the exact original
forward before comparison. Fresh same-source preparation `217851` passed every
gate, and guarded successor `217859` completed the registered 649-update
rank-32 Qwen3-1.7B run. Trained evaluation `218171` and the
revision/configuration-pinned pretrained comparison `218172`, whose report
declares no PEFT adapter, completed with immutable four-goal `k=1` reports of
3/4 and 0/4. The three trained proof claims independently kernel-replay; the
induction-heavy goal remains unsolved. Version-pinned producer recoveries and
the paired cross-binding pass as `paired_launch_smoke_admitted`, while the
ordinary trained-report replay correctly continues to reject its incomplete
historical nested environment. This is a narrow launch smoke, not bit-for-bit
base identity, a statistical or causal comparison, broad PA ability, or
induction capability. See
[`PLAN/09_peano_lab.md`](PLAN/09_peano_lab.md). M18 remains the latest staged
browser milestone; production remains untouched behind the M14 cache-header
blocker.

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
385-entry catalog has 23 `checked_existing`, 361 `checked_m20`, no remaining
planned theorem, and one representation-blocked
conventional integer-coefficient Bézout interface. A pinned Lean companion
independently checks conventional list-based FTA up to permutation. Remaining
M20's native arithmetic and synchronized release artifacts are complete. The
main Jupyter Book now includes a guided zero-to-FTA route, a quadratic
reciprocity campaign chapter, and a generated interactive 384-proof atlas;
the integrated local browser candidate deterministically verifies as build
`2026-08-04b`, application `a-903a05e31da9`, with 150 worker sources. Its
source inventory, content manifest, and deployment contracts pass; complete
local staging awaits the gitignored pinned vendor mirror. It is not deployed,
and direct attached-browser UI inspection remains
explicitly unclaimed. Model-v3 curriculum training is a separate milestone—not mathematical
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
forces at least 731,423 proof nodes. The preferred replacement is implemented
as an isolated 45-layer balanced-conjunction compiler whose output is one
ordinary existing `Proof` checked by the unchanged kernel. Its focused tests
pass `25/25`; an exact 557-node/1,787-edge dependency-consuming surrogate is
kernel-green at 19,066 nodes/depth 74, while false bodies against the actual
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
Static exact-topology evidence preserves the `19,066/74` proof receipt and now
adds `142,134/84` annotations/envelope depth; the actual-formula false scaffold
adds `157,579/92`. Bare `pa lib` no longer replays the ladder, and the browser
integrated worker inventory deterministically covers 149 Python sources. A
migration audit identifies 125 pre-admission absence assertions and the exact 317/29 public
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
navigable. Its persistent 557-page tag corpus has 1,787 dependency edges,
27,491 line-addressable tactic commands, 8,553 explicit theorem links, and a
separate foundations view for PA grammar, PA1–PA6, proof constructors, and
tactics. The permanent QR endpoint is `PA00FW`. The interface labels 240
public theorems, 316 body-checked candidates, and the one root awaiting
layered closure; it does not enroll any candidate. Source integration and 24
bounded explorer/Book/WMI-harness checks are complete. A fresh WMI Jupyter
Book build/integrity receipt and attached-browser interaction pass remain
publication gates, and the former frozen QR upload hash is stale after these
payload-changing additions.

Graph v2 now exposes the same closure as navigable premise paths: 557 theorem
nodes, 1,787 direct edges, 45 layers, and 48 theorem roots (corpus roots, not
PA axioms or kernel foundations). For `PA00FW` it records 101,278 distinct
root-to-target paths, a 4-vertex shortest witness, and a 45-vertex critical
depth witness. The Book endpoint is
`book/arithmetic-library/dependency-graph.md`, and the static explorer opens at
`book/_static/pa-proof-explorer/graph.html?target=PA00FW` with the exact proof
page one click away. This completes the static dependency-path presentation;
the generator owns all 1,123 files under a pinned aggregate, and the full
local Book build/integrity check is green. `PA00FW` remains pending layered
closure: WMI job `187187` failed at gate 5 on one redundant dependency, and
replacement job `210714` failed at gate 15 after a second direct-edge mutation
still checked. Neither fail-closed dependency-minimality result is a QR result;
attached-browser validation also remains a publication gate.

## Parallel Peano Hydra program

The adopted Hydra plan has a permanent product track and a sealed research
track. Both use only the curated Peano Lab object language. The product will
grow a reviewed elementary-number-theory library with exact direct dependencies, readable
scripts, best-known checked certificates, and generated documentation. Its
planned revisioned authoring assistant will turn accepted prose into candidate
PA statements, flag evidenced ambiguity or mistakes, open a Peano Lab proof
workspace, and export a reviewable patch only after explicit human acceptance.

Constructive PA is the default. Classical `PA+DNE` is a separately versioned,
visible mode; excluded middle may be a derived surface theorem, not a second
casually added kernel axiom. Native search is planned to perform dense closure,
Vampire is the initial external hint engine, and future separate small Qwen
LoRA roles will handle formalization, retrieval, sparse macro proposals,
ranking, and critique. All
remain untrusted. Rust native/WASM checking can accelerate candidate filtering,
but Python keeps final QED authority until the exact Rust accepted path is
refined to the Lean specification and survives the K5–K11 review/soak gates.

H0–H6 define the falsifiable experiment rather than another model demo. H0
freezes the exact logic/fragment and forbids a general Heyting-arithmetic
decidability claim. H1 freezes authoring contracts, an ordered library epoch,
and a lineage-separated benchmark under an independent owner. H2 establishes
the strongest native/Vampire proof-producing symbolic baseline before model
credit is possible. H3 requires deterministic checked macro and separately
adjudicated formalization corpora. H4 admits learned components only through
paired DEV gates. H5 is a one-shot `S` versus `S+R` versus full-Hydra
comparison at matched time, compute, energy, and cost; a failed preregistered
gate is reported as no demonstrated LLM advantage. H6 requires independent
reproduction. A0–A6 separately deliver the live authoring product.

The existing four-goal Qwen result is retained only as a launch regression,
not evidence for the campaign. Any later quadratic-reciprocity development
belongs to a new library epoch and, if used for evaluation, requires
whole-lineage masking. H0 completed 2026-08-04. Active semantic profile v2
(`4f2713e6a21e6261bbefe5991ef545e6356807e7042c6b2c7c07183e142c3b4b`)
and exact result schema v1
(`cf1caf1c867ddfbe3c247e42a18b730ea6790269718170a51f9733d5a7a36b26`)
freeze the theorem-prover-only `proved | unknown` claim, evidence fields, and
hash preimages. Typed macro protocol v1 compiles every action to public tactics
or isolated untrusted reconstruction. The retained H0 report
(`55c60502b2229f4420bd4557058842bebb582f491739e82a6dae06de5b803fdb`)
records two identical 384-theorem cold roots, 1,024 positives, exact pinned-Lean
agreement, all required mutation/trust-boundary rejections, and the complete
H0.3 typed-macro evidence bundle. No H1 benchmark is sealed, no Hydra training
claim exists, and no H5 result exists. The first H1/A0 protocol slices now
provide a 28-test canonical authoring boundary (digest
`31a344bbc0b22cfacf5803c85d25a80a0234cf7387395283c5e1ab25ada80553`)
and a 38-test live-candidate/epoch transition boundary (digest
`f4695013ee4aeb660abf3a1e57a6334d86c990a8904c4435d94628694a2e875b`).
Review registries are empty and the three-file epoch
fixture lacks formula/certificate bytes, so no living catalog has been
declared frozen `L0` and neither A0 nor H1 is complete. See
[`docs/PEANO_HYDRA_DESIGN.md`](docs/PEANO_HYDRA_DESIGN.md) and
[`PLAN/11_peano_hydra.md`](PLAN/11_peano_hydra.md).
