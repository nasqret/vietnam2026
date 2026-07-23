# λ-calculus quick reference

```{admonition} How to use this page
:class: tip
Keep it open in a tab next to the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/).
Every entry has a lab command you can paste. If a command is new to you, `help <command>` in the lab
explains it with examples.
```

## Syntax and reading conventions

$$ t, u ::= x \;\mid\; \lam x.\,t \;\mid\; t\,u $$

| Convention | Meaning | So this… | …reads as |
|---|---|---|---|
| Application associates **left** | $f\,x\,y = (f\,x)\,y$ | `f x y` | `(f x) y` |
| λ-body extends **right** | $\lam x.\,x\,y = \lam x.\,(x\,y)$ | `\x. x y` | `λx. (x y)` — *not* `(λx. x) y` |
| Nested λ collapse | $\lam x.\lam y.\,t = \lam x\,y.\,t$ | `\x y. t` | `λx. λy. t` |

**Lab:** `lam \x y. x (y z)` — parse anything and see its free variables before you reduce it.

## The three conversions

| Rule | Statement | Side condition | Lab command |
|---|---|---|---|
| **α** (renaming) | $\lam x.\,t \;\equiv_\alpha\; \lam y.\,t[x{:=}y]$ | $y \notin \mathrm{FV}(t)$ | `alpha \x. x = \y. y` |
| **β** (computation) | $(\lam x.\,t)\,u \;\betared\; t[x{:=}u]$ | substitution must avoid capture | `reduce (\x. x x) (\y. y)` |
| **η** (extensionality) | $\lam x.\,t\,x \;\to_\eta\; t$ | $x \notin \mathrm{FV}(t)$ | `eta \x. f x` |

- A term with no β-redex is a **β-normal form**; by **Church–Rosser** it is unique up to α.
- **Normal order** (leftmost-outermost, what `reduce` shows — highlighted) finds a normal form
  whenever one exists.
- $\Omega = (\lam x.\,x\,x)(\lam x.\,x\,x)$ has no normal form; the lab reports its limit honestly.

```{admonition} The capture trap — the one substitution mistake everyone makes once
:class: warning
$(\lam y.\,x)[x{:=}y] \ne \lam y.\,y$. The incoming free $y$ would be **captured**. Rename first:
$\lam y.\,x \equiv_\alpha \lam y'.\,x$, then substitute: $\lam y'.\,y$ — a *constant* function, not
the identity. When in doubt: `debruijn` the term — nameless form makes capture impossible to miss.
```

## Church encodings

| Concept | Definition | Try it |
|---|---|---|
| `TRUE` | $\lam t\,f.\,t$ | `church TRUE` |
| `FALSE` | $\lam t\,f.\,f$ — *the same term as* `0` | `decode FALSE` |
| `IF` | $\lam b\,t\,f.\,b\,t\,f$ | `reduce IF TRUE a b` |
| `AND` / `OR` / `NOT` | $\lam p\,q.\,p\,q\,p$ · $\lam p\,q.\,p\,p\,q$ · $\lam p.\,p\,\mathtt{FALSE}\,\mathtt{TRUE}$ | `equiv NAND TRUE TRUE = NOT TRUE` |
| `PAIR` / `FST` / `SND` | $\lam a\,b\,f.\,f\,a\,b$ · $\lam p.\,p\,\mathtt{TRUE}$ · $\lam p.\,p\,\mathtt{FALSE}$ | `nf FST (PAIR a b)` |
| numeral $\overline{n}$ | $\lam f\,x.\,f^{\,n}\,x$ | `church 3` · `peano 3` |
| `SUCC` | $\lam n\,f\,x.\,f\,(n\,f\,x)$ | `nf SUCC 2` |
| `PLUS` / `MULT` | $\lam m\,n\,f\,x.\,m\,f\,(n\,f\,x)$ · $\lam m\,n\,f.\,m\,(n\,f)$ | `nf PLUS 2 3` |
| `POW` (η-long) | $\lam m\,n\,f\,x.\,n\,m\,f\,x$ | `nf POW 2 0` → `1` |
| `PRED` (Kleene) | $\lam n\,f\,x.\,n\,(\lam g\,h.\,h\,(g\,f))\,(\lam u.\,x)\,(\lam u.\,u)$ | `nf PRED 3` |
| `ISZERO` / `LEQ` / `EQ` | via `PRED` and `SUB` | `nf EQ 2 2` |

