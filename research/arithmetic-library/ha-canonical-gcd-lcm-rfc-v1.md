# RFC HA-K4-GCD-LCM-1: canonical relational gcd and lcm interface

**Status:** representation and theorem statements frozen; canonical-gcd edge,
17-row relational-LCM, and nine-row gcd--LCM totality/compatibility tranches
are closed-checked candidates but remain unadmitted

**Scope:** HA3/K4 divisibility, gcd, lcm, and their product compatibility

**Object language:** first-order HA over \(\{0,S,+,\times,=\}\)

**Kernel change:** none

This RFC freezes the relational least-common-multiple interface that is dual
to the repository's existing relational gcd interface, and records the first
closed canonical-gcd boundary and relational-LCM tranches built over that
interface. It does not register a parser primitive, change the kernel, admit a
gcd or LCM theorem, or change the campaign manifest. Every displayed predicate
is conservative surface syntax which must expand to the unchanged first-order
language before checking.

The words **must**, **must not**, **should**, and **may** are normative within
this RFC.

## 1. Decision

Use the universal property of a least common multiple as the definition of
`IsLCM`. The result is the first argument:

```text
IsLCM(l,a,b)
```

This matches the established result-first order

```text
IsGCD(g,a,b)
```

and makes the two relations exact order duals under divisibility:

- `IsGCD(g,a,b)` says that `g` divides both inputs and every common divisor
  divides `g`;
- `IsLCM(l,a,b)` says that both inputs divide `l` and `l` divides every
  common multiple.

The identity

\[
  \gcd(a,b)\operatorname{lcm}(a,b)=ab
\]

is a frozen target theorem, not the definition of `IsLCM`.

## 2. Exact base-language definitions

The following blocks are normative templates. Implementations must generate
hygienic binder names when an argument would otherwise be captured. The
displayed short binder names record the alpha-equivalence class of the
required expansion.

### 2.1 `Dvd(divisor,value)`

Stable RFC identifier: `HA-K4-GCD-LCM-D01`.

```text
exists q. value = divisor * q
```

The argument order is divisor first, value second. This agrees with all
existing public multiple witnesses, such as `exists q. n = d * q`.

### 2.2 `IsGCD(gcd,left,right)`

Stable RFC identifier: `HA-K4-GCD-LCM-D02`.

```text
(((exists x. left = gcd * x) /\ (exists y. right = gcd * y)) /\ forall c. (exists u. left = c * u) -> (exists v. right = c * v) -> exists w. gcd = c * w)
```

This is the already reviewed relational gcd convention. The RFC repeats it
to pin the duality and argument order; it does not create a second gcd
definition.

### 2.3 `IsLCM(lcm,left,right)`

Stable RFC identifier: `HA-K4-GCD-LCM-D03`.

```text
(((exists x. lcm = left * x) /\ (exists y. lcm = right * y)) /\ forall c. (exists u. c = left * u) -> (exists v. c = right * v) -> exists w. c = lcm * w)
```

The equalities are deliberately oriented like the existing multiple API:
`Dvd(left,lcm)` is `exists x. lcm = left * x`, and `Dvd(lcm,c)` is
`exists w. c = lcm * w`.

### 2.4 Unique relational LCM

Stable RFC identifier: `HA-K4-GCD-LCM-D04`.

```text
exists l. ((IsLCM(l,a,b)) /\ forall m. (IsLCM(m,a,b)) -> m = l)
```

Both occurrences of `IsLCM` in this template must expand independently and
hygienically using `HA-K4-GCD-LCM-D03`. `m = l`, rather than `l = m`, matches
the comparison-to-chosen orientation of the canonical gcd interface.

## 3. Forced zero convention

No extra zero convention is postulated. The universal property forces

\[
\operatorname{lcm}(0,b)=0,
\qquad
\operatorname{lcm}(a,0)=0,
\qquad
\operatorname{lcm}(0,0)=0.
\]

Indeed, `0` is a multiple of every natural, while any multiple of `0` is
equal to `0`. Consequently `IsLCM(0,a,0)` and `IsLCM(0,0,b)` have
constructive proofs. The selected tranche proves the right-zero statement
directly and derives the left-zero statement by symmetry. No theorem in this
layer may use the competing convention `lcm(0,b)=b`, exclude zero inputs
silently, or add a positivity premise to `IsLCM`.

This convention is also why product compatibility must not define LCM. The
formula

```text
exists g. ((IsGCD(g,a,b)) /\ g * l = a * b)
```

accepts every `l` when `a = b = g = 0`, because `0 * l = 0`. It is therefore
not functional at the zero pair.

## 4. Frozen canonical-gcd boundary checkpoint

