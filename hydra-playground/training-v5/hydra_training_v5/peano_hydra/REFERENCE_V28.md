# Alpha v28 reference and cold calibration

This controller is separate from the immutable v25 APIs and archives. It binds
epoch `f64b5f100c9c9bc77049ea627f13e641be83ac72aaa474216682076679a468ad`,
edition `4936d155e8d2a39409a4e83beb4ac5cb2481948d8b6eeecf1c7571161786646b`,
and all **2,764** dependency-ordered declarations (432 Stable, 2,332 Alpha only).
The full original statement/script/dependency record root is
`8c78b236606b5e0979d90c2b6cf94e67c40af549417411dc67c845689d512ed9`.

The current plan/report schema is `peano-hydra-reference-cold-review-v28-v2`.
Native hotspot execution additionally requires the two exact historical JSON
bundles declared in `review_inputs_v28.py`, at their normal repository-relative
paths. They total 16,887,078 bytes and are checked before, inside and after
workers. Missing, changed or shadowed inputs fail before proof execution. This
is a separate input closure for the selected hotspots, not full-library proof
coverage. The earlier v1 code-only snapshot and its unknown outcomes remain
historical evidence; use its own immutable controller to inspect that archive.

The compact plan retains every target's exact hashes, byte counts, dependencies
and eligibility. Canonical full target bodies require 38,640,967 bytes, exceeding
the inherited 32 MiB plan cap. They are therefore hashed in full, while only
the two selected bounded target bodies enter a hotspot plan. This is an encoding
choice, not target removal or a larger worker/parser reservation.

## Commands

Use an explicit Python 3.10 or newer interpreter. Draft planning is read only and
may describe dirty sources. Save `--full-plan` stdout with an exclusive creation
operation in the invoking archive runner, then independently pin its raw SHA256.
Do not overwrite an earlier plan to accommodate a changed source tree.

```sh
python3 -I -B scripts/check_peano_hydra_review_v28.py --plan --mode native-hotspots --full-plan
python3 -I -B scripts/check_peano_hydra_review_v28.py --plan --mode full-plan-only --full-plan
python3 -I -B scripts/check_peano_hydra_review_v28.py --plan --mode reference-only --reference-project /absolute/companion --lean-binary /absolute/lean-4.31.0/bin/lean --full-plan
```

Execution requires the exact independently frozen clean Git source tree. Its
source inventory covers the new CLI, controller, source validator and adapter,
as well as the original checker, shared certificate fingerprinting and reference
implementation. Neither a renamed dirty receipt nor a rehashed changed CLI can
pass historical Git-blob validation.

Current plans/reports use `peano-hydra-reference-cold-review-v28-v2`. The earlier
v1 snapshot and its first four missing-input outcomes remain immutable and are
read with that historical controller. V2 adds a strict `ancillary_inputs` field
with schema `peano-hydra-native-calibration-input-closure-v28-v1`. Hotspot replay
requires exactly these repository-relative historical files:

| Path under `research/arithmetic-library/artifacts/` | Bytes | Raw SHA256 |
| --- | ---: | --- |
| `bertrand-proof-bundle-v1.json` | 14,368,763 | `84078d40d2df7b072938975191fb70c95731059ced716a12050df4376e2d4883` |
| `alpha-v23-milestone-closure-proof-bundle-v1.json` | 2,518,315 | `cc0051da2cac31e382c79223999d448a1119f62aa448f1c7f68a6b9c3edf9d11` |

These 16,887,078 bytes form a separately pinned data closure, outside the old
source-only freezer scope. A fresh explicit data-aware snapshot must provide
them without changing old frozen trees or freezer defaults. Their raw seals and
graph expectations already live in the original pinned Python providers; no
external provenance JSON is consumed. Historical parent proof bodies are
embedded in these self-contained bundles. The older QR/Lucas/Kummer/v19–v22 data
files are construction inputs, not additional inputs of these two replay routes.

Planning declares expected data without reading it. Execution streams the fixed
files before creating its calibration archive, before each worker, in each
worker before replay, and after replay. Symlinks, hardlinks, special files,
wrong hashes/sizes, observed file drift, or a shadowing `/lab/proof-artifacts`
copy stop execution. Worker records already observed remain retained on later
failure. The default repository-relative loader paths are unchanged; the v18
explicit Bertrand source setter has an incompatible checker alias and is not
used. Byte preflight grants no proof validity: every actual body still goes
through the original native checker under the same worker limits. Reference-only
and full-plan-only modes declare an empty ancillary closure and gain no native
library readiness from it.

The following invocations must run **inside an additional owned process-group
supervisor**. The controller enforces individual child limits; it does not claim
to implement or attest the enclosing guard. The proposed enclosing bounds in the
plan are metadata, not permission or measured resource receipts. The operator
must provide that guard and retain its actual process evidence separately.

