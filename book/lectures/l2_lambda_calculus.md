# Lecture 2 — Simple calculations with the Church $\lam$-calculus

```{admonition} Abstract
:class: tip
The untyped $\lam$-calculus is a complete model of computation built from one binding rule and one
reduction rule. We nail down **$\alpha$-equivalence**, **capture-avoiding substitution**, and
**$\beta/\eta$-reduction**, state **Church–Rosser**, and then *compute*: Church **booleans**,
**numerals**, arithmetic, the notorious **predecessor**, and the **$Y$-combinator**. Every calculation
here is reproducible in the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda).
```

## Learning objectives

- Reduce a $\lam$-term by hand in normal order and recognize a normal form.
- Explain $\alpha$-equivalence and why substitution must avoid variable capture.
- Encode `true`, `false`, `if`, numerals and `+`, `×` as pure $\lam$-terms.
- Explain how the $Y$-combinator produces recursion from nothing.

## Syntax

$$ t, u ::= x \mid \lam x.\,t \mid t\,u. $$
Application binds tighter than abstraction and associates to the left: $f\,x\,y = (f\,x)\,y$, and
$\lam x.\,x\,y = \lam x.\,(x\,y)$. A variable occurrence is **bound** if it lies under a $\lam$ that binds
it, else **free**; $\mathrm{FV}(t)$ collects the free ones.

## $\alpha$, substitution, $\beta$, $\eta$

- **$\alpha$-equivalence** — bound names don't matter: $\lam x.\,x \equiv_\alpha \lam y.\,y$.
- **Substitution** $t[x := u]$ replaces free $x$ by $u$, **renaming** bound variables when needed so no
  free variable of $u$ is captured. (Getting this right is the whole subtlety; the Lab's engine does it
  for you.)
- **$\beta$-reduction** — the one computational step:
  $$ (\lam x.\,t)\,u \betared t[x := u]. $$
- **$\eta$** — extensionality: $\lam x.\,(t\,x) \to_\eta t$ when $x \notin \mathrm{FV}(t)$.

A term with no $\beta$-redex is in **normal form**. **Normal-order** (leftmost-outermost) reduction
finds a normal form if one exists.

```{admonition} Church–Rosser (confluence)
:class: important
If $t \reduces u_1$ and $t \reduces u_2$, then there is a $v$ with $u_1 \reduces v$ and
$u_2 \reduces v$. **Consequence:** normal forms are unique up to $\alpha$. "The answer" is
well-defined, independent of the order you reduce in.
```

## Church booleans

$$ \mathtt{true} = \lam t\,f.\,t, \qquad \mathtt{false} = \lam t\,f.\,f, \qquad
   \mathtt{if} = \lam b\,t\,f.\,b\,t\,f. $$
Then $\mathtt{and} = \lam p\,q.\,p\,q\,p$, $\mathtt{or} = \lam p\,q.\,p\,p\,q$,
$\mathtt{not} = \lam p.\,p\,\mathtt{false}\,\mathtt{true}$.

## Church numerals

The numeral $\overline{n}$ is "apply $f$ to $x$, $n$ times":
$$ \overline{n} = \lam f\,x.\,\underbrace{f\,(f\,(\cdots(f}_{n}\,x)\cdots)). $$
$$ \mathtt{succ} = \lam n\,f\,x.\,f\,(n\,f\,x), \quad
   \mathtt{plus} = \lam m\,n\,f\,x.\,m\,f\,(n\,f\,x), \quad
   \mathtt{mult} = \lam m\,n\,f.\,m\,(n\,f). $$
Exponentiation is the tiny miracle $\mathtt{pow} = \lam m\,n.\,n\,m$.

The **predecessor** is famously awkward — Kleene's trick threads a pair "$(n, n{-}1)$" through:
$$ \mathtt{pred} = \lam n\,f\,x.\,n\,(\lam g\,h.\,h\,(g\,f))\,(\lam u.\,x)\,(\lam u.\,u). $$

## Recursion from nothing: the $Y$-combinator

There are no named self-references in the pure calculus, yet
$$ Y = \lam f.\,(\lam x.\,f\,(x\,x))\,(\lam x.\,f\,(x\,x)) $$
satisfies $Y\,f \reduces f\,(Y\,f)$ — a fixed point of *any* $f$. That single line is enough to define
factorial, and it is why the untyped calculus is Turing-complete (and why $\Omega = (\lam x.\,x\,x)(\lam
x.\,x\,x)$ has **no** normal form).

```{admonition} Run it
:class: seealso
In the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda):
`reduce AND TRUE FALSE`, `nf PLUS 2 3`, `nf MULT 2 3`, `church SUCC`, and
`reduce (\x. x x) (\y. y)`. Type `tour` for a 60-second guided version.
```

## References

Barendregt, *The Lambda Calculus* (Ch. 2–3, 6); Sørensen–Urzyczyn (Ch. 1); the course's own
[falenty-2026 λ-calculus book](https://github.com/nasqret/falenty-2026/tree/main/book/en).
```{note}
Deeper worked reductions, the Kleene predecessor in slow motion, and $\eta$ vs $\beta$ examples land as
the chapter grows.
```
