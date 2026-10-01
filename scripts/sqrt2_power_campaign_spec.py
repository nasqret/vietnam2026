"""Authoritative planning contracts, NOT admitted definitions or HA theorems.

Universal closure and rational/algebraic notation are specification shorthand.
ENG001 must elaborate each contract to the unchanged first-order HA signature
before a worker may claim a proof. Generated JSON is the portable work queue.
"""

SCHEMA = "sqrt2-power-ha-campaign-plan-v1"
SLUG = "sqrt2-power"
TITLE = "Irrationality of (√2)^(√2)"
DATE = "2026-09-19"
PARENT = "book/_static/constructive-jordan-campaign-v35"

GROUPS = {
    "A": "Arithmetic contracts and finite certificates",
    "S": "Certified square root, logarithm, and exponential",
    "Q": "Exact quadratic arithmetic",
    "L": "Small integer kernels and auxiliary coefficients",
    "V": "Moment polynomials and bounded nonvanishing",
    "H": "Finite confluent interpolation",
    "B": "Explicit upper and lower bounds",
    "P": "Perturbation and positive irrationality",
    "T": "Transcendence: phase two, not current execution",
    "E": "Automation, reconstruction, and release gates",
}


def definition(identifier, name, parameters, expansion, dependencies=()):
    return dict(id=identifier, kind="definition", title=name,
                parameters=parameters.split(), arity=len(parameters.split()),
                contract=expansion, deps=list(dependencies), status="proposed",
                kernel_definition_id=None, expansion_ast_sha256=None,
                authority="planning_only", group="definitions", phase=1)


DEFINITIONS = [
    definition("IRD01", "RatRep", "p m d", "d>0; represented value is (p-m)/d. No coprimality or canonical-code equality is assumed."),
    definition("IRD02", "RatEq", "p m d P M D", "RatRep(p,m,d) and RatRep(P,M,D) and p*D+M*d=m*D+P*d.", ["IRD01"]),
    definition("IRD03", "RatLt", "p m d P M D", "RatRep(p,m,d) and RatRep(P,M,D) and exists k. p*D+M*d+S(k)=m*D+P*d.", ["IRD01"]),
    definition("IRD04", "RatInterval", "q lo hi", "Decode three rational triples; RatLt-or-RatEq(lo,q) and RatLt-or-RatEq(q,hi). Decoding witnesses remain explicit.", ["IRD02", "IRD03"]),
    definition("IRD05", "RatFold", "xs length trace result", "A beta-coded finite addition/multiplication execution; all input/output triples have positive denominators. It does not assert any analytic estimate.", ["IRD01", "IRD02"]),
    definition("IRD06", "Sqrt2Bracket", "k z pow trace", "pow=2^k by the existing Pow graph, and integer-square-root trace establishes z²<=2*pow²<(z+1)². Bracket endpoints z/pow and (z+1)/pow.", ["IRD04"]),
    definition("IRD07", "Log2Partial", "K value trace", "value=2*sum(j<K,1/((2*j+1)*3^(2*j+1))) by a rational fold trace; no limit or inverse-exponential assertion is part of the definition.", ["IRD05"]),
    definition("IRD08", "ExpPartial", "x N value trace", "value=sum(j<=N,x^j/j!) by witnessed powers, factorials and a rational fold; denominator positivity is explicit.", ["IRD05"]),
    definition("IRD09", "CApprox", "n up um ud trace", "k=n+8; s=floor_sqrt(2*2^(2*k))/2^k; L=Log2Partial(k); t=L/s; u=ExpPartial(t,k+2). trace witnesses these actual computations; (up-um)/ud=u. No error bound is assumed.", ["IRD06", "IRD07", "IRD08", "IRD02"]),
    definition("IRD10", "IrrCert", "ap am b n up um ud e trace", "b>0 and CApprox(n,up,um,ud,trace) and e=2^n and [(b*um+ap*ud)*e+2*b*ud < (b*up+am*ud)*e or (b*up+am*ud)*e+2*b*ud < (b*um+ap*ud)*e].", ["IRD09"]),
    definition("IRD11", "QuadRep", "A B D", "A,B are witnessed signed integers and D>0; denotes (A+B*sqrt2)/D. sqrt2 is semantic shorthand only, not a kernel term.", ["IRD01"]),
    definition("IRD12", "QuadMul", "x y z", "Decode quadratic triples; z represents ((A*C+2*B*E)+(A*E+B*C)*sqrt2)/(D*F). Equality is of coefficients after cross multiplication.", ["IRD11", "IRD02"]),
    definition("IRD13", "QuadNorm", "x norm", "For x=(A+B*sqrt2)/D, norm is the signed rational (A²-2*B²)/D².", ["IRD11", "IRD01"]),
    definition("IRD14", "AuxParameters", "ap am b H q n N", "H=max(2,abs(ap-am),b), b>0, q>0, 28 divides q, N=q²=28*n. A reviewed choice of q(H) is a theorem, not a premise silently hidden here."),
    definition("IRD15", "Frequency", "q i j lambda", "i<q and j<q and lambda is the quadratic pair (i,j,1).", ["IRD11"]),
    definition("IRD16", "AuxJet", "a b q coeff ell k value trace", "value=sum(i,j<q, coeff[i,j]*(i+j*sqrt2)^k*(sqrt2)^(i*ell)*(a/b)^(j*ell)) in exact quadratic arithmetic. Signed coefficients and 0^0=1 are explicit.", ["IRD12", "IRD15", "IRD05"]),
    definition("IRD17", "AuxMatrix", "a b q n matrix trace", "Two signed integer coordinate rows per (ell<7,k<n), obtained from AuxJet by the uniform multiplier b^(6*(q-1)); columns enumerate i*q+j.", ["IRD16", "IRD14"]),
    definition("IRD18", "AuxKernelVector", "matrix N coeff B trace", "coeff is an actual length-N signed integer vector, not all zero, max abs(coeff)<=B, and every decoded matrix-row dot product is zero.", ["IRD17"]),
    definition("IRD19", "NodeBracket", "ell precision lo hi trace", "Rational enclosures for x_ell=ell*Log2/2, obtained from the fixed Log2Partial sequence, for ell<7.", ["IRD07", "IRD04"]),
    definition("IRD20", "HomogeneousSum", "nodes degree value trace", "Finite sum of all monomials of total degree in the listed nodes, with explicit weak-composition enumeration.", ["IRD05"]),
    definition("IRD21", "ConfluentFunctional", "nodes mults polynomial value trace", "Finite repeated-node divided difference of a polynomial, defined algebraically by a recurrence/monomial table. Equality cases use multiplicities, not division by zero.", ["IRD20"]),
    definition("IRD22", "HermiteBasis", "nodes mults ell k polynomial trace", "Explicit finite product and truncated reciprocal-series construction of a cardinal Hermite polynomial. Its cardinality identities are separate theorems.", ["IRD05", "IRD21"]),
    definition("IRD23", "JetErrorBound", "a b q coeff ell k eps bound trace", "Finite positive rational expression bounding the difference between AuxJet at a/b and the fixed-exponential jet, under |c-a/b|<=eps. This definition records the expression, not its validity.", ["IRD16", "IRD08"]),
    definition("IRD24", "SeparationSchedule", "H q n B K W eps precision trace", "A finite computation selecting positive rational error budgets and dyadic precision from explicit bounds; no irrationality or search-termination hypothesis is allowed.", ["IRD14", "IRD23"]),
    definition("IRD25", "IntegerPolynomial", "code degree trace", "Decode an actual signed coefficient list; nonzero means some decoded coefficient is nonzero. Reuse the existing polynomial representation after argument-alignment review."),
    definition("IRD26", "TransCert", "poly precision witness", "A CApprox computation and exact rational evaluation establish |P(u_precision)|>2*M_P*2^(-precision), with M_P=1+sum(j>=1,j*abs(a_j)*2^(j-1)).", ["IRD09", "IRD25"]),
]
for _row in DEFINITIONS:
    if _row["id"] in {"IRD25", "IRD26"}:
        _row["phase"] = 2