```sh
python3 -I -B scripts/check_peano_hydra_review_v28.py --run --plan-file /absolute/plan.json --plan-sha256 RAW_FILE_SHA256 --output-dir /absolute/fresh-calibration
python3 -I -B scripts/check_peano_hydra_review_v28.py --verify /absolute/original-calibration --report-sha256 RAW_REPORT_SHA256 --output-dir /absolute/disjoint-fresh-reproduction
```

No planning flags can override a saved execution plan. The parent output
directory must already exist and have canonical nonsymlink ancestry. Archives
are fresh only. Failures retain their partial directories, error receipt and
observed native worker records. Reproduction creates a separate archive and
compares every previously accepted original target's deterministic proof
projection; an earlier resource failure is not a mathematical negative result.

`full-plan-only` always rejects execution before creating any output directory.
There is no full-campaign resource envelope, automatic retry, model invocation,
installation, H0/H1 completion, human review or benchmark seal in this controller.

## Fixed calibration scope

`native-hotspots` selects `central_binom_upper_support_package` (index 1108) and
`three_mod_four_good_prime_exclusive` (index 1940), in dependency enrollment order,
with two separately planned fresh-process passes. It reserves four sequential
workers: 45 seconds wall and 30 CPU seconds each, 1 GiB sampled RSS, and 1 MiB per
captured stream. Their maximum child reservations sum to 180 wall / 120 CPU
seconds. These deliberately difficult targets are not a representative sample.
The unchanged cold-stage budget default is 900 seconds, range 30–3600. A worker
starts only if the stage has its complete 45-second reservation remaining.

`reference-only` requires the actual exact pinned Lean **4.31.0** compiler and
runtime bytes; Lean 4.28 or an RC is rejected. It preserves all 1,321 original
fixtures without changing their expectations: 1,024 positive formulas from 32
correlated authored templates, 280 certificate mutations, and 17 wire cases.
The run includes one native fixture worker, eight fresh module builds, one axiom
audit and 21 Lean fixture batches. The original child limits total 31 workers,
2,055 reserved child wall seconds and 1,460 CPU seconds. Lean retains `-j1 -M768`.
The enclosing proposed reservation is 2,400 wall / 1,800 aggregate CPU seconds,
2 GiB group RSS and 64 MiB aggregate captured output. No proof-library cold
workers are included in reference-only mode.

Neither mode changes data admission or the existing benchmark reference gate.
Native hotspot outcomes are not Lean evidence. Fixture agreement is not a
complete cold-library result, a theoremhood decision procedure, or an independent
human review. A completed archive therefore keeps all research and approval
flags false.

## Remaining profile incompatibilities

Exactly 17 v28 statements exceed the unchanged 128 KiB worker statement cap.
They remain in the pinned full inventory and cannot enter calibration workers:

- `signed_recursive_determinant_cofactor_equation` (2179)
- `matrix_rank_maximal_nonzero_prefix_exists` (2228)
- `rectangular_matrix_rank_functional` (2232)
- `rectangular_matrix_rank_exists_unique` (2233)
- `rectangular_matrix_rank_successor_minors_zero` (2234)
- `integer_matrix_vector_add_coefficients` (2260)
- `integer_matrix_vector_add_constructive` (2261)
- `integer_column_span_transport` (2262)
- `integer_column_span_negate_closed` (2266)
- `integer_column_span_add_closed` (2267)
- `integer_column_span_add_exists` (2268)
- `integer_column_span_negate_exists` (2269)
- `matrix_integer_cofactor_streams_from_recursion` (2283)
- `rectangular_matrix_rank_integer_transport` (2295)
- `rectangular_matrix_rank_integer_invariant` (2296; maximum 254,812 bytes)
- `square_matrix_full_rank_from_nonzero_determinant` (2316)
- `positive_determinant_matrix_data_full_rank` (2317)

All current targets fit the other inherited declaration bounds: maximum target
record 350,296 bytes, maximum whole script 317,585 bytes, maximum 479 commands,
and maximum 27 declared dependencies. This metadata says nothing about actual
proof replay CPU, RSS or fingerprint limits. A separately reviewed v28 field
bound change could address serialization without raising worker resource caps;
none is made here.

Remaining measured work: provision/verify an actual Lean 4.31 toolchain without
relabeling older evidence; run guarded current-source reference calibration;
measure the two hotspots; resolve the 17 field-profile incompatibilities;
establish a complete two-pass and separate fresh-reproduction resource envelope;
then collect real human/resource/readiness reviews. Matching partial roots or
successful subset calibration must never substitute for 2,764 accepted targets
in each of two complete passes with matching full roots and no unknowns.
