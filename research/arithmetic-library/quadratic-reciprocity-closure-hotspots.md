# Static hotspot audit of the optimized QR closure

Date: **2026-07-30**

Scope: exact graph rooted at `quadratic_reciprocity_combined`

Graph SHA-256: `2231ca4cde6931fad296513fb0c419e19beb7c37989d31fbf6cf01771597cb46`

Candidate-source SHA-256: `457327e29134e08fd8802a18b9e1a9e0e23fa84bb44f2934f1fcba466f6e6cb5`

This is a source-only audit. It calls the neutral quadratic-reciprocity stack
collector, reads theorem specifications, and performs integer/counter
recurrences. It does not replay tactics, construct a recursive certificate,
call the kernel, register a theorem, or admit anything.

## Result

The present recursively Cut-expanded proof tree **cannot** satisfy the
500,000 structural-node policy. This follows before a WMI replay:

| statically forced contribution | occurrences |
|---|---:|
| theorem bodies, at least one proof node each | 191,669 |
| dependency `Cut` nodes | 191,668 |
| leading theorem-level `intro` constructors in the recorded bodies | 348,145 |
| **rigorous structural-node lower bound** | **731,482** |

The third row counts only the consecutive `intro` commands at the start of
each theorem's own script. The closure builder's generated dependency
introductions are peeled before its Cuts are installed, while these
theorem-level introductions remain in the body. No `apply`, `split`,
`exists`, equality, induction, or rewrite proof node is charged. The true
tree is therefore strictly larger in all nontrivial cases.

For scale, weighting each recorded tactic command by its theorem occurrence
gives 1,994,700 command occurrences, versus 27,491 commands across the 557
unique bodies. This is only a pressure proxy—commands and proof nodes are not
one-to-one—and is not used in the rigorous lower bound.

WMI is still required for the exact node/object/depth/RSS receipt and kernel
and mutation gates. It is no longer required to decide whether this specific
tree can be below 500,000 nodes. Raising the limit would treat a known
compilation duplication as policy headroom and is not recommended.

## Exact recurrence

For a theorem `t` with ordered direct dependencies `deps(t)`, define

```text
R(t) = 1 + sum(R(d) for d in deps(t)).
```

This is exactly the number of theorem-certificate occurrences in the
recursively expanded tree, before proof-body nodes are counted. Propagating
`O(root)=1` downward by `O(d) += O(t)` gives the multiplicity of each named
theorem. The graph has 557 unique specifications, 1,791 direct edges, and 45
theorem levels (44 edges on the longest path), but:

| theorem | `R(t)` | `O(t)` at the QR root |
|---|---:|---:|
| `quadratic_reciprocity_combined` | 191,669 | 1 |
| `distinct_odd_primes_gauss_eisenstein_data_exists` | 191,205 | 1 |
| `odd_prime_gauss_eisenstein_orientation_data_exists` | 173,655 | 1 |
| `arbitrary_gauss_lemma_complete` | 161,897 | 1 |
| `arbitrary_euler_criterion_complete` | 144,191 | 1 |
| `arbitrary_euler_criterion_nonresidue_iff` | 95,413 | 1 |
| `bounded_euler_criterion_nonresidue_iff` | 93,272 | 1 |
| `arbitrary_euler_criterion_residue_iff` | 48,777 | 1 |
| `bounded_euler_criterion_residue_iff` | 46,636 | 2 |
| `bounded_euler_criterion_dichotomy` | 46,560 | 3 |

The three direct root children weigh 191,205, 223, and 240. Thus the final
sharing-conscious QR wrapper has already done its job: 99.76% of its theorem
recurrence lies in the data branch, not in the two final truth-table clients.

There are no repeated names inside any one direct dependency tuple. The
duplication is transitive fan-in. The largest direct fan-in values are:

| theorem | distinct parents | root occurrences | `R(t)` |
|---|---:|---:|---:|
| `le_refl` | 64 | 1,758 | 2 |
| `beta_at_unique` | 62 | 840 | 31 |
| `le_succ` | 55 | 992 | 2 |
| `succ_ne_zero` | 45 | 1,937 | 1 |
| `add_assoc` | 44 | 25,037 | 1 |
| `mul_comm` | 43 | 5,335 | 7 |
| `add_succ_left` | 42 | 21,931 | 1 |
| `add_comm` | 41 | 15,771 | 3 |
| `add_eq_zero_right` | 39 | 3,439 | 1 |
| `zero_add` | 38 | 26,513 | 1 |

