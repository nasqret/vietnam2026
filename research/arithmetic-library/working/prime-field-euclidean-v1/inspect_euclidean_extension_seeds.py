#!/usr/bin/env python3
"""Inert exact target/premise coverage planning, never proof acceptance.

The observed global report only supplies a planning name inventory. The real
exporter derives its own current-parent cone and checks every seed body.
This diagnostic imports no Alpha edition and decodes no proof constructors.
"""
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import resource
import signal
import sys
import time

STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import working_euclidean_extension_support as support
import inspect_working_seed_syntax as previous
from peano_lab.library.proof_bundle import encode_formula
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula
from check_constructive_bottom_layers import authoring_rss_bytes


HINT = support.FilePin(support.WORKING_RELATIVE + "/working-113-global-syntax-v1.json", 9835,
                      "e138bc133d3ff566f98381fb18e5e74faf91fa42b0122e0f2978a1a99139e49a")
SEEDS = (
    (support.PRIOR81_ARTIFACT, 314),
    (support.FilePin("research/arithmetic-library/artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json",
                     1060637, "fec8cf768ef2b94430d58d947daa0affada315bbc5160a03991dc4d2550dd0e9"), 293),
    (support.FilePin("research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json",
                     745307, "55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3"), 210),
)


def inspect():
    support.require_preserved81()
    support.require_extension_sources()
    hint = json.loads(previous._bytes(HINT, support.MAX_SOURCE_BYTES))
    if (hint["syntax_only"] is not True or hint["original_ha_checked"] is not False
            or hint["combined_working_rows"] != 113 or hint["inherited_alpha_v32_rows"] != 254):
        raise support.ExtensionError("an unexpected inert global observation was supplied")
    prior = support.base.load_candidate_state(final=True)
    wanted = (*hint["inherited_alpha_v32_names"], *(row.name for row in prior.rows))
    if len(wanted) != 335 or len(set(wanted)) != 335:
        raise support.ExtensionError("the observed pre-existing335 target inventory changed")
    wanted_set = set(wanted)
    table = {row.name: row for row in (*THEOREMS, *prior.rows) if row.name in wanted_set}
    manifest = json.loads(previous._bytes(support.base.PARENT_CATALOG_PINS[0], support.base.MAX_CATALOG_COMPONENT_BYTES))
    documents = {entry["path"]: entry for entry in manifest["metadata"]["evidence_documents"]}
    extra_pins = {pin.path: pin for pin in (*support.base.inherited.PARENT_CONTROL_PINS, *previous.OBSERVED_RECIPE_PINS)}
    source_pins = []
    for name in previous.SELECTIVE_FACTORIES:
        relative = "peano-lab/py/peano_lab/library/" + name + ".py"
        record = documents.get(relative)
        pin = support.FilePin(relative, record["bytes"], record["sha256"]) if record is not None else extra_pins[relative]
        previous._bytes(pin, support.MAX_SOURCE_BYTES)
        source_pins.append(pin)
        module = import_module("peano_lab.library." + name)
        if Path(module.__file__).resolve() != support.ROOT / relative:
            raise support.ExtensionError("a selected inherited syntax factory resolved elsewhere")
        factory = "make_" + name + "_theorems"
        if name == "bertrand_power_valuation_laws_candidate":
            factory = "make_bertrand_power_valuation_law_candidate_theorems"
        for row in getattr(module, factory)(TheoremSpec):
            if row.name in wanted_set:
                if row.name in table and table[row.name] != row:
                    raise support.ExtensionError("two actual inherited syntax sources disagree")
                table[row.name] = row
    if wanted_set != table.keys() or any(not set(row.dependencies) <= wanted_set for row in table.values()):
        raise support.ExtensionError("the selective actual source inventory is not complete")
    targets = {name: previous._encoded(encode_formula(_closed_formula(table[name].statement))) for name in wanted}
    by_target = {}
    for name, target in targets.items():
        by_target.setdefault(target, []).append(name)
    union, reports = set(), []
    for pin, count in SEEDS:
        value = json.loads(previous._bytes(pin, support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes))
        if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
                or type(value[1]) is not int or value[1] != count - 1 or len(value[3]) != count):
            raise support.ExtensionError("a pinned seed has unexpected inert JSON envelope metadata")
        nodes = value[3]
        encoded = tuple(previous._encoded(node[1]) for node in nodes)
        matched = {}
        for index, node in enumerate(nodes):
            if (len(node) != 4 or type(node[2]) is not list
                    or any(type(edge) is not int or not 0 <= edge < index for edge in node[2])):
                raise support.ExtensionError("a seed has malformed inert ordered-premise metadata")
            for name in by_target.get(encoded[index], ()):
                if tuple(encoded[edge] for edge in node[2]) == tuple(targets[edge] for edge in table[name].dependencies):
                    matched[name] = index
        before = len(union)
        union.update(matched)
        reports.append({"path": pin.path, "bytes": pin.bytes, "sha256": pin.sha256, "inert_nodes": count,
                        "exact_matches": len(matched), "newly_covered": len(union) - before,
                        "matched_node_ids": matched})
        del value, nodes, encoded
    for pin in (*source_pins, *(pin for pin, _count in SEEDS)):
        support.check_pin(pin, support.ROOT, support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    support.require_preserved81()
    assert not any(name.startswith("peano_lab.library.editions_v") for name in sys.modules)
    return {"syntax_only": True, "preexisting_targets": 335, "inherited_alpha_targets": 254,
            "prior_working_targets": 81, "covered_targets": len(union), "missing_names": sorted(wanted_set - union),
            "seeds": reports, "proof_bodies_decoded": False, "original_ha_checked": False,
            "independent_lean_checked": False, "ordinary_principals_checked": False,
            "alpha_admission_performed": False, "stable_admission_performed": False}


if __name__ == "__main__":
    report = inspect()
    report.update(seconds=time.monotonic() - STARTED, peak_rss_bytes=authoring_rss_bytes())
    print(support.canonical(report).decode(), flush=True)
    raise SystemExit(0 if not report["missing_names"] else 1)
