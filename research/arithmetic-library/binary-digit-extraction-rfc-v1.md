# RFC: canonical beta-coded binary extraction and complete G102

Status: original-kernel constructive candidate over immutable Alpha v22;
neither Alpha v23-enrolled nor Stable until independently admitted.

The immutable Alpha-v22 parent separately proves formal `BitLen` totality and
functionality, genuine binary quotient/digit decomposition, relational powers
of two, beta-prefix extension, beta-coded Horner evaluation, canonical modular
power, and complete square-and-multiply execution **only for an externally
supplied valid digit prefix**. This campaign removes that last digit-supply
hypothesis for every arbitrary natural exponent. It also constructs a genuine
first-order operation count using the independently beta-coded population
count, and proves the precise campaign bound

```text
operations = 2 + 2*BitLen(exponent) + BitCount(canonical_digits)
operations <= 3*BitLen(exponent) + 2.
```

The zero convention is exact: `BitLen(0,1)` constructs the genuine single-bit
prefix `[0]`, one actual square transition, and an operation count of four.

No quotient, bit, list, beta, Horner, power, modular exponentiation, count,
complexity, or `BitLen` function/predicate is added to the language or kernel.
Each authoring relation below expands completely and hygienically into the
unchanged first-order Heyting-arithmetic language `0, S, +, *, =`; ordinary
natural induction is the only induction principle used.

## Conservative definition DAG

The four new public authoring surfaces have the following exact conceptual
dependencies and first-order expansions; every arrow references an already
reviewed conservative relation, not a new axiom or primitive:

```text
BitLen ─────────────────┐
BinaryDigitPrefix ──────┼── ExponentDigitCode ── CanonicalExponentDigitCode ──┐
Horner(base=2) ─────────┘                      ▲                           │
                                               └──────────── BitLen ───────┤
BinaryModularExecution ────────────────────────────────────────────────────┼── CompleteModularExecution
BinaryModularPower ────────────────────────────────────────────────────────┘
BitCount ─────────────────────────────── BinaryExecutionOperationCount
```

1. `binary_exponent_digit_code(exponent,length,code,scale,*,tag)` expands to

   ```text
   BinaryDigitPrefix(code,scale,length)
   ∧ Horner(code,scale,2,length,exponent).
   ```

   Definition dependencies: `BinaryDigitPrefix`, `Horner`.

2. `binary_canonical_exponent_digit_code(exponent,length,code,scale,*,tag)`
   expands to

   ```text
   BitLen(exponent,length)
   ∧ ExponentDigitCode(exponent,length,code,scale).
   ```

   Definition dependencies: `BitLen`, `ExponentDigitCode`.

3. `binary_complete_modular_execution(exponent,base,modulus,length,code,scale,
   result,*,tag)` expands to

   ```text
   CanonicalExponentDigitCode(exponent,length,code,scale)
   ∧ BinaryModularExecution(code,scale,base,modulus,length,result)
   ∧ BinaryModularPower(base,exponent,modulus,result).
   ```

   Definition dependencies: `CanonicalExponentDigitCode`,
   `BinaryModularExecution`, `BinaryModularPower`.

4. `binary_execution_operation_count(code,scale,length,operations,*,tag)`
   expands to

   ```text
   ∃ ones.
     BitCount(code,scale,length,ones)
     ∧ operations = (2 + (length + length)) + ones.
   ```

   Definition dependency: `BitCount`.

The helpers validate distinct, non-reserved first-order variables, reject
generated-binder collisions, validate binder tags, and produce
alpha-equivalent formulas independently of the chosen tag.

## Constructive proof architecture

First, `beta_prefix_extend` appends a genuine final bit while preserving every
old decoded entry. Two transport proofs preserve both the zero/one invariant
and an independently witnessed base-two Horner trace across this recoding.
The Horner successor decomposition and functionality then prove that appending
bit `d` to the representation of `h` represents exactly `2*h+d`.

Next, ordinary induction on `l` proves the stronger uniform statement

```text
PowTwo(l,p) → n < p →
  ∃ code scale.
    BinaryDigitPrefix(code,scale,l)
    ∧ Horner(code,scale,2,l,n).
```

The inductive step extracts the actual quotient and bit `n=2*h+d`, uses the
constructive inequality `n<2*p → h<p`, invokes the inductive hypothesis at
`h`, and appends the genuine beta-coded bit. The base case obtains `n=0` from
`n<2^0=1` and supplies an actual empty Horner trace.

Every Alpha-v22 `BitLen(n,l)` witness, including the explicit zero case,
supplies a genuine upper power `p=2^l` and the strict inequality `n<p`.
Consequently the bounded induction supplies an actual beta-coded binary digit
prefix of **exactly the canonical bit length** for every arbitrary exponent.

The existing Alpha-v22 execution theorem now builds a complete real beta-coded
square-and-multiply history from those constructed digits. Existing Horner
correctness identifies its terminal residue with the canonical modular power
of the original exponent. Canonical modular-power functionality proves the
result independent even of which admissible beta encoding was constructed.

Finally, the universal binary-digit invariant supplies actual decoded `AllBits`
witnesses. Existing `BitCount` totality and boundedness construct the exact
number of one bits and prove it at most the digit length. Adding two
initializations and two operations for each digit, then normalizing Peano
arithmetic, gives the genuine first-order bound
`operations ≤ 3*BitLen(exponent)+2`.

