# Finite-list multinomial Kummer theorem

This is an additive, non-admitting candidate over the unchanged intuitionistic
Peano kernel. Its parent is the immutable Alpha-v26 catalogue, with 2,138
checked-use theorems and unchanged Stable432. The catalogue SHA-256 is
`969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534`.

## Exact G035 interface

The principal theorem has exactly two premises:

```
forall p b c l n z.
  Prime(p) -> Multinomial(b,c,l,n,z) ->
  exists e. PowerValuation(p,z,e) /\ CarryCountMany(p,b,c,l,e).
```

`Multinomial` is the blueprint's iterated-binomial definition, with the opaque
list parameter made explicit as a beta code `(b,c)` and its length `l`.
It supplies an actual running sum beginning at zero, actual binomial factors
`Choose(prefix + part, prefix, factor)`, and their actual finite product.
There is no factorial-ratio oracle. Totality and nonzeroness are proved, with
the empty list giving total zero and coefficient one. Zero-valued parts and
one-element lists require no exceptional hypotheses.

`CarryCountMany` is independent of multinomial coefficients and valuations.
It witnesses the running addition of the parts, the existing exact quotient-
column carry relation for every binary addition, and the sum of those carry
counts. The binary carry relation is AST-identical to the conclusion of the
previous full binary Kummer theorem. It is not an equation defining the carry
count to be a valuation. This is a sequential-addition carry grid; a separate
formal equivalence with every possible simultaneous-column encoding or an
order-invariance theorem is not claimed here.

The existing bounded `PowerValuation` relation is reused without modification.
It is defined even at value zero, but product additivity explicitly requires
nonzero factors, and multinomial nonzeroness is proved before that theorem is
applied. No statement identifies the bounded value at zero with an ordinary
unbounded prime-adic valuation.

## Conservative definition DAG

Six public, hygienic builders expose exact first-order expansions:

1. `beta_valuation_prefix`: beta entries paired with actual prime valuations.
2. `multinomial_binomial_prefix`: the running sums' actual binomial factors.
3. `multinomial`: a sum trace, binomial prefix, and product witness.
4. `binary_column_carry_count`: existing quotient prefixes, carry bits, count.
5. `multinomial_carry_prefix`: actual carries for successive running sums.
6. `carry_count_many`: a sum trace, carry prefix, and sum of carry counts.

No reviewed definition identifier is reassigned. The planned opaque-list
signatures need an explicit reviewed binding to these beta-code interfaces;
the five-argument definitions must not be presented as arity-compatible with
the old three-argument placeholders. The proof DAG and this notation DAG
remain separate.

## Constructive proof route

First, beta extension constructs a table of actual valuations. Induction on
the finite product length proves that the valuation of a nonzero product is
the sum of its factor valuations. This uses the already checked binary
valuation-additivity theorem, not an assumed finite-product identity.

Second, beta extension constructs binomial factors along an actual running
sum. Binomial totality supplies each factor, and positivity proves every
factor nonzero. Finite-product totality then supplies the multinomial value.

Finally, apply the full binary Kummer theorem to each actual binomial factor.
The valuation table becomes a table of witnessed binary carry counts. The
proved finite-product valuation identity supplies their total and the final
existential valuation/carry witness. Empty-list value and carry endpoints
are separately derived from the same definitions.

## Candidate evidence and admission boundary

All 19 ordinary dependency-curried bodies pass the original kernel. They
have 55 direct dependency edges, 841 authored tactic commands, and no body
larger than 375 proof nodes or depth64. Ordered names SHA-256:
`7733a3cb6bbd7327a9d443eea98082fd75d3556d69467f856fee8d48894f73ce`.
The full root statement SHA-256 is
`f69d92599b4eaa9e893e3a4c0e8ab998234bbce6223fbbde949433c1ee7c8266`.

The focused suite passes 144 tests: all bodies, altered conclusions, truncated
proofs, every missing dependency, exact root-premise shape, exact binary carry
expansion, hygienic renaming and capture/injection rejection, and numerical
boundary examples including empty lists, zeros, and repeated carries.
Numerical comparisons with factorial ratios and simultaneous carry counts
are tests, not replacements for formal theorems about those representations.

For memory-bounded authoring, tests reconstruct dependency hypotheses from
the pinned parent catalogue. A catalogue hash is not proof authority. These
receipts are not an Alpha admission or a closed-bundle/Lean receipt: integration
must reconstruct and independently verify the real dependency-closed bodies.
No kernel, historical release, Stable inventory, or remote site is changed.
