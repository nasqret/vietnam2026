"""Add a reversible reading guide to an authenticated exact/defined proof page.

This is presentation, not proof reconstruction. Every checkpoint cites original
line IDs. Structural descriptions say what commands do, never invent a lemma,
claim a branch is closed, or grant proof authority. Curated mathematical notes
are accepted only for their exact native script digest.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from hashlib import sha256
from html import escape, unescape
import re


SCHEMA = "peano-proof-reading-guide-v1"
MAX_PAGE_BYTES = 64 * 1024 * 1024
MAX_LINES = 65_536
MAX_CHECKPOINT_LINES = 10
MAX_VISIBLE_FORMULA = 600
HEAD_START = "<!-- proof-reader-v1:assets -->"
HEAD_END = "<!-- /proof-reader-v1:assets -->"
GUIDE_START = "<!-- proof-reader-v1:guide -->"
GUIDE_END = "<!-- /proof-reader-v1:guide -->"
EXACT_START = "<!-- proof-reader-v1:exact -->"
EXACT_END = "<!-- /proof-reader-v1:exact -->"
RAW_CLOSE = "</details>" + EXACT_END
_OL = re.compile(r'<ol\b[^>]*class="(?:pa|pd)-formal-proof"[^>]*>.*?</ol>', re.S)
_LINE = re.compile(r'<li\b([^>]*\bclass="[^\"]*\b(?:pa|pd)-proof-line\b[^\"]*"[^>]*)>(.*?)</li>', re.S)
_CODE = re.compile(r'<code\b[^>]*>(.*?)</code>', re.S)
_ATTR = re.compile(r'([\w-]+)="([^"]*)"')
_ANCHOR = re.compile(r'<a\b([^>]*)>(.*?)</a>', re.S)
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z")


class ReadabilityError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReadabilityError(message)


def text(markup):
    return unescape(re.sub(r"<[^>]*>", "", markup)).strip()


def human(name):
    return name.replace("_", " ")


def digest(value):
    return sha256(value.encode("utf-8")).hexdigest()


def safe_href(value):
    value = unescape(value)
    return bool(value) and not re.search(r"[\x00-\x20\\]", value) and (
        value.startswith(("https://", "http://", "#", "./", "../"))
        or not re.match(r"(?:[A-Za-z][A-Za-z0-9+.-]*:|//)", value)
    )


@dataclass(frozen=True)
class ProofLine:
    number: int
    anchor: str
    command: str
    displayed: str
    definitions: tuple[tuple[str, str], ...]
    has_expansion: bool = False
    native_anchor: str = ""

    @property
    def tactic(self):
        return self.command.split(maxsplit=1)[0]

    @property
    def args(self):
        parts = self.command.split(maxsplit=1)
        return parts[1] if len(parts) == 2 else ""


@dataclass(frozen=True)
class ProofPage:
    name: str
    edition: str
    lines: tuple[ProofLine, ...]
    script_sha256: str
    dependencies: dict[str, str]
    proof_start: int
    proof_end: int
    exact_href: str | None = None
    exact_page_sha256: str | None = None
    paired_notation_rows: int = 0


def parse_page(source):
    require(type(source) is str and len(source.encode()) <= MAX_PAGE_BYTES, "oversized proof page")
    require(GUIDE_START not in source, "proof page already has a reading guide")
    matches = list(_OL.finditer(source))
    if not matches:
        return None
    require(len(matches) == 1, "ambiguous formal proof lists")
    match = matches[0]
    heading = re.search(r"<h1\b[^>]*>(.*?)</h1>", source, re.S)
    require(heading is not None, "proof page lacks a theorem heading")
    name = text(heading[1])
    require(_NAME.fullmatch(name), "ambiguous theorem name")
    lines = []
    for item in _LINE.finditer(match[0]):
        attrs = dict(_ATTR.findall(item[1]))
        require(attrs.get("data-line", "").isdigit(), "proof line lacks an ordinal")
        number = int(attrs["data-line"])
        anchor = attrs.get("id", "")
        require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_:.-]*", anchor), "unsafe proof anchor")
        codes = _CODE.findall(item[2])
        require(1 <= len(codes) <= 2, "ambiguous exact/defined command")
        if len(codes) == 2:
            require('class="pd-exact-line"' in item[2], "second command has no expansion disclosure")
        original, displayed = text(codes[-1]), text(codes[0])
        require(original and number == len(lines) + 1, "missing, reordered, or empty proof command")
        definitions = []
        for link in _ANCHOR.finditer(codes[0]):
            lattrs = dict(_ATTR.findall(link[1]))
            if "pd-definition-ref" in lattrs.get("class", "").split():
                href = unescape(lattrs.get("href", ""))
                require(safe_href(href), "unsafe definition link")
                entry = (text(link[2]), href)
                if entry not in definitions:
                    definitions.append(entry)
        lines.append(ProofLine(number, anchor, original, displayed, tuple(definitions), len(codes) == 2))
        require(len(lines) <= MAX_LINES, "proof line bound exceeded")
    require(lines, "formal proof list has no supported lines")
    require(match[0].count('<li ') == len(lines), "unparsed proof row")
    require(len({line.anchor for line in lines}) == len(lines), "duplicate proof anchor")
    dependencies = {}
    for link in _ANCHOR.finditer(source):
        attrs = dict(_ATTR.findall(link[1]))
        classes = attrs.get("class", "").split()
        if not any(item in classes for item in ("pa-theorem-ref", "pd-theorem-ref", "pd-theorem-chip")):
            continue
        label = text(link[2]).split()
        if label and _NAME.fullmatch(label[-1]):
            href = unescape(attrs.get("href", ""))
            if safe_href(href):
                dependencies[label[-1]] = href
    used = {line.args.split()[0] for line in lines if line.args and line.tactic in
            {"apply", "exact", "specialize", "forall_elim", "use", "rewrite"}}
    dependencies = {name: href for name, href in dependencies.items() if name in used}
    return ProofPage(name, "defined" if 'class="pd-formal-proof"' in match[0] else "exact",
        tuple(lines), digest("\n".join(line.command for line in lines)), dependencies,
        match.start(), match.end())


def bind_exact_page(page, exact_raw, exact_href):
    """Bind notation rows to their paired, authenticated exact-edition source.

    Older defined editions abbreviate some ``have`` formulas without an inline
    expansion. Pair identity is checked here; the caller authenticates both
    files. This is provenance, not a new formula-equivalence certificate.
    """
    require(page.edition == "defined", "only a defined page needs an exact pair")
    require(type(exact_raw) is bytes, "defined page requires its exact source bytes")
    require(type(exact_href) is str and safe_href(exact_href), "unsafe exact-edition link")
    exact = parse_page(exact_raw.decode("utf-8"))
    require(exact is not None and exact.edition == "exact", "paired source is not an exact theorem page")
    require(exact.name == page.name and len(exact.lines) == len(page.lines), "exact/defined theorem identity differs")
    lines, notation_rows = [], 0
    for defined_line, native_line in zip(page.lines, exact.lines):
        if defined_line.command != native_line.command:
            # Only the historical typed-have notation renderer changes these
            # rows. All names and every other command must match literally.
            native_name, native_colon, _ = native_line.args.partition(":")
            defined_name, defined_colon, _ = defined_line.args.partition(":")
            require(not defined_line.has_expansion
                and defined_line.tactic == native_line.tactic == "have"
                and native_colon == defined_colon == ":"
                and ":=" not in native_line.args and ":=" not in defined_line.args
                and native_name.strip() == defined_name.strip(),
                "exact/defined commands differ beyond local-formula notation")
            notation_rows += 1
        lines.append(replace(defined_line, command=native_line.command, native_anchor=native_line.anchor))
    return replace(page, lines=tuple(lines), script_sha256=exact.script_sha256,
        exact_href=exact_href, exact_page_sha256=sha256(exact_raw).hexdigest(),
        paired_notation_rows=notation_rows)


def category(line):
    tactic = line.tactic
    if tactic in {"have", "suffices"}:
        return "claim"
    if tactic == "induction":
        return "induction"
    if tactic in {"cases", "left", "right", "split", "exfalso"}:
        return "cases"
    if tactic == "exists":
        return "witness"
    if tactic in {"rewrite", "simp", "norm_num", "refl", "symm", "trans", "congr"}:
        return "calculation"
    if tactic in {"apply", "exact", "assumption", "specialize", "forall_elim", "use"}:
        return "application"
    if tactic == "intro":
        return "setup"
    return "structural"


def checkpoints(lines):
    """Contiguous reading groups, deliberately not an inferred proof tree."""
    groups = []
    pending = []
    for line in lines:
        kind = category(line)
        boundary = bool(pending) and (
            len(pending) >= MAX_CHECKPOINT_LINES
            or kind in {"claim", "induction"}
            or (category(pending[0]) not in {"claim", "induction"}
                and kind != category(pending[0]))
            or (category(pending[0]) in {"claim", "induction"}
                and kind not in {"setup", "application", "calculation"})
        )
        if boundary:
            groups.append(tuple(pending))
            pending = []
        pending.append(line)
    if pending:
        groups.append(tuple(pending))
    return tuple(groups)


def description(group):
    first = group[0]
    kind, args = category(first), first.args
    if kind == "claim":
        name = args.split(":", 1)[0].strip()
        if ":=" in args:
            return "Deduce " + name, "The conclusion is inferred from the named hypothesis and explicit arguments."
        if first.tactic == "suffices":
            return "Reduce to " + name, "First show that this intermediate claim suffices; its proof is a separate obligation."
        applications = [line.args for line in group[1:] if line.tactic == "apply"]
        reason = "Establish this local claim before using it. It is not an additional assumption."
        if applications:
            reason += " The following proof commands apply " + human(applications[0]) + "."
        return "Establish " + name, reason
    if kind == "induction":
        return "Induction on " + args, "Split the argument into the base and successor obligations. The induction hypothesis is available only in the successor branch."
    if kind == "witness":
        return "Construct an explicit witness", "Supply the displayed value, then prove that it has the required property."
    if kind == "calculation":
        return "Calculate and transport equalities", "Carry out the recorded arithmetic or equality steps; inspect the exact commands for their direction and premises."
    if kind == "application":
        return "Use earlier facts", "Instantiate or apply named facts and discharge the corresponding proof obligations."
    if kind == "setup":
        return "Fix variables and assumptions", "Work with arbitrary variables or the premises of the current implication."
    if kind == "cases":
        return "Separate the logical cases", "Follow the explicit conjunction, disjunction, witness, or contradiction step recorded below."
    return "Continue the formal argument", "The exact commands specify this part of the derivation."


def notes_for(page, notes):
    candidates = [item for item in notes.get("notes", []) if item.get("theorem") == page.name
                  and item.get("script_sha256") == page.script_sha256]
    require(len(candidates) <= 1, "ambiguous mathematical explanation")
    return candidates[0] if candidates else None


def audit_page(page, note=None):
    claims = [line for line in page.lines if line.tactic in {"have", "suffices"}]
    groups = checkpoints(page.lines)
    repeated = Counter(line.command.split(":", 1)[-1].strip() for line in claims if ":=" not in line.command)
    return dict(theorem=page.name, edition=page.edition, script_sha256=page.script_sha256,
        script_source="paired-exact-edition" if page.exact_href else page.edition + "-edition",
        exact_page_sha256=page.exact_page_sha256, paired_notation_rows=page.paired_notation_rows,
        line_count=len(page.lines), checkpoint_count=len(groups), local_claim_count=len(claims),
        max_exact_claim_characters=max((len(line.command) for line in claims), default=0),
        max_defined_claim_characters=max((len(line.displayed) for line in claims), default=0),
        large_display_claims=sum(len(line.displayed) > MAX_VISIBLE_FORMULA for line in claims),
        repeated_local_formulas=sum(count - 1 for count in repeated.values()),
        curated_mathematical_explanation=note is not None,
        explanation_kind="script-bound mathematical commentary" if note else "structural reading guide",
        new_proof_authority=False)


def render_guide(page, note=None, audit_href=None):
    groups = checkpoints(page.lines)
    links = []
    for name, href in page.dependencies.items():
        if name != page.name:
            links.append(f'<a href="{escape(href, quote=True)}">{escape(human(name))}</a>')
    source = "curated mathematical commentary" if note else "structural guide from the recorded commands"
    intro = '<p class="pr-kicker">Read the argument</p><h3 id="proof-reading-title">Proof checkpoints</h3>'
    intro += (f'<p class="pr-meta">{len(page.lines)} script commands · {len(groups)} reading checkpoints · '
              f'{sum(line.tactic in {"have", "suffices"} for line in page.lines)} local claims</p>')
    intro += ('<p class="pr-boundary">This is a reading aid, not a new proof or a proof-tree certificate. '
              'Checkpoint groups are consecutive commands, not inferred branch boundaries. '
              'Every step links to the preserved script.</p>')
    if page.exact_href:
        intro += ('<p class="pr-meta">Definition notation is shown below. '
                  '<a href="' + escape(page.exact_href, quote=True) + '">Open the paired exact edition</a>'
                  ' for the original native formulas. Source pairing is not a new equivalence certificate.</p>')
    if note:
        intro += '<div class="pr-idea"><h4>' + escape(note["title"]) + '</h4>'
        intro += ''.join('<p>' + escape(paragraph) + '</p>' for paragraph in note["paragraphs"])
        intro += '<p class="pr-meta">Mathematical commentary bound to this exact script; it grants no proof authority.</p></div>'
    if links:
        intro += '<details class="pr-ingredients"><summary>Named ingredients (' + str(len(links)) + ')</summary><div class="pr-links">' + ''.join(links) + '</div></details>'
    intro += ('<div class="pr-toolbar" data-reader-toolbar hidden>'
              '<button type="button" data-reader-action="open">Expand checkpoints</button>'
              '<button type="button" data-reader-action="close">Collapse checkpoints</button>'
              '<button type="button" data-reader-action="exact">Show original steps</button>'
              '<label>Find a step <input type="search" data-reader-search placeholder="lemma, witness, induction…"></label>'
              '<span role="status" aria-live="polite" data-reader-status></span></div>')
    rendered = []
    for index, group in enumerate(groups, 1):
        first, last = group[0], group[-1]
        title, why = description(group)
        first_note = (note or {}).get("claims", {}).get(str(first.number))
        if first_note:
            why = first_note
        commands = []
        for line in group:
            label = f'<a class="pr-line-ref" href="#{escape(line.anchor)}" data-reader-exact-line>L{line.number}</a>'
            compact = line.displayed
            if len(compact) > MAX_VISIBLE_FORMULA:
                command = (f'<details class="pr-long-claim"><summary>{escape(line.tactic)} '
                           f'{escape(line.args.split(":", 1)[0][:100])} · expand full local formula '
                           f'({len(compact):,} characters)</summary><code>{escape(compact)}</code></details>')
            else:
                command = '<code>' + escape(compact) + '</code>'
            definitions = ''.join(f'<a href="{escape(href, quote=True)}">{escape(label)}</a>'
                                  for label, href in line.definitions)
            if definitions:
                command += '<span class="pr-definition-links">Definitions: ' + definitions + '</span>'
            if page.exact_href and line.command != line.displayed:
                href = page.exact_href + "#" + line.native_anchor
                command += ('<a class="pr-native-link" href="' + escape(href, quote=True)
                            + '">Original native command in the exact edition</a>')
            commands.append('<li>' + label + '<div>' + command + '</div></li>')
        opened = ' open' if (index == 1 or len(groups) <= 3) else ''
        rendered.append(
            f'<details class="pr-checkpoint" data-reader-checkpoint id="reading-step-{index}"{opened}>'
            f'<summary><span class="pr-step-number">{index:02d}</span><span>{escape(title)}</span>'
            f'<span class="pr-step-range">L{first.number}–{last.number}</span></summary>'
            f'<div class="pr-step-body"><p class="pr-why">{escape(why)}</p>'
            '<ol class="pr-commands">' + ''.join(commands) + '</ol></div></details>')
    footer = ('<p class="pr-meta"><a href="' + escape(audit_href, quote=True) + '">Library-wide reading audit</a></p>') if audit_href else ''
    return (GUIDE_START + '<section class="pr-reader" data-proof-reader aria-labelledby="proof-reading-title" '
            f'data-script-sha256="{page.script_sha256}" data-explanation-kind="{escape(source)}">'
            + intro + '<div class="pr-checkpoints">' + ''.join(rendered) + '</div>' + footer + '</section>' + GUIDE_END)


def enhance_page(raw, *, assets_prefix, revision, notes=None, exact_raw=None, exact_href=None, definitions=None):
    require(type(raw) is bytes, "proof page must be exact UTF-8 bytes")
    source = raw.decode("utf-8")
    page = parse_page(source)
    if page is None:
        return raw, None
    if page.edition == "defined":
        page = bind_exact_page(page, exact_raw, exact_href)
    else:
        require(exact_raw is None and exact_href is None, "exact page must not be rebound")
    require(re.fullmatch(r"[0-9a-f]{12}", revision), "invalid reader asset revision")
    require(safe_href(assets_prefix) and '"' not in assets_prefix, "unsafe reader asset location")
    require(source.count("</head>") == 1, "ambiguous page head")
    previous = audit_page(page)
    notation = dict(notation_compactions=[], notation_compacted_claims=0,
        notation_source_size_skips=0, notation_display_characters_saved=0)
    if definitions is not None:
        page, notation = definitions.apply(page)
    note = notes_for(page, notes or {})
    record = audit_page(page, note)
    record.update(notation, previous_max_defined_claim_characters=previous["max_defined_claim_characters"],
        previous_large_display_claims=previous["large_display_claims"])
    guide = render_guide(page, note, assets_prefix[:-7] + "reading/" if assets_prefix.endswith("assets/") else None)
    if notation["notation_compacted_claims"]:
        explanation = ('<p class="pr-meta">Long local formulas use this family’s existing definitions. '
                       'Each new abbreviation was expanded back to the identical native formula, including its free-variable context. '
                       'The original edition is preserved below.</p>')
        guide = guide.replace('<div class="pr-checkpoints">', explanation + '<div class="pr-checkpoints">', 1)
    preserved = source[page.proof_start:page.proof_end]
    raw_open = (EXACT_START + '<details class="pr-exact-script" data-reader-exact>'
                '<summary>Original ' + page.edition + ' command ledger · ' + str(len(page.lines)) + ' lines</summary>')
    replacement = guide + raw_open + preserved + RAW_CLOSE
    revised = source[:page.proof_start] + replacement + source[page.proof_end:]
    assets = (HEAD_START + f'<link rel="stylesheet" href="{escape(assets_prefix)}proof-reader.css?v={revision}">'
              f'<script defer src="{escape(assets_prefix)}proof-reader.js?v={revision}"></script>' + HEAD_END)
    revised = revised.replace("</head>", assets + "</head>")
    # Byte-level reversibility is stronger than comparing a loose HTML DOM.
    require(strip_reading_layer(revised.encode()) == raw, "reading layer failed exact recovery")
    return revised.encode(), record


def strip_reading_layer(raw):
    source = raw.decode("utf-8")
    for begin, end in ((HEAD_START, HEAD_END), (GUIDE_START, GUIDE_END)):
        require(source.count(begin) == source.count(end) == 1, "missing or duplicated reading boundary")
        left, right = source.index(begin), source.index(end) + len(end)
        source = source[:left] + source[right:]
    require(source.count(EXACT_START) == source.count(EXACT_END) == 1, "ambiguous original ledger wrapper")
    start = source.index(EXACT_START)
    first_list = source.index("<ol", start)
    source = source[:start] + source[first_list:]
    require(RAW_CLOSE in source, "missing original ledger end")
    source = source.replace(RAW_CLOSE, "", 1)
    return source.encode()
