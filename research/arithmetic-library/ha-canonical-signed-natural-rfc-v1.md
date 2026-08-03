# RFC HA-K3-SIGNED-1: canonical signed naturals by parity interleaving

**Status:** representation frozen; decoder, code-extensionality,
balance-normalization, and negation candidate tranches are closed but not
publicly admitted
**Scope:** HA3 signed coefficients and the signed-integer component of K3  
**Object language:** first-order HA over \(\{0,S,+,\times,=\}\)  
**Controlling documents:**
[`ha-number-theory-formalization-campaign-blueprint.md`](ha-number-theory-formalization-campaign-blueprint.md)
and
[`ha-definition-representation-freeze-v1.md`](ha-definition-representation-freeze-v1.md)

This RFC selects a natural-number representation for signed integers and
freezes its intended base-language relations. It does not itself register a
parser definition, introduce a kernel symbol, provide a certificate, or admit
a theorem. Current implementation and evidence status is recorded in
`ha-number-theory-campaign.json`; the RFC identifiers and theorem names below
remain the normative design obligations. Source inventory anchors must still
pass the campaign's dependency and replay audits before use.

The words **must**, **must not**, **should**, and **may** are normative within
this RFC.

## 1. Decision

Use a **parity-interleaved code with normalized sign-magnitude semantics**:

\[
\begin{array}{c|ccccc}
\text{integer} & 0 & -1 & +1 & -2 & +2 \\
\hline
\text{code}    & 0 &  1 &  2 &  3 &  4
\end{array}
\]

More generally,

\[
\operatorname{enc}(p)=2p\quad(p\in\mathbb N),\qquad
\operatorname{enc}(-(k+1))=2k+1.
\]

Thus even codes are nonnegative and odd codes are strictly negative. The
semantic decoder returns a pair \((p,n)\) denoting \(p-n\), constrained so
that at least one component is zero. The negative branch returns a successor
magnitude, so negative zero has no representation.

This is the selected representation, not merely a provisional tie-break. It
is justified by four properties specific to the current campaign:

1. every natural is a valid code, so validity is not a partial side
   condition carried through later theorems;
2. zero has exactly one code and negative zero cannot be constructed;
3. decoding uses constructive parity decomposition and elementary
   cancellation only;
4. the code does not depend on the still-unfrozen pair/list representation,
   division, CRT, `BetaAt`, or `Product`.

The choice is therefore storage by parity and semantics by normalized
sign-magnitude. It satisfies the campaign's sign-magnitude requirement
without placing a pair container inside every signed value.

## 2. Alternatives considered

### 2.1 Pair-coded sign-magnitude

A conventional alternative stores a pair \((s,m)\), where \(s\in\{0,1\}\),
and imposes

\[
s=1\Longrightarrow m>0.
\]

One sign denotes \(+m\), the other denotes \(-m\), and the displayed
constraint removes negative zero.

This representation is mathematically sound and visually direct. It was not
selected for the first signed layer because:

- it cannot be frozen as a natural code until the independent K3 pair codec
  and its projection theorems are frozen;
- most naturals are invalid unless the pair codec, sign-bit restriction, and
  zero convention are all carried as premises;
- signed equality inherits pair validity and projection dependencies; and
- HA3 needs signed Bezout coefficients before K3 lists and finite maps are
  otherwise needed.

Pair-coded sign-magnitude remains a possible interoperability format after
the pair layer closes. Any conversion theorem must show literal agreement
with the parity code's decoded value; it must not create a second canonical
equality for signed integers.

### 2.2 Parity/interleaving

Parity interleaving stores the sign in the low-order parity class and the
magnitude in the half. It has no invalid codes. Its cost is that encoded
addition and multiplication are graph relations rather than the ambient
natural `+` and `*`, and numeric order on codes is unrelated to signed order.

Those costs are acceptable. The campaign already requires conservative
operation graphs, and no theorem may silently use natural order on signed
codes. In return, signed coding can be developed directly from K0--K2.

### 2.3 Unnormalized pairs of naturals

The existing balanced convention treats \((p,n)\) as \(p-n\). It is an
excellent proof interface but not a canonical data representation: for every
\(t\), \((p+t,n+t)\) denotes the same integer. It remains the bridge format
for existing Bezout witnesses, not the identity of a signed object.

