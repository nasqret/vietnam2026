"""Current v31 delivery contracts, distinct from the frozen v30 regression.

Formatting fixtures contain no proof data and never enter a proof checker.
The real-tree tests require the actual three published v31 trees; no missing
release is skipped or replaced by a fixture.
"""

from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_constructive_completed_lower_hub_v31 as hub
import constructive_completed_lower_publication_v31 as publication
import stage_completed_lower_publication_v31 as staging
from serve_lean_strands import COMPLETED_LOWER_V31_FAMILIES, HISTORICAL_V31_FIRST_ADMISSIONS


class Links(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.primary = []
        self.links = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a" and "href" in attributes:
            self.links.append(attributes["href"])
            if "primary-action" in attributes.get("class", "").split():
                self.primary.append(attributes["href"])


@pytest.fixture()
def format_only():
    # Deliberately no theorem statements, proof receipts, or LiveReleaseContext.
    families = [{"slug": name, "title": "Formatting fixture " + name,
                 "theorem_count": count, "goals": ["G009"], "caveat": "<honest scope>"}
                for name, count in publication.FAMILY_COUNTS.items()]
    return hub.HISTORICAL_HUB.read_text(), families, "a" * 12


def test_historical_template_is_literal_not_silently_updated():
    assert sha256(hub.HISTORICAL_HUB.read_bytes()).hexdigest() == "6c4738a077b2cc147ccb4393b1f3c369274b6253553a11f2bfaa5ec9f025be6b"
    assert "not Alpha admitted" in hub.HISTORICAL_HUB.read_text()


def test_formatter_preserves_qr_design_and_exact_63_family_inventory(format_only):
    text = hub.render_hub(*format_only).decode()
    links = Links(text)
    families = [urlsplit(link).path.rstrip("/") for link in links.primary
                if urlsplit(link).path.rstrip("/") != "grand-campaign"]
    assert len(families) == len(set(families)) == 63
    assert set(families) == set(COMPLETED_LOWER_V31_FAMILIES) | set(HISTORICAL_V31_FIRST_ADMISSIONS)
    assert 'class="family-card qr-card"' in text
    assert 'class="family-card bertrand-card"' in text
    assert 'class="hero"' in text and 'class="family-grid' in text
    assert '&lt;honest scope&gt;' in text and '<honest scope>' not in text
    assert "3,796 checked-use" in text and "unchanged 432" in text
    assert "Full G009 still needs multiplicative closure" in text
    assert "general prime-power fields in G091 remain open" in text
    assert "not Alpha admitted" not in text
    assert "Full Möbius inversion and general prime-power fields remain open" not in text
    for link in links.primary:
        assert parse_qs(urlsplit(link).query)["v"] == [format_only[2]]
    assert "checkpoints/?v=ac7111ec14ff" in links.links
    assert "checkpoints/lower-tier/?v=ac7111ec14ff" in links.links
    assert 'data-alpha-first="v31"' in text
    assert 'Alpha v30 checked use' not in text


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "wrong_count", "unreviewed", "revision", "old_template"))
def test_formatter_rejects_incomplete_or_unreviewed_inventory(format_only, mutation):
    source, rows, revision = format_only
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = deepcopy(rows[0])
    elif mutation == "wrong_count":
        rows[0]["theorem_count"] += 1
    elif mutation == "unreviewed":
        rows[0]["slug"] = "invented-proof"
    elif mutation == "revision":
        revision = '<script>bad'
    else:
        source = source.replace("Forty-two constructive proof campaigns, transparently labeled.", "Altered template")
    with pytest.raises((hub.DeliveryError, ValueError)):
        hub.render_hub(source, rows, revision)


@pytest.mark.parametrize("name", ("/outside", "../outside", "x/../outside", "x//file", "x\\file", ""))
def test_staging_rejects_unsafe_inventory_paths(name):
    with pytest.raises(hub.DeliveryError):
        staging._pins({"files": {name: {"bytes": 1, "sha256": "a" * 64}}, "file_count_excluding_manifest": 1})


@pytest.mark.parametrize("binding", (
    {"bytes": True, "sha256": "a" * 64}, {"bytes": 0, "sha256": "a" * 64},
    {"bytes": 64 * 1024 * 1024 + 1, "sha256": "a" * 64},
    {"bytes": 1, "sha256": "bad"}, {"bytes": 1, "sha256": 123},
    {"bytes": 1, "sha256": "a" * 64, "extra": True},
))
def test_staging_rejects_unsafe_file_bindings(binding):
    with pytest.raises(hub.DeliveryError):
        staging._pins({"files": {"file.html": binding}, "file_count_excluding_manifest": 1})


