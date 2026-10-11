# Irrationality first, transcendence next: the non-LLM-first HA campaign

Planning date: 2026-09-19. Active mathematical target: **IR072 / G121**.
Next target: **TR006 / G122**, deferred until the first target is closed.

Research execution continuation (2026-10-11): 212 additional exact statements now have
ordinary HA replay, independent fresh Lean checks and 1619 distinct focused regressions;
see the active section of `research/arithmetic-library/sqrt2-power/README.md`.
QF002/QF003 construct the previously missing integer product trace and nonzero
endpoint. QH001/QF004/QH002/QF005 construct canonical traces and prove finite
coefficient-height bounds for their nonzero endpoints. CV002 proves all-index
uniqueness of the denominator-cleared log-exp coefficient recurrence. CV003
constructs arbitrary finite natural convolution tables with extensional value
uniqueness. CV004 constructs actual truncated power traces; CV005 proves their
coefficients vanish below the exponent for positive-order inputs. CV006
constructs three actual finite sums and proves general weighted linearity from
the separate pointwise relation. CV007 constructs Euler prefixes and proves the
coefficientwise product rule for actual natural convolutions. CV008 constructs
both orders of every finite natural affine double sum and proves interchange.
CV009 proves general affine sum splitting; CV010 proves finite reversal and
all-index natural convolution commutativity. CV011 transports actual sums across
zero tails; CV012 constructs the actual triple-product grid; CV013 proves the
actual row-sum formula. CV014 proves natural convolution associativity below
a common truncation width. CV015 proves weighted convolution linearity, CV016
constructs the unit and proves its law, and CV017 proves all-exponents Euler
power differentiation for actual constructed traces. CV018 constructs weighted
prefixes, CV019 constructs their finite accumulation traces, and CV020 constructs
the shifted coefficient weights. CV021 proves the finite composition Euler
identity for both actual accumulations. CV022 constructs denominator-cleared
weights and proves conditional nonvanishing. CV023 proves all-row scalar
transport of weighted traces. CV024 constructs the denominator-cleared finite
composition and proves its Euler equation. CV025 constructs its finite inner
atanh coefficient table with a positive denominator; CV026 proves the actual
Euler table's initial values and period two. CV027 proves the corresponding
convolution recurrence; CV028 constructs a composition satisfying the actual
three-term recurrence; CV029 proves both initial values and identifies every
in-range coefficient. CV030 proves the factorial/power interpretation of the
weights; CV031 applies it to the same constructed composition witnesses.
CV032 constructs unique-valued Horner traces. CV033 proves their geometric
remainder for the coefficient pattern; CV034 applies it to the same actual
composition, with a proved nonzero denominator and no pattern premise.
CV035 proves weighted Horner linearity; CV036 proves exact zero-padding scaling.
CV037 interprets a Horner endpoint as an actual weighted sum, conditional on
the geometric weight table and pointwise product prefix.
CV038 constructs the geometric weights and proves their power-product invariant.
CV039 constructs the product prefix and applies CV037 to the same witnesses.
CV040 identifies every weight and term with its actual complementary power.
CV041 proves convolution weight multiplication with the necessary extra factor;
CV042 transports it through actual antidiagonal terms and coefficient sums.
CV043 proves the scaled shifted-block sum law with both zero margins; CV044
constructs the Cauchy grid and CV045 identifies all its row sums.
CV046 proves the complete-column sum formula with its explicit span equality.
CV047 constructs one grid and all full-length row/column sums with shared data.
CV048 constructs full convolution and proves the product-of-sums identity.
CV049 proves the exact full-length Horner product identity, retaining the extra
multiplier. CV050 proves local convolution transport across input encodings
and lengths, preserving the actual diagonal and sum witnesses.
CV051 constructs power traces at two ordered widths and proves all-row
coefficient transport. CV052 constructs both weighted compositions with the
same weights and extends that transport to every accumulation row.
CV053 proves upper-support addition for arbitrary convolution prefixes;
CV054 proves all power rows have support at most 1+kL. CV055 transports an
actual Horner history across equal shorter prefixes. CV056 proves exact
support-complete multiplication p*z=t*(x*y), with p=t^q and N+q=L+M.
CV057 extends multiplication to supplied actual values; CV058 proves the
all-exponents finite power-evaluation identity under a whole-support bound.
CV059 constructs actual row-evaluation prefixes and proves extensionality.
CV060 proves weighted accumulation evaluation, and CV061 connects it to the
same actual whole-support power trace and each row's monomial identity.
CV062-CV064 prove exact Horner splitting, scaled base comparison and the
finite integer omitted-tail majorant for arbitrary ordered bases.
CV065-CV066 prove the bounded-coefficient Horner majorant and apply it to the
same actual atanh table. CV067 proves `(k+2)!>=2*3^k`; CV068 proves finite
ratio-sum domination, including empty prefixes and zero ratio.
CV069 constructs actual weighted-power prefixes and sums; CV070 supplies the
same-table exponential recurrence, nonzero initial weight and factorial
normalization. CV071 retains all those witnesses and proves the finite sum
is at most nine times its initial weight when x<=2d. CV072-CV073 prove the
same actual composition-row/product recurrence; CV074 constructs the whole
composition at base two and bounds its normalized finite sum by nine.
CV075-CV077 give valid rational omitted-tail bounds for the same actual
composition and for supplied input/weight tables. CV078-CV079 connect consumed
rows and unequal power depths without requiring an unused extra source row.
CV080 puts the coefficient pattern, geometric-prefix value and rational tails
on the same constructed full table. CV081-CV082 evaluate and split supplied
computations without replacing their encodings; CV083 gives the finite
geometric-prefix/tail sandwich arithmetic. CV084 aligns actual powers and
supplied values to prove both valid rational error comparisons.
CV085 constructs the actual normalized finite composition and both rational
error bounds without a pattern or tail premise. CV086 proves the sharper
base-three finite inner bound. CV087-CV088 construct actual outer-exponential
tails and prove their cutoff decay uniformly in every extra finite horizon.
CV089 proves the general base-three coefficient-tail bound without a zero head.
CV090 constructs the actual inner truncation and cross-multiplied error bounds;
CV091 gives both valid rational comparisons with explicitly nonzero denominators.
CV092 proves the exact cross-scale identity for independent tables and values.
CV093 proves the valid rational truncation bounds for two independent supplied tables.
CV094-CV096 prove finite exponential term and sum continuity; CV097 constructs
rescaled computations and CV098-CV099 remove the shared-normalization restriction.
CV100 proves the uniform finite exponential truncation bound for supplied sums;
CV101 combines independent-argument and truncation errors using a constructed
middle prefix. All eight pass original HA, fresh Lean and focused regressions.
CV102 proves all denominator guards and states the same two errors as valid
rational comparisons; HA, fresh Lean and its seven proof regressions pass.
SQ001 replays the small historical Bertrand floor-root cone and proves exact
existence and uniqueness, including zero; HA, fresh Lean and eight tests pass.
SQ002 proves the square-to-root comparison. SQ003 constructs the unique
positive floor root of twice any positive scale squared, with strict bounds;
both pass HA, fresh Lean and seven regressions each.
SQ004 constructs the unique positive dyadic computation with separate bounds;
SQ005 proves positive integer rescaling of floor-root brackets. HA, fresh Lean
and seven proof regressions pass for both, with the conservative definition DAG intact.
SQ006 constructs the intervening actual power and proves exact integer
refinement for supplied dyadic computations; HA, fresh Lean and seven tests pass.
SQ007 proves valid-rational interval nesting with every denominator guard;
HA, fresh Lean and seven tests pass.
SQ008 proves the explicit finite dyadic modulus in cross-multiplied arithmetic;
HA, fresh Lean and seven regressions pass.
SQ009 proves the square residual and supplied root bounds; SQ010 proves the
reciprocal modulus. Both pass HA, fresh Lean and seven proof regressions each.
AP001 constructs the actual logarithm/root input and proves its denominator
positive and value at most one. AP002 constructs its actual finite exponential
sample with positive normalization and all factorial/power identities.
Both pass HA, fresh Lean and eight proof regressions each. AP003 proves exact
quotient-value independence for independent supplied graphs and positive
coefficient scales; HA, fresh Lean and seven proof tests pass. AP004 proves
positivity, range, recurrence and normalization for every supplied sample,
with HA, fresh Lean and seven proof regressions. AP005 proves exact rational
output-value independence for complete samples with independent encodings and
scales; HA, fresh Lean and seven proof tests pass.
These are supporting statements (including audited reuse), not closed IR
packages.
The published v5 index remains its frozen 33-statement checkpoint; the current
local total is recorded in the active README section. No promotion or deployment
is implied.

Active analytic queue: the finite natural composition recurrence, its actual
initial values and all coefficient values are now checked through CV029;
the factorial/common-denominator interpretation is checked through CV031.
Exact finite Horner evaluation at 1/3 is now checked through CV034; weighted
linearity and zero-padding scaling are checked through CV036. CV037 gives the
conditional weighted-sum interpretation; CV038 constructs and interprets the
weight table; CV039 constructs the product table and closes the unconditional
finite weighted-sum construction. CV040 proves exact complementary weight
exponents; CV041/CV042 prove the coefficient-level multiplication compatibility.
CV043-CV045 now provide shifted zero-padded sums, the actual Cauchy grid and
all row-sum identities; CV046-CV049 close the columns, full sums and full Horner
product law. CV050 proves low-coefficient locality; cross-width power and
accumulation transport is checked through CV052, upper support through CV054,
and support-complete shorter multiplication through CV056. CV057-CV058 connect
supplied power-row values to this law at every exponent; CV059 constructs row
evaluation tables. CV060-CV061 prove weighted-accumulation and same-witness
finite composition evaluation. CV062-CV064 prove the integer tail-majorant
core; CV065-CV066 prove the integer inner-polynomial majorant. CV067-CV068
prove factorial and ratio-sum ingredients for the outer majorant. CV069-CV070
construct the actual factorial-weighted power terms, their sum, recurrence
and denominator-cleared normalization. CV071 proves their finite exponential
sum bound. CV072-CV074 connect it to the same actual composition, preserving
every scale and trace. CV075-CV077 prove its actual rational omitted-tail
bound; CV078-CV079 align weighted transport with the consumed power depths.
CV080 now combines the coefficient pattern and tail bound on the same full
row. CV084 proves scale alignment and valid rational error bounds for the
supplied actual base-three values; CV085 instantiates them on the constructed
computation. CV088 proves the finite outer tail's uniform cutoff decay, and
CV091 proves the finite same-table inner truncation error. Independent-table
normalization and truncation are checked through CV093; finite exponential
continuity and the combined two-error estimate are checked through CV102.
AP082-AP086 now give independent logarithm/exponential refinement, uniform
near-two bounds and fixed-schedule positive witnesses. AP087-AP089 give the
explicit half-logarithm refinement and a uniform finite comparison with one
actual dyadic root, chosen before arbitrary later independent tables. The
next contract aligns that root comparison with the fixed index schedule;
its exact statement and separate resource gate are recorded below.
Certified analytic accuracy of the actual approximation algorithm, its analytic interpretation, the final
combination of the checked omitted-coefficient tail, variable-multiplicity
Hermite identity, real-norm/moment bounds and final positive precision
certificate still require proofs. IR072 remains open. The dated October 1
execution account below is retained as historical evidence, not current status.

### Checked finite-series gate: Euler product rule (CV007)

Use the Euler operator `E(A)[i]=i*A[i]` before introducing shifted ordinary
derivatives. This is natural arithmetic with no cancellation or division.
Local ND0410 is the conservative computation graph:

    NatEulerPrefix(ab,ac,db,dc,L) :=
      forall i a. Lt(i,L) -> BetaAt(ab,ac,i,a) -> BetaAt(db,dc,i,i*a).

The checked unconditional theorem constructs both Euler prefixes and all
three actual antidiagonal coefficient sums, for arbitrary inputs and index i:

    exists db dc eb ec p q r.
      NatEulerPrefix(ab,ac,db,dc,L) and
      NatEulerPrefix(bb,bc,eb,ec,M) and
      NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,p) and
      NatConvolutionCoefficient(db,dc,L,bb,bc,M,i,q) and
      NatConvolutionCoefficient(ab,ac,L,eb,ec,M,i,r) and i*p=q+r.

This contract now has an ordinary HA certificate, fresh replay, independent
fresh Lean checking and seven regressions. Its bundle has 123 nodes and 6,413
ordinary constructors; see `shared-wave-euler-product-v1`, its `-lean-v1`
check and `-validation-v1.json` under the campaign's observations. Its proof:

1. Construct each Euler prefix by induction and actual `beta_prefix_extend`.
   At the appended position, use the actual input decoding and multiply it by
   the index. Preserve earlier output entries; use beta uniqueness at the
   last position. Include L=0 and M=0.
2. Prove zero-extension compatibility of that graph. Inside the prefix use
   its computation clause; outside use the input's zero value and `i*0=0`.
3. Reuse actual `polynomial_diagonal_prefix_entry` and
   `polynomial_diagonal_term_functional` bodies (original polynomial bundle
   nodes 168 and 162; CV003 archive nodes 116 and 115). For j+k=i, construct
   the two derivative summands `(j*a)*b` and `a*(k*b)` from one original term
   `a*b`; functionality identifies the independently computed summands.
4. Reconstruct `i*(a*b)=(j*a)*b+a*(k*b)` from the explicit index equation,
   distributivity, associativity and commutativity. No algebraic law enters a
   definition, and solver success is not an imported HA premise.
5. Apply the actual all-lengths linearity body inside CV006 (node 107) with
   weights alpha=beta=1, gamma=i to the three actual diagonal sums. Simplify
   `1*q+1*r` using the original one-multiplication proof.
6. Construct all coefficient witnesses using CV003's coefficient-existence
   body (node 120), and assemble the unconditional root. Merge only exact
   actual rows with stable ordered dependencies; discard unreachable rows
   before canonical replay. Check the same bytes in fresh HA and fresh Lean.

After CV007: natural convolution associativity is checked as CV014; iterate this product rule
along CV004 power traces, establish the
finite coefficient chain rule, transport factorial/common denominators, then
derive `(1-z^2)F'=2F`. CV005 supplies vanishing of powers above each coefficient
degree; CV002 supplies the recurrence solution only after this missing chain
has been proved. Composition tails and analytic interpretation remain later
obligations, not consequences of the product rule alone. The existing public
prime-field polynomial associativity theorem assumes a prime modulus and
canonical residues. It cannot be reused at modulus zero as if it were natural
convolution associativity. CV008 now supplies actual finite-sum interchange,
with separate construction and extensionality lemmas. Its unconditional root
constructs row/column codes and their common total for source cells at
`(o+s*i)+t*j`. All dimensions and strides are arbitrary naturals. The four new
inductions passed first-attempt ordinary HA replay and fresh independent Lean
(126 nodes, 6,597 constructors), plus seven regressions. Local conservative
ND0411–ND0413 contain no interchange identity. CV009 now proves finite sum
splitting (120 nodes, 5,872 constructors); CV010 proves the needed sum reversal
and natural coefficient commutativity (133 nodes, 6,944 constructors). Each
passed first-attempt HA, fresh Lean and seven regressions, without new aliases.
The associativity bridge is now checked. Its exact sequence is:

1. Checked CV011: an actual length-m sum retains its value at length
   m+n when every newly decoded entry is zero. Derive this from actual split
   sums and checked weighted linearity, not from an assumed padding identity.
2. Checked CV012: construct the actual finite grid with cell
   `A[j]*B[k]*C[l]` when `j+k+l=i`, and zero when `j+l>i`, using decoded
   quotient/remainder coordinates in an `(i+1)`-square beta table.
3. Checked CV013/CV014: identify its row and column sums with scaled antidiagonal sums. Use CV010
   only where the inner antidiagonal order is reversed, CV006 for scalar
   summation, and zero-tail transport to extend the shorter diagonals.
4. Checked CV014: apply actual CV008 interchange and actual coefficient uniqueness to prove
   `(A*B)*C=A*(B*C)` below the common truncation width. Keep that width premise:
   arbitrary shorter intermediate tables do not satisfy the claim.
5. Lift Euler products along power traces using associativity and bilinearity,
   then prove the actual finite composition recurrence and denominator laws.

Items 1 and 2 now have ordinary HA, fresh Lean and seven regressions each:
CV011 has 123 nodes / 6,303 constructors; CV012 has 110 / 5,165. Items 3 and 4
also passed HA/Lean and seven regressions each (CV013 and CV014 below). Item 5
remains an obligation; the supporting theorem count is not a percentage of IR072.

The now checked CV013 row-sum contract is more precise. Given
`j+r=i`, an actual padded coefficient `A[j]=a`, and a coded prefix U satisfying
`NatTripleCell(A,B,C,i,j,l,U[l])` for every `l<i+1`, construct t and s with
`NatConvolutionCoefficient(C,B,r,t)`, `Sum(U,i+1,s)` and `s=a*t`.
This does not assume a row-sum equation. It passed first-attempt HA, fresh Lean
and seven regressions (139 nodes / 7,443 constructors). Local ND0418 contains
only actual cell decoding. The implementation uses these ordinary sublemmas:

- Match a genuine `(C*B)` antidiagonal term to the actual triple cell: cancel
  the complementary index equations, use actual padded-entry functionality,
  and contradict the inactive case with `Lt` versus `Le`. This direct matching
  proof avoids introducing an unused general cell-functionality theorem.
- For `r<l`, every triple cell in row j is zero. An active cell would force
  `k+l=r`, contradicting `r<l`; the inactive case already says zero.
- Construct `Sum(U,r+1,u)`. CV006 with weights `(a,0,1)` identifies u with
  a times the real antidiagonal sum. CV011 extends U across its j zero entries;
  `r+1+j=i+1` and sum uniqueness identify s=u.
- Checked in CV014: prove cell transposition by swapping A/C and j/l, with actual
  multiplication laws; apply the same row lemma to column slices and convert
  affine slice addresses to the row-major grid indices explicitly.

CV014 now uses those certificates, CV008 interchange and CV010 commutativity
to identify the nested convolutions. Its root allows any common intermediate
width W with `i<W`, constructs the two inner prefixes at W, and constructs a
common value for `(A*B)*C` and `A*(B*C)` at i. Its conditional assembly for
supplied prefixes is retained as actual bundle node 166. First-attempt HA and
fresh Lean checks passed (168 nodes / 10,172 constructors), plus seven tests.
The small-grid model tests are never substituted for these certificates. At
the boundary i=W the identity can fail: A=[1,1], B=C=[1], W=i=1 gives 0 versus 1.

CV015 now proves weighted convolution linearity from actual weighted prefix
linearity and antidiagonal functionality, including zero weights, zero-length
inputs and unbounded coefficient index (123 nodes / 6,449 constructors).
CV016 constructs the unit and proves its law below the unit width from an
actual first term and zero tail (142 / 7,503). CV017 iterates the Euler product
rule along actual power traces (193 / 12,931). All three passed first-attempt
HA, fresh Lean and seven regressions each. No new definitions were introduced.

The power-rule induction retains genuine execution and decoding premises:
`i*P[k+1][i]=(k+1)*(EA*P[k])[i]` for i<H and k<K. Its unconditional root
constructs EA and the entire trace through K; no vanishing constant coefficient
is required. At k=0 use the proved unit law. At the successor, decode the
previous row, construct its convolution with EA and the current row's Euler
table, apply the induction hypothesis pointwise, transport the scalar through
CV015, and use CV014 associativity and CV007's product rule. The independent
checkers accept the actual ordinary induction, not these descriptions.

Critical chain status (all are local; none is a library admission):

1. Checked CV018: construct actual weighted prefixes
   C[i]=alpha*A[i]+beta*B[i]. The weighted relation is an output rather than a
   premise. Preserve its convolution law by the actual CV015 body. First-attempt
   HA, fresh Lean and seven regressions passed (125 nodes / 6,687 constructors).
2. Checked CV019–CV021: construct finite accumulation traces with Q[0]=0 and
   Q[k+1]=Q[k]+w[k]*P[k], and the shifted weighted trace
   R[0]=0, R[k+1]=R[k]+(k+1)*w[k+1]*P[k]. Each row step is a separate
   conservative computation relation on actual decoded tables. CV019 constructs
   the generic accumulation for every supplied source family and weight table,
   without a power-property premise (110 / 5,326; first-attempt HA, fresh Lean,
   seven regressions). ND0419–ND0421 are conservative computations only. CV021
   specializes both source families to the same actually constructed power
   trace. CV020 constructs the shifted weights `(k+1)*w[k+1]` using actual
   Euler and affine-slice bodies (107 / 4,967; first-attempt HA, fresh Lean,
   seven regressions; no new induction). ND0422 records only that computation.
3. Checked CV021: prove E(Q[K+1])=EA*R[K] coefficientwise below H. The base
   is the weighted unit; each successor combines CV017 with actual weighted-prefix
   linearity. First-attempt HA, fresh Lean and seven regressions passed
   (208 nodes / 14,786 constructors; 909,502-byte canonical bundle).
4. CV022 constructs weights with terminal one and adjacent identity
   `(j+1)*d*w[j+1]=w[j]`, with conditional nonvanishing. Their factorial
   interpretation `w[j]*j!*d^j=N!*d^N` is now proved in CV030 with actual
   relational factorial and power bodies, not host-language division. CV031
   connects that invariant to the same constructed composition witnesses.
5. Checked CV023–CV029: transport the weight equation, remove the omitted
   outer term by vanishing, construct the inner atanh table, derive the
   recurrence and both initial values, then apply CV002. The tails and analytic
   interpretation remain open. No supporting count closes IR072.

### Checked finite composition Euler identity (CV021)

For arbitrary natural A coefficients, outer weights w, width H and degree N,
construct EA, the power trace P through N, the shifted weight table
`d[k]=(k+1)*w[k+1]` through N, and two actual weighted traces:

    Q[0]=0, Q[k+1]=Q[k]+w[k]*P[k]       (through N+1),
    R[0]=0, R[k+1]=R[k]+d[k]*P[k]       (through N).

Prove, for every i<H, that `i*Q[N+1][i]=(EA*R[N])[i]`. The unconditional
root must construct all five objects; the conditional assembly must retain
their actual execution relations and supplied row decodings. No condition on
the input's constant coefficient is needed for this finite polynomial identity.
No rational/exponential interpretation or tail bound is part of this target.
The full ordinary HA construction and fresh replay, independent fresh Lean
check, and seven regression tests now pass. The root constructs all five
objects with 16 code witnesses; helper node 206 retains the conditional
induction for supplied actual traces and row decodings. No new definitions
were added, and no resource ceilings or kernel rules were changed.

Use one induction on k, with N and all terminal row/value witnesses generalized.
Its motive is the identity for Q[k+1], R[k] from the full traces above and
`Le(k,N)`. This avoids pretending arbitrary shorter traces are given. At the
successor, `Le(k+1,N)` is precisely the range premise k<N needed for the
power rule, shifted weights and R step; successor monotonicity gives k+1<N+1
for the Q step. The old induction bound k<=N follows by transitivity.

Required ordinary helpers before the induction:

- Transport a weighted trace's zero initial row to any supplied decoding of
  row zero, using the two actual beta-functionality equalities.
- Extract a weighted step as `NatLinearTriple(1,w,1,V,U,W,H)` for supplied
  source/current/output rows and an actual decoded weight. Decode the seven
  witnesses of the stored step and substitute all six row-code equalities
  and the weight equality. Do not assume execution is extensional by name.
- A zero actual prefix makes every actual convolution coefficient zero. Use
  CV015 with alpha=beta=0, gamma=1 and beta uniqueness; use CV014's actual
  coefficient swap for a right zero factor.
- The Euler value of the unit is zero. Use CV016's actual unit-entry helper
  and its two cases; the zero index or zero coefficient yields i*a=0.
- Normalize `1*c=1*a+w*b` to `c=a+w*b` using actual one-multiplication.
- Reconstruct `i*(a+w*b)=x+((k+1)*w)*y` from i*a=x and
  i*b=(k+1)*y using ordinary multiplication laws, not a trusted ring oracle.

Base: decode Q[0], P[0] and w[0]. The weighted step gives
Q[1]=0+w[0]*unit. Its Euler coefficient is zero; R[0] is a genuine zero
prefix, so its convolution with EA is zero. Include N=0 and H=0.

Successor: decode Q[k+1], R[k], P[k], P[k+1], and w[k+1]. Construct
x=(EA*R[k])[i] and y=(EA*P[k])[i]. The induction hypothesis gives
i*Q[k+1][i]=x; CV017 gives i*P[k+1][i]=(k+1)*y. The Q step and ordinary
multiplication yield x+((k+1)*w[k+1])*y. CV020 supplies that exact weight
to the R step. CV015, with all three actual convolution coefficients
swapped to a common right EA input, identifies the same value with the
coefficient of EA*R[k+1]. Preserve i<H throughout.

### Checked constructive denominator-cleared outer weights (CV022)

Use a finite recurrence as the computation, with factorials as its later
proved interpretation. For arbitrary d,N construct a table w with terminal
entry w[N]=1 and, for j<N, `w[j]=((j+1)*d)*w[j+1]`. Prove separately that
every entry through N is nonzero when d is nonzero. This is a computation
graph plus a positivity theorem, not an assumed denominator identity.

Construct by induction on N. At zero, append the value 1 to an empty prefix.
At the successor, construct the scaled old prefix
`v[j]=((N+1)*d)*w[j]` for j<N+1 using CV018, then append 1 with actual beta
extension. For j<N the old adjacent equation transports by commutative
multiplication; the new final equation uses the old terminal value 1. Prove
positivity with actual multiplication-nonzero bodies and beta functionality.
Keep d=0 and N=0 in the unconditional construction; use d!=0 only for
nonvanishing. Freeze the computation as local ND0423 if the collision check
passes. No rational division or factorial quotient is needed for construction.
The collision check passed; local ND0423 is now the conservative terminal-one
computation. Its unconditional root and separate nonvanishing conclusion passed
first-attempt HA, fresh Lean and seven regressions (108 nodes / 5,284
constructors). The nonzero-d premise is necessary: d=0,N=1 gives [0,1].

CV023/CV024 use the adjacent equation and CV020 to show that scaling the derivative
accumulation R by d gives the original accumulation Q through degree N-1.
Use CV005 to remove the omitted degree-N contribution below degree N. This
connects CV021 to the exponential coefficient equation. Separately establish
`w[j]*j!*d^j=N!*d^N` (and the positive common denominator), using actual
factorial/power proof bodies; only this interpretation licenses identifying
the normalized finite composition with the exponential partial sum. The
existing finite-factorial module was located read-only; its theorem names
or source factories are not proof authority. Authenticate archived bodies and
select their actual dependency cone before using them.

Checked exact transport gate (CV023): for a common arbitrary source-row
family and two actual weight tables satisfying
`NatLinearTriple(d,0,1,Z,Z,W,K)`, construct both weighted traces and prove
their corresponding rows satisfy the same scalar relation, for every k<=K
and coefficient below H. Retain a conditional helper for supplied traces.
Induct on k with K, row codes and coefficient values generalized. At zero use
the genuine zero rows. At the successor extract both actual weighted steps
with CV021's stored-row helper, decode a shared source coefficient, use the
weight relation and the old row relation, and distribute multiplication.
Neither d!=0 nor a power property of the source rows is needed.

CV024 now combines CV022's adjacent equation with CV020's shifted table to obtain
that weight relation for W and its shifted derivative weights. Specialize
CV023 to the two accumulations constructed by CV021. Restrict Q's trace from
N+1 to N with explicit range transport. With input zero constant term and
width H=N, CV005's conditional vanishing helper makes P[N][i]=0 for every
i<N, so Q[N+1] and Q[N] agree there. Use CV015 to transport the resulting
pointwise relation Q[N+1]=d*R[N] through convolution, yielding
`d*(i*C[i])=(EA*C)[i]`. CV025–CV029 below supply the inner coefficients and
initial values. Factorial/denominator interpretation and analytic tails remain
required before an exponential or irrationality theorem follows.

Both gates passed first-attempt ordinary HA and fresh Lean. CV023 uses one
ordinary induction, 116 nodes and 6,125 constructors. CV024 uses no new
induction, 224 nodes and 16,942 constructors. The combined current-file
regression run passes all 14 tests; the earlier CV023-only run is retained.
No source premise was removed, and no new alias or axiom was introduced.
CV025 now constructs the finite inner atanh coefficient prefix using a positive
common denominator and genuine beta extension (108 nodes / 5,026 constructors).
Its two conservative aliases ND0424/ND0425 contain only the coefficient
computation and finite lookup relation. CV026 constructs the Euler table and
proves the in-range initial values and period-two law (111 / 5,287). Both passed
first-attempt HA and independent Lean, with seven regressions each. No analytic
derivative or logarithm identity has been assumed or proved by these leaves.
CV027 now shifts actual antidiagonal sums twice to derive the convolution
recurrence (137 nodes / 7,195 constructors). CV028 specializes CV024 to the
constructed inner coefficients, using nonzero-d cancellation to prove the
three-term recurrence (245 / 18,901). CV029 proves the constant coefficient by
ordinary induction over the actual weighted trace; its linear coefficient
uses an explicit length-two convolution calculation and Euler's equation.
It applies the actual CV002 proof to obtain z at zero and 2z at every positive
index below N, with z nonzero and N>=2 (252 / 20,299). All three passed
first-attempt HA, fresh Lean and seven regressions each.

Checked factorial gate (CV030–CV031): interpret the weight computation by factorials and powers.
For every j<=N, prove `w[j]*j!*d^j=w[0]`, then use w[N]=1 to derive
`w[0]=N!*d^N`. Generalize actual factorial/power value witnesses in the
induction, using their zero and successor bodies. Keep positivity
separate. The 1,103,202-byte Lucas archive was inspected read-only; actual
factorial existence/functionality/zero/successor targets occur at nodes 132–135.
It contains no matching Pow endpoints. Authenticate/select/replay their
dependency cones before use. The full theorem registry must not be imported.

Sharper induction design: retain the conditional lemma for *supplied* weight,
factorial and power data. Fix d,N,W,w0 with the actual weight table and
BetaAt(W,0,w0). Induct on j, generalizing decoded weight w and both factorial
and power values f,p. Base uses actual Factorial(0,f), Pow(d,0,p) zero laws
and beta functionality. At j+1, decompose f and p using their actual successor
bodies, decode w[j], apply the adjacent weight equation and the induction
hypothesis, and reorder only multiplication. Thus factorial/power functionality
is not required for this invariant. At j=N use the actual terminal value one
to prove w0=fN*pN. Construct fN and pN from actual existence bodies. Preserve
zero d as an allowed algebraic case; positivity remains a separate implication.
The small Lucas archive supplies factorial bodies; existing QH002 and QF005
wave archives supply the actual power zero/successor and existence bodies.
The new untrusted mixed-archive assembly helper leaves the accepted builders
frozen, validates exact envelope/target/ordered dependency data, and replays
every selected ordinary body. No new trusted reader or kernel rule was added.
CV030 has 130 nodes / 6,558 constructors and nine passing regressions, including
a forged factorial ancestor. CV031 has 272 / 21,575 and seven regressions;
it preserves CV029's actual weights rather than substituting a separately
constructed table. Both passed first-attempt HA and fresh Lean.

Checked evaluation gate (CV032–CV034): construct finite integer Horner traces,
prove their equations for the identified coefficients, and retain exact powers
of three as denominators. CV032 has 107 nodes / 5,084 constructors; CV033 has
126 / 6,175; CV034 has 284 / 22,574. All passed first-attempt HA, fresh Lean and
seven regressions each. Local ND0426/ND0427 describe the computation only.
At N=K+2 the combined certificate constructs p=3^(K+1), the same coefficient
table's Horner value r, and proves r+z=(2z)*p and z*p nonzero. This is finite
evaluation, not an exponential or limit axiom.

CV035 now proves weighted Horner linearity for actual traces, with arbitrary
natural scalars (including zero), and constructs all three endpoint values
(111 nodes / 5,615 constructors). CV036 proves exact scaling for actual zero
tails, retaining the power witness and both actual endpoints (122 / 6,061).
Both passed first-attempt HA, fresh Lean and seven regressions.

