# Irrationality-first campaign: checked research checkpoint

Active target: positive HA irrationality of `(sqrt2)^(sqrt2)` (IR072 / G121).
Next: full positive transcendence (TR006 / G122). No campaign **parent** theorem
has been proved and no proposed definition has been admitted. Publication is
separate from library admission; see the release status below. The original
eight-leaf pilot is preserved below as a historical
baseline. The shared-proof execution wave adds exact HA and independent Lean
checks; it does not complete the irrationality theorem.

- [Mathematical dossier and execution policy](../../../PLAN/32_sqrt2_power_irrationality_campaign.md)
- [Local campaign landing page](../../../book/_static/constructive-sqrt2-power-campaign/index.html)
- [Lemma/definition planning DAG](../../../book/_static/constructive-sqrt2-power-campaign/map.html)
- [Twelve bounded pilot contracts](../../../book/_static/constructive-sqrt2-power-campaign/pilot.html)
- [Actual pilot results and downloadable certificates](../../../book/_static/constructive-sqrt2-power-campaign/pilot-results.html)
- [Current shared-proof wave and its exact evidence](../../../book/_static/constructive-sqrt2-power-campaign/wave-results.html)
- [Local rational definition DAG](../../../book/_static/constructive-sqrt2-power-campaign/local-definitions.html)
- [Checked arithmetic DAG and open planning parents](../../../book/_static/constructive-sqrt2-power-campaign/arithmetic-frontier.html)
- [Additive combined campaign atlas](../../../book/_static/constructive-sqrt2-power-campaign/grand-campaign/index.html)
- [Machine-readable plan](../../../book/_static/constructive-sqrt2-power-campaign/api/plan.json)

The inventory contains 81 irrationality work packages, 26 proposed definitions,
9 engineering/contingency gates and 6 future transcendence packages. Every
parent contract remains explicitly unproved; the bounded pilot's exact formulas
and checked premises are recorded separately. The existing 120-goal atlas, Alpha, Stable and historical
proof pages remain unchanged.

## Active proof work, 2026-10-11 (research checkpoint)

The full positive irrationality target IR072 remains **open**. 212 additional
exact statements now have fresh original-HA replay and independent checks by a
freshly compiled Lean checker. Together with the published 33-statement
checkpoint, this makes **245 distinct checked statements**, not 245 of the 81
major work packages. Source and original evidence through AP095 were committed
and pushed as `ee3ff29a1` on `release/jordan-v35-20260908` in
`nasqret/vietnam2026`. The older v5 evidence index remains the immutable
33-statement release. See the separate publication and Alpha-readiness status
below; a research publication is not a library admission.

### October 11 publication and Alpha-readiness

The additive [245-statement checkpoint](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/sqrt2-power/checkpoints/2026-10-11/)
is deployed, with source and publication tooling pushed as `6f5e630f5`.
It preserves the Quadratic
Reciprocity layout, exact named/expanded statement equality, and a conservative
77-definition DAG. Its 322-node map contains 1,163 **notation-use** links, not
invented proof-dependency edges. All 246 observations (the two P08 solvers prove
the same statement) are pinned to their original HA and same-data Lean records.
The publication suites passed **49 tests**; static validation checked **8,277
links**. Activation verified **15,378 registered public files**, preserving
14,060 predecessor files unchanged. All **1,318 delivery files** subsequently
matched their hashes over HTTPS with normal certificate validation. Chrome
confirmed the landing page, AP095's readable named statement, definition
navigation, interactive node selection and the 245-theorem whole-corpus view;
no graph JavaScript errors were logged. The focused map is left open in Chrome.

The first browser/HTTPS pass exposed private permissions on the newly created
`checkpoints` parent and the three switched navigation files. Those four exact
paths were corrected to public directory/file modes (0755/0644); the activation
tool now handles a restrictive SSH umask explicitly. The initial failed HTTPS
receipt is retained alongside the successful rerun. No proof or historical
release bytes changed during that correction. Receipts:
[activation](observations/publication-20261011-activation-v1.json),
[HTTPS](observations/publication-20261011-https-v2.json),
[Chrome](observations/publication-20261011-browser-v1.json).

AP095 also passed a fresh WMI diagnostic of the existing ordinary-certificate
Alpha gate: job **284699**, `COMPLETED 0:0`, 28,316 proof nodes, depth 88,
335,423 annotations, 3.33 wall seconds, and 60 MiB peak RSS. The unchanged HA
kernel accepted the closed certificate and rejected the false target. See the
[readiness receipt](observations/alpha-readiness-ap095-wmi-v1/receipt.json).
This is **not Alpha enrollment**. Alpha remains v35 (4,318 entries), Stable
remains 432, and IR072 remains open. The outstanding promotion work is a
versioned native-bundle source/enrollment adapter, exact novelty/dependency
inventory, fresh release audit, catalogue/runtime integration and release
validation. Saved research receipts do not substitute for those gates.
The browser check also noted a minor inherited spacing issue in the selected
definition panel's long "Theorems/definitions using it" label; node selection,
counts and links work. This is a presentation follow-up, not proof evidence.

