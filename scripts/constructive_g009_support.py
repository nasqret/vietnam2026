"""Non-admitting G009 syntax support over exact current Alpha v31.

The unchanged assembler has an immutable v30 base.  Its execution frontier
therefore explicitly includes the needed *already inherited* v31 entries.
This is an additive argument adapter, not a replacement parent, proof-cache
patch, source mutation, or mathematical ownership claim.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if HERE != ROOT / 'scripts' or not (ROOT / 'peano-lab/py/peano_lab').is_dir():
    raise RuntimeError('G009 support must reside in its repository scripts directory')
sys.path[:0] = [str(ROOT / 'peano-lab/py'), str(ROOT / 'scripts')]
MATH_DIRECTORY = ROOT / 'peano-lab/py/peano_lab/library'

from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import TheoremSpec, _closed_formula


class G009Error(ValueError):
    """An exact input, ownership, proof, or original resource gate failed."""


@dataclass(frozen=True, slots=True)
class FilePin:
    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class Factory:
    module: str
    count: int

    @property
    def factory(self):
        return 'make_' + self.module + '_theorems'

    @property
    def path(self):
        return 'peano-lab/py/peano_lab/library/' + self.module + '.py'


FACTORIES = (
    Factory('arithmetic_multiplicative_candidate', 11),
    Factory('coprime_divisor_decomposition_candidate', 8),
    Factory('divisor_pair_index_candidate', 4),
    Factory('signed_block_sum_candidate', 7),
    Factory('signed_cartesian_product_candidate', 20),
    Factory('signed_support_reindex_candidate', 25),
    Factory('dirichlet_multiplicative_entry_candidate', 5),
    Factory('dirichlet_multiplicative_support_candidate', 6),
    Factory('dirichlet_multiplicative_candidate', 4),
)
EXPECTED_NEW_COUNT = 90
PARENT_COUNT = 3796
PARENT_STABLE_COUNT = 432
PARENT_IDENTITY_SHA256 = '902fa75c2bf4624bb7fc5aca9a6c49b71ff8fa4499f8bdf9ce726cfd4166a5d7'
PARENT_ENROLLMENT_SHA256 = 'e4f6330197152cab52427ea724c488390e1cd3bd50a77c09746161cb0d343768'
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_CATALOG_COMPONENT_BYTES = 64 * 1024 * 1024

# Exact adopted source identities, not proof acceptance or admission.
# A live fingerprint, old receipt, or partial prefix cannot replace them.
MATH_SOURCE_PINS: tuple[FilePin, ...] = (
    FilePin("peano-lab/py/peano_lab/library/arithmetic_multiplicative_candidate.py",10836,
            "f4374450ec543f69093b98367c90f67f09ac15daacd1df2f90961d7b6ece4a7e"),
    FilePin("peano-lab/py/peano_lab/library/coprime_divisor_decomposition_candidate.py",14805,
            "de19bb61543f5d7ab3a1d1b675c96ae4b31c7c96b58d6107904e7188973a2e1c"),
    FilePin("peano-lab/py/peano_lab/library/divisor_pair_index_candidate.py",6642,
            "fc6a5a555fdee62cf5f54365163f32c4acfee10b8f416b811bb69debdbcf62a0"),
    FilePin("peano-lab/py/peano_lab/library/signed_block_sum_candidate.py",14390,
            "0597b3806fec32b8eb117f5d0f6be2304c754aa8078df6f50de9dd4d12a2c18f"),
    FilePin("peano-lab/py/peano_lab/library/signed_cartesian_product_candidate.py",33563,
            "d7dbe1d9a82ee5b91e33d6a4624d3e7f05b20d4618045ecab8e753eee6c7e351"),
    FilePin("peano-lab/py/peano_lab/library/signed_support_reindex_candidate.py",44258,
            "db91e38ca5e671adf88e3bf70396b1a242f9c760d6f2c52c4785e6a63316339e"),
    FilePin("peano-lab/py/peano_lab/library/dirichlet_multiplicative_entry_candidate.py",10482,
            "d7f55b8f25e56f8b9c5bc3f6c4b83698d5f1ad770e1e4ed77c53f12a602bd897"),
    FilePin("peano-lab/py/peano_lab/library/dirichlet_multiplicative_support_candidate.py",19151,
            "56e9f8ccaa7c795e42b33984bc2346182ba3a1f820883ba884e571b89091d4a5"),
    FilePin("peano-lab/py/peano_lab/library/dirichlet_multiplicative_candidate.py",9345,
            "bb1342735115781fd8f0107d3876c95098e0b6dc459f31981ffb2c16432eab77"),
)
PARENT_CONTROL_PINS: tuple[FilePin, ...] = (
    FilePin("peano-lab/py/peano_lab/kernel/__init__.py",263,
            "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84"),
    FilePin("peano-lab/py/peano_lab/kernel/checker.py",10021,
            "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe"),
    FilePin("peano-lab/py/peano_lab/kernel/formulas.py",10950,
            "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645"),
    FilePin("peano-lab/py/peano_lab/kernel/proofs.py",5015,
            "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2"),
    FilePin("peano-lab/py/peano_lab/kernel/subst.py",5165,
            "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3"),
    FilePin("peano-lab/py/peano_lab/kernel/terms.py",11144,
            "f49313e209a8861918e3aaca38ddfb27f147f824308af699ab5cc1aafbb6dff5"),
    FilePin("peano-lab/py/peano_lab/engine/__init__.py",286,
            "1fbd27721e00e873b4b6839508b63889e6ba8a4a51165b11e042c05270d1308b"),
    FilePin("peano-lab/py/peano_lab/engine/compact_arith.py",49086,
            "8e9d6330e7594e54a7b7917d9b95c5335a3bba2b38ce16c7d6c458c5c38d8fc0"),
    FilePin("peano-lab/py/peano_lab/engine/decide.py",17710,
            "07044458d92b68781d95091fabbe0fbc4a476c58f3821e0c806553e0813c2e0a"),
    FilePin("peano-lab/py/peano_lab/engine/induction.py",6433,
            "4bb1db5f3b944e1f9a0ebe388ab76970aae055bf4d1171d896fbb0323172545f"),
    FilePin("peano-lab/py/peano_lab/engine/norm_num.py",16127,
            "79d9ebe369348779aca6c7f12932a1204756a13d631ebd69f2612de082ab13b1"),
    FilePin("peano-lab/py/peano_lab/engine/proof_reduction.py",23381,
            "deb17a5a0d5562f73248d6fbaa8db46b923c7bab07e491f37cb98e5e19a8251f"),
    FilePin("peano-lab/py/peano_lab/engine/rewrite.py",28506,
            "05f0b5fe8d46910d9cc2b1604d96756aa68e42339ca90afc094d60bfce48aa5f"),
    FilePin("peano-lab/py/peano_lab/engine/ring.py",43196,
            "7ba5c4b4085725677ba984afa8a50cee8061ce9ba333b644993ecff5fd5f249e"),
    FilePin("peano-lab/py/peano_lab/engine/search.py",15634,
            "935d50ce4ad81e9a0a0483e8b52c61be93049ead02f8f0971ad58b6f9326e415"),
    FilePin("peano-lab/py/peano_lab/engine/state.py",22928,
            "368aa1a6d8e57b48396c0f17d124c280c7ebf5cfdbe8086bc053940af5f72e68"),
    FilePin("peano-lab/py/peano_lab/engine/tacticals.py",11282,
            "9285da2f6bc3ebebaa6c341b5dc94dd9282c6886b78ec8b8beebd58dc68536d6"),
    FilePin("peano-lab/py/peano_lab/engine/tactics.py",69649,
            "23307a7dde5a16e72ae844ad9762a3a95e14406f6da44c412a51be20eae6e69d"),
    FilePin("peano-lab/py/peano_lab/engine/trace.py",17735,
            "d9a7b2aa789fefd8d0da8d6ce6b6ae37b925f92a3e611e0809b02cd5e9173df7"),
    FilePin("peano-lab/py/peano_lab/library/theorems.py",536011,
            "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919"),
    FilePin("peano-lab/py/peano_lab/library/proof_bundle.py",26383,
            "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4"),
    FilePin("peano-lab/py/peano_lab/library/formula_dag.py",20794,
            "3dfd0ad9ec3270cb2cd40948b62f223ba9e5f7284152c823405d8002b7a1a45f"),
    FilePin("peano-lab/py/peano_lab/library/layered_replay.py",35376,
            "7c8b14b95ab76fe10f265a10271fd58f779fab3b7524c8f9002884b753b2badf"),
    FilePin("peano-lab/py/peano_lab/library/campaign_bottom_layer_closure.py",22539,
            "e4d6f74feabf16ac342c9bfb875a39d060f5b97039866ae3a0a5fea99db84477"),
    FilePin("peano-lab/py/peano_lab/library/campaign_lower_layer_closure.py",24500,
            "d7b31c8511d4439e1a2075cba718b2cba0fd7ea42a07c2ffb41d55dd7e75542c"),
    FilePin("peano-lab/py/peano_lab/library/campaign_gaussian_factorization_closure.py",38094,
            "68af15379776c0cb36125c1d2f24e7c87b98880a7caad24725453937b864ac3e"),
    FilePin("peano-lab/py/peano_lab/library/alpha_enrollment_v31.py",19548,
            "7106c15b7196ca70d4bd62a4708696bd38e9b4eee07a127844c2d8398cd6e81b"),
    FilePin("peano-lab/py/peano_lab/library/campaign_completed_lower_closure.py",92122,
            "9aec583406e6b890fdd626cb60ecf8de4271581e20e86e1aa8499a4b1701dab3"),
    FilePin("peano-lab/py/peano_lab/library/editions_v31.py",18745,
            "24fedcd8a492578f9a1e32bdd984693bd8e27216105000f719188a3a38200870"),
    FilePin("peano-lab/py/peano_lab/library/editions_v30.py",18555,
            "88499fde8ae5b19be5fea2d2d88d3ab56c0a27901abdbf6f005c16a0c1c1328f"),
    FilePin("peano-lab/py/peano_lab/library/alpha_enrollment_v30.py",11831,
            "ca61a5efa17c8624c29ad3388c97743947a81f648e7f1aeeef848833cd484bac"),
    FilePin("scripts/constructive_bottom_layer_checkpoints.py",14684,
            "edbab69b368b2944ceb38d6c7cee856c04c570ef6f7dc167f73528dd9581ab15"),
    FilePin("scripts/check_constructive_bottom_layers.py",2891,
            "5a2d4225cd82498ff6988d9dcb84cd18bb865e6d7318cb99752f0fe34fcad34f"),
    FilePin("scripts/check_constructive_lower_continuation.py",19402,
            "0db0df31d763ae2b747fd2eb3315066fc17c3be049ff481641a149fc2665603b"),
    FilePin("scripts/peano_catalog_shards.py",29340,
            "961d2698a309795e91ce8fc32564ea5113e6f36ed2798301c805e58c560942b9"),
)
# These are the actual newly generated v31 catalogue components, not G009
# proof evidence. Their bytes are authenticated without expanding the 93MB
# logical catalogue. G009 proof acceptance is checked separately every time.
PARENT_CATALOG_PINS: tuple[FilePin, ...] = (
    FilePin('artifacts/peano-library/alpha/catalog-v31.json',293294,
            '6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab'),
    FilePin(closure.PARENT_CATALOG,closure.PARENT_CATALOG_BYTES,closure.PARENT_CATALOG_SHA256),
    FilePin('artifacts/peano-library/alpha/catalog-v31-delta.json',27237393,
            'fb334cc28a234c3d5d6d65b417b7a10a2af19a5377f57f4dedb4ca65276f185e'),
)
NEW_SPECS_SHA256 = '25086b5c317b7dddd47cc06b0d9ad5639b6a5d88b6ede323cf7aa1124fa9dba7'


def canonical(value) -> bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,
                      separators=(',',':')).encode('utf-8')


def _repository_path(path: Path) -> str:
    """Relocation-stable label only; bounded physical reads remain mandatory."""
    if not isinstance(path, Path) or not path.is_absolute() or '..' in path.parts:
        raise G009Error('fingerprint input must be an absolute repository path')
    try:
        relative = path.relative_to(ROOT)
    except ValueError as error:
        raise G009Error('fingerprint input is outside the repository') from error
    if not relative.parts:
        raise G009Error('fingerprint input must name a repository file')
    return relative.as_posix()


def _file_identity(value):
    return (value.st_dev,value.st_ino,value.st_mode,value.st_size,
            value.st_mtime_ns,value.st_ctime_ns)


@contextmanager
def _bounded_stream(path: Path, maximum: int, *, exact_size: int | None = None):
    """One checked descriptor; reject ancestor, inode and in-place read races.

    Parent directory identities, rather than their mutable timestamps, are
    retained: unrelated files appearing in /private/tmp do not invalidate a
    read.  O_NONBLOCK prevents a leaf swapped to a FIFO from blocking open.
    Large pinned artifacts still stream through the original 64 MiB bound.
    """
    if (type(maximum) is not int or not 0 < maximum <= MAX_CATALOG_COMPONENT_BYTES
            or exact_size is not None and (type(exact_size) is not int or not 0 < exact_size <= maximum)):
        raise G009Error('invalid unchanged bounded-file limit')
    path = Path(path).absolute()
    try:
        parents = []
        for parent in reversed(path.parents):
            value = parent.lstat()
            if not stat.S_ISDIR(value.st_mode):
                raise G009Error('input has a nonregular or symbolic-link ancestor: ' + str(path))
            parents.append((parent,(value.st_dev,value.st_ino,value.st_mode)))
        before = path.lstat()
        if (not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum
                or exact_size is not None and before.st_size != exact_size):
            raise G009Error('input is not an exact nonempty bounded regular file: ' + str(path))
        descriptor = os.open(path,os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            stream = os.fdopen(descriptor,'rb')
        except BaseException:
            os.close(descriptor)
            raise
        with stream:
            opened = os.fstat(stream.fileno())
            if _file_identity(opened) != _file_identity(before):
                raise G009Error('input changed between inspection and open: ' + str(path))
            yield stream,before.st_size
            after = os.fstat(stream.fileno())
            latest = path.lstat()
            if (_file_identity(after) != _file_identity(before)
                    or _file_identity(latest) != _file_identity(after)):
                raise G009Error('input identity or contents changed during its read: ' + str(path))
            for parent,identity in parents:
                value = parent.lstat()
                if (value.st_dev,value.st_ino,value.st_mode) != identity:
                    raise G009Error('input ancestor changed during its read: ' + str(path))
    except OSError as error:
        raise G009Error('missing or unsafe bounded input: ' + str(path)) from error


def bounded_bytes(path: Path, maximum: int) -> bytes:
    with _bounded_stream(path,maximum) as (stream,size):
        payload = stream.read(size + 1)
        if len(payload) != size:
            raise G009Error('input changed beyond its exact observed byte bound')
    return payload


def check_pin(pin: FilePin, base: Path, maximum: int) -> None:
    if (type(maximum) is not int or not 0 < maximum <= MAX_CATALOG_COMPONENT_BYTES
            or type(pin) is not FilePin or type(pin.bytes) is not int or not 0 < pin.bytes <= maximum
            or type(pin.path) is not str or Path(pin.path).is_absolute()
            or '..' in Path(pin.path).parts or type(pin.sha256) is not str
            or re.fullmatch(r'[0-9a-f]{64}',pin.sha256) is None):
        raise G009Error('invalid literal bounded file pin')
    count,digest = 0,sha256()
    with _bounded_stream(base / pin.path,maximum,exact_size=pin.bytes) as (stream,_size):
        while chunk := stream.read(min(1024 * 1024,pin.bytes + 1 - count)):
            count += len(chunk)
            if count > pin.bytes:
                raise G009Error('literal file grew during its read')
            digest.update(chunk)
        if count != pin.bytes or digest.hexdigest() != pin.sha256:
            raise G009Error('literal file bytes changed: ' + pin.path)


def require_final_source_pins() -> None:
    if (type(MATH_SOURCE_PINS) is not tuple or any(type(pin) is not FilePin for pin in MATH_SOURCE_PINS)
            or tuple(pin.path for pin in MATH_SOURCE_PINS) != tuple(owner.path for owner in FACTORIES)
            or type(PARENT_CONTROL_PINS) is not tuple
            or any(type(pin) is not FilePin for pin in PARENT_CONTROL_PINS)
            or tuple(pin.path for pin in PARENT_CONTROL_PINS) != tuple(str(path.relative_to(ROOT)) for path in parent_control_paths())
            or tuple(pin.path for pin in PARENT_CATALOG_PINS) != (
                'artifacts/peano-library/alpha/catalog-v31.json',closure.PARENT_CATALOG,
                'artifacts/peano-library/alpha/catalog-v31-delta.json')
            or re.fullmatch(r'[0-9a-f]{64}',NEW_SPECS_SHA256) is None):
        raise G009Error('G009 final source/catalog/specification pins are not sealed')
    for pin in PARENT_CONTROL_PINS:
        check_pin(pin,ROOT,MAX_SOURCE_BYTES)
    for pin in PARENT_CATALOG_PINS:
        check_pin(pin,ROOT,MAX_CATALOG_COMPONENT_BYTES)
    import peano_catalog_shards
    bindings = peano_catalog_shards.verify_catalog_bindings(ROOT/PARENT_CATALOG_PINS[0].path,
                                                           expected_sha256=PARENT_CATALOG_PINS[0].sha256)
    if tuple((str(item.path.relative_to(ROOT)),item.bytes,item.sha256) for item in bindings.files) != tuple(
            (pin.path,pin.bytes,pin.sha256) for pin in PARENT_CATALOG_PINS):
        raise G009Error('the exact current v31 catalogue component bindings changed')


@dataclass(frozen=True, slots=True)
class CandidateState:
    rows: tuple[TheoremSpec, ...]
    sources: tuple[FilePin, ...]
    specs_sha256: str


def load_candidate_state(*, final: bool = False) -> CandidateState:
    if type(final) is not bool:
        raise G009Error('final must be an explicit Boolean')
    if final:
        require_final_source_pins()
    rows,sources = [],[]
    # Only these nine new package names are loaded. No old package path,
    # imported provider, checker, cache or module global is patched.
    for owner in FACTORIES:
        path = MATH_DIRECTORY / (owner.module + '.py')
        raw = bounded_bytes(path,MAX_SOURCE_BYTES)
        pin = FilePin(owner.path,len(raw),sha256(raw).hexdigest())
        if final and pin != MATH_SOURCE_PINS[len(sources)]:
            raise G009Error('a final mathematical source differs from its literal pin')
        qualified = 'peano_lab.library.' + owner.module
        existing = sys.modules.get(qualified)
        if existing is not None and Path(getattr(existing,'__file__','')).resolve() != path.resolve():
            raise G009Error('a candidate package name shadows a different source file')
        spec = importlib.util.spec_from_file_location(qualified,path)
        if spec is None or spec.loader is None:
            raise G009Error('cannot load an exact new mathematical source')
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        # Compile the authenticated bytes themselves; do not read a stale pyc.
        exec(compile(raw,str(path),'exec'),module.__dict__)
        factory = getattr(module,owner.factory,None)
        if not callable(factory) or getattr(factory,'__module__',None) != qualified:
            raise G009Error('the exact ordinary candidate factory is missing')
        values = factory(TheoremSpec)
        if type(values) is not tuple or len(values) != owner.count:
            raise G009Error('the prospective nine-factory inventory changed')
        rows.extend(values)
        sources.append(pin)
        if bounded_bytes(path,MAX_SOURCE_BYTES) != raw:
            raise G009Error('a mathematical source changed while its factory ran')
    result = tuple(rows)
    closure._validate_frontier(result)
    digest = closure._specs_digest(result)
    if len(result) != EXPECTED_NEW_COUNT or final and digest != NEW_SPECS_SHA256:
        raise G009Error('the exact ordered ninety-row specification changed')
    return CandidateState(result,tuple(sources),digest)


def all_new_rows(*, final: bool = False) -> tuple[TheoremSpec, ...]:
    return load_candidate_state(final=final).rows


def current_parent_specs() -> tuple[TheoremSpec, ...]:
    from peano_lab.library import editions_v31 as parent
    parent.require_completed_lower_seal()
    if (len(parent.ALPHA_CHECKED_SPECS) != PARENT_COUNT
            or len(parent.STABLE_SPECS) != PARENT_STABLE_COUNT
            or parent.ALPHA_V31_IDENTITY_SHA256 != PARENT_IDENTITY_SHA256
            or parent.ALPHA_V31_ENROLLMENT_SHA256 != PARENT_ENROLLMENT_SHA256
            or parent.STABLE_EDITION is not parent.v30.STABLE_EDITION
            or any(new is not old for new,old in zip(parent.ALPHA_ENTRIES,parent.v30.ALPHA_ENTRIES))):
        raise G009Error('the immutable current v31 or Stable identity changed')
    # The compatibility assembler must use byte-for-byte the same original
    # v30 specifications as the first 3222 v31 entries, not another catalogue.
    if closure.parent_snapshot().specs != parent.ALPHA_CHECKED_SPECS[:closure.PARENT_COUNT]:
        raise G009Error('the v30 execution base differs from the actual v31 prefix')
    return parent.ALPHA_CHECKED_SPECS


def dependency_cone(parent, new_rows, owned_names):
    """Pure syntax selection; deliberately not a proof/acceptance API."""
    if (type(parent) is not tuple or type(new_rows) is not tuple
            or type(owned_names) is not tuple or not owned_names
            or any(type(name) is not str for name in owned_names)
            or len(set(owned_names)) != len(owned_names)):
        raise G009Error('a nonempty exact owned-name tuple is required')
    table,available = {},set()
    for row in (*parent,*new_rows):
        if (type(row) is not TheoremSpec or row.name in available
                or type(row.dependencies) is not tuple
                or len(set(row.dependencies)) != len(row.dependencies)
                or not set(row.dependencies) <= available):
            raise G009Error('duplicate, missing, forward or cyclic actual dependency')
        table[row.name] = row
        available.add(row.name)
    new_names = {row.name for row in new_rows}
    if any(type(name) is not str for name in owned_names) or not set(owned_names) <= new_names:
        raise G009Error('only current new rows may be counted as owned')
    included,pending = set(),list(owned_names)
    while pending:
        name = pending.pop()
        if name not in included:
            included.add(name)
            pending.extend(table[name].dependencies)
    return tuple(row for row in (*parent,*new_rows) if row.name in included)


@dataclass(frozen=True, slots=True)
class SupportSelection:
    owned: tuple[TheoremSpec, ...]
    current_support: tuple[str, ...]
    parent_support: tuple[str, ...]
    frontier: tuple[TheoremSpec, ...]  # Explicit v30-execution frontier only.
    plan: closure.BottomLayerPlan
    complete_specs: tuple[TheoremSpec, ...]

    def role(self,name):
        if name in {row.name for row in self.owned}:
            return 'new_owned_theorem'
        if name in self.current_support:
            return 'new_cross_track_support'
        if name in self.parent_support:
            return 'inherited_alpha_v31'
        raise G009Error('name is outside the exact complete proof cone')


def select_support(new_rows: tuple[TheoremSpec, ...], owned_names: tuple[str, ...]) -> SupportSelection:
    closure._validate_frontier(new_rows)
    parent = current_parent_specs()
    complete = dependency_cone(parent,new_rows,owned_names)
    included = {row.name for row in complete}
    owned_set = set(owned_names)
    inherited_names = {row.name for row in parent}
    # These promoted entries are inherited Alpha-v31 prerequisites, despite
    # being passed as additive inputs to the unchanged v30-era assembler.
    promoted = tuple(row for row in parent[closure.PARENT_COUNT:] if row.name in included)
    current = tuple(row for row in new_rows if row.name in included)
    execution_frontier = (*promoted,*current)
    plan = closure.bottom_layer_plan(execution_frontier)
    if (tuple(row.name for row in plan.rows) != tuple(row.name for row in complete)
            or any(a.dependencies != b.dependencies or a.statement_sha256 != sha256(b.statement.encode()).hexdigest()
                   for a,b in zip(plan.rows,complete,strict=True))
            or not set(plan.root_names) <= owned_set):
        raise G009Error('the compatibility plan differs from the exact v31 dependency cone')
    return SupportSelection(tuple(row for row in new_rows if row.name in owned_set),
        tuple(row.name for row in current if row.name not in owned_set),
        tuple(row.name for row in complete if row.name in inherited_names),
        execution_frontier,plan,complete)


def parent_seed_paths() -> tuple[Path, ...]:
    """All 39 exact historical artifacts, identified but not accepted by hash."""
    from peano_lab.library import campaign_completed_lower_closure as completed
    current_parent_specs()
    completed.validate_completed_lower_source_bytes()
    legacy = closure.parent_snapshot().documents
    # Authenticate every original provider without retaining its inert bytes.
    # The same old snapshot supplies every literal path, size and digest.
    for document in legacy:
        check_pin(FilePin(document.path,document.bytes,document.sha256),ROOT,
                  closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    paths = [ROOT / pin.path for pin in legacy]
    for family in completed.COMPLETED_LOWER_FAMILIES:
        path = ROOT / family.artifact
        # Preserve the original per-family metadata gate as well as its pins.
        registered = completed.completed_lower_family(family.slug)
        check_pin(FilePin(family.artifact,registered.artifact_bytes,registered.artifact_sha256),ROOT,
                  closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
        paths.append(path)
    if len(paths) != 39 or len(set(paths)) != 39:
        raise G009Error('the exact 20+19 inherited proof-provider inventory changed')
    return tuple(paths)


def statement_duplicates(new_rows: tuple[TheoremSpec, ...]):
    closure._validate_frontier(new_rows)
    index,duplicates = {},[]
    for row in new_rows:
        encoded = FormulaArena().freeze(_closed_formula(row.statement)).to_json()
        key = sha256(encoded.encode()).digest()
        duplicates.extend((row.name,name) for name,other in index.get(key,()) if encoded == other)
        index.setdefault(key,[]).append((row.name,encoded))
    for row in current_parent_specs():
        encoded = FormulaArena().freeze(_closed_formula(row.statement)).to_json()
        duplicates.extend((name,row.name) for name,other in index.get(sha256(encoded.encode()).digest(),()) if encoded == other)
    return tuple(duplicates)


def parent_control_paths() -> tuple[Path,...]:
    # All implementation files in the old trusted kernel and tactic engine,
    # plus every explicit untrusted compiler/checking adapter used here.
    paths = tuple(sorted((ROOT/'peano-lab/py/peano_lab/kernel').glob('*.py')))
    paths += tuple(sorted((ROOT/'peano-lab/py/peano_lab/engine').glob('*.py')))
    relative = (
        'peano-lab/py/peano_lab/library/theorems.py',
        'peano-lab/py/peano_lab/library/proof_bundle.py',
        'peano-lab/py/peano_lab/library/formula_dag.py',
        'peano-lab/py/peano_lab/library/layered_replay.py',
        'peano-lab/py/peano_lab/library/campaign_bottom_layer_closure.py',
        'peano-lab/py/peano_lab/library/campaign_lower_layer_closure.py',
        'peano-lab/py/peano_lab/library/campaign_gaussian_factorization_closure.py',
        'peano-lab/py/peano_lab/library/alpha_enrollment_v31.py',
        'peano-lab/py/peano_lab/library/campaign_completed_lower_closure.py',
        'peano-lab/py/peano_lab/library/editions_v31.py',
        'peano-lab/py/peano_lab/library/editions_v30.py',
        'peano-lab/py/peano_lab/library/alpha_enrollment_v30.py',
        'scripts/constructive_bottom_layer_checkpoints.py',
        'scripts/check_constructive_bottom_layers.py',
        'scripts/check_constructive_lower_continuation.py',
        'scripts/peano_catalog_shards.py',
    )
    paths += tuple(ROOT/path for path in relative)
    return paths


def state_binding(state: CandidateState, *, final: bool = False) -> str:
    if final:
        require_final_source_pins()
    controls = []
    paths = parent_control_paths()
    paths += tuple(HERE/name for name in ('constructive_g009_support.py','constructive_g009_checkpoints.py',
                                        'export_constructive_g009.py','check_constructive_g009.py'))
    for path in paths:
        raw = bounded_bytes(path,MAX_SOURCE_BYTES)
        controls.append((_repository_path(path),len(raw),sha256(raw).hexdigest()))
    current_parent_specs()
    check_pin(FilePin(closure.PARENT_CATALOG,closure.PARENT_CATALOG_BYTES,
                      closure.PARENT_CATALOG_SHA256),ROOT,MAX_CATALOG_COMPONENT_BYTES)
    providers = parent_seed_paths()
    # parent_seed_paths re-authenticates all literal old provider bytes. Final
    # catalogue-component pins are checked separately, never parsed as proof.
    return sha256(canonical({'controls':controls,'sources':[asdict(pin) for pin in state.sources],
        'specs_sha256':state.specs_sha256,'parent':[PARENT_COUNT,PARENT_IDENTITY_SHA256,PARENT_ENROLLMENT_SHA256],
        'legacy_catalog':[closure.PARENT_CATALOG,closure.PARENT_CATALOG_BYTES,closure.PARENT_CATALOG_SHA256],
        'provider_paths':[_repository_path(path) for path in providers],
        'parent_catalog_pins':[asdict(pin) for pin in PARENT_CATALOG_PINS],
        'parent_control_pins':[asdict(pin) for pin in PARENT_CONTROL_PINS],
        'final_source_pins_required':final})).hexdigest()