CV037 proves h[k]*W[k]=sum(Q,k) by induction over actual Horner and Sum data,
given W[j]=t*W[j+1] and Q[j]=A[j]*W[j+1]. At k=N the actual terminal weight
one identifies the Horner endpoint with Sum(Q,N). It constructs the Horner
trace and endpoint, not the supplied W/Q tables. Local ND0428/ND0429 introduce
only those computation graphs. First-attempt HA, fresh Lean and seven tests
passed (115 nodes / 5,728 constructors).

Checked CV038 construction gate: build terminal-one geometric weights by induction
on N, scaling the previous table by t and appending one. Reuse the actual
CV022 scaled-extension and adjacent-scaling bodies, not their names as axioms.
Retain a supplied-table invariant: for j<=N, BetaAt(W,j,w) and Pow(t,j,q)
give w*q=W[0]. Generalizing w,q in the induction uses actual power zero and
successor-decomposition bodies. At j=N this identifies W[0] with t^N.
CV038 passed first-attempt HA, fresh Lean and seven regressions (123 nodes /
6,042 constructors), including t=0. No new definition was added.
CV039 now constructs Q[j]=A[j]*W[j+1] by beta extension and applies CV037 to
those same witnesses. Both supplied-table premises are removed from the root.
First-attempt HA, fresh Lean and seven regressions passed (137 / 7,321).

Checked CV040 exact exponent interface: for a supplied geometric table, j+e=N,
BetaAt(W,j,w) and actual Pow(t,e,q), prove w=q by induction on e with j,w,q
generalized. Base rewrites j+0=N to j=N and uses terminal one/power zero.
Successor uses (S j)+e=N, decodes W[S j], applies power decomposition and
the adjacent weight law. Construct Lt(j,N) from the same index equation;
no cancellation or nonzero-t premise is needed. Then identify each actual
term Q[j]=A[j]*q when (S j)+e=N, preserving all CV039 witnesses. First-attempt
HA, fresh Lean and seven tests passed (142 nodes / 7,593 constructors).

Checked CV041 multiplication interface: for geometric weights at L, M and L+M,
W_(L+M)[k+1]=t*W_L[i+1]*W_M[j+1] when i<L, j<M and i+j=k. Decode the
complementary exponents from the bounds and apply CV040 plus actual Pow-add
and successor-decomposition bodies. The 1,528,814-byte Kummer archive has the
exact Pow-add target at node 168 and Pow-functionality at 142; the smaller
571,540-byte Euler-units archive has functionality but no Pow-add. These are
not proof authorities. CV041 now retains and replays the actual Pow-add cone
through the bounded mixed assembler, with fresh Lean and a corrupted-import
negative control (135 nodes / 7,022 constructors; seven passing tests).
CV042 uses actual three weight tables and two weighted term prefixes to prove
u*w=t*v for the original and weighted convolution coefficients at every index.
It handles zero-padded terms by cases and applies the actual CV006 finite-sum
linearity body. Both coefficient values and the output weight are constructed.
First-attempt HA, fresh Lean and seven regressions passed (148 / 8,193).
For full convolution lengths L,M and output length L+M, the intended exact
Horner identity is H(C,L+M)=t*H(A,L)*H(B,M); keep this extra t factor and the
zero-length cases explicit. A truncated product cannot use that identity
without accounting for its omitted degrees.

Checked CV043-CV045: scaled shifted sums with both zero margins, an actual
square Cauchy grid of side N+1, and all length-N+1 row sums. The grid's (k,j)
cell is the actual padded product A[j]*B[k-j] for j<=k and zero for k<j.
Definitions ND0430-0434 describe only these computations. For any coded row
of length T>k, the actual diagonal prefix has length k+1; prove its remaining
entries zero and apply CV011 to identify the total with the convolution
coefficient. CV043 has 125 nodes / 6,488 constructors; CV044 110 / 5,103;
CV045 136 / 7,126. All passed first-attempt HA, fresh Lean and seven tests.

Checked CV046: a complete column at j is a scaled B block starting
at j, preceded and followed by zeros. Require (j+M)+q=T explicitly, identify
its middle cells using actual antidiagonal uniqueness, and apply CV043.
The root constructs both sum values from the actual padded left value,
column computation and span equality. ND0435 describes cells, not their sum.
First-attempt HA, fresh Lean and seven tests passed (133 / 7,204).
Remaining column integration plan:
For the final double sum use N=L+M and sum only N rows and N columns of the
side-N+1 grid. Do not silently sum N+1 rows: that would change the homogeneous
evaluation length. For j<L decode h+(j+1)=L and choose q=h+1 to get
(j+M)+q=N. For j>=L prove the entire column zero from actual padding,
without requiring j+M<=N. Construct affine row/column slices of length N;
the existing CV045 row-total helper works at arbitrary T>k. Reuse CV008
finite Fubini, CV006 scaling and actual sum uniqueness to conclude the full
convolution total is (sum A)*(sum B), including L=0 or M=0. Then apply CV042
to the constructed geometric-weight product prefixes and CV039 to obtain
the full Horner product law.

CV047 now checks the common-grid and all-row/all-column part of this plan,
including zero columns outside left support. It constructs N=L+M, grid codes,
one right-input sum x, every row coefficient/affine sum, and every column sum
a*x for the actual padded left value a. No new definition or induction.
Its first attempt stopped at the scope guard on a reused local name `span`;
the single changed retry used `span_witness` and passed HA, fresh Lean and
seven tests (149 nodes / 8,381 constructors). Both attempts are retained.

Checked CV048 full-sum producer: apply CV008 to this grid with
origin 0, row stride N+1, column stride 1 and both lengths N. It constructs
row-sum codes R, column-sum codes T and a common total z. Use actual affine-sum
uniqueness to identify R[k] with the CV047 convolution coefficient and obtain
NatConvolutionPrefix(A,B,R,N). For T[j], combine CV047's column theorem and
CV008 row lookup, rewriting origin 0+1*j to j, to prove T[j]=a*y where y is
the same right-input sum. Construct the left-input sum x and the prefix sum
w of T at length L. Apply CV006 linearity on [0,L) to get w=x*y. Prove the
tail T[L+h]=0 for h<M using actual padding and the same column-entry lemma,
then CV011 gives Sum(T,L+M,w). Actual sum uniqueness with CV008's total gives
z=w=x*y. Rewrite the constructed N=L+M and return the actual convolution
prefix, both input sums, output sum and product identity. No new padded-A
table or generic permutation theorem is needed. This also handles N=0.
The first attempt was rejected at local column entry because naive textual
renaming captured the right-input sum in a column's existential binder. A
bounded, non-mutating checker profiler identified the mismatch; an initial
diagnostic display-call error is retained too. Distinct column witnesses
and an exact alpha-renaming regression fix the authoring error. The same
root target passed the single retry, fresh Lean and eight tests (162 / 9,597).
The premature Lean-v1 run refused the unsuccessful HA observation; it is not
accepted evidence. The successful Lean report is `-lean-v2`.

Checked CV049 full-Horner product: construct C=A*B at length
N=L+M via CV003. Use CV039 independently for A at L, B at M and C at N;
each gives weights, pointwise weighted terms Q, a Horner trace, and the same
endpoint/sum value. Apply CV048 to Q_A and Q_B to construct their full
convolution D with total d=(sum Q_A)*(sum Q_B). For each i<N, use the exact
CV042 coefficient_product helper with the actual C[i], D[i] and W_C[i+1].
CV003 prefix_entry supplies both coefficient facts; the weighted C-prefix
then gives Q_C[i]=t*D[i]. Package this as NatLinearTriple(t,0,1,D,D,Q_C,N)
and apply CV006 to obtain sum Q_C=t*d. Actual sum uniqueness identifies
the CV048 input sums with the CV039 endpoints, proving the constructed
Horner endpoint z=t*(x*y), including t=0 and empty inputs. Keep all three
Horner traces and the actual convolution prefix in the unconditional root.
First-attempt HA, fresh Lean and seven regressions passed (218 nodes / 14,338
constructors), with no new definitions or induction.

Checked CV050 local convolution transport: if the actual padded inputs
transport below H and i<H, each j+k=i lies below H on both coordinates.
Transport each actual diagonal term, retain the same diagonal prefix codes
and actual finite sum, and construct a common coefficient. This is not
equality of full products or of tails. Arbitrary input lengths are allowed.
First-attempt HA, fresh Lean and seven regressions passed (117 / 5,495).
The next transport induction applies this helper at every actual power row,
using explicit H<=J and preserving coefficients only at i<H.

CV051 bounded-repair exception (recorded 2026-10-02 before execution): the
first candidate failed on an incorrect disjunction-constructor signature;
its one repair reached the unchanged kernel, which rejected unit uniqueness.
A 15-CPU/20-wall/768-MiB/64-KiB observational diagnostic identified use of
successor injectivity where successor nonzero was needed. Generation CPU
was 0.714479 + 1.029950 seconds; diagnostic CPU 0.393449 seconds. No proof
was accepted, no Lean run was started, and all records are retained.
Authorize one additional bounded repair for this leaf only: replace that
axiom-number guess with the exact existing, archived successor-nonzero
endpoint. The target, resource ceilings, checker and remaining campaign
retry policy stay unchanged. This is an explicit revision of the default
attempt count, not a fresh leaf or a claim that the two failures did not occur.
The additional run succeeded in HA (141 nodes / 7,483 constructors), then
fresh Lean and all seven regressions. CV052 separately proves the generic
weighted-accumulation transport induction, constructs both power and weighted
traces, and retains both all-row coefficient invariants. Its first attempt,
fresh Lean and seven regressions passed (151 / 8,802). No new definition or
analytic equality was introduced by either result.

Checked CV053-CV056 support-complete evaluation gate: local ND0436
`NatZeroAfter(b,c,L,r)` expands to `forall i a. Le(r,i) ->
BetaZeroExtend(b,c,L,i,a) -> a=0`. It is a separate conservative property,
not part of a computation definition. CV053 proves support r+s for actual
convolution prefixes; CV054 proves support 1+kL for every power row, including
the unit at zero. CV055 transports the same Horner history across equal
shorter prefixes. CV056 keeps the actual full product history, proves its tail
zero and applies CV036, obtaining p*z=t*(x*y) for p=t^q, N+q=L+M and
r+s<=N. Zero multiplier and empty lengths remain allowed. All four passed
first-attempt HA, independent fresh Lean and seven regressions each.

CV057 is now checked in HA and fresh Lean, with seven passing regressions:
CV056 extends to supplied convolution codes and supplied Horner endpoints,
using actual prefix extensionality, history transport and value uniqueness.
The archived Kummer power-uniqueness body (node 142) is reused after exact AST
matching and complete ancestor replay. The first Lean invocation supplied
`report.json` instead of its directory and stopped before certificate intake;
the corrected invocation is recorded as `supported-horner-values-lean-v2`.

CV058 applies this to all rows of a width-J+1 power trace under 1+K*L<=J+1.
The exact identity is a*y=(v*b)*c, with actual p=t^L, v=t^J, a=p^k, b=t^k,
c=x^k, input Horner endpoint x and row endpoint y. The first HA attempt was
rejected: a case-analysis equality was placed inside an inference-only
equality chain. A bounded unchanged-body diagnostic isolated this to the
unit-value helper; every other local body checked under its explicit
dependency hypotheses. The single repair exposes the unit-head equality as
a separate ordinary helper. HA v2 and fresh Lean passed; no target, kernel,
axiom, or resource ceiling changed. The diagnostic is not ancestor replay
or proof authority.

CV058's seven regressions also passed. CV059 now constructs an actual table
of Horner values for arbitrary encoded rows, with local conservative ND0437
`NatHornerValue` and ND0438 `NatRowHornerPrefix`. These contain only actual
traces/decoding; totality and extensionality are separate proved statements.
Its first HA attempt, fresh Lean and seven regressions passed.

CV060 is checked in HA, fresh Lean and seven regressions. It constructs the
pointwise weight-times-value prefix Q, actual accumulation R and s with
Sum(Q,K,s), then proves every actual terminal row U satisfies
NatHornerValue(U,t,H,s). It uses supplied-value Horner linearity from CV035,
a separately proved zero-prefix evaluation, actual prior/source rows and
sum decomposition. Local ND0439 describes decoded entry multiplication only.

CV061 combines CV058 and CV060 using the same actual power trace. It retains
the whole-support width, input endpoint x, actual p=t^L and v=t^J, source-row
value table V, weighted products Q, accumulation R and common terminal value
s. Every entry y=V[k] satisfies a*y=(v*b)*c for actual a=p^k, b=t^k, c=x^k.
HA, fresh Lean and all seven regressions have passed for each statement.

Quantitative gate, with no analytic limits hidden in definitions:

1. Checked CV062: exact Horner splitting. Construct the genuine affine tail
   B[j]=A[M+j], actual traces/endpoints x=H(A,t,M), y=H(B,t,N),
   z=H(A,t,M+N), and p=t^N. Prove z=p*x+y. Use an all-prefix induction
   on the tail length with the actual full and tail histories; permit zero
   multiplier and empty lengths. Retain an arbitrary-supplied-trace helper.
2. Checked CV063: scaled comparison at different bases. For a<=b and length r+1,
   prove a^r*H(A,b,r+1)<=b^r*H(A,a,r+1), with all four powers and
   endpoint values represented by their actual graphs. A joint induction
   can also prove a^r<=b^r. Base r=0 uses the first coefficient; step uses
   monotone addition/multiplication and the two Horner recurrences. Avoid a
   length-r exponent, which introduces an unnecessary extra factor b/a.
3. Checked CV064: combine splitting with CV063 on the same nonempty tail
   of length r+1, for general a<=b. Prove a^r*H(tail,b,r+1)
   <=b^r*H(whole,a,N+r+1), including zero bases. In particular, specialize
   to 2 and 3. Still open: treat an empty tail explicitly and perform positive
   denominator transport to obtain the finite bound
   tail(1/3)<=(2/3)^N*whole(1/2). No convergence inference is part of it.
4. Checked CV065-CV066: the integer inner atanh-polynomial majorant.
   Construct the same coefficient table, nonzero d, zero head, separate
   coefficient bound 2d, actual Horner value y and p=2^k, with
   y+2d<=(2d)*p. Positive rational-denominator interpretation remains open.
5. Partially checked CV067-CV068: actual f=(k+2)! and p=3^k satisfy
   2*p<=f, and an actual finite sum with (r+1)*a[i+1]<=r*a[i] is at most
   (r+1)*a[0]. Still prove the finite outer exponential at arguments <=2
   is <=9 by applying the bounds to the actual factorial-weighted terms.
   Combine with CV030 factorial normalization and CV061 finite composition
   evaluation, then apply the omitted-degree bound.

CV062-CV068 passed first-attempt HA, fresh independent Lean and seven
regressions each. Items 3-4's rational-denominator interpretations and the
complete finite exponential sum bound in item 5 remain open.

Checked quantitative targets:

- CV065: generic bounded-coefficient Horner majorant at 2. From actual
  BetaAt(A,0,0) and the separate bound a_i<=D for i<k+1, construct y and
  p with NatHornerValue(A,2,k+1,y), Pow(2,k,p), and y+D<=D*p. A supplied-
  trace induction maintains the same inequality at every positive
  prefix length. Base uses the actual zero head; step uses c<=D and
  (2h+c)+D<=2(h+D). D=0 is allowed. Local ND0440 NatBoundedPrefix
  depends only on Lt, BetaAt and Le; it is separate from computation graphs.
- CV066: apply CV065 to the actual CV025 atanh coefficient table of length
  k+1, with D=2d and d nonzero. Prove every coefficient <=2d: even entries
  are zero; for odd i, 1<=i and i*a_i=2d imply a_i<=2d by multiplication
  monotonicity. Prove the zero head separately from its parity cases. Retain
  the same actual table, denominator, Horner value and power. The integer
  inequality y+2d<=(2d)*2^k is not by itself an analytic logarithm statement.
- CV067: actual factorial/power lower bound. For every k construct
  f=(k+2)! and p=3^k with 2*p<=f. The supplied-values induction uses the
  exact factorial step and 3<=k+3; the base computes the actual factorial
  at two. No asymptotic or rational-division inference is included.
- CV068: finite ratio-sum bound for actual beta prefixes. Local ND0441
  NatRatioBoundPrefix(A,r,N) abbreviates the adjacent-entry condition
  (r+1)*a[i+1]<=r*a[i] for i+1<N, separately from Sum. The induction
  maintains sum(prefix k+1)+r*a[k]<=(r+1)*a[0]. The root constructs the
  actual sum for any N, including N=0, with s<=(r+1)*a[0]. r=0 is allowed.

Next quantitative targets and execution status:

1. Checked CV069: generic weighted monomial constructor for arbitrary
   supplied W, x and length K. Construct a beta prefix T such that
   every actual W[j]=w, Pow(x,j,p)
   and T[j]=t, for j<K, satisfies t=w*p. Keep computation graphs separate
   from positivity, ratio or sum bounds. Use power totality/uniqueness and
   beta extension; construct the finite Sum(T,K,s) as well.
2. Checked CV070: apply that constructor to CV030's same actual factorial weight
   table at denominator d and horizon N. Retain W, T, the nonzero initial
   weight t0 (under d!=0), the sum through N, and the exact term recurrence
   ((j+1)*d)*T[j+1]=x*T[j] for j<N. Prove the factorial/power identity
   (T[j]*j!)*d^j=t0*x^j with all three graphs supplied. This is the
   positive-denominator finite exp(x/d) computation, not yet convergence.
3. Checked CV071: from those actual terms, d!=0 and x<=2d, prove their finite sum
   is <=9*t0. Handle N=0 and N=1 explicitly. The implemented prefix-surplus
   induction below replaces the initial slice-and-CV068 plan. Prove T[1]<=2*t0
   and T[2]<=2*t0, then retain sum(prefix)+2*last<=9*t0. Every use of
   order cancellation must carry d!=0 and actual ordinary proof evidence.
   CV067 also supplies a separate factorial-tail comparison for later errors.
4. Checked CV074-CV077: transfer the resulting finite bound to CV061's same composition values.
   Do not identify its p=2^L with CV066's 2^(L-1): discharge the extra
   base-two factor and common-denominator powers explicitly. The finite
   rational omitted-degree bound is checked. Connecting the low-prefix
   coefficient identity and proving the analytic tail estimates remain.

CV069 and CV070 passed first-attempt ordinary HA, independent fresh Lean and
seven regressions each. ND0442 NatPowerWeightedPrefix depends only on Lt,
BetaAt and Pow; ND0443 NatScaledExpRecurrence depends only on Lt and BetaAt.
Their exact expansions contain no sum bound, positivity or convergence claim.
CV070 retains the same W, T, initial value w0, actual N!, actual d^N,
identity w0=N!*d^N, actual sum through N, recurrence and all-index
normalization. The new aliases remain local and unadmitted.

CV071 checked implementation refinement: the same finite bound is
proved more directly by retaining the surplus in a supplied prefix sum,
avoiding extra slice-code construction and sum-transport helpers. Keep the
root's full CV070 data and add s<=9*w0; do not weaken it to a premise-only
exponential computation. Prove the supplied-sum helper for arbitrary actual
recurrence tables first:

- Derive nonzero left order cancellation from actual `factor_difference`
  and `mul_left_cancel_nonzero`. For g+c*a=c*b, factor g=c*w and cancel
  c in c*(w+a)=c*b. `factor_difference` is an actual CV061 ancestor
  (node 51); equality cancellation is in the small CV002 archive. The
  14 MB Bertrand bundle is outside the current 8 MiB archive ceiling and
  must not be loaded as a shortcut.
- From x<=2d, d!=0, h<=j+1 and ((j+1)*d)*b=x*a, prove h*b<=2*a
  by two monotonicity steps, exact multiplicative reassociation and the
  guarded order cancellation. This gives the first two term bounds and,
  for j>=2 and h=3, the tail ratio 3*b<=2*a.
- Prove the strengthened invariant for prefixes ending at index k+2:
  Sum(T,k+3,s) and T[k+2]=z imply s+2*z<=9*w0, within the same
  supplied horizon. The base uses T[1]<=2*w0 and T[2]<=2*w0;
  the step uses the actual sum decomposition and 3*next<=2*last.
  Check the small identity (a+2*a)+3*(2*a)=9*a by bounded ordinary
  arithmetic reconstruction, not an unverified host simplification.
- Handle horizon N=0 and N=1 separately; for N>=2 drop the explicit
  nonnegative surplus. Preserve d!=0 at every cancellation. Applying
  the resulting helper to CV070's actual sum completes the finite bound,
  not any analytic convergence claim. CV068 remains separately available
  for later shifted tails; do not report it as a proof dependency if the
  direct prefix-surplus route is used.

CV071 passed first-attempt HA replay, independent fresh Lean and all seven
regressions: 163 nodes, 9,817 ordinary constructors and one new induction.
The stronger root retains all eleven CV070 computation/normalization fields.
There is no new definition or analytic-limit claim.

Same-computation bridges (now checked):

- CV072: reuse CV061's exact monomial law
  p^k*V[k]=(v*t^k)*x^k. With p!=0, prove V[0]=v for nonempty
  prefixes and p*V[k+1]=(t*x)*V[k] at every adjacent in-range pair.
  Use actual Pow graphs, successor decomposition, proved power nonvanishing,
  and guarded natural cancellation. No identification of beta-code numbers.
- CV073: combine this with the same factorial weights
  W[k]=((k+1)*d)*W[k+1] and actual pointwise products Z[k]=W[k]*V[k].
  Obtain NatScaledExpRecurrence(d*p,t*x,Z,N) for K=N+1 and the
  actual initial value Z[0]=W[0]*v. The extra factor p remains explicit.
- CV074: construct CV066's actual atanh table of length L=k+1 and
  CV061's whole-support composition at base two, with J=(N+1)*L.
  Identify its inner value by actual Horner uniqueness. From
  x+2d<=2d*2^k and p=2^L=(2^k)*2 derive x<=d*p; do not replace
  p by 2^k. The weighted recurrence has D=d*p, X=2*x and initial
  value W[0]*2^J. Prove D!=0 and X<=2D, then apply CV071's
  supplied-sum helper to the same actual composition sum. Retain all
  construction traces and normalizations, with bound s<=9*(W[0]*2^J).

After those bridges: exact rational transport and the finite omitted-coefficient
tail bound are now checked in CV075-CV077; the outer factorial tail and inner
odd-reciprocal tail remain.

CV072, CV073 and CV074 passed first-attempt HA and independent fresh Lean,
with respectively 119/5,937, 122/6,373 and 325/25,678 nodes/constructors.
Each has seven passing regressions and no new induction. CV074 retains
27 constructed witnesses and 37 fields, including all eleven specialized
CV061 fields, factorial normalization and the explicit p=q*2 relation.
Its first regression run found only a missing trailing newline in the
forged-bundle test fixture; the unchanged proof passes regression v2.
Both runs are preserved. No analytic parent is closed.

CV075 (HA and fresh Lean checked, seven regressions passed): let a supplied actual coefficient table have length
1+M+r, Horner value y at two, v=2^(M+r), positive denominator D and
y<=(B*D)*v. Construct its actual tail after M, value u at three, and
p=2^M, q=3^M, h=3^(M+r). Prove all relevant denominators nonzero and
u*q<=(B*p)*(D*h). This is the exact rational estimate
tail(1/3)/D <= B*(2/3)^M, with actual powers and a nonempty tail of r+1
coefficients. Use CV064, actual power-addition, CV071's guarded order
cancellation and natural monotonicity. Add only a conservative IRatLe
abbreviation of valid denominators and the cross-product Le relation,
not an analytic estimate hidden in a definition. The empty-tail case and
application to CV074's terminal rows were separate obligations. CV076 now
has HA, fresh Lean and eight passing regressions for that application:
retain all CV074 fields, decode one actual terminal
row, and construct every tail for M<=J with rational bound 9*(2/3)^M.

Next critical connection, without assuming equality of separately generated
weight tables:

1. Checked CV077 (HA, fresh Lean, eight regressions): generalize the majorant/tail construction to a supplied actual
   atanh prefix of length k+1 and supplied W satisfying the factorial-weight
   recurrence, with supplied nonzero head w0. Reuse CV066's arbitrary-prefix
   helper, CV074's inner-scale helper, CV061 construction and CV076's
   arbitrary-value tail helper. This permits the already constructed
   CV031/CV034 weight table to be used verbatim.
2. Checked CV078 (HA, fresh Lean, seven regressions): weighted width transport assuming source-row agreement only for
   k<K, the rows actually consumed. CV052 currently assumes agreement for
   k<=K. Its induction can use the existing step bound k<K directly; do not
   invent agreement of an unused extra power row.
3. Checked CV079 (HA, fresh Lean, seven regressions):
   for a small power trace of depth N and N+1 weighted terms, use
   CV051's supplied-trace agreement through power depth N. Restrict the
   full-width power trace from depth N+1 to N explicitly. Convert
   k<N+1 into k<=N for the preceding strict-source transport. The remaining
   application must prove N<=1+(N+1)*N by ordinary monotonicity and retain
   the same W throughout.
4. Transport the small table's proved coefficient pattern and exact base-three
   Horner value to the low prefix of the full terminal row. Use actual
   Horner-prefix transport and splitting, not equality of beta codes.
5. Evaluate the supplied full power/accumulation traces at base three using
   the arbitrary-trace helpers behind CV058-CV061. Then combine the exact
   low-prefix value and CV075's rational tail bound. The outer factorial
   tail and inner atanh tail still require their own precision schedules.

These are finite arithmetic bridges, not a substitute for the later analytic
and variable-multiplicity interpolation obligations in IR072.

CV075-CV079 passed first-attempt HA and fresh Lean. Their node/constructor
counts are 144/8,777, 336/28,904, 317/26,443, 30/1,602 and 55/3,467.
CV075 and CV078-CV079 have seven passing tests each; CV076-CV077 have
eight each, with large negative replay checks isolated under unchanged caps.
Only CV078 introduces a new induction. ND0444 IRatLe depends only on
the existing IRatValid and Le; it is a local conservative alias, not an
admission or an analytic axiom. All other new statements add no definitions.

CV080 bounded protocol-repair exception (recorded before the third run):
both v1 and its single target-projection repair v2 completed generation with
ordinary HA checking, but the combined positive/negative fresh replay reached
its unchanged 20-second CPU guard. The controller repeated the entire
ancestor replay for a forged-root negative control. Both observations remain
`not_checked`. The v2 target
and producer are now frozen. Repair the controller's negative control to
check the forged root body directly, in the unchanged HA kernel, against
the **same closed curried dependency/target formula** used by the ordinary
bundle checker. The full positive bundle and false-target rejection are
still checked normally; no ancestor body, source pin, or positive check is
skipped. Add exact-curried-goal and fail-open negative-control regressions.
Permit one new source-bound observation under this changed controller only;
keep generation 28 CPU / 40 wall, fresh replay 20 CPU / 30 wall, aggregate
60 CPU / 90 wall, one worker and 768 MiB unchanged. This is an explicit
one-leaf exception to the default retry count, not a larger resource limit,
changed kernel, or permission to regard the two previous runs as accepted.

Checked assembly CV080 (v3 HA, fresh Lean, eight regressions): instantiate CV031 at N=K+2
to obtain the small coefficient-pattern computation, its actual W, nonzero
head z, and factorial normalization. Apply CV077 at k=K+1, horizon N=K+2
to the exact same A and W, using z as w0; do not generate replacement weights.
The large width is 1+J with J=(N+1)*N. Prove N<=1+J and N<=J by
monotonicity from 1<=N+1 (N>=2 here), then apply CV079 to the supplied small
and large traces and their terminal accumulation rows. Decode each small
coefficient, transport it to the large row, and use beta uniqueness to obtain
the large row's actual low-prefix pattern z,2z,2z,... below N.

CV033 can then construct a new base-three Horner trace for that same large
row's low prefix, proving r+z=(2*z)*3^(N-1). This avoids any assumption
that independently constructed Horner codes are equal, and does not require
reusing the old small Horner history. Retain CV077's actual tail bound at
cutoff M=N; the next split/evaluation stage compares the full finite
exponential polynomial with 2 using the separate geometric-prefix and
omitted-coefficient errors. The accepted 26-witness target exports the
downstream computation and normalization data, not the obsolete small
histories or all base-two intermediate values. It has 426 nodes / 39,864
ordinary constructors. The preserved first two runs remain `not_checked`;
the original resource ceilings and positive checker remain unchanged.

CV081 (v2 HA, fresh Lean, seven regressions; 263 / 18,894) now evaluates
arbitrary supplied whole-support power and accumulation traces. It constructs
the input Horner value, both scaling powers, row values, weighted products
and sum, with the actual terminal-value and monomial laws. Its first run
incorrectly supplied the entire Horner-constructor package instead of the
trace projection; the single repair changed the proof, not its target.
Zero base and empty lengths remain allowed.

CV082 (first-attempt HA/fresh Lean, seven regressions; 38 / 2,024) proves
the scaled split for supplied slice, prefix, tail and whole values. It
restricts the whole Horner history and uses actual value uniqueness to
identify the supplied prefix value. There is no assumption that independently
constructed Horner codes are equal.

CV083 (first-attempt HA/fresh Lean, seven regressions; 14 / 997) proves the
natural-arithmetic combination. From r+z=(2*z)*p, y=b*r+u, h=p*b and
u*q<=(9*a)*(z*h), derive the exact balance y+z*b=(2*z)*h+u and both bounds
y*q<=(2*q+9*a)*(z*h) and (2*p)*(z*h)<=y*p+z*h. Every step is deterministic
checked reassociation/distributivity with explicit natural gap witnesses;
there is no division, cancellation, new definition, induction or axiom.
Rational denominator validity is a separate next obligation.

Checked CV084 (first-attempt HA/fresh Lean, seven regressions; 134 / 7,897): for the supplied full coefficient
row U, cutoff N=S k, and J=N+r, retain its actual low-prefix Horner value,
geometric identity, nonzero scale z and tail slice of length S r. Construct
b=3^(S r). Prove J=k+S r and use the actual power-addition theorem to obtain
h=p*b for p=3^k and h=3^J. Transport the full base-three value from length
S J to N+S r, then apply CV082 to these same values and the supplied slice.
Apply CV083 with q=3^N and a=2^N. All denominator validity is established
explicitly before expressing the bounds as IRatLe comparisons. Thus the
supplied normalized value E=y/(z*3^J) satisfies 2<=E+3^(1-N) and
E<=2+9*(2/3)^N. This remains conditional on its explicit computation,
geometric-prefix and tail-bound premises. It introduces no new definition,
induction or axiom and does not construct an exponential or limit.

Assembly refinement, CV085 (now checked in v3; fresh Lean and eight regressions): take CV080's actual input,
factorial weights, full power/accumulation traces and terminal row. Apply
CV081 at base three to these same codes, with L=N and K=N+1, keeping the
actual input Horner value, scaling powers, row values, pointwise products,
sum and monomial interpretation. Apply its terminal-value law to CV080's
actual terminal row. Decode CV080's already constructed tail at cutoff N.
Use the explicit N=S k equality and tail degree equation J=N+r to transport
the supplied slice, prefix value, full value and power witnesses to CV084's
exact argument positions; no code-number equality is needed.
The tail's h=3^J and CV081's separately constructed v=3^J must be identified
by actual power uniqueness before normalizing the same finite sum s by z*v.
Retain both rational comparisons, z=N!*d^N, the all-index weight invariant
and the exact monomial/product/sum data needed for the next outer-exp step.
Export the needed finite computation contract, not every obsolete trace
intermediate. CV080's accepted fresh replay used 19.381871 CPU seconds under
its 20-second phase guard, so keep the next assembly compact and measure it;
do not silently enlarge a failed budget. Complete the outer-factorial and
inner-atanh limit estimates only after this same-computation assembly.

