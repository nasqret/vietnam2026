#!/usr/bin/env python3
"""Pure v32 public-hub projection of the immutable, literal v31 hub.

This module formats delivery bytes only. It does not import an edition, read a
receipt, perform admission, or create a live proof capability. The v32 stager
must authenticate the actual completed release before using this projection.
The v31 source, its first-admission records, QR style, and historical artifact
links remain unchanged. There is deliberately no file-writing CLI.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit


PARENT_HUB_PATH = "deploy/proofs/index.html"
PARENT_HUB_BYTES = 80289
PARENT_HUB_SHA256 = "7d82eafef7694aee35970a546a82542caa5045cbb79eb284fd5117ffcaae3992"
PARENT_REVISION = "6c9ebfb3c37e"
MAX_HUB_BYTES = 256 * 1024

# Literal, ordered primary entrances in the pinned parent, not a discovered
# subset and not a theorem/admission registry.
PARENT_FAMILY_ROUTES = (
    "quadratic-reciprocity", "bertrand-postulate",
    "euler-units", "prime-fields", "mobius-values", "signed-sums",
    "divisor-sums", "signed-weighted-sums", "prime-field-polynomials",
    "divisor-involutions", "mobius-divisor-cancellation", "rectangular-sums",
    "polynomial-products", "finite-support", "dirichlet-convolution",
    "dirichlet-fubini", "dirichlet-units", "mobius-inversion",
    "dirichlet-signed-units", "dirichlet-triangular", "dirichlet-inverses",
    "best-approximation", "totient-products", "squarefree-kernels",
    "exponent-lifting", "gaussian-factorization", "prime-valuation-support",
    "arithmetic-foundations", "prime-enumeration", "gaussian-integers",
    "eisenstein-integers", "integer-linear-algebra", "hensel-lifting",
    "generalized-crt", "multinomial-kummer", "prime-count-chebyshev",
    "cornacchia", "cauchy-davenport", "matrix-cofactor-expansion",
    "polynomial-taylor-hensel", "generalized-crt-compatibility",
    "matrix-determinant-minors", "polynomial-hensel", "generalized-crt-fold",
    "euclidean-logarithmic-bound", "binary-digit-extraction",
    "primes-three-mod-four", "supplementary-laws", "kummer", "two-squares",
    "four-squares", "lucas", "pythagorean-fermat-four", "polynomial-horner",
    "matrix-dot-product", "bertrand-prime-chains", "continued-fractions",
    "matrix-coded-products", "euclidean-complexity",
    "binary-modular-exponentiation", "binary-length",
    "euclidean-gcd-transport", "binary-modular-execution",
)
NEW_FAMILIES = (
    ("multiplicative-convolution", 90),
    ("polynomial-division-prerequisites", 85),
)
FAMILY_ROUTES = (
    *PARENT_FAMILY_ROUTES[:2], *(slug for slug, _count in NEW_FAMILIES),
    *PARENT_FAMILY_ROUTES[2:],
)

# These are current hub statements, not changes to any historical theorem,
# source, receipt, or reader. Every old fragment occurs exactly once.
_G009_PROSE = (
    (
        "Full G009 still needs multiplicative closure; general prime-power fields in G091 remain open.",
        "Full finite signed G009 is now closed, including multiplicative closure; general prime-power fields in G091 remain open.",
    ),
    (
        "G009: inverse criterion and remaining closure",
        "G009: complete finite signed convolution and multiplicative closure",
    ),
    (
        "Full G009 still requires multiplicative-function closure.",
        "The separately admitted multiplicative-convolution family completes finite signed G009.",
    ),
    (
        "Full G009 remains broader.",
        "Together with the separately admitted multiplicative-convolution family, the finite signed G009 contract is complete.",
    ),
    (
        "The separate inverse family proves the general unit-at-one criterion; multiplicative-function closure remains open.",
        "The separate inverse family proves the general unit-at-one criterion; the new multiplicative-convolution family supplies the remaining finite signed G009 closure.",
    ),
    (
        "Full G009 multiplicative closure and G091 prime-power fields remain open.",
        "Finite signed G009, including multiplicative closure, is now proved; general G091 prime-power fields remain open.",
    ),
    (
        "full G009 remains broader.",
        "the separately admitted multiplicative-convolution family completes finite signed G009.",
    ),
    (
        "Multiplicative-function closure and full G009 remain open.",
        "Multiplicative closure on nonempty normalized prefixes is proved in its separate family, completing finite signed G009.",
    ),
)

_CURRENT_PROSE = (
    ('content="alpha-v31-checked-use"', 'content="alpha-v32-checked-use"'),
    ('data-current-alpha="v31"', 'data-current-alpha="v32" data-alpha-first="v31"'),
    ("Nineteen chapters, 574 newly admitted proofs.",
     "Nineteen chapters, 574 proofs first admitted in v31."),
    ("now belong to Alpha v31.",
     "were first admitted in Alpha v31 and remain checked use in Alpha v32."),
    ("Alpha has 3,796 checked-use entries.", "Alpha v32 has 3,971 checked-use entries."),
    ('aria-label="New Alpha v31 proof families"',
     'aria-label="Proof families first admitted in Alpha v31"'),
    ("372 reviewed conservative definitions with 787 actual expansion arrows, and 12,248 theorem dependencies.",
     "390 reviewed conservative definitions with 844 actual expansion arrows, and 12,751 theorem dependencies."),
    ("Alpha v31 has 3,796 checked-use entries: 432 unchanged Stable theorems and 3,364 additional Alpha-closed theorems.",
     "Alpha v32 has 3,971 checked-use entries: 432 unchanged Stable theorems and 3,539 additional Alpha-closed theorems."),
    ("Its 574 new statements extend every earlier admission without rewriting historical evidence.",
     "The 175 first admissions in v32 extend the 3,796-entry v31 parent without rewriting historical evidence."),
    ("The current library contains 63 proof families.",
     "The current library contains 65 proof families."),
)

_VOID_TAGS = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input",
                        "link", "meta", "param", "source", "track", "wbr"))
_ARTICLE = re.compile(r'<article\b[^>]*>.*?</article>', re.DOTALL)
_HISTORY_ANCHOR = re.compile(
    r'<a\b[^>]*href="(?:artifacts/|checkpoints/|release-v31/)[^"]*"[^>]*>.*?</a>',
    re.DOTALL,
)


class HubError(ValueError):
    """A literal parent, bounded input, or presentation invariant changed."""


class _Inventory(HTMLParser):
    """Small structural check; it does not interpret proof or release data."""

    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.ids: set[str] = set()
        self.links: list[tuple[str, str, str]] = []
        self.cards: list[str] = []
        self.scopes: list[str] = []
        self._card: list[str] | None = None
        self.feed(source)
        self.close()
        if self.stack or self._card is not None:
            raise HubError("unclosed hub HTML element")

    def handle_starttag(self, tag, attrs):
        if len(dict(attrs)) != len(attrs):
            raise HubError("duplicate hub HTML attribute")
        values = dict(attrs)
        if tag in {"script", "iframe", "base", "style"} or any(key.startswith("on") for key in values):
            raise HubError("the static QR hub cannot add active content or styles")
        identifier = values.get("id")
        if identifier is not None:
            if not identifier or identifier in self.ids:
                raise HubError("empty or duplicate hub HTML identifier")
            self.ids.add(identifier)
        for field in ("href", "src"):
            if field in values:
                if type(values[field]) is not str:
                    raise HubError("hub link has no literal URL")
                self.links.append((tag, field, values[field]))
        if tag == "meta" and values.get("name") == "proof-publication-scope":
            self.scopes.append(values.get("content"))
        if tag == "article":
            if self._card is not None or "family-card" not in values.get("class", "").split():
                raise HubError("unexpected or nested hub article")
            self._card = []
        if tag == "a" and self._card is not None and "primary-action" in values.get("class", "").split():
            self._card.append(values.get("href", ""))
        if tag not in _VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise HubError("mismatched hub HTML element")
        if tag == "article":
            if self._card is None or len(self._card) != 1:
                raise HubError("each family needs exactly one primary entrance")
            self.cards.append(self._card[0])
            self._card = None


def _once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise HubError("the literal parent hub no longer has its reviewed fragment: " + old[:96])
    return source.replace(old, new, 1)


def _legacy_card(card: str, revision: str) -> str:
    """Only current labels/navigation and the eight reviewed G009 sentences."""
    card = card.replace(PARENT_REVISION, revision)
    card = card.replace("Alpha v31 checked use", "Alpha v32 checked use")
    for old, new in _G009_PROSE:
        card = card.replace(old, new)
    return card


def _new_section(revision: str) -> str:
    return f'''    <section class="frontier-intro" aria-labelledby="research-v32-heading" data-current-alpha="v32">
      <p class="eyebrow">Current Alpha v32 release</p>
      <h2 id="research-v32-heading">Two new chapters, 175 first admissions.</h2>
      <p>Alpha v32 extends the unchanged 3,796-entry v31 parent to 3,971 checked-use entries. The 90 multiplicative-convolution results and 85 polynomial-division prerequisites now have current Alpha checked use. Stable remains the separate, unchanged 432-theorem default library; the 3,539 additional Alpha-closed entries are not Stable admissions.</p>
      <p class="candidate-disclaimer">G009 is closed for its finite signed arithmetic-table contract, including multiplicative closure. G091 remains open: polynomial division prerequisites do not construct every prime-power field. Current membership, first admission, historical proof evidence and still-open goals are distinct.</p>
      <p><a href="grand-campaign/?view=goal&amp;focus=G009&amp;v={revision}">G009: completed finite signed Dirichlet theory</a> · <a href="grand-campaign/?view=goal&amp;focus=G091&amp;v={revision}">G091: polynomial prerequisites and the open field construction</a></p>
    </section>
    <section class="family-grid frontier-grid" aria-label="New Alpha v32 proof families">
      <article class="family-card candidate-card euclidean-card" data-alpha-first="v32" id="multiplicative-convolution-card">
        <p class="card-kicker">Alpha v32 checked use · 90 independently proved theorems</p>
        <h2>Multiplicative Dirichlet Convolution</h2>
        <p>Construct actual coprime divisor pairs, finite Cartesian sums and support-sensitive reindexing, then prove that convolution preserves multiplicativity on nonempty finite signed prefixes. Normalization is F(1)=+1, signed code 2, not an arbitrary signed unit. Coprime products must lie in the inclusive prefix; zeroth values remain unrestricted.</p>
        <p class="candidate-badge">G009 complete · independently kernel and Lean verified; not Stable</p>
        <a class="primary-action" href="multiplicative-convolution/?v={revision}">Explore the proof map <span aria-hidden="true">→</span></a>
        <p>Original HA and compiled Lean verification · first admitted v32 · not Stable.</p>
        <p>The inherited convolution, associativity, delta and inverse theorems retain their original first-admission evidence.</p>
        <p>Campaign connections: <a href="grand-campaign/?view=goal&amp;focus=G009&amp;v={revision}">G009</a></p>
      </article>
      <article class="family-card candidate-card polynomial-card" data-alpha-first="v32" id="polynomial-division-prerequisites-card">
        <p class="card-kicker">Alpha v32 checked use · 85 independently proved theorems</p>
        <h2>Prime-Field Polynomial Division Prerequisites</h2>
        <p>Follow 26 coefficient negation/subtraction results, 22 actual leading-zero trimming results, 20 monic-normalization results and 17 Horner/synthetic-division results. Highest-degree-first beta prefixes carry explicit lengths; uniqueness compares decoded coefficients, not code numbers. Synthetic executions have actual quotient traces, coefficient laws and evaluation remainders.</p>
        <p class="candidate-badge">G091 prerequisites proved · full G091 remains open; not Stable</p>
        <a class="primary-action" href="polynomial-division-prerequisites/?v={revision}">Explore the proof map <span aria-hidden="true">→</span></a>
        <p>Original HA and compiled Lean verification · first admitted v32 · not Stable.</p>
        <p>General division by an arbitrary nonzero polynomial, polynomial gcd/Bézout, irreducible-polynomial existence in every positive degree and general prime-power fields remain open in this release. The zero polynomial has no represented natural-number degree.</p>
        <p>Campaign connections: <a href="grand-campaign/?view=goal&amp;focus=G091&amp;v={revision}">G091</a></p>
      </article>
    </section>
'''


def _validate_projection(parent: str, result: str, revision: str) -> None:
    """Fail closed on delivery structure, never confer mathematical authority."""
    original, current = _Inventory(parent), _Inventory(result)
    old_routes = tuple(f"{slug}/?v={PARENT_REVISION}" for slug in PARENT_FAMILY_ROUTES)
    new_routes = tuple(f"{slug}/?v={revision}" for slug in FAMILY_ROUTES)
    if tuple(original.cards) != old_routes or tuple(current.cards) != new_routes:
        raise HubError("the exact 63 inherited and two new family entrances changed")
    if len(set(current.cards)) != 65:
        raise HubError("the current hub needs exactly 65 distinct family entrances")
    if original.scopes != ["alpha-v31-checked-use"] or current.scopes != ["alpha-v32-checked-use"]:
        raise HubError("the current Alpha display scope changed")
    added_ids = {"research-v32-heading", "multiplicative-convolution-card",
                 "polynomial-division-prerequisites-card"}
    if current.ids != original.ids | added_ids or original.ids & added_ids:
        raise HubError("historical hub anchors changed")
    old_cards, new_cards = _ARTICLE.findall(parent), _ARTICLE.findall(result)
    if len(old_cards) != 63 or len(new_cards) != 65:
        raise HubError("unexpected family article layout")
    if result.count(_new_section(revision)) != 1:
        raise HubError("the two new family contracts or current-release introduction changed")
    historical_intro = ('<section class="frontier-intro" aria-labelledby="completed-lower-heading" '
                        'data-current-alpha="v32" data-alpha-first="v31">')
    if result.count(historical_intro) != 1:
        raise HubError("the completed lower layer lost its historical first admission")
    retained = (*new_cards[:2], *new_cards[4:])
    if tuple(retained) != tuple(_legacy_card(card, revision) for card in old_cards):
        raise HubError("a historical card or first-admission record changed")
    if Counter(_HISTORY_ANCHOR.findall(result)) != Counter(_HISTORY_ANCHOR.findall(parent)):
        raise HubError("a historical release or artifact link changed")
    styles = [url for tag, field, url in current.links if tag == "link" and field == "href"
              and urlsplit(url).path.endswith(".css")]
    if styles != [f"assets/proofs.css?v={revision}"]:
        raise HubError("the original QR stylesheet changed")
    # Every current HTML route has the supplied revision. Dated checkpoint
    # navigation and immutable downloadable artifacts intentionally keep theirs.
    for _tag, _field, url in current.links:
        split = urlsplit(url)
        if split.scheme or split.netloc or split.path.startswith(("artifacts/", "checkpoints/", "release-v31/", "release-v32/")):
            continue
        if split.path.endswith(("/", ".html")) and (split.query.split("&")[-1] != "v=" + revision or split.fragment):
            raise HubError("a current hub route has a stale revision or fragment")
    for old, _new in (*_G009_PROSE, *_CURRENT_PROSE):
        if old in result:
            raise HubError("stale current-edition or G009 hub prose remains")
    for required in (
        "G009 is closed for its finite signed arithmetic-table contract",
        "G091 remains open:", "3,971 checked-use entries", "3,539 additional Alpha-closed",
        "432 unchanged Stable theorems", "390 reviewed conservative definitions",
        "844 actual expansion arrows", "12,751 theorem dependencies",
        "release-v32/manifest.json", "release-v32/alpha-v32-research-receipt-v1.json",
    ):
        if required not in result:
            raise HubError("missing exact current hub boundary: " + required)


def render_public_hub(parent: bytes, revision: str) -> bytes:
    """Format one exact parent into a current hub, without reading or writing.

    ``revision`` is display navigation data (the stager supplies the actual
    catalog digest prefix), not evidence that a release has been verified.
    """
    if type(parent) is not bytes or len(parent) != PARENT_HUB_BYTES:
        raise HubError("the exact bounded v31 parent hub bytes are required")
    if sha256(parent).hexdigest() != PARENT_HUB_SHA256:
        raise HubError("the immutable v31 public hub changed")
    if type(revision) is not str or re.fullmatch(r"[0-9a-f]{12}", revision) is None:
        raise HubError("the current catalog navigation revision must be twelve lowercase hexadecimal characters")
    original = parent.decode("utf-8")
    result = original.replace(PARENT_REVISION, revision)
    result = result.replace("Alpha v31 checked use", "Alpha v32 checked use")
    for old, new in (*_G009_PROSE, *_CURRENT_PROSE):
        result = _once(result, old, new)
    marker = '    <section class="frontier-intro" aria-labelledby="completed-lower-heading"'
    result = _once(result, marker, _new_section(revision) + marker)
    old_release = '      <p><a href="release-v31/manifest.json">'
    current_release = (
        '      <p><a href="release-v32/manifest.json">Current v32 public-delivery inventory</a> · '
        '<a href="release-v32/alpha-v32-research-receipt-v1.json">V32 verification record</a>. '
        'Delivery metadata and stored records do not themselves grant proof or admission authority.</p>\n'
    )
    result = _once(result, old_release, current_release + old_release)
    _validate_projection(original, result, revision)
    raw = result.encode("utf-8")
    if len(raw) > MAX_HUB_BYTES:
        raise HubError("the current hub exceeds its fixed delivery bound")
    return raw
