# Proof readability across the libraries

Implemented on 2026-09-05 and separately deployed to the proof website and
Peano preview that day; see the [deployment record](PROOF_READABILITY_DEPLOYMENT_2026-09-05.md).
This is an authoring and presentation improvement, not a mathematical release
or Alpha promotion. Protected Peano production remains unchanged.
The original Quadratic Reciprocity design, source proof scripts, theorem
statements, kernel, definition identities, proof bundles and admission records
are preserved.

## The policy

1. Use `have h := lemma explicit_arguments` for routine applications of an
   available fact. Excess arguments, wrong premises, unresolved metavariables,
   reused local names and circular references are rejected. The elaborator
   constructs ordinary `ForallElim`, `ImpElim`, and local-cut proof terms; the
   unchanged independent kernel remains the acceptance boundary.
2. Reuse the family's existing conservative definitions. A shorter formula must
   expand to the identical de Bruijn AST in the identical free-variable context.
   Do not invent a name just to conceal an unexplained invariant. A genuinely
   new definition needs the usual conservative-expansion and DAG review.
3. Explain non-obvious choices: the induction parameter, invariant, descent
   measure, witness, and why each extra condition is needed. Identify assumed
   descent steps as assumptions, not as conclusions proved by a wrapper lemma.
4. Present a short reading view first. Keep line references, definition links,
   the complete original ledger, and exact/defined navigation. Do not substitute
   a generic structural description for a claimed human mathematical proof.
5. Audit all families, prioritize the remaining long claims, and preserve
   historical evidence. Never infer proof authority or admission from a reader,
   a content hash, a saved note, or a display equivalence check.

## Authoring and Lean reconstruction

The shared tactic implementation and defined-edition adapters accept the inferred
syntax; the four campaign-specific local-claim formatters preserve it too.
Named library dependencies must already be in the proof context. Compound
natural-number arguments need parentheses. There is no implicit theorem search
or premise synthesis. A substantive intermediate result still uses a typed
`have` and its own proof.

The Lean reconstructor safely abbreviates two old patterns: copying a named
fact, and an exact explicit application, optionally preceded by consecutive
specializations of that same fact. All original commands are replayed. The
shortening is installed only after checking the exact continuation target,
context, variables and remaining goals. Branch labels and scopes are retained;
other patterns keep their typed proofs. `infer_simple_claims=False` selects the
old fully explicit rendering.

Partial applications retain their remaining quantifiers and implications;
omitted premises are never invented or silently discharged.

Three real source-reconstruction regressions illustrate the change:

| Theorem | Original Lean body | Shortened body | Inferred claims |
|---|---:|---:|---:|
| Two-square zero/nonzero classification, TS003F | 11,280 bytes | 1,642 bytes | 2 |
| Binary modular execution logarithmic bound, BD0018 | 10,543 bytes | 3,092 bytes | 2 |
| Two-step Euclidean budget extension, EL0007 | 7,465 bytes | 1,191 bytes | 2 |

These are dependency-relative reconstruction measurements. Subsequent release
validation compiles all three shortened bodies in Lean 4.31.0, with their exact
original dependency statements as explicit parameters and conservative closed
type aliases. These conditional-body checks are not full dependency-closure
compilations or new theorem admissions. Six separate complete Stable/Alpha
strands also pass their existing independent compiler checks.
The new native inferred-application examples also pass the ordinary HA checker
and the existing independently compiled, hash-pinned Lean bundle verifier.
That verifier checks the same serialized native certificates; it does not
compile the newly emitted Lean source text.

The worker inventory includes the new engine module. The preview now serves
`a-4de50afd4366`, build `2026-09-05a`, with the exact `APP_MANIFEST.sha256`.
This does not change the protected production pointer, waive the hosting
cache-header gate, or re-enable public Lean build controls.

## Reading layer and exact evidence

`scripts/stage_proof_readability.py` authenticates the complete preserved public
stage against the fixed accepted `presentation/lean-policy-v1.json`. It creates
a separate no-clobber output, with a final complete inventory comparison. Every
changed HTML page is reversibly wrapped: stripping the reading layer must
recover the exact original bytes. Existing assets and non-page artifacts stay
byte-identical. Additive CSS and JavaScript inherit the original reader palette
and typography; they do not fetch data or execute proofs.

Every defined page is paired with its exact edition by family route, theorem
name, line count and command identity. Some older pages display abbreviated
`have` formulas without an inline native expansion: 3,318 such rows occur in
1,321 pairs. Their native script hashes now come from the authenticated exact
source, and explicit expansion links point there. The preserved defined ledger
is labeled **defined**, not incorrectly labeled an exact native script. Pairing
alone is not advertised as a new formula-equivalence certificate.

For long local formulas, `scripts/proof_reading_definitions.py` loads only that
family's preserved definition corpus. It validates expansion digests, parameter
and alias identities, links, and an acyclic dependency order, including existing
zero-argument closed conditions. The existing conservative matcher re-expands
each replacement and checks exact AST and free-context equality. It neither
imports newer definitions into historical scopes nor changes the original
definition graph. Each applied compaction has a line-specific receipt in the
audit.

