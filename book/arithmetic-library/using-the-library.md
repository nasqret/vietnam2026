# Using and extending the library

In a checkout containing this candidate, the theorem index is available
through `pa lib`. A theorem card shows the closed statement, earlier
dependencies, generated replay prelude, authored tactic body, exact
certificate size, and independent-kernel result.

The URLs below are promotion targets for the public browser application.
Existing production entries may already open there; candidate-only entries,
including the division, gcd, Bézout, Gauss, Euclid, and constructive
prime-search layers, balanced modular congruence, and single-position Gödel-β
decoding and congruence projection, become available only after this build is
promoted. The 161-entry
local candidate has not been
deployed by this documentation change.

- [`pa lib`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib)
- [`pa lib add_congr`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20add_congr)
- [`pa lib multiple_trans`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20multiple_trans)
- [`pa lib division_remainder_unique`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20division_remainder_unique)
- [`pa lib prime_decidable`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20prime_decidable)
- [`pa lib prime_divisor_exists`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20prime_divisor_exists)
- [`pa lib mod_eq_add`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20mod_eq_add)
- [`pa lib mod_eq_mul`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20mod_eq_mul)
- [`pa lib beta_at_exists_unique`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20beta_at_exists_unique)
- [`pa lib beta_at_to_mod_eq`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20beta_at_to_mod_eq)
- [`pa lib square_residue_witness`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20square_residue_witness)
- [`pa lib mod5_fourth_power_one`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20mod5_fourth_power_one)

## Importing a checked theorem

`use` adds a checked formula to the local context. Exact reuse can close a goal
without reconstructing its proof interactively:

```text
pa> pa prove forall a b c d. a = b -> c = d -> a + c = b + d
pa> use add_congr
pa> exact add_congr
pa> qed
```

Here is the same pattern for product closure of divisibility:

```text
pa> pa prove forall a n m. (exists q. n = a * q) -> exists s. n * m = a * s
pa> use multiple_mul_right
pa> exact multiple_mul_right
pa> qed
```

The context import is backed by a self-contained Cut. It embeds the theorem's
closed certificate, the focused conclusion, and the body that may use the new
hypothesis. At QED the independent kernel checks both branches and the original
target from the empty context; no theorem name or hash reaches the checker.

The original modulus-five exercise now has the same short route:

```text
pa> pa prove forall n. ~(exists x. n = 5 * x) -> exists x. n * n * n * n = 5 * x + 1
pa> intro n
pa> intro h
pa> use mod5_fourth_power_one
pa> apply mod5_fourth_power_one
pa> exact h
pa> qed
```

This imports the complete current 2,675-node shared certificate; it does not
add a modular-arithmetic oracle or external theorem lookup to the kernel.

## Turning a hypothesis into pointwise facts

The motivating interaction is now a generic lemma. A negated existential
multiple can be converted without inventing a witness:

```text
pa> pa prove forall a n. ~(exists q. n = a * q) -> forall q. ~(n = a * q)
pa> use not_multiple_pointwise
pa> exact not_multiple_pointwise
pa> qed
```

After importing and specializing this theorem in a larger proof, a concrete
term such as `5 * m + 1` is legal only when `m` is already a variable in the
current context. `specialize` instantiates a universal hypothesis; it does not
create new variables.

## Adding a theorem

An admitted entry has five authored fields:

```python
TheoremSpec(
    name="my_fact",
    statement="forall n. ...",
    dependencies=("earlier_fact",),
    script=("intro n", "..."),
    summary="One precise sentence.",
)
```

The admission workflow is:

1. choose a stable name and place the fact at the smallest correct layer;
2. write a closed formula in the current Peano language;
3. list only earlier dependencies;
4. replay the primitive tactic body;
5. package each checked dependency as a self-contained Cut, embedding both
   proof branches without external theorem-name or hash authority;
6. check the closed certificate independently;
7. measure live-import bounds;
8. update source, book, vault, catalog, graph, and snapshot links;
9. run the full repository gates.

Do not add a trusted predicate merely for notation. Do not mark a curriculum
target Peano-checked because Lean or a textbook proves an analogous theorem.
Do not hide missing checked β-sequence/product laws behind a factorization
name; keep separately checked companion authority explicit. The native library
now has constructive prime-divisor existence, the balanced additive and
multiplicative congruence API, and functional single-position β decoding with
its congruence bridge. It does not yet have greatest-prime descent, binary or
bounded CRT, bounded congruence uniqueness, finite-prefix extension,
prefix-product traces, or FTA.

## Reproducing the artifact

From the repository root:

```bash
python3 scripts/build_peano_library_snapshot.py --check
python3 scripts/verify_arithmetic_knowledge_base.py
cd peano-lab/py
python3 -m pytest tests/test_foundational_arithmetic_library.py -q
```

The first command verifies exact metadata for the 161 checked certificates,
the second validates the 168-node research DAG and source register, and the
last exercises the checked foundational layer directly.
