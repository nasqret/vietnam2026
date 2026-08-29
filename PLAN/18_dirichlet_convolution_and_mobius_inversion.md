# Actual Dirichlet convolution toward Möbius inversion

Date: 2026-08-29. Immutable starting commit:
`cef66ddf52658ee9f878b9a81ff8eca19f991485`.

The current request is to proceed with the next mathematical layer. Work is
local implementation and verification: no new deployment, Alpha/Stable
promotion, history rewrite, service change, or increased proof limit.
The 125 preceding results and their 395-file local explorer remain frozen.
All 3,643 prior statements (3,222 Alpha + 170 public + 126 public + 125 local)
are authenticated support, not new results or assumed mathematical oracles.

## Exact construction boundary

For actual signed tables F and G, a convolution summand at a positive divisor
d uses a real quotient witness `n=d*q`, actual lookups `F(d)=a`, `G(q)=b`,
and the existing signed multiplication graph `SignedMul(a,b,z)`. Zero and
nondivisors contribute canonical zero. A real signed table of these summands
is constructed, followed by its actual signed prefix sum of length `S n`.
The scalar convolution excludes `n=0`.

`Convolution(N,F,G,H)` requires genuine input/output tables and the actual
convolution value at every `0<n<=N`. Values at zero remain unrestricted;
output uniqueness is positive-prefix equality, never equality of table codes
or of arbitrary component representatives. `N=0` still requires actual table
witnesses and has a vacuous positive-value conclusion.

## Ordered proof layers

1. **Finite support and construction.** Prove actual signed zero-tail and
   padding lemmas. Construct convolution summands, finite summand tables,
   scalar sums and complete positive-prefix output tables, with actual
   totality, unique represented values and positive-domain transport.
2. **Reindexing and units.** Use the already constructed divisor-complement
   permutation to prove convolution commutativity. Construct actual one and
   delta tables; prove the delta identity and the divisor-sum specialization.
3. **Finite associativity.** Construct a genuine square grid on first/last
   factors with witnessed `n=(a*e)*c` and signed value
   `F(a)*(H(e)*G(c))`, zero off its positive divisor domain. Prove its row and
   column identifications, including zero tails beyond the positive quotient.
   Apply the existing actual finite Fubini theorem and commutativity to prove
   convolution associativity. No grid or rearrangement law is an input oracle.
4. **Möbius inversion.** Use the already proved Möbius divisor cancellation,
   actual one/delta tables and convolution laws. Apply the transform hypothesis
   at every required positive quotient. Only after proving the identity may
   the final output table be chosen as `H=F`.
5. **Evidence and readers.** Close every complete dependency cone, check it
   with original HA and the unchanged independently compiled Lean checker,
   and separately check ordinary principal certificates. Extend conservative
   definition DAGs and canonical Quadratic Reciprocity-style local explorers.
   Keep all three inherited research generations and Alpha authority distinct.

G007's full quantified statement is closed only after layer 4 has an actual
complete certificate. G009 is broader: arbitrary convolution units require
the exact signed `f(1)=+1 or f(1)=-1` inverse criterion, and the campaign prose
also requests multiplicative-function closure. Neither commutativity nor
Möbius inversion alone closes all of G009. General prime-power fields G091
remain a separate open campaign.

## Verification policy

Every new statement must be exactly AST-distinct from all 3,643 prior rows
and from every other new row. Each declared prerequisite must occur in the
actual proof; inherited bodies are included and freshly checked. Negative
tests mutate conclusions, dependencies, domains, representations and exact
proof metadata rather than supplying mocked positive verification.

Definitions are hygienic conservative abbreviations over the unchanged HA
signature. Preserve all 356 existing identities and graph records; new stable
IDs begin after ND0299. Actual expansion edges, theorem-definition uses and
proof dependencies remain three separate kinds; proof paths use only the last.

