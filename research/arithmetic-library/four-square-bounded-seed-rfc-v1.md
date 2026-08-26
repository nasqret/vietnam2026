# Constructive strictly prime-bounded four-square seed

This isolated candidate tranche retains the actual coordinate bounds already
present inside the constructive odd-prime half-square residue intersection.
For an odd prime `p = 2h + 1`, its produced witnesses satisfy `a <= h` and
`b <= h`; primality also supplies `1 <= h`. The independently checked odd
half-norm estimate applied to `(a,b,1,0)` therefore yields

    a² + b² + 1 < p².

Because the same residue intersection constructs `a²+b²+1 = p*k`, the
existing natural strict multiplier bound implies `k < p`. The exceptional
prime `2` has the explicit seed `(a,b,k)=(1,0,1)`.

All six candidate bodies replay independently through the HA kernel; the
largest certificate has 209 nodes and depth 40. The exact unconditional
first-order endpoint is

    forall p. Prime(p) -> exists a b k.
      ((a*a + b*b + 1 = p*k) /\ (exists gap. gap + S k = p)).

Its statement SHA-256 is
`664f15010c001437b0d990b4e1f81f845a0bc734a8fb5a3b31633ed463774077`.

`Prime` abbreviates its existing expanded first-order definition; no new
primitive, classical axiom, release admission, or assertion of complete
Lagrange descent is introduced in this candidate tranche.
