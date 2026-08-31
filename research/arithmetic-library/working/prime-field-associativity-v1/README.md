# Verified working shift/scalar checkpoint

Exactly 25 working theorems are covered: the frozen 15 trailing-zero shift
rows followed by the 10 right-input scalar-covariance rows. All nine required
fresh verification processes completed with exit status 0. This is a verified
working checkpoint, not Alpha or Stable admission. Current Alpha remains 4,092
and Stable remains 432.

## Exact artifact and source scope

- [Proof bundle](artifacts/working-shift-scalar-proof-bundle-v1.json): 707,587 bytes,
  SHA256 `e8ed419608273f0230348ae498e57a23f0b59ade805964d30e0e8a3f10083cd0`.
- 207 theorem bodies: 182 unchanged current-v33 prerequisites and 25 working rows.
  One packaging node gives 208 nodes, 495 edges and 12,725 body proof nodes.
- Ordered 25-spec digest:
  `15d48cfcf25a997db2e18771d0c084f4465225c6137f47f53350d39a5ebb6981`.
- Identical before/after source binding in all nine reports:
  `641e5ac74c67d303ab3ca9f75b37f5931886a7d71dce119f102047a1daec47c4`.

The separate append, shift-equivalence, associativity-step and induction
tranches are excluded. Polynomial associativity, gcd/Bézout, uniqueness of arbitrary
quotient/remainder pairs from a formal identity, and the full G091 goal remain
open. The exact premises and empty-factor cases are those of the frozen source
statements;
this checkpoint does not strengthen their scope.

## Actual final verification

The first process compared all 25 parsed statements against the actual 4,092-row
v33 catalogue and one another: no duplicates, with all 182 inherited source
specifications reconciled exactly. The second process checked all 208 bundle
nodes in original HA, then submitted the same authenticated bytes to
the original pinned compiled Lean checker. Both passed.

Seven separate processes replayed each exact ordinary principal and checked
its returned empty-context certificate again in the original HA kernel:

| Principal | Bundle node | Ordinary certificate nodes |
| --- | ---: | ---: |
| `prime_field_polynomial_convolution_shift_right_nonempty` | 158 | 5431 |
| `prime_field_polynomial_convolution_shift_right_equivalent` | 171 | 7198 |
| `prime_field_polynomial_convolution_shift_right_exists` | 180 | 14300 |
| `prime_field_polynomial_shift_power_successor` | 182 | 252 |
| `prime_field_polynomial_convolution_right_scale` | 191 | 3163 |
| `prime_field_polynomial_convolution_right_scale_equal` | 194 | 3918 |
| `prime_field_polynomial_convolution_right_scale_exists` | 204 | 12042 |

Every process kept the original 170/175-second CPU, 180-second wall and
1,536-MiB RSS limits. Maximum reported time was 27.355964 seconds and maximum
RSS was 438,747,136 bytes. No external `time -l` wrapper was used for these
nine final gates. The source/data/rejection suite also passed all 363 distinct
cases; those cases are not extra proof windows.

## Evidence and historical distinction

[Final observations](final-verification-observations-v1.json) retain each exact
command, real report, exit status and resource metric. They are observations,
never inputs that authorize a later proof check or publication.

The earlier [candidate-authoring observations](candidate-authoring-observations-v1.json)
preserve the separate optional timer failure: after the real 208-kernel-call
report and exclusive artifact write, `time -l` exited 1 on the denied
`sysctl kern.clockrate` query. No clean authoring-process exit was claimed,
no permission workaround or reauthoring occurred, and no final gate was waived.
The nine fresh final processes subsequently verified the existing bytes with
clean exits.

The [source RFC](working-shift-scalar-integration-rfc-v1.md) remains at its
proof-bound registration-stage bytes; this README records the later observed
completion without changing those inputs. The earlier source and parent
registration observation files are preserved unchanged.
