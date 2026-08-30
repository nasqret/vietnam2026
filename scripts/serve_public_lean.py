#!/usr/bin/env python3
"""Run Hydra's public Lean gateway through a loopback-only SSH reverse tunnel.

The faculty web host runs only a narrowly scoped PHP gateway. Its separate SSH
login node services an owner-only shared-home mailbox through this foreground
SSH session and its loopback-only reverse tunnel. The checked Python repository,
private Lean companion, compiler, and all proof subprocesses remain on this
machine. Stopping this command closes both the foreground mailbox broker and
tunnel, and stops only a local Lean service that this command started itself.
"""

from __future__ import annotations

import argparse
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import signal
import ssl
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "scripts" / "serve_lean_strands.py"
DEFAULT_SSH_HOST = "lts-faculty.wmi.amu.edu.pl"
DEFAULT_PUBLIC_ORIGIN = "https://bnaskrecki.faculty.wmi.amu.edu.pl"
LOCAL_PORT = 8787
REMOTE_PORT = 18787
API_PATH = "/api/lean-strands"
SCHEMA = "peano-lean-strand-service-v1"
REMOTE_BROKER = "~/.hydra-lean-mailbox/broker.py"
REMOTE_MAILBOX = "~/.hydra-lean-mailbox"
SAFE_SSH_HOST = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?\Z")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ssh-host",
        default=DEFAULT_SSH_HOST,
        help="configured faculty SSH host (default: %(default)s)",
    )
    parser.add_argument(
        "--startup-seconds",
        type=float,
        default=20.0,
        help="maximum time allowed for the local bounded Lean service",
    )
    parser.add_argument(
        "--no-public-check",
        action="store_true",
        help="skip the informational HTTPS gateway readiness probe",
    )
    return parser


def _local_config(*, timeout: float = 1.0) -> bool:
    try:
        request = Request(
            f"http://127.0.0.1:{LOCAL_PORT}{API_PATH}/config",
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read(65_537))
        return (
            type(payload) is dict
            and payload.get("schema") == SCHEMA
            and payload.get("single_worker") is True
            and payload.get("max_concurrent_jobs") == 1
            and payload.get("independent_lean_verification") is True
            and payload.get("public_host") is False
            and type(payload.get("max_memory_mib")) is int
            and 1 <= payload["max_memory_mib"] <= 1024
            and type(payload.get("max_live_source_bytes")) is int
            and 1 <= payload["max_live_source_bytes"] <= 1024 * 1024
        )
    except (HTTPException, OSError, URLError, UnicodeError, ValueError):
        return False


def _stop_owned(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=5)


def _start_service(startup_seconds: float) -> subprocess.Popen[bytes] | None:
    if _local_config():
        print("Reusing the existing loopback-only checked Lean service.", flush=True)
        return None
    process: subprocess.Popen[bytes] = subprocess.Popen(
        [
            sys.executable,
            str(SERVICE),
            "--host",
            "127.0.0.1",
            "--port",
            str(LOCAL_PORT),
        ],
        cwd=ROOT,
        start_new_session=True,
    )
    deadline = time.monotonic() + startup_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("the loopback-only Lean proof service failed to start")
        if _local_config(timeout=0.5):
            return process
        time.sleep(0.1)
    _stop_owned(process)
    raise RuntimeError("the bounded Lean proof service exceeded its startup timeout")


def _start_tunnel(host: str) -> subprocess.Popen[bytes]:
    if type(host) is not str or SAFE_SSH_HOST.fullmatch(host) is None:
        raise RuntimeError("the faculty SSH host must be one safe bounded DNS hostname")
    forwarding = f"127.0.0.1:{REMOTE_PORT}:127.0.0.1:{LOCAL_PORT}"
    return subprocess.Popen(
        [
            "ssh",
            "-T",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=10",
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            "ServerAliveInterval=30",
            "-o",
            "ServerAliveCountMax=3",
            "-R",
            forwarding,
            host,
            (
                f"python3 -u {REMOTE_BROKER} "
                f"--directory {REMOTE_MAILBOX} "
                f"--upstream-port {REMOTE_PORT}"
            ),
        ],
        cwd=ROOT,
        start_new_session=True,
    )


def _report_public_status() -> None:
    address = f"{DEFAULT_PUBLIC_ORIGIN}{API_PATH}/config"
    try:
        request = Request(address, headers={"Accept": "application/json"})
        context = ssl.create_default_context()
        if not context.get_ca_certs():
            try:
                import certifi
            except ImportError:
                pass
            else:
                context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=8, context=context) as response:
            payload = json.loads(response.read(65_537))
        if response.status == 200 and payload.get("schema") == SCHEMA:
            print(f"Public verified Lean API is ready: {address}", flush=True)
            return
    except (AttributeError, HTTPException, OSError, URLError, UnicodeError, ValueError):
        pass
    print(
        "The tunnel is active, but the public PHP gateway is not ready yet; "
        "publish it with `make deploy-proofs`.",
        file=sys.stderr,
        flush=True,
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not 1 <= args.startup_seconds <= 120:
        print("Public Lean gateway: startup timeout must be between 1 and 120 seconds.", file=sys.stderr)
        return 2

    service: subprocess.Popen[bytes] | None = None
    tunnel: subprocess.Popen[bytes] | None = None
    try:
        service = _start_service(args.startup_seconds)
        tunnel = _start_tunnel(args.ssh_host)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if tunnel.poll() is not None:
                raise RuntimeError("the faculty SSH reverse tunnel could not be established")
            time.sleep(0.1)

        print("Public Lean proof builder is running.", flush=True)
        print(f"Faculty-side tunnel: 127.0.0.1:{REMOTE_PORT}", flush=True)
        print("Private shared-home proof mailbox: ~/.hydra-lean-mailbox (0700)", flush=True)
        print(f"Private local service: 127.0.0.1:{LOCAL_PORT}", flush=True)
        print(
            f"Theorem explorer: {DEFAULT_PUBLIC_ORIGIN}/proofs/quadratic-reciprocity/"
            "explorer/defined/graph.html?target=PA000F",
            flush=True,
        )
        print("Press Ctrl-C to close the tunnel and stop this public proof worker.", flush=True)
        if not args.no_public_check:
            _report_public_status()

        while True:
            if tunnel.poll() is not None:
                raise RuntimeError("the faculty SSH reverse tunnel disconnected")
            if service is not None and service.poll() is not None:
                raise RuntimeError("the bounded local Lean proof service stopped")
            try:
                tunnel.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                continue
    except KeyboardInterrupt:
        print("\nClosing the public Lean proof tunnel.", flush=True)
        return 0
    except (OSError, RuntimeError) as error:
        print(f"Public Lean gateway: {error}", file=sys.stderr)
        return 1
    finally:
        _stop_owned(tunnel)
        _stop_owned(service)


if __name__ == "__main__":
    raise SystemExit(main())
