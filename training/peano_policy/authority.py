"""Opt-in primitive-only authority constraints; no framework import or proof search.

The tokenizer constraint is deliberately a subset, not a second native parser:
canonical encoded command prefixes, exact imported names, and independently
decodable ByteLevel argument tokens. The native compiler remains authoritative.
It checks the whole completed line before search receives a candidate. Neither
that preflight nor the token mask claims that the tactic's arguments execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import re
from typing import Any
import unicodedata

from .prompt import PEANO_PROMPT_V4, PromptEnvironment, extract_one_tactic, prompt_contract_sha256


AUTHORITY_PRIMITIVE_PROFILE = "peano-authority-primitive-v1"
_NO_ARGUMENT = frozenset({"assumption", "split", "left", "right", "exfalso", "refl", "symm",
                          "congr", "norm_num", "ring"})
_OPTIONAL_ARGUMENT = frozenset({"intro", "simp", "compact_arith"})
_REQUIRED_ARGUMENT = frozenset({"have", "suffices", "apply", "exact", "cases", "exists",
                                "specialize", "forall_elim", "trans", "rewrite", "induction"})
AUTHORITY_PRIMITIVE_COMMANDS = _NO_ARGUMENT | _OPTIONAL_ARGUMENT | _REQUIRED_ARGUMENT | {"use"}
MAX_AUTHORITY_NEW_TOKENS = 128
MAX_VOCABULARY = 262_144
MAX_TOKEN_BYTES = 24
MAX_PREFIX_NODES = 65_536
_ASCII_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z", re.ASCII)


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, allow_nan=False,
                                     sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def authority_contract_record() -> dict[str, object]:
    """Return detached, versioned decoding semantics (not tokenizer weights)."""

    return {
        "schema": "peano-authority-decoding-contract-v1",
        "profile": AUTHORITY_PRIMITIVE_PROFILE,
        "prompt_version": PEANO_PROMPT_V4,
        "commands": sorted(AUTHORITY_PRIMITIVE_COMMANDS),
        "mode": "one primitive; no tacticals or session commands",
        "use": "exact finite allowed name, no alias; empty authority disables use",
        "heads": "canonical tokenizer.encode(head); arguments begin with an ASCII-space-prefixed token",
        "arguments": "independently valid UTF-8 ByteLevel tokens; no controls, semicolon, or pipe; < only in <- or <=",
        "tokenizer": "ByteLevel decoder only; other decoders fail closed",
        "completion": "EOS only after a complete head/import or non-space argument suffix",
        "postflight": "exact one line plus native whole-line primitive authority compilation",
        "argument_execution_checked": False,
        "repair_retry_refill_fallback": False,
        "model_generate_calls_per_batch": 1,
        "max_new_tokens": MAX_AUTHORITY_NEW_TOKENS,
        "max_vocabulary": MAX_VOCABULARY,
        "max_argument_token_bytes": MAX_TOKEN_BYTES,
        "max_prefix_nodes": MAX_PREFIX_NODES,
        "token_inventory_cache_size": 2,
        "native_capability_cache_size": 8,
        "tokenizer_byte_fragments": "excluded unless individually valid UTF-8; no completeness claim",
    }


def authority_contract_sha256() -> str:
    return _digest(authority_contract_record())


def _environment(environment: PromptEnvironment) -> tuple[str, ...]:
    if type(environment) is not PromptEnvironment or environment.prompt_version != PEANO_PROMPT_V4:
        raise ValueError("primitive authority decoding requires explicit prompt v4")
    capabilities = environment.capabilities
    commands, theorems = capabilities.allowed_commands, capabilities.allowed_theorems
    if commands is None or theorems is None:
        raise ValueError("primitive authority decoding requires finite permissions")
    if set(commands) - AUTHORITY_PRIMITIVE_COMMANDS:
        raise ValueError("authority contains unsupported non-primitive/session commands")
    if any(_ASCII_NAME.fullmatch(name) is None for name in theorems):
        raise ValueError("primitive profile v1 import names must be safe ASCII identifiers")
    return tuple(name for name in commands if name != "use" or theorems)


def authority_profile_record(environment: PromptEnvironment) -> dict[str, object]:
    """Bind the explicit profile to its complete, unchanged execution authority."""

    commands = _environment(environment)
    record = {
        "profile": AUTHORITY_PRIMITIVE_PROFILE,
        "contract_sha256": authority_contract_sha256(),
        "prompt_version": PEANO_PROMPT_V4,
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V4),
        "classical": environment.classical,
        "capabilities": environment.capabilities.to_record(),
        "environment_sha256": environment.sha256,
        "effective_commands": list(commands),
    }
    return {**record, "profile_sha256": _digest(record)}


@lru_cache(maxsize=8)
def _native_capabilities(environment: PromptEnvironment) -> Any:
    from peano_lab.ui.prove import SurfaceCapabilities

    identity = environment.capabilities
    return SurfaceCapabilities(label=identity.label,
                               allowed_commands=frozenset(identity.allowed_commands or ()),
                               allowed_theorems=frozenset(identity.allowed_theorems or ()))


def validate_authority_tactic(line: object, environment: PromptEnvironment) -> str:
    """Return the unmodified authorized primitive, without executing any tactic."""

    commands = _environment(environment)
    tactic = extract_one_tactic(line)
    if (len(tactic.encode("utf-8")) > 4096 or ";" in tactic or "|" in tactic
            or re.search(r"<(?![-=])", tactic)):
        raise ValueError("primitive authority profile forbids tactical separators or oversized lines")
    pieces = tactic.split(maxsplit=1)
    head = pieces[0]
    if head not in commands:
        raise ValueError("command is outside the primitive authority profile")
    args = pieces[1] if len(pieces) == 2 else ""
    if head in _NO_ARGUMENT and args or head in _REQUIRED_ARGUMENT and not args:
        raise ValueError("primitive argument presence differs from the profile")
    if head == "use" and args not in (environment.capabilities.allowed_theorems or ()):
        raise ValueError("use requires one exact allowed theorem name; aliases are not in this profile")
    from peano_lab.engine.tactics import TacticError
    from peano_lab.ui.prove import surface_transaction_name

    try:
        transaction = surface_transaction_name(tactic, environment.classical,
                                               _native_capabilities(environment))
    except (TacticError, TypeError, ValueError, RuntimeError, RecursionError) as error:
        raise ValueError(f"native primitive authority compilation failed: {error}") from error
    if transaction != head:
        raise ValueError("compiled command is a tactical rather than one primitive")
    return tactic


@dataclass(frozen=True, slots=True)
class _Vocabulary:
    pieces: dict[int, str]
    body_ids: tuple[int, ...]
    space_ids: tuple[int, ...]
    less_ids: tuple[int, ...]
    known_ids: frozenset[int]
    special_ids: frozenset[int]
    eos: int


def _safe_piece(piece: str) -> bool:
    return bool(piece) and len(piece.encode("utf-8")) <= MAX_TOKEN_BYTES and re.search(r"<(?![-=]|$)", piece) is None and not any(
        char in {";", "|", "\ufffd"} or unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for char in piece
    )


@lru_cache(maxsize=2)
def _vocabulary(tokenizer: Any) -> _Vocabulary:
    """One bounded vocabulary scan per tokenizer, never per generation step."""

    try:
        raw_decoder = tokenizer.backend_tokenizer.decoder.__getstate__()
        if type(raw_decoder) not in {str, bytes} or len(raw_decoder) > 4096:
            raise ValueError("missing bounded tokenizer decoder declaration")
        decoder = json.loads(raw_decoder)
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("authority decoding requires an inspectable ByteLevel tokenizer") from error
    if type(decoder) is not dict or decoder.get("type") != "ByteLevel":
        raise ValueError("authority decoding supports only a ByteLevel tokenizer")
    vocab = tokenizer.get_vocab()
    if type(vocab) is not dict or not 1 <= len(vocab) <= MAX_VOCABULARY:
        raise ValueError("tokenizer vocabulary exceeds its finite bound")
    values = tuple(vocab.values())
    if any(type(value) is not int or not 0 <= value < MAX_VOCABULARY for value in values) or len(set(values)) != len(values):
        raise ValueError("tokenizer vocabulary identifiers must be unique bounded integers")
    ids = tuple(sorted(values))
    eos = tokenizer.eos_token_id
    special = frozenset(tokenizer.all_special_ids)
    if type(eos) is not int or eos not in ids or eos not in special:
        raise ValueError("authority decoding requires one declared EOS token")
    pieces = {}
    for token in ids:
        if token in special:
            continue
        piece = tokenizer.decode([token], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if type(piece) is not str:
            raise ValueError("tokenizer did not decode a text token")
        if _safe_piece(piece):
            pieces[token] = piece
    if not pieces:
        raise ValueError("tokenizer has no safe independently decoded argument tokens")
    return _Vocabulary(pieces, tuple(sorted(pieces)),
                       tuple(token for token in sorted(pieces) if pieces[token].startswith(" ")),
                       tuple(token for token in sorted(pieces) if pieces[token].startswith(("-", "="))),
                       frozenset(ids), special, eos)


class AuthorityTokenConstraint:
    """Stateless per-beam prefix callback; one model.generate call is sufficient.

    Only prefix paths are tokenized per batch. Argument token IDs are cached
    once, and each callback examines at most max_new_tokens retained IDs.
    """

    def __init__(self, tokenizer: Any, environment: PromptEnvironment, *, prompt_length: int,
                 max_new_tokens: int) -> None:
        commands = _environment(environment)
        if type(prompt_length) is not int or prompt_length < 0:
            raise ValueError("prompt_length must be a nonnegative integer")
        if type(max_new_tokens) is not int or not 1 <= max_new_tokens <= MAX_AUTHORITY_NEW_TOKENS:
            raise ValueError("authority max_new_tokens must be an integer in [1,128]")
        if not commands:
            raise ValueError("authority has no decodable primitive command")
        self.prompt_length = prompt_length
        self.max_new_tokens = max_new_tokens
        self.vocabulary = _vocabulary(tokenizer)
        if set(commands) & (_OPTIONAL_ARGUMENT | _REQUIRED_ARGUMENT) and not self.vocabulary.space_ids:
            raise ValueError("tokenizer cannot begin a primitive argument with an ASCII space")
        self.nodes: list[dict[int, int]] = [{}]
        self.terminal: dict[int, str] = {}

        def add(text: str, mode: str) -> None:
            encoded = tokenizer.encode(text, add_special_tokens=False)
            if type(encoded) is not list or not encoded or len(encoded) > 512:
                raise ValueError("authority prefix tokenization is not bounded exact IDs")
            if any(type(token) is not int or token not in self.vocabulary.known_ids
                   or token in self.vocabulary.special_ids for token in encoded):
                raise ValueError("authority prefix contains an invalid token identifier")
            if tokenizer.decode(encoded, skip_special_tokens=False,
                                clean_up_tokenization_spaces=False) != text:
                raise ValueError("authority prefix does not round-trip exactly")
            node = 0
            for token in encoded:
                if token not in self.nodes[node]:
                    if len(self.nodes) >= MAX_PREFIX_NODES:
                        raise ValueError("authority token prefix trie exceeds its bound")
                    self.nodes[node][token] = len(self.nodes)
                    self.nodes.append({})
                node = self.nodes[node][token]
            if node in self.terminal and self.terminal[node] != mode:
                raise ValueError("tokenizer produced an ambiguous authority prefix")
            self.terminal[node] = mode

        for command in commands:
            if command in _NO_ARGUMENT:
                add(command, "end")
            if command in _OPTIONAL_ARGUMENT:
                add(command, "end-or-args")
            if command in _REQUIRED_ARGUMENT:
                add(command, "args")
            if command == "use":
                for name in environment.capabilities.allowed_theorems or ():
                    add("use " + name, "end")

    def __call__(self, batch_id: int, input_ids: Any) -> list[int]:
        del batch_id  # Every beam is determined by its own full suffix, never a mutable cursor.
        values = input_ids.tolist()
        if type(values) is not list or len(values) < self.prompt_length:
            raise ValueError("authority callback requires a complete one-dimensional prompt prefix")
        suffix = values[self.prompt_length:]
        if len(suffix) > self.max_new_tokens or any(type(token) is not int for token in suffix):
            raise ValueError("authority prefix exceeds its generation bound")
        node = 0
        mode = None
        body: list[str] = []
        for index, token in enumerate(suffix):
            if mode == "body":
                if token == self.vocabulary.eos and body and not body[-1][-1].isspace() and not body[-1].endswith("<"):
                    if any(rest != self.vocabulary.eos for rest in suffix[index:]):
                        raise ValueError("non-EOS token follows completed authority output")
                    return [self.vocabulary.eos]
                piece = self.vocabulary.pieces.get(token)
                if piece is None:
                    raise ValueError("generated token is outside the safe primitive argument alphabet")
                if body and body[-1].endswith("<") and not piece.startswith(("-", "=")):
                    raise ValueError("less-than token can continue only as <- or <=, never markup")
                body.append(piece)
            elif token in self.nodes[node]:
                node = self.nodes[node][token]
                mode = self.terminal.get(node)
            elif token == self.vocabulary.eos and mode in {"end", "end-or-args"}:
                if any(rest != self.vocabulary.eos for rest in suffix[index:]):
                    raise ValueError("non-EOS token follows completed authority output")
                return [self.vocabulary.eos]
            elif mode in {"args", "end-or-args"}:
                piece = self.vocabulary.pieces.get(token)
                if piece is None or not piece.startswith(" "):
                    raise ValueError("primitive arguments must start with an ASCII space")
                mode = "body"
                body.append(piece)
            else:
                raise ValueError("generated prefix is outside the exact primitive authority trie")
        if mode == "body":
            if body and body[-1].endswith("<"):
                return list(self.vocabulary.less_ids)
            result = list(self.vocabulary.body_ids)
            if body and not body[-1][-1].isspace():
                result.append(self.vocabulary.eos)
            return result
        result = sorted(self.nodes[node])
        if mode in {"args", "end-or-args"}:
            result.extend(self.vocabulary.space_ids)
        if mode in {"end", "end-or-args"}:
            result.append(self.vocabulary.eos)
        if not result:
            raise ValueError("authority decoder reached an impossible prefix")
        return result


__all__ = ["AUTHORITY_PRIMITIVE_PROFILE", "AUTHORITY_PRIMITIVE_COMMANDS", "AuthorityTokenConstraint",
           "authority_contract_record", "authority_contract_sha256", "authority_profile_record",
           "validate_authority_tactic"]
