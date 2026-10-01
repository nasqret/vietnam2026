"""Source/AST tests plus explicit original-kernel adversaries. Root runs tests.

The module-scoped certificate fixture performs native proof work only for tests
requesting it. The tiny host-integer counterexamples are diagnostics, not proofs.
"""
import ast
from dataclasses import replace
from hashlib import sha256
import json
from math import factorial, prod
import sys

import pytest

import sqrt2_power_convolution_vanishing as cv
from sqrt2_power_definitions import parse_named
from sqrt2_power_native import closed_formula
from peano_lab.library import defined_syntax
from peano_lab.library.finite_sum_theorems import _sum_relation_terms
from peano_lab.library.proof_bundle import encode_formula


def _at(b, c, i, a, tag):
    modulus = f"S ((S ({i}))*({c}))"
    return (f"((exists h{tag}. h{tag}+S ({a})={modulus}) /\\ "
            f"(exists q{tag}. ({b})=q{tag}*{modulus}+({a})))")


def _lt(a, b, tag):
    return f"exists gap{tag}. gap{tag}+S ({a})=({b})"


def _pad(b, c, length, i, a, tag):
    return (f"(({_lt(i,length,tag)}) /\\ ({_at(b,c,i,a,tag)})) \\/ "
            f"((exists out{tag}. out{tag}+({length})=({i})) /\\ ({a})=0)")


def _independent_expanded_source():
    # Independent textual expansion; no producer definition-builder is called.
    left = f"forall j a. ({_lt('j','r','L')}) -> ({_pad('ab','ac','L','j','a','L')}) -> a=0"
    right = f"forall j b. ({_lt('j','s','R')}) -> ({_pad('bb','bc','M','j','b','R')}) -> b=0"
    term = (f"exists h a b. j+h=i /\\ (({_pad('ab','ac','L','j','a','A')}) /\\ "
            f"(({_pad('bb','bc','M','h','b','B')}) /\\ t=a*b))")
    diagonal = (f"forall j. ({_lt('j','S i','D')}) -> exists t. "
                f"({_at('db','dc','j','t','D')}) /\\ ({term})")
    summed = _sum_relation_terms("db", "dc", "S i", "n", tag="independentcv")
    return (f"forall ab ac L bb bc M r s i db dc n. ({left}) -> ({right}) -> "
            f"({_lt('i','r+s','G')}) -> ({diagonal}) -> ({summed}) -> n=0")


def test_original_target_matches_independent_expansion_and_literal_pins():
    assert cv.frozen_convolution_vanishing_target() == closed_formula(_independent_expanded_source())
    assert sha256(cv.SOURCE.encode()).hexdigest() == cv.SOURCE_SHA256
    assert cv.formula_sha256(cv.frozen_convolution_vanishing_target()) == cv.TARGET_SHA256
    assert cv.CONVOLUTION_VANISHING_NAMED_SOURCE == cv.SOURCE


def test_definition_identity_argument_order_and_global_registry_are_preserved():
    before = dict(defined_syntax.DEFINITIONS_BY_NAME)
    definitions = cv.convolution_definitions()
    assert len(definitions) == 8
    for name, identifier, parameters, digest in cv.DEFINITION_PINS:
        definition = definitions[name]
        assert (definition.stable_id, definition.parameters, definition.arity) == (
            identifier, parameters, len(parameters))
        assert cv.formula_sha256(definition.template_formula) == digest
    for name in ("Le", "Lt", "BetaAt", "Sum", "Repeat"):
        assert definitions[name] is before[name]
    assert dict(defined_syntax.DEFINITIONS_BY_NAME) == before
    with pytest.raises(TypeError):
        definitions["Invented"] = object()


def test_named_calls_reject_unknown_names_wrong_arities_and_free_variables():
    definitions = cv.convolution_definitions()
    for source in ("Unknown(0)", "Sum(0,1,0)", "BetaZeroExtend(0,1,0,0)",
                   "PolynomialDiagonalPrefix(0,1,0,0,1,0,0,0,1)", "Sum(b,1,0,0)"):
        with pytest.raises(ValueError):
            parse_named(source, registry=definitions)


