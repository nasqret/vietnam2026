#!/usr/bin/env python3
"""Expose the bounded loopback Lean worker through the reviewed faculty gateway.

The faculty server runs neither Python nor Lean.  One owner-authenticated SSH
reverse forward binds *only* 127.0.0.1 on that server, where the narrow PHP
gateway relays its exact reviewed proof-job routes.  No credentials, source
checkout, companion project, or persistent daemon are deployed there.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import signal
import ssl
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
SSH_HOST = "lts-faculty.wmi.amu.edu.pl"
PUBLIC_ORIGIN = "https://bnaskrecki.faculty.wmi.amu.edu.pl"
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 8787
REMOTE_PORT = 18787
REMOTE_MAILBOX = "~/.hydra-lean-mailbox"
REMOTE_BROKER = REMOTE_MAILBOX + "/broker.py"
API_PATH = "/api/lean-strands/config"
SCHEMA = "peano-lean-public-tunnel-v1"
WORKER_SCHEMA = "peano-lean-strand-service-v1"
MAX_MEMORY_MIB = 1024
MAX_SOURCE_BYTES = 1024 * 1024
CONTROL_NAME = ".hydra-lean-public.sock"
STATE_NAME = ".hydra-lean-public.json"
LOG_NAME = "hydra-lean-public-worker.log"
SAFE_HOST = re.compile(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?\Z")


class TunnelError(RuntimeError):
    """A requested public tunnel cannot preserve its reviewed safety bounds."""


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    directory: Path
    control: Path
    state: Path
    log: Path


def _verified_https_context() -> ssl.SSLContext:
    """Preserve verified HTTPS when framework Python has no system CA store."""

    context = ssl.create_default_context()
    defaults = ssl.get_default_verify_paths()
    if (
        context.get_ca_certs()
        or os.environ.get("SSL_CERT_FILE")
        or os.environ.get("SSL_CERT_DIR")
        or defaults.cafile
        or defaults.capath
    ):
        return context
    try:
        import certifi
    except ImportError as error:
        raise ssl.SSLError("HTTPS requires system trust anchors or installed certifi") from error
    context = ssl.create_default_context(cafile=certifi.where())
    if (
        context.verify_mode != ssl.CERT_REQUIRED
        or not context.check_hostname
        or not context.get_ca_certs()
    ):
        raise ssl.SSLError("the installed certifi bundle provides no verified trust anchors")
    return context


def _paths(root: Path = ROOT) -> RuntimePaths:
    directory = root.resolve() / "_deploy"
    directory.mkdir(mode=0o755, parents=True, exist_ok=True)
    if directory.is_symlink() or not directory.is_dir():
        raise TunnelError("public Lean runtime directory is not a safe real directory")
    control = directory / CONTROL_NAME
    if control.is_symlink():
        raise TunnelError("public Lean control socket cannot be a symbolic link")
    if len(os.fsencode(control)) >= 100:
        raise TunnelError("reviewed SSH control-socket path exceeds the portable Unix limit")
    return RuntimePaths(directory, control, directory / STATE_NAME, directory / LOG_NAME)


def _configuration(url: str, *, timeout: float = 8.0) -> dict[str, Any]:
    try:
        options: dict[str, Any] = {"timeout": timeout}
        if url.startswith("https://"):
            options["context"] = _verified_https_context()
        with urlopen(url, **options) as response:  # noqa: S310 - fixed reviewed origins
            content = response.read(16_385)
    except (HTTPError, OSError, URLError, ValueError) as error:
        raise TunnelError(f"checked Lean endpoint is unavailable: {error}") from error
    if len(content) > 16_384:
        raise TunnelError("checked Lean configuration exceeds its exact response budget")
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeError, ValueError) as error:
        raise TunnelError("checked Lean endpoint returned invalid strict JSON") from error
    if (
        type(payload) is not dict
        or payload.get("schema") != WORKER_SCHEMA
        or payload.get("public_host") is not False
        or payload.get("single_worker") is not True
        or payload.get("max_concurrent_jobs") != 1
        or payload.get("independent_lean_verification") is not True
        or type(payload.get("max_memory_mib")) is not int
        or not 1 <= payload["max_memory_mib"] <= MAX_MEMORY_MIB
        or type(payload.get("max_live_source_bytes")) is not int
        or not 1 <= payload["max_live_source_bytes"] <= MAX_SOURCE_BYTES
    ):
        raise TunnelError("Lean worker did not authenticate its reviewed single-worker bounds")
    return payload


def _local_configuration() -> dict[str, Any]:
    return _configuration(f"http://{LOCAL_HOST}:{LOCAL_PORT}{API_PATH}", timeout=3.0)


def _public_configuration() -> dict[str, Any]:
    return _configuration(PUBLIC_ORIGIN + API_PATH, timeout=12.0)


def _ssh_base(control: Path) -> list[str]:
    if SAFE_HOST.fullmatch(SSH_HOST) is None:
        raise TunnelError("faculty SSH hostname is not a safe literal")
    return [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        "-S", str(control),
    ]


def _control_running(paths: RuntimePaths) -> bool:
    if not paths.control.exists():
        return False
    result = subprocess.run(
        _ssh_base(paths.control) + ["-O", "check", SSH_HOST],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    return result.returncode == 0


def _read_state(paths: RuntimePaths) -> dict[str, Any]:
    if not paths.state.exists():
        return {}
    if paths.state.is_symlink() or not paths.state.is_file():
        raise TunnelError("public Lean runtime state is not a safe ordinary file")
    if paths.state.stat().st_size > 4096:
        raise TunnelError("public Lean runtime state exceeds its reviewed size limit")
    try:
        state = json.loads(paths.state.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise TunnelError("public Lean runtime state is invalid") from error
    if type(state) is not dict or state.get("schema") != SCHEMA:
        raise TunnelError("public Lean runtime state has the wrong exact schema")
    return state


def _write_state(
    paths: RuntimePaths,
    *,
    worker_pid: int | None,
    broker_pid: int | None,
) -> None:
    if worker_pid is not None and (type(worker_pid) is not int or worker_pid <= 0):
        raise TunnelError("owned Lean worker process identifier is invalid")
    if broker_pid is not None and (type(broker_pid) is not int or broker_pid <= 0):
        raise TunnelError("owned faculty mailbox process identifier is invalid")
    payload = {
        "schema": SCHEMA,
        "ssh_host": SSH_HOST,
        "local_port": LOCAL_PORT,
        "remote_port": REMOTE_PORT,
        "worker_pid": worker_pid,
        "broker_pid": broker_pid,
    }
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=".hydra-lean-public-",
        dir=paths.directory,
        delete=False,
    ) as output:
        temporary = Path(output.name)
        os.chmod(temporary, 0o600)
        json.dump(payload, output, sort_keys=True, separators=(",", ":"))
        output.write("\n")
    temporary.replace(paths.state)


def _start_worker(paths: RuntimePaths) -> int | None:
    try:
        _local_configuration()
        return None
    except TunnelError:
        pass
    if paths.log.is_symlink():
        raise TunnelError("public Lean worker log cannot be a symbolic link")
    with paths.log.open("ab") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "scripts" / "serve_lean_strands.py"),
                "--host", LOCAL_HOST,
                "--port", str(LOCAL_PORT),
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise TunnelError(
                "bounded local Lean worker exited before it became ready; "
                f"inspect {paths.log}"
            )
        try:
            _local_configuration()
            return process.pid
        except TunnelError:
            time.sleep(0.2)
    process.terminate()
    raise TunnelError("bounded local Lean worker did not start within 20 seconds")


def _stop_owned_worker(pid: object) -> None:
    if type(pid) is not int or pid <= 0:
        return
    inspected = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    expected = "scripts/serve_lean_strands.py"
    if inspected.returncode != 0 or expected not in inspected.stdout:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return


def _start_broker(paths: RuntimePaths) -> subprocess.Popen[bytes]:
    if paths.log.is_symlink():
        raise TunnelError("public Lean mailbox log cannot be a symbolic link")
    with paths.log.open("ab") as log:
        return subprocess.Popen(
            _ssh_base(paths.control)
            + [
                "-T",
                SSH_HOST,
                (
                    f"python3 -u {REMOTE_BROKER} "
                    f"--directory {REMOTE_MAILBOX} "
                    f"--upstream-port {REMOTE_PORT}"
                ),
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def _wait_for_public_broker(process: subprocess.Popen[bytes], paths: RuntimePaths) -> None:
    deadline = time.monotonic() + 25.0
    previous: TunnelError | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise TunnelError(
                "private faculty mailbox broker stopped before becoming ready; "
                f"inspect {paths.log}"
            )
        try:
            _public_configuration()
            return
        except TunnelError as error:
            previous = error
            time.sleep(0.25)
    raise TunnelError(
        "private faculty mailbox broker did not authenticate its public gateway: "
        + (str(previous) if previous is not None else "timeout")
    )


def start(*, check_public: bool = True) -> None:
    paths = _paths()
    owned = _read_state(paths).get("worker_pid") if paths.state.exists() else None
    if _control_running(paths):
        _local_configuration()
        if check_public:
            _public_configuration()
        print(f"Public Lean proof service is already live: {PUBLIC_ORIGIN}/proofs/")
        return
    if paths.control.exists():
        if not paths.control.is_socket():
            raise TunnelError("refusing to replace a non-socket SSH control path")
        paths.control.unlink()

    owned = _start_worker(paths)
    broker: subprocess.Popen[bytes] | None = None
    command = _ssh_base(paths.control) + [
        "-o", "ExitOnForwardFailure=yes",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "-M", "-f", "-N",
        "-R", f"127.0.0.1:{REMOTE_PORT}:{LOCAL_HOST}:{LOCAL_PORT}",
        SSH_HOST,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=25,
        )
        if result.returncode != 0:
            detail = " ".join(result.stderr.split())[:320]
            raise TunnelError("loopback-only faculty SSH tunnel was rejected: " + detail)
        broker = _start_broker(paths)
        _write_state(paths, worker_pid=owned, broker_pid=broker.pid)
        if check_public:
            _wait_for_public_broker(broker, paths)
    except (OSError, subprocess.TimeoutExpired, TunnelError):
        if _control_running(paths):
            subprocess.run(
                _ssh_base(paths.control) + ["-O", "exit", SSH_HOST],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                timeout=15,
            )
        _stop_owned_worker(owned)
        if broker is not None and broker.poll() is None:
            broker.terminate()
        raise
    print(f"Public Lean proof service is live: {PUBLIC_ORIGIN}/proofs/")
    print(f"Faculty gateway: {PUBLIC_ORIGIN}{API_PATH}")
    print("One independently checked worker · 1,024 MiB · owner-private faculty mailbox")


def stop() -> None:
    paths = _paths()
    state = _read_state(paths)
    if _control_running(paths):
        result = subprocess.run(
            _ssh_base(paths.control) + ["-O", "exit", SSH_HOST],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if result.returncode != 0:
            raise TunnelError("reviewed faculty SSH tunnel could not be stopped")
    _stop_owned_worker(state.get("worker_pid"))
    if paths.state.exists():
        paths.state.unlink()
    print("Stopped the public Lean tunnel and its owned local proof worker.")


def status() -> None:
    paths = _paths()
    managed = _control_running(paths)
    local = _local_configuration()
    public = _public_configuration()
    if local != public:
        raise TunnelError("faculty gateway does not expose the exact reviewed local worker")
    print(f"Public Lean proof service is live: {PUBLIC_ORIGIN}/proofs/")
    print(
        f"Single worker · {local['max_memory_mib']} MiB · "
        f"{local.get('max_strand_nodes', '?')} theorem nodes"
    )
    if not managed:
        print("Connection: existing foreground operator session; no managed tunnel is owned.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "stop", "status"))
    parser.add_argument(
        "--skip-public-check",
        action="store_true",
        help="start the reviewed SSH tunnel before publishing its dedicated PHP gateway",
    )
    arguments = parser.parse_args(argv)
    if arguments.skip_public_check and arguments.action != "start":
        parser.error("--skip-public-check is allowed only with start")
    try:
        if arguments.action == "start":
            start(check_public=not arguments.skip_public_check)
        elif arguments.action == "stop":
            stop()
        else:
            status()
    except (OSError, subprocess.SubprocessError, TunnelError) as error:
        print(f"Public Lean service failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