def lemma(identifier, group, title, contract, deps=(), definitions=(),
          method="native-ring", induction="none", risk="routine", phase=1):
    return dict(id=identifier, kind="lemma", group=group, title=title,
                contract=contract, deps=deps.split() if isinstance(deps, str) else list(deps),
                definitions=definitions.split() if isinstance(definitions, str) else list(definitions),
                method=method, induction=induction, risk=risk, phase=phase,
                status="planned", authority="planning_only", statement_ast_sha256=None,
                native_ha_receipt=None, independent_lean_receipt=None,
                worker_state="blocked_on_contract_elaboration")


# Dependencies are proposed mathematical obligations, never claimed proof edges.
LEMMAS = [
    lemma("IR001", "A", "Rational representation equivalence", "Positive-denominator RatEq is reflexive, symmetric and transitive; signed numerator pairs may be noncanonical.", definitions="IRD01 IRD02"),
    lemma("IR002", "A", "Rational operations respect representation", "Cross-multiplied addition, product and negation preserve RatEq; every constructed denominator is positive.", "IR001", "IRD02", "native-ring"),
    lemma("IR003", "A", "Rational order and decision", "RatLt and RatEq are decidable; exactly one of x<y,x=y,y<x holds for valid triples; positive-denominator clearing preserves strict inequalities.", "IR001", "IRD03", "native-order"),
    lemma("IR004", "A", "Absolute value and interval arithmetic", "Triangle/product inequalities and inclusion-preserving addition, multiplication and reciprocal on intervals with positive lower endpoint.", "IR002 IR003", "IRD04", "native-order"),
    lemma("IR005", "A", "Finite rational folds", "Every coded finite rational list has addition/product/factorial/power fold witnesses; results are unique up to RatEq, not unique codes.", "IR002", "IRD05", "native-induction", "list length"),
    lemma("IR006", "A", "Dyadic domination", "For each positive rational eta and natural A, construct t with (A+1)*2^(-t)<eta by an explicit natural bound; prove power monotonicity.", "IR003 IR005", method="native-induction", induction="natural exponent"),
    lemma("IR007", "A", "Finite pigeonhole", "An explicit map from a finite box with cardinality strictly exceeding a finite target box has two distinct inputs with the same output.", "IR005", method="native-induction", induction="finite target cardinality", risk="reuse-audit"),
    lemma("IR008", "A", "Bounded decidable minimum", "For decidable D and a witness i<N with D(i), construct least r<N with D(r) and all k<r satisfying not D(k).", "IR003", method="native-induction", induction="N"),
    lemma("IR009", "A", "Power difference factorization", "For integer e>=1, x^e-y^e=(x-y)*sum(j<e,x^(e-1-j)*y^j); if |x|,|y|<=H, then |x^e-y^e|<=e*H^(e-1)*|x-y|. Treat e=0 separately.", "IR004 IR005", method="native-induction", induction="e"),
    lemma("IR010", "A", "Geometric tail arithmetic", "For 0<=rho<1, every finite tail sum from K to K+M is <=rho^K/(1-rho), with denominator and rho=0 boundaries explicit.", "IR004 IR005", method="native-induction", induction="M"),
    lemma("IR011", "A", "Factorial lower bounds", "For t>=1, (t+1)!>=2^t; for r>=1,m>=1, (mr)!>=r! * r^((m-1)r). All quotient formulations are derived by positive clearing.", "IR003 IR005", method="native-induction", induction="t and factorial-product length"),
    lemma("IR012", "A", "Approximation operations without real sorts", "For the finitely many named rational-sequence codes used here, prove addition/product/reciprocal enclosure transport with explicit input-precision moduli; no quantification over arbitrary functions.", "IR004 IR006", "IRD04", "native-induction", "precision", "critical"),

    lemma("IR013", "S", "Integer square root totality", "For every v, construct z with z²<=v<(z+1)² by a bounded binary-search or existing division trace; establish uniqueness of z.", "IR003 IR008", "IRD06", "native-induction", "search interval length", "reuse-audit"),
    lemma("IR014", "S", "Dyadic sqrt2 enclosures", "For k>=1 and z²<=2*2^(2k)<(z+1)², 1<=z/2^k and the interval [z/2^k,(z+1)/2^k] has width 2^-k; enclosures are compatible across precisions.", "IR013 IR011 IR012", "IRD06", "native-order"),
    lemma("IR015", "S", "Sqrt2 algebra and strict bounds", "The fixed bracket sequence squares to 2 with an explicit multiplication modulus and lies strictly between 1 and 3/2. Derive the exact reciprocal and conjugation identities.", "IR014 IR012", "IRD06", "native-ring"),
    lemma("IR016", "S", "Even-square descent", "For natural A,B, A²=2*B² implies A=B=0; signed versions follow by absolute values. Replay in HA, not merely the separate Lean demo.", "IR003 IR008", method="native-induction", induction="strong induction on A+B", risk="reuse-audit"),
    lemma("IR017", "S", "Logarithm series remainder", "For L_K=2*sum(j<K,1/((2j+1)*3^(2j+1))), every finite extension increment lies in [0,9^-K]; construct a fixed compatible sequence from these bounds.", "IR005 IR010 IR012", "IRD07", "native-induction", "finite extension length"),
    lemma("IR018", "S", "Logarithm interval and node gaps", "2/3<=L<1 for the fixed log series; x_ell=ell*L/2 satisfies 0<=x_ell<3 and x_(ell+1)-x_ell>=1/3 for ell<6. A weaker [0,7] enclosure is allowed in bounds.", "IR017 IR012", "IRD19", "native-order"),
    lemma("IR019", "S", "Exponential partial-sum totality", "For every rational x and N, construct ExpPartial(x,N) with witnessed factorial and power tables; prove the successor recurrence and representation independence.", "IR005", "IRD08", "native-induction", "N"),
    lemma("IR020", "S", "Exponential explicit tail", "For x>=0 and N+2>=2*x, bound each finite tail beyond N by 2*x^(N+1)/(N+1)!; give an explicit N(x,t) making this <2^-t. Handle x=0 separately.", "IR019 IR010 IR011 IR006", "IRD08", "native-induction", "tail length and precision schedule", "critical"),
    lemma("IR021", "S", "Finite binomial convolution", "The degree<=N coefficients of ExpPartial(x+z,N) equal the corresponding convolution coefficients of ExpPartial(x,N)*ExpPartial(z,N); bound the discarded terms explicitly.", "IR009 IR019 IR020", "IRD08", "native-induction", "N", "high"),
    lemma("IR022", "S", "Exponential addition and integer powers", "For fixed rational-sequence arguments with supplied enclosures, exp(x+z)=exp(x)*exp(z), exp(0)=1, and exp(j*x)=exp(x)^j, witnessed to every finite accuracy.", "IR012 IR020 IR021", "IRD08", "native-induction", "j and precision", "high"),
    lemma("IR023", "S", "Exponential order and Lipschitz", "On [0,M], positive-series estimates give positivity/monotonicity and |exp(x)-exp(y)|<=3^(ceil(M)+1)*|x-y|; on [0,1] improve the bound to 3. Prove e<3 by a factorial tail.", "IR020 IR022 IR010", "IRD08", "native-order", risk="high"),
    lemma("IR024", "S", "Log-exp inverse at two", "For L given by IR017, specialize IR079-81 at z=1/3 to obtain exp(L)=2. Do not assume this identity in Log2Partial or appeal to an imported real logarithm.", "IR017 IR020 IR021 IR022 IR079 IR080 IR081", "IRD07 IRD08", "native-induction", "finite coefficient identities and explicit precision", "critical"),
    lemma("IR025", "S", "Canonical approximation totality", "For every n, CApprox(n,up,um,ud,trace) has witnesses with ud>0; results are unique up to RatEq. No unbounded numerical search is part of this algorithm.", "IR014 IR017 IR019 IR005", "IRD09", "native-induction", "finite algorithm traces"),
    lemma("IR026", "S", "Canonical approximation accuracy", "For k=n+8, the sqrt/log quotient error is <=2*2^-k and exponential truncation error <=2^-k; hence |u_n-exp(L/sqrt2)|<=7*2^-k<2^-n and 1<=u_n<=2.", "IR015 IR020 IR023 IR024 IR025", "IRD09", "native-order", risk="critical"),
    lemma("IR027", "S", "Identification with the requested constant", "From exp(L)=2 and positivity, exp(L/2)=sqrt2 and exp(L/sqrt2)=exp(sqrt2*L/2). Thus the fixed approximation sequence denotes the positive real power (sqrt2)^(sqrt2).", "IR015 IR022 IR024 IR026", "IRD09", "native-ring", risk="high"),
    lemma("IR028", "S", "A strict coarse enclosure", "Establish 3/2<c<7/4 from one exact rational CApprox computation and IR026; emit a native certificate for the finite rational inequalities.", "IR026", "IRD09", "native-numeral"),

    lemma("IR029", "Q", "Quadratic ring operations", "QuadRep addition/multiplication/conjugation respect cross-multiplied coefficient equivalence and satisfy commutative-ring laws.", "IR002 IR005", "IRD11 IRD12", "native-ring"),
    lemma("IR030", "Q", "Quadratic equality is decidable", "(A+B*sqrt2)/D=0 iff A=B=0; equality of two triples is equivalent to two signed integer equalities after clearing denominators.", "IR016 IR029 IR015", "IRD11", "native-order"),
    lemma("IR031", "Q", "Norm identity and multiplicativity", "N(x)=x*conj(x)=(A²-2B²)/D² and N(x*y)=N(x)*N(y).", "IR029", "IRD13", "native-ring"),
    lemma("IR032", "Q", "Integral quadratic norm separation", "If A,B are integers not both zero, abs(A²-2B²)>=1; hence |A+B*sqrt2|>=1/(|A|+2*|B|). Denominator is positive.", "IR016 IR030 IR031 IR015 IR004", "IRD13", "native-order"),
    lemma("IR033", "Q", "Quadratic powers and coefficient height", "For integer pair (A,B), powers have integer-pair traces; weighted height h(A,B)=|A|+2|B| is submultiplicative and h(i,j)<=3q for i,j<q.", "IR029 IR005 IR004", "IRD12 IRD15", "native-induction", "power exponent"),
    lemma("IR034", "Q", "Distinct frequencies with quantitative gap", "For distinct (i,j),(I,J) in [0,q)^2, their frequencies differ; give a nonzero quadratic norm and rational lower bound >=1/(3q) on the absolute gap.", "IR032 IR033", "IRD15", "native-order"),
    lemma("IR035", "Q", "Cleared rational quadratic lower bound", "If D>0 and D*g=A+B*sqrt2!=0, then |g|>=1/(D*(|A|+2|B|)); do not conflate the denominator D with a square or omit it.", "IR032 IR004", "IRD11 IRD13", "native-order"),

    lemma("IR036", "L", "Auxiliary parameter arithmetic", "q is a positive multiple of 28, N=q², n=N/28: n>=q, 14*n=N/2 and N=28*n. Dimensions are exact integers.", "IR003 IR005", "IRD14", "native-order"),
    lemma("IR037", "L", "Matrix row/column enumerations", "Column (i,j) maps bijectively to i*q+j<N; rows (ell,k,coordinate) biject with 14*n positions. Construct all tables from beta traces.", "IR036 IR005", "IRD17", "native-induction", "table length"),
    lemma("IR038", "L", "Uniform denominator clearing", "D=b^(6*(q-1)) clears every AuxJet coefficient for ell<7,k<n; powers of sqrt2 introduce no denominators. Equivalence of cleared coordinate zero and quadratic zero is proved.", "IR033 IR030 IR037", "IRD16 IRD17", "native-induction", "finite row/column enumeration"),
    lemma("IR039", "L", "Auxiliary matrix height", "For H=max(2,|a|,b), each cleared integer matrix entry has absolute value <=A=(3q)^n*(2H)^(6q). Prove inequalities symbolically; never materialize this huge matrix for the universal proof.", "IR038 IR033 IR009", "IRD17", "native-order", risk="high"),
    lemma("IR040", "L", "Linear-map image box", "For an M by N integer matrix bounded by A>=1 and x in {0,...,2NA}^N, each image coordinate lies in [-2N²A²,2N²A²].", "IR005 IR004", "IRD18", "native-induction", "dot-product length"),
    lemma("IR041", "L", "Strict box cardinality inequality", "If N=2M>0 and A>=1, (2NA+1)^N>(4N²A²+1)^M. Prove the base inequality by ring normalization and lift through positive powers.", "IR011 IR003", method="native-ring"),
    lemma("IR042", "L", "Small nonzero integer kernel vector", "Combine IR007,IR040,IR041: construct nonzero signed beta with matrix*beta=0 and max|beta|<=2NA; handle zero matrix separately if A=0 is exposed by an API.", "IR007 IR040 IR041", "IRD18", "native-induction", "finite-map construction", "high"),
    lemma("IR043", "L", "Auxiliary low jets vanish algebraically", "For B=2*N*(3q)^n*(2H)^(6q), construct beta not all zero, |beta|<=B, and AuxJet(a,b,q,beta,ell,k)=0 for every ell<7,k<n.", "IR036 IR039 IR042 IR038", "IRD16 IRD18", "native-search", risk="high"),

    lemma("IR044", "V", "Annihilating polynomial construction", "For each t<N construct P_t(X)=product(u<N,u!=t,X-lambda_u), its coefficient list of degree<N, and prove evaluation at every frequency. No determinant library is required.", "IR029 IR005 IR009", "IRD15", "native-induction", "finite factor-list length", "high"),
    lemma("IR045", "V", "Moment polynomial identity", "Writing P_t=sum(k<N,p_tk*X^k), prove sum(k<N,p_tk*A_(0,k))=beta_t*product(u!=t,lambda_t-lambda_u) by finite sum interchange and polynomial evaluation.", "IR044 IR005 IR029", "IRD15 IRD16", "native-induction", "finite double sums", "high"),
    lemma("IR046", "V", "Nonzero quadratic products", "A finite product of nonzero quadratic elements is nonzero, by norm multiplicativity and integer no-zero-divisors.", "IR030 IR031 IR005", "IRD13", "native-induction", "factor count"),
    lemma("IR047", "V", "Bounded nonzero jet at zero", "For nonzero beta and distinct frequencies, some k<N satisfies sum beta_j*lambda_j^k !=0. Use IR045 at a nonzero coefficient and bounded decidable search; no determinant or infinite-series argument.", "IR034 IR045 IR046 IR043 IR008", "IRD16", "native-search", risk="high"),
    lemma("IR048", "V", "Least nonzero jet across all nodes", "Decidable bounded search yields n<=r<N and ell0<7 with A_(ell0,r)!=0, while A_(ell,k)=0 for all ell<7,k<r. Minimality is across all seven nodes, not just zero.", "IR008 IR030 IR043 IR047", "IRD16", "native-search"),
    lemma("IR049", "V", "Selected jet height and separation", "For selected r, bound the cleared jet and its conjugate; prove |A_(ell0,r)|>=1/K with K=N*B*(3q)^r*(2H²)^(6q). Audit all b-denominator factors explicitly.", "IR035 IR033 IR038 IR048 IR039", "IRD16 IRD13", "native-order", risk="critical"),

    lemma("IR050", "H", "Weak compositions and homogeneous sums", "Construct the weak compositions of s into N+1 parts; count them as binomial(N+s,s), and implement the complete homogeneous sum h_s.", "IR005 IR007", "IRD20", "native-induction", "N+s", "high"),
    lemma("IR051", "H", "Monomial divided differences", "The algebraic repeated-node functional of order N sends X^j to 0 if j<N, and X^(N+s) to h_s(t_0,...,t_N), without assuming distinct nodes.", "IR050 IR009", "IRD21", "native-induction", "N and monomial degree", "critical"),
    lemma("IR052", "H", "Homogeneous-sum enclosure", "For 0<=t_i<=M, 0<=h_s<=binomial(N+s,s)*M^s. This includes s=0, M=0 and repeated nodes.", "IR050 IR004", "IRD20", "native-order"),
    lemma("IR053", "H", "Factorial-binomial cancellation", "binomial(N+s,s)/(N+s)!=1/(N!*s!); derive by positive integer factorial identities.", "IR011 IR005", method="native-induction", induction="s"),
    lemma("IR054", "H", "Finite exponential divided-difference estimate", "Apply IR051-53 to ExpPartial(lambda*t,J): for nodes in [0,M] and lambda>=0, its order-N functional is bounded by lambda^N/N!*ExpPartial(lambda*M,max(J-N,0)), with J<N handled separately.", "IR019 IR051 IR052 IR053", "IRD08 IRD21", "native-induction", "finite polynomial degree", "critical"),
    lemma("IR055", "H", "Polynomial Hermite cardinal basis", "Construct H_(ell,k) for multiplicities s_ell>0 and distinct nodes such that H_(ell,k)^(j)(x_i)=delta_(i,ell)*delta_(j,k) for j<s_i. Include the k! normalization explicitly.", "IR009 IR005 IR018", "IRD22", "native-induction", "truncated reciprocal-series degree", "critical"),
    lemma("IR056", "H", "Finite confluent interpolation identity", "For any rational polynomial f, repeated-node divided differences equal the corresponding finite linear combination of its node derivatives. Specialize multiplicities r+1 at ell0, r elsewhere, total order 7r.", "IR051 IR055", "IRD21 IRD22", "native-induction", "polynomial degree", "critical"),
    lemma("IR057", "H", "Explicit interpolation coefficient bound", "For L0=L/2 in [1/4,1/2], M=7r and multiplicities r+1 at ell0,r elsewhere: C_jk=[w^(m_j-1-k)] product(h!=j,(x_j-x_h+w)^(-m_h)); |C_jk|<=2^(21r), |P|<=12^r, P=product(h!=ell0,(x_ell0-x_h)^r). The lower-jet aggregate is bounded by W=7r*r!*12^r*2^(21r).", "IR055 IR056 IR018 IR004", "IRD22", "native-order", risk="critical"),
    lemma("IR058", "H", "Polynomial-to-exponential tail transfer", "For the finitely many derivatives and functional coefficients in IR056, construct J(t,N,lambda,W) making every omitted Taylor contribution <2^-t, including the multiplied functional error. Explicitly bound all nodes and frequencies.", "IR020 IR054 IR057 IR012 IR077 IR078", "IRD08 IRD21", "native-induction", "tail precision schedule", "critical"),
    lemma("IR059", "H", "Zero-jet interpolation estimate", "If all true exponential jets below r vanish at every node, then |F^(r)(x_ell0)| <= r!*12^r/(7r)! * N*B*(3q)^(7r)*2^(15q). Nodes lie in [0,3], so exp(9q)<3^(9q)<2^(15q). Derive via IR056/58, not Rolle or compactness.", "IR054 IR056 IR057 IR058 IR022 IR023", "IRD16 IRD21", "native-order", risk="critical"),
    lemma("IR060", "H", "Approximate-zero interpolation estimate", "Without assuming c=a/b: bound the selected actual jet by the IR059 analytic term plus W times the maximum of the true lower-jet residuals. Include normalization at the selected node and all 7r lower jets.", "IR056 IR057 IR058", "IRD21 IRD22 IRD23", "native-order", risk="critical"),

    lemma("IR061", "B", "Exponential jet identity", "For x_ell=ell*L/2, exp((i+j*sqrt2)*x_ell)=(sqrt2)^(i*ell)*c^(j*ell); jets multiply by (i+j*sqrt2)^k. Prove this through finite exponential identities and tails.", "IR027 IR022 IR033 IR058", "IRD16 IRD19", "native-ring", risk="high"),
    lemma("IR062", "B", "Growth on the interpolation interval", "For 0<=t<=3, frequencies<=3q and |beta|<=B, bound the derivative-order-7r series by N*B*(3q)^(7r)*2^(15q), using e<3 and 3^9<2^15.", "IR023 IR033 IR043 IR058", "IRD16 IRD08", "native-order"),
    lemma("IR063", "B", "Factorial and q-to-r descent", "With n<=r and q²=28n, prove r!/(7r)!<=r^(-6r) and q^(8r)<=28^(4r)*r^(4r), by cleared positive inequalities.", "IR011 IR036 IR048", method="native-order"),
    lemma("IR064", "B", "Explicit combined gap", "Set q=28*2^44*H^12, n=q²/28. With U=N*B*12^r*(3q)^(7r)*2^(15q)*r!/(7r)!, prove K*U<=(2^88*H^24/r)^r<=28^(-r)<=1/4 for n<=r<q². Intermediate contracts: 4q^8<=2^(10r), q^(10r)<=(28r)^(5r), 2^55*3^11*7^5<=2^88. Never expand the auxiliary matrix at this bound.", "IR049 IR059 IR062 IR063", "IRD14", "native-order", risk="critical"),
    lemma("IR065", "B", "Negative irrationality checkpoint", "If the fixed c sequence equals a/b at every accuracy, IR061 identifies its jets with AuxJet; IR048/49/59/64 contradict one another. Conclude not(c=a/b) for b>0, without a Markov axiom.", "IR048 IR049 IR059 IR061 IR064 IR026", "IRD16 IRD09", "native-search", risk="high"),

    lemma("IR066", "P", "Rational competitors outside the unit interval", "For z=a/b outside [1,2], IR028 gives a positive explicit separation from c. Construct a precision certificate using IR006 and IR026; signed/negative/zero a are included.", "IR028 IR026 IR006 IR003", "IRD10", "native-order"),
    lemma("IR067", "P", "Uniform perturbation of algebraic jets", "For z=a/b, H=max(2,|a|,b), c<=4, prove |F^(k)(x_ell)-A_(ell,k)(z)|<=J*|c-z| for ell<7,k<=r, J=6q*N*B*(3q)^r*(4H)^(6q). Use power telescoping, including exponent zero.", "IR009 IR061 IR043 IR048 IR026", "IRD23", "native-order", risk="critical"),
    lemma("IR068", "P", "Finite accuracy removes vanishing assumptions", "With S=1+7r*r!*12^r*2^(21r), derive 1/K<=U+S*J*|c-z| in rational-sequence form. Compile the finite polynomial substitution errors and Taylor errors to total <=1/(4K); include selected-jet error and all 7r unselected jets.", "IR048 IR060 IR067 IR058 IR049 IR012 IR075 IR076 IR078", "IRD23 IRD24", "native-order", risk="critical"),
    lemma("IR069", "P", "Excluded neighborhood with rational slack", "Set epsilon=1/(4*K*S*J), all factors positive. A hypothetical |c-z|<=epsilon yields upper bound<=1/(2K), plus at most1/(4K) finite-evaluation error, contradicting the lower bound1/K. Establish the required rational implications, not a general real-order decision principle.", "IR064 IR068 IR049 IR003 IR006", "IRD24", "native-order", risk="critical"),
    lemma("IR070", "P", "Decidable precision-to-certificate bridge", "Construct t with 2^t>=12*K*S*J. Failure of the decidable test |b*u_t-a|>2*b*2^-t implies |c-z|<=3*2^-t<=epsilon, contradicting IR069. Decidability of this single finite rational test yields the certificate in HA; no Markov rule is used.", "IR069 IR026 IR006 IR004 IR003", "IRD10 IRD24", "native-order", risk="critical"),
    lemma("IR071", "P", "Irrationality certificate soundness", "IrrCert implies |b*c-a|>b*2^-n>0 using IR026. This is a semantic explanation backed by rational-sequence inequalities, not a kernel real-number predicate.", "IR026 IR004", "IRD10", "native-order"),
    lemma("IR072", "P", "Full positive HA irrationality", "forall ap am b. b>0 -> exists n up um ud e trace. IrrCert(ap,am,b,n,up,um,ud,e,trace). Split rational competitors inside/outside [1,2]; no classical rule, oracle, missing premise or degree/height restriction.", "IR066 IR070 IR071 IR025", "IRD10", "native-search", risk="critical"),
    lemma("IR073", "P", "Certificate-search totality", "For every signed a and b>0, sequential exact evaluation of CApprox followed by the decidable certificate test halts. Termination follows from IR072; practical complexity is a separate question.", "IR072 IR003 IR025", "IRD10", "native-induction", "bounded search up to the witnessed precision"),
    lemma("IR074", "P", "Representation-invariant endpoint", "Equivalent signed numerator pairs and rational representations yield the same irrationality conclusion; positive rescaling of a,b is supported without identifying raw trace codes.", "IR072 IR001 IR002", "IRD10", "native-ring"),

    lemma("IR075", "Q", "Quadratic polynomial remainder certificate", "For every finite signed/rational polynomial P, construct U,V,Q with P(X)=U+V*X+(X²-2)*Q(X). Emit an identity certificate; substitution at approximate sqrt2 has an explicit residual (x²-2)*Q(x).", "IR005 IR029 IR009", "IRD11", "native-induction", "polynomial degree", "high"),
    lemma("IR076", "A", "Finite multivariate substitution error", "For P=sum_alpha c_alpha*X^alpha, coordinate magnitudes<=R with R>=1 and coordinate differences<=delta imply |P(x)-P(y)|<=delta*sum_alpha |c_alpha|*|alpha|*R^(|alpha|-1), omitting degree-zero terms. Compute the bound from the coefficient table.", "IR009 IR005 IR004", method="native-induction", induction="monomial length and finite coefficient list", risk="critical"),
    lemma("IR077", "H", "Finite Taylor derivative identity", "For d>=k, (d/dt)^k E_d(lambda*t)=lambda^k E_(d-k)(lambda*t); for d<k the formal derivative is zero. Derivative means the finite coefficient-list operation.", "IR019 IR005 IR011", "IRD08", "native-induction", "k and polynomial degree"),
    lemma("IR078", "H", "Denominator-cleared confluent identity", "For M=7r, C_jk=L0^(-(M-k))*c_jk with rational denominator dividing720^M. Therefore M!*(720*L0)^M times the IR056 identity is polynomial; include the Taylor degree factorial to clear Taylor coefficients. Record every nonzero denominator and its lower bound.", "IR055 IR056 IR018 IR005", "IRD21 IRD22", "native-induction", "truncated inverse-product coefficients", "critical"),
    lemma("IR079", "S", "Formal atanh/exponential coefficient recurrence", "Let A(z)=2*sum(j>=0,z^(2j+1)/(2j+1)) as finite coefficient tables. Formal exp(A) has F(0)=1 and (1-z²)F'=2F coefficientwise to each finite degree; composition only uses finitely many positive-degree terms.", "IR005 IR019 IR021 IR077", "IRD07 IRD08", "native-induction", "coefficient degree", "critical"),
    lemma("IR080", "S", "Formal recurrence identifies rational series", "The recurrence of IR079 uniquely determines coefficients and agrees with (1+z)/(1-z)=1+2*sum(j>=1,z^j). Prove by induction on the coefficient index, with positive integer division justified.", "IR079 IR003 IR005", "IRD07 IRD08", "native-induction", "coefficient index", "high"),
    lemma("IR081", "S", "Composition-tail bound at one third", "For z=1/3, construct finite truncation degrees making the difference between exp(A(z)), the finite formal composition and the rational-series truncation smaller than any dyadic error. Bound the outer exponential tail, inner atanh tail and positive omitted coefficient mass separately.", "IR080 IR017 IR020 IR010 IR023 IR012", "IRD07 IRD08", "native-induction", "explicit tail schedules", "critical"),

    lemma("TR001", "T", "Integer polynomial evaluation stability", "For P over Z, x,y in [1,2], |P(x)-P(y)|<=M_P*|x-y|, where M_P=1+sum(j>=1,j*abs(a_j)*2^(j-1)); zero/trailing-zero encodings handled.", "IR009 IR005 IR026", "IRD25 IRD26", "native-induction", "degree", phase=2),
    lemma("TR002", "T", "Coded algebraic extension presentations", "Under P(c)=0, construct the finite arithmetic data needed for Q(sqrt2,c), including a valid basis, multiplication and equality procedure; degree bounds derive from P, not an algebraicity oracle.", "IR029 IR044 TR001", "IRD25", "native-induction", "finite algebraic construction", "critical", 2),
    lemma("TR003", "T", "General denominator and norm separation", "Prove explicit nonzero algebraic lower bounds using finite determinants/resultants and conjugate/root bounds from a coded presentation. Replace the special quadratic norm without importing classical analysis.", "TR002 IR044 IR035", "IRD25", "native-induction", "field degree", "critical", 2),
    lemma("TR004", "T", "Variable-node auxiliary estimate", "Generalize the fixed seven-node proof to m=2h+3, N=q², n=N/(2hm), with uniform finite interpolation and height estimates.", "TR003 IR043 IR047 IR054 IR060 IR064", method="native-induction", induction="m and h", risk="critical", phase=2),
    lemma("TR005", "T", "Polynomial nonvanishing bridge", "Produce positive polynomial certificates, by a reviewed quantitative approximate-root construction or an implemented checked PA-to-HA transformation. Neither route is assumed available.", "TR001 TR002 TR003 TR004 IR072", "IRD26", "native-induction", "explicit certificate construction", "critical", 2),
    lemma("TR006", "T", "Full positive transcendence", "forall integer polynomial codes P. Nonzero(P) -> exists n,w. TransCert(P,n,w). Establish the fixed constant interpretation by IR027; no bounded-degree substitute.", "TR005 IR027", "IRD26", "native-search", risk="critical", phase=2),
]

