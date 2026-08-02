# M21–M25 — Native quadratic reciprocity

## Objective

Produce a closed, independently kernel-checked proof of quadratic reciprocity
for distinct odd primes in Peano Lab's unchanged first-order arithmetic
language. Every expository relation must expand to `0`, `S`, `+`, `*`,
equality, intuitionistic logic and ordinary induction before kernel checking.

The exact endpoint and constructive entrance gates are specified in
[`quadratic-reciprocity-surface.md`](../research/arithmetic-library/quadratic-reciprocity-surface.md).
Finite encodings are specified in
[`finite-fold-surface.md`](../research/arithmetic-library/finite-fold-surface.md).
Resource policy is recorded in
[`quadratic-reciprocity-capacity.md`](../research/arithmetic-library/quadratic-reciprocity-capacity.md).

## Non-negotiable trust boundary

- No quadratic-reciprocity, Legendre-symbol, Euler-criterion or finite-field
  axiom.
- No primitive integer, power, sum, count, list, set or remainder function.
- Surface helpers are untrusted formula producers and grant no theorem
  authority.
- Definition-aware pages and `PD` tags are likewise conservative presentation:
  they must expand to the same native PA AST, and notation edges never become
  proof dependencies.
- Every library entry reconstructs a self-contained certificate and passes the
  independent kernel from the empty context.
- Intuitionistic mode is the default; campaign certificates contain no `DNE`.
- Live composition is bounded independently by 500,000 structural
  occurrences, 100,000 distinct proof objects and depth 256.

## M21 — QR-0 parity and constructive residue membership

- [x] Fix the sign-free same-case, opposite-case and combined endpoint
      formulas below `MAX_INPUT`.
- [x] Add constructive even/odd cases and exclusivity.
- [x] Add successor, addition and multiplication parity.
- [x] Add the constructive converse classifiers for sum parity.
      `even_sum_parity_cases` and `odd_sum_parity_cases` recover same/opposite
      summand parities, while `even_sum_iff_same_parity` and
      `odd_sum_iff_opposite_parity` package both directions. Their bodies are
      `61/18`, `61/18`, `63/19`, and `63/19`; the focused audit passes `4/4`
      in 0.40 seconds with no automation or classical escape.
- [x] Identify expanded evenness and oddness with balanced congruence to zero
      and one modulo two, and prove congruence transports both parity classes.
      The five dependency-curried bodies check at `14/9`, `20/13`, `42/18`,
      `50/16`, and `86/20`; the focused audit passes `4/4` and the contracts
      remain unregistered and unadmitted.
- [x] Prove that an odd multiplier preserves and reflects both parity classes,
      then transport parity across every exact equation `n=p*q+r` as
      `parity(n)=parity(q+r)`. The six constructive bodies culminate at
      `93/22`, `93/22`, and the combined `51/20` package; the prerequisite-
      integrated parity run passes `12/12` in 1.27 seconds.
- [x] Add odd-half existence/uniqueness.
- [x] Add exhaustive odd (1/3\pmod4) cases and their exclusivity.
- [x] Relate those cases to the parity of the fixed odd half. The exact
      identities `p=2*h+1=p=4*a+1 -> h=2*a` and
      `p=2*h+1=p=4*a+3 -> h=2*a+1` check at `20/13` and `78/27`; the two
      existential iff packages check at `42/18` and `100/30`. All four parity
      suites pass `16/16` in 1.24 seconds.
- [x] Derive oddness of every prime other than two.
- [x] Prove balanced congruence decidable for nonzero modulus.
- [x] Prove bounded quadratic-root search by concrete induction.
- [x] Prove bounded/unbounded quadratic-residue equivalence.
- [x] Prove `QRes(p,a) \/ ~QRes(p,a)` for `p != 0`.
- [x] Add complete checked quadratic-residue classifications for moduli 3, 5
      and 7, including explicit witnesses and complementary nonresidue proofs.

Exit gate: every entry cold-replays twice, rejects a nearby false mutation,
contains no `DNE`, fits all three live bounds, appears in the snapshot,
research catalog, vault and theorem atlas, and passes cold browser replay.

## M22 — QR-1 relational finite folds

- [x] Specify hygienic expanded `Repeat`, `Range`, `Pow`, `Sum`, `AllBits` and
      `BitCount` relations.
- [x] Prove constant β-prefix (`Repeat`) existence and transport.
- [x] Prove relational power existence, functionality, zero and successor.
- [x] Prove β-coded sum-trace existence and functionality.
- [x] Prove bit-count existence, functionality and `count <= length`.
- [x] Prove interval/range prefix existence.
- [x] Prove pointwise-congruent finite products and sums transport.
- [x] Prove exact finite-sum invariance under a bounded injective β-coded
      reindexing. The replacement, swap-last, fixed-last induction and general
      permutation bodies check at `327/59`, `133/50`, `85/33`, and `631/88`;
      their two focused suites pass `8/8` in 22.67 seconds. This is body-only
      evidence pending WMI recursive closure and admission.

Exit gate: no individual fold endpoint exceeds 35,000 structural occurrences
without a written review; the largest endpoint passes browser replay.

## M23 — QR-2 prime residue systems and Euler's criterion

- [x] Derive modular inverses for nonzero residues from balanced Bézout.
- [x] Prove cancellation modulo a prime.
- [x] Build relational factorials over the checked consecutive-range/product
      encoding, with existence, functionality, zero and successor laws.
- [x] Prove first-power, successor-pair and base-congruence laws for relational
      powers.
- [x] Prove square, exponent-addition and exponent-multiplication laws for
      relational powers.
- [ ] Construct the nonzero residue interval and its product.
  - [ ] WMI-admit `beta_range_one_entry_eq_succ`.
  - [ ] WMI-admit `beta_product_pointwise_coprime`.
  - [ ] WMI-admit `prime_range_product_coprime`.
- [x] Prove bounded injection implies surjection, via constructive β-prefix
      swap/reindex and transport of boundedness, injectivity and surjectivity.
- [x] Prove the one-position product replacement balance law.
- [x] Prove exact product invariance for an interior/final β-prefix swap.
- [ ] Lift swap-last invariance to arbitrary bounded injective β-coded
      reindexings by successor induction.
  - [x] Prove and locally audit the fixed-last and alignment-swap support
        rungs.
  - [ ] Complete the content-addressed WMI discovery replay for the two
        isolated general-reindex candidates.
  - [ ] Pin the WMI receipts and pass a separate admission replay before
        importing either candidate.
