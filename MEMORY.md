# Project Memory — VIASM 2026 "Automatic Theorem Proving in Mathematics"

> Durable facts about this project. One fact per bullet; update in place rather than duplicating.
> This is the human-and-agent-readable ground truth; the dated narrative lives in [`JOURNAL.md`](JOURNAL.md),
> the actionable breakdown in [`PLAN.md`](PLAN.md).

## Identity

- **What:** A 6-lecture mini-course *An introduction to automatic theorem proving in mathematics* for
  **VIASM** (Vietnam Institute for Advanced Study in Mathematics, Hanoi), 2026.
- **Author:** dr Bartosz Naskręcki — Faculty of Mathematics and Computer Science, Adam Mickiewicz
  University in Poznań (WMI UAM); also Centre for Trustworthy AI (CCAI), Warsaw University of Technology.
- **Active local repo root:** `/Users/bnaskrecki/codex/peano` (git `peano-lab`).
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
  M19 is the active, not-yet-complete post-training milestone. Its compact headless adapter is not
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
  theorem reuse, and the current 189-entry checked ladder (whose initial public-catalog/M20
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
  theorem probes are complete. Model-v2 curriculum/search work, controlled model comparison, and
  milestone-wide release gates are not yet complete.
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
  and 170 documented commands replayed, and 412/412 Obsidian wikilinks resolved. The remaining M19
  work is the model-v2 curriculum/search experiment, not repair of this recorded result.

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
- The current native arithmetic runtime has 189 unique checked theorems: 23
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
- **Current M20 native FTA and unbounded-primes checkpoint (2026-07-29):** the runtime now contains
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
  The untrusted import and live-proof gates are aligned at 100,000 nodes and
  depth 256; exact boundary and transactional-failure tests cover them.
- **Constructive prime unboundedness:** `prime_unbounded` constructs a nonzero
  common multiple through an arbitrary bound `n`, chooses a prime divisor of
  its successor, and proves that divisor is above `n`. If it were at most
  `n`, it would divide both the common multiple and its successor, hence one,
  contradicting primality. Its exact certificate has 4,595 nodes, depth 82,
  146 self-contained Cuts, and SHA-256
  `8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b`.
  It uses PA1–PA6 only, contains no DNE, and passes exact-statement,
  dependency-slot, PA-leaf, authored-hypothesis, and live-use audits.
- **Current M20 generated identities:** the 247-theorem snapshot contains
  982,534 structural nodes and 28,892 Cuts across 204 Cut-bearing
  certificates. Its ordered root is
  `eb4775dfd181dc5e45bec463a93f14b0ea9d02501c40c5167b7cae77cd4ff432`
  and source digest is
  `295ca3b65970324e7d2ed51b57dc4510227b0abbc2d35b68a809dbde26aba868`.
  The Obsidian graph has 327 notes and 3,286 resolved links, including 247
  lemma notes. The deterministic 1,692-session/13,344-transition corpus has
  fingerprint
  `6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`;
  its isolated smoke has 494 sessions, 9,235 raw/9,232 unique transitions,
  and all 247 authored QEDs. Local browser build `2026-07-29k` packages
  manifest identity `a-77df7c0860bc`; it is not staged or deployed. The strict
  book rebuild passes 38 sources with no warnings; 195 deep links and 47
  executable blocks containing 287 commands verify. A guided ten-stage route
  and generated interactive atlas expose all 247 exact statements, complete
  authored proof recipes, dependencies, dependents, metrics and source/vault
  links. The complete Peano suite passes 1,288 tests with one intentional skip
  in 1,259.11 seconds; Lambda passes 360 tests plus 36 subtests. An in-app
  browser was unavailable, so direct Pyodide and rendered
  book UI smokes are not claimed; automated runtime/worker tests, static HTML
  contracts and the deployment-manifest check remain green.
- **Model-v3 training curriculum (2026-07-29):** the complete 247-theorem
  declaration order is now a content-bound training authority. Exact authored
  predecessor-prefix replay contributes 8,494 transitions, and a separate
  70,000-row, 51-schema synthetic lane balances 14 root tactic heads while
  capping `intro` at 20%. Catalog-derived components are train-only;
  validation and test are synthetic-only, and held-out target formulas are
  rejected at every intermediate state. Prompt-v3 exposes exact theorem
  names and statements and losslessly compacts repeated proof declarations
  with `shared-declarations-v1`; across all 222 stress-proof transitions the
  maximum pinned Qwen3 prompt, completion, and EOS length is 29,111 tokens,
  leaving 3,657 below the native 32,768-token limit. The registered WMI run is
  Qwen3-1.7B Base with rank-32/alpha-64 LoRA, effective batch 32, and two
  epochs. These are implemented and locally verified launch controls, not a
  trained-model result; no model-v3 adapter or solve-rate claim exists yet.