def test_staging_does_not_authorize_any_arbitrary_output_root(tmp_path):
    with pytest.raises(hub.DeliveryError, match="limited"):
        staging.stage(tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("kind", ("file_link", "directory_link", "regular_directory"))
def test_destination_refuses_symlinks_and_wrong_file_types(tmp_path, kind):
    target = tmp_path / "a"
    outside = tmp_path / "outside"
    outside.mkdir()
    if kind == "directory_link":
        target.symlink_to(outside, target_is_directory=True)
        name = "a/file.html"
    elif kind == "file_link":
        target.symlink_to(outside / "absent")
        name = "a"
    else:
        target.mkdir()
        name = "a"
    with pytest.raises(hub.DeliveryError):
        staging._destination(tmp_path, name, create=True)
    assert not list(outside.iterdir())


def test_check_accepts_only_one_exact_delivery_selector(tmp_path):
    source = b"<html><head></head><body>honest proof</body></html>"
    selector = b'<script src="/proofs/assets/lean-selector.js"></script>'
    path = tmp_path / "reader.html"
    path.write_bytes(source)
    staging._public_bytes(path, hub.pin(source), selector=selector)
    path.write_bytes(source.replace(b"</head>", selector + b"</head>"))
    staging._public_bytes(path, hub.pin(source), selector=selector)
    for wrong in (source + selector + selector, source.replace(b"honest", b"forged"), source + b" "):
        path.write_bytes(wrong)
        with pytest.raises(hub.DeliveryError):
            staging._public_bytes(path, hub.pin(source), selector=selector)


def test_actual_current_hub_and_delivery_inventory_are_exact():
    expected = hub.build_files()
    assert all(path.read_bytes() == payload for path, payload in expected.items())
    lock = json.loads(expected[hub.LOCK])
    assert lock["family_count"] == 63 and lock["new_theorem_count"] == 574
    assert lock["checked_use_count"] == 3796 and lock["stable_count"] == 432
    inventory, observed = staging.source_inventory()
    assert lock == observed
    assert len(inventory) > 11000
    assert {slug + "/index.html" for slug in COMPLETED_LOWER_V31_FAMILIES} <= inventory.keys()
    assert {slug + "/api/first-admission.json" for slug in HISTORICAL_V31_FIRST_ADMISSIONS} <= inventory.keys()
    assert inventory["grand-campaign/campaign.json"][0] == ROOT / "book/_static/constructive-completed-lower-campaign-v31/campaign.json"
    assert "quadratic-reciprocity/explorer/k3b/index.html" not in inventory


def test_stage_orders_current_overlay_before_selectors_and_checks_final_bytes():
    process = subprocess.run(["make", "-n", "stage-proofs"], cwd=ROOT, text=True,
                             capture_output=True, timeout=15, check=True)
    output = process.stdout
    historical = output.index("scripts/stage_lower_tier_checkpoint_navigation.py")
    current = output.index("scripts/stage_completed_lower_publication_v31.py")
    selector = output.index("scripts/stage_public_lean_selector.py")
    final_check = output.rindex("scripts/stage_completed_lower_publication_v31.py")
    assert historical < current < selector < final_check
    assert "--check --api-url" in output[final_check:]
    assert "book/_static/pa-proof-explorer/" in output
    assert "rsync -avz" not in output and "ssh " not in output


def test_actual_current_atlas_closes_only_exact_new_endpoints():
    campaign = json.loads((ROOT / "book/_static/constructive-completed-lower-campaign-v31/campaign.json").read_bytes())
    nodes = {row["id"]: row for row in campaign["nodes"]}
    assert campaign["meta"]["completed_lower_named_targets"] == ["G007", "G014"]
    assert nodes["G007"]["evidence"]["theorem_name"] == "mobius_inversion_arithmetic_tables"
    assert nodes["G014"]["evidence"]["theorem_name"] == "euler_coprime_totient_power"
    assert nodes["G009"]["status"] == nodes["G091"]["status"] == "open"
    assert nodes["G009"]["evidence"]["multiplicative_convolution_closure_proved"] is False