ENGINEERING = [
    lemma("ENG001", "E", "Contract and definition elaboration gate", "For every dispatched lemma freeze exact hypotheses, binder order, arities and expanded HA AST hash. Proposed IRD names acquire reviewed existing/new definition identities only after hygienic expansion-equivalence tests. Reject circular definitions and a definition containing its desired theorem.", method="structural-check", risk="critical"),
    lemma("ENG002", "E", "Existing-premise audit", "Map each reused result to the exact checked Alpha/Stable statement, dependency closure and first-admission evidence. Similar names, an ordinary Lean demo and source-only candidates do not discharge any IR obligation.", "ENG001", method="structural-check", risk="critical"),
    lemma("ENG003", "E", "Model-free native baseline", "Run bounded native ring/compact_arith/norm_num/search pilots; record original goal, exact premise allowlist, deterministic strategy, certificate size and fresh HA replay. No external proof or model calls are silently accepted.", "ENG001 ENG002", method="native-ring"),
    lemma("ENG004", "E", "Guarded SMT/TPTP export", "Export only whitelisted elaborated obligations with natural-domain guards, exact integer/rational encoding, original target hash and checked-premise hashes. No real pow/log oracle, unproved induction schema or lossy denominator transformation.", "ENG001 ENG002", method="structural-check", risk="critical"),
    lemma("ENG005", "E", "External hint reconstruction", "Initially consume solver substitutions/rewrite hints through native proof generation. A success requires reconstruction of the original HA formula and fresh native checking. Unknown inference, clausification, Skolemization or arithmetic rule fails closed.", "ENG003 ENG004", method="certificate-reconstruction", risk="critical"),
    lemma("ENG006", "E", "Hostile replay and independent Lean", "Reject altered premises/targets, missing natural guards, swapped variables, forged unsat, unsupported proof steps, DNE, truncated logs and stale caches; independently check identical accepted native bundle bytes in Lean.", "ENG005", method="structural-check", risk="critical"),
    lemma("ENG007", "E", "Bounded scheduler and accounting", "Wrap each native/solver worker in run_bounded with CPU,wall,RSS and output limits; hard total tranche deadline; no solver-internal process portfolios; checkpoint exact inputs, unknowns, solver hits, reconstructed proofs, genuine LLM tokens and fresh HA accepts separately.", "ENG003", method="structural-check", risk="high"),
    lemma("ENG008", "E", "Final irrationality closure and presentation", "IR072-74 are accepted in empty context by ordinary HA and independent Lean; every dependency is authenticated, definitions expanded, full quantified endpoint retained. Only then replace planning pages with canonical exact/defined proof explorers and seek Alpha promotion/deployment.", "IR072 IR073 IR074 ENG006 ENG007", method="structural-check", risk="critical"),
    lemma("ENG009", "E", "Fallback proof-translation pilot (not primary route)", "If direct perturbation fails its bounded pilot, separately implement negative translation plus Friedman A-translation on a tiny supported arithmetic proof calculus. Test induction, binders and eigenvariables; emit ordinary HA certificates. No Markov axiom or automatic arbitrary Lean import.", "ENG001 ENG003", method="certificate-reconstruction", risk="critical"),
]
for _row in ENGINEERING:
    _row["kind"] = "engineering"
    if _row["id"] == "ENG009":
        _row["phase"] = 0  # contingency, excluded from the primary proof cone

