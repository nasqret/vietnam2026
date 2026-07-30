# Fermat, Wilson, and the remaining reciprocity spine

Status: **native-PA design and isolated-candidate note, not an admission
record**. All eight fixed Fermat rungs now have isolated source candidates,
both immediate Fermat endpoints now have isolated source candidates, and the
first Wilson fixed-point lemma, seven inverse-index/prefix lemmas, six
extensional involution lemmas, and three explicit inverse-endpoint lemmas are
also isolated. None is public until its
content-addressed WMI discovery and separate receipt-pinned admission replay
pass. The mathematical chain through the exact quadratic-reciprocity surface
is now dependency-curried and body-green, but none of Wilson's theorem,
Fermat's little theorem, Euler's criterion, Gauss's lemma, Eisenstein's lemma,
or quadratic reciprocity is recursively closed or admitted by this document.

This note records the shortest reviewed route from the current finite-fold
library to Fermat, then separates the extra combinatorics required for Wilson.
That separation matters: Fermat needs multiplication to permute the nonzero
residues and cancellation of their product; Wilson additionally needs a
finite fixed-point-free involution argument and a classification of the fixed
points of inversion.

## Boundary at the start of this tranche

The checked library already supplies the following native ingredients:

- division with remainder, balanced congruence, bounded-remainder uniqueness,
  congruence algebra, divisor bounds, Euclid's lemma, prime modular
  cancellation, and constructive prime/coprime alternatives;
- hygienically expanded `BetaAt`, consecutive `Range`, exact `Product`,
  relational `Pow`, and relational factorial surfaces, together with their
  existence, functionality, zero, successor, and transport theorems;
- pointwise congruence transport for finite products;
- constructive bounded-injection-implies-surjection for decoded prefixes;
- one-position replacement balance and exact product invariance under an
  interior/final swap;
- the fixed-last bounded-prefix and synchronized alignment-swap support rungs
  for general product reindexing;
- parity, odd-prime, half-range, and predecessor-sign foundations needed later
  by Gauss's lemma.
- the checked `prime_is_succ_succ` and
  `prime_bounded_nonzero_mod_inverse` rungs, giving a nonzero representative
  below a prime for every nonzero bounded residue.

The general theorem `beta_product_permutation_invariant` is still an active
pre-Fermat gate at this design checkpoint. Its fixed-last proof and full
successor induction live as isolated candidates until they pass the complete
admission audit. The eight theorems below may be developed independently
where their dependency slices permit, but theorem 8 must not enter the public
registry before that general reindex theorem is checked.

The bounded-inverse rungs are public checked facts. They become relevant to
Wilson's inversion map rather than to the eight-rung Fermat route below.

## Formula conventions

The names in this section are **notation in this document only**. They are not
new parser tokens, kernel constants, definitions trusted by the checker, or
theorem hypotheses. An implementation must generate their hygienic expansions
before parsing.

For natural variables, write

\[
\begin{aligned}
i<l &\;:\!\Longleftrightarrow\; \exists h.\;h+S i=l,\\
i\le n &\;:\!\Longleftrightarrow\; \exists h.\;h+i=n,\\
d\mid x &\;:\!\Longleftrightarrow\; \exists k.\;x=d k,\\
x\equiv y\pmod m
 &\;:\!\Longleftrightarrow\;\exists u,v.\;x+m u=y+m v,\\
\operatorname{Coprime}(x,m)
 &\;:\!\Longleftrightarrow\;
 \forall d.\;(d\mid x)\to(d\mid m)\to d=1,\\
\operatorname{Prime}(p)
 &\;:\!\Longleftrightarrow\;
 p\ne1\land\forall c,e.\;p=ce\to(c=1\lor e=1).
\end{aligned}
\]

The exact decoded-entry convention is

\[
\operatorname{At}(b,c,i,x)\;:\!\Longleftrightarrow\;
 \bigl(\exists h.\;h+Sx=S((Si)c)\bigr)\land
 \bigl(\exists q.\;b=qS((Si)c)+x\bigr).
\]

The remaining finite relations expand through `At` as follows:

\[
\begin{aligned}
\operatorname{Range}(b,c,a,l)
 &:\!\Longleftrightarrow
 \forall i.\;i<l\to\operatorname{At}(b,c,i,a+i),\\
\operatorname{Product}(b,c,l,P)
 &:\!\Longleftrightarrow
 \exists u,v.\;\operatorname{At}(u,v,0,1)\land
 \operatorname{At}(u,v,l,P)\\
 &\qquad\land\forall i.\;i<l\to\exists x,r,s.\;
 \operatorname{At}(b,c,i,x)\land\operatorname{At}(u,v,i,r)\\
 &\hspace{13.2em}\land\operatorname{At}(u,v,Si,s)\land s=rx,\\
\operatorname{Pow}(a,l,A)
 &:\!\Longleftrightarrow
 \exists b,c.\;\bigl(\forall i.\;i<l\to
 \operatorname{At}(b,c,i,a)\bigr)\land
 \operatorname{Product}(b,c,l,A).
\end{aligned}
\]

For a decoded index map, use

\[
\begin{aligned}
\operatorname{Bounded}(r,s,l)
 &:\!\Longleftrightarrow
 \forall i.\;i<l\to\exists j.\;
 \operatorname{At}(r,s,i,j)\land j<l,\\
\operatorname{Injective}(r,s,l)
 &:\!\Longleftrightarrow
 \forall i,j,x.\;i<l\to j<l\to
 \operatorname{At}(r,s,i,x)\to
 \operatorname{At}(r,s,j,x)\to i=j,\\
\operatorname{Aligned}(r,s,b,c,z,d,l)
 &:\!\Longleftrightarrow
 \forall i,j,x.\;i<l\to
 \operatorname{At}(r,s,i,j)\to
 \operatorname{At}(b,c,j,x)\to
 \operatorname{At}(z,d,i,x),\\
\operatorname{ScaleMod}(m,a,b,c,z,d,l)
 &:\!\Longleftrightarrow
 \forall i,x,y.\;i<l\to
 \operatorname{At}(b,c,i,x)\to
 \operatorname{At}(z,d,i,y)\to ax\equiv y\pmod m.
\end{aligned}
\]

Every multiplication in the generated source uses the existing binary `*`
term constructor; juxtaposition above is only mathematical typography. Raw
equality of two beta codes is never used as extensional sequence equality.

## Immediate eight-theorem Fermat tranche

The prototype expanded statements have already been checked for input size.
The lengths below are authoring prototypes, not certificate metrics or stable
statement hashes; hygienic implementation must remeasure the final strings.

| order | isolated candidate | prototype source characters | logical role |
|---:|---|---:|---|
| 1 | `beta_range_one_entry_eq_succ` | 425 | normalize the range `1,...,l` |
| 2 | `beta_product_pointwise_coprime` | 1,503 | fold pointwise coprimality |
| 3 | `prime_range_product_coprime` | 1,752 | make the nonzero-residue product cancellable |
| 4 | `beta_successor_lift_exists` | 301 | recode every decoded value by successor |
| 5 | `prime_mul_index_map_exists_up_to` | 482 | construct multiplication remainders on a prefix |
| 6 | `prime_mul_residue_reindex_exists` | 2,363 | package the residue permutation and both alignments |
| 7 | `beta_product_pointwise_scale_mod` | 4,790 | extract a constant scale from a finite product modulo `m` |
| 8 | `prime_mul_residue_product_balance` | 3,677 | identify the scaled residue product with the original one |

