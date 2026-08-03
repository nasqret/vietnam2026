# HA number-theory campaign: definition and representation freeze v1

**Freeze date:** 2026-08-03  
**Repository baseline:** `d9d6e739e7c452ddf2cc9013d8772dfb185ff44f`  
**Machine companion:**
[`ha-definition-representation-freeze-v1.json`](ha-definition-representation-freeze-v1.json)

**Controlling blueprint:**
[`ha-number-theory-formalization-campaign-blueprint.md`](ha-number-theory-formalization-campaign-blueprint.md)

This note freezes the first representation boundary for the new
number-theory campaign. It records what the current Peano Lab implementation
actually means. It does not admit a theorem, add a kernel symbol, or claim
that a relation has a complete mathematical API.

Version 1 inventories the 11 definitions already present in the shared
defined-syntax registry. The campaign's readable `Rem(m,n,r)` notation is a
derived candidate surface, not a twelfth registered predicate: it expands to
`exists q. n = m*q+r /\ Lt(r,m)`. Its expansion and theorem API are tested in
the isolated HA1 module and may enter the shared registry only during a
separate reviewed admission.

The controlling campaign requires strict object-level Heyting arithmetic in
the language \(\{0,S,+,\times,=\}\). The current default checker meets that
logical shape: `check` rejects `DNE`; the separately named `check_classical`
accepts it. Human-facing relation calls are handled even more conservatively
than kernel-level definitional rules: they are hygienically expanded to the
old formula AST before any certificate reaches `check`.

## Reading the classifications

| Classification | Meaning in this freeze |
|---|---|
| `frozen-compatible` | The exact current expansion is suitable as the campaign's canonical relation. Missing convenience lemmas do not change its meaning. |
| `bridge-required` | The exact expansion remains usable and conservative, but the campaign names a second canonical presentation. A checked equivalence or normalization theorem is required before the campaign treats the presentations interchangeably. |
| `legacy-late` | The relation remains valid, useful, and checked where stated, but it is not permitted to supply the foundational K3 representation. It can re-enter only after the non-circular finite-data layer and CRT are established independently. |

These classifications concern representations, not theorem validity. In
particular, `legacy-late` does **not** mean “unproved” or “deprecated.”

## Frozen K0 boundary

The trusted object syntax is exactly:

- one sort, natural numbers;
- terms `Var`, `Zero`, `Succ`, `Add`, and `Mul`;
- formulas `Eq`, `Bot`, `Imp`, `And`, `Or`, `Forall`, and `Exists`;
- de Bruijn variables and capture-avoiding shifting/substitution;
- intuitionistic natural-deduction certificate nodes, equality rules, the six
  fixed arithmetic axioms `PA1`–`PA6`, and formula-specific induction;
- the checked `Cut` node for self-contained proof sharing.

The six arithmetic axioms are successor nonzero, successor injectivity,
addition at zero, addition at successor, multiplication at zero, and
multiplication at successor. `Cut` is a derivation rule, not an additional
arithmetic axiom. The `DNE` data constructor exists for the explicitly
classical entry point but is rejected by the campaign entry point `check`.

Source boundary:

- `peano-lab/py/peano_lab/kernel/terms.py`
- `peano-lab/py/peano_lab/kernel/formulas.py`
- `peano-lab/py/peano_lab/kernel/subst.py`
- `peano-lab/py/peano_lab/kernel/proofs.py`
- `peano-lab/py/peano_lab/kernel/checker.py`

This freeze does not claim a new independent verification result. Such a
result requires its own pinned replay receipt.

## Conservative macros are not theorem APIs

The opt-in parser in
`peano-lab/py/peano_lab/library/defined_syntax.py` recognizes a reviewed
relation call, substitutes its term arguments hygienically into a de Bruijn
template, and immediately returns an ordinary core formula. The ordinary
formula parser and kernel do not acquire a predicate constructor. The runtime
registry is version 2 with SHA-256
`924c8bc220f23ce772b72991b8234c3499be7698dc086d90509d39760a1ed0fe`.

This establishes only a syntactic fact:

```text
defined source
    -> hygienic expansion
ordinary Formula AST
    -> ordinary tactic elaboration
ordinary certificate
    -> intuitionistic check
```

It does not by itself prove totality, functionality, decidability,
characterization, or transport for a relation. Those properties require
ordinary object-level theorems. The machine companion therefore records
`proved_api` and `required_bridge_theorems` separately from
`exact_expanded_template`.

For this freeze, all 44 distinct public theorem names cited by the 45
`proved_api` rows were replayed successfully through the default
intuitionistic checker. This was a selected API audit, not a new full-library
or independent-checker replay.

## Frozen-compatible core relations

The following expansions are accepted without a semantic representation
change:

\[
\begin{aligned}
\operatorname{Le}(a,b) &:\!\iff \exists h\;(h+a=b),\\
\operatorname{Lt}(a,b) &:\!\iff \exists h\;(h+S(a)=b),\\
\operatorname{Dvd}(d,n) &:\!\iff \exists k\;(n=d k),\\
\operatorname{DivRem}(n,d,q,r) &:\!\iff n=dq+r\;\wedge\;r<d,\\
\operatorname{Coprime}(a,b) &:\!\iff
  \forall d\;(d\mid a\to d\mid b\to d=1),\\
\operatorname{IsGCD}(g,a,b) &:\!\iff
  g\mid a\;\wedge\;g\mid b\;\wedge
  \forall d\;(d\mid a\to d\mid b\to d\mid g).
\end{aligned}
\]