The public library already proves `is_gcd_zero_right`, `is_gcd_symm`, both
divisibility projections, `is_gcd_of_dvd`, and `is_gcd_unique`. The isolated
canonical-gcd package additionally supplies `canonical_gcd_functional` as a
closed-checked candidate. The following tranche therefore records equality
characterizations and cross-witness symmetry rather than duplicating public
constructors.

The exact source is
[`ha_canonical_gcd_edges_candidate.py`](../../peano-lab/py/peano_lab/library/ha_canonical_gcd_edges_candidate.py),
with the focused audit in
[`test_ha_canonical_gcd_edges_candidate.py`](../../peano-lab/py/tests/test_ha_canonical_gcd_edges_candidate.py).
Its local `edge_is_gcd` expander accepts identifiers and exactly the reviewed
operand literals `0` and `1`; it rejects arbitrary interpolated term strings.
Every displayed `IsGCD` below is expanded hygienically before parsing.

### G01. Zero on the right

Stable RFC identifier: `HA-K4-GCD-LCM-G01`.

```text
canonical_gcd_zero_right_iff :
forall a g. (IsGCD(g,a,0) -> g = a) /\ (g = a -> IsGCD(g,a,0))
```

Ordered dependencies:
`is_gcd_zero_right`, `canonical_gcd_functional`.

### G02. Zero on the left

Stable RFC identifier: `HA-K4-GCD-LCM-G02`.

```text
canonical_gcd_zero_left_iff :
forall a g. (IsGCD(g,0,a) -> g = a) /\ (g = a -> IsGCD(g,0,a))
```

Ordered dependencies:
`is_gcd_symm`, `canonical_gcd_zero_right_iff`.

### G03. One on the left

Stable RFC identifier: `HA-K4-GCD-LCM-G03`.

```text
canonical_gcd_one_left_iff :
forall a g. (IsGCD(g,1,a) -> g = 1) /\ (g = 1 -> IsGCD(g,1,a))
```

Ordered dependencies:
`is_gcd_dvd_left`, `divisor_one`, `one_multiple`, `is_gcd_of_dvd`.

### G04. One on the right

Stable RFC identifier: `HA-K4-GCD-LCM-G04`.

```text
canonical_gcd_one_right_iff :
forall a g. (IsGCD(g,a,1) -> g = 1) /\ (g = 1 -> IsGCD(g,a,1))
```

Ordered dependencies:
`is_gcd_symm`, `canonical_gcd_one_left_iff`.

### G05. Function-style symmetry

Stable RFC identifier: `HA-K4-GCD-LCM-G05`.

```text
canonical_gcd_swap_functional :
forall a b g h. IsGCD(g,a,b) -> IsGCD(h,b,a) -> g = h
```

Ordered dependencies:
`is_gcd_symm`, `canonical_gcd_functional`.

This is the genuinely new function-style consequence of symmetry for two
independently chosen relational outputs. It must not be confused with the
already public predicate transport `is_gcd_symm`.

### 4.1 Frozen statement and closure receipts

Statement hashes are SHA-256 over the exact expanded parser text. Closed
receipts are ordered as
`(nodes, depth, objects, edges, reused, cuts, certificate_sha256)`.

| Candidate | Expanded statement SHA-256 | Empty-context closure receipt |
|---|---|---|
| `canonical_gcd_zero_right_iff` | `8eae442eaa8b347cd9f71b106b9b85c7ddd4de460b7cf498ba2bb04613296576` | `(819, 37, 667, 702, 36, 25, d140ad3b257626cc287b51d576feb4aac6930aa7da58e9d72e5e2b2c30e2e45f)` |
| `canonical_gcd_zero_left_iff` | `46965c33d414fc67bde4ed7b1e6a4cc2b02af87f69e4abb84d487d9f85d3e2ae` | `(893, 39, 741, 776, 36, 27, a720a0a90192a564ab908357a59838ed8b25395045b631705e8da112c19f8932)` |
| `canonical_gcd_one_left_iff` | `278eb32964ddbc738e81303372f64cf1728d340a34035f4bcf079841913fd3e0` | `(329, 30, 287, 303, 17, 12, 4e4c7ceaab45dc15f9378f08e981524d07044d9e7e35a5f827bc510a8a383727)` |
| `canonical_gcd_one_right_iff` | `06a3c3a600eea5f97b2987a34c2cded18322680bd4d50d8501e3dd02fc91bc8b` | `(394, 32, 352, 368, 17, 14, b21067e80580a93f1d1e76d77cf20bb9846598c2971d643fb35d0d6ee2f1c98c)` |
| `canonical_gcd_swap_functional` | `503a5cf41ddd3dac5fcb70c2df9605e218176d0f046b893c94c6242723fab34e` | `(766, 37, 647, 681, 35, 22, 55650ade915e38fd01207d48169d891e06761dd3a277c827ea7b32d0bbb96615)` |

