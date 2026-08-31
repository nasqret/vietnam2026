# Actual right-factor append recurrence

This working checkpoint contains six constructive, dependency-curried HA theorems. It does not by itself provide a complete dependency bundle, independent Lean verification, Alpha admission, full convolution associativity, or gcd/Bézout.

For highest-degree-first natural coefficient prefixes, an actual append is the existing pair of clauses `BetaPrefixEqual(C,D,M)` and `BetaAt(D,M,c)`. It is not a new definition containing the desired recurrence.

The uniform principal, `prime_field_polynomial_convolution_right_append_equivalent`, starts with `Prime(p)`, actual proper-length products `P=A*C` of length `N` and `Q=A*D` of length `K`, and the following actual witnesses:

```text
Shift(P,N;U)                         U has length S N
Scale(p,c,A;V,L)                     V has length L
LeftPad(U,S N,L;UP)                  UP has length L+S N
LeftPad(V,L,S N;VP)                  VP has length S N+L
Add(p,UP,VP;R,L+S N).
```

The commuted padding length is explicitly reconciled. The conclusion is formal coefficient equivalence `Equivalent(Q,K;R,L+S N)`: in polynomial notation, `A*append(C,c) ≃ X*(A*C)+c*A`. It is neither raw beta-code equality nor a finite-field evaluation identity. No universal `K=S N` relation is assumed or concluded. Empty factors, zero scalar, characteristic two with natural unit `1`, reencodings, and free values beyond every represented prefix are retained.

`prime_field_polynomial_convolution_right_append_exists` genuinely constructs the appended prefix, its proper-length product, the shift, scalar output, both leading pads, and the sum from `Prime(p)`, `c<p`, and an actual old product. The independent aligned-sum constructor needs bounded source and old prefixes, not an assumed product relation. The all-index coefficient lemma uses real diagonal sums and residues at every natural index; it is not restricted to a triangular boundary.

The six source-order rows are:

1. `prime_field_polynomial_append_shift_constant_add`
2. `prime_field_polynomial_append_shift_constant_decomposition_exists`
3. `prime_field_convolution_coefficient_right_append_add`
4. `prime_field_polynomial_shift_scale_aligned_sum_exists`
5. `prime_field_polynomial_convolution_right_append_equivalent`
6. `prime_field_polynomial_convolution_right_append_exists`

There are 42 declared dependency edges and 878 commands. The actual conditional bodies have 137, 115, 108, 158, 448, and 246 nodes respectively (1,212 total occurrences). All 400 distinct focused cases passed in 22 disjoint original-bounded processes, with 1,200 passed setup/call/teardown records. This includes the six actual HA bodies, independently expanded contracts, real beta/sum/residue models, all 42 removed and 42 poisoned dependencies, and 52 altered-contract checks. The longest clean window was 91.913967 seconds; maximum CPU and RSS were 91.057367 seconds and 229,113,856 bytes. Original per-process limits remained 170/175 CPU seconds, 180 wall seconds, and 1536 MiB RSS. The complete suite must be partitioned as recorded; its aggregate runtime is not a single enlarged proof window.

Frozen mathematical pins:

- Source: 28,396 B; SHA256 `271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042`.
- Test: 36,494 B; SHA256 `0c554b05b2c7e2c40e3b0e8044160379a3284bb173e48d59d77def0cad4272aa`.
- Ordered specifications: `6035968b0f11aec5e4bd6cb43b4d4958318b55f600fab914025479f571b75c2a`.
- Ordered 400-test IDs: `43eb3143d43047279c0a6573ed4ba6b9e54ad480cea943c734dfb46e76e3aa71`.

The [conditional observations](conditional-observations-v1.json) are non-authorizing metadata and must never replace live proof checking or an admission guard. Their per-window selectors, slices, ID hashes, original resource bounds, and source pins preserve exact accounting; detailed raw phase and command records were retained separately in the private validation session. The independently maintained [notation note](NOTATION.md) is a presentation aid, not additional mathematical evidence. No new aligned-sum alias is introduced by these six rows.
