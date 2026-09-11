# Jordan107 → prime-power cardinality → distinct-prime product

Source-only audit, 11 September 2026. **Every proposed row below is unproved.**
No native checker, test, Lean compiler, admission or publication was run for
this note. The existing107 research inventory and the separate95-row Alpha
promotion retain the boundaries recorded in `JORDAN107-SCALING-HANDOFF.md`.

## Route choice

Build a box enumeration by induction on tuple width, appending one coordinate.
Flatten `(old_index,digit)` as `n*old_index+digit`. This uses four existing
Jordan rectangle lemmas whose actual contracts concern only natural indices;
they have **no CRT, coprimality or primitive-tuple premise**. A separate
fixed-width radix development or the G091 assembly is therefore not required.
The construction still proves a genuine fixed-width, leading-zero-inclusive
bijection; it does not count nonunique beta codes.

```text
beta extension + rectangle geometry + actual Pow
                  ↓
             exact BoxEnum ──────── Jordan107 scaling
                  ↓                       ↓
divisibility mask + filter       exact DivEnum of length U
                  ↓                       ↓
complementary counts ─────── tuple-enumeration count comparison
                  ↓
prime-power characterization + Jordan count uniqueness
                  ↓
            j + U = W → arithmetic prime-power factor
                                   ↓
Jordan(k,1,1) + coprime product + actual distinct prime support
                                   ↓
                       actual finite factor product
```

## Existing factories to select, not reimplement

Paths in this table are under `peano-lab/py/peano_lab/library/`, except the
explicit research scaling source. Names are source-audited dependencies, not
a fresh claim that a particular new dependency cone has been checked.

| Source / factory | Exact reusable rows and role |
| --- | --- |
| `theorems.py` original tuples | `beta_at_exists`, `beta_at_unique`, `beta_prefix_extend`, `division_remainder_exists`, `division_remainder_unique`; `beta_product_exists`, `beta_product_functional`, `beta_product_zero`, `beta_product_succ_decompose`. Actual finite codes and arithmetic traces. |
| `jordan_totient_candidate.py` / `make_jordan_totient_candidate_theorems`, `make_jordan_enumeration_candidate_theorems`, `make_jordan_enumeration_bridge_candidate_theorems` | `jordan_tuple_all_divisible_decidable`, `jordan_tuple_common_divisor_transport`; `jordan_tuple_equal_empty`, `jordan_tuple_equal_drop_last`, `jordan_tuple_equal_extend`; `jordan_tuple_prefix_equal`, `jordan_tuple_equal_entry`, `jordan_tuple_bounded_transport`, `jordan_tuple_outer_append_exists`. |
| `jordan_multiplicativity_candidate.py` / `make_jordan_multiplicativity_candidate_theorems` | `jordan_rectangle_width_nonzero`, `jordan_rectangle_quotient_bound`, `jordan_rectangle_flat_bound`, `jordan_rectangle_pair_unique` (geometry rows at lines162–198). Later `jordan_totient_coprime_product` constructs the actual product count. |
| Research `jordan_tuple_scaling_candidate.py` / `make_jordan_tuple_scaling_candidate_theorems` | `jordan_box_scaling_divisible_image_exists`, `jordan_box_divisible_scaling_preimage_exists`, `jordan_tuple_scaling_respects_tuple_equality`, `jordan_tuple_scaling_injective`. These construct and identify decoded tuples, not enumerations. |
| `finite_bitcount_theorems.py` / `make_finite_bitcount_theorems` | `bit_count_exists`, `bit_count_functional`, `bit_count_zero`, `bit_count_succ_decompose`; use the existing `AllBits` / `BitCount` expansions. |
| `finite_bitcount_complement_candidate.py` / `make_finite_bitcount_complement_candidate_theorems` | `complementary_bit_counts_add_length`: two actual complementary bit streams with counts `a,b` over length `W` give `a+b=W`. |
| `finite_modular_set_candidate.py` / `make_finite_modular_set_candidate_theorems` | `finite_bit_complement_exists`, `finite_bit_complement_member_iff`. Despite the module name, these contracts are unrestricted finite bit-prefix results, not prime-modulus theorems. The former constructs the complementary code and count, using `beta_sign_factor_prefix_exists`. |
| `jordan_count_uniqueness_candidate.py` / `make_jordan_count_uniqueness_candidate_theorems` | `jordan_totient_count_unique` applies once the nondivisible list becomes an actual Jordan enumeration. Its index-map construction is a proof template for new box/divisible-list comparison, **not** an already-general enumeration theorem. |
| `fermat_two_squares_pigeonhole_candidate.py` / `make_fermat_two_squares_pigeonhole_candidate_theorems` | `finite_bounded_into_oversized_not_injective`, with `finite_permutation_theorems.injective_prefix`; the genuine bounded-index injection supplies the count inequality. Apply in both directions, then `le_antisymm`. |
| `jordan_prime_power_characterization_candidate.py` / `make_jordan_prime_power_characterization_candidate_theorems` | `jordan_prime_power_tuple_primitive_characterization` converts nondivisibility to primitivity and back at a positive prime power. It does not assert a count. |

