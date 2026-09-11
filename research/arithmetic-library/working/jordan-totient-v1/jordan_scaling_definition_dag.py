"""One additive local identity for natural beta-coordinate scaling.

ND0440 is syntax only. All 493 historical definition objects are preserved;
positivity, canonical bounds, divisibility, bijectivity and counts are not
clauses of this relation. They are separate theorem statements.
"""
from hashlib import sha256
import importlib.util
from pathlib import Path
from types import MappingProxyType

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.defined_syntax import DefinitionSpec, _definition

HERE = Path(__file__).resolve().parent
SOURCE_PINS = MappingProxyType({
    '../jordan-orders-fields-v1/existence_definition_dag.py':
        '6bc11df67dc3b5de1e734cc818876cd87e19e44e66de23958dee09c24cf2ec71',
    'jordan_tuple_scaling_candidate.py':
        '3cac74be7ead60c091c9a5b6941631e4ddcd6e5bf49b2e018376f94558051bd2',
})


def _load(relative):
    path = HERE / relative
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError('scaling definition provider must be an ordinary bounded source')
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != SOURCE_PINS[relative]:
        raise ValueError('reviewed scaling definition source changed: ' + relative)
    loader = importlib.util.spec_from_file_location('_scaling_dag_' + path.stem, path)
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    if path.read_bytes() != raw:
        raise ValueError('definition provider changed during loading')
    return module


BASE = _load('../jordan-orders-fields-v1/existence_definition_dag.py')
SOURCE = _load('jordan_tuple_scaling_candidate.py')
PREVIOUS = BASE.ALL_DEFINITIONS
PARAMETERS = ('p', 'b', 'c', 'd', 'e', 'k')
NEW_DEFINITIONS = (_definition(
    stable_id='ND0440', name='JordanTupleScaling', parameters=PARAMETERS,
    template_source=SOURCE.tuple_scaling_relation(*PARAMETERS, tag='scaling_definition'),
    conceptual_dependencies=('Lt', 'BetaAt'),
    summary='Every actual decoded image coordinate equals p times its source coordinate below k. No positivity, canonical bound, existence, divisibility, injectivity or count equation is assumed.',
    category='working_jordan_scaling', priority='P2'),)


def extend_definitions(previous):
    snapshot = tuple(previous.items())
    known = dict(snapshot)
    BASE.VALIDATOR._validate(known)
    ids = {d.stable_id for d in known.values()}
    for definition in NEW_DEFINITIONS:
        if type(definition) is not DefinitionSpec or definition.name in known or definition.stable_id in ids:
            raise ValueError('scaling definition would shadow an existing identity')
        parents = definition.conceptual_dependencies
        if len(set(parents)) != len(parents) or not set(parents) <= known.keys():
            raise ValueError('missing, duplicate or forward scaling definition parent')
        if any(d.arity == definition.arity and d.template_formula == definition.template_formula for d in known.values()):
            raise ValueError('an exact relation already has a definition identity')
        renamed = tuple('argument' + str(i) for i in range(definition.arity))
        if definition.template_formula != parse_formula_in_context(
                SOURCE.tuple_scaling_relation(*renamed, tag='renamed_scaling'), list(renamed)):
            raise ValueError('scaling definition builder captures a parameter')
        known[definition.name] = definition
        ids.add(definition.stable_id)
    BASE.VALIDATOR._validate(known)
    if tuple(previous.items()) != snapshot or any(known[name] is not value for name, value in snapshot):
        raise ValueError('an existing definition object changed')
    return MappingProxyType(known)


if len(PREVIOUS) != 493:
    raise ValueError('frozen historical definition inventory changed')
ALL_DEFINITIONS = extend_definitions(PREVIOUS)


def definition_closure(names):
    return BASE.VALIDATOR.definition_closure(names, registry=ALL_DEFINITIONS)


def definition_dag(names=('JordanTupleScaling',)):
    definitions = definition_closure(names)
    return dict(schema='working-jordan-scaling-definition-dag-v1', syntax_only=True,
        alpha_admitted=False, stable_changed=False,
        roots=[ALL_DEFINITIONS[name].stable_id for name in names],
        nodes=[dict(id=d.stable_id, name=d.name, parameters=list(d.parameters),
                    expanded_formula=d.template_source, summary=d.summary) for d in definitions],
        edges=[dict(source=ALL_DEFINITIONS[parent].stable_id, target=d.stable_id,
                    kind='definition_uses_definition')
               for d in definitions for parent in d.conceptual_dependencies])
