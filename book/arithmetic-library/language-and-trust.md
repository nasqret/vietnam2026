# Language, notation, and trust

Peano Lab intentionally has a small object language. Natural-number terms are
built from

$$
0,\qquad S(n),\qquad n+m,\qquad n\cdot m,
$$

and formulas use equality, first-order connectives, and quantifiers. The
surface notation $n\le m$ is already conservative sugar for an existential
equality. There is no trusted remainder operation, primality oracle, power
function, list, multiset, or theorem database.

This is a useful constraint. It forces every library abstraction to answer a
precise question: is it merely readable notation that expands to the old
language, or is it genuinely new expressive power?

## Conservative definitions

Divisibility needs no kernel change. We read

$$
a\mid b \quad:\!\Longleftrightarrow\quad \exists q.\ b=a\cdot q.
$$

The current library stores the right-hand formula literally. For example,
`multiple_trans` says that witnesses for $a\mid n$ and $b\mid a$ compose to a
witness for $b\mid n$.

A subtraction-free definition of modular congruence over naturals is

$$
a\equiv b\pmod m
\quad:\!\Longleftrightarrow\quad
\exists u\,v.\ a+m\cdot u=b+m\cdot v.
$$

Unlike the asymmetric claim that one number is the other plus a multiple,
this formula is symmetric even when $a<b$. It is also meaningful at modulus
zero: then it reduces to equality. The definition-aware Proof Explorer now
uses `ModEq(m,a,b)` as conservative display notation for this formula, while
native replay still expands it before checking, exactly as `<=` expands
today.

Primality can also be expanded:

$$
\operatorname{Prime}(p) \quad:\!\Longleftrightarrow\quad
p\ne1\;\land\;
\forall a\,b.\bigl(p=a\cdot b\to(a=1\lor b=1)\bigr).
$$

This factor-pair form is the catalog's current convention; it is equivalent to
the familiar assertion that every divisor is either one or the number itself.
Over the naturals it also rules out zero, since zero has nontrivial factors.
The catalog records completely expanded Peano targets rather than asking the
checker to trust `Prime` as a new atom. In particular, the checked theorem
`prime_two` is stored as

```text
~(2 = 1) /\ forall a b. 2 = a * b -> a = 1 \/ b = 1
```

and introduces no primitive predicate.

The same expansion is now used by general checked theorems:
`prime_or_composite` constructs either the expanded prime formula or an
explicit nontrivial factor pair, `prime_decidable` returns that formula or its
negation for every natural, and `prime_divisor_exists` constructs an expanded
prime together with a divisibility witness for every nonzero nonunit natural.
Their bounded search and descent certificates contain no DNE node; decidability
is proved rather than imported from the host language.

### The definition-aware reading edition

The {doc}`definition-aware proof explorer <defined-proof-explorer>` provides a
40-entry registry over the exact 557-specification quadratic-reciprocity
closure. Thirty-eight definitions occur; `AllPrime` and `Sorted` have zero
whole-schema matches. The edition compacts 506 theorem statements and 1,275
of 1,839 proposition-bearing local commands. Aggregate statement text falls
from 2,457,096 to 107,386 characters (95.63%); local proposition text falls
from 1,971,403 to 111,519 (94.34%). Every changed formula links to its expansion
and an exact native replay line, and the generator checks equality of the
parsed PA abstract syntax trees.

This is a reading layer, not a language extension. The compiler, registry,
`PD` identifiers, hashes, pages, and notation edges are untrusted and cannot
participate in a theorem dependency path. The current QR slice contains 241
Stable rows and 316 Alpha-only rows. The historical campaign-local source
labels remain separate from current immutable Alpha-v20 evidence: all 316
Alpha-only QR rows, including the `PA00FW` root, are now `alpha_closed`
because their complete actual proofs were independently checked in historical
v16. Historical v17 independently closed the supplementary laws; historical
v18 adds complete Lucas, Kummer, Bertrand, four-square, and two-square proof
bundles. Historical v19 additionally closes all remaining historical
obligations and appends four wholly checked constructive theorem families;
current v20 independently adds four further beta-coded polynomial, finite
matrix-component, Bertrand-prime, and continued-fraction campaigns. Compact
notation itself grants neither theorem evidence nor Stable promotion. These
figures describe the focused QR slice, not the complete current 1,776-row
Alpha v20 catalog, every entry of which has checked-use authority; its Stable subset
remains exactly 432 theorems.

## Relational definitions before functions