Power constructors are already available: `make_finite_fold_theorems` gives
`pow_exists`, `pow_zero`, `pow_functional`, `pow_successor_decompose`;
`make_power_congruence_theorems` gives `pow_successor_pair_mul`;
`make_bertrand_power_bridge_candidate_theorems` gives the actual constructor
`pow_successor_compose` (no supplied totality premise). For the factor form,
`make_bertrand_integer_envelope_candidate_theorems` gives `pow_mul_base` and
`make_power_algebra_theorems` gives `pow_mul_exp`. Positivity uses
`pow_nonzero_of_one_le` from `make_bertrand_power_growth_candidate_theorems`,
with `one_le_of_ne_zero` and `prime_nonzero`.

## Exact proposed notation and contracts

All displayed predicates are abbreviations to expand into the unchanged HA
signature before proof checking; they are not new kernel symbols. Reuse
`BetaAt`, `Lt`, `Pow`, `BitCount`, and the exact Jordan `_bounded`, `_equal`,
`_all_dvd`, `_primitive`, `_jordan` builders. Below call the latter
`Bound(b,c,k,n)`, `TupleEq(b,c,d,e,k)`, `AllDvd(p,b,c,k)`,
`Primitive(n,b,c,k)`, `Jordan(k,n,j)` respectively. Preserve their existing
definition identities and argument alignments, including nonobvious aliases.

Define `Entry(B,C,D,E,i,b,c)` literally as
`BetaAt(B,C,i,b) /\ BetaAt(D,E,i,c)`.
The following enumeration template specifies three concrete new abbreviations:

```text
Enum_R(k,n,B,C,D,E,j) :=
  (forall i. Lt(i,j) -> exists b c.
    Entry(B,C,D,E,i,b,c) /\ Bound(b,c,k,n) /\ R(b,c)) /\
  (forall b c. Bound(b,c,k,n) -> R(b,c) -> exists i d e.
    Lt(i,j) /\ Entry(B,C,D,E,i,d,e) /\ TupleEq(b,c,d,e,k)) /\
  (forall i h b c d e. Lt(i,j) -> Lt(h,j) ->
    Entry(B,C,D,E,i,b,c) -> Entry(B,C,D,E,h,d,e) ->
    TupleEq(b,c,d,e,k) -> i=h).
```

`R` is a **source-generation placeholder, never an HA predicate variable**.
Instantiate it with `0=0` for `BoxEnum(k,n,...)`, `AllDvd(p,b,c,k)` for
`DivEnum(p,k,n,...)`, and `~AllDvd(p,b,c,k)` for `NonDivEnum(p,k,n,...)`.
No desired power/count equality belongs in any of these definitions.
Assign no stable IDs until an exact-AST identity/hygiene audit against both
the public definition registry and the local494 research registry.