All five dependency-curried bodies and empty-context certificates check
without `DNE` or a classical axiom. They remain isolated, unregistered, and
unadmitted. In particular, **closed-checked candidate** does not mean public
theorem.

No sixth zero-zero row is required. The exact convention

```text
forall g. (IsGCD(g,0,0) -> g = 0) /\ (g = 0 -> IsGCD(g,0,0))
```

is the `a = 0` specialization of G01; its four-command dependency-curried
corollary is checked by the focused audit. A later consumer may name that
corollary, but doing so must not create an independent proof or convention.

## 5. Frozen gcd--lcm compatibility theorem

Stable RFC identifier: `HA-K4-GCD-LCM-T20`.

Surface statement:

```text
forall g l a b. IsGCD(g,a,b) -> IsLCM(l,a,b) -> g * l = a * b
```

Normative fully expanded statement:

```text
forall g l a b. ((((exists x. a = g * x) /\ (exists y. b = g * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. g = c * w)) -> ((((exists x. l = a * x) /\ (exists y. l = b * y)) /\ forall c. (exists u. c = a * u) -> (exists v. c = b * v) -> exists w. c = l * w)) -> g * l = a * b
```

The theorem includes zero inputs. It must be obtained from the universal
relations and their checked existence/uniqueness theory; it must not be used
to redefine either relation.

## 6. Closed relational-LCM universal-property tranche

The exact source is
[`ha_relational_lcm_candidate.py`](../../peano-lab/py/peano_lab/library/ha_relational_lcm_candidate.py),
with the focused audit in
[`test_ha_relational_lcm_candidate.py`](../../peano-lab/py/tests/test_ha_relational_lcm_candidate.py).
All 17 rows in this section are **closed_checked_candidate**: their
dependency-curried bodies and deterministic empty-context certificates check,
but they remain isolated, unregistered, and unadmitted.

The local `is_lcm` expander accepts Peano identifiers and exactly the reviewed
closed literals `0` and `1` in any of its three argument positions. It rejects
all other interpolated term strings and generated-binder capture. Each
occurrence expands independently and hygienically to D03 before parsing; no
`IsLCM` symbol reaches the kernel.

### 6.1 Frozen L01--L08 core

The factory order and ordered dependencies are normative:

| Row | Candidate | Surface statement | Ordered dependencies |
|---|---|---|---|
| L01 | `is_lcm_multiple_left` | `forall l a b. IsLCM(l,a,b) -> Dvd(a,l)` | none |
| L02 | `is_lcm_multiple_right` | `forall l a b. IsLCM(l,a,b) -> Dvd(b,l)` | none |
| L03 | `is_lcm_least` | `forall l a b c. IsLCM(l,a,b) -> Dvd(a,c) -> Dvd(b,c) -> Dvd(l,c)` | none |
| L04 | `is_lcm_symm` | `forall l a b. IsLCM(l,a,b) -> IsLCM(l,b,a)` | none |
| L05 | `is_lcm_unique` | `forall l m a b. IsLCM(l,a,b) -> IsLCM(m,a,b) -> l = m` | `multiple_antisymm` |
| L06 | `is_lcm_zero_right` | `forall a. IsLCM(0,a,0)` | `multiple_zero` |
| L07 | `is_lcm_zero_left` | `forall b. IsLCM(0,0,b)` | `is_lcm_zero_right`, `is_lcm_symm` |
| L08 | `is_lcm_of_dvd` | `forall a b. Dvd(a,b) -> IsLCM(b,a,b)` | `multiple_refl` |

L03 expands its final three divisibility clauses as

```text
(exists u. c = a * u) -> (exists v. c = b * v) -> exists w. c = l * w
```

L05 applies each leastness clause to the other candidate and then uses
`multiple_antisymm`. L06 is the single direct zero constructor. L07 is
deliberately derived from L06 by L04, rather than carrying a second
independent `multiple_zero` proof, so the two zero conventions cannot drift.
L08 uses the expanded premise `exists q. b = a * q`; its second
common-multiple premise already supplies the required leastness conclusion.

### 6.2 Nine convenience rows

These rows follow L01--L08 in the exact displayed order:

