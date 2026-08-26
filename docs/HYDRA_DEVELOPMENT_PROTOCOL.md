# Hydra's bounded development protocol

Hydra now has an opt-in, typed way to propose arithmetic proof steps. It uses
the existing public Peano tactics and independent kernel. It does not change
the older `surface-macro-v0` records, and it does **not** complete the
[H0 acceptance gates](../PLAN/11_peano_hydra.md#h0--semantic-and-functional-core).

## What is admitted

`training.peano_hydra.protocol.development_profile()` returns a detached,
machine-readable profile named `hydra-ha-development-v1`. Its SHA-256 binds
the grammar, limits, arithmetic axioms, proof rules, action semantics, and
the exact relevant compiler/kernel/native-tactic source files. The digest
uses compact UTF-8 JSON with sorted keys, excluding `profile_sha256` itself.
The caller's frozen catalog epoch remains a separate identity: the syntax
profile is not an attestation of every library theorem or source file.

Statements are closed intuitionistic first-order formulas over natural
numbers: zero, successor, addition, multiplication, equality, falsehood,
implication, conjunction, disjunction, and quantifiers. Negation and `≤`
expand to the native kernel encodings. Binder names become de Bruijn indices;
alpha-equivalent inputs receive the same canonical printed formula.

The admission ceilings include 4,096 source bytes, 256 AST occurrences,
depth 96, 16 bound-plus-context variables, decimal numerals through 64,
and safe ASCII names through 64 characters. Action JSON is at most 16,384
bytes. Duplicate/unknown fields, unsupported versions, hidden tactics,
explicit `#` indices, model metavariables, Unicode identifier lookalikes,
and unlisted extensions are rejected. `goal` is reserved because it denotes
the rewrite location. Derived proof states retain the existing native
certificate/resource limits; these admission limits are not a theoremhood
decision bound.

`validate_statement("forall n. n + 0 = n")` returns `∀ x. x + 0 = x`.
It checks syntax and scope, not truth: `validate_statement("0 = 1")` also
returns a valid statement. A failed proof attempt means **unknown**, never
“not a theorem.” Classical DNE and external solver status are not accepted.

## The seven action types

Every record contains integer `v: 1`, a case-sensitive `op`, and exactly the
fields below. All names and formulas are checked in the supplied context.

| `op` | Additional required fields | Public effect |
| --- | --- | --- |
| `Use` | `name`, `specializations` (term array) | Optional checked `use`; explicit `specialize` steps; `apply` |
| `Cut` | `kind` (`have`/`suffices`), fresh `name`, `formula` | A native local proof obligation |
| `Witness` | `term` | `exists term` |
| `Induct` | existing `variable`, `motive: "goal"` | `induction variable` on the current goal |
| `Rewrite` | local `source`, `direction` (`forward`/`backward`), `location` (`goal`/local hypothesis name) | One native rewrite |
| `Split` | `kind` (`intro`/`and`/`left`/`right`/`cases`), `name` | One structural tactic |
| `Dispatch` | `solver`, `premises` (local-name array), `bounds: {"max_calls": 1}` | One bounded native tactic |

For `Split`, `name` is optional as a value, not as a field: use JSON `null`
for anonymous `intro` and for `and`/`left`/`right`; `cases` requires a local
hypothesis name. `Dispatch` supports only `refl`, `assumption`, `simp`,
`norm_num`, and `compact_arith`. Only `simp` and `compact_arith` accept named
premises. Their source-bound native work/proof/time ceilings are recorded in
the profile; arbitrary caller overrides are rejected.

`Use` needs a local hypothesis or an explicitly permitted checked theorem.
Native constants `PA1`–`PA6` need no theorem import, but require an empty
specialization array: native `apply` handles their instantiation. Explicit
specialization needs a local hypothesis. Induction first requires a rigid
context variable; introduce a leading `forall` before proposing it. Arbitrary
explicit induction motives are not supported by this development version.

## Compile, execute, then independently check

```python
from training.peano_hydra.protocol import compile_action, execute_action

record = {"v": 1, "op": "Use", "name": "h", "specializations": ["0"]}
commands = compile_action(record, capabilities=caps, hypotheses=("h",))
# ("specialize h 0", "apply h")

new_session, receipt = execute_action(session, record, capabilities=caps)
```

`caps` must be a finite, caller-owned `SurfaceCapabilities`; the compiler
checks every emitted command and theorem import. Compilation alone does not
execute or certify anything.

`execute_action` focuses the first open goal and submits the whole generated
sequence as one public `run_surface` transaction. If a later specialization
fails after an earlier command succeeds, the supplied proof state, history,
and replay program remain unchanged. Its append-only trace records the failed
attempt. Existing tail goals are untouched. Successful actions return a new
session and a receipt; the supplied session is not replaced implicitly.

Proposal receipts bind canonical action/commands, the complete observed goal
tuple, focus, context names, finite authority, and profile digest. Execution
receipts additionally record the resulting goals and history counts. These
are provenance records, not signatures or QED certificates. Even a closed
goal needs the ordinary original-goal kernel check and retained replay before
it counts as a proved theorem.

## Focused verification

From `peano-lab/py`, run:

```sh
python3 -m pytest -q tests/test_peano_hydra_protocol.py
```

The tests exercise all seven actions, native original-goal replay, admission
and authority failures, receipt bindings, and partial-prefix rollback for
both local and imported multi-step `Use`. This is not the independently
implemented reference/conformance suite or the twice-cold full-library replay
required by [the normative design](PEANO_HYDRA_DESIGN.md).

The [development evaluation guide](HYDRA_DEVELOPMENT_EVALUATION.md) shows the
measured symbolic run and blocked training-exposure audit. The
[single product roadmap](HYDRA_PRODUCT_ROADMAP.md) sets the next review gate;
the native action implementation does not authorize a new model comparison.