Authoring and verification windows retain 170/175 CPU seconds, 180 wall
seconds and 1,536 MiB observed RSS. Use separate bounded workers where the
aggregate campaign exceeds one window. No kernel, syntax, replay, catalog,
checker or service limit is relaxed. Alpha remains v30 (3,222 entries) and
Stable remains 432. The constructive-proof-explorer skill controls the page
topology, exact evidence, unchanged assets and regression gates.

## Implemented tranche

Seven mathematical modules now provide 113 new statements, 354 actual direct
prerequisite edges and 5,595 tactic commands. The five complete proof-data
families are:

| Family | New statements | Complete bundle nodes, including packaging |
| --- | ---: | ---: |
| Signed finite support | 8 | 170 |
| Convolution construction and commutativity | 40 | 270 |
| Constructed grids, Fubini and associativity | 32 | 347 |
| Constant-one, delta and divisor-transform identities | 25 | 282 |
| Forward and reverse Möbius inversion | 8 | 531 |

Thirteen new conservative definitions, ND0300–ND0312, extend the unchanged
356-definition registry to 369 definitions and 784 actual expansion edges.
The maximum zero-based definition layer remains 12. In particular, a grid's
construction through flattened prefixes is a proof dependency, not an
invented edge in its defining formula.

The final audit is deliberately scheduled as 21 fresh jobs: one whole-tranche
exact-AST novelty comparison, five complete original-HA/same-byte compiled-Lean
checks, and fifteen separate ordinary principal certificates. Each job keeps
the original proof limits. A three-root Fubini aggregate exceeded one CPU
window; the individual certificates fit. The proof-audit controller's derived
scheduling deadline is `21*185+180 = 4065` seconds, not a larger proof-checking
window.

The local explorer has five original Quadratic Reciprocity-style branches,
with stable ZS/DC/DF/DU/MI tags, a common campaign dispatch, exact and defined
readers, and separate theorem/definition edge kinds. A single live audit
supplies both the rendered pages and the machine-readable audit; stored
success sidecars are never verification inputs.

The first integrated run passed all 21 actual proof jobs, then its combined
controller exhausted the unchanged CPU budget while recomputing presentation
metadata. It produced neither a final audit nor an explorer snapshot. The
corrected build retains the live, already selected support plans (syntax, not
proof receipts) and runs rendering and UI tests in a separate forked process.
That child inherits only the current live evidence, accepts no receipt-file
input, and keeps 170/175 CPU seconds, 180 wall seconds and 1,536 MiB RSS. The
parent's derived scheduling deadline adds one 185-second render/cleanup window:
`4065+185 = 4250` seconds. Its CPU/RSS ceilings are unchanged. Clean child exit,
nonce/source binding and exact output hashes precede any final audit write.

## Completed outcome

All five implementation layers are complete. The corrected combined run
passed all 21 fresh proof jobs, all 85 same-live-snapshot explorer tests, and
the final parent source/integrity gates before writing the audit. All 113
new theorem bodies passed original HA and the unchanged compiled Lean
checker; all fifteen principal roots have actual ordinary empty-context
certificates. The complete finite signed G007 theorem and its converse are
proved locally. G009 and general G091 remain open.

The original Quadratic Reciprocity-style snapshot has 424 files and 378 HTML
pages. A total of 2,778 distinct focused tests passed across the bounded
windows. No per-worker proof or resource limit, historical catalog, shared
renderer, previous proof snapshot or remote state was changed.

See the [verification record](../research/arithmetic-library/dirichlet-verification-receipt-2026-08-29.md)
for exact statements, all fifteen certificate counts, literal output hashes,
resource measurements, the browser-availability limitation and the concrete
next G009 proof sequence. The [local map](../book/_static/constructive-dirichlet-explorer/index.html)
connects the five chapters and all three preceding research generations.
The work remains uncommitted, unpromoted and undeployed. No original RFC was
retrospectively rewritten to disguise its conditional authoring evidence as
a complete proof receipt.