METHODS = {
    "native-ring": "Existing proof-producing ring/compact arithmetic; exact CAS only suggests identities.",
    "native-order": "Native arithmetic reconstruction first; Z3 QF_LIA suggests coefficients, cases or substitutions. Nonlinear obligations must be decomposed or certified separately.",
    "native-numeral": "Exact integers/Fraction computation plus proof-producing normalization; floats are not evidence.",
    "native-induction": "Agent fixes the induction invariant once; deterministic generators build base/step proof obligations and native proof terms.",
    "native-search": "Bounded HA logical search and checked-premise retrieval; E/Vampire may suggest instantiations after export/reconstruction gates.",
    "structural-check": "Deterministic schema, graph, provenance and mutation tests; not a mathematical proof.",
    "certificate-reconstruction": "New fail-closed adapter work, not presently implemented or trusted.",
}

SOURCES = [
    dict(id="SRC1", title="Friedman: Gelfond-Schneider and the conditional PA-to-HA route (2000)", url="https://fomarchive.ugent.be/2000-June/004116.html"),
    dict(id="SRC2", title="Selinger: Friedman's A-translation (1992)", url="https://www.mathstat.dal.ca/~selinger/papers/friedman.pdf"),
    dict(id="SRC3", title="Karatarakis and Wiedijk: Lean Gelfond-Schneider formalization (2026)", url="https://arxiv.org/html/2603.24823v1"),
    dict(id="SRC4", title="Z3: proof logs and incomplete big-step hints", url="https://microsoft.github.io/z3guide/programming/Proof%20Logs/"),
    dict(id="SRC5", title="E: proof objects and checker limitations", url="https://github.com/eprover/eprover"),
    dict(id="SRC6", title="Vampire: supported TPTP proof output", url="https://github.com/vprover/vampire/releases"),
]


