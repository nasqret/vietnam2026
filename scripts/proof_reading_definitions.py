"""Reuse a preserved family's own conservative definition DAG in reading aids.

No definitions are invented or imported from a newer family. The existing
matcher re-expands every proposed abbreviation and checks exact de Bruijn AST
and free-context equality. These are notation checks, not proof admissions.
"""
from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import re
import sys

PY_ROOT = Path(__file__).resolve().parents[1] / "peano-lab/py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from constructive_formula_compactor import _FormulaCompactor
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from proof_readability import MAX_VISIBLE_FORMULA, require

_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z")
_ID = re.compile(r"[A-Z]{2}[0-9A-Z]{4}\Z")
MAX_DEFINITIONS = 1_024
MAX_LOCAL_SOURCE_BYTES = 262_144


class ReadingDefinitions:
    def __init__(self, rows, provenance):
        require(type(rows) is list and 0 < len(rows) <= MAX_DEFINITIONS, "invalid family definition inventory")
        self.provenance = dict(provenance)
        self.by_id = {}
        names, definitions = set(), []
        for row in rows:
            identifier, name = row.get("id", ""), row.get("name", "")
            require(_ID.fullmatch(identifier) and _NAME.fullmatch(name), "unsafe definition identity")
            require(identifier not in self.by_id and name not in names, "ambiguous definition identity")
            parameters = row.get("parameters")
            if parameters is None:
                signature = row.get("signature", "")
                match = re.fullmatch(re.escape(name) + r"\(([^()]*)\)", signature)
                require(match is not None, "definition has no exact parameter signature")
                parameters = [part.strip() for part in match[1].split(",")] if match[1].strip() else []
            require(type(parameters) is list and all(type(p) is str and _NAME.fullmatch(p) for p in parameters)
                and len(parameters) == len(set(parameters)), "invalid definition parameters")
            source = row.get("expanded_template", row.get("expansion"))
            expected = row.get("expansion_sha256", row.get("template_sha256"))
            require(type(source) is str and sha256(source.encode()).hexdigest() == expected,
                "definition expansion differs from its preserved digest")
            dependencies = row.get("dependencies", [])
            require(type(dependencies) is list and all(type(dep) is str for dep in dependencies)
                and len(dependencies) == len(set(dependencies)), "invalid definition arrows")
            if parameters:
                definition = _definition(stable_id=identifier, name=name, parameters=tuple(parameters),
                    template_source=source, summary=row.get("summary") or name,
                    category="preserved_family_reading", priority="P2")
            else:
                # Some existing campaigns name a closed condition, e.g. the
                # strict-descent hypothesis. Its zero-argument call expands to
                # the same closed formula; it is never admitted as an axiom.
                definition = DefinitionSpec(identifier, name, (), source,
                    parse_formula_in_context(source, []), row.get("summary") or name,
                    "preserved_family_reading", "P2")
            require(row.get("arity", len(parameters)) == len(parameters), "definition arity differs")
            definitions.append(definition)
            self.by_id[identifier] = dict(name=name, dependencies=dependencies)
            names.add(name)
        by_name = {row["name"]: identifier for identifier, row in self.by_id.items()}
        arrows = {}
        for identifier, row in self.by_id.items():
            dependencies = [dep if dep in self.by_id else by_name.get(dep) for dep in row["dependencies"]]
            require(all(dep is not None for dep in dependencies), "definition arrow has no target")
            arrows[identifier] = set(dependencies)
        order, levels, pending = [], {}, dict(arrows)
        while pending:
            ready = sorted(identifier for identifier, deps in pending.items() if deps <= set(order))
            require(ready, "cyclic definition DAG")
            for identifier in ready:
                levels[identifier] = 1 + max((levels[dep] for dep in pending[identifier]), default=-1)
                order.append(identifier)
                del pending[identifier]
        self.report = dict(self.provenance, definition_count=len(definitions),
            definition_edge_count=sum(map(len, arrows.values())), topological_order=order,
            layer_count=1 + max(levels.values()), new_definitions=False, proof_authority=False)
        self.compactor = _FormulaCompactor(definitions)
        self.compact = lru_cache(maxsize=128)(self.compactor.compact)

    def apply(self, page, *, minimum_characters=MAX_VISIBLE_FORMULA):
        lines, changes, oversized = [], [], 0
        prefix = "../definition/" if page.edition == "defined" else "../defined/definition/"
        for line in page.lines:
            if line.tactic not in {"have", "suffices"} or ":=" in line.args or len(line.displayed) <= minimum_characters:
                lines.append(line)
                continue
            name, colon, proposition = line.args.partition(":")
            require(colon and name.strip() and proposition.strip(), "malformed native local proposition")
            proposition = proposition.strip()
            if len(proposition.encode()) > MAX_LOCAL_SOURCE_BYTES:
                oversized += 1
                lines.append(line)
                continue
            compact = self.compact(proposition)
            displayed = f"{line.tactic} {name.strip()} : " + compact["defined_statement"]
            if not compact["statement_definition_uses"] or len(displayed) >= len(line.displayed):
                lines.append(line)
                continue
            uses = compact["statement_definition_uses"]
            links = tuple((self.by_id[identifier]["name"], prefix + identifier + ".html") for identifier in uses)
            changes.append(dict(line=line.number, exact_ast_equivalence=True,
                original_proposition_sha256=compact["expanded_statement_sha256"],
                defined_proposition_sha256=compact["defined_statement_sha256"],
                free_names=compact["free_names"], definition_uses=uses,
                previous_display_characters=len(line.displayed), reading_display_characters=len(displayed)))
            lines.append(replace(line, displayed=displayed, definitions=links))
        return replace(page, lines=tuple(lines)), dict(
            notation_source=self.provenance, notation_compactions=changes,
            notation_compacted_claims=len(changes), notation_source_size_skips=oversized,
            notation_display_characters_saved=sum(row["previous_display_characters"] - row["reading_display_characters"] for row in changes))
