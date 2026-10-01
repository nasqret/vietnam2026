"""Reader/adversarial tests only; no solver launch or native proof generation."""
from copy import deepcopy
from hashlib import sha256
import re

import pytest

import sqrt2_power_solver_hints as hints
from sqrt2_power_external import ExportError, export_problem, canonical as external_json


@pytest.fixture(params=("eprover", "vampire"))
def archived(request):
    return hints.archived_p08(request.param)


def _changed_log(observed, change):
    result = deepcopy(observed)
    process = result["process"]
    process["stdout"] = change(process["stdout"])
    raw = process["stdout"].encode()
    process["stdout_bytes"] = len(raw)
    process["stdout_sha256"] = sha256(raw).hexdigest()
    return result


def _proof_body(text):
    start = re.search(r"^[%#]\s*SZS output start (?:Proof|CNFRefutation)\b[^\n]*\n", text, re.M)
    end = re.search(r"^[%#]\s*SZS output end (?:Proof|CNFRefutation)\b", text, re.M)
    return text[start.end():end.start()]


def _changed_original_formula(text, change):
    records = hints._records(_proof_body(text))
    formula = next(formula for _, _, formula, source in records if source.startswith("file"))
    changed = change(formula)
    assert changed != formula
    return text.replace(formula, changed, 1)


def _capture_first_binder(formula):
    binders = list(re.finditer(r"!\s*\[\s*([A-Z][A-Za-z0-9_]*)\s*\]", formula))
    assert len(binders) >= 2
    first, second = binders[:2]
    return formula[:first.start(1)] + second[1] + formula[first.end(1):]


def test_archived_proofs_select_only_two_original_native_laws(archived):
    problem, observed, contract = archived
    result = hints.extract_premise_hint(problem, observed, contract)
    assert result["selected_premises"] == ["mul_assoc", "mul_comm"]
    assert result["original_premises_offered"] == 15
    assert result["statement_ast_sha256"] == hints.P08_AST_SHA256
    assert result["contract_sha256"] == hints.P08_CONTRACT_SHA256
    assert result["external_target_ast_sha256"] == problem["target"]["ast_sha256"]
    assert result["input_sha256"] == problem["input_sha256"]
    assert result["log_sha256"] == observed["process"]["stdout_sha256"]
    assert result["requires_fresh_HA_replay"] is True
    assert result["ha_checked"] is False
    for key in ("solver_proof_logs_translated", "derived_formulas_imported",
                "classical_or_skolem_steps_imported", "IR_parents_closed",
                "model_proof_search_calls", "library_admissions"):
        assert result[key] == 0


