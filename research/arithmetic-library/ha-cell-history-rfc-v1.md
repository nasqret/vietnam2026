# RFC HA-K3B-CELLHISTORY-1: CRT-backed reverse cell histories

**Status:** representation and first ten obligations frozen; all eight theorem
rows are private `closed_checked_candidate` evidence; no public admission

**Layer:** `K3B`, a post-K4/M3 bridge; **not** part of strict K3

**Object language:** first-order intuitionistic arithmetic over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

## 1. Decision and layer amendment

Uniform lists will be represented by a beta-coded computation history of
successor-tagged doubled-Cantor cells.  This selects resolution 3 of the
uniform-list blocker in
[`HA-K3-PAIR-1`](ha-canonical-pair-cell-rfc-v1.md): scalar division and binary
CRT are established first, and the already checked bounded beta-prefix
machinery is then used to encode variable-length cell traces.

This decision does not change the strict-K3 evidence boundary.  Strict K3
remains exactly **96 private rows across 21 modules**:

- 74 canonical signed-natural rows; and
- 22 doubled-Cantor pair and exact-D06 cell rows.

Those rows remain independent of division, remainder, beta coding, CRT,
classical logic, and DNE.  The new `K3B` name means “finite-data bridge used
after K4/M3”; it is not a claim that the theorems below satisfy the original
strict-K3 dependency quarantine.

The refined dependency order is:

```text
K0--K2 arithmetic/order          strict K3 pair/cell API (96 rows)
             |                              |
             +--------------+---------------+
                            |
K4 scalar division ---------+--------- M3 scalar binary CRT
                            |                  |
                            +---------+--------+
                                      |
                         BetaAt + beta_prefix_extend
                                      |
                            K3B reverse CellHistory
                                      |
                              CellListLen / ListAt
                                      |
                            K6 finite folds and M4
```

The broad planning edge from K3 to M3 is therefore refined at proof level:
the scalar binary-CRT closure used here must not depend on `K3B`, `ListAt`, a
finite fold, or any theorem downstream of them.  There is no theorem
dependency cycle.

## 2. Existing exact primitives

All names in this RFC are untrusted authoring abbreviations.  They expand to
the unchanged object language before parsing and before kernel checking.

The checked beta convention is exactly

```text
BetaAt(b,c,i,a) :=
  ((exists H. H + S (a) = S ((S (i)) * c)) /\
   exists Q. b = Q * S ((S (i)) * c) + (a))
```

Thus the modulus at index `i` is
\(S((S(i))c)=1+(i+1)c\), and `a` is both below that modulus and the displayed
remainder of `b`.  This is the convention implemented by
[`finite_fold_surface.beta_at`](../../peano-lab/py/peano_lab/library/finite_fold_surface.py).

The strict bound and exact D06 cell relation are

```text
Lt(i,l) := exists gap. gap + S i = l

Cell(u,h,t) :=
  u = S ((h + t) * S (h + t) + (t + t))
```

`Cell` is functional in `h,t`, and both components are strictly below `u`, by
the private strict-K3 pair/cell tranche.  None of these displayed names is a
new predicate symbol in the kernel.

## 3. Exact reverse definitions

### D01 `CellHistory(z,l;b,c)`

The association of conjunctions and the order `t u h` of the edge witnesses
are normative:

```text
CellHistory(z,l;b,c) :=
  BetaAt(b,c,0,0) /\
  (BetaAt(b,c,l,z) /\
   forall i. Lt(i,l) -> exists t u h.
     BetaAt(b,c,i,t) /\
     (BetaAt(b,c,S i,u) /\ Cell(u,h,t)))
```

This is a **reverse construction trace**:

- entry `0` is the nil code `0`;
- entry `l` is the represented list code `z`; and
- an edge from entry `i=t` to entry `S i=u` records `u=Cell(h,t)`.

