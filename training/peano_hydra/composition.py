"""Small, exposed native teacher routes; never an enrolled or unseen corpus.

The complete family/seed/script inventory is fixed before replay. Every row is
derived from original-goal kernel QED under the same finite no-import command
authority as the capacity evaluator. The two DEV families are diagnostic
teacher groups, NOT independent mathematical dependency components. This
module performs no model calls, theorem/definition admission, or subprocesses.
Call the complete build/verify pipeline inside one host-owned bounded worker.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import TYPE_CHECKING

from peano_lab.batch import MODEL_V1_COMMANDS, BatchResult, run_proof
from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.ui.prove import SurfaceCapabilities
from training.peano_hydra.curriculum import (
    TRANSITION_SCHEMA, VerifiedCurriculum, encode_jsonl,
)
from training.peano_hydra.epoch import HydraEpoch, freeze_epoch
from training.peano_policy.contract import authority_prompt_environment
from training.peano_policy.prompt import (
    COMPLETION_SUFFIX, CapabilityIdentity, ProofExample, render_prompt,
)
from training.peano_policy.search import state_sha256

if TYPE_CHECKING:
    from training.peano_hydra.posttrain import VerifiedSource


ROOT = Path(__file__).resolve().parents[2]
COMPOSITION_SCHEMA = "peano-hydra-native-composition-source-v1"
COMPOSITION_PLAN_SCHEMA = "peano-hydra-native-composition-plan-v1"
COMPOSITION_PROFILE = "peano-authority-primitive-v1"
COMPOSITION_SPLIT_POLICY = "declared-whole-composition-families-v1"
NATIVE_AUTHORITY_LABEL = "hydra-authority-no-imports-v1"
SOURCE_FILENAMES = (
    "epoch.json", "manifest.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl",
)
SEEDS = (0, 1, 2, 3)
MAX_ROUTES = 64
MAX_ROUTE_DECISIONS = 16
MAX_TOTAL_DECISIONS = 512
MAX_ROUTE_TRACE_BYTES = 256 * 1024
MAX_PROMPT_BYTES = 16 * 1024
MAX_SOURCE_FILE_BYTES = 64 * 1024**2
MAX_SOURCE_TOTAL_BYTES = 96 * 1024**2
TEACHER_TRACK = "compositional_teacher"
TEACHER_SOURCE = "independently_checked_native_composition_teacher"
_AUTHORSHIP = "explicitly-authored-after-public-capacity-32-model-results"
_REPLAY_SOURCE_FILES = (
    "training/peano_hydra/composition.py", "training/peano_hydra/curriculum.py",
    "training/peano_hydra/epoch.py", "training/peano_policy/authority.py",
    "training/peano_policy/contract.py", "training/peano_policy/prompt.py",
    "training/peano_policy/search.py", "training/peano_policy/state_identity.py",
    "peano-lab/py/peano_lab/__init__.py",
    "peano-lab/py/peano_lab/batch.py", "peano-lab/py/peano_lab/ui/__init__.py",
    "peano-lab/py/peano_lab/ui/prove.py", "peano-lab/py/peano_lab/ui/panels.py",
    "peano-lab/py/peano_lab/library/theorems.py",
)
_REPLAY_SOURCE_DIRECTORIES = (
    "peano-lab/py/peano_lab/kernel", "peano-lab/py/peano_lab/engine",
)

# All seeds of a declared family share a diagnostic split. The common exposure
# component below explicitly joins these family groups; this is NOT a semantic
# or theorem-DAG separation and must never be relabeled as an H1 holdout.
_FAMILIES = (
    ("conjunction_transport", "train", "Reorder conjunction and reverse an assumed equality."),
    ("universal_equalities", "train", "Right-zero normalization around a variable-containing sum."),
    ("existential_composition", "train", "Construct a variable-dependent witness satisfying two claims."),
    ("inductive_arithmetic", "train", "Prove a local successor-addition lemma by induction, then distribute."),
    ("nested_zero_induction", "train", "Induction through one to four nested left-zero additions."),
    ("implication_transport", "train", "Transport an equality through an arithmetic context."),
    ("disjunction_injection", "dev", "Supporting exposed diagnostic: introduce a justified disjunction."),
    ("closed_additive_witness", "dev", "Supporting exposed diagnostic: choose a closed numerical witness."),
)


class HydraCompositionError(ValueError):
    """A teacher source lost its fixed proof, authority, or exposure boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HydraCompositionError(message)


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                          separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise HydraCompositionError("composition evidence is not strict JSON") from error


