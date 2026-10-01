"""Frozen, directly expanded HA leaves; never a silent replacement of a parent.

IR definitions remain proposed. Each source below uses only the existing HA
parser, and nonnegative numerator pairs represent signed quantities.
Unfinished analytic/computation bridges stay explicitly unfinished.
"""
from __future__ import annotations

from hashlib import sha256
import json

from sqrt2_power_campaign_spec import PILOT
from sqrt2_power_native import BASIS_NAMES, Basis, closed_formula
from peano_lab.library.proof_bundle import encode_formula


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def signed_moment_source():
    """Inlining conservative signed-pair operations; no guessed coefficient table."""
    def add(x, y):
        return f"({x[0]}+{y[0]})", f"({x[1]}+{y[1]})"
    def mul(x, y):
        return f"({x[0]}*{y[0]}+{x[1]}*{y[1]})", f"({x[0]}*{y[1]}+{x[1]}*{y[0]})"
    b0, b1, l0, l1 = ("a", "A"), ("b", "B"), ("c", "C"), ("d", "D")
    m0 = add(b0, b1)
    m1 = add(mul(b0, l0), mul(b1, l1))
    left, right = add(m1, mul(b0, l1)), add(mul(l1, m0), mul(b0, l0))
    return f"forall a A b B c C d D. {left[0]}+{right[1]}={left[1]}+{right[0]}"


SPECS = {
    "P01": dict(
        leaf_id="P01", coverage="full_pilot_contract", native_factory="p01",
        interpretation="RatEq addition for arbitrary signed numerator pairs; all four input denominators and both output products are nonzero naturals (therefore positive). Equality and product guards are in the actual target.",
        source=("forall p m d P M D q n e Q N E. "
            "~(d=0) -> ~(e=0) -> ~(D=0) -> ~(E=0) -> "
            "p*D+M*d=m*D+P*d -> q*E+N*e=n*E+Q*e -> "
            "(~(d*e=0) /\\ (~(D*E=0) /\\ "
            "((p*e+q*d)*(D*E)+(M*E+N*D)*(d*e)="
            "(m*e+n*d)*(D*E)+(P*E+Q*D)*(d*e))))")),
    "P02": dict(
        leaf_id="P02-natural-core", coverage="supporting_subleaf_only", native_factory="ring",
        interpretation="Subtraction-free norm polynomial identity over natural coefficients. The lift to all signed coefficient pairs in P02 remains separate and is NOT closed by this target.",
        source=("forall a b c d. "
            "(a*c+2*b*d)*(a*c+2*b*d)+2*(a*a)*(d*d)+2*(b*b)*(c*c)="
            "2*(a*d+b*c)*(a*d+b*c)+(a*a)*(c*c)+4*(b*b)*(d*d)")),
    "P03": dict(
        leaf_id="P03-semiring-step", coverage="supporting_subleaf_only", native_factory="p03_step",
        interpretation="One algebraic induction step with an explicit equality hypothesis. Rational representation and power/fold trace links in the full P03 contract remain open.",
        source="forall x y X Y T. X+y*T=Y+x*T -> x*X+y*(X+y*T)=y*Y+x*(X+y*T)"),
    "P05": dict(
        leaf_id="P05", coverage="full_pilot_contract", native_factory="p05_step",
        interpretation="Set k=n+2, so k>=2. a=f_k and b=f_(k-1) are explicitly assumed 2. The proposed next coefficient is the literal 2; this proves only the fixed recurrence step, not coefficient uniqueness or its base cases.",
        source="forall n a b. a=2 -> b=2 -> (S (S n)+1)*2=2*a+S n*b"),
    "P06": dict(
        leaf_id="P06-cleared-contraction", coverage="supporting_subleaf_only", native_factory="mul_transport",
        factor_index=2, reverse_premise=True,
        interpretation="The product-order algebra with an explicit nonnegative slack h. Positive rational denominator and factorial/power witness links remain required for full P06.",
        source="forall p u h C. C=2*p+h -> 2*(p*u)+h*u=C*u"),
    "P07": dict(
        leaf_id="P07", coverage="full_pilot_contract", native_factory="ring",
        interpretation="The two-frequency identity for four arbitrary signed integers, represented by eight natural components. M0 and M1 are inlined by exact signed-pair addition/multiplication. The arbitrary-N quadratic moment theorem IR045 remains open.",
        source=signed_moment_source()),
    "P08": dict(
        leaf_id="P08-reciprocal-cancellation", coverage="supporting_subleaf_only", native_factory="mul_transport",
        factor_index=0, reverse_premise=False,
        interpretation="Cancellation algebra assuming the reciprocal recurrence d*v=u. This does not establish nonzero d, rational inverse existence, powers, or full P08. Removing d!=0 is not a falsehood test of THIS weaker conditional identity.",
        source="forall d u v m. d*v=u -> d*(m*v)=m*u"),
    "P11": dict(
        leaf_id="P11-cleared-precision", coverage="supporting_subleaf_only", native_factory="exists_transport",
        interpretation="Constructively transports an explicit additive witness for 12V<=e into the cleared precision comparison. The product V=KSJ and denominator positivity are still separate obligations; no rational interpretation is assumed by this formula.",
        source="forall V e. (exists h. 12*V+h=e) -> exists w. 3*(4*V)+w=e"),
}

PENDING = {
    "P04": "A precisely fixed finite composition and its coefficient witnesses remain to be connected to HA; 1=1 is not a replacement.",
    "P09": "Exact r=1 coefficient tables are separately elaborated; native trace and denominator-clearing links remain required.",
    "P10": "The full closed statement is separately elaborated, but the binary certificate assembly hits its copy-work cap. Small binary proofs pass; this large target remains unresolved. Do not increase unary norm_num limits.",
    "P12": "The full fixed CApprox execution trace must be connected to its final rational comparison by HA proofs.",
}


def contracts():
    result = []
    basic = Basis()
    allowed = [{"name": name, "source": basic.specs[name][1],
                "source_file_sha256": basic.source_sha256,
                "statement_ast_sha256": sha256(canonical(encode_formula(closed_formula(basic.specs[name][1])))).hexdigest()}
               for name in sorted(BASIS_NAMES)]
    for parent in PILOT:
        row = dict(pilot_id=parent["id"], parent=parent["parent"],
                   pilot_contract=parent["contract"],
                   pilot_contract_sha256=sha256(canonical(parent)).hexdigest(),
                   closes_IR_parent=False, allowed_external_premises=allowed,
                   source=None, statement_ast=None, statement_ast_sha256=None,
                   coverage="unelaborated", dispatchable=False)
        if parent["id"] in SPECS:
            row.update(SPECS[parent["id"]])
            formula = closed_formula(row["source"])
            row["statement_ast"] = encode_formula(formula)
            row["statement_ast_sha256"] = sha256(canonical(row["statement_ast"])).hexdigest()
            row["dispatchable"] = True
        else:
            row["reason"] = PENDING[parent["id"]]
        row["contract_sha256"] = sha256(canonical(row)).hexdigest()
        result.append(row)
    return result
