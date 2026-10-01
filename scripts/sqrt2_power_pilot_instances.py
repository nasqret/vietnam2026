"""Deterministic P04/P08/P09/P10/P12 instances and arithmetic subleaves.

This is contract/adapter engineering, NOT proof search or HA evidence. A source
formula is not a certificate, and a checked arithmetic subleaf would not by
itself close its pilot or the pilot's universal parent. No library or theorem
loader is imported. Main prints a compact inventory, not the large source set.
"""

from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
import json
from math import comb, factorial, isqrt, lcm, prod


AUTHORITY = "exact_instance_specification_only"
MAX_INTEGER_BITS = 8192


def _balanced(operator, terms, identity):
    terms = list(terms)
    if not terms:
        return identity
    if len(terms) == 1:
        return terms[0]
    middle = len(terms) // 2
    return f"({_balanced(operator, terms[:middle], identity)} {operator} {_balanced(operator, terms[middle:], identity)})"


@lru_cache(maxsize=128)
def fixed_power_term(base, exponent):
    """A fixed power is multiplication syntax, never a new HA function."""
    if type(base) is not int or base < 0 or type(exponent) is not int or not 0 <= exponent <= 8192:
        raise ValueError("invalid bounded fixed power")
    return _balanced("*", [nat_term(base)] * exponent, "S(0)")


@lru_cache(maxsize=256)
def nat_term(value):
    """Balanced ordinary 0/S/+/* spelling; no giant decimal/unary literal."""
    if type(value) is not int or value < 0 or value.bit_length() > MAX_INTEGER_BITS:
        raise ValueError("invalid bounded natural numeral")
    if value < 16:
        return "S(" * value + "0" + ")" * value
    split = value.bit_length() // 2
    high, low = divmod(value, 1 << split)
    high_term = f"({nat_term(high)} * {fixed_power_term(2, split)})"
    return high_term if low == 0 else f"({high_term} + {nat_term(low)})"


def _mul(*terms):
    return _balanced("*", terms, "S(0)")


def _add(*terms):
    return _balanced("+", terms, "0")


def _power_variable(name, exponent):
    return _balanced("*", [name] * exponent, "S(0)")


def _forall(names, formula):
    return "".join(f"forall {name}. " for name in names) + formula


def _source(identifier, formula, meaning):
    return dict(id=identifier, formula=formula, meaning=meaning,
                signature="0,S,+,*,=,bot,and,or,implies,forall,exists",
                expected_free_names=[], formula_sha256=sha256(formula.encode()).hexdigest(),
                authority=AUTHORITY, ha_checked=False, closes_pilot=False, closes_parent=False)


def _pilot(identifier, parent, status, gaps):
    return dict(id=identifier, parent=parent, authority=AUTHORITY,
                fully_elaborated_pilot=False, native_replay_performed=False,
                closes_pilot=False, closes_parent=False, contract_status=status,
                outstanding_bridges=gaps, sources=[])


