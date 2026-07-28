---
title: Self-contained proof sharing
tags: [peano-lab, kernel, proof-certificate, cut, trust]
---

**Self-contained proof sharing** is Peano Lab's trusted certificate rule

$$
\frac{\Gamma\vdash p:A\qquad A,\Gamma\vdash q:B}
     {\Gamma\vdash\operatorname{Cut}(A,B,p,q):B}.
$$

The [[trusted-kernel]] checks the embedded lemma once in the ambient context,
then checks the body with its proposition at hypothesis zero. The conclusion
annotation lets the bidirectional checker check an introduction-shaped body;
it is verified rather than trusted. Both branches use the same logic mode.

A Cut contains both formulas and both [[proof-certificate|proof branches]]. It
contains no theorem name, hash, declaration identifier, or external lookup.
It therefore supplies lexical sharing without creating a trusted theorem
environment. The trusted checker has genuinely grown, but Peano Lab's term
grammar, formula grammar, PA axioms, induction schema, and intuitionistic
default have not changed.

This node is distinct from a [[local-reasoning-cut]]. Engine-only `LocalHave`
and `LocalSuffices` still schedule open goals and compile away before QED.
[[checked-theorem-reuse]] and the [[lemma-dependency-dag]] instead embed
already checked closed certificates in trusted Cuts.

The untrusted `erase_trusted_cuts` utility recursively expands a Cut to
`(λh. body) lemma` without beta-normalizing it. Erasure is a compatibility
audit, not authority and not a complete operational equivalence: the
bidirectional checker cannot synthesize every introduction-shaped erased
argument, and the capture-sensitive reducer is incomplete for some large
induction-bearing expansions. An erased result counts only after a fresh
kernel check.

Full design: [research proof-sharing note](../../research/arithmetic-library/proof-sharing-design.md)
· [book chapter](../../book/arithmetic-library/proof-sharing.md)

## Related

[[trusted-kernel]] · [[proof-certificate]] · [[checked-theorem-reuse]] ·
[[local-reasoning-cut]] · [[lemma-dependency-dag]] · [[de-bruijn-criterion]]
