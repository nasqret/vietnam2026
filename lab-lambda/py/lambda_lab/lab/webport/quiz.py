"""Browser port of the desktop Lambda Lab ``quiz`` command family.

Ported from ``lambda_lab/lab/commands/quiz.py`` + ``lambda_lab/lab/quiz/``
(loader / registry / matcher / validators / fullscreen wording). The
desktop batch session becomes a line-by-line flow driven through
``handle(arg, state)``: the driver persists ``state`` across lines.

Commands:
  quiz                 ask the next question (auto-starts the default bundle)
  quiz <bundle-id>     switch to a bundle and start a fresh session
  quiz bundles         list the frozen bundles
  quiz score           session score history (``quiz score reset`` clears)
  quiz topics          question counts by topic
  quiz types           question counts by type
  quiz hint            hint for the pending question
  quiz skip | stop     skip the pending question | end the session
  quiz help            summary of the above

Answers are checked locally, as in the pure parts of the desktop matcher:
exact / whitespace / α-equivalence / α-equivalence after β-normalisation
(via ``lc.alpha_eq`` after ``lc.normalize_checked``) / substring; numeric
answers work because integer literals and Church constants are expanded
before parsing. The desktop LLM judge (``--online``) degrades to this
local checking with a one-line notice.

Data files are frozen into ``data_quiz.py`` (no JSON/YAML at runtime).
All state lives under keys prefixed ``webquiz_``.
"""

from __future__ import annotations

import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from lambda_lab.lab import church, lc
from lambda_lab.lab.parser import parse
from lambda_lab.lab.webport.data_quiz import BUNDLES, DEFAULT_BUNDLE, QUESTIONS

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


def _lines(*rows: str) -> str:
    return NL.join(rows)


MAX_NORMALIZE = 1_000
MAX_NODES = 50_000
MAX_NUMERAL = 200
MAX_SHOW = 120

_BUNDLE_BY_ID = {b["id"]: b for b in BUNDLES}
_Q_BY_ID = {q["id"]: q for q in QUESTIONS}

TYPE_LABELS = {
    "open": "open",
    "mc": "multiple choice",
    "tf": "true/false",
    "completion": "completion",
    "code": "λ-code",
}

METHOD_LABELS = {
    "exact": "exact match",
    "whitespace": "matched after whitespace",
    "alpha": "α-equivalent",
    "alpha+beta": "α-equivalent after β-reduction",
    "substring": "substring",
}

_TRUE_WORDS = ("t", "true", "yes", "y", "1", "tak", "prawda")
_FALSE_WORDS = ("f", "false", "no", "n", "0", "nie", "falsz")

_NUM_RE = re.compile(r"(?<![\w'])\d+(?![\w'])")


# ---------------------------------------------------------------------------
# Matcher (port of lambda_lab/lab/quiz/matcher.py; parse also expands
# integer literals and named Church constants, as the desktop validators do)
# ---------------------------------------------------------------------------


def _expand_numbers(src: str) -> str:
    def repl(match: "re.Match[str]") -> str:
        n = int(match.group())
        if n > MAX_NUMERAL:
            raise ValueError(f"numeral {n} too large")
        return f"({church.church_numeral_src(n)})"

    return _NUM_RE.sub(repl, src)


def _try_parse(s: str, expand: bool = True):
    if not s:
        return None
    if expand:
        try:
            return parse(church.expand_named(_expand_numbers(s)))
        except Exception:
            pass
    try:
        return parse(s)
    except Exception:
        return None


def _normal_or_self(t):
    result = lc.normalize_checked(t, max_steps=200, max_nodes=MAX_NODES)
    return result.term if result.complete else t


def _normalize_whitespace(s: str) -> str:
    return " ".join((s or "").split())


