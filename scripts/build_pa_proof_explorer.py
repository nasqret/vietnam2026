#!/usr/bin/env python3
"""Generate the replay-free, Stacks-style native PA proof explorer.

The exact quadratic-reciprocity stack supplies immutable theorem data and a
topological admission order.  Its historical ``api/corpus.json`` is separately
bound by immutable Alpha catalogs: it is authenticated and preserved verbatim,
while current checked-use authority is published in ``api/current-corpus.json``.
This documentation builder never runs tactics, constructs certificates, changes
the public theorem registry, or replaces its immutable evidence corpus.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from dataclasses import fields
from hashlib import sha256
import html
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import quote


REPO = Path(__file__).resolve().parents[1]
PY_ROOT = REPO / "peano-lab" / "py"
sys.path.insert(0, str(PY_ROOT))

from peano_lab.kernel.checker import axiom_formula  # noqa: E402
from peano_lab.kernel.formulas import pretty_formula  # noqa: E402
from peano_lab.kernel import proofs as kernel_proofs  # noqa: E402
from peano_lab.library import editions_v16 as alpha_v16  # noqa: E402
from peano_lab.library import editions_v24 as current_alpha  # noqa: E402
from peano_lab.library.quadratic_reciprocity_stack_runtime import (  # noqa: E402
    quadratic_reciprocity_stack,
)
from peano_lab.ui.data_tactics import TACTIC_CARDS  # noqa: E402


OUTPUT = REPO / "book" / "_static" / "pa-proof-explorer"
CURRENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v24.json"
IMMUTABLE_EVIDENCE_CORPUS_PATH = "api/corpus.json"
CURRENT_CORPUS_PATH = "api/current-corpus.json"
IMMUTABLE_EVIDENCE_CORPUS_SHA256 = (
    "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"
)
IMMUTABLE_EVIDENCE_CORPUS_BYTES = 17_229_311
TAGS = REPO / "research" / "arithmetic-library" / "pa-proof-tags.json"
INFORMAL = REPO / "research" / "arithmetic-library" / "pa-proof-informal.json"
LIBRARY = PY_ROOT / "peano_lab" / "library"
GITHUB_ROOT = "https://github.com/nasqret/vietnam2026/blob/peano-lab"
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXY"
TAG_RE = re.compile(r"^PA[0-9A-Y]{4}$")
IDENT_RE = r"[A-Za-z_][A-Za-z0-9_']*"
PA_AXIOMS = {f"PA{i}" for i in range(1, 7)}
PINNED_UI_ASSETS = {
    "assets/explorer.css": "6dd0cf105c498dec70fe6a7fac04dcda397b40f947de677b36fc9c01962d84bc",
    "assets/explorer.js": "98f11fff5d34b5fa481c1dd6a6b39eef58fed28d00bb7d1f4ac7d1226b4d6606",
}
# Separate documentation surfaces own the conservative defined-notation
# reading edition and the private K3B CellHistory/ListAt microsite.  Keeping
# both subtrees outside this frozen explicit manifest preserves every explicit
# page and receipt byte-for-byte while allowing the three editions to share
# one stable static URL.  Neither reserved subtree enters the 557-node graph.
RESERVED_SUBTREES = {"defined", "k3b"}
CAMPAIGN_HTML_REVISION = sha256(CURRENT_CATALOG.read_bytes()).hexdigest()[:12]

EXPECTED = {
    "theorem_count": 557,
    "public_count": 241,
    "candidate_count": 316,
    "edge_count": 1787,
    "layer_count": 45,
    "formal_line_count": 27491,
    "explicit_dependency_reference_count": 8553,
    "graph_sha256": "26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253",
    "source_sha256": "23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1",
}
EXPECTED_ALPHA_EVIDENCE = {
    "alpha_edition_version": "v24",
    "alpha_edition_identity_sha256": (
        "1f4390b8ca5784ece54857fa666007f884b79e2670ef8bb32b2710c10f298a1b"
    ),
    "alpha_edition_checked_use_count": 2008,
    "proof_edition_version": "v16",
    "proof_edition_identity_sha256": (
        "3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10"
    ),
    "proof_edition_checked_use_count": 885,
    "graph_checked_use_count": 557,
    "graph_stable_closed_count": 241,
    "graph_alpha_closed_count": 316,
    "graph_newly_promoted_count": 315,
    "source_scope_policy": "historical_origin_not_current_release_authority",
}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _digest(value: bytes | str) -> str:
    return sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _immutable_evidence_corpus() -> bytes:
    """Authenticate the parent-catalog-bound corpus without ever replacing it."""

    path = OUTPUT / IMMUTABLE_EVIDENCE_CORPUS_PATH
    if not path.is_file():
        raise ValueError("missing immutable Alpha-parent quadratic-reciprocity corpus")
    payload = path.read_bytes()
    if (
        len(payload) != IMMUTABLE_EVIDENCE_CORPUS_BYTES
        or _digest(payload) != IMMUTABLE_EVIDENCE_CORPUS_SHA256
    ):
        raise ValueError("immutable Alpha-parent quadratic-reciprocity corpus changed")
    return payload


def _javascript_assignment(name: str, value: Any) -> str:
    """Return a deterministic assignment safe inside an HTML script element."""

    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
        raise ValueError(f"unsafe JavaScript data name: {name!r}")
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    # JSON is valid JavaScript here.  Escaping the three HTML-sensitive ASCII
    # characters prevents any theorem metadata from ending the script element
    # or becoming markup; ensure_ascii already protects U+2028 and U+2029.
    payload = (
        payload
        .replace("&", r"\u0026")
        .replace("<", r"\u003c")
        .replace(">", r"\u003e")
    )
    return f"window.{name}={payload};"


def _pinned_ui_assets() -> dict[str, bytes]:
    """Load hand-authored UI assets only when their reviewed bytes match."""

    files = {}
    for relative, expected_sha256 in PINNED_UI_ASSETS.items():
        path = OUTPUT / relative
        if not path.is_file():
            raise ValueError(f"missing PA proof explorer UI asset: {relative}")
        payload = path.read_bytes()
        actual_sha256 = _digest(payload)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"PA proof explorer UI asset drift for {relative}: "
                f"expected {expected_sha256}, found {actual_sha256}"
            )
        files[relative] = payload
    return files


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _base35(value: int) -> str:
    if not 0 <= value < 35**4:
        raise ValueError("PA proof-tag space exhausted")
    chars = []
    for _ in range(4):
        value, digit = divmod(value, 35)
        chars.append(ALPHABET[digit])
    return "".join(reversed(chars))


def _load_tags() -> dict[str, Any]:
    data = json.loads(TAGS.read_text(encoding="utf-8"))
    if data.get("schema") != "peano-lab-proof-tags-v1":
        raise ValueError("unknown PA proof-tag registry schema")
    assignments = data.get("assignments")
    if not isinstance(assignments, dict):
        raise ValueError("proof-tag assignments must be an object")
    values = list(assignments.values())
    if any(not isinstance(name, str) or not TAG_RE.fullmatch(tag or "") for name, tag in assignments.items()):
        raise ValueError("invalid theorem name or PA proof tag")
    if len(values) != len(set(values)):
        raise ValueError("PA proof tags must be unique")
    if data.get("alphabet") != ALPHABET or data.get("tag_pattern") != "PA[0-9A-Y]{4}":
        raise ValueError("PA proof-tag format changed")
    if type(data.get("next_value")) is not int or data["next_value"] < 1:
        raise ValueError("invalid PA proof-tag allocation cursor")
    exposed = data.get("tags")
    if exposed is not None and exposed != assignments:
        raise ValueError("exposed PA proof tags disagree with assignments")
    return data


def _update_tags(names: list[str]) -> dict[str, Any]:
    data = _load_tags()
    assignments = data["assignments"]
    used = set(assignments.values())
    cursor = data["next_value"]
    for name in names:
        if name in assignments:
            continue
        while f"PA{_base35(cursor)}" in used:
            cursor += 1
        tag = f"PA{_base35(cursor)}"
        assignments[name] = tag
        used.add(tag)
        cursor += 1
    data["next_value"] = cursor
    data["tags"] = dict(assignments)
    TAGS.write_bytes(_json_bytes(data))
    return data


def _command_spans(command: str, dependencies: set[str]) -> tuple[str, list[dict[str, Any]]]:
    match = re.match(rf"\s*({IDENT_RE})", command)
    if match is None:
        raise ValueError(f"cannot parse tactic command {command!r}")
    tactic = match.group(1)
    start = match.end()
    args = command[start:]
    spans: list[tuple[int, int]] = []
    if tactic in {"apply", "exact", "cases"}:
        found = re.fullmatch(rf"\s*({IDENT_RE})\s*", args)
        if found:
            spans.append((start + found.start(1), start + found.end(1)))
    elif tactic in {"specialize", "forall_elim"}:
        found = re.match(rf"\s*({IDENT_RE})(?:\s|$)", args)
        if found:
            spans.append((start + found.start(1), start + found.end(1)))
    elif tactic == "rewrite":
        found = re.match(rf"\s*(?:(?:<-|←)\s*)?({IDENT_RE})(?:\s|$)", args)
        if found:
            spans.append((start + found.start(1), start + found.end(1)))
    elif tactic == "simp":
        stripped = args.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            offset = start + args.index("[") + 1
            body = stripped[1:-1]
            for found in re.finditer(IDENT_RE, body):
                spans.append((offset + found.start(), offset + found.end()))
    elif tactic == "use":
        found = re.match(rf"\s*({IDENT_RE})(?:\s|$)", args)
        if found:
            spans.append((start + found.start(1), start + found.end(1)))
    references = []
    for left, right in spans:
        name = command[left:right]
        kind = "theorem" if name in dependencies else "axiom" if name in PA_AXIOMS else None
        if kind:
            references.append({"kind": kind, "name": name, "start": left, "end": right})
    return tactic, references


def _literal_locations() -> dict[str, list[tuple[str, int]]]:
    found: dict[str, list[tuple[str, int]]] = defaultdict(list)
    paths = [LIBRARY / "theorems.py"] + sorted(
        path for path in LIBRARY.glob("*.py") if path.name != "theorems.py"
    )
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        calls = sorted((node for node in ast.walk(tree) if isinstance(node, ast.Call)), key=lambda node: node.lineno)
        for node in calls:
            if not isinstance(node.func, ast.Name) or node.func.id not in {"spec", "TheoremSpec"}:
                continue
            value = node.args[0] if node.args else next((item.value for item in node.keywords if item.arg == "name"), None)
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                relative = str(path.relative_to(REPO))
                found[value.value].append((relative, node.lineno))
    return found


def _source_record(name: str, scope: str, stack: Any, locations: dict[str, list[tuple[str, int]]]) -> dict[str, Any]:
    choices = locations.get(name, [])
    owner = stack.owner_by_name.get(name) if scope == "candidate" else None
    if owner:
        owned = [row for row in choices if Path(row[0]).stem == owner]
        choices = owned or choices
    if choices:
        path, line = choices[0]
        kind = "declaration"
    else:
        entry = next(item for item in stack.source_rows if item[0] == owner)
        path = f"peano-lab/py/peano_lab/library/{owner}.py"
        line = next(item.builder.__code__.co_firstlineno for item in __import__(
            "peano_lab.library.quadratic_reciprocity_stack", fromlist=["QR_CANDIDATE_FACTORY_MANIFEST"]
        ).QR_CANDIDATE_FACTORY_MANIFEST if item.module_name == owner)
        kind = "generated_factory"
    payload = (REPO / path).read_bytes()
    return {
        "path": path,
        "line": line,
        "kind": kind,
        "owner_module": owner,
        "sha256": _digest(payload),
        "href": f"{GITHUB_ROOT}/{path}#L{line}",
    }


def _shape_guide(spec: Any, counts: Counter[str]) -> dict[str, Any]:
    if spec.dependencies:
        opening = "Use the direct prerequisites " + ", ".join(spec.dependencies) + " as previously established PA formulas."
    else:
        opening = "This root lemma is proved directly from the PA rules and the hypotheses introduced by its statement."
    moves = []
    for tactic, label in (("induction", "structural induction"), ("cases", "case analysis"), ("have", "intermediate claims"), ("rewrite", "equality transport"), ("simp", "certified simplification"), ("norm_num", "closed numeral normalization")):
        if counts[tactic]:
            moves.append(f"{label} ({counts[tactic]})")
    middle = "The proof proceeds by " + (", ".join(moves) if moves else "direct introduction and elimination") + "."
    return {
        "kind": "generated_structural_guide",
        "review": "generated",
        "title": "Structural proof guide",
        "paragraphs": [spec.summary, opening, middle],
        "reference_names": list(spec.dependencies),
    }


def _render_command(line: dict[str, Any]) -> str:
    text = line["text"]
    pieces = []
    tactic_end = len(line["tactic"])
    spans = [(0, tactic_end, "tactic", line["tactic"], None)] + [
        (ref["start"], ref["end"], ref["kind"], ref["name"], ref)
        for ref in line["references"] + line.get("axiom_references", [])
    ]
    cursor = 0
    for left, right, kind, name, reference in sorted(spans, key=lambda row: (row[0], row[1])):
        if left < cursor:
            continue
        pieces.append(_e(text[cursor:left]))
        if kind == "tactic":
            pieces.append(f'<a class="pa-tactic-ref" href="../foundations.html#tactic-{_e(name)}">{_e(name)}</a>')
        elif kind == "theorem":
            assert reference is not None
            pieces.append(f'<a class="pa-theorem-ref" href="{_e(reference["href"])}">{_e(name)}</a>')
        else:
            pieces.append(f'<a class="pa-axiom-ref" href="../foundations.html#axiom-{_e(name).lower()}">{_e(name)}</a>')
        cursor = right
    pieces.append(_e(text[cursor:]))
    return "".join(pieces)


def _page(title: str, page: str, body: str, asset_prefix: str = "") -> bytes:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)}</title><link rel="stylesheet" href="{asset_prefix}assets/explorer.css"><script defer src="{asset_prefix}assets/explorer.js"></script></head>
<body class="pa-proof-site" data-page="{page}">{body}</body></html>
""".encode()