The newest accepted statement, **AP095**, turns AP094's 18/d comparison into
the requested error at most 2^-n for the unchanged n+8 approximation program.
It constructs the actual dyadic powers and reuses AP015's checked cancellation
proof, preserving both independent positive heads and the original degree.
Full HA replay, fresh same-data Lean verification and all scheduled regressions
passed in one WMI job. The campaign records **1,619 distinct focused proof regressions**;
rerunning older tests and checking infrastructure do not increase that total.
See the [AP095 checkpoint](#ap095-accepted-evidence-audited-2026-10-11) below.

The eight statements CV094-CV101 now have complete original HA replay,
[fresh Lean verification](observations/shared-wave-exp-continuity-chain-lean-v3/report.json)
and all 59 focused proof regressions. They connect finite exponential term
differences, weighted sums, independent denominator/head rescaling and uniform
finite truncation. The strongest natural bound keeps both errors explicit:
after positive normalization its reading is `9*g/(d*e)+2/2^m`. It does not
assert analytic convergence or irrationality.

CV102 now gives that same two-error bound as an actual valid-rational theorem,
proving the cutoff power and every denominator nonzero. Its independent fresh
Lean check and seven proof regressions also pass; it has no new definition,
induction, analytic axiom or closed IR parent.

SQ001 reuses the exact Bertrand floor-root proof dependencies and proves
unconditional existence and uniqueness. Its original `FloorSqrt` definition
and Le/Lt dependencies are preserved. HA, fresh Lean and eight regressions
pass; this is audited reuse, not a newly discovered number-theoretic result.
SQ002 converts square bounds to floor-root bounds, and SQ003 constructs the
unique positive floor root of `2*d*d` with `d<=s<2*d` for every `d!=0`.
Both now pass HA, independent fresh Lean and seven regressions each.
SQ004 constructs the unique positive dyadic computation at every precision,
using local computation-only definition ND0446. SQ005 proves the exact
positive-integer rescaling bracket. Both pass HA, fresh Lean and seven tests;
the definition DAG retains all old power/floor-root dependencies.
SQ006 preserves both supplied dyadic computations at precisions k and k+l,
constructs the intervening actual power, and proves the denominator product
and integer refinement bounds. HA, fresh Lean and seven regressions pass.
SQ007 now proves actual valid-rational nested intervals: lower endpoints are
nondecreasing and upper endpoints nonincreasing. All denominator guards are
proved; HA, fresh Lean and seven regressions pass.
SQ008 extracts the finite dyadic modulus in exact natural arithmetic:
`s*q<=t*d<=s*q+q`, with both denominators proved nonzero. Its rational reading
is `0<=t/q-s/d<=2^-k`; HA, fresh Lean and seven regressions pass.
SQ009 supplies the square error `0<=2-(s/d)^2<=4/d` and the actual positive
root range. SQ010 supplies the reciprocal error `0<=d/s-q/t<=2^-k`, proving
every used denominator nonzero. Both pass HA, fresh Lean and seven proof tests
each. These are finite estimates, not assumed real square-root identities.
AP001 constructs the actual finite logarithm/root quotient and proves its
denominator positive and value at most one. AP002 constructs the same input's
degree-k+2 finite exponential sample, positive normalization, recurrence and
all-index factorial/power identities. Both pass HA, fresh Lean and eight proof
tests each. Their local definitions ND0447/ND0448 contain computations only;
neither is claimed to be a completed, certified CApprox sequence.
AP003 proves that independent supplied logarithm/root graphs at the same
precision give the same rational quotient when both coefficient scales are
positive. It preserves the separate codes and scales, proves denominator
validity, and passes HA, fresh Lean and seven proof tests.
AP004 derives positive denominators, the input range, recurrence and all-index
normalization for every supplied sample graph under D!=0. HA, fresh Lean and
seven proof tests pass; these properties have not been added to the definition.
AP005 proves the final finite rational output independent of the positive
scaling and code choices, with both heads proved nonzero. HA, fresh Lean and
seven proof tests pass. This is value independence, not yet an accuracy theorem.
AP006 proves two-sided finite error bounds for independently supplied quotient
inputs at precisions k and k+l: the possible increase is at most 3/p and decrease
at most 1/d. Actual powers and encodings are preserved, not assumed monotone.
HA, fresh Lean and eight proof tests pass; analytic convergence remains open.
AP007 propagates two-sided scaled input errors through same-degree finite
exponential sums with independent denominators and normalization heads.
Constructive natural order handles both input directions; the common error
multiplier is never cancelled. HA, fresh Lean and eight proof tests pass.
AP008 extends those two-sided bounds to unequal finite horizons by constructing
the shorter sum of the actual longer table and adding its checked tail error.
It preserves the cutoff power and both encodings. HA, fresh Lean and eight
proof tests pass; this is still a finite statement, not analytic identification.
AP009 applies those bridges to complete actual samples at k and k+S l and
removes arbitrary coefficient scales by proved positive-factor cancellation.
The errors are at most 27/p+2/r in one direction and 9/d in the other, with
all displayed denominators nonzero. HA, fresh Lean and eight proof tests pass.
AP010 supplies general joint base/exponent monotonicity for actual powers,
allowing zero smaller base and zero exponents but requiring the larger base
nonzero. HA, fresh Lean and seven proof tests pass, with one explicit induction.
AP011 specializes that result to the actual approximation powers and proves
all three positive, with d<=p and d<=r. HA, fresh Lean and seven proof tests
pass without a new induction or definition.
AP012 proves a uniform two-sided bound of 29/2^k for actual samples at strictly
finer precision. It constructs the auxiliary cutoff internally, preserves both
supplied graphs and proves positive output denominators. HA, fresh Lean and
eight proof tests pass; the intended real and irrationality are not yet identified.
AP013 extends that bound to every precision increment, including zero, using
exact value independence for the equal-precision case. HA, fresh Lean and
seven proof tests pass. This proves a finite uniform error property, not yet
the canonical approximation algorithm or its identification with the real constant.
AP014 proves the actual fixed shift power 2^8 positive and at least 29, by
constructing 2^5 and checking arithmetic no larger than 32. HA, fresh Lean and
nine proof tests pass after one proof-constructor repair; the rejected first
attempt is preserved. Neither the numeral limit nor any kernel rule changed.
AP015 now proves finite two-sided error at most 2^-n between samples at n+8
and any finer precision. It constructs both powers, factors the actual coarse
denominator and cancels only the proved positive shift power. HA, fresh Lean
and eight proof tests pass. This is a finite Cauchy bound, not yet analytic
identification or a full irrationality proof.
AP016 constructs the actual odd-index slice of the encoded logarithm
coefficient table and proves every odd reciprocal equation and even zero,
including the final even entry. HA, fresh Lean and seven proof tests pass.
The reused six-definition DAG contains no assumed logarithm or accuracy law.
AP017 proves the generic paired-Horner identity on supplied histories:
when every even coefficient through 2*k is zero, the original value at base
t is t times the odd-slice value at base t*t. HA, fresh Lean and seven proof
tests pass, with one explicit induction and no new definitions or axioms.
AP018 supplies the matching exact power normalization: t^(2*k+1) equals
t times (t*t)^k for the actual supplied power computations. HA, fresh Lean
and seven proof regressions pass, including zero base and zero exponent.
Five unchanged definitions and one explicit induction suffice; no
cancellation or positivity assumption is used.
AP019 now constructs the actual odd slice's base-nine value and power and
proves the valid rational identity 3*x/(D*p)=3*y/(D*q), preserving the
supplied base-three prefix, value and power. All denominator-positivity
obligations are proved. HA, fresh Lean and seven proof regressions pass;
fourteen unchanged definitions and no new induction are used.
AP020 identifies that finite logarithm quotient with its actual odd-reciprocal
sum. It constructs a term table with sum y and proves every normalized entry
3*T[j]/(D*q) equals 2/((2*j+1)*3^(2*j+1)), including actual positive power
witnesses. HA, fresh Lean and seven proof regressions pass; 17 unchanged
definitions suffice. This is not yet an infinite logarithm identity.
AP021 identifies every actual exponential-sample term with U^j/(j!*V^j),
retaining the caller's term table, head and sum. Every factorial and both
powers are constructed and all denominators proved nonzero. HA, fresh Lean
and seven proof tests pass; 25 unchanged definitions and no new induction
are used. This remains a finite-series interpretation, not an analytic limit.
AP022 fixes the logarithm coefficient scale to the actual factorial N! and
constructs the coefficient table at that scale. HA, fresh Lean and seven
proof tests pass, with one positive-divisor induction and ten unchanged
definitions. This fixes the numerical scale, not the beta-code representation
or the complete primitive-recursive approximation trace.

The earlier [first](observations/shared-wave-exp-term-difference-lean-v1/report.json)
and [second](observations/shared-wave-exp-term-and-sum-lean-v2/report.json)
Lean build timeouts and interrupted regression diagnostics are retained as
history, not successful evidence. After unchanged replay timings returned to
normal, all nine fresh checker modules and eight certificates passed in 19.01
seconds with both negative controls. No checker, kernel or resource guard was
weakened. The validator now preserves earlier validated process records in an
explicit failed/incomplete report if supervision fails; its four adversarial
reporting tests pass. This changes reporting, not proof acceptance.

| Exact statement | Scope | Bundle nodes / ordinary constructors |
| --- | --- | --- |
| QF002 | For every finite factor sequence, construct eight codes for an actual quadratic product trace; no nonzero-factor premise | 108 / 5,271 |
| QF003 | From nonzero factors, construct both an actual finite product trace and a decoded nonzero terminal tuple | 272 / 84,522 |
| QH001 | Canonical quadratic multiplication satisfies the natural coefficient-height bound, with an explicit gap witness | 13 / 1,344 |
| QF004 | For every finite factor sequence, construct an actual trace whose outputs satisfy the canonical component equations | 108 / 5,268 |
| QH002 | Every decoded endpoint of a canonical length-L trace has height at most H^L when all decoded factors have height at most H; relational power and trace are explicit premises | 41 / 2,836 |
| QF005 | From bounded nonzero factors, construct the power value, canonical trace and nonzero terminal tuple, together with the endpoint height bound; none of those output witnesses is a premise | 297 / 86,942 |
| CV002 | Every finite natural table satisfying the denominator-cleared log-exp recurrence has coefficient D at zero and 2D at every positive index in its domain | 31 / 1,359 |
| CV003 | Construct a finite natural convolution of arbitrary input tables at every requested output length, and prove coefficientwise uniqueness across all output encodings | 126 / 6,282 |
| CV004 | Construct the actual truncated natural coefficient tables for every power from zero through an arbitrary exponent | 121 / 5,826 |
| CV005 | When the input vanishes below degree one, construct those power tables and prove every padded coefficient below its row's exponent is zero | 131 / 6,620 |
| CV006 | From a pointwise weighted relation between three actual prefixes, construct all three finite sums and prove the same weighted relation for their totals, including zero weights and empty sums | 109 / 5,286 |
| CV007 | Construct both coefficientwise Euler tables and three actual natural convolution coefficients, and prove `i*(A*B)[i]=(EA*B)[i]+(A*EB)[i]` for arbitrary input lengths and coefficient index | 123 / 6,413 |
| CV008 | Construct both orders of every finite affine natural double sum and prove they have the same total, including empty dimensions and zero strides | 126 / 6,597 |
| CV009 | Construct the prefix, shifted tail and whole sum at arbitrary split lengths, and prove the whole total is the sum of the two pieces | 120 / 5,872 |
| CV010 | Construct natural convolution coefficients in both input orders and prove they have a common value at every index, with arbitrary input lengths and zero padding | 133 / 6,944 |
| CV011 | Transport an actual length-m sum witness to length m+n when the n actual appended entries are all zero; both premises are required | 123 / 6,303 |
| CV012 | Construct the actual `(i+1)`-square triple-product grid, using genuine quotient/remainder coordinates and an explicit zero case outside the triangle | 110 / 5,165 |
| CV013 | Given complementary indices and an actual coded triple-product row, construct its total and the inner convolution coefficient, and prove the total is the outer coefficient times the inner coefficient | 139 / 7,443 |
| CV014 | At every index below a common truncation width, construct both intermediate convolution prefixes and a common coefficient for the two nested products | 168 / 10,172 |
| CV015 | From a weighted relation among three actual prefixes, construct their three convolutions with a common right input and prove the weighted relation for the outputs; zero weights and arbitrary coefficient indices are allowed | 123 / 6,449 |
| CV016 | Construct an actual truncated unit and the padded input coefficient, and prove their convolution has that value below the unit width | 142 / 7,503 |
| CV017 | Construct an Euler input table and all finite power rows, and prove `i*P[k+1][i]=(k+1)*(EA*P[k])[i]` for every available row and every coefficient below the truncation width | 193 / 12,931 |
| CV018 | Construct a weighted prefix `C[i]=alpha*A[i]+beta*B[i]` and prove the corresponding convolution identity, with the pointwise relation as an output rather than a premise | 125 / 6,687 |
| CV019 | Construct every finite weighted accumulation trace: an actual zero initial row and actual successor rows formed by adding the next weighted input row; input rows need not be powers | 110 / 5,326 |
| CV020 | Construct the shifted coefficient table `D(A)[i]=(i+1)*A[i+1]` by an actual Euler table and an actual affine slice, including an empty output prefix | 107 / 4,967 |
| CV021 | Construct the input Euler table, powers, shifted outer weights and both weighted accumulations, and prove the finite composition identity `i*Q[N+1][i]=(EA*R[N])[i]` for i<H | 208 / 14,786 |
| CV022 | Construct the terminal-one weight table `w[j]=((j+1)*d)*w[j+1]` and prove all entries through N are nonzero when d is nonzero; construction also covers d=0 | 108 / 5,284 |
| CV023 | From an actual pointwise weight relation W=d*Z, construct both weighted accumulation traces and prove the same scalar relation for every corresponding row through K; arbitrary source rows and d=0 are allowed | 116 / 6,125 |
| CV024 | For a zero-constant input, construct weights and the actual width-N finite composition and prove `d*(i*C[i])=(EA*C)[i]` for i<N; retain all computation witnesses and conditional weight nonvanishing | 224 / 16,942 |
| CV025 | Construct a positive common denominator and every finite natural prefix with even coefficients zero and odd coefficients satisfying `i*A[i]=2*d`; prove zero constant term with actual beta coding | 108 / 5,026 |
| CV026 | Given that actual coefficient prefix, construct its Euler table and prove the in-range initial values 0,2d and its period-two law | 111 / 5,287 |
| CV027 | For a zero-headed period-two prefix E with E[1]=h, construct actual convolution coefficients and prove `(E*C)[i+2]=(E*C)[i]+h*C[i+1]` within the common width | 137 / 7,195 |
| CV028 | Construct the positive-denominator inner table, weights, powers, accumulation and terminal row, and prove its three-term coefficient recurrence without assuming it | 245 / 18,901 |
| CV029 | At every width N>=2, construct that full computation and nonzero initial weight z; prove C[0]=z and C[i]=2z for every positive i<N, including actual initial values and recurrence witnesses | 252 / 20,299 |
| CV030 | Construct terminal-one weights and actual factorial/power witnesses; prove w[0]=N!*d^N and (w[j]*j!)*d^j=w[0] for every j<=N, including d=0; positivity keeps its nonzero-d premise | 130 / 6,558 |
| CV031 | Preserve all CV029 composition witnesses and prove factorial normalization for that same weight table and nonzero z, using the supplied-table invariant rather than constructing unrelated weights | 272 / 21,575 |
| CV032 | Construct an integer Horner trace for every natural coefficient prefix, multiplier and length; prove value uniqueness at every index through its endpoint, including empty prefixes and zero multipliers | 107 / 5,084 |
| CV033 | From the explicit coefficient pattern z,2z,..., construct its length-k+1 Horner trace at 3, a nonzero actual p=3^k, and endpoint r with r+z=(2z)*p | 126 / 6,175 |
| CV034 | Construct the entire normalized composition at N=K+2 and evaluate the same coefficient table by Horner: p=3^(K+1), r+z=(2z)*p, z*p nonzero; the coefficient pattern is proved, not assumed | 284 / 22,574 |
| CV035 | From an actual pointwise weighted coefficient relation, construct three Horner traces and endpoint values and prove the same relation for their evaluations, with all-row transport and zero cases | 111 / 5,615 |
| CV036 | From an actual zero tail on [M,M+N), construct a Horner trace, both endpoints and p=t^N; prove the longer numerator is p times the shorter numerator, including zero multiplier and empty lengths | 122 / 6,061 |
| CV037 | Given terminal-one geometric weights and the actual coefficient-times-weight prefix, construct a Horner endpoint r and prove that the supplied weighted prefix has actual finite sum r | 115 / 5,728 |
| CV038 | Construct geometric weights and an actual p=t^N, identify the initial weight with p, and prove W[j]*q=p for every actual Pow(t,j,q) at j<=N, including t=0 | 123 / 6,042 |
| CV039 | For arbitrary A,t,N construct the geometric weights, power, pointwise product prefix, Horner trace and common endpoint/sum value; no weight or product-table premise remains | 137 / 7,321 |
| CV040 | Preserve that construction and prove W[j]=q for j+e=N and actual Pow(t,e,q), and Q[j]=a*q for (j+1)+e=N, A[j]=a; zero multiplier remains allowed | 142 / 7,593 |
| CV041 | Construct weights at L, M and L+M and prove W[L+M][i+j+1]=t*(W[L][i+1]*W[M][j+1]) for in-range pairs, replaying actual archived power addition | 135 / 7,022 |
| CV042 | Given three geometric tables and two weighted prefixes, construct both convolution coefficients u,v and output weight w, and prove u*w=t*v for every index, including zero-padding cases | 148 / 8,193 |
| CV043 | Given actual leading zeros, a shifted block scaled by a, and trailing zeros, construct both finite sums and prove the longer sum is a times the source sum; all lengths and zero scalar allowed | 125 / 6,488 |
| CV044 | Construct a square Cauchy grid of side N+1 with actual antidiagonal products when j<=k and explicit zero cells when k<j; no sum law is in its definitions | 110 / 5,103 |
| CV045 | Construct that grid and every affine row sum, proving each row sum is the corresponding actual convolution coefficient by extending the diagonal with proved zeros | 136 / 7,126 |
| CV046 | Given an actual Cauchy column and padded left value a, and the explicit complete-span equality (j+M)+q=T, construct both sums and prove the column total is a times the right-input sum | 133 / 7,204 |
| CV047 | Construct N=L+M, one grid of side N+1, one shared right-input sum, and all length-N row and column sums; columns outside left support are proved zero without a false complete-span assumption | 149 / 8,381 |
| CV048 | Construct the full length-L+M convolution, both input sums and its output sum, and prove output sum = product of input sums using actual finite Fubini, including empty inputs | 162 / 9,597 |
| CV049 | Construct the full convolution and all three actual Horner traces; prove H(A*B)=t*(H(A)*H(B)) at length L+M, retaining the extra multiplier and the zero/empty cases | 218 / 14,338 |
| CV050 | From two local padded-input transport premises and i<H, construct a common actual convolution coefficient across arbitrary input lengths and encodings, preserving the same diagonal/sum witnesses | 117 / 5,495 |
| CV051 | Given H<=J, construct power traces at both widths and prove every row through K preserves the actual coefficient at each i<H, including zero width and exponent | 141 / 7,483 |
| CV052 | Construct both power traces and both weighted accumulation traces using the same input and outer weights; prove all power and accumulation rows preserve coefficients below H | 151 / 8,802 |
| CV053 | From separate upper-support bounds r,s on actual padded inputs, construct a convolution prefix of any length and prove it vanishes from r+s | 127 / 6,250 |
| CV054 | Construct all power rows through K and prove every actual row k vanishes from 1+kL; the unit at exponent zero and empty inputs are retained | 141 / 7,124 |
| CV055 | Transport one actual Horner history to a shorter prefix with coefficientwise equal values, without asserting equality of different-length endpoints | 109 / 5,185 |
| CV056 | With r+s<=N and N+q=L+M, construct the support-complete product and actual Horner endpoints; prove p*z=t*(x*y) for actual p=t^q, retaining both scaling factors | 229 / 15,213 |
| CV057 | Prove the same support-complete multiplication law for supplied convolution codes, supplied Horner endpoints and a supplied actual scaling power, using extensional value transport | 233 / 15,726 |
| CV058 | Under 1+K*L<=J+1, construct the power trace and input evaluation; prove every row k through K satisfies (p^k)*y=(t^J*t^k)*x^k for actual p=t^L, retaining the unit and zero cases | 253 / 17,619 |
| CV059 | Construct a coded table of actual Horner values for arbitrary encoded rows, and prove that every supplied actual evaluation has the same decoded value; no power-trace premise | 115 / 5,475 |
| CV060 | Construct the actual weighted accumulation, row values, pointwise weighted products and their sum; prove every terminal row evaluates to that same sum, including zero/empty cases | 137 / 7,812 |
| CV061 | Use the same whole-support power trace in the weighted accumulation and row-value table; retain all constructed data and prove the exact denominator-cleared monomial law for every table entry | 276 / 20,043 |
| CV062 | Construct a genuine shifted tail, prefix/tail/whole Horner values and p=t^N; prove the exact splitting z=p*x+y for arbitrary split lengths, including zero multiplier and empty pieces | 124 / 6,368 |
| CV063 | For a<=b construct length-r+1 Horner values x at b and y at a and actual p=a^r,q=b^r; prove p<=q and p*x<=q*y, retaining zero bases and the exact exponent r | 125 / 6,591 |
| CV064 | Construct a tail of length r+1 after N, its value u at b, the whole value v at a and actual p=a^r,q=b^r; prove p*u<=q*v under a<=b, without claiming rational division transport | 132 / 7,376 |
| CV065 | From a zero head and separate coefficient bound D, construct the base-two length-k+1 Horner value y and actual p=2^k with y+D<=D*p, including D=0 | 125 / 6,170 |
| CV066 | Construct one actual atanh coefficient table, nonzero d, zero head, coefficient bounds, Horner value y and p=2^k; prove y+2d<=(2d)*p for that same table | 136 / 6,748 |
| CV067 | Construct actual f=(k+2)! and p=3^k with 2*p<=f; retain an arbitrary-supplied-values helper and the exact offset | 125 / 5,832 |
| CV068 | From separate adjacent-entry bounds (r+1)*a[i+1]<=r*a[i] and the actual head a0, construct the finite sum s with s<=(r+1)*a0, including empty prefixes and r=0 | 112 / 5,303 |
| CV069 | For arbitrary supplied weights and base x, construct the actual prefix T[j]=W[j]*x^j and its actual sum; all power values use the existing graph, including zero base and empty prefix | 121 / 5,849 |
| CV070 | Construct one actual factorial-weight/term pair, nonzero initial weight, exact adjacent exponential recurrence, all-index factorial normalization and the same prefix sum under d!=0 | 144 / 7,955 |
| CV071 | Retain every CV070 witness and normalization, and prove the same finite sum is at most nine times its initial weight under d!=0 and x<=2d | 163 / 9,817 |
| CV072 | From CV061's supplied monomial law and p!=0, prove the actual row-value head and adjacent recurrence p*next=(t*x)*previous | 119 / 5,937 |
| CV073 | For the same factorial weights, row values and products, prove the initial product w0*v and scaled exponential recurrence with denominator d*p and numerator t*x | 122 / 6,373 |
| CV074 | Construct the actual atanh table, factorial weights and full-support composition at base two; retain all traces/normalizations and prove s<=9*(w0*v), with v=2^J and nonzero w0*v | 325 / 25,678 |
| CV075 | From an actual whole-table majorant and nonzero denominator, construct the actual tail at one third and certify its valid rational bound B*(2/3)^M | 144 / 8,777 |
| CV076 | Retain every CV074 field, decode its terminal row and construct every in-range tail with valid rational bound 9*(2/3)^M | 336 / 28,904 |
| CV077 | Preserve supplied atanh and weight codes and their nonzero head while constructing the full composition, finite majorant and every in-range rational tail bound | 317 / 26,443 |
| CV078 | Transport all weighted accumulation rows through K from source agreement only for consumed rows k<K; the unused source row K may differ | 30 / 1,602 |
| CV079 | Explicitly restrict an N+1-deep large power trace and transport all N+1 weighted terms against an N-deep small trace with the same input and weights | 55 / 3,467 |
| CV080 | Construct one full composition with the actual factorial weights, prove its low coefficient pattern and exact geometric-prefix value, and retain its rational omitted-tail bounds | 426 / 39,864 |
| CV081 | Evaluate supplied whole-support power and accumulation tables at any base, constructing only evaluation data and proving the same terminal sum and monomial law | 263 / 18,894 |
| CV082 | Prove the exact scaled prefix-plus-tail identity for supplied slices and values, using value uniqueness across independent Horner histories | 38 / 2,024 |
| CV083 | Derive an exact balance and two denominator-cleared bounds from the finite geometric prefix, supplied split, scale identity and tail bound | 14 / 997 |
| CV084 | Align actual base-three prefix/tail powers and supplied values, then prove valid rational upper and lower error comparisons with every denominator nonzero | 134 / 7,897 |
| CV085 | Construct one normalized finite composition and its actual weighted sum, monomial interpretation and both valid rational errors, without coefficient-pattern or tail-bound premises | 435 / 42,054 |
| CV086 | For the supplied atanh table, base-three value y and p=3^(k+1), prove 3*y+3*d<=d*p using a zero-head bounded-prefix invariant | 46 / 2,038 |
| CV087 | Construct the actual finite exponential tail from m+1, its adjacent ratio bound and sum s; prove s<=2*first when d is nonzero and x<=d | 121 / 5,970 |
| CV088 | Construct p=2^m, the first omitted term and actual tail; prove p*first<=head and p*sum<=2*head uniformly in the extra finite horizon | 136 / 7,001 |
| CV089 | For any supplied 2D-bounded coefficient prefix, actual base-three value y and p=3^N, prove y+D<=D*p without a zero-head assumption, including empty prefixes | 40 / 1,774 |
| CV090 | Construct the actual supplied atanh table's prefix, tail and whole values and powers; prove exact scaled splitting and both natural cross-multiplied truncation bounds | 142 / 7,798 |
| CV091 | Retain the actual prefix and whole values and prove all rational denominators nonzero; certify prefix<=whole<=prefix+3/3^M, including empty parts | 146 / 8,619 |
| CV092 | For independently supplied atanh tables with scales d,e and supplied Horner values x,y at the same length/base, prove e*x=d*y, including zero scales/base and empty prefixes | 37 / 2,025 |
| CV093 | Preserve two independently supplied atanh tables, values and powers; prove valid rational monotonicity and truncation error <=3/3^M across their distinct nonzero common denominators | 155 / 9,793 |
| CV094 | Prove all-index monotonicity and denominator-cleared finite differences for two actual exponential recurrences with a common head | 40 / 2,377 |
| CV095 | Transport a separately defined pointwise weighted order to three actual finite sums, including zero weights and empty prefixes | 26 / 1,279 |
| CV096 | Derive the finite exponential sum bound s<=t and d*t<=d*s+9*g*a0 from actual tails and their supplied shared-head sums | 147 / 9,501 |
| CV097 | Construct rescaled exponential terms, their exact recurrence at denominator d*f and numerator f*x, and the scaled sum t=c*s | 114 / 5,945 |
| CV098 | Compare actual sums across independent nonzero denominators and arbitrary initial scales by constructing both common-scale computations | 156 / 10,698 |
| CV099 | Prove valid rational finite-sum monotonicity and continuity error 9*g/(d*e), explicitly excluding zero normalizing heads | 159 / 11,137 |
| CV100 | Preserve supplied exponential prefix and whole sums and the actual power p=2^m; prove uniform truncation bounds s<=t and p*t<=p*s+2*a0 | 155 / 8,327 |
| CV101 | Construct the middle prefix and combine independent-argument and finite-horizon errors into the exact natural counterpart of 9*g/(d*e)+2/p | 189 / 13,723 |
| CV102 | Prove every denominator nonzero and turn the two-error inequalities into actual valid-rational comparisons for independent finite exponential computations | 193 / 14,188 |
| SQ001 | Reuse the actual Bertrand floor-root ancestors to prove existence and uniqueness for every natural input, including zero | 31 / 990 |
| SQ002 | From a supplied actual floor root and lower/strict-upper square bounds, prove the corresponding lower/strict-upper root bounds | 16 / 541 |
| SQ003 | For every positive scale d, construct the unique floor root of 2*d*d and prove d<=s<2*d and s!=0 | 42 / 1,426 |
| SQ004 | Construct the unique dyadic power/root pair for every precision; positivity and bounds are conclusions, not clauses of ND0446 | 139 / 6,614 |
| SQ005 | Supplied floor roots at n and n*e*e obey s*e<=t<(s+1)*e for e!=0, including zero input/root | 24 / 913 |
| SQ006 | Preserve supplied dyadic computations at k and k+l; construct e=2^l, prove q=d*e and s*e<=t<(s+1)*e | 131 / 6,594 |
| SQ007 | Convert actual refinement into valid-rational nested intervals, proving all power denominators nonzero | 134 / 6,824 |
| SQ008 | Prove positive denominators and the exact cross-multiplied finite dyadic error s*q<=t*d<=s*q+q | 136 / 6,947 |
| SQ009 | Prove every supplied dyadic root positive, its range, and the square residual s*s<=2*d*d<=s*s+4*d | 53 / 2,160 |
| SQ010 | Prove positive reciprocal denominators, reversed order and finite reciprocal error at most 2^-k | 149 / 7,782 |
| AP001 | Construct the actual odd-reciprocal table, Horner value, power and dyadic root; prove the quotient denominator positive and its value at most one | 161 / 8,262 |
| AP002 | Construct the actual finite exponential output with positive head, exact factorial/power witnesses, same-term recurrence and all-index normalization | 186 / 10,686 |
| AP003 | Preserve independent positive coefficient scales and table codes; prove identical dyadic data/powers and exact rational quotient-value independence | 156 / 8,603 |
| AP004 | Derive positive input/output denominators, range, recurrence and normalization for every supplied complete sample with positive scale D | 152 / 7,916 |
| AP005 | Preserve both complete supplied sample graphs and independent scales/heads; prove positive output denominators and exact rational output-value equality | 228 / 16,692 |
| AP006 | Preserve actual quotient computations at k and k+l; prove positive denominators and two-sided finite input errors without assuming monotonicity | 188 / 13,317 |
| AP007 | Preserve supplied same-degree exponential recurrences and sums; propagate two-sided errors with an arbitrary common multiplier, including zero | 164 / 11,662 |
| AP008 | Preserve actual unequal-horizon sums and cutoff power; combine two-sided input errors with the longer table's finite tail | 197 / 14,850 |
| AP009 | Preserve complete actual samples at strictly finer precision; prove positive denominators and scale-free two-sided errors 27/p+2/r and 9/d | 273 / 26,093 |
| AP010 | Compare supplied powers under ordered bases and an additive exponent increase, with positive larger base and zero smaller base allowed | 126 / 6,042 |
| AP011 | Preserve d=2^k, p=3^(2*k+1), r=2^(k+2); prove positive denominators and domination d<=p, d<=r | 128 / 6,144 |
| AP012 | Construct the auxiliary cutoff internally and prove uniform two-sided finite sample error 29/2^k at strictly finer precision | 282 / 27,341 |
| AP013 | Join equal-precision value independence and strict-precision bounds to prove uniform finite sample error for all increments, including zero | 297 / 29,263 |
| AP014 | Prove the actual supplied 2^8 positive and at least (9*3)+2 using an actual fifth power and ordinary small-arithmetic proofs | 130 / 7,170 |
| AP015 | Construct the actual positive 2^n and prove two-sided finite sample error at most 2^-n after the fixed eight-bit precision shift, for every finer increment including zero | 303 / 30,878 |
| AP016 | Construct the actual odd-index coefficient slice; prove (2*j+1)*B[j]=2*d for j<k and A[2*j]=0 for j<=k, including zero scale and empty slice | 113 / 5,016 |
| AP017 | Compare both actual Horner histories and prove Horner(A,t,2*k+1)=t*Horner(odd_slice,t*t,k), including zero base and empty odd slice | 40 / 1,598 |
| AP018 | Match two actual base-t successor steps with one squared-base step and normalize the odd power without cancellation | 27 / 1,209 |
| AP019 | Construct the actual base-nine odd value and power and identify the finite logarithm quotient as a valid rational | 142 / 7,152 |
| AP020 | Construct the actual finite sum and identify every normalized entry with the intended odd reciprocal, retaining the original log computation | 169 / 9,774 |
| AP021 | Identify every actual exponential sample term with its factorial-series value, constructing the factorial and both powers | 160 / 8,400 |
| AP022 | Prove every required positive divisor divides the actual factorial and construct the coefficient prefix at prescribed scale N! | 124 / 5,880 |
| AP023 | Construct the full log/root/exponential sample at scale (2*k+1)!, retaining positive D and every computation/normalization field | 190 / 10,891 |
| AP024 | Constructively decide equality, order, beta decoding, powers, factorials, sums and integer floor roots, from replayed totality and uniqueness | 153 / 7,160 |
| AP025 | Decide actual logarithm coefficients, Horner values and dyadic square-root records, including invalid supplied candidates | 146 / 6,803 |
| AP026 | Compile and replay constructive decisions of every row and bounded prefix of the supplied coefficient, weight and term tables | 133 / 6,360 |
| AP027 | Decide the full supplied sample, prescribed factorial scale and positive scale/output denominator by checking every actual computation field | 174 / 8,788 |
| AP028 | Construct a genuine fifteen-field beta record of the positive fixed-factorial sample at n+8, with both code components explicit | 206 / 14,914 |
| AP029 | Decide any supplied record by beta decoding and uniqueness transport of all thirteen internal witnesses, with both output slots checked | 178 / 9,739 |
| AP030 | Prove valid denominators and rational output equality for two genuine records at the same precision, without equating their code numbers | 229 / 16,810 |
| AP031 | Transport the actual all-finer dyadic error to two complete records, preserving the constructed power and nonzero denominators | 305 / 31,023 |
| AP032 | Construct actual finite log/exponential data whose same term table has its recurrence, positive head, sum and both quantitative errors near two | 439 / 42,538 |
| AP033 | Prove two power inductions and an explicit cutoff N=18*r+2 that makes both finite log/exponential errors at most 1/r | 46 / 2,824 |
| AP034 | Construct r=2^n and actual finite log/exponential computations whose same sum y/h satisfies both integer errors at most 2^-n around two | 452 / 44,672 |
| AP035 | Prove (T[j]*j!)*d^j=h*x^j for any supplied actual exponential recurrence and head, without cancellation and including zero parameters | 36 / 1,812 |
| AP036 | Identify every term of any supplied positive-denominator exponential recurrence with its valid rational factorial-series term | 130 / 6,260 |
| AP037 | Carry a locally specified denominator-cleared one-place shift with zero head through actual finite convolution coefficients | 131 / 6,988 |
| AP038 | Prove the actual finite convolution of two exponential recurrences obeys the added-argument recurrence below their common cutoff | 147 / 8,608 |
| AP039 | Construct the finite exponential convolution prefix and sum, proving its product head, added-argument recurrence and factorial normalization | 163 / 9,894 |
| AP040 | Prove extending the same two natural input prefixes cannot decrease any actual convolution coefficient, including empty lengths | 46 / 2,330 |
| AP041 | Construct the extended-input convolution and place the product of the short input sums between its short and double-length sums | 191 / 11,747 |
| AP042 | Bound the actual degree-n exponential product error by 2/2^n times its product head when x+y<=d, retaining the finite Cauchy table | 243 / 16,475 |
| AP043 | Transport that product error to three actual supplied sums with independent output code and head, using cross-value identity | 278 / 21,182 |
| AP044 | Construct positive factorial-weighted half-argument terms and compare their short sum squared with a supplied whole-argument sum | 303 / 23,493 |
| AP045 | Combine the supplied square error 2/p and reference-to-two error 1/r, for r<=p, by positive natural cancellation | 28 / 1,558 |
| AP046 | Prove actual 2^(18*r+2) is nonzero and at least r, using the generic ordinary-induction inequality n+1<=2^n | 37 / 1,434 |
| AP047 | Construct the actual finite half-log exponential with positive normalization and prove 2-1/2^n <= (u/h)^2 <= 2+3/2^n | 535 / 54,491 |
| AP048 | Convert two supplied square errors to linear errors by decidable natural order and positive scale cancellation | 31 / 1,162 |
| AP049 | Compare supplied half-log and dyadic-root square witnesses with forward allowance 7/r and reverse allowance 1/r | 38 / 3,603 |
| AP050 | Construct both actual witnesses at every precision, preserving every half-log computation and proving their two finite cross-product errors | 560 / 58,554 |
| AP051 | Prove each supplied exponential recurrence step halves beyond twice an arbitrary natural argument bound, including zero argument | 23 / 832 |
| AP052 | Construct the actual shifted table, halving relation, head and finite tail sum beyond that threshold | 123 / 6,057 |
| AP053 | Prove symbolic binary decay at every bounded index of a supplied halving prefix by ordinary HA induction | 36 / 1,526 |
| AP054 | Construct actual powers, heads, slices and finite sums with dyadic tail decay for arbitrary bounded rational arguments | 138 / 7,210 |
| AP055 | Preserve two supplied sums and their actual head/power while proving the large-argument truncation bound, including an empty short prefix | 157 / 8,561 |
| AP056 | Bound every supplied exponential term by its original head times the actual power L^k, including zero arguments and heads | 44 / 1,971 |
| AP057 | Prove the finite truncation error relative to the original head h: p*t<=p*s+2*(L^K*h) | 160 / 9,036 |
| AP058 | Construct the actual factorial-weighted table, nonzero normalization, sums and powers satisfying the original-head truncation bound | 184 / 11,412 |
| AP059 | Construct the finite convolution and prove a normalized product error for arbitrary naturally bounded rational arguments | 248 / 17,215 |
| AP060 | Prove equality of supplied finite exponential values at equal rational arguments, without argument bounds or head positivity | 37 / 2,457 |
| AP061 | Transport the general-argument product error to three independently supplied tables, heads and sums | 255 / 18,591 |
| AP062 | Prove L^K<=2^(L*K) and the symbolic requested-precision budget 2*(2^n*L^K)<=2^(L*K+n+1) | 129 / 6,254 |
| AP063 | At explicit short length K+(L*K+n+1), prove the supplied finite tail is at most 2^-n times the original head | 171 / 9,998 |
| AP064 | At explicit degree K+(L*K+n), prove requested 2^-n product accuracy for three independently supplied finite exponential sums | 266 / 19,599 |
| AP065 | Compare independent equal-argument exponential computations at different horizons with requested dyadic accuracy and no equality of codes or heads | 179 / 11,773 |
| AP066 | Construct one positive factorial-normalized coarse approximation before the universal later horizon, with actual positive fine witnesses and requested error | 202 / 14,267 |
| AP067 | Construct all three positive factorial-normalized tables and the actual input prefixes satisfying the requested finite product error | 289 / 22,331 |
| AP068 | Prove relative finite exponential continuity for unrestricted nonnegative arguments at a common denominator and head | 137 / 8,077 |
| AP069 | Transfer unrestricted relative continuity to independent positive argument denominators, arbitrary heads and actual table codes | 144 / 9,148 |
| AP070 | Turn an explicit supplied sum majorant and symbolic precision budget into absolute finite continuity | 146 / 9,520 |
| AP071 | Prove unrestricted submultiplicativity for three actual finite exponential sums at the same degree | 216 / 15,057 |
| AP072 | Prove the horizon-independent integer-argument bound s<=9^(L+1)*h by ordinary induction with positive constructed factors | 267 / 20,100 |
| AP073 | Transport the uniform bound to every actual nonnegative rational argument x/d<=L by a positive reference computation | 281 / 22,610 |
| AP074 | Prove two-sided absolute finite continuity under a symmetric cross-product error and explicit budget, without assuming the input order | 288 / 23,493 |
| AP075 | Construct the majorant power and prove the explicit dyadic continuity modulus m=9*(L+1)+n+1, uniformly in the common finite horizon | 299 / 24,315 |
| AP076 | Ordered natural power difference with actual powers: b=a+g and b<=M imply b^(k+1)<=a^(k+1)+(k+1)*g*M^k, including zero bases | 36 / 1,709 |
| AP077 | Two-sided natural power difference under a,b<=M and both input gaps bounded by g; actual power values retained | 41 / 1,999 |
| AP078 | Actual powers preserve multiplication: Pow(a,k,u), Pow(b,k,v), Pow(a*b,k,w) imply w=u*v, including exponent zero | 121 / 5,854 |
| AP079 | Two-sided power-error propagation for independently normalized nonnegative rationals, with actual denominator powers proved nonzero | 136 / 6,964 |
| AP080 | Convert rational power errors to requested precision under an explicit budget by constructing and identifying the denominator-product powers | 138 / 7,376 |
| AP081 | Combine explicit input and finite-tail errors for independently normalized exponential computations at different arguments and horizons | 323 / 27,568 |
| AP082 | Refine independently supplied logarithm and exponential tables with explicit error 27/3^M+2/2^m and proved positive argument denominators | 229 / 18,933 |
| AP083 | Prove that the actual auxiliary cutoff M=18*r+2 pays both refinement errors, giving cross-normalized error at most 1/r | 238 / 20,970 |
| AP084 | Choose one dyadic threshold before arbitrary independent later tables and prove their finite exponential-of-logarithm values uniformly near two | 511 / 55,569 |
| AP085 | Align the original logarithm-prefix length 2*k+1 and exponential degree k+2 with the uniform near-two threshold, preserving all actual supplied computations | 513 / 55,732 |
| AP086 | At every index beyond that threshold, construct positive factorial-normalized logarithm/exponential samples and retain every term's exact normalization | 522 / 57,051 |
| AP087 | Compare independent half-logarithm exponential tables through explicit doubled-denominator and scaled-gap transport, without changing their logarithm coefficients | 231 / 19,610 |
| AP088 | Derive the actual cutoff power budgets and reduce the half-logarithm refinement error to 1/r by reusing checked positive cancellation | 240 / 21,647 |
| AP089 | Choose one actual dyadic root before all later independent half-logarithm tables and prove both cross-errors, with upper allowance 7+1=8 | 583 / 65,490 |

QF003 composes the complete actual QF001 and QF002 ancestor bodies, with exact
ordered-dependency remapping. Neither a pre-existing trace nor a terminal
value is an assumption. It is still an integer statement: rational denominator
clearing, real interpretation and the quantitative moment lower bound remain
separate obligations.

For QH001 the coefficient mass is
`H(ap,an,bp,bn)=(ap+an)+2*(bp+bn)`. With the explicit canonical multiplication
components, the checked proof witnesses
`2*((bp+bn)*(dp+dn)) + H(output) = H(left)*H(right)`.
The two new conservative, local definitions are ND0394
`IQuadCanonicalProduct` and ND0395 `IQuadHeight`; neither contains a height
inequality or a nonvanishing claim. They are not definition admissions.
Arbitrary balanced representatives cannot satisfy this bound: multiplying
`(1,0,0,0)` by itself permits the balanced representation `(11,10,7,7)`, whose
mass exceeds one. A hostile regression preserves this distinction.

Exact execution records and independent checks:

- QF002: [HA generation/replay](observations/shared-wave-quadratic-trace-exists-v2/report.json),
  [fresh Lean](observations/shared-wave-quadratic-trace-exists-lean-v2/report.json),
  [eight regressions](observations/shared-wave-quadratic-trace-exists-validation-v1.json).
- QF003: [HA generation/replay](observations/shared-wave-quadratic-product-exists-v1/report.json),
  [fresh Lean](observations/shared-wave-quadratic-product-exists-lean-v1/report.json),
  [seven regressions](observations/shared-wave-quadratic-product-exists-validation-v1.json).
- QH001: [HA generation/replay](observations/shared-wave-quadratic-height-v2/report.json),
  [fresh Lean](observations/shared-wave-quadratic-height-lean-v1/report.json),
  [eight regressions](observations/shared-wave-quadratic-height-validation-v1.json).
- QF004: [HA generation/replay](observations/shared-wave-canonical-quadratic-trace-v1/report.json),
  [fresh Lean](observations/shared-wave-canonical-quadratic-trace-lean-v1/report.json),
  [seven regressions](observations/shared-wave-canonical-quadratic-trace-validation-v1.json).
- QH002: [HA generation/replay](observations/shared-wave-quadratic-trace-height-v1/report.json),
  [fresh Lean](observations/shared-wave-quadratic-trace-height-lean-v1/report.json),
  [seven regressions](observations/shared-wave-quadratic-trace-height-validation-v1.json).
- QF005: [HA generation/replay](observations/shared-wave-bounded-quadratic-product-v1/report.json),
  [fresh Lean](observations/shared-wave-bounded-quadratic-product-lean-v1/report.json),
  [seven regressions](observations/shared-wave-bounded-quadratic-product-validation-v1.json).
- CV002: [HA generation/replay](observations/shared-wave-logexp-recurrence-v2/report.json),
  [fresh Lean](observations/shared-wave-logexp-recurrence-lean-v1/report.json),
  [seven regressions](observations/shared-wave-logexp-recurrence-validation-v1.json).
- CV003: [HA generation/replay](observations/shared-wave-natural-convolution-v1/report.json),
  [fresh Lean](observations/shared-wave-natural-convolution-lean-v1/report.json),
  [seven regressions](observations/shared-wave-natural-convolution-validation-v1.json).
- CV004: [HA generation/replay](observations/shared-wave-series-power-trace-v2/report.json),
  [fresh Lean](observations/shared-wave-series-power-trace-lean-v1/report.json),
  [seven regressions](observations/shared-wave-series-power-trace-validation-v1.json).
- CV005: [HA generation/replay](observations/shared-wave-series-power-vanishing-v1/report.json),
  [fresh Lean](observations/shared-wave-series-power-vanishing-lean-v1/report.json),
  [seven regressions](observations/shared-wave-series-power-vanishing-validation-v1.json).
- CV006: [HA generation/replay](observations/shared-wave-sum-linearity-v1/report.json),
  [fresh Lean](observations/shared-wave-sum-linearity-lean-v1/report.json),
  [seven regressions](observations/shared-wave-sum-linearity-validation-v1.json).
- CV007: [HA generation/replay](observations/shared-wave-euler-product-v1/report.json),
  [fresh Lean](observations/shared-wave-euler-product-lean-v1/report.json),
  [seven regressions](observations/shared-wave-euler-product-validation-v1.json).
- CV008: [HA generation/replay](observations/shared-wave-natural-fubini-v1/report.json),
  [fresh Lean](observations/shared-wave-natural-fubini-lean-v1/report.json),
  [seven regressions](observations/shared-wave-natural-fubini-validation-v1.json).
- CV009: [HA generation/replay](observations/shared-wave-sum-splitting-v1/report.json),
  [fresh Lean](observations/shared-wave-sum-splitting-lean-v1/report.json),
  [seven regressions](observations/shared-wave-sum-splitting-validation-v1.json).
- CV010: [HA generation/replay](observations/shared-wave-convolution-commutative-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-commutative-lean-v1/report.json),
  [seven regressions](observations/shared-wave-convolution-commutative-validation-v1.json).
- CV011: [HA generation/replay](observations/shared-wave-sum-zero-tail-v1/report.json),
  [fresh Lean](observations/shared-wave-sum-zero-tail-lean-v1/report.json),
  [seven regressions](observations/shared-wave-sum-zero-tail-validation-v1.json).
- CV012: [HA generation/replay](observations/shared-wave-triple-grid-v1/report.json),
  [fresh Lean](observations/shared-wave-triple-grid-lean-v1/report.json),
  [seven regressions](observations/shared-wave-triple-grid-validation-v1.json).
- CV013: [HA generation/replay](observations/shared-wave-triple-row-sum-v1/report.json),
  [fresh Lean](observations/shared-wave-triple-row-sum-lean-v1/report.json),
  [seven regressions](observations/shared-wave-triple-row-sum-validation-v1.json).

- CV014: [HA generation/replay](observations/shared-wave-convolution-associative-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-associative-lean-v1/report.json),
  [seven regressions](observations/shared-wave-convolution-associative-validation-v1.json).

- CV015: [HA generation/replay](observations/shared-wave-convolution-linearity-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-linearity-lean-v1/report.json),
  [seven regressions](observations/shared-wave-convolution-linearity-validation-v1.json).
- CV016: [HA generation/replay](observations/shared-wave-convolution-unit-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-unit-lean-v1/report.json),
  [seven regressions](observations/shared-wave-convolution-unit-validation-v1.json).
- CV017: [HA generation/replay](observations/shared-wave-series-power-euler-v1/report.json),
  [fresh Lean](observations/shared-wave-series-power-euler-lean-v1/report.json),
  [seven regressions](observations/shared-wave-series-power-euler-validation-v1.json).

- CV018: [HA generation/replay](observations/shared-wave-series-linear-combination-v1/report.json),
  [fresh Lean](observations/shared-wave-series-linear-combination-lean-v1/report.json),
  [seven regressions](observations/shared-wave-series-linear-combination-validation-v1.json).
- CV019: [HA generation/replay](observations/shared-wave-weighted-series-trace-v1/report.json),
  [fresh Lean](observations/shared-wave-weighted-series-trace-lean-v1/report.json),
  [seven regressions](observations/shared-wave-weighted-series-trace-validation-v1.json).

- CV020: [HA generation/replay](observations/shared-wave-shifted-euler-prefix-v1/report.json),
  [fresh Lean](observations/shared-wave-shifted-euler-prefix-lean-v1/report.json),
  [seven regressions](observations/shared-wave-shifted-euler-prefix-validation-v1.json).

- CV021: [HA generation/replay](observations/shared-wave-finite-composition-euler-v1/report.json),
  [fresh Lean](observations/shared-wave-finite-composition-euler-lean-v1/report.json),
  [seven regressions](observations/shared-wave-finite-composition-euler-validation-v1.json).

- CV022: [HA generation/replay](observations/shared-wave-exponential-weights-v1/report.json),
  [fresh Lean](observations/shared-wave-exponential-weights-lean-v1/report.json),
  [seven regressions](observations/shared-wave-exponential-weights-validation-v1.json).

- CV023: [HA generation/replay](observations/shared-wave-weighted-series-scaling-v1/report.json),
  [fresh Lean](observations/shared-wave-weighted-series-scaling-lean-v1/report.json),
  [seven regressions in the combined transport run](observations/shared-wave-denominator-euler-and-scaling-validation-v1.json).

- CV024: [HA generation/replay](observations/shared-wave-denominator-euler-v1/report.json),
  [fresh Lean](observations/shared-wave-denominator-euler-lean-v1/report.json),
  [seven regressions in the combined transport run](observations/shared-wave-denominator-euler-and-scaling-validation-v1.json).

- CV025: [HA generation/replay](observations/shared-wave-atanh-coefficients-v1/report.json),
  [fresh Lean](observations/shared-wave-atanh-coefficients-lean-v1/report.json),
  [seven regressions](observations/shared-wave-atanh-coefficients-validation-v1.json).

- CV026: [HA generation/replay](observations/shared-wave-atanh-euler-v1/report.json),
  [fresh Lean](observations/shared-wave-atanh-euler-lean-v1/report.json),
  [seven regressions](observations/shared-wave-atanh-euler-validation-v1.json).

- CV027: [HA generation/replay](observations/shared-wave-periodic-convolution-v1/report.json),
  [fresh Lean](observations/shared-wave-periodic-convolution-lean-v1/report.json),
  [seven regressions](observations/shared-wave-periodic-convolution-validation-v1.json).

- CV028: [HA generation/replay](observations/shared-wave-composition-recurrence-v1/report.json),
  [fresh Lean](observations/shared-wave-composition-recurrence-lean-v1/report.json),
  [seven regressions](observations/shared-wave-composition-recurrence-validation-v1.json).

- CV029: [HA generation/replay](observations/shared-wave-composition-coefficients-v1/report.json),
  [fresh Lean](observations/shared-wave-composition-coefficients-lean-v1/report.json),
  [seven regressions](observations/shared-wave-composition-coefficients-validation-v1.json).

- CV030: [HA generation/replay](observations/shared-wave-weight-factorials-v1/report.json),
  [fresh Lean](observations/shared-wave-weight-factorials-lean-v1/report.json),
  [nine regressions](observations/shared-wave-weight-factorials-validation-v1.json).

- CV031: [HA generation/replay](observations/shared-wave-normalized-composition-v1/report.json),
  [fresh Lean](observations/shared-wave-normalized-composition-lean-v1/report.json),
  [seven regressions](observations/shared-wave-normalized-composition-validation-v1.json).

- CV032: [HA generation/replay](observations/shared-wave-horner-trace-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-trace-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-trace-validation-v1.json).

- CV033: [HA generation/replay](observations/shared-wave-geometric-horner-v1/report.json),
  [fresh Lean](observations/shared-wave-geometric-horner-lean-v1/report.json),
  [seven regressions](observations/shared-wave-geometric-horner-validation-v1.json).

- CV034: [HA generation/replay](observations/shared-wave-composition-evaluation-v1/report.json),
  [fresh Lean](observations/shared-wave-composition-evaluation-lean-v1/report.json),
  [seven regressions](observations/shared-wave-composition-evaluation-validation-v1.json).

- CV035: [HA generation/replay](observations/shared-wave-horner-linearity-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-linearity-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-linearity-validation-v1.json).

- CV036: [HA generation/replay](observations/shared-wave-horner-zero-tail-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-zero-tail-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-zero-tail-validation-v1.json).

- CV037: [HA generation/replay](observations/shared-wave-horner-weighted-sum-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-weighted-sum-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-weighted-sum-validation-v1.json).

- CV038: [HA generation/replay](observations/shared-wave-geometric-weights-v1/report.json),
  [fresh Lean](observations/shared-wave-geometric-weights-lean-v1/report.json),
  [seven regressions](observations/shared-wave-geometric-weights-validation-v1.json).

- CV039: [HA generation/replay](observations/shared-wave-constructed-horner-sum-v1/report.json),
  [fresh Lean](observations/shared-wave-constructed-horner-sum-lean-v1/report.json),
  [seven regressions](observations/shared-wave-constructed-horner-sum-validation-v1.json).

- CV040: [HA generation/replay](observations/shared-wave-horner-monomials-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-monomials-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-monomials-validation-v1.json).

- CV041: [HA generation/replay](observations/shared-wave-convolution-weights-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-weights-lean-v1/report.json),
  [seven regressions](observations/shared-wave-convolution-weights-validation-v1.json).

- CV042: [HA generation/replay](observations/shared-wave-weighted-convolution-v1/report.json),
  [fresh Lean](observations/shared-wave-weighted-convolution-lean-v1/report.json),
  [seven regressions](observations/shared-wave-weighted-convolution-validation-v1.json).

- CV043: [HA generation/replay](observations/shared-wave-shifted-scaled-sum-v1/report.json),
  [fresh Lean](observations/shared-wave-shifted-scaled-sum-lean-v1/report.json),
  [seven regressions](observations/shared-wave-shifted-scaled-sum-validation-v1.json).

- CV044: [HA generation/replay](observations/shared-wave-cauchy-grid-v1/report.json),
  [fresh Lean](observations/shared-wave-cauchy-grid-lean-v1/report.json),
  [seven regressions](observations/shared-wave-cauchy-grid-validation-v1.json).

- CV045: [HA generation/replay](observations/shared-wave-cauchy-row-sum-v1/report.json),
  [fresh Lean](observations/shared-wave-cauchy-row-sum-lean-v1/report.json),
  [seven regressions](observations/shared-wave-cauchy-row-sum-validation-v1.json).

- CV046: [HA generation/replay](observations/shared-wave-cauchy-column-sum-v1/report.json),
  [fresh Lean](observations/shared-wave-cauchy-column-sum-lean-v1/report.json),
  [seven regressions](observations/shared-wave-cauchy-column-sum-validation-v1.json).

- CV047: [HA generation/replay](observations/shared-wave-cauchy-grid-sums-v2/report.json),
  [fresh Lean](observations/shared-wave-cauchy-grid-sums-lean-v1/report.json),
  [seven regressions](observations/shared-wave-cauchy-grid-sums-validation-v1.json).

- CV048: [HA generation/replay](observations/shared-wave-convolution-total-v2/report.json),
  [fresh Lean](observations/shared-wave-convolution-total-lean-v2/report.json),
  [eight regressions](observations/shared-wave-convolution-total-validation-v1.json).

- CV049: [HA generation/replay](observations/shared-wave-horner-product-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-product-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-product-validation-v1.json).

- CV050: [HA generation/replay](observations/shared-wave-convolution-locality-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-locality-lean-v1/report.json),
  [seven regressions](observations/shared-wave-convolution-locality-validation-v1.json).

- CV051: [HA generation/replay](observations/shared-wave-power-width-transport-v3/report.json),
  [fresh Lean](observations/shared-wave-power-width-transport-lean-v1/report.json),
  [seven regressions](observations/shared-wave-power-width-transport-validation-v1.json).

- CV052: [HA generation/replay](observations/shared-wave-composition-width-transport-v1/report.json),
  [fresh Lean](observations/shared-wave-composition-width-transport-lean-v1/report.json),
  [seven regressions](observations/shared-wave-composition-width-transport-validation-v1.json).

- CV053: [HA generation/replay](observations/shared-wave-convolution-upper-support-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-upper-support-lean-v1/report.json),
  [seven regressions](observations/shared-wave-convolution-upper-support-validation-v1.json).

- CV054: [HA generation/replay](observations/shared-wave-power-upper-support-v1/report.json),
  [fresh Lean](observations/shared-wave-power-upper-support-lean-v1/report.json),
  [seven regressions](observations/shared-wave-power-upper-support-validation-v1.json).

- CV055: [HA generation/replay](observations/shared-wave-horner-prefix-transport-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-prefix-transport-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-prefix-transport-validation-v1.json).

- CV056: [HA generation/replay](observations/shared-wave-supported-horner-product-v1/report.json),
  [fresh Lean](observations/shared-wave-supported-horner-product-lean-v1/report.json),
  [seven regressions](observations/shared-wave-supported-horner-product-validation-v1.json).

- CV057: [HA generation/replay](observations/shared-wave-supported-horner-values-v1/report.json),
  [fresh Lean](observations/shared-wave-supported-horner-values-lean-v2/report.json),
  [seven regressions](observations/shared-wave-supported-horner-values-validation-v1.json).

- CV058: [HA generation/replay](observations/shared-wave-finite-power-evaluation-v2/report.json),
  [fresh Lean](observations/shared-wave-finite-power-evaluation-lean-v1/report.json),
  [seven regressions](observations/shared-wave-finite-power-evaluation-validation-v1.json).

- CV059: [HA generation/replay](observations/shared-wave-row-horner-values-v1/report.json),
  [fresh Lean](observations/shared-wave-row-horner-values-lean-v1/report.json),
  [seven regressions](observations/shared-wave-row-horner-values-validation-v1.json).

- CV060: [HA generation/replay](observations/shared-wave-weighted-accumulation-evaluation-v1/report.json),
  [fresh Lean](observations/shared-wave-weighted-accumulation-evaluation-lean-v1/report.json),
  [seven regressions](observations/shared-wave-weighted-accumulation-evaluation-validation-v1.json).

- CV061: [HA generation/replay](observations/shared-wave-full-composition-evaluation-v1/report.json),
  [fresh Lean](observations/shared-wave-full-composition-evaluation-lean-v1/report.json),
  [seven regressions](observations/shared-wave-full-composition-evaluation-validation-v1.json).

- CV062: [HA generation/replay](observations/shared-wave-horner-splitting-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-splitting-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-splitting-validation-v1.json).

- CV063: [HA generation/replay](observations/shared-wave-horner-base-comparison-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-base-comparison-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-base-comparison-validation-v1.json).

- CV064: [HA generation/replay](observations/shared-wave-horner-tail-majorant-v1/report.json),
  [fresh Lean](observations/shared-wave-horner-tail-majorant-lean-v1/report.json),
  [seven regressions](observations/shared-wave-horner-tail-majorant-validation-v1.json).

- CV065: [HA generation/replay](observations/shared-wave-bounded-horner-v1/report.json),
  [fresh Lean](observations/shared-wave-bounded-horner-lean-v1/report.json),
  [seven regressions](observations/shared-wave-bounded-horner-validation-v1.json).

- CV066: [HA generation/replay](observations/shared-wave-atanh-majorant-v1/report.json),
  [fresh Lean](observations/shared-wave-atanh-majorant-lean-v1/report.json),
  [seven regressions](observations/shared-wave-atanh-majorant-validation-v1.json).

- CV067: [HA generation/replay](observations/shared-wave-factorial-majorant-v1/report.json),
  [fresh Lean](observations/shared-wave-factorial-majorant-lean-v1/report.json),
  [seven regressions](observations/shared-wave-factorial-majorant-validation-v1.json).

- CV068: [HA generation/replay](observations/shared-wave-ratio-sum-bound-v1/report.json),
  [fresh Lean](observations/shared-wave-ratio-sum-bound-lean-v1/report.json),
  [seven regressions](observations/shared-wave-ratio-sum-bound-validation-v1.json).

- CV069: [HA generation/replay](observations/shared-wave-power-weighted-prefix-v1/report.json),
  [fresh Lean](observations/shared-wave-power-weighted-prefix-lean-v1/report.json),
  [seven regressions](observations/shared-wave-power-weighted-prefix-validation-v1.json).

- CV070: [HA generation/replay](observations/shared-wave-scaled-exp-terms-v1/report.json),
  [fresh Lean](observations/shared-wave-scaled-exp-terms-lean-v1/report.json),
  [seven regressions](observations/shared-wave-scaled-exp-terms-validation-v1.json).

- CV071: [HA generation/replay](observations/shared-wave-scaled-exp-bound-v1/report.json),
  [fresh Lean](observations/shared-wave-scaled-exp-bound-lean-v1/report.json),
  [seven regressions](observations/shared-wave-scaled-exp-bound-validation-v1.json).

- CV072: [HA generation/replay](observations/shared-wave-monomial-recurrence-v1/report.json),
  [fresh Lean](observations/shared-wave-monomial-recurrence-lean-v1/report.json),
  [seven regressions](observations/shared-wave-monomial-recurrence-validation-v1.json).

- CV073: [HA generation/replay](observations/shared-wave-weighted-monomial-recurrence-v1/report.json),
  [fresh Lean](observations/shared-wave-weighted-monomial-recurrence-lean-v1/report.json),
  [seven regressions](observations/shared-wave-weighted-monomial-recurrence-validation-v1.json).

- CV074: [HA generation/replay](observations/shared-wave-composition-majorant-v1/report.json),
  [fresh Lean](observations/shared-wave-composition-majorant-lean-v1/report.json),
  [seven regressions](observations/shared-wave-composition-majorant-validation-v2.json).

- CV075: [HA generation/replay](observations/shared-wave-rational-tail-majorant-v1/report.json),
  [fresh Lean](observations/shared-wave-rational-tail-majorant-lean-v1/report.json),
  [seven regressions](observations/shared-wave-rational-tail-majorant-validation-v1.json).

- CV076: [HA generation/replay](observations/shared-wave-composition-tail-bound-v1/report.json),
  [fresh Lean](observations/shared-wave-composition-tail-bound-lean-v1/report.json),
  [eight regressions](observations/shared-wave-composition-tail-bound-validation-v1.json).

- CV077: [HA generation/replay](observations/shared-wave-supplied-composition-bound-v1/report.json),
  [fresh Lean](observations/shared-wave-supplied-composition-bound-lean-v1/report.json),
  [eight regressions](observations/shared-wave-supplied-composition-bound-validation-v1.json).

- CV078: [HA generation/replay](observations/shared-wave-consumed-row-transport-v1/report.json),
  [fresh Lean](observations/shared-wave-consumed-row-transport-lean-v1/report.json),
  [seven regressions](observations/shared-wave-consumed-row-transport-validation-v1.json).

- CV079: [HA generation/replay](observations/shared-wave-successor-composition-transport-v1/report.json),
  [fresh Lean](observations/shared-wave-successor-composition-transport-lean-v1/report.json),
  [seven regressions](observations/shared-wave-successor-composition-transport-validation-v1.json).

- CV080: [HA generation/replay](observations/shared-wave-same-table-composition-v3/report.json),
  [fresh Lean](observations/shared-wave-same-table-composition-lean-v1/report.json),
  [eight regressions](observations/shared-wave-same-table-composition-validation-v1.json).

- CV081: [HA generation/replay](observations/shared-wave-supplied-composition-evaluation-v2/report.json),
  [fresh Lean](observations/shared-wave-supplied-composition-evaluation-lean-v1/report.json),
  [seven regressions](observations/shared-wave-supplied-evaluation-splitting-validation-v1.json).

- CV082: [HA generation/replay](observations/shared-wave-supplied-horner-splitting-v1/report.json),
  [fresh Lean](observations/shared-wave-supplied-horner-splitting-lean-v1/report.json),
  [seven regressions](observations/shared-wave-supplied-evaluation-splitting-validation-v1.json).

- CV083: [HA generation/replay](observations/shared-wave-geometric-tail-sandwich-v1/report.json),
  [fresh Lean](observations/shared-wave-geometric-tail-sandwich-lean-v1/report.json),
  [seven regressions](observations/shared-wave-geometric-tail-sandwich-validation-v1.json).

- CV084: [HA generation/replay](observations/shared-wave-supplied-geometric-error-v1/report.json),
  [fresh Lean](observations/shared-wave-supplied-geometric-error-lean-v1/report.json),
  [seven regressions](observations/shared-wave-supplied-geometric-error-validation-v1.json).

- CV085: [HA generation/replay](observations/shared-wave-constructed-composition-error-v3/report.json),
  [fresh Lean](observations/shared-wave-constructed-composition-error-lean-v1/report.json),
  [eight regressions](observations/shared-wave-constructed-composition-error-validation-v1.json).

- CV086: [HA generation/replay](observations/shared-wave-ternary-atanh-bound-v1/report.json),
  [fresh Lean](observations/shared-wave-ternary-atanh-bound-lean-v1/report.json),
  [seven regressions](observations/shared-wave-ternary-atanh-bound-validation-v1.json).

- CV087: [HA generation/replay](observations/shared-wave-scaled-exp-tail-v1/report.json),
  [fresh Lean](observations/shared-wave-scaled-exp-tail-lean-v1/report.json),
  [eight regressions](observations/shared-wave-scaled-exp-tail-validation-v1.json).

- CV088: [HA generation/replay](observations/shared-wave-scaled-exp-tail-decay-v1/report.json),
  [fresh Lean](observations/shared-wave-scaled-exp-tail-decay-lean-v1/report.json),
  [seven proof regressions and three solver-observer guards](observations/shared-wave-scaled-exp-tail-decay-validation-v1.json).

- CV089: [HA generation/replay](observations/shared-wave-ternary-prefix-bound-v1/report.json),
  [fresh Lean](observations/shared-wave-ternary-prefix-bound-lean-v1/report.json),
  [seven proof regressions and twenty protocol tests](observations/shared-wave-ternary-prefix-bound-validation-v1.json).

- CV090: [HA generation/replay](observations/shared-wave-atanh-truncation-v1/report.json),
  [fresh Lean](observations/shared-wave-atanh-truncation-lean-v1/report.json),
  [seven proof regressions and three solver-observer guards](observations/shared-wave-atanh-truncation-validation-v1.json).

- CV091: [HA generation/replay](observations/shared-wave-atanh-rational-truncation-v1/report.json),
  [fresh Lean](observations/shared-wave-atanh-rational-truncation-lean-v1/report.json),
  [seven regressions](observations/shared-wave-atanh-rational-truncation-validation-v1.json).

- CV092: [HA generation/replay](observations/shared-wave-atanh-scale-independence-v1/report.json),
  [fresh Lean](observations/shared-wave-atanh-scale-independence-lean-v1/report.json),
  [seven proof regressions and three solver-observer guards](observations/shared-wave-atanh-scale-independence-validation-v1.json).

- CV093: [HA generation/replay](observations/shared-wave-independent-atanh-truncation-v1/report.json),
  [fresh Lean](observations/shared-wave-independent-atanh-truncation-lean-v1/report.json),
  [seven proof regressions and three solver-observer guards](observations/shared-wave-independent-atanh-truncation-validation-v1.json).

- CV094-CV101: [fresh Lean for all eight exact certificates](observations/shared-wave-exp-continuity-chain-lean-v3/report.json).
  Their HA observations are [CV094](observations/shared-wave-exp-term-difference-v1/report.json),
  [CV095](observations/shared-wave-sum-linear-bound-v1/report.json),
  [CV096](observations/shared-wave-exp-sum-continuity-v1/report.json),
  [CV097](observations/shared-wave-exp-rescaling-v1/report.json),
  [CV098](observations/shared-wave-exp-cross-continuity-v1/report.json),
  [CV099](observations/shared-wave-exp-rational-continuity-v1/report.json),
  [CV100](observations/shared-wave-exp-truncation-v1/report.json), and
  [CV101](observations/shared-wave-exp-two-error-bound-v2/report.json).
  The 59 proof regressions are recorded in the
  [term/rescaling](observations/shared-wave-exp-rescaling-and-term-validation-v3.json),
  [sum/continuity](observations/shared-wave-sum-continuity-validation-v1.json),
  [cross-continuity](observations/shared-wave-exp-cross-continuity-validation-v1.json),
  [rational continuity](observations/shared-wave-exp-rational-continuity-validation-v3.json), and
  [truncation/two-error](observations/shared-wave-exp-truncation-two-error-validation-v3.json) reports.
  Separate [reporting regressions](observations/shared-wave-validation-reporting-regressions-v1.json)
  preserve failure semantics. The inconclusive
  [two-error solver observation](observations/exp-two-error-arithmetic-solvers-v1.json)
  is only a classical hint, not proof authority.

- CV102: [HA generation/replay](observations/shared-wave-exp-rational-two-error-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-rational-two-error-lean-v1/report.json),
  [seven proof regressions and four reporting guards](observations/shared-wave-exp-rational-two-error-validation-v1.json).

- SQ001: [HA generation/replay](observations/shared-wave-floor-sqrt-v1/report.json),
  [fresh Lean](observations/shared-wave-floor-sqrt-lean-v1/report.json),
  [eight proof and import-boundary regressions](observations/shared-wave-floor-sqrt-validation-v1.json).

- SQ002: [HA generation/replay](observations/shared-wave-floor-sqrt-comparison-v1/report.json),
  [fresh Lean](observations/shared-wave-floor-sqrt-comparison-lean-v1/report.json),
  [seven regressions](observations/shared-wave-floor-sqrt-comparison-validation-v1.json).
- SQ003: [HA generation/replay](observations/shared-wave-scaled-sqrt2-v2/report.json),
  [fresh Lean](observations/shared-wave-scaled-sqrt2-lean-v1/report.json),
  [seven proof regressions and eleven solver-observer guards](observations/shared-wave-scaled-sqrt2-validation-v1.json).
  The [first failed assembly](observations/shared-wave-scaled-sqrt2-v1/report.json)
  and [non-authoritative diagnostic](observations/scaled-sqrt2-diagnostic-v1.json)
  are retained. The single repair matched the frozen target's left-associated
  conjunction; no theorem, checker or limit was changed. The earlier
  [solver observation](observations/scaled-sqrt2-arithmetic-solvers-v1.json)
  confirmed the arithmetic with Z3; E was inconclusive and Vampire unavailable.
  No solver proof was imported as authority.

- SQ004: [HA generation/replay](observations/shared-wave-dyadic-sqrt2-v1/report.json),
  [fresh Lean](observations/shared-wave-dyadic-sqrt2-lean-v1/report.json),
  [seven proof regressions and twenty replay-protocol tests](observations/shared-wave-dyadic-sqrt2-validation-v1.json).
- SQ005: [HA generation/replay](observations/shared-wave-floor-sqrt-scaling-v1/report.json),
  [fresh Lean](observations/shared-wave-floor-sqrt-scaling-lean-v1/report.json),
  [seven regressions](observations/shared-wave-floor-sqrt-scaling-validation-v1.json).

- SQ006: [HA generation/replay](observations/shared-wave-dyadic-sqrt2-refinement-v1/report.json),
  [fresh Lean](observations/shared-wave-dyadic-sqrt2-refinement-lean-v1/report.json),
  [seven regressions](observations/shared-wave-dyadic-sqrt2-refinement-validation-v1.json).

- SQ007: [HA generation/replay](observations/shared-wave-dyadic-sqrt2-intervals-v1/report.json),
  [fresh Lean](observations/shared-wave-dyadic-sqrt2-intervals-lean-v1/report.json),
  [seven regressions](observations/shared-wave-dyadic-sqrt2-intervals-validation-v1.json).

- SQ008: [HA generation/replay](observations/shared-wave-dyadic-sqrt2-modulus-v2/report.json),
  [fresh Lean](observations/shared-wave-dyadic-sqrt2-modulus-lean-v1/report.json),
  [seven regressions](observations/shared-wave-dyadic-sqrt2-modulus-validation-v1.json).
  The [first producer failure](observations/shared-wave-dyadic-sqrt2-modulus-v1/report.json)
  is retained. The single repair corrected axiom specialization to the existing
  forall-elimination API; it did not change the target or checker.

- SQ009: [HA generation/replay](observations/shared-wave-dyadic-sqrt2-square-error-v1/report.json),
  [fresh Lean](observations/shared-wave-dyadic-sqrt2-square-error-lean-v1/report.json),
  [seven proof regressions and twelve observer guards](observations/shared-wave-dyadic-sqrt2-square-error-validation-v1.json).
  [Z3 confirmed the floor-residual helper](observations/dyadic-sqrt2-square-residual-solvers-v1.json);
  E was inconclusive. This is a hint, not proof authority.
- SQ010: [HA generation/replay](observations/shared-wave-dyadic-sqrt2-reciprocal-v1/report.json),
  [fresh Lean](observations/shared-wave-dyadic-sqrt2-reciprocal-lean-v1/report.json),
  [seven proof regressions and thirteen observer guards](observations/shared-wave-dyadic-sqrt2-reciprocal-validation-v1.json).
  Both solvers were [inconclusive](observations/dyadic-sqrt2-reciprocal-solvers-v1.json).

- AP001: [HA generation/replay](observations/shared-wave-log-root-argument-v1/report.json),
  [fresh Lean](observations/shared-wave-log-root-argument-lean-v1/report.json),
  [eight proof regressions and fourteen observer guards](observations/shared-wave-log-root-argument-validation-v1.json).
  Both solvers were [inconclusive](observations/log-root-argument-solvers-v1.json).
- AP002: [HA generation/replay](observations/shared-wave-exp-sample-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-sample-lean-v1/report.json),
  [eight proof regressions](observations/shared-wave-exp-sample-validation-v1.json).

- AP003: [HA generation/replay](observations/shared-wave-log-root-independence-v1/report.json),
  [fresh Lean](observations/shared-wave-log-root-independence-lean-v1/report.json),
  [seven proof regressions and fifteen observer guards](observations/shared-wave-log-root-independence-validation-v1.json).
  [Z3 confirmed the cross-product identity](observations/log-root-independence-solvers-v1.json);
  E was inconclusive. The solver observation is not acceptance evidence.

- AP004: [HA generation/replay](observations/shared-wave-supplied-exp-sample-v1/report.json),
  [fresh Lean](observations/shared-wave-supplied-exp-sample-lean-v1/report.json),
  [seven proof regressions and twenty replay-protocol tests](observations/shared-wave-supplied-exp-sample-validation-v1.json).
  The [bounded factorial archive audit](observations/supplied-exp-sample-factorial-audit-v1.json)
  is non-authoritative; factorial nonvanishing is proved by explicit HA induction.

- AP005: [HA generation/replay](observations/shared-wave-exp-sample-independence-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-sample-independence-lean-v1/report.json),
  [seven proof regressions and sixteen observer guards](observations/shared-wave-exp-sample-independence-validation-v1.json).
  [Z3 confirmed the zero-gap identity](observations/exp-sample-independence-solvers-v1.json);
  E was inconclusive. The hint did not replace ordinary HA reconstruction.

- AP006: [HA generation/replay](observations/shared-wave-argument-modulus-v1/report.json),
  [fresh Lean](observations/shared-wave-argument-modulus-lean-v1/report.json),
  [eight proof regressions and seventeen observer guards](observations/shared-wave-argument-modulus-validation-v1.json).
  [Both Z3 and E were inconclusive](observations/argument-modulus-solvers-v1.json);
  deterministic ordinary HA reconstruction supplied the actual proof.

- AP007: [HA generation/replay](observations/shared-wave-exp-two-sided-continuity-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-two-sided-continuity-lean-v1/report.json),
  [eight proof regressions and eighteen observer guards](observations/shared-wave-exp-two-sided-continuity-validation-v1.json).
  [Z3 confirmed scaled-gap cancellation](observations/exp-two-sided-continuity-solvers-v1.json);
  E was inconclusive. The [archive audit](observations/two-sided-continuity-archive-audit-v1.json)
  and [sandbox diagnostic](observations/exp-two-sided-continuity-solvers-sandbox-v1.json)
  are non-authoritative; every retained ordinary proof body was replayed.

- AP008: [HA generation/replay](observations/shared-wave-exp-two-sided-horizons-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-two-sided-horizons-lean-v1/report.json),
  [eight proof regressions and nineteen observer guards](observations/shared-wave-exp-two-sided-horizons-validation-v1.json).
  [Both solvers were inconclusive](observations/exp-two-sided-horizons-solvers-v1.json);
  the [bounded archive audit](observations/two-sided-horizons-archive-audit-v1.json)
  is provenance, not proof authority.

- AP009: [HA generation/replay](observations/shared-wave-exp-sample-modulus-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-sample-modulus-lean-v1/report.json),
  [eight proof regressions and twenty observer guards](observations/shared-wave-exp-sample-modulus-validation-v1.json).
  [Both solvers were inconclusive](observations/exp-sample-modulus-solvers-v1.json);
  the [archive/target audit](observations/sample-modulus-archive-audit-v1.json)
  is non-authoritative. Only proved positive factors were cancelled.

- AP010: [HA generation/replay](observations/shared-wave-positive-power-comparison-v1/report.json),
  [fresh Lean](observations/shared-wave-positive-power-comparison-lean-v1/report.json),
  [seven proof regressions and twenty-one observer guards](observations/shared-wave-positive-power-comparison-validation-v1.json).
  [Both solvers were inconclusive](observations/positive-power-comparison-solvers-v1.json);
  the [archive audit](observations/positive-power-comparison-archive-audit-v1.json)
  records the endpoint ambiguity resolved by explicit CV071 ownership.

- AP011: [HA generation/replay](observations/shared-wave-approximation-power-bounds-v1/report.json),
  [fresh Lean](observations/shared-wave-approximation-power-bounds-lean-v1/report.json),
  [seven proof regressions and twenty-two observer guards](observations/shared-wave-approximation-power-bounds-validation-v1.json).
  [Z3 confirmed exponent alignment](observations/approximation-power-bounds-solvers-v1.json);
  E was inconclusive. The [archive audit](observations/approximation-power-bounds-archive-audit-v1.json)
  is provenance, not proof authority.

- AP012: [HA generation/replay](observations/shared-wave-exp-sample-uniform-error-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-sample-uniform-error-lean-v1/report.json),
  [eight proof regressions and twenty-three observer guards](observations/shared-wave-exp-sample-uniform-error-validation-v1.json).
  [Both solvers were inconclusive](observations/uniform-sample-error-solvers-v1.json);
  the [archive/target audit](observations/uniform-sample-error-archive-audit-v1.json)
  is non-authoritative. The result contains no assumed accuracy clause.

- AP013: [HA generation/replay](observations/shared-wave-exp-sample-all-precision-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-sample-all-precision-lean-v1/report.json),
  [seven proof regressions and twenty HA/Lean protocol tests](observations/shared-wave-exp-sample-all-precision-validation-v1.json).
  The [archive/target audit](observations/all-precision-sample-error-archive-audit-v1.json)
  is non-authoritative. This is constructive case composition, with no new
  solver oracle, induction, definition, or analytic assumption.

- AP014: [repaired HA generation/replay](observations/shared-wave-fixed-precision-threshold-v2/report.json),
  [fresh Lean](observations/shared-wave-fixed-precision-threshold-lean-v1/report.json),
  [nine proof regressions and twenty-four observer guards](observations/shared-wave-fixed-precision-threshold-validation-v1.json).
  The [rejected first attempt](observations/shared-wave-fixed-precision-threshold-v1/report.json)
  and [bounded local diagnostic](observations/fixed-precision-threshold-local-diagnostic-v1.json)
  record the inferability failure and its single repair. [Z3 confirmed the
  exact arithmetic target](observations/fixed-precision-threshold-solvers-v1.json)
  before that repair; E was inconclusive. No solver output is proof authority.

- AP015: [HA generation/replay](observations/shared-wave-exp-sample-dyadic-error-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-sample-dyadic-error-lean-v1/report.json),
  [eight proof regressions and twenty-five observer guards](observations/shared-wave-exp-sample-dyadic-error-validation-v1.json).
  [Both solvers were inconclusive](observations/exp-sample-dyadic-error-solvers-v1.json).
  The [exact target and predecessor archive audit](observations/exp-sample-dyadic-error-archive-audit-v1.json)
  is provenance, not proof authority. Generation used 27.900420 CPU seconds,
  below its unchanged 28-second ceiling; fresh replay used 15.476446 seconds.

- AP016: [HA generation/replay](observations/shared-wave-atanh-odd-slice-v1/report.json),
  [fresh Lean](observations/shared-wave-atanh-odd-slice-lean-v1/report.json),
  [seven proof regressions](observations/shared-wave-atanh-odd-slice-validation-v1.json).
  The [exact archive and definition-DAG audit](observations/atanh-odd-slice-archive-audit-v1.json)
  is non-authoritative. This is logical assembly from actual parity, slice and
  natural-order bodies, with no new solver target or induction.

- AP017: [HA generation/replay](observations/shared-wave-paired-horner-v1/report.json),
  [fresh Lean](observations/shared-wave-paired-horner-lean-v1/report.json),
  [seven proof regressions and twenty-six observer guards](observations/shared-wave-paired-horner-validation-v1.json).
  [Z3 confirmed the paired-step arithmetic](observations/paired-horner-solvers-v1.json);
  E was inconclusive. The [archive and local-constructor audit](observations/paired-horner-archive-audit-v1.json)
  is diagnostic, not authority. One explicit induction compares every pair
  of steps; the terminal even-zero premise is retained and tested.

- AP018: [HA generation/replay](observations/shared-wave-paired-power-v1/report.json),
  [fresh Lean](observations/shared-wave-paired-power-lean-v1/report.json),
  [seven proof regressions and twenty protocol tests](observations/shared-wave-paired-power-validation-v1.json).
  The [archive and local-constructor audit](observations/paired-power-archive-audit-v1.json)
  is diagnostic, not authority. Actual power-successor bodies and one
  induction prove the doubled exponent identity; the final successor
  supplies the leading factor. No new solver target was needed.

- AP019: [HA generation/replay](observations/shared-wave-odd-horner-quotient-v1/report.json),
  [fresh Lean](observations/shared-wave-odd-horner-quotient-lean-v1/report.json),
  [seven proof regressions and twenty-seven observer guards](observations/shared-wave-odd-horner-quotient-validation-v1.json).
  [Z3 confirmed the arithmetic helper](observations/odd-horner-quotient-solvers-v1.json);
  E was inconclusive. The [first archive audit](observations/odd-horner-quotient-archive-audit-v1.json)
  found a missing positivity endpoint in its selected archive; the
  [corrected audit](observations/odd-horner-quotient-archive-audit-v2.json)
  uses the actual AP010 positivity body. Neither diagnostic is proof authority.

- AP020: [HA generation/replay](observations/shared-wave-finite-odd-log-series-v1/report.json),
  [fresh Lean](observations/shared-wave-finite-odd-log-series-lean-v1/report.json),
  [seven proof regressions and twenty-eight observer guards](observations/shared-wave-finite-odd-log-series-validation-v1.json).
  [Z3 confirmed the arithmetic helper](observations/finite-odd-log-series-solvers-v1.json);
  E was inconclusive. The [exact endpoint and local-constructor audit](observations/finite-odd-log-series-archive-audit-v1.json)
  is diagnostic, not authority. The actual weighted-sum and weight/power
  invariant supply the finite series without an additional induction.

- AP021: [HA generation/replay](observations/shared-wave-finite-exp-series-v1/report.json),
  [fresh Lean](observations/shared-wave-finite-exp-series-lean-v1/report.json),
  [seven proof regressions and twenty-nine observer guards](observations/shared-wave-finite-exp-series-validation-v1.json).
  [Z3 confirmed the normalization helper](observations/finite-exp-series-solvers-v1.json);
  E was inconclusive. The [exact archive and local-constructor audit](observations/finite-exp-series-archive-audit-v1.json)
  is diagnostic, not authority. The proof uses the existing actual
  factorial/power constructors and supplied-sample normalization law.

- AP022: [HA generation/replay](observations/shared-wave-factorial-atanh-prefix-v1/report.json),
  [fresh Lean](observations/shared-wave-factorial-atanh-prefix-lean-v1/report.json),
  [seven proof regressions and twenty protocol tests](observations/shared-wave-factorial-atanh-prefix-validation-v1.json).
  The [exact archive and local-constructor audit](observations/factorial-atanh-prefix-archive-audit-v1.json)
  is diagnostic, not authority. One explicit induction proves the needed
  factorial divisibilities; the existing actual coefficient constructor
  consumes them. No new solver target was needed.

- AP023: [HA generation/replay](observations/shared-wave-factorial-exp-sample-v1/report.json),
  [fresh Lean](observations/shared-wave-factorial-exp-sample-lean-v1/report.json),
  [seven proof regressions](observations/shared-wave-factorial-exp-sample-validation-v1.json).
  The [archive/local-constructor audit](observations/factorial-exp-sample-archive-audit-v1.json)
  and [size/hash audit](observations/factorial-exp-sample-metrics-v1.json) are
  diagnostics. The fixed scale and all original computation fields are
  conclusions, without a new induction or definition. This is not yet the
  complete certified primitive-recursive CApprox trace.

- AP024: [HA generation/replay](observations/shared-wave-atomic-computation-decisions-v1/report.json),
  [fresh Lean](observations/shared-wave-atomic-computation-decisions-lean-v1/report.json),
  [seven proof regressions and twenty protocol guards](observations/shared-wave-atomic-computation-decisions-validation-v1.json).
  The [endpoint/local-constructor audit](observations/atomic-computation-decisions-archive-audit-v1.json)
  and [size/hash audit](observations/atomic-computation-decisions-metrics-v1.json)
  are diagnostics. Ordinary constructive terms, including one factorial
  uniqueness induction, decide the eight relations without an LEM/Markov
  axiom. These are verifier prerequisites, not a complete CApprox verifier.

- AP025: [HA generation/replay](observations/shared-wave-approximation-component-decisions-v1/report.json),
  [fresh Lean](observations/shared-wave-approximation-component-decisions-lean-v1/report.json),
  [seven proof regressions](observations/shared-wave-approximation-component-decisions-validation-v1.json).
  The [endpoint/local-constructor audit](observations/approximation-component-decisions-archive-audit-v1.json)
  and [size/hash audit](observations/approximation-component-decisions-metrics-v1.json)
  are diagnostics. Actual parity and functional-computation proofs decide
  these three components without a new induction or definition. Finite-table
  and complete-record verification remain separate obligations.

- AP026: [HA generation/replay](observations/shared-wave-finite-table-decisions-v1/report.json),
  [fresh Lean](observations/shared-wave-finite-table-decisions-lean-v1/report.json),
  [seven proof regressions](observations/shared-wave-finite-table-decisions-validation-v1.json).
  The [endpoint/local-constructor audit](observations/finite-table-decisions-archive-audit-v1.json)
  and [size/hash audit](observations/finite-table-decisions-metrics-v1.json)
  are diagnostics. A deterministic row-proof generator and a bounded-prefix
  generator emit ordinary HA terms for three table types, including invalid
  tables and zero/empty boundaries. Three explicit inductions are replayed;
  no new trusted inference rule is added.

- AP027: [HA generation/replay](observations/shared-wave-prescribed-sample-decision-v1/report.json),
  [fresh Lean](observations/shared-wave-prescribed-sample-decision-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-prescribed-sample-decision-validation-v1.json).
  The [first local audit](observations/prescribed-sample-decision-archive-audit-v1.json)
  rejected unannotated nested OrElim eliminands. A single sequential-branch
  repair passes the [second audit](observations/prescribed-sample-decision-archive-audit-v2.json)
  without changing the target or kernel; both records are retained.
  [Size/hash audit](observations/prescribed-sample-decision-metrics-v1.json).
  The supplied computation is decidable; a canonical coded-record/program
  connection and analytic identification are not claimed by this theorem.

- AP028: [HA generation/replay](observations/shared-wave-approximation-record-exists-v1/report.json),
  [fresh Lean](observations/shared-wave-approximation-record-exists-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-approximation-record-exists-validation-v1.json).
  The [definition/endpoint/local-constructor audit](observations/approximation-record-exists-archive-audit-v1.json)
  and [size/hash audit](observations/approximation-record-exists-metrics-v1.json)
  are diagnostics. Local ND0449 conservatively records all fifteen consumed
  fields, positive denominators and the fixed n+8 computation. Two beta-code
  components remain explicit; single-code packing, a PR program certificate
  and analytic accuracy are not definition clauses or claims of this result.

- AP029: [HA generation/replay](observations/shared-wave-approximation-record-decision-v1/report.json),
  [fresh Lean](observations/shared-wave-approximation-record-decision-lean-v1/report.json),
  [eight proof regressions](observations/shared-wave-approximation-record-decision-validation-v1.json).
  The [endpoint/local-constructor audit](observations/approximation-record-decision-archive-audit-v1.json)
  and [size/hash audit](observations/approximation-record-decision-metrics-v1.json)
  are diagnostics. Decoding plus actual beta uniqueness removes the apparent
  unbounded existential witness search. Exact Python tests exercise a genuine
  precision-zero record, an alternative code for its same fields and corrupted
  fields; these examples remain calibration, not formal proof authority.

- AP030: [HA generation/replay](observations/shared-wave-approximation-record-independence-v1/report.json),
  [fresh Lean](observations/shared-wave-approximation-record-independence-lean-v1/report.json),
  [seven proof regressions and twenty protocol guards](observations/shared-wave-approximation-record-independence-validation-v1.json).
  The [endpoint/local-constructor audit](observations/approximation-record-independence-archive-audit-v1.json)
  and [size/hash audit](observations/record-error-ancestor-metrics-v1.json)
  are diagnostics. Actual AP005 bodies establish equality of rational outputs
  after both records are opened. The code numbers may differ; no new induction,
  definition or analytic claim is added.

- AP031: [HA generation/replay](observations/shared-wave-approximation-record-error-v2/report.json),
  [fresh Lean](observations/shared-wave-approximation-record-error-lean-v2/report.json),
  [eight proof regressions](observations/shared-wave-approximation-record-error-validation-v2.json)
  and [twenty protocol guards](observations/shared-wave-approximation-record-error-protocol-validation-v2.json).
  The [original run](observations/shared-wave-approximation-record-error-v1/report.json)
  hit the generation CPU guard and remains `not_checked`. The repair removes
  repeated recursive source hashing, using a [frozen exact closure](observations/approximation-record-error-source-closure-v1.json)
  and streaming revalidation of every actual file on every call. It does not
  alter the theorem, proof checker, positive replay or resource ceilings.
  The [endpoint audit](observations/approximation-record-error-archive-audit-v1.json),
  [cost audit](observations/approximation-record-error-cost-audit-v1.json) and
  [size/hash audit](observations/log-exp-witness-archive-audit-v1.json)
  are diagnostics, not proof authority. All finite increments including zero
  are covered; analytic identification and the certified PR evaluator remain open.

- AP032: [HA generation/replay](observations/shared-wave-log-exp-witness-v1/report.json),
  [fresh Lean](observations/shared-wave-log-exp-witness-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-log-exp-witness-validation-v1.json).
  The [endpoint/constructor audit](observations/log-exp-witness-archive-audit-v1.json)
  and [size/hash audit](observations/log-exp-budget-archive-audit-v1.json) are diagnostics.
  CV085's actual construction/evaluation stages and CV073's actual recurrence
  proof use the same product table. Thus the near-two bound now belongs to
  genuine finite exponential terms, with positive input/output denominators.
  This is not yet the infinite logarithm identity. The original phase caps
  apply, with no inherited CV085 exception.

- AP033: [HA generation/replay](observations/shared-wave-log-exp-budget-v1/report.json),
  [fresh Lean](observations/shared-wave-log-exp-budget-lean-v1/report.json),
  [ten proof regressions and twenty protocol guards](observations/shared-wave-log-exp-budget-validation-v1.json).
  The [local audit](observations/log-exp-budget-archive-audit-v1.json) and
  [size/hash audit](observations/log-exp-dyadic-witness-archive-audit-v1.json)
  are diagnostics. Two ordinary HA inductions prove (n+2)*2^n<=2*3^n and
  n+1<=3^n; arithmetic gives the explicit auxiliary cutoff N=18*r+2.
  [Step-search](observations/log-exp-budget-step-solvers-v1.json) and
  [budget-search](observations/log-exp-budget-arithmetic-solvers-v1.json) logs
  record Z3/E non-resolution and unavailable Vampire, with no proof authority.
  The fixed irrationality approximation program is unchanged.

- AP034: [HA generation/replay](observations/shared-wave-log-exp-dyadic-witness-v1/report.json),
  [fresh Lean](observations/shared-wave-log-exp-dyadic-witness-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-log-exp-dyadic-witness-validation-v1.json).
  The [local audit](observations/log-exp-dyadic-witness-archive-audit-v1.json) and
  [size/hash audit](observations/exp-recurrence-normalization-archive-audit-v1.json)
  are diagnostics. At the explicit auxiliary degree 18*2^n+2, the actual
  finite log/exponential sum is within 2^-n of two. The target retains its
  coefficient table, Horner value, power, recurrence, head and sum; no accuracy
  clause is smuggled into a computation definition. Infinite analytic
  identification and the original irrationality certificate remain open.

- AP035: [HA generation/replay](observations/shared-wave-exp-recurrence-normalization-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-recurrence-normalization-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-recurrence-normalization-validation-v1.json).
  The [constructor audit](observations/exp-recurrence-normalization-archive-audit-v1.json)
  and [size/hash audit](observations/exp-recurrence-series-input-audit-v1.json)
  are diagnostics. The single index induction derives factorial normalization
  from the supplied recurrence and head, including zero denominator, numerator,
  head and horizon. Rational validity and analytic interpretation are separate.

- AP036: [HA generation/replay](observations/shared-wave-exp-recurrence-series-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-recurrence-series-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-recurrence-series-validation-v1.json).
  The [constructor audit](observations/exp-recurrence-series-archive-audit-v1.json)
  and [size/hash audit](observations/convolution-shift-archive-audit-v2.json)
  are diagnostics. Every actual term T[j]/h is identified with x^j/(j!*d^j)
  after constructing the factorial and both powers and proving nonzero
  denominators. Zero numerator, index and horizon are included. This finite
  interpretation does not assert convergence or an analytic identity.

- AP037: [HA generation/replay](observations/shared-wave-convolution-shift-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-shift-lean-v1/report.json),
  [nine proof regressions and twenty protocol guards](observations/shared-wave-convolution-shift-validation-v1.json).
  The [first endpoint audit](observations/convolution-shift-archive-audit-v1.json)
  detects a missing body in the proposed CV010 owner; the
  [corrected audit](observations/convolution-shift-archive-audit-v2.json) uses its
  actual CV008 owner and checks every local constructor. The
  [size/hash audit](observations/exp-convolution-recurrence-archive-audit-v1.json)
  is diagnostic. The shift identity requires the zero head and the inclusive
  local endpoint. Tests include counterexamples when either is omitted.

- AP038: [HA generation/replay](observations/shared-wave-exp-convolution-recurrence-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-convolution-recurrence-lean-v1/report.json),
  [ten proof regressions and twenty protocol guards](observations/shared-wave-exp-convolution-recurrence-validation-v1.json).
  The [constructor audit](observations/exp-convolution-recurrence-archive-audit-v1.json)
  and [size/hash audit](observations/exp-convolution-prefix-archive-audit-v1.json)
  are diagnostics. Actual Euler tables, the Euler product rule and the local
  shift law give the recurrence for the added argument below the cutoff.
  [Solver observations](observations/exp-convolution-recurrence-solvers-v1.json)
  record Z3 resolving the arithmetic helper, E not resolving it and unavailable
  Vampire. HA reconstruction remains independent; no solver receipt is trusted.
  A counterexample at the cutoff guards against a false full-tail claim.

- AP039: [HA generation/replay](observations/shared-wave-exp-convolution-prefix-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-convolution-prefix-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-convolution-prefix-validation-v1.json).
  The [constructor audit](observations/exp-convolution-prefix-archive-audit-v1.json)
  and [size/hash audit](observations/convolution-prefix-order-archive-audit-v1.json)
  are diagnostics. The actual product table has head a0*b0 and the factorial
  terms for x+y. Its sum is constructed, not assumed equal to the product
  of the truncated input sums. A degree-one counterexample protects this
  boundary. AP042 below now supplies a finite discarded-term estimate under
  its explicit argument bound; analytic addition remains open.

- AP040: [HA generation/replay](observations/shared-wave-convolution-prefix-order-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-prefix-order-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-convolution-prefix-order-validation-v1.json).
  The [constructor audit](observations/convolution-prefix-order-archive-audit-v1.json)
  and [size/hash audit](observations/convolution-sum-sandwich-archive-audit-v1.json)
  are diagnostics. Both ordered lengths and unchanged input codes are required;
  tests exhibit failures without either restriction. Every coefficient index
  and empty inputs are included. The resulting order is finite, not a tail bound.

- AP041: [HA generation/replay](observations/shared-wave-convolution-sum-sandwich-v1/report.json),
  [fresh Lean](observations/shared-wave-convolution-sum-sandwich-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-convolution-sum-sandwich-validation-v1.json).
  The [size/hash audit](observations/exp-product-error-archive-audit-v2.json)
  is diagnostic. All four sums and the extended-input Cauchy table are
  constructed. The theorem distinguishes the two output cutoffs and includes
  empty inputs; it supplies no analytic identity or error bound on its own.

- AP042: [HA generation/replay](observations/shared-wave-exp-product-error-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-product-error-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-product-error-validation-v1.json).
  The [constructor audit](observations/exp-product-error-constructor-audit-v1.json)
  and [size/hash audit](observations/exp-supplied-product-archive-audit-v1.json)
  are diagnostics. Actual recurrence, head, prefix and whole sums yield the
  finite dyadic product error. Both d!=0 and x+y<=d are essential; tests
  exhibit counterexamples without them. No infinite addition or positive
  rational-denominator claim is made, and zero heads remain permitted.

- AP043: [HA generation/replay](observations/shared-wave-exp-supplied-product-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-supplied-product-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-supplied-product-validation-v1.json).
  The [corrected constructor audit](observations/exp-supplied-product-constructor-audit-v2.json)
  is diagnostic; its first failed owner selection remains recorded.
  [Solver observations](observations/exp-supplied-product-solvers-v1.json)
  report unresolved Z3/E searches and unavailable Vampire, not proof authority.
  Checked finite value independence transports the internal Cauchy sum to the
  supplied third table. Numerators and beta codes are not asserted equal;
  independent heads, including zero heads, are explicitly tested.

- AP044: [HA generation/replay](observations/shared-wave-exp-half-square-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-half-square-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-half-square-validation-v1.json).
  The [corrected constructor audit](observations/exp-half-square-constructor-audit-v2.json)
  and [size/hash audit](observations/half-square-error-transfer-constructor-audit-v1.json)
  are diagnostics; the first missing-Sum-definition audit remains preserved.
  The finite half-argument table has a proved positive normalization. Its
  square estimate retains the supplied whole-argument code and allows that
  supplied head to be zero. Exact equality is not claimed at finite cutoffs;
  no identification with logarithm or sqrt(2) is assumed.

- AP045: [HA generation/replay](observations/shared-wave-half-square-error-transfer-v1/report.json),
  [fresh Lean](observations/shared-wave-half-square-error-transfer-lean-v1/report.json),
  [nine proof regressions and twenty protocol guards](observations/shared-wave-half-square-error-transfer-validation-v1.json).
  The [constructor audit](observations/half-square-error-transfer-constructor-audit-v1.json)
  and [size/hash audit](observations/half-log-precision-constructor-audit-v1.json)
  are diagnostics. The five supplied inequalities yield upper allowance 3/r
  and lower allowance 1/r after positive cancellation. Small-model tests
  include zero remaining scales and counterexamples when the cancelled head
  is zero or the precision order is removed. No exponential is constructed.

- AP046: [HA generation/replay](observations/shared-wave-half-log-precision-v1/report.json),
  [fresh Lean](observations/shared-wave-half-log-precision-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-half-log-precision-validation-v1.json).
  The [constructor audit](observations/half-log-precision-constructor-audit-v1.json)
  and [size/hash audit](observations/half-log-square-archive-audit-v1.json)
  are diagnostics. One new ordinary induction proves the generic binary
  growth inequality; the actual old cutoff helper supplies the required
  precision domination. Tests cover r=0, reject forged induction, and keep
  example computations below 128 bits. No enormous ground power is generated.

- AP047: [HA generation/replay](observations/shared-wave-half-log-square-v2/report.json),
  [fresh Lean](observations/shared-wave-half-log-square-lean-v1/report.json),
  [nine proof regressions and twenty protocol guards](observations/shared-wave-half-log-square-validation-v1.json).
  The [first replay hit the CPU cap](observations/shared-wave-half-log-square-v1/report.json)
  and remains unverified. The single repair removes repeated definition/source
  setup, not any proof body: [exact definition and source comparison](observations/half-log-square-input-repair-audit-v1.json).
  Both attempts generated the identical canonical certificate. Fresh replay
  now uses 19.347711 CPU seconds under the unchanged 20-second cap. Every
  retained ancestor body is checked. No infinite logarithm/root identity is assumed.

- AP048: [HA generation/replay](observations/shared-wave-square-error-linear-v1/report.json),
  [fresh Lean](observations/shared-wave-square-error-linear-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-square-error-linear-validation-v1.json).
  The [constructor audit](observations/square-error-linear-constructor-audit-v1.json)
  checks difference-of-squares reasoning with actual additive gaps. The
  [solver observations](observations/square-error-linear-solvers-v1.json)
  are not proofs: Z3/E were unresolved under their small limits, and Vampire
  was unavailable. Only ordinary HA bodies provide proof authority.

- AP049: [HA generation/replay](observations/shared-wave-half-log-root-comparison-v1/report.json),
  [fresh Lean](observations/shared-wave-half-log-root-comparison-lean-v1/report.json),
  [eight proof regressions, protocol guards and solver-observer regressions](observations/shared-wave-half-log-root-comparison-validation-v1.json).
  The [constructor audit](observations/half-log-root-comparison-constructor-audit-v1.json)
  binds all five local stages and thirteen actual endpoints. Positive h,d and
  supplied finite square bounds give `r*u*d<=r*s*h+7*h*d` and
  `r*s*h<=r*u*d+h*d`. This lemma does not itself construct the witnesses.

- AP050: [HA generation/replay](observations/shared-wave-half-log-root-witness-v1/report.json),
  [fresh Lean](observations/shared-wave-half-log-root-witness-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-half-log-root-witness-validation-v1.json).
  The [constructor audit](observations/half-log-root-witness-constructor-audit-v1.json)
  verifies the unconditional actual-witness assembly and all five owned
  endpoints. Nineteen existing definitions are shared conservatively; no new
  definition, induction or axiom is added. For r=2^n, the rational reading is
  `-1/r<=u/h-s/r<=7/r`, with both computations constructed and h,r positive.
  Replay passes at 19.934335 CPU seconds, very near the unchanged cap. Future
  large assemblies need cost-aware proof packaging, not relaxed limits.
  Analytic identification and the final irrationality certificate remain open.

- AP051: [HA generation/replay](observations/shared-wave-exp-large-argument-ratio-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-large-argument-ratio-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-large-argument-ratio-validation-v1.json).
  For x<=L*d and j+1>=2*L, positive-coefficient cancellation proves
  `2*T[j+1]<=T[j]`. Neither L nor x is cancelled, so their zero cases remain.
  The [solver observations](observations/exp-large-argument-ratio-solvers-v1.json)
  record Z3 UNSAT with proof-shaped output for the exact arithmetic helper;
  E was unresolved and Vampire unavailable. That log is not reconstructed
  proof authority: the deterministic ordinary HA body and fresh Lean check
  are separate. No solver speedup is claimed.

- AP052: [HA generation/replay](observations/shared-wave-exp-large-argument-tail-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-large-argument-tail-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-large-argument-tail-validation-v1.json).
  For M>=2*L, construct the actual length-(N+1) slice starting at M, its
  decoded head a and its sum s; retain its halving predicate and prove s<=2*a.
  Seven exact existing definitions are reused. No new induction is introduced.

- AP053: [HA generation/replay](observations/shared-wave-halving-prefix-decay-v1/report.json),
  [fresh Lean](observations/shared-wave-halving-prefix-decay-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-halving-prefix-decay-validation-v1.json).
  One ordinary induction proves `p*a[k]<=a[0]` for a supplied halving prefix,
  k<=N and actual Pow(2,k,p). Seven existing definitions are reused;
  zero index, zero horizon and zero head are covered without division.

- AP054: [HA generation/replay](observations/shared-wave-exp-large-argument-decay-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-large-argument-decay-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-large-argument-decay-validation-v2.json).
  Construct p=2^m, both actual heads, the slice starting at K+m and its sum s;
  for K>=2*L prove `p*T[K+m]<=T[K]` and `p*s<=2*T[K]`, uniformly in N.
  Ten existing definitions are reused; no new induction is introduced.
  The [first validation](observations/shared-wave-exp-large-argument-decay-validation-v1.json)
  found a test-count typo: all 864 rational examples passed their inequalities,
  but the test incorrectly expected more than 1,000 examples. The single repair
  asserts the exact count 864; theorem, producer and certificate bytes are unchanged.

- AP055: [HA generation/replay](observations/shared-wave-exp-large-argument-truncation-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-large-argument-truncation-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-large-argument-truncation-validation-v1.json).
  Retain a supplied head a0 at K, prefix sum s of length K+m, whole sum t of
  length K+m+N+1 and actual p=2^m. Exact affine-sum, head and power uniqueness
  identify AP054's witnesses and prove `s<=t` and `p*t<=p*s+2*a0`.
  Eleven existing definitions are reused. The 864 rational models include
  nine empty-prefix cases. No analytic limit or original-head bound is assumed.

- AP056: [HA generation/replay](observations/shared-wave-exp-geometric-majorant-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-geometric-majorant-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-geometric-majorant-validation-v1.json).
  One ordinary induction proves `T[k]<=L^k*h` for k<=N, x<=L*d and d!=0.
  Zero L, argument, index and head are covered. The exact one-step helper has
  an [untrusted Z3 UNSAT observation](observations/exp-geometric-majorant-solvers-v1.json);
  E is unresolved within three seconds and Vampire unavailable. The checked
  ordinary HA construction does not trust any solver output.

- AP057: [HA generation/replay](observations/shared-wave-exp-normalized-truncation-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-normalized-truncation-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-normalized-truncation-validation-v1.json).
  For K>=2*L and actual p=2^m, B=L^K, retain the supplied original head h
  and sums s,t, proving `s<=t` and `p*t<=p*s+2*(B*h)`. The decoded head
  at K is constructed and bounded, not added as an assumption. Empty short
  prefixes and zero heads are covered.

- AP058: [HA generation/replay](observations/shared-wave-exp-normalized-witness-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-normalized-witness-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-normalized-witness-validation-v1.json).
  Construct eleven witnesses, retaining the actual weight/term tables,
  positive original head, factorial/power normalization at every index,
  recurrence, both sums, nonzero p=2^m, B=L^K and both AP057 bounds.
  This finite witness theorem assumes no analytic exponential or limit.

- AP059: [HA generation/replay](observations/shared-wave-exp-large-argument-product-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-large-argument-product-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-large-argument-product-validation-v1.json).
  For x+y<=L*d, K>=2*L and n=K+m, construct an actual convolution with
  added-argument recurrence and product head a0*b0. Its degree-n sum s
  and input sums u,v satisfy `s<=u*v` and
  `p*(u*v)<=p*s+2*(B*(a0*b0))`, where p=2^(m+1), B=L^K.
  No equality of finite products with infinite exponentials is asserted.

- AP060: [HA generation/replay](observations/shared-wave-exp-recurrence-independence-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-recurrence-independence-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-recurrence-independence-validation-v1.json).
  Positive d,e, equal arguments x*e=y*d, two actual recurrences, their
  heads h,g and supplied sums s,t imply `g*s=h*t`. No argument bound or
  positive head is required. One ordinary induction proves termwise cross-
  equality; existing ND0409 and the actual CV006 sum-linearity body finish.
  The [exact cross-step Z3 observation](observations/exp-recurrence-independence-solvers-v1.json)
  reports UNSAT but is not proof authority. All 3,024 integer models pass,
  including 1,728 with arguments greater than one and separate zero heads.

- AP061: [HA generation/replay](observations/shared-wave-exp-supplied-large-product-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-supplied-large-product-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-supplied-large-product-validation-v1.json).
  Preserve all three supplied tables, heads a0,b0,c0 and degree-K+m sums
  u,v,w. AP060 identifies the internal convolution value and gives
  `(a0*b0)*w<=c0*(u*v)` and
  `p*(c0*(u*v))<=p*((a0*b0)*w)+2*(B*(c0*(a0*b0)))`.
  The [bounded solver probe](observations/exp-supplied-large-product-solvers-v1.json)
  is unresolved; the independent ordinary HA construction passes.

- AP062: [HA generation/replay](observations/shared-wave-exp-binary-budget-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-binary-budget-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-binary-budget-validation-v1.json).
  One ordinary induction proves `L^K<=2^(L*K)` for actual supplied powers.
  With B=L^K, r=2^n and p=2^(L*K+n+1), prove r,p nonzero and
  `2*(r*B)<=p`, including L=K=n=0 and the actual value 0^0=1.
  No large ground power is materialized. The
  [arithmetic solver probe](observations/exp-binary-budget-solvers-v1.json)
  is unresolved; the HA/Lean certificate is independently checked.

- AP063: [HA generation/replay](observations/shared-wave-exp-requested-truncation-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-requested-truncation-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-requested-truncation-validation-v1.json).
  For x<=L*d and K>=2*L, short length K+(L*K+n+1) suffices for
  `s<=t` and `r*t<=r*s+h`, uniformly in every extra finite horizon.
  The theorem constructs its auxiliary powers and proves r=2^n nonzero.
  Its [positive-cancellation helper](observations/exp-requested-truncation-solvers-v1.json)
  has an untrusted Z3 UNSAT observation and a separate ordinary HA proof.

- AP064: [HA generation/replay](observations/shared-wave-exp-requested-product-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-requested-product-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-requested-product-validation-v1.json).
  At D=K+(L*K+n), retain three supplied degree-D sums and input recurrences
  through 2*D+1. Prove r=2^n nonzero, `(a0*b0)*w<=c0*(u*v)`, and
  `r*(c0*(u*v))<=r*((a0*b0)*w)+c0*(a0*b0)`.
  This is finite product accuracy, not an assumed analytic addition law.

- AP065: [HA generation/replay](observations/shared-wave-exp-independent-horizon-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-independent-horizon-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-independent-horizon-validation-v1.json).
  Retain independent denominators d,e, equal arguments x*e=y*d, heads h,g
  and sums s,t at degrees D=K+(L*K+n) and (D+1)+N. Construct the fine
  table's short sum and prove `g*s<=h*t` and
  `r*(h*t)<=r*(g*s)+h*g`, with actual r=2^n proved nonzero.
  All 1,440 integer models pass, including zero heads, different denominator
  representations and arguments above one. The
  [bounded solver probe](observations/exp-independent-horizon-solvers-v1.json)
  remains unresolved; full HA and Lean checks pass independently.

- AP066: [HA generation/replay](observations/shared-wave-exp-uniform-witness-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-uniform-witness-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-uniform-witness-validation-v1.json).
  Construct the coarse weight/term tables, positive head h, sum s and r=2^n
  before `forall N`; then construct the positive fine head g and sum t at
  every degree (D+1)+N. Retain all eleven CV070 fields for both computations,
  including their factorial head factorizations and all-index term identities.
  The same coarse witness satisfies `g*s<=h*t` and
  `r*(h*t)<=r*(g*s)+h*g` for every N. All 272 bounded integer models pass.
  The first constructor-audit harness had an incorrect checker-module import;
  its [failed record](observations/exp-uniform-witness-constructor-audit-v1.json)
  and [corrected audit](observations/exp-uniform-witness-constructor-audit-v2.json)
  are both preserved. The proof producer did not require a repair.

- AP067: [HA generation/replay](observations/shared-wave-exp-product-witness-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-product-witness-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-product-witness-validation-v1.json).
  Construct three actual CV070 tables at x, y and x+y, their nonzero heads
  a0,b0,c0, their full sums, both input prefixes u,v and the precision power.
  Preserve all 39 fields, including each all-index factorial normalization.
  AP064 gives `(a0*b0)*w<=c0*(u*v)` and its requested dyadic upper error
  for those same witnesses. All 62 bounded integer models pass. The first
  [constructor/ownership audit](observations/exp-product-witness-constructor-audit-v1.json)
  exposed selection of the wrong archive for the sum-existence endpoint;
  the [single repair](observations/exp-product-witness-constructor-audit-v2.json)
  selects its actual CV003 body. No target or resource ceiling changed.

- AP068: [HA generation/replay](observations/shared-wave-exp-relative-continuity-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-relative-continuity-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-relative-continuity-validation-v1.json).
  With y=x+g, a positive common argument denominator and the same head,
  prove `s<=t` and `d*t<=d*s+g*t` without any upper bound on x or y.
  Construct actual tail slices and bound the preceding prefix by t; no
  small-argument majorant is imported. All 2,268 integer models pass,
  including arguments above two and zero heads. The
  [three-second solver probes](observations/exp-relative-continuity-solvers-v1.json)
  leave Z3 and E unresolved; Vampire is unavailable. The ordinary HA proof
  and independent Lean check succeed separately from those untrusted hints.

- AP069: [HA generation/replay](observations/shared-wave-exp-relative-cross-continuity-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-relative-cross-continuity-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-relative-cross-continuity-validation-v1.json).
  For independent denominators d,e and heads a0,b0, with d*y=e*x+g,
  construct common-scale tables and prove `b0*s<=a0*t` and
  `(d*e)*(a0*t)<=(d*e)*(b0*s)+g*(a0*t)`. All 1,344 integer models pass.
  This relative estimate has no argument-size restriction; an absolute
  majorant and positive rational interpretation remain separate obligations.

- AP070: [HA generation/replay](observations/shared-wave-exp-absolute-continuity-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-absolute-continuity-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-absolute-continuity-validation-v1.json).
  An actual bound `t<=C*b0` and budget `(r*g)*C<=d*e` turn AP069's
  relative error into `r*(a0*t)<=r*(b0*s)+a0*b0`, preserving monotonicity.
  The majorant is an explicit premise here, not an imported analytic fact.
  The [three-second Z3/E probes](observations/exp-absolute-continuity-solvers-v1.json)
  remain unresolved; Vampire is unavailable. Ordinary HA constructors prove
  the exact helper independently of those untrusted observations.

- AP071: [HA generation/replay](observations/shared-wave-exp-submultiplicative-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-submultiplicative-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-submultiplicative-validation-v1.json).
  Three actual recurrences at x,y,x+y through the same N satisfy
  `(a0*b0)*w<=c0*(u*v)`. Construct the actual Cauchy table via AP041,
  restrict its prefix, use AP039's recurrence/head identities and AP060's
  unrestricted value identity. No input upper bound or longer horizon is
  required. All 3,510 integer models pass, including zero heads.

- AP072: [HA generation/replay](observations/shared-wave-exp-integer-majorant-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-integer-majorant-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-integer-majorant-validation-v1.json).
  For an actual recurrence at L*d and actual `Pow(9,S L,C)`, prove
  `s<=C*h` independently of the finite horizon. One ordinary induction
  constructs positive factor tables at L*d and d and uses AP071. Only
  their positive head product is cancelled; the supplied head may be zero.
  All 648 integer models and 567 successor instances pass. The
  [bounded arithmetic probes](observations/exp-integer-majorant-solvers-v1.json)
  leave Z3/E unresolved; Vampire is unavailable. No solver output is trusted.

- AP073: [HA generation/replay](observations/shared-wave-exp-bounded-majorant-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-bounded-majorant-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-bounded-majorant-validation-v1.json).
  For every actual x<=L*d, construct a positive reference table at L*d,
  extract the actual natural gap and combine AP069 with AP072. Cancelling
  only the reference head yields `s<=9^(L+1)*h`, uniformly in N and
  independently of d. All 2,268 integer models pass; no new induction is used.

- AP074: [HA generation/replay](observations/shared-wave-exp-bounded-continuity-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-bounded-continuity-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-bounded-continuity-validation-v1.json).
  With both arguments bounded by L, symmetric cross-product error at most
  g, `Pow(9,S L,C)` and `(r*g)*C<=d*e`, prove both requested absolute
  error directions. The actual input order is split constructively, the
  extracted gap is bounded by g, and AP073 supplies AP070's majorant.
  All 4,000 integer models pass: 1,200 in each strict input order, 2,400
  with a zero head, and 1,440 with nonzero precision and nonzero input error.

- AP075: [HA generation/replay](observations/shared-wave-exp-dyadic-continuity-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-dyadic-continuity-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-dyadic-continuity-validation-v1.json).
  For actual r=2^n and p=2^m with `m=9*(L+1)+n+1`, construct the
  actual power C=9^(L+1). AP062 proves both dyadic scales nonzero and
  `2*(r*C)<=p`. The premise `p*g<=d*e` then discharges AP074's budget.
  Both output cross-product errors are at most a0*b0 after multiplication
  by r, for any common finite horizon. All 3,400 integer models pass;
  bounded examples use degree at most one to respect the 128-bit limit,
  while the HA certificate is universal in N. The
  [three-second solver probes](observations/exp-dyadic-continuity-solvers-v1.json)
  remain unresolved for Z3/E; Vampire is unavailable. Interpreting these
  finite cross-product bounds as rational errors still requires positive
  heads; connecting them to an analytic exponential remains separate.

- AP076: [HA generation/replay](observations/shared-wave-ordered-power-difference-v1/report.json),
  [fresh Lean](observations/shared-wave-ordered-power-difference-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-ordered-power-difference-validation-v1.json).
  From b=a+g, b<=M and actual powers u=a^(k+1), v=b^(k+1), w=M^k,
  prove `v<=u+(k+1)*(g*w)` by ordinary induction in k. Zero bases,
  M=0, g=0 and k=0 are included. All 840 actual-power models and more
  than 2,000 loose arithmetic-helper models pass. The
  [three-second arithmetic probes](observations/ordered-power-difference-solvers-v1.json)
  remain unresolved for Z3/E; Vampire is unavailable. The arithmetic helper
  has an ordinary HA proof; the solver logs have no proof authority.

- AP077: [HA generation/replay](observations/shared-wave-symmetric-power-difference-v1/report.json),
  [fresh Lean](observations/shared-wave-symmetric-power-difference-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-symmetric-power-difference-validation-v1.json).
  Constructive order splitting and actual natural gaps lift AP076 to both
  error directions for a,b<=M and both input gaps at most g. All 6,300
  integer models pass, including both strict orders and slack gap bounds.
  No new induction or definition is used.

- AP078: [HA generation/replay](observations/shared-wave-product-power-v1/report.json),
  [fresh Lean](observations/shared-wave-product-power-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-product-power-validation-v1.json).
  One ordinary induction proves `(a*b)^k=a^k*b^k` for supplied actual
  power values. Actual predecessor witnesses and power uniqueness identify
  every successor; the retained helper proves q=p*a from Pow(a,k,p) and
  Pow(a,S k,q). All 640 integer models pass, including 0^0=1.

- AP079: [HA generation/replay](observations/shared-wave-rational-power-difference-v1/report.json),
  [fresh Lean](observations/shared-wave-rational-power-difference-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-rational-power-difference-validation-v1.json).
  For d,e nonzero, a<=M*d, b<=M*e and both cross-product gaps at most g,
  retain actual u=a^(k+1), v=b^(k+1), D=d^(k+1), E=e^(k+1),
  C=M^k and Q=(d*e)^k. Prove D,E nonzero and both inequalities with
  allowance `(k+1)*(g*(C*Q))` between v*D and u*E. AP078 identifies the
  independently constructed crossed powers and AP077 supplies their errors.
  All 34,992 integer models pass, including unequal denominators and zero
  numerators. This root alone is finite rational error propagation; AP080
  supplies its requested-precision adapter. Analytic identification is separate.

- AP080: [HA generation/replay](observations/shared-wave-requested-power-precision-v1/report.json),
  [fresh Lean](observations/shared-wave-requested-power-precision-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-requested-power-precision-validation-v1.json).
  Retain AP079's two input bounds, symmetric crossed gap, positive d,e and
  five supplied powers u,v,D,E,C. Under `(r*(k+1))*(g*C)<=d*e`, construct
  Q=(d*e)^k and H=(d*e)^(k+1), and replay AP078's actual product and
  successor identities to identify `D*E=(d*e)*Q`. Both errors between v*D
  and u*E, multiplied by r, are at most D*E. D,E are proved nonzero;
  no cancellation or new induction is needed. The symbolic r can be zero;
  a caller supplies an actual dyadic power when that precision is needed.
  More than 40,000 bounded integer models pass, including positive gaps,
  unequal denominators and zero cases. The
  [three-second probes](observations/requested-power-precision-solvers-v1.json)
  include Z3 `unsat` for the exact arithmetic helper; E is unresolved and
  Vampire unavailable. A separate native HA constructor proves the helper;
  the Z3 proof-shaped output is not imported as HA authority.

- AP081: [HA generation/replay](observations/shared-wave-exp-joint-error-v1/report.json),
  [fresh Lean](observations/shared-wave-exp-joint-error-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-exp-joint-error-validation-v1.json).
  For 2*L<=K, coarse degree D=K+(L*K+n) and fine degree (D+1)+N,
  preserve independently supplied arguments, denominators, heads and tables.
  With AP075's dyadic input budget, construct the fine short sum and use
  AP075 on that actual prefix. AP063 controls its remaining tail. The
  coarse-minus-fine crossed error after scaling by r=2^n is at most a0*b0;
  the other error is at most 2*(a0*b0). Both dyadic powers are nonzero.
  More than 1,000 actual finite rational models pass, including both strict
  input orders, unequal denominators, positive tails and zero heads. The
  [three-second Z3/E probes](observations/exp-joint-error-solvers-v1.json)
  are unresolved; Vampire is unavailable. Both error budgets are preserved;
  no new induction, definition, analytic limit or fixed-program change is used.

- AP082: [HA generation/replay](observations/shared-wave-log-exp-refinement-v1/report.json),
  [fresh Lean](observations/shared-wave-log-exp-refinement-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-log-exp-refinement-validation-v1.json).
  Preserve actual logarithm lengths M=k+1 and M+l, independent coefficient
  scales, and exponential degrees m and m+1+N. Construct the ordered input
  gap and prove both argument denominators and all three supplied powers
  nonzero. The finite sums are monotone, with normalized error at most
  `27/p+2/P`, where p=3^M and P=2^m. The logarithm and exponential cutoffs
  are not silently identified. All 1,080 small actual-computation models
  pass, including independent scales and zero heads.

- AP083: [HA generation/replay](observations/shared-wave-log-exp-cutoff-refinement-v1/report.json),
  [fresh Lean](observations/shared-wave-log-exp-cutoff-refinement-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-log-exp-cutoff-refinement-validation-v1.json).
  At the existing auxiliary cutoff M=18*r+2, actual ternary predecessor
  extraction and binary/ternary growth prove `54*r<=3^M` and `4*r<=2^M`.
  These are conclusions, not added premises. Absorb AP082's two errors,
  cancel proved positive factors, and obtain `r*(a0*v)<=r*(b0*u)+a0*b0`,
  retaining monotonicity and all independent tables. Symbolic r=0 is allowed;
  its rational error reading requires positive r and heads. Numerical checks
  cover actual cutoff powers and arithmetic implications for positive r;
  the 27 complete exponential-table examples use r=0 to respect the 128-bit
  guard. The universal proof does not rely on these examples.

- AP084: [HA generation/replay](observations/shared-wave-log-exp-uniform-two-v2/report.json),
  [fresh Lean](observations/shared-wave-log-exp-uniform-two-lean-v1/report.json),
  [nine proof regressions and twenty protocol guards](observations/shared-wave-log-exp-uniform-two-validation-v1.json).
  For every n, construct r=2^n and the actual near-two reference before
  quantifying over arbitrary later logarithm/exponential tables. With
  M=18*r+2, their lengths are M+l and M+1+N. Every such table with positive
  coefficient scale satisfies `r*v<=(r*2)*b+2*b` and
  `(r*2)*b<=r*v+b`; the argument denominator is proved nonzero.
  For b>0 this reads `2-1/r<=v/b<=2+2/r`. No equality of codes, analytic
  limit or change of the original approximation program is assumed.
  The [first generation](observations/shared-wave-log-exp-uniform-two-v1/report.json)
  hit its 28-second CPU limit and is retained as not checked. One changed
  repair removed repeated syntax/source reconstruction, preserving the
  exact theorem, proof constructors, definition descriptors and full source
  closure: [cost audit](observations/log-exp-uniform-two-cost-audit-v1.json),
  [repair-equivalence audit](observations/log-exp-uniform-two-repair-audit-v1.json).
  Every ancestor body is still replayed. The repaired generation/replay use
  20.361823/19.181567 CPU seconds; the replay is close to its unchanged
  20-second ceiling, so further compositions need a cost audit first.

- AP085: [HA generation/replay](observations/shared-wave-fixed-log-exp-convergence-v1/report.json),
  [fresh Lean](observations/shared-wave-fixed-log-exp-convergence-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-fixed-log-exp-convergence-validation-v1.json).
  Choose r=2^n before arbitrary k and supplied tables. If 18*r+2<=k, their
  actual logarithm prefix has length 2*k+1 and the exponential degree is k+2.
  Prove the argument denominator positive and both bounds
  `r*y<=(r*2)*h+2*h` and `(r*2)*h<=r*y+h`. The cutoff-gap witness is extracted
  in HA; [Z3 confirms the frozen index identities](observations/fixed-log-exp-convergence-solvers-v1.json),
  separately from their native proof. E is unresolved and Vampire unavailable.
  AP020 has the same actual logarithm interface but is not a proof dependency.
  The [cost audit](observations/fixed-log-exp-convergence-constructor-cost-audit-v1.json)
  matches the checked bundle: 163 additional constructors. Generation/replay
  take 19.784548/18.887757 CPU seconds, fresh Lean 19.724626 wall seconds.

- AP086: [HA generation/replay](observations/shared-wave-fixed-log-exp-witness-v1/report.json),
  [fresh Lean](observations/shared-wave-fixed-log-exp-witness-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-fixed-log-exp-witness-validation-v1.json).
  Construct the actual coefficient, Horner, power, factorial and exponential
  tables for every such k. The head h is positive, satisfies
  `h=(k+2)!*(d*p)^(k+2)`, and normalizes every actual term: for j<=k+2,
  `(a*j!)*(d*p)^j=h*(3*x)^j`. Hence the bounds apply to actual positive
  samples, not only supplied premises. Six small subcomputations check 24
  term identities and 18 recurrences; these are not numerical models at
  the theorem's large threshold. The universal proof remains symbolic.
  No new arithmetic helper or solver call is needed. The
  [cost audit](observations/fixed-log-exp-witness-constructor-cost-audit-v1.json)
  matches the checked bytes: 1,319 additional retained constructors.
  Generation/replay take 20.771410/19.435420 CPU seconds, fresh Lean
  19.217983 wall seconds, all under the unchanged limits.

- AP087: [HA generation/replay](observations/shared-wave-half-log-exp-refinement-v1/report.json),
  [fresh Lean](observations/shared-wave-half-log-exp-refinement-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-half-log-exp-refinement-validation-v1.json).
  Preserve the original coefficient scales, logarithm prefixes, Horner values
  and powers p=3^M, q=3^(M+l). The actual exponential arguments are now
  `3*x/(2*d*p)` and `3*z/(2*e*q)`, at degrees m and m+1+N. Prove positivity
  of both doubled denominators, monotonicity `b0*u<=a0*v`, and finite error
  `27/p+2/P`, with the actual P=2^m retained. A scaled gap is constructed;
  the positive factor `(2*2)*(d*(e*q))` is proved nonzero before cancellation.
  No atanh-prefix assumption is transferred to a doubled coefficient scale.
  The [solver-first probes](observations/half-log-exp-refinement-solvers-v1.json)
  are inconclusive for Z3/E; Vampire is unavailable. The authenticated
  [pre-construction source](observations/half-log-exp-refinement-preconstruction-source-v1.py.gz)
  freezes all declarations before the native factories were added. All
  proof work is checked separately in HA. The combined constructor/test
  [first audit](observations/half-log-exp-refinement-constructor-cost-audit-v1.json)
  hit its 10-second CPU cap. Its one changed
  [constructor-only audit](observations/half-log-exp-refinement-constructor-cost-audit-v2.json)
  passed with unchanged proof code and limits; every test then passed under
  its normal separate budget. The exact bundle adds 677 constructors relative
  to AP082. Generation/replay take 12.810175/7.344228 CPU seconds and fresh
  Lean 11.843865 wall seconds. The 1,080 small actual models include independent
  scales, zero heads and equal logarithm lengths; they do not replace the proof.

- AP088: [HA generation/replay](observations/shared-wave-half-log-exp-cutoff-v1/report.json),
  [fresh Lean](observations/shared-wave-half-log-exp-cutoff-lean-v1/report.json),
  [eight proof regressions and twenty protocol guards](observations/shared-wave-half-log-exp-cutoff-validation-v1.json).
  At M=18*r+2, retain every AP087 computation and prove
  `r*(a0*v)<=r*(b0*u)+a0*b0`. AP083's archived budget and arithmetic bodies,
  and its unchanged native root constructor, are reused with the exact
  half-logarithm premise. Both power budgets are conclusions, not assumptions.
  The [statement/owner audit](observations/half-log-exp-cutoff-statement-archive-audit-v1.json)
  resolves all three exact endpoints; the
  [constructor audit](observations/half-log-exp-cutoff-constructor-cost-audit-v1.json)
  matches the checked bundle. No new arithmetic helper is needed.
  Generation/replay take 18.635869/10.420918 CPU seconds and fresh Lean
  11.983166 wall seconds. As for AP083, positive-r examples check only actual
  powers and budget arithmetic; the 27 complete half-exponential examples
  use r=0 to stay under the 128-bit guard. The theorem is universal in r.

- AP089: [HA generation/replay](observations/shared-wave-half-log-root-uniform-v3/report.json),
  [fresh Lean](observations/shared-wave-half-log-root-uniform-lean-v1/report.json),
  [thirteen focused regressions and twenty protocol guards](observations/shared-wave-half-log-root-uniform-validation-v2.json).
  For each n, choose actual r=2^n and DyadicSqrt2(n,r,s) before every later
  independent table. With M=18*r+2, an actual logarithm prefix at M+l and
  half-logarithm exponential at degree M+1+N satisfy
  `r*v<=s*b+8*b` and `s*b<=r*v+b`; their actual power and doubled argument
  denominator are proved nonzero. For b>0 the error is between -1/r and 8/r.
  The fine head may be zero in the arithmetic theorem. All 19 existing
  definition identities and dependencies are retained; no new definition,
  induction or axiom is added. This is a finite comparison, not yet an
  analytic identification of exp(log(2)/2) or the original root quotient.
  Generation/replay took 26.067345/24.615095 CPU seconds; the fresh nine-module
  Lean run took 23.250591 wall seconds. The owner-approved AP089-only replay
  allocation stays within the unchanged aggregate budget. The test-only
  repair and preserved earlier failures are detailed below.

All 1541 new-statement regressions passed at the historical AP089 checkpoint. Its 206 additional exact statements have successful
fresh Lean checks; each corresponding fresh-check run includes false-target and
forged-body rejection controls. The kernel and aggregate resource ceilings are unchanged;
CV085's phase redistribution and AP089's explicitly approved one-attempt replay
allocation are recorded below. Supervisors retain
their one-worker bounds. The AP019 handoff launched validation before its
successful fresh-Lean session was explicitly reaped; the plan records this
scheduling exception. Subsequent heavy launches require a terminal result.
The [AP047-AP050 consistency audit](observations/half-log-root-progress-audit-v2.json)
also confirms current producer/kernel pins and unchanged relevant controller
semantics against authenticated historical source snapshots. Its first,
over-strict whole-controller comparison is preserved separately. The
[new solver-target regression](observations/square-error-linear-observer-regression-v1.json)
checks AP048's exact binding and the no-proof-authority boundary.
The [AP051-AP055 consistency audit](observations/large-argument-tail-progress-audit-v1.json)
confirms exact targets, same-byte HA/Lean evidence, all five regression reports,
current producer/kernel pins and unchanged relevant controller semantics.
The [AP056-AP059 consistency audit](observations/normalized-exp-progress-audit-v1.json)
confirms exact targets, same-byte HA/Lean checks, all four regression reports,
current producer/kernel pins and unchanged relevant controller semantics.
The [AP060-AP064 consistency audit](observations/requested-exp-progress-audit-v1.json)
confirms exact targets, same-byte HA/Lean evidence, all five regression reports,
unchanged current proof/test sources and authenticated relevant controller semantics.
AP060 supplies the unrestricted value identity missing from AP005, and
AP061-AP064 supply independent-code product bounds and explicit requested-
precision cutoffs. AP065 now compares independently normalized tables at
different horizons. Its [consistency audit](observations/independent-horizon-progress-audit-v1.json)
checks the exact same-byte evidence and rechecks current proof sources and
relevant controller semantics for AP060-AP064. AP066-AP067 now construct
positive witnesses for every requested precision, with one coarse witness
uniform in all later finite horizons. AP068-AP069 supply unrestricted relative
continuity. Their [consistency audit](observations/positive-witness-relative-continuity-progress-audit-v1.json)
checks all four exact same-byte HA/Lean certificates, unchanged proof/test
sources and relevant controller semantics, and rechecks AP060-AP065's source
closures. No new definitions, axioms or inductions are introduced by these
four roots. AP070-AP075 now supply the uniform exponential-size majorant
and two-sided finite continuity with an explicit dyadic modulus. Their
[consistency audit](observations/bounded-exp-modulus-progress-audit-v1.json)
checks all six exact same-byte HA/Lean certificates and unchanged proof/test
sources, authenticates the relevant historical controller semantics, and
rechecks AP060-AP069. Only AP072 introduces a new ordinary induction; all
six reuse existing conservative definitions and introduce no new axiom.
AP076-AP079 now prove finite natural and independently normalized rational
power-error propagation. Their
[consistency audit](observations/power-error-progress-audit-v1.json) confirms
all four exact targets, same-byte HA/Lean certificates, current proof/test
sources and authenticated relevant controller semantics, and rechecks
AP070-AP075. Only AP076 and AP078 add ordinary inductions; no new axiom or
definition is introduced. AP080 now normalizes the rational power error to
requested precision, and AP081 combines independent exponential-input and
finite-tail errors. Their
[consistency audit](observations/precision-and-joint-error-progress-audit-v1.json)
checks both exact same-byte HA/Lean certificates, unchanged proof/test sources,
relevant controller semantics and exact solver-helper/source bindings, and
rechecks AP076-AP079. Neither adds a new induction, definition or axiom.
AP082-AP084 now connect actual logarithm refinements to exponential errors,
prove the required auxiliary cutoff budgets, and obtain uniform finite
near-two bounds over independent later tables. Their
[consistency audit](observations/log-exp-identification-progress-audit-v1.json)
confirms all three exact same-byte HA/Lean certificates, 25 focused tests,
the unchanged relevant controller semantics, and current source bindings.
It rechecks AP080-AP081 and authenticates AP084's metadata-only repair against
the failed run's source snapshot. Z3 discharges AP082/AP083's frozen arithmetic
helpers; their [probes](observations/log-exp-refinement-solvers-v1.json) and
[cutoff probes](observations/log-exp-cutoff-refinement-solvers-v1.json) remain
non-authoritative. AP084's [Z3/E probes](observations/log-exp-uniform-two-solvers-v1.json)
are unresolved; Vampire is unavailable in all three. Separate ordinary HA
constructors prove every helper. No new definition, axiom or induction is added.
The 15/15/13-definition closures retain existing identities and dependencies;
AP084 omits the two rational-order aliases unused by its immediate statements.
AP082's two contract-discovery failures (display metadata, then an unnecessary
source import) and AP084's unused first input snapshot, which omitted display
priorities, are retained. They are not successful proof evidence.
AP085-AP086 preserve the fixed logarithm schedule and construct positive
samples at every sufficiently late index. Their
[consistency audit](observations/fixed-log-exp-progress-audit-v1.json) verifies
both exact same-byte HA/Lean certificates, 16 focused tests, current source
bindings, constructor estimates and relevant controller semantics, and
rechecks AP082-AP084. Their 13/19-definition DAGs reuse existing identities;
neither adds a definition, axiom or induction. The exponential here takes
the full logarithm, not the original root quotient. The threshold
18*2^n+2 does not replace the fixed precision schedule n+8.
AP087-AP088 now supply the explicit half-logarithm transport that was missing
from AP082-AP083. Their [consistency audit](observations/half-log-refinement-progress-audit-v1.json)
checks both same-byte HA/Lean certificates, 16 focused tests, unchanged proof
sources, authenticated controller semantics, constructor-byte predictions
and the solver-first boundary. It also rechecks AP082-AP086. Both retain the
same 15-definition conservative DAG; no new definition, axiom or induction
is added. The uniform bridge to the actual dyadic-root witnesses is now
checked as AP089. Its earlier [dependency-size audit](observations/half-log-root-uniform-cone-cost-audit-v1.json)
finds 581 nodes and 64,560 constructors before the new bridge body or any
extra endpoints; it is not a replay or a runtime prediction. The subsequent
construction, failed attempts and successful acceptance are recorded below. Analytic identification,
interpolation and the final irrationality argument remain separate obligations.

