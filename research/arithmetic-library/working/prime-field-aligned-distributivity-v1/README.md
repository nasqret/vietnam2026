# Convolution distributes over independently aligned sums

This working-only pair lifts the canonical fixed-length distributivity laws
to independently represented polynomials.

Both the left and right theorem assume Prime(p), AlignedAdd(U,V,W), and three
actual supplied proper products. They conclude AlignedAdd(P,Q,R) for those
outputs. Their proofs construct genuine common-length products, apply the
existing fixed-length distributivity theorem, and transport the result using
formal polynomial equivalence. Output equivalence is not a premise, and no
new multiplication or addition operation is defined.

The original conditional HA checker accepted the left body at 262 nodes,
depth 71, and the right body at 263 nodes, depth 71. These are not
dependency-complete or Lean certificates and do not admit any theorem to Alpha.

The final suite has 253 distinct cases: 211 independent source/contract/model
checks and 42 native positive/rejection cases. Native selections were
left-basic 11, right-basic 11, left-dependency 10, and right-dependency 10.
Its sorted exact pytest-ID digest is
8b808690b3b657a80e2f3c143cae3eb8abe74484294b1f0231d1f1e1489dadc5.

The shared
[focused observations](../prime-field-euclidean-identity-v1/focused-observations-v1.json)
and [exact commands](../prime-field-euclidean-identity-v1/focused-test-commands-v1.json)
preserve all six final native windows for this pair and the identity pair,
their disjoint 495-case accounting, unchanged source/archive pins, and the
zero-credit failed scheduling attempt. Original resource limits and all
kernel/codec/checker bytes remain unchanged. These records are observations,
never authority for a later complete-cone check, admission or publication.