def _campaign_navigation(prefix: str) -> str:
    """Link the immutable local proof presentation to its broader research atlas."""

    return (
        f'<a href="{prefix}grand-campaign/?v={CAMPAIGN_HTML_REVISION}">'
        "Grand campaign</a>"
        f'<a href="{prefix}grand-campaign/?view=domain&amp;focus=D02'
        f'&amp;v={CAMPAIGN_HTML_REVISION}">Research domain</a>'
        f'<a href="{prefix}grand-campaign/?view=family&amp;focus=F05'
        f'&amp;v={CAMPAIGN_HTML_REVISION}">Reciprocity family</a>'
        f'<a href="{prefix}grand-campaign/?view=goal&amp;focus=G043'
        f'&amp;v={CAMPAIGN_HTML_REVISION}">Campaign milestone</a>'
    )


def _render_index(records: list[dict[str, Any]], stack: Any) -> bytes:
    layers = "".join(f'<option value="{n}">Layer {n}</option>' for n in range(EXPECTED["layer_count"]))
    cards = []
    for row in records:
        search = " ".join((row["name"], row["tag"], row["summary"], row["status"], *[item["name"] for item in row["dependencies"]])).lower()
        cards.append(f'''<article class="pa-proof-result pa-status-{row["scope"]}" data-pa-theorem data-name="{_e(row["name"])}" data-tag="{row["tag"]}" data-status="{row["scope"]}" data-layer="{row["layer"]}" data-search="{_e(search)}"><a href="tag/{row["tag"]}.html"><code>{row["tag"]}</code> · <strong>{_e(row["name"])}</strong></a><p>{_e(row["summary"])}</p><small>layer {row["layer"]} · {len(row["lines"])} lines · {row["status_label"]}</small></article>''')
    atlas = _campaign_navigation("../../")
    body = f'''<header class="pa-proof-header pa-hero"><p><a href="../../arithmetic-library/quadratic-reciprocity.html">Jupyter Book</a></p><h1>Native PA Proof Explorer</h1><p>The complete replay-free reading surface for the exact quadratic-reciprocity dependency closure.</p><div class="pa-proof-stats"><b>557</b> checked-use theorems · <b>1,787</b> edges · <b>27,491</b> tactic lines · <b>45</b> layers</div><p>Current Alpha v24 independently verifies all 557 graph theorems among 2008 checked release theorems: 241 Stable and 316 Alpha-only. The historical Alpha-v16 proof-bearing release and the original 241/316 source partition remain immutable; Alpha-only closure does not grant Stable membership.</p><nav><a href="foundations.html">PA language, axioms, and rules</a><a href="defined/index.html?v={CAMPAIGN_HTML_REVISION}">Definition-aware edition</a><a href="graph.html?target=PA00FW&amp;view=prerequisites&amp;edges=focus&amp;v={CAMPAIGN_HTML_REVISION}">Complete proof graph</a>{atlas}</nav></header>
<main data-proof-dashboard data-pa-explorer-index><section class="pa-proof-controls"><label>Search <input data-proof-search data-pa-search type="search"></label><label>Source origin <select data-proof-status data-pa-status><option value="all">All</option><option value="public">Stable source (241)</option><option value="candidate">Alpha-only candidate-factory source (316)</option></select></label><label>Layer <select data-proof-layer data-pa-layer><option value="all">All 45 layers</option>{layers}</select></label><button data-proof-clear data-pa-clear type="button">Clear</button><output data-proof-count data-pa-count>557 checked-use theorems</output></section><section class="pa-layer-map">{''.join(f'<a href="?layer={n}">{n}</a>' for n in range(45))}</section><section class="pa-proof-results">{"".join(cards)}</section></main>'''
    return _page("Native PA Proof Explorer", "index", body)