All eight prototypes fit below the current 8,192-character interactive source
ceiling. Their contracts and intended direct dependency slices follow.

### 1. `beta_range_one_entry_eq_succ`

Contract schema:

\[
\forall b,c,l,i,x.\;
 \operatorname{Range}(b,c,1,l)\to i<l\to
 \operatorname{At}(b,c,i,x)\to x=Si.
\]

Intended direct dependencies: checked `beta_range_entry_eq` plus ordinary
addition normalization.

Proof route: `beta_range_entry_eq` gives `x = 1 + i`; normalize `1+i` to
`S i`. This small lemma prevents every later residue argument from repeating
the same syntactic conversion.

### 2. `beta_product_pointwise_coprime`

Contract schema:

\[
\begin{aligned}
\forall b,c,l,z,m.\;&
 \bigl(\forall i,x.\;i<l\to\operatorname{At}(b,c,i,x)
       \to\operatorname{Coprime}(x,m)\bigr)\\
&\to\operatorname{Product}(b,c,l,z)
 \to\operatorname{Coprime}(z,m).
\end{aligned}
\]

Intended direct dependencies: checked `beta_product_zero`,
`beta_product_succ_decompose`, `coprime_one_left`, `coprime_mul_left`,
`le_succ`, and `le_refl`.

Proof route: induct on `l`. At zero the product is one. At `S l`, decompose
the product as prefix product times its final factor, apply the induction
hypothesis to the restricted pointwise premise, obtain coprimality of the
last factor at the reflexive bound, and combine both facts with
`coprime_mul_left`.

### 3. `prime_range_product_coprime`

Contract schema:

\[
\begin{aligned}
\forall p,n,b,c,F.\;&p=Sn\to\operatorname{Prime}(p)
 \to\operatorname{Range}(b,c,1,n)\\
&\to\operatorname{Product}(b,c,n,F)
 \to\operatorname{Coprime}(F,p).
\end{aligned}
\]

Intended direct dependencies: planned rungs 1 and 2, together with checked
`prime_not_divides_coprime`, `coprime_symm`, `divisor_le_nonzero`,
`lt_not_le`, `succ_ne_zero`, and the basic successor/order lemmas.

Proof route: every decoded factor is `S i` with `i<n`, hence `0<S i<p` when
`p=S n`. If `p` divided `S i`, `divisor_le_nonzero` would give `p<=S i`,
contradicting the strict bound. Primality therefore makes each factor
coprime to `p`; theorem 2 folds those pointwise facts into coprimality of
`F`. No factorial function is needed: `F` is the exact product witness for
the range.

### 4. `beta_successor_lift_exists`

Contract schema:

\[
\forall r,s,l.\;\exists z,d.\;\forall i,j.\;
i<l\to\operatorname{At}(r,s,i,j)\to
\operatorname{At}(z,d,i,Sj).
\]

Intended direct dependencies: checked `beta_at_exists`,
`beta_prefix_extend`, `beta_at_unique`, and the finite successor-bound split
lemmas.

Proof route: induct on `l`. The empty prefix is vacuous. At a successor,
decode the old code at the new final index, extend the output prefix by the
successor of that decoded value, and transport earlier positions. This is a
finite recoding theorem, not a primitive map operation.

### 5. `prime_mul_index_map_exists_up_to`

Contract schema:

\[
\begin{aligned}
\forall l,n,p,a.\;&l\le n\to p=Sn\to\operatorname{Prime}(p)
 \to\neg(p\mid a)\\
&\to\exists r,s.\;\forall i.\;i<l\to\exists j.\;
 j<n\land\operatorname{At}(r,s,i,j)
 \land a(Si)\equiv Sj\pmod p.
\end{aligned}
\]

Intended direct dependencies: checked `division_remainder_exists`,
`remainder_decomposition_to_mod_eq`, `euclid_prime_dvd_product`,
`divisor_le_nonzero`, `prime_nonzero`, `beta_prefix_extend`, and the discrete
order lemmas.

Proof route: inductively divide `a*S i` by `p`. The canonical remainder is
below `p`. It cannot be zero: otherwise Euclid's lemma makes `p` divide `a`
or `S i`; the first alternative is excluded by hypothesis and the second by
`S i<p`. Therefore the remainder is `S j`, and `S j<p=S n` yields `j<n`.
Append `j` to the decoded map. This is a constructive bounded-remainder
construction; it does not choose an unspecified residue representative.

### 6. `prime_mul_residue_reindex_exists`

Contract schema:

\[
\begin{aligned}
\forall p,n,a,b,c.\;&p=Sn\to\operatorname{Prime}(p)
 \to\neg(p\mid a)\to\operatorname{Range}(b,c,1,n)\\
&\to\exists r,s,z,d.\;
 \operatorname{Bounded}(r,s,n)
 \land\operatorname{Injective}(r,s,n)\\
&\qquad\land\operatorname{Aligned}(r,s,b,c,z,d,n)
 \land\operatorname{ScaleMod}(p,a,b,c,z,d,n).
\end{aligned}
\]

Intended direct dependencies: planned rungs 1, 4, and 5; checked
`prime_mod_cancel`, `mod_eq_trans`, `mod_eq_symm`,
`mod_eq_bounded_unique`, `beta_at_unique`, and successor injectivity.

Proof route: instantiate theorem 5 at `l=n`. Successor-lift its decoded map,
so target entry `i` is `S j` when the map sends `i` to `j`. The range lemma
identifies source entry `j` with `S j`, giving target-to-source alignment.
It also identifies source entry `i` with `S i`, giving the pointwise scaling
congruence. Boundedness is part of theorem 5. For injectivity, equal decoded
map values give

\[
a(Si)\equiv a(Sk)\pmod p.
\]

Cancel `a` with `prime_mod_cancel`, use bounded-remainder uniqueness on
`S i,S k<p`, and apply successor injectivity. The output deliberately carries
both alignments: permutation alignment compares products, while scale
alignment extracts `a^n`.

### 7. `beta_product_pointwise_scale_mod`

Contract schema:

\[
\begin{aligned}
\forall m,a,b,c,z,d,l,P,Q,A.\;&
 \operatorname{ScaleMod}(m,a,b,c,z,d,l)\\
&\to\operatorname{Product}(b,c,l,P)
 \to\operatorname{Product}(z,d,l,Q)\\
&\to\operatorname{Pow}(a,l,A)
 \to AP\equiv Q\pmod m.
\end{aligned}
\]

Intended direct dependencies: checked product and power zero/successor
decomposition, `mod_eq_refl`, `mod_eq_mul`, `mul_assoc`, `mul_comm`, and the
successor-bound lemmas. `beta_product_pointwise_mod_congruent` may be reused
if an auxiliary scaled-prefix code makes the proof smaller, but it is not a
license to introduce multiplication as a sequence primitive.