def test_hint_reader_does_not_regenerate_or_check_native_proofs(archived, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("proof-generation call in a read-only hint extraction")
    monkeypatch.setattr(hints.Basis, "get", forbidden)
    monkeypatch.setattr(hints, "check", forbidden)
    hints.extract_premise_hint(*archived)


def test_changed_frozen_contract_is_rejected(archived):
    problem, observed, contract = archived
    contract = deepcopy(contract)
    contract["source"] = "forall d u v m. d*v=u -> d*(m*v)=u*m"
    with pytest.raises(hints.HintError, match="changed frozen"):
        hints.extract_premise_hint(problem, observed, contract)


def test_extra_contract_fields_are_not_trusted(archived):
    problem, observed, contract = archived
    with pytest.raises(hints.HintError, match="changed frozen"):
        hints.extract_premise_hint(problem, observed, dict(contract, authorized=True))


def test_changed_original_target_is_rejected_even_in_valid_export(archived):
    problem, observed, contract = archived
    changed = export_problem("forall d u v m. d*v=u -> d*(m*v)=u", format="tptp")
    with pytest.raises(hints.HintError, match="changed target"):
        hints.extract_premise_hint(changed, observed, contract)


def test_resealed_export_bytes_are_reconstructed_not_trusted(archived):
    problem, observed, contract = archived
    problem = deepcopy(problem)
    problem["input"] += "fof(extra,axiom,$false).\n"
    problem["input_bytes"] = len(problem["input"].encode())
    problem["input_sha256"] = sha256(problem["input"].encode()).hexdigest()
    del problem["export_sha256"]
    problem["export_sha256"] = sha256(external_json(problem)).hexdigest()
    with pytest.raises((hints.HintError, ExportError)):
        hints.extract_premise_hint(problem, observed, contract)


def test_unoffered_native_premise_name_is_rejected(archived):
    _, observed, contract = archived
    changed = export_problem(hints.P08_SOURCE, (("alien", "forall n. n=n"),), format="tptp")
    with pytest.raises(hints.HintError, match="unknown or changed original premise"):
        hints.extract_premise_hint(changed, observed, contract)


def test_changed_known_premise_statement_is_rejected(archived):
    _, observed, contract = archived
    changed = export_problem(hints.P08_SOURCE, (("mul_assoc", "forall n. n=n"),), format="tptp")
    with pytest.raises(hints.HintError, match="unknown or changed original premise"):
        hints.extract_premise_hint(changed, observed, contract)


def test_log_cannot_change_original_binder_scope(archived):
    problem, observed, contract = archived
    changed = _changed_log(observed, lambda text: _changed_original_formula(text, _capture_first_binder))
    with pytest.raises(hints.HintError, match="captured"):
        hints.extract_premise_hint(problem, changed, contract)


def test_log_cannot_import_an_unknown_original_symbol(archived):
    problem, observed, contract = archived
    changed = _changed_log(observed, lambda text: _changed_original_formula(
        text, lambda formula: formula.replace("mul(", "mystery(", 1)))
    with pytest.raises(hints.HintError, match="unknown original term"):
        hints.extract_premise_hint(problem, changed, contract)


def test_unknown_proof_rule_is_rejected_not_skipped(archived):
    problem, observed, contract = archived
    changed = _changed_log(observed, lambda text: re.sub(
        r"inference\([a-z_]+,", "inference(magic_oracle,", text, count=1))
    with pytest.raises(hints.HintError, match="unsupported solver proof rule"):
        hints.extract_premise_hint(problem, changed, contract)


def test_unknown_original_file_premise_is_rejected(archived):
    problem, observed, contract = archived
    changed = _changed_log(observed, lambda text: re.sub(
        r"file\('<stdin>',\s*'?p00[67]'?\)", "file('<stdin>',p999)", text, count=1))
    with pytest.raises(hints.HintError, match="unknown original premise"):
        hints.extract_premise_hint(problem, changed, contract)


def test_foreign_input_file_is_rejected(archived):
    problem, observed, contract = archived
    changed = _changed_log(observed, lambda text: text.replace("file('<stdin>'", "file('other.p'", 1))
    with pytest.raises(hints.HintError, match="foreign source file"):
        hints.extract_premise_hint(problem, changed, contract)


def test_unknown_dependency_reference_is_rejected(archived):
    problem, observed, contract = archived
    def change(text):
        records = hints._records(_proof_body(text))
        annotation = next(source for _, _, _, source in records if source.startswith("inference"))
        rule, attributes, _ = hints._application(annotation, "inference", 3)
        return text.replace(annotation, f"inference({rule},{attributes},[unknown_node])", 1)
    with pytest.raises(hints.HintError, match="unknown or forward dependency"):
        hints.extract_premise_hint(problem, _changed_log(observed, change), contract)


def test_theorem_marker_without_log_is_not_a_hint(archived):
    problem, observed, contract = archived
    changed = _changed_log(observed, lambda text: "% SZS status Theorem\n")
    with pytest.raises(hints.HintError, match="complete proof section"):
        hints.extract_premise_hint(problem, changed, contract)


def test_false_root_is_required_even_with_theorem_marker(archived):
    problem, observed, contract = archived
    changed = _changed_log(observed, lambda text: text.replace("$false", "(zero=zero)"))
    with pytest.raises(hints.HintError, match="refutation root"):
        hints.extract_premise_hint(problem, changed, contract)


def test_altered_log_hash_is_rejected_before_parsing(archived):
    problem, observed, contract = archived
    observed = deepcopy(observed)
    observed["process"]["stdout_sha256"] = "0" * 64
    with pytest.raises(hints.HintError, match="invalid bound process"):
        hints.extract_premise_hint(problem, observed, contract)


def test_changed_export_receipt_binding_is_rejected(archived):
    problem, observed, contract = archived
    with pytest.raises(hints.HintError, match="exact input"):
        hints.extract_premise_hint(problem, dict(observed, input_sha256="0" * 64), contract)


def test_receipt_cannot_self_promote_classical_output_to_ha(archived):
    problem, observed, contract = archived
    with pytest.raises(hints.HintError, match="authority"):
        hints.extract_premise_hint(problem, dict(observed, ha_checked=True), contract)


def test_insufficient_hint_does_not_fall_back_to_all_fifteen_laws(monkeypatch):
    monkeypatch.setattr(hints, "extract_premise_hint", lambda *args: {"selected_premises": ["mul_comm"]})
    def forbidden(*args, **kwargs):
        raise AssertionError("must reject before native proof generation")
    monkeypatch.setattr(hints, "Basis", forbidden)
    with pytest.raises(hints.HintError, match="do not support"):
        hints.reconstruct_p08(None, None, None)


@pytest.mark.parametrize("source", (
    "![X,X]:(nat(X)=>X=X)", "![X]:![X]:(X=X)",
    "![X]:(mul(X,Y)=X)", "![X]:(foreign(X)=X)",
    "![X]:(mul(X)=X)", "![X]:(mul(X,X,X)=X)",
    "![X]:(nat(X)=>X=X) trailing",
))
def test_original_formula_parser_rejects_capture_unknown_symbols_and_arity(source):
    with pytest.raises(hints.HintError):
        hints._InputFormula(source).parse()


def test_original_formula_parser_accepts_only_alpha_renaming_not_capture():
    first = hints._InputFormula("![X]:![Y]:(nat(X)=>(nat(Y)=>mul(X,Y)=mul(Y,X)))").parse()
    second = hints._InputFormula("![A]:![B]: (nat(A) => (nat(B) => mul(A,B)=mul(B,A)))").parse()
    assert first == second
    different = hints._InputFormula("![A]:![B]:(nat(A)=>(nat(B)=>mul(A,A)=mul(B,A)))").parse()
    assert first != different
