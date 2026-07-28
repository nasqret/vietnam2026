---
title: Peano Lab theorem ladder
tags: [peano-arithmetic, induction, regression, library]
---

The **theorem ladder** is both curriculum and regression suite for [[peano-lab]]. It begins with
$0+n=n$, develops commutativity and associativity of addition and multiplication, proves the
successor lemmas, defines $n\le m$ by an additive witness, establishes the partial-order laws and
totality, and reaches the 23-entry core capstone

$$
\forall n\,m.\;n\cdot m=0\to n=0\lor m=0.
$$

Each named entry stores a closed statement, earlier dependencies, and an exact tactic script. CI
replays the script and submits the dependency-free result to the [[trusted-kernel]]. Helper lemmas
are first-class checked entries, not hidden rewrite axioms.

The browser commands `pa lib <name>` and `pa lean <name>` expose the script and an exact Lean 4
statement stub respectively. Inside a live proof, `use <name>` performs [[checked-theorem-reuse]]
by compiling the closed certificate into an ordinary local cut.

A [[replayable-proof-script]] may preserve how a live theorem was discovered, but it does not add a
library entry. Admission still requires a reviewed closed statement, earlier dependencies, replay,
kernel check, tests, and a source commit.

M11 extends the twenty-rung core with `one_mul`, `mul_one`, and `add_mul`, completing the oriented
[[commutative-semiring-basis]] needed by proof-producing polynomial normalization.

A public 26-entry extension brings the complete ladder to 49 entries. It develops multiples,
residue transport, the five residue cases, square residues, and the capstone
$\neg(5\mid n)\to\exists q.\;n^4=5q+1$. Its source commit and catalog hash are retained, and every
expanded certificate is checked in the empty context. This extension is also a useful seed for a
[[verifier-guided-policy-evaluation-and-search|model-v2 curriculum]], but the capstone itself is now
a library-retrieval test rather than a sealed theorem-discovery benchmark.

## Related

[[peano-lab]] · [[proof-certificate]] · [[replayable-proof-script]] · [[substitution]] ·
[[intuitionistic-logic]]
