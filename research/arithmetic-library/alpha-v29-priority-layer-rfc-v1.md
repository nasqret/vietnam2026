# Alpha v29: four complete constructive priority campaigns

Date: 2026-08-27. This additive release closes the exact goals G072, G006,
G010 and G036. Its self-contained proof artifact has passed the original
intuitionistic HA kernel and the independently compiled Lean verifier.
Publication, deployment and Stable promotion are separate operations.
Gaussian factorization G082 is not part of this frozen release and must not
be appended to its factories, specifications or proof artifact.

## Immutable parent and exact addition

The parent is the unchanged Alpha-v28 edition: 2,764 checked-use theorems,
8,984 direct theorem edges and 53 dependency layers. Every inherited
`EditionEntry` is reused by object identity. Stable remains the identical,
separate default edition of 432 theorems.

```text
parent catalogue:
897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9
parent edition identity:
4936d155e8d2a39409a4e83beb4ac5cb2481948d8b6eeecf1c7571161786646b
parent ordered enrollment:
75c80dffb8899dbf6f97a561322e630679d9df58416309e5c439746e96466fce
exact complete parent specifications:
e80e011ab3dc4b19d9a11ce09033418c3157be91b7c905dc59db581a5bbcdc11
```

The eleven frozen factories are ordered as follows. The shared prime
valuation support is independent of each final campaign and precedes all
consumers; no cyclic import or assumed support witness is introduced.

| Admission campaign | Ordered modules, omitting `_candidate` | New theorems | New edges |
| --- | --- | ---: | ---: |
| `prime_valuation_support` | `prime_valuation_support` | 20 | 81 |
| `continued_fraction_approximation` | `continued_fraction_approximation`, `continued_fraction_convergents` | 83 | 247 |
| `euler_totient` | `euler_totient_count`, `euler_totient_interval`, `euler_totient_prime_step`, `euler_totient_algebra`, `euler_totient_product` | 84 | 266 |
| `squarefree_perfect_power` | `squarefree_decomposition`, `perfect_power_profile` | 53 | 148 |
| `odd_prime_lte` | `odd_prime_lte` | 38 | 189 |
| Total | | 278 | 931 |

Alpha v29 therefore has exactly **3,042 checked-use theorems**, 9,915 direct
theorem edges and 53 layers. Its 2,610 non-Stable entries remain Alpha-only.

```text
new-name order:
cf4615b863bb1640151bde7dffd8dd904dc47cb9589c2cc4ec90485c82c4f509
all new specification fields, including scripts and summaries:
99c0f9b3ad573043717d68714e9121475d62a9dd36974d0739352b15c6652a90
ordered factory metadata:
585e82858bec74d758be931e49e7509e5652ba2d7773c5d5ff84e0161633fe03
v29 edition identity:
57da70c3718579cb8eb81c59a4c2898a5071140fa944e31bca312fe53432574c
v29 ordered enrollment:
feac02afbfe516116accd30a6a117060f5d5cd99d608971a7f62bd1f3787104d
```

## Exact mathematics and boundaries

G072 proves the second-kind best-approximation inequality for every actual
Euclidean continued-fraction convergent: if `0<t<v`, then
`|a*v-b*u| <= |a*t-b*r|`. Both the exact natural-numerator endpoint and an
explicit arbitrary signed-pair numerator extension are proved. Convergents
are genuine finite matrix computations, not approximation assertions
hidden in a definition. Every valid history index has a unique numerator
and denominator; adjacent determinants, coprimality, the terminal value,
and the legitimate initial zero numerator are separately proved. The
planning-only positive-numerator restriction was corrected additively;
for a proper fraction, `0/1` is an actual initial convergent. Neither
infinite irrational expansions nor the false non-strict denominator
variant are silently claimed.

G006 starts from the actual beta-coded count of residues `0<=r<n` coprime
to positive `n`. It proves unique existence, prime powers,
multiplicativity, and Euler's full distinct-prime product formula using
constructed exact valuation support and an actual product trace. The
definition of totient is not the Euler product. The unit has value one;
zero lies outside the positive-domain graph.

