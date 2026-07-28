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

The arithmetic entrance gate is now checked: the runtime has constructive
equality and divisibility decisions, bounded factor search,
prime-or-composite and primality decisions, proper-factor descent,
prime-divisor existence, relational gcd/Bézout, Gauss cancellation, and
Euclid's lemma. The decoded-value foundation is also checked: the β modulus is
nonzero, bounded values self-decode, and every position has exactly one
decoded value. Bounded balanced-congruent representatives are equal, and the
directed remainder/congruence bridge now works both ways. Consequently β
decoding is equivalent to the value bound plus balanced congruence between the
code and value at the β modulus. This does **not** prove FTA. The remaining
critical path starts with greatest-prime-divisor descent and then crosses the
still-unimplemented β-modulus coprimality, binary/bounded CRT, finite-prefix,
prefix-product, and finite-product layers.

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

These theorems decode an existing pair `(b,c)`. They do not yet construct one
code satisfying an arbitrary finite family of prescribed residues;
β-modulus coprimality, binary/bounded CRT, and finite-prefix extension remain
necessary.

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

The existential decoded values make non-vacuity explicit. Before admission,
these schemas must be frozen as hygienic Peano expanders with round-trip and
capture tests; the displayed names are not new kernel predicates.

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

The combined Peano FTA will expose both statements only after their fully
expanded targets and closed certificates pass the ordinary kernel gate.

## Proof dependency spine

The selected encoding fixes the intended first-order endpoint; it does not
make the proof small. The admission route and its current status are:

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
6. **Next arithmetic gate:** construct a greatest prime divisor with a strict
   quotient descent suitable for appending to an already sorted
   factorization.
7. **Encoding gate:** prove β-modulus coprimality, binary and bounded CRT, and
   finite-prefix extension and restriction.
8. **Product gate:** prove prefix-product trace extension/functionality and
   preservation of `AllPrime`/`Sorted`.
9. **Existence gate:** perform the strengthened natural-number descent using
   the greatest prime divisor and the encoded prefix/product extension laws.
10. **Uniqueness gate:** prove finite-product Euclid, prime matching,
   cancellation, and extensional equality of the two sorted decoded prefixes.

The reviewed self-contained `Cut` rule now supplies lexical proof sharing while
keeping every dependency proof inside the checked certificate. This removes
the former fully expanded proof-tree bottleneck, but it does not establish that
the much larger β/CRT/product spine will fit the live 32,768-node/depth-128
import budget. The current runtime maximum is 5,382 nodes, while
`prime_divisor_exists` reaches depth 80; those observations are evidence for
the arithmetic layer only, not a resource proof for encoded FTA. The
proof-sharing trust review is recorded separately and must not be disguised as
part of this notation.

## Independently checked companion

[`artifacts/lean-fta/FTA.lean`](../../artifacts/lean-fta/FTA.lean) already
checks the intended list-based theorem in Lean 4: existence for every nonzero
natural and uniqueness up to list permutation. Mathlib is pinned at commit
`37df177aaa770670452312393d4e84aaad56e7b6`. The repository audit rejects
`sorryAx` and requires the exact declared standard-axiom footprint
`propext`, `Classical.choice`, and `Quot.sound`.

That artifact establishes the target mathematics and statement shape. It is
not imported as a Peano axiom, and the Peano catalog remains explicit about
which sequence and arithmetic lemmas still lack closed PA certificates.