CV085 pre-execution refinement (2026-10-02): reuse CV080's actual checked
component rows (CV031 construction, CV077 supplied-table construction,
CV079 transport, CV033 geometric evaluation, and CV080's small width/pattern
helpers), but reassemble the needed final contract directly. The large
intermediate CV080 root is not needed as an additional proof node. All
retained ancestors still undergo full ordinary replay; neither old receipts
nor theorem names supply authority. Construct k=K+1 and N=K+2 directly so
that unnecessary existential index equalities do not need later transport.
Retain the finite weighted sum, monomial interpretation, normalization and
both rational errors, rather than obsolete power/accumulation trace outputs.
Before this new leaf's first attempt, assign it generation 28 CPU / 40 wall
and fresh replay 28 CPU / 40 wall, sequentially. Their reservations including
one-second hard-limit margins total 58 CPU seconds, within the original
60-CPU/90-wall aggregate ceiling; RSS remains 768 MiB and output 8 MiB.
Other leaves retain their previous phase allocations. This explicit phase
rebalance uses the existing aggregate allowance, not a larger leaf budget.

CV085 first attempt was not checked: generation reached its 28-CPU-second
phase guard (28.533122 CPU seconds, 486,785,024 peak RSS bytes). No certificate
or Lean acceptance follows from that run. The one structural repair separates
the same target's construction and evaluation stages into two ordinary checked
helper nodes. The construction helper exports just the actual shared codes,
normalization, low pattern and cutoff tail. The evaluation helper consumes
those exact codes and data, constructs the finite value and proves both bounds.
The final node composes these stages. This reduces the deeply nested witness
scope; no formula is assumed, no ancestor replay is skipped, and neither the
target nor resource ceilings is changed. Preserve the failed v1 observation.

CV085 v2 also remains `not_checked`: its generation observation reports
`cpu_limit` at 28.140506 CPU seconds and 352,288,768 peak RSS bytes. A zero
process return code does not override the supervisor's resource failure.
There is no accepted CV085 certificate or independent Lean result. The
ordinary one-repair allowance is exhausted; do not retry unchanged or increase
its guard silently. Review assembly/replay cost before proposing another run.

CV085 explicit protocol review (2026-10-02, after independent CV086-CV088
HA/Lean checks): v2 produced complete `native_generated` output with 435
nodes, 42,054 ordinary constructors and a 2,727,157-byte canonical bundle,
but the supervisor correctly rejected the 28.140506 CPU-second generation.
Do not retroactively accept that output. Authorize one additional,
protocol-only v3 observation: redistribute its previous 28/28 CPU allocation
to 30 generation / 26 fresh replay, with the same 40/40 wall allocations.
Including both hard-limit margins, the reservation is still 58<=60 CPU
seconds, and the 90-wall/768-MiB/8-MiB aggregate policy is unchanged. The
producer, target, proof bodies, positive checker and negative controls are
unchanged from v2. This is a recorded one-leaf exception to the normal
one-repair attempt rule, not a new global retry allowance. Require complete
successful generation, fresh ordinary replay and then fresh Lean; preserve
both failed observations regardless of the v3 result. If v3 fails, stop its
retries and retain the unresolved assembly/performance task.

CV085 v3 outcome: accepted ordinary generation and complete fresh replay,
using 28.187952 and 21.721790 CPU seconds respectively, 52.215444 seconds
overall wall time, and at most 388,579,328 peak RSS bytes. All 435 retained
nodes / 42,054 ordinary constructors were checked. Fresh independent Lean
and eight isolated regressions pass, including complete archived replay,
exact witness/field binding, forged-root and forged-power-uniqueness rejection.
Both earlier failures remain unaccepted. Twenty protocol regressions pass
after the explicit phase redistribution (8 existing warnings).

Checked independent leaf CV086 (first-attempt HA/fresh Lean, seven regressions,
46 nodes / 2,038 constructors): for any supplied atanh coefficient table A of
length k+1, supplied base-three Horner value y, and supplied p=3^(k+1),
prove 3*y+3*d<=d*p. First prove the general finite invariant y+d<=d*3^k
for a zero-headed table with every coefficient <=2*d, by Horner induction
using 3*h+c+d<=3*(h+d). Reuse CV066's proved zero head and coefficient
bound; do not construct a replacement table or assume logarithmic accuracy.
Multiplication by three and the actual power-step equation put the result
at the same scaling as CV085. This proves the finite inner input is <=1
once the separately required denominator nonzero fact is supplied, and is
needed for an outer-factorial tail ratio <=1/2 after the first term.

Checked CV087 finite outer-tail estimate (first-attempt HA/fresh Lean, eight
regressions, 121 nodes / 5,970 constructors): for supplied terms T satisfying
((j+1)*d)*T[j+1]=x*T[j], with d nonzero and x<=d, construct the actual
slice starting at m+1 of length N+1, its sum s, and prove s<=2*T[m+1].
The recurrence horizon is exactly (m+1)+N, sufficient for all consumed
adjacent pairs. Prove h*T[j+1]<=T[j] whenever h<=j+1 by natural order
monotonicity and guarded cancellation of d. On the shifted tail h=2 is
available because m+1>=1. Transport both decoded slice entries and all
index bounds explicitly, then use CV068's checked finite geometric-sum
theorem. This is not yet decay of the first omitted term with m, nor an
infinite-series remainder. Those are separate next obligations.

Checked CV088 cutoff decay (first-attempt HA/fresh Lean, seven proof regressions,
136 nodes / 7,001 constructors): on the same supplied recurrence with x<=d and
d nonzero, prove by induction that 2^k*T[k+1]<=T[0] at every in-range
index. The base is the guarded first-step inequality T[1]<=T[0]. For the
successor, use CV087's exact ratio lemma with h=2, the actual previous beta
entry, and the supplied power-step equation. Construct p=2^m and decode
T[m+1], then instantiate CV087's actual finite tail. From p*T[m+1]<=T[0]
and s<=2*T[m+1], prove p*s<=2*T[0]. Export the power, slice, first term,
ratio predicate, sum and both bounds. This is a uniform finite remainder
estimate for every extra horizon N; an analytic limit still requires its
separate constructive interpretation.

CV087 solver observation: the exact frozen natural ratio helper was sent to
a sequential 18-CPU/25-wall/512-MiB classical portfolio before HA generation.
Z3 returned `unsat` with a proof-shaped log in 0.035160 child CPU seconds;
E hit its three-second CPU guard; Vampire was unavailable on PATH. Total
measured child CPU was 3.102608 seconds with 12 seconds reserved. No solver
certificate was imported and no success was inferred from unavailable or
timed-out engines. The HA body separately reconstructs the needed ordered
arithmetic and guarded cancellation, then the independent Lean checker
checks the same ordinary proof data. Three observer regressions pass.

Checked refinement CV089 (first-attempt HA/fresh Lean, seven proof regressions,
40 nodes / 1,774 constructors): for arbitrary supplied coefficients
bounded by 2*d, prove every base-three Horner endpoint y at length r obeys
y+d<=d*3^r, without requiring a zero head. The empty endpoint is zero and
the step is the already checked CV086 step-bound lemma. Then restrict the
same actual atanh table to a cutoff M and transport its 2*d coefficient bound
to the actual tail slice. Combine the resulting bound for its tail value u
with the actual split z=3^r*x+u and actual power multiplication. This yields
an explicit truncation-difference estimate (at most 3^(1-M) after normalizing)
without identifying independently constructed code numbers. Use M=2*k+1
to obtain a 9^(-k) bound. A separate finite exponential continuity estimate
and the constructive analytic interpretation are still required; neither
CV085 nor CV088 closes IR079-IR081 or IR072 by itself.

CV089 integration also reran all twenty controller/fresh-Lean protocol tests
successfully (8 existing warnings). No definition, kernel rule, resource
ceiling or ancestor trust boundary changed.

CV090 checked assembly (first-attempt HA, fresh Lean, seven proof regressions;
142 nodes / 7,798 constructors, no new induction): on an arbitrary supplied atanh table A of
length M+N, construct its actual slice B from M of length N, prefix value x,
tail value y and whole value z at base three, and powers p=3^M, q=3^N and
h=3^(M+N). Reuse CV062's constructor, not independently guessed codes.
Transport CV066's coefficient bound to B with the actual affine index
M+1*i=M+i and the proved shifted strict bound. CV089 then gives y+d<=d*q.
Use actual power addition to prove h=p*q, and retain z=q*x+y from CV062.
The natural arithmetic helper must derive both h*x<=p*z and
p*z<=h*x+d*h: first prove p*z=h*x+p*y, then use y<=d*q and monotonicity.
Include zero lengths and d=0 in this natural theorem; do not silently divide.
For nonzero d, these exact witnesses later express monotonicity and a
normalized truncation difference bounded by 3/p. Preserve the atanh table
as a premise, with a general bounded-prefix helper if useful; no definition
may contain the desired difference inequality or an infinite-limit claim.

CV090's arithmetic helper also had a bounded solver observation: Z3 returned
unknown with no proof, and E reached its three-CPU-second limit. Neither result
was proof authority. Native deterministic reconstruction succeeded under the
unchanged HA limits; all three solver-observer guards also pass.

CV091 checked rational interpretation (first-attempt HA, fresh Lean, seven
regressions; 146 nodes / 8,619 constructors, no new induction): from d!=0 and the supplied atanh
prefix of length M+N, retain CV090's actual prefix and whole values x,z and
p=3^M,h=3^(M+N). Prove p and h nonzero from their actual power predicates,
then d*p and d*h nonzero. Lift CV090's two natural cross bounds by 3*d and
normalize products with checked associativity, commutativity and distributivity.
Use the existing IRatLe definition and positive-order theorem to prove
3*x/(d*p)<=3*z/(d*h)<=(3*x+3*d)/(d*p), exporting the actual value and power
witnesses. This records the finite truncation error <=3/p with valid rational
denominators; no analytical logarithm identity or independent-code equality
is inferred. Empty prefixes and tails remain permitted.

CV092 checked normalization (first-attempt HA, fresh Lean, seven proof
regressions plus three observer guards; 37 nodes / 2,025 constructors): for independently supplied atanh tables
A and B at the same length N with respective common denominators d and e,
and supplied Horner values x and y at any common base t, prove e*x=d*y.
At each coefficient i, prove e*A[i]=d*B[i]: split the existing finite
even/odd coefficient definitions, use CV026's checked parity separation for
mixed cases, and cancel the explicitly nonzero odd index in the odd/odd case.
Build the weighted coefficient relation with weights e,0,d and reuse CV035's
all-row linearity on the supplied histories, duplicating A's history for the
zero-weight input. Do not construct replacement codes or assume their equality.
The natural cross identity allows zero denominators/base and empty prefixes;
rational equality will separately require nonzero denominators. No new
definition or induction was added, and no convergence is claimed. Z3 reported
unsat for the frozen coefficient helper with proof-shaped output; E hit its
bounded CPU limit. Neither solver output was admitted or translated as proof
authority. The native HA certificate independently reconstructs the parity
cases, guarded cancellation and actual supplied-history transport.

CV093 checked supplied truncation (first-attempt HA, fresh Lean, seven proof
regressions and three observer guards; 155 nodes / 9,793 constructors): remove the shared-table restriction from
CV091. Given independent atanh tables A at length M and B at length M+N,
their nonzero scales d,e, supplied values x,z and supplied powers p=3^M,
h=3^(M+N), prove both valid rational bounds
3*x/(d*p)<=3*z/(e*h)<=(3*x+3*d)/(d*p). Restrict B to M, apply CV092 to its
actual prefix value and x, and transport CV090's constructed whole value and
powers to the supplied values by proved uniqueness. Multiply the two natural
bounds by 3*d, substitute the cross-scale identity and normalize products;
prove each denominator nonzero before applying rational order. Preserve both
input codes and allow empty parts. No new definition/induction or identification
of code numbers is needed. The claim remains a finite Cauchy estimate, not
the logarithm identity or IR072.

CV094 planned finite exponential continuity core: for two supplied natural
term tables A,B with the same head a0 and the actual recurrences
(j+1)*d*A[j+1]=x*A[j] and (j+1)*d*B[j+1]=y*B[j], assume d!=0 and y=x+g.
Prove, at every available positive index k+1, both A[k+1]<=B[k+1] and
d*B[k+1]<=d*A[k+1]+g*B[k]. This is a denominator-cleared finite-difference
bound, not a derivative/limit axiom. One induction suffices: the first index
is an exact equality; the step multiplies the previous inequality by x,
uses x<=y, substitutes B's previous recurrence, and cancels only the proved
nonzero (k+2)*d. Both supplied histories and their common actual head remain
premises; zero x,g,a0 are allowed. An arbitrary finite sum transport theorem
will then give d*sum(B)<=d*sum(A)+g*sum(B's preceding terms), followed by the
already checked finite exponential majorant. Keep this distinct from the
later cross-denominator and analytic-continuity interpretation.

CV094 first HA generation and complete fresh replay passed (13.742815 and
5.766014 CPU seconds), but independent validation is not yet complete.
Fresh Lean v1 stopped in the unchanged Semantics module at its 15-second wall
guard, after only 3.318940 CPU seconds; no CV094 certificate check was reached.
The previous CV093 run compiled that same module in 1.991999 wall seconds.
Retain the incomplete report; it is not evidence against or for CV094's target.
Regression v1 passed its first two tests then hit the 35-second wall guard
while repeatedly expanding the same immutable definition registry in a
six-mutation formula test. The single changed test repair expands that registry
once and varies only the caller formula; exact registry identity has its own
test. No producer, theorem, kernel, dependency or resource guard changes.
Do not count CV094 among fully checked statements until Lean and all tests pass.

The repaired validation v2 passed its first five tests, including the changed
formula-mutation test, then aborted when the OS process-accounting command
itself timed out. It produced no complete validation receipt. The manual
`exp-term-difference-validation-v2-local-diagnostic.json` records only those
observed terminal facts and explicitly grants no proof authority. The runtime's
exception path killed and reaped its owned worker; user applications were not
altered. Subsequent process accounting and CV095's supervised first HA run
completed successfully (19.202652-second generation and 10.878578-second fresh
replay). Schedule one fresh Lean build for the newly accepted CV095 together
with the still-pending CV094 certificate, retaining the original incomplete
build and all unchanged per-stage limits. This is an infrastructure recheck
after observed accounting recovery, not a proof repair or widened budget.

That combined Lean v2 build also stopped at Semantics before checking either
certificate. Both CV094 and CV095 remain HA-only, outside the fully checked
count. Do not repeat the same failing build under unchanged machine conditions.
Continue source-level and bounded HA work while waiting for a material change
in local availability; do not disable process accounting or raise limits.

CV095 planned reusable finite-sum comparison: define only the pointwise
weighted order between decoded prefixes, NatLinearBound(alpha,beta,gamma,A,B,C,N).
Its conservative expansion contains Lt, BetaAt and Le, but no sums or analytic
claim. Prove that three supplied actual length-N sums satisfy the same weighted
order gamma*sum(C)<=alpha*sum(A)+beta*sum(B). Use one ordinary induction on
the common prefix length, actual sum decomposition and ordered distributivity.
Include empty prefixes and zero weights. This transports CV094's pointwise
term errors to the finite sum needed for exponential continuity; it does not
assume that the sum bound holds by definition.

CV096 next finite exponential sum continuity assembly: preserve two supplied
recurrence tables A,B, their common head a0 and actual sums s,t through index N.
For d!=0, y=x+g and y<=2*d, prove s<=t and
d*t<=d*s+9*(g*a0). Construct both actual tails from index one using checked
sum splitting, identify the supplied totals by sum uniqueness, and apply
CV094/CV095 to the tail tables and the actual length-N B prefix. The latter
sum is <=t by actual decomposition, while CV071 proves t<=9*a0. Normalize
the two common-head sums and retain all scale factors. Zero argument, gap,
head and degree N are allowed. No new induction, rational division or analytic
limit is needed for this natural bound. A later normalization stage must still
relate independently scaled rational exponential computations.

CV097 next normalization constructor: given an actual recurrence at argument
x/d, its head a0 and supplied sum s through index N, construct the actual
coefficient-scaled table U[j]=c*A[j] and its sum t. Prove the recurrence for
denominator d*f and numerator f*x, actual head c*a0, and t=c*s. Reuse the
checked arbitrary weighted-prefix constructor with weights c,0 and the same
input twice; use the checked weighted-sum equality, not an equality between
independent code numbers. This natural computation law permits zero d,f,c.

CV095, CV096 and CV097 now have successful first-attempt HA generation and
complete fresh replay. CV095's eight regressions and CV096's seven regressions
passed in the isolated sum-continuity validation. The later rescaling-and-term
validation completed all 23 isolated tests: seven for CV097, seven for CV094,
and nine solver-interface guards. This completes CV094's interrupted regression
validation without changing its producer or resource caps. No independent Lean
success is claimed for these statements.
CV096 retains 147 actual ancestor/helper nodes (9,501 ordinary constructors);
CV097 retains 114 (5,945 constructors). Both add zero new inductions.

CV098 planned cross-normalization assembly: instantiate CV097 twice to compare
different nonzero denominators d,e and arbitrary initial scales a0,b0 (including
zero). Scale A by B's head and B by A's head, putting both at denominator d*e
with numerators e*x and d*y and shared head a0*b0. Transport the second
recurrence denominator e*d and the first head b0*a0 by checked commutativity,
not code equality. From d*y=e*x+g and y<=2*e, apply CV096 to the constructed
sums and substitute the proved identities u=b0*s and v=a0*t. The exact output
is b0*s<=a0*t and
(d*e)*(a0*t)<=(d*e)*(b0*s)+9*(g*(a0*b0)). Keep both denominator nonzero guards;
derive the common-denominator nonzero proof explicitly. No new induction or
definition is needed. This is still a natural finite inequality, before
positive-head rational normalization and the later analytic interpretation.

CV098's first generation and complete fresh replay passed; all seven focused
regressions passed, including actual ancestor-body replay and forged-alignment
rejection. Its 156 nodes contain 10,698 ordinary constructors. Lean remains
pending, so it is not added to the fully checked count.

CV099 planned rational normalization: additionally require a0!=0 and b0!=0.
Prove IRatLe(s,0,a0,t,0,b0) and
IRatLe(t,0,b0,(d*e)*s+(9*g)*a0,0,(d*e)*a0). These say
s/a0<=t/b0<=s/a0+9*g/(d*e). Prove the product denominator nonzero and normalize
the exact two cross-products from CV098 before invoking the existing checked
rational-order lemma. Reuse ND0382/ND0444 unchanged; no new alias, axiom or
analytic interpretation is needed. Both actual term tables and supplied sums
remain inputs. Zero argument, gap and degree are allowed, but zero heads are
excluded explicitly rather than silently treated as rational denominators.

CV099's first HA generation and complete fresh replay passed (21.297918 and
11.853424 CPU seconds). The first isolated regression passed, but the second
process aborted when /bin/ps exceeded the unchanged one-second accounting
deadline. No complete validation report was written. Retain the manual terminal
diagnostic; do not count it as a completed test run or Lean evidence. Hold
further heavy checks until process accounting is available again, with no
increase to any timeout, CPU or memory cap and no change to user applications.
A subsequent read-only accounting probe completed in 0.120585 seconds for 738
process rows. CV100's exact target/helper and owned-endpoint preflight also
completed. Resume one bounded worker at a time after that observed recovery;
retain CV099's interrupted test run and the unchanged resource guards.

CV100 planned supplied finite truncation: from one actual exponential recurrence
through (m+1)+N, head a0, supplied prefix sum s through m, supplied whole sum t
through (m+1)+N, and actual p=2^m, prove s<=t and p*t<=p*s+2*a0, assuming
d!=0 and x<=d. CV088 constructs the actual tail from index m+1 with p*tail<=2*a0.
Use arbitrary sum splitting and actual affine-sum uniqueness to identify that
tail with the difference of the two supplied totals; do not identify table codes.
The later independent-computation Cauchy bound will combine this omitted-term
error with CV098's cross-argument error. No infinite tail is a definition here.

CV100's first HA generation and complete fresh replay passed (22.064930 and
12.120257 CPU seconds), with 155 nodes / 8,327 ordinary constructors and zero
new inductions. The later combined validation observed all seven CV099 tests
and three CV100 tests pass, then process accounting timed out again. Retain
the terminal diagnostic; no complete report or independent Lean success is
claimed. The test controller is being repaired to preserve prior validated
process records in an explicitly failed/incomplete report on a supervision
exception. This does not change the supervisor, limits or proof acceptance.

CV101 planned two-error assembly: compare A through degree m and B through
degree m+N+1 at independent arguments x/d<=y/e<=1, with actual nonzero d,e,
cross-gap d*y=e*x+g, initial scales a0,b0, sums s,t, and p=2^m. Construct the
actual length-(m+1) B-prefix sum r. Restrict B's recurrence to m with proved
index bounds, apply CV098 to s,r and CV100 to r,t, then add the two explicit
errors by ordered polynomial arithmetic. The natural target is
b0*s<=a0*t and
(d*e)*(p*(a0*t))<=(d*e)*(p*(b0*s))+(9*(g*p)+2*(d*e))*(a0*b0).
Its eventual rational reading is s/a0<=t/b0<=s/a0+9*g/(d*e)+2/p, but this
natural target still allows zero heads and does not assert rational validity.
The arithmetic helper is an exact frozen target for the detached solver
portfolio; native HA reconstruction, not a solver status, supplies authority.

CV101's first generation reached the unchanged 40-second wall guard after
21.193990 CPU seconds. It produced no accepted certificate or fresh replay;
retain the v1 observation. The single changed repair memoizes only the immutable
expected source path/size/hash inventory, avoiding repeated recursive diamond
traversals. Every invocation still rereads and hashes every actual file and
rejects mutations. Complete actual ancestor-body replay and all resource guards
remain unchanged. Dedicated regressions compare the full pin map against the
original recursive calculation and verify rejection after a source mutation.
The exact theorem/helper ASTs and proof factories are unchanged. Detached Z3
returned unknown with no available proof; E reached its wall guard. Neither
observation has admission authority, and the changed producer does not relabel
those historical observations as a current proof.

CV101 v2 generation and complete fresh replay passed (12.927321 and 9.304143
CPU seconds; generation wall 19.509987 seconds), retaining 189 nodes / 13,723
ordinary constructors. Its nine proof/metadata regressions and CV100's seven
regressions now pass; ten solver-interface guards also pass. CV099 has a new
complete seven-test receipt. The reporting repair passes four adverse tests.

The unchanged CV099 replay subsequently dropped from 23.19 to 3.46 wall seconds,
providing a material host-availability change for the pending Lean recheck.
Fresh Lean v3 compiled all nine modules, checked the exact CV094-CV101 payloads,
and rejected both hostile controls in 19.013155 seconds. Semantics compiled in
1.515666 wall / 0.791668 CPU seconds, under the original limits. Thus all eight
statements now enter the fully checked local count. Preserve the earlier
incomplete observations; no resource or kernel guard was weakened.

CV102 checked rational two-error conclusion: additionally require the two
initial scales a0,b0 nonzero. Derive p!=0 from the actual Pow(2,m,p) proof, prove
(d*e)*(p*a0)!=0, and normalize CV101's two natural inequalities into
IRatLe(s,0,a0,t,0,b0) and
IRatLe(t,0,b0,(d*e)*(p*s)+(9*(g*p)+2*(d*e))*a0,0,(d*e)*(p*a0)).
The common denominator is not cancelled without its nonzero proof. Reuse the
existing valid-rational order definition unchanged, with no hidden accuracy
condition. This remains a finite quantitative comparison, not the analytic
identification of the requested constant or a closed IR parent.

CV102 first-attempt generation and fresh replay used 4.650570 and 3.107643 CPU
seconds, respectively. The exact certificate has 193 nodes / 14,188 ordinary
constructors, with no new induction. Fresh Lean compiled all nine modules,
accepted the same bytes and rejected both negative controls in 10.556890 wall
seconds. Seven proof regressions and four reporting guards passed separately.

Checked SQ001 audits exact reuse of floor-square-root totality and monotonicity
from the sealed Bertrand certificate. Keep the historical definition PD0051
unchanged, including its Le/Lt DAG. Select only the 30 required inert ancestor
rows before ordinary decoding, and prove unconditional existence and uniqueness
with no new induction. The old 14,368,763-byte archive is untrusted source data,
not an exception to the 8 MiB final-certificate decoder limit. Then derive
dyadic brackets and a computational approximation graph; none of those later
accuracy or analytic interpretation claims is a clause of FloorSqrt.
SQ001 generation/fresh replay used 0.839485 / 0.202283 CPU seconds; the pruned
ordinary certificate has 31 nodes / 990 constructors and 29,866 bytes. Fresh
Lean accepted the exact bytes with both negative controls after nine fresh
module builds. All eight focused tests pass, including a forged historical
totality body and a reduced final-node ceiling. Published definition hashes
bind template text; independent AST hashes and roundtrips bind its semantics.

Checked SQ002 contract: for any supplied actual FloorSqrt(n,s), a*a<=n and n<b*b
imply a<=s and s<b. Both alternatives of natural decidable order have ordinary
HA proofs; neither classical excluded middle nor real square roots are added.
This will locate the floor root of 2*d*d between d and 2*d for d>0, before
specializing d to an actual power of two.
SQ002 passed first-attempt HA, fresh Lean and seven regressions: 16 nodes /
541 constructors, with no new induction or definition. Generation/fresh replay
used 0.287352 / 0.237395 CPU seconds.

SQ003 constructs the unique actual floor root of 2*d*d for every d!=0 and
proves d<=s<2*d and s!=0. Its separate polynomial-order estimate was confirmed
by Z3 (`unsat`, proof-shaped output); E was inconclusive and Vampire unavailable.
These are untrusted classical hints, not imported proofs. The first ordinary
HA attempt rejected the final tuple assembly: the parser's frozen conjunction
is left-associated, whereas the generic constructor was right-associated.
The one changed repair preserves the exact target AST and constructs that
left-associated tuple. Keep the original failure and bounded diagnostic;
neither the kernel nor any cap changes.
SQ003 v2 passed generation/fresh replay (0.423341 / 0.339631 CPU seconds),
fresh Lean and seven proof regressions. Its certificate has 42 nodes / 1,426
constructors. Eleven observer guards separately pass; the solver observation
retains its pre-repair source snapshot and is never acceptance evidence.

Checked SQ004 constructs the actual dyadic pair (d,s) at every k, including zero.
Local conservative ND0446 DyadicSqrt2(k,d,s) expands only to Pow(2,k,d) and
FloorSqrt(2*d*d,s). Its DAG reuses the complete BetaAt/Product/Repeat/Pow branch
and Le/Lt/FloorSqrt branch. Separately prove both values nonzero, d<=s<2*d and
uniqueness of the output pair across all actual encodings. No real-number
interpretation, convergence or accuracy condition is smuggled into the graph.
Its certificate has 139 nodes / 6,614 constructors. First-attempt generation
and fresh replay used 0.739637 / 0.518786 CPU seconds; fresh Lean and seven
proof tests pass. Twenty existing HA/Lean protocol tests also pass separately.

Checked SQ005: if FloorSqrt(n,s), FloorSqrt(n*e*e,t) and e!=0, then
s*e<=t<(s+1)*e. Prove strict multiplication by a positive factor from the
existing successor-product and order bodies; use square comparison for the
two supplied roots. Zero n and s are allowed. First-attempt HA, fresh Lean
and seven regressions pass; 24 nodes / 913 constructors, no new induction.

Checked SQ006: preserve supplied DyadicSqrt2(k,d,s) and
DyadicSqrt2(k+l,q,t); construct the actual intervening Pow(2,l,e), prove
e!=0 and q=d*e, then s*e<=t<(s+1)*e. Zero precision and increment are allowed.
Next transport those integer bounds into valid-rational nested intervals
and an explicit dyadic Cauchy error, proving each denominator nonzero.
SQ006 passed first-attempt HA, fresh Lean and seven proof regressions:
131 nodes / 6,594 constructors, generation/replay 0.853524 / 0.565929 CPU
seconds. No new induction, definition, code equality or analytic assumption.

Checked SQ007: derive valid-rational lower-endpoint monotonicity s/d<=t/q
and upper-endpoint antitonicity (t+1)/q<=(s+1)/d for the same supplied
computations. Retain the conservative dyadic graph; reuse IRatValid and IRatLe
unchanged and merge only their actual two-definition dependency subset into
the power/floor-root DAG. Prove each actual power denominator nonzero.
First-attempt HA, fresh Lean and seven regressions pass: 134 nodes / 6,824
constructors, generation/replay 3.214694 / 1.381623 CPU seconds.

Checked SQ008: retain both supplied computations and prove d!=0, q!=0,
s*q<=t*d<=s*q+q. This is the explicit finite rational modulus
0<=t/q-s/d<=1/d=2^-k for every increment l, including zero. Eliminate only
the signed-rational zero terms through ordinary equality proofs and use the
successor numerator to obtain the upper bound. No real limit is a premise.
SQ008's first producer run failed before kernel checking because it passed
specialization arguments to the Axiom constructor. The one repair uses the
existing forall-elimination API for PA3, preserving the exact statement.
The repaired HA generation/replay passed (3.246639 / 1.378010 CPU seconds),
and all seven proof tests pass. Independent fresh Lean subsequently accepted
the same certificate (136 nodes / 6,947 constructors) and rejected both
negative controls. Retain v1 as failed evidence.

Checked SQ009: for every supplied DyadicSqrt2(k,d,s), prove d!=0, s!=0,
d<=s<2*d and s*s<=2*d*d<=s*s+2*(2*d). The general integer-floor residual
lemma is n<=s*s+(s+s), obtained from the strict floor upper bound by an
ordinary square-successor identity and successor-order cancellation. This
supplies a quantitative square error, not an assumed real sqrt(2) identity.
First-attempt HA generation/replay used 0.538298 / 0.394990 CPU seconds;
fresh Lean and seven proof regressions pass, with 53 nodes / 2,160 constructors.
Z3 confirmed the exact floor-residual helper as an untrusted classical hint;
E was inconclusive. Twelve observer guards passed separately at this checkpoint.
Checked SQ010 combines the direct modulus with the supplied positivity/range
facts to prove 0<=d/s-q/t<=1/d=2^-k. The exact natural upper bound is
d*(d*t)<=d*(q*s)+s*t, and d,s,t are proved nonzero. First-attempt HA
generation/replay used 0.825644 / 0.619629 CPU seconds; fresh Lean and seven
proof regressions pass, with 149 nodes / 7,782 constructors. Z3 and E were
inconclusive; thirteen observer guards pass separately. Neither lemma assumes
a reciprocal real identity, closes an IR parent, or changes any resource cap.

Checked AP001 constructs the dyadic pair, positive odd-reciprocal scale,
actual coefficient table, Horner value and base-three power. ND0447 is the
intermediate computation-only graph NatSqrt2LogArgument, with the exact
dependency cone of DyadicSqrt2, NatAtanhPrefix, NatHornerValue and Pow.
The quotient denominator is proved nonzero and its value at most one separately;
do not call this graph CApprox or assert its analytic interpretation.
First-attempt HA generation/replay used 3.703622 / 1.670167 CPU seconds;
fresh Lean and eight regressions pass, with 161 nodes / 8,262 constructors.
The dependency cone has sixteen definitions; shared Le/Lt descriptions may
differ, but IDs, parameters, exact expansion source/AST and dependencies must
match. Z3/E were inconclusive for the bounded arithmetic observation; fourteen
observer guards pass separately. No untrusted hint replaces HA replay.

Checked AP002 constructs the actual degree-k+2 exponential sample of that
quotient. Local computation-only ND0448 NatSqrt2ExpSample retains every input
code, weight/term code, head, exact factorial, denominator power, normalization
equation and sum. Output y/w0 has w0!=0 as a separately proved conclusion.
The same terms satisfy the exact adjacent recurrence and all-index factorial
normalization. First-attempt HA generation/replay used 6.987754 / 3.186838 CPU
seconds; fresh Lean and eight regressions pass, with 186 nodes / 10,686
constructors and a twenty-three-definition DAG. This leaf is exact logical
composition of two replayed totality proofs; there is no new solver search,
induction, accuracy definition or analytic identity claim.

