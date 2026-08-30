"""Pure delivery/QR checks on the actual pinned v31 hub, never proof authority.

No release capability, kernel result, Lean result or stored receipt is faked.
The positive input is the real immutable 80,289-byte HTML parent. Only the new
in-memory formatter is exercised; no staged or public tree is written.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import inspect
import json
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlsplit


_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest
import build_constructive_research_hub_v32 as hub


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "deploy/proofs/index.html"
PARENT_PIN = (80289, "7d82eafef7694aee35970a546a82542caa5045cbb79eb284fd5117ffcaae3992")
REVISION = "0123456789ab"  # Formatting data only; not a claimed catalog digest.
OLD_REVISION = "6c9ebfb3c37e"

# Independent literal inventory; do not obtain expected routes from the code
# being tested or from a synthetic release/capability.
OLD_SLUGS = (
    "quadratic-reciprocity", "bertrand-postulate", "euler-units", "prime-fields",
    "mobius-values", "signed-sums", "divisor-sums", "signed-weighted-sums",
    "prime-field-polynomials", "divisor-involutions", "mobius-divisor-cancellation",
    "rectangular-sums", "polynomial-products", "finite-support", "dirichlet-convolution",
    "dirichlet-fubini", "dirichlet-units", "mobius-inversion", "dirichlet-signed-units",
    "dirichlet-triangular", "dirichlet-inverses", "best-approximation", "totient-products",
    "squarefree-kernels", "exponent-lifting", "gaussian-factorization", "prime-valuation-support",
    "arithmetic-foundations", "prime-enumeration", "gaussian-integers", "eisenstein-integers",
    "integer-linear-algebra", "hensel-lifting", "generalized-crt", "multinomial-kummer",
    "prime-count-chebyshev", "cornacchia", "cauchy-davenport", "matrix-cofactor-expansion",
    "polynomial-taylor-hensel", "generalized-crt-compatibility", "matrix-determinant-minors",
    "polynomial-hensel", "generalized-crt-fold", "euclidean-logarithmic-bound",
    "binary-digit-extraction", "primes-three-mod-four", "supplementary-laws", "kummer",
    "two-squares", "four-squares", "lucas", "pythagorean-fermat-four", "polynomial-horner",
    "matrix-dot-product", "bertrand-prime-chains", "continued-fractions", "matrix-coded-products",
    "euclidean-complexity", "binary-modular-exponentiation", "binary-length",
    "euclidean-gcd-transport", "binary-modular-execution",
)
NEW_SLUGS = ("multiplicative-convolution", "polynomial-division-prerequisites")
EXPECTED_SLUGS = OLD_SLUGS[:2] + NEW_SLUGS + OLD_SLUGS[2:]


class _Page(HTMLParser):
    """Independent, permissive observation parser, not the product validator."""

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags, self.links, self.family_links, self.ids, self.text = [], [], [], [], []
        self.article = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        row = dict(attrs)
        self.tags.append((tag, row))
        if "id" in row:
            self.ids.append(row["id"])
        if tag == "article":
            assert self.article is None
            self.article = row
        if tag == "a":
            self.links.append(row["href"])
            if self.article is not None and "primary-action" in row.get("class", "").split():
                self.family_links.append((row["href"], self.article))

    def handle_endtag(self, tag):
        if tag == "article":
            self.article = None

    def handle_data(self, data):
        self.text.append(data)


def _raw_cards(source):
    result = {}
    for fragment in re.findall(r"<article\b.*?</article>", source, re.S):
        parsed = _Page(fragment)
        assert len(parsed.family_links) == 1
        slug = urlsplit(parsed.family_links[0][0]).path.rstrip("/")
        assert slug not in result
        result[slug] = fragment
    return result


@pytest.fixture(scope="module")
def parent_bytes():
    before = PARENT.read_bytes()
    assert (len(before), sha256(before).hexdigest()) == PARENT_PIN
    yield before
    assert PARENT.read_bytes() == before


@pytest.fixture(scope="module")
def output(parent_bytes):
    return hub.render_public_hub(parent_bytes, REVISION).decode("utf-8")


def test_actual_literal_parent_and_public_api_are_exact(parent_bytes):
    assert (hub.PARENT_HUB_BYTES, hub.PARENT_HUB_SHA256) == PARENT_PIN
    assert hub.PARENT_HUB_PATH == "deploy/proofs/index.html"
    assert hub.PARENT_REVISION == OLD_REVISION
    assert hub.MAX_HUB_BYTES == 262144
    assert tuple(inspect.signature(hub.render_public_hub).parameters) == ("parent", "revision")
    assert tuple(hub.PARENT_FAMILY_ROUTES) == OLD_SLUGS
    assert tuple(hub.NEW_FAMILIES) == tuple(zip(NEW_SLUGS, (90, 85)))
    assert tuple(hub.FAMILY_ROUTES) == EXPECTED_SLUGS
    assert (len(parent_bytes), sha256(parent_bytes).hexdigest()) == PARENT_PIN


def test_all_65_primary_routes_are_literal_ordered_unique_and_revised(output):
    actual = _Page(output).family_links
    assert tuple(href for href, _attrs in actual) == tuple(f"{slug}/?v={REVISION}" for slug in EXPECTED_SLUGS)
    assert len(actual) == len(set(href for href, _attrs in actual)) == 65
    assert len(OLD_SLUGS) == 63 and len(set(OLD_SLUGS)) == 63


# Independently allowed changes to current prose inside six historical cards.
_CARD_SCOPE_UPDATES = {
    "dirichlet-convolution": (
        "Full G009 still requires multiplicative-function closure.",
        "The separately admitted multiplicative-convolution family completes finite signed G009.",
    ),
    "dirichlet-fubini": (
        "Full G009 remains broader.",
        "Together with the separately admitted multiplicative-convolution family, the finite signed G009 contract is complete.",
    ),
    "dirichlet-units": (
        "The separate inverse family proves the general unit-at-one criterion; multiplicative-function closure remains open.",
        "The separate inverse family proves the general unit-at-one criterion; the new multiplicative-convolution family supplies the remaining finite signed G009 closure.",
    ),
    "mobius-inversion": (
        "Full G009 multiplicative closure and G091 prime-power fields remain open.",
        "Finite signed G009, including multiplicative closure, is now proved; general G091 prime-power fields remain open.",
    ),
    "dirichlet-signed-units": (
        "full G009 remains broader.",
        "the separately admitted multiplicative-convolution family completes finite signed G009.",
    ),
    "dirichlet-inverses": (
        "Multiplicative-function closure and full G009 remain open.",
        "Multiplicative closure on nonempty normalized prefixes is proved in its separate family, completing finite signed G009.",
    ),
}


@pytest.mark.parametrize("slug", OLD_SLUGS)
def test_each_real_historical_card_preserves_exact_math_and_first_admission(parent_bytes, output, slug):
    original = _raw_cards(parent_bytes.decode())[slug]
    actual = _raw_cards(output)[slug]
    expected = original.replace(OLD_REVISION, REVISION)
    expected = expected.replace("Alpha v31 checked use", "Alpha v32 checked use")
    if slug in _CARD_SCOPE_UPDATES:
        before, after = _CARD_SCOPE_UPDATES[slug]
        assert expected.count(before) == 1
        expected = expected.replace(before, after)
    assert actual == expected


@pytest.mark.parametrize("slug,count,style", (
    ("multiplicative-convolution", 90, "euclidean-card"),
    ("polynomial-division-prerequisites", 85, "polynomial-card"),
))
def test_two_new_cards_have_exact_first_admission_and_original_qr_classes(output, slug, count, style):
    raw = _raw_cards(output)[slug]
    parsed = _Page(raw)
    attrs = parsed.family_links[0][1]
    assert attrs["class"].split() == ["family-card", "candidate-card", style]
    assert attrs["data-alpha-first"] == "v32"
    assert attrs["id"] == slug + "-card"
    text = "".join(parsed.text)
    assert f"Alpha v32 checked use · {count} independently proved theorems" in text
    assert "Original HA and compiled Lean verification · first admitted v32 · not Stable." in text
    assert "Alpha v31 checked use" not in text


@pytest.mark.parametrize("term", (
    "nonempty finite signed prefixes", "Normalization is F(1)=+1, signed code 2",
    "not an arbitrary signed unit", "inclusive prefix", "zeroth values remain unrestricted",
    "coprime divisor pairs", "support-sensitive reindexing", "G009 complete",
    "retain their original first-admission evidence",
))
def test_multiplicative_closure_has_the_actual_normalization_and_finite_guards(output, term):
    assert term in _raw_cards(output)["multiplicative-convolution"]


@pytest.mark.parametrize("term", (
    "26 coefficient negation/subtraction", "22 actual leading-zero trimming",
    "20 monic-normalization", "17 Horner/synthetic-division", "Highest-degree-first",
    "decoded coefficients, not code numbers", "actual quotient traces",
    "full G091 remains open", "General division by an arbitrary nonzero polynomial",
    "polynomial gcd/Bézout", "irreducible-polynomial existence in every positive degree",
    "general prime-power fields remain open in this release", "zero polynomial has no represented natural-number degree",
))
def test_polynomial_card_is_exact_prerequisite_progress_not_g091_closure(output, term):
    assert term in _raw_cards(output)["polynomial-division-prerequisites"]


@pytest.mark.parametrize("term", (
    "Current Alpha v32 release", "175 first admissions", "3,796-entry v31 parent",
    "3,971 checked-use entries", "3,539 additional Alpha-closed",
    "432 unchanged Stable theorems", "unchanged 432-theorem default library",
    "390 reviewed conservative definitions", "844 actual expansion arrows",
    "12,751 theorem dependencies", "120 major goals", "65 proof families",
    "G009 is closed for its finite signed arithmetic-table contract", "G091 remains open:",
    "Definition arrows, proof dependencies and still-open research goals remain distinct",
))
def test_current_inventory_and_proof_definition_goal_separation(output, term):
    assert term in output


def test_574_v31_admissions_are_historical_not_recounted_as_v32(output):
    assert "Nineteen chapters, 574 proofs first admitted in v31." in output
    assert "were first admitted in Alpha v31 and remain checked use in Alpha v32." in output
    assert "All 19 complete dependency bundles" in output
    assert "all 52 principal ordinary certificates were checked separately" in output
    assert output.count('data-alpha-first="v31"') == 20  # 19 cards plus their historical introduction.
    assert output.count('data-alpha-first="v32"') == 2
    assert output.count("first admitted v31 · not Stable.") == 19
    assert output.count("first admitted v32 · not Stable.") == 2


def test_current_hub_has_no_remaining_open_g009_claims(output):
    text = " ".join("".join(_Page(output).text).split())
    for sentence in re.split(r"(?<=\.)\s+", text):
        if "G009" in sentence:
            assert not re.search(r"G009 (?:still|remains broader|remain open|remains open)", sentence)
            assert "multiplicative-function closure remains open" not in sentence
    assert "G009: inverse criterion and remaining closure" not in output
    assert "G091 complete" not in output and "G091 is closed" not in output


@pytest.mark.parametrize("prefix", ("artifacts/", "checkpoints/", "release-v31/"))
def test_historical_download_and_dated_release_anchors_are_byte_exact(parent_bytes, output, prefix):
    pattern = r'<a\b[^>]*href="' + re.escape(prefix) + r'[^"]*"[^>]*>.*?</a>'
    old = Counter(re.findall(pattern, parent_bytes.decode(), re.S))
    assert old
    assert Counter(re.findall(pattern, output, re.S)) == old


def test_new_delivery_links_do_not_relabel_old_verification_records(output):
    links = _Page(output).links
    assert links.count("release-v32/manifest.json") == 1
    assert links.count("release-v32/alpha-v32-research-receipt-v1.json") == 1
    assert "Fresh v31 verification record" in output
    assert "Delivery metadata and stored records do not themselves grant proof or admission authority." in output


def test_actual_qr_hub_structure_assets_metadata_and_old_anchors_are_preserved(parent_bytes, output):
    before, after = _Page(parent_bytes.decode()), _Page(output)
    assert set(after.ids) == set(before.ids) | {"research-v32-heading", *(slug + "-card" for slug in NEW_SLUGS)}
    assert len(after.ids) == len(set(after.ids))
    assert [attrs for tag, attrs in after.tags if tag in {"header", "main", "footer"}] == [
        attrs for tag, attrs in before.tags if tag in {"header", "main", "footer"}]
    assert '<header class="hero">' in output and '<main class="shell">' in output
    assert '<div class="trust-row" aria-label="Proof properties">' in output
    assert not any(tag in {"script", "iframe", "base", "style"} for tag, _attrs in after.tags)
    assert not any(key.startswith("on") for _tag, attrs in after.tags for key in attrs)
    old_links = [attrs for tag, attrs in before.tags if tag == "link"]
    new_links = [attrs for tag, attrs in after.tags if tag == "link"]
    assert new_links == [{key: value.replace(OLD_REVISION, REVISION) for key, value in attrs.items()} for attrs in old_links]
    assert [attrs for tag, attrs in after.tags if tag == "meta" and attrs.get("name") == "proof-publication-scope"] == [
        {"name": "proof-publication-scope", "content": "alpha-v32-checked-use"}]


def test_current_html_navigation_and_atlas_deep_links_have_exact_revision(output):
    scopes = Counter()
    for link in _Page(output).links:
        parts = urlsplit(link)
        if parts.scheme or parts.path.startswith(("artifacts/", "checkpoints/", "release-v31/", "release-v32/")):
            continue
        assert parts.path.endswith(("/", ".html"))
        query = parse_qs(parts.query, strict_parsing=True)
        assert query["v"] == [REVISION]
        assert parts.fragment == ""
        if parts.path == "grand-campaign/" and query.get("focus") in (["G009"], ["G091"]):
            assert query["view"] == ["goal"]
            scopes[query["focus"][0]] += 1
    assert scopes["G009"] >= 9 and scopes["G091"] >= 5


@pytest.mark.parametrize("revision", ("abcdef123456", "000000000000", "ffffffffffff", OLD_REVISION))
def test_revision_is_only_deterministic_navigation_data_and_does_not_change_math(parent_bytes, output, revision):
    raw = hub.render_public_hub(parent_bytes, revision)
    assert type(raw) is bytes and len(raw) < 262144
    assert raw == hub.render_public_hub(parent_bytes, revision)
    assert raw.decode().replace(revision, REVISION) == output
    assert parent_bytes == PARENT.read_bytes()


class _BytesSubclass(bytes):
    pass


@pytest.mark.parametrize("attack", (
    "string", "path", "bytearray", "view", "subclass", "receipt", "foreign_capability",
    "none", "empty", "truncated", "appended", "one_changed_byte", "oversized",
))
def test_foreign_or_mutated_parent_inputs_cannot_be_formatted(parent_bytes, attack):
    inputs = {
        "string": parent_bytes.decode(), "path": PARENT, "bytearray": bytearray(parent_bytes),
        "view": memoryview(parent_bytes), "subclass": _BytesSubclass(parent_bytes),
        "receipt": {"passed": True}, "foreign_capability": object(), "none": None,
        "empty": b"", "truncated": parent_bytes[:-1], "appended": parent_bytes + b"\n",
        "one_changed_byte": b"?" + parent_bytes[1:], "oversized": b"x" * (262144 + 1),
    }
    with pytest.raises(hub.HubError):
        hub.render_public_hub(inputs[attack], REVISION)


@pytest.mark.parametrize("revision", (
    None, False, 123, b"0123456789ab", [], {}, "", "0123456789a", "0123456789abc",
    "0123456789aG", "ABCDEF012345", "0123456789a\n", "../../indexx", '" onload="x"',
))
def test_revision_is_strict_bounded_lowercase_hex_not_markup(parent_bytes, revision):
    with pytest.raises(hub.HubError, match="revision"):
        hub.render_public_hub(parent_bytes, revision)


_MUTATIONS = (
    ("old_math", ">557</dt>", ">558</dt>"),
    ("old_first_admission", "first admitted v31 · not Stable.", "first admitted v32 · not Stable."),
    ("old_first_attribute", 'data-alpha-first="v31"', 'data-alpha-first="v32"'),
    ("old_special_first", "first closed v17 · enrolled v15", "first closed v32 · enrolled v32"),
    ("old_route", "quadratic-reciprocity/?v=0123456789ab", "unknown/?v=0123456789ab"),
    ("old_external_route", "bertrand-postulate/?v=0123456789ab", "https://invalid.example/"),
    ("new_count", "90 independently proved theorems", "91 independently proved theorems"),
    ("new_first", 'data-alpha-first="v32"', 'data-alpha-first="v31"'),
    ("new_unit", "F(1)=+1, signed code 2", "F(1)=±1, either signed unit"),
    ("new_empty", "nonempty finite signed prefixes", "arbitrary empty prefixes"),
    ("new_stable", "G009 complete · independently kernel and Lean verified; not Stable", "G009 complete · Stable"),
    ("g091_overclaim", "G091 remains open:", "G091 is closed:"),
    ("g009_reopened", "G009 is closed for its finite signed arithmetic-table contract", "G009 remains open"),
    ("poly_general_division", "General division by an arbitrary nonzero polynomial", "Complete arbitrary-divisor Euclidean division"),
    ("current_count", "3,971 checked-use entries", "3,970 checked-use entries"),
    ("definition_count", "390 reviewed conservative definitions", "391 reviewed conservative definitions"),
    ("definition_edges", "844 actual expansion arrows", "845 actual expansion arrows"),
    ("proof_edges", "12,751 theorem dependencies", "12,752 theorem dependencies"),
    ("old_receipt_route", "release-v31/manifest.json", "release-v31/changed.json"),
    ("old_receipt_label", "Fresh v31 verification record", "Fresh v32 verification record"),
    ("old_checkpoint_revision", "checkpoints/?v=ac7111ec14ff", "checkpoints/?v=0123456789ab"),
    ("new_record_missing", "release-v32/alpha-v32-research-receipt-v1.json", "release-v32/unknown.json"),
    ("scope", 'content="alpha-v32-checked-use"', 'content="stable-checked-use"'),
    ("css", "assets/proofs.css?v=0123456789ab", "assets/other.css?v=0123456789ab"),
    ("script", "</head>", "<script>alert(1)</script></head>"),
    ("event", '<main class="shell">', '<main class="shell" onload="alert(1)">'),
    ("iframe", "</main>", '<iframe src="https://invalid.example/"></iframe></main>'),
    ("duplicate_id", 'id="research-v32-heading"', 'id="completed-lower-heading"'),
    ("duplicate_attribute", '<main class="shell">', '<main class="shell" class="other">'),
    ("unclosed", "</footer>", ""),
)


@pytest.mark.parametrize("_label,old,new", _MUTATIONS, ids=[row[0] for row in _MUTATIONS])
def test_rejects_mutated_delivery_projection_without_relaxing_the_parent(parent_bytes, output, _label, old, new):
    assert old in output
    changed = output.replace(old, new, 1)
    with pytest.raises(hub.HubError):
        hub._validate_projection(parent_bytes.decode(), changed, REVISION)


@pytest.mark.parametrize("attack", ("remove_old", "duplicate_old", "remove_new", "duplicate_new", "reorder_new", "missing_primary", "two_primaries"))
def test_exact_family_inventory_cannot_lose_duplicate_reorder_or_redirect_cards(parent_bytes, output, attack):
    cards = _raw_cards(output)
    old, new = cards[OLD_SLUGS[0]], cards[NEW_SLUGS[0]]
    if attack == "remove_old":
        changed = output.replace(old, "", 1)
    elif attack == "duplicate_old":
        changed = output.replace(old, old + old, 1)
    elif attack == "remove_new":
        changed = output.replace(new, "", 1)
    elif attack == "duplicate_new":
        changed = output.replace(new, new + new, 1)
    elif attack == "reorder_new":
        other = cards[NEW_SLUGS[1]]
        changed = output.replace(new, "<swap>", 1).replace(other, new, 1).replace("<swap>", other, 1)
    elif attack == "missing_primary":
        changed = output.replace('class="primary-action"', 'class="secondary-action"', 1)
    else:
        changed = output.replace("</article>", f'<a class="primary-action" href="x/?v={REVISION}">x</a></article>', 1)
    with pytest.raises(hub.HubError):
        hub._validate_projection(parent_bytes.decode(), changed, REVISION)


@pytest.mark.parametrize("source", ("no reviewed fragment", "needle needle"))
def test_reviewed_exact_fragment_replacement_rejects_absence_and_duplicates(source):
    with pytest.raises(hub.HubError):
        hub._once(source, "needle", "replacement")


def test_fixed_output_size_gate_remains_fail_closed(parent_bytes, monkeypatch):
    monkeypatch.setattr(hub, "MAX_HUB_BYTES", 1)
    with pytest.raises(hub.HubError, match="bound"):
        hub.render_public_hub(parent_bytes, REVISION)


def test_formatter_imports_only_stdlib_and_has_no_io_or_proof_authority():
    tree = ast.parse(Path(hub.__file__).read_text())
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert imports == {"__future__", "collections", "hashlib", "html.parser", "re", "urllib.parse"}
    calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    assert not calls & {"open", "exec", "eval", "compile", "__import__"}
    assert not any(isinstance(node, ast.Attribute) and node.attr in {
        "read_bytes", "read_text", "write_bytes", "write_text", "check_proof", "replay", "require_live",
        "bind_live_context", "verify_in_fresh_windows", "setrlimit", "system", "Popen",
    } for node in ast.walk(tree))


def test_actual_formatter_cold_import_and_execution_do_not_import_an_edition(parent_bytes):
    code = """import importlib.util, json, pathlib, sys
