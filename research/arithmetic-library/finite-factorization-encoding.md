# Conservative finite-factorization encoding

## Decision

Peano Lab will represent a finite factorization by natural-number codes, not
by adding a trusted list sort or a primitive factorization predicate. The
selected representation is a sorted Gödel β-coded factor sequence together
with a second β-coded trace of its prefix products.

This is an authoring interface only. Every named relation below must expand to
the existing first-order language before the theorem target reaches the
independent kernel. The kernel continues to know only `0`, `S`, `+`, `*`,
equality, logical connectives, quantifiers, PA1–PA6, and induction.

The arithmetic entrance gate is checked: the library has constructive
equality and divisibility decisions, bounded factor search,
prime-or-composite and primality decisions, proper-factor descent,
prime-divisor existence, relational gcd/Bézout, Gauss cancellation, and
Euclid's lemma. The decoded-value foundation is also checked: the β modulus is
nonzero, bounded values self-decode, and every position has exactly one
decoded value. Bounded balanced-congruent representatives are equal, and the
directed remainder/congruence bridge now works both ways. Consequently β
decoding is equivalent to the value bound plus balanced congruence between the
code and value at the β modulus. Constructive binary CRT is now checked, as is
a constructor for one code realizing two bounded β values under an explicit
coprimality premise. The new conditional layer proves that premise when the
ordered index gap divides `c`, applies the constructor, and produces a
nonzero `c` divisible by every positive gap through a chosen bound.
The bounded-prefix pairwise-coprimality theorem and the product/modulus/CRT
fold algebra are checked too. The later tranche now crosses the former
representation gap: it proves β finite-prefix recoding and exact one-value
extension, β-coded prefix-product trace existence and functionality,
relational finite-product laws, all-prime and sorted prefix laws,
greatest-prime-divisor descent, canonical append, factorization existence, and
extensional uniqueness. The exact combined FTA certificate is checked at this
integration checkpoint; runtime synchronization is complete.

## Sequence values

For natural codes $b,c$, index $i$, and value $x$, put

$$
M(c,i)=1+(i+1)c
$$

and define

$$
\operatorname{At}(b,c,i,x);:\!\Longleftrightarrow\;
x<M(c,i)\;\land\;
\exists q.\;b=qM(c,i)+x.
$$

In Peano surface syntax the modulus is `S ((S i) * c)`, strict inequality is
`S x <= S ((S i) * c)`, and `<=` itself expands to an existential addition
equation. Thus `At` introduces no new object-language constructor.

Seven checked theorems establish the relation's basic API:

- `beta_modulus_nonzero` proves constructively that $M(c,i)$ is a successor;
- `beta_at_self_of_bound` gives a quotient-zero code for any bounded value;
- `beta_at_exists` obtains a decoded residue from division with remainder;
- `beta_at_unique` reduces two decodings to remainder uniqueness;
- `beta_at_exists_unique` packages totality and functionality;
- `beta_at_to_mod_eq` exposes each decoding through the balanced congruence
  API after `remainder_decomposition_to_mod_eq` converts its quotient witness;
  and
- `beta_at_of_mod_eq_bound` uses `mod_eq_bounded_unique` and
  `mod_eq_to_remainder_decomposition` to reconstruct decoding from the bound
  and congruence.

Thus the checked API proves

$$
\operatorname{At}(b,c,i,x)
\quad\Longleftrightarrow\quad
x<M(c,i)\;\land\;b\equiv x\pmod{M(c,i)}
$$

when congruence is read as the subtraction-free balanced relation.

The next checked layer composes two positions. `bezout_mod_left` and
`bezout_mod_right` expose the modular inverse equations from balanced
natural Bézout witnesses; `mod_eq_predecessor_cancel` implements
minus-one behavior modulo a successor; `binary_crt` constructs the
balanced-congruence solution; and `binary_crt_remainders` exposes directed
remainder equations for bounded residues. `binary_crt_beta_pair` then
constructs one code for two bounded β values.

These theorems do not yet construct one code satisfying an arbitrary finite
family of prescribed residues. In particular, `binary_crt_beta_pair`
assumes coprimality of its two β moduli.

Unconditional pairwise coprimality is false: when `c=1`, positions
`i=1` and `j=4` have moduli 3 and 6. The checked replacement has
four parts:

- `beta_modulus_coprime_base` proves each successor β modulus coprime
  to `c`;
- `common_divisor_beta_moduli_divides_gap_times_c` shows a common
  divisor of the moduli at `j=i+gap` divides `gap*c`;