First bounded authoring tranche:

```text
jordan_box_enumeration_empty_width_exists:
  forall n. exists B C D E. BoxEnum(0,n,B,C,D,E,1)

jordan_box_enumeration_successor_exists:
  forall k n B C D E u. ~(n=0) -> BoxEnum(k,n,B,C,D,E,u) ->
  exists F G H I. BoxEnum(S k,n,F,G,H,I,u*n)

jordan_box_enumeration_power_exists:
  forall k n W. ~(n=0) -> Pow(n,k,W) ->
  exists B C D E. BoxEnum(k,n,B,C,D,E,W)

jordan_divisible_box_enumeration_from_scaling:
  forall p k A B C D E U. ~(p=0) -> BoxEnum(k,A,B,C,D,E,U) ->
  exists F G H I. DivEnum(p,k,p*A,F,G,H,I,U)
```

Prove successor construction, coverage and distinctness separately before
combining them. Decode each position below `u*n` by actual division by `n`,
append its digit with `beta_prefix_extend`, then append the two resulting
inner-code fields with `jordan_tuple_outer_append_exists`. Recover both the
old tuple and final digit from tuple equality; use the rectangle pair lemma.
The power-existence theorem inducts on `k`, not on a guessed large numeral.
Width zero is essential internally even though Jordan itself excludes it.

Second tranche: actual filtering and comparison. Define `DivMask` by
`AllBits(M,T,W)` together with

```text
forall i b c e. Lt(i,W) -> Entry(B,C,D,E,i,b,c) -> BetaAt(M,T,i,e) ->
  ((e=1 /\ AllDvd(p,b,c,k)) \/ (e=0 /\ ~AllDvd(p,b,c,k))).
```

New targets are:

```text
forall p k n B C D E W. BoxEnum(k,n,B,C,D,E,W) ->
  exists M T. DivMask(p,k,B,C,D,E,W,M,T)

forall p k n B C D E W M T d.
  BoxEnum(k,n,B,C,D,E,W) -> DivMask(p,k,B,C,D,E,W,M,T) ->
  BitCount(M,T,W,d) -> exists F G H I. DivEnum(p,k,n,F,G,H,I,d)

forall p k n B C D E d F G H I U.
  DivEnum(p,k,n,B,C,D,E,d) -> DivEnum(p,k,n,F,G,H,I,U) -> d=U
```

Add the analogous complement-mask → `NonDivEnum` constructor. Filtering
requires a new prefix invariant with actual selected positions, coverage,
distinctness and output length equal to the actual prefix `BitCount`.
Neither the original representative-code sweep nor Jordan-specific
enumeration completeness can be substituted for this invariant. Comparison
constructs real beta index maps by finite induction, following the count96
template without importing its primitive-tuple hypotheses into `DivEnum`.

The first formula endpoint is exactly:

```text
forall p h k A N U W j.
  Prime(p) -> ~(k=0) -> Pow(p,h,A) -> Pow(p,S h,N) ->
  Pow(A,k,U) -> Pow(N,k,W) -> Jordan(k,N,j) -> j+U=W
```

Align `N=p*A` using `pow_successor_pair_mul` and `mul_comm`. The mask count
equals `U` by the new divisible-enumeration comparison. Its complement
enumerates primitive tuples by the existing characterization and therefore
has count `j` by `jordan_totient_count_unique`. Apply the existing complement
sum, then `add_comm`. No subtraction principle or excluded middle is needed.

## Arithmetic factor, then distinct-prime product

Next prove, rather than define Jordan by, this target:

```text
forall p h k A N U V t.
  Prime(p) -> ~(k=0) -> Pow(p,h,A) -> Pow(p,S h,N) ->
  Pow(A,k,U) -> Pow(p,k,V) -> V=S t -> Jordan(k,N,U*t)
```

