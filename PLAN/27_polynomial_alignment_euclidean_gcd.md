# Polynomial alignment, Euclidean transport, and normalized gcd witnesses

Authorized continuation on 2026-09-01, starting from clean pushed
`2717214d1acb95d775e0d956971ba2c8968d5766`. Follow the mathematical contracts
in [plan 26](26_polynomial_gcd_bezout_witnesses.md).

## Scope and invariants

Implement actual common-length representatives, aligned coefficient algebra,
Euclidean common-divisor and backward Bézout transport, then degree descent
and monic normalization. Each stage needs native proofs, independent expanded
contracts and actual beta models, rejection tests, conservative definition
DAG checks, dependency-complete HA/Lean and ordinary-root verification.
No result is proved merely by declaring its interface or drawing its node.

The old 25/37/44/52 checkpoints stay byte-identical. Alpha remains 4,092 and
Stable remains 432; this implementation request does not authorize promotion,
deployment, a catalogue-capacity change, commits or pushes. Keep all original
CPU 170/175-second, wall 180-second, RSS 1,536-MiB and live-depth 256 bounds.
Only one heavyweight proof/Alpha/Lean job may run at a time.

## Representation interfaces

`CommonRepresentatives(A_L,B_M,U_K,V_K)` is formal equivalence of each
original prefix to its actual length-K representative. It is not itself a
padding assertion or a statement that K is at least both original lengths.
The at-length existence theorem requires those bounds and constructs actual
leading-zero beta prefixes. The unconditional prime-field constructor uses
the explicit common upper bound `L+M`.

The implemented aligned addition graph retains canonical coefficients for the
three original polynomials and existential actual common-length input and
sum prefixes, related by the existing fixed-length addition graph and formal
input/output equivalence. Aligned subtraction reuses addition as `B+R=A`.
No evaluation equality, raw-code uniqueness or algebraic conclusion is an
extra constructor premise. All definitions must remain conservative over
the original HA signature.

## Execution state

1. Source interfaces and canonical reusable contracts passed independent
   review. Seven common-representation bodies pass original conditional HA
   and all 224 focused source/model/body/rejection cases in the separate
   `working/prime-field-alignment-v1` directory. An initial eighth
   helper passed conditional HA but was recognized as the existing
   power-coefficient-functionality statement and removed before any new
   statement or admission credit. No complete dependency-cone or admission
   credit is claimed from these conditional checks.
2. Nine basic aligned-operation bodies pass original conditional HA, including
   existence, transport, functionality and realization on arbitrary supplied
   canonical common-length representatives. All 367 focused cases pass,
   including the 229 independent source/model checks and 138 native cases.
   Four higher algebra bodies also pass: subtraction existence, cancellation,
   addition associativity and subtraction functionality. An initial captured
   local witness binder was rejected and corrected with genuinely fresh names;
   the failure is retained. Their 51 independent source/model checks and a
   separate 49-case expanded-contract suite pass. All 74 native cases also
   pass in 14 original-bounded windows: 174 distinct algebra cases overall.
3. The six genuine left-constant/scalar bridge bodies pass all 332 focused
   cases. The two division-identity bodies and the two aligned-distributivity
   bodies pass original conditional HA. Their combined 410 source/model cases
   passed; all 85 native cases also pass. The combined final suites contain
   495 distinct cases (identity 242, distributivity 253).
4. All five common-divisor transport bodies and all three backward Bézout
   bodies pass original conditional HA and independent source review. The
   latter construct the actual update `(U,V) -> (V,U-V*Q)`; they do not commute
   Q and V or require the resulting identity as an extra hypothesis.
   The constructor initially exceeded the
   original live-depth limit: moving its already-proved sum into a local
   lemma before packaging witnesses fixes that depth without changing the
   statement, prerequisites or any kernel limit. The rejected attempt is
   retained. All 329 independent expanded-contract/model cases pass against
   the final repaired source. All five degree/normalization bodies also pass,
   including the all-input zero-or-monic mutually-dividing representative
   constructor. All 313 focused cases pass: 228 source/model and 85 native
   body/rejection cases, with no change to the mathematical source or test.
