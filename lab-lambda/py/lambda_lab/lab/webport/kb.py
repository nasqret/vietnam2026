"""Browser port of the desktop ``kb`` command -- curated literature browser.

Pure-stdlib rendering of the desktop Knowledge Base registry
(``lambda_lab/lab/kb/`` on the desktop) over the frozen data in
:mod:`lambda_lab.lab.webport.data_kb`.

Subcommands (all pure; ``kb open`` degrades gracefully -- the browser
build cannot launch external programs, so it prints the link instead):

  kb                        -- overview panel + topic / concept listing
  kb help                   -- full command reference
  kb topics                 -- table of topics + resource counts
  kb topic <id>             -- topic + reading list (canon first)
                               [--difficulty 1-3] [--kind paper,book]
  kb show <id>              -- resource details (with its external link)
  kb open <id>              -- show the resource's external link
  kb search <kw>            -- full-text search  [--topic <id>]
                               [--kind ...] [--difficulty ...]   (alias: find)
  kb random [--topic <id>]  -- random recommendation
  kb bundles                -- curated reading paths
  kb bundle <id>            -- one reading path
  kb path <topic_id>        -- auto easy-to-hard path [--max n]
  kb stats                  -- statistics
  kb <name>                 -- concept / topic / resource lookup
"""

from __future__ import annotations

import random
import shlex
import textwrap
from typing import Callable, Dict, List, Optional, Tuple

from lambda_lab.lab.webport.data_kb import BUNDLES, CONCEPTS, RESOURCES, TOPICS

RESET = "\x1b[0m"


def _c(s: str, code: str) -> str:
    return f"\x1b[{code}m{s}{RESET}"


def bold(s: str) -> str: return _c(s, "1")
def dim(s: str) -> str: return _c(s, "2")
def green(s: str) -> str: return _c(s, "92")
def cyan(s: str) -> str: return _c(s, "96")
def yellow(s: str) -> str: return _c(s, "93")
def magenta(s: str) -> str: return _c(s, "95")
def red(s: str) -> str: return _c(s, "91")
def blue(s: str) -> str: return _c(s, "94")


NL = "\r\n"
WRAP = 76
MAX_SEARCH_HITS = 30


def _lines(*rows: str) -> str:
    return NL.join(rows)


def _wrap(text: str, indent: str = "  ") -> List[str]:
    out: List[str] = []
    for para in text.splitlines():
        if not para.strip():
            out.append("")
            continue
        out.extend(indent + w for w in textwrap.wrap(para, WRAP))
    return out


# ---------------------------------------------------------------------------
# Registry helpers over the frozen dicts (port of kb/registry.py)
# ---------------------------------------------------------------------------


def _authors_str(r: dict) -> str:
    return ", ".join(r.get("authors", ()))


def _best_target(r: dict) -> Optional[str]:
    """Priority order of the desktop, minus local PDFs (browser has none)."""
    if r.get("doi"):
        return f"https://doi.org/{r['doi']}"
    if r.get("arxiv"):
        return f"https://arxiv.org/abs/{r['arxiv']}"
    if r.get("url"):
        return r["url"]
    if r.get("isbn"):
        return f"https://isbnsearch.org/isbn/{r['isbn']}"
    return None


def _resources_for_topic(topic_id: str) -> List[str]:
    out = [rid for rid, r in RESOURCES.items() if topic_id in r.get("topics", ())]
    return sorted(out, key=lambda rid: (RESOURCES[rid]["diff"], RESOURCES[rid]["title"].lower()))


def _canonical(topic_id: str) -> List[str]:
    topic = TOPICS.get(topic_id)
    if topic is None:
        return []
    return [rid for rid in topic.get("canonical", ()) if rid in RESOURCES]


def _search(keyword: str, *, topic: Optional[str] = None) -> List[str]:
    """Case-insensitive scored substring search (title, authors, abstract, tags, id)."""
    kw = keyword.strip().lower()
    if not kw:
        return []
    scored: List[Tuple[int, str, str]] = []
    for rid, r in RESOURCES.items():
        if topic and topic not in r.get("topics", ()):
            continue
        score = 0
        if kw in r["title"].lower():
            score += 5
        if any(kw in a.lower() for a in r.get("authors", ())):
            score += 3
        if kw in r.get("abstract", "").lower():
            score += 2
        if any(kw in tag.lower() for tag in r.get("tags", ())):
            score += 2
        if kw in rid.lower():
            score += 1
        if score > 0:
            scored.append((-score, r["title"].lower(), rid))
    scored.sort()
    return [rid for _, _, rid in scored]


def _filter(
    *,
    topic: Optional[str] = None,
    kinds: Optional[List[str]] = None,
    min_difficulty: Optional[int] = None,
    max_difficulty: Optional[int] = None,
) -> List[str]:
    kinds_set = {k.strip().lower() for k in kinds if k.strip()} if kinds else None
    out = []
    for rid, r in RESOURCES.items():
        if topic and topic not in r.get("topics", ()):
            continue
        if kinds_set is not None and r["kind"].lower() not in kinds_set:
            continue
        if min_difficulty is not None and r["diff"] < min_difficulty:
            continue
        if max_difficulty is not None and r["diff"] > max_difficulty:
            continue
        out.append(rid)
    return sorted(out, key=lambda rid: (RESOURCES[rid]["diff"], RESOURCES[rid]["title"].lower()))


def _reading_path(topic_id: str, max_items: int = 10) -> List[str]:
    path = list(_canonical(topic_id))
    seen = set(path)
    for rid in _resources_for_topic(topic_id):
        if rid not in seen:
            path.append(rid)
            seen.add(rid)
    return path[:max_items]


# ---------------------------------------------------------------------------
# Argument helpers (port of commands/kb.py)
# ---------------------------------------------------------------------------


def _split_flags(args: List[str]) -> Tuple[List[str], Dict[str, str]]:
    """Minimal flag parser -- ``--foo bar`` and ``--foo=bar``."""
    pos: List[str] = []
    flags: Dict[str, str] = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            if "=" in a:
                k, v = a[2:].split("=", 1)
                flags[k] = v
            else:
                key = a[2:]
                if i + 1 < len(args) and not args[i + 1].startswith("--"):
                    flags[key] = args[i + 1]
                    i += 1
                else:
                    flags[key] = "1"
        else:
            pos.append(a)
        i += 1
    return pos, flags


def _parse_difficulty(value: str) -> Optional[Tuple[Optional[int], Optional[int]]]:
    """``"1-3"`` -> (1, 3); ``"2"`` -> (2, 2); ``""`` -> (None, None); bad -> None."""
    v = value.strip()
    if not v:
        return (None, None)
    if "-" in v:
        a, _, b = v.partition("-")
        try:
            return (int(a), int(b))
        except ValueError:
            return None
    try:
        n = int(v)
    except ValueError:
        return None
    return (n, n)


def _parse_kinds(value: str) -> List[str]:
    return [k.strip() for k in value.split(",") if k.strip()]


# ---------------------------------------------------------------------------
# Rendering helpers (port of kb/preview.py)
# ---------------------------------------------------------------------------


def _difficulty_marker(diff: int) -> str:
    diff = max(1, min(5, diff))
    return "*" * diff + "." * (5 - diff)


KIND_BADGES = {
    "book": "BOOK",
    "paper": "PAPER",
    "course": "COURSE",
    "website": "WEB",
    "video": "VIDEO",
    "blog": "BLOG",
    "thesis": "THESIS",
    "documentation": "DOCS",
    "manual": "MANUAL",
}


def _kind_badge(kind: str) -> str:
    return KIND_BADGES.get(kind, kind.upper()[:6])


