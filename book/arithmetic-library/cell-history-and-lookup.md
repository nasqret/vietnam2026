# Cell histories and extensional lookup

This chapter is the readable front end to the private K3B finite-data bridge.
It represents a finite list by its terminal doubled-Cantor cell code and uses a
Gödel-β computation history to witness how that code was built.  The resulting
`ListAt` relation has the expected outer-head equations, unique values, and an
extensionality theorem—without adding lists, projections, division, or a
function-valued lookup to the Peano term grammar.

```{admonition} Closed candidate evidence is not public admission
:class: important
WMI job **219217** checked all seventeen selected theorem candidates twice
from the empty context.  Both passes were deterministic and every resulting
certificate contains zero uses of double-negation elimination.  These rows are
still private `closed_checked_candidate` evidence: they are unregistered,
unadmitted, and absent from the 432-theorem public runtime and its permanent
`PA`/`PD` tag spaces.  The graph below uses descriptive names, not public
theorem identifiers.
```

<div class="pa-dashboard-metrics" aria-label="Private K3B closure metrics">
  <div><strong>17</strong><span>closed private rows</span></div>
  <div><strong>2</strong><span>deterministic cold passes</span></div>
  <div><strong>95,253</strong><span>largest certificate</span></div>
  <div><strong>0</strong><span>DNE proof objects</span></div>
</div>

## Explore the direct dependencies

The embedded map starts in a deliberately sparse neighborhood view.  Click a
node to make it the focus; only its direct prerequisites and direct dependents
remain visible.  The full-map option still records only direct edges, and its
default arrow mode draws only edges incident to the selected node.  Yellow
hexagons are conservative definitions, blue rounded nodes are private
candidates or private support, and green rectangles are already-public
boundary lemmas.

<p>
  <a class="btn btn-primary" href="../_static/pa-proof-explorer/k3b/index.html?focus=cell_list_extensional&amp;view=neighborhood&amp;edges=focus">
    Open the K3B map in a full page
  </a>
</p>

<iframe
  src="../_static/pa-proof-explorer/k3b/index.html?focus=cell_list_extensional&amp;view=neighborhood&amp;edges=focus"
  title="Private K3B CellHistory and ListAt direct-dependency explorer"
  width="100%"
  height="900"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/pa-proof-explorer/k3b/index.html?focus=cell_list_extensional&amp;view=neighborhood&amp;edges=focus">Open the K3B map directly.</a>
  </p>
</iframe>

The solid arrows are proof dependencies and point from prerequisite to
dependent.  Dashed purple arrows are notation relationships.  They explain
which readable definitions occur in a statement; they never participate in a
proof path and add no logical premise.

## The unchanged arithmetic underneath

All the names in this section are authoring notation.  Each call is
hygienically expanded before the ordinary formula parser runs, and the kernel
receives only first-order formulas over

$$
0,\qquad S,\qquad +,\qquad \times,\qquad =.
$$

<span id="definition-lt"></span>
### Strict order

The development uses the ordinary gap representation

$$
i<l \quad:\!\Longleftrightarrow\quad
\exists g,\;g+S(i)=l.
$$

<span id="definition-beta-at"></span>
### Bounded β decoding

`BetaAt(b,c,i,a)` says that $a$ is the bounded remainder of $b$ at the
$i$th β modulus:

$$
\operatorname{BetaAt}(b,c,i,a)
\quad:\!\Longleftrightarrow\quad
\begin{cases}
\exists H,\;H+S(a)=S\bigl(S(i)c\bigr),\\
\exists Q,\;b=Q\,S\bigl(S(i)c\bigr)+a.
\end{cases}
$$

Thus the modulus is $1+(i+1)c$, and the first witness is the strict bound on
the remainder.

<span id="definition-cell"></span>
### Exact cells

The successor tag makes nil and every nonempty cell disjoint:

$$
\operatorname{Cell}(u,h,t)
\quad:\!\Longleftrightarrow\quad
u=S\!\left((h+t)S(h+t)+(t+t)\right).
$$