def answers_match(user_str: str, answer_str: str) -> Tuple[bool, str]:
    """Return ``(matched, method)`` — same strategy ladder as the desktop:
    literal, whitespace, α-equivalence, α-equivalence after β-normalising
    both sides, then case-insensitive substring for text answers."""
    user_compact = (user_str or "").strip()
    if not user_compact:
        return False, "empty"
    answer_compact = (answer_str or "").strip()

    if user_compact == answer_compact:
        return True, "exact"
    if _normalize_whitespace(user_compact) == _normalize_whitespace(answer_compact):
        return True, "whitespace"

    user_term = _try_parse(user_compact)
    answer_term = _try_parse(answer_compact)
    if user_term is not None and answer_term is not None:
        if lc.alpha_eq(user_term, answer_term):
            return True, "alpha"
        if lc.alpha_eq(_normal_or_self(user_term), _normal_or_self(answer_term)):
            return True, "alpha+beta"

    u = _normalize_whitespace(user_compact).lower()
    a = _normalize_whitespace(answer_compact).lower()
    if u and u in a:
        return True, "substring"
    return False, "none"


def strict_match(user_str: str, answer_str: str) -> bool:
    """Whitespace-normalised literal match (desktop ``quiz --strict``)."""
    return (_normalize_whitespace(user_str) == _normalize_whitespace(answer_str)
            and bool((user_str or "").strip()))


# ---------------------------------------------------------------------------
# Validators for `code` questions (port of lambda_lab/lab/quiz/validators.py)
# ---------------------------------------------------------------------------


def _safe_parse(src: str):
    try:
        return parse(church.expand_named(_expand_numbers(src))), None
    except Exception as exc:
        return None, str(exc)


def _safe_normalize(term, max_steps: int):
    try:
        result = lc.normalize_checked(term, max_steps=max_steps, max_nodes=MAX_NODES)
    except Exception as exc:
        return None, str(exc)
    if not result.complete:
        return None, "reduction limit reached"
    return result.term, None


def _v_decode_numeral_eq(user: str, expected: Any, *, max_steps: int = 1000) -> Tuple[bool, str]:
    try:
        target = int(expected)
    except (TypeError, ValueError):
        return False, "bad-expected"
    term, err = _safe_parse(user)
    if term is None:
        return False, f"parse-error: {err}"
    norm, err = _safe_normalize(term, max_steps)
    if norm is None:
        return False, f"normalize-error: {err}"
    decoded = church.try_decode_numeral(norm)
    if decoded is None:
        return False, "not-a-numeral"
    if decoded != target:
        return False, f"got {decoded}, expected {target}"
    return True, f"decoded numeral {decoded}"


def _v_decode_bool_eq(user: str, expected: Any, *, max_steps: int = 1000) -> Tuple[bool, str]:
    if isinstance(expected, bool):
        target = expected
    elif isinstance(expected, str):
        low = expected.strip().lower()
        if low in ("true", "t", "1", "yes"):
            target = True
        elif low in ("false", "f", "0", "no"):
            target = False
        else:
            return False, "bad-expected"
    else:
        return False, "bad-expected"
    term, err = _safe_parse(user)
    if term is None:
        return False, f"parse-error: {err}"
    norm, err = _safe_normalize(term, max_steps)
    if norm is None:
        return False, f"normalize-error: {err}"
    decoded = church.try_decode_bool(norm)
    if decoded is None:
        return False, "not-a-boolean"
    if decoded != target:
        return False, f"got {decoded}, expected {target}"
    return True, f"decoded boolean {decoded}"


def _v_alpha_equiv_to(user: str, expected: Any, *, max_steps: int = 1000) -> Tuple[bool, str]:
    if not isinstance(expected, str):
        return False, "bad-expected"
    user_term, err = _safe_parse(user)
    if user_term is None:
        return False, f"parse-error: {err}"
    expected_term, err = _safe_parse(expected)
    if expected_term is None:
        return False, f"bad-expected: {err}"
    user_norm, err = _safe_normalize(user_term, max_steps)
    if user_norm is None:
        return False, f"normalize-error: {err}"
    expected_norm, err = _safe_normalize(expected_term, max_steps)
    if expected_norm is None:
        return False, f"bad-expected: {err}"
    if lc.alpha_eq(user_norm, expected_norm):
        return True, "alpha-equivalent"
    if lc.alpha_eq(user_term, expected_term):
        return True, "alpha-equivalent"
    return False, "not-alpha-equivalent"


