#!/usr/bin/env python3
"""Exact delivery of an already checked, non-admitted G009 research reader.

This is not a proof checker, a receipt-acceptance API, or an Alpha enrollment.
The separate live eight-worker publisher must first produce the literal
reader. Empty delivery registration is a hard stop. The existing v31 stage,
including its original Lean selector, must already be present.

Only the dedicated local _deploy/proofs tree can be changed. The v31 source
hub and all source readers remain unchanged; no remote operation or user-file
deletion is performed. New research HTML never receives the Alpha selector.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from hashlib import sha256
from html.parser import HTMLParser
from importlib import import_module
import json
import os
from pathlib import Path
import posixpath
import re
import resource
import signal
import stat
import sys
import tempfile
import time
from urllib.parse import parse_qs, unquote, urlsplit


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if HERE != ROOT/'scripts' or not (ROOT/'peano-lab/py/peano_lab').is_dir():
    raise RuntimeError('G009 delivery must reside in its repository scripts directory')
READER = ROOT/'book/_static/constructive-g009-explorer'
STAGE = ROOT/'_deploy/proofs'
PARENT_HUB = ROOT/'deploy/proofs/index.html'
PARENT_LOCK = ROOT/'deploy/proofs/release-v31.json'
SLUG = 'multiplicative-convolution'
REVISION = '6c9ebfb3c37e'
CATALOG_SHA256 = '6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab'
ALPHA_IDENTITY = '902fa75c2bf4624bb7fc5aca9a6c49b71ff8fa4499f8bdf9ce726cfd4166a5d7'
READER_SCHEMA = 'peano-lab-local-g009-proof-explorer-v1'
SCHEMA = 'peano-lab-g009-public-delivery-v1'
CPU_LIMITS, WALL_SECONDS, MAX_RSS_BYTES = (170,175), 180, 1536*1024*1024
MAX_FILE_BYTES, MAX_MANIFEST_BYTES = 64*1024*1024, 2*1024*1024
MAX_METADATA_BYTES, MAX_HUB_BYTES, MAX_FILES = 8*1024*1024, 512*1024, 20000
ATLAS_FILES = ('campaign.json','definitions.json','dag-audit.json','index.html')
OVERRIDES = frozenset(('index.html',*('grand-campaign/'+name for name in ATLAS_FILES)))
RELOCATIONS = {name:'release-g009/'+name for name in ('checkpoints.json','proof-audit.json','manifest.json')}
DELIVERY_RECORD = 'release-g009/delivery.json'
ASSETS = {
    'assets/proofs.css':'44ac9983416435ac33efada9eaa3ff914588845fe55932f5e8c54623b28c9285',
    'assets/defined-explorer.css':'eb26033797a96d83d62b36d9562ffa37afe7443e2a54bd1d693fc9d5da5ad220',
    'assets/defined-explorer.js':'1b95ce2289502ba87f76708096aa76c07961be733d37dd56f64711b04621d982',
    'assets/exact-explorer.css':'6dd0cf105c498dec70fe6a7fac04dcda397b40f947de677b36fc9c01962d84bc',
    'assets/exact-explorer.js':'98f11fff5d34b5fa481c1dd6a6b39eef58fed28d00bb7d1f4ac7d1226b4d6606',
}
MATH_FILES = (
    'arithmetic_multiplicative_candidate.py','coprime_divisor_decomposition_candidate.py',
    'divisor_pair_index_candidate.py','signed_block_sum_candidate.py',
    'signed_cartesian_product_candidate.py','signed_support_reindex_candidate.py',
    'dirichlet_multiplicative_entry_candidate.py','dirichlet_multiplicative_support_candidate.py',
    'dirichlet_multiplicative_candidate.py',
)
RFC = 'g009-multiplicative-convolution-rfc-v1.md'
PRINCIPALS = (
    'signed_support_reindex_sum_equal','signed_cartesian_product_sums_exists',
    'coprime_divisor_factor_pair_exists_unique','dirichlet_convolution_multiplicative_values',
    'dirichlet_convolution_multiplicative_table','dirichlet_convolution_multiplicative_exists_unique',
)
NO_ADMISSION = ('enrolled_in_alpha','admitted_to_alpha','alpha_checked_use',
                'checked_use','stable_member','admitted_to_stable')
NO_VERSION = ('alpha_first_enrolled_version','alpha_edition_version','alpha_evidence','first_admitted_version')
SELECTOR_MARKER = b'/proofs/assets/lean-selector.js'


class DeliveryError(ValueError):
    """A literal delivery input, boundary, route, or safe destination changed."""


@dataclass(frozen=True,slots=True)
class Pin:
    bytes: int
    sha256: str


@dataclass(frozen=True,slots=True)
class Registration:
    reader_manifest: Pin
    parent_hub: Pin
    parent_lock: Pin


# Fill only from the real, fully checked outputs. These identify bytes; they
# are never successful-proof flags and do not replace the original verifier.
REGISTRATION: Registration | None = Registration(
    reader_manifest=Pin(45222,'3882fba2f018961d90d8afd1ffbe317ec49e85320b7a0d6adb9e97d48db91f20'),
    parent_hub=Pin(80289,'7d82eafef7694aee35970a546a82542caa5045cbb79eb284fd5117ffcaae3992'),
    parent_lock=Pin(1989,'519d56845069d5c2c04420c15e7f2b3bd9f91b64b39f39cb974a992ccecaa2f3'),
)


@dataclass(frozen=True,slots=True)
class File:
    pin: Pin
    origin: str
    source: Path | None = None
    base: Path | None = None
    content: bytes | None = None


@dataclass(frozen=True,slots=True)
class Plan:
    registration: Registration
    parent: dict[str,File]
    overlay: dict[str,File]
    merged: dict[str,File]
    metadata: dict
    script_sha256: str


def _pin(raw: bytes) -> Pin:
    return Pin(len(raw),sha256(raw).hexdigest())


def _valid_pin(pin: Pin, maximum=MAX_FILE_BYTES) -> None:
    if (type(pin) is not Pin or type(pin.bytes) is not int or not 0 < pin.bytes <= maximum
            or type(pin.sha256) is not str or re.fullmatch(r'[0-9a-f]{64}',pin.sha256) is None):
        raise DeliveryError('invalid bounded literal delivery pin')


def _safe_name(name: str) -> bool:
    return (type(name) is str and bool(name) and not name.startswith('/')
            and re.fullmatch(r'[A-Za-z0-9_./-]+',name) is not None
            and all(part not in ('','.','..') for part in name.split('/')))


def _ordinary_ancestors(path: Path, base: Path, *, owned=False):
    try:
        relative = path.relative_to(base)
    except ValueError as error:
        raise DeliveryError('delivery path escaped its fixed ordinary tree') from error
    if any(part in ('.','..') for part in relative.parts):
        raise DeliveryError('delivery path traverses a parent')
    parents = []
    for current in reversed(path.parents):
        value = current.lstat()
        in_owned_tree = current == base or base in current.parents
        if (not stat.S_ISDIR(value.st_mode)
                or owned and in_owned_tree and value.st_uid != os.getuid()):
            raise DeliveryError('delivery ancestor is not an owned ordinary directory')
        parents.append((current,(value.st_dev,value.st_ino,value.st_mode),in_owned_tree))
    return tuple(parents)


def _file_identity(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def _read(path: Path, maximum: int, *, base: Path, owned=False) -> bytes:
    if type(maximum) is not int or not 0 < maximum <= MAX_FILE_BYTES:
        raise DeliveryError('invalid unchanged bounded-file limit')
    path,base = Path(path).absolute(),Path(base).absolute()
    try:
        parents = _ordinary_ancestors(path,base,owned=owned)
        before = path.lstat()
        if (not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum
                or owned and before.st_uid != os.getuid()):
            raise DeliveryError('delivery input has an unsafe size, owner, or type')
        descriptor = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
        try:
            stream = os.fdopen(descriptor,'rb')
        except BaseException:
            os.close(descriptor)
            raise
        with stream:
            opened = os.fstat(stream.fileno())
            if _file_identity(opened) != _file_identity(before):
                raise DeliveryError('delivery input changed between inspection and open')
            raw = stream.read(before.st_size+1)
            if len(raw) != before.st_size:
                raise DeliveryError('delivery input changed beyond its exact observed byte bound')
            after = os.fstat(stream.fileno())
            latest = path.lstat()
            if _file_identity(after) != _file_identity(before) or _file_identity(latest) != _file_identity(after):
                raise DeliveryError('delivery input changed inode or bytes during its bounded read')
            for parent,identity,in_owned_tree in parents:
                value = parent.lstat()
                if ((value.st_dev,value.st_ino,value.st_mode) != identity
                        or owned and in_owned_tree and value.st_uid != os.getuid()):
                    raise DeliveryError('delivery ancestor changed during its bounded read')
        return raw
    except OSError as error:
        raise DeliveryError('missing or unsafe bounded delivery input: '+str(path)) from error


def _pinned(path: Path, pin: Pin, *, base: Path, maximum=MAX_FILE_BYTES) -> bytes:
    _valid_pin(pin,maximum)
    raw = _read(path,pin.bytes,base=base)
    if _pin(raw) != pin:
        raise DeliveryError('literal delivery bytes changed: '+str(path))
    return raw


def _json(value) -> bytes:
    raw = (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    if len(raw) > MAX_METADATA_BYTES:
        raise DeliveryError('delivery metadata exceeds the existing bounded document budget')
    return raw


def _parse(raw: bytes, maximum=MAX_METADATA_BYTES):
    if type(raw) is not bytes or not 0 < len(raw) <= maximum:
        raise DeliveryError('invalid bounded JSON document')
    def pairs(items):
        result = {}
        for key,value in items:
            if key in result:
                raise DeliveryError('duplicate JSON key')
            result[key] = value
        return result
    def constant(_value):
        raise DeliveryError('non-finite JSON number')
    try:
        return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    except (UnicodeError,ValueError,TypeError,RecursionError) as error:
        raise DeliveryError('malformed delivery JSON') from error


def require_registration() -> Registration:
    value = REGISTRATION
    if type(value) is not Registration:
        raise DeliveryError('actual G009 reader and v31 hub delivery pins are not registered')
    _valid_pin(value.reader_manifest,MAX_MANIFEST_BYTES)
    _valid_pin(value.parent_hub,MAX_HUB_BYTES)
    _valid_pin(value.parent_lock,MAX_MANIFEST_BYTES)
    return value


def _legacy():
    # No proof runtime is imported. This is the established delivery-only
    # inventory reader, plus the unchanged selector's exact byte formatter.
    scripts = str(ROOT/'scripts')
    if scripts not in sys.path:
        sys.path.insert(0,scripts)
    stage = import_module('stage_completed_lower_publication_v31')
    selector = import_module('stage_public_lean_selector')
    if stage.ROOT != ROOT or stage.STAGE != STAGE or selector.ROOT != ROOT:
        raise DeliveryError('the established v31 delivery modules belong to another repository')
    return stage,selector


def _file_bytes(item: File) -> bytes:
    if type(item) is not File or item.origin not in {'alpha_v31','research_g009','delivery_metadata'}:
        raise DeliveryError('invalid delivery file record')
    _valid_pin(item.pin)
    if item.content is not None:
        if (type(item.content) is not bytes or item.source is not None or item.base is not None
                or _pin(item.content) != item.pin):
            raise DeliveryError('inline delivery bytes differ from their pin')
        return item.content
    if type(item.source) is not type(Path()) or type(item.base) is not type(Path()):
        raise DeliveryError('a delivery file has no exact ordinary source')
    return _pinned(item.source,item.pin,base=item.base)


def _inline(raw: bytes, origin='delivery_metadata') -> File:
    return File(_pin(raw),origin,content=raw)


class _HTML(HTMLParser):
    def __init__(self, raw: bytes):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.primary, self.heads = set(), [], [], 0
        self.feed(raw.decode('utf-8'))
        self.close()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if len(attrs) != len(attributes):
            raise DeliveryError('duplicate HTML attribute')
        if tag == 'base':
            raise DeliveryError('a base URL would change exact relative delivery routes')
        if tag == 'head':
            self.heads += 1
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                raise DeliveryError('duplicate HTML fragment identifier')
            self.ids.add(attrs['id'])
        if tag == 'a' and 'primary-action' in attrs.get('class','').split():
            self.primary.append(attrs.get('href',''))
        for field in ('href','src'):
            if field in attrs:
                self.links.append((tag,field,attrs[field]))

    handle_startendtag = handle_starttag


def _family_links(document: _HTML) -> tuple[str,...]:
    families = []
    for link in document.primary:
        parsed = urlsplit(link)
        name = parsed.path.rstrip('/')
        if name == 'grand-campaign':
            continue
        if (parsed.scheme or parsed.netloc or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name)
                or not parsed.path.endswith('/') or parsed.fragment
                or parse_qs(parsed.query) != {'v':[REVISION]}):
            raise DeliveryError('the canonical hub family route changed')
        families.append(name)
    return tuple(families)


def _once(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise DeliveryError('the literal v31 hub template changed: '+before[:65])
    return source.replace(before,after,1)


def render_public_hub(parent: bytes) -> bytes:
    """Pure QR-layout formatter, not an evidence verification entrypoint."""
    if type(parent) is not bytes or not 0 < len(parent) <= MAX_HUB_BYTES:
        raise DeliveryError('the literal parent hub is missing or oversized')
    original = _HTML(parent)
    names = _family_links(original)
    if (len(names) != len(set(names)) or len(names) != 63 or SLUG in names
            or not {'quadratic-reciprocity','bertrand-postulate'} <= set(names) or original.heads != 1):
        raise DeliveryError('the parent hub must contain exactly63 unchanged Alpha family routes')
    source = parent.decode('utf-8')
    source = _once(source,'Full G009 still needs multiplicative closure;',
        'The separate G009 research checkpoint now completes multiplicative closure; it is not an Alpha or Stable admission;')
    source = _once(source,'G009: inverse criterion and remaining closure',
        'G009: complete local research proof, separate admission status')
    source = _once(source,'The current library contains 63 proof families.',
        'This site presents 64 proof families: 63 Alpha-v31 families and one separately verified research family.')
    source = _once(source,'372 reviewed conservative definitions with 787 actual expansion arrows',
        '383 reviewed conservative definitions with 825 actual expansion arrows in the extended research atlas')
    source = _once(source,'<meta name="proof-publication-scope" content="alpha-v31-checked-use">',
        '<meta name="proof-publication-scope" content="alpha-v31-and-non-admitted-research">')
    section = '''    <section class="frontier-intro" aria-labelledby="g009-research-heading" data-public-research="G009">
      <p class="eyebrow">A separately verified research completion</p>
      <h2 id="g009-research-heading">Full finite signed G009, with its admission boundary intact.</h2>
      <p>90 independently proved research theorems; not Alpha/Stable. The complete dependency bundle passed original HA and independently compiled Lean, and six principal theorems have ordinary empty-context HA certificates. These new statements are not counted again among the 371 inherited Alpha-v31 prerequisites.</p>
      <p class="candidate-disclaimer">Alpha v31 remains 3,796 checked-use entries; Stable remains the unchanged 432-theorem edition. Full finite signed Dirichlet convolution, including multiplicative closure on nonempty prefixes normalized by F(1)=+1, is now locally proved. Zeroth values and table encodings remain unrestricted. General prime-power fields in G091 remain open.</p>
      <p><a href="release-g009/delivery.json">Exact research delivery inventory</a> · <a href="release-g009/manifest.json">Unchanged reader manifest</a> · <a href="release-g009/proof-audit.json">Literal independently checked research record</a> · <a href="release-g009/checkpoints.json">Exact research membership boundaries</a></p>
    </section>
    <section class="family-grid frontier-grid" aria-label="Independently proved non-admitted G009 research">
      <article class="family-card candidate-card euclidean-card" data-research-family="multiplicative-convolution" data-alpha-admitted="false" data-stable-admitted="false">
        <p class="card-kicker">90 independently proved research theorems · not Alpha/Stable</p>
        <h2>Multiplicative Dirichlet convolution</h2>
        <p>Follow constructed coprime divisor pairs, actual Cartesian signed sums and support-only reindexing to the complete coprime product law and positive-value uniqueness.</p>
        <a class="primary-action" href="multiplicative-convolution/?v='''+REVISION+'''">Explore the research proof map <span aria-hidden="true">→</span></a>
        <p><a href="multiplicative-convolution/explorer/defined/tag/MX0059.html?v='''+REVISION+'''">Read the exact constructed closure theorem</a> · <a href="grand-campaign/?view=goal&amp;focus=G009&amp;v='''+REVISION+'''">G009: independently proved research</a></p>
      </article>
    </section>
'''
    marker = '    <section class="frontier-intro" aria-labelledby="grand-campaign-heading">'
    source = _once(source,marker,section+marker)
    raw = source.encode('utf-8')
    revised = _family_links(_HTML(raw))
    if (len(raw) > MAX_HUB_BYTES or len(revised) != len(set(revised)) or len(revised) != 64
            or tuple(name for name in revised if name != SLUG) != names):
        raise DeliveryError('research delivery changed an existing family route')
    return raw


def _manifest(raw: bytes) -> dict[str,Pin]:
    value = _parse(raw,MAX_MANIFEST_BYTES)
    if (type(value) is not dict or value.get('schema') != READER_SCHEMA+'-manifest'
            or value.get('publication_scope') != 'local-only-checkpoint'
            or value.get('navigation_revision') != REVISION
            or type(value.get('checkpoint_digest')) is not str
            or re.fullmatch(r'[0-9a-f]{64}',value['checkpoint_digest']) is None
            or type(value.get('files')) is not dict
            or type(value.get('file_count_excluding_manifest')) is not int
            or not 1 <= len(value['files']) == value['file_count_excluding_manifest'] < MAX_FILES
            or _json(value) != raw):
        raise DeliveryError('the exact canonical non-admitting reader manifest changed')
    pins = {}
    for name,record in value['files'].items():
        if not _safe_name(name) or name == 'manifest.json' or type(record) is not dict or set(record) != {'bytes','sha256'}:
            raise DeliveryError('unsafe or incomplete reader file registration')
        pin = Pin(**record)
        _valid_pin(pin)
        pins[name] = pin
    required = {'index.html','checkpoints.json','proof-audit.json',
                *(SLUG+'/'+name for name in ('index.html','checkpoint.html','api/corpus.json','api/checkpoint.json',
                    'api/graph.json','explorer/index.html','explorer/defined/index.html','explorer/defined/graph.html',
                    'explorer/defined/api/graph.json')),
                *('grand-campaign/'+name for name in ATLAS_FILES),*ASSETS,
                *('sources/'+name for name in (*MATH_FILES,RFC)),
                *(SLUG+'/explorer/'+prefix+'tag/MX'+format(index,'04X')+'.html'
                  for prefix in ('','defined/') for index in range(1,91))}
    if not required <= pins.keys():
        raise DeliveryError('the complete90 theorem reader/source/atlas layout is missing')
    if ({name for name in pins if name.startswith('assets/')} != set(ASSETS)
            or {name for name in pins if name.startswith('sources/')} != {'sources/'+name for name in (*MATH_FILES,RFC)}
            or {name for name in pins if name.startswith('grand-campaign/')} != {'grand-campaign/'+name for name in ATLAS_FILES}
            or len([name for name in pins if name.startswith('checkpoints/')]) != 1):
        raise DeliveryError('research delivery must retain exactly5 assets,9 sources,RFC,one bundle and4 atlas files')
    for name,pin in pins.items():
        if name in ASSETS:
            if pin.sha256 != ASSETS[name]:
                raise DeliveryError('a canonical shared QR asset changed')
        elif name not in required and not (
            name.startswith(SLUG+'/explorer/defined/definition/') and len(Path(name).parts) == 5
            and re.fullmatch(r'(?:ND|PD)[0-9]{4}\.html',Path(name).name)
            or name.startswith('checkpoints/') and len(Path(name).parts) == 2 and name.endswith('.json')
        ):
            raise DeliveryError('unexpected file outside the exact research reader layout: '+name)
    return pins


def _tree_files(base: Path) -> set[str]:
    if base.is_symlink() or not base.is_dir():
        raise DeliveryError('reader tree is not an ordinary directory')
    result = set()
    for directory,children,names in os.walk(base,followlinks=False):
        for child in children:
            path = Path(directory)/child
            if path.is_symlink() or not path.is_dir():
                raise DeliveryError('linked or special directory in exact reader tree')
        for name in names:
            path = Path(directory)/name
            if path.is_symlink() or not path.is_file():
                raise DeliveryError('linked or special file in exact reader tree')
            result.add(path.relative_to(base).as_posix())
            if len(result) > MAX_FILES:
                raise DeliveryError('reader file inventory exceeded its existing bound')
    return result


def _local_flags(value: dict) -> None:
    if (type(value) is not dict or any(value.get(key) is not False for key in NO_ADMISSION)
            or any(value.get(key) is not None for key in NO_VERSION)
            or any(value.get(key) is not True for key in (
                'local_checkpoint_verified','original_ha_bundle_verified','independent_lean_bundle_verified'))):
        raise DeliveryError('delivery would mislabel research as an Alpha/Stable admission')


def _research_metadata(files: dict[str,File], parent: dict[str,File], manifest_raw: bytes) -> None:
    """Check literal displayed boundaries, not the truth of proof receipts."""
    inventory = _parse(_file_bytes(files['checkpoints.json']))
    if (type(inventory) is not dict or inventory.get('schema') != READER_SCHEMA
            or inventory.get('publication_scope') != 'local-only-checkpoint'
            or inventory.get('family_slug') != SLUG or inventory.get('navigation_revision') != REVISION
            or type(inventory.get('new_theorems')) is not int or inventory['new_theorems'] != 90
            or inventory.get('inherited_alpha_v31_theorems') != 371 or inventory.get('complete_theorems') != 461
            or any(inventory.get(key) is not False for key in (
                'published','alpha_admission_performed','stable_admission_performed','inherited_support_counted_as_new',
                'general_G091_prime_power_fields_proved'))
            or inventory.get('multiplicative_convolution_principals_checked') is not True
            or inventory.get('parent') != {'alpha_version':'v31','alpha_checked_use_count':3796,
                                         'stable_count':432,'catalog_sha256':CATALOG_SHA256}):
        raise DeliveryError('the literal research/parent inventory boundary changed')
    digest = inventory.get('checkpoint_digest')
    if (type(digest) is not str or digest != sha256(_json({key:value for key,value in inventory.items() if key != 'checkpoint_digest'})).hexdigest()
            or digest != _parse(manifest_raw,MAX_MANIFEST_BYTES)['checkpoint_digest']):
        raise DeliveryError('reader checkpoint metadata digest changed')
    raw_report = _file_bytes(files['proof-audit.json'])
    report = _parse(raw_report)
    if (type(report) is not dict or report.get('schema') != 'peano-g009-local-research-audit-presentation-v1'
            or report.get('fresh_worker_count') != 8 or inventory.get('checkpoint') != report
            or any(report.get(key) is not False for key in ('stored_receipt_is_proof_authority','published',
                                                          'alpha_admission_performed','stable_admission_performed'))
            or _file_bytes(files[SLUG+'/api/checkpoint.json']) != raw_report
            or tuple(row.get('name') for row in report.get('principal_roots',())) != PRINCIPALS):
        raise DeliveryError('the unchanged eight-job/six-principal presentation is incomplete')
    bundle = report.get('checkpoint',{}).get('bundle',{})
    name = 'checkpoints/'+Path(bundle.get('path','')).name
    if (name not in files or files[name].pin != Pin(bundle.get('bytes'),bundle.get('sha256'))
            or bundle.get('nodes') != 462 or bundle.get('original_ha_checked') is not True
            or bundle.get('independent_lean_checked') is not True):
        raise DeliveryError('the literal complete proof bundle is absent or changed')
    corpus = _parse(_file_bytes(files[SLUG+'/api/corpus.json']),MAX_FILE_BYTES)
    _local_flags(corpus)
    nodes = corpus.get('nodes')
    if (corpus.get('family_slug') != SLUG or corpus.get('node_count') != 90
            or corpus.get('new_theorem_count') != 90 or corpus.get('parent_alpha_checked_use_count') != 3796
            or corpus.get('parent_stable_count') != 432 or corpus.get('root_names') != list(PRINCIPALS)
            or type(nodes) is not list or len(nodes) != 90
            or [node.get('id') for node in nodes] != ['MX'+format(index,'04X') for index in range(1,91)]
            or len({node.get('name') for node in nodes}) != 90
            or corpus.get('tags') != {node.get('name'):node.get('id') for node in nodes}
            or inventory.get('tags') != corpus['tags']
            or corpus['tags'].get(PRINCIPALS[-1]) != 'MX0059'):
        raise DeliveryError('the90 exact research rows/tags or six roots were changed')
    for node in nodes:
        _local_flags(node)
    graph_raw = _file_bytes(files[SLUG+'/api/graph.json'])
    if graph_raw != _file_bytes(files[SLUG+'/explorer/defined/api/graph.json']):
        raise DeliveryError('the two literal graph API copies disagree')
    graph = _parse(graph_raw,MAX_FILE_BYTES)
    _local_flags(graph)
    theorem_nodes = [node for node in graph.get('nodes',()) if node.get('kind') == 'theorem']
    if len(theorem_nodes) != 90 or {node.get('id') for node in theorem_nodes} != {node['id'] for node in nodes}:
        raise DeliveryError('the actual mixed graph changed its research inventory')
    for node in theorem_nodes:
        _local_flags(node)
    old = _parse(_file_bytes(parent['grand-campaign/campaign.json']))
    campaign = _parse(_file_bytes(files['grand-campaign/campaign.json']))
    old_nodes = {node['id']:node for node in old['nodes']}
    current_nodes = {node['id']:node for node in campaign['nodes']}
    if (len(old_nodes) != 144 or set(current_nodes) != set(old_nodes)
            or any(current_nodes[name] != node for name,node in old_nodes.items() if name != 'G009')
            or campaign['ambitious_boundaries']['alpha_v31_edition'] != old['ambitious_boundaries']['alpha_v31_edition']):
        raise DeliveryError('research delivery changed current Alpha or an unrelated campaign node')
    goal = current_nodes['G009']
    evidence = goal.get('evidence',{})
    if (goal.get('status') != 'available' or goal.get('research_proof_closed') is not True
            or evidence.get('full_G009_finite_coded_contract_proved') is not True
            or any(evidence.get(key) is not False for key in ('checked_use','alpha_enrolled','stable_member'))
            or current_nodes['G091']['status'] != 'open'):
        raise DeliveryError('G009 research closure or the open G091 boundary was mislabeled')


def _merge(parent: dict[str,File], overlay: dict[str,File]) -> dict[str,File]:
    if not OVERRIDES <= parent.keys() or not OVERRIDES <= overlay.keys():
        raise DeliveryError('only a complete hub/four-file atlas replacement is supported')
    if (not set(ASSETS) <= parent.keys()
            or {name for name in overlay if name.startswith('assets/')} != set(ASSETS)):
        raise DeliveryError('the research overlay must share exactly the five original assets')
    merged = dict(parent)
    for name,item in overlay.items():
        if not _safe_name(name):
            raise DeliveryError('unsafe merged destination')
        if name in parent:
            if name in ASSETS:
                if parent[name].pin != item.pin or item.pin.sha256 != ASSETS[name]:
                    raise DeliveryError('shared QR asset bytes differ from the current v31 stage')
                continue
            if name not in OVERRIDES:
                raise DeliveryError('unexpected collision with an immutable v31 destination: '+name)
        elif name in OVERRIDES:
            raise DeliveryError('the required v31 replacement target is missing')
        merged[name] = item
    if len(merged) > MAX_FILES:
        raise DeliveryError('merged public inventory exceeds its existing file-count bound')
    return merged


def source_inventory() -> Plan:
    """Authenticate literal source bytes only; never reconstruct proof authority."""
    registration = require_registration()
    parent_hub = _pinned(PARENT_HUB,registration.parent_hub,base=ROOT,maximum=MAX_HUB_BYTES)
    parent_lock = _pinned(PARENT_LOCK,registration.parent_lock,base=ROOT,maximum=MAX_MANIFEST_BYTES)
    manifest_raw = _pinned(READER/'manifest.json',registration.reader_manifest,base=READER,maximum=MAX_MANIFEST_BYTES)
    pins = _manifest(manifest_raw)
    if _tree_files(READER) != set(pins)|{'manifest.json'}:
        raise DeliveryError('the actual G009 reader has missing or extra files')
    legacy,_selector = _legacy()
    prior,lock = legacy.source_inventory()  # Actual complete v31 byte verification.
    if (len(prior) <= 11000 or _json(lock) != parent_lock or lock.get('family_count') != 63
            or lock.get('checked_use_count') != 3796 or lock.get('stable_count') != 432
            or lock.get('catalog_sha256') != CATALOG_SHA256 or lock.get('edition_identity_sha256') != ALPHA_IDENTITY):
        raise DeliveryError('the complete existing v31 delivery inventory changed')
    parent = {name:File(Pin(**pin),'alpha_v31',source=path,base=ROOT) for name,(path,pin) in prior.items()}
    if parent['index.html'].pin != registration.parent_hub:
        raise DeliveryError('the literal v31 hub differs from its delivery inventory')
    files = {name:File(pin,'research_g009',source=READER/name,base=READER) for name,pin in pins.items()}
    for item in files.values():
        _file_bytes(item)
    _research_metadata(files,parent,manifest_raw)
    overlay = {RELOCATIONS.get(name,name):item for name,item in files.items() if name != 'index.html'}
    overlay[RELOCATIONS['manifest.json']] = File(registration.reader_manifest,'research_g009',source=READER/'manifest.json',base=READER)
    overlay['index.html'] = _inline(render_public_hub(parent_hub))
    merged = _merge(parent,overlay)
    script_sha = sha256(_read(Path(__file__),MAX_MANIFEST_BYTES,base=HERE)).hexdigest()
    metadata = {
        'schema':SCHEMA,'delivery_metadata_only':True,'stored_receipts_are_proof_authority':False,
        'alpha_admission_performed':False,'stable_admission_performed':False,
        'source_reader_flags_and_evidence_preserved_literally':True,
        'alpha_version':'v31','alpha_checked_use_count':3796,'stable_count':432,
        'family_count':64,'alpha_family_count':63,'research_family_count':1,'new_research_theorem_count':90,
        'inherited_alpha_theorems_not_counted_as_new':371,
        'G009':'independently_proved_research_not_alpha_or_stable_admitted','G091':'open',
        'catalog_sha256':CATALOG_SHA256,'navigation_revision':REVISION,
        'delivery_source_sha256':script_sha,
        'literal_inputs':asdict(registration),'parent_hub_source_unchanged':'deploy/proofs/index.html',
        'excluded_reader_aggregate':'index.html','unmodified_reader_metadata_relocations':RELOCATIONS,
        'only_v31_replacements':sorted(OVERRIDES),'shared_byte_identical_assets':sorted(ASSETS),
        'lean_selector_policy':'original exact insertion on old Alpha graph/theorem HTML only; none on new research',
        'file_count_excluding_this_delivery_record':len(merged),
        'source_bytes_excluding_this_delivery_record':sum(item.pin.bytes for item in merged.values()),
        'files':{name:asdict(item.pin) for name,item in sorted(merged.items())},
    }
    overlay[DELIVERY_RECORD] = merged[DELIVERY_RECORD] = _inline(_json(metadata))
    return Plan(registration,parent,overlay,merged,metadata,script_sha)


def _stage_root(root: Path) -> None:
    if (type(root) is not type(Path()) or root != STAGE or root.parent != ROOT/'_deploy'
            or ROOT.is_symlink() or not ROOT.is_dir()
            or root.is_symlink() or not root.is_dir() or root.stat().st_uid != os.getuid()
            or root.parent.is_symlink() or not root.parent.is_dir() or root.parent.stat().st_uid != os.getuid()):
        raise DeliveryError('G009 delivery is limited to the owned ordinary _deploy/proofs directory')


def _destination(root: Path, name: str, *, create: bool) -> Path:
    _stage_root(root)
    if not _safe_name(name):
        raise DeliveryError('unsafe staged destination')
    target = root/name
    current = root
    for part in Path(name).parts[:-1]:
        current /= part
        if current.is_symlink() or current.exists() and not current.is_dir():
            raise DeliveryError('unsafe staged directory')
        if create and not current.exists():
            current.mkdir(mode=0o755)
        if not current.is_dir() or current.stat().st_uid != os.getuid():
            raise DeliveryError('staged directory is absent or has a foreign owner')
    if target.is_symlink() or target.exists() and (not target.is_file() or target.stat().st_uid != os.getuid()):
        raise DeliveryError('refusing to replace a linked, special, or foreign staged file')
    return target


def _normalized_public_bytes(raw: bytes, pin: Pin, *, selector: bytes | None) -> bytes:
    if selector is not None and selector in raw:
        if raw.count(selector) != 1 or raw.count(SELECTOR_MARKER) != 1:
            raise DeliveryError('duplicate or foreign Lean selector')
        position = raw.index(selector)
        normalized = raw[:position]+raw[position+len(selector):]
        closing = re.search(rb'</head\s*>',normalized,re.I)
        if closing is None or closing.start() != position:
            raise DeliveryError('the original selector was inserted outside the exact head boundary')
    else:
        normalized = raw
        if SELECTOR_MARKER in raw:
            raise DeliveryError('a research page or old page has an unauthorized selector')
    if _pin(normalized) != pin:
        raise DeliveryError('staged bytes differ from their immutable source')
    return normalized


def _check_file(root: Path, name: str, item: File, selector_module, selector: bytes) -> bytes:
    eligible = (item.origin == 'alpha_v31' and selector_module._candidate(Path(name),Path(name))[0])
    insertion = selector if eligible else None
    raw = _read(root/name,item.pin.bytes+(len(insertion) if insertion else 0),base=root,owned=True)
    return _normalized_public_bytes(raw,item.pin,selector=insertion)


def _existing_additions(plan: Plan, root: Path) -> None:
    # Identical files from an interrupted/idempotent run are safe. A different
    # pre-existing file outside the five explicit overrides is never replaced.
    for name,item in plan.overlay.items():
        _preflight_destination(root,name)
        if name in plan.parent:
            continue
        target = root/name
        if target.exists() or target.is_symlink():
            raw = _read(target,item.pin.bytes,base=root,owned=True)
            _normalized_public_bytes(raw,item.pin,selector=None)
    for prefix in (SLUG,'release-g009'):
        directory = root/prefix
        if directory.exists() or directory.is_symlink():
            actual = {prefix+'/'+name for name in _tree_files(directory)}
            if not actual <= plan.overlay.keys():
                raise DeliveryError('unexpected existing file in the dedicated research namespace')


def _preflight_destination(root: Path, name: str) -> None:
    """Validate every already-existing ancestor without creating directories."""
    _stage_root(root)
    if not _safe_name(name):
        raise DeliveryError('unsafe planned destination')
    current = root
    for part in Path(name).parts[:-1]:
        current /= part
        if current.is_symlink() or current.exists() and (
                not current.is_dir() or current.stat().st_uid != os.getuid()):
            raise DeliveryError('a planned staged ancestor is linked, special, or foreign')
        if not current.exists():
            break
    target = root/name
    if target.is_symlink() or target.exists() and (
            not target.is_file() or target.stat().st_uid != os.getuid()):
        raise DeliveryError('an existing destination cannot be replaced safely')


def _link_target(page: str, href: str) -> tuple[str,str] | None:
    if type(href) is not str or '\\' in href or '\x00' in href:
        raise DeliveryError('unsafe HTML link')
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in ('https','http','mailto'):
            raise DeliveryError('unexpected non-web HTML link scheme')
        if not (parsed.scheme == 'https' and parsed.netloc == 'bnaskrecki.faculty.wmi.amu.edu.pl'
                and parsed.path.startswith('/proofs/')):
            return None
    path = unquote(parsed.path)
    if '\\' in path or '\x00' in path:
        raise DeliveryError('unsafe encoded HTML path')
    if path.startswith('/proofs/'):
        path = path[len('/proofs/'):]
        target = posixpath.normpath(path or 'index.html')
    elif path.startswith('/'):
        # Other same-origin applications are not part of this proof overlay.
        return None
    else:
        target = posixpath.normpath(posixpath.join(posixpath.dirname(page),path)) if path else page
    if path.endswith('/'):
        target = posixpath.normpath(target+'/index.html')
    if not _safe_name(target):
        raise DeliveryError('relative HTML link escapes the dedicated proof site')
    return target,unquote(parsed.fragment)


def check_internal_links(files: dict[str,File], root: Path) -> dict[str,int]:
    """Static routes/fragments of all merged immutable HTML, without a browser."""
    identifiers = {}
    count,fragments,html_count,extra_targets = 0,0,0,set()
    def payload(name):
        if name in files:
            return _file_bytes(files[name])
        # Explicitly staged historical checkpoints/k3b and other old assets
        # remain outside the v31 overlay inventory. Check their real bounded
        # target files, without assigning them new proof authority.
        extra_targets.add(name)
        return _read(root/name,MAX_FILE_BYTES,base=root,owned=True)
    for name,item in sorted(files.items()):
        if not name.endswith('.html'):
            continue
        raw = _file_bytes(item)
        if item.origin != 'alpha_v31' and SELECTOR_MARKER in raw:
            raise DeliveryError('the research source contains an Alpha-only selector')
        document = _HTML(raw)
        identifiers[name] = document.ids
        html_count += 1
        for _tag,_field,href in document.links:
            resolved = _link_target(name,href)
            if resolved is None:
                continue
            target,fragment = resolved
            if target in RELOCATIONS:
                raise DeliveryError('a relocated top-level research record was linked instead of remaining unlinked')
            if target not in files:
                payload(target)
            count += 1
            if fragment:
                if not target.endswith('.html'):
                    raise DeliveryError('a local fragment targets a non-HTML artifact')
                if target not in identifiers:
                    identifiers[target] = _HTML(payload(target)).ids
                if fragment not in identifiers[target]:
                    raise DeliveryError('missing exact HTML fragment: '+name+' -> '+target+'#'+fragment)
                fragments += 1
    return {'html_files':html_count,'local_links':count,'local_fragments':fragments,
            'existing_supplement_targets':len(extra_targets)}


def _atomic_write(root: Path, name: str, item: File) -> None:
    raw = _file_bytes(item)
    target = _destination(root,name,create=True)
    descriptor,temporary = tempfile.mkstemp(prefix='.g009-delivery-',dir=target.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor,'wb') as stream:
            stream.write(raw)
        temporary.chmod(0o644)
        _destination(root,name,create=False)
        os.replace(temporary,target)
    finally:
        # Only this invocation's private staging temporary can be removed.
        if temporary.exists():
            temporary.unlink()


def _write_order(overlay: dict[str,File]) -> tuple[str,...]:
    if 'index.html' not in overlay:
        raise DeliveryError('the final root hub is missing')
    return tuple(sorted((name for name in overlay if name not in ASSETS),
                        key=lambda name:(name == 'index.html',name)))


def _resource_gate(started: float) -> int:
    factor = 1 if sys.platform == 'darwin' else 1024
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)*factor
    if not 0 < peak <= MAX_RSS_BYTES or time.monotonic()-started > WALL_SECONDS:
        raise DeliveryError('the original delivery RSS/wall window was exceeded')
    return peak


def _rebind(plan: Plan) -> None:
    if require_registration() != plan.registration:
        raise DeliveryError('the literal delivery registration changed during staging')
    _pinned(PARENT_HUB,plan.registration.parent_hub,base=ROOT,maximum=MAX_HUB_BYTES)
    _pinned(PARENT_LOCK,plan.registration.parent_lock,base=ROOT,maximum=MAX_MANIFEST_BYTES)
    raw = _pinned(READER/'manifest.json',plan.registration.reader_manifest,base=READER,maximum=MAX_MANIFEST_BYTES)
    pins = _manifest(raw)
    if _tree_files(READER) != set(pins)|{'manifest.json'}:
        raise DeliveryError('the exact reader tree changed during delivery')
    _pinned(READER/'index.html',pins['index.html'],base=READER)
    for name in ASSETS:
        _file_bytes(plan.overlay[name])
    if sha256(_read(Path(__file__),MAX_MANIFEST_BYTES,base=HERE)).hexdigest() != plan.script_sha256:
        raise DeliveryError('the delivery implementation changed during staging')


def stage(root: Path = STAGE, *, check=False, api_url='') -> dict:
    started = time.monotonic()
    if type(check) is not bool:
        raise DeliveryError('check must be an explicit Boolean')
    require_registration()  # Fail before importing even the old delivery modules.
    _stage_root(root)
    plan = source_inventory()
    _legacy_stage,selector_module = _legacy()
    selector = selector_module._overlay(selector_module._api_url(api_url))
    for filename in ('lean-selector.css','lean-selector.js'):
        expected = selector_module._source_asset(filename)
        actual = _read(root/'assets'/filename,len(expected),base=root,owned=True)
        if actual != expected:
            raise DeliveryError('the original v31 Lean selector assets must already be staged exactly')
    _existing_additions(plan,root)
    if not check:
        for name,item in plan.parent.items():
            try:
                _check_file(root,name,item,selector_module,selector)
            except DeliveryError:
                if name not in OVERRIDES:
                    raise
                # Rerunning a partially completed overlay is allowed only for
                # these five exact alternate bytes, never for arbitrary files.
                _check_file(root,name,plan.merged[name],selector_module,selector)
    links = check_internal_links(plan.merged,root)
    _rebind(plan)
    _resource_gate(started)
    if not check:
        for name in _write_order(plan.overlay):
            _atomic_write(root,name,plan.overlay[name])
    # Byte equality with the already link-checked source files also proves
    # those exact static routes after staging. The only added old HTML bytes
    # are the separately checked, original root-relative selector insertion.
    for name,item in plan.merged.items():
        _check_file(root,name,item,selector_module,selector)
        _file_bytes(item)
    _existing_additions(plan,root)
    _rebind(plan)
    peak = _resource_gate(started)
    return {'schema':SCHEMA,'delivery_metadata_only':True,'check_only':check,
            'alpha_admission_performed':False,'stable_admission_performed':False,
            'family_count':64,'new_research_theorem_count':90,'alpha_checked_use_count':3796,'stable_count':432,
            'files':len(plan.merged),'source_bytes':sum(item.pin.bytes for item in plan.merged.values()),
            **links,'peak_rss_bytes':peak,'seconds':time.monotonic()-started}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=STAGE)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--api-url',default='')
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU,CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    root = args.root if args.root.is_absolute() else ROOT/args.root
    try:
        report = stage(root,check=args.check,api_url=args.api_url)
    except (DeliveryError,OSError,ValueError,KeyError,TypeError) as error:
        print('G009 delivery failed: '+str(error),file=sys.stderr)
        return 1
    print(_json(report).decode(),end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