Checked AP003 proves that two supplied NatSqrt2LogArgument graphs at
the same precision and positive independent coefficient scales give the same
rational quotient. Prove the dyadic values and base-three powers equal,
retain both separate coefficient-table codes, prove both quotient denominators
nonzero, and establish the exact cross-product equality using CV092.
First-attempt HA generation/replay used 4.299003 / 2.030254 CPU seconds;
fresh Lean and seven proof regressions pass, with 156 nodes / 8,603
constructors. Z3 confirmed the polynomial identity as a detached classical
hint; E was inconclusive. Fifteen observer guards pass separately.

Checked AP004 derives positive input/output denominators, input <= 1,
the recurrence and all-index normalization for every supplied sample graph
under D!=0, not just the witnesses chosen by AP002. Reuse the actual CV030
weight invariant and CV070 recurrence/normalization helpers. The bounded
Lucas archive audit found factorial uniqueness but no factorial-nonzero
endpoint; prove the latter by one explicit HA induction using the already
retained zero/successor factorial laws. No archive-limit increase is needed.
First-attempt generation/replay used 6.731077 / 2.872868 CPU seconds;
fresh Lean and seven proof regressions pass (152 nodes / 7,916 constructors).
Twenty HA/Lean protocol tests also pass, with eight existing warnings.

Checked AP005 proves rational output-value independence for two supplied
complete samples at the same precision and positive independent scales.
Use AP004's laws on each supplied graph and AP003's quotient equality;
apply CV098 in both directions at zero gap and conclude by antisymmetry.
Keep both output denominators nonzero, and never equate independent beta
codes, coefficient scales or factorial normalization heads.
First-attempt HA generation/replay used 10.444127 / 5.036939 CPU seconds;
fresh Lean and seven proof regressions pass, with 228 nodes / 16,692
constructors. Z3 confirmed the exact zero-gap arithmetic hint, E was
inconclusive, and sixteen observer guards pass separately. No new induction
or definition is needed. Canonical PR computation and accuracy remain open.

Checked precision bridge AP006: the quotient inputs need
not be monotone. The finite logarithm increases while the reciprocal root
decreases; their product can move in either direction. For supplied graphs at
k and k+l, write U=(3*x)*d, V=(D*p)*s, Z=(3*z)*q, W=(E*h)*t. Prove V,W!=0
and the asymmetric natural estimates

    V*Z <= W*U + ((3*D)*(E*h))*(s*t),
    d*(W*U) <= d*(V*Z) + V*W.

Their rational readings are Z/W-U/V<=3/p and U/V-Z/W<=1/d. They retain the
actual powers p=3^(S(2*k)) and d=2^k. Use this exact dependency route:

1. Prove S(2*(k+l))=S(2*k)+2*l by distributivity and successor addition.
   Align only the fine coefficient-prefix length, Horner length and power
   exponent before applying CV093 to the two actual supplied encodings.
2. Extract CV093's cross-multiplied natural log bounds using SQ008's checked
   positive-rational order helper; reuse only the existing IRatValid/IRatLe
   definition cone. Distribute the upper numerator without changing scales.
3. Apply SQ010 to the two supplied dyadic subgraphs, and SQ009 to get q<=t.
   Use CV086 to prove 3*x<=D*p. AP004's argument helper supplies V,W!=0.
4. Prove one generic polynomial/order lemma: from a*e<=b*c<=a*e+r,
   a<=c, q*s<=d*t, d*(d*t)<=d*(q*s)+s*t, and q<=t, derive
   (c*s)*(b*q)<=(e*t)*(a*d)+r*(s*t) and
   d*((e*t)*(a*d))<=d*((c*s)*(b*q))+(c*s)*(e*t).
   Substitute a=3*x,b=3*z,c=D*p,e=E*h,r=(3*D)*(E*h).
   For the first inequality multiply the log upper bound by q*s, then use
   q*s<=d*t and q<=t on the two summands. For the second multiply the
   reciprocal error by a*e, then use a*e<=b*c and a<=c on its two summands.
   Observe the exact helper with the bounded solver portfolio and reconstruct
   it by ordinary multiplication/addition monotonicity and deterministic AC.
5. Only after this input bridge, combine same-degree finite continuity in both
   argument orders with CV100's longer-horizon tail. CV102 alone cannot be
   applied assuming that the shorter-horizon input is always the smaller one.

The canonical primitive-recursive trace, odd-sum identification, analytic
interpretation and the final irrationality argument remain distinct obligations.

AP006 passed first-attempt HA generation/replay in 10.112797 / 4.686381 CPU
seconds, independent fresh Lean in 12.709294 wall seconds, and all eight proof
regressions (188 nodes / 13,317 constructors). Seventeen observer guards also
pass. Z3 and E were inconclusive on the detached arithmetic helper; its actual
ordinary HA reconstruction, not a solver verdict, supplies acceptance.

Checked AP007 contract: two-sided same-degree finite
exponential continuity with an explicit common error multiplier C. For
supplied recurrences at x/d and y/e, positive d,e, inputs x<=d,y<=e,
heads a0,b0 and actual length-(N+1) sums s,t, assume

    C*(d*y) <= C*(e*x)+R,
    C*(e*x) <= C*(d*y)+H.

Conclude

    C*((d*e)*(a0*t)) <= C*((d*e)*(b0*s)) + 9*(R*(a0*b0)),
    C*((d*e)*(b0*s)) <= C*((d*e)*(a0*t)) + 9*(H*(a0*b0)).

C and the heads may be zero in this natural-arithmetic theorem; actual sample
applications separately prove every rational denominator nonzero. Keeping C
is important: AP006's reciprocal error is already multiplied by its actual
coarse dyadic denominator. Do not silently cancel it or assume it divides
the independent logarithm scale. For the AP006 application take C=d_coarse,
R=d_coarse*((3*D)*(E*h))*(s*t), H=V*W.

Use constructive total order of the two natural cross-products e*x,d*y.
In either branch obtain its actual additive gap g from the Le witness.
Prove C*g<=R (or H) by substituting the gap equation, distributing C and
cancelling common addition through the existing equality-cancellation body.
Apply CV098 in that orientation, multiply its error inequality by C, and use
the bound on C*g. The opposite-direction inequality follows from its proved
monotonicity plus a nonnegative error allowance. Normalize swapped products
d*e and a0*b0 by ordinary AC proofs, not by identifying independent codes.
This uses decidable natural order, not excluded middle or Markov for reals.

AP007 passed first-attempt generation/replay in 4.479951 / 2.259935 CPU seconds,
fresh Lean in 11.003059 wall seconds, eight proof regressions and eighteen
observer guards. Its bundle has 164 nodes / 11,662 constructors and no new
induction or definition. The bounded archive audit found natural total order
and equality cancellation already in CV098's actual cone. Only the five
existing definitions Le, Lt, BetaAt, Sum and NatScaledExpRecurrence are exposed
by this local interface. Z3 confirmed scaled-gap cancellation; E was
inconclusive. A sandbox-denied process-accounting attempt is retained as a
non-authoritative diagnostic; the permitted run kept all existing limits.

Checked AP008: before applying the preceding estimate to complete sample
graphs, prove its generic unequal-horizon form. Preserve the two recurrences
at degrees m and (S m)+N, their actual sums, and p=2^m. Construct the length-S m
sum of the actual longer table and restrict its recurrence using CV101's
checked helper. Compose AP007 with CV100. Writing D=d*e, the conclusions are

    p*(C*(D*(a0*t))) <= p*(C*(D*(b0*s))) + (9*(p*R)+2*(C*D))*(a0*b0),
    C*(D*(b0*s)) <= C*(D*(a0*t)) + 9*(H*(a0*b0)).

All variables are natural. The interpretation as errors 9*R/(C*d*e)+2/p and
9*H/(C*d*e) requires separately proved positivity of C and the normalization
heads; those conditions must not be silently inferred in the generic lemma.
This generic finite bridge is not yet an assertion about the intended real.

AP008 passed first-attempt HA generation/replay in 10.130146 / 4.722829 CPU
seconds, fresh Lean in 12.259559 wall seconds and eight proof regressions.
Nineteen observer guards pass separately. The exact bundle has 197 nodes /
14,850 constructors, no new induction, and only the eight existing definitions
in the recurrence/sum/power cone. Z3 and E were inconclusive; deterministic
HA composition and independent Lean supplied acceptance.

Checked AP009 instantiates this bridge for actual samples at k and k+S l.
Keep a supplied r=2^(k+2), align (k+S l)+2=S(k+2)+l, and derive the AP008
scaled premises from AP006. Let F=V*W and B=((3*D)*(E*v))*(s*t). Prove
p*B=3*F by ordinary multiplicative AC. Multiply the forward output bound by
p, factor d*F and cancel it only after proving it nonzero; cancel F from the
reverse bound. This removes all arbitrary coefficient scales from the result:

    (p*r)*(w0*o) <= (p*r)*(v0*y) + ((9*3)*r+2*p)*(w0*v0),
    d*(v0*y) <= d*(w0*o) + 9*(w0*v0).

Also derive nonzero d,p,r,w0,v0. The rational readings are 27/p+2/r for
increase and 9/d for decrease. The source numeral 9*3 is left as an exact
ordinary product, not an unproved evaluation oracle. Same-precision pairs
remain covered by AP005; joining that case and a uniform dyadic budget follows.

AP009 passed first-attempt generation/replay in 13.518009 / 7.489345 CPU
seconds, fresh Lean in 11.460638 wall seconds and eight proof regressions.
Twenty observer guards also pass. Its 273-node / 26,093-constructor bundle
uses no new induction or definition and retains the same 23-definition
computation DAG. Both detached solvers were inconclusive on normalization;
all cancellation and AC steps were reconstructed and independently checked.

Checked AP010 supplies reusable joint monotonicity of actual powers:
Le(a,b), b!=0, Pow(a,k,x), Pow(b,k+l,y) imply Le(x,y). Prove same-exponent
base monotonicity by explicit induction using the actual zero/successor power
laws. Construct b^k and b^l, use the checked power-addition equality, and prove
that multiplication by a nonzero natural cannot decrease a number. The zero
base a, zero exponent and zero increment must remain covered; positivity of b
is essential. This avoids routing elementary power comparison through unrelated
Horner witnesses. It will give d<=p and d<=r for AP009's actual powers.
A deliberately generous uniform error ((9*3)+2)/d suffices for the fixed
precision shift k=n+8; no tighter constant is needed to close that budget.

AP010 passed first-attempt HA generation/replay in 9.331439 / 4.123647 CPU
seconds, fresh Lean in 10.705555 wall seconds and seven proof regressions.
Twenty-one observer guards pass separately. It has 126 nodes / 6,042 ordinary
constructors and one new induction, exposing only six existing power/order
definitions. AP006 contains two actual left-multiplication monotonicity bodies;
the explicit CV071 archive owner resolves that ambiguity without treating a
name or hash as authority. Both solvers were inconclusive on the detached step.

Checked AP011 specializes the general theorem to the supplied powers
Pow(2,k,d), Pow(3,S(2*k),p), Pow(2,k+2,r), deriving d,p,r!=0, d<=p and d<=r.
Prove the exact exponent equality S(2*k)=k+S k from distributivity before
applying AP010; do not replace an actual supplied power witness.

AP011 passed first-attempt HA generation/replay in 9.369534 / 4.174920 CPU
seconds, fresh Lean in 12.179837 wall seconds and seven proof regressions.
Twenty-two observer guards pass separately. The bundle has 128 nodes / 6,144
constructors, no new induction or definition. Z3 confirmed the exact exponent
alignment; E was inconclusive. The ordinary reconstructed identity was replayed.

Checked AP012: the uniform-error arithmetic is: for p,r!=0, d<=p, d<=r,

    (p*r)*X <= (p*r)*Y + (A*r+B*p)*h
    implies d*X <= d*Y + (A+B)*h.

Multiply by d, bound d*A*r by A*p*r and d*B*p by B*p*r, factor p*r, and
cancel it only after proving it nonzero. Apply with A=9*3, B=2 to AP009's
actual samples. Construct the cutoff power internally using actual power
totality. Enlarge the reverse coefficient 9 to (9*3)+2 using the checked
positive-factor lemma and natural addition. This gives a uniform strict-
precision bound without any new definition or analytic assumption.

AP012 passed first-attempt HA generation/replay in 18.356903 / 10.095987 CPU
seconds, fresh Lean in 14.494532 wall seconds and eight proof regressions.
Twenty-three observer guards pass separately. The exact bundle has 282 nodes /
27,341 constructors, with no new induction or definition. Both solvers were
inconclusive on the denominator-reduction helper; ordinary HA reconstructed
every inequality and cancellation. The auxiliary cutoff is constructed inside
the proof, not required as a premise of the final supplied-sample statement.

Checked AP013: join l=0 (AP005 value independence) and l=S j (the uniform strict-
precision bound) by the existing constructive zero/successor split. In the
zero case transport only the fine precision k+0=k; in the successor case
transport only k+l=k+S j. Keep both complete supplied graphs and both positive
coefficient scales. The result should constructively bound all precision
increments, including zero, by ((9*3)+2)/2^k. The canonical PR computation,
real identification and final irrationality argument still remain separate.

AP013 passed first-attempt HA generation/replay in 23.351091 / 12.945787 CPU
seconds, fresh Lean in 12.643821 wall seconds and seven proof regressions.
Fourteen HA-wave and six fresh-Lean protocol tests also pass (eight existing
warnings). The bundle has 297 nodes / 29,263 constructors and no new induction
or definition. No new solver target was needed for this constructive case
composition; both actual predecessor certificates and the equality transports
were fully replayed. This is the finite all-increment error theorem, not yet
the analytic or irrationality theorem.

Following AP013, use the fixed shift n+8 without introducing a unary literal
256. Checked AP014 is the small fixed-power threshold

    forall v. Pow(2,8,v) -> ~v=0 /\ Le((9*3)+2,v).

Construct an actual x=2^5. Five applications of the existing power-successor
law and its zero law prove x=32; a bounded closed-arithmetic reconstruction
with values at most 32 proves 3+((9*3)+2)=32. Thus (9*3)+2<=32. Apply AP010
with base 2, exponents 5 and increment 3, after proving 5+3=8 by the same
small arithmetic reconstruction. This yields 32<=v and hence the threshold;
power nonvanishing gives v!=0. No exact value 256, expanded eight-step beta
table, numeral-limit change, or new induction is needed. Any integer
evaluation used by a generator only chooses an ordinary HA derivation.

AP014's first attempt was rejected at the fixed five-step unrolling helper:
an existential-elimination proof cannot synthesize its type inside a
congruence constructor. One repair moved the eliminations outside the
equality chain, resolving all hypotheses in their live scopes. The failed
attempt and bounded diagnostic are preserved. Repaired generation/fresh
replay passed in 9.385784 / 4.167826 CPU seconds, fresh Lean in 11.967207 wall
seconds, with nine proof regressions and twenty-four solver-observer guards.
The bundle has 130 nodes / 7,170 constructors; no new induction, definition,
axiom, or raised limit. Z3 confirmed the exact small threshold target before
the proof repair; E was inconclusive. The solver observation is only a hint.

Checked AP015 uses actual sample graphs at k=n+8 and k+l. Construct
q=2^n and v=2^8 by existing power totality. The coarse dyadic subgraph supplies
the actual d=2^(n+8); the checked addition law gives d=q*v. Apply AP013's
uniform bounds and AP014's (9*3)+2<=v. From

    d*X <= d*Y + ((9*3)+2)*h

derive v*(q*X)<=v*(q*Y+h), and cancel only the proved nonzero v. Do this in
both directions, retaining actual positive q and both output denominators.
The resulting natural bounds q*X<=q*Y+h and q*Y<=q*X+h express the desired
finite error <=2^-n for all finer samples, including equal precision. They
still do not supply the canonical PR trace or identify its limit with the
intended real constant; those are subsequent obligations, not definitions.

AP015 passed first-attempt HA generation/fresh replay in 27.900420 /
15.476446 CPU seconds, fresh Lean in 15.273019 wall seconds and eight proof
regressions, plus twenty-five solver-observer guards. Its 303 nodes / 30,878
constructors contain no new induction, definition or axiom. Both external
solvers were inconclusive on the general cancellation helper. The ordinary
proof and every reachable dependency body were checked independently. The
generation remained below, but close to, its unchanged 28-CPU-second ceiling;
subsequent units must remain small rather than relaxing that ceiling.

The odd-sum identification is isolated in small checked units. Checked
AP016 constructs the actual odd-index affine slice B[j]=A[1+2*j] of a
supplied atanh table of length S(2*k), and proves

    j<k -> (2*j+1)*B[j]=2*D,
    j<=k -> A[2*j]=0.

The even/odd separation must use CV026's actual arithmetic proof; the slice
must be constructed, not postulated. Empty slices k=0 and zero scale D are
allowed. Reuse the conservative NatAffineSlice definition ND0411; introduce
no analytic or accuracy abbreviation.

AP016 passed first-attempt HA generation/fresh replay in 2.622240 / 1.414206
CPU seconds, fresh Lean in 7.773566 wall seconds and seven proof regressions.
It retains 113 nodes / 5,016 constructors and a minimal six-definition DAG,
with no new induction, definition or solver target. The reused parity and
affine-slice bodies were fully checked, not accepted as handles.

Checked AP017 proves the generic paired-Horner bridge: for an actual odd-index slice,
zero even entries through 2*k, and actual supplied Horner computations,

    Horner(A,t,S(2*k),x), Horner(B,t*t,k,y) -> x=t*y.

An explicit induction compares every pair of steps in A with one step in B;
the base consumes A[0]=0, and the successor consumes the odd entry and the
following zero even entry. This is the finite reindexing bridge toward the
stated odd-reciprocal logarithm algorithm. Power normalization, canonical
trace correctness and identification of its limit remain separate gates.

AP017 passed first-attempt full HA generation/fresh replay in 2.998614 /
1.579132 CPU seconds, fresh Lean in 9.549207 wall seconds, seven proof tests
and twenty-six solver-observer guards. The minimal retained proof has 40
nodes / 1,598 constructors and one explicit induction; all seven definitions
are reused unchanged. Z3 confirmed the exact paired-step arithmetic; E was
inconclusive. Countermodels in the regressions demonstrate why omitting the
terminal even-zero premise would make the theorem false.

Checked AP018 supplies the matching actual-power normalization:

    Pow(t,S(2*k),p) -> Pow(t*t,k,q) -> p=t*q.

It first proves Pow(t,2*k,p) and Pow(t*t,k,q) imply p=q, by one induction on k
using two actual successor decompositions on the left and one on the right.
It then consumes the final successor. Zero base and zero exponent are allowed;
no cancellation or nonzero premise is needed. First-attempt HA generation
and fresh replay used 8.402001 / 4.324970 CPU seconds; fresh Lean used
10.671387 wall seconds. Seven proof regressions, fourteen HA-wave protocol
tests and six fresh-Lean protocol tests pass (eight existing warnings).
The retained certificate has 27 nodes / 1,209 constructors, one explicit
induction and five unchanged definitions. No new solver target was needed.
Checked AP019 combines this with AP016/AP017 at t=3, constructs the odd
Horner value and actual power at base 9, proves 3*3=9 by ordinary bounded
arithmetic, and identifies the exact finite quotient
3*x/(D*p)=3*y/(D*q). Every rational denominator is proved nonzero.
First-attempt HA generation/replay used 13.273273 / 6.796753 CPU seconds;
fresh Lean used 13.519125 wall seconds. Seven proof regressions and 27
solver-observer guards pass. The certificate has 142 nodes / 7,152
constructors, fourteen unchanged definitions and no new induction.
Z3 confirmed the quotient helper; E was inconclusive. The first archive
audit detected an absent power-positivity endpoint in CV061; its corrected
explicit owner is the actual AP010 archive. Both audit records are retained.
This still does not identify the infinite logarithm or a canonical PR trace.

Scheduling note: the AP019 regression supervisor was launched before the
fresh-Lean session had been explicitly reaped. That session then returned
successful verification. This handoff is an exception to the intended
sequential-launch discipline, not an increased resource limit or additional
proof authority; subsequent heavy launches require a terminal session result.

Checked AP020 preserves all AP019 outputs and constructs an actual term
table T with Sum(T,k,y), plus for every j<k and actual entry c=T[j] an actual
positive r=3^(2*j+1) and IRatEq(3*c,0,D*q,2,0,(2*j+1)*r).
It uses CV039's actual weighted-sum construction and weight/power invariant,
aligns its endpoint and power by uniqueness, then applies AP018 to the odd
power. This avoids a new induction or definition. It identifies the finite
odd reciprocal sum, not its infinite logarithm limit. First-attempt HA
generation/replay used 13.887047 / 7.218190 CPU seconds; fresh Lean used
14.615021 wall seconds. Seven proof regressions and 28 solver-observer
guards pass. The certificate has 169 nodes / 9,774 constructors and 17
unchanged definitions. Z3 confirmed the arithmetic helper; E was inconclusive.

Checked AP021 retains the complete supplied exponential sample and its
actual sum, and identifies every term t/head with U^j/(j!*V^j), constructing
the factorial and both power values. All denominators are proved nonzero;
zero numerator and zero index are permitted. AP004 supplies normalization
and positivity, CV070 supplies the finite witnesses, and AP019 supplies the
ordinary positive-rational equivalence constructor. First-attempt HA
generation/replay used 12.252430 / 6.388703 CPU seconds; fresh Lean used
9.989859 wall seconds. Seven proof regressions and 29 solver-observer
guards pass. The certificate has 160 nodes / 8,400 constructors and 25
unchanged definitions. No new induction or definition is used. Z3 confirmed
the normalization helper; E was inconclusive.

Checked AP022 fixes the coefficient scale to N!, rather than an unspecified
common multiple. It proves every positive i<=N divides the supplied factorial
by one induction on N, then supplies CV025's existing prefix constructor with
that explicit common-multiple property. The root constructs the factorial,
positive scale, actual coefficient table and zero-initial-coefficient law,
including N=0. It does not claim canonical beta codes or the whole PR trace.
First-attempt HA generation/replay used 5.083190 / 2.711614 CPU seconds;
fresh Lean used 10.088160 wall seconds. Seven proof regressions, fourteen
HA-wave protocol tests and six fresh-Lean protocol tests pass (eight existing
warnings). The certificate has 124 nodes / 5,880 constructors and ten unchanged
definitions. No new solver target was needed for the logical induction.

Checked AP023 reconstructs the whole log/root/exponential sample with
D=(2*k+1)! and retains D!=0 in the conclusion. It reuses AP001's bound and
CV070's actual exponential constructor; no new definition or induction is
necessary. First-attempt ordinary HA generation/replay, independent fresh Lean
and all seven regressions pass. The certificate has 190 nodes / 10,891
constructors and the unchanged 23-definition sample DAG. Do not rename this
finite construction a complete CApprox trace certificate.

Checked AP024 proves constructive decisions of natural equality, Le, Lt,
BetaAt, Pow, Factorial, Sum and FloorSqrt. A deterministic term schema uses
actual totality and uniqueness proofs; one induction supplies factorial
uniqueness. First-attempt HA generation/replay used 5.179679 / 2.742578 CPU
seconds, and fresh Lean used 10.275602 wall seconds. Seven proof regressions,
fourteen HA-wave guards and six Lean guards pass (eight existing warnings).
The certificate has 153 nodes / 7,160 constructors and ten unchanged
definitions. No classical or Markov axiom and no solver verdict is trusted.
This is not a completed CApprox verifier or a PR extraction theorem.

Checked AP025 decides NatAtanhCoefficient, NatHornerValue and DyadicSqrt2
for arbitrary supplied candidates, including invalid scales and zero inputs.
It consumes the actual parity, coefficient, Horner-totality/uniqueness and
atomic-decision bodies. Its first-attempt HA generation/replay used 5.835000 /
3.087357 CPU seconds; fresh Lean used 9.397706 wall seconds. All seven proof
regressions pass. There are 146 nodes / 6,803 constructors, twelve unchanged
definitions and no new induction. No full-table, record or PR extraction
theorem follows merely from these component decisions.

Checked AP026 decides every supplied NatAtanhPrefix, NatExpWeightTable and
NatPowerWeightedPrefix. Its deterministic row schema constructs the actual
beta/power values, decides the row property and transports it by uniqueness;
one bounded-induction schema is instantiated for each of the three prefixes.
Invalid tables, empty prefixes, zero scales and the last row are covered.
HA generation/replay used 5.801242 / 3.053451 CPU seconds; fresh Lean used
9.491723 wall seconds. All seven regressions pass, including last-row
mutations and forged-body rejection. The certificate has 133 nodes / 6,360
constructors, ten unchanged definitions and three new inductions. No solver
call or new trusted inference rule is introduced by these proof generators.

The computation-verifier bridge is now split explicitly:

1. AP024: decisions for the basic total functional computations (checked).
2. AP025: coefficient parity, Horner-value and dyadic-graph decisions
   (HA, independent fresh Lean and regressions checked).
3. AP026: finite-prefix decisions for actual coefficient/weight/term tables
   using bounded induction, actual beta decoding and value uniqueness
   (HA, independent fresh Lean and regressions checked).
4. AP027: decide the supplied full sample, prescribed scale and positive
   input/output denominators (HA, fresh Lean and regressions checked).
5. Construct and decode a genuine finite record, prove output independence,
   and establish the specified primitive-recursive execution/record bridge.

Step 5 is not implied by the supplied-sample decision. Analytic identification,
auxiliary-vector construction, interpolation and final separation remain
separate obligations after this bridge.

AP027 passes first-attempt full ordinary HA generation/replay (6.000019 /
3.319943 CPU seconds), fresh Lean (10.999899 wall seconds) and eight proof
regressions, plus fourteen HA-wave and six Lean protocol guards. Its certificate
has 174 nodes / 8,788 constructors, 23 unchanged definitions and no new
induction. Its exact target decides Factorial(S(2*k),D), D!=0, the unchanged
NatSqrt2ExpSample graph and w0!=0 together for all sixteen supplied inputs.
The first local-constructor audit rejected the attempted nested disjunction
eliminand, which the bidirectional checker cannot synthesize. One repair
replaced it with sequential CPS branches: inspect each synthesizable decision,
and reject the matching actual conjunct on the first no branch. The exact
target is unchanged, all repaired local constructors check, and both audits
are retained. No logical rule or resource limit changed. The earlier AP025
two-conjunct schema remains frozen and valid for its existing uses; the new
sequential schema handles longer conjunctions without an inferability hole.

AP028 introduces the local conservative
NatSqrt2ApproxRecord(n,up,ud,rb,rc), with two beta-code components
and thirteen internal witnesses for AP023's remaining fields. Decode all
fifteen fields in AP002 order, with up in the sum slot and ud in the head
slot. At k=n+8 require the actual factorial scale, positive D, original
NatSqrt2ExpSample and positive output head. No accuracy, uniqueness of code
numbers, infinite-series identity or irrationality is a definition clause.
Prove totality by AP023 and a fixed fifteen-field beta-prefix construction,
using actual beta_extend bodies and exact small-index order proofs. Then use
AP027 and beta uniqueness to decide supplied records, and AP005 to prove
rational output independence. A single-code packing/decoding bridge, if used
for the original IRD09 trace parameter, must be proved separately; two code
components are not silently identified with one natural number. Finally prove
the stated bounded/primitive-recursive evaluator connection before claiming
the canonical CApprox program. This avoids freezing an unused opaque trace.

AP028's prospective definition and all fifteen prefix constructors pass their
local diagnostic audit. The frozen ordinary HA proof passes first-attempt
generation/replay in 7.671121 / 4.513059 CPU seconds. The local alias ND0449
has the exact conservative expansion and genuine BetaAt/Factorial/sample
definition dependencies; it adds no kernel symbol. Independent fresh Lean
passes in 11.140073 wall seconds, along with all eight focused regressions,
fourteen HA-wave protocol guards and six Lean guards (eight existing warnings).
The certificate has 206 nodes / 14,914 constructors and 24 definitions,
including the one new conservative alias; no new induction is needed.
The definition is local and is not an Alpha admission or an asserted
certified PR CApprox program.

The AP029 target is implemented and checked by HA, independent fresh Lean
and all eight focused regressions:
`forall n up ud rb rc. NatSqrt2ApproxRecord(n,up,ud,rb,rc) or
not NatSqrt2ApproxRecord(n,up,ud,rb,rc)`.
For each supplied code pair, decode the thirteen internal fields using the
actual beta totality theorem; keep the two output slots fixed by up/ud.
Generate a fifteen-field tuple decision from AP024's beta decision, and a
whole-body decision from that tuple decision and AP027 at k=n+8. A separate
transport helper must open any purported record, equate each internal field
with the decoded value using beta uniqueness, and transport its entire
computation body by equality substitution. The yes branch supplies the
thirteen existential fields; the no branch uses that transport helper. This
is constructive elimination of functionally determined witnesses, not an
unbounded existential search or a general Markov principle. Keep decision
subproofs synthesizable via named helper nodes or sequential CPS branches.
After AP029, AP030 should derive valid output denominators and cross-multiplied
output equality for two records at the same precision using the actual AP005
sample-independence body; beta code numbers need not be equal. Only then
transport the existing finite precision/error bounds and close the separate
bounded evaluator/primitive-recursive execution obligation.

AP029's exact endpoint and four local-constructor audits pass. Full ordinary
HA generation/replay passes on the first attempt (9.907658 / 5.586797 CPU
seconds), including every retained ancestor. The transport helper uses the
thirteen actual beta-uniqueness equalities to replace every competing field
in the complete computation body; no canonical code-number assumption or
unbounded witness search is introduced. Tests include an actual encoded
precision-zero sample, an alternative code for the same fifteen fields and
re-encoded corrupted scalar fields; these Python computations are calibration,
not a replacement for either formal checker.

Fresh Lean verifies AP029 in 13.048867 wall seconds; all eight tests pass,
including the actual encoded precision-zero example, noncanonical-code
example and corrupted-field cases. Its certificate has 178 nodes / 9,739
constructors and the unchanged 24-definition DAG, with no new induction.
No code, precision or memory limit was enlarged.

AP030 passes its exact endpoint/local-constructor audit, first-attempt
ordinary HA generation/replay (12.692934 / 7.451179 CPU seconds), independent
fresh Lean (13.280302 wall seconds) and all seven focused regressions. The
fourteen HA-wave and six Lean protocol guards also pass. Its certificate has
229 nodes / 16,810 constructors, 24 unchanged definitions and no new induction.
It opens two genuine records at the same precision and replays AP005 to prove
ud!=0, vd!=0 and vd*up=ud*vp. No equality between beta-code numbers is asserted.

The finite-error transport AP031 is checked: from records at n and
n+l, construct the actual power r=2^n and the two inequalities
`r*(ud*vp) <= r*(vd*up)+ud*vd` and its reverse. Open both record bodies and
apply the actual AP015 theorem with positive scales. First prove
`(n+l)+8=(n+8)+l` using the ordinary addition associativity/commutativity
bodies, then transport the finer sample graph to AP015's exact precision.
Preserve the actual power and all nonzero denominators. This remains a
finite all-finer error statement; it does not itself identify the analytic
limit with the requested real power or complete the PR evaluator bridge.

AP031's original run hit the generation CPU guard and remains `not_checked`.
A bounded cost audit found that recursively recomputing the source closure
alone consumed 5.923815 CPU seconds per invocation. The single changed repair
captures the exact existing 270-file closure and streams each frozen file once
per call, checking both its length and digest. The existing historical 14 MB
input is hashed in 64 KiB chunks up to its frozen length; the generated proof
limit remains 8 MiB. A first preflight caught that historical input exceeding
the draft reader's 2 MiB per-file assumption; no proof worker or v2 output was
started before the exact-length reader was corrected. There is no stale cache,
trusted theorem handle, changed proof target, kernel change or cap increase.

AP031 v2 passes ordinary HA generation/replay in 8.879292 / 6.961769 CPU
seconds, independent fresh Lean in 15.740063 wall seconds, eight focused
regressions and all twenty controller/Lean protocol guards (eight existing
warnings). It has 305 nodes / 31,023 ordinary constructors, the unchanged
24-definition DAG, and no new induction. The original failed run and the
source-cost/closure audits are retained separately from successful evidence.