Here $h$ is the head, $t$ the tail code, and $u$ the resulting cell code.  The
private strict-K3 support proves constructor existence, functionality, and
strict descent of both components.

<span id="definition-cell-history"></span>
### Reverse construction histories

A history begins at nil, ends at the displayed code, and records one exact
cell at each adjacent β position:

$$
\begin{aligned}
\operatorname{CellHistory}(z,l;b,c) \quad:\!\Longleftrightarrow\quad
&\operatorname{BetaAt}(b,c,0,0)\\
{}\land{}&\operatorname{BetaAt}(b,c,l,z)\\
{}\land{}&\forall j<l\;\exists t,u,h,\;
  \operatorname{BetaAt}(b,c,j,t)\\
&\hspace{7.7em}\land\operatorname{BetaAt}(b,c,S(j),u)
  \land\operatorname{Cell}(u,h,t).
\end{aligned}
$$

The orientation is reverse only in the sense used by lookup: construction
edge $0$ is the innermost cell, while edge $l-1$ is the outermost cell.

<span id="definition-cell-list-len"></span>
### Semantic length

Raw β witnesses are intentionally hidden:

$$
\operatorname{CellListLen}(z,l)
\quad:\!\Longleftrightarrow\quad
\exists b,c,\;\operatorname{CellHistory}(z,l;b,c).
$$

Different pairs $(b,c)$ may encode the same finite trace.  The represented
list is identified by its terminal exact-cell code $z$, not by a chosen β
witness.

<span id="definition-history-at"></span>
### Selection inside one history witness

The local authoring abbreviation

$$
\begin{aligned}
\operatorname{HistoryAt}(l;b,c;i,a)
\quad:\!\Longleftrightarrow\quad
\exists j,t,u,\;&j+S(i)=l\\
{}\land{}&\operatorname{BetaAt}(b,c,j,t)\\
{}\land{}&\operatorname{BetaAt}(b,c,S(j),u)\\
{}\land{}&\operatorname{Cell}(u,a,t)
\end{aligned}
$$

selects edge $j$ by counting $i$ from the outside.

<span id="definition-list-at"></span>
### Extensional client lookup

Finally, `ListAt` existentially hides the history:

$$
\begin{aligned}
\operatorname{ListAt}(z,i,a)
\quad:\!\Longleftrightarrow\quad
\exists l,b,c,j,t,u,\;&\operatorname{CellHistory}(z,l;b,c)\\
{}\land{}&j+S(i)=l\\
{}\land{}&\operatorname{BetaAt}(b,c,j,t)\\
{}\land{}&\operatorname{BetaAt}(b,c,S(j),u)\\
{}\land{}&\operatorname{Cell}(u,a,t).
\end{aligned}
$$

The existential order $l,b,c,j,t,u$, right-associated conjunctions, and cell
orientation `Cell(u,a,t)` are frozen parts of the surface contract.  The
fully expanded call has 3,331 characters, 54 formula constructors, 210 total
PA syntax nodes, and SHA-256
`b83d91b6ec8e6b83fe637e1533c72beef54c7e7a4b41f1518bce8785cc9f11ce`.

## A concrete two-cell trace

Start with nil and construct heads $0$ and then $2$:

$$
0
\xrightarrow{\ h=0\ }
1
\xrightarrow{\ h=2\ }
15.
$$

Indeed, `Cell(1,0,0)` and `Cell(15,2,1)` both satisfy the exact polynomial.
The trace values $(0,1,15)$ are simultaneously decoded by the distinct β
witnesses $(b,c)=(1288,6)$ and $(3690,8)$.  Outer-head lookup therefore gives

$$
\operatorname{ListAt}(15,0,2),
\qquad
\operatorname{ListAt}(15,1,0).
$$

This fixture illustrates both orientations at once: construction proceeds
inner-to-outer, lookup counts outer-to-inner.  It also exposes why raw β-code
equality would be the wrong notion of list equality.