def pilot(identifier, parent, contract, method, mutation):
    return dict(id=identifier, parent=parent, contract=contract, method=method,
                required_negative_test=mutation,
                status="blocked_on_contract_and_premise_elaboration",
                statement_ast_sha256=None, closes_parent=False)


# These are representative child contracts, not twelve already elaborated
# formulas, and not a replacement for their universal parent obligations.
PILOT = [
    pilot("P01", "IR002", "Addition respects RatEq for two pairs of positive-denominator triples: clear denominators and emit the cross-multiplied polynomial identity.",
          "native-ring", "Drop one positive-denominator guard or swap a numerator sign."),
    pilot("P02", "IR031", "For four arbitrary signed integers A,B,C,D, (AC+2BD)^2-2(AD+BC)^2=(A^2-2B^2)(C^2-2D^2), encoded as a subtraction-free natural equality.",
          "native-ring", "Replace the coefficient 2 in the quadratic product by 3."),
    pilot("P03", "IR009", "Power-difference induction STEP only: from witnessed e-th powers and their telescoping-sum identity derive the (e+1)-st identity using the sum recurrence. Freeze the exact induction hypothesis as a premise.",
          "native-ring", "Omit the induction hypothesis or shift the final summand exponent."),
    pilot("P04", "IR079", "Constant-coefficient BASE of formal exp(A): for the fixed positive-degree inner series with A_0=0, the coefficient of degree zero of the finite composition is 1.",
          "native-numeral", "Allow a nonzero constant term in the inner series."),
    pilot("P05", "IR080", "Recurrence STEP for k>=2 after f_k=f_(k-1)=2: justify the candidate f_(k+1)=2 in (k+1)f_(k+1)=2f_k+(k-1)f_(k-1). The k=0,1 boundaries stay separate parent obligations.",
          "native-ring", "Use k instead of k+1 on the left-hand coefficient."),
    pilot("P06", "IR020", "Single tail-contraction step: for x>=0, j>=0, j+1>=2x and t=x^j/j!>=0, the successor term x*t/(j+1)<=t/2. Clear strictly positive denominators and keep the product-order lemma explicit.",
          "native-order", "Omit j+1>=2x and require a counterexample to be detected."),
    pilot("P07", "IR045", "Two-frequency moment INSTANCE: M0=b0+b1, M1=b0*l0+b1*l1 imply M1+b0*l1=l1*M0+b0*l0. Signed values use coefficient-pair encoding; arbitrary N is not inferred.",
          "native-ring", "Exchange b0 and b1 only on one side of the identity."),
    pilot("P08", "IR055", "First reciprocal-coefficient step for the fixed factor (d+w)^(-m), m>=1,d!=0: c0=d^(-m), c1=-m*d^(-m-1), so d*c1+m*c0=0. Powers and inverse witnesses are explicit.",
          "native-ring", "Change the sign of c1 or remove the nonzero-denominator premise."),
    pilot("P09", "IR056", "Finite confluent INSTANCE r=1, ell*=3, x_j=j*L0 (j<7), 1/4<=L0<=1/2: the degree-7 monomial functional equals 1. Generate its exact reciprocal coefficients, clear 7!*(720L0)^7 and replay the resulting identity; no universal r claim.",
          "native-ring", "Give the selected node multiplicity 1 instead of 2."),
    pilot("P10", "IR064", "Closed constant inequality 2^55*3^11*7^5<=2^88. Compute exact integers and generate a double-and-add arithmetic certificate, not a floating-point comparison.",
          "native-numeral", "Lower the right exponent to 85; the resulting inequality is false."),
    pilot("P11", "IR069", "Precision-bridge arithmetic: K,S,J>0 and e>=12KSJ imply 3/e<=1/(4KSJ). Introduce an explicit product witness V=KSJ, prove its positivity, clear denominators, then isolate the linear leaf e>=12V.",
          "native-order", "Replace 12 by 8 and demand rejection or a rational counterexample."),
    pilot("P12", "IR071", "Fixed rational certificate INSTANCE a=3,b=2,n=6: generate the specified CApprox trace and prove |2*u_6-3|>4*2^(-6) in the unchanged kernel. This instance does not prove accuracy or universal irrationality.",
          "native-numeral", "Mutate one approximation trace entry while retaining the claimed result."),
]


