#!/usr/bin/env python3
"""Export and optionally verify a completed Lean theorem from a Peano proof."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.library.lean_certified import (  # noqa: E402
    export_checked_bundle_theorem,
    export_checked_theorem,
)
from peano_lab.library.proof_bundle import (  # noqa: E402
    DEFAULT_BUNDLE_LIMITS,
    decode_proof_bundle,
)
from peano_lab.library.theorems import get, replay  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Translate one independently checked Peano theorem into a complete "
            "Lean 4 theorem through the verified certificate checker."
        )
    )
    parser.add_argument("theorem", help="exact public Peano theorem name")
    parser.add_argument(
        "--proof-bundle",
        type=Path,
        help="translate this complete canonical self-contained proof DAG instead",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the generated Lean module to this path; default prints stdout",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow replacement of an explicitly selected existing output file",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="typecheck the emitted complete theorem inside the Lean companion",
    )
    parser.add_argument(
        "--lean-project",
        type=Path,
        default=ROOT.parent / "peano-lab-lean",
        help="path to the separately verified Peano Lab Lean project",
    )
    parser.add_argument(
        "--lake",
        type=Path,
        help="explicit installed Lake executable; never downloads a toolchain",
    )
    parser.add_argument(
        "--no-axiom-audit",
        action="store_true",
        help="omit the final Lean axiom-dependency report",
    )
    parser.add_argument(
        "--max-memory-mib",
        type=int,
        default=1536,
        help="bound the Lean verifier's own memory to this many MiB (default: 1536)",
    )
    parser.add_argument(
        "--max-verify-seconds",
        type=int,
        default=180,
        help="terminate the complete Lean process group after this many seconds (default: 180)",
    )
    return parser


def _lake_binary(project: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        if not candidate.is_file():
            raise ValueError(f"Lake executable does not exist: {candidate}")
        return candidate

    installed = Path.home() / ".elan" / "toolchains"
    pinned = project / "lean-toolchain"
    preferred: list[Path] = []
    if pinned.is_file():
        identity = pinned.read_text(encoding="utf-8").strip()
        encoded = identity.replace("/", "--").replace(":", "---")
        preferred.append(installed / encoded / "bin" / "lake")

    def version_key(path: Path) -> tuple[int, int, int, int]:
        match = re.search(r"v(\d+)\.(\d+)\.(\d+)(?:-rc(\d+))?$", path.name)
        if match is None:
            return (-1, -1, -1, -1)
        major, minor, patch, release_candidate = match.groups()
        return (
            int(major),
            int(minor),
            int(patch),
            10_000 if release_candidate is None else int(release_candidate),
        )

    if installed.is_dir():
        for directory in sorted(installed.iterdir(), key=version_key, reverse=True):
            preferred.append(directory / "bin" / "lake")

    for candidate in preferred:
        if candidate.is_file():
            return candidate
    raise ValueError(
        "no installed Lean/Lake toolchain was found; install one or pass --lake"
    )


def _verify(
    module: Path,
    project: Path,
    lake: Path,
    *,
    max_memory_mib: int,
    max_verify_seconds: int,
) -> None:
    if not project.is_dir() or not (project / "PeanoLab" / "Codec.lean").is_file():
        raise ValueError(
            "the Lean project must contain the separately verified PeanoLab.Codec"
        )
    process = subprocess.Popen(
        [
            str(lake),
            "env",
            "lean",
            "-M",
            str(max_memory_mib),
            "-j",
            "1",
            str(module),
        ],
        cwd=project,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=max_verify_seconds)
    except subprocess.TimeoutExpired as exc:
        # Lake is a wrapper around the actual Lean process. Killing only Lake
        # would leave an unbounded orphan behind, so this session is private.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
        raise ValueError(
            f"Lean verification exceeded its {max_verify_seconds}-second limit"
        ) from exc

    if stdout:
        print(stdout, file=sys.stderr, end="")
    if stderr:
        print(stderr, file=sys.stderr, end="")
    if process.returncode != 0:
        raise ValueError("Lean rejected the generated theorem")
    output = stdout + stderr
    if "sorryAx" in output:
        raise ValueError("the generated Lean theorem depends on an incomplete proof")
    if "Lean.trustCompiler" in output:
        raise ValueError("the generated Lean theorem unexpectedly trusts native code")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    specification = get(args.theorem)
    if specification is None and args.proof_bundle is None:
        print(f"Unknown public Peano theorem: {args.theorem!r}", file=sys.stderr)
        return 2

    try:
        if not 64 <= args.max_memory_mib <= 16_384:
            raise ValueError("Lean memory bound must be between 64 and 16384 MiB")
        if not 1 <= args.max_verify_seconds <= 3_600:
            raise ValueError("Lean verification timeout must be between 1 and 3600 seconds")

        if args.proof_bundle is None:
            assert specification is not None
            theorem = replay(specification.name)
            exported = export_checked_theorem(
                specification.name,
                theorem.formula,
                theorem.certificate,
                specification.script,
                dependencies=specification.dependencies,
                include_axiom_audit=not args.no_axiom_audit,
            )
            theorem_name = specification.name
            proof_description = f"{theorem.proof_nodes} proof nodes"
        else:
            source = args.proof_bundle.expanduser().resolve()
            if source.stat().st_size > DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
                raise ValueError("proof bundle exceeds its reviewed canonical byte limit")
            bundle, formula = decode_proof_bundle(source.read_text(encoding="utf-8"))
            if specification is not None:
                checked = replay(specification.name)
                if checked.formula != formula:
                    raise ValueError(
                        "proof-bundle target disagrees with the named public theorem"
                    )
                script = specification.script
                dependencies = specification.dependencies
                theorem_name = specification.name
            else:
                script = ()
                dependencies = ()
                theorem_name = args.theorem
            exported = export_checked_bundle_theorem(
                theorem_name,
                bundle,
                formula,
                script,
                dependencies=dependencies,
                include_axiom_audit=not args.no_axiom_audit,
            )
            proof_description = f"{len(bundle.nodes)} independently checked bundle nodes"

        if args.output is not None:
            output = args.output.expanduser().resolve()
            if output.exists() and not args.force:
                raise ValueError(
                    f"output already exists: {output}; use --force to replace it"
                )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(exported.code + "\n", encoding="utf-8")
            if args.verify:
                project = args.lean_project.expanduser().resolve()
                _verify(
                    output,
                    project,
                    _lake_binary(project, args.lake),
                    max_memory_mib=args.max_memory_mib,
                    max_verify_seconds=args.max_verify_seconds,
                )
            print(
                f"Exported checked Peano theorem {theorem_name!r} "
                f"({proof_description}) to {output}",
                file=sys.stderr,
            )
            return 0

        if args.verify:
            project = args.lean_project.expanduser().resolve()
            with tempfile.TemporaryDirectory(prefix="peano-lean-proof-") as directory:
                module = Path(directory) / "Exported.lean"
                module.write_text(exported.code + "\n", encoding="utf-8")
                _verify(
                    module,
                    project,
                    _lake_binary(project, args.lake),
                    max_memory_mib=args.max_memory_mib,
                    max_verify_seconds=args.max_verify_seconds,
                )
        print(exported.code)
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Peano-to-Lean conversion failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