def _pretty(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                       indent=2) + "\n").encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _read(path: Path, *, maximum: int = MAX_SOURCE_FILE_BYTES) -> bytes:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            _require(stat.S_ISREG(before.st_mode) and before.st_size <= maximum,
                     "composition input is not a bounded regular file")
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
        _require(len(raw) <= maximum and len(raw) == before.st_size
                 and (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                 == (after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                 "composition input changed while reading")
        return raw
    except OSError as error:
        raise HydraCompositionError(f"cannot read composition input {path.name}: {error}") from error


def _read_source(directory: Path) -> dict[str, bytes]:
    _require(isinstance(directory, Path), "source directory must be a path")
    _require(directory.is_dir() and not directory.is_symlink(), "composition source must be a regular directory")
    _require(not any(parent.is_symlink() for parent in directory.parents),
             "composition source ancestors must not be symlinks")
    _require({path.name for path in directory.iterdir()} == set(SOURCE_FILENAMES),
             "composition source inventory must contain exactly five files")
    result: dict[str, bytes] = {}
    total = 0
    for name in SOURCE_FILENAMES:
        raw = _read(directory / name, maximum=min(MAX_SOURCE_FILE_BYTES, MAX_SOURCE_TOTAL_BYTES - total))
        result[name] = raw
        total += len(raw)
    _require(total <= MAX_SOURCE_TOTAL_BYTES, "composition source exceeds aggregate byte bound")
    return result


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        _require(key not in result, "duplicate composition JSON field")
        result[key] = value
    return result


def _decode(raw: bytes) -> dict[str, object]:
    def bad_constant(value: str) -> None:
        raise HydraCompositionError(f"non-finite composition JSON: {value}")
    try:
        value = json.loads(raw, object_pairs_hook=_strict_object, parse_constant=bad_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise HydraCompositionError("invalid composition JSON") from error
    _require(type(value) is dict, "composition JSON must be an object")
    return value


def _source_identity() -> dict[str, object]:
    """Bounded native source bytes, not a Git or whole-repository attestation."""
    names = set(_REPLAY_SOURCE_FILES)
    entries_seen = 0
    for relative in _REPLAY_SOURCE_DIRECTORIES:
        directory = ROOT / relative
        _require(directory.is_dir() and not directory.is_symlink(), "native source directory is unsafe")
        pending = [(directory, 0)]
        while pending:
            current, depth = pending.pop()
            with os.scandir(current) as entries:
                for entry in entries:
                    entries_seen += 1
                    _require(entries_seen <= 256, "native source inventory exceeds its entry bound")
                    if entry.name == "__pycache__":
                        continue
                    _require(not entry.is_symlink(), "native source inventory contains a symlink")
                    if entry.is_dir(follow_symlinks=False):
                        _require(depth < 4, "native source inventory exceeds its depth bound")
                        pending.append((Path(entry.path), depth + 1))
                    elif entry.name.endswith(".py"):
                        _require(entry.is_file(follow_symlinks=False), "native source is not a regular Python file")
                        names.add(Path(entry.path).relative_to(ROOT).as_posix())
                    _require(len(names) <= 128, "native source inventory exceeds its file bound")
    files = {name: hashlib.sha256(_read(ROOT / name, maximum=2 * 1024**2)).hexdigest()
             for name in sorted(names)}
    return {"coverage": "direct teacher/grammar sources and bounded native kernel/engine Python inventory; not whole-repository attestation",
            "files": files, "source_files_sha256": _digest(files)}


def execution_capabilities(epoch: HydraEpoch) -> SurfaceCapabilities:
    """New finite native authority; the separately bound epoch grants no imports.

    An Alpha-edition label would load its entire theorem module solely to
    validate an empty allowlist. This new profile deliberately uses a distinct
    native label; it does not change or bypass any existing Alpha authority.
    """
    _require(type(epoch) is HydraEpoch, "native teacher authority requires a frozen epoch identity")
    return SurfaceCapabilities(label=NATIVE_AUTHORITY_LABEL, allowed_commands=MODEL_V1_COMMANDS,
                               allowed_theorems=frozenset())


def _authority(epoch: HydraEpoch, profile: str):
    # Lazy import keeps source inspection independent of the decoder module and
    # avoids a cycle with posttrain's explicit source-schema dispatch.
    from training.peano_policy.authority import (
        AUTHORITY_PRIMITIVE_PROFILE, authority_contract_record, authority_profile_record,
    )
    _require(profile == COMPOSITION_PROFILE == AUTHORITY_PRIMITIVE_PROFILE,
             "composition requires the explicit authority-primitive profile")
    caps = execution_capabilities(epoch)
    _require(caps.allowed_commands == MODEL_V1_COMMANDS and caps.allowed_theorems == frozenset(),
             "composition requires exact finite model-v1 commands and no theorem imports")
    identity = CapabilityIdentity(caps.label, tuple(sorted(caps.allowed_commands)), ())
    environment = authority_prompt_environment(False, identity)
    authority = {"capabilities": identity.to_record(), "environment_sha256": environment.sha256,
                 "classical": False}
    return caps, environment, authority, authority_contract_record(), authority_profile_record(environment)


def _route(family: str, seed: int) -> tuple[str, tuple[str, ...]]:
    k = seed + 1
    if family == "conjunction_transport":
        return (f"forall n m. (n = m /\\ {k} = {k}) -> ({k} = {k} /\\ m = n)",
                ("intro n", "intro m", "intro h", "cases h", "split", "refl", "symm", "assumption"))
    if family == "universal_equalities":
        return f"forall n. (n + {k}) + 0 = n + {k}", ("intro n", "simp")
    if family == "existential_composition":
        return (f"forall n. exists x. (x = n + {k} /\\ x + 1 = n + {k + 1})",
                ("intro n", f"exists n + {k}", "split", "refl", "simp"))
    if family == "inductive_arithmetic":
        return (f"forall n. (n + {k}) * 2 = n * 2 + {2 * k}",
                ("have hs : forall a b. S a + b = S (a + b)", "intro a", "intro b",
                 "induction b", "simp", "simp [IH]", "intro n", "simp [hs]"))
    if family == "nested_zero_induction":
        term = "n"
        for _ in range(k):
            term = f"0 + ({term})"
        return f"forall n. {term} = n", ("intro n", "induction n", "simp", "simp [IH]")
    if family == "implication_transport":
        return (f"forall n m. n = m -> {k} + n = {k} + m",
                ("intro n", "intro m", "intro h", "rewrite h", "refl"))
    if family == "disjunction_injection":
        return (f"forall n. n = {k} -> (n = {k} \\/ n = {k + 1})",
                ("intro n", "intro h", "left", "assumption"))
    if family == "closed_additive_witness":
        return f"exists x. x + {k} = {2 * k}", (f"exists {k}", "norm_num")
    raise HydraCompositionError("undeclared composition family")


def composition_plan(epoch: HydraEpoch, *, profile: str = COMPOSITION_PROFILE) -> dict[str, object]:
    """Declare the entire authored inventory before seeing any replay outcome."""
    _require(type(epoch) is HydraEpoch, "composition requires an exact frozen HydraEpoch")
    caps, environment, authority, prompt_contract, decoder_profile = _authority(epoch, profile)
    from training.peano_policy.authority import validate_authority_tactic
    families, routes = [], []
    catalog_names = {theorem.name for theorem in epoch.theorems}
    for family, split, description in _FAMILIES:
        declaration = {"id": family, "split": split, "description": description,
                       "generator_seeds": list(SEEDS), "authorship": _AUTHORSHIP,
                       "semantic_independence_claim": False}
        lineage = _digest({"kind": "declared-teacher-family-not-mathematical-component",
                           "epoch_sha256": epoch.epoch_sha256, "declaration": declaration})
        declaration["lineage_sha256"] = lineage
        families.append(declaration)
        for seed in SEEDS:
            source, commands = _route(family, seed)
            _require(len(source.encode()) <= 4096 and 1 <= len(commands) <= MAX_ROUTE_DECISIONS,
                     "teacher route exceeds declared bounds")
            formula, names = parse_formula_with_names(source)
            _require(not names, "teacher target must be closed")
            statement = pretty_formula(formula, list(names))
            name = f"hydra_teacher_{family}_{seed:02d}"
            _require(name not in catalog_names, "teacher name impersonates an enrolled theorem")
            for command in commands:
                validate_authority_tactic(command, environment)
            routes.append({"name": name, "family": family, "generator_seed": seed,
                           "lineage_sha256": lineage, "split": split, "source": source,
                           "statement": statement, "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
                           "commands": list(commands), "commands_sha256": _digest(list(commands))})
    _require(len(routes) == len(_FAMILIES) * len(SEEDS) <= MAX_ROUTES,
             "teacher inventory has the wrong route count")
    decisions = sum(len(route["commands"]) for route in routes)
    _require(decisions <= MAX_TOTAL_DECISIONS, "teacher inventory exceeds its decision budget")
    _require(len({route["name"] for route in routes}) == len(routes)
             and len({route["statement_sha256"] for route in routes}) == len(routes),
             "teacher route inventory has duplicate names or exact statements")
    common_component = _digest({"kind": "common-exposed-native-teacher-authoring-component",
                                "epoch_sha256": epoch.epoch_sha256, "authorship": _AUTHORSHIP,
                                "families": [row["id"] for row in families]})
    plan = {
        "schema": COMPOSITION_PLAN_SCHEMA, "epoch_sha256": epoch.epoch_sha256,
        "authority_profile": profile, "authority": authority,
        "prompt_contract": prompt_contract, "decoder_profile": decoder_profile,
        "source_identity": _source_identity(),
        "families": families, "routes": routes, "route_count": len(routes),
        "tactic_decisions": decisions, "split_policy": COMPOSITION_SPLIT_POLICY,
        "limits": {"max_routes": MAX_ROUTES, "max_route_decisions": MAX_ROUTE_DECISIONS,
                   "max_total_decisions": MAX_TOTAL_DECISIONS, "max_route_trace_bytes": MAX_ROUTE_TRACE_BYTES,
                   "max_prompt_bytes": MAX_PROMPT_BYTES},
        "exposure": {"authorship": _AUTHORSHIP, "guided_teacher_proofs": True,
                     "model_generated": False, "public_and_correlated": True,
                     "public_capacity_goals_may_be_exact_teacher_targets": True,
                     "common_exposure_component_sha256": common_component,
                     "declared_family_groups_are_mathematical_components": False,
                     "eligible_for_unseen_model_comparison": False,
                     "semantic_equivalence_complete": False, "independent_human_review": False,
                     "sealed_benchmark": False, "research_claim_eligible": False,
                     "alpha_admitted": False, "dag_mutated": False},
    }
    plan["plan_sha256"] = _digest(plan)
    return plan


def composition_profile_record(epoch: HydraEpoch | None = None, *, profile: str = COMPOSITION_PROFILE) -> dict[str, object]:
    """Cheap declaration/profile record; does not execute or claim checked proofs."""
    return composition_plan(freeze_epoch(ROOT) if epoch is None else epoch, profile=profile)


def _checked_result(result: BatchResult, route: dict[str, object], *, caps: SurfaceCapabilities,
                    environment_sha256: str) -> None:
    _require(type(result) is BatchResult and result.status == "proved" and result.kernel_checked is True
             and result.theorem == route["statement"] and not result.goals and result.failed_tactics == 0
             and result.tactics_applied == len(route["commands"])
             and result.tactics_requested == len(route["commands"])
             and result.surface == caps.label and result.environment_sha256 == environment_sha256
             and result.classical is False and result.on_error == "stop"
             and result.error is None and result.error_type is None and result.failed_step is None
             and type(result.proof_nodes) is int and result.proof_nodes > 0,
             "teacher route lacks original-goal native kernel QED")
    trace = result.trace
    _require(type(trace) is tuple and len(trace) == len(route["commands"]) + 1,
             "teacher route has an incomplete transition trace")
    footer = trace[-1]
    _require(type(footer) is dict and footer.get("qed") is True
             and footer.get("theorem") == route["statement"]
             and footer.get("proof_size") == result.proof_nodes
             and footer.get("tactic_count") == len(route["commands"]),
             "teacher trace lost its exact original-goal QED footer")
    _require(type(trace[-2]) is dict and trace[-2].get("goals_after") == [],
             "teacher trace did not close its final goal")


def _rows(epoch: HydraEpoch, route: dict[str, object], result: BatchResult, environment):
    rows = []
    for index, trace in enumerate(result.trace[:-1], 1):
        command = route["commands"][index - 1]
        _require(type(trace) is dict and trace.get("status") == "ok" and trace.get("error") is None
                 and trace.get("step") == index and trace.get("session") == result.session_id
                 and trace.get("tactic") == command,
                 "teacher transition differs from its declared primitive step")
        before, after, focus = trace.get("goals_before"), trace.get("goals_after"), trace.get("focus")
        _require(type(before) is list and before and all(type(goal) is str for goal in before)
                 and type(after) is list and all(type(goal) is str for goal in after)
                 and type(focus) is int and 0 <= focus < len(before),
                 "teacher transition has an invalid complete state")
        if index > 1:
            _require(before == result.trace[index - 2]["goals_after"], "teacher trace is disconnected")
        prompt = render_prompt(goals=tuple(before), focus=focus, environment=environment)
        _require(len(prompt.encode()) <= MAX_PROMPT_BYTES, "teacher prompt exceeds its byte bound")
        example = ProofExample(example_id=f"{route['name']}:{index}", prompt=prompt,
                               completion=command + COMPLETION_SUFFIX,
                               environment_sha256=environment.sha256)
        rows.append({
            "schema": TRANSITION_SCHEMA, "epoch_sha256": epoch.epoch_sha256,
            "theorem_name": route["name"], "theorem": route["statement"],
            "track": TEACHER_TRACK, "source": TEACHER_SOURCE, "family": route["family"],
            "authority_profile": COMPOSITION_PROFILE, "lineage_sha256": route["lineage_sha256"],
            "split": route["split"], "step": index, "state_sha256": state_sha256(tuple(before)),
            "goals_before": before, "goals_after": after, "focus": focus,
            "action": example.tactic, "action_head": example.tactic.split(" ", 1)[0],
            "prompt": example.prompt, "completion": example.completion,
            "environment_sha256": environment.sha256, "commands_sha256": route["commands_sha256"],
            "proof_nodes": result.proof_nodes, "kernel_checked": True, "research_claim_eligible": False,
        })
    return tuple(rows)


def _check_split(rows: tuple[dict[str, object], ...]) -> None:
    declared = {family: split for family, split, _ in _FAMILIES}
    seen: dict[tuple[object, ...], str] = {}
    for row in rows:
        _require(row["family"] in declared and row["split"] == declared[row["family"]],
                 "teacher family was split or silently reassigned")
        # Ignore lineage/name: they must not hide an exact cross-split duplicate.
        key = (row["environment_sha256"], row["state_sha256"], row["focus"], row["action"])
        _require(key not in seen or seen[key] == row["split"],
                 "exact teacher state/action leaked across diagnostic splits")
        seen[key] = row["split"]
    _require({row["split"] for row in rows} == {"train", "dev"}, "teacher source lost a declared split")


@dataclass(frozen=True, slots=True)
class CompositionSource:
    epoch: HydraEpoch
    curriculum: VerifiedCurriculum
    manifest: dict[str, object]
    payloads: dict[str, bytes]


def build_composition_source(epoch: HydraEpoch | None = None, *, profile: str = COMPOSITION_PROFILE) -> CompositionSource:
    """Build fixed exposed teacher evidence in memory; never publish partial QED."""
    if epoch is None:
        epoch = freeze_epoch(ROOT)
    plan = composition_plan(epoch, profile=profile)
    caps, environment, authority, prompt_contract, decoder_profile = _authority(epoch, profile)
    rows, evidence = [], []
    for route in plan["routes"]:
        result = run_proof(route["source"], tuple(route["commands"]), request_id=route["name"],
                           session_id=route["name"], classical=False, on_error="stop",
                           capabilities=caps, trace_byte_limit=MAX_ROUTE_TRACE_BYTES)
        _checked_result(result, route, caps=caps, environment_sha256=environment.sha256)
        rows.extend(_rows(epoch, route, result, environment))
        evidence.append({"name": route["name"], "statement": route["statement"],
                         "commands_sha256": route["commands_sha256"], "kernel_checked": True,
                         "proof_nodes": result.proof_nodes, "trace_sha256": _digest(result.trace),
                         "trace": list(result.trace)})
    transitions = tuple(rows)
    _require(len(transitions) == plan["tactic_decisions"], "teacher row inventory differs from declared decisions")
    _check_split(transitions)
    curriculum = VerifiedCurriculum(epoch.epoch_sha256, transitions, (), ())
    manifest = curriculum.manifest()
    manifest.update({
        "schema": COMPOSITION_SCHEMA, "version": epoch.version,
        "edition_identity_sha256": epoch.edition_identity_sha256,
        "theorem_dag_sha256": epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": epoch.reviewed_definition_dag_sha256,
        "authority_profile": profile, "authority": authority,
        "prompt_contract": prompt_contract, "decoder_profile": decoder_profile,
        "split_policy": COMPOSITION_SPLIT_POLICY, "exposure": plan["exposure"],
        "composition": {"plan": plan, "teacher_routes": evidence,
                        "verified_route_count": len(evidence), "verified_tactic_decisions": len(transitions),
                        "family_route_counts": dict(sorted(Counter(route["family"] for route in plan["routes"]).items())),
                        "exact_cross_split_state_action_overlaps": 0,
                        "independent_verification": "regenerate every fixed teacher route against the original goal"},
        "proof_optimization_claim": "none; explicitly authored teacher routes, not minimality or autonomous discovery",
        "discovery_claim": "none; no theorem admission, independent discovery, or unseen-model claim",
        "open_research_gates": ["H0 full reference/conformance scope", "H1 independently reviewed sealed benchmark",
                                "H5 unseen model advantage; not established by exposed teachers"],
    })
    payloads = {"epoch.json": _pretty(epoch.to_dict(include_graphs=True)),
                "sft.jsonl": encode_jsonl(transitions), "preferences.jsonl": b"", "discovery.jsonl": b""}
    payloads["manifest.json"] = _pretty(manifest)
    _require(all(len(raw) <= MAX_SOURCE_FILE_BYTES for raw in payloads.values())
             and sum(map(len, payloads.values())) <= MAX_SOURCE_TOTAL_BYTES,
             "composition source exceeds file/aggregate bounds")
    _require(composition_plan(epoch, profile=profile) == plan,
             "teacher generator or authority changed during replay")
    return CompositionSource(epoch, curriculum, manifest, payloads)


def publish_composition_source(source: CompositionSource, directory: Path) -> Path:
    """Independently replay an in-memory source, then atomically publish fresh."""
    from training.peano_policy.manifest import publish_staged_directory_noreplace
    _require(type(source) is CompositionSource, "publication requires an exact CompositionSource")
    directory = Path(directory).absolute()
    _require(not directory.exists() and not directory.is_symlink(), "composition destination already exists")
    _require(not any(parent.is_symlink() for parent in directory.parents), "composition output ancestors must not be symlinks")
    fresh = build_composition_source(source.epoch, profile=source.manifest.get("authority_profile"))
    _require(source.payloads == fresh.payloads and source.manifest == fresh.manifest
             and source.curriculum == fresh.curriculum, "refusing to publish altered or unverified teacher data")
    directory.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{directory.name}.partial-", dir=directory.parent))
    # Interrupted staging is retained for inspection; no existing user output
    # or failed source is overwritten or recursively removed.
    for name in SOURCE_FILENAMES:
        with (staging / name).open("xb") as stream:
            stream.write(fresh.payloads[name])
            stream.flush()
            os.fsync(stream.fileno())
    publish_staged_directory_noreplace(staging, directory)
    return directory


def verify_composition_source(directory: Path) -> VerifiedSource:
    """Authenticate exact bytes and current epoch by redoing every teacher QED."""
    from training.peano_hydra.posttrain import VerifiedSource
    directory = Path(directory).absolute()
    payloads = _read_source(directory)
    manifest = _decode(payloads["manifest.json"])
    _require(manifest.get("schema") == COMPOSITION_SCHEMA
             and manifest.get("authority_profile") == COMPOSITION_PROFILE,
             "composition source requires its distinct schema and explicit profile")
    epoch = freeze_epoch(ROOT)
    _require(_decode(payloads["epoch.json"]) == epoch.to_dict(include_graphs=True),
             "composition source differs from the current frozen epoch and both DAGs")
    plan = composition_plan(epoch)
    _require(type(manifest.get("composition")) is dict
             and manifest["composition"].get("plan") == plan,
             "composition source changed the declared generator, routes, families, or authority")
    fresh = build_composition_source(epoch)
    _require(payloads == fresh.payloads, "composition bytes differ from independently regenerated native QED evidence")
    _require(_read_source(directory) == payloads, "composition source changed during independent replay")
    return VerifiedSource(directory, epoch, fresh.curriculum, fresh.manifest, payloads)


__all__ = [
    "COMPOSITION_SCHEMA", "COMPOSITION_PLAN_SCHEMA", "COMPOSITION_PROFILE", "COMPOSITION_SPLIT_POLICY",
    "NATIVE_AUTHORITY_LABEL", "execution_capabilities",
    "CompositionSource", "HydraCompositionError", "composition_plan", "build_composition_source",
    "composition_profile_record", "publish_composition_source", "verify_composition_source",
]
