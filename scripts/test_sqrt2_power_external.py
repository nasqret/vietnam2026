"""Typed classical-hint exporters and bounded invocation; no proof authority."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

PATH = Path(__file__).with_name("sqrt2_power_external.py")
spec = importlib.util.spec_from_file_location("sqrt2_external_test_subject", PATH)
external = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = external
spec.loader.exec_module(external)
from peano_lab.kernel.formulas import Eq, Forall, parse_formula  # noqa: E402
from peano_lab.kernel.terms import Add, Succ, Var, Zero  # noqa: E402


def test_smt_preserves_closed_debruijn_mapping_and_both_natural_guards():
    problem = external.export_problem("forall a. exists b. b = a + 1")
    assert "(forall ((v0 Int)) (=> (>= v0 0) (exists ((v1 Int)) (and (>= v1 0)" in problem["input"]
    assert "(= v1 (+ v0 (+ 0 1)))" in problem["input"]
    assert "(set-option :produce-proofs true)" in problem["input"]
    assert problem["input"].endswith("(check-sat)\n(get-proof)\n")
    assert external.validate_problem(problem) == problem
    assert not problem["induction_included"] and not problem["ha_translation_verified"]


def test_tptp_is_guarded_with_exact_six_kernel_axioms_no_induction():
    from peano_lab.kernel.checker import axiom_formula
    problem = external.export_problem("forall n. n + 0 = n", format="tptp")
    assert "fof(target,conjecture,(! [V0] : (nat(V0) => (add(V0,zero) = V0))))" in problem["input"]
    assert "nat(s(X))" in problem["input"] and "nat(add(X,Y))" in problem["input"]
    axioms = [row for row in problem["background"] if row["kind"] == "actual_kernel_arithmetic_axiom"]
    assert [row["name"] for row in axioms] == ["pa1", "pa2", "pa3", "pa4", "pa5", "pa6"]
    assert all(row["ast_sha256"] == external.ast_sha256(axiom_formula(row["name"].upper())) for row in axioms)
    assert not problem["induction_included"]
    assert external.validate_problem(problem) == problem


def test_names_are_metadata_not_injected_solver_syntax_and_order_is_exact():
    premises = (("Second", "0 = 0"), ("First", "forall x. x = x"))
    problem = external.export_problem("0 = 0", premises)
    assert [row["name"] for row in problem["premises"]] == ["Second", "First"]
    assert [row["export_name"] for row in problem["premises"]] == ["p000", "p001"]
    assert "Second" not in problem["input"]
    with pytest.raises(external.ExportError):
        external.validate_export(problem, "0 = 0", tuple(reversed(premises)))


def test_alias_spelling_shares_ast_not_source_hash():
    left = external.export_problem("forall n. n = n")
    right = external.export_problem("forall m. m = m")
    assert left["target"]["ast_sha256"] == right["target"]["ast_sha256"]
    assert left["target"]["source_sha256"] != right["target"]["source_sha256"]
    external.validate_export(left, parse_formula("forall z. z = z"))


def test_existing_order_sugar_exports_its_actual_existential_ast():
    problem = external.export_problem("forall n. n <= n")
    ast = problem["target"]["ast"]
    assert ast[0] == "Forall" and ast[1][0] == "Exists"
    assert "(exists ((v1 Int)) (and (>= v1 0)" in problem["input"]


@pytest.mark.parametrize("source", ["x = x", "forall n. sqrt(n) = n", "1 - 1 = 0",
    "forall n. n^2 = n*n", "forall n. n = n; (exit)", "9" * 40000 + " = 0", ""])
def test_unsupported_or_excessive_source_fails_closed(source):
    with pytest.raises(external.ExportError): external.export_problem(source)


def test_foreign_subclass_ill_scoped_index_boolean_and_cycle_are_rejected():
    class Foreign(Eq): pass
    cycle = object.__new__(Succ)
    object.__setattr__(cycle, "term", cycle)
    for formula in (Foreign(Zero(), Zero()), Eq(Var(0), Var(0)),
                    Forall(Eq(Var(True), Zero())), Eq(cycle, Zero())):
        with pytest.raises(external.ExportError): external.export_problem(formula)


def test_deep_and_large_shared_ast_are_bounded_before_printing():
    deep = Zero()
    for _ in range(129): deep = Succ(deep)
    huge = Zero()
    for _ in range(14): huge = Add(huge, huge)
    for formula in (Eq(deep, Zero()), Eq(huge, Zero())):
        with pytest.raises(external.ExportError): external.export_problem(formula)


@pytest.mark.parametrize("premises", [[], (("same", "0=0"), ("same", "0=0")),
    (("bad);include", "0=0"),), (("p", "x=x"),), tuple(("p"+str(i), "0=0") for i in range(17))])
def test_premise_contract_fails_closed(premises):
    with pytest.raises(external.ExportError): external.export_problem("0=0", premises)


@pytest.mark.parametrize("mutation", ["text", "guard", "target", "source", "extra", "nested_extra", "boolean_index"])
def test_changed_even_resealed_problem_rejected(mutation):
    problem = external.export_problem("forall n. n = n")
    if mutation == "text": problem["input"] += "(assert false)\n"
    elif mutation == "guard": problem["input"] = problem["input"].replace("(>= v0 0)", "true")
    elif mutation == "target": problem["target"]["ast"] = ["Bot"]
    elif mutation == "source": problem["target"]["source"] = "0 = 1"
    elif mutation == "extra": problem["ha_checked"] = True
    elif mutation == "nested_extra": problem["target"]["certificate"] = "forged"
    else: problem["target"]["ast"][1][1][1] = False
    problem["export_sha256"] = external._hash(external.canonical({key: value for key, value in problem.items() if key != "export_sha256"}))
    with pytest.raises(external.ExportError): external.validate_problem(problem)


def test_public_validation_binds_independently_supplied_original_goal():
    problem = external.export_problem("forall n. n = n")
    with pytest.raises(external.ExportError): external.validate_export(problem, "0 = 1")


def test_fixed_argv_never_enables_multiprocess_portfolio_or_shell():
    for name in external.SOLVERS:
        args = external.solver_argv(name, "/fixed/solver", 2)
        assert type(args) is tuple and args[0] == "/fixed/solver"
        assert not any("schedule" in part or "portfolio" in part or "casc" in part for part in args)
    assert "--proof-object" in external.solver_argv("eprover", "/e", 2)
    assert "--proof" in external.solver_argv("vampire", "/v", 2)
    assert "-smt2" in external.solver_argv("z3", "/z", 2)


@pytest.mark.parametrize("value", [0, 1, 31, True, 2.5])
def test_aggregate_cpu_contract_rejects_invalid_limits(value):
    with pytest.raises(external.ExportError): external.ExternalBudget(cpu_seconds=value)


def test_shared_budget_reserves_hard_cpu_limit_and_rejects_overlap(monkeypatch):
    real = external._runtime()
    records = []
    class Runtime:
        ProcessLimits = real.ProcessLimits
        @staticmethod
        def run_bounded(command, **kwargs):
            records.append(kwargs)
            return {"resources": {"cpu_seconds": .01}}
        @staticmethod
        def validate_process_record(*args, **kwargs): pass
    monkeypatch.setattr(external, "_runtime", lambda: Runtime)
    budget = external.ExternalBudget(cpu_seconds=4)
    returned = budget._run(("/solver",), 1)
    returned["resources"]["cpu_seconds"] = 900
    assert budget.snapshot()["measured_child_cpu_seconds"] == .01
    assert budget._run(("/solver",), 1) is not None
    assert budget._run(("/solver",), 1) is None
    assert budget.snapshot()["cpu_hard_limit_reserved_seconds"] == 4
    assert all(r["limits"].rss_bytes == 512*1024**2 for r in records)
    external._WORKER_LOCK.acquire()
    try:
        with pytest.raises(external.ExportError): external.ExternalBudget()._run(("/solver",), 1)
    finally: external._WORKER_LOCK.release()


def test_unavailable_explicit_path_never_falls_back_to_PATH(monkeypatch, tmp_path):
    monkeypatch.setattr(external.shutil, "which", lambda _name: pytest.fail("unexpected fallback"))
    result = external.probe_solver("eprover", budget=external.ExternalBudget(), executable=tmp_path / "missing")
    assert result["status"] == "unavailable" and result["discovery"] == "explicit_path"


def test_expired_budget_does_not_launch(monkeypatch):
    budget = external.ExternalBudget()
    budget._deadline = 0
    monkeypatch.setattr(external, "_runtime", lambda: pytest.fail("expired launch"))
    assert budget._run(("/solver",), 1) is None


def test_solver_output_never_claims_HA_authority(monkeypatch):
    problem = external.export_problem("0=0")
    monkeypatch.setattr(external, "source_pins", lambda: {})
    monkeypatch.setattr(external, "probe_solver", lambda *args, **kwargs: {"status": "unavailable"})
    result = external.invoke_solver(problem, budget=external.ExternalBudget())
    assert result["ha_checked"] is result["proof_log_checked"] is result["ha_translation_verified"] is False
    assert result["IR_obligations_closed"] == result["solver_proofs_reconstructed"] == result["model_proof_search_calls"] == 0


@pytest.mark.parametrize("solver,text,status", [
    ("z3", "unsat\n(proof not-checked)", "unsat"),
    ("eprover", "# SZS status Theorem\n# SZS output start CNFRefutation\n", "Theorem"),
    ("vampire", "% SZS status Theorem for stdin\n% SZS output start Proof for stdin\n", "Theorem")])
def test_observation_is_only_proof_shaped_and_nonzero_exit_is_unknown(solver, text, status):
    process = {"reason": "exited", "returncode": 0, "output_truncated": False, "stdout": text}
    assert external._observation(process, solver) == {"solver_status": status, "proof_shaped_output_present": True}
    process["returncode"] = 1
    assert not external._observation(process, solver)["proof_shaped_output_present"]


def test_format_mismatch_rejected_before_any_probe(monkeypatch):
    monkeypatch.setattr(external, "probe_solver", lambda *args, **kwargs: pytest.fail("unexpected probe"))
    with pytest.raises(external.ExportError):
        external.invoke_solver(external.export_problem("0=0"), "vampire", budget=external.ExternalBudget())
