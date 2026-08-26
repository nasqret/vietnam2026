#!/usr/bin/env python3
"""Check the Lean FTA companion and its exact declared axiom footprint."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "artifacts" / "lean-fta"
COMPANION_ID = "lean_fta_companion"
MATHLIB_SOURCE_ID = "mathlib_nat_factorization"
MATHLIB_REVISION = "37df177aaa770670452312393d4e84aaad56e7b6"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.23.0"
DECLARATIONS = (
    "ArithmeticFTA.prime_factorization_exists",
    "ArithmeticFTA.prime_factorization_unique",
    "ArithmeticFTA.fundamental_theorem_of_arithmetic",
)
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
AXIOM_LINE = re.compile(r"^'([^']+)' depends on axioms: \[([^]]*)\]$")
TYPE_AUDIT = r"""
example (n : ℕ) (hn : n ≠ 0) :
    ∃ factors : List ℕ,
      (factors.prod = n ∧ ∀ p ∈ factors, Nat.Prime p) ∧
      ∀ other : List ℕ,
        (other.prod = n ∧ ∀ p ∈ other, Nat.Prime p) →
        other.Perm factors :=
  ArithmeticFTA.fundamental_theorem_of_arithmetic n hn
"""


def verify_metadata(
    catalog_path: Path | None = None,
    source_register_path: Path | None = None,
) -> None:
    """Bind catalog claims to the pinned project and audited declarations."""

    if catalog_path is None:
        catalog_path = ROOT / "research/arithmetic-library/catalog.json"
    if source_register_path is None:
        source_register_path = (
            ROOT / "research/arithmetic-library/source-register.json"
        )
    catalog = json.loads(
        catalog_path.read_text(encoding="utf-8")
    )
    companions = {
        item["id"]: item for item in catalog.get("companion_artifacts", [])
    }
    companion = companions.get(COMPANION_ID)
    if companion is None:
        raise SystemExit(f"catalog is missing companion {COMPANION_ID!r}")
    expected_companion = {
        "artifact_path": "artifacts/lean-fta/FTA.lean",
        "source": MATHLIB_SOURCE_ID,
        "dependency_revision": MATHLIB_REVISION,
        "declarations": list(DECLARATIONS),
        "allowed_axioms": ["propext", "Classical.choice", "Quot.sound"],
    }
    drift = {
        key: (expected, companion.get(key))
        for key, expected in expected_companion.items()
        if companion.get(key) != expected
    }
    if drift:
        raise SystemExit(f"Lean FTA catalog metadata drifted: {drift!r}")

    register = json.loads(
        source_register_path.read_text(encoding="utf-8")
    )
    sources = {item["id"]: item for item in register.get("sources", [])}
    source = sources.get(MATHLIB_SOURCE_ID)
    if source is None or source.get("revision") != MATHLIB_REVISION:
        raise SystemExit("Lean FTA source-register revision drifted")

    toolchain = (PROJECT / "lean-toolchain").read_text(encoding="utf-8").strip()
    if toolchain != LEAN_TOOLCHAIN:
        raise SystemExit(
            f"Lean FTA toolchain drifted: expected {LEAN_TOOLCHAIN!r}, got {toolchain!r}"
        )
    manifest = json.loads(
        (PROJECT / "lake-manifest.json").read_text(encoding="utf-8")
    )
    mathlib = next(
        (
            package
            for package in manifest.get("packages", [])
            if package.get("name") == "mathlib"
        ),
        None,
    )
    if mathlib is None or mathlib.get("rev") != MATHLIB_REVISION:
        raise SystemExit(
            "Lean FTA lake manifest is not pinned to the cataloged Mathlib revision"
        )
    lakefile = (PROJECT / "lakefile.toml").read_text(encoding="utf-8")
    if f'rev = "{MATHLIB_REVISION}"' not in lakefile:
        raise SystemExit("Lean FTA lakefile revision drifted from the manifest")


def main() -> None:
    verify_metadata()
    build = subprocess.run(
        ["lake", "build", "FTA"],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    if build.returncode != 0:
        raise SystemExit(build.stdout + build.stderr)

    source = "import FTA\n\n" + TYPE_AUDIT + "\n" + "\n".join(
        f"#print axioms {declaration}" for declaration in DECLARATIONS
    ) + "\n"
    with tempfile.TemporaryDirectory(prefix="vietnam2026-fta-") as directory:
        check_file = Path(directory) / "AxiomAudit.lean"
        check_file.write_text(source, encoding="utf-8")
        completed = subprocess.run(
            ["lake", "env", "lean", str(check_file)],
            cwd=PROJECT,
            text=True,
            capture_output=True,
            check=False,
        )

    output = completed.stdout + completed.stderr
    if completed.returncode != 0:
        raise SystemExit(output)
    if "sorryAx" in output:
        raise SystemExit("Lean FTA companion unexpectedly depends on sorryAx")

    expected = {declaration: ALLOWED_AXIOMS for declaration in DECLARATIONS}
    actual: dict[str, frozenset[str]] = {}
    for line in output.splitlines():
        match = AXIOM_LINE.fullmatch(line.strip())
        if match is None:
            continue
        names = frozenset(
            name.strip() for name in match.group(2).split(",") if name.strip()
        )
        actual[match.group(1)] = names
    if actual != expected:
        raise SystemExit(
            "Lean FTA axiom footprint drifted"
            f"\nexpected: {expected!r}"
            f"\nactual: {actual!r}"
        )

    rendered = "[" + ", ".join(sorted(ALLOWED_AXIOMS)) + "]"
    print(
        "verified Lean FTA existence and uniqueness; exact axiom footprint: "
        + rendered
    )


if __name__ == "__main__":
    main()
