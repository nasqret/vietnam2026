# A guided route from zero to FTA

This chapter is a map for repeated passes through the library. On a first pass,
read the mathematical idea in each stage. On a second pass, open the exact
native statement and proof links. On later passes, move backward to a missing
prerequisite or forward to a theorem that consumes it.

```{admonition} Two views at all times
:class: tip
Readable notation such as $a\mid b$, $\gcd(a,b)=d$ and
$\operatorname{Product}(F,n)$ is explanatory notation. The native theorem
cards show the fully expanded first-order formulas actually parsed and checked
by Peano Lab.
```

## Your learning route

The checkboxes below are stored only in this browser. They do not affect the
book, prover, or repository.

<div class="pa-learning-route" data-pa-learning-route>
  <label><input type="checkbox" data-learning-step="foundations"> <span><strong>Foundations:</strong> understand induction, equality transport and semiring normalization.</span></label>
  <label><input type="checkbox" data-learning-step="order"> <span><strong>Order:</strong> read <var>a</var> ≤ <var>b</var> as an existential additive gap.</span></label>
  <label><input type="checkbox" data-learning-step="division"> <span><strong>Division:</strong> follow the remainder successor/reset invariant.</span></label>
  <label><input type="checkbox" data-learning-step="bezout"> <span><strong>GCD and Bézout:</strong> follow Euclidean descent with four natural coefficients.</span></label>
  <label><input type="checkbox" data-learning-step="euclid"> <span><strong>Gauss and Euclid:</strong> see why coprimality enables cancellation.</span></label>
  <label><input type="checkbox" data-learning-step="primes"> <span><strong>Prime search:</strong> separate constructive bounded search from classical negation.</span></label>
  <label><input type="checkbox" data-learning-step="beta"> <span><strong>β codes:</strong> decode one finite position using division and CRT.</span></label>
  <label><input type="checkbox" data-learning-step="products"> <span><strong>Products:</strong> track prefix products with a second code.</span></label>
  <label><input type="checkbox" data-learning-step="factorization"> <span><strong>Factorization:</strong> compare greatest-prime descent and last-factor cancellation.</span></label>
  <label><input type="checkbox" data-learning-step="fta"> <span><strong>FTA:</strong> connect the three-command wrapper to its 73,767-node certificate.</span></label>
  <button class="pa-route-reset" type="button" data-route-reset>Reset this route</button>
</div>

(stage-foundations)=
## Stage 1 — equality, semiring laws and induction

Peano Lab begins with `0`, successor `S`, addition, multiplication and
equality. Even familiar algebraic laws are theorems. For example, PA3 explains
addition by recursion on the right, so the left identity

$$0+n=n$$

requires induction.

The complete native session is small enough to run here:

```text
pa> pa prove forall n. 0 + n = n
pa> induction n
pa> simp
pa> simp [IH]
pa> qed
```

Open the <a href="theorem-atlas.html#theorem-zero_add"><code>zero_add</code> proof card</a>, then
move forward to `add_comm`. Its card shows exactly why `zero_add` and
`add_succ_left` are the two prerequisites.

```{admonition} Predict before opening the card
:class: dropdown
Why does `add_comm` need two earlier theorems while `add_assoc` is proved
directly by induction? Look at which argument PA3 unfolds, and then compare the
two authored scripts in the atlas.
```

(stage-order)=
## Stage 2 — discrete order without a primitive relation

The surface notation $a\le b$ expands to an additive gap:

$$
a\le b \quad:\!\Longleftrightarrow\quad \exists k.\;k+a=b.
$$

Strict order is encoded by $S(a)\le b$. This makes constructive order proofs
witness-producing: a proof that $a\le b$ contains the distance from $a$ to
$b$. Cancellation, monotonicity and the discrete split

$$a\le b \Longrightarrow a=b\ \lor\ a<b$$

are the descent tools used by division, bounded factor search and
factorization induction.

<div class="pa-flow-bridge" role="figure" aria-label="Order dependencies used for descent">
  <div class="pa-flow-node"><strong>Additive gap</strong><br><small><var>k</var> + <var>a</var> = <var>b</var></small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>Cancellation</strong><br><small>remove common prefixes</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>Descent</strong><br><small>strictly smaller recursive input</small></div>
