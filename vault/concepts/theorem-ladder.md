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

The complete public ladder now has 63 entries: the original 23-entry core, 14 audited
general-arithmetic additions, and the 26-entry modular extension. The general additions cover
equality transport and congruence, additive cancellation, elementary order and zero facts,
nonzero-product reasoning, and `prime_two`. The modular extension develops multiples, residue
transport, the five residue cases, square residues, and the capstone
$\neg(5\mid n)\to\exists q.\;n^4=5q+1$.

The ordered catalog root is
`d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0`.

The 14-entry source origin `bb90b0b…e24e1` and audited merge `90bd8dcd…d1d7`, together with the
modular source commit and catalog hash, are retained under `artifacts/peano-library/`. Every
expanded certificate is checked in the empty context. The modular extension remains a useful seed
for a [[verifier-guided-policy-evaluation-and-search|policy curriculum]], but the capstone itself is
now a library-retrieval test rather than a sealed theorem-discovery benchmark.

## Related

[[peano-lab]] · [[proof-certificate]] · [[replayable-proof-script]] · [[substitution]] ·
[[intuitionistic-logic]]
