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
[`ha-number-theory-campaign.json`](https://github.com/nasqret/vietnam2026/blob/9b2feb66b5fcc2530394f5b6bcce5e63dfea627f/research/arithmetic-library/ha-number-theory-campaign.json).
It separates three facts which are easy to blur in an informal development:

- a dependency-curried tactic body may check;
- its complete empty-context certificate may check while it remains isolated;
- only an explicit promotion makes it a Stable theorem.

```{admonition} Current Alpha v2 / Stable status (2026-08-09)
:class: important
The tables and dated checkpoints below preserve the campaign's historical
`public`/`private` admission boundary. They are not the current library
membership ledger. The canonical Alpha edition now contains every reviewed row
from this campaign: its strict-HA contribution is 121 Alpha-closed rows, one of
which shares an exact QR specification and therefore occupies the earlier QR
position. These rows are Alpha checked-use facts, but they are not Stable. The
current additive Alpha v2 edition preserves the sealed 885-row Alpha v1 ledger
and appends seventeen K3C rows at indices 885--901. It now has 902 specs,
2,674 direct edges, 45 layers, 470 Alpha-only rows, and 570 checked-use rows;
Stable remains 432. The authoritative current counts and evidence states are
in {doc}`Alpha and Stable library editions <library-editions>` and
`artifacts/peano-library/channels-v2.json`.
```

## Historical Stable/public boundary

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
  - mixed
  - The relational gcd core is public. Three canonical packaging rows and five
    zero/one/swap convenience rows remain closed private candidates.
* - Universal-property lcm
  - seven public / ten private
  - The projections, leastness, symmetry, uniqueness, and both forced-zero
    constructors are public. The L08 divisibility constructor and nine
    convenience rows remain private.
* - Gcd--lcm totality and compatibility
  - public K4
  - All nine constructive bridge rows are public: compatible gcd/lcm
    existence, relational and unique lcm existence, and the product identity.
* - Canonical signed naturals
  - closed candidate
  - The representation is frozen. Seventy-four parity, decoder,
    code-extensionality, balance-normalization, negation, addition, and
    multiplication theorems, together with the direct natural-scaling graph,
    its laws, and the balanced-to-signed Bezout bridge, close from the empty
    context without division.
* - Signed coefficients for relational gcd
  - closed K4 candidate
  - A separate client returns a relational gcd together with two canonical
    signed Bezout codes. Its audited dependency path intentionally includes
    Euclidean division.
* - Canonical pair/cell coding
  - 15 closed private candidates
  - Doubled-Cantor constructors, doubled-triangular shell separation, and
    exact pair injectivity now close constructively. Cell functionality,
    descending projections, and uniform finite-data infrastructure remain open.
* - Generalized CRT
  - 23 public / 6 private
  - The public dependency closure proves the all-modulus criterion, classifies
    solutions modulo relational LCM, supplies the zero/nonzero canonical
    boundary, and returns either a solution or a certified obstruction from
    raw inputs. Six convenience rows retain closed private receipts.
```

The public registry now has **432** entries. The nine tranche-01 interfaces at
positions 384--392 are followed by the exact 16-row K4 admission at positions
393--408 and the exact 23-row M5 admission at positions 409--431. The research
catalog has **433** entries, including **409** `checked_m20` rows. The campaign
manifest records **95** public references, **99** isolated candidates, and
**147** exact theorem receipts across **22** candidate modules and **31**
focused test paths. Generalized CRT accounts for **29** audited rows: **23**
public interfaces and six closed private conveniences. This append-only
extension leaves the frozen first-247 model curriculum unchanged.

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
remain nonpublic.

## Canonical signed addition: the closed graph core

If the two inputs and output decode respectively as
((l_+,l_-)), ((r_+,r_-)), and ((o_+,o_-)), D05 defines addition by the
subtraction-free equation

$$
(l_+ + r_+) + o_- = (l_- + r_-) + o_+.
$$

This is exactly the integer identity

$$
(l_+-l_-)+(r_+-r_-)=o_+-o_-,
$$

but the checked statement never introduces subtraction or an integer term
type. Totality decodes both inputs and sends the two natural contribution sums
through `SignedBalance`; functionality reduces two outputs to the same
balance-normalization problem.

```text
flowchart LR
  DL[decode left] --> C[contribution sums]
  DR[decode right] --> C
  C --> B[SignedBalance totality]
  B --> T[SignedAdd totality]
  DF[decoder functionality] --> E[decoded equation elimination]
  E --> U[SignedAdd functionality]
  BF[SignedBalance functionality] --> U
```

```{list-table}
:header-rows: 1
:widths: 45 10 10 10 25

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate prefix
* - `signed_add_of_decoded_equation`
  - 26
  - 23
  - 0
  - `94c77cd7434e`
* - `signed_add_to_decoded_equation`
  - 823
  - 35
  - 14
  - `77bb73fbc741`
* - `signed_add_decoded_iff_equation`
  - 956
  - 39
  - 16
  - `376faba0f2bf`
* - `signed_add_total`
  - 411
  - 27
  - 8
  - `793ef15dc81c`
* - `signed_add_functional`
  - 1,754
  - 38
  - 34
  - `63eb78997ade`
```

The bounded semantic regression table starts with

```{list-table}
:header-rows: 1
:widths: 20 20 20 20

* - encoded sum
  - left value
  - right value
  - output value
* - `SignedAdd(1,1,3)`
  - $-1$
  - $-1$
  - $-2$
* - `SignedAdd(1,2,0)`
  - $-1$
  - $+1$
  - $0$
* - `SignedAdd(2,2,4)`
  - $+1$
  - $+1$
  - $+2$
```

Two cold replays agree on the complete 31-theorem signed-stack digest
`11f41d395be9597892e2d5577ff80b54d04a61a57c81e50d02bc335c7e6012da`.
The closure has no DNE, division, remainder, CRT, Gödel-β, or negation edge.
These five results remain nonpublic. They establish the total functional graph
and its decoded specification; zero identity, commutativity, associativity,
and addition of a value to its negation are the next separate theorem tranche.
Inspect the immutable
[`native tactic source`](https://github.com/nasqret/vietnam2026/blob/ce2f865389013ab2ad16cb2c351f735972330554/peano-lab/py/peano_lab/library/ha_signed_add_candidate.py#L85)
and its
[`cold-closure audit`](https://github.com/nasqret/vietnam2026/blob/ce2f865389013ab2ad16cb2c351f735972330554/peano-lab/py/tests/test_ha_signed_add_candidate.py#L456)
for every expanded statement, tactic line, mutation, and receipt.

### Elementary addition laws

The next five graph theorems close commutativity, both zero orientations, and
both orders of adding a code to its canonical negation:

$$
0+x=x,qquad x+0=x,qquad x+y=y+x,qquad
x+(-x)=0,qquad(-x)+x=0.
$$

Each displayed equality abbreviates an exact D05 graph statement whose
inputs and output are literal canonical natural codes. In particular, the
inverse results consume the exact D04 negation graph; they do not use host
subtraction or an integer evaluator.

```{list-table}
:header-rows: 1
:widths: 45 10 10 10 25

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate prefix
* - `signed_add_commutative`
  - 139
  - 38
  - 3
  - `047393b1f607`
* - `signed_add_zero_left`
  - 266
  - 25
  - 7
  - `9612c4bdec80`
* - `signed_add_zero_right`
  - 427
  - 40
  - 10
  - `a2cf2150e8f0`
* - `signed_add_negate_right_zero`
  - 145
  - 24
  - 4
  - `fef01c135149`
* - `signed_add_negate_left_zero`
  - 299
  - 40
  - 7
  - `c0644346209c`
```

The complete 36-theorem signed stack has deterministic digest
`a5fdad35078f386ccb42fd6e17f942f83f504aaaf748c40259b68a2798ab28c7`.
An independent audit verified that the private literal-zero expansions are
alpha-identical to D05 instantiated at the appropriate slot. The transitive
closure uses only four public arithmetic facts and five earlier/local signed
facts, with no division, remainder, CRT, Gödel-β, classical, or DNE edge.

At this checkpoint associativity remained deliberately separate because it
needed a reusable cross-sum composition lemma before graph reassociation.
Inspect the immutable
[`law tactic source`](https://github.com/nasqret/vietnam2026/blob/a1fa4162f92d4ce6c5501cebceadd75403d7a563/peano-lab/py/peano_lab/library/ha_signed_add_laws_candidate.py#L171)
and its
[`eight-gate audit`](https://github.com/nasqret/vietnam2026/blob/a1fa4162f92d4ce6c5501cebceadd75403d7a563/peano-lab/py/tests/test_ha_signed_add_laws_candidate.py#L472)
for every expanded graph, native tactic, semantic fixture, and receipt.

### Associativity through cross-sum composition

The final additive law is organized as a three-step proof rather than one
large graph manipulation:

```text
flowchart LR
  C[generic cross-sum chain] --> E[three decoded equations associate]
  D[D05 elimination aligns decoders] --> E
  E --> G[SignedAdd graph associativity]
  I[D05 introduction] --> G
```

The reusable arithmetic helper says

$$
a+x=b+y,\quad y+c=x+d\quad\Longrightarrow\quad a+c=b+d.
$$

It prefixes both target sums by the shared contribution and cancels it. The
second lemma applies this principle twice, with a proved four-summand shuffle,
to the decoded equations for $a+b$, $(a+b)+c$, and $b+c$. The graph
theorem aligns all decoder witnesses through the existing elimination bridge
and reconstructs exactly `SignedAdd(a,bc,abc)`.

```{list-table}
:header-rows: 1
:widths: 45 10 10 10 25

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate prefix
* - `add_cross_sum_chain`
  - 315
  - 29
  - 7
  - `dff8ac71df78`
* - `signed_add_equations_associate`
  - 703
  - 35
  - 13
  - `ac5629e6081d`
* - `signed_add_associative`
  - 1,695
  - 47
  - 30
  - `dbac676cc565`
```

The complete 39-theorem signed stack has deterministic digest
`39ac0f7083ed54d2762289c7417b57a21c6dc97971b57efe2649ecb1cb7ec895`.
The semantic regression gate exhausts `4^6` tuples for the generic helper,
`3^12` tuples for the equation associator, and all 4,913 triples of the first
17 canonical codes for graph associativity. Independent replay verifies the
exact witness map and finds no division, remainder, CRT, Gödel-β, classical,
or DNE edge.

This closes the RFC's totality, functionality, zero, commutativity, inverse,
and associativity obligations for SignedAdd at nonpublic candidate status.
The following sections carry the same discipline through the complete D06
elementary `SignedMul` algebra.
Inspect the immutable
[`associativity tactic source`](https://github.com/nasqret/vietnam2026/blob/883febe3fcf3b8a29707f34780c457f8fcd8edc6/peano-lab/py/peano_lab/library/ha_signed_add_associative_candidate.py#L16)
and its
[`exhaustive focused audit`](https://github.com/nasqret/vietnam2026/blob/883febe3fcf3b8a29707f34780c457f8fcd8edc6/peano-lab/py/tests/test_ha_signed_add_associative_candidate.py#L381)
for the full native proof and every receipt.

### The total functional SignedMul core

The D06 multiplication graph decodes the two inputs and output and checks the
subtraction-free equation

$$
(l_+r_+ + l_-r_-) + o_-
=
(l_+r_- + l_-r_+) + o_+.
$$

This is precisely

$$
(l_+-l_-)(r_+-r_-)=o_+-o_-
$$

written in the unchanged natural-only object language. The implementation
does not multiply parity codes as naturals and does not invoke an external
integer evaluator. Its proof ladder mirrors the addition core:

```{list-table}
:header-rows: 1
:widths: 45 10 10 10 25

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate prefix
* - `signed_mul_of_decoded_equation`
  - 26
  - 23
  - 0
  - `94c77cd7434e`
* - `signed_mul_to_decoded_equation`
  - 877
  - 39
  - 14
  - `d50b8c46989e`
* - `signed_mul_decoded_iff_equation`
  - 1,010
  - 41
  - 16
  - `14adcb23ed89`
* - `signed_mul_total`
  - 411
  - 27
  - 8
  - `85d12bb18f09`
* - `signed_mul_functional`
  - 1,808
  - 40
  - 34
  - `632bd740e1f6`
```

Totality sends the positive and negative product contributions through the
already proved `SignedBalance` normalizer. Functionality sends two possible
outputs to the same balance problem. The core therefore needs no
commutativity, associativity, or distributivity theorem.

Two cold replays agree on the complete 44-theorem signed-stack digest
`2230cd2b67196ccec58ab5259052b08f9ef3f43275ef0b717fc35cf581cd0f6c`.
The semantic gate checks the unique output for all 289 pairs of the first 17
codes, including

$$
(-1)(-1)=1,\qquad (-1)(1)=-1,\qquad (2)(-2)=-4.
$$

These five rows remain nonpublic. Zero, one, commutativity, associativity, and
distributivity are deliberately separate D06 law gates. Inspect the
[`candidate source`](https://github.com/nasqret/vietnam2026/blob/01fb459bc2ef797ca1e1e76b353c219dcc1eecb6/peano-lab/py/peano_lab/library/ha_signed_mul_candidate.py)
and
[`focused audit`](https://github.com/nasqret/vietnam2026/blob/01fb459bc2ef797ca1e1e76b353c219dcc1eecb6/peano-lab/py/tests/test_ha_signed_mul_candidate.py)
for the complete expanded formulas, tactic scripts, mutations, and receipts.

### Elementary SignedMul laws

Five additional candidates prove the first algebraic laws of the D06 graph:

```{list-table}
:header-rows: 1
:widths: 45 10 10 10 25

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate prefix
* - `signed_mul_commutative`
  - 376
  - 41
  - 8
  - `6bc3661f663b`
* - `signed_mul_zero_left`
  - 209
  - 25
  - 4
  - `78a9b2f876c7`
* - `signed_mul_zero_right`
  - 607
  - 43
  - 14
  - `30d11a080942`
* - `signed_mul_one_left`
  - 347
  - 25
  - 10
  - `8d1406a347d4`
* - `signed_mul_one_right`
  - 745
  - 43
  - 18
  - `fe3977029e00`
```

The multiplicative identity is code `2`, not code `1`:

$$
2\longmapsto (1,0)=+1,
\qquad
1\longmapsto (0,1)=-1.
$$

Thus the identity statements are graph facts

$$
\operatorname{SignedMul}(2,a,a),
\qquad
\operatorname{SignedMul}(a,2,a),
$$

while zero annihilates in both orientations. Commutativity swaps the two
decoded input pairs, commutes the four products, and reorders the two cross
terms. The left zero and unit proofs construct literal D01 decoders for codes
`0` and `2`; the right laws follow from graph commutativity. Every private
literal expansion is alpha-checked against D06, so this convenience introduces
no new object-language construct.

Two cold replays agree on the complete 49-theorem signed-stack digest
`be074dfe1b79e3f27b2d48851c64f58360ee86fc3776ae681c451d38f67d25b2`.
The semantic audit checks all five laws on every pair of the first 33 codes
and preserves the crucial representation test

$$
1\cdot 1=1\quad\hbox{as natural codes},
\qquad
(-1)(-1)=+1\quad\hbox{with signed output code }2.
$$

The dependency closure reaches no SignedAdd law, division, remainder, CRT,
Gödel-β, classical theorem, or DNE. These laws are still isolated candidates;
the next section closes associativity and distributivity without admitting
them. Inspect the immutable
[`law tactic source`](https://github.com/nasqret/vietnam2026/blob/37bd997ac9890be9f040b94e8e713f19246d9186/peano-lab/py/peano_lab/library/ha_signed_mul_laws_candidate.py)
and
[`focused audit`](https://github.com/nasqret/vietnam2026/blob/37bd997ac9890be9f040b94e8e713f19246d9186/peano-lab/py/tests/test_ha_signed_mul_laws_candidate.py)
for the full expanded formulas, tactic scripts, exact receipts, and rejected
mutations.

### SignedMul associativity and distributivity

The last D06 algebra tranche consists of four associativity candidates and
seven distributivity candidates. The endpoint statements preserve the exact
forward graph surfaces used by the native proofs. Associativity is

$$
\begin{aligned}
\forall a,b,c,\mathit{ab},\mathit{abc},\mathit{bc},\quad
&\operatorname{SignedMul}(a,b,\mathit{ab})
\to \operatorname{SignedMul}(\mathit{ab},c,\mathit{abc})\\
&\qquad\to \operatorname{SignedMul}(b,c,\mathit{bc})
\to \operatorname{SignedMul}(a,\mathit{bc},\mathit{abc}).
\end{aligned}
$$

Left distributivity is

$$
\begin{aligned}
\forall a,b,c,\mathit{bc},\mathit{ab},\mathit{ac},\mathit{out},\quad
&\operatorname{SignedAdd}(b,c,\mathit{bc})
\to \operatorname{SignedMul}(a,b,\mathit{ab})
\to \operatorname{SignedMul}(a,c,\mathit{ac})\\
&\qquad\to \operatorname{SignedMul}(a,\mathit{bc},\mathit{out})
\to \operatorname{SignedAdd}(\mathit{ab},\mathit{ac},\mathit{out}),
\end{aligned}
$$

and right distributivity is the separately exposed orientation

$$
\begin{aligned}
\forall a,b,c,\mathit{bc},\mathit{ba},\mathit{ca},\mathit{out},\quad
&\operatorname{SignedAdd}(b,c,\mathit{bc})
\to \operatorname{SignedMul}(b,a,\mathit{ba})
\to \operatorname{SignedMul}(c,a,\mathit{ca})\\
&\qquad\to \operatorname{SignedMul}(\mathit{bc},a,\mathit{out})
\to \operatorname{SignedAdd}(\mathit{ba},\mathit{ca},\mathit{out}).
\end{aligned}
$$

These are relational laws: every intermediate product and sum is supplied as
a graph witness. No hidden function application or host-integer operation is
introduced.

The associativity ladder first proves that a balanced decoded pair remains
balanced after multiplication on either side. It next proves the two raw
positive/negative component identities for reassociation. Those helpers feed
a decoded-equation associator, which is transported through the existing D06
elimination and introduction bridges to obtain the graph theorem.

The distributivity ladder reuses that two-sided transport instead of
duplicating it. A four-term shuffle, pairwise cross-sum composition, raw
component distribution, and balanced-output composition establish left
distribution at the decoded level. D05 and D06 bridges then recover the exact
left graph. The right graph uses three checked applications of
`signed_mul_commutative` followed by the left law, so there is only one large
decoded calculation.

```{list-table}
:header-rows: 1
:widths: 47 10 10 10 23

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate prefix
* - `signed_pair_mul_cross_transport`
  - 785
  - 26
  - 15
  - `1ff73d62de76`
* - `signed_pair_mul_components_associate`
  - 887
  - 26
  - 17
  - `35dd7e68185d`
* - `signed_mul_equations_associate`
  - 2,150
  - 33
  - 30
  - `159168d3c8ed`
* - `signed_mul_associative`
  - 3,196
  - 47
  - 47
  - `c6a9694ced9e`
* - `add_shuffle_middle`
  - 245
  - 17
  - 6
  - `4dd61bd9bfab`
* - `add_cross_sum_pairwise`
  - 272
  - 18
  - 7
  - `cb63dfdbd073`
* - `signed_mul_distributive_component`
  - 345
  - 19
  - 9
  - `c4f2ccd30f68`
* - `add_balance_outputs_compose`
  - 708
  - 32
  - 15
  - `9be646df81e7`
* - `signed_mul_left_cross_sum_distributes`
  - 1,172
  - 27
  - 21
  - `a40d2cd61a28`
* - `signed_mul_left_distributive`
  - 3,297
  - 58
  - 49
  - `c02d8258cce2`
* - `signed_mul_right_distributive`
  - 3,717
  - 60
  - 53
  - `63d17772d424`
```

The focused validation is deliberately redundant. Each dependency-curried
body and each empty-context certificate is checked; a conclusion-changing
mutation is rejected for every row and a concrete semantic fixture confirms
that each mutated claim is false. The natural helper sweeps include all
`3^12` assignments for the decoded associator, of which exactly 11,283
satisfy its premises, and all `2^14` assignments for the decoded
distributivity checkpoint, of which 496 satisfy its premises. The graph
oracles exhaust all `17^3=4,913`
triples for associativity and for both distributive orientations. Two
cache-cleared closure runs agree on every receipt and on the complete
60-row signed-stack digest
`7befb7ae830b866a606e47f674730959e76599ded863aadd9868b850bcb190cd`.

All eleven rows are constructive, dependency-curried, registry-isolated, and
closed from the empty context. Their transitive closure reaches neither DNE
nor classical reasoning, forbidden automation, division, remainder, CRT, or
Gödel-β coding. At this D06 checkpoint the campaign had 60 signed candidates,
63 candidates in total, and 72 theorem receipts. The public registry remained
at 393; the definition freeze and research catalog likewise remained at 45
API rows over 44 distinct public-theorem replays and 394 entries,
respectively. Nothing in this tranche is
publicly admitted; D07 natural scaling was the next signed-arithmetic gate.

Inspect the immutable
[`associativity tactic source`](https://github.com/nasqret/vietnam2026/blob/497d0fc3327e6fa2564aad8b44c4ce151e20269c/peano-lab/py/peano_lab/library/ha_signed_mul_associative_candidate.py#L22),
[`associativity audit`](https://github.com/nasqret/vietnam2026/blob/497d0fc3327e6fa2564aad8b44c4ce151e20269c/peano-lab/py/tests/test_ha_signed_mul_associative_candidate.py#L479),
[`distributivity tactic source`](https://github.com/nasqret/vietnam2026/blob/497d0fc3327e6fa2564aad8b44c4ce151e20269c/peano-lab/py/peano_lab/library/ha_signed_mul_distributive_candidate.py#L22),
and
[`distributivity audit`](https://github.com/nasqret/vietnam2026/blob/497d0fc3327e6fa2564aad8b44c4ce151e20269c/peano-lab/py/tests/test_ha_signed_mul_distributive_candidate.py#L563)
for the exact expanded statements, tactic scripts, dependency audits,
mutations, semantic oracles, and closed receipts.

### Direct natural scaling: D07

`SignedNatScale` multiplies a canonical signed code by an ordinary natural
without first encoding that natural as a signed value. If `input` decodes as
\((i_+,i_-)\) and `output` decodes as \((o_+,o_-)\), its exact defining
equation is

$$
s i_+ + o_- = s i_- + o_+.
$$

Equivalently, the frozen D07 graph is the following conservative expansion:

$$
\begin{aligned}
\operatorname{SignedNatScale}(s,i,o)\;:\!\Longleftrightarrow\;
\exists i_+,i_-,o_+,o_-,\quad
&\operatorname{SignedDecode}(i,i_+,i_-)\\
{}\land{}&\operatorname{SignedDecode}(o,o_+,o_-)\\
{}\land{}&s i_+ + o_- = s i_- + o_+.
\end{aligned}
$$

All three predicate occurrences expand before kernel checking. The first five
candidate rows prove introduction from the decoded equation, elimination back
to it, the exact iff package, totality, and literal-code functionality. The
second five supply the arithmetic transport and graph laws:

```text
signed_nat_scale_of/to_decoded_equation
  |--> totality / functionality
  |--> zero / one
  `--> signed_nat_scale_compose
            ^
            |
mul_cross_sum_left + add_cross_sum_chain
  `--> signed_nat_scale_equations_compose
```

The exposed graph formulas are exactly

$$
\operatorname{SignedNatScale}(0,i,0),
\qquad
\operatorname{SignedNatScale}(1,i,i),
$$

and

$$
\begin{aligned}
&\operatorname{SignedNatScale}(n,i,m)
\to \operatorname{SignedNatScale}(k,m,o)\\
&\hspace{34mm}\to
\operatorname{SignedNatScale}(kn,i,o).
\end{aligned}
$$

Here `0` is the unique signed-zero code and the product in the last scale slot
is the ordinary natural product. The full ten-row empty-context receipt table
is:

```{list-table}
:header-rows: 1
:widths: 37 7 7 7 42

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate SHA-256
* - `signed_nat_scale_of_decoded_equation`
  - 19
  - 17
  - 0
  - `348988d2b7802c5c319975a537c568f51b55b894890638b1465bc7c8617eb918`
* - `signed_nat_scale_to_decoded_equation`
  - 785
  - 28
  - 14
  - `66ef87988a3703a713a4ce0a16e235228df640be182c22d51d01f082ca5df1bd`
* - `signed_nat_scale_decoded_iff_equation`
  - 888
  - 31
  - 16
  - `1b96a56388461895781783b29c091b55a61f562b198a93c8c1a7449049ec1e6a`
* - `signed_nat_scale_total`
  - 431
  - 39
  - 8
  - `e1ee2921a7e967369bd70cd70564ef340ad643926c15c62dba394ae535e76947`
* - `signed_nat_scale_functional`
  - 1,698
  - 36
  - 34
  - `59f948b0d2c8335cd3cd0098fb4acec9f895d8db2f930393d4dad33375ee2727`
* - `mul_cross_sum_left`
  - 98
  - 17
  - 2
  - `ffa3381d8208858dee25aba6f2f96ddfe2252f7c4c45d724a84f29f043e42586`
* - `signed_nat_scale_equations_compose`
  - 575
  - 32
  - 13
  - `064add40a96584356d47ca6a5455d16273403d23648ea64de5c5b3c5dc37a76b`
* - `signed_nat_scale_zero`
  - 183
  - 21
  - 4
  - `0e24789df5c82b513e59f376f03758a8d8f5e8ab03869d7e54fde7b7118e63af`
* - `signed_nat_scale_one`
  - 257
  - 21
  - 7
  - `90f005fdc0330354282b2dfec0105558dbc4533f1ef6436bdc070ed3a8789c4b`
* - `signed_nat_scale_compose`
  - 1,453
  - 34
  - 30
  - `7548acf6871b7db3db4ba2cdaf89b9544e2d641c881a9f27e47dc4c77448b49e`
```

The direct D07 definition was chosen deliberately over the possible D06
alias `SignedMul(2*scale,input,output)`. That alias can be related to D07 by a
later theorem, but making it foundational would force a signed encoding of
every natural coefficient, add D06 to each dependency path, and hide the
simple equation needed by the forthcoming Bezout bridge. The direct graph
keeps the common coefficient path smaller and exposes exactly the natural
arithmetic being checked.

The core audit passes all eight focused tests and the law/helper audit passes
all nine. In addition to statement, hygiene, dependency, body, mutation,
registry-isolation, and two-cold-replay gates, their semantic oracles are
exhaustive over the selected domains:

- all \(17\cdot17=289\) scale/input pairs are tested against every one of 257
  candidate output codes;
- the natural helper checks exactly 425 assignments satisfying its cross-sum
  premise, and the decoded composition helper checks exactly 477 assignments
  satisfying both premises;
- zero and one are checked on the first 33 canonical codes, while composition
  is checked on all \(17^3=4{,}913\) bounded triples.

The raw-code regression is essential: \(2\cdot1=2\) in natural arithmetic,
but code `1` denotes \(-1\), so scaling it by two produces code `3`, the
canonical representation of \(-2\), rather than code `2`. Host evaluation is
only a test oracle; logical authority comes from the empty-context kernel
certificates above.

Two cache-cleared closures agree on the five-core-row, 65-theorem signed-stack
digest
`511aa0ba4a6dac1a22f52db740f539c675307b5b77b6b1a7d9ef2e00dd8a5331`.
Adding the five law/helper rows gives the 70-theorem digest
`81a18daf55e564c11dee83ce7465bc91876109a5e6bc092f75e0f31f46e27d8d`.
The closure is intuitionistic and reaches no DNE, forbidden automation,
division, remainder, CRT, Gödel-β, or classical theorem.

This checkpoint contains 70 signed candidates and 73 candidates overall,
with 82 theorem receipts across 15 K3 candidate modules and 17 focused
evidence tests. The public registry is unchanged at 393 entries with 56
public references; the definition layer is unchanged at 45 API rows over 44
distinct public-theorem replays; and the research catalog is unchanged at
394 entries. None of D07 is admitted. D08 `SignedBezout` is the next
signed-arithmetic gate.

The sealed checkpoint
[`campaign manifest`](https://github.com/nasqret/vietnam2026/blob/bc45de0da2ff60ca65d81d4b8cef612f0b935892/research/arithmetic-library/ha-number-theory-campaign.json)
and
[`signed-natural RFC`](https://github.com/nasqret/vietnam2026/blob/bc45de0da2ff60ca65d81d4b8cef612f0b935892/research/arithmetic-library/ha-canonical-signed-natural-rfc-v1.md)
bind these claims to the exact
[`core tactic source`](https://github.com/nasqret/vietnam2026/blob/bc45de0da2ff60ca65d81d4b8cef612f0b935892/peano-lab/py/peano_lab/library/ha_signed_nat_scale_candidate.py),
[`law tactic source`](https://github.com/nasqret/vietnam2026/blob/bc45de0da2ff60ca65d81d4b8cef612f0b935892/peano-lab/py/peano_lab/library/ha_signed_nat_scale_laws_candidate.py),
[`eight-test core audit`](https://github.com/nasqret/vietnam2026/blob/bc45de0da2ff60ca65d81d4b8cef612f0b935892/peano-lab/py/tests/test_ha_signed_nat_scale_candidate.py),
and
[`nine-test law audit`](https://github.com/nasqret/vietnam2026/blob/bc45de0da2ff60ca65d81d4b8cef612f0b935892/peano-lab/py/tests/test_ha_signed_nat_scale_laws_candidate.py).

### Canonical signed Bezout coefficients: D08

The legacy Euclidean layer represents a signed Bezout identity with four
naturals. Write

$$
\operatorname{BalancedBezout}(r,a,b)
\;:\!\Longleftrightarrow\;
\exists x_+,y_+,x_-,y_-,\quad
a x_+ + b y_+ = r + \bigl(a x_- + b y_-\bigr).
$$

This is honest natural arithmetic: it means
\(a(x_+-x_-)+b(y_+-y_-)=r\) without adding subtraction or an integer type.
D08 connects it to the parity-interleaved canonical signed codes. If
\(\operatorname{Decode}(x,x_+,x_-)\) and
\(\operatorname{Decode}(y,y_+,y_-)\) are the frozen D01 decoders, define

$$
\begin{aligned}
\operatorname{SignedBezout}(r,a,b,x,y)
\;:\!\Longleftrightarrow\;&
\exists x_+,x_-,y_+,y_-,\\
&\operatorname{Decode}(x,x_+,x_-)
\land \operatorname{Decode}(y,y_+,y_-)\\
&\land\;a x_+ + b y_+
   = r + \bigl(a x_- + b y_-\bigr).
\end{aligned}
$$

The checked endpoint is the intuitionistic pair of implications

$$
\operatorname{BalancedBezout}(r,a,b)
\quad\Longleftrightarrow\quad
\exists x,y,\ \operatorname{SignedBezout}(r,a,b,x,y),
$$

where the displayed \(\Longleftrightarrow\) is stored as a conjunction of
two implications. It does **not** claim that \((x,y)\) is unique. Canonical
representation makes each chosen coefficient unique as a code, but a Bezout
equation may have many coefficient pairs. For example,

$$
2(-1)+3(1)=1=2(2)+3(-1),
$$

so codes `(1,2)` and `(4,1)` are two distinct D08 witnesses for the same
result and inputs.

The main algebraic step takes raw coefficients and normalized coefficients:

$$
\begin{aligned}
x_+ + x'_- &= x_- + x'_+,\\
y_+ + y'_- &= y_- + y'_+,\\
a x_+ + b y_+ &= r + (a x_- + b y_-),
\end{aligned}
$$

and proves

$$
a x'_+ + b y'_+ = r + (a x'_- + b y'_-).
$$

The first two equalities come independently from `SignedBalance`. They are
lifted by `mul_cross_sum_left`, combined by
`add_balance_outputs_compose`, and oriented with ordinary commutativity. No
signed multiplication or natural-scale graph is needed in this bridge. The
proof also makes an easy-to-miss representation change explicit:
`BalancedBezout` stores witnesses in the order
`xp,yp,xn,yn`, while `SignedBezout` groups decoder parts as
`xp,xn,yp,yn`.

```text
flowchart LR
  SB[SignedBalance totality] --> F[balanced to signed]
  MC[mul_cross_sum_left] --> T[equation transport]
  AC[add_balance_outputs_compose] --> T
  T --> F
  R[signed to balanced] --> I[packaged equivalence]
  F --> I
```

The proof surface has four topologically ordered rows:

```{list-table}
:header-rows: 1
:widths: 34 10 10 10 36

* - Candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate SHA-256
* - `balanced_bezout_equation_transport`
  - 943
  - 34
  - 20
  - `9e3f3b984b0c9bdd42e7747f5660541364bb5bee3655b95b9242e5ed3305e4cc`
* - `balanced_bezout_to_signed_bezout`
  - 1,241
  - 39
  - 24
  - `f39a790749e8da2b6d6c36f3639e2b81ecdd1b5db892a543a7ece18941978923`
* - `signed_bezout_to_balanced_bezout`
  - 35
  - 23
  - 0
  - `f0fb3fa8d5f09c69d22721164468227765bab34b6f1eadb8d67593bfeb81fa28`
* - `balanced_bezout_iff_signed_bezout_exists`
  - 1,326
  - 40
  - 26
  - `1bc7e28457b07b7aaf37b48aea0f3f86b58035797aeca50a022c73409f6eae1d`
```

The focused audit pins the exact D08 template, statements, ordered
dependencies, tactic bodies, empty-context DAG receipts, false mutations,
registry isolation, and endpoint reachability. Its untrusted semantic oracle
exhausts 2,185 satisfying transport premises, 5,736 raw balanced witnesses,
and 1,600 bounded direct graph cases. It includes nonunique solutions, an
all-zero coefficient boundary, and a trap showing that the raw parity codes
cannot be substituted for decoded signed values.

Two cache-cleared closures agree on the complete 74-row signed-stack digest
`b7949148236ab243830a2bfebd80ddafeb31a63c5e70ace1c032de8bd2415f15`.
The transitive closure contains no DNE, forbidden automation, division,
remainder, CRT, Gödel-β, or classical theorem. The campaign now records 74
signed candidates, 77 candidates overall, and 86 exact receipts across 16 K3
candidate modules and 18 focused evidence tests. The public registry remains
393 entries with 56 public references; the definition freeze remains 45 rows
over 44 public theorems; and the catalog remains 394 entries. No D08 row is
publicly admitted.

The separate theorem that combines this bridge with
`gcd_balanced_bezout_exists` belongs to K4, not this strict K3 closure: the
public gcd route transitively reaches division. Likewise, D08 does not assert
a canonical choice of Bezout pair. Those are deliberate mathematical and
architectural boundaries, not missing hidden assumptions.

The sealed source checkpoint binds the exact
[`campaign manifest`](https://github.com/nasqret/vietnam2026/blob/bb02ee5a767f6c4c585916269de688e7068b3716/research/arithmetic-library/ha-number-theory-campaign.json),
[`signed-natural RFC`](https://github.com/nasqret/vietnam2026/blob/bb02ee5a767f6c4c585916269de688e7068b3716/research/arithmetic-library/ha-canonical-signed-natural-rfc-v1.md),
[`D08 tactic source`](https://github.com/nasqret/vietnam2026/blob/bb02ee5a767f6c4c585916269de688e7068b3716/peano-lab/py/peano_lab/library/ha_signed_bezout_candidate.py),
and
[`ten-test focused audit`](https://github.com/nasqret/vietnam2026/blob/bb02ee5a767f6c4c585916269de688e7068b3716/peano-lab/py/tests/test_ha_signed_bezout_candidate.py)
to commit `bb02ee5a767f6c4c585916269de688e7068b3716`.

### K4 client: a gcd with canonical signed coefficients

Once the strict D08 bridge is available, the public Euclidean theorem can be
given its canonical signed interface without reproving the algorithm. The
checked client states

$$
\forall a,b\;\exists d,x,y,\quad
\operatorname{IsGCD}(d,a,b)
\land \operatorname{SignedBezout}(d,a,b,x,y).
$$

Both named relations are expanded to the base HA grammar. The proof has just
two declared inputs:

```text
gcd_balanced_bezout_exists
        |
        v
raw gcd + four-natural Bezout witnesses
        |
        +---- balanced_bezout_to_signed_bezout (D08)
        v
gcd_signed_bezout_exists
```

The first theorem supplies `d` together with the relational-gcd proof and raw
coefficients. D08 normalizes only the coefficient conjunct; the gcd proof is
copied unchanged. No uniqueness of `(x,y)` is asserted.

```{list-table}
:header-rows: 1
:widths: 35 10 10 10 35

* - Candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate SHA-256
* - `gcd_signed_bezout_exists`
  - 3,535
  - 48
  - 74
  - `4edeb4ffc7de0b9aa0a870d2125f7640f2447a7358ba454abba3db003f9044a3`
```

The focused audit pins the 592-byte expanded statement (SHA-256
`2e729fe9d25b8afda315489713f0a4cd7980371bf621e8af9e557f4ffca7496e`),
its 20-command body, two cold closures, a false successor mutation, bounded
gcd semantics, and explicit nonunique Bezout pairs. The transitive closure
contains eight local K3 rows and 33 public theorems. Exactly the expected
division boundary is visible: `divides_remainder`,
`division_remainder_exists`, and `division_remainder_succ`. It contains no
DNE, CRT, Gödel-β, or classical theorem.

This is why the machine manifest adds the honest layer edge
\(K3\rightarrow K4\). The client is not appended to the strict 74-row K3
stack, whose digest stays
`b7949148236ab243830a2bfebd80ddafeb31a63c5e70ace1c032de8bd2415f15`.
At this intermediate checkpoint the complete isolated corpus had 78
candidates and 87 receipts across 18 candidate modules and 19 focused tests;
the public boundary was still 393 theorems. The later selective K4 admission
does not include this client: `gcd_signed_bezout_exists` is one of the 19
checked K4 conveniences which remain private.

The immutable source links are the
[`campaign manifest`](https://github.com/nasqret/vietnam2026/blob/1d10c37535d829280398c2522ff3fd9d5f059e6c/research/arithmetic-library/ha-number-theory-campaign.json),
[`K4 tactic source`](https://github.com/nasqret/vietnam2026/blob/1d10c37535d829280398c2522ff3fd9d5f059e6c/peano-lab/py/peano_lab/library/ha_signed_bezout_gcd_candidate.py),
and
[`six-test focused audit`](https://github.com/nasqret/vietnam2026/blob/1d10c37535d829280398c2522ff3fd9d5f059e6c/peano-lab/py/tests/test_ha_signed_bezout_gcd_candidate.py).

## Canonical gcd and universal-property lcm

This K4 tranche first closed the natural-valued gcd and lcm interface in
isolation and was then admitted selectively. It does not add either operation
as a term former. Divisibility remains the relation

$$
d\mid n\quad:\!\Longleftrightarrow\quad\exists q,\ n=dq,
$$

and the least-common-multiple relation is the exact order dual of `IsGCD`:

$$
\operatorname{IsLCM}(l,a,b)
\;:\!\Longleftrightarrow\;
(a\mid l)\land(b\mid l)\land
\forall c,\ (a\mid c)\to(b\mid c)\to(l\mid c).
$$

In the native parser this expands hygienically to

```text
(((exists x. l = a * x) /\ (exists y. l = b * y)) /\
 forall c. (exists u. c = a * u) ->
           (exists v. c = b * v) ->
           exists w. c = l * w)
```

No new predicate reaches the kernel. In particular,

$$
\gcd(a,b)\operatorname{lcm}(a,b)=ab
$$

is proved after the two universal properties; it is not used to define lcm.
The product equation alone would be nonfunctional at $(a,b)=(0,0)$.

### Forced boundary values

The universal property constructively forces

$$
\operatorname{lcm}(0,b)=0,\qquad
\operatorname{lcm}(a,0)=0,\qquad
\operatorname{lcm}(0,0)=0.
$$

The selected proof proves the right-zero constructor directly and derives the
left-zero constructor by symmetry. Those two constructors,
<a href="theorem-atlas.html#theorem-is_lcm_zero_right"><code>is_lcm_zero_right</code></a>
and
<a href="theorem-atlas.html#theorem-is_lcm_zero_left"><code>is_lcm_zero_left</code></a>,
are public. The derived zero-value and unique-existence conveniences remain
private. The companion gcd tranche supplies five function-style boundary
laws:

$$
\begin{aligned}
\operatorname{IsGCD}(g,a,0)&\;\Longleftrightarrow\;g=a,\\
\operatorname{IsGCD}(g,0,a)&\;\Longleftrightarrow\;g=a,\\
\operatorname{IsGCD}(g,1,a)&\;\Longleftrightarrow\;g=1,\\
\operatorname{IsGCD}(g,a,1)&\;\Longleftrightarrow\;g=1,
\end{aligned}
$$

together with equality of independently chosen gcd witnesses after swapping
the two inputs. All five close from the empty context and remain private.

### The constructive totality route

The 17-row structural lcm API proves its two multiple projections, leastness,
symmetry, uniqueness, zero/one/reflexive constructors, divisibility
constructors, product common-multiple witnesses, and the zero-value packages.
General totality is then obtained through the following K4 route:

```text
balanced Bezout for a gcd
        |
        +--> cancel a nonzero gcd --> Bezout result 1 --> coprime quotients
        |                                                   |
        |                                                   v
        |                                      product of quotients is an lcm
        |                                                   |
decide gcd = 0                                              v
        |                                        scale the lcm by the gcd
        +---------------------------> compatible gcd/lcm existence
                                                     |
                          +--------------------------+-------------------+
                          v                          v                   v
                 relational lcm exists       unique lcm value     gcd*lcm = a*b
```

The zero branch uses the forced-zero lcm law. The nonzero branch cancels the
gcd from a balanced Bezout equation, proves the two quotients coprime, takes
their product as an lcm, and scales it by the gcd. The split uses the already
proved constructive theorem `eq_decidable`; none of these certificates
contains `DNE` or a classical axiom.

### The public K4 atlas

Admission is an exact append-only slice: seven universal-property lcm lemmas
followed by nine bridge lemmas. Each name below opens its theorem-atlas card,
where the expanded HA statement, direct prerequisites, tactic source, and
certificate receipt can be inspected.

```{list-table}
:header-rows: 1
:widths: 13 40 47

* - Position
  - Public theorem
  - Mathematical role
* - 393
  - <a href="theorem-atlas.html#theorem-is_lcm_multiple_left"><code>is_lcm_multiple_left</code></a>
  - An lcm is a multiple of its left input.
* - 394
  - <a href="theorem-atlas.html#theorem-is_lcm_multiple_right"><code>is_lcm_multiple_right</code></a>
  - An lcm is a multiple of its right input.
* - 395
  - <a href="theorem-atlas.html#theorem-is_lcm_least"><code>is_lcm_least</code></a>
  - Every common multiple is a multiple of the lcm.
* - 396
  - <a href="theorem-atlas.html#theorem-is_lcm_symm"><code>is_lcm_symm</code></a>
  - Symmetry of the relational lcm specification.
* - 397
  - <a href="theorem-atlas.html#theorem-is_lcm_unique"><code>is_lcm_unique</code></a>
  - Uniqueness from the universal property.
* - 398
  - <a href="theorem-atlas.html#theorem-is_lcm_zero_right"><code>is_lcm_zero_right</code></a>
  - The forced right-zero constructor.
* - 399
  - <a href="theorem-atlas.html#theorem-is_lcm_zero_left"><code>is_lcm_zero_left</code></a>
  - The forced left-zero constructor.
* - 400
  - <a href="theorem-atlas.html#theorem-balanced_bezout_one_implies_coprime"><code>balanced_bezout_one_implies_coprime</code></a>
  - A balanced Bezout witness for one implies coprimality.
* - 401
  - <a href="theorem-atlas.html#theorem-coprime_product_is_lcm"><code>coprime_product_is_lcm</code></a>
  - The product of coprime inputs satisfies `IsLCM`.
* - 402
  - <a href="theorem-atlas.html#theorem-is_lcm_scale_nonzero"><code>is_lcm_scale_nonzero</code></a>
  - Nonzero common scaling preserves the lcm relation.
* - 403
  - <a href="theorem-atlas.html#theorem-balanced_bezout_cancel_gcd"><code>balanced_bezout_cancel_gcd</code></a>
  - Cancel a nonzero gcd from a balanced Bezout equation.
* - 404
  - <a href="theorem-atlas.html#theorem-gcd_zero_inputs"><code>gcd_zero_inputs</code></a>
  - Both inputs are zero when their gcd is zero.
* - 405
  - <a href="theorem-atlas.html#theorem-gcd_lcm_compatible_exists"><code>gcd_lcm_compatible_exists</code></a>
  - Construct compatible relational gcd and lcm witnesses.
* - 406
  - <a href="theorem-atlas.html#theorem-lcm_exists_relational"><code>lcm_exists_relational</code></a>
  - Totality of the relational lcm specification.
* - 407
  - <a href="theorem-atlas.html#theorem-canonical_lcm_exists_unique"><code>canonical_lcm_exists_unique</code></a>
  - Unique existence of the natural lcm value.
* - 408
  - <a href="theorem-atlas.html#theorem-gcd_lcm_product"><code>gcd_lcm_product</code></a>
  - The relational product identity (g l = a b).
```

```{list-table}
:header-rows: 1
:widths: 31 8 8 8 7 38

* - Public K4 endpoint
  - Nodes
  - Depth
  - Cuts
  - DNE
  - Certificate SHA-256
* - <a href="theorem-atlas.html#theorem-gcd_lcm_compatible_exists"><code>gcd_lcm_compatible_exists</code></a>
  - 9,038
  - 60
  - 101
  - 0
  - `dfe0e69fb172e48b6aa785c0c088ebf1a7cdf09c95ae436305d51d6224e90bc3`
* - <a href="theorem-atlas.html#theorem-lcm_exists_relational"><code>lcm_exists_relational</code></a>
  - 9,071
  - 61
  - 102
  - 0
  - `f4e764738627255eb885d78b5cefd74663d68be022370a8036ee450b116a7220`
* - <a href="theorem-atlas.html#theorem-canonical_lcm_exists_unique"><code>canonical_lcm_exists_unique</code></a>
  - 9,791
  - 62
  - 111
  - 0
  - `3ab4c410a0e4c6717e77d7f951d26304a35b5e9451df299167bb42cadf227747`
* - <a href="theorem-atlas.html#theorem-gcd_lcm_product"><code>gcd_lcm_product</code></a>
  - 10,441
  - 61
  - 112
  - 0
  - `c0829496624e993a4c437aa98c32355605109e728acd03d6b5d857fcb5350d0a`
```

The selective admission raises the runtime registry to **409** theorems and
the research catalog to **410** rows, of which **386** are `checked_m20`.
The campaign manifest now carries **72** public references, **116** isolated
candidates, and **141** exact theorem receipts. The strict 74-row K3 signed
stack and its digest
`b7949148236ab243830a2bfebd80ddafeb31a63c5e70ace1c032de8bd2415f15`
are unchanged, as is the frozen first-247 model curriculum.

### What remains private

Admission deliberately stops at the reusable mathematical interface. The
following 19 checked K4 conveniences retain exact receipts but are not public
registry entries:

* canonical gcd packaging (3): `canonical_gcd_exists`,
  `canonical_gcd_functional`, and `canonical_gcd_exists_unique`;
* gcd boundary conveniences (5): `canonical_gcd_zero_right_iff`,
  `canonical_gcd_zero_left_iff`, `canonical_gcd_one_left_iff`,
  `canonical_gcd_one_right_iff`, and `canonical_gcd_swap_functional`;
* residual lcm conveniences (10): `is_lcm_of_dvd`,
  `is_lcm_of_dvd_right`, `product_common_multiple`, `is_lcm_refl`,
  `is_lcm_one_left`, `is_lcm_one_right`, `lcm_zero_left_value`,
  `lcm_zero_right_value`, `lcm_zero_left_exists_unique`, and
  `lcm_zero_right_exists_unique`;
* the signed client (1): `gcd_signed_bezout_exists`.

A checked private receipt is evidence of empty-context closure, not an
admission by implication. The public/private boundary is therefore explicit
and machine-audited.

The current implementation and audit trail are the
[`canonical gcd/lcm RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-canonical-gcd-lcm-rfc-v1.md),
[`relational-lcm source`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_relational_lcm_candidate.py),
[`relational-lcm tests`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_relational_lcm_candidate.py),
[`totality/compatibility source`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_lcm_totality_bridge_candidate.py),
[`totality/compatibility tests`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_lcm_totality_bridge_candidate.py),
and the
[`exact K4 admission test`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_number_theory_k4_gcd_lcm_admission.py).