The orientation is essential.  The public theorem `beta_prefix_extend`
preserves every old entry below its append index and adds the new value at
that index.  To extend a history of length `l`, it is invoked at `S l`; it
preserves indices `0,...,l` and appends the new cell code at `S l`.

### D02 `CellListLen(z,l)`

```text
CellListLen(z,l) := exists b c. CellHistory(z,l;b,c)
```

Raw beta-code equality is deliberately hidden.  Many pairs `b,c` can encode
the same finite trace, so list identity is the terminal cell code `z`, not
identity of history witnesses.

### D03 Canonical expansion receipt

The authoring implementation is
[`ha_cell_history_candidate.py`](../../peano-lab/py/peano_lab/library/ha_cell_history_candidate.py).
For the canonical calls

```python
beta_at("b", "c", "i", "x", tag="rfc_v1")
cell_history("z", "l", "b", "c", tag="rfc_v1")
cell_list_len("z", "l", tag="rfc_v1")
```

the fully expanded strings have these receipts:

| Expansion | UTF-8 characters | Formula constructors | Full AST nodes | SHA-256 |
|---|---:|---:|---:|---|
| `BetaAt(b,c,i,x)` | 172 | 5 | 24 | `17706704196c2088288197f9d1a1bbd9c692e863f29a2e9a01abdb1252c3d243` |
| `CellHistory(z,l;b,c)` | 1,278 | 32 | 129 | `3bd6cd64446b6acec60b2106296d12fbafe781e9caa61246835ebfb8315b6e0b` |
| `CellListLen(z,l)` | 1,885 | 34 | 131 | `662411fc848c5f8e5daf438fd72fa195fba44d8301f448d9be750ab016bcc026` |

The architecture prototype used short binders and measured 671 characters
and 32 formula constructors for D01.  Hygienic role-bearing binder names make
the canonical implementation string longer without changing its 32-node
formula skeleton.  Parsing confirms that its `BetaAt` subformulas are
alpha-equivalent to the existing checked helper.  Tags may rename generated
binders, but must not change the parsed formula up to alpha-equivalence.

## 4. The first ten deliverables

The following order is normative.  Definitions count as the first two
deliverables because their exact expansion is itself an admission artifact.

| No. | Deliverable | Exact surface contract | Principal ingredients |
|---:|---|---|---|
| 1 | `CellHistory` exact definition | D01 above | `BetaAt`, `Lt`, exact D06 `Cell` |
| 2 | `CellListLen` wrapper | D02 above | existentially hide beta witnesses |
| 3 | `cell_history_nil` | `CellHistory(0,0;0,0)` | direct `BetaAt(0,0,0,0)` witnesses and vacuity of `Lt(i,0)` |
| 4 | `cell_history_extend` | `forall b c l t u h. CellHistory(t,l;b,c) -> Cell(u,h,t) -> exists b2 c2. CellHistory(u,S l;b2,c2)` | `beta_prefix_extend` at `S l`, bounded successor split |
| 5 | `cell_history_succ_elim` | `forall b c l u. CellHistory(u,S l;b,c) -> exists t h. Cell(u,h,t) /\ CellHistory(t,l;b,c)` | instantiate the final edge and restrict the same prefix |
| 6 | `cell_list_zero_iff_nil` | `forall z. ((CellListLen(z,0) -> z = 0) /\ (z = 0 -> CellListLen(z,0)))` | `beta_at_unique`, nil history |
| 7 | `cell_list_succ_iff_cell` | conjunction of the two implications displayed below | deliverables 4--5 |
| 8 | `cell_list_length_functional` | `forall z l m. CellListLen(z,l) -> CellListLen(z,m) -> l = m` | list-length induction, nil/cell separation, cell functionality |
| 9 | `cell_list_length_le_code` | `forall z l. CellListLen(z,l) -> exists k. k + l = z` | strict cell-tail descent and order transitivity |
| 10 | `cell_list_length_total` | `forall l. exists z. CellListLen(z,l)` | induction, nil seed, exact zero-head cell, history extension |