Proof route: induct on `l`. At zero, all three fold values normalize to one.
At a successor, decompose both products and the power, apply the induction
hypothesis to the prefixes, apply the pointwise premise to the two last
entries, multiply the two congruences, and reassociate/commute multiplication
to obtain `(A*a)*(P*x) ≡ Q*y`. This is exactly the successor instance of the
displayed endpoint.

### 8. `prime_mul_residue_product_balance`

Contract schema:

\[
\begin{aligned}
\forall p,n,a,b,c,F,A.\;&p=Sn\to\operatorname{Prime}(p)
 \to\neg(p\mid a)\to\operatorname{Range}(b,c,1,n)\\
&\to\operatorname{Product}(b,c,n,F)
 \to\operatorname{Pow}(a,n,A)
 \to AF\equiv F\pmod p.
\end{aligned}
\]

Intended direct dependencies: planned rungs 6 and 7; checked
`beta_product_exists`; and the still-active prerequisite
`beta_product_permutation_invariant` once admitted.

Proof route: theorem 6 supplies a bounded injective map and a target prefix.
Construct its target product `Q`. General product-reindex invariance identifies
`Q=F` from boundedness, injectivity, and alignment. Theorem 7 gives
`A*F ≡ Q`; rewrite `Q` to `F`. Surjectivity is not carried as an extra premise:
the checked finite pigeonhole theorem is used inside general reindex
invariance.

### Non-admitting Fermat body preflight

The reusable
`peano_lab.library.candidate_validation.replay_candidate_bodies` utility
kernel-checks dependency-curried candidate scripts without replaying or
closing their dependencies and returns exact structural/identity metrics. Its
three unit tests pass. This is deliberately a fast defect detector, never an
admission receipt.

Applied to the finite-product plus Fermat stack, it now passes all 21 bodies.
It caught and fixed a missing second rewrite in
`beta_successor_range_reindex_aligned` and eliminated an invalid locally
repackaged `hprojection` in `prime_mul_residue_product_balance`. Key body-only
nodes/depth are:

| candidate | nodes/depth |
|---|---:|
| `beta_successor_range_reindex_aligned` | `86/34` |
| `beta_successor_range_scale_mod` | `62/32` |
| `prime_mul_residue_reindex_exists` | `106/40` |
| `prime_mul_residue_product_balance` | `93/39` |
| `fermat_predecessor_exponent_mod_one` | `93/34` |
| `fermat_little_all_inputs` | `104/30` |

Nine bounded structural gates pass across reindex, balance, and endpoints.
Original zero-CPU jobs `172769`, `172770`, and `172837` were cancelled stale.
Corrected snapshot
`73d2863a0138c8dce1f8a7f2793bcd96f543e389c0c4af6cce75cc13005ac3d9`
backs pending jobs `172988` (reindex, 16 GiB/2 hours), `172989` (balance,
16 GiB/2 hours), and `172990` (endpoints, 32 GiB/4 hours). Neither body
preflight nor structural gates close recursive dependencies; no theorem is
admitted.

## The two immediate Fermat endpoints

The eight-rung tranche is intentionally followed by two small corollaries.
Their exact expanded contracts and final candidate names are now generated in
`fermat_endpoints_candidate.py`, but both remain isolated pending the
dedicated five-gate `fermat-endpoints` WMI discovery result and a later pinned
admission replay. Corrected discovery job `172990` is pending from snapshot
`73d2863a0138c8dce1f8a7f2793bcd96f543e389c0c4af6cce75cc13005ac3d9`.

### Predecessor-exponent form

Isolated candidate: `fermat_predecessor_exponent_mod_one`.

Exact candidate contract:

\[
\begin{aligned}
\forall p,n,a,A.\;&p=Sn\to\operatorname{Prime}(p)
 \to\neg(p\mid a)\to\operatorname{Pow}(a,n,A)\\
&\to A\equiv1\pmod p.
\end{aligned}
\]

Choose a checked range/product witness `F` for `1,...,n`. Theorem 8 gives
`A*F ≡ F`, while theorem 3 gives `Coprime(F,p)`. Rewrite the right side as
`1*F`, orient both products consistently, and apply checked coprime modular
cancellation. Since `p=S n`, the exponent `n` is exactly the native
predecessor representation of `p-1`; no subtraction term is introduced.
Its direct dependencies are `factorial_exists`,
`prime_mul_residue_product_balance`, `prime_range_product_coprime`,
`prime_nonzero`, `mod_eq_cancel_coprime`, `mul_comm`, and `mul_one`.

### All-input form

Isolated candidate: `fermat_little_all_inputs`.

Exact candidate contract:

\[
\forall p,a,A.\;\operatorname{Prime}(p)\to
\operatorname{Pow}(a,p,A)\to A\equiv a\pmod p.
\]

Extract `p=S n` from checked prime nonzeroness. Constructively split whether
`p` divides `a` using division/remainder data (or the checked prime
coprime-or-divides alternative plus its elementary conversion). In the
nondivisibility branch, decompose the successor power, apply the
predecessor-exponent theorem, and multiply its congruence by `a`. In the
divisibility branch, the last factor `a` makes the successor power divisible
by `p`, so both sides are congruent to zero. This wrapper must not use a
classical `by_cases` or `DNE`; the isolated candidate script uses neither.
Its direct dependencies are `prime_nonzero`, `nonzero_is_succ`,
`pow_successor_decompose`, `prime_coprime_or_divides`, `multiple_refl`, the
predecessor endpoint, `mod_eq_mul_right`, `one_mul`, `multiple_mul_left`, and
`add_comm`.

These are source and test contracts, not theorem results. Corrected endpoint
job `172990` requests 1 CPU, 32768 MiB, and `04:00:00`. It was pending at
submission, so there is no validated report, metric receipt, pass claim, or
admission. Heavy replay and profiling remain WMI-only.

## Wilson's theorem is a separate gate

Fermat does not require a globally chosen inverse for every residue. Wilson
does. Reusable Wilson arithmetic candidates can be isolated while the Fermat
tranche is under WMI review, but Wilson composition should begin only after
that tranche is admitted. The branch should expose reusable pieces rather
than burying them in one large certificate.

### Fixed points of inversion

Isolated candidate, not a checked theorem:
`prime_bounded_square_one_cases`.

\[
\begin{aligned}
\forall p,n,x.\;&p=Sn\to\operatorname{Prime}(p)
 \to 0<x\to x<p\to x^2\equiv1\pmod p\\
&\to(x=1\lor x=n).
\end{aligned}
\]

Here `x^2` must be the ordinary term `x*x`, not exponentiation syntax. From
bounded congruence, obtain `x*x = 1 + p*k`. Write nonzero `x` as `S t` and
normalize

\[
x^2-1=t(t+2)
\]

without subtraction, as an equality `x*x = 1 + t*(S(S t))`. Thus `p` divides
`t*(x+1)`. Euclid's lemma gives `p|t` or `p|(x+1)`. Bounds force `t=0` in the
first branch and `x+1=p` in the second, hence `x=1` or `x=n`. This is the
native replacement for the field argument `(x-1)(x+1)=0`.

The candidate no longer invokes the UI-only `ring` tactic. Its normalization
is an explicit native equality/rewrite derivation, and the authored proof uses
exactly these 16 direct dependencies, in this order:

