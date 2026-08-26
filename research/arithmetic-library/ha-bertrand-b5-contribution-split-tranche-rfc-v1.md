# HA Bertrand B5 Contribution-Split Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`16f233b1081e37ade9ed2d05577c32504967a30a`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_b5_contribution_split_candidate.py
a5b1e955cdd903adc6ada446fbcdb56d620a8e89372e3c3b71183ec22cfe1b7b
```

The focused-test seal remains pending until every fail-closed receipt is
measured.  Hashes and receipts are evidence only and grant no authority.

## 1. Scope

This ten-row tranche constructs offset intervals of the already frozen
complete prime-power contribution selector.  It then splits the complete
Product of length `n+n` at two exact additive cut points:

```text
s+g=q
q+h=n+n.
```

The capstone returns a prefix Product of length `s`, an interval Product
covering global indices `s..q-1`, and an interval Product covering global
indices `q..n+n-1`, with the checked equality

```text
z=(x*y)*w.
```

This tranche does not bound any of the three factors, compact neutral
entries, compare an interval with a Primorial, or prove the B5 central
binomial upper bound.

## 2. Representation contract

All readable relations below are authoring abbreviations expanded before
parsing.  They add no kernel symbol.

```text
Choice(n,i,p) := CompletePrimeContribution(n,i,p)

Prefix(n,b,c,l) :=
  forall i. i<l -> exists p. BetaAt(b,c,i,p) /\ Choice(n,i,p)

ProductOf(n,l,z) :=
  exists b c. Prefix(n,b,c,l) /\ Product(b,c,l,z)

IntervalPrefix(n,a,b,c,l) :=
  forall i. i<l ->
    exists p. BetaAt(b,c,i,p) /\ Choice(n,a+i,p)

Interval(n,a,l,z) :=
  exists b c. IntervalPrefix(n,a,b,c,l) /\ Product(b,c,l,z)
```

`Choice`, `Prefix`, and `ProductOf` use the exact helper expansions from
the pinned prime-contribution source.  Generated binders are checked against
the complete public and local context.  Compound terms are parsed in that
context and rendered canonically.

No row may use DNE, raw beta-code equality, an AllPrime membership oracle,
candidate-only concatenation, arbitrary provider discovery, or a
whole-relation rewrite of `Choice`, `Prefix`, `ProductOf`, or `Interval`.

## 3. Binding rows, tags, and dependencies

The order is dependency-topological and binding.

### 3.1 `prime_contribution_interval_prefix_extend`

```text
forall n a b c l.
  IntervalPrefix(n,a,b,c,l) ->
  exists d e. IntervalPrefix(n,a,d,e,S l)
```

Public tags are `bpcifpe_before` and `bpcifpe_after`.

```text
(prime_contribution_choice_exists,
 beta_prefix_extend,
 finite_lt_succ_eq_or_lt)
```

The terminal branch performs exactly twelve scalar rewrites of `i=l` in
the expanded complete-contribution choice.  The earlier-index branch uses
the source prefix unchanged.

### 3.2 `prime_contribution_interval_prefix_exists`

```text
forall n a l. exists b c. IntervalPrefix(n,a,b,c,l)
```

Public tag: `bpcipx_result`.

```text
(add_eq_zero_right,
 succ_ne_zero,
 prime_contribution_interval_prefix_extend)
```

### 3.3 `prime_contribution_interval_prefix_transport_entry`

```text
forall n a b c d e l.
  IntervalPrefix(n,a,b,c,l) ->
  IntervalPrefix(n,a,d,e,l) ->
  forall i p. i<l -> BetaAt(b,c,i,p) -> BetaAt(d,e,i,p)
```

Public tags are `bpcipt_left`, `bpcipt_right`, `bpcipt_bound`,
`bpcipt_source`, and `bpcipt_target`.

```text
(beta_at_unique, prime_contribution_choice_functional)
```

Only the small decoded entry is transported, with two value rewrites.

### 3.4 `prime_contribution_interval_exists`

```text
forall n a l. exists z. Interval(n,a,l,z)
```

Public tag: `bpci_exists`.

```text
(beta_product_exists, prime_contribution_interval_prefix_exists)
```

### 3.5 `prime_contribution_interval_functional`

```text
forall n a l x y.
  Interval(n,a,l,x) -> Interval(n,a,l,y) -> x=y
