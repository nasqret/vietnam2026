"""One separately admitted, exposed scaled-plus-witness teacher curriculum.

The 1,008 scaled routes are freshly regenerated, never imported from an old
training preparation. The additional 16 route declarations come from the
pinned witness-fixture-02 archive and are freshly proved as well. Its origin
bytes and source identity remain historical facts, distinct from this module's
current execution identity and frozen epoch. No mode trains, loads a model,
admits a theorem to the DAG, or establishes an unseen-model improvement.

Run a full build/publication/verification only in an owned bounded worker.
Publication replays again in fresh native sessions in the same caller process;
it is not independent-process verification. There is only one fixed mixture,
with no repetition, filtering, curriculum choice, or fallback to a small pilot.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
import tempfile
from typing import TYPE_CHECKING

from peano_lab.batch import run_proof
from hydra_training_v5.peano_hydra import composition as native
from hydra_training_v5.peano_hydra import composition_scale as scaled
from hydra_training_v5.peano_hydra import witness_repair as witness
from hydra_training_v5.peano_hydra.curriculum import VerifiedCurriculum, encode_jsonl
from hydra_training_v5.peano_hydra.epoch import HydraEpoch, freeze_epoch

if TYPE_CHECKING:
    from hydra_training_v5.peano_hydra.posttrain import VerifiedSource


ROOT = Path(__file__).resolve().parents[2]
CORRECTIVE_SOURCE_SCHEMA = "peano-hydra-native-witness-corrective-source-v1"
CORRECTIVE_PLAN_SCHEMA = "peano-hydra-native-witness-corrective-plan-v1"
CORRECTIVE_EVIDENCE_SCHEMA = "peano-hydra-native-witness-corrective-evidence-v1"
CORRECTIVE_CURRICULUM_PROFILE = "scaled-1008-plus-witness-16-v1"
AUTHORITY_PROFILE = native.COMPOSITION_PROFILE
SOURCE_FILENAMES = native.SOURCE_FILENAMES
FROZEN_WITNESS_RELATIVE = "artifacts/peano-hydra/native-search-repair-2026-08-28/witness-fixture-02"
FROZEN_WITNESS_DIRECTORY = ROOT / FROZEN_WITNESS_RELATIVE
FROZEN_WITNESS_MANIFEST_SHA256 = "7a132a61be1d17e6834034d79ff547635b0ff3fb7abbd34e452b9add912e6970"
FROZEN_WITNESS_PLAN_SHA256 = "35688fdcf73aa58806f2edc942b3c184cd3aebd02e343333be4ed8fa20461a12"
SCALED_ROUTE_COUNT = 1008
SCALED_TRANSITION_COUNT = 9612
SCALED_SPLIT_TRANSITIONS = {"train": 8892, "dev": 720}
CORRECTIVE_ROUTE_COUNT = 16
CORRECTIVE_TRANSITION_COUNT = 64
CORRECTIVE_SPLIT_TRANSITIONS = {"train": 40, "dev": 24}
MAX_ROUTES = 1024
MAX_TRANSITIONS = 9676
MAX_SOURCE_FILE_BYTES = native.MAX_SOURCE_FILE_BYTES
MAX_SOURCE_TOTAL_BYTES = native.MAX_SOURCE_TOTAL_BYTES


class HydraCorrectiveSourceError(ValueError):
    """The fixed mixture lost its original data, proof, or authority binding."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HydraCorrectiveSourceError(message)


def _digest(value: object) -> str:
    return hashlib.sha256(native._canonical(value)).hexdigest()


def _directory(path: Path, *, fresh: bool = False) -> Path:
    _require(isinstance(path, Path), "directory must be an explicit Path")
    path = path.absolute()
    _require(".." not in path.parts and not path.is_symlink()
             and not any(parent.is_symlink() for parent in path.parents),
             "directory must use direct paths without traversal or symlinks")
    _require(not path.exists() if fresh else path.is_dir(),
             "destination already exists" if fresh else "input must be an existing directory")
    return path