5. The initial combined 68-row notation map passes 174 exact AST/DAG cases:
   402 definitions and 876 definition-expansion edges, retaining all 399 old
   working definition objects. The later CommonRightDivisor and Bezout
   definitions have distinct identifiers in a separate 95-row map, preserving
   those 402 objects and extending the registry to 404 definitions and 879
   expansion arrows. All 257 exact AST/DAG cases pass against the final
   95-row source order shared with the complete-cone controller.
6. The separate complete-cone controller is implemented over the actual
   immutable old52 and canonical division121, polynomial202 and field85
   proof artifacts. It plans 11 strict source-order stages ending in
   95 working rows plus 343 canonical ancestors: 438 mathematical nodes,
   1,368 theorem edges, and 15 maximal ordinary roots. Its package adds one
   conjunction node. All 394 initial source/inert controller guards pass,
   with a second read-only review of the original HA/Lean/ordinary paths.
   All 43 new conditional bodies pass, and all eleven actual authoring stages
   now pass original whole-seed and whole-result HA. All 17 final gates also
   pass: same-byte compiled Lean, original HA, all fifteen ordinary principal
   checks and current-Alpha exact-AST novelty. Full recursive normalized gcd/Bézout existence is not
   inferred from these component or backward-transport statements.

### Resource-driven proof refactor

Actual stages 59 through 93 passed under the original limits. Stage 94 reported
its reconstructed body but hit SIGXCPU before finishing whole-result checking;
no stage-94 artifact was written. The failed attempt and all nine valid artifacts
are retained. Scoping copied coefficient facts and auxiliary products alone
did not improve runtime enough. A proved local universal lemma now specializes
the identity's first 25 input parameters before introducing the large witness
context; the remaining 24 parameters are specialized only at its final use.
The original conditional checker accepts the final constructor in 84.979455
seconds at 760,709,120 bytes RSS, with 374 proof nodes, depth 137, and 299 commands.
Direct generated-source comparison confirms all three Bézout statements,
ordered prerequisites and summaries are unchanged, and rows 0 and 2 are exact
in all five fields. The final source is 18,747 bytes, SHA-256
`c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702`.
Model/map/controller source pins were refreshed and the same 329/257/394
substantive cases passed again. Genuine stages 94 and 95 then passed in
133.355468 and 51.324234 seconds. Their actual complete artifact has 439 nodes,
1,383 edges, 40,515 proof-body nodes, 3,446,531 bytes, and SHA-256
`454f23a30acfb9188d7458a9dc206ce9fc14a61510d0c3b548a611a9d682af56`.
It is registered and all 17 final gates pass under source binding
`005eeadb5fe1798f531940bac31c9ae60d9346619459814b998500cb958b2449`.
The final backward Bézout ordinary certificate has 41,328 nodes. The maximum
final-gate runtime is 69.976253 seconds and the maximum measured peak RSS is
485,310,464 bytes. No limit or kernel changed, and old source-bound reports
were not relabeled. All 51 files and 59 file/directory identity records in
the four older checkpoint archives match the pre-work snapshots exactly.

The [completed checkpoint](../research/arithmetic-library/working/prime-field-euclidean-closure-v1/README.md)
links the source groups, definition maps and exact-source verification records.
There are 3,059 distinct substantive focused cases, all passing; historical
reruns and diagnostics are not counted again. The five new conservative
definitions extend the working registry to 404 definitions and 879 expansion
arrows. This is a completed local component checkpoint, not an Alpha admission
or a completed recursive gcd algorithm.

## Following endpoint — still open

The next construction must perform genuine induction on the retained length
of the second polynomial, carrying all intermediate codes, lengths and Bézout
coefficients. Its zero-second-input case must include `(0,0)`. For a nonempty
trimmed second input, actual division gives a strictly shorter remainder;
the proved backward maps transport the recursively constructed witnesses.
The final normalization must transport both divisibility and the Bézout
representation. Greatestness and uniqueness of the zero-or-monic result up
to formal equivalence require their own proofs. None of these endpoints is
closed by the component checkpoint alone.
