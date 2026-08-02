#!/usr/bin/env python3
"""Build the parallel, definition-aware PA Proof Explorer.

This is a documentation generator only.  It neither parses defined notation nor
replays tactics.  The reviewed elaboration layer is expected to expose
``peano_lab.library.defined_edition.build_defined_edition()`` with this exact
JSON-compatible result shape::

    {
      "schema": "peano-lab-defined-edition-v1",
      "identity_sha256": "<sha256 of the adapter's reviewed records>",
      "definitions": [
        {
          "id": "PD0001",
          "name": "Prime",
          "signature": "Prime(p)",
          "summary": "...",
          "expansion": "~(p = 1) /\\ ...",
          "expansion_sha256": "<sha256 of expansion>",
          "dependencies": ["PD...."],
          "source": {
            "path": "peano-lab/py/peano_lab/library/defined_edition.py",
            "line": 1,
            "sha256": "<sha256 of source file>"
          }
        }
      ],
      "theorems": [
        {
          "name": "add_zero",
          "defined_statement": "forall n. n + 0 = n",
          "expanded_statement_sha256": "<sha256 of exact TheoremSpec.statement>",
          "statement_parts": [
            {"kind": "text", "text": "forall n. "},
            {"kind": "definition", "definition": "PD0001",
             "text": "Prime(n)"}
          ],
          "defined_script_lines": [
            {
              "number": 1,
              "defined_command": "have hp : Prime(p)",
              "expanded_command_sha256": "<sha256 of exact tactic command>",
              "command_parts": [
                {"kind": "text", "text": "have hp : "},
                {"kind": "definition", "definition": "PD0001",
                 "text": "Prime(p)"}
              ]
            }
          ]
        }
      ]
    }

The theorem list must cover the explicit QR corpus exactly.  Concatenating the
``text`` fields of statement or command parts must reproduce the corresponding
defined surface.  Definition parts are the sole source of
theorem-to-definition edges.  A definition's ``dependencies`` are the sole
source of definition-to-definition edges.  The adapter is responsible for
proving that expanding every displayed theorem and local ``have``/``suffices``
proposition recovers the exact native input; this generator checks the
adapter-provided expanded-source and definition-expansion digests.

The existing explicit explorer is read but never written.  All output belongs
below ``book/_static/pa-proof-explorer/defined``.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from hashlib import sha256
import html
import importlib
import json
from pathlib import Path
import re
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PY_ROOT = REPO / "peano-lab" / "py"
sys.path.insert(0, str(PY_ROOT))

EXPLICIT = REPO / "book" / "_static" / "pa-proof-explorer"
EXPLICIT_CORPUS = EXPLICIT / "api" / "corpus.json"
EXPLICIT_GRAPH = EXPLICIT / "api" / "graph.json"
OUTPUT = EXPLICIT / "defined"
ASSET_SOURCE = OUTPUT / "assets"
PA_RE = re.compile(r"^PA[0-9A-Y]{4}$")
PD_RE = re.compile(r"^PD[0-9A-Y]{4}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ADAPTER_MODULE = "peano_lab.library.defined_edition"
ADAPTER_FUNCTION = "build_defined_edition"
PINNED_ASSETS = {
    "assets/explorer.css": "2aab0ad0521683f09e88de459be6857140b99617fe317e8a08affe407932eb6c",
    "assets/explorer.js": "72e347ac99a7507d001db7458d81f7ed4a0244398c03dc0917f864ce4fbe0aa8",
}


class DefinedEditionError(ValueError):
    """The notation adapter or explicit explorer violates the display contract."""


def _digest(value: bytes | str) -> str:
    return sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DefinedEditionError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise DefinedEditionError(f"{label} must be a JSON object")
    return value


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _require_text(record: Mapping[str, Any], key: str, label: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DefinedEditionError(f"{label}.{key} must be nonempty text")
    return value


def _require_sha(record: Mapping[str, Any], key: str, label: str) -> str:
    value = _require_text(record, key, label)
    if not SHA_RE.fullmatch(value):
        raise DefinedEditionError(f"{label}.{key} must be a lowercase SHA-256")
    return value


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DefinedEditionError(f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise DefinedEditionError(f"{label} must be an array")
    return value


def load_defined_edition() -> Mapping[str, Any]:
    """Load the narrow reviewed adapter without importing it at module import time."""

    try:
        module = importlib.import_module(ADAPTER_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name == ADAPTER_MODULE:
            raise DefinedEditionError(
                f"missing {ADAPTER_MODULE}; implement {ADAPTER_FUNCTION}() with the "
                "record contract documented in this script"
            ) from exc
        raise
    builder = getattr(module, ADAPTER_FUNCTION, None)
    if not callable(builder):
        raise DefinedEditionError(
            f"{ADAPTER_MODULE} must export callable {ADAPTER_FUNCTION}()"
        )
    return _mapping(builder(), f"{ADAPTER_MODULE}.{ADAPTER_FUNCTION}()")


def _validate_source(value: object, label: str) -> dict[str, Any]:
    source = _mapping(value, f"{label}.source")
    path = _require_text(source, "path", f"{label}.source")
    line = source.get("line")
    if type(line) is not int or line < 1:
        raise DefinedEditionError(f"{label}.source.line must be a positive integer")
    source_sha = _require_sha(source, "sha256", f"{label}.source")
    return {"path": path, "line": line, "sha256": source_sha}


def _validate_parts(
    value: object,
    *,
    theorem_name: str,
    definitions: Mapping[str, Mapping[str, Any]],
    field: str = "statement_parts",
) -> tuple[list[dict[str, str]], Counter[str]]:
    parts: list[dict[str, str]] = []
    uses: Counter[str] = Counter()
    label = f"theorem {theorem_name}.{field}"
    for index, raw in enumerate(_sequence(value, label)):
        part = _mapping(raw, f"{label}[{index}]")
        kind = part.get("kind")
        text = part.get("text")
        if kind not in {"text", "definition"} or not isinstance(text, str) or not text:
            raise DefinedEditionError(
                f"{label}[{index}] has invalid kind/text"
            )
        if kind == "text":
            if set(part) != {"kind", "text"}:
                raise DefinedEditionError(
                    f"plain {field} part {index} for {theorem_name} has extra fields"
                )
            parts.append({"kind": "text", "text": text})
            continue
        definition_id = part.get("definition")
        if set(part) != {"kind", "definition", "text"}:
            raise DefinedEditionError(
                f"definition {field} part {index} for {theorem_name} has extra fields"
            )
        if not isinstance(definition_id, str) or definition_id not in definitions:
            raise DefinedEditionError(
                f"unknown definition {definition_id!r} in theorem {theorem_name}"
            )
        parts.append(
            {"kind": "definition", "definition": definition_id, "text": text}
        )
        uses[definition_id] += 1
    if not parts:
        raise DefinedEditionError(f"theorem {theorem_name} has no {field}")
    return parts, uses


def validate_edition(
    raw: Mapping[str, Any],
    explicit_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate and normalize the adapter result without trusting display HTML."""

    if raw.get("schema") != "peano-lab-defined-edition-v1":
        raise DefinedEditionError("defined edition has an unknown schema")
    identity_sha = _require_sha(raw, "identity_sha256", "defined edition")
    definitions: dict[str, dict[str, Any]] = {}
    definition_names: set[str] = set()
    ordered_definition_ids: list[str] = []
    for index, raw_definition in enumerate(
        _sequence(raw.get("definitions"), "defined edition.definitions")
    ):
        record = _mapping(raw_definition, f"definition[{index}]")
        definition_id = _require_text(record, "id", f"definition[{index}]")
        if not PD_RE.fullmatch(definition_id):
            raise DefinedEditionError(f"invalid persistent definition ID {definition_id!r}")
        if definition_id in definitions:
            raise DefinedEditionError(f"duplicate definition ID {definition_id}")
        name = _require_text(record, "name", f"definition {definition_id}")
        if name in definition_names:
            raise DefinedEditionError(f"duplicate definition name {name!r}")
        signature = _require_text(record, "signature", f"definition {definition_id}")
        summary = _require_text(record, "summary", f"definition {definition_id}")
        expansion = _require_text(record, "expansion", f"definition {definition_id}")
        expansion_sha = _require_sha(
            record, "expansion_sha256", f"definition {definition_id}"
        )
        if expansion_sha != _digest(expansion):
            raise DefinedEditionError(f"definition {definition_id} expansion digest disagrees")
        dependencies = list(
            _sequence(record.get("dependencies"), f"definition {definition_id}.dependencies")
        )
        if any(not isinstance(item, str) for item in dependencies):
            raise DefinedEditionError(
                f"definition {definition_id}.dependencies must contain definition IDs"
            )
        if len(dependencies) != len(set(dependencies)):
            raise DefinedEditionError(f"definition {definition_id} repeats a dependency")
        # Requiring preceding definitions gives the presentation graph a simple,
        # audited acyclic order without interpreting any mathematical syntax.
        unknown = [item for item in dependencies if item not in definitions]
        if unknown:
            raise DefinedEditionError(
                f"definition {definition_id} has non-preceding dependencies: {unknown!r}"
            )
        definitions[definition_id] = {
            "id": definition_id,
            "name": name,
            "signature": signature,
            "summary": summary,
            "expansion": expansion,
            "expansion_sha256": expansion_sha,
            "dependencies": dependencies,
            "source": _validate_source(record.get("source"), f"definition {definition_id}"),
        }
        definition_names.add(name)
        ordered_definition_ids.append(definition_id)
    if not definitions:
        raise DefinedEditionError("defined edition must contain at least one definition")

    explicit_by_name = {str(row.get("name")): row for row in explicit_records}
    if len(explicit_by_name) != len(explicit_records):
        raise DefinedEditionError("explicit corpus contains duplicate theorem names")
    theorem_rows = _sequence(raw.get("theorems"), "defined edition.theorems")
    normalized_theorems: dict[str, dict[str, Any]] = {}
    adapter_theorem_order: list[str] = []
    for index, raw_theorem in enumerate(theorem_rows):
        record = _mapping(raw_theorem, f"defined theorem[{index}]")
        name = _require_text(record, "name", f"defined theorem[{index}]")
        if name not in explicit_by_name:
            raise DefinedEditionError(f"defined edition contains unknown theorem {name!r}")
        if name in normalized_theorems:
            raise DefinedEditionError(f"defined edition repeats theorem {name!r}")
        adapter_theorem_order.append(name)
        statement = _require_text(record, "defined_statement", f"theorem {name}")
        expanded_sha = _require_sha(
            record, "expanded_statement_sha256", f"theorem {name}"
        )
        explicit_statement = _require_text(explicit_by_name[name], "statement", f"explicit {name}")
        if expanded_sha != _digest(explicit_statement):
            raise DefinedEditionError(
                f"theorem {name} does not attest the current explicit statement"
            )
        parts, statement_uses = _validate_parts(
            record.get("statement_parts"),
            theorem_name=name,
            definitions=definitions,
        )
        if "".join(part["text"] for part in parts) != statement:
            raise DefinedEditionError(
                f"theorem {name} statement parts do not reproduce defined_statement"
            )
        explicit_lines = _sequence(
            explicit_by_name[name].get("lines"), f"explicit theorem {name}.lines"
        )
        raw_script_lines = _sequence(
            record.get("defined_script_lines"),
            f"theorem {name}.defined_script_lines",
        )
        if len(raw_script_lines) != len(explicit_lines):
            raise DefinedEditionError(
                f"theorem {name} defined script has {len(raw_script_lines)} lines; "
                f"explicit script has {len(explicit_lines)}"
            )
        script_lines: list[dict[str, Any]] = []
        script_uses: Counter[str] = Counter()
        for line_index, (raw_line, raw_explicit_line) in enumerate(
            zip(raw_script_lines, explicit_lines, strict=True)
        ):
            label = f"theorem {name}.defined_script_lines[{line_index}]"
            line = _mapping(raw_line, label)
            explicit_line = _mapping(
                raw_explicit_line, f"explicit theorem {name}.lines[{line_index}]"
            )
            number = line.get("number")
            explicit_number = explicit_line.get("number")
            if type(number) is not int or number != explicit_number:
                raise DefinedEditionError(
                    f"{label}.number must equal explicit line number {explicit_number!r}"
                )
            command = _require_text(line, "defined_command", label)
            command_sha = _require_sha(line, "expanded_command_sha256", label)
            explicit_command = _require_text(
                explicit_line, "text", f"explicit theorem {name}.lines[{line_index}]"
            )
            if command_sha != _digest(explicit_command):
                raise DefinedEditionError(
                    f"{label} does not attest the current explicit tactic command"
                )
            command_parts, line_uses = _validate_parts(
                line.get("command_parts"),
                theorem_name=name,
                definitions=definitions,
                field=f"defined_script_lines[{line_index}].command_parts",
            )
            if "".join(part["text"] for part in command_parts) != command:
                raise DefinedEditionError(
                    f"{label}.command_parts do not reproduce defined_command"
                )
            tactic = explicit_line.get("tactic")
            changed = command != explicit_command
            if changed and tactic not in {"have", "suffices"}:
                raise DefinedEditionError(
                    f"{label} changes nonlocal tactic {tactic!r}"
                )
            if changed and not line_uses:
                raise DefinedEditionError(
                    f"{label} changes text without using a reviewed definition"
                )
            script_uses.update(line_uses)
            script_lines.append(
                {
                    "number": number,
                    "defined_command": command,
                    "expanded_command_sha256": command_sha,
                    "command_parts": command_parts,
                }
            )
        total_uses = statement_uses + script_uses
        normalized_theorems[name] = {
            "name": name,
            "defined_statement": statement,
            "expanded_statement_sha256": expanded_sha,
            "statement_parts": parts,
            "defined_script_lines": script_lines,
            "statement_definition_uses": dict(sorted(statement_uses.items())),
            "script_definition_uses": dict(sorted(script_uses.items())),
            "definition_uses": dict(sorted(total_uses.items())),
        }
    missing = set(explicit_by_name) - set(normalized_theorems)
    if missing or len(normalized_theorems) != len(explicit_by_name):
        raise DefinedEditionError(
            f"defined theorem coverage differs from explicit corpus; missing={sorted(missing)[:8]!r}"
        )

    normalized = {
        "schema": "peano-lab-defined-edition-v1",
        "identity_sha256": identity_sha,
        "definitions": [definitions[item] for item in ordered_definition_ids],
        "theorems": [normalized_theorems[str(row["name"])] for row in explicit_records],
    }
    # The adapter identity is over its semantic normalized payload, excluding
    # the self-referential identity field itself.
    identity_payload = {
        "schema": normalized["schema"],
        "definitions": normalized["definitions"],
        # The adapter identity follows its reviewed dependency order.  The
        # returned display edition is separately reordered to the persistent
        # explicit-corpus/tag order below.
        "theorems": [normalized_theorems[name] for name in adapter_theorem_order],
    }
    actual_identity = _digest(
        json.dumps(identity_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    if actual_identity != identity_sha:
        raise DefinedEditionError(
            f"defined edition identity changed: expected {identity_sha}, found {actual_identity}"
        )
    return normalized


def _pinned_assets() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for relative, expected in PINNED_ASSETS.items():
        path = OUTPUT / relative
        if not path.is_file():
            raise DefinedEditionError(f"missing defined-explorer UI asset: {relative}")
        payload = path.read_bytes()
        actual = _digest(payload)
        if actual != expected:
            raise DefinedEditionError(
                f"defined-explorer UI asset drift for {relative}: expected {expected}, found {actual}"
            )
        files[relative] = payload
    return files


def _page(title: str, page: str, body: str, asset_prefix: str = "") -> bytes:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)}</title><link rel="stylesheet" href="{asset_prefix}assets/explorer.css"><script defer src="{asset_prefix}assets/explorer.js"></script></head>
<body class="pa-defined-proof-site" data-page="{_e(page)}">{body}</body></html>
""".encode()


def _javascript_assignment(name: str, value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    payload = payload.replace("&", r"\u0026").replace("<", r"\u003c").replace(">", r"\u003e")
    return f"window.{name}={payload};"


def _render_defined_parts(
    parts: Sequence[Mapping[str, str]],
    *,
    tactic: str | None = None,
) -> str:
    rendered: list[str] = []
    tactic_pending = tactic
    for part in parts:
        if part["kind"] == "text":
            text = part["text"]
            if tactic_pending and text.startswith(tactic_pending):
                rendered.append(
                    f'<a class="pd-tactic-ref" href="../../foundations.html#tactic-{_e(tactic_pending)}">'
                    f'{_e(tactic_pending)}</a>{_e(text[len(tactic_pending):])}'
                )
                tactic_pending = None
            else:
                rendered.append(_e(text))
        else:
            rendered.append(
                f'<a class="pd-definition-ref" href="../definition/{_e(part["definition"])}.html">'
                f'{_e(part["text"])}</a>'
            )
    return "".join(rendered)


def _render_command(line: Mapping[str, Any]) -> str:
    text = str(line["text"])
    tactic = str(line["tactic"])
    spans: list[tuple[int, int, str, Mapping[str, Any] | None]] = [
        (0, len(tactic), "tactic", None)
    ]
    for reference in list(line.get("references", [])) + list(line.get("axiom_references", [])):
        spans.append((int(reference["start"]), int(reference["end"]), str(reference["kind"]), reference))
    pieces: list[str] = []
    cursor = 0
    for left, right, kind, reference in sorted(spans):
        if left < cursor:
            continue
        pieces.append(_e(text[cursor:left]))
        token = text[left:right]
        if kind == "tactic":
            pieces.append(
                f'<a class="pd-tactic-ref" href="../../foundations.html#tactic-{_e(token)}">{_e(token)}</a>'
            )
        elif kind in {"theorem", "dependency"} and reference is not None:
            pieces.append(
                f'<a class="pd-theorem-ref" href="{_e(reference["tag"])}.html">{_e(token)}</a>'
            )
        elif reference is not None:
            pieces.append(
                f'<a class="pd-axiom-ref" href="../../foundations.html#axiom-{_e(str(reference["name"]).lower())}">{_e(token)}</a>'
            )
        else:
            pieces.append(_e(token))
        cursor = right
    pieces.append(_e(text[cursor:]))
    return "".join(pieces)


def _render_defined_command(
    explicit_line: Mapping[str, Any],
    defined_line: Mapping[str, Any],
) -> str:
    if defined_line["defined_command"] == explicit_line["text"]:
        return _render_command(explicit_line)
    return _render_defined_parts(
        defined_line["command_parts"], tactic=str(explicit_line["tactic"])
    )


def _relation(items: Sequence[Mapping[str, Any]]) -> str:
    if not items:
        return '<span class="pd-empty">none</span>'
    return " ".join(
        f'<a class="pd-chip pd-theorem-chip" href="{_e(item["tag"])}.html">'
        f'<code>{_e(item["tag"])}</code> {_e(item["name"])}</a>'
        for item in items
    )


def _definition_chips(ids: Sequence[str], definitions: Mapping[str, Mapping[str, Any]], prefix: str = "../definition/") -> str:
    if not ids:
        return '<span class="pd-empty">none</span>'
    return " ".join(
        f'<a class="pd-chip pd-definition-chip" href="{prefix}{_e(item)}.html">'
        f'<code>{_e(item)}</code> {_e(definitions[item]["name"])}</a>'
        for item in ids
    )


def _render_theorem(
    row: Mapping[str, Any],
    definitions: Mapping[str, Mapping[str, Any]],
    previous: Mapping[str, Any] | None,
    following: Mapping[str, Any] | None,
) -> bytes:
    defined = row["defined"]
    statement_uses = list(defined["statement_definition_uses"])
    script_uses = list(defined["script_definition_uses"])
    line_rows: list[str] = []
    changed_line_count = 0
    for explicit_line, defined_line in zip(
        row["lines"], defined["defined_script_lines"], strict=True
    ):
        number = int(explicit_line["number"])
        changed = defined_line["defined_command"] != explicit_line["text"]
        changed_line_count += changed
        exact = ""
        classes = "pd-proof-line pd-proof-line-defined" if changed else "pd-proof-line"
        if changed:
            exact = (
                '<details class="pd-exact-line"><summary>Exact native replay line</summary>'
                f'<code>{_render_command(explicit_line)}</code></details>'
            )
        line_rows.append(
            f'<li class="{classes}" id="proof-line-{number:04d}" data-line="{number}" '
            f'data-defined-changed="{str(changed).lower()}">'
            f'<a class="pd-line-number" href="#proof-line-{number:04d}">{number:04d}</a>'
            f'<code class="pd-defined-command">{_render_defined_command(explicit_line, defined_line)}</code>'
            f'{exact}</li>'
        )
    lines = "".join(line_rows)
    prev_link = f'<a href="{_e(previous["tag"])}.html">← {_e(previous["name"])}</a>' if previous else ""
    next_link = f'<a href="{_e(following["tag"])}.html">{_e(following["name"])} →</a>' if following else ""
    body = f'''<header class="pd-header"><nav><a href="../index.html">Defined edition</a><a href="../../tag/{_e(row["tag"])}.html">Explicit edition</a><a href="../graph.html?target={_e(row["tag"])}">Mixed graph</a>{prev_link}{next_link}</nav><p class="pd-kicker">{_e(row["tag"])} · theorem</p><h1>{_e(row["name"])}</h1><p class="pd-status pd-status-{_e(row["scope"])}">{_e(row["status_label"])}</p><p>{_e(row["summary"])}</p></header>
<main class="pd-theorem-layout"><div><section><h2>Statement with defined notation</h2><button type="button" data-copy-target="defined-statement">Copy text</button><pre id="defined-statement"><code>{_render_defined_parts(defined["statement_parts"])}</code></pre><p class="pd-callout">Every purple notation token opens its conservative definition. This is a reading surface; the compiler expands the statement before the unchanged kernel checks it.</p></section><section><h2>Definitions used by this theorem</h2><h3>In the theorem statement</h3><div class="pd-chip-row">{_definition_chips(statement_uses, definitions)}</div><p>{sum(defined["statement_definition_uses"].values())} occurrences</p><h3>In local proof propositions</h3><div class="pd-chip-row">{_definition_chips(script_uses, definitions)}</div><p>{sum(defined["script_definition_uses"].values())} occurrences</p></section><details><summary>Exact expanded native-PA statement</summary><button type="button" data-copy-target="expanded-statement">Copy expansion</button><pre id="expanded-statement"><code>{_e(row["statement"])}</code></pre></details><section><h2>Proof neighborhood</h2><h3>Direct theorem prerequisites</h3><div class="pd-chip-row">{_relation(row["dependencies"])}</div><h3>Direct theorem dependents</h3><div class="pd-chip-row">{_relation(row["dependents"])}</div></section><section><h2>Definition-aware tactic body</h2><p>Only local propositions introduced by <code>have</code> or <code>suffices</code> are compacted. The untrusted compiler re-expands each one before the original tactic script is replayed; defined notation is never accepted by the kernel. Open the exact replay line beneath every changed command.</p><ol class="pd-formal-proof">{lines}</ol></section></div><aside><h2>Display receipt</h2><dl><dt>Proof layer</dt><dd>{row["layer"]}</dd><dt>Defined-notation uses</dt><dd>{sum(defined["definition_uses"].values())}</dd><dt>Statement definitions</dt><dd>{len(statement_uses)}</dd><dt>Local-proof definitions</dt><dd>{len(script_uses)}</dd><dt>Compacted local lines</dt><dd>{changed_line_count}</dd><dt>Exact statement SHA-256</dt><dd><code>{_e(row["statement_sha256"])}</code></dd><dt>Explicit proof</dt><dd><a href="../../tag/{_e(row["tag"])}.html">open immutable explicit page</a></dd><dt>Native source</dt><dd><a href="{_e(row["source"]["href"])}">{_e(row["source"]["path"])}:{row["source"]["line"]}</a></dd></dl></aside></main>'''
    return _page(f'{row["tag"]} — {row["name"]} — defined notation', "theorem", body, "../")


def _render_definition(
    definition: Mapping[str, Any],
    definitions: Mapping[str, Mapping[str, Any]],
    theorem_users: Sequence[Mapping[str, Any]],
    definition_users: Sequence[Mapping[str, Any]],
) -> bytes:
    source = definition["source"]
    dependent_definitions = (
        " ".join(
            f'<a class="pd-chip pd-definition-chip" href="{_e(item["id"])}.html"><code>{_e(item["id"])}</code> {_e(item["name"])}</a>'
            for item in definition_users
        ) or '<span class="pd-empty">none</span>'
    )
    used_theorems = (
        " ".join(
            f'<a class="pd-chip pd-theorem-chip" href="../tag/{_e(item["tag"])}.html"><code>{_e(item["tag"])}</code> {_e(item["name"])}</a>'
            for item in theorem_users
        ) or '<span class="pd-empty">none</span>'
    )
    body = f'''<header class="pd-header pd-definition-header"><nav><a href="../index.html">Defined edition</a><a href="../graph.html?focus={_e(definition["id"])}">Mixed graph</a><a href="../../foundations.html">PA foundations</a></nav><p class="pd-kicker">{_e(definition["id"])} · conservative definition</p><h1>{_e(definition["name"])}</h1><p>{_e(definition["summary"])}</p></header><main class="pd-definition-page"><section><h2>Readable signature</h2><pre><code>{_e(definition["signature"])}</code></pre></section><section><h2>Exact expansion</h2><button type="button" data-copy-target="definition-expansion">Copy expansion</button><pre id="definition-expansion"><code>{_e(definition["expansion"])}</code></pre><p class="pd-callout">This node is notation, not a theorem, axiom, predicate constant, or kernel rule. The elaboration layer must expand it before proof checking.</p></section><section><h2>Definition neighborhood</h2><h3>Expands using</h3><div class="pd-chip-row">{_definition_chips(definition["dependencies"], definitions, "")}</div><h3>Used by definitions</h3><div class="pd-chip-row">{dependent_definitions}</div><h3>Used by theorem statements or local proof propositions</h3><div class="pd-chip-row">{used_theorems}</div></section><aside><h2>Definition receipt</h2><dl><dt>Expansion SHA-256</dt><dd><code>{_e(definition["expansion_sha256"])}</code></dd><dt>Source</dt><dd>{_e(source["path"])}:{source["line"]}</dd><dt>Source SHA-256</dt><dd><code>{_e(source["sha256"])}</code></dd></dl></aside></main>'''
    return _page(f'{definition["id"]} — {definition["name"]}', "definition", body, "../")


def _mixed_graph(
    theorem_records: Sequence[Mapping[str, Any]],
    definitions: Sequence[Mapping[str, Any]],
    explicit_graph: Mapping[str, Any],
    identity_sha: str,
) -> dict[str, Any]:
    by_definition = {row["id"]: row for row in definitions}
    nodes: list[dict[str, Any]] = [
        {
            "id": row["tag"], "kind": "theorem", "tag": row["tag"],
            "name": row["name"], "scope": row["scope"], "status": row["status"],
            "layer": row["layer"], "summary": row["summary"],
            "href": f'tag/{row["tag"]}.html',
        }
        for row in theorem_records
    ]
    nodes.extend(
        {
            "id": row["id"], "kind": "definition", "name": row["name"],
            "signature": row["signature"], "summary": row["summary"],
            "href": f'definition/{row["id"]}.html',
        }
        for row in definitions
    )
    proof_edges = [
        {
            "kind": "proof_dependency",
            "source": edge["dependency"], "target": edge["dependent"],
            "body_reference": edge["body_reference"],
            "explicit_reference_count": edge["explicit_reference_count"],
        }
        for edge in explicit_graph["edges"]
    ]
    notation_edges: list[dict[str, Any]] = []
    for row in theorem_records:
        for definition_id, occurrences in row["defined"]["definition_uses"].items():
            notation_edges.append({
                "kind": "uses_definition", "source": row["tag"],
                "target": definition_id, "occurrence_count": occurrences,
                "statement_occurrences": row["defined"][
                    "statement_definition_uses"
                ].get(definition_id, 0),
                "local_proposition_occurrences": row["defined"][
                    "script_definition_uses"
                ].get(definition_id, 0),
            })
    for row in definitions:
        for definition_id in row["dependencies"]:
            if definition_id not in by_definition:
                raise DefinedEditionError(f"unknown definition graph target {definition_id}")
            notation_edges.append({
                "kind": "definition_uses_definition", "source": row["id"],
                "target": definition_id, "occurrence_count": 1,
            })
    notation_adjacency = {
        node["id"]: {"uses": [], "used_by": []}
        for node in nodes
    }
    for edge in notation_edges:
        notation_adjacency[edge["source"]]["uses"].append(edge["target"])
        notation_adjacency[edge["target"]]["used_by"].append(edge["source"])
    return {
        "schema": "peano-lab-pa-defined-graph-v1",
        "orientation": {
            "proof_dependency": "prerequisite_theorem_to_dependent_theorem",
            "uses_definition": "theorem_to_definition",
            "definition_uses_definition": "definition_to_referenced_definition",
        },
        "path_policy": "proof_dependency_edges_only",
        "edition_identity_sha256": identity_sha,
        "theorem_count": len(theorem_records),
        "definition_count": len(definitions),
        "proof_edge_count": len(proof_edges),
        "notation_edge_count": len(notation_edges),
        "nodes": nodes,
        "edges": [*proof_edges, *notation_edges],
        "proof_foundations": explicit_graph["foundations"],
        "proof_terminals": explicit_graph["terminals"],
        "proof_layers": explicit_graph["layers"],
        "proof_adjacency": explicit_graph["adjacency"],
        "notation_adjacency": notation_adjacency,
    }


def _graph_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:peano-lab:pa-defined-graph-v1",
        "title": "Peano Lab theorem and conservative-definition graph",
        "type": "object",
        "required": [
            "schema", "orientation", "path_policy", "edition_identity_sha256",
            "theorem_count", "definition_count", "proof_edge_count",
            "notation_edge_count", "nodes", "edges", "proof_foundations",
            "proof_terminals", "proof_layers", "proof_adjacency",
            "notation_adjacency",
        ],
        "properties": {
            "schema": {"const": "peano-lab-pa-defined-graph-v1"},
            "path_policy": {"const": "proof_dependency_edges_only"},
            "nodes": {"type": "array", "items": {"type": "object"}},
            "edges": {"type": "array", "items": {"type": "object"}},
        },
        "additionalProperties": True,
    }


def _render_index(theorems: Sequence[Mapping[str, Any]], definitions: Sequence[Mapping[str, Any]]) -> bytes:
    theorem_cards = "".join(
        f'<article class="pd-result" data-entry data-kind="theorem" data-search="{_e(" ".join((row["name"], row["tag"], row["summary"], row["defined"]["defined_statement"])).lower())}"><a href="tag/{_e(row["tag"])}.html"><code>{_e(row["tag"])}</code> · <strong>{_e(row["name"])}</strong></a><p>{_e(row["summary"])}</p><small>theorem · proof layer {row["layer"]} · {len(row["defined"]["definition_uses"])} definitions</small></article>'
        for row in theorems
    )
    definition_cards = "".join(
        f'<article class="pd-result pd-result-definition" data-entry data-kind="definition" data-search="{_e(" ".join((row["name"], row["id"], row["signature"], row["summary"])).lower())}"><a href="definition/{_e(row["id"])}.html"><code>{_e(row["id"])}</code> · <strong>{_e(row["name"])}</strong></a><p>{_e(row["summary"])}</p><small>conservative definition · not a theorem</small></article>'
        for row in definitions
    )
    body = f'''<header class="pd-header pd-hero"><nav><a href="../index.html">Exact explicit edition</a><a href="graph.html?target=PA00FW">Mixed dependency graph</a><a href="../../../arithmetic-library/defined-proof-explorer.html">Jupyter Book guide</a></nav><p class="pd-kicker">Parallel reading edition</p><h1>Native PA with defined notation</h1><p>Readable conservative notation is linked to exact expansions while the complete explicit tactic corpus remains visible.</p><div class="pd-stats"><b>{len(theorems)}</b> theorems · <b>{len(definitions)}</b> definitions</div></header><main data-defined-dashboard><section class="pd-controls"><label>Search <input data-search type="search"></label><label>Kind <select data-kind><option value="all">Theorems and definitions</option><option value="theorem">Theorems</option><option value="definition">Definitions</option></select></label><button data-clear type="button">Clear</button><output data-count>{len(theorems) + len(definitions)} entries</output></section><section class="pd-results">{definition_cards}{theorem_cards}</section></main>'''
    return _page("Native PA with defined notation", "index", body)


def _render_graph(graph: Mapping[str, Any]) -> bytes:
    inline = _javascript_assignment("PA_DEFINED_GRAPH", graph)
    body = f'''<header class="pd-header"><nav><a href="index.html">Defined edition</a><a href="../graph.html?target=PA00FW">Exact theorem graph</a><a href="../../../arithmetic-library/defined-proof-explorer.html">Jupyter Book guide</a></nav><p class="pd-kicker">Typed mixed graph</p><h1>Theorems and conservative definitions</h1><p>Proof arrows and notation arrows are intentionally different relations. Only theorem-proof arrows participate in premise paths.</p></header><main class="pd-graph-page" data-defined-graph><form class="pd-graph-controls" data-graph-form><label>Target theorem <input data-graph-target list="pd-graph-theorems" value="PA00FW" required></label><datalist id="pd-graph-theorems"></datalist><label>View <select data-graph-view><option value="critical">Critical theorem path</option><option value="prerequisites">Complete theorem prerequisite cone</option><option value="neighborhood">Direct theorem neighborhood</option><option value="corpus">Entire theorem corpus</option></select></label><label><input data-graph-definitions type="checkbox" checked> Include definition nodes</label><button type="submit">Draw</button></form><div class="pd-graph-layout"><section><div class="pd-graph-toolbar"><p data-graph-summary aria-live="polite">Loading graph…</p><div><button type="button" data-graph-zoom="in">+</button><button type="button" data-graph-zoom="out">−</button><button type="button" data-graph-fit>Fit</button></div></div><div class="pd-graph-stage"><svg data-graph-svg tabindex="0" role="group" aria-label="Mixed theorem and definition graph"><text x="20" y="35">Loading…</text></svg></div><div class="pd-legend"><span><i class="pd-legend-theorem"></i> theorem</span><span><i class="pd-legend-definition"></i> definition</span><span><i class="pd-legend-proof"></i> proof dependency</span><span><i class="pd-legend-notation"></i> uses definition</span></div></section><aside class="pd-graph-details"><p class="pd-kicker">Selected node</p><h2 data-graph-title>Loading…</h2><p data-graph-kind></p><p data-graph-description></p><dl data-graph-metadata></dl><p><a data-graph-open href="index.html">Open node →</a></p><h3>Outgoing relations</h3><ul data-graph-outgoing></ul><h3>Incoming relations</h3><ul data-graph-incoming></ul></aside></div><noscript><p class="pd-callout">The graph requires JavaScript. Every theorem and definition page remains available from the index.</p></noscript></main><script id="pa-defined-graph-data">{inline}</script>'''
    return _page("Theorems and definitions — Native PA", "graph", body)


def build_files(raw_edition: Mapping[str, Any] | None = None) -> tuple[dict[str, bytes], dict[str, Any]]:
    explicit_corpus = _json_object(EXPLICIT_CORPUS, "explicit proof corpus")
    explicit_graph = _json_object(EXPLICIT_GRAPH, "explicit theorem graph")
    explicit_records = _sequence(explicit_corpus.get("theorems"), "explicit corpus.theorems")
    edition = validate_edition(raw_edition or load_defined_edition(), explicit_records)
    edition_by_name = {row["name"]: row for row in edition["theorems"]}
    theorem_records: list[dict[str, Any]] = []
    for explicit in explicit_records:
        row = dict(explicit)
        row["defined"] = edition_by_name[row["name"]]
        theorem_records.append(row)
    if [row["tag"] for row in theorem_records] != [node["tag"] for node in explicit_graph["nodes"]]:
        raise DefinedEditionError("explicit corpus and graph theorem order disagree")

    definitions = edition["definitions"]
    definitions_by_id = {row["id"]: row for row in definitions}
    theorem_users: dict[str, list[dict[str, Any]]] = defaultdict(list)
    definition_users: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in theorem_records:
        for definition_id in row["defined"]["definition_uses"]:
            theorem_users[definition_id].append(row)
    for definition in definitions:
        for dependency in definition["dependencies"]:
            definition_users[dependency].append(definition)

    graph = _mixed_graph(theorem_records, definitions, explicit_graph, edition["identity_sha256"])
    corpus = {
        "schema": "peano-lab-pa-defined-corpus-v1",
        "edition_identity_sha256": edition["identity_sha256"],
        "explicit_corpus_sha256": _digest(EXPLICIT_CORPUS.read_bytes()),
        "theorem_count": len(theorem_records),
        "definition_count": len(definitions),
        "theorems": [
            {
                "tag": row["tag"], "name": row["name"], "scope": row["scope"],
                "status": row["status"], "layer": row["layer"],
                "summary": row["summary"], "defined": row["defined"],
                "explicit_statement": row["statement"],
                "explicit_statement_sha256": row["statement_sha256"],
                "dependencies": row["dependencies"], "dependents": row["dependents"],
            }
            for row in theorem_records
        ],
        "definitions": definitions,
    }
    files: dict[str, bytes] = {
        "index.html": _render_index(theorem_records, definitions),
        "graph.html": _render_graph(graph),
        "api/corpus.json": _json_bytes(corpus),
        "api/graph.json": _json_bytes(graph),
        "api/graph.schema.json": _json_bytes(_graph_schema()),
        **_pinned_assets(),
    }
    for index, row in enumerate(theorem_records):
        files[f'tag/{row["tag"]}.html'] = _render_theorem(
            row, definitions_by_id,
            theorem_records[index - 1] if index else None,
            theorem_records[index + 1] if index + 1 < len(theorem_records) else None,
        )
        target = f'../tag/{row["tag"]}.html'
        files[f'name/{row["name"]}.html'] = (
            f'<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}">'
            f'<link rel="canonical" href="{target}"><script>location.replace({json.dumps(target)}+location.search+location.hash)</script>'
            f'</head><body><a href="{target}">{_e(row["name"])}</a></body></html>\n'
        ).encode()
    for definition in definitions:
        files[f'definition/{definition["id"]}.html'] = _render_definition(
            definition, definitions_by_id,
            theorem_users[definition["id"]], definition_users[definition["id"]],
        )
    manifest_files = [
        {"path": path, "bytes": len(payload), "sha256": _digest(payload)}
        for path, payload in sorted(files.items())
    ]
    aggregate = _digest("\n".join(f'{row["path"]}\0{row["sha256"]}' for row in manifest_files))
    manifest = {
        "schema": "peano-lab-pa-defined-explorer-manifest-v1",
        "edition_identity_sha256": edition["identity_sha256"],
        "explicit_corpus_sha256": _digest(EXPLICIT_CORPUS.read_bytes()),
        "explicit_graph_sha256": _digest(EXPLICIT_GRAPH.read_bytes()),
        "theorem_count": len(theorem_records), "definition_count": len(definitions),
        "proof_edge_count": graph["proof_edge_count"],
        "notation_edge_count": graph["notation_edge_count"],
        "generated_file_count": len(files) + 1,
        "aggregate_sha256": aggregate,
        "required_assets": sorted(PINNED_ASSETS),
        "files": manifest_files,
    }
    files["manifest.json"] = _json_bytes(manifest)
    return files, manifest


def _safe_output(path: Path) -> Path:
    resolved = path.resolve(strict=False)
    if resolved in {REPO.resolve(), EXPLICIT.resolve(), REPO.parent.resolve()}:
        raise DefinedEditionError("refusing a broad defined-explorer output directory")
    return resolved


def _write(files: Mapping[str, bytes], output: Path) -> None:
    output = _safe_output(output)
    for relative, payload in files.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    expected = set(files)
    if output.is_dir():
        for path in output.rglob("*"):
            if path.is_file() and str(path.relative_to(output)) not in expected:
                path.unlink()


def _check(files: Mapping[str, bytes], output: Path) -> bool:
    output = _safe_output(output)
    drift = [
        relative for relative, payload in files.items()
        if not (output / relative).is_file() or (output / relative).read_bytes() != payload
    ]
    expected = set(files)
    if output.is_dir():
        drift.extend(
            str(path.relative_to(output)) for path in output.rglob("*")
            if path.is_file() and str(path.relative_to(output)) not in expected
        )
    if drift:
        print("defined PA explorer drift: " + ", ".join(sorted(set(drift))[:20]), file=sys.stderr)
        return False
    return True


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files have drifted")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="defined-edition output directory")
    args = parser.parse_args(argv)
    try:
        files, manifest = build_files()
        if args.check:
            if not _check(files, args.output):
                return 1
            print(
                f'verified defined PA explorer: {manifest["generated_file_count"]} files, '
                f'{manifest["aggregate_sha256"]}'
            )
            return 0
        _write(files, args.output)
    except DefinedEditionError as exc:
        print(f"defined PA explorer: {exc}", file=sys.stderr)
        return 2
    print(
        f'wrote defined PA explorer: {manifest["generated_file_count"]} files, '
        f'{manifest["aggregate_sha256"]}'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
