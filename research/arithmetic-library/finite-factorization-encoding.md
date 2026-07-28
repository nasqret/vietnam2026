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

The first checked instance of this formula is `prime_two`; a reusable general
`Prime` macro and its hygiene tests are still planned. The selected schemas
for the factor conditions are

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
make the proof small. The proposed admission route is:

1. discrete order, nonzero multiplication cancellation, and divisor bounds;
2. division with unique remainder and bounded divisibility search;
3. least divisor, prime-divisor existence, gcd, balanced-natural Bézout, and
   Euclid's lemma;
4. β-value existence/functionality, finite-prefix extension, and the required
   CRT/common-multiple coding theorem;
5. prefix-product extension and preservation of `AllPrime`/`Sorted`;
6. factorization existence by strengthened natural-number induction;
7. finite-product Euclid, prime matching, cancellation, and extensional
   uniqueness.

The current cut-eliminated proof-tree representation may exceed the live
4,096-node/depth-128 import budget. Any future proof-sharing mechanism needs
its own trust review; it must not be disguised as part of this notation.

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
