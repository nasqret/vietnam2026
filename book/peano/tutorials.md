# Checked tutorials: commands, not transcripts

Peano Lab tutorials are executable programs with a deliberately tiny control language.  A displayed
step advances only when you press ENTER; `?` shows the same step again without changing state, and
`q` leaves it.  Command steps run against the real tactic engine.  A chapter that promises a proof
cannot complete until `qed` has sent the generated certificate through the independent kernel.

Useful fresh-session links:

- [`pa axioms`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20axioms)
- [`pa prove forall n m. n + m = m + n`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20prove%20forall%20n%20m.%20n%20%2B%20m%20%3D%20m%20%2B%20n)
- [`pa tutorial add_comm`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tutorial%20add_comm)
- [`pa tutorial symm_all`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tutorial%20symm_all)

## Prove `add_comm` by hand

The theorem is the premise-free PA statement

$$
  \forall n\,m.\; n + m = m + n.
$$

There is no `auto` call and no imported commutativity lemma.  Because addition recurses on its right
argument, the frozen script uses nested induction to establish the mirror-image equations that PA3
and PA4 do not simplify directly.  In the block below each bare `pa>` is one ENTER press.  The book
gate preserves those empty inputs and requires the final checked QED.

```text
pa> pa tutorial add_comm
pa>
pa>
pa>
pa>
pa>
pa>
pa>
pa>
pa>
pa>
pa>
pa>
pa>
```

## Build a toy `symm_all` tactical

The second tutorial follows a small extension through three layers: compose `all_goals` with `symm`,
add one surface-grammar branch, then pin rollback and kernel-checking in tests.  It does not ask the
kernel to trust a new rule.  Its live specimen runs the existing equivalent spelling
`all_goals symm` over two goals and finishes with checked QED.

```text
pa> pa tutorial symm_all
pa>
pa>
pa>
pa>
pa>
pa>
pa>
pa>
pa>
```

For comparison, ordinary Peano proof blocks use the same `pa>` prefix and keep one proof session for
the whole fence:

```text
pa> pa prove forall n. n = n
pa> intro n
pa> refl
pa> qed
```

The prefixes are part of the documentation contract: `λ>` blocks replay in Lambda Lab and `pa>`
blocks replay in Peano Lab.  This prevents a plausible-looking transcript from drifting away from
the browser implementation unnoticed.
