# K3C Alpha: valid lists, membership, and semantic lookup

K3B proved that natural numbers can carry finite, outer-head cell histories and
that an entry can be recovered through the relational predicate `ListAt`.
K3C is the first client-facing layer over that representation. It introduces
two readable definitions and seventeen reusable theorems without adding a
list type, an indexing function, or a new kernel constant.

```{admonition} Exact evidence boundary
:class: important
These seventeen rows belong to **Alpha v2** with `body_checked` evidence. Every
expanded statement is a closed formula of the unchanged PA language, every
dependency-curried tactic body is accepted by the intuitionistic kernel, every
declared direct dependency survives removal testing, and false-conclusion
mutations fail. They are not yet checked-use facts: a two-pass isolated
empty-context closure receipt is pending while WMI is unavailable. Stable
remains exactly 432 theorems, and Alpha v1 remains byte-for-byte sealed.
```

## Two conservative definitions

The mathematical surface is

$$
\begin{aligned}
\operatorname{CellListValid}(z)
  &:\!\Longleftrightarrow \exists \ell\;\operatorname{CellListLen}(z,\ell),\\
\operatorname{ListMember}(z,a)
  &:\!\Longleftrightarrow \exists i\;\operatorname{ListAt}(z,i,a).
\end{aligned}
$$

`CellListValid` hides the length of the represented list. `ListMember` hides
the index of an occurrence. Both are expanded before parsing into formulas
over only (0,S,+,\times,=), connectives, and quantifiers. In particular,
membership is relational and permits repeated values; it does not choose a
distinguished occurrence.

The list orientation is inherited from K3B. If

$$
\operatorname{Cell}(z,h,t)
\quad:\!\Longleftrightarrow\quad
z=S\bigl((h+t)S(h+t)+(t+t)\bigr),
$$

then (h) is the entry at outer index (0), and index (S(i)) in (z)
is index (i) in the tail (t).

## The seventeen-theorem interface

| Layer | Theorems | Mathematical role |
|---|---|---|
| validity | `cell_list_valid_nil`, `cell_list_valid_cell_intro`, `cell_list_valid_cases`, `cell_list_valid_cell_elim`, `list_at_implies_cell_list_valid` | construct, split, and descend through valid codes; recover validity from lookup |
| membership | `list_member_implies_cell_list_valid`, `list_member_nil_false`, `list_member_cell_intro_head`, `list_member_cell_intro_tail`, `list_member_cell_elim`, `list_member_cell_iff`, `list_member_pointwise_transport` | domain, nil exclusion, head/tail introduction and elimination, and representation-independent transport |
| semantic lookup | `list_at_exists_unique`, `cell_list_nonempty_iff_head_exists`, `cell_list_code_eq_lookup_values`, `cell_list_code_eq_iff_pointwise`, `cell_list_decompose_unique` | total and unique in-range lookup, nonemptiness, extensional equality, and unique outer-cell decomposition |

The most useful equations are the following. For a valid tail,

$$
\operatorname{Cell}(z,h,t)
\Longrightarrow
\bigl(\operatorname{ListMember}(z,a)
\leftrightarrow a=h\lor\operatorname{ListMember}(t,a)\bigr).
$$

For two represented lists of the same length, code equality is equivalent to
agreement of every pair of values returned at every in-range index. And every
successor-length list has a uniquely determined outer head and tail.

## Sparse dependency view

Yellow hexagons are definitions, green rectangles are previously checked-use
inputs, blue rounded rectangles are the new Alpha-only theorem rows, and the
grey dashed box is a future gate rather than a theorem in this tranche. The
diagram is a grouped conceptual spine; the exact catalog—not these grouped
arrows—is authoritative for declared direct dependencies.

```{image} ../_static/k3c-list-interface.svg
:alt: Sparse dependency spine from K3B through the K3C definitions and theorem APIs to append and restriction
:width: 100%
```

## Proof anatomy

The proofs stay constructive throughout.

1. Validity cases induct on the hidden represented length. Length zero gives
   nil; successor length exposes one exact cell and a valid tail.
2. Membership elimination inducts on the hidden lookup index. At zero,
   `list_at_head_iff` identifies the value with the outer head. At a successor,
   `list_at_succ_iff` moves the lookup to the tail.
3. Unique lookup first constructs a value with `list_at_exists`, then compares
   any competing value with `list_at_functional`.
4. Extensional equality proves the easy direction by lookup functionality and
   the hard direction with K3B's `cell_list_extensional` theorem.
5. Unique decomposition exposes one cell from a successor length and uses
   exact-cell functionality to identify every competing head and tail.

No proof uses excluded middle, double-negation elimination, choice, a trusted
solver, or equality of raw beta-history codes.

### One complete native proof body

Here is the exact tactic sequence of `list_at_exists_unique`, with the single
long `have` type rendered through its readable `ListAt` name. Its two declared
dependencies are introduced as local hypotheses by the body checker. The
later empty-context compiler must replace those hypotheses with their checked
certificates through `Cut` nodes.