- [ ] Complete the successor-lift, multiplication-map, scale-product, and
      residue-product-balance rungs specified in
      `fermat-wilson-next-tranche.md`.
  - [x] Author isolated, hygienic candidates for successor lifting and the
        canonical prime multiplication map (rungs 4--5).
  - [x] Author isolated pointwise scale-product transport (rung 7).
  - [x] Decompose residue reindexing into independently reusable boundedness,
        injectivity, alignment, and scale-alignment lemmas, then package rung
        6 as an isolated candidate.
  - [x] Author isolated product balance (rung 8) using only rung 6, exact
        target-product existence, general product reindexing, and rung 7.
  - [x] Cancel stale WMI jobs `172769` (rung 6) and `172770` (rung 8), both
        bound to snapshot `c6e6cabbbaf8b617...`, after zero CPU.
  - [x] Fix the missing second rewrite in
        `beta_successor_range_reindex_aligned` and the invalid locally
        repackaged `hprojection` in `prime_mul_residue_product_balance`.
  - [x] Add and test (3/3)
        `peano_lab.library.candidate_validation.replay_candidate_bodies`.
        It kernel-checks dependency-curried candidate scripts and reports
        structural/identity metrics without replaying/closing dependencies;
        it is explicitly non-admitting.
  - [x] Pass all 21 finite-product plus Fermat candidate bodies. Key
        nodes/depth are reindex aligned `86/34`, scale `62/32`, reindex exists
        `106/40`, balance `93/39`, predecessor Fermat `93/34`, and all-input
        Fermat `104/30`. Pass nine bounded structural gates across reindex,
        balance, and endpoints. This is not closed-certificate admission.
  - [x] Submit corrected jobs `172988` (`fermat-reindex`, 16 GiB/2 hours) and
        `172989` (`fermat-balance`, 16 GiB/2 hours) from snapshot
        `73d2863a0138c8dce1f8a7f2793bcd96f543e389c0c4af6cce75cc13005ac3d9`.
        Both were pending at submission.
  - [ ] Validate jobs `172988` and `172989` by closed recursive replay and
        mutations, then require distinct receipt-pinned admission snapshots.
  - [ ] Pin every discovered statement/script/dependency hash and structural/
        identity metric, then pass separate admission snapshots before public
        registration.
- [x] Author the isolated predecessor-exponent endpoint
      `fermat_predecessor_exponent_mod_one`, using the exact residue product,
      rung 8, product coprimality, and coprime modular cancellation.
- [x] Author the isolated constructive all-input wrapper
      `fermat_little_all_inputs`, using successor-power decomposition and the
      prime coprime-or-divides split.
- [x] Submit the dedicated five-gate `fermat-endpoints` WMI discovery suite
      as job `172837`, bound to snapshot
      `c7cc39f94b2cb0ae5542f89b3ddec947d84c55627168e07851c62da36f51bd34`
      on `cpu_idle` with 1 CPU, 32768 MiB, and `04:00:00`; it was later
      cancelled after zero CPU.
- [x] Submit corrected endpoint job `172990` from snapshot
      `73d2863a0138c8dce1f8a7f2793bcd96f543e389c0c4af6cce75cc13005ac3d9`
      with 32 GiB and 4 hours. It was pending at submission.
- [ ] Validate pending discovery job `172990`. Its queued scheduler receipt is
      neither a pass nor an admission result.
- [ ] Pin the endpoint hashes and metrics and pass a distinct immutable
      admission replay before either endpoint enters the public registry.
- [x] Author isolated `prime_bounded_square_one_cases`. Its constructive route
      writes positive `x` as `S t`, extracts `p | t * (t + 2)` from the
      balanced square-one witnesses, applies `euclid_prime_dvd_product`, and
      closes the two branches by strict bounds and antisymmetry.
- [x] Remove the UI-only `ring` tactic and fix the explicit native
      equality/rewrite proof at its exact 16-dependency boundary:
      `ne_zero_of_one_le`, `nonzero_is_succ`, `mul_succ_left`, `add_assoc`, `add_comm`,
      `add_left_cancel`, `factor_difference`, `euclid_prime_dvd_product`,
      `le_succ_self`, `lt_of_le_of_lt`, `zero_or_succ`,
      `divisor_le_nonzero`, `lt_not_le`, `succ_ne_zero`, `le_antisymm`, and
      `succ_injective`.
- [x] Wire and submit the dedicated five-gate `wilson-square-one` WMI
      discovery suite as job `172855`, bound to snapshot
      `396af02c5aa4fdf62d4c3484f8a2c711b03c489cad498c121d0402ce3ee79981`
      on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`; it was later
      cancelled after consuming zero CPU and is retained as provenance only.
- [x] Record the square-one body-only laptop receipt at 182 nodes/depth 48
      and pass its three bounded structural gates. This is not a closed
      recursive replay or admission result.
- [x] Submit replacement discovery job `172966` from common exact snapshot
      `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`.
      It is `PENDING (Priority)` with zero CPU.
- [ ] Validate pending discovery job `172966`, pin its exact hashes and
      structural/identity metrics, and pass a distinct immutable admission
      replay. Its queued receipt is not a pass or theorem admission.
- [x] Fix the zero-based inverse representation: `InvIdx(p,n,i,j)` stores
      `i<n`, `j<n`, and `(S i)*(S j) ≡ 1 (mod p)`; `InvPrefix(p,n,b,c,l)`
      requires every `i<l` to decode some such `j` through the existing
      expanded `BetaAt` relation.
- [x] Author the four isolated pointwise candidates
      `prime_inverse_index_exists`, `bounded_mod_inverse_unique`,
      `bounded_inverse_index_unique`, and `inverse_index_symmetric`.
- [x] Author the three isolated prefix candidates
      `prime_inverse_prefix_extend`, `prime_inverse_prefix_exists_bounded`,
      and `prime_inverse_prefix_exists`. Extension uses
      `prime_inverse_index_exists`, `beta_prefix_extend`, and
      `finite_lt_succ_eq_or_lt`; bounded existence is ordinary induction; the
      full map specializes `l≤n` to `n≤n`.
- [x] Wire and submit the five-gate `wilson-inverse-prefix` WMI discovery
      suite, recursively closing all seven inverse candidates, as job
      `172899` from snapshot
      `1a11442b18dd6c40b49975e16f0b2062be57fade347acca20d87dba27e6adffc`
      on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`; cheap body replay
      later exposed two existential-binder errors, so it was cancelled after
      zero CPU.
- [x] Fix both prefix binder errors, pass the three bounded structural gates,
      and submit replacement job `172975` from corrected snapshot
      `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`.
      It was pending at submission.
- [ ] Validate pending discovery job `172975`, pin all seven candidates'
      exact hashes and structural/identity metrics, then pass a distinct
      immutable admission replay. Its queued receipt is not a pass or theorem
      admission.
- [x] Author six isolated extensional-map candidates:
      `inverse_prefix_entry_sound`, `inverse_prefix_extensional`,
      `inverse_prefix_involutive`, `inverse_prefix_injective`,
      `inverse_prefix_surjective`, and `prime_inverse_prefix_fixed_cases`.
      The first five are prime-free; only the fixed theorem assumes primality,
      and it concludes exactly `i = 0 \/ S i = n`.
