"""Bounded exact-arithmetic calibration; NOT HA or analytic proof evidence.

Only integers and Fraction enter the mathematical checks. These finite examples
do not prove a tail bound, approximation accuracy, irrationality, or a universal
identity. In particular, an ``IrrCert`` check here means the finite rational
inequality in IRD10, not its unproved semantic soundness theorem.

Run directly to print a small JSON report. There are no downloads, solver calls,
proof admissions, auxiliary-matrix allocations, or unbounded searches.
"""

from fractions import Fraction
from functools import lru_cache
import json
from math import comb, factorial, isqrt, prod


MAX_PRECISION = 16
MAX_MULTIPLICITY = 3
MAX_MOMENT_Q = 3
AUTHORITY = "exact_arithmetic_calibration_only"
CERTIFICATE_CASES = (
    (-3, 2), (0, 1), (1, 1), (3, 2), (8, 5), (5, 3),
    (2, 1), (4, 1), (49, 30), (163, 100), (1633, 1000), (23, 14),
)


def _check(condition, message):
    """Keep CLI checks active even when Python runs with -O."""
    if not condition:
        raise AssertionError(message)


def _bounded_integer(value, lower, upper, name):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


@lru_cache(maxsize=MAX_PRECISION + 1)
def c_approx(n):
    """Evaluate exactly the campaign's IRD09 CApprox, for 0 <= n <= 16.

    k=n+8; s=isqrt(2*2**(2*k))/2**k; L=Log2Partial(k);
    u=ExpPartial(L/s,k+2). No error bound is asserted by this function.
    """
    _bounded_integer(n, 0, MAX_PRECISION, "precision")
    k = n + 8
    s = Fraction(isqrt(2 * 2 ** (2 * k)), 2 ** k)
    log2 = 2 * sum((Fraction(1, (2 * j + 1) * 3 ** (2 * j + 1))
                    for j in range(k)), Fraction(0))
    argument = log2 / s
    term = Fraction(1)
    value = term
    for j in range(1, k + 3):
        term *= argument / j
        value += term
    return value


def irr_cert_holds(a, b, n):
    """Test only |b*u_n-a| > 2*b*2**(-n), using exact rational order."""
    if type(a) is not int or type(b) is not int or b <= 0:
        raise ValueError("a must be an integer and b a positive integer")
    return abs(b * c_approx(n) - a) > Fraction(2 * b, 2 ** n)


def first_certificate(a, b, max_precision=MAX_PRECISION):
    """A bounded pilot search; return None if no tested precision succeeds."""
    _bounded_integer(max_precision, 0, MAX_PRECISION, "max_precision")
    for n in range(max_precision + 1):
        if irr_cert_holds(a, b, n):
            return n
    return None


def _poly_mul(left, right):
    result = [Fraction(0)] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] += a * b
    return result


def normalized_jet(polynomial, node, order):
    """The exact formal derivative at node, divided by order!."""
    return sum((coefficient * comb(degree, order) * node ** (degree - order)
                for degree, coefficient in enumerate(polynomial)
                if degree >= order), Fraction(0))


def homogeneous_coefficients(nodes, multiplicities, degree):
    """Coefficients of product_y (1-y*z)^(-1), through the given degree."""
    coefficients = [Fraction(1)] + [Fraction(0)] * degree
    for node, multiplicity in zip(nodes, multiplicities):
        for _ in range(multiplicity):
            for k in range(1, degree + 1):
                coefficients[k] += node * coefficients[k - 1]
    return coefficients