The current term grammar cannot add a gcd function without changing the
language. It can state a graph relation instead:

$$
\begin{aligned}
\operatorname{IsGCD}(g,a,b) :\!\Longleftrightarrow {} &
g\mid a\land g\mid b\\
&{}\land\forall d.\bigl(d\mid a\land d\mid b\to d\mid g\bigr).
\end{aligned}
$$

Existence and uniqueness of such a $g$ are ordinary first-order claims. A
subtraction-free Bézout statement can represent signed coefficients by
positive and negative parts:

$$
a x_+ + b y_+ = g + a x_- + b y_-.
$$

This is less convenient than integer notation, but it remains honest about
the underlying language. A conventional integer-coefficient Bézout statement
is not representable with these natural-only terms; the four-natural balanced
relation is a separately named, checked native theorem, not hidden integer
syntax.

## Proof sharing is not a new arithmetic language

The object language and the proof-certificate language are different layers.
Peano Lab now has a reviewed certificate node

```text
Cut(A, B, lemma, body)
```

with the rule

$$
\frac{\Gamma\vdash\mathit{lemma}:A\qquad
      A,\Gamma\vdash\mathit{body}:B}
     {\Gamma\vdash\operatorname{Cut}(A,B,\mathit{lemma},\mathit{body}):B}.
$$

The checker verifies the embedded lemma once, then checks the body with its
formula as the newest hypothesis. This enlarges the trusted checker and must
be audited as such. It does not add a natural-number operation, predicate,
axiom, theorem constant, or classical principle. In particular, it cannot
make gcd, primality, β decoding, or factorization expressible unless the
corresponding first-order formula was already expressible.

The node is self-contained: it stores both formulas and both proof branches.
It stores no theorem name, content hash, declaration key, or external lookup.
Names and hashes remain useful provenance data, but the checker never accepts
them as evidence. See {doc}`Self-contained proof sharing <proof-sharing>` for
the full trust and erasure contract.