```text
ne_zero_of_one_le, nonzero_is_succ, mul_succ_left, add_assoc, add_comm,
add_left_cancel, factor_difference, euclid_prime_dvd_product,
le_succ_self, lt_of_le_of_lt, zero_or_succ, divisor_le_nonzero,
lt_not_le, succ_ne_zero, le_antisymm, succ_injective
```

The source is
[`wilson_square_one_candidate.py`](../../peano-lab/py/peano_lab/library/wilson_square_one_candidate.py).
Its expanded `Prime`, positivity, strict-bound, and balanced-congruence
surfaces are hygienic authoring helpers only; all disappear before parsing by
the native PA kernel. The dedicated five-gate `wilson-square-one` WMI suite
checks the exact contract, helper hygiene, isolated dependency boundary, two
cold full-Cut replays with resource profiles, no-DNE/capacity properties, and
false-contract/every-dependency-edge mutations. It was submitted as discovery
job `172855` from snapshot
`396af02c5aa4fdf62d4c3484f8a2c711b03c489cad498c121d0402ce3ee79981`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`; it was cancelled stale
after zero CPU. The corrected body-only receipt is 182 nodes/depth 48, and the
three bounded structural gates passed. Replacement job `172966`, from exact
snapshot `9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
is pending with zero CPU. Body-only and structural evidence is not closed-
certificate admission: there is no report, WMI pass, or new theorem. Heavy
execution remains WMI-only.

### Zero-based inverse indices and β-prefixes

Seven isolated source candidates now implement the inverse-map construction,
without a choice function and without adding a function or list type. Original
discovery job `172899`, suite `wilson-inverse-prefix`, used snapshot
`1a11442b18dd6c40b49975e16f0b2062be57fade347acca20d87dba27e6adffc`.
Cheap body replay found two existential-binder errors, so that job was
cancelled after zero CPU. The fixes are staged in exact snapshot
`6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`;
replacement job `172975` is pending at submission. This is only a scheduler
receipt: no report, pass, pinned metrics, or admission exists yet.

For `p = S n`, positions and decoded values are both **zero-based**. Position
`i < n` denotes the nonzero residue `S i`; decoded mate `j < n` denotes
`S j`. The readable relation is exactly

\[
\begin{aligned}
\operatorname{InvIdx}(p,n,i,j) :\!\Longleftrightarrow{}&
 (\exists g_i.\;g_i+S i=n)\\
 &\land (\exists g_j.\;g_j+S j=n)\\
 &\land (\exists u,v.\;(S i)(S j)+pu=1+pv).
\end{aligned}
\]

Thus `InvIdx` stores both bounds and the balanced modular-inverse witness. It
does not store raw residues, so no `-1` conversion is ever required.

The existing β convention is expanded literally as

\[
\operatorname{At}(b,c,i,j) :\!\Longleftrightarrow
 (\exists h.\;h+S j=S((S i)c))\land
 (\exists q.\;b=q\,S((S i)c)+j).
\]

The prefix relation is existential-total, not a primitive sequence:

\[
\begin{aligned}
\operatorname{InvPrefix}(p,n,b,c,\ell) :\!\Longleftrightarrow
\forall i.\;&(\exists g.\;g+S i=\ell)\to\exists j.\\
&\operatorname{At}(b,c,i,j)\land
  \operatorname{InvIdx}(p,n,i,j).
\end{aligned}
\]

All three displayed names are documentation-only surfaces. The two candidate
factories hygienically expand them to `0`, `S`, `+`, `*`, equality,
quantifiers, and intuitionistic connectives before parsing.

The exact theorem decomposition and ordered direct dependencies are:

| candidate | role | exact direct dependencies |
|---|---|---|
| `prime_inverse_index_exists` | every `i<n` has a zero-based mate | `succ_ne_zero`, `succ_le_succ`, `prime_bounded_nonzero_mod_inverse`, `nonzero_is_succ`, `le_of_succ_le_succ` |
| `bounded_mod_inverse_unique` | two bounded raw inverse residues are equal | `mod_eq_symm`, `mod_eq_mul_left`, `mod_eq_mul_right`, `mul_assoc`, `mul_comm`, `mul_one`, `one_mul`, `mod_eq_trans`, `mod_eq_bounded_unique` |
| `bounded_inverse_index_unique` | two `InvIdx` mates of one index are equal | `succ_le_succ`, `bounded_mod_inverse_unique`, `succ_injective` |
| `inverse_index_symmetric` | `InvIdx(p,n,i,j)` implies `InvIdx(p,n,j,i)` | `mul_comm` |
| `prime_inverse_prefix_extend` | append the mate at position `l` | `prime_inverse_index_exists`, `beta_prefix_extend`, `finite_lt_succ_eq_or_lt` |
| `prime_inverse_prefix_exists_bounded` | construct every prefix with `l≤n` by induction | `add_eq_zero_right`, `succ_ne_zero`, `lt_to_le`, `prime_inverse_prefix_extend` |
| `prime_inverse_prefix_exists` | specialize bounded existence to length `n` | `le_refl`, `prime_inverse_prefix_exists_bounded` |

The first four live in
[`wilson_inverse_point_candidate.py`](../../peano-lab/py/peano_lab/library/wilson_inverse_point_candidate.py);
the last three live in
[`wilson_inverse_prefix_candidate.py`](../../peano-lab/py/peano_lab/library/wilson_inverse_prefix_candidate.py).
The extension proof first obtains the mate for `l`, invokes checked
`beta_prefix_extend`, and classifies each `i<S l` as `i=l` or `i<l`. The
bounded theorem then inducts on `l`, and the final theorem supplies `n≤n`.
The dedicated WMI suite audits the exact helper/contracts and dependency
topology, replays the seven-node stack twice from cold state, profiles the
entire Cut closure, rejects DNE and capacity violations, and mutates the
contract plus every live dependency edge. Job `172975` remains pending, so
none of those closed-replay gates is yet a result.

### Extensional involution and fixed indices

Six more isolated candidates compose the zero-based prefix into the API needed
by pairing:

| candidate | role | exact direct dependencies |
|---|---|---|
| `inverse_prefix_entry_sound` | decoded entry implies its stored `InvIdx` | `beta_at_unique` |
| `inverse_prefix_extensional` | a valid mate is the decoded entry | `bounded_inverse_index_unique` |
| `inverse_prefix_involutive` | decode twice and return to the source | `inverse_prefix_entry_sound`, `inverse_index_symmetric`, `inverse_prefix_extensional` |
| `inverse_prefix_injective` | equal mates imply equal indices | `inverse_prefix_involutive`, `beta_at_unique` |
| `inverse_prefix_surjective` | every bounded value is hit | `inverse_prefix_involutive` |
| `prime_inverse_prefix_fixed_cases` | classify a decoded fixed index | `inverse_prefix_entry_sound`, `succ_le_succ`, `prime_bounded_square_one_cases`, `succ_injective` |

The first five theorems are prime-free by design. Entry soundness is fully
general in `p,n`; extensionality, involution, injectivity, and surjectivity
assume only `p=S n`. Primality occurs solely in
`prime_inverse_prefix_fixed_cases`, whose exact conclusion is

\[
i=0\lor S i=n.
\]

