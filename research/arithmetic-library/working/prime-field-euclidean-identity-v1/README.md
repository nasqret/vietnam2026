# Division execution to an aligned polynomial identity

This working-only pair connects the actual division execution relation to an
actual proper convolution product and an aligned addition identity. It does
not introduce arbitrary quotient-pair uniqueness, a gcd, or a completed
Euclidean algorithm.

The add-trim-aligned theorem needs no primality assumption. From an actual
fixed-length addition, equivalence of its first summand to a canonical
independently sized representation, and a genuine trim of its second summand,
it derives the aligned sum with the trimmed output.

The division-execution-aligned-identity theorem assumes Prime(p) and the
existing division execution graph. It constructs a proper product P = Q*B
and proves AlignedAdd(P,R,A). An empty quotient is handled by a genuine empty
product and formal equivalence with the ambient zero prefix; the theorem
does not assert that proper product length always equals the dividend length.

Both bodies passed the original conditional HA checker: respectively
87 nodes/depth 47 and 194 nodes/depth 54. This is conditional body evidence,
not a dependency-complete or Lean certificate and not Alpha admission.

The final focused suite has 242 distinct cases: 199 source/contract/model
cases and 43 native positive/rejection cases. The native cases ran in two
disjoint windows of 15 and 28. Its sorted exact pytest-ID digest is
16f17b42b43c448a6fa6c2dac24701af2e28dde7e9d0121a64cbdefaa688689f.

The shared [focused observations](focused-observations-v1.json) also preserve
the separate distributivity pair: 495 distinct cases in total, including six
native windows containing exactly 85 cases. All original CPU, wall, RSS and
proof-depth limits were unchanged. The failed ephemeral collection attempt
stopped before any test body or proof call and receives zero credit.
[Exact commands](focused-test-commands-v1.json) retain that failed attempt,
the corrected quiet collection, actual successful windows, and reconciliation.

The independent
[transport/Bézout model observations](transport-bezout-model-observations-v1.json)
record 329 substantive source/model cases at both the original and repaired
Bézout source pins. Only the literal source-pin parameter changed one display
ID; there are not 658 distinct tests. Those checks make no proof calls.

All observations are historical, non-authorizing data. They must not replace
any fresh complete-cone, original HA, compiled Lean, admission or publication
gate. The sealed 25/37/44/52 archives and current runtime bytes were preserved.