def campaign_plan():
    from copy import deepcopy
    return dict(
        schema=SCHEMA, slug=SLUG, title=TITLE, date=DATE,
        authority="planning_only", active_target="IR072", next_target="TR006",
        grand_campaign=dict(family="F13", domain="D06", goals=["G121", "G122"],
                            parent=PARENT, existing_goal_count=120),
        verified_new_theorem_count=0, admitted_new_definition_count=0,
        execution_priority=["irrationality", "transcendence"],
        groups=GROUPS, methods=METHODS,
        nodes=deepcopy(DEFINITIONS + LEMMAS + ENGINEERING), sources=SOURCES,
        pilot=deepcopy(PILOT),
        pilot_policy=dict(
            count_as="child-leaf checks only, never universal parent closure",
            elaboration_gates=["ENG001", "ENG002"],
            paired_runs="Identical frozen formulas: native-only, then native plus guarded solver hints; both runs share the per-leaf budget.",
            repair_budget="One changed-strategy repair, within the original reservation; no unchanged retry.",
            external_inference_acceptance="Only fresh reconstruction of the original HA target counts; unavailable tools are recorded, not installed implicitly."),
        budget=dict(status="proposed_defaults_not_a_spend_authorization",
                    smoke_total_wall_seconds=30, portfolio_cpu_seconds_per_lemma=60,
                    portfolio_wall_seconds_per_lemma=90, worker_rss_mib=768,
                    worker_output_mib=8, max_local_workers=1,
                    retry_limit_without_contract_change=0,
                    repair_attempt_limit_with_strategy_change=1,
                    pilot_lemma_limit=12, pilot_total_wall_seconds=1200,
                    model_proof_search_calls=0,
                    llm_use="planning, contract review, one bounded repair after deterministic failure; log actual tokens",
                    stop="No bulk launch before contract/reconstruction gates; no overnight run, cloud spend or installation implicit."),
        acceptance=dict(primary_route="direct_finite_perturbation",
                        fallback="ENG009 is a separate gated contingency, not an assumption",
                        original_ha_required=True, independent_lean_required=True,
                        classical_kernel_allowed=False, external_unsat_is_proof=False,
                        finite_examples_close_universal_target=False),
    )