## 3. Normative boundary conventions

- The carrier of signed codes is all of \(\mathbb N\).
- Code `0` is signed zero.
- Code `1` is negative one; code `2` is positive one.
- `2 * p` decodes to \((p,0)\).
- `2 * k + 1` decodes to \((0,S(k))\).
- There is no constructor for a negative magnitude of zero.
- Equality of represented signed integers is literal equality of their
  natural codes. No quotient equality and no separate `SignedEq` predicate
  are introduced.
- Natural coercion is the graph equation `code = 2 * n`.
- Natural order on codes has no signed mathematical meaning.
- Signed operations are relations until totality and functionality have
  object-level HA certificates. A host function may be an oracle or
  elaborator convenience, never the trusted meaning of an operation.
- All formulas must expand before reaching the unchanged kernel.

The first five decoder values are fixed regression fixtures:

| Code | Positive part | Negative part | Meaning |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 1 | 0 | 1 | -1 |
| 2 | 1 | 0 | +1 |
| 3 | 0 | 2 | -2 |
| 4 | 2 | 0 | +2 |

## 4. Exact base-language definitions

The names in this section are design labels for prospective hygienic surface
macros. The text in each `text` block is the normative template. It contains
only the existing term and formula grammar; nested defined-predicate calls
are intentionally absent. Parenthesization is normative because the current
parser associates repeated conjunctions to the left unless told otherwise.

Numerals remain parser notation and elaborate to successors of zero. In
particular, `1` is `S 0` and `2` is `S (S 0)`.

### 4.1 `SignedDecode(code,pos,neg)`

Stable RFC identifier: `HA-K3-SIGNED-D01`.

```text
(code = 2 * pos /\ neg = 0) \/ exists half. ((code = 2 * half + 1 /\ pos = 0) /\ neg = S half)
```

This is the only primitive semantic decoder. It means that `code` denotes
the formal difference `pos-neg`, with normalized parts.

### 4.2 `SignedValid(code)`

Stable RFC identifier: `HA-K3-SIGNED-D02`.

```text
exists pos neg. ((code = 2 * pos /\ neg = 0) \/ exists half. ((code = 2 * half + 1 /\ pos = 0) /\ neg = S half))
```

This relation is retained for uniform K3 APIs even though its intended
totality theorem says every natural satisfies it.

### 4.3 `SignedBalance(code,left,right)`

Stable RFC identifier: `HA-K3-SIGNED-D03`.

```text
exists pos neg. (((code = 2 * pos /\ neg = 0) \/ exists half. ((code = 2 * half + 1 /\ pos = 0) /\ neg = S half)) /\ left + neg = right + pos)
```

`SignedBalance(code,left,right)` says that the canonical code represents the
possibly unnormalized formal difference `left-right`. It is the normalization
boundary between four-natural balanced arithmetic and canonical signed data.

### 4.4 `SignedNegate(input,output)`

Stable RFC identifier: `HA-K3-SIGNED-D04`.

```text
exists pos neg. (((input = 2 * pos /\ neg = 0) \/ exists input_half. ((input = 2 * input_half + 1 /\ pos = 0) /\ neg = S input_half)) /\ ((output = 2 * neg /\ pos = 0) \/ exists output_half. ((output = 2 * output_half + 1 /\ neg = 0) /\ pos = S output_half)))
```

The output decoder swaps the normalized positive and negative parts. This
also fixes `SignedNegate(0,0)`.

### 4.5 `SignedAdd(left,right,output)`

Stable RFC identifier: `HA-K3-SIGNED-D05`.

```text
exists lp ln rp rn op on. (((left = 2 * lp /\ ln = 0) \/ exists left_half. ((left = 2 * left_half + 1 /\ lp = 0) /\ ln = S left_half)) /\ (((right = 2 * rp /\ rn = 0) \/ exists right_half. ((right = 2 * right_half + 1 /\ rp = 0) /\ rn = S right_half)) /\ (((output = 2 * op /\ on = 0) \/ exists output_half. ((output = 2 * output_half + 1 /\ op = 0) /\ on = S output_half)) /\ (lp + rp) + on = (ln + rn) + op)))
```

