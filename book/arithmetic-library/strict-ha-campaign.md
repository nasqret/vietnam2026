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
[`ha-number-theory-campaign.json`](https://github.com/nasqret/vietnam2026/blob/bb02ee5a767f6c4c585916269de688e7068b3716/research/arithmetic-library/ha-number-theory-campaign.json).
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
  - The representation is frozen. Seventy-four parity, decoder,
    code-extensionality, balance-normalization, negation, addition, and
    multiplication theorems, together with the direct natural-scaling graph,
    its laws, and the balanced-to-signed Bezout bridge, close from the empty
    context without division.
* - Canonical pair/cell coding
  - design frozen
  - Doubled-Cantor pairs and successor-tagged cells have exact expanded
    templates. Their theorem ladder has not yet been proved, and uniform lists
    remain blocked on a computation-trace representation.
```

The public registry therefore has 393 entries. The first nine campaign
theorems occupy append-only positions 384--392. The three gcd and seventy-four
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

## Independent pair/cell checkpoint

The finite-data lane has selected a representation for pairs and single cells,
but not yet for arbitrary lists. For `s=x+y`, define

$$
\operatorname{PairCode}(c,x,y)
\quad\Longleftrightarrow\quad
c=s(s+1)+2y.
$$

This is twice the Cantor pairing polynomial. The constructor is a literal
Peano term, while injectivity can proceed by doubled-triangular shell bounds.
It needs no division, remainder, CRT, Gödel-β code, square root, or prime
factorization. Cells use the successor tag

$$
\operatorname{Cell}(c,h,t)
\quad\Longleftrightarrow\quad
c=S\bigl((h+t)S(h+t)+2t\bigr),
$$

with `0` reserved for nil.

The important negative result of the design audit is architectural, not
mathematical: a finite first-order macro cannot follow a cell tail a variable
number of times merely by textual recursion. Pairing alone therefore gives
fixed-length schemas, not an honest uniform formula
`ListValid(code,length)`. General lookup, append, folds, finite maps, and
finite CRT remain blocked until the campaign selects an independent encoded
computation history or a proved conservative primitive-recursive definition
mechanism.

The
[`pair/cell RFC`](https://github.com/nasqret/vietnam2026/blob/01fb459bc2ef797ca1e1e76b353c219dcc1eecb6/research/arithmetic-library/ha-canonical-pair-cell-rfc-v1.md)
freezes eight exact expanded templates and their SHA-256 receipts, the pair
injectivity and cell-descent theorem ladder, forbidden dependencies, and four
honest ways to resolve the uniform-list blocker. It is a design target; no
pair theorem or list theorem is claimed by that document.

Read the complete
[`signed-natural RFC`](https://github.com/nasqret/vietnam2026/blob/bb02ee5a767f6c4c585916269de688e7068b3716/research/arithmetic-library/ha-canonical-signed-natural-rfc-v1.md)
for the exact formulas, hashes, forbidden dependency paths, and staged proof
obligations.

## Reproducing the boundary

From the repository root:

```bash
make ha-number-theory-check
python3 scripts/verify_arithmetic_knowledge_base.py
python3 scripts/build_peano_library_snapshot.py --check
```

The first command checks the 12-layer campaign manifest, all 86 theorem
receipts, the 45-row definition API over 44 distinct public-theorem replays,
the nine public admissions, the three isolated gcd candidates, and the
seventy-four isolated signed representation, normalization, arithmetic,
natural-scaling, and Bezout-bridge candidates. The
second cross-checks all 393 public runtime theorems against the 394-row
research catalog. The third independently replays the full public ladder and
compares the deterministic snapshot.