The separate
[`peano-lab-lean`](https://github.com/nasqret/peano-lab-lean) project models
this rule and the rest of the certificate calculus in Lean. Its semantic
theorem proves accepted derivations true in standard natural numbers, relative
to Lean's kernel and reported standard axioms. Historical WMI job `211445`
seals cut-free v1. Cut-aware version-two source
[`ab966fd1`](https://github.com/nasqret/peano-lab-lean/commit/ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2)
passed pinned Lean 4.31/WMI job
[`218358`](https://github.com/nasqret/peano-lab-lean/tree/8515336ab3b89ca6f0c8ab521d01745a220b5211/artifacts/wmi/218358).
This metaverification does not move readable predicates into either kernel.

## How conservative expansion reaches factorization

The Fundamental Theorem of Arithmetic quantifies over an arbitrary finite
collection of primes and compares factorizations up to permutation or
multiplicity. Today's Peano surface has no primitive finite-sequence,
multiset, finite-map, generic power, or recursive factorization relation.

The representation review selected a Gödel-β encoding because it elaborates
entirely to existing PA formulas and therefore needs no further object-language
or kernel rule. A factor sequence uses natural codes `(b,c,l)`; a second code stores
prefix products; bounded formulas express decoded values, primality, and
sortedness. This is intentionally an untrusted authoring facade rather than a
new kernel atom.

The expanded single-position relation now has checked totality and
functionality through `beta_at_exists`, `beta_at_unique`, and
`beta_at_exists_unique`; `beta_modulus_nonzero` and
`beta_at_self_of_bound` supply its first boundary helpers, and
`beta_at_to_mod_eq` projects the decoded quotient-remainder witness into the
checked balanced-congruence API. `mod_eq_bounded_unique` and
`mod_eq_to_remainder_decomposition` justify the reverse direction, which
`beta_at_of_mod_eq_bound` specializes back to the β modulus. Consequently,
`At` is now checked equivalent to its bound plus balanced congruence. These
theorem names do not add a predicate symbol. Constructive `binary_crt` now
combines any two bounded residues for nonzero coprime moduli, and
`binary_crt_beta_pair` turns that result into two expanded `At` facts. The
latter keeps coprimality of the two β moduli as an explicit premise.
`beta_modulus_coprime_base` proves each modulus coprime to $c$, while
`common_divisor_beta_moduli_divides_gap_times_c` and Gauss cancellation yield
the checked conditional theorem

$$
j=i+g\;\land\;g\mid c
\quad\Longrightarrow\quad
\operatorname{Coprime}(M(c,i),M(c,j)).
$$

The condition matters. Unconditional pairwise coprimality is false: for
$c=1$, $M(1,1)=3$ and $M(1,4)=6$. The checked
`binary_crt_beta_pair_of_gap_dvd` applies precisely the conditional theorem.
`bounded_common_multiple_exists` separately constructs a nonzero $c$
divisible by every positive natural at most a supplied bound. The checked
bounded-prefix bridge now turns that invariant into pairwise coprimality for
all distinct bounded positions. Product coprimality, modulus descent, and
`binary_crt_fold_step` also check the algebraic preservation step. The new
product and congruence successor lemmas combine in
`beta_crt_prefix_invariant_step`, and
`bounded_beta_crt_prefix_invariant` uses ordinary induction to carry four
facts through every bounded prefix: the accumulated product is nonzero; every
earlier beta modulus divides it; the constructed value is congruent to each
earlier value already decoded from the supplied code $b$; and the product is
coprime to every future bounded beta modulus.

The theorem `bounded_beta_crt_for_existing_code` projects only the third part
at the full bound. It is extensionally trivial—choosing $z=b$ already gives
the advertised congruences—because the residues in its premise are decoded
from $b$. It is therefore not an arbitrary finite-sequence recoding or
extension theorem. The later checked exclusive-prefix invariant and
`beta_prefix_extend` cross that separate gate. Exact β-coded prefix-product
trace existence and functionality then supply a relational Product API;
greatest-prime-divisor descent and canonical append prove existence, while
Euclid, sorted last-factor matching, and cancellation prove extensional
uniqueness.

The now-checked native route is:

1. add untrusted named-predicate expansion for the formulas already
   expressible;
2. reuse the checked division, relational gcd, balanced Bézout, Gauss, and
   Euclid spine together with the now-checked proper-factor search and
   prime-divisor-existence clients;
3. prove greatest-prime descent for the selected sorted factorization route;
4. reuse the checked equivalence between single-position β decoding and
   bounded congruence together with checked binary CRT, conditional
   bounded-prefix pairwise coprimality, product coprimality, modulus descent,
   the generic CRT fold step, and the now-checked bounded prefix invariant;
   prove independent finite-prefix recoding and extension, exact beta-coded
   prefix-product traces and bounds, and their factorization relations;
5. check factorization existence, extensional uniqueness, and their exact
   combined FTA statement.

A separate Lean companion checks the conventional finite-list FTA, including
uniqueness up to permutation and an exact axiom audit. It grants no Peano
authority. Steps 3–5 now have closed native PA certificates at this integration
checkpoint. Existence checks at 43,973 nodes/depth 98; uniqueness at
29,789/depth 82; their exact conjunction checks at 73,767 nodes/depth 99 with
2,184 self-contained Cuts. The combined certificate SHA-256 is
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It passes empty-context and full live-use checking under the
500,000-occurrence/100,000-object/depth-256 cap, uses only PA1–PA6 and
induction, and contains no
DNE. Runtime integration is complete.

The theorem remains conservative in a precise sense: it adds no primitive
list, multiset, Product function, Prime predicate, or factorization atom.
Because β encodings are non-unique, its uniqueness clause compares lengths and
decoded entries instead of raw codes. The independently checked
`prime_unbounded` endpoint is not required for FTA.

## The trust path

For a checked entry the path is always

$$
\text{statement + dependencies + script}
\longrightarrow \text{replayed proof}
\longrightarrow \text{self-contained Cut packaging}
\longrightarrow \operatorname{check}(\varnothing,p,T).
$$

Notation expansion, tactic execution, catalog generation, dependency graphs,
and hash generation are all untrusted. Any of them may cause a true proof to
be rejected or an artifact to become stale. None may make the independent
kernel accept a false closed formula.

There is an untrusted `erase_trusted_cuts` compatibility utility implementing
the formal expansion `(λh. body) lemma`. It deliberately does not normalize
the implication redex it creates. Erasure is not an alternative source of
authority and is operationally incomplete: the bidirectional checker cannot
synthesize every introduction-shaped erased argument, while the existing
capture-sensitive reducer does not reliably normalize every large
induction-bearing expansion. Only a separate successful kernel check licenses
an erased result. Ordinary replay instead checks the self-contained Cut tree
directly. Engine-only `LocalHave` and `LocalSuffices` remain a different
mechanism and are still compiled away before QED.