The final equation is the subtraction-free expansion of

\[
(l_p-l_n)+(r_p-r_n)=o_p-o_n.
\]

### 4.6 `SignedMul(left,right,output)`

Stable RFC identifier: `HA-K3-SIGNED-D06`.

```text
exists lp ln rp rn op on. (((left = 2 * lp /\ ln = 0) \/ exists left_half. ((left = 2 * left_half + 1 /\ lp = 0) /\ ln = S left_half)) /\ (((right = 2 * rp /\ rn = 0) \/ exists right_half. ((right = 2 * right_half + 1 /\ rp = 0) /\ rn = S right_half)) /\ (((output = 2 * op /\ on = 0) \/ exists output_half. ((output = 2 * output_half + 1 /\ op = 0) /\ on = S output_half)) /\ (lp * rp + ln * rn) + on = (lp * rn + ln * rp) + op)))
```

The positive product contribution is `lp*rp + ln*rn`; the negative
contribution is `lp*rn + ln*rp`.

### 4.7 `SignedNatScale(scale,input,output)`

Stable RFC identifier: `HA-K3-SIGNED-D07`.

```text
exists ip inn op on. (((input = 2 * ip /\ inn = 0) \/ exists input_half. ((input = 2 * input_half + 1 /\ ip = 0) /\ inn = S input_half)) /\ (((output = 2 * op /\ on = 0) \/ exists output_half. ((output = 2 * output_half + 1 /\ op = 0) /\ on = S output_half)) /\ scale * ip + on = scale * inn + op))
```

This direct graph is the preferred interface for multiplying a signed
coefficient by a natural. It avoids coercing the natural to a signed code in
the common Bezout path.

### 4.8 `SignedBezout(result,a,b,x,y)`

Stable RFC identifier: `HA-K3-SIGNED-D08`.

```text
exists xp xn yp yn. (((x = 2 * xp /\ xn = 0) \/ exists x_half. ((x = 2 * x_half + 1 /\ xp = 0) /\ xn = S x_half)) /\ (((y = 2 * yp /\ yn = 0) \/ exists y_half. ((y = 2 * y_half + 1 /\ yp = 0) /\ yn = S y_half)) /\ a * xp + b * yp = result + (a * xn + b * yn)))
```

This relation means \(aX+bY=\mathit{result}\), where `x` and `y` are the
canonical codes of \(X\) and \(Y\). The coefficients satisfying a Bezout
identity are generally not unique. Therefore `SignedBezout` has no
functionality obligation in `(x,y)`. Canonical representation of each
coefficient must not be confused with canonical selection of a coefficient
pair.

### 4.9 Template identity receipts

Each digest is SHA-256 of the UTF-8 bytes between the corresponding
`text` fences, excluding the fence-newline on either side.

| RFC identifier | SHA-256 |
|---|---|
| `HA-K3-SIGNED-D01` | `06d5b4bd0034d03439b5976b70074a836ca1598b4c32794d50f1f95691ed7922` |
| `HA-K3-SIGNED-D02` | `19c754659652d9158c1ac26e86cabc3ddeab385412d4e485861ffffdc9de977a` |
| `HA-K3-SIGNED-D03` | `8cf2a9b1678dfe5b774a01adf746df046b2056e1ae620c8b0de89c741b7e4997` |
| `HA-K3-SIGNED-D04` | `67086486e367deed66d5dc66e2f7de5ec7aa280c542086aefd4be8e2330f1f11` |
| `HA-K3-SIGNED-D05` | `29eaf592586c3bc9ec951b09b17d08c184284950f1997a3c109a048a8e610629` |
| `HA-K3-SIGNED-D06` | `9b5a4a168cea119713e6892e590344fffd91c3abea6d349255edee0dcbe1af27` |
| `HA-K3-SIGNED-D07` | `ea3c130a4f8fe5f1a9d18cdbfbc5017175801db23d2e8ac66e6429fdfa1dfa6a` |
| `HA-K3-SIGNED-D08` | `385bb4059c37669d69b2b069e59fb8ff32d6b48f097df79673cc193359ccfb78` |

These are representation receipts only. They are not formula theorem hashes
or certificate hashes.