AP032 now targets the analytic bottleneck's finite bridge. At N=K+2, reuse
CV085's actual computation and evaluation stages, and connect their exact
product table to CV073's recurrence at argument (3*x)/(d*p). Export a positive
head h, the same actual sum y, the original logarithm coefficient/Horner/power
computations, and the two bounds y/h<=2+9*(2/3)^N and
2<=y/h+3^(-(K+1)). Prove the input denominator positive and the argument at
most one using CV086. This is not yet exp(log(2))=2: the limit and identification
steps remain separate. The local constructor/endpoint audit passes. CV085's
redundant root is not replayed, but
every reachable body of its two actual stage proofs is retained and checked.

AP032 passes first-attempt ordinary HA generation/replay in 20.352214 /
18.326638 CPU seconds, fresh Lean in 20.180024 wall seconds, all eight focused
regressions and all twenty protocol guards (eight existing warnings). It has
439 nodes / 42,538 constructors, 53 unchanged definitions and no new induction.
The flat source closure is revalidated from actual bytes on every invocation.
The ordinary 28/20-second generation/replay caps are unchanged; CV085's older
phase exception was not transferred to this theorem.

AP033 is being implemented with explicit HA inductions for
(n+2)*2^n<=2*3^n and n+1<=3^n. At N=18*r+2 these imply the two concrete budgets
9*r*2^N<=3^N and r<=3^(N-1). Selecting r=2^n later will make both AP032 errors
at most 2^(-n), without an unspecified sufficiently-large cutoff. This coarse
auxiliary index does not change the fixed approximation program; no practical
extracted-running-time claim is made and no huge powers are materialized by
the certificate generator. The two induction constructors and all local
arithmetic helpers pass their exact-goal audit. Full first-attempt HA
generation/replay passes in 3.606270 / 1.971251 CPU seconds, fresh Lean in
11.897147 wall seconds, all ten focused regressions and all twenty protocol
guards (eight existing warnings). The certificate has 46 nodes / 2,824
constructors and six unchanged definitions. Z3 and E did not resolve either
exported arithmetic helper within the detached short budgets; Vampire was
unavailable. These are retained untrusted observations, not proof evidence.

AP034 constructs r=2^n and applies AP032 at K=18*r, then AP033 to its exact
three powers. It converts both valid-rational bounds to natural inequalities,
scales by r and cancels only the proved positive comparison powers. The
target retains the coefficient prefix, Horner value, input power, recurrence,
head and actual sum, with `r*y<=(r*2)*h+h` and its reverse. Thus the intended
finite log/exponential sum is within 2^(-n) of two. No limit passage or
identification with log(2) is silently substituted for these computations.
All local constructors and exact archived endpoints pass their diagnostic
audit. First-attempt full HA generation/replay passes in 20.670973 / 18.782700
CPU seconds; fresh Lean passes in 19.915861 wall seconds. All eight focused
regressions and twenty protocol guards pass (eight existing warnings).
The certificate has 452 nodes / 44,672 constructors and 53 unchanged
definitions, with no new induction or phase-limit change.

AP035 targets a reusable missing link for the analytic interpretation:
from any supplied NatScaledExpRecurrence(d,x,T,N) and actual head T[0]=h,
prove `(T[j]*j!)*d^j=h*x^j` for every j<=N and every actual factorial/power
computation. The index induction uses the actual recurrence and previous
entry; multiplication transports the identity without cancelling d. Thus
zero d, x, h and N are all included. Rational validity remains separate.
The exact constructor audit and first-attempt full HA generation/replay pass
(2.025068 / 1.199961 CPU seconds); fresh Lean passes in 8.561404 wall seconds.
All eight focused regressions and twenty protocol guards pass (eight existing
warnings). The certificate has 36 nodes / 1,812 constructors, nine unchanged
definitions and one new induction, with no phase-limit changes.

AP036 applies this normalization to AP021's actual generic term-construction
body, not its specialized sample root. For positive d and h it constructs
j!, d^j and x^j, proves the term denominator positive, and identifies T[j]/h
with x^j/(j!*d^j) for every j<=N. The actual table, head and finite horizon
are preserved. The eleven-definition cone reuses existing exact identities;
no new abbreviation or infinite-series assertion is introduced. Its local
constructor and exact endpoint audit and full first-attempt HA generation/replay
pass (11.919506 / 6.213200 CPU seconds). Fresh Lean passes in 9.536309 wall
seconds; eight focused regressions and twenty protocol guards pass (eight
existing warnings). The certificate has 130 nodes / 6,260 constructors and
no new induction. No resource ceiling was changed.

AP037 implements the finite shift law gamma*(C*B)[i+1]=alpha*(A*B)[i],
assuming C[0]=0 and gamma*C[j+1]=alpha*A[j] only for j<=i. All three input
lengths can differ, padded values are explicit and both scalars may be zero.
The proof decodes the actual diagonals, proves their zero head and shifted
entry relation, and uses actual affine slicing plus weighted finite-sum
linearity. The first endpoint audit found the affine-sum-existence body was
not retained in CV010; assigning its actual CV008 archive fixes the ownership
claim. The second audit checks all endpoints and all four local constructors.
First-attempt full HA generation/replay passes in 0.885685 / 0.692194 CPU
seconds, fresh Lean in 7.901638 wall seconds, all nine focused regressions
and twenty protocol guards pass (eight existing warnings). The certificate
has 131 nodes / 6,988 constructors and eleven unchanged definitions, with
no new induction. No full exponential addition claim follows yet.

AP038 derives ((i+1)*d)*C[i+1]=(x+y)*C[i] for the actual convolution of
supplied recurrences with arguments x/d and y/d, for i<N and input length
N+1. It constructs both Euler tables and their actual convolution coefficients,
then applies CV007's Euler product rule, AP037's shift law and actual
coefficient commutation. All local constructors and exact archived endpoint
matches pass. Zero d and zero arguments remain allowed: no cancellation is
used. The finite cutoff is essential and has a concrete counterexample at
i=N. Z3 resolves the frozen arithmetic helper; E does not resolve it within
the short budget and Vampire is unavailable. The ordinary constructor checks
the helper independently; no solver output becomes authority. First-attempt
full HA generation/replay passes in 3.679385 / 2.207764 CPU seconds, fresh Lean
in 9.752631 wall seconds. Ten focused regressions and twenty protocol guards
pass (eight existing warnings). The certificate has 147 nodes / 8,608
constructors and ten unchanged definitions, with no new induction.

AP039 constructs the actual length-N+1 Cauchy table and its sum from the
two supplied exponential recurrences and heads. Its head is proved a0*b0;
AP038 supplies its added-argument recurrence and AP035 supplies all-index
factorial normalization. Zero d, x, y, heads and N are included. Every local
constructor and endpoint match passes. First-attempt full HA generation/replay
passes in 3.910103 / 2.406764 CPU seconds; fresh Lean in 11.360881 wall seconds.
All eight focused regressions and twenty protocol guards pass (eight existing
warnings). The certificate has 163 nodes / 9,894 constructors and fifteen
unchanged definitions, with no new induction. The
output sum is NOT claimed to be the full product of the input sums; the
degree-one example (1+X)^2 has truncated sum 3, whereas 2*2=4.

The planned quantitative addition bridge can avoid a new binomial library:
on actual long recurrence tables of degree 2*N+1, compare the rectangular
product of the two degree-N sums with the degree-N and degree-(2*N+1)
convolution sums. Local coefficient equality gives the lower endpoint;
monotonicity under input-prefix extension and CV048's full convolution sum
identity give the upper endpoint. AP039 identifies both bounding prefixes
with the added-argument factorial series. Existing explicit exponential
tails can then bound the gap when x+y<=d. AP041 now checks the sandwich;
AP042 is the explicit finite error step, not an analytic addition identity.

AP040 proves coefficient monotonicity when the same two beta-coded inputs
are extended from lengths L,M to N,O with L<=N and M<=O. Its proof derives
padded-entry order, diagonal-product order and actual finite-sum order via
CV095, for every coefficient index including empty inputs. All exact
endpoint matches and local constructors pass. First-attempt full HA generation/
replay passes in 2.166554 / 1.272759 CPU seconds; fresh Lean in 9.397770 wall
seconds. Eight focused regressions and twenty protocol guards pass (eight
existing warnings). The certificate has 46 nodes / 2,330 constructors, with
no new induction. The nine-definition cone reuses the existing ND0445
pointwise bound and does not add an inequality to a computation definition.

AP041 constructs the long-input convolution through length L+L and all four
sums, for L<=M, proving sum(C,L)<=sum(A,L)*sum(B,L)<=sum(C,L+L).
The lower comparison uses actual low-coefficient locality and finite prefix
sum order; the upper comparison uses AP040 and actual full-product identity
CV048. The proof preserves the input codes and includes L=0. All exact
endpoint matches and five local constructors pass. First-attempt full HA
generation/replay passes in 1.987122 / 1.658853 CPU seconds; fresh Lean in
9.540856 wall seconds. Eight focused regressions and twenty protocol guards
pass (eight existing warnings). The certificate has 191 nodes / 11,747
constructors and eleven unchanged definitions, with no new induction.
This is still a finite sandwich, not an exponential error estimate.

AP042 applies that sandwich with L=n+1 and M=2*n+2. The PA4 identity
(n+1)+(n+1)=((n+1)+n)+1 aligns the actual Cauchy table with AP039's recurrence
and head. CV100 then proves s<=u*v and 2^n*(u*v)<=2^n*s+2*(a0*b0),
for supplied actual input recurrences through degree 2*n+1 and x+y<=d,
with d nonzero. Every table and sum is retained as finite evidence. All
exact endpoint matches and the local constructor pass. First-attempt full HA
generation/replay passes in 5.292036 / 3.588148 CPU seconds; fresh Lean in
10.674105 wall seconds. Eight focused regressions and twenty protocol guards
pass (eight existing warnings). The certificate has 243 nodes / 16,475
constructors and thirteen unchanged definitions, with no new induction.
The archive audit's first run had an incorrect metrics-helper
import; its corrected second run passes, and both diagnostics are preserved.

AP043 transports this finite error to a third, independently supplied
added-argument prefix, retaining all three supplied codes, heads and short
sums. The constructed Cauchy table remains internal; AP005's actual
same-value helper identifies its short sum by cross multiplication after
CV101's restriction to degree n. This removes a code/normalization obstacle
to using the product estimate with existing logarithm witnesses. First-attempt
full HA generation/replay passes in 5.727777 / 3.904619 CPU seconds; fresh Lean
in 12.755525 wall seconds. Eight focused regressions and twenty protocol guards
pass (eight existing warnings). The certificate has 278 nodes / 21,182 ordinary
constructors and thirteen unchanged definitions, with no new induction.
The initial constructor audit incorrectly assigned sum uniqueness to CV071;
the corrected owner CV003 and all local constructors pass in v2. Both audits
are retained. Z3 and E returned unresolved results under their unchanged
three-second limits; Vampire was unavailable. No solver proof was imported.
The ordinary HA constructors supply the proof; no infinite addition identity
is asserted.

AP044 is the constructed half-argument bridge. From an actual degree-n
sum for x/d<=1, construct positive factorial-weighted terms for x/(2*d)
through degree 2*n+1, retain their full and short sums, and apply AP043 to
the short sum squared. The supplied whole-argument code and head stay fixed.
The recurrence is transported by a proved denominator/numerator scaling law,
not an assumption about real exponentials. The first definition-cone audit
omitted the existing Sum definition; it is restored, with the failed record
preserved. All four local constructors and exact endpoint matches pass in v2.
First-attempt full HA generation/replay passes in 6.059322 / 4.310308 CPU
seconds; fresh Lean in 11.426846 wall seconds. Eight focused regressions and
twenty protocol guards pass (eight existing warnings). The certificate has
303 nodes / 23,493 constructors and twelve unchanged definitions, with no
new induction. No square-root or logarithm identity is asserted.

AP045 is the isolated natural-arithmetic error-combination step. Given
b,p nonzero, r<=p, a*v<=b*s, p*(b*s)<=p*(a*v)+2*(b*a), and the two
reference-to-two bounds, prove r*s<=(r*2)*a+3*a and (r*2)*a<=r*s+a.
Its precision-weakening helper reduces the p-scaled error to r by cancelling
only the supplied positive p; upper and lower transport cancel only b.
All five local constructors and exact arithmetic endpoint matches pass.
First-attempt full HA generation/replay passes in 3.380747 / 1.859247 CPU
seconds; fresh Lean in 8.914264 wall seconds. Nine focused regressions and
twenty protocol guards pass (eight existing warnings). The certificate has
28 nodes / 1,558 constructors and only the existing Le definition, with no
new induction. This lemma constructs no exponential or root.

AP046 supplies the remaining cutoff domination without needing a separately
proved n<=2^n comparison for the outer precision. Its generic helper proves
n+1<=2^n by one ordinary HA induction on actual supplied powers. AP033's
existing cutoff helper gives r<=18*r+2, hence r<=p for a supplied actual
p=2^(18*r+2). All exact endpoint matches and four local constructors pass;
full HA generation/replay passes in 3.767907 / 2.076043 CPU seconds. Fresh Lean
passes in 11.680975 wall seconds. Eight focused regressions and twenty protocol
guards pass (eight existing warnings). The certificate has 37 nodes / 1,434
constructors and six unchanged definitions, with one new induction. Zero r
is included and no huge ground power is materialized.

AP047 now combines the half-argument square error with AP034's actual
log/exponential witnesses. At degree M=18*2^n+2 it constructs p=2^M and proves
2^n<=p. Positivity permits cancellation of the supplied head in the integer
cross bounds. The result is an actual half-log exponential sum U/h with
2-1/2^n<=(U/h)^2<=2+3/2^n. No enormous powers are instantiated as ground data.

Implemented AP047 construction:

1. Apply AP034 at n, naming its witnesses
   `(r,d,lb,lc,x,q,eb,ec,b,v)`. Set M=18*r+2 and H=(M+1)+M.
   Keep the actual atanh and Horner computations for the argument 3*x/(d*q).
2. Construct a genuine p with Pow(2,M,p) by the existing power-existence
   theorem. AP046 proves p!=0 and r<=p, without a large ground computation.
3. Apply AP044 with denominator d*q, numerator 3*x, whole-argument code
   (eb,ec), degree M, head b and sum v. Name its witnesses
   `(wb,wc,ab,ac,h,f,t,z,u)`; here t is the denominator-power witness,
   z the degree-H whole sum, and u the degree-M short sum.
4. Apply AP045 at `(r,p,b,h*h,u*u,v)`. Its product inequalities are AP044's
   two final fields; its reference inequalities are AP034's two final fields.
   Its positive b guard is AP034's supplied positive exponential head.
5. Return r,d,lb,lc,x,q and the nine half-argument witnesses, retaining the
   actual logarithm data and all half-argument computation/normalization
   fields, and prove
   `Le(r*(u*u),(r*2)*(h*h)+3*(h*h))` and
   `Le((r*2)*(h*h),r*(u*u)+(h*h))`.
   The auxiliary eb,ec,b,v,p may stay internal; discarding those outputs is
   not discarding their dependency-closed proof bodies.
6. Freeze the exact statement and reused definition cone, check local
   constructors and all owned endpoints, then perform bounded full HA,
   fresh Lean and adversarial regressions. Source/archive metrics for AP034
   and AP046 are retained in `half-log-square-archive-audit-v1.json`.

AP047's first generation succeeded, but fresh replay reached its unchanged
20-second CPU cap (20.133701 CPU). The failed `shared-wave-half-log-square-v1`
remains `not_checked`. Two capped cost diagnostics found 18.065069 seconds
in ordinary row checks, plus repeated definition/source setup. A separate
inert audit found only ten unused dependency binders; none were removed.
The single changed repair snapshots the exact existing 17-definition cone
and source closure, reparses each template with the unchanged hygienic
constructor, checks its exact AST, and streams every actual source once.
An independent audit compares all definitions and source pins to the old
recursive producers. This reduces measured definition/target and source
setup to 0.011557 / 0.028867 CPU seconds. It changes no theorem or proof byte:
the bundle SHA-256 remains
`bcfc3286e107e3bdd1183f92793abd07c53a65c28f685c9f8f147cde6b08dc08`.
V2 passes full generation/replay in 20.371711 / 19.347711 CPU seconds,
fresh Lean in 19.794917 wall seconds, and nine focused regressions plus
twenty protocol guards. The certificate has 535 nodes / 54,491 constructors,
17 reused definitions, and no new induction. No ancestor receipt is authority.

AP048 proves a general finite square-to-linear error conversion. For k!=0,
k<=x+y and supplied square bounds
`r*x*x<=r*y*y+a*k*k`, `r*y*y<=r*x*x+b*k*k`, it proves
`r*x<=r*y+a*k` and `r*y<=r*x+b*k`. Decidable natural order gives an actual
additive gap; difference of squares bounds it and positive k is cancelled.
All four local constructors and owned endpoints pass. Full generation/replay
uses 0.568925 / 0.442548 CPU seconds; fresh Lean takes 7.990103 wall seconds.
Eight focused regressions and twenty protocol guards pass. Its 31-node,
1,162-constructor certificate reuses only Le and adds no induction or axiom.
Z3 and E did not resolve the exact one-sided target in their three-second
allocations; Vampire was unavailable. `square-error-linear-solvers-v1.json`
retains the untrusted observations, without any solver acceleration claim.

AP049 applies that arithmetic to supplied half-log and root square bounds.
For positive h,d, r<=d, d<=s, the SQ009-style square bounds on s/d, and the
AP047-style square bounds on u/h, it proves
`r*u*d<=r*s*h+7*h*d` and `r*s*h<=r*u*d+h*d`.
The forward allowance is 3/r+4/d<=7/r; the reverse allowance is 1/r.
All five constructors and thirteen owned endpoints pass. Full generation/
replay uses 0.577120 / 0.472709 CPU seconds, fresh Lean 6.727620 wall seconds.
Eight focused regressions, twenty protocol guards and the existing solver-
observer regressions pass. Its 38 nodes / 3,603 constructors reuse only Le
and add no induction. These are supplied bounds, not constructed witnesses.

AP050 now closes that finite actual-witness assembly: it retains all AP047
fields, constructs the integer floor root of 2*r*r with SQ001's actual totality
body, forms the existing DyadicSqrt2(n,r,s) graph, obtains its six SQ009 bounds
and applies AP049 at d=r. The exact 16-witness / 25-field statement and its
19-definition DAG are frozen. The local constructor and all five exact owned
endpoints pass. First-attempt full generation/replay uses 20.910126 / 19.934335
CPU seconds; independent fresh Lean takes 18.701339 wall seconds. Eight
focused regressions and twenty protocol guards pass (eight existing warnings).
Its canonical certificate has 560 nodes / 58,554 constructors and SHA-256
`7c36ebfc20bc30b67500cb3c89192873f059af2f30b2cf4f26baeb80c3d822b6`.
No new definition, induction or axiom is introduced. This yields an actual
finite comparison at every precision, not an admitted infinite identity.

Final consistency audit `half-log-root-progress-audit-v2.json` confirms all
four targets, same-byte HA/Lean certificates, passing regressions and current
producer/kernel pins. V1's naive whole-controller equality check failed
because AP048-AP050 were registered after earlier observations. The source
diff audit isolates exactly that controller file; v2 authenticates each saved
historical controller and compares its run/replay/guard/limit functions and
relevant case branches by exact AST. None of those semantics changed. Both
diagnostic attempts are preserved; neither is additional proof authority.

The remaining replay margin is only about 0.066 CPU seconds. Do not simply
append another large combined cone or increase the cap. Preserve AP047-AP050
as immutable evidence. First plan any necessary untrusted proof-package
refactoring against the recorded per-row costs, and check every resulting
ordinary body in both kernels. Independent small arithmetic leaves may proceed
without replaying these large parent producers.

AP051-AP055 now remove the x<=d restriction from the finite exponential-tail
machinery. Their actual proof DAG uses AP051's threshold cancellation for
AP052's constructed halving tail, combines AP052 with the independent AP053
halving-prefix induction in AP054, then uses CV009 sum splitting and CV100's
finite finish-bound arithmetic to transport AP054 to supplied sums in AP055.
Definitions retain their existing identities; no new abbreviation is admitted.

- AP051 proves
  `~d=0 -> Le(x,L*d) -> Le(2*L,S j) -> ((S j)*d)*b=x*a -> Le(2*b,a)`.
  Its internal general cancellation target is
  `~c=0 -> Le(2*x,c) -> c*b=x*a -> Le(2*b,a)`.
  Only positive c=(j+1)*d is cancelled. Z3 reports UNSAT with proof-shaped
  output for this exact helper; E is unresolved within three seconds and
  Vampire unavailable. The observation remains an untrusted hint; the HA
  reconstruction is separate and no solver speedup is asserted.
- AP052 constructs the actual affine slice at M>=2*L with length N+1,
  its ND0441 ratio-one relation, its decoded head a and its sum s<=2*a.
  It accepts the supplied recurrence only through M+N, not an extra row.
- AP053 proves `Pow(2,k,p) -> p*a[k]<=a[0]` at each k<=N of a supplied
  halving prefix of length N+1. One ordinary HA induction supplies the entire
  universal claim. Zero heads, zero horizon and zero index are included.
- AP054 constructs p=2^m, both decoded heads and a genuine tail at K+m
  from a supplied recurrence through K+m+N, with K>=2*L. Its nine retained
  fields include the actual slice, ratio, sum, `p*T[K+m]<=T[K]` and
  `p*tail_sum<=2*T[K]`. Extensional beta uniqueness aligns the slice at K
  used for AP053 with the independently constructed final slice.
- AP055 preserves the supplied source code, head a0 at K, short sum s of
  length K+m, whole sum t of length K+m+N+1 and actual p=2^m. General
  supplied splitting includes K+m=0. Actual sum, head and power uniqueness
  yield `s<=t` and `p*t<=p*s+2*a0`. No infinite remainder is assumed.

All five first-attempt HA generation/replay runs pass under the existing
limits: respectively 0.540527/0.443512, 3.896326/2.121727,
3.701844/2.030588, 4.053131/2.202232 and 4.129094/2.384292 CPU seconds.
Fresh nine-module Lean runs pass on the same bytes in 9.478770, 12.131488,
9.325671, 10.068387 and 10.566873 wall seconds. Each has eight focused
regressions and twenty protocol guards. AP054 validation v1 found only a
model-count typo (864 examples, not more than 1,000); all inequalities held.
The single correction asserts 864, and v2 passes; no proof/producer byte
changed. Both reports are retained. The certificates have respectively
23/832, 123/6,057, 36/1,526, 138/7,210 and 157/8,561 nodes/constructors.
Their exact existing definition cones have 1, 7, 7, 10 and 11 members.
AP053 alone adds one new induction; none adds an axiom.
`large-argument-tail-progress-audit-v1.json` confirms the five exact targets,
same-byte HA/Lean checks, passing regressions and current producer/kernel pins.
Historical controllers differ only as later cases were registered; the saved
controller bytes are authenticated and relevant case, replay and resource-limit
functions are AST-identical. This is a consistency audit, not proof authority.

AP056-AP059 now complete the original-head majorant and a general-argument
finite product estimate. AP056 adds one ordinary induction proving
`T[k]<=L^k*T[0]`, without requiring L or the head nonzero. Its one-step
helper cancels only positive d; Z3's exact-helper UNSAT observation remains
untrusted and the HA construction is independent. AP057 combines the bound
at K with AP055 to retain both supplied sums and prove
`s<=t` and `p*t<=p*s+2*(B*h)`, for p=2^m and B=L^K.
AP058 constructs the actual factorial-weighted table and eleven witnesses,
including positive original normalization, all-index term identities, both
sums and powers. AP059 constructs the actual convolution at horizon
H=(n+1)+n, n=K+m, and proves `s<=u*v` and
`p*(u*v)<=p*s+2*(B*(a0*b0))`, with p=2^(m+1), B=L^K and x+y<=L*d.
The latter uses exact successor/cutoff alignment, not an infinite-product axiom.

All four first-attempt HA generation/replay runs pass: respectively
3.653905/2.033397, 4.056372/2.381320, 4.615945/2.751700 and
5.508858/3.661694 CPU seconds. Fresh nine-module Lean runs pass on the
same bytes in 11.141017, 9.634091, 10.483607 and 13.404908 wall seconds.
Each passes eight focused regressions and twenty protocol guards. Certificates
have respectively 44/1,971, 160/9,036, 184/11,412 and 248/17,215
nodes/constructors, reusing 7, 8, 12 and 13 existing definitions. Only AP056
adds an induction; none adds an axiom or definition. The four rational/integer
model suites cover 2,688, 1,728, 864 and 768 instances, including zero heads
and arguments where allowed. `normalized-exp-progress-audit-v1.json` confirms
exact targets, same-byte evidence, passing regressions, current producer/kernel
pins and authenticated historical controller semantics. All heavy sessions
were explicitly reaped before the next launch. No IR parent is closed.

AP060-AP064 now complete unrestricted recurrence value independence and the
requested-precision finite truncation/product budgets:

- AP060 retains positive denominators d,e, x*e=y*d, both actual recurrences,
  heads h,g and degree-N sums s,t, and proves `g*s=h*t`. One ordinary
  induction propagates termwise cross-equality. Its step cancels only the
  proved nonzero coefficient `(j+1)*d*e`; neither head is cancelled.
  Existing ND0409 packages the pointwise identity for actual CV006 linearity.
  The old AP005 unit-argument restriction is not silently removed or reused.
- AP061 transports AP059 to three independently supplied tables/heads/sums
  using AP060, actual sum uniqueness and recurrence restriction. For
  n=K+m, p=2^(m+1), B=L^K, prove `(a0*b0)*w<=c0*(u*v)` and
  `p*(c0*(u*v))<=p*((a0*b0)*w)+2*(B*(c0*(a0*b0)))`.
- AP062 proves `L^K<=2^(L*K)` by ordinary induction on K. At successor,
  actual power addition and `L<=2^L` bound the next product. Thus actual
  B=L^K, r=2^n and p=2^(L*K+n+1) give nonzero r,p and
  `2*(r*B)<=p`. All zero parameters, including 0^0=1, are covered.
- AP063 chooses extra cutoff m=L*K+n+1. Applying AP057 and AP062 gives
  `s<=t` and `r*t<=r*s+h` at short length K+m, uniformly in the extra
  finite horizon. Auxiliary powers are constructed, not premise certificates.
  The arithmetic helper multiplies the old bound by r and cancels only
  positive p after bounding its error by p*h.
- AP064 uses degree D=K+(L*K+n), input recurrences through 2*D+1 and
  an independent output recurrence through D. It retains all supplied sums,
  proves r=2^n nonzero and both requested-precision product inequalities:
  `(a0*b0)*w<=c0*(u*v)` and
  `r*(c0*(u*v))<=r*((a0*b0)*w)+c0*(a0*b0)`.

All five first-attempt HA generation/replay runs pass under unchanged limits:
2.672266/1.500027, 6.108747/4.102571, 3.770802/2.144799,
4.270750/2.546048 and 6.389590/4.341009 CPU seconds. Fresh nine-module
Lean checks of the same bytes pass in 10.449751, 12.478891, 9.472287,
10.653806 and 12.435406 wall seconds. Each passes eight focused regressions
and twenty protocol guards, including false-target/forged-body rejection.
Certificates have respectively 37/2,457, 255/18,591, 129/6,254,
171/9,998 and 266/19,599 nodes/constructors, with 6, 13, 6, 8 and
13 reused definitions. AP060 and AP062 each introduce one ordinary induction;
none introduces an axiom or new definition. The integer model suites cover
3,024, 640, 693, 540 and 205 instances within the 128-bit example bound.
Z3 reports UNSAT for the exact AP060 and AP063 arithmetic helpers; AP061
and AP062 probes remain unresolved. E is unresolved and Vampire unavailable.
All observations are untrusted hints, not reconstructed solver proof logs.
`requested-exp-progress-audit-v1.json` confirms the five exact targets,
same-byte evidence, current proof/test source pins and authenticated unchanged
relevant controller semantics. All heavy sessions were reaped before each
next launch. The public v5 checkpoint, Alpha/Stable and IR parents are unchanged.

AP065 now supplies the independent-code variable-horizon comparison. For
D=K+(L*K+n), keep a coarse recurrence through D and a fine recurrence through
(D+1)+N, with independent positive denominators, heads h,g and sums s,t.
At equal rational arguments, with the fine argument at most L and K>=2*L,
construct the actual fine short sum z, prove `g*s=h*z` by AP060, and align
its cutoff with AP063 using PA4. Scaling the latter's bounds by h gives
`g*s<=h*t` and `r*(h*t)<=r*(g*s)+h*g`, with r=2^n proved nonzero.
No head positivity, code equality, real object or infinite limit is assumed.

First-attempt HA generation/replay pass in 5.093747/2.993455 CPU seconds;
fresh nine-module Lean checks the same bytes in 12.493967 wall seconds.
All eight focused regressions and twenty protocol guards pass. The certificate
has 179 nodes / 11,773 constructors and reuses eight definitions, with no new
induction or axiom. All 1,440 integer models pass within the 128-bit example
bound. Z3 and E probes are unresolved and Vampire unavailable; no solver log
is used as authority. `independent-horizon-progress-audit-v1.json` confirms
the exact same-byte evidence and rechecks AP060-AP064's unchanged current
proof sources and authenticated relevant controller semantics. All supervisors
were reaped; library/publication status and IR parent status are unchanged.

AP066-AP069 now complete the next positive-witness and relative-continuity
tranche, without changing the original approximation program:

- AP066 constructs coarse weights/terms, h,s and r=2^n **before** the
  `forall N` binder. For D=K+(L*K+n), actual CV070 fine witnesses at
  (D+1)+N retain their own tables, nonzero heads, factorial factorizations
  and all-index normalization. AP065 proves the two cross-product bounds
  for the same coarse witness at every later horizon. The statement has
  fourteen outer fields and thirteen fields under each fine existential.
- AP067 constructs three positive CV070 computations at x, y and x+y,
  the actual short input sums and r=2^n. All 39 output fields are retained;
  AP064 proves the requested product error on those exact witnesses.
- AP068 removes the small-argument restriction from common-head relative
  continuity: y=x+g implies s<=t and d*t<=d*s+g*t. The unrestricted
  CV096 tail-graph bodies and actual prefix comparison suffice. An absolute
  majorant is not silently assumed.
- AP069 constructs common-scale tables for two independent denominators,
  heads and codes. With d*y=e*x+g it proves b0*s<=a0*t and
  `(d*e)*(a0*t)<=(d*e)*(b0*s)+g*(a0*t)` without an argument upper bound.

All four full HA generation/replay runs pass on their first attempt, in
5.666272/3.486960, 7.673181/5.540754, 2.955436/1.747650 and
3.668603/2.164648 CPU seconds respectively. Fresh nine-module Lean checks
the identical bytes in 12.944168, 13.966050, 8.130346 and 8.261322 wall
seconds. Each root has eight passing focused regressions and twenty passing
protocol guards (eight existing Lean-protocol warnings). Certificates have
202/14,267, 289/22,331, 137/8,077 and 144/9,148 nodes/constructors;
they reuse 12, 12, 7 and 6 definitions. No new induction, axiom or definition
is introduced. Integer models cover 272, 62, 2,268 and 1,344 instances,
all within the 128-bit example bound.

AP066's initial constructor-audit harness failed on an incorrect module
import; correcting only that import passed, with the failed observation
preserved. AP067's initial constructor/ownership audit passed the local
constructor but exposed use of the wrong archive for sum existence. Its one
changed repair selects the actual CV003 archive; the second audit passed.
Both observations remain immutable. The subsequent full wave, fresh Lean and
regression runs required no repairs or increased limits. AP068's exact
arithmetic helper remains unresolved by the three-second Z3/E probes;
Vampire is unavailable. Solver observations have no proof authority.

