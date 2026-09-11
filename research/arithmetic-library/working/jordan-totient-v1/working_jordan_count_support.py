"""Separate complete86 source/seed policy; never changes the sealed Jordan75."""
from hashlib import sha256
import importlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PRIOR_BINDING='8bad0619f8f1e4c0b8a429526c52e1dc5c2eb0c697d994e61243ef9d8ac5aef6'
PRIOR_CONTROLS=(
    ('working_jordan_support.py',8784,'a42d10324585f5d1ce6f45d5dbacf11fbf8e59e0c3efeb40c75a6ea95c757394'),
    ('source_plan_jordan.py',8674,'5373e1b49869f45aec88347fb420dd1ea39d8b1483a3fea00fd3caaf57dfed31'),
    ('check_working_jordan.py',12112,'28d6c4bf966c5a1998c5131e2b8c8df8a7810699d45ea0b03f9c4dc9be88012c'),
    ('export_working_jordan.py',884,'fde3d3d7265957aa43d450f5274320f5272e5f2c58fe368e57e1fe12f23720a2'),
    ('test_working_jordan.py',7520,'d852210634ff93a537e52f68c3452b382118e7e1583f5e6bcca1417f29a5efef'),
    ('working-jordan-closure-rfc-v1.md',4684,'500fcc953d67ea7168f4f35a2829de3207830c4bedfed8a49694ebb1f04dd5c5'),
)
for name,size,digest in PRIOR_CONTROLS:
    path=HERE/name
    if path.is_symlink():raise ValueError('prior control symlink')
    data=path.read_bytes()
    if (len(data),sha256(data).hexdigest())!=(size,digest):raise ValueError('prior75 control changed')
sys.path.insert(0,str(HERE))
import working_jordan_support as prior
if Path(prior.__file__).resolve()!=HERE/'working_jordan_support.py':raise ValueError('foreign prior helper owner')

FilePin=prior.FilePin
raw,read_pin,actual_pin,canonical,require=prior.raw,prior.read_pin,prior.actual_pin,prior.canonical,prior.require
MAX_BYTES=prior.MAX_BYTES
PHASES=(86,)
METRICS={86:(270,690,5)}
PRINCIPALS=(*prior.PRINCIPALS,'jordan_totient_multiplicativity_unique_counts')
ARTIFACT_DIRECTORY=HERE/'artifacts'
NEW_PINS=(
    ('jordan_count_uniqueness_candidate.py',16706,'94fc0194d3fd049666a5475ead7606f5d51a17b6e643cea5b90fa01bc18ef575'),
    ('test_jordan_count_uniqueness_candidate.py',10845,'55a8b5239c3fbfb76cbd4b4cc49e2da5eaa3ecf0c6abb197c31ae698ac81e432'),
    ('jordan_multiplicativity_unique_candidate.py',1980,'7dd880155e468cf73c7e43f013cd50decc6633d9f2fb0d1cd673fe164ad72a3b'),
    ('test_jordan_multiplicativity_unique_candidate.py',3646,'666b23a68b6ee57dd953c8681bc8109f6bb86696ad37872d0257f948dbea6f95'),
)
CONTROLS=('working_jordan_count_support.py','check_working_jordan_count.py','export_working_jordan_count.py',
          'test_working_jordan_count.py','working-jordan-count-closure-rfc-v1.md')
SEEDS=(
    FilePin('research/arithmetic-library/working/jordan-totient-v1/artifacts/working-jordan-prefix-75-proof-bundle-v1.json',
            847318,'47754de334ada44e4eb9869358f4f3d0ec659083d529894d8cdc8e9fed30eca0'),
    FilePin('research/arithmetic-library/working/cyclic-unit-power-equations-v1/artifacts/working-cyclic-units-proof-bundle-v1.json',
            1615338,'e5114632c8af2c70bd7b09430cf8b860748ec4b62d391e7b977857fc5e33de64'),
)
# Measured DFS specification pin is set only after source construction checks.
SOURCE_DIGEST='b374b6f50496fda40ae1bf398214df2552b9443ad75223decc70c345a6ea1611'


def stage_path(through):
    require(type(through) is int and through==86,'only the exact complete86 stage is allowed')
    return ARTIFACT_DIRECTORY/'working-jordan-count-prefix-86-proof-bundle-v1.json'


def required_seeds(through):
    stage_path(through)
    return tuple(ROOT/p.path for p in SEEDS)


def _new_sources():
    for name,size,digest in NEW_PINS:read_pin(FilePin((HERE/name).relative_to(ROOT).as_posix(),size,digest))
    from peano_lab.library.theorems import TheoremSpec
    rows=[]
    for name,count in ((NEW_PINS[0][0],10),(NEW_PINS[2][0],1)):
        before=actual_pin(HERE/name)
        loader=importlib.util.spec_from_file_location('_jordan_count86_'+name[:-3],HERE/name)
        module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
        selected=getattr(module,'make_'+name[:-3]+'_theorems')(TheoremSpec)
        require(len(selected)==count and actual_pin(HERE/name)==before,'new source changed during construction')
        rows.extend(selected)
    return tuple(rows)


