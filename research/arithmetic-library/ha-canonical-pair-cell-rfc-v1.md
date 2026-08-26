# RFC HA-K3-PAIR-1: doubled-Cantor pairs and successor-tagged cells

**Status:** constructor/injectivity/cell-functionality/descent core closed privately; no public admission

**Scope:** pair and single-cell component of K3/HA4  
**Logic:** first-order intuitionistic arithmetic over `0`, `S`, `+`, `*`, `=`  
**Public admission:** none

## 1. Decision

The first canonical pair representation is the doubled Cantor polynomial

\[
  \operatorname{pair}_2(x,y)
  =(x+y)(x+y+1)+2y.
\]

It is twice the usual Cantor pairing function. The factor of two removes every
division or hidden halving operation from the constructor. A cell is tagged by
one successor:

\[
  \operatorname{cell}(h,t)=S(\operatorname{pair}_2(h,t)).
\]

Thus `0` is the nil code and every constructed cell is nonzero. Both
constructors are literal polynomial terms in the frozen object language.

This RFC deliberately freezes only pairs and one-step cells. It does **not**
claim that pairing alone defines arbitrary-length lists.

## 2. Why this representation

For `s=x+y`, the code lies in the doubled triangular shell

\[
  s(s+1)\leq \operatorname{pair}_2(x,y)<S(s)S(S(s)).
\]

Within one shell, the offset is `2*y`. Different shells are disjoint, and
additive cancellation recovers `y`, then `x`. This gives a constructive route
to literal injectivity without division, remainder, CRT, Gödel-β coding, prime
factorization, or a square-root operation.

The codes are sparse: pair codes are even and cells are their successors. K3
requires functional decoding on valid codes and valid canonical constructors;
it does not require every natural to be a pair or cell code.

## 3. Exact expanded definitions

The following strings are normative. Each is already in the unchanged base
language. Names such as `PairCode` are readable macros only.

### D01 `PairCode(code,left,right)`

```text
code = (left + right) * S (left + right) + (right + right)
```

### D02 `PairValid(code)`

```text
exists left right. code = (left + right) * S (left + right) + (right + right)
```

### D03 `PairFirst(code,left)`

```text
exists right. code = (left + right) * S (left + right) + (right + right)
```

### D04 `PairSecond(code,right)`

```text
exists left. code = (left + right) * S (left + right) + (right + right)
```

### D05 `Nil(code)`

```text
code = 0
```

### D06 `Cell(code,head,tail)`

```text
code = S ((head + tail) * S (head + tail) + (tail + tail))
```

### D07 `CellValid(code)`

```text
exists head tail. code = S ((head + tail) * S (head + tail) + (tail + tail))
```

### D08 `MapEntry(entry,key,value)`

```text
entry = (key + value) * S (key + value) + (value + value)
```

`MapEntry` supplies only one key/value entry. It does not define a finite map.

## 4. Template identity receipts

Hashes are SHA-256 of the exact UTF-8 strings in Section 3, without a trailing
newline.

| ID | SHA-256 |
|---|---|
| `HA-K3-PAIR-D01` | `4a1f7584e17e14e5895e51feefb6083707c52d080277000a423af9edb75fc3a1` |
| `HA-K3-PAIR-D02` | `b4ccb897c33781d571f092f9fbce98963fedeab1733b7755e7622c8dcaef8bb5` |
| `HA-K3-PAIR-D03` | `934ba249236665486bc18c7d734f04a6b126793a4d0a3a2371476d62200b5762` |
| `HA-K3-PAIR-D04` | `ee497668c0a9e865d52102fd0bb2840154494df13984cc3d77a165a77458024b` |
| `HA-K3-PAIR-D05` | `90dfaef5b4215cce02fe969e7a5c252e963bd35509fc68e9116277c0928fd3d6` |
| `HA-K3-PAIR-D06` | `43b3520acd7e6b372169fe2e9636b72214359ee09c432181d38eb741ddb69e34` |
| `HA-K3-PAIR-D07` | `7313b358853482a4b4254bee45fa7bced9921cc3af56cc357eed877831e9e173` |
| `HA-K3-PAIR-D08` | `9d7cee278c784dd602f815c4feb3e3155953e91beeab3a358fbd85c6b05e1aab` |

These are definition receipts, not theorem or admission receipts.

## 5. Required theorem ladder

### 5.1 Doubled-triangular shell arithmetic

The proof should first expose small reusable facts, provisionally named:

```text
dt_shell_successor
dt_shell_monotone
dt_right_le_shell
dt_pair_shell_lower
dt_pair_below_next_shell
dt_pair_shell_separated
```

They establish the shell bounds, strict separation of different `left+right`
values, and cancellation of the doubled right offset.

### 5.2 Pair API

The core obligations are:

