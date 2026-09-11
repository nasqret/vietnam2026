"""Jordan/atlas publication authorized only by a genuine same-live v35 audit.

Legacy readers remain the immutable September readable/layout publication.
New syntax and HTML sources are bound independently from mathematical proof
authority; neither a receipt nor a lookalike context can publish a theorem.
"""
from hashlib import sha256
from pathlib import Path

import constructive_completed_lower_publication_v31 as original

ROOT = Path(__file__).resolve().parents[1]
PublicationError = original.PublicationError
digest, json_bytes, strict_json = original.digest, original.json_bytes, original.strict_json
safe_relative, read_pinned = original.safe_relative, original.read_pinned
OUTPUT_NAMES = {"jordan": "constructive-jordan-explorer-v35", "atlas": "constructive-jordan-campaign-v35"}
_RENDER_TOKEN = object()


def require_live(context):
    kind = type(context)
    if kind is not BoundPresentation and (kind.__module__, kind.__name__) != (
            "verify_peano_library_channels_v35", "LiveReleaseContext"):
        raise PublicationError("only a genuine live v35 release can authorize publication")
    from verify_peano_library_channels_v35 import LiveReleaseContext
    if type(context) not in (LiveReleaseContext, BoundPresentation):
        raise PublicationError("foreign release capability")
    context.require_unchanged()
    rows = context.catalog.get("theorems")
    if (type(rows) is not list or len(rows) != 4318
            or context.catalog.get("checked_use_count") != 4318
            or context.catalog.get("stable_count") != 432
            or len(context.promoted_names) != 95
            or tuple(row["name"] for row in rows[4223:]) != context.promoted_names
            or tuple(context.families) != ("jordan-totient",)
            or context.channels.get("default_channel") != "stable"
            or context.revision != context.catalog_sha256[:12]
            or context.channels["channels"]["alpha"]["artifact_sha256"] != context.catalog_sha256):
        raise PublicationError("live release differs from exact4223+95 Jordan admission")


def require_render_inputs():
    from check_alpha_v35_jordan import _file_digest
    paths = (
        "scripts/constructive_jordan_publication_v35.py",
        "scripts/constructive_alpha_v35_publication_process.py",
        "scripts/publish_constructive_jordan_v35.py",
        "scripts/test_publish_constructive_jordan_v35.py",
        "scripts/build_constructive_jordan_explorer_v35.py",
        "scripts/constructive_jordan_definitions_v35.py",
        "scripts/extend_constructive_jordan_campaign_v35.py",
        "scripts/stage_constructive_jordan_publication_v35.py",
        "scripts/test_constructive_jordan_explorer_v35.py",
        "scripts/test_constructive_jordan_live_ids_v35.py",
        "scripts/stage_proof_explorer_layout.py",
        "scripts/proof_explorer_layout.py",
        "scripts/stage_proof_readability.py",
        "scripts/proof_readability.py",
        "scripts/proof_reading_definitions.py",
        "deploy/proofs/proof-reader.css",
        "deploy/proofs/proof-reader.js",
        "deploy/proofs/proof-reader-notes.json",
        "deploy/proofs/lean-selector-disabled.js",
        "book/_static/constructive-historical-explorers-v34/integer-linear-algebra/explorer/defined/tag/DL0071.html",
        "peano-lab/py/tests/test_constructive_jordan_publication_v35.py",
    )
    records = [(path, *_file_digest(path, 4 * 1024 * 1024)) for path in paths]
    # Bind all transitive historical renderer/definition sources with their
    # original checks. This does not accept any historical release capability.
    import constructive_research_publication_v34 as previous
    records.append(("inherited_presentation_sources", previous.require_render_inputs()))
    from extend_constructive_jordan_campaign_v35 import parent_files
    for name, raw in sorted(parent_files().items()):
        records.append(("parent_atlas/" + name, len(raw), sha256(raw).hexdigest()))
    return digest(json_bytes(records))


class BoundPresentation:
    __slots__ = ("_token", "_release", "render_source_binding_sha256")

    def __init__(self, token, context, binding):
        if token is not _RENDER_TOKEN:
            raise PublicationError("stored metadata cannot mint a presentation capability")
        self._token, self._release, self.render_source_binding_sha256 = token, context, binding

    def __getattr__(self, name):
        return getattr(self._release, name)

    def require_unchanged(self):
        if self._token is not _RENDER_TOKEN:
            raise PublicationError("foreign presentation capability")
        self._release.require_unchanged()
        if require_render_inputs() != self.render_source_binding_sha256:
            raise PublicationError("presentation source changed after binding")


def bind_live_context(context):
    require_live(context)
    from verify_peano_library_channels_v35 import LiveReleaseContext
    if type(context) is not LiveReleaseContext:
        raise PublicationError("binding requires the original live release capability")
    return BoundPresentation(_RENDER_TOKEN, context, require_render_inputs())


def iter_phase_entries(context, phase):
    require_live(context)
    if phase == "jordan":
        from build_constructive_jordan_explorer_v35 import build_files_from_live
    elif phase == "atlas":
        from extend_constructive_jordan_campaign_v35 import build_files_from_live
    else:
        raise PublicationError("unknown Jordan publication phase")
    yield from build_files_from_live(context).items()
    require_live(context)
