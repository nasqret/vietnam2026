# G009: constructive multiplicative closure of Dirichlet convolution

Date: 2026-08-30.
Parent: Alpha v31, 3,796 checked-use entries; Stable remains 432.
Scope: 90 genuinely new statements in the unchanged first-order HA language.

This document specifies the final missing multiplicative-closure part of the
G009 contract in PLAN/14. The existing admitted convolution, associativity,
delta identity, and general signed inverse criterion are prerequisites, not
new results counted again. The present proof data does not alter an earlier
Alpha catalogue, any first-admission record, or the Stable library.

## Precise representation

An arithmetic function is represented by an actual finite beta-coded signed
table. Signed zero, positive one, and negative one are respectively natural
codes 0, 2, and 1. Multiplication of signed values is the existing relational
graph SignedMul; multiplying their natural codes is not an implementation.

The conservative abbreviation MultiplicativePrefix(N,F) expands to:

1. N is nonzero.
2. F is an actual ArithTable through the inclusive index N.
3. ArithAt(F,1,2).
4. For every positive a,b with a*b <= N and Coprime(a,b), actual lookups
   F(a)=x, F(b)=y, and F(a*b)=z satisfy SignedMul(x,y,z).

Neither F(0) nor any value outside the prefix is constrained. The product
bound cannot be replaced by the two separate bounds a<=N and b<=N. The
normalization is positive one, not either signed unit. In particular, the
new two-argument graph is not silently aliased to the blueprint's untyped
one-argument planning label Multiplicative(f).

The central exact statements, with only conservative abbreviations, are:

~~~text
forall N F G H.
  MultiplicativePrefix(N,F) ->
  MultiplicativePrefix(N,G) ->
  DirichletTable(N,F,G,H) ->
  MultiplicativePrefix(N,H)

forall N F G.
  MultiplicativePrefix(N,F) ->
  MultiplicativePrefix(N,G) ->
  exists H.
    DirichletTable(N,F,G,H) /\
    MultiplicativePrefix(N,H) /\
    (forall K. DirichletTable(N,F,G,K) -> ArithPositiveEqual(H,K,N))
~~~

The value-level theorem proves the actual SignedMul relation between the
three witnessed convolution sums at m, n, and m*n, under positivity,
coprimality and m*n<=N. No sum identity or multiplicativity conclusion is
hidden among its hypotheses.

## Proof architecture

~~~mermaid
flowchart BT
  old[Admitted gcd, actual beta tables, signed arithmetic, finite Fubini]
  pair[Unique positive divisor pairs for coprime inputs]
  map[Constructed natural-beta map: i=(n+1)d+e maps to d*e]
  cart[Constructed Cartesian signed table and product-of-sums]
  support[Unequal-window nonzero-support reindexing via incidence/Fubini]
  factor[Four-factor interchange and actual convolution summand factorization]
  grid[Construct actual data; prove preservation, injectivity and coverage]
  values[Convolution values multiply at coprime m,n]
  final[Construct a normalized multiplicative convolution table; positive uniqueness]
  old --> pair
  old --> map
  old --> cart
  old --> support
  pair --> factor
  old --> factor
  pair --> grid
  map --> grid
  cart --> grid
  factor --> grid
  grid --> values
  support --> values
  cart --> values
  values --> final
~~~

This diagram is a mathematical summary. The reader's proof arrows come from
the actual ordered theorem dependencies. Definition-expansion and
theorem-uses-definition arrows remain separate and do not grant proof use.

### Layer A: normalized tables and divisor coordinates

Eleven multiplicativity lemmas give the exact projections, introduction,
nonempty-domain obstruction, value at one, restriction, actual product
witnesses, and positive extensionality.

Eight gcd/divisor lemmas construct and uniquely identify the positive
factorization k=d*e with d|m and e|n when k|m*n and m,n are coprime.
Their cofactor theorem supplies actual m=d*u, n=e*v and exactly the four
cross-input coprimality facts. It does not assert false within-input
coprimality such as Coprime(d,u).

Four native-beta lemmas construct the row-product index map, extend its
prefix, and establish lookup/value uniqueness. This is a natural-index
map, not a signed-table encoding.

