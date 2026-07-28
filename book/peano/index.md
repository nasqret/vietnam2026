# Building Peano Lab

*A little Lean for Peano arithmetic — and a guided tour of how such systems are built.*

Peano Lab is a lightweight, readable theorem prover for Peano arithmetic. It runs entirely in the
browser next to the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/), but its
central lesson is not a flashy tactic: **every QED is checked again by an independent kernel against
the original theorem**. Tactics may search, guess and fail. The kernel sees only an explicit proof
certificate.

This part tells the construction story from the implementation diary. Read it in order:

1. {doc}`Why Peano arithmetic <why-pa>` develops the staged path from computation to induction and
   first-order logic.
2. {doc}`The kernel and the De Bruijn criterion <kernel>` explains the trusted boundary, proof terms,
   capture-safe substitution and the audit that made independent checking non-negotiable.
3. {doc}`Anatomy of a tactic <tactics>` follows one tactic from a goal transformation to a certificate
   with proof-wide metavariable substitution and transactional failure.
4. {doc}`Tacticals: when tactics become a language <tacticals>` builds sequencing, choice, repetition,
   focusing and their rollback laws.
5. {doc}`Induction and the theorem ladder <induction-ladder>` climbs from the defining equations to a
   checked zero-product proof.
6. {doc}`Checked arithmetic automation <arithmetic-automation>` separates numerical computation,
   polynomial normalization, and bounded search from the certificates that justify their results.
7. {doc}`compact_arith: searching for a small PA certificate <compact-arith>` follows one theorem
   from a 30,030-node generic elaboration to a 180-node checked record, then designs a bounded
   equality tactic without confusing a best-found certificate with a proven minimum.
8. {doc}`The deliberate limits <limits>` draws the line around PA, Gödel's theorems, bounded search,
   and the facilities that a production prover such as Lean adds.
9. {doc}`Training a Peano policy without trusting it <training-a-peano-policy>` turns the prover
   into a warm headless data and evaluation service, then develops replay-validated synthetic data,
   leakage-safe prompts and splits, completion-only SFT, kernel-judged search, and a reproducible
   Helios protocol without placing a learned model inside the trusted base.

The working design lives in
[`docs/PEANO_LAB_DESIGN.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_LAB_DESIGN.md),
the task board in
[`PLAN/09_peano_lab.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/PLAN/09_peano_lab.md).

Then use {doc}`Checked tutorials <tutorials>` to replay a premise-free hand proof of addition
commutativity, a source-level `symm_all` tactical walkthrough, and a numerical-normalization proof.
Every `pa>` block and browser deep link in this part is replayed through the real driver during the
book gate; prose examples do not get a private, easier semantics.

The full library is executable too. {doc}`The checked theorem ladder <ladder>` follows the original
23 scripted entries through order totality and the zero-product core capstone, then a public
26-entry modular-arithmetic extension to the fourth-power modulo-five capstone. It also links to
the separately validated M20 foundational snapshot. The chapter explains how theorem reuse is
packaged as self-contained Cuts whose complete branches are checked by the reviewed kernel rule,
without granting theorem names or hashes any authority. It also links each statement to the browser
and Lean 4 cross-checking surface. M9 then turns the same checked interactions into a reproducible
[proof-trace corpus](https://github.com/nasqret/vietnam2026/tree/peano-lab/peano-lab/corpus) and fixes
a [kernel-judged evaluation protocol](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_LLM.md)
for later small-model experiments; at that milestone no model was trained. The dated
{doc}`implementation diary <diary>` preserves the design choices, bugs and objections behind the
polished account.

M19 is the authorized continuation of that deliberately frozen M9 protocol.  The
{doc}`policy-training chapter <training-a-peano-policy>` explains the compact headless adapter and
the small-model experiment. Its first attested release contains 2,522 independently
kernel-checked roots and exactly 10,000 next-tactic rows, split by genealogy, canonical formula,
and exact policy prompt and reproduced byte-for-byte from raw traces. The first WMI Qwen3-1.7B
pilot completed, scoring 0/4 at pass@4 on the frozen induction/order benchmark and 1/8 on one fresh
direct-witness probe. The chapter treats this as a curriculum diagnosis, not broad proving ability.

M11 extends that core with three ordinary checked entries—`one_mul`, `mul_one`, and `add_mul`—to
complete the commutative-semiring basis for certificate-producing arithmetic normalization. M12's
argument-free `ring` turns that basis into checked polynomial identities; the ladder chapter gives
the complete odd-square induction proof and makes its explicit `trans`/`rewrite` boundary visible.
M13 adds bounded `norm_num` for closed numerical islands and arithmetic-aware hints. The new
arithmetic-automation chapter contrasts its exact equality contract with `simp`, `ring`, and `auto`,
and records why general PA, nonlinear hypothesis solving, and Presburger `omega` remain outside it.
M14 then treats browser delivery as another explicit boundary: versioned caching, negotiated WASM
compression, and concurrent source transfer reduce cold network cost without changing one proof rule.
The limits chapter distinguishes that runtime boot from theorem proving. M15 adds a replayable
current-branch artifact: active text remains unchecked, while only a successful kernel QED may
produce the retained script's final `qed`. The tactics and ladder chapters explain why downloading
that program is still separate from checking a certificate or admitting a library theorem. M17
applies the same distinction to multiline paste: a bounded complete script runs sequentially
through the ordinary session owner, and its final `qed` gains no new authority.
M18 applies it once more to certificate size. The `compact_arith` tactic searches a fixed
PA recurrence-template space for a small proof of one rigid equality, optionally using an explicit
ordered list of equality hypotheses. It neither chooses an outer induction invariant nor invents an
existential witness, and its cost report is never a substitute for independent checking.

M20 begins a general {doc}`foundational arithmetic library
<../arithmetic-library/index>`. Its first independently validated branch snapshot extended the
original 23-entry base to 51 checked entries. That snapshot and the 49-entry public-catalog source
remain provenance: fourteen post-core records coincide, so their initial reconciliation contained
63 unique entries rather than their arithmetic sum. Subsequent native passes extend the current
local candidate to **176 checked theorems**: the 23-entry base, 141 post-baseline foundational
entries, and twelve further unique modular capstones. The checked route now includes division and
remainder, relational gcd, balanced-natural Bézout, Gauss cancellation, the general prime-divisor
characterization, Euclid's lemma, constructive equality/divisibility/primality decisions, bounded
nontrivial-factor search, proper-factor descent, prime-divisor existence,
balanced-congruence transitivity and addition/multiplication,
both directions between bounded congruence and a remainder decomposition,
functional single-position Gödel-β decoding equivalent to bounded congruence,
constructive binary CRT, and a one-code/two-position β client under an explicit
modulus-coprimality premise. It now also proves beta-modulus coprimality under
the explicit conditions $j=i+\mathit{gap}$ and $\mathit{gap}\mid c$, applies
that result to the two-position client, and constructs a nonzero common
multiple of every positive natural through a given bound. Unconditional
beta-modulus coprimality is false: with $c=1$, the family contains moduli
$3$ and $6$. The associated
183-node research catalog records those 176 checked entries alongside three planned expressible
targets and four language-interface targets:
conventional signed Bézout and the three finite-factorization endpoints. This is local candidate
authority; it does not claim that every new theorem card has already been promoted to the
production browser. Native FTA remains unproved; greatest-prime descent,
index-bound finite-prefix glue, product-modulus CRT iteration, finite-prefix
extension, and prefix-product infrastructure are the next critical gates.
