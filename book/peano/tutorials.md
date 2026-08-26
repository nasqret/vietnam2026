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
- [`pa tutorial norm_num`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tutorial%20norm_num)

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

## Turn numerical computation into a proof

The third tutorial puts a closed calculation beside the same calculation inside an open equality.
On each focused goal, `hint` recommends `norm_num` without changing the proof state.  The tactic then
constructs PA3--PA6 certificates for the closed numerical islands; it never asks the kernel to trust
the evaluated Python integer.

The ENTER-only lesson has one narrative step followed by the exact eight-command proof below:

```text
pa> pa tutorial norm_num
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

Here is the frozen proof sequence without the tutorial wrapper.  Its first branch is wholly closed;
the second keeps `n` rigid while normalizing only `2 * 3`.

```text
pa> pa prove (2 * 3 = 6) /\ (forall n. n + (2 * 3) = n + 6)
pa> split
pa> hint
pa> norm_num
pa> intro n
pa> hint
pa> norm_num
pa> qed
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
