"""Bounded, byte-exact counterfactual JSON for current publication tests only."""

from __future__ import annotations

import io
import json

import pytest


def compact_current_catalog_bytes(document: object) -> bytes:
    """Use the actual compact catalog format without a whole Unicode copy."""

    encoder = json.JSONEncoder(
        ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"),
    )
    with io.BytesIO() as output:
        for chunk in encoder.iterencode(document):
            output.write(chunk.encode("utf-8"))
        output.write(b"\n")
        return output.getvalue()


@pytest.mark.parametrize("document", (
    None, True, False, 0, -(2 ** 256), 2 ** 256, 1.25,
    "ASCII </script>", "Ω∀🙂↔<>\"\\\n", [], {},
    {"z": 1, "a": [None, "Ω", {"b": True}]},
))
def test_counterfactual_encoding_matches_exact_strict_compact_json(document: object) -> None:
    expected = json.dumps(
        document, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    assert compact_current_catalog_bytes(document) == expected


@pytest.mark.parametrize("document,error", (
    (float("nan"), ValueError), (float("inf"), ValueError),
    (-float("inf"), ValueError), ({"bad": float("nan")}, ValueError),
    ([float("inf")], ValueError), (object(), TypeError),
    ({"bad": {1, 2}}, TypeError), ({"bad": b"bytes"}, TypeError),
    ({(1, 2): "key"}, TypeError),
))
def test_counterfactual_encoding_preserves_strict_json_rejections(
    document: object, error: type[Exception],
) -> None:
    with pytest.raises(error):
        compact_current_catalog_bytes(document)


@pytest.mark.parametrize("kind", ("list", "dict"))
def test_counterfactual_encoding_rejects_circular_documents(kind: str) -> None:
    document = [] if kind == "list" else {}
    if kind == "list":
        document.append(document)
    else:
        document["self"] = document
    with pytest.raises(ValueError, match="Circular reference"):
        compact_current_catalog_bytes(document)


@pytest.mark.parametrize("repetitions", (0, 1, 10000))
def test_counterfactual_encoding_preserves_multibyte_string_and_token_boundaries(
    repetitions: int,
) -> None:
    document = {"z": ["∀n. Ω🙂\\\n" * repetitions], "a": {"quoted": "\""}}
    expected = json.dumps(
        document, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    assert compact_current_catalog_bytes(document) == expected


def test_counterfactual_encoding_never_materializes_a_whole_unicode_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = {"b": "Ω", "a": [1, 2]}
    expected = b'{"a":[1,2],"b":"\xce\xa9"}\n'

    def forbidden(*args: object, **kwargs: object) -> str:
        raise AssertionError("whole-document Unicode encoding was used")

    monkeypatch.setattr(json, "dumps", forbidden)
    monkeypatch.setattr(json.JSONEncoder, "encode", forbidden)
    assert compact_current_catalog_bytes(document) == expected
