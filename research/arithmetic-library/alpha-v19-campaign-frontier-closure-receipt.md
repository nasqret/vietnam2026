# Alpha v19 constructive campaign frontier: independently checked closure

The additive constructive campaign frontier contains exactly 64 new theorem
specifications: 44 Pythagorean forward-construction results, the exact prime
two-square equivalence, nine complete linear-congruence results, and ten
results culminating in constructive infinitude of primes one modulo four.

Its full real dependency closure contains 544 theorem nodes and 1,633 direct
theorem prerequisite arrows. Seventeen maximal endpoints are connected to one
balanced, non-enrolled synthetic conjunction root, producing the following
canonical self-contained ordinary intuitionistic proof artifact:

```text
research/arithmetic-library/artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json
SHA-256: cf7947a944d54e9eb956fb153702b29c953100ece6cf05743162759b0fba9b17
Canonical bytes: 1,617,207
Bundle proof nodes: 545
Direct dependency edges: 1,650
Actual structural body-proof nodes: 34,020
Independent original-kernel checks: 545
Immutable two-square parent proof bodies reused: 452
Exact other parent bodies reconstructed and independently checked: 28
New campaign bodies reconstructed and independently checked: 64
```

Every reused proof body is included again inside the self-contained artifact
and independently checked by the unchanged original intuitionistic kernel;
no historical theorem name, receipt, hash, or source annotation grants proof
authority. All 92 reconstructed bodies are produced in 12 bounded batches,
each respecting the unchanged limits of at most 16 bodies, 125,000 structural
proof nodes, and 25,000 immutable proof objects.

The exact new flagship theorem roots are:

```text
pythagorean_primitive_euclidean_from_order
pythagorean_primitive_normal_form
prime_is_two_squares_iff_two_or_one_mod_four
linear_congruence_solvable_iff_gcd_divides
infinitely_many_primes_one_mod_four
```

The prime progression proof derives its witnesses directly from prime
divisors of `4*C*C+1` for a bounded common multiple `C`; it does not depend
on an assumed proof of infinitely many primes three modulo four. The
Pythagorean theorem is the independently checked forward constructor only:
inverse primitive classification and unconditional Fermat exponent-four
descent are not claimed.

Both independent checks use the frozen artifact and unchanged proof kernel:

```text
PYTHONMALLOC=malloc python3 -m pytest -q \
  peano-lab/py/tests/test_library_editions_v19_admission.py
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json
```