AP089 is now **included in the local checked totals**. It chooses
an actual dyadic root r,s before all later independent half-logarithm tables
and targets `r*v<=s*b+8*b` and `s*b<=r*v+b`. The
[contract/input audit](observations/half-log-root-uniform-statement-input-audit-v1.json)
freezes the exact statement, 19 existing definitions and 352 inherited source
pins. Its [solver-first probes](observations/half-log-root-uniform-solvers-v1.json)
were inconclusive for Z3/E; Vampire was unavailable. Both new proof bodies
passed the [constructor check](observations/half-log-root-uniform-constructor-cost-audit-v1.json).
The [first full run](observations/shared-wave-half-log-root-uniform-v1/report.json)
completed generation, including its ordinary kernel check, in 23.767728 CPU
seconds, but fresh replay hit the 20-second CPU cap at 20.109661.

The one permitted changed repair uses two existing checked `Cut` nodes to
share the instantiated refinement and resulting bound pair. It reduces the
new root from 1,095 to 339 constructors, retaining the same theorem,
arithmetic helper and every ancestor row:
[repair audit](observations/half-log-root-uniform-cut-sharing-repair-audit-v1.json),
[repaired constructor check](observations/half-log-root-uniform-constructor-cost-audit-v2.json).
The [second full run](observations/shared-wave-half-log-root-uniform-v2/report.json)
completed generation in 23.629728 CPU seconds, but fresh replay again hit
the unchanged cap, at 20.110590. Its bundle contains 583 nodes / 65,490
constructors; no kernel or resource limit was changed. Whole-formula sharing
and unused-context inspections found no substantial safe reduction and are
retained as diagnostics, not proof evidence.