| Row | Candidate | Surface statement | Ordered dependencies |
|---|---|---|---|
| C01 | `is_lcm_of_dvd_right` | `forall a b. Dvd(b,a) -> IsLCM(a,a,b)` | `is_lcm_of_dvd`, `is_lcm_symm` |
| C02 | `product_common_multiple` | `forall a b. Dvd(a,a*b) /\ Dvd(b,a*b)` | `right_factor_divides_product` |
| C03 | `is_lcm_refl` | `forall a. IsLCM(a,a,a)` | `multiple_refl`, `is_lcm_of_dvd` |
| C04 | `is_lcm_one_left` | `forall b. IsLCM(b,1,b)` | `one_multiple`, `is_lcm_of_dvd` |
| C05 | `is_lcm_one_right` | `forall a. IsLCM(a,a,1)` | `is_lcm_one_left`, `is_lcm_symm` |
| C06 | `lcm_zero_left_value` | `forall l b. IsLCM(l,0,b) -> l = 0` | `is_lcm_zero_left`, `is_lcm_unique` |
| C07 | `lcm_zero_right_value` | `forall l a. IsLCM(l,a,0) -> l = 0` | `is_lcm_zero_right`, `is_lcm_unique` |
| C08 | `lcm_zero_left_exists_unique` | `forall b. exists l. (IsLCM(l,0,b) /\ forall m. IsLCM(m,0,b) -> m = l)` | `is_lcm_zero_left`, `is_lcm_unique` |
| C09 | `lcm_zero_right_exists_unique` | `forall a. exists l. (IsLCM(l,a,0) /\ forall m. IsLCM(m,a,0) -> m = l)` | `is_lcm_zero_right`, `is_lcm_unique` |

`product_common_multiple` expands to

```text
forall a b. ((exists x. a * b = a * x) /\ (exists y. a * b = b * y))
```

The value and unique-existence rows assert uniqueness of the natural LCM
value only; they make no uniqueness claim about divisibility witnesses.

### 6.3 Frozen statement and closure receipts

Statement hashes are SHA-256 over the exact expanded parser text. Closed
receipts are ordered as
`(nodes, depth, objects, edges, reused, cuts, certificate_sha256)`.

| Candidate | Expanded statement SHA-256 | Empty-context closure receipt |
|---|---|---|
| `is_lcm_multiple_left` | `6bca8a86fc180bd4feba561e4808ce8fd694f687e220137f6be105ef79cf7a43` | `(21, 13, 21, 20, 0, 0, 5c190bf7def19fc23909654cc772afcab5c479fb858898d5f143a80db366e953)` |
| `is_lcm_multiple_right` | `cfd58405c02982ebe269c680dcb0a62ac0ac33c18c8e9526046c9505f2238c61` | `(21, 13, 21, 20, 0, 0, f56c306a18651121802b73a86d0beab26f7b595bf569318f7396f3b99c76ca89)` |
| `is_lcm_least` | `7d232c7416d15f3cf128a8df8cab34ffc63e906dcc9bd0b33368b4352bd869bf` | `(24, 16, 24, 23, 0, 0, c1fa2a7ad9ee24262f2d1fe916db3a988dee5da6d53b067be60f378d4456f38b)` |
| `is_lcm_symm` | `e5ca139205068d953bb4d9e3c6da0c2501064201ac6ee54bd707640b7c7c30b6` | `(36, 21, 36, 35, 0, 0, 1651a88cf14cd0940f75b4cad21f75b4d7babd563e6df09ae54442e8fd865b43)` |
| `is_lcm_unique` | `1e8351beb8ca8bd1ab14ce85864e37af888d97f613896316c60ba0dcbc11b48c` | `(680, 34, 561, 595, 35, 19, 28b5d50ea9f274effaecd0ba637805b5535976124380f9647b31cab1b812dc4f)` |
| `is_lcm_zero_right` | `a84f5e0a22729e73c1a31f5d6e2571fde1ddb828006f96db2070421d1d5e9d87` | `(25, 7, 25, 24, 0, 1, 1f46d596bf5887fb6fbbf47a571a7773c0e803a57767ddc624a016e3771d1a36)` |
| `is_lcm_zero_left` | `7c6f2f252ee95f63821288659f8208bef80dc883a7927330b337e00711a2f374` | `(71, 23, 71, 70, 0, 3, a40c084aceae295b1af3ea106a436dfcbb2289b81387ebb03a1bc39c7676fc92)` |
| `is_lcm_of_dvd` | `eb81fefc899776cd175dc71a078d579174fbe5c7936b57014f1ff862da0ddc3b` | `(55, 11, 55, 54, 0, 3, d1263366658d3d37613817c9bcd0e21f7180136fcfdc25d8617d7c2f548dc766)` |
| `is_lcm_of_dvd_right` | `e51e5862e544864a48d59d1e21d21d875476c723da77288122815a6f82d11113` | `(106, 23, 106, 105, 0, 5, 7aff4b6e58da3dda088da6ba977f0b4a1fabb50a263288635bf2ebce8e38f4b0)` |
| `product_common_multiple` | `f87e8656fc1bd22ac5bae5a740627c718db6b7940651f99c1ead6f8c0b78abea` | `(244, 26, 222, 243, 22, 8, 70144cd71d6b2cda4cb382dc33100c0dbc3d6242472cf18422657115473dde11)` |
| `is_lcm_refl` | `22834919e7a01e3e787607ed95a47d888f71c21820b3ff73b259a50e37d3d53a` | `(103, 13, 64, 64, 1, 5, 9c1c7f996a39ae851114fd6191e3d4e867584ecb6b74dadf5c21e87da35944ab)` |
| `is_lcm_one_left` | `b304968358057e53b071eeee9f4468d42388012373d4ced91254d9603bff05bb` | `(96, 13, 92, 95, 4, 6, 734740e90689cc82db1a3aaba42eb2471229a29c80cd2b4cb7481723278d0965)` |
| `is_lcm_one_right` | `c589196ec5efe0bfe2e2f50e6522d7dc204aa45ae809bbbf26736709592d1f46` | `(142, 23, 138, 141, 4, 8, 90ede4dea5adabe411b2e5a81f45efcfeaca3514d229e440eb79cbbae0b523ef)` |
| `lcm_zero_left_value` | `469b141cedd8543fc22618655f9cd83517b9bcba0df449a5bd8d8999e8dd5791` | `(781, 36, 662, 696, 35, 24, c4fb7bc6dc2d811c0a8591ee85be5d9ddcd00e67837a124b2d7baee3e4d9268f)` |
| `lcm_zero_right_value` | `731d9238983dc7d932e28eab75772f3d91ff1a41ad7c87d5cc3917d481f0e999` | `(735, 36, 616, 650, 35, 22, 9e51cac408db5d62721a01bd3c71da4216f7728767d22736e05df02e3075063e)` |
| `lcm_zero_left_exists_unique` | `9c134aff1a98a052cc459008668afa94d9b56c4997072385d17c43b0c25f3900` | `(788, 36, 669, 703, 35, 24, b2ce4efd6a15d2249e224682cb8fe571f8e1cc542b1af3ebeb40ad9164eff097)` |
| `lcm_zero_right_exists_unique` | `9d17f29f58181dd887856b708e539ab3b6331603d3f28e14379613dec170f269` | `(742, 36, 623, 657, 35, 22, 2ab337c21a1fbb5a607ad5cd9f829bed5b0ff355bf34e33dc62ee1362a06999e)` |

