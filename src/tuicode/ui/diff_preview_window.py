"""Read-only Git diff preview window — split (side-by-side) view."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static

from tuicode.ui.float_window import FloatWindow


@dataclass
class _DiffRow:
    kind: str  # header | hunk | context | removed | added | changed
    old_no: Optional[int] = None
    old_text: str = ""
    new_no: Optional[int] = None
    new_text: str = ""
    raw: str = ""


def _parse_diff(diff: str) -> list[_DiffRow]:
    """Parse unified diff text into structured rows for split display."""
    rows: list[_DiffRow] = []
    old_no = 0
    new_no = 0
    pending_rem: list[tuple[int, str]] = []

    def flush(added: list[tuple[int, str]]) -> None:
        n = max(len(pending_rem), len(added)) if (pending_rem or added) else 0
        for j in range(n):
            has_r = j < len(pending_rem)
            has_a = j < len(added)
            if has_r and has_a:
                rows.append(_DiffRow("changed", pending_rem[j][0], pending_rem[j][1], added[j][0], added[j][1]))
            elif has_r:
                rows.append(_DiffRow("removed", pending_rem[j][0], pending_rem[j][1]))
            else:
                rows.append(_DiffRow("added", new_no=added[j][0], new_text=added[j][1]))
        pending_rem.clear()

    i = 0
    lines = diff.splitlines()
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff ") or line.startswith("index ") or line.startswith("---") or line.startswith("+++"):
            flush([])
            rows.append(_DiffRow("header", raw=line))
            i += 1
        elif line.startswith("@@"):
            flush([])
            rows.append(_DiffRow("hunk", raw=line))
            m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if m:
                old_no = int(m.group(1))
                new_no = int(m.group(2))
            i += 1
        elif line.startswith("-"):
            pending_rem.append((old_no, line[1:]))
            old_no += 1
            i += 1
        elif line.startswith("+"):
            added: list[tuple[int, str]] = []
            while i < len(lines) and lines[i].startswith("+"):
                added.append((new_no, lines[i][1:]))
                new_no += 1
                i += 1
            flush(added)
        elif line.startswith(" "):
            flush([])
            rows.append(_DiffRow("context", old_no, line[1:], new_no, line[1:]))
            old_no += 1
            new_no += 1
            i += 1
        else:
            flush([])
            i += 1

    flush([])
    return rows


def _render_split(rows: list[_DiffRow], total_width: int = 94) -> str:
    """Render diff rows as Rich markup in split (side-by-side) format."""
    LINENO_W = 4
    DIV = " │ "
    code_w = max((total_width - 2 * (LINENO_W + 1) - len(DIV)) // 2, 10)

    def no(n: Optional[int]) -> str:
        return f"{n:>{LINENO_W}}" if n is not None else " " * LINENO_W

    def clip(s: str, w: int) -> str:
        s = s.expandtabs(4)
        if len(s) > w:
            return s[: w - 1] + "…"
        return s.ljust(w)

    blank = " " * (LINENO_W + 1 + code_w)
    out: list[str] = []

    for row in rows:
        if row.kind == "header":
            out.append(f"[bold yellow]{escape(row.raw)}[/bold yellow]")
        elif row.kind == "hunk":
            out.append(f"[cyan]{escape(row.raw)}[/cyan]")
        elif row.kind == "context":
            on = escape(no(row.old_no))
            ot = escape(clip(row.old_text, code_w))
            nn = escape(no(row.new_no))
            nt = escape(clip(row.new_text, code_w))
            out.append(f"[dim]{on}│{ot}{DIV}{nn}│{nt}[/dim]")
        elif row.kind == "removed":
            on = escape(no(row.old_no))
            ot = escape(clip(row.old_text, code_w))
            out.append(f"[dim]{on}│[/dim][red]{ot}[/red][dim]{DIV}[/dim]{blank}")
        elif row.kind == "added":
            nn = escape(no(row.new_no))
            nt = escape(clip(row.new_text, code_w))
            out.append(f"{blank}[dim]{DIV}{nn}│[/dim][green]{nt}[/green]")
        elif row.kind == "changed":
            on = escape(no(row.old_no))
            ot = escape(clip(row.old_text, code_w))
            nn = escape(no(row.new_no))
            nt = escape(clip(row.new_text, code_w))
            out.append(f"[dim]{on}│[/dim][red]{ot}[/red][dim]{DIV}{nn}│[/dim][green]{nt}[/green]")

    return "\n".join(out)


class DiffPreviewWindow(FloatWindow):
    """Floating window showing a side-by-side Git diff."""

    DEFAULT_CSS = """
    DiffPreviewWindow #diff-scroll {
        width: 1fr;
        height: 1fr;
    }
    DiffPreviewWindow #diff-content {
        width: 1fr;
    }
    """

    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 30

    def __init__(self, path: Path, diff: str, **kwargs) -> None:
        self._path = path
        self._diff = diff or "(no diff)"
        super().__init__(title=f"diff: {path.name}", **kwargs)

    def compose_body(self) -> ComposeResult:
        rows = _parse_diff(self._diff)
        rendered = _render_split(rows, total_width=self.DEFAULT_WIDTH - 4)
        with ScrollableContainer(id="diff-scroll"):
            yield Static(rendered, markup=True, id="diff-content")