Thus the concluding root jointly proves actual arbitrary-exponent canonical
digit extraction, genuine complete modular execution, canonical power
correctness, exact beta-counted operations, and the logarithmic bound.

## Exact original-kernel theorem inventory

The dependency-ordered candidate contains exactly **24 distinct constructive
theorems**, **63 direct declared proof-dependency edges**, and **812 authored
tactic commands**:

1. `binary_digit_code_recode_exists` — append one actual decoded beta entry.
2. `binary_digit_prefix_recode` — transport the binary-digit invariant.
3. `binary_horner_prefix_recode` — transport a real Horner trace.
4. `binary_digit_prefix_append` — append a genuine zero-or-one digit.
5. `binary_digit_horner_append` — prove exact value `2*h+d` after appending.
6. `binary_digit_half_below_double` — prove `2*h+d<2*p → h<p`.
7. `binary_digit_bounded_prefix_exists` — represent every `n<2^l` in `l` bits.
8. `binary_length_upper_power_bound` — extract `n<2^l` from `BitLen(n,l)`.
9. `binary_exponent_digit_prefix_at_length` — construct the exact-length code.
10. `binary_exponent_digit_prefix_exists` — construct canonical digits for
    **every arbitrary natural exponent**.
11. `binary_exponent_digit_prefix_value_functional` — the represented value
    of a fixed digit code is unique.
12. `binary_canonical_exponent_length_functional` — canonical representations
    of one exponent have equal length.
13. `binary_digit_prefix_all_bits` — provide genuine `AllBits` witnesses.
14. `binary_digit_prefix_bit_count_exists` — construct the exact population
    count in the unchanged first-order language.
15. `binary_three_times_cost_normalization` — prove the exact Peano equality
    `(2+(l+l))+l = 3*l+2`.
16. `binary_digit_operation_count_exists` — construct the actual counted cost.
17. `binary_digit_operation_count_functional` — prove cost uniqueness.
18. `binary_digit_operation_count_bound` — prove the cost bound for any
    genuine binary prefix.
19. `binary_modular_exponent_coded_execution_power_correct` — identify the
    actual terminal residue with the supplied arbitrary exponent's power.
20. `binary_modular_exponent_coded_execution_exists` — construct exact digits,
    complete beta-coded execution, and the correct modular power together.
21. `binary_modular_exponent_coded_execution_result_functional` — prove the
    result independent even of the selected canonical digit code.
22. `binary_modular_exponent_coded_execution_exists_unique` — prove existence
    and uniqueness of that actual execution result.
23. `binary_modular_execution_bitlength_bound` — prove the genuine counted
    operation bound for every complete execution.
24. `binary_modular_execution_logarithmic_bound` — jointly construct and prove
    the complete arbitrary-exponent G102 milestone.

Exact ordered-name SHA-256:

`dfca399b15ba72e14afa2beee595acd8dbb925030f6b53e16c2c0bc075412253`.

Frozen endpoint statement identities:

| Original-kernel theorem | Statement SHA-256 |
|---|---|
| `binary_digit_bounded_prefix_exists` | `70d6bec43aaf800d0915f268b3d90c60274e28a20bb5d7e46dbf384c41df637b` |
| `binary_exponent_digit_prefix_exists` | `32bdeec52d9746fee467a709ae2315e25800e4f0603fe465c14fa84f03452f0d` |
| `binary_digit_operation_count_bound` | `bfa38c8809cf8abe8209ff27e2e136972707db9889de8be549d90f01eb3ffa56` |
| `binary_modular_exponent_coded_execution_exists` | `d2c7995fed0f8265109081af92313d7a0ff7bd740a238c578b2a06522f016a3a` |
| `binary_modular_exponent_coded_execution_exists_unique` | `3b7d9957844c9972de1f2a4cea63b355134d634dab471fc1ad31a89b3e509bfc` |
| `binary_modular_execution_bitlength_bound` | `f26f699912b4f5feb522f8afe77676b881747f5a997fa169d27e924c6f7acb73` |
| `binary_modular_execution_logarithmic_bound` | `3ac6949afecc26acc6e5fb9d8d9041be9a9f2b8120dcbc918b8e771a7a1bd27d` |

## Executable examples and admission boundary

Bounded executable examples actually construct canonical MSB-first digits,
verify their base-two Horner value, run every square-and-multiply transition,
and count the initializations, squares, and optional multiplies precisely.
Small examples additionally CRT-encode the digits as an actual Gödel-beta
pair and independently decode every position.

General exponent and digit histories are capped at **4,096 bits**. Concrete
CRT encodings are separately capped at **128 entries** and **65,536 code
bits**. Invalid booleans, negative inputs, oversized values, nonbinary or
altered digits, forged beta metadata, changed transitions, forged terminal
residues, changed population counts, and changed operation counts fail closed.

These executable checks are never theorem authority. Every exact
dependency-curried body must pass the unchanged original intuitionistic
kernel; all external dependencies must belong to immutable checked Alpha v22;
and independent v23 admission, transitive proof closure, immutable evidence,
and Lean verification remain separate mandatory release decisions.
