"""Repository-owned prompt contract for Peano next-tactic policies.

The policy sees only a canonical proof state plus the exact authority under
which its proposed tactic will run.  The theorem's library name and a separate
copy of its statement are deliberately absent.  Dataset compilation stores
the rendered prompt verbatim; training consumes that stored value after
checking it against the row's redundant state and capability fields.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
import re
import unicodedata


PEANO_PROMPT_VERSION = 1
TASK = "next_tactic"
ENVIRONMENT_BASE = "peano-lab-v1"
COMPLETION_SUFFIX = "</tactic>"
_CAPABILITY_FIELDS = ("label", "allowed_commands", "allowed_theorems")
_RESERVED_MARKERS = (
    "<task>",
    "</task>",
    "<env>",
    "</env>",
    "<state>",
    "</state>",
    "<tactic>",
    COMPLETION_SUFFIX,
)
_ENVIRONMENT_RE = re.compile(
    r"peano-lab-v1;surface=([^;\n]+);"
    r"logic=(classical|intuitionistic);capability_sha256=([0-9a-f]{64})"
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
class PromptEnvironment:
    """Logic mode and exact capability preimage included in every prompt."""

    classical: bool
    capabilities: CapabilityIdentity

    def __post_init__(self) -> None:
        if type(self.classical) is not bool:
            raise PromptError("classical must be a Boolean")
        if type(self.capabilities) is not CapabilityIdentity:
            raise PromptError("capabilities must be a CapabilityIdentity")

    @property
    def sha256(self) -> str:
        return self.capabilities.sha256

    @property
    def text(self) -> str:
        logic = "classical" if self.classical else "intuitionistic"
        return (
            f"{ENVIRONMENT_BASE};surface={self.capabilities.label};logic={logic};"
            f"capability_sha256={self.sha256}"
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
    return (
        f"<task>{TASK}</task>\n"
        f"<env>{environment.text}</env>\n"
        f"<state>{state}</state>\n"
        "<tactic>"
    )


def prompt_manifest_record() -> dict[str, str]:
    """Return the dataset manifest declaration for this exact contract."""

    return {
        "task": TASK,
        "environment_base": ENVIRONMENT_BASE,
        "environment_template": (
            "peano-lab-v1;surface=LABEL;logic=MODE;capability_sha256=SHA256"
        ),
        "template": (
            "<task>...</task>\\n<env>...</env>\\n<state>...</state>\\n<tactic>"
        ),
        "completion_suffix": COMPLETION_SUFFIX,
        "binder_policy": "exact-authored-binders-v1",
        "binder_policy_detail": (
            "preserve exact visible state names and exact successful tactic "
            "lines so every emitted transition is executable"
        ),
    }


def parse_prompt(value: object) -> ParsedPrompt:
    """Validate a stored/inference prefix and expose its visible fields."""

    prompt = _safe_text("prompt", value, multiline=True)
    prefix = f"<task>{TASK}</task>\n<env>"
    state_marker = "</env>\n<state>"
    suffix = "</state>\n<tactic>"
    if not prompt.startswith(prefix) or not prompt.endswith(suffix):
        raise PromptError("prompt does not match the Peano next-tactic template")
    middle = prompt[len(prefix) : -len(suffix)]
    if middle.count(state_marker) != 1:
        raise PromptError("prompt has a malformed environment/state boundary")
    environment_text, state_text = middle.split(state_marker)
    match = _ENVIRONMENT_RE.fullmatch(environment_text)
    if match is None:
        raise PromptError("prompt has a malformed environment identity")
    surface, logic, environment_sha256 = match.groups()
    _safe_text("surface", surface)
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
    return ParsedPrompt(
        environment=environment_text,
        surface=surface,
        classical=logic == "classical",
        environment_sha256=environment_sha256,
        goals=goals,
        focus=focus,
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
    "ParsedPrompt",
    "PromptEnvironment",
    "PromptError",
    "ProofExample",
    "TASK",
    "extract_one_tactic",
    "parse_prompt",
    "prompt_manifest_record",
    "render_prompt",
    "validate_completion",
    "validate_tactic_line",
]