def confluent_case(r, selected, spacing=Fraction(1, 3)):
    """Return nodes, multiplicities and C_(j,k) for one bounded pilot."""
    _bounded_integer(r, 1, MAX_MULTIPLICITY, "r")
    _bounded_integer(selected, 0, 6, "selected node")
    if not isinstance(spacing, Fraction) or spacing <= 0:
        raise ValueError("spacing must be a positive Fraction")
    nodes = [j * spacing for j in range(7)]
    multiplicities = [r + int(j == selected) for j in range(7)]
    coefficients = {}
    for j in range(7):
        degree = multiplicities[j] - 1
        inverse_product = [Fraction(1)] + [Fraction(0)] * degree
        for h in range(7):
            if h == j:
                continue
            gap = nodes[j] - nodes[h]
            exponent = multiplicities[h]
            factor = [Fraction((-1) ** d * comb(exponent + d - 1, d))
                      * gap ** (-exponent - d) for d in range(degree + 1)]
            inverse_product = _poly_mul(inverse_product, factor)[:degree + 1]
        for k in range(multiplicities[j]):
            coefficients[j, k] = inverse_product[degree - k]
    return nodes, multiplicities, coefficients


def calibrate_confluent():
    counts = dict(configurations=0, monomial_identities=0,
                  selected_coefficients=0, factorial_indexing=0,
                  selected_polynomial_functionals=0, vanishing_lower_jets=0,
                  coefficient_bounds=0, denominator_scalings=0,
                  homogeneous_sanity_checks=0)
    spacing = Fraction(1, 3)
    for r in range(1, MAX_MULTIPLICITY + 1):
        for selected in range(7):
            nodes, multiplicities, coefficients = confluent_case(r, selected, spacing)
            order = 7 * r
            counts["configurations"] += 1
            _check(sum(multiplicities) == order + 1, "wrong confluent order")
            expected = homogeneous_coefficients(nodes, multiplicities, 6)
            power_sum1 = sum((m * x for x, m in zip(nodes, multiplicities)), Fraction(0))
            power_sum2 = sum((m * x * x for x, m in zip(nodes, multiplicities)), Fraction(0))
            _check(expected[:3] == [1, power_sum1, (power_sum1 ** 2 + power_sum2) / 2],
                   "complete homogeneous coefficient sanity check failed")
            counts["homogeneous_sanity_checks"] += 3
            for degree in range(order + 7):
                actual = sum((coefficient * comb(degree, k) * nodes[j] ** (degree - k)
                              for (j, k), coefficient in coefficients.items()
                              if degree >= k), Fraction(0))
                wanted = Fraction(0) if degree < order else expected[degree - order]
                _check(actual == wanted, f"monomial identity failed: r={r}, selected={selected}, d={degree}")
                counts["monomial_identities"] += 1

            selected_product = prod((nodes[selected] - nodes[h]) ** r
                                    for h in range(7) if h != selected)
            _check(coefficients[selected, r] * selected_product == 1,
                   "selected coefficient is not the reciprocal node product")
            _check(abs(selected_product) <= 12 ** r, "selected product bound failed")
            counts["selected_coefficients"] += 1
            for (j, k), coefficient in coefficients.items():
                _check(abs(coefficient) <= 2 ** (21 * r), "coefficient height bound failed")
                counts["coefficient_bounds"] += 1
                integer_scaled = 720 ** order * spacing ** (order - k) * coefficient
                _check(integer_scaled.denominator == 1, "720^M denominator clearing failed")
                counts["denominator_scalings"] += 1

            # Omega has degree M and order-r zeros at every original node.
            omega = [Fraction(1)]
            for node in nodes:
                for _ in range(r):
                    omega = _poly_mul(omega, [-node, Fraction(1)])
            for node in nodes:
                for k in range(r):
                    _check(normalized_jet(omega, node, k) == 0, "lower jet did not vanish")
                    counts["vanishing_lower_jets"] += 1
            derivative = factorial(r) * normalized_jet(omega, nodes[selected], r)
            _check(derivative == factorial(r) * selected_product, "r! normalization failed")
            counts["factorial_indexing"] += 1
            functional = sum((coefficient * normalized_jet(omega, nodes[j], k)
                              for (j, k), coefficient in coefficients.items()), Fraction(0))
            _check(functional == 1, "degree-M monic polynomial functional must be one")
            counts["selected_polynomial_functionals"] += 1
    return counts