## Generalized CRT: the all-modulus binary criterion is closed

The M5a layer keeps congruence and gcd relational. Its readable definitions
are

$$
\operatorname{ModEq}(d,a,b)\;:\!\Longleftrightarrow\;
\exists u,v,\ a+du=b+dv,
$$

$$
\operatorname{CRTSolution}(x;m,n;a,b)\;:\!\Longleftrightarrow\;
\operatorname{ModEq}(m,x,a)\land\operatorname{ModEq}(n,x,b),
$$

and the already frozen result-first relation

$$
\operatorname{IsGCD}(g,m,n)
\;:\!\Longleftrightarrow\;
g\mid m\land g\mid n\land
\forall d\,(d\mid m\land d\mid n\to d\mid g).
$$

Every displayed predicate expands before parsing to the unchanged language
\(\{0,S,+,\times,=\}\). The kernel receives no congruence, gcd, quotient,
remainder, or CRT primitive.

The original eight-row foundation proves congruence algebra, necessity, and
obstruction. The new seven-row sufficiency ladder is:

```{list-table}
:header-rows: 1
:widths: 8 42 50

* - Row
  - Candidate
  - Mathematical role
* - 1
  - `factor_nonzero_right`
  - The right factor of a nonzero product is nonzero.
* - 2
  - `is_gcd_quotients_coprime_nonzero`
  - If \(m=gM\), \(n=gN\), and \(g\ne0\), then \(M,N\) are coprime.
* - 3
  - `is_gcd_nonzero_coprime_quotients`
  - Package the two factor equations, all three nonzero facts, and cofactor coprimality.
* - 4
  - `mod_eq_common_remainder_decomposition`
  - Compatible residues share \(r<g\): \(a=gA+r\), \(b=gB+r\).
* - 5
  - `crt_scaled_common_remainder_lift`
  - Solve modulo \(M,N\), scale by \(g\), then add the common \(r\).
* - 6
  - `generalized_binary_crt_sufficient_nonzero`
  - Gcd compatibility constructs an actual common solution for nonzero moduli.
* - 7
  - `generalized_binary_crt_solvable_iff_nonzero`
  - Solvability is equivalent to gcd compatibility for nonzero moduli.
```

