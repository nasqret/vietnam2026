"""No-clobber Jordan overlay on the exact Sept5 public reading release.

The original layout repair, reading layer and disabled public Lean selector
remain byte-identical. Only the hub and current atlas replace existing paths;
old theorem pages, artifacts and historical manifests remain unchanged.
"""
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
from tempfile import TemporaryDirectory

from stage_proof_explorer_layout import canonical, inventory, ordinary, pin, read, require
from proof_explorer_layout import repair_release_notices
from proof_readability import enhance_page, strip_reading_layer
from proof_reading_definitions import ReadingDefinitions
from stage_proof_readability import ASSETS, NOTES, asset_prefix, reading_audit, render_audit

ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST = "presentation/readability-v1.json"
BASE_SHA256 = "10471f7ace1719110af485479052a87dca4cda5a410515d556ebce5473adefc9"
MANIFEST = "release-v35/manifest.json"
READING_AUDIT = "reading/jordan-v35-audit.json"
READING_HTML = "reading/jordan-v35.html"
REPLACEMENTS = frozenset(("index.html", "grand-campaign/campaign.json", "grand-campaign/definitions.json",
                         "grand-campaign/dag-audit.json", "grand-campaign/index.html"))


def validate_base(base, files):
    raw = read(base / BASE_MANIFEST)
    require(pin(raw)["sha256"] == BASE_SHA256, "the exact Sept5 readable parent is required")
    record = json.loads(raw)
    require(record.get("schema") == "peano-proof-readability-stage-v1"
        and record.get("proof_bytes_changed") is False and record.get("native_scripts_changed") is False
        and record.get("public_on_demand_builds") is False and record.get("original_assets_changed") is False,
        "the parent lost the approved public reading policy")
    restored = dict(files)
    require(restored.pop(BASE_MANIFEST) == pin(raw), "parent manifest differs from inventory")
    for name, expected in record["additions"].items():
        require(restored.pop(name, None) == expected, "an inherited reading asset or audit changed")
    for name, change in record["changed_files"].items():
        require(restored.get(name) == change["after"], "an inherited readable proof changed")
        restored[name] = change["before"]
    require(len(restored) == record["base_file_count"]
        and sha256(canonical(restored)).hexdigest() == record["base_inventory_sha256"],
        "the exact inherited proof/asset inventory differs")
    require(len(files) == 13556 and MANIFEST not in files
        and not any(name.startswith("jordan-totient/") for name in files),
        "the exact baseline already contains a foreign Jordan overlay")
    for name, source in ASSETS.items():
        require(files.get(name) == pin(read(ROOT / source)), "the approved reading asset changed")
    require(files.get("assets/lean-selector.js") == pin(read(ROOT / "deploy/proofs/lean-selector-disabled.js")),
            "public on-demand Lean builds were re-enabled")
    from constructive_checked_explorer_renderer import ASSET_DIGESTS
    for name, digest in ASSET_DIGESTS.items():
        require(files.get("assets/" + name, {}).get("sha256") == digest,
                "a canonical Quadratic Reciprocity graph asset changed")
    return record