## 5. Definitions deliberately deferred

The first freeze does not introduce signed order, subtraction, absolute
value, division, quotient, remainder, powers, or a general signed polynomial
evaluator. They can be added after the core ring graph is accepted.

In particular:

- subtraction should be derived from `SignedNegate` and `SignedAdd`;
- absolute value should expose a natural output graph from `SignedDecode`;
- signed order should be defined by a subtraction-free cross-sum comparison,
  then related to code constructors;
- lists of signed integers should store the natural code chosen here; signed
  coding must not depend on the list codec in return.

No operation may be defined by natural arithmetic directly on the codes. For
example, natural addition of codes does not implement signed addition.

## 6. Required theorem ladder

The following is the normative dependency order. None of these rows is a
proof-status assertion.

```text
K0/K1 equality, addition, multiplication, order, induction
  |
  +--> parity_cases
  +--> K1-only even/odd separation
  +--> doubling and successor cancellation
  |
  v
SignedDecode constructors, totality, functionality, normality
  |
  +--> SignedBalance totality and unique code
  |       |
  |       +--> SignedAdd totality/functionality
  |       +--> SignedMul totality/functionality
  |       +--> SignedNatScale totality/functionality
  |
  +--> SignedNegate totality/functionality
  |
  v
balanced-pair normalization
  |
  v
BalancedBezout <--> existence of SignedBezout codes
  |
  v
relational gcd + signed coefficient packaging
```

### 6.1 Pre-decoder arithmetic dependencies

The intended source inventory anchors are `parity_cases`,
`odd_half_unique`,
`mul_left_cancel_nonzero`, `add_left_cancel`, `add_right_cancel`,
`succ_injective`, `lt_trichotomy`, `eq_decidable`, and the ordinary additive
and multiplicative algebra API.

The current source implementation of `even_odd_exclusive_pointwise` names
`division_remainder_unique` as a dependency. That route is forbidden here:
K3 depends on K0--K2, while division belongs to K4. Before the decoder can be
accepted, the campaign must supply and audit a K1-only separation lemma of
the shape

```text
forall n even_half odd_half. n = 2 * even_half -> n = 2 * odd_half + 1 -> false
```

using induction/order/cancellation but not division. The dependency audit
must be transitive. Renaming the existing theorem or hiding the K4 edge
behind a cut would not satisfy this requirement.

The other small prerequisite wrapper is:

```text
even_half_unique:
forall n a b. n = 2 * a -> n = 2 * b -> a = b
```

It should depend only on nonzero multiplication cancellation and the numeral
fact `~(2 = 0)`.

### 6.2 Decoder obligations

The minimum decoder API is:

1. `signed_decode_nonnegative_constructor`:
   `forall p. SignedDecode(2*p,p,0)`;
2. `signed_decode_negative_constructor`:
   `forall k. SignedDecode(2*k+1,0,S k)`;
3. `signed_decode_total`:
   `forall code. exists pos neg. SignedDecode(code,pos,neg)`;
4. `signed_decode_functional`: two decodings of one code have equal positive
   and negative parts;
5. `signed_decode_normal`: decoding implies `pos = 0 \/ neg = 0`;
6. `signed_decode_zero_iff`: decoding to `(0,0)` is equivalent to `code = 0`;
7. `signed_valid_all`: `forall code. SignedValid(code)`;
8. `signed_code_eq_iff_balance`: for decoded `x` and `y`, literal code
   equality is equivalent to `xp + yn = xn + yp`;
9. `signed_eq_decidable`: literal equality of signed codes is decidable.

The biconditionals above must be stored as a conjunction of the two
intuitionistically valid implications; the base grammar has no primitive
`iff`.

### 6.3 Balanced-pair normalization obligations

The central constructor theorem is:

```text
signed_balance_total:
forall left right. exists code. SignedBalance(code,left,right)
```

Its intended constructive split is the three-way natural comparison of
`left` and `right`:

- equality produces code `0`;
- `left < right` supplies `right = left + S gap` and produces code
  `2*gap+1`;
- `right < left` supplies `left = right + S gap` and produces code
  `2*S(gap)`.

Required companion theorems are:

