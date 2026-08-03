# The strict-HA number-theory campaign

This campaign develops reusable number theory in the unchanged Peano Lab
object language

$$
0,\quad S,\quad +,\quad \times,\quad =
$$

with intuitionistic connectives, quantifiers, and formula-specific induction.
Readable names such as `Rem`, `IsGCD`, and the proposed signed predicates are
conservative notation: every occurrence expands before the ordinary kernel
checks a certificate.

The controlling machine manifest is
[`ha-number-theory-campaign.json`](https://github.com/nasqret/vietnam2026/blob/d5a734292b11e516a86606c65653be38d2faa7f1/research/arithmetic-library/ha-number-theory-campaign.json).
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
  - closed candidate
  - The representation is frozen. Twenty-six parity, decoder,
    code-extensionality, balance-normalization, and negation theorems close
    from the empty context without division.
```

The public registry therefore has 393 entries. The first nine campaign
theorems occupy append-only positions 384--392. The three gcd and twenty-six
signed candidates stay outside it. This tail append leaves the frozen
first-247 model curriculum unchanged.

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

```text
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

```text
flowchart TD
  P[K1-only parity separation] --> D[SignedDecode total and functional]
  D --> E[decoded-code extensionality]
  D --> B[SignedBalance totality]
  E --> X[SignedBalance extensionality and functionality]
  B --> X
  X --> N[signed negation]
  N --> A[signed addition]
  N --> M[signed multiplication]
  X --> Z[signed Bézout bridge]
  A --> Z
  M --> Z
```

The RFC freezes exact expansions for `SignedDecode`, `SignedValid`,
`SignedBalance`, `SignedNegate`, `SignedAdd`, `SignedMul`, `SignedNatScale`, and
`SignedBezout`. It also records a crucial dependency audit: the existing
`even_odd_exclusive_pointwise` theorem depends on division uniqueness, so it
cannot seed foundational K3 coding.

That prerequisite is now a closed candidate. Its mathematical statement is

$$
\forall n,a,b,\qquad
n=2a\longrightarrow n=2b+1\longrightarrow\bot.
$$

The proof is a direct induction on $n$. At zero, the odd decomposition would
identify zero with a successor. At $S n$, the odd equation peels to
$n=2b$. The even half is either zero, which is immediately impossible, or a
successor; peeling that equation produces $n=2a'+1$, contradicting the
induction hypothesis. The only named dependency is the elementary
zero-or-successor decomposition. In particular, the certificate does not
pass through quotient or remainder uniqueness.

The decoder itself is the expanded relation

$$
\operatorname{SignedDecode}(c,p,m)\;:\!\Longleftrightarrow\;
\bigl(c=2p\land m=0\bigr)
\lor
\exists h\,\bigl((c=2h+1\land p=0)\land m=S h\bigr).
$$

Seven isolated theorems now establish its two constructors, totality,
normality, functionality, exact zero characterization, and the fact that every
natural is a valid code. Functionality considers the four possible pairs of
decoder branches. The even/even and odd/odd cases use uniqueness of their half
witnesses; both mixed cases contradict the new elementary parity separation.

```{list-table}
:header-rows: 1
:widths: 46 10 10 10 24

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate SHA-256 prefix
* - `even_odd_exclusive_k1`
  - 80
  - 20
  - 1
  - `d2ebac65fdad`
* - `even_half_unique`
  - 245
  - 24
  - 7
  - `03df34e8e967`
* - `signed_decode_total`
  - 105
  - 20
  - 1
  - `6fb3f4a46760`
* - `signed_decode_functional`
  - 709
  - 27
  - 13
  - `50818b666470`
* - `signed_decode_zero_iff`
  - 53
  - 16
  - 1
  - `7a1f625296bb`
* - `signed_valid_all`
  - 112
  - 21
  - 2
  - `38b54ca5dfbe`
```

The two constructor certificates have only 5 and 8 nodes, and normality has
36. All nine parity/decoder candidates remain outside the public registry.

## Literal code equality and balanced values

Suppose codes \\(c_1,c_2\\) decode to natural pairs
\\((p_1,n_1),(p_2,n_2)\\). Their represented signed values are equal exactly when

$$
p_1+n_2=n_1+p_2.
$$

Three new candidates prove both constructive directions and package them as
`signed_code_eq_iff_balance`. This is the key extensionality fact: later
operation laws can conclude literal equality of canonical natural codes,
instead of introducing an untrusted quotient or a second equality relation.

```{list-table}
:header-rows: 1
:widths: 49 10 10 10 21

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate prefix
* - `signed_decoded_balance_implies_code_eq`
  - 276
  - 31
  - 8
  - `61adea012248`
* - `signed_code_eq_implies_decoded_balance`
  - 830
  - 28
  - 17
  - `8799714212e5`
* - `signed_code_eq_iff_balance`
  - 1,181
  - 32
  - 25
  - `26dbecbb46fe`
```

## Canonical normalization of balanced pairs

`SignedBalance(c,l,r)` says that \\(c\\) decodes to some normalized pair
\\((p,n)\\) and that

$$
l+n=r+p.
$$

The totality proof uses constructive trichotomy on \\(l\\) and \\(r\\). Equality
selects code \\(0\\); a positive excess on the right selects the appropriate odd
negative code; a positive excess on the left selects an even positive code.
The extensionality proof transports equality of two balanced equations to the
decoded cross sum and then invokes the literal-code theorem above.

```{list-table}
:header-rows: 1
:widths: 47 10 10 10 23

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate prefix
* - `signed_balance_total`
  - 236
  - 24
  - 4
  - `831fdaf085ae`
* - `signed_decode_to_balance`
  - 91
  - 13
  - 3
  - `3d663431a6c1`
* - `signed_balance_equations_cross_sum`
  - 410
  - 29
  - 8
  - `9124fbef806a`
* - `signed_balance_extensional`
  - 736
  - 33
  - 16
  - `ba68aa6e0e09`
* - `signed_balance_functional`
  - 850
  - 34
  - 18
  - `900fbfc0c813`
* - `signed_balance_zero_iff`
  - 1,660
  - 36
  - 33
  - `d54bade5be97`
```

These nine extensionality/normalization certificates, like the earlier nine
parity/decoder certificates, contain no `DNE` and reach no division,
remainder, CRT, or Gödel-β dependency. They remain nonpublic. The next
dependency-ordered milestone was signed negation, before addition or
multiplication.

## The first signed operation: negation

Negation is especially clean in the parity-interleaved representation. If
the input decodes to \((p,n)\), the output is the unique code decoding to
\((n,p)\):

$$
\operatorname{SignedNegate}(i,o)
\;:\!\Longleftrightarrow\;
\exists p,n,
\operatorname{SignedDecode}(i,p,n)
\land
\operatorname{SignedDecode}(o,n,p).
$$

No subtraction operation is involved. A constructive helper builds the
swapped decoder by cases on the normalized input; output functionality follows
from decoder functionality and the code-extensionality bridge. Symmetry is
obtained by swapping the witnesses again, and involution follows by symmetry
plus functionality.

```text
flowchart LR
  D[decoder totality] --> W[swapped decoder exists]
  W --> T[negation totality]
  F[decoder functionality] --> E[decoder/spec elimination]
  E --> U[negation functionality]
  C[decoded code extensionality] --> U
  S[negation symmetry] --> I[negation involution]
  U --> I
```

```{list-table}
:header-rows: 1
:widths: 45 10 10 10 25

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate prefix
* - `signed_decode_swap_exists`
  - 77
  - 21
  - 1
  - `77550f5f6828`
* - `signed_negate_of_swapped_decode`
  - 11
  - 10
  - 0
  - `e06c193ec50f`
* - `signed_negate_to_swapped_decode`
  - 774
  - 28
  - 14
  - `068786f8c357`
* - `signed_negate_total`
  - 219
  - 23
  - 5
  - `fe693a95bba9`
* - `signed_negate_functional`
  - 1,160
  - 33
  - 25
  - `43ba0ab36414`
* - `signed_negate_zero`
  - 19
  - 9
  - 0
  - `813a59731e04`
* - `signed_negate_symmetric`
  - 20
  - 13
  - 0
  - `f911ecaee17a`
* - `signed_negate_involutive`
  - 1,199
  - 35
  - 27
  - `7aec997db1ea`
```

The bounded semantic oracle checks, among other cases,

$$
0\mapsto0,\qquad 1\mapsto2,\qquad 2\mapsto1,\qquad
3\mapsto4,\qquad4\mapsto3,
$$

which are exactly \(0\mapsto0\), \(-1\mapsto+1\), \(+1\mapsto-1\),
\(-2\mapsto+2\), and \(+2\mapsto-2\). The oracle is a regression test; the
authority remains the empty-context certificate. All eight negation results
remain nonpublic. The next candidate graph is `SignedAdd`, built from decoded
natural contribution sums and `SignedBalance` normalization.

Read the complete
[`signed-natural RFC`](https://github.com/nasqret/vietnam2026/blob/d5a734292b11e516a86606c65653be38d2faa7f1/research/arithmetic-library/ha-canonical-signed-natural-rfc-v1.md)
for the exact formulas, hashes, forbidden dependency paths, and staged proof
obligations.

## Reproducing the boundary

From the repository root:

```bash
make ha-number-theory-check
python3 scripts/verify_arithmetic_knowledge_base.py
python3 scripts/build_peano_library_snapshot.py --check
```

The first command checks the 12-layer campaign manifest, all 38 theorem
receipts, the 44-theorem definition API, the nine public admissions, the three
isolated gcd candidates, and the twenty-six isolated signed representation,
normalization, and negation candidates. The second cross-checks all 393 public runtime
theorems against the 394-row research catalog. The third independently replays
the full public ladder and compares the deterministic snapshot.
