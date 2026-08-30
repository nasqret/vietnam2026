"""Separate working-only 81 + 9 + 23 proof-data integration.

The previous 81 rows remain a separately verified, non-admitted working
checkpoint. They are not reclassified as inherited Alpha. The current Alpha
parent is still exactly v32/3971 with Stable432 unchanged. Byte bindings and
saved observations never substitute for fresh original proof checking.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from hashlib import sha256
import importlib.util
from pathlib import Path
import re
import sys
from types import ModuleType

import working_euclidean_support as base


HERE = Path(__file__).resolve().parent
ROOT, WORKING_RELATIVE = base.ROOT, base.WORKING_RELATIVE
if HERE != base.HERE or Path(base.__file__).resolve() != HERE / "working_euclidean_support.py":
    raise RuntimeError("the extension must use the exact preserved working81 adapter")

closure, FilePin = base.closure, base.FilePin
TheoremSpec = base.TheoremSpec
canonical, bounded_bytes, check_pin = base.canonical, base.bounded_bytes, base.check_pin
MAX_SOURCE_BYTES = base.MAX_SOURCE_BYTES
EXPECTED_PRIOR_WORKING_COUNT, EXPECTED_ADDED_COUNT, EXPECTED_COMBINED_COUNT = 81, 32, 113
EXPECTED_FACTORIES = (
    ("prime_field_polynomial_division_uniqueness_candidate", 9),
    ("prime_field_polynomial_convolution_padding_candidate", 23),
)
PRINCIPAL_ROOTS = (
    "prime_field_polynomial_division_execution_functional",
    "prime_field_polynomial_division_execution_exists_unique",
    "prime_field_polynomial_convolution_both_left_paddings_equivalent",
    "prime_field_polynomial_convolution_both_left_paddings_exists",
)


class ExtensionError(ValueError):
    """A frozen input, exact ownership, or original proof boundary failed."""


def _pin(name, size, digest):
    return FilePin(WORKING_RELATIVE + "/" + name, size, digest)


# Literal preservation records. Observation files are authenticated but never
# decoded or treated as proof authority by this adapter.
PRESERVED81_PINS = (
    _pin("working_euclidean_support.py", 18552, "80e73f977f2464e2f62939610667def8bbf96f19e4d95bf734c52969c39cec4a"),
    _pin("export_working_euclidean.py", 7319, "5b5ff76c08c01240baa239ca189ad3a372f5d6e7777a0aa9b12eaf88a37b19de"),
    _pin("check_working_euclidean.py", 9619, "390033da96271b2347a99d5fe5f033d1c6c60f0b82496a1707df6260de353603"),
    _pin("test_working_euclidean_integration.py", 18658, "04f66780d6b0d7408b72b8e9a8cdc54772d1593e03dfb2e61579a44410ba1038"),
    _pin("working-euclidean-integration-rfc-v1.md", 9958, "f39c915949e5ca9312553836e7672c4c1b07bffb8b6d8a4efe3d3a0c02d560d9"),
    _pin("prime_field_polynomial_convolution_triangular_candidate.py", 16677, "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f"),
    _pin("prime_field_polynomial_representation_candidate.py", 42623, "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a"),
    _pin("prime_field_polynomial_division_candidate.py", 47986, "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2"),
    _pin("prime_field_polynomial_distributivity_candidate.py", 26118, "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86"),
    _pin("test_prime_field_polynomial_convolution_triangular_candidate.py", 9162, "e6bf4d2a0b2b00336b8d83b4ffe5d068e34e3d5bd44e8af4b995ca2723289822"),
    _pin("test_prime_field_polynomial_representation_candidate.py", 25517, "75a2cee90850ff07468b1d568ce4d3665f8006fdbb892c5838186abbc8fd57b7"),
    _pin("test_prime_field_polynomial_division_candidate.py", 23978, "c4f7555b19e88789c4a561ec5b66d1f9487f44a32b388f2beea90f9ec42eed3b"),
    _pin("test_prime_field_polynomial_distributivity_candidate.py", 21925, "d6200ef1e0447f3efb98461ce343a1a3ae5530f74490bd4b7782cbc13ed2e9a6"),
    _pin("augment_inherited_polynomial_seed.py", 10355, "e9dce56cff718bdce62ecfb258e4f2eb640053c010a1ebd1e8fb433f1b4f3a0f"),
    _pin("inspect_working_seed_syntax.py", 11886, "f4b374f6696d8772bbd24a4dd830e9e5679ac2a58f8a81489a44dfa591858f61"),
    _pin("artifacts/inherited-polynomial-products-three-lemmas-seed-v1.json", 812095,
         "f4d2567e664ae3ad6092e6b54a6599d2858ac4fafc0b4343085a218da6735624"),
    _pin("artifacts/working-prime-field-euclidean-proof-bundle-v1.json", 1635441,
         "3614e9504b84cfd24a52780d54ddc9eb16e49bf2df996c99664c9427e9a9fd83"),
    _pin("working-81-global-syntax-v1.json", 10290, "38e99d5574810ff9820b94952d11fa7b4f17a09a030c36fd42e4df94f2bf23b7"),
    _pin("working-81-verification-observations-v1.json", 14806, "28fba8440872bcc852f43ce0511d3a7659edc6da9a773bf373f037c7495be5ac"),
)
_PRESERVED81_PATHS = tuple(pin.path for pin in PRESERVED81_PINS)
PRIOR81_ARTIFACT = PRESERVED81_PINS[16]
WORKING_ALIAS_PINS = (
    ("peano_lab.library.prime_field_polynomial_division_candidate", PRESERVED81_PINS[7]),
    ("peano_lab.library.prime_field_polynomial_representation_candidate", PRESERVED81_PINS[6]),
)


@dataclass(frozen=True, slots=True)
class Factory:
    module: str
    count: int
    source_bytes: int
    source_sha256: str
    test_bytes: int
    test_sha256: str
    specs_sha256: str

    @property
    def factory(self):
        return "make_" + self.module + "_theorems"

    @property
    def source(self):
        return _pin(self.module + ".py", self.source_bytes, self.source_sha256)

    @property
    def test(self):
        return _pin("test_" + self.module + ".py", self.test_bytes, self.test_sha256)


# Both authors' actual final source/test/specification freezes. The complete
# ordered specification digest is measured separately by the local phase.
EXTENSION_FACTORIES: tuple[Factory, ...] = (
    Factory("prime_field_polynomial_division_uniqueness_candidate", 9, 23258,
            "6a9d9ebe1f72202743e5df2c069b9aa367fdb3d61108f1d9354cdc9276ab2d15",
            15599, "b74083e6707eb83e7fab3efa3f610d562edf2168511b07c5995f9ef9f7f588e2",
            "41bb0ad58b6e7ef3cc6fefba62bcc75ae0fe18a10fb87019905cb43e810ae1da"),
    Factory("prime_field_polynomial_convolution_padding_candidate", 23, 39740,
            "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007",
            27054, "7632654e36e18cf7c872bd29dd783a55cf597e33e7b5369be178a2d2f42b87f9",
            "5bd7b23cf69bfd35fbf99c47da09a0751c3e267b8cdc31a078b2b65b99f5d619"),
)
COMBINED_SPECS_SHA256: str | None = "aac561ef7706c53af00464feba7d0f4a51a3e3960404dba4a53d80405913b8a9"
CONTROL_FILES = (
    "working_euclidean_extension_support.py", "export_working_euclidean_extension.py",
    "check_working_euclidean_extension.py", "test_working_euclidean_extension.py",
    "working-euclidean-extension-rfc-v1.md",
)


def _read(pin):
    maximum = closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes
    check_pin(pin, ROOT, maximum)
    raw = bounded_bytes(ROOT / pin.path, maximum)
    if (len(raw), sha256(raw).hexdigest()) != (pin.bytes, pin.sha256):
        raise ExtensionError("an exact pinned extension input changed during reading")
    return raw


def require_preserved81():
    if (type(PRESERVED81_PINS) is not tuple or len(PRESERVED81_PINS) != 19
            or any(type(pin) is not FilePin for pin in PRESERVED81_PINS)
            or any(type(pin.bytes) is not int or pin.bytes <= 0 or type(pin.sha256) is not str
                   or re.fullmatch(r"[0-9a-f]{64}", pin.sha256) is None for pin in PRESERVED81_PINS)
            or tuple(pin.path for pin in PRESERVED81_PINS) != _PRESERVED81_PATHS
            or PRIOR81_ARTIFACT != PRESERVED81_PINS[16]):
        raise ExtensionError("the exact separately verified working81 preservation inventory changed")
    for pin in PRESERVED81_PINS:
        check_pin(pin, ROOT, closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    base.require_working_sources()
    base.require_final_registration()


def require_extension_sources():
    if (type(EXTENSION_FACTORIES) is not tuple
            or any(type(owner) is not Factory for owner in EXTENSION_FACTORIES)
            or any(type(owner.module) is not str or type(owner.count) is not int
                   or type(owner.source_bytes) is not int or owner.source_bytes <= 0
                   or type(owner.test_bytes) is not int or owner.test_bytes <= 0
                   for owner in EXTENSION_FACTORIES)
            or tuple((owner.module, owner.count) for owner in EXTENSION_FACTORIES) != EXPECTED_FACTORIES):
        raise ExtensionError("both final 9+23 source and test freezes are required")
    for owner in EXTENSION_FACTORIES:
        if (type(owner.specs_sha256) is not str
                or re.fullmatch(r"[0-9a-f]{64}", owner.specs_sha256) is None):
            raise ExtensionError("an exact added-factory specification identity is missing")
        check_pin(owner.source, ROOT, MAX_SOURCE_BYTES)
        check_pin(owner.test, ROOT, MAX_SOURCE_BYTES)


@contextmanager
def temporary_working_aliases():
    """Install only absent pinned working names, never replace a runtime."""
    if WORKING_ALIAS_PINS != (
            ("peano_lab.library.prime_field_polynomial_division_candidate", PRESERVED81_PINS[7]),
            ("peano_lab.library.prime_field_polynomial_representation_candidate", PRESERVED81_PINS[6])):
        raise ExtensionError("only the two exact frozen working import aliases are permitted")
    import peano_lab.library as package
    inserted = []
    try:
        for alias, pin in WORKING_ALIAS_PINS:
            short = alias.rsplit(".", 1)[1]
            if alias in sys.modules or short in vars(package):
                raise ExtensionError("an existing runtime/working module cannot be replaced: " + alias)
            if importlib.util.find_spec(alias) is not None:
                raise ExtensionError("an actual runtime source already owns the requested working alias")
            path = ROOT / pin.path
            raw = _read(pin)
            specification = importlib.util.spec_from_file_location(alias, path)
            if specification is None or specification.loader is None:
                raise ExtensionError("a pinned working import has no exact loader")
            module = importlib.util.module_from_spec(specification)
            sys.modules[alias] = module
            inserted.append((alias, module))
            exec(compile(raw, str(path), "exec"), module.__dict__)
            if (Path(module.__file__).resolve() != path or _read(pin) != raw
                    or sys.modules.get(alias) is not module):
                raise ExtensionError("a working alias changed while loading its pinned source")
        yield tuple(module for _alias, module in inserted)
    finally:
        foreign = []
        for alias, module in reversed(inserted):
            if sys.modules.get(alias) is module:
                del sys.modules[alias]
            else:
                foreign.append(alias)
        if foreign:
            # Retain any foreign replacement rather than deleting a module
            # the adapter does not own, but reject the altered import scope.
            raise ExtensionError("a temporary working alias was replaced during its scope")


@dataclass(frozen=True, slots=True)
class CandidateState:
    prior_state: base.CandidateState
    added_rows: tuple[TheoremSpec, ...]
    rows: tuple[TheoremSpec, ...]
    added_sources: tuple[FilePin, ...]
    specs_sha256: str


def _require_spec_pin():
    if (type(COMBINED_SPECS_SHA256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", COMBINED_SPECS_SHA256) is None):
        raise ExtensionError("the actual complete ordered113 specification is not registered")


def load_candidate_state(*, require_spec_pin=True):
    if type(require_spec_pin) is not bool:
        raise ExtensionError("require_spec_pin must be an explicit Boolean")
    require_preserved81()
    require_extension_sources()
    if require_spec_pin:
        _require_spec_pin()
    previous = base.load_candidate_state(final=True)
    added = []
    with temporary_working_aliases():
        for owner in EXTENSION_FACTORIES:
            path = ROOT / owner.source.path
            raw = _read(owner.source)
            alias = "_working_euclidean_extension_" + owner.module
            if alias in sys.modules:
                raise ExtensionError("a private extension factory alias already exists")
            module = ModuleType(alias)
            module.__file__ = str(path)
            module.__package__ = ""
            exec(compile(raw, str(path), "exec"), module.__dict__)
            factory = getattr(module, owner.factory, None)
            if not callable(factory) or getattr(factory, "__module__", None) != alias:
                raise ExtensionError("an exact added theorem factory is missing")
            rows = factory(TheoremSpec)
            if (type(rows) is not tuple or len(rows) != owner.count
                    or any(type(row) is not TheoremSpec for row in rows)
                    or closure._specs_digest(rows) != owner.specs_sha256):
                raise ExtensionError("an added factory differs from its complete frozen specification")
            if _read(owner.source) != raw:
                raise ExtensionError("an added source changed during actual syntax construction")
            added.extend(rows)
    added = tuple(added)
    rows = (*previous.rows, *added)
    closure._validate_frontier(rows)
    names, seen = {row.name for row in rows}, set()
    for row in rows:
        if not (set(row.dependencies) & names) <= seen:
            raise ExtensionError("the actual combined working dependency order is not topological")
        seen.add(row.name)
    digest = closure._specs_digest(rows)
    if (len(previous.rows) != 81 or len(added) != 32 or len(rows) != 113
            or not set(PRINCIPAL_ROOTS) <= {row.name for row in added}
            or require_spec_pin and digest != COMBINED_SPECS_SHA256):
        raise ExtensionError("the complete81+9+23 working theorem inventory changed")
    return CandidateState(previous, added, rows, tuple(owner.source for owner in EXTENSION_FACTORIES), digest)


def validate_state(state):
    _require_spec_pin()
    if (type(state) is not CandidateState or type(state.rows) is not tuple
            or type(state.added_rows) is not tuple or len(state.rows) != 113
            or any(type(row) is not TheoremSpec for row in state.rows)
            or len(state.added_rows) != 32 or type(state.prior_state) is not base.CandidateState
            or type(state.prior_state.rows) is not tuple
            or any(type(row) is not TheoremSpec for row in state.prior_state.rows)
            or state.rows != (*state.prior_state.rows, *state.added_rows)
            or len(state.prior_state.rows) != 81
            or state.prior_state.sources != base.MATH_SOURCE_PINS
            or state.prior_state.specs_sha256 != base.NEW_SPECS_SHA256
            or closure._specs_digest(state.prior_state.rows) != base.NEW_SPECS_SHA256
            or type(state.added_sources) is not tuple
            or state.added_sources != tuple(owner.source for owner in EXTENSION_FACTORIES)
            or state.specs_sha256 != COMBINED_SPECS_SHA256
            or closure._specs_digest(state.rows) != COMBINED_SPECS_SHA256):
        raise ExtensionError("a foreign or altered working113 syntax state is not authority")


def state_binding(state):
    validate_state(state)
    require_preserved81()
    require_extension_sources()
    previous = base.state_binding(state.prior_state, final=True)
    controls = []
    for name in CONTROL_FILES:
        raw = bounded_bytes(HERE / name, MAX_SOURCE_BYTES)
        controls.append((WORKING_RELATIVE + "/" + name, len(raw), sha256(raw).hexdigest()))
    return sha256(canonical({
        "base_working81_binding": previous,
        "preserved81": [asdict(pin) for pin in PRESERVED81_PINS],
        "added_factories": [asdict(owner) for owner in EXTENSION_FACTORIES],
        "temporary_working_aliases": [(alias, asdict(pin)) for alias, pin in WORKING_ALIAS_PINS],
        "controls": controls, "combined_specs_sha256": state.specs_sha256,
        "prior_working_count": 81, "added_working_count": 32, "combined_working_count": 113,
        "ordinary_principals": PRINCIPAL_ROOTS,
        "readme_plan_or_saved_observation_authority": False,
    })).hexdigest()


@dataclass(frozen=True, slots=True)
class SupportSelection:
    selected: base.SupportSelection
    previous_working_names: tuple[str, ...]
    added_working_names: tuple[str, ...]

    @property
    def owned(self):
        return self.selected.owned

    @property
    def frontier(self):
        return self.selected.frontier

    @property
    def plan(self):
        return self.selected.plan

    @property
    def complete_specs(self):
        return self.selected.complete_specs

    @property
    def inherited_alpha_names(self):
        return self.selected.parent_support

    def role(self, name):
        if name in self.previous_working_names:
            return "prior_non_admitted_working81"
        if name in self.added_working_names:
            return "added_non_admitted_working32"
        if name in self.inherited_alpha_names:
            return "inherited_alpha_v32"
        raise ExtensionError("a requested row is outside the actual combined dependency cone")


def select_support(state, owned_names=None):
    validate_state(state)
    if owned_names is None:
        owned_names = tuple(row.name for row in state.rows)
    if (type(owned_names) is not tuple or not owned_names
            or any(type(name) is not str for name in owned_names)
            or len(set(owned_names)) != len(owned_names)
            or not set(owned_names) <= {row.name for row in state.rows}):
        raise ExtensionError("only exact nonempty working theorem selections are allowed")
    chosen = base.select_support(state.rows, owned_names)
    complete = {row.name for row in chosen.complete_specs}
    return SupportSelection(chosen,
        tuple(row.name for row in state.prior_state.rows if row.name in complete),
        tuple(row.name for row in state.added_rows if row.name in complete))


def local_manifest():
    state = load_candidate_state(require_spec_pin=False)
    names = {row.name for row in state.rows}
    used = {name for row in state.rows for name in row.dependencies}
    return {
        "schema": "peano-working-polynomial-euclidean-extension-syntax-v1", "syntax_only": True,
        "prior_working_rows": 81, "added_working_rows": 32, "combined_working_rows": 113,
        "source_factory_counts": [8, 30, 25, 18, 9, 23],
        "combined_specs_sha256": state.specs_sha256,
        "ordered_names": [row.name for row in state.rows],
        "working_dependency_edges": sum(len(row.dependencies) for row in state.rows),
        "working_script_commands": sum(len(row.script) for row in state.rows),
        "direct_external_dependencies": sorted(used - names),
        "maximal_working_roots": [row.name for row in state.rows if row.name not in used],
        "ordinary_principals": list(PRINCIPAL_ROOTS),
        "global_current3971_novelty_checked": False, "original_ha_checked": False,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "prior_working_rows_reclassified_as_alpha": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }
