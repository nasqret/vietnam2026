# HA Bertrand B6 Release Tranche RFC v1

Status: frozen for additive Alpha enrollment
Date: 2026-08-17
Trust target: body-checked Alpha evidence only

## 1. Purpose

This RFC binds the forty-three reviewed support rows needed to expose the
already completed native B6 theorem `bertrand_main_inequality_nat` to later
Bertrand clients. It also binds the two generic finite-product order rows used
by B5. The tranche changes no theorem statement, proof script, dependency
tuple, kernel rule, Stable entry, or checked-use permission.

The mathematical contracts remain those of the campaign RFCs:

- `ha-bertrand-postulate-campaign-rfc-v1.md`, SHA-256
  `0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`;
- `ha-bertrand-postulate-campaign-rfc-v2.md`, SHA-256
  `af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`.

## 2. Immutable parent

The parent is Alpha v11 at commit
`02c5d4421fa39ed61dc5f2057d230b37a7304f5a`, with:

- 1,123 ordered Alpha entries;
- 3,482 direct dependency edges;
- 45 dependency layers;
- enrollment identity
  `c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36`;
- edition identity
  `46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3`.

The parent artifact hashes are:

- `catalog-v11.json`:
  `d992c4aeb37829838cefd668679c513c5d45f6304f9842dcbe825bb25563182c`;
- `metrics-v11.json`:
  `92cb654431a1b631cede3a0957993b41b8ad0fb0a0175d1587413dbf54c14300`;
- `dependency-graph-v11.mmd`:
  `c020f3207b0408cf446200b2c91f0767874c50466eebda830c3faeeef08aeae1`;
- `channels-v11.json`:
  `039712b6a1db739738f49b5cec20afdc0582ffae477bc43c52f96c00687b066f`.

## 3. Exact source blocks

The release manifest preserves the following source order. Every factory must
produce exactly the listed names and no others.

### 3.1 Thirty-row base-window block

Source: `bertrand_hj_base_thirty_two_candidate.py`, SHA-256
`2ca24de2693a8bb32bfb999fdb9602460bdce16dd5ce94f64c59d2a06f4a2386`.

Test: `test_bertrand_hj_base_thirty_two_candidate.py`, SHA-256
`40d902435f2ff3bcdedbea8534ea64720b11b17fe52ff2b269f8ffb91c0c2992`.

The exact names, in order, are:

1. `pow_block_bound_from_total`
2. `pow_three_five_le_pow_four_four_from_total`
3. `pow_eleven_two_le_pow_two_seven_from_total`
4. `pow_six_ten_le_pow_four_thirteen_from_total`
5. `linear_square_budget`
6. `bertrand_scaled_budget_root_32`
7. `bertrand_scaled_budget_root_33`
8. `bertrand_scaled_budget_root_34`
9. `bertrand_scaled_budget_root_35`
10. `bertrand_scaled_budget_root_36`
11. `bertrand_scaled_budget_root_37`
12. `ceil_div_six_budget_of_scaled_le`
13. `pow_six_six_le_pow_four_eight_from_total`
14. `pow_six_four_le_pow_four_six_from_total`
15. `pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total`
16. `pow_two_double_eq_pow_four_from_total`
17. `pow_two_successor_double_le_pow_four_successor_from_total`
18. `pow_eleven_double_block_le_pow_two_seven_block_from_total`
19. `pow_eleven_double_block_le_pow_four_even_from_total`
20. `pow_eleven_double_block_le_pow_four_odd_from_total`
21. `pow_six_ten_block_le_pow_four_thirteen_block_from_total`
22. `pow_thirty_six_double_block_eq_pow_six_four_block_from_total`
23. `bertrand_h_root_32_from_total`
24. `bertrand_h_root_33_from_total`
25. `bertrand_h_root_34_from_total`
26. `bertrand_h_root_35_from_total`
27. `bertrand_h_root_36_from_total`
28. `bertrand_h_root_37_from_total`
29. `bertrand_j_base_thirty_two_window_from_total`
30. `bertrand_hj_base_window_thirty_two_from_total`

