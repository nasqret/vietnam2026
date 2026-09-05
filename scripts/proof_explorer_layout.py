"""Presentation-only repair for release notices inserted into explorer grids.

Keep the original Quadratic Reciprocity assets and all proof bytes intact.
Only a real, direct child release-notice opening tag receives an inline grid
span. It then occupies its own full-width row in both desktop and mobile grids.
"""
from html.parser import HTMLParser

NOTICE_STYLE = "grid-column: 1 / -1;"
VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())


class LayoutError(ValueError):
    pass


class _Notices(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.offsets = [0]
        for line in text.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.stack, self.edits = [], []
        self.notices = 0

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if (tag == "p" and self.stack and self.stack[-1] == "main"
                and "data-current-release" in values):
            if len(values) != len(attributes):
                raise LayoutError("duplicate release-notice attribute")
            self.notices += 1
            style = values.get("style")
            if style is not None and style.strip() != NOTICE_STYLE:
                raise LayoutError("release notice has an unexpected inline style")
            if style is None:
                raw = self.get_starttag_text()
                if not raw.endswith(">") or raw.endswith("/>"):
                    raise LayoutError("release notice is not an ordinary paragraph")
                line, column = self.getpos()
                start = self.offsets[line - 1] + column
                self.edits.append((start, start + len(raw),
                    raw[:-1] + ' style="' + NOTICE_STYLE + '">'))
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            raise LayoutError("unbalanced explorer HTML: " + tag)
        self.stack.pop()

    def handle_startendtag(self, tag, attributes):
        if tag == "p" and "data-current-release" in dict(attributes):
            raise LayoutError("release notice cannot be self-closing")


def repair_release_notices(payload):
    """Return (exact repaired bytes, notices seen, opening tags changed)."""
    if type(payload) is not bytes:
        raise LayoutError("explorer HTML must be exact bytes")
    if b"data-current-release" not in payload.lower():
        return payload, 0, 0
    text = payload.decode("utf-8")
    parser = _Notices(text)
    parser.feed(text)
    parser.close()
    if parser.stack:
        raise LayoutError("unclosed explorer HTML")
    for start, end, replacement in reversed(parser.edits):
        text = text[:start] + replacement + text[end:]
    return text.encode("utf-8"), parser.notices, len(parser.edits)
