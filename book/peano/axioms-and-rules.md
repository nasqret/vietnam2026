# PA axioms, induction, and proof rules

Peano Lab's kernel recognizes six arithmetic axiom constants. Everything else
in the arithmetic library—including Euclid's lemma, the Fundamental Theorem of
Arithmetic, and the quadratic-reciprocity candidate—is built from these,
first-order logic, equality, and concrete induction instances.

## The six arithmetic axioms

| Name | Exact schema | Role |
|---|---|---|
| `PA1` | $\forall x.\;\neg(Sx=0)$ | no successor is zero |
| `PA2` | $\forall x\,y.\;Sx=Sy\to x=y$ | successor is injective |
| `PA3` | $\forall x.\;x+0=x$ | addition at zero |
| `PA4` | $\forall x\,y.\;x+Sy=S(x+y)$ | addition at a successor |
| `PA5` | $\forall x.\;x*0=0$ | multiplication at zero |
| `PA6` | $\forall x\,y.\;x*Sy=x*y+x$ | multiplication at a successor |

The equations recurse on the right argument. Thus `n + 0 = n` is immediate
from `PA3`, while `0 + n = n` requires induction.

Each occurrence in a formal proof is explicit. For example, specializing
`PA4` produces nested universal-elimination certificate nodes; rewriting with
it produces an equality-substitution node. The tactic layer never asks the
kernel to accept the string `PA4` by reputation.

## Induction is a rule, not `PA7`

For each concrete formula $P(n)$, the certificate grammar can construct the
instance

$$
P(0)\to\bigl(\forall n.\;P(n)\to P(Sn)\bigr)\to\forall n.\;P(n).
$$

The motive is an actual first-order formula. There is no object-language
predicate variable $P$ and no theorem name that grants arbitrary induction.
The `induction n` tactic constructs the corresponding `Ind` certificate for
the current goal.

## Logical and equality rules

The proof grammar contains ordinary natural-deduction constructors for:

- implication introduction and elimination;
- conjunction introduction and both projections;
- disjunction introductions and case elimination;
- universal introduction and elimination;
- existential introduction and elimination;
- explosion from bottom;
- equality reflexivity, symmetry, transitivity, congruence, and substitution;
- formula-specific induction;
- the six fixed arithmetic axiom constants.

The contextual `Cut(A,B,lemma,body)` constructor shares a closed proof of $A$
with a body that derives $B$ under hypothesis $A$. The checker verifies both
branches. `Cut` is proof packaging, not a theorem-name lookup and not a new
arithmetic assumption.

## Constructive default and classical extension

The native library is constructive. A separate `DNE` certificate constructor
is available only when a proof owner explicitly enables classical mode. It is
not used as hidden authority for the quadratic-reciprocity development. The
proof explorer therefore distinguishes:

- an explicit occurrence of PA1--PA6;
- an induction step generated for a concrete motive;
- a tactic such as `simp`, whose exact internal rewrites require replay to
  attribute line by line;
- any classical extension.

## Tactics versus rules

A tactic is an untrusted program that constructs a proof. It is not itself a
logical rule. The QR scripts use nineteen primitive surface tactics:

```text
intro  have  specialize  induction  apply  split  left  right
cases  exfalso  exists  refl  symm  trans  congr  exact
rewrite  simp  norm_num
```

For example, `apply L` builds eliminations against the exact type of `L`;
`rewrite L` builds equality substitution; `exists w` supplies a witness; and
`simp` builds a sequence of explicit equality proofs. Read
{doc}`the tactic reference <tactics>` for examples and
{doc}`the tactical language <tacticals>` for sequencing and backtracking.

## The trust boundary

```text
statement + tactic script + dependency metadata
                    |
                    v
       untrusted proof construction
                    |
                    v
        ordinary certificate tree/DAG
                    |
                    v
  kernel check(empty context, proof, statement)
                    |
                    v
             theorem accepted
```

Names, hashes, source locations, dashboards, WMI receipts, and generated prose
are provenance. None is consumed by the kernel as proof authority.

The QR candidate adds one engineering challenge: recursively copying all
dependency certificates would exceed the live proof-node policy. The layered
compiler instead packages dependency layers with ordinary conjunctions and
`Cut`, then submits one ordinary certificate to the unchanged checker. Until
that exact certificate passes WMI replay and public enrollment, the explorer
labels QR bodies as candidates rather than admitted theorems.

## Continue reading

- {doc}`Native PA language reference <language-reference>`
- {doc}`Kernel and certificate checker <kernel>`
- {doc}`Tactics <tactics>`
- {doc}`Proof sharing <../arithmetic-library/proof-sharing>`
- {doc}`PA Proof Explorer <../arithmetic-library/proof-explorer>`

