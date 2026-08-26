# G102 — constructive binary modular exponentiation, first certified layer

Status: **sixteen actual, independently kernel-checked dependency-curried
theorems** above immutable Alpha v20, plus a bounded, independently checkable
square-and-multiply implementation and actual finite Gödel-beta execution
encodings. These isolated candidates do not alter v20, do not confer Alpha or
Stable authority, and do not change the first-order parser or intuitionistic
kernel.

The complete grand-campaign milestone **G102 remains open**. This document
does not confuse a checked theorem about the unique result, a checked theorem
about each binary transition, or a host-language execution example with an
object-level proof of an arbitrary complete execution and its logarithmic
complexity bound.

Implementation:

```text
peano-lab/py/peano_lab/library/binary_modular_exponentiation_candidate.py
peano-lab/py/tests/test_binary_modular_exponentiation_candidate.py
```

## Conservative mathematical definitions

All displayed names below are authoring abbreviations. Every occurrence is
expanded hygienically before the unchanged kernel sees a formula. The trusted
language remains exactly `{0, S, +, *, =}` with first-order quantifiers and
intuitionistic logical connectives.

```text
BinaryModulus(m) := ∃g. g + S(1) = m.

ModEq(m,x,r) := ∃u v. x + m*u = r + m*v.

CanonicalResidue(m,x,r) :=
  (∃g. g + S(r) = m) ∧ ModEq(m,x,r).

BinarySplit(e,h,b) :=
  (b = 0 ∨ b = 1) ∧ e = (h+h)+b.

DoubledPower(a,h,e,x,y) :=
  e = h+h ∧ Pow(a,h,x) ∧ Pow(a,e,y).

OddPower(a,h,e,x,z) :=
  e = S(h+h) ∧ Pow(a,h,x) ∧ Pow(a,e,z).

BinaryStep(m,x,a,b,r) :=
  (b = 0 ∧ CanonicalResidue(m,x*x,r)) ∨
  (b = 1 ∧ CanonicalResidue(m,(x*x)*a,r)).

BinaryModularPower(a,e,m,r) :=
  ∃p. Pow(a,e,p) ∧ CanonicalResidue(m,p,r).
```

`Pow` is the previously admitted beta-coded finite-product relation, not a
new exponentiation function or term former. The constructor
`binary_modulus_relation` proves exactly `m>1`; it never weakens the actual
grand-campaign precondition to `m≠0`, `m>0`, or a prime-modulus assumption.

The seven public definition builders are

```text
binary_modulus_relation(m, *, tag)
binary_exponent_split(e,h,b, *, tag)
canonical_modular_residue(m,x,r, *, tag)
binary_doubled_power(a,h,e,x,y, *, tag)
binary_odd_power(a,h,e,x,z, *, tag)
binary_modular_step(m,x,a,b,r, *, tag)
binary_modular_power(a,e,m,r, *, tag).
```

Each accepts identifiers only, checks tags, prevents generated-binder
capture, and produces alpha-equivalent formulas for different safe tags.
Compound terms such as `x*x` and `(x*x)*a` are constructed solely by the
reviewed implementation; arbitrary caller term interpolation is rejected.

The definition DAG is

```text
                              first-order HA
                             /      |       \
                      BinaryModulus ModEq   beta-coded Pow
                             |       |          |
                             |  CanonicalResidue|
                             |    /     |       |
                             | BinaryStep  BinaryModularPower
                             |               |
                             +-------- exact unique residue

               BinarySplit → DoubledPower / OddPower → BinaryStep
```

Arrows describe reusable mathematical structure; they are not theorem
admission edges and do not silently manufacture object-level execution
witnesses.

## Exact proved endpoint

The final theorem
`binary_modular_exponentiation_result_exists_unique` has the exact
constructive surface meaning

```text
∀a e m.
  BinaryModulus(m) →
  ∃r.
    BinaryModularPower(a,e,m,r) ∧
    ∀s. BinaryModularPower(a,e,m,s) → r=s.
```

Consequently every natural `a,e` and every `m>1` have exactly one actual
result `r<m` congruent to the witnessed relational power `a^e`. Its
fully expanded statement SHA-256 is

```text
7b9895f8ad3956c33e9fb06ea8040113f17f272be5e97d942ca71aed2a88f136.
```

Existence first invokes the existing checked totality theorem `pow_exists`,
then constructive Euclidean division to obtain an actual bounded residue.
Uniqueness invokes existing `pow_functional`, transports the witnessed power
equality, and applies bounded congruence uniqueness.

This is an exact mathematical result about modular powers, but it does **not**
yet assert `Execution(BinaryPow,...)` or any complexity estimate.

## Proved square-and-multiply infrastructure

The separate binary-exponent theorem establishes

```text
∀e. ∃h b. (b=0 ∨ b=1) ∧ e=(h+h)+b.
```

It uses the already checked constructive parity theorem and the exact identity
`2*h=h+h`. There is no implicit `div`, `%`, machine-int oracle, or
excluded-middle assumption.

The exact even and odd algebraic branches are independently checked:

```text
e=h+h, Pow(a,h,x), Pow(a,e,y)     ⟹ y=x*x
e=S(h+h), Pow(a,h,x), Pow(a,e,z) ⟹ z=(x*x)*a.
```

Existing relational power addition proves the even case. The odd case first
constructs the actual even power, invokes the even theorem, and uses the
already checked successor-power multiplication theorem.

Two additional original-kernel proofs establish preservation of balanced
congruence under squaring and simultaneous multiplication. The guarded
square-and-multiply transition has both a totality proof and a functionality
proof:

```text
m>1, b∈{0,1} ⟹ ∃r. BinaryStep(m,x,a,b,r)

BinaryStep(m,x,a,b,r), BinaryStep(m,x,a,b,s) ⟹ r=s.
```