def exponent_ledger():
    """Formal exponent vectors for U*K after r!/(7r)! <= r^(-6r).

    Each tuple lists coefficients of (1, q, n, r). Addition here is only
    symbolic bookkeeping; it is not a proof of the estimates being recorded.
    """
    upper = {"2": (1, 21, 0, 2), "3": (0, 0, 1, 8),
             "q": (4, 0, 1, 7), "H": (0, 6, 0, 0), "r": (0, 0, 0, -6)}
    lower_reciprocal = {"2": (1, 12, 0, 0), "3": (0, 0, 1, 1),
                        "q": (4, 0, 1, 1), "H": (0, 18, 0, 0), "r": (0, 0, 0, 0)}
    return {base: tuple(a + b for a, b in zip(upper[base], lower_reciprocal[base]))
            for base in upper}


def calibrate_parameter_bounds():
    wanted = {"2": (2, 33, 0, 2), "3": (0, 0, 2, 9),
              "q": (8, 0, 2, 8), "H": (0, 24, 0, 0), "r": (0, 0, 0, -6)}
    _check(exponent_ledger() == wanted, "U*K exponent collection failed")
    _check(2 ** 55 * 3 ** 11 * 7 ** 5 < 2 ** 88, "coarse constant domination failed")
    _check(3 ** 9 < 2 ** 15, "exponential majorant constant failed")
    _check(Fraction(factorial(6), 2 ** 6) < 12, "node product constant failed")
    parameter_cases = 0
    for height in (2, 3, 7, 16):
        q = 28 * 2 ** 44 * height ** 12
        n = q * q // 28
        constant = 2 ** 88 * height ** 24
        _check(q % 28 == 0 and q * q == 28 * n, "parameter divisibility failed")
        _check(n == 28 * constant and n >= q and n >= 4 * constant,
               "q(H) threshold arithmetic failed")
        # Do not construct B, a matrix, or powers with these huge exponents.
        parameter_cases += 1
    reduction_cases = 0
    # These are only examples of the conditional numerical reductions, not
    # actual auxiliary parameter choices. Keep every evaluated r <= 3; check
    # the actual q(H) divisibility relation separately above.
    for q, n, r in ((1, 1, 1), (1, 1, 2), (1, 2, 3),
                    (2, 2, 2), (2, 2, 3), (3, 3, 3)):
        _check(q <= r and n <= r and q * q <= 28 * r, "small conditional hypotheses failed")
        _check(8 * r + 2 * n <= 10 * r, "exponent reduction failed")
        _check(q ** 10 <= 28 ** 5 * r ** 5, "q-square reduction failed")
        _check(4 * q ** 8 <= 2 ** (10 * r), "polynomial prefactor bound failed")
        reduction_cases += 1
    factorial_cases = 0
    for r in range(1, MAX_MULTIPLICITY + 1):
        _check(factorial(7 * r) >= factorial(r) * r ** (6 * r),
               "factorial-ratio bound failed")
        factorial_cases += 1
    return dict(symbolic_exponent_components=5, coarse_constant_checks=3,
                parameter_cases=parameter_cases, small_reduction_cases=reduction_cases,
                factorial_cases=factorial_cases, auxiliary_matrices_allocated=0)


def _quad_add(left, right):
    return left[0] + right[0], left[1] + right[1]


def _quad_mul(left, right):
    return (left[0] * right[0] + 2 * left[1] * right[1],
            left[0] * right[1] + left[1] * right[0])


def _quad_pow(value, exponent):
    result = (1, 0)
    for _ in range(exponent):
        result = _quad_mul(result, value)
    return result


