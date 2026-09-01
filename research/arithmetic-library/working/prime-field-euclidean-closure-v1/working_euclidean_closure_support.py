"""Exact source-only planning for the separate non-admitted52+43 Euclidean cone.

Six prior52 authority files and their unchanged transitive archives are pinned.
Authoring uses only the actual previous stage and its literal canonical seeds;
every whole seed is checked anew by the original assembler. No saved report is
proof authority. Only the separate novelty task parses current Alpha4092.
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
WORKING_RELATIVE = "research/arithmetic-library/working/prime-field-euclidean-closure-v1"
if HERE != ROOT / WORKING_RELATIVE or not (ROOT / "peano-lab/py/peano_lab").is_dir():
    raise RuntimeError("the Euclidean closure belongs only in its new working directory")
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import constructive_g009_support as inherited

FilePin = inherited.FilePin
PRIOR52_RELATIVE = "research/arithmetic-library/working/prime-field-left-unit-closure-v1"
PRIOR52_SUPPORT_PIN = FilePin(
    PRIOR52_RELATIVE + "/working_left_unit_closure_support.py", 31719,
    "e1374a8d87915bfd72349b675953e5396043704ddb847e435445cc0451e44fc8")
_PRIVATE_PRIOR_NAME = "_working_euclidean_closure_v1_prior52"


def _load_prior_support():
    """Dataclasses need a temporary private controller name, never a peano alias."""
    if _PRIVATE_PRIOR_NAME in sys.modules:
        raise ValueError("the private prior-controller name is already owned")
    pin = PRIOR52_SUPPORT_PIN
    inherited.check_pin(pin, ROOT, inherited.MAX_SOURCE_BYTES)
    path = ROOT / pin.path
    raw = inherited.bounded_bytes(path, inherited.MAX_SOURCE_BYTES)
    if (len(raw), sha256(raw).hexdigest()) != (pin.bytes, pin.sha256):
        raise ValueError("the pinned prior52 controller changed before loading")
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
EXPECTED_COUNT, EXPECTED_INHERITED_COUNT = 95, 343
SPECS_SHA256 = "b2b381d67064401d3325b464396c6d156b5fc27a56639f3909dacaa60ae83994"
NAMES_SHA256 = "264f9aaa740b58d792fc3be4890cc292b25500d7475ac7fff78fc910c6cbe54f"
ARTIFACT_DIRECTORY = HERE / "artifacts"
OUTPUT_PREFIX = "working-euclidean-closure-prefix-"
PHASES = (59, 68, 72, 74, 76, 82, 87, 92, 93, 94, 95,)
# through, theorem nodes, theorem edges, maximal roots; packager is additional.
STAGE_RECORDS = (
    (59, 312, 886, 17),
    (68, 324, 917, 17),
    (72, 341, 989, 18),
    (74, 353, 1022, 19),
    (76, 372, 1109, 21),
    (82, 378, 1141, 23),
    (87, 430, 1316, 21),
    (92, 435, 1348, 17),
    (93, 436, 1359, 15),
    (94, 437, 1366, 15),
    (95, 438, 1368, 15),
)
PREVIOUS_THROUGH = {59: 52, 68: 59, 72: 68, 74: 72, 76: 74, 82: 76, 87: 82, 92: 87, 93: 92, 94: 93, 95: 94}
CONTROL_FILES = (
    "working_euclidean_closure_support.py", "export_working_euclidean_closure.py",
    "check_working_euclidean_closure.py", "test_working_euclidean_closure.py",
    "working-euclidean-closure-rfc-v1.md",
)
_CONTROL_NAMES = CONTROL_FILES
PRINCIPAL_ROOTS = (
    "prime_field_polynomial_convolution_shift_right_exists",
    "prime_field_polynomial_convolution_right_scale_exists",
    "prime_field_polynomial_convolution_right_scale_zero",
    "prime_field_convolution_coefficient_right_append_add",
    "prime_field_polynomial_convolution_right_append_exists",
    "prime_field_polynomial_right_divides_divisor_bounded",
    "prime_field_polynomial_right_divides_dividend_bounded",
    "prime_field_polynomial_right_divides_reflexive",
    "prime_field_polynomial_aligned_subtract_from_fixed",
    "prime_field_polynomial_aligned_subtract_functional",
    "prime_field_polynomial_left_constant_product_to_scale",
    "prime_field_polynomial_division_constant_remainder_empty",
    "prime_field_polynomial_normalized_right_associate_exists",
    "prime_field_polynomial_division_execution_common_right_divisors",
    "prime_field_polynomial_division_execution_bezout_backward",
)
PRINCIPAL_STATEMENT_SHA256 = (
    "0fc173b813282a7111d604245b1706a4c01c5bcf566812151810e9afe38f065d",
    "5d0349367decc3084471726b73a77617d49f484cf31191bb78effbc434167156",
    "fd6d04fd88ff9f594f7ee27de04486c1932ce5de30b6030b6b9b18cb547511ef",
    "a11e1f29b31ae9076959706b6b5d0813689194a2ab57a1a4e879e6a6c3ad69bd",
    "0ef69b8524dd48c1a9805f158e9eff25c41e421b85378b96b51b7c63bd89f087",
    "544318213b2b7d1697a9d395876f8de05096b5f5d66464fcf35d0607b2766f8d",
    "a1f28266b77ee02c24747cf96ca7234d9d13bc3c46d38b2bb6b2f805c1538278",
    "d8f3531eb2f6d2fb37e8ee936807a66a7dc1e49b71c95c7c7023c7964fc03852",
    "3122386d4be93f7e4bca06128ec30ae0e3334dd046f69bb995b602499ae49804",
    "1025f30027f56856f3370a9d951e7ed68e7b83c785a30164ee5a868824667813",
    "c93e29c84d993f933394eb2fc82600d8f3d88f50a06a25ee9d6dc69e6b2141fe",
    "ac7f30f0841995aa9fe25e0546803c6bcf4aab7c09fa337a4c61eafa6f196a9b",
    "21d68a815be43fce3458f0b51fa22b3080e0f67ae51702d3bb09a7e9a7a6711c",
    "78ca6741f3988aa03e63edc2bf14ce1f50e0882f0a38f2004f231df9efac31f3",
    "0308b3b63fea32baa1eb473222ffa0dd93c119908c6c324191e08969d0d7b76c",
)

# Precisely five prior52 controls and its real final artifact, not its README,
# observations, or notation. Full-tree non-mutation is observed independently.
PROTECTED_PRIOR52_PINS = (
    FilePin("research/arithmetic-library/working/prime-field-left-unit-closure-v1/working_left_unit_closure_support.py", 31719, "e1374a8d87915bfd72349b675953e5396043704ddb847e435445cc0451e44fc8"),
    FilePin("research/arithmetic-library/working/prime-field-left-unit-closure-v1/export_working_left_unit_closure.py", 9099, "7e77bfe907ff4804456c62c6bf4076e8939c53e929d6f80dab77d2a3c68fe6df"),
    FilePin("research/arithmetic-library/working/prime-field-left-unit-closure-v1/check_working_left_unit_closure.py", 12577, "72453c57fc4e138927cb4daeb955bcc0c7292880883c9f496fabe7dc230d9d1b"),
    FilePin("research/arithmetic-library/working/prime-field-left-unit-closure-v1/test_working_left_unit_closure.py", 53367, "b22b344f95d50fb4cc3305de2529dfead84d1d69870b7f2ac9085c366d9eaeb0"),
    FilePin("research/arithmetic-library/working/prime-field-left-unit-closure-v1/working-left-unit-closure-rfc-v1.md", 13331, "9ba37f4f1e1d1dc0a0958a917ec38e6b3c1a8951cc8d77876dcf1da0e17297ba"),
    FilePin("research/arithmetic-library/working/prime-field-left-unit-closure-v1/artifacts/working-left-unit-closure-prefix-52-proof-bundle-v1.json", 1837245, "4051c93175faed973fb3b88d963fdd03f15514e481aab9516d56b7b1e67c44c4"),
)
_PRIOR52_RECORDS = tuple((pin.path, pin.bytes, pin.sha256) for pin in PROTECTED_PRIOR52_PINS)


@dataclass(frozen=True, slots=True)
class AdditionalFactory:
    directory: str
    module: str
    count: int
    source_bytes: int
    source_sha256: str
    tests: tuple[FilePin, ...]
    specs_sha256: str

    @property
    def source(self):
        return FilePin(self.directory + "/" + self.module + ".py", self.source_bytes, self.source_sha256)

    @property
    def factory(self):
        return "make_" + self.module + "_theorems"


# The shared proof-free transport/Bezout model test is an explicit test input,
# not an invented sibling filename or a provider of mathematical hypotheses.
ADDITIONAL_FACTORIES = (
    AdditionalFactory("research/arithmetic-library/working/prime-field-alignment-v1",
        "prime_field_polynomial_alignment_candidate", 7, 11780,
        "eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e",
        (FilePin("research/arithmetic-library/working/prime-field-alignment-v1/test_prime_field_polynomial_alignment_candidate.py", 30676, "6adbed23a43a393a4988d6eba9323cb09a8777b62b644cb1992ebdf7c6411c8b"),),
        "76b9c342744170146fcb7898cb5a20154334147578b7e01d059f01b9015d5aec"),
    AdditionalFactory("research/arithmetic-library/working/prime-field-aligned-add-v1",
        "prime_field_polynomial_aligned_add_candidate", 9, 20704,
        "a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db",
        (FilePin("research/arithmetic-library/working/prime-field-aligned-add-v1/test_prime_field_polynomial_aligned_add_candidate.py", 33347, "6e67b246e1c565e44d721ad92ecb2e273c2e1330d226922af89f762630de2ed8"),),
        "b8ce285a000180baef6318db67202fc4fa258ae5bd6aabecfc098236f9588339"),
    AdditionalFactory("research/arithmetic-library/working/prime-field-aligned-algebra-v1",
        "prime_field_polynomial_aligned_algebra_candidate", 4, 16013,
        "a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390",
        (FilePin("research/arithmetic-library/working/prime-field-aligned-algebra-v1/test_prime_field_polynomial_aligned_algebra_candidate.py", 10321, "11f096addd3afb6301e98d61cf359b833754b29eebd7abf61a9e85b3da06d073"),
         FilePin("research/arithmetic-library/working/prime-field-aligned-algebra-v1/test_prime_field_polynomial_aligned_algebra_contracts.py", 12694, "09c34419021d60ad8c78ea5b0430bc17a595fb2b3d97469e1e375a5f55697b2d"),),
        "0db1ddc08762db5e207469343143a7ead24de983e8f9a21473592a8d6c97d6f4"),
    AdditionalFactory("research/arithmetic-library/working/prime-field-euclidean-identity-v1",
        "prime_field_polynomial_euclidean_identity_candidate", 2, 11235,
        "8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77",
        (FilePin("research/arithmetic-library/working/prime-field-euclidean-identity-v1/test_prime_field_polynomial_euclidean_identity_candidate.py", 31004, "e7225749330ccd9392e584196057ab3a2547856764d25296bee775f9eb62e2c0"),),
        "f992bc15fd84b7f3ba9b0f28c0219cb97a53c47c669a9563b087e7a3c535ab27"),
    AdditionalFactory("research/arithmetic-library/working/prime-field-aligned-distributivity-v1",
        "prime_field_polynomial_aligned_distributivity_candidate", 2, 8518,
        "7d535939e24fe6d82158c485533b2ff6934f4d897b6141fde6c50b4fec9788ba",
        (FilePin("research/arithmetic-library/working/prime-field-aligned-distributivity-v1/test_prime_field_polynomial_aligned_distributivity_candidate.py", 22358, "5fa4ff32894dcbe7f2010ae526731e88cbe4c2307e1043b56da326c487c26039"),),
        "22b9e7ed76b79f0210eee74433a965db62cc5a4b688c3ab2cf0f236b1dca5719"),
    AdditionalFactory("research/arithmetic-library/working/prime-field-left-constant-v1",
        "prime_field_polynomial_left_constant_candidate", 6, 17620,
        "9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a",
        (FilePin("research/arithmetic-library/working/prime-field-left-constant-v1/test_prime_field_polynomial_left_constant_candidate.py", 27847, "cc93a6d0b8d1ff3eae9bc0b16527936301a7a15e13e7baae3cf818a919cc6a60"),),
        "736cd0d7d21f33ac50a189f66a7457909042c83917d9e9cfc2d4932c6fe06836"),
    AdditionalFactory("research/arithmetic-library/working/prime-field-euclidean-normalization-v1",
        "prime_field_polynomial_euclidean_normalization_candidate", 5, 16401,
        "d2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f",
        (FilePin("research/arithmetic-library/working/prime-field-euclidean-normalization-v1/test_prime_field_polynomial_euclidean_normalization_candidate.py", 29037, "e291538321e9d078a8b0044bacfb50d46b5eea59b2126001a2129c69de342791"),),
        "815b67478a8c42bd854002317e31ab5e77739551f19516dfc923b7fe66d0ce74"),
    AdditionalFactory("research/arithmetic-library/working/prime-field-euclidean-transport-v1",
        "prime_field_polynomial_euclidean_transport_candidate", 5, 18256,
        "9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30",
        (FilePin("research/arithmetic-library/working/prime-field-euclidean-transport-v1/test_prime_field_polynomial_transport_models.py", 25634, "0c814915ee8b8f6ecc8ffb945699cd4888fa4c4cf86e6b4cb077063407f5cfab"),),
        "aba201eca067048dc65b5a2f7f6affd415c6ebd639c35bc613503227a65059b8"),
    AdditionalFactory("research/arithmetic-library/working/prime-field-bezout-backward-v1",
        "prime_field_polynomial_bezout_backward_candidate", 3, 18747,
        "c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702",
        (FilePin("research/arithmetic-library/working/prime-field-euclidean-transport-v1/test_prime_field_polynomial_transport_models.py", 25634, "0c814915ee8b8f6ecc8ffb945699cd4888fa4c4cf86e6b4cb077063407f5cfab"),),
        "bbab74ad9d4ecfe3b01e97ab75dccd532fc23e22a5cb275a68963f15dbf57564"),
)
FACTORIES = (*prior.FACTORIES, *ADDITIONAL_FACTORIES)
_FACTORY_RECORDS = tuple(asdict(owner) for owner in FACTORIES)
ADDITIONAL_RUNTIME_PINS = (
    FilePin("peano-lab/py/peano_lab/library/ha_signed_decode_candidate.py", 10802, "98cd745fe7e75ffabc532bbef491b908550e2dcd0f30295944b126f7748409aa"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_division_candidate.py", 47986, "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_monic_candidate.py", 25658, "3bf93aff71b48a332920b1a6174e44167bf78238caac3b6d35634f3591582eef"),
    FilePin("peano-lab/py/peano_lab/library/signed_integer_division_candidate.py", 9708, "f9471954bb5e2bd470ae09c08da4b224839c7a29942816f9cf43c8d48cced384"),
)
RUNTIME_PINS = (*prior.RUNTIME_PINS, *ADDITIONAL_RUNTIME_PINS)
_RUNTIME_RECORDS = tuple((pin.path, pin.bytes, pin.sha256) for pin in RUNTIME_PINS)
_RUNTIME_BY_PATH = {pin.path: pin for pin in RUNTIME_PINS}
# Preserve the exact old nineteen factories, including the singular "law".
PROVIDER_FACTORIES = (*prior.PROVIDER_FACTORIES,
    ("prime_field_polynomial_subtraction_candidate", "make_prime_field_polynomial_subtraction_candidate_theorems"),
    ("prime_field_polynomial_degree_candidate", "make_prime_field_polynomial_degree_candidate_theorems"),
    ("prime_field_polynomial_trim_candidate", "make_prime_field_polynomial_trim_candidate_theorems"),
    ("prime_field_polynomial_division_candidate", "make_prime_field_polynomial_division_candidate_theorems"),
    ("prime_field_polynomial_monic_candidate", "make_prime_field_polynomial_monic_candidate_theorems"),
    ("finite_sum_pointwise_mod_candidate", "make_finite_sum_pointwise_mod_candidate_theorems"),
    ("signed_integer_division_candidate", "make_signed_integer_division_candidate_theorems"),
)
_PROVIDER_FACTORY_RECORDS = PROVIDER_FACTORIES
PROVIDER_MODULES = tuple(name for name, _factory in PROVIDER_FACTORIES)
_PROVIDER_IDENTITIES = PROVIDER_MODULES

PRIOR52_SEED = PROTECTED_PRIOR52_PINS[-1]
CANONICAL121_SEED = FilePin(
    "research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json",
    2449379, "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf")
POLYNOMIAL_SEED = FilePin(
    "research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json",
    688987, "6e3a08c73b8a45de127e6d50a771f95b52fd54894b1c2e43468751421488a01a")
PREREQUISITES85_SEED = FilePin(
    "research/arithmetic-library/artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json",
    1060637, "fec8cf768ef2b94430d58d947daa0affada315bbc5160a03991dc4d2550dd0e9")
SEED_PINS = (PRIOR52_SEED, CANONICAL121_SEED, POLYNOMIAL_SEED, PREREQUISITES85_SEED)
_SEED_IDENTITIES = tuple((pin.path, pin.bytes, pin.sha256) for pin in SEED_PINS)
PARENT_CATALOG_PINS = prior.PARENT_CATALOG_PINS
PARENT_CHANNEL_PIN = prior.PARENT_CHANNEL_PIN
PARENT_IDENTITY_SHA256 = prior.PARENT_IDENTITY_SHA256
PARENT_ENROLLMENT_SHA256 = prior.PARENT_ENROLLMENT_SHA256
_PARENT_RECORDS = (PARENT_CATALOG_PINS, PARENT_CHANNEL_PIN,
                   PARENT_IDENTITY_SHA256, PARENT_ENROLLMENT_SHA256)


def require_preserved_archives():
    prior.require_preserved_archives()
    _require(type(PROTECTED_PRIOR52_PINS) is tuple and len(PROTECTED_PRIOR52_PINS) == 6
             and all(type(pin) is FilePin for pin in PROTECTED_PRIOR52_PINS)
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in PROTECTED_PRIOR52_PINS)
                 == _PRIOR52_RECORDS
             and PROTECTED_PRIOR52_PINS[0] == PRIOR52_SUPPORT_PIN,
             "the six exact prior52 authority-file identities changed")
    for pin in PROTECTED_PRIOR52_PINS:
        check_pin(pin, ROOT, MAX_BYTES)


def require_runtime_sources():
    prior.require_runtime_sources()
    _require(type(RUNTIME_PINS) is tuple and len(RUNTIME_PINS) == len(_RUNTIME_RECORDS) == 116
             and all(type(pin) is FilePin for pin in RUNTIME_PINS)
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in RUNTIME_PINS) == _RUNTIME_RECORDS
             and RUNTIME_PINS == (*prior.RUNTIME_PINS, *ADDITIONAL_RUNTIME_PINS)
             and len(_RUNTIME_BY_PATH) == len(RUNTIME_PINS),
             "the original runtime or four actual additional source identities changed")
    _require(type(PROVIDER_FACTORIES) is tuple and len(PROVIDER_FACTORIES) == 26
             and all(type(pair) is tuple and len(pair) == 2
                     and all(type(value) is str and value for value in pair) for pair in PROVIDER_FACTORIES)
             and PROVIDER_FACTORIES == _PROVIDER_FACTORY_RECORDS
             and PROVIDER_MODULES == _PROVIDER_IDENTITIES
                 == tuple(name for name, _factory in PROVIDER_FACTORIES)
             and PROVIDER_FACTORIES[:19] == prior.PROVIDER_FACTORIES,
             "the twenty-six exact canonical module/factory identities changed")
    for pin in RUNTIME_PINS:
        check_pin(pin, ROOT, MAX_SOURCE_BYTES)


def require_working_sources():
    prior.require_working_sources()
    _require(type(FACTORIES) is tuple and len(FACTORIES) == 17
             and FACTORIES[:8] == prior.FACTORIES
             and type(ADDITIONAL_FACTORIES) is tuple and len(ADDITIONAL_FACTORIES) == 9
             and FACTORIES[8:] == ADDITIONAL_FACTORIES
             and all(type(owner) is AdditionalFactory for owner in ADDITIONAL_FACTORIES)
             and tuple(asdict(owner) for owner in FACTORIES) == _FACTORY_RECORDS
             and tuple(owner.count for owner in FACTORIES) == (15, 10, 6, 1, 3, 2, 7, 8, 7, 9, 4, 2, 2, 6, 5, 5, 3),
             "the exact prior52 plus nine new source ownership records changed")
    for owner in ADDITIONAL_FACTORIES:
        _require(type(owner.tests) is tuple and bool(owner.tests)
                 and all(type(pin) is FilePin for pin in owner.tests),
                 "each additional source needs its exact independent test-file identities")
        read_pin(owner.source, MAX_SOURCE_BYTES)
        for pin in owner.tests:
            read_pin(pin, MAX_SOURCE_BYTES)


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
        alias = "_working_euclidean_closure_v1_" + owner.module
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
             and len(state.rows) == EXPECTED_COUNT == 95
             and all(type(row) is TheoremSpec for row in state.rows)
             and state.specs_sha256 == SPECS_SHA256
             and closure._specs_digest(state.rows) == SPECS_SHA256,
             "an altered or incomplete frozen95 syntax state is not accepted")
    closure._validate_frontier(state.rows)
    _require(sha256("\n".join(row.name for row in state.rows).encode()).hexdigest() == NAMES_SHA256
             and sum(len(row.dependencies) for row in state.rows) == 436
             and sum(len(row.script) for row in state.rows) == 10062,
             "the exact95 names, ordered premises or native command inventory changed")
    table, seen = {row.name: row for row in state.rows}, set()
    for row in state.rows:
        _require((set(row.dependencies) & table.keys()) <= seen,
                 "a new source has a forward or cyclic prerequisite")
        seen.add(row.name)
    _require(len(PRINCIPAL_ROOTS) == 15 and len(set(PRINCIPAL_ROOTS)) == 15
             and tuple(sha256(table[name].statement.encode()).hexdigest()
                       for name in PRINCIPAL_ROOTS if name in table) == PRINCIPAL_STATEMENT_SHA256,
             "one of the fifteen exact ordinary principal statements changed")


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
             and PHASES == (59, 68, 72, 74, 76, 82, 87, 92, 93, 94, 95,)
             and STAGE_RECORDS == (
                 (59, 312, 886, 17),
                 (68, 324, 917, 17),
                 (72, 341, 989, 18),
                 (74, 353, 1022, 19),
                 (76, 372, 1109, 21),
                 (82, 378, 1141, 23),
                 (87, 430, 1316, 21),
                 (92, 435, 1348, 17),
                 (93, 436, 1359, 15),
                 (94, 437, 1366, 15),
                 (95, 438, 1368, 15),
             )
             and PREVIOUS_THROUGH == {59: 52, 68: 59, 72: 68, 74: 72, 76: 74, 82: 76, 87: 82, 92: 87, 93: 92, 94: 93, 95: 94},
             "only the eleven exact source-order authoring stages are authorized")
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
        if name in {row.name for row in self.owned[:52]}:
            return "prior_non_admitted_left_unit"
        if name in {row.name for row in self.owned[52:]}:
            return "new_non_admitted_euclidean_transport"
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
    if through == 95:
        _require(len(selected.support) == EXPECTED_INHERITED_COUNT == 343
                 and selected.root_names == PRINCIPAL_ROOTS,
                 "the complete343+95 source cone or fifteen maximal roots changed")
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
    if through == 59:
        return (ROOT / PRIOR52_SEED.path,)
    previous = stage_path(PREVIOUS_THROUGH[through])
    if through in (68, 72):
        return (previous, ROOT / CANONICAL121_SEED.path, ROOT / POLYNOMIAL_SEED.path)
    if through in (74, 76):
        return (previous, ROOT / CANONICAL121_SEED.path)
    if through == 87:
        return (previous, ROOT / CANONICAL121_SEED.path, ROOT / PREREQUISITES85_SEED.path)
    # In particular, stages93/94/95 reuse only actual92/93/94 respectively.
    return (previous,)


def require_seed_identities():
    _require(type(SEED_PINS) is tuple and len(SEED_PINS) == 4
             and all(type(pin) is FilePin for pin in SEED_PINS)
             and SEED_PINS == (PRIOR52_SEED, CANONICAL121_SEED, POLYNOMIAL_SEED, PREREQUISITES85_SEED)
             and PRIOR52_SEED == PROTECTED_PRIOR52_PINS[-1]
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in SEED_PINS) == _SEED_IDENTITIES,
             "the four literal actual seed identities or their phase roles changed")


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
    coverage = prior.prior.prior.prior.seed_coverage(prior.prior.prior.prior.SupportSelection(
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
    _require(type(CONTROL_FILES) is tuple and CONTROL_FILES == _CONTROL_NAMES
             and len(CONTROL_FILES) == 5,
             "the five exact new proof controls cannot be omitted or replaced by observations")
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
        "prior52_authority_files": _PRIOR52_RECORDS,
        "prior44_authority_files": prior._PRIOR44_RECORDS,
        "prior37_authority_files": prior.prior._PRIOR37_RECORDS,
        "complete_prior52_tree_bound": False, "complete_prior44_tree_bound": False,
        "complete_prior37_tree_bound": False,
        "accepted25_preservation_only": prior.prior.prior._PRIOR25_RECORDS,
        "earlier_archives": prior.prior.prior.prior.PRESERVED_ARCHIVES, "literal_seeds": _SEED_IDENTITIES,
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
        "schema": "peano-working-euclidean-closure-syntax-v1", "syntax_only": True,
        "non_admitted_rows": 95, "previous_non_admitted_rows": 52, "additional_non_admitted_rows": 43,
        "factory_counts": [owner.count for owner in FACTORIES], "specs_sha256": state.specs_sha256,
        "ordered_names": [row.name for row in state.rows],
        "inherited_source_rows": len(selected.support), "complete_source_rows": len(selected.complete_specs),
        "new_dependency_edges": 436, "new_script_commands": 10062,
        "complete_dependency_edges": 1368, "packaged_nodes": 439, "packaged_edges": 1383,
        "maximal_roots": list(selected.root_names), "ordinary_principals": list(PRINCIPAL_ROOTS),
        "phases": [{"through": through, "nodes": nodes + 1, "edges": edges + roots,
                    "required_seeds": [path.relative_to(ROOT).as_posix()
                                       for path in required_seed_paths(through)]}
                   for through, nodes, edges, roots in STAGE_RECORDS],
        "global_current4092_novelty_checked": False, "original_ha_checked": False,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "complete_checkpoint_acceptance": False, "gcd_bezout_proved": False,
        "prior52_authority_file_count": 6, "complete_prior52_tree_bound": False,
        "full_G091_proved": False, "alpha_admission_performed": False, "stable_admission_performed": False,
    }
