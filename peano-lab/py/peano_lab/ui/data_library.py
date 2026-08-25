"""Deterministic terminal views of the checked public theorem ladder."""

from __future__ import annotations

from collections import Counter

from ..kernel.formulas import parse_formula_with_names, pretty_formula
from ..library.lean import LeanExport
from ..library.lean_certified import export_checked_theorem
from ..library.theorems import THEOREMS, TheoremSpec, get, replay, replay_target


NL = "\r\n"


def _statement(spec: TheoremSpec) -> str:
    """Render one closed statement without constructing its certificate.

    The library index is an inventory, not a theorem-use boundary.  Replaying
    every certificate merely to list names makes ``pa lib`` scale with the
    transitive proof closure (and would make the QR-sized ladder unusable in a
    browser).  The detail card and ``use`` still call :func:`replay`, so no
    theorem can be consumed or reported as independently checked through this
    lightweight path.
    """

    formula, free_names = parse_formula_with_names(spec.statement)
    if free_names:
        raise ValueError(
            "library theorem statements must be closed; free variable(s): "
            + ", ".join(free_names)
        )
    return pretty_formula(formula, [])


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
            f"{len(THEOREMS)} scripted theorems; each closed certificate is "
            "independently kernel-checked when replayed.",
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


def _alpha_edition():
    """Load the opt-in research channel without changing Stable boot behavior."""

    from ..library import editions_v16

    return editions_v16


def render_alpha_index(*, checked_only: bool = False, include_entries: bool = False) -> str:
    """Inspect immutable Alpha evidence without loading or replaying proof data."""

    alpha = _alpha_edition()
    selected = alpha.edition("alpha")
    counts = Counter(item.evidence.value for item in selected.entries)
    rows = [
        "Peano Lab immutable Alpha v16 research theorem library",
        "",
        f"Enrolled statements: {len(selected.entries):,}",
        f"Stable closed: {counts.get('stable_closed', 0):,}",
        f"Alpha closed: {counts.get('alpha_closed', 0):,}",
        f"Dependency-curried body only: {counts.get('body_checked', 0):,}",
        f"Pending closure: {counts.get('pending_layered_closure', 0):,}",
        f"Available for independently checked use: {len(alpha.ALPHA_CHECKED_SPECS):,}",
        f"Newly promoted quadratic-reciprocity results: {len(alpha.QR_PROMOTED_NAMES):,}",
        f"Edition SHA-256: {alpha.ALPHA_V16_IDENTITY_SHA256}",
        "",
        "Stable remains the default public theorem registry.",
        "Alpha body-only entries have no checked-use authority.",
        "Inspect evidence: `pa lib alpha <name>`.",
        "Independently replay: `pa lib alpha check <name>`.",
        "List entries: `pa lib alpha list` or `pa lib alpha checked`.",
        "Export a checked Alpha theorem: `pa lean alpha <name>`.",
    ]
    if include_entries:
        rows.extend(("", "Alpha evidence ledger:"))
        for item in selected.entries:
            if not checked_only or item.checked_use:
                rows.append(f"  {item.spec.name:<48} {item.evidence.value}")
    return NL.join(rows)


def _alpha_item(name: str):
    alpha = _alpha_edition()
    return alpha, alpha.entry(name, edition="alpha")


def render_alpha_theorem(name: str, *, verify: bool = False) -> str:
    """Keep Alpha ledger inspection cheap and real proof verification explicit."""

    alpha, item = _alpha_item(name)
    if item is None:
        return f"No Alpha v16 theorem {name!r}. Type `pa lib alpha`."
    spec = item.spec
    dependencies = ", ".join(spec.dependencies) if spec.dependencies else "none"
    rows = [
        f"{spec.name} — Alpha v16 theorem evidence",
        "",
        f"Statement: {_statement(spec)}",
        f"Summary: {spec.summary}",
        f"Release evidence: {item.evidence.value}",
        f"Release membership: {item.membership.value}",
        f"Checked-use authority: {'YES' if item.checked_use else 'NO'}",
        f"Earlier dependencies: {dependencies}",
    ]
    if verify:
        if not item.checked_use:
            rows.extend(
                (
                    "",
                    "Independent kernel check: DENIED; dependency-curried body "
                    "evidence is not a closed theorem certificate.",
                )
            )
            return NL.join(rows)
        checked = alpha.replay(spec.name, edition="alpha")
        rows.extend(
            (
                "",
                f"Independent empty-context kernel check: PASS "
                f"({checked.proof_nodes:,} certificate nodes).",
                f"Cross-check: `pa lean alpha {spec.name}`.",
            )
        )
    elif item.checked_use:
        rows.extend(
            (
                "",
                "This evidence card does not itself replay a proof.",
                f"Verify the complete certificate: `pa lib alpha check {spec.name}`.",
            )
        )
    else:
        rows.extend(
            (
                "",
                "No closed proof is available for checked use in this edition.",
            )
        )
    return NL.join(rows)