`positive-witness-relative-continuity-progress-audit-v1.json` confirms all
four exact targets, same-byte HA/Lean evidence, unchanged current proof/test
sources and authenticated unchanged relevant controller semantics. It also
rechecks AP060-AP065's current proof sources and controller branches.
Every heavy supervisor was terminal-reaped before the next launch. At that
checkpoint the total was 186 additional / 219 distinct checked statements and 1,375 focused
new-statement regressions. Public v5 remains 33; Alpha/Stable, commits and
deployment are unchanged. Every IR parent remains open.

AP070-AP075 now complete the uniform-majorant and explicit-modulus tranche:

- AP070 converts AP069's relative error into requested absolute accuracy
  under the actual supplied bound t<=C*b0 and budget `(r*g)*C<=d*e`.
  The pure arithmetic helper cancels only the proved positive d*e; r remains
  symbolic. No majorant construction is claimed by this statement alone.
- AP071 proves unrestricted same-degree submultiplicativity for actual
  recurrences at x,y,x+y: `(a0*b0)*w<=c0*(u*v)`. AP041 constructs the
  Cauchy table, its prefix is restricted, and AP039/AP060 identify the
  recurrence, head and cross-normalized value. No larger input horizon is
  necessary and no argument bound is assumed.
- AP072 uses one ordinary induction in L to prove `s<=9^(L+1)*h` at
  integer arguments L*d, uniformly in N. The successor constructs actual
  positive CV070 factors at L*d and d, applies the induction hypothesis,
  CV071 and AP071, and cancels only their positive head product. The supplied
  output head may be zero. The base uses the actual power-at-one identity.
- AP073 constructs a positive reference at L*d and transports this bound
  to every actual x<=L*d with AP069. Its natural argument gap and reference
  head are actual witnesses; only the latter is cancelled.
- AP074 uses AP073 to discharge AP070's majorant. A decidable order split
  and AP007's actual gap/cancellation bodies handle either input order.
  With both arguments bounded by L, both cross-product gaps at most g,
  `Pow(9,S L,C)` and `(r*g)*C<=d*e`, both output errors after scaling by
  r are at most a0*b0. Independent denominators, heads and codes remain.
- AP075 constructs C=9^(L+1) and instantiates AP062's binary budget. For
  actual r=2^n and p=2^m, where `m=9*(L+1)+n+1`, the premise
  `p*g<=d*e` suffices for AP074's requested error. Both dyadic scales are
  proved nonzero. This modulus is uniform in the common finite horizon N.
  Rational error interpretation still needs positive heads; no analytic
  exponential or fixed-program accuracy theorem is claimed.

The main checked proof routes, omitting shared arithmetic ancestors, are:

```text
AP069 -------------------------------> AP070
AP041 + AP039 + AP060 ----------------> AP071
AP071 + CV070 + CV071 + AP010 ---------> AP072
AP072 + CV070 + AP069 ----------------> AP073
AP070 + AP073 + AP007 ----------------> AP074
AP074 + AP062 + AP010 ----------------> AP075
```

All six first-attempt full HA generation/replay runs pass, using respectively
3.667513/2.171014, 5.778588/3.761985, 11.262794/6.804965,
12.933664/7.759656, 16.221017/9.356081 and 15.989655/9.379349 CPU
seconds. Fresh nine-module Lean checks the identical bytes in 8.554104,
10.481808, 11.405336, 11.188676, 13.934994 and 12.981456 wall seconds.
Each root has eight passing focused tests and twenty protocol guards, with
the eight existing Lean-protocol warnings. Certificates have 146/9,520,
216/15,057, 267/20,100, 281/22,610, 288/23,493 and 299/24,315
nodes/constructors. The definition closures contain 5, 10, 12, 12, 12 and
12 unchanged conservative definitions. Only AP072 adds an ordinary induction;
none adds an axiom or definition. AP071-AP075 have 3,510, 648, 2,268,
4,000 and 3,400 bounded integer models respectively. AP075's numerical
examples use degree at most one to preserve the 128-bit cap; the checked
statement remains universal in N.

The three-second Z3/E probes for AP070, AP072 and AP075 remain unresolved;
Vampire is unavailable. Exact HA constructors, not solver output, establish
their arithmetic helpers. AP071, AP073 and AP074 reuse already checked
arithmetic endpoints. No constructor, HA, Lean or regression repair was
needed for these six roots, and no resource ceiling changed.
`bounded-exp-modulus-progress-audit-v1.json` confirms all six exact targets,
same-byte HA/Lean evidence, unchanged proof/test sources and authenticated
relevant controller semantics, and rechecks AP060-AP069. All supervisors were
terminal-reaped. At that checkpoint the local total was 192 additional / 225 distinct
checked statements and 1,423 focused new-statement regressions. Public v5
remains 33; Alpha/Stable, commits and deployment are unchanged. IR072 and
every IR parent remain open.

AP076-AP079 now complete finite power-error propagation:

- AP076 proves the ordered natural bound from b=a+g, b<=M and actual
  u=a^(k+1), v=b^(k+1), w=M^k: `v<=u+(k+1)*(g*w)`.
  One ordinary induction in k extracts actual previous powers. Its arithmetic
  step uses the induction hypothesis, same-exponent monotonicity and the
  actual successor value of M^k. No positive-base assumption is needed.
- AP077 splits constructive natural order, constructs the actual gap and
  bounds it by g. AP076 gives the forward error and monotonicity the other
  direction. Thus both power errors are bounded for a,b<=M and both input
  gaps at most g, including slack gaps, M=0, g=0 and k=0.
- AP078 proves actual product powers by one ordinary induction:
  Pow(a,k,u), Pow(b,k,v), Pow(a*b,k,w) imply w=u*v. Its retained
  successor-value helper uses actual power uniqueness, not a presumed table
  equality. Zero bases and exponent zero remain allowed.
- AP079 crosses independently normalized rationals before invoking AP077.
  For d,e nonzero, a<=M*d, b<=M*e and both crossed input gaps at most g,
  retain actual u=a^(k+1), v=b^(k+1), D=d^(k+1), E=e^(k+1),
  C=M^k and Q=(d*e)^k. Construct the crossed powers and use AP078 to
  identify their values. Prove D,E nonzero and both error bounds between
  v*D and u*E with allowance `(k+1)*(g*(C*Q))`. This root requires no
  denominator cancellation, new induction or analytic assumption.

The checked routes, omitting shared arithmetic, are:

```text
AP010 -------------------------------> AP076
AP076 + AP010 + AP007 ----------------> AP077
AP010 -------------------------------> AP078
AP077 + AP078 + AP010 ----------------> AP079
```

All four first-attempt full HA generation/replay runs pass, using respectively
7.719946/4.023999, 7.924659/4.077102, 7.846631/4.147916 and
12.195714/6.303755 CPU seconds. Fresh nine-module Lean checks the same bytes
in 11.160653, 9.618815, 9.567635 and 10.788971 wall seconds. Each root
has eight passing focused tests and twenty protocol guards, with the eight
existing Lean-protocol warnings. Certificates have 36/1,709, 41/1,999,
121/5,854 and 136/6,964 nodes/constructors. Their definition closures have
6, 6, 5 and 6 unchanged conservative definitions. Only AP076 and AP078 add
ordinary inductions; none adds an axiom or definition. The bounded actual-
power model counts are 840, 6,300, 640 and 34,992 respectively, all within
the 128-bit numerical guard.

AP076's arithmetic helper remains unresolved by three-second Z3/E probes;
Vampire is unavailable. Ordinary HA constructors prove it. The other three
roots reuse checked algebra/order endpoints and deterministic AC constructors;
solver observations do not supply proof authority. No repair or ceiling
increase was needed. `power-error-progress-audit-v1.json` checks all four
exact targets, same-byte HA/Lean evidence, current proof/test sources and
authenticated relevant controller semantics, and rechecks AP070-AP075.
All heavy supervisors were terminal-reaped. At that checkpoint the local total was
196 additional / 229 distinct checked statements and 1,455 focused
new-statement regressions. Public v5 remains 33; Alpha/Stable, commits and
deployment are unchanged. Every IR parent remains open.

AP080 and AP081 now close the two finite precision adapters:

- AP080 keeps d,e nonzero, a<=M*d, b<=M*e, both crossed input gaps at
  most g, and actual u=a^(k+1), v=b^(k+1), D=d^(k+1), E=e^(k+1),
  C=M^k. From `(r*(k+1))*(g*C)<=d*e`, it proves D,E nonzero and

  ```text
  Le(r*(v*D),r*(u*E)+D*E) /\
  Le(r*(u*E),r*(v*D)+D*E).
  ```

  It constructs Q=(d*e)^k and H=(d*e)^(k+1). AP078's actual root and
  retained successor-value body (node 119) identify `D*E=(d*e)*Q`.
  Multiplication, distribution and the supplied budget absorb AP079's
  allowance without cancelling any factor. r=0 and zero numerator/bound
  cases are included. Dyadic precision is supplied by the eventual caller.
- AP081 retains independently supplied finite exponential computations with
  positive argument denominators, x/d,y/e<=L, 2*L<=K, coarse degree
  D=K+(L*K+n), and fine degree (D+1)+N. It retains r=2^n,
  p=2^(9*(L+1)+n+1), both crossed argument gaps at most g, and p*g<=d*e.
  Construct the fine short sum z at degree D, restrict its actual recurrence,
  and apply AP075. Align K+(L*K+n+1) with D+1 by actual arithmetic and
  apply AP063 to the fine table. The root proves r,p nonzero and

  ```text
  Le(r*(b0*s),r*(a0*t)+a0*b0) /\
  Le(r*(a0*t),r*(b0*s)+2*(a0*b0)).
  ```

  The factor two is the sum of input and tail error budgets, not an omitted
  normalization. Heads may be zero; a rational interpretation requires their
  positivity. No equality of independent codes or analytic limit is assumed.

The new actual proof routes, omitting shared arithmetic, are:

```text
AP079 + AP078 + AP010 ----------------> AP080
AP075 + AP063 + CV101 + CV003 ---------> AP081
```

Both first-attempt full HA generation/replay runs pass, in 12.209716/6.375159
and 16.701029/9.901696 CPU seconds. Fresh nine-module Lean checks identical
bytes in 10.406002 and 14.359502 wall seconds. Each has eight passing focused
tests plus twenty protocol guards (eight existing Lean-protocol warnings).
Their certificates have 138/7,376 and 323/27,568 nodes/constructors and
6 and 12 unchanged conservative definitions. Neither introduces induction,
axioms or definitions. Numerical models respect the 128-bit cap; they include
more than 40,000 rational-power cases and more than 1,000 finite exponential
cases, with strict input errors and boundary cases, not only equal arguments.

Z3 returns `unsat` for AP080's exact arithmetic helper within three seconds;
its proof-shaped output is not reconstructed or imported. E is unresolved and
Vampire unavailable. AP081's three-second Z3/E probes remain unresolved.
Both helpers have separate ordinary HA proofs. No retry, resource ceiling
change or scheduling exception was needed. The
`precision-and-joint-error-progress-audit-v1.json` audit confirms both exact
targets, same-byte HA/Lean checks, unchanged proof/test sources, relevant
authenticated controller semantics, exact solver-helper/source bindings and
the unchanged AP076-AP079 proof closures. Every heavy session was explicitly
terminal-reaped. At that checkpoint the total was 198 additional / 231 distinct local
statements and 1,471 focused new-statement regressions. Published v5 remains
33; no promotion, commit, push or deployment is claimed. IR072 remains open.

AP082-AP084 now connect the independent finite logarithm/exponential
computations to a uniform near-two statement:

- AP082 retains actual logarithm lengths M=k+1 and M+l, actual powers
  p=3^M, q=3^(M+l), P=2^m, and independent exponential computations of
  degrees m and m+1+N. Extract the ordered logarithm gap from CV093 and
  use CV086's actual unit-interval bound before applying CV101. Prove all
  argument denominators and powers nonzero; cancel only the proved positive
  coefficient factor. The result is `b0*u<=a0*v` and
  `(p*P)*(a0*v)<=(p*P)*(b0*u)+((9*3)*P+2*p)*(a0*b0)`.
  For positive heads this is error at most 27/p+2/P, with independent
  logarithm and exponential cutoffs, not an analytic identity.
- AP083 specializes both coarse cutoffs to M=18*r+2 without assuming any
  budget. Extract an actual ternary predecessor and use the existing growth
  proofs to obtain `54*r<=p` and `4*r<=P`. Native arithmetic adds the two
  half-budgets and cancels only proved positive factors. Retain all supplied
  computations and monotonicity and conclude
  `r*(a0*v)<=r*(b0*u)+a0*b0`. Symbolic r=0, l=0, N=0 and zero heads are
  included. This auxiliary degree does not replace the fixed c-program.
- AP084 constructs AP034's actual near-two reference and the cutoff power
  before introducing arbitrary later codes, coefficient scale, l and N.
  Its quantified shape is `forall n. exists r. Pow(2,n,r) /\ ... /\ forall
  e bb bc l z q N eb ec b v. ...`: the same r works for all later tables.
  For logarithm length M+l and exponential degree M+1+N, where M=18*r+2,
  it proves q and e*q nonzero and both finite bounds

  ```text
  Le(r*v,(r*2)*b+2*b) /\ Le((r*2)*b,r*v+b).
  ```

  With b>0 their reading is `2-1/r<=v/b<=2+2/r`. Only the independently
  proved positive reference head is cancelled; raw codes and heads remain
  independent. The theorem does not postulate an analytic limit.

The actual routes, omitting shared arithmetic, are:

```text
CV093 + CV101 + CV086 + AP006/AP007 ---> AP082
AP082 + AP033 + AP046 + AP010 --------> AP083
AP034 + AP083 + AP010 ----------------> AP084
```

All three roots now have fresh ordinary HA and same-byte independent fresh
Lean evidence. Their certificates have 229/18,933, 238/20,970 and
511/55,569 nodes/constructors, with 15, 15 and 13 unchanged conservative
definitions. No new induction, axiom or definition is introduced. AP082 and
AP083 generation/replay use 12.731049/7.288667 and 12.987696/7.579174 CPU
seconds. AP084's first generation hit the 28-second CPU limit and remains
not checked. The one changed repair preserves the exact target and proof
factories, reparses only the exact needed definition cone, and streams every
source once per source check. All 295 inherited source pins and complete
definition descriptors are independently compared with the original recursive
construction. No proof body is replaced by a receipt. Definition/source
reconstruction fell from 2.317145/2.158307 to 0.004681/0.019343 CPU seconds.
The repaired AP084 generation/replay pass in 20.361823/19.181567 CPU seconds.
Its replay is near the unchanged 20-second ceiling: cost-audit further
compositions before adding ancestors, and do not silently extend the limit.
Fresh nine-module Lean takes 14.140705, 14.404884 and 19.740224 wall seconds.
The three regression runs pass 8, 8 and 9 focused tests plus twenty protocol
guards each (eight existing Lean-protocol warnings per run).

The frozen AP082/AP083 arithmetic helpers receive Z3 `unsat` within the
three-second probes; E is unresolved and Vampire unavailable. AP084's Z3/E
probes are unresolved. All helpers have separate ordinary HA constructors;
no solver proof is imported. The audit binds AP084's earlier solver observation
to its authenticated pre-repair source and unchanged helper/proof factories.
AP082's two contract-discovery failures (historical display descriptors, then
an unnecessary archive-descriptor import) are preserved. AP084's first input
snapshot omitted display priorities and is retained but unused; the consumed
second snapshot preserves every field. No mathematical target was weakened.

`log-exp-identification-progress-audit-v1.json` verifies all three exact
targets, same-byte HA/Lean evidence, current proof/test sources, relevant
authenticated controller semantics, the repaired source equivalence and solver
boundaries, and rechecks AP080-AP081. All heavy sessions were terminal-reaped.
At that checkpoint the total was 201 additional / 234 distinct local statements and 1,496
focused new-statement regressions. Published v5 remains 33; Alpha/Stable,
commits, push and deployment are unchanged. Every IR parent remains open.

AP085-AP086 now apply the uniform near-two bounds to the original logarithm
prefix schedule 2*k+1 and exponential degree k+2. AP085 chooses r=2^n before
all later indices, extracts the gap from 18*r+2<=k, and proves both exact
index identities in ordinary HA. The actual coefficient/Horner/power and
exponential recurrence/head/sum premises are transported, not replaced.
AP086 then constructs all those computations with positive denominator and
head, retaining h=(k+2)!*(d*p)^(k+2) and every term's factorial normalization.
Both establish 2-1/r<=y/h<=2+2/r for positive h. Neither concerns the original
root quotient, changes the fixed n+8 schedule or asserts an analytic limit.

The exact proof DAG is:

```text
AP084 + AP007 + CV071 -----------------> AP085
AP085 + CV025 + CV061 + CV070 + AP010 --> AP086
```

AP020's odd-reciprocal interface matches AP085, but it is not an ancestor of
these proofs. The roots retain 513/522 proof nodes, 55,732/57,051 constructors
and 13/19 existing definition identities. No new induction or axiom is added.
Constructor-only audits predicted the exact final bundle bytes, without
treating those audits as proof authority. HA generation/replay use
19.784548/18.887757 and 20.771410/19.435420 CPU seconds; fresh nine-module Lean
uses 19.724626 and 19.217983 wall seconds. Both runs pass eight focused tests
and twenty protocol guards. AP085's frozen index helper receives Z3 `unsat`;
E is unresolved and Vampire unavailable. AP086 adds no arithmetic helper.
Six small AP086 subcomputations check 24 term normalizations and 18
recurrences; they are not full target models beyond its large threshold.

`fixed-log-exp-progress-audit-v1.json` binds the exact same-byte evidence,
current sources, controller semantics, cost estimates and solver observation,
and rechecks AP082-AP084. All heavy supervisors were terminal-reaped. The
total at that checkpoint was 203 additional / 236 distinct local statements and 1,512
focused new-statement regressions. Public v5 remains 33; no new admission,
commit, push or deployment is claimed. All IR parents remain open.

AP087-AP088 now close the explicitly doubled-denominator refinement branch.
AP087 keeps the original logarithm prefixes and Horner computations at
lengths M=k+1 and M+l, with their actual powers p and q, and changes only
the actual exponential arguments to 3*x/(2*d*p) and 3*z/(2*e*q). The proof
constructs the scaled gap, proves both doubled denominators positive,
establishes monotonicity and bounds the normalized difference by
27/p+2/P at degrees m and m+1+N, P=2^m. It never reuses an atanh-prefix
predicate at a different coefficient scale. AP088 specializes to M=18*r+2
and proves error at most 1/r, using AP083's exact archived budget and
positive-cancellation bodies and its unchanged native root constructor.

```text
CV093 + CV101 + CV086 + AP006/AP007
     + AP082's arithmetic helper ------> AP087
AP087 + AP083's budget/arithmetic ------> AP088
AP050 + AP088 + restriction/powers -----> AP089 uniform root bridge (checked below)
```

The roots have 231/240 proof nodes and 19,610/21,647 constructors, with
the same 15-definition DAG and no new induction or axiom. Generation/replay
use 12.810175/7.344228 and 18.635869/10.420918 CPU seconds. Fresh nine-module
Lean uses 11.843865 and 11.983166 wall seconds; each run passes eight focused
tests and twenty protocol guards. AP087 has 1,080 small actual models;
AP088's 27 complete tables use r=0, while positive-r checks cover the actual
power budgets only. No large ground computation exceeds the 128-bit guard.

AP087's frozen scaling contract was sent to the bounded solver portfolio
before adding the native factories. Z3/E were inconclusive and Vampire
unavailable. The retained pre-construction source snapshot verifies that
only the three native factory/assembly functions were subsequently added;
every prior declaration remains identical. The combined constructor/test
audit hit its 10-second CPU cap. One changed constructor-only audit passed,
and the separated tests all passed; no proof code or ceiling was changed.
AP088 needs no new arithmetic helper. `half-log-refinement-progress-audit-v1.json`
checks both exact same-byte certificates, tests, sources, relevant controller
semantics, constructor estimates and the solver boundary, and rechecks
AP082-AP086. All heavy sessions were terminal-reaped. At that checkpoint the total was
205 additional / 238 distinct local statements and 1,528 focused regressions.
Public v5 remains 33 and all IR parents remain open; no promotion or deployment.

AP089 was planned with the following uniform half-log/root contract,
unproved at that planning checkpoint and now checked below.
For every n, choose r,s before any later exponential table, retaining
Pow(2,n,r), ~r=0 and DyadicSqrt2(n,r,s). Set M=18*r+2. For arbitrary
e,bb,bc,l,z,q,N,eb,ec,b,v retain ~e=0, actual atanh/Horner/Pow(3,-,q)
data at M+l, and the actual recurrence with denominator 2*(e*q), numerator
3*z, degree M+1+N, head b and sum v. The proposed finite conclusions are:

```text
~q=0 /\ ~(2*(e*q))=0
r*v <= s*b + 8*b
s*b <= r*v + b
```

For b>0 these read -1/r<=v/b-s/r<=8/r. Do not replace the dyadic root
by sqrt(2) without the separate certified identification argument. The proof
plan is to restrict AP050's retained half-exponential recurrence from
H=(M+1)+M to M, using the exact existing restriction endpoint and a proved
Le(M,H); construct the actual power 2^M; apply AP088; then transport AP050's
two cross errors, cancelling only its positive r and head h. The new upper
allowance is 7+1=8, not 7. Freeze its exact arithmetic helper and run the
solver portfolio before constructing that helper. Preserve the quantifier
order: the reference root is chosen before all later independent tables.
`half-log-root-uniform-cone-cost-audit-v1.json` merges the actual AP050/AP088
cones and finds a lower bound of 581 nodes / 64,560 constructors. It neither
includes the new body/extra endpoints nor replays the combined proof or
predicts runtime. Audit complete costs before launch, retain the 20-second
fresh-replay ceiling, and prepare exact source/definition sharing from the
start rather than spending the reservation on repeated metadata construction.

AP089 implementation checkpoint: the exact proposed contract is now frozen
as `bdd05acec456f38c8dbd660093564668cdcb6a6207fd285396940740dcf42ff8`.
The 19-definition DAG and 352 inherited source pins were prepared before
proof generation. Z3/E were inconclusive on the frozen error-transport helper;
Vampire was unavailable. Its native arithmetic body and uniform root both
pass their ordinary local curried-goal checks. At that first checkpoint AP089
was **not accepted**: generation succeeded in 23.767728 CPU seconds, but the independent
fresh replay hit its 20-second cap at 20.109661.

The one changed repair shares the instantiated refinement and bound pair
using two existing checked `Cut` nodes. The new root shrinks from 1,095 to
339 constructors, with the same target, helper and ancestor graph. Every
one of the 582 non-root rows is byte-identical in the generated bundles.
The repaired bundle has 583 nodes / 65,490 constructors. Generation again
succeeded (23.629728 CPU), but fresh replay stopped at 20.110590 CPU.
Both `shared-wave-half-log-root-uniform-v1` and `-v2` remain `not_checked`.
The whole-formula/context inspections found only three duplicate rows and
eleven unused declarations, not a substantial graph reduction; no general
rewriter, altered kernel or enlarged limit was introduced.

`half-log-root-uniform-unaccepted-progress-audit-v1.json` authenticates those
results and eight lightweight contract/input tests. Full proof regressions
and independent Lean had not run at that checkpoint; their intended existence
was not evidence. Counts remained 205 additional / 238 distinct accepted local
statements and 1,528 accepted-statement regressions. No IR parent closed.
All workers were terminal-reaped. The one-repair policy was exhausted for
AP089. The owner subsequently replied **"Approve."** to the explicit request
for one additional AP089 attempt: fresh replay 30 CPU / 40 wall seconds,
generation unchanged at 28 CPU / 40 wall, aggregate 60 CPU / 90 wall
(including hard-limit margins), 768 MiB, one worker and unchanged certificate
caps. This phase allocation is now implemented only for AP089, with
reservation (28+1)+(30+1)=60; CV085 and every other case are unchanged.
The authorization covers `shared-wave-half-log-root-uniform-v3` only, not
further retries, other leaves, Lean or regression limits, or kernel changes.
The two failed observations remain immutable. This authorization does not
itself accept AP089: fresh replay, same-byte Lean and all ten focused
regressions must pass before its checked counts can change.

The approved v3 passed generation (26.067345 CPU seconds) and complete fresh
HA replay (24.615095 CPU), then the exact same bytes passed freshly compiled
Lean, including both negative controls (23.250591 wall seconds overall).
The first regression run remains `failed_or_incomplete`: eight lightweight
tests passed, but regenerating and replaying the entire bundle inside the
ninth test hit its separate 25-CPU-second limit at 25.199275 CPU. The final
negative-control test and common protocol tests were not reached.

The one changed regression repair keeps all limits and proof sources frozen.
It authenticates the successful v3 bytes against current source pins,
reconstructs both new native bodies and compares their actual encodings,
and checks every one of the 583 bodies with the unchanged ordinary kernel
and exactly the full checker's closed curried goals. Those body checks are
split into three disjoint test processes (195/194/194 rows); complete
canonical decoding still checks the entire dependency graph in each.
The negative controls run on those same authenticated bytes. This adds
three focused tests (thirteen total), not a new theorem or a replacement
for complete positive HA replay. No receipt is fabricated and no ancestor
is assumed as an axiom. All thirteen tests and the twenty protocol guards
now pass in `shared-wave-half-log-root-uniform-validation-v2.json`; the failed
validation record is retained. The three complete-coverage body batches use
12.159842, 9.754083 and 7.034540 CPU seconds, all below the unchanged 25-second
ceiling. No further AP089 generation/replay attempt was run or authorized
by this test-only repair.

**AP089 accepted local checkpoint:**
`half-log-root-uniform-progress-audit-v1.json` binds the exact statement,
3,848,765 canonical bytes, complete original HA replay, same-byte fresh Lean,
all 33 regressions, current proof/kernel source pins and constructor costs.
It verifies unchanged 19-definition syntax/DAG, preserved solver-first
contract, all 582 non-root rows identical across the three HA attempts,
repaired v2 and successful v3 bundles byte-identical, and both failed HA
attempts and the failed first validation preserved. The test-only repair
leaves its first eight tests unchanged. AP085-AP088 sources and relevant
controller semantics are rechecked, allowing only the authenticated AP089
replay exception. Totals are 206 additional / 239 distinct locally checked
statements and 1,541 focused regressions. All heavy sessions were explicitly
terminal-reaped. No IR parent closes; public v5 remains 33 and no Alpha/Stable
promotion, commit, push or deployment is claimed.

After those completed gates, the final documentation/syntax audit was
interrupted when `/bin/ps -axo pid=,pgid=,rss=` exceeded the supervisor's
unchanged one-second accounting timeout. No validated worker receipt was
returned, so no documentation success is inferred from that attempt.
`half-log-root-uniform-documentation-interruption-v1.json` preserves the
terminal failure and its evidence boundary; the owned worker was cleaned up
by the existing supervisor and the terminal session was reaped. A subsequent
single read-only probe, `half-log-root-uniform-accounting-recovery-v1.json`,
observed accounting available again in 0.0227675 seconds for 832 process rows.
Only after that recovery may the bounded documentation audit be retried.
No timeout was enlarged and no user application was stopped or changed.
The completed HA, Lean, regressions and proof-consistency audit are unchanged;
`git diff --check` passed separately.

The then-next **unproved AP090 contract** (now checked in the WMI checkpoint
below) was the fixed-schedule half-log/root
comparison, with no new definition and no new arithmetic helper planned:

```text
forall n. exists r s. Pow(2,n,r) /\ (~r=0 /\ (DyadicSqrt2(n,r,s) /\
  (forall k e bb bc z q eb ec b v.
    Le(S(S(18*r)),k) -> ~e=0 ->
    NatAtanhPrefix(e,bb,bc,S(2*k)) ->
    NatHornerValue(bb,bc,3,S(2*k),z) -> Pow(3,S(2*k),q) ->
    NatScaledExpRecurrence(2*(e*q),3*z,eb,ec,S(S k)) ->
    BetaAt(eb,ec,0,b) -> Sum(eb,ec,S(S(S k)),v) ->
    ~q=0 /\ (~(2*(e*q))=0 /\
      (Le(r*v,s*b+8*b) /\ Le(s*b,r*v+b))))))
```

Reuse only AP085's checked `indices` helper, not its unrelated near-two
root, and AP007's actual `Le` gap endpoint. After choosing r,s from AP089,
construct t with k=M+t, M=18*r+2. The checked index equalities give
2*k+1=M+(k+t+1) and k+2=(M+1)+(t+1). Transport the supplied prefix, Horner
value, power, recurrence and sum along these equalities, then instantiate
AP089 with l=k+t+1 and N=t+1. Keep r,s outside every later universal
quantifier, preserve all codes and heads, and use existing checked `Cut`
sharing when the instantiated conjunction is consumed more than once.
The exact dependency plan is AP089 + AP085(indices) + AP007(le_gap) -> AP090;
this arrow records a plan, not an accepted proof edge. It does not identify
the original log/root quotient or assert a real-limit theorem.

AP090 has a separate resource gate: AP089's measured 24.615095-second replay
already exceeds the ordinary 20-second ceiling for other cases. The
one-attempt AP089 approval does not transfer. Audit the actual retained
closure and new body before launch; a full AP090 attempt needs either a
proved-safe reduction that fits the existing ceilings or explicit separate
authorization. Do not omit ancestor checks, alter the kernel, or relabel a
previous receipt as a new proof to get around this gate. Contract and local
constructor preparation may continue under their existing small budgets.

The owner subsequently replied **"Yes."** to the separate explicit request
for **one AP090 attempt**: generation 28 CPU / 40 wall seconds, fresh replay
30 CPU / 40 wall, aggregate 60 CPU / 90 wall including hard-limit margins,
768 MiB and one worker. This AP090-only allocation is now implemented for
`shared-wave-fixed-half-log-root-v1`; it does not authorize a second attempt,
other leaves, larger Lean/regression/constructor budgets, or kernel changes.
AP089's prior permission remains exhausted by its successful v3. AP090 must
still pass constructor preflight, complete HA replay, fresh same-byte Lean,
all focused/protocol regressions and evidence/source consistency checks.
The preconstruction statement/input audit matches the planned AST
`41651cb7c7afc07ceb0eaeab7bf02392001a704ec0891d7bf1db0ed4aa33211f`,
retains all 19 definitions, and resolves AP089 root 582, AP085 indices 511
and AP007 gap 157 from their actual archived bodies. A source-only snapshot
binds 362 inherited inputs. No new arithmetic helper is needed: the exact
AP085 helper is already proved and solver-observed; do not repeat a solver
search or treat its old `unsat` observation as proof authority.

AP090 preparation checkpoint (historical, not then accepted): the native transport is
implemented, with one existing checked `Cut` sharing the instantiated index
equalities. `fixed-half-log-root-native-constructor-audit-v1.json` checks
its exact closed curried goal in the unchanged ordinary kernel: 99
constructors, depth 53, body SHA-256
`0b110197ccd472fc4d367af10f3e948b6609dcc89f27d1357ba673482e6b7b04`.
It retains 19 definitions and adds no induction or arithmetic helper.
This local node check does not establish the complete dependency-closed
AP090 theorem. The producer is pinned as
`d0677792dfa5a394ec6f2beea788290e5b85d00c7dd487405607da1c1d5b1cde`.

The combined constructor/cost preflight v1 was interrupted by unavailable
process accounting; its controller-exception record is not a validated
worker receipt. One read-only recovery probe succeeded with the same
one-second timeout (0.09957525 seconds, 739 process rows). V2 then reached
the unchanged 15-second wall cap after only 4.963220 CPU seconds. The one
changed repair separates the native body check from dependency-size
bookkeeping. The native-only check passed (2.117661 CPU / 12.596256 wall),
but the separate cost audit v3 was interrupted by accounting again. All
interrupted/failed records are retained; no timeout or memory ceiling was
enlarged. Further heavy work is held until accounting and host availability
recover. The **one authorized full AP090 attempt has not been launched**.

