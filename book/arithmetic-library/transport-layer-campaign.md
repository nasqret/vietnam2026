# Binary length, Euclidean gcd transport, and coded binary executions

Historical immutable **Alpha v22** extends the fully checked **1,830-theorem Alpha-v21
parent** by exactly **60 new independently checked theorems**: **21 binary
length**, **20 Euclidean gcd transport**, and **19 binary modular execution**.
All **1,890 enrolled theorems** have checked-use authority: **432 unchanged
Stable** and **1,458 Alpha-only**, with **6,128 exact proof-dependency edges**
and **53 dependency-first layers**. The proof kernel, first-order signature,
and every historical theorem remain unchanged. Its mathematical purpose is
to replace externally computed algorithm intuitions with actual arithmetic
relations and independently checked induction proofs.

Historical immutable **Alpha v23** preserves this complete 1,890-row historical
snapshot and adds **59 independently checked theorems**, closing all of G101,
G102, and G025. Its **1,949 checked-use rows** include 432 unchanged Stable
results and 1,517 Alpha-only results. The v22 definitions and proofs below
retain their exact first-enrollment provenance; subsequent v23 closes the
previously missing logarithmic bounds and arbitrary-exponent digit construction.

## A genuine first-order binary length

`PowTwo(e,p)` is simply the existing conservative relation `Pow(2,e,p)`.
`BitLen(n,ell)` means exactly

```text
(n = 0 and ell = 1)
or
(n > 0 and there are e, lower, upper with
    ell = e + 1,
    PowTwo(e, lower),
    PowTwo(ell, upper),
    lower <= n,
    n < upper).
```

The zero convention is deliberate: zero has one displayed binary digit.
Twenty-one original-kernel proofs establish exact binary quotient/digit
existence and uniqueness, total and functional powers of two, strict and
monotone power growth, the successor construction for binary-length
witnesses, totality and functionality of `BitLen`, unique binary-length
existence, and the exact length of each power of two.

The major checked roots are:

```text
binary_length_exists
binary_length_functional
binary_length_exists_unique
binary_length_power_exact
```

The ordinary proof of `binary_length_exists` uses induction over natural
numbers. No Python `bit_length`, builtin exponentiation term, classical
excluded middle, or untrusted trace is admitted as proof evidence.

## Actual Euclidean terminal-state identification

Historical Alpha v21 established a genuine beta-coded Euclidean execution
history and separately witnessed a relational gcd. It did not prove that the
terminal state of the former was the value of the latter.

Twenty new constructive theorems close exactly that gap:

1. Divisibility and common divisors transport forward and backward through
   every Euclidean remainder step.
2. The full relational gcd predicate is preserved across such steps.
3. Beta decoding and packed-state injectivity make each history state unique.
4. First-order induction transports the gcd invariant through every actual
   encoded history transition.
5. The zero-remainder terminal state is identified with the unique relational
   gcd witness.
6. The strengthened `EuclideanAnchoredExecution(a,b,g,k)` relation records
   the complete actual history, its terminal state `(g,0)`, and the proved
   gcd condition.

Its decisive checked roots are

```text
euclidean_trace_prefix_gcd_invariant
euclidean_execution_terminal_identified
euclidean_anchored_execution_linear_bound
```

This historical v22 result proves the bound `k <= b`. Subsequent Alpha v23
derives `k <= 2*BitLen(b)+1` by a separate checked induction over the already
proved two-step halving theorem, genuinely closing the complete G101 target.

## Beta-coded repeated-squaring execution

`BinaryDigitPrefix(d,s,n)` validates each digit of an actual finite beta-coded
prefix. `BinaryExecutionTrace(d,s,a,m,n,h,t)` asserts a genuine encoded
accumulator history beginning at one and satisfying the checked
square-or-square-and-multiply transition at every index.

`BinaryModularExecution(d,s,a,m,n,r)` connects that actual history to its
decoded terminal accumulator. `BinaryExecutionPowerInvariant` separately
expresses the base-two Horner value of the supplied digit prefix together with
its canonical modular power.

Nineteen checked theorems construct the supplied-digit trace, prove its
terminal existence and functionality, and establish the exact modular
transition/power invariants by ordinary constructive induction.
Their major genuinely proved roots are:

```text
binary_execution_prefix_exists
binary_modular_execution_exists
binary_modular_execution_power_correct
binary_modular_execution_horner_exists
binary_modular_execution_result_exists_unique
```

At the historical v22 checkpoint, the full G102 statement remained open.
Subsequent Alpha v23 connects every arbitrary exponent to its complete
canonical digit code, proves actual modular execution, and derives the exact
`operations <= 3*BitLen(e)+2` logarithmic bound, closing G102 completely.

## Hygienic shared definitions

The transport layer adds ten reviewed, conservative definitions:

