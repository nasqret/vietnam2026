#!/usr/bin/env python3
"""Stage the library-wide reading policy over a preserved, authenticated release.

Only proof-page presentation changes. Exact recovery of each original page,
unchanged mathematical artifacts/assets, a complete audit and a no-clobber
atomic publication boundary are checked before a new local stage is admitted.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import resource
import signal
import sys
from tempfile import TemporaryDirectory
import time

from proof_readability import enhance_page, strip_reading_layer
from proof_reading_definitions import ReadingDefinitions
from stage_proof_explorer_layout import (
    CPU_LIMITS, MAX_RSS, WALL_SECONDS, canonical, inventory, ordinary, pin, read, require,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST = "presentation/lean-policy-v1.json"
BASE_SHA256 = "ac463f91abecc4da1db5be466d7215adaa9002d0450f41f973977630bdd95aac"
MANIFEST = "presentation/readability-v1.json"
AUDIT = "reading/audit.json"
AUDIT_HTML = "reading/index.html"
ASSETS = {
    "assets/proof-reader.css": "deploy/proofs/proof-reader.css",
    "assets/proof-reader.js": "deploy/proofs/proof-reader.js",
}
NOTES = "deploy/proofs/proof-reader-notes.json"
CONTROLS = ("scripts/stage_proof_readability.py", "scripts/proof_readability.py", NOTES, *ASSETS.values(),
    "scripts/proof_reading_definitions.py", "scripts/constructive_formula_compactor.py",
    "peano-lab/py/peano_lab/library/defined_edition.py", "peano-lab/py/peano_lab/library/defined_syntax.py",
    "peano-lab/py/peano_lab/library/bertrand_defined_edition.py",
    "peano-lab/py/peano_lab/kernel/formulas.py", "peano-lab/py/peano_lab/kernel/terms.py")


def validate_base(base, files, accepted_sha256):
    raw = read(base / BASE_MANIFEST)
    require(sha256(raw).hexdigest() == accepted_sha256, "unaccepted public policy manifest")
    policy = json.loads(raw)
    require(policy.get("schema") == "peano-proof-public-lean-policy-v1"
        and policy.get("presentation_only") is True
        and policy.get("proof_bytes_changed") is False
        and policy.get("html_bytes_changed") is False
        and policy.get("public_on_demand_builds") is False
        and policy.get("alpha_admission_performed") is False
        and policy.get("stable_admission_performed") is False,
        "base is not the preserved public Lean policy")
    require(not ({MANIFEST, AUDIT, AUDIT_HTML, *ASSETS} & set(files)), "base already contains a reading layer")
    restored = {name: value for name, value in files.items() if name != BASE_MANIFEST}
    for name, change in policy["changed_files"].items():
        require(restored.get(name) == change["after"], "base public asset changed: " + name)
        restored[name] = change["before"]
    require(len(restored) == policy["base_file_count"]
        and sha256(canonical(restored)).hexdigest() == policy["base_inventory_sha256"],
        "base proof, page or asset inventory changed")
    return policy, pin(raw)


def asset_prefix(name):
    return posixpath.relpath("assets", str(PurePosixPath(name).parent)) + "/"


def reading_audit(records, registries=None):
    families = {}
    for path, record in records.items():
        parts = path.split("/")
        require("explorer" in parts and parts.index("explorer") > 0, "proof page has no family route")
        family = parts[parts.index("explorer") - 1]
        data = families.setdefault(family, dict(pages=0, exact_pages=0, defined_pages=0,
            local_claims=0, large_defined_claims=0, previous_large_defined_claims=0,
            compacted_defined_claims=0, curated_pages=0))
        data["pages"] += 1
        data[record["edition"] + "_pages"] += 1
        data["curated_pages"] += int(record["curated_mathematical_explanation"])
        if record["edition"] == "defined":
            data["local_claims"] += record["local_claim_count"]
            data["large_defined_claims"] += record["large_display_claims"]
            data["previous_large_defined_claims"] += record.get("previous_large_display_claims", record["large_display_claims"])
            data["compacted_defined_claims"] += record.get("notation_compacted_claims", 0)
    defined = [(path, record) for path, record in records.items() if record["edition"] == "defined"]
    worst = sorted(defined, key=lambda item: (-item[1]["max_defined_claim_characters"], item[0]))[:100]
    historical = sum(path.startswith("checkpoints/") for path in records)
    return dict(schema="peano-proof-reading-audit-v1", presentation_only=True,
        proof_authority=False, pages=len(records), family_count=len(families), families=families,
        current_release_pages=len(records) - historical, historical_checkpoint_pages=historical,
        distinct_theorem_names=len({record["theorem"] for record in records.values()}),
        distinct_native_scripts=len({record["script_sha256"] for record in records.values()}),
        curated_pages=sum(record["curated_mathematical_explanation"] for record in records.values()),
        curated_theorem_names=sorted({record["theorem"] for record in records.values() if record["curated_mathematical_explanation"]}),
        local_claims_in_defined_pages=sum(record["local_claim_count"] for _, record in defined),
        large_defined_claims=sum(record["large_display_claims"] for _, record in defined),
        previous_large_defined_claims=sum(record.get("previous_large_display_claims", record["large_display_claims"]) for _, record in defined),
        compacted_defined_claims=sum(record.get("notation_compacted_claims", 0) for _, record in defined),
        compacted_exact_claims=sum(record.get("notation_compacted_claims", 0) for record in records.values() if record["edition"] == "exact"),
        notation_display_characters_saved=sum(record.get("notation_display_characters_saved", 0) for record in records.values()),
        notation_source_size_skips=sum(record.get("notation_source_size_skips", 0) for record in records.values()),
        definition_registries=registries or {},
        paired_exact_defined_pages=len(defined),
        pages_with_paired_notation=sum(record.get("paired_notation_rows", 0) > 0 for _, record in defined),
        paired_notation_rows=sum(record.get("paired_notation_rows", 0) for _, record in defined),
        worst_defined_claim_pages=[dict(path=path, **record) for path, record in worst],
        pages_by_path=records,
        caveat="Structural coverage is library-wide. Curated mathematical explanations are explicitly counted, not claimed for every proof. No new theorem, definition, admission or Lean Live verification is created.")


def render_audit(audit):
    rows = ''.join('<tr><td><a href="../' + escape(family) + '/">' + escape(family.replace('-', ' ')) + '</a></td>'
        + ''.join('<td>' + str(data[key]) + '</td>' for key in ('defined_pages', 'local_claims', 'compacted_defined_claims', 'large_defined_claims')) + '</tr>'
        for family, data in sorted(audit["families"].items()))
    worst = ''.join('<li><a href="../' + escape(row["path"]) + '">' + escape(row["theorem"].replace('_', ' '))
        + '</a> · ' + format(row["max_defined_claim_characters"], ',') + ' characters in the largest defined local claim</li>'
        for row in audit["worst_defined_claim_pages"][:30] if row["max_defined_claim_characters"])
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Proof reading audit · Constructive number theory</title><link rel="stylesheet" href="../assets/proofs.css"></head>'
        '<body class="family-page proof-readability-page"><header class="family-hero"><div class="shell">'
        '<nav class="crumbs"><a href="../">Proof library</a><span>/</span><a href="../grand-campaign/">Campaign atlas</a></nav>'
        '<p class="eyebrow">Reading policy · transparent coverage</p><h1>Understand the argument.<br>Inspect every detail.</h1>'
        f'<p class="lede">Source-linked reading checkpoints across {audit["family_count"]} proof families: {audit["current_release_pages"]:,} current-release theorem pages and {audit["historical_checkpoint_pages"]:,} preserved historical-checkpoint pages. Mathematical evidence and admission status stay unchanged.</p>'
        '<div class="hero-actions"><a href="../two-squares/explorer/defined/tag/TS003F.html">Read the two-squares example</a>'
        '<a href="audit.json">Inspect the complete audit</a></div></div></header>'
        '<main class="shell family-main"><section class="release-note"><h2>What this layer does—and does not claim</h2>'
        '<p>Each reading checkpoint cites its original commands. Definitions keep their original links; long formulas and the original command ledger remain expandable. Every defined page is bound to its paired exact edition, with direct links to native commands. Structural groups are consecutive commands, not reconstructed proof-tree branches.</p>'
        f'<p>The existing family definition DAGs reduce {audit["compacted_defined_claims"]:,} long defined-edition local claims and {audit["compacted_exact_claims"]:,} exact-edition reading claims. '
        f'Each replacement passes an exact formula-and-free-context expansion comparison. Large defined claims fall from {audit["previous_large_defined_claims"]:,} to {audit["large_defined_claims"]:,}; no new definition is invented.</p>'
        f'<p>There are script-bound mathematical notes for {len(audit["curated_theorem_names"])} distinct theorem names, appearing on {audit["curated_pages"]} pages. Other pages explicitly use structural guides. '
        'This is not a claim that every proof now has a human-authored explanation. No additional theorem or definition has been admitted to Alpha or Stable.</p></section>'
        '<section class="release-note"><h2>Coverage by family</h2><div style="overflow-x:auto"><table><thead><tr><th>Family</th><th>Defined pages</th><th>Local claims</th><th>Newly compacted</th><th>Long claims still expandable</th></tr></thead><tbody>'
        + rows + '</tbody></table></div></section><section class="release-note"><h2>Next mathematical exposition priorities</h2>'
        '<p>These pages still contain large compound conditions even after existing conservative definitions are applied. They are visible priorities for further definition work and mathematical explanation, not silently declared solved.</p><ol>'
        + worst + '</ol></section></main></body></html>').encode()


def stage(base, output, *, check=False, accepted_sha256=BASE_SHA256):
    base, output = Path(base).absolute(), Path(output).absolute()
    require(base != output and base not in output.parents and output not in base.parents, "reading output must be separate from its preserved base")
    require(not output.is_symlink(), "linked reading destination")
    ordinary(output.parent, directory=True)
    if not check:
        require(not output.exists(), "reading output already exists; use --check")
    files = inventory(base)
    policy, base_pin = validate_base(base, files, accepted_sha256)
    controls = {name: pin(read(ROOT / name)) for name in CONTROLS}
    assets = {name: read(ROOT / source) for name, source in ASSETS.items()}
    revision = sha256(b"".join(assets.values())).hexdigest()[:12]
    notes = json.loads(read(ROOT / NOTES))
    require(notes.get("schema") == "peano-script-bound-reading-notes-v1" and notes.get("proof_authority") is False, "invalid reading notes")
    changed, records, registries = {}, {}, {}

    @lru_cache(maxsize=2)
    def definitions_for(family_root):
        for relative in ("api/corpus.json", "explorer/defined/api/corpus.json"):
            name = family_root + "/" + relative
            if name not in files:
                continue
            raw = read(base / name)
            require(pin(raw) == files[name], "family definition source changed")
            rows = json.loads(raw).get("definitions", [])
            if not rows:
                continue
            definitions = ReadingDefinitions(rows, dict(path=name, **files[name]))
            for identifier in definitions.by_id:
                require(family_root + "/explorer/defined/definition/" + identifier + ".html" in files,
                    "definition DAG lacks an existing expansion page")
            registries[family_root] = definitions.report
            return definitions
        return None

    def transform(name, raw):
        if not name.endswith(".html"):
            return raw, None
        notation = None
        if b'class="pd-formal-proof"' in raw or b'class="pa-formal-proof"' in raw:
            require(name.count("/explorer/") == 1, "proof page lacks an unambiguous family route")
            notation = definitions_for(name.split("/explorer/", 1)[0])
        exact_raw, exact_href, exact_name = None, None, name
        if b'class="pd-formal-proof"' in raw:
            route = "/explorer/defined/tag/"
            require(name.count(route) == 1, "defined theorem lacks an unambiguous paired route")
            exact_name = name.replace(route, "/explorer/tag/", 1)
            require(exact_name in files, "defined theorem lacks its exact edition")
            exact_raw = read(base / exact_name)
            require(pin(exact_raw) == files[exact_name], "paired exact source changed before reading")
            exact_href = posixpath.relpath(exact_name, str(PurePosixPath(name).parent))
        revised, report = enhance_page(raw, assets_prefix=asset_prefix(name), revision=revision,
            notes=notes, exact_raw=exact_raw, exact_href=exact_href, definitions=notation)
        if report is not None:
            report["exact_source_path"] = exact_name
        return revised, report

    def process(destination=None):
        for name, before in files.items():
            raw = read(base / name)
            require(pin(raw) == before, "base changed before reading")
            revised, report = transform(name, raw)
            if report is not None:
                require(strip_reading_layer(revised) == raw, "original proof page cannot be recovered")
                changed[name] = {"before": before, "after": pin(revised)}
                records[name] = dict(report, historical_checkpoint=name.startswith("checkpoints/"))
            if destination is not None:
                write(destination, name, revised)

    def write(directory, name, raw):
        path = directory / name
        path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
        path.chmod(0o644)

    def metadata():
        require(records, "base contains no supported theorem pages")
        for name, record in records.items():
            if record["edition"] == "defined":
                exact = records.get(record["exact_source_path"], {})
                require(exact.get("edition") == "exact" and exact.get("theorem") == record["theorem"]
                    and exact.get("script_sha256") == record["script_sha256"],
                    "defined page is not bound to an identical native script: " + name)
        audit = reading_audit(records, registries)
        require(set(audit["families"]) == set(policy["families"]),
            "reading family mismatch; missing=" + repr(sorted(set(policy["families"]) - set(audit["families"])))
            + "; unexpected=" + repr(sorted(set(audit["families"]) - set(policy["families"]))))
        additions = {**assets, AUDIT: canonical(audit), AUDIT_HTML: render_audit(audit)}
        record = dict(schema="peano-proof-readability-stage-v1", presentation_only=True,
            proof_bytes_changed=False, native_scripts_changed=False, original_assets_changed=False,
            mathematical_definitions_changed=False, alpha_admission_performed=False,
            stable_admission_performed=False, public_on_demand_builds=False,
            base_manifest={"path": BASE_MANIFEST, **base_pin}, base_file_count=len(files),
            base_inventory_sha256=sha256(canonical(files)).hexdigest(), controls=controls,
            asset_revision=revision, page_count=len(records), family_count=audit["family_count"],
            families=sorted(audit["families"]), changed_files=changed,
            additions={name: pin(raw) for name, raw in additions.items()})
        additions[MANIFEST] = canonical(record)
        return additions, audit

    def verify(directory, additions):
        actual = inventory(directory)
        require(set(actual) == set(files) | set(additions), "unexpected reading output files")
        for name, before in files.items():
            require(actual[name] == changed.get(name, {}).get("after", before), "reading output changed unexpected bytes: " + name)
        for name, raw in additions.items():
            require(actual[name] == pin(raw), "reading addition differs: " + name)
        require(inventory(base) == files, "preserved public base changed during reading stage")
        require(all(pin(read(ROOT / name)) == expected for name, expected in controls.items()), "reading controls changed during staging")

    if check:
        process()
        additions, audit = metadata()
        verify(output, additions)
    else:
        with TemporaryDirectory(prefix=".proof-reading-", dir=output.parent) as temporary:
            candidate = Path(temporary) / "files"
            candidate.mkdir(mode=0o755)
            process(candidate)
            additions, audit = metadata()
            for name, raw in additions.items():
                write(candidate, name, raw)
            for path in (candidate, *(path for path in candidate.rglob("*") if path.is_dir())):
                path.chmod(0o755)
            verify(candidate, additions)
            require(not output.exists() and not output.is_symlink(), "reading destination appeared")
            from constructive_alpha_v34_publication_process import _rename_new
            _rename_new(candidate, output)
    return dict(files=len(files) + len(additions), pages=len(records), families=audit["family_count"],
        curated_pages=audit["curated_pages"], large_defined_claims=audit["large_defined_claims"],
        previous_large_defined_claims=audit["previous_large_defined_claims"],
        compacted_defined_claims=audit["compacted_defined_claims"],
        check_only=check, manifest_sha256=sha256(additions[MANIFEST]).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=ROOT / "_deploy/proofs-public-v1")
    parser.add_argument("--output", type=Path, default=ROOT / "_deploy/proofs-readable-v1")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    started = time.monotonic()
    result = stage(args.base, args.output, check=args.check)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = int(rss if sys.platform == "darwin" else rss * 1024)
    require(0 < rss <= MAX_RSS and time.monotonic() - started < WALL_SECONDS, "reading stage resource limit exceeded")
    print(json.dumps(dict(result, seconds=time.monotonic() - started, peak_rss_bytes=rss), sort_keys=True))


if __name__ == "__main__":
    main()
