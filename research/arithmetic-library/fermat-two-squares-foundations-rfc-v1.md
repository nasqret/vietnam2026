# RFC v1: constructive Fermat two-square foundations

Date: **2026-08-23**

Status: **12 isolated intuitionistic, dependency-curried candidate bodies
independently accepted by the unchanged Peano kernel.** No root in this
tranche is registered, promoted, or presented as a closed proof of Fermat's
two-square theorem.

Sources:

- `peano-lab/py/peano_lab/library/fermat_two_squares_candidate.py`
- `peano-lab/py/tests/test_fermat_two_squares_candidate.py`
- first supplementary-law prerequisite:
  `peano-lab/py/peano_lab/library/quadratic_supplement_minus_one_candidate.py`

The exact ordered candidate graph SHA-256 is
`dd2f4004c479d87f595cdba68bc6a08fbb368a64bc98bbec7934ad2ec68b6f3f`.

The subsequently checked
[`prime two-square theorem tranche`](fermat-two-squares-prime-rfc-v1.md)
now consumes these foundations to prove the full constructive prime endpoint.
Statements below describing a remaining gap apply to this initial tranche in
isolation, not to the current complete multi-tranche proof body.

## Purpose and trust boundary

The flagship eventually requires the independently closed statement

```text
forall p.
  Prime(p) -> ModEq(4,p,1) -> exists a b. p = a*a + b*b.
```

Here `Prime` and `ModEq` are explanatory abbreviations only. All actual
contracts expand into ordinary first-order formulas over `0`, successor,
addition, multiplication, equality, implication, conjunction, disjunction,
and quantifiers. No predicate symbol, signed primitive, division operation,
finite-choice axiom, classical principle, or trusted theorem name enters the
kernel.

This tranche proves several necessary arithmetic lemmas and explicitly
constructs a **canonical square root of minus one** together with a divisible
two-square norm. It also proves the exact final step that would turn a
sufficiently short divisible norm into a representation of the prime.

It does **not** construct that short norm. The finite pigeonhole or Euclidean
descent bridge is the remaining mathematical gap. The first supplementary law
used here is itself an isolated dependency-curried candidate; its name conveys
no independent proof authority. Consequently even a green focused test suite
does not admit Fermat's theorem or the complete two-square classification.

## Expanded relation conventions

For clarity only, the following names describe their fully expanded forms:

```text
FourResidue(z,c) := exists q. z = 4*q + c

Lt(a,b)          := exists h. h + S a = b

Dvd(p,z)         := exists k. z = p*k

QRes(p,n)        := exists r u v. r*r + p*u = n + p*v

BoundedQRes(p,n) := exists r.
                     (exists h. h + S r = p)
                     /\ (exists u v. r*r + p*u = n + p*v)

Prime(p)         := ~(p = 1)
                    /\ forall a b. p = a*b -> a = 1 \/ b = 1.
```

The first supplementary law represents `-1 modulo p` by the natural
predecessor `n` where `p = S n`; there is no negative object-language term.
All existential binder names are hygienic and the focused suite rejects free
variables and unexpanded display aliases.

## Ordered theorem contracts

1. `even_square_is_four_multiple`:

   ```text
   forall z k. z = 2*k -> exists q. z*z = 4*q + 0.
   ```

   The actual witness is `q = k*k`.

2. `odd_square_is_four_multiple_plus_one`:

   ```text
   forall z k. z = 2*k + 1 -> exists q. z*z = 4*q + 1.
   ```

   The actual witness is `q = k*k + k`.

3. `square_mod_four_zero_or_one`:

   ```text
   forall z. FourResidue(z*z,0) \/ FourResidue(z*z,1).
   ```

   An existing constructive parity decomposition selects the witness-bearing
   even or odd branch.

4. `sum_two_squares_mod_four_cases`:

   ```text
   forall a b.
     (FourResidue(a*a+b*b,0) \/ FourResidue(a*a+b*b,1))
     \/ FourResidue(a*a+b*b,2).
   ```

   All four combinations of square residues construct their own quotient.