The [unaccepted-work audit](observations/half-log-root-uniform-unaccepted-progress-audit-v1.json)
authenticates both failures, byte-identical 582 non-root rows, the unchanged
root dependencies, and eight passing lightweight contract/input tests.
At that failed-v2 checkpoint, fresh HA replay, independent Lean and the two
full proof regressions were uncompleted. After the one-repair policy was exhausted,
the owner explicitly approved one additional AP089 attempt, `-v3`, with a
30-CPU/40-wall-second replay phase. Generation stays at 28 CPU / 40 wall;
the overall 60-CPU/90-wall-second budget, 768 MiB memory cap, one-worker rule
and certificate limits are unchanged. The implemented AP089-only allocation
reserves (28+1)+(30+1)=60 CPU seconds including hard-limit margins. The
approval does not cover another retry, other leaves, larger Lean/test limits
or kernel changes. The failed observations are retained; the approved run
required fresh HA, same-byte Lean and complete focused regressions before
acceptance. The [approval-scope audit](observations/half-log-root-uniform-approval-scope-audit-v1.json)
confirms that only AP089's replay allocation changed, not any proof source,
kernel rule, aggregate limit or other case's allocation.

The [approved v3](observations/shared-wave-half-log-root-uniform-v3/report.json)
passed full HA replay, and [fresh Lean](observations/shared-wave-half-log-root-uniform-lean-v1/report.json)
accepted exactly the same canonical bundle as repaired v2. The
[first validation run](observations/shared-wave-half-log-root-uniform-validation-v1.json)
is retained as failed: eight lightweight tests passed, then the combined
regeneration/replay test hit its unchanged 25-CPU-second cap at 25.199275.
The one changed test-only repair reconstructs both new native bodies and
compares their actual encodings with v3, then checks all 583 bodies using
the ordinary kernel in three disjoint test processes (195/194/194 rows).
Each process still performs complete canonical decoding and graph analysis;
the negative controls use the same authenticated bundle. No ancestor is
omitted, no positive receipt is fabricated, and full HA/Lean acceptance is
not replaced by the partitioned tests. All thirteen focused tests and twenty
protocol guards [pass](observations/shared-wave-half-log-root-uniform-validation-v2.json)
under unchanged limits. The three body batches use 12.159842, 9.754083 and
7.034540 CPU seconds, safely below 25; there was no further proof attempt.