### 3.2 Six-row all-root block

Source: `bertrand_hj_all_s_candidate.py`, SHA-256
`1dd96d72ff5d548dc6d8eb71cdcec58d151dd6632c45301e528a1cb2c9a6f31a`.

Test: `test_bertrand_hj_all_s_candidate.py`, SHA-256
`4f30e07a689eb554e5f673b505c61f32fb02def34c18e75221a43bb2bd24620b`.

The exact names are:

1. `scaled_factor_square_identity`
2. `thirty_two_square_eq_twice_sixteen_times_thirty_two`
3. `floor_sqrt_factorized_threshold_thirty_two`
4. `six_block_window_decomposition_above_thirty_two`
5. `bertrand_hj_six_block_iterate_from_total`
6. `bertrand_hj_envelope_thirty_two`

### 3.3 Two-row growth block

Source: `bertrand_b6_growth_candidate.py`, SHA-256
`a3fd12f2331d3817c8f6e21bd226fa3dbcb2059d7e17a05bb745ba3acb2d1cba`.

Test: `test_bertrand_b6_growth_candidate.py`, SHA-256
`4ad318473446edfb5942fa56b6527eab7adcf371027911892e7cf43edea65774`.

The exact names are:

1. `bertrand_floor_power_product_le_h_from_total`
2. `bertrand_four_power_product_le_of_sum_from_total`

### 3.4 Three-row main block

Source: `bertrand_b6_main_inequality_candidate.py`, SHA-256
`0b6aed58cf2865fde8e41c5d20e301169727e40599afec7ce03e0a9517d2f657`.

The binding closure audit is `test_bertrand_b6_layered_closure.py`, SHA-256
`1b9651a9fcb0096a06b3bd1177b200c309adc48ec640bb5c2e4ebb64c97f81e6`.

The exact names are:

1. `bertrand_main_inequality_factorized_from_total`
2. `bertrand_main_inequality_factorized`
3. `bertrand_main_inequality_nat`

The empty-context audit must retain the explicit balanced-v1 successor
lineage. Enrollment does not reinterpret its closure receipt as checked-use
authority.

### 3.5 Two-row finite-product order block

Source: `finite_product_order_candidate.py`, SHA-256
`4a502fe8e233c631305ebb644cec9e3c877e1830e0348995f8e6e481fff1b433`.

Test: `test_finite_product_order_candidate.py`, SHA-256
`5fcd164e0fee70f48dd2fd4117676c570b7c4f09271d0896098bee435161f132`.

The exact names are:

1. `beta_product_pointwise_le`
2. `beta_product_uniform_le_pow`

## 4. Enrollment semantics

All forty-three rows enter Alpha as `body_checked`, `checked_use=False`, with
Bertrand enrollment origin. Their theorem bodies must replay against the exact
Alpha-v11 parent plus the preceding local prefix. Stable remains byte-identical
to Alpha v11's 432-row Stable view.

The release must reject:

1. any source, test, RFC, or parent-artifact hash drift;
2. any name, order, statement, script, or dependency drift;
3. any duplicate or forward dependency;
4. any occurrence of DNE in the new scripts;
5. any attempt to replay a new Alpha row as checked-use authority;
6. any change to the exact Alpha-v11 prefix or Stable identity.

## 5. Evidence gates

The additive edition must freeze:

- the exact 43-row source-block manifest;
- dependency-curried kernel receipts for every appended body;
- dependency depths, edge count, layer count, enrollment identity, and edition
  identity;
- canonical source, test, RFC, and parent-artifact SHA-256 bindings;
- the complete nine-microbatch Alpha-v12 order that also contains the later B5,
  B7, B8, BP01, and BP02 tranches.

This RFC grants visibility and provenance only. Empty-context closure evidence
remains in the focused audits, and a later dependency-closed promotion is
required before any appended theorem can become Alpha checked-use or Stable.
