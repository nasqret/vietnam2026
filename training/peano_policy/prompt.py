"""Repository-owned prompt contract for Peano next-tactic policies.

The policy sees a canonical proof state plus the exact authority under which
its proposed tactic will run.  Version 1 remains the original state-only byte
contract.  Version 2 adds the complete-line grammar and a deterministic,
bounded projection of the permitted public theorem catalog.  Dataset
compilation stores the rendered prompt verbatim; training consumes that stored
value after checking it against the row's redundant state and capability
fields.
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
SUPPORTED_PROMPT_VERSIONS = (PEANO_PROMPT_V1, PEANO_PROMPT_V2)
TASK = "next_tactic"
ENVIRONMENT_BASE = "peano-lab-v1"
COMPLETION_SUFFIX = "</tactic>"
V2_RETRIEVAL_K = 8
V2_RETRIEVAL_METHOD = "weighted-token-ngram-v1"
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

    def __post_init__(self) -> None:
        if type(self.classical) is not bool:
            raise PromptError("classical must be a Boolean")
        if type(self.capabilities) is not CapabilityIdentity:
            raise PromptError("capabilities must be a CapabilityIdentity")
        if self.prompt_version not in SUPPORTED_PROMPT_VERSIONS:
            raise PromptError("prompt_version must be exactly 1 or 2")
        if type(self.library) is not tuple or not all(
            type(record) is LibraryRecord for record in self.library
        ):
            raise PromptError("library must be a tuple of LibraryRecord values")
        if self.prompt_version == PEANO_PROMPT_V1:
            if self.library or self.library_identity_sha256 is not None:
                raise PromptError("model-v1 environments have no library identity")
            return
        allowed = self.capabilities.allowed_theorems
        if allowed is None:
            raise PromptError("model-v2 needs a finite theorem allow-list")
        names = tuple(record.name for record in self.library)
        if names != allowed:
            raise PromptError(
                "model-v2 library names must exactly match allowed_theorems"
            )
        if len(self.library) < V2_RETRIEVAL_K:
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
                "model-v2 needs the full 64-hex checked-library identity"
            )

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
        return (
            f"{base};prompt=v2;"
            f"contract_sha256={prompt_contract_sha256(PEANO_PROMPT_V2)};"
            f"library_sha256={self.library_sha256}"
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
    prompt_contract_sha256: str | None = None
    library_sha256: str | None = None
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
    k: int = V2_RETRIEVAL_K,
) -> tuple[LibraryRecord, ...]:
    """Select a deterministic bounded projection of a v2 library snapshot.

    Scoring is deliberately small and inspectable: focused-goal tokens count
    twice, rare library tokens count more than ubiquitous syntax, and theorem
    name tokens participate alongside statement tokens.  Lexical theorem name
    is the complete tie-breaker, so no hash/random iteration order can leak in.
    """

    canonical_goals = _validate_goals(goals)
    if type(focus) is not int or not 0 <= focus < len(canonical_goals):
        raise PromptError("focus must index the non-empty goal array")
    if type(environment) is not PromptEnvironment:
        raise PromptError("environment must be a PromptEnvironment")
    if environment.prompt_version != PEANO_PROMPT_V2:
        raise PromptError("theorem retrieval is available only in model-v2 prompts")
    if type(k) is not int or k < 1 or k > V2_RETRIEVAL_K:
        raise PromptError(f"retrieval k must lie between 1 and {V2_RETRIEVAL_K}")

    query = frozenset(
        token
        for goal in canonical_goals
        for token in _retrieval_tokens(goal)
    )
    focused_query = frozenset(_retrieval_tokens(canonical_goals[focus]))
    record_tokens = {
        record.name: frozenset(_retrieval_tokens(record.statement))
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

    ranked = sorted(environment.library, key=lambda record: (-score(record), record.name))
    return tuple(ranked[: min(k, len(ranked))])


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
    state = json.dumps(
        {"focus": focus, "goals": list(canonical_goals)},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    prefix = (
        f"<task>{TASK}</task>\n"
        f"<env>{environment.text}</env>\n"
    )
    if environment.prompt_version == PEANO_PROMPT_V1:
        return prefix + f"<state>{state}</state>\n<tactic>"
    retrieved = retrieve_theorems(
        goals=canonical_goals,
        focus=focus,
        environment=environment,
    )
    library = json.dumps(
        {
            "k": V2_RETRIEVAL_K,
            "method": V2_RETRIEVAL_METHOD,
            "records": [record.to_record() for record in retrieved],
            "snapshot_sha256": environment.library_sha256,
        },
        ensure_ascii=False,
        separators=(",", ":"),
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
        raise PromptError("prompt manifest version must be exactly 1 or 2")
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
    raise PromptError("prompt contract is neither exact model-v1 nor model-v2")


def _parse_state(state_text: str) -> tuple[tuple[str, ...], int]:
    try:
        state = json.loads(
            state_text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise PromptError(f"prompt state is invalid JSON: {exc}") from exc
    if type(state) is not dict or tuple(state) != ("focus", "goals"):
        raise PromptError("prompt state must contain focus then goals")
    goals = _validate_goals(state["goals"])
    focus = state["focus"]
    if type(focus) is not int or not 0 <= focus < len(goals):
        raise PromptError("prompt focus does not index its goals")
    return goals, focus


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
        goals, focus = _parse_state(body[len(state_prefix) : -len(state_suffix)])
        return ParsedPrompt(
            environment=environment_text,
            surface=_safe_text("surface", surface),
            classical=logic == "classical",
            environment_sha256=environment_sha256,
            goals=goals,
            focus=focus,
        )

    v2_match = _V2_ENVIRONMENT_RE.fullmatch(environment_text)
    if v2_match is None:
        raise PromptError("prompt has a malformed environment identity")
    surface, logic, environment_sha256, contract_sha256, snapshot_sha256 = (
        v2_match.groups()
    )
    if contract_sha256 != prompt_contract_sha256(PEANO_PROMPT_V2):
        raise PromptError("model-v2 prompt contract hash is stale or forged")
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
        raise PromptError("model-v2 prompt has malformed grammar/library/state boundaries")
    grammar_and_rest = body[len(grammar_prefix) :]
    grammar, library_and_state = grammar_and_rest.split(grammar_marker)
    if grammar != V2_TACTIC_GRAMMAR:
        raise PromptError("model-v2 tactic grammar differs from the contract")
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
    if type(library_value) is not dict or tuple(library_value) != (
        "k",
        "method",
        "records",
        "snapshot_sha256",
    ):
        raise PromptError("prompt library has non-canonical fields")
    if (
        library_value["k"] != V2_RETRIEVAL_K
        or library_value["method"] != V2_RETRIEVAL_METHOD
        or library_value["snapshot_sha256"] != snapshot_sha256
        or type(library_value["records"]) is not list
        or len(library_value["records"]) != V2_RETRIEVAL_K
    ):
        raise PromptError("prompt library retrieval metadata is invalid")
    retrieved = tuple(
        LibraryRecord.from_record(record) for record in library_value["records"]
    )
    if len({record.name for record in retrieved}) != len(retrieved):
        raise PromptError("prompt library contains duplicate theorem names")
    goals, focus = _parse_state(state_text)
    return ParsedPrompt(
        environment=environment_text,
        surface=_safe_text("surface", surface),
        classical=logic == "classical",
        environment_sha256=environment_sha256,
        goals=goals,
        focus=focus,
        prompt_version=PEANO_PROMPT_V2,
        prompt_contract_sha256=contract_sha256,
        library_sha256=snapshot_sha256,
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
    "extract_one_tactic",
    "library_snapshot_sha256",
    "parse_prompt",
    "prompt_contract_sha256",
    "prompt_manifest_record",
    "prompt_version_from_manifest",
    "retrieve_theorems",
    "render_prompt",
    "validate_completion",
    "validate_tactic_line",
]