## The lookup ladder

The order below is the proof-engineering order, not just a presentation
order.  T01 is a definition and therefore has no proof certificate.  T02–T10
are included among the seventeen rows closed by job 219217.

| Rung | Deliverable | Mathematical role | Proof idea |
|---:|---|---|---|
| T01 | `ListAt` | conservative outer-head lookup relation | expand D01/D02 and hide all β witnesses |
| T02 | `cell_history_extend_preserves_prefix` | extend a history while retaining every old decoded entry | apply `beta_prefix_extend` at $S(l)$ |
| T03 | `list_at_domain` | expose a semantic length and prove $i<l$ | unpack the defining witnesses |
| T04 | `list_at_head_iff` | lookup at zero is exactly the outer head | eliminate the final edge and use β uniqueness |
| T05 | `list_at_succ_iff` | successor lookup is lookup in the tail | eliminate or extend one history edge |
| T06 | `list_at_external_bound` | move the hidden index bound to a supplied length | T03 plus length functionality |
| T07 | `list_at_exists` | every in-range index has an entry | instantiate the history edge clause |
| T08 | `list_at_functional` | a fixed code and index have one value | induction on $i$ using T04/T05 and cell functionality |
| T09 | `list_at_history_independent` | lookup does not depend on β witnesses | create two client lookups and apply T08 |
| T10 | `cell_list_extensional` | equal-length pointwise-equal lists have equal codes | induction on length using T04/T05 |

<span id="cell-history-extend-preserves-prefix"></span>
### T02 — prefix-preserving extension

```text
forall b c l t u h.
  CellHistory(t,l;b,c) -> Cell(u,h,t) ->
  exists b2 c2.
    CellHistory(u,S l;b2,c2) /\
    forall k x.
      (exists d. d + k = l) ->
      BetaAt(b,c,k,x) -> BetaAt(b2,c2,k,x)
```

Calling `beta_prefix_extend` at $S(l)$ preserves positions $0$ through $l$,
including both endpoints of every old lookup edge, and appends $u$ at the new
terminal position.

<span id="list-at-domain"></span>
### T03 — domain

```text
forall z i a.
  ListAt(z,i,a) ->
  exists l. CellListLen(z,l) /\ (exists k. k + S i = l)
```

This theorem is dependency-free after expansion: its proof is pure
definition elimination and repackaging.

<span id="list-at-head-iff"></span>
### T04 — the outer head equation

```text
forall z a.
  ((ListAt(z,0,a) ->
    exists t l. Cell(z,a,t) /\ CellListLen(t,l)) /\
   ((exists t l. Cell(z,a,t) /\ CellListLen(t,l)) ->
    ListAt(z,0,a)))
```

Native PA has no biconditional constructor, so the equation is a conjunction
of implications.  Forward reasoning identifies the selected edge with the
history's final edge by two applications of `beta_at_unique`; reverse
reasoning uses T02 to append the outer cell while preserving the tail prefix.

<span id="list-at-succ-iff"></span>
### T05 — the successor equation

```text
forall z i a.
  ((ListAt(z,S i,a) ->
    exists t h. Cell(z,h,t) /\ ListAt(t,i,a)) /\
   ((exists t h. Cell(z,h,t) /\ ListAt(t,i,a)) ->
    ListAt(z,S i,a)))
```

The forward direction restricts the same history to its predecessor.  The
reverse direction transports both endpoints of the selected old edge through
T02.  Only PA4 normalization and `add_comm` are needed to align the outer
index.

<span id="list-at-external-bound"></span>
### T06 — an external length bound

```text
forall z l i a.
  CellListLen(z,l) -> ListAt(z,i,a) ->
  exists k. k + S i = l
```

T03 returns a hidden length $m$; `cell_list_length_functional` proves $m=l$.

<span id="list-at-exists"></span>
### T07 — in-range existence