def source_inventory():
    from peano_lab.library.theorems import TheoremSpec
    owned,core,providers=prior.source.inventory()
    old_rows,_=prior.source.select_source(owned,core,75)
    extra=_new_sources()
    for row in extra:
        require(row.name not in core,'new/old theorem ownership overlap')
        core[row.name]=row
    module=importlib.import_module('peano_lab.library.fermat_two_squares_pigeonhole_candidate')
    for row in module.make_fermat_two_squares_pigeonhole_candidate_theorems(TheoremSpec):
        require(row.name not in core or core[row.name]==row,'nonidentical canonical provider overlap')
        core[row.name]=row
    owned=owned+extra;ordered={};active=set()
    def visit(name):
        require(name in core,'missing canonical source: '+name)
        if name in ordered:return
        require(name not in active,'source cycle')
        active.add(name)
        for dependency in core[name].dependencies:visit(dependency)
        active.remove(name);ordered[name]=core[name]
    for row in owned:visit(row.name)
    rows=tuple(ordered.values());used={d for r in rows for d in r.dependencies}
    roots=tuple(n for n in ordered if n not in used)
    require(len(owned)==86 and len({r.name for r in owned})==86,'owned inventory changed')
    require(len(old_rows)==238 and all(ordered.get(r.name)==r for r in old_rows),'full prior238 source cone not preserved')
    records=[dict(name=r.name,statement=r.statement,dependencies=list(r.dependencies),script=list(r.script),summary=r.summary) for r in rows]
    digest=sha256(('\n'.join(json.dumps(r,sort_keys=True,separators=(',',':')) for r in records)+'\n').encode()).hexdigest()
    return owned,rows,roots,digest


def source_selection(through):
    stage_path(through);owned,rows,roots,digest=source_inventory()
    require(type(SOURCE_DIGEST) is str and digest==SOURCE_DIGEST,'complete86 source not frozen or changed')
    require((len(rows),sum(len(r.dependencies) for r in rows),len(roots))==METRICS[86],'complete86 geometry changed')
    require(roots==PRINCIPALS,'final exact roots changed')
    return owned,rows,roots


def state_binding():
    require(prior.state_binding()==PRIOR_BINDING,'sealed prior75 changed')
    for name,size,digest in (*PRIOR_CONTROLS,*NEW_PINS):
        read_pin(FilePin((HERE/name).relative_to(ROOT).as_posix(),size,digest))
    for pin in SEEDS:read_pin(pin)
    pins=[actual_pin(HERE/name) for name in CONTROLS]
    pins.extend(actual_pin(HERE/name) for name,_,_ in NEW_PINS)
    return sha256(canonical(dict(prior75=PRIOR_BINDING,local=[(p.path,p.bytes,p.sha256) for p in pins],
                                seeds=[(p.path,p.bytes,p.sha256) for p in SEEDS]))).hexdigest()


def execution_selection(through):
    from peano_lab.library import campaign_bottom_layer_closure as closure
    from peano_lab.library.theorems import _closed_formula
    owned,rows,roots=source_selection(through)
    inherited={r.name:r for r in closure.parent_snapshot().specs}
    for row in rows:
        if row.name in inherited:
            old=inherited[row.name]
            require(_closed_formula(old.statement)==_closed_formula(row.statement) and old.dependencies==row.dependencies,
                    'original-v30 canonical target/premise overlap differs')
    require(not set(r.name for r in owned)&set(inherited),'working name already in original parent')
    frontier=tuple(r for r in rows if r.name not in inherited);plan=closure.bottom_layer_plan(frontier)
    byname={r.name:r for r in rows}
    require(set(r.name for r in plan.rows)==set(byname) and set(plan.root_names)==set(roots),'original plan differs from full source cone')
    for row in plan.rows:
        exact=byname[row.name]
        require(row.statement_sha256==sha256(exact.statement.encode()).hexdigest() and row.dependencies==exact.dependencies,
                'original-plan target or ordered premises differ')
    return owned,tuple(byname[r.name] for r in plan.rows),frontier,plan


def seed_coverage(through):
    owned,rows,_=source_selection(through)
    fresh={r.name for r in owned[75:]}
    targets={n:v for n,v in prior.source.target_records(rows).items() if n not in fresh}
    require(len(targets)==259,'preexisting source count changed')
    for pin in SEEDS:read_pin(pin)
    result=prior.source.inert_seed_coverage(required_seeds(through),targets)
    first=result['seeds'][0]
    require(first['package_nodes']==239 and first['package_edges']==591,'not exact complete75 seed')
    require(not result['missing_names'],'real complete seeds do not cover every exact target and ordered premise')
    for pin in SEEDS:read_pin(pin)
    return result