def _v_reduces_to_var(user: str, expected: Any, *, max_steps: int = 1000) -> Tuple[bool, str]:
    if not isinstance(expected, str) or not expected:
        return False, "bad-expected"
    term, err = _safe_parse(user)
    if term is None:
        return False, f"parse-error: {err}"
    norm, err = _safe_normalize(term, max_steps)
    if norm is None:
        return False, f"normalize-error: {err}"
    if isinstance(norm, lc.Var) and norm.name == expected:
        return True, f"reduced to {expected}"
    return False, "did-not-reduce-to-var"


VALIDATORS = {
    "decode_numeral_eq": _v_decode_numeral_eq,
    "decode_bool_eq": _v_decode_bool_eq,
    "alpha_equiv_to": _v_alpha_equiv_to,
    "reduces_to_var": _v_reduces_to_var,
}


def run_validator(name: str, user: str, expected: Any, *, max_steps: int = 1000) -> Tuple[bool, str]:
    fn = VALIDATORS.get(name)
    if fn is None:
        return False, f"unknown-validator: {name}"
    try:
        return fn(user, expected, max_steps=max_steps)
    except Exception as exc:
        return False, f"validator-crash: {exc}"


# ---------------------------------------------------------------------------
# Grading (port of commands/quiz.py _grade family)
# ---------------------------------------------------------------------------


def _grade(q: Dict[str, Any], user: str, *, strict: bool = False) -> Tuple[bool, str]:
    qtype = q["type"]
    if qtype == "open":
        if strict:
            ok = strict_match(user, q.get("answer") or "")
            return ok, ("exact match" if ok else "")
        ok, method = answers_match(user, q.get("answer") or "")
        return (True, METHOD_LABELS.get(method, method)) if ok else (False, "")
    if qtype == "mc":
        u = (user or "").strip().upper()
        labels = "ABCDEFGH"
        if not u or u[0] not in labels:
            return False, ""
        return labels.index(u[0]) == q.get("correct"), ""
    if qtype == "tf":
        low = (user or "").strip().lower()
        if low in _TRUE_WORDS:
            ans = True
        elif low in _FALSE_WORDS:
            ans = False
        else:
            return False, ""
        return ans == q.get("answer"), ""
    if qtype == "completion":
        answers = q.get("answers") or []
        user_norm = (user or "").strip()
        if not answers or not user_norm:
            return False, ""
        method = (q.get("match_method") or "smart").lower()
        if method == "exact":
            return any(user_norm == c for c in answers), ""
        if method == "alpha":
            return any(answers_match(user_norm, c)[0] for c in answers), ""
        low = user_norm.lower()
        for cand in answers:
            if low == cand.lower() or answers_match(user_norm, cand)[0]:
                return True, ""
        return False, ""
    if qtype == "code":
        if not (q.get("validator") and q.get("expected") is not None):
            return False, "missing-validator"
        return run_validator(q["validator"], user, q["expected"],
                             max_steps=q.get("max_steps", 1000))
    return False, ""


def _canonical_answer(q: Dict[str, Any]) -> str:
    """Port of fullscreen._format_correct_answer / feedback_panel."""
    qtype = q["type"]
    if qtype == "mc" and q.get("correct") is not None:
        choices = q.get("choices") or []
        idx = q["correct"]
        text = choices[idx] if 0 <= idx < len(choices) else "?"
        return f"{'ABCDEFGH'[idx]}) {text}"
    if qtype == "tf":
        return "TRUE" if q.get("answer") else "FALSE"
    if qtype == "completion" and q.get("answers"):
        answers = q["answers"]
        return " · ".join(answers[:3]) + ("…" if len(answers) > 3 else "")
    if qtype == "code":
        return f"λ-term reducing to {q.get('expected')}"
    return str(q.get("answer") or "?")