```text
forall z l i.
  CellListLen(z,l) -> (exists k. k + S i = l) ->
  exists a. ListAt(z,i,a)
```

The universal edge clause in `CellHistory` supplies the selected head.  The
proof uses no choice principle: it simply reuses the existential witnesses
already stored by the history relation.

<span id="list-at-functional"></span>
### T08 — lookup functionality

```text
forall z i a d.
  ListAt(z,i,a) -> ListAt(z,i,d) -> a = d
```

Induction on $i$ uses the head equation in the base case.  In the successor
case, cell functionality identifies the two predecessor codes, after which
the induction hypothesis compares the inner entries.

<span id="list-at-history-independent"></span>
### T09 — history-witness independence

```text
forall z l b c d e i a.
  CellHistory(z,l;b,c) -> CellHistory(z,l;d,e) ->
  HistoryAt(l;b,c;i,a) -> HistoryAt(l;d,e;i,a)
```

The result does not assert $(b,c)=(d,e)$.  It turns the selected edge in each
history into a `ListAt` witness and invokes T08, transporting only the decoded
head.

<span id="cell-list-extensional"></span>
### T10 — list extensionality

```text
forall z w l.
  CellListLen(z,l) -> CellListLen(w,l) ->
  (forall i a d.
    (exists k. k + S i = l) ->
    ListAt(z,i,a) -> ListAt(w,i,d) -> a = d) ->
  z = w
```

The induction base reduces both codes to nil.  At successor length, T04
compares the outer heads, T05 shifts the pointwise hypothesis to the two
tails, and the induction hypothesis identifies those tails.  Expanding the
exact cell polynomial then rewrites the two original codes to the same term.

<span id="closure-receipt"></span>
## The sealed closure receipt

