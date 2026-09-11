"""Frozen source and real-seed policy for three complete Jordan checkpoints."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path[:0]=[str(ROOT/'peano-lab/py'),str(ROOT/'scripts')]
import source_plan_jordan as source

MAX_BYTES=64*1024*1024
PHASES=(51,69,75)
PREVIOUS={51:0,69:51,75:69}
METRICS={51:(205,498,6),69:(232,569,13),75:(238,587,4)}
SOURCE_DIGESTS={51:'64fca60b9ca85f50c70004b519059f990698658bf6dbe8975473e53861990f3c',
                69:'1b01bd3a6b641acdc76cad40e1f552cc88841e5c8900479657bf7b4ddf269a87',
                75:'1f3a80196d9552811cb1ef93e8b42adfbd6def155b42066c68eaf645be1979c9'}
PRINCIPALS=('jordan_primitive_tuple_modulus_one','jordan_order_zero_excluded',
            'jordan_modulus_zero_excluded','jordan_totient_multiplicativity_exists')
ARTIFACT_DIRECTORY=HERE/'artifacts'
RUNTIME_MANIFEST=HERE/'original-runtime-byte-pins-v1.json'
RUNTIME_MANIFEST_SHA='780177298f746a2eaec9c6910ba7649c3a160bc9983e371cbd1fb2b123a5f34d'
TEST_PINS=(('test_jordan_totient_candidate.py',11745,'1664beaa7030f596d2075cccf9294d28707a84b42ea9d7ce332ed1cb97316e3f'),
           ('test_jordan_enumeration_candidate.py',12206,'82db22d13482a1b8f70d8ecce8e0f1ab07629297a3d4dfb4fd4cd6039fe9f2cf'),
           ('test_jordan_multiplicativity_candidate.py',9637,'1dfe2b0da1e875b94c92e113eb63c18b8a5f7a4f1f5bf31c76d5d4338db7a981'))
CONTROLS=('working_jordan_support.py','source_plan_jordan.py','check_working_jordan.py',
          'export_working_jordan.py','test_working_jordan.py','working-jordan-closure-rfc-v1.md')


@dataclass(frozen=True,slots=True)
class FilePin:
    path:str
    bytes:int
    sha256:str


SEEDS=(
    FilePin('research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json',688987,'6e3a08c73b8a45de127e6d50a771f95b52fd54894b1c2e43468751421488a01a'),
    FilePin('research/arithmetic-library/artifacts/g009-multiplicative-convolution-proof-bundle-v1.json',7840579,'953dc5ef340379b1e34883c2f9ab2181e91c872f5bbb7943c52b2fb70ce76959'),
    FilePin('research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json',14648599,'c4711433c92b67d2ebeb30131669c60563c70e0464dafa851d417fb88fb21a6d'),
)


def require(condition,message):
    if not condition:raise ValueError(message)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def raw(path,maximum=MAX_BYTES):
    path=Path(path).absolute()
    require('..' not in path.parts,'unresolved source traversal')
    for parent in path.parents:require(stat.S_ISDIR(parent.lstat().st_mode),'linked/non-directory source ancestor')
    info=path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_size<=maximum,'invalid bounded ordinary file')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        first=os.fstat(stream.fileno());data=stream.read(maximum+1);last=os.fstat(stream.fileno())
    require((info.st_dev,info.st_ino)==(first.st_dev,first.st_ino) and len(data)==info.st_size and
            (first.st_size,first.st_mtime_ns,first.st_ctime_ns)==(last.st_size,last.st_mtime_ns,last.st_ctime_ns),
            'file changed during authenticated read')
    require(path.lstat().st_ino==info.st_ino and path.lstat().st_dev==info.st_dev,'path replaced during read')
    return data


def read_pin(pin):
    require(type(pin) is FilePin and type(pin.bytes) is int and 0<pin.bytes<=MAX_BYTES and
            type(pin.path) is str and not Path(pin.path).is_absolute() and '..' not in Path(pin.path).parts and
            type(pin.sha256) is str and re.fullmatch('[0-9a-f]{64}',pin.sha256) is not None,'malformed literal file pin')
    data=raw(ROOT/pin.path)
    require(len(data)==pin.bytes and sha256(data).hexdigest()==pin.sha256,'literal bytes changed: '+pin.path)
    return data


def actual_pin(path):
    data=raw(path)
    return FilePin(Path(path).relative_to(ROOT).as_posix(),len(data),sha256(data).hexdigest())


def stage_path(through):
    require(type(through) is int and through in PHASES,'unknown exact stage')
    return ARTIFACT_DIRECTORY/f'working-jordan-prefix-{through}-proof-bundle-v1.json'


def required_seeds(through):
    stage_path(through)
    if through==51:return tuple(ROOT/p.path for p in SEEDS)
    if through==69:return (stage_path(51),ROOT/SEEDS[1].path,ROOT/SEEDS[2].path)
    return (stage_path(69),)


def state_binding():
    data=raw(RUNTIME_MANIFEST)
    require(sha256(data).hexdigest()==RUNTIME_MANIFEST_SHA,'original runtime inventory changed')
    records=json.loads(data)['files']
    expected=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'peano-lab/py/peano_lab').rglob('*.py'))
    require([r[0] for r in records if r[0].startswith('peano-lab/py/peano_lab/')]==expected,
            'original runtime file inventory changed')
    require(len(records)==563 and len({r[0] for r in records})==563,'invalid original runtime pins')
    for record in records:read_pin(FilePin(*record))
    for name,size,digest in (*source.SOURCE_PINS,*TEST_PINS):read_pin(FilePin((HERE/name).relative_to(ROOT).as_posix(),size,digest))
    allpins=[actual_pin(HERE/name) for name in CONTROLS]
    allpins.extend(actual_pin(HERE/name) for name,_,_ in (*source.SOURCE_PINS,*TEST_PINS))
    allpins.append(actual_pin(RUNTIME_MANIFEST))
    return sha256(canonical({'runtime':records,'local':[(p.path,p.bytes,p.sha256) for p in allpins]})).hexdigest()


def source_selection(through):
    owned,core,_=source.inventory()
    rows,roots=source.select_source(owned,core,through)
    records=[{'name':r.name,'statement':r.statement,'dependencies':list(r.dependencies),'script':list(r.script),'summary':r.summary} for r in rows]
    digest=sha256(('\n'.join(json.dumps(r,sort_keys=True,separators=(',',':')) for r in records)+'\n').encode()).hexdigest()
    require(digest==SOURCE_DIGESTS[through],'complete source specifications changed')
    require((len(rows),sum(len(r.dependencies) for r in rows),len(roots))==METRICS[through],'complete source geometry changed')
    if through==75:require(roots==PRINCIPALS,'final maximal roots changed')
    return owned[:through],rows,roots


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
    frontier=tuple(r for r in rows if r.name not in inherited)
    plan=closure.bottom_layer_plan(frontier)
    byname={r.name:r for r in rows}
    require(set(r.name for r in plan.rows)==set(byname) and set(plan.root_names)==set(roots),
            'original assembler plan differs from exact source cone')
    for row in plan.rows:
        actual=byname[row.name]
        require(row.statement_sha256==sha256(actual.statement.encode()).hexdigest() and row.dependencies==actual.dependencies,
                'actual parent plan target/premise metadata differs')
    return owned,tuple(byname[r.name] for r in plan.rows),frontier,plan


def seed_coverage(through):
    owned,rows,_=source_selection(through)
    fresh={r.name for r in owned[PREVIOUS[through]:]}
    targets={n:v for n,v in source.target_records(rows).items() if n not in fresh}
    paths=required_seeds(through)
    for path in paths:
        literal=next((p for p in SEEDS if ROOT/p.path==path),None)
        if literal is not None:read_pin(literal)
        else:
            require(path==stage_path(PREVIOUS[through]),'unknown previous-stage data')
            info=path.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1,'previous stage is not owned ordinary data')
            raw(path)
    result=source.inert_seed_coverage(paths,targets)
    if through!=51:
        nodes,edges,roots=METRICS[PREVIOUS[through]]
        first=result['seeds'][0]
        require(first['package_nodes']==nodes+1 and first['package_edges']==edges+roots,
                'previous artifact is not the exact complete preceding stage')
    require(not result['missing_names'],'real seeds do not cover every pre-existing target and ordered premises')
    return result
