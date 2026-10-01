#!/usr/bin/env python3
"""Stage an additive, non-admitting research publication over sealed Alpha v35.

Hashes authenticate delivery bytes, never mathematical proof or checked use.
No network, registry mutation, public Lean build, or Alpha admission is performed.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "_deploy/proofs-v35"
SITE = ROOT / "book/_static/constructive-sqrt2-power-campaign"
PARENT_MANIFEST = "release-v35/manifest.json"
PARENT_SHA256 = "6b11439683ec1d60baa0ea328536e1f8fb2d9057f362c3fe269f684894142756"
SITE_MANIFEST = "api/manifest.json"
SITE_SHA256 = "1f715918afb40927553537b2b23a1dc6f2fe6e2b954d237c43bd0468e6df1515"
RELEASE = "research-releases/sqrt2-power-2026-10-01/manifest.json"
ENTRANCES = ("index.html", "grand-campaign/index.html")


def pin(data):
    return dict(bytes=len(data), sha256=sha256(data).hexdigest())


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def safe_path(root, name):
    if (not isinstance(name, str) or not name or len(name) > 300
        or not re.fullmatch(r"[A-Za-z0-9_./-]+", name)
        or any(part in {"", ".", ".."} for part in name.split("/"))
        or PurePosixPath(name).is_absolute()):
        raise ValueError("unsafe delivery path")
    root = Path(root)
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("symlink delivery root")
    path = root
    for part in name.split("/"):
        path /= part
        if path.is_symlink():
            raise ValueError("symlink delivery member: " + name)
    return path


def file_pin(path):
    size = path.stat().st_size
    if not path.is_file() or size > 32 * 1024**2:
        raise ValueError("not a bounded regular delivery file")
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            h.update(chunk)
    return dict(bytes=size, sha256=h.hexdigest())


def inventory(root, expected):
    if not isinstance(expected, dict) or not 1 <= len(expected) <= 15000:
        raise ValueError("invalid delivery inventory")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlink in delivery tree")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
            if len(actual) > 15000:
                raise ValueError("oversized delivery inventory")
    if actual != set(expected):
        raise ValueError("missing or unregistered delivery files")
    for name, item in expected.items():
        if (not isinstance(item, dict) or set(item) != {"bytes", "sha256"}
            or type(item["bytes"]) is not int or item["bytes"] < 0
            or not isinstance(item["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
            or file_pin(safe_path(root, name)) != item):
            raise ValueError("delivery bytes differ: " + name)


def authenticated_manifest(root, name, expected_hash, field):
    path = safe_path(root, name)
    if path.stat().st_size > 8 * 1024**2:
        raise ValueError("oversized manifest")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_hash:
        raise ValueError("sealed manifest differs")
    value = json.loads(raw)
    expected = dict(value[field])
    if name in expected:
        raise ValueError("manifest cannot authenticate itself")
    expected[name] = pin(raw)
    inventory(root, expected)
    return value, expected


def insert_once(raw, marker, addition):
    if raw.count(marker) != 1:
        raise ValueError("navigation insertion point changed")
    return raw.replace(marker, marker + addition, 1)


def entrance_bytes(parent):
    hub = (parent / ENTRANCES[0]).read_bytes()
    atlas = (parent / ENTRANCES[1]).read_bytes()
    hub_notice = b'''
    <section class="frontier-intro" id="sqrt2-research-checkpoint" aria-labelledby="sqrt2-research-title">
      <p class="eyebrow">Research checkpoint / 1 October 2026 / not an Alpha admission</p>
      <h2 id="sqrt2-research-title">Irrationality first, transcendence next.</h2>
      <p>Explore the campaign for (sqrt2)^(sqrt2): 33 distinct HA/Lean-checked supporting statements, conservative local definition DAGs and exact downloadable evidence.</p>
      <p class="candidate-disclaimer">Full irrationality and transcendence remain open. These supporting results do not increase Alpha v35 (4,318 entries) or Stable (432 theorems).</p>
      <p><a class="primary-action" href="sqrt2-power/">Open the research campaign</a></p>
      <p><a href="sqrt2-power/arithmetic-frontier.html">Checked arithmetic DAG</a> / <a href="sqrt2-power/quadratic-trace-definitions.html">Finite-product definitions</a> / <a href="sqrt2-power/grand-campaign/index.html?view=family&amp;focus=F13">Combined 122-goal research atlas</a> / <a href="research-releases/sqrt2-power-2026-10-01/manifest.json">Research delivery inventory</a></p>
    </section>'''
    atlas_notice = b'''
  <aside class="notice" id="sqrt2-research-checkpoint" style="margin:1rem;padding:1rem">
    <strong>New research extension: irrationality first, transcendence next.</strong>
    <a href="../sqrt2-power/grand-campaign/index.html?view=family&amp;focus=F13">Open the combined 122-goal atlas (F13 / G121 / G122)</a> /
    <a href="../sqrt2-power/arithmetic-frontier.html">33 checked supporting statements and their arithmetic DAG</a>.
    Both new targets remain open; no new Alpha/Stable admissions. This historical 120-goal atlas and its proof evidence are unchanged.
  </aside>'''
    return {
        ENTRANCES[0]: insert_once(hub, b'<main class="shell">', hub_notice),
        ENTRANCES[1]: insert_once(atlas, b"<body>", atlas_notice),
    }


def stage(output):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("new, non-overwriting stage directory required")
    safe_path(output.parent, output.name)
    parent, old = authenticated_manifest(PARENT, PARENT_MANIFEST, PARENT_SHA256, "current_files")
    site, campaign = authenticated_manifest(SITE, SITE_MANIFEST, SITE_SHA256, "files")
    if (len(old) != 13798 or len(campaign) != 264
        or parent["current_alpha_checked_use_count"] != 4318 or parent["stable_count"] != 432
        or site["authority"] != "planning_only" or site["new_ha_proofs"] != 0):
        raise ValueError("release boundary changed")
    wave = json.loads((SITE / "api/wave-results.json").read_bytes())
    if (wave["counts"]["unique_HA_statements"] != 33
        or wave["counts"]["unique_Lean_checked_statements"] != 33
        or wave["library_admissions"] != 0 or wave["IR_parents_closed"] != 0):
        raise ValueError("research evidence boundary changed")
    files = {"sqrt2-power/" + name: safe_path(SITE, name).read_bytes() for name in campaign}
    files.update(entrance_bytes(PARENT))
    additions = set(files) - set(ENTRANCES)
    if additions & set(old) or RELEASE in old:
        raise ValueError("new research namespace collides with parent")
    manifest = dict(
        schema="sqrt2-power-research-delivery-v1", delivery_metadata_only=True,
        authority="research_publication_not_library_admission",
        current_alpha_version="v35", current_alpha_checked_use_count=4318, stable_count=432,
        alpha_admission_performed=False, stable_admission_performed=False,
        IR072_proved=False, TR006_proved=False, new_library_admissions=0,
        public_on_demand_builds=False, published_supporting_statements=33,
        parent_manifest=dict(path=PARENT_MANIFEST, sha256=PARENT_SHA256),
        campaign_manifest=dict(path="sqrt2-power/"+SITE_MANIFEST, sha256=SITE_SHA256),
        parent_file_count=len(old), preserved_parent_file_count=len(old)-len(ENTRANCES),
        replaced_navigation={name: dict(before=old[name], after=pin(files[name])) for name in ENTRANCES},
        files={name: pin(raw) for name, raw in sorted(files.items())},
        payload_file_count=len(files)+1,
        proof_evidence="Exact indexed historical HA/Lean observations; no stored receipt grants checked-use authority.",
    )
    files[RELEASE] = encode(manifest)
    for name, raw in files.items():
        path = safe_path(output, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
    inventory(output, {name: pin(raw) for name, raw in files.items()})
    return dict(status="research_delta_staged", files=len(files),
        preserved_parent_files=manifest["preserved_parent_file_count"],
        manifest_sha256=pin(files[RELEASE])["sha256"], new_library_admissions=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(stage(args.output), sort_keys=True))
        return
    if not args.report or args.report.exists() or args.report.is_symlink():
        parser.error("a new append-only --report is required")
    from sqrt2_power_automation_baseline import runtime
    from run_sqrt2_power_pilot import save_new, successful
    command = (sys.executable, "-B", str(Path(__file__).resolve()), "--worker", "--output", str(args.output))
    limits = runtime().ProcessLimits(cpu_seconds=25, wall_seconds=35,
        rss_bytes=512*1024**2, output_bytes=1024**2)
    process = runtime().run_bounded(command, cwd=ROOT, limits=limits)
    runtime().validate_process_record(process, command=command, limits=limits)
    save_new(args.report, encode(dict(schema="sqrt2-power-research-stage-observation-v1",
        process=process, status="passed" if successful(process) else "failed",
        authority="delivery_observation_not_proof", source=file_pin(Path(__file__)), max_workers=1)))
    print(process["stdout"] or process["stderr"], end="")
    raise SystemExit(0 if successful(process) else 1)


if __name__ == "__main__":
    main()
