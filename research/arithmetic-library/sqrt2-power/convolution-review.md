# CV001: universal natural convolution vanishing

The [HA observation](observations/shared-wave-convolution-vanishing-v3/report.json)
and [fresh Lean observation](observations/fresh-lean-convolution-vanishing-v1/report.json)
accept the same 28-node, 1,400-body-node certificate:
`93d3871e7c7f06fc5974b61bec48616a7a7f13e6f919bf7dbf34570624e918b6`.
The exact target AST is
`b5ca16c60cf9aff317a93603448843e717d17228380fb7c1a1287e31f12e5e22`.
This does not close IR079 or irrationality.

## Exact named statement

```text
forall ab ac L bb bc M r s i db dc n.
  (forall j a. Lt(j,r) -> BetaZeroExtend(ab,ac,L,j,a) -> a=0) ->
  (forall j b. Lt(j,s) -> BetaZeroExtend(bb,bc,M,j,b) -> b=0) ->
  Lt(i,r+s) ->
  PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,i,db,dc,S i) ->
  Sum(db,dc,S i,n) -> n=0
```

All relations are existing conservative definitions. The first table vanishes
below index `r`, the second below `s`. The conclusion concerns an actual
beta-coded diagonal and actual summation trace; neither is merely a desired
convolution value supplied as an unchecked assertion.

For every diagonal term choose its witnessed complementary index `h`, with
`j+h=i`, and decoded values `a,b`. If both `r<=j` and `s<=h`, then
`r+s<=j+h=i`, contradicting `i<r+s`. Constructive order splitting therefore
gives `j<r` or `h<s`. The corresponding decoded value is zero, hence so is
their product. Thus every entry of the diagonal table is zero. The actual
`beta_repeat_sum_exact` proof gives its sum as `(S i)*0=0`.

The complete reused ancestor cone has 27 nodes and 1,146 ordinary proof nodes.
It includes the actual order laws, zero multiplication, and finite-repeat sum
proofs, not names or receipts masquerading as premises.

## Two recorded failures and the confirmed repair

Attempt v1 stopped on a concrete rewrite mismatch: a beta-entry formula contains
the value twice, whereas the existing rewrite tactic changes one occurrence.
The second rewrite repaired that mismatch, but attempt v2 then failed the
original kernel check. Neither attempt produced accepted evidence.

The [bounded diagnostic](observations/shared-wave-convolution-diagnostic-v1.json)
profiled the unmodified checker. It observed an `ExistsElim`-headed equality
inserted into `EqSubst` after local-lemma compilation had removed its type
annotation. The checker requires that equation's type to be synthesizable;
the rejection was correct for those certificate bytes.

The producer now wraps each actual local lemma `L:P` in the ordinary typed
identity proof `Cut(P,P,L,Hyp(0))` before the existing compiler runs. It preserves
all eleven propositions and proof bodies. The original Cut rule checks `L`
against `P`; the annotation does not supply an axiom or validate a false lemma.
All 28 final bodies still pass the original kernel and fresh Lean.

The [tests](observations/shared-wave-convolution-validation-v1.json) reproduce
the unannotated rejection and annotated acceptance, and reject a forged
annotation lemma. They also check exact inherited bodies, changed boundaries,
missing zero-prefix premises, altered dependencies, and hostile archive bytes.
Concrete beta-trace counterexamples show why `i<=r+s` is insufficient and why
both zero-prefix hypotheses matter. These host models are not proof receipts.

## Next bridge, not silently assumed

The existing polynomial infrastructure uses raw highest-degree-first table
indices. CV001 is an index-sum theorem: `j+h=i`. It does not identify those
indices with ascending formal-series degrees or provide signed-rational
coefficients, power tables, derivatives, or a chain rule.

Next, define the ascending series representation explicitly, prove the
coefficient-order bridge and rational operation transport, then lift vanishing
by induction through actual finite power-table execution. Only that can justify
truncating formal `exp(A)` to finitely many positive-degree powers before
proving IR079's coefficient recurrence and IR081's analytic error bounds.
