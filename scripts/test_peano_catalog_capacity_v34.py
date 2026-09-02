"""Logical-capacity tests only: false transport rows never authorize proofs."""
import ast
from hashlib import sha256
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

import pytest
import peano_catalog_capacity_v34 as capacity
import peano_catalog_shards as old


def rows(count):
    return [{"name": f"transport_false_{i}", "enrollment_index": i,
        "dependencies": [], "checked_use": True, "body_checked": True,
        "membership": "alpha_only", "evidence_status": "alpha_closed",
        "enrollment_origin": "ha", "statement": "0 = 1",
        "script": ["NOT A PROOF"], "notice": "structural test only"}
        for i in range(count)]


@pytest.mark.parametrize("count", [4096, 4097, 8192])
def test_exact_new_capacity_boundaries(count):
    data = rows(count)
    assert capacity.logical_count(count, "count") == count
    assert capacity.counts({"ha": count}, "counts") == {"ha": count}
    edges, levels, counters = capacity.validate_rows(data, count)
    assert (edges, levels, counters["membership"]["alpha_only"]) == (0, 1, count)
    assert data[-1]["enrollment_index"] == count - 1
    assert data[-1]["statement"] == "0 = 1"  # No proof acceptance from transport.


@pytest.mark.parametrize("value", [True, False, 4096.0, "4097", None, -1, 8193])
def test_logical_counts_reject_numeric_lookalikes_and_overflow(value):
    with pytest.raises(old.CatalogError): capacity.logical_count(value, "count")
    with pytest.raises(old.CatalogError): capacity.counts({"ha": value}, "counts")
    with pytest.raises(old.CatalogError): capacity.validate_rows([], value)


def test_8193_actual_rows_reject():
    with pytest.raises(old.CatalogError): capacity.validate_rows(rows(8193), 8193)


@pytest.mark.parametrize("value", [{}, [], {1: 1}, {"": 1}, {"ha": 8192, "other": 1}])
def test_count_object_shape_and_aggregate_budget(value):
    with pytest.raises(old.CatalogError): capacity.counts(value, "counts")


@pytest.mark.parametrize("count", [4097, 8192])
def test_historical_validator_still_rejects_new_capacity(count):
    with pytest.raises(old.CatalogError): old._rows(rows(count), count)
    with pytest.raises(old.CatalogError): old._counts({"ha": count}, "counts")
    assert old.MAX_ROWS == 4096


@pytest.mark.parametrize("value", [True, False, 1.0, "1", -1, 8192, None])
def test_enrollment_indices_remain_exact_integer_order(value):
    data = rows(2)
    data[1]["enrollment_index"] = value
    with pytest.raises(old.CatalogError): capacity.validate_rows(data, 2)


@pytest.mark.parametrize("value", [None, [], True, "row"])
def test_row_requires_exact_json_object(value):
    with pytest.raises(old.CatalogError): capacity.validate_rows([value], 1)


@pytest.mark.parametrize("value", [None, 1, True, "", "bad-name", "transport_false_0"])
def test_names_are_unique_native_identifiers(value):
    data = rows(2)
    data[1]["name"] = value
    with pytest.raises(old.CatalogError): capacity.validate_rows(data, 2)


@pytest.mark.parametrize("value", [None, (), "transport_false_0", [True], ["missing"],
    ["transport_false_1"], ["transport_false_2"], ["transport_false_0", "transport_false_0"]])
def test_dependency_shapes_and_self_forward_missing_duplicate_guards(value):
    data = rows(3)
    data[1]["dependencies"] = value
    with pytest.raises(old.CatalogError): capacity.validate_rows(data, 3)


def test_cycle_rejects_before_any_topological_acceptance():
    data = rows(2)
    data[0]["dependencies"] = [data[1]["name"]]
    data[1]["dependencies"] = [data[0]["name"]]
    with pytest.raises(old.CatalogError): capacity.validate_rows(data, 2)


def test_existing_256_dependencies_and_65536_edges_are_exact_bounds():
    data = rows(513)
    ancestors = [row["name"] for row in data[:256]]
    for row in data[256:512]: row["dependencies"] = ancestors[:]
    assert capacity.validate_rows(data, 513)[:2] == (65536, 2)
    data[-1]["dependencies"] = [data[0]["name"]]
    with pytest.raises(old.CatalogError, match="edge budget"):
        capacity.validate_rows(data, 513)
    data = rows(258)
    data[-1]["dependencies"] = [row["name"] for row in data[:257]]
    with pytest.raises(old.CatalogError, match="per-row budget"):
        capacity.validate_rows(data, 258)


@pytest.mark.parametrize("key", ["checked_use", "body_checked"])
@pytest.mark.parametrize("value", [1, False, None, "true"])
def test_declared_flags_require_exact_true_but_are_not_proof_authority(key, value):
    data = rows(1)
    data[0][key] = value
    with pytest.raises(old.CatalogError): capacity.validate_rows(data, 1)


