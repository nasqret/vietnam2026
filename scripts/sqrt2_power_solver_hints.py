"""Bound TSTP dependency selection, followed by a small ordinary HA proof.

This is NOT a TSTP proof translator. Derived classical/Skolem formulas are
opaque text, never HA terms or premises. Only original, alpha-equivalent input
declarations and a bounded dependency graph select native laws. Every selected
law is regenerated from its actual source; no theorem marker grants authority.
Currently only the exact frozen P08 supporting leaf is reconstructible.
Call reconstruction only inside the pilot's existing process/resource guard.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from sqrt2_power_automation_baseline import runtime, source_pins as base_pins
from sqrt2_power_external import validate_problem, validate_export, source_pins as external_pins
from sqrt2_power_native import ROOT, BASIS_NAMES, Basis, closed_formula, instantiate, close_proof
from sqrt2_power_pilot_contracts import canonical, contracts
from sqrt2_power_pilot_results import ARCHIVE, archive_member
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Bot
from peano_lab.kernel.proofs import CongMul, EqRefl, EqSym, EqTrans, Hyp
from peano_lab.kernel.terms import Var
from peano_lab.library.proof_bundle import encode_formula

SCHEMA = "sqrt2-power-tstp-premise-selection-v1"
P08_SOURCE = "forall d u v m. d*v=u -> d*(m*v)=m*u"
P08_AST_SHA256 = "5ab0ba252962549290db0651035439a1e1ab719b485f7c91893895b7a9ce8352"
P08_CONTRACT_SHA256 = "2004ac46733eb7a773ca2b8670bbbe6d8a39c26da383b144b9ae0d040c20adac"
MAX_LOG_BYTES = 2 * 1024**2
MAX_RECORDS = 1024
MAX_DEPTH = 128
SELECTED_LAWS = frozenset({"mul_assoc", "mul_comm"})
_ATOM = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
_TOKEN = re.compile(r"\s*(=>|!=|\$false|[A-Za-z][A-Za-z0-9_]*|[!?~&|=()\[\],:])")
_RULES = {
    "eprover": frozenset({"assume_negation", "fof_nnf", "skolemize", "variable_rename",
        "shift_quantors", "split_conjunct", "cn", "rw", "spm"}),
    "vampire": frozenset({"negated_conjecture", "ennf_transformation", "flattening",
        "skolemize", "cnf_transformation", "resolution", "superposition",
        "forward_demodulation", "forward_subsumption_resolution"}),
}


class HintError(ValueError):
    """Unsupported, unbound or insufficient hint; no fallback to full-ring search."""


def source_pins():
    result = base_pins()
    paths = [Path(__file__).resolve()]
    paths.extend(ROOT / "scripts" / name for name in (
        "sqrt2_power_external.py", "sqrt2_power_native.py", "sqrt2_power_pilot_contracts.py",
        "sqrt2_power_campaign_spec.py", "sqrt2_power_pilot_results.py"))
    paths.extend(ROOT / "peano-lab/py/peano_lab/library" / name
                 for name in ("__init__.py", "theorems.py", "proof_bundle.py"))
    for path in paths:
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    return result


def _split(text, separator=","):
    """Split only outside balanced parentheses/brackets and simple quotes."""
    result, start, stack, quote = [], 0, [], None
    for index, char in enumerate(text):
        if quote:
            if char == "\\":
                raise HintError("escaped TSTP atoms are outside this reader")
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char in "([":
            stack.append(char)
            if len(stack) > MAX_DEPTH:
                raise HintError("TSTP nesting exceeds bound")
        elif char in ")]":
            if not stack or stack.pop() != (")" == char and "(" or "["):
                raise HintError("unbalanced TSTP structure")
        elif char == separator and not stack:
            result.append(text[start:index].strip())
            start = index + 1
    if stack or quote:
        raise HintError("unterminated TSTP structure")
    result.append(text[start:].strip())
    return result


def _atom(text):
    if len(text) >= 2 and text[0] == text[-1] == "'":
        text = text[1:-1]
    if not _ATOM.fullmatch(text):
        raise HintError("unsupported TSTP name")
    return text


def _application(text, name, arity):
    match = re.fullmatch(re.escape(name) + r"\s*\((.*)\)", text, re.S)
    if match is None:
        raise HintError("unsupported TSTP annotation")
    args = _split(match.group(1))
    if len(args) != arity:
        raise HintError("incorrect TSTP annotation arity")
    return args


def _list(text):
    if not text.startswith("[") or not text.endswith("]"):
        raise HintError("expected a TSTP annotation list")
    return _split(text[1:-1]) if text[1:-1].strip() else []


class _InputFormula:
    """Alpha-normalized guarded FOF input syntax, NOT a classical HA decoder."""
    def __init__(self, text):
        self.tokens = []
        cursor = 0
        while cursor < len(text):
            if not text[cursor:].strip():
                break
            match = _TOKEN.match(text, cursor)
            if match is None:
                raise HintError("unsupported symbol in original input declaration")
            self.tokens.append(match.group(1))
            cursor = match.end()
            if len(self.tokens) > 8192:
                raise HintError("original input declaration exceeds token bound")
        self.index = 0

    def take(self, expected=None):
        if self.index == len(self.tokens):
            raise HintError("incomplete original formula")
        token = self.tokens[self.index]
        if expected is not None and token != expected:
            raise HintError("unexpected original formula token")
        self.index += 1
        return token

    def peek(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def term(self, scope, depth):
        if depth > MAX_DEPTH:
            raise HintError("original formula exceeds depth bound")
        name = self.take()
        if name[0].isupper():
            if name not in scope:
                raise HintError("free or captured original variable")
            return ("var", tuple(reversed(scope)).index(name))
        arity = {"zero": 0, "s": 1, "add": 2, "mul": 2}.get(name)
        if arity is None:
            raise HintError("unknown original term symbol")
        args = []
        if arity:
            self.take("(")
            for index in range(arity):
                if index:
                    self.take(",")
                args.append(self.term(scope, depth + 1))
            self.take(")")
        return (name, *args)

    def formula(self, scope=(), depth=0, minimum=0):
        if depth > MAX_DEPTH:
            raise HintError("original formula exceeds depth bound")
        token = self.peek()
        if token in ("!", "?"):
            quantifier = self.take()
            self.take("[")
            names = [self.take()]
            while self.peek() == ",":
                self.take(",")
                names.append(self.take())
            self.take("]")
            self.take(":")
            if (any(not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", n) for n in names)
                or len(set(names)) != len(names) or set(names) & set(scope)):
                raise HintError("duplicate, shadowed or captured original binder")
            left = self.formula(scope + tuple(names), depth + 1)
            for _ in names:
                left = (quantifier, left)
        elif token == "(":
            self.take("(")
            left = self.formula(scope, depth + 1)
            self.take(")")
        elif token == "~":
            self.take("~")
            left = ("~", self.formula(scope, depth + 1, 3))
        elif token == "$false":
            self.take()
            left = ("false",)
        elif token == "nat":
            self.take("nat")
            self.take("(")
            left = ("nat", self.term(scope, depth + 1))
            self.take(")")
        else:
            lhs = self.term(scope, depth + 1)
            relation = self.take()
            if relation not in ("=", "!="):
                raise HintError("only equality and natural guards are supported")
            left = (relation, lhs, self.term(scope, depth + 1))
        priorities = {"=>": 0, "|": 1, "&": 2}
        while self.peek() in priorities and priorities[self.peek()] >= minimum:
            operator = self.take()
            priority = priorities[operator]
            right = self.formula(scope, depth + 1, priority if operator == "=>" else priority + 1)
            left = (operator, left, right)
        return left

    def parse(self):
        try:
            result = self.formula()
        except RecursionError as exc:
            raise HintError("original formula exceeds parser recursion bound") from exc
        if self.index != len(self.tokens):
            raise HintError("trailing or unsupported original formula syntax")
        return result


def _records(text):
    text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("%", "#")))
    pieces = _split(text, ".")
    if pieces[-1]:
        raise HintError("unterminated TSTP record")
    if not 1 <= len(pieces) - 1 <= MAX_RECORDS:
        raise HintError("TSTP record count exceeds bound")
    result = []
    for piece in pieces[:-1]:
        match = re.fullmatch(r"(fof|cnf)\s*\((.*)\)", piece, re.S)
        if not match:
            raise HintError("only FOF/CNF records are supported")
        fields = _split(match.group(2))
        if len(fields) not in (3, 4, 5):
            raise HintError("unsupported TSTP record arity")
        if len(fields) == 5 and fields[4] != "['proof']":
            raise HintError("unsupported TSTP useful-info annotation")
        result.append((_atom(fields[0]), _atom(fields[1]), fields[2], fields[3] if len(fields) >= 4 else None))
    return result


def _dependencies(annotation, solver, rules, depth=0):
    if depth > MAX_DEPTH:
        raise HintError("dependency annotations exceed depth bound")
    if not annotation.startswith("inference"):
        return {_atom(annotation)}
    rule, attributes, parent_list = _application(annotation, "inference", 3)
    rule = _atom(rule)
    if rule not in _RULES[solver]:
        raise HintError("unsupported solver proof rule: " + rule)
    rules.add(rule)
    for attribute in _list(attributes):
        if re.fullmatch(r"status\((thm|cth|esa)\)", attribute):
            continue
        # Vampire's Skolem annotations are observed syntax only, never imported.
        if solver == "vampire" and rule == "skolemize":
            if attribute.startswith("new_symbols"):
                kind, names = _application(attribute, "new_symbols", 2)
                if kind != "skolem" or not _list(names):
                    raise HintError("unsupported new-symbol annotation")
                for name in _list(names):
                    _atom(name)
                continue
            if attribute.startswith("skolemize"):
                variable, symbol = _application(attribute, "skolemize", 2)
                if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", variable):
                    raise HintError("unsupported Skolem annotation variable")
                _atom(symbol)
                continue
        raise HintError("unsupported solver inference annotation")
    parents = _list(parent_list)
    if not parents:
        raise HintError("inference has no original dependency ancestry")
    dependencies = set()
    for parent in parents:
        dependencies.update(_dependencies(parent, solver, rules, depth + 1))
    return dependencies


def _bound_inputs(problem, observed, contract):
    if type(contract) is not dict:
        raise HintError("contract must be exact JSON data")
    expected = next(row for row in contracts() if row["pilot_id"] == "P08")
    if (canonical(contract) != canonical(expected) or contract["contract_sha256"] != P08_CONTRACT_SHA256
        or contract["statement_ast_sha256"] != P08_AST_SHA256 or contract["source"] != P08_SOURCE):
        raise HintError("changed frozen P08 contract")
    checked = validate_problem(problem)
    if checked["format"] != "tptp" or checked["target"]["source"] != P08_SOURCE:
        raise HintError("changed target or non-TPTP export")
    allowed = {row["name"]: row["source"] for row in contract["allowed_external_premises"]}
    if set(allowed) != BASIS_NAMES or len(allowed) != 15:
        raise HintError("changed original fifteen-law allowlist")
    premises = []
    for row in checked["premises"]:
        if row["name"] not in allowed or row["source"] != allowed[row["name"]]:
            raise HintError("unknown or changed original premise")
        premises.append((row["name"], row["source"]))
    validate_export(checked, P08_SOURCE, tuple(premises))
    if type(observed) is not dict or observed.get("solver") not in _RULES:
        raise HintError("only recorded E/Vampire observations are supported")
    required = {"target_ast_sha256": checked["target"]["ast_sha256"],
        "input_sha256": checked["input_sha256"], "export_sha256": checked["export_sha256"],
        "premises": [{"name": r["name"], "ast_sha256": r["ast_sha256"]} for r in checked["premises"]],
        "source_pins": external_pins(), "authority": "untrusted_classical_search_hint_only",
        "ha_checked": False, "proof_log_checked": False, "ha_translation_verified": False,
        "solver_proofs_reconstructed": 0, "model_proof_search_calls": 0, "IR_obligations_closed": 0}
    if any(canonical(observed.get(key)) != canonical(value) for key, value in required.items()):
        raise HintError("solver observation changed its exact input or authority binding")
    process = observed.get("process")
    if type(process) is not dict or type(observed.get("argv")) is not list:
        raise HintError("missing actual solver process observation")
    try:
        limits = runtime().ProcessLimits(**process["limits"])
        runtime().validate_process_record(process, command=tuple(observed["argv"]), limits=limits,
            input_bytes=checked["input"].encode(), success_codes=(0,))
    except (KeyError, TypeError, ValueError) as exc:
        raise HintError("invalid bound process observation") from exc
    if (process["reason"] != "exited" or process["returncode"] != 0
        or process["output_truncated"] or process["output_encoding"] != "utf-8"
        or process["stdout_bytes"] > MAX_LOG_BYTES):
        raise HintError("no complete successful lossless TSTP log")
    return checked, process["stdout"]


def extract_premise_hint(problem, observed, contract):
    """Consume only dependency selection; return diagnostics, NEVER a certificate."""
    before = source_pins()
    checked, text = _bound_inputs(problem, observed, contract)
    starts = list(re.finditer(r"^[%#]\s*SZS output start (Proof|CNFRefutation)\b[^\n]*\n", text, re.M))
    ends = list(re.finditer(r"^[%#]\s*SZS output end (Proof|CNFRefutation)\b[^\n]*", text, re.M))
    if len(starts) != 1 or len(ends) != 1 or starts[0].end() >= ends[0].start() or starts[0][1] != ends[0][1]:
        raise HintError("missing or ambiguous complete proof section")
    original = {name: (role, _InputFormula(formula).parse())
                for name, role, formula, annotation in _records(checked["input"])
                if annotation is None}
    exported_names = {row["export_name"]: row["name"] for row in checked["premises"]}
    graph, inputs, rules = {}, {}, set()
    records = _records(text[starts[0].end():ends[0].start()])
    for name, role, formula, annotation in records:
        if name in graph or annotation is None:
            raise HintError("duplicate node or missing source annotation")
        if annotation.startswith("file"):
            file_name, original_name = _application(annotation, "file", 2)
            original_name = _atom(original_name)
            if file_name != "'<stdin>'" or original_name not in {"target", *exported_names}:
                raise HintError("unknown original premise or foreign source file")
            expected_role, expected_formula = original[original_name]
            valid_roles = {"conjecture"} if original_name == "target" else {"axiom", "hypothesis"}
            if role not in valid_roles or _InputFormula(formula).parse() != expected_formula:
                raise HintError("original declaration changed formula, variables or role")
            inputs[name] = original_name
            dependencies = set()
        else:
            if role not in {"plain", "hypothesis", "negated_conjecture"}:
                raise HintError("unsupported derived role")
            dependencies = _dependencies(annotation, observed["solver"], rules)
            if not dependencies <= graph.keys():
                raise HintError("unknown or forward dependency reference")
        graph[name] = dependencies
    last = records[-1]
    if _InputFormula(last[2]).parse() != ("false",):
        raise HintError("proof section does not end at a refutation root")
    reachable, pending = set(), [last[0]]
    while pending:
        name = pending.pop()
        if name not in reachable:
            reachable.add(name)
            pending.extend(graph[name])
    used_inputs = {inputs[name] for name in reachable if name in inputs}
    if "target" not in used_inputs:
        raise HintError("refutation does not depend on the original target")
    names = sorted(exported_names[name] for name in used_inputs - {"target"})
    if not names:
        raise HintError("solver supplied no usable native premise selection")
    if source_pins() != before:
        raise HintError("hint reader inputs changed")
    return dict(schema=SCHEMA, authority="untrusted_dependency_selection_not_TSTP_translation",
        pilot_id="P08", contract_sha256=P08_CONTRACT_SHA256, statement_ast_sha256=P08_AST_SHA256,
        external_target_ast_sha256=checked["target"]["ast_sha256"], input_sha256=checked["input_sha256"],
        export_sha256=checked["export_sha256"], solver=observed["solver"], source_pins=before,
        log_sha256=sha256(text.encode()).hexdigest(), log_bytes=len(text.encode()),
        original_premises_offered=len(checked["premises"]), selected_premises=names,
        dependency_nodes=len(reachable), observed_rules=sorted(rules),
        derived_formulas_imported=0, solver_proof_logs_translated=0,
        classical_or_skolem_steps_imported=0, ha_checked=False, requires_fresh_HA_replay=True,
        model_proof_search_calls=0, IR_parents_closed=0, library_admissions=0)


def reconstruct_p08(problem, observed, contract):
    """Return (exact target, closed ordinary certificate, bound diagnostics).