def _clip(s: str) -> str:
    return s if len(s) <= MAX_SHOW else s[:MAX_SHOW] + "…"


def _alpha_note(user: str, answer: str) -> Optional[str]:
    """Desktop show_alpha_note: display both forms when they differ."""
    u = _try_parse(user)
    a = _try_parse(answer)
    if u is not None and a is not None:
        pu, pa = lc.pretty(u), lc.pretty(a)
        if pu != pa:
            return dim("(α-equivalent — your form: ") + cyan(_clip(pu)) + \
                dim(", canonical: ") + cyan(_clip(pa)) + dim(")")
    return None


# ---------------------------------------------------------------------------
# Session state (all keys prefixed webquiz_)
# ---------------------------------------------------------------------------


def _score0() -> Dict[str, Any]:
    return {"asked": 0, "correct": 0, "skipped": 0, "by_topic": {}, "by_type": {}}


def pending(state: dict) -> bool:
    """True when a question is awaiting an answer (driver routing helper)."""
    return bool(state.get("webquiz_current"))


def _run_active(state: dict) -> bool:
    return bool(state.get("webquiz_queue")) or pending(state)


def _difficulty_stars(d: int) -> str:
    d = max(1, min(5, int(d)))
    return "*" * d + "-" * (5 - d)


def _start_run(state: dict, bundle: Dict[str, Any]) -> List[str]:
    lo, hi = list(bundle.get("difficulty") or [1, 5])[:2]
    topics = bundle.get("topics") or []
    types = bundle.get("types") or []
    pool = [q for q in QUESTIONS
            if (not topics or q["topic"] in topics)
            and (not types or q["type"] in types)
            and lo <= q["difficulty"] <= hi]
    if not pool:
        return [red("No questions match the filter.")]
    rng = random.Random(state.get("webquiz_seed"))
    n = bundle.get("n_questions", 10)
    if n >= len(pool):
        rng.shuffle(pool)
        chosen = pool
    else:
        chosen = rng.sample(pool, n)
    state["webquiz_bundle"] = bundle["id"]
    state["webquiz_queue"] = [q["id"] for q in chosen]
    state["webquiz_total"] = len(chosen)
    state["webquiz_idx"] = 0
    state["webquiz_current"] = None
    state["webquiz_score"] = _score0()
    state["webquiz_t0"] = time.time()

    run_topics = sorted({q["topic"] for q in chosen})
    run_types = sorted({q["type"] for q in chosen})
    rows = [
        bold(magenta("Quiz session")) + dim(" · " + bundle["title"]),
        dim("  Bundle: ") + cyan(bundle["id"]),
        dim("  Questions: ") + str(len(chosen)),
        dim("  Topics: ") + (", ".join(run_topics) or "(any)"),
        dim("  Types: ") + (", ".join(run_types) or "(any)"),
        dim("  Controls: answer each question · ") + yellow("quiz skip")
        + dim(" · ") + yellow("quiz stop") + dim("."),
        "",
    ]
    rows.extend(_advance(state))
    return rows