The [final consistency audit](observations/half-log-root-uniform-progress-audit-v1.json)
binds the exact statement, actual HA/Lean bytes, constructor counts, all
regressions, current proof/kernel sources, unchanged definition DAG and
solver-first contract. It preserves both failed HA attempts and the failed
test run, verifies the test repair left the first eight tests unchanged,
and rechecks AP085-AP088's sources and relevant controller semantics. Counts
were then 206 additional / 239 distinct local statements and 1,541 focused
regressions. All workers were terminal-reaped. Public v5 remains 33; Alpha,
Stable and every IR parent remain unchanged. No promotion or deployment.
The subsequent documentation/syntax audit was interrupted by the supervisor's
one-second process-accounting timeout; its [manual incident record](observations/half-log-root-uniform-documentation-interruption-v1.json)
is not a validated worker receipt. A single unchanged-timeout
[read-only probe](observations/half-log-root-uniform-accounting-recovery-v1.json)
observed accounting available again in 0.0227675 seconds. No proof check was
replaced or invalidated, and no user application or resource guard was changed.

Historical AP090 preparation (superseded by WMI acceptance below): AP090 was
implemented but **not yet accepted or counted**. It aligns AP089 with
the fixed logarithm length 2*k+1 and exponential degree k+2 using the exact
AP085 index identities and AP007 gap witness, retaining the same root before
all later independent tables. The [statement/input preflight](observations/fixed-half-log-root-statement-input-audit-v1.json)
checks its previously planned AST and three actual archive owners. The
[native-body check](observations/fixed-half-log-root-native-constructor-audit-v1.json)
passes its ordinary closed curried goal with 99 constructors and depth 53;
this is not a complete dependency-closed theorem check. No definition,
induction or arithmetic helper is added. The owner approved one full run
with generation 28 CPU/40 wall and replay 30 CPU/40 wall seconds, within
60 CPU/90 wall aggregate, 768 MiB and one worker.