Two cold closures agree on the ordered 17-row stack digest
`a314f85fcee6f04ec548f7a5fd724dc67e35e514a4b79241fce4bad7b5aed318`.
The focused audit also pins dependency-curried body receipts, literal-edge
statements, a false zero mutation, bounded universal-property semantics, and
strict registry isolation. The transitive closure contains neither `DNE` nor
division, remainder, CRT, beta, or a classical axiom. These results establish
the structural LCM API and forced edge values. Taken alone, these 17 rows do
not establish general LCM totality; the closed bridge in Section 7 supplies
that result.

## 7. Closed constructive totality ladder

The preferred route is now complete. Exact source lives in
[`ha_lcm_totality_bridge_candidate.py`](../../peano-lab/py/peano_lab/library/ha_lcm_totality_bridge_candidate.py),
with the focused audit in
[`test_ha_lcm_totality_bridge_candidate.py`](../../peano-lab/py/tests/test_ha_lcm_totality_bridge_candidate.py).
Every row A--I is **closed_checked_candidate**, isolated, unregistered, and
unadmitted. The route uses no excluded-middle axiom: its zero split is supplied
by the already checked constructive theorem `eq_decidable`.

The exact factory order and ordered direct dependencies are:

| Row | Candidate | Ordered dependencies |
|---|---|---|
| A | `balanced_bezout_one_implies_coprime` | `common_divisor_divides_balanced_result`, `divisor_one` |
| B | `coprime_product_is_lcm` | `mul_comm`, `gauss_coprime_cancel`, `mul_assoc` |
| C | `is_lcm_scale_nonzero` | `mul_assoc`, `mul_left_cancel_nonzero` |
| D | `balanced_bezout_cancel_gcd` | `mul_left_cancel_nonzero`, `mul_add`, `mul_assoc`, `mul_one` |
| E | `gcd_zero_inputs` | `mul_zero_left` |
| F | `gcd_lcm_compatible_exists` | `gcd_balanced_bezout_exists`, `eq_decidable`, `gcd_zero_inputs`, `is_lcm_zero_left`, `balanced_bezout_cancel_gcd`, `balanced_bezout_one_implies_coprime`, `coprime_product_is_lcm`, `is_lcm_scale_nonzero`, `mul_assoc`, `mul_comm` |
| G | `lcm_exists_relational` | `gcd_lcm_compatible_exists` |
| H | `canonical_lcm_exists_unique` | `lcm_exists_relational`, `is_lcm_unique` |
| I | `gcd_lcm_product` | `gcd_lcm_compatible_exists`, `is_gcd_unique`, `is_lcm_unique` |