```text
pair_code_constructor
pair_code_output_functional
pair_code_injective
pair_first_functional
pair_second_functional
pair_constructor_valid
pair_component_bounds
pair_code_even
```

The central statements have the shapes

```text
forall left right. exists code. PairCode(code,left,right)
```

and

```text
forall code left1 right1 left2 right2.
  PairCode(code,left1,right1) -> PairCode(code,left2,right2) ->
  left1 = left2 /\ right1 = right2
```

The first proof chooses the displayed polynomial and closes by reflexivity.
The second must be an object-level shell/injectivity proof. A host-language
Cantor decoder is only a semantic oracle.

`pair_valid_decidable` is deferred until its exact bounded-search dependencies
are selected. Universal decoding of all even naturals is useful but is not a
prerequisite for the constructor/injectivity core.

### 5.3 Cell API

After pair injectivity:

```text
cell_constructor
cell_nonzero
cell_functional
nil_not_cell
cell_head_functional
cell_tail_functional
cell_head_lt_code
cell_tail_lt_code
```

The strict component bounds are important: any later recursion on a valid
cell tail must visibly descend in the natural code.

### 5.4 Closed private proof-API checkpoint

The private proof API is implemented in five isolated factories:

- [`ha_pair_cell_seed_candidate.py`](../../peano-lab/py/peano_lab/library/ha_pair_cell_seed_candidate.py)
  provides seven literal constructor and nil/cell-boundary rows;
- [`ha_pair_shell_candidate.py`](../../peano-lab/py/peano_lab/library/ha_pair_shell_candidate.py)
  provides six doubled-triangular shell rows;
- [`ha_pair_injective_candidate.py`](../../peano-lab/py/peano_lab/library/ha_pair_injective_candidate.py)
  provides self-doubling cancellation and exact D01 component injectivity;
- [`ha_cell_functional_candidate.py`](../../peano-lab/py/peano_lab/library/ha_cell_functional_candidate.py)
  transfers that injectivity through the exact D06 successor tag and projects
  head and tail functionality; and
- [`ha_cell_bounds_candidate.py`](../../peano-lab/py/peano_lab/library/ha_cell_bounds_candidate.py)
  proves D01 component bounds and exact D06 strict head/tail descent.

Their focused audits are respectively
[`test_ha_pair_cell_seed_candidate.py`](../../peano-lab/py/tests/test_ha_pair_cell_seed_candidate.py),
[`test_ha_pair_shell_candidate.py`](../../peano-lab/py/tests/test_ha_pair_shell_candidate.py),
[`test_ha_pair_injective_candidate.py`](../../peano-lab/py/tests/test_ha_pair_injective_candidate.py),
[`test_ha_cell_functional_candidate.py`](../../peano-lab/py/tests/test_ha_cell_functional_candidate.py),
and
[`test_ha_cell_bounds_candidate.py`](../../peano-lab/py/tests/test_ha_cell_bounds_candidate.py).
Every row closes twice from the empty context with the same certificate DAG,
contains zero DNE, and fits the unchanged live/use limits. The receipt tuple
below is `(nodes,depth,objects,edges,reused,Cuts,certificate SHA-256)`.

