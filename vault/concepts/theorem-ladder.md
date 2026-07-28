---
title: Peano Lab theorem ladder
tags: [peano-arithmetic, induction, regression, library]
---

The **theorem ladder** is both curriculum and regression suite for [[peano-lab]]. It begins with
$0+n=n$, develops commutativity and associativity of addition and multiplication, proves the
successor lemmas, defines $n\le m$ by an additive witness, establishes the partial-order laws and
totality, and ends at

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

M11 extends the twenty-rung core with `one_mul`, `mul_one`, and `add_mul`, completing the original
23-entry oriented
[[commutative-semiring-basis]] needed by proof-producing polynomial normalization.

M20 adds 28 general nodes for a total of 51: equality congruence, additive cancellation and
zero-sum, order endpoints, nonzero-product and small-factor reasoning, [[divisibility]],
constructive non-divisibility, generic residue algebra, and [[prime_two]] as the first checked
fully expanded prime instance. The checked DAG and its planned route through the general
[[prime-number]] spine and [[fundamental-theorem-of-arithmetic]] live in the
[[arithmetic-library-moc]].

## Related

[[peano-lab]] · [[proof-certificate]] · [[replayable-proof-script]] · [[substitution]] ·
[[intuitionistic-logic]] · [[foundational-arithmetic-library]]
