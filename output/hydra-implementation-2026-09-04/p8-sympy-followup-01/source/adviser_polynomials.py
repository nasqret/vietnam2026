"""Small exact polynomial data and native-command reconstruction for P8.

This is proposal validation, never certificate checking. Even an exactly matched
integer identity supplies no trusted Peano proof. Every generated surface line
and the original theorem must still pass the owning native search/replay path.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from adviser_protocol import (BudgetStop, ProtocolError, checked_response, prepare_request,
                              semantic_context)


MAX_VARIABLES = 4
MAX_DEGREE = 8
MAX_MONOMIALS = 256
MAX_COEFFICIENT = 4096
MAX_HYPOTHESES = 3
MAX_WORK = 32768
MAX_COMMANDS = 8
MAX_COMMAND_BYTES = 512


class PolynomialOps:
    def __init__(self, variables):
        if type(variables) is not int or not 0 <= variables <= MAX_VARIABLES:
            raise ProtocolError("Polynomial variable count exceeds four.")
        self.variables = variables
        self.work = 0

    def tick(self, amount=1):
        self.work += amount
        if self.work > MAX_WORK:
            raise ProtocolError("Polynomial proposal work exceeded its finite bound.")

    def bounded(self, poly):
        self.tick(len(poly) + 1)
        result = {}
        if len(poly) > MAX_MONOMIALS:
            raise ProtocolError("Polynomial exceeds 256 monomials.")
        for powers, coefficient in poly.items():
            if (type(powers) is not tuple or len(powers) != self.variables
                    or any(type(p) is not int or p < 0 for p in powers)
                    or sum(powers) > MAX_DEGREE or type(coefficient) is not int
                    or abs(coefficient) > MAX_COEFFICIENT):
                raise ProtocolError("Polynomial degree/coefficient/scope bound exceeded.")
            if coefficient:
                result[powers] = coefficient
        return result

    def read(self, value):
        if type(value) is not list or len(value) > MAX_MONOMIALS:
            raise ProtocolError("Malformed polynomial JSON.")
        result = {}
        previous = None
        for row in value:
            self.tick()
            if type(row) is not list or len(row) != 2 or type(row[0]) is not list:
                raise ProtocolError("Malformed polynomial monomial.")
            powers, coefficient = tuple(row[0]), row[1]
            if (len(powers) != self.variables or any(type(p) is not int for p in powers)
                    or type(coefficient) is not int or not coefficient
                    or previous is not None and powers <= previous):
                raise ProtocolError("Polynomial rows must be ordered, unique integer monomials.")
            result[powers] = coefficient
            previous = powers
        return self.bounded(result)

    def write(self, poly):
        return [[list(powers), coefficient] for powers, coefficient in sorted(self.bounded(poly).items())]

    def constant(self, number):
        return {} if number == 0 else self.bounded({(0,) * self.variables: number})

    def add(self, left, right, factor=1):
        if type(factor) is not int or abs(factor) > MAX_COEFFICIENT:
            raise ProtocolError("Unbounded polynomial multiplier.")
        result = dict(left)
        for powers, coefficient in right.items():
            self.tick()
            result[powers] = result.get(powers, 0) + factor * coefficient
        return self.bounded(result)

    def multiply(self, left, right):
        result = {}
        for a, first in left.items():
            for b, second in right.items():
                self.tick()
                powers = tuple(x + y for x, y in zip(a, b))
                if sum(powers) > MAX_DEGREE:
                    raise ProtocolError("Polynomial product exceeds degree eight.")
                result[powers] = result.get(powers, 0) + first * second
                if len(result) > MAX_MONOMIALS:
                    raise ProtocolError("An explicit intermediate exceeds 256 monomials.")
        return self.bounded(result)

    def native(self, term):
        from peano_lab.kernel import terms as t
        nodes = 0

        def visit(item, depth=0):
            nonlocal nodes
            nodes += 1
            self.tick()
            if nodes > 4096 or depth > 112:
                raise ProtocolError("Native polynomial AST exceeds its bound.")
            if type(item) is t.Zero:
                return {}
            if type(item) is t.Var:
                if type(item.index) is not int or not 0 <= item.index < self.variables:
                    raise ProtocolError("Polynomial variable escaped its native scope.")
                powers = [0] * self.variables
                powers[item.index] = 1
                return {tuple(powers): 1}
            if type(item) is t.Succ:
                return self.add(visit(item.term, depth + 1), self.constant(1))
            if type(item) in (t.Add, t.Mul):
                left, right = visit(item.left, depth + 1), visit(item.right, depth + 1)
                return self.add(left, right) if type(item) is t.Add else self.multiply(left, right)
            raise ProtocolError("Only rigid natural-number arithmetic terms are supported.")

        return visit(term)


def _number(number):
    from peano_lab.kernel.terms import Succ, Zero
    if type(number) is not int or not 0 <= number <= 64:
        raise ProtocolError("A native proposal needs coefficients in 0..64.")
    result = Zero()
    for _ in range(number):
        result = Succ(result)
    return result


def _sum(terms):
    from peano_lab.kernel.terms import Add, Zero
    if not terms:
        return Zero()
    result = terms[0]
    for term in terms[1:]:
        result = Add(result, term)
    return result


def quote_polynomial(poly, variables):
    from peano_lab.kernel.terms import Mul, Var
    ops = PolynomialOps(variables)
    poly = ops.bounded(poly)
    if len(poly) > 32:
        raise ProtocolError("A proposed native term has too many printed monomials.")
    terms = []
    for powers, coefficient in sorted(poly.items(), reverse=True):
        if not 0 < coefficient <= 64:
            raise ProtocolError("A natural witness or rewrite factor has a negative/oversized coefficient.")
        factors = [Var(index) for index, power in enumerate(powers) for _ in range(power)]
        if not factors:
            terms.append(_number(coefficient))
            continue
        item = factors[0]
        for factor in factors[1:]:
            item = Mul(item, factor)
        terms.append(item if coefficient == 1 else Mul(_number(coefficient), item))
    return _sum(terms)


def render_term(term, variables):
    from peano_lab.kernel.terms import pretty_term
    value = pretty_term(term, list(variables))
    if len(value.encode("utf-8")) > 448:
        raise ProtocolError("Proposed native term exceeds its command byte budget.")
    return value


@dataclass(frozen=True)
class PolynomialProblem:
    payload: dict
    target: object
    variables: tuple[str, ...]
    hypotheses: tuple[tuple[str, object], ...]


def focus_problem(state, backend):
    """A deliberately small post-introduction fragment; no context truncation."""
    from peano_lab.kernel.formulas import Eq, Exists
    goal = state.current()
    if goal is None or backend not in {"sympy", "cvc5"}:
        raise ProtocolError("No supported focused adviser goal.")
    variables = tuple(goal.variables)
    n = len(variables)
    witness = type(goal.target) is Exists and type(goal.target.body) is Eq
    if type(goal.target) is not Eq and not witness:
        raise ProtocolError("Introduce binders first; only equations or one existential equation are supported.")
    if n + int(witness) > MAX_VARIABLES:
        raise ProtocolError("The focused polynomial uses more than four variables including its witness.")
    ops = PolynomialOps(n)
    selected, seen = [], set()
    for name, formula in goal.context:
        if name in seen:
            continue  # Only the newest binding is available to a surface rewrite.
        seen.add(name)
        if type(formula) is not Eq:
            raise ProtocolError("This initial arithmetic bridge requires equation-only local assumptions.")
        selected.append((name, formula))
    if len(selected) > MAX_HYPOTHESES:
        raise ProtocolError("More than three local equations need a larger reconstruction contract.")
    hypotheses = [{"name": name, "left": ops.write(ops.native(formula.left)),
                   "right": ops.write(ops.native(formula.right))} for name, formula in selected]
    payload = {"schema": "hydra-natural-polynomial-problem-v1", "variables": n,
        "parameter_domain": "Nat", "natural_lower_bounds": [0] * n,
        "mode": "witness" if witness else "equality", "hypotheses": hypotheses}
    if witness:
        bound_ops = PolynomialOps(n + 1)
        difference = bound_ops.add(bound_ops.native(goal.target.body.left),
                                   bound_ops.native(goal.target.body.right), -1)
        divisor, numerator = {}, {}
        for powers, coefficient in difference.items():
            if powers[0] > 1:
                raise ProtocolError("Nonlinear dependence on the existential witness is unsupported.")
            (divisor if powers[0] else numerator)[powers[1:]] = coefficient if powers[0] else -coefficient
        if not divisor:
            raise ProtocolError("The existential witness has no nonzero polynomial coefficient.")
        payload.update(divisor=ops.write(divisor), numerator=ops.write(numerator))
    else:
        payload.update(left=ops.write(ops.native(goal.target.left)),
                       right=ops.write(ops.native(goal.target.right)))
    validate_problem(payload, backend)
    return PolynomialProblem(payload, goal.target, variables, tuple(selected))


def validate_problem(payload, backend):
    """Validate the same finite data in parent and pinned child."""
    if (type(payload) is not dict or payload.get("schema") != "hydra-natural-polynomial-problem-v1"
            or payload.get("mode") not in {"witness", "equality"}
            or payload.get("parameter_domain") != "Nat"):
        raise ProtocolError("Unsupported adviser polynomial problem.")
    ops = PolynomialOps(payload.get("variables"))
    n = ops.variables
    if payload.get("natural_lower_bounds") != [0] * n:
        raise ProtocolError("All introduced parameters must have explicit natural-number domains.")
    rows = payload.get("hypotheses")
    if type(rows) is not list or len(rows) > MAX_HYPOTHESES:
        raise ProtocolError("Too many local equalities.")
    names, parsed = set(), []
    for row in rows:
        if type(row) is not dict or set(row) != {"name", "left", "right"}:
            raise ProtocolError("Malformed local equality.")
        name = row["name"]
        if type(name) is not str or name in names or len(name) > 64:
            raise ProtocolError("Ambiguous local equality name.")
        names.add(name)
        parsed.extend((ops.read(row["left"]), ops.read(row["right"])))
    mode = payload["mode"]
    keys = {"schema", "variables", "parameter_domain", "natural_lower_bounds", "mode", "hypotheses"}
    keys |= {"divisor", "numerator"} if mode == "witness" else {"left", "right"}
    if set(payload) != keys:
        raise ProtocolError("Unknown polynomial problem fields.")
    if mode == "witness":
        divisor, numerator = ops.read(payload["divisor"]), ops.read(payload["numerator"])
        if not divisor:
            raise ProtocolError("Zero witness divisor is unsupported.")
        parsed.extend((divisor, numerator))
        if backend == "cvc5" and any(any(powers) for powers in divisor):
            raise ProtocolError("SMT witness templates require a constant affine witness coefficient.")
    else:
        parsed.extend((ops.read(payload["left"]), ops.read(payload["right"])))
    degree = max((sum(powers) for poly in parsed for powers in poly), default=0)
    if backend == "cvc5" and degree > 1:
        raise ProtocolError("Nonlinear arithmetic is outside the initial cvc5 contract.")
    if backend == "sympy" and math.comb(n + degree, degree) > MAX_MONOMIALS:
        # Degree-compatible division cannot create a larger monomial universe.
        # Private CAS workspace is additionally bounded by child CPU/RSS limits.
        raise ProtocolError("The bounded polynomial monomial universe exceeds 256.")
    return ops


def equality_macro(target, hypotheses, multipliers, variables):
    """Reconstruct nonnegative equality combinations using trans/rewrite/ring.

    Some valid integer consequences need cancellation or further lemmas. They
    are intentionally rejected when no subtraction-free intermediate fits.
    """
    from peano_lab.kernel.terms import Mul
    ops = PolynomialOps(len(variables))
    left, right = ops.native(target.left), ops.native(target.right)
    if left == right:
        return ("ring",)
    for reverse in (False, True):
        sources, source_poly, rewrites = [], {}, []
        for (name, formula), multiplier in zip(hypotheses, multipliers):
            for sign in (1, -1):
                chosen = {powers: abs(coefficient) for powers, coefficient in multiplier.items()
                          if (coefficient > 0) == (sign > 0)}
                if not chosen:
                    continue
                direction = -sign if reverse else sign
                term = formula.left if direction > 0 else formula.right
                factor = quote_polynomial(chosen, len(variables))
                source = term if chosen == ops.constant(1) else Mul(factor, term)
                sources.append(source)
                source_poly = ops.add(source_poly, ops.multiply(chosen, ops.native(term)))
                rewrites.append(f"rewrite {'<- ' if direction < 0 else ''}{name}")
        if len(rewrites) > 3:
            continue
        remainder = ops.add(right if reverse else left, source_poly, -1)
        if any(coefficient < 0 for coefficient in remainder.values()):
            continue
        middle = _sum(sources + ([quote_polynomial(remainder, len(variables))] if remainder else []))
        prefix = ("symm",) if reverse else ()
        return prefix + (f"trans ({render_term(middle, variables)})", "ring", *rewrites, "ring")
    raise ProtocolError("This equality combination needs an unsupported cancellation/reconstruction step.")


def reconstruct(problem, evidence, backend):
    from peano_lab.engine.state import instantiate_formula
    if type(evidence) is not dict or set(evidence) != {"kind", "witness", "multipliers", "factorization"}:
        raise ProtocolError("Malformed arithmetic evidence.")
    payload = problem.payload
    ops = validate_problem(payload, backend)
    expected = "polynomial_witness" if payload["mode"] == "witness" else "polynomial_combination"
    if evidence["kind"] != expected:
        raise ProtocolError("Evidence does not match the requested fragment.")
    rows = evidence["multipliers"]
    if type(rows) is not list or len(rows) != len(problem.hypotheses):
        raise ProtocolError("Evidence refers to different local equations.")
    multipliers = [ops.read(row) for row in rows]
    combination = {}
    for row, multiplier in zip(payload["hypotheses"], multipliers):
        if backend == "cvc5" and any(any(powers) or abs(value) > 8 for powers, value in multiplier.items()):
            raise ProtocolError("SMT supplied a nonconstant or oversized equality multiplier.")
        difference = ops.add(ops.read(row["left"]), ops.read(row["right"]), -1)
        combination = ops.add(combination, ops.multiply(multiplier, difference))
    prefix = ()
    target = problem.target
    if payload["mode"] == "witness":
        witness = ops.read(evidence["witness"])
        if any(value < 0 or value > 64 for value in witness.values()):
            raise ProtocolError("Only bounded natural polynomial witnesses are reconstructible.")
        if backend == "cvc5" and any(sum(powers) > 1 for powers in witness):
            raise ProtocolError("SMT supplied a nonlinear witness.")
        expected_numerator = ops.add(ops.multiply(ops.read(payload["divisor"]), witness), combination)
        if expected_numerator != ops.read(payload["numerator"]):
            raise ProtocolError("The proposed witness fails exact coefficient matching for all parameters.")
        witness_term = quote_polynomial(witness, len(problem.variables))
        prefix = (f"exists ({render_term(witness_term, problem.variables)})",)
        target = instantiate_formula(problem.target.body, witness_term)
        multipliers = [ops.add({}, multiplier, -1) for multiplier in multipliers]
        factor_source = witness
    else:
        if evidence["witness"] is not None:
            raise ProtocolError("An equality response cannot introduce a witness.")
        difference = ops.add(ops.read(payload["left"]), ops.read(payload["right"]), -1)
        if difference != combination:
            raise ProtocolError("The equality combination does not match the target polynomial.")
        factor_source = ops.read(payload["left"])
    factorization = evidence["factorization"]
    if factorization is not None:
        if (backend != "sympy" or type(factorization) is not dict
                or set(factorization) != {"unit", "factors"}
                or type(factorization["unit"]) is not int or abs(factorization["unit"]) > 64
                or type(factorization["factors"]) is not list or len(factorization["factors"]) > 8):
            raise ProtocolError("Malformed bounded factorization.")
        product = ops.constant(factorization["unit"])
        total_powers = 0
        for row in factorization["factors"]:
            if type(row) is not dict or set(row) != {"polynomial", "power"}:
                raise ProtocolError("Malformed factorization entry.")
            power = row["power"]
            if type(power) is not int or not 1 <= power <= 8:
                raise ProtocolError("Unbounded factor exponent.")
            total_powers += power
            if total_powers > 8:
                raise ProtocolError("Factorization has too many factors.")
            factor = ops.read(row["polynomial"])
            for _ in range(power):
                product = ops.multiply(product, factor)
        if product != factor_source:
            raise ProtocolError("Factorization does not reconstruct its exact input polynomial.")
    commands = prefix + equality_macro(target, problem.hypotheses, multipliers, problem.variables)
    if not commands or len(commands) > MAX_COMMANDS or any(len(command.encode("utf-8")) > MAX_COMMAND_BYTES
                                                          for command in commands):
        raise ProtocolError("Native reconstruction exceeds eight commands or 512 bytes per command.")
    return commands


class PolynomialAdvisor:
    """Shared glue for the two small arithmetic bridges; no backend dispatch registry."""
    def __init__(self, backend, session, runner, *, capabilities, authority_identity):
        if backend not in {"sympy", "cvc5"}:
            raise ProtocolError("Unsupported polynomial adviser.")
        self.backend, self.session, self.runner = backend, session, runner
        self.capabilities, self.authority_identity = capabilities, authority_identity
        self.advice_requests = self.actual_invocations = 0
        self.accounting_complete = True

    def advise(self, state):
        self.advice_requests += 1
        result = {"status": "unsupported", "suggestions": [], "candidates": (),
                  "kernel_checked": False, "solver": {"backend": self.backend, "invocations": 0}}
        try:
            context = semantic_context(state, self.capabilities, authority_identity=self.authority_identity)
            problem = focus_problem(state, self.backend)
            request = prepare_request(self.backend, problem.payload, context, self.runner.identity)
            with self.session.lease(request) as lease:
                execution = self.runner(lease)
                record = lease.record_external(execution, quiescent=execution.get("quiescent") is True)
            self.actual_invocations += record["actual_launches"]
            result["solver"] = {key: execution.get(key) for key in (
                "status", "available", "exit_code", "elapsed_seconds", "input_sha256",
                "termination", "peak_rss_bytes", "rss_samples", "quiescent", "identity", "limits")}
            result["solver"].update(backend=self.backend, invocations=record["actual_launches"])
            result["context_sha256"] = request.context_sha256
            if execution.get("status") != "completed":
                result.update(status=execution.get("status", "failed"),
                              detail="The bounded external attempt supplied no usable native advice.")
                return result
            response = checked_response(request, execution)
            if response.get("status") == "no_candidate":
                result.update(status="no_candidate", detail="No supported bounded coefficient proposal was found.")
                return result
            if response.get("status") != "candidate":
                raise ProtocolError("Unsupported external response status.")
            commands = reconstruct(problem, response.get("evidence"), self.backend)
            if any(command.split(maxsplit=1)[0] not in self.capabilities.allowed_commands for command in commands):
                raise ProtocolError("The proposed reconstruction needs a disallowed native command.")
            result.update(status="advisory_candidate", candidates=(commands,), suggestions=[{
                "commands": list(commands), "source": self.backend,
                "reason": "Exact bounded coefficient data suggests these native steps; final replay remains mandatory.",
                "context_sha256": request.context_sha256, "input_sha256": request.input_sha256,
                "kernel_checked": False}])
            return result
        except BudgetStop as error:
            result.update(status="budget_stop", detail=str(error))
        except (ProtocolError, TypeError, AttributeError, KeyError, RecursionError) as error:
            result.update(status="unsupported" if result["solver"].get("invocations") == 0 else "unsupported_evidence",
                          detail=str(error)[:400])
            if not self.session.report()["accounting_complete"]:
                self.accounting_complete = False
                result["solver"]["invocations"] = None
                result["status"] = "infrastructure_error"
        return result

    def report(self):
        return {"backend": self.backend, "advice_requests": self.advice_requests,
                "actual_invocations": self.actual_invocations if self.accounting_complete else None,
                "known_actual_invocations": self.actual_invocations,
                "accounting_complete": self.accounting_complete, "kernel_checked": False}
