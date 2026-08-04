# Project Memory — VIASM 2026 "Automatic Theorem Proving in Mathematics"

> Durable facts about this project. One fact per bullet; update in place rather than duplicating.
> This is the human-and-agent-readable ground truth; the dated narrative lives in [`JOURNAL.md`](JOURNAL.md),
> the actionable breakdown in [`PLAN.md`](PLAN.md).

## Identity

- **What:** A 6-lecture mini-course *An introduction to automatic theorem proving in mathematics* for
  **VIASM** (Vietnam Institute for Advanced Study in Mathematics, Hanoi), 2026.
- **Author:** dr Bartosz Naskręcki — Faculty of Mathematics and Computer Science, Adam Mickiewicz
  University in Poznań (WMI UAM); also Centre for Trustworthy AI (CCAI), Warsaw University of Technology.
- **Active local repo root:** `/Users/bnaskrecki/codex/test/vietnam2026-arithmetic`
  (git branch `agent/quadratic-reciprocity-campaign`).
- **Public GitHub repo:** `nasqret/vietnam2026`.
- **VIASM course page:** <https://viasm.edu.vn/en/hdkh/Mini-Course_AIATPM>
- **Lecture-title doc (Google Docs):** `1w08zKuLrq3XLFEWS_jNN4ZZv6lkXJWHKgVUSBWYSI7A`.

## Deployment targets (faculty server)

- **Host / SSH:** `bnaskrecki@lts-faculty.wmi.amu.edu.pl` (key `~/.ssh/id_ed25519`, already in agent).
- **Landing page + book + slides:** `~/public_html/vietnam2026/` → <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026>
- **Browser Lambda Lab:** `~/public_html/lab-lambda/` → <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda>
- **Browser Peano Lab targets:** `~/public_html/peano-lab/` (production) and
  `~/public_html/peano-lab-next/` (staging). Production remains on verified M13 build
  `2026-07-27h`; staging serves M18 build `2026-07-28c` from commit `98ee0dd` and application release
  `a-953fa3777cd4`. Its exact HTML and all 41 application files match the staged bytes, but production
  promotion is stopped because
  account-level `.htaccess` did not emit the required cache policy; administrator-managed host/proxy
  headers or an explicit PHP-relay design exception is needed. The probe did not establish the
  central server's loaded-module inventory.
- **Server tooling:** Apache static hosting + PHP; Python 3.8, Node present. **No persistent daemons** →
  the lab must be **fully client-side** (this is why the browser lab uses Pyodide, not a server kernel).
- **Site/Lambda deploy verb:** `rsync -avz --delete <local>/ lts-faculty.wmi.amu.edu.pl:~/public_html/<target>/`.
- **Peano deploy rule:** retain old content-addressed `releases/a-*` and `vendor/v-*` paths; upload
  assets first without remote `--delete`, then publish the non-stored `index.html` pointer.

## The six lectures (working titles)

