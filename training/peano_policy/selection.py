"""Deterministic whole-session selection for the model-v3 PA curriculum.

The checked dataset builder remains the authority for whether a row is valid
training data.  This module performs only a *dropping* transformation over
already validated builder rows:

* every predecessor-prefix catalog transition is mandatory;
* synthetic examples are selected as complete proof sessions;
* every reviewed schema is anchored by one complete session;
* all root-tactic heads receive exactly the same number of sessions; and
* every choice is content-independent, seed-bound, and order-independent.

An exact row quota is generally incompatible with complete sessions because
sessions have different lengths.  The public contract therefore uses a hard
synthetic-row ceiling.  It admits only complete balanced rounds and reports
the deterministic unused remainder in its attestation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from .prompt import ProofExample


SELECTION_FORMAT = "peano-policy-v3-curriculum-selection"
SELECTION_VERSION = 1
SELECTION_ALGORITHM = "catalog-all-schema-anchor-balanced-whole-sessions-v1"
CATALOG_LANE = "catalog-predecessor-prefix-v1"
SYNTHETIC_LANE = "synthetic-root-balanced"
MODEL_V3_SYNTHETIC_ROW_CEILING = 12_288

MODEL_V3_ROOT_HEADS = (
    "compact_arith",
    "congr",
    "exists",
    "induction",
    "intro",
    "left",
    "norm_num",
    "refl",
    "rewrite",
    "right",
    "ring",
    "split",
    "symm",
    "trans",
)

MODEL_V3_SCHEMA_HEADS = (
    ("root-equality-refl", "refl"),
    ("root-equality-norm", "norm_num"),
    ("root-equality-ring", "ring"),
    ("root-equality-rewrite", "rewrite"),
    ("root-equality-trans", "trans"),
    ("root-equality-symm", "symm"),
    ("root-equality-congr", "congr"),
    ("root-equality-compact", "compact_arith"),
    ("root-existential", "exists"),
    ("root-conjunction", "split"),
    ("root-disjunction-left", "left"),
    ("root-disjunction-right", "right"),
    ("reused-logic-identity", "intro"),
    ("reused-logic-and-swap", "intro"),
    ("reused-logic-or-swap", "intro"),
    ("reused-logic-and-left", "intro"),
    ("reused-logic-compose", "intro"),
    ("reused-equality-symmetry", "intro"),
    ("reused-equality-transitivity", "intro"),
    ("reused-equality-successor-congruence", "intro"),
    ("reused-equality-add-congruence", "intro"),
    ("reused-equality-rewrite-forward", "intro"),
    ("reused-equality-rewrite-reverse", "intro"),
    ("reused-recurrence-pa3", "intro"),
    ("reused-recurrence-pa4", "intro"),
    ("reused-recurrence-pa5", "intro"),
    ("reused-recurrence-pa6", "intro"),
    ("reused-recurrence-pa1", "intro"),
    ("reused-recurrence-pa2", "intro"),
    ("reused-witness-right", "intro"),
    ("reused-witness-left", "intro"),
    ("reused-witness-pair", "intro"),
    ("reused-witness-add-zero", "intro"),
    ("reused-witness-mul-zero", "intro"),
    ("reused-witness-repack", "intro"),
    ("reused-witness-two", "intro"),
    ("reused-arithmetic-closed-norm", "norm_num"),
    ("reused-arithmetic-open-norm", "intro"),
    ("reused-arithmetic-ring-square", "intro"),
    ("reused-arithmetic-ring-product", "intro"),
    ("reused-arithmetic-compact", "intro"),
    ("reused-logic-assumption", "intro"),
    ("reused-logic-exfalso", "intro"),
    ("reused-logic-specialize", "intro"),
    ("reused-logic-forall-elim", "intro"),
    ("reused-logic-have", "intro"),
    ("reused-logic-suffices", "intro"),
    ("reused-induction-add-zero", "induction"),
    ("reused-induction-mul-zero", "induction"),
    ("reused-induction-add-one", "induction"),
    ("reused-induction-explicit-IH", "induction"),
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class CurriculumSelectionError(ValueError):
    """The validated population cannot satisfy the selection contract."""


def _text(label: str, value: object) -> str:
    if (
        type(value) is not str
        or not value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise CurriculumSelectionError(f"{label} must be non-empty safe text")
    return value


def _positive_integer(label: str, value: object) -> int:
    if type(value) is not int or value < 1:
        raise CurriculumSelectionError(f"{label} must be a positive integer")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise CurriculumSelectionError(
            f"selection evidence is not canonical JSON: {exc}"
        ) from exc
    return text.encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _rank(seed: str, purpose: str, *parts: str) -> tuple[str, tuple[str, ...]]:
    material = {
        "algorithm": SELECTION_ALGORITHM,
        "parts": list(parts),
        "purpose": purpose,
        "seed": seed,
    }
    return _sha256_json(material), parts


@dataclass(frozen=True, slots=True)
class CurriculumSelectionContract:
    """Closed population requirements, independent of seed and row ceiling."""

    library_size: int
    expected_catalog_rows: int
    root_heads: tuple[str, ...]
    schema_heads: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _positive_integer("library_size", self.library_size)
        if (
            type(self.expected_catalog_rows) is not int
            or self.expected_catalog_rows < self.library_size
        ):
            raise CurriculumSelectionError(
                "expected_catalog_rows must cover every catalog target"
            )
        if type(self.root_heads) is not tuple or not self.root_heads:
            raise CurriculumSelectionError("root_heads must be a non-empty tuple")
        for head in self.root_heads:
            _text("root head", head)
        if len(set(self.root_heads)) != len(self.root_heads):
            raise CurriculumSelectionError("root_heads must be unique")
        if type(self.schema_heads) is not tuple or not self.schema_heads:
            raise CurriculumSelectionError(
                "schema_heads must be a non-empty tuple"
            )
        schemas: set[str] = set()
        observed_heads: set[str] = set()
        for pair in self.schema_heads:
            if type(pair) is not tuple or len(pair) != 2:
                raise CurriculumSelectionError(
                    "schema_heads entries must be (schema, head) pairs"
                )
            schema = _text("schema", pair[0])
            head = _text("schema root head", pair[1])
            if schema in schemas:
                raise CurriculumSelectionError("schema names must be unique")
            if head not in self.root_heads:
                raise CurriculumSelectionError(
                    f"schema {schema!r} uses an unreviewed root head"
                )
            schemas.add(schema)
            observed_heads.add(head)
        if observed_heads != set(self.root_heads):
            raise CurriculumSelectionError(
                "every reviewed root head must own at least one schema"
            )

    @property
    def schema_map(self) -> dict[str, str]:
        return dict(self.schema_heads)

    def to_record(self) -> dict[str, object]:
        schema_record = [
            {"schema": schema, "root_head": head}
            for schema, head in self.schema_heads
        ]
        return {
            "library_size": self.library_size,
            "expected_catalog_rows": self.expected_catalog_rows,
            "root_heads": list(self.root_heads),
            "schema_count": len(self.schema_heads),
            "schema_heads_sha256": _sha256_json(schema_record),
        }


MODEL_V3_SELECTION_CONTRACT = CurriculumSelectionContract(
    library_size=247,
    expected_catalog_rows=8_494,
    root_heads=MODEL_V3_ROOT_HEADS,
    schema_heads=MODEL_V3_SCHEMA_HEADS,
)


@dataclass(frozen=True, slots=True)
class CurriculumRow:
    """Selection fields extracted from one structurally validated builder row."""

    example: ProofExample
    session: str
    step: int
    expected_steps: int
    lane: str
    library_size: int
    row_sha256: str
    script_sha256: str
    catalog_target_index: int | None = None
    catalog_target_name: str | None = None
    schema: str | None = None
    root_head: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.example, ProofExample):
            raise CurriculumSelectionError(
                "curriculum row must contain a validated ProofExample"
            )
        session = _text("session", self.session)
        step = _positive_integer("step", self.step)
        expected = _positive_integer("expected_steps", self.expected_steps)
        if step > expected:
            raise CurriculumSelectionError("step exceeds the complete session length")
        if self.example.example_id != f"{session}:{step}":
            raise CurriculumSelectionError(
                "ProofExample id does not match the row session and step"
            )
        _positive_integer("library_size", self.library_size)
        if type(self.row_sha256) is not str or _SHA256_RE.fullmatch(
            self.row_sha256
        ) is None:
            raise CurriculumSelectionError("row_sha256 must be lowercase SHA-256")
        if type(self.script_sha256) is not str or _SHA256_RE.fullmatch(
            self.script_sha256
        ) is None:
            raise CurriculumSelectionError(
                "script_sha256 must be lowercase SHA-256"
            )
        if self.lane == CATALOG_LANE:
            if (
                type(self.catalog_target_index) is not int
                or not 0 <= self.catalog_target_index < self.library_size
            ):
                raise CurriculumSelectionError(
                    "catalog row has an invalid target index"
                )
            _text("catalog target name", self.catalog_target_name)
            if self.schema is not None or self.root_head is not None:
                raise CurriculumSelectionError(
                    "catalog rows must not claim synthetic strata"
                )
        elif self.lane == SYNTHETIC_LANE:
            if (
                self.catalog_target_index is not None
                or self.catalog_target_name is not None
            ):
                raise CurriculumSelectionError(
                    "synthetic rows must not claim a catalog target"
                )
            _text("synthetic schema", self.schema)
            _text("synthetic root head", self.root_head)
        else:
            raise CurriculumSelectionError(f"unsupported curriculum lane {self.lane!r}")


def row_from_validated_record(
    example: ProofExample,
    record: Mapping[str, Any],
) -> CurriculumRow:
    """Extract selector evidence from one already validated builder record.

    This adapter deliberately checks the redundancy used by selection.  It is
    not a replacement for :func:`training.peano_policy.data.example_from_record`;
    callers must run that structural validator first and pass its exact
    :class:`ProofExample` result here.
    """

    if not isinstance(example, ProofExample):
        raise CurriculumSelectionError(
            "record adapter requires a validated ProofExample"
        )
    if not isinstance(record, Mapping):
        raise CurriculumSelectionError("builder row must be a mapping")
    session = _text("row session", record.get("session"))
    step = _positive_integer("row step", record.get("step"))
    if record.get("surface") != "model-v3" or record.get("split") != "train":
        raise CurriculumSelectionError(
            "model-v3 curriculum selection accepts training rows only"
        )
    if (
        record.get("prompt") != example.prompt
        or record.get("completion") != example.completion
        or record.get("environment_sha256") != example.environment_sha256
        or example.example_id != f"{session}:{step}"
    ):
        raise CurriculumSelectionError(
            "ProofExample does not match its structurally validated row"
        )
    metadata = record.get("metadata")
    if not isinstance(metadata, Mapping):
        raise CurriculumSelectionError("builder row metadata must be a mapping")
    library_size = _positive_integer(
        "metadata library_size", metadata.get("library_size")
    )
    prefix = metadata.get("library_prefix_length")
    if type(prefix) is not int or not 0 <= prefix <= library_size:
        raise CurriculumSelectionError("metadata has an invalid library prefix")

    trajectory_marker = metadata.get("trajectory")
    lane_marker = metadata.get("lane")
    catalog = trajectory_marker == CATALOG_LANE
    synthetic = lane_marker == SYNTHETIC_LANE
    if catalog == synthetic:
        raise CurriculumSelectionError(
            "row must claim exactly one reviewed curriculum lane"
        )
    if (catalog and "lane" in metadata) or (
        synthetic and "trajectory" in metadata
    ):
        raise CurriculumSelectionError(
            "row mixes catalog and synthetic curriculum markers"
        )
    tactics = metadata.get("tactics")
    if (
        type(tactics) is not list
        or not tactics
        or any(type(tactic) is not str or not tactic for tactic in tactics)
    ):
        raise CurriculumSelectionError("row metadata has no exact tactic script")
    expected_steps = len(tactics)
    script_sha256 = _sha256_json(tactics)
    if step > expected_steps or example.tactic != tactics[step - 1]:
        raise CurriculumSelectionError(
            "row completion differs from its metadata tactic script"
        )

    try:
        row_sha256 = hashlib.sha256(_canonical_json_bytes(record)).hexdigest()
    except CurriculumSelectionError:
        raise

    if catalog:
        target_index = metadata.get("library_target_index")
        target_name = metadata.get("library_target_name")
        if prefix != target_index:
            raise CurriculumSelectionError(
                "catalog target index differs from its predecessor prefix"
            )
        return CurriculumRow(
            example=example,
            session=session,
            step=step,
            expected_steps=expected_steps,
            lane=CATALOG_LANE,
            library_size=library_size,
            row_sha256=row_sha256,
            script_sha256=script_sha256,
            catalog_target_index=target_index,
            catalog_target_name=target_name,
        )

    tactic_rows = metadata.get("tactic_rows")
    if (
        prefix != library_size
        or type(tactic_rows) is not int
        or tactic_rows != expected_steps
    ):
        raise CurriculumSelectionError(
            "synthetic session is not bound to its full-prefix tactic count"
        )
    return CurriculumRow(
        example=example,
        session=session,
        step=step,
        expected_steps=expected_steps,
        lane=SYNTHETIC_LANE,
        library_size=library_size,
        row_sha256=row_sha256,
        script_sha256=script_sha256,
        schema=metadata.get("template"),
        root_head=metadata.get("root_first_tactic_head"),
    )


@dataclass(frozen=True, slots=True)
class _Session:
    session: str
    lane: str
    rows: tuple[CurriculumRow, ...]
    catalog_target_index: int | None
    catalog_target_name: str | None
    schema: str | None
    root_head: str | None

    @property
    def row_count(self) -> int:
        return len(self.rows)


def _group_complete_sessions(
    rows: Sequence[CurriculumRow],
    *,
    contract: CurriculumSelectionContract,
) -> tuple[tuple[_Session, ...], tuple[_Session, ...]]:
    if not rows:
        raise CurriculumSelectionError("curriculum population is empty")
    by_session: dict[str, list[CurriculumRow]] = defaultdict(list)
    example_ids: set[str] = set()
    row_hashes: set[str] = set()
    for row in rows:
        if not isinstance(row, CurriculumRow):
            raise CurriculumSelectionError(
                "selection accepts CurriculumRow values only"
            )
        if row.library_size != contract.library_size:
            raise CurriculumSelectionError(
                "row library size differs from the selection contract"
            )
        if row.example.example_id in example_ids:
            raise CurriculumSelectionError(
                f"duplicate example id {row.example.example_id!r}"
            )
        if row.row_sha256 in row_hashes:
            raise CurriculumSelectionError("duplicate canonical builder row")
        example_ids.add(row.example.example_id)
        row_hashes.add(row.row_sha256)
        by_session[row.session].append(row)

    catalog: list[_Session] = []
    synthetic: list[_Session] = []
    for session_name, members in by_session.items():
        ordered = tuple(sorted(members, key=lambda row: row.step))
        first = ordered[0]
        expected_signature = (
            first.lane,
            first.expected_steps,
            first.script_sha256,
            first.catalog_target_index,
            first.catalog_target_name,
            first.schema,
            first.root_head,
        )
        if any(
            (
                row.lane,
                row.expected_steps,
                row.script_sha256,
                row.catalog_target_index,
                row.catalog_target_name,
                row.schema,
                row.root_head,
            )
            != expected_signature
            for row in ordered
        ):
            raise CurriculumSelectionError(
                f"session {session_name!r} changes its curriculum metadata"
            )
        expected_steps = tuple(range(1, first.expected_steps + 1))
        if tuple(row.step for row in ordered) != expected_steps:
            raise CurriculumSelectionError(
                f"session {session_name!r} is not a complete step sequence"
            )
        grouped = _Session(
            session=session_name,
            lane=first.lane,
            rows=ordered,
            catalog_target_index=first.catalog_target_index,
            catalog_target_name=first.catalog_target_name,
            schema=first.schema,
            root_head=first.root_head,
        )
        (catalog if first.lane == CATALOG_LANE else synthetic).append(grouped)
    return tuple(catalog), tuple(synthetic)


def _validate_catalog(
    sessions: Sequence[_Session],
    *,
    contract: CurriculumSelectionContract,
) -> tuple[_Session, ...]:
    by_target: dict[int, _Session] = {}
    names: set[str] = set()
    for session in sessions:
        index = session.catalog_target_index
        name = session.catalog_target_name
        if type(index) is not int or type(name) is not str:
            raise CurriculumSelectionError(
                "catalog session lost its target identity"
            )
        if index in by_target:
            raise CurriculumSelectionError(
                f"catalog target index {index} has multiple sessions"
            )
        if name in names:
            raise CurriculumSelectionError(
                f"catalog target name {name!r} is duplicated"
            )
        by_target[index] = session
        names.add(name)
    expected = set(range(contract.library_size))
    if set(by_target) != expected:
        missing = sorted(expected - set(by_target))
        extra = sorted(set(by_target) - expected)
        raise CurriculumSelectionError(
            "catalog target coverage is not exact"
            + (f"; missing={missing}" if missing else "")
            + (f"; extra={extra}" if extra else "")
        )
    ordered = tuple(by_target[index] for index in range(contract.library_size))
    row_count = sum(session.row_count for session in ordered)
    if row_count != contract.expected_catalog_rows:
        raise CurriculumSelectionError(
            f"catalog has {row_count} rows, expected "
            f"{contract.expected_catalog_rows}"
        )
    return ordered


def _validate_synthetic(
    sessions: Sequence[_Session],
    *,
    contract: CurriculumSelectionContract,
) -> tuple[dict[str, list[_Session]], dict[str, list[_Session]]]:
    schema_map = contract.schema_map
    by_schema: dict[str, list[_Session]] = defaultdict(list)
    by_head: dict[str, list[_Session]] = defaultdict(list)
    for session in sessions:
        schema = session.schema
        head = session.root_head
        if type(schema) is not str or type(head) is not str:
            raise CurriculumSelectionError(
                "synthetic session lost its schema or root head"
            )
        if schema not in schema_map:
            raise CurriculumSelectionError(
                f"synthetic session names unreviewed schema {schema!r}"
            )
        if schema_map[schema] != head:
            raise CurriculumSelectionError(
                f"schema {schema!r} uses root head {head!r}, expected "
                f"{schema_map[schema]!r}"
            )
        by_schema[schema].append(session)
        by_head[head].append(session)
    missing_schemas = [
        schema for schema, _ in contract.schema_heads if not by_schema[schema]
    ]
    missing_heads = [head for head in contract.root_heads if not by_head[head]]
    if missing_schemas or missing_heads:
        raise CurriculumSelectionError(
            "synthetic population lacks reviewed strata"
            + (f"; schemas={missing_schemas}" if missing_schemas else "")
            + (f"; heads={missing_heads}" if missing_heads else "")
        )
    return dict(by_schema), dict(by_head)


def _select_synthetic_sessions(
    sessions_by_schema: Mapping[str, Sequence[_Session]],
    sessions_by_head: Mapping[str, Sequence[_Session]],
    *,
    contract: CurriculumSelectionContract,
    seed: str,
    row_ceiling: int,
) -> tuple[tuple[_Session, ...], int, int]:
    selected: dict[str, _Session] = {}
    for schema, _ in contract.schema_heads:
        candidates = sessions_by_schema[schema]
        anchor = min(
            candidates,
            key=lambda session: _rank(
                seed, "schema-anchor", schema, session.session
            ),
        )
        selected[anchor.session] = anchor

    anchor_counts = Counter(
        session.root_head for session in selected.values()
    )
    balance_target = max(anchor_counts.values())
    remaining: dict[str, list[_Session]] = {}
    for head in contract.root_heads:
        candidates = sorted(
            (
                session
                for session in sessions_by_head[head]
                if session.session not in selected
            ),
            key=lambda session: _rank(
                seed, "head-fill", head, session.session
            ),
        )
        required = balance_target - anchor_counts[head]
        if len(candidates) < required:
            raise CurriculumSelectionError(
                f"root head {head!r} cannot reach the anchor balance target"
            )
        for session in candidates[:required]:
            selected[session.session] = session
        remaining[head] = candidates[required:]

    selected_rows = sum(session.row_count for session in selected.values())
    if selected_rows > row_ceiling:
        raise CurriculumSelectionError(
            "synthetic row ceiling cannot fit the mandatory schema anchors "
            "and head rebalance"
        )

    balanced_rounds = 0
    while all(remaining[head] for head in contract.root_heads):
        candidate_round = tuple(
            remaining[head][0] for head in contract.root_heads
        )
        round_rows = sum(session.row_count for session in candidate_round)
        if selected_rows + round_rows > row_ceiling:
            break
        for head, session in zip(
            contract.root_heads, candidate_round, strict=True
        ):
            selected[session.session] = session
            del remaining[head][0]
        selected_rows += round_rows
        balanced_rounds += 1

    counts = Counter(session.root_head for session in selected.values())
    if set(counts) != set(contract.root_heads) or len(set(counts.values())) != 1:
        raise CurriculumSelectionError(
            "internal selection error: root-head session counts are unbalanced"
        )
    ordered = tuple(
        sorted(
            selected.values(),
            key=lambda session: (
                contract.root_heads.index(str(session.root_head)),
                session.session,
            ),
        )
    )
    return ordered, balance_target, balanced_rounds


def _bind_selection_rows(
    rows: tuple[CurriculumRow, ...], record: Mapping[str, object]
) -> None:
    """Fail closed unless the immutable evidence describes these exact rows."""

    if type(rows) is not tuple or not rows:
        raise CurriculumSelectionError(
            "selection result rows must be a non-empty tuple"
        )
    if any(not isinstance(row, CurriculumRow) for row in rows):
        raise CurriculumSelectionError(
            "selection result contains a non-curriculum row"
        )
    if (
        record.get("format") != SELECTION_FORMAT
        or record.get("v") != SELECTION_VERSION
        or record.get("algorithm") != SELECTION_ALGORITHM
    ):
        raise CurriculumSelectionError(
            "selection result has an incompatible record identity"
        )
    contract = record.get("contract")
    selected = record.get("selected")
    if not isinstance(contract, Mapping) or not isinstance(selected, Mapping):
        raise CurriculumSelectionError(
            "selection result lacks contract or selected-row evidence"
        )
    library_size = contract.get("library_size")
    root_heads = contract.get("root_heads")
    if type(library_size) is not int or library_size < 1:
        raise CurriculumSelectionError(
            "selection result has an invalid contract library size"
        )
    if (
        type(root_heads) is not list
        or not root_heads
        or any(type(head) is not str or not head for head in root_heads)
        or len(set(root_heads)) != len(root_heads)
    ):
        raise CurriculumSelectionError(
            "selection result has invalid contract root heads"
        )
    if any(row.library_size != library_size for row in rows):
        raise CurriculumSelectionError(
            "selection rows differ from the attested library size"
        )

    ids = [row.example.example_id for row in rows]
    row_evidence = [
        (row.example.example_id, row.row_sha256) for row in rows
    ]
    if len(set(ids)) != len(ids) or len({item[1] for item in row_evidence}) != len(
        row_evidence
    ):
        raise CurriculumSelectionError(
            "selection result repeats an example or builder row"
        )
    if (
        selected.get("rows") != len(rows)
        or selected.get("example_ids_sha256") != _sha256_json(sorted(ids))
        or selected.get("rows_sha256") != _sha256_json(sorted(row_evidence))
    ):
        raise CurriculumSelectionError(
            "selection result rows differ from their attested identity"
        )

    head_positions = {head: index for index, head in enumerate(root_heads)}
    if any(
        row.lane == SYNTHETIC_LANE and row.root_head not in head_positions
        for row in rows
    ):
        raise CurriculumSelectionError(
            "selection row uses a root head outside its attested contract"
        )

    def canonical_key(row: CurriculumRow) -> tuple[object, ...]:
        if row.lane == CATALOG_LANE:
            return (0, row.catalog_target_index, row.session, row.step)
        return (1, head_positions[row.root_head], row.session, row.step)

    if rows != tuple(sorted(rows, key=canonical_key)):
        raise CurriculumSelectionError(
            "selection result rows are not in canonical curriculum order"
        )


@dataclass(frozen=True, slots=True)
class CurriculumSelection:
    """Selected rows and the canonical evidence that identifies them."""

    rows: tuple[CurriculumRow, ...]
    record_json: str

    def __post_init__(self) -> None:
        try:
            decoded = json.loads(self.record_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise CurriculumSelectionError(
                f"selection result has invalid record JSON: {exc}"
            ) from exc
        if type(decoded) is not dict:
            raise CurriculumSelectionError(
                "selection result record must be a JSON object"
            )
        if canonical_selection_json(decoded) != self.record_json:
            raise CurriculumSelectionError(
                "selection result record is not canonical JSON"
            )
        _bind_selection_rows(self.rows, decoded)

    @property
    def record(self) -> dict[str, object]:
        """Return a detached copy of the immutable canonical record."""

        decoded = json.loads(self.record_json)
        if type(decoded) is not dict:  # guarded by ``__post_init__``
            raise RuntimeError("selection record changed after validation")
        return decoded

    @property
    def examples(self) -> tuple[ProofExample, ...]:
        return tuple(row.example for row in self.rows)

    @property
    def sha256(self) -> str:
        value = self.record.get("selection_sha256")
        if type(value) is not str:
            raise RuntimeError("selection record has no digest")
        return value


def selection_record_sha256(record: Mapping[str, object]) -> str:
    """Recompute the self-excluding digest of a selection record."""

    if not isinstance(record, Mapping):
        raise CurriculumSelectionError("selection record must be a mapping")
    core = dict(record)
    claimed = core.pop("selection_sha256", None)
    if type(claimed) is not str or _SHA256_RE.fullmatch(claimed) is None:
        raise CurriculumSelectionError("selection record has no valid digest")
    return _sha256_json(core)


def canonical_selection_json(record: Mapping[str, object]) -> str:
    """Validate and serialize a selection record as canonical UTF-8 JSON."""

    claimed = record.get("selection_sha256")
    if selection_record_sha256(record) != claimed:
        raise CurriculumSelectionError("selection record digest mismatch")
    return _canonical_json_bytes(record).decode("utf-8") + "\n"


def select_curriculum(
    rows: Iterable[CurriculumRow],
    *,
    seed: str,
    synthetic_row_ceiling: int = MODEL_V3_SYNTHETIC_ROW_CEILING,
    contract: CurriculumSelectionContract = MODEL_V3_SELECTION_CONTRACT,
) -> CurriculumSelection:
    """Select one exact, balanced, whole-session model-v3 training view."""

    if not isinstance(contract, CurriculumSelectionContract):
        raise CurriculumSelectionError(
            "selection requires a CurriculumSelectionContract"
        )
    seed = _text("selection seed", seed)
    ceiling = _positive_integer(
        "synthetic_row_ceiling", synthetic_row_ceiling
    )
    population = tuple(rows)
    catalog_raw, synthetic_raw = _group_complete_sessions(
        population, contract=contract
    )
    catalog = _validate_catalog(catalog_raw, contract=contract)
    by_schema, by_head = _validate_synthetic(
        synthetic_raw, contract=contract
    )
    synthetic, balance_target, balanced_rounds = _select_synthetic_sessions(
        by_schema,
        by_head,
        contract=contract,
        seed=seed,
        row_ceiling=ceiling,
    )

    catalog_rows = tuple(row for session in catalog for row in session.rows)
    synthetic_rows = tuple(row for session in synthetic for row in session.rows)
    selected_rows = catalog_rows + synthetic_rows
    selected_ids = sorted(row.example.example_id for row in selected_rows)
    selected_row_evidence = sorted(
        (row.example.example_id, row.row_sha256) for row in selected_rows
    )
    candidate_row_evidence = sorted(
        (row.example.example_id, row.row_sha256) for row in population
    )

    head_counts: dict[str, dict[str, int]] = {}
    for head in contract.root_heads:
        head_sessions = tuple(
            session for session in synthetic if session.root_head == head
        )
        head_counts[head] = {
            "sessions": len(head_sessions),
            "rows": sum(session.row_count for session in head_sessions),
        }
    schema_counts: dict[str, dict[str, int]] = {}
    for schema, _ in contract.schema_heads:
        schema_sessions = tuple(
            session for session in synthetic if session.schema == schema
        )
        schema_counts[schema] = {
            "sessions": len(schema_sessions),
            "rows": sum(session.row_count for session in schema_sessions),
        }
    catalog_names = [str(session.catalog_target_name) for session in catalog]
    selected_schemas = sorted({str(session.schema) for session in synthetic})
    core: dict[str, object] = {
        "format": SELECTION_FORMAT,
        "v": SELECTION_VERSION,
        "algorithm": SELECTION_ALGORITHM,
        "seed": seed,
        "contract": {
            **contract.to_record(),
            "synthetic_row_ceiling": ceiling,
        },
        "source": {
            "rows": len(population),
            "sessions": len(catalog_raw) + len(synthetic_raw),
            "catalog_rows": sum(session.row_count for session in catalog_raw),
            "catalog_sessions": len(catalog_raw),
            "synthetic_rows": sum(
                session.row_count for session in synthetic_raw
            ),
            "synthetic_sessions": len(synthetic_raw),
            "rows_sha256": _sha256_json(candidate_row_evidence),
        },
        "selected": {
            "rows": len(selected_rows),
            "sessions": len(catalog) + len(synthetic),
            "example_ids_sha256": _sha256_json(selected_ids),
            "rows_sha256": _sha256_json(selected_row_evidence),
            "catalog": {
                "rows": len(catalog_rows),
                "sessions": len(catalog),
                "target_count": len(catalog),
                "target_index_range": [0, contract.library_size - 1],
                "target_names_sha256": _sha256_json(catalog_names),
            },
            "synthetic": {
                "rows": len(synthetic_rows),
                "row_ceiling": ceiling,
                "unused_row_capacity": ceiling - len(synthetic_rows),
                "sessions": len(synthetic),
                "schema_count": len(selected_schemas),
                "schema_names_sha256": _sha256_json(selected_schemas),
                "anchor_balance_sessions_per_head": balance_target,
                "balanced_fill_rounds": balanced_rounds,
                "root_head_session_imbalance": 0,
                "root_heads": head_counts,
                "schemas": schema_counts,
            },
        },
    }
    record = {**core, "selection_sha256": _sha256_json(core)}
    return CurriculumSelection(
        rows=selected_rows,
        record_json=canonical_selection_json(record),
    )


__all__ = [
    "CATALOG_LANE",
    "MODEL_V3_ROOT_HEADS",
    "MODEL_V3_SCHEMA_HEADS",
    "MODEL_V3_SELECTION_CONTRACT",
    "MODEL_V3_SYNTHETIC_ROW_CEILING",
    "SELECTION_ALGORITHM",
    "SELECTION_FORMAT",
    "SELECTION_VERSION",
    "SYNTHETIC_LANE",
    "CurriculumRow",
    "CurriculumSelection",
    "CurriculumSelectionContract",
    "CurriculumSelectionError",
    "canonical_selection_json",
    "row_from_validated_record",
    "select_curriculum",
    "selection_record_sha256",
]
