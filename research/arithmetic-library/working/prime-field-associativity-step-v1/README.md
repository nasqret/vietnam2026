# Constructive polynomial associativity: append step

This working checkpoint contains three conditional HA proofs: two alignment/transport helpers and the rightmost-factor append induction step. It does not, by itself, establish the universally quantified associativity theorem, perform Alpha/Stable admission, or publish a reader.

## Exact mathematical boundary

All lists are the existing highest-degree-first, native-beta-coded natural coefficients. `Equivalent` means formal coefficient equality, including leading-zero reencoding; it is not equality of beta codes or equality of evaluations over a finite field. Trailing-zero `Shift` is multiplication by X, not leading-zero padding.

The step assumes `Prime(p)`, an actual product `P=A*B`, actual prefix products `Q0=B*C`, `R0=P*C`, `S0=A*Q0`, and the actual induction hypothesis `Equivalent(R0,S0)`. The rightmost factor is extended using a genuine prefix-equality relation and a beta entry `c`. Given the three actual new products `Q1=B*D`, `R1=P*D`, and `S1=A*Q1`, the conclusion is `Equivalent(R1,S1)`.

Every product length is independent and constrained by its own actual convolution graph. The proof derives `c<p` from the bounded appended factor; it does not assume nonempty A or B, identify unrelated output lengths, or assume the desired new equivalence. Required shift, scalar, padding, addition and intermediate-product witnesses are genuinely constructed.

The three rows are:

- `prime_field_polynomial_convolution_shift_scale_aligned_equivalent`: transports convolution through an actual shifted/scaled aligned sum.
- `prime_field_polynomial_shift_scale_aligned_congruent`: transports formal equivalence through the corresponding actual aligned construction.
- `prime_field_polynomial_convolution_associativity_append_step`: derives the next associativity instance from the actual old instance.

The source has 38 declared dependency edges and 1,122 tactic commands. The final original-HA receipts have exact node/depth pairs `(539,110)`, `(229,72)`, and `(698,140)`. Object-sharing counts are observations, not mathematical invariants.

## Focused verification and rejected history

All 546 distinct focused test IDs passed in 78 clean, disjoint original-bounded windows; all 1638 setup/call/teardown records passed. A fresh collection and byte/specification audit reproduced the exact inventory. The largest successful window used 153.169822 seconds wall time; the maximum observed CPU time was 152.488114 seconds and maximum peak RSS was 1,287,241,728 bytes.

The tests independently expand the three contracts, exercise native-beta witnesses and empty/characteristic-two cases, check every removed and poisoned dependency, and reject the tested dropped premises and stronger claims. Each body is checked by the unchanged original kernel with its exact declared prerequisite formulas curried as hypotheses. This is conditional evidence, not an empty-context dependency-complete certificate.

The first append-step draft failed the original 256-live-depth compiler guard. Its proof receipt, elapsed time and peak RSS are unknown. A source-only scope repair kept every outer statement and declared prerequisite unchanged: only the shared alignment remained outside, while the two separate transport branches constructed and discharged their own witnesses. The repaired body then passed without relaxing any guard.

A later nine-case negative batch hit the original CPU guard and receives zero credit. All nine cases were rerun in disjoint successful bounded windows. No partial or failed run contributes to the final count.

Every successful process retained CPU soft/hard limits 170/175 seconds, a 180-second wall alarm, 1,536 MiB RSS ceiling and the original depth limit. Sources and test inputs were pinned before and after each window. No Alpha import, admission, kernel edit or saved-receipt acceptance was used.

See [conditional observations](conditional-verification-observations-v1.json) for exact source/spec/test-ID hashes, successful window accounting and the uncredited failures. That JSON is an observation ledger only and must never be read as proof authority. The [notation record](NOTATION.md) is likewise a separate source presentation.

The full quantified induction is a separate [working checkpoint](../prime-field-associativity-induction-v1/README.md). Dependency-complete integration, when cited, must use its separate actual proof artifact and checker records; neither this README nor the focused observations substitutes for it.