```

Public tags are `bpci_functional_left` and
`bpci_functional_right`.

```text
(beta_product_transport_prefix,
 beta_product_functional,
 prime_contribution_interval_prefix_transport_entry)
```

### 3.6 `prime_contribution_interval_prefix_shift`

```text
forall n a b c d e l.
  Prefix(n,b,c,a+l) -> IntervalPrefix(n,a,d,e,l) ->
  forall i p. i<l -> BetaAt(b,c,a+i,p) -> BetaAt(d,e,i,p)
```

Public tags are `bpcips_source`, `bpcips_interval`, `bpcips_bound`,
`bpcips_source_entry`, and `bpcips_target_entry`.

```text
(add_le_add_left, beta_at_unique,
 prime_contribution_choice_functional)
```

### 3.7 `prime_contribution_prefix_restrict_add`

```text
forall n a b c l. Prefix(n,b,c,a+l) -> Prefix(n,b,c,a)
```

Public tags are `bpcpra_source` and `bpcpra_target`.

```text
(le_add_right, lt_of_lt_of_le)
```

### 3.8 `prime_contribution_prefix_interval_split`

```text
forall n a l z.
  ProductOf(n,a+l,z) ->
  exists x y.
    ProductOf(n,a,x) /\ (Interval(n,a,l,y) /\ z=x*y)
```

Public tags are `bpcpis_source`, `bpcpis_prefix`, and
`bpcpis_interval`.

```text
(beta_product_prefix_suffix_split,
 prime_contribution_interval_prefix_exists,
 prime_contribution_interval_prefix_shift,
 prime_contribution_prefix_restrict_add)
```

The Product split is applied exactly once.  Prefix and interval codes remain
independent and are related only by pointwise decoded-entry transport.

### 3.9 `prime_contribution_product_length_eq_transport`

```text
forall n l m z. l=m -> ProductOf(n,l,z) -> ProductOf(n,m,z)
```

Public tags are `bpcplet_source` and `bpcplet_target`.

Dependencies: `()`.

The source hypothesis is transported by exactly four scoped rewrites: one
prefix bound occurrence and three Product length occurrences.

### 3.10 `prime_contribution_three_range_split`

```text
forall n s q g h z.
  s+g=q -> q+h=n+n -> ProductOf(n,n+n,z) ->
  exists x y w.
    ProductOf(n,s,x) /\
    (Interval(n,s,g,y) /\
    (Interval(n,q,h,w) /\ z=(x*y)*w))
```

Public tags are `bpctrs_source`, `bpctrs_small`, `bpctrs_middle`, and
`bpctrs_high`.

```text
(prime_contribution_product_length_eq_transport,
 prime_contribution_prefix_interval_split)
```

The proof first aligns `n+n` with `q+h`, splits at `q`, aligns `q` with
`s+g`, then splits the prefix at `s`.  It rewrites only the small product
equality when combining the two packages.

## 4. Evidence gates

The focused harness must:

1. pin Stable, Alpha-v11, the complete-contribution helpers, the finite-fold
   surface, the checked prefix/suffix split, this source, and this RFC;
2. reconstruct every public formula independently of this candidate's
   interval helpers;
3. expose Stable plus the exact Alpha-v11 graph and only the first two
   complete-contribution rows as predecessor authority;
4. expose earlier local rows only as a strict prefix;
5. replay every body, kernel-check it, enforce the live caps and bounded
   envelope, and reject DNE;
6. remove every one of the 24 dependency edges and reject the body;
7. reject a false conjunct and one genuine semantic mutation per row;
8. recursively rebuild each empty-context closure, assert the direct Cut
   vector `(3,3,2,2,3,3,2,4,0,2)`, corrupt every direct Cut, and require
   kernel rejection before receipt acceptance; and
9. fail closed while any artifact, body, envelope, or closure receipt is
   absent.

The default candidate caps remain binding.  No cap increase is authorized.

## 5. Release and next obligation

All ten rows begin as Alpha-only `body_checked`, with no checked-use or
Stable authority upgrade.  Promotion is a separate dependency-closed gate.

The next B5 tranche must use the resulting middle and high interval factors
together with the already proved range classification.  It must still solve
the representation-sensitive neutral-entry compaction needed for a
duplicate-free Primorial comparison.  This RFC does not assume that step.