```text
intro z
intro l
intro i
intro hlength
intro hbound
have hexists : exists a. ListAt(z,i,a)
specialize list_at_exists z
specialize list_at_exists l
specialize list_at_exists i
apply list_at_exists
exact hlength
exact hbound
cases hexists
exists x
split
exact hexists_witness
intro d
intro hlookup_d
specialize list_at_functional z
specialize list_at_functional i
specialize list_at_functional d
specialize list_at_functional x
apply list_at_functional
exact hlookup_d
exact hexists_witness
```

The displayed `ListAt` in the `have` line is the readable version. The source
factory substitutes its complete conservative expansion before parsing, so
the kernel sees no `ListAt` constant.

## Exact body receipts

Each tuple below is

```text
(direct dependencies, tactic commands, proof nodes, depth,
 distinct proof objects, proof-DAG edges, reused objects)
```

| Theorem | Receipt |
|---|---:|
| `cell_list_valid_nil` | `(1,4,5,5,5,4,0)` |
| `cell_list_valid_cell_intro` | `(1,18,19,13,19,18,0)` |
| `cell_list_valid_cases` | `(2,35,41,22,41,40,0)` |
| `cell_list_valid_cell_elim` | `(3,33,56,23,56,55,0)` |
| `list_at_implies_cell_list_valid` | `(1,14,15,11,15,14,0)` |
| `list_member_implies_cell_list_valid` | `(1,9,21,13,21,20,0)` |
| `list_member_nil_false` | `(5,33,41,19,41,40,0)` |
| `list_member_cell_intro_head` | `(1,18,19,13,19,18,0)` |
| `list_member_cell_intro_tail` | `(1,20,21,15,21,20,0)` |
| `list_member_cell_elim` | `(3,77,100,41,100,99,0)` |
| `list_member_cell_iff` | `(3,32,79,23,79,78,0)` |
| `list_member_pointwise_transport` | `(2,37,71,25,71,70,0)` |
| `list_at_exists_unique` | `(2,25,30,19,30,29,0)` |
| `cell_list_nonempty_iff_head_exists` | `(2,38,46,14,46,45,0)` |
| `cell_list_code_eq_lookup_values` | `(1,17,40,24,40,39,0)` |
| `cell_list_code_eq_iff_pointwise` | `(2,30,62,29,62,61,0)` |
| `cell_list_decompose_unique` | `(2,29,36,22,36,35,0)` |

The largest authored body has only 100 structural proof nodes. That is not an
empty-context size estimate: closing a row embeds its dependency certificates
through checked `Cut` sharing. A local capacity preflight closed the five
semantic-interface rows; the largest was 160,934 structural occurrences at
depth 89. Those ephemeral numbers guide capacity planning but do not replace
the pending sealed receipt.

## The next gate: append and prefix restriction

The interface was chosen to support a canonical next definition:

$$
\begin{aligned}
\operatorname{CellListAppend}(x,y,z) :\!\Longleftrightarrow
\exists \ell,m\;(&\operatorname{CellListLen}(x,\ell)\land
\operatorname{CellListLen}(y,m)\land
\operatorname{CellListLen}(z,\ell+m)\land{}\\
&[\forall i,a\;\operatorname{ListAt}(x,i,a)\to
                 \operatorname{ListAt}(z,i,a)]\land{}\\
&[\forall j,a\;\operatorname{ListAt}(y,j,a)\to
                 \operatorname{ListAt}(z,\ell+j,a)]),
\end{aligned}
$$

followed by exact prefix restriction

$$
\operatorname{CellListRestrict}(z,k,w)
:\!\Longleftrightarrow
\operatorname{CellListLen}(w,k)\land
\exists r\;\operatorname{CellListAppend}(w,r,z).
$$

Append existence will recurse through `cell_list_decompose_unique`; append
functionality will compare the two results with
`cell_list_code_eq_iff_pointwise`; restriction will then become a prefix
factorization rather than a second competing representation.

## Sources and reproduction

- [representation RFC](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/research/arithmetic-library/ha-cell-list-validity-membership-rfc-v1.md)
- [definition surface](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_cell_list_membership_surface_candidate.py)
- [validity proofs](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_cell_list_validity_candidate.py)
- [membership proofs](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_cell_list_membership_candidate.py)
- [semantic-interface proofs](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/peano_lab/library/ha_cell_list_interface_candidate.py)
- [exact proof audit](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/peano-lab/py/tests/test_ha_cell_list_membership_candidate.py)
- [cold-closure runner](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/scripts/run_wmi_k3c_cell_list_closure.py)
- [reviewed WMI job wrapper](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/slurm/peano_wmi_k3c_cell_list_closure.sbatch)

From the repository root:

```bash
PYTHONPATH=peano-lab/py python3 -m pytest -q \
  peano-lab/py/tests/test_ha_cell_list_membership_surface_candidate.py \
  peano-lab/py/tests/test_ha_cell_list_membership_candidate.py
make peano-library-alpha-v2-check
```

Continue backward to {doc}`K3B cell histories and lookup
<cell-history-and-lookup>`, or forward to the append/restriction design in the
linked RFC.