def render_public_hub(parent, context, definition_edges):
    """Keep all68 historical cards, add one canonical Jordan card."""
    from build_constructive_research_hub_v34 import _Inventory, FAMILY_ROUTES
    text = parent.decode()
    before = _Inventory(text)
    require(len(before.cards) == 68 and 'content="alpha-v34-checked-use"' in text,
            "the historical68-family hub changed")
    # The scoped parent input was authenticated by validate_base; current
    # navigation revisions may change without touching first-admission text.
    current = re.search(r'assets/proofs\.css\?v=([a-f0-9]{12})', text)
    require(current is not None, "the canonical hub stylesheet revision is missing")
    result = text.replace(current.group(1), context.revision)
    result = result.replace('content="alpha-v34-checked-use"', 'content="alpha-v35-checked-use"')
    result = result.replace('data-current-alpha="v34"', 'data-current-alpha="v35"')
    result = result.replace("Alpha v34 checked use", "Alpha v35 checked use")
    result = result.replace("remain checked use in Alpha v34.", "remain checked use in Alpha v35.")
    result = result.replace("remain available in Alpha v34.", "remain available in Alpha v35.")
    pairs = (
        ("Alpha v34 has 4,223 checked-use entries.", "Alpha v35 has 4,318 checked-use entries."),
        ("Alpha v34 has 4,223 checked-use entries: 432 unchanged Stable theorems and 3,791 additional Alpha-closed theorems.",
         "Alpha v35 has 4,318 checked-use entries: 432 unchanged Stable theorems and 3,886 additional Alpha-closed theorems."),
        ("407 reviewed conservative definitions with 884 actual expansion arrows, and 13,816 theorem dependencies.",
         f"418 reviewed conservative definitions with {definition_edges:,} actual expansion arrows, and {context.catalog['edge_count']:,} theorem dependencies."),
        ("The 131 first admissions in v34 extend the 4,092-entry v33 parent without rewriting historical evidence.",
         "The 95 first admissions in v35 extend the 4,223-entry v34 parent without rewriting historical evidence."),
        ("The current library contains 68 proof families.", "The current library contains 69 proof families."),
        ('<p class="eyebrow">Current Alpha v34 release</p>', '<p class="eyebrow">First admitted in Alpha v34</p>'),
        ("131 newly admitted results extend Alpha to 4,223 checked-use entries.",
         "The v34 release added131 results to reach4,223 checked-use entries; those admissions remain available in Alpha v35."),
        ("Current v34 public-delivery inventory", "Historical v34 public-delivery inventory"),
        ('aria-label="New Alpha v34 proof families"', 'aria-label="Proof families first admitted in Alpha v34"'),
    )
    for old, new in pairs:
        require(result.count(old) == 1, "the canonical hub extension point changed: " + old)
        result = result.replace(old, new, 1)
    marker = '    <section class="frontier-intro" aria-labelledby="research-v34-heading"'
    require(result.count(marker) == 1, "the v34 historical hub section changed")
    section = f'''    <section class="frontier-intro" aria-labelledby="research-v35-heading" data-current-alpha="v35">
      <p class="eyebrow">Current Alpha v35 release</p>
      <h2 id="research-v35-heading">Jordan totients: count, compare, multiply.</h2>
      <p>95 novel admissions extend Alpha to 4,318 checked-use entries. The 96 original source lemmas include one inherited tuple-equality alias, not counted twice. Stable remains the unchanged432-theorem default.</p>
      <p class="candidate-disclaimer">G008 multiplicativity is proved using actual finite primitive-tuple enumerations and canonical tuple CRT. General prime-power counts and the distinct-prime product formula are further goals; G091 remains open.</p>
    </section>
    <section class="family-grid frontier-grid" aria-label="New Alpha v35 proof family">
      <article class="family-card candidate-card" data-alpha-first="v35" id="jordan-totient-card">
        <p class="card-kicker">Alpha v35 checked use · 95 independently proved theorems</p>
        <h2>Jordan Totients and Primitive Tuples</h2>
        <p>Follow finite tuple enumeration, CRT, uniqueness of counts and coprime multiplicativity. The unit modulus and prime-power primitivity are handled explicitly.</p>
        <p>Eleven exact conservative definitions share the existing tuple-equality meaning. Syntax arrows are not proof assumptions.</p>
        <p class="candidate-badge">G008 multiplicativity proved; prime-power count and product formula remain open</p>
        <a class="primary-action" href="jordan-totient/?v={context.revision}">Explore the proof map <span aria-hidden="true">→</span></a>
        <p>Same-byte original HA and compiled Lean checks of359 bundle nodes; seven ordinary roots. First admitted v35; not Stable.</p>
        <p><a href="grand-campaign/?view=goal&amp;focus=G008&amp;v={context.revision}">G008 in the campaign atlas</a> · <a href="reading/jordan-v35.html">Reading coverage</a> · <a href="release-v35/manifest.json">Current delivery inventory</a></p>
      </article>
    </section>
'''
    result = result.replace(marker, section + marker, 1)
    after = _Inventory(result)
    require(len(after.cards) == 69 and set(href.split("/", 1)[0] for href in after.cards) == set(FAMILY_ROUTES) | {"jordan-totient"}
        and after.ids == before.ids | {"research-v35-heading", "jordan-totient-card"},
        "a historical hub card or anchor was lost")
    return result.encode()


def _reading_layer(files):
    result = dict(files)
    records = {}
    corpus_path = "jordan-totient/api/corpus.json"
    corpus = json.loads(files[corpus_path])
    definitions = ReadingDefinitions(corpus["definitions"], dict(path=corpus_path, **pin(files[corpus_path])))
    revision = sha256(b"".join(read(ROOT / source) for source in ASSETS.values())).hexdigest()[:12]
    notes = json.loads(read(ROOT / NOTES))
    repaired = {name: repair_release_notices(raw)[0] if name.endswith(".html") else raw
                for name, raw in files.items()}
    for name, raw in repaired.items():
        if not name.endswith(".html"):
            continue
        exact_name, exact_raw, exact_href = name, None, None
        if b'class="pd-formal-proof"' in raw:
            exact_name = name.replace("/explorer/defined/tag/", "/explorer/tag/", 1)
            require(exact_name != name and exact_name in repaired, "a Jordan defined page lacks its exact source")
            exact_raw = repaired[exact_name]
            exact_href = posixpath.relpath(exact_name, str(PurePosixPath(name).parent))
        revised, report = enhance_page(raw, assets_prefix=asset_prefix(name), revision=revision,
            notes=notes, exact_raw=exact_raw, exact_href=exact_href, definitions=definitions)
        result[name] = revised
        if report is not None:
            require(strip_reading_layer(revised) == raw, "the original exact Jordan page cannot be recovered")
            report["exact_source_path"] = exact_name
            records[name] = dict(report, historical_checkpoint=False)
    require(len(records) == 190 and sum(row["edition"] == "defined" for row in records.values()) == 95,
            "Jordan reading coverage is not95 paired exact/defined pages")
    for row in records.values():
        if row["edition"] == "defined":
            exact = records[row["exact_source_path"]]
            require(exact["edition"] == "exact" and exact["theorem"] == row["theorem"]
                and exact["script_sha256"] == row["script_sha256"], "paired Jordan scripts differ")
    audit = reading_audit(records, {"jordan-totient": definitions.report})
    result[READING_AUDIT] = canonical(audit)
    result[READING_HTML] = render_audit(audit).replace(b'href="audit.json"', b'href="jordan-v35-audit.json"')
    return result, audit


