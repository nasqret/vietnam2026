"""Exact non-admitting linear-congruence source selection and original plan.

DFS is a source ordering only. Artifact IDs always come from the unchanged
v30-parent-first assembler. A saved observation never supplies proof authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import importlib
import json
from pathlib import Path
import re
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING_RELATIVE = HERE.relative_to(ROOT).as_posix()
sys.path[:0] = [str(ROOT / 'peano-lab/py'), str(ROOT / 'scripts')]
from constructive_g009_support import FilePin, bounded_bytes, check_pin
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name
from peano_lab.library.proof_bundle import encode_formula
import constructive_bottom_layer_checkpoints as independent
from check_constructive_bottom_layers import authoring_rss_bytes

MAX_BYTES = 64 * 1024 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
SOURCE_PIN = FilePin(WORKING_RELATIVE + '/linear_congruence_classification_candidate.py',18128,
    '12b1a98ce830704485f1ea78475fba8b10e39031ffbef00b1b5dfc8ffdef7f47')
TEST_PIN = FilePin(WORKING_RELATIVE + '/test_linear_congruence_classification_candidate.py',13751,
    '97bb95b1f388fe947eba41f443265a30d5b8f3fa216df4a1abd688d95db5da35')
SPECS_SHA256 = 'ee5a8f02bd360e7e164e25172af6460cb770881f4470ea6acbc2e04b944c75ec'
PROVIDERS = (
    ('linear_congruence_complete_candidate','make_linear_congruence_complete_candidate_theorems'),
    ('ha_generalized_crt_congruence_candidate','make_ha_generalized_crt_congruence_candidate_theorems'),
    ('finite_modular_set_candidate','make_finite_modular_set_candidate_theorems'),
    ('generalized_crt_compatibility_candidate','make_generalized_crt_compatibility_candidate_theorems'),
    ('fermat_endpoints_candidate','make_fermat_endpoint_candidate_theorems'),
    ('fermat_product_balance_candidate','make_fermat_product_balance_candidate_theorems'),
    ('fermat_residue_product_candidate','make_fermat_residue_product_candidate_theorems'),
    ('fermat_residue_reindex_candidate','make_fermat_residue_reindex_candidate_theorems'),
    ('fermat_scale_product_candidate','make_fermat_scale_product_candidate_theorems'),
    ('fermat_residue_map_candidate','make_fermat_residue_map_candidate_theorems'),
    ('finite_product_reindex_candidate','make_finite_product_reindex_candidate'),
)
PRINCIPAL_ROOTS = (
    'linear_congruence_exact_bounded_enumeration_exists',
    'linear_congruence_zero_modulus_nonzero_coefficient_unique',
    'linear_congruence_zero_modulus_zero_coefficient_iff',
    'linear_congruence_modulus_one_bounded_iff_zero',
    'fermat_little_all_inputs',
)
SEED_PINS = (FilePin('research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json',
    14648599,'c4711433c92b67d2ebeb30131669c60563c70e0464dafa851d417fb88fb21a6d'),)
PHASES = (12,)
ARTIFACT_DIRECTORY = HERE / 'artifacts'
OUTPUT_PREFIX = 'working-linear-congruence-prefix-'
CONTROL_FILES = ('working_linear_congruence_support.py','export_working_linear_congruence.py',
    'check_working_linear_congruence.py','test_working_linear_congruence_controls.py')
# Set only after authentic helper files and the exact direct factory closure are read.
RUNTIME_MANIFEST_SHA256 = 'e38157fd486f21a16ccac8252f2ec8a7df54b031985e490a44ecc33e3044c943'

def _require(condition, message):
    if not condition:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def _safe_relative(value):
    return type(value) is str and bool(value) and not Path(value).is_absolute() and '..' not in Path(value).parts

def _digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None

def read_pin(pin, maximum=MAX_BYTES):
    _require(type(pin) is FilePin and _safe_relative(pin.path) and type(pin.bytes) is int
             and 0 < pin.bytes <= maximum and _digest(pin.sha256),'malformed exact file pin')
    raw = bounded_bytes(ROOT / pin.path,maximum)
    _require(len(raw)==pin.bytes and sha256(raw).hexdigest()==pin.sha256,'actual pinned bytes differ: '+pin.path)
    return raw

def spec_digest(rows):
    return sha256(canonical([asdict(row) for row in rows])).hexdigest()

def candidate_rows():
    raw = read_pin(SOURCE_PIN,MAX_SOURCE_BYTES)
    read_pin(TEST_PIN,MAX_SOURCE_BYTES)
    module = ModuleType('_private_linear_congruence_source')
    module.__file__ = str(ROOT / SOURCE_PIN.path)
    exec(compile(raw,module.__file__,'exec'),module.__dict__)
    rows = module.make_linear_congruence_classification_candidate_theorems(TheoremSpec)
    _require(type(rows) is tuple and len(rows)==12 and spec_digest(rows)==SPECS_SHA256
             and len({r.name for r in rows})==12
             and sum(len(r.dependencies) for r in rows)==61
             and sum(len(r.script) for r in rows)==658,'frozen mathematical inventory differs')
    return rows

def provider_table():
    table = dict(_specs_by_name())
    for name,factory in PROVIDERS:
        module = importlib.import_module('peano_lab.library.'+name)
        for row in getattr(module,factory)(TheoremSpec):
            _require(row.name not in table or table[row.name]==row,'canonical provider collision: '+row.name)
            table[row.name]=row
    return table

@dataclass(frozen=True,slots=True)
class Selection:
    owned: tuple
    inherited: tuple
    complete_specs: tuple
    root_names: tuple

def select_support(rows=None):
    if rows is None:
        rows=candidate_rows()
    _require(type(rows) is tuple and spec_digest(rows)==SPECS_SHA256,'altered source selection')
    table=provider_table()
    owned={r.name for r in rows}
    for row in rows:
        _require(row.name not in table or row==table[row.name],'new/canonical ownership collision')
        table[row.name]=row
    seen=set();active=set();ordered=[]
    def visit(name):
        _require(name in table and name not in active,'missing/cyclic actual prerequisite: '+name)
        if name in seen:return
        row=table[name]
        _require(len(set(row.dependencies))==len(row.dependencies),'duplicate actual prerequisite')
        active.add(name)
        for dep in row.dependencies:visit(dep)
        active.remove(name);seen.add(name);ordered.append(row)
    for row in rows:visit(row.name)
    used={d for r in rows for d in r.dependencies}
    roots=tuple(r.name for r in rows if r.name not in used)
    result=Selection(rows,tuple(r for r in ordered if r.name not in owned),tuple(ordered),roots)
    _require((len(result.inherited),len(ordered),sum(len(r.dependencies) for r in ordered))==(202,214,642)
             and roots==PRINCIPAL_ROOTS,'exact source dependency cone differs')
    return result

def execution_selection():
    selected=select_support()
    parent={r.name:r for r in closure.parent_snapshot().specs}
    _require(all(r.name not in parent or r==parent[r.name] for r in selected.complete_specs),
             'the original parent source identity differs')
    frontier=tuple(r for r in selected.complete_specs if r.name not in parent)
    plan=closure.bottom_layer_plan(frontier)
    exact={r.name:r for r in selected.complete_specs}
    _require(set(exact)=={r.name for r in plan.rows} and plan.root_names==selected.root_names,
             'original artifact plan differs from source cone')
    for row in plan.rows:
        expected=exact[row.name]
        _require(row.dependencies==expected.dependencies
                 and row.statement_sha256==sha256(expected.statement.encode()).hexdigest(),
                 'original artifact target or ordered premises differ')
    return selected,frontier,plan

def stage_path(through=12):
    _require(type(through) is int and through in PHASES,'unregistered stage')
    return ARTIFACT_DIRECTORY / (OUTPUT_PREFIX+str(through)+'-proof-bundle-v1.json')

def stage_metrics(through=12):
    stage_path(through)
    return 214,642,5

def seed_coverage(selected):
    targets={r.name:canonical(encode_formula(_closed_formula(r.statement))) for r in selected.complete_specs}
    table={r.name:r for r in selected.inherited}
    index={}
    for n in table:index.setdefault(targets[n],[]).append(n)
    matched=set();records=[]
    for pin in SEED_PINS:
        value=json.loads(read_pin(pin))
        _require(type(value) is list and len(value)==4 and value[0]=='peano-lab-bundle-v1'
                 and type(value[1]) is int and type(value[3]) is list and len(value[3])==1224
                 and value[1]==1223,'actual seed envelope differs')
        nodes=value[3]
        _require(all(type(n) is list and len(n)==4 and type(n[2]) is list
                     and all(type(d) is int and 0<=d<i for d in n[2]) for i,n in enumerate(nodes))
                 and value[2]==nodes[value[1]][1],'malformed seed topology')
        encoded=tuple(canonical(n[1]) for n in nodes)
        covered=set()
        for i,node in enumerate(nodes):
            for name in index.get(encoded[i],()):
                if tuple(encoded[d] for d in node[2])==tuple(targets[d] for d in table[name].dependencies):
                    covered.add(name)
        matched.update(covered)
        records.append(dict(**asdict(pin),inert_nodes=len(nodes),covered_targets=len(covered)))
    return dict(preexisting_targets=len(table),covered_targets=len(matched),missing_names=sorted(set(table)-matched),
                seeds=records,raw_json_only=True,proof_bodies_decoded=False,proof_authority=False)

def runtime_manifest():
    _require(_digest(RUNTIME_MANIFEST_SHA256),'actual helper/source registration is unset')
    raw=bounded_bytes(HERE/'runtime-source-pins-v1.json',MAX_SOURCE_BYTES)
    _require(sha256(raw).hexdigest()==RUNTIME_MANIFEST_SHA256,'helper source manifest differs')
    data=json.loads(raw)
    _require(type(data) is list and data and all(type(x) is dict and set(x)=={'path','bytes','sha256'} for x in data),
             'malformed helper source registration')
    pins=tuple(FilePin(**x) for x in data)
    _require(len({p.path for p in pins})==len(pins),'duplicate helper pin')
    for pin in pins:read_pin(pin,MAX_SOURCE_BYTES)
    return pins

def state_binding():
    rows=candidate_rows()
    pins=runtime_manifest()
    controls=[]
    for name in CONTROL_FILES:
        raw=bounded_bytes(HERE/name,MAX_SOURCE_BYTES)
        controls.append(dict(path=WORKING_RELATIVE+'/'+name,bytes=len(raw),sha256=sha256(raw).hexdigest()))
    for pin in SEED_PINS:read_pin(pin)
    return sha256(canonical(dict(sources=[asdict(SOURCE_PIN),asdict(TEST_PIN)],helpers=[asdict(p) for p in pins],
        controls=controls,seeds=[asdict(p) for p in SEED_PINS],specs=spec_digest(rows),
        principal_roots=PRINCIPAL_ROOTS,phases=PHASES,saved_reports_supply_authority=False))).hexdigest()

def local_manifest():
    selected=select_support()
    return dict(schema='working-linear-congruence-source-plan-v1',syntax_only=True,
        names=[r.name for r in selected.owned],new_rows=12,inherited_rows=202,theorem_rows=214,
        theorem_edges=642,bundle_nodes=215,bundle_edges=647,specs_sha256=SPECS_SHA256,
        complete_source_dfs_specs_sha256=spec_digest(selected.complete_specs),
        original_frontier_and_positions_require_parent_plan=True,maximal_roots=PRINCIPAL_ROOTS,
        seed_coverage=seed_coverage(selected),original_ha_checked=False,independent_lean_checked=False,
        alpha_admission_performed=False,stable_admission_performed=False)