| Candidate | Statement SHA-256 | Empty-context receipt |
|---|---|---|
| `pair_code_constructor` | `f34a905487d7eb61c3515cbd0b6555f264be2a99cf9c1a17029d4a8d4a714017` | `(4,4,4,3,0,0,1682a2eb02ee68612732e527260f82758260d96df5e4d1424d0a813d8c66bd39)` |
| `pair_code_output_functional` | `4e71c8cc7a39becc48cdf6f45ffce1d33bb4996a7201f8284a6aab40420d0d0a` | `(10,9,10,9,0,0,e2479e24af1b8b96209bcd65950895a8dcfe687a4803e8ef458f372ebed9327e)` |
| `pair_constructor_valid` | `51e11d9dfb235d5b4e1a75bc17649746de19467e270e177fef4a2affb1d96ebd` | `(5,5,5,4,0,0,d9f2c1c74b269be3d596004f77c80adbd841bce6841d9308a398702bcfad001d)` |
| `cell_constructor` | `e4cc27df174657acfd4515daebd353cb13828be9bbb3074bc1664d0d28c3b8a1` | `(4,4,4,3,0,0,4953e55da6c805b23447cbb1d4f1b7af5f2c42900e142d45838309ae75fae93b)` |
| `cell_nonzero` | `1b621236aa1d6fb0f6bd24bfb10180b864ab638bf830aeb65cc4a44a372006a1` | `(12,9,12,11,0,0,7a0247f36cd2dffe6812b0c49c8f49e4680b59ebceff29421012e2810f150d73)` |
| `nil_not_cell` | `3f9d2ff05aaca29e9df0d9c919b41ed3614a804a8d51119d912bda99a9536629` | `(35,15,35,34,0,1,4041048d66c132bfa7e8d6be1f58f1a5c9b1bb15a2539ad2e3a21730038d78de)` |
| `map_entry_constructor` | `e2606d6088e4613d59bcd97835f3da3e92bfba7718a01e163740345631c5062a` | `(4,4,4,3,0,0,1682a2eb02ee68612732e527260f82758260d96df5e4d1424d0a813d8c66bd39)` |
| `dt_shell_successor` | `4de65f84b31ef5ded138a85e9f57db9763c363ec7364e04f8b3cc5e4858f4b03` | `(363,24,228,258,31,7,52a39e68acc98d0c44c0b07c95f003eb6eff6ee8c4ca6e11adb9f9e275a03301)` |
| `dt_shell_monotone` | `64ebd7569b4923a6cd864404f8d4e4e727e9113b2125d5757e1b6718ceeb267b` | `(536,27,363,395,33,16,8fa6c58b51036c23d4bdfb6a3c58f8495d6d3ffb1a92cd14f82a5671327d210a)` |
| `dt_right_le_shell` | `add5fcbb6eaa853d8923f16ef0c5d81f248170eecf04533bef45583be8ba8dc5` | `(274,19,197,209,13,10,0db4ad7cc71c95435a1326d30e9ad67773da45eb1a94a553129ed6db3da71182)` |
| `pair_code_shell_lower` | `80e197c464b5241e57c4d15efdd3b07ca7b7d06467da1009566b0d8c51ddcad8` | `(85,13,79,84,6,3,ecec6b8a7ff41f1b28205a9f711ce7520e08511583c4d895257686d461214483)` |
| `pair_code_below_next_shell` | `50e6bd0164dc1ce9cd0aef876c3a0a7ab75d78d29f6ec2b8a1a550107e21faa0` | `(857,29,388,424,37,21,accbb0fc28dcdd8ccd9471ecf1142487ba751d4430907cc22995a59d5a9231d1)` |
| `pair_code_shell_separated` | `53d7aacc96e356a2793f1f1174e34ba4f45cd9621c1489dc21224d304e6102ff` | `(1600,30,636,692,57,38,302d87068774ecbbe5bc6883ace27243e755627e6129d276938f31dd25dad72d)` |
| `double_add_injective` | `9a7cfdd4513598881e04ccd832c6e76923d935141a8dbe8f468d3cb32b71d4b9` | `(493,25,408,430,23,15,b0905453455317eb8e7bb8e7835fd049ad6afb98dabbf865719c02e2cc5b33ec)` |
| `pair_code_injective` | `be57f575eb538308784fb75d9be99c53c6a2c1982145e7cb8e47040800ac1a4a` | `(2525,32,1121,1186,66,59,7dc47f845a11797827e8682f4223af1e083afd48af60e0e22cd56862c44d06d8)` |
| `cell_functional` | `090f28cb4425b8e512218607f5ed10559784f36059b180454cc6487ef619c77f` | `(2550,33,1146,1211,66,60,e1cfdfcfbe2b1bfb70f51cc724280d3bc7ac046c4bd14865bf390952b412a45c)` |
| `cell_head_functional` | `5e177bb042df92bc4e59a06335ccb791d8db0aae7e67d0a9e653c08515dd856c` | `(2569,34,1165,1230,66,61,289cb3b6a42ca39e424e40712e44a24e4b7d4c7b355c4c0bd697d75ae42dfc9f)` |
| `cell_tail_functional` | `7fcdf8eab469302e0d6e7bd0ac6e3715fcce825cf0a1e5250defb1a575cd215b` | `(2569,34,1165,1230,66,61,e03fdd8affeba3e1c0c1cb6f6e496c6ac53b13469db8c9c5b517f0df9de72d5c)` |
| `pair_left_le_code` | `7975a8493f202e62b6949199396f92fd52c10bf6dad0cf11c0b8a8a053966159` | `(257,18,173,184,12,8,2216484e9a09321c065b6fbac742ff1763b28f799720fb4b729468cdeaa8ce3c)` |
| `pair_right_le_code` | `592ea096f736bbeb757f57b16996b1f6209973b21ada4d1ec85d70ab3bae7f9d` | `(181,18,170,180,11,7,48ae46ea34331fc1cdadc03a0e510681748aeade658cf1d9783ab6e7a6740601)` |
| `cell_head_lt_code` | `01c14044a7045b619d91f547260f624b4fe2e5e59a49536ff4b1f32dcbb74e9d` | `(304,20,220,231,12,10,4cbccb9c232ff1ee40d05a3ee0520e5a99beeeebb645f3e5142a5c40681d1d3d)` |
| `cell_tail_lt_code` | `fa147a1b1ef5eba0840b7b6cee35f90a1990938b45956ae80a5cd7dbb0801640` | `(228,20,217,227,11,9,145f2c4c0c00c4b7145a6f847e90af1dd72e500b1d88b03e7ed4fdd267d2867b)` |