Contradictory zero/one branches are rejected constructively by the ordinary
successor-not-zero axiom; equal branches reduce to the proven uniqueness of
canonical residues.

## Actual checked proof-body ledger

| Exact theorem | Commands | Kernel proof nodes | Depth |
| --- | ---: | ---: | ---: |
| `binary_modulus_nontrivial_nonzero` | 13 | 17 | 11 |
| `binary_canonical_residue_exists` | 32 | 39 | 17 |
| `binary_canonical_residue_functional` | 29 | 36 | 17 |
| `binary_canonical_residue_exists_unique` | 21 | 25 | 17 |
| `binary_exponent_split_exists` | 24 | 37 | 16 |
| `binary_exponent_doubled_power` | 20 | 60 | 34 |
| `binary_exponent_odd_power` | 40 | 45 | 20 |
| `binary_modular_square_congruence` | 12 | 30 | 18 |
| `binary_modular_multiply_congruence` | 15 | 33 | 21 |
| `binary_modular_square_residue_exists` | 7 | 15 | 10 |
| `binary_modular_multiply_residue_exists` | 8 | 16 | 11 |
| `binary_modular_step_exists` | 29 | 31 | 13 |
| `binary_modular_step_functional` | 41 | 127 | 30 |
| `binary_modular_exponentiation_result_exists` | 18 | 21 | 12 |
| `binary_modular_exponentiation_result_functional` | 27 | 37 | 21 |
| `binary_modular_exponentiation_result_exists_unique` | 24 | 28 | 19 |

The tranche contains exactly **16 genuinely checked theorem bodies**, **29
direct dependency edges**, **360 primitive tactic commands**, and **597
original-kernel proof-body nodes**. Its maximum single body has **127 nodes**
and maximum proof depth is **34**. The ordered-name SHA-256 is

```text
b8165f5d62afded3312f199aa52c0a105e46943a47a2affe9835ee35e7507db8.
```

The entire existing Alpha-v20 external prerequisite set is

```text
add_eq_zero_right
division_remainder_exists
mod_eq_bounded_unique
mod_eq_mul
mod_eq_symm
mod_eq_trans
mul_comm
parity_cases
pow_add
pow_exists
pow_functional
pow_successor_pair_mul
remainder_decomposition_to_mod_eq
succ_ne_zero
two_mul_eq_add_self.
```

Every direct dependency is either one of these independently checked existing
theorems or a strictly earlier row in the displayed ledger. No candidate uses
`DNE`, a classical principle, an admitted axiom, or an unregistered theorem.

## Bounded executable algorithm and real beta-coded examples

`execute_binary_modular_exponentiation(a,e,m)` computes the ordinary
most-significant-bit-first square-and-multiply algorithm:

```text
base_residue := a mod m
accumulator  := 1 mod m

for every exponent bit, from most significant to least:
  squared := accumulator*accumulator mod m
  accumulator := squared*base_residue mod m if bit=1 else squared.
```

For each actual step it records its index, bit, decoded exponent prefix,
previous accumulator, square residue, and resulting residue. The explicit
resource caps are

```text
base width                 ≤ 16,384 bits
exponent width             ≤  4,096 bits
modulus width              ≤  4,096 bits
optional beta entries      ≤    128 naturals
each encoded beta entry    ≤    256 bits
complete optional beta code≤ 65,536 bits.
```

`BitLen(0)` is exactly `1`, as required by the blueprint; the zero exponent
needs no loop iteration. Each input normalization costs one operation, each
bit consumes two operations, and a set bit costs one extra multiplication:

```text
operations = 2 + 2*e.bit_length() + e.bit_count()
           ≤ 3*max(1,e.bit_length()) + 2.
```

This step bound is a true assertion about the bounded executable example. It
is **not yet an object-level Heyting-arithmetic theorem**.

`encode_binary_modular_execution` additionally creates actual Gödel-beta
codes for sufficiently small executions. It flattens the result metadata and
all transition fields into a finite sequence, chooses a witnessed common
scale divisible by the factorial of its length, and constructs the unique
canonical Chinese-remainder representative incrementally. The resulting
certificate satisfies exactly

```text
code mod (1+(i+1)*scale) = entry[i]
```

for every represented coordinate. The implementation rejects excessive trace
length, entry width, or projected code width **before** constructing oversized
Chinese-remainder witnesses.

Both execution and beta-code verifiers reject malformed dataclasses, booleans
masquerading as naturals, changed input/output fields, omitted/reordered/
duplicated/forged transitions, invalid residues, altered operation counts,
out-of-policy resource usage, forged CRT code/scale/entries, and mismatched
execution receipts.

## Exact remaining work before G102 can be closed

1. Add a hygienic object-level definition of `BitLen(e,l)` covering both
   `e=0,l=1` and the positive power-of-two bracket, and prove its totality and
   uniqueness using existing relational `Pow`.
2. Define one complete beta-coded state/step history carrying the actual
   prefix, accumulator, bit, modular square, and optional multiplication.
3. Prove arbitrary trace construction and preservation by induction over the
   actual binary-digit length, using the checked transition-totality and
   functionality theorems from this tranche.
4. Prove the full correctness invariant connecting each decoded prefix to the
   relational power and its unique canonical residue.
5. Prove in HA the exact operation counter and
   `steps ≤ 3*BitLen(e)+2`, then produce the complete empty-context release
   certificate for the precise blueprint `Execution(BinaryPow,...)` goal.

Until all five are genuine independently checked object-level theorems,
**G102 must remain open**, regardless of successful host examples, finite
beta-coded traces, or any later separate promotion of the sixteen prerequisite
theorems.