def _signature(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, value.st_nlink)


def _read_file(path: Path, *, maximum: int) -> bytes:
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                 and before.st_size <= maximum, "input is not a bounded single-link regular file")
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    _require(len(raw) == before.st_size <= maximum
             and _signature(before) == _signature(after) == _signature(path.lstat()),
             "input changed during its bounded read")
    return raw


def _read_directory(directory: Path, names: tuple[str, ...], *, maximum: int) -> dict[str, bytes]:
    directory = _directory(directory)
    before = directory.lstat()
    seen = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            _require(entry.name in names and entry.is_file(follow_symlinks=False)
                     and not entry.is_symlink(), "source has an unexpected or unsafe inventory entry")
            seen.add(entry.name)
    _require(seen == set(names), "source inventory is incomplete")
    result, total = {}, 0
    for name in names:
        raw = _read_file(directory / name, maximum=min(MAX_SOURCE_FILE_BYTES, maximum - total))
        total += len(raw)
        result[name] = raw
    _require(total <= maximum and _signature(before) == _signature(directory.lstat()),
             "source directory changed during its bounded read")
    return result


def _source_identity() -> dict[str, object]:
    files = dict(scaled._source_identity()["files"])
    files.update(witness._source_identity()["files"])
    relative = "training/peano_hydra/corrective_source.py"
    files[relative] = hashlib.sha256(_read_file(ROOT / relative, maximum=2 * 1024**2)).hexdigest()
    files = dict(sorted(files.items()))
    return {"files": files, "source_files_sha256": _digest(files),
            "coverage": "fixed mixture/origin admission, native replay and prompt sources; not whole-repository or transitive-import attestation"}


@dataclass(frozen=True, slots=True)
class _WitnessOrigin:
    plan: dict[str, object]
    rows: tuple[dict[str, object], ...]
    payloads: dict[str, bytes]
    record: dict[str, object]


def _read_witness_origin() -> _WitnessOrigin:
    payloads = _read_directory(FROZEN_WITNESS_DIRECTORY, witness.SOURCE_FILENAMES,
                               maximum=witness.MAX_OUTPUT_BYTES)
    _require(hashlib.sha256(payloads["manifest.json"]).hexdigest() == FROZEN_WITNESS_MANIFEST_SHA256,
             "frozen witness origin manifest differs from its reviewed raw hash")
    _require(hashlib.sha256(payloads["plan.json"]).hexdigest() == FROZEN_WITNESS_PLAN_SHA256,
             "frozen witness origin plan differs from its reviewed raw hash")
    manifest, plan = native._decode(payloads["manifest.json"]), native._decode(payloads["plan.json"])
    _require(manifest.get("schema") == witness.SOURCE_SCHEMA and plan.get("schema") == witness.PLAN_SCHEMA,
             "frozen witness origin has a different schema")
    _require(set(manifest["files"]) == set(witness.SOURCE_FILENAMES) - {"manifest.json"},
             "frozen witness origin lost its exact file inventory")
    for name, identity in manifest["files"].items():
        _require(identity == {"bytes": len(payloads[name]), "sha256": hashlib.sha256(payloads[name]).hexdigest()},
                 "frozen witness origin payload differs from its manifest")
    _require(plan["plan_sha256"] == _digest({key: value for key, value in plan.items() if key != "plan_sha256"})
             and manifest["plan_sha256"] == plan["plan_sha256"], "frozen witness plan identity is inconsistent")
    current = witness.build_witness_repair_plan()
    # Old implementation hashes remain origin evidence, not assertions about
    # the code executing now. The exact fixed data/authority must still agree.
    for key in ("authority_profile", "authority", "prompt_contract", "decoder_profile",
                "families", "routes", "route_count", "transition_count", "split_policy",
                "excluded_targets", "excluded_targets_sha256"):
        _require(plan[key] == current[key], f"frozen witness {key} no longer matches the reviewed fixed declaration")
    raw_rows = payloads["sft.jsonl"].splitlines(keepends=True)
    _require(len(raw_rows) == CORRECTIVE_TRANSITION_COUNT
             and all(len(raw) <= witness.MAX_LINE_BYTES and raw.endswith(b"\n") for raw in raw_rows),
             "frozen witness transition inventory is malformed")
    rows = tuple(native._decode(raw) for raw in raw_rows)
    _require(encode_jsonl(rows) == payloads["sft.jsonl"], "frozen witness rows are not canonical")
    record = {"kind": "frozen-standalone-witness-fixture-not-an-old-training-preparation",
              "directory": FROZEN_WITNESS_RELATIVE, "schema": witness.SOURCE_SCHEMA,
              "plan_sha256": plan["plan_sha256"], "source_identity": plan["source_identity"],
              "files": {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                        for name, raw in sorted(payloads.items())},
              "original_bytes_modified": False,
              "saved_qed_flags_are_sufficient_for_admission": False}
    return _WitnessOrigin(plan, rows, payloads, record)


