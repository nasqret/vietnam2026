"""Integrity and leakage boundary for the M20-refreshed corpus release."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
CORPUS = REPO / "peano-lab" / "corpus"
STEP_FIELDS = (
    "v",
    "session",
    "step",
    "goals_before",
    "focus",
    "tactic",
    "goals_after",
    "status",
    "error",
)
RELEASE_ARTIFACT_SHA256 = {
    "train.jsonl": "4e0053e1da89a32043cdfad98e6e6924ce19a6748a914c55095308f48dd2ad54",
    "val.jsonl": "abe0aa84de861aae9a72a173fd1114cf0a99114a8f4f9a6d6019fb3433d94e69",
    "stats.json": "68affad0cd91e0ad4fadda28901b083b6e45f4694791aa1d24b42a82183c04ca",
    "generation-manifest.json": "a89a2d2bdbe6362c17ece6b886ab5eba1dbd7af2b04ddd32d86d2fcccdde3d95",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_tree() -> tuple[int, str]:
    digest = hashlib.sha256()
    sources = sorted((REPO / "peano-lab" / "py" / "peano_lab").rglob("*.py"))
    for path in sources:
        relative = path.relative_to(REPO).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return len(sources), digest.hexdigest()


def _load_evaluator():
    script = REPO / "scripts" / "eval_peano_policy.py"
    spec = importlib.util.spec_from_file_location("_release_eval_protocol", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_release_metadata_counts_hashes_and_source_provenance() -> None:
    manifest = json.loads((CORPUS / "generation-manifest.json").read_text("utf-8"))
    stats = json.loads((CORPUS / "stats.json").read_text("utf-8"))
    readme = (CORPUS / "README.md").read_text("utf-8")

    assert manifest["format"] == "peano-lab-trace-generation-manifest"
    assert manifest["version"] == manifest["trace_version"] == 1
    assert manifest["generator_version"] == 2
    assert manifest["run_fingerprint"] == (
        "6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939"
    )
    assert manifest["config"] == {
        "auto_depth": 5,
        "auto_max_nodes": 5000,
        "commuted": 96,
        "ladder_auto": False,
        "ladder_scripts": False,
        "numeric": 96,
        "renamed": 1500,
        "seed": 0,
    }
    assert manifest["provenance"]["runtime"] == {
        "implementation": "CPython",
        "version": "3.10.0",
    }
    assert manifest["counts"] == {
        "controlled_failure_records": 1692,
        "failure_records": 1692,
        "footer_records": 1692,
        "kernel_checked_sessions": 1692,
        "sessions": 1692,
        "sessions_by_kind": {
            "variant_commuted": 96,
            "variant_numeric": 96,
            "variant_renamed": 1500,
        },
        "sessions_by_result": {"qed": 1692},
        "transition_records": 13344,
    }
    assert manifest["raw"] == {
        "bytes": 6215711,
        "encoding": "utf-8",
        "sha256": "c88a05343d27ded77ba871bd3552ddd099817ef78e6fbfa2a959b8a2e2aea306",
    }
    assert all(
        session["kernel_checked"] is True and session["result"] == "qed"
        for session in manifest["sessions"]
    )
    assert all(
        session["session"].startswith(
            f"peano-{manifest['run_fingerprint'][:24]}-"
        )
        for session in manifest["sessions"]
    )
    assert {session["kind"] for session in manifest["sessions"]} == {
        "variant_commuted",
        "variant_numeric",
        "variant_renamed",
    }

    for source in manifest["provenance"]["sources"].values():
        assert _sha256(REPO / source["path"]) == source["sha256"]
    expected_semantic_source_tree = {
        "root": "peano-lab/py/peano_lab",
        "pattern": "**/*.py",
        "files": 32,
        "sha256": "55a6e70ce5a3ffe855866beb04b7441a85c58d6ac7c7bb9de727d1fefe14d250",
    }
    assert manifest["provenance"]["semantic_source_tree"] == (
        expected_semantic_source_tree
    )
    tree_files, tree_sha256 = _semantic_tree()
    assert {
        "root": "peano-lab/py/peano_lab",
        "pattern": "**/*.py",
        "files": tree_files,
        "sha256": tree_sha256,
    } == expected_semantic_source_tree

    assert stats["source"]["sessions"] == 1692
    assert stats["source"]["transitions"] == 13344
    assert stats["source"]["canonical_sessions_sha256"] == (
        "b2444c3e8c2ed5bce118f81305d638fd337a9ba232a42666c08336467f571cac"
    )
    assert stats["deduplication"]["unique_transitions"] == 13344
    assert stats["deduplication"]["duplicates_removed"] == 0
    assert stats["splits"]["train"] == {
        "sessions": 1683,
        "records": 13326,
        "sha256": RELEASE_ARTIFACT_SHA256["train.jsonl"],
    }
    assert stats["splits"]["val"] == {
        "sessions": 9,
        "records": 18,
        "sha256": RELEASE_ARTIFACT_SHA256["val.jsonl"],
    }
    assert stats["theorem_coverage"]["source_count"] == 99
    assert stats["theorem_coverage"]["train_count"] == 90
    assert stats["theorem_coverage"]["val_count"] == 9
    assert all(
        formula.startswith("∀ x. (")
        for formula in stats["theorem_coverage"]["val"]
    )
    assert stats["outcomes"]["total"] >= 10_000
    assert stats["outcomes"] == {
        "ok": 11652,
        "error": 1692,
        "total": 13344,
        "failure_ratio": 0.12679856115107913,
    }
    assert stats["tactic_distribution"]["norm_num now"] == 96
    assert stats["tactic_distribution"]["norm_num"] == 96
    for split in ("train", "val"):
        assert _sha256(CORPUS / f"{split}.jsonl") == stats["splits"][split]["sha256"]
    for artifact, expected_sha256 in RELEASE_ARTIFACT_SHA256.items():
        assert _sha256(CORPUS / artifact) == expected_sha256
        assert expected_sha256 in readme
    assert manifest["raw"]["sha256"] in readme


def test_release_rows_keep_v1_schema_are_unique_and_omit_heldout_goals() -> None:
    evaluator = _load_evaluator()
    heldout = {
        f"⊢ {evaluator._parse_closed_goal(goal)[2]}"
        for goal in evaluator.DEFAULT_HELD_OUT_GOALS
    }
    semantic: set[str] = set()
    counts = {"train": 0, "val": 0}
    numerical = {"norm_num now": 0, "norm_num": 0}

    for split in ("train", "val"):
        with (CORPUS / f"{split}.jsonl").open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                counts[split] += 1
                assert tuple(row) == STEP_FIELDS
                assert row["v"] == 1
                assert row["status"] in {"ok", "error"}
                if row["status"] == "error":
                    assert row["goals_after"] == row["goals_before"]
                    assert isinstance(row["error"], str) and row["error"]
                else:
                    assert row["error"] is None
                assert heldout.isdisjoint(row["goals_before"])
                assert heldout.isdisjoint(row["goals_after"])
                if row["tactic"] in numerical:
                    numerical[row["tactic"]] += 1
                if row["tactic"] == "norm_num now":
                    assert row["status"] == "error"
                    assert row["error"] == "`norm_num` takes no arguments."
                if row["tactic"] == "norm_num":
                    assert row["status"] == "ok"

                identity = json.dumps(
                    [row[field] for field in STEP_FIELDS if field not in {"session", "step"}],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                assert identity not in semantic
                semantic.add(identity)

    assert counts == {"train": 13326, "val": 18}
    assert numerical == {"norm_num now": 96, "norm_num": 96}
    assert len(semantic) == 13344
