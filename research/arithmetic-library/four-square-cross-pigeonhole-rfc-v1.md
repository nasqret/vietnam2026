# Constructive cross-prefix pigeonhole for Lagrange square-residue sets

These isolated, dependency-curried candidate bodies address the exact finite
intersection step used in Lagrange's prime-case proof.

For two injective beta-coded prefixes of equal length `l`, both with values
strictly below `p`, assume an actual beta-coded length-`l+l` prefix whose
every entry is covered by one of the two families at the corresponding even
or odd interleaving index. If `p < l+l`, then:

```text
exists i j value.
  i < l and j < l and
  BetaAt(left_code,left_scale,i,value) and
  BetaAt(right_code,right_scale,j,value).
```

The first body proves that the covered interleaving is itself bounded. The
second invokes the independently checked constructive finite pigeonhole
theorem and eliminates same-family collisions by the two injectivity proofs;
either mixed branch returns explicit cross-family indices and their shared
value. No excluded middle, double-negation elimination, or host-language set
argument is used in the kernel certificate.

The third body constructs the genuine covered interleaving by induction,
using checked two-entry beta-prefix extension and constructive finite-index
splitting. The fourth removes the interleaving premise entirely: two actual
bounded injective prefixes already suffice to construct their common value.
The actual modular square/negative-square prefixes remain separate
prerequisites. No Alpha or Stable admission is claimed.
