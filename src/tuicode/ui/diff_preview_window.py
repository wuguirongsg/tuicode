"""Read-only Git diff preview window."""
from __future__ import annotations

from pathlib import Path

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static

from tuicode.ui.float_window import FloatWindow


def _colorize_diff(diff: str) -> str:
    lines = []
    for line in diff.splitlines():
        esc = escape(line)
        if line.startswith("+++") or line.startswith("---"):
            lines.append(f"[bold]{esc}[/bold]")
        elif line.startswith("+"):
            lines.append(f"[green]{esc}[/green]")
        elif line.startswith("-"):
            lines.append(f"[red]{esc}[/red]")
        elif line.startswith("@@"):
            lines.append(f"[cyan]{esc}[/cyan]")
        elif line.startswith("diff ") or line.startswith("index "):
            lines.append(f"[bold yellow]{esc}[/bold yellow]")
        else:
            lines.append(esc)
    return "\n".join(lines)


class DiffPreviewWindow(FloatWindow):
    """A read-only floating window for inspecting Git diffs."""

    DEFAULT_CSS = """
    DiffPreviewWindow #diff-scroll {
        width: 1fr;
        height: 1fr;
    }
    DiffPreviewWindow #diff-content {
        width: 1fr;
    }
    """

    DEFAULT_WIDTH = 90
    DEFAULT_HEIGHT = 28

    def __init__(self, path: Path, diff: str, **kwargs) -> None:
        self._path = path
        self._diff = diff or "(no diff)"
        super().__init__(title=f"diff: {path.name}", **kwargs)

    def compose_body(self) -> ComposeResult:
        with ScrollableContainer(id="diff-scroll"):
            yield Static(
                _colorize_diff(self._diff),
                markup=True,
                id="diff-content",
            )
