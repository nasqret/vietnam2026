# Irrationality first, transcendence next: the non-LLM-first HA campaign

Planning date: 2026-09-19. Active mathematical target: **IR072 / G121**.
Next target: **TR006 / G122**, deferred until the first target is closed.

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
the quotient error <=2*2^-k, the exponential Lipschitz bound 3 on [0,1], and
`|u_n-c|<=7*2^-k<2^-n` with `1<=u_n<=2`.

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