The capstone has the standard mathematical statement

$$
\begin{aligned}
&m\ne0\to n\ne0\to \operatorname{IsGCD}(g,m,n)\to{}\\
&\qquad\Bigl[
  (\exists x\,\operatorname{CRTSolution}(x;m,n;a,b))
       \to \operatorname{ModEq}(g,a,b)
\Bigr]\\
&\qquad\land\Bigl[
  \operatorname{ModEq}(g,a,b)
       \to \exists x\,\operatorname{CRTSolution}(x;m,n;a,b)
\Bigr].
\end{aligned}
$$

### Why the cofactors are coprime

Suppose \(d\mid M\) and \(d\mid N\). Then

$$
gd\mid m,\quad gd\mid n,
$$

so greatestness in `IsGCD(g,m,n)` gives \(gd\mid g\). For some \(w\),

$$
g=(gd)w=g(dw).
$$

Since \(g\ne0\), left cancellation against \(g\cdot1\) gives \(1=dw\),
and hence \(d=1\). This is the whole cofactor-coprimality proof; it does not
need a new Bézout theorem.

### Construction

Compatibility supplies a common canonical remainder:

$$
a=gA+r,\qquad b=gB+r,\qquad r<g.
$$

The public coprime CRT produces \(z\) with

$$
z\equiv A\pmod M,\qquad z\equiv B\pmod N.
$$

