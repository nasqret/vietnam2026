# Jordan prime-power and distinct-prime formula: source-only route

This is prospective proof planning, not a checked theorem, definition of
Jordan, or admission record. The independently defined Jordan75 tuple-count
relation and its verified multiplicativity bundle remain unchanged. The new
count10 and arbitrary-witness wrapper still require native verification and
an extended complete bundle.

## Natural-number contract

Use a successor exponent instead of subtraction. A suitable prime-power
target is

    Prime(p), k != 0,
    Pow(p,h,A), Pow(p,S h,N), Pow(A,k,U), Pow(N,k,W), Jordan(k,N,j)
      -> j + U = W.

Here every `Pow` is the existing actual beta-chain power relation, not a new
function symbol. This says J_k(p^(h+1)) + p^(hk) = p^((h+1)k).
After the appropriate natural power laws and predecessor witness for p^k,
it gives J_k(p^(h+1)) = p^(hk)(p^k-1). It does not put that equation inside
the Jordan definition or assume a count as a premise beyond actual Jordan.

## Existing source-supported ingredients

- `theorems.py`, `prime_divisor_exists`: every nonzero nonunit natural has
  an actual prime divisor. `prime_divisor_eq_one_or_self` handles exponent one.
- `prime_valuation_support_candidate.py`,
  `prime_divisor_of_prime_power`: a prime divisor q of an actual power of
  prime p equals p. `pow_positive_exponent_base_divides` supplies p | p^(S h).
- Jordan75 `jordan_tuple_all_divisible_decidable` (the existing finite
  coordinate divisibility decision), actual beta prefix extension, tuple
  equality, and primitive-tuple enumeration constructors supply the relevant
  local coding vocabulary. These references are source evidence, not a new
  checked dependency-closed formula proof.
- `euler_totient_product_candidate.py`,
  `totient_pairwise_coprime_product_fold`, is an existing induction template
  over actual beta products. Its theorem concerns Euler's scalar totient;
  it cannot be applied as a Jordan tuple-count theorem.
- That same source's `totient_prime_support_powers_pairwise_coprime` uses
  `coprime_powers` and `distinct_primes_coprime` to obtain coprimality of
  genuinely distinct prime-power entries. Existing prime-exponent support
  supplies actual nonzero moduli and positive exponents.

The prime-power primitive characterization is constructive: primitive implies
not all coordinates divisible by p, since p divides the modulus and p != 1.
Conversely, given a common divisor d, decide d=1. If not, its divisibility of
the nonzero prime power implies d != 0, hence it has a prime divisor q.
Transitivity gives q | p^(S h), so q=p, contradicting that not all coordinates
are divisible by p. This argument does not negate an unbounded universal to
extract a witness.

## Missing actual count bridge

1. Construct an exact, duplicate-free enumeration of all canonical width-k
   tuples with entries below N, with length witnessed by Pow(N,k,W).
   An actual index x<W, not an arbitrary beta code, is the carrier. A
   width-k radix expansion must include leading zeros; arbitrary inner and
   outer beta presentations remain nonunique.
2. Prove actual coordinate scaling by p bijects the width-k A-box with the
   all-p-divisible tuples in the N-box, where N=p*A. Construct the quotient
   tuple using the original division/finite beta extension mechanisms.
3. Partition the N-box into divisible and nondivisible tuples using the
   already decidable finite divisibility predicate. Construct both lists and
   a disjoint coverage/injectivity argument. Cardinalities must come from
   real lists/maps, not from declaring the desired subtraction result.
4. Identify the second list with the actual primitive-tuple enumeration by
   the characterization above. Use checked count uniqueness only after its
   ordinary body and complete extension have passed.

Jordan's existing finite representative-code sweep proves totality but gives
no exact N^k length. Similarly, `lucas_multidigit_candidate.py` has actual
digit chains, not by itself the fixed-width x<N^k bijection. That radix bridge
also appears useful for the separate G091 field-cardinality task; no shared
implementation or ownership is assumed here.

## Distinct-prime product

First prove Jordan(k,1,1) for k>0 by the actual singleton all-zero tuple list;
this is the empty-factor-product case, not an inference from multiplicativity
alone. Then fold the checked arbitrary-witness multiplicativity law over
actual pairwise-coprime prime-power factors. Construct the factor-count
sequence and its actual beta product. An injective prime support list must
not count a repeated prime twice.

The resulting natural factor product is the formal target. The familiar
rational expression n^k product_(p|n)(1-p^(-k)) is a mathematical restatement,
not a new HA primitive or substitute for the actual count proof.

## Boundary checks

Prime p, positive exponent, and positive order are essential. A composite
base need not characterize primitivity by one common divisibility test.
Exponent zero gives modulus one and needs the separate singleton argument.
Width zero is a valid radix carrier but is excluded by the Jordan relation.
Coordinatewise units are not the primitive tuple condition. Raw code equality
and equality of finite-field evaluations are not tuple equality.

`test_jordan_prime_power_models.py` tests actual finite tuples and beta
encodings against this route. Its passing cases are model evidence only.
