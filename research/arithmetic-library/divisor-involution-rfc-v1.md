# Positive divisor quotients and a constructed finite involution

This is an additive, non-admitting mathematical checkpoint toward G007.
It proves actual positive quotient extraction and a genuinely beta-coded
divisor-complement permutation. It does **not** prove Möbius cancellation,
the convolution identity, or Möbius inversion. Those are separate subsequent
proof obligations, not assumptions hidden in the graphs below.

## Immutable basis and evidence boundary

The unchanged Alpha-v30 catalogue has 3,222 checked-use rows and Stable has
432 rows. Its SHA-256 is
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
The previous 170 and 126 research-checkpoint rows remain non-admitted.
Exact AST novelty was tested against all **3,518** earlier statements and
within this new factory. None of the twelve statements is a duplicate.

The evidence recorded here is actual original-kernel **conditional-body**
checking against the exact declared theorem specifications. It is not a
claim that specification hashes discharge the hypotheses. The integration
layer must reconstruct and check the complete dependency cone and, before
claiming independent Lean verification or an ordinary closed principal
certificate, run those checks separately. No Alpha or Stable admission,
publication, kernel alteration, resource increase, or new axiom occurs here.

## Exact reusable graphs

For terms `n,d,q`, `DivisorComplement(n,d,q)` expands to

```text
(d != 0 /\ n = d*q)
\/
((d = 0 \/ not Divides(d,n)) /\ q = d).
```

Thus a retained positive divisor has an actual quotient equation. The zero
index and all nondivisors are fixed. No claim of positivity for a quotient
at `n=0`, and no claim of unrestricted symmetry at `n=0`, is made.

`DivisorComplementPrefix(n,b,c,l)` is the actual finite graph

```text
forall i. i < l -> exists q.
  BetaAt(b,c,i,q) /\ DivisorComplement(n,i,q).
```

This is constructed by ordinary induction using the existing `beta_prefix_extend`.
It is not a finite-choice oracle or a supplied map. The prefix constructor
allows any length `l`; the finite permutation theorem uses exactly `l=S n`,
so the domain is `0,...,n`. The permutation relation is the unchanged
bounded/injective/surjective beta-map graph, not a newly defined lookalike.
Different valid beta codes are not asserted to be equal.

The public builders are

```python
positive_divisor_complement_relation(n, d, q, *, tag, variables)
divisor_complement_prefix_relation(n, b, c, l, *, tag, variables)
```

Both accept genuine compound terms in an explicit context and reject every
generated-binder collision with that whole context. Existing divisibility,
order, beta and permutation abbreviations are reused; this RFC allocates
no global definition IDs.

## Principal statements

1. `positive_divisor_quotient_exists_unique`:
   every divisor `d` of a positive `n` has a quotient `q` with `n=d*q`,
   `q != 0`, `q | n`, `q <= n`, and every `r` satisfying `n=d*r` equals `q`.
2. `positive_divisor_involution_exists`:
   for every `n != 0`, construct `b,c` satisfying both
   `DivisorComplementPrefix(n,b,c,S n)` and the full finite permutation graph.
3. `divisor_complement_prefix_involution`:
   given such a prefix and `i <= n`, an actual lookup `BetaAt(b,c,i,q)`
   entails the actual return lookup `BetaAt(b,c,q,i)`.

The additional reusable `divisor_complement_prefix_positive_quotient`
identifies the literal decoded output: if `n != 0`, `d != 0`, `n=d*q`
and the full prefix is supplied, then `BetaAt(b,c,d,q)`. Its index bound
is proved from divisibility rather than assumed separately.

The unit `n=1` is included. The involution is **not** claimed to be
fixed-point-free: for `n=r*r`, the divisor `r` is fixed.

## Exact inventory and source pins

Factory: `make_divisor_involution_candidate_theorems(TheoremSpec)` in
`peano-lab/py/peano_lab/library/divisor_involution_candidate.py`.

The ordered twelve rows are:

```text
positive_divisor_quotient_exists_unique
divisor_complement_exists
divisor_complement_functional
divisor_complement_positive_equation
divisor_complement_symmetric
divisor_complement_bounded
divisor_complement_prefix_exists
divisor_complement_prefix_lookup
divisor_complement_prefix_permutation
positive_divisor_involution_exists
divisor_complement_prefix_involution
divisor_complement_prefix_positive_quotient
```

There are **34** declared dependency edges and **480** tactic commands.
Every declared dependency is used; the order is topological and no old name
is overwritten. The ordered-names SHA-256 (newline-joined, with a final
newline) is `16959bbf9fd0bb571dab2e5034cc2d8c647cccde91e1bfe4da28f38126a93f41`.

| Source | SHA-256 |
|---|---|
| `peano-lab/py/peano_lab/library/divisor_involution_candidate.py` | `67297015bcfbeb16b9090f537a2771d5c3cbfa4000d5c83c90cd0ba16cb15be7` |
| `peano-lab/py/tests/test_divisor_involution_candidate.py` | `3015085ad2d5ad88b7cb85d553b07992d2c22cc9395f1257f80b1ed8727f5b79` |

| Principal statement | Literal statement SHA-256 |
|---|---|
| `positive_divisor_quotient_exists_unique` | `a02a6f2e061e89191c7e4dff86b60611ebf035717468a17707bf5537486da384` |
| `positive_divisor_involution_exists` | `7fff4b15206b4bc27488134518c5e8231aee964a484e515576a6426be170719d` |
| `divisor_complement_prefix_involution` | `24bdefde49ebf80220bf5c974be3261d250dc98472d1228f6f3484492a9f34c1` |
| `divisor_complement_prefix_positive_quotient` | `758424c31f40bb748a54a9609b49b71c9df767580b50917f16d44e4e08e2edf0` |

## Actual checks and resource bounds

All twelve ordinary bodies passed `candidate_validation.replay_candidate_bodies`.
Their summed body occurrences are **920**, and summed per-body distinct
objects are **912**; these are not a claim of global shared-object identity.
The largest body has **188** occurrences, and the greatest depth is **36**.
Exact per-row occurrence/object/depth values are pinned in the test file.

The complete focused suite passed **84/84 tests**, with no skipped cases,
in **22.05 seconds** (22.237962 seconds including runner overhead), at an
observed peak RSS of **379,240,448 bytes**. Each fresh authoring process
retains the unchanged 170/175 CPU-second soft/hard limits, 180-second wall
alarm, and observed 1,536-MiB ceiling. No limit was increased.

Coverage includes independently written root and graph ASTs; every nested
binder against the complete explicit context; compound terms and large
double-and-add numerals; all 3,518 prior statements; poisoned conclusions;
removed actual dependencies and altered principal contracts; real CRT-built
beta maps; positive quotient uniqueness; arbitrary prefix lengths; unit,
zero-input and square fixed-point boundaries.

Reproduce from the continuation repository with `PYTHONPATH=peano-lab/py`:

```sh
python3 peano-lab/py/tests/test_divisor_involution_candidate.py
python3 -m pytest -q peano-lab/py/tests/test_divisor_involution_candidate.py
```

The first command supplies the authoring bounds itself; run the pytest
command under the same bounds when collecting a release receipt.