The displayed formulas are mathematical renderings. The exact parser text,
association, parameter order, hashes, and implementation paths are in the
JSON manifest. Existing public theorems already include quotient/remainder
existence and uniqueness, relational gcd existence and uniqueness, and both
directions between `Coprime(a,b)` and `IsGCD(1,a,b)`. Those theorem names are
listed in the manifest; this document does not infer them merely from the
macros.

## Relations requiring bridges

### Congruence

The existing balanced-natural relation is frozen verbatim:

\[
\operatorname{ModEq}(m,a,b) :\!\iff
\exists u\,v\;(a+mu=b+mv).
\]

This is the campaign appendix's positive, subtraction-free option. The
campaign nevertheless prefers equality of canonical remainders once division
is available. Existing checked theorems provide the key pieces:
`remainder_decomposition_to_mod_eq`,
`mod_eq_to_remainder_decomposition`, and `mod_eq_bounded_unique`. A single
packaged biconditional with canonical quotient/remainder witnesses is still a
required public bridge. Supplied remainder bounds already rule out modulus
zero, so the strongest bridge needs no duplicate nonzero premise. A closed
candidate now exists, but this freeze does not claim its public admission.

### Primality

The current relation is the factor-pair presentation

\[
\operatorname{Prime}(p) :\!\iff p\ne1\;\wedge\;
\forall a\,b\;(p=ab\to a=1\vee b=1).
\]

The campaign statement instead uses \(p>1\) and a bounded divisor
characterization. Existing checked results prove useful forward components,
including `prime_nonzero`, `prime_is_succ_succ`, and
`prime_divisor_eq_one_or_self`, but this freeze does not pretend those names
already constitute the full stated biconditional. A checked two-way bridge is
required before swapping definitions in campaign statements.

### Balanced Bezout witnesses

The existing four-natural relation is

\[
\operatorname{BalancedBezout}(d,a,b) :\!\iff
\exists x_+,y_+,x_-,y_-\;
  ax_+ + by_+ = d + (ax_- + by_-).
\]

It is an honest subtraction-free encoding of a signed linear combination,
and `gcd_balanced_bezout_exists` is already a checked public theorem. It is
not, however, the campaign's canonical signed-integer representation: it does
not itself select canonical coefficient codes or eliminate negative zero.
The eventual K3 signed-code relation must therefore be connected to this
relation by checked conversion theorems. Until then the existing relation is
safe for arithmetic proofs but cannot close the signed-data representation
gate.

## K3 quarantine: beta coding is late infrastructure

`BetaAt` and `Product` remain exact conservative macros with substantial
checked APIs. They are nevertheless classified `legacy-late` for this
campaign.

`BetaAt(b,c,i,x)` says that `x` is the strictly bounded remainder of `b`
modulo \(1+(i+1)c\). `Product(b,c,l,z)` introduces a second beta-coded trace
whose initial value is one, terminal value is `z`, and successive values
multiply by entries decoded from `(b,c)`.

The existing route for constructing arbitrary bounded beta prefixes uses
pairwise-coprime beta moduli and CRT. The campaign explicitly requires its
first pair/list representation to precede CRT. Therefore:

```text
FORBIDDEN AS K3 FOUNDATION
    BetaAt -> beta prefix existence -> CRT
    CRT -> list coding needed to state/prove CRT

REQUIRED ORDER
    primitive-recursive pair/cell code
        -> canonical explicit-length lists
        -> finite functions/products over those lists
        -> binary and finite CRT
        -> optional theorem translating canonical lists to beta prefixes
```

The quarantine has four operational consequences:

1. no K3 milestone may cite `BetaAt`, `Product`, beta-prefix extension, or a
   beta-coded permutation as its foundational data representation;
2. no M1–M3 theorem needs beta coding merely to speak about one or two
   residues;
3. M4 finite CRT must use the new non-CRT list representation;
4. beta-coded results may be retained as regression tests and, after CRT, as
   an alternative encoding connected by explicit interoperability theorems.

The checked theorems `beta_at_exists_unique` and
`beta_product_exists_unique` establish functionality of the current late
relations. They do not discharge the five K3 acceptance obligations for the
eventual canonical list representation.

## First bridge and representation obligations

The machine manifest gives proposed stable names without claiming proofs.
The immediate dependency order is:

1. package balanced congruence as equality of canonical remainders;
2. prove the two-way factor-pair/bounded-divisor primality bridge;
3. freeze a non-CRT pair code and prove constructor/decoder functionality;
4. freeze explicit-length canonical list cells and their validity predicate;
5. freeze a canonical signed-integer code and connect it to
   `BalancedBezout`;
6. only after those gates, build list folds and finite CRT;
7. optionally prove canonical-list/beta-prefix interoperability.

Every new definition must preserve the same discipline: a surface expansion
receipt is not a theorem receipt, and a host implementation is not an
object-level HA proof.