def _frozen_epoch(epoch: HydraEpoch | None) -> HydraEpoch:
    current = freeze_epoch(ROOT)
    _require(type(current) is HydraEpoch and (epoch is None or type(epoch) is HydraEpoch),
             "corrective admission requires an exact frozen epoch")
    _require(epoch is None or epoch.to_dict(include_graphs=True) == current.to_dict(include_graphs=True),
             "requested epoch differs from the currently verified epoch and both DAGs")
    return current


def _plan(epoch: HydraEpoch, origin: _WitnessOrigin) -> dict[str, object]:
    scale = scaled.scaled_composition_profile_record(epoch)
    _require(scale["route_count"] == SCALED_ROUTE_COUNT
             and scale["tactic_decisions"] == SCALED_TRANSITION_COUNT,
             "fixed scaled component changed its route/decision inventory")
    scale_splits = Counter()
    for route in scale["routes"]:
        scale_splits[route["split"]] += len(route["commands"])
    _require(dict(scale_splits) == SCALED_SPLIT_TRANSITIONS, "fixed scaled component changed its diagnostic splits")
    _, _, authority, prompt_contract, decoder_profile = native._authority(epoch, AUTHORITY_PROFILE)
    for key, expected in (("authority", authority), ("prompt_contract", prompt_contract),
                          ("decoder_profile", decoder_profile), ("authority_profile", AUTHORITY_PROFILE)):
        _require(scale[key] == origin.plan[key] == expected, "mixed components disagree about exact V4 authority")
    _require(scale["excluded_targets"] == origin.plan["excluded_targets"], "mixed components changed the 96+4 exclusion panel")
    families = [dict(row) for row in scale["families"]]
    families.extend({"id": row["name"], "split": row["split"], "generator_seeds": row["seeds"],
                     "lineage_sha256": row["lineage_sha256"], "origin": "frozen-witness-fixture-02",
                     "semantic_independence_claim": False} for row in origin.plan["families"])
    _require(len({row["id"] for row in families}) == len(families)
             and len({row["lineage_sha256"] for row in families}) == len(families),
             "mixed components have a family or lineage collision")
    routes = [dict(row) for row in (*scale["routes"], *origin.plan["routes"])]
    _require(len(routes) == SCALED_ROUTE_COUNT + CORRECTIVE_ROUTE_COUNT <= MAX_ROUTES
             and len({row["name"] for row in routes}) == len(routes)
             and len({row["statement"] for row in routes}) == len(routes),
             "mixed route inventory has duplicate names or canonical goals")
    catalog_names = {row.name for row in epoch.theorems}
    excluded = {row["statement"] for row in origin.plan["excluded_targets"]}
    _require(not catalog_names.intersection(row["name"] for row in routes), "a corrective teacher impersonates an enrolled theorem")
    _require(not excluded.intersection(row["statement"] for row in routes), "mixed source contains an excluded exact target")
    decisions = sum(len(row["commands"]) for row in routes)
    _require(decisions == SCALED_TRANSITION_COUNT + CORRECTIVE_TRANSITION_COUNT <= MAX_TRANSITIONS,
             "mixed source changed its fixed transition inventory")
    exposure = {"authorship": "fixed-scaled-teachers-plus-explicit-public-failure-witness-correction",
                "guided_teacher_proofs": True, "model_generated": False, "public_and_correlated": True,
                "inherited_scaled_exposure": scale["exposure"],
                "corrective_authorship": origin.plan["claims"]["authorship"],
                "common_exposure_component_sha256": _digest({"epoch_sha256": epoch.epoch_sha256,
                    "profile": CORRECTIVE_CURRICULUM_PROFILE, "scaled_component": scale["exposure"]["common_exposure_component_sha256"],
                    "witness_origin_manifest_sha256": FROZEN_WITNESS_MANIFEST_SHA256}),
                "exact_public_comparison_target_exclusion": True, "exact_historical_target_exclusion": True,
                "closed_intermediate_target_exclusion_required": True,
                "declared_family_groups_are_mathematical_components": False,
                "eligible_for_unseen_model_comparison": False, "semantic_equivalence_complete": False,
                "independent_human_review": False, "sealed_benchmark": False,
                "research_claim_eligible": False, "alpha_admitted": False, "dag_mutated": False,
                "model_weights_repaired": False, "autonomous_improvement_verified": False}
    result = {"schema": CORRECTIVE_PLAN_SCHEMA, "curriculum_profile": CORRECTIVE_CURRICULUM_PROFILE,
              "epoch_sha256": epoch.epoch_sha256, "authority_profile": AUTHORITY_PROFILE,
              "authority": authority, "prompt_contract": prompt_contract, "decoder_profile": decoder_profile,
              "source_identity": _source_identity(), "families": families, "routes": routes,
              "route_count": len(routes), "tactic_decisions": decisions,
              "split_route_counts": dict(sorted(Counter(row["split"] for row in routes).items())),
              "split_transition_counts": {split: scale_splits[split] + CORRECTIVE_SPLIT_TRANSITIONS[split]
                                          for split in ("train", "dev")},
              "split_policy": native.COMPOSITION_SPLIT_POLICY,
              "scaled_component": {"kind": "fresh-regeneration-not-old-preparation-adoption",
                                   "schema": scaled.SCALED_COMPOSITION_SCHEMA, "plan_sha256": scale["plan_sha256"],
                                   "route_count": SCALED_ROUTE_COUNT, "transition_count": SCALED_TRANSITION_COUNT},
              "witness_origin": origin.record,
              "excluded_targets": origin.plan["excluded_targets"],
              "excluded_targets_sha256": origin.plan["excluded_targets_sha256"],
              "exposure": exposure, "limits": {"routes": MAX_ROUTES, "transitions": MAX_TRANSITIONS,
                  "source_file_bytes": MAX_SOURCE_FILE_BYTES, "source_total_bytes": MAX_SOURCE_TOTAL_BYTES,
                  "corrective_route_trace_bytes": witness.MAX_TRACE_BYTES}}
    return {**result, "plan_sha256": _digest(result)}


