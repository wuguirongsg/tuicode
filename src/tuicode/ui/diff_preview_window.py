"""Read-only Git diff preview window."""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import TextArea

from tuicode.ui.float_window import FloatWindow


class DiffPreviewWindow(FloatWindow):
    """A read-only floating window for inspecting Git diffs."""

    DEFAULT_WIDTH = 90
    DEFAULT_HEIGHT = 28

    def __init__(self, path: Path, diff: str, **kwargs) -> None:
        self._path = path
        self._diff = diff or "(no diff)"
        super().__init__(title=f"diff: {path.name}", **kwargs)

    def compose_body(self) -> ComposeResult:
        yield TextArea(
            self._diff,
            language="diff",
            read_only=True,
            show_line_numbers=False,
            id="diff-textarea",
        )
