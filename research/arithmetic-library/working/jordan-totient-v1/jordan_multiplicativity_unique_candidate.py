"""Arbitrary-witness multiplicativity, conditional on genuine count uniqueness.

This one new ordinary body is unverified. It neither changes the frozen
Jordan75/count10 sources nor claims a distinct-prime product formula.
"""
from hashlib import sha256
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
COUNT_SOURCE=HERE/'jordan_count_uniqueness_candidate.py'
COUNT_BYTES=16706
COUNT_SHA256='94fc0194d3fd049666a5475ead7606f5d51a17b6e643cea5b90fa01bc18ef575'


def _check_source():
    if COUNT_SOURCE.is_symlink():raise ValueError('count source cannot be a symlink')
    raw=COUNT_SOURCE.read_bytes()
    if len(raw)!=COUNT_BYTES or sha256(raw).hexdigest()!=COUNT_SHA256:
        raise ValueError('count source changed')


_check_source()
loader=importlib.util.spec_from_file_location('_jordan_unique_count_source',COUNT_SOURCE)
count=importlib.util.module_from_spec(loader);loader.loader.exec_module(count)
_check_source()


def make_jordan_multiplicativity_unique_candidate_theorems(spec):
    args=('k','a','b','u','v','w')
    ja=count._jordan('k','a','u','arbitrary_left')
    jb=count._jordan('k','b','v','arbitrary_right')
    jw=count._jordan('k','a*b','w','arbitrary_product')
    product=count._jordan('k','a*b','u*v','constructed_product')
    body=count._intro(*args,'hcop','ha','hb','hw')+('have hp : '+product,)
    body+=count._call('jordan_totient_coprime_product','k','a','b','u','v')+(
        'exact hcop','exact ha','exact hb')
    body+=count._call('jordan_totient_count_unique','k','a*b','w','u*v')+('exact hw','exact hp')
    return (spec('jordan_totient_multiplicativity_unique_counts',count._contract(args,
        (count.base._cop('a','b','arbitrary_coprime'),ja,jb,jw),'w=u*v'),
        ('jordan_totient_coprime_product','jordan_totient_count_unique'),body,
        'Any three genuine Jordan counts at coprime moduli obey multiplication, by the independently constructed product enumeration and count uniqueness.'),)
