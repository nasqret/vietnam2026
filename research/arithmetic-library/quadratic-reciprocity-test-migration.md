# Quadratic-reciprocity test migration for public enrollment

## Result

The future admission commit must migrate candidate tests from the blanket
assumption “every factory output is private” to the exact partition:

- 346 reviewed factory outputs;
- 317 enrolled dependency ancestors, **including**
  `quadratic_reciprocity_combined`;
- 29 non-ancestor outputs that remain private;
- 240 already-public ancestors and a 557-node root closure.

The current tests contain 125 explicit absence assumptions in 79 files.  More
importantly, 74 files seed 113 candidate dependency cores from the unified
`_specs_by_name()` mapping.  After enrollment that mapping contains the 317
new entries, so those helpers can silently stop testing isolated modular
bodies even when no negative assertion fails.

This is a preparation note only.  No candidate is currently enrolled.

## Reproducible audit

The audit covers every candidate- or QR-named test:

```console
rg --files peano-lab/py/tests \
  | rg '/test_.*(candidate|quadratic_reciprocity|qr_).*\.py$'
```

That set has 86 files: 78 candidate-named files and 10 QR-named files, with
two files in both groups.

The four disjoint direct-assumption searches are:

```console
rg -n 'not in public' peano-lab/py/tests \
  --glob '*candidate*.py' --glob '*quadratic_reciprocity*.py' \
  --glob 'test_qr_*.py'

rg -n 'not in _specs_by_name\(\)' peano-lab/py/tests \
  --glob '*candidate*.py' --glob '*quadratic_reciprocity*.py' \
  --glob 'test_qr_*.py'

rg -n 'not in core' peano-lab/py/tests \
  --glob '*candidate*.py' --glob '*quadratic_reciprocity*.py' \
  --glob 'test_qr_*.py'

rg -n 'not in registry_source' peano-lab/py/tests \
  --glob '*candidate*.py' --glob '*quadratic_reciprocity*.py' \
  --glob 'test_qr_*.py'
```

Current exact results are:

| Category | Matches | Files | Syntactic split |
|---|---:|---:|---|
| `not in public` | 45 | 44 | 43 whole-group, 2 direct/root |
| `not in _specs_by_name()` | 14 | 14 | 2 whole-group, 12 direct |
| `not in core` | 48 | 30 | 22 whole-group, 26 singular/collision guards |
| `not in registry_source` | 16 | 15 | 15 literal module names, 1 manifest loop |
| subtotal | 123 | 78 unique | categories are disjoint by match |

Two additional assumptions bring the exact total to 125 matches in 79 unique
files:

- `assert not set(local) & set(core)` in
  `test_fermat_residue_map_candidate.py`;
- the expected `"root_public": False` subprocess receipt in
  `test_quadratic_reciprocity_stack.py`.

The broader resolver audit is:

```console
rg -n '_specs_by_name\(\)' peano-lab/py/tests \
  --glob '*candidate*.py' --glob '*quadratic_reciprocity*.py' \
  --glob 'test_qr_*.py'

rg -n 'core = dict\(_specs_by_name\(\)\)|core = _specs_by_name\(\)' \
  peano-lab/py/tests \
  --glob '*candidate*.py' --glob '*quadratic_reciprocity*.py' \
  --glob 'test_qr_*.py'
```

It finds 179 `_specs_by_name()` references in 83 files and 113 direct core
seeds in 74 files.  Not every reference is wrong: a public-replay test should
use the unified registry.  Every modular candidate-body test, however, must
be reviewed so enrollment does not change its resolver by accident.

The 125-match combined search also produces the same totals over *all* Python
tests, so this filename-based scope does not miss another direct absence
assertion elsewhere in `peano-lab/py/tests`.

## Exact omitted partition

At graph hash
`98a36450cfe1de29c20be67a1c5f65c8064e9f9eec5368ab769065f910008698`,
the sorted 29 names joined by `\n` with no terminal newline have SHA-256
`1b08f341edf897538d43c4f6b77100b95d15a528283f65b083120c34be2ded85`:

```text
bounded_euler_criterion_complete
distinct_odd_prime_half_rectangle_oriented
eisenstein_initial_segment_indicator_choice
eisenstein_initial_segment_prefix_exists
eisenstein_initial_segment_prefix_extend
eisenstein_rectangle_decoded_successor_row_count_decompose
eisenstein_rectangle_row_count_prefix_succ_restrict
fermat_little_all_inputs
finite_bounded_into_injective_omits
gauss_magnitude_positive_below_prime
gauss_magnitude_product_coprime
gauss_magnitude_successor_coverage
gauss_signed_pointwise_mul_successor_mod
inverse_prefix_injective
inverse_prefix_surjective
pair_order_remaining_pairs_short
pair_order_terminal_double_length
prime_inverse_prefix_exact_endpoints
prime_pair_order_iteration
prime_pair_order_pair_count_step
prime_pair_order_remaining_pair_step
prime_pair_order_state_step
prime_pair_order_terminal_state_exists
prime_scaled_inverse_involutive
quadratic_reciprocity_opposite_case
quadratic_reciprocity_same_case
scaled_inverse_pair_order_terminal_coverage
scaled_inverse_prefix_injective
scaled_inverse_qres_or_fixed_free
```

These names come from 17 factory owners.  Tests for those factories require a
per-output partition check; a factory-level “all public” replacement would be
just as wrong as the present “all private” assertion.

Tests must compute this set from the reviewed stack rather than trusting the
duplicated list in this note:

```python
enrolled = set(stack.candidate_by_name)
all_outputs = set(stack.all_candidate_by_name)
omitted = all_outputs - enrolled

assert len(all_outputs) == 346
assert len(enrolled) == 317
assert len(omitted) == 29
assert stack.candidate_order[-1].name == QR_ROOT_NAME
```

## Migration by assertion category

### 1. Blanket public-absence assertions

Current forms include:

```python
assert all(spec.name not in public for spec in factory_specs)
assert NAME not in _specs_by_name()
assert QR_ROOT_NAME not in public
```

These are pre-admission-only.  Replace them with an exact per-spec assertion:

```python
def assert_factory_partition(specs, stack, public):
    enrolled = stack.candidate_by_name
    omitted = set(stack.all_candidate_by_name) - set(enrolled)
    for spec in specs:
        assert stack.all_candidate_by_name[spec.name] == spec
        if spec.name in enrolled:
            assert public[spec.name] == spec
        else:
            assert spec.name in omitted
            assert spec.name not in public
```

Use specification equality, not only name membership.  This detects a changed
statement, script, dependency order, or summary under an enrolled name.

### 2. Candidate dependency cores

This pattern is unsafe after enrollment:

```python
core = dict(_specs_by_name())
for spec in candidate_factory(TheoremSpec):
    assert spec.name not in core
    core[spec.name] = spec
```

Choose the table according to the purpose of the test.

For an isolated modular-body replay, begin with the explicitly frozen pre-QR
base exported by the admission implementation, then add local candidate specs
in topological order:

```python
pre_qr_by_name = dict(QR_BASE_BY_NAME)
local_by_name = {}

def add_local(spec):
    existing = local_by_name.get(spec.name)
    if existing is None:
        existing = pre_qr_by_name.get(spec.name)
    if existing is not None:
        assert existing == spec
    else:
        local_by_name[spec.name] = spec

def resolve(name):
    return local_by_name.get(name) or pre_qr_by_name[name]
```

Local candidate bodies must take precedence over the unified public table.
Otherwise a test may unknowingly consume an already closed public replay
instead of checking the factory's dependency-curried body.

For a public-admission test, do not reconstruct a candidate core.  Call
`replay(name)` through the production registry and independently check the
returned empty-context certificate and live-use bounds.

If a helper genuinely accepts either a base theorem or a locally rebuilt
equal spec, replace “must be absent” with an exact compatibility insertion:

```python
def insert_compatible(table, spec):
    previous = table.get(spec.name)
    if previous is None:
        table[spec.name] = spec
    else:
        assert previous == spec
```

Do not silently overwrite a differing public specification with `dict.update`.

### 3. Registry-source substring assertions

