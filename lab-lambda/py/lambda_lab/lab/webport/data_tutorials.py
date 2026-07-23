"""Frozen tutorial chapters for the browser build of Lambda Lab.

Generated from the desktop data files ``lambda_lab/lab/tutorial/data/*.json``
(12 chapters). The browser build is English-only, so only the English
strings were frozen (with Polish used as a fallback where an English field
was empty). Do not edit by hand beyond small wording fixes.
"""

CHAPTERS = [{'slug': 'gauss_sum',
  'order': 1,
  'title': "Gauss's sum: 1 + 2 + ... + n",
  'summary': 'Induction over a finite range: we prove 2*(0+1+...+n) = n*(n+1). A '
             "schoolbook identity reshaped through Lean's term-level lens.",
  'duration_min': 12,
  'steps': [{'kind': 'narrative',
             'title': 'The Gauss anecdote',
             'body': 'Young Karl Friedrich Gauss was nine when his teacher, J.G. '
                     'Buttner, asked the class to sum the integers from 1 to 100 - '
                     'mostly to buy himself a quiet hour. Gauss glanced at the task, '
                     'raised one eyebrow, and handed in his slate with the answer: '
                     '5050. The idea is plain enough: pairing 1 + 100, 2 + 99, 3 + 98, '
                     '..., 50 + 51 gives 50 pairs, each summing to 101. So 50 * 101 = '
                     '5050. No magic, only symmetry. We are about to relive the same '
                     'identity through the lens of Lean and induction.'},
            {'kind': 'command',
             'label': 'A short walk through Church-style counting for context.',
             'command': 'tour church'},
            {'kind': 'lean_walk',
             'label': 'Inductive proof in Lean',
             'narrative': 'The base case is closed by `simp` (the sum over `range 1` '
                          'is just 0). In the inductive step `Finset.sum_range_succ` '
                          'expands the sum over `range (n+1)` into the previous one '
                          'plus `n`. We multiply through by 2, plug in the hypothesis '
                          '`ih`, and a final `ring` settles the equation.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'open Finset\n'
                            '\n'
                            'theorem tutorial_gauss_sum (n : Nat) :\n'
                            '    2 * (∑ k ∈ Finset.range (n+1), k) = n * (n + 1) := '
                            'by\n'
                            '  induction n with\n'
                            '  | zero => simp\n'
                            '  | succ n ih =>\n'
                            '      rw [Finset.sum_range_succ, Nat.mul_add]\n'
                            '      rw [ih]\n'
                            '      ring\n',
             'name': 'tutorial_gauss_sum'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_01_gauss',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 1}},
            {'kind': 'kb',
             'label': 'Where does this story come from?',
             'topic': 'history'},
            {'kind': 'narrative',
             'title': 'What stays with you after the chapter',
             'body': 'The takeaway: induction in Lean is not an incantation - it is '
                     'two obligations (base case and step n -> n+1) packaged inside '
                     '`induction n with`. Everything else is algebraic plumbing: '
                     "`Finset.sum_range_succ`, `ring`, and our own `rw`. Gauss's sum "
                     'was just a vehicle.'}]},
 {'slug': 'sqrt2_irrational',
  'order': 2,
  'title': 'The square root of 2 is irrational',
  'summary': 'The archetypal proof by contradiction: we extract a contradiction from '
             'sqrt(2) = p/q. Mathlib delivers it as a corollary of '
             '`Nat.Prime.irrational_sqrt`.',
  'duration_min': 14,
  'steps': [{'kind': 'narrative',
             'title': 'Scandal in the Pythagorean school',
             'body': 'In the Pythagorean school everything was supposed to be '
                     'expressible as a ratio of integers. Measure, harmony, justice - '
                     'all rational. So the disciple who is said to have first proven '
                     'that the diagonal of a unit square cannot be such a ratio met a '
                     'stern example: legend speaks of Hippasus of Metapontum drowned '
                     'at sea. Did it really happen that way - we cannot say. What we '
                     'do know is that the proof attributed to him still sits at the '
                     'foundations of mathematics: the square root of two is not a '
                     'ratio of two natural numbers. The starting point is a '
                     'contradiction: assume it is, and follow the consequences to the '
                     'absurd.'},
            {'kind': 'command',
             'label': 'A short logical warm-up - de Morgan in our playground.',
             'command': 'prove demorgan1'},
            {'kind': 'lean_walk',
             'label': 'A tiny lemma: 2 divides n iff n = 2k',
             'narrative': "Looks like a tautology, and in Lean's library it almost is: "
                          '`2 ∣ n` unfolds to exactly `∃ k, n = 2 * k`. The '
                          '`constructor` tactic splits the iff into the two '
                          'directions, and each is closed by the same witness `k`.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'theorem tutorial_two_dvd_iff (n : Nat) :\n'
                            '    2 ∣ n ↔ ∃ k, n = 2 * k := by\n'
                            '  constructor\n'
                            '  · intro h; exact h\n'
                            '  · intro ⟨k, hk⟩; exact ⟨k, hk⟩\n',
             'name': 'tutorial_two_dvd_iff'},
            {'kind': 'lean_walk',
             'label': 'The main result via Mathlib',
             'narrative': 'In Mathlib the Hippasus argument lives as '
                          '`Nat.Prime.irrational_sqrt`. Hand it any prime (here: 2) '
                          'and the rest is a careful coercion via `exact_mod_cast`.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'theorem tutorial_sqrt2_irrational :\n'
                            '    Irrational (Real.sqrt 2) := by\n'
                            '  exact_mod_cast Nat.Prime.irrational_sqrt (p := 2) '
                            'Nat.prime_two\n',
             'name': 'tutorial_sqrt2_irrational'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_02_sqrt2',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 2}},
            {'kind': 'kb',
             'label': 'Proofs by contradiction - background',
             'topic': 'proof-theory'}]},
 {'slug': 'pigeonhole',
  'order': 3,
  'title': 'Pigeonhole on a finite set',
  'summary': 'Three pigeons, two pigeonholes - two birds must share. We formalise the '
             'concrete case (Fin 3 -> Fin 2) and point at the Mathlib general form via '
             '`Fintype.card_le_of_injective`.',
  'duration_min': 12,
  'steps': [{'kind': 'narrative',
             'title': 'Three pigeons, two pigeonholes',
             'body': 'Picture three birds landing in two nesting holes. Whatever the '
                     'third bird chooses, one of the holes ends up with two tenants. '
                     'That is the pigeonhole principle: if n+1 objects must fit into n '
                     'bins, two of them share a bin. Dirichlet used it for number '
                     'theory; we use it as a compact combinatorial argument.'},
            {'kind': 'command',
             'label': "Let's look at case-splitting tactics.",
             'command': 'ch tactic cases'},
            {'kind': 'lean_walk',
             'label': 'Concrete instance: Fin 3 -> Fin 2',
             'narrative': 'Strategy: assume there is no clash. Then `f` would be '
                          'injective and `Fintype.card_le_of_injective` gives 3 ≤ 2 - '
                          'a contradiction `simp` can spot. The full general form in '
                          'Mathlib is `Finset.exists_ne_map_eq_of_card_lt_of_maps_to` '
                          '(see `Mathlib.Combinatorics.Pigeonhole`).',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'theorem tutorial_pigeonhole_3_2 (f : Fin 3 → Fin 2) :\n'
                            '    ∃ x y : Fin 3, x ≠ y ∧ f x = f y := by\n'
                            '  classical\n'
                            '  by_contra h\n'
                            '  push_neg at h\n'
                            '  have hinj : Function.Injective f := by\n'
                            '    intro x y hxy\n'
                            "    by_contra hxy'\n"
                            "    exact (h x y hxy') hxy\n"
                            '  have : Fintype.card (Fin 3) ≤ Fintype.card (Fin 2) :=\n'
                            '    Fintype.card_le_of_injective f hinj\n'
                            '  simp at this\n',
             'name': 'tutorial_pigeonhole_3_2'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_03_pigeonhole',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 3}},
            {'kind': 'kb',
             'label': 'Related reading in the knowledge base',
             'topic': 'combinators'}]},
 {'slug': 'infinitude_primes',
  'order': 4,
  'title': 'Infinitude of primes (Euclid)',
  'summary': 'For every N there exists a prime larger than N. In Lean we lean on '
             "Mathlib's `Nat.exists_infinite_primes` and pull a tight little corollary "
             'out of it.',
  'duration_min': 13,
  'steps': [{'kind': 'narrative',
             'title': 'A proof that has worked for 23 centuries',
             'body': 'In Book IX of the Elements, Euclid noticed that if there were '
                     'only finitely many primes - p1, p2, ..., pk - then the number N '
                     '= p1 * p2 * ... * pk + 1 would not be divisible by any of them. '
                     'And since N > 1, it has some prime divisor not on the list. '
                     'Contradiction. Twenty-three centuries later Lean encodes the '
                     'same idea as `Nat.exists_infinite_primes` in '
                     '`Mathlib.Data.Nat.Prime`. We carve a tight corollary off of it '
                     'for didactic use.'},
            {'kind': 'command',
             'label': 'Let Aristotle sketch the proof plan informally.',
             'command': 'arist informal infinitude of primes'},
            {'kind': 'lean_walk',
             'label': 'Corollary: above every N there is a prime',
             'narrative': '`Nat.exists_infinite_primes` hands us a prime p with `N + 1 '
                          '≤ p`. To convert this to the strict inequality `N < p`, we '
                          'hand the hypotheses to `omega`. Shorter than two prose '
                          'sentences.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'theorem tutorial_prime_above (N : Nat) :\n'
                            '    ∃ p, N < p ∧ p.Prime := by\n'
                            '  obtain ⟨p, hN, hp⟩ := Nat.exists_infinite_primes (N + '
                            '1)\n'
                            '  exact ⟨p, by omega, hp⟩\n',
             'name': 'tutorial_prime_above'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_04_primes',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 4}},
            {'kind': 'kb',
             'label': "Why is this proof considered 'the most beautiful in "
                      "mathematics'?",
             'topic': 'history'}]},
 {'slug': 'am_gm_two',
  'order': 5,
  'title': 'AM-GM for two non-negative reals',
  'summary': 'The classical inequality 2*sqrt(a*b) <= a + b for a, b ≥ 0. Lean kills '
             'it with one `nlinarith` call given three algebraic hints.',
  'duration_min': 11,
  'steps': [{'kind': 'narrative',
             'title': 'Arithmetic mean versus geometric mean',
             'body': "For two non-negative reals the 'arithmetic mean' (a+b)/2 is "
                     "never below the 'geometric mean' sqrt(a*b). It is one of the "
                     'most cited facts in elementary analysis. The trick: expanding (a '
                     '- b)^2 ≥ 0 yields a^2 - 2*a*b + b^2 ≥ 0, i.e. a^2 + b^2 ≥ 2*a*b. '
                     'Adding 2*a*b on both sides gives (a+b)^2 ≥ 4*a*b, hence a + b ≥ '
                     '2*sqrt(a*b).'},
            {'kind': 'command',
             'label': 'A short walk through the `linarith` tactic.',
             'command': 'ch tactic linarith'},
            {'kind': 'lean_walk',
             'label': 'Lean: 2*sqrt(a*b) <= a + b',
             'narrative': 'We feed `nlinarith` four algebraic hints: the squared '
                          'difference is non-negative, the squared root is '
                          'non-negative, `Real.sq_sqrt` rewrites (sqrt(a*b))^2 to a*b, '
                          'and `Real.sqrt_nonneg` keeps the root above zero. Given '
                          'that linear-with-quadratic-witnesses mix, `nlinarith` '
                          'closes the goal.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'theorem tutorial_am_gm_two (a b : ℝ) (ha : 0 ≤ a) (hb : 0 '
                            '≤ b) :\n'
                            '    2 * Real.sqrt (a * b) ≤ a + b := by\n'
                            '  have hab : 0 ≤ a * b := mul_nonneg ha hb\n'
                            '  nlinarith [sq_nonneg (a - b), sq_nonneg (Real.sqrt (a * '
                            'b)),\n'
                            '             Real.sq_sqrt hab, Real.sqrt_nonneg (a * '
                            'b)]\n',
             'name': 'tutorial_am_gm_two'},
            {'kind': 'quiz_checkpoint', 'bundle': 'tutorial_05_amgm', 'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 5}},
            {'kind': 'kb',
             'label': 'How does Mathlib organise inequalities?',
             'topic': 'mathlib'}]},
 {'slug': 'heroic_finset_sum',
  'order': 6,
  'title': "Heroic chapter: Mathlib's Finset.sum_range_id",
  'summary': "We return to Gauss's sum, but this time we touch Mathlib's "
             'production-grade lemma `Finset.sum_range_id`. We show a one-line '
             'corollary and walk through the elaborated proof term.',
  'duration_min': 12,
  'steps': [{'kind': 'narrative',
             'title': 'From textbook to production',
             'body': "In chapter 1 we wrote Gauss's sum proof by hand. Mathlib already "
                     'has a finished version: `Finset.sum_range_id` says `(∑ k ∈ range '
                     'n, k) = n * (n - 1) / 2`. It is foundational enough that many '
                     "places in Mathlib's algebra layer rely on it. Our goal is to "
                     'peek at what a production-grade lemma looks like - and to see '
                     'how a single `rw` lets us build a small wrapper over it.'},
            {'kind': 'command',
             'label': 'Let Aristotle add an informal commentary.',
             'command': 'arist informal Finset.sum_range_id and the closed-form Gauss '
                        'sum'},
            {'kind': 'lean_walk',
             'label': 'Corollary: harvesting the closed form from Mathlib',
             'narrative': 'The entire proof is one `rw [Finset.sum_range_id]`. Lean '
                          'unfolds the lemma, matches the sides, and closes. That '
                          'terse stylistic standard is what production Mathlib looks '
                          'like - the contributions you make there should aim for '
                          'one-liners like this.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'open Finset\n'
                            '\n'
                            'theorem tutorial_heroic_gauss (n : Nat) :\n'
                            '    (∑ k ∈ Finset.range n, k) = n * (n - 1) / 2 := by\n'
                            '  rw [Finset.sum_range_id]\n',
             'name': 'tutorial_heroic_gauss'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_06_heroic',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 6}},
            {'kind': 'kb',
             'label': 'Mathlib - how to read the library',
             'topic': 'mathlib'}]},
 {'slug': 'bezout',
  'order': 7,
  'title': "Bezout's identity for natural numbers",
  'summary': 'The greatest common divisor of two numbers can always be written as an '
             'integer linear combination: gcd(a,b) = a*x + b*y. In Mathlib this '
             'identity is shipped as `Nat.gcd_eq_gcd_ab`.',
  'duration_min': 13,
  'steps': [{'kind': 'narrative',
             'title': 'An algorithm that has lived for 2300 years',
             'body': 'Euclid in Book VII of the Elements describes how to find the '
                     'greatest common divisor of two numbers by repeated subtraction. '
                     'Read backwards, the same procedure shows something more: that '
                     'divisor can always be written as an organised sum of the '
                     'original numbers. For instance gcd(12, 18) = 6 - and indeed 6 = '
                     "12 * (-1) + 18 * 1. That one step beyond Euclid is Bezout's "
                     'identity. Etienne Bezout proved it in the eighteenth century for '
                     'polynomials, but the arithmetic version was known much earlier. '
                     'The crucial point: the proof of Bezout is not abstract - it is a '
                     'concrete algorithm that returns the coefficients x, y. Mathlib '
                     'carries it as `Nat.xgcd` (the extended Euclidean algorithm).'},
            {'kind': 'command',
             'label': 'Tactic cheat-sheet: `rw` and `exact` in a single breath.',
             'command': 'ch tactic exact'},
            {'kind': 'lean_walk',
             'label': 'Bezout in one line: a Mathlib citation',
             'narrative': 'The real work lives in `Nat.gcd_eq_gcd_ab`. The functions '
                          '`Nat.gcdA` and `Nat.gcdB` are constructive witnesses: while '
                          'computing `Nat.xgcd a b`, Lean produces not just the gcd '
                          'but also the coefficient pair x, y that certifies the '
                          'identity. The lemma `Nat.gcd_eq_gcd_ab` states only that '
                          'the gcd value is in fact that linear combination. Our proof '
                          'cites the ready-made result in a single line - the same '
                          'one-liner discipline you saw with `Finset.sum_range_id` in '
                          'chapter 6.',
             'lean_source': 'import Mathlib.Tactic\n'
                            'import Mathlib.Data.Nat.GCD.Basic\n'
                            '\n'
                            'theorem tutorial_bezout (a b : Nat) :\n'
                            '    Nat.gcd a b = a * Nat.gcdA a b + b * Nat.gcdB a b := '
                            'by\n'
                            '  exact Nat.gcd_eq_gcd_ab a b\n',
             'name': 'tutorial_bezout'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_07_bezout',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 7}},
            {'kind': 'kb',
             'label': 'Where to look in Mathlib for Bezout-style identities?',
             'topic': 'mathlib'},
            {'kind': 'narrative',
             'title': 'Why this identity carries so much weight',
             'body': "Bezout's identity is the bridge between divisibility and integer "
                     'combinations. From it follows the foundational fact of number '
                     'theory: if a prime p divides a product a*b, then it divides a or '
                     'b. From it also follows that whenever gcd(a, n) = 1, the element '
                     'a has a multiplicative inverse modulo n. That is why the whole '
                     'RSA cryptosystem begins with this very line - without Bezout '
                     'there would be no algorithm for key generation.'}]},
 {'slug': 'cauchy_schwarz',
  'order': 8,
  'title': 'Cauchy-Schwarz inequality for two reals',
  'summary': 'We prove the classical form (a*x + b*y)^2 ≤ (a^2 + b^2) * (x^2 + y^2). '
             'In Lean it takes a single witness for `nlinarith`: the squared '
             'determinant `a*y - b*x`.',
  'duration_min': 11,
  'steps': [{'kind': 'narrative',
             'title': 'The geometric seed of Cauchy-Schwarz',
             'body': 'Two vectors in the plane, (a, b) and (x, y), have a scalar '
                     'product a*x + b*y. When the vectors are parallel, their scalar '
                     'product equals the product of their lengths - that is its '
                     'greatest possible value. Otherwise it is smaller. Cauchy-Schwarz '
                     'states this numerically: the square of the scalar product cannot '
                     'exceed the product of the squared norms. Classically: |<u, v>| ≤ '
                     '||u|| * ||v||. In numbers: (a*x + b*y)^2 ≤ (a^2 + b^2) * (x^2 + '
                     "y^2). Cauchy's loaded-trinomial argument from 1821 runs like "
                     'this: consider the function t -> (a*t - x)^2 + (b*t - y)^2, '
                     'non-negative as a sum of squares, and as a degree-two polynomial '
                     'in t it must have non-positive discriminant. That discriminant '
                     'is exactly the Cauchy-Schwarz inequality.'},
            {'kind': 'command',
             'label': 'A walk through the `nlinarith` tactic - the one that closes our '
                      'goal today.',
             'command': 'ch tactic linarith'},
            {'kind': 'lean_walk',
             'label': 'Lean: one line, one witness',
             'narrative': 'Everything rests on the determinant `a*y - b*x`. '
                          'Algebraically: expanding (a*x + b*y)^2 and (a^2 + b^2)*(x^2 '
                          '+ y^2), the difference between the two sides is exactly '
                          '(a*y - b*x)^2. `sq_nonneg (a*y - b*x)` tells `nlinarith` '
                          'that this square is non-negative - and `nlinarith` does the '
                          'rest, including multiplying out every term.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'theorem tutorial_cauchy_schwarz_two (a b x y : ℝ) :\n'
                            '    (a*x + b*y)^2 ≤ (a^2 + b^2) * (x^2 + y^2) := by\n'
                            '  nlinarith [sq_nonneg (a*y - b*x)]\n',
             'name': 'tutorial_cauchy_schwarz_two'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_08_cauchy_schwarz',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 8}},
            {'kind': 'kb',
             'label': 'Cauchy-Schwarz in Mathlib - for inner products in Hilbert '
                      'spaces',
             'topic': 'mathlib'}]},
 {'slug': 'fibonacci',
  'order': 9,
  'title': 'The Fibonacci recurrence',
  'summary': 'We prove the classical recurrence fib(n+2) = fib(n) + fib(n+1) as a '
             'one-liner backed by `Nat.fib_add_two` from Mathlib. Along the way we '
             'recall why `decide` does not finish this for arbitrary n.',
  'duration_min': 12,
  'steps': [{'kind': 'narrative',
             'title': 'The rabbit sequence that hides in plain sight',
             'body': "Leonardo of Pisa, known as Fibonacci, in his 1202 book 'Liber "
                     "abaci' poses the question: how many pairs of rabbits will we "
                     'have after n months, if each pair only starts breeding in its '
                     'second month? The answer is the sequence 1, 1, 2, 3, 5, 8, 13, '
                     '21, ... The rules: fix the first two values, then every next one '
                     'is the sum of the previous two. That same principle stands '
                     "behind a cascade of ideas - from Pascal's triangle through "
                     'divide-and-conquer algorithms to the golden ratio φ = (1 + '
                     'sqrt(5))/2. In Mathlib the function `Nat.fib` is defined by '
                     'exactly this recurrence, so the lemma `Nat.fib_add_two` is '
                     'almost tautological - but neatly packaged and ready for `rw`.'},
            {'kind': 'command',
             'label': 'A look at the `induction` tactic we use in the second step.',
             'command': 'ch tactic induction'},
            {'kind': 'lean_walk',
             'label': 'The recurrence in Lean: two lines',
             'narrative': 'All the work sits in `Nat.fib_add_two`: `Nat.fib (n + 2) = '
                          'Nat.fib n + Nat.fib (n + 1)`. Lean does not need induction '
                          'here, because the definition of `Nat.fib` already covers '
                          'the `succ (succ n)` case - the lemma just exposes it '
                          'cleanly. Why not `decide`? Because `decide` likes concrete '
                          'numbers; here n is a variable, so the computation tree is '
                          'infinite.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'theorem tutorial_fib_recurrence (n : Nat) :\n'
                            '    Nat.fib (n + 2) = Nat.fib n + Nat.fib (n + 1) := by\n'
                            '  rw [Nat.fib_add_two]\n',
             'name': 'tutorial_fib_recurrence'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_09_fibonacci',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 9}},
            {'kind': 'kb',
             'label': 'A history of the Fibonacci sequence',
             'topic': 'history'},
            {'kind': 'narrative',
             'title': 'What you walk away with',
             'body': "A lemma with 'ancient ring' is in Mathlib just a plain neutral "
                     "formula. Fibonacci's recurrence is not a metaphor - it is an "
                     'equation between two function values, exactly as testable as '
                     '`Nat.add_succ`. That is the strength of formalisation: phrases '
                     "like 'obvious from the definition' stop being soft handwaves and "
                     'become a lemma you `rw` with.'}]},
 {'slug': 'wilson_small',
  'order': 10,
  'title': "Wilson's theorem - small cases: p = 5",
  'summary': 'A classical fact: for a prime p we have (p-1)! ≡ -1 (mod p). The general '
             'proof is non-trivial, but for a concrete prime everything is settled by '
             '`decide` in one line. We show p = 5.',
  'duration_min': 10,
  'steps': [{'kind': 'narrative',
             'title': 'A theorem noticed before anyone could prove it',
             'body': 'John Wilson, a Cambridge student, in 1770 noticed the '
                     'regularity: for every prime p the product 1 * 2 * ... * (p-1) '
                     'leaves a remainder of p - 1 when divided by p. Wilson could not '
                     'prove this; Lagrange did so a year later. In modular language: '
                     '(p-1)! ≡ -1 (mod p). Concretely: for p = 2 we have 1 ≡ -1 ≡ 1 '
                     '(mod 2). For p = 3 we have 2 ≡ -1 ≡ 2 (mod 3). For p = 5 we have '
                     '24 ≡ -1 ≡ 4 (mod 5). For p = 7 we have 720 ≡ -1 ≡ 6 (mod 7). The '
                     'general proof rests on the fact that in the multiplicative group '
                     '(Z/pZ)* an element equals its inverse iff it equals ±1. We will '
                     'show a weaker but utterly concrete version: a single case p = 5 '
                     'that `decide` will close for us in one shot.'},
            {'kind': 'command',
             'label': 'A short walk through `decide` - why it suffices here.',
             'command': 'ch tactic decide'},
            {'kind': 'lean_walk',
             'label': 'Lean: Wilson for p = 5 by one `decide`',
             'narrative': 'There is no algebra here. `decide` reduces both sides to '
                          'concrete natural numbers: the left side is 4! % 5 = 24 % 5 '
                          '= 4, the right side is 5 - 1 = 4. Lean checks 4 = 4 and '
                          'finishes. The whole trick: we phrased the task in a form '
                          'Lean can compute for us.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'theorem tutorial_wilson_5 :\n'
                            '    Nat.factorial (5 - 1) % 5 = 5 - 1 := by\n'
                            '  decide\n',
             'name': 'tutorial_wilson_5'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_10_wilson_small',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 10}},
            {'kind': 'kb',
             'label': 'Decisions by enumeration - the limits of `decide`',
             'topic': 'proof-theory'}]},
 {'slug': 'euler_identity',
  'order': 11,
  'title': "Euler's identity: e^(iπ) + 1 = 0",
  'summary': 'An identity that holds 0, 1, e, π and i in a single formula. Mathlib '
             'already has `Complex.exp_pi_mul_I`, and we add a `ring` step to move '
             'from `exp(πi) = -1` to `exp(πi) + 1 = 0`.',
  'duration_min': 13,
  'steps': [{'kind': 'narrative',
             'title': 'Five constants in one equation',
             'body': "Euler's identity packs into a single line the five most "
                     'important constants of mathematics: 0, 1, the base of the '
                     'natural logarithm e, the geometric constant π and the imaginary '
                     "unit i from the complex numbers. In a 2004 'Physics World' poll "
                     "it was voted 'the most beautiful formula in mathematics'. How "
                     'does one understand it? The fastest route: the definition '
                     '`Complex.exp z = sum n in N, z^n / n!` as a power series. '
                     'Splitting e^(iπ) into real and imaginary parts we recognise the '
                     "cosine and sine series: e^(iθ) = cos θ + i*sin θ (Euler's "
                     'formula). For θ = π we have cos π = -1, sin π = 0, so e^(iπ) = '
                     '-1. Moving the one across yields the headline equation. In '
                     'Mathlib all this work lives inside the lemma '
                     '`Complex.exp_pi_mul_I`. We only cite it and add `ring` to turn '
                     '`= -1` into `+ 1 = 0`.'},
            {'kind': 'command',
             'label': 'A short walk through `ring` - the tactic that closes our proof.',
             'command': 'ch tactic ring'},
            {'kind': 'lean_walk',
             'label': 'Lean: two steps, two borrowed results',
             'narrative': 'The first line, `rw [Complex.exp_pi_mul_I]`, substitutes '
                          'the value `-1` for `exp(π * i)`. The goal becomes `(-1) + 1 '
                          '= 0`. The second line `ring` settles an algebraic truth in '
                          "the complex ring. The full Mathlib proof of Euler's "
                          'identity runs over several hundred lines (complex analysis, '
                          'power series, the definitions of cos and sin), but for us '
                          'it is two lines, because Mathlib has done the rest already.',
             'lean_source': 'import Mathlib.Tactic\n'
                            'import Mathlib.Analysis.SpecialFunctions.Complex.Circle\n'
                            '\n'
                            'open Complex Real\n'
                            '\n'
                            'theorem tutorial_euler_identity :\n'
                            '    Complex.exp (Real.pi * Complex.I) + 1 = 0 := by\n'
                            '  rw [Complex.exp_pi_mul_I]\n'
                            '  ring\n',
             'name': 'tutorial_euler_identity'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_11_euler_identity',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 11}},
            {'kind': 'kb',
             'label': "A history of Euler's identity",
             'topic': 'history'},
            {'kind': 'narrative',
             'title': 'What you walk away with',
             'body': 'The second and third floors of Mathlib (complex analysis, the '
                     'geometry of the torus T = {z : ‖z‖ = 1}) rest on lemmas like '
                     '`Complex.exp_pi_mul_I`. The value of such identities is that '
                     'they are at once a result and a hinge - they can be slotted into '
                     'infinitely many contexts. Train yourself to notice in Mathlib '
                     "not only 'what' is being proved, but also 'where' it will later "
                     'be cited - that is the compositional design of Mathlib.'}]},
 {'slug': 'heroic_ii',
  'order': 12,
  'title': 'Heroic chapter II: divisors of a prime',
  'summary': "We return to Mathlib's production style. Every divisor of a prime p "
             'equals 1 or p - that is the very content of being prime. Mathlib carries '
             'this as `Nat.Prime.eq_one_or_self_of_dvd`, and we wrap it in a '
             'one-liner.',
  'duration_min': 13,
  'steps': [{'kind': 'narrative',
             'title': "What 'prime' really means",
             'body': 'The definition in Mathlib: `p.Prime ↔ 2 ≤ p ∧ ∀ m, m ∣ p → m = 1 '
                     '∨ m = p`. Translating: p is prime if (a) it is at least 2 and '
                     '(b) its only divisors are 1 and itself. That second clause is '
                     'exactly what `Nat.Prime.eq_one_or_self_of_dvd` packages. The '
                     'lemma is a piece of inference - not the definition itself. Lean '
                     'does not force us to unfold `Nat.Prime`; we just cite the lemma. '
                     'This is a characteristic feature of Mathlib: definitions tend to '
                     'be wrapped by lemmas that we are meant to use. Then if someone '
                     'changes the internals of the definition, the lemma remains a '
                     'stable interface.'},
            {'kind': 'command',
             'label': 'Let Aristotle add an informal commentary.',
             'command': 'arist informal divisors of a prime number'},
            {'kind': 'lean_walk',
             'label': 'Corollary: dissecting divisors of a prime',
             'narrative': 'The whole proof is a one-line `exact ...`. '
                          '`Nat.Prime.eq_one_or_self_of_dvd` is a lemma taking three '
                          'arguments: the proof that p is prime, the divisor m, and '
                          'the proof that m ∣ p. It returns a disjunction. Note the '
                          "naming: `Nat.Prime.<property>` is Mathlib's convention for "
                          "'if p.Prime, then ...'. The same shape appears in "
                          '`Nat.Prime.two_le`, `Nat.Prime.pos`, `Nat.Prime.one_lt`, '
                          'and so on. Learn this pattern - it saves you hours of '
                          'searching.',
             'lean_source': 'import Mathlib.Tactic\n'
                            '\n'
                            'theorem tutorial_heroic_prime_dvd (p : Nat) (hp : '
                            'p.Prime) (m : Nat)\n'
                            '    (hm : m ∣ p) : m = 1 ∨ m = p := by\n'
                            '  exact Nat.Prime.eq_one_or_self_of_dvd hp m hm\n',
             'name': 'tutorial_heroic_prime_dvd'},
            {'kind': 'quiz_checkpoint',
             'bundle': 'tutorial_12_heroic_ii',
             'min_correct': 3},
            {'kind': 'exercise',
             'exercise': {'game': 'lambda_lab_tutorial',
                          'world': 'exercises',
                          'level': 12}},
            {'kind': 'kb',
             'label': 'Mathlib naming conventions (`Nat.Prime.*`, `Eq.*`, `Or.*`)',
             'topic': 'mathlib'},
            {'kind': 'narrative',
             'title': 'The arc of twelve chapters',
             'body': 'After twelve chapters you carry a kit of archetypes: induction '
                     'over `Finset` (ch. 1, 9), proof by contradiction (ch. 2), '
                     'Fintype combinatorics (ch. 3), existential corollaries (ch. 4), '
                     'inequalities via `nlinarith` (ch. 5, 8), one-liners around '
                     'Mathlib (ch. 6, 7, 12), `decide` on concrete cases (ch. 10), and '
                     'complex analysis via `rw + ring` (ch. 11). That kit is roughly '
                     '80% of everyday Mathlib work. The remaining 20% is what you will '
                     'keep learning probably for the rest of your life, because those '
                     'are the chapters that have not been written yet.'}]}]
