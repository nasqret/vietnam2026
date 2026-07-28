# Using and extending the library

The live index is available through `pa lib`. A theorem card shows the closed
statement, earlier dependencies, generated replay prelude, authored tactic
body, exact certificate size, and independent-kernel result.

Useful entry points include:

- [`pa lib`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib)
- [`pa lib add_congr`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20add_congr)
- [`pa lib multiple_trans`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20multiple_trans)
- [`pa lib square_residue_witness`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20square_residue_witness)

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

The context import is a temporary cut. At QED the untrusted compiler replaces
it with the theorem's closed certificate, normalizes the exposed cuts, and
asks the independent kernel to check the original target from the empty
context.

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
5. eliminate all dependency cuts;
6. check the closed certificate independently;
7. measure live-import bounds;
8. update source, book, vault, catalog, graph, and snapshot links;
9. run the full repository gates.

Do not add a trusted predicate merely for notation. Do not mark a curriculum
target checked because Lean or a textbook proves an analogous theorem. Do not
hide a missing sequence representation behind a factorization name.

## Reproducing the artifact

From the repository root:

```bash
python3 scripts/build_peano_library_snapshot.py --check
python3 scripts/verify_arithmetic_knowledge_base.py
cd peano-lab/py
python3 -m pytest tests/test_foundational_arithmetic_library.py -q
```

The first command verifies exact certificate metadata, the second validates
the larger research DAG and source register, and the last exercises the
checked foundational layer directly.
