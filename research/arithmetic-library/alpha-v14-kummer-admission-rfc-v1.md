# Alpha v14 constructive Kummer admission and evidence boundary

## Scope and immutable parent

Alpha v14 is a strictly additive extension of the sealed **1,543-entry Alpha
v13** edition.  It admits precisely the missing constructive dependency
closures of the complete binomial Kummer carry-count theorem and its
carry-free/nondivisibility corollary.  The **432-entry Stable edition**, its
default channel, every previous Alpha theorem object and catalog row, and the
existing **570 checked-use theorems** remain unchanged.

The reviewed expanded-statement SHA-256 identities are:

```text
kummer_binomial_carry_bit_count
  f9f7312eacb89563dff059b63d310a3148b0b7df7f9e0425bbf4fdbd868e3c4f

kummer_carry_free_iff_not_divides
  ed30b756bd9703193020ae395a87f1f32a12859d2b9df8fbb79708e9bed2dc00
```

The theorem and corollary are already established as dependency-curried
constructive proof bodies.  Enrollment does not manufacture an empty-context
proof, checked-use authority, or Stable membership.

## Exact dependency-minimal admission

Depth-first dependency traversal, stopping exactly at existing Alpha-v13
entries, first visits the complete Kummer root and then the carry-free
corollary.  Its exact ordered append is:

```text
choose_factorial_valuation_balance
choose_legendre_valuation_balance
binomial_legendre_valuation_balance
division_add_quotient_bit
add_quotient_carry_choice
add_quotient_carry_prefix_extend
add_quotient_carry_prefix_exists
add_quotient_carry_prefix_all_bits
add_quotient_carry_prefix_restrict
beta_sum_add_carry_exact
kummer_binomial_carry_bit_count
prime_power_valuation_zero_iff_not_divides
kummer_carry_free_iff_not_divides
```

The first flagship requires **11 new rows**.  Its corollary adds exactly **2**
more rows, so the union contains **13** bodies and Alpha v14 has precisely
**1,556 theorems**.  The exact compact-JSON ordered-name SHA-256 is:

```text
2ff93cb296e4d4a077a8e8722bde54be2f0a9e4a72caedac5fcaa58508c60d6c
```

Three independently bounded source-factory blocks supply the closure:

```text
make_kummer_valuation_candidate_theorems          4
make_kummer_carry_candidate_theorems              7
make_kummer_carry_corollary_candidate_theorems     2
```

Both carry factories share their reviewed `kummer_carry_candidate.py` source
and focused executable test; valuation bodies use their corresponding
`kummer_valuation_candidate.py` source and focused test.  Every row links the
reviewed `ha-kummer-theorem-campaign-rfc-v1.md` and the exact sealed Alpha-v13
catalog bytes.  Actual dependency-curried kernel receipts are initially
obtained in **three separate factory subprocesses**; no process replays the
entire parent library.

The sealed runtime dependency graph has **5,251 edges** and **45 layers**. Its
ordered-enrollment identity is
`d7758c5cfcce4fbe2b48b6b213b134acf9126b84a58a0016c523055be952024e`; its full
edition identity is
`06274ac80612403f6851266fa00f8b543d904072434d5717ca95ae7d40588c16`.

## Exact evidence boundary

Every appended theorem has precisely:

```text
membership            alpha_only
enrollment_origin     ha
evidence_status       body_checked
body_checked          true
checked_use           false
empty_context_closure null
```

The 41 distinct direct Alpha-v13 prerequisites contain 26 `stable_closed`, one
`alpha_closed`, and **14 `body_checked`** rows.  Their complete 267-row
transitive parent closure contains 171 `stable_closed`, one `alpha_closed`,
and **95 `body_checked`** ancestors.  Thus neither Kummer flagship has an
empty-context closure receipt or checked-use authority.  The final Alpha-v14
evidence ledger is 432 `stable_closed`, 138 `alpha_closed`, 985
`body_checked`, and one `pending_layered_closure`; checked-use stays **570**.
Both roots must be rejected by edition `replay()`.

Candidate statement/script/dependency hashes, release identity, source/RFC/test
bindings, graph topology, and mutation audits are integrity safeguards.  They
do not replace an actual independently kernel-checked dependency-curried body.

## Immutable Alpha-v13 parent bytes

```text
artifacts/peano-library/alpha/catalog-v13.json
  cad57a21657e2df09f01174069efcfed194d87b68c0b4042b234df5759583e5a
artifacts/peano-library/alpha/metrics-v13.json
  b3ad8140487486cbe51e8ef6ae0ef9586636cb9576305de47ef77ad864c93bc9
artifacts/peano-library/alpha/dependency-graph-v13.mmd
  f6664c7f415fff8444dafab331b184b04426e2c395b3828c7d91929dfe74805a
artifacts/peano-library/channels-v13.json
  db8c195d98fb02ca0b1561d483cb8f5472d550d7e662cfe4b733ffb1b9ae8634
```

Alpha v14 writes only new `catalog-v14.json`, `metrics-v14.json`,
`dependency-graph-v14.mmd`, and `channels-v14.json` artifacts.  No earlier
Alpha artifact or Stable byte may be rewritten.
