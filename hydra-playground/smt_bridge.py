"""cvc5 coefficient synthesis for a small constructive affine fragment.

The SMT query searches bounded coefficient vectors, not sampled assignments to
the theorem's parameters. Parent-side exact coefficient matching then constructs
a natural witness/equality macro. Neither SAT nor UNSAT is a Peano proof.
"""
from __future__ import annotations

from adviser_polynomials import PolynomialAdvisor, validate_problem
from adviser_protocol import ProtocolError


BACKEND_VERSION = "1.3.4"


class SmtAdvisor(PolynomialAdvisor):
    def __init__(self, session, runner, *, capabilities, authority_identity):
        super().__init__("cvc5", session, runner, capabilities=capabilities,
                         authority_identity=authority_identity)


def coefficient_problem(payload):
    """Pure bounded JSON-to-integer constraints; no solver imports or calls."""
    ops = validate_problem(payload, "cvc5")
    n = ops.variables
    monomials = [(0,) * n]
    for index in range(n):
        monomials.append(tuple(int(i == index) for i in range(n)))
    differences = [ops.add(ops.read(row["left"]), ops.read(row["right"]), -1)
                   for row in payload["hypotheses"]]
    if payload["mode"] == "witness":
        divisor = ops.read(payload["divisor"])
        scalar = divisor.get((0,) * n, 0)
        target = ops.read(payload["numerator"])
    else:
        scalar = None
        target = ops.add(ops.read(payload["left"]), ops.read(payload["right"]), -1)
    rows = [{"powers": list(powers), "target": target.get(powers, 0),
             "hypotheses": [poly.get(powers, 0) for poly in differences]}
            for powers in monomials]
    return {"parameter_count": n, "parameter_lower_bounds": [0] * n,
            "witness_coefficient": scalar, "witness_coefficient_bounds": [0, 64],
            "combination_coefficient_bounds": [-8, 8], "rows": rows,
            "mode": payload["mode"], "hypothesis_count": len(differences)}


def solve_payload(payload):
    """Exactly one real cvc5 QF_LIA check, inside the owned helper only."""
    problem = coefficient_problem(payload)
    import cvc5
    from cvc5 import Kind
    manager = cvc5.TermManager()
    solver = cvc5.Solver(manager)
    if cvc5.__version__ != BACKEND_VERSION:
        raise ProtocolError("The actual cvc5 version differs from the pinned bridge version.")
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    solver.setOption("incremental", "false")
    solver.setOption("tlimit-per", "5000")
    integer_sort = manager.getIntegerSort()

    def number(value):
        return manager.mkInteger(value)

    def bounded_variable(name, low, high=None):
        value = manager.mkConst(integer_sort, name)
        solver.assertFormula(manager.mkTerm(Kind.GEQ, value, number(low)))
        if high is not None:
            solver.assertFormula(manager.mkTerm(Kind.LEQ, value, number(high)))
        return value

    # Parameters have their true Nat lower bounds. Their sample assignments are
    # never read. The equations below match every coefficient, hence the proposal
    # is an identity for all parameter values, not just this satisfying model.
    for index in range(problem["parameter_count"]):
        bounded_variable(f"hydra_nat_{index}", 0)
    combinations = [bounded_variable(f"hydra_combination_{index}", -8, 8)
                    for index in range(problem["hypothesis_count"])]
    witnesses = ([bounded_variable(f"hydra_witness_coefficient_{index}", 0, 64)
                  for index in range(len(problem["rows"]))]
                 if problem["mode"] == "witness" else [])
    for index, row in enumerate(problem["rows"]):
        summands = [manager.mkTerm(Kind.MULT, number(coefficient), variable)
                    for coefficient, variable in zip(row["hypotheses"], combinations) if coefficient]
        if witnesses:
            summands.append(manager.mkTerm(Kind.MULT, number(problem["witness_coefficient"]), witnesses[index]))
        left = number(0) if not summands else summands[0] if len(summands) == 1 else manager.mkTerm(Kind.ADD, *summands)
        solver.assertFormula(manager.mkTerm(Kind.EQUAL, left, number(row["target"])))
    verdict = solver.checkSat()
    if not verdict.isSat():
        return {"status": "no_candidate", "evidence": None,
                "detail": "bounded_coefficient_template_unsat" if verdict.isUnsat() else "coefficient_query_unknown",
                "operations": ["cvc5_QF_LIA_checkSat"], "solver_verdict": str(verdict)}

    def coefficient(variable, minimum, maximum):
        value = solver.getValue(variable)
        if not value.isIntegerValue():
            raise ProtocolError("cvc5 returned a non-integer template coefficient.")
        result = value.getIntegerValue()
        if type(result) is not int or not minimum <= result <= maximum:
            raise ProtocolError("cvc5 returned an out-of-range template coefficient.")
        return result

    n = problem["parameter_count"]
    multipliers = []
    for variable in combinations:
        value = coefficient(variable, -8, 8)
        multipliers.append([[list((0,) * n), value]] if value else [])
    witness = None
    if witnesses:
        entries = [(tuple(row["powers"]), coefficient(variable, 0, 64))
                   for row, variable in zip(problem["rows"], witnesses)]
        witness = [[list(powers), value] for powers, value in sorted(entries) if value]
    return {"status": "candidate", "evidence": {
        "kind": "polynomial_witness" if witnesses else "polynomial_combination",
        "witness": witness, "multipliers": multipliers, "factorization": None},
        "detail": "A bounded integer coefficient vector, not a theorem verdict or sampled witness.",
        "operations": ["cvc5_QF_LIA_checkSat"], "solver_verdict": "sat"}