- `signed_balance_functional`: the code for a fixed balanced pair is unique;
- `signed_decode_to_balance`: a decoder witness gives the corresponding
  balanced witness;
- `signed_balance_extensional`: cross-sum-equivalent balanced pairs produce
  the same code;
- `signed_balance_zero_iff`: the balanced code is zero exactly when
  `left = right`.

No least-witness principle or unbounded excluded-middle principle is part of
this route. The source entry named `lt_trichotomy` is the intended comparison
anchor and must pass the same replay and transitive-dependency audit as every
other imported theorem.

#### 6.3.1 Closed candidate checkpoint

The representation-level normalization obligations are now implemented as
closed, nonpublic candidates. In dependency order they are:

```text
signed_balance_total
signed_decode_to_balance
signed_balance_equations_cross_sum
signed_balance_extensional
signed_balance_functional
signed_balance_zero_iff
```

The separate decoded-code bridge closes in both directions and is packaged as
`signed_code_eq_iff_balance`. Thus literal equality of two decoded canonical
codes is now connected constructively to the subtraction-free cross sum

```text
xp + yn = xn + yp.
```

All nine new certificates check from the empty context, contain no `DNE`, and
their transitive dependency closures contain no division, remainder, CRT, or
beta-coded theorem. They remain outside the public registry. The next
topological obligation is `SignedNegate`, not addition or multiplication.

### 6.4 Arithmetic graph obligations

Each of `SignedNegate`, `SignedAdd`, `SignedMul`, and `SignedNatScale` must
receive:

- an object-level totality theorem;
- an object-level output-functionality theorem;
- a decoder/specification theorem in both directions;
- constructor boundary tests for zero, positive one, and negative one; and
- a transitive dependency receipt showing only K0--K2 and earlier signed
  rows.

The first arithmetic acceptance gate additionally requires:

- negation fixes zero and is involutive;
- addition has zero as identity, is commutative and associative, and adding
  a value to its negation yields zero;
- multiplication has zero and one laws, is commutative and associative, and
  distributes over addition;
- natural scaling by zero and one has the expected results and composes with
  natural multiplication;
- literal output equality, not a newly postulated equivalence relation, is
  used in every law.

These laws may be proved through decoded balanced equations. They must not be
implemented as trusted arithmetic on host integers.

#### 6.4.1 Closed negation checkpoint

The first arithmetic graph is now closed at candidate status. Its eight rows
are, in dependency order:

```text
signed_decode_swap_exists
signed_negate_of_swapped_decode
signed_negate_to_swapped_decode
signed_negate_total
signed_negate_functional
signed_negate_zero
signed_negate_symmetric
signed_negate_involutive
```

The proof follows D04 literally: decode the input pair and decode the output
with its two parts swapped. It does not use host subtraction or depend on
`SignedBalance`. The largest certificate is the involution theorem at 1,199
structural nodes and depth 35. All eight certificates close from the empty
context without `DNE`, division, remainder, CRT, or beta-coded dependencies,
and remain outside the public registry. `SignedAdd` is the next arithmetic
graph obligation.

#### 6.4.2 Closed addition-core checkpoint

The exact D05 graph now has a five-row closed candidate core, in dependency
order:

```text
signed_add_of_decoded_equation
signed_add_to_decoded_equation
signed_add_decoded_iff_equation
signed_add_total
signed_add_functional
```

The introduction row packages three decoder witnesses and the contribution
equation

```text
(lp + rp) + on = (ln + rn) + op.
```

The elimination row uses decoder functionality to recover that same equation
from any D05 witness. Totality decodes both inputs, normalizes their positive
and negative contribution sums with `SignedBalance`, and packages the
normalized output. Functionality transports two output witnesses to a common
balanced pair and applies `signed_balance_functional`.

The five empty-context certificates have respectively 26, 823, 956, 411, and
1,754 structural nodes, with depths 23, 35, 39, 27, and 38. Their exact
certificate hashes and statements are pinned in the campaign manifest and
focused test. The 31-theorem signed-stack digest is
`11f41d395be9597892e2d5577ff80b54d04a61a57c81e50d02bc335c7e6012da`.
The transitive closure contains no `DNE`, division, remainder, CRT, or
beta-coded theorem and does not use `SignedNegate`.

