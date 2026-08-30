"""Additive G091 polynomial prerequisites over the immutable Alpha-v31 base.

This is syntax selection and input authentication, never proof acceptance.
The existing assembler, parent adapter, kernel and all old releases remain
unchanged. The already checked G009 research tranche is a novelty comparand,
not a newly admitted parent or a counted polynomial prerequisite.
"""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import importlib.util
from pathlib import Path
import re
import sys

import constructive_g009_support as inherited
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT, HERE = inherited.ROOT, Path(__file__).resolve().parent
if HERE != ROOT/'scripts':
    raise RuntimeError('polynomial support must reside in the repository scripts directory')
MATH_DIRECTORY = inherited.MATH_DIRECTORY
closure = inherited.closure
FilePin, Factory = inherited.FilePin, inherited.Factory
CandidateState, SupportSelection = inherited.CandidateState, inherited.SupportSelection
PolynomialDivisionError = inherited.G009Error
canonical, bounded_bytes, check_pin = inherited.canonical, inherited.bounded_bytes, inherited.check_pin
current_parent_specs, parent_seed_paths = inherited.current_parent_specs, inherited.parent_seed_paths
select_support, dependency_cone = inherited.select_support, inherited.dependency_cone
_repository_path = inherited._repository_path
PARENT_COUNT, PARENT_STABLE_COUNT = inherited.PARENT_COUNT, inherited.PARENT_STABLE_COUNT
PARENT_IDENTITY_SHA256 = inherited.PARENT_IDENTITY_SHA256
PARENT_ENROLLMENT_SHA256 = inherited.PARENT_ENROLLMENT_SHA256
PARENT_CONTROL_PINS, PARENT_CATALOG_PINS = inherited.PARENT_CONTROL_PINS, inherited.PARENT_CATALOG_PINS
MAX_SOURCE_BYTES, MAX_CATALOG_COMPONENT_BYTES = inherited.MAX_SOURCE_BYTES, inherited.MAX_CATALOG_COMPONENT_BYTES

FACTORIES = (
    Factory('prime_field_polynomial_subtraction_candidate',26),
    Factory('prime_field_polynomial_trim_candidate',22),
    Factory('prime_field_polynomial_monic_candidate',20),
    Factory('prime_field_polynomial_synthetic_candidate',17),
)
EXPECTED_NEW_COUNT = 85
PRIOR_RESEARCH_COUNT = 90
# Filled only after the actual mathematical sources and ordered rows freeze.
# Empty identities are a hard final-check failure, not an authoring receipt.
MATH_SOURCE_PINS: tuple[FilePin,...] = (
    FilePin('peano-lab/py/peano_lab/library/prime_field_polynomial_subtraction_candidate.py',27165,
            'd08562b26c683a891e58a4b10faa495867d7487054b1ee7c99f091dd1c707b2b'),
    FilePin('peano-lab/py/peano_lab/library/prime_field_polynomial_trim_candidate.py',26425,
            '1125c02fd11646efaa20963380ba1086e18551f2c89b242b8900a8043d358e4c'),
    FilePin('peano-lab/py/peano_lab/library/prime_field_polynomial_monic_candidate.py',25658,
            '3bf93aff71b48a332920b1a6174e44167bf78238caac3b6d35634f3591582eef'),
    FilePin('peano-lab/py/peano_lab/library/prime_field_polynomial_synthetic_candidate.py',25265,
            '0938e369e528666e8e52c5d49b157a12bd00bf50150783182b3b5ebc36b02022'),
)
NEW_SPECS_SHA256 = '93663cc10d2d034fb933a60a914f1656fd0beb8d715bbbab8d8e1359c780ab11'


def require_final_source_pins():
    inherited.require_final_source_pins()
    if (tuple(pin.path for pin in MATH_SOURCE_PINS) != tuple(owner.path for owner in FACTORIES)
            or re.fullmatch(r'[0-9a-f]{64}',NEW_SPECS_SHA256) is None
            or sum(owner.count for owner in FACTORIES) != EXPECTED_NEW_COUNT):
        raise PolynomialDivisionError('the complete polynomial source/specification pins are not sealed')
    for pin in MATH_SOURCE_PINS:
        check_pin(pin,ROOT,MAX_SOURCE_BYTES)


