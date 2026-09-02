"""Explicit v34 logical catalogue capacity; no proof or admission authority.

Only the logical row/count/enrollment budget is 8192. Historical codecs retain
4096 and are never mutated. Byte, edge, dependency and JSON bounds are original.
"""
from collections import Counter
import peano_catalog_shards as previous

CatalogError = previous.CatalogError
MAX_ROWS = 8192
MAX_CATALOG_BYTES = previous.MAX_CATALOG_BYTES
MAX_REFERENCED_DOCUMENTS = previous.MAX_REFERENCED_DOCUMENTS
MAX_DEPENDENCIES_PER_ROW = previous.MAX_DEPENDENCIES_PER_ROW
MAX_EDGES = previous.MAX_EDGES
MAX_JSON_CONTAINERS = previous.MAX_JSON_CONTAINERS
MAX_JSON_DEPTH = previous.MAX_JSON_DEPTH
MAX_JSON_VALUES = previous.MAX_JSON_VALUES
_integer = previous._integer
_NAME = previous._NAME


def logical_count(value, label, *, minimum=0):
    """Exact v34 logical cardinality; bools and numeric lookalikes reject."""
    return _integer(value, label, minimum=minimum, maximum=MAX_ROWS)


def counts(value, label):
    """Original count-object semantics with the explicit v34 row budget."""
    if type(value) is not dict or not value or len(value) > MAX_ROWS:
        raise CatalogError(f"{label} must be a nonempty bounded count object")
    for key, number in value.items():
        if type(key) is not str or not key:
            raise CatalogError(f"{label} contains an invalid key")
        logical_count(number, label)
    if sum(value.values()) > MAX_ROWS:
        raise CatalogError(f"{label} exceeds the v34 row budget")
    return value


def validate_rows(rows: object, expected_count: int) -> tuple[int, int, dict[str, Counter]]:
    logical_count(expected_count, "expected row count")
    if type(rows) is not list or len(rows) != expected_count or len(rows) > MAX_ROWS:
        raise CatalogError("catalogue has the wrong exact bounded row count")
    layers = {}
    edges = 0
    counters = {key: Counter() for key in ("membership", "evidence_status", "enrollment_origin")}
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise CatalogError("every theorem row must be a JSON object")
        name = row.get("name")
        if type(name) is not str or _NAME.fullmatch(name) is None or name in layers:
            raise CatalogError("catalogue theorem names must be unique identifiers")
        if _integer(row.get("enrollment_index"), "enrollment_index", maximum=MAX_ROWS - 1) != index:
            raise CatalogError("catalogue enrollment indices are not in exact canonical order")
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or len(dependencies) > MAX_DEPENDENCIES_PER_ROW:
            raise CatalogError("theorem dependencies exceed the existing per-row budget or are not a list")
        if any(type(dep) is not str for dep in dependencies) or len(set(dependencies)) != len(dependencies):
            raise CatalogError("theorem dependencies must be distinct names")
        if any(dep not in layers for dep in dependencies):
            raise CatalogError("missing, self, forward, or cyclic theorem dependency")
        edges += len(dependencies)
        if edges > MAX_EDGES:
            raise CatalogError("catalogue exceeds the existing dependency-edge budget")
        layers[name] = max((layers[dep] for dep in dependencies), default=-1) + 1
        if row.get("checked_use") is not True or row.get("body_checked") is not True:
            raise CatalogError("catalogue checked-use flags disagree with the declared fully checked release")
        for key, counter in counters.items():
            value = row.get(key)
            if type(value) is not str or not value:
                raise CatalogError(f"theorem row has invalid {key}")
            counter[value] += 1
    return edges, max(layers.values(), default=-1) + 1, counters


# Named compatibility seams for new-version builders only.
_rows = validate_rows
_counts = counts