def _render_foundations(tactics: list[str]) -> bytes:
    """Explain the complete checked language, not merely list corpus tokens.

    The explorer is published both inside the Jupyter Book and independently
    under ``/proofs/``.  Site-root book links are consequently intentional:
    relative ``../../peano`` links worked only in the former deployment.
    """

    def book(chapter: str, fragment: str = "") -> str:
        suffix = f"#{fragment}" if fragment else ""
        return f"/vietnam2026/book/{chapter}.html{suffix}"

    def tactic_slug(name: str) -> str:
        return {";": "then", "<|>": "orelse"}.get(name, name)

    constructor_guide: dict[str, tuple[str, str, str, tuple[str, ...]]] = {
        "Hyp": (
            "Use a hypothesis already present in the current logical context.",
            "Γ, A ⊢ A",
            "Index zero selects the newest assumption; the checker rejects missing or malformed context indices.",
            ("exact", "assumption"),
        ),
        "ImpIntro": (
            "Introduce an implication by proving its conclusion under a fresh assumption.",
            "Γ, A ⊢ B  ⇒  Γ ⊢ A → B",
            "The checker extends the context with the exact antecedent before it checks the body.",
            ("intro",),
        ),
        "ImpElim": (
            "Apply an established implication to an independently checked proof of its premise.",
            "Γ ⊢ A → B; Γ ⊢ A  ⇒  Γ ⊢ B",
            "This is ordinary modus ponens; both the function and its argument must match exactly.",
            ("apply", "specialize"),
        ),
        "Cut": (
            "Share a checked intermediate lemma with a continuation that may reuse it.",
            "Γ ⊢ A; Γ, A ⊢ B  ⇒  Γ ⊢ B",
            "The checker validates both branches. Cut is proof sharing, not a theorem oracle or another arithmetic axiom.",
            ("use",),
        ),
        "AndIntro": (
            "Establish a conjunction by constructing proofs of both component propositions.",
            "Γ ⊢ A; Γ ⊢ B  ⇒  Γ ⊢ A ∧ B",
            "Its left and right certificate branches are checked separately against the corresponding conjuncts.",
            ("split",),
        ),
        "AndElimL": (
            "Project the left component from a proof of a conjunction.",
            "Γ ⊢ A ∧ B  ⇒  Γ ⊢ A",
            "The source must synthesize a genuine conjunction; no assumption about its right field is discarded unsafely.",
            ("cases",),
        ),
        "AndElimR": (
            "Project the right component from a proof of a conjunction.",
            "Γ ⊢ A ∧ B  ⇒  Γ ⊢ B",
            "The checker first identifies both conjuncts and returns exactly the independently established right component.",
            ("cases",),
        ),
        "OrIntroL": (
            "Prove a disjunction by supplying a proof of its left alternative.",
            "Γ ⊢ A  ⇒  Γ ⊢ A ∨ B",
            "The expected target supplies the unchosen right alternative; no proof of that alternative is claimed.",
            ("left",),
        ),
        "OrIntroR": (
            "Prove a disjunction by supplying a proof of its right alternative.",
            "Γ ⊢ B  ⇒  Γ ⊢ A ∨ B",
            "The expected target supplies the unchosen left alternative; the chosen branch must still be checked.",
            ("right",),
        ),
        "OrElim": (
            "Reason by cases on a proved disjunction, establishing the same conclusion in both cases.",
            "Γ ⊢ A ∨ B; Γ, A ⊢ C; Γ, B ⊢ C  ⇒  Γ ⊢ C",
            "Both branches receive their own precise hypothesis and must prove the identical original conclusion.",
            ("cases",),
        ),
        "BotElim": (
            "Derive any specified conclusion from an independently checked proof of contradiction.",
            "Γ ⊢ ⊥  ⇒  Γ ⊢ A",
            "Explosion is constructive logic: it consumes real evidence of bottom and never manufactures the contradiction.",
            ("exfalso", "cases"),
        ),
        "ForallIntro": (
            "Prove a universal statement using an arbitrary fresh rigid term variable.",
            "Γ ⊢ P(x fresh)  ⇒  Γ ⊢ ∀x. P(x)",
            "The context is shifted beneath the binder so the introduced eigenvariable cannot capture an outer variable.",
            ("intro", "induction"),
        ),
        "ForallElim": (
            "Instantiate a proved universal formula at one well-scoped arithmetic term.",
            "Γ ⊢ ∀x. P(x)  ⇒  Γ ⊢ P(t)",
            "Capture-avoiding substitution replaces the quantified slot with the supplied term before comparison.",
            ("specialize", "forall_elim", "apply"),
        ),
        "ExistsIntro": (
            "Prove existence by exhibiting a concrete witness and checking its required property.",
            "Γ ⊢ P(t)  ⇒  Γ ⊢ ∃x. P(x)",
            "The certificate stores both the witness term and the proof of the exactly substituted body.",
            ("exists",),
        ),
        "ExistsElim": (
            "Open an existential hypothesis using a fresh witness that cannot escape into the conclusion.",
            "Γ ⊢ ∃x. P(x); Γ, P(w fresh) ⊢ C  ⇒  Γ ⊢ C",
            "The checker lifts the surrounding context and the target, preventing the private witness from leaking.",
            ("cases",),
        ),
        "EqRefl": (
            "Certify that a well-formed arithmetic term is equal to itself.",
            "Γ ⊢ t = t",
            "The checker constructs exactly the reflexive equation for the stored rigid kernel term.",
            ("refl", "simp"),
        ),
        "EqSym": (
            "Reverse the direction of an already checked equality proof.",
            "Γ ⊢ s = t  ⇒  Γ ⊢ t = s",
            "Only a certificate that actually synthesizes an equality can be reversed by this constructor.",
            ("symm", "rewrite"),
        ),
        "EqTrans": (
            "Compose two checked equality proofs through exactly the same intermediate term.",
            "Γ ⊢ r = s; Γ ⊢ s = t  ⇒  Γ ⊢ r = t",
            "The middle expressions must agree syntactically after legitimate substitution; unrelated chains are rejected.",
            ("trans",),
        ),
        "CongS": (
            "Lift an equality through the successor constructor on both sides.",
            "Γ ⊢ s = t  ⇒  Γ ⊢ S(s) = S(t)",
            "This is structural congruence for the sole unary arithmetic function in the native language.",
            ("congr", "norm_num"),
        ),
        "CongAdd": (
            "Lift two component equalities through the binary addition constructor.",
            "Γ ⊢ a = c; Γ ⊢ b = d  ⇒  Γ ⊢ a + b = c + d",
            "Both argument certificates are checked; addition congruence does not assume commutativity or associativity.",
            ("congr", "norm_num"),
        ),
        "CongMul": (
            "Lift two component equalities through the binary multiplication constructor.",
            "Γ ⊢ a = c; Γ ⊢ b = d  ⇒  Γ ⊢ a · b = c · d",
            "Both factor equalities need evidence; multiplication laws remain separate theorems or arithmetic axioms.",
            ("congr", "norm_num"),
        ),
        "EqSubst": (
            "Transport a proved formula along an equality using an explicit one-variable motive.",
            "Γ ⊢ s = t; Γ ⊢ P(s)  ⇒  Γ ⊢ P(t)",
            "The stored Leibniz motive uses a distinguished de Bruijn slot; both substitutions are capture-avoiding.",
            ("rewrite", "simp"),
        ),
        "DNE": (
            "State double-negation elimination for one concrete proposition in explicitly classical mode.",
            "Γ ⊢ ((A → ⊥) → ⊥) → A   [classical only]",
            "The ordinary constructive checker rejects every DNE node; only owner-authorized classical checking accepts it.",
            ("apply",),
        ),
        "Axiom": (
            "Introduce exactly one of the six fixed arithmetic axiom schemas PA1 through PA6.",
            "Γ ⊢ PAi   where i ∈ {1, 2, 3, 4, 5, 6}",
            "The checker reconstructs the precise named schema and rejects arbitrary theorem names or fabricated formulas.",
            ("apply", "rewrite", "simp"),
        ),
        "Ind": (
            "Prove a concrete first-order induction instance from its zero and successor cases.",
            "Γ ⊢ P(0); Γ ⊢ ∀n. P(n) → P(S n)  ⇒  Γ ⊢ ∀n. P(n)",
            "The motive is an actual stored formula, never a predicate variable, a blanket axiom, or an unchecked induction oracle.",
            ("induction",),
        ),
    }
    constructor_names = tuple(name for name in kernel_proofs.__all__ if name != "Proof")
    if set(constructor_names) != set(constructor_guide):
        raise ValueError("foundations guide does not cover the exact native kernel constructors")

    cards_by_name = {card.name: card for card in TACTIC_CARDS}
    if len(cards_by_name) != len(TACTIC_CARDS):
        raise ValueError("native tactic encyclopedia contains duplicate cards")
    used_tactics = set(tactics)
    if unknown := sorted(used_tactics - set(cards_by_name)):
        raise ValueError(f"foundations guide is missing corpus tactic cards: {unknown!r}")

    axiom_roles = {
        "PA1": "Zero is not the successor of any natural number.",
        "PA2": "Equal successors have equal predecessors; successor is injective.",
        "PA3": "Adding zero on the right leaves a number unchanged.",
        "PA4": "Addition recurses on its right-hand successor argument.",
        "PA5": "Multiplying by zero on the right produces zero.",
        "PA6": "Multiplication recurses on its right-hand successor argument.",
    }
    axioms = []
    for name in sorted(PA_AXIOMS):
        formula = axiom_formula(name)
        axioms.append(
            f'<article id="axiom-{name.lower()}"><h3><code>{name}</code> · '
            f'{_e(axiom_roles[name])}</h3>'
            f'<pre><code>{_e(pretty_formula(formula, []))}</code></pre>'
            f'<p><a href="{book("peano/axioms-and-rules", "the-six-arithmetic-axioms")}">'
            "Read the arithmetic-axiom explanation in the book</a></p></article>"
        )

    constructor_groups = (
        ("Context, implication, and checked sharing", ("Hyp", "ImpIntro", "ImpElim", "Cut")),
        ("Conjunction", ("AndIntro", "AndElimL", "AndElimR")),
        ("Disjunction and contradiction", ("OrIntroL", "OrIntroR", "OrElim", "BotElim")),
        ("Quantifiers and explicit witnesses", ("ForallIntro", "ForallElim", "ExistsIntro", "ExistsElim")),
        ("Equality, congruence, and transport", ("EqRefl", "EqSym", "EqTrans", "CongS", "CongAdd", "CongMul", "EqSubst")),
        ("Arithmetic, induction, and explicit classicality", ("Axiom", "Ind", "DNE")),
    )
    if tuple(sorted(name for _, names in constructor_groups for name in names)) != tuple(sorted(constructor_names)):
        raise ValueError("foundations guide must classify every kernel constructor exactly once")

    constructor_sections = []
    for heading, names in constructor_groups:
        entries = []
        for name in names:
            summary, rule, explanation, related = constructor_guide[name]
            signature = f'{name}({", ".join(field.name for field in fields(getattr(kernel_proofs, name)))})'
            if name == "Cut":
                chapter = book("arithmetic-library/proof-sharing", "the-rule")
            elif name == "Ind":
                chapter = book("peano/axioms-and-rules", "induction-is-a-rule-not-pa7")
            elif name == "DNE":
                chapter = book("peano/axioms-and-rules", "constructive-default-and-classical-extension")
            elif name == "Axiom":
                chapter = book("peano/axioms-and-rules", "the-six-arithmetic-axioms")
            else:
                chapter = book("peano/axioms-and-rules", "logical-and-equality-rules")
            tactic_links = " · ".join(
                f'<a href="#tactic-{_e(tactic_slug(tactic))}"><code>{_e(tactic)}</code></a>'
                for tactic in related
            )
            entries.append(
                f'<article id="constructor-{name.lower()}" data-constructor="{_e(name)}">'
                f'<h4><code>{_e(signature)}</code></h4><p>{_e(summary)}</p>'
                f'<pre><code>{_e(rule)}</code></pre><p>{_e(explanation)}</p>'
                f'<p><a href="{chapter}">Read the corresponding proof rule</a>'
                f' · Related commands: {tactic_links}</p></article>'
            )
        constructor_sections.append(f'<section><h3>{_e(heading)}</h3>{"".join(entries)}</section>')

    def card_chapter(card: Any) -> tuple[str, str]:
        if card.kind == "tactical":
            fragment = "focus-follows-holes-not-list-positions" if card.name == "focus" else "six-combinators-six-precise-meanings"
            return book("peano/tacticals", fragment), "How tactical composition works"
        if card.name == "auto":
            return book("peano/tacticals", "auto-is-bounded-search-followed-by-replay"), "Bounded proof search and replay"
        if card.name == "compact_arith":
            return book("peano/compact-arith", "the-surface-contract"), "The compact arithmetic contract"
        if card.name in {"norm_num", "ring", "hint"}:
            return book("peano/arithmetic-automation", "four-tools-four-contracts"), "Checked arithmetic and advisory automation"
        if card.name in {"have", "suffices"}:
            return book("peano/tactics", "local-lemmas-schedule-one-cut-in-two-useful-orders"), "How local intermediate facts compile"
        if card.name in {"rewrite", "simp"}:
            return book("peano/tactics", "rewrite-produces-transport-evidence"), "Equality transport and simplification"
        if card.name in {"exists", "trans"}:
            return book("peano/tactics", "holes-are-not-metavariables"), "Witnesses and scoped metavariables"
        if card.name == "induction":
            return book("peano/induction-ladder", "induction-is-a-schema-not-a-magic-command"), "Concrete first-order induction motives"
        if card.name == "undo":
            return book("peano/tactics", "immutability-makes-failure-transactional"), "Transactional states and undo"
        if card.name == "use":
            return book("arithmetic-library/proof-sharing", "why-this-is-not-a-theorem-oracle"), "Checked theorem reuse, without a theorem oracle"
        return book("peano/tactics", "a-state-is-goals-plus-a-proof-with-matching-holes"), "Goals, holes, and proof constructors"

    cards_by_kind: dict[str, list[str]] = {"primitive": [], "tactical": [], "automation": []}
    for card in TACTIC_CARDS:
        if card.kind not in cards_by_kind:
            raise ValueError(f"unknown tactic-card kind: {card.kind!r}")
        slug = tactic_slug(card.name)
        if not re.fullmatch(r"[a-z][a-z0-9_]*", slug):
            raise ValueError(f"unsafe tactic-card anchor: {card.name!r}")
        chapter, chapter_label = card_chapter(card)
        in_corpus = card.name in used_tactics
        corpus_label = "Used in the quadratic-reciprocity proof corpus" if in_corpus else "Available in Peano Lab; not used in this proof slice"
        replay = "\n".join((f"pa prove {card.example_theorem}", *card.example_commands, "qed"))
        failures = "".join(f"<li>{_e(error)}</li>" for error in card.common_errors)
        card_name = quote(card.name, safe="")
        cards_by_kind[card.kind].append(
            f'<article id="tactic-{_e(slug)}" data-tactic="{_e(card.name)}" '
            f'data-tactic-kind="{_e(card.kind)}" data-corpus-used="{str(in_corpus).lower()}">'
            f'<h3><code>{_e(card.name)}</code> · {_e(card.summary)}</h3>'
            f'<p><strong>{_e(corpus_label)}</strong></p>'
            f'<p><strong>Syntax:</strong> <code>{_e(card.syntax)}</code></p>'
            f'<p><strong>Goal effect:</strong> {_e(card.goal_effect)}</p>'
            f'<p><strong>Kernel evidence:</strong> {_e(card.certificate_effect)}</p>'
            f'<p><strong>Complete executable example:</strong></p>'
            f'<pre><code>{_e(replay)}</code></pre>'
            f'<details><summary>Common mistakes and failure modes</summary><ul>{failures}</ul></details>'
            f'<p><a href="{chapter}">{_e(chapter_label)}</a> · '
            f'<a href="/peano-lab/?cmd=pa%20tactic%20{card_name}">'
            "Open this interactive tactic card</a></p></article>"
        )

    corpus_links = " · ".join(
        f'<a href="#tactic-{_e(tactic_slug(name))}"><code>{_e(name)}</code></a>'
        for name in sorted(used_tactics)
    )
    atlas = _campaign_navigation("../../")
    body = f'''<header class="pa-proof-header pa-foundations-heading">
<nav aria-label="Proof Explorer and research atlas"><a href="index.html">← Proof Explorer</a><a href="defined/index.html">Definition-aware explorer</a><a href="graph.html?target=PA00FW&amp;view=prerequisites&amp;edges=focus">Complete proof graph</a>{atlas}</nav>
<h1>Native PA foundations</h1>
<p>A complete reader’s guide to the first-order arithmetic language, its six arithmetic axioms, every independently checked proof constructor, and every executable Peano Lab proof command.</p>
<p><strong>{len(PA_AXIOMS)} arithmetic axioms</strong> · <strong>{len(constructor_names)} kernel proof constructors</strong> · <strong>{len(TACTIC_CARDS)} documented commands</strong> · <strong>{len(used_tactics)} commands used by this 557-theorem proof corpus</strong></p>
<nav aria-label="Foundations page sections"><a href="#trust-boundary">Trust boundary</a><a href="#grammar-terms">Language</a><a href="#arithmetic-axioms">Arithmetic axioms</a><a href="#proof-constructors">All proof constructors</a><a href="#primitive-tactics">Primitive tactics</a><a href="#tactical-combinators">Tacticals</a><a href="#checked-automation">Automation</a><a href="#worked-proof">Worked proof</a><a href="#reading-guide">Continue reading</a></nav>
</header><main>
<section class="pa-foundation-card" id="trust-boundary"><h2>First, what is actually trusted?</h2><p>A proof script is a human-readable recipe, not proof authority. Tactics, search, simplification, theorem names, dashboards, and generated explanations are <strong>untrusted proof builders</strong>. They propose an explicit certificate. The small independent kernel accepts a theorem only after checking that certificate against the exact original formula in the empty context.</p><pre><code>native statement + tactic script + checked prerequisites
                    ↓ untrusted proof construction
               explicit proof certificate
                    ↓ independent kernel checker
             original theorem accepted — QED</code></pre><p><strong>Constructive by default.</strong> The quadratic-reciprocity corpus does not gain classical reasoning from a dashboard or a tactic. Double-negation elimination requires an explicitly authorized classical session and leaves a visible <a href="#constructor-dne"><code>DNE</code> certificate</a>. A checked <a href="#constructor-cut"><code>Cut</code></a> shares evidence but adds no arithmetic assumption.</p><p><a href="{book("peano/kernel", "certificates-are-data-not-authority")}">Why certificates are data, not authority</a> · <a href="{book("arithmetic-library/language-and-trust", "the-trust-path")}">Follow the complete library trust path</a> · <a href="{book("peano/axioms-and-rules", "constructive-default-and-classical-extension")}">Constructive versus explicitly classical checking</a></p></section>

<section class="pa-foundation-card" id="grammar-terms"><h2>Terms: the complete arithmetic vocabulary</h2><pre><code>t ::= x | 0 | S(t) | t + u | t * u</code></pre><p>The kernel understands variables, zero, successor, addition, and multiplication—nothing else. A numeral such as <code>3</code> is convenient notation for <code>S(S(S(0)))</code>. Bound names become de Bruijn indices, so renaming a bound variable cannot change its mathematical meaning.</p><p>There are no primitive division, remainder, subtraction, exponentiation, lists, sets, primes, or residue symbols. Bigger mathematics is encoded using this same small term language.</p><p><a href="{book("peano/language-reference", "terms")}">Read the complete term grammar and parser conventions</a> · <a href="{book("peano/kernel", "two-de-bruijn-ideas-both-about-trust")}">Understand de Bruijn indices and capture avoidance</a></p></section>

<section class="pa-foundation-card" id="grammar-formulas"><h2>Formulas: first-order logic with equality</h2><pre><code>A ::= t = u | false | A -&gt; B | A /\\ B | A \\/ B
    | forall x. A | exists x. A</code></pre><p>These forms mean equality, contradiction, implication, conjunction, disjunction, universal quantification, and existential quantification. Negation is the conservative abbreviation <code>~A := A -&gt; false</code>, not an additional kernel constructor.</p><p>Familiar number-theoretic notation is relational shorthand: <code>a ≤ b</code> expands to <code>exists k. b = a + k</code>; <code>a &lt; b</code> expands to <code>exists k. b = a + S k</code>; and divisibility expands to <code>exists k. b = a * k</code>. Every definition-aware theorem ultimately expands back to this exact grammar.</p><p><a href="{book("peano/language-reference", "formulas")}">Full formula grammar</a> · <a href="{book("peano/language-reference", "conservative-mathematical-relations")}">How order, divisibility, residues, and finite objects expand</a> · <a href="{book("arithmetic-library/language-and-trust", "conservative-definitions")}">Why mathematical definitions add no kernel axioms</a> · <a href="defined/index.html">Open the linked definition-aware edition</a></p></section>

<section class="pa-foundation-card" id="arithmetic-axioms"><h2>Arithmetic axioms PA1–PA6</h2><p>These are the only named arithmetic axiom constants. Notice that both addition and multiplication recurse on their <strong>right</strong> argument: <code>n + 0 = n</code> follows immediately from PA3, whereas <code>0 + n = n</code> needs induction.</p>{''.join(axioms)}<article id="proof-induction"><h3>Induction is a checked proof rule, not “PA7”</h3><pre><code>P(0),  forall n. P(n) -&gt; P(S n)
────────────────────────────────
         forall n. P(n)</code></pre><p>Each <a href="#constructor-ind"><code>Ind</code> constructor</a> stores one concrete first-order motive and separate base and successor proofs. The kernel checks both; there is no object-language predicate variable and no unrestricted induction oracle.</p><p><a href="{book("peano/axioms-and-rules", "induction-is-a-rule-not-pa7")}">Induction is a rule, not PA7</a> · <a href="{book("peano/induction-ladder", "induction-is-a-schema-not-a-magic-command")}">See induction build the arithmetic ladder</a></p></article><article id="proof-cut"><h3>Cut shares checked evidence; it is not an arithmetic axiom</h3><p>The <a href="#constructor-cut"><code>Cut</code> constructor</a> checks an intermediate proposition and then checks its use in a continuation. Local <a href="#tactic-have"><code>have</code></a> and <a href="#tactic-suffices"><code>suffices</code></a> first use administrative engine-only forms that are compiled away before final checking; they are not extra kernel constructors.</p><p><a href="{book("arithmetic-library/proof-sharing", "the-rule")}">Understand checked proof sharing</a> · <a href="{book("arithmetic-library/proof-sharing", "local-reasoning-remains-administrative")}">Why local reasoning remains administrative</a></p></article><article id="proof-dne"><h3>DNE is explicitly classical, never silently constructive</h3><p><code>((A -&gt; false) -&gt; false) -&gt; A</code> is represented only by an explicit <a href="#constructor-dne"><code>DNE</code></a> node. The ordinary constructive checker rejects it. An owner must separately authorize classical mode; it is not proof authority for this quadratic-reciprocity stack.</p><p><a href="{book("peano/axioms-and-rules", "constructive-default-and-classical-extension")}">Read the exact constructive/classical boundary</a></p></article></section>

<section class="pa-foundation-card" id="proof-constructors"><h2>All {len(constructor_names)} native proof constructors</h2><p>These are the <strong>complete, exact proof-certificate constructors accepted by the kernel</strong>, grouped by their mathematical rule. Signatures are generated from the actual frozen proof dataclasses; the displayed sequent explains what each constructor has to establish. Neither a tactic nor an engine-only administrative node appears in this inventory.</p>{''.join(constructor_sections)}<p><a href="{book("peano/kernel", "certificates-are-data-not-authority")}">How the checker interprets inert proof data</a> · <a href="{book("peano/axioms-and-rules", "logical-and-equality-rules")}">Natural deduction, equality, and induction rules</a></p></section>

<section class="pa-foundation-card" id="corpus-tactics"><h2>The {len(used_tactics)} tactics occurring in this proof corpus</h2><p>The 557 quadratic-reciprocity theorem pages link every formal proof line to the corresponding command below. Peano Lab has additional supported commands; their cards are included too and clearly labeled as outside this particular proof slice.</p><p>{corpus_links}</p><p>A command’s <strong>goal effect</strong> describes the obligation a reader sees; its <strong>kernel evidence</strong> describes the explicit certificate that must ultimately survive independent checking. Every example below is a complete replay ending in ordinary <code>qed</code>.</p></section>

<section class="pa-foundation-card" id="primitive-tactics"><h2>Primitive tactics and session commands · {len(cards_by_kind['primitive'])}</h2><p>Primitive commands introduce or eliminate logical structure, manipulate equalities, build explicit witnesses, or manage an honest proof session. Commands such as <code>undo</code> restore state but never create a logical inference; <code>use</code> imports only an independently checked theorem.</p>{''.join(cards_by_kind['primitive'])}</section>

<section class="pa-foundation-card" id="tactical-combinators"><h2>Tactical composition and goal selection · {len(cards_by_kind['tactical'])}</h2><p>A tactical combines existing proof-building steps; it adds no kernel inference rule. Sequencing, alternatives, repetition, first-success search, all-goal traversal, and focused execution retain exact goal-to-certificate-hole correspondence and roll back failed transactions.</p>{''.join(cards_by_kind['tactical'])}<p><a href="{book("peano/tacticals", "one-tactical-expression-is-one-transaction")}">Why one tactical expression is one transaction</a></p></section>

<section class="pa-foundation-card" id="checked-automation"><h2>Checked arithmetic, bounded search, and advice · {len(cards_by_kind['automation'])}</h2><p>Automation computes or searches, then constructs ordinary independently checked evidence. A bounded failure means only that this attempt exceeded its supported search or resource policy; it never proves a statement impossible. Advisory <code>hint</code> changes neither the goal nor the certificate.</p>{''.join(cards_by_kind['automation'])}<p><a href="{book("peano/arithmetic-automation", "the-boundary-is-intentionally-smaller-than-arithmetic")}">Why these commands are not decision procedures for all arithmetic</a></p></section>

<section class="pa-foundation-card" id="worked-proof"><h2>Read one complete proof from source text to kernel evidence</h2><pre><code>pa prove forall n. n + 0 = n
intro n
rewrite PA3
refl
qed</code></pre><p><a href="#tactic-intro"><code>intro n</code></a> contributes <a href="#constructor-forallintro"><code>ForallIntro</code></a>. <a href="#tactic-rewrite"><code>rewrite PA3</code></a> specializes the checked <a href="#axiom-pa3"><code>PA3</code></a> constant with <a href="#constructor-forallelim"><code>ForallElim</code></a> and transports the equality using <a href="#constructor-eqsubst"><code>EqSubst</code></a>. Finally, <a href="#tactic-refl"><code>refl</code></a> supplies <a href="#constructor-eqrefl"><code>EqRefl</code></a>. Only <code>qed</code> asks the independent kernel to check the completed certificate against the original universal formula.</p><p><a href="{book("peano/tactics", "rewrite-produces-transport-evidence")}">See the proof-state and transport explanation</a> · <a href="{book("peano/tutorials", "prove-add-comm-by-hand")}">Continue with a complete hand proof of addition commutativity</a> · <a href="/peano-lab/">Open the live Peano proof lab</a></p></section>

<section class="pa-foundation-card" id="reading-guide"><h2>Where to go next</h2><ul><li><a href="{book("peano/language-reference")}">Native PA language reference</a> — the exact term grammar, formulas, binding, and conservative relations.</li><li><a href="{book("peano/axioms-and-rules")}">PA axioms, induction, and proof rules</a> — the six arithmetic schemas and their logical interpretation.</li><li><a href="{book("peano/kernel")}">The independent proof kernel</a> — certificates, de Bruijn indices, and the owner-held QED boundary.</li><li><a href="{book("peano/tactics")}">Anatomy of a tactic</a> — proof states, holes, local facts, equality transport, and replay.</li><li><a href="{book("peano/tacticals")}">When tactics become a language</a> — sequencing, alternatives, focusing, rollback, and bounded search.</li><li><a href="{book("peano/induction-ladder")}">The induction ladder</a> — how small PA facts grow into reusable arithmetic.</li><li><a href="{book("peano/arithmetic-automation")}">Checked arithmetic automation</a> — the precise contracts of <code>simp</code>, <code>norm_num</code>, <code>ring</code>, and <code>auto</code>.</li><li><a href="{book("peano/compact-arith")}">Compact arithmetic certificates</a> — bounded PA-specific certificate synthesis.</li><li><a href="{book("arithmetic-library/language-and-trust")}">Arithmetic-library language and trust</a> — definitions, expansion, and checked theorem authority.</li><li><a href="{book("arithmetic-library/proof-sharing")}">Proof sharing without a theorem oracle</a> — checked <code>Cut</code>, dependency DAGs, and evidence reuse.</li><li><a href="{book("arithmetic-library/proof-explorer")}">How to read the quadratic-reciprocity proof explorer</a> — theorem pages, tags, and prerequisite paths.</li><li><a href="{book("arithmetic-library/quadratic-reciprocity")}">The quadratic-reciprocity campaign</a> — the complete mathematics supported by these foundations.</li></ul></section>
</main>'''
    return _page("Native PA foundations", "foundations", body)