spec = importlib.util.spec_from_file_location('isolated_hub', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
raw = pathlib.Path(sys.argv[2]).read_bytes()
result = module.render_public_hub(raw, '0123456789ab')
bad = [name for name in sys.modules if name.startswith(('peano_lab', 'constructive_research_publication', 'check_alpha', 'lean'))]
assert bad == [], bad
print(json.dumps({'bytes': len(result), 'rows': len(module.FAMILY_ROUTES), 'proof_imports': bad}))
"""
    completed = subprocess.run([sys.executable, "-I", "-B", "-c", code, hub.__file__, str(PARENT)],
                               check=True, capture_output=True, text=True, timeout=15)
    assert json.loads(completed.stdout) == {"bytes": len(hub.render_public_hub(parent_bytes, REVISION)), "rows": 65, "proof_imports": []}
    assert completed.stderr == ""


class _Accounting:
    def __init__(self):
        self.ids, self.calls, self.bad = (), [], []

    def pytest_collection_modifyitems(self, items):
        self.ids = tuple(item.nodeid for item in items)
        if len(self.ids) != len(set(self.ids)):
            raise pytest.UsageError("duplicate hub test IDs")

    def pytest_runtest_logreport(self, report):
        if report.failed or report.skipped or hasattr(report, "wasxfail"):
            self.bad.append(report.nodeid)
        if report.when == "call" and report.passed:
            self.calls.append(report.nodeid)


def _main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect", type=int)
    args, pytest_args = parser.parse_known_args(argv)
    account = _Accounting()
    status = int(pytest.main([str(Path(__file__)), *(pytest_args or ["-q"])], plugins=[account]))
    elapsed = time.monotonic() - _STARTED
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = int(usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024)
    if args.expect is not None and len(account.ids) != args.expect:
        status = 1
    if "--collect-only" not in pytest_args and (account.calls != list(account.ids) or account.bad):
        status = 1
    if elapsed > 180 or rss > 1536 * 1024 * 1024 or resource.getrlimit(resource.RLIMIT_CPU) != (170, 175):
        status = 1
    print(json.dumps({"status": status, "unique_cases": len(account.ids),
        "node_ids_sha256": sha256("\n".join(sorted(account.ids)).encode()).hexdigest(),
        "seconds": elapsed, "cpu_seconds": usage.ru_utime + usage.ru_stime,
        "peak_rss_bytes": rss, "cpu_limits": [170, 175], "wall_alarm_seconds": 180}, sort_keys=True), flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(_main())