def _question_lines(state: dict, q: Dict[str, Any]) -> List[str]:
    idx, total = state.get("webquiz_idx", 1), state.get("webquiz_total", 1)
    header = (bold(magenta("Quiz"))
              + dim(f" · Question {idx}/{total} · Topic: {q['topic']}"
                    f" · Type: {TYPE_LABELS.get(q['type'], q['type'])}"
                    f" · Difficulty: {_difficulty_stars(q['difficulty'])}"))
    rows = [header, "  " + q["prompt"]]
    if q["type"] == "mc":
        rows.append("")
        for i, choice in enumerate(q.get("choices") or []):
            rows.append("    " + green("ABCDEFGH"[i] + ".") + " " + choice)
        rows.append(dim("  Answer with a letter (A, B, …)."))
    elif q["type"] == "tf":
        rows.append(dim("  Enter T/F (or yes/no, 1/0)."))
    elif q["type"] == "completion":
        rows.append(dim("  Fill in the missing word / expression."))
    elif q["type"] == "code":
        rows.append(dim("  Write a full λ-term (Church constants are recognised)."))
    return rows


def _advance(state: dict) -> List[str]:
    queue = state.get("webquiz_queue") or []
    if not queue:
        return _final_lines(state)
    qid = queue.pop(0)
    state["webquiz_queue"] = queue
    state["webquiz_current"] = qid
    state["webquiz_idx"] = state.get("webquiz_idx", 0) + 1
    return _question_lines(state, _Q_BY_ID[qid])


def _final_lines(state: dict) -> List[str]:
    score = state.get("webquiz_score") or _score0()
    state["webquiz_current"] = None
    state["webquiz_queue"] = []
    asked = score["asked"]
    if asked == 0:
        return [dim("quiz closed.")]
    correct = score["correct"]
    pct = round(100 * correct / asked, 1) if asked else 0.0
    duration = int(time.time() - state.get("webquiz_t0", time.time()))
    color = green if pct >= 60 else yellow
    rows = [
        bold(magenta("Final score")) + dim(" · " + str(state.get("webquiz_bundle") or "-")),
        "  " + color(f"Correct: {correct}/{asked} ({pct}%)"),
        "  " + dim(f"Skipped: {score['skipped']}"),
        "  " + dim(f"Duration: {duration} s"),
        "  " + dim("By topic:"),
    ]
    for topic, (n, c) in sorted(score["by_topic"].items()):
        rows.append(f"    {topic:<18s} {c}/{n}")
    rows.append("  " + dim("By type:"))
    for typ, (n, c) in sorted(score["by_type"].items()):
        rows.append(f"    {typ:<18s} {c}/{n}")
    rows.append(dim("  type ") + yellow("quiz") + dim(" for another round or ")
                + yellow("quiz bundles") + dim(" to switch."))
    attempts = state.setdefault("webquiz_attempts", [])
    attempts.append({
        "bundle": state.get("webquiz_bundle"),
        "n_questions": asked,
        "n_correct": correct,
        "n_skipped": score["skipped"],
        "duration_sec": duration,
    })
    state["webquiz_score"] = _score0()
    return rows


def _tally(state: dict, q: Dict[str, Any], *, correct: bool, skipped: bool) -> None:
    score = state.setdefault("webquiz_score", _score0())
    score["asked"] += 1
    if skipped:
        score["skipped"] += 1
    by_topic = score["by_topic"].setdefault(q["topic"], [0, 0])
    by_type = score["by_type"].setdefault(q["type"], [0, 0])
    by_topic[0] += 1
    by_type[0] += 1
    if correct:
        score["correct"] += 1
        by_topic[1] += 1
        by_type[1] += 1


def _answer(state: dict, q: Dict[str, Any], user: str) -> List[str]:
    ok, detail = _grade(q, user, strict=bool(state.get("webquiz_strict")))
    _tally(state, q, correct=ok, skipped=False)
    state["webquiz_current"] = None
    rows: List[str] = []
    if ok:
        head = green("✓ Correct!")
        if detail:
            head += " " + dim(f"({detail})")
        rows.append(head)
        if q["type"] == "open" and detail in ("α-equivalent", "α-equivalent after β-reduction"):
            note = _alpha_note(user, q.get("answer") or "")
            if note:
                rows.append("  " + note)
    else:
        rows.append(red("✗ Incorrect"))
        rows.append("  " + yellow("Canonical answer: ") + cyan(_canonical_answer(q)))
        if detail:
            rows.append("  " + dim(f"({detail})"))
    expl = q.get("explanation")
    if expl:
        rows.append("  " + dim(expl))
    rows.append("")
    rows.extend(_advance(state))
    return rows