Reading checkpoints are consecutive command groups, **not reconstructed proof
branches**. Search, expand/collapse, original-line navigation, and print-state
restoration are progressive enhancements; the complete original content
remains available without JavaScript.

## Measured scope and honest limits

The successful full build covers 8,786 theorem pages in 68 families:
8,194 current-release pages and 592 preserved checkpoint pages. There are
4,393 exact/defined pairs and 3,908 distinct theorem names; page counts must not
be confused with the 4,223-entry Alpha catalogue.

- The defined editions contain 10,973 local claims.
- Existing definitions shorten 198 previously long defined claims. The number
  exceeding 600 display characters falls from 279 to 85; four shortened claims
  still exceed that threshold.
- The exact-edition reading views shorten another 3,543 claims. Together the
  reading views remove 27,981,499 repeated display characters, without deleting
  the original ledgers or mathematical content.
- All 75 current/historical family definition scopes encountered are checked.
  Repeated definitions across scopes are not counted as new global definitions.
- Five theorem names have manually written, exact-script-bound mathematical
  explanations, appearing on ten pages. Other pages explicitly use structural
  descriptions. Library-wide reader coverage is not a claim of library-wide
  human-authored mathematical exposition.
- No local proposition was skipped for the fixed source-size bound. The 85
  remaining long claims remain fully expandable and ranked in the audit. The
  largest remaining example is in the Eisenstein-integer family.

The final default stage built in 79.96 seconds at 227,573,760 bytes peak RSS,
within the original CPU, 180-second wall and 1,536 MiB memory limits. The
implementation streams pages and bounds the family/notation caches. Its
13,556-file manifest is:

```text
10471f7ace1719110af485479052a87dca4cda5a410515d556ebce5473adefc9
```

A fresh default-stage check reproduced that manifest in 70.59 seconds at
417,824,768 bytes peak RSS, without rewriting the existing stage.

All 504,859 inserted local links and 441,247 fragments passed a full link audit.
All 4,393 exact/defined pairs have matching native-script digests.

A final palette regression verifies that the reading layer inherits `--pe-*`
variables in exact editions and `--pd-*` variables in defined editions. The
earlier unpublished candidate was retained under
`_deploy/proof-reading-review-oVh2FN/before-exact-theme-fix`, not overwritten or
deployed. Original preserved base stages remain unchanged.

## Reproduce and review

```sh
make proof-readability-check PEANO_DELIVERY_PYTHON=python3.10
make stage-proofs PEANO_DELIVERY_PYTHON=python3.10
python3.10 -B scripts/stage_proof_readability.py --check
python3.10 -B scripts/update_peano_worker_sources.py --check
bash scripts/update_peano_app_manifest.sh --check
PYTHONPATH=scripts:peano-lab/py python3.10 -B -m pytest -q \
  scripts/test_proof_readability_compiler.py
```

Use an installed Python 3.10 or newer. The final output is
`_deploy/proofs-readable-v1`; open `reading/index.html` for coverage, examples,
and the remaining exposition priorities. `reading/audit.json` contains per-page
provenance and notation receipts. `presentation/readability-v1.json` records
the accepted parent, control-source hashes and every changed/additional file.
A different mathematical release requires an explicitly reviewed new parent
binding, not a command-line hash override. Existing output is checked, never
silently overwritten.

Tests cover malformed and mismatched source pairs, exact byte recovery, stale
notes, conservative compaction, cyclic/missing definition edges, all authoring
adapters, proof reconstruction and branch scoping, independent certificate
checking, output tampering, no-clobber staging, permissions and deterministic
Node interaction/worker harnesses. The Node harness is not a real browser.

During the initial implementation, four focused groups passed 201, 123, 259
and 658 tests: **1,241 passed in total**. Six additional compiler tests failed at
toolchain discovery because the companion's pinned Lean 4.31.0 / Lake toolchain
was not installed. Those checks were not weakened, disabled, or counted as
passed. Worker inventory, app-manifest consistency, and `git diff --check`
also pass.

### Subsequent release validation — 2026-09-05

The missing compiler has now been installed from the official Darwin ARM64
Lean 4.31.0 archive, SHA-256
`264105500c8abdf37b68ffe03390a783ed259807807222698da8dd92d6ce0a27`.
The companion's generated import cache was refreshed from Lean 4.28.0 to
4.31.0 using the unchanged sources and bounded sequential compiler jobs.
The old cache remains recoverable locally. The source worktree and the
hash-pinned independent bundle-checker executable are unchanged.

All six previously unavailable full-strand compiler tests now pass. The new
compiler suite passes all 15 cases: seven native inferred applications, five
legacy-claim/scope cases, and the three explicitly dependency-relative large
library bodies above. Each tested declaration is checked for an empty axiom
dependency list. The actual compiler runs use the same import-free surface as
the production standalone exporter, with the existing 1,024 MiB and 90-second
limits; an initial over-heavy test harness importing all of Lean exhausted the
memory limit and was corrected, without raising any bound.

No browser connection is available, so browser-visual QA remains outstanding.
Automated interaction checks and exact file/HTTPS checks are not described as
visual verification. Mathematical proof artifacts and historical compiler
evidence remain unchanged. The separate deployment record confirms the
published website and preview; protected Peano production promotion remains
blocked by the missing hosting cache headers.