This closes only the total functional graph and its decoded specification.
The zero identities, commutativity, associativity, and inverse law remain
separate proof obligations. No algebraic law and no public admission is
claimed by this checkpoint.

#### 6.4.3 Closed elementary addition laws

The next five closed candidates establish the inexpensive graph laws:

```text
signed_add_commutative
signed_add_zero_left
signed_add_zero_right
signed_add_negate_right_zero
signed_add_negate_left_zero
```

Commutativity swaps the two decoder pairs and commutes the positive and
negative contribution sums. Left zero decodes the input once, reuses that
decoder for the output, and supplies the explicit canonical zero decoder;
right zero follows by graph commutativity. The inverse laws destruct the D04
negation graph, whose output decoder swaps the source parts, and construct the
D05 zero-output graph. Neither inverse proof uses host subtraction.

The five certificates contain respectively 139, 266, 427, 145, and 299
structural nodes, at depths 38, 25, 40, 24, and 40. Two cold replays agree on
the complete 36-theorem signed-stack digest
`a5fdad35078f386ccb42fd6e17f942f83f504aaaf748c40259b68a2798ab28c7`.
Their exact transitive dependency union consists only of `add_comm`,
`add_succ_left`, `zero_add`, `parity_cases`, decoder totality, the D05
introduction theorem, and earlier laws in this five-row tranche. It reaches no
division, remainder, CRT, beta, classical, or DNE theorem.

The private literal-zero expanders used by these statements are regression
checked for alpha-identity with D05 instantiated at the corresponding zero
slot; they add no surface or kernel primitive. Associativity is still open and
will use a separately reviewed cross-sum composition helper. Therefore the
full addition-law acceptance gate remains open, and all 36 signed results
remain nonpublic.

### 6.5 Bezout bridge obligations

The existing expanded balanced relation is

```text
exists xp yp xn yn. a * xp + b * yp = result + (a * xn + b * yn)
```

The required forward bridge has the shape:

```text
forall result a b.
  (exists xp yp xn yn.
     a * xp + b * yp = result + (a * xn + b * yn)) ->
  exists x y. SignedBezout(result,a,b,x,y)
```

The proof obligation normalizes `(xp,xn)` and `(yp,yn)` separately with
`SignedBalance`, then transports the displayed equation by additive and
multiplicative algebra.

The required reverse bridge has the shape:

```text
forall result a b x y.
  SignedBezout(result,a,b,x,y) ->
  exists xp yp xn yn.
    a * xp + b * yp = result + (a * xn + b * yn)
```

After both directions close, a packaged equivalence may be exposed as
`balanced_bezout_iff_signed_bezout_exists`. The proposed client theorem
`gcd_signed_bezout_exists` may then combine the bridge with relational gcd
and balanced-Bezout existence. It may assert existence of codes `x,y`; it
must not assert uniqueness of Bezout coefficients.

The observed source names `gcd_balanced_bezout_exists`,
`coprime_balanced_bezout`, and `balanced_bezout_euclid_step` are possible
later dependency anchors, subject to the normal campaign replay and closure
checks. This RFC makes no fresh claim about their status.

## 7. Primitive-recursive and conservativity argument to be certified

At the design level, the selected operations are primitive recursive:

1. decode a code by parity and halving;
2. interpret the result as one nonzero magnitude at most;
3. perform natural additions and multiplications on positive and negative
   contributions;
4. normalize the resulting pair by natural comparison;
5. interleave the normalized sign and magnitude again.

This paragraph is a design argument, not an HA proof. Conservative admission
requires ordinary certificates for each totality and functionality theorem,
plus a checked expansion showing that every surface call becomes the exact
base formula in Section 4. No host `int`, subtraction, quotient, remainder,
bit operation, or pattern match enters the kernel.

## 8. Forbidden dependencies

The signed foundation must have neither direct nor transitive dependencies
on:

- `BetaAt`, `Product`, beta-prefix construction, or beta-coded folds;
- binary, finite, or generalized CRT;
- pair/list/map coding that is not already independently accepted;
- division or remainder merely to decide parity;
- classical `DNE`, excluded middle for arbitrary formulas, Markov's
  principle, choice, or quotient types;
- host integer correctness treated as a theorem.

