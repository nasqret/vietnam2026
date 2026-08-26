"""Fast contract tests for the model-v3 metadata join."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPOSITORY_ROOT / "scripts" / "combine_peano_v3_corpus_metadata.py"


def _load_script():
    specification = importlib.util.spec_from_file_location(
        "_test_combine_peano_v3_corpus_metadata", SCRIPT
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


combiner = _load_script()
FULL_IDENTITY = "a" * 64
SYNTHETIC_ENVIRONMENT = "b" * 64
SYNTHETIC_PREFIX_IDENTITY = "c" * 64


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _common(
    *,
    session: str,
    statement: str,
    prefix: int,
    prefix_identity: str,
    environment: str,
) -> dict[str, object]:
    return {
        "session": session,
        "theorem": f"theorem.{session}",
        "family": f"family/{session}",
        "lineage": f"lineage/{session}",
        "classical": False,
        "surface": "model-v3",
        "environment_sha256": environment,
        "capabilities": {
            "label": "model-v3",
            "allowed_commands": [],
            "allowed_theorems": [],
        },
        "statement": statement,
        "library_identity_sha256": prefix_identity,
        "library_full_identity_sha256": FULL_IDENTITY,
        "library_prefix_length": prefix,
        "library_size": 247,
    }


def _library_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for index in range(247):
        name = f"library_{index:03d}"
        record = _common(
            session=f"library-session-{index:03d}",
            statement=f"library statement {index:03d}",
            prefix=index,
            prefix_identity=_digest(f"prefix-{index}"),
            environment=_digest(f"environment-{index}"),
        )
        record.update(
            {
                "theorem": name,
                "trajectory": "catalog-predecessor-prefix-v1",
                "library_target_index": index,
                "library_target_name": name,
            }
        )
        records.append(record)
    return records


def _synthetic_records(count: int = 3) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for ordinal in range(1, count + 1):
        record = _common(
            session=f"synthetic-session-{ordinal:03d}",
            statement=f"synthetic statement {ordinal:03d}",
            prefix=247,
            prefix_identity=SYNTHETIC_PREFIX_IDENTITY,
            environment=SYNTHETIC_ENVIRONMENT,
        )
        record.update(
            {
                "lane": "synthetic-root-balanced",
                "seed": "unit-test-v3",
                "ordinal": ordinal,
                "root": f"synthetic/root/{ordinal:03d}",
            }
        )
        records.append(record)
    return records


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )
    return path


def _inputs(
    root: Path,
    *,
    library: list[dict[str, object]] | None = None,
    synthetic: list[dict[str, object]] | None = None,
) -> tuple[Path, Path, Path, Path]:
    return (
        _write_jsonl(root / "library.jsonl", library or _library_records()),
        _write_jsonl(root / "synthetic.jsonl", synthetic or _synthetic_records()),
        root / "combined.jsonl",
        root / "combined-manifest.json",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_combines_exact_populations_in_canonical_order_with_manifest(
    tmp_path: Path,
) -> None:
    library = list(reversed(_library_records()))
    synthetic = list(reversed(_synthetic_records()))
    paths = _inputs(tmp_path, library=library, synthetic=synthetic)

    result = combiner.combine_metadata(*paths)

    rows = _read_jsonl(paths[2])
    assert [row["library_target_index"] for row in rows[:247]] == list(range(247))
    assert [row["ordinal"] for row in rows[247:]] == [1, 2, 3]
    assert paths[2].read_bytes().endswith(b"\n")
    # Canonical output is independent of source record ordering and spacing.
    first_output = paths[2].read_bytes()
    ordered_paths = _inputs(tmp_path / "ordered")
    combiner.combine_metadata(*ordered_paths)
    assert ordered_paths[2].read_bytes() == first_output

    manifest = json.loads(paths[3].read_text(encoding="utf-8"))
    assert result.manifest == manifest
    assert manifest["format"] == "peano-v3-combined-corpus-metadata"
    assert manifest["library"] == {
        "full_identity_sha256": FULL_IDENTITY,
        "size": 247,
        "trajectory": "catalog-predecessor-prefix-v1",
        "prefix_coverage": [0, 246],
    }
    assert manifest["synthetic_population"] == {
        "lane": "synthetic-root-balanced",
        "library_prefix_length": 247,
        "seed": "unit-test-v3",
        "environment_sha256": SYNTHETIC_ENVIRONMENT,
        "library_identity_sha256": SYNTHETIC_PREFIX_IDENTITY,
    }
    assert manifest["counts"] == {
        "sessions": 250,
        "unique_sessions": 250,
        "unique_target_statements": 250,
        "library_sessions": 247,
        "synthetic_sessions": 3,
        "synthetic_populations": 1,
    }
    assert manifest["artifact"]["metadata"]["sha256"] == hashlib.sha256(
        paths[2].read_bytes()
    ).hexdigest()


def test_rejects_incomplete_library_coverage_without_changing_outputs(
    tmp_path: Path,
) -> None:
    paths = _inputs(tmp_path, library=_library_records()[:-1])
    paths[2].write_text("old combined\n", encoding="utf-8")
    paths[3].write_text("old manifest\n", encoding="utf-8")

    with pytest.raises(combiner.CombinationError, match="exactly 247"):
        combiner.combine_metadata(*paths)

    assert paths[2].read_text(encoding="utf-8") == "old combined\n"
    assert paths[3].read_text(encoding="utf-8") == "old manifest\n"


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("second_seed", "exactly one full-prefix population"),
        ("partial_prefix", "must use the full 247-theorem prefix"),
        ("duplicate_ordinal", "duplicate synthetic ordinal"),
        ("duplicate_target", "duplicate target statement"),
        ("duplicate_session", "duplicate session"),
        ("wrong_full_identity", "one common full-library identity"),
    ),
)
def test_rejects_population_or_join_ambiguity(
    tmp_path: Path, mutation: str, message: str
) -> None:
    library = _library_records()
    synthetic = _synthetic_records()
    if mutation == "second_seed":
        synthetic[1]["seed"] = "another-run"
    elif mutation == "partial_prefix":
        synthetic[1]["library_prefix_length"] = 246
    elif mutation == "duplicate_ordinal":
        synthetic[1]["ordinal"] = 1
    elif mutation == "duplicate_target":
        synthetic[1]["statement"] = library[0]["statement"]
    elif mutation == "duplicate_session":
        synthetic[1]["session"] = library[0]["session"]
    elif mutation == "wrong_full_identity":
        synthetic[1]["library_full_identity_sha256"] = "d" * 64
    paths = _inputs(tmp_path, library=library, synthetic=synthetic)

    with pytest.raises(combiner.CombinationError, match=message):
        combiner.combine_metadata(*paths)

    assert not paths[2].exists()
    assert not paths[3].exists()


@pytest.mark.parametrize(
    ("contents", "message"),
    (
        ('{"session":"a","session":"b"}\n', "duplicate JSON key"),
        ('{"session":"a","value":NaN}\n', "non-finite JSON number"),
        ('{"session":"a"}', "missing final newline"),
        ('{"session":"a"}\n\n', "blank JSONL records"),
    ),
)
def test_jsonl_parser_is_strict(
    tmp_path: Path, contents: str, message: str
) -> None:
    library, synthetic, output, manifest = _inputs(tmp_path)
    library.write_text(contents, encoding="utf-8")

    with pytest.raises(combiner.CombinationError, match=message):
        combiner.combine_metadata(library, synthetic, output, manifest)


def test_cli_contract_reports_success_and_validation_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library, synthetic, output, manifest = _inputs(tmp_path / "ok")
    assert (
        combiner.main(
            [
                "--library-metadata",
                str(library),
                "--synthetic-metadata",
                str(synthetic),
                "--output",
                str(output),
                "--manifest",
                str(manifest),
            ]
        )
        == 0
    )
    assert "combined 247 library + 3 synthetic sessions" in capsys.readouterr().out

    broken = tmp_path / "broken.jsonl"
    broken.write_text("{}\n", encoding="utf-8")
    assert (
        combiner.main(
            [
                "--library-metadata",
                str(broken),
                "--synthetic-metadata",
                str(synthetic),
                "--output",
                str(tmp_path / "no-output.jsonl"),
                "--manifest",
                str(tmp_path / "no-manifest.json"),
            ]
        )
        == 2
    )
    assert "metadata combination failed:" in capsys.readouterr().err