Use actual Jordan totality (`make_jordan_scan_candidate_theorems` /
`jordan_totient_exists`), `pow_exists` for `W`, the count endpoint,
`pow_mul_base` for `W=U*V`, distributivity and additive cancellation.
Existing `nonzero_is_succ` and power positivity construct `t`; its existence
must not be inferred from a supplied factor-count formula.

For `e>0`, let the new arithmetic-only `JFactor(k,p,e,f)` expand to

```text
Prime(p) /\ ~(e=0) /\ exists h A U V t.
  e=S h /\ Pow(p,h,A) /\ Pow(A,k,U) /\ Pow(p,k,V) /\
  V=S t /\ f=U*t.
```

Construct a beta factor prefix from actual decoded prime/exponent entries.
Use `prime_valuation_support_relation` / `make_prime_valuation_support_candidate_theorems`
and `prime_valuation_support_exists`: it already gives distinct prime codes,
positive exact exponents, genuine powers and their product equal to `n`.
From `make_euler_totient_product_candidate_theorems`, directly reuse
`totient_prime_entries_decoded_power`, `totient_prime_entries_selected_power`
and `totient_prime_support_powers_pairwise_coprime`; their contracts contain
no `Phi`. Its `totient_pairwise_coprime_product_fold` is **only a template**,
because its actual conclusion and per-factor hypotheses do contain `Phi`.

The Jordan-specific fold to author is:

```text
forall k l vb vc fb fc N T. ~(k=0) -> PairwiseCoprime(vb,vc,l) ->
  (forall i a f. Lt(i,l) -> BetaAt(vb,vc,i,a) -> BetaAt(fb,fc,i,f) ->
     Jordan(k,a,f)) ->
  Product(vb,vc,l,N) -> Product(fb,fc,l,T) -> Jordan(k,N,T)
```

`PairwiseCoprime` is the existing `_pairs` expansion from the Euler product
source; `Product` is the original beta product relation. Base case:
`jordan_totient_at_one` from `make_jordan_unit_modulus_candidate_theorems`.
Step: `jordan_totient_coprime_product`, `beta_product_succ_decompose`,
`crt_pairwise_coprime_prefix_drop_last` and
`crt_pairwise_coprime_prefix_product_coprime_last` from
`make_generalized_crt_fold_candidate_theorems`, with literal equality
transport. This step may be authored independently while box counting runs.

Define `JProduct(k,n,T)` only by an actual complete distinct-prime support,
its actual `JFactor` prefix, and `Product(fb,fc,l,T)`; it must not mention
Jordan. Final targets: positive `k,n` construct `T` with both `JProduct` and
`Jordan`, and `Jordan(k,n,j) -> JProduct(k,n,T) -> j=T`.
The rational Euler-product notation remains a mathematical restatement,
not a new HA primitive. The empty support at `n=1` is indispensable.

## Gates and counterexamples before any new completion claim

- Independently specified contracts, exact conservative definition DAG
  roundtrips, and actual tuple/beta models: width0; modulus1; distinct beta
  encodings of one tuple; empty/full masks; missing or duplicate indices.
- Check count examples `(p,h,k)=(2,0,1),(2,1,2),(2,2,3)` giving respectively
  `1+1=2`, `12+4=16`, `448+64=512`; product example `J_2(12)=12*8=96`.
  These are model expectations, not formal evidence.
- Reject composite-base characterization (`p=4`, modulus4, tuple `(2)`),
  repeated-prime product support, zero order, and raw-code injectivity.
- Separate original-HA body/adverse checks, complete dependency-cone HA,
  same-byte Lean, standalone maximal roots, and only then Alpha promotion.
  Keep CPU170/175s, wall180s, RSS1536MiB and depth256. No controller, kernel,
  public definition registry or frozen96/107 artifact was modified here.