def calibrate_moments():
    identity_count = gap_count = nonvanishing_cases = 0
    for q in range(2, MAX_MOMENT_Q + 1):
        frequencies = [(i, j) for i in range(q) for j in range(q)]
        size = q * q
        for t, frequency in enumerate(frequencies):
            for other in frequencies[t + 1:]:
                gap = frequency[0] - other[0], frequency[1] - other[1]
                _check(gap[0] ** 2 - 2 * gap[1] ** 2 != 0, "frequency norm vanished")
                gap_count += 1
        vectors = ([(-1) ** t * (t + 1) for t in range(size)],
                   [int(t == 0) for t in range(size)])
        for vector in vectors:
            moments = []
            for k in range(size):
                moment = (0, 0)
                for coefficient, frequency in zip(vector, frequencies):
                    moment = _quad_add(moment, _quad_mul((coefficient, 0), _quad_pow(frequency, k)))
                moments.append(moment)
            _check(any(moment != (0, 0) for moment in moments), "all small moments vanished")
            nonvanishing_cases += 1
            for t, frequency in enumerate(frequencies):
                polynomial = [(1, 0)]
                gap_product = (1, 0)
                for u, other in enumerate(frequencies):
                    if u == t:
                        continue
                    new = [(0, 0)] * (len(polynomial) + 1)
                    for k, coefficient in enumerate(polynomial):
                        new[k] = _quad_add(new[k], _quad_mul(coefficient, (-other[0], -other[1])))
                        new[k + 1] = _quad_add(new[k + 1], coefficient)
                    polynomial = new
                    gap_product = _quad_mul(gap_product,
                                            (frequency[0] - other[0], frequency[1] - other[1]))
                left = (0, 0)
                for coefficient, moment in zip(polynomial, moments):
                    left = _quad_add(left, _quad_mul(coefficient, moment))
                right = _quad_mul((vector[t], 0), gap_product)
                _check(left == right, "quadratic moment-polynomial identity failed")
                identity_count += 1
    return dict(q_values=[2, 3], moment_identities=identity_count,
                nonzero_gap_norms=gap_count, nonvanishing_examples=nonvanishing_cases)


def calibrate_approximations():
    approximations = [c_approx(n) for n in range(MAX_PRECISION + 1)]
    bracket_checks = 0
    for n, value in enumerate(approximations):
        k = n + 8
        root = isqrt(2 * 2 ** (2 * k))
        _check(root * root <= 2 * 2 ** (2 * k) < (root + 1) ** 2,
               "integer-square-root bracket failed")
        _check(1 <= value <= 2, "finite approximation outside coarse range")
        bracket_checks += 1
    coherence_checks = 0
    for n, value in enumerate(approximations):
        for m in range(n + 1, len(approximations)):
            _check(abs(value - approximations[m]) <= Fraction(1, 2 ** n) + Fraction(1, 2 ** m),
                   "finite dyadic coherence check failed")
            coherence_checks += 1
    rows = []
    for a, b in CERTIFICATE_CASES:
        n = first_certificate(a, b)
        _check(n is not None, f"no bounded certificate found for {a}/{b}")
        rows.append(dict(a=a, b=b, precision=n))
    refined = approximations[MAX_PRECISION]
    radius = Fraction(1, 2 ** MAX_PRECISION)
    _check(Fraction(3, 2) < refined - radius, "lower finite enclosure comparison failed")
    _check(refined + radius < Fraction(7, 4), "upper finite enclosure comparison failed")
    return dict(precision_count=len(approximations), integer_sqrt_brackets=bracket_checks,
                finite_coherence_checks=coherence_checks, finite_enclosure_comparisons=2,
                certificate_count=len(rows), certificates=rows,
                analytic_accuracy_proved=False, certificate_soundness_proved=False)


def run_calibration():
    return dict(schema="sqrt2-power-exact-pilots-v1", authority=AUTHORITY,
                ha_evidence=False, admitted_theorems=0,
                tail_estimates_proved=False, universal_claims_proved=False,
                bounds=dict(max_precision=MAX_PRECISION, max_r=MAX_MULTIPLICITY,
                            max_moment_q=MAX_MOMENT_Q),
                confluent=calibrate_confluent(), parameter_bounds=calibrate_parameter_bounds(),
                quadratic_moments=calibrate_moments(), approximations=calibrate_approximations())


if __name__ == "__main__":
    print(json.dumps(run_calibration(), indent=2, sort_keys=True))
