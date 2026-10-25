"""Prepare inspectable scripts; this program performs no native proof search."""
from pathlib import Path
import argparse
import hashlib
import json
import signal
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
APP = ROOT / "hydra-playground"
sys.path[:0] = [str(HERE), str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
signal.alarm(9)

from arithmetic_search import _add, _equations, _number, _polynomial, _quote, _witness
from polynomial_chunks import polynomial_chunk_plan
from peano_lab.engine.state import instantiate_formula
from peano_lab.kernel.formulas import Eq, Exists, Forall, parse_formula_with_names, pretty_formula
from peano_lab.kernel.terms import Add, Mul, Succ, Var, pretty_term


def power(term, degree):
    result = term
    for _ in range(degree - 1):
        result = Mul(result, term)
    return result


def case_from_equation(case_id, theorem, binders):
    target, _ = parse_formula_with_names(theorem)
    for _ in binders:
        assert type(target) is Forall
        target = target.body
    plan = polynomial_chunk_plan(target, list(reversed(binders)))
    return {"case_id": case_id, "theorem": theorem, "plan_generated": plan is not None,
            "commands": None if plan is None else [*("intro " + name for name in binders), *plan.commands],
            "obligations": [] if plan is None else plan.obligations}


def fermat_case(degree):
    """Use the existing generic witness synthesizer, then decompose its bridges."""
    n, k = Var(1), Var(0)
    ih = Eq(power(n, degree), Add(n, Mul(_number(degree), k)))
    target = Exists(Eq(power(Succ(Var(2)), degree), Add(Succ(Var(2)), Mul(_number(degree), Var(0)))))
    context = (("IH_witness", ih),)
    found = _witness(target, _equations(context))
    assert found is not None
    witness = found[0]
    instance = instantiate_formula(target.body, witness)
    difference = _add(_polynomial(instance.left), _polynomial(ih.left), -1)
    middle = Add(ih.left, _quote(difference))
    first = polynomial_chunk_plan(Eq(instance.left, middle), ["x", "n"], context)
    second = polynomial_chunk_plan(Eq(Add(ih.right, _quote(difference)), instance.right), ["x", "n"], context)
    theorem = "forall n. exists k. " + pretty_formula(
        Eq(power(Var(1), degree), Add(Var(1), Mul(_number(degree), Var(0)))), ["k", "n"])
    generated = first is not None and second is not None
    commands = None if not generated else ["intro n", "induction n", "exists 0", "simp", "cases IH",
        "exists (" + pretty_term(witness, ["x", "n"]) + ")", "trans (" + pretty_term(middle, ["x", "n"]) + ")",
        *first.commands, "rewrite IH_witness", *second.commands]
    return {"case_id": "fermat_" + str(degree), "theorem": theorem,
            "plan_generated": generated, "commands": commands,
            "first_bridge_steps": None if first is None else len(first.commands),
            "second_bridge_steps": None if second is None else len(second.commands),
            "witness": pretty_term(witness, ["x", "n"]),
            "obligations": [] if not generated else [*first.obligations, *second.obligations]}


def prepare():
    expanded = power(Succ(Var(0)), 7)
    expansion = "forall n. " + pretty_formula(Eq(expanded, _quote(_polynomial(expanded))), ["n"])
    return [
        case_from_equation("expansion_7", expansion, ["n"]),
        fermat_case(7),
        case_from_equation("sophie_coordinates",
            "forall a b. (a+b)*(a+b)*(a+b)*(a+b)+4*b*b*b*b=(a*a+b*b)*(a*a+4*a*b+5*b*b)", ["a", "b"]),
        case_from_equation("brahmagupta_balanced",
            "forall a b c d. (a*a+b*b)*(c*c+d*d)+4*a*b*c*d=(a*c+b*d)*(a*c+b*d)+(a*d+b*c)*(a*d+b*c)", ["a", "b", "c", "d"]),
        case_from_equation("pythagorean_positive",
            "forall a b. (a*a+2*a*b)*(a*a+2*a*b)+2*b*(a+b)*(2*b*(a+b))=(a*a+2*a*b+2*b*b)*(a*a+2*a*b+2*b*b)", ["a", "b"]),
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", required=True)
    args = parser.parse_args()
    assert args.attempt.isascii() and args.attempt.replace("-", "").isalnum()
    out = HERE / args.attempt
    out.mkdir(exist_ok=False)
    pins = {}
    for path in (Path(__file__), HERE / "polynomial_chunks.py", APP / "arithmetic_search.py"):
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        pins[str(path.relative_to(ROOT))] = digest
        archive = HERE / "source-archive" / (digest + "-" + path.name)
        if not archive.exists():
            with archive.open("xb") as stream:
                stream.write(data)
    cases = prepare()
    result = {"schema": "hydra-polynomial-chunk-plans-v1", "native_execution": False,
              "proof_claims": False, "source_pins": pins, "cases": cases}
    with (out / "plans.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    for case in cases:
        print(json.dumps({"case_id": case["case_id"], "generated": case["plan_generated"],
                          "steps": None if case["commands"] is None else len(case["commands"]),
                          "obligations": len(case["obligations"]),
                          "max_line_bytes": max((len(line.encode("utf-8")) for line in case["commands"] or ()), default=0)}))
