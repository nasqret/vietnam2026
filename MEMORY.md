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
  library inclusion retains the existing closed-statement, dependency, cut-elimination, test, and
  independent-check workflow. M16 introduces named local reasoning with the exact surface forms
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
  derives its exact surface authority from the embedded dataset attestation. No model has yet been
  downloaded or trained and no Slurm job has been submitted; the model never enters the trusted
  computing base.
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
  theorem reuse, 23-entry semiring ladder, certificate-producing `ring`, and bounded checked
  `norm_num` teaching surface are present. The odd-square induction closes through explicit
  `trans`/`rewrite` structure, while concrete coefficients can now be certified without obscuring
  the independent final check. M19's headless runner, first 10,000-row checked corpus, and policy
  infrastructure have focused green coverage, but the real Helios smoke, model comparison, and
  milestone-wide release gates are not yet complete.
- M19 pre-training infrastructure gate on 2026-07-28: 363 focused tests, 912 full Peano tests,
  Lambda 360 tests plus 36 subtests, clean book build/command replay, and green local staging as
  build `2026-07-28f`, application `a-69aa3b753965`. This is not deployed and is not a model result.
