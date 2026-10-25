"""Bounded E-specific dependency hints, not imported Peano certificates.

The scoped FOF exporter supplies only the actual focused assumptions and the
six exact PA axioms. Addition/multiplication remain uninterpreted symbols;
there is no integer theory, induction schema, or hidden lemma library.
"""
import hashlib
import re

from adviser_protocol import MAX_OUTPUT, ProtocolError, external_request
from p9_bridge_common import P9Advisor
from vampire_bridge import (UnsupportedProof, _call, _name, _native_hints, _split_top,
                            export_state)


MAX_RECORDS = 1024
MAX_DAG_DEPTH = 128
REFUTATION_STATUSES = frozenset({"Theorem", "ContradictoryAxioms", "Unsatisfiable"})


def _source(value, depth=0):
    if depth > 64:
        raise UnsupportedProof("E proof source nesting exceeds its bound.")
    try:
        return (_name(value),), ()
    except UnsupportedProof:
        pass
    kind, args = _call(value)
    if kind == "file" and len(args) == 2:
        return (), (_name(args[1]),)
    if kind == "introduced" and args and args[0] in {"definition", "tautology", "assumption"}:
        # Fresh solver definitions are not native axioms. No native fact is
        # reconstructed from one unless its original input ancestors are used.
        return (), ()
    if (kind != "inference" or len(args) != 3 or not args[2].startswith("[")
            or not args[2].endswith("]")):
        raise UnsupportedProof("Unsupported E inference source.")
    refs, inputs = [], []
    children = args[2][1:-1].strip()
    for child in _split_top(children) if children else ():
        parent_refs, parent_inputs = _source(child, depth + 1)
        refs.extend(parent_refs)
        inputs.extend(parent_inputs)
        if len(refs) + len(inputs) > MAX_RECORDS:
            raise UnsupportedProof("E inference fan-in exceeds its bound.")
    return tuple(refs), tuple(inputs)


def proof_used_inputs(stdout, allowed_inputs):
    """Only ancestors of the final false clause; no claim of proof checking."""
    if type(stdout) is not str or len(stdout.encode("utf-8")) > MAX_OUTPUT:
        raise UnsupportedProof("E output exceeds 256 KiB.")
    begin = list(re.finditer(r"(?m)^[%#]\s*SZS output start CNFRefutation\s*\r?$", stdout))
    end = list(re.finditer(r"(?m)^[%#]\s*SZS output end CNFRefutation\s*\r?$", stdout))
    if len(begin) != 1 or len(end) != 1 or end[0].start() <= begin[0].end():
        raise UnsupportedProof("E did not provide one complete CNFRefutation block.")
    block = stdout[begin[0].end():end[0].start()]
    block = "\n".join(row for row in block.splitlines() if not row.lstrip().startswith(("%", "#")))
    statements = _split_top(block, ".")
    if statements.pop() or not statements or len(statements) > MAX_RECORDS:
        raise UnsupportedProof("Incomplete or oversized E proof records.")
    records, roots = {}, []
    for statement in statements:
        kind, args = _call(statement)
        if kind not in {"fof", "cnf"} or len(args) not in (4, 5):
            raise UnsupportedProof("Only E's sourced untyped FOF/CNF records are accepted.")
        label = _name(args[0])
        if label in records:
            raise UnsupportedProof("Duplicate E proof record.")
        records[label] = _source(args[3])
        if re.fullmatch(r"\(*\s*\$false\s*\)*", args[2]):
            roots.append(label)
    if not roots:
        raise UnsupportedProof("The complete E block has no final false clause.")
    active, visited, used = set(), set(), []

    def visit(label, depth=0):
        if label in active or depth > MAX_DAG_DEPTH:
            raise UnsupportedProof("Cyclic or too-deep E proof dependencies.")
        if label in visited:
            return
        if label not in records:
            raise UnsupportedProof("An E inference parent is missing.")
        active.add(label)
        references, inputs = records[label]
        for parent in references:
            visit(parent, depth + 1)
        for name in inputs:
            if name not in allowed_inputs:
                raise UnsupportedProof("E referred to an input not exported from this state.")
            if name not in used:
                used.append(name)
        active.remove(label)
        visited.add(label)

    visit(roots[-1])
    return tuple(name for name in used if name != "hydra_goal"), len(visited)


class EAdvisor(P9Advisor):
    def __init__(self, session, runner, *, capabilities, authority_identity):
        super().__init__("e", session, runner, capabilities=capabilities,
                         authority_identity=authority_identity)

    def prepare(self, state, context):
        problem = export_state(state)
        request = external_request("e", problem.text.encode("utf-8"), context, self.runner.identity)
        return problem, request

    def decode(self, problem, request, execution):
        raw = execution.get("stdout")
        if type(raw) is not bytes or len(raw) > MAX_OUTPUT:
            raise ProtocolError("E output is not a bounded byte stream.")
        try:
            text = raw.decode("utf-8", "strict")
        except UnicodeError as error:
            raise ProtocolError("Invalid E output encoding.") from error
        versions = re.findall(r"(?m)^[%#]\s*Version:\s*([^\r\n]+)$", text)
        if not versions or any(not re.fullmatch(r"(?:E\s+)?3\.3\.6(?:\s+.*)?", version) for version in versions):
            raise ProtocolError("No recognized output from the pinned E backend.")
        statuses = re.findall(r"(?m)^[%#]\s*SZS status ([A-Za-z]+)\b", text)
        if len(statuses) != 1:
            raise ProtocolError("Missing or ambiguous E SZS status.")
        evidence = {"szs_status": statuses[0], "proof_checked": False,
                    "output_sha256": hashlib.sha256(raw).hexdigest(),
                    "translation": "focused classical FOF with exact PA1-PA6; no induction/library"}
        if statuses[0] not in REFUTATION_STATUSES:
            return "no_refutation", [], evidence
        allowed = {premise.tptp_name for premise in problem.premises} | {"hydra_goal"}
        try:
            used, nodes = proof_used_inputs(text, allowed)
        except UnsupportedProof as error:
            raise ProtocolError(str(error)) from error
        suggestions = _native_hints(problem, used, 12)
        for suggestion in suggestions:
            suggestion["source"] = "e"
            suggestion["reason"] = suggestion["reason"].replace("Vampire", "E")
        evidence.update(used_inputs=list(used), reachable_records=nodes,
                        native_reconstruction_required=True)
        return "advisory_refutation_without_reconstruction", suggestions, evidence