Scale both congruences by \(g\), add the reflexive congruence \(r\equiv r\),
and choose

$$
x=gz+r.
$$

Then \(x\equiv a\pmod m\) and \(x\equiv b\pmod n\).

```text
flowchart LR
  G[IsGCD(g,m,n)] --> Q[m=gM, n=gN]
  Q --> NZ[g,M,N nonzero]
  Q --> CP[Coprime(M,N)]
  C[a congruent b mod g] --> R[a=gA+r, b=gB+r, r<g]
  CP --> B[binary_crt M N A B]
  B --> Z[z mod M=A, z mod N=B]
  Z --> SC[scale congruences by g]
  R --> ADD[add common remainder r]
  SC --> ADD
  ADD --> X[x=gz+r is a common solution]
  X --> IFF[nonzero solvability iff compatibility]
  N[necessity theorem] --> IFF
  IFF --> D[decide m=0 and n=0]
  ZL[left modulus zero: choose x=a] --> D
  ZR[right modulus zero: choose x=b] --> D
  D --> ALL[all-modulus solvability iff compatibility]
  ALL -. next .-> L[classify solutions modulo IsLCM]
```

```{list-table}
:header-rows: 1
:widths: 43 10 9 9 29

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate SHA-256 prefix
* - `is_gcd_quotients_coprime_nonzero`
  - 660
  - 33
  - 18
  - `b20e99453775b469`
* - `mod_eq_common_remainder_decomposition`
  - 2,894
  - 69
  - 43
  - `7615686f1fb9c23b`
* - `crt_scaled_common_remainder_lift`
  - 5,745
  - 52
  - 92
  - `188a46f051c74f8a`
* - `generalized_binary_crt_sufficient_nonzero`
  - 9,482
  - 74
  - 141
  - `9c1ad09a4bfb2ee8`
* - `generalized_binary_crt_solvable_iff_nonzero`
  - 10,073
  - 76
  - 149
  - `8956a66d8f72d512`
```

Two cache-cleared closures agree for every row. The focused tests pin the
expanded statements, dependencies, scripts, body metrics, complete proof-DAG
digests, false-endpoint mutations, and bounded arithmetic semantics. All
certificates use the intuitionistic checker and contain zero `DNE` nodes. No
formula or proof limit was raised.

### The zero boundary does not use division

The four-row M5b layer closes the cases deliberately excluded from the
remainder construction:

```{list-table}
:header-rows: 1
:widths: 43 57

* - Candidate
  - Mathematical role
* - `generalized_binary_crt_sufficient_zero_left`
  - From `IsGCD(g,0,n)`, public gcd uniqueness gives \(g=n\); choose \(x=a\).
* - `generalized_binary_crt_sufficient_zero_right`
  - From `IsGCD(g,m,0)`, public gcd uniqueness gives \(g=m\); choose \(x=b\).
* - `generalized_binary_crt_sufficient`
  - Constructively dispatch left-zero, right-zero, and both-nonzero cases.
* - `generalized_binary_crt_solvable_iff`
  - Combine total sufficiency with the earlier necessity theorem.
```

The first row includes \((m,n)=(0,0)\): compatibility is then equality of
the residues, so the chosen residue solves both equations. The total theorem
uses the already checked constructive decision `eq_decidable`; it does not
use excluded middle as a kernel principle. In readable notation the capstone
is

