"""Independent pure v33 hub observations; no publication authority."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

import pytest
import build_constructive_research_hub_v33 as hub
import test_build_constructive_research_hub_v32 as old_tests

ROOT = Path(__file__).resolve().parents[1]
REVISION = "0123456789ab"
SLUGS = (*old_tests.EXPECTED_SLUGS[:2], "polynomial-euclidean-division", *old_tests.EXPECTED_SLUGS[2:])


@pytest.fixture(scope="module")
def parent():
    raw = hub.previous.render_public_hub((ROOT / "deploy/proofs/index.html").read_bytes(), "41b9f387d88a")
    assert len(raw) == 85047
    assert sha256(raw).hexdigest() == "307611d61cf2deabd021f50f920f305368aadfc040f7ceb0e78c66806ed20a36"
    return raw


@pytest.fixture(scope="module")
def output(parent):
    return hub.render_public_hub(parent, REVISION).decode()


def test_exact66_primary_entrances_and_unchanged_qr_structure(parent, output):
    before, after = old_tests._Page(parent.decode()), old_tests._Page(output)
    assert len(SLUGS) == len(set(SLUGS)) == 66
    assert [href for href, _attributes in after.family_links] == [slug + "/?v=" + REVISION for slug in SLUGS]
    assert set(after.ids) == set(before.ids) | {"research-v33-heading", "polynomial-euclidean-division-card"}
    assert not re.search(r"<(?:script|style|iframe)\b", output)
    assert 'href="assets/proofs.css?v=' + REVISION + '"' in output


@pytest.mark.parametrize("phrase", (
    "4,092 checked-use entries", "3,660 additional Alpha-closed", "432 unchanged Stable theorems",
    "397 reviewed conservative definitions", "865 actual expansion arrows", "13,212 theorem dependencies",
    "66 proof families", "121 newly admitted results", "full G091 remains open",
    "execution uniqueness", "arbitrary formal-identity quotient/remainder uniqueness is a later theorem",
    "first admitted v33", "first admitted v32", "first admitted v31",
    "release-v33/manifest.json", "release-v33/alpha-v33-research-receipt-v1.json",
))
def test_exact_new_current_and_first_admission_boundaries(output, phrase):
    assert phrase in output


def test_old_artifact_and_first_admission_links_are_retained(parent, output):
    before, after = old_tests._Page(parent.decode()), old_tests._Page(output)
    prefix = ("artifacts/", "checkpoints/", "release-v31/", "release-v32/")
    assert Counter(x for x in before.links if x.startswith(prefix)) == Counter(x for x in after.links if x.startswith(prefix))
    assert output.count('data-alpha-first="v33"') == 1
    assert output.count('data-alpha-first="v32"') == parent.decode().count('data-alpha-first="v32"') + 1


@pytest.mark.parametrize("bad", (None, b"", b"unissued", bytearray(b"unissued"), "not bytes"))
def test_nonliteral_hub_parent_is_rejected(bad):
    with pytest.raises(hub.HubError):
        hub.render_public_hub(bad, REVISION)


@pytest.mark.parametrize("bad", (None, "", "A" * 12, "../unsafe", "a" * 64, "a" * 11))
def test_unsafe_current_revisions_are_rejected(parent, bad):
    with pytest.raises(hub.HubError):
        hub.render_public_hub(parent, bad)


@pytest.mark.parametrize("before,after", (
    ('id="research-v33-heading"', 'id="completed-lower-heading"'),
    ('data-alpha-first="v33"', 'data-alpha-first="v32"'),
    ("4,092 checked-use entries", "4,091 checked-use entries"),
    ("121 newly admitted results", "122 newly admitted results"),
    ("865 actual expansion arrows", "866 actual expansion arrows"),
    ("66 proof families", "67 proof families"),
    ("first admitted v32 · not Stable.", "first admitted v33 · not Stable."),
    ('href="polynomial-euclidean-division/?v=', 'href="foreign-family/?v='),
    ('content="alpha-v33-checked-use"', 'content="stable-checked-use"'),
    ("full G091 remains open", "full G091 is closed"),
))
def test_altered_structure_counts_admission_or_proof_claim_is_rejected(parent, output, before, after):
    assert before in output
    with pytest.raises(hub.HubError):
        hub._validate_projection(parent.decode(), output.replace(before, after, 1), REVISION)