For readability, `Dvd`, `IsGCD`, and `IsLCM` are shown as surface macros.
Candidate source must expand them before parsing the kernel goal.

### A. Balanced result one implies coprimality

```text
balanced_bezout_one_implies_coprime :
forall a b xp yp xn yn.
  a * xp + b * yp = 1 + (a * xn + b * yn) ->
  forall d. Dvd(d,a) -> Dvd(d,b) -> d = 1
```

Route: `common_divisor_divides_balanced_result` gives `Dvd(d,1)` and
`divisor_one` gives `d = 1`. This is the missing converse to the existing
`coprime_balanced_bezout` direction and is independently reusable.

### B. The product of coprime inputs is their LCM

```text
coprime_product_is_lcm :
forall a b.
  (forall d. Dvd(d,a) -> Dvd(d,b) -> d = 1) ->
  IsLCM(a * b,a,b)
```

Route: multiplication gives the two common-multiple witnesses. If
`c = a*r = b*s`, symmetry of coprimality and `gauss_coprime_cancel` show
`Dvd(b,r)`, hence `Dvd(a*b,c)` after reassociation.

### C. Nonzero scaling preserves LCM

```text
is_lcm_scale_nonzero :
forall k l a b.
  ~(k = 0) -> IsLCM(l,a,b) -> IsLCM(k * l,k * a,k * b)
```

Route: cancel the common left factor `k` with
`mul_left_cancel_nonzero`, apply the old leastness clause, and reassociate
the resulting witness. A later zero-inclusive corollary may branch on
`eq_decidable k 0` and use L06/L07:

```text
is_lcm_scale :
forall k l a b. IsLCM(l,a,b) -> IsLCM(k * l,k * a,k * b)
```

### D. Cancel a nonzero gcd from balanced Bezout

```text
balanced_bezout_cancel_gcd :
forall g a b A B xp yp xn yn.
  ~(g = 0) ->
  a = g * A ->
  b = g * B ->
  a * xp + b * yp = g + (a * xn + b * yn) ->
  A * xp + B * yp = 1 + (A * xn + B * yn)
```

Route: rewrite both inputs, factor `g` on each side, rewrite `g` as `g*1`,
and apply `mul_left_cancel_nonzero`. The checked row is reassociation-heavy
and its focused audit rejects direct equation mutations.

### E. A zero relational gcd forces zero inputs

```text
gcd_zero_inputs :
forall g a b. g = 0 -> IsGCD(g,a,b) -> (a = 0 /\ b = 0)
```

Route: eliminate the two divisibility witnesses and rewrite with
`mul_zero_left`.

### F. Joint compatible gcd and lcm existence

```text
gcd_lcm_compatible_exists :
forall a b. exists g l.
  ((IsGCD(g,a,b) /\ IsLCM(l,a,b)) /\ g * l = a * b)
```

Checked construction:

1. obtain `g`, both quotient witnesses `a = g*A`, `b = g*B`, and balanced
   Bezout coefficients from `gcd_balanced_bezout_exists`;
2. decide `g = 0` constructively;
3. in the zero branch, use E and the forced-zero LCM law;
4. in the nonzero branch, use D then A to prove `Coprime(A,B)`;
5. use B to obtain `IsLCM(A*B,A,B)` and C to scale by `g`;
6. close `g * (g * (A * B)) = (g * A) * (g * B)` by checked
   associativity and commutativity.

No uniqueness of Bezout coefficients is asserted or needed.

### G. Relational LCM totality

```text
lcm_exists_relational : forall a b. exists l. IsLCM(l,a,b)
```

This is a projection of F, not a second existence proof.

### H. Unique relational LCM existence

```text
canonical_lcm_exists_unique :
forall a b. exists l. ((IsLCM(l,a,b)) /\ forall m. (IsLCM(m,a,b)) -> m = l)
```

Route: combine G with L05. The theorem states uniqueness of the natural LCM
value, not uniqueness of divisibility witnesses.

### I. Arbitrary gcd--lcm product compatibility

```text
gcd_lcm_product :
forall g l a b. IsGCD(g,a,b) -> IsLCM(l,a,b) -> g * l = a * b
```

