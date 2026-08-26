# Constructive polynomial formal differentiation and Hensel foundations

Status: 15 independently original-kernel-checked additive Alpha-v24 candidates.

This campaign supplies the previously missing *formal differentiation*
component of the local-lifting roadmap. It does **not** claim simple-root
Hensel lifting, a Taylor divisibility theorem, a prime-power lift, finite-field
factorization, or any additional logical principle.

## Exact first-order representation

A polynomial is the established finite Gödel-beta coefficient prefix
`Beta(b,c,i,a)`, with coefficients supplied in Horner order. Two independently
beta-coded natural traces are related by

```text
v(0) = 0                  d(0) = 0
v(i+1) = v(i)*t + a(i)    d(i+1) = d(i)*t + v(i)
```

The second trace is exactly the already checked ordinary Horner recurrence
whose coefficient code is the first trace itself. Thus no derivative-code
oracle, new object-language function, new predicate, new sort, classical
excluded middle, or modified kernel is needed.

The conservative hygienic authoring relations are:

```text
HornerDerivativeTrace(b,c,t,l,u,v,d,e)
HornerDerivative(b,c,t,l,n,z)
HornerDerivativeOnly(b,c,t,l,z)
```

`HornerDerivativeTrace` supplies both complete beta traces, including their
zero starts and every bounded transition. `HornerDerivative` adds both actual
terminal values. `HornerDerivativeOnly` existentially packages the independently
witnessed polynomial value. Every abbreviation expands to a formula over the
unchanged strict Heyting-arithmetic signature `0,S,+,*,=`.

## Dependency-ordered candidate inventory

1. `beta_horner_derivative_trace_exists`
2. `beta_horner_derivative_value_exists`
3. `beta_horner_derivative_value_projection`
4. `beta_horner_derivative_only_projection`
5. `beta_horner_derivative_only_exists`
6. `beta_horner_derivative_first_component_functional`
7. `beta_horner_derivative_empty`
8. `beta_horner_derivative_successor_decompose`
9. `beta_horner_derivative_functional`
10. `beta_horner_derivative_second_component_functional`
11. `beta_horner_derivative_exists_unique`
12. `beta_horner_derivative_only_functional`
13. `beta_horner_derivative_only_exists_unique`
14. `beta_horner_derivative_constant`
15. `beta_horner_derivative_linear`

The 15 results have 27 direct proof dependencies, 583 authored tactic commands,
1,002 independently checked ordinary dependency-curried proof nodes, maximum
body size 173, and maximum proof depth 41. The ordered theorem-name digest is

```text
2f9f8f66433ce0f597fc5f8e1a71349996be02e2329700d70a33a97c4d4d52e1
```

The exact simultaneous existence/uniqueness endpoint is

```text
∀ b c t l. ∃ n z.
  HornerDerivative(b,c,t,l,n,z)
  ∧ ∀ m w. HornerDerivative(b,c,t,l,m,w) → n=m ∧ z=w.
```

Its expanded first-order statement SHA-256 is

```text
171b5939376bfb9e9ec9469d3addd98e27584931fa7994dccb4b372c4d9a693f
```

The exact successor theorem additionally extracts an actual last coefficient
`a` and predecessor pair `(r,q)` such that

```text
n = r*t + a
z = q*t + r.
```

Its expanded first-order statement SHA-256 is

```text
042cb58aec7a7a63eaef9c83958feefbc51b1ce89e927010c2e9427f401b7435
```

The empty polynomial has value and derivative zero. A one-coefficient
polynomial evaluates to its decoded constant and has derivative zero. A
two-coefficient polynomial `a*t+k` has exact derivative `a`.

## Proof and trust boundary

Existence composes the historical original-kernel-checked
`beta_prefix_horner_trace_exists` theorem twice: first for the coefficient
prefix, then for the first value trace. Actual terminal entries come from
`beta_at_exists`. The exact successor recurrence follows from the two real
bounded trace transitions and beta-value uniqueness. Simultaneous
functionality is proved by ordinary natural-number induction on the coefficient
length. No extensional trace-code equality or choice principle is assumed.

The Python dual-Horner evaluator and its tamper-evident receipt are bounded
illustrative computation only; they grant no formal proof authority. Additive
Alpha admission further requires the dependency-closed original-kernel bundle,
the unchanged independently compiled Lean proof checker, immutable Alpha-v23
parent authentication, and the release's separate fail-closed admission audit.

## Honest Hensel frontier

Milestone **G095 remains open**. The missing work includes an exact witnessed
Taylor divisibility identity at arbitrary prime-power precision, the actual
derivative-unit modular inverse, the constructed lifted residue, its strict
canonical bound, and its uniqueness. Formal differentiation is a genuinely
proved prerequisite, not the already completed Hensel theorem.
