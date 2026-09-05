"""Reading aids preserve exact proof bytes and never manufacture evidence."""
from __future__ import annotations

from hashlib import sha256
from html import escape
import json
from pathlib import Path

import pytest

from proof_readability import (
    ReadabilityError, audit_page, checkpoints, enhance_page, parse_page,
    safe_href, strip_reading_layer,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture(commands=("intro n", "have h : n = n", "refl", "exact h"), *, defined=False):
    prefix = "pd" if defined else "pa"
    lines = ''.join(f'<li class="{prefix}-proof-line" id="L{i}" data-line="{i}">'
                    f'<code>{escape(command)}</code></li>' for i, command in enumerate(commands, 1))
    return ('<!doctype html><html><head><title>Proof</title></head><body><h1>example</h1>'
            '<main><pre id="statement"><code>forall n. n = n</code></pre>'
            f'<ol class="{prefix}-formal-proof">{lines}</ol></main></body></html>').encode()


@pytest.mark.parametrize("defined", [False, True])
def test_exact_recovery_retains_original_scripts_statements_anchors_and_assets(defined):
    raw = fixture(defined=defined)
    paired = dict(exact_raw=fixture(), exact_href="../../tag/T.html") if defined else {}
    revised, report = enhance_page(raw, assets_prefix="../../assets/", revision="0123456789ab", **paired)
    assert strip_reading_layer(revised) == raw
    assert b'data-proof-reader' in revised and b'data-reader-exact' in revised
    assert report["line_count"] == 4 and report["local_claim_count"] == 1
    assert report["new_proof_authority"] is False
    assert report["curated_mathematical_explanation"] is False
    assert revised.count(b'id="L2"') == 1


def test_older_defined_notation_is_bound_to_native_source_not_mislabeled():
    exact = fixture(("intro n", "have h : exists k. n = k", "exists n", "refl", "exact h"))
    defined = fixture(("intro n", "have h : ∃ k. n = k", "exists n", "refl", "exact h"), defined=True)
    native = parse_page(exact.decode())
    note = dict(theorem="example", script_sha256=native.script_sha256,
                title="Construct the witness", paragraphs=["The witness is n."], claims={})
    revised, report = enhance_page(defined, assets_prefix="../../assets/", revision="0123456789ab",
        exact_raw=exact, exact_href="../../tag/T.html", notes={"notes": [note]})
    assert report["script_sha256"] == native.script_sha256
    assert report["script_source"] == "paired-exact-edition"
    assert report["exact_page_sha256"] == sha256(exact).hexdigest()
    assert report["paired_notation_rows"] == 1 and report["curated_mathematical_explanation"]
    assert b'Original defined command ledger' in revised
    assert b'Original exact command ledger' not in revised
    assert b'href="../../tag/T.html#L2"' in revised
    assert strip_reading_layer(revised) == defined


@pytest.mark.parametrize("fault", ["missing", "theorem", "length", "name", "tactic", "argument", "expansion", "unsafe-link"])
def test_invalid_exact_defined_pair_is_rejected(fault):
    exact, defined = fixture(), fixture(defined=True)
    href = "../../tag/T.html"
    if fault == "missing":
        exact = None
    elif fault == "theorem":
        exact = exact.replace(b'<h1>example</h1>', b'<h1>other</h1>')
    elif fault == "length":
        exact = fixture(("intro n",))
    elif fault == "name":
        defined = defined.replace(b'have h :', b'have another :')
    elif fault == "tactic":
        defined = defined.replace(b'have h :', b'suffices h :')
    elif fault == "argument":
        defined = defined.replace(b'exact h', b'exact another')
    elif fault == "expansion":
        defined = defined.replace(b'<code>have h : n = n</code>',
            b'<code>have h : Reflexive(n)</code><details class="pd-exact-line"><code>have h : n = 0</code></details>')
    else:
        href = "javascript:alert(1)"
    with pytest.raises(ReadabilityError):
        enhance_page(defined, assets_prefix="../../assets/", revision="0123456789ab", exact_raw=exact, exact_href=href)


def test_long_claim_is_disclosed_without_changing_or_truncating_its_formula():
    command = "have h : " + "(0 = 0 /\\ " * 100 + "0 = 0" + ")" * 100
    raw = fixture((command, "refl"))
    revised, report = enhance_page(raw, assets_prefix="../../assets/", revision="0123456789ab")
    assert b'class="pr-long-claim"' in revised
    assert escape(command).encode() in revised
    assert report["large_display_claims"] == 1
    assert strip_reading_layer(revised) == raw


def test_curated_mathematics_is_bound_to_the_entire_exact_script():
    raw = fixture()
    page = parse_page(raw.decode())
    note = dict(theorem="example", script_sha256=page.script_sha256,
                title="Mathematical reason", paragraphs=["Motivation, not proof authority."], claims={})
    revised, report = enhance_page(raw, assets_prefix="../assets/", revision="0123456789ab", notes={"notes": [note]})
    assert b'Mathematical reason' in revised and report["curated_mathematical_explanation"]
    changed = fixture(("intro m", "have h : m = m", "refl", "exact h"))
    revised, report = enhance_page(changed, assets_prefix="../assets/", revision="0123456789ab", notes={"notes": [note]})
    assert b'Mathematical reason' not in revised and not report["curated_mathematical_explanation"]


def test_curated_prose_and_commands_are_escaped():
    raw = fixture(("intro n",))
    page = parse_page(raw.decode())
    note = dict(theorem="example", script_sha256=page.script_sha256,
                title='<script>alert("bad")</script>', paragraphs=['<img src=x onerror=bad>'], claims={})
    revised, _ = enhance_page(raw, assets_prefix="../assets/", revision="0123456789ab", notes={"notes": [note]})
    assert b'<img' not in revised and b'<script>alert' not in revised
    assert b'&lt;img' in revised


@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,test", "//evil.test/x", "a\\b", "x\ny"])
def test_link_protocols_are_not_executable(url):
    assert not safe_href(url)


@pytest.mark.parametrize("mutation", [
    lambda raw: raw.replace(b'data-line="2"', b'data-line="5"'),
    lambda raw: raw.replace(b'id="L2"', b'id="L1"'),
    lambda raw: raw.replace(b'<h1>example</h1>', b'<h1>two ambiguous names</h1>'),
    lambda raw: raw.replace(b'</head>', b'</head></head>'),
    lambda raw: raw.replace(b'</code></li>', b'</code><code>forged</code></li>', 1),
])
def test_malformed_source_fails_closed(mutation):
    with pytest.raises(ReadabilityError):
        enhance_page(mutation(fixture()), assets_prefix="../assets/", revision="0123456789ab")


def test_no_inferred_proof_tree_or_new_axiom_is_advertised():
    revised, _ = enhance_page(fixture(), assets_prefix="../assets/", revision="0123456789ab")
    assert b'not inferred branch boundaries' in revised
    assert b'not a new proof' in revised
    page = parse_page(fixture().decode())
    assert [line.number for group in checkpoints(page.lines) for line in group] == [1, 2, 3, 4]


def test_current_two_square_and_descent_pilots_match_their_curated_notes():
    stage = ROOT / "_deploy/proofs-public-v1"
    if not stage.exists():
        pytest.skip("preserved public stage is not available")
    notes = json.loads((ROOT / "deploy/proofs/proof-reader-notes.json").read_text())
    targets = [stage / "two-squares/explorer/defined/tag/TS003F.html",
               stage / "quadratic-reciprocity/explorer/defined/tag/PA00A7.html"]
    for target in targets:
        raw = target.read_bytes()
        exact = Path(str(target).replace('/explorer/defined/tag/', '/explorer/tag/')).read_bytes()
        revised, report = enhance_page(raw, assets_prefix="../../../../assets/", revision="0123456789ab", notes=notes,
            exact_raw=exact, exact_href="../../tag/" + target.name)
        assert report["curated_mathematical_explanation"]
        assert strip_reading_layer(revised) == raw
    page = parse_page(targets[0].read_text())
    report = audit_page(page)
    assert report["max_exact_claim_characters"] == 21622
    assert report["max_defined_claim_characters"] == 231


def test_non_theorem_pages_remain_byte_identical():
    raw = b'<html><head></head><body><h1>Library</h1></body></html>'
    assert enhance_page(raw, assets_prefix="assets/", revision="0123456789ab") == (raw, None)


def test_apply_policy_twice_is_rejected_not_duplicated():
    revised, _ = enhance_page(fixture(), assets_prefix="../assets/", revision="0123456789ab")
    with pytest.raises(ReadabilityError):
        enhance_page(revised, assets_prefix="../assets/", revision="0123456789ab")


@pytest.mark.parametrize("family,theorem,expected", [
    ("two-squares", "two_square_iff_zero_or_even_three_mod_four_prime_valuations", "have hiff :="),
    ("binary-digit-extraction", "binary_modular_execution_logarithmic_bound", "have hfull := binary_modular_exponent_coded_execution_exists n a m hmodulus"),
    ("euclidean-logarithmic-bound", "euclidean_log_budget_extend_twice", "have hcopy := euclidean_log_budget_extend"),
])
def test_real_long_claim_pilots_replay_and_shorten_without_source_rewriting(family, theorem, expected):
    # Source-reconstruction regression, not a fresh textual Lean compilation or
    # a replacement for the preserved release's independent proof admission.
    from peano_lab.kernel.formulas import parse_formula
    from peano_lab.library.lean_proof_reconstruction import reconstruct_theorem
    from peano_lab.library.theorems import TheoremSpec
    path = ROOT / "_deploy/proofs-public-v1" / family / "api/corpus.json"
    if not path.exists():
        pytest.skip("preserved public corpus is not available")
    raw = path.read_bytes()
    rows = {row["name"]: row for row in json.loads(raw)["nodes"]}
    row = rows[theorem]
    spec = TheoremSpec(theorem, row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row["summary"])
    references = {name: name for name in spec.dependencies}
    formulas = {name: parse_formula(rows[name]["statement"]) for name in spec.dependencies if name in rows}
    before = reconstruct_theorem(spec, dependency_references=references, dependency_formulas=formulas, infer_simple_claims=False)
    after = reconstruct_theorem(spec, dependency_references=references, dependency_formulas=formulas)
    assert before.status == after.status == "translated"
    assert after.inferred_claims == 2 and after.translated_steps == len(spec.script)
    assert expected in after.lean_body and len(after.lean_body.encode()) < len(before.lean_body.encode()) // 2
    assert path.read_bytes() == raw
