# Using and extending the library

In a checkout containing this candidate, the theorem index is available
through `pa lib`. A theorem card shows the closed statement, earlier
dependencies, generated replay prelude, authored tactic body, exact
certificate size, and independent-kernel result.

The URLs below are promotion targets for the public browser application.
Existing production entries may already open there; candidate-only entries,
including the division, gcd, Bézout, Gauss, Euclid, and constructive
prime-search layers, balanced modular congruence, single-position Gödel-β
decoding as bounded congruence, and constructive binary CRT become available
only after this build is promoted. The source runtime now has 384 checked
entries. The last source-bound 1,692-session/13,344-transition corpus was built
at the 247-theorem checkpoint and has fingerprint
`6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`.
The isolated all-ladder smoke has 494 sessions, 9,235 raw/9,232 unique
transitions, and all 247 authored QEDs. The integrated local browser candidate
deterministically verifies as build `2026-08-09a`, application
`a-a195e3ab28b3`, with 150 worker sources; its source inventory, content
manifest, deployment contracts, and complete local stage pass. The build has
not been deployed, and direct attached-browser UI inspection remains
unclaimed.

The [public Peano Lab shell](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib)
still serves the earlier production snapshot. In this candidate checkout, try
representative milestones directly:

```text
pa lib division_remainder_unique
pa lib gcd_bezout_exists
pa lib euclid_prime_dvd_product
pa lib prime_unbounded
pa lib bounded_beta_crt_for_existing_code
pa lib prime_factorization_existence
pa lib prime_factorization_uniqueness
pa lib fundamental_theorem_of_arithmetic
```

The {doc}`theorem atlas <theorem-atlas>` provides the complete 384-theorem
index, with a full replay recipe and immutable source links for every entry.
Candidate-only browser commands must not be presented as live until the
corresponding Peano Lab build is promoted.

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
target Peano-checked because Lean or a textbook proves an analogous theorem,
and keep companion authority explicit. The native library now checks the full
conservative β route: bounded CRT, independent finite-prefix recoding,
one-value extension, exact prefix-product traces, Product functionality,
`AllPrime`, sortedness, greatest-prime descent, canonical append,
factorization existence, extensional uniqueness and the combined FTA.
Unconditional β-modulus coprimality remains false—$c=1$ gives moduli $3$ and
$6$—so the checked bounded construction deliberately chooses a suitable
common multiple. The generated {doc}`theorem atlas <theorem-atlas>` is the
authoritative book view for current scripts and dependencies; this workflow
must regenerate it whenever the snapshot changes.

## Reproducing the artifact

From the repository root:

```bash
python3 scripts/build_peano_library_snapshot.py --check
python3 scripts/build_arithmetic_book_atlas.py --check
python3 scripts/verify_arithmetic_knowledge_base.py
cd peano-lab/py
python3 -m pytest tests/test_foundational_arithmetic_library.py -q
```

The snapshot command verifies exact metadata for all 384 checked certificates
and ordered root digest `73b31b4775d2…6e89b`. The atlas command verifies that
every displayed statement, dependency, proof recipe, metric and hash still
matches that snapshot. The catalog command validates the 385-node research DAG
and source register, and the last command exercises the checked foundational
layer directly.