def _render_graph(graph: dict[str, Any]) -> bytes:
    inline_data = _javascript_assignment("PA_PROOF_GRAPH", graph)
    atlas = _campaign_navigation("../../")
    return ('''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Theorem dependency paths — Native PA Proof Explorer</title>
  <link rel="stylesheet" href="assets/explorer.css">
  <script id="pa-proof-graph-data">''' + inline_data + '''</script>
  <script defer src="assets/explorer.js"></script>
</head>
<body class="pa-proof-site" data-page="graph">
  <header class="pa-proof-header pa-graph-heading">
    <nav aria-label="Proof Explorer">
      <a href="index.html">Theorem index</a>
      <a href="foundations.html">PA foundations</a>
      <a href="defined/graph.html?target=PA00FW&amp;view=neighborhood&amp;definitions=visible&amp;edges=focus&amp;v=''' + CAMPAIGN_HTML_REVISION + '''">Definition-aware graph</a>
      <a href="../../arithmetic-library/quadratic-reciprocity.html">Jupyter Book</a>
      ''' + atlas + '''
    </nav>
    <p class="pa-kicker">Interactive proof map</p>
    <h1>Theorem dependency paths</h1>
    <p>Follow a premise chain into any theorem, inspect its complete prerequisite cone, or open a node’s exact native-PA proof.</p>
  </header>

  <main class="pa-graph-page" data-dependency-graph data-graph-json="api/graph.json">
    <section class="pa-graph-controls" aria-labelledby="graph-controls-title">
      <h2 id="graph-controls-title">Choose a path</h2>
      <form data-graph-form>
        <label>
          Optional start theorem
          <input data-graph-source type="search" list="pa-graph-theorems" autocomplete="off" placeholder="Automatic theorem root">
        </label>
        <label>
          Target theorem
          <input data-graph-target type="search" list="pa-graph-theorems" autocomplete="off" required placeholder="PA00FW or theorem name">
        </label>
        <label>
          View
          <select data-graph-view>
            <option value="critical">Critical/deepest premise chain</option>
            <option value="shortest">Short premise chain</option>
            <option value="corridor">All routes from start to target</option>
            <option value="prerequisites">Complete prerequisite cone</option>
            <option value="neighborhood" selected>Direct neighborhood</option>
            <option value="dependents">Complete dependent cone</option>
            <option value="corpus">Entire theorem corpus</option>
          </select>
        </label>
        <label>
          Arrows
          <select data-graph-edges>
            <option value="focus" selected>Focused: path + target</option>
            <option value="none">Hide arrows</option>
            <option value="all">All direct arrows (heavy)</option>
          </select>
        </label>
        <button type="submit">Draw path</button>
      </form>
      <datalist id="pa-graph-theorems"></datalist>
      <p class="pa-graph-control-note">The sparse view suppresses arrows visually only: exact direct relations remain in the details panel and graph data. Large views use compact clickable theorem marks. A theorem root has no <em>theorem</em> prerequisites; it is not an axiom.</p>
    </section>

    <div class="pa-graph-layout">
      <section class="pa-graph-canvas-panel" aria-labelledby="graph-canvas-title">
        <div class="pa-graph-toolbar">
          <div>
            <h2 id="graph-canvas-title">Layered dependency graph</h2>
            <p data-graph-summary aria-live="polite">Loading theorem graph…</p>
          </div>
          <div class="pa-graph-zoom" aria-label="Graph viewport controls">
            <button type="button" data-graph-zoom="in" aria-label="Zoom in">+</button>
            <button type="button" data-graph-zoom="out" aria-label="Zoom out">−</button>
            <button type="button" data-graph-center>Center target</button>
            <button type="button" data-graph-fit>Fit view</button>
          </div>
        </div>
        <div class="pa-graph-stage" data-graph-stage>
          <svg data-graph-svg tabindex="0" role="group" aria-labelledby="graph-canvas-title graph-instructions">
            <text x="24" y="42">Loading theorem graph…</text>
          </svg>
        </div>
        <p id="graph-instructions" class="pa-graph-instructions">Shown arrows run from prerequisite to dependent. Click a node or compact mark to make it the target; use its ↗ link, when shown, or the details-panel proof link to open the formal proof. Drag the background to pan. Use the buttons or Control/Command + wheel to zoom.</p>
        <div class="pa-graph-legend" aria-label="Graph legend">
          <span><i class="pa-legend-node pa-legend-selected"></i> target</span>
          <span><i class="pa-legend-node pa-legend-critical"></i> chosen chain</span>
          <span><i class="pa-legend-node pa-legend-public"></i> Stable-source checked theorem</span>
          <span><i class="pa-legend-node pa-legend-candidate"></i> Alpha-only checked theorem; historical candidate-factory source</span>
          <span><i class="pa-legend-edge pa-legend-declared"></i> declared but not cited in tactic body</span>
        </div>
      </section>

      <aside class="pa-graph-details" aria-labelledby="graph-details-title">
        <p class="pa-eyebrow">Selected theorem</p>
        <h2 id="graph-details-title" data-graph-title tabindex="-1">Loading…</h2>
        <p data-graph-status></p>
        <p data-graph-description></p>
        <dl data-graph-metadata></dl>
        <p><a class="pa-graph-proof-link" data-graph-proof href="index.html">Open the formal proof →</a></p>
        <h3>Direct prerequisites</h3>
        <ul class="pa-graph-relation-list" data-graph-dependencies></ul>
        <h3>Direct dependents</h3>
        <ul class="pa-graph-relation-list" data-graph-dependents></ul>
      </aside>
    </div>

    <section class="pa-graph-path-fallback" aria-labelledby="graph-path-title">
      <p class="pa-eyebrow">Text alternative</p>
      <h2 id="graph-path-title">Ordered premise chain</h2>
      <p data-graph-path-note>The same selected route is listed here as ordinary links.</p>
      <ol data-graph-path-list>
        <li><a href="foundations.html">PA language, arithmetic axioms, and proof rules</a> <small>foundations prelude; not a theorem node</small></li>
      </ol>
    </section>

    <noscript>
      <p class="pa-callout">The interactive graph requires JavaScript. The <a href="index.html">theorem index</a> and every formal proof remain available without it.</p>
    </noscript>
  </main>
  <script id="pa-proof-release-evidence">
  (function () {
    "use strict";
    function install() {
      var root = document.querySelector("[data-dependency-graph]");
      var payload = window.PA_PROOF_GRAPH;
      if (!root || !payload || !Array.isArray(payload.nodes)) return;
      var title = root.querySelector("[data-graph-title]");
      var status = root.querySelector("[data-graph-status]");
      if (!title || !status || typeof MutationObserver !== "function") return;
      var nodes = new Map(payload.nodes.map(function (node) {
        return [node.tag, node];
      }));
      function showEvidence() {
        var tag = title.textContent.split(" · ", 1)[0].trim();
        var node = nodes.get(tag);
        if (!node || node.alpha_checked_use !== true) return;
        status.className = "pa-status-public";
        status.textContent = node.stable_member ?
          "Stable checked-use theorem; independently closed" :
          "Alpha v24 checked-use theorem; independently closed; not Stable";
      }
      new MutationObserver(showEvidence).observe(title, {
        childList: true, characterData: true, subtree: true
      });
      showEvidence();
    }
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", install, { once: true });
    } else {
      install();
    }
  })();
  </script>
</body>
</html>
''').encode("utf-8")