The injectivity proof uses trichotomy on the two shell indices. Either strict
ordering would force the common code to be strictly below itself by
`pair_code_shell_separated`; hence the shells agree. Additive cancellation
then equates the doubled right offsets, `double_add_injective` recovers the
right components, and a final cancellation recovers the left components.
This closes literal pair component injectivity without a decoder, division, or
choice. `cell_functional` removes the common D06 successor with PA2 and applies
that exact pair result; its two projections recover the head and tail
separately. The bound tranche first proves each D01 component is at most its
code, then lifts those witnesses through the D06 successor to obtain
`head < code` and `tail < code` in the native existential order encoding.

Thus the private constructor/injectivity/cell-functionality/descent core is
complete. It does **not** decide whether an arbitrary natural is a valid pair
or cell code. Likewise `map_entry_constructor` constructs one D08 entry but
does not define a finite map, computation history, or list.
The projection conveniences `pair_first_functional` and
`pair_second_functional`, plus the parity convenience `pair_code_even`, remain
unmaterialized theorem rows. So does a dedicated `cell_constructor_valid` row;
these conveniences are not prerequisites for the closed core.

## 6. Forbidden dependencies

The transitive closure of the foundational pair/cell candidates must exclude:

- `BetaAt`, beta-prefix extension, and beta-coded folds;
- binary or finite CRT;
- division and remainder interfaces;
- prime-power or factorization coding;
- classical checking, DNE, and hidden choice;
- an assumed list, trace, or recursive predicate.

Only K0--K2 equality, addition, multiplication, order, cancellation, and
formula-specific induction are permitted.

## 7. The uniform-list blocker

Pairing does not by itself produce one finite first-order expansion for

```text
ListValid(code,length)
```

that follows `length` cell tails. Variable iteration requires an encoded
computation history or an equivalent independently justified sequence
mechanism. Recursively expanding the readable macro only gives a distinct
formula for each fixed host numeral:

```text
List0(code) := code = 0
List(k+1)(code) := exists head tail.
  Cell(code,head,tail) /\ Listk(tail)
```

This fixed-length schema cannot support a quantified length, general lookup,
append, folds, list induction, or finite CRT. Calling `CellValid` a list
predicate would therefore be unsound documentation.

This is not an undefinability claim. The desired relations are primitive
recursive and representable in PA. The missing design choice is how their
variable computation traces are represented without importing the very list
or beta infrastructure under construction.

## 8. Permitted resolutions of the list blocker

Exactly one route must be reviewed before a uniform list macro is frozen:

1. construct an independent non-CRT computation-trace encoding and prove
   extension plus functional lookup;
2. add a reviewed primitive-recursive definitional compiler with a proved HA
   elimination/conservativity translation;
3. amend the layer order to permit scalar binary CRT first, then use the
   existing beta representation for sequences before finite CRT; or
4. retain generated fixed-length schemas temporarily and make their bounded
   scope explicit.

Nested pairs, base digits, bitsets, and prime exponents do not remove the
problem by themselves. They move variable iteration into powers, digit
extraction, finite products, or another trace code.

## 9. Alternatives considered

### Dense Cantor coding

The equation `code+code = s*S(s)+2*right` makes every natural a code, but
constructor totality requires consecutive-product evenness and explicit
halving. It adds proof cost without helping the current valid-code API.

### Szudzik square shells

The dense piecewise square-shell bijection has simple host computation, but
its object-level decoder needs a floor-square-root search and its injectivity
proof splits across both branches. The current library has no square-shell
API, so this is deferred.

### Prime powers, binary digits, and beta coding

These routes depend on factorization, powers/digit extraction, division, or
CRT-backed prefix existence. They violate the K3 foundational order.

## 10. Acceptance boundary

The pair/cell gate closes only after:

- all eight templates parse and match the hashes above;
- constructor, literal output, and injectivity candidates close twice from
  the empty context;
- component functionality and strict cell-tail descent are proved;
- false-definition and false-injectivity mutations are rejected;
- the transitive dependency closure passes the K3 quarantine;
- finite semantic oracles agree with the expanded relations; and
- deliberate public admission and independent heavy validation are recorded.

Until then this RFC is a frozen design target, not evidence that pairs, cells,
lists, or maps have entered the public HA library.

The current checkpoint satisfies the template, constructor, literal-output,
pair/cell functionality, strict-descent, mutation, bounded-semantic,
dependency-quarantine, and twice-cold closure parts of this boundary. Valid-code
decision, deliberate public admission, and independent heavy validation keep
the overall pair/cell gate open. Uniform computation histories, lists, and maps
remain separate representation work.