def load_candidate_state(*, final=False):
    if type(final) is not bool:
        raise PolynomialDivisionError('final must be an explicit Boolean')
    if final:
        require_final_source_pins()
    rows,sources=[],[]
    for owner in FACTORIES:
        path=MATH_DIRECTORY/(owner.module+'.py')
        raw=bounded_bytes(path,MAX_SOURCE_BYTES)
        pin=FilePin(owner.path,len(raw),sha256(raw).hexdigest())
        if final and pin != MATH_SOURCE_PINS[len(sources)]:
            raise PolynomialDivisionError('a frozen polynomial source changed')
        qualified='peano_lab.library.'+owner.module
        previous=sys.modules.get(qualified)
        if previous is not None and Path(getattr(previous,'__file__','')).resolve()!=path.resolve():
            raise PolynomialDivisionError('an additive polynomial module shadows another file')
        spec=importlib.util.spec_from_file_location(qualified,path)
        if spec is None or spec.loader is None:
            raise PolynomialDivisionError('an exact polynomial source is not loadable')
        module=importlib.util.module_from_spec(spec)
        sys.modules[qualified]=module
        exec(compile(raw,str(path),'exec'),module.__dict__)
        factory=getattr(module,owner.factory,None)
        if not callable(factory) or getattr(factory,'__module__',None)!=qualified:
            raise PolynomialDivisionError('the exact polynomial factory is missing')
        values=factory(TheoremSpec)
        if type(values) is not tuple or len(values)!=owner.count:
            raise PolynomialDivisionError('the complete polynomial factory inventory changed')
        rows.extend(values); sources.append(pin)
        if bounded_bytes(path,MAX_SOURCE_BYTES)!=raw:
            raise PolynomialDivisionError('a polynomial source changed during its factory call')
    rows=tuple(rows)
    closure._validate_frontier(rows)
    digest=closure._specs_digest(rows)
    if len(rows)!=EXPECTED_NEW_COUNT or final and digest!=NEW_SPECS_SHA256:
        raise PolynomialDivisionError('the exact complete polynomial specifications changed')
    return CandidateState(rows,tuple(sources),digest)


def all_new_rows(*, final=False):
    return load_candidate_state(final=final).rows


def statement_duplicates(new_rows):
    duplicates=list(inherited.statement_duplicates(new_rows))
    index={}
    for row in new_rows:
        encoded=FormulaArena().freeze(_closed_formula(row.statement)).to_json()
        index.setdefault(sha256(encoded.encode()).digest(),[]).append((row.name,encoded))
    previous=inherited.all_new_rows(final=True)
    if len(previous)!=PRIOR_RESEARCH_COUNT:
        raise PolynomialDivisionError('the separate G009 research inventory changed')
    for row in previous:
        encoded=FormulaArena().freeze(_closed_formula(row.statement)).to_json()
        duplicates.extend((name,row.name) for name,other in index.get(sha256(encoded.encode()).digest(),())
                          if encoded==other)
    return tuple(duplicates)


def state_binding(state, *, final=False):
    if final:
        require_final_source_pins()
    # The existing function authenticates the unmodified parent controls,
    # 39 inherited proof-data providers and supplied syntax identities.
    parent_binding=inherited.state_binding(state,final=False)
    controls=[]
    for name in ('constructive_polynomial_division_support.py',
                 'export_constructive_polynomial_division.py',
                 'constructive_polynomial_division_checkpoints.py',
                 'check_constructive_polynomial_division.py'):
        path=HERE/name
        raw=bounded_bytes(path,MAX_SOURCE_BYTES)
        controls.append((_repository_path(path),len(raw),sha256(raw).hexdigest()))
    return sha256(canonical({'parent_binding':parent_binding,'controls':controls,
        'sources':[asdict(pin) for pin in state.sources],'specs_sha256':state.specs_sha256,
        'factories':[asdict(owner) for owner in FACTORIES],
        'expected_new_count':EXPECTED_NEW_COUNT,'prior_research_count':PRIOR_RESEARCH_COUNT,
        'frozen_math_pins':[asdict(pin) for pin in MATH_SOURCE_PINS],
        'frozen_specs_sha256':NEW_SPECS_SHA256,'final_source_pins_required':final})).hexdigest()
