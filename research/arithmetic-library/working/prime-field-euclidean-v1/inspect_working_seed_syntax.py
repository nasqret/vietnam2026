#!/usr/bin/env python3
"""Read-only seed coverage planning; never decode or accept proof bodies.

This diagnostic uses the observed cone name list solely as a planning hint.
It authenticates the installed catalogue and its source records, constructs
only selective existing factories, then compares encoded target and ordered
premise syntax in small pinned JSON payloads. No Alpha edition is imported.
The real exporter independently derives its cone and checks every supplied
seed in full; it never imports this script or reads its output.
"""

from __future__ import annotations

from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import resource
import signal
import sys
import time

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import working_euclidean_support as support
from check_constructive_bottom_layers import authoring_rss_bytes
from peano_lab.library.proof_bundle import encode_formula
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula


SEEDS = (
    (support.FilePin(support.WORKING_RELATIVE + "/artifacts/inherited-polynomial-products-three-lemmas-seed-v1.json",
                     812095, "f4d2567e664ae3ad6092e6b54a6599d2858ac4fafc0b4343085a218da6735624"), 214),
    (support.FilePin("research/arithmetic-library/artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json",
                     1060637, "fec8cf768ef2b94430d58d947daa0affada315bbc5160a03991dc4d2550dd0e9"), 293),
    (support.FilePin("research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json",
                     688987, "6e3a08c73b8a45de127e6d50a771f95b52fd54894b1c2e43468751421488a01a"), 202),
)
SYNTAX_HINT = support.FilePin(support.WORKING_RELATIVE + "/working-81-global-syntax-v1.json", 10290,
    "38e99d5574810ff9820b94952d11fa7b4f17a09a030c36fd42e4df94f2bf23b7")
SELECTIVE_FACTORIES = (
    "finite_pointwise_mul_recode_candidate", "finite_division_prefix_candidate",
    "finite_sum_transport_candidate", "finite_sum_pointwise_mod_candidate",
    "finite_repeat_sum_candidate", "bertrand_power_valuation_laws_candidate",
    "matrix_coded_product_candidate", "binary_modular_exponentiation_candidate",
    "matrix_recursive_determinant_extensional_candidate", "matrix_rank_finite_coding_candidate",
    "hensel_prime_power_candidate", "signed_integer_division_candidate",
    "prime_field_arithmetic_candidate", "prime_field_polynomial_candidate",
    "prime_field_polynomial_convolution_candidate", "prime_field_polynomial_degree_candidate",
    "prime_field_polynomial_subtraction_candidate", "prime_field_polynomial_trim_candidate",
)
# These five earlier recipe files have no standalone entry in the later
# catalogue evidence_documents. Their current bytes were independently
# compared with their exact tracked HEAD blobs before this source-only
# diagnostic. They are not reclassified as historical admission evidence.
OBSERVED_RECIPE_PINS = (
    support.FilePin("peano-lab/py/peano_lab/library/finite_pointwise_mul_recode_candidate.py", 15489,
        "390e453959339720836e37ea488f226db3ad0c2fabe9dc53572053801e0c9dd3"),
    support.FilePin("peano-lab/py/peano_lab/library/finite_division_prefix_candidate.py", 13578,
        "a6af47a7d918d46cdd4b83f60524d3c7afad42886ebb8e560bda5a1318f0b606"),
    support.FilePin("peano-lab/py/peano_lab/library/finite_sum_transport_candidate.py", 4087,
        "5b875f94f987c8f7b77a8ef227d2209dfb209244a38f2b7b03c6197034578023"),
    support.FilePin("peano-lab/py/peano_lab/library/finite_sum_pointwise_mod_candidate.py", 16646,
        "8e6c55bc4700302d57959e3318b595d616b185b3af5329988b17b295a929de8a"),
    support.FilePin("peano-lab/py/peano_lab/library/finite_repeat_sum_candidate.py", 6860,
        "7e468d7ddced0220b4c6da6c7417edfa1f1392e793770b0109808ad32d84d182"),
)


def _bytes(pin, maximum):
    support.check_pin(pin, support.ROOT, maximum)
    raw = support.bounded_bytes(support.ROOT / pin.path, maximum)
    if len(raw) != pin.bytes or sha256(raw).hexdigest() != pin.sha256:
        raise support.WorkingError("a syntax-planning input changed during its read")
    return raw


