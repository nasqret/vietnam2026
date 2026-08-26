"""Deterministic terminal views of the checked public theorem ladder."""

from __future__ import annotations

from collections import Counter
from shlex import quote

from ..kernel.formulas import parse_formula_with_names, pretty_formula
from ..library.lean import LeanExport, formula_to_lean
from ..library.lean_certified import export_checked_theorem
from ..library.theorems import THEOREMS, TheoremSpec, get, replay, replay_target


NL = "\r\n"
_LEAN_BROWSER_LIMIT = 15 * 1024
_LEAN_FULL_BROWSER_DEPENDENCY_LIMIT = 128
_LEAN_MODES = frozenset({"compact", "pretty", "full", "exact", "tactics", "strand"})
_PROOF_STRAND_SCRIPT_LINES = 48
_PROOF_STRAND_DIRECT_DEPENDENCIES = 16


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

    from ..library import editions_v24

    return editions_v24


def render_alpha_index(*, checked_only: bool = False, include_entries: bool = False) -> str:
    """Inspect immutable Alpha evidence without loading or replaying proof data."""

    alpha = _alpha_edition()
    historical_v23 = alpha.v23
    historical_v22 = historical_v23.v22
    historical_v21 = historical_v22.v21
    selected = alpha.edition("alpha")
    counts = Counter(item.evidence.value for item in selected.entries)
    rows = [
        "Peano Lab immutable Alpha v24 research theorem library",
        "",
        f"Enrolled statements: {len(selected.entries):,}",
        f"Stable closed: {counts.get('stable_closed', 0):,}",
        f"Alpha closed: {counts.get('alpha_closed', 0):,}",
        f"Dependency-curried body only: {counts.get('body_checked', 0):,}",
        f"Pending closure: {counts.get('pending_layered_closure', 0):,}",
        f"Available for independently checked use: {len(alpha.ALPHA_CHECKED_SPECS):,}",
        f"Previously promoted quadratic-reciprocity results: "
        f"{len(historical_v21.v19.v18.v17.v16.QR_PROMOTED_NAMES):,}",
        f"Previously promoted supplementary-law results: "
        f"{len(historical_v21.v19.v18.v17.SUPPLEMENTARY_PROMOTED_NAMES):,}",
        f"Previously promoted five-campaign flagship results: "
        f"{len(historical_v21.v19.v18.FLAGSHIP_PROMOTED_NAMES):,}",
        f"Newly closed legacy residual results: "
        f"{len(historical_v21.v19.RESIDUAL_PROMOTED_NAMES):,}",
        f"Previously added Alpha v19 campaign results: {len(historical_v21.v19.FRONTIER_NEW_NAMES):,}",
        f"Previously added Alpha v20 campaign results: {len(historical_v21.v20.FRONTIER_NEW_NAMES):,}",
        f"Previously added Alpha v21 campaign results: {len(historical_v21.FRONTIER_NEW_NAMES):,}",
        f"Previously added Alpha v22 campaign results: {len(historical_v22.FRONTIER_NEW_NAMES):,}",
        f"Previously added Alpha v23 campaign results: {len(historical_v23.FRONTIER_NEW_NAMES):,}",
        f"New constructive campaign results: {len(alpha.FRONTIER_NEW_NAMES):,}",
        f"Edition SHA-256: {alpha.ALPHA_V24_IDENTITY_SHA256}",
        "",
        "Stable remains the default public theorem registry.",
        "Every enrolled Alpha theorem now has independently checked-use authority.",
        "Inspect evidence: `pa lib alpha <name>`.",
        "Independently replay bounded proofs: `pa lib alpha check <name>`.",
        "Large proof roots remain checked and can be audited safely offline.",
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
        return f"No Alpha v24 theorem {name!r}. Type `pa lib alpha`."
    spec = item.spec
    dependencies = ", ".join(spec.dependencies) if spec.dependencies else "none"
    rows = [
        f"{spec.name} — Alpha v24 theorem evidence",
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
        closure_size = _lean_full_dependency_count(
            spec,
            edition="alpha",
            alpha_module=alpha,
        )
        if closure_size > _LEAN_FULL_BROWSER_DEPENDENCY_LIMIT:
            rows.extend(
                (
                    "",
                    "Independent empty-context kernel check: NOT RUN; "
                    "browser replay blocked for safety.",
                    "Authenticated transitive dependency closure exceeds "
                    f"{_LEAN_FULL_BROWSER_DEPENDENCY_LIMIT} theorem entries.",
                    "Checked-use authority remains YES; no proof certificate "
                    "was loaded.",
                    f"Inspect the safe Lean export path: `pa lean alpha {spec.name}`.",
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
                "  pa lib alpha           inspect the opt-in Alpha v24 research edition",
                "  pa lib alpha check <name>  independently verify one Alpha theorem",
                "  pa lean <name>         show a compact checked Lean 4 theorem",
                "  pa lean full <name>    show its complete certificate explicitly",
                "  pa lean exact <name>   inspect the exact unabbreviated proposition",
                "  pa lean tactics <name> inspect its original Peano tactic script",
                "  pa proof <name>        inspect a bounded readable proof strand",
                "  pa proof alpha <name>  inspect an Alpha-v24 proof strand safely",
                "  pa lean strand <name>  alternate readable proof-strand spelling",
                "  pa lean alpha <name>   inspect a checked Alpha-v24 theorem",
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


def _bounded_lean_view(
    text: str,
    *,
    limit: int = _LEAN_BROWSER_LIMIT,
    notice: str | None = None,
) -> str:
    """Keep ordinary theorem inspection safe for a browser terminal."""

    encoded = text.encode("utf-8")
    if len(encoded) <= limit:
        return text
    if notice is None:
        notice = (
            NL
            + "... [browser output truncated; use the complete package export command above]"
        )
    available = max(0, limit - len(notice.encode("utf-8")))
    return encoded[:available].decode("utf-8", errors="ignore").rstrip() + notice


def _lean_usage(*, edition: str = "stable", mode: str = "compact") -> str:
    if edition == "alpha":
        command = "pa lean alpha"
        if mode != "compact":
            command += f" {mode}"
        return f"Usage: {command} <theorem>; inspect `pa lib alpha`."
    command = "pa lean"
    if mode != "compact":
        command += f" {mode}"
    return f"Usage: {command} <theorem>; list names with `pa lib`."


def _lean_package_command(spec: TheoremSpec, *, edition: str) -> str:
    name = quote(spec.name)
    channel = " --edition alpha" if edition == "alpha" else ""
    destination = quote(f"artifacts/lean/{spec.name}")
    bundle = _lean_flagship_bundle_argument(spec, edition=edition)
    return (
        f"python3 scripts/export_peano_lean.py {name}{channel} "
        f"--format compact --package-dir {destination}{bundle} --verify"
    )


def _proof_strand_terminal_command(spec: TheoremSpec, *, edition: str) -> str:
    name = quote(spec.name)
    channel = " --edition alpha" if edition == "alpha" else ""
    destination = quote(f"/private/tmp/peano-proof-strands/{spec.name}")
    return (
        f"python3 scripts/export_peano_lean.py {name}{channel} "
        f"--format strand --package-dir {destination} --verify"
    )


def _lean_flagship_bundle_argument(spec: TheoremSpec, *, edition: str) -> str:
    """Expose an exact matching checked DAG without loading proof bytes."""

    if edition != "alpha":
        return ""
    alpha = _alpha_edition()
    historical = alpha.v23.v22.v21.v19.v18
    owner = historical.FLAGSHIP_PROMOTION_OWNERS.get(spec.name)
    if owner is None or historical.FLAGSHIP_BUNDLE_ROOTS[owner] != (spec.name,):
        return ""
    artifact = (
        "research/arithmetic-library/artifacts/"
        + historical.FLAGSHIP_ARTIFACT_FILENAMES[owner]
    )
    return f" --proof-bundle {quote(artifact)}"


def _lean_full_dependency_count(
    spec: TheoremSpec,
    *,
    edition: str,
    alpha_module=None,
) -> int:
    """Bound full browser audits using authenticated inventory metadata only."""

    entries = (
        alpha_module.edition("alpha").by_name
        if edition == "alpha" and alpha_module is not None
        else None
    )
    if edition == "alpha" and entries is None:
        raise ValueError("Alpha dependency inspection requires its authenticated edition")
    pending = [spec.name]
    visited: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        if len(visited) > _LEAN_FULL_BROWSER_DEPENDENCY_LIMIT:
            return len(visited)
        if entries is None:
            dependency = get(name)
            if dependency is None:
                raise ValueError(f"Stable dependency {name!r} is not in its release")
        else:
            item = entries.get(name)
            if item is None or not item.checked_use:
                raise ValueError(
                    f"Alpha dependency {name!r} has no authenticated checked-use authority"
                )
            dependency = item.spec
        pending.extend(dependency.dependencies)
    return len(visited)


def _lean_full_browser_denial(spec: TheoremSpec, *, edition: str) -> str:
    name = quote(spec.name)
    channel = " --edition alpha" if edition == "alpha" else ""
    destination = quote(f"/private/tmp/peano-{spec.name}.lean")
    browser_channel = "alpha " if edition == "alpha" else ""
    bundle = _lean_flagship_bundle_argument(spec, edition=edition)
    command = (
        f"python3 scripts/export_peano_lean.py {name}{channel} "
        f"--format full --output {destination}{bundle} "
        "--max-memory-mib 1536 --max-verify-seconds 180 --verify"
    )
    return NL.join(
        (
            f"Browser full-certificate audit blocked for safety — {spec.name}",
            "Authenticated transitive dependency closure exceeds "
            f"{_LEAN_FULL_BROWSER_DEPENDENCY_LIMIT} theorem entries.",
            "No proof certificate was loaded; fresh kernel replay and Lean "
            "verification were NOT RUN.",
            "Checked-use authority remains YES; this is a browser resource "
            "limit, not a theorem rejection.",
            f"Safe theorem-first preview: `pa lean {browser_channel}{spec.name}`.",
            "",
            "If you deliberately need the full audit, run this bounded Lean "
            "command in a terminal:",
            f"  {command}",
            "Python proof reconstruction can still require substantial memory.",
        )
    )


def _proof_strand_usage(*, edition: str = "stable") -> str:
    if edition == "alpha":
        return "Usage: pa proof alpha <theorem>; inspect `pa lib alpha`."
    return "Usage: pa proof [alpha] <theorem>; list names with `pa lib`."


def _proof_strand_dependency_rows(
    spec: TheoremSpec,
    *,
    edition: str,
    alpha_module=None,
) -> list[str]:
    rows = [f"Direct authored dependencies ({len(spec.dependencies)}):"]
    if not spec.dependencies:
        rows.append("  (none)")
        return rows

    entries = alpha_module.edition("alpha").by_name if edition == "alpha" else None
    for name in spec.dependencies[:_PROOF_STRAND_DIRECT_DEPENDENCIES]:
        dependency = get(name) if entries is None else entries[name].spec
        if dependency is None:
            raise ValueError(f"proof-strand dependency {name!r} left its release")
        summary = " ".join(dependency.summary.split())
        if len(summary) > 116:
            summary = summary[:113].rstrip() + "..."
        rows.append(f"  - {name}: {summary}")
    hidden = len(spec.dependencies) - _PROOF_STRAND_DIRECT_DEPENDENCIES
    if hidden > 0:
        rows.append(f"  ... {hidden} additional direct dependencies")
    return rows


def _proof_strand_root_rows(spec: TheoremSpec) -> list[str]:
    rows = [
        "Root authored Peano proof (original Peano tactics; not executable Lean tactics):"
    ]
    for index, command in enumerate(
        spec.script[:_PROOF_STRAND_SCRIPT_LINES],
        start=1,
    ):
        rows.append(f"  {index:>3}. {command}")
    hidden = len(spec.script) - _PROOF_STRAND_SCRIPT_LINES
    if hidden > 0:
        rows.append(f"  ... {hidden} additional authored Peano tactic lines")
    return rows


def render_proof(request: str) -> str:
    """Inspect an authenticated proof strand without replay or certificate data."""

    pieces = request.split()
    if not pieces or pieces[0].casefold() in {"help", "?"}:
        return _proof_strand_usage()
    edition = "stable"
    alpha_module = None
    if pieces[0].casefold() == "alpha":
        edition = "alpha"
        pieces.pop(0)
    if len(pieces) != 1:
        return _proof_strand_usage(edition=edition)

    name = pieces[0]
    if edition == "alpha":
        alpha_module, item = _alpha_item(name)
        if item is None:
            return f"No Alpha v24 theorem {name!r}. Type `pa lib alpha`."
        if not item.checked_use:
            return (
                f"Alpha v24 theorem {item.spec.name!r} has evidence "
                f"{item.evidence.value!r}; a proof strand requires "
                "closed checked-use authority."
            )
        spec = item.spec
        evidence = item.evidence.value
        membership = item.membership.value
        source = item.source_module
    else:
        spec = get(name)
        if spec is None:
            return f"No library theorem {name!r}. Type `pa lib`."
        evidence = "stable_closed"
        membership = "stable"
        source = "peano-lab/py/peano_lab/library/theorems.py"

    formula, free_names = parse_formula_with_names(spec.statement)
    if free_names:
        raise ValueError(
            "proof-strand theorem statements must be closed; free variable(s): "
            + ", ".join(free_names)
        )

    from ..library.lean_proof_strand import (
        plan_proof_strand,
        preview_proof_strand,
        readable_strand_formula,
    )

    count = _lean_full_dependency_count(
        spec,
        edition=edition,
        alpha_module=alpha_module,
    )
    bounded = count <= _LEAN_FULL_BROWSER_DEPENDENCY_LIMIT
    preview = None
    if bounded:
        plan = plan_proof_strand(
            spec.name,
            edition=edition,
            max_nodes=_LEAN_FULL_BROWSER_DEPENDENCY_LIMIT,
            max_edges=4_096,
            max_depth=_LEAN_FULL_BROWSER_DEPENDENCY_LIMIT,
        )
        if plan.node_count != count:
            raise ValueError("proof strand changed its authenticated dependency closure")
        root = next(node for node in plan.nodes if node.name == spec.name)
        statement = root.readable_statement
        source = root.source_path
        preview = preview_proof_strand(plan, max_bytes=6 * 1024, max_rows=12)
        closure = str(plan.node_count)
    else:
        statement = readable_strand_formula(formula, source_statement=spec.statement)
        closure = (
            f"more than {_LEAN_FULL_BROWSER_DEPENDENCY_LIMIT}; stopped at "
            f"{_LEAN_FULL_BROWSER_DEPENDENCY_LIMIT + 1} without traversing the full graph"
        )

    rows = [
        f"Readable Peano-to-Lean proof strand — {spec.name}",
        "",
        f"Theorem: {statement}",
        f"Summary: {spec.summary}",
        f"Release edition: {'Alpha v24' if edition == 'alpha' else 'Stable'}.",
        f"Authenticated release evidence: {evidence}.",
        f"Release membership: {membership}.",
        "Checked-use authority: YES.",
        f"Declaration source: {source}",
        f"Transitive authenticated theorem entries: {closure}.",
        f"Root authored Peano tactic decisions: {len(spec.script):,}.",
        "Fresh Peano proof replay: NOT RUN; authenticated metadata only.",
        "Independent Lean compilation: NOT RUN; no proof certificate was loaded.",
        "",
        "Export the complete dependency strand and request independent Lean verification:",
        f"  {_proof_strand_terminal_command(spec, edition=edition)}",
        "",
        *_proof_strand_dependency_rows(
            spec,
            edition=edition,
            alpha_module=alpha_module,
        ),
        "",
        *_proof_strand_root_rows(spec),
    ]
    if preview is not None:
        rows.extend(("", "Bounded topological strand outline (metadata only):"))
        rows.extend(preview.splitlines())
    else:
        rows.extend(
            (
                "",
                "Dependency expansion stopped at the browser safety limit; "
                "the root proof above remains visible.",
                "Use the terminal strand exporter for the complete topological graph.",
            )
        )
    return _bounded_lean_view(NL.join(rows))


def _lean_evidence_rows(
    spec: TheoremSpec,
    checked,
    *,
    edition: str,
    release_evidence: str,
) -> list[str]:
    dependencies = ", ".join(spec.dependencies) if spec.dependencies else "none"
    rows = [
        f"Release edition: {'Alpha v24' if edition == 'alpha' else 'Stable'}.",
        f"Authenticated release evidence: {release_evidence}.",
        "Checked-use authority: YES.",
    ]
    if checked is None:
        rows.extend(
            (
                "Fresh independent empty-context Peano kernel replay: NOT RUN; "
                "this safe preview uses release evidence only.",
                "Certificate proof nodes: not loaded; request the explicit full audit.",
            )
        )
    else:
        rows.append(
            "Independent empty-context Peano kernel check: "
            f"PASS ({checked.proof_nodes:,} certificate nodes)."
        )
    rows.extend(
        (
            "Independent Lean compilation: NOT RUN; compile the complete package below.",
            f"Direct checked dependencies ({len(spec.dependencies)}): {dependencies}.",
            f"Original Peano tactic decisions: {len(spec.script):,}.",
            "Certificate companion import: import PeanoLab.Codec",
            "Certificate soundness theorem: PeanoLab.Artifact.check_sound",
            "",
            "Export and independently verify the complete local Lean package:",
            f"  {_lean_package_command(spec, edition=edition)}",
        )
    )
    return rows


def _lean_compact_view(
    spec: TheoremSpec,
    formula,
    *,
    edition: str,
    release_evidence: str,
) -> str:
    """Render theorem-first notation without constructing a Lean certificate."""

    from ..library.lean_presentation import preview_checked_presentation

    preview = preview_checked_presentation(
        spec.name,
        formula,
        source_statement=spec.statement,
        script=spec.script,
        dependencies=spec.dependencies,
        summary=spec.summary,
        edition=edition,
    )
    prefix = "alpha " if edition == "alpha" else ""
    heading = f"Lean 4 independently checked theorem — {spec.name}"
    details = [
        *_lean_evidence_rows(
            spec,
            None,
            edition=edition,
            release_evidence=release_evidence,
        ),
        "",
        f"Exact expanded proposition: `pa lean {prefix}exact {spec.name}`.",
        f"Original Peano proof script: `pa lean {prefix}tactics {spec.name}`.",
        f"Full certificate audit: `pa lean {prefix}full {spec.name}`.",
    ]
    evidence = NL.join(details)
    reserve = len((heading + NL + NL + NL + NL + evidence).encode("utf-8"))
    preview = _bounded_lean_view(
        NL.join(preview.splitlines()),
        limit=max(0, _LEAN_BROWSER_LIMIT - reserve),
        notice=NL + "... [theorem presentation abbreviated; inspect the views below]",
    )
    return _bounded_lean_view(NL.join((heading, "", preview, "", evidence)))


def _lean_exact_view(
    spec: TheoremSpec,
    formula,
    *,
    edition: str,
    release_evidence: str,
) -> str:
    rows = [
        f"Lean 4 exact checked proposition — {spec.name}",
        "",
        *_lean_evidence_rows(
            spec,
            None,
            edition=edition,
            release_evidence=release_evidence,
        ),
        "",
        "Exact Lean proposition; semantic aliases have been fully expanded:",
        formula_to_lean(formula),
    ]
    return _bounded_lean_view(NL.join(rows))


def _lean_tactics_view(spec: TheoremSpec, *, edition: str, release_evidence: str) -> str:
    rows = [
        f"Original Peano proof tactics — {spec.name}",
        "",
        *_lean_evidence_rows(
            spec,
            None,
            edition=edition,
            release_evidence=release_evidence,
        ),
        "",
        "Generated dependency introductions (Peano commands; not Lean tactics):",
    ]
    rows.extend(f"  intro {dependency}" for dependency in spec.dependencies)
    if not spec.dependencies:
        rows.append("  (none)")
    rows.extend(("", "Original authored Peano tactics (not Lean tactics):"))
    rows.extend(
        f"  {index:>4}. {command}"
        for index, command in enumerate(spec.script, start=1)
    )
    return _bounded_lean_view(NL.join(rows))


def _lean_full_view(
    spec: TheoremSpec,
    checked,
    *,
    edition: str,
    release_evidence: str,
) -> str:
    """Reveal full code only when the potentially large audit is requested."""

    exported = (
        lean_export(spec)
        if edition == "stable"
        else export_checked_theorem(
            spec.name,
            checked.formula,
            checked.certificate,
            spec.script,
            dependencies=spec.dependencies,
        )
    )
    return NL.join(
        (
            f"Lean 4 independently checked theorem — {spec.name}",
            "The exact statement and complete constructive certificate are translated.",
            *_lean_evidence_rows(
                spec,
                checked,
                edition=edition,
                release_evidence=release_evidence,
            ),
            "",
            "Complete local Lean source; build it in the sibling peano-lab-lean project:",
            "",
            exported.code,
        )
    )


def render_lean(request: str) -> str:
    """Inspect checked mathematics compactly; expose full certificates on demand."""

    pieces = request.split()
    if not pieces:
        return _lean_usage()

    edition = "stable"
    mode = "compact"
    if pieces[0].casefold() == "alpha":
        edition = "alpha"
        pieces.pop(0)
        if not pieces:
            return _lean_usage(edition=edition)
    if pieces and pieces[0].casefold() in _LEAN_MODES:
        mode = pieces.pop(0).casefold()
        if mode == "pretty":
            mode = "compact"
        if pieces and pieces[0].casefold() == "alpha" and edition == "stable":
            edition = "alpha"
            pieces.pop(0)
    if len(pieces) != 1:
        return _lean_usage(edition=edition, mode=mode)

    selected_name = pieces[0]
    if edition == "alpha":
        alpha, item = _alpha_item(selected_name)
        if item is None:
            return f"No Alpha v24 theorem {selected_name!r}. Type `pa lib alpha`."
        if not item.checked_use:
            return (
                f"Alpha v24 theorem {item.spec.name!r} has evidence "
                f"{item.evidence.value!r}; a complete checked Lean export "
                "requires a closed theorem certificate."
            )
        spec = item.spec
        release_evidence = item.evidence.value
    else:
        spec = get(selected_name)
        if spec is None:
            return f"No library theorem {selected_name!r}. Type `pa lib`."
        release_evidence = "stable_closed"

    if mode == "full":
        if (
            _lean_full_dependency_count(
                spec,
                edition=edition,
                alpha_module=alpha if edition == "alpha" else None,
            )
            > _LEAN_FULL_BROWSER_DEPENDENCY_LIMIT
        ):
            return _lean_full_browser_denial(spec, edition=edition)
        checked = (
            alpha.replay(spec.name, edition="alpha")
            if edition == "alpha"
            else replay(spec.name)
        )
        return _lean_full_view(
            spec,
            checked,
            edition=edition,
            release_evidence=release_evidence,
        )
    if mode == "strand":
        prefix = "alpha " if edition == "alpha" else ""
        return render_proof(prefix + spec.name)

    formula, free_names = parse_formula_with_names(spec.statement)
    if free_names:
        raise ValueError(
            "library theorem statements must be closed; free variable(s): "
            + ", ".join(free_names)
        )
    if mode == "exact":
        return _lean_exact_view(
            spec,
            formula,
            edition=edition,
            release_evidence=release_evidence,
        )
    if mode == "tactics":
        return _lean_tactics_view(
            spec,
            edition=edition,
            release_evidence=release_evidence,
        )
    return _lean_compact_view(
        spec,
        formula,
        edition=edition,
        release_evidence=release_evidence,
    )


__all__ = [
    "script_with_prelude",
    "render_index",
    "render_theorem",
    "render_alpha_index",
    "render_alpha_theorem",
    "render_request",
    "render_proof",
    "lean_export",
    "render_lean",
]