def _poly_mul(left, right, degree):
    out = [Fraction(0)] * (degree + 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            if i + j <= degree:
                out[i + j] += a * b
    return out


def _rat(value):
    value = Fraction(value)
    return [value.numerator, value.denominator]


def p04_instance():
    record = _pilot("P04", "IR079", "fixed-degree-7 composition and guarded coefficient subleaf ready", [
        "The pilot text does not specify a truncation degree; this selects outer/inner degree 7 only.",
        "Tie the emitted finite coefficient table to the chosen formal-composition encoding in HA.",
        "A proof of the guarded arithmetic equality is not by itself a formal-series proof."])
    degree = 7
    inner = [Fraction(0)] * (degree + 1)
    for j in range(4):
        inner[2 * j + 1] = Fraction(2, 2 * j + 1)
    power = [Fraction(1)] + [Fraction(0)] * degree
    result = [Fraction(0)] * (degree + 1)
    constant_rows = []
    for k in range(degree + 1):
        constant_rows.append(dict(power=k, coefficient=_rat(power[0]), factorial=factorial(k)))
        result = [a + b / factorial(k) for a, b in zip(result, power)]
        power = _poly_mul(power, inner, degree)
    scale = factorial(degree)
    left = _add(*(_mul(nat_term(scale // factorial(k)), _power_variable("a", k))
                  for k in range(degree + 1)))
    formula = _forall(["a"], f"a = 0 -> {left} = {nat_term(scale)}")
    record.update(truncation_degree=degree, inner_coefficients=list(map(_rat, inner)),
                  composition_prefix=list(map(_rat, result)), constant_power_rows=constant_rows,
                  mutation=dict(a0=1, scaled_constant=sum(scale // factorial(k) for k in range(8)),
                                expected_scale=scale, equality_holds=False))
    record["sources"] = [_source("P04.constant-subleaf", formula,
        "Given A_0=a=0, clear 7! in sum(k<=7,A_0^k/k!)=1; finite degree-7 arithmetic only.")]
    return record


def p08_instance():
    record = _pilot("P08", "IR055", "signed-rational cancellation subleaf ready; power graph unelaborated", [
        "No variable-exponent Pow graph, inverse trace, or c0/c1 definition is admitted here.",
        "Establish d*v=u from the requested power/inverse witnesses, then identify c0=u,c1=-m*v.",
        "Removing d!=0 leaves the cancellation implication true; reject that mutation at full-contract level."])
    m = "S(k)"
    dv_pos = _add(_mul("dp", "vp"), _mul("dm", "vm"))
    dv_neg = _add(_mul("dp", "vm"), _mul("dm", "vp"))
    premise = f"{_add(_mul(dv_pos, 'ud'), _mul('um', 'dd', 'vd'))} = {_add(_mul(dv_neg, 'ud'), _mul('up', 'dd', 'vd'))}"
    conclusion = f"{_add(_mul(_add(_mul('dp', m, 'vm'), _mul('dm', m, 'vp')), 'ud'), _mul(m, 'up', 'dd', 'vd'))} = {_add(_mul(_add(_mul('dp', m, 'vp'), _mul('dm', m, 'vm')), 'ud'), _mul(m, 'um', 'dd', 'vd'))}"
    guards = "(exists zd. dd = S(zd)) -> (exists zu. ud = S(zu)) -> (exists zv. vd = S(zv)) -> (dp = dm -> bot) -> "
    names = ["dp", "dm", "up", "um", "vp", "vm", "dd", "ud", "vd", "k"]
    record["sources"] = [_source("P08.cancellation-subleaf", _forall(names, guards + f"({premise}) -> {conclusion}"),
        "d=(dp-dm)/dd, u=(up-um)/ud, v=(vp-vm)/vd, m=S(k); d*v=u implies d*(-m*v)+m*u=0 after positive denominator clearing.")]
    record["mutation"] = dict(sign_flip_counterexample=dict(d=1, m=1, u=1, v=1, wrong_sum=2),
                              nonzero_guard_removal="manifest rejection, not a false cancellation identity")
    return record


def _reciprocal_table(multiplicities):
    """Only the fixed seven integer nodes and multiplicities 1 or 2."""
    if len(multiplicities) != 7 or any(m not in (1, 2) for m in multiplicities):
        raise ValueError("unsupported fixed reciprocal table")
    rows = []
    for j, multiplicity in enumerate(multiplicities):
        constant = prod((Fraction(j - h) ** (-mh)
                         for h, mh in enumerate(multiplicities) if h != j), start=Fraction(1))
        if multiplicity == 2:
            linear = -constant * sum((Fraction(mh, j - h)
                                     for h, mh in enumerate(multiplicities) if h != j), Fraction(0))
            rows.append((j, 0, linear))
        rows.append((j, multiplicity - 1, constant))
    return rows


def p09_instance():
    record = _pilot("P09", "IR056", "actual fixed confluent coefficient table and cleared identity ready", [
        "Replay the coefficient witnesses and their interpretation as truncated reciprocal products.",
        "Bridge rational L0=p/d and nonzero scaling to this homogeneous cleared polynomial identity.",
        "This is r=1, selected node 3, degree 7 only; no universal-r assertion."])
    order = 7
    coefficients = _reciprocal_table([1, 1, 1, 2, 1, 1, 1])
    common = lcm(*(value.denominator for _, _, value in coefficients))
    scale = 720 ** order
    full_scale = factorial(order) * scale
    rows, positives, negatives = [], [], []
    value = Fraction(0)
    for j, k, coefficient in coefficients:
        normalized_jet = comb(order, k) * j ** (order - k)
        value += coefficient * normalized_jet
        cleared = coefficient * scale
        if cleared.denominator != 1:
            raise AssertionError("denominator did not divide 720^7")
        weighted = factorial(order) * cleared.numerator * comb(order, k)
        jet_term = _mul(nat_term(abs(weighted)), _power_variable("p", k),
                        _power_variable(_mul(nat_term(j), "p"), order - k))
        (positives if weighted >= 0 else negatives).append(jet_term)
        rows.append(dict(node=j, derivative=k, coefficient=_rat(coefficient),
                         normalized_monomial_jet=normalized_jet,
                         common_weight=int(coefficient * common), scaled_weight=cleared.numerator))
        record["sources"].append(_source(f"P09.coefficient-{j}-{k}",
            f"{_mul(nat_term(abs(cleared.numerator)), nat_term(coefficient.denominator))} = {_mul(nat_term(scale), nat_term(abs(coefficient.numerator)))}",
            "Absolute numerator identity witnessing signed coefficient multiplication by 720^7; the coefficient sign is retained in the table."))
    if value != 1:
        raise AssertionError("the actual confluent monomial functional is not one")
    equality = f"{_add(*positives)} = {_add(_mul(nat_term(full_scale), _power_variable('p', order)), *negatives)}"
    guards = "(exists zd. d = S(zd)) -> (exists lo. d + lo = S(S(S(S(0)))) * p) -> (exists hi. S(S(0)) * p + hi = d) -> "
    record["sources"].append(_source("P09.cleared-monomial-instance", _forall(["p", "d"], guards + equality),
        "Multiply D(t^7)=1 by 7!*(720*L0)^7, substitute L0=p/d, and clear d^7; positive/negative coefficient sums are kept on opposite sides."))
    mutated = _reciprocal_table([1] * 7)
    mutated_value_at_one = sum((coefficient * j ** 7 for j, k, coefficient in mutated), Fraction(0))
    # With only seven simple nodes the order is six, so this degree-seven
    # functional scales by L0, not by L0^0. Use a counterexample inside the
    # original [1/4,1/2] spacing interval.
    mutated_spacing = Fraction(1, 3)
    mutated_value = mutated_spacing * mutated_value_at_one
    record.update(r=1, selected_node=3, monomial_degree=7,
                  common_denominator=common, scale_720_power=scale, full_clearing_scale=full_scale,
                  coefficients=rows, exact_functional_value=_rat(value),
                  mutation=dict(selected_multiplicity=1, L0=_rat(mutated_spacing),
                                at_L0_one_third_value=_rat(mutated_value),
                                equals_one=mutated_value == 1))
    return record


def addition_columns(left, right):
    """Binary carry data; assembling its small leaves into HA is a separate task."""
    if min(left, right) < 0 or max(left.bit_length(), right.bit_length()) > MAX_INTEGER_BITS:
        raise ValueError("invalid bounded addition")
    total = left + right
    carry = 0
    rows = []
    for index in range(max(left.bit_length(), right.bit_length(), total.bit_length()) + 1):
        a, b = (left >> index) & 1, (right >> index) & 1
        result_bit = (total >> index) & 1
        next_carry = (a + b + carry) // 2
        rows.append(dict(index=index, a=a, b=b, carry=carry, result=result_bit, next_carry=next_carry))
        if a + b + carry != result_bit + 2 * next_carry:
            raise AssertionError("bad binary carry")
        carry = next_carry
    if carry:
        raise AssertionError("unconsumed carry")
    return rows


def p10_instance():
    record = _pilot("P10", "IR064", "full closed target frozen; binary certificate assembly pending", [
        "Compact numeral parsing is available, but generic decide/norm_num proof normalization is unary and bounded.",
        "Replay the fixed-power arithmetic and assemble binary addition/carry witnesses into the original closed target.",
        "Small carry equalities alone do not close P10."])
    # Statement elaboration and proof construction are deliberately separate:
    # this entire closed pilot target has a fixed-signature formula below.
    record["fully_elaborated_pilot"] = True
    record["full_target_formula_id"] = "P10.full-closed-target"
    left = 2 ** 55 * 3 ** 11 * 7 ** 5
    right = 2 ** 88
    difference = right - left
    lhs = _mul(fixed_power_term(2, 55), fixed_power_term(3, 11), fixed_power_term(7, 5))
    rhs = fixed_power_term(2, 88)
    record.update(left=left, right=right, difference=difference,
                  left_bits=left.bit_length(), right_bits=right.bit_length(),
                  binary_addition_columns=addition_columns(left, difference),
                  fixed_exponents={"2_left": 55, "3": 11, "7": 5, "2_right": 88},
                  mutation=dict(right_exponent=85, exact_inequality_holds=left <= 2 ** 85))
    record["sources"] = [
        _source("P10.full-closed-target", f"exists delta. {_add(lhs, 'delta')} = {rhs}",
                "The literal closed P10 inequality, with <= expanded as a natural additive witness and all powers expanded into fixed multiplication terms."),
        _source("P10.explicit-difference-subleaf", f"{_add(lhs, nat_term(difference))} = {rhs}",
                "Explicit additive witness for P10; requires a real HA arithmetic certificate, not host integer comparison."),
    ]
    return record


def _trace_step(rows, label, operation, inputs, result):
    rows.append(dict(id=label, operation=operation, inputs=list(map(_rat, inputs)), output=_rat(result)))
    return result


def p12_trace():
    """The fixed n=6 CApprox execution; direct powers/factorials, no tail claim."""
    n, k = 6, 14
    integer_steps = []
    tables = {}
    for base, stop in ((2, 2 * k + 1), (3, 2 * k - 1)):
        values = [1]
        for exponent in range(1, stop + 1):
            values.append(values[-1] * base)
            integer_steps.append(dict(id=f"power{base}-{exponent}", operation="mul",
                                      inputs=[values[-2], base], output=values[-1]))
        tables[base] = values
    scale, radicand = tables[2][k], tables[2][2 * k + 1]
    root = isqrt(radicand)
    rows = []
    s = _trace_step(rows, "sqrt-rational", "div", [Fraction(root), Fraction(scale)], Fraction(root, scale))
    partial = Fraction(0)
    for j in range(k):
        odd = 2 * j + 1
        denominator = odd * tables[3][odd]
        integer_steps.append(dict(id=f"log-denominator-{j}", operation="mul",
                                  inputs=[odd, tables[3][odd]], output=denominator))
        term = _trace_step(rows, f"log-term-{j}", "div", [Fraction(1), Fraction(denominator)], Fraction(1, denominator))
        partial = _trace_step(rows, f"log-sum-{j}", "add", [partial, term], partial + term)
    log2 = _trace_step(rows, "log2-scale", "mul", [Fraction(2), partial], 2 * partial)
    argument = _trace_step(rows, "argument", "div", [log2, s], log2 / s)
    power, fact, exponential = Fraction(1), 1, Fraction(1)
    for j in range(1, k + 3):
        power = _trace_step(rows, f"argument-power-{j}", "mul", [power, argument], power * argument)
        integer_steps.append(dict(id=f"factorial-{j}", operation="mul", inputs=[fact, j], output=fact * j))
        fact *= j
        term = _trace_step(rows, f"exp-term-{j}", "div", [power, Fraction(fact)], power / fact)
        exponential = _trace_step(rows, f"exp-sum-{j}", "add", [exponential, term], exponential + term)
    return dict(n=n, k=k, exp_degree=k + 2, integer_steps=integer_steps, rational_steps=rows,
                root=root, root_scale=scale, radicand=radicand,
                root_lower_difference=radicand - root * root,
                root_upper_strict_witness=(root + 1) ** 2 - radicand - 1,
                sqrt_rational=_rat(s), log2_partial=_rat(log2), argument=_rat(argument),
                approximation=_rat(exponential))


def validate_p12_trace(trace):
    """Strict deterministic regeneration, not a checker for HA proof terms."""
    if trace != p12_trace():
        raise ValueError("P12 trace differs from the fixed CApprox execution")
    return True


def p12_trace_sources(trace):
    """Generate portable cross-multiplied arithmetic leaves lazily."""
    validate_p12_trace(trace)
    for step in trace["integer_steps"]:
        left, right = map(nat_term, step["inputs"])
        yield _source("P12." + step["id"], f"{_mul(left, right)} = {nat_term(step['output'])}",
                      "One fixed integer multiplication in the CApprox execution; not the whole trace graph.")
    for step in trace["rational_steps"]:
        (a, b), (c, d) = step["inputs"]
        e, f = step["output"]
        a, b, c, d, e, f = map(nat_term, (a, b, c, d, e, f))
        if step["operation"] == "add":
            left, right = _mul(_add(_mul(a, d), _mul(c, b)), f), _mul(e, b, d)
        elif step["operation"] == "mul":
            left, right = _mul(a, c, f), _mul(e, b, d)
        else:
            left, right = _mul(a, d, f), _mul(e, b, c)
        yield _source("P12." + step["id"], f"{left} = {right}",
                      "One exact rational operation after denominator clearing; positive denominators and trace-graph linkage remain separate leaves.")
    positive = {denominator for row in trace["rational_steps"]
                for _, denominator in row["inputs"] + [row["output"]]}
    positive.update(row["inputs"][1][0] for row in trace["rational_steps"] if row["operation"] == "div")
    for index, value in enumerate(sorted(positive)):
        if value <= 0:
            raise AssertionError("trace divisor is not positive")
        yield _source(f"P12.positive-denominator-{index}", f"{nat_term(value)} = S({nat_term(value - 1)})",
                      "An explicit successor witness for a denominator or divisor numerator used in the fixed trace.")


def p12_instance():
    record = _pilot("P12", "IR071", "complete host execution trace; HA CApprox graph unelaborated", [
        "IRD09's beta-coded execution/trace relation has not been admitted or fully expanded to the fixed HA signature.",
        "Replay every arithmetic trace leaf, its positive denominator witnesses, and the trace linkage/initial conditions.",
        "The final integer comparison alone neither closes P12 nor proves approximation accuracy or irrationality."])
    trace = p12_trace()
    numerator, denominator = trace["approximation"]
    # For a=3,b=2,n=6: 2*u-3>4/64 clears to 196*den < 128*num.
    left, right = 196 * denominator, 128 * numerator
    strict_witness = right - left - 1
    if strict_witness < 0:
        raise AssertionError("the specified finite P12 inequality failed")
    root, radicand = trace["root"], trace["radicand"]
    record["sources"] = [
        _source("P12.sqrt-lower", f"{_add(_mul(nat_term(root), nat_term(root)), nat_term(trace['root_lower_difference']))} = {nat_term(radicand)}",
                "Concrete lower integer-square-root bracket witness."),
        _source("P12.sqrt-upper", f"{_add(nat_term(radicand), 'S(' + nat_term(trace['root_upper_strict_witness']) + ')')} = {_mul(nat_term(root + 1), nat_term(root + 1))}",
                "Concrete strict upper integer-square-root bracket witness."),
        _source("P12.final-inequality-subleaf", f"{_add(_mul(nat_term(196), nat_term(denominator)), 'S(' + nat_term(strict_witness) + ')')} = {_mul(nat_term(128), nat_term(numerator))}",
                "Only the final |2*u_6-3|>1/16 comparison, assuming this numerator/denominator is linked to the complete CApprox trace."),
    ]
    record.update(a=3, b=2, precision=6, trace=trace,
                  comparison=dict(left=left, right=right, strict_witness=strict_witness),
                  numerator_bits=numerator.bit_length(), denominator_bits=denominator.bit_length(),
                  mutation="Change any trace entry; deterministic regeneration rejects it before native dispatch.")
    return record


def build_pilot_instances():
    return dict(schema="sqrt2-power-pilot-instances-v1", authority=AUTHORITY,
                ha_checked=False, completed_pilots=0, completed_parents=0,
                pilots=[p04_instance(), p08_instance(), p09_instance(), p10_instance(), p12_instance()])


def summary(instances=None):
    instances = instances or build_pilot_instances()
    rows = []
    for pilot in instances["pilots"]:
        row = {key: pilot[key] for key in ("id", "parent", "contract_status", "fully_elaborated_pilot", "closes_pilot", "closes_parent")}
        row["immediate_source_count"] = len(pilot["sources"])
        if pilot["id"] == "P12":
            row.update(integer_trace_steps=len(pilot["trace"]["integer_steps"]),
                       rational_trace_steps=len(pilot["trace"]["rational_steps"]),
                       numerator_bits=pilot["numerator_bits"], denominator_bits=pilot["denominator_bits"])
        rows.append(row)
    return dict(schema=instances["schema"], authority=AUTHORITY, ha_checked=False,
                completed_pilots=0, completed_parents=0, pilots=rows)


if __name__ == "__main__":
    print(json.dumps(summary(), indent=2, sort_keys=True))