At that historical checkpoint the full attempt remained **unspent**. The combined preflight
[v1](observations/fixed-half-log-root-constructor-cost-audit-v1.json) lost
process accounting. After a [successful read-only recovery probe](observations/fixed-half-log-root-accounting-recovery-v1.json),
[v2](observations/fixed-half-log-root-constructor-cost-audit-v2.json) hit its
unchanged 15-second wall cap after 4.963220 CPU seconds. The changed repair
separates native-body checking from archive-size bookkeeping: the former
passed, but the [separate cost audit](observations/fixed-half-log-root-constructor-cost-audit-v3.json)
lost accounting again. These failures are retained; at that checkpoint heavy
verification was held for recovery, not bypassed. Thirteen AP090 tests and an AP089
controller-compatibility test repair are prepared but not yet validated;
no current-suite success is inferred from their existence. All accepted
proof counts and public releases remain unchanged.

### Initial WMI execution checkpoint, 2026-10-04 (historical)

Remote execution infrastructure is implemented: deterministic source archives,
one-CPU Slurm submission with a held-job ledger and no requeue, unchanged HA
worker limits in the initial pilot, Linux-capable fresh Lean checking, and hash-verified receipt
collection. This is compute migration, not website deployment or admission.

The approved pilot **257867** ran on WMI node `c5n1`. All nine initial migration
tests passed there. Its constructor preflight then stopped because the first
snapshot omitted a transitive Python library import, `finite_factorial_theorems`.
This was neither a timeout nor a mathematical rejection. Slurm reports
`FAILED`, exit `1:0`, elapsed 37 seconds. **AP090 generation/replay never
started**, so the one full proof attempt was then unspent. The
[pilot report](observations/wmi-ap090-pilot-v1/evidence/pilot-report.json) and
[hash-verified collection receipt](observations/wmi-ap090-pilot-v1/collection.json)
preserve all failed-run evidence and matching before/after source hashes.

The corrected package now includes the complete Peano Python runtime package.
Its [packaging receipt](observations/wmi-ap090-packaging-v2.json) binds archive
`b8ced94ece3cb8e398558797c502520d3d93f5694663b1655a7d699fea3b80bb`.
An [isolated import/statement check](observations/wmi-ap090-isolated-import-v2.json)
passes using only that extracted snapshot: 190 campaign modules, all 364
original AP090 input pins and all 19 definitions; no full catalogue import or
proof generation. [Eleven migration tests](observations/wmi-migration-tests-v4.json)
and [six existing Lean-intake tests](observations/wmi-fresh-lean-intake-validation-v1.json)
pass locally. These infrastructure checks are separate from the 1,541
focused proof regressions at the AP089 checkpoint.

At that checkpoint no replacement had been submitted, and the corrected archive
had not been uploaded. A new recorded request needed to preserve predecessor
257867 and its consumed ledger. HA/Lean checks, focused tests and the final
audit were still pending; WMI's Python environment also lacked pytest. The
subsequent owner approval and completed work are recorded next.

### WMI acceptance checkpoint, 2026-10-04

The owner explicitly approved using WMI's larger limits. The new hardware
profile requests one CPU, 4 GiB and a 45-minute outer Slurm envelope, with
120 CPU / 180 wall seconds and 2 GiB RSS per HA phase. Proof validity limits,
kernel rules, the original AP090 producer and all 19 definitions are unchanged.
Node-local scratch avoids repeatedly reading the source tree over the shared
filesystem. Jobs are held until their identity is recorded; no requeue or
automatic proof-generation retry is enabled. All earlier failures are retained.

Job **258959** passed the full constructor preflight, original HA generation
and fresh complete HA replay. Generation used **35.396 CPU seconds**; replay
used **33.938**, each about 245 MiB RSS. These observed CPU times exceed the
old Mac-oriented 28/30-second caps, so simply moving those caps to WMI would
not have solved the problem. The [HA report](observations/shared-wave-fixed-half-log-root-v1/report.json)
binds 585 DAG nodes, 65,644 constructors and a 3,868,304-byte certificate,
SHA-256 `603a7c00633d251a1f6b4476247eb6e48a8d13d47b47b4dbf75b5eab5747ef8c`.
All 583 AP089 rows are retained byte-for-byte. No new definition, induction,
arithmetic helper or axiom was introduced. The exact AP090 statement preserves
the chosen dyadic root before every later supplied fixed-schedule computation.

That job ended as failed only because the Lean version probe encountered the
Linux virtual-address limit. A Lean-only guard now separates a **16 GiB virtual
address cap** from the unchanged **2 GiB resident-memory limit**; this is not
a 16 GiB physical-memory allocation. The original HA guard and supervisor files
remain byte-for-byte unchanged. Lean uses a separately loaded instance of the
same supervisor, retaining CPU, sampled RSS, wall-time, output and process-group
cleanup checks. The executable is fixed and Lean is restricted to one thread.

Verification-only job **259148** reused the completed certificate without
regenerating it. Its [fresh Lean report](observations/shared-wave-fixed-half-log-root-lean-wmi-v2/report.json)
passes all nine fresh checker-module builds, the exact endpoint axiom audit,
same-byte acceptance, and both false-target/forged-body controls. The whole
Lean sequence used **14.166 CPU seconds**, 22.994 wall seconds; certificate
acceptance itself used 3.189 CPU seconds. Its Linux toolchain/library pins and
execution-guard sources are archived. [Downloaded evidence](observations/wmi-ap090-lean-followup-v1/collection.json)
matches the remote hashes. This does not claim that the Lean metatheory is
axiom-free: its previously documented exact axiom audit is preserved.

Regression job **259307** passed **13 AP089 + 13 AP090 tests** in 1 minute
43 seconds of scheduler time, using about 435 MiB peak RSS. It installed five
pinned pure-Python wheels offline into fresh node-local scratch, not the shared
Python environment. No proof was regenerated. The
[regression report](observations/wmi-ap090-regressions-v1/evidence/pilot-report.json)
binds the current test sources and includes both full test-process transcripts.
The [final consistency audit](observations/fixed-half-log-root-wmi-progress-audit-v1.json)
checks all downloaded hashes, exact HA/Lean identities, current proof/kernel
inputs, the preserved proof/definition DAGs, and both regression batches.
[Nineteen migration tests](observations/wmi-migration-tests-v8.json) and
[six Lean-intake tests](observations/wmi-fresh-lean-intake-validation-v3.json)
also pass; those are infrastructure checks, not additional proved theorems.

AP090 is therefore counted at this research checkpoint: **207 additional /
240 distinct checked statements; 1,554 focused proof regressions**. It proves
the finite fixed-schedule half-log/root comparison, not an analytic limit,
irrationality or transcendence. The next mathematical work is to connect that
comparison to actual positive-normalized witnesses and the finite-to-limit
identification of the original approximation program. Public v5 remains 33;
Alpha/Stable, website, and every IR parent remain unchanged. No commit,
promotion, push or deployment was performed in this compute-migration work.

#### AP091: accepted, evidence audited 2026-10-11

The next native proof constructs positive factorial-normalized half-logarithm
exponential samples on the fixed `2*k+1` / `k+2` schedule, all compared with
one dyadic root chosen before the later index. Its 13 witness outputs retain
the actual coefficient, Horner, power, weight, term, factorial and sum data;
the finite bounds are `r*y <= s*h+8*h` and `s*h <= r*y+h`. This is a support
lemma, not an irrationality or analytic-limit assertion.

The bounded metadata inspection found all eight prerequisites in AP090's
actual archive. Its candidate adds one node to the unchanged 585-row parent:
586 nodes / 66,081 constructors / 3,913,686 bytes. The 21-definition DAG reuses
only existing IDs and exact expansions; the two historical Le/Lt presentation
differences retain AP090's labels. The complete AP091 certificate has now
passed ordinary HA replay and fresh same-data Lean checking.

With the owner's explicit authorization, both WMI `cpu` and `cpu_idle` are
eligible, without increasing the one-CPU / 4 GiB Slurm allocation or the
per-process limits. Corrected preflight **268994** and full validation
**269156** both completed on `cpu`, with exit 0. The latter ran only after
the exact successful preflight. It passed full HA replay, fresh same-data
Lean, 13 new proof tests, 26 AP089/AP090 tests and 14 controller tests, plus
19 migration and seven routing tests. These reruns/infrastructure checks do
not count as additional proof regressions. The cancelled earlier preflight and its diagnostic are
[preserved](observations/wmi-ap091-preflight-v1/collection.json).

Full execution took 5 minutes 57 seconds. HA generation/replay used
55.008070 / 52.856511 CPU seconds; the fresh Lean sequence used 18.209128 CPU
and 29.013354 wall seconds. All 585 AP090 rows were retained exactly, with no
new definition, induction or axiom. The
[consistency audit](observations/fixed-half-log-root-witness-wmi-progress-audit-v1.json)
binds the [HA report](observations/shared-wave-fixed-half-log-root-witness-v1/report.json),
[Lean report](observations/shared-wave-fixed-half-log-root-witness-lean-wmi-v1/report.json)
and [downloaded evidence](observations/wmi-ap091-full-v1/collection.json).
Accepted counts are **208 additional / 241 distinct / 1,567 focused proof
regressions**. IR072 remains open. No promotion, commit or deployment.

#### AP092: accepted, evidence audited 2026-10-11

AP092 transfers these samples to every
supplied finer dyadic root at the same index n+l, retaining all positive
normalizations and finite errors -2/r and 8/r. It reuses SQ008/SQ009 and the
same 21-definition DAG. Its new arithmetic helper is reconstructed natively;
Z3 and E reached their bounded limits, and Vampire was unavailable. The
[solver observation](observations/fixed-half-log-fine-root-solvers-v1.json)
confers no proof authority. WMI job **284684** completed in 3 minutes
42 seconds. HA generation/replay used 37.284625 / 34.657140 CPU seconds;
fresh Lean used 14.272296 CPU / 25.040109 wall seconds. All 595 ordinary
bodies, both HA rejection controls, all nine fresh Lean modules, the exact
axiom audit, both Lean rejection controls, 13 new proof tests, 13 AP090
regressions, 14 controller tests and 19 migration tests passed.

The [evidence audit](observations/fixed-half-log-fine-root-wmi-progress-audit-v1.json)
binds the [HA report](observations/shared-wave-fixed-half-log-fine-root-v1/report.json),
[Lean report](observations/shared-wave-fixed-half-log-fine-root-lean-wmi-v1/report.json)
and [downloaded evidence](observations/wmi-ap092-full-v1/collection.json).
All 586 AP091 rows are preserved exactly. The certificate has 67,967
constructors / 4,000,332 bytes, with no new definition, induction or axiom.
Accepted totals are **209 additional / 242 distinct / 1,580 focused proof
regressions**. IR072 remains open; nothing was promoted or deployed.
The exact statement and next reciprocal-root/half-root bridge are in
[PLAN/32](../../../PLAN/32_sqrt2_power_irrationality_campaign.md).

#### AP093: accepted, evidence audited 2026-10-11

For every supplied original `NatSqrt2LogArgument` with positive coefficient
scale, set A=3*x and B=D*p for display. AP093 proves both argument
denominators positive, both arguments in [0,1], and

    0 <= (A*d)/(B*s) - (A*s)/(2*B*d) <= 2/d.

It retains the actual square-root and logarithm data. This is a finite
residual, not an exact equality. Its 69-node / 4,933-constructor / 189,044-byte
certificate reuses exactly 16 definitions, with no new induction or axiom.
WMI job **284690** completed in 1 minute 30 seconds. HA generation/replay
used 3.530134 / 1.696720 CPU seconds; fresh Lean used 5.603104 CPU /
7.215492 wall seconds. Thirteen new proof tests, 13 AP090 tests, 14 controller
tests and 19 migration tests passed, including every retained ordinary body
and both checkers' negative controls.

The [consistency audit](observations/log-root-half-argument-wmi-progress-audit-v1.json)
authenticates the [HA report](observations/shared-wave-log-root-half-argument-v1/report.json),
[fresh Lean report](observations/shared-wave-log-root-half-argument-lean-wmi-v1/report.json)
and [collected evidence](observations/wmi-ap093-full-v1/collection.json).
The later v2 audit also binds the unchanged AP093 case after adding AP094
dispatch. The [solver observation](observations/log-root-half-argument-solvers-v1.json)
provides no proof authority. Accepted totals: **210 additional / 243 distinct /
1,593 focused proof regressions**. IR072 remains open; no publication or admission.

#### AP094: accepted, evidence audited 2026-10-11

AP094 carries this residual through finite exponential continuity. It retains
the complete original sample, compares it with an independently normalized
half-root exponential at the same k+2 degree, and proves

    w0*z <= v*y
    d*(v*y) <= d*(w0*z) + 18*(w0*v).

Thus `0 <= y/w0-z/v <= 18/d`, with d, w0, v and both argument denominators
proved positive. The certificate has 214 nodes / 18,440 constructors /
817,481 bytes and retains every AP093 row. All 23 definitions are existing
exact identities; no induction, new axiom or analytic assumption is added.
Ordinary HA generation/replay used 14.474244 / 7.378637 CPU seconds; fresh
same-byte Lean used 6.257812 CPU / 8.850145 wall seconds.

Two infrastructure failures are preserved, not relabelled as successful jobs:
job **284694** passed HA/Lean but its pip test installer triggered the
unexpected-descendant guard. Test-only job **284696** used the same five pinned
pure-Python wheels, extracted without pip or child processes, and passed all
13 AP094, 13 AP093 and 13 AP090 proof tests. Its final controller batch found
an omitted historical RF001 fixture. The unchanged 14 controller tests then
[passed locally](observations/exp-log-root-half-transport-controller-v1.json)
in 0.512409 CPU seconds under the original 20-second CPU / 30-second wall /
768-MiB limit. The snapshot packager now includes that fixture for every case.
Eight wheel-staging safety tests and 19 migration tests also pass. No successful
certificate was regenerated and the guard was not weakened.

The [combined evidence audit](observations/exp-log-root-half-transport-wmi-progress-audit-v1.json)
binds the [HA report](observations/shared-wave-exp-log-root-half-transport-v1/report.json),
[fresh Lean report](observations/shared-wave-exp-log-root-half-transport-lean-wmi-v1/report.json),
both [full-run](observations/wmi-ap094-full-v1/collection.json) and
[test-only](observations/wmi-ap094-tests-v1/collection.json) collections,
unchanged original test sources and the local controller completion.
Accepted totals: **211 additional / 244 distinct / 1,606 focused proof regressions**.
IR072 is still open. At this checkpoint AP095 remained planned; the following
accepted result completes that requested-precision comparison. There is no
promotion, commit, push or deployment.

#### AP095: accepted, evidence audited 2026-10-11

For every complete original sample at k=n+8 and every independently normalized
half-root exponential table at the same degree (n+8)+2, AP095 constructs r=2^n,
proves r,d,w0,v positive, and establishes

    w0*z <= v*y
    r*(v*y) <= r*(w0*z) + w0*v.

Thus `0 <= y/w0-z/v <= 2^-n`. The actual supplied d is factored as r times
the constructed power 2^8. The proof replays AP015's existing arithmetic
body once, uses AP014's shift threshold and proves the tiny closed inequality
18 <= (9*3)+2 with the existing value-32-capped proof-producing evaluator.
No new external solver search, definition, axiom or induction is required.
All 23 conservative definitions and both independent table heads are retained.

WMI job **284698** completed successfully on cpu/c5n1, one CPU / 4 GiB, in
3m22s. The ordinary HA certificate has **231 nodes / 21,056 constructors /
969,777 bytes**, with the entire AP094 prefix unchanged. Generation and fresh
replay used 14.986556 and 7.743126 CPU seconds; fresh same-byte Lean used
6.489492 CPU / 9.154838 wall seconds, including both negative controls.
All 13 new proof tests, 26 predecessor proof tests, 14 controller tests,
19 migration tests and eight offline-staging safety tests passed. The earlier
[local selected-test precheck](observations/requested-half-transport-local-diagnostic-v1.json)
hit its unchanged 30-CPU-second ceiling; it is not recorded as a successful
test run. WMI used the established resource profile without weakening guards.

The [evidence audit](observations/requested-half-transport-wmi-progress-audit-v1.json)
binds the [HA report](observations/shared-wave-requested-half-transport-v1/report.json),
[fresh Lean report](observations/shared-wave-requested-half-transport-lean-wmi-v1/report.json),
exact current proof/test sources and [downloaded job evidence](observations/wmi-ap095-full-v1/collection.json).
Accepted totals: **212 additional / 245 distinct / 1,619 focused proof regressions**.
IR026/IR027/IR061 and the full IR072 remain open: this is a finite comparison,
not an analytic identity or the full approximation-accuracy theorem. Retain
AP094's 18/d estimate when allocating the remaining input and Taylor-tail
errors; do not spend the whole requested tolerance on each error separately.
No Alpha/Stable admission, commit, push or deployment was performed.

For subsequent work, size each cluster phase from measured CPU/RSS plus
headroom; do not carry laptop-sized time caps over blindly. Preserve the
ordinary full HA replay and same-byte fresh Lean checks. Parallelize only
independent tasks with matching Slurm allocations; allocating many CPUs to
this single-threaded dependent replay would not make it faster. Keep test
dependencies isolated and reserve the Mac for planning and lightweight checks.

The proposed final quantitative constants must
not silently treat `9^(L+1)` as a sharper exponential bound.
No IR parent is closed by these statements.
Proof workers use deterministic construction;
agent planning, implementation and review remain LLM engineering work, with
unmeasured token cost rather than an asserted zero cost.
After CV084 integration, the [controller and fresh-Lean protocol regression
run](observations/shared-wave-supplied-geometric-error-validation-v1.json)
also passed all 19 protocol tests (8 existing warnings), separately from that
file's seven CV084 tests. This is not a whole-repository
test-suite claim.

CV080's [first run](observations/shared-wave-same-table-composition-v1/report.json)
and [single proof-package repair](observations/shared-wave-same-table-composition-v2/report.json)
passed generation's ordinary HA check but hit the fresh replay's 20-second CPU
guard; both remain `not_checked`. The dossier records a one-leaf protocol-repair
exception before v3. Full positive bundle replay is unchanged. Its forged-root
negative control now checks that exact body against the same closed curried
goal in the ordinary kernel, without replaying all unchanged ancestors a second
time. [Protocol tests](observations/shared-wave-root-negative-control-protocol-validation-v1.json)
verify the exact goal, empty context and fail-open rejection. V3 passes within
the original caps; no kernel or positive-verification shortcut was introduced.
CV080 exports 26 downstream-needed witnesses, not all 47 intermediate values
from the initial candidate. Its exact accepted statement is separately pinned.

CV081's [first run](observations/shared-wave-supplied-composition-evaluation-v1/report.json)
was rejected because the Horner constructor package was used where its trace
projection was required. The single repair takes that projection, with the
same target; v2 and fresh Lean pass. CV082-CV084 passed their first attempts.

CV085's [v1](observations/shared-wave-constructed-composition-error-v1/report.json)
and [single structural repair v2](observations/shared-wave-constructed-composition-error-v2/report.json)
both remain `not_checked`: generation exceeded its 28-second CPU phase guard.
V2 produced complete output but took 28.140506 CPU seconds, so its zero exit
code did not override the resource rejection. The dossier records one explicit
protocol-only v3 retry, redistributing 28/28 CPU seconds to 30 generation / 26
fresh replay. The reservation including hard-limit margins remains 58<=60;
the 90-wall-second, 768-MiB and 8-MiB ceilings are unchanged. V3 used 28.187952
generation and 21.721790 replay CPU seconds. Its producer, target and proof
bodies are unchanged from v2; every retained ancestor is replayed. Fresh Lean
and all eight regressions also pass. The [phase and verification protocol
regressions](observations/shared-wave-composite-phase-redistribution-protocol-validation-v1.json)
pass all 20 tests (8 existing warnings). This is not a global retry allowance.

The [detached solver portfolio](observations/scaled-exp-tail-ratio-solvers-v1.json)
tested CV087's exact natural-arithmetic ratio helper before its HA run. Z3
returned `unsat` with a proof-shaped log; E reached its three-second CPU limit;
Vampire was unavailable on PATH. The observed portfolio used 3.102608 child
CPU seconds with 12/18 reserved CPU seconds. These logs confer no HA authority
and no solver proof was imported. The ordinary certificate explicitly
reconstructs order monotonicity and guarded cancellation, and fresh Lean checks
those same proof data. Three observer regressions verify this separation.

CV074's [initial regression run](observations/shared-wave-composition-majorant-validation-v1.json)
found a missing canonical trailing newline in the forged-bundle test fixture.
The fixture was corrected; the accepted producer and HA/Lean certificates
were unchanged. Regression v2 passes all seven tests within the existing caps.

CV057's first Lean invocation supplied a report file where its parent directory
was required. It stopped before certificate intake; the corrected fresh check
is v2, not a changed proof candidate.

Failed attempts are retained. CV058's [first attempt](observations/shared-wave-finite-power-evaluation-v1/report.json)
was rejected at its unit-value helper. A [bounded unchanged-body diagnostic](observations/finite-power-evaluation-v1-local-diagnostic-v1.json)
identified case analysis inside an inference-only equality chain. The single
repair introduced an explicit ordinary unit-head helper, with no changed
root theorem or kernel. HA v2, fresh Lean and all seven regressions passed.
The diagnostic does not check ancestor proofs or constitute proof authority.

CV047's [first attempt](observations/shared-wave-cauchy-grid-sums-v1/report.json)
stopped at the proof-authoring hygiene guard because a local witness reused
the dependency name `span`; no certificate was accepted. The single retry
renamed that local hypothesis to `span_witness`, without changing the target
or limits, and passed both checkers and the seven regressions.
CV051 had two rejected attempts: an incorrect disjunction-constructor call,
then a wrong axiom reference in unit uniqueness. A [bounded diagnostic](observations/power-width-transport-v2-local-diagnostic-v1.json)
identified successor injectivity being used instead of successor nonzero.
The plan records an explicit one-leaf exception to the default retry count,
made before the additional run. Its third attempt uses the actual archived
successor-nonzero body and passes HA, Lean and seven tests. The formula,
kernel and all resource ceilings stayed unchanged. Neither failed attempt
was sent to Lean or counted as accepted evidence.
CV048's [first attempt](observations/shared-wave-convolution-total-v1/report.json)
was rejected by the unchanged HA kernel at the local column-entry body. A
[bounded observational diagnostic](observations/convolution-total-v1-local-diagnostic-v2.json)
identified capture of the shared right-input sum by a column witness during
textual renaming. The corrected helper uses a distinct witness and has an
exact alpha-renaming regression. The root theorem and limits are unchanged;
the single retry passed HA, fresh Lean and eight regressions. The initial
diagnostic's display-call failure is also retained. A prematurely started
Lean run correctly refused the unsuccessful HA observation and produced no
accepted proof report; its staged sources are retained in the `-lean-v1` folder.
QF002's [first HA run](observations/shared-wave-quadratic-trace-exists-v1/report.json)
produced the same proof bytes, but [Lean preflight rejected its packaging](observations/shared-wave-quadratic-trace-exists-lean-v1/failure.json):
a redundant 19 MB parent archive exceeded the unchanged 16 MiB source-snapshot
cap. The successful run omits that redundant snapshot while authenticating
the parent archive before and after use and embedding every selected proof
body. The first run is not part of the published evidence index and has no
independent Lean success claim.