- `beta_moduli_coprime_of_gap_dvd` combines those facts with Gauss to
  prove the moduli coprime when `gap | c`; and
- `binary_crt_beta_pair_of_gap_dvd` discharges the original pair
  constructor's premise.

Separately, `bounded_common_multiple_step` and
`bounded_common_multiple_exists` construct a nonzero `c`
divisible by every positive natural at most a specified bound.
`beta_moduli_coprime_of_lt_bounded_common_multiple`,
`beta_moduli_pairwise_coprime_bounded`, and
`bounded_beta_moduli_pairwise_coprime_exists` now orient the indices
and package pairwise coprimality across the whole chosen prefix.

Four checked facts supply fold algebra:
`coprime_mul_left` and `coprime_mul_right` preserve
coprimality for an accumulated product,
`mod_eq_of_mod_eq_multiple` descends a product-modulus congruence to
each factor, and `binary_crt_fold_step` performs one extension while
preserving every earlier congruence. The checked bounded induction carries an
encoded modulus-product and solution invariant through all positions; the
subsequent exclusive-prefix invariant is what enables genuine recoding and
append.

A code pair is deliberately not treated as a canonical sequence identity.
Different pairs can decode the same finite prefix, so all later equality is
extensional: equal length and equal decoded entries at every bounded index.

## Prime factors and product trace

Primality uses the catalog's factor-pair expansion

$$
\operatorname{Prime}(p)\;:\!\Longleftrightarrow\;
p\ne1\land
\forall a\,d.\;p=ad\to(a=1\lor d=1).
$$

The first checked instance of this formula is `prime_two`. General
`prime_or_composite`, `prime_decidable`, and `prime_divisor_exists` theorems
now use the same formula fully expanded; a reusable surface `Prime` macro and
its hygiene tests remain an authoring convenience, not a mathematical
prerequisite or kernel extension. The selected schemas for the factor
conditions are

$$
\begin{aligned}
\operatorname{AllPrime}(b,c,l)
&\;:\!\Longleftrightarrow\;
  \forall i.\;i<l\to
  \exists p.\;\operatorname{At}(b,c,i,p)\land\operatorname{Prime}(p),\\
\operatorname{Sorted}(b,c,l)
&\;:\!\Longleftrightarrow\;
  \forall i.\;S i<l\to
  \exists p\,q.\;
  \operatorname{At}(b,c,i,p)\land
  \operatorname{At}(b,c,S i,q)\land p\le q.
\end{aligned}
$$

The existential decoded values make non-vacuity explicit. In the checked
targets these schemas are fully expanded; the displayed names are expository
abbreviations, not new kernel predicates.

The product is not introduced as a function. A second β-code `(u,v)` stores
prefix products:

$$
\begin{aligned}
\operatorname{Product}(b,c,l,n)\;:\!\Longleftrightarrow\;
\exists u\,v.\;&
  \operatorname{At}(u,v,0,1)\land
  \operatorname{At}(u,v,l,n)\\
&\land\forall i<l.\;\exists p\,r\,s.\;
  \operatorname{At}(b,c,i,p)\land
  \operatorname{At}(u,v,i,r)\\
&\hspace{34mm}\land
  \operatorname{At}(u,v,S i,s)\land s=rp.
\end{aligned}
$$

Finally,

$$
\operatorname{CanonicalPF}(n,l,b,c)
\;:\!\Longleftrightarrow\;
\operatorname{Product}(b,c,l,n)\land
\operatorname{AllPrime}(b,c,l)\land
\operatorname{Sorted}(b,c,l).
$$

Sorting removes the need for a primitive permutation relation in the Peano
endpoint while preserving every multiplicity.

## Peano endpoints

Existence is the closed first-order claim

$$
\forall n.\;n\ne0\to
\exists l\,b\,c.\;\operatorname{CanonicalPF}(n,l,b,c).
$$

The empty prefix represents the factorization of one. Uniqueness must compare
decoded values rather than raw codes:

$$
\begin{aligned}
\forall n\,l\,b\,c\,l'\,b'\,c'.\;&
  \operatorname{CanonicalPF}(n,l,b,c)\land
  \operatorname{CanonicalPF}(n,l',b',c')\to\\
&l=l'\land
  \forall i\,p\,q.\;i<l\land
  \operatorname{At}(b,c,i,p)\land
  \operatorname{At}(b',c',i,q)\to p=q.
\end{aligned}
$$

The exact combined Peano FTA is the conjunction of those fully expanded
endpoints. At this integration checkpoint its closed certificate passes the
ordinary empty-context kernel gate. The conclusion compares lengths and
decoded entries, never raw codes.

## Proof dependency spine

The selected encoding fixes the intended first-order endpoint; it does not
make the proof small. The completed admission route is:

1. **Checked:** discrete order, nonzero multiplication cancellation, and
   divisor bounds.
2. **Checked:** division with unique remainder and constructive divisibility
   and bounded factor search.
3. **Checked:** prime/composite decision, proper-factor descent,
   prime-divisor existence, relational gcd, balanced-natural Bézout, Gauss,
   and Euclid's lemma.
4. **Checked decoding gate:** prove β-value modulus nonzeroness, bounded
   self-decoding, existence, uniqueness, unique existence, and conversion to
   balanced congruence.
5. **Checked congruence gate:** prove bounded representative uniqueness, the
   reverse remainder bridge, and reconstruction of β decoding from bound plus
   balanced congruence.
6. **Checked binary CRT gate:** project balanced Bézout coefficients, prove
   successor-predecessor cancellation in congruence, prove binary CRT and its
   bounded-remainder form, and construct two β positions under an explicit
   modulus-coprimality premise.
7. **Checked conditional β-coprimality gate:** prove the base-coprimality and
   common-divisor/gap lemmas, discharge binary β-pair CRT when the gap divides
   `c`, and construct nonzero bounded common multiples.
8. **Checked greatest-prime gate:** construct a greatest prime divisor with a
   strict quotient descent suitable for appending to an already sorted
   factorization.
9. **Checked bounded-prefix/fold-algebra gate:** orient and bound all index
   gaps, package pairwise coprimality for the chosen prefix, close coprimality
   under products, descend congruence from product moduli, and prove one
   invariant-preserving CRT fold step.
10. **Checked existing-code prefix gate:** combine the accumulated-product and
   decoded-congruence successor steps, fold their invariant by ordinary
   induction, and project a common congruence witness for positions already
   decoded from a supplied `BetaAt` code. This is not arbitrary
   finite-sequence coding.
11. **Checked recoding/product gate:** prove exclusive-prefix recoding,
   `beta_prefix_extend`, exact prefix-product trace existence,
   `beta_product_exists`, functionality, unique existence, zero/successor
   decomposition, append, and prefix transport.
12. **Checked canonical append gate:** preserve `AllPrime`, `Sorted`, and the
   exact Product relation while appending the greatest prime divisor.
13. **Checked existence gate:** perform strengthened natural-number descent
   using greatest-prime-divisor descent and canonical append. The final
   existence certificate has 43,973 nodes and depth 98.
14. **Checked uniqueness gate:** prove product membership for a prime divisor,
   match sorted last factors, cancel them, and induct on length. The final
   uniqueness certificate has 29,789 nodes and depth 82.
15. **Checked FTA gate:** combine the exact catalog endpoints in a closed
   73,767-node, depth-99 certificate containing 2,184 self-contained Cuts.

The reviewed self-contained `Cut` rule now supplies lexical proof sharing while
keeping every dependency proof inside the checked certificate. The exact FTA
certificate fits the current live/use budget of 500,000 structural
occurrences, 100,000 distinct proof objects, and depth 256:
73,767 nodes, depth 99, and 2,184 Cuts. Its SHA-256 is
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
The full prove/use/exact/QED path and independent empty-context replay pass;
dependency, hypothesis, PA-rule, and semantic mutations are rejected. The
proof uses PA1–PA6 and induction only and contains no DNE. The proof-sharing
trust review is recorded separately and must not be disguised as part of the
β notation.

## Independently checked companion

[`artifacts/lean-fta/FTA.lean`](../../artifacts/lean-fta/FTA.lean) already
checks the intended list-based theorem in Lean 4: existence for every nonzero
natural and uniqueness up to list permutation. Mathlib is pinned at commit
`37df177aaa770670452312393d4e84aaad56e7b6`. The repository audit rejects
`sorryAx` and requires the exact declared standard-axiom footprint
`propext`, `Classical.choice`, and `Quot.sound`.

That artifact establishes the conventional list statement independently. It
is not imported as a Peano axiom. The native theorem is instead the checked
β-coded, sorted, extensional endpoint above. Peano Lab still has no primitive
list or multiset type, and code equality is intentionally not the uniqueness
criterion. Prime unboundedness is checked independently of FTA by the
bounded-common-multiple/successor-prime-divisor argument.
