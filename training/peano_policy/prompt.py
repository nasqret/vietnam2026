"""Repository-owned prompt contract for Peano next-tactic policies.

The policy sees a canonical proof state plus the exact authority under which
its proposed tactic will run.  Version 1 remains the original state-only byte
contract.  Version 2 adds the complete-line grammar and a deterministic,
bounded projection of the permitted public theorem catalog.  Version 3 keeps
that grammar while binding a dependency-prefix authority, bounding each
displayed statement, and exposing a compact complete inventory of every
permitted theorem name. It also losslessly shares repeated exact context
chunks and targets across canonical one-line goals; raw proof states are never
shortened. Dataset compilation stores the rendered prompt
verbatim; training consumes that stored value after checking it against the
row's redundant state and capability fields.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import re
import unicodedata

from .library_identity import (
    LIBRARY_IDENTITY_FORMAT,
    LIBRARY_IDENTITY_VERSION,
)


PEANO_PROMPT_VERSION = 1
PEANO_PROMPT_V1 = 1
PEANO_PROMPT_V2 = 2
PEANO_PROMPT_V3 = 3
SUPPORTED_PROMPT_VERSIONS = (
    PEANO_PROMPT_V1,
    PEANO_PROMPT_V2,
    PEANO_PROMPT_V3,
)
TASK = "next_tactic"
ENVIRONMENT_BASE = "peano-lab-v1"
COMPLETION_SUFFIX = "</tactic>"
V2_RETRIEVAL_K = 8
V2_RETRIEVAL_METHOD = "weighted-token-ngram-v1"
V3_RETRIEVAL_K = 12
V3_RETRIEVAL_METHOD = "weighted-token-ngram-prefix-v1"
V3_STATEMENT_CHAR_LIMIT = 640
V3_NAME_INVENTORY_METHOD = "sorted-space-separated-utf8-v1"
V3_NAME_INVENTORY_MAX_PROMPT_CHARS = 5_600
V3_STATE_ENCODING_METHOD = "shared-declarations-v1"
V3_STATE_MAX_PROMPT_CHARS = 44_000
V2_TACTIC_GRAMMAR = (
    "Return exactly one complete line (never qed). "
    "tactic := primitive | (tactic) | tactic ; tactic | tactic <|> tactic | "
    "repeat tactic | first [tactic | ...] | all_goals tactic | "
    "focus POSITIVE tactic. primitive := intro [NAME] | "
    "have NAME : PROP | suffices NAME : PROP | apply NAME | exact NAME | "
    "assumption | split | left | right | cases NAME | exfalso | exists TERM | "
    "specialize NAME TERM | forall_elim NAME TERM | refl | symm | trans TERM | "
    "congr | rewrite [<-] NAME [at NAME] | induction NAME | "
    "simp [[<-] NAME,...] | norm_num | ring | "
    "compact_arith [[<-] NAME,...] | use THEOREM [as NAME]."
)
_CAPABILITY_FIELDS = ("label", "allowed_commands", "allowed_theorems")
_RESERVED_MARKERS = (
    "<task>",
    "</task>",
    "<env>",
    "</env>",
    "<state>",
    "</state>",
    "<grammar>",
    "</grammar>",
    "<library>",
    "</library>",
    "<tactic>",
    COMPLETION_SUFFIX,
)
_V1_ENVIRONMENT_RE = re.compile(
    r"peano-lab-v1;surface=([^;\n]+);"
    r"logic=(classical|intuitionistic);capability_sha256=([0-9a-f]{64})"
)
_V2_ENVIRONMENT_RE = re.compile(
    r"peano-lab-v1;surface=([^;\n]+);"
    r"logic=(classical|intuitionistic);capability_sha256=([0-9a-f]{64});"
    r"prompt=v2;contract_sha256=([0-9a-f]{64});"
    r"library_sha256=([0-9a-f]{64})"
)
_V3_ENVIRONMENT_RE = re.compile(
    r"peano-lab-v1;surface=([^;\n]+);"
    r"logic=(classical|intuitionistic);capability_sha256=([0-9a-f]{64});"
    r"prompt=v3;contract_sha256=([0-9a-f]{64});"
    r"library_sha256=([0-9a-f]{64});"
    r"library_full_sha256=([0-9a-f]{64});"
    r"library_prefix=([0-9]+);library_size=([0-9]+)"
)
_RETRIEVAL_TOKEN_RE = re.compile(
    r"[^\W_]+(?:'[^\W_]*)?|->|<=|[+*·~=∧∨∀∃¬→≤]",
    re.UNICODE,
)


class PromptError(ValueError):
    """A dataset prompt, completion, or inference prefix is malformed."""


def _safe_text(
    label: str,
    value: object,
    *,
    nonempty: bool = True,
    multiline: bool = False,
) -> str:
    if type(value) is not str or (nonempty and not value):
        raise PromptError(f"{label} must be {'non-empty ' if nonempty else ''}text")
    if not multiline and ("\n" in value or "\r" in value):
        raise PromptError(f"{label} must be one line")
    for character in value:
        category = unicodedata.category(character)
        if category in {"Cf", "Cs", "Zl", "Zp"}:
            raise PromptError(f"{label} contains an unsafe character")
        if category == "Cc" and not (multiline and character == "\n"):
            raise PromptError(f"{label} contains an unsafe control character")
    return value


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _name_tuple(label: str, value: object) -> tuple[str, ...] | None:
    if value is None:
        return None
    if type(value) is not list:
        raise PromptError(f"{label} must be null or an array")
    names = tuple(_safe_text(f"{label} entry", item) for item in value)
    if tuple(sorted(names)) != names:
        raise PromptError(f"{label} must be sorted")
    if len(set(names)) != len(names):
        raise PromptError(f"{label} contains duplicate names")
    return names


@dataclass(frozen=True, slots=True)
class CapabilityIdentity:
    """Canonical, hashable description of the model's surface authority."""

    label: str
    allowed_commands: tuple[str, ...] | None
    allowed_theorems: tuple[str, ...] | None

    def __post_init__(self) -> None:
        _safe_text("capability label", self.label)
        if ";" in self.label:
            raise PromptError("capability label must not contain ';'")
        for field in ("allowed_commands", "allowed_theorems"):
            value = getattr(self, field)
            if value is not None:
                if type(value) is not tuple:
                    raise PromptError(f"{field} must be a tuple or None")
                for item in value:
                    _safe_text(f"{field} entry", item)
                if tuple(sorted(value)) != value or len(set(value)) != len(value):
                    raise PromptError(f"{field} must be sorted and unique")

    @classmethod
    def from_record(cls, value: object) -> "CapabilityIdentity":
        if type(value) is not dict or tuple(value) != _CAPABILITY_FIELDS:
            raise PromptError(
                "capabilities must contain label, allowed_commands, and "
                "allowed_theorems in canonical order"
            )
        return cls(
            label=_safe_text("capability label", value["label"]),
            allowed_commands=_name_tuple(
                "allowed_commands", value["allowed_commands"]
            ),
            allowed_theorems=_name_tuple(
                "allowed_theorems", value["allowed_theorems"]
            ),
        )

    def to_record(self) -> dict[str, object]:
        return {
            "label": self.label,
            "allowed_commands": (
                None if self.allowed_commands is None else list(self.allowed_commands)
            ),
            "allowed_theorems": (
                None if self.allowed_theorems is None else list(self.allowed_theorems)
            ),
        }

    @property
    def sha256(self) -> str:
        payload = json.dumps(
            self.to_record(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class LibraryRecord:
    """One name/statement pair in a prompt-visible checked-library snapshot."""

    name: str
    statement: str

    def __post_init__(self) -> None:
        _safe_text("library theorem name", self.name)
        if any(character.isspace() for character in self.name):
            raise PromptError("library theorem name must be one token")
        _safe_text("library theorem statement", self.statement)

    @classmethod
    def from_record(cls, value: object) -> "LibraryRecord":
        if type(value) is not dict or tuple(value) != ("name", "statement"):
            raise PromptError(
                "library theorem must contain name then statement"
            )
        return cls(value["name"], value["statement"])

    def to_record(self) -> dict[str, str]:
        return {"name": self.name, "statement": self.statement}


def encode_v3_name_inventory(names: Sequence[str]) -> str:
    """Encode an exact model-v3 theorem allow-list compactly.

    The prompt library already requires theorem names to be whitespace-free,
    sorted, and unique.  A single ASCII space is therefore an unambiguous
    delimiter and avoids the per-name quotes/commas of a JSON array while
    leaving every legal ``use NAME`` spelling literally visible to the model.
    """

    canonical = tuple(names)
    for name in canonical:
        _safe_text("model-v3 name inventory entry", name)
        if any(character.isspace() for character in name):
            raise PromptError(
                "model-v3 name inventory entries must be one token"
            )
    if tuple(sorted(canonical)) != canonical:
        raise PromptError("model-v3 name inventory must be sorted")
    if len(set(canonical)) != len(canonical):
        raise PromptError("model-v3 name inventory contains duplicate names")
    return " ".join(canonical)


def v3_name_inventory_sha256(inventory: object) -> str:
    """Hash the exact inventory text under its versioned encoding method."""

    text = _safe_text(
        "model-v3 name inventory", inventory, nonempty=False
    )
    payload = (
        V3_NAME_INVENTORY_METHOD.encode("ascii")
        + b"\0"
        + text.encode("utf-8")
    )
    return hashlib.sha256(payload).hexdigest()


def library_snapshot_sha256(records: Sequence[LibraryRecord]) -> str:
    """Hash a complete, canonically ordered theorem snapshot."""

    canonical = tuple(records)
    if not all(type(record) is LibraryRecord for record in canonical):
        raise PromptError("library snapshot must contain LibraryRecord values")
    if tuple(sorted(record.name for record in canonical)) != tuple(
        record.name for record in canonical
    ) or len({record.name for record in canonical}) != len(canonical):
        raise PromptError("library snapshot must be sorted by unique theorem name")
    payload = json.dumps(
        [record.to_record() for record in canonical],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class PromptEnvironment:
    """Logic mode and exact capability preimage included in every prompt."""

    classical: bool
    capabilities: CapabilityIdentity
    prompt_version: int = PEANO_PROMPT_V1
    library: tuple[LibraryRecord, ...] = ()
    library_identity_sha256: str | None = None
    library_prefix_length: int | None = None
    library_full_length: int | None = None
    library_full_identity_sha256: str | None = None

    def __post_init__(self) -> None:
        if type(self.classical) is not bool:
            raise PromptError("classical must be a Boolean")
        if type(self.capabilities) is not CapabilityIdentity:
            raise PromptError("capabilities must be a CapabilityIdentity")
        if self.prompt_version not in SUPPORTED_PROMPT_VERSIONS:
            raise PromptError("prompt_version must be exactly 1, 2, or 3")
        if type(self.library) is not tuple or not all(
            type(record) is LibraryRecord for record in self.library
        ):
            raise PromptError("library must be a tuple of LibraryRecord values")
        if self.prompt_version == PEANO_PROMPT_V1:
            if (
                self.library
                or self.library_identity_sha256 is not None
                or self.library_prefix_length is not None
                or self.library_full_length is not None
                or self.library_full_identity_sha256 is not None
            ):
                raise PromptError("model-v1 environments have no library identity")
            return
        allowed = self.capabilities.allowed_theorems
        if allowed is None:
            raise PromptError("library prompts need a finite theorem allow-list")
        names = tuple(record.name for record in self.library)
        if names != allowed:
            raise PromptError(
                "prompt library names must exactly match allowed_theorems"
            )
        if (
            self.prompt_version == PEANO_PROMPT_V2
            and len(self.library) < V2_RETRIEVAL_K
        ):
            raise PromptError(
                f"model-v2 needs at least {V2_RETRIEVAL_K} library theorems"
            )
        # Validate ordering/uniqueness and make the snapshot hash total now.
        library_snapshot_sha256(self.library)
        identity = self.library_identity_sha256
        if (
            type(identity) is not str
            or re.fullmatch(r"[0-9a-f]{64}", identity) is None
        ):
            raise PromptError(
                "library prompts need a full 64-hex checked-library identity"
            )
        if self.prompt_version == PEANO_PROMPT_V2:
            if any(
                value is not None
                for value in (
                    self.library_prefix_length,
                    self.library_full_length,
                    self.library_full_identity_sha256,
                )
            ):
                raise PromptError("model-v2 has no dependency-prefix metadata")
            return
        if (
            type(self.library_prefix_length) is not int
            or self.library_prefix_length != len(self.library)
            or type(self.library_full_length) is not int
            or not 0 <= self.library_prefix_length <= self.library_full_length
            or type(self.library_full_identity_sha256) is not str
            or re.fullmatch(
                r"[0-9a-f]{64}", self.library_full_identity_sha256
            ) is None
        ):
            raise PromptError("model-v3 dependency-prefix metadata is malformed")

    @property
    def sha256(self) -> str:
        return self.capabilities.sha256

    @property
    def library_sha256(self) -> str | None:
        if self.prompt_version == PEANO_PROMPT_V1:
            return None
        # Stronger than the prompt-visible name/statement projection: this
        # also binds dependencies, source and script hashes, independently
        # checked certificates, and their node/depth metrics.
        return self.library_identity_sha256

    @property
    def library_statement_sha256(self) -> str | None:
        """Digest of the prompt-visible name/statement projection."""

        if self.prompt_version == PEANO_PROMPT_V1:
            return None
        return library_snapshot_sha256(self.library)

    @property
    def text(self) -> str:
        logic = "classical" if self.classical else "intuitionistic"
        base = (
            f"{ENVIRONMENT_BASE};surface={self.capabilities.label};logic={logic};"
            f"capability_sha256={self.sha256}"
        )
        if self.prompt_version == PEANO_PROMPT_V1:
            return base
        result = (
            f"{base};prompt=v{self.prompt_version};"
            f"contract_sha256={prompt_contract_sha256(self.prompt_version)};"
            f"library_sha256={self.library_sha256}"
        )
        if self.prompt_version == PEANO_PROMPT_V2:
            return result
        return (
            f"{result};library_full_sha256={self.library_full_identity_sha256};"
            f"library_prefix={self.library_prefix_length};"
            f"library_size={self.library_full_length}"
        )


@dataclass(frozen=True, slots=True)
class ParsedPrompt:
    """Information visible in a syntactically valid policy prefix."""

    environment: str
    surface: str
    classical: bool
    environment_sha256: str
    goals: tuple[str, ...]
    focus: int
    prompt_version: int = PEANO_PROMPT_V1
    state_encoding: str | None = None
    prompt_contract_sha256: str | None = None
    library_sha256: str | None = None
    library_full_sha256: str | None = None
    library_prefix_length: int | None = None
    library_size: int | None = None
    name_inventory_method: str | None = None
    name_inventory_count: int | None = None
    name_inventory_sha256: str | None = None
    allowed_theorem_names: tuple[str, ...] = ()
    retrieved_theorems: tuple[LibraryRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class ProofExample:
    """One replay-validated supervised next-tactic decision."""

    example_id: str
    prompt: str
    completion: str
    environment_sha256: str

    def __post_init__(self) -> None:
        _safe_text("example id", self.example_id)
        parsed = parse_prompt(self.prompt)
        if self.environment_sha256 != parsed.environment_sha256:
            raise PromptError(
                "example environment_sha256 does not match its stored prompt"
            )
        validate_completion(self.completion)

    @property
    def tactic(self) -> str:
        return validate_completion(self.completion)


def _validate_goals(goals: object) -> tuple[str, ...]:
    if type(goals) not in {list, tuple} or not goals:
        raise PromptError("state goals must be a non-empty array")
    result = tuple(
        _safe_text("goal", goal, multiline=True) for goal in goals
    )
    for goal in result:
        if any(marker in goal for marker in _RESERVED_MARKERS):
            raise PromptError("goal contains a reserved prompt marker")
    return result


def _canonical_goal_parts(goal: str) -> tuple[tuple[str, ...], str]:
    """Split one canonical trace goal without changing a byte of information."""

    if goal.startswith("⊢ ") and goal.count("⊢") == 1:
        context = ""
        target = goal[2:]
    elif goal.count("⊢") == 1 and goal.count(" ⊢ ") == 1:
        context, target = goal.split(" ⊢ ", 1)
    else:
        raise PromptError(
            "model-v3 state goals must use canonical 'declarations ⊢ target' text"
        )
    if not target or target != target.strip() or "\n" in target or "\r" in target:
        raise PromptError("model-v3 state target is not canonical one-line text")
    if context:
        if context != context.strip() or "\n" in context or "\r" in context:
            raise PromptError("model-v3 state context is not canonical one-line text")
        declarations = tuple(context.split(", "))
        if any(not declaration for declaration in declarations):
            raise PromptError("model-v3 state contains an empty declaration")
    else:
        declarations = ()
    reconstructed = (
        (f"{', '.join(declarations)} " if declarations else "")
        + f"⊢ {target}"
    )
    if reconstructed != goal:
        raise PromptError("model-v3 state goal is not canonical")
    return declarations, target


def encode_v3_state(
    goals: Sequence[str], focus: int
) -> dict[str, object]:
    """Losslessly deduplicate exact declarations and targets for prompt v3.

    Tables use deterministic first-occurrence order.  The declaration table
    contains exact canonical comma-delimited context chunks; it does not
    reinterpret their formulas. Goal records contain a vector of table
    indices and one target-table index. Parsing
    reconstructs the original canonical goal strings byte-for-byte; this is
    state encoding, not an abbreviated observation and not truncation.
    """

    canonical_goals = _validate_goals(goals)
    if type(focus) is not int or not 0 <= focus < len(canonical_goals):
        raise PromptError("focus must index the non-empty goal array")
    declarations: list[str] = []
    declaration_indices: dict[str, int] = {}
    targets: list[str] = []
    target_indices: dict[str, int] = {}
    encoded_goals: list[list[object]] = []
    for goal in canonical_goals:
        goal_declarations, target = _canonical_goal_parts(goal)
        context: list[int] = []
        for declaration in goal_declarations:
            if declaration not in declaration_indices:
                declaration_indices[declaration] = len(declarations)
                declarations.append(declaration)
            context.append(declaration_indices[declaration])
        if target not in target_indices:
            target_indices[target] = len(targets)
            targets.append(target)
        encoded_goals.append([context, target_indices[target]])
    return {
        "encoding": V3_STATE_ENCODING_METHOD,
        "focus": focus,
        "declarations": declarations,
        "targets": targets,
        "goals": encoded_goals,
    }


def _retrieval_tokens(value: str) -> tuple[str, ...]:
    tokens = tuple(
        "VAR" if len(token) == 1 and token.isalpha() and token.islower()
        else token.casefold()
        for token in _RETRIEVAL_TOKEN_RE.findall(value.replace("_", " "))
    )
    features = list(tokens)
    for width in (2, 3, 4):
        features.extend(
            f"{width}:" + "\x1f".join(tokens[index : index + width])
            for index in range(len(tokens) - width + 1)
        )
    return tuple(features)


def retrieve_theorems(
    *,
    goals: Sequence[str],
    focus: int,
    environment: PromptEnvironment,
    k: int | None = None,
) -> tuple[LibraryRecord, ...]:
    """Select a deterministic bounded projection of a checked library.

    Scoring is deliberately small and inspectable: focused-goal tokens count
    twice and rare library tokens count more than ubiquitous syntax.  Version
    2 retains its historical statement-only scoring byte-for-byte.  Version 3
    also scores theorem-name tokens, as its manifest says.  Lexical theorem
    name is the complete tie-breaker, so no hash/random iteration order can
    leak in.
    """

    canonical_goals = _validate_goals(goals)
    if type(focus) is not int or not 0 <= focus < len(canonical_goals):
        raise PromptError("focus must index the non-empty goal array")
    if type(environment) is not PromptEnvironment:
        raise PromptError("environment must be a PromptEnvironment")
    if environment.prompt_version not in {PEANO_PROMPT_V2, PEANO_PROMPT_V3}:
        raise PromptError("theorem retrieval needs a library prompt")
    maximum = (
        V2_RETRIEVAL_K
        if environment.prompt_version == PEANO_PROMPT_V2
        else V3_RETRIEVAL_K
    )
    if k is None:
        k = maximum
    if type(k) is not int or k < 1 or k > maximum:
        raise PromptError(f"retrieval k must lie between 1 and {maximum}")

    query = frozenset(
        token
        for goal in canonical_goals
        for token in _retrieval_tokens(goal)
    )
    focused_query = frozenset(_retrieval_tokens(canonical_goals[focus]))
    record_tokens = {
        record.name: frozenset(
            _retrieval_tokens(record.statement)
            if environment.prompt_version == PEANO_PROMPT_V2
            else (
                *_retrieval_tokens(record.name),
                *_retrieval_tokens(record.statement),
            )
        )
        for record in environment.library
    }
    document_frequency = {
        token: sum(token in tokens for tokens in record_tokens.values())
        for token in set().union(*record_tokens.values())
    }
    document_count = len(environment.library)

    def weighted_jaccard(
        left: frozenset[str], right: frozenset[str]
    ) -> Fraction:
        union = left | right
        if not union:
            return Fraction(0)
        intersection_weight = sum(
            document_count + 1 - document_frequency.get(token, 0)
            for token in left & right
        )
        union_weight = sum(
            document_count + 1 - document_frequency.get(token, 0)
            for token in union
        )
        return Fraction(intersection_weight, union_weight)

    def score(record: LibraryRecord) -> Fraction:
        tokens = record_tokens[record.name]
        return (
            2 * weighted_jaccard(focused_query, tokens)
            + weighted_jaccard(query, tokens)
        )

    ranked = sorted(
        environment.library,
        key=lambda record: (-score(record), record.name),
    )
    return tuple(ranked[: min(k, len(ranked))])


def _v3_display_record(record: LibraryRecord) -> LibraryRecord:
    """Return a deterministic bounded display projection of one theorem.

    Retrieval still scores the complete canonical proposition.  Only the text
    sent to the language model is abbreviated, and the embedded digest makes
    that abbreviation content-addressed rather than ambiguous.
    """

    statement = record.statement
    if len(statement) <= V3_STATEMENT_CHAR_LIMIT:
        return record
    digest = hashlib.sha256(statement.encode("utf-8")).hexdigest()[:16]
    marker = f" … [statement_sha256={digest}] … "
    suffix_length = 96
    prefix_length = V3_STATEMENT_CHAR_LIMIT - len(marker) - suffix_length
    return LibraryRecord(
        record.name,
        statement[:prefix_length] + marker + statement[-suffix_length:],
    )


def render_prompt(
    *,
    goals: Sequence[str],
    focus: int,
    environment: PromptEnvironment,
) -> str:
    """Render the exact prefix shared by dataset compilation and inference."""

    canonical_goals = _validate_goals(goals)
    if type(focus) is not int or not 0 <= focus < len(canonical_goals):
        raise PromptError("focus must index the non-empty goal array")
    if type(environment) is not PromptEnvironment:
        raise PromptError("environment must be a PromptEnvironment")
    prefix = (
        f"<task>{TASK}</task>\n"
        f"<env>{environment.text}</env>\n"
    )
    if environment.prompt_version == PEANO_PROMPT_V1:
        state = json.dumps(
            {"focus": focus, "goals": list(canonical_goals)},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return prefix + f"<state>{state}</state>\n<tactic>"
    retrieved = retrieve_theorems(
        goals=canonical_goals,
        focus=focus,
        environment=environment,
    )
    if environment.prompt_version == PEANO_PROMPT_V2:
        library_record = {
            "k": V2_RETRIEVAL_K,
            "method": V2_RETRIEVAL_METHOD,
            "records": [record.to_record() for record in retrieved],
            "snapshot_sha256": environment.library_sha256,
        }
    else:
        names = tuple(record.name for record in environment.library)
        name_inventory = encode_v3_name_inventory(names)
        name_inventory_record = {
            "method": V3_NAME_INVENTORY_METHOD,
            "count": len(names),
            "sha256": v3_name_inventory_sha256(name_inventory),
            "names": name_inventory,
        }
        inventory_prompt_chars = len(
            json.dumps(
                {"name_inventory": name_inventory_record},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ) - 1
        if inventory_prompt_chars > V3_NAME_INVENTORY_MAX_PROMPT_CHARS:
            raise PromptError("model-v3 name inventory exceeds its prompt bound")
        library_record = {
            "k": V3_RETRIEVAL_K,
            "method": V3_RETRIEVAL_METHOD,
            "library_prefix": environment.library_prefix_length,
            "library_size": environment.library_full_length,
            "library_full_sha256": environment.library_full_identity_sha256,
            "statement_char_limit": V3_STATEMENT_CHAR_LIMIT,
            "name_inventory": name_inventory_record,
            "records": [
                _v3_display_record(record).to_record() for record in retrieved
            ],
            "snapshot_sha256": environment.library_sha256,
        }
    library = json.dumps(
        library_record,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    state_record = (
        encode_v3_state(canonical_goals, focus)
        if environment.prompt_version == PEANO_PROMPT_V3
        else {"focus": focus, "goals": list(canonical_goals)}
    )
    state = json.dumps(
        state_record,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    if (
        environment.prompt_version == PEANO_PROMPT_V3
        and len(state) > V3_STATE_MAX_PROMPT_CHARS
    ):
        raise PromptError(
            "model-v3 lossless state encoding exceeds its "
            f"{V3_STATE_MAX_PROMPT_CHARS}-character prompt bound"
        )
    return (
        prefix
        + f"<grammar>{V2_TACTIC_GRAMMAR}</grammar>\n"
        + f"<library>{library}</library>\n"
        + f"<state>{state}</state>\n<tactic>"
    )


def prompt_manifest_record(
    version: int = PEANO_PROMPT_VERSION,
) -> dict[str, object]:
    """Return the dataset manifest declaration for this exact contract."""

    if version not in SUPPORTED_PROMPT_VERSIONS:
        raise PromptError("prompt manifest version must be exactly 1, 2, or 3")
    common: dict[str, object] = {
        "task": TASK,
        "environment_base": ENVIRONMENT_BASE,
        "completion_suffix": COMPLETION_SUFFIX,
        "binder_policy": "exact-authored-binders-v1",
        "binder_policy_detail": (
            "preserve exact visible state names and exact successful tactic "
            "lines so every emitted transition is executable"
        ),
    }
    if version == PEANO_PROMPT_V1:
        return {
            "task": common["task"],
            "environment_base": common["environment_base"],
            "environment_template": (
                "peano-lab-v1;surface=LABEL;logic=MODE;capability_sha256=SHA256"
            ),
            "template": (
                "<task>...</task>\\n<env>...</env>\\n"
                "<state>...</state>\\n<tactic>"
            ),
            "completion_suffix": common["completion_suffix"],
            "binder_policy": common["binder_policy"],
            "binder_policy_detail": common["binder_policy_detail"],
        }
    if version == PEANO_PROMPT_V2:
        return {
        "task": common["task"],
        "environment_base": common["environment_base"],
        "environment_template": (
            "peano-lab-v1;surface=LABEL;logic=MODE;capability_sha256=SHA256;"
            "prompt=v2;contract_sha256=SHA256;library_sha256=SHA256"
        ),
        "template": (
            "<task>...</task>\\n<env>...</env>\\n<grammar>...</grammar>\\n"
            "<library>...</library>\\n<state>...</state>\\n<tactic>"
        ),
        "completion_suffix": common["completion_suffix"],
        "binder_policy": common["binder_policy"],
        "binder_policy_detail": common["binder_policy_detail"],
        "grammar": V2_TACTIC_GRAMMAR,
        "retrieval": {
            "k": V2_RETRIEVAL_K,
            "method": V2_RETRIEVAL_METHOD,
            "source": (
                "deterministic projection of the exact checked-library identity"
            ),
            "tie_breaker": "lexical theorem name",
        },
        "library_identity": {
            "format": LIBRARY_IDENTITY_FORMAT,
            "version": LIBRARY_IDENTITY_VERSION,
            "theorem_fields": [
                "name",
                "statement",
                "dependencies",
                "source_spec_sha256",
                "script_sha256",
                "certificate_sha256",
                "proof_nodes",
                "proof_depth",
            ],
            "prompt_projection": "retrieved name and canonical statement only",
        },
        }
    return {
        "task": common["task"],
        "environment_base": common["environment_base"],
        "environment_template": (
            "peano-lab-v1;surface=LABEL;logic=MODE;capability_sha256=SHA256;"
            "prompt=v3;contract_sha256=SHA256;library_sha256=PREFIX_SHA256;"
            "library_full_sha256=FULL_SHA256;library_prefix=COUNT;"
            "library_size=COUNT"
        ),
        "template": (
            "<task>...</task>\\n<env>...</env>\\n<grammar>...</grammar>\\n"
            "<library>...</library>\\n<state>...</state>\\n<tactic>"
        ),
        "completion_suffix": common["completion_suffix"],
        "binder_policy": common["binder_policy"],
        "binder_policy_detail": common["binder_policy_detail"],
        "grammar": V2_TACTIC_GRAMMAR,
        "authority": "strict dependency prefix; current target unavailable",
        "retrieval": {
            "k": V3_RETRIEVAL_K,
            "method": V3_RETRIEVAL_METHOD,
            "source": "deterministic projection of the exact checked prefix",
            "statement_char_limit": V3_STATEMENT_CHAR_LIMIT,
            "record_features": "theorem name plus full canonical statement",
            "tie_breaker": "lexical theorem name",
        },
        "name_inventory": {
            "method": V3_NAME_INVENTORY_METHOD,
            "coverage": "complete exact allowed_theorems prefix",
            "count": "exact library_prefix value",
            "digest": (
                "sha256(method ASCII + NUL + exact UTF-8 inventory text)"
            ),
            "purpose": (
                "make every permitted use THEOREM spelling prompt-visible"
            ),
            "prompt_cost_metric": (
                "additional Unicode characters in compact library JSON"
            ),
            "prompt_cost_max_chars": V3_NAME_INVENTORY_MAX_PROMPT_CHARS,
        },
        "state_encoding": V3_STATE_ENCODING_METHOD,
        "state_encoding_detail": {
            "scope": "prompt v3 only",
            "loss": "none; reconstruct exact canonical goal strings",
            "table_order": "deterministic first occurrence",
            "declarations": (
                "exact comma-delimited context chunks shared across goals"
            ),
            "targets": "exact target strings shared across goals",
            "goal_record": "[declaration index vector, target index]",
            "index_type": "strict non-negative JSON integer",
            "canonicality": (
                "no duplicate or unused table entries; byte-exact reconstruction"
            ),
            "prompt_cost_metric": "Unicode characters in compact state JSON",
            "prompt_cost_max_chars": V3_STATE_MAX_PROMPT_CHARS,
            "overflow_policy": "fail closed; never truncate or abbreviate",
        },
        "library_identity": {
            "format": "peano-model-v3-library-identity",
            "version": 1,
            "theorem_fields": [
                "name",
                "statement",
                "dependencies",
                "source_spec_sha256",
                "script_sha256",
                "certificate_sha256",
                "proof_nodes",
                "proof_depth",
            ],
            "prompt_projection": (
                "complete allowed-name inventory plus retrieved name and "
                "bounded canonical-statement excerpt"
            ),
        },
    }


def prompt_contract_sha256(version: int) -> str:
    payload = json.dumps(
        prompt_manifest_record(version),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def prompt_version_from_manifest(value: object) -> int:
    """Recognize exactly one repository-owned prompt manifest record."""

    for version in SUPPORTED_PROMPT_VERSIONS:
        if value == prompt_manifest_record(version):
            return version
    raise PromptError("prompt contract is not an exact supported Peano contract")


def _parse_state(
    state_text: str, *, prompt_version: int
) -> tuple[tuple[str, ...], int, str | None]:
    try:
        state = json.loads(
            state_text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise PromptError(f"prompt state is invalid JSON: {exc}") from exc
    if type(state) is not dict:
        raise PromptError("prompt state must be an object")
    if prompt_version != PEANO_PROMPT_V3:
        if tuple(state) != ("focus", "goals"):
            raise PromptError("prompt state must contain focus then goals")
        goals = _validate_goals(state["goals"])
        focus = state["focus"]
        if type(focus) is not int or not 0 <= focus < len(goals):
            raise PromptError("prompt focus does not index its goals")
        return goals, focus, None

    if len(state_text) > V3_STATE_MAX_PROMPT_CHARS:
        raise PromptError("model-v3 prompt state exceeds its character bound")
    if json.dumps(
        state,
        ensure_ascii=False,
        separators=(",", ":"),
    ) != state_text:
        raise PromptError("model-v3 prompt state JSON is not compact canonical text")

    expected_fields = (
        "encoding",
        "focus",
        "declarations",
        "targets",
        "goals",
    )
    if tuple(state) != expected_fields or state.get("encoding") != (
        V3_STATE_ENCODING_METHOD
    ):
        raise PromptError("model-v3 prompt state encoding is not canonical")
    focus = state["focus"]
    declarations_value = state["declarations"]
    targets_value = state["targets"]
    encoded_goals = state["goals"]
    if (
        type(focus) is not int
        or type(declarations_value) is not list
        or type(targets_value) is not list
        or type(encoded_goals) is not list
        or not encoded_goals
    ):
        raise PromptError("model-v3 prompt state tables are malformed")
    declarations = tuple(
        _safe_text("model-v3 declaration table entry", declaration)
        for declaration in declarations_value
    )
    targets = tuple(
        _safe_text("model-v3 target table entry", target)
        for target in targets_value
    )
    if len(set(declarations)) != len(declarations) or len(set(targets)) != len(
        targets
    ):
        raise PromptError("model-v3 prompt state tables contain duplicates")
    reconstructed: list[str] = []
    for goal_index, goal_record in enumerate(encoded_goals, 1):
        if (
            type(goal_record) is not list
            or len(goal_record) != 2
            or type(goal_record[0]) is not list
            or type(goal_record[1]) is not int
        ):
            raise PromptError(
                f"model-v3 prompt goal record {goal_index} is malformed"
            )
        context_indices = goal_record[0]
        target_index = goal_record[1]
        if (
            not 0 <= target_index < len(targets)
            or any(
                type(index) is not int or not 0 <= index < len(declarations)
                for index in context_indices
            )
        ):
            raise PromptError(
                f"model-v3 prompt goal record {goal_index} has an invalid index"
            )
        context = tuple(declarations[index] for index in context_indices)
        prefix = f"{', '.join(context)} " if context else ""
        reconstructed.append(f"{prefix}⊢ {targets[target_index]}")
    goals = _validate_goals(reconstructed)
    if not 0 <= focus < len(goals):
        raise PromptError("prompt focus does not index its goals")
    # Re-encoding enforces first-use table order, no unused entries, strict
    # integer indices (including rejection of bool), and exact reconstruction.
    if encode_v3_state(goals, focus) != state:
        raise PromptError("model-v3 prompt state encoding is non-canonical")
    return goals, focus, V3_STATE_ENCODING_METHOD


def parse_prompt(value: object) -> ParsedPrompt:
    """Validate a stored/inference prefix and expose its visible fields."""

    prompt = _safe_text("prompt", value, multiline=True)
    prefix = f"<task>{TASK}</task>\n<env>"
    if not prompt.startswith(prefix) or not prompt.endswith("</state>\n<tactic>"):
        raise PromptError("prompt does not match the Peano next-tactic template")
    environment_marker = "</env>\n"
    middle = prompt[len(prefix) :]
    if middle.count(environment_marker) != 1:
        raise PromptError("prompt has a malformed environment/state boundary")
    environment_text, body = middle.split(environment_marker)

    v1_match = _V1_ENVIRONMENT_RE.fullmatch(environment_text)
    if v1_match is not None:
        state_prefix = "<state>"
        state_suffix = "</state>\n<tactic>"
        if not body.startswith(state_prefix) or not body.endswith(state_suffix):
            raise PromptError("model-v1 prompt has a malformed state boundary")
        surface, logic, environment_sha256 = v1_match.groups()
        goals, focus, state_encoding = _parse_state(
            body[len(state_prefix) : -len(state_suffix)],
            prompt_version=PEANO_PROMPT_V1,
        )
        return ParsedPrompt(
            environment=environment_text,
            surface=_safe_text("surface", surface),
            classical=logic == "classical",
            environment_sha256=environment_sha256,
            goals=goals,
            focus=focus,
            state_encoding=state_encoding,
        )

    library_match = _V2_ENVIRONMENT_RE.fullmatch(environment_text)
    prompt_version = PEANO_PROMPT_V2
    full_snapshot_sha256: str | None = None
    prefix_length: int | None = None
    library_size: int | None = None
    if library_match is None:
        library_match = _V3_ENVIRONMENT_RE.fullmatch(environment_text)
        prompt_version = PEANO_PROMPT_V3
    if library_match is None:
        raise PromptError("prompt has a malformed environment identity")
    groups = library_match.groups()
    surface, logic, environment_sha256, contract_sha256, snapshot_sha256 = groups[:5]
    if prompt_version == PEANO_PROMPT_V3:
        full_snapshot_sha256 = groups[5]
        prefix_length = int(groups[6])
        library_size = int(groups[7])
        if not 0 <= prefix_length <= library_size:
            raise PromptError("model-v3 prompt has an invalid library prefix")
    if contract_sha256 != prompt_contract_sha256(prompt_version):
        raise PromptError(
            f"model-v{prompt_version} prompt contract hash is stale or forged"
        )
    grammar_prefix = "<grammar>"
    grammar_marker = "</grammar>\n<library>"
    library_marker = "</library>\n<state>"
    state_suffix = "</state>\n<tactic>"
    if (
        not body.startswith(grammar_prefix)
        or body.count(grammar_marker) != 1
        or body.count(library_marker) != 1
        or not body.endswith(state_suffix)
    ):
        raise PromptError(
            f"model-v{prompt_version} prompt has malformed "
            "grammar/library/state boundaries"
        )
    grammar_and_rest = body[len(grammar_prefix) :]
    grammar, library_and_state = grammar_and_rest.split(grammar_marker)
    if grammar != V2_TACTIC_GRAMMAR:
        raise PromptError(
            f"model-v{prompt_version} tactic grammar differs from the contract"
        )
    library_text, state_text = library_and_state.split(library_marker)
    state_text = state_text[: -len(state_suffix)]
    try:
        library_value = json.loads(
            library_text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise PromptError(f"prompt library is invalid JSON: {exc}") from exc
    if type(library_value) is not dict:
        raise PromptError("prompt library has non-canonical fields")
    if prompt_version == PEANO_PROMPT_V2:
        expected_fields = ("k", "method", "records", "snapshot_sha256")
        metadata_valid = (
            library_value.get("k") == V2_RETRIEVAL_K
            and library_value.get("method") == V2_RETRIEVAL_METHOD
            and type(library_value.get("records")) is list
            and len(library_value["records"]) == V2_RETRIEVAL_K
        )
    else:
        expected_fields = (
            "k",
            "method",
            "library_prefix",
            "library_size",
            "library_full_sha256",
            "statement_char_limit",
            "name_inventory",
            "records",
            "snapshot_sha256",
        )
        name_inventory = library_value.get("name_inventory")
        metadata_valid = (
            library_value.get("k") == V3_RETRIEVAL_K
            and library_value.get("method") == V3_RETRIEVAL_METHOD
            and library_value.get("library_prefix") == prefix_length
            and library_value.get("library_size") == library_size
            and library_value.get("library_full_sha256") == full_snapshot_sha256
            and library_value.get("statement_char_limit")
            == V3_STATEMENT_CHAR_LIMIT
            and type(name_inventory) is dict
            and tuple(name_inventory)
            == ("method", "count", "sha256", "names")
            and type(library_value.get("records")) is list
            and len(library_value["records"])
            == min(V3_RETRIEVAL_K, prefix_length or 0)
        )
    if (
        tuple(library_value) != expected_fields
        or library_value.get("snapshot_sha256") != snapshot_sha256
        or not metadata_valid
    ):
        raise PromptError("prompt library retrieval metadata is invalid")
    retrieved = tuple(
        LibraryRecord.from_record(record) for record in library_value["records"]
    )
    if len({record.name for record in retrieved}) != len(retrieved):
        raise PromptError("prompt library contains duplicate theorem names")
    allowed_theorem_names: tuple[str, ...] = ()
    name_inventory_method: str | None = None
    name_inventory_count: int | None = None
    name_inventory_digest: str | None = None
    if prompt_version == PEANO_PROMPT_V3:
        name_inventory = library_value["name_inventory"]
        assert type(name_inventory) is dict
        name_inventory_method = name_inventory.get("method")
        name_inventory_count = name_inventory.get("count")
        name_inventory_digest = name_inventory.get("sha256")
        inventory_text = name_inventory.get("names")
        if (
            name_inventory_method != V3_NAME_INVENTORY_METHOD
            or type(name_inventory_count) is not int
            or name_inventory_count != prefix_length
            or type(name_inventory_digest) is not str
            or re.fullmatch(r"[0-9a-f]{64}", name_inventory_digest) is None
            or type(inventory_text) is not str
        ):
            raise PromptError("prompt name inventory metadata is invalid")
        allowed_theorem_names = (
            () if inventory_text == "" else tuple(inventory_text.split(" "))
        )
        try:
            canonical_inventory = encode_v3_name_inventory(
                allowed_theorem_names
            )
        except PromptError as exc:
            raise PromptError("prompt name inventory is malformed") from exc
        if (
            canonical_inventory != inventory_text
            or len(allowed_theorem_names) != name_inventory_count
            or v3_name_inventory_sha256(inventory_text)
            != name_inventory_digest
            or not set(record.name for record in retrieved).issubset(
                allowed_theorem_names
            )
        ):
            raise PromptError("prompt name inventory is forged or inconsistent")
    goals, focus, state_encoding = _parse_state(
        state_text, prompt_version=prompt_version
    )
    return ParsedPrompt(
        environment=environment_text,
        surface=_safe_text("surface", surface),
        classical=logic == "classical",
        environment_sha256=environment_sha256,
        goals=goals,
        focus=focus,
        prompt_version=prompt_version,
        state_encoding=state_encoding,
        prompt_contract_sha256=contract_sha256,
        library_sha256=snapshot_sha256,
        library_full_sha256=full_snapshot_sha256,
        library_prefix_length=prefix_length,
        library_size=library_size,
        name_inventory_method=name_inventory_method,
        name_inventory_count=name_inventory_count,
        name_inventory_sha256=name_inventory_digest,
        allowed_theorem_names=allowed_theorem_names,
        retrieved_theorems=retrieved,
    )


def validate_tactic_line(value: object) -> str:
    """Return one canonical model action or reject anything else."""

    tactic = _safe_text("tactic", value)
    if tactic != tactic.strip():
        raise PromptError("tactic must not have leading or trailing whitespace")
    if len(tactic) > 4_000:
        raise PromptError("tactic exceeds the Peano Lab command limit")
    if any(marker in tactic for marker in _RESERVED_MARKERS):
        raise PromptError("tactic contains a reserved prompt marker")
    return tactic


def validate_completion(value: object) -> str:
    """Validate ``TACTIC</tactic>`` and return its one tactic line."""

    completion = _safe_text("completion", value)
    if not completion.endswith(COMPLETION_SUFFIX):
        raise PromptError(f"completion must end with {COMPLETION_SUFFIX}")
    tactic = completion[: -len(COMPLETION_SUFFIX)]
    return validate_tactic_line(tactic)


def extract_one_tactic(generated_text: object) -> str:
    """Validate the bare tactic line decoded before EOS."""

    return validate_tactic_line(generated_text)


__all__ = [
    "COMPLETION_SUFFIX",
    "CapabilityIdentity",
    "ENVIRONMENT_BASE",
    "PEANO_PROMPT_VERSION",
    "PEANO_PROMPT_V1",
    "PEANO_PROMPT_V2",
    "PEANO_PROMPT_V3",
    "SUPPORTED_PROMPT_VERSIONS",
    "LibraryRecord",
    "ParsedPrompt",
    "PromptEnvironment",
    "PromptError",
    "ProofExample",
    "TASK",
    "V2_RETRIEVAL_K",
    "V2_RETRIEVAL_METHOD",
    "V2_TACTIC_GRAMMAR",
    "V3_RETRIEVAL_K",
    "V3_RETRIEVAL_METHOD",
    "V3_NAME_INVENTORY_METHOD",
    "V3_NAME_INVENTORY_MAX_PROMPT_CHARS",
    "V3_STATE_ENCODING_METHOD",
    "V3_STATE_MAX_PROMPT_CHARS",
    "V3_STATEMENT_CHAR_LIMIT",
    "encode_v3_state",
    "encode_v3_name_inventory",
    "extract_one_tactic",
    "library_snapshot_sha256",
    "parse_prompt",
    "prompt_contract_sha256",
    "prompt_manifest_record",
    "prompt_version_from_manifest",
    "retrieve_theorems",
    "render_prompt",
    "v3_name_inventory_sha256",
    "validate_completion",
    "validate_tactic_line",
]
