"""Public proof hosting stays isolated, authenticated, and resource bounded."""

from __future__ import annotations

import ast
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts" / "public_lean_tunnel.py"
SPEC = importlib.util.spec_from_file_location("hydra_public_lean_tunnel", SOURCE)
assert SPEC is not None and SPEC.loader is not None
PUBLIC = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PUBLIC
SPEC.loader.exec_module(PUBLIC)


def _dry_run(target: str, *assignments: str) -> str:
    result = subprocess.run(
        ["make", "-n", *assignments, target],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _configuration(**changes: object) -> dict[str, object]:
    return {
        "schema": "peano-lean-strand-service-v1",
        "public_host": False,
        "single_worker": True,
        "max_concurrent_jobs": 1,
        "independent_lean_verification": True,
        "max_memory_mib": 1024,
        "max_live_source_bytes": 1048576,
        **changes,
    }


class _Response:
    def __init__(self, payload: bytes) -> None:
        self._stream = io.BytesIO(payload)

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        self._stream.close()

    def read(self, size: int) -> bytes:
        return self._stream.read(size)


def test_public_gateway_has_its_own_fixed_remote_and_stage_directories() -> None:
    output = _dry_run("deploy-lean-api")

    assert 'rm -rf "_deploy/lean-api"' in output
    assert 'cp deploy/lean-api/.htaccess "_deploy/lean-api/.htaccess"' in output
    assert 'cp deploy/lean-api/index.php "_deploy/lean-api/index.php"' in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/api/lean-strands/" in output
    assert "~/public_html/proofs/" not in output


def test_public_gateway_delete_targets_cannot_be_widened() -> None:
    output = _dry_run(
        "deploy-lean-api",
        "STAGELEANAPI=/tmp/unsafe",
        "LEANAPI=~/public_html",
    )

    assert "/tmp/unsafe" not in output
    assert 'rm -rf "_deploy/lean-api"' in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/api/lean-strands/" in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/\n" not in output


def test_public_proof_deployment_installs_both_isolated_surfaces() -> None:
    output = _dry_run("deploy-lean-public")

    assert "python3 -B scripts/stage_constructive_research_publication_v33.py" in output
    # The current Python stager applies the unchanged selector implementation;
    # the historical shell-only staging command is no longer the public entry.
    source = (ROOT / "scripts/stage_constructive_research_publication_v33.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert any(isinstance(node, ast.Import) and any(
        name.name == "stage_public_lean_selector" and name.asname == "selector" for name in node.names
    ) for node in tree.body)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    selection = ast.unparse(functions["_selector_bytes"])
    inventory = ast.unparse(functions["source_inventory"])
    assert "selector._candidate(Path(name), Path(name))" in selection
    assert "selector.CLOSING_HEAD.search(raw)" in selection
    assert "insertion = selector._overlay(selector._api_url(api_url))" in inventory
    assert "_selector_bytes(destination, payload, insertion)" in inventory
    assert "read(selector.SOURCE / name)" in inventory
    payload = "rsync -avz --exclude '/index.html' _deploy/proofs-v33/ lts-faculty.wmi.amu.edu.pl:~/public_html/proofs/"
    index = "rsync -avz _deploy/proofs-v33/index.html lts-faculty.wmi.amu.edu.pl:~/public_html/proofs/index.html"
    assert output.index(payload) < output.index(index)
    assert "--delete" not in output
    assert "deploy/lean-api/index.php" in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/api/lean-strands/" in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/proofs/" in output


def test_faculty_gateway_never_accepts_a_caller_selected_upstream() -> None:
    gateway = (ROOT / "deploy" / "lean-api" / "index.php").read_text(encoding="utf-8")

    assert "const HYDRA_FACULTY_HOST = 'bnaskrecki.faculty.wmi.amu.edu.pl';" in gateway
    assert "const HYDRA_TUNNEL_HOST = '127.0.0.1';" in gateway
    assert "const HYDRA_TUNNEL_PORT = 18787;" in gateway
    assert "const HYDRA_SERVICE_HOST = '127.0.0.1:8787';" in gateway
    assert "const HYDRA_MAX_REQUEST_BYTES = 16384;" in gateway
    assert "[0-9a-f]{32}" in gateway
    assert "Cross-origin Lean proof requests are forbidden" in gateway
    assert "$_GET['url']" not in gateway
    assert "shell_exec(" not in gateway
    assert "exec(" not in gateway