This keeps reusable β-map facts independent of number theory. Soundness uses
β uniqueness; extensionality uses bounded inverse-index uniqueness; symmetry
plus extensionality gives involution; and injection/surjection follow without
excluded middle. The fixed theorem turns `At(b,c,i,i)` into the square-one
hypothesis for residue `S i` and applies the isolated prime classifier.

All six live in
[`wilson_inverse_involution_candidate.py`](../../peano-lab/py/peano_lab/library/wilson_inverse_involution_candidate.py).
The five-gate `wilson-inverse-involution` suite recursively closes 14 isolated
specs and was submitted as discovery job `172920` from snapshot
`cfa4eea18d4a746a49a2d7579f217dbd65a27a79df61c76e8dba49079ba1aaa4`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`; it was cancelled after
zero CPU. First replacement `172967`, from snapshot
`9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
was also cancelled after zero CPU when the prefix dependency changed.
Corrected job `172976`, from snapshot
`6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
is pending. There is no report, pass, pinned metric set, or admission.

### Explicit fixed endpoint entries

Three isolated candidates now turn the fixed-index cases into decoded facts:

| candidate | role | exact direct dependencies |
|---|---|---|
| `inverse_prefix_zero_fixed` | decode `At(b,c,0,0)` from `p=S n`, `n=S k`, and the full prefix | `mod_eq_refl`, `one_mul`, `inverse_prefix_extensional` |
| `inverse_prefix_last_fixed` | decode `At(b,c,k,k)` under the same shape | `zero_add`, `predecessor_square_mod_one`, `inverse_prefix_extensional` |
| `prime_inverse_prefix_exact_endpoints` | package `n=S k`, both entries, and `i<n -> At(b,c,i,i) -> i=0 \/ i=k` | `prime_is_succ_succ`, `succ_injective`, both endpoint candidates, `prime_inverse_prefix_fixed_cases` |

The source is
[`wilson_inverse_endpoints_candidate.py`](../../peano-lab/py/peano_lab/library/wilson_inverse_endpoints_candidate.py).
The theorem package makes no false distinctness claim: for prime `2`, its
witness is `k=0` and `At(0,0)` is both endpoint facts; prime `3` has `k=1`.

The focused five-gate `wilson-inverse-endpoints` suite closes the 17-spec
recursive graph and checks exact contracts/dependencies, hygienic helpers,
graph/core isolation, two cold closed replays with proof hashes and RSS, no-DNE
and capacity bounds, and a unique false contract plus every direct Cut-edge
mutation. Discovery job `172927` was submitted from exact snapshot
`7083e3876cc54daa782153aa6e1a2554aa75fa5a40cce3d6cf6b5971979dc35d`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`; it was cancelled after
zero CPU. First replacement `172968`, from snapshot
`9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
was also cancelled after zero CPU when the prefix dependency changed. The
three bounded structural gates passed locally; heavy recursive replay,
profiling, and mutation remain WMI-only. Corrected job `172977`, from snapshot
`6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
is pending discovery only. There is no report, pass, pinned metric receipt, or
admission. At the original endpoint checkpoint the runner exposed seven
focused suites and a 66-gate full audit.

### First nonendpoint inverse orbits

Two further isolated candidates make the endpoint classification operational
away from those endpoints:

| candidate | role | exact direct dependencies |
|---|---|---|
| `prime_inverse_prefix_nonendpoint_not_fixed` | from `At(b,c,i,j)` and `~(i=0) /\ ~(S i=n)`, prove `~(i=j)` | `prime_inverse_prefix_fixed_cases` |
| `prime_inverse_prefix_nonendpoint_mate` | prove the decoded mate also satisfies `~(j=0) /\ ~(S j=n)` | `prime_inverse_prefix_nonendpoint_not_fixed`, `inverse_prefix_involutive`, `prime_is_succ_succ`, `succ_injective`, `inverse_prefix_zero_fixed`, `inverse_prefix_last_fixed`, `beta_at_unique` |

The first proof rewrites an assumed fixed decode into `At(b,c,i,i)` and
contradicts the existing fixed-case classification. The second decodes back by
involution; if the mate were `0` or the last index, β uniqueness against the
corresponding fixed endpoint entry would force `i=j`. No excluded middle or
double-negation elimination is used. Prime `2` remains honest: the endpoint
descriptions may coincide, and the contracts never assert that a nonendpoint
source exists.

The source is
[`wilson_inverse_orbit_candidate.py`](../../peano-lab/py/peano_lab/library/wilson_inverse_orbit_candidate.py).
Its focused five-gate `wilson-inverse-orbit` suite recursively closes
`1+4+3+6+3+2 = 19` isolated specs and audits exact contracts/helpers, the
ordered dependency/core/source boundary, two cold closed replays with proof
metrics and hashes/RSS/no-DNE/capacity receipts, and a unique false contract
plus every direct Cut-edge mutation. Local syntax and the first three cheap
gates passed. The replay, profiling, and mutation gates remain WMI-only.

Discovery job `172932` was submitted from exact snapshot
`5463565294da6d757356985a0e8d353ad2e0e16ca1b21b99d2aa5cfa6bb5c6f6`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`; it was cancelled after
zero CPU. Cheap body replay then caught and fixed an apply-to-negation error.
First replacement `172970`, from snapshot
`9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
was also cancelled after zero CPU. Corrected job `172978`, from snapshot
`6d32a5ba65b2268dc3fd6c027726a86c5054788bbeb5edacd6d6cbec3373403e`,
is pending discovery only: there is no report, pass, pinned metric receipt, or
admission. At the original orbit checkpoint the runner exposed eight focused
suites and a 71-gate full audit.

### Bounded replay of the 19 Wilson bodies

After the three source corrections, every isolated Wilson candidate body
passes the cheap replay. The nodes/depth measurements are:

| layer | body nodes/depth in source order |
|---|---|
| square one | `182/48` |
| pointwise inverse | `55/22`, `70/28`, `50/21`, `20/12` |
| inverse prefix | `76/29`, `64/25`, `29/16` |
| inverse involution | `44/23`, `49/25`, `80/29`, `55/29`, `31/22`, `83/31` |
| inverse endpoints | `76/23`, `54/23`, `104/32` |
| inverse orbit | `45/26`, `206/40` |

Twelve bounded structural gates pass across prefix, involution, endpoints, and
orbit—three per suite for contract/dependency, hygiene/native/witness, and
graph/core/source isolation. These receipts exercise bodies and bounded
structure only. They do not recursively close dependencies, are not closed-
certificate admission, and admit no theorem.

### Adjacent-pair product fold

The generic product half of Wilson pairing now has two isolated candidates:

| candidate | role | exact direct dependencies |
|---|---|---|
| `beta_product_double_succ_decompose` | decompose a product of length `S(S k)` into its exact `k`-prefix and final two decoded factors | `beta_product_succ_decompose` |
| `beta_adjacent_unit_pairs_product_one` | if each of `m` adjacent decoded pairs has product congruent to one modulo `p`, prove the exact product of the first `m+m` factors is congruent to one | `beta_product_double_succ_decompose`, `beta_product_zero`, `le_succ`, `le_refl`, `mod_eq_refl`, `mod_eq_mul`, `add_succ_left`, `mul_assoc`, `one_mul` |

The second proof is ordinary induction on the pair count. The zero product is
one; the successor step takes the final two factors from the decomposition,
applies the induction hypothesis to the prefix, multiplies the two modular
equalities, and reassociates the exact product. This theorem is deliberately
generic: it does not yet reindex Wilson's nonendpoint inverse orbits into
adjacent positions or restore the fixed endpoint factors.

Bounded replay found two separate missing third-occurrence length rewrites in
successive snapshots. Jobs `172936` and `172943` were therefore cancelled
before start as superseded known-broken jobs; neither supplies evidence. After
both corrections, all five focused gates passed locally in 5.4 seconds,
including two cold passes. Exact metrics are:

| candidate | nodes | depth | distinct objects |
|---|---:|---:|---:|
| `beta_product_double_succ_decompose` | 1,317 | 63 | 844 |
| `beta_adjacent_unit_pairs_product_one` | 4,372 | 64 | 1,290 |

The deterministic graph SHA-256 is
`622496753bd474f9f64d5d3001424d3c4513d43d6a5256022cd5a172167959ec`;
the candidate-source SHA-256 is
`193fe015b32ffde4d93e00720c9fef510a804228e24f19f5cc6c97e8ad5fa724`.
The source is
[`wilson_pair_product_candidate.py`](../../peano-lab/py/peano_lab/library/wilson_pair_product_candidate.py).
Its five gates audit exact contracts and hygienic/canonical helper expansions,
the two-spec dependency/core/source boundary, two cold closed replays with
deterministic hashes and RSS/no-DNE/capacity receipts, and a unique false
contract plus every direct Cut-edge mutation.

Authoritative WMI job `172946` was submitted from exact snapshot
`9d890542b964d40580ad2f8f77fa83455de3b9af0f8ca905a37f6a6ee278e296`
on `cpu_idle` with 1 CPU, 16384 MiB, and `02:00:00`. It is queued/pending.
The complete local pass does not replace the independent WMI admission
receipt; there is no WMI pass or theorem admission yet. At that checkpoint the
runner exposed nine focused suites and a 76-gate full audit.

### Pointwise signed halves and finite omission

The Gauss route now has two isolated candidates:
`odd_upper_remainder_reflection` reflects an upper-half remainder across an odd
modulus, and `gauss_pointwise_signed_half_representative` chooses the lower or
reflected representative pointwise. Their body-only nodes/depth are `125/34`
and `116/38`. All three bounded structural gates pass. Focused job `172964`,
from exact snapshot
`9a59e7a590223d4852f02dde19633b21bfcc4fb92491705d4aade022a116265a`,
is pending with zero CPU. Seven further isolated candidates now encode aligned
magnitude/sign β-prefixes, specialize them to the full half range, project
`AllBits`, and obtain relational `BitCount` existence. Their body nodes/depth
are `73/27`, `133/39`, `164/47`, `70/31`, `33/22`, `35/25`, and `31/26`;
magnitude permutation remains the next boundary.

The finite-omission route contributes eight isolated candidates, in dependency
order:

| candidate | body nodes/depth |
|---|---:|
| `finite_covers_into_or_omits` | `73/22` |
| `finite_inverse_choice_prefix_extend` | `69/27` |
| `finite_inverse_choice_prefix_exists` | `58/23` |
| `finite_inverse_choice_bounded_into` | `21/15` |
| `finite_inverse_choice_injective` | `89/31` |
| `finite_short_cover_impossible` | `149/43` |
| `finite_short_prefix_omits` | `24/16` |
| `finite_bounded_into_injective_omits` | `27/18` |

Its three bounded structural gates pass. Focused job `172965`, from the same
snapshot, is pending with zero CPU. For both suites these local receipts are
body-only or structural; closed recursive replay, profiling, no-DNE/capacity,
mutation, and any receipt-pinned admission remain WMI work. No theorem is
admitted.

The current exact snapshot
`8c9c4ae067b0dc202684e410bee563cd592a67080cb7c9939440ae8b44d4bccd`
adds focused jobs `173015` (`euler-scaled-inverse`), `173016`
(`gauss-signed-prefix`), and `173017` (`wilson-pair-order`). All are pending
with zero CPU. Their remote test-only validations returned exit zero after the
transport changed from `bash -l -s` to `bash -s`; the WMI login-shell logout
hook had overwritten successful validation status. The runner selected 101
gates across 22 test-source modules and exposed 14 focused five-gate suites
plus `full` at that first frozen checkpoint. This is validation/queue
provenance, not proof evidence.

The second frozen checkpoint is exact snapshot
`fd129d34bf4a31a131a28d55bc6a16153984e0d37ac24dcefe7c2735cfb058d1`.
Pending zero-CPU jobs `173021` (`gauss-magnitude-permutation`) and `173022`
(`wilson-pair-order-induction`) bring the live surface to 111 gates across 24
test sources and 16 focused five-gate suites plus `full`.

The Gauss endpoint has eleven body-valid candidates for magnitude range,
collision control, injectivity, predecessor recoding and finite surjectivity:
`39/25`, `48/24`, `96/34`, `169/50`, `626/70`, `157/45`, `31/25`, `87/30`,
`48/20`, `60/31`, `39/21`. Three product-alignment bodies pass at `51/28`,
`127/39`, `72/34`, and two sign-product/power bodies at `35/24`, `259/46`.
Sign-factor recoding, generic pointwise-product recoding, signed product
congruence, prime-product cancellation, and existential witness packaging are
now body-green. The bounded and arbitrary actual-residue classifications are
body-green too; their direct receipts are `597/53` and `547/49` nodes/depth.
The corrected PairOrder follow-on has fifteen body-valid bounded-state/base/
step/terminal-coverage candidates: `95/40`, `19/12`, `69/27`, `90/42`,
`23/19`, `18/14`, `20/16`, `22/18`, `64/19`, `8/8`, `12/9`, `266/44`,
`33/20`, `72/37`, `51/36`. Full PairOrder iteration, successor lift and the
extensional product bridge are body-green. Body receipts and pending jobs are
not recursive closure or admission.

To prioritize focused prerequisite discovery, superseded full jobs `172707`,
`172716`, `172722`, and `172737` are user-held. They were not cancelled; the
reversible holds are to be released after focused results settle.

The source blueprint now covers decoded soundness, extensionality, involution,
injectivity, surjectivity, fixed-index classification, both endpoint entries,
closure of nonendpoint status under inverse mates, and the generic adjacent-
pair product fold. Wilson still requires:

1. WMI validation and distinct receipt-pinned admission of these isolated
   layers;
2. a β-coded reindexing that removes the explicit indices `0` and `k` and
   lays out the stable nonendpoint inverse orbits as adjacent pairs;
3. an explicit prime-two branch, where the two endpoint descriptions
   coincide;
4. application of the generic pair-product certificate, restoration of the
   endpoint factors, and identification with the exact `(p-1)!` range product.

The principal representation blocker is step 2: native PA has no deletion or
filter primitive. The fixed entries, nonendpoint orbit closure, and generic
adjacent-pair fold are now represented, but the removal/reindexing certificate,
prime-two branch, and final product recomposition remain unauthored.

### Authored PairOrder extension

