# Four-square constructive parity selection and even descent

This isolated candidate tranche supplies the missing unconditional parity
selection required to halve an arbitrary represented even four-square norm.
No candidate changes the sealed Alpha or Stable editions.

The proof first establishes constructively that each natural square is
congruent modulo two to its coordinate. Congruence addition transports the
parity of the full four-square norm to the ordinary coordinate sum. The
checked even/odd sum classifications then select one of the three possible
partitions into two matching-parity coordinate pairs. Explicit additive
permutations align the selected partition with the independently checked
matching-parity halving theorem.

All 13 candidate bodies have independently replayed through the HA kernel;
the largest certificate has 81 nodes and depth at most 25. The exact
unconditional first-order endpoint is

    forall n. FourSquare(n + n) -> FourSquare(n),

where `FourSquare(t)` abbreviates four explicit existential natural witnesses,
not a new primitive predicate. The matching multiplicative endpoint also uses
`n * 2`. The additive endpoint's statement SHA-256 is
`ceedc3db189c22bb6c0a7a6fc76fcebe7248e5de4dded044352ad9d1c7028c22`; the
multiplicative endpoint's is
`c5af9314d7cf3d665f914153f1a7e96176854a735ce7a7a82b4ae812125d12bc`.
Neither endpoint alone is asserted to prove Lagrange's complete four-square
theorem; further prime-seed and strict-descent integration remains outside
this candidate tranche.
