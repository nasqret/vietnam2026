# Bottom-layer implementation tranche after Alpha v30

Date: 2026-08-28. Initially completed as local mathematical development;
the separately authorized publication follow-up below does not admit any
theorem to Alpha or Stable and does not deploy Peano production.

Completed mathematical checkpoint: **170 new theorems**, in eleven additive
modules, with four complete original-HA bundles independently accepted by the
compiled Lean checker. Seven principal roots also have rechecked ordinary
empty-context HA certificates. The integrated record is
[`bottom-layer-checkpoints-v2.json`](../research/arithmetic-library/artifacts/bottom-layer-checkpoints-v2.json);
the readable report is
[`bottom-layer-checkpoints-v2.md`](../research/arithmetic-library/bottom-layer-checkpoints-v2.md).

## Immutable starting point

The five previous dispatch goals are complete: G072 (best approximation),
G006 (totient products), G010 (squarefree kernels and power profiles), G036
(odd-prime LTE), and G082 (Gaussian unique factorization). Their complete HA
bundles and independent Lean checks are recorded in the v29 and v30 receipts.
The v30 catalogue has 3,222 checked entries and SHA-256
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
Default Stable is unchanged at 432 entries.

Work is isolated on `proof/lower-foundations-v31-20260828`, based on the
published release commit `18ce79d3137616687183d17fcaed0a2c1383fecf`.
Existing frozen mathematical sources, catalogues, definitions, and public
snapshots are not edited. Unrelated Hydra work remains in its original tree.

## Current bottom frontier and implementation order

The first open goal by actual campaign layer is **G091, layer 6**. Its graph
prerequisites are available, but they do not include polynomial division,
polynomial gcd, irreducibles of every positive degree, or extension-field
tables. In particular, T12 proves natural beta-coded Horner evaluation; it
does not already supply arbitrary finite-field polynomial arithmetic.

The current graph has eighteen open goals with checked displayed direct
prerequisites. This is a dispatch hint, not proof of their missing internal
lemmas. We first build the following concrete foundational parts in parallel:

| Track | Exact target | Current stage | Required completion evidence |
| --- | --- | --- | --- |
| G091 substrate | Canonical prime-field operations and actual finite arithmetic tables for every prime, including 2 | 87 theorems checked locally | Actual tables, twenty field laws, a p-element bijection and characteristic p; full HA and Lean checks |
| G014 | Euler's theorem for every explicitly invertible residue, using the actual independently defined totient | Full endpoint checked locally, 32 theorems | Complete HA closure and independent Lean acceptance; actual power and congruence witnesses |
| G007 foundations | Möbius values, fresh-prime negation, actual signed tables and permutation-invariant sums | 51 theorems checked locally | Separate complete 21-row and 30-row HA/Lean bundles; cancellation and inversion are still open |

The full G091 statement, for every prime power `p^k` with `k>0`, remains open
until the polynomial and extension-field construction is actually proved.
The characteristic-prime case `k=1` is useful infrastructure, not a substitute
for that quantified endpoint or its irreducible-polynomial witness. G093 also remains open: a prime-field kernel
alone does not provide inseparability-aware squarefree decomposition.

An exhaustive parsed-AST audit against all 3,222 parent statements removed
two initially duplicated Euler lemmas. Their consumers now directly reuse
`binary_modulus_nontrivial_nonzero` and `mul_shuffle_four`. The current
170 statements are pairwise distinct and are not exact parent clones.
The original v1 sources and certificates remain archived; the active Euler
bundle and integrated audit are v2. Surviving local theorem tags, including
the G014 endpoint EU0022, are unchanged.

## Proof decomposition

1. **Prime fields.** Construct the unique residue `r<p` congruent to each
   natural input. Define addition and multiplication by their actual residue
   graphs, additive negation by addition to zero, and multiplicative inverse
   only for nonzero residues. Prove the laws from congruence and bounded
   uniqueness. Build real beta-coded binary and unary tables, with bounds,
   row-major lookup, and the explicit harmless table convention `inv(0)=0`.
   That convention is never asserted to be an inverse of zero.