The [PairOrder encoding](pair-order-encoding.md) now supplies nine isolated
dependency-curried bodies for one constructive extension step: append and
reflect two β entries, choose an omitted nonendpoint, extract its unused
inverse mate, preserve orbit closure/nonendpoint range/injectivity, and package
the Wilson choose-and-append result. In source order their nodes/depth are
`63/27`, `115/32`, `113/30`, `138/43`, `34/20`, `167/38`, `63/31`,
`202/36`, and `191/53`.

This is substantial reusable infrastructure, but it is not a complete
PairOrder: pair-count induction, terminal coverage, successor lift and product
transport remain explicit next steps. Job `173017` is the focused recursive/
profile/mutation experiment for the common `8c9c4ae0...` snapshot; pending
zero CPU means no result or admission.

### Generic fixed-point-free involution pairing

For precision, let the following again be documentation-only abbreviations,
all expanded through `At` in a generated statement:

\[
\begin{aligned}
\operatorname{Involution}(r,s,L)
 &:\!\Longleftrightarrow
 \forall i,j.\;i<L\to\operatorname{At}(r,s,i,j)
 \to\operatorname{At}(r,s,j,i),\\
\operatorname{NoFix}(r,s,L)
 &:\!\Longleftrightarrow
 \forall i.\;i<L\to\neg\operatorname{At}(r,s,i,i),\\
\operatorname{MateMod}(m,a,r,s,b,c,L)
 &:\!\Longleftrightarrow
 \forall i,j,x,y.\;i<L\to\operatorname{At}(r,s,i,j)\\
 &\qquad\to\operatorname{At}(b,c,i,x)
 \to\operatorname{At}(b,c,j,y)\to xy\equiv a\pmod m.
\end{aligned}
\]

The reusable combinatorial gate should then have the expanded schema

\[
\begin{aligned}
\forall m,a,h,r,s,b,c,P,A.\;&
 \operatorname{Bounded}(r,s,h+h)
 \to\operatorname{Involution}(r,s,h+h)\\
&\to\operatorname{NoFix}(r,s,h+h)
 \to\operatorname{MateMod}(m,a,r,s,b,c,h+h)\\
&\to\operatorname{Product}(b,c,h+h,P)
 \to\operatorname{Pow}(a,h,A)
 \to P\equiv A\pmod m.
\end{aligned}
\]

Thus, for a prefix of length `h+h`, a bounded decoded involution, no fixed
point, and a factor prefix whose entry at each `i` multiplied by its mate at
`sigma(i)` is congruent to a fixed `a` imply

\[
P\equiv A\pmod m.
\]

All occurrences of “involution”, “no fixed point”, and “mate” must expand to
quantified `At` formulas. A constructive successor proof should select the
mate of the final position, swap the resulting two-cycle to the last two
positions, restrict the involution to the old prefix, use exact product
permutation invariance, and recurse. This is why the already reviewed
swap-last and general product-reindex infrastructure is on the Wilson path.
Merely asserting that the orbits have size two is not a native proof.

For an odd prime `p`, remove the two classified fixed residues `1` and
`p-1`; inversion is fixed-point-free on the remaining even-length prefix and
each mate pair has product congruent to one. Reinsert the fixed factors to
obtain

\[
(p-1)!\equiv p-1\pmod p.
\]

Prime two is a separate direct base case. This yields Wilson only after the
inverse-prefix construction, fixed-point classification, restriction/removal
transport, generic pairing theorem, and final product recomposition all carry
closed certificates.

## Euler, Gauss, Eisenstein, and reciprocity

The mathematical dependency spine is now body-green end to end:

```text
general product reindex
          |
          v
 eight-rung product balance --> Fermat (p-1) --> Fermat (all inputs)
          |
          +-------------------------------+
                                          |
bounded inverse prefix + square-one cases |
          |                               |
          v                               |
fixed-point-free involution pairing       |
          |                               |
          v                               |
        Wilson <--------------------------+
          |
          v
Euler criterion for actual QRes
          |
          v
least/signed half residues --> sign-bit count --> Gauss lemma
                                                   |
division floor codes --> rectangle partition --> Eisenstein parity
                                                   |
                                                   v
                                  sign-free quadratic reciprocity
```

### Euler criterion

The isolated pointwise entrance ladder, its implemented boundary, and its
dedicated WMI-only gates are specified in
[Euler scaled-inverse entrance ladder](euler-scaled-inverse.md). The later
beta-prefix, PairOrder, bounded, and arbitrary endpoints are now body-green.
They remain unadmitted pending recursive replay and mutation review.

The ten scripts construct and uniquely characterize the bounded relation
`x*y == a (mod p)`, prove symmetry and involution, identify fixed points with
square roots, and derive fixed-point freedom under `~QRes`. Their
dependency-curried body nodes/depth are `36/17`, `30/19`, `59/26`, `126/34`,
`74/24`, `31/12`, `28/19`, `38/15`, `17/15`, and `24/15`. Focused job
`173015`, from exact snapshot `8c9c4ae0...`, is pending with zero CPU and has
not produced a closed-replay receipt.

For `p=2h+1` and `p` not dividing `a`, construct the involution on nonzero
residues

\[
x\longmapsto a x^{-1}.
\]

Its fixed points are exactly roots of `x*x ≡ a`. If `QRes(p,a)` holds, a
bounded root and Fermat give `a^h ≡ 1`. If `QRes(p,a)` fails, the involution
has no fixed point; generic pairing identifies the full residue product with
`a^h`, and Wilson identifies that product with `p-1`. The checked constructive
decision theorem for `QRes` then packages the two branches as an equivalence
with actual square-witness status. No Legendre symbol is introduced.

### Parity transport clients

Three further isolated tranches package the parity algebra needed after the
finite sums are constructed. Four sum-classification bodies characterize an
even sum by equal summand parity and an odd sum by opposite summand parity.
Five modulo-two bodies prove `Even(n)` exactly when `n` is congruent to zero,
`Odd(n)` exactly when it is congruent to one, and transport both predicates
across balanced congruence modulo two. Six odd-division bodies prove that an
odd multiplier preserves and reflects parity and, from `n=p*q+r` with odd
`p`, derive

\[
 \operatorname{Even}(n)\leftrightarrow\operatorname{Even}(q+r),\qquad
 \operatorname{Odd}(n)\leftrightarrow\operatorname{Odd}(q+r).
\]

Four odd-half/modulo-four bodies then prove the exact equalities `h=2*a` and
`h=2*a+1` in the two classes and package
`Even(h) iff p=1 mod 4` and `Odd(h) iff p=3 mod 4` under `p=2*h+1`.
All four focused parity modules pass together at `16/16` in 1.24 seconds
under the laptop cap. These are dependency-curried, unregistered and
unadmitted bodies; they do not claim recursive closure.

### Gauss's lemma

The entire mathematical composition is now dependency-curried and body-green.
The authored chain:

1. divides every `a*i`, for `1<=i<=h`, to obtain a bounded nonzero remainder;
2. chooses constructively between its lower magnitude and odd-modulus
   reflection, recording an explicit beta-coded sign bit;
3. proves the magnitude prefix is a permutation of `1,...,h`;
4. recodes sign factors and pointwise products, then folds them to show
   `a^h*h! ≡ (p-1)^e*h!`;