def stage(context, base, output, *, check=False):
    publication = import_module("constructive_jordan_publication_v35")
    publication.require_live(context)
    base, output = Path(base).absolute(), Path(output).absolute()
    ordinary(base, directory=True)
    ordinary(output.parent, directory=True)
    require(base != output and base not in output.parents and output not in base.parents,
            "Jordan staging input and output overlap")
    require(check or not output.exists() and not output.is_symlink(), "Jordan stage must not overwrite an existing destination")
    parents = inventory(base)
    validate_base(base, parents)
    from build_constructive_jordan_explorer_v35 import build_files_from_live as build_reader
    from extend_constructive_jordan_campaign_v35 import build_files_from_live as build_atlas
    reader = build_reader(context)
    atlas = build_atlas(context, reader_files=reader)
    files, audit = _reading_layer(reader)
    for name in tuple(files):
        if name.startswith("assets/"):
            require(parents.get(name) == pin(files[name]), "a standalone-reader shared asset differs from the public parent")
            del files[name]
    files.update({"grand-campaign/" + name: raw for name, raw in atlas.items()})
    # The inherited atlas uses canonical package URLs in source snapshots;
    # its public home link is made relative by the established delivery step.
    files["grand-campaign/index.html"] = files["grand-campaign/index.html"].replace(
        b"../constructive-research-explorer-v34/index.html", b"../index.html")
    edges = json.loads(atlas["definitions.json"])["reviewed_definition_edge_count"]
    files["index.html"] = render_public_hub(read(base / "index.html"), context, edges)
    require(set(files) & set(parents) == REPLACEMENTS, "Jordan overlay attempted an unapproved historical overwrite")
    require(not any(name.startswith("assets/") for name in files), "Jordan overlay attempted to alter shared assets")
    final = dict(parents)
    final.update({name: pin(raw) for name, raw in files.items()})
    manifest = dict(schema="peano-lab-alpha-v35-public-delivery-v1", delivery_metadata_only=True,
        alpha_admission_performed=False, stable_admission_performed=False, public_on_demand_builds=False,
        current_alpha_version="v35", current_alpha_checked_use_count=4318, stable_count=432,
        new_theorem_count=95, source_owned_theorem_count=96, source_alias_count=1, family_count=69,
        current_G008_proved=True, current_G091_proved=False, distinct_prime_product_formula_proved=False,
        catalog_sha256=context.catalog_sha256, source_binding_sha256=context.source_binding_sha256,
        parent_manifest=dict(path=BASE_MANIFEST, sha256=BASE_SHA256),
        parent_file_count=len(parents), parent_inventory_sha256=sha256(canonical(parents)).hexdigest(),
        preserved_file_count=len(set(parents) - REPLACEMENTS),
        changed_files={name: dict(before=parents[name], after=final[name]) for name in sorted(REPLACEMENTS)},
        additions={name: final[name] for name in sorted(set(files) - set(parents))},
        current_files=final, current_file_count=len(final), jordan_reading_pages=audit["pages"],
        proof_verification_provenance="genuine_same_live_v35_admission; never_stored_observations")
    files[MANIFEST] = canonical(manifest)
    expected = dict(final, **{MANIFEST: pin(files[MANIFEST])})

    def verify(directory):
        require(inventory(directory) == expected, "the complete staged Jordan inventory differs")
        require(inventory(base) == parents, "the preserved readable parent changed during staging")
        publication.require_live(context)

    if check:
        verify(output)
    else:
        with TemporaryDirectory(prefix=".jordan-v35-", dir=output.parent) as temporary:
            candidate = Path(temporary) / "files"
            candidate.mkdir(mode=0o755)
            for name in sorted(expected):
                raw = files[name] if name in files else read(base / name)
                require(pin(raw) == expected[name], "an input changed while copying the exact overlay")
                path = candidate / name
                path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(raw)
                path.chmod(0o644)
            verify(candidate)
            from constructive_alpha_v34_publication_process import _rename_new
            _rename_new(candidate, output)
    return dict(files=len(expected), families=69, new_theorems=95, source_lemmas=96,
        reading_pages=190, manifest_sha256=pin(files[MANIFEST])["sha256"], check_only=check)
