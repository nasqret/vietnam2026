#!/usr/bin/env python3
"""Generate or verify one Obsidian lemma note per checked Peano theorem."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
DEFAULT_OUTPUT = ROOT / "vault" / "lemmas"
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")

if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from peano_lab.engine.state import proof_metrics  # noqa: E402
from peano_lab.library.theorems import THEOREMS, replay  # noqa: E402


def _book_target(name: str) -> str:
    if name.startswith(
        (
            "parity_",
            "even_",
            "odd_",
            "successor_even_",
            "successor_odd_",
            "mod4_",
            "prime_ne_two_is_odd",
            "four_mul_eq_double_double",
            "mul_double_right",
            "quadratic_residue_",
            "bounded_square_",
            "qres_",
            "not_qres_",
            "lt_three_cases",
            "lt_five_cases",
            "lt_seven_cases",
            "mod_eq_decidable_",
            "beta_repeat_",
            "beta_range_",
            "beta_half_range_",
            "beta_prefix_replace_",
            "beta_prefix_swap_",
            "beta_product_replace_",
            "beta_product_swap_",
            "beta_sum_",
            "beta_prefix_sum_",
            "beta_product_pointwise_",
            "pow_",
            "predecessor_square_mod_one",
            "bit_count_",
            "all_bits_",
            "factorial_",
            "finite_",
            "prime_coprime_or_divides",
            "prime_not_divides_coprime",
            "distinct_primes_coprime",
            "coprime_balanced_mod_inverse",
            "coprime_mod_inverse",
            "mod_eq_cancel_coprime",
            "prime_mod_inverse",
            "prime_mod_cancel",
        )
    ):
        return "The quadratic-reciprocity campaign"
    if name.startswith(("multiple_", "not_multiple", "add_residue", "square_")):
        return "Divisibility and congruence"
    return "The dependency ladder"


def build_notes() -> dict[str, str]:
    dependents: dict[str, list[str]] = {spec.name: [] for spec in THEOREMS}
    for spec in THEOREMS:
        for dependency in spec.dependencies:
            dependents[dependency].append(spec.name)

    notes: dict[str, str] = {}
    for spec in THEOREMS:
        theorem = replay(spec.name)
        nodes, depth = proof_metrics(theorem.certificate)
        dependency_lines = (
            "\n".join(f"- [[{name}]]" for name in spec.dependencies)
            if spec.dependencies
            else "- None; the script closes directly from PA rules."
        )
        dependent_lines = (
            "\n".join(f"- [[{name}]]" for name in dependents[spec.name])
            if dependents[spec.name]
            else "- No checked theorem currently depends on this node."
        )
        book = _book_target(spec.name)
        notes[f"{spec.name}.md"] = f"""---
title: "Lemma: {spec.name}"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `{spec.name}`

{spec.summary}

## Closed Peano statement

```text
{spec.statement}
```

## Dependencies

{dependency_lines}

## Checked dependents

{dependent_lines}

## Verification record

- Independently checked from the empty context.
- Certificate: **{nodes} nodes**, depth **{depth}**.
- Authored script length: **{len(spec.script)} commands**.
- Runtime card: `pa lib {spec.name}`.
- Book route: *{book}* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
"""
    return notes


def _check_or_write(output: Path, notes: dict[str, str], check_only: bool) -> None:
    if check_only:
        problems: list[str] = []
        actual = {path.name for path in output.glob("*.md")} if output.is_dir() else set()
        expected = set(notes)
        for name in sorted(expected - actual):
            problems.append(f"missing vault/lemmas/{name}")
        for name in sorted(actual - expected):
            problems.append(f"unexpected vault/lemmas/{name}")
        for name in sorted(actual & expected):
            if (output / name).read_text(encoding="utf-8") != notes[name]:
                problems.append(f"stale vault/lemmas/{name}")
        if problems:
            raise SystemExit("\n".join(problems))
        return

    output.mkdir(parents=True, exist_ok=True)
    for name, text in notes.items():
        (output / name).write_text(text, encoding="utf-8")


def _validate_vault_graph(vault: Path) -> tuple[int, int]:
    """Reject duplicate stems, unresolved wiki links, and disconnected notes."""

    paths = sorted(path for path in vault.rglob("*.md") if path.name != "README.md")
    by_stem: dict[str, Path] = {}
    for path in paths:
        stem = path.stem
        if stem in by_stem:
            raise SystemExit(
                f"duplicate vault note stem {stem!r}: "
                f"{by_stem[stem].relative_to(ROOT)} and {path.relative_to(ROOT)}"
            )
        by_stem[stem] = path

    graph: dict[str, set[str]] = {stem: set() for stem in by_stem}
    unresolved: list[str] = []
    link_count = 0
    for stem, path in by_stem.items():
        source = path.read_text(encoding="utf-8")
        for match in WIKILINK.finditer(source):
            target = Path(match.group(1).strip()).name
            link_count += 1
            if target not in by_stem:
                unresolved.append(
                    f"{path.relative_to(ROOT)} -> [[{match.group(1)}]]"
                )
                continue
            graph[stem].add(target)
            graph[target].add(stem)
    if unresolved:
        raise SystemExit("unresolved vault link(s):\n" + "\n".join(unresolved))

    if "00-index" not in graph:
        raise SystemExit("vault has no moc/00-index.md root")
    reached = {"00-index"}
    pending = deque(["00-index"])
    while pending:
        current = pending.popleft()
        for target in graph[current] - reached:
            reached.add(target)
            pending.append(target)
    disconnected = sorted(set(graph) - reached)
    if disconnected:
        raise SystemExit("disconnected vault note(s): " + ", ".join(disconnected))
    return len(paths), link_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    notes = build_notes()
    _check_or_write(args.output.resolve(), notes, args.check)
    note_count, link_count = _validate_vault_graph(ROOT / "vault")
    action = "verified" if args.check else "wrote"
    print(
        f"{action} {len(notes)} checked lemma notes in {args.output}; "
        f"vault graph has {note_count} notes and {link_count} resolved links"
    )


if __name__ == "__main__":
    main()
