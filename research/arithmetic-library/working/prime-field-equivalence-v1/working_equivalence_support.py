"""Working-only coefficient-equivalence extension of the frozen113 prefix.

All old tracked files are preserved, including human notes and deferred data.
Their hashes are preservation checks, never proof authority. New rows remain
non-admitted working mathematics; current Alpha v32/3971 and Stable432 do not
change. Final registrations are literal and fail closed until actually set.
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


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING_RELATIVE = "research/arithmetic-library/working/prime-field-equivalence-v1"
PRIOR_RELATIVE = "research/arithmetic-library/working/prime-field-euclidean-v1"
PRIOR_DIRECTORY = ROOT / PRIOR_RELATIVE
if HERE != ROOT / WORKING_RELATIVE or not (ROOT / "peano-lab/py/peano_lab").is_dir():
    raise RuntimeError("the equivalence integration must remain in its new exact working directory")
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import constructive_g009_support as inherited

closure, FilePin = inherited.closure, inherited.FilePin
canonical, bounded_bytes, check_pin = inherited.canonical, inherited.bounded_bytes, inherited.check_pin
MAX_SOURCE_BYTES = inherited.MAX_SOURCE_BYTES
TheoremSpec = inherited.TheoremSpec


class EquivalenceError(ValueError):
    """An exact working source, ownership, or original proof boundary failed."""


# Complete git-tracked inventory measured before this tranche began. Nothing
# here, especially a README, deferred draft or observation, supplies a proof.
_PRESERVED_RECORDS = (
    ("DEFERRED_division_identity_converse.txt", 18608, "64d2e1197fb0a600146b07fdc3c51cf0532653dabaebb74a824a63dc166821ff"),
    ("README.md", 10758, "37a415f572e1d703ef754dc2c32e1ad8ab9ab7841e39a3c0164c3891a5903f77"),
    ("artifacts/inherited-polynomial-products-three-lemmas-seed-v1.json", 812095, "f4d2567e664ae3ad6092e6b54a6599d2858ac4fafc0b4343085a218da6735624"),
    ("artifacts/inherited-successor-injective-seed-v1.json", 256, "bcdf16c331497c3dc26bec8cdfe92b991eb83bfe353d1d9429527a32541f1edb"),
    ("artifacts/working-euclidean-extension-proof-bundle-v1.json", 2219445, "c2e097f0e04c4b4f01bb219102405d0e93bc847c19625113eb48e55c7900734d"),
    ("artifacts/working-prime-field-euclidean-proof-bundle-v1.json", 1635441, "3614e9504b84cfd24a52780d54ddc9eb16e49bf2df996c99664c9427e9a9fd83"),
    ("augment_inherited_polynomial_seed.py", 10355, "e9dce56cff718bdce62ecfb258e4f2eb640053c010a1ebd1e8fb433f1b4f3a0f"),
    ("author_inherited_successor_seed.py", 7093, "312df3229ae99a8ec39538d8fd8c2d7f19936d9c9c70062197e0eb23c40512ea"),
    ("check_working_euclidean.py", 9619, "390033da96271b2347a99d5fe5f033d1c6c60f0b82496a1707df6260de353603"),
    ("check_working_euclidean_extension.py", 10353, "be03cbdb4e19b22a2ffac2ce50625b4bd9f81dcf1b9e8b8bcac782ab05cb74e4"),
    ("current-alpha-v32-ui-observations-v1.json", 33421, "d5f78f0f96c57c562ffd464eb2ad71dae5cdd15b58b9811eb5d5de0e8a8a0a40"),
    ("export_working_euclidean.py", 7319, "5b5ff76c08c01240baa239ca189ad3a372f5d6e7777a0aa9b12eaf88a37b19de"),
    ("export_working_euclidean_extension.py", 5158, "33eb64d1e7015d596f217e5a190577bdb9f36665de5074d1922ff8af15071f56"),
    ("inspect_euclidean_extension_seeds.py", 6797, "3aa8e9f74200f960641c7e14f9971dea9d4b28c763412c8f20087ecd0ff6fff5"),
    ("inspect_working_seed_syntax.py", 11886, "f4b374f6696d8772bbd24a4dd830e9e5679ac2a58f8a81489a44dfa591858f61"),
    ("prime_field_polynomial_convolution_padding_candidate.py", 39740, "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007"),
    ("prime_field_polynomial_convolution_triangular_candidate.py", 16677, "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f"),
    ("prime_field_polynomial_distributivity_candidate.py", 26118, "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86"),
    ("prime_field_polynomial_division_candidate.py", 47986, "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2"),
    ("prime_field_polynomial_division_uniqueness_candidate.py", 23258, "6a9d9ebe1f72202743e5df2c069b9aa367fdb3d61108f1d9354cdc9276ab2d15"),
    ("prime_field_polynomial_representation_candidate.py", 42623, "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a"),
    ("test_prime_field_polynomial_convolution_padding_candidate.py", 27054, "7632654e36e18cf7c872bd29dd783a55cf597e33e7b5369be178a2d2f42b87f9"),
    ("test_prime_field_polynomial_convolution_triangular_candidate.py", 9162, "e6bf4d2a0b2b00336b8d83b4ffe5d068e34e3d5bd44e8af4b995ca2723289822"),
    ("test_prime_field_polynomial_distributivity_candidate.py", 21925, "d6200ef1e0447f3efb98461ce343a1a3ae5530f74490bd4b7782cbc13ed2e9a6"),
    ("test_prime_field_polynomial_division_candidate.py", 23978, "c4f7555b19e88789c4a561ec5b66d1f9487f44a32b388f2beea90f9ec42eed3b"),
    ("test_prime_field_polynomial_division_uniqueness_candidate.py", 15599, "b74083e6707eb83e7fab3efa3f610d562edf2168511b07c5995f9ef9f7f588e2"),
    ("test_prime_field_polynomial_representation_candidate.py", 25517, "75a2cee90850ff07468b1d568ce4d3665f8006fdbb892c5838186abbc8fd57b7"),
    ("test_working_euclidean_definitions.py", 16004, "c30ef4a5aec9065ed745b512fef3e464e53e32a0be2d642d5f3a4f96d62cd3af"),
    ("test_working_euclidean_extension.py", 30204, "f92f8784ad84247328b8ebd0f27bfe1595d9989caf37c22b2e9439bcc8ef9c4b"),
    ("test_working_euclidean_integration.py", 18658, "04f66780d6b0d7408b72b8e9a8cdc54772d1593e03dfb2e61579a44410ba1038"),
    ("working-113-global-syntax-v1.json", 9835, "e138bc133d3ff566f98381fb18e5e74faf91fa42b0122e0f2978a1a99139e49a"),
    ("working-113-verification-observations-v1.json", 18976, "8b070373ea08119fc350d54286382c732d456d8bc62f995a6c1338c99f0f87f5"),
    ("working-81-global-syntax-v1.json", 10290, "38e99d5574810ff9820b94952d11fa7b4f17a09a030c36fd42e4df94f2bf23b7"),
    ("working-81-verification-observations-v1.json", 14806, "28fba8440872bcc852f43ce0511d3a7659edc6da9a773bf373f037c7495be5ac"),
    ("working-9-execution-uniqueness-observations-v1.json", 11217, "5c2f3ef1fd0891f86655da3028f015e9f2dbc487faede851e2918615cf0ef9f4"),
    ("working-definition-validation-observations-v1.json", 2962, "441d03b867ead6948610c3fc0cb63f4ec75954896f978d99fbaf9e2fc2eb9eec"),
    ("working-euclidean-extension-rfc-v1.md", 6400, "60227449868efa500ba8dde65d3a80697ea6c2f102d7323586de7c9aba31a280"),
    ("working-euclidean-integration-rfc-v1.md", 9958, "f39c915949e5ca9312553836e7672c4c1b07bffb8b6d8a4efe3d3a0c02d560d9"),
    ("working-padding23-focused-observations-v1.json", 9315, "08fd13f02df30c48c54da13961e44de8039c56e86ac34e3fda6131b28c9f2ea8"),
    ("working_euclidean_definition_graph.py", 1226, "4489cec7dff3a1ea48d12725f2d28b9c9c648543d94f8ee6a7233b3350e7ba15"),
    ("working_euclidean_definitions.py", 7278, "aec02f0130c3bcaa0b09395874530e2d844eb583411e1a5b7f8033c3fba9c49d"),
    ("working_euclidean_extension_support.py", 19237, "df377f2ada5015601945caedc93b442a83cb3142ea5d4a652bab78f705ef460e"),
    ("working_euclidean_support.py", 18552, "80e73f977f2464e2f62939610667def8bbf96f19e4d95bf734c52969c39cec4a"),
)
PRESERVED_TREE_PINS = tuple(FilePin(PRIOR_RELATIVE + "/" + name, size, digest)
                            for name, size, digest in _PRESERVED_RECORDS)
_EXPECTED_PRESERVED_PATHS = tuple(pin.path for pin in PRESERVED_TREE_PINS)
PRIOR113_ARTIFACT = next(pin for pin in PRESERVED_TREE_PINS
                        if pin.path.endswith("/artifacts/working-euclidean-extension-proof-bundle-v1.json"))
PRIOR113_SPECS_SHA256 = "aac561ef7706c53af00464feba7d0f4a51a3e3960404dba4a53d80405913b8a9"
PRIOR_WORKING_COUNT = 113
PRINCIPAL_ROOTS = (
    "prime_field_polynomial_equivalent_implies_left_pad",
    "prime_field_polynomial_add_equivalent_congruent",
    "prime_field_polynomial_subtract_equivalent_congruent",
    "prime_field_polynomial_convolution_equivalent_congruent",
)
EXPECTED_MODULES = (
    "prime_field_polynomial_equivalence_candidate",
    "prime_field_polynomial_convolution_congruence_candidate",
)
CONTROL_FILES = (
    "working_equivalence_support.py", "export_working_equivalence.py",
    "check_working_equivalence.py", "test_working_equivalence_integration.py",
    "working-polynomial-equivalence-rfc-v1.md",
)
REPRESENTATION_ALIAS = "peano_lab.library.prime_field_polynomial_representation_candidate"
REPRESENTATION_PIN = next(pin for pin in PRESERVED_TREE_PINS
                          if pin.path.endswith("/prime_field_polynomial_representation_candidate.py"))


def _digest(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def require_preserved_tree():
    if (type(PRESERVED_TREE_PINS) is not tuple or len(PRESERVED_TREE_PINS) != 43
            or any(type(pin) is not FilePin or type(pin.bytes) is not int or pin.bytes <= 0
                   or not _digest(pin.sha256) for pin in PRESERVED_TREE_PINS)
            or tuple(pin.path for pin in PRESERVED_TREE_PINS) != _EXPECTED_PRESERVED_PATHS
            or len(set(_EXPECTED_PRESERVED_PATHS)) != 43
            or type(PRIOR113_ARTIFACT) is not FilePin
            or (PRIOR113_ARTIFACT.path, PRIOR113_ARTIFACT.bytes, PRIOR113_ARTIFACT.sha256) != (
                PRIOR_RELATIVE + "/artifacts/working-euclidean-extension-proof-bundle-v1.json",
                2219445, "c2e097f0e04c4b4f01bb219102405d0e93bc847c19625113eb48e55c7900734d")):
        raise EquivalenceError("the complete43-file frozen prior working inventory changed")
    for pin in PRESERVED_TREE_PINS:
        check_pin(pin, ROOT, closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)


def _read(pin):
    maximum = closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes
    check_pin(pin, ROOT, maximum)
    raw = bounded_bytes(ROOT / pin.path, maximum)
    if (len(raw), sha256(raw).hexdigest()) != (pin.bytes, pin.sha256):
        raise EquivalenceError("an exact pinned working source changed during reading")
    return raw


def _preserved_helper(name):
    """Use exact old source without writing bytecode in the old directory."""
    if name not in ("working_euclidean_support", "working_euclidean_extension_support"):
        raise EquivalenceError("only the two exact preserved integration helpers may be loaded")
    pin = next(pin for pin in PRESERVED_TREE_PINS if pin.path == PRIOR_RELATIVE + "/" + name + ".py")
    path, raw = ROOT / pin.path, _read(pin)
    previous = sys.modules.get(name)
    if previous is not None:
        specification = getattr(previous, "__spec__", None)
        if (type(previous) is not ModuleType
                or Path(getattr(previous, "__file__", "")).resolve() != path
                or getattr(specification, "origin", None) != str(path)
                or getattr(specification, "name", None) != name):
            raise EquivalenceError("a foreign module owns the preserved helper name: " + name)
        return previous
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise EquivalenceError("an exact preserved helper has no loader")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        exec(compile(raw, str(path), "exec"), module.__dict__)
        if _read(pin) != raw or sys.modules.get(name) is not module:
            raise EquivalenceError("the preserved helper changed while loading exact source")
    except BaseException:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        raise
    return module


require_preserved_tree()
prior_base = _preserved_helper("working_euclidean_support")
prior = _preserved_helper("working_euclidean_extension_support")
if prior.base is not prior_base or prior.closure is not closure:
    raise EquivalenceError("the exact unchanged prior113 assembler chain is required")


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
        return FilePin(WORKING_RELATIVE + "/" + self.module + ".py",
                       self.source_bytes, self.source_sha256)

    @property
    def test(self):
        return FilePin(WORKING_RELATIVE + "/test_" + self.module + ".py",
                       self.test_bytes, self.test_sha256)


# Both authors' actual final mathematical source/test/specification freezes.
# These authenticate syntax; no source pin substitutes for actual proof jobs.
REGISTERED_COUNTS: tuple[int, int] | None = (5, 3)
FACTORIES: tuple[Factory, ...] = (
    Factory("prime_field_polynomial_equivalence_candidate", 5, 10469,
            "929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373",
            19312, "778a8c9dcd43d5bed00125f176ac013a6aabfa4ae132a3ca16ba2bae2875b0dc",
            "2fe70cc2ff26a6938768fcbdb661c84b2ad17e19dd7d9551689f3f4ea39da273"),
    Factory("prime_field_polynomial_convolution_congruence_candidate", 3, 8183,
            "effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70",
            19162, "224e7d441f17217616a34e9e6fe85d321ba8c1ba410675cbacf56c34b6f7c4b8",
            "b0da9dd22a52c42045fd22ac189fb9d7fc92365527818f5a61e0f4a71d1be7e6"),
)
COMBINED_SPECS_SHA256: str | None = "b1e2106738d15dc3714dd1a57f88fedec492692259b6009e4edccc49de439769"


def require_source_registration():
    if (type(REGISTERED_COUNTS) is not tuple or len(REGISTERED_COUNTS) != 2
            or any(type(count) is not int or count <= 0 for count in REGISTERED_COUNTS)
            or type(FACTORIES) is not tuple or len(FACTORIES) != 2
            or any(type(owner) is not Factory for owner in FACTORIES)
            or tuple(owner.module for owner in FACTORIES) != EXPECTED_MODULES
            or tuple(owner.count for owner in FACTORIES) != REGISTERED_COUNTS):
        raise EquivalenceError("both actual final equivalence factories must be registered")
    for owner in FACTORIES:
        if (type(owner.count) is not int or type(owner.source_bytes) is not int or owner.source_bytes <= 0
                or type(owner.test_bytes) is not int or owner.test_bytes <= 0
                or not all(_digest(value) for value in (
                    owner.source_sha256, owner.test_sha256, owner.specs_sha256))):
            raise EquivalenceError("an exact equivalence source/test/specification pin is invalid")
        check_pin(owner.source, ROOT, MAX_SOURCE_BYTES)
        check_pin(owner.test, ROOT, MAX_SOURCE_BYTES)
    return sum(REGISTERED_COUNTS)


def _require_spec_pin():
    if not _digest(COMBINED_SPECS_SHA256):
        raise EquivalenceError("the actual complete ordered equivalence specification is not registered")


@contextmanager
def temporary_representation_alias():
    """Only an absent mathematical alias may refer to the pinned old source."""
    import peano_lab.library as package
    name = REPRESENTATION_ALIAS
    if (name != "peano_lab.library.prime_field_polynomial_representation_candidate"
            or REPRESENTATION_PIN != next(pin for pin in PRESERVED_TREE_PINS
                if pin.path == PRIOR_RELATIVE + "/prime_field_polynomial_representation_candidate.py")):
        raise EquivalenceError("only the exact frozen representation alias is permitted")
    short = name.rsplit(".", 1)[1]
    if name in sys.modules or short in vars(package) or importlib.util.find_spec(name) is not None:
        raise EquivalenceError("an existing production or working representation alias cannot be replaced")
    path, raw = ROOT / REPRESENTATION_PIN.path, _read(REPRESENTATION_PIN)
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise EquivalenceError("the exact working representation source has no loader")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        exec(compile(raw, str(path), "exec"), module.__dict__)
        if _read(REPRESENTATION_PIN) != raw or sys.modules.get(name) is not module:
            raise EquivalenceError("the exact representation changed while loading")
        yield module
    finally:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        else:
            raise EquivalenceError("the owned temporary representation alias was replaced")


def load_prior_state():
    require_preserved_tree()
    state = prior.load_candidate_state()
    prior.validate_state(state)
    if len(state.rows) != PRIOR_WORKING_COUNT or state.specs_sha256 != PRIOR113_SPECS_SHA256:
        raise EquivalenceError("the exact non-admitted113 prefix changed")
    return state


@dataclass(frozen=True, slots=True)
class CandidateState:
    prior_state: prior.CandidateState
    added_rows: tuple[TheoremSpec, ...]
    rows: tuple[TheoremSpec, ...]
    added_sources: tuple[FilePin, ...]
    specs_sha256: str


def load_candidate_state(*, require_spec_pin=True):
    if type(require_spec_pin) is not bool:
        raise EquivalenceError("require_spec_pin must be an explicit Boolean")
    require_preserved_tree()
    added_count = require_source_registration()
    if require_spec_pin:
        _require_spec_pin()
    previous = load_prior_state()
    added = []
    with temporary_representation_alias():
        for owner in FACTORIES:
            path, raw = ROOT / owner.source.path, _read(owner.source)
            alias = "_working_equivalence_v1_" + owner.module
            if alias in sys.modules:
                raise EquivalenceError("a private equivalence factory alias already exists")
            module = ModuleType(alias)
            module.__file__, module.__package__ = str(path), ""
            exec(compile(raw, str(path), "exec"), module.__dict__)
            factory = getattr(module, owner.factory, None)
            if not callable(factory) or getattr(factory, "__module__", None) != alias:
                raise EquivalenceError("an exact added equivalence factory is missing")
            values = factory(TheoremSpec)
            if (type(values) is not tuple or len(values) != owner.count
                    or any(type(row) is not TheoremSpec for row in values)
                    or closure._specs_digest(values) != owner.specs_sha256):
                raise EquivalenceError("an added factory differs from its actual frozen specifications")
            if _read(owner.source) != raw:
                raise EquivalenceError("an added source changed during syntax construction")
            added.extend(values)
    added = tuple(added)
    rows = (*previous.rows, *added)
    closure._validate_frontier(rows)
    names, seen = {row.name for row in rows}, set()
    for row in rows:
        if not (set(row.dependencies) & names) <= seen:
            raise EquivalenceError("the complete working source order is not topological")
        seen.add(row.name)
    digest = closure._specs_digest(rows)
    if (len(added) != added_count or len(rows) != PRIOR_WORKING_COUNT + added_count
            or not set(PRINCIPAL_ROOTS) <= {row.name for row in added}
            or require_spec_pin and digest != COMBINED_SPECS_SHA256):
        raise EquivalenceError("the actual complete prior113 plus equivalence inventory changed")
    return CandidateState(previous, added, rows, tuple(owner.source for owner in FACTORIES), digest)


def validate_state(state):
    _require_spec_pin()
    count = require_source_registration()
    if type(state) is not CandidateState or type(state.prior_state) is not prior.CandidateState:
        raise EquivalenceError("an actual combined equivalence syntax state is required")
    prior.validate_state(state.prior_state)
    if (type(state.rows) is not tuple or type(state.added_rows) is not tuple
            or len(state.rows) != PRIOR_WORKING_COUNT + count or len(state.added_rows) != count
            or any(type(row) is not TheoremSpec for row in state.rows)
            or len(state.prior_state.rows) != PRIOR_WORKING_COUNT
            or state.prior_state.specs_sha256 != PRIOR113_SPECS_SHA256
            or state.rows != (*state.prior_state.rows, *state.added_rows)
            or type(state.added_sources) is not tuple
            or state.added_sources != tuple(owner.source for owner in FACTORIES)
            or state.specs_sha256 != COMBINED_SPECS_SHA256
            or closure._specs_digest(state.rows) != COMBINED_SPECS_SHA256):
        raise EquivalenceError("a foreign or altered combined syntax state is not authority")


def state_binding(state):
    validate_state(state)
    require_preserved_tree()
    previous = prior.state_binding(state.prior_state)
    controls = []
    for name in CONTROL_FILES:
        raw = bounded_bytes(HERE / name, MAX_SOURCE_BYTES)
        controls.append((WORKING_RELATIVE + "/" + name, len(raw), sha256(raw).hexdigest()))
    return sha256(canonical({
        "preserved113_binding": previous,
        "complete_preserved_tracked_tree": [asdict(pin) for pin in PRESERVED_TREE_PINS],
        "new_factories": [asdict(owner) for owner in FACTORIES],
        "representation_alias": [REPRESENTATION_ALIAS, asdict(REPRESENTATION_PIN)],
        "controls": controls, "combined_specs_sha256": state.specs_sha256,
        "prior_non_admitted_working_count": PRIOR_WORKING_COUNT,
        "added_non_admitted_working_count": len(state.added_rows),
        "ordinary_principals": PRINCIPAL_ROOTS,
        "notes_or_saved_observations_supply_proof_authority": False,
    })).hexdigest()


@dataclass(frozen=True, slots=True)
class SupportSelection:
    selected: prior_base.SupportSelection
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
            return "prior_non_admitted_working113"
        if name in self.added_working_names:
            return "new_non_admitted_equivalence"
        if name in self.inherited_alpha_names:
            return "inherited_alpha_v32"
        raise EquivalenceError("the requested theorem is outside the exact dependency cone")


def select_support(state, owned_names=None):
    validate_state(state)
    if owned_names is None:
        owned_names = tuple(row.name for row in state.rows)
    if (type(owned_names) is not tuple or not owned_names
            or any(type(name) is not str for name in owned_names)
            or len(set(owned_names)) != len(owned_names)
            or not set(owned_names) <= {row.name for row in state.rows}):
        raise EquivalenceError("only exact nonempty ordered working selections are permitted")
    chosen = prior_base.select_support(state.rows, owned_names)
    complete = {row.name for row in chosen.complete_specs}
    return SupportSelection(chosen,
        tuple(row.name for row in state.prior_state.rows if row.name in complete),
        tuple(row.name for row in state.added_rows if row.name in complete))


def local_manifest():
    state = load_candidate_state(require_spec_pin=False)
    names = {row.name for row in state.rows}
    used = {name for row in state.rows for name in row.dependencies}
    return {
        "schema": "peano-working-polynomial-equivalence-syntax-v1", "syntax_only": True,
        "prior_non_admitted_working_rows": PRIOR_WORKING_COUNT,
        "added_non_admitted_working_rows": len(state.added_rows),
        "combined_working_rows": len(state.rows),
        "new_factory_counts": [owner.count for owner in FACTORIES],
        "combined_specs_sha256": state.specs_sha256,
        "ordered_names": [row.name for row in state.rows],
        "working_dependency_edges": sum(len(row.dependencies) for row in state.rows),
        "working_script_commands": sum(len(row.script) for row in state.rows),
        "direct_external_dependencies": sorted(used - names),
        "maximal_working_roots": [row.name for row in state.rows if row.name not in used],
        "ordinary_principals": list(PRINCIPAL_ROOTS),
        "global_current3971_novelty_checked": False, "original_ha_checked": False,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "prior113_reclassified_as_alpha": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }
