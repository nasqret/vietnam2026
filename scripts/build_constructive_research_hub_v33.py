#!/usr/bin/env python3
"""Pure current-v33 hub over the exact85,047-byte v32 public hub.

No catalogue/receipt loading, proof replay, or file-writing entrypoint exists.
The delivery stager must authenticate the completed live release separately.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import re
from urllib.parse import urlsplit

import build_constructive_research_hub_v32 as previous

PARENT_HUB_BYTES = 85047
PARENT_HUB_SHA256 = "307611d61cf2deabd021f50f920f305368aadfc040f7ceb0e78c66806ed20a36"
PARENT_REVISION = "41b9f387d88a"
MAX_HUB_BYTES = previous.MAX_HUB_BYTES
PARENT_FAMILY_ROUTES = previous.FAMILY_ROUTES
FAMILY_ROUTES = (*PARENT_FAMILY_ROUTES[:2], "polynomial-euclidean-division", *PARENT_FAMILY_ROUTES[2:])
HubError, _Inventory, _once = previous.HubError, previous._Inventory, previous._once
_OLD_DIVISION = ("General division by an arbitrary nonzero polynomial, polynomial gcd/Bézout, "
    "irreducible-polynomial existence in every positive degree and general prime-power fields remain open in this release.")
_NEW_DIVISION = ("General division by an arbitrary nonzero polynomial is now admitted in the separate "
    "polynomial-euclidean-division family. Polynomial associativity, gcd/Bézout, irreducible-polynomial "
    "existence in every positive degree and general prime-power fields remain open.")
_CURRENT_PROSE = (
    ('content="alpha-v32-checked-use"', 'content="alpha-v33-checked-use"'),
    ('aria-labelledby="research-v32-heading" data-current-alpha="v32">',
     'aria-labelledby="research-v32-heading" data-current-alpha="v33" data-alpha-first="v32">'),
    ('<p class="eyebrow">Current Alpha v32 release</p>',
     '<p class="eyebrow">First admitted in Alpha v32</p>'),
    ("Two new chapters, 175 first admissions.", "Two chapters, 175 proofs first admitted in v32."),
    ("Alpha v32 extends the unchanged 3,796-entry v31 parent to 3,971 checked-use entries. The 90 multiplicative-convolution results and 85 polynomial-division prerequisites now have current Alpha checked use. Stable remains the separate, unchanged 432-theorem default library; the 3,539 additional Alpha-closed entries are not Stable admissions.",
     "The v32 release added 90 multiplicative-convolution results and 85 polynomial-division prerequisites to its 3,796-entry v31 parent. These 175 first admissions remain checked use in Alpha v33. Stable remains the separate, unchanged 432-theorem default library."),
    ('aria-label="New Alpha v32 proof families"', 'aria-label="Proof families first admitted in Alpha v32"'),
    ('data-current-alpha="v32" data-alpha-first="v31"', 'data-current-alpha="v33" data-alpha-first="v31"'),
    ("were first admitted in Alpha v31 and remain checked use in Alpha v32.",
     "were first admitted in Alpha v31 and remain checked use in Alpha v33."),
    ("Alpha v32 has 3,971 checked-use entries. Stable remains",
     "Alpha v33 has 4,092 checked-use entries. Stable remains"),
    ("390 reviewed conservative definitions with 844 actual expansion arrows, and 12,751 theorem dependencies.",
     "397 reviewed conservative definitions with 865 actual expansion arrows, and 13,212 theorem dependencies."),
    ("Alpha v32 has 3,971 checked-use entries: 432 unchanged Stable theorems and 3,539 additional Alpha-closed theorems.",
     "Alpha v33 has 4,092 checked-use entries: 432 unchanged Stable theorems and 3,660 additional Alpha-closed theorems."),
    ("The 175 first admissions in v32 extend the 3,796-entry v31 parent without rewriting historical evidence.",
     "The 121 first admissions in v33 extend the 3,971-entry v32 parent without rewriting historical evidence."),
    ("The current library contains 65 proof families.", "The current library contains 66 proof families."),
    ("Current v32 public-delivery inventory", "Historical v32 public-delivery inventory"),
)


def _legacy_card(card, revision):
    return (card.replace(PARENT_REVISION, revision)
            .replace("Alpha v32 checked use", "Alpha v33 checked use")
            .replace(_OLD_DIVISION, _NEW_DIVISION))


def _new_section(revision):
    return f'''    <section class="frontier-intro" aria-labelledby="research-v33-heading" data-current-alpha="v33">
      <p class="eyebrow">Current Alpha v33 release</p>
      <h2 id="research-v33-heading">General polynomial division, with representation-independent operations.</h2>
      <p>121 newly admitted results extend Alpha to 4,092 checked-use entries. Stable remains the unchanged 432-theorem default. The actual 377-node artifact has fresh original HA and same-byte compiled Lean verification, with eight independently replayed ordinary HA principal certificates.</p>
      <p class="candidate-disclaimer">General Euclidean execution, its coefficient identity, remainder-degree bound and execution uniqueness are proved. The separate shift/scalar → associativity → gcd/Bézout campaign continues; full G091 remains open. Neither raw beta-code equality nor equality of evaluations replaces formal coefficient equivalence.</p>
      <p><a href="grand-campaign/?view=goal&amp;focus=G091&amp;v={revision}">G091: division accomplished, associativity and gcd/Bézout next</a></p>
    </section>
    <section class="family-grid frontier-grid" aria-label="New Alpha v33 proof family">
      <article class="family-card candidate-card polynomial-card" data-alpha-first="v33" id="polynomial-euclidean-division-card">
        <p class="card-kicker">Alpha v33 checked use · 121 independently proved theorems</p>
        <h2>Prime-Field Polynomial Euclidean Division</h2>
        <p>Construct actual triangular quotient executions for every canonical nonzero divisor, form the residual, trim its leading zeros and prove the coefficient identity and strict remainder bound. Decoded execution uniqueness and formal coefficient equivalence handle different beta encodings and representation lengths.</p>
        <p>Seven conservative definitions organize quotient steps, execution, left padding and formal equivalence. Addition, subtraction and convolution respect representation equivalence, including empty and leading-zero cases.</p>
        <p class="candidate-badge">General division proved · associativity and gcd/Bézout remain open; not Stable</p>
        <a class="primary-action" href="polynomial-euclidean-division/?v={revision}">Explore the proof map <span aria-hidden="true">→</span></a>
        <p>Original HA and compiled Lean verification · first admitted v33 · not Stable.</p>
        <p>Uniqueness concerns actual executions on the same annotated input; arbitrary formal-identity quotient/remainder uniqueness is a later theorem. No degree is assigned to the zero polynomial.</p>
        <p>Campaign connections: <a href="polynomial-division-prerequisites/?v={revision}">Division prerequisites</a> · <a href="polynomial-products/?v={revision}">Convolution and degree</a> · <a href="grand-campaign/?view=goal&amp;focus=G091&amp;v={revision}">G091</a></p>
      </article>
    </section>
'''


def _validate_projection(parent, result, revision):
    before, after = _Inventory(parent), _Inventory(result)
    if tuple(before.cards) != tuple(slug + "/?v=" + PARENT_REVISION for slug in PARENT_FAMILY_ROUTES):
        raise HubError("the exact65 inherited hub entrances changed")
    if tuple(after.cards) != tuple(slug + "/?v=" + revision for slug in FAMILY_ROUTES):
        raise HubError("the exact66 current hub entrances changed")
    if before.scopes != ["alpha-v32-checked-use"] or after.scopes != ["alpha-v33-checked-use"]:
        raise HubError("current display scope changed")
    if after.ids != before.ids | {"research-v33-heading", "polynomial-euclidean-division-card"}:
        raise HubError("historical hub anchors were removed, renamed or shadowed")
    old_cards, new_cards = previous._ARTICLE.findall(parent), previous._ARTICLE.findall(result)
    retained = (*new_cards[:2], *new_cards[3:])
    if len(old_cards) != 65 or len(new_cards) != 66 or tuple(retained) != tuple(_legacy_card(card, revision) for card in old_cards):
        raise HubError("a prior card or first-admission identity changed")
    if result.count(_new_section(revision)) != 1:
        raise HubError("the new family has a different exact boundary")
    def history(document):
        return Counter(url for _, _, url in document.links
                       if urlsplit(url).path.startswith(("artifacts/", "checkpoints/", "release-v31/", "release-v32/")))
    if history(before) != history(after):
        raise HubError("a historical artifact destination changed")
    styles = [url for tag, field, url in after.links if tag == "link" and field == "href" and urlsplit(url).path.endswith(".css")]
    if styles != ["assets/proofs.css?v=" + revision]:
        raise HubError("original Quadratic Reciprocity stylesheet changed")
    for _, _, href in after.links:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc or parsed.path.startswith(("artifacts/", "checkpoints/", "release-v31/", "release-v32/", "release-v33/")):
            continue
        if parsed.path.endswith(("/", ".html")) and parsed.query.split("&")[-1] != "v=" + revision:
            raise HubError("a current hub route has a stale revision")
    for phrase in ("4,092 checked-use entries", "3,660 additional Alpha-closed",
                   "432 unchanged Stable theorems", "397 reviewed conservative definitions",
                   "865 actual expansion arrows", "13,212 theorem dependencies",
                   "66 proof families", "full G091 remains open", "release-v33/manifest.json"):
        if phrase not in result:
            raise HubError("missing current boundary: " + phrase)


def render_public_hub(parent, revision):
    if (type(parent) is not bytes or len(parent) != PARENT_HUB_BYTES
            or sha256(parent).hexdigest() != PARENT_HUB_SHA256):
        raise HubError("the exact immutable v32 hub bytes are required")
    if type(revision) is not str or re.fullmatch(r"[0-9a-f]{12}", revision) is None:
        raise HubError("current navigation requires a twelve-hex catalogue digest")
    original = parent.decode("utf-8")
    result = original.replace(PARENT_REVISION, revision)
    result = result.replace("Alpha v32 checked use", "Alpha v33 checked use")
    for before, after in _CURRENT_PROSE:
        result = _once(result, before, after)
    result = _once(result, _OLD_DIVISION, _NEW_DIVISION)
    marker = '    <section class="frontier-intro" aria-labelledby="research-v32-heading"'
    result = _once(result, marker, _new_section(revision) + marker)
    marker = '      <p><a href="release-v32/manifest.json">'
    release = ('      <p><a href="release-v33/manifest.json">Current v33 public-delivery inventory</a> · '
               '<a href="release-v33/alpha-v33-research-receipt-v1.json">V33 verification record</a>. '
               'Delivery metadata and stored records do not themselves grant proof or admission authority.</p>\n')
    result = _once(result, marker, release + marker)
    _validate_projection(original, result, revision)
    raw = result.encode("utf-8")
    if len(raw) > MAX_HUB_BYTES:
        raise HubError("current hub exceeds its unchanged delivery limit")
    return raw
