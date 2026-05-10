import re


_HEADER_RE = re.compile(r"^\[(HIGH|MEDIUM|LOW) PRIORITY\]")
_ITEM_RE = re.compile(r"^\s*-\s+(.+)")


def parse_checklist(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    current_priority: str | None = None

    for line in text.splitlines():
        header_match = _HEADER_RE.match(line)
        if header_match:
            current_priority = header_match.group(1)
            continue

        item_match = _ITEM_RE.match(line)
        if item_match and current_priority:
            rows.append((current_priority, item_match.group(1).strip()))

    return rows
