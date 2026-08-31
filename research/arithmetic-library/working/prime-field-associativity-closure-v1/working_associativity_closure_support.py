"""Exact source-only planning for the non-admitted shift/scalar/append37 cone.

The accepted25 archive is immutable input, not proof authority. Each authoring
stage checks its real seeds anew through the unchanged original assembler.
Only the separate novelty task parses the full current4092 catalogue.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib import import_module, util
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING_RELATIVE = "research/arithmetic-library/working/prime-field-associativity-closure-v1"
if HERE != ROOT / WORKING_RELATIVE or not (ROOT / "peano-lab/py/peano_lab").is_dir():
    raise RuntimeError("the associativity closure belongs only in its new working directory")
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import constructive_g009_support as inherited

FilePin = inherited.FilePin
PRIOR25_RELATIVE = "research/arithmetic-library/working/prime-field-associativity-v1"
PRIOR25_SUPPORT_PIN = FilePin(
    PRIOR25_RELATIVE + "/working_shift_scalar_support.py", 44398,
    "63935e29c539bb1a7577235c2254b867b49723c505ba3e47a6d079b3682c204f")
_PRIVATE_PRIOR_NAME = "_working_associativity_closure_v1_prior25"


def _load_prior_support():
    """Dataclasses need a temporary private controller name, never a peano alias."""
    if _PRIVATE_PRIOR_NAME in sys.modules:
        raise ValueError("the private prior-controller name is already owned")
    pin = PRIOR25_SUPPORT_PIN
    inherited.check_pin(pin, ROOT, inherited.MAX_SOURCE_BYTES)
    path = ROOT / pin.path
    raw = inherited.bounded_bytes(path, inherited.MAX_SOURCE_BYTES)
    if (len(raw), sha256(raw).hexdigest()) != (pin.bytes, pin.sha256):
        raise ValueError("the pinned accepted25 controller changed before loading")
    module = ModuleType(_PRIVATE_PRIOR_NAME)
    module.__file__, module.__package__ = str(path), ""
    module.__spec__ = util.spec_from_file_location(_PRIVATE_PRIOR_NAME, path)
    sys.modules[_PRIVATE_PRIOR_NAME] = module
    try:
        exec(compile(raw, str(path), "exec"), module.__dict__)
        inherited.check_pin(pin, ROOT, inherited.MAX_SOURCE_BYTES)
        return module
    finally:
        if sys.modules.get(_PRIVATE_PRIOR_NAME) is not module:
            raise ValueError("a foreign private controller is preserved, not deleted")
        del sys.modules[_PRIVATE_PRIOR_NAME]


prior = _load_prior_support()
closure, TheoremSpec, THEOREMS = prior.closure, prior.TheoremSpec, prior.THEOREMS
WorkingError, Factory = prior.WorkingError, prior.Factory
_require, _digest, _safe_relative = prior._require, prior._digest, prior._safe_relative
canonical, bounded_bytes, check_pin, read_pin = prior.canonical, prior.bounded_bytes, prior.check_pin, prior.read_pin
MAX_SOURCE_BYTES, MAX_BYTES, MAX_CATALOG_BYTES = prior.MAX_SOURCE_BYTES, prior.MAX_BYTES, prior.MAX_CATALOG_BYTES
CPU_LIMITS, WALL_SECONDS, MAX_RSS_BYTES = (170, 175), 180, 1536 * 1024 * 1024
EXPECTED_COUNT, EXPECTED_INHERITED_COUNT = 37, 246
SPECS_SHA256 = "de95fea3806bc6c227c032bf2c29095ce191e27624c2196bd417df6c77c31491"
NAMES_SHA256 = "872162ac6020bfeb9985d9ae9534c26eb0273976ff381f28df53ad9cd0b50d4d"
ARTIFACT_DIRECTORY = HERE / "artifacts"
OUTPUT_PREFIX = "working-associativity-closure-prefix-"
PHASES = (32, 34, 35, 37)
# through, theorem nodes, theorem edges, maximal roots (packager is additional).
STAGE_RECORDS = ((32, 276, 756, 6), (34, 278, 780, 7),
                 (35, 280, 798, 6), (37, 283, 812, 6))
PREVIOUS_THROUGH = {32: 25, 34: 32, 35: 34, 37: 35}
CONTROL_FILES = (
    "working_associativity_closure_support.py", "export_working_associativity_closure.py",
    "check_working_associativity_closure.py", "test_working_associativity_closure.py",
    "working-associativity-closure-rfc-v1.md",
)
PRINCIPAL_ROOTS = (
    "prime_field_polynomial_convolution_shift_right_exists",
    "prime_field_polynomial_convolution_right_scale_exists",
    "prime_field_polynomial_convolution_right_scale_zero",
    "prime_field_convolution_coefficient_right_append_add",
    "prime_field_polynomial_convolution_right_append_exists",
    "prime_field_polynomial_convolution_associative_equivalent",
)
PRINCIPAL_STATEMENT_SHA256 = (
    "0fc173b813282a7111d604245b1706a4c01c5bcf566812151810e9afe38f065d",
    "5d0349367decc3084471726b73a77617d49f484cf31191bb78effbc434167156",
    "fd6d04fd88ff9f594f7ee27de04486c1932ce5de30b6030b6b9b18cb547511ef",
    "a11e1f29b31ae9076959706b6b5d0813689194a2ab57a1a4e879e6a6c3ad69bd",
    "0ef69b8524dd48c1a9805f158e9eff25c41e421b85378b96b51b7c63bd89f087",
    "7b693d78212d80c6406b09f6ca5151ac88862da29d824494ed6338f601fb6912",
)

# These bytes are preservation inputs only; saved observations are never parsed.
PRIOR25_PINS = (
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/README.md", 3846, "e8540c5328d1873f892007e93f89710048dba9d28cc5081f69aa92e912d29cba"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/artifacts/working-shift-scalar-proof-bundle-v1.json", 707587, "e8ed419608273f0230348ae498e57a23f0b59ade805964d30e0e8a3f10083cd0"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/candidate-authoring-observations-v1.json", 12674, "6bd47f563a67b3d1d562fe4fc1a1f39f816bf8dcf039cab8c0c1150c889b19c1"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/check_working_shift_scalar.py", 12209, "97a0163bb9b7129c4c73b5f28114247a9d6b25e3669884e179201718259ede55"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/export_working_shift_scalar.py", 8746, "ddaa096159509804fcd2d8819e120f9cb4749006efadc27b6d24455e0832f81f"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/final-verification-observations-v1.json", 27006, "dd5459a90ca66e47ee555e6ee114395edabb13b35861d9a39486d8c99cd86932"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/parent-registration-observations-v1.json", 7165, "cf577e082340a8f41ddc5efc1625d7f14fa3adba027bed69deec6985679d9761"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/source-integration-observations-v1.json", 6272, "0696c02488259f8056894125dfbbc0e90c8e56f2e5ec077265a4da01250886b8"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/test_working_shift_scalar_integration.py", 34786, "078e91864a0331fe56da060e46b23a7664b1589ab49f9143632142d938d48cc4"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/working-shift-scalar-integration-rfc-v1.md", 7121, "bf9886bdf21ad977808fda1d780d6f7cd0dd1801a0a4f8d5b5d3e40487a660a6"),
    FilePin("research/arithmetic-library/working/prime-field-associativity-v1/working_shift_scalar_support.py", 44398, "63935e29c539bb1a7577235c2254b867b49723c505ba3e47a6d079b3682c204f"),
)
_PRIOR25_RECORDS = tuple((pin.path, pin.bytes, pin.sha256) for pin in PRIOR25_PINS)

FACTORIES = (*prior.FACTORIES,
    Factory("research/arithmetic-library/working/prime-field-append-v1",
            "prime_field_polynomial_append_candidate", 6, 28396,
            "271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042",
            36494, "0c554b05b2c7e2c40e3b0e8044160379a3284bb173e48d59d77def0cad4272aa",
            "6035968b0f11aec5e4bd6cb43b4d4958318b55f600fab914025479f571b75c2a"),
    Factory("research/arithmetic-library/working/prime-field-shift-equivalence-v1",
            "prime_field_polynomial_shift_equivalence_candidate", 1, 6021,
            "8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068",
            20376, "9ed90ddc4680f8c2c3d04e2e3a76f8cffda4bfb95b1b83ab391d134c7fe5ab18",
            "d68b99a4ed9f996bd7e8b23fd0f17e165176b949f07a806a4d2c935d4372529e"),
    Factory("research/arithmetic-library/working/prime-field-associativity-step-v1",
            "prime_field_polynomial_associativity_step_candidate", 3, 26607,
            "dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1",
            29135, "4cbd15750521b2ad1a3ecd8288bfdf631bd5ad90dc7e623d4e593dc79f615262",
            "87017c7298a0247444be68f9be34e6b354b89d491ca7ee49ea4bd06effd6b2cd"),
    Factory("research/arithmetic-library/working/prime-field-associativity-induction-v1",
            "prime_field_polynomial_associativity_induction_candidate", 2, 9924,
            "8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c",
            19628, "d3725cbdd86f8d72446baf5417d25a4ddf31f61b0b6f1d076cb065b8131f2003",
            "b6ad06b7925dbb35202bb263ef14c7dc69d18c80771e075497d0a17d42294dc8"),
)
_FACTORY_RECORDS = tuple(asdict(owner) for owner in FACTORIES)
ADDITIONAL_RUNTIME_PINS = (
    FilePin("peano-lab/py/peano_lab/library/matrix_rank_finite_coding_candidate.py", 22758, "9a72aed5aa215816b5e26868c04453e0a3042486580e79a13234431b5f45952d"),
    FilePin("peano-lab/py/peano_lab/library/matrix_recursive_determinant_extensional_candidate.py", 32183, "bb2872950c416964ce6fde1012359526e748f856bc6263e080b8e2da852ca59a"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_convolution_congruence_candidate.py", 8183, "effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_convolution_padding_candidate.py", 39740, "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_distributivity_candidate.py", 26118, "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_equivalence_candidate.py", 10469, "929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373"),
)
RUNTIME_PINS = (*prior.RUNTIME_PINS, *ADDITIONAL_RUNTIME_PINS)
_RUNTIME_RECORDS = tuple((pin.path, pin.bytes, pin.sha256) for pin in RUNTIME_PINS)
_RUNTIME_BY_PATH = {pin.path: pin for pin in RUNTIME_PINS}
PROVIDER_MODULES = (*prior.PROVIDER_MODULES,
    "prime_field_polynomial_convolution_triangular_candidate",
    "prime_field_polynomial_distributivity_candidate",
    "prime_field_polynomial_convolution_padding_candidate",
    "prime_field_polynomial_equivalence_candidate",
    "prime_field_polynomial_convolution_congruence_candidate",
    "matrix_coded_product_candidate", "matrix_rank_finite_coding_candidate",
    "matrix_recursive_determinant_extensional_candidate",
)
_PROVIDER_IDENTITIES = PROVIDER_MODULES

PRIOR25_SEED = FilePin(
    PRIOR25_RELATIVE + "/artifacts/working-shift-scalar-proof-bundle-v1.json",
    707587, "e8ed419608273f0230348ae498e57a23f0b59ade805964d30e0e8a3f10083cd0")
CANONICAL121_SEED = prior.INITIAL_SEED
POLYNOMIAL_SEED = FilePin(
    "research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json",
    688987, "6e3a08c73b8a45de127e6d50a771f95b52fd54894b1c2e43468751421488a01a")
V27_SEED = FilePin(
    "research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json",
    14648599, "c4711433c92b67d2ebeb30131669c60563c70e0464dafa851d417fb88fb21a6d")
SEED_PINS = (PRIOR25_SEED, CANONICAL121_SEED, POLYNOMIAL_SEED, V27_SEED)
_SEED_IDENTITIES = tuple((pin.path, pin.bytes, pin.sha256) for pin in SEED_PINS)
PARENT_CATALOG_PINS = prior.PARENT_CATALOG_PINS
PARENT_CHANNEL_PIN = prior.PARENT_CHANNEL_PIN
PARENT_IDENTITY_SHA256 = prior.PARENT_IDENTITY_SHA256
PARENT_ENROLLMENT_SHA256 = prior.PARENT_ENROLLMENT_SHA256
_PARENT_RECORDS = (PARENT_CATALOG_PINS, PARENT_CHANNEL_PIN,
                   PARENT_IDENTITY_SHA256, PARENT_ENROLLMENT_SHA256)


def require_preserved_archives():
    prior.require_preserved_archives()
    _require(type(PRIOR25_PINS) is tuple and len(PRIOR25_PINS) == 11
             and all(type(pin) is FilePin for pin in PRIOR25_PINS)
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in PRIOR25_PINS) == _PRIOR25_RECORDS,
             "the accepted25 complete archive inventory changed")
    directory = ROOT / PRIOR25_RELATIVE
    _require(stat.S_ISDIR(directory.lstat().st_mode), "the accepted25 archive is not a real directory")
    actual, directories = set(), set()
    for path in directory.rglob("*"):
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            directories.add(path.relative_to(directory).as_posix())
        else:
            _require(stat.S_ISREG(mode), "the accepted25 archive gained a link or special path")
            actual.add(path.relative_to(ROOT).as_posix())
    _require(actual == {pin.path for pin in PRIOR25_PINS} and directories == {"artifacts"},
             "a file was added to or removed from the immutable accepted25 archive")
    for pin in PRIOR25_PINS:
        check_pin(pin, ROOT, MAX_BYTES)


def require_runtime_sources():
    prior.require_runtime_sources()
    _require(type(RUNTIME_PINS) is tuple and len(RUNTIME_PINS) == len(_RUNTIME_RECORDS)
             and all(type(pin) is FilePin for pin in RUNTIME_PINS)
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in RUNTIME_PINS) == _RUNTIME_RECORDS
             and len(_RUNTIME_BY_PATH) == len(RUNTIME_PINS)
             and PROVIDER_MODULES == _PROVIDER_IDENTITIES,
             "the original runtime or minimal canonical-provider inventory changed")
    for pin in RUNTIME_PINS:
        check_pin(pin, ROOT, MAX_SOURCE_BYTES)


def require_working_sources():
    _require(type(FACTORIES) is tuple and len(FACTORIES) == 6
             and all(type(owner) is Factory for owner in FACTORIES)
             and tuple(asdict(owner) for owner in FACTORIES) == _FACTORY_RECORDS
             and tuple(owner.count for owner in FACTORIES) == (15, 10, 6, 1, 3, 2),
             "the frozen25+6+1+3+2 source ownership changed")
    for owner in FACTORIES:
        read_pin(owner.source, MAX_SOURCE_BYTES)
        read_pin(owner.test, MAX_SOURCE_BYTES)


def require_parent_registration():
    _require((PARENT_CATALOG_PINS, PARENT_CHANNEL_PIN, PARENT_IDENTITY_SHA256,
              PARENT_ENROLLMENT_SHA256) == _PARENT_RECORDS,
             "the exact installed current-v33 parent registration changed")
    return prior.require_parent_registration()


@dataclass(frozen=True, slots=True)
class CandidateState:
    rows: tuple[TheoremSpec, ...]
    specs_sha256: str


def load_candidate_state():
    require_working_sources()
    require_runtime_sources()
    before = prior._edition_bindings()
    rows = []
    for owner in FACTORIES:
        raw, path = read_pin(owner.source, MAX_SOURCE_BYTES), ROOT / owner.source.path
        alias = "_working_associativity_closure_v1_" + owner.module
        _require(alias not in sys.modules, "a private mathematical source name is already owned")
        module = ModuleType(alias)
        module.__file__, module.__package__ = str(path), ""
        # No sys.modules insertion or future canonical mathematical alias.
        exec(compile(raw, str(path), "exec"), module.__dict__)
        factory = getattr(module, owner.factory, None)
        _require(callable(factory) and getattr(factory, "__module__", None) == alias,
                 "a frozen private factory is missing or foreign")
        values = factory(TheoremSpec)
        _require(type(values) is tuple and len(values) == owner.count
                 and all(type(row) is TheoremSpec for row in values)
                 and closure._specs_digest(values) == owner.specs_sha256,
                 "a frozen factory changed its exact ordered specifications")
        _require(read_pin(owner.source, MAX_SOURCE_BYTES) == raw,
                 "a mathematical source changed during actual construction")
        rows.extend(values)
    after = prior._edition_bindings()
    _require(before.keys() == after.keys()
             and all(after[name] is value for name, value in before.items()),
             "source construction imported or replaced an Alpha edition")
    state = CandidateState(tuple(rows), closure._specs_digest(tuple(rows)))
    validate_state(state)
    return state


def validate_state(state):
    _require(type(state) is CandidateState and type(state.rows) is tuple
             and len(state.rows) == EXPECTED_COUNT == 37
             and all(type(row) is TheoremSpec for row in state.rows)
             and state.specs_sha256 == SPECS_SHA256
             and closure._specs_digest(state.rows) == SPECS_SHA256,
             "an altered or incomplete frozen37 syntax state is not accepted")
    closure._validate_frontier(state.rows)
    _require(sha256("\n".join(row.name for row in state.rows).encode()).hexdigest() == NAMES_SHA256
             and sum(len(row.dependencies) for row in state.rows) == 179
             and sum(len(row.script) for row in state.rows) == 4303,
             "the exact37 names, ordered premises or native command inventory changed")
    table, seen = {row.name: row for row in state.rows}, set()
    for row in state.rows:
        _require((set(row.dependencies) & table.keys()) <= seen,
                 "a new source has a forward or cyclic prerequisite")
        seen.add(row.name)
    _require(len(PRINCIPAL_ROOTS) == 6 and len(set(PRINCIPAL_ROOTS)) == 6
             and tuple(sha256(table[name].statement.encode()).hexdigest()
                       for name in PRINCIPAL_ROOTS if name in table) == PRINCIPAL_STATEMENT_SHA256,
             "one of the six exact ordinary principal statements changed")


def canonical_provider_table():
    require_runtime_sources()
    before = prior._edition_bindings()
    table = {row.name: row for row in THEOREMS}
    _require(len(table) == len(THEOREMS), "the primitive theorem ladder repeats a name")
    for short in PROVIDER_MODULES:
        relative = "peano-lab/py/peano_lab/library/" + short + ".py"
        _require(relative in _RUNTIME_BY_PATH, "an inherited source is not registered")
        module = import_module("peano_lab.library." + short)
        _require(type(module) is ModuleType and getattr(module, "__file__", None) == str(ROOT / relative)
                 and getattr(getattr(module, "__spec__", None), "origin", None) == str(ROOT / relative),
                 "an inherited canonical module resolved to foreign bytes")
        factory = getattr(module, "make_" + short + "_theorems", None)
        _require(callable(factory) and factory.__module__ == "peano_lab.library." + short,
                 "an inherited canonical factory was replaced")
        rows = factory(TheoremSpec)
        _require(type(rows) is tuple and all(type(row) is TheoremSpec for row in rows),
                 "an inherited factory returned something other than exact source rows")
        for row in rows:
            _require(row.name not in table or table[row.name] == row,
                     "different canonical specifications share a name")
            table[row.name] = row
    after = prior._edition_bindings()
    _require(before.keys() == after.keys()
             and all(after[name] is value for name, value in before.items()),
             "source planning unexpectedly imported an Alpha edition")
    return table


def stage_metrics(through):
    _require(type(through) is int and through in PHASES
             and PHASES == (32, 34, 35, 37)
             and STAGE_RECORDS == ((32, 276, 756, 6), (34, 278, 780, 7),
                                   (35, 280, 798, 6), (37, 283, 812, 6))
             and PREVIOUS_THROUGH == {32: 25, 34: 32, 35: 34, 37: 35},
             "only the four exact bounded source prefixes are authorized")
    return next(record[1:] for record in STAGE_RECORDS if record[0] == through)


def stage_path(through):
    stage_metrics(through)
    return ARTIFACT_DIRECTORY / (OUTPUT_PREFIX + str(through) + "-proof-bundle-v1.json")


@dataclass(frozen=True, slots=True)
class SourceSelection:
    owned: tuple[TheoremSpec, ...]
    canonical_support: tuple[TheoremSpec, ...]
    complete_specs: tuple[TheoremSpec, ...]
    root_names: tuple[str, ...]
    through: int

    @property
    def support(self):
        return self.canonical_support

    def role(self, name):
        if name in {row.name for row in self.owned[:25]}:
            return "prior_non_admitted_shift_scalar"
        if name in {row.name for row in self.owned[25:]}:
            return "new_non_admitted_associativity_support"
        if name in {row.name for row in self.canonical_support}:
            return "inherited_canonical_source"
        raise WorkingError("the requested theorem is outside this exact source cone")


def select_support(state, owned_names=None):
    validate_state(state)
    all_new = {row.name: row for row in state.rows}
    if owned_names is None:
        owned_names = tuple(all_new)
    _require(type(owned_names) is tuple and all(type(name) is str for name in owned_names)
             and len(owned_names) in PHASES
             and owned_names == tuple(all_new)[:len(owned_names)],
             "only an exact approved source-order prefix is allowed")
    through = len(owned_names)
    count, edges, root_count = stage_metrics(through)
    canonical_table = canonical_provider_table()
    _require(not canonical_table.keys() & all_new.keys(),
             "a working theorem overwrites a canonical source name")
    table = canonical_table | all_new
    ordered, active, seen = [], set(), set()

    def visit(name):
        _require(name in table, "missing actual source prerequisite: " + name)
        _require(name not in active, "cyclic actual source prerequisite: " + name)
        if name in seen:
            return
        row = table[name]
        _require(type(row.dependencies) is tuple and len(set(row.dependencies)) == len(row.dependencies),
                 "an actual ordered premise list repeats a dependency")
        active.add(name)
        for dependency in row.dependencies:
            visit(dependency)
        active.remove(name)
        seen.add(name)
        ordered.append(row)

    for name in owned_names:
        visit(name)
    used = {dependency for row in ordered for dependency in row.dependencies}
    roots = tuple(name for name in owned_names if name not in used)
    _require(len(ordered) == count and sum(len(row.dependencies) for row in ordered) == edges
             and len(roots) == root_count and count + 1 <= closure.DEFAULT_BUNDLE_LIMITS.max_nodes
             and edges + root_count <= closure.DEFAULT_BUNDLE_LIMITS.max_edges,
             "the exact stage source cone or original size ceiling changed")
    selected = SourceSelection(tuple(all_new[name] for name in owned_names),
        tuple(row for row in ordered if row.name in canonical_table), tuple(ordered), roots, through)
    _require({row.name for row in selected.owned} | {row.name for row in selected.support} == seen,
             "a source cone contains a future or unowned working theorem")
    if through == 37:
        _require(len(selected.support) == EXPECTED_INHERITED_COUNT == 246
                 and selected.root_names == PRINCIPAL_ROOTS,
                 "the complete246+37 source cone or six maximal roots changed")
    return selected


@dataclass(frozen=True, slots=True)
class ExecutionSelection:
    source: SourceSelection
    frontier: tuple[TheoremSpec, ...]
    plan: closure.BottomLayerPlan


def execution_selection(state, owned_names=None):
    """Only proof workers ask the unchanged assembler for its actual v30 base."""
    selected = select_support(state, owned_names)
    parent = {row.name: row for row in closure.parent_snapshot().specs}
    for row in selected.complete_specs:
        if row.name in parent:
            _require(row == parent[row.name], "an inherited source differs from its literal v30 premise")
    frontier = tuple(row for row in selected.complete_specs if row.name not in parent)
    plan = closure.bottom_layer_plan(frontier)
    complete = {row.name: row for row in selected.complete_specs}
    _require(set(complete) == {row.name for row in plan.rows}
             and plan.root_names == selected.root_names,
             "the unchanged assembler cone differs from the source-only plan")
    for row in plan.rows:
        exact = complete[row.name]
        _require(row.dependencies == exact.dependencies
                 and row.statement_sha256 == sha256(exact.statement.encode()).hexdigest(),
                 "the unchanged assembler changed an exact target or ordered premise")
    return ExecutionSelection(selected, frontier, plan)


def required_seed_paths(through):
    stage_metrics(through)
    require_seed_identities()
    if through == 32:
        return tuple(ROOT / pin.path for pin in (PRIOR25_SEED, CANONICAL121_SEED, POLYNOMIAL_SEED))
    if through == 34:
        return (stage_path(32),)
    if through == 35:
        return (stage_path(34), ROOT / CANONICAL121_SEED.path)
    return (stage_path(35), ROOT / V27_SEED.path)


def require_seed_identities():
    _require(type(SEED_PINS) is tuple and len(SEED_PINS) == 4
             and all(type(pin) is FilePin for pin in SEED_PINS)
             and SEED_PINS == (PRIOR25_SEED, CANONICAL121_SEED, POLYNOMIAL_SEED, V27_SEED)
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in SEED_PINS) == _SEED_IDENTITIES,
             "the four literal seed identities or exact phase roles changed")


def _inert_bundle_metadata(raw):
    value = json.loads(raw)
    _require(type(value) is list and len(value) == 4 and value[0] == "peano-lab-bundle-v1"
             and type(value[1]) is int and type(value[3]) is list
             and 0 < len(value[3]) <= closure.DEFAULT_BUNDLE_LIMITS.max_nodes
             and 0 <= value[1] < len(value[3]),
             "a seed has malformed inert bundle metadata")
    nodes = value[3]
    _require(all(type(node) is list and len(node) == 4 and type(node[0]) is int
                 and node[0] > 0 and type(node[2]) is list
                 and all(type(edge) is int and 0 <= edge < position for edge in node[2])
                 for position, node in enumerate(nodes))
             and value[2] == nodes[value[1]][1],
             "a seed has malformed ordered target metadata")
    return value


def seed_inventory(paths, *, through):
    expected = required_seed_paths(through)
    _require(type(paths) is tuple and bool(paths)
             and all(isinstance(path, (str, Path)) for path in paths),
             "stage seed paths must be an explicit nonempty tuple")
    absolute = tuple(Path(path).absolute() for path in paths)
    _require(all(".." not in path.parts for path in absolute) and absolute == expected,
             "only this phase's exact real seeds, in the declared order, are allowed")
    require_seed_identities()
    checked = closure._validate_seeds(paths)
    _require(tuple(Path(path).absolute() for path in checked) == expected,
             "original seed validation changed the exact stage inputs")
    known, result = {ROOT / pin.path: pin for pin in SEED_PINS}, []
    for path in expected:
        if path in known:
            pin = known[path]
            read_pin(pin)
        else:
            _require(path == stage_path(PREVIOUS_THROUGH[through])
                     and path.parent == ARTIFACT_DIRECTORY,
                     "only the immediately preceding owned stage artifact may be reused")
            info = path.lstat()
            _require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1,
                     "a previous stage is not an owned regular artifact")
            raw = bounded_bytes(path, MAX_BYTES)
            pin = FilePin(path.relative_to(ROOT).as_posix(), len(raw), sha256(raw).hexdigest())
            value = _inert_bundle_metadata(raw)
            nodes, edges, roots = stage_metrics(PREVIOUS_THROUGH[through])
            _require(len(value[3]) == nodes + 1 and value[1] == nodes
                     and sum(len(node[2]) for node in value[3]) == edges + roots,
                     "a previous stage has the wrong actual inert node/edge inventory")
            read_pin(pin)
        result.append(pin)
    return tuple(result)


def seed_coverage(selected, pins):
    """Exact target/ordered-premise coverage, explicitly NOT a proof check."""
    _require(type(selected) is SourceSelection and type(pins) is tuple and bool(pins)
             and all(type(pin) is FilePin for pin in pins), "exact stage syntax and seed pins are required")
    state = load_candidate_state()
    _require(selected == select_support(state, tuple(row.name for row in selected.owned)),
             "seed coverage received an altered source selection")
    _require(tuple(ROOT / pin.path for pin in pins) == required_seed_paths(selected.through),
             "seed coverage is not this stage's exact input sequence")
    fresh = {row.name for row in selected.owned[PREVIOUS_THROUGH[selected.through]:]}
    wanted = tuple(row for row in selected.complete_specs if row.name not in fresh)
    # Reuse only the old inert JSON target/premise comparison. The following
    # container is coverage data; it creates no HA receipt or replay capability.
    coverage = prior.seed_coverage(prior.SupportSelection(
        selected.owned, wanted, selected.complete_specs, selected.root_names), pins)
    coverage["preexisting_targets"] = coverage.pop("inherited_targets")
    coverage.update(through=selected.through, fresh_working_rows=len(fresh),
                    previous_working_rows=PREVIOUS_THROUGH[selected.through])
    return coverage


def state_binding(state, *, final=False):
    _require(type(final) is bool, "final registration must be a literal Boolean")
    validate_state(state)
    require_working_sources()
    require_runtime_sources()
    require_preserved_archives()
    require_seed_identities()
    for pin in SEED_PINS:
        check_pin(pin, ROOT, MAX_BYTES)
    check_pin(FilePin(closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES,
                      closure.PARENT_CATALOG_SHA256), ROOT, MAX_CATALOG_BYTES)
    if final:
        require_parent_registration()
    controls = []
    for name in CONTROL_FILES:
        raw = bounded_bytes(HERE / name, MAX_SOURCE_BYTES)
        controls.append((WORKING_RELATIVE + "/" + name, len(raw), sha256(raw).hexdigest()))
    return sha256(canonical({
        "controls": controls, "runtime": _RUNTIME_RECORDS, "providers": PROVIDER_MODULES,
        "factories": _FACTORY_RECORDS, "specs_sha256": state.specs_sha256,
        "accepted25_preservation_only": _PRIOR25_RECORDS,
        "earlier_archives": prior.PRESERVED_ARCHIVES, "literal_seeds": _SEED_IDENTITIES,
        "original_v30_syntax": [closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES, closure.PARENT_CATALOG_SHA256],
        "current_parent": [asdict(pin) for pin in PARENT_CATALOG_PINS],
        "channels": asdict(PARENT_CHANNEL_PIN), "current_parent_identity": PARENT_IDENTITY_SHA256,
        "current_parent_enrollment": PARENT_ENROLLMENT_SHA256,
        "phases": STAGE_RECORDS, "ordinary_principals": list(zip(PRINCIPAL_ROOTS, PRINCIPAL_STATEMENT_SHA256, strict=True)),
        "final_registration_required": final, "stored_observations_supply_authority": False,
    })).hexdigest()


def local_manifest():
    state = load_candidate_state()
    selected = select_support(state)
    return {
        "schema": "peano-working-associativity-closure-syntax-v1", "syntax_only": True,
        "non_admitted_rows": 37, "previous_non_admitted_rows": 25, "additional_non_admitted_rows": 12,
        "factory_counts": [15, 10, 6, 1, 3, 2], "specs_sha256": state.specs_sha256,
        "ordered_names": [row.name for row in state.rows],
        "inherited_source_rows": len(selected.support), "complete_source_rows": len(selected.complete_specs),
        "new_dependency_edges": 179, "new_script_commands": 4303,
        "complete_dependency_edges": 812, "packaged_nodes": 284, "packaged_edges": 818,
        "maximal_roots": list(selected.root_names), "ordinary_principals": list(PRINCIPAL_ROOTS),
        "phases": [{"through": through, "nodes": nodes + 1, "edges": edges + roots,
                    "required_seeds": [path.relative_to(ROOT).as_posix()
                                       for path in required_seed_paths(through)]}
                   for through, nodes, edges, roots in STAGE_RECORDS],
        "global_current4092_novelty_checked": False, "original_ha_checked": False,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "complete_checkpoint_acceptance": False, "gcd_bezout_proved": False,
        "full_G091_proved": False, "alpha_admission_performed": False, "stable_admission_performed": False,
    }