def _render_theorem(row: dict[str, Any], previous: dict[str, Any] | None, following: dict[str, Any] | None) -> bytes:
    relation = lambda items: " ".join(f'<a class="pa-theorem-ref" href="{item["tag"]}.html"><code>{item["tag"]}</code> { _e(item["name"])}</a>' for item in items) or "none"
    paragraphs = "".join(f"<p>{_e(text)}</p>" for text in row["informal"]["paragraphs"])
    ingredients = " ".join(
        f'<a class="pa-informal-ref" href="{_e(item["href"])}"><code>{_e(item["tag"])}</code> {_e(item["name"])}</a>'
        for item in row["informal"]["references"]
    ) or "none"
    lines = []
    for line in row["lines"]:
        lines.append(f'<li class="pa-proof-line" id="{line["id"]}" data-line="{line["number"]}" data-tactic="{_e(line["tactic"])}" data-line-id="{line["stable_id"]}"><a class="pa-line-number" href="#{line["id"]}">{line["number"]:04d}</a><code>{_render_command(line)}</code></li>')
    prev_link = f'<a href="{previous["tag"]}.html">← { _e(previous["name"])}</a>' if previous else ""
    next_link = f'<a href="{following["tag"]}.html">{ _e(following["name"])} →</a>' if following else ""
    source_label = (
        "Stable public-theorem source"
        if row["scope"] == "public"
        else "historical candidate-factory source; Alpha-only"
    )
    use_label = (
        "Stable checked-use theorem is independently kernel-checked when replayed"
        if row["stable_member"]
        else "Alpha-v24 checked-use theorem is independently kernel-checked when replayed; it is not a Stable theorem"
    )
    atlas = _campaign_navigation("../../../")
    body = f'''<header class="pa-proof-header pa-theorem-heading"><nav><a href="../index.html">Explorer</a><a href="../foundations.html">Foundations</a><a href="../defined/tag/{_e(row["tag"])}.html">Definition-aware theorem</a><a href="../defined/graph.html?target={_e(row["tag"])}&amp;view=neighborhood&amp;definitions=visible&amp;edges=focus">Theorem and definition graph</a>{atlas}{prev_link}{next_link}</nav><p class="pa-tag">{row["tag"]}</p><h1>{_e(row["name"])}</h1><p class="pa-status-public">{_e(row["status_label"])}</p><p>{_e(row["summary"])}</p></header><main class="pa-theorem-layout"><div class="pa-proof-panel"><section class="pa-statement"><h2>Exact expanded PA statement</h2><button data-copy-target="statement" type="button">Copy</button><pre id="statement"><code>{_e(row["statement"])}</code></pre></section><section class="pa-informal-proof" data-informal-kind="{_e(row["informal"]["kind"])}" data-informal-review="{_e(row["informal"]["review"])}"><h2>{_e(row["informal"]["title"])}</h2><p><strong>{"Curated informal proof" if row["informal"]["review"] == "curated_reviewed" else "Generated structural guide"}</strong></p>{paragraphs}<h3>Referenced ingredients</h3><div class="pa-chip-row">{ingredients}</div></section><section><h2>Proof neighborhood</h2><h3>Direct dependencies</h3><div class="pa-chip-row">{relation(row["dependencies"])}</div><h3>Direct dependents</h3><div class="pa-chip-row">{relation(row["dependents"])}</div></section><section><h2>Formal native tactic body</h2><p>Dependencies are introduced as named hypotheses before line 1. Linked names are exact direct references. This {use_label}.</p><ol class="pa-formal-proof">{"".join(lines)}</ol></section></div><aside class="pa-proof-sidebar pa-trust-panel"><h2>Receipt and source provenance</h2><dl><dt>Layer</dt><dd>{row["layer"]}</dd><dt>Lines</dt><dd>{len(row["lines"])}</dd><dt>Current Alpha edition</dt><dd>{_e(row["alpha_edition_version"])}</dd><dt>Proof-bearing Alpha edition</dt><dd>{_e(row["proof_edition_version"])}</dd><dt>Current release evidence</dt><dd>{_e(row["alpha_evidence"])}</dd><dt>Checked theorem use</dt><dd>{"yes" if row["alpha_checked_use"] else "no"}</dd><dt>Stable membership</dt><dd>{"yes" if row["stable_member"] else "no"}</dd><dt>Historical source origin</dt><dd>{_e(source_label)}</dd><dt>Specification SHA-256</dt><dd><code>{row["spec_sha256"]}</code></dd><dt>Source</dt><dd><a href="{_e(row["source"]["href"])}">{_e(row["source"]["path"])}:{row["source"]["line"]}</a> ({row["source"]["kind"]})</dd><dt>Source SHA-256</dt><dd><code>{row["source"]["sha256"]}</code></dd></dl></aside></main>'''
    return _page(f'{row["tag"]} — {row["name"]}', "theorem", body, "../")