def _encoded(value):
    # Exact JSON comparison keeps booleans distinct from naturals and does
    # not rely only on a digest or Python's True == 1 comparison.
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def inspect_seed_syntax():
    support.require_final_registration()
    manifest = json.loads(_bytes(support.PARENT_CATALOG_PINS[0], support.MAX_CATALOG_COMPONENT_BYTES))
    documents = {row["path"]: row for row in manifest["metadata"]["evidence_documents"]}
    hint = json.loads(_bytes(SYNTAX_HINT, support.MAX_SOURCE_BYTES))
    if (hint["syntax_only"] is not True or hint["whole_original_ha_checked"] is not False
            or hint["new_rows"] != 81 or hint["parent_count"] != 3971):
        raise support.WorkingError("the inert planning hint has an unexpected scope")
    wanted = tuple(hint["direct_current_alpha_dependencies"])
    if len(wanted) != len(set(wanted)) or len(wanted) != 232:
        raise support.WorkingError("the observed inherited name inventory changed")
    wanted_set = set(wanted)
    table = {row.name: row for row in THEOREMS if row.name in wanted_set}
    source_pins = []
    paths = ("theorems", *SELECTIVE_FACTORIES)
    missing_pins = []
    for name in paths:
        path = "peano-lab/py/peano_lab/library/" + name + ".py"
        metadata = documents.get(path)
        if metadata is None:
            metadata = next(({"path": pin.path, "bytes": pin.bytes, "sha256": pin.sha256}
                             for pin in support.inherited.PARENT_CONTROL_PINS if pin.path == path), None)
        if metadata is None:
            metadata = next(({"path": pin.path, "bytes": pin.bytes, "sha256": pin.sha256}
                             for pin in OBSERVED_RECIPE_PINS if pin.path == path), None)
        if metadata is None:
            missing_pins.append(path)
            continue
        pin = support.FilePin(path, metadata["bytes"], metadata["sha256"])
        _bytes(pin, support.MAX_SOURCE_BYTES)
        source_pins.append(pin)
        if name == "theorems":
            continue
        module = import_module("peano_lab.library." + name)
        if Path(module.__file__).resolve() != support.ROOT / path:
            raise support.WorkingError("a selective syntax factory resolved outside the frozen source")
        factory_name = "make_" + name + ("" if name.endswith("_theorems") else "_theorems")
        if name == "bertrand_power_valuation_laws_candidate":
            factory_name = "make_bertrand_power_valuation_law_candidate_theorems"
        rows = getattr(module, factory_name)(TheoremSpec)
        for row in rows:
            if row.name not in wanted_set:
                continue
            if row.name in table and table[row.name] != row:
                raise support.WorkingError("selective source factories disagree on an inherited row")
            table[row.name] = row
    missing = sorted(wanted_set - table.keys())
    if missing or missing_pins:
        return {"syntax_only": True, "complete_source_inventory": False,
                "missing_names": missing, "missing_source_pins": missing_pins,
                "original_ha_checked": False, "independent_lean_checked": False}
    if any(not set(row.dependencies) <= wanted_set for row in table.values()):
        raise support.WorkingError("the observed inherited cone is not closed under actual source premises")
    targets = {name: _encoded(encode_formula(_closed_formula(table[name].statement))) for name in wanted}
    candidates = {}
    for name, target in targets.items():
        candidates.setdefault(sha256(target.encode()).digest(), []).append(name)
    reports, union = [], set()
    for pin, node_count in SEEDS:
        value = json.loads(_bytes(pin, support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes))
        if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
                or type(value[1]) is not int or value[1] != node_count - 1
                or type(value[3]) is not list or len(value[3]) != node_count):
            raise support.WorkingError("a pinned seed has an unexpected inert JSON envelope")
        nodes = value[3]
        for index, node in enumerate(nodes):
            if (type(node) is not list or len(node) != 4
                    or type(node[0]) is not int or node[0] <= 0
                    or type(node[2]) is not list
                    or any(type(edge) is not int or not 0 <= edge < index for edge in node[2])):
                raise support.WorkingError("a pinned seed has malformed inert target/premise metadata")
        actual_targets = tuple(_encoded(node[1]) for node in nodes)
        if _encoded(value[2]) != actual_targets[-1]:
            raise support.WorkingError("the inert packaging target differs from its root record")
        matched, target_only = {}, set()
        for index, node in enumerate(nodes):
            encoded = actual_targets[index]
            for name in candidates.get(sha256(encoded.encode()).digest(), ()):
                if targets[name] != encoded:
                    continue
                target_only.add(name)
                if tuple(actual_targets[edge] for edge in node[2]) == tuple(
                        targets[dependency] for dependency in table[name].dependencies):
                    matched[name] = index
        before = len(union)
        union.update(matched)
        reports.append({
            "path": pin.path, "bytes": pin.bytes, "sha256": pin.sha256,
            "inert_node_count": node_count, "matching_targets": len(target_only),
            "matching_exact_ordered_premises": len(matched),
            "newly_covered_in_this_order": len(union) - before,
            "matched_node_ids": matched, "original_ha_checked": False,
        })
        del value, nodes, actual_targets
    for pin in (*source_pins, *(pin for pin, _count in SEEDS)):
        support.check_pin(pin, support.ROOT, support.MAX_CATALOG_COMPONENT_BYTES)
    support.require_final_registration()
    alpha_imports = sorted(name for name in sys.modules if name.startswith("peano_lab.library.editions_v"))
    if alpha_imports:
        raise support.WorkingError("a source-only diagnostic unexpectedly imported an Alpha edition")
    return {
        "schema": "peano-working-polynomial-euclidean-seed-syntax-v1",
        "syntax_only": True, "complete_source_inventory": True,
        "selective_source_count": len(source_pins), "inherited_names": 232,
        "observed_recipe_bytes_not_admission_evidence": [pin.path for pin in OBSERVED_RECIPE_PINS],
        "covered_target_and_ordered_premise_names": len(union),
        "missing_names": sorted(wanted_set - union),
        "seeds": reports, "alpha_editions_imported": alpha_imports,
        "proof_bodies_decoded": False, "original_ha_checked": False,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "export_performed": False, "alpha_admission_performed": False,
        "stable_admission_performed": False,
    }


def main():
    report = inspect_seed_syntax()
    elapsed = time.monotonic() - _STARTED
    peak = authoring_rss_bytes()
    if elapsed > 180 or resource.getrlimit(resource.RLIMIT_CPU) != (170, 175):
        raise support.WorkingError("the original source-only process limits changed")
    report.update(seconds=elapsed, peak_rss_bytes=peak, cpu_limits=[170, 175], wall_alarm_seconds=180)
    print(support.canonical(report).decode(), flush=True)
    return 0 if report.get("complete_source_inventory") and not report.get("missing_names") else 1


if __name__ == "__main__":
    raise SystemExit(main())