Natural equality and order decision theorems are allowed only through their
explicit constructive HA certificates.

## 9. Staged acceptance tests

Passing an earlier stage does not imply public admission.

### Stage A — static representation lint

- Parse every Section 4 template in its exact parameter context with the
  ordinary base formula parser.
- Assert that the resulting AST uses only the frozen K0 constructors.
- Reject unknown/free variables and binder capture under adversarial actual
  arguments.
- Recompute and compare the UTF-8 template hashes in Section 4.9; a
  whitespace or parenthesization change requires a new freeze revision.
- Scan direct and transitive dependency metadata for every forbidden name in
  Section 8.
- Assert that no prospective definition calls another surface definition;
  the stored template itself must already be base-language text.

### Stage B — finite semantic oracle tests

Use bounded host evaluation only as an untrusted regression oracle.

- Check unique decoding for a documented initial interval.
- Pin the five fixtures in Section 3.
- Check that every sampled code has exactly one decoded pair.
- Check that `(0,0)` decodes only from code `0`.
- Check sampled `SignedBalance`, negation, addition, multiplication, and
  natural scaling against host integers.
- Include mixed-sign cancellation and zero-heavy cases.

These tests detect statement mistakes; they are not certificates.

### Stage C — dependency-curried candidate proofs

- Author the prerequisite parity-separation and even-half uniqueness bodies
  first.
- Replay each decoder theorem against explicit dependency hypotheses.
- Proceed in topological order through balance, negation, addition,
  multiplication, scaling, and the two Bezout bridges.
- Use the default intuitionistic checker and assert that no `DNE` node occurs.
- Reject nearby false mutations, including wrong decodings of codes `0`, `1`,
  and `2`, nonunique decoder parts, an incorrect signed sum, and a claimed
  negative-zero constructor.

Candidate-body success is not an admission receipt.

### Stage D — empty-context closure

- Close every candidate from the empty context with self-contained `Cut`
  sharing only.
- Run two cold deterministic passes.
- Record structural nodes, depth, distinct objects, edges, reused objects,
  cuts, and the content-stable certificate digest.
- Assert exact theorem statement hashes and the absence of external theorem
  authority in the final certificate.
- Re-run the transitive K0--K2 dependency audit on the closure recipe.

### Stage E — representation mutation audit

- Swap the parity orientation in one constructor and require downstream
  fixture failure.
- Permit an odd code with zero negative magnitude and require the
  no-negative-zero tests to fail.
- Remove one decoder branch and require totality closure to fail.
- Remove normalization from one arithmetic output and require functionality
  or canonical equality to fail.
- Replace literal code equality with unnormalized pair equality and require
  the extensional-equality tests to detect the drift.

### Stage F — deliberate public admission

Only after review of Stages A--E may the registry, definition freeze,
campaign manifest, catalog, book, vault, and explorer be changed. Admission
must include:

- exact definition records and hashes;
- theorem dependency and induction footprints;
- empty-context certificate receipts;
- human proofs explaining normalization and constructive case splits;
- generated-artifact checks; and
- a clean build from an empty cache.

### Stage G — independent/heavy validation

Replay the accepted roots with the independent checker or the campaign's
approved second-check route. Run resource, corruption, browser-memory, and
large closure checks on WMI when local gates have passed. Archive the exact
payload and environment receipts.

## 10. Exit criteria

The HA3/K3 signed-code gate is closed only when all of the following hold:

- the eight templates in Section 4 are registered or explicitly reduced to
  a smaller reviewed subset with the same semantics;
- decoding is total and functional for every natural code;
- no-negative-zero and literal canonical equality are certified;
- balance normalization is total and has a unique code;
- negate, add, multiply, and natural-scale graphs are total and functional;
- the minimum arithmetic laws in Section 6.4 are certified;
- both balanced-Bezout conversion directions are certified;
- the full dependency closure is K0--K2-only and contains no forbidden K3
  foundation; and
- all public-admission and independent validation receipts are recorded.

Until those conditions hold, the exact formulas in this RFC are a reviewed
design target only. In particular, this document must not be cited as a
proof that signed integers, signed arithmetic, or signed Bezout coefficients
have been admitted to the native HA library.