def _dependency_graph_payload(
    records: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    """Build the deterministic query model consumed by the graph explorer.

    Every edge is directed from a prerequisite to a theorem which uses it.
    The admission order is already a topological order.  We use that same
    stable order for every tag array, including transitive closures and the
    tie-break between equally short foundation paths.
    """

    tags = [row["tag"] for row in records]
    rank = {tag: index for index, tag in enumerate(tags)}
    layer_by_tag = {row["tag"]: row["layer"] for row in records}
    if len(rank) != len(tags):
        raise ValueError("dependency graph tags must be unique")

    dependencies: dict[str, list[str]] = {}
    dependents: dict[str, list[str]] = {tag: [] for tag in tags}
    for row in records:
        tag = row["tag"]
        direct = sorted(
            (dependency["tag"] for dependency in row["dependencies"]),
            key=rank.__getitem__,
        )
        if len(direct) != len(set(direct)):
            raise ValueError(f"duplicate dependency for {tag}")
        if any(rank[dependency] >= rank[tag] for dependency in direct):
            raise ValueError(f"dependency graph is not topologically ordered at {tag}")
        dependencies[tag] = direct
        for dependency in direct:
            dependents[dependency].append(tag)

    edge_pairs = {
        (edge["dependency"], edge["dependent"])
        for edge in edges
    }
    adjacency_pairs = {
        (dependency, tag)
        for tag, direct in dependencies.items()
        for dependency in direct
    }
    if len(edge_pairs) != len(edges) or edge_pairs != adjacency_pairs:
        raise ValueError("edge list and direct adjacency disagree")

    ancestors: dict[str, set[str]] = {}
    shortest_root_paths: dict[str, list[str]] = {}
    critical_root_paths: dict[str, list[str]] = {}
    root_path_counts: dict[str, int] = {}
    for tag in tags:
        closure: set[str] = set()
        for dependency in dependencies[tag]:
            closure.add(dependency)
            closure.update(ancestors[dependency])
        ancestors[tag] = closure
        if dependencies[tag]:
            shortest_candidates = [
                [*shortest_root_paths[dependency], tag]
                for dependency in dependencies[tag]
            ]
            shortest_root_paths[tag] = min(
                shortest_candidates,
                key=lambda path: (len(path), tuple(rank[item] for item in path)),
            )
            critical_candidates = [
                [*critical_root_paths[dependency], tag]
                for dependency in dependencies[tag]
            ]
            critical_root_paths[tag] = min(
                critical_candidates,
                key=lambda path: (-len(path), tuple(rank[item] for item in path)),
            )
            root_path_counts[tag] = sum(
                root_path_counts[dependency]
                for dependency in dependencies[tag]
            )
        else:
            shortest_root_paths[tag] = [tag]
            critical_root_paths[tag] = [tag]
            root_path_counts[tag] = 1
        if len(critical_root_paths[tag]) != layer_by_tag[tag] + 1:
            raise ValueError(f"critical root path does not witness layer depth at {tag}")

    descendants: dict[str, set[str]] = {}
    for tag in reversed(tags):
        closure = set()
        for dependent in dependents[tag]:
            closure.add(dependent)
            closure.update(descendants[dependent])
        descendants[tag] = closure

    layers_by_index: dict[int, list[str]] = defaultdict(list)
    for row in records:
        layers_by_index[row["layer"]].append(row["tag"])
    expected_layers = list(range(receipt["layer_count"]))
    if sorted(layers_by_index) != expected_layers:
        raise ValueError("dependency graph layers are not contiguous")

    foundations = [tag for tag in tags if not dependencies[tag]]
    terminals = [tag for tag in tags if not dependents[tag]]
    adjacency = {
        tag: {
            "dependencies": dependencies[tag],
            "dependents": dependents[tag],
            "ancestors": sorted(ancestors[tag], key=rank.__getitem__),
            "descendants": sorted(descendants[tag], key=rank.__getitem__),
            # Compatibility alias for the first graph UI prototype.
            "foundation_path": shortest_root_paths[tag],
            "shortest_root_path": shortest_root_paths[tag],
            "critical_root_path": critical_root_paths[tag],
            "root_path_count": root_path_counts[tag],
        }
        for tag in tags
    }
    return {
        "schema": "peano-lab-pa-proof-graph-v2",
        **receipt,
        "orientation": "dependency_to_dependent",
        "path_policy": {
            "foundation_path_alias": "shortest_root_path",
            "shortest_root_path": "fewest_edges_from_any_foundation",
            "critical_root_path": "dependency_depth_witness",
            "tie_break": "admission_order_lexicographic",
            "includes_endpoints": True,
        },
        "foundations": foundations,
        "terminals": terminals,
        "layers": [
            {"index": index, "nodes": layers_by_index[index]}
            for index in expected_layers
        ],
        "nodes": [
            {
                key: row[key]
                for key in (
                    "tag", "name", "scope", "status", "layer", "summary",
                    "alpha_edition_version", "alpha_evidence",
                    "alpha_checked_use", "stable_member",
                )
            }
            | {"href": f'../tag/{row["tag"]}.html'}
            for row in records
        ],
        "edges": edges,
        "adjacency": adjacency,
    }


def _dependency_graph_schema() -> dict[str, Any]:
    """JSON Schema for the public v2 dependency-graph payload."""

    tag = {"type": "string", "pattern": r"^PA[0-9A-Y]{4}$"}
    tag_array = {
        "type": "array",
        "items": {"$ref": "#/$defs/tag"},
        "uniqueItems": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:peano-lab:pa-proof-graph-v2",
        "title": "Peano Lab native-PA proof dependency graph",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema", "theorem_count", "public_count", "candidate_count",
            "edge_count", "layer_count", "formal_line_count",
            "explicit_dependency_reference_count", "graph_sha256",
            "source_sha256", "alpha_edition_version",
            "alpha_edition_identity_sha256", "alpha_edition_checked_use_count",
            "proof_edition_version", "proof_edition_identity_sha256",
            "proof_edition_checked_use_count",
            "graph_checked_use_count", "graph_stable_closed_count",
            "graph_alpha_closed_count", "graph_newly_promoted_count",
            "source_scope_policy", "orientation", "path_policy", "foundations",
            "terminals", "layers", "nodes", "edges", "adjacency",
        ],
        "properties": {
            "schema": {"const": "peano-lab-pa-proof-graph-v2"},
            "theorem_count": {"type": "integer", "minimum": 0},
            "public_count": {"type": "integer", "minimum": 0},
            "candidate_count": {"type": "integer", "minimum": 0},
            "edge_count": {"type": "integer", "minimum": 0},
            "layer_count": {"type": "integer", "minimum": 0},
            "formal_line_count": {"type": "integer", "minimum": 0},
            "explicit_dependency_reference_count": {"type": "integer", "minimum": 0},
            "graph_sha256": {"$ref": "#/$defs/sha256"},
            "source_sha256": {"$ref": "#/$defs/sha256"},
            "alpha_edition_version": {"const": "v24"},
            "alpha_edition_identity_sha256": {"$ref": "#/$defs/sha256"},
            "alpha_edition_checked_use_count": {"type": "integer", "minimum": 0},
            "proof_edition_version": {"const": "v16"},
            "proof_edition_identity_sha256": {"$ref": "#/$defs/sha256"},
            "proof_edition_checked_use_count": {"type": "integer", "minimum": 0},
            "graph_checked_use_count": {"type": "integer", "minimum": 0},
            "graph_stable_closed_count": {"type": "integer", "minimum": 0},
            "graph_alpha_closed_count": {"type": "integer", "minimum": 0},
            "graph_newly_promoted_count": {"type": "integer", "minimum": 0},
            "source_scope_policy": {
                "const": "historical_origin_not_current_release_authority",
            },
            "orientation": {"const": "dependency_to_dependent"},
            "path_policy": {"$ref": "#/$defs/path_policy"},
            "foundations": {"$ref": "#/$defs/tag_array"},
            "terminals": {"$ref": "#/$defs/tag_array"},
            "layers": {
                "type": "array",
                "items": {"$ref": "#/$defs/layer"},
            },
            "nodes": {
                "type": "array",
                "items": {"$ref": "#/$defs/node"},
            },
            "edges": {
                "type": "array",
                "items": {"$ref": "#/$defs/edge"},
            },
            "adjacency": {
                "type": "object",
                "patternProperties": {
                    r"^PA[0-9A-Y]{4}$": {"$ref": "#/$defs/neighborhood"},
                },
                "additionalProperties": False,
            },
        },
        "$defs": {
            "tag": tag,
            "tag_array": tag_array,
            "sha256": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
            "path_policy": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "foundation_path_alias", "shortest_root_path",
                    "critical_root_path", "tie_break", "includes_endpoints",
                ],
                "properties": {
                    "foundation_path_alias": {"const": "shortest_root_path"},
                    "shortest_root_path": {"const": "fewest_edges_from_any_foundation"},
                    "critical_root_path": {"const": "dependency_depth_witness"},
                    "tie_break": {"const": "admission_order_lexicographic"},
                    "includes_endpoints": {"const": True},
                },
            },
            "layer": {
                "type": "object",
                "additionalProperties": False,
                "required": ["index", "nodes"],
                "properties": {
                    "index": {"type": "integer", "minimum": 0},
                    "nodes": {"$ref": "#/$defs/tag_array"},
                },
            },
            "node": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "tag", "name", "scope", "status", "layer", "summary", "href",
                    "alpha_edition_version", "alpha_evidence",
                    "alpha_checked_use", "stable_member",
                ],
                "properties": {
                    "tag": {"$ref": "#/$defs/tag"},
                    "name": {"type": "string", "minLength": 1},
                    "scope": {"enum": ["public", "candidate"]},
                    "status": {
                        "enum": [
                            "public", "alpha_closed", "candidate_body_checked",
                            "pending_layered_closure",
                        ],
                    },
                    "layer": {"type": "integer", "minimum": 0},
                    "summary": {"type": "string", "minLength": 1},
                    "href": {"type": "string", "pattern": r"^\.\./tag/PA[0-9A-Y]{4}\.html$"},
                    "alpha_edition_version": {"const": "v24"},
                    "alpha_evidence": {"enum": ["stable_closed", "alpha_closed"]},
                    "alpha_checked_use": {"const": True},
                    "stable_member": {"type": "boolean"},
                },
            },
            "edge": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "dependency", "dependency_name", "dependent", "dependent_name",
                    "body_reference", "explicit_reference_count",
                ],
                "properties": {
                    "dependency": {"$ref": "#/$defs/tag"},
                    "dependency_name": {"type": "string", "minLength": 1},
                    "dependent": {"$ref": "#/$defs/tag"},
                    "dependent_name": {"type": "string", "minLength": 1},
                    "body_reference": {"type": "boolean"},
                    "explicit_reference_count": {"type": "integer", "minimum": 0},
                },
            },
            "neighborhood": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "dependencies", "dependents", "ancestors", "descendants",
                    "foundation_path", "shortest_root_path", "critical_root_path",
                    "root_path_count",
                ],
                "properties": {
                    "dependencies": {"$ref": "#/$defs/tag_array"},
                    "dependents": {"$ref": "#/$defs/tag_array"},
                    "ancestors": {"$ref": "#/$defs/tag_array"},
                    "descendants": {"$ref": "#/$defs/tag_array"},
                    "foundation_path": {
                        "allOf": [
                            {"$ref": "#/$defs/tag_array"},
                            {"minItems": 1},
                        ],
                    },
                    "shortest_root_path": {
                        "allOf": [
                            {"$ref": "#/$defs/tag_array"},
                            {"minItems": 1},
                        ],
                    },
                    "critical_root_path": {
                        "allOf": [
                            {"$ref": "#/$defs/tag_array"},
                            {"minItems": 1},
                        ],
                    },
                    "root_path_count": {"type": "integer", "minimum": 1},
                },
            },
        },
    }