**Build your own:** `let COMPOSE = \f g x. f (g x)` — then `nf COMPOSE SUCC SUCC 1`. List with `defs`.

## Combinators

| Name | Term | Fact | Try it |
|---|---|---|---|
| **I** | $\lam x.\,x$ | identity; principal type $\alpha\to\alpha$ | `ch term \x. x` |
| **K** | $\lam x\,y.\,x$ | constant; type $\alpha\to\beta\to\alpha$ | `ch term \x. \y. x` |
| **S** | $\lam f\,g\,x.\,f\,x\,(g\,x)$ | with K generates everything; its type is a tautology | `ch term \f. \g. \x. f x (g x)` |
| **Y** | $\lam f.(\lam x.f(x\,x))(\lam x.f(x\,x))$ | $Y f \reduces f\,(Y f)$ — recursion from nothing | `church Y` |
| **Ω** | $(\lam x.\,x\,x)(\lam x.\,x\,x)$ | no normal form | `reduce OMEGA` |

## The typed layer at a glance

- **Typing judgment** $\Gamma \proves t : A$; STLC rules: variable, abstraction (→-intro),
  application (→-elim). Well-typed ⇒ strongly normalizing ⇒ `Y` and `Ω` are untypable.
- **Principal type** = the most general simple type; the lab's `ch term <t>` runs Algorithm W.
- **Inhabitation** = provability (intuitionistic, implicational): `ch type (P -> Q) -> P -> P` finds a
  witness; `ch type ((P -> Q) -> P) -> P` reports Peirce **uninhabited**.

## Curry–Howard in one table

| Logic | Type | Proof term | Lab |
|---|---|---|---|
| $A \To B$ | function | λ-abstraction | `prove P -> Q -> P` |
| $A \land B$ | product | pair | — (implicational builder) |
| $A \lor B$ | sum | tagged injection | see Lecture 3 |
| $\bot$ | empty type | *(no intro)* | `ch type P -> Q` (uninhabited) |
| proof normalization | β-reduction | `reduce` on the proof term | `qed` then `reduce` it |

**The full loop:** `prove (P -> Q) -> P -> Q` → `intro f` → `intro p` → `apply f` → `exact p` → `qed`
prints the λ-term **and** its principal type. That term *is* your proof.

## Lab commands by intent

| I want to… | Command |
|---|---|
| watch a computation, redex by redex | `reduce <t>` (or just type the term) |
| get the answer only | `nf <t>` · `decode <t>` |
| see lazy evaluation stop early | `whnf <t>` |
| check "are these the same?" | `alpha <t> = <u>` (spelling) · `equiv <t> = <u>` (value) |
| understand a binder puzzle | `debruijn <t>` · `alligators <t>` |
| apply extensionality | `eta <t>` |
| name my own construction | `let NAME = <t>` · `defs` |
| infer / inhabit types | `ch term <t>` · `ch type <T>` |
| prove a proposition interactively | `prove <prop>` … `qed` |
| be taught step by step | `tutorial` · `tour` · `quiz` |
| look something up | `kb <topic>` · `kb search <text>` · `help <command>` |
| jump to real Lean | `lean <name>` → Live Lean link |

## Top five mistakes (all fixable in one command)

1. **Reading `\x. x y` as `(λx. x) y`.** The body extends right. Check: `lam \x. x y`.
2. **Substituting into a binder that captures.** See the warning box above; check with `debruijn`.
3. **Thinking `alpha` computes.** It only renames. "Same value" is `equiv`.
4. **Expecting `FALSE` ≠ `0`.** Untyped Church encoding makes them the *same term*: `decode FALSE`.
5. **Expecting every term to finish.** `reduce OMEGA` — divergence is a feature, and the lab says so
   honestly instead of freezing.