| Identifier | Definition | Direct reviewed dependencies |
|---|---|---|
| `ND0028` | `PowTwo` | `Pow` |
| `ND0029` | `BinaryDigit` | `BinaryExponentSplit` |
| `ND0030` | `BitLen` | `PowTwo`, `Le`, `Lt` |
| `ND0031` | `EuclideanCommonDivisor` | `Dvd` |
| `ND0032` | `EuclideanStateAt` | `Beta` |
| `ND0033` | `EuclideanAnchoredExecution` | `ContinuedFractionTrace`, `EuclideanStateAt`, `IsGCD` |
| `ND0034` | `BinaryDigitPrefix` | `Beta`, `Lt` |
| `ND0035` | `BinaryExecutionTrace` | `Beta`, `Lt`, `BinaryModularStep` |
| `ND0036` | `BinaryModularExecution` | `BinaryExecutionTrace`, `Beta` |
| `ND0037` | `BinaryExecutionPowerInvariant` | `Horner`, `BinaryModularPower` |

Every expansion is parsed directly into the original formula language and
audited for exact argument arity, freshness, dependency order, and historical
identity preservation. Definition arrows are notation prerequisites, never
theorem-proof dependencies.

The historical v22 research vocabulary contained **141 blueprint terms**,
**88 definition-to-definition prerequisites**, **311 lexical statement
uses**, and **41 separately declared notation references**: **352 total
milestone-to-notation edges** across five dependency-first layers.
Its expansion-checked registry contained **89 reviewed conservative
definitions**, **142 exact reviewed definition edges**, and **50 compatible
blueprint matches**. Historical Alpha v23 extended the same graph to **152
blueprint terms**, **97 reviewed definitions**, **159 exact reviewed
definition edges**, and **61 compatible blueprint matches**: **57 exact
names** and **four explicitly reviewed aliases**. All preceding
`ND0001`–`ND0037` objects retain their identities and
unchanged expanded formulas. Inspect the exact
[global definition dependency DAG](../_static/constructive-grand-campaign/definitions.json),
the <a href="../_static/constructive-grand-campaign/index.html?view=goal&amp;focus=G101">completely closed G101 milestone</a>,
or the <a href="../_static/constructive-grand-campaign/index.html?view=goal&amp;focus=G102">completely closed G102 milestone</a>.

## Honest remaining obligations

- **G101:** completely proved in Alpha v23, including the formal logarithmic
  Euclidean step bound and identification of the actual terminal gcd.
- **G102:** completely proved in Alpha v23, including arbitrary-exponent
  canonical digit encoding and the exact formal logarithmic execution bound.
- **G025:** completely proved in Alpha v23, establishing infinitely many
  primes congruent to three modulo four.
- **T13:** Alpha v27 closes arbitrary-dimensional recursive determinants,
  rectangular rank, integer-span closure, and positive determinant data.
  Determinant multiplicativity, lattice index, independent bases, and
  lattice-reduction theorems remain separate open goals.

Thus historical v22 supplied actual object-language binary length, actual
terminal gcd transport, and actual supplied-digit execution histories, while
historical v23 genuinely closed their full algorithmic milestones and proves a
new prime-distribution theorem. Alpha v27 later closed T13's exact finite
substrate without claiming its stronger lattice successors.

## Independent proof certificate

The complete ordinary intuitionistic proof bundle contains **239 real theorem
nodes**, **one synthetic packaging root**, **597 exact proof edges**, and
**11,848 structural proof nodes**. Its **1,099,541 bytes** have SHA-256
`95e5f8a3baef113721d748f9d7071864b4bf9511737a27a1272d2695428fb938`.
Every one of its **240 proof bodies** is checked by the original kernel and
independently accepted by the separately compiled Lean verifier. The synthetic
root is packaging only and never becomes an enrolled arithmetic theorem.

```text
Bundle: research/arithmetic-library/artifacts/alpha-v22-transport-layer-proof-bundle-v1.json
Bytes: 1,099,541
SHA-256: 95e5f8a3baef113721d748f9d7071864b4bf9511737a27a1272d2695428fb938

Historical v22 channels: artifacts/peano-library/channels-v22.json
Catalog SHA-256: fd0e385e3d0c2d614bfa2754a2c3b70939b9437076ec53501082ddfb5bf9ae22
Enrollment SHA-256: 431f7300f9190f6fdc35ef84212e93701f2bb565b7e32c1624b7ae0c89cfc5ea
Edition SHA-256: 2750384264856ad10910c1e9369746da886f4760d41e356bfc9e7f8f4563c7db

Historical v23 channels: artifacts/peano-library/channels-v23.json
Historical v23 catalog SHA-256: 818da349674b1ef33c17fa85b2e9a0a6653370046d88e7814300297f7bc7f4d2
Historical v23 enrollment SHA-256: f5d94af7a11c642d7076a195e2e795e7b84c61a6de1a6b074708669b2dac1648
Current edition SHA-256: 02059eef420eb96abd48c41bf62049a3cc69f025b00bed9dc3466e7eb2294a85
```

The exact frozen Alpha-v21 parent remains independently reproducible.
Definition notation, host-side example certificates, and artifact hashes
organize review; only real original-kernel checking gives a theorem its
Alpha checked-use authority, and none of these results is promoted to Stable.
