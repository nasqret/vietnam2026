# Lecture 2 — Simple Calculations with the (Church) Lambda Calculus

> A hands-on lecture that turns the three-rule grammar of the untyped lambda calculus into a working programming language: students perform capture-avoiding substitution and beta/eta reduction by hand, state Church-Rosser, then build booleans, pairs, numerals, arithmetic (including Kleene's predecessor) and recursion via Y — every calculation reproduced live in the lambda_lab REPL.

## Learning objectives

- Read and manipulate untyped lambda-terms fluently: apply the left-associativity/scope-extends-right conventions, identify free vs. bound variables, use alpha-equivalence, and perform capture-avoiding substitution by hand, then confirm with the `lam` (tree + free-vars) and `reduce` REPL commands.
- Execute beta-reduction under both normal order (leftmost-outermost) and applicative order, recognise redexes and beta-normal forms, contrast beta with eta, and exhibit a non-terminating term (Omega) to show that normal forms need not exist and that strategy can matter.
- State the Church-Rosser (confluence) theorem and derive its corollary that beta-normal forms are unique up to alpha-equivalence, and explain why the leftmost-outermost strategy is normalising (Standardization / Leftmost Reduction theorem).
- Construct Church encodings from nothing but functions -- TRUE/FALSE/IF, AND/OR/NOT, PAIR/FST/SND, and the numerals n = lambda f x. f^n x -- and compute SUCC, PLUS, MULT, POW, verifying each with `church PLUS 2 3`, `church POW 2 5`, etc.
- Reconstruct Kleene's predecessor (the historically hard case), explain the pair-shifting trick, and derive truncated subtraction SUB, ISZERO, LEQ and EQ, checking them with `church PRED 3` and the `peano` command.
- Explain how the Y (fixed-point) combinator manufactures recursion without names via Y f = f (Y f), connect lambda-definability to Turing-completeness, and give the flavour of undecidability: beta-convertibility is not decidable (Church 1936).

## Prerequisites

- Comfort with functions as first-class objects and with reading recursive/inductive definitions (a term is a variable, or an abstraction, or an application).
- Lecture 1's Alligator Eggs metaphor (abstraction = hungry alligator, application = adjacency, variable = egg) -- this lecture formalises it.
- Basic mathematical logic and the idea of an equivalence relation / congruence; naive familiarity with 'computable function' helps for the finale.
- Ability to run `python -m lambda_lab` locally to follow the live REPL calculations.

## Syntax, binding, alpha-equivalence and capture-avoiding substitution

Establish the object language precisely and drill the one operation everything else rests on -- substitution done correctly. Do the classic capture example live: subst on (lambda y. x) with x := y must rename the bound y (the repo's `subst` in lc.py does exactly this). Introduce Barendregt's variable convention as the human shortcut. Free/bound and alpha are already the subject of notebook 02; this lecture makes substitution rigorous before any reduction.

**Key definitions**

- Terms: t ::= x | (lambda x. t) | (t t); application left-associative (a b c = (a b) c); abstraction body extends as far right as possible (lambda x. a b = lambda x. (a b)).
- Free variables FV(x)={x}, FV(lambda x. t)=FV(t)\{x}, FV(t u)=FV(t) u FV(u); closed term / combinator = term with FV empty.
- Alpha-equivalence: lambda x. t =_alpha lambda y. t[x:=y] when y not in FV(t); terms identified up to renaming of bound variables.
- Capture-avoiding substitution t[x:=u]: recurse structurally; under lambda y. t with y in FV(u), first alpha-rename y to a fresh variable, then substitute.

**Key results**

- Alpha-equivalence is an equivalence relation and a congruence (compatible with abstraction and application); we compute on alpha-equivalence classes.
- Substitution Lemma (Barendregt 2.1.16): if x != y and x not in FV(L), then M[x:=N][y:=L] = M[y:=L][x:=N[y:=L]].
- Barendregt Variable Convention: bound variables may be chosen distinct from free variables, making the naive substitution clause correct on suitably-named representatives.

## Beta-reduction, eta, normal forms and evaluation strategies

Beta is the sole computation rule. Define redex, one-step and many-step reduction, and convertibility. Show a divergent term. Contrast normal order vs applicative order and demonstrate that the choice is not cosmetic: (lambda x. y) Omega reduces to y under normal order but loops under applicative order. Note honestly that lambda_lab's engine implements ONLY beta in normal order (lc.py `_find_outermost_redex`/`beta_step`); eta must be discussed conceptually because `reduce` will not eta-contract lambda x. f x to f.

**Key definitions**

- Redex = an application (lambda x. t) u; the beta-rule (lambda x. t) u ->_beta t[x:=u].
- One-step ->_beta (contract any redex), many-step ->>_beta (reflexive-transitive closure), beta-convertibility =_beta (symmetric-transitive closure).
- Eta-rule: lambda x. (t x) ->_eta t when x not in FV(t) (extensionality of functions).
- Beta-normal form = term containing no redex; head normal form / weak head normal form.
- Normal order = leftmost-outermost redex first; applicative order = leftmost-innermost (eager, argument evaluated first).

**Key results**

- Omega = (lambda x. x x)(lambda x. x x) reduces in one step to itself: a term with no normal form (no terminating reduction).
- K Omega I pattern: (lambda x. y) Omega ->_beta y under normal order (one step), but never terminates under applicative order -- strategies are not interchangeable.
- Adding eta gives beta-eta-reduction; it remains confluent and encodes function extensionality; the REPL does not perform it, so lambda x. f x and f are only beta-eta-equal, not beta-equal.

## Confluence, Church-Rosser and normalisation

The theoretical spine that makes 'the normal form' well-defined and justifies the REPL's single normal-order strategy. Prove nothing in full (Barendregt/Hindley give the parallel-reduction proof) but state precisely and draw the diamond. Emphasise the crucial distinction students conflate: confluent but NOT strongly normalising -- Omega shows non-termination coexists with confluence.

**Key definitions**

- Confluence / Church-Rosser property of ->>_beta: a diamond that closes for arbitrary multi-step reductions.
- Local confluence (weak diamond); strong normalisation (every reduction path terminates) -- which the untyped calculus lacks.

**Key results**

- Church-Rosser theorem: if M ->>_beta P and M ->>_beta Q then there exists S with P ->>_beta S and Q ->>_beta S (SEP; Church & Rosser 1936).
- Corollary (uniqueness of normal forms): every term has at most one beta-normal form up to alpha-equivalence; consequently =_beta is non-trivial (e.g. K and I are not beta-equal because they are distinct normal forms).
- Standardization / Leftmost Reduction theorem (Curry-Feys 1958): if M has a normal form, the leftmost-outermost (normal-order) reduction reaches it -- so lambda_lab's default strategy is complete.
- The untyped calculus is confluent but not strongly normalising: Omega witnesses non-termination.

## Church booleans, conditionals and pairs

First encodings: data as its own eliminator. A boolean IS a chooser. Derive the connectives and observe the pleasant algebra (AND p q = p q p). Pairs reuse the same idea and are the tool needed for the predecessor. Reproduce with `church TRUE`, `church AND TRUE FALSE`, `church FST (PAIR 1 2)`. Flag the structural coincidence FALSE = ZERO = lambda x y. y -- the `church` command literally warns about this ambiguity when decoding.

**Key definitions**

- TRUE = lambda t f. t, FALSE = lambda t f. f; IF = lambda b t f. b t f.
- AND = lambda p q. p q p, OR = lambda p q. p p q, NOT = lambda p. p FALSE TRUE (repo also derives NAND, NOR, XOR, XNOR, IMPLIES).
- PAIR = lambda a b f. f a b, FST = lambda p. p TRUE, SND = lambda p. p FALSE.

**Key results**

- IF TRUE a b ->>_beta a and IF FALSE a b ->>_beta b (a boolean selects one branch).
- FST (PAIR a b) ->>_beta a and SND (PAIR a b) ->>_beta b (pairing/projection laws hold up to =_beta).
- Structural ambiguity: FALSE and the Church numeral ZERO are the same term lambda x y. y -- decoding a normal form to 'bool' vs 'numeral' is a heuristic, not intrinsic.

## Church numerals and arithmetic (SUCC, PLUS, MULT, POW)

A number is an iterator: n applies f n times. This single idea makes addition, multiplication and exponentiation astonishingly short (POW m n = n m). Give the iteration intuition (PLUS = do n then m more; MULT = iterate the n-fold-application m times). Verify live with `church PLUS 2 3` -> 5, `church MULT 3 4` -> 12, `church POW 2 5` -> 32; the REPL auto-decodes the numeral.

**Key definitions**

- Numeral: n-bar = lambda f x. f (f (... (f x)...)) with n applications; ZERO = lambda f x. x, ONE = lambda f x. f x.
- SUCC = lambda n f x. f (n f x); PLUS = lambda m n f x. m f (n f x); MULT = lambda m n f. m (n f); POW = lambda m n. n m; ISZERO = lambda n. n (lambda _. FALSE) TRUE.

**Key results**

- SUCC n-bar =_beta (n+1)-bar; PLUS m-bar n-bar =_beta (m+n)-bar; MULT m-bar n-bar =_beta (m*n)-bar; POW m-bar n-bar =_beta (m^n)-bar.
- Semantic core: a Church numeral n-bar realises the map f |-> f^n, and f^m . f^n = f^{m+n}, which is exactly why PLUS/MULT work.
- ISZERO ZERO =_beta TRUE and ISZERO (SUCC n) =_beta FALSE.

## The predecessor and subtraction -- the hard case

Historically the crux: Church believed the predecessor was undefinable until his student Kleene found it (the 'wisdom teeth trick'). Present Kleene's pair-shifting idea: carry a pair (i, i+1) and read off the first component. The repo's constant PRED = lambda n f x. n (lambda g h. h (g f)) (lambda u. x) (lambda u. u) is exactly this construction; SUB iterates PRED. Reproduce with `church PRED 3` -> 2 and `peano pred (succ (succ 0))`.

**Key definitions**

- Kleene predecessor (repo form): PRED = lambda n f x. n (lambda g h. h (g f)) (lambda u. x) (lambda u. u); the (lambda g h. h (g f)) is the pair-shift.
- SUB (monus) = lambda m n. n PRED m; LEQ = lambda m n. ISZERO (SUB m n); EQ = lambda m n. AND (LEQ m n) (LEQ n m).

**Key results**

- PRED ZERO =_beta ZERO and PRED (n+1)-bar =_beta n-bar (truncated at zero).
- SUB m-bar n-bar =_beta (m - n)-bar for m >= n and ZERO otherwise (natural-number monus), giving decidable LEQ and EQ.
- Historical fact: the definability of PRED (Kleene, c. 1932) was the breakthrough showing all recursive functions are lambda-definable; Church had thought it impossible.

## Recursion via Y, and a taste of undecidability

Names are absent, yet self-reference appears through a fixed-point combinator. Show two normal-order steps of Y g exposing g (...) -- the recursive call unfolding (notebook 06 does exactly this trace). Explain why eager languages need Z, and close with the meta-level payoff: lambda-definable = Turing-computable = general recursive, and beta-convertibility is undecidable. This is the bridge to Lectures on formalisation: computation-as-reduction is the same 'engine' that later powers proofs-as-programs.

**Key definitions**

- Fixed-point combinator: any F with F g =_beta g (F g) for all g.
- Y = lambda f. (lambda x. f (x x)) (lambda x. f (x x)) (Curry's paradoxical combinator).
- Z (call-by-value fixed point) = lambda f. (lambda x. f (lambda v. x x v)) (lambda x. f (lambda v. x x v)) -- eta-delays the recursive call.

**Key results**

- Fixed-Point Theorem (First Recursion Theorem): for every term F there exists X with F X =_beta X; witnessed by X = Y F, giving Y F =_beta F (Y F).
- Turing-completeness: the class of lambda-definable functions on the naturals equals the general recursive functions equals the Turing-computable functions (Church-Turing; Turing 1937).
- Undecidability (Church 1936): beta-convertibility =_beta is not decidable; equivalently, no lambda-term decides whether an arbitrary term has a normal form. (More generally every non-trivial beta-closed set of terms is undecidable -- the lambda-calculus form of Rice's theorem.)

## Pedagogical arc
"A ~90-minute session in five movements, each ending with a live lambda_lab check so nothing stays abstract. (0-10 min) Bridge from Lecture 1's Alligator Eggs: the hungry alligator = abstraction, families side by side = application, eggs = variables; write the three-rule grammar t ::= x | lambda x. t | t t and the two reading conventions, then run `lam \\x y. x (y z)` to show the AST, pretty-print and free variable z (notebook 02). (10-30 min) The one operation that matters: define free/bound, alpha-equivalence, and capture-avoiding substitution; do the capture trap on the board -- (lambda y. x)[x:=y] must NOT become lambda y. y -- and confirm with `reduce` / the subst demo (notebook 03). Introduce beta: redex, ->_beta, normal form; trace (lambda x. x x)(lambda y. y) live with `reduce`. (30-45 min) Non-termination and strategy: exhibit Omega, show it reduces to itself, contrast normal vs applicative order on (lambda x. y) Omega; then state Church-Rosser and its uniqueness corollary and the leftmost-reduction theorem that justifies why the REPL's single strategy is enough; stress confluent-but-not-terminating. Mention eta as extensionality and warn that `reduce` does beta only. (45-70 min) Programming with functions: booleans as choosers (`church TRUE`, `church AND TRUE FALSE`), pairs (`church FST (PAIR 1 2)`), then numerals as iterators and the arithmetic quartet SUCC/PLUS/MULT/POW (`church PLUS 2 3` -> 5, `church POW 2 5` -> 32) -- the whole `tour church` scripts this. Spend real time on the predecessor: tell the Kleene 'wisdom teeth' story, unfold the pair-shift, run `church PRED 3` and `peano pred (succ (succ 0))`, then SUB/LEQ/EQ. (70-88 min) Recursion without names: motivate with factorial, present Y, and trace Y g two steps to watch g (...) appear (notebook 06); note Z for eager evaluation. Close (88-90 min) with the meta-payoff: lambda-definable = general recursive = Turing-computable, and beta-convertibility is undecidable (Church 1936) -- three grammar rules give a Turing-complete language, and this same 'compute by reducing' engine reappears as 'prove by type-checking' in the formalisation lectures. Throughout, invite students to type each expression themselves in `python -m lambda_lab`; every board calculation has a one-line REPL twin."

## Connections to existing material
"This lecture IS the spine of notebooks 02-06 in falenty-2026/book/en/notebooks and is fully reproducible in lambda_lab. Direct reuse: notebook 02_lambda_basics.md (grammar, conventions, free_vars via `lam`); 03_substitution_reduction.md (capture-avoiding subst, beta_step, Omega, normal vs applicative order); 04_church_booleans.md (TRUE/FALSE/IF/AND/OR/NOT + try_decode_bool); 05_church_numerals.md (numerals + SUCC/PLUS/MULT/POW + try_decode_numeral); 06_recursion_and_Y.md (Y, Z, PRED via pairs, factorial). REPL commands to demo, all in lambda_lab/lab/commands: `lam`/`λ` (lam.py -- AST tree, pretty, free vars), `reduce` (reduce.py -- step-by-step normal-order beta trace with numeral/bool decode), `church` (church.py -- expands constants and digit literals, traces, decodes; also the FALSE=ZERO ambiguity note), and `peano` for pred/plus/times/sub/leq. The guided tours in tour.py are turnkey: `tour lambda` (lam/reduce/Omega/Y), `tour church` (TRUE, AND, NAND, 3, PLUS 2 3, EQ 2 2, FST (PAIR 1 2)), `tour peano`. All encodings live in lambda_lab/lab/church.py CONSTANTS (note the exact Kleene PRED = \\n f x. n (\\g h. h (g f)) (\\u. x) (\\u. u)); the engine is lambda_lab/lab/lc.py (subst with alpha-renaming, beta_step/_find_outermost_redex = leftmost-outermost, normalize, alpha_eq, free_vars). Forward links this lecture plants: notebook 07_peano_preview.md (the encoding satisfies Peano's axioms -> Lecture 3 on arithmetic/logic) and 08_curry_howard.md -> 09_lean_first_steps.md; for Lecture 6, the 'computation = reduction' idea here becomes 'proof = well-typed term' in the Lean4+Mathlib work in scratchpad/eml-formalization (README.md, DASHBOARD.md), where the same lambda-abstraction/application substrate underlies Lean's type theory. Structural/style continuity with scratchpad/classical-foundations-ann: per-part notebooks, embedded runnable code cells, dropdown exercises with solutions -- L2 should mirror that cadence."

## Artifact ideas

- **Lean 4** (easy): Define Church numerals polymorphically, `def Ch := (n : Nat) -> forall (a : Type), (a -> a) -> a -> a` (or `Ch := forall a, (a->a)->a->a`), with `czero`, `csucc`, `cplus`, `cmult`. Prove `cplus ctwo cthree = cfive` and `cmult ctwo cthree = csix` by `rfl`/`decide`, and prove the round-trip `toNat (fromNat n) = n` by induction. Shows the encoding computes and is faithful.
- **Lean 4** (medium): Define an inductive `Term` (Var/App/Lam with de Bruijn indices or named variables), a `subst` function, and single-step `beta : Term -> Term -> Prop`. Prove the concrete reduction `(lam (app (var 0) (var 0))) applied to id ->>_beta id` and prove Omega reduces to itself. Illustrates syntax + capture-avoiding substitution and non-termination inside a total prover.
- **Agda** (easy): Encode System-F-style Church booleans `CBool = forall {A} -> A -> A -> A` with `ctrue`, `cfalse`, `cand`, `cif`, and prove definitionally `cif ctrue a b == a` and `cand ctrue cfalse == cfalse` (via `refl`). A clean demonstration that 'data as its own eliminator' type-checks and computes.
- **Agda** (medium): Define `iterate : (A -> A) -> Nat -> A -> A` and prove the arithmetic laws behind Church encodings: `iterate f (m + n) x == iterate f m (iterate f n x)` and `iterate f (m * n) == iterate (iterate f n) m`, i.e. the semantic content of PLUS and MULT. Proof by induction on m/n; makes precise why the encodings are correct rather than merely checking small cases.
- **Rocq (Coq)** (hard): Formalise untyped terms with parallel (Tait/Martin-Lof) reduction and prove local confluence, or import the standard library development and prove the diamond property for parallel reduction, obtaining Church-Rosser for beta as a corollary. Directly formalises the lecture's central theorem.
- **Rocq (Coq)** (easy): Define SKI combinators and beta-like combinatory reduction and prove `S K K x = x` (i.e. SKK behaves as identity) and that `I`, `K`, `S` are definable, illustrating combinatory completeness -- a name-free counterpart to lambda-abstraction that the audience can check with `simpl`/`reflexivity`.
- **Mizar** (medium): In the Mizar/Tarski-Grothendieck set-theoretic setting, define the n-fold iterate `f^[n]` of a function f on a set and prove the functional-power laws `f^[m+n] = f^[m] * f^[n]` and `f^[m*n] = (f^[n])^[m]` (composition), which are the mathematical meaning of Church PLUS and MULT. Bridges the lambda-encoding to conventional set-theoretic functions in a very different foundational style.
- **Lean 4** (medium): Conceptual contrast artifact: attempt `def Y (f : T -> T) : T := f (Y f)` and observe Lean rejects it (no termination / not well-founded), then show the legitimate `Nat.rec`-based recursion instead. Demonstrates precisely why the untyped Y combinator lives outside a total type theory -- the boundary between Lecture 2's untyped world and Lecture 6's Lean.

## Pitfalls / misconceptions

- Treating substitution as blind textual replacement: (lambda y. x)[x := y] is NOT lambda y. y; the bound y must be alpha-renamed first (variable capture).
- Confusing alpha-equivalence (renaming bound variables, a syntactic identification) with beta-equality (computation). lambda x. x and lambda y. y are alpha-equal; they are not 'reduced' into each other.
- Believing every term has a normal form / that reduction always terminates. Omega diverges; the calculus is confluent but not strongly normalising.
- Assuming evaluation order is irrelevant. Applicative (eager) order loops on (lambda x. y) Omega and breaks the plain Y combinator, whereas normal order succeeds -- this is why lambda_lab uses normal order and why Python needs the Z variant.
- Misreading scope: lambda x. M N parses as lambda x. (M N), not (lambda x. M) N; and a b c means (a b) c. Wrong bracketing silently changes the term.
- Thinking the Church numeral 3 'is the number 3'. It is the iterator f |-> f^3; numbers here are higher-order functions, and arithmetic is composition of iterations.
- Forgetting the structural coincidence FALSE = ZERO = lambda x y. y (and TRUE = the FST selector). Decoding a normal form as 'bool' vs 'numeral' is a heuristic; `church` even prints an ambiguity warning.
- Expecting `reduce` to perform eta-contraction: it implements beta only, so lambda x. f x will NOT collapse to f in the REPL even though they are beta-eta-equal.
- Reading Y f = f (Y f) as if it terminates. Under naive expansion it unfolds forever; it only 'works' because a guard (like ISZERO) eventually selects a non-recursive branch, and only under a compatible reduction strategy.
- Assuming confluence implies termination. They are independent: Church-Rosser guarantees at most one normal form but says nothing about whether reduction halts.

## Canonical references

- H. P. Barendregt & E. Barendsen, Introduction to Lambda Calculus (revised edition, March 2000), free lecture notes. — <https://www.cse.chalmers.se/research/group/logic/TypesSS05/Extra/geuvers.pdf>  
  _The single best free, self-contained source at exactly this lecture's level: syntax, substitution, Church-Rosser, the encodings and fixed points, by the author of the canonical monograph. Ideal assigned reading._
- Peter Selinger, Lecture Notes on the Lambda Calculus, arXiv:0804.3434 (2008/2013). — <https://arxiv.org/abs/0804.3434>  
  _Clean, rigorous, freely available; treats the untyped calculus, Church-Rosser, and Church numerals carefully, and is the source for the Kleene predecessor 'wisdom teeth' history used in the undecidability segment._
- The Lambda Calculus, Stanford Encyclopedia of Philosophy (E. Barendsen et al.), current edition. — <https://plato.stanford.edu/entries/lambda-calculus/>  
  _Authoritative, citable statements of the Church-Rosser theorem and the consistency/uniqueness corollary; good for precise theorem wording on slides._
- H. P. Barendregt, The Lambda Calculus: Its Syntax and Semantics, Studies in Logic and the Foundations of Mathematics vol. 103, revised edition, North-Holland/Elsevier 1984. — <https://philpapers.org/rec/BARTLC>  
  _The definitive reference ('the bible', already cited in the book's Further Reading) for the Substitution Lemma, the variable convention, confluence proofs and standardization -- the depth backstop for every claim in this lecture._
- Raul Rojas, A Tutorial Introduction to the Lambda Calculus, arXiv:1503.09060 (2015). — <https://arxiv.org/abs/1503.09060>  
  _A short, concrete walk-through of exactly the encodings this lecture computes (booleans, numerals, arithmetic, recursion), matching the audience of newcomers; excellent handout companion to lambda_lab._
- Alonzo Church, An Unsolvable Problem of Elementary Number Theory, American Journal of Mathematics 58 (1936), pp. 345-363. — <https://ics.uci.edu/~lopes/teaching/inf212W12/readings/church.pdf>  
  _Primary source for the undecidability finale (undecidability of beta-convertibility and lambda-definability of effective computability); grounds the historical Church-Turing narrative._
- B. C. Pierce, Types and Programming Languages, MIT Press 2002 (ch. 5, the untyped lambda-calculus). — <https://www.cis.upenn.edu/~bcpierce/tapl/>  
  _The bridge forward: rigorous operational semantics and evaluation strategies, and the on-ramp to the typed calculus and Curry-Howard used in later lectures (L3/L6)._
- J.-Y. Girard, Y. Lafont, P. Taylor, Proofs and Types, Cambridge Tracts in TCS 7, 1989 (free PDF). — <http://www.paultaylor.eu/stable/prot.pdf>  
  _Canonical, freely available foundation for the proofs-as-programs theme this lecture seeds and Lecture 6 (Lean/Mathlib formalisation) cashes out._

## Volatile facts (sent to fact-check)

- Church-Rosser theorem (confluence of beta-reduction): if M ->>_beta P and M ->>_beta Q then there is S with P ->>_beta S and Q ->>_beta S; corollary: beta-normal forms are unique up to alpha-equivalence, so beta-convertibility is non-trivial (K and I are not identified). (src: https://plato.stanford.edu/entries/lambda-calculus/)
- The predecessor was historically the hard encoding: Church thought it undefinable until his student Kleene found it (the 'wisdom teeth trick') using pair-shifting; the repo encodes exactly this as PRED = lambda n f x. n (lambda g h. h (g f)) (lambda u. x) (lambda u. u). (src: https://arxiv.org/abs/0804.3434)
- Standardization / Leftmost Reduction theorem (Curry & Feys, 1958): if a term has a normal form, the leftmost-outermost (normal-order) reduction strategy reaches it -- justifying lambda_lab's single default strategy. (src: https://www.cse.chalmers.se/research/group/logic/TypesSS05/Extra/geuvers.pdf)
- Church (1936) proved that beta-convertibility is undecidable and that the lambda-definable numeric functions coincide with the effectively computable (general recursive) ones -- a pillar of the Church-Turing thesis. (src: https://ics.uci.edu/~lopes/teaching/inf212W12/readings/church.pdf)
- The Y (fixed-point) combinator Y = lambda f. (lambda x. f (x x))(lambda x. f (x x)) is due to Haskell Curry (his 'paradoxical combinator') and satisfies Y F =_beta F (Y F), giving recursion without names. (src: https://en.wikipedia.org/wiki/Fixed-point_combinator)