The exact contract for deliverable 10 is

```text
forall l. exists z. CellListLen(z,l)
```

The exact contract for deliverable 7 is

```text
forall z l.
  ((CellListLen(z,S l) ->
      exists t h. Cell(z,h,t) /\ CellListLen(t,l)) /\
   ((exists t h. Cell(z,h,t) /\ CellListLen(t,l)) ->
      CellListLen(z,S l)))
```

The phrases “if and only if” and “equivalence” below are informal.  Native PA
has no `Iff` constructor and accepts no `<->` syntax; each such contract is
the displayed conjunction of two implications.

“Total” here means that every natural length is inhabited by some valid list
code.  The constructive proof may choose the canonical all-zero list at each
length.  It must **not** be confused with
`forall z. exists l. CellListLen(z,l)`: doubled-Cantor cell codes are
intentionally sparse, and an arbitrary natural need not be nil or a valid
cell chain.  Unique length on the valid-code domain is the useful derived
helper `cell_list_valid_length_unique`, obtained by unpacking a validity
witness and applying deliverable 8.

Surface names in this table expand before parsing.  Native theorem
statements must contain the fully expanded formulas, not uninterpreted
`CellHistory`, `CellListLen`, `Lt`, `Cell`, or `BetaAt` symbols.

## 5. Expected proof architecture

### 5.1 Nil and extension

`cell_history_nil` chooses trace code and scale `0,0`.  The beta modulus at
index zero is then one, so direct zero witnesses prove `BetaAt(0,0,0,0)` in
both endpoint positions.  The edge obligation assumes `Lt(i,0)`, obtains
`S i=0`, and contradicts successor nonzeroness constructively.

For `cell_history_extend`, apply

```text
beta_prefix_extend (S l) b c u
```

so every old value at an index below `S l`, including the old terminal at
`l`, is preserved.  For an edge index below `S l`, the discrete successor
split gives either `i=l`, discharged by the supplied `Cell(u,h,t)`, or
`i<l`, discharged by the old history after transporting its two beta values.

### 5.2 Successor elimination

Given a history ending at `S l`, instantiate its universal edge at `i=l`.
`beta_at_unique` identifies the edge successor with the terminal code `u`.
The current edge value becomes the terminal value for the restricted prefix;
all earlier edges are reused with the same `b,c`.  No new CRT construction is
needed in this direction.

### 5.3 Length uniqueness and descent

The zero/successor list equivalences expose an ordinary induction on length.
The mixed zero/successor case contradicts `nil_not_cell`.  In the
successor/successor case, exact-D06 cell functionality identifies both tails,
and the induction hypothesis identifies their predecessor lengths.

For the bound, `Cell(z,h,t)` gives `t<z`; the induction hypothesis gives
`l<=t`; successor monotonicity and transitivity give `S l<=z`.  This proves a
visible decreasing measure for every recursive client of `CellListLen`.

### 5.4 Length inhabitation

`cell_list_length_total` inducts on the requested length, not on a purported
list code.  At zero it existentially hides the witnesses from
`cell_history_nil`.  At `S l`, unpack the induction hypothesis, construct the
exact D06 cell with head zero and the old list code as tail, and apply
`cell_history_extend`.  This produces an all-zero list of every natural
length without deciding whether any arbitrary input code is valid.

### 5.5 Internal helpers

The proof factories may isolate the following conveniences without changing
the ten-item public ladder:

```text
cell_history_endpoint_unique
cell_history_edge_functional
cell_history_prefix_restrict
cell_history_one
cell_list_valid_length_unique
```

Each helper remains subject to the same dependency firewall and receipt
requirements.  It is not evidence of a larger list API by name alone.

### 5.6 Body-checked implementation checkpoint

The eight theorem rows in the complete first-ten ladder (after the two
definition rows) are implemented privately in
[`ha_cell_history_candidate.py`](../../peano-lab/py/peano_lab/library/ha_cell_history_candidate.py)
and
[`ha_cell_list_equations_candidate.py`](../../peano-lab/py/peano_lab/library/ha_cell_list_equations_candidate.py),
with the three length endpoints in
[`ha_cell_list_length_functional_candidate.py`](../../peano-lab/py/peano_lab/library/ha_cell_list_length_functional_candidate.py),
[`ha_cell_list_length_bound_candidate.py`](../../peano-lab/py/peano_lab/library/ha_cell_list_length_bound_candidate.py),
and
[`ha_cell_list_length_total_candidate.py`](../../peano-lab/py/peano_lab/library/ha_cell_list_length_total_candidate.py).
Their focused audits are deliberately split from the expensive recursive
public-library closure.  The body tuple below is
`(dependencies, commands, nodes, depth, objects, edges, reused)`.

| Row | Statement SHA-256 | Dependency-curried body receipt | Empty-context status |
|---|---|---|---|
| `cell_history_nil` | `18568ecbb4bcc3f923c504be74f4933a2b4f79e5d21751a1791715449374de37` | `(2,24,135,18,135,134,0)` | `closed_checked_candidate` |
| `cell_history_extend` | `50e26cefb18371aed02b5c926757bbfc22a007a51b995aafd3675c9a960bf407` | `(5,86,122,36,122,121,0)` | `closed_checked_candidate` |
| `cell_history_succ_elim` | `2f44b8405bb60e1571452cdae993c024c80cb079be6ded25edd58716888ecdee` | `(3,43,59,23,59,58,0)` | `closed_checked_candidate` |
| `cell_list_zero_iff_nil` | `bef9e900318713718a2e981eb04de28fb21e4641ff4f80c2a98b1dc41af2db29` | `(2,24,33,16,33,32,0)` | `closed_checked_candidate` |
| `cell_list_succ_iff_cell` | `bb678323c7061f561ce69bb0357bf93ece948acf763503eec4763934cf50b23c` | `(2,38,51,19,51,50,0)` | `closed_checked_candidate` |
| `cell_list_length_functional` | `e08563402824e2af98ac5fcd56065b173da4713dd33ab96ec16fb6fc5346b8e3` | `(5,119,163,42,163,162,0)` | `closed_checked_candidate` |
| `cell_list_length_le_code` | `48af1df5e7ca96895308b04b48ed154ed33399424d19a38b7cb18841ac12a08a` | `(5,43,49,22,49,48,0)` | `closed_checked_candidate` |
| `cell_list_length_total` | `8e6cea3fc40ffe051e4e3eb8af5b698e087c0f3d798fcfc628a107db1b09d765` | `(3,22,58,32,58,57,0)` | `closed_checked_candidate` |

WMI job `219203` closed every row twice from the empty context, with identical
receipts on both passes.  The tuple order below is
`(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)`:

| Row | Exact closed receipt |
|---|---|
| `cell_history_nil` | `(155,18,155,154,0,2,a3038bd67616f11f8e97727c98f03af09aacde863a70637d9575e2ff9d337ff8)` |
| `cell_history_extend` | `(29352,81,4651,4879,229,241,370de792b2c3fed8b3d36f90147c426b846d15578cac8c66520a59df81750c78)` |
| `cell_history_succ_elim` | `(1245,60,772,810,39,27,e8aee67cfef618fde3b08d48dffb4a6b31cdd22a578e38206d4e5a20a96c338c)` |
| `cell_list_zero_iff_nil` | `(1309,60,880,916,37,26,f7fdef58a28a86bd70b133bf839f6b49526817e020da6c698b85b3cd369f2f73)` |
| `cell_list_succ_iff_cell` | `(30648,83,4761,4992,232,246,a64ad8e5095d50afe10b47b1036ad9b680ab82462b41beb115d23956f9fa5699)` |
| `cell_list_length_functional` | `(34732,85,5700,5976,277,299,5dd0e4b8f585990ec826ba5ef02960cb6817f0aec5edcb86c9bb1e22d44c5a6c)` |
| `cell_list_length_le_code` | `(31002,84,4891,5129,239,257,50fe47364958e1a506315935796e517f41ddd947a1792fcdb134956ba05290a9)` |
| `cell_list_length_total` | `(29569,84,4848,5078,231,246,2d6063d54e16c0f093aab270329bdd4ca5a7c02aa68b528c2c7c771945ccba17)` |

