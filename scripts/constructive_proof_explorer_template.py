#!/usr/bin/env python3
"""Canonical Quadratic Reciprocity-style landing pages for proof campaigns.

The renderer owns presentation only. The caller must first authenticate every
theorem, conservative definition, current release, and independent proof
certificate; page generation never grants checked-use authority.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
import re
from typing import Any, Protocol


_SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
_REVISION = re.compile(r"[a-f0-9]{12}")
_VERSION = re.compile(r"v[1-9][0-9]*")
_DOMAIN = re.compile(r"D[0-9]{2}")
_FAMILY = re.compile(r"F[0-9]{2}")
_MILESTONE = re.compile(r"(?:G[0-9]{3}|T[0-9]{2}|A[0-9]{2})")
_TAG = re.compile(r"[A-Z]{2}[A-Z0-9]{4}")
_SHA256 = re.compile(r"[a-f0-9]{64}")
_DEFAULT_ORIGIN = "https://bnaskrecki.faculty.wmi.amu.edu.pl"


class ProofExplorerTemplateError(ValueError):
    """The requested family does not satisfy the canonical landing contract."""


class _Family(Protocol):
    slug: str
    title: str
    kicker: str
    description: str
    formula: str
    domain: str
    family_id: str
    milestones: Sequence[str]
    roots: Sequence[str]
    caveat: str


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProofExplorerTemplateError(f"the proof family has no valid {name}")
    return value


def _number(corpus: Mapping[str, Any], key: str, *, positive: bool = False) -> int:
    value = corpus.get(key)
    if type(value) is not int or value < int(positive):
        raise ProofExplorerTemplateError(f"the proof family has an invalid {key}")
    return value


def _html(value: object) -> str:
    return escape(str(value), quote=True)


def _href(path: str, revision: str) -> str:
    separator = "&" if "?" in path else "?"
    return _html(f"{path}{separator}v={revision}")


def render_canonical_family_landing(
    family: _Family,
    corpus: Mapping[str, Any],
    *,
    revision: str,
    current_alpha_version: str,
    first_admitted_version: str,
    bundle_node_count: int,
    canonical_origin: str = _DEFAULT_ORIGIN,
) -> bytes:
    """Render the actual established Quadratic Reciprocity family experience."""

    slug = _text(family.slug, name="slug")
    if _SLUG.fullmatch(slug) is None:
        raise ProofExplorerTemplateError("the proof family has an unsafe URL slug")
    if _REVISION.fullmatch(revision) is None:
        raise ProofExplorerTemplateError("the sealed catalog revision is not 12 hexadecimal digits")
    if _VERSION.fullmatch(current_alpha_version) is None:
        raise ProofExplorerTemplateError("the current Alpha version is invalid")
    if _VERSION.fullmatch(first_admitted_version) is None:
        raise ProofExplorerTemplateError("the first-admission Alpha version is invalid")
    if _DOMAIN.fullmatch(family.domain) is None or _FAMILY.fullmatch(family.family_id) is None:
        raise ProofExplorerTemplateError("the proof family has invalid campaign coordinates")
    if type(bundle_node_count) is not int or bundle_node_count <= 0:
        raise ProofExplorerTemplateError("the independently checked bundle has no nodes")
    if not canonical_origin.startswith("https://") or canonical_origin.endswith("/"):
        raise ProofExplorerTemplateError("the canonical publication origin is invalid")

    milestones = tuple(family.milestones)
    roots = tuple(family.roots)
    if not milestones or any(_MILESTONE.fullmatch(value) is None for value in milestones):
        raise ProofExplorerTemplateError("the proof family has no exact campaign milestone")
    if not roots or len(set(roots)) != len(roots):
        raise ProofExplorerTemplateError("the proof family has no distinct checked theorem roots")
    tags = corpus.get("tags")
    if not isinstance(tags, Mapping):
        raise ProofExplorerTemplateError("the proof family has no authenticated theorem tags")
    for name in roots:
        tag = tags.get(name)
        if not isinstance(tag, str) or _TAG.fullmatch(tag) is None:
            raise ProofExplorerTemplateError(f"the proof family root has no stable tag: {name!r}")

    theorem_count = _number(corpus, "node_count", positive=True)
    checked_count = _number(corpus, "alpha_checked_use_node_count", positive=True)
    if checked_count != theorem_count:
        raise ProofExplorerTemplateError("the canonical checked-use landing contains an unverified theorem")
    definition_count = _number(corpus, "definition_count")
    definition_edges = _number(corpus, "definition_dependency_count")
    proof_edges = _number(corpus, "edge_count")
    tactic_lines = _number(corpus, "formal_line_count")
    bundle_sha256 = corpus.get("alpha_proof_bundle_sha256")
    if not isinstance(bundle_sha256, str) or _SHA256.fullmatch(bundle_sha256) is None:
        raise ProofExplorerTemplateError("the independently checked proof bundle has no SHA-256")
    if corpus.get("independent_lean_bundle_verified") is not True:
        raise ProofExplorerTemplateError("the proof family lacks independent Lean evidence")

    title = _html(_text(family.title, name="title"))
    description = _html(_text(family.description, name="description"))
    kicker = _html(_text(family.kicker, name="mathematical classification"))
    formula = _html(_text(family.formula, name="mathematical formula"))
    caveat = _html(_text(family.caveat, name="mathematical evidence boundary"))
    root_name = roots[-1]
    root_tag = str(tags[root_name])
    goal = milestones[-1]

    graph = _href(
        f"explorer/defined/graph.html?target={root_tag}"
        "&view=neighborhood&definitions=selected&edges=focus",
        revision,
    )
    visible_graph = _href(
        f"explorer/defined/graph.html?target={root_tag}"
        "&view=neighborhood&definitions=visible&edges=focus",
        revision,
    )
    prerequisite_graph = _href(
        f"explorer/defined/graph.html?target={root_tag}"
        "&view=prerequisites&definitions=selected&edges=focus",
        revision,
    )
    atlas = _href("../grand-campaign/", revision)
    domain_atlas = _href(
        f"../grand-campaign/?view=domain&focus={family.domain}", revision
    )
    family_atlas = _href(
        f"../grand-campaign/?view=family&focus={family.family_id}", revision
    )
    goal_atlas = _href(f"../grand-campaign/?view=goal&focus={goal}", revision)
    goal_links = " · ".join(
        f'<a data-campaign-link="goal" data-campaign-goal="{_html(milestone)}" '
        f'href="{_href(f"../grand-campaign/?view=goal&focus={milestone}", revision)}">'
        f"{_html(milestone)} milestone</a>"
        for milestone in milestones
    )
    roots_html = " · ".join(
        f'<a href="{_href(f"explorer/defined/tag/{tags[name]}.html", revision)}">'
        f"<code>{_html(tags[name])}</code> {_html(name)}</a>"
        for name in roots
    )
    canonical_url = f"{canonical_origin}/proofs/{slug}/"

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Proof Explorer</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{title} — Proof Explorer">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{_html(canonical_origin)}/proofs/assets/proofs-og.png">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{_html(canonical_url)}">
  <link rel="canonical" href="{_html(canonical_url)}">
  <link rel="stylesheet" href="{_href('../assets/proofs.css', revision)}">
</head>
<body class="family-page {_html(slug)}-page">
  <header class="family-hero">
    <div class="shell">
      <nav class="crumbs"><a href="{_href('../', revision)}">Proof explorers</a><span>/</span><a data-campaign-link="global" href="{atlas}">Grand campaign</a><span>/</span><a data-campaign-link="family" href="{family_atlas}">Family atlas</a><span>/</span><span>{title}</span></nav>
      <p class="eyebrow">{kicker} · Constructive arithmetic</p>
      <h1>{title}</h1>
      <p class="formula">{formula}</p>
      <p class="lede">{description}</p>
      <div class="hero-actions">
        <a class="primary-action" href="{graph}">Open the definition-aware map</a>
        <a class="secondary-action" href="{_href(f'explorer/defined/tag/{root_tag}.html', revision)}">Read the final theorem</a>
        <a class="secondary-action" data-campaign-link="milestone" href="{goal_atlas}">See campaign milestone {_html(goal)}</a>
      </div>
    </div>
  </header>
  <main class="shell family-main">
    <section class="view-grid">
      <article class="view-card featured">
        <p class="card-kicker">Recommended</p>
        <h2>Defined mathematical notation</h2>
        <p>Browse {definition_count} linked conservative definitions and {theorem_count} independently checked theorems without losing their exact first-order expansions.</p>
        <a href="{_href('explorer/defined/', revision)}">Browse definitions and theorems →</a>
        <p><a href="{visible_graph}">Inspect the local definition DAG →</a></p>
      </article>
      <article class="view-card">
        <p class="card-kicker">Exact certificate</p>
        <h2>Fully expanded arithmetic</h2>
        <p>Inspect all {tactic_lines} native tactic lines and {proof_edges} actual proof prerequisites with every definition fully expanded.</p>
        <a href="{_href('explorer/', revision)}">Open the exact edition →</a>
      </article>
      <article class="view-card">
        <p class="card-kicker">Focused route</p>
        <h2>Final dependency cone</h2>
        <p>Start at theorem <code>{_html(root_tag)}</code> and follow only the lemmas and conservative definitions supporting {_html(root_name)}.</p>
        <a href="{prerequisite_graph}">Trace prerequisites →</a>
      </article>
    </section>
    <section class="release-note"><strong>Zoom between mathematical scales:</strong> <a data-campaign-link="global" href="{atlas}">complete research atlas</a> → <a data-campaign-link="domain" href="{domain_atlas}">research domain</a> → <a data-campaign-link="family" href="{family_atlas}">proof family</a> → {goal_links} → <a href="{visible_graph}">theorem and definition dependencies</a>.</section>
    <section class="release-note"><strong>Major independently established statements:</strong> {roots_html}.</section>
    <section class="release-note"><strong>Independently verified Alpha {_html(current_alpha_version)} checked-use theorem family:</strong> {theorem_count} dependency-curried kernel-checked theorem bodies · {proof_edges} proof prerequisites · {definition_count} linked definitions · {definition_edges} definition-dependency arrows · {tactic_lines} exact tactic lines · first admitted {_html(first_admitted_version)} · not Stable. The unchanged intuitionistic kernel and separately compiled Lean verifier independently accept all {bundle_node_count} bundle nodes; SHA-256 <code>{_html(bundle_sha256)}</code>.</section>
    <section class="release-note"><strong>Exact mathematical boundary:</strong> {caveat}</section>
  </main>
</body>
</html>
"""
    return page.encode("utf-8")