2. **Euler.** Define the weighted residue list whose entry is `i` for a unit
   and `1` otherwise. Construct multiplication-by-a-unit as a genuine bounded
   permutation. Prove product invariance, identify the exponent by induction
   over the actual totient count, and cancel the coprime product. The exact
   G014 endpoint retains `m>1`; any broader `m=1` lemma must respect
   `Phi(1,1)` and distinguish congruence from canonical remainder equality.
3. **Möbius.** Define the canonical signed value by actual square divisibility
   and the parity of a genuine prime factor list. Prove representation
   independence, the unit case, prime adjunction, and divisor-sum cancellation.
   Establish signed finite-sum transport and double-sum reindexing before
   deriving inversion. Every divisor is positive, every quotient is witnessed,
   and the input divisor-sum identity is available at every `0<m<=N`.

All existence claims need ordinary HA proof objects. Finite Python examples
are independent diagnostics, not mathematical authority. Dependency-curried
body checks are followed by complete dependency-closed bundle checking;
an unproved prerequisite never becomes an accepted theorem.

## Conservative definition and proof DAGs

All 284 existing reviewed definition identities are retained literally.
There are 34 new definitions, ND0228–ND0261: **318 total reviewed definitions,
645 genuine expansion edges, maximum definition layer 12**. Three exact
historical graphs are reused instead of cloned: ND0023 canonical modular
residue, ND0141 identity enumeration, and ND0058 four-parameter packing.
New IDs were allocated only after the actual public builders were fixed.
The new definitions must retain the strict first-order HA signature and pass
exact parsed-AST equality, compound-term, large-numeral, and binder-capture
tests. Table validity describes actual encoded data; it must not assume the
theorem that will later be proved about that data.

The three edge types stay separate:

- Actual proof premises determine theorem reachability and proof layers.
- Theorem-to-definition edges describe notation used by a statement.
- Definition-to-definition edges describe genuine conservative expansion.

Prime-field residue graphs precede operations, operations precede table graphs,
and table laws are proved separately. Unit-product/count and signed-divisor-sum
graphs similarly precede their mathematical endpoints. Reused concepts are not
renamed merely to manufacture new definitions or apparent theorem counts.

## Verification and publication boundary

Keep every existing kernel, proof, formula, bundle, CPU, and memory guard.
Use fresh bounded processes for substantial proof work; no monolithic test
process is required merely to obtain an aggregate count. Complete bundles
must pass the original checker and the independently compiled Lean verifier.
Negative tests must reject poisoned conclusions, missing prerequisites,
malformed encodings, and counterfeit source or proof receipts.

The current compact v30 catalogue is 66,503,303 bytes, only 605,561 bytes
below the unchanged 64 MiB publication/service ceiling. New mathematical
certificates can be constructed and checked independently of admission.
This tranche does not increase that ceiling, discard evidence to fit it, or
silently claim that future Alpha packaging has already passed its gates.

Any local proof explorer must keep the established Quadratic Reciprocity
renderer and clearly distinguish independently checked local proof data from
current Alpha membership. Published v30 artifacts and their original admission
records remain unchanged. Commits, pushes, remote deployment, and Peano cache
work were not part of the original implementation-only request. The subsequent
"Commit and deploy" request authorizes the separate proof-site publication
described below, not a change to admission or production-cache gates.

The new local preview is
[`constructive-bottom-layer-explorer`](../book/_static/constructive-bottom-layer-explorer/index.html).
The historical public renderer requires positive Alpha-admission flags, so a
narrow additive local renderer preserves its exact layout and byte-identical
assets while replacing only the authority text and validation. It never feeds
false admission flags into the public renderer. The historical atlas remains
unchanged; the local dispatch page distinguishes the newly checked G014 proof
from the still-open published milestone and links both directions locally.

Reproduce complete verification without changing any library membership:

```sh
PYTHONPATH=peano-lab/py:scripts PYTHONMALLOC=malloc python3 scripts/check_constructive_bottom_layers.py --check
```