def _trunc(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


Style = Optional[Callable[[str], str]]


def _table(title: str, headers: List[str], rows: List[List[str]],
           styles: List[Style]) -> List[str]:
    """Plain-text aligned table with per-column ANSI styling."""
    lines: List[str] = []
    if title:
        lines.append(bold(magenta(title)))
    if not rows:
        return lines
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    lines.append("  " + bold("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))))
    lines.append("  " + dim("-" * (sum(widths) + 2 * (len(widths) - 1))))
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            padded = cell.ljust(widths[i])
            style = styles[i] if i < len(styles) else None
            cells.append(style(padded) if style else padded)
        lines.append("  " + "  ".join(cells))
    return lines


def _resource_row(rid: str, *, with_diff: bool = True) -> List[str]:
    r = RESOURCES[rid]
    row = [rid, _kind_badge(r["kind"])]
    if with_diff:
        row.append(_difficulty_marker(r["diff"]))
    row.append(str(r["year"]) if r.get("year") else "-")
    row.append(_trunc(r["title"], 48))
    row.append(_trunc(_authors_str(r), 30))
    return row


def _render_resource(rid: str) -> List[str]:
    """Port of ``render_resource`` -- the full resource panel."""
    r = RESOURCES[rid]
    rows: List[str] = [bold(magenta(r["title"])) + "  " + dim(f"({rid})")]

    def meta(label: str, value: str) -> None:
        rows.append("  " + dim((label + ":").ljust(12)) + value)

    meta("Authors", _authors_str(r) or "-")
    meta("Year", str(r["year"]) if r.get("year") else "-")
    meta("Kind", magenta(_kind_badge(r["kind"])))
    meta("Difficulty", f"{_difficulty_marker(r['diff'])}  ({r['diff']}/5)")
    meta("License", r["license"])
    if r.get("pages"):
        meta("Pages", str(r["pages"]))
    if r.get("topics"):
        meta("Topics", ", ".join(green(t) for t in r["topics"]))
    if r.get("tags"):
        meta("Tags", ", ".join(r["tags"]))
    if r.get("doi"):
        meta("DOI", blue(f"https://doi.org/{r['doi']}"))
    if r.get("arxiv"):
        meta("arXiv", blue(f"https://arxiv.org/abs/{r['arxiv']}"))
    if r.get("isbn"):
        meta("ISBN", r["isbn"])
    if r.get("url"):
        meta("URL", blue(r["url"]))

    rows.append("")
    rows.append("  " + bold("Abstract"))
    rows.extend(_wrap(r.get("abstract", "").strip() or "-"))

    why = r.get("why", "").strip()
    if why:
        rows.append("")
        rows.append("  " + bold("Why it is here"))
        rows.extend(dim(line) if line else line for line in _wrap(why))

    if r.get("prereq"):
        rows.append("")
        rows.append("  " + dim("Prerequisites: ") + ", ".join(green(p) for p in r["prereq"]))
    if r.get("follow"):
        if not r.get("prereq"):
            rows.append("")
        rows.append("  " + dim("Follow-up: ") + ", ".join(green(f) for f in r["follow"]))
    return rows


def _render_topic(tid: str) -> List[str]:
    """Port of ``render_topic`` -- header panel + readings table (canon first)."""
    topic = TOPICS[tid]
    rows: List[str] = [bold(magenta(topic["title"])) + "  " + dim(f"({tid})"), ""]
    intro = topic.get("intro", "").strip()
    summary = topic.get("summary", "").strip()
    if intro:
        rows.extend(_wrap(intro))
    if summary:
        rows.append("")
        rows.extend(dim(line) if line else line for line in _wrap(summary))
    if topic.get("related_topics"):
        rows.append("")
        rows.append("  " + dim("Related topics: ") + ", ".join(green(t) for t in topic["related_topics"]))
    if topic.get("related_commands"):
        rows.append("  " + dim("Related REPL commands: ")
                    + ", ".join(yellow(c) for c in topic["related_commands"])
                    + dim("  (desktop build)"))

    canonical = _canonical(tid)
    canon_set = set(canonical)
    others = [rid for rid in _resources_for_topic(tid) if rid not in canon_set]
    ordered = canonical + others
    if ordered:
        rows.append("")
        rows.extend(_table(
            "Recommended readings (* = canon)",
            ["Can.", "ID", "Kind", "Difficulty", "Year", "Title", "Authors"],
            [["*" if rid in canon_set else ""] + _resource_row(rid) for rid in ordered],
            [yellow, green, magenta, dim, dim, None, dim],
        ))
    return rows


def _render_bundle(bid: str) -> List[str]:
    """Port of ``render_bundle`` -- header panel + ordered resources."""
    b = BUNDLES[bid]
    rows: List[str] = [bold(magenta(b["title"])) + "  " + dim(f"({bid})"), ""]
    desc = b.get("desc", "").strip()
    if desc:
        rows.extend(_wrap(desc))
        rows.append("")
    rows.append("  " + dim("Audience: ") + green(b["audience"])
                + "   " + dim("Estimated time: ") + green(f"{b['hours']} h"))
    rows.append("")
    body = []
    for idx, rid in enumerate(b.get("resources", ()), start=1):
        if rid not in RESOURCES:
            body.append([str(idx), rid, "?", "(missing from registry)", ""])
            continue
        r = RESOURCES[rid]
        body.append([str(idx), rid, _kind_badge(r["kind"]),
                     _trunc(r["title"], 48), _trunc(_authors_str(r), 30)])
    rows.extend(_table("Reading order", ["Step", "ID", "Kind", "Title", "Authors"],
                       body, [yellow, green, magenta, None, dim]))
    return rows


def _render_concept(key: str) -> List[str]:
    title, body, see = CONCEPTS[key]
    rows = [bold(magenta(title)), *_wrap(body)]
    if see:
        rows.append("  " + dim("Readings: ")
                    + ", ".join(yellow(f"kb topic {t}") for t in see))
    return rows


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------


def _cmd_overview(_args: List[str]) -> str:
    rows = [
        bold(magenta("Knowledge Base -- a literature companion"))
        + dim(f"  · {len(TOPICS)} topics · {len(RESOURCES)} resources · {len(BUNDLES)} bundles"),
        "",
        "  Curated library for lambda calculus, type theory, Curry-Howard,",
        "  Lean 4 and AI-driven mathematics. Suggested entry points:",
        "",
        "    " + yellow("kb topics") + "                -- list every topic",
        "    " + yellow("kb topic combinators") + "     -- deep dive into combinators",
        "    " + yellow("kb topic inductive-types") + " -- deep dive into inductive types",
        "    " + yellow("kb bundles") + "               -- curated reading paths",
        "    " + yellow("kb random") + "                -- random recommendation",
        "    " + yellow("kb search Curry-Howard") + "   -- full-text search",
        "",
        "  " + bold("Topics") + dim(" (kb topic <id>)"),
    ]
    tids = sorted(TOPICS)
    for i in range(0, len(tids), 3):
        rows.append("    " + "  ".join(green(t.ljust(24)) for t in tids[i:i + 3]))
    rows.append("")
    rows.append("  " + bold("Concepts") + dim(" (kb <name>)"))
    keys = list(CONCEPTS)
    for i in range(0, len(keys), 4):
        rows.append("    " + "  ".join(green(k) for k in keys[i:i + 4]))
    rows.append("")
    rows.append(dim("  Type ") + bold("kb help") + dim(" for the full command reference."))
    return _lines(*rows)


def _cmd_help(_args: List[str]) -> str:
    entries = [
        ("kb", "overview panel + topic / concept listing"),
        ("kb topics", "table of topics + resource counts"),
        ("kb topic <id>", "topic + readings [--difficulty 1-3] [--kind paper,book]"),
        ("kb show <id>", "resource details (with its external link)"),
        ("kb open <id>", "show the resource's external link"),
        ("kb search <kw>", "full-text search [--topic <id>] [--kind ...] [--difficulty ...]"),
        ("kb random", "random recommendation [--topic <id>]"),
        ("kb bundles", "curated reading paths"),
        ("kb bundle <id>", "one reading path"),
        ("kb path <topic_id>", "auto easy-to-hard reading path [--max n]"),
        ("kb stats", "knowledge base statistics"),
        ("kb <name>", "concept / topic / resource lookup"),
    ]
    rows = [bold(magenta("kb")) + dim(" -- knowledge base subcommands"), ""]
    for cmd, desc in entries:
        rows.append("  " + green(cmd.ljust(20)) + dim(desc))
    return _lines(*rows)


def _cmd_topics(_args: List[str]) -> str:
    if not TOPICS:
        return yellow("No topics found.")
    body = [[tid, _trunc(TOPICS[tid]["title"], 48), str(len(_resources_for_topic(tid)))]
            for tid in sorted(TOPICS)]
    return _lines(*_table("Topics in the knowledge base",
                          ["ID", "Title", "Resources"], body, [green, None, magenta]))


def _cmd_topic(args: List[str]) -> str:
    pos, flags = _split_flags(args)
    if not pos:
        return yellow("Usage: kb topic <id>. Example: `kb topic combinators`.")
    tid = pos[0]
    if tid not in TOPICS:
        return yellow(f"Unknown topic: {tid}. Try `kb topics`.")

    diff_filter = None
    if "difficulty" in flags:
        diff_filter = _parse_difficulty(flags["difficulty"])
        if diff_filter is None:
            return yellow(f"Invalid difficulty range: {flags['difficulty']}. "
                          "Use `1-3` or a single integer.")
    kind_filter = _parse_kinds(flags["kind"]) if "kind" in flags else None

    rows = _render_topic(tid)
    if diff_filter or kind_filter:
        filtered = _filter(
            topic=tid,
            kinds=kind_filter,
            min_difficulty=diff_filter[0] if diff_filter else None,
            max_difficulty=diff_filter[1] if diff_filter else None,
        )
        rows.append("")
        if not filtered:
            rows.append(dim("This topic has no resources yet."))
        else:
            rows.extend(_table(
                "Recommended readings (* = canon)",
                ["ID", "Kind", "Difficulty", "Year", "Title", "Authors"],
                [_resource_row(rid) for rid in filtered],
                [green, magenta, dim, dim, None, dim],
            ))
    return _lines(*rows)


def _show_resource_with_link(rid: str) -> str:
    rows = _render_resource(rid)
    target = _best_target(RESOURCES[rid])
    rows.append("")
    if target is None:
        rows.append("  " + dim("No URL/DOI/arXiv/ISBN -- nothing to open."))
    else:
        rows.append("  " + dim("Open in a new tab: ") + blue(target))
        rows.append("  " + dim("(the browser build cannot launch external programs)"))
    return _lines(*rows)


def _cmd_show(args: List[str]) -> str:
    pos, _flags = _split_flags(args)
    if not pos:
        return yellow("Usage: kb show <id>. Lists: `kb topic <id>` or `kb search ...`.")
    rid = pos[0]
    if rid not in RESOURCES:
        return yellow(f"Unknown resource: {rid}. Try `kb search ...` or `kb topic <id>`.")
    return _show_resource_with_link(rid)


def _cmd_open(args: List[str]) -> str:
    pos, _flags = _split_flags(args)
    if not pos:
        return yellow("Usage: kb open <id>.")
    rid = pos[0]
    if rid not in RESOURCES:
        return yellow(f"Unknown resource: {rid}.")
    target = _best_target(RESOURCES[rid])
    if target is None:
        return dim("No URL/DOI/arXiv/ISBN -- nothing to open.")
    return _lines(
        dim("The browser build cannot launch external programs."),
        "  " + dim("Open this link in a new tab: ") + blue(target),
    )


def _cmd_search(args: List[str]) -> str:
    pos, flags = _split_flags(args)
    if not pos:
        return yellow("Usage: kb search <keyword> [--topic <id>] "
                      "[--kind paper,book] [--difficulty 1-3].")
    kw = " ".join(pos)
    hits = _search(kw, topic=flags.get("topic"))
    if "difficulty" in flags:
        diff_filter = _parse_difficulty(flags["difficulty"])
        if diff_filter is None:
            return yellow(f"Invalid difficulty range: {flags['difficulty']}. "
                          "Use `1-3` or a single integer.")
        lo, hi = diff_filter
        if lo is not None:
            hits = [rid for rid in hits if RESOURCES[rid]["diff"] >= lo]
        if hi is not None:
            hits = [rid for rid in hits if RESOURCES[rid]["diff"] <= hi]
    if "kind" in flags:
        kinds = set(_parse_kinds(flags["kind"]))
        hits = [rid for rid in hits if RESOURCES[rid]["kind"] in kinds]
    if not hits:
        return dim(f"No matches for: {kw}.")
    rows = _table(
        f"Search results for: {kw} ({len(hits)})",
        ["ID", "Kind", "Year", "Title", "Authors"],
        [_resource_row(rid, with_diff=False) for rid in hits[:MAX_SEARCH_HITS]],
        [green, magenta, dim, None, dim],
    )
    if len(hits) > MAX_SEARCH_HITS:
        rows.append(dim(f"  … {len(hits) - MAX_SEARCH_HITS} more; "
                        "narrow with --topic / --kind / --difficulty."))
    rows.append(dim("  Details: ") + yellow("kb show <id>"))
    return _lines(*rows)


def _cmd_random(args: List[str]) -> str:
    _pos, flags = _split_flags(args)
    topic = flags.get("topic")
    candidates = list(RESOURCES)
    if topic:
        candidates = [rid for rid in candidates if topic in RESOURCES[rid].get("topics", ())]
    if not candidates:
        return dim("Empty knowledge base -- nothing to recommend.")
    rid = random.choice(candidates)
    return _lines(bold(magenta("Random recommendation")), "", _show_resource_with_link(rid))


def _cmd_bundles(_args: List[str]) -> str:
    if not BUNDLES:
        return yellow("No bundles found.")
    body = [[bid, _trunc(BUNDLES[bid]["title"], 44), BUNDLES[bid]["audience"],
             str(BUNDLES[bid]["hours"]), str(len(BUNDLES[bid].get("resources", ())))]
            for bid in sorted(BUNDLES)]
    rows = _table("Reading bundles", ["ID", "Title", "Audience", "Hours", "Resources"],
                  body, [green, None, magenta, dim, dim])
    rows.append(dim("  Details: ") + yellow("kb bundle <id>"))
    return _lines(*rows)


def _cmd_bundle(args: List[str]) -> str:
    pos, _flags = _split_flags(args)
    if not pos:
        return yellow("Usage: kb bundle <id>. Lists: `kb bundles`.")
    bid = pos[0]
    if bid not in BUNDLES:
        return yellow(f"Unknown bundle: {bid}. Try `kb bundles`.")
    return _lines(*_render_bundle(bid))


def _cmd_path(args: List[str]) -> str:
    pos, flags = _split_flags(args)
    if not pos:
        return yellow("Usage: kb path <topic_id>. Builds an easy-to-hard path.")
    tid = pos[0]
    if tid not in TOPICS:
        return yellow(f"Unknown topic: {tid}.")
    try:
        max_items = int(flags.get("max", "10"))
    except ValueError:
        max_items = 10
    path = _reading_path(tid, max_items=max_items)
    if not path:
        return dim("No resources to order for this topic yet.")
    body = []
    for idx, rid in enumerate(path, start=1):
        r = RESOURCES[rid]
        body.append([str(idx), rid, _kind_badge(r["kind"]),
                     _difficulty_marker(r["diff"]), _trunc(r["title"], 48)])
    return _lines(*_table(f"Reading path: {tid}",
                          ["Step", "ID", "Kind", "Difficulty", "Title"],
                          body, [yellow, green, magenta, dim, None]))


def _cmd_stats(_args: List[str]) -> str:
    by_kind: Dict[str, int] = {}
    by_topic: Dict[str, int] = {}
    by_difficulty: Dict[int, int] = {}
    by_license: Dict[str, int] = {}
    for r in RESOURCES.values():
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
        by_difficulty[r["diff"]] = by_difficulty.get(r["diff"], 0) + 1
        by_license[r["license"]] = by_license.get(r["license"], 0) + 1
        for tid in r.get("topics", ()):
            by_topic[tid] = by_topic.get(tid, 0) + 1
    rows = [
        bold(magenta("Knowledge base statistics")),
        f"  Topics: {bold(str(len(TOPICS)))}   Resources: {bold(str(len(RESOURCES)))}"
        f"   Bundles: {bold(str(len(BUNDLES)))}",
    ]

    def section(title: str, mapping: Dict, sort_by_key: bool = False) -> None:
        rows.append("")
        rows.append("  " + bold(title))
        items = sorted(mapping.items(), key=(lambda kv: kv[0]) if sort_by_key
                       else (lambda kv: -kv[1]))
        for k, v in items:
            rows.append("    " + green(str(k).ljust(26)) + str(v))

    section("By kind", by_kind)
    section("By topic", by_topic)
    section("By difficulty", by_difficulty, sort_by_key=True)
    section("By license", by_license)
    return _lines(*rows)


# ---------------------------------------------------------------------------
# Lookup fallback: kb <name> -> concept | topic | resource
# ---------------------------------------------------------------------------


def _lookup(raw: str) -> str:
    q = raw.strip().lower().replace(" ", "-")
    if q in CONCEPTS:
        return _lines(*_render_concept(q))
    if q in TOPICS:
        return _cmd_topic([q])
    if q in RESOURCES:
        return _show_resource_with_link(q)
    # Fuzzy: prefix first, then substring, over concepts -> topics -> resources.
    for pool, view in ((CONCEPTS, lambda k: _lines(*_render_concept(k))),
                       (TOPICS, lambda k: _cmd_topic([k])),
                       (RESOURCES, _show_resource_with_link)):
        key = next((k for k in pool if k.startswith(q)), None)
        if key is not None:
            return view(key)
    for pool, view in ((CONCEPTS, lambda k: _lines(*_render_concept(k))),
                       (TOPICS, lambda k: _cmd_topic([k])),
                       (RESOURCES, _show_resource_with_link)):
        key = next((k for k in pool if q in k), None)
        if key is not None:
            return view(key)
    return (red(f"No entry for {raw.strip()!r}. ")
            + dim("Try ") + bold("kb") + dim(", ") + bold("kb topics")
            + dim(" or ") + bold("kb search <text>") + dim("."))


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


SUBCOMMANDS: Dict[str, Callable[[List[str]], str]] = {
    "help": _cmd_help,
    "topics": _cmd_topics,
    "topic": _cmd_topic,
    "show": _cmd_show,
    "open": _cmd_open,
    "search": _cmd_search,
    "find": _cmd_search,
    "random": _cmd_random,
    "bundles": _cmd_bundles,
    "bundle": _cmd_bundle,
    "path": _cmd_path,
    "stats": _cmd_stats,
}


def handle(arg: str, state: Optional[dict] = None) -> str:
    """Entry point for the browser driver: ``kb <arg>``.

    ``state`` is accepted for driver compatibility but unused -- every ``kb``
    subcommand is a pure, single-shot query.
    """
    del state
    arg = (arg or "").strip()
    if not arg:
        return _cmd_overview([])
    try:
        parts = shlex.split(arg)
    except ValueError as e:
        return red(f"Argument parsing error: {e}")
    if not parts:
        return _cmd_overview([])
    sub, rest = parts[0], parts[1:]
    handler = SUBCOMMANDS.get(sub)
    if handler is not None:
        return handler(rest)
    return _lookup(arg)
