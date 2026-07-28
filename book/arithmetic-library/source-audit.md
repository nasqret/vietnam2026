# Sources and clean-room provenance

The arithmetic corpus uses external curricula as coverage maps, not as an
unexamined pool of proof text. For each source the repository records its exact
URL, revision where available, license, reuse mode, topic mapping, and known
gaps.

## Natural Number Game 4

The [Lean 4 Natural Number Game](https://github.com/leanprover-community/NNG4)
is pinned in the source register and licensed Apache-2.0. Its active worlds
give a strong foundation in Peano equations, addition, multiplication, order,
cancellation, nonzero products, and powers.

Its current game manifest does not supply a prime-number corpus: the prime,
even/odd, and strong-induction worlds remain outside the active game, and the
prime-world file is an empty work-in-progress stub. The final power-world FLT
exercise uses a deliberately unsound teaching escape and is excluded from the
lemma corpus. The source is therefore evidence for the early semiring/order
coverage, not for primes or factorization.

## The Mechanics of Proof

Heather Macbeth's [The Mechanics of
Proof](https://hrmacbeth.github.io/math2001/) supplies an excellent curricular
map from structured proof through parity, modular arithmetic, division, the
Euclidean algorithm, gcd, prime divisors, Euclid's lemma, and infinitely many
primes.

The associated source repository has no repository-wide reuse license and its
relevant Lean files reserve rights. The policy here is reference-only,
clean-room reconstruction: do not copy its prose, Lean code, exercises, or
proof scripts. We independently state Peano formulas, construct Peano proofs,
and require the local kernel check.

## An Illustrated Theory of Numbers

Martin Weissman's [programming
resources](https://illustratedtheoryofnumbers.com/prog.html#notebooks) provide
a later computational roadmap: Euclidean algorithms, sieves, primality tests,
factorization, modular exponentiation, primitive roots, totients, and
cryptographic applications.

The companion Python notebooks are GPL-3.0. They remain external algorithm
indexes; no notebook code is copied into this MIT/CC BY-SA project. The
published AMS book is cited as a book, not mined for source or prose.

## TeX-source search

The requested three resources do not collectively expose reusable book TeX
source. The broader search found a useful three-source set:

- the [Open Logic Project](https://openlogicproject.org/) publishes CC-BY-4.0
  LaTeX for induction and arithmetization;
- [An Infinite Descent into Pure Mathematics](https://infinitedescent.org/)
  publishes CC-BY-SA-4.0/LPPL TeX covering induction, divisibility, modular
  arithmetic, and primes;
- William Stein's [elementary-number-theory TeX
  repository](https://github.com/williamstein/ent) covers primes and
  congruences but has no repository license and identifies a Springer
  publication, so it is reference-only.

Every path and revision is pinned in the source register. No external TeX has
been vendored into this release: the mathematical statements and explanations
were written independently, and direct links preserve provenance without
creating a license mixture.

## Reuse modes

The source register uses explicit modes:

- `project_internal` for this repository's own material;
- `statement_adapted_proof_reconstructed` where a licensed mathematical
  statement informs coverage but the Peano proof is rebuilt;
- `reference_only_clean_room` for unlicensed or publisher-controlled sources;
- `algorithm_index_clean_room` for GPL notebooks used only to identify future
  algorithms and examples.

Mathematical facts are reusable; distinctive prose and source code are not
silently treated as public domain. Provenance accompanies even independently
proved facts because it explains why a lemma belongs in the curriculum.