5. `sum_two_squares_not_four_mod_three`:

   ```text
   forall a b. ~FourResidue(a*a+b*b,3).
   ```

   Constructive uniqueness of quotient and remainder excludes each of the
   previous three possibilities. This proves the elementary modulo-four
   obstruction, not the stronger prime-factor valuation criterion.

6. `prime_mod_four_one_minus_one_square_exists`:

   ```text
   forall p n.
     p = S n -> Prime(p) -> FourResidue(p,1) -> QRes(p,n).
   ```

   `mod4_one_is_odd` supplies the oddness hypothesis of
   `quadratic_supplement_minus_one_residue_iff_mod_four_one`. The positive
   direction of that exact supplementary law returns a genuine existential
   square-root witness.

7. `prime_mod_four_one_bounded_minus_one_square_exists`:

   ```text
   forall p n.
     p = S n -> Prime(p) -> FourResidue(p,1) -> BoundedQRes(p,n).
   ```

   The public `quadratic_residue_bounded_equiv` theorem reduces the preceding
   root to its canonical representative `r < p`. Successor shape alone proves
   that the modulus is nonzero.

8. `predecessor_square_congruence_yields_divisible_norm`:

   ```text
   forall p n r.
     p = S n ->
     (exists u v. r*r + p*u = n + p*v) ->
     exists k. r*r + 1 = p*k.
   ```

   Given the balanced congruence witnesses, the proof explicitly derives

   ```text
   (r*r + 1) + p*u = 0 + p*S(v).
   ```

   Existing constructive conversion from balanced congruence to canonical
   remainder decomposition then supplies the exact quotient `k`. No
   subtraction, quotient oracle, or host integer arithmetic is trusted.

9. `prime_mod_four_one_divisible_two_square_norm_exists`:

   ```text
   forall p n.
     p = S n -> Prime(p) -> FourResidue(p,1) ->
     exists r k. r*r + 1 = p*k.
   ```

   This combines the unbounded root with the exact divisibility bridge.

10. `prime_mod_four_one_bounded_divisible_two_square_norm_exists`:

    ```text
    forall p n.
      p = S n -> Prime(p) -> FourResidue(p,1) ->
      exists r k. Lt(r,p) /\ r*r + 1 = p*k.
    ```

    This stronger reusable endpoint packages a canonical representative and
    the same explicit divisible norm.

11. `positive_multiple_below_twice_equals_base`:

    ```text
    forall p z.
      Lt(0,z) -> Dvd(p,z) -> Lt(z,p+p) -> z = p.
    ```

    The proof constructs the quotient cases `0`, `1`, and `S(S k)`.
    Positivity rejects quotient zero; the last case explicitly witnesses
    `p+p <= z`, contradicting the strict upper bound. This argument even
    handles `p = 0` constructively, since its premises are then inconsistent.

12. `bounded_divisible_two_square_norm_equals_prime`:

    ```text
    forall p a b.
      Lt(0,a*a+b*b) -> Dvd(p,a*a+b*b) ->
      Lt(a*a+b*b,p+p) -> p = a*a+b*b.
    ```

    This is the exact final arithmetic implication required once a future
    pigeonhole or descent construction supplies the three hypotheses.

## Dependency and capacity receipts

The ordered tranche has 12 candidate nodes and 42 direct dependency edges:

- 10 edges connect earlier candidates in this tranche;
- 31 edges point to already public arithmetic/residue theorems; and
- exactly one edge points to the isolated positive first supplementary law.

The unique external supplementary dependency is
`quadratic_supplement_minus_one_residue_iff_mod_four_one`; its fully expanded
contract is injected as an ordinary implication hypothesis during body replay.