Every certificate contains zero DNE.  The authoritative
[`ha-k3b-cell-history-closure-219203.json`](../../artifacts/peano-library/ha-k3b-cell-history-closure-219203.json)
has SHA-256
`6ef49fcb5edb2b1c5478ff592c97dc9af56ed2f79ec03308c5ebf341833b825c`.
It binds clean commit `0b33b6675481a93d0e330987b22d9ef91564a0a0` to payload
`edf77bff5cf824cbfd549179f8cef2a18ac65904d473ce3bbd2bd5e5f1c95620`
(3,911,680 bytes, 201 entries).  Scheduler job `219203` completed on `c3n1`
with state/exit `COMPLETED 0:0` in `00:04:46` and `MaxRSS=82428K`.

## 6. Dependency firewall

### 6.1 Permitted dependencies

The transitive closure may contain only:

- K0--K2 intuitionistic logic, equality, arithmetic, order, cancellation,
  bounded successor splits, and formula-specific induction;
- the exact strict-K3 D05/D06 pair/cell API, especially `nil_not_cell`,
  `cell_functional`, `cell_head_functional`, `cell_tail_functional`, and
  strict head/tail descent;
- reviewed K4 scalar division/remainder, gcd, balanced Bezout, coprimality,
  and bounded arithmetic needed by the beta representation;
- reviewed M3 **scalar binary** CRT and its coprime fold step;
- `beta_at_exists`, `beta_at_unique`, the exact beta bounds, and
  `beta_prefix_extend`; and
- proof sharing through checked `Cut` nodes.

`beta_prefix_extend` is whitelisted as one reviewed endpoint, but its entire
closed dependency DAG must still pass the no-cycle audit.

The pre-implementation audit finds 101 names in that transitive closure.  It
contains the permitted scalar division/remainder, gcd/Bezout, coprimality,
and binary-CRT machinery, but no list, lookup, finite fold, product, sum,
range, factorization, or quadratic-reciprocity theorem.  Its current closed
receipt is 29,057 proof occurrences at depth 80, with 4,508 unique objects,
4,732 DAG edges, and 225 reused objects.  The composed extension theorem must
be profiled again rather than assuming this baseline receipt will remain
within every downstream limit.

### 6.2 Forbidden dependencies

The closure must reject:

- any existing `List`, `ListAt`, `Map`, matrix, permutation, finite-function,
  `Product`, `Sum`, `Range`, `Repeat`, or finite-fold theorem;
- M4 finite CRT, a finite generalized-CRT fold, or a theorem whose proof
  already quantifies over a coded list of congruences;
- factorization, FTA, Wilson, Fermat, Euler, Gauss, or quadratic-reciprocity
  theorems that consume beta-coded finite data;
- an external list type, host-language recursion presented as a proof,
  unchecked `%`/division computation, or raw equality of beta codes; and
- `DNE`, excluded middle beyond a separately proved decidable proposition,
  choice, sorry, admission, or a trusted solver result.

The semantic oracle may test finite examples, but it is never a theorem
dependency.

## 7. Admission gates

The tranche is accepted only when all of the following gates pass.

### G0 — representation freeze

- D01 and D02 parse after full expansion.
- Their free-variable tables contain exactly the displayed parameters.
- The conjunction association, reverse edge orientation, and witness order
  `t u h` match Section 3.
