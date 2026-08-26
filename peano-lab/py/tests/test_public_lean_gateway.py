"""Public Lean proofs stay same-origin, bounded, and faculty-loopback-only."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[3]
GATEWAY = ROOT / "deploy" / "lean-api" / "index.php"
POLICY = ROOT / "deploy" / "lean-api" / ".htaccess"
LAUNCHER = ROOT / "scripts" / "serve_public_lean.py"


def _launcher() -> ModuleType:
    specification = importlib.util.spec_from_file_location("public_lean_gateway", LAUNCHER)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _dry_run(*arguments: str) -> str:
    result = subprocess.run(
        ["make", "-n", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_php_gateway_targets_only_the_exact_faculty_loopback_tunnel() -> None:
    source = GATEWAY.read_text(encoding="utf-8")

    assert "declare(strict_types=1);" in source
    assert "HYDRA_API_PREFIX = '/api/lean-strands'" in source
    assert "HYDRA_FACULTY_HOST = 'bnaskrecki.faculty.wmi.amu.edu.pl'" in source
    assert "HYDRA_TUNNEL_HOST = '127.0.0.1'" in source
    assert "HYDRA_TUNNEL_PORT = 18787" in source
    assert "HYDRA_SERVICE_HOST = '127.0.0.1:8787'" in source
    assert "HYDRA_MAX_REQUEST_BYTES = 16384" in source
    assert "HYDRA_MAX_RESPONSE_BYTES = 67108864" in source
    assert "HYDRA_MAILBOX_SCHEMA = 'peano-lean-mailbox-v1'" in source
    assert "dirname(__DIR__, 3) . '/.hydra-lean-mailbox'" in source
    assert "($permissions & 0777) !== 0700" in source
    assert "& 0777) !== 0600" in source
    assert "hash_equals($record['body_sha256']" in source
    assert "'.request.json'" in source
    assert "'.response.json'" in source
    assert "'.body'" in source
    assert "stream_socket_client(" in source
    assert "'tcp://' . HYDRA_TUNNEL_HOST . ':' . HYDRA_TUNNEL_PORT" in source
    assert "[0-9a-f]{32}" in source
    assert "Cross-origin Lean proof requests are forbidden." in source
    assert "Cross-site Lean proof mutations are forbidden." in source
    assert "Only one opaque proof-job identifier accepts DELETE." in source
    assert "Use bounded job-status polling" in source
    assert "make lean-public" in source
    for unsafe in ("$_GET['host']", "$_GET['url']", "shell_exec(", "passthru(", "exec("):
        assert unsafe not in source


def test_php_gateway_rewrites_only_inside_its_dedicated_api_directory() -> None:
    policy = POLICY.read_text(encoding="utf-8")

    assert "DirectoryIndex index.php" in policy
    assert "RewriteRule ^ index.php [QSA,L]" in policy
    assert 'Header always set Cache-Control "no-store, max-age=0"' in policy
    assert "ProxyPass" not in policy
    assert "public_html/proofs" not in policy


def test_public_gateway_staging_is_local_and_isolated() -> None:
    output = _dry_run("stage-lean-api")

    assert 'rm -rf "_deploy/lean-api"' in output
    assert 'deploy/lean-api/.htaccess "_deploy/lean-api/.htaccess"' in output
    assert 'deploy/lean-api/index.php "_deploy/lean-api/index.php"' in output
    assert 'scripts/public_lean_mailbox.py "_deploy/lean-api/broker.py"' in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def test_gateway_stage_and_remote_destinations_cannot_be_widened() -> None:
    output = _dry_run(
        "STAGELEANAPI=/tmp/unsafe",
        "LEANAPI=~/public_html",
        "deploy-lean-api",
    )

    assert "/tmp/unsafe" not in output
    assert 'rm -rf "_deploy/lean-api"' in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/api/lean-strands/" in output
    assert "chmod 755 ~/public_html/api ~/public_html/api/lean-strands" in output
    assert "chmod 700 ~/.hydra-lean-mailbox" in output
    assert "chmod 600 ~/.hydra-lean-mailbox/broker.py" in output
    assert "lts-faculty.wmi.amu.edu.pl:~/public_html/\n" not in output


def test_public_proof_deployment_stages_selector_and_installs_gateway_first() -> None:
    output = _dry_run("deploy-proofs")

    assert "scripts/stage_public_lean_selector.py" in output
    assert '--root "_deploy/proofs"' in output
    assert '--api-url ""' in output
    assert "~/public_html/api/lean-strands" in output
    gateway = output.index('rsync -avz "_deploy/lean-api/.htaccess"')
    proofs = output.index('rsync -avz --delete "_deploy/proofs/"')
    assert gateway < proofs


def test_explicit_external_https_service_is_passed_only_to_staged_selector() -> None:
    output = _dry_run(
        "PEANO_LEAN_PUBLIC_API=https://lean.example.org/api/lean-strands",
        "stage-proofs",
    )

    assert '--api-url "https://lean.example.org/api/lean-strands"' in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def test_public_launcher_reuses_an_existing_verified_loopback_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launcher = _launcher()
    monkeypatch.setattr(launcher, "_local_config", lambda **_kwargs: True)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("an existing verified local service must not be replaced")

    monkeypatch.setattr(launcher.subprocess, "Popen", forbidden)

    assert launcher._start_service(2.0) is None


def test_public_ssh_tunnel_is_exactly_remote_loopback_to_local_loopback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launcher = _launcher()
    captured: dict[str, object] = {}
    sentinel = object()

    def fake_process(arguments: list[str], **kwargs: object) -> object:
        captured["arguments"] = arguments
        captured["kwargs"] = kwargs
        return sentinel

    monkeypatch.setattr(launcher.subprocess, "Popen", fake_process)

    assert launcher._start_tunnel("lts-faculty.wmi.amu.edu.pl") is sentinel
    arguments = captured["arguments"]
    assert isinstance(arguments, list)
    assert arguments[:2] == ["ssh", "-T"]
    assert "BatchMode=yes" in arguments
    assert "ExitOnForwardFailure=yes" in arguments
    assert "ServerAliveInterval=30" in arguments
    assert "ServerAliveCountMax=3" in arguments
    assert "127.0.0.1:18787:127.0.0.1:8787" in arguments
    assert arguments[-2] == "lts-faculty.wmi.amu.edu.pl"
    assert arguments[-1] == (
        "python3 -u ~/.hydra-lean-mailbox/broker.py "
        "--directory ~/.hydra-lean-mailbox --upstream-port 18787"
    )
    assert captured["kwargs"]["start_new_session"] is True


@pytest.mark.parametrize("host", ("", "faculty host", "faculty\nexample"))
def test_public_ssh_tunnel_rejects_unsafe_hostnames(host: str) -> None:
    with pytest.raises(RuntimeError, match="hostname"):
        _launcher()._start_tunnel(host)


def test_public_make_targets_preserve_checked_browser_workflow() -> None:
    service = _dry_run("lean-public")
    checker = _dry_run("lean-public-check")

    assert "python3 scripts/serve_public_lean.py" in service
    assert '--ssh-host "lts-faculty.wmi.amu.edu.pl"' in service
    assert "scripts/check_lean_browser.py" in checker
    assert '--base-url "https://bnaskrecki.faculty.wmi.amu.edu.pl"' in checker
    assert '--site-url "https://bnaskrecki.faculty.wmi.amu.edu.pl"' in checker


def test_public_launcher_keeps_tls_verification_when_system_ca_store_is_missing() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "ssl.create_default_context()" in source
    assert "ssl.create_default_context(cafile=certifi.where())" in source
    assert "context=context" in source
    assert "_create_unverified_context" not in source
    assert "CERT_NONE" not in source