def build() -> tuple[dict[str, bytes], dict[str, Any]]:
    immutable_evidence_corpus = _immutable_evidence_corpus()
    stack = quadratic_reciprocity_stack()
    specs = list(stack.admission_order)
    names = [spec.name for spec in specs]
    tags_data = _load_tags()
    missing = [name for name in names if name not in tags_data["assignments"]]
    if missing:
        raise ValueError(f"missing {len(missing)} persistent proof tags; run --update-tags")
    tags = tags_data["assignments"]
    overrides = json.loads(INFORMAL.read_text(encoding="utf-8"))["overrides"]
    public = {spec.name for spec in stack.public_order}
    candidate = {spec.name for spec in stack.candidate_order}
    by_name = {spec.name: spec for spec in specs}
    dependents: dict[str, list[str]] = {name: [] for name in names}
    for spec in specs:
        for dependency in spec.dependencies:
            dependents[dependency].append(spec.name)
    locations = _literal_locations()
    edge_reference_counts: Counter[tuple[str, str]] = Counter()
    records = []
    all_tactics: Counter[str] = Counter()
    evidence_counts: Counter[str] = Counter()
    total_lines = 0
    total_refs = 0
    for index, spec in enumerate(specs):
        scope = "public" if spec.name in public else "candidate"
        release_entry = current_alpha.ALPHA_EDITION.by_name.get(spec.name)
        if release_entry is None or release_entry.spec != spec:
            raise ValueError(
                f"QR proof explorer theorem {spec.name!r} differs from sealed Alpha v24"
            )
        proof_entry = alpha_v16.ALPHA_EDITION.by_name.get(spec.name)
        if (
            proof_entry is None
            or proof_entry.spec != release_entry.spec
            or proof_entry.membership is not release_entry.membership
            or proof_entry.evidence is not release_entry.evidence
            or not proof_entry.checked_use
        ):
            raise ValueError(
                f"QR proof explorer theorem {spec.name!r} lost its immutable "
                "Alpha-v16 proof-bearing release evidence"
            )
        stable_member = release_entry.membership is current_alpha.Membership.STABLE
        expected_evidence = (
            current_alpha.EvidenceStatus.STABLE_CLOSED
            if scope == "public"
            else current_alpha.EvidenceStatus.ALPHA_CLOSED
        )
        if (
            release_entry.evidence is not expected_evidence
            or not release_entry.checked_use
            or stable_member != (scope == "public")
        ):
            raise ValueError(
                f"QR proof explorer theorem {spec.name!r} has unexpected "
                "Alpha-v24 evidence, membership, or checked-use authority"
            )
        evidence_counts[release_entry.evidence.value] += 1
        counts: Counter[str] = Counter()
        occurrence: Counter[str] = Counter()
        lines = []
        for number, command in enumerate(spec.script, 1):
            tactic, references = _command_spans(command, set(spec.dependencies))
            counts[tactic] += 1
            all_tactics[tactic] += 1
            occurrence[command] += 1
            theorem_references = []
            axiom_references = []
            for reference in references:
                if reference["kind"] == "theorem":
                    reference["tag"] = tags[reference["name"]]
                    reference["href"] = f'{tags[reference["name"]]}.html'
                    edge_reference_counts[(spec.name, reference["name"])] += 1
                    total_refs += 1
                    theorem_references.append(reference)
                else:
                    reference["href"] = f'../foundations.html#axiom-{reference["name"].lower()}'
                    axiom_references.append(reference)
            lines.append({
                "id": f"proof-line-{number:04d}",
                "number": number,
                "text": command,
                "tactic": tactic,
                "tactic_href": f"../foundations.html#tactic-{tactic}",
                "stable_id": _digest(f"{spec.name}\x1f{command}\x1f{occurrence[command]}")[:16],
                "references": theorem_references,
                "axiom_references": axiom_references,
            })
        total_lines += len(lines)
        informal = overrides.get(spec.name) or _shape_guide(spec, counts)
        if spec.name in overrides:
            informal = {
                "kind": "curated_override",
                "review": "curated_reviewed",
                **informal,
                "reference_names": list(informal.get("references", ())),
            }
            informal.pop("references", None)
        reference_names = informal.pop("reference_names")
        if len(reference_names) != len(set(reference_names)):
            raise ValueError(f"duplicate informal reference for {spec.name}")
        unknown_informal = [name for name in reference_names if name not in by_name]
        if unknown_informal:
            raise ValueError(
                f"unknown informal reference(s) for {spec.name}: {unknown_informal!r}"
            )
        informal["references"] = [
            {"name": name, "tag": tags[name], "href": f"{tags[name]}.html"}
            for name in reference_names
        ]
        payload = "\x1f".join((scope, spec.name, spec.statement, "\x1e".join(spec.script), "\x1e".join(spec.dependencies)))
        records.append({
            "index": index,
            "tag": tags[spec.name],
            "name": spec.name,
            "scope": scope,
            "status": "public" if scope == "public" else "alpha_closed",
            "status_label": (
                "Stable checked-use theorem · independently closed"
                if stable_member
                else "Alpha v24 checked-use theorem · independently closed; not Stable"
            ),
            "alpha_edition_version": "v24",
            "proof_edition_version": "v16",
            "alpha_evidence": release_entry.evidence.value,
            "alpha_checked_use": release_entry.checked_use,
            "stable_member": stable_member,
            "layer": stack.dependency_depth_by_name[spec.name],
            "summary": spec.summary,
            "statement": spec.statement,
            "statement_sha256": _digest(spec.statement),
            "script_sha256": _digest("\n".join(spec.script)),
            "spec_sha256": _digest(payload),
            "dependencies": [],
            "dependents": [],
            "lines": lines,
            "informal": informal,
            "source": _source_record(spec.name, scope, stack, locations),
        })
    edges = []
    for row in records:
        spec = by_name[row["name"]]
        row["dependencies"] = [{
            "name": name, "tag": tags[name], "href": f'{tags[name]}.html',
            "body_reference": edge_reference_counts[(row["name"], name)] > 0,
            "explicit_reference_count": edge_reference_counts[(row["name"], name)],
        } for name in spec.dependencies]
        row["dependents"] = [{
            "name": name, "tag": tags[name], "href": f'{tags[name]}.html',
            "body_reference": edge_reference_counts[(name, row["name"])] > 0,
            "explicit_reference_count": edge_reference_counts[(name, row["name"])],
        } for name in dependents[row["name"]]]
        for dependency in row["dependencies"]:
            edges.append({
                "dependency": dependency["tag"], "dependency_name": dependency["name"],
                "dependent": row["tag"], "dependent_name": row["name"],
                "body_reference": dependency["body_reference"],
                "explicit_reference_count": dependency["explicit_reference_count"],
            })
    actual = {
        "theorem_count": len(records), "public_count": len(public), "candidate_count": len(candidate),
        "edge_count": len(edges), "layer_count": len(stack.dependency_layers), "formal_line_count": total_lines,
        "explicit_dependency_reference_count": total_refs, "graph_sha256": stack.graph_sha256,
        "source_sha256": stack.source_sha256,
    }
    if actual != EXPECTED:
        raise ValueError(f"QR proof explorer receipt changed: {actual!r}")
    evidence_receipt = {
        "alpha_edition_version": "v24",
        "alpha_edition_identity_sha256": current_alpha.ALPHA_V24_IDENTITY_SHA256,
        "alpha_edition_checked_use_count": len(current_alpha.ALPHA_CHECKED_SPECS),
        "proof_edition_version": "v16",
        "proof_edition_identity_sha256": alpha_v16.ALPHA_V16_IDENTITY_SHA256,
        "proof_edition_checked_use_count": len(alpha_v16.ALPHA_CHECKED_SPECS),
        "graph_checked_use_count": sum(row["alpha_checked_use"] for row in records),
        "graph_stable_closed_count": evidence_counts["stable_closed"],
        "graph_alpha_closed_count": evidence_counts["alpha_closed"],
        "graph_newly_promoted_count": len(alpha_v16.QR_PROMOTED_NAMES),
        "source_scope_policy": "historical_origin_not_current_release_authority",
    }
    if evidence_receipt != EXPECTED_ALPHA_EVIDENCE:
        raise ValueError(
            f"QR proof explorer Alpha-v24/v16 evidence receipt changed: {evidence_receipt!r}"
        )
    receipt = {**actual, **evidence_receipt}
    corpus = {
        "schema": "peano-lab-pa-proof-corpus-v1", **receipt, "theorems": records,
    }
    graph = _dependency_graph_payload(records, edges, receipt)
    graph_schema = _dependency_graph_schema()
    files: dict[str, bytes] = {
        "index.html": _render_index(records, stack),
        "foundations.html": _render_foundations(sorted(all_tactics)),
        "graph.html": _render_graph(graph),
        IMMUTABLE_EVIDENCE_CORPUS_PATH: immutable_evidence_corpus,
        CURRENT_CORPUS_PATH: _json_bytes(corpus),
        "api/graph.json": _json_bytes(graph),
        "api/graph.schema.json": _json_bytes(graph_schema),
        **_pinned_ui_assets(),
    }
    for index, row in enumerate(records):
        files[f'tag/{row["tag"]}.html'] = _render_theorem(row, records[index - 1] if index else None, records[index + 1] if index + 1 < len(records) else None)
        target = f'../tag/{row["tag"]}.html'
        files[f'name/{row["name"]}.html'] = f'''<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}"><script>location.replace({json.dumps(target)}+location.search+location.hash)</script></head><body><a href="{target}">{_e(row["name"])}</a></body></html>\n'''.encode()
    manifest_files = [{"path": path, "bytes": len(payload), "sha256": _digest(payload)} for path, payload in sorted(files.items())]
    aggregate = _digest("\n".join(f'{item["path"]}\0{item["sha256"]}' for item in manifest_files))
    manifest = {
        "schema": "peano-lab-pa-proof-explorer-manifest-v1", **receipt,
        "immutable_evidence_corpus_path": IMMUTABLE_EVIDENCE_CORPUS_PATH,
        "immutable_evidence_corpus_sha256": IMMUTABLE_EVIDENCE_CORPUS_SHA256,
        "immutable_evidence_corpus_bytes": IMMUTABLE_EVIDENCE_CORPUS_BYTES,
        "current_corpus_path": CURRENT_CORPUS_PATH,
        "current_corpus_sha256": _digest(files[CURRENT_CORPUS_PATH]),
        "generated_file_count": len(files) + 1,
        "canonical_tag_page_count": len(records), "name_alias_page_count": len(records),
        "aggregate_sha256": aggregate,
        "tag_registry_sha256": _digest(TAGS.read_bytes()),
        "informal_overrides_sha256": _digest(INFORMAL.read_bytes()),
        "required_assets": ["assets/explorer.css", "assets/explorer.js"],
        "files": manifest_files,
    }
    files["manifest.json"] = _json_bytes(manifest)
    return files, manifest