The high multiplicities of tiny arithmetic facts are a symptom of tree
expansion. Rewriting those facts would not remove their many incoming paths.

## Top ten sibling-closure duplication sources

For each child `d`, let `C(d)` be the counter of named theorem occurrences in
its expanded subtree. At a parent, the sibling excess is

```text
sum(C(d) for d in deps) - elementwise_max(C(d) for d in deps).
```

Its counter norm, multiplied by `O(parent)`, is the maximum theorem-occurrence
reduction if all common child closure at that parent could be shared
perfectly. It is an upper bound for a source refactor, not a proof that the
refactor exists. Rows overlap and their savings must not be added.

| rank | parent | parent occurrences | local excess | propagated upper bound | refactor assessment |
|---:|---|---:|---:|---:|---|
| 1 | `arbitrary_euler_criterion_complete` | 1 | 48,776 | 48,776 | **Package refactor, moderate.** Construct the canonical representative once and return both iff results. Not a legal bare edge deletion. |
| 2 | `beta_prefix_extend` | 166 | 284 | 47,144 | **Deep encoding rewrite.** Nine CRT, modulus-product, and bound branches must share coherent existential witnesses. |
| 3 | `bounded_euler_criterion_nonresidue_iff` | 1 | 46,635 | 46,635 | **Package refactor, moderate.** Derive both iff views from one dichotomy package instead of recursively importing the residue view. |
| 4 | `bounded_euler_criterion_dichotomy` | 3 | 14,051 | 42,153 | **Deep arithmetic rewrite.** Its residue and nonresidue power endpoints share the Fermat/Wilson backbone but prove genuinely different branches. |
| 5 | `prime_wilson_terminal_product_package_exists` | 3 | 10,757 | 32,271 | **Deep Wilson/encoding rewrite.** Terminal state, coverage, magnitude recoding, and products would need one coherent constructor. |
| 6 | `beta_exclusive_recode_invariant_step` | 166 | 191 | 31,706 | **Deep local step rewrite.** Merge accumulated-product and recode-congruence construction while retaining the same witnesses. |
| 7 | `beta_product_permutation_invariant` | 10 | 2,390 | 23,900 | **Deep finite-fold rewrite.** Sixteen branches share prefix replacement and beta-product infrastructure. |
| 8 | `scaled_pair_order_terminal_power_mod_predecessor` | 3 | 7,665 | 22,995 | **Deep Wilson/Euler rewrite.** Successor lift, factorial transport, and Wilson congruence overlap below distinct semantic endpoints. |
| 9 | `beta_exclusive_accumulated_product_step` | 166 | 137 | 22,742 | **Deep arithmetic/CRT rewrite.** The overlap is spread over twelve divisor, order, and coprimality dependencies. |
| 10 | `binary_crt` | 332 | 63 | 20,916 | **Deep CRT rewrite.** A monolithic balanced-Bezout/congruence proof could share helpers, but this is not a wrapper change. |

The two Euler rows are the only attractive semantics-preserving package
refactors. Perfectly merging both overlapping child closures would reduce the
recurrence from 191,669 to 96,258 occurrences (95,411 saved; not the sum of
the two row values). Even under that optimistic model, the retained source
has a 367,511-node `Cut`/body/leading-intro lower bound and 1,000,029 weighted
script-command occurrences. The command count is a pressure proxy, not a
proof-node bound, but it leaves no credible margin for the many omitted proof
constructors.

Perfect sharing at all ten rows simultaneously would reduce the modeled
recurrence to 29,434 occurrences and the weighted command count to 386,768.
That scenario is not ten easy wrappers: it assumes coherent subtree sharing
inside beta extension, CRT, finite permutation, Wilson, and Euler. Implementing
it theorem by theorem would amount to a second proof-engineering campaign and
would still be capacity-borderline until replayed.

## Recommended unchanged-kernel compiler

A layered balanced-conjunction Cut bundle attacks the cause directly without
adding a kernel rule:

1. Assign every ancestor its longest dependency depth. There are 45 layers;
   the largest contains 63 theorem formulas.
2. Keep each already checked dependency-curried authoring body once. Do not
   recursively close that body.
3. Form a balanced conjunction package for each layer. Under the packages
   Cut for earlier layers, apply a theorem's curried body to ordinary
   `AndElimL`/`AndElimR` projections of its exact dependencies, then combine
   all theorems in the layer with `AndIntro`.
