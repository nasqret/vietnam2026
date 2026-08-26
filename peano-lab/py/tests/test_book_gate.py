"""The executable-book gate routes Lambda and Peano transcripts independently."""

from __future__ import annotations

import subprocess
import sys
import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
GATE = REPO / "scripts" / "verify_book_commands.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("_test_book_gate_module", GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), str(path)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_gate_routes_deep_links_by_lab_and_pa_family(tmp_path: Path) -> None:
    page = tmp_path / "links.md"
    page.write_text(
        "\n".join(
            (
                "# Links",
                "",
                "[PA axioms](https://example.test/peano-lab/?cmd=pa%20axioms)",
                "[PA eval](https://example.test/elsewhere/?cmd=pa%20eval%20%282%20%2B%203%29)",
                "[PA KB alias](https://example.test/peano-lab/?cmd=kb%20pa1)",
                "[Lambda parens](https://example.test/lab-lambda/?cmd=nf%20PLUS%20(MULT%203%204)%200)",
                "[Lambda](https://example.test/lab-lambda/?cmd=church%202)",
            )
        ),
        encoding="utf-8",
    )

    result = _run(page)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "5 deep links" in result.stdout
    assert "lambda: 2 links" in result.stdout
    assert "peano: 3 links" in result.stdout
    assert "all commands replay cleanly" in result.stdout


def test_gate_keeps_each_prefixed_block_in_one_real_session(tmp_path: Path) -> None:
    page = tmp_path / "sessions.md"
    page.write_text(
        """# Sessions

```text
pa> pa prove forall n. n = n
pa> intro n
pa> refl
pa> qed
```

```text
λ> reduce SUCC 0
```
""",
        encoding="utf-8",
    )

    result = _run(page)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 session blocks (5 commands)" in result.stdout
    assert "lambda: 0 links, 1 blocks (1 commands)" in result.stdout
    assert "peano: 0 links, 1 blocks (4 commands)" in result.stdout


def test_gate_does_not_confuse_a_python_fence_with_the_next_session(tmp_path: Path) -> None:
    page = tmp_path / "mixed-fences.md"
    page.write_text(
        """```python
print("not a lab session")
```

```text
pa> pa prove 0 = 0
pa> refl
pa> script
pa> qed
pa> script
```
""",
        encoding="utf-8",
    )

    result = _run(page)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 session blocks (5 commands)" in result.stdout
    assert "peano: 0 links, 1 blocks (5 commands)" in result.stdout


def test_gate_reports_bad_peano_commands_with_the_lab_label(tmp_path: Path) -> None:
    page = tmp_path / "bad.md"
    page.write_text(
        """```text
pa> pa definitely-not-a-command
```
""",
        encoding="utf-8",
    )

    result = _run(page)

    assert result.returncode == 1
    assert "[peano session]" in result.stdout
    assert "Unknown `pa` command" in result.stdout


def test_gate_rejects_failing_tactics_and_failed_qed(tmp_path: Path) -> None:
    page = tmp_path / "bad-proofs.md"
    page.write_text(
        """```text
pa> pa prove 0 = S 0
pa> refl
```

```text
pa> pa prove 0 = S 0
pa> qed
```
""",
        encoding="utf-8",
    )

    result = _run(page)

    assert result.returncode == 1
    assert "Tactic error:" in result.stdout
    assert "QED check failed:" in result.stdout


def test_nonstandalone_pa_tactic_deep_link_is_rejected(tmp_path: Path) -> None:
    page = tmp_path / "bad-link.md"
    page.write_text(
        "[bad](https://example.test/peano-lab/?cmd=refl)\n",
        encoding="utf-8",
    )

    result = _run(page)

    assert result.returncode == 1
    assert "peano deep link is not standalone" in result.stdout


def test_gate_rejects_driver_exception_lines_but_not_explanatory_prose() -> None:
    gate = _load_gate_module()

    for lab in ("lambda", "peano"):
        assert gate._failure("ZeroDivisionError: division by zero", lab) == (
            "ZeroDivisionError: division by zero"
        )
        assert gate._failure("RuntimeException: crashed", lab) == (
            "RuntimeException: crashed"
        )
        assert gate._failure("Exception: boom", lab) == "Exception: boom"
        assert gate._failure(
            "A card may mention ValueError: as an example.", lab
        ) is None
