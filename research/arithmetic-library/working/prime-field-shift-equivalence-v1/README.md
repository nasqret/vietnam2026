# Actual shift preserves formal polynomial equivalence

This is a working-only, one-theorem checkpoint. It is not an Alpha enrollment, a dependency-complete proof bundle, or a proof of associativity or gcd/Bézout.

The theorem `prime_field_polynomial_shift_equivalent_congruent` has the exact contract

```text
Equivalent(b,c,L; d,e,M)
→ Shift(b,c,L; ub,uc)
→ Shift(d,e,M; vb,vc)
→ Equivalent(ub,uc,S L; vb,vc,S M).
```

`Shift(b,c,L;d,e)` is the existing working ND0341 expansion: actual beta-prefix equality through length `L`, followed by `BetaAt(d,e,L,0)`. No new alias is introduced. `Equivalent` compares every formal power coefficient, not finite-field evaluations or raw beta codes. There is no modulus, primality, nonempty-prefix, or coefficient-bound premise. Empty and differently sized representations, arbitrary natural coefficients, and free values beyond the represented prefixes are retained.

The proof splits the actual power into zero or a successor. It uses the actual zero endpoint at power zero; otherwise it obtains actual source coefficients, transports them through the frozen shift laws, and uses coefficient functionality and the given equivalence. Its five declared dependencies are `zero_or_succ`, the two frozen shift power laws, and actual power-coefficient existence and functionality.

Validation completed on these exact bytes: 151 distinct tests and 453 passed setup/call/teardown records in one original-bounded process. The original HA body has 147 nodes and depth 41, with 138 commands and 5 declared dependencies. All removed and poisoned dependencies reject. Independent native-AST contracts, 108 actual beta models, five concrete input-clause counterexamples, empty cases, reencoding, and characteristic-two evaluation counterexamples are included. Observed wall/CPU/RSS were 4.404040 s / 4.356264 s / 55,574,528 B; unchanged limits were 170/175 CPU seconds, 180 wall seconds, and 1536 MiB RSS.

Pins:

- Source: 6,021 B; SHA256 `8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068`.
- Test: 20,376 B; SHA256 `9ed90ddc4680f8c2c3d04e2e3a76f8cffda4bfb95b1b83ab391d134c7fe5ab18`.
- Ordered specification: `d68b99a4ed9f996bd7e8b23fd0f17e165176b949f07a806a4d2c935d4372529e`.
- Exact UTF-8 statement: `7378d8a98b894a47bd3d88b64bf0899879b88a4854c913a28910802486972365`.
- Ordered 151-test IDs: `4876eb3e52f57b2d8e34dd7598098aec6573ced0e77155e7796d7876523469e8`.

The compact [observations](conditional-observations-v1.json) are explicitly non-authorizing and must never replace actual proof checking or an admission guard. Their detailed command/phase records belong to the private validation session, not to proof inputs. All six frozen shift/scalar/append source and test files remained byte-identical. Global novelty, complete dependency replay, independent Lean, and any later associativity induction are separate pending work.

To repeat the focused checks from the repository root under the same limits:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONMALLOC=pymalloc PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=peano-lab/py python3 - <<'PY'
import resource, signal, sys
resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
signal.alarm(180)
import pytest
code = pytest.main(['-q', '-p', 'no:cacheprovider',
    'research/arithmetic-library/working/prime-field-shift-equivalence-v1/test_prime_field_polynomial_shift_equivalence_candidate.py'])
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
peak *= 1 if sys.platform == 'darwin' else 1024
assert peak <= 1536 * 1024 * 1024
assert not any(name.startswith('peano_lab.library.editions_v') for name in sys.modules)
raise SystemExit(code)
PY
```
