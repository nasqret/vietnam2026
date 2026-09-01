# Normalized polynomial gcd uniqueness — working candidates

Status: all eleven source scripts have passed actual original-kernel
**conditional** HA checks, and all **415 distinct focused test cases pass** on
the final source and metric-pinned test bytes. This includes 224 syntax/model
cases and 191 native cases: 11 actual positive regressions, 33 false/missing/
truncated bodies, all 51 removed and 51 poisoned dependency edges, 40 removed
input premises, and five false raw-code uniqueness assertions. The exact
collection reconciles with 1,245 retained passed setup/call/teardown rows.
Earlier positive diagnostics and source-only repeats are not counted twice.
See `conditional-verification-observations-v1.json` and the retained raw window
records. All six rejected development attempts and the unsuccessful launcher
attempt remain recorded with zero credit.

The representations are highest-degree-first, canonical natural residue
coefficients. Formal equivalence compares the coefficient at every natural
power, including zero outside each represented prefix. It does not compare
finite-field evaluations, raw beta codes, or unspecified values beyond a
prefix.

`RightDivides(p,D,A)` retains the existing ND0342 orientation: it contains a
canonical target and genuinely coded witnesses for `Q * D`, formally
equivalent to `A`. The quotient is initially allowed to be empty or to have
leading zeros. `Normal(p,G)` means `Glen=0` or the existing canonical monic
graph. The grouped greatest-divisor and normalized-gcd graphs match the
shared ND0349/ND0350 contracts; this directory does not register definitions.

## Conditionally checked proof chain

1. A nonzero leading coefficient at power `d` forces every formally equivalent
   representation to have length at least `S d`. Apply this in both directions
   to compare genuine represented degrees.
2. Extract the actual quotient from divisibility, trim it, construct a new
   product, and transport formal equivalence with the existing convolution
   congruence law. A nonzero target excludes an empty retained quotient.
3. The existing prime-field product-degree theorem yields `e+d=a` for that
   actual quotient degree. Thus a represented right divisor has degree at
   most its represented target.
4. Mutual divisibility between monic polynomials forces equal degrees. The
   retained quotient then has degree zero. The genuine leading product is
   `k*1=1`; field multiplication functionality gives `k=1`, and the existing
   actual **left-unit** convolution law gives formal equivalence.
5. Empty-divisor branches are proved from actual empty product lengths, with
   no degree assigned to zero. Combining the branches gives the
   zero-or-monic mutual-associate result.
6. The two grouped greatestness clauses yield mutual divisibility of any two
   normalized gcds, so the final intended wrapper concludes formal
   coefficient equivalence.

The main names are
`prime_field_polynomial_normal_right_associates_equivalent` and
`prime_field_polynomial_normalized_gcd_equivalent_unique`.
Both normal premises are essential: distinct nonzero scalar associates can
mutually divide while having different formal coefficients. In particular,
the normalized gcd of two zero polynomials is represented by the empty
normal form, not the polynomial one.

All original kernel/compiler and resource gates remain unchanged. The largest
individual development check used 136,151,040 bytes and 12.646 seconds (rounded
upward). The nine successful native test windows used at most 151,683,072 bytes
and 40.487 seconds (rounded upward), below the original 170/175 CPU, 180 wall,
1,536 MiB RSS and depth-256 gates.
The final source has eleven rows, 51 declared edges and 931 commands. Its
SHA256 is `916c24ad6c59609612e97daee6e49347a9522cdb28b44f6f09c6c5760bff0b5b`;
the metric-pinned test SHA256 is
`6deba14cd0c750c5158c130c8e03f2402861769211605d42d5b61c7bd6936edd`.
The ordered five-field specification digest is
`56620b77f2bcee3c41f52397797afabdbf5e41b874f6a60ce3eac9c7e77c7f3d`.

Conditional checks leave declared dependencies as hypotheses. No Alpha import,
complete-cone proof, Lean verification, admission, deployment, recursive
existence, or uniqueness of Bézout coefficients is asserted here. The JSON
records are accounting only and are not read by the mathematical checker.