- [x] Wire and submit the five-gate `wilson-inverse-involution` WMI suite,
      recursively closing 14 specs, as job `172920` from snapshot
      `cfa4eea18d4a746a49a2d7579f217dbd65a27a79df61c76e8dba49079ba1aaa4`
      on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`; it was later
      cancelled after consuming zero CPU.
- [x] Submit first replacement job `172967` from snapshot
      `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`;
      it was cancelled after zero CPU when the prefix dependency changed.
- [x] Submit corrected job `172976` from snapshot
      `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`;
      it was pending at submission.
- [ ] Validate pending discovery job `172976`, pin all six candidates' exact
      hashes and structural/identity metrics, and pass a distinct immutable
      admission replay. Its queued receipt is not a pass or theorem admission.
- [x] Author isolated `inverse_prefix_zero_fixed`,
      `inverse_prefix_last_fixed`, and
      `prime_inverse_prefix_exact_endpoints`. The package supplies `n=S k`,
      entries `At(0,0)` and `At(k,k)`, and the converse fixed-index cases
      `i=0 \/ i=k`; at prime `2`, `k=0` and the entries coincide.
- [x] Wire and submit the focused five-gate `wilson-inverse-endpoints` WMI
      suite, recursively closing 17 specs, as job `172927` from snapshot
      `7083e3876cc54daa782153aa6e1a2554aa75fa5a40cce3d6cf6b5971979dc35d`
      on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. Syntax and the first
      three bounded cheap gates passed locally; heavy recursive replay,
      profiling, and mutations remain WMI-only. The full runner now has 66
      gates and seven focused suites at that historical checkpoint. Job
      `172927` was later cancelled after consuming zero CPU.
- [x] Submit first replacement job `172968` from snapshot
      `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`;
      it was cancelled after zero CPU when the prefix dependency changed.
- [x] Submit corrected job `172977` from snapshot
      `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`;
      it was pending at submission.
- [ ] Validate pending discovery job `172977`, pin all three candidates'
      exact hashes and structural/identity metrics, and pass a distinct
      immutable admission replay. Its queued receipt is not a pass or theorem
      admission.
- [x] Author isolated `prime_inverse_prefix_nonendpoint_not_fixed` and
      `prime_inverse_prefix_nonendpoint_mate`. For a decoded source whose
      zero-based index satisfies `~(i=0) /\ ~(S i=n)`, the first rules out a
      fixed point and the second proves the involutive mate satisfies the same
      nonendpoint predicate. The contracts remain honest at prime `2`: they
      do not assert distinct endpoints or existence of a nonendpoint index.
- [x] Wire and submit the focused five-gate `wilson-inverse-orbit` WMI suite,
      recursively closing `1+4+3+6+3+2 = 19` specs, as job `172932` from
      snapshot
      `5463565294da6d757356985a0e8d353ad2e0e16ca1b21b99d2aa5cfa6bb5c6f6`
      on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. Syntax and the first
      three cheap gates passed locally; cold replay, profiling, no-DNE/
      capacity checks, and mutations remain WMI-only. The full runner now has
      71 gates and eight focused suites at that historical checkpoint. Job
      `172932` was later cancelled after consuming zero CPU.
- [x] Fix the apply-to-negation error found by cheap orbit-body replay.
- [x] Submit first replacement job `172970` from snapshot
      `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`;
      it was cancelled after zero CPU.
- [x] Submit corrected job `172978` from snapshot
      `6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`;
      it was pending at submission.
- [ ] Validate pending discovery job `172978`, pin both orbit candidates'
      exact hashes and structural/identity metrics, and pass a distinct
      immutable admission replay. Its queued receipt is not a pass or theorem
      admission.
- [x] Pass the cheap bodies for all 19 Wilson candidates. Layered nodes/depth:
      square `182/48`; point `55/22`, `70/28`, `50/21`, `20/12`; prefix
      `76/29`, `64/25`, `29/16`; involution `44/23`, `49/25`, `80/29`,
      `55/29`, `31/22`, `83/31`; endpoints `76/23`, `54/23`, `104/32`; orbit
      `45/26`, `206/40`. Twelve structural gates pass across prefix,
      involution, endpoints, and orbit. These are body-only/structural checks,
      not closed-certificate admission.
- [x] Author isolated `beta_product_double_succ_decompose` and
      `beta_adjacent_unit_pairs_product_one`. The first exposes the final two
      factors of an exact β-product; the second constructively folds `m`
      adjacent unit-congruent pairs to show that the product of the first
      `m+m` factors is congruent to one.
- [x] Reject and cancel pre-start jobs `172936` and `172943`. Their snapshots
      were superseded and known broken after bounded replay found two separate
      missing third length rewrites; neither job is evidence.
- [x] Pass all five corrected `wilson-pair-product` gates locally in 5.4
      seconds, including two cold passes. Pin discovery metrics at
      1,317 nodes/depth 63/844 objects for the decomposition and 4,372 nodes/
      depth 64/1,290 objects for the capstone; graph SHA-256
      `622496753bd474f9f64d5d3001424d3c4513d43d6a5256022cd5a172167959ec`;
      source SHA-256
      `193fe015b32ffde4d93e00720c9fef510a804228e24f19f5cc6c97e8ad5fa724`.
- [x] Submit the authoritative five-gate `wilson-pair-product` WMI replay for
      the exact two-spec graph as job `172946` from snapshot
      `9d890542b964d40580ad2f8f77fa83455de3b9af0f8ca905a37f6a6ee278e296`
      on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. At that checkpoint
      the full runner had 76 gates and nine focused suites.
- [ ] Validate pending job `172946` as an independent WMI admission receipt.
      The complete local pass does not by itself admit either theorem.
- [x] Author the eight-candidate finite-omission stack from constructive
      cover-or-omit search through bounded injective omission. Its body-only
      nodes/depth receipts, in dependency order, are `73/22`, `69/27`,
      `58/23`, `21/15`, `89/31`, `149/43`, `24/16`, and `27/18`.
- [x] Pass the finite-omission contract/dependency,
      hygiene/native/witness, and graph/core/source-isolation gates locally.
      These three structural checks and the body-only metrics are not closed-
      certificate admission and admit no theorem.
- [x] Submit focused `finite-omission` job `172965` from snapshot
      `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`.
      It is `PENDING (Priority)` with zero CPU.
- [ ] Validate job `172965` by closed recursive replay and mutations, then
      require a separate receipt-pinned admission replay.
- [x] Author the isolated ten-spec
      [Euler scaled-inverse ladder](../research/arithmetic-library/euler-scaled-inverse.md):
      bounded existence/uniqueness, symmetry, involution, fixed-point/square
      equivalence, and fixed-point freedom under `~QRes`. Body nodes/depth are
      `36/17`, `30/19`, `58/25`, `126/34`, `74/24`, `31/12`, `28/19`,
      `38/15`, `17/15`, and `24/15`; these dependency-curried receipts are not
      closed replay or admission.
- [x] Lift the pointwise scaled inverse to a full beta-coded predecessor
      prefix. Extension, bounded existence, and full existence check at
      `105/36`, `81/33`, and `40/23` nodes/depth; their exact-contract,
      hygiene, native-syntax, no-DNE body audit passes `4/4` under the laptop
      CPU cap.
- [x] Prove decoded soundness and extensionality, fixed-point freedom under
      `~QRes`, positive-mate predecessor extraction, and decoded involution.
      The five bodies measure `58/25`, `54/26`, `36/27`, `67/36`, and
      `91/39`; their focused no-DNE audit passes `4/4`. Finite two-cycle
      ordering and product comparison remain separate.
- [x] Prove decoded scaled-prefix injectivity directly by symmetry and
      pointwise uniqueness (`77/36`); no finite cardinality or classical
      argument is used.
- [x] Generalize the adjacent-unit product fold to a fixed target residue.
      `beta_adjacent_target_pairs_product_power` proves that `m` adjacent
      decoded pairs, each with product congruent to `a`, have exact
      `2*m`-prefix product congruent to any relational `Pow(a,m,A)` witness.
      Its 118-command dependency-curried body checks at `171/47`, with a
      `4/4` no-DNE audit in 1.71 seconds. It is not recursively closed or
      admitted; the scaled-inverse prefix still has to be reordered into the
      required adjacent two-cycle history.
- [x] Prove the quadratic-residue direction of Euler's criterion under the
      explicit unit premise. The reusable bridge
      `mod_eq_zero_to_dvd_nonzero` checks at `48/18`; then
      `quadratic_residue_half_power_mod_one` uses a square witness, relational
      `pow_mul_exp`, Fermat's predecessor endpoint and modular power transport
      to derive `Pow(a,h,A) -> A == 1 (mod p)` for `p=2*h+1`, at `148/39`.
      The focused exact-contract/no-DNE audit passes `4/4` in 2.11 seconds.
      These remain dependency-curried candidates.
- [x] Open the fixed-point-free Euler PairOrder with the correct shifted
      closure relation: the scaled prefix stores actual mates `S j`, not raw
      zero-based indices `j`. Four bodies transfer omission across a back
      edge, preserve shifted closure under a two-entry append, choose an
      omitted distinct orbit under `~QRes`, and append it while preserving
      closure and order injectivity. They check at `34/20`, `184/40`,
      `107/38`, and `190/52`; the focused no-DNE audit passes `3/3` in 2.78
      seconds. The terminal iteration below consumes this one-orbit entrance.
- [x] Author the isolated nine-spec Wilson
      [PairOrder extension](../research/arithmetic-library/pair-order-encoding.md):
      append/reflection, constructive unused-nonendpoint and inverse-orbit
      choice, invariant preservation, injectivity, and one choose-and-append
      step. Body nodes/depth are `63/27`, `115/32`, `113/30`, `138/43`,
      `34/20`, `167/38`, `63/31`, `202/36`, and `191/53`.
- [x] Validate all three new focused submissions remotely with exit zero after
      changing the transport from `bash -l -s` to `bash -s`; the WMI
      login-shell logout hook had overwritten successful test-only status.
      Submit exact snapshot
      `8c9c4ae067b0dc202684e410bee563cd592a67080cb7c9939440ae8b44d4bccd`
      as pending zero-CPU jobs `173015` (`euler-scaled-inverse`), `173016`
      (`gauss-signed-prefix`), and `173017` (`wilson-pair-order`).
- [x] Record the first frozen WMI selection surface: 101 gates across 22 test
      source modules, exposed as 14 focused five-gate suites plus `full`.
- [ ] Validate jobs `173015` and `173017` by recursive closure, profiles,
      no-DNE/capacity and every-direct-Cut mutations on WMI, then require
      separate receipt-pinned admission replays. Those frozen jobs cover only
      the earlier entrance candidates; the later PairOrder layers below remain
      body-valid candidates until their own WMI snapshots are reviewed.
- [x] Correct PairOrder state with decoded boundedness and author fifteen
      follow-on candidates for state preservation, zero/base facts,
      remaining-pair arithmetic and terminal nonendpoint coverage. Body
      nodes/depth are `95/40`, `19/12`, `69/27`, `90/42`, `23/19`, `18/14`,
      `20/16`, `22/18`, `64/19`, `8/8`, `12/9`, `266/44`, `33/20`, `72/37`,
      and `51/36`.
- [x] Submit focused `wilson-pair-order-induction` job `173022` from exact
      snapshot
      `fd129d34bf4a31a131a28d55bc6a16153984e0d37ac24dcefe7c2735cfb058d1`;
      it is pending with zero CPU and has no proof result.
- [x] Confirm the second frozen WMI surface: 111 gates across 24 test sources,
      exposed as 16 focused five-gate suites plus `full`.
- [x] User-hold superseded full jobs `172707`, `172716`, `172722`, and
      `172737` to prioritize focused prerequisite discovery. This is reversible:
      the jobs were not cancelled and are to be released after focused results
      settle.
- [x] Complete paired PairOrder induction with an explicit adjacent-orbit
      history, terminal specialization, successor lifting, and the generic
      adjacent-pair product-one endpoint. The seven history/iteration bodies
      measure `34/16`, `38/17`, `19/15`, `114/31`, `122/40`, `169/39`, and
      `52/26`; the four lift/product bodies measure `17/11`, `124/38`,
      `41/31`, and `65/32`. These are dependency-curried only.
- [x] Reindex the lifted terminal order to the canonical nonendpoint residue
      prefix and transport its exact product. The four isolated bodies
      `pair_order_terminal_state_magnitude_range`,
      `pair_order_predecessor_range_two_successor_lift_aligned`,
      `pair_order_terminal_successor_product_eq_range_two`, and
      `prime_wilson_terminal_product_package_exists` measure `80/30`,
      `152/42`, `79/39`, and `188/65` nodes/depth. Their focused test passes
      `3/3` under a 60-second process CPU cap; this is not recursive closure or
      admission.
- [x] Restore endpoint factors and identify the exact factorial relation.
      Seven isolated bodies prove `Factorial(1)=1`, the missing leading-unit
      `Range2` bridge, last-factor restoration, modular restoration, the
      constructive prime-2/odd split, the terminal product projection, and
      `prime_factorial_wilson_congruence`. The largest body is `258/45`; all
      seven replay in 3.63 seconds and the focused audit passes `3/3`.
      Prime `2` is handled separately and never invokes the odd PairOrder.
- [x] Iterate the fixed-point-free scaled involution to a terminal
      adjacent-orbit order while preserving shifted orbit semantics,
      boundedness, injectivity, and an explicit adjacent scaled-orbit history.
      The ten dependency-curried bodies measure `23/19`, `19/15`, `114/31`,
      `49/18`, `125/40`, `80/24`, `40/15`, `155/39`, `41/25`, and `64/26`
      nodes/depth. Their exact-contract, hygiene, registry-isolation and
      no-`DNE` focused audit passes `4/4` in 4.72 seconds. The authoring audit
      corrected composite-length parenthesization, simplification order,
      typed terminal specialization, both injectivity-bound rewrites, and
      hygienic formula generation without changing the mathematical route.
      These candidates are unregistered and not admitted.
- [x] Align the terminal scaled order with the successor-lifted product
      prefix, apply the generic adjacent-target product/power fold, and prove
      the bounded nonresidue half-power endpoint. Five bodies establish
      adjacent target products, exact factorial alignment, the terminal power
      congruence, the nonresidue package, and the public bounded endpoint at
      `132/39`, `144/45`, `136/52`, `61/34`, and `49/30`. The focused audit
      passes `4/4` in 4.39 seconds and the related body-only Euler run passes
      `16/16` in 12.19 seconds. For `p=S n`, `n=h+h`, `0<a<p`, `~QRes(p,a)`
      and `Pow(a,h,A)`, the endpoint proves `A == n (mod p)`.
- [x] Prove Wilson's theorem at the isolated dependency-curried candidate
      level: `p=S n -> Prime(p) -> Factorial(n,F) -> F == n (mod p)`.
- [ ] Complete WMI closure/admission for Wilson and Fermat.
- [ ] Run recursive WMI closure, capacity/no-DNE profiling, direct-Cut
      mutations, and a separate receipt-pinned admission replay for the Euler
      terminal-iteration graph and its eventual endpoint.
- [x] Package the residue/nonresidue branches into the full bounded odd-prime
      Euler criterion with actual `QRes`. Seven isolated bodies derive
      nondivisibility from `0<a<p`, rule out `1 == p-1`, construct the
      residue/nonresidue dichotomy, prove both iff directions, and expose one
      complete package at `20/13`, `65/19`, `56/25`, `120/39`, `92/30`,
      `91/37`, and `80/31` nodes/depth. The focused audit passes `4/4` in
      1.67 seconds and the combined bounded Euler run passes `12/12` in 7.62
      seconds, with no `DNE`, `auto`, `ring`, registration, or admission.
- [x] Add division/remainder reduction and congruence transport from an
      arbitrary unit representative to the bounded Euler package. Six bodies
      construct a canonical nonzero remainder, transport `QRes`, transport a
      relational power witness, prove the two arbitrary residue/nonresidue
      iff statements, and expose the complete package. They check at `49/20`,
      `38/17`, `29/22`, `140/36`, `146/37`, and `75/29`; the focused audit
      passes `4/4` in 2.04 seconds and the combined Euler run passes `16/16`
      in 9.96 seconds. The final assumptions are `p=S n`, prime `p`,
      `p` not dividing `a`, `n=h+h`, and `Pow(a,h,A)`—no boundedness premise
      on `a` remains.

Exit gate: the combined Euler package stays below 100,000 distinct objects and
preferably below 250,000 structural occurrences; otherwise pause for the
self-contained proof-DAG review.

## M24 — QR-3 Gauss's lemma

- [x] Prove natively that the predecessor of a modulus squares to one and
      that its relational powers alternate by exponent parity.
- [x] Prove positive half-range bounds and equality/modular injectivity for
      the β-coded interval $1,\ldots,(p-1)/2$.
- [x] Author isolated `odd_upper_remainder_reflection` and
      `gauss_pointwise_signed_half_representative`. Their body-only laptop
      receipts are 125 nodes/depth 34 and 116 nodes/depth 38; all three
      bounded structural gates passed. This establishes the pointwise
      candidate layer, not yet a β-coded signed-half prefix.
- [x] Submit focused `gauss-signed-half` job `172964` from snapshot
      `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`.
      It is `PENDING (Priority)` with zero CPU. The local body/structure
      receipts are not closed-certificate admission and admit no theorem.
- [ ] Validate job `172964` by closed recursive replay and mutations, then
      require a separate receipt-pinned admission replay.
- [x] Author the isolated seven-candidate signed-prefix ladder: explicit
      pointwise choices, full-range choices, simultaneous magnitude/sign
      β-prefix extension, generic and full-range prefix existence, `AllBits`
      projection, and relational `BitCount` existence. All nine bodies,
      including the two earlier signed-half candidates, pass the bounded
      dependency-curried kernel preflight; the seven new bodies measure
      `73/27`, `133/39`, `164/47`, `70/31`, `33/22`, `35/25`, and `31/26`
      nodes/depth. This is not closed replay or admission.
- [ ] Validate pending zero-CPU job `173016` from exact snapshot
      `8c9c4ae067b0dc202684e410bee563cd592a67080cb7c9939440ae8b44d4bccd`
      by recursive closure, profiling, no-DNE/capacity, deterministic-hash,
      false-contract, and every-direct-Cut mutation gates on WMI; require a
      separate receipt-pinned admission replay.
- [x] Author the eleven-spec magnitude-permutation endpoint; body nodes/depth
      are `39/25`, `48/24`, `96/34`, `169/50`, `626/70`, `157/45`, `31/25`,
      `87/30`, `48/20`, `60/31`, and `39/21`.
- [x] Submit focused `gauss-magnitude-permutation` job `173021` from exact
      snapshot
      `fd129d34bf4a31a131a28d55bc6a16153984e0d37ac24dcefe7c2735cfb058d1`;
      it is pending with zero CPU and has no proof result.
- [x] Author three body-green magnitude product-alignment candidates at
      `51/28`, `127/39`, `72/34`, and two sign-product/power candidates at
      `35/24`, `259/46`. These are dependency-curried only.
- [x] Construct the β sign-factor and generic pointwise-product codes and join
      the magnitude, sign, pointwise, and scale folds. The isolated balance
      body proves `A*P == P*R (mod p)` at `148/70` nodes/depth.
- [x] Prove the reusable positive-bounded-prime-product coprimality boundary
      and constructively cancel `P`; the resulting body proves
      `A == R (mod p)` at `156/87` nodes/depth. This is the algebraic heart of
      Gauss's lemma, still dependency-curried and unadmitted.
- [x] Define the upper-half indicator sequence and its β-coded count through
      the signed-prefix and `BitCount` existence layers.
- [x] Relate the sign-factor product to the count by the exact identity
      `Product = (p-1)^e`; parity reduction of predecessor powers is already
      checked in the earlier power layer.
- [x] Package all constructive existence witnesses into
      `gauss_lemma_power_congruence_exists`. Its body has 10 dependencies, 193
      commands, 258 nodes and depth 83, exposes only `e,A,R` plus hidden
      signed/count evidence, and uses no DNE.
- [ ] Run closed WMI replay, profiling, mutations, and a separate pinned
      admission replay for the Gauss power-congruence endpoint.
- [x] Combine the power-congruence package with bounded Euler criterion to
      prove Gauss's lemma for actual quadratic-residue status of a canonical
      representative. `bounded_gauss_lemma_complete` constructs the signed
      `BitCount e` and proves `QRes(p,a) <-> Even(e)` together with
      `~QRes(p,a) <-> Odd(e)`. Its 11-dependency, 204-command body checks at
      597 nodes/depth 53 (559 objects, 596 edges, 38 reused); an independent
      laptop replay passes `5/5` in 7.88 seconds. It remains body-only.
- [x] Replace the bounded representative premise in the complete Gauss
      endpoint by `p` not dividing `a`, using the arbitrary-representative
      Euler package. `arbitrary_gauss_lemma_complete` retains the original
      signed-prefix/count provenance and both actual-QRes iff conclusions at
      547 nodes/depth 49 (513 objects, 546 edges, 34 reused). Its focused
      audit passes `4/4`, and bounded plus arbitrary endpoints pass `9/9` in
      13.64 seconds. Both remain dependency-curried and unadmitted.
- [ ] Add the first supplementary law for (-1).

Exit gate: a closed Gauss certificate, mutation suite and browser replay.

## M25 — QR-4 Eisenstein and reciprocity

- [ ] Construct the two quotient/floor sequences from division witnesses.
  - [x] Build the generic native `DivisionPrefix` layer over an arbitrary
        beta-coded source prefix. `beta_division_prefix_extend` and
        `beta_division_prefix_exists` check dependency-curried at `132/41`
        and `71/30` nodes/depth, with `94` and `62` commands; the focused test
        passes `4/4` under a 60-second CPU cap.
  - [x] Specialize to the exact half-range multiplication source and construct
        its quotient sum. `beta_scaled_successor_prefix_from_pointwise`,
        `prime_scaled_half_division_prefix_exists`, and
        `prime_scaled_half_quotient_sum_exists` check at `34/24`, `71/40`,
        and `52/28`; their focused test passes `4/4` in the capped lane.
  - [x] Relate one arbitrary orientation's quotient sum to its semantic
        rectangle total. Pointwise entry matching, exact sum transport, and
        endpoint functionality check at `104/52`, `73/54`, and `67/51`; the
        focused audit passes `4/4` in 4.92 seconds. The theorem is symmetric
        under exchanging `p,h` with `q,k`.
  - [ ] Instantiate the two orientations needed by Eisenstein inside the
        final lattice package and relate their semantic totals by the nested
        complement partition.
- [ ] Prove the lattice rectangle partition and its finite count.
  - [x] Eliminate diagonal equality for distinct odd primes and orient every
        bounded half-rectangle cell constructively. The noncollision, exclusive
        cell, and universal rectangle bodies check at `72/30`, `77/34`, and
        `53/34`; the focused audit passes `4/4` under the CPU cap.
  - [x] Add concrete beta-coded row indicators: pointwise bit choice,
        extension, induction, prime-specialized choices, `AllBits`, decoded
        semantics, and native row `BitCount`. The seven bodies measure
        `46/29`, `71/27`, `58/23`, `53/34`, `27/16`, `43/23`, and `63/29`;
        their focused audit passes `4/4`.
  - [x] Beta-code the semantic row-count witnesses over `i<h` and sum that
        outer prefix. Eight bodies cover fixed-row choice, append/induction,
        bounded/full prefix existence, decoded soundness and the final native
        `Sum`, at `39/25`, `71/27`, `58/23`, `40/27`, `37/26`, `30/23`,
        `43/23`, and `40/22`; the capped audit passes `4/4` in 2.22 seconds.
  - [x] Prove the generic nonzero-remainder division threshold
        `p*S(j)<n <-> S(j)<=q` from `n=p*q+r`, `r!=0`, and `r<p`.
        Its 67-command constructive body checks at `92/30`; the focused
        audit passes `4/4` in 0.30 seconds.
  - [x] Prove remainder nonzeroness with the sound bound orientation. The
        generic prime/nondivisor theorem, distinct-prime wrapper, and corrected
        own-half wrapper check at `47/21`, `45/24`, and `45/28`; their `4/4`
        no-DNE audit takes 0.40 seconds. The tempting cross-half claim is
        false (`p=3`, `q=7`, `i=2`) and is pinned as a regression test.
  - [x] Prove the odd-half quotient bound without primality or remainder
        assumptions. `odd_half_cross_product_gap` gives
        `(2*k+1)*h < (2*h+1)*S(k)` at `160/45`, and
        `odd_half_division_quotient_bounded` derives `d<=k` at `67/29`.
        Their focused no-DNE/no-ring audit passes with the remainder suite
        (`8/8` in 0.54 seconds).
  - [x] Prove the generic exact-initial-segment count. Eight bodies construct
        the threshold-indicator beta prefix, recover decoded semantics, prove
        the all-one base count, and derive functional/exact `BitCount=q`.
        Their nodes/depth are `23/12`, `63/25`, `40/19`, `25/14`, `41/21`,
        `91/28`, `160/37`, and `49/21`; the full focused no-DNE audit passes
        `11/11` in 2.09 seconds.
  - [x] Add exact extensional transport for relational sums.
        `beta_sum_transport_prefix` reuses a source sum trace whenever a
        second beta prefix decodes the same bounded entries. Its dependency-
        free 44-command body checks at `59/29`; the focused audit passes
        `3/3`, and the combined count/transport run passes `14/14` in 2.20
        seconds.
  - [x] Add exact pointwise addition for three relational sums.
        `beta_sum_pointwise_add` proves `n+m=q` when three equal-length beta
        prefixes have exact `Sum` values `n,m,q` and every third decoded
        entry is the sum of the corresponding first two. Its six-dependency,
        127-command constructive body checks at `195/57` with no object
        reuse or `DNE`; the focused audit passes `3/3`.
  - [x] Evaluate constant beta-prefix sums exactly. `beta_repeat_sum_exact`
        proves any `Sum` over a length-`l` `Repeat(a)` prefix equals `l*a`,
        and `beta_repeat_sum_exists_exact` packages the code, trace, and
        endpoint. Their constructive bodies check at `85/32` and `33/21`;
        the focused audit passes `4/4` and the combined constant/pointwise sum
        run passes `7/7` in 2.18 seconds.
  - [x] Prove the one-dimensional complement-count identity.
        `complementary_bit_counts_add_length` derives `n+m=l` from two
        length-`l` `BitCount` witnesses whose decoded entries are exactly
        `(0,1)` or `(1,0)`. Its 112-command constructive body checks at
        `220/46` with nine shared objects; the focused audit passes `3/3` in
        1.47 seconds. A nested transpose/Fubini bridge is still required.
  - [x] Identify each semantic row `BitCount` with its decoded division
        quotient. Four bodies transport the row predicate to the exact
        initial-segment relation, derive `BitCount=d`, connect it to a decoded
        quotient entry, and consume the rectangle layer's existing semantic
        row witness. They check at `78/36`, `95/45`, `111/55`, and `119/72`;
        the focused no-DNE/no-auto/no-ring audit passes `4/4` in 3.40 seconds.
  - [x] Instantiate exact sum transport between a quotient prefix and its
        outer row-count prefix. The three entry/transport/endpoint bodies are
        `104/52`, `73/54`, and `67/51`; their related five-suite run passes
        `19/19` in 10.71 seconds.
  - [x] Expose exact complementarity at the transposed semantic interface.
        `eisenstein_transposed_decoded_cell_bits_complementary` checks at
        `95/33`; opening both outer entries, their existential inner rows and
        the transposed cell bits checks at `116/58`. Their focused tests pass
        together `6/6` in 2.08 seconds.
  - [x] Construct one coherent transposed column from a fixed original row,
        retaining swapped-outer, inner-row, `BitCount`, and decoded-cell
        provenance at every entry. Six candidates cover choices, extension,
        prefix existence, `AllBits`, pointwise complementarity, and the exact
        row/column count partition `n+m=k`; they check at `42/26`, `80/31`,
        `64/29`, `56/33`, `87/47`, and `117/56`. The focused audit passes
        `5/5` in 5.21 seconds and a related five-suite run passes `18/18` in
        10.39 seconds. This does not identify the sum of column counts with
        the swapped outer total.
  - [x] Beta-code and sum all coherent transposed-column counts. Eight bodies
        construct the provenance-carrying outer prefix, recover each decoded
        row/column partition, attach an exact `Sum M`, align the pointwise
        equation with a constant `Repeat(k)` prefix, and use exact sum
        addition/evaluation to prove `N+M=h*k`. Their receipts are `70/32`,
        `88/35`, `68/33`, `59/28`, `51/26`, `60/36`, `61/43`, and `116/61`;
        the focused audit passes `5/5` in 13.29 seconds and a related five-
        suite run passes `21/21` in 23.05 seconds.
  - [x] Prove the native nested row/column decomposition/Fubini bridge. The
        universal induction identifies every genuine transposed-column total
        with the swapped semantic total at `264/65`; the constructed-prefix
        specialization proves `M=T` at `49/33`, and composition proves
        `N+T=h*k` at `65/37`. The recovered row-decomposition, universal
        Fubini and quotient endpoint suites pass `12/12` in an independent
        45.25-second replay.
- [x] Prove the two floor-sum identity and its parity form.
  - [x] Tie both decoded quotient traces to the semantic rectangle totals.
        `distinct_odd_prime_eisenstein_quotient_sum_identity` proves the exact
        native identity `Q+U=h*k` at `145/68`, with SHA-256
        `d10467b948c749bcf5727127213b5337583b3bba415da7d30a1589ede66116ae`.
  - [x] Prove the generic pointwise signed-division parity bridge. Five
        constructive bodies show that equal parity gives congruence modulo
        two, transport `a*x=p*q+r` through odd `a,p`, handle the reflected
        equation `r+m=p`, and conclude
        `x == q+m+s (mod 2)` from the exact lower/reflected sign branch.
        Their nodes/depth are `53/15`, `77/27`, `87/27`, `64/22`, and
        `43/25`; the focused audit passes `5/5` in 0.56 seconds.
  - [x] Align the independently encoded canonical half range, scaled prefix,
        division quotient/remainder prefix and Gauss magnitude/sign prefix.
        Four exact remainder-alignment bodies construct the complement and
        prove `r=m` or `r+m=p`; their receipts are `238/39`, `53/22`,
        `49/24`, and `115/35`. The two composition bodies then prove the
        generic odd signed-division congruence at `58/34` and the common-index
        β-prefix endpoint `x_i == q_i+m_i+s_i (mod 2)` at `250/61`.
        Exact hashes, dependencies, lengths and identity metrics are pinned;
        five related suites pass `21/21` in 3.07 seconds. All are isolated,
        dependency-curried bodies rather than admissions.
  - [x] Aggregate the common-index congruence into terminal sums and cancel
        the magnitude sum using exact finite-sum permutation invariance.
        `beta_sum_pointwise_mod_three_add` lifts the pointwise relation across
        three exact beta-prefix sums at `328/66`. The Gauss--Eisenstein
        specialization aligns the magnitude prefix with the canonical
        half-range permutation, identifies their exact sums, and uses
        `mod_two_cancel_middle` to prove
        `gauss_eisenstein_sign_count_mod_quotient_sum`: `Q == E (mod 2)`
        while retaining every scaled, division, signed, count, and quotient
        code parameter. Its terminal receipt is `89/65`; pointwise,
        aggregation, and cancellation replay together `12/12` in 17.47
        seconds. All bodies remain isolated, dependency-curried, unregistered
        and unadmitted.
- [x] Prove the constructive final parity truth tables. Six isolated bodies
      show that an even/odd
      Gauss-count sum yields equal/opposite QRes status, transport that result
      from congruence with `h*k`, and derive the one-mod-four and both-three-
      mod-four cases. Their nodes/depth are `48/17`, `48/17`, `31/20`,
      `31/20`, `56/27`, and `52/26`; the focused audit passes `4/4` in 0.93
      seconds. The later terminal aggregation supplies their count-sum
      congruence premise in both prime orientations.
- [x] Construct one provenance-preserving existential package joining both
      orientations of Gauss's lemma to the exact quotient-sum identity.
      The one-orientation constructor hides its half-range and signed-prefix
      machinery while retaining scaled/division quotient data, a complete
      QRes/count classification and `e == Q (mod 2)`; it checks at `139/67`.
      `distinct_odd_primes_gauss_eisenstein_data_exists` invokes that package
      twice, adds mutual nondivisibility and the exact Fubini endpoint, and
      exposes only `e,f,Q,U`, the two classifications, the two congruences,
      and `Q+U=h*k`; it checks at `222/77`.
- [x] Prove same-status reciprocity when one prime is (1\pmod4). The theorem's
      statement is exactly `QUADRATIC_RECIPROCITY_SAME_CASE`; its two-
      dependency, 46-command body checks at `73/33`.
- [x] Prove exactly-one reciprocity when both primes are (3\pmod4). The
      statement is exactly `QUADRATIC_RECIPROCITY_OPPOSITE_CASE`; its body
      has the same `73/33` receipt.
- [x] Package the combined native quadratic-reciprocity theorem. The exact
      predeclared `QUADRATIC_RECIPROCITY_COMBINED` surface checks at `54/22`,
      with no auxiliary count, quotient, half, or beta-code variables. Its
      first body was then structurally optimized: the final wrapper now
      constructs the two-orientation data once and shares it across both case
      implications, checking at 3 dependencies, 65 commands and `113/35`.
      The statement and pinned hash are unchanged. A
      downstream integration replay passes `20/20` in 27.25 seconds. These
      three certificates are body-green only; the recursive closure is now
      statically known to exceed policy, so the unchanged-kernel layered
      closure, dependency/formula/certificate mutation gates, capacity
      profiling and receipt-pinned admission remain mandatory.
- [ ] Add the supplementary law for (2); scope Jacobi reciprocity separately.

Exit gate: the combined endpoint checks below 500,000 occurrences, 100,000
objects and depth 256, rejects formula/certificate/dependency mutations, and
passes cold CPython and browser/Pyodide replay. If it does not, use a reviewed
self-contained proof-DAG bundle; never trust an external theorem name or hash.
Static dependency discovery currently reaches 557 unique specifications at
dependency depth 45, but 191,669 theorem-certificate occurrences before even
counting body nodes. A sharper static lower bound is decisive: recursive Cut
expansion contributes 191,668 Cuts, the repeated dependency-curried scripts
contribute 348,145 leading theorem introductions, and every theorem occurrence
needs at least one terminal body node. Hence the old tree has at least 731,482
proof nodes before any substantive `apply`, `split`, `exists`, or arithmetic
node. It cannot pass the 500,000 policy, so raising the limit without measuring
the much larger actual tree would be unsound engineering.

The preferred capacity route requires no kernel extension: compile the
557-spec, 1,791-edge DAG into 45 topological layers (maximum width 63), package
each layer as a balanced conjunction, discharge direct dependencies by
projections from earlier packages, and Cut each package once. Every theorem
body then occurs once. The result is an ordinary existing Peano Lab `Proof`
checked by unchanged `check((), certificate, QR)`. A content-addressed
`ClosedCut`/proof-DAG format remains fallback-only if this layered certificate
misses measured resource gates.

The WMI transport now separates three meanings. The six-gate
`quadratic-reciprocity-final` suite retains exact body plus source/graph
statics; the nine-gate `quadratic-reciprocity-layered` suite is the actual
unchanged-kernel admission experiment; and the three known-over-budget
recursive gates are isolated as `quadratic-reciprocity-recursive-diagnostic`
and excluded from `full`. The layered and full profiles request one CPU,
32 GiB and four hours. The hardened bounded integration gate passes `42`
selected tests with four WMI-only functions skipped, and suite manifests pin
`9/6/3` selectors. Payload-specific permission was subsequently granted for
SHA-256
`2bab0898a5bc628a0e1f06b5e6cdf56af86fe39c2fdbeaaa4147ac43d2c7faaa`.
The wrapper uploaded and remotely verified that exact 338-member,
5,374,464-byte dirty snapshot, passed scheduler validation, and submitted full
136-gate job `187187` on `cpu_idle` with one CPU, 32 GiB and four hours. Its
final state is `FAILED` after 39 seconds with exit code `1:0`. The first four
scaled-inverse gates passed; gate 5 found an unused `succ_ne_zero` dependency,
and the remaining 131 gates did not run. This fail-closed hygiene result is
not a mathematical rejection or a QR proof receipt.

- [x] Implement and statically audit the unchanged-kernel layered Cut-bundle
      compiler. The hardened compiler scans all 25 exact kernel proof
      constructors, rejects `DNE`, holes, metavariables and malformed nodes,
      and bounds repeated formula/term annotations plus combined envelope
      depth. Its focused and integration gates pass without real-body laptop
      replay. A 20-node
      sharing fixture shrinks from `3,643/20` recursive nodes/depth to
      `274/16`. The real 557-node formulas with false one-node bodies produce
      a rejected `13,715/56` scaffold and exact package-formula cost
      `144,197/68`, plus `157,579/92` annotations/envelope depth; a
      distinct-marker, dependency-consuming surrogate checks
      every real edge/order under the unchanged kernel at `19,088/74` with
      package cost `19,297/18` and annotations/envelope `142,346/84`. Neither
      surrogate is QR evidence.
- [x] Remove the QR stack/registry import cycle through an injected copied
      pre-QR mapping while preserving the exact 317-candidate order and hashes.
- [x] Make bare `pa lib` list statements without replay and add the
      deterministic 147-file Pyodide worker-source inventory gate.
- [x] Audit the 125 pre-admission test assumptions and pin the exact
      317-enrolled/29-omitted migration in
      `quadratic-reciprocity-test-migration.md`.
- [x] Freeze and audit the external WMI payload before transport. The cleaned
      337-member, 5,343,232-byte archive excludes caches, bytecode and
      `.DS_Store`; two builds agree at
      `13f279cf2390104009825abac01c17e8b96d56bb764719964e36949ea3345a43`,
      and source/extracted transport checks pass `9/9`. This is not a WMI
      result; upload permission is valid only for that exact hash.
- [x] Upload the subsequently approved 338-member snapshot
      `2bab0898a5bc628a0e1f06b5e6cdf56af86fe39c2fdbeaaa4147ac43d2c7faaa`,
      verify its remote digest and 5,374,464-byte size, pass `sbatch`
      validation, and submit full 136-gate job `187187`. The snapshot records
      base commit `a549a537cfe3d3d7e8ef292a49250c4308d12c5d` with
      `local_dirty=true`.
- [x] Retrieve and diagnose job `187187`: it failed closed at gate 5/136
      because `prime_scaled_inverse_target_nonzero` declared but did not use
      `succ_ne_zero`; four gates passed and 131 were unrun.
- [x] Remove that redundant edge, preserve the mutation test, refresh all
      graph/source/scaffold pins, regenerate the Proof Explorer, and pass the
      focused local replay/topology/Explorer suites.
- [x] Freeze the corrected archive twice at exact SHA-256
      `989011c09d82dbbb239df43334e88553e1fb3e0d2f1033f93c5b8b1791851757`;
      both builds contain 338 members and 5,374,464 bytes.
- [x] Obtain content-specific approval, upload and remotely verify that exact
      clean snapshot, pass Slurm test-only validation, and submit all 136
      gates as job `210714` with one CPU, 32 GiB and four hours.
- [x] Retrieve and diagnose job `210714`: it failed closed at gate 15/136
      after 14 passes because the direct-edge mutation
      `odd_upper_remainder_reflection -> add_succ_left` did not invalidate the
      certificate; 121 gates were unrun. Record that this is a
      dependency-minimality failure, not a kernel-soundness failure or QR
      result.
- [ ] Remove or justify that redundant edge, refresh every affected pin, and
      obtain a complete passing 136-gate receipt before any admission claim.
- [ ] After those gates pass, migrate the generic layered closure into the
      public theorem replay/registry without a theorem-name or hash trust
      shortcut; regenerate the catalog and run cold Pyodide `use` gates.
- [ ] Only if that route fails, review a closed-proof-reference/DAG kernel
      representation; do not merely increase the recursive-tree limit.

## Documentation and training at every gate

- [x] Regenerate the deterministic theorem snapshot and dependency graph.
- [x] Synchronize the research catalog and source register.
- [x] Regenerate Obsidian lemma notes and the arithmetic-library MOC.
- [x] Regenerate the interactive Jupyter Book theorem atlas.
- [x] Update the quadratic-reciprocity chapter and roadmap diagram.
- [x] Generate the native PA Proof Explorer for the exact 557-node closure:
      persistent `PAxxxx` tags, 557 canonical pages and name aliases, 1,791
      forward/reverse edges, 27,491 tactic-line anchors, syntax-aware theorem
      and PA-axiom links, truthful public/candidate status, and explicitly
      generated-versus-curated informal proofs. The QR endpoint is `PA00FW`.
- [x] Integrate the explorer into the Jupyter Book with a searchable embedded
      dashboard, direct QR links, PA grammar and axiom/rule chapters,
      foundations/tactic navigation, responsive isolated assets, deterministic
      `--check`, and bounded static/security tests.
- [x] Add graph v2 to the Book and explorer: 557 theorem nodes, 1,791 direct
      edges, 45 layers, and 48 corpus roots distinct from the PA foundations.
      For `PA00FW`, expose the 4-vertex shortest chain, 45-vertex critical
      chain, complete prerequisite cone, and all 101,293 theorem-root paths.
      This is navigational evidence only; `PA00FW` remains pending layered
      closure.
- [x] Add the conservative defined-notation edition over the same exact
      closure: a 40-entry persistent `PD` registry (38 definitions used), 557
      theorem pages, 27,491 tactic lines, 506 compacted statements, and
      1,275/1,839 compacted local propositions. Exact expansion/native-replay
      receipts preserve the theorem graph and the
      `240 public / 316 body-checked / 1 pending layered closure` status split;
      the readable `PA00FW` remains a candidate.
- [x] Add the static-clean
      [WMI Jupyter Book build harness](../docs/WMI_JUPYTER_BOOK_BUILD.md).
      Its independent static audit findings are remediated. Test-only
      scheduler validation succeeded for the 125-file snapshot
      `6feb5ebcdb9f59e6d94b71acd3fb2bce06d45b3a3885ad95aa8e9c02d61a3bcb`
      with content-manifest SHA-256
      `c09064eb67906761c357626df4ee9e0cf387a89b7593654c8c5bf74baf836c24`.
- [ ] Validate pending Book job `173024`, last observed `PENDING (Priority)`
      with zero CPU. Do not claim a Book-build or integrity result until its
      snapshot-bound receipts exist and pass review.
- [ ] Create a fresh content-addressed Book snapshot containing the Proof
      Explorer and run the strict WMI build plus built-copy/link/fragment
      integrity gate. The earlier 125-file snapshot predates the explorer and
      cannot validate it.
- [ ] Run attached-browser smoke tests for search, filters, theorem/informal
      links, tactic and axiom jumps, line anchors, Back/Forward, keyboard
      access, mobile layout, and dark mode. The current session had no
      attached in-app browser, so static DOM tests are not a substitute for
      this gate.
- [ ] Export dependency-local training examples without granting the corpus
      theorem authority.
- [x] Record the initial WMI jobs, hashes, resource policy, and isolation
      boundary in the Book, vault, research notes, journal, and memory.
- [ ] Continue recording commands, hashes, metrics and failures in `JOURNAL.md`, with
      stable architectural conclusions in `MEMORY.md`.
