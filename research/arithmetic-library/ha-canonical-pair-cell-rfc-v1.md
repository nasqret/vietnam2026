# RFC HA-K3-PAIR-1: doubled-Cantor pairs and successor-tagged cells

**Status:** representation selected; proof candidates not yet implemented  
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
