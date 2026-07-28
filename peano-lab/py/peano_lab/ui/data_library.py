"""Deterministic terminal views of the checked public theorem ladder."""

from __future__ import annotations

from ..kernel.formulas import pretty_formula
from ..library.lean import LeanExport, export_theorem
from ..library.theorems import THEOREMS, TheoremSpec, get, replay, replay_target


NL = "\r\n"


def _statement(spec: TheoremSpec) -> str:
    theorem = replay(spec.name)
    return pretty_formula(theorem.formula, [])


def script_with_prelude(spec: TheoremSpec) -> tuple[str, ...]:
    """Return the exact curried replay script, including generated intros."""

    return tuple(f"intro {name}" for name in spec.dependencies) + spec.script


def render_index() -> str:
    """List the immutable library in its theorem-ladder order."""

    rows = [
        "Peano Lab checked theorem library",
        "",
    ]
    for spec in THEOREMS:
        rows.append(f"  {spec.name:<30} {_statement(spec)}")
    rows.extend(
        (
            "",
            f"{len(THEOREMS)} scripted theorems; each final closed certificate is kernel-checked.",
            "Open one with `pa lib <name>`; export it with `pa lean <name>`.",
        )
    )
    return NL.join(rows)


def render_theorem(spec: TheoremSpec) -> str:
    """Render one statement, dependency prelude, authored script, and check."""

    checked = replay(spec.name)
    dependencies = ", ".join(spec.dependencies) if spec.dependencies else "none"
    rows = [
        f"{spec.name} — checked theorem",
        "",
        f"Statement: {_statement(spec)}",
        f"Summary: {spec.summary}",
        f"Earlier dependencies: {dependencies}",
    ]
    if spec.dependencies:
        rows.extend(
            (
                "",
                "Temporary curried replay target:",
                f"  {pretty_formula(replay_target(spec), [])}",
                "Generated dependency prelude:",
            )
        )
        rows.extend(f"  intro {name}" for name in spec.dependencies)
    rows.extend(("", "Authored tactic body:"))
    rows.extend(f"  {line}" for line in spec.script)
    composition = (
        "Composition: self-contained Cut nodes carry and kernel-check each dependency proof."
        if spec.dependencies
        else "Composition: direct closed certificate; no dependency-sharing Cut nodes."
    )
    rows.extend(
        (
            "",
            composition,
            f"Independent kernel check: PASS ({checked.proof_nodes} certificate nodes).",
            f"Cross-check: `pa lean {spec.name}`.",
        )
    )
    return NL.join(rows)


def render_request(request: str) -> str:
    """Handle the data-only portion of ``pa lib [name]``."""

    name = request.strip()
    if not name or name.casefold() in {"list", "ls"}:
        return render_index()
    if name.casefold() in {"help", "?"}:
        return NL.join(
            (
                "Peano Lab theorem library",
                "  pa lib                 list the full ladder",
                "  pa lib <name>          show statement and exact tactic script",
                "  pa lean <name>         export a Lean 4 theorem stub",
            )
        )
    spec = get(name)
    if spec is None:
        return f"No library theorem {name!r}. Type `pa lib`."
    return render_theorem(spec)


def lean_export(spec: TheoremSpec) -> LeanExport:
    """Export the exact checked statement and its replay script."""

    theorem = replay(spec.name)
    return export_theorem(
        spec.name,
        theorem.formula,
        spec.script,
        dependencies=spec.dependencies,
    )


def render_lean(request: str) -> str:
    """Render ``pa lean <name>`` code and the exact Live Lean link."""

    name = request.strip()
    if not name:
        return "Usage: pa lean <theorem>; list names with `pa lib`."
    spec = get(name)
    if spec is None:
        return f"No library theorem {name!r}. Type `pa lib`."
    exported = lean_export(spec)
    return NL.join(
        (
            f"Lean 4 cross-check stub — {spec.name}",
            "The statement is translated exactly; `sorry` is an intentional proof stub.",
            "",
            exported.code,
            "",
            "Open this exact code in Live Lean:",
            exported.live_url,
        )
    )


__all__ = [
    "script_with_prelude",
    "render_index",
    "render_theorem",
    "render_request",
    "lean_export",
    "render_lean",
]