- Canonical string hashes and AST metrics match the D03 receipts.
- Adversarial tags and colliding identifiers are rejected or expanded
  hygienically.
- Every generated `BetaAt` is alpha-equivalent to the existing helper.

### G1 — seed closure

- the unconditional `CellHistory(0,0;0,0)` seed closes twice from the empty
  context with identical
  statement, body, certificate, and DAG receipts.
- The impossible-edge branch uses constructive successor nonzeroness.
- A mutation replacing the zero endpoint by a successor fails.

### G2 — extension closure

- The proof calls `beta_prefix_extend` at exactly `S l`, not `l`.
- Both the old endpoint and all old edges are preserved.
- The new final edge has the supplied exact D06 orientation
  `Cell(u,h,t)`.
- Empty and one-cell bounded semantic cases agree with the expanded formula.

### G3 — elimination closure

- The final edge is extracted by the native `Lt(l,S l)` witness.
- `beta_at_unique` identifies the edge endpoint with the displayed terminal.
- Prefix restriction reuses the same beta witnesses and does not invoke
  choice or a fresh CRT construction.

### G4 — list equations

- Both directions of the zero and successor equivalences close.
- Nil/cell and reversed-cell mutations are rejected.
- The one-cell instance reduces to `Cell(z,h,0)` as expected.

### G5 — functionality, measure, and inhabitation

- Length functionality and `length<=code` close by object-level induction.
- The mixed zero/successor branch uses exact nil/cell separation.
- The successor branch uses exact cell functionality and strict tail descent.
- Length inhabitation closes by induction using the zero-head exact-D06
  constructor and history extension.
- Nearby false claims `l=z`, `z<l`, and unconditional validity of every
  natural fail.

### G6 — logical and resource audit

- Every theorem checks through the ordinary intuitionistic entry point.
- Every certificate contains zero `DNE` nodes.
- No kernel, parser, proof-node, or live-proof limit is raised merely to make
  the tranche pass.
- All formulas and closed proof DAGs fit the existing reviewed limits.

### G7 — quarantine and admission

- The transitive closure satisfies Section 6, including the scalar-CRT
  no-cycle refinement.
- Strict K3 still reports exactly 96 rows across 21 modules after integration.
- Focused tests, campaign structural validation, generated integration, and
  independent heavy replay all pass.
- Public admission, if desired, is a separate reviewed commit with explicit
  registry, catalog, snapshot, Book, and explorer receipts.

G1--G6 pass for the frozen first-ten tranche.  G7's dependency-quarantine and
closure audit passes, but its optional public-admission action was deliberately
not performed.  All eight rows therefore remain private, unregistered,
unadmitted `closed_checked_candidate` evidence.  Strict K3 remains 96 rows
across 21 modules, and the campaign JSON remains unchanged at 95 public
references, 121 private candidates, and 169 receipts.  Closure does not imply
that lists, lookup, folds, or finite CRT have been admitted.

## 8. Next batch after the ten-item gate

The follow-on
[`HA-K3B-LISTAT-1`](ha-cell-list-lookup-rfc-v1.md) now freezes the exact
outer-head `ListAt` definition and its ten-deliverable proof architecture.
Only that definition and its lightweight structural/semantic evidence exist
at the current checkpoint; no lookup theorem is body-checked or closed. Its
first proof obligation is a strengthened history extension that exposes
pointwise preservation of the old beta prefix. After the lookup equations,
existence, functionality, representation independence, and list
extensionality close, later RFCs should add:

1. interoperability between reverse cells and the legacy beta value surface;
2. list append/restriction and representation-independent induction; and
3. `Product` and `Sum` folds over `CellListLen` data.

Only after that API closes should K6 finite combinatorics or M4 finite CRT be
rebased onto canonical cell lists.  Existing beta-coded finite-fold theorems
remain mathematical guidance, not dependencies of this foundational bridge.