Thirteen focused tests are prepared, including the exact quantifiers,
mutation rejection, definition metadata, owned archived endpoints, source
closure, existing solver-helper binding, native-body reconstruction and
three disjoint full-coverage body batches. Their final report/bundle pins
remain explicit fail-closed placeholders until successful artifacts exist.
AP089's test-only source binder now authenticates the historical controller
and compares its exact AP089 dispatch, full acceptance functions and literal
AP089 phase allocation; unrelated AP090 dispatch additions do not require
rerunning AP089 generation. The binder does not execute archived Python,
allow proof-source changes, or replace any kernel check. Its adverse tests
and the modified AP089 regressions still needed validation. At that checkpoint,
counts remained 206 additional / 239 distinct statements and 1,541 focused
regressions at the previous AP089 checkpoint. AP090 had not yet passed HA,
Lean or focused regression checks; see the WMI acceptance checkpoint below.

### Initial WMI migration checkpoint, 2026-10-04 (historical)

The owner approved migration and one bounded AP090 cluster pilot. Live SSH to
`wmicluster` works; this is separate from WMI website hosting. Existing Linux
Python 3.12.12 and Lean 4.31.0 were found. The new snapshot packager,
held-before-ledger Slurm submission wrapper, sequential pilot controller and
read-only receipt collector are in `scripts/*sqrt2_power_wmi*` and
`slurm/peano_wmi_sqrt2_pilot.sbatch`. Fresh Lean accepts explicit absolute
executable/source paths and pins the same six platform-specific libraries
(`.so` on Linux, `.dylib` on macOS), with the nine checker-module source hashes,
exact axiom audit, same-byte certificates and all process caps unchanged.
The AP090 proof producer is byte-for-byte unchanged.

Job **257867** was submitted on `cpu_idle`, one CPU, 2 GiB outer job memory,
ten-minute outer wall envelope, with no requeue. These scheduler resources do
not enlarge the existing per-worker bounds. Its 706-file snapshot is
`6385ec7eed50950238b44b2d6194f04da13f11fab4c6cdf669cc4b388c453472`.
All nine initial migration tests passed on WMI in 0.196325 CPU seconds. The
constructor-cost preflight then failed after 0.153505 CPU / 0.189584 wall
seconds because `peano_lab.library.finite_factorial_theorems` was absent.
This was a packaging/import error, not a kernel rejection or resource limit.
Slurm ended `FAILED`, exit `1:0`, elapsed 37 seconds. The **full AP090 attempt
never started**, and no Lean proof verification ran. Before/after snapshot
hashes agree. Exact remote evidence and scheduler records were downloaded and
hash-verified in `observations/wmi-ap090-pilot-v1/`; retain that failed run.

The corrected packager includes the complete small Peano Python package,
not just historical proof-input pins, which were not a Python import-closure
manifest. It still excludes credentials, environments, bytecode and `.git`.
Corrected archive SHA-256 is
`b8ced94ece3cb8e398558797c502520d3d93f5694663b1655a7d699fea3b80bb`
(1,246 files, 46,807,040 archive bytes; manifest
`be808aa87d30c3338433a410c4dfe716f0decb776b64d2dd983fd782bbd61b98`).
`wmi-ap090-isolated-import-v2.json` verifies the extracted archive with isolated
Python: all 190 imported campaign modules come from the snapshot, the full
theorem catalogue is not imported, the frozen AP090 target matches, all 364
original source pins match, and all 19 definitions remain. No proof generation
is performed by that import test. Eleven corrected migration tests and the
six existing fresh-Lean intake regressions pass locally under unchanged caps;
see `wmi-migration-tests-v4.json` and `wmi-fresh-lean-intake-validation-v1.json`.
The earlier sandbox-accounting interruption and input-map mutation test failure
remain recorded in migration-test v1/v2; v3 records the initial nine-test pass.

At that checkpoint no replacement had been submitted. The original guard and
remote authorization ledger remained consumed and intact, awaiting a new
owner-approved request bound to predecessor 257867. AP090 generation/replay,
focused tests and the modified AP089 regression were pending. Counts were
206 additional / 239 distinct / 1,541. The subsequent approval and completed
checks supersede that pending status below; the old ledgers are retained.

### WMI larger-resource execution and AP090 acceptance, 2026-10-04

The owner explicitly directed using WMI's more generous resources optimally.
The new `wmi-ap090-v2` profile requests one CPU, 4 GiB and 45 minutes from
Slurm. Its HA phases each receive 120 CPU / 180 wall seconds and 2 GiB RSS;
the original local profile, source-pinned supervisor, guard and all proof
validity limits remain unchanged. Execution is node-local, one worker, no
requeue, with immutable input snapshots and held-before-ledger submissions.

Job **258959**, snapshot
`e8353c52fbefb9f711d9e08af2870453caee341bce83fa45af39ab17e6d40553`,
completed full original HA generation and fresh replay. The complete attempt
has now been spent successfully: do not regenerate it to repair later checks.
Generation used 35.395584 CPU / 35.554370 wall seconds; replay used
33.938125 CPU / 34.049739 wall seconds, approximately 245 MiB RSS each.
The retained certificate has 585 nodes, 65,644 constructors, 3,868,304 bytes,
SHA-256 `603a7c00633d251a1f6b4476247eb6e48a8d13d47b47b4dbf75b5eab5747ef8c`.
The HA report SHA-256 is
`d97afbf151e451450e0551b8d49e8c0e0f6ac074c43c42d44b716d6f685ebf86`.
All 583 AP089 rows and all 19 definitions are preserved; the 99-constructor
new root remains exactly the previously checked native transport. HA rejects
the false target and forged body. No proof/kernel source or axiom changed.

The job's terminal failure was solely its Linux Lean startup probe: Lean
could not reserve virtual address space under a 2 GiB `RLIMIT_AS`. A bounded
version diagnostic succeeded with 16 GiB virtual address space while using
about 34 MiB RSS. The Lean-only guard therefore separates **16 GiB virtual
address space** from **2 GiB sampled RSS** and the **4 GiB outer job envelope**.
It fixes the executable and one-thread option. A private instance of the
unchanged supervisor retains wait4 accounting, cleanup, wall/CPU/output checks
and receipt validation; neither the original supervisor nor HA guard is patched.

Verification-only job **259148**, snapshot
`23141c6d4550624976c85c768260639ecb21a97c27f54023918978679a8fafdb`,
completed all nine fresh Lean builds, exact axiom audit, same-byte acceptance
and two rejection controls. Lean took 14.165559 CPU / 22.994377 wall seconds;
the actual certificate check took 3.189438 CPU seconds. No HA generation or
replay was repeated. The fresh report is
`observations/shared-wave-fixed-half-log-root-lean-wmi-v2/report.json`, SHA-256
`d0e929841e922a9c11ac170d8d1e0a5db8bc56f88990bef04aa0803281aee247`.
The preceding incomplete Lean output is retained in `wmi-ap090-pilot-v2/`.

Regression job **259307**, snapshot
`4da45635215319ceb7e98d7c9e383f5f4f8dda9d329d4f600fe58a5b5814872b`,
passed all **13 AP089 and 13 AP090 tests**, including current controller/source
binding, actual-body rechecks, quantifier and definition guards, and negative
controls. Scheduler time was 1:43, peak RSS 445,784 KiB. Pytest and four
dependencies were installed from pinned wheels offline into node-local scratch;
the shared Python environment was not modified. The regression job reserved
120 CPU / 180 wall seconds and 2 GiB RSS for each complete 13-test batch.
Source, proof and transport hashes match the collected results.

`fixed-half-log-root-wmi-progress-audit-v1.json` binds the HA/Lean records,
downloaded inventories, current proof/kernel sources, definition/proof DAGs
and both regression batches. Infrastructure validation separately passed
19 migration tests (`wmi-migration-tests-v8.json`) and six Lean-intake tests
(`wmi-fresh-lean-intake-validation-v3.json`). They do not inflate proof counts.
The accepted research checkpoint is **207 additional / 240 distinct checked
statements and 1,554 focused regressions**. Public v5 remains 33; Alpha/Stable
and all IR parents remain unchanged. No commit, promotion or deployment.

Operational continuation: keep heavy proof construction, replay, Lean and
regressions on WMI. Set explicit phase budgets from actual measurements plus
headroom, retaining immutable evidence and full semantic checks. Use Slurm
parallelism for genuinely independent obligations, not extra idle CPUs on a
single-threaded replay. Do not infer solver speedups from this hardware move;
the AP090 worker is deterministic and introduces no new solver-search leaf.

### AP091: positive fixed-schedule half-log/root witnesses

Contract, now checked at the acceptance checkpoint below: for every n, choose r,s with Pow(2,n,r),
r nonzero and DyadicSqrt2(n,r,s) before quantifying over k. For every
k >= 18*r+2, construct actual logarithm coefficients of length 2*k+1,
their base-three Horner value x and power p, and the degree-k+2 exponential
weight/term tables at numerator 3*x and denominator 2*(d*p). Prove d,p,
the doubled denominator and the normalization head h nonzero. Retain the
actual factorial f, denominator power q, identity h=f*q, sum y and every
term's factorial normalization, together with r*y <= s*h+8*h and
s*h <= r*y+h. No accuracy or positivity property enters a definition.

Dependency route: AP090 -> chosen root and uniform conditional bounds;
CV025 -> positive logarithm coefficient witnesses; CV061 -> actual Horner
value; AP010 -> actual powers and nonvanishing; CV070 -> actual positive
factorial-normalized exponential tables; CV071 -> positive products.
The inspection found their exact bodies already in AP090's archive.
Merge the existing AP090/AP086 definition cones conservatively, reusing
ND0291/ND0408 for the coefficient constructor's zero-prefix bookkeeping.
No new definition, induction, solver arithmetic search or analytic axiom
is planned. This contract remains unproved until full HA, fresh Lean,
mutation/regression and evidence checks pass. Heavy work runs on WMI;
the local accounting interruption is retained as an infrastructure incident.

Historical implementation checkpoint (2026-10-04, not then an accepted theorem):
`scripts/sqrt2_power_fixed_half_log_root_witness.py` now constructs that exact
native proof body. Bounded metadata inspection on WMI found all eight actual
endpoints in AP090: fixed=584, atanh=228, exponential=520, value_exists=358,
power_exists=266, power_nonzero=280, succ_nonzero=12, mul_nonzero=47.
The proposed bundle retains all 585 AP090 rows and adds one 437-constructor
body (depth 87): 586 nodes, 66,081 constructors, 3,913,686 canonical bytes.
These are inspected candidate bytes, **not** a successful kernel replay.
The target AST is frozen as
`9fba277808e08f9fc794a636d0be0242f1a8498dbd631870d0f88440174b708a`;
candidate bundle SHA-256 is
`ca771f818bb607d30de80c5bc19a15ee2d05a0932355fc71c7800b0ef096d67b`.

The definition merge checks stable IDs, names, arities, exact expanded
formulas and conceptual dependencies. Historical Le/Lt prose/category labels
differ between the two source cones; AP090's presentation is retained exactly.
Only those two presentation differences are allowed. All 21 definitions are
existing definitions, with no accuracy/positivity clause added.

The first preparation, job 268413, was cancelled while pending after a
metadata-only inspection exposed that presentation mismatch; it used no
compute allocation. Its ledger and [collected diagnostic evidence](../research/arithmetic-library/sqrt2-power/observations/wmi-ap091-preflight-v1/collection.json)
remain intact. The corrected native preflight is job **268994**, snapshot
`5d3a7f7ab86e1fb9a9b37eb1281556463b914028d35ca9d432e34c900b5f0642`.
Its successful metadata-only inspection took 0.847119 CPU seconds; native
checking is still queued. The owner explicitly authorized the normal `cpu`
partition as well as `cpu_idle`; both are now eligible, with the same one CPU,
4 GiB Slurm allocation and unchanged process/kernel limits. The preflight
has a five-minute outer allocation, not a full proof attempt.

Full validation job **269156**, snapshot
`4098461cc203b1a422961e1d18a08af283fd5619f492bbeee13c62e030498cc0`,
is queued with **afterok:268994** and cancellation on an invalid dependency.
Before any full attempt its runner also requires the exact successful native
preflight receipt and identical statement/body/DAG metadata. Thus scheduler
success alone is not treated as proof evidence. The job reserves one CPU,
4 GiB and 45 minutes; individual HA phases retain 120 CPU / 180 wall seconds
and 2 GiB RSS, followed by fresh Lean and four regression batches. The
source-pinned original supervisor and HA guard remain unchanged.
Seven lightweight routing tests pass locally; thirteen AP091 proof tests,
AP089/AP090 reruns and the controller tests are queued, not passed. No new
statement is counted, promoted or published at submission time. Queue state
and exact collection commands are retained in the
[submission record](../research/arithmetic-library/sqrt2-power/observations/fixed-half-log-root-witness-wmi-submission-v1.json).

Acceptance checkpoint (evidence collected and audited 2026-10-11): both jobs
completed with exit 0, on `cpu`. Full job 269156 took 5 minutes 57 seconds.
HA generation and fresh complete replay used 55.008070 and 52.856511 CPU
seconds respectively, at about 246 MiB peak RSS. The actual certificate is
exactly the candidate pinned above: 586 nodes / 66,081 constructors, with all
585 AP090 rows unchanged. Fresh Lean rebuilt all nine checker modules, checked
those same bytes, passed the exact endpoint axiom audit and rejected both
negative controls; the sequence took 18.209128 CPU / 29.013354 wall seconds.
Thirteen AP091 tests, 13 AP090 tests, 13 AP089 tests, 14 controller tests,
19 migration tests and seven routing tests passed. Only the 13 new focused
proof tests increase the campaign count. The
[evidence consistency audit](../research/arithmetic-library/sqrt2-power/observations/fixed-half-log-root-witness-wmi-progress-audit-v1.json)
verifies downloaded hashes, canonical copies, exact source/definition/proof
identities and process records. Accepted totals: **208 additional / 241
distinct checked statements / 1,567 focused proof regressions**. No IR parent
is closed and there is no promotion, commit, push or deployment.

### AP092 contract: fixed half-log samples versus a supplied finer dyadic root

This continuation removes the hidden coarse-root reference from the usable
comparison. For every n construct r=2^n; for every l,e,t satisfying
DyadicSqrt2(n+l,e,t) and 18*r+2<=n+l, construct the same thirteen positive
factorial-normalized AP091 witnesses at index k=n+l. Keep all seventeen
computation/normalization clauses. Also prove e,t nonzero and e<=t<2*e,
and retain the two cross inequalities

    r*(e*y) <= r*(t*h) + 8*(e*h)
    r*(t*h) <= r*(e*y) + 2*(e*h).

Dependency DAG: AP091 -> positive same-index samples near the coarse root;
SQ008 -> s*e<=t*r<=s*e+e; SQ009 -> supplied fine-root positivity/range;
one new arithmetic transfer helper -> AP092. Its forward error stays 8/r;
its reverse error is (1+1)/r. A helper-level hostile example rejects replacing
the latter 2 by 1. The existing 21-definition cone is unchanged. The original
approximation algorithm, n+8 shift and k+2 degree are not redefined.

The expanded statement is frozen as
`6d4b5804c59942bc029957cbb384a3a6d2235616d7c0e1cf4c0af32be3e12771`;
the arithmetic helper as
`29e6869a859b6574ae57e2d59c9f33a46ee5f500d8bb99cb0c3602df0ddee974`.
Metadata inspection preserves all 586 AP091 rows and predicts 595 retained
nodes, 67,967 constructors and 4,000,332 bytes. One duplicated multiplication
monotonicity statement in AP091 was resolved by explicit ownership of its
unique actual CV071 body, not by choosing an arbitrary matching row.
The original process/kernel limits are unchanged.

The tiny detached solver portfolio used 6.104541 child CPU seconds within an
18-second hard-limit reservation. Z3 and E both hit their three-second CPU
limits; Vampire was unavailable. Its logs are untrusted hints and no proof
was imported. The native reconstruction explicitly applies monotonicity,
distributivity, associativity and transitivity. A sandbox permission failure
in `/bin/ps` was resolved by the approved out-of-sandbox small solver run;
the supervisor itself was not weakened. Full generation/replay and Lean stay
on WMI. Thirteen regression tests cover the statement, unchanged definitions,
mutations, arithmetic counterexamples, exact dependencies, every actual body,
both negative controls and same-data fresh Lean. AP092 is not counted until
those gates pass.

AP092 full validation was submitted as WMI job **284684** on 2026-10-11,
snapshot `9257c94c11d59b1211c4afeff0dc9562469197d0a69a611ab194dcc5ca11ae26`.
The manifest contains 2,430 allowlisted files / 78,924,385 input bytes, including
the five unchanged pinned offline test wheels recovered from the completed
AP091 snapshot. The job uses the approved one-CPU/4-GiB profile, fresh node-local
scratch, a native-body preflight, full generation/replay, independent fresh
Lean and three regression batches. The preflight selects exact prerequisite
bodies; it does not replace checking all retained ancestors.

AP092 acceptance (2026-10-11): job **284684** completed with exit 0 in
3 minutes 42 seconds. Full HA generation/replay used 37.284625 / 34.657140
CPU seconds; fresh same-byte Lean used 14.272296 CPU / 25.040109 wall seconds.
The complete 595-node / 67,967-constructor certificate matches the preflight,
including all 586 unchanged AP091 rows. Thirteen new proof regressions,
13 AP090 tests, 14 controller tests and 19 migration tests passed. All
ordinary bodies, both HA controls, nine fresh Lean modules, the exact axiom
audit and both Lean controls passed. The
[evidence audit](../research/arithmetic-library/sqrt2-power/observations/fixed-half-log-fine-root-wmi-progress-audit-v1.json)
authenticates the downloads, canonical copies, source pins and process records.
Accepted totals: **209 additional / 242 distinct / 1,580 focused regressions**.
No IR parent, admission, commit or deployment is claimed.

#### Next bridge after AP092: reciprocal root versus half-root argument

The next proposed AP093 should connect the **original** log/root quotient to
the algebraic argument needed by the auxiliary jets, rather than introduce
another approximation sequence. First prove this finite natural-arithmetic
helper with all its guards:

    ~B=0, ~d=0, d<=s, A<=B,
    s*s<=2*(d*d)<=s*s+4*d
      imply ~V=0, ~Z=0, U<=V, W<=Z,
             V*W<=Z*U,
             d*(Z*U)<=d*(V*W)+2*(V*Z),
    where U=A*d, V=B*s, W=A*s, Z=2*(B*d).

These last four quantities are displayed substitutions, not new function
symbols or hidden definition assumptions. For supplied actual logarithm/root
data substitute A=3*x, B=D*p and the same DyadicSqrt2(k,d,s). Obtain the square
residual/range from SQ009, A<=B from CV086 with its positive coefficient-scale
guard, and nonzero powers/products from the actual computation. The rational
reading is

    0 <= (A/B)/(s/d) - (A/B)*(s/d)/2 <= 2/d.

AP093 implementation checkpoint (2026-10-11): the exact target now accepts
only `~D=0` and the supplied, unchanged `NatSqrt2LogArgument` computation.
The helper additionally accepts `~s=0` and `s<=2*d`, both derived from SQ009
in the root rather than imposed on the caller. CV086 itself allows D=0 for
its natural bound; the positive-scale guard is needed for the quotient, not
for that coefficient inequality. The helper preserves SQ009's exact nested
residual `2*(2*d)` instead of introducing a numeral-conversion assumption.

The target AST is
`244e83e9bb6930441b55dd6bc755802920abede937100ccbd61c180210112cf3`;
its eight-premise arithmetic helper is
`312add90eebbf75d44c4fd8aefbd7418034d9701b6f0bb65fde0f86df502377e`.
Fourteen prerequisites have unique explicitly owned archived bodies.
Dependency pruning yields a candidate with 69 nodes / 4,933 constructors /
189,044 bytes and the exact existing 16-definition DAG. Eight lightweight
contract/model/source/solver-observation tests and 19 migration tests pass
locally. No local proof-generation or full replay pass is claimed.

Full WMI job **284690**, snapshot
`dbe20831c2290caf4492dac7c66001ee4d5046a45675513e22b6cb7f2dc70dbb`,
has been submitted with the unchanged cpu/cpu_idle one-CPU / 4-GiB profile.
All retained bodies, ordinary HA rejection controls, fresh same-data Lean,
13 proof tests and older regressions are required before counting AP093.
The solver observation is untrusted; no external proof log is admitted.

AP093 acceptance (2026-10-11): job **284690** completed with exit 0 in
1 minute 30 seconds. HA generation/replay used 3.530134 / 1.696720 CPU seconds;
fresh Lean used 5.603104 CPU / 7.215492 wall seconds. Thirteen new proof tests,
13 AP090 tests, 14 controller tests and 19 migration tests pass. The
[audit](../research/arithmetic-library/sqrt2-power/observations/log-root-half-argument-wmi-progress-audit-v1.json)
checks every inherited body's exact statement/dependency/body signature,
the minimal reachable DAG, both new bodies, current source pins, definition
identities, same-byte Lean checks and both checkers' rejection controls.
Accepted totals are **210 additional / 243 distinct / 1,593 focused regressions**.

AP094 is now implemented, not yet accepted. Its target retains the complete
original `NatSqrt2ExpSample`, a positive coefficient scale D and a second
supplied recurrence at `(3*x)*s/(2*((D*p)*d))`, through the same degree k+2,
with its independent positive head v and actual sum z. Prove w0 nonzero and

    w0*z <= v*y
    d*(v*y) <= d*(w0*z) + 18*(w0*v).

The root also retains d and both argument denominators as proved nonzero.
AP004 supplies the original recurrence/head/sum; AP093 supplies the two
argument bounds; AP007 supplies finite continuity. A new arithmetic helper
cancels only explicitly positive d, V and Z. The tiny closed equality
9*2=18 is emitted as ordinary PA3-PA6 constructors by the existing capped
ground evaluator (maximum 32), not admitted from a host-language calculation.
No definition, induction or analytic assumption is added.

AP094 target AST:
`d987799164353f66ab8981951790a46ec16203c12f377c44a23181eb042ebe7a`.
Metadata inspection predicts 214 nodes / 18,440 constructors / 817,481 bytes
and the unchanged 23-definition original-sample cone. Eight lightweight
contract/model/source/solver tests pass; 13 full proof tests, fresh ordinary
HA replay and same-data independent Lean remain the acceptance gates.

AP094 full job **284694**, snapshot
`8661c34d98d55bfd2239a9c03a9eb7ec6f77f83b9256296d4d5ecca8584bd532`,
passed its native-body preflight, full HA generation/replay and fresh same-byte
Lean, but exited after 46 seconds when the unchanged supervisor rejected an
unexpected descendant of the offline pip installer. No proof regression had
started. The original [failed collection](../research/arithmetic-library/sqrt2-power/observations/wmi-ap094-full-v1/collection.json)
and process record are retained. HA used 14.474244 / 7.378637 CPU seconds;
fresh Lean used 6.257812 CPU / 8.850145 wall seconds. These are successful
proof gates, but AP094 is not counted until the remaining regressions pass.

Changed strategy: perform one **regression-only** follow-up on those exact
completed certificates. Stage the same five hash-pinned pure-Python wheels
directly in a fresh job-local directory, with no pip, installation hooks,
entry-point scripts or child processes. Validate all member names, regular
file modes, sizes, cumulative bounds, duplicates and file/directory collisions
before creating the directory; verify extracted bytes afterward. Eight
staging tests and the unchanged 19 migration tests pass locally. The new
runner pins both completed proof reports and the original full-job test
manifest. It cannot generate a certificate or rebuild Lean, and does not
change the supervisor, kernel, resource ceilings or original test files.

AP094 acceptance (2026-10-11): test-only job **284696**, snapshot
`edefdd8629a58fdf140b660647cbd7bb95dbdb5284ba5c1416d7d03111ca7610`,
passed child-free wheel staging, eight staging safety tests, 19 migration
tests, 13 AP094 proof tests, 13 AP093 tests and 13 AP090 tests. Its final
controller batch failed because the AP094 snapshot branch omitted the RF001
historical fixture; this distinct packaging failure is preserved in the
[test-only collection](../research/arithmetic-library/sqrt2-power/observations/wmi-ap094-tests-v1/collection.json).
The original test file and fixture, authenticated against the original AP094
and accepted AP093 manifests respectively, then passed all 14 controller
tests locally in 0.512409 CPU / 0.589741 wall seconds under the unchanged
20/30-second, 768-MiB local cap. The packager's common allowlist now includes
that fixture, independently of campaign-case routing.

The [combined audit](../research/arithmetic-library/sqrt2-power/observations/exp-log-root-half-transport-wmi-progress-audit-v1.json)
accepts the original successful HA/Lean checks plus the exact WMI proof-test
passes and local controller completion. It validates both original failed
jobs as failures, the two specific diagnoses, all process/source/report hashes,
every reused proof body, the unchanged definition DAG, same-data Lean axiom
audit and both checkers' negative controls. No proof was regenerated, no
checker was weakened, and no test source was changed to make a failure pass.
AP094's pending status above is superseded by this acceptance. Totals are
**211 additional / 244 distinct checked statements / 1,606 focused regressions**.
IR072 and all IR parents remain open; no admission, commit, push or deployment.

Thus the new argument is within 2/d of the original argument, **not equal**
at finite precision. Preserve this residual throughout subsequent transports.
The subsequent AP094 acceptance above carries the residual through finite
exponential continuity, with two independent positive normalizations, to
output difference at most 18/d. It keeps the original degree k+2.
No claim about a real limit follows until the explicit finite error budgets
are joined with AP031, AP085/AP091/AP092 and the series interpretations.

For the auxiliary-function identity, the following genuinely remaining steps
are finite exponential addition/scaling at arbitrary integer multiples, the
transport to the rational powers of the candidate c using AP080's error
budget, and then the variable-multiplicity interpolation/jet estimates. This
prioritizes a needed semantic bridge; adding more equivalent witness packaging
does not by itself discharge IR061, IR026 or IR072.

AP095 accepted (2026-10-11):
`scripts/sqrt2_power_requested_half_transport.py` implements the precise
requested-precision contract. It constructs r=2^n and shift=2^8, obtains
d=r*shift from the original supplied graph, and replays AP015's exact
arithmetic helper
`a7c53737271485b94934c473aece0dc46b01bc06fb94722136bb502ba69f7eb8`
with C=18. AP014 supplies the threshold; the only new arithmetic body is
18 <= (9*3)+2, proved by the unchanged value-32-capped evaluator. The result
retains both output heads, the degree (n+8)+2 and the entire original graph:

    exists r. Pow(2,n,r) /\ ~r=0 /\ ~d=0 /\ ~w0=0 /\ ~v=0
      /\ Le(w0*z,v*y) /\ Le(r*(v*y),r*(w0*z)+w0*v).

Target AST:
`0b7a36d2e72c832a07f9a5512667ba40107b5b367d5a8715c776889e56a485e5`.
Certificate: 231 nodes / 21,056 constructors / 969,777 bytes; bundle
`07d48fca1276244b05d415dc9c46a505b1fd357dc8178abea55a624e7347ff7e`.
All 214 AP094 prefix rows and the actual AP015 arithmetic body are retained.
The 23 definitions are unchanged; no new induction, axiom or solver admission.

WMI job **284698**, snapshot
`ad4ebd383f177ad1989942b3d643d9b86af632e8ab00a53c12c7589025c06d2e`,
completed 0:0 in 3m22s on cpu/c5n1 with one CPU / 4 GiB. HA generation/replay:
14.986556 / 7.743126 CPU seconds. Fresh same-data Lean: 6.489492 CPU /
9.154838 wall seconds, all nine checker modules and both negative controls.
All 13 new proof regressions, 26 predecessor proof regressions, 14 controller,
19 migration and eight offline-wheel-staging tests passed. The local eight-test
precheck hit its unchanged 30-second CPU limit after six progress dots; it
remains recorded as incomplete, not silently relabelled as passing.

Evidence: `observations/requested-half-transport-wmi-progress-audit-v1.json`,
the HA/Lean folders `shared-wave-requested-half-transport{,-lean-wmi}-v1`, and
`observations/wmi-ap095-full-v1/collection.json` under the campaign directory.
Totals: **212 additional / 245 distinct checked statements / 1,619 focused
regressions**. IR072 and all IR parents remain open. No admission or publication.

Next mathematical work remains explicitly unproved:

1. Finish the fixed-program interpretation using the now-checked AP095
   requested-precision half-root comparison. Join AP020's odd-reciprocal
   interpretation, AP085-AP092's checked fixed
   schedules and positive witnesses, and the finite-to-limit interpretation
   without adding accuracy to any computation definition. AP060 handles only
   equal rational arguments; AP081's prescribed degree must not be identified
   silently with an unrelated supplied one. Keep AP094's original 18/d error
   when budgeting the remaining input and Taylor-tail errors; the weaker
   requested bound must not be spent separately on every error term. AP095
   proves neither the earlier proposed 7*2^-k total error nor IR026/IR027.
   The next advance must address this interpretation or the arbitrary-integer
   auxiliary-function identity, not another equivalent witness wrapper.
2. Apply AP080's requested power precision to the actual auxiliary-function
   factors, with their proved input bounds and budget. Keep all actual powers
   and positive denominators; preserve the separate treatment of rationals
   outside the positive candidate range. Do not add an unrelated generic
   power API or infer analytic jet identities from finite power arithmetic.
3. Combine the positive witness construction AP066, the two-budget adapter
   AP081, AP084's uniform near-two bounds and the fixed log/root witnesses. Establish
   finite-to-limit identification of the fixed computation, including
   exp(L)=2, exp(L/2)=sqrt2, and its required range and accuracy. The
   computation-only definitions must not acquire accuracy assumptions.
   Sharpen or consistently enlarge the final quantitative constants;
   AP073's `9^(L+1)` must not silently replace a sharper bound in U.
4. Build quantitative finite addition/scaling and logarithm/root identities,
   then the variable-multiplicity interpolation, auxiliary linear system,
   nonzero jet, norm lower bound and final positive nonvanishing certificate.
   IR072/G121 remains open until the entire target has closed HA and same-data
   fresh Lean verification; TR006/G122 stays deferred.

The Euler-product/convolution route now has actual finite recurrence, head,
sum, tail and requested product-error theorems through AP064/AP067. Reuse those
results for arbitrary integer scaling and the actual two-frequency auxiliary
nodes; do not restart with more fixed composition instances. Analytic
interpretation, original-program accuracy, variable-multiplicity interpolation
and the final positive certificate are still separate integration obligations
before IR072 can close.

The completed AP005/AP007-AP015 horizon route splits l=0 or l=S j. At zero use AP005;
otherwise align the fine degree (k+l)+2 with S(k+2)+j, construct the shorter
sum of the same fine term table, restrict its recurrence, apply AP007, and
use CV100 on that actual prefix and whole sum. A proposed rational reading is
fine_output-coarse_output<=27/p+2/2^(k+2) and
coarse_output-fine_output<=9/d. These finite estimates, power comparison and
dyadic Cauchy budget are now checked. Fixed-algorithm interpretation and
analytic identification remain open.

The approximation-computation assembly follows this explicit dependency route
(partly checked by AP001-AP002, still not an admitted CApprox graph):

1. For k=n+8, use a coefficient prefix of length S(2*k). Its extra even-index
   coefficient is zero, so it represents the same k odd logarithm terms;
   prove that identification rather than silently changing the sequence.
   Construct actual nonzero scale D, coefficient codes, base-three Horner value
   x and actual power p=3^(S(2*k)). CV025 and the existing Horner totality
   provide the finite computations; CV086 applies directly to this length.
2. Construct DyadicSqrt2(k,d,s). Set the outer argument numerator to 3*x*d and
   denominator to (D*p)*s. Prove this denominator nonzero and the numerator
   at most it, using the sharp inner bound and d<=s. These are conclusions,
   not clauses of an approximation-accuracy definition.
3. At degree k+2 use CV070 to construct the actual exponential term prefix,
   nonzero normalization/head and actual sum. The output rational is sum/head.
   Retain every power, factorial and beta-trace datum that the eventual
   bounded verification predicate needs; never add an unused opaque trace.
4. Freeze the exact computational graph only after checking its canonical
   primitive-recursive algorithm/trace interpretation and proving value
   independence of auxiliary encodings and scales. Existing total relations
   alone are not yet a certified particular approximation algorithm.