The log chooses TWO laws; there is no full-ring fallback. This deterministic
four-step equality/congruence proof does not translate the solver's derivation.
The caller must freshly replay the canonical artifact in another process.
"""
    hint = extract_premise_hint(problem, observed, contract)
    if frozenset(hint["selected_premises"]) != SELECTED_LAWS:
        raise HintError("selected dependencies do not support the narrow P08 reconstruction")
    basis = Basis()
    chosen = {name: basis.get(name) for name in hint["selected_premises"]}
    target = closed_formula(P08_SOURCE)
    if sha256(canonical(encode_formula(target))).hexdigest() != P08_AST_SHA256:
        raise HintError("original HA target identity changed")
    d, u, v, m = (Var(index) for index in (3, 2, 1, 0))
    assoc, comm = chosen["mul_assoc"].certificate, chosen["mul_comm"].certificate
    step1 = EqSym(instantiate(assoc, d, m, v))
    step2 = CongMul(instantiate(comm, d, m), EqRefl(v))
    step3 = instantiate(assoc, m, d, v)
    step4 = CongMul(EqRefl(m), Hyp(0))
    proof = close_proof(EqTrans(step1, EqTrans(step2, EqTrans(step3, step4))), 4, (None,))
    if not check((), proof, target) or check((), proof, Bot()):
        raise HintError("ordinary HA rejected the exact hinted reconstruction")
    if source_pins() != hint["source_pins"]:
        raise HintError("native reconstruction sources changed")
    diagnostics = dict(hint, ha_checked=True, producer_ordinary_HA_checked=True,
        native_strategy="selected_mul_assoc_mul_comm_then_equality_congruence",
        direct_native_laws=hint["selected_premises"], native_dependency_closure=basis.manifest(),
        native_dependency_closure_count=len(basis.checked), equality_steps=4,
        independent_fresh_replay_completed=False)
    return target, proof, diagnostics


def archived_p08(solver="eprover", archive=ARCHIVE):
    """Read hash-checked lossless archive members; these are observations only."""
    if solver not in _RULES:
        raise HintError("only E/Vampire archived hints are supported")
    report_raw, _ = archive_member(Path(archive), "run/report.json")
    report = json.loads(report_raw)
    rows = [row for row in report["rows"] if row["contract"]["pilot_id"] == "P08"]
    if len(rows) != 1:
        raise HintError("ambiguous archived target")
    observations = [value for value in rows[0]["external"] if value["solver"] == solver]
    if len(observations) != 1:
        raise HintError("ambiguous archived solver observation")
    problem_raw, _ = archive_member(Path(archive), f"run/solver-inputs/P08-{solver}.json")
    return json.loads(problem_raw), observations[0], rows[0]["contract"]
