"""Working-only polynomial Euclidean syntax, ownership, and exact inputs.

The current v32 parent is syntax input, not a receipt or a proof oracle. The
unchanged assembler executes against its immutable v30 base; any later Alpha
entry passed through its frontier remains inherited Alpha-v32 support. Only
the four exact working factories may be counted as the 81 new research rows.
No old module, factory, source, cache, limit, or admission table is patched.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import importlib.util
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING_RELATIVE = "research/arithmetic-library/working/prime-field-euclidean-v1"
if HERE != ROOT / WORKING_RELATIVE or not (ROOT / "peano-lab/py/peano_lab").is_dir():
    raise RuntimeError("the Euclidean integration must remain in its exact working directory")
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import constructive_g009_support as inherited
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import TheoremSpec, _closed_formula


closure = inherited.closure
FilePin = inherited.FilePin
CandidateState = inherited.CandidateState
canonical, bounded_bytes, check_pin = inherited.canonical, inherited.bounded_bytes, inherited.check_pin
MAX_SOURCE_BYTES = inherited.MAX_SOURCE_BYTES
MAX_CATALOG_COMPONENT_BYTES = inherited.MAX_CATALOG_COMPONENT_BYTES
EXPECTED_NEW_COUNT = 81
PARENT_COUNT, PARENT_STABLE_COUNT = 3971, 432
PARENT_IDENTITY_SHA256 = "2821b3ef1e5761283af9c015b05c0a02ede073554412585a1ff5ead455269939"
PARENT_ENROLLMENT_SHA256 = "911df25bac9987e73d3313c90bdd0602e9e7e6f3f4af00c81701d35b14268cb5"


class WorkingError(ValueError):
    """A working source, exact dependency, or unchanged proof boundary failed."""


@dataclass(frozen=True, slots=True)
class Factory:
    module: str
    count: int
    source_bytes: int
    source_sha256: str
    test_bytes: int
    test_sha256: str

    @property
    def factory(self):
        return "make_" + self.module + "_theorems"

    @property
    def source(self):
        return FilePin(WORKING_RELATIVE + "/" + self.module + ".py",
                       self.source_bytes, self.source_sha256)

    @property
    def test(self):
        return FilePin(WORKING_RELATIVE + "/test_" + self.module + ".py",
                       self.test_bytes, self.test_sha256)


# The triangular module supplies actual proof dependencies of the later
# representation and division modules. Its position does not change any
# within-factory order or mathematical source.
FACTORIES = (
    Factory("prime_field_polynomial_convolution_triangular_candidate", 8, 16677,
            "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f",
            9162, "e6bf4d2a0b2b00336b8d83b4ffe5d068e34e3d5bd44e8af4b995ca2723289822"),
    Factory("prime_field_polynomial_representation_candidate", 30, 42623,
            "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a",
            25517, "75a2cee90850ff07468b1d568ce4d3665f8006fdbb892c5838186abbc8fd57b7"),
    Factory("prime_field_polynomial_division_candidate", 25, 47986,
            "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2",
            23978, "c4f7555b19e88789c4a561ec5b66d1f9487f44a32b388f2beea90f9ec42eed3b"),
    Factory("prime_field_polynomial_distributivity_candidate", 18, 26118,
            "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86",
            21925, "d6200ef1e0447f3efb98461ce343a1a3ae5530f74490bd4b7782cbc13ed2e9a6"),
)
MATH_SOURCE_PINS = tuple(owner.source for owner in FACTORIES)
MATH_TEST_PINS = tuple(owner.test for owner in FACTORIES)
PARENT_RUNTIME_PINS = (
    FilePin("peano-lab/py/peano_lab/library/editions_v32.py", 16128,
            "69707c34aed369163cc0cce95db7e6078302fe639df75210176e9b53ab719785"),
    FilePin("peano-lab/py/peano_lab/library/alpha_enrollment_v32.py", 10725,
            "81003d179548d50417ef093e1e7c6fc1006ec72ff06f39d1e0a47e56335172c6"),
    FilePin("peano-lab/py/peano_lab/library/campaign_research_v32_closure.py", 42913,
            "cdbc803669fc35c0d8b91e06f5f79d1470ffc2355e041fc12c205ec21dfb3ea0"),
)
PRINCIPAL_ROOTS = (
    "prime_field_polynomial_division_execution_exists",
    "prime_field_polynomial_division_remainder_degree",
    "prime_field_polynomial_division_coefficient_identity",
    "prime_field_polynomial_trim_equivalent",
    "prime_field_polynomial_add_left_pad_transport",
    "prime_field_polynomial_left_distributive_products_exists",
    "prime_field_polynomial_right_distributive_products_exists",
    "prime_field_convolution_prefix_left_subtract",
)

# Actual frozen local specifications and the installed v32 catalogue after its
# fifteen genuine proof gates. These byte identities do not accept any of the
# 81 working proofs; the separate complete working artifact remains unset.
NEW_SPECS_SHA256 = "b9fef22dbce3893dfadb7c9c5192c7a5a3c8d717ae112a0fff9e016aa68162fb"
PARENT_CATALOG_PINS: tuple[FilePin, ...] = (
    FilePin("artifacts/peano-library/alpha/catalog-v32.json", 603900,
            "41b9f387d88a5a4f0fe5ee2bd5578f37a27a4657b0a80f1a1a2cb5109f69a623"),
    FilePin("artifacts/peano-library/alpha/catalog-v30.json", 66503303,
            "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"),
    FilePin("artifacts/peano-library/alpha/catalog-v32-delta.json", 34813857,
            "d7739760283864277399ff8c524c29cc6561b1a56763fd5c86768fc21499d1e6"),
)
CONTROL_FILES = (
    "working_euclidean_support.py", "export_working_euclidean.py",
    "check_working_euclidean.py", "test_working_euclidean_integration.py",
    "working-euclidean-integration-rfc-v1.md",
)


def require_working_sources():
    if (type(FACTORIES) is not tuple or any(type(owner) is not Factory for owner in FACTORIES)
            or tuple(owner.count for owner in FACTORIES) != (8, 30, 25, 18)
            or type(MATH_SOURCE_PINS) is not tuple or type(MATH_TEST_PINS) is not tuple
            or MATH_SOURCE_PINS != tuple(owner.source for owner in FACTORIES)
            or MATH_TEST_PINS != tuple(owner.test for owner in FACTORIES)):
        raise WorkingError("the exact four-factory working inventory changed")
    for pin in (*MATH_SOURCE_PINS, *MATH_TEST_PINS):
        check_pin(pin, ROOT, MAX_SOURCE_BYTES)


def require_parent_runtime():
    if (type(PARENT_RUNTIME_PINS) is not tuple
            or any(type(pin) is not FilePin for pin in PARENT_RUNTIME_PINS)
            or tuple(pin.path for pin in PARENT_RUNTIME_PINS) != tuple(
                "peano-lab/py/peano_lab/library/" + name + ".py" for name in (
                    "editions_v32", "alpha_enrollment_v32", "campaign_research_v32_closure"))):
        raise WorkingError("the exact current-parent runtime source inventory changed")
    for pin in PARENT_RUNTIME_PINS:
        check_pin(pin, ROOT, MAX_SOURCE_BYTES)


def require_final_registration():
    require_working_sources()
    require_parent_runtime()
    expected_paths = (
        "artifacts/peano-library/alpha/catalog-v32.json",
        closure.PARENT_CATALOG,
        "artifacts/peano-library/alpha/catalog-v32-delta.json",
    )
    if (type(NEW_SPECS_SHA256) is not str or re.fullmatch(r"[0-9a-f]{64}", NEW_SPECS_SHA256) is None
            or type(PARENT_CATALOG_PINS) is not tuple
            or any(type(pin) is not FilePin for pin in PARENT_CATALOG_PINS)
            or tuple(pin.path for pin in PARENT_CATALOG_PINS) != expected_paths):
        raise WorkingError("the actual complete working specs/current v32 catalogue are not registered")
    for pin in PARENT_CATALOG_PINS:
        check_pin(pin, ROOT, MAX_CATALOG_COMPONENT_BYTES)
    import peano_catalog_shards_v32
    bindings = peano_catalog_shards_v32.verify_catalog_bindings(
        ROOT / PARENT_CATALOG_PINS[0].path, expected_sha256=PARENT_CATALOG_PINS[0].sha256)
    actual = tuple((item.path.relative_to(ROOT).as_posix(), item.bytes, item.sha256)
                   for item in bindings.files)
    if actual != tuple((pin.path, pin.bytes, pin.sha256) for pin in PARENT_CATALOG_PINS):
        raise WorkingError("the exact three current catalogue component identities changed")


def load_candidate_state(*, final=False):
    if type(final) is not bool:
        raise WorkingError("final must be an explicit Boolean")
    require_working_sources()
    if final:
        require_final_registration()
    rows = []
    for owner in FACTORIES:
        path = HERE / (owner.module + ".py")
        raw = bounded_bytes(path, MAX_SOURCE_BYTES)
        if (len(raw), sha256(raw).hexdigest()) != (owner.source_bytes, owner.source_sha256):
            raise WorkingError("a frozen working factory changed before loading")
        # These private aliases are not production library names. Every old
        # import remains the normal existing absolute peano_lab import.
        alias = "_working_euclidean_v1_" + owner.module
        previous = sys.modules.get(alias)
        if previous is not None and Path(getattr(previous, "__file__", "")).resolve() != path:
            raise WorkingError("a private working factory alias shadows another file")
        spec = importlib.util.spec_from_file_location(alias, path)
        if spec is None or spec.loader is None:
            raise WorkingError("the exact working mathematical source is not loadable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[alias] = module
        exec(compile(raw, str(path), "exec"), module.__dict__)
        factory = getattr(module, owner.factory, None)
        if not callable(factory) or getattr(factory, "__module__", None) != alias:
            raise WorkingError("the exact working theorem factory is missing")
        values = factory(TheoremSpec)
        if type(values) is not tuple or len(values) != owner.count:
            raise WorkingError("a complete working factory has the wrong row inventory")
        rows.extend(values)
        if bounded_bytes(path, MAX_SOURCE_BYTES) != raw:
            raise WorkingError("a working mathematical source changed during its factory call")
    rows = tuple(rows)
    closure._validate_frontier(rows)
    names = {row.name for row in rows}
    seen = set()
    for row in rows:
        if not (set(row.dependencies) & names) <= seen:
            raise WorkingError("the working factory order has a forward or cyclic dependency")
        seen.add(row.name)
    digest = closure._specs_digest(rows)
    if (len(rows) != EXPECTED_NEW_COUNT or not set(PRINCIPAL_ROOTS) <= names
            or digest != NEW_SPECS_SHA256):
        raise WorkingError("the complete 81-row ordered working specification changed")
    return CandidateState(rows, MATH_SOURCE_PINS, digest)


def local_manifest():
    """Actual four-factory syntax only; does not load an Alpha edition."""
    state = load_candidate_state()
    names = {row.name for row in state.rows}
    external = sorted({name for row in state.rows for name in row.dependencies} - names)
    used = {name for row in state.rows for name in row.dependencies}
    return {
        "schema": "peano-working-polynomial-euclidean-syntax-v1",
        "syntax_only": True, "new_rows": len(state.rows),
        "factory_counts": [[owner.module, owner.count] for owner in FACTORIES],
        "specs_sha256": state.specs_sha256,
        "new_dependency_edges": sum(len(row.dependencies) for row in state.rows),
        "new_script_commands": sum(len(row.script) for row in state.rows),
        "ordered_names": [row.name for row in state.rows],
        "direct_external_dependencies": external,
        "maximal_working_roots": [row.name for row in state.rows if row.name not in used],
        "ordinary_principals": list(PRINCIPAL_ROOTS),
        "global_current_parent_novelty_checked": False,
        "whole_original_ha_checked": False, "independent_lean_checked": False,
        "ordinary_principals_checked": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def current_parent_specs():
    require_parent_runtime()
    from peano_lab.library import editions_v32 as parent
    parent.require_research_seal()
    if (len(parent.ALPHA_CHECKED_SPECS) != PARENT_COUNT
            or len(parent.STABLE_SPECS) != PARENT_STABLE_COUNT
            or parent.ALPHA_V32_IDENTITY_SHA256 != PARENT_IDENTITY_SHA256
            or parent.ALPHA_V32_ENROLLMENT_SHA256 != PARENT_ENROLLMENT_SHA256
            or parent.STABLE_EDITION is not parent.v31.STABLE_EDITION
            or any(new is not old for new, old in zip(parent.ALPHA_ENTRIES, parent.v31.ALPHA_ENTRIES))):
        raise WorkingError("the immutable current v32 parent or Stable identity changed")
    if closure.parent_snapshot().specs != parent.ALPHA_CHECKED_SPECS[:closure.PARENT_COUNT]:
        raise WorkingError("the unchanged v30 assembler base is not the exact current parent prefix")
    return parent.ALPHA_CHECKED_SPECS


@dataclass(frozen=True, slots=True)
class SupportSelection:
    owned: tuple[TheoremSpec, ...]
    current_support: tuple[str, ...]
    parent_support: tuple[str, ...]
    frontier: tuple[TheoremSpec, ...]
    plan: closure.BottomLayerPlan
    complete_specs: tuple[TheoremSpec, ...]

    def role(self, name):
        if name in {row.name for row in self.owned}:
            return "new_working_owned_theorem"
        if name in self.current_support:
            return "new_working_cross_track_support"
        if name in self.parent_support:
            return "inherited_alpha_v32"
        raise WorkingError("a role was requested outside the complete working cone")


def select_support(new_rows, owned_names):
    closure._validate_frontier(new_rows)
    parent = current_parent_specs()
    complete = inherited.dependency_cone(parent, new_rows, owned_names)
    included, owned_set = {row.name for row in complete}, set(owned_names)
    inherited_names = {row.name for row in parent}
    promoted = tuple(row for row in parent[closure.PARENT_COUNT:] if row.name in included)
    current = tuple(row for row in new_rows if row.name in included)
    execution_frontier = (*promoted, *current)
    plan = closure.bottom_layer_plan(execution_frontier)
    if (tuple(row.name for row in plan.rows) != tuple(row.name for row in complete)
            or any(actual.dependencies != expected.dependencies
                   or actual.statement_sha256 != sha256(expected.statement.encode()).hexdigest()
                   for actual, expected in zip(plan.rows, complete, strict=True))
            or not set(plan.root_names) <= owned_set):
        raise WorkingError("the unchanged assembler plan differs from the exact v32 dependency cone")
    return SupportSelection(tuple(row for row in new_rows if row.name in owned_set),
        tuple(row.name for row in current if row.name not in owned_set),
        tuple(row.name for row in complete if row.name in inherited_names),
        execution_frontier, plan, complete)


def parent_seed_paths():
    """Authenticate all 41 existing providers; no hash grants proof acceptance."""
    current_parent_specs()
    paths = list(inherited.parent_seed_paths())
    from peano_lab.library import campaign_research_v32_closure as research
    research.validate_research_source_bytes()
    for family in research.RESEARCH_FAMILIES:
        pin = FilePin(family.artifact, family.artifact_bytes, family.artifact_sha256)
        check_pin(pin, ROOT, closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
        paths.append(ROOT / pin.path)
    if len(paths) != 41 or len(set(paths)) != 41:
        raise WorkingError("the exact 20+19+2 current Alpha proof-data providers changed")
    return tuple(paths)


def statement_duplicates(new_rows):
    """Exact parsed FormulaArena comparison against all 3971 and one another."""
    closure._validate_frontier(new_rows)
    indexed, duplicates = {}, []
    for row in new_rows:
        encoded = FormulaArena().freeze(_closed_formula(row.statement)).to_json()
        key = sha256(encoded.encode()).digest()
        duplicates.extend((row.name, name) for name, other in indexed.get(key, ()) if encoded == other)
        indexed.setdefault(key, []).append((row.name, encoded))
    for row in current_parent_specs():
        encoded = FormulaArena().freeze(_closed_formula(row.statement)).to_json()
        duplicates.extend((name, row.name) for name, other in indexed.get(sha256(encoded.encode()).digest(), ())
                          if encoded == other)
    return tuple(duplicates)


def state_binding(state, *, final=False):
    if type(final) is not bool or type(state) is not CandidateState:
        raise WorkingError("an exact working state and explicit Boolean are required")
    if (type(state.rows) is not tuple or len(state.rows) != EXPECTED_NEW_COUNT
            or any(type(row) is not TheoremSpec for row in state.rows)
            or state.sources != MATH_SOURCE_PINS
            or state.specs_sha256 != NEW_SPECS_SHA256
            or closure._specs_digest(state.rows) != state.specs_sha256):
        raise WorkingError("the supplied working syntax state was changed")
    # Even draft proof-data authoring uses the actually installed exact parent,
    # not merely prospective runtime counts or an unregistered catalogue.
    require_final_registration()
    import check_alpha_v32_research as current_audit
    parent_binding = current_audit.source_binding()
    providers = parent_seed_paths()
    controls = []
    for name in CONTROL_FILES:
        raw = bounded_bytes(HERE / name, MAX_SOURCE_BYTES)
        controls.append((WORKING_RELATIVE + "/" + name, len(raw), sha256(raw).hexdigest()))
    return sha256(canonical({
        "parent_source_binding": parent_binding,
        "parent": [PARENT_COUNT, PARENT_STABLE_COUNT, PARENT_IDENTITY_SHA256, PARENT_ENROLLMENT_SHA256],
        "parent_runtime_pins": [asdict(pin) for pin in PARENT_RUNTIME_PINS],
        "parent_catalog_pins": [asdict(pin) for pin in PARENT_CATALOG_PINS],
        "provider_paths": [path.relative_to(ROOT).as_posix() for path in providers],
        "math": [asdict(pin) for pin in MATH_SOURCE_PINS],
        "tests": [asdict(pin) for pin in MATH_TEST_PINS],
        "controls": controls, "specs_sha256": state.specs_sha256,
        "expected_specs_sha256": NEW_SPECS_SHA256,
        "principal_roots": PRINCIPAL_ROOTS, "final_registration_required": final,
    })).hexdigest()
