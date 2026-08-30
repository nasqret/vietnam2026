# Actual general finite signed Dirichlet inverses

Date: 2026-08-29. This is a local, non-admitting mathematical authoring record
for [PLAN/19](../../PLAN/19_general_dirichlet_inverses.md). It does not grant
Alpha or Stable membership and is not a complete dependency-closed proof
receipt. Independent full-cone HA, compiled Lean and ordinary-principal
verification are subsequent required gates.

## Conservative relations and exact endpoints

The inverse relation uses only the existing genuine table, delta and
convolution graphs:

```text
SignedUnit(u) := u=2 ∨ u=1.
DirichletUnitAtOne(F) := ArithAt(F,1,2) ∨ ArithAt(F,1,1).
DirichletInverse(N,F,G) :=
  ∃E. KroneckerDeltaTable(N,E) ∧
      (DirichletTable(N,F,G,E) ∧ DirichletTable(N,G,F,E)).
```

Signed code 2 represents +1 and code 1 represents -1. `SignedUnit` is the
scalar foundation's single predicate, not a second independently defined
notion. `DirichletUnitAtOne` directly expands through actual lookups. Its
relationship with `SignedUnit` is proved by witness/from-value theorems; it
must not be invented as a definition-expansion edge. `DirichletInverse`
contains no unit criterion or asserted inverse law without actual folds.

The main necessary-and-sufficient condition is:

```text
∀N F. ArithTable(N,F) →
  ((∃G. DirichletInverse(N,F,G)) →
     (N=0 ∨ DirichletUnitAtOne(F))) ∧
  ((N=0 ∨ DirichletUnitAtOne(F)) →
     ∃G. DirichletInverse(N,F,G)).
```

The constructive endpoint is stronger than existence:

```text
∀N F w. ArithTable(N,F) → (N=0 ∨ DirichletUnitAtOne(F)) →
  ∃G. DirichletInverse(N,F,G) ∧
      (ArithAt(G,0,w) ∧
       ∀H. DirichletInverse(N,F,H) → ArithPositiveEqual(G,H,N)).
```

The construction first solves a general target equation:

```text
∀N F T u w. ArithTable(N,F) → ArithTable(N,T) →
  ArithAt(F,1,u) → SignedUnit(u) →
  ∃G. DirichletTable(N,G,F,T) ∧ ArithAt(G,0,w).
```

Here `T` is any actual signed table, not a supplied inverse or a delta oracle.
Specialization constructs an actual delta target using the prior existence
theorem. Every weighted fold is constructed before its value is identified.

## Inductive construction and domain boundary

Suppose an actual prefix G solves G*F=T through k. At n=S k:

1. Construct the actual inclusive summand prefix only through k, then its
   signed fold of length n. Its remainder r includes d<n but not d=n.
2. Read the actual target value e=T(n). From the actual signed unit u=F(1),
   construct x and y satisfying `SignedMul(x,u,y)` and `SignedAdd(r,y,e)`.
3. Perform genuine paired-beta recoding to append x as G(n), preserving every
   earlier represented value. Apply the restricted input-transport lemma and
   append the endpoint with actual quotient one. The full signed fold has
   length S n and value e.
4. Prove that every earlier convolution is preserved. Induction starts from
   a real singleton whose zeroth value is the independently prescribed w.

The strict-prefix constructor and input-transport/last-step obligations are
in [the triangular foundation](dirichlet-triangular-rfc-v1.md); the actual
unit classification and affine solver are in
[the signed scalar foundation](dirichlet-signed-unit-rfc-v1.md). Neither a
finite-choice principle nor a recursion/inverse oracle is assumed.

Necessity uses the actual convolution at n=1. On a nonempty prefix, delta(1)
is signed one; classification of its actual signed factors forces F(1) to
be +1 or -1. At N=0 there is no unit condition. Both input tables and a real
delta witness still exist, but their positive-value constraints are empty.

Uniqueness is equality of positive represented values, never equality of
arbitrary table codes or of zeroth values. With actual inverse witnesses
G*F=E and F*H=D, associativity gives E*H=G*D; the independently proved left
and right delta identities give H=G on 0<n<=N. The same argument works for
separately encoded delta witnesses with different zeroth values.

Restriction preserves the same actual delta and convolution witnesses.
Independent inverse constructions on different prefixes therefore agree on
their common positive domain. Inversion twice recovers positive represented
values without imposing any additional equality on codes or index zero.

## Frozen mathematical source and conditional body checks

Source: `peano-lab/py/peano_lab/library/dirichlet_inverse_candidate.py`.
Factory: `make_dirichlet_inverse_candidate_theorems`.
There are **21 statements, 53 direct prerequisites and 764 tactic commands**.

Source SHA-256:
`05347563a82486859a49539e99055504720cc823e14b310389e1d90766a85379`.
Ordered specification SHA-256:
`6ccb0ee24d871bffbdedb3100445411ec03cd1d515586f5b63fa9d4780bfdf20`.

All 21 actual theorem bodies passed the original HA candidate-body checker
in three separate original-bound authoring windows:

| Group | Bodies | Seconds | Peak resident bytes |
| --- | ---: | ---: | ---: |
| Elementary relations and inverse calculus | 11 | 38.712 | 601,505,792 |
| General target append and induction | 2 | 35.764 | 554,909,696 |
| Constructed inverses, necessity and equivalences | 8 | 26.838 | 478,248,960 |

These are conditional-body checks with the exact declared prerequisites,
not ordinary empty-context certificates or full dependency-cone receipts.
They do not replace the subsequent independent tests, exact novelty against
all 3,756 prior statements, complete original HA/Lean checks and separately
replayed principal certificates. The 40-row tranche comprises these 21 rows,
9 signed-unit rows and 10 triangular rows; support is not counted as new.

Selected exact statements and hashes:

| Theorem | Statement SHA-256 |
| --- | --- |
| `dirichlet_unit_equation_construct` | `cbb0fc99f0f2eb3e77871b21e4a8d5cfe01d22c86b737e77b516f4c060f8644e` |
| `dirichlet_inverse_criterion` | `8c777567eae9fae4a3b6f0e0df4e4d80205c694f5b15f93f1808376e1b7d05fc` |
| `dirichlet_inverse_exists_positive_unique` | `eb7703bdacfaca3d2d4a6c0cf5d2a43326be82107047a7609ce053da0fedd164` |

All windows retain CPU (170,175) seconds, wall 180 seconds and observed RSS
1,536 MiB. No kernel, replay, proof-object or formula limit was changed.

## Scope

This closes the mathematical inverse-construction/criterion obligation
subject to the complete proof-evidence gates, not all of G009. General
multiplicative-function closure still needs a separate actual coprime-divisor
reindexing and finite-Fubini proof. G007's earlier finite signed Möbius theorem
and general G091's open status are unchanged. Alpha remains v30 (3,222),
Stable remains 432, and all four earlier research generations and their
snapshots remain separate and unchanged. No promotion or publication occurs.
