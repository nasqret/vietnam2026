# Self-contained proof sharing

The arithmetic library reached a point where proof composition, rather than
arithmetic, was the limiting resource. If a closed dependency proof is copied
into every place where its hypothesis is used, a short modular script can
expand into a large tree. More seriously, doing that copying correctly
requires capture-sensitive substitution through implication, disjunction,
existential, universal, and induction scopes.

Peano Lab addresses this with one small, explicit sharing boundary. The
solution changes how proof certificates are represented; it does not change
what first-order Peano arithmetic can say or prove.

## The rule

The certificate constructor is

```text
Cut(A, B, lemma, body)
```

and its checking rule is

$$
\frac{\Gamma\vdash\mathit{lemma}:A\qquad
      A,\Gamma\vdash\mathit{body}:B}
     {\Gamma\vdash\operatorname{Cut}(A,B,\mathit{lemma},\mathit{body}):B}.
$$

The four fields are all necessary:

- `A` is the proposition established by the lemma;
- `B` is the conclusion of the whole node;
- `lemma` is a complete proof checked in the ambient context $\Gamma$;
- `body` is checked with $A$ added as hypothesis zero.

The conclusion annotation matters because Peano Lab's checker is
bidirectional. An elimination often synthesizes its result, while an
introduction such as implication or universal introduction normally needs a
known target. Storing `B` lets the checker validate an introduction-shaped
body without asking an untrusted caller to infer it. The annotation supplies
no authority: a mismatch between `B` and the body is rejected.

The same logic-mode flag is used in both branches. A classical lemma cannot be
smuggled into an intuitionistic body, and an intuitionistic Cut does not add
double-negation elimination.

## What is shared

The lemma branch occurs once in the certificate and is checked once at that
Cut. The body may refer to it any number of times through hypothesis zero.
This removes repeated proof substitution within that lexical scope.

This is deliberately smaller than a general proof DAG. Reusing the same
certificate at two distinct Cut nodes still creates two structural
occurrences. Peano Lab does not memoize arbitrary nodes by identity and does
not ask the checker to retrieve a proof from a global table.

Library replay uses nested Cuts. It first proves the dependency-curried body,
peels the generated implication introductions, and surrounds the remaining
body with one Cut per already checked dependency. The live `use` command
similarly rechecks the selected closed certificate before placing it in a Cut
around the focused goal.

## Why this is not a theorem oracle

A theorem oracle would let the checker accept a name, hash, database row, or
external callback as evidence. Cut does none of those things. It contains its
own formula, lemma proof, conclusion, and body proof. The checker has all the
data needed for one self-contained invocation.

Consequently:

- a renamed theorem changes no checking rule;
- a content hash can detect drift but can never establish truth;
- the library and UI remain untrusted name-resolution layers;
- a forged lemma branch is rejected when that branch is checked;
- a forged body or conclusion annotation is rejected independently.

The trusted base nevertheless did grow. `Cut` is a kernel proof constructor,
and the checker has a case implementing the displayed rule. Calling it
“derived” explains its mathematical conservativity; it does not move the
implementation outside the soundness boundary. The constructor and checker
case therefore require the same review, mutation tests, malformed-input tests,
and classical-mode tests as every other trusted rule.

## What did not change

Natural-number terms are still built only from $0$, successor, addition, and
multiplication. Formulas still use equality, the first-order connectives, and
quantifiers. PA1--PA6 and formula-specific induction are unchanged. No
primitive division, gcd, prime predicate, sequence type, product function, or
factorization axiom was added.

Proof sharing therefore cannot replace any mathematical rung in the
{doc}`dependency ladder <dependency-ladder>`. It makes those rungs practical
to compose while leaving their fully expanded first-order statements intact.

## Local reasoning remains administrative

The surface tactics `have h : P` and `suffices h : P` are not direct Cut
constructors. They use engine-only `LocalHave` and `LocalSuffices` nodes to
schedule two open goals in opposite orders. Before QED, an untrusted
capture-avoiding compiler removes those nodes by proof-hypothesis
substitution. The trusted checker never accepts either administrative class.

This separation is intentional. A library dependency is already a closed,
rechecked certificate suited to lexical sharing. A local claim is still being
constructed and must retain the established live-goal, undo, and transaction
semantics.

The reducer's public normalization pass reflects this distinction: it
contracts implication and universal beta redexes and eliminates the two local
schedulers, but preserves trusted Cut nodes.

## Erasure is an audit, not authority

Mathematically, one Cut can be expanded to

$$
(\lambda h.\,\mathit{body})\;\mathit{lemma}.
$$

The untrusted `erase_trusted_cuts` utility performs exactly this structural
expansion recursively. It does not beta-normalize the redexes it creates, it
rejects live certificates containing holes, and its output must be checked
again.

The utility is intentionally not advertised as a complete route from every
accepted Cut proof to an accepted expanded tree. Peano Lab's bidirectional
checker cannot synthesize every introduction-shaped lemma when it appears as
an implication argument. Applying the separate reducer helps in many cases,
but the reducer's capture-sensitive behavior around large induction-bearing
proofs was one reason sharing was introduced. Neither transformation is a
second kernel, and neither successful transformation is evidence until the
kernel accepts its result.

This limited erasure is still useful. It supports small conservativity tests,
compares shared and legacy representations where both check, and documents
the ordinary natural-deduction meaning of the new node without pretending
that the compatibility tooling is complete.

## The resulting trust path

For a library theorem, the path is now

$$
\begin{aligned}
&\text{statement + dependency scripts}\\
&\quad\longrightarrow\text{untrusted replay and packaging}\\
&\quad\longrightarrow\text{one closed, self-contained Cut certificate}\\
&\quad\longrightarrow\operatorname{check}(\varnothing,p,T).
\end{aligned}
$$

Only the last arrow grants theorem authority. For the surrounding distinctions
between notation, object language, and certificate representation, continue
with {doc}`Language, notation, and trust <language-and-trust>`.