</div>

Use the atlas to traverse
<a href="theorem-atlas.html#theorem-le_refl"><code>le_refl</code></a> →
<a href="theorem-atlas.html#theorem-le_eq_or_lt"><code>le_eq_or_lt</code></a> →
<a href="theorem-atlas.html#theorem-proper_factor_lt"><code>proper_factor_lt</code></a>.

(stage-division)=
## Stage 3 — division with remainder

The native relation is

$$
\operatorname{DivRem}(n,d,q,r)
\quad:\!\Longleftrightarrow\quad
n=dq+r\ \land\ S(r)\le d.
$$

The successor step has exactly two branches:

<div class="pa-flow-bridge" role="figure" aria-label="Division remainder successor step">
  <div class="pa-flow-node"><strong><var>n</var> = <var>dq</var> + <var>r</var></strong><br><small>current quotient and remainder</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>S(<var>r</var>) &lt; <var>d</var></strong><br><small>keep <var>q</var>, replace <var>r</var> by S(<var>r</var>)</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">or</div>
  <div class="pa-flow-node"><strong>S(<var>r</var>) = <var>d</var></strong><br><small>replace <var>q</var> by S(<var>q</var>) and reset <var>r</var> to 0</small></div>
</div>

`division_remainder_succ` implements that invariant. The general theorem first
uses constructive case analysis to write the nonzero divisor as a successor,
then specializes the successor theorem:

```text
pa> pa prove forall m n. ~(m = 0) -> exists q r. n = m * q + r /\ S r <= m
pa> use zero_or_succ
pa> use division_remainder_succ
pa> intro m
pa> intro n
pa> intro hm
pa> specialize zero_or_succ m
pa> cases zero_or_succ
pa> exfalso
pa> apply hm
pa> exact zero_or_succ_left
pa> cases zero_or_succ_right
pa> specialize division_remainder_succ x
pa> specialize division_remainder_succ n
pa> rewrite zero_or_succ_right_witness
pa> rewrite zero_or_succ_right_witness
pa> exact division_remainder_succ
pa> qed
```

The wrapper has 219 nodes; uniqueness grows to 854 nodes because two quotient
blocks must be separated and then the remainders cancelled. Move between
<a href="theorem-atlas.html#theorem-division_remainder_exists"><code>division_remainder_exists</code></a> and
<a href="theorem-atlas.html#theorem-division_remainder_unique"><code>division_remainder_unique</code></a>
to compare their neighborhoods.

(stage-bezout)=
## Stage 4 — relational GCD and balanced Bézout

There is no `gcd(a,b)` term. Instead, `IsGCD(d,a,b)` expands to:

$$
d\mid a\ \land\ d\mid b\ \land
\forall c.\;c\mid a\to c\mid b\to c\mid d.
$$

Euclidean invariance transports this relation across $a=bq+r$. The existence
proof then performs formula-specific bounded descent and removes the bound with
reflexivity.

Ordinary integer coefficients are also absent. The checked balanced equation
uses four naturals:

$$
a x_+ + b y_+ = d + a x_- + b y_-.
$$

It represents $ax+by=d$ with $x=x_+-x_-$ and $y=y_+-y_-$ without adding
integers or subtraction to the language.

<div class="pa-flow-bridge" role="figure" aria-label="Euclidean gcd and balanced Bezout construction">
  <div class="pa-flow-node"><strong><var>a</var> = <var>bq</var> + <var>r</var></strong><br><small>division witness</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>GCD(<var>b</var>, <var>r</var>) + balance</strong><br><small>inductive package</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>GCD(<var>a</var>, <var>b</var>) + balance</strong><br><small>transport coefficients</small></div>
</div>

Study the complete scripts for
<a href="theorem-atlas.html#theorem-balanced_bezout_euclid_step"><code>balanced_bezout_euclid_step</code></a> and
<a href="theorem-atlas.html#theorem-gcd_balanced_bezout_exists"><code>gcd_balanced_bezout_exists</code></a>.

(stage-euclid)=
## Stage 5 — from Bézout to Gauss cancellation and Euclid's lemma

Balanced Bézout supplies the algebra behind Gauss cancellation:

$$
\operatorname{Coprime}(a,b)\land a\mid bc
\Longrightarrow a\mid c.
$$

For a prime $p$, take a relational gcd $g$ of $p$ and $a$. Every divisor of a
prime is either $1$ or the prime itself:

- if $g=1$, then $p$ and $a$ are coprime and Gauss cancellation gives
  $p\mid b$;
- if $g=p$, the gcd witness already gives $p\mid a$.

Thus

$$p\mid ab\Longrightarrow p\mid a\lor p\mid b.$$

The full 36-command proof is embedded in
<a href="theorem-atlas.html#theorem-euclid_prime_dvd_product"><code>euclid_prime_dvd_product</code></a>.
Move backward from that card to see its four immediate prerequisites, or
forward to finite-product membership and factorization uniqueness.

(stage-primes)=
## Stage 6 — constructive prime search and a prime above every bound

Primality is the expanded factor-pair formula

$$
\operatorname{Prime}(p)\;:\!\Longleftrightarrow\;
p\ne1\land\forall a,b.\;p=ab\to(a=1\lor b=1).
$$

Because the kernel is intuitionistic, negating that formula does not magically
extract a factor. The library builds bounded factor search, a constructive
prime-or-composite decision, proper-factor descent, and finally
`prime_divisor_exists`.

Prime unboundedness then uses a separate Euclidean argument:

<div class="pa-flow-bridge" role="figure" aria-label="Constructive prime unboundedness argument">
  <div class="pa-flow-node"><strong>Common multiple <var>c</var></strong><br><small>every 1 ≤ <var>t</var> ≤ <var>n</var> divides <var>c</var></small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>Prime <var>p</var> ∣ S(<var>c</var>)</strong><br><small>prime-divisor existence</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong><var>n</var> &lt; <var>p</var></strong><br><small>otherwise <var>p</var> ∣ <var>c</var> and <var>p</var> ∣ 1</small></div>
</div>

Open <a href="theorem-atlas.html#theorem-prime_unbounded"><code>prime_unbounded</code></a> to read
all 84 authored commands and traverse its ten direct prerequisites.

(stage-beta)=
## Stage 7 — Gödel-β codes from division and CRT

A β code is a pair of naturals $(b,c)$. Position $i$ is decoded modulo

$$M(c,i)=1+(i+1)c.$$

The exact `BetaAt(b,c,i,x)` relation says that $x<M(c,i)$ and that $x$ is the
remainder of $b$ modulo $M(c,i)$. Nothing here is a new sequence primitive:
it is an expanded formula made from addition, multiplication, equality and
existential witnesses.

<div class="pa-flow-bridge" role="figure" aria-label="From division and CRT to beta finite-prefix recoding">
  <div class="pa-flow-node"><strong>DivRem</strong><br><small>functional bounded remainders</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>Binary + bounded CRT</strong><br><small>combine compatible residues</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>β prefix extension</strong><br><small>preserve old entries, append one</small></div>
</div>

The main construction is
<a href="theorem-atlas.html#theorem-beta_prefix_extend"><code>beta_prefix_extend</code></a>: 105
authored commands elaborate, with checked dependencies, to 29,057 nodes.

(stage-products)=
## Stage 8 — finite products without primitive lists

One β code stores factors $p_0,p_1,\ldots,p_{l-1}$. A second code stores
prefix products $r_0,r_1,\ldots,r_l$ with

$$r_0=1,\qquad r_{i+1}=r_i p_i,\qquad r_l=n.$$

<div class="pa-sequence-diagram" role="figure" aria-label="Beta-coded factor sequence and prefix product trace">
  <div class="pa-sequence-label">factor code</div><div class="pa-sequence-cell"><var>p</var><sub>0</sub></div><div class="pa-sequence-cell"><var>p</var><sub>1</sub></div><div class="pa-sequence-cell">⋯</div><div class="pa-sequence-cell"><var>p</var><sub><var>l</var>−1</sub></div>
  <div class="pa-sequence-label">product trace</div><div class="pa-sequence-cell"><var>r</var><sub>0</sub> = 1</div><div class="pa-sequence-cell"><var>r</var><sub>1</sub> = <var>r</var><sub>0</sub><var>p</var><sub>0</sub></div><div class="pa-sequence-cell">⋯</div><div class="pa-sequence-cell"><var>r</var><sub><var>l</var></sub> = <var>n</var></div>
