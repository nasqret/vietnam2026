# Right-factor scalar covariance: working checkpoint

Ten new theorem specifications establish scalar covariance for the actual
natural-sum and prime-field polynomial convolution graphs. This is working
mathematics, **not an Alpha admission**. The later
[combined 25-law checkpoint](../prime-field-associativity-v1/README.md)
provides dependency-complete HA and same-byte compiled Lean verification
of these exact 10 rows together with the 15 shift rows.

The existing conservative definition `ND0271 FpPolyScale` is reused without
a new alias. Its canonical-scalar condition `k<p` remains necessary even for
an empty polynomial. The proof does not substitute raw beta-code equality
or equality of evaluations for actual decoded coefficients.

The main statements are:

- A genuine pointwise modular scalar relation transports through two actual
  natural sum traces. This auxiliary statement does not assume primality.
- Scaling the right input scales every convolution coefficient, at every
  natural index, using actual diagonal, natural-sum and residue witnesses.
- For actual products `P=A*B` and `Q=A*S`, with `S=k*B`, the lengths agree
  and `Q=k*P` in the actual scale graph.
- Every other actual scale `T=k*P` has the same decoded output prefix as
  `Q`; a constructive principal supplies the genuine `S,Q,T` witnesses.

The polynomial principals require a nonzero modulus and canonical scalar,
not primality; empty factors, scalar zero, characteristic two and composite
moduli are included. The generic natural-sum helper also covers modulus
zero under its explicit congruence hypotheses.

`conditional-observations-v1.json` preserves the author's exact non-authorizing
test record: **583 distinct cases passed**, including all 10 conditional HA
bodies, all removed and poisoned dependency edges, independent contracts,
actual CRT-beta/trace models and changed-premise rejection tests. There are
35 declared dependency edges, 745 commands and 1,241 conditional proof-node
occurrences. All five windows stayed within the unchanged resource limits;
maximum wall time was 24.071 seconds and maximum RSS 79,216,640 bytes.

Current-parent novelty, dependency-complete original HA, same-byte compiled
Lean and all seven combined ordinary principals subsequently passed in nine
fresh processes, recorded in the
[final checkpoint observations](../prime-field-associativity-v1/final-verification-observations-v1.json).
These records are not later admission authority. The properly aligned
append recurrence and associativity route live in separate checkpoints;
polynomial gcd/Bézout and full G091 are not claimed here.