def _skip(state: dict) -> List[str]:
    qid = state.get("webquiz_current")
    if not qid:
        return [dim("Nothing to skip — no question is pending.")]
    q = _Q_BY_ID[qid]
    _tally(state, q, correct=False, skipped=True)
    state["webquiz_current"] = None
    rows = [yellow("↷ Skipped."),
            "  " + dim("Canonical answer: ") + cyan(_canonical_answer(q)), ""]
    rows.extend(_advance(state))
    return rows


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------


def _cmd_bundles(state: dict) -> List[str]:
    current = state.get("webquiz_bundle") or DEFAULT_BUNDLE
    rows = [bold(magenta("Question bundles"))]
    for b in BUNDLES:
        marker = green("→ ") if b["id"] == current else "  "
        rows.append(marker + green(f"{b['id']:<22s}") + bold(b["title"])
                    + dim(f"  · {b['n_questions']} q · {b['duration_min']} min"))
        rows.append("      " + dim(b["description"]))
    rows.append(dim("Switch with ") + yellow("quiz <bundle-id>") + dim("."))
    return rows


def _cmd_topics(state: dict) -> List[str]:
    del state
    counts: Dict[str, int] = {}
    for q in QUESTIONS:
        counts[q["topic"]] = counts.get(q["topic"], 0) + 1
    rows = [bold(magenta("Quiz topics"))]
    for topic, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        rows.append("  " + green(f"{topic:<16s}") + str(n))
    return rows


def _cmd_types(state: dict) -> List[str]:
    del state
    counts: Dict[str, int] = {}
    for q in QUESTIONS:
        counts[q["type"]] = counts.get(q["type"], 0) + 1
    rows = [bold(magenta("Question types"))]
    for typ, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        rows.append("  " + green(f"{typ:<12s}") + dim(f"{TYPE_LABELS.get(typ, typ):<18s}") + str(n))
    return rows


def _cmd_score(state: dict, rest: str) -> List[str]:
    if rest.strip().lstrip("-") == "reset":
        state["webquiz_attempts"] = []
        state["webquiz_score"] = _score0()
        return [green("Score history reset.")]
    attempts = state.get("webquiz_attempts") or []
    rows = [bold(magenta("Quiz score")) + dim(" · this browser session")]
    if not attempts:
        rows.append(dim("  No finished sessions yet."))
    for i, a in enumerate(attempts, start=1):
        n = a["n_questions"]
        pct = round(100 * a["n_correct"] / n) if n else 0
        rows.append(f"  {i:>2d}. " + green(f"{(a['bundle'] or '-'):<22s}")
                    + f"{a['n_correct']}/{n}  {pct}%"
                    + dim(f"  · skipped {a['n_skipped']} · {a['duration_sec']}s"))
    score = state.get("webquiz_score")
    if score and score["asked"]:
        rows.append(dim("  In progress: ")
                    + f"{score['correct']}/{score['asked']} correct"
                    + dim(f" · bundle {state.get('webquiz_bundle') or '-'}"))
    rows.append(dim("  Reset with ") + yellow("quiz score reset") + dim("."))
    return rows


def _cmd_hint(state: dict) -> List[str]:
    qid = state.get("webquiz_current")
    if not qid:
        return [dim("No question is pending — type ") + bold("quiz") + dim(" first.")]
    hint = _Q_BY_ID[qid].get("hint")
    if not hint:
        return [dim("(no hint for this question)")]
    return [yellow("💡 ") + hint]