def test_cross_host_mailbox_stays_private_and_authenticated() -> None:
    gateway = (ROOT / "deploy" / "lean-api" / "index.php").read_text(encoding="utf-8")

    assert "dirname(__DIR__, 3) . '/.hydra-lean-mailbox'" in gateway
    assert "HYDRA_MAILBOX_SCHEMA = 'peano-lean-mailbox-v1'" in gateway
    assert "($permissions & 0777) !== 0700" in gateway
    assert "@chmod($temporary, 0600)" in gateway
    assert "@fileowner($metadata) !== $owner" in gateway
    assert "@fileowner($payload) !== $owner" in gateway
    assert "hash_equals($record['body_sha256']" in gateway
    assert "bin2hex(random_bytes(16))" in gateway
    assert "@touch($directory)" in gateway
    assert "clearstatcache(true, $directory)" in gateway
    assert "clearstatcache(true, $metadata)" in gateway
    assert "'/public_html/.hydra-lean-mailbox'" not in gateway
    assert "01733" not in gateway


def test_reviewed_public_worker_configuration_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps(_configuration()).encode("utf-8")
    monkeypatch.setattr(PUBLIC, "urlopen", lambda *_args, **_kwargs: _Response(payload))

    actual = PUBLIC._configuration("http://127.0.0.1:8787/api/lean-strands/config")

    assert actual["max_memory_mib"] == 1024
    assert actual["single_worker"] is True


def test_public_https_configuration_keeps_certificate_verification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps(_configuration()).encode("utf-8")
    captured: dict[str, object] = {}
    sentinel = object()

    def fetch(_url: str, **options: object) -> _Response:
        captured.update(options)
        return _Response(payload)

    monkeypatch.setattr(PUBLIC, "urlopen", fetch)
    monkeypatch.setattr(PUBLIC, "_verified_https_context", lambda: sentinel)

    actual = PUBLIC._configuration(
        "https://bnaskrecki.faculty.wmi.amu.edu.pl/api/lean-strands/config"
    )

    assert actual["independent_lean_verification"] is True
    assert captured["context"] is sentinel


def test_local_http_configuration_never_requests_an_https_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps(_configuration()).encode("utf-8")
    captured: dict[str, object] = {}

    def fetch(_url: str, **options: object) -> _Response:
        captured.update(options)
        return _Response(payload)

    monkeypatch.setattr(PUBLIC, "urlopen", fetch)
    monkeypatch.setattr(
        PUBLIC,
        "_verified_https_context",
        lambda: (_ for _ in ()).throw(AssertionError("HTTP must not load HTTPS trust")),
    )

    PUBLIC._configuration("http://127.0.0.1:8787/api/lean-strands/config")

    assert "context" not in captured


@pytest.mark.parametrize(
    "change",
    (
        {"schema": "unreviewed"},
        {"public_host": True},
        {"single_worker": False},
        {"max_concurrent_jobs": 2},
        {"independent_lean_verification": False},
        {"max_memory_mib": 2048},
        {"max_memory_mib": True},
        {"max_live_source_bytes": 1048577},
        {"max_live_source_bytes": 0},
    ),
)
def test_public_tunnel_rejects_workers_outside_reviewed_bounds(
    monkeypatch: pytest.MonkeyPatch,
    change: dict[str, object],
) -> None:
    payload = json.dumps(_configuration(**change)).encode("utf-8")
    monkeypatch.setattr(PUBLIC, "urlopen", lambda *_args, **_kwargs: _Response(payload))

    with pytest.raises(PUBLIC.TunnelError, match="single-worker bounds"):
        PUBLIC._configuration("http://127.0.0.1:8787/api/lean-strands/config")