4. Cut each layer package once, accumulating 45 package hypotheses. Project
   the exact QR root from the final package.
5. Ask the unchanged independent kernel to check the one resulting empty-
   context certificate against the original QR formula.

This uses only existing implication, conjunction, hypothesis, and `Cut`
rules. It does not trust a theorem name, hash, cache, or external registry.
With the present graph it has these static scaffolding bounds:

| item | count/bound |
|---|---:|
| unique dependency-curried bodies | 557 |
| unique source commands across those bodies | 27,491 |
| layer Cuts | 45 |
| balanced layer-package `AndIntro` nodes | 512 |
| dependency applications (`ImpElim`) | 1,791 |
| maximum projection depth (`ceil(log2(63))`) | 6 |
| worst-case dependency projection nodes | 10,746 |

The last four rows add at most about 13,100 structural nodes beyond the 557
unique curried bodies, ignoring small final packaging details. Exact body
nodes, depth, formula memory, normalization behavior, and the 100,000-object
policy still require an implementation and WMI receipts. A 45-Cut spine plus
six-level projections is much more plausible under depth 256 than the current
44-level recursive dependency tree with repeated subtrees.

This compiler should be attempted before hotspot proof rewrites. If it
passes, the two Euler packages may still improve documentation and isolated
body cost, but they no longer control final closure size because every
ancestor body is already compiled once. Deep beta/CRT/Wilson rewrites should
be deferred unless the layered bundle exposes a direct-body, object, formula,
or depth hotspot. A content-addressed proof-DAG remains the fallback if
logical layer packaging is too large or normalization re-expands it.

## Reproduction

Run this from `peano-lab/py`; it completes in under two seconds on the audited
laptop and performs no replay:

```python
from collections import Counter, defaultdict

from peano_lab.library.quadratic_reciprocity_stack import (
    QR_ROOT_NAME,
    build_quadratic_reciprocity_stack,
)

stack = build_quadratic_reciprocity_stack()
specs = [spec for _, spec in stack.combined_order]
by_name = {spec.name: spec for spec in specs}

counters = {}
weights = {}
depths = {}
for spec in specs:
    counter = Counter({spec.name: 1})
    for dependency in spec.dependencies:
        counter += counters[dependency]
    counters[spec.name] = counter
    weights[spec.name] = sum(counter.values())
    depths[spec.name] = (
        0 if not spec.dependencies
        else 1 + max(depths[name] for name in spec.dependencies)
    )

occurrences = Counter({QR_ROOT_NAME: 1})
parents = defaultdict(set)
for spec in specs:
    for dependency in spec.dependencies:
        parents[dependency].add(spec.name)
for spec in reversed(specs):
    for dependency in spec.dependencies:
        occurrences[dependency] += occurrences[spec.name]

def leading_intros(spec):
    count = 0
    for command in spec.script:
        if command == "intro" or command.startswith("intro "):
            count += 1
        else:
            break
    return count

root_weight = weights[QR_ROOT_NAME]
cut_nodes = root_weight - 1
intro_nodes = sum(
    occurrences[name] * leading_intros(spec)
    for name, spec in by_name.items()
)
lower_bound = cut_nodes + root_weight + intro_nodes

sibling_rows = []
for spec in specs:
    if len(spec.dependencies) < 2:
        continue
    total = Counter()
    maximum = Counter()
    for dependency in spec.dependencies:
        child = counters[dependency]
        total += child
        for name, count in child.items():
            maximum[name] = max(maximum[name], count)
    local = sum((total - maximum).values())
    if local:
        sibling_rows.append(
            (occurrences[spec.name] * local, local, spec.name)
        )

assert stack.graph_sha256 == (
    "2231ca4cde6931fad296513fb0c419e19beb7c37989d31fbf6cf01771597cb46"
)
assert len(specs) == 557
assert sum(len(spec.dependencies) for spec in specs) == 1791
assert max(depths.values()) == 44
assert root_weight == 191669
assert cut_nodes == 191668
assert intro_nodes == 348145
assert lower_bound == 731482
assert not any(
    len(spec.dependencies) != len(set(spec.dependencies)) for spec in specs
)
print(sorted(sibling_rows, reverse=True)[:10])
```

The expected first tuple is
`(48776, 48776, 'arbitrary_euler_criterion_complete')`; the tenth is
`(20916, 63, 'binary_crt')`.
