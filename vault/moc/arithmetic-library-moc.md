---
title: Foundational arithmetic library — Map of Content
tags: [moc, peano-arithmetic, number-theory, library]
---

> The executable and planned dependency graph from elementary equality through
> divisibility, modular arithmetic, primes, and unique factorization.

The current runtime has 51 checked nodes: 23 from the original ladder and 28
from M20. The broader 75-node catalog contains 20 `planned_expressible` and
four `blocked_by_language` nodes in addition to those checked layers.

## Design and trust

- [[foundational-arithmetic-library]]
- [[lemma-dependency-dag]]
- [[arithmetic-library-provenance]]
- [[theorem-ladder]]
- [[trusted-kernel]]
- [[proof-certificate]]

## Mathematical concepts

- [[arithmetic-congruence]]
- [[divisibility]]
- [[quotient-and-remainder]]
- [[gcd-and-coprimality]]
- [[prime-number]]
- [[euclids-lemma]]
- [[fundamental-theorem-of-arithmetic]]

## Checked equality and additive nodes

- [[zero_add]] · [[add_succ_left]] · [[add_comm]] · [[add_assoc]]
- [[eq_symm]] · [[eq_trans]] · [[succ_congr]] · [[add_congr]]
- [[add_right_cancel]] · [[add_left_cancel]] · [[add_eq_zero_right]] · [[add_eq_zero_left]]
- [[no_succ_add_fixed]] · [[drop_add_prefix_from_fixed]]

## Checked multiplication nodes

- [[mul_zero_left]] · [[mul_succ_left]] · [[mul_comm]] · [[mul_add]]
- [[mul_assoc]] · [[one_mul]] · [[mul_one]] · [[add_mul]] · [[mul_congr]]
- [[mul_eq_zero]] · [[mul_ne_zero]] · [[two_large_factors_impossible]]

## Checked order nodes

- [[succ_ne_zero]] · [[succ_injective]]
- [[le_refl]] · [[le_trans]] · [[antisymm_from_witnesses]]
- [[le_antisymm]] · [[le_total]] · [[zero_le]] · [[le_succ_self]] · [[le_zero]]

## Checked divisibility nodes

- [[multiple_zero]] · [[one_multiple]] · [[multiple_refl]]
- [[multiple_add]] · [[multiple_mul_right]] · [[multiple_mul_left]]
- [[multiple_trans]]
- [[not_multiple_pointwise]] · [[not_multiple_from_pointwise]]

## Checked quotient-and-remainder algebra

- [[add_residue]] · [[add_residue_lift]]
- [[square_decomp]] · [[square_residue_lift]] · [[square_residue_witness]]

## Checked first prime instance

- [[prime_two]] — the fully expanded factor-pair predicate for the numeral two

## Executable and documentary views

- Runtime: `peano-lab/py/peano_lab/library/theorems.py`
- Catalog: `research/arithmetic-library/catalog.json`
- Generated snapshot: `artifacts/peano-library/catalog-v1.json`
- Dependency graph: `artifacts/peano-library/dependency-graph.mmd`
- Book: `book/arithmetic-library/`
- Plan: `PLAN/10_arithmetic_library.md`

## Up

[[peano-lab-moc]] · [[00-index]]
