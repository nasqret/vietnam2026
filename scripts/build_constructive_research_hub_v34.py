#!/usr/bin/env python3
"""Pure v34 proof-library hub over the exact v33 public page.

No catalogue, receipt, proof or publication authority is loaded here.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
import re
from urllib.parse import urlsplit

import build_constructive_research_hub_v33 as previous

PARENT_HUB_BYTES = 88263
PARENT_HUB_SHA256 = "f9f0d4d2f149f91695d5ff0f4333f3e10f8f27fc83ec2760fca59b2d3eed3551"
PARENT_REVISION = "6be052da195a"
MAX_HUB_BYTES = previous.MAX_HUB_BYTES
PARENT_FAMILY_ROUTES = previous.FAMILY_ROUTES
FAMILY_ROUTES = (*PARENT_FAMILY_ROUTES[:2], "polynomial-gcd-bezout", "congruence-arithmetic", *PARENT_FAMILY_ROUTES[2:])
HubError, _Inventory, _once = previous.HubError, previous._Inventory, previous._once
_ARTICLE = previous.previous._ARTICLE
_OLD_DIVISION = previous._NEW_DIVISION
_NEW_DIVISION = (
    "General polynomial division remains admitted in polynomial-euclidean-division. "
    "The new polynomial-gcd-bezout family proves shift/scalar laws, associativity, "
    "recursive normalized gcd/Bézout existence, greatestness and formal uniqueness. "
    "Irreducible-polynomial existence in every positive degree and general prime-power fields remain open.")
_OLD_BADGE = "General division proved · associativity and gcd/Bézout remain open; not Stable"
_NEW_BADGE = "General division proved · normalized gcd/Bézout is now proved in its separate chapter; not Stable"
_CURRENT_PROSE = (
    ('content="alpha-v33-checked-use"', 'content="alpha-v34-checked-use"'),
    ('aria-labelledby="research-v33-heading" data-current-alpha="v34">',
     'aria-labelledby="research-v33-heading" data-current-alpha="v34" data-alpha-first="v33">'),
    ('<p class="eyebrow">Current Alpha v33 release</p>', '<p class="eyebrow">First admitted in Alpha v33</p>'),
    ("121 newly admitted results extend Alpha to 4,092 checked-use entries.",
     "The v33 release added121 results to reach4,092 checked-use entries; those first admissions remain available in Alpha v34."),
    ("The separate shift/scalar → associativity → gcd/Bézout campaign continues; full G091 remains open.",
     "The separate shift/scalar → associativity → gcd/Bézout campaign is now proved; full G091 remains open."),
    ("G091: division accomplished, associativity and gcd/Bézout next",
     "G091: division and normalized gcd/Bézout accomplished; finite fields next"),
    ('aria-label="New Alpha v33 proof family"', 'aria-label="Proof family first admitted in Alpha v33"'),
    ("remain checked use in Alpha v33.", "remain checked use in Alpha v34."),
    ("Alpha v33 has 4,092 checked-use entries.", "Alpha v34 has 4,223 checked-use entries."),
    ("397 reviewed conservative definitions with 865 actual expansion arrows, and 13,212 theorem dependencies.",
     "407 reviewed conservative definitions with 884 actual expansion arrows, and 13,816 theorem dependencies."),
    ("Alpha v33 has 4,092 checked-use entries: 432 unchanged Stable theorems and 3,660 additional Alpha-closed theorems.",
     "Alpha v34 has 4,223 checked-use entries: 432 unchanged Stable theorems and 3,791 additional Alpha-closed theorems."),
    ("The 121 first admissions in v33 extend the 3,971-entry v32 parent without rewriting historical evidence.",
     "The 131 first admissions in v34 extend the 4,092-entry v33 parent without rewriting historical evidence."),
    ("The current library contains 66 proof families.", "The current library contains 68 proof families."),
    ("Current v33 public-delivery inventory", "Historical v33 public-delivery inventory"),
)

def _legacy_card(card, revision):
    return (card.replace(PARENT_REVISION, revision)
            .replace("Alpha v33 checked use", "Alpha v34 checked use")
            .replace(_OLD_DIVISION, _NEW_DIVISION).replace(_OLD_BADGE, _NEW_BADGE))

def _new_section(revision):
    return f'''    <section class="frontier-intro" aria-labelledby="research-v34-heading" data-current-alpha="v34">
      <p class="eyebrow">Current Alpha v34 release</p>
      <h2 id="research-v34-heading">Constructive polynomial gcd and exact congruence classes.</h2>
      <p>131 newly admitted results extend Alpha to 4,223 checked-use entries. Stable remains the unchanged 432-theorem default. The actual 493-node polynomial bundle and 215-node congruence bundle have fresh original HA and same-byte compiled Lean checks, with nineteen ordinary principal certificates.</p>
      <p class="candidate-disclaimer">Polynomial gcd/Bézout existence, greatestness and normalized uniqueness are proved, including zero inputs. Non-coprime congruences have explicit bounded solution parametrizations. The first-layer foundations remain complete; full G091 remains open. Definition arrows remain notation, never extra proof premises.</p>
    </section>
    <section class="family-grid frontier-grid" aria-label="New Alpha v34 proof families">
      <article class="family-card candidate-card polynomial-card" data-alpha-first="v34" id="polynomial-gcd-bezout-card">
        <p class="card-kicker">Alpha v34 checked use · 119 independently proved theorems</p>
        <h2>Prime-Field Polynomial GCD and Bézout</h2>
        <p>Follow shift/scalar laws, associativity, length alignment and Euclidean backward transport through degree descent to an actual zero-or-monic gcd with Bézout coefficients. Prove greatestness and uniqueness up to formal coefficient equivalence.</p>
        <p>Ten conservative definitions organize the construction. Empty and all-zero polynomials are included; raw beta codes and non-unique Bézout coefficients are never equated.</p>
        <p class="candidate-badge">Recursive normalized gcd/Bézout proved · full G091 remains open; not Stable</p>
        <a class="primary-action" href="polynomial-gcd-bezout/?v={revision}">Explore the proof map <span aria-hidden="true">→</span></a>
        <p>Original HA and compiled Lean verification · first admitted v34 · not Stable.</p>
        <p>Campaign connections: <a href="polynomial-euclidean-division/?v={revision}">Euclidean division</a> · <a href="grand-campaign/?view=goal&amp;focus=G091&amp;v={revision}">G091: the larger finite-field goal</a></p>
      </article>
      <article class="family-card candidate-card" data-alpha-first="v34" id="congruence-arithmetic-card">
        <p class="card-kicker">Alpha v34 checked use · 12 independently proved theorems</p>
        <h2>Congruence Arithmetic</h2>
        <p>Cancel a coefficient at the gcd-reduced modulus, describe every solution class and construct a reduced representative. Bounded solutions are in explicit bijection with t&lt;g through x=r+M*t: exactly g solutions when the gcd divides the target.</p>
        <p>Modulus zero and one have separate exact contracts. Fermat's theorem covers all natural inputs, including zero and prime multiples. No quotient or cardinality oracle is assumed.</p>
        <p class="candidate-badge">Exact non-coprime classes and bounded solution bijections proved; not Stable</p>
        <a class="primary-action" href="congruence-arithmetic/?v={revision}">Explore the proof map <span aria-hidden="true">→</span></a>
        <p>Original HA and compiled Lean verification · first admitted v34 · not Stable.</p>
        <p>Campaign connections: <a href="generalized-crt/?v={revision}">Generalized CRT</a> · <a href="euler-units/?v={revision}">Euler's theorem</a> · <a href="grand-campaign/?view=goal&amp;focus=G012&amp;v={revision}">G012</a></p>
      </article>
    </section>
'''

def _validate_projection(parent, result, revision):
    before, after = _Inventory(parent), _Inventory(result)
    if tuple(before.cards) != tuple(slug+"/?v="+PARENT_REVISION for slug in PARENT_FAMILY_ROUTES):
        raise HubError("the exact66 inherited hub entrances changed")
    if tuple(after.cards) != tuple(slug+"/?v="+revision for slug in FAMILY_ROUTES):
        raise HubError("the exact68 current hub entrances changed")
    if before.scopes != ["alpha-v33-checked-use"] or after.scopes != ["alpha-v34-checked-use"]:
        raise HubError("current display scope changed")
    if after.ids != before.ids | {"research-v34-heading","polynomial-gcd-bezout-card","congruence-arithmetic-card"}:
        raise HubError("historical hub anchors changed")
    old_cards,new_cards = _ARTICLE.findall(parent),_ARTICLE.findall(result)
    retained = (*new_cards[:2],*new_cards[4:])
    if len(old_cards)!=66 or len(new_cards)!=68 or tuple(retained)!=tuple(_legacy_card(card,revision) for card in old_cards):
        raise HubError("an old card or first-admission identity changed")
    if result.count(_new_section(revision))!=1:
        raise HubError("the new two-family boundary changed")
    historical=("artifacts/","checkpoints/","release-v31/","release-v32/","release-v33/")
    def history(page):
        return Counter(url for _,_,url in page.links if urlsplit(url).path.startswith(historical))
    if history(before)!=history(after):
        raise HubError("historical artifact destinations changed")
    styles=[url for tag,field,url in after.links if tag=="link" and field=="href" and urlsplit(url).path.endswith(".css")]
    if styles!=["assets/proofs.css?v="+revision]:
        raise HubError("the original Quadratic Reciprocity stylesheet changed")
    for _,_,href in after.links:
        parsed=urlsplit(href)
        if parsed.scheme or parsed.netloc or parsed.path.startswith((*historical,"release-v34/")):continue
        if parsed.path.endswith(("/",".html")) and parsed.query.split("&")[-1]!="v="+revision:
            raise HubError("a current hub route has a stale revision")
    for phrase in ("4,223 checked-use entries","3,791 additional Alpha-closed","432 unchanged Stable theorems",
                   "407 reviewed conservative definitions","884 actual expansion arrows","13,816 theorem dependencies",
                   "68 proof families","full G091 remains open","release-v34/manifest.json"):
        if phrase not in result:raise HubError("missing current boundary: "+phrase)

def render_public_hub(parent,revision):
    if type(parent) is not bytes or len(parent)!=PARENT_HUB_BYTES or sha256(parent).hexdigest()!=PARENT_HUB_SHA256:
        raise HubError("the exact immutable v33 public hub bytes are required")
    if type(revision) is not str or re.fullmatch(r"[0-9a-f]{12}",revision) is None:
        raise HubError("current navigation requires a twelve-hex catalogue digest")
    original=parent.decode("utf-8")
    result=(original.replace(PARENT_REVISION,revision)
            .replace("Alpha v33 checked use","Alpha v34 checked use")
            .replace('data-current-alpha="v33"','data-current-alpha="v34"'))
    for before,after in _CURRENT_PROSE:
        if before=="remain checked use in Alpha v33.":
            if result.count(before)!=2:raise HubError("the two historical current captions changed")
            result=result.replace(before,after)
        else:result=_once(result,before,after)
    result=_once(result,_OLD_DIVISION,_NEW_DIVISION)
    result=_once(result,_OLD_BADGE,_NEW_BADGE)
    marker='    <section class="frontier-intro" aria-labelledby="research-v33-heading"'
    result=_once(result,marker,_new_section(revision)+marker)
    marker='      <p><a href="release-v33/manifest.json">'
    release=('      <p><a href="release-v34/manifest.json">Current v34 public-delivery inventory</a> · '
             '<a href="release-v34/alpha-v34-research-receipt-v1.json">V34 verification record</a>. '
             'Delivery metadata and saved records do not grant proof or admission authority.</p>\n')
    result=_once(result,marker,release+marker)
    _validate_projection(original,result,revision)
    raw=result.encode("utf-8")
    if len(raw)>MAX_HUB_BYTES:raise HubError("current hub exceeds its unchanged delivery limit")
    return raw