def test_compound_arguments_and_existing_binders_are_capture_safe():
    definitions = cv.convolution_definitions()
    names = ("j", "a", "b", "c", "gap")
    actual = parse_named("BetaZeroExtend(b,c,S j,gap,a)", names, definitions)
    from peano_lab.kernel.formulas import parse_formula_in_context
    expected = parse_formula_in_context(_pad("b", "c", "S j", "gap", "a", "fresh"), list(names))
    assert actual == expected


def test_beta_entry_value_transport_requires_two_single_occurrence_rewrites():
    from peano_lab.engine.rewrite import rewrite_formula
    definitions = cv.convolution_definitions()
    names = ("db", "dc", "j", "x")
    original = parse_named("BetaAt(db,dc,j,x)", names, definitions)
    equality = parse_named("x=0", names, definitions)
    expected = parse_named("BetaAt(db,dc,j,0)", names, definitions)
    first, _ = rewrite_formula(original, equality)
    second, _ = rewrite_formula(first, equality)
    assert first != expected
    assert second == expected
    commands = cv._script(definitions)
    index = commands.index("rewrite heq at ht_witness_left")
    assert commands[index:index + 3] == (
        "rewrite heq at ht_witness_left", "rewrite heq at ht_witness_left", "exact ht_witness_left")


def test_strict_vanishing_order_guard_is_not_weakened_or_reversed():
    definitions = cv.convolution_definitions()
    target = cv.frozen_convolution_vanishing_target()
    for source in (cv.SOURCE.replace("Lt(i,r+s)", "Le(i,r+s)"),
                   cv.SOURCE.replace("Lt(i,r+s)", "Lt(r+s,i)"),
                   cv.SOURCE.replace("S i,n", "i,n"),
                   cv.SOURCE.replace("n=0", "n=1")):
        assert parse_named(source, registry=definitions) != target


