# Constructive polynomial Taylor remainders and genuine Hensel lifting

Status: 19 additive Alpha-v25 candidates, all independently accepted by the
unchanged first-order constructive Heyting-arithmetic proof kernel.

This campaign advances the established beta-coded polynomial/formal-derivative
foundation to an **actual one-step root-lifting theorem**. It additionally
proves simultaneous evaluation/derivative congruence, a witnessed natural
Taylor identity, a strictly bounded and uniquely determined correction digit,
and a genuine bounded inverse of the evaluated formal derivative.

## Exact hygienic conservative definitions

The two proposed reviewed relation abbreviations are

```text
HornerTaylorRemainder(b,c,a,h,l,n,d,y,q)
  ≡ HornerDerivative(b,c,a,l,n,d)
    ∧ Horner(b,c,a+h,l,y)
    ∧ y=(n+h*d)+(h*h)*q

HenselCorrection(d,p,q,t)
  ≡ t<p ∧ q+d*t ≡ 0 (mod p).
```

`HornerTaylorRemainder` depends precisely on the already reviewed
`HornerDerivative` and `Horner` relations. `HenselCorrection` depends on
reviewed `Lt` and `ModEq`. Both expand hygienically to the unchanged language
`0,S,+,*,=`. No new predicate, function symbol, ring oracle, subtraction,
excluded middle, choice principle, axiom, or kernel rule is added.

The exact dependency-ordered theorem inventory is:

1. `hensel_predecessor_annihilates_residue`
2. `horner_mod_congruence_successor_step`
3. `horner_derivative_mod_congruence_successor_step`
4. `beta_horner_eval_mod_congruence`
5. `beta_horner_derivative_mod_congruence`
6. `hensel_add_swap_nested`
7. `horner_taylor_successor_identity`
8. `beta_horner_taylor_remainder_exists`
9. `hensel_correction_exists`
10. `hensel_correction_unique`
11. `hensel_correction_exists_unique`
12. `horner_derivative_coprime_bounded_inverse`
13. `beta_horner_taylor_square_congruence`
14. `beta_horner_taylor_remainder_total`
15. `hensel_correction_implies_multiple`
16. `hensel_linear_correction_multiple`
17. `hensel_square_shift_multiple`
18. `beta_horner_hensel_lift_divisibility`
19. `beta_horner_hensel_lift_exists`

The 19 constructive theorem bodies have **69 direct proof dependencies**,
**867 authored tactic commands**, and **1,362 independently checked ordinary
dependency-curried proof nodes**. The largest individual body has 262 nodes;
maximum proof depth is 58. The exact ordered theorem-name SHA-256 is

```text
f909e072a84a460d63971e51c54e034b10c54295b368ef2ce49b09d469c63e40
```

## Exact witnessed natural Taylor theorem

For every arbitrary finite beta-coded coefficient prefix, natural evaluation
point and natural shift, the checked root theorem is

```text
∀ b c a h l n d y.
  HornerDerivative(b,c,a,l,n,d)
  → Horner(b,c,a+h,l,y)
  → ∃ q. y=(n+h*d)+(h*h)*q.
```

Its expanded first-order statement SHA-256 is

```text
5df4c9bd62d28df38c7fdcd0daf41c5fddf518942db92a74ac3a17676033ed82
```

The proof inducts over the actual coefficient prefix. For predecessor value
`r`, predecessor derivative `d`, predecessor remainder `q`, evaluation point
`a`, shift `h`, and next coefficient `k`, the exact transition is

```text
(((r+h*d)+(h*h)*q)*(a+h)+k)
  = ((r*a+k)+h*(d*a+r))+(h*h)*(q*(a+h)+d).
```

Thus the genuinely witnessed remainder evolves by

```text
q_next = q*(a+h)+d.
```

The moderately large successor identity is proved solely from previously
checked distributivity, associativity, and commutativity. A finite sequence
of generated adjacent summand swaps expands into individually checked
ordinary tactics; it never introduces an untrusted ring-normalization rule.

## Unique bounded correction and derivative inverse

The exact correction endpoint is

```text
∀ d p q. p≠0 → Coprime(d,p)
  → ∃ t. HenselCorrection(d,p,q,t)
          ∧ ∀ u. HenselCorrection(d,p,q,u) → u=t.
```

Expanded first-order statement SHA-256:

```text
116197e3bebc5a3e2ee9290c2826b209e4d7f3047121533cc22c8e32324c3d70
```

No subtraction is postulated: for `p=S k`, the checked predecessor residue
gives `q+k*q ≡ 0 (mod p)`. The existing constructive bounded linear
congruence solver supplies the actual digit. Uniqueness uses checked
congruence cancellation by a coprime factor and uniqueness of bounded
residues. The independently checked derivative-inverse root further supplies

```text
HornerDerivative(b,c,a,l,n,d) → p≠0 → Coprime(d,p)
  → ∃ u. u<p ∧ d*u ≡ 1 (mod p).
```

## Actual one-step root lifting

The strongest checked endpoint is

```text
∀ b c a l n d m p s q.
  p≠0
  → HornerDerivative(b,c,a,l,n,d)
  → m=p*s
  → n=m*q
  → Coprime(d,p)
  → ∃ t y.
      HenselCorrection(d,p,q,t)
      ∧ Horner(b,c,a+m*t,l,y)
      ∧ ∃ w. y=(p*m)*w.
```

Its expanded first-order statement SHA-256 is

```text
9cfc4633ea27c492b0deb35a56fe44b25b8dbf50d56fb27f29285f74b6c58a8b
```

This is a genuine root-lifting theorem, not merely a named surrogate:
the digit is an actual natural witness with `t<p`, the polynomial at the
lifted point is actually evaluated, and its divisibility by the next modulus
`p*m` has an explicit natural witness. The proof applies the exact Taylor
identity at shift `m*t`; its linear part is divisible by `p*m` by the checked
correction, and its quadratic part is divisible by `p*m` because `m=p*s`.
Existing checked divisibility closure combines both real witnesses.

## Honest remaining G095 boundary

The exact roadmap milestone **G095 remains OPEN**. Its requested statement
requires a unique representative strictly bounded by the new prime power for
an unrestricted original input `a`, not just the bounded correction digit.
Still outstanding are the transport to the canonical old residue `a₀`, its
explicit strict lifted bound `a₀+m*t<p*m`, uniqueness among *all* canonical
lifted representatives, and the exact relational prime-power bridge.

The new campaign proves actual one-step lift existence, witnessed Taylor
divisibility, derivative-unit inverse, simultaneous congruence, and unique
bounded correction without claiming those remaining canonical conclusions.
Bounded Python Taylor and correction receipts are illustrative computations
only and provide no formal theorem evidence or new proof authority.