def _cmd_help(state: dict) -> List[str]:
    del state
    return [
        bold(magenta("quiz")) + " — question bundles from the desktop Lambda Lab",
        f"  {green('quiz')}               ask the next question (auto-starts "
        + cyan(DEFAULT_BUNDLE) + ")",
        f"  {green('quiz <bundle-id>')}   switch bundle and start a session",
        f"  {green('quiz bundles')}       list bundles",
        f"  {green('quiz score')}         session score history " + dim("(quiz score reset)"),
        f"  {green('quiz topics')}        question counts by topic",
        f"  {green('quiz types')}         question counts by type",
        f"  {green('quiz hint')}          hint for the pending question",
        f"  {green('quiz skip')} / {green('quiz stop')}  skip the question / end the session",
        dim("  Answers are checked locally: exact · numeric · α/β-equivalence."),
        dim("  The desktop LLM judge (--online) is not available in the browser."),
    ]


def _cmd_stop(state: dict) -> List[str]:
    if not _run_active(state) and not (state.get("webquiz_score") or {}).get("asked"):
        state["webquiz_current"] = None
        return [dim("quiz closed.")]
    return _final_lines(state)


_STOP_WORDS = ("stop", "quit", "exit", "off", "q")
_SKIP_WORDS = ("skip", "s")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def handle(arg: str, state: dict) -> str:
    """Handle one ``quiz`` line. ``state`` is the driver-persisted dict."""
    arg = (arg or "").strip()
    low = arg.lower()
    head = low.split()[0] if low else ""

    notices: List[str] = []
    if head.startswith("--"):
        flags = low.split()
        if "--online" in flags:
            notices.append(yellow("--online (LLM judge) is not available in the "
                                  "browser; using local α/β-equivalence checking."))
        if "--strict" in flags:
            state["webquiz_strict"] = True
            notices.append(yellow("Strict matching enabled for this session "
                                  "(literal match only)."))
        unknown = [f for f in flags if f not in ("--online", "--strict")]
        if unknown:
            notices.append(red(f"Unknown flag {unknown[0]!r}."))
        arg, low, head = "", "", ""

    if head in ("bundles", "bundle") and low in ("bundles", "bundle"):
        return _lines(*_cmd_bundles(state))
    if head in ("score", "history"):
        rest = arg.split(None, 1)[1] if len(arg.split(None, 1)) > 1 else ""
        return _lines(*_cmd_score(state, rest.lower()))
    if low == "topics":
        return _lines(*_cmd_topics(state))
    if low == "types":
        return _lines(*_cmd_types(state))
    if low in ("help", "?"):
        return _lines(*_cmd_help(state))
    if low == "hint":
        return _lines(*_cmd_hint(state))
    if low in _STOP_WORDS:
        return _lines(*_cmd_stop(state))
    if low in _SKIP_WORDS:
        return _lines(*_skip(state))
    if low in _BUNDLE_BY_ID:
        return _lines(*(notices + _start_run(state, _BUNDLE_BY_ID[low])))

    if pending(state) and arg:
        q = _Q_BY_ID[state["webquiz_current"]]
        return _lines(*_answer(state, q, arg))

    if not arg or low == "next":
        if pending(state):
            rows = notices + [dim("(current question repeated — it is still waiting "
                                  "for your answer)")]
            rows += _question_lines(state, _Q_BY_ID[state["webquiz_current"]])
            return _lines(*rows)
        if state.get("webquiz_queue"):
            return _lines(*(notices + _advance(state)))
        bundle = _BUNDLE_BY_ID.get(state.get("webquiz_bundle") or DEFAULT_BUNDLE,
                                   _BUNDLE_BY_ID[DEFAULT_BUNDLE])
        return _lines(*(notices + _start_run(state, bundle)))

    return _lines(
        red(f"No quiz subcommand or bundle named {arg!r}."),
        dim("Try ") + yellow("quiz help") + dim(" or ") + yellow("quiz bundles") + dim("."),
    )
