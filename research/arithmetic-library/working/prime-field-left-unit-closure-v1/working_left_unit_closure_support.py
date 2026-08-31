"""Exact source-only planning for the separate non-admitted44+8 left-unit cone.

Six prior44 authority files and the transitive prior37/old25 inputs are pinned;
prior44 READMEs and observations are not proof inputs. Authoring checks both
real whole seeds anew through the unchanged original assembler. Only the
separate novelty task parses the full current4092 catalogue.
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
WORKING_RELATIVE = "research/arithmetic-library/working/prime-field-left-unit-closure-v1"
if HERE != ROOT / WORKING_RELATIVE or not (ROOT / "peano-lab/py/peano_lab").is_dir():
    raise RuntimeError("the left-unit closure belongs only in its new working directory")
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import constructive_g009_support as inherited

FilePin = inherited.FilePin
PRIOR44_RELATIVE = "research/arithmetic-library/working/prime-field-divisibility-closure-v1"
PRIOR44_SUPPORT_PIN = FilePin(
    PRIOR44_RELATIVE + "/working_divisibility_closure_support.py", 29359,
    "774899f1dd1ddfb205505ad89e5fbe7d3306f4e0508dc8073c4bb2019a27042c")
_PRIVATE_PRIOR_NAME = "_working_left_unit_closure_v1_prior44"


def _load_prior_support():
    """Dataclasses need a temporary private controller name, never a peano alias."""
    if _PRIVATE_PRIOR_NAME in sys.modules:
        raise ValueError("the private prior-controller name is already owned")
    pin = PRIOR44_SUPPORT_PIN
    inherited.check_pin(pin, ROOT, inherited.MAX_SOURCE_BYTES)
    path = ROOT / pin.path
    raw = inherited.bounded_bytes(path, inherited.MAX_SOURCE_BYTES)
    if (len(raw), sha256(raw).hexdigest()) != (pin.bytes, pin.sha256):
        raise ValueError("the pinned prior44 controller changed before loading")
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
_edition_bindings = prior._edition_bindings
CPU_LIMITS, WALL_SECONDS, MAX_RSS_BYTES = (170, 175), 180, 1536 * 1024 * 1024
EXPECTED_COUNT, EXPECTED_INHERITED_COUNT = 52, 253
SPECS_SHA256 = "c6c4b0610b911d1f17a8b0ef2b6fa4b8f7b79e73e7f1f85f0fe2d6b1a42edc63"
NAMES_SHA256 = "ae22374d7ba85dbcb65cf0659eeec772234ba45eefd0138b601869c98ca170b2"
ARTIFACT_DIRECTORY = HERE / "artifacts"
OUTPUT_PREFIX = "working-left-unit-closure-prefix-"
PHASES = (52,)
# through, theorem nodes, theorem edges, maximal roots (packager is additional).
STAGE_RECORDS = ((52, 305, 876, 12),)
PREVIOUS_THROUGH = {52: 44}
CONTROL_FILES = (
    "working_left_unit_closure_support.py", "export_working_left_unit_closure.py",
    "check_working_left_unit_closure.py", "test_working_left_unit_closure.py",
    "working-left-unit-closure-rfc-v1.md",
)
PRINCIPAL_ROOTS = (
    "prime_field_polynomial_convolution_shift_right_exists",
    "prime_field_polynomial_convolution_right_scale_exists",
    "prime_field_polynomial_convolution_right_scale_zero",
    "prime_field_convolution_coefficient_right_append_add",
    "prime_field_polynomial_convolution_right_append_exists",
    "prime_field_polynomial_right_divides_divisor_bounded",
    "prime_field_polynomial_right_divides_dividend_bounded",
    "prime_field_polynomial_right_divides_equivalent_target",
    "prime_field_polynomial_right_divides_empty",
    "prime_field_polynomial_right_divides_equivalent_divisor",
    "prime_field_polynomial_right_divides_transitive",
    "prime_field_polynomial_right_divides_reflexive",
)
PRINCIPAL_STATEMENT_SHA256 = (
    "0fc173b813282a7111d604245b1706a4c01c5bcf566812151810e9afe38f065d",
    "5d0349367decc3084471726b73a77617d49f484cf31191bb78effbc434167156",
    "fd6d04fd88ff9f594f7ee27de04486c1932ce5de30b6030b6b9b18cb547511ef",
    "a11e1f29b31ae9076959706b6b5d0813689194a2ab57a1a4e879e6a6c3ad69bd",
    "0ef69b8524dd48c1a9805f158e9eff25c41e421b85378b96b51b7c63bd89f087",
    "544318213b2b7d1697a9d395876f8de05096b5f5d66464fcf35d0607b2766f8d",
    "a1f28266b77ee02c24747cf96ca7234d9d13bc3c46d38b2bb6b2f805c1538278",
    "87d9faf6a5934bdd2423446f49f7a9b58ff6b0da1c60509d4f0b9af98bb04b14",
    "3fdc5c341af454a1bf0018deaae0d0f6bdf04d524f98073f07d191911246c9de",
    "608a6407b35414fe4335c37afae0bbd3de15caa82ee1d3c67f25ef9cf9b76ccb",
    "581d2fad3dc745194f2297dad6cff729117d75f5b686c87dd8716374d0a98d10",
    "d8f3531eb2f6d2fb37e8ee936807a66a7dc1e49b71c95c7c7023c7964fc03852",
)

# Exactly five prior44 controls plus its actual final artifact. This is NOT
# a complete-tree44 binding: its README and observations are never read here.
PROTECTED_PRIOR44_PINS = (
    FilePin("research/arithmetic-library/working/prime-field-divisibility-closure-v1/working_divisibility_closure_support.py", 29359, "774899f1dd1ddfb205505ad89e5fbe7d3306f4e0508dc8073c4bb2019a27042c"),
    FilePin("research/arithmetic-library/working/prime-field-divisibility-closure-v1/export_working_divisibility_closure.py", 9100, "69584baf75da16ac6e33abed775d118036397cf1b0cf76841347d586225a1cb9"),
    FilePin("research/arithmetic-library/working/prime-field-divisibility-closure-v1/check_working_divisibility_closure.py", 12601, "346ff063b6f2b5b9d76b6e11a8456115376f773118b7306fc57fe2661845351e"),
    FilePin("research/arithmetic-library/working/prime-field-divisibility-closure-v1/test_working_divisibility_closure.py", 47787, "35a798278f90212969a5e16f2400908b9c152eb8208079f7ef1d89a9be59969f"),
    FilePin("research/arithmetic-library/working/prime-field-divisibility-closure-v1/working-divisibility-closure-rfc-v1.md", 11623, "a72c8c9887f866296b0204abae82e87d03c8615e12c1ac1f33a9fe20d321af7d"),
    FilePin("research/arithmetic-library/working/prime-field-divisibility-closure-v1/artifacts/working-divisibility-closure-prefix-44-proof-bundle-v1.json", 1757906, "6fb92e887c2ddd604e71574095fdf492814af9651e15f0b36386be3538b1a7e7"),
)
_PRIOR44_RECORDS = tuple((pin.path, pin.bytes, pin.sha256) for pin in PROTECTED_PRIOR44_PINS)

FACTORIES = (*prior.FACTORIES,
    Factory("research/arithmetic-library/working/prime-field-left-unit-v1",
            "prime_field_polynomial_left_unit_candidate", 8, 16858,
            "dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6",
            16474, "5b8758079485c1c7f8a448f218a4b70b9e5df11722eabf63ec6fcc1e68802c71",
            "d948ceded7269773df58eca0ec6d16f77aa8f207483beed48f85bec30e083f08"),
)
_FACTORY_RECORDS = tuple(asdict(owner) for owner in FACTORIES)
ADDITIONAL_RUNTIME_PINS = (
    FilePin("peano-lab/py/peano_lab/library/bertrand_power_valuation_candidate.py", 23839, "e1d7177ba713425dd3545fa7de2d78dae73ce155e09fabcfe6cd46fcf562fd57"),
    FilePin("peano-lab/py/peano_lab/library/bertrand_power_valuation_laws_candidate.py", 12196, "7b95e4f2a16df3866cb3e01f17d1b455000706454a1a241948957c4548a0a17f"),
    FilePin("peano-lab/py/peano_lab/library/fermat_residue_map_candidate.py", 19111, "2b30505a6f6febe5e55874726855b25ae63ed420afd1c3821ba5a082509833e8"),
)
RUNTIME_PINS = (*prior.RUNTIME_PINS, *ADDITIONAL_RUNTIME_PINS)
_RUNTIME_RECORDS = tuple((pin.path, pin.bytes, pin.sha256) for pin in RUNTIME_PINS)
_RUNTIME_BY_PATH = {pin.path: pin for pin in RUNTIME_PINS}
# The final factory genuinely uses singular "law"; no inferred alias is used.
PROVIDER_FACTORIES = (
    ("prime_field_arithmetic_candidate", "make_prime_field_arithmetic_candidate_theorems"),
    ("prime_field_polynomial_candidate", "make_prime_field_polynomial_candidate_theorems"),
    ("prime_field_polynomial_convolution_candidate", "make_prime_field_polynomial_convolution_candidate_theorems"),
    ("prime_field_polynomial_representation_candidate", "make_prime_field_polynomial_representation_candidate_theorems"),
    ("finite_division_prefix_candidate", "make_finite_division_prefix_candidate_theorems"),
    ("finite_pointwise_mul_recode_candidate", "make_finite_pointwise_mul_recode_candidate_theorems"),
    ("finite_repeat_sum_candidate", "make_finite_repeat_sum_candidate_theorems"),
    ("finite_sum_transport_candidate", "make_finite_sum_transport_candidate_theorems"),
    ("binary_modular_exponentiation_candidate", "make_binary_modular_exponentiation_candidate_theorems"),
    ("hensel_prime_power_candidate", "make_hensel_prime_power_candidate_theorems"),
    ("prime_field_polynomial_convolution_triangular_candidate", "make_prime_field_polynomial_convolution_triangular_candidate_theorems"),
    ("prime_field_polynomial_distributivity_candidate", "make_prime_field_polynomial_distributivity_candidate_theorems"),
    ("prime_field_polynomial_convolution_padding_candidate", "make_prime_field_polynomial_convolution_padding_candidate_theorems"),
    ("prime_field_polynomial_equivalence_candidate", "make_prime_field_polynomial_equivalence_candidate_theorems"),
    ("prime_field_polynomial_convolution_congruence_candidate", "make_prime_field_polynomial_convolution_congruence_candidate_theorems"),
    ("matrix_coded_product_candidate", "make_matrix_coded_product_candidate_theorems"),
    ("matrix_rank_finite_coding_candidate", "make_matrix_rank_finite_coding_candidate_theorems"),
    ("matrix_recursive_determinant_extensional_candidate", "make_matrix_recursive_determinant_extensional_candidate_theorems"),
    ("bertrand_power_valuation_laws_candidate", "make_bertrand_power_valuation_law_candidate_theorems"),
)
_PROVIDER_FACTORY_RECORDS = PROVIDER_FACTORIES
PROVIDER_MODULES = tuple(name for name, _factory in PROVIDER_FACTORIES)
_PROVIDER_IDENTITIES = PROVIDER_MODULES

PRIOR44_SEED = FilePin(
    PRIOR44_RELATIVE + "/artifacts/working-divisibility-closure-prefix-44-proof-bundle-v1.json",
    1757906, "6fb92e887c2ddd604e71574095fdf492814af9651e15f0b36386be3538b1a7e7")
PRODUCTS_SEED = FilePin(
    "research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json",
    745307, "55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3")
SEED_PINS = (PRIOR44_SEED, PRODUCTS_SEED)
_SEED_IDENTITIES = tuple((pin.path, pin.bytes, pin.sha256) for pin in SEED_PINS)
PARENT_CATALOG_PINS = prior.PARENT_CATALOG_PINS
PARENT_CHANNEL_PIN = prior.PARENT_CHANNEL_PIN
PARENT_IDENTITY_SHA256 = prior.PARENT_IDENTITY_SHA256
PARENT_ENROLLMENT_SHA256 = prior.PARENT_ENROLLMENT_SHA256
_PARENT_RECORDS = (PARENT_CATALOG_PINS, PARENT_CHANNEL_PIN,
                   PARENT_IDENTITY_SHA256, PARENT_ENROLLMENT_SHA256)


def require_preserved_archives():
    # The unchanged prior44 helper authenticates the prior37 authority subset
    # and complete old25 archive. No prior44 observation supplies authority.
    prior.require_preserved_archives()
    _require(type(PROTECTED_PRIOR44_PINS) is tuple and len(PROTECTED_PRIOR44_PINS) == 6
             and all(type(pin) is FilePin for pin in PROTECTED_PRIOR44_PINS)
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in PROTECTED_PRIOR44_PINS)
                 == _PRIOR44_RECORDS
             and PROTECTED_PRIOR44_PINS[0] == PRIOR44_SUPPORT_PIN,
             "the six exact prior44 authority-file identities changed")
    for pin in PROTECTED_PRIOR44_PINS:
        check_pin(pin, ROOT, MAX_BYTES)


def require_runtime_sources():
    prior.require_runtime_sources()
    _require(type(RUNTIME_PINS) is tuple and len(RUNTIME_PINS) == len(_RUNTIME_RECORDS) == 112
             and all(type(pin) is FilePin for pin in RUNTIME_PINS)
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in RUNTIME_PINS) == _RUNTIME_RECORDS
             and RUNTIME_PINS == (*prior.RUNTIME_PINS, *ADDITIONAL_RUNTIME_PINS)
             and len(_RUNTIME_BY_PATH) == len(RUNTIME_PINS),
             "the original runtime or three actual additional source identities changed")
    _require(type(PROVIDER_FACTORIES) is tuple and len(PROVIDER_FACTORIES) == 19
             and all(type(pair) is tuple and len(pair) == 2
                     and all(type(value) is str and value for value in pair) for pair in PROVIDER_FACTORIES)
             and PROVIDER_FACTORIES == _PROVIDER_FACTORY_RECORDS
             and PROVIDER_MODULES == _PROVIDER_IDENTITIES
                 == tuple(name for name, _factory in PROVIDER_FACTORIES)
             and PROVIDER_MODULES[:-1] == prior.PROVIDER_MODULES,
             "the nineteen actual canonical module/factory identities changed")
    # Derive every actual byte read from the validated full inventory, not a
    # separately mutable list of optional extras.
    for pin in RUNTIME_PINS:
        check_pin(pin, ROOT, MAX_SOURCE_BYTES)


def require_working_sources():
    _require(type(FACTORIES) is tuple and len(FACTORIES) == 8
             and all(type(owner) is Factory for owner in FACTORIES)
             and tuple(asdict(owner) for owner in FACTORIES) == _FACTORY_RECORDS
             and tuple(owner.count for owner in FACTORIES) == (15, 10, 6, 1, 3, 2, 7, 8),
             "the frozen44+8 source ownership changed")
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
    before = _edition_bindings()
    rows = []
    for owner in FACTORIES:
        raw, path = read_pin(owner.source, MAX_SOURCE_BYTES), ROOT / owner.source.path
        alias = "_working_left_unit_closure_v1_" + owner.module
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
    after = _edition_bindings()
    _require(before.keys() == after.keys()
             and all(after[name] is value for name, value in before.items()),
             "source construction imported or replaced an Alpha edition")
    state = CandidateState(tuple(rows), closure._specs_digest(tuple(rows)))
    validate_state(state)
    return state


def validate_state(state):
    _require(type(state) is CandidateState and type(state.rows) is tuple
             and len(state.rows) == EXPECTED_COUNT == 52
             and all(type(row) is TheoremSpec for row in state.rows)
             and state.specs_sha256 == SPECS_SHA256
             and closure._specs_digest(state.rows) == SPECS_SHA256,
             "an altered or incomplete frozen52 syntax state is not accepted")
    closure._validate_frontier(state.rows)
    _require(sha256("\n".join(row.name for row in state.rows).encode()).hexdigest() == NAMES_SHA256
             and sum(len(row.dependencies) for row in state.rows) == 234
             and sum(len(row.script) for row in state.rows) == 5256,
             "the exact52 names, ordered premises or native command inventory changed")
    table, seen = {row.name: row for row in state.rows}, set()
    for row in state.rows:
        _require((set(row.dependencies) & table.keys()) <= seen,
                 "a new source has a forward or cyclic prerequisite")
        seen.add(row.name)
    _require(len(PRINCIPAL_ROOTS) == 12 and len(set(PRINCIPAL_ROOTS)) == 12
             and tuple(sha256(table[name].statement.encode()).hexdigest()
                       for name in PRINCIPAL_ROOTS if name in table) == PRINCIPAL_STATEMENT_SHA256,
             "one of the twelve exact ordinary principal statements changed")


def canonical_provider_table():
    require_runtime_sources()
    before = _edition_bindings()
    table = {row.name: row for row in THEOREMS}
    _require(len(table) == len(THEOREMS), "the primitive theorem ladder repeats a name")
    for short, factory_name in PROVIDER_FACTORIES:
        relative = "peano-lab/py/peano_lab/library/" + short + ".py"
        _require(relative in _RUNTIME_BY_PATH, "an inherited source is not registered")
        module = import_module("peano_lab.library." + short)
        _require(type(module) is ModuleType and getattr(module, "__file__", None) == str(ROOT / relative)
                 and getattr(getattr(module, "__spec__", None), "origin", None) == str(ROOT / relative),
                 "an inherited canonical module resolved to foreign bytes")
        factory = getattr(module, factory_name, None)
        _require(callable(factory) and factory.__module__ == "peano_lab.library." + short,
                 "an inherited canonical factory was replaced")
        rows = factory(TheoremSpec)
        _require(type(rows) is tuple and all(type(row) is TheoremSpec for row in rows),
                 "an inherited factory returned something other than exact source rows")
        for row in rows:
            _require(row.name not in table or table[row.name] == row,
                     "different canonical specifications share a name")
            table[row.name] = row
    after = _edition_bindings()
    _require(before.keys() == after.keys()
             and all(after[name] is value for name, value in before.items()),
             "source planning unexpectedly imported an Alpha edition")
    return table


def stage_metrics(through):
    _require(type(through) is int and through in PHASES
             and PHASES == (52,)
             and STAGE_RECORDS == ((52, 305, 876, 12),)
             and PREVIOUS_THROUGH == {52: 44},
             "only the exact complete52 source prefix is authorized")
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
        if name in {row.name for row in self.owned[:44]}:
            return "prior_non_admitted_divisibility"
        if name in {row.name for row in self.owned[44:]}:
            return "new_non_admitted_left_unit"
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
    if through == 52:
        _require(len(selected.support) == EXPECTED_INHERITED_COUNT == 253
                 and selected.root_names == PRINCIPAL_ROOTS,
                 "the complete253+52 source cone or twelve maximal roots changed")
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
    return tuple(ROOT / pin.path for pin in (PRIOR44_SEED, PRODUCTS_SEED))


def require_seed_identities():
    _require(type(SEED_PINS) is tuple and len(SEED_PINS) == 2
             and all(type(pin) is FilePin for pin in SEED_PINS)
             and SEED_PINS == (PRIOR44_SEED, PRODUCTS_SEED)
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in SEED_PINS) == _SEED_IDENTITIES,
             "the two literal real seed identities or their exact roles changed")


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
        pin = known[path]
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
    coverage = prior.prior.prior.seed_coverage(prior.prior.prior.SupportSelection(
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
        "provider_factories": PROVIDER_FACTORIES,
        "factories": _FACTORY_RECORDS, "specs_sha256": state.specs_sha256,
        "prior44_authority_files": _PRIOR44_RECORDS,
        "prior37_authority_files": prior._PRIOR37_RECORDS,
        "complete_prior44_tree_bound": False,
        "complete_prior37_tree_bound": False,
        "accepted25_preservation_only": prior.prior._PRIOR25_RECORDS,
        "earlier_archives": prior.prior.prior.PRESERVED_ARCHIVES, "literal_seeds": _SEED_IDENTITIES,
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
        "schema": "peano-working-left-unit-closure-syntax-v1", "syntax_only": True,
        "non_admitted_rows": 52, "previous_non_admitted_rows": 44, "additional_non_admitted_rows": 8,
        "factory_counts": [15, 10, 6, 1, 3, 2, 7, 8], "specs_sha256": state.specs_sha256,
        "ordered_names": [row.name for row in state.rows],
        "inherited_source_rows": len(selected.support), "complete_source_rows": len(selected.complete_specs),
        "new_dependency_edges": 234, "new_script_commands": 5256,
        "complete_dependency_edges": 876, "packaged_nodes": 306, "packaged_edges": 888,
        "maximal_roots": list(selected.root_names), "ordinary_principals": list(PRINCIPAL_ROOTS),
        "phases": [{"through": through, "nodes": nodes + 1, "edges": edges + roots,
                    "required_seeds": [path.relative_to(ROOT).as_posix()
                                       for path in required_seed_paths(through)]}
                   for through, nodes, edges, roots in STAGE_RECORDS],
        "global_current4092_novelty_checked": False, "original_ha_checked": False,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "complete_checkpoint_acceptance": False, "gcd_bezout_proved": False,
        "prior44_authority_file_count": 6, "complete_prior44_tree_bound": False,
        "full_G091_proved": False, "alpha_admission_performed": False, "stable_admission_performed": False,
    }
