# Polynomial degree descent and zero-or-monic right associates

This is a working-only, five-row prerequisite checkpoint. It uses the original
dependency-curried HA checker with exact declared premise types. It is not an
Alpha or Stable admission, a complete dependency-bundle verification, an
independent Lean check, or a completed polynomial gcd/Bézout theorem.

## Actual contracts

Polynomials are canonical natural-coefficient beta prefixes in highest-degree-first
order. Formal equivalence compares every power coefficient, including zero beyond
the declared length; it is not finite-field evaluation equality or equality of
raw beta codes. A represented degree requires a nonempty prefix with a genuinely
nonzero leading coefficient. The zero polynomial is handled by retained length
zero, without assigning it degree zero.

The exact first-order statements are in the candidate source and are compared
against separately expanded native contracts by the focused tests. The five rows
are:

1. `prime_field_polynomial_division_remainder_length_descent`: over
   `Prime(p)`, an actual existing division execution by a divisor of
   represented prefix length `S d` has retained remainder length
   `R ≤ d` and `R < S d`.
2. `prime_field_polynomial_division_constant_remainder_empty`: the
   same actual execution at `d = 0` has retained remainder length
   zero.
3. `prime_field_polynomial_scale_implies_right_divides`: an actual
   canonical scalar product `Scale(p,k,A,H,L)` over a prime field
   gives `RightDivides(A,H)`. The proof constructs a canonical
   singleton as a **left** quotient and a real left-constant convolution;
   it does not assume convolution commutativity.
4. `prime_field_polynomial_monic_normalization_right_associates`:
   actual monic normalization of `G` to `H`
   gives both `RightDivides(G,H)` and
   `RightDivides(H,G)`. The reverse direction uses the actual
   inverse/scale graph and the original inverse-scale theorem.
5. `prime_field_polynomial_normalized_right_associate_exists`:
   from `Prime(p)` and any canonical input `A`,
   construct actual codes and a length for `H` such that
   `Hlen = 0 ∨ Monic(H)` and the same mutual right-divisibility
   relations hold.

The fifth proof first constructs an actual trim. Its empty branch retains the
real empty prefix and constructs the needed zero products. Its nonempty branch
obtains a genuine represented degree, applies the existing monic-normalization
constructor, and transports the independently encoded divisor and target through
proved formal equivalences. The two output lengths are never silently identified.

`RightDivides(D,A)` is the unchanged conservative ND0342 graph:
the canonical target `A` is formally equivalent to an actual product
`Q*D` for genuinely witnessed quotient and product prefixes.
The new source contains a hygienic literal expansion, independently compared
with the original graph. No definition or public notation is added.

## Focused evidence

All **313 distinct focused cases** passed in six original-bounded windows:
228 independent source/contract/model cases, five actual HA bodies, and 80
hostile proof cases. Fresh collection reconciled the same 313 IDs and all 939
actual setup/call/teardown reports, with no skipped or duplicate credit.
The clean windows totalled 92.515921 seconds; the largest used 26.271848 seconds
and the maximum peak RSS was 106,168,320 bytes.

Every process retained CPU soft/hard 170/175 seconds, wall alarm 180 seconds,
RSS ceiling 1,536 MiB and proof depth 256. All 21 bound input paths and protected
module identities were unchanged before and after each window.

- Source: 16,401 bytes, SHA-256
  `d2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f`.
- Test: 29,037 bytes, SHA-256
  `e291538321e9d078a8b0044bacfb50d46b5eea59b2126001a2129c69de342791`.
- Five ordered specifications: 385 commands and 25 declared edges, digest
  `815b67478a8c42bd854002317e31ab5e77739551f19516dfc923b7fe66d0ce74`.
- Ordered 313 test IDs: SHA-256
  `caf0db764a508a9a65d6a77ffed1b8daae6d92d5705a06517130ee913c55c42d`.

The complete accounting is in
[conditional-verification-observations-v1.json](conditional-verification-observations-v1.json).

Every positive proof and each false/missing/truncated proof, removed or poisoned
declared edge, removed input clause, and false stronger conclusion uses the
unchanged original checker. The tests additionally construct native beta-coded
division, inverse, convolution, trim and associate witnesses, including
characteristic two, scalar zero, leading zeros, empty inputs and constant divisors.
No accepted-proof mock or saved receipt supplies mathematical authority.

The JSON observation is reproducibility/accounting data only. It preserves exact
test IDs, actual phases, command templates, resource outcomes and input pins; it
is never an input authorizing proof acceptance. The five exploratory singleton
body checks and the pre-metric pure repeat receive no additional unique-case
credit.

## Boundary and next use

The retained remainder length is a suitable strictly decreasing natural
measure for a future genuine Euclidean induction. The last row supplies the
zero-or-monic terminal associate and real left quotient witnesses. Backward
common-divisor/Bézout transport and the full induction must still be assembled
and checked separately. This checkpoint does not prove arbitrary
quotient/remainder uniqueness, normalized-gcd uniqueness, the gcd endpoint or
Bézout existence.

All old working archives, canonical mathematical providers, kernel, compiler,
runtime and resource ceilings are unchanged.