def _render_alpha_request(request: str) -> str:
    pieces = request.split(maxsplit=1)
    if not pieces:
        return render_alpha_index()
    operation = pieces[0].casefold()
    if operation == "list" and len(pieces) == 1:
        return render_alpha_index(include_entries=True)
    if operation == "checked" and len(pieces) == 1:
        return render_alpha_index(checked_only=True, include_entries=True)
    if operation == "check":
        if len(pieces) == 1:
            return "Usage: pa lib alpha check <theorem>."
        return render_alpha_theorem(pieces[1], verify=True)
    return render_alpha_theorem(request)


def render_request(request: str) -> str:
    """Handle the data-only portion of ``pa lib [name]``."""

    name = request.strip()
    if not name or name.casefold() in {"list", "ls"}:
        return render_index()
    channel, _, remainder = name.partition(" ")
    if channel.casefold() == "alpha":
        return _render_alpha_request(remainder.strip())
    if name.casefold() in {"help", "?"}:
        return NL.join(
            (
                "Peano Lab theorem library",
                "  pa lib                 list the full ladder",
                "  pa lib <name>          show statement and exact tactic script",
                "  pa lib alpha           inspect the opt-in Alpha v16 research edition",
                "  pa lib alpha check <name>  independently verify one Alpha theorem",
                "  pa lean <name>         export a complete checked Lean 4 theorem",
                "  pa lean alpha <name>   export a checked Alpha-v16 theorem",
            )
        )
    spec = get(name)
    if spec is None:
        return f"No library theorem {name!r}. Type `pa lib`."
    return render_theorem(spec)


def lean_export(spec: TheoremSpec) -> LeanExport:
    """Translate the complete checked certificate into an ordinary Lean theorem."""

    theorem = replay(spec.name)
    return export_checked_theorem(
        spec.name,
        theorem.formula,
        theorem.certificate,
        spec.script,
        dependencies=spec.dependencies,
    )


def render_lean(request: str) -> str:
    """Render ``pa lean <name>`` code and the exact Live Lean link."""

    name = request.strip()
    if not name:
        return "Usage: pa lean <theorem>; list names with `pa lib`."
    channel, _, selected_name = name.partition(" ")
    if channel.casefold() == "alpha":
        selected_name = selected_name.strip()
        if not selected_name:
            return "Usage: pa lean alpha <theorem>; inspect `pa lib alpha`."
        alpha, item = _alpha_item(selected_name)
        if item is None:
            return f"No Alpha v16 theorem {selected_name!r}. Type `pa lib alpha`."
        if not item.checked_use:
            return (
                f"Alpha v16 theorem {item.spec.name!r} has evidence "
                f"{item.evidence.value!r}; a complete checked Lean export "
                "requires a closed theorem certificate."
            )
        spec = item.spec
        checked = alpha.replay(spec.name, edition="alpha")
        exported = export_checked_theorem(
            spec.name,
            checked.formula,
            checked.certificate,
            spec.script,
            dependencies=spec.dependencies,
        )
    else:
        spec = get(name)
        if spec is None:
            return f"No library theorem {name!r}. Type `pa lib`."
        exported = lean_export(spec)
    return NL.join(
        (
            f"Lean 4 independently checked theorem — {spec.name}",
            "The exact statement and complete constructive certificate are translated.",
            "Build this source in the sibling peano-lab-lean project.",
            "",
            exported.code,
            "",
            "Open this exact source (requires the PeanoLab.Codec companion):",
            exported.live_url,
        )
    )


__all__ = [
    "script_with_prelude",
    "render_index",
    "render_theorem",
    "render_alpha_index",
    "render_alpha_theorem",
    "render_request",
    "lean_export",
    "render_lean",
]