### Layer B: actual finite sums

Seven block-sum lemmas prove concatenation and row-major flattening,
including empty rows or columns.

Twenty Cartesian-product lemmas construct an actual product table, decode
its bounded row-major coordinates, prove scalar row identities and the
full product-of-sums identity, and establish represented-value
extensionality. No input or output table is an oracle.

Twenty-five support-reindexing lemmas construct a genuine incidence table
and prove row and column folds. The resulting theorem equates two actual
signed sums over possibly unequal windows when the nonzero supports are
value-preservingly bijective. Zero entries may collide or map outside the
target window; no whole-window permutation is claimed.

### Layer C: convolution closure

Five entry lemmas prove signed four-factor interchange, nonzero-factor and
nonzero-divisor support, and actual summand factorization.

Six grid lemmas construct a Cartesian summand table and beta map from the
three actual input/output masks. They establish preservation, injectivity
on nonzero entries, and coverage of every nonzero output entry. The source
window has (m+1)(n+1) entries, while the target has m*n+1 entries.

Four final theorems prove the scalar product law, normalized convolution
table closure, actual existence with positive uniqueness, and the
corollary that a normalized multiplicative prefix has a two-sided
Dirichlet inverse with any prescribed zeroth value.

The last corollary uses the already admitted signed-unit inverse theorem.
It does not assert that the constructed inverse is multiplicative. That
stronger additional theorem is not required by the original G009
convolution-closure contract and is not claimed here.

## Exact inventory and evidence

The ordered module counts are 11+8+4+7+20+25+5+6+4 = 90. The exact
specification digest is:

25086b5c317b7dddd47cc06b0d9ad5639b6a5d88b6ede323cf7aa1124fa9dba7.

The full dependency cone contains 461 theorem rows: 371 already inherited
from Alpha v31 and 90 new rows. The unchanged v30-era assembler receives an
explicit compatibility frontier of 131 already-admitted v31 ancestors plus
the 90 new statements. Those 131 ancestors are never counted as new
theorems. All 39 inherited provider artifacts are authenticated as data;
the original kernel still checks every body retained in the final result.

The final acceptance command requires the entire exact ninety-row
inventory, an original-HA check of the complete dependency-closed bundle,
independently compiled Lean verification of the identical bytes, six
separately bounded ordinary empty-context principal certificates, and exact
statement-AST novelty against all 3,796 parent rows and the other new rows.
Saved receipts, partial authoring prefixes, and seed-only authoring options
cannot substitute for that gate.

Each worker retains the existing CPU limits 170/175 seconds, wall budget
180 seconds, observed RSS ceiling 1,536 MiB, and the existing proof-bundle
and ordinary-certificate limits. No kernel, axiom, signature, or resource
limit is enlarged by this campaign.

The complete authoring bundle has passed the original HA kernel with all
90 new bodies and all 371 inherited prerequisites. Including its single
packaging root, the bundle has 462 nodes, 1,371 edges and 35,945 proof-body
node occurrences. Its 7,840,579 bytes have SHA-256
953dc5ef340379b1e34883c2f9ab2181e91c872f5bbb7943c52b2fb70ce76959.
The exact ninety-versus-3,796 statement-novelty and adapter checks have
also passed. These authoring results are not admission or publication
authority: a verified reader still requires a fresh complete-bundle HA
check, independent Lean verification, all six ordinary certificates, and
its mandatory same-run presentation tests. Contract, hygiene, actual-beta
model, dependency-mutation and false-conclusion tests are separate
regressions; none can replace those final checks.

## Publication and admission boundary

The single new proof family is multiplicative-convolution, with stable
theorem tags MX0001 through MX005A (the established hexadecimal slots). Its exact and definition-aware pages
reuse the established Quadratic Reciprocity assets and page structure.
Eleven additive reviewed graphs occupy ND0316–ND0326; all 372 prior
definition identities are retained unchanged.

Current Alpha membership and local research verification are distinct.
Until a separate genuine additive admission, the 90 rows remain
non-admitted research proofs even after complete verification. The reader
must expose that distinction and preserve the historical Alpha v31
catalogue and its 63 published family snapshots.
