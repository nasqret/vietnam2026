"""CI provisioning and bounded pytest IDs preserve the real proof gates."""

from __future__ import annotations

import ast
import os
from pathlib import Path
import re
import subprocess
import sys
import textwrap

import pytest

import ci_peano_pytest as plugin


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
COMPANION_COMMIT = "d2903c8bd507b7e4458b1249f840a4e274befdbf"
COMPANION_TOOLCHAIN = "leanprover/lean4:v4.31.0"


def _job(name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  [\w-]+:\n|\Z)",
        WORKFLOW.read_text(encoding="utf-8"),
    )
    assert match is not None, f"Missing required workflow job: {name}"
    return match.group(1)


def _steps() -> list[str]:
    return re.split(r"(?m)^      - ", _job("peano-lab-shards"))[1:]


def _step(name: str) -> str:
    matches = [step for step in _steps() if step.startswith(f"name: {name}\n")]
    assert len(matches) == 1, f"Missing or duplicated required step: {name}"
    return matches[0]


def _native_guard() -> int | None:
    getter = getattr(sys, "get_int_max_str_digits", None)
    return getter() if getter is not None else None


@pytest.mark.parametrize("bits", (513, 4097, 16385, 100_001))
@pytest.mark.parametrize("negative", (False, True))
def test_large_integer_ids_use_only_sign_and_bit_length(bits: int, negative: bool) -> None:
    magnitude = 1 << (bits - 1)
    value = -magnitude if negative else magnitude
    original = value
    before = _native_guard()
    identifier = plugin.pytest_make_parametrize_id(value)
    assert identifier == f"int-{'neg' if negative else 'pos'}-{bits}bits"
    assert len(identifier) < 32
    assert value is original
    assert value.bit_length() == bits
    assert _native_guard() == before


@pytest.mark.parametrize("value", (0, 1, -1, (1 << 512) - 1, -((1 << 512) - 1)))
def test_small_integer_ids_keep_pytest_defaults(value: int) -> None:
    assert plugin.pytest_make_parametrize_id(value) is None


@pytest.mark.parametrize("value", (None, False, True, "unchanged", 1.5, (1, 2)))
def test_nonintegers_keep_pytest_defaults(value: object) -> None:
    assert plugin.pytest_make_parametrize_id(value) is None


def test_integer_subclasses_and_objects_are_not_inspected_or_rendered() -> None:
    class TrapInt(int):
        def bit_length(self):
            raise AssertionError("a non-exact int was inspected")

        def __repr__(self):
            raise AssertionError("a non-exact int was rendered")

        def __str__(self):
            raise AssertionError("a non-exact int was rendered")

    class TrapObject:
        def __repr__(self):
            raise AssertionError("an unrelated object was rendered")

    assert plugin.pytest_make_parametrize_id(TrapInt(1 << 16384)) is None
    assert plugin.pytest_make_parametrize_id(TrapObject()) is None


def test_plugin_does_not_change_or_bypass_the_native_decimal_guard() -> None:
    before = _native_guard()
    value = 1 << 16384
    assert plugin.pytest_make_parametrize_id(value) == "int-pos-16385bits"
    assert _native_guard() == before
    # Python 3.10.0 predates the guard; CI is explicitly Python 3.12 below.
    # On every guarded interpreter the actual conversion must still fail.
    if before is not None:
        assert 0 < before <= sys.int_info.default_max_str_digits, (
            "Do not disable or raise the native integer-conversion guard in CI"
        )
        with pytest.raises(ValueError, match="limit"):
            str(value)
        assert _native_guard() == before


