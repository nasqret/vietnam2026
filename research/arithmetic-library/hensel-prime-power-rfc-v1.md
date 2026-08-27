# Canonical and iterated simple-root Hensel lifting

This is an additive, non-admitting candidate over the unchanged original
intuitionistic Peano kernel. The parent is the sealed Alpha v26 catalogue
with 2,138 checked-use theorems and unchanged Stable432. Its SHA-256 is
`969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534`.

## Exact scope and the G095 boundary

The natural-coefficient core uses the established beta-coded `Horner` and
`HornerDerivative` relations, not an external polynomial evaluator. It proves
canonical existence, uniqueness among **all** roots in the old residue class,
preservation of a genuinely evaluated simple derivative, and arbitrary finite
iteration. The source input is unrestricted: no hidden `a < p^k` hypothesis.

The wider G095 blueprint also promises integer coefficients. The natural core
alone must not close that wider claim. The additive signed-coefficient bridge
is separate work: encode `F = Fplus - Fminus`, use the natural polynomial
`G = Fplus + (M-1)*Fminus` at each desired nonzero final modulus `M`, prove
value/derivative linearity and balanced modular transport, then apply this core.
No redefinition of the blueprint's coefficient domain is authorized.

## Main mathematical interfaces

The following are notation only, with exact conservative first-order expansions
in `hensel_prime_power_candidate.py`:

- `HornerRootModulo(b,c,a,l,m)` supplies an actual beta-coded Horner value
  congruent to zero modulo `m`.
- `SimpleHornerRoot(b,c,a,l,m,p)` additionally supplies the actual derivative
  and proves that derivative coprime to `p`.
- `CanonicalHornerLift(b,c,l,m,a,M,r)` states `r<M`, `r≡a (mod m)`, and an
  actual polynomial root at `r` modulo `M`.

For arbitrary nonzero `p,m`, with `m=p*s`, an actual value/derivative pair
`f(a)=n, f'(a)=d`, `n≡0 (mod m)`, and `Coprime(d,p)`, the core constructs a
unique `CanonicalHornerLift(...,m,a,p*m,r)`. Thus it is stronger than the
prime-base special case, without asking for a correction or modular inverse
as an extra premise.

For every actual `Pow(p,j,q)`, HA induction constructs the unique canonical
root modulo `m*q` in the original class modulo `m`. Iteration zero is included.
Starting at actual `Pow(p,k,m)` with `k≠0`, the final root theorem constructs
an actual `Pow(p,k+j,M)` witness and the unique canonical lift modulo `M`.
No power, sequence, ring, or choice oracle is assumed.

## Proof dependency structure

1. Normalize arbitrary inputs by constructive Euclidean division; transport
   polynomial values and derivative coprimality.
2. Decompose every bounded candidate lift as the canonical old representative
   plus `m*t`, with a proved digit bound `t<p`.
3. Use the original Taylor identity to prove the missing converse: every root
   lift satisfies the actual linear correction equation.
4. Apply the already checked correction uniqueness theorem, so uniqueness is
   over all candidate roots, not merely the algorithm's selected digit.
5. Transport simplicity through genuine derivative congruence.
6. Induct on the number of lifting steps. Normalize an arbitrary competing
   final root to the previous level, apply induction uniqueness, then one-step
   uniqueness. Finally combine actual power witnesses by `pow_add`.

## Current checked evidence

All 19 natural-core dependency-curried bodies are accepted by the unchanged
original kernel: 103 direct dependency edges, 1,192 authored tactic commands,
1,947 proof-node occurrences, maximum proof depth71. Ordered names SHA-256:
`0d83fabda9745836a771e5424e8be9ba1c9ac1d2d82b66d9301a08b54f4342a3`.

The exact unrestricted one-step root statement SHA-256 is
`0e2015d8ecd34aa6fb39d8f478e7c20f1dd878a6daf3915d3f1faf86349800a1`.
The higher-exponent root statement SHA-256 is
`22300cdb65e3bddb402c0e4a95b2bb487823919e489f02ee25fd7d5cb22c279d`.

These are candidate-body checks, not a new Alpha admission, a complete closed
bundle receipt, or independent Lean acceptance. Integration must reconstruct
the real dependency cone and pass original-kernel and compiled Lean closure.
To keep authoring memory bounded, focused tests reconstruct exact dependency
statements from the pinned immutable catalogue, one checking process at a time.

No historical source, kernel, trusted checker, edition, publication surface,
or release artifact has been changed for this candidate.
