"""Source/JSON-only prospective Jordan closure inventory; never proof authority.

This does not initialize Alpha or parse the original parent catalogue. Its DFS
order is not claimed to be the original assembler order. Actual authoring must
use parent_snapshot/bottom_layer_plan, freshly check every complete seed, and
check each complete result with the original HA and independent Lean gates.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import stat
import sys

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
PHASES=(51,69,75)
FACTORIES=(
    'coprime_divisor_decomposition_candidate',
    'linear_congruence_complete_candidate',
    'matrix_rank_finite_coding_candidate',
    'prime_field_polynomial_candidate',
    'finite_modular_set_candidate',
    'finite_division_prefix_candidate',
    'ha_canonical_gcd_candidate',
    'generalized_crt_compatibility_candidate',
    'ha_generalized_crt_sufficiency_candidate',
)
BASE_FACTORIES=(
    'make_jordan_totient_candidate_theorems',
    'make_jordan_enumeration_candidate_theorems',
    'make_jordan_enumeration_bridge_candidate_theorems',
    'make_jordan_scan_candidate_theorems',
    'make_jordan_crt_tuple_candidate_theorems',
    'make_jordan_canonical_crt_candidate_theorems',
)
SOURCE_PINS=(
    ('jordan_totient_candidate.py',68642,'ec2f9c368b4d30dfb8ffe0a2c89dca6e82966d3c8819ce10d29123189fe7052c'),
    ('jordan_multiplicativity_candidate.py',39602,'649f8725555429aadef26571f1975dc9a21c14ccbb23c22ea45d3107ef2e1556'),
)


def digest(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def pin(path):
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_size>67108864:
        raise ValueError('not a bounded ordinary source/data file: '+str(path))
    raw=path.read_bytes()
    if len(raw)!=info.st_size:raise ValueError('file changed during read')
    return [str(path.relative_to(ROOT)),len(raw),hashlib.sha256(raw).hexdigest()]


def load_owned(name):
    path=HERE/name
    expected=next(item for item in SOURCE_PINS if item[0]==name)
    before=pin(path)
    if tuple(before[1:])!=expected[1:]:raise ValueError('frozen Jordan source changed')
    loader=importlib.util.spec_from_file_location('_source_only_'+name[:-3],path)
    module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
    if pin(path)!=before:raise ValueError('Jordan source changed during loading')
    return module


def inventory():
    from peano_lab.library.theorems import TheoremSpec,_specs_by_name
    core=dict(_specs_by_name())
    providers=[pin(ROOT/'peano-lab/py/peano_lab/library/theorems.py')]
    for short in FACTORIES:
        module=importlib.import_module('peano_lab.library.'+short)
        providers.append(pin(Path(module.__file__)))
        for row in getattr(module,'make_'+short+'_theorems')(TheoremSpec):
            if row.name in core and core[row.name]!=row:
                raise ValueError('nonidentical canonical overlap: '+row.name)
            core[row.name]=row
    base=load_owned('jordan_totient_candidate.py')
    companion=load_owned('jordan_multiplicativity_candidate.py')
    owned=tuple(row for factory in BASE_FACTORIES for row in getattr(base,factory)(TheoremSpec))
    if len(owned)!=51:raise ValueError('base inventory drift')
    owned+=companion.make_jordan_multiplicativity_candidate_theorems(TheoremSpec)
    if len(owned)!=75 or len({r.name for r in owned})!=75:raise ValueError('owned inventory drift')
    for row in owned:
        if row.name in core:raise ValueError('owned/canonical name overlap')
        core[row.name]=row
    return owned,core,providers


def select_source(owned,core,through):
    if type(through) is not int or through not in PHASES:raise ValueError('unknown source phase')
    ordered={};active=set()
    def visit(name):
        if name in ordered:return
        if name in active:raise ValueError('source cycle')
        if name not in core:raise ValueError('missing canonical source: '+name)
        active.add(name)
        for dependency in core[name].dependencies:visit(dependency)
        active.remove(name);ordered[name]=core[name]
    for row in owned[:through]:visit(row.name)
    used={d for r in ordered.values() for d in r.dependencies}
    roots=tuple(n for n in ordered if n not in used)
    if set(ordered)&{r.name for r in owned[through:]}:raise ValueError('later working row in prefix cone')
    return tuple(ordered.values()),roots


def target_records(rows):
    from peano_lab.library.theorems import _closed_formula
    from peano_lab.library.proof_bundle import encode_formula
    hashes={r.name:digest(encode_formula(_closed_formula(r.statement))) for r in rows}
    return {r.name:(hashes[r.name],tuple(hashes[d] for d in r.dependencies)) for r in rows}


def inert_seed_coverage(paths,targets):
    """Compare actual closed targets AND ordered prerequisite targets, not names."""
    remaining=dict(targets);records=[]
    for path in paths:
        before=pin(path)
        data=json.loads(path.read_bytes())
        if not (type(data) is list and len(data)==4 and data[0]=='peano-lab-bundle-v1'):
            raise ValueError('not a native proof bundle')
        nodes=data[3]
        if type(data[1]) is not int or not 0<=data[1]<len(nodes) or data[2]!=nodes[data[1]][1]:
            raise ValueError('bad package root metadata')
        hashes=[];available={}
        for index,node in enumerate(nodes):
            if len(node)!=4 or type(node[0]) is not int or node[0]<=0 or not all(type(d) is int and 0<=d<index for d in node[2]):
                raise ValueError('bad ordered node metadata')
            target=digest(node[1]);hashes.append(target)
            available.setdefault((target,tuple(hashes[d] for d in node[2])),[]).append(index)
        covered={name:available[key] for name,key in remaining.items() if key in available}
        for name in covered:del remaining[name]
        records.append({'pin':before,'package_nodes':len(nodes),'package_edges':sum(len(n[2]) for n in nodes),'newly_covered':covered})
        if pin(path)!=before:raise ValueError('seed changed during inert comparison')
        del data,nodes,hashes,available
        gc.collect()
    return {'proof_check_performed':False,'seeds':records,'covered_count':len(targets)-len(remaining),'required_count':len(targets),'missing_names':sorted(remaining)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seed',action='append',default=[])
    args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)
    owned,core,providers=inventory();phases=[]
    previous=set()
    for through in PHASES:
        rows,roots=select_source(owned,core,through)
        records=[{'name':r.name,'statement':r.statement,'dependencies':list(r.dependencies),'script':list(r.script),'summary':r.summary} for r in rows]
        phases.append({'through':through,'theorem_nodes':len(rows),'inherited':len(rows)-through,'theorem_edges':sum(len(r.dependencies) for r in rows),
                       'package_nodes':len(rows)+1,'package_edges':sum(len(r.dependencies) for r in rows)+len(roots),'root_names':roots,
                       'source_dfs_names':[r.name for r in rows],'source_dfs_specs_sha256':hashlib.sha256(('\n'.join(json.dumps(r,sort_keys=True,separators=(',',':')) for r in records)+'\n').encode()).hexdigest(),
                       'new_canonical_names':[r.name for r in rows if r.name not in previous and r.name not in {x.name for x in owned}]})
        previous={r.name for r in rows}
    allrows,_=select_source(owned,core,75);targets=target_records(allrows)
    inherited={name:value for name,value in targets.items() if name not in {r.name for r in owned}}
    coverage=inert_seed_coverage(tuple(ROOT/seed for seed in args.seed),inherited) if args.seed else None
    report={'proof_authority':False,'source_dfs_not_original_parent_order':True,'original_parent_plan_checked':False,
            'source_pins':[pin(HERE/name) for name,_,_ in SOURCE_PINS],'canonical_source_pins':providers,'phases':phases,'all_inherited_seed_coverage':coverage,
            'alpha_imported':any(n.startswith('peano_lab.library.editions') for n in sys.modules),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    print(json.dumps(report,separators=(',',':')))
    signal.alarm(0)
    if report['alpha_imported'] or report['peak_rss_bytes']>268435456:raise SystemExit(1)


if __name__=='__main__':main()