@pytest.mark.parametrize("key", ["membership", "evidence_status", "enrollment_origin"])
@pytest.mark.parametrize("value", [1, None, ""])
def test_counter_labels_remain_exact_nonempty_strings(key, value):
    data = rows(1)
    data[0][key] = value
    with pytest.raises(old.CatalogError): capacity.validate_rows(data, 1)


def test_only_explicit_logical_capacity_differs_and_no_historical_global_write():
    assert capacity.MAX_ROWS == 8192 and old.MAX_ROWS == 4096
    for key in ("MAX_CATALOG_BYTES", "MAX_REFERENCED_DOCUMENTS", "MAX_DEPENDENCIES_PER_ROW",
                "MAX_EDGES", "MAX_JSON_CONTAINERS", "MAX_JSON_DEPTH", "MAX_JSON_VALUES"):
        assert getattr(capacity, key) == getattr(old, key)
    assert (capacity.MAX_CATALOG_BYTES, capacity.MAX_REFERENCED_DOCUMENTS,
            capacity.MAX_DEPENDENCIES_PER_ROW, capacity.MAX_EDGES,
            capacity.MAX_JSON_CONTAINERS, capacity.MAX_JSON_DEPTH, capacity.MAX_JSON_VALUES
            ) == (67108864, 2, 256, 65536, 65536, 256, 5000000)
    tree = ast.parse(Path(capacity.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)):
            pytest.fail("capacity code must not mutate historical module globals")
    old_function = next(n for n in ast.parse(Path(old.__file__).read_text()).body
                        if isinstance(n, ast.FunctionDef) and n.name == "_rows")
    new_function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == "validate_rows")
    # Every original row-validation statement remains exact, after the one new
    # exact-type check on expected_count. MAX_ROWS resolves only in this module.
    assert [ast.dump(n) for n in new_function.body[1:]] == [ast.dump(n) for n in old_function.body]
    assert not any(name.startswith("peano_lab") for name in sys.modules)


def _main(filename=__file__, argv=None):
    """Record exact real case/phase outputs in one original bounded process."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pytest-select", default="")
    parser.add_argument("--case-start", type=int, default=0)
    parser.add_argument("--case-count", type=int)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args(argv)
    if args.case_start < 0 or args.case_count is not None and args.case_count <= 0:
        parser.error("invalid exact window")
    scriptdir = Path(__file__).resolve().parent
    paths = sorted({*scriptdir.glob("peano_catalog_shards*.py"), Path(capacity.__file__).resolve(),
                    Path(__file__).resolve(), Path(filename).resolve()})
    def pins():
        return [[str(path), len(raw), sha256(raw).hexdigest()]
                for path in paths for raw in (path.read_bytes(),)]
    before = pins()
    class Window:
        selected = None
        def __init__(self): self.phases = []
        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            chosen = items[args.case_start:None if args.case_count is None else args.case_start+args.case_count]
            if not chosen or args.case_count is not None and len(chosen) != args.case_count:
                raise ValueError("the exact nonempty case window is unavailable")
            names = {item.nodeid for item in chosen}
            config.hook.pytest_deselected(items=[item for item in items if item.nodeid not in names])
            items[:] = chosen
            self.selected = [item.nodeid for item in chosen]
        def pytest_runtest_logreport(self, report):
            self.phases.append([report.nodeid, report.when, report.outcome,
                                report.duration, bool(getattr(report, "wasxfail", False))])
    plugin = Window()
    options = [str(Path(filename).resolve()), "-q", "--disable-warnings", "-k", args.pytest_select]
    if args.collect_only: options.append("--collect-only")
    status = int(pytest.main(options, plugins=[plugin]))
    after = pins()
    expected = {(nodeid, phase) for nodeid in plugin.selected or [] for phase in ("setup", "call", "teardown")}
    actual = [(record[0], record[1]) for record in plugin.phases]
    phase_ok = (len(actual) == len(expected) and set(actual) == expected
                and all(record[2] == "passed" and not record[4] for record in plugin.phases))
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    if sys.platform != "darwin": peak *= 1024
    if before != after or not 0 < peak <= 1536*1024*1024 or not args.collect_only and not phase_ok:
        status = status or 1
    result = {"observation_only": True, "proof_authority": False, "selected_ids": plugin.selected,
        "phases": plugin.phases, "collect_only": args.collect_only, "exit_code": status,
        "source_pins_before": before, "source_pins_after": after,
        "elapsed_seconds": time.monotonic()-STARTED, "peak_rss_bytes": peak,
        "cpu_limits": list(resource.getrlimit(resource.RLIMIT_CPU)), "wall_seconds": 180}
    print("CAPACITY_TRANSPORT_OBSERVATION " + json.dumps(result, sort_keys=True), flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(_main())
