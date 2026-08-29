# General finite signed Dirichlet inverses toward G009

Date: 2026-08-29. Starting commit remains
`cef66ddf52658ee9f878b9a81ff8eca19f991485`; the completed, uncommitted
113-theorem convolution/Möbius tranche is an additional immutable input.
This request authorizes new local proofs and readers, not commits, Alpha/Stable
promotion, deployment, history changes or larger proof limits.

## Exact target and construction boundary

Use actual beta-coded signed arithmetic tables and the previously proved
convolution graph. Signed code 2 is +1 and code 1 is -1. The proposed
conservative abbreviations are:

```text
SignedUnit(u) := u=2 ∨ u=1.
DirichletUnitAtOne(F) := ArithAt(F,1,2) ∨ ArithAt(F,1,1).
DirichletInverse(N,F,G) :=
  ∃E. KroneckerDeltaTable(N,E) ∧
      (DirichletTable(N,F,G,E) ∧ DirichletTable(N,G,F,E)).
```

The inverse definition contains actual table and convolution witnesses, never
the unit criterion to be proved. The principal target is:

```text
∀N F. ArithTable(N,F) →
  ((∃G. DirichletInverse(N,F,G)) ↔
   (N=0 ∨ DirichletUnitAtOne(F))).
```

Also construct an inverse with any prescribed zeroth value, prove uniqueness
of positive represented values, and prove compatibility across smaller
prefixes. Do not assert equality of arbitrary table codes or of values at zero.
At N=0 actual witnesses are still required, but there is no condition at one.

The construction first proves the stronger triangular equation solver:

```text
∀N F T u w. ArithTable(N,F) → ArithTable(N,T) →
  ArithAt(F,1,u) → SignedUnit(u) →
  ∃G. DirichletTable(N,G,F,T) ∧ ArithAt(G,0,w).
```

At n=S k, isolate the last divisor d=n in G*F. Construct
`DirichletPrefix(G,F,n,k,M)` and a signed fold of length n, whose remainder
uses only d<n. Solve the actual signed equation `r+x*u=e`, append x as G(n),
transport the restricted prefix, and construct the last entry with quotient
one. The resulting full fold has length S n. Constructing a full inclusive
prefix through n before solving would include the old arbitrary G(n), which
is not the required remainder. Existing full-prefix input extensionality does
not preserve a newly changed last index; a restricted transport proof is needed.

## Ordered implementation layers

1. **Signed units.** Classify all actual signed products equal to one; construct
   and verify the affine solver for a unit coefficient, including negative
   units. Keep all decoded arithmetic, multiplication and addition witnesses.
2. **Triangular convolution.** Prove restricted first-input prefix transport,
   preservation of earlier convolutions under input extension, actual last-term
   append, and convolution at one. Reuse genuine quotient and bound lemmas.
3. **Constructed inverses.** Inductively construct solutions for every target
   table, specialize to a constructed delta table, prove both inverse laws,
   necessity/sufficiency with the N=0 boundary, positive uniqueness and prefix
   compatibility. No inverse or finite-choice oracle is assumed.
4. **Complete evidence.** Check every new body and exact statement, include and
   check the complete dependency cones with original HA and the unchanged
   independently compiled Lean verifier, and separately replay the principal
   ordinary empty-context certificates. Reject false targets, missing/poisoned
   dependencies, wrong returned specifications, partial bundles and stale data.
5. **Definitions and readers.** Following the constructive-proof-explorer
   skill, preserve all 369 definition identities and expand the genuine DAG
   conservatively from ND0313. Reuse the original Quadratic Reciprocity layout
   and five assets. Provide exact/defined readers, three distinct edge kinds,
   proof-only paths and navigation to all four inherited research generations.

## Evidence and resource policy

The exact novelty basis is 3,756 statements: Alpha v30's 3,222 plus the four
research generations 170, 126, 125 and 113. Their 534 research statements are
inherited proof data, not new results, new Alpha members or proof assumptions.
The first two research generations are published; the next two are local.
The old 113-theorem receipt and 424-file explorer remain byte-identical.

The immutable 113 audit SHA-256 is
`6c138b44b94c15a72416c312130bacb37a7ccce1d70e5261d5e497fc7ae18b51`;
its explorer manifest is
`9755ca72a5e0341e6f42aa8f05253009d36e0950678a917a400961201b36f921`.
These hashes identify preserved outputs; saved success reports are never
inputs to proof acceptance. Reused seeds must contain genuine, freshly
HA-checked bodies, including any unused seed nodes.

Every proof/authoring window keeps CPU (170,175) seconds, wall 180 seconds and
observed RSS 1,536 MiB. Use separately bounded jobs and a live, source-bound
render handoff. Avoid repeating presentation-only support selection per root
in the controller or renderer; every fresh principal proof worker still
authenticates and selects its actual dependency cone. Never reuse an earlier
success receipt as authority. Scheduling multiple windows
does not increase any individual proof bound. No kernel, replay, catalog,
historical source, renderer or service setting is changed.

Alpha remains v30 with 3,222 checked-use entries; Stable remains 432. G007's
finite signed Möbius inversion remains proved locally. **G009 is still broader
than the present inverse criterion:** general multiplicative-function closure
requires its own actual coprime-divisor reindexing/Fubini proofs. General
prime-power fields G091 also remain open.

## Outcome

Mathematical authoring is complete: 9 signed-unit, 10 triangular-convolution
and 21 inverse results, with 132 direct prerequisites and 1,712 tactic commands.
All 40 original HA conditional bodies and all 716 distinct mathematical tests
pass. The complete 40-row exact-AST novelty comparison against 3,756 earlier
statements also passes. Independent review confirms the genuine triangular
construction, both signed units, the N=0 boundary, and positive-only uniqueness.

All three complete dependency-closed original HA bundles and their same-byte
independent compiled-Lean checks now pass, with 71, 219 and 401 nodes including
their packaging roots. All nine ordinary principal certificates, 192 registry
tests and 154 audit-protocol tests pass. The final fresh thirteen-job audit and
all 72 same-run explorer tests also pass. The complete tranche has 1,555
distinct new passing test cases and 173 canonical local reader files (144
HTML), with the original proof and render limits unchanged.

All five implementation layers are complete for this local inverse tranche.
The [reader library](../book/_static/constructive-dirichlet-inverse-explorer/index.html)
and [inverse graph](../book/_static/constructive-dirichlet-inverse-explorer/dirichlet-inverses/explorer/defined/graph.html)
are ready. Exact bundle, audit and reader identities, all certificate counts,
resource measurements, unchanged historical outputs and the unrelated
pre-existing site-test failure are documented in
[the verification record](../research/arithmetic-library/dirichlet-inverse-verification-receipt-2026-08-29.md).
Full G009 still requires multiplicative-function closure. No commit, admission
or deployment was performed.
