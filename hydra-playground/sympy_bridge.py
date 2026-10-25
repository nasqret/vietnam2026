"""Exact bounded SymPy proposals, reconstructed as ordinary native commands.

Importing this module does not import SymPy. ``solve_payload`` is called only
inside the fixed, pinned, resource-limited adviser child. No parse_expr, eval,
floating-point simplification, Gröbner basis import, or cancellation rule is used.
"""
from __future__ import annotations

from adviser_polynomials import PolynomialAdvisor, validate_problem
from adviser_protocol import ProtocolError


BACKEND_VERSION = "1.14.0"


class SympyAdvisor(PolynomialAdvisor):
    def __init__(self, session, runner, *, capabilities, authority_identity):
        super().__init__("sympy", session, runner, capabilities=capabilities,
                         authority_identity=authority_identity)


def solve_payload(payload):
    """A real CAS operation; never call in the proof/model process."""
    ops = validate_problem(payload, "sympy")
    import sympy as sp
    if sp.__version__ != BACKEND_VERSION:
        raise ProtocolError("The actual SymPy version differs from the pinned bridge version.")
    n = ops.variables
    generators = sp.symbols("hydra_x0:" + str(max(1, n)))

    def to_poly(value):
        parsed = ops.read(value)
        if n == 0:
            parsed = {(0,): coefficient for _, coefficient in parsed.items()}
        return sp.Poly.from_dict(parsed, generators, domain=sp.ZZ)

    def from_poly(value):
        poly = sp.Poly(value, *generators, domain=sp.ZZ)
        if poly.domain != sp.ZZ or len(poly.terms()) > 256 or poly.total_degree() > 8:
            raise ProtocolError("SymPy returned an oversized or non-integer polynomial.")
        result = {}
        for powers, coefficient in poly.terms():
            if coefficient.is_Integer is not True:
                raise ProtocolError("SymPy introduced a non-integer coefficient.")
            if n == 0 and any(powers):
                raise ProtocolError("A dummy CAS variable escaped a constant polynomial.")
            if coefficient:
                result[powers if n else ()] = int(coefficient)
        return ops.write(result)

    mode = payload["mode"]
    if mode == "witness":
        source = to_poly(payload["numerator"])
        divisors = [to_poly(payload["divisor"])]
        divisor_indices = [None]
    else:
        source = to_poly(payload["left"]) - to_poly(payload["right"])
        divisors, divisor_indices = [], []
    for index, row in enumerate(payload["hypotheses"]):
        difference = to_poly(row["left"]) - to_poly(row["right"])
        if not difference.is_zero:
            divisors.append(difference)
            divisor_indices.append(index)
    operations = []
    if divisors:
        operations.append("reduced_ZZ_grlex")
        quotients, remainder = sp.reduced(source, divisors, *generators,
                                         domain=sp.ZZ, order="grlex", polys=True, auto=False)
        # Degree-compatible division plus the validated monomial-universe bound
        # bounds polynomials over these generators; opaque CAS workspace is RSS-
        # and CPU-bounded, not falsely reported as a counted monomial allocation.
        from_poly(remainder)
    else:
        quotients, remainder = [], source
    if not remainder.is_zero:
        return {"status": "no_candidate", "evidence": None,
                "detail": "nonzero_exact_remainder", "operations": operations}
    multipliers = [[] for _ in payload["hypotheses"]]
    witness = None
    for index, quotient in zip(divisor_indices, quotients):
        row = from_poly(quotient)
        if index is None:
            witness = row
        else:
            multipliers[index] = row
    if mode == "witness":
        if witness is None or any(coefficient < 0 or coefficient > 64 for _, coefficient in witness):
            return {"status": "no_candidate", "evidence": None,
                    "detail": "no_bounded_nonnegative_quotient", "operations": operations}
        factor_source = to_poly(witness)
    else:
        factor_source = to_poly(payload["left"])
    factorization = None
    operations.append("factor_list_ZZ")
    unit, factors = sp.factor_list(factor_source)
    if getattr(unit, "is_Integer", None) is True and abs(int(unit)) <= 64:
        if len(factors) <= 8 and sum(int(power) for _, power in factors) <= 8:
            factorization = {"unit": int(unit), "factors": [
                {"polynomial": from_poly(factor), "power": int(power)} for factor, power in factors]}
    return {"status": "candidate", "evidence": {
        "kind": "polynomial_witness" if mode == "witness" else "polynomial_combination",
        "witness": witness, "multipliers": multipliers, "factorization": factorization},
        "detail": "Exact integer polynomial data; native reconstruction is still required.",
        "operations": operations}
