# Actual Gaussian finite-product replacement and swaps

Status: frozen additive candidates, 2026-08-28. These three ordinary-HA proofs
support G082's finite factor permutation argument. They do not constitute a
factorization-existence or unique-factorization admission on their own.

## Exact contracts

`GProduct(b,c,l,P)` is the independently defined actual beta-coded Gaussian
multiplication history in `gaussian_factorization_candidate.py`: the trace
starts at Gaussian identity code **6**, each step decodes the actual factor
and multiplies the previous Gaussian value by it, and the last trace entry
is `P`. It is not the natural product of the factor codes.

`gaussian_product_replace_balance` has the following exact shape:

```text
∀k b c d e i p q P Q T.
  i<k → Beta(b,c,i,p) → Beta(d,e,i,q) →
  (∀j a. j<k → j≠i → Beta(b,c,j,a) → Beta(d,e,j,a)) →
  GProduct(b,c,k,P) → GProduct(d,e,k,Q) →
  GMul(Q,p,T) → GMul(P,q,T).
```

The two multiplication relations share their actual output code `T`.
The proof does not use a natural-number equality `Q*p=P*q` for coded values.
Ordinary induction on `k` exposes the final step of both product histories.
Replacing the final factor reduces to equality of the recoded prefix
products and the checked Gaussian commutation/association law. Replacing
an earlier factor applies the induction hypothesis to the shorter histories
and constructs the needed intermediate product explicitly.

`gaussian_product_replace_balance_iff` proves both directions of this
equivalence. It uses the previously checked, untyped beta-prefix reflection
theorem to derive preservation of the reverse prefix, rather than assuming
that a one-way preservation assertion is automatically reversible.

`gaussian_product_swap_last_invariant` proves:

```text
∀b c d e l i p q P Q.
  i<l → SwapLast(b,c,d,e,l,i,p,q) →
  GProduct(b,c,S l,P) → GProduct(d,e,S l,Q) → P=Q.
```

`SwapLast` is exactly the historical five-clause beta relation: old index
`i` is `p`, old last index `l` is `q`, new index `i` is `q`, new last index
is `p`, and every other entry below `S l` is preserved. The conclusion is
literal equality of the canonical product codes. There are **no** nonzero,
unit, prime, irreducibility or cancellation premises. Zero factors, units
and repetitions are permitted. The endpoint concerns an interior/last swap;
it does not silently replace its explicit `i<l` boundary by a different one.

## Dependency order and inventory

The factory is
`gaussian_product_reindex_candidate.make_gaussian_product_reindex_candidate_theorems`.
It follows the ring, divisibility, gcd, Gaussian factor-search and actual
Gaussian-product/factorization factories. The subsequent Gaussian
factor-permutation factory may use it. No dependency points backwards from
these proofs to a factor-uniqueness conclusion.

| Item | Value |
| --- | ---: |
| Ordinary theorem rows | 3 |
| Direct dependency edges | 22 |
| Tactic commands | 431 |
| Body occurrences / distinct body objects | 565 / 565 |
| Largest body | 314 |
| Maximum proof depth | 61 |

Ordered-name SHA-256, with newline separators and no trailing newline:
`52a3a25db3d51827c7a85bf37514977d405d1bf1e026d7927e7ef144b18d5ca3`.

Exact statement pins:

| Theorem | SHA-256 |
| --- | --- |
| `gaussian_product_replace_balance` | `1b5a5e94da214ed6664dd8464acad9a88b1732badc4af8e282daf1800e51350a` |
| `gaussian_product_replace_balance_iff` | `f9b481d187747f5c3084772a722011398d5f5692e2b7174f8a2d9215505c0f7c` |
| `gaussian_product_swap_last_invariant` | `fe08f5ab6dc2dfcc72533571cadba5a55dfa4a9a4d320c9f97d4314d47ff480a` |

## Verification receipt and boundary

The full focused suite passed **42/42 tests in 167.00s**:

```text
env PYTHONPATH=peano-lab/py:scripts python3 -m pytest -q \
  peano-lab/py/tests/test_gaussian_product_reindex_candidate.py
```

All three positive ordinary HA bodies pass in isolated fresh processes.
The existing 45/50-second CPU and 60-second wall limits remain unchanged.
Every proof is tested against false-conclusion, truncated-script, removed-
dependency and corrupted-dependency mutations. Additional negative tests
drop the actual second product, drop preservation of the other entries, or
falsely assert that a swapped product is always the identity. Independent
AST assertions reconstruct both actual beta multiplication traces and all
five swap clauses. Every local proposition and every direct dependency is
audited, with literal row, command, body-profile and statement hash pins.

Numerical microaudits construct genuine beta codes for both factor lists
and Gaussian product histories. They cover zero factors, repeated factors,
all four units, negative and nonreal factors, replacement at every index,
and every interior/last swap. The initial trace value is explicitly checked
as code `6`. These microaudits are supplementary tests, not proof authority.

The immutable historical test parent is the 2764-row Alpha-v28 catalog with
SHA-256 `897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`.
New dependency statements are curried into candidate-body checks; this
does not itself admit their assumptions. A complete empty-context HA bundle
and independent compiled Lean receipt remain separate release gates. No
kernel, old provider, old definition, checked-use flag or publication is
changed by this candidate.

Frozen source SHA-256:
`7a5b5d0b19aa8217fab943d215b859e031bada36f7eebc1409c0949b99b33f2c`.
