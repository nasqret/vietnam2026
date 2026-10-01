"""A fully explicit, fixed degree-seven formal-composition child of P04.

No new HA symbols, function axioms, beta graph, or theorem registry imports.
The source-only layer uses integer coefficient tables. Proof-producing entry
points are lazy and must be run only by the root's bounded native worker.

Two DIFFERENT targets are frozen:
* ground_instance: every actual finite trace equality, AND c_0=D;
* trace_soundness: every valid such finite trace has c_0=D.
Checking the latter alone does not close the former or variable-degree IR079.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEGREE = 7
DENOMINATOR = 105
INNER = (0, 210, 0, 70, 0, 42, 0, 30)
SCHEMA = "sqrt2-power-degree7-composition-v1"
BASIS_SOURCE_SHA256 = "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919"
BINARY_DAG_SOURCE_SHA256 = "517535807fe06a317fae48c5fc5f47db944b0c32904fb8d02a0a1b102af12227"
FROZEN_TARGETS = {
    "trace_soundness": {
        "source_sha256": "edfbef3b916c28000a1a546a38bda23e60b136f064887f6b53b650437b0cc105",
        "statement_ast_sha256": "b8f9f93c128ddf06790122276e27c6e818daf7c31239959e4675c558002a189f",
    },
    "ground_instance": {
        "source_sha256": "17b1baaecceaa5ebfe5d70f23519e6f71c90aec601ead3c03eb4b26472415117",
        "statement_ast_sha256": "67e5493f462533be7b0278c71e26557a606ae3499d32b3fee2ea51e7b4b1ec83",
    },
}
FROZEN_BASIS_LITERALS = {
    "add_assoc": "e23c2a908bb512efab19bed67839aba91ed24fd1b9ab9b91c599e62a56764aea",
    "add_comm": "fe0b9b47ad59a0ff1b3d7eee860c8262421e735cdf0128ba9a486958f6b077a1",
    "add_eq_zero_right": "132ddb7a5346ef030b57e8afa6c379ff5a692d4ab71119b4bed19b19d741fb93",
    "add_mul": "c48f5e849574cefc49610099fe2fe9dd8ef44a04b8213241ebf7e8f57cccee72",
    "add_succ_left": "dd447ec544541bd02f1be2fe72e316bda715120e5abeebfba74af98c11858071",
    "mul_add": "515b74ebcffe7f7cff1861d440fae3e50f44a49cfd65bf3ce0889e72e5991c99",
    "mul_assoc": "02cba3297fd04616267d496eed53360b9eeca6d892a5f1c117f0a50f23653814",
    "mul_comm": "6844833d88b702ddda39f8c0826d11e3859ed234bf55136fef5bb79120a7fb8c",
    "mul_eq_zero": "1fbd7b8a10712cbcab381b042c9dfa33fd5c2fae31d98001a4f34ffd617a5f1f",
    "mul_ne_zero": "e05e515ab64967a58ef6e60a5fce240a079d418d274c6759600db61b58b6a275",
    "mul_one": "71b277c52d72b1b3b4b161567b6bf03e9020d0523585f3d952974f4f579dc5ea",
    "mul_succ_left": "b966ea1d9d1ab60cc34c0899b08fc8b0248bc51cc2678088f7cf993fb042ed11",
    "mul_zero_left": "bc9747ec6d522ffe76b7ff4ca024b8cd2e30ce82d474cd6901dc8045da4cdf49",
    "one_mul": "8f6177cea2a072dd61ec2c8037772ff8e673ac09c02904f781a7c89afd7e9ef4",
    "zero_add": "a60ce5f8481e1ca36b7f67c945370d405115cda727bdf29fb06e1be57458aef3",
}
SOUNDNESS_REQUESTED_LAWS = ("mul_one", "mul_zero_left")
SOUNDNESS_DEPENDENCY_CLOSURE = ("mul_one", "mul_zero_left", "zero_add")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


# These named source trees are NOT extra kernel term constructors. encode()
# removes binder names and checks all arities before emitting the established
# ordinary HA JSON AST. The original parser comparison is a separate check.
def v(name):
    return ("var", name)


def n(value):
    if type(value) is not int or value < 0 or value.bit_length() > 128:
        raise ValueError("bounded natural numeral required")
    if value == 0:
        return ("zero",)
    if value == 1:
        return ("succ", ("zero",))
    doubled = ("mul", ("succ", ("succ", ("zero",))), n(value // 2))
    return ("succ", doubled) if value & 1 else doubled


def add(a, b):
    return ("add", a, b)


def mul(a, b):
    return ("mul", a, b)


def eq(a, b):
    return ("eq", a, b)


def balanced(tag, items):
    items = tuple(items)
    if not items:
        raise ValueError("empty finite source fold")
    if len(items) == 1:
        return items[0]
    middle = len(items) // 2
    return (tag, balanced(tag, items[:middle]), balanced(tag, items[middle:]))


def source(tree):
    tag = tree[0]
    if tag == "zero" and len(tree) == 1:
        return "0"
    if tag == "var" and len(tree) == 2:
        return tree[1]
    if tag == "succ" and len(tree) == 2:
        return "S(" + source(tree[1]) + ")"
    operators = {"add": "+", "mul": "*", "eq": "=", "and": "/\\", "imp": "->"}
    if tag in operators and len(tree) == 3:
        return f"({source(tree[1])} {operators[tag]} {source(tree[2])})"
    if tag in ("forall", "exists") and len(tree) == 3:
        return f"{tag} {tree[1]}. {source(tree[2])}"
    raise ValueError("unknown source constructor or arity")


def encode(tree, bound=()):
    tag = tree[0]
    if tag == "zero" and len(tree) == 1:
        return ["zero"]
    if tag == "var" and len(tree) == 2:
        if tree[1] not in bound:
            raise ValueError("free variable in frozen source: " + tree[1])
        return ["var", bound.index(tree[1])]
    if tag == "succ" and len(tree) == 2:
        return ["succ", encode(tree[1], bound)]
    if tag in ("add", "mul", "eq", "and", "imp") and len(tree) == 3:
        return [tag, encode(tree[1], bound), encode(tree[2], bound)]
    if tag in ("forall", "exists") and len(tree) == 3:
        if tree[1] in bound:
            raise ValueError("shadowing is forbidden in this fixed adapter")
        return [tag, encode(tree[2], (tree[1],) + bound)]
    raise ValueError("unknown source constructor or arity")


def substitute(tree, values):
    if tree[0] == "var":
        return n(values[tree[1]])
    if tree[0] in ("forall", "exists"):
        raise ValueError("ground substitution is only for quantifier-free trace rows")
    return (tree[0], *(substitute(child, values) for child in tree[1:]))


def evaluate(tree, values):
    tag = tree[0]
    if tag == "zero":
        return 0
    if tag == "var":
        return values[tree[1]]
    if tag == "succ":
        return evaluate(tree[1], values) + 1
    if tag == "add":
        return evaluate(tree[1], values) + evaluate(tree[2], values)
    if tag == "mul":
        return evaluate(tree[1], values) * evaluate(tree[2], values)
    if tag == "eq":
        return evaluate(tree[1], values) == evaluate(tree[2], values)
    if tag == "and":
        return evaluate(tree[1], values) and evaluate(tree[2], values)
    raise ValueError("host evaluator is only for finite trace arithmetic")


def variable_names():
    return ([f"a{i}" for i in range(8)]
            + [f"p{k}_{d}" for k in range(8) for d in range(8)]
            + [f"q{k}" for k in range(8)] + [f"f{k}" for k in range(8)]
            + [f"w{k}" for k in range(8)] + [f"c{d}" for d in range(8)]
            + ["D", "positiveD"])


def trace_rows(*, inner_constant=0, factorial_base=1):
    """106 literal defining equalities: no unexpanded predicates or schemas."""
    if inner_constant not in (0, 105) or factorial_base not in (1, 2):
        raise ValueError("only the frozen instance and two fixed hostile variants are allowed")
    inner = (inner_constant,) + INNER[1:]
    rows = [(f"inner-{d}", eq(v(f"a{d}"), n(value))) for d, value in enumerate(inner)]
    rows += [(f"power-base-{d}", eq(v(f"p0_{d}"), n(int(d == 0)))) for d in range(8)]
    for k in range(1, 8):
        for d in range(8):
            convolution = balanced("add", [mul(v(f"a{i}"), v(f"p{k-1}_{d-i}")) for i in range(d + 1)])
            rows.append((f"power-{k}-{d}", eq(v(f"p{k}_{d}"), convolution)))
    rows.append(("denominator-base", eq(v("q0"), n(1))))
    rows += [(f"denominator-{k}", eq(v(f"q{k}"), mul(n(105), v(f"q{k-1}")))) for k in range(1, 8)]
    rows.append(("factorial-base", eq(v("f0"), n(factorial_base))))
    rows += [(f"factorial-{k}", eq(v(f"f{k}"), mul(n(k), v(f"f{k-1}")))) for k in range(1, 8)]
    rows.append(("common-denominator", eq(v("D"), mul(v("q7"), v("f7")))))
    rows.append(("positive-denominator", eq(v("D"), ("succ", v("positiveD")))))
    rows += [(f"weight-{k}", eq(mul(v(f"w{k}"), mul(v(f"q{k}"), v(f"f{k}"))), v("D"))) for k in range(8)]
    rows += [(f"composition-{d}", eq(v(f"c{d}"), balanced("add", [mul(v(f"w{k}"), v(f"p{k}_{d}")) for k in range(8)]))) for d in range(8)]
    return rows


def concrete_trace(*, inner_constant=0, factorial_base=1):
    """Construct the actual integer table, not merely a claimed coefficient."""
    rows = trace_rows(inner_constant=inner_constant, factorial_base=factorial_base)
    inner = (inner_constant,) + INNER[1:]
    values = {f"a{i}": value for i, value in enumerate(inner)}
    for d in range(8):
        values[f"p0_{d}"] = int(d == 0)
    for k in range(1, 8):
        for d in range(8):
            values[f"p{k}_{d}"] = sum(inner[i] * values[f"p{k-1}_{d-i}"] for i in range(d + 1))
    values["q0"], values["f0"] = 1, factorial_base
    for k in range(1, 8):
        values[f"q{k}"] = 105 * values[f"q{k-1}"]
        values[f"f{k}"] = k * values[f"f{k-1}"]
    values["D"] = values["q7"] * values["f7"]
    values["positiveD"] = values["D"] - 1
    for k in range(8):
        denominator = values[f"q{k}"] * values[f"f{k}"]
        quotient, remainder = divmod(values["D"], denominator)
        if remainder:
            raise ValueError("factorial/power denominator does not divide the common denominator")
        values[f"w{k}"] = quotient
    for d in range(8):
        values[f"c{d}"] = sum(values[f"w{k}"] * values[f"p{k}_{d}"] for k in range(8))
    if set(values) != set(variable_names()) or not all(evaluate(tree, values) for _, tree in rows):
        raise AssertionError("the concrete finite execution failed its literal relations")
    return values


def trees():
    rows = trace_rows()
    trace = balanced("and", [tree for _, tree in rows])
    conclusion = eq(v("c0"), v("D"))
    soundness = ("imp", trace, conclusion)
    for name in reversed(variable_names()):
        soundness = ("forall", name, soundness)
    values = concrete_trace()
    ground = balanced("and", [substitute(tree, values) for _, tree in rows] + [substitute(conclusion, values)])
    return dict(trace_soundness=soundness, ground_instance=ground)


@dataclass(frozen=True)
class FlatCollectorLayout:
    """Untrusted source plan: unique Eq leaves and the ORIGINAL And shape."""
    leaves: tuple
    body: tuple
    leaf_occurrences: int


def flat_collector_layout(tree):
    """Deduplicate Eq dependencies, never equations or Ands in the target.

    A ('leaf', i) placeholder refers to the i-th unique Eq in first-occurrence
    order. It is not a trusted proof reference or a new kernel constructor.
    materialize_collector replaces every placeholder by an ordinary Proof.
    """
    leaves, indexes = [], {}
    occurrences = 0
    def visit(current):
        nonlocal occurrences
        if len(current) == 3 and current[0] == "and":
            return ("and_intro", visit(current[1]), visit(current[2]))
        if len(current) != 3 or current[0] != "eq":
            raise ValueError("the flat collector accepts only an exact Eq/And target")
        occurrences += 1
        if current not in indexes:
            indexes[current] = len(leaves)
            leaves.append(current)
        return ("leaf", indexes[current])
    body = visit(tree)
    return FlatCollectorLayout(tuple(leaves), body, occurrences)


def materialize_collector(template, references, and_intro):
    """Expand a source plan using ordinary dependency Hyp and AndIntro values."""
    if type(template) is not tuple:
        raise ValueError("malformed source collector template")
    if len(template) == 2 and template[0] == "leaf":
        index = template[1]
        if type(index) is not int or not 0 <= index < len(references):
            raise ValueError("collector reference is outside its exact dependency list")
        return references[index]
    if len(template) == 3 and template[0] == "and_intro":
        return and_intro(materialize_collector(template[1], references, and_intro),
                         materialize_collector(template[2], references, and_intro))
    raise ValueError("unknown source collector constructor")


def conjunction_source_diagnosis():
    """Count source AST copies only; NOT an observed certificate-size saving."""
    tree = trees()["ground_instance"]
    sizes = []
    def visit(current):
        if current[0] == "and":
            sizes.append(len(canonical(encode(current))))
            visit(current[1])
            visit(current[2])
    visit(tree)
    return dict(authority="source_only_AST_copy_count_not_measured_proof_size",
        original_internal_conjunction_targets=len(sizes), flat_collector_targets=1,
        ground_target_ast_bytes=sizes[0],
        original_internal_target_ast_bytes=sum(sizes),
        removed_intermediate_target_ast_bytes=sum(sizes[1:]),
        measured_certificate_size_reduction=None,
        full_ground_certificate_fits_budget=None)


def _literal_basis():
    path = ROOT / "peano-lab/py/peano_lab/library/theorems.py"
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != BASIS_SOURCE_SHA256:
        raise ValueError("the frozen existing Basis source changed")
    module = ast.parse(raw)
    declarations = [item for item in module.body if isinstance(item, ast.AnnAssign)
                    and isinstance(item.target, ast.Name) and item.target.id == "THEOREMS"]
    if len(declarations) != 1 or not isinstance(declarations[0].value, ast.Tuple):
        raise ValueError("the literal theorem table changed shape")
    selected = {}
    for item in declarations[0].value.elts:
        if not isinstance(item, ast.Call) or not isinstance(item.func, ast.Name) or item.func.id != "TheoremSpec":
            raise ValueError("nonliteral theorem table entry")
        name = ast.literal_eval(item.args[0])
        if name in FROZEN_BASIS_LITERALS:
            spec = tuple(ast.literal_eval(arg) for arg in item.args)
            if sha256(repr(spec).encode()).hexdigest() != FROZEN_BASIS_LITERALS[name]:
                raise ValueError("the frozen literal Basis law changed: " + name)
            selected[name] = spec
    if set(selected) != set(FROZEN_BASIS_LITERALS):
        raise ValueError("missing frozen Basis law")
    return selected


def premise_allowlist():
    return [dict(name=name, source=spec[1], dependencies=list(spec[2]),
                 source_file_sha256=BASIS_SOURCE_SHA256,
                 literal_spec_sha256=FROZEN_BASIS_LITERALS[name])
            for name, spec in sorted(_literal_basis().items())]


def contracts():
    values = concrete_trace()
    result = []
    for name, tree in trees().items():
        encoded = encode(tree)
        text = source(tree)
        source_hash = sha256(text.encode()).hexdigest()
        ast_hash = sha256(canonical(encoded)).hexdigest()
        if dict(source_sha256=source_hash, statement_ast_sha256=ast_hash) != FROZEN_TARGETS[name]:
            raise ValueError("a complete source-frozen composition target changed")
        result.append(dict(id="P04-degree7-" + name.replace("_", "-"),
            target_kind=name, pilot="P04", parent="IR079", degree=7,
            source=text, source_sha256=source_hash,
            statement_ast=encoded, statement_ast_sha256=ast_hash,
            coverage=("full_fixed_degree7_composition_child" if name == "ground_instance"
                      else "supporting_conditional_trace_soundness"),
            closes_P04=False, closes_IR079=False, closes_IR080=False, closes_IR081=False,
            authority="frozen_source_not_a_certificate", original_HA_checked=False,
            expected_free_names=[], trace_rows=len(trace_rows()), trace_witnesses=len(values),
            existing_premise_allowlist=premise_allowlist(),
            soundness_requested_laws=list(SOUNDNESS_REQUESTED_LAWS),
            soundness_dependency_closure=list(SOUNDNESS_DEPENDENCY_CLOSURE)))
    return result


def hostile_examples():
    examples = []
    for label, a0, f0 in (("nonzero-inner-constant", 105, 1), ("wrong-factorial-base", 0, 2)):
        values = concrete_trace(inner_constant=a0, factorial_base=f0)
        rows = trace_rows(inner_constant=a0, factorial_base=f0)
        examples.append(dict(name=label, a0_numerator=a0, factorial_base=f0,
            all_mutated_trace_relations_hold=all(evaluate(tree, values) for _, tree in rows),
            conclusion_holds=values["c0"] == values["D"], c0=values["c0"], D=values["D"],
            meaning="The changed hypotheses admit a genuine trace but do not imply constant coefficient one."))
    malformed = concrete_trace()
    malformed["f3"] = 5
    examples.append(dict(name="wrong-factorial-entry", failed_rows=[identifier for identifier, tree in trace_rows()
                         if not evaluate(tree, malformed)], meaning="Keep the original definition; reject a changed execution entry."))
    return examples


def future_invariant():
    return dict(status="unproved_variable_degree_specification", kernel_certificate=None,
        invariant="For coefficient rows P[k,d] of B^k with B[0]=0 and P[0,0]=1, P[k,d]=0 whenever d<k; the degree-zero case follows directly from P[k+1,0]=B[0]*P[k,0].",
        needed="A general coded convolution/fold graph and induction on k,d, then factorial/denominator transport. IR081 additionally needs separate quantitative composition-tail estimates.",
        remaining_universal_bridges=[
            "IR079: total/unique variable-length power and coefficient tables; the invariant that coefficients below k of A^k vanish when A[0]=0.",
            "IR079: finite product/derivative/composition identities and the full coefficient recurrence (1-z^2)F'=2F; not just its constant-coefficient base.",
            "IR080: boundary coefficients and uniqueness of the recurrence, with positive-integer division justified.",
            "IR081: separate computable bounds for the outer exponential tail, inner atanh tail, and omitted positive coefficient mass at z=1/3.",
        ])


def verify_sources_with_original_parser():
    """Source-only parser/AST agreement; no theorem or proof generation."""
    from sqrt2_power_native import closed_formula
    from peano_lab.library.proof_bundle import encode_formula
    rows = contracts()
    for row in rows:
        if encode_formula(closed_formula(row["source"])) != row["statement_ast"]:
            raise ValueError("independent named-source elaboration disagrees with the original parser")
    return [{key: row[key] for key in ("id", "statement_ast_sha256", "source_sha256", "coverage")} for row in rows]


@dataclass(frozen=True)
class CompositionCertificate:
    formula: object
    certificate: object
    manifest: dict


@dataclass(frozen=True)
class CompositionDAGCertificate:
    formula: object
    bundle_certificate: object
    manifest: dict


def _validated_basis(basis):
    if getattr(basis, "source_sha256", None) != BASIS_SOURCE_SHA256:
        raise ValueError("wrong existing Basis source")
    if set(getattr(basis, "specs", {})) != set(FROZEN_BASIS_LITERALS):
        raise ValueError("wrong fixed Basis allowlist")
    for name, spec in basis.specs.items():
        if sha256(repr(spec).encode()).hexdigest() != FROZEN_BASIS_LITERALS[name]:
            raise ValueError("changed literal Basis specification")


def _freeze_target(kind, expected_ast_sha256):
    from sqrt2_power_native import closed_formula
    from peano_lab.library.proof_bundle import encode_formula
    row = next(row for row in contracts() if row["target_kind"] == kind)
    if expected_ast_sha256 != row["statement_ast_sha256"]:
        raise ValueError("original fixed composition target hash changed")
    target = closed_formula(row["source"])
    if encode_formula(target) != row["statement_ast"]:
        raise ValueError("original kernel AST differs from the frozen source")
    return row, target


def prove_trace_soundness(basis, *, expected_ast_sha256):
    """Native worker only: prove the entire CONDITIONAL trace theorem.

    This is not a certificate of the ground execution. No native runs are
    performed on import, during source construction, or by the default CLI.
    """
    _validated_basis(basis)
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import And, Eq, Forall, Imp
    from peano_lab.kernel.proofs import (AndElimL, AndElimR, Axiom, CongAdd, CongMul,
        EqRefl, EqSym, EqTrans, ForallElim, ForallIntro, Hyp, ImpIntro)
    from peano_lab.kernel.terms import Add, Mul, Succ, Zero
    row, target = _freeze_target("trace_soundness", expected_ast_sha256)
    body, binders = target, 0
    while type(body) is Forall:
        body, binders = body.body, binders + 1
    if type(body) is not Imp or type(body.consequent) is not Eq:
        raise ValueError("unexpected complete trace-soundness shape")
    flat = []
    def flatten(formula, path=()):
        if type(formula) is And:
            flatten(formula.left, path + (0,))
            flatten(formula.right, path + (1,))
        else:
            flat.append((formula, path))
    flatten(body.antecedent)
    identifiers = [identifier for identifier, _ in trace_rows()]
    if len(flat) != len(identifiers):
        raise ValueError("trace field count changed")
    facts = dict(zip(identifiers, flat))
    def fact(identifier):
        proof = Hyp(0)
        for direction in facts[identifier][1]:
            proof = AndElimL(proof) if direction == 0 else AndElimR(proof)
        return proof
    def instantiate(proof, term):
        return ForallElim(proof, term)
    def pa(name, term):
        return instantiate(Axiom(name), term)
    one, zero = Succ(Zero()), Zero()
    mul_one = basis.get("mul_one").certificate
    mul_zero = basis.get("mul_zero_left").certificate
    power_zero = {}
    for k in range(1, 8):
        equation = facts[f"power-{k}-0"][0]
        if type(equation.right) is not Mul:
            raise ValueError("degree-zero convolution is not the expected single product")
        previous = equation.right.right
        power_zero[k] = EqTrans(fact(f"power-{k}-0"), EqTrans(
            CongMul(fact("inner-0"), EqRefl(previous)), instantiate(mul_zero, previous)))
    weight_equation = facts["weight-0"][0]
    w0 = weight_equation.left.left
    base_product = EqTrans(CongMul(fact("denominator-base"), fact("factorial-base")), instantiate(mul_one, one))
    normalize_weight = EqTrans(CongMul(EqRefl(w0), base_product), instantiate(mul_one, w0))
    weight_equals_D = EqTrans(EqSym(normalize_weight), fact("weight-0"))
    composition = facts["composition-0"][0]
    summands = []
    def flatten_sum(term):
        if type(term) is Add:
            flatten_sum(term.left)
            flatten_sum(term.right)
        else:
            summands.append(term)
    flatten_sum(composition.right)
    if len(summands) != 8:
        raise ValueError("composition constant must contain all eight powers")
    normalized = []
    for k, term in enumerate(summands):
        if type(term) is not Mul:
            raise ValueError("composition summand is not a weighted coefficient")
        if k == 0:
            proof = EqTrans(CongMul(EqRefl(term.left), fact("power-base-0")), instantiate(mul_one, term.left))
            normalized.append((term.left, proof))
        else:
            proof = EqTrans(CongMul(EqRefl(term.left), power_zero[k]), pa("PA5", term.left))
            normalized.append((zero, proof))
    def join(items):
        if len(items) == 1:
            return items[0]
        middle = len(items) // 2
        left, lp = join(items[:middle])
        right, rp = join(items[middle:])
        if type(right) is not Zero:
            raise ValueError("unexpected nonconstant branch in constant-coefficient proof")
        return left, EqTrans(CongAdd(lp, rp), pa("PA3", left))
    _, sum_proof = join(normalized)
    certificate = ImpIntro(EqTrans(fact("composition-0"), EqTrans(sum_proof, weight_equals_D)))
    for _ in range(binders):
        certificate = ForallIntro(certificate)
    if not check((), certificate, target):
        raise ValueError("original HA kernel rejected conditional trace soundness")
    return CompositionCertificate(target, certificate, dict(
        target=row["id"], statement_ast_sha256=row["statement_ast_sha256"],
        original_HA_checked=True, empty_context=True,
        coverage="supporting_conditional_trace_soundness", closes_P04=False,
        requested_existing_laws=list(SOUNDNESS_REQUESTED_LAWS),
        existing_dependency_closure=list(SOUNDNESS_DEPENDENCY_CLOSURE),
        closes_IR079=False, closes_IR080=False, closes_IR081=False))


def prove_ground_instance(basis, equation_prover, *, expected_ast_sha256):
    """Native worker only: check EVERY actual execution leaf before composing.

    equation_prover(Eq, basis) must return an ordinary Proof. Root supplies a
    bounded binary/ground arithmetic adapter; there is no unary fallback here.
    Callback observations or solver claims cannot replace kernel certificates.
    """
    _validated_basis(basis)
    if not callable(equation_prover):
        raise ValueError("an explicitly selected bounded equation prover is required")
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import And, Eq
    from peano_lab.kernel.proofs import AndIntro, EqRefl
    row, target = _freeze_target("ground_instance", expected_ast_sha256)
    checked_leaves = 0
    def visit(formula):
        nonlocal checked_leaves
        if type(formula) is And:
            return AndIntro(visit(formula.left), visit(formula.right))
        if type(formula) is not Eq:
            raise ValueError("unexpected fixed execution leaf")
        proof = EqRefl(formula.left) if formula.left == formula.right else equation_prover(formula, basis)
        if not check((), proof, formula):
            raise ValueError("original HA rejected a ground composition execution leaf")
        checked_leaves += 1
        return proof
    certificate = visit(target)
    if not check((), certificate, target):
        raise ValueError("original HA rejected the full fixed composition instance")
    return CompositionCertificate(target, certificate, dict(
        target=row["id"], statement_ast_sha256=row["statement_ast_sha256"],
        original_HA_checked=True, empty_context=True, checked_execution_leaves=checked_leaves,
        coverage="full_fixed_degree7_composition_child", closes_P04_degree7_child=True,
        closes_P04=False, closes_IR079=False, closes_IR080=False, closes_IR081=False,
        variable_degree_claim=False))


def prove_ground_instance_dag(basis, *, expected_ast_sha256, limits=None):
    """Root worker only: one bounded ordinary DAG for the entire ground trace.

    Every leaf is either syntactic reflexivity or a binary arithmetic derivation.
    One final node contains the original balanced AndIntro body, with all its
    unique Eq leaves as local dependencies. There are no intermediate And DAG
    nodes repeating large ground targets. Arithmetic nodes are shared across
    all 107 leaf occurrences, and finish() replays canonical bytes in the
    unchanged HA kernel. No Eq certificate, trace row, or final conclusion is
    accepted from host arithmetic evaluation alone. Existing DAG limits cannot
    be widened by this entry point. This changed packaging is not a claim that
    the full certificate will fit those limits.
    """
    _validated_basis(basis)
    path = ROOT / "scripts/sqrt2_power_binary_dag.py"
    if sha256(path.read_bytes()).hexdigest() != BINARY_DAG_SOURCE_SHA256:
        raise ValueError("the source-frozen ordinary binary DAG adapter changed")
    from peano_lab.kernel.formulas import And, Eq
    from peano_lab.kernel.proofs import AndIntro, EqRefl
    from peano_lab.library.proof_bundle import encode_formula
    from sqrt2_power_binary_dag import BinaryDAGLimits, _Builder, _basis, _values
    if limits is None:
        limits = BinaryDAGLimits()
    if type(limits) is not BinaryDAGLimits:
        raise ValueError("expected the existing bounded binary DAG limits")
    row, target = _freeze_target("ground_instance", expected_ast_sha256)
    builder = _Builder(_basis(basis), limits)
    layout = flat_collector_layout(trees()["ground_instance"])
    native_leaves, indexes = [], {}
    native_occurrences = 0
    def collect(formula):
        nonlocal native_occurrences
        if type(formula) is And:
            collect(formula.left)
            collect(formula.right)
            return
        if type(formula) is not Eq:
            raise ValueError("unexpected complete composition execution leaf")
        native_occurrences += 1
        if formula not in indexes:
            indexes[formula] = len(native_leaves)
            native_leaves.append(formula)
    collect(target)
    if (native_occurrences != layout.leaf_occurrences
            or len(native_leaves) != len(layout.leaves)
            or any(encode_formula(actual) != encode(expected)
                   for actual, expected in zip(native_leaves, layout.leaves))):
        raise ValueError("source/native flat-collector dependency mapping changed")
    leaf_nodes = []
    for formula in native_leaves:
        if formula.left == formula.right:
            node = builder.emit(formula, (), lambda _: EqRefl(formula.left))
        else:
            node = builder.equality(formula, _values(formula, limits))
        leaf_nodes.append(node)
    root = builder.emit(target, tuple(leaf_nodes), lambda ref:
        materialize_collector(layout.body, tuple(ref(node) for node in leaf_nodes), AndIntro))
    checked = builder.finish(root, target)
    if checked.target_ast_sha256 != row["statement_ast_sha256"]:
        raise ValueError("canonical ground trace replay changed the frozen AST")
    return CompositionDAGCertificate(target, checked, dict(
        target=row["id"], statement_ast_sha256=row["statement_ast_sha256"],
        original_HA_checked=True, canonical_bytes_replayed=True, empty_context=True,
        checked_execution_leaves=layout.leaf_occurrences,
        unique_execution_dependencies=len(leaf_nodes), final_conjunction_collector_nodes=1,
        coverage="full_fixed_degree7_composition_child", closes_P04_degree7_child=True,
        closes_P04=False, closes_IR079=False, closes_IR080=False, closes_IR081=False,
        variable_degree_claim=False,
        conjunction_source_diagnosis=conjunction_source_diagnosis(),
        ordinary_binary_dag_source_sha256=BINARY_DAG_SOURCE_SHA256,
        requested_existing_laws=list(checked.basis_names)))


def summary():
    rows = contracts()
    values = concrete_trace()
    return dict(schema=SCHEMA, authority="frozen_source_not_a_certificate",
        native_runs_performed=False, original_HA_checked=False,
        targets=[{key: row[key] for key in ("id", "statement_ast_sha256", "source_sha256", "coverage", "trace_rows", "trace_witnesses")} for row in rows],
        degree=7, integer_inner_coefficients=list(INNER), inner_denominator=105,
        coefficient_table_shape=[8, 8], common_denominator=values["D"],
        host_constant_comparison=values["c0"] == values["D"],
        native_ground_trace_completed=False, beta_graph_needed_for_this_fixed_child=False,
        hostile_examples=hostile_examples(), future_invariant=future_invariant(),
        conjunction_source_diagnosis=conjunction_source_diagnosis())


if __name__ == "__main__":
    print(json.dumps(summary(), sort_keys=True, indent=2))
