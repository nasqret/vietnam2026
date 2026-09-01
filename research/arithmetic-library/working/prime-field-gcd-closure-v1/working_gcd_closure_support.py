"""Source planning and fail-closed registration for a separate gcd checkpoint.

Mutable candidate snapshots are permitted ONLY for planning and conditional
diagnostics. Authoring/final verification require a subsequent explicit literal
freeze of every source/test, ordered specification, stage and ordinary root.
No historical observation supplies mathematical authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib import util
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING_RELATIVE = 'research/arithmetic-library/working/prime-field-gcd-closure-v1'
if HERE != ROOT / WORKING_RELATIVE:
    raise ValueError('gcd controls belong only to the new working directory')
for _path in (ROOT / 'peano-lab/py', ROOT / 'scripts'):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
import constructive_g009_support as inherited

FilePin = inherited.FilePin
PRIOR_RELATIVE = 'research/arithmetic-library/working/prime-field-euclidean-closure-v1'
PRIOR_AUTHORITY_PINS = (
    FilePin(PRIOR_RELATIVE + '/working_euclidean_closure_support.py', 39832, '2cf88350845af863835de0c96670a8f1aa96a102ef806e9a0c11b19cc8b6fb5d'),
    FilePin(PRIOR_RELATIVE + '/export_working_euclidean_closure.py', 9096, '1bc647d2ea8569a758e80e382bfce5dfee8702ba874d665a526b007b04c43e76'),
    FilePin(PRIOR_RELATIVE + '/check_working_euclidean_closure.py', 12600, 'ea919490f2a780e3b632c170f224fdf943f4290125367e6abb69bcf458aa25c5'),
    FilePin(PRIOR_RELATIVE + '/test_working_euclidean_closure.py', 55619, '61e2fdadc3adb845bdfe90e5b03ae8d69dc01342fb660f86ffc95bb05f0fe0ae'),
    FilePin(PRIOR_RELATIVE + '/working-euclidean-closure-rfc-v1.md', 10758, '9e25630589c175775e4d741647c02e3aa263e129ac869cef13a33b210e92db75'),
    FilePin(PRIOR_RELATIVE + '/artifacts/working-euclidean-closure-prefix-95-proof-bundle-v1.json', 3446531, '454f23a30acfb9188d7458a9dc206ce9fc14a61510d0c3b548a611a9d682af56'),
)
PRIOR_FINAL_BINDING = '005eeadb5fe1798f531940bac31c9ae60d9346619459814b998500cb958b2449'
_PRIVATE_PRIOR_NAME = '_working_gcd_closure_prior95'


def _load_prior():
    if _PRIVATE_PRIOR_NAME in sys.modules:
        raise ValueError('private predecessor controller name already owned')
    pin = PRIOR_AUTHORITY_PINS[0]
    inherited.check_pin(pin, ROOT, inherited.MAX_SOURCE_BYTES)
    raw = inherited.bounded_bytes(ROOT / pin.path, inherited.MAX_SOURCE_BYTES)
    if (len(raw), sha256(raw).hexdigest()) != (pin.bytes, pin.sha256):
        raise ValueError('predecessor bytes changed before execution')
    module = ModuleType(_PRIVATE_PRIOR_NAME)
    module.__file__, module.__package__ = str(ROOT / pin.path), ''
    module.__spec__ = util.spec_from_file_location(_PRIVATE_PRIOR_NAME, ROOT / pin.path)
    sys.modules[_PRIVATE_PRIOR_NAME] = module
    try:
        exec(compile(raw, module.__file__, 'exec'), module.__dict__)
        inherited.check_pin(pin, ROOT, inherited.MAX_SOURCE_BYTES)
        return module
    finally:
        if sys.modules.get(_PRIVATE_PRIOR_NAME) is not module:
            raise ValueError('foreign replacement is preserved, not removed')
        del sys.modules[_PRIVATE_PRIOR_NAME]


prior = _load_prior()
closure, TheoremSpec = prior.closure, prior.TheoremSpec
WorkingError, _require = prior.WorkingError, prior._require
canonical, bounded_bytes, read_pin, check_pin = prior.canonical, prior.bounded_bytes, prior.read_pin, prior.check_pin
_safe_relative, _digest = prior._safe_relative, prior._digest
MAX_SOURCE_BYTES, MAX_BYTES, MAX_CATALOG_BYTES = prior.MAX_SOURCE_BYTES, prior.MAX_BYTES, prior.MAX_CATALOG_BYTES
CPU_LIMITS, WALL_SECONDS, MAX_RSS_BYTES = (170, 175), 180, 1536 * 1024 * 1024
PRIOR95_SEED = PRIOR_AUTHORITY_PINS[-1]
_PRIOR_RECORDS = tuple(asdict(pin) for pin in PRIOR_AUTHORITY_PINS)
PARENT_CATALOG_PINS, PARENT_CHANNEL_PIN = prior.PARENT_CATALOG_PINS, prior.PARENT_CHANNEL_PIN
PARENT_IDENTITY_SHA256, PARENT_ENROLLMENT_SHA256 = prior.PARENT_IDENTITY_SHA256, prior.PARENT_ENROLLMENT_SHA256
require_parent_registration = prior.require_parent_registration

# Exact directories, factories and mathematical/test bytes are registered.
FAMILIES = (
    ('laws', 'prime-field-gcd-bezout-laws-v1', 'prime_field_polynomial_gcd_bezout_laws_candidate'),
    ('existence', 'prime-field-gcd-existence-v1', 'prime_field_polynomial_gcd_existence_candidate'),
    ('uniqueness', 'prime-field-gcd-uniqueness-v1', 'prime_field_polynomial_gcd_uniqueness_candidate'),
)
_FAMILY_IDENTITIES = FAMILIES
# Literal source-only freeze; future authored output pins remain absent.
FROZEN_SOURCE_PINS = (
    FilePin("research/arithmetic-library/working/prime-field-gcd-bezout-laws-v1/prime_field_polynomial_gcd_bezout_laws_candidate.py", 15300, "76b90226e5e29fdde3d9bb49accccf8d9b4c0cc17a4de406af253e999102533c"),
    FilePin("research/arithmetic-library/working/prime-field-gcd-existence-v1/prime_field_polynomial_gcd_existence_candidate.py", 26480, "81f2f48dd2e81894c7a267453646eb6f2b6f9bd3ee320386d8c561f6b9f8b8ca"),
    FilePin("research/arithmetic-library/working/prime-field-gcd-uniqueness-v1/prime_field_polynomial_gcd_uniqueness_candidate.py", 31432, "916c24ad6c59609612e97daee6e49347a9522cdb28b44f6f09c6c5760bff0b5b"),
)
FROZEN_TEST_PINS = (
    FilePin("research/arithmetic-library/working/prime-field-gcd-bezout-laws-v1/test_prime_field_polynomial_gcd_bezout_laws_candidate.py", 20903, "21da40c3b70a9eb3436b681cfdfd99a2278786dea73b4e5bfdfdefaccdd1b7e0"),
    FilePin("research/arithmetic-library/working/prime-field-gcd-existence-v1/test_prime_field_polynomial_gcd_existence_candidate.py", 15017, "f42c8387e3e84d73eadc0f3eb96e1be1207d2a29fff1f5b2dabd7f60c554ddba"),
    FilePin("research/arithmetic-library/working/prime-field-gcd-uniqueness-v1/test_prime_field_polynomial_gcd_uniqueness_candidate.py", 21350, "6deba14cd0c750c5158c130c8e03f2402861769211605d42d5b61c7bd6936edd"),
)
SPECS_SHA256 = "72701944f71e8d93c55bcf29d27fc92ac616452801ab75c3e478df4d77df4c38"
NAMES_SHA256 = "51f959e944c81af1f430aebed63f10934f50f67fdae6934048551ce7bbf81ef5"
COMPONENT_SPECS = (("laws", 4, "cbf875f3e7d13394f062e4f5f4349beba59a2ac363a599e7b02649906ea6d6a2"), ("existence", 9, "d0bfe3e77e26b0e97c3b20bdd3f6256064c2b34ff56a48039e04f9dbdfcc5d7e"), ("uniqueness", 11, "4bea19123a71314f8d2bf07019377497f56990b31f71a51de861f2b9339a1db3"),)
PHASES = (99, 101, 102, 103, 104, 105, 108, 111, 112, 119,)
STAGE_RECORDS = (
    (99, 443, 1390, 18),
    (101, 446, 1399, 20),
    (102, 447, 1404, 18),
    (103, 448, 1409, 18),
    (104, 449, 1411, 17),
    (105, 463, 1458, 13),
    (108, 466, 1463, 12),
    (111, 472, 1479, 14),
    (112, 484, 1536, 13),
    (119, 492, 1565, 13),
)
SEED_PINS = (PRIOR95_SEED,
    FilePin("research/arithmetic-library/artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json", 1060637, "fec8cf768ef2b94430d58d947daa0affada315bbc5160a03991dc4d2550dd0e9"),
    FilePin("research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json", 2449379, "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf"),
    FilePin("research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json", 745307, "55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3"),
)
STAGE_SEEDS = (
    (99, ("research/arithmetic-library/working/prime-field-euclidean-closure-v1/artifacts/working-euclidean-closure-prefix-95-proof-bundle-v1.json", "research/arithmetic-library/artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json",)),
    (101, ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-99-proof-bundle-v1.json", "research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json",)),
    (102, ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-101-proof-bundle-v1.json",)),
    (103, ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-102-proof-bundle-v1.json",)),
    (104, ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-103-proof-bundle-v1.json",)),
    (105, ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-104-proof-bundle-v1.json", "research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json",)),
    (108, ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-105-proof-bundle-v1.json",)),
    (111, ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-108-proof-bundle-v1.json", "research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json",)),
    (112, ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-111-proof-bundle-v1.json", "research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json", "research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json",)),
    (119, ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-112-proof-bundle-v1.json", "research/arithmetic-library/artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json",)),
)
PRINCIPAL_ROOTS = (
    "prime_field_polynomial_convolution_shift_right_exists",
    "prime_field_polynomial_convolution_right_scale_exists",
    "prime_field_polynomial_convolution_right_scale_zero",
    "prime_field_convolution_coefficient_right_append_add",
    "prime_field_polynomial_convolution_right_append_exists",
    "prime_field_polynomial_right_divides_dividend_bounded",
    "prime_field_polynomial_right_divides_reflexive",
    "prime_field_polynomial_aligned_subtract_from_fixed",
    "prime_field_polynomial_aligned_subtract_functional",
    "prime_field_polynomial_left_constant_product_to_scale",
    "prime_field_polynomial_division_constant_remainder_empty",
    "prime_field_polynomial_normalized_gcd_bezout_exists",
    "prime_field_polynomial_normalized_gcd_equivalent_unique",
    "prime_field_polynomial_bezout_is_right_gcd",
)
PRINCIPAL_STATEMENT_SHA256 = (
    "0fc173b813282a7111d604245b1706a4c01c5bcf566812151810e9afe38f065d",
    "5d0349367decc3084471726b73a77617d49f484cf31191bb78effbc434167156",
    "fd6d04fd88ff9f594f7ee27de04486c1932ce5de30b6030b6b9b18cb547511ef",
    "a11e1f29b31ae9076959706b6b5d0813689194a2ab57a1a4e879e6a6c3ad69bd",
    "0ef69b8524dd48c1a9805f158e9eff25c41e421b85378b96b51b7c63bd89f087",
    "a1f28266b77ee02c24747cf96ca7234d9d13bc3c46d38b2bb6b2f805c1538278",
    "d8f3531eb2f6d2fb37e8ee936807a66a7dc1e49b71c95c7c7023c7964fc03852",
    "3122386d4be93f7e4bca06128ec30ae0e3334dd046f69bb995b602499ae49804",
    "1025f30027f56856f3370a9d951e7ed68e7b83c785a30164ee5a868824667813",
    "c93e29c84d993f933394eb2fc82600d8f3d88f50a06a25ee9d6dc69e6b2141fe",
    "ac7f30f0841995aa9fe25e0546803c6bcf4aab7c09fa337a4c61eafa6f196a9b",
    "d97cbfa3dc334fa5bcf7b9bd92bde2e117b29595864a9cddb093ffe842832463",
    "302df17d7792e85eb95dc25ff3b82ef61c84f67da66a886c1ef383f1115ef7a7",
    "91a89630be8631cd892a7e0dd57bc4a36c2f3a3b734b16f12390124493a0ab43",
)
FINAL_MAXIMAL_ROOTS = PRINCIPAL_ROOTS[:-1]
_REGISTERED_IDENTITIES = (FROZEN_SOURCE_PINS, FROZEN_TEST_PINS, SPECS_SHA256, NAMES_SHA256,
    COMPONENT_SPECS, PHASES, STAGE_RECORDS, STAGE_SEEDS, SEED_PINS,
    PRINCIPAL_ROOTS, PRINCIPAL_STATEMENT_SHA256, FINAL_MAXIMAL_ROOTS)
ARTIFACT_DIRECTORY = HERE / 'artifacts'
OUTPUT_PREFIX = 'working-gcd-closure-prefix-'
CONTROL_FILES = ('working_gcd_closure_support.py', 'export_working_gcd_closure.py',
                 'check_working_gcd_closure.py', 'test_working_gcd_closure.py',
                 'working-gcd-closure-rfc-v1.md')
_CONTROL_NAMES = CONTROL_FILES


def preserve_prior():
    _require(tuple(asdict(pin) for pin in PRIOR_AUTHORITY_PINS) == _PRIOR_RECORDS,
             'the six prior95 authority identities changed')
    for pin in PRIOR_AUTHORITY_PINS:
        check_pin(pin, ROOT, MAX_BYTES)
    state = prior.load_candidate_state()
    _require(prior.state_binding(state, final=True) == PRIOR_FINAL_BINDING,
             'the actual prior95 final source binding changed')
    return state


def snapshot_source(path):
    raw = bounded_bytes(path, MAX_SOURCE_BYTES)
    pin = FilePin(path.relative_to(ROOT).as_posix(), len(raw), sha256(raw).hexdigest())
    check_pin(pin, ROOT, MAX_SOURCE_BYTES)
    return pin, raw


@dataclass(frozen=True, slots=True)
class CandidateState:
    rows: tuple[TheoremSpec, ...]
    specs_sha256: str
    source_pins: tuple[FilePin, ...]
    families: tuple[str, ...]


def load_candidate_state(families=None):
    """Read exact current bytes before executing; recheck after construction."""
    _require(FAMILIES == _FAMILY_IDENTITIES, 'source family ownership changed')
    labels = tuple(item[0] for item in FAMILIES)
    if families is None:
        families = labels
    _require(type(families) is tuple and bool(families) and len(set(families)) == len(families)
             and set(families) <= set(labels), 'unknown or repeated source family')
    prior_state = preserve_prior()
    owners = prior._edition_bindings()
    inputs = []
    for label, directory, short in FAMILIES:
        if label in families:
            path = HERE.parent / directory / (short + '.py')
            pin, raw = snapshot_source(path)
            if FROZEN_SOURCE_PINS is not None:
                _require(pin == FROZEN_SOURCE_PINS[labels.index(label)],
                         'registered mathematical bytes differ before execution')
            inputs.append((label, short, path, pin, raw))
    rows = list(prior_state.rows)
    for label, short, path, pin, raw in inputs:
        alias = '_working_gcd_closure_candidate_' + label
        _require(alias not in sys.modules, 'private mathematical source name is owned')
        module = ModuleType(alias)
        module.__file__, module.__package__ = str(path), ''
        exec(compile(raw, str(path), 'exec'), module.__dict__)
        factory = getattr(module, 'make_' + short + '_theorems', None)
        _require(callable(factory) and factory.__module__ == alias, 'missing or foreign candidate factory')
        values = factory(TheoremSpec)
        _require(type(values) is tuple and all(type(row) is TheoremSpec for row in values),
                 'candidate factory must supply exact specification objects')
        rows.extend(values)
        _require(alias not in sys.modules, 'candidate source installed a private module alias')
    for _, _, _, pin, raw in inputs:
        _require(read_pin(pin, MAX_SOURCE_BYTES) == raw, 'candidate changed during source construction')
    after = prior._edition_bindings()
    _require(owners.keys() == after.keys() and all(after[k] is v for k, v in owners.items()),
             'source-only construction imported or replaced an Alpha edition')
    result = CandidateState(tuple(rows), closure._specs_digest(tuple(rows)),
                            tuple(item[3] for item in inputs), families)
    validate_state(result)
    return result


def validate_state(state):
    _require(type(state) is CandidateState and type(state.rows) is tuple
             and all(type(row) is TheoremSpec for row in state.rows)
             and state.specs_sha256 == closure._specs_digest(state.rows), 'altered candidate snapshot')
    _require(len(state.rows) > 95 and len({r.name for r in state.rows}) == len(state.rows),
             'new candidates are missing or duplicate an old theorem')
    _require(closure._specs_digest(state.rows[:95]) == prior.SPECS_SHA256,
             'the literal prior95 ordered specification prefix changed')
    closure._validate_frontier(state.rows)
    for pin in state.source_pins:
        check_pin(pin, ROOT, MAX_SOURCE_BYTES)


def canonical_provider_table():
    # No source scan or accepting provider fallback is added. Missing source
    # names are reported by planning and need a separately reviewed exact pin.
    return prior.canonical_provider_table()


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
        if name in {r.name for r in self.owned[:95]}:
            return 'prior_non_admitted_euclidean'
        if name in {r.name for r in self.owned[95:]}:
            return 'new_non_admitted_gcd'
        if name in {r.name for r in self.support}:
            return 'inherited_canonical_source'
        raise WorkingError('name outside this exact source cone')


def select_support(state, owned_names=None):
    validate_state(state)
    all_owned = {row.name: row for row in state.rows}
    if owned_names is None:
        owned_names = tuple(all_owned)
    _require(type(owned_names) is tuple and len(owned_names) > 95
             and owned_names == tuple(all_owned)[:len(owned_names)], 'expected an exact source prefix')
    canonical_table = canonical_provider_table()
    _require(not canonical_table.keys() & all_owned.keys(), 'candidate shadows a canonical theorem')
    table = canonical_table | all_owned
    ordered, seen, active = [], set(), set()

    def visit(name):
        _require(name in table, 'missing actual source prerequisite: ' + name)
        _require(name not in active, 'cyclic actual source prerequisite: ' + name)
        if name in seen:
            return
        row = table[name]
        _require(type(row.dependencies) is tuple and len(set(row.dependencies)) == len(row.dependencies),
                 'ordered premise list repeats a name')
        active.add(name)
        for dependency in row.dependencies:
            visit(dependency)
        active.remove(name)
        seen.add(name)
        ordered.append(row)

    for name in owned_names:
        visit(name)
    _require((seen & all_owned.keys()) == set(owned_names), 'prefix uses a future unselected working row')
    used = {name for row in ordered for name in row.dependencies}
    roots = tuple(name for name in owned_names if name not in used)
    _require(len(ordered) + 1 <= closure.DEFAULT_BUNDLE_LIMITS.max_nodes
             and sum(len(r.dependencies) for r in ordered) + len(roots) <= closure.DEFAULT_BUNDLE_LIMITS.max_edges,
             'the unchanged bundle node/edge limits would be exceeded')
    return SourceSelection(tuple(all_owned[n] for n in owned_names),
        tuple(r for r in ordered if r.name in canonical_table), tuple(ordered), roots, len(owned_names))


def require_registration():
    actual = (FROZEN_SOURCE_PINS, FROZEN_TEST_PINS, SPECS_SHA256, NAMES_SHA256,
        COMPONENT_SPECS, PHASES, STAGE_RECORDS, STAGE_SEEDS, SEED_PINS,
        PRINCIPAL_ROOTS, PRINCIPAL_STATEMENT_SHA256, FINAL_MAXIMAL_ROOTS)
    _require(actual == _REGISTERED_IDENTITIES,
             'literal source/stage/seed/root registration changed')
    _require(type(FROZEN_SOURCE_PINS) is tuple and bool(FROZEN_SOURCE_PINS)
             and type(FROZEN_TEST_PINS) is tuple and bool(FROZEN_TEST_PINS)
             and _digest(SPECS_SHA256) and type(PHASES) is tuple and bool(PHASES)
             and type(STAGE_RECORDS) is tuple and len(STAGE_RECORDS) == len(PHASES)
             and tuple(r[0] for r in STAGE_RECORDS) == PHASES
             and type(STAGE_SEEDS) is tuple and tuple(r[0] for r in STAGE_SEEDS) == PHASES
             and bool(PRINCIPAL_ROOTS) and len(PRINCIPAL_ROOTS) == len(PRINCIPAL_STATEMENT_SHA256),
             'gcd source/test/stage/root freeze is not registered; planning and conditional diagnostics only')


def require_frozen(state=None):
    require_registration()
    if state is None:
        state = load_candidate_state()
    validate_state(state)
    _require(state.families == tuple(x[0] for x in FAMILIES)
             and state.source_pins == FROZEN_SOURCE_PINS and state.specs_sha256 == SPECS_SHA256
             and len(state.rows) == PHASES[-1], 'frozen source specifications differ')
    for pin in (*FROZEN_SOURCE_PINS, *FROZEN_TEST_PINS):
        _require(type(pin) is FilePin, 'freeze requires exact source/test file pins')
        check_pin(pin, ROOT, MAX_SOURCE_BYTES)
    selected = select_support(state)
    _require((len(state.rows), sum(len(r.dependencies) for r in state.rows),
              sum(len(r.script) for r in state.rows), len(selected.support),
              len(selected.complete_specs), sum(len(r.dependencies) for r in selected.complete_specs))
             == (119, 543, 12211, 373, 492, 1565), 'frozen inventory differs')
    _require(sha256('\n'.join(r.name for r in state.rows).encode()).hexdigest() == NAMES_SHA256,
             'ordered theorem names differ')
    offset = 95
    for label, count, digest in COMPONENT_SPECS:
        _require(closure._specs_digest(state.rows[offset:offset + count]) == digest,
                 'registered component specification differs: ' + label)
        offset += count
    _require(selected.root_names == FINAL_MAXIMAL_ROOTS
             and set(FINAL_MAXIMAL_ROOTS) <= set(PRINCIPAL_ROOTS)
             and tuple(sha256(next(r.statement for r in state.rows if r.name == name).encode()).hexdigest()
                       for name in PRINCIPAL_ROOTS) == PRINCIPAL_STATEMENT_SHA256,
             'final ordinary root identities changed')
    return state


def final_through():
    require_registration()
    return PHASES[-1]


def stage_metrics(through):
    require_registration()
    _require(type(through) is int and through in PHASES, 'unregistered authoring stage')
    return next(row[1:] for row in STAGE_RECORDS if row[0] == through)


def previous_through(through):
    stage_metrics(through)
    index = PHASES.index(through)
    return 95 if index == 0 else PHASES[index - 1]


def stage_path(through):
    stage_metrics(through)
    return ARTIFACT_DIRECTORY / (OUTPUT_PREFIX + str(through) + '-proof-bundle-v1.json')


@dataclass(frozen=True, slots=True)
class ExecutionSelection:
    source: SourceSelection
    frontier: tuple[TheoremSpec, ...]
    plan: closure.BottomLayerPlan


def execution_selection(state, owned_names=None):
    """Only scheduled proof workers invoke the unchanged original assembler."""
    require_frozen(state)
    selected = select_support(state, owned_names)
    count, edges, roots = stage_metrics(selected.through)
    _require((len(selected.complete_specs), sum(len(r.dependencies) for r in selected.complete_specs),
              len(selected.root_names)) == (count, edges, roots), 'frozen stage cone differs')
    parent = {r.name: r for r in closure.parent_snapshot().specs}
    for row in selected.complete_specs:
        _require(row.name not in parent or row == parent[row.name], 'original v30 parent differs')
    frontier = tuple(r for r in selected.complete_specs if r.name not in parent)
    plan = closure.bottom_layer_plan(frontier)
    complete = {r.name: r for r in selected.complete_specs}
    _require(set(complete) == {r.name for r in plan.rows} and plan.root_names == selected.root_names,
             'original assembler differs from source cone')
    for row in plan.rows:
        exact = complete[row.name]
        _require(row.dependencies == exact.dependencies
                 and row.statement_sha256 == sha256(exact.statement.encode()).hexdigest(),
                 'original assembler target or ordered premises differ')
    return ExecutionSelection(selected, frontier, plan)


def required_seed_paths(through):
    stage_metrics(through)
    return tuple(ROOT / path for stage, paths in STAGE_SEEDS if stage == through for path in paths)


def seed_inventory(paths, *, through):
    expected = required_seed_paths(through)
    _require(type(paths) is tuple and tuple(Path(p).absolute() for p in paths) == expected
             and expected and all('..' not in p.parts for p in expected), 'wrong explicit stage seeds')
    _require(tuple(Path(p).absolute() for p in closure._validate_seeds(paths)) == expected,
             'original seed path validation differs')
    known = {ROOT / pin.path: pin for pin in SEED_PINS}
    output = []
    for path in expected:
        if path in known:
            pin = known[path]
            read_pin(pin)
        else:
            _require(previous_through(through) != 95 and path == stage_path(previous_through(through)),
                     'only exact canonical seeds or the immediately preceding stage are permitted')
            info = path.lstat()
            _require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1,
                     'previous stage is not an owned ordinary file')
            raw = bounded_bytes(path, MAX_BYTES)
            pin = FilePin(path.relative_to(ROOT).as_posix(), len(raw), sha256(raw).hexdigest())
            value = prior._inert_bundle_metadata(raw)
            nodes, edges, roots = stage_metrics(previous_through(through))
            _require(len(value[3]) == nodes + 1 and value[1] == nodes
                     and sum(len(n[2]) for n in value[3]) == edges + roots, 'previous stage inventory differs')
        output.append(pin)
    return tuple(output)


def inert_coverage(selected, pins, *, previous_count=95):
    """Source-only exact targets and ordered premises, never decoded proofs."""
    from peano_lab.library.proof_bundle import encode_formula
    from peano_lab.library.theorems import _closed_formula
    _require(type(selected) is SourceSelection and type(pins) is tuple
             and all(type(pin) is FilePin for pin in pins), 'exact selection and file pins required')
    table = {r.name: r for r in selected.complete_specs}
    targets = {name: canonical(encode_formula(_closed_formula(row.statement))) for name, row in table.items()}
    fresh = {r.name for r in selected.owned[previous_count:]}
    wanted = set(table) - fresh
    index = {}
    for name in wanted:
        index.setdefault(targets[name], []).append(name)
    matched, records = set(), []
    for pin in pins:
        value = prior._inert_bundle_metadata(read_pin(pin))
        nodes = value[3]
        encoded = tuple(canonical(node[1]) for node in nodes)
        covered = set()
        for position, node in enumerate(nodes):
            for name in index.get(encoded[position], ()):
                if tuple(encoded[i] for i in node[2]) == tuple(targets[d] for d in table[name].dependencies):
                    covered.add(name)
        records.append({**asdict(pin), 'inert_nodes': len(nodes), 'covered_targets': len(covered),
                        'newly_covered_names': sorted(covered - matched)})
        matched.update(covered)
        check_pin(pin, ROOT, MAX_BYTES)
    return dict(preexisting_targets=len(wanted), covered_targets=len(matched),
        missing_names=sorted(wanted - matched), seeds=records, raw_json_only=True,
        proof_bodies_decoded=False, original_ha_checked=False, proof_authority=False)


def seed_coverage(selected, pins):
    state = require_frozen()
    _require(selected == select_support(state, tuple(row.name for row in selected.owned)),
             'seed coverage received an altered frozen source selection')
    _require(tuple(ROOT / pin.path for pin in pins) == required_seed_paths(selected.through),
             'wrong stage seed inventory')
    return inert_coverage(selected, pins, previous_count=previous_through(selected.through))


def state_binding(state, *, final=False):
    _require(type(final) is bool, 'final must be a literal Boolean')
    require_frozen(state)
    preserve_prior()
    _require(CONTROL_FILES == _CONTROL_NAMES, 'new control inventory changed')
    if final:
        require_parent_registration()
    for pin in SEED_PINS:
        check_pin(pin, ROOT, MAX_BYTES)
    controls = [asdict(snapshot_source(HERE / name)[0]) for name in CONTROL_FILES]
    return sha256(canonical(dict(controls=controls, prior95_binding=PRIOR_FINAL_BINDING,
        prior95_authority_files=_PRIOR_RECORDS, sources=[asdict(p) for p in state.source_pins],
        tests=[asdict(p) for p in FROZEN_TEST_PINS], specs_sha256=state.specs_sha256,
        stages=STAGE_RECORDS, stage_seeds=STAGE_SEEDS, seeds=[asdict(p) for p in SEED_PINS],
        ordinary_roots=list(zip(PRINCIPAL_ROOTS, PRINCIPAL_STATEMENT_SHA256)),
        final_registration_required=final, stored_observations_supply_authority=False))).hexdigest()


def local_manifest():
    state = load_candidate_state()
    selected = select_support(state)
    old = prior.select_support(prior.load_candidate_state())
    coverage = inert_coverage(selected, (PRIOR95_SEED,))
    return dict(schema='working-gcd-prospective-source-plan-v1', syntax_only=True,
        previous_working_rows=95, new_working_rows=len(state.rows)-95,
        source_pins=[asdict(p) for p in state.source_pins], specs_sha256=state.specs_sha256,
        theorem_nodes=len(selected.complete_specs), theorem_edges=sum(len(r.dependencies) for r in selected.complete_specs),
        package_nodes=len(selected.complete_specs)+1,
        package_edges=sum(len(r.dependencies) for r in selected.complete_specs)+len(selected.root_names),
        maximal_roots=selected.root_names,
        additional_canonical_names=sorted({r.name for r in selected.support}-{r.name for r in old.support}),
        actual95_inert_coverage=coverage, source_freeze_registered=FROZEN_SOURCE_PINS is not None,
        original_ha_checked=False, independent_lean_checked=False, ordinary_roots_checked=False,
        alpha_admission_performed=False, full_G091_proved=False)