This is the named theorem for frozen target `HA-K4-GCD-LCM-T20`. Obtain a
compatible pair from F, identify its gcd with `g` using `is_gcd_unique`,
identify its LCM with `l` using L05, and rewrite the compatible product
equation.

### 7.1 Frozen statement and closure receipts

Statement hashes are SHA-256 over the exact expanded parser text. Closed
receipts are ordered as
`(nodes, depth, objects, edges, reused, cuts, DNE, certificate_sha256)`.

| Row | Candidate | Expanded statement SHA-256 | Empty-context closure receipt |
|---|---|---|---|
| A | `balanced_bezout_one_implies_coprime` | `15ea38440ee20616b269602106c298e93b8e8e2260dda9cf587ebb67cc04601b` | `(871, 40, 616, 656, 41, 19, 0, 6c0e03c2f140d71999c98f4c8a4b15095bc3f922a8a61332a8fb58d9108907a2)` |
| B | `coprime_product_is_lcm` | `ca92cea1f3eaa8750de6280a3e1c2ef0f805d88cd72f1a0a345b44f7f0068c37` | `(4191, 53, 1552, 1646, 95, 69, 0, c23fbcd7191b32d3d2543edecb330e42719d366fe1c6e99b471299f4314e7b17)` |
| C | `is_lcm_scale_nonzero` | `6ac3b09e048aaea3926dcbe3f2aec301e6c94ae106f32ec142b7d699c01db8ac` | `(430, 27, 371, 383, 13, 10, 0, 03918aed31b503afffd000c497bd8442198d370799d046246fdf088bd83ebeee)` |
| D | `balanced_bezout_cancel_gcd` | `0439333ca1d13314222adf5ab96ec61079fe8d4f738f697ae780db03c750de0e` | `(549, 38, 409, 426, 18, 13, 0, a938ef67adb719c111c268255c32f6ad2836ab02da82e2a9113245fd25153bfd)` |
| E | `gcd_zero_inputs` | `df92b2685a693e5be486c34fddd877b12376cbc23b30b03b6cb3019c111e7350` | `(62, 21, 62, 61, 0, 1, 0, b1e47b053b892e56877ab5a4cdd4b6f78ca399957dbf97b97fd427df8676d941)` |
| F | `gcd_lcm_compatible_exists` | `04331aaa9adc6b04b5aea8dbcac34b46fed098b5233a08b88e957a37b9d7ebd5` | `(9038, 60, 2390, 2510, 121, 101, 0, dfe0e69fb172e48b6aa785c0c088ebf1a7cdf09c95ae436305d51d6224e90bc3)` |
| G | `lcm_exists_relational` | `6269a6276e71f62a970b11a696013faf90b5e67ac498f5eb03a2f0f000f0556c` | `(9071, 61, 2423, 2543, 121, 102, 0, f4e764738627255eb885d78b5cefd74663d68be022370a8036ee450b116a7220)` |
| H | `canonical_lcm_exists_unique` | `708dbaee014b840dcde57d6b0fcd43ca4e484cdaf63db7488391beefe147cf7e` | `(9791, 62, 2565, 2691, 127, 111, 0, 3ab4c410a0e4c6717e77d7f951d26304a35b5e9451df299167bb42cadf227747)` |
| I | `gcd_lcm_product` | `f3b5095a728faab08137e6ee281f9da8ce6ea2697abd376170c34b1a62d47176` | `(10441, 61, 2569, 2696, 128, 112, 0, c0829496624e993a4c437aa98c32355605109e728acd03d6b5d857fcb5350d0a)` |

Two independent cold closure passes reproduce every receipt. The focused audit
also pins exact script digests, transitive public/local boundaries, safe
compound-term expansion for rows B/C/F, and false mutations for every row.
F's zero and nonzero branches receive separate tactic mutations. Every DNE
count is zero. Rows B and F--I intentionally reach the public Euclidean
division chain and are K4, while the strict 74-row K3 signed stack is
unchanged.

## 8. Alternative constructive route

An independent proof may search for the least nonzero common multiple below
`a*b`, using `multiple_decidable`, concrete induction on the bound, and
division with remainder. A remainder of a common multiple by a least positive
common multiple is again a common multiple by `divides_remainder`; minimality
then forces the remainder to zero.

This route is valid in first-order HA and is not blocked by the language. It
is no longer needed to establish totality: the preferred gcd/Bezout/Gauss
route is closed. The bounded-search construction remains deferred as a
possible independent cross-check.

The search predicate must say **nonzero** common multiple. Zero is always a
common multiple and would otherwise be the numerically least candidate,
which does not prove the desired universal property for nonzero inputs.

## 9. Existing dependency anchors

The following names were inventoried in the checked public registry and are
the intended anchors, subject to ordinary replay at implementation time:

- divisibility algebra: `multiple_zero`, `multiple_refl`, `multiple_add`,
  `multiple_mul_left`, `multiple_mul_right`, `multiple_trans`, and
  `multiple_antisymm`;
- multiplication and cancellation: `mul_assoc`, `mul_comm`, `mul_one`,
  `one_mul`, `mul_ne_zero`, `mul_left_cancel_nonzero`, and
  `mul_right_cancel_nonzero`;
- constructive case analysis: `zero_or_succ` and `eq_decidable`;
- gcd: `is_gcd_zero_right`, `is_gcd_symm`, `is_gcd_dvd_left`,
  `is_gcd_dvd_right`, `is_gcd_greatest`, `is_gcd_unique`,
  `gcd_exists_relational`, and `gcd_balanced_bezout_exists`;
- Bezout and Gauss: `common_divisor_divides_balanced_result`,
  `coprime_balanced_bezout`, `coprime_symm`, `divisor_one`, and
  `gauss_coprime_cancel`.

The checked K4 closure of F--I reaches division through the public gcd and
Gauss developments. Those rows must not be reported as strict-K3 merely
because the final LCM formulas contain only multiplication and quantifiers.

## 10. Dependency and admission rules

1. `Dvd`, `IsGCD`, and `IsLCM` are hygienic surface macros only. They must
   expand before the unchanged kernel sees a formula.
2. Every candidate theorem must declare all dependencies explicitly and be
   checked first as a dependency-curried body.
3. Admission requires an empty-context certificate with exact structural
   node, depth, proof-DAG identity, Cut-count, and digest receipts.
4. The candidate stack must be replayed cold at least twice and yield the
   same ordered stack digest.
5. Tests must pin statement hashes, dependency order, binder hygiene, zero
   fixtures, symmetry, false mutations, and registry isolation.
6. No `DNE`, excluded-middle axiom, external arithmetic solver, admitted
   lemma, hidden host computation, or trusted theorem name may close an HA
   row. Constructive decidability theorems already proved in HA may be used.
7. A theorem remains outside the public registry until its body, transitive
   closure, resource bounds, documentation counts, and independent snapshot
   all pass.
8. F--I form a K4 client layer. They must remain separate from the closed
   strict-K3 signed stack and must not alter that stack's receipt.
9. Product compatibility must be derived after universal-property totality
   and uniqueness. It must never substitute for `IsLCM` at zero.

## 11. Honest status table

| Item | Status | Meaning |
|---|---|---|
| D01 `Dvd` orientation | `frozen_existing` | Matches checked public multiple witnesses; no new theorem admitted here. |
| D02 `IsGCD` expansion | `frozen_existing` | Matches the reviewed relational gcd API. |
| D03 `IsLCM` expansion | `representation_frozen` | Exact literal-safe hygienic relation selected; the totality certificate remains nonpublic. |
| Result-first argument order | `frozen` | `IsGCD(g,a,b)` and `IsLCM(l,a,b)`. |
| G01--G05 canonical gcd boundary laws | `closed_checked_candidate` | Exact expanded statements, ordered dependencies, and deterministic empty-context receipts are recorded; all five remain isolated and unadmitted. |
| Zero convention | `closed_checked_candidate` | L06 proves right-zero directly; L07 derives left-zero by symmetry; value and unique-existence corollaries are closed but unadmitted. |
| L01--L08 and nine convenience rows | `closed_checked_candidate` | Exact expanded statements, ordered dependencies, and deterministic empty-context receipts are recorded; all 17 remain isolated and unadmitted. |
| A--E infrastructure | `closed_checked_candidate` | All five algebraic bridge rows have exact expanded statements and deterministic empty-context receipts; none is admitted. |
| F joint compatible existence | `closed_checked_candidate` | Both the zero and nonzero constructions close; the 9,038-node certificate remains isolated and unadmitted. |
| G/H LCM totality and unique existence | `closed_checked_candidate` | Totality is projected from F and unique value is packaged with L05; both remain nonpublic. |
| I gcd--lcm product theorem | `closed_checked_candidate` | The frozen target closes by compatible existence plus gcd/lcm uniqueness; it is not admitted. |
| Bounded-minimum alternative | `deferred_constructive` | Expressible in native HA; not selected for the first implementation. |

No proof blocker remains in this RFC's candidate scope: LCM totality, unique
value, compatible gcd/LCM existence, and the product identity all have checked
empty-context certificates. The remaining boundary is deliberate public
admission and repository integration. This RFC must not be cited as evidence
that any of these nine rows is already a public theorem.