$$
\begin{aligned}
\operatorname{IsGCD}(g,m,n)\to\Bigl(&
  [\exists x\,\operatorname{CRTSolution}(x;m,n;a,b)
     \to \operatorname{ModEq}(g,a,b)]\\
  &\land[\operatorname{ModEq}(g,a,b)
     \to\exists x\,\operatorname{CRTSolution}(x;m,n;a,b)]\Bigr),
\end{aligned}
$$

with no assumptions that \(m\), \(n\), or \(g\) is nonzero.

```{list-table}
:header-rows: 1
:widths: 43 10 9 9 29

* - Closed candidate
  - Nodes
  - Depth
  - Cuts
  - Certificate SHA-256 prefix
* - `generalized_binary_crt_sufficient_zero_left`
  - 834
  - 37
  - 26
  - `074f07df17330847`
* - `generalized_binary_crt_sufficient_zero_right`
  - 805
  - 36
  - 26
  - `da2d830f65077816`
* - `generalized_binary_crt_sufficient`
  - 11,240
  - 78
  - 160
  - `931fbcc775154507`
* - `generalized_binary_crt_solvable_iff`
  - 11,825
  - 80
  - 168
  - `3f1d82f0f06df9e0`
```

All four certificates have zero `DNE` nodes and fit the existing limits. No
private canonical-gcd convenience theorem is a dependency. This is still
candidate evidence, not public admission: the registry remains at 409 and
the research catalog at 410.

### Complete solution classes via relational LCM

The four-row M5c layer now closes that classification boundary without adding
a primitive lcm function:

