# RFC: beta-coded binary square-and-multiply execution

Status: constructive candidate; neither Alpha-enrolled nor Stable.

The immutable Alpha-v21 parent provides genuine parity decomposition,
relational powers, canonical modular residues, guarded functional
square-and-multiply transitions, beta-prefix extension, and finite base-two
Horner evaluation. This candidate joins those previously checked components
into actual beta-coded most-significant-bit binary execution histories for a
*supplied valid finite beta-coded zero/one digit prefix*.

Every formula expands hygienically into ordinary first-order Heyting
arithmetic over `0, S, +, *, =`; no new axiom, induction principle, kernel
rule, matrix/list sort, division function, power function, `BitLen` function,
or host-computation oracle is introduced.

Conservative public relations:

- `binary_digit_prefix(code, scale, length, *, tag)`: every actually decoded
  entry in the requested finite beta prefix is zero or one.
- `binary_execution_trace(code, scale, base, modulus, length, trace_code,
  trace_scale, *, tag)`: a second beta prefix starts at accumulator one and
  witnesses every canonical modular square-and-optional-multiply transition.
- `binary_modular_execution(code, scale, base, modulus, length, result, *,
  tag)`: an actual witnessed execution history and its decoded final value.
- `binary_execution_power_invariant(code, scale, base, modulus, length,
  result, *, tag)`: an existentially supplied finite base-two Horner exponent
  and the independently reviewed relational canonical modular power.

The user-supplied digit code is an honest explicit hypothesis. Constructing a
canonical binary digit prefix for *every supplied natural exponent*, proving
an object-level `BitLen` relation, and deriving the complete logarithmic
execution bound are separate future proofs. Therefore the ambitious G102
milestone remains open irrespective of executable examples or candidate
closure.

Concrete Python certificates are explicitly bounded and adversarially audited,
but remain examples only: release authority requires independently checking
every exact dependency-curried body through the unchanged intuitionistic
kernel, followed by a separate immutable Alpha admission review.

## Exact original-kernel theorem inventory

The frozen dependency-first campaign contains exactly **19 distinct constructive
theorems**, **60 direct declared dependency edges**, and **794 authored tactic
commands**:

1. `binary_digit_prefix_empty` — every empty beta-coded digit prefix is valid.
2. `binary_digit_prefix_restrict` — successor-prefix validity restricts exactly.
3. `binary_digit_prefix_terminal_bit` — a valid nonempty prefix has an actual
   decoded final digit equal to zero or one.
4. `binary_execution_initial_state` — an actual beta code decodes accumulator
   one at index zero.
5. `binary_execution_step_digit` — every witnessed modular transition contains
   a genuine zero-or-one digit.
6. `binary_execution_power_zero` — accumulator one is the actual canonical
   zeroth power for every guarded modulus.
7. `binary_execution_even_power_invariant` — a canonical square transition
   preserves the witnessed doubled-exponent power.
8. `binary_execution_odd_power_invariant` — a canonical square-and-multiply
   transition preserves the witnessed odd-exponent power.
9. `binary_execution_step_power_invariant` — either actual binary transition
   preserves the exact digit/exponent/power invariant.
10. `binary_execution_prefix_extend` — append one genuinely beta-coded digit
    and reduced transition without losing any earlier accumulator state.
11. `binary_execution_prefix_exists` — ordinary induction constructs a complete
    beta-coded execution for every supplied guarded valid digit prefix.
12. `binary_modular_execution_exists` — decode an actual terminal result from
    that complete execution history.
13. `binary_modular_execution_empty` — the empty execution ends exactly at one.
14. `binary_modular_execution_successor_decompose` — a nonempty execution
    splits into its genuine prefix and exact final digit/transition.
15. `binary_execution_horner_digit_split` — the existing base-two Horner
    successor yields the exact binary exponent decomposition.
16. `binary_modular_execution_power_correct` — full object-level induction
    proves that the actual execution result is the canonical modular power of
    the exact Horner exponent represented by the supplied beta-coded digits.
17. `binary_modular_execution_horner_exists` — jointly construct the actual
    base-two exponent, beta-coded execution, and proved modular-power witness.
18. `binary_modular_execution_result_functional` — two actual histories for
    one guarded digit prefix have the same proved canonical terminal residue.
19. `binary_modular_execution_result_exists_unique` — every guarded valid
    beta-coded digit prefix has exactly one genuine execution result.

Exact ordered-name SHA-256:

`606055de125b92a17c8111f6b041429ad6f74d12ac1175579f2e1e42bdec9087`.

Frozen endpoint statement hashes:

| Original-kernel theorem | Statement SHA-256 |
|---|---|
| `binary_execution_prefix_exists` | `d4021e49514a61208d99766bd84f04b3e272d3c52c151ca8f9dccf1ad04f67eb` |
| `binary_modular_execution_exists` | `103c179820815d1978bc1f147e0e7ad6b4289a98b8fb275c72f9ed9a66dd3c7c` |
| `binary_modular_execution_power_correct` | `8f924863e885c353860e298956baced60a6a43d56e9d3f3f1c6267deac657321` |
| `binary_modular_execution_horner_exists` | `345afe4884b51a608ea42c66b8c56f4ba9e6031a66ab52f2fb679ec5d93138e3` |
| `binary_modular_execution_result_exists_unique` | `10df7f702c8ab056bfaeb1d391e7b06d9c69011b5f50bd3fef12e91de53ee9ce` |

The final correctness theorem proves real formal execution, not a Python
simulation: each digit and accumulator occurs in an actual first-order beta
prefix, each transition proves its canonical residue, and ordinary natural
induction connects its terminal value to the independently constructed
base-two Horner exponent. The separately reviewed `BitLen` campaign may
eventually supply a usable formal length function, but this isolated module
neither depends on that unfinished work nor claims the still-missing theorem
constructing canonical binary digits for every arbitrary exponent, the exact
execution-to-`BitLen` relationship, or the complete G102 logarithmic bound.

Concrete example generation reads at most **4,097** digits even from an
infinite hostile iterator, limits accepted histories to **4,096** digits,
caps the base at **16,384 bits** and modulus at **4,096 bits**, and rejects
non-natural, Boolean, invalid-bit, changed-transition, and forged-terminal
inputs. None of these executable checks is substituted for the unchanged
intuitionistic kernel or a separate Alpha admission decision.