5. proves the half product coprime to `p`, cancels it constructively, and
   packages `a^h ≡ (p-1)^e`; and
6. composes the predecessor-power parity bridge with Euler's criterion.

For the canonical bounded input, `bounded_gauss_lemma_complete` assumes
`p=2*h+1`, `Prime(p)`, `0<a<p`, and `HalfRange(b,c,h)`. It constructs a
reflection count `e`, retains the signed prefix and exact `BitCount(e)`, and
proves

\[
 \operatorname{QRes}(p,a)\leftrightarrow\operatorname{Even}(e),\qquad
 \neg\operatorname{QRes}(p,a)\leftrightarrow\operatorname{Odd}(e).
\]

Its direct receipt is 11 dependencies, 204 commands, `597/53` nodes/depth,
559 objects, 596 edges, and 38 reused objects. The
`arbitrary_gauss_lemma_complete` wrapper replaces `0<a<p` by `p` not dividing
`a` and invokes the arbitrary-representative Euler criterion; its direct
receipt is 9 dependencies, 188 commands, `547/49` nodes/depth, 513 objects,
546 edges, and 34 reused objects. The bounded and arbitrary focused audits
pass together at `9/9` in 13.64 seconds.

The arbitrary script is fail-closed source-shared from the audited bounded
classification tail and then replayed independently against its own expanded
contract. Neither candidate is registered, recursively closed, or admitted.
The remaining Gauss work is WMI recursive replay, mutations, and a separate
receipt-pinned admission—not another mathematical bridge to `QRes`.

The first supplementary law follows by specializing `a` to the predecessor
of `p` and using the already checked predecessor-power parity bridge.

### Eisenstein and quadratic reciprocity

For distinct odd primes `p=2h+1` and `q=2k+1`, division witnesses must encode
the two floor sequences

\[
\left\lfloor\frac{qi}{p}\right\rfloor\quad(1\le i\le h),
\qquad
\left\lfloor\frac{pj}{q}\right\rfloor\quad(1\le j\le k).
\]

The body-green combinatorial chain partitions the `h*k` lattice rectangle
around `p*y=q*x`; distinct primality rules out diagonal points. A
provenance-carrying transposed-column induction now proves the semantic
Fubini identity, and the exact quotient wrapper concludes

\[
  Q+U=h k
\]

with a `145/68` nodes/depth receipt. The Gauss--Eisenstein pointwise theorem
(`250/61`, statement hash prefix `84b039`) and exact finite-sum permutation/
cancellation ladder prove `Q congruent e (mod 2)` in each orientation while
retaining the beta data. The pointwise plus sum suites pass `12/12` in 17.47
seconds.

One-orientation and two-prime existential data packages have direct receipts
`5/102/139/67` and `4/150/222/77` in
dependencies/commands/nodes/depth order. Constructive parity truth tables then
feed the exact sign-free endpoints:

- same residue status when at least one prime is `1 mod 4`;
- exactly one residue status when both primes are `3 mod 4`.

The same and opposite bodies are `2/46/73/33` each; the combined endpoint is
`3/65/113/35`. It constructs the two-prime data once and applies both
conditional clients directly. Their downstream integration passes `20/20`
in 27.25 seconds.
Every one of these results remains dependency-curried, unregistered and
unadmitted, so this is not yet a public theorem claim.

The supplementary law for two follows only after the main reciprocity
endpoint; Jacobi symbols remain a separately scoped extension.

## Constructive and trust policy

Every theorem in this spine must satisfy all of the following:

- the kernel language remains `0`, `S`, `+`, `*`, equality, first-order
  intuitionistic logic, and induction;
- `Range`, `Product`, `Pow`, `Coprime`, maps, involutions, floor sequences,
  signs, and counts are hygienic authoring expansions, never trusted syntax;
- certificates contain no `DNE`; every split is supplied by a checked finite,
  equality, order, remainder, divisibility, parity, or residue decision;
- existential witnesses are constructed explicitly by induction and beta
  recoding; no external function, list, finite set, quotient ring, or choice
  operator is imported;
- extensional decoded-entry relations, not raw beta-code equality, express
  equality of finite data;
- candidate factories remain isolated until every declared dependency is
  earlier in the ladder and the exact closed target checks from the empty
  context;
- each admission gets two cold deterministic replays, exact statement and
  dependency hashes, no-`DNE` inspection, nearby false-contract rejection,
  Cut/dependency mutation rejection, and independent kernel checking;
- the laptop runs only static gates and dependency-curried body preflight
  under a hard 60-second cap; recursive closure, profiles, mutations and book
  builds remain WMI-only;
- only after admission are the registry, deterministic snapshot, catalog,
  vault, theorem atlas, campaign chapter, memory, and journal regenerated.

## Capacity decision

No capacity increase is warranted for this tranche.

The current policy remains:

| resource | bound |
|---|---:|
| interactive expanded source | 8,192 characters |
| structural certificate occurrences | 500,000 |
| distinct in-memory proof objects | 100,000 |
| proof depth | 256 |

The largest of the eight prototype statements is 4,790 characters, leaving
substantial source headroom. The current checked global maximum remains the
FTA certificate at 73,767 structural occurrences, 8,701 distinct objects,
and depth 99; the finite-pigeonhole and swap-product gates also fit the
existing policy. None of those measurements predicts a need to raise a cap.

Each new certificate must be measured rather than estimated. If an Euler,
Gauss, pairing, or reciprocity composition approaches the live limits, first
split the mathematics into reusable checked rungs and preserve immutable Cut
sharing. If the final endpoint still fails a measured gate, pause for the
reviewed self-contained proof-DAG design. Raising a limit in anticipation,
trusting a theorem name or hash, or bypassing the full independent kernel
check is not an acceptable response.

## Recommended engineering order

1. Finish and admit `beta_product_reindex_fixed_last` and
   `beta_product_permutation_invariant` under the current limits.
2. Implement the eight Fermat theorems in the order shown, with theorem 4
   allowed to proceed in parallel with the first three.
3. Admit the predecessor-exponent Fermat theorem, then the all-input wrapper.
4. Validate and admit `prime_bounded_square_one_cases`, the seven isolated
   inverse-index/prefix candidates, the six extensional involution candidates,
   and the three explicit endpoint candidates.
5. Validate the nine PairOrder extension and fifteen bounded-state/coverage
   bodies, then add full pair-count iteration, successor lift and product
   transport before completing Wilson.
6. Validate the ten pointwise Euler scaled-inverse bodies, instantiate the
   completed generic PairOrder/fold, and prove Euler's criterion for the
   existing expanded `QRes` relation.
7. Recursively validate and mutate the complete signed-prefix through
   arbitrary-Gauss graph on WMI, then admit it only through a distinct pinned
   replay before deriving the first supplementary law.
8. Recursively validate, mutate and capacity-profile the completed Fubini,
   quotient-identity, Gauss--Eisenstein parity, data-package, and exact QR
   graph on WMI; admit only through a distinct pinned replay.

This order keeps the Fermat tranche small and useful on its own while ensuring
that every later theorem rests on general finite arithmetic infrastructure
rather than on a reciprocity-specific shortcut.