def corrective_source_profile_record(epoch: HydraEpoch | None = None) -> dict[str, object]:
    """Declare the single fixed mixture, authenticating metadata but doing no QED."""
    return _plan(_frozen_epoch(epoch), _read_witness_origin())


def _corrective_slice(epoch: HydraEpoch, origin: _WitnessOrigin):
    caps, environment, _, _, _ = native._authority(epoch, AUTHORITY_PROFILE)
    rows, evidence = [], []
    for route in origin.plan["routes"]:
        result = run_proof(route["source"], tuple(route["commands"]), request_id=route["name"],
                           session_id=route["name"], classical=False, on_error="stop", capabilities=caps,
                           trace_byte_limit=witness.MAX_TRACE_BYTES)
        native._checked_result(result, route, caps=caps, environment_sha256=environment.sha256)
        rows.extend(native._rows(epoch, route, result, environment))
        evidence.append({"name": route["name"], "statement": route["statement"],
                         "commands_sha256": route["commands_sha256"], "kernel_checked": True,
                         "proof_nodes": result.proof_nodes, "trace_sha256": _digest(result.trace),
                         "trace": list(result.trace)})
    transitions = tuple(rows)
    expected = tuple({**{key: value for key, value in row.items() if key not in {"schema", "plan_sha256"}},
                      "schema": native.TRANSITION_SCHEMA, "epoch_sha256": epoch.epoch_sha256,
                      "track": native.TEACHER_TRACK, "source": native.TEACHER_SOURCE} for row in origin.rows)
    _require(transitions == expected, "fresh corrective QED states/actions differ from the exact frozen fixture")
    _require(len(evidence) == CORRECTIVE_ROUTE_COUNT and len(transitions) == CORRECTIVE_TRANSITION_COUNT,
             "corrective component changed its fixed route/transition inventory")
    witness._check_intermediates(transitions, {row["statement"] for row in origin.plan["excluded_targets"]})
    counts = {split: witness._empty_counts() for split in ("train", "dev")}
    for row in transitions:
        witness._observe(counts[row["split"]], row)
    coverage = witness._coverage(counts)
    _require({split: counts[split]["rows"] for split in counts} == CORRECTIVE_SPLIT_TRANSITIONS
             and coverage["gate"]["status"] == "covered", "corrective slice lost its actual TRAIN coverage")
    return transitions, evidence, coverage