Assertions such as

```python
assert "wilson_pair_order_candidate" not in registry_source
```

are pre-admission-only and must be removed as admission evidence.  The public
registry can enroll through the pure stack assembler without containing every
candidate module name literally, so this assertion could remain green while
the candidate is public.

Replace it with runtime equality against `QR_THEOREMS` and the 317/29
partition.  Keep the separate static architecture check that the *pure stack
module* does not import the theorem registry; that check remains valid after
admission.

### 4. QR coordination tests

These files require explicit state changes in the admission commit:

- `test_quadratic_reciprocity_stack.py`: change candidate-order absence and
  `root_public: False` to exact 317-entry enrollment; retain factory counts,
  graph/source hashes, import-order checks, immutability, and builder
  non-mutation;
- `test_quadratic_reciprocity_closure.py`: remove “intentionally absent” and
  registry-source assumptions; make its diagnostic resolver use the frozen
  base plus local bodies, never the unified table by accident;
- `test_quadratic_reciprocity_layered_wmi.py`: replace root absence with
  `public[QR_ROOT_NAME] == stack.candidate_by_name[QR_ROOT_NAME]`, then test the
  public layered replay path;
- `test_quadratic_reciprocity_candidate.py`: its factory contains the enrolled
  combined root and two omitted case-split helpers, so it must use the mixed
  per-output partition rather than either blanket assertion;
- `test_fermat_residue_map_candidate.py`: replace its blanket set-disjointness
  with compatible equality or the exact partition helper.

## Assertions by lifetime

### Retire at admission

- every unqualified `candidate.name not in public/core/_specs_by_name()` claim;
- `QR_ROOT_NAME not in public` and `root_public: False`;
- candidate-module substring absence from `theorems.py`;
- the closure docstring saying the final candidates are intentionally absent.

These assertions describe the pre-admission campaign state.  Keeping them in
the admitted suite either fails correctly or, for source substrings, can pass
for the wrong reason.

### Keep, but bind explicitly to the frozen pre-QR base

- local candidate-name freshness before adding a modular body;
- dependency resolution against public ancestors only;
- candidate-body replay that deliberately avoids public closed certificates.

Rename generic `core` variables to `pre_qr_by_name` or `local_by_name`.  The
name makes it difficult for a later edit to substitute `_specs_by_name()`.

### Become enrollment assertions

- all 317 `candidate_order` names exist publicly with equal `TheoremSpec`
  values and in dependency-before-consumer order;
- the combined root is the last candidate entry and uses the pinned statement
  and direct dependency spine;
- all 29 computed omitted names remain absent from the public registry;
- no other one of the 346 factory outputs is lost or accidentally enrolled;
- every enrolled theorem replays through its pinned public strategy and
  passes the unchanged kernel and capacity limits.

### Remain permanently valid

- candidate factories are deterministic and return exact spec values;
- factory ownership, source hashes, graph hash, counts, and topology are
  pinned;
- the pure stack builder does not mutate or import the public registry;
- candidate-body preflight itself remains non-admitting;
- rebuilding a stack or body does not grant theorem authority;
- only the unchanged empty-context kernel check admits a certificate.

## Safe migration order

1. Export and test an immutable pre-QR base mapping before changing
   `THEOREMS`.
2. Add shared test helpers for the exact partition, compatible insertion, and
   local-first resolution.
3. Convert modular-body helpers away from unified `_specs_by_name()` while the
   old pre-admission suite is still available for comparison.
4. Append exactly `stack.candidate_order` and pin the 317-entry public order.
5. Replace all blanket absence/source-substring assertions with enrollment or
   exact omitted-set assertions in the same commit.
6. Run candidate modular-body tests and public replay tests separately.  A
   green public replay must not substitute for a skipped modular-body check.
7. Run the complete cold WMI, mutation, catalog, UI, and Pyodide gates before
   changing release artifacts.

After migration, rerun the combined 125-match search.  Any remaining result
must mention either the computed `omitted` set or an explicitly frozen
`pre_qr_by_name`; unqualified `public`, `core`, source-substring, and root
absence assumptions should be zero.