QH001's [generic-ring attempt](observations/shared-wave-quadratic-height-v1/report.json)
failed the unchanged local-row serialization preflight. Its single
changed-strategy retry uses shared arithmetic laws, deterministic additive
reassociation and distributivity, reducing the accepted whole bundle to
1,344 constructors. The two-second Z3 checks returned no successful answer;
they are not proof evidence or a demonstrated acceleration. No failed record
was deleted or overwritten.

QF004 adds local ND0396 `IQuadCanonicalStep` and ND0397
`IQuadCanonicalTrace`, with explicit definition-DAG edges to ND0390,
ND0394 and the existing strict-order alias. The old ND0392 balanced trace is
unchanged. The new definitions contain neither a height bound nor a nonzero
assumption. Zero factors and empty traces are included in the tests.

QH002 adds local ND0398 `IQuadHeightBound` and ND0399
`IQuadFactorHeightBound`. The latter is an explicit premise, separate from
canonical trace validity, and has no power or terminal-height clause. The
definition DAG includes the exact existing Le, Product, Repeat and Pow
templates. The proof replays the real power-zero and power-successor bodies,
not theorem names, and includes H=0 and L=0 without extra positivity premises.

QF005 now assembles actual power-existence, canonical-trace-existence,
height-bound and nonvanishing proofs into one witnessed bounded-product
theorem. Its internal forgetful bridge proves that the canonical trace satisfies
the unchanged balanced trace definition. QF002's looser balance-based trace
alone does not imply those bounds for every representation.

Next mathematical gate: the analytic critical path, beginning with finite-series
composition and interpolation. Remaining bridges include certified sqrt/log/exp
approximations and their identity, variable-multiplicity finite Hermite
interpolation with error/denominator bounds, and the positive finite precision
certificate for every rational competitor, together with quantitative real-norm
and moment bounds. None of these remaining bridges is silently discharged by
the eighteen new statements.

CV002 adds local ND0400 `NatExpAtanhRecurrence`: two initial entries and the
equation `(k+2)*f[k+2]=k*f[k]+2*f[k+1]`, restricted to the actual finite domain.
The solution is proved, not included in this definition. The induction carries
`k*f[k]=k*(2*D)` and cancels only the nonzero factor `k+2`; it includes D=0.
Its [first run](observations/shared-wave-logexp-recurrence-v1/report.json)
stopped on an incorrect constructor import before producing a certificate.
The corrected retry uses the existing `CongS` constructor; no kernel change
or enlarged limit was needed. The failure remains recorded.

CV003 adds ND0401 `NatConvolutionCoefficient` and ND0402
`NatConvolutionPrefix`, with explicit DAG edges to the unchanged actual
antidiagonal, sum, beta-decoding and order definitions. It constructs all
requested output coefficients by beta-prefix extension and actual finite
sums. There is no modulus and no assumed multiplication law. Empty inputs,
empty outputs, and zero padding are included. Uniqueness is extensional:
different numerical beta encodings need not be equal.

CV004 adds local ND0403–ND0407: unit coefficient, truncated unit prefix,
decoded power row, actual convolution step and full power trace. Two genuine
HA inductions construct the unit prefix and the sequence of rows. Width zero
and exponent zero are included; no zero-constant premise is needed for this
existence theorem. Its [first packaging attempt](observations/shared-wave-series-power-trace-v1/report.json)
was rejected because it retained unreachable convolution-uniqueness bodies.
The successful retry retains every reachable body with ordered dependency
remapping. The target, kernel and limits are unchanged.

CV005 adds local ND0408 `NatZeroBefore`, separate from the execution DAG.
It combines actual CV001, CV003 and CV004 bodies with one new induction to
prove that every row k has zero padded coefficients below k, assuming only
that the input vanishes below one. The root also constructs the whole trace;
none is supplied. Zero padding outside the truncation width is handled
explicitly. The statement without the zero-input premise would be false and
is covered by hostile tests.

CV006 adds local ND0409 `NatLinearTriple`, containing only a weighted relation
between decoded entries. One induction lifts it to actual finite sums; the
root constructs all three sum values. In notation, `gamma*c_i=alpha*a_i+beta*b_i`
implies `gamma*sum(c)=alpha*sum(a)+beta*sum(b)`. Zero weights and empty sums
need no special assumptions. The proof reuses deterministic four-atom additive
reassociation and actual distributivity bodies, not a ring or solver oracle.

CV007 adds local ND0410 `NatEulerPrefix`, whose only computation is multiplying
each coefficient by its index. The product rule is proved separately from the
actual antidiagonal witnesses and CV006's weighted-sum theorem. Both Euler
prefixes and all three coefficient sums are constructed; no input positivity,
nonempty length, or degree bound is assumed. A regression deliberately passes
free table codes named like the coefficient definition's internal witnesses,
checking exact hygienic expansion. This is the Euler operator, not yet the
shifted ordinary derivative, a power rule, or an analytic derivative theorem.

CV008 adds local ND0411–ND0413 for affine slices, their actual finite sums,
and tables of those sums. Four ordinary inductions construct slices and row
tables, handle zero-width rows, and prove finite Fubini interchange. The cell
is the actual source lookup at `(o+s*i)+t*j`; the swapped order uses the same
cells by proved addition laws. Repeated source indices, zero strides and empty
rectangles are included. No interchange equality occurs in the definitions.
This is a general finite-sum theorem, not yet natural convolution associativity.

CV009 proves general affine concatenation by one induction and specializes it
to actual ordinary prefix sums. The shifted tail is separately constructed,
not an unspecified remainder. CV010 uses this splitting law to prove finite
sum reversal by induction. Complementary antidiagonal indices then identify
the two actual convolution sums. Neither a prime modulus nor a nonempty-input
premise is required. Both statements reuse the existing conservative aliases
without new definitions and passed first-attempt HA, Lean and seven regressions
each. Commutativity is not associativity; the triangular-grid bridge remains.

CV011 now constructs the longer actual sum trace across an explicitly zero
tail, using CV009 and CV006 with zero weights. The nonzero-tail counterexample
is a regression; the zero premise cannot be dropped. No new induction or
definition is needed. CV012 constructs the finite triple-product grid: its
`(j,l)` cell is `A[j]*(B[k]*C[l])` when `j+(k+l)=i`, and zero for `j+l>i`.
Local ND0414–ND0417 describe cells, actual quotient/remainder coordinates,
flat beta prefixes and the resulting square grid. A separate index-bound proof
ensures every addressed cell lies inside the constructed prefix. The definitions
contain no row/column sum identity or associativity clause. The cell formulas
and future row/column identities are additionally tested on small natural
examples; those model tests are not formal evidence for the still-open sum bridge.

CV013 now proves the row-sum part of that bridge. Local ND0418
`NatTripleRowPrefix` asserts only that each decoded entry is an actual triple
cell. From `j+r=i`, the actual padded value `A[j]=a`, and that row computation,
the proof constructs t and s with `(C*B)[r]=t`, actual row sum s, and `s=a*t`.
Complement cancellation and padded-entry uniqueness identify each active term;
order contradiction handles the inactive case. It then applies actual weighted
linearity and zero-tail transport. No new induction is needed.

CV014 now completes cell transposition, affine row/column transport and natural
convolution associativity. It constructs both intermediate prefixes at width W
and a common value at every i<W. The actual conditional assembly body for
supplied prefixes is retained for power-trace reasoning. The width premise is
necessary: with A=[1,1], B=C=[1] and W=i=1, the two truncated nested products
have respective coefficients 0 and 1. All input lengths, including zero, are
allowed. Actual finite Fubini, row-sum and commutativity bodies establish the
identity; no algebraic identity is placed in a definition. Seven tests and
fresh HA/Lean replay passed on the first attempt, with no new induction.

These are general finite-series building blocks, not the completed exp/log
identity. CV015 now proves arbitrary weighted convolution linearity using
actual zero-extended coefficient matching and CV006 summation. CV016 constructs
the unit and proves its coefficient law from an actual first term and zero
tail. CV017 then proves the all-exponents Euler power rule by one ordinary
induction. Its root constructs the Euler input and the full power trace; its
conditional helper retains the exact trace, row decodings and width premises.
The input constant coefficient need not be zero. All three passed first-attempt
HA, fresh Lean and seven tests each, without new definitions or axioms.

In particular, CV002 does not assert that the exponential composition satisfies
its recurrence. Power differentiation is now checked, but finite composition,
rational common denominators and the three explicit composition-tail bounds
remain open. CV018 now constructs actual weighted prefixes. CV019 constructs
all rows of their finite accumulation by a second ordinary induction. New local
ND0419–ND0421 describe only a zero prefix, one weighted computation step and its
execution trace; they contain no sum formula or differentiation property. Both
passed first-attempt HA, fresh Lean and seven tests each. A source family of
actual powers can be supplied, but the weighted constructor does not silently
assume that arbitrary source rows are powers.

CV020 now constructs the shifted weights `(k+1)*w[k+1]`, using actual Euler
and affine-slice bodies and explicit index transport. Local ND0422 is only
the shifted multiplication computation; no derivative or chain-rule property
is assumed. First-attempt HA, fresh Lean and seven regressions passed, with no
new induction. CV021 now proves the finite chain rule relating those actual
accumulations. Its unconditional root constructs all five finite objects, with
16 code witnesses, and its single induction proves the identity for all
coefficients below H. Arbitrary natural weights and nonzero constant terms
are allowed. The proof includes actual stored-row transport, zero convolution,
the unit's Euler value, weighted step equations and CV017's power rule.
First-attempt HA, fresh Lean and seven regressions passed without new aliases
or axioms. The canonical bundle is 909,502 bytes, not an assumed chain-rule
name or an external reference.

CV022 now constructs denominator-cleared weights by their terminal-one
recurrence. Local ND0423 records that finite computation only; nonvanishing
for d!=0 is proved separately in the root. The induction scales the previous
prefix by `(N+1)*d` and appends 1, using actual beta extension. First-attempt
HA, fresh Lean and seven tests passed. CV030 below now proves the factorial
interpretation; d=0 is allowed for that equality but not for nonvanishing.

CV023 now proves the weight-scaling transport for every corresponding row of
two actual accumulation traces. CV024 combines that conditional helper with
CV021's constructed traces, CV022's adjacent weight equation and CV005's
vanishing theorem. It restricts the first trace from N+1 to N, removes the
degree-N power below degree N, and transports the resulting pointwise scalar
relation through actual convolution. Both passed first-attempt HA and fresh
Lean, with seven regressions each and no new aliases or axioms. The zero-input
premise is necessary: A=[1,1],d=1,N=2 gives C=[5,4], for which the claimed
equation at index 1 would read 4=5.

CV025 now constructs the inner finite odd-reciprocal coefficient table with a
positive common denominator, using actual division and common-multiple bodies
and one beta-extension induction. Local ND0424/ND0425 express only parity,
exact natural division and finite coding; they do not assert an analytic
logarithm identity. CV026 constructs its Euler table and proves its in-range
initial values and period two, using actual division uniqueness to separate
even and odd indices. Both passed first-attempt HA, fresh Lean and seven
regressions each. The definition DAG has explicit expansion checks and hygiene
tests; no Alpha admission is claimed.

CV027 now transports the period-two pattern through convolution by shifting
actual antidiagonal sum witnesses twice. CV028 combines this with the proved
Euler equation and nonzero-denominator cancellation to construct a composition
whose coefficients satisfy the three-term recurrence. CV029 proves its two
initial values: the constant term by an ordinary induction over the actual
weighted trace, the linear term by an explicit two-term convolution and Euler
equation. It then applies the actual CV002 body to identify every coefficient.
All three passed first-attempt HA, fresh Lean and seven regressions each, with
no new definitions or axioms. CV029's canonical bundle is 1,247,644 bytes.

This closes the finite natural coefficient-identification step, not the
analytic log-exp identity or an IR parent package. CV030 now proves the
factorial normalization `w[j]*j!*d^j=N!*d^N` from actual factorial and power
computations. Its generalized induction works for supplied weight tables.
CV031 applies that invariant to the very same witnesses constructed by CV029,
preserving their coefficient formulas, positive denominator and all computation
traces. Both passed first-attempt HA and fresh Lean; nine and seven regressions
passed respectively. No new definitions or axioms were introduced.

The bounded mixed-archive adapter authenticates the small Lucas archive and
existing wave archives, with explicit endpoint ownership. Every retained body
is replayed in the unchanged kernel; hashes and historical theorem names are
not authority. Tests reject a forged factorial ancestor as well as root forgeries.
The accepted older assemblers remain unchanged.

CV032 constructs integer Horner traces, with local conservative computation
aliases ND0426/ND0427 and explicit definition DAG/hygiene checks. CV033 proves
the integer geometric remainder identity from the all-coefficient pattern.
CV034 preserves CV031's actual witnesses and constructs the same table's Horner
value at 3. For N=K+2, it proves p=3^(K+1) relationally, r+z=(2z)*p and z*p
nonzero. Mathematically this is the finite value r/(z*p)=2-1/p; the exact
checked statement uses only natural arithmetic and actual computation traces.
All three passed first-attempt HA, fresh Lean and seven regressions each.

CV035 proves weighted Horner linearity for supplied coefficient relations,
constructing all three traces and values. CV036 proves the exact power scaling
under an actual zero coefficient tail. Both passed first-attempt HA, fresh Lean
and seven regressions without new definitions. Their conditional all-row
invariants are retained for application to supplied computation witnesses.

CV037 identifies the actual Horner value with an actual finite weighted sum,
given terminal-one geometric weights and a separate pointwise product prefix.
Its all-row invariant is h[k]*W[k]=sum(Q,k). It does not construct W or Q.
The local ND0428/ND0429 definitions record those two computation graphs only;
their DAGs, exact expansions and hygiene passed checks. First-attempt HA,
fresh Lean and seven regressions passed.

CV038 now constructs the geometric weights by scaling and appending one,
using actual CV022 bodies. A separate induction with actual power decomposition
proves W[j]*t^j=W[0], and identifies W[0] with the constructed t^N. Zero t is
allowed; no unconditional positivity claim is made. First-attempt HA, fresh
Lean and seven regressions passed, with no new definition.

CV039 constructs the weighted term prefix by beta extension and applies CV037
to the same witnesses. Thus the weights, actual power, term products, Horner
trace and common endpoint/sum value are now unconditionally constructed.
First-attempt HA, fresh Lean and seven regressions passed; no new definition.

CV040 identifies each weight with the actual complementary power when j+e=N,
and every actual term with a times that power when (j+1)+e=N. Its induction
uses actual power decomposition and explicit index equalities, not subtraction
or cancellation. All CV039 witnesses are preserved. First-attempt HA, fresh
Lean and seven regressions passed; no new definition was introduced.

CV041 now proves convolution weight multiplication, including the extra t
factor for output length L+M. The exact power-addition body from the Kummer
archive is retained and replayed in HA and Lean; a regression corrupts that
actual imported body and verifies rejection. CV042 transports this law through
actual zero-padded antidiagonals and their sums. Its five premises are the
three geometric tables and two pointwise weighted prefixes, not a coefficient
or evaluation equality. All coefficient indices and zero multipliers are allowed.
Both leaves passed first-attempt HA replay, fresh Lean and seven tests each.

CV043 now proves the shifted, scaled sum law with both zero margins explicit.
CV044 constructs the actual Cauchy grid; CV045 constructs the same grid and
identifies every row sum with its actual convolution coefficient. New aliases
ND0430-0434 describe cells, quotient/remainder coding and decoded rows only,
not the sum identities. All three leaves passed first-attempt HA replay,
fresh Lean and seven tests each.

CV046 proves the complete-column sum formula under its explicit length
equality, padded left value and actual column computation. The leading and
trailing zero regions are proved, not assumed. ND0435 describes decoded cells
only. First-attempt HA, fresh Lean and seven tests passed, including a finite
counterexample to dropping the complete-span requirement.

CV047 now assembles all length-L+M row and column sums on the same actual
grid and shares one right-input sum. Its storage width is N+1 while each
summation length is N=L+M. Outside left support every column is proved zero;
no invalid j+M<=N premise is used there. Empty inputs remain allowed.

CV048 now proves the full convolution product-of-sums identity, constructing
the actual output prefix and all three sum values. It replays CV008 finite
Fubini and proves the column tail zero before extending the shorter sum.
The output length is L+M, including when either input is empty.

CV049-CV052 now prove full Horner multiplication and cross-width transport
of actual powers and weighted accumulations. CV053 introduces local ND0436
`NatZeroAfter`, a separate upper-support property, and proves support addition
for actual convolution. CV054 proves the conservative power support 1+kL.
CV055 transports actual Horner histories across equal prefixes. CV056 combines
the actual full product with proved zero tails, giving support-complete
multiplication at shorter output lengths without cancelling a possibly zero
factor. All four new statements passed HA, fresh Lean and seven tests each.

CV057-CV058 now apply support-complete evaluation to supplied values and all
actual power rows. The latter retains the exponent-zero unit, explicit whole
support bound, relational power data and every scaling factor. CV059 adds
local conservative ND0437 `NatHornerValue` and ND0438 `NatRowHornerPrefix`:
actual trace and row-decoding graphs only. Its totality and extensionality
are proved separately; arbitrary input rows need not be powers.

CV060 now proves the actual weighted accumulation evaluates to the constructed
weighted sum. Local ND0439 `NatPointwiseProductPrefix` contains only decoded
entry multiplication, not a sum identity. CV061 applies this to the same
whole-support power trace from CV058, retaining the actual input value,
scaling powers, every row-value monomial law, accumulation and terminal sum.
Both passed first-attempt HA, fresh Lean and seven regressions each.

CV062-CV064 now prove exact Horner splitting, scaled comparison at arbitrary
ordered bases, and a finite integer tail majorant. At bases 2 and 3 the latter
is the denominator-cleared core of the `(2/3)^N` omitted-degree estimate.
It does not yet certify rational-denominator transport or bound the whole
composition. All three passed first-attempt HA, fresh Lean and seven tests.

CV065-CV066 prove the integer inner-polynomial majorant at base two. The
coefficient table, nonzero denominator, actual Horner value and power are
retained together; the arbitrary-supplied-prefix helper permits later reuse
with the same composition input. Local ND0440 is the separate coefficient
bound, not a correctness condition hidden in the Horner graph.

CV067 proves the actual-factorial lower bound `(k+2)!>=2*3^k`. CV068 proves
finite ratio-sum domination with the strengthened prefix invariant
`sum+r*last<=(r+1)*head`; its root covers empty sums and zero r. Local ND0441
contains only adjacent-entry inequalities, not a sum or convergence claim.
Both new definition DAGs depend only on Lt, BetaAt and Le, pass exact AST
roundtrips and collision checks, and are not library admissions. All four
statements passed their first HA attempt, fresh Lean and seven tests each.

CV069-CV070 now construct the actual factorial-weighted power terms and their
sum. Local ND0442 expresses only entry multiplication by an actual Pow value;
ND0443 expresses only the adjacent arithmetic recurrence. The same tables
satisfy `((j+1)*d)*T[j+1]=x*T[j]` and
`(T[j]*j!)*d^j=t0*x^j`, with every power/factorial graph explicit. Under d!=0,
the initial value t0 is proved nonzero. The denominator and argument are not
conflated; x=0 remains allowed. Both statements passed first-attempt HA,
fresh Lean and all seven regressions, with no new induction in CV070.

CV071 proves the finite integer bound `s<=9*t0` for the same constructed
terms when x<=2d, retaining every CV070 field. Its supplied-sum helper proves
the stronger prefix estimate `sum+2*last<=9*t0`, with zero/one horizons
handled separately and every order cancellation guarded by d!=0. It passed
first-attempt HA, independent fresh Lean and seven regressions, with one new
induction. No limit or rational-division theorem is included.

CV072-CV073 connect that recurrence to CV061's actual row values and products,
with denominator d*p, numerator t*x and initial value w0*v. CV074 constructs
the same actual atanh table, factorial weights, whole-support power rows,
accumulation rows, products and sum at base two. Its 27 witnesses and 37 fields
retain all CV061 computation fields and the explicit p=2^k*2 relation;
the sum is bounded by 9*(w0*v), with nonzero normalization w0*v.
All three statements pass HA, fresh Lean and seven regressions, without new
inductions or definitions.

CV075 transports the finite majorant into a valid rational bound for the actual
nonempty omitted tail at one third. Local ND0444 IRatLe abbreviates only valid
denominators and the natural cross-product order; its dependency DAG is
IRatValid plus Le, with no hidden estimate. CV076 applies this to every cutoff
M<=J of one actual constructed terminal row. CV077 preserves supplied input
and weight codes, allowing the older coefficient-pattern computation to supply
its exact weight table instead of assuming independently generated codes match.
CV078 needs source agreement only at k<K; CV079 uses that fact to transport
N+1 weighted terms from power traces of depths N and N+1. No unused small
power row, code equality or limit argument is assumed.

These five statements passed first-attempt HA and fresh Lean, with 37 passing
tests in total and only one new induction (CV078). Large negative replay
tests are isolated under the unchanged resource limits. ND0444 remains local
and unadmitted; the established website design and frozen public DAG are unchanged.

CV080 combines CV031, CV077 and CV079 on the same actual input and weight
codes. Its full terminal row has low coefficients z,2z,2z,... through N-1,
with N=K+2 and z=N!*d^N. That row's low-prefix Horner value r at base three
satisfies r+z=(2*z)*3^(N-1), with a nonzero normalization, while every in-range
tail retains its rational bound, including the cutoff N.

CV081 evaluates supplied power and accumulation traces at an arbitrary base,
without replacing either trace. CV082 splits supplied values across an actual
tail slice even when their Horner histories were independently constructed.
CV083 supplies the arithmetic combination: from r+z=2*z*p, y=b*r+u, h=p*b
and u*q<=9*a*(z*h), it proves
`y+z*b=(2*z)*h+u`, `y*q<=(2*q+9*a)*(z*h)` and
`(2*p)*(z*h)<=y*p+z*h`. These are natural inequalities; nonzero denominators
and actual power/evaluation instantiation are not silently assumed.

CV084 instantiates the splitting and sandwich laws on supplied actual
base-three values and tail witnesses. For N=k+1 and J=N+r it constructs
b=3^(r+1), proves h=p*b for p=3^k and h=3^J, and establishes every nonzero
rational denominator. With E=y/(z*3^J), its two exact rational comparisons
express `2<=E+3^(1-N)` and `E<=2+9*(2/3)^N`. The geometric prefix and tail
estimate are explicit premises, not hidden definition clauses. It passed
first-attempt HA, fresh Lean and seven regressions, with no new induction,
definition or axiom.

CV085 now closes that finite assembly: at N=K+2 it constructs the actual input,
factorial weights, row products and sum s with z=N!*d^N and v=3^((N+1)*N),
and proves both rational comparisons for E=s/(z*v). The monomial laws and
all-index factorial normalization refer to these same witnesses. Its checked
construction and evaluation helper stages avoid retaining obsolete histories;
there is no assumed coefficient pattern or tail estimate in the root theorem.

CV086 proves the sharper base-three inner bound, 3*y+3*d<=d*p, for supplied
atanh coefficients and p=3^(k+1). With the separately proved nonzero denominator
this places the normalized finite inner value in [0,1]. CV087-CV088 prove an
effective finite exponential remainder: for any supplied recurrence with
d nonzero and x<=d, the actual tail from m+1 has sum s and head a satisfying
2^m*a<=a0 and 2^m*s<=2*a0, uniformly in its extra finite horizon. This includes
zero argument and zero initial scale, without division or an infinite-sum claim.

CV089 proves the corresponding arbitrary-coefficient tail bound: y+D<=D*3^N
for every actual length-N base-three Horner value when all coefficients are
at most 2D. Unlike CV086, this does not require a zero head; it includes N=0
and D=0. It reuses CV086's actual checked step-bound body and adds one explicit
prefix induction. First-attempt HA, fresh Lean and seven proof regressions pass.

CV090-CV091 now prove that actual shared-prefix inner truncation difference:
3*x/(d*3^M)<=3*z/(d*3^(M+N))<=(3*x+3*d)/(d*3^M), with d nonzero
and every actual power and denominator validity witness retained. The finite
error is at most 3/3^M, including empty parts. Both first-attempt HA checks,
fresh Lean checks and fourteen proof regressions pass. A bounded
[arithmetic solver observation](observations/atanh-truncation-arithmetic-solvers-v1.json)
was inconclusive (Z3 unknown; E CPU limit); native HA reconstruction succeeded
without importing either solver's conclusion as authority.

CV092 now proves invariance under independently encoded common denominators:
the actual finite values satisfy e*x=d*y without equating their codes. The
certificate reuses the checked parity separation and all-row Horner linearity,
cancelling only a proved nonzero odd index. No new induction is needed. Its
[bounded solver observation](observations/atanh-scale-independence-solvers-v1.json)
reports Z3 unsat and E's CPU limit; only the independently reconstructed and
checked ordinary HA body provides authority.

CV093 now transports the rational truncation estimate across those independent
tables, preserving the supplied values and powers by checked uniqueness. Its
error bound remains 3/3^M, and every rational denominator is proved nonzero.

Next: prove finite exponential term and sum difference estimates;
combine finite exponential continuity and the uniform outer-tail estimate with
the constructed composition. Then give the explicit analytic interpretation
and certified approximation bounds. The finite arithmetic bounds alone are
not a logarithm or irrationality theorem.
The quantitative gate is recorded in the dossier.
No analytic limit, logarithm identity or irrationality parent is asserted.

## Research publication, 2026-10-01

The owner requested an update of the repositories and website. This checkpoint
publishes the planning DAG, conservative local definitions and exact supporting
evidence without promoting the unfinished campaign to Alpha. Alpha v35 stays
at **4,318 checked-use entries**; Stable stays at **432**. In particular,
neither a recorded check nor this website is a checked-use admission token.

The additive release is prepared by `scripts/stage_sqrt2_power_research.py`.
It authenticates the complete sealed v35 delivery inventory and the exact
campaign snapshot, preserves all existing theorem pages and shared assets,
and changes only the proof-library and grand-campaign navigation entrances.
The new campaign is served at `/proofs/sqrt2-power/`; its own combined atlas
adds two **open** goals to the frozen 120-goal parent. The current grand atlas
keeps its original data and links to this 122-goal research extension.

Publication status: **committed, pushed, deployed and publicly verified**.
This section supersedes the historical local-only status below.

- [Live campaign](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/sqrt2-power/)
- [Checked arithmetic DAG](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/sqrt2-power/arithmetic-frontier.html)
- [Conservative finite-trace definition DAG](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/sqrt2-power/quadratic-trace-definitions.html)
- [Combined 122-goal research atlas](https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/sqrt2-power/grand-campaign/index.html?view=family&focus=F13)

Source checkpoint: `0091a44a0cdd956c2dd216f27d078dd7284e8f3d`, pushed to
`nasqret/vietnam2026`, branch `release/jordan-v35-20260908`. No force-push or
history rewrite was used. `main` was not merged: that remains a milestone-owner
decision. The branch is outside the current GitHub Actions push filters; these
recorded local and remote checks are not a claim of a new full Actions run.

The [faculty-server activation audit](observations/research-publication-remote-activation-v1.json)
verified **14,063 registered public files** after publication. **13,796**
parent files remain byte-identical; only the two navigation entrances changed,
with private rollback copies retained. No remote files were deleted. All
[267 publication files passed exact public HTTPS comparison](observations/research-publication-https-v2.json),
and all **23 browser routes** passed both
[locally](observations/research-publication-browser-local-v1.json) and
[on production](observations/research-publication-browser-remote-v1.json).
Production theorem and definition screenshots were visually inspected; the
constructive-proof-explorer skill preserved the Quadratic Reciprocity shell
and the distinction between proof, notation and planned edges.