def _check_union(rows: tuple[dict[str, object], ...], plan: dict[str, object]) -> None:
    declared = {row["id"]: row for row in plan["families"]}
    routes = {row["name"]: row for row in plan["routes"]}
    expected_keys = [(route["name"], index) for route in plan["routes"]
                     for index in range(1, len(route["commands"]) + 1)]
    _require([(row.get("theorem_name"), row.get("step")) for row in rows] == expected_keys,
             "mixed source lost its exact ordered route-step inventory")
    states, splits = {}, Counter()
    for row in rows:
        route = routes[row["theorem_name"]]
        family = declared.get(row["family"])
        _require(family is not None and row["family"] == route["family"]
                 and row["split"] == route["split"] == family["split"]
                 and row["lineage_sha256"] == route["lineage_sha256"] == family["lineage_sha256"],
                 "mixed family/lineage was split or reassigned")
        _require(row["epoch_sha256"] == plan["epoch_sha256"]
                 and row["environment_sha256"] == plan["authority"]["environment_sha256"]
                 and row["theorem"] == route["statement"]
                 and row["action"] == route["commands"][row["step"] - 1]
                 and row["commands_sha256"] == route["commands_sha256"],
                 "mixed transition changed its epoch, authority, goal or command")
        key = (row["environment_sha256"], row["state_sha256"], row["focus"], row["action"])
        _require(key not in states or states[key] == row["split"], "exact state/action crosses the mixed TRAIN/DEV boundary")
        states[key] = row["split"]
        splits[row["split"]] += 1
    _require(dict(splits) == plan["split_transition_counts"], "mixed source changed its full split counts")
    # Both components already checked their own closed intermediates; repeat
    # the common exclusion check after the exact union, without changing text.
    scaled._check_intermediates(rows, {row["statement"] for row in plan["excluded_targets"]})


@dataclass(frozen=True, slots=True)
class CorrectiveSource:
    epoch: HydraEpoch
    curriculum: VerifiedCurriculum
    manifest: dict[str, object]
    payloads: dict[str, bytes]