def test_plugin_has_no_guard_mutations_value_rendering_or_collection_filters() -> None:
    source = Path(plugin.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert [node.name for node in tree.body if isinstance(node, ast.FunctionDef)] == [
        "pytest_make_parametrize_id"
    ]
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert all(
        (isinstance(call.func, ast.Name) and call.func.id == "type")
        or (isinstance(call.func, ast.Attribute) and call.func.attr == "bit_length")
        for call in calls
    )
    assert "set_int_max_str_digits" not in source
    assert "PYTHONINTMAXSTRDIGITS" not in source
    assert "pytest_collection_modifyitems" not in source


@pytest.fixture
def specimen(tmp_path: Path) -> Path:
    source = tmp_path / "test_large_parameter_values.py"
    source.write_text(
        textwrap.dedent(
            """\
            import sys
            import pytest

            BIG = 1 << 16384
            NEXT = BIG + 1
            EXPECTED = {"positive": BIG, "negative": -BIG, "next": NEXT,
                        "small": 7, "boolean": True, "explicit": BIG}
            GUARD = getattr(sys, "get_int_max_str_digits", lambda: None)()

            @pytest.mark.parametrize(("key", "value"), [
                (key, value) for key, value in EXPECTED.items() if key != "explicit"
            ] + [pytest.param("explicit", BIG, id="explicit-large-value")])
            def test_unchanged_values_and_native_guard(key, value):
                assert value is EXPECTED[key]
                assert type(value) is type(EXPECTED[key])
                assert getattr(sys, "get_int_max_str_digits", lambda: None)() == GUARD
                if GUARD is not None:
                    assert 0 < GUARD <= sys.int_info.default_max_str_digits
                    with pytest.raises(ValueError, match="limit"):
                        str(BIG)

            @pytest.mark.parametrize("value", [BIG, NEXT, BIG])
            def test_duplicate_bit_lengths_preserve_every_case(value):
                assert value is BIG or value is NEXT
            """
        ),
        encoding="utf-8",
    )
    return source


def _run_pytest(
    source: Path, *, with_plugin: bool, collect: bool = False
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    inherited = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = str(SCRIPTS) + (os.pathsep + inherited if inherited else "")
    # Only these synthetic subprocesses isolate ambient third-party plugins.
    # The real shard executes its complete, unchanged test inventory.
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment.pop("PYTEST_ADDOPTS", None)
    environment.pop("PYTEST_PLUGINS", None)
    arguments = [sys.executable, "-m", "pytest", "-q", "--tb=short"]
    if with_plugin:
        arguments.extend(("-p", "ci_peano_pytest"))
    if collect:
        arguments.append("--collect-only")
    arguments.extend(("--confcutdir", str(source.parent), str(source)))
    return subprocess.run(
        arguments, cwd=source.parent, env=environment,
        capture_output=True, text=True, timeout=60, check=False,
    )


def test_native_guard_collection_failure_is_reproduced_without_the_plugin(specimen: Path) -> None:
    result = _run_pytest(specimen, with_plugin=False, collect=True)
    if _native_guard() is not None:
        assert result.returncode == 2
        assert "Exceeds the limit" in result.stdout + result.stderr
    else:
        assert result.returncode == 0
    assert len(result.stdout + result.stderr) < 32 * 1024


def test_explicit_plugin_collects_every_case_with_short_unique_ids(specimen: Path) -> None:
    result = _run_pytest(specimen, with_plugin=True, collect=True)
    assert result.returncode == 0, result.stdout + result.stderr
    node_ids = [line for line in result.stdout.splitlines() if "::test_" in line]
    assert len(node_ids) == len(set(node_ids)) == 9
    assert all(len(node_id) < 160 for node_id in node_ids)
    assert any("int-pos-16385bits" in node_id for node_id in node_ids)
    assert any("int-neg-16385bits" in node_id for node_id in node_ids)
    assert any("explicit-large-value" in node_id for node_id in node_ids)
    assert any("small-7" in node_id for node_id in node_ids)
    assert any("boolean-True" in node_id for node_id in node_ids)


def test_explicit_plugin_executes_unchanged_integer_values_and_native_guards(specimen: Path) -> None:
    result = _run_pytest(specimen, with_plugin=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "9 passed" in result.stdout
    assert "skipped" not in result.stdout


def test_full_history_source_and_exact_companion_are_actual_siblings() -> None:
    checkouts = [step for step in _steps() if "uses: actions/checkout@v4" in step]
    assert len(checkouts) == 2
    main, companion = checkouts
    assert "fetch-depth: 0\n" in main
    assert "path: vietnam2026\n" in main
    assert "persist-credentials: false\n" in main
    assert "repository: nasqret/peano-lab-lean\n" in companion
    assert f"ref: {COMPANION_COMMIT}\n" in companion
    assert "path: peano-lab-lean\n" in companion
    assert "persist-credentials: false\n" in companion
    assert "ref: main" not in companion


def test_companion_uses_only_its_dedicated_ssh_key_with_strict_host_verification() -> None:
    step = _step("Check out the independently verified Lean companion")
    assert "ssh-key: ${{ secrets.PEANO_LEAN_READONLY_DEPLOY_KEY }}\n" in step
    assert "ssh-strict: true\n" in step
    assert "persist-credentials: false\n" in step
    assert re.search(r"(?m)^\s+token:", step) is None
    assert "ssh-known-hosts:" not in step  # checkout includes GitHub's pinned host key
    assert "StrictHostKeyChecking=no" not in step


def test_companion_key_is_not_exposed_to_builds_or_untrusted_fork_events() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    job = _job("peano-lab-shards")
    assert "    permissions:\n      contents: read\n" in job
    before_steps = job.split("    steps:\n", 1)[0]
    assert "PEANO_LEAN_READONLY_DEPLOY_KEY" not in before_steps
    assert "pull_request_target" not in workflow
    assert "  pull_request:\n" in workflow
    assert workflow.count("${{ secrets.PEANO_LEAN_READONLY_DEPLOY_KEY }}") == 2
    for step in _steps():
        if "PEANO_LEAN_READONLY_DEPLOY_KEY" in step:
            assert step.startswith((
                "name: Require the read-only companion deploy key\n",
                "name: Check out the independently verified Lean companion\n",
            ))
    names = [part.splitlines()[0] for part in _steps()]
    assert names.index("name: Require the read-only companion deploy key") < names.index(
        "name: Check out the independently verified Lean companion"
    )


@pytest.mark.parametrize("value", (None, "", "synthetic-multiline-key\nnot-a-credential"))
def test_missing_companion_key_fails_closed_without_printing_key_material(value: str | None) -> None:
    step = _step("Require the read-only companion deploy key")
    assert "PEANO_LEAN_READONLY_DEPLOY_KEY: ${{ secrets.PEANO_LEAN_READONLY_DEPLOY_KEY }}\n" in step
    script = textwrap.dedent(step.split("        run: |\n", 1)[1])
    environment = dict(os.environ)
    environment.pop("PEANO_LEAN_READONLY_DEPLOY_KEY", None)
    if value is not None:
        environment["PEANO_LEAN_READONLY_DEPLOY_KEY"] = value
    result = subprocess.run(
        ["bash", "-e", "-c", script], env=environment,
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == (0 if value else 1)
    assert result.stdout == ""
    if value:
        assert result.stderr == ""
        assert value not in result.stdout + result.stderr
    else:
        assert "requires PEANO_LEAN_READONLY_DEPLOY_KEY" in result.stderr
        assert "Fork PRs receive no repository secret" in result.stderr


def test_companion_source_and_declared_toolchain_are_checked_before_build() -> None:
    step = _step("Verify the exact companion source and toolchain pins")
    assert "working-directory: peano-lab-lean\n" in step
    assert f'test "$(git rev-parse HEAD)" = "{COMPANION_COMMIT}"' in step
    assert f'test "$(cat lean-toolchain)" = "{COMPANION_TOOLCHAIN}"' in step
    names = [part.splitlines()[0] for part in _steps()]
    assert names.index("name: Verify the exact companion source and toolchain pins") < names.index(
        "name: Install the pinned companion Lean toolchain"
    ) < names.index("name: Build the independent Lean proof checkers")


def test_exact_toolchain_and_both_compiled_interfaces_are_provisioned() -> None:
    assert f"ELAN_TOOLCHAIN: {COMPANION_TOOLCHAIN}\n" in _job("peano-lab-shards")
    install = _step("Install the pinned companion Lean toolchain")
    assert "https://elan.lean-lang.org/elan-init.sh" in install
    assert "--default-toolchain none --no-modify-path" in install
    assert f'"$HOME/.elan/bin/elan" toolchain install {COMPANION_TOOLCHAIN}' in install
    assert 'echo "$HOME/.elan/bin" >> "$GITHUB_PATH"' in install
    build = _step("Build the independent Lean proof checkers")
    assert "working-directory: peano-lab-lean\n" in build
    assert "          lake build\n" in build
    assert "test -f .lake/build/lib/lean/PeanoLab/Codec.olean" in build
    assert "test -x .lake/build/bin/peano_lab_verify" in build
    assert "test -x .lake/build/bin/peano_lab_bundle_verify" in build


def test_shards_explicitly_load_bounded_ids_without_altering_any_guard_or_selection() -> None:
    job = _job("peano-lab-shards")
    assert 'python-version: "3.12"' in job
    assert "PYTHONPATH: ${{ github.workspace }}/vietnam2026/scripts" in job
    assert "timeout-minutes: 90\n" in job
    assert "fail-fast: false\n" in job
    assert "shard: [0, 1, 2, 3, 4, 5, 6, 7]\n" in job
    step = _step("Run Peano Lab shard ${{ matrix.shard }}")
    assert "working-directory: vietnam2026/peano-lab/py\n" in step
    assert "python ci_shard.py" in step
    assert re.search(r"--count 8\s+--index \$\{\{ matrix\.shard \}\}\s+--\s+-p ci_peano_pytest\s+-q\s+--durations=20", step)
    for forbidden in ("PYTHONINTMAXSTRDIGITS", "set_int_max_str_digits", "continue-on-error", "--ignore", "--deselect", " -k "):
        assert forbidden not in job
    assert re.search(r"(?m)^\s+if:", job) is None
    assert _steps()[-1] == step


def test_ci_runs_its_environment_regressions_and_retains_the_aggregate_gate() -> None:
    step = _step("Check the CI collection and provisioning contracts")
    assert "working-directory: vietnam2026\n" in step
    assert "python -m pytest -q scripts/test_ci_peano_environment.py\n" in step
    aggregate = _job("peano-lab")
    assert "needs: peano-lab-shards\n" in aggregate
    assert 'if [ "$SHARD_RESULT" != "success" ]; then' in aggregate
    assert "exit 1" in aggregate
    for name in ("book", "lean", "lean-fta", "lab-engine", "rocq", "agda"):
        assert _job(name)