def _write(files: dict[str, bytes]) -> None:
    protected = files.get(IMMUTABLE_EVIDENCE_CORPUS_PATH)
    if protected is not None and protected != _immutable_evidence_corpus():
        raise ValueError("refusing to replace the immutable Alpha-parent proof corpus")
    for relative, payload in files.items():
        if relative == IMMUTABLE_EVIDENCE_CORPUS_PATH:
            continue
        path = OUTPUT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    expected = set(files)
    if OUTPUT.exists():
        for path in OUTPUT.rglob("*"):
            relative = path.relative_to(OUTPUT)
            if (
                path.is_file()
                and (not relative.parts or relative.parts[0] not in RESERVED_SUBTREES)
                and str(relative) not in expected
                and str(relative) != IMMUTABLE_EVIDENCE_CORPUS_PATH
            ):
                path.unlink()
    if protected is not None:
        _immutable_evidence_corpus()


def _check(files: dict[str, bytes]) -> bool:
    drift = []
    for relative, payload in files.items():
        path = OUTPUT / relative
        if not path.is_file() or path.read_bytes() != payload:
            drift.append(relative)
    expected = set(files)
    if OUTPUT.exists():
        drift.extend(
            str(path.relative_to(OUTPUT))
            for path in OUTPUT.rglob("*")
            if path.is_file()
            and (
                not path.relative_to(OUTPUT).parts
                or path.relative_to(OUTPUT).parts[0] not in RESERVED_SUBTREES
            )
            and str(path.relative_to(OUTPUT)) not in expected
        )
    if drift:
        print("PA proof explorer drift: " + ", ".join(sorted(set(drift))[:20]), file=sys.stderr)
        return False
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--update-tags", action="store_true")
    args = parser.parse_args(argv)
    stack = quadratic_reciprocity_stack()
    if args.update_tags:
        _update_tags([spec.name for spec in stack.admission_order])
    files, manifest = build()
    if args.check:
        if not _check(files):
            return 1
        print(f'verified PA proof explorer: {manifest["generated_file_count"]} files, {manifest["aggregate_sha256"]}')
        return 0
    _write(files)
    print(f'wrote PA proof explorer: {manifest["generated_file_count"]} files, {manifest["aggregate_sha256"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