</div>

The second code is not cosmetic. First-order PA cannot recursively multiply an
unbounded list term because no such term exists. The trace makes every
successor multiplication locally checkable.

Compare
<a href="theorem-atlas.html#theorem-beta_prefix_product_trace_exists"><code>beta_prefix_product_trace_exists</code></a>,
<a href="theorem-atlas.html#theorem-beta_product_functional"><code>beta_product_functional</code></a> and
<a href="theorem-atlas.html#theorem-beta_factor_divides_product"><code>beta_factor_divides_product</code></a>.

(stage-factorization)=
## Stage 9 — existence and uniqueness take different routes

Existence selects a greatest prime divisor $p$ of $n$, writes $n=pq$, proves
$q<n$, recursively factors $q$, and appends $p$. Greatestness makes the append
preserve sortedness.

<div class="pa-flow-bridge" role="figure" aria-label="Factorization existence by greatest-prime descent">
  <div class="pa-flow-node"><strong><var>n</var></strong><br><small>nonzero input</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong><var>n</var> = <var>pq</var>, <var>q</var> &lt; <var>n</var></strong><br><small><var>p</var> greatest prime divisor</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>factor <var>q</var>, append <var>p</var></strong><br><small>sorted canonical code</small></div>
</div>

Uniqueness instead compares two sorted codes. Euclid's lemma proves that the
last prime in one product occurs in the other; sortedness forces it to be the
other last prime. Cancel that factor and recurse on the shorter prefix.

<div class="pa-flow-bridge" role="figure" aria-label="Factorization uniqueness by last-factor matching">
  <div class="pa-flow-node"><strong>same product</strong><br><small>two sorted prime codes</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>match last primes</strong><br><small>finite-product Euclid + sortedness</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>cancel and recurse</strong><br><small>equal length and entries</small></div>
</div>

Use the atlas to compare the two large wrappers:
<a href="theorem-atlas.html#theorem-prime_factorization_existence"><code>prime_factorization_existence</code></a> and
<a href="theorem-atlas.html#theorem-prime_factorization_uniqueness"><code>prime_factorization_uniqueness</code></a>.

(stage-fta)=
## Stage 10 — the native Fundamental Theorem of Arithmetic

The combined theorem is the conjunction of the two preceding endpoints. Its
authored body is exactly:

```text
split
exact prime_factorization_existence
exact prime_factorization_uniqueness
```

```{admonition} Why three commands still produce 73,767 nodes
:class: dropdown
Before the body is checked, `prime_factorization_existence` and
`prime_factorization_uniqueness` have each been reconstructed as complete
closed certificates. `Cut` embeds those certificates once and exposes their
formulas locally. The final `split` uses the two local hypotheses. The kernel
therefore receives a single self-contained tree, not three trusted theorem
names.
```

| Component | Nodes | Depth | Cuts |
|---|---:|---:|---:|
| existence | 43,973 | 98 | 1,328 |
| uniqueness | 29,789 | 82 | 854 |
| combined FTA | 73,767 | 99 | 2,184 |

The exact certificate SHA-256 is
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It passes empty-context replay, live `use`/`exact`/`qed`, dependency and
hypothesis mutation tests, a PA-leaf mutation, and a no-DNE/PA1–PA6 audit.

Open the complete
<a href="theorem-atlas.html#theorem-fundamental_theorem_of_arithmetic"><code>fundamental_theorem_of_arithmetic</code> card</a>.
Then use its prerequisite and dependent columns to move backward into the two
proofs or forward into any future client theorem.

## What to do next

- Use the {doc}`theorem atlas <theorem-atlas>` as the back-and-forth proof
  reader.
- Read {doc}`Language, notation, and trust <language-and-trust>` when an exact
  expanded formula looks mysterious.
- Read {doc}`Self-contained proof sharing <proof-sharing>` when a short script
  seems too small for its measured certificate.
- Read {doc}`Primes and unique factorization <primes-and-factorization>` for
  the full representation argument and the separate Lean list-based
  cross-check.
- Use {doc}`Using and extending the library <using-the-library>` to reproduce
  or extend the checked artifacts.