1. A general introduction to type theory
2. Simple calculations with the Church (λ-)calculus
3. Propositional logic proofs (via Emily Riehl's *A Reintroduction to Proofs*)
4. Introduction to Lean
5. Advanced Lean
6. Auto-formalization of mathematics with Lean (the **EML** project as flagship case study)

## Source projects reused (author's own)

- **`nasqret/falenty-2026`** — existing λ-calculus JupyterBook (`book/en/`, EN) + the Python
  **`lambda_lab`** (Typer CLI + prompt_toolkit REPL + Rich): commands `church reduce lam tour quiz kb
  peano curry_howard eml aristotle games tutorial`. Covers Lectures 1–3 material already. Uses the same
  MEMORY/JOURNAL/PLAN + JupyterBook documentation pattern this project mirrors.
- **`nasqret/eml-formalization`** — Lean 4 + Mathlib formalization of `arXiv:2603.21852`
  (Odrzywołek, *All elementary functions from a single binary operator*). 36/36 primitives, 100 public
  theorems, sorry-free, 8062 `lake` jobs; live **EML Tree Builder** demo at
  <https://nasqret.github.io/eml-formalization/>. This is the Lecture 6 case study.
- **`nasqret/classical-foundations-ann`** — **style/layout template**: JupyterBook (`_config.yml`/`_toc.yml`)
  + self-contained `index.html` hero landing page (Inter font, CSS-variable design system, EN/PL toggle,
  card grid) + per-part reveal.js `slides_*.html` + in-browser `applets/*.html`.

## Key architecture decisions

- **Browser lab = Pyodide-in-a-Web-Worker + xterm.js, fully self-hosted** (promoted 2026-07-24):
  evaluation off the main thread with a Stop control; all assets (Pyodide core, xterm+addons, fonts)
  served from the faculty server via `lab-lambda/vendor/` (`scripts/fetch_vendor.sh`), zero CDN.
  `/lab-lambda-next/` = staging. Desktop-only features (lake/lean verify, openai judge) degrade to
  notices; `lean` links out to Live Lean.
- **Lean metaverification boundary:** the separate
  [`nasqret/peano-lab-lean`](https://github.com/nasqret/peano-lab-lean)
  project proves `Derives.sound`, `check_derives`, `checkClosed_sound`, and
  `Artifact.check_sound` for the modeled checker over standard `Nat`, relative
  to Lean's kernel and reported axioms. WMI job `211445` seals the historical
  cut-free v1 snapshot. The production `Cut` rule and `peano-lab-v2` codec at
  source commit
  [`ab966fd1`](https://github.com/nasqret/peano-lab-lean/commit/ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2)
  passed pinned Lean 4.31/WMI job
  [`218358`](https://github.com/nasqret/peano-lab-lean/tree/8515336ab3b89ca6f0c8ab521d01745a220b5211/artifacts/wmi/218358):
  `COMPLETED`, `0:0`, `00:03:03`, 22 build jobs, 11 security tests, two
  artifacts, and 154 differential cases all passed. Python correspondence
  remains finite differential evidence, not exhaustive program equivalence.
- **Peano Lab = proof certificates + an independent kernel checker** on branch `peano-lab`:
  tactics are untrusted, every QED is rechecked against the original goal, tactic failures are
  transactional, and the kernel may not import the engine/UI. M0 landed a 196-line structural
  checker, de Bruijn syntax/substitution, all ND/equality/PA/IND certificate forms, and adversarial
  mutation tests. M1 adds immutable goal/hole states, rigid/flexible term unification, proof-wide
  substitutions, equational tactics, checked finalization with an external session-owned original,
  and stable v1 JSONL traces. M2 adds capture-safe universal introduction/specialization and two
  induction entry paths (fresh `forall` binder or named rigid context variable), both constructing
  explicit `Ind` certificates with scoped IHs. M3 adds the complete intuitionistic first-order
  tactic layer, scope-indexed witness metavariables, capture-safe rewriting beneath quantifiers,
  defined `≤` sugar, honest hints, and an explicit session-owned classical boundary: ordinary
  `check` remains intuitionistic, while visible `DNE` certificates require `check_classical`.
  M4 adds atomic hole-safe tactic combinators, proof-producing ordered simplification with an LPO
  termination gate, certified closed arithmetic separate from explicitly bounded semantic reports,
  and depth/node-bounded backtracking that replays only kernel-valid winning plans into traces. M5
  adds the self-hosted worker page, single-owner command router, deterministic goal/context/partial-
  certificate panels, and safe production/staging build targets. The owner retains the original
  theorem and classical authority outside `ProofState`; QED still passes only through independent
  finalization. Browser and JSONL text escape invisible controls and Unicode line separators. M6
  adds 28 replay-tested tactic/tactical cards, 13 immutable PA/kernel knowledge cards, and two
  ENTER-driven tutorials whose frozen proof commands run in isolated nested proof sessions and may
  complete only after checked QED. The book gate now routes `/peano-lab/?cmd=` links and `pa>`
  blocks to the Peano driver while retaining the Lambda gate unchanged. M7 adds a 20-entry scripted
  theorem library through the zero-product capstone. Earlier certificates are substituted by
  untrusted capture-safe cut elimination, then every resulting closed certificate is checked again
  against its original statement. `pa lib` exposes the dependency graph and authored script;
  `pa lean` emits an exact Lean 4 `Nat` statement, intentional proof stub, and Live Lean link. M8
  turns the dated implementation diary into a six-chapter Jupyter Book part covering staged PA,
  the De Bruijn trust boundary, tactic transactions, tacticals, induction/the ladder, and honest
  limits. Its 45 chapter commands and 15 live links replay through the real driver; the landing
  page now announces the checked browser lab as live. Six connected Obsidian concepts extend the
  vault without unresolved links. M9 adds deterministic checked trace generation, a strict v1
  session importer and theorem-group exporter, a committed 13,152-transition leakage-separated
  corpus, and a pinned four-family pass@k harness whose only success label comes from independent
  finalization. Generator/checker sources and complete run inputs are fingerprinted; policy-visible
  goals retain session-stable metavariable aliases and expose neither theorem labels nor logic-mode
  authority. The repository deliberately contains data and protocol, not model training. M10 adds
  live `use <library-theorem> [as <alias>]`: UI/library code resolves a cached replay, the engine
  rechecks its closed certificate and inserts a bounded local cut, and untrusted surface
  finalization contracts cuts before the unchanged independent checker sees the owner-held original
  theorem. Imports are ordinary hypotheses for `specialize`, `apply`, `rewrite`, `exact`, and
  `simp`; aliases share the Unicode identifier rules of binder tactics. Explicit proof node/depth
  budgets fail transactionally, and exact undo retains the raw pre-compilation state. M11 extends
  the twenty-entry core with exactly three checked semiring orientations: `one_mul`, `mul_one`, and
  `add_mul`. Their ordinary scripts replay from the empty context, their Lean stubs preserve the
  exact statements, and binder-capture tests validate the import/specialization path required by
  later certificate-producing normalization. M12 adds an argument-free, bounded `ring` tactic for
  rigid polynomial equality goals. It reifies sparse natural-coefficient polynomials but constructs
  every successful equality certificate from PA3--PA6 and rechecked M11 laws; the generated proof
  is checked before the tactic commits and again at QED. `ring` ignores local hypotheses by design,
  so conditional algebra remains explicit through `trans` and `rewrite`. M13 adds argument-free,
  bounded `norm_num` for equality goals, optionally under at most 64 leading universal binders. It
  computes only maximal closed numerical islands, constructs PA3--PA6/congruence certificates, and
  either closes by a checked bridge or transports one explicit residual goal. Its pure hint
  preflight simulates the exact immutable commit without consuming allocator state. Computation,
  generated proof, live partial proof, and wall-clock bounds fail transactionally; neither
  `norm_num` nor `ring` decides general PA or nonlinear consequences of hypotheses, and a future
  Presburger `omega` requires a separate certificate-producing design. The refreshed generator-v2
  corpus retains the v1 row schema: 13,344 unique transitions from 1,692 checked QED sessions, with
  a deliberately small 18-row same-family validation split used only as a pipeline check. M14 adds
  a transport-only browser boundary: content-addressed immutable application and vendor URLs,
  non-stored HTML published after its release assets, negotiated Brotli/gzip for WASM/source media, and
  concurrent source transfer with deterministic failure and mount order. It changes no proof rule,
  kernel dependency, certificate, corpus row, or server-side execution model. M15 adds an untrusted,
  undo-aligned proof-owner replay journal plus `script [download]`: active artifacts are explicitly
  unchecked and omit `qed`; only successful independent finalization retains a checked replay. The
  browser accepts a one-shot download only for the exact directly typed command and validates a
  fixed-name LF/UTF-8 payload. Exported text is neither certificate authority nor a mutable library;
  library inclusion retains the existing closed-statement, dependency, test, and independent-check
  workflow; the later reviewed self-contained Cut milestone replaces full dependency inlining.
  M16 introduces named local reasoning with the exact surface forms
  `have h : P` and `suffices h : P`. Engine-only `LocalHave` and `LocalSuffices` nodes preserve the
  two opposite visible goal orders, then a capture-avoiding untrusted compiler removes them before
  the unchanged kernel checks the session owner's original target. They add scheduling and naming,
  not a trusted cut rule, theorem environment, or proof-sharing guarantee. M16 is locally green as
  application release `a-f6c33c7840ad`, build `2026-07-28a`; it is not deployed.
  M17 is the locally green browser multiline-paste milestone. Its dialog and direct terminal-paste
  paths accept only a bounded complete replay (`pa prove ` first, exact `qed` last), ignore blanks,
  and submit commands sequentially to the existing session owner. Preflight bounds are 100,000
  characters, 256 nonblank lines, and `MAX_INPUT` per line. A failed line stops the suffix while
  preserving the successful prefix and per-command undo; preflight rejects `script` and the batch
  executor has no download authority. This is an untrusted input convenience, and independent QED
  is unchanged. Build `2026-07-28b`, application `a-404fdbdb55e4`, is deployed to staging with
  exact HTML/manifest/worker/driver bytes. Production remains `2026-07-27h`: the host still omits
  the required cache headers, so the delivery verifier blocks promotion.
  M18 is the locally green compact-certificate milestone. Its exact arithmetic surface is
  `compact_arith` or `compact_arith [h, <- k]` on one rigid equality. The optional list is the
  complete ordered set of local equalities the tactic may use; there is no hidden context mining.
  The phase-1 planner memoizes a finite grammar of PA3--PA6-oriented paths and checked recurrence
  templates. It does not invent an outer induction invariant or existential witness, and it adds no
  kernel constructor. The motivating readable `ring` replay expands to 30,030 proof-tree nodes;
  the existing hand-authored 180-node/depth-34 certificate is the current checked upper bound, not
  a proven absolute minimum. Focused/full acceptance, corpus provenance, documentation, manifests,
  and exact local staging are green at build `2026-07-28c`, application `a-953fa3777cd4`; the same
  bytes are deployed to staging. No in-app browser was attached, so a live Pyodide click-through is
  not claimed. The delivery verifier reaches the known missing-cache-header stop, so production is
  unchanged.
  M19 began as the post-training milestone; its narrow model-v3 launch smoke is
  now completed, while broader capability and induction evaluation remain open.
  Its compact headless adapter is not
  a second prover: one warm JSONL/Python process reuses the production parser, public surface,
  proof engine, theorem library, binding v1 trace logger, checked finalizer, and unchanged kernel.
  Its CLI is a bounded finite transaction (not a duplex service), with strict JSON numbers,
  all-or-nothing trace/result publication, propagated cancellation, and optional
  `--require-proved` CI semantics. Generation is traced; quiet verification is a separately named
  non-training path. A fixed
  capability-scoped `model-v1` environment excludes `auto`, `undo`, session commands, and held-out
  targets. Positive policy rows come only from complete QED sessions whose exact authored actions,
  states, proof size, original theorem, logic mode, and capability preimage replay to another
  kernel-checked QED. The first frozen training-scale release has 2,522 kernel-checked independent
  roots and unique canonical statements, exactly 10,000 positive rows across 29 schemas/five
  domains, and train/validation/test counts 8,149/926/925. Its aggregate SHA-256 is
  `1fa98caa2e0528d39c1b9003c4ee153dfbe633cb1ee4505e8f5b28eb837465dd`.
  Family/lineage/canonical-formula/exact-policy-prompt connected components prevent identical
  theorems or policy inputs crossing splits; the independent attestor rejects both formula and
  prompt overlap, recompiles the three byte-identical splits from raw source sessions under the
  current compiler and fixed environment, and reports zero frozen-target contamination.
  Training code pins Qwen3 1.7B and controlled 4B/Pythagoras comparisons, uses completion-only BF16
  LoRA, immutable model revisions, streaming hash validation, checkpoint-resume identity, and
  complete closed-directory hashes for every loader-visible adapter/tokenizer file. Evaluation
  derives its exact surface authority from the embedded dataset attestation. The first guarded
  prepare job failed before model loading because `ML-bundle/25.10` exposes, but does not install,
  its ARM Torch wheel. Dependency gating prevented training/evaluation and the stale jobs were
  canceled. The corrected isolated recipe pins `torch==2.9.1+cu129`, its transitive closure, binary
  wheels, and `pip check`. Replacement preparation job `20029964` passed on a GH200 from exact
  commit `41683e2`: the pinned Qwen3-1.7B revision downloaded, one BF16 LoRA step and adapter
  save/reload produced finite losses, and closed artifact hashes were recorded. Training job
  `20029970` then completed 100 steps in 9m51s (train loss 0.78446, final validation loss 0.13518),
  but evaluator `20029980` failed before generation because sorted manifest JSON conflicted with a
  construction-order parser. The corrected parser preserves exact fields, values, authority hash,
  and strict row-order checks. The model never enters the
  trusted computing base. WMI access is available through `hw_csi`; typed-A100 probe `171369` passed on an
  A100-SXM4-80GB. Its distinct x86-64/PyTorch-2.5.1/CUDA-12.4 route now has a reviewed central-base
  manifest, a 12-wheel hash-locked overlay, transactional deployment locks, and a one-shot
  safetensors model-weight contract. Full WMI preparation `171395` passed in 8m39s, including exact
  dataset replay and BF16 LoRA save/reload. Its first training submission was refused before
  `sbatch` when Bash whitespace splitting collapsed the empty dependency TSV field; a strict
  nine-field parser replaces that boundary. Fresh preparation/training/evaluation jobs
  `171414`/`171421`/`171423` then completed from commit `0c84fc3`. The immutable WMI manifest binds
  adapter `ff187542…` and records train/validation loss 0.78301/0.13615, but the kernel-judged
  held-out result is 0/4 at pass@4. Parity request `171428` also failed in 16 samples. A fresh
  direct-witness theorem absent exactly from every split succeeded once in eight samples under
  `171430`, exporting a seven-node checked proof. The dataset has no IH states, no foundation-lemma
  uses, and only 16/25 tactic heads, so model-v1 is an easy-schema baseline rather than a useful
  induction prover. The Helios ARM lock is never reused.

  The owner authorized the compatibility-tested 26-lemma candidate for publication. It now extends
  the checked catalog to 49 entries with source commit, catalog hash, exact MIT notice, deterministic
  cold replay, empty-context kernel checks, and a 21,515-node/depth-66 capstone. The kernel is
  unchanged; only the untrusted `use` import ceiling rises to 32,768. Model-v1 stays frozen. The
  public snapshot becomes model-v2's retrieval foundation, while every imported exact theorem is a
  retrieval/application target rather than a sealed benchmark.
  The active checkout is
  `/Users/bnaskrecki/codex/peano`.
- **Peano Hydra campaign protocol (2026-08-03):**
  [`docs/PEANO_HYDRA_DESIGN.md`](docs/PEANO_HYDRA_DESIGN.md) freezes a
  kernel-judged H0–H6 experiment before implementation. Standard Heyting
  arithmetic is not claimed decidable; any decision result requires an exact
  restricted fragment and independent negative evidence. H1 freezes an ordered
  library epoch (the historical 247-theorem corpus checkpoint or a later
  explicitly frozen successor) and a sealed
  lineage-separated benchmark; later mathematics, including the quadratic-
  reciprocity campaign, enters a new epoch. Native search,
  retrieval/ranking, Qwen, Codex, Vampire/E/SMT, translations, and
  reconstruction are untrusted. Generative actions occur only at symbolic
  critical frontiers through macros compiled to public Peano commands. The H5
  headline compares symbolic `S`, non-generative `S+R`, and full Hydra under
  matched resources; teacher-oracle DEV pilots and the historical four-goal
  smoke make no model or performance claim. The pre-H0 provider-neutral core
  now composes identified fixed, null, recorded, Qwen-compatible, or future
  Codex-compatible candidate heads through fixed quotas and exact-state gates;
  search validates every edge and a separate traced runner replays any QED.
  Its deterministic teacher-oracle pilot has a symbolic-only control
  (`exhausted`), a hybrid replay of the known 13-command/180-node proof
  (`proof`, kernel checked), and a mutated-transcript integrity lane
  (`exhausted`, therefore `unknown`). The committed report is explicitly
  plumbing evidence, not model capability or H0/H5 completion. Every
  surface-macro-v0 row is comparison-ineligible until raw model/resource
  evidence, provider attestations, and genuine frontier detection exist.
- **Four formal foundations, on purpose:** Lean 4 = CIC, Agda = MLTT, Rocq (ex-Coq) = CIC, Mizar =
  Tarski–Grothendieck set theory. The same statements are proved in all four to *show* the foundations.
- **Local tooling present:** Lean/`elan`/`lake` ✓ (proofs verifiable here), `jupyter-book` ✓, `gh` (as
  `nasqret`) ✓, `pandoc` ✓, Agda 2.8.0 ✓, Rocq 9.2 ✓ (compiled artifacts present — `artifacts/rocq/*.vo`,
  `artifacts/agda/*.agdai` — kernel-checked locally). **Missing locally:** Mizar and GHC.

## Verified tool versions (research pass, 2026-07)

- **Lean:** current stable **4.32.0** (2026-07-13); latest RC 4.33.0-rc1. This repo's Lean artifact is
  pinned to the locally-installed **v4.28.0-rc1** (builds here, sorry-free, no axioms); EML pins Lean 4.28.
- **Mathlib:** ≈ **283,067 theorems / 134,678 definitions**, **> 2 million lines**, ~772 contributors.
  Note: `polyrith` is **retired** (its Sage certificate server was shut down) — do not teach it; search
  via **Loogle / LeanSearch / Moogle**.
- **Agda:** **2.8.0** (2025-07-05), agda-stdlib 2.x (v2.3); intensional predicative MLTT.
- **Rocq:** **9.2.0** (2026-03-27). Coq was renamed *The Rocq Prover*; first Rocq release 9.0.0
  (2025-03-12). MathComp 2.5.0.
- **Mizar:** **8.1.15** with MML **5.94.1493** (2025-05-30): 1493 articles, 65,000+ theorems.
- **Verified landscape numbers:** IMO 2024 AlphaProof+AlphaGeometry 2 = **28/42** (silver);
  DeepSeek-Prover-V2 **88.9%** miniF2F; Goedel-Prover-V2 **88.1%** (pass@32). Full log in
  `research/fact_checks.md`.

## Conventions

- **Documentation set:** `MEMORY.md` (this), `JOURNAL.md` (ISO dates, Europe/Warsaw), `PLAN.md` + `PLAN/*.md`
  (L0 goals → L1 modules → L2/L3 tasks), the Obsidian `vault/`, and the JupyterBook `book/`.
- **Language:** the course is delivered in **English** (audience is international at VIASM).
- **Growing notes:** the book/vault are expected to grow lecture-by-lecture; build foundations first.

## Status pointers

- Build/deploy strategy chosen: **go live incrementally** (public GitHub + faculty URLs as pieces land).
- Session-1 scope chosen: **maximum parallel build** across all workstreams.
- See [`JOURNAL.md`](JOURNAL.md) for the current day's state and [`PLAN.md`](PLAN.md) for what's next.
- Peano Lab milestones M0–M18 are locally green on `peano-lab`; M19 is active. M16 adds named local reasoning and
  a readable checked parity replay; M17 adds bounded sequential multiline proof paste and is on
  staging. M18 adds checked PA-specific compact
  equality certificates while leaving invariant and witness choice visible. M14 production
  delivery remains blocked on administrator-managed cache headers, while M17 is published to
  staging. The implementation, checked corpus,
  construction book, Obsidian knowledge base, kernel-judged evaluation protocol, live checked-
  theorem reuse, and the historical 189-entry checked ladder (whose initial public-catalog/M20
  reconciliation produced a historical 63-entry release),
  certificate-producing `ring`, and bounded checked
  `norm_num` teaching surface are present. The odd-square induction closes through explicit
  `trans`/`rewrite` structure, while concrete coefficients can now be certified without obscuring
  the independent final check. M19's headless runner, first 10,000-row checked corpus, and policy
  infrastructure have focused green coverage. The real Helios environment/one-step LoRA smoke has
  passed. WMI typed-A100 probe `171369` also passed on an A100-SXM4-80GB; its independent
  x86-64/PyTorch-2.5.1/CUDA-12.4 route now has a reviewed central-base manifest, a 12-wheel
  hash-locked overlay, transactional deployment locks, and a one-shot safetensors model-weight
  contract. The WMI LoRA save/reload, 100-step training, frozen evaluation, and two arbitrary
  theorem probes are complete. Those model-v1/model-v2 results are historical.
  The current model-v3 chain instead records passing same-source preparation
  `217851`, completed 649-update training `217859`, trained evaluation `218171`,
  and the revision/configuration-pinned no-PEFT-reported comparison `218172`.
  Their narrowly admitted four-goal `k=1` launch smoke is 3/4 versus 0/4; the
  three trained claims kernel-replay, the induction goal remains unsolved, and
  no bit-for-bit base, statistical, causal, broad-PA, or induction claim follows.
- M19 pre-training infrastructure gate on 2026-07-28: 363 focused tests, 912 full Peano tests,
  Lambda 360 tests plus 36 subtests, clean book build/command replay, and green local staging as
  build `2026-07-28f`, application `a-69aa3b753965`. This is not deployed and is not a model result.
- M19 pre-result local gate on 2026-07-28: 140 focused trained-policy/WMI/arbitrary-proof tests and
  1,030 complete Peano tests. A trained adapter is usable on any bounded closed PA formula through
  an exact `model-v1` CLI that exports `.pa` only after a second kernel replay. WMI use goes through
  an immutable canonical request, SHA-256-only Slurm transport, durable request/job ledger, and
  allowlisted typed-A100 proof job. The adapter remains untrusted. The accepted WMI chain now has a
  reproducible negative hard-proof result (0/4 pass@4) and one positive shallow rollout result
  (1/8); exact hashes and the replayable proof live under `artifacts/peano-policy/`. A new local
  artifact regression adds three tests. The post-result gate is green: 1,033 complete Peano tests,
  Lambda 360 tests plus 36 subtests, a clean 27-source warning-as-error book build, 193 deep links
  and 170 documented commands replayed, and 412/412 Obsidian wikilinks resolved.
  At that checkpoint the remaining M19 work was the model-v2 curriculum/search
  experiment; the present next gate is a larger hidden induction-rich,
  kernel-checked benchmark under fixed pretrained/adapted/search budgets.

## Foundational arithmetic library (M20)

- M20 is a parallel library milestone on top of `peano-lab`, not a replacement for the active M19
  policy experiment. It organizes reusable facts as equality → semiring → order → divisibility →
  congruence → division → gcd → primes → factorization. The modulus-five fourth-power theorem is a
  downstream example rather than the organizing principle.
- The independently validated M20 branch snapshot grows its 23-entry base to 51 closed theorems:
  28 new equality congruence, additive cancellation and zero-sum, order-endpoint,
  zero-product/nonzero-product,
  small-factor, divisibility, non-divisibility, and generic quotient/remainder lemmas. It now
  includes `prime_two`, the first checked instance of the fully expanded prime predicate. Every
  script replays, every cut-free certificate passes the unchanged independent kernel, and the
  largest new certificate is 1,601 nodes/depth 59, within live `use`.
- The version-1 research catalog has 75 DAG nodes across nine domains: 23 `checked_existing`, 28
  `checked_m20`, 20 `planned_expressible`, and four `blocked_by_language`. Divisibility and
  primality can be expanded in current first-order PA. Full Peano FTA is not claimed before the
  selected finite-sequence/product representation and its proof spine have closed certificates.
- The FTA representation review selected sorted Gödel-β factor codes plus a second β-coded
  prefix-product trace. This is a conservative authoring design whose relations must expand to the
  unchanged PA language. A separate Lean 4.23.0/Mathlib companion now proves finite-list
  factorization existence for every nonzero natural and uniqueness up to permutation. Its pinned
  audit rejects `sorryAx` and reports exactly `propext`, `Classical.choice`, and `Quot.sound`; it is
  cataloged as one checked companion and is never imported as Peano theorem authority.
- Source policy is pinned and clean-room. NNG4 is Apache-2.0 and maps the early arithmetic ladder;
  Macbeth is reference-only because its repository lacks a reuse license; Weissman's notebooks are
  GPL-3.0 external algorithm indexes. Open Logic and Newstead supply openly licensed TeX references;
  Stein's elementary-number-theory TeX is reference-only because its repository has no license.
  No external source is vendored in M20.
- The synchronized knowledge surfaces are `PLAN/10_arithmetic_library.md`,
  `research/arithmetic-library/`, `book/arithmetic-library/`,
  `vault/moc/arithmetic-library-moc.md` plus generated `vault/lemmas/`, and
  `artifacts/peano-library/`. The generated snapshot binds exact source bytes, statements, scripts,
  dependencies, certificate hashes, proof metrics, and an ordered root digest; hashes are
  provenance, never theorem authority.
- The M20 branch validation record is 1,049 passing Peano tests on both Python 3.10 and
  Python 3.12, a warning-as-error Jupyter Book build over 34 sources, 197 checked deep links, 43
  documentation blocks with 253 replayed
  commands, and a clean 129-note/884-link Obsidian vault after integrating the latest `peano-lab`
  result-recording commit. The batch transport now enforces an explicit iterative 256-container
  JSON nesting limit, so malformed-depth behavior and session hashing are runtime-independent.
- M19 public-catalog local gate on 2026-07-28: 26 source-exact modular lemmas extend the ladder to
  49 entries; 1,036 Peano tests, Lambda 360 plus 36 subtests, all 27 book sources, 193 deep links,
  170 commands, and 414/414 vault wikilinks pass. Local browser candidate `2026-07-28g` has
  application identity `a-3ea7b7142aa0`; automated worker boot passes, direct in-app Pyodide
  latency remains unmeasured, and production is untouched.
- At the 189-theorem arithmetic checkpoint, the native runtime had 189 unique
  checked theorems: 23
  baseline entries, 154 general foundational entries, and twelve unique
  modular capstones. It now includes discrete order, multiplication
  cancellation/monotonicity, constructive quotient-remainder existence, full
  quotient-remainder uniqueness, zero-remainder/divisibility bridges,
  unit-factor/coprimality bridges, mutual-divisibility antisymmetry, and
  relational gcd uniqueness, constructive remainder-divisibility transport,
  both directions of Euclidean gcd invariance, constructive relational gcd
  existence by bounded induction, simultaneous balanced-natural Bézout
  witnesses, Gauss cancellation, the prime-divisor one-or-self API, and
  Euclid's lemma. The constructive prime-search layer adds equality and
  divisibility decisions, bounded factor search, prime/composite and prime
  decisions, nonzero/proper-factor interfaces, and bounded plus unrestricted
  prime-divisor existence. Balanced natural congruence is now transitive and
  additive, and the expanded Gödel-β decoding layer proves its successor
  modulus nonzero, constructs a bounded self-code, and proves decoded-value
  existence, uniqueness, and unique existence. The pre-CRT bridge now proves
  balanced congruence compatible with right, left, and paired multiplication,
  maps a directed remainder decomposition into balanced congruence, and maps
  every expanded β value to that congruence relation. Bounded congruent
  representatives are now equal, and the reverse bridge reconstructs a
  directed remainder decomposition from a nonzero modulus, bound, and balanced
  congruence. Consequently expanded β decoding is equivalent to a bound plus
  balanced congruence. The new subtraction-free CRT layer projects balanced
  Bézout identities, proves constructive binary CRT and its bounded-residue
  form, and constructs one code for two bounded β values under an explicit
  coprimality premise. The latest six admissions prove that two ordered β
  moduli are coprime when their index gap divides `c`, discharge the
  β-pair CRT premise under that condition, and construct a nonzero `c`
  divisible by every positive natural through a chosen bound. Unconditional
  pairwise coprimality is false: `c=1` at indices 1 and 4 gives moduli
  3 and 6. The latest seven admissions use the constructed common-multiple
  base to prove pairwise coprimality for every distinct pair in a bounded
  prefix, close coprimality under products on both sides, descend congruence
  from an accumulated product modulus to its factors, and prove one binary CRT
  extension preserves all earlier congruences. The latest six admissions add
  the right-factor divisibility witness, advance accumulated-product and
  decoded-congruence invariants together, fold them through every bounded
  prefix by ordinary induction, and project a common congruence witness for
  values already decoded from an existing `BetaAt` code. That final wrapper is
  not arbitrary finite-sequence coding. Under self-contained dependency
  sharing, the complete ladder contains 242,629 structural proof nodes and
  6,895 Cuts across 149 Cut-bearing entries.
  `bounded_beta_crt_for_existing_code` is largest by
  nodes and Cuts at 25,545/755;
  `prime_divisor_exists` sets the maximum depth at 80. The synchronized
  research catalog has 196 nodes (23 baseline checked, 166 post-baseline
  checked, three planned, four language-blocked) plus the separate Lean FTA
  companion. The generated vault has 268 notes and 2,513 resolved links,
  including 189 lemma notes. The
  object language, PA axioms,
  induction schema, and intuitionistic default are unchanged. The trusted
  proof grammar/checker now contains the reviewed self-contained
  `Cut(A,B,lemma,body)` rule: both formulas and both proof branches are embedded,
  with no theorem-name/hash authority. The checker is 247 lines. Its untrusted
  erasure utility is diagnostic and cannot round-trip every introduction-headed
  or induction-bearing certificate. The ordered snapshot root is
  `9650ae53f506c282daf84fca5e9c08d0d48bb36db813b4efc43f54156d25bf6b`.
  The local browser candidate is `2026-07-29h` / `a-98b1d8bb8dd7` and exposes
  all 189 entries. The current source suite passes 1,098 Peano tests on
  CPython 3.10 in 181.34 seconds. Lambda remains green at 360 tests plus 36
  subtests.
  The preceding checkpoint's 36-source book, 213 deep links, and 45 session
  blocks with 264 documented
  commands were also green. Those documentary counts have not been reused as
  a current 189-theorem book claim.
  The source-bound corpus retains 13,344 transitions/1,692 sessions under run
  fingerprint
  `a3c2f8c5c762b10fc9c1117723c74fecb50348cfb699f73bc76fb3714df3bf1b`;
  the isolated smoke has 378 sessions, 5,373 raw and 5,370 unique transitions,
  and all 189 authored QEDs. Peano FTA remains absent pending genuine
  prefix-product recurrence and bounds, arbitrary finite-prefix coding,
  greatest-prime descent, and the remaining finite-product spine.
  Production is untouched.
- **Historical M20 native FTA and unbounded-primes checkpoint (2026-07-29):** the runtime then contained
  247 unique closed theorems: 23 baseline, 212 general foundational entries,
  and twelve unique modular capstones. The synchronized 248-entry catalog has
  23 `checked_existing`, 224 `checked_m20`, no `planned_expressible`
  entry, and one `blocked_by_language` entry (the conventional
  integer-coefficient Bézout interface; balanced four-natural Bézout is
  checked). The conservative Gödel-β spine now includes finite-prefix
  recoding, exact prefix-product traces, `AllPrime`, adjacent sortedness,
  canonical append, greatest-prime-divisor descent, factorization existence,
  and extensional uniqueness. `prime_factorization_existence` checks at
  43,973 nodes/depth 98/1,328 Cuts;
  `prime_factorization_uniqueness` at 29,789/82/854; and
  `fundamental_theorem_of_arithmetic` at 73,767/99/2,184. The exact FTA
  certificate SHA-256 is
  `fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
  It checks from the empty context and through live `use`/`exact`/`qed`, uses
  only PA1–PA6 plus induction, and contains no DNE. All dependency-slot,
  authored-hypothesis, and PA-leaf mutations fail closed. The PA term/formula
  language remains unchanged, with no primitive lists or raw β-code equality.
  At that M20 checkpoint the untrusted import and live-proof gates were
  aligned at 100,000 nodes and depth 256; the later quadratic-reciprocity
  checkpoint replaces this with the dual policy recorded below.
- **Constructive prime unboundedness:** `prime_unbounded` constructs a nonzero
  common multiple through an arbitrary bound `n`, chooses a prime divisor of
  its successor, and proves that divisor is above `n`. If it were at most
  `n`, it would divide both the common multiple and its successor, hence one,
  contradicting primality. Its exact certificate has 4,595 nodes, depth 82,
  146 self-contained Cuts, and SHA-256
  `8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b`.
  It uses PA1–PA6 only, contains no DNE, and passes exact-statement,
  dependency-slot, PA-leaf, authored-hypothesis, and live-use audits.
- **Historical M20 generated identities (2026-07-29):** the 247-theorem snapshot contains
  982,534 structural nodes and 28,892 Cuts across 204 Cut-bearing
  certificates. Its ordered root is
  `eb4775dfd181dc5e45bec463a93f14b0ea9d02501c40c5167b7cae77cd4ff432`
  and source digest is
  `295ca3b65970324e7d2ed51b57dc4510227b0abbc2d35b68a809dbde26aba868`.
  The Obsidian graph has 327 notes and 3,288 resolved links, including 247
  lemma notes. The deterministic 1,692-session/13,344-transition corpus has
  fingerprint
  `6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`;
  its isolated smoke has 494 sessions, 9,235 raw/9,232 unique transitions,
  and all 247 authored QEDs. Local browser build `2026-07-29k` packages
  manifest identity `a-77df7c0860bc`; it is not staged or deployed. The strict
  book rebuild passes 38 sources with no warnings; 194 deep links and 47
  executable blocks containing 287 commands verify. A guided ten-stage route
  and generated interactive atlas expose all 247 exact statements, complete
  authored proof recipes, dependencies, dependents, metrics and source/vault
  links. The complete Peano suite passes 1,298 tests with one intentional skip
  in 1,275.58 seconds; Lambda passes 360 tests plus 36 subtests. An in-app
  browser was unavailable, so direct Pyodide and rendered
  book UI smokes are not claimed; automated runtime/worker tests, static HTML
  contracts and the deployment-manifest check remain green.
- **Quadratic-reciprocity campaign checkpoint (2026-07-29):** the exact
  sign-free same/opposite/combined reciprocity endpoints are expressible in
  unchanged first-order PA; the combined expanded target is 1,520 source
  characters. The runtime has 133 new checked campaign theorems covering
  parity, constructive residue decision, finite folds and congruence,
  factorial and power algebra, modular units, small-modulus classifications,
  sign and half-range bridges, β-prefix swap/reindex, constructive finite
  pigeonhole, replacement balance, and exact swap-last product invariance.
  At that checkpoint the runtime had 380 closed theorems (23 legacy, 212
  general foundational, twelve modular capstones, 133 quadratic-residue
  foundations). Four later public support lemmas bring the current total to
  384 while reciprocity itself remains unproved. The next dependency gate is
  general product invariance under finite permutations, followed by
  Wilson/Fermat/Euler, Gauss, and Eisenstein counting.
- **Constructive sum-parity API (2026-07-30):** four isolated bodies prove
  that an even sum has same-parity summands and an odd sum has opposite-parity
  summands, then package both iff statements. Nodes/depth are `61/18`,
  `61/18`, `63/19`, and `63/19`; focused tests pass `4/4` in 0.40 seconds.
  The bodies are fully expanded, no-DNE, unregistered candidate evidence for
  the final lattice-count parity extraction, not admitted theorems.
- **Dual certificate availability policy:** live and imported certificates
  admit at most 500,000 structural occurrences, 100,000 distinct proof
  objects, and depth 256. This changes no kernel rule or PA syntax. The FTA
  certificate has 73,767 occurrences but 8,701 objects. Proof substitution
  and surface cut normalization must memoize by input identity: without that,
  normalizing two shared FTA branches inflated to 109,150 objects; with
  memoization the checked result has 139,203 occurrences, depth 99, and 8,274
  objects. Exact boundary, one-past-boundary, compact interactive-QED, and real
  two-FTA regressions cover the policy.
- **Current quadratic-residue snapshot identities:** the 384-theorem
  snapshot contains 1,806,923 structural occurrences and 52,626 Cuts across
  329 Cut-bearing certificates. Its ordered root is
  `73b31b4775d24b6bb9730f2f2df37409aa56dc771fe3e1d0f9de5134b166e89b`.
  The synchronized research graph has 385 records (384 checked and one
  language-blocked conventional interface). The Obsidian vault has 482 notes
  and 4,886 resolved links, including all 384 generated theorem notes. The
  integrated local browser candidate deterministically verifies as build
  `2026-08-03a`, application `a-ff0ad1985520`, with 149 worker sources; it
  assembles successfully in the local content-addressed stage and is not
  deployed.
- **QR heavy-execution boundary (2026-07-30):** proof replay, certificate
  profiling, mutation audits, full-ladder tests, and documentation builds run
  on WMI from content-addressed dirty-worktree archives; the Mac is restricted
  to source inspection and text authoring. A queued Slurm job is not theorem
  evidence. A candidate enters the registry only after a discovery report is
  validated, exact hashes and structural/identity metrics are pinned, and a
  separate immutable admission snapshot passes from the empty kernel context.
  Jobs `172707` (`e4a0ff3909b9704...`) and `172716`
  (`27cf34986f0b7f0...`), followed by residue-map discovery job `172722`
  (`0d050e5d631a080...`) and scale-product discovery job `172737`
  (`08cb916fee48cfd5...`), were still pending at the recorded checkpoint.
  Focused residue-reindex job `172769` and product-balance job `172770` share
  immutable source snapshot `c6e6cabbbaf8b617...`; both were later cancelled
  stale after zero CPU.
  The five-gate `fermat-endpoints` suite was submitted as discovery job
  `172837` from immutable snapshot
  `c7cc39f94b2cb0ae5542f89b3ddec947d84c55627168e07851c62da36f51bd34`
  on `cpu_idle` with 1 CPU, 32768 MiB, and `04:00:00`; it too was cancelled
  after zero CPU. Corrected snapshot
  `73d2863a0138c8dce1f8a7f2793bcd96f543e389c0c4af6cce75cc13005ac3d9`
  carries replacement jobs `172988` (reindex, 16 GiB/2 hours), `172989`
  (balance, 16 GiB/2 hours), and `172990` (endpoints, 32 GiB/4 hours). All
  were pending at submission, so there is no validated pass or admission.
  Superseded job `172734` was cancelled pending with zero CPU time after its
  helper hygiene was strengthened; its archive is provenance only.
- **Active Fermat-first route:** general product reindexing, all eight
  residue-product rungs, and both endpoint corollaries now exist as isolated
  candidates. The constructive sequence is successor recoding, canonical
  nonzero multiplication remainders, a bounded injective residue map with
  alignments, pointwise scale extraction, product balance, and coprime
  cancellation. Wilson is a later and strictly stronger involution/pairing
  gate; it is not a prerequisite for Fermat.
- **Fermat body preflight:** all 21 finite-product plus Fermat candidate bodies
  now pass. Preflight fixed a missing second rewrite in
  `beta_successor_range_reindex_aligned` and removed an invalid locally
  repackaged `hprojection` in `prime_mul_residue_product_balance`. Key body-
  only nodes/depth are reindex aligned `86/34`, scale `62/32`, reindex exists
  `106/40`, balance `93/39`, predecessor Fermat `93/34`, and all-input Fermat
  `104/30`. Nine bounded structural gates pass across reindex, balance, and
  endpoints—three per suite. The reusable
  `candidate_validation.replay_candidate_bodies` helper kernel-checks
  dependency-curried scripts without replaying/closing dependencies and
  returns structural/identity metrics; its three unit tests pass. This helper
  is explicitly non-admitting. These body-only/structural receipts are not
  closed-certificate admission and admit no theorem.
- **Isolated Fermat endpoints:** `fermat_predecessor_exponent_mod_one` cancels
  the exact nonzero-residue product using `prime_range_product_coprime` and
  `mod_eq_cancel_coprime`. `fermat_little_all_inputs` then uses successor-power
  decomposition and the constructive `prime_coprime_or_divides` split to
  cover both coprime and divisible inputs. Both remain outside the registry;
  WMI discovery and a later receipt-pinned admission replay are still
  required.
- **Isolated Wilson square-one gate:** `prime_bounded_square_one_cases` writes
  positive `x` as `S t`, converts the balanced congruence into
  `p | t * (t + 2)`, applies `euclid_prime_dvd_product`, and uses the strict
  bounds to derive `x = 1 \/ x = n`. The candidate no longer uses the
  UI-only `ring` tactic: the square normalization is an explicit native
  equality/rewrite derivation. Its exact 16 direct dependencies are
  `ne_zero_of_one_le`, `nonzero_is_succ`, `mul_succ_left`, `add_assoc`, `add_comm`,
  `add_left_cancel`, `factor_difference`, `euclid_prime_dvd_product`,
  `le_succ_self`, `lt_of_le_of_lt`, `zero_or_succ`,
  `divisor_le_nonzero`, `lt_not_le`, `succ_ne_zero`, `le_antisymm`, and
  `succ_injective`. The body-only laptop receipt is 182 nodes/depth 48, and
  its three bounded structural gates passed. Original five-gate WMI discovery
  job `172855` was bound to snapshot
  `396af02c5aa4fdf62d4c3484f8a2c711b03c489cad498c121d0402ce3ee79981`
  but was cancelled after consuming zero CPU. Replacement job `172966`, from
  common snapshot
  `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
  is `PENDING (Priority)` with zero CPU. Body-only and structural local checks
  are not closed-certificate admission: there is no WMI pass, pinned receipt,
  or new theorem admission.
- **Zero-based Wilson inverse candidates:** for `p=S n`, `InvIdx(p,n,i,j)`
  expands to `i<n /\ (j<n /\ (S i)*(S j) ≡ 1 (mod p))`, with both bounds and
  congruence witness fully expanded in PA. `InvPrefix(p,n,b,c,l)` says every
  `i<l` β-decodes some `j` satisfying `InvIdx`; position/value indices denote
  residues `S i`/`S j`. Four source-only pointwise candidates are
  `prime_inverse_index_exists` (dependencies `succ_ne_zero`, `succ_le_succ`,
  `prime_bounded_nonzero_mod_inverse`, `nonzero_is_succ`,
  `le_of_succ_le_succ`), `bounded_mod_inverse_unique` (`mod_eq_symm`,
  `mod_eq_mul_left`, `mod_eq_mul_right`, `mul_assoc`, `mul_comm`, `mul_one`,
  `one_mul`, `mod_eq_trans`, `mod_eq_bounded_unique`),
  `bounded_inverse_index_unique` (`succ_le_succ`,
  `bounded_mod_inverse_unique`, `succ_injective`), and
  `inverse_index_symmetric` (`mul_comm`). Three source-only prefix candidates
  are `prime_inverse_prefix_extend` (`prime_inverse_index_exists`,
  `beta_prefix_extend`, `finite_lt_succ_eq_or_lt`),
  `prime_inverse_prefix_exists_bounded` (`add_eq_zero_right`, `succ_ne_zero`,
  `lt_to_le`, `prime_inverse_prefix_extend`), and
  `prime_inverse_prefix_exists` (`le_refl`,
  `prime_inverse_prefix_exists_bounded`). Their five-gate
  `wilson-inverse-prefix` suite recursively closes the seven-candidate stack.
  Original discovery job `172899` was bound to snapshot
  `1a11442b18dd6c40b49975e16f0b2062be57fade347acca20d87dba27e6adffc`
  but was cancelled after zero CPU when cheap body replay exposed two
  existential-binder errors. Those errors are fixed in exact snapshot
  `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`;
  replacement job `172975` is pending. It has no pass, pinned metric receipt,
  or admission effect.
- **Isolated Wilson involution layer:** six candidates now provide
  `inverse_prefix_entry_sound` (`beta_at_unique`),
  `inverse_prefix_extensional` (`bounded_inverse_index_unique`),
  `inverse_prefix_involutive` (soundness, `inverse_index_symmetric`, and
  extensionality), `inverse_prefix_injective` (involution and
  `beta_at_unique`), `inverse_prefix_surjective` (involution), and
  `prime_inverse_prefix_fixed_cases` (soundness, `succ_le_succ`, square-one
  classification, and `succ_injective`). The first five are prime-free; only
  the last assumes primality and concludes `i = 0 \/ S i = n`. The original
  five-gate `wilson-inverse-involution` discovery job `172920` targeted the
  14-spec recursive surface from snapshot
  `cfa4eea18d4a746a49a2d7579f217dbd65a27a79df61c76e8dba49079ba1aaa4`
  but was cancelled after zero CPU. First replacement `172967`, from snapshot
  `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
  was also cancelled after zero CPU when the prefix dependency changed.
  Corrected job `172976`, from snapshot
  `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
  is pending. It has no pass, pinned metric receipt, or admission effect.
- **Isolated Wilson endpoint layer:** three further candidates expose the
  actual fixed entries of the full inverse prefix. `inverse_prefix_zero_fixed`
  proves `At(b,c,0,0)` from `p=S n`, `n=S k`, and the full prefix;
  `inverse_prefix_last_fixed` proves `At(b,c,k,k)` using checked
  `predecessor_square_mod_one`; and
  `prime_inverse_prefix_exact_endpoints` packages an existential `k` with
  `n=S k`, both entries, and the converse classification
  `i<n -> At(b,c,i,i) -> i=0 \/ i=k`. At prime `2`, `k=0` and the endpoint
  facts intentionally coincide; no distinctness is claimed. The focused
  five-gate `wilson-inverse-endpoints` suite recursively closes 17 isolated
  specs. Original discovery job `172927` was bound to snapshot
  `7083e3876cc54daa782153aa6e1a2554aa75fa5a40cce3d6cf6b5971979dc35d`
  but was cancelled after zero CPU. First replacement `172968`, from snapshot
  `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
  was also cancelled after zero CPU when the prefix dependency changed.
  Corrected job `172977`, from snapshot
  `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
  is pending. The three bounded structural gates passed locally; both cold
  recursive replays, profiling, no-DNE/capacity checks, and mutations remain
  WMI-only. There is no discovery result, pinned receipt, or admission.
- **Isolated Wilson nonendpoint-orbit layer:** two source-only candidates now
  establish the first general inverse orbits beyond the fixed endpoints.
  `prime_inverse_prefix_nonendpoint_not_fixed` turns the fixed-case
  classification into `NonEndpoint(i,n) -> i != j` for a decoded mate `j`.
  `prime_inverse_prefix_nonendpoint_mate` combines that fact with involution,
  the two decoded endpoint entries, prime successor shape, successor
  injectivity, and β uniqueness to prove `NonEndpoint(j,n)` as well. The
  premise explicitly excludes `i=0` and `S i=n`; it neither asserts that the
  endpoints are distinct nor invents a nonendpoint at prime `2`. Its focused
  five-gate suite recursively closes 19 specs. Local syntax and the first
  three bounded cheap gates passed; heavy replay, profiling, no-DNE/capacity,
  and mutation work is WMI-only. Cheap body replay caught and fixed an
  apply-to-negation error in the orbit source. Original discovery job `172932`
  was bound to snapshot
  `5463565294da6d757356985a0e8d353ad2e0e16ca1b21b99d2aa5cfa6bb5c6f6`
  but was cancelled after zero CPU. First replacement `172970`, from snapshot
  `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
  was also cancelled after zero CPU. Corrected job `172978`, from snapshot
  `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
  is pending. There is no result, pinned receipt, or admission.
- **All-stack Wilson body checkpoint:** all 19 Wilson candidate bodies now
  pass the cheap replay. Nodes/depth in layer order are square `182/48`;
  point `55/22`, `70/28`, `50/21`, `20/12`; prefix `76/29`, `64/25`,
  `29/16`; involution `44/23`, `49/25`, `80/29`, `55/29`, `31/22`,
  `83/31`; endpoints `76/23`, `54/23`, `104/32`; and orbit `45/26`,
  `206/40`. Twelve bounded structural gates pass across prefix, involution,
  endpoints, and orbit—three per suite. These are body-only and structural
  receipts, not closed recursive replay or admission.
- **Isolated Wilson pair-product layer:** two source-only candidates provide
  the generic even-prefix fold needed after inverse entries are reindexed.
  `beta_product_double_succ_decompose` splits a product of length `S(S k)`
  into its `k`-prefix and final two factors;
  `beta_adjacent_unit_pairs_product_one` proves that the exact product of
  `m+m` β-decoded factors is congruent to one modulo `p` when every adjacent
  pair is. All five focused gates passed locally in 5.4 seconds, including two
  cold passes: the decomposition measured 1,317 nodes/depth 63/844 objects and
  the capstone 4,372 nodes/depth 64/1,290 objects. Graph SHA-256 is
  `622496753bd474f9f64d5d3001424d3c4513d43d6a5256022cd5a172167959ec`;
  source SHA-256 is
  `193fe015b32ffde4d93e00720c9fef510a804228e24f19f5cc6c97e8ad5fa724`.
  WMI job `172946` is bound to exact snapshot
  `9d890542b964d40580ad2f8f77fa83455de3b9af0f8ca905a37f6a6ee278e296`
  and is queued/pending on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`.
  The local pass does not replace the independent WMI admission receipt; no
  WMI pass or admission is claimed. Jobs `172936` and `172943` were cancelled
  before start as superseded known-broken snapshots, each exposing a separate
  missing third length rewrite, and supply no evidence.
- **Signed-half and finite-omission discovery checkpoint:** the isolated
  signed-half source now contains `odd_upper_remainder_reflection` and
  `gauss_pointwise_signed_half_representative`; their body-only receipts are
  respectively 125/34 and 116/38 nodes/depth. The finite-omission source adds
  eight candidates in dependency order with body-only nodes/depth
  `73/22`, `69/27`, `58/23`, `21/15`, `89/31`, `149/43`, `24/16`, and
  `27/18`. For each of `wilson-square-one`, `gauss-signed-half`, and
  `finite-omission`, the three bounded structural gates—contract/dependency,
  hygiene/native/witness, and graph/core/source isolation—passed locally.
  WMI jobs `172964` (`gauss-signed-half`) and `172965` (`finite-omission`),
  from common snapshot
  `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
  are both `PENDING (Priority)` with zero CPU. These body-only metrics and
  structural checks are not closed recursive replay or closed-certificate
  admission, and no new theorem is admitted.
- **Wilson blockers after generic pair products:** split the coincident
  prime-two case, β-reindex the nonendpoint inverse orbits into adjacent pairs,
  restore the fixed endpoint factors, and build the final exact factorial
  bridge. At that checkpoint the WMI runner exposed 11 focused five-gate
  suites and an 86-gate full audit across 19 source modules.
- **Reversible WMI queue prioritization:** superseded full jobs `172707`,
  `172716`, `172722`, and `172737` are user-held, not cancelled, so focused
  prerequisite discoveries can run first. Release those holds only after the
  focused results settle.
- **Isolated Gauss signed-prefix layer:** seven source-only candidates now
  turn the pointwise signed-half representative into aligned beta codes for
  positive magnitudes and zero/one sign bits, specialize the construction to
  the full half range, project canonical `AllBits`, and obtain relational
  `BitCount` existence. The seven new dependency-curried body metrics are
  `73/27`, `133/39`, `164/47`, `70/31`, `33/22`, `35/25`, and `31/26`
  nodes/depth. A 60-second-capped body replay of these plus the two earlier
  signed-half candidates passed in about 1.8 seconds after fixing one missing
  explicit negation binder. The new `gauss-signed-prefix` WMI suite adds five
  closed-replay/profile/mutation gates; at that checkpoint the runner had 91
  gates across 20 source modules and 12 focused suites. No closed WMI result
  or admission is claimed. The exact next mathematical boundary is
  magnitude-prefix permutation; product/sign parity and Gauss's lemma remain
  unproved.
- **Euler scaled-inverse entrance:** ten isolated native-PA candidates now
  construct and uniquely characterize the bounded relation
  `x*y == a (mod p)`, prove symmetry and involution, identify fixed points
  with square roots, and make the relation fixed-point-free under `~QRes`.
  Their dependency-curried body nodes/depth are `36/17`, `30/19`, `58/25`,
  `126/34`, `74/24`, `31/12`, `28/19`, `38/15`, `17/15`, and `24/15`.
  A three-candidate follow-on now constructs the complete beta-coded map on
  sources `1,...,p-1`: extension, bounded existence, and full existence pass
  at `105/36`, `81/33`, and `40/23`, with a `4/4` focused capped audit. The
  next five bodies establish decoded soundness/extensionality, nonresidue
  fixed-point freedom, bounded mate predecessors and decoded involution at
  `58/25`, `54/26`, `36/27`, `67/36`, and `91/39`; decoded injectivity adds
  `77/36`. That capped audit passes `4/4`. A generic fixed-target adjacent-pair
  fold now proves that the exact `2*m`-entry product is congruent to a
  relational `a^m` witness; its 118-command body checks at `171/47` and its
  focused no-DNE audit passes `4/4` in 1.71 seconds. The actual-residue branch
  of Euler is body-green too: `mod_eq_zero_to_dvd_nonzero` (`48/18`) supplies
  the general congruence/divisibility bridge, and
  `quadratic_residue_half_power_mod_one` (`148/39`) derives `a^h == 1` from a
  square witness using Fermat and relational power algebra; its `4/4` audit
  takes 2.11 seconds. The structural nonresidue route now has a correct
  shifted-closure entrance because the raw scaled map decodes actual residues
  `S j`. Four one-orbit bodies at `34/20`, `184/40`, `107/38`, and `190/52`
  choose omitted distinct involutive mates and append them while preserving
  shifted closure and order-prefix injectivity; their no-DNE audit passes
  `3/3` in 2.78 seconds. Ten follow-on bodies now establish the empty shifted
  state/history, history-preserving pair append, balanced-length arithmetic,
  full paired iteration, terminal packaging, and terminal coverage. Their
  nodes/depth are `23/19`, `19/15`, `114/31`, `49/18`, `125/40`, `80/24`,
  `40/15`, `155/39`, `41/25`, and `64/26`; the focused exact-contract,
  hygiene, registry-isolation and no-DNE audit passes `4/4` in 4.72 seconds.
  The replay corrected composite-length parenthesization, simplification
  order, typed terminal specialization, both injectivity-bound rewrites, and
  hygienic formula generation as authoring defects. The product/sign endpoint
  is now body-green too. Five bodies align successor-lifted adjacent targets
  with the exact factorial, apply Wilson and the generic power fold, package
  terminal nonresidue pairing, and prove the bounded endpoint at `132/39`,
  `144/45`, `136/52`, `61/34`, and `49/30`; focused tests pass `4/4` in 4.39
  seconds and the related Euler run passes `16/16` in 12.19 seconds. The
  strongest result assumes `p=S n`, `n=h+h`, `0<a<p`, `~QRes(p,a)` and
  `Pow(a,h,A)`, and concludes `A == n (mod p)`, i.e. `A == p-1`. Bounded
  equivalence is now body-green too. Seven package bodies derive `p` not
  dividing a bounded nonzero `a`, exclude `1 == p-1`, establish the
  constructive dichotomy, prove both residue and nonresidue iff directions,
  and expose the complete bounded criterion at `20/13`, `65/19`, `56/25`,
  `120/39`, `92/30`, `91/37`, and `80/31`; focused tests pass `4/4` in 1.67
  seconds and the combined bounded Euler run passes `12/12` in 7.62 seconds.
  Arbitrary-unit reduction is now body-green too. Six bodies construct the
  canonical nonzero remainder, transport `QRes`, transport relational powers,
  and prove both arbitrary iff statements plus one combined endpoint at
  `49/20`, `38/17`, `29/22`, `140/36`, `146/37`, and `75/29`. The focused
  audit passes `4/4` in 2.04 seconds and the combined Euler run passes `16/16`
  in 9.96 seconds. The final endpoint needs only `p=S n`, prime `p`,
  `p` not dividing `a`, `n=h+h`, and `Pow(a,h,A)`. WMI closure, mutations and
  admission remain. These are body-only receipts: the candidates remain
  unregistered and no Euler theorem is admitted. See
  `research/arithmetic-library/euler-scaled-inverse.md`.
- **Wilson PairOrder extension:** nine isolated candidates provide generic
  two-entry β-prefix append/reflection, constructive unused-nonendpoint
  choice, unused inverse-orbit extraction, preservation of orbit closure,
  nonendpoint range and injectivity, and a Wilson-specific choose-and-append
  step. Their body nodes/depth are `63/27`, `115/32`, `113/30`, `138/43`,
  `34/20`, `167/38`, `63/31`, `202/36`, and `191/53`. The representation,
  exact limits and Euler reuse are documented in
  `research/arithmetic-library/pair-order-encoding.md`. The later iteration,
  terminal coverage, successor lift and canonical nonendpoint product
  transport are now body-green; only endpoint restoration and recursive WMI
  review remain on this Wilson product route.
- **Common focused WMI tranche:** exact snapshot
  `8c9c4ae067b0dc202684e410bee563cd592a67080cb7c9939440ae8b44d4bccd`
  produced pending zero-CPU jobs `173015` (`euler-scaled-inverse`), `173016`
  (`gauss-signed-prefix`), and `173017` (`wilson-pair-order`). All three
  remote `--test-only` validations returned exit zero after the transport
  changed from `bash -l -s` to `bash -s`; the login-shell logout hook had
  previously overwritten an otherwise successful validation status. At this
  first frozen checkpoint the runner selected 101 gates across 22 test-source
  modules and exposed 14 focused five-gate suites plus `full`. Laptop work is
  limited to static gates
  and dependency-curried body preflight under a hard 60-second cap; recursive
  closure, profiling, mutations and book builds remain WMI-only. Pending is
  not a proof result or admission.
- **Second frozen QR checkpoint:** exact snapshot
  `fd129d34bf4a31a131a28d55bc6a16153984e0d37ac24dcefe7c2735cfb058d1`
  produced pending zero-CPU jobs `173021` (`gauss-magnitude-permutation`) and
  `173022` (`wilson-pair-order-induction`). The live runner now selects 111
  gates across 24 test-source modules and exposes 16 focused five-gate suites
  plus `full`. Neither pending job has produced a proof result or admission.
- **Prepared third QR replay surface:** the runner now exposes 121 gates
  across 26 test-source modules and 18 focused five-gate suites plus `full`.
  A local-only frozen two-suite archive contains 197 regular files, is
  3,552,256 bytes, and has SHA-256
  `938b212fb594708f7cee05c12a10e7c709110619b70d71b3200a27e6e85ede1b`.
  It selects `gauss-sign-factor-recode` and
  `wilson-pair-order-iteration`, each at 1 CPU, 16384 MiB, and `02:00:00`,
  and excludes all six newer untested bridge modules. Static/dry-run checks
  pass under a 60-second cap. The archive has not been transferred and no job
  has been submitted; explicit authorization of this exact upload is still
  required.
- **Magnitude permutation and composed product frontier:** eleven isolated candidates
  prove magnitude range, same/mixed-sign collision control, injectivity,
  predecessor recoding and finite surjectivity. Body nodes/depth are `39/25`,
  `48/24`, `96/34`, `169/50`, `626/70`, `157/45`, `31/25`, `87/30`,
  `48/20`, `60/31`, and `39/21`; see
  `research/arithmetic-library/gauss-magnitude-permutation.md`. Three further
  product-alignment bodies are green at `51/28`, `127/39`, and `72/34`, and
  two sign-product/power bodies at `35/24` and `259/46`. Sign-factor recoding,
  pointwise-product recoding, and signed product congruence are now body-green.
  The composed balance and constructive-cancellation bodies prove
  `A*P == P*R (mod p)` and then `A == R (mod p)` at `148/70` and `156/87`
  nodes/depth. `gauss_lemma_power_congruence_exists` now packages every hidden
  code/product witness and exposes `e,A,R`, the two relational powers, signed
  `BitCount` evidence, and `A == R (mod p)` at 258 nodes/depth 83. This is
  dependency-curried evidence for the power-congruence form of Gauss's lemma,
  not recursive closure, actual-QRes equivalence, or admission.
- **Bounded PairOrder state and coverage:** fifteen follow-on candidates add
  boundedness to the four-part state, establish empty/base facts, preserve the
  state under pair append, and prove terminal nonendpoint coverage. Their body
  nodes/depth are `95/40`, `19/12`, `69/27`, `90/42`, `23/19`, `18/14`,
  `20/16`, `22/18`, `64/19`, `8/8`, `12/9`, `266/44`, `33/20`, `72/37`,
  and `51/36`. A corrected iteration carries explicit adjacent inverse-pair
  history; its seven bodies pass at `34/16`, `38/17`, `19/15`, `114/31`,
  `122/40`, `169/39`, and `52/26`. Four successor-lift/product bodies pass at
  `17/11`, `124/38`, `41/31`, and `65/32`, ending in a paired product
  congruent to one. Four terminal transport bodies then extract the canonical
  nonendpoint range and prove exact product equality at `80/30`, `152/42`,
  `79/39`, and `188/65`; their focused test passes `3/3` under the laptop CPU
  cap. Seven endpoint-restoration bodies then prove the exact factorial Wilson
  congruence; nodes/depth are `30/15`, `258/45`, `63/29`, `21/16`, `104/30`,
  `94/35`, and `110/31`, with a `3/3` focused audit. Prime `2` is a separate
  branch and never invokes the odd PairOrder. Wilson is therefore body-green,
  while recursive closure/admission remains; see `pair-order-encoding.md`.
- **Eisenstein division-prefix entrance:** the generic native
  `DivisionPrefix` relation now beta-encodes aligned quotient and bounded
  remainder prefixes for any finite beta source. The extension/existence
  bodies pass at `132/41` and `71/30` nodes/depth (`94` and `62` commands),
  and the focused capped audit passes `4/4`. Three follow-on bodies construct
  an exact `a*(1+i)` half-range source, its quotient/remainder trace and its
  quotient `Sum` at `34/24`, `71/40`, and `52/28`; that audit also passes
  `4/4`. Three further bodies rule out equality and constructively orient
  every distinct-odd-prime half-rectangle cell at `72/30`, `77/34`, and
  `53/34`, with another `4/4` capped audit. Seven row-indicator/count bodies
  then pass at `46/29`, `71/27`, `58/23`, `53/34`, `27/16`, `43/23`, and
  `63/29`, with a `4/4` audit. Eight nested outer-count bodies now beta-code
  those semantic row counts and attach their native `Sum` at `39/25`,
  `71/27`, `58/23`, `40/27`, `37/26`, `30/23`, `43/23`, and `40/22`; their
  `4/4` audit takes 2.22 seconds. Quotient/floor-sum identification and the
  transposed two-orientation identity remain. A generic 67-command threshold
  body now proves `p*S(j)<n <-> S(j)<=q` for a division with nonzero bounded
  remainder at `92/30`, with a `4/4` audit in 0.30 seconds. Instantiating
  the first two arithmetic premises is now body-green as well: three sound
  remainder-nonzero bodies check at `47/21`, `45/24`, and `45/28`, with the
  false cross-half claim (`p=3,q=7,i=2`) retained as a regression; the odd-
  half cross-product and quotient-bound bodies check at `160/45` and `67/29`
  without primality or a nonzero-remainder assumption. The generic exact
  initial-segment ladder is now body-green too: its eight bodies check at
  `23/12`, `63/25`, `40/19`, `25/14`, `41/21`, `91/28`, `160/37`, and
  `49/21`, and the complete focused no-DNE test passes `11/11` in 2.09
  seconds. Exact sum transport is body-green too:
  `beta_sum_transport_prefix` is dependency-free at `59/29` and preserves a
  relational `Sum` under pointwise-equal decoded entries. Generic exact
  pointwise addition is body-green as well: `beta_sum_pointwise_add` proves
  that two exact terminal values add to a third when the decoded entries add
  pointwise. Its 127-command body checks at `195/57` with 195 objects, 194
  edges, no reuse and no `DNE`; its focused audit passes `3/3`. Constant
  prefixes now have an exact sum interface too: `beta_repeat_sum_exact` and
  `beta_repeat_sum_exists_exact` prove/package the endpoint `l*a` at `85/32`
  and `33/21`; the focused audit passes `4/4`. The reusable
  one-dimensional partition lemma is body-green too:
  `complementary_bit_counts_add_length` proves `n+m=l` for pointwise
  complementary bit prefixes at `220/46` (`3/3` in 1.47 seconds). The
  Eisenstein-specific row bridge is body-green as well: four bodies transport
  the threshold semantics through `BitCount`, decoded division entries, and
  the rectangle layer's semantic witness at `78/36`, `95/45`, `111/55`, and
  `119/72`; the focused audit passes `4/4` in 3.40 seconds. Exact outer sum
  identification is now body-green: pointwise quotient/rectangle entry
  matching, sum transport, and endpoint functionality check at `104/52`,
  `73/54`, and `67/51` (`4/4` in 4.92 seconds). The semantic transpose is
  exposed pointwise at `95/33`, and opening both outer entries plus their
  existential inner rows and complementary cell bits checks at `116/58`;
  those focused tests pass `6/6` in 2.08 seconds. A coherent transposed-column
  layer now retains the swapped outer entry, one inner row and `BitCount`, and
  every decoded transposed cell across a complete column. Its six bodies check
  at `42/26`, `80/31`, `64/29`, `56/33`, `87/47`, and `117/56`; the endpoint
  proves an original row count plus its transposed-column count equals `k`.
  Focused tests pass `5/5` in 5.21 seconds and a five-suite related run passes
  `18/18` in 10.39 seconds. Eight further bodies now beta-code and sum all
  column counts, recover decoded partitions, align them against `Repeat(k)`,
  and combine exact pointwise/constant sum theorems to prove `N+M=h*k`. They
  check at `70/32`, `88/35`, `68/33`, `59/28`, `51/26`, `60/36`, `61/43`,
  and `116/61`; focused tests pass `5/5` in 13.29 seconds and five related
  suites pass `21/21` in 23.05 seconds. The native nested transpose/Fubini
  gap is now body-green. The universal induction proves `M=T` at `264/65`,
  the constructed-prefix specialization at `49/33`, and composition gives
  `N+T=h*k` at `65/37`. The decoded quotient endpoint then identifies both
  quotient traces with the two semantic rectangle totals and proves
  `Q+U=h*k` at `145/68` (SHA-256
  `d10467b948c749bcf5727127213b5337583b3bba415da7d30a1589ede66116ae`).
  An independent replay of the row decomposition, universal Fubini and
  quotient endpoint suites passes `12/12` in 45.25 seconds.
  The nine earlier lightweight Eisenstein suites through generic exact sum
  transport pass together `42/42` in 6.48 seconds; see
  `research/arithmetic-library/eisenstein-division-prefix.md`.
- **Gauss--Eisenstein terminal parity (2026-07-30):** the generic
  `beta_sum_pointwise_mod_three_add` induction lifts aligned pointwise
  congruences into exact terminal sums at `328/66`. The specialization then
  aligns the signed magnitudes with the canonical half-range permutation,
  proves exact equality of their sums without equating beta codes, and
  cancels that common sum modulo two. The strongest endpoint,
  `gauss_eisenstein_sign_count_mod_quotient_sum`, preserves all shared prefix
  parameters and proves `Q == E (mod 2)` at `89/65`. The pointwise,
  finite-sum, and terminal suites pass `12/12` in 17.47 seconds. These are
  dependency-curried body checks, not registration, recursive closure or
  admission.
- **Exact quadratic reciprocity bodies (2026-07-30):**
  `odd_prime_gauss_eisenstein_orientation_data_exists` checks at `139/67` and
  the two-prime existential join at `222/77`. The latter hides every beta and
  rectangle code and returns only the two complete QRes/count
  classifications, `e == Q`, `f == U` modulo two, and `Q+U=h*k`. The exact
  public same-case and opposite-case formulas then check at `73/33` each.
  The initial 54-node combined wrapper was replaced by a direct, sharing-
  conscious body that constructs the common data once; it checks at 3
  dependencies, 65 commands and `113/35`, with the exact combined statement
  unchanged. The terminal downstream
  slice passes `20/20` in 27.25 seconds. This establishes the complete
  dependency-curried mathematical body in unchanged first-order PA; it does
  **not** establish recursive closure or admission. Those trust and capacity
  gates run on WMI.
- **QR closure pressure forecast (2026-07-30):** static recursive dependency
  discovery for the optimized combined endpoint reaches 557 unique
  public/candidate specifications at depth 45. The naive theorem-certificate
  recurrence has 191,669 occurrences before proof-body nodes are counted,
  almost exactly half the first wrapper's 382,882. This predicts that
  the 500,000 structural-occurrence boundary may fail even when the 100,000
  distinct-object boundary succeeds. Do not convert that forecast into a
  larger limit. Measure structural nodes, distinct objects, time and RSS on
  WMI first; if sharing is the only issue, use the planned reviewed
  self-contained closed-proof DAG rather than an arbitrarily larger proof
  tree.
- **Recursive QR tree is statically over budget (2026-07-30):** the optimized
  recurrence forces 191,668 recursive Cuts, 348,145 repeated leading
  dependency introductions, and at least 191,669 terminal body nodes: a
  rigorous lower bound of 731,482 proof nodes before substantive tactics.
  The selected response is not a guessed larger limit. Compile the 557
  specifications and 1,791 edges into 45 balanced-conjunction layers (maximum
  width 63), Cut each layer package once, and project dependencies from prior
  packages. This uses every body once and produces an ordinary certificate
  for the unchanged kernel. A new proof-reference node is fallback-only.
- **Final QR WMI transport state (2026-07-30):** the reviewed focused suite
  selects nine gates: four exact endpoint/body checks and five recursive
  closure, graph, mutation and capacity checks. It requests one CPU, 32 GiB
  and four hours, archives the complete candidate closure, and preserves
  strict-JSON discovery metadata even when the capacity gate fails. Its local
  transport harness passes `5/5`; both safe manifest tests pass `2/2`. A
  test-only submission attempt timed out at the SSH gateway before any upload
  or Slurm action. Do not cite a WMI snapshot or job until the wrapper returns
  their identifiers.
- **WMI Book harness audit:** an independent static audit remediated canonical
  packaging/output-alias checks, worktree drift detection, non-login shell and
  Python-environment isolation, immutable source/output separation, and
  relative-link escape rejection. Test-only scheduler validation succeeded for
  the 125-file frozen snapshot
  `6feb5ebcdb9f59e6d94b71acd3fb2bce06d45b3a3885ad95aa8e9c02d61a3bcb`,
  with content-manifest SHA-256
  `c09064eb67906761c357626df4ee9e0cf387a89b7593654c8c5bf74baf836c24`.
  Real job `173024` is `PENDING (Priority)` with zero CPU at the last
  observation. It has produced no Book-build or integrity result yet.
- **Residue-reindex architecture:** keep rung 6 decomposed into bounded-map
  projection, prime multiplication-map injectivity, successor-range
  alignment, and successor-range scale congruence. Package these four facts
  only at the endpoint. Rung 8 then needs exactly the package, target-product
  existence, general product permutation invariance, and pointwise
  scale-product transport. This separation makes failures local and exposes
  reusable LLM curriculum lemmas without changing PA or adding classical
  reasoning.
- **Modulo-two and odd-division parity bridge (2026-07-30):** five isolated
  bodies identify expanded evenness/oddness with balanced congruence to
  `0`/`1` modulo two and prove congruence transport; their nodes/depth are
  `14/9`, `20/13`, `42/18`, `50/16`, and `86/20`. Six further bodies prove
  that an odd multiplier preserves and reflects parity and that every exact
  `n=p*q+r` with odd `p` has the same even/odd status as `q+r`; the two main
  iff bodies are `93/22` and the combined package is `51/20`. The three
  parity suites pass together `12/12` in 1.27 seconds. All are constructive,
  dependency-curried, unregistered and unadmitted.
- **Odd half versus modulo four (2026-07-30):** four isolated bodies prove
  the exact identities `h=2*a` and `h=2*a+1` from a shared decomposition
  `p=2*h+1` and the respective equations `p=4*a+1`/`p=4*a+3`, then package
  `Even(h)` iff the first case and `Odd(h)` iff the second. Nodes/depth are
  `20/13`, `78/27`, `42/18`, and `100/30`; the complete four-suite parity
  replay passes `16/16` in 1.24 seconds. These bodies supply the constructive
  last-mile parity cases for reciprocity but are not admitted.
- **Actual bounded Gauss classification (2026-07-30):**
  `bounded_gauss_lemma_complete` composes the witness-producing Gauss power
  congruence, predecessor-power parity, and bounded Euler criterion. For
  prime `p=2*h+1` and `0<a<p`, it constructs a provenance-carrying signed
  `BitCount e` and proves both `QRes(p,a) <-> Even(e)` and
  `~QRes(p,a) <-> Odd(e)`. The 11-dependency, 204-command body checks at
  597 nodes/depth 53, 559 objects, 596 edges and 38 reused objects; an
  independent focused replay passes `5/5` in 7.88 seconds. This is not
  recursive closure or admission.
- **Arbitrary-unit Gauss classification (2026-07-30):**
  `arbitrary_gauss_lemma_complete` removes both literal bounds on `a` and
  assumes only `p` does not divide `a`. It preserves the same signed-prefix
  and `BitCount e` provenance and proves the same residue/even and
  nonresidue/odd equivalences. Its fail-closed source recipe shares only the
  audited classification tail with the bounded candidate; the resulting
  expanded body is independently kernel-checked at 9 dependencies, 188
  commands, 547 nodes/depth 49, 513 objects, 546 edges and 34 reused objects.
  The bounded and arbitrary focused suites pass together `9/9` in 13.64
  seconds. This makes both reciprocity orientations available without first
  reducing one prime modulo the other; closure and admission remain WMI-only.
- **Pointwise Gauss--Eisenstein parity join (2026-07-30):** five isolated
  bodies prove that same constructive parity entails balanced congruence
  modulo two, carry an exact division `a*x=p*q+r` through odd scale/modulus,
  prove `r == m+1 (mod 2)` from `r+m=p` with odd `p`, and combine the lower
  and reflected branches. The endpoint
  `odd_scaled_division_signed_mod_two` proves
  `x == q+m+s (mod 2)` and checks at 43 nodes/depth 25; preceding receipts
  are `53/15`, `77/27`, `87/27`, and `64/22`. The focused test passes `5/5`
  in 0.56 seconds. Representation alignment is now body-green too. Four exact
  candidates build the odd-half complement, transport the reflected modular
  equation, identify the canonical remainder, and prove `r=m` or `r+m=p`;
  their nodes/depth are `238/39`, `53/22`, `49/24`, and `115/35`.
  `odd_signed_division_congruence_mod_two` composes this at `58/34`, and
  `gauss_eisenstein_prefix_pointwise_mod_two` opens the canonical, scaled,
  division and signed β-prefixes at one common index and proves
  `x_i == q_i+m_i+s_i (mod 2)` at `250/61`. Its statement is 5,440
  characters with SHA-256
  `84b039612f162c0c0935ebf49e1ffadf0cdf8e660914f583b7f490744175884e`.
  Five related suites pass `21/21` in 3.07 seconds. The remaining layer is to
  aggregate the pointwise congruences and cancel the permuted magnitude sum.
- **Exact finite-sum permutation API (2026-07-30):** the constructive
  replacement, swap-last, fixed-last reindex and general bounded-injective
  reindex bodies check at `327/59`, `133/50`, `85/33`, and `631/88`.
  Their two isolated focused suites pass `8/8` in 22.67 seconds. This supplies
  the exact magnitude-sum cancellation mechanism without equating raw β
  codes; range alignment and aggregation remain separate contracts.
- **Constructive reciprocity parity truth tables (2026-07-30):** six isolated
  bodies convert an even/odd sum of two Gauss counts into equal/opposite
  quadratic-residue status, transport the result across congruence modulo
  two with `h*k`, and discharge the one-mod-four/both-three-mod-four split.
  Their nodes/depth are `48/17`, `48/17`, `31/20`, `31/20`, `56/27`, and
  `52/26`; exact dependencies, hashes, lengths and identity receipts are
  pinned and the focused audit passes `4/4` in 0.93 seconds. This is the final
  logical layer only: it assumes the still-unproved count-sum congruence.
- **Recursive QR closure is impossible under the current policy
  (2026-07-30):** the exact 557-spec/1,791-edge graph unfolds to 191,669
  theorem occurrences. Its Cuts, repeated leading introductions and one
  terminal node per occurrence already force at least 731,482 proof nodes,
  before substantive proof constructors. Do not raise the 500,000 limit to
  hide this compilation duplication.
- **Layered Cut closure is the preferred unchanged-kernel route
  (2026-07-30):** package each of 45 dependency-depth layers as a balanced
  conjunction, apply every dependency-curried body once to projections from
  earlier packages, Cut each package once, and project the QR root. The
  compiler is isolated and untrusted; only `check((), certificate, QR)` grants
  authority. A fallback closed-proof DAG is not yet justified.
- **Layered QR static evidence (2026-07-30):** 25 focused architecture tests
  pass. The real formulas plus deliberately false bodies compile to a
  13,715-node/depth-56 scaffold with 144,197 package-formula occurrences and
  depth 68, and the unchanged kernel rejects it. A distinct-marker surrogate
  consumes every one of the real 1,791 ordered dependencies and is accepted
  at 19,088 nodes/depth 74; it is compiler evidence, not a QR proof.
- **Layered WMI transport boundary (2026-07-30):** the actual acceptance suite
  has nine gates; exact body/statics have six; the known-over-budget recursive
  experiment has three diagnostic gates and is excluded from the passing
  `full` surface. At that checkpoint laptop checks passed 49 with four heavy
  functions skipped, and a test-only SSH attempt timed out before upload.
  It produced no snapshot, scheduler receipt, job ID, or QR admission.
- **QR public enrollment must decouple stack construction (2026-07-30):** the
  pre-refactor stack imported `TheoremSpec` and cached `_specs_by_name` from
  the registry it would join. Direct enrollment would therefore create an
  import cycle and later make candidate names conflict with the unified public
  table. The implemented repair builds against an explicitly injected frozen
  pre-QR registry; a future admission must append the exact topological order.
  Its count is 317 total: 316 proper new ancestors plus
  `quadratic_reciprocity_combined`, not 317 plus another root.
- **QR stack import cycle is removed, but admission is still absent
  (2026-07-30):** the pure collector now accepts an exact specification type
  and copied public mapping; only a thin runtime adapter imports the current
  registry. Fresh-process import orders preserve the exact
  `84/346/317/240/557/45` receipt and the pinned graph/source hashes. Do not
  rebuild the stack against the future unified post-QR table.
- **Layered replay must bound the whole proof envelope (2026-07-30):** proof
  nodes alone omit formulas and terms carried by `Cut`, elimination,
  substitution, induction, and witness constructors. The production-neutral
  constructive compiler now scans all 25 exact kernel constructors, rejects
  `DNE`, holes, metavariables, custom/malformed nodes, and charges repeated
  annotations plus combined proof/annotation depth. Candidate limits remain
  500,000 proof occurrences, 100,000 objects and depth 256, with a separate
  five-million annotation ceiling and envelope depth 256. Only the unchanged
  kernel grants theorem authority.
- **Hardened layered static receipts (2026-07-30):** the false-body actual-QR
  scaffold is `13,715/56`, annotations/envelope `157,579/92`, package
  `144,197/68`, and kernel-rejected. The exact dependency-consuming surrogate
  is `19,088/74`, annotations/envelope `142,346/84`, package `19,297/18`, and
  kernel-accepted; swapping the two `beta_range_empty` dependencies is
  rejected. Neither receipt proves QR.
- **Public/browser preparation is non-admitting (2026-07-30):** bare `pa lib`
  lists parsed closed statements without replay, while detail, Lean export and
  `use` replay on demand. The deterministic worker inventory covers 147
  Python files. The future test migration has 125 absence assertions in 79
  files and must use the exact 317/29 partition. The checkpoint manifest is
  synchronized with repository-local release ID `a-279f7fd6f2b9` and build
  label `2026-07-31a`; external deployment, candidate admission, and the cold
  Pyodide replay remain pending.
- **Latest WMI boundary (2026-07-31):** payload-specific approval was granted
  for SHA-256
  `2bab0898a5bc628a0e1f06b5e6cdf56af86fe39c2fdbeaaa4147ac43d2c7faaa`.
  The wrapper uploaded and remotely verified the exact 338-member,
  5,374,464-byte dirty snapshot based on commit
  `a549a537cfe3d3d7e8ef292a49250c4308d12c5d`, passed scheduler validation,
  and submitted full 136-gate job `187187` on `cpu_idle` with one CPU,
  32 GiB and four hours. It failed after 39 seconds with exit code `1:0`:
  gates 1--4 passed, gate 5 exposed the unused `succ_ne_zero` dependency in
  `prime_scaled_inverse_target_nonzero`, and 131 gates were unrun. The
  redundant edge is now removed and focused local validation passes, but no
  complete WMI proof receipt or theorem admission exists yet. The corrected
  338-member, 5,374,464-byte archive was built twice identically at SHA-256
  `989011c09d82dbbb239df43334e88553e1fb3e0d2f1033f93c5b8b1791851757`;
  after new content-specific authorization it was uploaded and submitted as
  full job `210714` with one CPU, 32 GiB and four hours. Slurm later reported
  `FAILED`, elapsed `00:08:29`, exit `1:0`: gates 1--14 passed, gate 15 found
  that replacing the declared direct edge
  `odd_upper_remainder_reflection -> add_succ_left` did not invalidate the
  certificate, and 121 gates were unrun. This is a fail-closed
  dependency-minimality result, not a kernel-soundness failure, a complete
  replay receipt, or a theorem admission.
- **Historical QR WMI preflight (2026-07-30):** the earlier cleaned candidate
  upload excluded
  `__pycache__`, bytecode, and `.DS_Store`; two builds agree at SHA-256
  `13f279cf2390104009825abac01c17e8b96d56bb764719964e36949ea3345a43`,
  5,343,232 bytes and 337 tar members, from dirty base commit
  `a549a537cfe3d3d7e8ef292a49250c4308d12c5d`. Both source and extracted
  transport harnesses pass `9/9`. This is local payload evidence only—not a
  scheduler validation or proof receipt. It was superseded before upload by
  the approved `2bab0898...faaa` snapshot above.
- **PA Proof Explorer identity and status model (2026-07-30):** the exact
  557-node QR closure now has persistent append-only `PAxxxx` theorem tags,
  canonical tag pages, name aliases, forward/reverse neighborhoods, and
  27,491 numbered tactic-line anchors. `quadratic_reciprocity_combined` is
  permanently `PA00FW`. Status is evidence-level data: 240 public theorems,
  316 body-checked candidates, and one root pending layered closure. Never
  infer admission from a page, tag, source hash, body receipt, or prose.
- **Proof Explorer link policy (2026-07-30):** link only declared direct
  dependencies in theorem-accepting positions of the authored tactic
  language. The current corpus has 8,553 such occurrences and seven
  dependency edges with no literal body occurrence; those seven stay in the
  import/dependency panels. PA1–PA6 and tactic names link to foundations.
  Dynamic local-hypothesis lineage and implicit `simp` firing require a real
  replay trace and must not be reconstructed heuristically.
- **Informal proof provenance (2026-07-30):** every explorer page carries an
  explicit `generated` or `curated_reviewed` label. The initial corpus has 553
  generated structural guides and four curated QR explanations. Curated
  prose lives in a separate sidecar so deterministic regeneration cannot
  overwrite it; all informal references resolve through persistent tags.
- **Explorer release boundary (2026-07-30):** the deterministic generator
  aggregate is
  `669b978fff47fe7a6e9b55ddcffb4f12082872bbed1657ff35ff839b873ec13e`,
  and the local explorer/Book/WMI contract suite passes `24/24`. The WMI Book
  build, built-copy integrity receipt, and attached-browser visual smoke test
  are still absent. Dashboard work changed the QR/WMI payload, so the older
  `13f279...` archive is historical and cannot be uploaded under its former
  content-specific approval.
- **Dependency graph v2 (2026-07-30; refreshed 2026-08-03):** the generated
  QR closure graph has 557 theorem nodes, 1,787 direct edges, 45 layers, and
  48 theorem roots. Those
  roots mean “no theorem prerequisite in this corpus”; they are not PA
  axioms, whose language and rules remain in the separate foundations pages.
  For `PA00FW`, graph v2 records a deterministic short chain of 4 vertices, a
  critical depth witness of 45 vertices, and 101,278 distinct theorem-root-to-
  target paths. The Book entry is
  `book/arithmetic-library/dependency-graph.md`; the static explorer endpoint
  is `book/_static/pa-proof-explorer/graph.html?target=PA00FW`, with the exact
  theorem at `tag/PA00FW.html`. Navigation does not change status:
  `PA00FW` remains `pending_layered_closure`. The final explorer owns and
  hashes all 1,123 files (aggregate
  `50c1d143cf6008d3bce737c2e7c0f84fc4ff6eff33978f7690fa22409db3be8b`);
  the file-protocol payload is safely embedded only in `graph.html`, so it is
  not injected into ordinary Book chapters. A full local Book build and
  source/built-tree integrity check pass with zero broken relative targets,
  but the attached-browser visual gate remains unavailable.
- **Unified local terminal (2026-07-31):** `pa native` runs the current
  model-free 384-theorem worktree, while `pa model` and bare `pa` retain the
  separately attested 247-theorem diagnostic model. Native dispatch occurs
  before model seals or imports; `use THEOREM` still reconstructs and
  kernel-checks the selected dependency and the final empty-context proof.
- **Conservative defined-notation edition (2026-08-02):** the second PA Proof
  Explorer edition provides a 40-entry persistent `PD` registry over the exact
  557-specification QR closure and all 27,491 tactic lines. Thirty-eight
  definitions occur; `AllPrime` and `Sorted` have zero whole-schema matches.
  It compacts 506 theorem statements and 1,275 of 1,839 proposition-bearing
  `have`/`suffices` commands: aggregate statement text falls from 2,457,096 to
  107,386 characters (95.63%), and local proposition text from 1,971,403 to
  111,519 (94.34%). Every compact formula expands back to the same parsed PA
  AST and retains an exact native replay line. The compiler, registry, `PD`
  tags, hashes, pages, and 1,725 notation edges are untrusted presentation
  data; proof paths still use only the unchanged 557-node, 1,787-edge,
  45-layer theorem DAG. Status is also unchanged: 240 public theorems, 316
  body-checked candidates, and `PA00FW` alone pending layered closure. The
  edition supplies no quadratic-reciprocity admission.
- **QR dependency-hygiene supersession (2026-08-03):** four unused direct
  dependencies were removed after exact adversarial mutation checks:
  `gauss_signed_half_magnitude_injective -> add_assoc`,
  `odd_upper_remainder_reflection -> add_succ_left`, and the two
  `pair_order_iteration_* -> add_comm` edges. No theorem statement, PA rule,
  or kernel boundary changed. The live graph is 557 nodes / 1,787 edges / 45
  layers with graph SHA-256 `98a36450cfe1de29c20be67a1c5f65c8064e9f9eec5368ab769065f910008698`
  and candidate-source SHA-256
  `23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1`.
  Its recursive tree has 191,648 theorem occurrences, 191,647 dependency
  Cuts, 348,128 leading introductions, and a 731,423-node lower bound. The
  exact-marker surrogate checks at `19,066/74` nodes/depth with
  `142,134/84` annotations/envelope. Older 1,791-edge numbers and hashes in
  dated WMI entries identify the frozen historical jobs and remain valid only
  for those payloads.
- **Model-v3 training curriculum and launch gate (2026-07-31):** the frozen
  first-247 declaration-order prefix of the current 384-theorem native ladder
  is the content-bound training authority. Exact authored
  predecessor-prefix replay contributes 8,494 transitions. WMI preparation
  `172536` completed that library lane, then failed closed after 1:02:34 when
  the original synthetic ring schema exceeded its reviewed coefficient limit;
  no training or evaluation job was submitted. The repaired version-2
  synthetic plan has exactly 70,000 rows in 32,600 unique roots, covers all 51
  schemas, balances 14 first-tactic heads at 2,328--2,329 sessions, caps
  `intro` below 20%, and needs zero candidate skips. Its ordered SHA-256 is
  `79d2704eab6eb73205ff2234f55f0d4a7e034176fe8dc8649c6950ff499d547b`.
  Catalog-derived components are train-only;
  validation and test are synthetic-only, and held-out target formulas are
  rejected at every intermediate state. Prompt-v3 exposes exact theorem
  names and statements and losslessly compacts repeated proof declarations
  with `shared-declarations-v1`; across all 222 stress-proof transitions the
  maximum pinned Qwen3 prompt, completion, and EOS length is 29,111 tokens,
  leaving 3,657 below the native 32,768-token limit. Retry `172729` generated
  32,600 independently checked synthetic sessions/70,000 transitions and all
  247 library sessions/8,494 transitions, then atomically built 64,500 train,
  6,948 validation, and 7,046 test rows. The exact manifest SHA-256 is
  `ccb62c771d1f7dab1e90e98da42c6c8acee40f47b5527c4f65611f718661d983`.
  Its combined walltime could not also fit independent replay, token audit,
  and smoke. Exact-corpus continuation `173040` subsequently completed those
  gates from clean commit `5faa3d27cbaf522198ffa1bdcd11fa9d57341658`.
  Job `213641` published and independently verified the resulting immutable
  15-file seal at `checkpoints/corpora/peano-policy-v3-173040`, with content
  SHA-256 `7b22bdf083894e3d87b84fc463ff537a75eeecba8e34098429db215592ec6b5b`.
  These are corpus-preparation results, not transformer training.
- **Model-v3 selected objective (2026-07-30):** the trainer retains all 8,494
  catalog rows and selects only complete synthetic sessions under a 12,288-row
  ceiling, anchoring all 51 schemas and balancing all 14 root heads by a
  seed-bound, input-order-independent record. `run.max_train_samples` is
  forbidden. The pinned tokenizer binds every selected token sequence and
  enforces linear, quadratic, sequence, and supervised-completion ceilings.
  Completion-only causal loss uses Qwen's indexed `logits_to_keep` positions,
  the exact one-token shift, FP32 summed cross entropy, and the exact supervised
  token count across gradient accumulation; a pinned LoRA probe matches the
  full-logit loss and gradients to numerical precision.
- **Model-v3 historical/current boundary (2026-07-31):** the non-replacing,
  read-only corpus seal binds exactly twelve historical data artifacts and
  three preparation reports to clean source commit `5faa3d27`, preparation
  `173040`, and content SHA-256
  `7b22bdf083894e3d87b84fc463ff537a75eeecba8e34098429db215592ec6b5b`.
  Current code may consume it only after full seal verification and
  compiler/kernel/prompt/held-out/library eligibility comparison. The new WMI
  chain remains sealed preparation (eligibility + exact token audit + extremal
  indexed-loss A100 smoke), fresh one-GPU training, four-goal bounded search,
  then model-free independent kernel replay of every claimed proof. Its first
  current-source preparation, job `214264`, reached the selected-token audit
  and failed closed before runtime smoke or model loading because train exposure
  was 73,446,475 tokens against the reviewed 70,000,000-token ceiling. The
  replacement changed only that ceiling to 74,000,000. Job `217123` then passed
  eligibility and the complete selected token audit: train squared exposure was
  415,247,631,205, maximum sequence length 29,111, and maximum supervised
  completion 936. Its runtime smoke performed representative adapter updates
  and one real Trainer step, but saved-policy admission failed before report
  publication because Accelerate's retained mixed-precision forward wrapper
  was compared with a bare fresh reload. The repair explicitly unwraps to the
  original single-process forward and makes snapshot capture reject a retained
  wrapper. Fresh preparation `217768` then passed the exact eligibility, token-audit, runtime-smoke,
  saved-policy-admission, and reload gates; `sacct` records `COMPLETED|0:0|0:0`. Because Slurm rejects a new `afterok` edge after a
  completed job ages out of its 300-second controller retention, guarded submission now uses
  `--completed-predecessor` for the durable accounting/ledger/report binding and reserves
  `--afterok` for live jobs. Exact provenance therefore forbade relabelling `217768`. Fresh
  same-source preparation `217851` subsequently passed every gate under clean source `4d44609e`,
  and guarded production successor `217859` completed the 649-step rank-32 Qwen3-1.7B optimizer on
  one WMI A100. The schedule used logging 11, yielding 59 periodic boundaries through the terminal
  step. A loopback-only Training
  Observatory reads fixed bounded WMI evidence without exposing SSH or scheduler mutation to the
  browser and labels corpus examples as representative rather than current microbatches. The
  attestor's independent-builder watchdog is eight hours, above the
  exact measured 5h07m first build; the old four-hour value would have rejected
  a legitimate replay deterministically.
- **Model-v3 paired evaluation admission (2026-08-02):** trained-policy job `218171` completed in
  3m51s and revision/configuration-pinned pretrained comparison `218172`, whose report declares no
  PEFT adapter, in 4m20s under the same frozen four-goal, depth-32/beam-16 search authority. Their
  immutable raw `k=1` reports say 3/4 versus 0/4. The
  trained routes `norm_num`, `exists 5; norm_num`, and
  `intro n; rewrite PA3; simp` independently replay through the kernel with 98, 29, and 10 nodes;
  the induction-heavy consecutive-product theorem remains unsolved. The pretrained comparison
  produced 32 malformed sequences and executed no tactics. Canonical whole-report replay rejected the trained report
  because its nested policy environment retained the legacy four-field projection and omitted
  `library_identity_sha256`, `library_full_identity_sha256`, `library_prefix_length`, and
  `library_size`. The original report stays immutable and the ordinary replay gate stays strict.
  Separate version-pinned `trained-compatibility-replay.json` now passes after pinning the historical
  report, source, job, projection, reconstructed full authority, and source inventories; it
  independently replayed all 3/3 claims and has embedded attestation SHA-256
  `e900a10241db0451992313eb2a7b0341911a7a71cd8af91e831a279874afda56`.
  Dedicated `pretrained-base-replay.json` passes declared control identity, provenance, and search
  accounting with zero claims; its embedded attestation SHA-256 is
  `056519bc3598a390526fdf9054aa38090d499f7f837af0a2ace7af8caaa560e7`.
  Exact training manifest SHA-256
  `caa5569c98ed9ea048d413301b803c39011957d1c97307e5b109846989e18569` records expected and actual
  649 optimizer steps. `paired-launch-smoke-attestation.json` cross-binds that manifest, both
  reports and producer attestations, three jobs, source, goals, seed, and search limits. It verifies
  historical Git source maps of 36/36 semantic and 61/62 evaluation records (62 unique blobs) and
  reports `paired_launch_smoke_admitted`; embedded attestation SHA-256 is
  `9b33b4e488f14e38fc7c5a122410d53e9e1123409dcccafdc73e0a8ab1a14bae`, file SHA-256
  `cdd20cc6e97ff442cff1c476135963f726b740372223f6eac72335543f6c11ba`.
  The narrow four-goal `k=1` launch smoke is therefore admitted as 3/4 versus 0/4. Base weight
  shards were not content-hashed before/after loading, and raw generation/extraction/executed-edge
  transcripts are absent, so attribution relies on byte-pinned historical producer/source/job
  records rather than a bit-for-bit base or raw-output replay. Retained `sacct`/log artifacts also
  observe WMI completion but are not cryptographically authenticated by the scheduler. This is not
  a statistical benchmark or evidence of broad PA ability, induction capability, or causal
  superiority.
- **Post-merge integration seal (2026-08-02):** the 384-theorem native library
  and the incoming trained-policy stack coexist without widening either frozen
  model authority: model-v2 remains 56 theorems and model-v3 remains the first
  247 declaration-order theorems. The selected merged matrix passed 1,183 tests
  with five intentional skips, including six loopback-server tests run outside
  the socket-restricted sandbox. The 45-source Book rebuilt successfully; its
  integrity report covers 2,323 HTML pages with zero broken, escaping, or
  unsafe links and byte-identical explicit/defined explorer trees. The
  385-record knowledge catalog, 149-source browser manifest, historical corpus
  release, and 475-note/4,825-link vault all verify. This is an integration
  seal, not a quadratic-reciprocity admission: the 136-gate WMI QR campaign
  still has no complete passing receipt.
- **Model-v3 prelaunch durability and chain binding (2026-07-30):** the
  one-shot trainer preserves adapter/tokenizer tensors before its explicit
  full evaluation, while withholding the final manifest until evaluation and
  all immutable-input checks pass. Scheduled benchmark evaluation must match
  the manifest producer job, exported training predecessor, and submission-ledger
  predecessor before model load; its report records that relation for the
  independent replay gate. Interactive proof requests bind the completed
  manifest under a separate non-dependency status.
- **Model-v3 seal bootstrap closure (2026-07-31):** first publication used an
  exact two-source staged program with no package marker or bytecode cache. A
  submission-embedded launcher stable-reads, hashes, compiles, and executes
  identical CLI bytes under isolated Python; the CLI independently verifies
  and compiles the standard-library module. After historical preparation
  `173040` completed, job `213641` exercised the repaired Ceph publication
  profile and published the verified immutable seal; bootstrap staging is no
  longer pending.
- **Model-v3 completed-run authority (2026-07-30):** a usable v3 adapter now
  requires more than a positive/equal `global_step`. One canonical evidence
  object binds all schedule/result/Trainer-state step counts, the reviewed
  one-CUDA-process BF16 runtime, actual save/eval/clipping arguments, every raw
  and post-clip gradient boundary, all strict pre-clip norms, exact finite
  Trainer history and metrics, initial/final raw-byte fingerprints for the
  stable trainable tensor population, a nonempty adapter update, and the closed
  adapter/tokenizer hashes. Trainer's permissive built-in clipping and terminal
  checkpoints are disabled; a custom pre-optimizer max-norm-1 clip owns the
  update boundary. Model-v3 loaders and the same-base control reject absent,
  partial, stale, duplicate-key, non-finite, linked, or inconsistent manifests
  before framework import. Scheduled training also binds a retained
  no-replace recovery-publication probe on the exact output filesystem. The
  At that 2026-07-30 prelaunch checkpoint the local macOS branch was tested,
  while the WMI `/work` Linux branch and optimizer results were still pending
  during the FortiClient disconnection. Later entries record their completion.
- **Model-v3 saved-policy admission (2026-07-30):** completion now crosses the
  serialization boundary. Three run-bound admitted train/validation probes
  fingerprint terminal indexed losses/projected logits and the canonical PEFT
  tensor population. After releasing the original Trainer/model, one fresh
  local-only load must equal the actual safetensors and all probe outputs, and
  disabling LoRA must change at least one probe. The admission joins base
  commit/config, run identity, `cuda:0`, individual files, closed artifact
  trees, and completion evidence. `bf16_full_eval` is false because the pinned
  Transformers path would cast PEFT's FP32 weights; tensor fingerprints are
  rechecked after save and evaluation. Final output, adapter/tokenizer trees,
  run identity, and manifest are exclusive no-replace publications with a
  rechecked output inode/device/mode. V3 artifact closure rejects link/special/
  cross-device/hard-link nodes, descriptor or tree mutation, and any mode other
  than 0555 directories plus 0444 files; v1/v2 retain their legacy mode rule.
  At that 2026-07-30 checkpoint these were prelaunch safeguards: the WMI
  preparation, real optimizer losses, adapter digest, and replay results were
  still pending. Later entries record the completed run and narrow admission.
- **Model-v3 launch-contract wiring closure (2026-07-30):** before any Torch,
  PEFT, or Transformers import, prompt v3 is now accepted if and only if the
  model-v3 curriculum is present. After semantic admission and the remaining
  source/report checks, the trainer re-verifies the protected adapter and
  tokenizer trees immediately before publishing the final manifest without
  replacement. Direct generation and pretrained-base comparison verify those
  trees both before and after heavy loading, while recovery requires exact
  directory/file modes `0555`/`0444`. These modes detect provenance drift and
  accidental corruption; they are not a hostile-same-owner security boundary.
  The focused wiring audit passes 89 tests. No optimizer or trained-model
  result follows from this prelaunch gate.

## Strict HA number-theory campaign

- **Campaign launch (2026-08-03):** the repository-local controlling blueprint is
  `research/arithmetic-library/ha-number-theory-formalization-campaign-blueprint.md`,
  1,308 lines and 77,809 bytes, with SHA-256
  `8fd25fc3e68259e1a16c935d35dacccefa20a473cdec35f8771cb1d5d806f205`.
  `PLAN/12_ha_number_theory_campaign.md` and
  `research/arithmetic-library/ha-number-theory-campaign.json` reconcile that
  blueprint with the 384-theorem public baseline. Existing public certificates
  are reused; candidate-body replay is never treated as theorem admission.
- **Representation freeze v1 (2026-08-03):** 11 arithmetic definitions, 45 API
  rows, 44 distinct public theorem dependencies, and four representation
  obligations are frozen in paired Markdown/JSON artifacts and checked against
  live parser expansions. `BetaAt` and beta-coded folds are explicitly late
  interoperability encodings, not the K3 pair/list/map foundation. The signed
  component is now fixed by `HA-K3-SIGNED-1`: `2*p` encodes nonnegative `p` and
  `2*k+1` encodes `-(k+1)`. Pair/list/map encodings remain open and must be
  primitive recursive and independent of CRT and Goedel-beta coding.
- **Tranche 01 proof receipt (2026-08-03):** nine isolated HA1/HA2/M1 candidates
  close from the empty context under the intuitionistic checker: four canonical
  remainder results, one canonical-remainder/congruence bridge, and four bounded
  modular-inverse results including the exact iff-and-unique criterion. The root
  certificate checks at 9,512 structural nodes, depth 70, 2,538 distinct proof
  objects, and 126 unique `Cut` nodes; its content-stable DAG SHA-256 is
  `c3ed07e7caef52895001332d066ae9e4ce25167c7a0cd7189f8957c9aa7dc9f3`.
  They were first recorded as `closed_checked_candidate` and were later
  admitted atomically without changing their specifications or receipts.
- **Tranche 01 admission and tranche 02 local gate (2026-08-03):** the nine
  exact factory specifications are public at append-only positions 384--392.
  The one QR overlap, `bounded_mod_inverse_unique`, remains in candidate-factory
  provenance but resolves as public; the QR graph is still 557 nodes/1,787
  edges/45 layers, partitioned as 241 public and 316 candidate nodes. Three new
  canonical-gcd candidates close from the empty context and remain nonpublic.
  `make ha-number-theory-check` passes both manifest validators, 22 validator
  tests, and 20 focused proof/admission
  tests. The admission test performs two cold deterministic closures, bans DNE,
  pins metrics and certificate digests, checks selected nearby false targets,
  and cross-binds the nine public plus three isolated machine receipts. The
  393-theorem snapshot has 1,830,078 nodes, 53,293 Cuts, 338 Cut-bearing
  certificates, and ordered root
  `539a1195df131ed3e202efa15f48bef76a8b8c757789119e2265172453aaf566`.
  The 153-source browser application checks as release `a-9fe3f597bf8d`; no
  staging or deployment receipt is claimed.
- **Canonical gcd and signed boundary (2026-08-03):**
  `canonical_gcd_exists`, `canonical_gcd_functional`, and
  `canonical_gcd_exists_unique` close at respectively 1,280/708/2,010 nodes,
  depths 47/35/48, and 36/20/55 Cuts, with no zero side premise and no DNE.
  `HA-K3-SIGNED-1` freezes eight exact expanded graph predicates and their
  hashes but claims no signed theorem. Its dependency audit forbids using the
  existing `even_odd_exclusive_pointwise` as a K3 seed because that theorem
  reaches division uniqueness; the next proof obligation is a K1-only parity
  separation result.
- **Strict-HA Book integration (2026-08-03):** source checkpoint
  `07932576c3d00d7911acd158d81d9a21167ed2dd` anchors the 393-card theorem
  atlas and all new native-source links. The 47-source Book builds without
  warnings; its 2,325-page integrity gate reports zero broken/escaping targets
  or fragments and byte-identical explicit/defined explorer trees.
- **Signed decoder candidate closure (2026-08-03):** the K3 seed now has nine
  closed, nonpublic theorems: division-free parity separation, even-half
  uniqueness, two decoder constructors, totality, normality, functionality,
  zero characterization, and validity of every natural code. The largest
  certificate is `signed_decode_functional` at 709 nodes/depth 27/13 Cuts with
  DAG SHA-256
  `50818b66647097dee0680f1dacbcb62368049dcc95f66532cd36b63306ab3c0b`.
  The complete dependency audit reaches no division, remainder, beta, CRT, or
  DNE. The campaign manifest has 56 public references, twelve candidates, and
  21 exact receipts; the public registry remains 393. Next prove total and
  functional `SignedBalance` normalization before any signed operation graph.
- **Signed extensionality and balance closure (2026-08-03):** nine additional
  closed, nonpublic candidates connect literal parity-interleaved code equality
  to decoded cross-sum equality and make `SignedBalance` total, extensional,
  functional, decoder-compatible, and exact at zero. The largest is
  `signed_balance_zero_iff` at 1,660 nodes/depth 36/33 Cuts with DAG SHA-256
  `d54bade5be975a27fc08a189ac552110ed8e85878137bc2e8e5268469c46b419`.
  Two cold closures, mutation oracles, RFC D03 expansion, registry isolation,
  and independent reviews pass without DNE or transitive division, remainder,
  beta, or CRT dependencies. The manifest now binds 56 public references, 21
  closed candidates, and 30 exact receipts; the public registry remains 393.
  The next topological layer is `SignedNegate`, not addition or multiplication.
- **Signed negation closure (2026-08-03):** eight further closed, nonpublic
  candidates implement RFC D04 by swapping normalized decoder parts. They
  prove decoder introduction/elimination, totality, literal-output
  functionality, zero, symmetry, and involution. The endpoint
  `signed_negate_involutive` checks at 1,199 nodes/depth 35/27 Cuts with DAG
  SHA-256
  `7aec997db1ea6393ff1192eea1b16a73b4a7424349b7670e1541fa34029c882b`;
  the full 26-theorem signed stack digest is
  `89d806311b58860f130cabf862a17bd4e310710a9069b401b293609a0885ce3c`.
  Independent review and 42 combined tests found no DNE, forbidden tactic,
  division, remainder, beta, CRT, or registry edge. The manifest now binds 29
  closed candidates and 38 exact receipts; the public registry remains 393.
  `SignedAdd` is next and must normalize decoded contribution sums through
  `SignedBalance`. Final local gates pass 26 manifest/definition tests, 62
  proof/admission tests, a cold 393-theorem public replay, the 4,991-link vault
  audit, and the 2,325-page Book integrity audit. Local source checkpoint
  `d5a734292b11e516a86606c65653be38d2faa7f1` contains the exact tranche.
- **Signed addition core closure (2026-08-03):** five closed, nonpublic
  candidates implement RFC D05 exactly: decoded-equation introduction and
  elimination, the packaged equivalence, totality through `SignedBalance`, and
  literal-output functionality. Their certificates have 26, 823, 956, 411,
  and 1,754 structural nodes at depths 23, 35, 39, 27, and 38; the functional
  endpoint has 34 Cuts and DAG SHA-256
  `63eb78997ade1da36271de19138643f20e5e48666a1318d6a4982e616a6b9b87`.
  Two cold replays agree on full 31-theorem signed-stack digest
  `11f41d395be9597892e2d5577ff80b54d04a61a57c81e50d02bc335c7e6012da`.
  The exact transitive closure has 17 public and eleven earlier/local
  candidate dependencies, with no DNE, division, remainder, beta, CRT,
  classical, or SignedNegate edge. An independent review approved the witness
  plumbing and RFC alpha-equivalence; the focused semantic oracle checks 289
  input pairs. The manifest now binds 56 public references, 34 closed
  candidates, and 43 exact receipts. The public registry remains 393.
  `make ha-number-theory-check` passes 26 manifest/definition tests and 69
  proof/admission tests. The total functional graph is closed, but zero,
  commutativity, associativity, and inverse laws remain separate obligations.
  Immutable source checkpoint
  `ce2f865389013ab2ad16cb2c351f735972330554` anchors the Book links. The
  warning-free 47-source rebuild retains 2,325 HTML pages, zero integrity
  errors, and byte-identical 2,285-file explicit/defined explorer trees; the
  vault generation check also passes.
- **Signed addition elementary laws (2026-08-03):** five more closed,
  nonpublic candidates prove graph commutativity, left and right zero, and
  both orientations of addition with canonical `SignedNegate`. Their exact
  nodes/depths are 139/38, 266/25, 427/40, 145/24, and 299/40; certificate
  hashes are pinned in the campaign manifest. Two cold replays agree on the
  36-theorem signed-stack digest
  `a5fdad35078f386ccb42fd6e17f942f83f504aaaf748c40259b68a2798ab28c7`.
  An independent review verified all three private literal-zero D05
  expansions against the RFC AST and found the exact dependency closure to be
  four public arithmetic facts plus five earlier/local candidates, with no
  division, remainder, beta, CRT, classical, or DNE edge. The manifest now
  binds 39 candidates and 48 exact receipts; the registry remains 393.
  `make ha-number-theory-check` passes 26 manifest/definition tests and 77
  proof/admission tests. Associativity remains the one open additive law and
  is intentionally isolated behind a cross-sum helper tranche. Immutable
  source checkpoint `a1fa4162f92d4ce6c5501cebceadd75403d7a563` anchors
  the updated Book links. The warning-free rebuild again has 47 sources and
  2,325 HTML pages; its integrity audit finds zero broken, escaping, fragment,
  unsafe, or remote-runtime links and byte-identical explorer trees.
- **Signed addition associativity (2026-08-03):** the last additive law closes
  through `add_cross_sum_chain`, `signed_add_equations_associate`, and
  `signed_add_associative`. Their certificates have 315, 703, and 1,695 nodes,
  depths 29, 35, and 47, and 7, 13, and 30 Cuts; the graph endpoint's DAG
  SHA-256 is
  `dbac676cc5650d6f0d884dd2e4f9426d17342327cdf0abb59e71c40cc0a8a4cc`.
  Two cold replays agree on full 39-theorem signed-stack digest
  `39ac0f7083ed54d2762289c7417b57a21c6dc97971b57efe2649ecb1cb7ec895`.
  Independent witness review and exhaustive bounded semantic checks over
  `4^6`, `3^12`, and `17^3` tuples pass. The exact closure reaches no
  division, remainder, beta, CRT, classical, or DNE theorem. The manifest now
  binds 42 candidates and 51 receipts; the registry remains 393. The complete
  local gate passes 26 manifest/definition tests and 84 proof/admission tests.
  SignedAdd's totality, functionality, zero, commutativity, inverse, and
  associativity requirements are closed at candidate status; `SignedMul` is
  next. Immutable source checkpoint
  `883febe3fcf3b8a29707f34780c457f8fcd8edc6` anchors the final additive
  Book links. The warning-free 47-source rebuild retains 2,325 HTML pages,
  zero integrity errors, and byte-identical explicit/defined explorer trees.
- **Signed multiplication core (2026-08-03):** five closed, nonpublic D06
  candidates expose the decoded product equation in both directions, package
  its iff, prove totality through `SignedBalance`, and prove literal-code
  functionality. Their certificates have 26, 877, 1,010, 411, and 1,808
  nodes at depths 23, 39, 41, 27, and 40. The functional endpoint has 34 Cuts
  and DAG SHA-256
  `632bd740e1f6a5a00497205379dd64f3cdc3e45d75a33c8c02d46f727f05f410`;
  the 44-theorem signed-stack digest is
  `2230cd2b67196ccec58ab5259052b08f9ef3f43275ef0b717fc35cf581cd0f6c`.
  The exact closure uses no SignedAdd law, division, remainder, beta, CRT,
  classical theorem, or DNE. The manifest now binds 47 candidates and 56
  receipts; the registry remains 393. The next gate is elementary D06 laws,
  not public admission by implication.
- **Signed multiplication elementary laws (2026-08-04):** five further
  closed, nonpublic candidates prove graph commutativity, left and right zero
  annihilation, and left and right identity for signed positive-one code `2`.
  Their exact certificates have 376, 209, 607, 347, and 745 structural nodes
  at depths 41, 25, 43, 25, and 43, with 8, 4, 14, 10, and 18 Cuts. The
  `signed_mul_one_right` endpoint has DAG SHA-256
  `fe3977029e00057909e7204631ce6f66b5ce2aff10a4132872ce011a899ef378`;
  the complete 49-theorem signed-stack digest is
  `be074dfe1b79e3f27b2d48851c64f58360ee86fc3776ae681c451d38f67d25b2`.
  Literal-code alpha audits and a 33-code bounded oracle distinguish code `2`
  as `+1` from code `1` as `-1`, and reject raw multiplication of parity
  codes. The exact closure uses no SignedAdd law, division, remainder, beta,
  CRT, classical theorem, or DNE. The manifest now binds 52 candidates and 61
  receipts; the registry remains 393. Associativity and distributivity are the
  next D06 proof layer.
- **Independent pair/cell design audit (2026-08-03):** `HA-K3-PAIR-1`
  selects the doubled Cantor polynomial
  `code=(left+right)*S(left+right)+(right+right)` and successor-tagged cells,
  with exact template hashes and a K0--K2-only proof ladder. No pair theorem is
  yet claimed. Pairing does not itself provide a finite formula for following
  a tail a variable number of times, so uniform lists, lookup, append, folds,
  maps, and finite CRT remain blocked on a separate computation-history
  representation or proved conservative primitive-recursive definition
  mechanism. Fixed-length generated schemas are honest but insufficient.
- **Current strict-HA gate:** 29 manifest/definition/pair-RFC tests and 132
  proof/admission tests pass. The campaign manifest records 56 public
  references, 63 closed candidates, and 72 receipts; the public registry and
  independently replayed snapshot both remain at 393 theorems.
- **Current documentation gate:** the warning-free 47-source Book build has
  2,325 HTML pages and zero integrity errors. Its explicit/defined explorer
  source and built trees are byte-identical across 2,285 files; the vault has
  492 notes and 4,991 resolved links. Immutable complete SignedMul algebra
  source checkpoint: `497d0fc3327e6fa2564aad8b44c4ce151e20269c`.
- **Signed multiplication associativity and distributivity (2026-08-04):**
  eleven further isolated, closed, nonpublic candidates complete the D06
  semiring-law checkpoint: four rows factor associativity through two
  natural pair identities and a decoded-equation compositor; seven rows
  factor both distributive orientations through additive shuffling,
  balanced-output composition, fixed-left product transport, and graph
  commutativity. The focused associativity and distributivity suites each
  pass all eight tests. Two cold empty-context closures agree on the full
  60-row signed-stack DAG SHA-256
  `7befb7ae830b866a606e47f674730959e76599ded863aadd9868b850bcb190cd`.
  The closed graph endpoints are `signed_mul_associative` at 3,196
  nodes/depth 47 with digest
  `c6a9694ced9e0d4cb1426112b7b717dd9b60cf049ea89e71223f906512271775`,
  `signed_mul_left_distributive` at 3,297 nodes/depth 58 with digest
  `c02d8258cce2e4cbd6a16aa731c9ce3424f1cc4726f48c0bc55d80e9c19f6633`,
  and `signed_mul_right_distributive` at 3,717 nodes/depth 60 with digest
  `63d17772d42432a58c75064ff05ded34490519639625151c90c6cc591f7cf7d1`.
  Exhaustive bounded audits cover the natural helpers, all binary decoded
  associativity/distributivity checkpoints through `2^12` and `2^14`
  assignments, and every one of the `17^3` canonical-code triples for
  associativity and both distributive graphs. All seven distributivity rows
  are reachable from an endpoint; no DNE, forbidden automation, division,
  remainder, CRT, beta, or classical edge is introduced. This checkpoint has
  60 signed candidates, 63 campaign candidates in total, and 72 exact
  receipts; the public registry remains unchanged at 393. D07 natural
  scaling is the next proof layer. No public admission, commit, push, or
  deployment is claimed by the proof receipt itself. The source checkpoint is
  sealed as `497d0fc3327e6fa2564aad8b44c4ce151e20269c`. A clean 47-source
  Jupyter Book build and integrity pass produced 2,325 HTML pages with zero
  broken, escaping, unsafe, or remote-runtime links; its 2,493-file HTML tree
  has SHA-256
  `2eaf9bc60642a29f101a472553c1f21bb5dc30baab3c8bf76665550d9135f59f`.
- **D07 natural scaling (2026-08-04):** ten isolated, closed, nonpublic
  candidates establish `SignedNatScale`: five core rows give both directions
  of the decoded scaling equation, its iff packaging, totality, and literal-
  code functionality; five law rows give a reusable natural cross-sum helper,
  decoded-equation composition, zero, one, and graph composition. The focused
  core and law suites pass all 8 and 9 tests, respectively. Exact closed
  receipts `(nodes, depth, DAG objects, DAG edges, reused references, Cuts,
  DAG SHA-256)` are
  `signed_nat_scale_total = (431, 39, 416, 430, 15, 8,
  e1ee2921a7e967369bd70cd70564ef340ad643926c15c62dba394ae535e76947)`,
  `signed_nat_scale_functional = (1698, 36, 1047, 1080, 34, 34,
  59f948b0d2c8335cd3cd0098fb4acec9f895d8db2f930393d4dad33375ee2727)`,
  and `signed_nat_scale_compose = (1453, 34, 897, 923, 27, 30,
  7548acf6871b7db3db4ba2cdaf89b9544e2d641c881a9f27e47dc4c77448b49e)`.
  Two cold closures pin the 65-row core stack at
  `511aa0ba4a6dac1a22f52db740f539c675307b5b77b6b1a7d9ef2e00dd8a5331`
  and the complete 70-row signed stack at
  `81a18daf55e564c11dee83ce7465bc91876109a5e6bc092f75e0f31f46e27d8d`.
  Exhaustive audits scan all `17 * 17` scale/input pairs against all 257
  candidate output codes, cover exactly 425 cross-sum and 477 composition
  helper premise cases, check zero and one on 33 codes, and check composition
  on all `17^3` bounded triples. A raw-code trap confirms that natural code
  multiplication is not signed scaling (`2 * 1 = 2`, while twice signed
  code `1` has canonical code `3`). The transitive proof closure is strict HA
  and contains no DNE, forbidden automation, division, remainder, CRT, beta,
  or classical dependency. The checkpoint has 70 signed candidates, 73
  campaign candidates in total, and 82 exact receipts; the public registry
  remains unchanged at 393. The D08 `SignedBezout` bridge is next. The D07
  source checkpoint is sealed as
  `bc45de0da2ff60ca65d81d4b8cef612f0b935892`. Its clean 47-source Book
  build passed integrity with 2,325 HTML pages and zero broken, escaping,
  fragment, unsafe, or remote-runtime links; the 2,493-file HTML tree has
  SHA-256
  `7be58cd44aa4b2a8b4e1a233fc9db6101dc478b097f0a22f028d2391b7b194e6`.
  No public admission, push, deployment, or visual click-through is claimed.
- **D08 signed Bezout bridge (2026-08-04):** four isolated, closed,
  nonpublic candidates prove reusable balanced-equation transport, normalize
  a legacy four-natural Bezout witness into two canonical signed codes,
  recover the raw witness from signed codes, and package the two implications.
  Exact endpoint receipts are
  `balanced_bezout_equation_transport = (943, 34, 497, 518, 22, 20,
  9e3f3b984b0c9bdd42e7747f5660541364bb5bee3655b95b9242e5ed3305e4cc)`,
  `balanced_bezout_to_signed_bezout = (1241, 39, 722, 744, 23, 24,
  f39a790749e8da2b6d6c36f3639e2b81ecdd1b5db892a543a7ece18941978923)`,
  and `balanced_bezout_iff_signed_bezout_exists = (1326, 40, 807, 829,
  23, 26,
  1bc7e28457b07b7aaf37b48aea0f3f86b58035797aeca50a022c73409f6eae1d)`.
  The focused ten-test audit checks the RFC expansion, both witness orders,
  exact bodies and closures, mutations, no orphan rows, 2,185 helper cases,
  5,736 raw normalization cases, 1,600 bounded graph cases, nonuniqueness,
  zero coefficients, and raw-code traps. Two cold closures agree on the
  74-row digest
  `b7949148236ab243830a2bfebd80ddafeb31a63c5e70ace1c032de8bd2415f15`.
  The strict closure has no DNE, forbidden automation, division, remainder,
  CRT, beta, or classical dependency. The campaign now records 74 signed/77
  total candidates, 86 receipts, 16 K3 modules, and 18 focused tests; the
  registry/public references/definition freeze/catalog remain
  393/56/45-over-44/394. Nothing is admitted. The gcd client remains a
  separate K4 step because its public dependency closure reaches division.
  The integrated local gate passes 29 campaign-structure tests and all 142
  proof/admission tests. Independent checks keep the 394-row knowledge base,
  393-theorem snapshot, and 492-note/4,991-link vault green.
  The source checkpoint is sealed as
  `bb02ee5a767f6c4c585916269de688e7068b3716`. Its warning-free 47-source
  Book rebuild passes integrity with 2,325 HTML pages, byte-identical
  2,285-file source/built explorer trees, and zero broken, escaping,
  fragment, unsafe, or remote-runtime links. The 2,493-file HTML tree has
  87,178,354 bytes and SHA-256
  `ee4f046d54b019e780d05dfcf2fd75af7f1c481c930cea3de219a6c1c0870a8b`.
  No push, deployment, public admission, or visual click-through is claimed.
- **K4 signed gcd/Bezout client (2026-08-04):** the isolated nonpublic
  `gcd_signed_bezout_exists` candidate composes public
  `gcd_balanced_bezout_exists` with D08
  `balanced_bezout_to_signed_bezout`. Its exact expanded statement has
  SHA-256
  `2e729fe9d25b8afda315489713f0a4cd7980371bf621e8af9e557f4ffca7496e`;
  the closed receipt is `(3535,48,1734,1824,91,74,
  4edeb4ffc7de0b9aa0a870d2125f7640f2447a7358ba454abba3db003f9044a3)`.
  The closure has zero DNE and no CRT, beta, or classical dependency, but it
  intentionally reaches the public Euclidean division chain. The manifest
  therefore adds the honest `K3 -> K4` edge and keeps this theorem outside the
  unchanged 74-row strict-K3 stack. The campaign now has 78 candidates and 87
  receipts across 18 modules and 19 focused tests; public counts remain
  393/56/45-over-44/394. The integrated gate passes 29 campaign-structure
  tests and all 148 proof/admission tests. Independent checks keep the
  394-row knowledge base, 393-theorem snapshot, and 492-note/4,991-link vault
  green. Nothing is admitted.
  The source checkpoint is sealed as
  `1d10c37535d829280398c2522ff3fd9d5f059e6c`. The warning-free Book rebuild
  passes integrity across 47 sources and 2,325 HTML pages, with byte-identical
  2,285-file source/built explorer trees and no broken, escaping, fragment,
  unsafe, or remote-runtime links. Its 2,493-file HTML tree has 87,187,069
  bytes and SHA-256
  `647d12228514a9ad11ea227ac5ef436d18382cf0d8664e2cc3ea44fd0ab9ac07`.
  No push, deployment, public admission, or visual click-through is claimed.
- **K4 canonical gcd and relational lcm checkpoint (2026-08-04):** five
  canonical-gcd edge candidates, a 17-row universal-property `IsLCM` API, and
  the nine-row constructive A--I totality ladder are closed in isolation.
  The relation itself forces `lcm(0,b)=lcm(a,0)=0`, because every multiple of
  zero is zero. The product identity is a theorem about independently stated
  `IsGCD(g,a,b)` and `IsLCM(l,a,b)` predicates, not a definition of lcm by
  dividing `a*b` by gcd. Body receipts
  `(dependencies,commands,nodes,depth,objects,edges,reused)` for F--I are
  `(10,108,209,45,209,208,0)`, `(1,10,33,19,33,32,0)`,
  `(2,17,40,24,40,39,0)`, and `(3,31,43,21,43,42,0)`.
  Empty-context receipts
  `(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` are F
  `(9038,60,2390,2510,121,101,0,
  dfe0e69fb172e48b6aa785c0c088ebf1a7cdf09c95ae436305d51d6224e90bc3)`,
  G `(9071,61,2423,2543,121,102,0,
  f4e764738627255eb885d78b5cefd74663d68be022370a8036ee450b116a7220)`,
  H `(9791,62,2565,2691,127,111,0,
  3ab4c410a0e4c6717e77d7f951d26304a35b5e9451df299167bb42cadf227747)`,
  and I `(10441,61,2569,2696,128,112,0,
  c0829496624e993a4c437aa98c32355605109e728acd03d6b5d857fcb5350d0a)`.
  The campaign totals are 109 candidates, 118 receipts, 21 candidate modules,
  and 22 focused tests; the new closures have zero DNE. Public counts are
  unchanged at `393/56/45-over-44/394`. The integrated source gate passes all
  29 campaign-structure tests and all 175 proof/admission tests; the
  independent 394-entry knowledge base, 393-theorem snapshot, and
  492-note/4,991-link vault checks also pass. No admission, push, or deployment
  is claimed. The source checkpoint is sealed as
  `9b2feb66b5fcc2530394f5b6bcce5e63dfea627f`. Its warnings-as-errors,
  47-source Book rebuild passes integrity across 2,325 HTML pages with
  byte-identical 2,285-file source/built explorer trees and zero broken,
  escaping, fragment, unsafe, or remote-runtime links. The 2,493-file HTML
  tree contains 87,206,047 bytes and has SHA-256
  `1468972f63c3c9122fb0341559ac31f31e602589801381e60cb94e3b5d916472`.
  No visual click-through is claimed.
- **Selective K4 gcd/LCM admission (2026-08-04):** the public tail now contains
  exactly seven universal LCM rows—two projections, leastness, symmetry,
  uniqueness, and both forced-zero constructors—followed by all nine A--I
  gcd/LCM bridge rows. All 16 retain their isolated factory specifications,
  two-cold-pass receipts, zero-DNE property, and mutation gates. The public
  registry is 409; the catalog is 410 with 386 `checked_m20` rows. Exactly 19
  reviewed K4 candidates remain private: three canonical-gcd package rows,
  five gcd edge rows, ten LCM convenience rows, and the signed-gcd client.
- **Generalized-CRT congruence foundation (2026-08-04):** an eight-row isolated
  stack reuses the exact `mod_eq_add_cancel_left` candidate and adds seven
  constructive rows for zero modulus, right cancellation, scale/unscale,
  comparison of common solutions, compatibility necessity modulo relational
  gcd, and the incompatibility obstruction. Two cold closures and the focused
  six-test audit pass with zero DNE. Sufficiency, solution construction, the
  complete class modulo relational LCM, canonical representatives, finite
  generalized CRT, and public admission remain open.
- **Generalized-CRT M5a binary sufficiency (2026-08-04):** seven additional
  isolated candidates now prove `factor_nonzero_right`, coprimality and a
  reusable nonzero package for gcd cofactors, a shared bounded remainder for
  compatible residues, the scale-and-add lift from public `binary_crt`, the
  compatible-system existence theorem, and
  `generalized_binary_crt_solvable_iff_nonzero`. The capstone says exactly
  that for nonzero `m,n` and `IsGCD(g,m,n)`, a common CRT solution exists iff
  `ModEq(g,a,b)`. Its empty-context receipt is
  `(10073,76,3316,3476,161,149,0,
  8956a66d8f72d512f840464d2749e43258a2b74b3828dde58f2c206d53af0234)`
  in `(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` order. Two cold
  closures agree, mutation-sensitive tests pass, and no checker limit was
  raised. The campaign manifest now records 72 public references, 108
  candidate references, and 133 exact receipts. These rows remain private;
  zero-modulus wrappers, classification modulo relational LCM, bounded
  representatives, finite lifting, and deliberate admission are next. The
  integrated gate passes 30 campaign-structure tests and 189 proof/admission
  tests. The refreshed 47-source Book passes integrity across 2,325 HTML
  pages; its 2,493-file HTML tree has SHA-256
  `b322fe004bee4cfcd511973b74365f9d0c4b798d0b0c5711d352ba7046c1d579`.
  The browser application seal is `a-ed049a6d3d2c` with 175 worker sources.
- **Generalized-CRT M5b all-modulus closure (2026-08-04):** four further
  isolated candidates close the zero boundary and remove the nonzero premises
  from the binary solvability criterion. The left-zero and right-zero rows use
  only public relational-gcd symmetry, the public zero constructor, gcd
  uniqueness, and congruence reflexivity/symmetry; they do not depend on the
  private canonical-gcd edge conveniences. Constructive `eq_decidable`
  dispatches left-zero, right-zero, and both-nonzero cases, and the earlier
  necessity theorem yields `generalized_binary_crt_solvable_iff` for arbitrary
  natural moduli. Exact empty-context receipts are
  `zero_left = (834,37,682,717,36,26,0,
  074f07df173308477693b6e3bbfd3a3a4123078d8f7f5eaac9077666d3cbc763)`,
  `zero_right = (805,36,653,688,36,26,0,
  da2d830f65077816dfeecd1503a787cf8ba0f5ec99e93d13b5456e4ba772e2f6)`,
  `total_sufficient = (11240,78,3495,3662,168,160,0,
  931fbcc775154507996c768cb1de1cc8479c3ed805ce0d1a95fffb530e8b56c4)`,
  and `total_iff = (11825,80,3658,3830,173,168,0,
  3f1d82f0f06df9e0d2a5c746405ee46406db71c57e4bbf32f68792be07af8b0c)`
  in `(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` order. The `(0,0)`
  case is contained in the left-zero row; no remainder below zero is asserted.
  All four rows fit the existing limits with zero DNE, so neither the kernel
  nor any formula/proof limit changed. The campaign evidence becomes 112
  private candidate references and 137 receipts, while the public registry
  and catalog remain exactly 409 and 410. Relational-LCM classification,
  bounded canonical representatives, executable compatibility decisions,
  finite lifting, and deliberate admission remain open.
  The integrated gate passes 30 structural and 194 proof/admission tests; the
  unchanged public knowledge base/snapshot/vault gates remain green. The
  176-source browser application is sealed as `a-4286adc4e7f3` with
  `BUILD=2026-08-04d`. The 47-source Book rebuild passes integrity over 2,325
  HTML pages, and its 2,493-file HTML tree has SHA-256
  `df5eb6326836ce5d1f7ba8ce780dc24dcf6f2878cc1aff6a836e0b3790ada009`.
- **Generalized-CRT M5c relational-LCM classification (2026-08-04):** four
  isolated candidates close the complete class of solutions relative to a
  fixed solution. `mod_eq_ordered_gap_multiple` proves
  `k+x=y -> ModEq(d,x,y) -> Dvd(d,k)` from `add_comm`, `add_assoc`,
  `add_left_cancel`, and `factor_difference`; `mod_eq_lcm_merge` combines two
  input congruences by `le_total`, gap divisibility, and `is_lcm_least`;
  `mod_eq_lcm_iff_pair` packages congruence modulo a relational LCM iff the
  pair of input congruences; and `crt_solution_class_iff_lcm` proves, for a
  fixed solution `x`, `CRTSolution(y) iff ModEq(l,y,x)`. Their body receipts
  `(dependencies,commands,nodes,depth,objects,edges,reused)` are
  `(4,31,44,21,44,43,0)`, `(6,113,127,26,127,126,0)`,
  `(4,46,56,21,56,55,0)`, and `(3,62,79,27,79,78,0)`. Exact empty-context
  receipts `(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` are
  `(558,30,310,325,16,13,0,
  6a30012cfc1213bf167be2de794e05cdae2893ab075cfc24abf9b181bde9be67)`,
  `(1315,33,653,685,33,25,0,
  46cd67f69ccf0c669de283fca6a74a0a85cf18d54f248f1a6f428122196a331b)`,
  `(1570,37,864,908,45,32,0,
  855d5745c1613304fc0a5f26c70fe9f795ed3ebcff4a7276e3745681d41fc91a)`,
  and `(2208,39,1055,1104,50,40,0,
  305a913aaca1c3e307d8ca77bb90c063dd67f3fa9f9bdd69e28cf4064cdff7b3)`.
  The capstone orientation is audited as `y` to fixed `x`; its reverse branch
  composes that congruence with the two facts carried by `x`. At `l=0`,
  `ModEq(0,y,x)` is equality, so the same theorem gives exact uniqueness
  without division or a false remainder-below-zero claim. The bounded oracle
  passes 1,296 LCM-iff, 4,692 fixed-class, and 678 zero-LCM comparisons. All rows
  have zero DNE and fit unchanged limits. Evidence is now 116 private
  candidate references and 141 exact receipts; public registry/catalog counts
  remain 409/410. M5d is frozen to three rows only: zero-LCM exact
  uniqueness, a nonzero-LCM unique bounded remainder, and the constructive
  all-modulus canonical-boundary disjunction.
  The integrated gate passes 30 structural and 200 proof/admission tests; the
  unchanged public knowledge base/snapshot/vault gates remain green. The
  177-source browser application is sealed as `a-6353222cdacb` with
  `BUILD=2026-08-04e`. The 47-source Book rebuild passes integrity over 2,325
  HTML pages, and its 2,493-file HTML tree has SHA-256
  `a034d5c96b3aa7a108526b013edbcf21e326701b8241d6e97f49b2f7c36a8cd5`.
- **Generalized-CRT M5d canonical boundary (2026-08-04):** three isolated
  candidates close the mathematically honest canonical form for all natural
  moduli. `crt_solution_unique_lcm_zero` converts M5c classification into
  exact equality when `l=0`; `crt_solution_canonical_remainder_nonzero`
  divides a fixed solution by nonzero `l`, transports the remainder back into
  the solution class, retains `ModEq(l,r,x)`, and proves bounded uniqueness;
  `generalized_binary_crt_canonical_boundary` constructs a solution by M5b,
  decides `l=0`, and returns either exact uniqueness or a unique `r` with
  `Below(r,l) := exists h. h+S r=l`. Body receipts are
  `(2,33,37,28,37,36,0)`, `(6,83,141,39,141,140,0)`, and
  `(4,66,76,33,76,75,0)`. Closed receipts are
  `(2300,40,1126,1176,51,43,0,
  2afc46ac88613c95400eb37f80b1fbda095b18a7f6a774255426b48c35aed9ac)`,
  `(4086,65,1668,1746,79,64,0,
  091e8f2b1ba7e4665b87071fcd924ea1098880d65a97bcdd264ed544e33ff0e4)`,
  and `(17750,80,4239,4426,188,193,0,
  c704a17f6feed83142b160bbeafcc14764d5ae6590999187eed5455c3ad03bd7)`.
  All have zero DNE and fit unchanged limits. The retained audit passes 4,021
  compatible systems: 611 zero-LCM and 3,410 nonzero-LCM cases. Campaign
  evidence is 119 private candidates and 144 receipts; public registry and
  catalog remain 409/410. The integrated gates pass 30 structural and 206
  proof/admission tests, the 508-note/5,119-link vault is unchanged, and the
  178-source browser app is sealed as `a-1963d4a52744`
  (`BUILD=2026-08-04f`). The warning-free 47-source Book passes integrity over
  2,325 HTML pages; its 2,493-file HTML tree has SHA-256
  `3d2acf4edad4774379b3d618fcd16612e9bb9d855638e20f8936b862599a4fac`.
  Executable decision/obstruction output, deliberate admission, and finite
  lifting remain; no zero branch asserts a remainder below zero.
- **Generalized-CRT M5e executable boundary (2026-08-04):** two isolated
  candidates make the supplied-relational-gcd binary API total.
  `mod_eq_decidable` handles modulus zero through equality decision and
  `mod_eq_zero_iff_eq`, and nonzero modulus through the public remainder-based
  decision theorem. `generalized_binary_crt_solution_or_obstruction` returns
  either `ModEq(g,a,b)` with a CRT solution or `~ModEq(g,a,b)` with a proof
  that no CRT solution exists, using total M5b sufficiency and the direct
  obstruction theorem. Body receipts are `(3,35,47,16,47,46,0)` and
  `(3,36,43,22,43,42,0)`; closed receipts are
  `(2339,70,1217,1278,62,44,0,
  298e2b18fff84bcf3a2ec69dbc464454f958d4155b7afb687f0bab2fd95efe7e)`
  and `(14182,80,3909,4090,182,182,0,
  16e7cb1c430fa4e17ea878adc72d34c92e0bc3f135c4a3cf24cb2a296b38e525)`.
  Both have zero DNE and fit unchanged limits. Retained semantics cover 847
  congruence decisions and all 5,929 bounded CRT systems: 4,021 solution
  outputs and 1,908 obstruction outputs, including the full gcd-zero split of
  11 compatible and 110 incompatible residue pairs. Evidence is now 121
  private candidates and 146 receipts; public registry/catalog remain
  409/410. Integrated gates pass 30 structural and 212 proof/admission tests,
  plus 25 browser/deployment tests; the 508-note/5,119-link vault is unchanged.
  The 179-source browser app is sealed as `a-ef0683604e9b`
  (`BUILD=2026-08-04g`). The warning-free 47-source Book passes integrity over
  2,325 HTML pages; its 2,493-file tree has SHA-256
  `ff252854e07935c02016e79b44d831e440aa91c308875181427a72cc90ab3941`.
  The raw-input gcd wrapper is supplied by M5f below; minimal admission and
  finite lifting remain, while M5d stays the separate canonicalization API.
- **Generalized-CRT M5f raw-input total decision (2026-08-04):** the isolated
  `generalized_binary_crt_total_decision` candidate removes the supplied-gcd
  precondition from the executable M5e endpoint. For arbitrary `m,n,a,b`, it
  first uses `gcd_exists_relational` to construct a witness `g` with
  `IsGCD(g,m,n)`, then applies
  `generalized_binary_crt_solution_or_obstruction` and returns that gcd
  certificate together with either compatibility and a CRT solution or
  incompatibility and a proof that no solution exists. The exact statement
  SHA-256 is
  `42d29bf501421be60c1a2b14fa858a14abf230eee2f7669503db019d6b014151`.
  Its body receipt is `(2,17,42,25,42,41,0)` and its closed receipt is
  `(15492,82,4052,4240,189,192,0,
  c2d915d2eb60ccbb2dac9f31e9e1f9c310c28264b74483ec97ae33a1a0d965ee)`.
  The closed certificate contains zero DNE and fits the unchanged limits.
  Retained semantics cover all 5,929 bounded raw CRT systems: 4,021 solution
  outputs and 1,908 obstruction outputs, including the gcd-zero split of 11
  compatible and 110 incompatible residue pairs. Campaign evidence is now
  122 private candidates and 147 receipts across 27 candidate modules and 30
  focused test paths. The generalized-CRT tranche contains 29 rows: 28 new
  rows plus one reused support row. This is an existential relational-gcd
  wrapper, not a primitive gcd function and not a canonical bounded solver;
  M5d remains the separate canonicalization API. Deliberate admission and
  finite lifting remain. Integrated gates pass 30 structural and 217
  proof/admission tests, plus 25 browser/deployment tests; independent checks
  retain 410 catalog rows, 409 public theorems, and the 508-note/5,119-link
  vault. The 180-source browser app is sealed as `a-5f816312f00a`
  (`BUILD=2026-08-04h`). The warning-free 47-source Book passes integrity over
  2,325 HTML pages; its byte-identical explicit/defined explorer trees contain
  2,285 files, and the 2,493-file HTML tree has SHA-256
  `59d566a0af7a86a36cca7cd02958f27ba244e10871a222c5a4dcf2ccbf94efe4`.
- **Generalized-CRT M5 selective public admission (2026-08-04):** the exact
  23-row candidate-factory closure of `generalized_binary_crt_solvable_iff`,
  `generalized_binary_crt_canonical_boundary`, and
  `generalized_binary_crt_total_decision` is now public at ordered runtime
  indices 409--431. This admits the constructive solvability criterion, the
  complete solution class and zero/nonzero canonical boundary, and the
  executable solution-or-obstruction interface with an existential relational
  gcd. It deliberately leaves exactly six private rows:
  `mod_eq_add_cancel_left`, `mod_eq_add_cancel_right`,
  `mod_eq_unscale_nonzero`, `factor_nonzero_right`,
  `is_gcd_nonzero_coprime_quotients`, and
  `generalized_binary_crt_solvable_iff_nonzero`. The runtime now has 432
  theorems and the catalog has 433 rows: 23 `checked_existing`, 409
  `checked_m20`, and one `blocked_by_language`. Campaign accounting is 95
  public references, 99 private candidates, 147 receipts, 22 candidate
  modules, and 31 focused test paths. The regenerated public snapshot has
  1,982,360 structural nodes, 468,010 proof objects, 57,692 structural Cut
  occurrences, 373 Cut-bearing theorems, 1,185 dependency edges, and ordered
  root
  `4d02dc439d53533e8992a471b26ee34059fb6001f822041e42c56b2cc0a7a079`.
  The synchronized vault has 432 theorem notes, 531 total notes, and 5,377
  resolved links. The integrated admission gates pass 30 structural and 220
  proof/admission tests, while all 25 browser/deployment contracts pass. The
  180-source local browser app is sealed as `a-b544a04993a1`
  (`BUILD=2026-08-04i`); no deployment is claimed. The warning-free 47-source
  Book rebuild passes 26 source/explorer tests and integrity over 2,325 HTML
  pages. Its byte-identical source/built explorer trees contain 2,285 files,
  and the 2,493-file HTML tree has SHA-256
  `d9eddd01a0dcc228ceb17b75c8595f743c7e2b6bdcb1ba44e9c260e98b33f558`.
- **K3 doubled-Cantor pair core (2026-08-04):** 15 isolated, nonpublic
  `HA-K3-PAIR-1` candidates now close twice from the empty context across
  three modules. Seven seed rows prove literal D01/D02/D05/D06/D08
  constructors, fixed-component pair output functionality, validity, and the
  nil/constructed-cell boundary. Six shell rows prove doubled-triangular
  successor arithmetic, monotonicity, offset bounds, pair-code lower/strict
  upper bounds, and separation of distinct shells. `double_add_injective`
  then closes at 493 nodes/depth 25/15 Cuts with certificate SHA-256
  `b0905453455317eb8e7bb8e7835fd049ad6afb98dabbf865719c02e2cc5b33ec`;
  exact D01 `pair_code_injective` closes at 2,525 nodes/depth 32/59 Cuts with
  certificate SHA-256
  `7dc47f845a11797827e8682f4223af1e083afd48af60e0e22cd56862c44d06d8`.
  All rows have zero DNE, fit unchanged limits, reject nearby false
  mutations, and have a K0--K2-only transitive closure excluding division,
  remainder, beta coding, CRT, and classical logic. Campaign accounting is
  now 95 public references, 114 private candidates, 162 receipts, 25
  candidate modules, and 34 focused test paths; runtime/catalog remain
  432/433. The regenerated 183-source local browser app is sealed as
  `a-86a703f70af4` (`BUILD=2026-08-04j`), with no deployment claimed. Cell
  functionality, strict head/tail bounds, uniform lists, and finite maps are
  not claimed. The warning-free 47-source Book rebuild documents this exact
  private boundary and passes integrity over 2,325 HTML pages; its 2,493-file
  HTML tree has SHA-256
  `11b88b5d21c4c28d13aede8976b99b8b438812d738b2a7d69e8a20e20378fb38`.
- **K3 pair/cell functionality and descent API (2026-08-04):** seven further
  isolated `HA-K3-PAIR-1` candidates complete the private proof API through
  exact D06 functionality and strict component descent. `cell_functional`
  removes the common successor tag with PA2 and applies exact D01
  `pair_code_injective`; `cell_head_functional` and
  `cell_tail_functional` project its conjunction. Their closed receipts are
  `(2550,33,1146,1211,66,60,e1cfdfcfbe2b1bfb70f51cc724280d3bc7ac046c4bd14865bf390952b412a45c)`,
  `(2569,34,1165,1230,66,61,289cb3b6a42ca39e424e40712e44a24e4b7d4c7b355c4c0bd697d75ae42dfc9f)`,
  and
  `(2569,34,1165,1230,66,61,e03fdd8affeba3e1c0c1cb6f6e496c6ac53b13469db8c9c5b517f0df9de72d5c)`.
  `pair_left_le_code`, `pair_right_le_code`, `cell_head_lt_code`, and
  `cell_tail_lt_code` close respectively at
  `(257,18,173,184,12,8,2216484e9a09321c065b6fbac742ff1763b28f799720fb4b729468cdeaa8ce3c)`,
  `(181,18,170,180,11,7,48ae46ea34331fc1cdadc03a0e510681748aeade658cf1d9783ab6e7a6740601)`,
  `(304,20,220,231,12,10,4cbccb9c232ff1ee40d05a3ee0520e5a99beeeebb645f3e5142a5c40681d1d3d)`,
  and
  `(228,20,217,227,11,9,145f2c4c0c00c4b7145a6f847e90af1dd72e500b1d88b03e7ed4fdd267d2867b)`.
  Every row closes twice cold, contains zero DNE, rejects false mutations, and
  has a K0--K2-only dependency closure. Campaign accounting is 95 public
  references, 121 private candidates, 169 receipts, 27 candidate modules, and
  36 focused test paths. Strict K3 is 96 rows in 21 modules: 74 signed plus 22
  pair/cell. Runtime/catalog remain 432/433; no new theorem is public. The
  regenerated 185-source local browser app is sealed as `a-0d9a06f601cf`
  (`BUILD=2026-08-04k`), with no deployment. Valid-code decision, uniform
  computation histories, lists, maps, and public admission remain open.
- **K3B reverse cell-history closure checkpoint (2026-08-04):** the
  `HA-K3B-CELLHISTORY-1` RFC and exact `CellHistory`/`CellListLen` expansions
  are frozen as a post-K4/M3 bridge, outside strict K3. WMI job `219203`
  checked all eight first-ten theorem rows twice from the empty context.
  Exact `(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)` receipts
  are `cell_history_nil = (155,18,155,154,0,2,a3038bd67616f11f8e97727c98f03af09aacde863a70637d9575e2ff9d337ff8)`,
  `cell_history_extend = (29352,81,4651,4879,229,241,370de792b2c3fed8b3d36f90147c426b846d15578cac8c66520a59df81750c78)`,
  `cell_history_succ_elim = (1245,60,772,810,39,27,e8aee67cfef618fde3b08d48dffb4a6b31cdd22a578e38206d4e5a20a96c338c)`,
  `cell_list_zero_iff_nil = (1309,60,880,916,37,26,f7fdef58a28a86bd70b133bf839f6b49526817e020da6c698b85b3cd369f2f73)`,
  `cell_list_succ_iff_cell = (30648,83,4761,4992,232,246,a64ad8e5095d50afe10b47b1036ad9b680ab82462b41beb115d23956f9fa5699)`,
  `cell_list_length_functional = (34732,85,5700,5976,277,299,5dd0e4b8f585990ec826ba5ef02960cb6817f0aec5edcb86c9bb1e22d44c5a6c)`,
  `cell_list_length_le_code = (31002,84,4891,5129,239,257,50fe47364958e1a506315935796e517f41ddd947a1792fcdb134956ba05290a9)`, and
  `cell_list_length_total = (29569,84,4848,5078,231,246,2d6063d54e16c0f093aab270329bdd4ca5a7c02aa68b528c2c7c771945ccba17)`.
  All have zero DNE and status `closed_checked_candidate`. The authoritative
  report `artifacts/peano-library/ha-k3b-cell-history-closure-219203.json`
  has SHA-256
  `6ef49fcb5edb2b1c5478ff592c97dc9af56ed2f79ec03308c5ebf341833b825c`.
  Job `219203` completed `0:0` on `c3n1` in `00:04:46`, `MaxRSS=82428K`,
  from clean commit `0b33b6675481a93d0e330987b22d9ef91564a0a0` and payload
  `edf77bff5cf824cbfd549179f8cef2a18ac65904d473ce3bbd2bd5e5f1c95620`
  (3,911,680 bytes, 201 entries). Gates G1--G6 and G7 quarantine/closure pass;
  admission is deliberately unperformed. Every row remains private,
  unregistered, and unadmitted. Strict K3 stays 96 rows/21 modules and the
  unchanged campaign JSON stays 95 public/121 candidates/169 receipts.
- **K3B `ListAt` surface freeze (2026-08-04):**
  [`HA-K3B-LISTAT-1`](research/arithmetic-library/ha-cell-list-lookup-rfc-v1.md)
  selects outer-head lookup through `j + S i = l`, with normative witnesses
  `l b c j t u`. The hygienic expansion is 3,331 characters, 54 formula
  constructors, 210 PA AST nodes, and SHA-256
  `b83d91b6ec8e6b83fe637e1533c72beef54c7e7a4b41f1518bce8785cc9f11ce`;
  seven focused tests pass. The required
  `cell_history_extend_preserves_prefix` support row now has a checked body
  receipt `(5,99,139,37,139,138,0)` and four focused audits. WMI job `219209`
  closed it twice at
  `(29369,81,4668,4896,229,241,7fd7734ab34d90a869c637e76e138db692ba21d4f2bbec41af9817c38ef36498)`;
  the report SHA-256 is
  `0d51baf93121da4071d0bb3ebd2b4a2818a7658fa92510fd707620bc2dba6560`.
  It remains private and unadmitted. This row must precede successor
  introduction because the current extension theorem hides the old
  beta-prefix transport.
  Runtime/catalog, campaign accounting, and strict K3 remain exactly 432/433,
  95/121/169, and 96 rows/21 modules.
- **K3B lookup domain projection (2026-08-04):** `list_at_domain` eliminates
  the six hidden lookup witnesses and returns `CellListLen(z,l)` plus the
  native bound `k+S i=l`. It has no dependencies; its statement receipt is
  `(5903,065291362205b70ef41fff597d1d8762bff06ce7d3a5bead5dbcd8b97ea8a240)`
  and its Cut-free/DNE-free proof receipt is `(0,19,39,23,39,38,0)`. The row
  is private and awaits the next repeated cold lookup batch.
- **K3B outer-head equation body (2026-08-04):** the private
  `list_at_head_iff` statement expands to 12,530 characters with SHA-256
  `9f0b3e7496f79b7cc6f4833edc14431dd614081b6f02b2d384aa80c521e2f8ed`.
  Its dependency-curried body receipt is `(4,119,265,36,255,264,10)`, with
  direct dependencies exactly `cell_history_succ_elim`,
  `cell_history_extend_preserves_prefix`, `beta_at_unique`, and `le_refl`.
  Beta uniqueness is used once at `S j` for the terminal code and once at
  `j` for the predecessor tail, so `cell_tail_functional` is not a dependency.
  This is body-checked evidence only: no cold closure, registry entry,
  admission, public theorem, or campaign-accounting change is recorded.
- **K3B successor lookup equation body (2026-08-04):** private
  `list_at_succ_iff` has statement receipt
  `(14716,004ef041acbcfbaaeda594f5f47fbea75ac6f8df87ca8bcf49774cfcbc3a978c)`
  and dependency-curried body receipt `(3,124,198,38,196,197,2)`. Its exact
  dependency order is `cell_history_succ_elim`,
  `cell_history_extend_preserves_prefix`, `add_comm`. The direct same-history
  proof needs neither `list_at_head_iff` nor PA2: forward elimination retains
  `b,c`, while reverse extension preserves the selected entries at `j` and
  `S j` using additive witnesses `S i` and `i`. The body has zero DNE but no
  cold closure, registry entry, admission, public theorem, or accounting
  change.
