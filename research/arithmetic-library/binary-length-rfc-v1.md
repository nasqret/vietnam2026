# RFC: constructive binary-length foundation, v1

## Scope and conservative vocabulary

This candidate family stays entirely inside the original first-order
Heyting-arithmetic language and the original proof kernel. It adds no axiom,
primitive term former, classical principle, or trusted computational oracle.

- `PowTwo(e,p)` expands to the existing beta-coded relation `Pow(2,e,p)`.
- `BinaryDigit(n,h,b)` expands to
  `(b = 0 ∨ b = 1) ∧ n = (h + h) + b`, exactly the existing binary-exponent
  split relation.
- `BitLen(n,l)` expands to

  ```text
  (n = 0 ∧ l = 1)
  ∨ ∃ e p q.
      l = S e
      ∧ 1 ≤ n
      ∧ PowTwo(e,p)
      ∧ PowTwo(l,q)
      ∧ p ≤ n
      ∧ n < q.
  ```

  Both orders are their existing existential-additive encodings. The zero
  convention is **`BitLen(0,1)`**, as required by the pre-existing campaign
  blueprint; zero is represented by its one displayed binary digit.

All public authoring helpers accept only safe Peano identifiers, reject
capture by generated power/length binders, and return fully expanded formulas.

## Dependency-ordered theorem ladder

The frozen factory `make_binary_length_candidate_theorems` produces exactly:

1. `binary_length_digit_bounded`
2. `binary_length_digit_split_exists`
3. `binary_length_digit_split_functional`
4. `binary_length_digit_split_exists_unique`
5. `binary_power_two_exists`
6. `binary_power_two_functional`
7. `binary_power_two_zero_value`
8. `binary_power_two_nonzero`
9. `binary_power_two_successor_double`
10. `binary_power_two_strict_growth`
11. `binary_power_two_exponent_monotone`
12. `binary_power_two_exponent_strict`
13. `binary_length_zero`
14. `binary_length_one`
15. `binary_length_zero_input_value`
16. `binary_length_successor_step`
17. `binary_length_exists`
18. `binary_length_zero_input_general`
19. `binary_length_functional`
20. `binary_length_exists_unique`
21. `binary_length_power_exact`

The main constructive result is the full first-order theorem

```text
∀ n. ∃ l. BitLen(n,l) ∧ ∀ L. BitLen(n,L) → l = L.
```

Its existence proof performs natural-number induction. At each positive
successor, it constructively distinguishes whether the current input reaches
its upper power-of-two boundary. If so, it constructs the next power; if not,
it preserves the current bracket. Uniqueness compares candidate lengths and
uses monotonicity of powers to rule out incompatible positive brackets. The
exact-power theorem additionally proves `PowTwo(e,p) → BitLen(p,S e)`.

## Independently checked candidate evidence

All 21 dependency-curried proof bodies pass the original independent kernel
against the immutable Alpha v21 checked theorem statements:

```text
proof nodes:      969
direct edges:      50
tactic commands:  542
ordered-name SHA-256:
150dae13f4587c0787717d537e98612c022a655eb9721a5db6ee84af921e281c

binary_length_exists:
53b6739ac80ec864c4b36aecdbca366e4bc997a8a45e5a1ef2daaf05dbde7778

binary_length_functional:
4b14a06b7b09b4b54be5cbc0c0a22110d029c5e57a16e126f2f9298eca7f9e7f

binary_length_exists_unique:
4365c8d9b855b85331e421d1c5e82349c598097f22dfe65141738573ee7ae89e

binary_length_power_exact:
69eace7cc1b3f3f0b2a5b3694e4c43d54124099b5f2c7102ed705bb73cd7868f
```

These are isolated body-validation receipts, **not Alpha admission evidence**.
Promotion still requires the separate release-level recursive dependency,
artifact, original-kernel, and independently compiled Lean-verifier gates.

## Executable examples and remaining frontier

`binary_length_certificate(n)` computes an independently audited finite digit
and quotient history, reconstructs the exact input, checks its terminal zero,
checks the power bracket, and applies hard input/history caps. For example,
17 has length 5, bracket `[16,32)`, little-endian digits `(1,0,0,0,1)`, and
quotient history `(17,8,4,2,1,0)`.

These executable certificates are examples, not formal kernel proofs of an
unbounded beta-coded binary execution history. In particular this family does
not by itself prove the complete modular-exponentiation execution trace,
semantic trace/result identification, or its exact logarithmic step bound.
Those obligations remain separate dependencies of grand-campaign goal G102.