def build_corrective_source(epoch: HydraEpoch | None = None) -> CorrectiveSource:
    """Freshly check the entire fixed mixture; never adopt saved scaled rows."""
    epoch, origin = _frozen_epoch(epoch), _read_witness_origin()
    plan = _plan(epoch, origin)
    regenerated = scaled.build_scaled_composition_source(epoch)
    _require(type(regenerated) is scaled.ScaledCompositionSource
             and regenerated.epoch == epoch
             and regenerated.manifest["schema"] == scaled.SCALED_COMPOSITION_SCHEMA
             and regenerated.manifest["composition"]["plan"]["plan_sha256"] == plan["scaled_component"]["plan_sha256"],
             "fresh scaled component differs from the declared generator/epoch")
    corrective, correction_evidence, coverage = _corrective_slice(epoch, origin)
    transitions = (*regenerated.curriculum.transitions, *corrective)
    _require(len(transitions) == plan["tactic_decisions"], "mixed source is missing transitions")
    _check_union(transitions, plan)
    curriculum = VerifiedCurriculum(epoch.epoch_sha256, transitions, (), ())
    manifest = curriculum.manifest()
    manifest.update({"schema": CORRECTIVE_SOURCE_SCHEMA, "curriculum_profile": CORRECTIVE_CURRICULUM_PROFILE,
                     "version": epoch.version, "edition_identity_sha256": epoch.edition_identity_sha256,
                     "theorem_dag_sha256": epoch.theorem_dag_sha256,
                     "reviewed_definition_dag_sha256": epoch.reviewed_definition_dag_sha256,
                     "authority_profile": AUTHORITY_PROFILE, "authority": plan["authority"],
                     "prompt_contract": plan["prompt_contract"], "decoder_profile": plan["decoder_profile"],
                     "split_policy": native.COMPOSITION_SPLIT_POLICY, "exposure": plan["exposure"],
                     "composition": {"schema": CORRECTIVE_EVIDENCE_SCHEMA, "plan": plan,
                         "verified_route_count": len(plan["routes"]), "verified_tactic_decisions": len(transitions),
                         "transition_count": len(transitions),
                         "family_route_counts": dict(sorted(Counter(row["family"] for row in plan["routes"]).items())),
                         "teacher_routes": [*regenerated.manifest["composition"]["teacher_routes"], *correction_evidence],
                         "regenerated_scaled_files": {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                                                      for name, raw in sorted(regenerated.payloads.items())},
                         "witness_origin": origin.record, "corrective_coverage": coverage,
                         "exact_cross_split_state_action_overlaps": 0, "excluded_closed_intermediate_hits": 0,
                         "exact_original_target_overlaps": 0, "repeated_routes_added": 0,
                         "independent_verification": "fresh native replay of every scaled and corrective original goal; no trust in saved QED flags",
                         "publication_verification_scope": "same caller process, fresh native proof sessions; not independent-process attestation"},
                     "proof_optimization_claim": "none; fixed authored teachers, no minimality claim",
                     "discovery_claim": "none; no theorem-DAG admission or autonomous/model improvement claim",
                     "open_research_gates": ["H0 full reference/conformance scope", "H1 independently reviewed sealed benchmark", "H5 unseen model advantage"]})
    payloads = {"epoch.json": native._pretty(epoch.to_dict(include_graphs=True)),
                "manifest.json": native._pretty(manifest), "sft.jsonl": encode_jsonl(transitions),
                "preferences.jsonl": b"", "discovery.jsonl": b""}
    _require(all(len(raw) <= MAX_SOURCE_FILE_BYTES for raw in payloads.values())
             and sum(map(len, payloads.values())) <= MAX_SOURCE_TOTAL_BYTES, "mixed source exceeds byte bounds")
    _require(_read_witness_origin() == origin and _plan(epoch, origin) == plan,
             "fixed origin or execution source changed during native replay")
    _require(_frozen_epoch(epoch) == epoch, "epoch changed during native replay")
    return CorrectiveSource(epoch, curriculum, manifest, payloads)