```{list-table}
:header-rows: 1
:widths: 28 37 35

* - Candidate
  - Exact surface interface
  - Ordered direct dependencies
* - `mod_eq_ordered_gap_multiple`
  - `k+x=y -> ModEq(d,x,y) -> Dvd(d,k)`
  - `add_comm`, `add_assoc`, `add_left_cancel`, `factor_difference`
* - `mod_eq_lcm_merge`
  - `IsLCM(l,m,n) -> ModEq(m,x,y) -> ModEq(n,x,y) -> ModEq(l,x,y)`
  - `le_total`, `mod_eq_symm`, the ordered-gap row, `is_lcm_least`,
    `mul_comm`, `remainder_decomposition_to_mod_eq`
* - `mod_eq_lcm_iff_pair`
  - Under `IsLCM(l,m,n)`, `ModEq(l,x,y)` iff
    `ModEq(m,x,y) /\ ModEq(n,x,y)`
  - `is_lcm_multiple_left`, `is_lcm_multiple_right`,
    `mod_eq_of_mod_eq_multiple`, the merge row
* - `crt_solution_class_iff_lcm`
  - For a fixed solution `x`, `CRTSolution(y,m,n,a,b)` iff
    `ModEq(l,y,x)`
  - `crt_solution_pair_congruent`, the LCM-iff-pair row, `mod_eq_trans`
```

The proof is subtraction-free. Total order chooses a directed gap between
two naturals. Congruence modulo each input modulus makes each modulus divide
that gap; `is_lcm_least` then makes the supplied relational LCM divide it.
The public LCM projections prove the converse direction. For the capstone,
the forward implication compares the candidate `y` with the fixed solution
`x`; the reverse implication composes `y == x` with the two congruences
already carried by `x`. This orientation is part of the audited interface.

Body receipts below use
`(dependencies, commands, nodes, depth, objects, edges, reused)`. Closed
receipts use
`(nodes, depth, objects, edges, reused, Cuts, DNE, certificate SHA-256)`.

```{list-table}
:header-rows: 1
:widths: 24 25 51

* - Closed candidate
  - Dependency-curried body
  - Empty-context certificate
* - `mod_eq_ordered_gap_multiple`
  - `(4,31,44,21,44,43,0)`
  - `(558,30,310,325,16,13,0,6a30012cfc1213bf167be2de794e05cdae2893ab075cfc24abf9b181bde9be67)`
* - `mod_eq_lcm_merge`
  - `(6,113,127,26,127,126,0)`
  - `(1315,33,653,685,33,25,0,46cd67f69ccf0c669de283fca6a74a0a85cf18d54f248f1a6f428122196a331b)`
* - `mod_eq_lcm_iff_pair`
  - `(4,46,56,21,56,55,0)`
  - `(1570,37,864,908,45,32,0,855d5745c1613304fc0a5f26c70fe9f795ed3ebcff4a7276e3745681d41fc91a)`
* - `crt_solution_class_iff_lcm`
  - `(3,62,79,27,79,78,0)`
  - `(2208,39,1055,1104,50,40,0,305a913aaca1c3e307d8ca77bb90c063dd67f3fa9f9bdd69e28cf4064cdff7b3)`
```

The theorem is uniform at \(l=0\): `ModEq(0,y,x)` is exactly \(y=x\), so
the solution class collapses to exact uniqueness. The proof does not divide
by the LCM and never asserts a remainder below zero. A bounded semantic audit
passed 1,296 LCM-equivalence cases, 4,692 fixed-solution classification
comparisons, and 678 comparisons with \(l=0\). Both cold closures check with zero `DNE`
and the existing resource limits. M5c raises the private evidence totals to
**116** candidate references and **141** exact receipts; the public registry
and catalog remain unchanged at **409** and **410**.

### Honest canonical boundary at zero and nonzero LCM

The three-row M5d layer now closes the boundary that M5c exposed. Write

$$
\operatorname{Below}(r,l)\;:\!\Longleftrightarrow\;
\exists h\;(h+S(r)=l).
$$

```{list-table}
:header-rows: 1
:widths: 28 38 34

* - Candidate
  - Exact surface result
  - Ordered direct dependencies
* - `crt_solution_unique_lcm_zero`
  - At `l=0`, every solution `y` equals a fixed solution `x`.
  - `crt_solution_class_iff_lcm`, `mod_eq_zero_iff_eq`
* - `crt_solution_canonical_remainder_nonzero`
  - At `l!=0`, produce `r` with `Below(r,l)`, `CRTSolution(r)`,
    `ModEq(l,r,x)`, and bounded uniqueness.
  - division/remainder, `mul_comm`, remainder-to-congruence, `mod_eq_symm`,
    M5c classification, `mod_eq_bounded_unique`
* - `generalized_binary_crt_canonical_boundary`
  - From `IsGCD`, `IsLCM`, and compatibility, return either an exactly unique
    zero-LCM solution or a unique bounded nonzero-LCM solution.
  - `eq_decidable`, total M5b sufficiency, the first two M5d rows
```

The capstone first constructs a fixed solution and decides `l=0`
constructively. In the zero branch, M5c plus `mod_eq_zero_iff_eq` gives exact
equality. In the nonzero branch, division produces the remainder of the fixed
solution; M5c transports it back into the CRT solution class, and bounded
congruence uniqueness makes it canonical. The auxiliary `ModEq(l,r,x)` is
retained in row 2 and intentionally hidden by the capstone.

```{list-table}
:header-rows: 1
:widths: 24 25 51

* - Closed candidate
  - Dependency-curried body
  - Empty-context certificate
* - `crt_solution_unique_lcm_zero`
  - `(2,33,37,28,37,36,0)`
  - `(2300,40,1126,1176,51,43,0,2afc46ac88613c95400eb37f80b1fbda095b18a7f6a774255426b48c35aed9ac)`
* - `crt_solution_canonical_remainder_nonzero`
  - `(6,83,141,39,141,140,0)`
  - `(4086,65,1668,1746,79,64,0,091e8f2b1ba7e4665b87071fcd924ea1098880d65a97bcdd264ed544e33ff0e4)`
* - `generalized_binary_crt_canonical_boundary`
  - `(4,66,76,33,76,75,0)`
  - `(17750,80,4239,4426,188,193,0,c704a17f6feed83142b160bbeafcc14764d5ae6590999187eed5455c3ad03bd7)`
```

The body and closed-receipt schemas are the same as in the M5c table. Two
cold closures agree and all three certificates have zero `DNE`. A retained
bounded audit checks 4,021 compatible systems with `m,n<7` and `a,b<11`:
611 zero-LCM exact-uniqueness cases and 3,410 nonzero-LCM canonical-remainder
cases. Since either zero input modulus forces the relational LCM to zero, the
first count is intentionally broader than the single `(0,0)` case. No branch
asserts a remainder below zero. The private evidence totals are now **119**
candidates and **144** exact receipts; public counts remain **409/410**.

### Executable solution or obstruction

M5e makes the binary result total without adding a host-language decision
oracle:

```{list-table}
:header-rows: 1
:widths: 28 40 32

* - Candidate
  - Exact surface result
  - Ordered direct dependencies
* - `mod_eq_decidable`
  - `ModEq(d,a,b) \/ ~ModEq(d,a,b)` for every natural `d`.
  - `eq_decidable`, `mod_eq_zero_iff_eq`, public
    `mod_eq_decidable_nonzero`
* - `generalized_binary_crt_solution_or_obstruction`
  - Given `IsGCD(g,m,n)`, return either compatibility plus an actual CRT
    solution, or incompatibility plus a proof that no solution exists.
  - `mod_eq_decidable`, total M5b sufficiency,
    `crt_incompatibility_obstructs_solution`
```

At modulus zero the first row decides equality and uses
`mod_eq_zero_iff_eq`; at nonzero modulus it reuses the public
remainder-based decision theorem. The second row cases on that proof. Its
positive branch constructs a solution, while its negative branch applies the
already isolated obstruction theorem. Both branches retain the compatibility
or incompatibility certificate, so the result contains more information than
`P \/ ~P` alone.

```{list-table}
:header-rows: 1
:widths: 24 25 51

* - Closed candidate
  - Dependency-curried body
  - Empty-context certificate
* - `mod_eq_decidable`
  - `(3,35,47,16,47,46,0)`
  - `(2339,70,1217,1278,62,44,0,298e2b18fff84bcf3a2ec69dbc464454f958d4155b7afb687f0bab2fd95efe7e)`
* - `generalized_binary_crt_solution_or_obstruction`
  - `(3,36,43,22,43,42,0)`
  - `(14182,80,3909,4090,182,182,0,16e7cb1c430fa4e17ea878adc72d34c92e0bc3f135c4a3cf24cb2a296b38e525)`
```

Two cold closures agree, false endpoint mutations fail, and both certificates
have zero `DNE` within unchanged limits. The retained semantic audit covers
847 all-modulus congruence decisions and all 5,929 systems with `m,n<7` and
`a,b<11`: 4,021 return compatibility with a solution and 1,908 return
incompatibility with unsolvability. This brings private evidence to **121**
candidates and **146** receipts; the public registry/catalog remain
**409/410**. M5d remains the separate composable canonicalization API.

### Raw-input total decision

M5f removes the need for a caller to supply a gcd witness. Its single theorem
has the readable statement

$$
\begin{aligned}
\forall m,n,a,b\;\exists g\;\bigl(&\operatorname{IsGCD}(g,m,n)\land
  \Bigl([\operatorname{ModEq}(g,a,b)\land
      \exists x\,\operatorname{CRTSolution}(x;m,n;a,b)]\\
  {}\lor{}&[\neg\operatorname{ModEq}(g,a,b)\land
      \neg\exists x\,\operatorname{CRTSolution}(x;m,n;a,b)]\Bigr)\bigr).
\end{aligned}
$$

The proof first applies `gcd_exists_relational`, obtaining an existential
natural \(g\) together with `IsGCD(g,m,n)`, and then invokes
`generalized_binary_crt_solution_or_obstruction`. Thus the exact ordered
dependency list has only those two rows. The theorem does **not** introduce a
primitive gcd function: its witness remains governed by the expanded
`IsGCD` relation. Nor does it return a bounded canonical solution. That is
the separate zero/nonzero-LCM interface supplied by M5d.