That command checks actual proofs afresh, not cached success flags. Whole
ordered theorem specifications are pinned independently of imported Python
factories. The exact HA-checked bytes are passed to the pinned Lean binary in
a private temporary snapshot, and the audit sidecar is compared with a
bounded exact UTF-8 read. The original CPU, wall-time and memory ceilings are
retained; no current catalogue or service limit has been increased.

## Separately authorized commit and publication follow-up

The 170-theorem implementation, four checked bundles, archived Euler v1
sources and all 493 local explorer files are committed as `72f6a4ae`.
The four small proof-certificate copies are explicitly included despite the
general ignore rule for model-training checkpoints.

A separate public presentation at `/proofs/checkpoints/` keeps the canonical
Quadratic Reciprocity design and all original proof data. Its four chapters
are `euler-units`, `prime-fields`, `mobius-values`, and `signed-sums`. Public
navigation connects the checkpoint map to the unchanged Alpha campaign atlas;
an added staged-HTML notice prevents a local proof from impersonating Alpha
admission. The Alpha-only on-demand Lean controls are not enabled for these
new names. Literal independently verified bundles remain downloadable.

The durable build, staging and verification commands are documented in
[`docs/DEPLOY.md`](../docs/DEPLOY.md#public-research-checkpoints-without-alpha-promotion).
Remote deployment results belong in a separate release receipt, not in the
immutable mathematical checkpoint audit. Neither `/peano-lab/` nor
`/peano-lab-next/`, the existing Lean worker, or the unrelated Hydra worktree
is part of this publication.

Local packaging does include the twelve new Python modules in the existing
generated browser source inventory. The reproducible local app manifest is
`a-86993f944ca2`, with 483 browser Python files and 505 manifest entries.
This fixes the source-inventory integration checks without admitting the new
theorems or publishing either Peano application channel.

Publication completed and was checked live on 2026-08-28. The
[deployment receipt](../research/arithmetic-library/bottom-layer-publication-receipt-2026-08-28.md)
records the pushed source commits, complete staged-site checks, zero-difference
remote checksum comparison, and 617 exact HTTPS object comparisons. The
[checkpoint library](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/checkpoints/)
is live; Alpha and Stable remain unchanged.

## Next exact G007 sequence

1. **Masks and append:** construct actual Möbius-value tables and signed
   divisor masks by beta-prefix extension. Define `DivisorSum(F,n,z)` from
   the real `S n`-entry masked fold; prove totality and uniqueness for
   `0<n<=N`, not from an assumed finite-choice or sum oracle.
2. **Prime-toggle cancellation:** for prime `p|n`, construct the bounded map
   which fixes zero, nondivisors and p-square-divisible entries, multiplies
   the remaining p-free divisors by p, and otherwise supplies the quotient
   witness `d=p*e`. Prove its bounds, functionality and involution before
   using signed permutation invariance and fresh-prime negation. Handle
   `n=1` separately with signed positive-one code 2.
3. **Weighting and finite Fubini:** construct signed pointwise products,
   prove sum linearity, and build actual rectangular row/column slices.
   Prove finite double-sum interchange, including zero-sized rectangles.
   This can proceed in parallel with step 2 after step 1.
4. **Convolution:** define actual weighted divisor tables from positive
   witnesses `n=d*q`, then prove associativity, commutativity and the delta
   identity. Use equality only on `0<n<=N`: input values at zero are
   unrestricted, so `ArithTableEqual(F,G,S N)` would be too strong.
5. **Inversion:** apply the hypothesis at every required positive quotient
   `m<=N`. Derive the weighted identity from the proved convolution laws
   and cancellation; only then choose the final actual table `H=F`.
   For `N=0`, retain the genuine table witness and the vacuous positive
   conclusion. Neither cancellation nor inversion is yet a checked root.

## Follow-on work, not completed by this tranche

Prime-field polynomial coefficient operations, Euclidean division and gcd;
irreducible-polynomial construction and the full G091 endpoint; order and
unit-group structure after Euler; Jordan totients and convolution algebra
after the actual divisor-sum machinery. Eisenstein factorization, Jacobi
reciprocity, periodic quadratic continued fractions and zero-sum theorems
remain separate lower-frontier branches rather than implicit consequences.