def _protect_origin_destination(directory: Path, identity: tuple[int, int]) -> None:
    current = _directory(FROZEN_WITNESS_DIRECTORY).lstat()
    _require((current.st_dev, current.st_ino) == identity, "frozen witness origin directory changed during publication")
    for ancestor in (directory, *directory.parents):
        try:
            value = ancestor.lstat()
        except FileNotFoundError:
            continue
        _require((value.st_dev, value.st_ino) != identity, "publication must stay outside the immutable witness origin")


def publish_corrective_source(source: CorrectiveSource, directory: Path) -> Path:
    """Fresh-only atomic publication after full replay; existing data survive."""
    from hydra_training_v5.peano_policy.manifest import publish_staged_directory_noreplace
    _require(type(source) is CorrectiveSource, "publication requires an exact CorrectiveSource")
    directory = _directory(directory, fresh=True)
    origin = _directory(FROZEN_WITNESS_DIRECTORY).lstat()
    identity = (origin.st_dev, origin.st_ino)
    _protect_origin_destination(directory, identity)
    fresh = build_corrective_source(source.epoch)
    _require(source == fresh, "refusing altered or stale corrective source evidence")
    _directory(directory, fresh=True)
    _protect_origin_destination(directory, identity)
    directory.parent.mkdir(parents=True, exist_ok=True)
    _directory(directory.parent)
    _protect_origin_destination(directory, identity)
    staging = Path(tempfile.mkdtemp(prefix=f".{directory.name}.partial-", dir=directory.parent))
    for name in SOURCE_FILENAMES:
        with (staging / name).open("xb") as stream:
            stream.write(fresh.payloads[name])
            stream.flush()
            os.fsync(stream.fileno())
    _directory(directory, fresh=True)
    _protect_origin_destination(directory, identity)
    # Failed staging remains inspectable; never replace or clean user data.
    publish_staged_directory_noreplace(staging, directory)
    return directory


def verify_corrective_source(directory: Path) -> VerifiedSource:
    """Require exact current epoch/source bytes and a full fresh native replay."""
    from hydra_training_v5.peano_hydra.posttrain import VerifiedSource
    directory = _directory(directory)
    payloads = _read_directory(directory, SOURCE_FILENAMES, maximum=MAX_SOURCE_TOTAL_BYTES)
    manifest = native._decode(payloads["manifest.json"])
    _require(manifest.get("schema") == CORRECTIVE_SOURCE_SCHEMA
             and manifest.get("curriculum_profile") == CORRECTIVE_CURRICULUM_PROFILE
             and manifest.get("authority_profile") == AUTHORITY_PROFILE,
             "corrective source requires its distinct schema and single explicit profile")
    epoch = _frozen_epoch(None)
    _require(native._decode(payloads["epoch.json"]) == epoch.to_dict(include_graphs=True),
             "saved corrective source differs from the current epoch and both DAGs")
    plan = _plan(epoch, _read_witness_origin())
    _require(type(manifest.get("composition")) is dict
             and manifest["composition"].get("schema") == CORRECTIVE_EVIDENCE_SCHEMA
             and manifest["composition"].get("plan") == plan,
             "saved corrective source has stale or altered origin/execution metadata")
    fresh = build_corrective_source(epoch)
    _require(payloads == fresh.payloads, "saved corrective bytes differ from full freshly checked native evidence")
    _require(_read_directory(directory, SOURCE_FILENAMES, maximum=MAX_SOURCE_TOTAL_BYTES) == payloads,
             "saved corrective source changed during verification")
    return VerifiedSource(directory, epoch, fresh.curriculum, fresh.manifest, payloads)


__all__ = ["CORRECTIVE_SOURCE_SCHEMA", "CORRECTIVE_PLAN_SCHEMA", "CORRECTIVE_EVIDENCE_SCHEMA",
           "CORRECTIVE_CURRICULUM_PROFILE", "AUTHORITY_PROFILE", "SOURCE_FILENAMES",
           "CorrectiveSource", "HydraCorrectiveSourceError", "corrective_source_profile_record",
           "build_corrective_source", "publish_corrective_source", "verify_corrective_source"]