The machine-readable artifact is
[`ha-k3b-listat-full-closure-219217.json`](https://github.com/nasqret/vietnam2026/blob/51f6e081a4aa1223bcdff7ff3ff0a662de8f9b08/artifacts/peano-library/ha-k3b-listat-full-closure-219217.json).
Its exact local byte identity is 10,550 bytes with SHA-256
`c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8`.
The artifact itself is sealed at commit
`51f6e081a4aa1223bcdff7ff3ff0a662de8f9b08`; it binds clean source commit
`cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e` to payload SHA-256
`78e0c3d04b98ba1788edce0cd227dae3f7fe36f391a3a80b962da632a1970835`.
The two passes ran under CPython 3.12.12 with `PYTHONHASHSEED=20260804` and the
fixed one-CPU, 32,768-MiB, four-hour `cpu_idle` resource envelope.

The tuple columns are exact structural occurrences, maximum depth, distinct
proof objects, proof-DAG edges, reused object references, and `Cut` objects.
Rows share large public dependency closures, so summing the node column does
not measure a single combined proof.

| Closed private row | Nodes | Depth | Objects | Edges | Reused | Cuts |
|---|---:|---:|---:|---:|---:|---:|
| `cell_history_nil` | 155 | 18 | 155 | 154 | 0 | 2 |
| `cell_history_extend` | 29,352 | 81 | 4,651 | 4,879 | 229 | 241 |
| `cell_history_succ_elim` | 1,245 | 60 | 772 | 810 | 39 | 27 |
| `cell_history_extend_preserves_prefix` | 29,369 | 81 | 4,668 | 4,896 | 229 | 241 |
| `cell_list_zero_iff_nil` | 1,309 | 60 | 880 | 916 | 37 | 26 |
| `cell_list_succ_iff_cell` | 30,648 | 83 | 4,761 | 4,992 | 232 | 246 |
| `cell_list_length_functional` | 34,732 | 85 | 5,700 | 5,976 | 277 | 299 |
| `cell_list_length_le_code` | 31,002 | 84 | 4,891 | 5,129 | 239 | 257 |
| `cell_list_length_total` | 29,569 | 84 | 4,848 | 5,078 | 231 | 246 |
| `list_at_domain` | 39 | 23 | 39 | 38 | 0 | 0 |
| `list_at_head_iff` | 32,025 | 83 | 4,982 | 5,225 | 244 | 248 |
| `list_at_succ_iff` | 30,885 | 83 | 4,923 | 5,157 | 235 | 247 |
| `list_at_external_bound` | 34,799 | 87 | 5,767 | 6,043 | 277 | 301 |
| `list_at_exists` | 133 | 26 | 127 | 132 | 6 | 3 |
| `list_at_functional` | 65,579 | 85 | 5,851 | 6,140 | 290 | 296 |
| `list_at_history_independent` | 65,823 | 86 | 6,022 | 6,312 | 291 | 298 |
| `cell_list_extensional` | 95,253 | 87 | 5,888 | 6,162 | 275 | 266 |

Every numerical row and every full statement, dependency-closure, and proof
DAG SHA-256 is retained in the JSON artifact.  The largest structural proof
still fits the unchanged live policy of 500,000 occurrences, 100,000 distinct
objects, and depth 256.

## Formal sources and focused audits

The WMI payload was built from the exact commit linked below.  Each source
contains the complete tactic tuple; each focused audit checks the frozen
statement, dependency order, body certificate, mutation boundaries, semantic
fixtures, registry isolation, and absence of DNE where applicable.

| Proof group | Complete tactic source | Focused audit |
|---|---|---|
| reverse histories | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_history_candidate.py#L309) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_history_candidate.py#L243) |
| prefix preservation | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_history_prefix_preservation_candidate.py#L79) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_history_prefix_preservation_candidate.py#L177) |
| nil/successor equations | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_equations_candidate.py#L62) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_equations_candidate.py#L120) |
| length functionality | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_length_functional_candidate.py#L62) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_length_functional_candidate.py#L124) |
| length bound and totality | [bound](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_length_bound_candidate.py#L33) · [total](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_length_total_candidate.py#L31) | [bound test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_length_bound_candidate.py#L116) · [total test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_length_total_candidate.py#L112) |
| T03 domain | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_lookup_domain_candidate.py#L27) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_lookup_domain_candidate.py#L109) |
| T04 head equation | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_lookup_head_candidate.py#L116) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_lookup_head_candidate.py#L190) |
| T05 successor equation | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_lookup_succ_candidate.py#L125) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_lookup_succ_candidate.py#L192) |
| T06 external bound | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_lookup_external_bound_candidate.py#L37) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_lookup_external_bound_candidate.py#L167) |
| T07 existence | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_lookup_exists_candidate.py#L66) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_lookup_exists_candidate.py#L161) |
| T08 functionality | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_lookup_functional_candidate.py#L64) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_lookup_functional_candidate.py#L183) |
| T09 history independence | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_lookup_history_independent_candidate.py#L157) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_lookup_history_independent_candidate.py#L229) |
| T10 extensionality | [candidate](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/peano_lab/library/ha_cell_list_extensional_candidate.py#L147) | [test](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/peano-lab/py/tests/test_ha_cell_list_extensional_candidate.py#L203) |

The two design contracts give the expanded definitions, exact witness order,
mutation policy, and proof architecture:

- [`HA-K3B-CELLHISTORY-1`](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/research/arithmetic-library/ha-cell-history-rfc-v1.md);
- [`HA-K3B-LISTAT-1`](https://github.com/nasqret/vietnam2026/blob/cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e/research/arithmetic-library/ha-cell-list-lookup-rfc-v1.md).

To reproduce the lightweight authoring boundary without replaying the large
closed certificates on a laptop, run:

```bash
make ha-k3b-cell-history-check
make ha-k3b-list-lookup-check
```

Those commands validate surfaces, body certificates, semantic fixtures, and
the sealed WMI receipts.  They deliberately do not register or admit a
theorem.  Any later promotion still requires the separate G1–G8 admission and
release review described in {doc}`Curating the next conservative edition
<curation>`.
