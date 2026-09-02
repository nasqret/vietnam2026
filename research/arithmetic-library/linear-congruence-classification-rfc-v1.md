# Exact linear congruence classes and boundary contracts

This additive Alpha-v34 family contains eleven new ordinary intuitionistic HA
scripts and the unchanged `fermat_little_all_inputs` specification extracted
from its original canonical factory. Stable remains the separate 432-entry
default. Source syntax and saved observations never grant proof authority.

For nonzero modulus `m`, an actual gcd `IsGCD(g,a,m)` and explicit cofactor
equations `a=g*A` and `m=g*M`, the cancellation theorem proves
`ModEq(m,a*x,a*y)` if and only if `ModEq(M,x,y)`. Cofactor coprimality and
positivity are derived, not assumed as extra oracles. Given `g | b`, the
standalone enumeration theorem constructs an actual `r<M` satisfying
`a*r ≡ b (mod m)` and proves, for every natural `x`,

```text
x<m and a*x≡b (mod m)  iff  exists t<g. x=r+M*t.
```

The progression is injective. This is an explicit bijection with the natural
interval below `g`, not an assumed cardinality or a claim of beta-coded list
enumeration. A separate theorem characterizes all unbounded solutions from
any reference solution. Earlier constructive gcd and linear-solvability
theorems provide the required witnesses.

At modulus zero, congruence is equality: a nonzero coefficient has at most
one solution, and coefficient zero has every solution exactly when the target
is zero. No solution below a zero bound is asserted. At modulus one the
unique bounded solution is zero for every coefficient and target. Fermat's
endpoint includes all natural bases, including zero and prime multiples.

The source has 12 rows, 61 declared dependency edges and 658 native commands.
The complete artifact has 202 inherited theorem bodies, 12 new bodies and one
packaging body: 215 nodes, 647 edges and 13,079 body occurrences. Its original
filtered v30-parent plus ordered-frontier assembler order is explicitly
preserved, not confused with source DFS or Alpha enrollment order.
The exact artifact SHA-256 is
`983051afddc637a4e033546b8f3ddb8dc0ac22aa996b4e28b3822be8895576ad`.
The five maximal endpoints each require a separate ordinary empty-context
certificate; every complete artifact body also requires the original HA
kernel and the independent compiled Lean checker on the same bytes.

Original CPU170/175-second, wall180-second, RSS1536-MiB, depth256, certificate
and message limits remain unchanged. All admission and publication gates
must run freshly with current source binding. Neither this RFC nor an old
checkpoint receipt can instantiate a live release capability.

These statements complete the identified standard-congruence gaps. They do
not claim primitive roots, all multiplicative-order theorems, the Carmichael
function, higher simultaneous-polynomial congruences, or all of familyF02.
