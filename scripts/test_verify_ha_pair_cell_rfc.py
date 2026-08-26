"""Static and bounded-semantic audit for RFC HA-K3-PAIR-1."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.kernel.formulas import parse_formula_with_names  # noqa: E402


RFC_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "arithmetic-library"
    / "ha-canonical-pair-cell-rfc-v1.md"
)

TEMPLATES = {
    "HA-K3-PAIR-D01": (
        "code = (left + right) * S (left + right) + (right + right)"
    ),
    "HA-K3-PAIR-D02": (
        "exists left right. code = (left + right) * S (left + right) + "
        "(right + right)"
    ),
    "HA-K3-PAIR-D03": (
        "exists right. code = (left + right) * S (left + right) + "
        "(right + right)"
    ),
    "HA-K3-PAIR-D04": (
        "exists left. code = (left + right) * S (left + right) + "
        "(right + right)"
    ),
    "HA-K3-PAIR-D05": "code = 0",
    "HA-K3-PAIR-D06": (
        "code = S ((head + tail) * S (head + tail) + (tail + tail))"
    ),
    "HA-K3-PAIR-D07": (
        "exists head tail. code = S ((head + tail) * S (head + tail) + "
        "(tail + tail))"
    ),
    "HA-K3-PAIR-D08": (
        "entry = (key + value) * S (key + value) + (value + value)"
    ),
}

EXPECTED_SHA256 = {
    "HA-K3-PAIR-D01":
        "4a1f7584e17e14e5895e51feefb6083707c52d080277000a423af9edb75fc3a1",
    "HA-K3-PAIR-D02":
        "b4ccb897c33781d571f092f9fbce98963fedeab1733b7755e7622c8dcaef8bb5",
    "HA-K3-PAIR-D03":
        "934ba249236665486bc18c7d734f04a6b126793a4d0a3a2371476d62200b5762",
    "HA-K3-PAIR-D04":
        "ee497668c0a9e865d52102fd0bb2840154494df13984cc3d77a165a77458024b",
    "HA-K3-PAIR-D05":
        "90dfaef5b4215cce02fe969e7a5c252e963bd35509fc68e9116277c0928fd3d6",
    "HA-K3-PAIR-D06":
        "43b3520acd7e6b372169fe2e9636b72214359ee09c432181d38eb741ddb69e34",
    "HA-K3-PAIR-D07":
        "7313b358853482a4b4254bee45fa7bced9921cc3af56cc357eed877831e9e173",
    "HA-K3-PAIR-D08":
        "9d7cee278c784dd602f815c4feb3e3155953e91beeab3a358fbd85c6b05e1aab",
}

BINDERS = {
    "HA-K3-PAIR-D01": "forall code left right. ",
    "HA-K3-PAIR-D02": "forall code. ",
    "HA-K3-PAIR-D03": "forall code left. ",
    "HA-K3-PAIR-D04": "forall code right. ",
    "HA-K3-PAIR-D05": "forall code. ",
    "HA-K3-PAIR-D06": "forall code head tail. ",
    "HA-K3-PAIR-D07": "forall code. ",
    "HA-K3-PAIR-D08": "forall entry key value. ",
}


def _pair(left: int, right: int) -> int:
    shell = left + right
    return shell * (shell + 1) + 2 * right


def _cell(head: int, tail: int) -> int:
    return _pair(head, tail) + 1


def test_pair_cell_templates_parse_and_match_frozen_hashes() -> None:
    assert {
        name: sha256(template.encode()).hexdigest()
        for name, template in TEMPLATES.items()
    } == EXPECTED_SHA256

    for name, template in TEMPLATES.items():
        _, free_names = parse_formula_with_names(BINDERS[name] + template)
        assert not free_names
        assert all(
            marker not in template
            for marker in ("BetaAt", "Product", "CRT", "/", "%", "<")
        )


def test_pair_cell_rfc_contains_exact_templates_and_receipts() -> None:
    source = RFC_PATH.read_text(encoding="utf-8")
    for name, template in TEMPLATES.items():
        assert f"```text\n{template}\n```" in source
        assert f"| `{name}` | `{EXPECTED_SHA256[name]}` |" in source

    assert "## 7. The uniform-list blocker" in source
    normalized = " ".join(source.split())
    assert (
        "does **not** claim that pairing alone defines arbitrary-length lists"
        in normalized
    )
    assert "### D09 `ListValid" not in source


def test_doubled_cantor_pair_and_cell_bounded_oracle() -> None:
    observed: dict[int, tuple[int, int]] = {}
    for left in range(33):
        for right in range(33):
            code = _pair(left, right)
            assert code % 2 == 0
            assert code not in observed
            observed[code] = (left, right)

            cell = _cell(left, right)
            assert cell != 0
            assert cell % 2 == 1
            assert left < cell
            assert right < cell

    # Nearby mutations are not the selected representation.
    assert _pair(0, 1) == 4
    assert _pair(1, 0) == 2
    assert _pair(0, 1) != _pair(1, 0)
    assert _cell(0, 0) == 1
