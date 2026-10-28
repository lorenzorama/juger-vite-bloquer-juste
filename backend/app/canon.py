"""Ce qu'un humain voit d'un mail HTML, et tout ce que l'agent lit."""

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

ZERO_WIDTH = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")
HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0", re.IGNORECASE)
VOID_TAGS = {"br", "img", "hr", "meta", "link", "input", "wbr", "source"}
BLOCK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "table"}


@dataclass
class Canon:
    visible_text: str
    revealed_text: str
    hidden: list[str] = field(default_factory=list)


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[bool] = []
        self.visible: list[str] = []
        self.revealed: list[str] = []
        self.hidden: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self._newline()
        if tag not in VOID_TAGS:
            style = dict(attrs).get("style") or ""
            self.stack.append(bool(HIDDEN_STYLE.search(style)) or tag in {"script", "style"})

    def handle_endtag(self, tag):
        if tag not in VOID_TAGS and self.stack:
            self.stack.pop()
        if tag in BLOCK_TAGS:
            self._newline()

    def handle_data(self, data):
        if any(self.stack) and data.strip():
            self.hidden.append(data.strip())
            self.revealed.append(f"[HIDDEN] {data.strip()} [/HIDDEN]")
        else:
            self.visible.append(data)
            self.revealed.append(data)

    def handle_comment(self, data):
        if data.strip():
            self.hidden.append(data.strip())
            self.revealed.append(f"[HTML COMMENT] {data.strip()} [/HTML COMMENT]")

    def _newline(self):
        self.visible.append("\n")
        self.revealed.append("\n")


def _tidy(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def canonicalize(body_text: str = "", body_html: str | None = None) -> Canon:
    source = body_html or body_text
    zero_width = len(ZERO_WIDTH.findall(source))
    source = ZERO_WIDTH.sub("", source)
    if not body_html:
        return Canon(_tidy(source), _tidy(source))
    parser = _Parser()
    parser.feed(source)
    parser.close()
    revealed = _tidy("".join(parser.revealed))
    if zero_width:
        revealed += f"\n[{zero_width} zero-width character(s) removed]"
    return Canon(_tidy("".join(parser.visible)), revealed, parser.hidden)