```{list-table}
:header-rows: 1
:widths: 24 25 51

* - Closed candidate
  - Dependency-curried body
  - Empty-context certificate
* - `generalized_binary_crt_total_decision`
  - `(2,17,42,25,42,41,0)`
  - `(15492,82,4052,4240,189,192,0,c2d915d2eb60ccbb2dac9f31e9e1f9c310c28264b74483ec97ae33a1a0d965ee)`
```

The body and closed tuples use the schemas specified above. The expanded
statement SHA-256 is
`42d29bf501421be60c1a2b14fa858a14abf230eee2f7669503db019d6b014151`.
Two cold closures agree, the certificate has zero `DNE` nodes, and no proof
limit changed. The raw-input semantic audit covers all 5,929 systems with
`m,n<7` and `a,b<11`: 4,021 take the solution branch and 1,908 take the
obstruction branch. Among the 121 systems whose relational gcd is zero, 11
are solvable and 110 are obstructed. The campaign now contains **122** private
candidates and **147** receipts; the public registry/catalog remain
**409/410**.

Finite generalized CRT remains gated by the independent finite-data
representation.

Read the
[`generalized-CRT RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-generalized-crt-rfc-v1.md),
[`congruence source`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_generalized_crt_congruence_candidate.py),
[`sufficiency source`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_generalized_crt_sufficiency_candidate.py),
[`zero-boundary source`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_generalized_crt_zero_boundary_candidate.py),
[`classification source`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_generalized_crt_classification_candidate.py),
[`canonical-boundary source`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_generalized_crt_canonical_boundary_candidate.py),
[`executable-boundary source`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_generalized_crt_decision_candidate.py),
[`raw-input decision source`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_generalized_crt_total_decision_candidate.py),
[`foundation audit`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_generalized_crt_congruence_candidate.py),
[`sufficiency audit`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_generalized_crt_sufficiency_candidate.py),
[`zero-boundary audit`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_generalized_crt_zero_boundary_candidate.py),
[`classification audit`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_generalized_crt_classification_candidate.py),
[`canonical-boundary audit`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_generalized_crt_canonical_boundary_candidate.py),
[`executable-boundary audit`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_generalized_crt_decision_candidate.py),
and the
[`raw-input decision audit`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_generalized_crt_total_decision_candidate.py)
for the exact expanded formulas and line-by-line tactic scripts.

## Selective M5 admission: the exact public boundary

The campaign did not promote every closed convenience theorem. It admitted
the exact dependency closure needed by three durable endpoints:
`generalized_binary_crt_solvable_iff`,
`generalized_binary_crt_canonical_boundary`, and
`generalized_binary_crt_total_decision`. In registry order, the resulting
23-row public surface is:

```{list-table}
:header-rows: 1
:widths: 23 77

* - Role
  - Exact public theorem names
* - Congruence and necessity
  - `mod_eq_zero_iff_eq`; `mod_eq_scale`;
    `crt_solution_pair_congruent`;
    `crt_common_solution_implies_gcd_compatible`;
    `crt_incompatibility_obstructs_solution`
* - Nonzero construction
  - `is_gcd_quotients_coprime_nonzero`;
    `mod_eq_common_remainder_decomposition`;
    `crt_scaled_common_remainder_lift`;
    `generalized_binary_crt_sufficient_nonzero`
* - All-modulus solvability
  - `generalized_binary_crt_sufficient_zero_left`;
    `generalized_binary_crt_sufficient_zero_right`;
    `generalized_binary_crt_sufficient`;
    `generalized_binary_crt_solvable_iff`
* - Relational-LCM solution class
  - `mod_eq_ordered_gap_multiple`; `mod_eq_lcm_merge`;
    `mod_eq_lcm_iff_pair`; `crt_solution_class_iff_lcm`
* - Canonical boundary
  - `crt_solution_unique_lcm_zero`;
    `crt_solution_canonical_remainder_nonzero`;
    `generalized_binary_crt_canonical_boundary`
* - Executable decision
  - `mod_eq_decidable`;
    `generalized_binary_crt_solution_or_obstruction`;
    `generalized_binary_crt_total_decision`
```

The exact six-row private residual is equally important:

- `mod_eq_add_cancel_left` and `mod_eq_add_cancel_right`;
- `mod_eq_unscale_nonzero`;
- `factor_nonzero_right`;
- `is_gcd_nonzero_coprime_quotients`; and
- `generalized_binary_crt_solvable_iff_nonzero`.

These six formulas still have deterministic empty-context receipts, but no
public registry position and therefore no `pa lib` authority. The distinction
is mathematical curation rather than a proof-status ambiguity: the public
23-row closure already contains every premise needed by the three selected
endpoints.

The admission appends positions 409--431 without changing the first-247 model
prefix. The current snapshot has **432** theorem cards and **1,185** direct
dependency edges. Its synchronized Obsidian vault has **531** notes and
**5,377** resolved links. The research catalog has **433** rows: 432 checked
theorems and the one explicitly representation-blocked conventional
integer-coefficient Bézout interface.

## Independent pair/cell checkpoint

The finite-data lane now has **15 closed private candidates**: seven literal
constructor and nil/cell-boundary rows, six shell-arithmetic rows, and two
injectivity rows. For \(s=x+y\), write

$$
B_s=s(s+1),
\qquad
\operatorname{pair}_2(x,y)=B_s+2y.
$$

This is twice the Cantor pairing polynomial. The shell layer proves the exact
constructive bounds

$$
B_s\leq \operatorname{pair}_2(x,y)<B_{s+1}.
$$

Consequently two unequal shell indices force two unequal codes. The final
`pair_code_injective` proof applies trichotomy to
\(s_1=x_1+y_1\) and \(s_2=x_2+y_2\). Either strict branch, together with
`pair_code_shell_separated`, would make the shared code strictly smaller than
itself, so \(s_1=s_2\). Cancelling the common boundary \(B_{s_1}\) gives
\(2y_1=2y_2\); `double_add_injective` gives \(y_1=y_2\); and one final
additive cancellation gives \(x_1=x_2\). Thus injectivity uses no decoder,
division, choice, or hidden host computation.

The two largest checkpoint receipts, displayed as `(nodes, depth)`, are
`pair_code_shell_separated = (1600, 30)` and
`pair_code_injective = (2525, 32)`. Every one of the 15 rows closes twice from
the empty context with zero DNE. Their transitive closures are quarantined to
the K0--K2 equality, addition, multiplication, order, cancellation, and
formula-specific induction foundation: no division, remainder, CRT,
Gödel-β, prime-factor coding, classical rule, or assumed sequence enters.

The full statements, tactic bodies, receipts, mutations, and bounded semantic
oracles are linked from the
[`pair/cell RFC`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-canonical-pair-cell-rfc-v1.md),
the three source modules
([seed](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_pair_cell_seed_candidate.py),
[shells](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_pair_shell_candidate.py),
[injectivity](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_pair_injective_candidate.py)),
and their focused audits
([seed test](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_pair_cell_seed_candidate.py),
[shell test](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_pair_shell_candidate.py),
[injectivity test](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_pair_injective_candidate.py)).

These rows remain private: the public runtime and research catalog stay at
**432** and **433** entries. The campaign now records **95** public references,
**114** closed candidates, **162** distinct receipts, **25** candidate modules,
and **34** focused test paths. At this checkpoint the honest next obligations
were cell functionality, strict head and tail bounds, and an independent
uniform computation-history representation supporting lists and finite maps.
A successor-tagged cell constructor alone cannot express variable tail
iteration, lookup, append, or folds.

Those obligations now continue in the separate post-K4/M3 K3B bridge. The
{doc}`Cell histories and extensional lookup <cell-history-and-lookup>` chapter
explains its conservative definitions, seventeen Alpha-only `alpha_closed` rows,
outer-head lookup equations, compact dependency map, and exact WMI closure
receipt. That later result does not retroactively move any K3B theorem into
strict K3 or Stable. The next {doc}`K3C validity and membership layer
<list-validity-and-membership>` appends seventeen Alpha-only `body_checked`
rows; they fail closed until their repeated isolated WMI receipt is recorded.

## Reproducing the boundary

From the repository root:

```bash
make ha-number-theory-check
python3 scripts/verify_arithmetic_knowledge_base.py
python3 scripts/build_peano_library_snapshot.py --check
python3 scripts/build_peano_library_channels.py --check
python3 scripts/verify_peano_library_channels.py
python3 scripts/build_peano_library_channels_v2.py --check
python3 scripts/verify_peano_library_channels_v2.py
```

The first command checks the 12-layer campaign manifest and all **162**
theorem receipts: **95** public evidence rows and **114** closed private
candidates. This includes the exact nine-row tranche-01 admission, the exact
16-row K4 admission, eight private gcd conveniences, ten private lcm
conveniences, seventy-four strict-K3 signed rows, the private K4 signed-gcd
client, the 15-row private pair checkpoint, and the complete M5a--M5f
generalized-CRT evidence ladder. The
generalized-CRT lane has **29** audited rows: the exact **23** public rows
listed above and six closed private residuals. The manifest also pins **25**
candidate modules and **34** focused test paths. It checks the 45-row
definition API over 44 distinct public-theorem replays. The second
cross-checks all **432** public runtime theorems against the **433**-row
research catalog. The third independently replays the full public ladder and
compares the deterministic snapshot.
The two v1 channel commands preserve the sealed parent. The final v2 command
checks the additive 902-row Alpha publication and unchanged Stable subset; it
does not perform the still-pending K3C WMI closure work.