The [first HTTPS audit](observations/research-publication-https-v1.json) stopped
on the local Python client's certificate-trust error. The successful audit uses
the macOS system TLS client, normal certificate verification, HTTPS-only
requests, no redirects, and `--disable` to ignore ambient curl configuration.
No insecure certificate bypass was used. Its
[20 additional verification-client tests](observations/research-publication-https-client-tests-v1.json)
also pass, including certificate-failure and altered-byte rejection controls.
Neither Peano production nor its preview, the Lean companion, the Alpha
catalogue, or Stable was modified by this research publication.

Release preflight: [72 publication/DAG/evidence test executions](observations/research-publication-regressions-v4.json)
and [145 supervisor tests](observations/research-runtime-controller-validation-v1.json)
passed. The [bounded stage audit](observations/research-publication-stage-v1.json)
authenticated all 13,798 registered parent files and produced a 267-file
additive payload, preserving 13,796 parent files exactly. Its
[delivery manifest](observations/research-publication-manifest-v1.json) is
metadata only, never proof authority.

QN001 and QF001 were regenerated and freshly HA-checked again, producing the
exact same certificate hashes as the frozen checkpoint. The
[independent Lean checker was freshly compiled and accepted both exact bundles](observations/research-publication-fresh-lean-v1/report.json),
including successful false-target and forged-body rejection controls.
This does not increase the 33-statement count or enter ordinary checked use.

Three stopped preflight records are retained: a new absent-marker test fixture
accidentally contained its marker ([v1](observations/research-publication-regressions-v1.json));
legacy smoke workers requested the production 30-second default inside a
25-second test guard ([v2](observations/research-publication-regressions-v2.json));
and the proof-leaf harness correctly rejected the supervisor suite's intentional
process-accounting child ([v3](observations/research-publication-regressions-v3.json)).
The fixture was corrected, smoke reservations reduced, and supervisor tests
run as a separately bounded controller. All original assertions and proof-worker
restrictions remain intact; no proof, resource ceiling or kernel rule was relaxed.
An initial sandbox invocation could not run `/bin/ps`; explicit permission for
process accounting was obtained rather than disabling the memory guard.

## Quadratic product extension, 2026-10-01

The wave now has **33 distinct exact HA/Lean-checked supporting statements**.
The full positive irrationality theorem IR072 remains open.

| Lemma | Exact scope | Bundle nodes / ordinary proof nodes |
| --- | --- | --- |
| QN001 | Two nonzero signed quadratic integers have a nonzero product, with arbitrary input and output representatives. | 221 / 81,273 |
| QF001 | A supplied finite β-table product trace beginning at one has a nonzero terminal value when every decoded factor is nonzero. | 224 / 81,603 |

QN001 reuses complete SN001/SN003/SI001 proof bodies with lossless sharing;
59 duplicate rows are shared, and the parent generators are not rerun. QF001
adds actual HA induction and exact β-decoding uniqueness. Neither a source
hash, solver answer nor previous receipt is a mathematical premise. The work
uses agent-designed decomposition and deterministic ordinary proof assembly
and checking, not a claim of solver-discovered universal induction.

Both passed their first generation and fresh HA replay in a combined 11.17
seconds. Fresh compilation of the nine-module independent Lean checker and
same-byte checks, including false-target/forged-body rejections, took 14.51
seconds. Timings exclude planning, implementation and regression testing.
The largest proof process peaked at 441,991,168 bytes; no limits were raised.

- [QN001 ordinary HA observation](observations/shared-wave-quadratic-nonzero-v1/report.json)
- [QF001 ordinary HA observation](observations/shared-wave-quadratic-product-trace-v1/report.json)
- [Fresh independent Lean checks](observations/fresh-lean-quadratic-products-v1/report.json)
- [Exact v5 evidence index](observations/shared-wave-index-v5.json)
- [Finite trace definition DAG](../../../book/_static/constructive-sqrt2-power-campaign/quadratic-trace-definitions.html)

Four conservative local definitions ND0390–ND0393 separate actual execution
from the nonzero-factor assumption. The constructive-proof-explorer template
keeps the established Quadratic Reciprocity presentation, exact named statements,
and separately typed proof/definition/planning edges. The new actual proof
dependencies are SN001/SN003/SI001 → QN001 → QF001. All historical evidence
is retained: 42 attempts, eleven fresh-Lean reports and eight earlier failures.

Validation finished with **134 passing test executions**: [QN001](observations/shared-wave-quadratic-nonzero-validation-v1.json)
(20), [QF001](observations/shared-wave-quadratic-trace-validation-v2.json) (18),
[controller/evidence/Lean-intake guards](observations/shared-wave-quadratic-controller-validation-v1.json)
(46), and [presentation, DAG and site regressions](observations/shared-wave-quadratic-products-presentation-v2.json)
(50). The largest successful test process used 522,141,696 bytes, below the
unchanged 512 MiB ceiling. All [264 generated files match an independent
bounded rebuild](observations/shared-wave-quadratic-products-site-build-v1.json),
and all [23 browser routes passed](observations/shared-wave-quadratic-products-browser-v1.json)
in 25.54 seconds. New theorem/definition pages and the checked arithmetic map
were visually inspected with disposable browser profiles.

Two stopped regression attempts remain archived: an [expanded archive-case
batch reached its 25-second CPU guard](observations/shared-wave-quadratic-products-presentation-v1.json),
and an [ancestor-preservation test reached its 512 MiB RSS guard](observations/shared-wave-quadratic-trace-validation-v1.json)
while retaining two expanded archive copies. Isolating archive parameters and
retaining exact compact row bytes before proof reconstruction repaired the
test scheduling/storage. No assertion, resource ceiling, producer or kernel
rule was weakened; neither stop was a failed universal proof.

**Next:** construct finite product traces for arbitrary factor tables using
actual β-prefix extension, then extract a terminal witness and combine with
QF001. Trace totality is not a premise smuggled into a definition and is not
yet proved. Rational interpretation, conjugate-height bounds, moment-polynomial
identities and the analytic bridges remain open. This extension does not close
IR046 or IR072. All changes are local; no commit, promotion, push or deployment.

## Rational norm extension, 2026-09-30 (historical checkpoint)

Three new universal supporting lemmas passed fresh ordinary HA replay and the
independently freshly compiled Lean checker. That checkpoint contained **31
distinct checked statements**, not a completed irrationality proof.

| Lemma | Exact scope | Bundle nodes / ordinary proof nodes |
| --- | --- | --- |
| RN001 | Equal rational quadratic coordinates give equal rational norms, with arbitrary signed representatives and nonzero denominators. | 29 / 2,630 |
| RN002 | The norm of a quadratic product satisfies the existing rational multiplication relation, with output denominator `(u*v)*(u*v)`. | 46 / 42,483 |
| SI001 | Nonzero signed integers have a nonzero binary product, including arbitrary output representatives. | 34 / 2,400 |

RN001 reuses actual signed-square scaling, representative transport and
uniqueness bodies. RN002 includes the complete SN003 certificate and explicit
semiring-law transport; it does not silently replace the squared denominator
by `u*v`. SI001 uses actual square-existence and natural no-zero-divisor proofs.
All new proof construction is deterministic ordinary-inference composition;
agent work planned the decomposition and implementation. No new definition,
kernel change, solver axiom or global-registry mutation was introduced.

Z3 independently returned `unsat` for each exact negated conjecture. These logs
are cross-checks, not trusted HA proof imports. Generation, solver checks and
fresh HA replay took 11.17 seconds in total across three sequential bounded
observations; the fresh nine-module Lean compilation/check wave took 12.13
seconds. These timings exclude agent planning, engineering and regression tests.
The largest proof producer peaked at 508,788,736 bytes, below the unchanged
768 MiB proof ceiling. No resource cap was raised.

- [RN001 exact HA/Z3 observation](observations/shared-wave-rational-norm-transport-v1/report.json)
- [RN002 exact HA/Z3 observation](observations/shared-wave-rational-norm-product-v1/report.json)
- [SI001 exact HA/Z3 observation](observations/shared-wave-signed-product-nonzero-v1/report.json)
- [Independent Lean wave, including rejection controls](observations/fresh-lean-rational-norm-wave-v1/report.json)
- [RN001 hostile-input tests](observations/shared-wave-rational-norm-transport-validation-v1.json)
- [RN002 hostile-input tests](observations/shared-wave-rational-norm-product-validation-v1.json)
- [SI001 hostile-input tests](observations/shared-wave-signed-product-nonzero-validation-v1.json)

The [v4 evidence index](observations/shared-wave-index-v4.json) pins 40 attempts
and ten fresh-Lean reports; all eight historical failed attempts are retained.
The established Quadratic Reciprocity presentation and conservative definition
DAG are preserved. The checked DAG adds the actual SN003 → RN002 dependency;
links to IR031/IR046 remain explicitly planned support, not parent closure.

Final validation records **133 passing test executions**: the three proof suites
linked above (40), [exact presentation/controller regressions](observations/shared-wave-rational-norm-presentation-v3.json)
(28), and [site/evidence-reader/Lean-intake regressions](observations/shared-wave-rational-norm-site-regressions-v2.json)
(65). These are test executions, not additional theorem counts. All **255
generated local files** match the [separate bounded build and byte check](observations/shared-wave-rational-norm-site-build-v2.json).
All [20 browser routes passed](observations/shared-wave-rational-norm-browser-v1.json)
in 22.18 seconds; the new rational theorem pages and full checked DAG were
visually inspected using disposable profiles.

The first expanded presentation batch hit its [25-second CPU guard](observations/shared-wave-rational-norm-presentation-v1.json),
and the in-process double-build test hit its [512 MiB RSS guard](observations/shared-wave-rational-norm-site-regressions-v1.json).
Both stopped records remain intact. Smaller presentation batches and one fresh
regeneration compared byte-for-byte against the separately built disk snapshot
passed without raising any ceiling. The largest successful test process peaked
at 522,616,832 bytes. An [initial site build](observations/shared-wave-rational-norm-site-build-v1.json)
also rejected the new definition users until its explicit allowlist and hostile
regression tests were extended; this was a presentation integration issue,
not a failed mathematical proof. No worker was left running.

**IR072 remains open.** Next: lift SI001 through SN001/SN003 to quadratic binary
nonvanishing and then actual finite-product traces; prove conjugate-height
bounds and combine them with integer norm separation for the rational lower
bound; continue coefficientwise rational-series and analytic remainder bridges.
No commit, Alpha promotion, push, or deployment occurred in this extension.

## Universal arithmetic extension, 2026-09-19 (historical checkpoint)

Four more universal statements now pass **fresh ordinary HA and independently
compiled Lean**, bringing the wave to **28 distinct checked statements**:

- NG001: a constructive positive gap between unequal naturals (3 bundle
  nodes / 192 ordinary proof nodes). Z3 independently confirmed the same target.
- SN002: witnessed integer norm separation for arbitrary nonzero signed
  coefficient pairs (210 / 40,625).
- SN003: norm multiplicativity in Z[√2], with arbitrary signed output
  representatives and all eight premises explicit (37 / 41,346).
- CV001: universal vanishing of an actually executed natural antidiagonal
  convolution below the sum of the input vanishing orders (28 / 1,400).

The [quadratic arithmetic review](quadratic-arithmetic-review.md) records the
first three exact decompositions. Two local aliases, ND0388/ND0389, abbreviate
separate quadratic-product component equations; they do not hide a norm law.
CV001 reuses eight existing definition identities and argument orders.
Its [proof and annotation-repair review](convolution-review.md) records the
exact universal statement and the remaining coefficient-order bridge.
The small [checked DAG](../../../book/_static/constructive-sqrt2-power-campaign/arithmetic-frontier.html)
extracts solid edges from actual root dependencies. Dashed planning support
does not close a parent. Named theorem pages and larger parent pages link in
both directions, using the established Quadratic Reciprocity presentation.

CV001's first two failed attempts remain visible. A
[versioned diagnostic](observations/shared-wave-convolution-diagnostic-v1.json)
observed the unchanged checker rejecting an elimination-headed equality after
local-cut compilation had erased its synthesis annotation. The corrected
producer preserves the eleven actual local lemmas with ordinary typed identity
Cuts; every lemma body is still checked, and no kernel or global engine source
was changed. The [same original target then passed HA](observations/shared-wave-convolution-vanishing-v3/report.json)
in 1.70 seconds (91 MB peak), and
[fresh Lean](observations/fresh-lean-convolution-vanishing-v1/report.json)
in 9.70 seconds. Failed-attempt records are not retroactively relabeled.

**IR072 remains open.** SN002 supplies the integer-discreteness component of
IR032, not its real-algebraic lower bound. SN003 does not yet supply the
rational-denominator version of IR031. CV001 is an arbitrary natural-index
convolution theorem, not ascending rational power-table execution, formal
exp/log composition, or an analytic remainder estimate. The next work is
denominator/conjugate-height transport and coefficientwise series execution.
All execution remains single-worker and capped; agent planning/engineering
cost is unmeasured, not zero. No commit, promotion, push or deployment occurred.

The extension's final bounded suites record **158 passing test executions**
(including rechecks of existing security tests, not 158 new theorems):
[separation](observations/shared-wave-norm-separation-validation-v1.json),
[norm product](observations/shared-wave-norm-product-validation-v1.json),
[convolution](observations/shared-wave-convolution-validation-v1.json),
[controller bindings](observations/shared-wave-arithmetic-presentation-v2.json),
[reader/Lean-intake regressions](observations/shared-wave-reader-lean-regressions-v3.json),
and [final exact-presentation/page/link/DAG/determinism regressions](observations/shared-wave-final-presentation-v3.json).
All **245 generated local files** match the
[final fresh bounded build and independent byte comparison](observations/shared-wave-final-site-build-v3.json).
The [final browser smoke](observations/shared-wave-final-browser-v3.json)
passed all **17 routes** in 27.97 seconds, including the checked-proof DAG and
the clickable eight-definition convolution DAG. The final convolution DAG
screenshot was visually inspected; disposable browser process groups were
cleaned up without touching the user's browser profile. Browser validation is
presentation evidence only, not proof authority.
The largest focused test process peaked at 532,414,464 bytes, below the
unchanged 512 MiB test ceiling; no resource limit was increased.

## Shared-proof wave, 2026-09-19

The per-operation proof DAG now proves the **original exact P10 statement**
within the unchanged arithmetic/size limits: 1,486 local nodes, 19,539 ordinary
proof-body nodes. Generation and fresh HA replay took 6.85 seconds, with a
306 MB measured peak. A freshly compiled nine-module Lean checker independently
accepted the same bytes. The earlier failed adapter and its failure records
remain unchanged; its strict expected-failure test is not used as P10 evidence.

Six named rational-equivalence facts pass both HA and independent Lean:
reflexivity, symmetry, transitivity, nonzero scaling, numerator-pair shifts,
and negation compatibility. Their six local `IRat` definition templates use
capture-safe conservative expansion and do not mutate the global registry.

Live E and Vampire logs each select `mul_assoc` and `mul_comm` for the exact
P08 supporting statement. This now drives a narrow native reconstruction, not
the old full-ring fallback. It is **premise-guided reconstruction, not TSTP
proof-log translation**. Z3 separately checks the six rational conjectures.

The fixed degree-seven composition has a checked universal trace-soundness
lemma and **13/16 exact trace chunks** checked in both HA and fresh Lean.
The final three chunks hit the canonical payload cap. Neither the whole trace
nor the variable-degree IR079–081 claims is complete. Both full-trace attempts
are preserved; no limit was silently increased.

The natural twice-square statement `a*a=2*b*b -> a=0 /\ b=0` also passes
fresh HA and independent Lean. Its 182-node bundle includes the entire
180-node ancestor cone of the existing Fermat-four theorem. This supplies
the natural-number core needed by IR016/norm separation.

SN001 now extends the zero-norm criterion to **arbitrary signed-pair integer
coefficients**: `(ap-an)^2=2*(bp-bn)^2 -> ap=an and bp=bn`, with explicit natural
square witnesses. It reuses unchanged ND0157 `SignedDifferenceSquare`, plus
22 actual v28 proof nodes and the complete IR016 bundle. The final 206-node,
40,402-body-node proof passed fresh HA in 5.08 seconds and independently
compiled Lean in 11.08 seconds, including logical negative controls. No claim
that all four raw components vanish is made. See the
[reviewed decomposition and scope](signed-norm-review.md).
The rational/real quantitative norm bounds, denominator/analytic bridges and
IR072 remain open; integer separation and multiplicativity were added above.

The [September 19 v3 wave index](observations/shared-wave-index-v3.json) pins
37 proof attempts and nine fresh-Lean observations: 28 distinct statements
checked in both HA and fresh Lean, with eight failed attempts retained.
The [previous v2 index](observations/shared-wave-index-v2.json) preserves
31 attempts and six fresh-Lean observations. After deduplication of
the E/V P08 demonstrations, that checkpoint contained 24 distinct HA/Lean-checked
statements: six named rational foundations, the twice-square natural core,
the signed zero-norm bridge, P10, two supporting lemmas, and thirteen composition
pieces. These categories must not be presented as 24 major irrationality
milestones. The [previous v1 index](observations/shared-wave-index-v1.json)
remains unchanged.

New regression validation passed **188 tests and 138 subtests**, in fresh
bounded batches. A combined reader/proof-test process had previously reached
the 512 MiB RSS guard and was stopped; splitting test lifetimes reduced the
largest batch peak to 424 MB. No unchanged oversized batch was retried.

The existing regression modules were then rerun in bounded fresh processes:
**165 tests and 131 subtests passed**, with the old P10 adapter's one strict
expected failure preserved. Combined with the new tests, that is 353 passing
tests and 269 subtests, not 353 proof certificates. The 216 generated local
files match a fresh deterministic build. All nine browser routes passed in
disposable Chrome profiles, including the definition DAG, named transitivity
theorem, planning cones and grand atlas; the screenshots were inspected.
The user's normal browser profile and the production website were untouched.

Validation records: [new proof/infrastructure tests](observations/shared-wave-validation-v1.json),
[existing regressions](observations/shared-wave-baseline-regressions-v1.json),
[deterministic site build](observations/shared-wave-site-validation-v1.json),
[new evidence pages](observations/shared-wave-browser-v1.json), and
[planning-map navigation](observations/shared-wave-map-browser-v1.json).

The signed-norm extension adds 21 proof/hostile-case tests and four exact
archive/presentation tests; all passed. The shared reader, protocol and Lean
intake were rechecked in the same run: [70 passing checks](observations/shared-wave-signed-norm-validation-v2.json).
Across the three suites this is **378 distinct passing tests and 269 subtests**,
plus the preserved expected failure of the old P10 adapter. That checkpoint's
222-file site passed [fresh build/check](observations/shared-wave-site-validation-v2.json),
[page/link/DAG regressions](observations/shared-wave-final-site-regressions-v2.json),
and [all ten isolated browser routes](observations/shared-wave-browser-v2.json).
The new signed-theorem and updated definition-network pages were visually inspected in
the established Quadratic Reciprocity design. An earlier combined
signed-norm test process reached its 512 MiB guard; its [stopped record](observations/shared-wave-signed-norm-validation-v1.json)
is preserved. Separate archive-heavy test processes reduced the peak to 453 MB,
with no cap increase. The signed-norm proof producer and fresh replay succeeded
on their first run under the original 768 MiB proof-worker envelope.

The Lean intake now checks case/schema/source agreement across both original
processes, rebinds the exact frozen target, and verifies archived source bytes.
Its fixed axiom-audit source must print the two actual endpoint reports;
empty output does not pass. Structurally valid false-goal/forged-body controls
must produce logical `REJECT`, not merely a decoding error.

All execution is sequential and bounded. The scripts and evidence are local,
uncommitted and unpromoted. Rebuilding Lean means fresh compilation of the
existing checker source closure followed by `lean --run`, not a new standalone
C binary and not a claim that arbitrary Lean mathematics translates to HA.

### Current mathematical frontier (updated 2026-10-11)

1. Finish the original fixed-program interpretation. The newer variable-degree
   composition, finite tail and witness theorems supersede the early fixed-size
   experiments. AP091/AP092 construct half-log samples near supplied roots;
   AP093 connects the original quotient to its half-root argument. AP094 carries
   the comparison to actual finite exponentials, and AP095 now normalizes it
   to requested dyadic precision at the unchanged n+8 shift. Join these finite
   statements with the explicit logarithm/exponential interpretation. Keep a
   single combined error budget: AP095 alone proves neither IR026's earlier
   7*2^-k estimate nor analytic identification of the fixed computation.
2. Build the actual auxiliary-node/jet identities. Reuse AP064's finite product
   error and AP080's rational-power precision for arbitrary integer multiples
   and the two-frequency expressions, retaining all positive denominators and
   independent table heads. These are not consequences of merely naming exp.
3. Assemble variable-multiplicity interpolation, the chosen auxiliary vector
   and a nonzero jet. Connect the existing product, coefficient-height and norm
   results to those same witnesses; a qualitative nonzero norm alone is not a
   quantitative lower bound for the selected jet.
4. Complete the explicit upper/lower contradiction and positive rational
   separation certificate, then check the entire original IR072 statement in
   closed ordinary HA and fresh same-data Lean. No IR parent is counted closed
   by the supporting statements above; transcendence remains deferred.

Keep the same authority boundary throughout: Z3/E/Vampire output is untrusted
guidance or an independent conjecture test. Induction and domain-specific
identities need actual ordinary HA proof bodies, with fresh same-byte Lean
checks. No unchanged oversized retry, automatic memory increase, theorem
admission from a solver status, or claim of measured end-to-end LLM savings.

## Original verified pilot execution, 2026-09-19

The [post-hardening observation archive](observations/validated-pilot-v2/manifest.json)
contains exact source snapshots, frozen contracts, all solver exports and logs,
ordinary proof bundles, and fresh-process replay receipts. Gzip preserves the
original bytes; both compressed and uncompressed hashes are recorded.

The final run took **72.49 wall seconds** with one proof/solver worker. This
excludes earlier integration runs, agent engineering and the regression/UI tests:

| Result | Count / scope |
| --- | --- |
| HA-checked full pilot contracts | 3: P01, P05, P07 |
| HA-checked supporting subleaves | 5: P02, P03, P06, P08, P11 |
| Classical solver hits, two CPU seconds per call | Z3 8/8; E 3/8; Vampire 1/8 |
| Universal IR parents closed / new library admissions | 0 / 0 |
| SMT or TSTP proof logs translated / independent Lean rebuilds | 0 / 0 |

P01 is signed-rational addition compatibility with actual denominator guards.
P05 verifies the recurrence step, not its base cases or uniqueness. P07 is the
signed-integer two-frequency identity; it does **not** provide the quadratic-field
domain lift. Supporting targets are never silently substituted for their parents.

All 15 arithmetic premises supplied to the solvers were regenerated from the
literal source and freshly HA-checked, without importing the full theorem
registry. Fresh replay checks the original formula, closed context, canonical
bytes, forged-body rejection and false-root rejection. Contract-specific
mathematical mutation witnesses still need their own validation campaign.

The comparison is **native-only versus solver-gated independent native reproof**.
Both arms use the same native factory. Solver hits are not translated proof logs
and this run does not establish solver acceleration. Measured child CPU: native
20.20 s, solver-gated native 20.31 s, solver/probe 25.83 s, basis setup 0.39 s.
Proof workers made zero model calls; agent-authored contracts, code and review
are LLM engineering work whose token cost is not measured here.

E 3.2 is now installed through Homebrew. Z3 4.15.4 was already available.
The official Vampire 5.1.0 macOS ARM64 release was checksum-verified and used
from a temporary configured path, not installed globally. A missing future
Vampire path must be reported unavailable, never silently replaced.

### Historical resource boundary and then-remaining work

An initial test-filter typo included the P10 large-number case; it was stopped
by the 512 MiB memory guard. The corrected filter excludes that open benchmark.
After early copy-work/serialization checks and shared squaring were added, its
one changed-strategy retry failed closed in 0.52 CPU seconds at 58.3 MB peak RSS.
**P10 was not certified in this baseline.** Twenty small/adverse binary tests passed; the full P10
test remains an explicit strict expected failure, not a passing proof claim.

The controller now pins the canonical codec, enforces nested wall alarms, and
preserves supervisor output measurements. A real forced-alarm handoff smoke
confirmed owned-child cleanup and restoration of the caller's signal state.

Then-planned work (historical; item 1 is completed by the shared-proof wave):

1. Replace repeated whole-body Cut copying with topologically shared operation
   bundles; then certify the already elaborated P10 closed inequality.
2. Connect P04's finite composition and P09's exact confluent coefficients to
   their actual HA trace predicates.
3. Certify all steps of P12's fixed approximation trace; a final host comparison
   alone must not be counted as P12.
4. Lift P02/P07 to the required signed/quadratic domains, then finish the rational
   denominator and power/fold bridges in P03/P06/P08/P11.
5. Add contract-specific hostile witnesses and a deliberately small,
   fail-closed proof-log reconstruction subset before claiming solver speedups.

The original integration runs are retained in `observations/integration-*-v1`.
They predate the source-pin, deadline and root-mutation harness repairs; the v2
run is the final post-hardening observation. No failed experiment was erased.

## Observed non-LLM calibration, 2026-09-19

The recorded [automation baseline](automation-baseline.json) took approximately
0.42 seconds before report serialization, under a 30-second aggregate ceiling.
It regenerated three elementary arithmetic certificates with existing native
compact arithmetic and checked their universal closures in ordinary HA, in
empty context. It also checked rejection of a false target. These demonstrate
the existing proof-producing infrastructure, not new irrationality lemmas.

Z3 4.15.4 produced `unsat` and a proof-shaped log for a guarded parity example.
That earlier result is recorded as unchecked external evidence: no Z3 proof was
translated or admitted. At baseline time Vampire and E were unavailable on PATH;
they were configured later for the pilot above. Native and Z3 baseline workers
used approximately 24 MB peak RSS each.
The deterministic proof workers made zero model calls; agent planning/review
was separate LLM work, and its token cost is not being represented as zero.

Exact-integer/Fraction calibration separately checked:

- 441 small confluent monomial identities, 21 selected-coefficient identities,
  315 coefficient-bound checks and 315 denominator-clearing checks;
- 26 quadratic moment-polynomial identities and 42 nonzero frequency norms;
- 17 finite approximation precisions, 136 pairwise finite-coherence checks,
  and certificates for 12 specified rational candidates (largest precision 13);
- the symbolic exponent ledger and small arithmetic boundary cases.

These are bounded experiments. They do not prove the analytic accuracy of the
approximation sequence, any variable-degree interpolation theorem, universal
irrationality, a practical extracted running time, or the total campaign cost.
No enormous auxiliary matrix was allocated.

## Reproduction and validation

Original baseline validation: **165 tests and 131 subtests passed**, with the known-unresolved
P10 benchmark explicitly excluded. The 147 generated files match a deterministic
rebuild; graph/link/mutation checks and JavaScript syntax checks pass. Landing
and results pages rendered successfully in isolated Chrome profiles (8.29 s),
and both screenshots were inspected. Temporary headless helpers were closed
after rendering; the user's normal browser profile was not used.

From the repository root:

```sh
python3 scripts/build_sqrt2_power_campaign.py --check
python3 -B -m pytest -p no:cacheprovider -q scripts/test_sqrt2_power_campaign.py scripts/test_sqrt2_power_exact_pilots.py scripts/test_sqrt2_power_automation_baseline.py
python3 scripts/sqrt2_power_exact_pilots.py
node --check scripts/assets/campaign-plan.js
python3 scripts/check_sqrt2_power_browser.py
```

The website generator checks graph acyclicity, typed edges, definition arities,
immutable parent hashes, exact output hashes and byte-deterministic rebuilds.
Mutation tests reject forged proof status, fake definition authority, changed
pilot scope and a pilot instance being presented as its universal parent.

Five browser routes were rendered: landing, overview, the irrationality cone
including definitions, the future transcendence neighborhood, and combined-atlas
G121. The browser checker uses fresh isolated profiles and validates emitted
DOM; on this Mac, lingering headless Chrome processes required explicit cleanup
after rendering. This is reported separately from page correctness.

To repeat the native/Z3 smoke, use `scripts/sqrt2_power_automation_baseline.py
--run --output <new-report-path>`. Existing reports are never overwritten.
Its source/binary pins and subprocess transcripts belong to that individual
observation. A baseline result is not a campaign proof-admission receipt.

To reproduce the bounded pilot, run `scripts/run_sqrt2_power_pilot.py --run
--output <new-directory> --vampire <configured-absolute-binary-path>`. Its
supervisor needs read-only process accounting. Source changes produce a new
observation, never an overwritten historical receipt. For the green structural
suite, include the `test_sqrt2_power_external`, `pilot_instances`, `pilot`,
`binary_certificates` and `alarm_handoff` files, with
`-k 'not test_p10_actual_closed_certificate'`; keep the excluded P10 failure
explicit. Do not launch an unbounded proof grind or promote planning artifacts.
