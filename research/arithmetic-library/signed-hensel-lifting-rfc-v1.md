# Full integer-coefficient simple-root Hensel lifting

This additive candidate closes the mathematical coefficient-domain gap in
G095 without changing the original Heyting-arithmetic signature or kernel.
Its proof dependencies are the unchanged Alpha v26 catalogue and the separate
19-row `hensel_prime_power_candidate.py` natural-polynomial core.

## Representation and exact statements

A polynomial over the integers is represented by two arbitrary beta-coded
natural coefficient prefixes of common length, interpreted by their
difference. No nonnegative-coefficient restriction, sign-normalization premise,
or supplied polynomial evaluator is imposed. Both component values and their
formal derivatives are actual coupled Horner traces.

`SignedDerivativeUnit(p,dp,dn)` means an actual `u<p` satisfies the balanced
congruence `dp*u ≡ 1+dn*u (mod p)`. For prime `p` this is precisely an inverse
of the integer derivative `dp-dn`, not an extra lifting/correction oracle.

`SignedSimpleHornerRoot(pb,pc,nb,nc,a,l,m,p)` existentially packages those exact
value/derivative traces, the signed root equation modulo `m`, and the bounded
derivative inverse modulo `p`.

`CanonicalSignedHornerLift(pb,pc,nb,nc,l,m,a,M,r)` means `r<M`,
`r≡a (mod m)`, and the actual signed polynomial vanishes modulo `M` at `r`.

The final G095 theorem
`integer_polynomial_prime_power_hensel_lift_exists_unique` states:

```text
forall pb pc nb nc a l p k m.
  Prime(p) -> k != 0 -> Pow(p,k,m) ->
  SignedSimpleHornerRoot(pb,pc,nb,nc,a,l,m,p) ->
  exists M. Pow(p,S k,M) /\
    exists r. CanonicalSignedHornerLift(pb,pc,nb,nc,l,m,a,M,r) /\
      forall z. CanonicalSignedHornerLift(pb,pc,nb,nc,l,m,a,M,z) -> z=r.
```

The iteration endpoint replaces `S k` by `k+j` for arbitrary natural `j`,
including zero. It constructs an actual higher-power witness and proves
uniqueness over **all** roots in the entire original residue class, not just
among a preselected correction sequence. Input `a` has no upper bound.
`beta_signed_horner_lift_preserves_simplicity` constructs the lifted values,
derivatives, and a retained bounded inverse. Thus existence, uniqueness,
simplicity preservation, and arbitrary finite iteration are all proved.

## Constructive signed-to-natural bridge

For a desired nonzero final modulus `M=S h`, construct actual coefficient
codes for `G = Fplus + h*Fminus` using the existing constant-prefix,
pointwise-product, and pointwise-addition constructors.

Induction on coefficient length proves both exact identities
`G(a)=Fplus(a)+h*Fminus(a)` and
`G'(a)=Fplus'(a)+h*Fminus'(a)`. Consequently:

```text
G(a)  + Fminus(a)  = Fplus(a)  + M*Fminus(a)
G'(a) + Fminus'(a) = Fplus'(a) + M*Fminus'(a).
```

Balanced congruence and cancellation prove signed/natural root equivalence
in **both** directions modulo every divisor of `M`. The signed derivative
inverse proves the actual natural derivative coprime to `p`. Apply the already
proved natural arbitrary-step induction at this final `M`, then transport
existence and all-root uniqueness back. The recoded polynomial is an actual
finite object, never an assumed coefficient map or a new ring primitive.

## Definition DAG

Six new conservative surfaces are supplied, without allocating global IDs:

- `HornerCoefficientBlend` uses the existing beta-entry and strict-bound
  relations.
- `SignedHornerValueDerivative` uses the two existing Horner derivative pairs.
- `SignedDerivativeUnit` uses strict bound and balanced congruence.
- `SignedHornerRoot` uses two existing Horner value relations and congruence.
- `CanonicalSignedHornerLift` uses the signed root, bound, and old congruence.
- `SignedSimpleHornerRoot` uses actual signed value/derivative, congruence, and
  signed derivative unit.

All public helpers enforce distinct formal arguments, reserved-name and
capture checks, and tag-independent exact parsed AST equivalence. These are
untrusted authoring abbreviations, not kernel predicate symbols.

## Exact checked evidence and remaining release gate

All 17 signed dependency-curried bodies pass the unchanged original kernel:
74 direct edges, 1,295 tactic commands, 2,125 proof-node occurrences, maximum
depth70. Together with the natural core: 36 rows, 177 direct edges, 2,487
commands, 4,072 proof-node occurrences, maximum depth71.

The focused natural-core suite passes 90 tests and the signed suite passes
162 tests. They cover exact statement and metric pins, all original-kernel
body checks, fail-closed forged proofs, conservative-definition hygiene,
negative coefficients, noncanonical signed pairs, and unrestricted seed
representatives.

Signed ordered names SHA-256:
`1b358b5ee001b5d0db41a64f881da235fe7550031645c5509d910791a166b582`.

Full one-step G095 statement SHA-256:
`fbc1f6811c164ad5a2a9a52ed6788dd1e9b1e324b2a6cdc057043f318dbba19a`.

Full iterated statement SHA-256:
`6e08e64dfacb14e848089a7809fad3560041c600bc923ab665803b288868b28a`.

The parent catalogue is pinned to SHA-256
`969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534`.
Tests reconstruct dependency hypotheses from this immutable catalogue to keep
memory bounded. Python numerical examples, including genuinely negative
coefficients and noncanonical signed pairs, are explicitly only regressions.

These checks do **not** themselves admit Alpha rows, provide a dependency-closed
certificate, or claim independent Lean acceptance. The integration owner must
reconstruct the real proof dependency cone and pass original-kernel and
compiled Lean closure before changing published milestone status.

No historical proof source, kernel, checker, edition, release artifact,
website, or deployment has been modified by this candidate.
