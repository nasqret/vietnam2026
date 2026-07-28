from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from verify_arithmetic_knowledge_base import (  # noqa: E402
    KnowledgeBaseError,
    validate_files,
)
from verify_lean_fta import verify_metadata  # noqa: E402


CATALOG = ROOT / "research" / "arithmetic-library" / "catalog.json"
SOURCES = ROOT / "research" / "arithmetic-library" / "source-register.json"


def _catalog() -> dict[str, object]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def _write_catalog(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _validate(catalog: Path = CATALOG) -> dict[str, int]:
    return validate_files(catalog, SOURCES, repository_root=ROOT)


def test_arithmetic_knowledge_catalog_validates_against_production_peano() -> None:
    assert _validate() == {
        "lemmas": 190,
        "domains": 10,
        "companion_artifacts": 1,
        "blocked_by_language": 4,
        "checked_existing": 23,
        "checked_m20": 160,
        "planned_expressible": 3,
    }


def test_catalog_covers_every_domain_status_and_runtime_theorem() -> None:
    catalog = _catalog()
    lemmas = catalog["lemmas"]
    assert isinstance(lemmas, list)
    assert {lemma["domain"] for lemma in lemmas} == set(catalog["domain_order"])
    assert {lemma["status"] for lemma in lemmas} == set(catalog["statuses"])

    from peano_lab.library.theorems import names

    checked = {
        lemma["peano"]["existing_name"]
        for lemma in lemmas
        if lemma["status"] in {"checked_existing", "checked_m20"}
    }
    assert checked == set(names())


def test_catalog_rejects_a_dependency_that_is_not_earlier(tmp_path: Path) -> None:
    catalog = deepcopy(_catalog())
    catalog["lemmas"][2]["dependencies"] = ["future_or_missing"]
    with pytest.raises(KnowledgeBaseError, match="must name an earlier catalog entry"):
        _validate(_write_catalog(tmp_path, catalog))


def test_catalog_rejects_an_unknown_source_id(tmp_path: Path) -> None:
    catalog = deepcopy(_catalog())
    catalog["lemmas"][0]["sources"] = ["invented_source"]
    with pytest.raises(KnowledgeBaseError, match="unknown source id"):
        _validate(_write_catalog(tmp_path, catalog))


def test_catalog_rejects_an_open_planned_statement(tmp_path: Path) -> None:
    catalog = deepcopy(_catalog())
    catalog["lemmas"][2]["peano"]["statement"] = "a = a"
    with pytest.raises(KnowledgeBaseError, match="formula is open"):
        _validate(_write_catalog(tmp_path, catalog))


def test_catalog_rejects_a_checked_statement_mismatch(tmp_path: Path) -> None:
    catalog = deepcopy(_catalog())
    catalog["lemmas"][0]["peano"]["statement"] = "forall n. S n = 0"
    with pytest.raises(KnowledgeBaseError, match="does not match runtime theorem"):
        _validate(_write_catalog(tmp_path, catalog))


def test_catalog_requires_an_explicit_language_blocker(tmp_path: Path) -> None:
    catalog = deepcopy(_catalog())
    blocked = next(
        lemma for lemma in catalog["lemmas"] if lemma["status"] == "blocked_by_language"
    )
    blocked["blocker"] = None
    with pytest.raises(KnowledgeBaseError, match="must be an object"):
        _validate(_write_catalog(tmp_path, catalog))


def test_catalog_rejects_a_missing_companion_artifact(tmp_path: Path) -> None:
    catalog = deepcopy(_catalog())
    catalog["companion_artifacts"][0]["artifact_path"] = "artifacts/missing.lean"
    with pytest.raises(KnowledgeBaseError, match="missing artifact"):
        _validate(_write_catalog(tmp_path, catalog))


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("dependency_revision", "0" * 40),
        ("declarations", ["WrongNamespace.fundamental_theorem_of_arithmetic"]),
        ("allowed_axioms", ["sorryAx"]),
    ],
)
def test_lean_fta_audit_rejects_catalog_metadata_drift(
    tmp_path: Path,
    field: str,
    replacement: object,
) -> None:
    catalog = deepcopy(_catalog())
    catalog["companion_artifacts"][0][field] = replacement
    path = _write_catalog(tmp_path, catalog)
    with pytest.raises(SystemExit, match="catalog metadata drifted"):
        verify_metadata(catalog_path=path)