def test_raw_ancestor_cone_is_exact_small_and_not_a_proof_receipt(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("source inspection may not decode/check a proof")
    for name in ("decode_proof", "check_encoded_proof_bundle", "prove_convolution_vanishing"):
        monkeypatch.setattr(cv, name, forbidden)
    before = "peano_lab.library.theorems" in sys.modules
    data = cv.convolution_cone_data()
    assert ("peano_lab.library.theorems" in sys.modules) == before
    assert tuple(data["original_ids"]) == cv.ANCESTOR_IDS
    assert len(data["rows"]) == 27
    assert data["original_body_nodes"] == 1146
    assert data["original_max_body_depth"] == 52
    assert data["original_rows_bytes"] == len(cv._canonical(data["rows"])) == 40072
    assert data["original_dependency_edges"] == sum(len(row[2]) for row in data["rows"]) == 40
    assert sha256(cv._canonical(data["rows"])).hexdigest() == cv.ANCESTOR_ROWS_SHA256
    assert data["authority"] == "authenticated_ordinary_bytes_not_kernel_acceptance"
    table = dict(zip(data["original_ids"], data["rows"], strict=True))
    reached, pending = set(), [position for _, position, _ in cv.ROOT_PINS]
    while pending:
        node = pending.pop()
        if node not in reached:
            reached.add(node)
            pending.extend(table[node][2])
    assert reached == set(table)
    for name, position, digest in cv.ROOT_PINS:
        source = data["root_sources"][name]
        assert sha256(repr(source).encode()).hexdigest() == digest
        assert table[position][1] == encode_formula(closed_formula(source[1]))


def test_changed_original_artifact_is_rejected_before_metadata_use(tmp_path):
    original = cv.ARTIFACT.read_bytes()
    changed = tmp_path / "changed.json"
    changed.write_bytes(original.replace(b'"eq"', b'"or"', 1))
    with pytest.raises(cv.ConvolutionVanishingError, match="bytes changed"):
        cv.convolution_cone_data(changed)


def test_truncated_or_symlink_artifact_is_not_accepted(tmp_path):
    short = tmp_path / "short.json"
    short.write_bytes(b"[]")
    with pytest.raises(cv.ConvolutionVanishingError, match="size"):
        cv.convolution_cone_data(short)
    link = tmp_path / "link.json"
    link.symlink_to(cv.ARTIFACT)
    with pytest.raises(cv.ConvolutionVanishingError, match="nonsymlink"):
        cv.convolution_cone_data(link)


def test_false_named_source_and_ast_pin_fail_closed(monkeypatch):
    monkeypatch.setattr(cv, "SOURCE", cv.SOURCE.replace("n=0", "n=1"))
    with pytest.raises(cv.ConvolutionVanishingError, match="source changed"):
        cv.frozen_convolution_vanishing_target()
    monkeypatch.setattr(cv, "SOURCE", cv.CONVOLUTION_VANISHING_NAMED_SOURCE)
    monkeypatch.setattr(cv, "TARGET_SHA256", "0" * 64)
    with pytest.raises(cv.ConvolutionVanishingError, match="target changed"):
        cv.frozen_convolution_vanishing_target()


def test_changed_named_root_mapping_is_rejected(monkeypatch):
    first, *tail = cv.ROOT_PINS
    monkeypatch.setattr(cv, "ROOT_PINS", ((first[0], first[1] + 1, first[2]), *tail))
    with pytest.raises(cv.ConvolutionVanishingError, match="exact source target"):
        cv.convolution_cone_data()


def test_manifest_and_script_are_source_only_and_make_no_parent_claim(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("manifest cannot create or check proof objects")
    monkeypatch.setattr(cv, "decode_proof", forbidden)
    monkeypatch.setattr(cv, "check_encoded_proof_bundle", forbidden)
    manifest = cv.convolution_vanishing_manifest()
    assert manifest["statement_ast_sha256"] == cv.TARGET_SHA256
    assert manifest["library_admissions"] == manifest["IR_parents_closed"] == 0
    for name in ("closes_IR079", "closes_IR080", "ordinary_HA_checked", "independent_lean_checked",
                 "rational_convolution_claim", "power_table_graph_claim"):
        assert manifest[name] is False
    assert manifest["native_budget_fit"] is None
    assert manifest["limits"] == vars(cv.BinaryDAGLimits())
    commands = cv._script(cv.convolution_definitions())
    assert 80 < len(commands) < 180
    assert "have heq : x=0" in commands
    assert "apply beta_repeat_sum_exact" in commands
    assert not any("FpConvolution" in command or "power_table" in command for command in commands)


def test_smaller_budget_rejection_occurs_before_proof_construction(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("budget rejection must precede source and proof work")
    monkeypatch.setattr(cv, "convolution_source_pins", forbidden)
    with pytest.raises(cv.ConvolutionVanishingError, match="unchanged"):
        cv.prove_convolution_vanishing(limits=object())
    for limits in (cv.BinaryDAGLimits(max_nodes=27), cv.BinaryDAGLimits(max_depth=51),
                   cv.BinaryDAGLimits(max_total_body_nodes=1146)):
        with pytest.raises(cv.ConvolutionVanishingError, match="ancestor cone"):
            cv.prove_convolution_vanishing(limits=limits)


def test_no_full_registry_import_external_reference_or_clock_bypass():
    source = cv.Path(cv.__file__).read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module != "peano_lab.library.theorems"
        if isinstance(node, ast.Import):
            assert all(alias.name != "peano_lab.library.theorems" for alias in node.names)
        if isinstance(node, ast.keyword):
            assert node.arg != "clock"
    assert "check_encoded_proof_bundle(payload" in source
    assert "decode_proof(row[3]" in source
    assert "library_admissions=0" in source


def test_source_pin_records_have_exact_wave_schema_and_byte_bindings():
    pins = cv.convolution_source_pins()
    assert pins
    for path, record in pins.items():
        assert type(record) is dict and set(record) == {"bytes", "sha256"}
        assert type(record["bytes"]) is int and 0 < record["bytes"] <= 2 * 1024**2
        assert type(record["sha256"]) is str and len(record["sha256"]) == 64
        raw = (cv.ROOT / path).read_bytes()
        assert record == {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    artifact = str(cv.ARTIFACT.relative_to(cv.ROOT))
    assert pins[artifact] == {"bytes": cv.ARTIFACT_BYTES, "sha256": cv.ARTIFACT_SHA256}


@pytest.fixture(scope="module")
def convolution_certificate():
    """Native execution is reserved for the root's supervised test process."""
    return cv.prove_convolution_vanishing()


def _curried(bundle, node):
    from peano_lab.kernel.formulas import Imp
    target = node.target
    for dependency in reversed(node.dependencies):
        target = Imp(bundle.nodes[dependency].target, target)
    return target


def _omit_zero_prefix(index):
    from peano_lab.kernel.formulas import Forall, Imp
    assert index in (0, 1)
    target = cv.frozen_convolution_vanishing_target()
    for _ in range(12):
        assert type(target) is Forall
        target = target.body
    premises = []
    for _ in range(5):
        assert type(target) is Imp
        premises.append(target.left)
        target = target.right
    for position in reversed(range(5)):
        if position != index:
            target = Imp(premises[position], target)
    for _ in range(12):
        target = Forall(target)
    return target


def _small_beta_prefix(values):
    """Independent host CRT model encoding, never a native theorem premise."""
    assert 1 <= len(values) <= 4 and all(type(a) is int and 0 <= a <= 1 for a in values)
    scale = factorial(len(values)) * (max(values) + 1)
    moduli = tuple(1 + (i + 1) * scale for i in range(len(values)))
    modulus = prod(moduli)
    code = sum(a * (modulus // m) * pow(modulus // m, -1, m)
               for a, m in zip(values, moduli, strict=True)) % modulus
    assert tuple(code % m for m in moduli) == tuple(values)
    return code, scale


def _counterexample_model(left, right, r, s, i):
    """Check actual beta entries/zero extension and an actual additive trace."""
    ab, ac = _small_beta_prefix(left)
    bb, bc = _small_beta_prefix(right)
    def entry(b, c, index):
        return b % (1 + (index + 1) * c)
    def pad(b, c, length, index):
        return entry(b, c, index) if index < length else 0
    summands = tuple(pad(ab, ac, len(left), j) * pad(bb, bc, len(right), i - j)
                     for j in range(i + 1))
    db, dc = _small_beta_prefix(summands)
    partials = [0]
    for value in summands:
        partials.append(partials[-1] + value)
    tb, tc = _small_beta_prefix(partials)
    assert entry(tb, tc, 0) == 0
    assert all(entry(db, dc, j) == summands[j]
               and entry(tb, tc, j + 1) == entry(tb, tc, j) + entry(db, dc, j)
               for j in range(i + 1))
    n = entry(tb, tc, i + 1)
    return dict(left_zero=all(pad(ab, ac, len(left), j) == 0 for j in range(r)),
        right_zero=all(pad(bb, bc, len(right), j) == 0 for j in range(s)),
        strict_guard=i < r + s, weak_guard=i <= r + s, sum=n,
        beta_codes=(ab, ac, bb, bc, db, dc, tb, tc),
        actual_diagonal=True, actual_sum_trace=True, conclusion=n == 0)


def test_le_boundary_instead_of_lt_has_actual_beta_trace_counterexample():
    model = _counterexample_model((0, 1), (0, 1), 1, 1, 2)
    assert model["left_zero"] and model["right_zero"] and model["weak_guard"]
    assert model["actual_diagonal"] and model["actual_sum_trace"]
    assert not model["strict_guard"] and not model["conclusion"] and model["sum"] == 1


@pytest.mark.parametrize("omitted,r,s", ((0, 1, 0), (1, 0, 1)))
def test_missing_zero_prefix_has_actual_beta_trace_counterexample(omitted, r, s):
    model = _counterexample_model((1,), (1,), r, s, 0)
    assert model["strict_guard"] and model["actual_diagonal"] and model["actual_sum_trace"]
    flags = (model["left_zero"], model["right_zero"])
    assert not flags[omitted] and flags[1 - omitted]
    assert not model["conclusion"] and model["sum"] == 1
    assert _omit_zero_prefix(omitted) != cv.frozen_convolution_vanishing_target()


def test_actual_28_ordinary_bodies_and_fresh_canonical_replay(convolution_certificate):
    from peano_lab.library.proof_bundle import check_encoded_proof_bundle, encode_proof
    result = convolution_certificate
    assert result.target == result.receipt.target == cv.frozen_convolution_vanishing_target()
    assert result.target_ast_sha256 == cv.TARGET_SHA256
    assert len(result.bundle.nodes) == result.receipt.kernel_calls == 28
    assert result.bundle.root == 27
    remap = {old: new for new, old in enumerate(cv.ANCESTOR_IDS)}
    assert result.bundle.nodes[27].dependencies == tuple(remap[i] for _, i, _ in cv.ROOT_PINS)
    assert result.receipt.total_body_nodes <= 200000 and result.max_proof_depth <= 256
    assert len(result.payload.encode()) <= 8 * 1024**2
    data = cv.convolution_cone_data()
    for node, original in zip(result.bundle.nodes[:27], data["rows"], strict=True):
        assert encode_proof(node.body) == original[3]
        assert node.fuel == original[0]
        assert node.dependencies == tuple(remap[i] for i in original[2])
    fresh = check_encoded_proof_bundle(result.payload, limits=cv.BinaryDAGLimits().bundle_limits())
    assert fresh.target == result.target and fresh.kernel_calls == 28
    assert result.provenance["IR_parents_closed"] == result.provenance["library_admissions"] == 0
    assert result.provenance["independent_lean_checked"] is False


def test_original_kernel_rejects_wrong_le_boundary(convolution_certificate):
    from peano_lab.kernel.checker import check
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    bundle = convolution_certificate.bundle
    root = bundle.nodes[bundle.root]
    changed = parse_named(cv.SOURCE.replace("Lt(i,r+s)", "Le(i,r+s)"),
                          registry=cv.convolution_definitions())
    assert not check((), root.body, _curried(bundle, replace(root, target=changed)))
    with pytest.raises(ProofBundleError, match="exact caller target"):
        check_proof_bundle(bundle, changed, limits=cv.BinaryDAGLimits().bundle_limits())


@pytest.mark.parametrize("omitted", (0, 1))
def test_original_kernel_rejects_missing_zero_prefix(convolution_certificate, omitted):
    from peano_lab.kernel.checker import check
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    bundle = convolution_certificate.bundle
    root = bundle.nodes[bundle.root]
    changed = _omit_zero_prefix(omitted)
    assert not check((), root.body, _curried(bundle, replace(root, target=changed)))
    with pytest.raises(ProofBundleError, match="exact caller target"):
        check_proof_bundle(bundle, changed, limits=cv.BinaryDAGLimits().bundle_limits())


def test_original_kernel_rejects_missing_dependency_and_forged_body(convolution_certificate):
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import ProofBundleError, check_proof_bundle
    bundle = convolution_certificate.bundle
    root = bundle.nodes[bundle.root]
    missing = replace(root, dependencies=root.dependencies[:-1])
    assert not check((), root.body, _curried(bundle, missing))
    assert not check((), EqRefl(Zero()), _curried(bundle, root))
    forged_root = replace(root, body=EqRefl(Zero()))
    with pytest.raises(ProofBundleError, match="kernel rejected"):
        check_proof_bundle(replace(bundle, nodes=(*bundle.nodes[:-1], forged_root)),
                           convolution_certificate.target, limits=cv.BinaryDAGLimits().bundle_limits())
    forged_ancestor = replace(bundle.nodes[0], body=EqRefl(Zero()))
    with pytest.raises(ProofBundleError, match="kernel rejected"):
        check_proof_bundle(replace(bundle, nodes=(forged_ancestor, *bundle.nodes[1:])),
                           convolution_certificate.target, limits=cv.BinaryDAGLimits().bundle_limits())


@pytest.fixture(scope="module")
def convolution_annotation_variants():
    """Recreate observed v2 annotation loss without changing its statement/script."""
    from peano_lab.engine.state import final_certificate, start
    from peano_lab.engine.tactics import apply_tactic
    from peano_lab.engine.proof_reduction import compile_local_cuts
    from peano_lab.kernel.formulas import Imp
    data = cv.convolution_cone_data()
    curried = cv.frozen_convolution_vanishing_target()
    for name, _, _ in reversed(cv.ROOT_PINS):
        curried = Imp(closed_formula(data["root_sources"][name][1]), curried)
    state = start(curried)
    commands = tuple("intro " + name for name, _, _ in cv.ROOT_PINS) + cv._script(cv.convolution_definitions())
    for command in commands:
        tactic, _, argument = command.partition(" ")
        state = apply_tactic(state, tactic, argument)
    assert not state.goals and state.target == curried
    raw = final_certificate(state)
    assert raw is not None
    annotated, count = cv._preserve_local_lemma_synthesis(raw)
    assert count == cv.EXPECTED_LOCAL_LEMMAS == 11
    original, compiled = compile_local_cuts(raw), compile_local_cuts(annotated)
    for proof in (raw, annotated, original, compiled):
        cv._body_metrics(proof, cv.BinaryDAGLimits())
        cv._row_preflight(curried, proof, cv.BinaryDAGLimits())
    return curried, raw, annotated, original, compiled


def test_observed_unannotated_rejection_and_typed_local_lemma_acceptance(convolution_annotation_variants):
    from peano_lab.kernel.checker import check
    curried, _, _, original, compiled = convolution_annotation_variants
    assert not check((), original, curried)
    assert check((), compiled, curried)


def test_local_annotations_preserve_every_proposition_and_actual_lemma(convolution_annotation_variants):
    from dataclasses import fields
    from peano_lab.engine.proof_reduction import LocalHave
    from peano_lab.kernel.proofs import Cut, Hyp, Proof
    _, raw, annotated, _, _ = convolution_annotation_variants
    pending, count = [(raw, annotated)], 0
    while pending:
        original, transformed = pending.pop()
        assert type(original) is type(transformed)
        for field in fields(original):
            old, new = getattr(original, field.name), getattr(transformed, field.name)
            if type(original) is LocalHave and field.name == "proof":
                assert type(new) is Cut
                assert new.proposition == new.conclusion == original.proposition
                assert type(new.body) is Hyp and new.body.index == 0
                pending.append((old, new.lemma))
                count += 1
            elif isinstance(old, Proof):
                pending.append((old, new))
            else:
                assert old == new
    assert count == 11


def test_original_kernel_rejects_forged_annotation_lemma(convolution_annotation_variants):
    from dataclasses import fields
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.proofs import Cut, EqRefl, Hyp, Proof
    from peano_lab.kernel.terms import Zero
    curried, _, _, _, compiled = convolution_annotation_variants
    changed = False
    def forge(proof):
        nonlocal changed
        if (not changed and type(proof) is Cut and proof.proposition == proof.conclusion
                and type(proof.body) is Hyp and proof.body.index == 0):
            changed = True
            return replace(proof, lemma=EqRefl(Zero()))
        updates = {}
        for field in fields(proof):
            child = getattr(proof, field.name)
            if isinstance(child, Proof) and not changed:
                updates[field.name] = forge(child)
        return replace(proof, **updates) if updates else proof
    forged = forge(compiled)
    assert changed
    assert not check((), forged, curried)
