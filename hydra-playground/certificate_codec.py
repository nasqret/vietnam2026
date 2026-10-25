"""Bounded JSON for native proof data; decoding never establishes a theorem.

The node table is topological: every reference points to an earlier node.
Only the explicitly listed inert kernel constructors are instantiated. No
module names, pickles, scripts, imports or external proof references occur in
the wire format. Identity sharing is preserved, including annotation payloads.
The original kernel must independently check a decoded certificate.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import hmac
import json
import re

from peano_lab.kernel import formulas as f, proofs as p, terms as t
from proof_cost import ProofCostLimits, measure_proof


SCHEMA = "hydra-native-certificate-v1"
FORMULA_IDENTITY_SCHEMA = "hydra-formula-identity-v1"
VERSION = 1


class CodecError(ValueError):
    """Malformed, unsupported, cancelled or oversized certificate data."""


@dataclass(frozen=True, slots=True)
class CodecLimits:
    max_bytes: int = 512 * 1024
    max_proof_objects: int = 10_000
    max_proof_occurrences: int = 50_000
    max_proof_depth: int = 128
    max_graph_objects: int = 50_000
    max_graph_occurrences: int = 200_000
    max_graph_depth: int = 128

    def __post_init__(self):
        maxima = (512 * 1024, 10_000, 50_000, 128, 50_000, 200_000, 128)
        for field, maximum in zip(fields(self), maxima):
            value = getattr(self, field.name)
            if type(value) is not int or not 1 <= value <= maximum:
                raise CodecError(field.name + " must be a positive integer at most " + str(maximum))


DEFAULT_LIMITS = CodecLimits()

# These are field names, not aliases or dataclass introspection of unknown data.
_SPECS = (
    (t.Var, "term", (("index", "index"),)),
    (t.Zero, "term", ()),
    (t.Succ, "term", (("term", "term"),)),
    (t.Add, "term", (("left", "term"), ("right", "term"))),
    (t.Mul, "term", (("left", "term"), ("right", "term"))),
    (f.Eq, "formula", (("left", "term"), ("right", "term"))),
    (f.Bot, "formula", ()),
    (f.Imp, "formula", (("antecedent", "formula"), ("consequent", "formula"))),
    (f.And, "formula", (("left", "formula"), ("right", "formula"))),
    (f.Or, "formula", (("left", "formula"), ("right", "formula"))),
    (f.Forall, "formula", (("body", "formula"),)),
    (f.Exists, "formula", (("body", "formula"),)),
    (p.Hyp, "proof", (("i", "index"),)),
    (p.ImpIntro, "proof", (("body", "proof"),)),
    (p.ImpElim, "proof", (("f", "proof"), ("a", "proof"))),
    (p.Cut, "proof", (("proposition", "formula"), ("conclusion", "formula"), ("lemma", "proof"), ("body", "proof"))),
    (p.AndIntro, "proof", (("left", "proof"), ("right", "proof"))),
    (p.AndElimL, "proof", (("pair", "proof"),)),
    (p.AndElimR, "proof", (("pair", "proof"),)),
    (p.OrIntroL, "proof", (("proof", "proof"),)),
    (p.OrIntroR, "proof", (("proof", "proof"),)),
    (p.OrElim, "proof", (("disjunction", "proof"), ("left_case", "proof"), ("right_case", "proof"))),
    (p.BotElim, "proof", (("absurdity", "proof"),)),
    (p.ForallIntro, "proof", (("body", "proof"),)),
    (p.ForallElim, "proof", (("p", "proof"), ("t", "term"))),
    (p.ExistsIntro, "proof", (("t", "term"), ("p", "proof"))),
    (p.ExistsElim, "proof", (("p", "proof"), ("body", "proof"))),
    (p.EqRefl, "proof", (("t", "term"),)),
    (p.EqSym, "proof", (("proof", "proof"),)),
    (p.EqTrans, "proof", (("first", "proof"), ("second", "proof"))),
    (p.CongS, "proof", (("proof", "proof"),)),
    (p.CongAdd, "proof", (("left", "proof"), ("right", "proof"))),
    (p.CongMul, "proof", (("left", "proof"), ("right", "proof"))),
    (p.EqSubst, "proof", (("motive", "formula"), ("eq_proof", "proof"), ("body_proof", "proof"))),
    (p.DNE, "proof", (("proposition", "formula"),)),
    (p.Axiom, "proof", (("name", "axiom"),)),
    (p.Ind, "proof", (("motive", "formula"), ("base", "proof"), ("step", "proof"))),
)
_BY_TYPE = {kind: (category, spec) for kind, category, spec in _SPECS}
_BY_TAG = {kind.__name__: (kind, category, spec) for kind, category, spec in _SPECS}
_REFERENCES = frozenset(("term", "formula", "proof"))
for _kind, _category, _spec in _SPECS:
    if tuple(field.name for field in fields(_kind)) != tuple(name for name, _ in _spec):
        raise RuntimeError("The native constructor schema changed: " + _kind.__name__)


def _require(condition, message):
    if not condition:
        raise CodecError(message)


def _cancel(should_stop):
    if should_stop is not None and should_stop():
        raise CodecError("Certificate operation cancelled by caller.")


def _arguments(limits, should_stop):
    _require(type(limits) is CodecLimits, "Expected exact CodecLimits.")
    _require(should_stop is None or callable(should_stop), "should_stop must be callable.")
    _cancel(should_stop)


def _scalar(kind, value):
    if kind == "index":
        _require(type(value) is int and 0 <= value <= 50_000, "Invalid native variable/hypothesis index.")
    else:
        _require(type(value) is str and value in {"PA1", "PA2", "PA3", "PA4", "PA5", "PA6"},
                 "Unknown arithmetic axiom constant.")
    return value


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "Duplicate JSON object key.")
        result[key] = value
    return result


def _invalid_number(_):
    raise CodecError("Only bounded integer JSON numbers are allowed.")


def _integer(text):
    _require(len(text) <= 8, "Oversized JSON integer.")
    return int(text)


def bounded_json(raw, *, maximum):
    """Strict bounded JSON utility shared with the non-executable manifest."""
    _require(type(raw) is bytes and 0 < len(raw) <= maximum, "JSON byte limit exceeded.")
    try:
        return json.loads(raw, object_pairs_hook=_strict_object, parse_int=_integer,
                          parse_float=_invalid_number, parse_constant=_invalid_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise CodecError("Malformed JSON data.") from error


def _summary(children, occurrences, depths, limits):
    count = min(limits.max_graph_occurrences + 1, 1 + sum(occurrences[i] for i in children))
    depth = 1 + max((depths[i] for i in children), default=0)
    _require(count <= limits.max_graph_occurrences, "Expanded annotation/graph occurrence limit exceeded.")
    _require(depth <= limits.max_graph_depth, "Annotation/graph depth limit exceeded.")
    return count, depth


def _encode_graph(roots, limits, should_stop):
    records, objects, indices, active = [], [], {}, set()
    occurrences, depths, references = [], [], []
    pending = [(root, False, 1, None) for root in reversed(roots)]
    work = 0
    while pending:
        if work % 64 == 0:
            _cancel(should_stop)
        work += 1
        node, leaving, path_depth, values = pending.pop()
        identity = id(node)
        if not leaving:
            _require(identity not in active, "Cyclic native object graph.")
            _require(path_depth <= limits.max_graph_depth, "Annotation/graph depth limit exceeded.")
            if identity in indices:
                continue
            _require(len(objects) + len(active) < limits.max_graph_objects, "Native graph object limit exceeded.")
            spec = _BY_TYPE.get(type(node))
            _require(spec is not None, "Unsupported exact native constructor.")
            values = []
            for name, kind in spec[1]:
                try:
                    value = getattr(node, name)
                except AttributeError as error:
                    raise CodecError("Missing native constructor field.") from error
                if kind in _REFERENCES:
                    child_spec = _BY_TYPE.get(type(value))
                    _require(child_spec is not None and child_spec[0] == kind, "Native constructor field has the wrong category.")
                else:
                    _scalar(kind, value)
                values.append((name, kind, value))
            active.add(identity)
            pending.append((node, True, path_depth, values))
            pending.extend((value, False, path_depth + 1, None)
                           for _, kind, value in reversed(values) if kind in _REFERENCES)
            continue
        fields_record = {name: indices[id(value)] if kind in _REFERENCES else value
                         for name, kind, value in values}
        children = [indices[id(value)] for _, kind, value in values if kind in _REFERENCES]
        count, depth = _summary(children, occurrences, depths, limits)
        indices[identity] = len(records)
        records.append({"tag": type(node).__name__, "fields": fields_record})
        objects.append(node)  # Strong identity references; no recursive native hashing.
        occurrences.append(count); depths.append(depth); references.append(children)
        active.remove(identity)
    root_indices = [indices[id(root)] for root in roots]
    _require(sum(occurrences[i] for i in root_indices) <= limits.max_graph_occurrences,
             "Expanded root/annotation occurrence limit exceeded.")
    return records, root_indices, objects, occurrences, depths, references


def _proof_cost(certificate, limits, should_stop):
    cost = measure_proof(certificate, stage="final", should_stop=should_stop,
                        limits=ProofCostLimits(max_objects=limits.max_proof_objects,
                            max_occurrences=limits.max_proof_occurrences,
                            max_depth=limits.max_proof_depth, max_work=200_000))
    _require(cost["status"] == "complete", "Proof structure rejected: " + str(cost["reason"]))
    _cancel(should_stop)
    return cost


@dataclass(frozen=True, slots=True)
class DecodedCertificate:
    formula: f.Formula
    certificate: p.Proof
    sha256: str
    metrics: dict
    formula_identities: frozenset[str]


def encode_certificate(formula, certificate, *, limits=DEFAULT_LIMITS, should_stop=None):
    """Serialize exact native data; this neither checks nor claims a proof."""
    _arguments(limits, should_stop)
    _require(_BY_TYPE.get(type(formula), (None,))[0] == "formula", "Expected an exact native formula.")
    _require(_BY_TYPE.get(type(certificate), (None,))[0] == "proof", "Expected an exact native proof.")
    nodes, roots, *_ = _encode_graph((formula, certificate), limits, should_stop)
    _proof_cost(certificate, limits, should_stop)
    raw = _json({"schema": SCHEMA, "version": VERSION, "nodes": nodes,
                 "roots": {"formula": roots[0], "certificate": roots[1]}}) + b"\n"
    _require(len(raw) <= limits.max_bytes, "Certificate exceeds its byte limit.")
    return raw


def decode_certificate(raw, *, expected_sha256=None, limits=DEFAULT_LIMITS, should_stop=None):
    """Decode whitelisted inert objects, preserving DAG identity; no kernel call."""
    _arguments(limits, should_stop)
    _require(type(raw) is bytes and 0 < len(raw) <= limits.max_bytes, "Certificate exceeds its byte limit.")
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None:
        _require(type(expected_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", expected_sha256), "Malformed expected certificate hash.")
        _require(hmac.compare_digest(digest, expected_sha256), "Certificate hash mismatch.")
    document = bounded_json(raw, maximum=limits.max_bytes)
    _require(type(document) is dict and set(document) == {"schema", "version", "nodes", "roots"}, "Invalid certificate envelope fields.")
    _require(document["schema"] == SCHEMA and type(document["version"]) is int and document["version"] == VERSION, "Unsupported certificate version.")
    nodes = document["nodes"]
    _require(type(nodes) is list and 1 <= len(nodes) <= limits.max_graph_objects, "Invalid node-table size.")
    objects, categories, occurrences, depths, references = [], [], [], [], []
    for index, node in enumerate(nodes):
        if index % 64 == 0:
            _cancel(should_stop)
        _require(type(node) is dict and set(node) == {"tag", "fields"}, "Invalid node fields.")
        _require(type(node["tag"]) is str and node["tag"] in _BY_TAG, "Unknown constructor tag.")
        constructor, category, spec = _BY_TAG[node["tag"]]
        values = node["fields"]
        _require(type(values) is dict and set(values) == {name for name, _ in spec}, "Constructor fields differ from the explicit schema.")
        arguments, children = {}, []
        for name, kind in spec:
            value = values[name]
            if kind in _REFERENCES:
                _require(type(value) is int and 0 <= value < index, "A reference must point strictly backward.")
                _require(categories[value] == kind, "Reference has the wrong native category.")
                arguments[name] = objects[value]; children.append(value)
            else:
                arguments[name] = _scalar(kind, value)
        count, depth = _summary(children, occurrences, depths, limits)
        objects.append(constructor(**arguments)); categories.append(category)
        occurrences.append(count); depths.append(depth); references.append(children)
    roots = document["roots"]
    _require(type(roots) is dict and set(roots) == {"formula", "certificate"}, "Invalid root fields.")
    for name, category in (("formula", "formula"), ("certificate", "proof")):
        index = roots[name]
        _require(type(index) is int and 0 <= index < len(objects) and categories[index] == category, "Invalid root reference or category.")
    pending, reachable = list(roots.values()), set()
    while pending:
        if len(reachable) % 64 == 0:
            _cancel(should_stop)
        index = pending.pop()
        if index not in reachable:
            reachable.add(index); pending.extend(references[index])
    _require(len(reachable) == len(nodes), "Unreachable nodes are not allowed.")
    total = sum(occurrences[i] for i in roots.values())
    _require(total <= limits.max_graph_occurrences, "Expanded root/annotation occurrence limit exceeded.")
    formula, certificate = objects[roots["formula"]], objects[roots["certificate"]]
    cost = _proof_cost(certificate, limits, should_stop)
    metrics = {"proof_cost": cost, "graph_objects": len(objects),
               "graph_occurrences": total, "graph_depth": max(depths[i] for i in roots.values()),
               "graph_scope": "Formula and certificate roots, including term/formula annotations; sharing expanded for occurrences.",
               "kernel_check_performed": False}
    hashes = _structural_hashes(nodes, should_stop)
    formula_ids = frozenset(_formula_hash(hashes[i]) for i, category in enumerate(categories)
                            if category == "formula")
    return DecodedCertificate(formula, certificate, digest, metrics, formula_ids)


def _structural_hashes(nodes, should_stop):
    hashes = []
    for index, node in enumerate(nodes):
        if index % 64 == 0:
            _cancel(should_stop)
        _, _, spec = _BY_TAG[node["tag"]]
        values = {name: hashes[node["fields"][name]] if kind in _REFERENCES else node["fields"][name]
                  for name, kind in spec}
        hashes.append(hashlib.sha256(_json({"tag": node["tag"], "fields": values})).hexdigest())
    return hashes


def _formula_hash(root_hash):
    return hashlib.sha256(_json({"schema": FORMULA_IDENTITY_SCHEMA, "root": root_hash})).hexdigest()


def formula_identity(formula, *, limits=DEFAULT_LIMITS, should_stop=None):
    """Structural de Bruijn AST hash, independent of Python object sharing.

Binder spellings disappear when the caller parses with the native parser.
This is not normalization, theorem equivalence, or a check that a formula is
closed. Free variables remain explicit de Bruijn indices.
"""
    _arguments(limits, should_stop)
    _require(_BY_TYPE.get(type(formula), (None,))[0] == "formula", "Expected an exact native formula.")
    nodes, roots, *_ = _encode_graph((formula,), limits, should_stop)
    return _formula_hash(_structural_hashes(nodes, should_stop)[roots[0]])


__all__ = ["SCHEMA", "VERSION", "FORMULA_IDENTITY_SCHEMA", "CodecError", "CodecLimits",
           "DEFAULT_LIMITS", "DecodedCertificate", "bounded_json", "encode_certificate",
           "decode_certificate", "formula_identity"]
