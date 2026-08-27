# Signed integer floor division over unchanged HA

This additive substrate supports both the Gaussian (G081) and Eisenstein
(G084) Euclidean constructions. It does not itself assert either ring theorem.
The parent is the immutable Alpha v27 catalogue
`481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6`:
2,560 checked-use rows, with Stable unchanged at 432.

## Exact domain and definitions

The pair `(xp,xn)` represents the integer `xp−xn`, without requiring a
normalized representative. The new conservative six-argument graph is

```
SignedIntegerFloor(xp,xn,m,qp,qn,r) :=
  xp + m*qn = (xn + m*qp) + r ∧ ∃h. h + S(r) = m.
```

Thus the represented quotient is `qp−qn`, and `r` is a nonnegative remainder
strictly below `m`. All six supplied terms are parsed as actual Peano `Term`
objects in an explicit finite context before rendering. The gap binder is
capture-checked; malformed terms, unknown variables and invalid contexts fail
closed. No subtraction, integer division, floor function or integer type is a
kernel primitive.

`SignedCodeFloor(input,m,quotient,r)` existentially supplies the two normalized
decodings using the **existing** `SignedDecode` relation and the graph above.
Even code `2p` represents `p`; odd code `2k+1` represents `−(k+1)`. Canonical
quotient construction uses the existing `SignedBalance` totality theorem.

## Actual constructive algorithm

For arbitrary `xp,xn` and `m≠0`, construct `h` with `m=S h`. Divide the natural
number `xp+h*xn` by `m`, obtaining `xp+h*xn=m*q+r` with `r<m`. Choose `qp=q`
and `qn=xn`. The identity

```
xp + m*xn = (xn + m*q) + r
```

is proved by ordinary successor multiplication and additive rearrangements.
This single natural division works for positive, negative, and zero represented
inputs and for the unit divisor. It does not assume any quotient or correction
witness. Normalize the quotient only afterwards using the historic signed
encoding; a proved representative-transport lemma preserves the same remainder.

## Theorem DAG and verification boundary

In dependency order the five new rows are:

1. `natural_mul_swap_right_tail`: a small shared checked multiplication
   permutation, needed by bounded polynomial calculations in both rings.
2. `signed_integer_floor_exists`: unrestricted signed-pair floor totality.
3. `signed_integer_floor_quotient_transport`: invariance under a genuine equal
   integer representative of the quotient.
4. `signed_integer_canonical_floor_exists`: an actual canonical quotient code,
   its normalized decoder witnesses, and the strict remainder.
5. `signed_code_floor_exists`: totality for every canonical signed input code.

There are 17 declared dependency edges and 129 ordinary tactic commands. The
dependency-curried bodies pass the original intuitionistic kernel: 349 proof
nodes in total, maximum depth 49. Neither Gaussian nor Eisenstein facts occur
among their dependencies. No `ring`, `use`, `admit`, classical axiom, new trusted
tactic, or resource-cap increase is used.

The dedicated tests check the exact inventory and proof metrics, absence of
cycles and ring-specific prerequisites, rejection of forged proofs and a
missing divisor guard, independent primitive-AST meaning of compound-term
definitions, hygienic binders and contexts, and the actual one-division
algorithm on 1,584 signed-pair/divisor examples.

These checks are **body checks**, not admission certificates: the pinned
catalogue supplies only dependency statements during this bounded pass.
Dependency-closed original-kernel packaging, independent compiled Lean
verification, Alpha promotion and publication belong to the integrating
release. This module changes no old theorem, kernel, edition, or public site.