G010 constructs distinct prime support with positive exact valuations,
actual prime-power values, complete prime-divisor coverage, and their
product equal to positive `n`. It constructs the unique decomposition
`n=r*s*s` with squarefree `r`. Squarefreeness is the ordinary absence of
prime-square divisors, not a decomposition premise. Its coded nonunit
power profile contains the actual finite exponent gcd and a beta table
of roots. A separately proved equivalence identifies all positive perfect
power degrees with divisors of that actual gcd. Every permitted degree
has an actual root, constructed before tabulation. For `n=1`, an explicit
uniform theorem covers every positive degree; the empty support is not
assigned a fictitious positive gcd. Zero remains outside the target.

G036 proves the full odd-prime lifting-of-the-exponent statement under its
exact guards: prime `p>2`, `x>y>0`, positive exponent `n`, `p|(x-y)` and
`p` not dividing `x*y`. It constructs both power values and their positive
difference, with valuation `v_p(x-y)+v_p(n)`. The companion value theorem
covers every supplied pair of actual power values and difference balance.
There is no assumed output valuation, geometric sum, binomial expansion
or prime-power exponent decomposition. The binary-prime extension is a
different theorem and is not claimed here.

The individual mathematical RFCs retain their original candidate
status as historical development records. The later complete closure and
admission evidence is recorded separately in the v29 receipt; those frozen
records are not rewritten after successful integration.

## Complete proof closure and conservative authority

`campaign_priority_layer_closure.py` reconstructs the actual dependency
cone: 278 new and 287 inherited theorem bodies. A balanced conjunction
packages all 29 maximal endpoints, producing 566 bundle nodes, 1,690
edges and 38,443 structural body-node occurrences. The packaging node is
not counted as a new library theorem.

The only release artifact is
`artifacts/alpha-v29-priority-layer-proof-bundle-v1.json` relative to this
RFC's directory. Its 4,200,971 bytes have SHA-256
`4fcb3cd45e83448776abb9e33692496a7acfa98a051cae15761826a0b15fda44`.
All 566 ordinary bodies, including the packaging node, pass both verifiers.

Parent catalogues and all 18 historical proof-provider byte bindings are
integrity checks and source locators, never proof authority. A reused
body must have the exact requested target and every ordered prerequisite
target. Explicit candidate seeds are completely kernel-checked before
reuse, including nodes irrelevant to the requested branch. The final
combined graph is checked again. Missing bodies are reconstructed from
ordinary scripts. None of this trusts an earlier receipt or a matching
digest as a mathematical proof.

Reconstruction uses one-row microbatches under the existing maximums of
16 rows, 125,000 proof occurrences and 25,000 distinct proof objects.
Identity counts and occurrence counts are measured separately. Original
kernel, formula, body, graph, certificate-sharing and payload bounds are
unchanged. No axiom, classical rule, trusted tactic, checker shortcut,
resource-cap increase or private source modification is introduced.

The candidate exporter never overwrites existing files and does not enroll
anything. The separately sealed `priority_layer_bundle()` provider returns
the freshly checked bundle and receipt. The edition wrapper returns these
plus exact theorem positions. Its checked-use path authenticates the
immutable parent specifications, the artifact bytes, every exact statement
and ordered edge, and all actual proof bodies. It materializes a requested
ordinary empty-context certificate under the unchanged sharing limits and
checks that certificate with the original kernel. Inherited replay delegates
to v28; new theorems cannot be requested with Stable authority.

The compact browser path accepts the exact parent specification tuple and
mounted artifact, without reading a repository catalogue or historical
artifact files. This does not relax proof checks. Missing, altered, unsealed,
malformed or non-path proof inputs fail closed.

## Independent Lean provenance and publication

Local artifact verification uses the existing compiled bundle verifier.
Its binary hash and build traces identify Lean **4.28.0**, as documented
in the receipt. The companion checkout now requests Lean 4.31.0; that
toolchain was not available locally during these artifact checks. A remote
4.31.0 source build is a separate compatibility observation and is not
presented as verification of these new artifacts. No toolchain installation
or private repository write is performed by this closure workflow.

The verifier checks the complete HA proof encoding in Lean. This is not
a claim that an explanatory paragraph, hash or JSON receipt is a native
Lean theorem. Actual proof data remain the authority in both checkers.

Definition registries and current-publication adapters are separate
additive controls. Historical v28 definition objects, source evidence,
catalogues, proof artifacts and publication fixtures remain unchanged.
The canonical Quadratic Reciprocity design, conservative AST-equivalent
notation, separate theorem/definition/use edges, and honest first-admission
labels remain required. This RFC neither activates a live runtime nor
asserts a remote deployment or Stable promotion.