| candidate | direct dependencies | tactic commands | proof nodes | depth | proof objects |
|---|---:|---:|---:|---:|---:|
| `even_square_is_four_multiple` | 2 | 28 | 106 | 28 | 106 |
| `odd_square_is_four_multiple_plus_one` | 12 | 29 | 232 | 64 | 205 |
| `square_mod_four_zero_or_one` | 3 | 14 | 36 | 15 | 36 |
| `sum_two_squares_mod_four_cases` | 4 | 40 | 218 | 30 | 196 |
| `sum_two_squares_not_four_mod_three` | 2 | 74 | 271 | 27 | 271 |
| `prime_mod_four_one_minus_one_square_exists` | 2 | 19 | 22 | 15 | 22 |
| `prime_mod_four_one_bounded_minus_one_square_exists` | 2 | 25 | 29 | 14 | 29 |
| `predecessor_square_congruence_yields_divisible_norm` | 5 | 64 | 124 | 31 | 121 |
| `prime_mod_four_one_divisible_two_square_norm_exists` | 2 | 20 | 26 | 15 | 26 |
| `prime_mod_four_one_bounded_divisible_two_square_norm_exists` | 2 | 27 | 33 | 15 | 33 |
| `positive_multiple_below_twice_equals_base` | 5 | 43 | 128 | 31 | 125 |
| `bounded_divisible_two_square_norm_equals_prime` | 1 | 15 | 17 | 14 | 17 |
| **aggregate** | **42** | **398** | **1,242** | **maximum 64** | **1,187** |

These are metrics for separately checked dependency-curried bodies. They are
not a closed proof-tree or theorem-admission receipt. Every one of the 42
declared direct dependencies is independently poisoned to the false contract
`0 = 1`; its affected body then fails closed. This guards against the same
unused-dependency failure that previously interrupted quadratic-reciprocity
cluster replay.

The independent intuitionistic kernel accepts each original body certificate,
rejects strengthened false goals and targeted false arithmetic mutations, and
its unique proof-object traversal finds no `DNE` constructor. The focused test
enforces a hard 20-second real-time limit; on the development workstation all
78 checks pass in approximately 2.5 seconds.

## Computational sanity checks and the precise missing bridge

The following host-side calculations illustrate the existential statements.
They are independent regression examples, not extracted kernel programs or
proof authority.

| prime `p` | canonical root `r` | `(r*r+1)/p` | actual two-square representation |
|---:|---:|---:|---|
| 5 | 2 | 1 | `5 = 1*1 + 2*2` |
| 13 | 5 | 2 | `13 = 2*2 + 3*3` |
| 17 | 4 | 1 | `17 = 1*1 + 4*4` |
| 29 | 12 | 5 | `29 = 2*2 + 5*5` |
| 37 | 6 | 1 | `37 = 1*1 + 6*6` |
| 41 | 9 | 2 | `41 = 4*4 + 5*5` |
| 53 | 23 | 10 | `53 = 2*2 + 7*7` |
| 61 | 11 | 2 | `61 = 5*5 + 6*6` |
| 73 | 27 | 10 | `73 = 3*3 + 8*8` |
| 89 | 34 | 13 | `89 = 5*5 + 8*8` |
| 97 | 22 | 5 | `97 = 4*4 + 9*9` |

For `p = 13`, the canonical root gives `5*5+1 = 13*2`, not `13`. For
`p = 53`, it gives `23*23+1 = 53*10`. Therefore the existing canonical-root
endpoint alone cannot satisfy the final `norm < 2*p` premise. Claiming
Fermat's theorem from these witnesses would be unsound.

The next reviewed tranche must construct `a,b` satisfying all of

```text
0 < a*a+b*b,
p divides a*a+b*b,
a*a+b*b < p+p.
```

Two acceptable routes remain:

1. combine the existing finite pigeonhole infrastructure with a formally
   encoded integer square-root bound and signed coordinates; or
2. implement a terminating Euclidean/Cornacchia descent with an explicit
   natural-valued decreasing measure.

Only then can the already checked final implication provide
`p = a*a + b*b`. The signed Brahmagupta–Fibonacci multiplication identity,
the common-divisor lemma for primes congruent to three modulo four, the
even-valuation descent, and the complete representation criterion remain
separate future work.

## Reproduction

From `peano-lab/py`, run:

```bash
python3 -m pytest -q tests/test_fermat_two_squares_candidate.py
```

The suite verifies exact candidate ordering, graph and statement hashes,
native first-order closure, isolation from the public registry, dependency
ordering, pinned body receipts, intuitionistic kernel acceptance, no-DNE
audits, every-edge false-contract mutations, false theorem mutations, small
square residues, eleven `1 mod 4` prime roots, ten `3 mod 4` obstructions,
and bounded-multiple examples. It never attempts the expensive full
quadratic-reciprocity closure or a cluster submission.