5. Combine the supplied dyadic/reciprocal moduli, independent logarithm
   truncation and CV102's two finite exponential errors. Then prove analytic
   identification separately, including exp(L)=2 and the required range.
   The finite constructions in steps 1-3 are now supplied by AP001-AP002;
   AP020 now supplies the finite odd-sum identification; steps 4-5 still
   require their stated proofs.

Do not identify an
arbitrary truncated product evaluation with the full product: a support
premise or an explicit nonnegative omitted-degree tail is required. Actual
trace witnesses and explicit power/factorial data must be retained throughout.
For the later analytic comparison, separate the outer factorial tail, inner
odd-reciprocal tail and omitted-degree tail. The latter needs an actual
nonnegative-coefficient majorant, not a formal-series convergence assumption.

Finite estimates now checked: at x=1/3 use a majorant radius rho=1/2.
CV066 bounds the nonnegative inner polynomial at rho, CV071-CV074 provide
the finite exponential majorant 9, and CV075-CV080 bound omitted degrees
>=N by 9*(2/3)^N on an actual full composition. Their combination with the
geometric prefix at base three and any analytic-limit interpretation remain
separate obligations; CV034 alone never supplied those estimates.

Execution update (2026-10-01): the original planning inventory below is retained.
The source-pinned shared-proof wave is recorded separately in
`research/arithmetic-library/sqrt2-power/observations/shared-wave-index-v5.json`
and the local `wave-results.html` / `local-definitions.html` pages. It checks
six rational-equivalence foundations, the natural twice-square core via the
existing Fermat-four dependency cone, P10, two supporting lemmas and thirteen
finite composition chunks in HA and independently compiled Lean. SN001 now
extends the twice-square zero criterion to arbitrary signed coefficients using
the unchanged ND0157 definition and 22 actual prior proof nodes. The wave has
33 distinct checked statements, not 33 major campaign milestones. The earlier
four were the natural strict-gap lemma NG001, signed integer norm separation
SN002, signed quadratic norm multiplicativity SN003, and universal natural
convolution vanishing CV001. All four pass fresh HA and freshly compiled Lean.
ND0157 is reused unchanged; two local primitive-equation component aliases
ND0388/ND0389 and eight reused convolution definitions have exact expansion
gates. The checked arithmetic DAG derives its solid edges from actual proof
bundles and distinguishes them from open parent support.

The September 30 extension proved RN001 (rational norm independence from signed
representatives and nonzero denominators), RN002 (norm multiplication with
explicit squared denominators), and SI001 (nonzero signed-integer binary
products with arbitrary output representatives). All three passed ordinary HA,
fresh independent Lean and independent Z3 conjecture checks. The Z3 logs do not
enter HA as axioms or imported proof certificates. No additional definition was
introduced. RN002 includes the full SN003 dependency bundle; this actual edge
is visible in the checked DAG.

The October 1 extension proves QN001: two nonzero signed quadratic integers
have a nonzero product, with arbitrary signed input and output representatives.
QF001 then proves by genuine HA induction that an actually decoded finite
product trace starting at one preserves nonvanishing when every factor is
nonzero. Both passed first-attempt HA generation, fresh ordinary replay, and
independently freshly compiled Lean checking with negative controls. Their
complete proof bundles have respectively 221/81,273 and 224/81,603 shared
nodes/ordinary body constructors. Lossless sharing reuses actual proof bodies,
never receipts, and avoids rerunning large parent producers. No new solver
result is used as proof authority. The index now preserves all eight earlier
failed attempts among 42 attempts and eleven fresh-Lean observations.

Four local conservative aliases ND0390–ND0393 form the explicit finite-table
definition DAG: decoded coordinates, actual product step, trace starting at
one, and a separate nonzero-factor predicate. Execution does not assume its
nonvanishing conclusion. Their exact expansion and definition-use edges are
distinct from the actual SN001/SN003/SI001 → QN001 → QF001 proof edges.

Three composition chunks remain size-limited. IR072, the real-algebraic norm
lower bound, real interpretation, and universal analytic bridges remain open.
The rational representation and product-denominator laws above do not establish
these analytic claims. QF001 is conditional on a supplied trace: construction
of traces, rational-denominator transport and real interpretation are not
silently included, and IR046 remains open.
CV001 does not yet establish ascending rational-series power execution or
exp/log composition. Two failed CV001 attempts and an unmodified-checker
diagnostic are preserved; ordinary typed local-lemma annotations repaired
the certificate without changing any kernel rule. No Alpha/Stable admission
is implied. The previous v1/v2/v3/v4 evidence indices remain preserved.

Next bounded algebraic target: for every factor table and length L, construct
the four accumulator tables satisfying IQuadProductTrace, without a nonzero
hypothesis. Existing exact beta_at_exists and beta_prefix_extend bodies give
the prospective construction cone (101 nodes, 4,599 ordinary body nodes).
Append the successor at S L, preserving both the current entry at L and every
earlier transition. This is an audited next proof plan, not checked evidence.
Then obtain a terminal witness and combine with QF001 before proceeding to
coefficient-height bounds and the moment-polynomial nonvanishing argument.

This is a detailed proof specification and execution policy, not a proof receipt.
No lemma in this new campaign is currently admitted, no proposed definition is
claimed to have passed kernel expansion checking, and no production deployment
is authorized by this planning document. Historical Alpha v35 and Stable are
unchanged. Jordan and the previous campaigns remain preserved; they are not the
current research priority.

## 1. Controlling artifacts and what counts as completion

The authoritative individual contracts are in
`scripts/sqrt2_power_campaign_spec.py`. The deterministic generator
`scripts/build_sqrt2_power_campaign.py` produces:

- `book/_static/constructive-sqrt2-power-campaign/index.html`: canonical
  Quadratic Reciprocity-style planning entrance;
- `map.html`: drill-down planning DAG, including proposed definition edges;
- `lemmas/<ID>.html` and `definitions/<ID>.html`: every individual contract;
- `api/plan.json`: portable worker queue, edges, methods, risks and budgets;
- `pilot.html`: twelve fixed child contracts and their required hostile tests;
- `grand-campaign/`: additive combined atlas, with F13/D06 and open G121/G122;
- `api/manifest.json`: deterministic hashes of the generated presentation.

There are **81 irrationality lemma contracts**, **26 proposed definition
contracts**, **9 engineering/contingency gates**, and **6 phase-two contracts**.
These are work-package counts, not a claim that exactly 81 final kernel lemmas
will suffice. A package must be split further if its elaborated proof obligation
is too large for deterministic execution. IRD identifiers are planning IDs, not
new PD/ND kernel-definition identities. Existing compatible definitions must be
reused after exact argument-alignment review.

The mathematical acceptance criterion is a closed ordinary HA proof of:

    forall ap am b. b>0 ->
      exists n up um ud e trace.
        CApprox(n,up,um,ud,trace) and Pow(2,n,e) and
        [((b*um+ap*ud)*e + 2*b*ud < (b*up+am*ud)*e) or
         ((b*up+am*ud)*e + 2*b*ud < (b*um+ap*ud)*e)].

Here `a=ap-am`, `u_n=(up-um)/ud`, and `ud>0` is enforced by CApprox.
`Pow`, `<`, and CApprox are relational abbreviations, not added kernel symbols;
`x<y` expands to `exists k. x+S(k)=y`. All decoding and computation witnesses
must be exposed in the expanded first-order formula. This skeleton is not yet
the registered/parser-checked kernel statement: ENG001 freezes that statement.

The analytic interpretation must also be established, not merely asserted:
`|u_n-c|<=2^-n` for the positive real power `c=(sqrt2)^(sqrt2)`.
Consequently a successful finite certificate implies `|b*c-a|>b*2^-n>0`.
Neither finitely many rational examples nor the negative assertion `c!=a/b`
alone closes IR072. Completion requires original-kernel closure, independently
compiled Lean checking of the same certificate data, mutation tests and complete
dependency provenance. Promotion/deployment are separate later actions.

## 2. Scope control and proof architecture

The primary route is **direct finite perturbation**, entirely reconstructed in
HA. We use specific rational sequences and finite polynomial identities, not
a new real-number sort, a general real-analysis library, complex analysis,
arbitrary function spaces, compactness or a choice oracle.

The route is:

1. Certify the fixed square-root/logarithm/exponential approximation algorithms.
2. Construct exact auxiliary jets in Q(sqrt2) for an arbitrary rational a/b.
3. Obtain a small nonzero integer kernel vector by finite pigeonhole.
4. Find a nonzero jet by a **moment-polynomial identity**, not a general
   Vandermonde determinant or matrix-rank algorithm.
5. Separate that algebraic jet from zero by the quadratic norm.
6. Prove a denominator-cleared confluent interpolation identity and explicit
   finite Taylor bounds.
7. Bound the effect of replacing c by a/b. This removes the need to assume that
   the actual analytic jets vanish exactly.
8. Refute failure of one explicitly selected **decidable rational test**.
   Decidability, not Markov's principle, produces the positive certificate.

The classical negative argument remains useful as checkpoint IR065. A checked
negative/Friedman translation compiler is contingency ENG009 only. It is not a
prerequisite, is not already implemented, and may not import an arbitrary Lean
proof into arithmetic. The general PA/HA conservativity theorem cannot repair
missing arithmetization.

## 3. Exact finite constructions and deliberately generous constants

All the following equations are **contracts to prove**, not facts certified by
the current kernel. Loose bounds are intentional: the proof does not need an
optimized irrationality measure.

### 3.1 Fix the constant independently of the desired theorem

For requested precision n, set k=n+8, and compute by exact rational arithmetic:

    s = isqrt(2 * 2^(2*k)) / 2^k,
    L_k = 2 * sum(j<k, 1 / ((2*j+1)*3^(2*j+1))),
    t = L_k / s,
    u_n = sum(j<=k+2, t^j / j!).

The square-root search is bounded and s>=1. Prove the logarithm tail <=9^-k,
the square-root bracket width 2^-k, and the exponential tail bound. Then prove
the quotient error <=2*2^-k. Execution simplification (2026-10-02): use the
already-checked finite exponential continuity constant 9, rather than spend
new proof work sharpening it to 3. The proposed error budget becomes
`18*2^-k + 2/2^(k+2) < 19*2^-k < 2^-n`, still with the same k=n+8 and
the same computation. This is a planning estimate, not a checked limit
theorem: prove all quotient and tail bounds, the finite-to-limit passage,
`|u_n-c|<=19*2^-k<2^-n`, and `1<=u_n<=2` separately. The upper bound 2
requires the analytic identification exp(L)=2, not merely the majorant 9.

It is essential to prove `exp(L)=2`, where L is the limit notation for the fixed
logarithm series. IR079-81 break this into finite formal-composition identities,
coefficient recurrence uniqueness, and explicit composition tails at 1/3.
Only then derive `exp(L/2)=sqrt2` and identify c with `exp(L/sqrt2)`.

No definition is allowed to include its promised approximation error as a
premise. The computation relation and its accuracy theorem are separate.

### 3.2 Auxiliary coefficients with exact dimensions

For a signed integer a and b>=1, set

    H = max(2, |a|, b),
    q = 28 * 2^44 * H^12,
    n = q^2 / 28,       N = q^2,
    D = b^(6*(q-1)),
    T = (3q)^n * (2H)^(6q),
    B = 2*N*T.

Let s=sqrt2, z=a/b, L0=L/2, x_ell=ell*L0 for ell=0,...,6, and frequencies
lambda_(i,j)=i+j*s for i,j<q. Define the exact quadratic jets

    A_(ell,k) = sum(i,j<q, beta_(i,j)*lambda_(i,j)^k*s^(ell*i)*z^(ell*j)).

For k<n impose both integer coordinates of D*A_(ell,k)=0. The matrix has
14n=N/2 rows and N columns. Each entry has absolute value <=T, using the
submultiplicative weighted coefficient height `|U|+2|V|` in Z[sqrt2].

For an M-by-N matrix, N=2M, finite pigeonhole on `{0,...,2NT}^N` gives a
nonzero kernel vector beta with `max|beta|<=2NT=B`. This is witnessed
nonzeroness of a coordinate, not mere inequality of two beta-encoding numbers.
The exact image-box count and strict inequality are separate IR040-42 lemmas.

**Never instantiate this enormous auxiliary matrix in a routine computation.**
q(H) is a symbolic proof bound. The formal proof uses induction and finite-data
existence theorems; numerical certificates use the much smaller direct search
through u_n. No assertion of a practical extracted running time is made.

### 3.3 Bounded nonvanishing without determinants

For a frequency lambda_t form

    P_t(X) = product(u!=t, X-lambda_u) = sum(k<N, p_(t,k)*X^k).

Finite sum interchange proves

    sum(k<N, p_(t,k)*A_(0,k))
      = beta_t * product(u!=t, lambda_t-lambda_u).

The frequencies are distinct by the elementary irrationality of sqrt2, and
their nonzero product is witnessed by norm multiplicativity. At a nonzero
beta_t this forces a nonzero A_(0,k), k<N. Bounded decidable search gives the
least r<N with **some** A_(ell,r)!=0 across all seven nodes, and a selected ell*.
Thus n<=r<N and all A_(ell,k)=0 for k<r. Choosing a minimum only at node zero
would not justify the later interpolation argument.

For

    K = N*B*(3q)^r*(2H^2)^(6q),

the integral quadratic norm of D*A_(ell*,r) gives `|A_(ell*,r)|>=1/K`.
The factor D must appear in the final rational lower bound. The arithmetic
core is `U^2=2V^2 -> U=V=0`, proved by parity descent in HA.

### 3.4 Confluent interpolation as finite polynomial arithmetic

Use multiplicity r+1 at x_ell* and r at the other six nodes. Their total is
7r+1, so the divided-difference order is M=7r, not 7r-1. Define

    C_(j,k) = [w^(m_j-1-k)] product(h!=j, (x_j-x_h+w)^(-m_h)),
    Dfun(f) = sum(j,k<m_j, C_(j,k)*f^(k)(x_j)/k!),
    P = product(h!=ell*, (x_ell*-x_h)^r).

Prove the selected coefficient is 1/P, and the exact reconstruction identity

    f^(r)(x_ell*) = r!*P *
      (Dfun(f) - sum((j,k)!=(ell*,r), C_(j,k)*f^(k)(x_j)/k!)).

The coefficients are obtained from **truncated** inverse-polynomial products.
No analytic infinite inverse series is a primitive. With 1/4<=L0<=1/2,

    |P|<=12^r,          |C_(j,k)|<=2^(21r).

Their denominator clearing is an explicit separate obligation IR078:
`C_(j,k)=L0^(-(M-k))*c_(j,k)` with the rational denominator of c_(j,k)
dividing 720^M. Multiplication by `M!*(720L0)^M`, and by the Taylor degree
factorial if necessary, reduces the identities to finite polynomial equations.

The monomial identity is Dfun(X^d)=0 for d<M, and
`Dfun(X^(M+v))=h_v(nodes)` otherwise. For nodes in [0,3],
`0<=h_v<=binomial(M+v,v)*3^v`. Apply this to finite exponential polynomials,
then use explicit tails and the finite derivative identity
`(E_d(lambda*t))^(k)=lambda^k*E_(d-k)(lambda*t)` for d>=k (zero otherwise).

This is the analytic bottleneck. A successful small Fraction experiment is
valuable for checking indices; it is not an HA proof for variable r and d.

### 3.5 Perturbation, explicit slack, and positive certificates

Quantitative dependency warning (2026-10-03): the newly checked uniform
finite-exponential majorant is `9^(L+1)`. It does not by itself justify the
sharper `2^(15q)` factor in the proposed U below. Before using this parameter
package, either derive that sharper bound by a separate checked argument or
recompute U, the power-of-two slack and the choice of q together. The displays
below remain a planning target, not already checked consequences of AP073.

Set

    U = N*B*12^r*(3q)^(7r)*2^(15q)*r!/(7r)!,
    J = 6q*N*B*(3q)^r*(4H)^(6q),
    S = 1 + 7r*r!*12^r*2^(21r).

The fixed-series identity
`exp((i+j*s)*ell*L0)=s^(ell*i)*c^(ell*j)` and power telescoping bound every
actual-versus-candidate jet discrepancy through order r by `J*|c-z|`.
Combining the selected discrepancy and all lower jets yields

    1/K <= U + S*J*|c-z|.

This display abbreviates a collection of finite rational inequalities with
explicit approximation budgets. IR075 normalizes quadratic polynomials as
`P(X)=U0+V0*X+(X^2-2)*Q(X)`. IR076 supplies the multivariate polynomial
substitution modulus. IR058 supplies Taylor tails. The total finite-evaluation
error must be at most 1/(4K); there is a 1/(2K) contradiction gap below.
“Take sufficiently accurate approximations” is not a permitted proof step.

The parameter arithmetic must establish

    U*K <= (2^88 * H^24 / r)^r <= 28^(-r) <= 1/4,

using n<=r, q<=r, q^2<=28r, r!/(7r)!<=r^(-6r),
`4q^8<=2^(10r)` and `2^55*3^11*7^5<=2^88`.

Set epsilon=1/(4KSJ), and choose p with `2^p>=12KSJ`. A witnessed bit-length
bound is convenient; a coarse explicit natural upper bound plus bounded search
is sufficient and avoids making optimized logarithmic search a prerequisite.
If the finite certificate test failed, then

    |c-a/b| <= |c-u_p| + |u_p-a/b|
             <= 3*2^(-p) <= epsilon.

Hence the right-hand side of the jet inequality is at most 1/(2K), before at
most 1/(4K) finite-evaluation error, contradicting its lower bound 1/K.
The test is decidable rational arithmetic, so HA proves its positive outcome.
This is not an invocation of a general real-order decision or Markov principle.

## 4. Lemma layers and critical path

Every contract's full dependencies, proposed definitions, method, induction
parameter and risk appear in the generated directory. The main groups are:

| Group | Obligations | Principal content |
|---|---|---|
| Arithmetic | IR001-012, IR076 | Rational representations, order, folds, bounded search, power differences, factorials, polynomial error moduli |
| Fixed constant | IR013-028, IR079-081 | Square root, log series, exponential, composition identities, correct c and certified approximations |
| Quadratic arithmetic | IR029-035, IR075 | Exact pairs, decidable equality, norm separation, frequency gaps, polynomial remainder certificates |
| Auxiliary construction | IR036-043 | Exact matrix dimensions, denominator clearing, entry bounds, finite pigeonhole and coefficient vector |
| Nonvanishing | IR044-049 | Annihilating polynomials, moment identity, least global nonzero jet and its lower bound |
| Interpolation | IR050-060, IR077-078 | Weak compositions, monomial functional, Hermite coefficients, denominator clearing, finite derivatives and tails |
| Bound comparison | IR061-065 | Exponential jet identity, interval bounds, symbolic exponent arithmetic, negative checkpoint |
| Positive endpoint | IR066-074 | Perturbation, excluded neighborhood, decidable certificate and total search |

Do not begin by grinding all easy algebra. The risk-first path is
IR079-081 (log-exp identity), IR055-058/078 (finite interpolation), and
IR068-070 (finite error and positive witness). Small executable prototypes of
these three bridges precede expensive general proof generation.

Not every display-level lemma is an atomic worker job. ENG001 must split any
large package into binder-complete base, step, transport and closure obligations
before dispatch. New child IDs must have a parent ID and unchanged parent
contract; no weakening is hidden by replacing a difficult parent statement.

## 5. Non-LLM methods: precise roles and trust boundaries

The original intuitionistic checker remains the only authority for native
proofs. The independent Lean verifier checks those same certificates; it is
not used to import classical real analysis.

| Method | Work assigned | Acceptance boundary |
|---|---|---|
| Native ring/compact arithmetic | Polynomial identities, recurrences, denominator clearing | Existing proof-producing tools, then fresh ordinary HA check |
| Exact integers and Fraction | Coefficient generation, sample interpolation, rational certificate tests | Computations are experiments unless expanded into a checked proof |
| Z3 | Guarded linear integer arithmetic, case and coefficient suggestions, counterexamples to proposed contracts | `unsat` and proof logs are hints until reconstructed |
| E and Vampire | First-order equational/logical leaves and useful premise instantiations | TSTP output is not an HA certificate; reconstruct supported steps |
| Deterministic induction generators | Predeclared finite-sum/product, coefficient and trace invariants | Base and step checked separately, assembled into actual HA induction |
| Exact polynomial reduction | Quadratic remainders and finite formal-series identities | Emit a polynomial identity witness and replay it natively |

Initial inventory on this machine: Z3 CLI 4.15.4 is present; Vampire, E,
eproof and cvc5 were not found on PATH. The default Python has no z3/pysmt
module; command-line Z3 avoids that dependency. No installation, cloud service
or licensing action is implied by this plan. Pin binary hashes/options when
tools are eventually installed under the normal approval workflow.

Important existing implementation limits:

- Native `engine/search.py:search(..., classical=False)`,
  `engine/ring.py:prove_ring_equation`, `norm_num.normalize_equality`, and
  `compact_arith.prove_compact_equation` are useful existing proof producers.
- `peano_lab.batch.run_proof` and the Hydra runner provide fresh replay.
- The stock `SymbolicCandidatePolicy` requires an **empty** theorem allowlist;
  checked-library retrieval needs a new reviewed policy, not a configuration lie.
- Hydra's native Dispatch currently permits refl/assumption/simp/norm_num/
  compact_arith, not ring/auto/vampire. Direct ring API use in a separate
  proof-producing worker is possible; extending Dispatch is separate work.
- Hydra scheduling uses threads, not a process resource boundary.
  `training/peano_hydra/review_runtime.py:run_bounded` with `ProcessLimits`
  supplies process supervision. It rejects observed descendants; do not use
  solver-internal multiprocess portfolios. macOS RSS needs the parent sampler.

### External reconstruction policy

Start with **hint-only integration**, which is smaller than a universal TSTP
or SMT proof importer. Export only frozen, elaborated leaf obligations. Retain
the original HA target, exact dependency allowlist, substitutions, natural
domain guards, positive denominators, solver input and output, versions and
hashes. Reconstruct suggested equality chains or instantiations with native
proof constructors, and recheck the original statement.

Classical clausification and Skolemization are not generally intuitionistically
sound equivalences. Neither a universal claim nor an existential witness may
be admitted from a refutation without the appropriate constructive bridge.
For a closed or appropriately universally quantified **decidable arithmetic
leaf**, a reconstructed contradiction plus proved decidability can justify the
step. Unsupported inferences, nonlinear theory lemmas, preprocessing and
unknown proof rules must fail closed. QF_LIA tools do not solve arbitrary
nonlinear integer inequalities; normalize/split these or use a separate checked
arithmetic certificate. Solver real exp/log approximations are forbidden here.

Only if the pilot shows a clear bottleneck should we implement a restricted
resolution/paramodulation or Farkas/cutting-plane certificate translator.
Every accepted rule needs a native derivation, with hostile tests for variable
capture, omitted premises, missing guards and altered target hashes.

## 6. Bounded execution waves and subagent handoffs

These are conservative proposed local limits, not a claim about total cost or
a request to spend external money. Adjust only with a recorded reason.

1. **Wave 0: freeze and calibrate.** Validate this DAG; review representations;
   run finite interpolation/approximation experiments. Audit exact existing
   library statements and the target's expansion. Keep all new claims planned.
2. **Wave 1: 12-obligation pilot.** Select representative arithmetic leaves,
   a coefficient identity, an induction base/step, a moment identity, a Hermite
   coefficient identity, a tail inequality, and a rational certificate leaf.
   Compare native-only against native plus solver hints. Do not call a sample
   instance the parent universal theorem.
3. **Wave 2: constant and quadratic foundations.** Complete IR001-035 and
   their actual dependencies, prioritizing IR024/079-081. Exact proof-producing
   normalization should do most routine leaf work.
4. **Wave 3: two independent mathematical branches.** Auxiliary matrix and
   moment construction (IR036-049), and interpolation (IR050-060/077-078).
   Subagents own disjoint factories/tests; share frozen prerequisite contracts,
   never mutable ambient theorem registries.
5. **Wave 4: explicit comparison and perturbation.** IR061-070; audit every
   error term and denominator. Run mutation tests on weakened bounds and wrong
   selected-node multiplicity before accepting the capstone construction.
6. **Wave 5: whole-target verification.** IR071-074 and ENG008: fresh ordinary
   HA and Lean closure; honest definition-aware publication materials. Only
   then consider Alpha promotion, commits and deployment under authorization.
7. **Wave 6: transcendence planning refinement.** TR001-006 remain open.
   Replace the quadratic norm by general finite algebraic separation, keeping
   the established analytic lemmas. No general Gelfond-Schneider theorem is
   required as an initial deliverable.

Default worker constraints: one local proof/solver worker, 768 MiB RSS,
8 MiB output, total portfolio CPU 60 seconds and wall 90 seconds **per leaf**.
The pilot has at most 12 leaves and an additional 1,200-second aggregate wall
ceiling. Baseline smoke has a separate 30-second total wall ceiling including
imports and replay. No retries after a failed attempt without a changed
contract/strategy; at most one bounded repair attempt. Unknown, timeout and
unavailable are ordinary recorded outcomes. Do not silently raise proof-depth,
formula-size, memory or kernel limits to make a job pass.

Subagent assignment must contain:

    obligation ID and original expanded target hash;
    exact allowed prerequisite IDs and statement/bundle hashes;
    definition expansion identities and binder map;
    induction variable/invariant or finite witness contract;
    permitted deterministic methods, argv and resource reservation;
    disjoint source/test ownership;
    expected certificate, fresh-check receipt and negative-test format.

The planning agent chooses decomposition and invariants. Deterministic tools
attempt routine proof leaves first. A proof subagent is requested only when
those attempts expose a specific missing lemma or reconstruction step. A
successful solver search is not reported as “proved” while reconstruction is
still missing. No theorem-source editing, Alpha admission or deployment is
delegated to an unrestricted solver process.

### Fixed twelve-child pilot

The complete child contracts and individual mutation tests are in the
specification's `PILOT` table and generated `pilot.html`. The scope is:

| Child | Parent | Fixed test of the method |
|---|---|---|
| P01 | IR002 | Rational addition respects cross-multiplied equality |
| P02 | IR031 | Quadratic norm multiplicativity, encoded without subtraction |
| P03 | IR009 | Power-difference induction step with the exact hypothesis |
| P04 | IR079 | Constant-coefficient base of formal exp composition |
| P05 | IR080 | Recurrence step for the candidate coefficients 2 |
| P06 | IR020 | A single factorial-tail contraction inequality |
| P07 | IR045 | Two-frequency moment-polynomial identity |
| P08 | IR055 | First truncated reciprocal coefficient identity |
| P09 | IR056 | Seven-node confluent monomial identity, r=1, selected node 3 |
| P10 | IR064 | Exact comparison 2^55*3^11*7^5<=2^88 |
| P11 | IR069 | Precision bridge after an explicit positive product witness |
| P12 | IR071 | Fixed CApprox certificate for a=3, b=2, n=6 |

These children are not yet binder-complete kernel statements. ENG001/002 must
freeze their elaborations and exact allowed premises before dispatch. Several
are intentionally instances or a single induction step: their success must not
close their universal parents. P04/P05/P09 test algebraic machinery, not the
full composition-tail or variable-multiplicity interpolation bottleneck.

Native-only and native-plus-hint runs use identical frozen formulas and share
the original 60-second CPU / 90-second wall reservation per child. A changed-
strategy repair also uses that reservation. Report unavailable E/Vampire as
unavailable, not as successful integrations; installation is a separate action.

## 7. Budget/coverage evidence and stop conditions

Measure separately, per original obligation and in aggregate:

- planned, elaborated, attempted, solver-solved, reconstructed, HA-checked,
  independently Lean-checked, and admitted counts;
- deterministic strategy, wall/CPU/RSS, proof bytes/nodes/depth, rejected
  rules, timeouts, cache hits and fresh replays;
- genuine model proof-search calls and tokens versus agent planning/review
  calls/tokens. Unknown token costs stay null; they are not reported as zero;
- wall time and verified coverage in a native-only ablation versus solver-hint
  runs on the same frozen leaf set. A higher solver-hit rate alone is not a win.

Hydra's legacy `model_calls` can count symbolic-policy requests; it must not be
mislabelled as actual LLM calls. CPU instructions and energy are null when not
measured. Training Qwen or using an LLM proof-search loop is outside this
campaign's initial scope.

Stop and revise the plan if any of these occurs:

- the log-exp identity or confluent interpolation cannot be reduced to the
  promised finite arithmetic contracts;
- positive irrationality is replaced by a merely negative statement;
- an induction hypothesis or target inequality is smuggled into a definition;
- reconstruction coverage is too low to justify an external solver adapter;
- repeated resource failures suggest proof representation/decomposition costs,
  rather than a need for a longer blind search;
- a proposed reuse depends on a different coefficient domain, unchecked
  candidate, classical mode, or mismatched statement.

This is a stage-gated research plan, not a guarantee of a completion date or
that a chosen percentage of final lemmas will be solved automatically. The
12-obligation pilot determines the next defensible budget and adapter scope.

## 8. Sources, novelty, and presentation policy

- [Friedman, 2000](https://fomarchive.ugent.be/2000-June/004116.html): the
  Gelfond-Schneider Pi02/PA-to-HA route is explicitly conditional on arithmetic
  formalizability. This foundational idea is not new.
- [Selinger, Friedman's A-translation](https://www.mathstat.dal.ca/~selinger/papers/friedman.pdf):
  fallback proof transformation, with axiom and eigenvariable obligations.
- [Karatarakis and Wiedijk, 2026](https://arxiv.org/html/2603.24823v1): a
  classical Lean Gelfond-Schneider development exists. It is neither an HA
  certificate nor evidence that our arithmetization is finished.
- [Sadiq and Viswanath, Section 2](https://arxiv.org/html/1105.3466v2#S2):
  finite truncated-product construction of barycentric Hermite coefficients.
  Our arithmetic reconstruction and explicit bounds remain separate obligations.
- [Z3 proof logs](https://microsoft.github.io/z3guide/programming/Proof%20Logs/):
  big-step proof hints can need further solving; not every log is an elementary
  independently replayable certificate.
- [E](https://github.com/eprover/eprover): proof objects are available, but its
  documented checker skips nonclausal first-order material. That is not our HA
  acceptance criterion.
- [Vampire releases](https://github.com/vprover/vampire/releases): pin supported
  proof-output interfaces and versions before implementing any adapter.

The public design follows the established Quadratic Reciprocity shell and
unchanged proofs.css. Planned edges, proposed definition expansion edges and
notation-use edges remain distinguishable. A planning page never says “read
the final proof”; real exact/defined theorem explorers are added only when
there are authenticated proof artifacts to read.

The combined planning atlas adds F13/D06 and G121/G122 without rewriting the
144 nodes of the sealed 120-goal parent or increasing its checked-theorem
counts. Existing proof links continue to point to their established pages.
The new campaign is generated locally first; public hosting remains unchanged
until a later authorized deployment and its validation gates succeed.

## 9. Bounded execution checkpoint (2026-09-19)

The [local execution dossier](../research/arithmetic-library/sqrt2-power/README.md)
now records eight fresh ordinary-HA-checked pilot leaves: three full pilot
contracts and five supporting subleaves. P07 is explicitly limited to signed
integers. None closes an IR parent or admits a proposed definition.

All three classical solvers are operational. The post-hardening run took 72.49
wall seconds; two-second calls produced Z3 8/8, E 3/8 and Vampire 1/8 hits.
This is a native-only / solver-gated reproof integration baseline, **not** a
proof-log translator or evidence of solver acceleration. Agent engineering
cost remains unmeasured, not zero.

P10 exposed repeated proof-body copying. Its memory-guard stop and its single
changed-strategy, fail-closed retry are retained. No larger limit is authorized
by this checkpoint. The next engineering gate is per-operation proof-bundle
sharing, followed by the exact finite-composition, confluent and approximation
traces. P04/P09/P10/P12, full domain lifts, and contract-specific mathematical
hostile witnesses remain open. The primary irrationality target is unchanged.