def test_public_tunnel_uses_exact_loopback_forward_and_owner_credentials(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    directory = tmp_path / "runtime"
    directory.mkdir()
    runtime = PUBLIC.RuntimePaths(
        directory,
        directory / "s",
        directory / "state.json",
        directory / "worker.log",
    )
    calls: list[list[str]] = []

    def execute(command: list[str], **_options: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    class Broker:
        pid = 24680

        @staticmethod
        def poll() -> None:
            return None

    monkeypatch.setattr(PUBLIC, "_paths", lambda: runtime)
    monkeypatch.setattr(PUBLIC, "_control_running", lambda _paths: False)
    monkeypatch.setattr(PUBLIC, "_start_worker", lambda _paths: None)
    monkeypatch.setattr(PUBLIC, "_start_broker", lambda _paths: Broker())
    monkeypatch.setattr(PUBLIC, "_wait_for_public_broker", lambda *_args: None)
    monkeypatch.setattr(PUBLIC.subprocess, "run", execute)

    PUBLIC.start()

    command = calls[0]
    assert command[0] == "ssh"
    assert command[-1] == "lts-faculty.wmi.amu.edu.pl"
    assert "127.0.0.1:18787:127.0.0.1:8787" in command
    assert "0.0.0.0" not in " ".join(command)
    assert "-M" in command
    assert "-f" in command
    assert "-N" in command
    assert runtime.state.exists()
    assert json.loads(runtime.state.read_text(encoding="utf-8"))["broker_pid"] == 24680


def test_public_status_recognizes_an_existing_checked_foreground_tunnel(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    directory = tmp_path / "runtime"
    directory.mkdir()
    runtime = PUBLIC.RuntimePaths(
        directory,
        directory / "s",
        directory / "state.json",
        directory / "worker.log",
    )
    checked = _configuration(max_strand_nodes=1024)

    monkeypatch.setattr(PUBLIC, "_paths", lambda: runtime)
    monkeypatch.setattr(PUBLIC, "_control_running", lambda _paths: False)
    monkeypatch.setattr(PUBLIC, "_local_configuration", lambda: dict(checked))
    monkeypatch.setattr(PUBLIC, "_public_configuration", lambda: dict(checked))

    PUBLIC.status()

    output = capsys.readouterr().out
    assert "Public Lean proof service is live" in output
    assert "Single worker · 1024 MiB · 1024 theorem nodes" in output
    assert "existing foreground operator session" in output


def test_public_status_rejects_a_nonmatching_foreground_worker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    directory = tmp_path / "runtime"
    directory.mkdir()
    runtime = PUBLIC.RuntimePaths(
        directory,
        directory / "s",
        directory / "state.json",
        directory / "worker.log",
    )

    monkeypatch.setattr(PUBLIC, "_paths", lambda: runtime)
    monkeypatch.setattr(PUBLIC, "_control_running", lambda _paths: False)
    monkeypatch.setattr(PUBLIC, "_local_configuration", _configuration)
    monkeypatch.setattr(
        PUBLIC,
        "_public_configuration",
        lambda: _configuration(max_memory_mib=512),
    )

    with pytest.raises(PUBLIC.TunnelError, match="exact reviewed local worker"):
        PUBLIC.status()


def test_public_background_tunnel_starts_only_the_private_remote_mailbox(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    directory = tmp_path / "runtime"
    directory.mkdir()
    runtime = PUBLIC.RuntimePaths(
        directory,
        directory / "s",
        directory / "state.json",
        directory / "worker.log",
    )
    commands: list[list[str]] = []
    sentinel = object()

    def launch(command: list[str], **_options: object) -> object:
        commands.append(command)
        return sentinel

    monkeypatch.setattr(PUBLIC.subprocess, "Popen", launch)

    assert PUBLIC._start_broker(runtime) is sentinel
    assert commands[0][-2] == "lts-faculty.wmi.amu.edu.pl"
    assert "python3 -u ~/.hydra-lean-mailbox/broker.py" in commands[0][-1]
    assert "--directory ~/.hydra-lean-mailbox" in commands[0][-1]
    assert "--upstream-port 18787" in commands[0][-1]
    assert "public_html" not in commands[0][-1]


def test_public_tunnel_rejects_unsafe_control_socket(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(PUBLIC, "CONTROL_NAME", "s")
    deployment = tmp_path / "_deploy"
    deployment.mkdir()
    (deployment / PUBLIC.CONTROL_NAME).symlink_to(tmp_path / "untrusted")

    with pytest.raises(PUBLIC.TunnelError, match="symbolic link"):
        PUBLIC._paths(tmp_path)


def test_public_tunnel_cli_does_not_skip_checks_for_status_or_stop() -> None:
    with pytest.raises(SystemExit):
        PUBLIC.main(["status", "--skip-public-check"])
