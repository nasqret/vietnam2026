# The strict-HA number-theory campaign

This campaign develops reusable number theory in the unchanged Peano Lab
object language

$$
0,quad S,quad +,quad \times,quad =
$$

with intuitionistic connectives, quantifiers, and formula-specific induction.
Readable names such as `Rem`, `IsGCD`, and the proposed signed predicates are
conservative notation: every occurrence expands before the ordinary kernel
checks a certificate.

The controlling machine manifest is
[`ha-number-theory-campaign.json`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-number-theory-campaign.json).
It separates three facts which are easy to blur in an informal development:

- a dependency-curried tactic body may check;
- its complete empty-context certificate may check while it remains isolated;
- only an explicit registry change makes it a public theorem.

## Current boundary

```{list-table}
:header-rows: 1
:widths: 26 18 56

* - Layer
  - Status
  - Result
* - Canonical remainder
  - public
  - Existence, functionality, the zero-modulus boundary, and unique existence.
* - Canonical congruence
  - public
  - Equality of supplied canonical remainders is equivalent to balanced
    congruence.
* - Bounded modular inverse
  - public
  - Existence from coprimality, the converse, bounded uniqueness, and the exact
    iff-with-unique-witness package.
* - Canonical relational gcd
  - closed candidate
  - Existence, functionality, and unique existence check from the empty
    context but are not in the public registry.
* - Canonical signed naturals
  - representation frozen
  - The code and eight expanded graph predicates are selected; their theorem
    DAG has not yet been claimed proved.
```

The public registry therefore has 393 entries. The first nine campaign
theorems occupy append-only positions 384--392. The three gcd candidates stay
outside it. This tail append leaves the frozen first-247 model curriculum
unchanged.

## Why canonical remainder is a relation

For naturals (m,n,r), write

$$
\operatorname{Rem}(m,n,r)
\;:\!\Longleftrightarrow\;
\bigl(\exists q,\ n=mq+r\bigr)\land r<m.
$$

Neither division nor remainder is added as a term former. Totality therefore
has the honest boundary premise (m\ne0):

$$
\forall m,n,\quad m\ne0\to\exists r,\operatorname{Rem}(m,n,r).
$$

Functionality requires no extra nonzero premise because an inhabitant of
`Rem(m,n,r)` already contains (r<m), which is impossible when (m=0).
Together the two results give a unique-existence interface. Follow the exact
expanded statements and tactic recipes in the theorem atlas:

- <a href="theorem-atlas.html#theorem-canonical_remainder_exists">canonical
  remainder existence</a>;
- <a href="theorem-atlas.html#theorem-canonical_remainder_functional">canonical
  remainder functionality</a>;
- <a href="theorem-atlas.html#theorem-canonical_remainder_zero_impossible">the
  modulus-zero boundary</a>;
- <a href="theorem-atlas.html#theorem-canonical_remainder_exists_unique">unique
  canonical remainder</a>.

The bridge theorem then states, for supplied canonical remainders (r,s),

$$
a\equiv b\pmod m\quad\Longleftrightarrow\quad r=s.
$$

Here congruence is still the subtraction-free balanced relation

$$
\exists u,v,\quad a+mu=b+mv.
$$

See <a href="theorem-atlas.html#theorem-canonical_remainders_characterize_mod_eq">the
exact bridge</a>.

## The modular-inverse package

For (m\ne0), the public endpoint has the familiar mathematical reading

$$
\operatorname{Coprime}(a,m)
\quad\Longleftrightarrow\quad
\exists!u<m,\ au\equiv1\pmod m.
$$

Its formal proof is deliberately split into reusable directions:

```{mermaid}
flowchart LR
  R[canonical remainder exists] --> E[coprime gives bounded inverse]
  U[bounded inverses are unique] --> P[unique bounded inverse package]
  E --> P
  C[any inverse implies coprime] --> P
```

The full endpoint has 9,512 structural proof occurrences, depth 70, 2,538
distinct proof objects, and 126 self-contained `Cut` nodes. Its certificate
DAG SHA-256 is
`c3ed07e7caef52895001332d066ae9e4ce25167c7a0cd7189f8957c9aa7dc9f3`.
These are reproducibility receipts, not sources of logical authority.

## The next closed layer: canonical gcd

`IsGCD(g,a,b)` remains a relation. The new candidate package merely gives it
the conventional value interface:

$$
\forall a,b,\ \exists g,\operatorname{IsGCD}(g,a,b),
$$

$$
\operatorname{IsGCD}(g,a,b)\land\operatorname{IsGCD}(h,a,b)
\to g=h,
$$

and their unique-existence packaging. All three certificates check from the
empty context without double-negation elimination, but deliberate public
admission is a later gate.

```{list-table}
:header-rows: 1
:widths: 42 12 12 12 22

* - Candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate SHA-256 prefix
* - `canonical_gcd_exists`
  - 1,280
  - 47
  - 36
  - `8e3b24c93772`
* - `canonical_gcd_functional`
  - 708
  - 35
  - 20
  - `7cca97c44c84`
* - `canonical_gcd_exists_unique`
  - 2,010
  - 48
  - 55
  - `20db8565558e`
```

## Signed naturals without negative zero

The selected `HA-K3-SIGNED-1` representation interleaves signs by parity:

$$
\operatorname{enc}(p)=2p,
\qquad
\operatorname{enc}(-(k+1))=2k+1.
$$

Thus (0,1,2,3,4) represent (0,-1,+1,-2,+2). Every natural is a valid
code, zero has one code, and the construction is independent of division,
CRT, Gödel-β coding, and the future pair/list codec.

```{mermaid}
flowchart TD
  P[K1-only parity separation] --> D[SignedDecode total and functional]
  D --> N[natural coercion and negation]
  D --> B[balanced-witness normalization]
  N --> A[signed addition]
  N --> M[signed multiplication]
  B --> Z[signed Bézout bridge]
  A --> Z
  M --> Z
```

The RFC freezes exact expansions for `SignedDecode`, `SignedValid`,
`SignedBalance`, `SignedNegate`, `SignedAdd`, `SignedMul`, `SignedNatScale`, and
`SignedBezout`. It also records a crucial dependency audit: the existing
`even_odd_exclusive_pointwise` theorem depends on division uniqueness, so it
cannot seed foundational K3 coding. The next proof must instead be a K1-only
parity-separation lemma.

Read the complete
[`signed-natural RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-canonical-signed-natural-rfc-v1.md)
for the exact formulas, hashes, forbidden dependency paths, and staged proof
obligations.

## Reproducing the boundary

From the repository root:

```bash
make ha-number-theory-check
python3 scripts/verify_arithmetic_knowledge_base.py
python3 scripts/build_peano_library_snapshot.py --check
```

The first command checks the 12-layer campaign manifest, all twelve theorem
receipts, the 44-theorem definition API, the nine public admissions, and the
three isolated gcd candidates. The second cross-checks all 393 public runtime
theorems against the 394-row research catalog. The third independently replays
the full public ladder and compares the deterministic snapshot.
