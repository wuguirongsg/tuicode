from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from tuicode.ui.pty_terminal import PtyTerminal

_MIN_HEIGHT = 5
_MAX_HEIGHT = 40


class _ResizeHandle(Widget):
    """顶部拖动把手 — 上下拖动改变 TerminalStrip 高度。"""

    DEFAULT_CSS = """
    _ResizeHandle {
        height: 1;
        background: $panel-darken-2;
        color: $text-disabled;
        content-align: center middle;
    }
    _ResizeHandle:hover { color: $accent; }
    """

    def __init__(self) -> None:
        super().__init__()
        self._dragging = False
        self._drag_start_y = 0
        self._drag_start_h = 0

    def render(self):
        from rich.text import Text
        return Text("─ ↕ 拖动调整终端高度 ↕ ─", style="dim", justify="center")

    def on_mouse_down(self, event: events.MouseDown) -> None:
        strip = self.parent
        if not isinstance(strip, TerminalStrip):
            return
        self._dragging = True
        self._drag_start_y = event.screen_y
        h = strip.styles.height
        self._drag_start_h = int(h.value) if h and h.value else 12
        self.capture_mouse()
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._dragging:
            return
        strip = self.parent
        if not isinstance(strip, TerminalStrip):
            return
        delta = self._drag_start_y - event.screen_y   # 向上拖 = 增大
        new_h = max(_MIN_HEIGHT, min(_MAX_HEIGHT, self._drag_start_h + delta))
        strip.styles.height = new_h
        event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self._dragging = False
        self.release_mouse()


class TerminalStrip(Widget):
    """底部运行终端区 — 单标签 bash 会话（feat-007）。"""

    DEFAULT_CSS = """
    TerminalStrip {
        height: 14;
        background: #0a0a0a;
        border-top: solid $panel-darken-2;
    }
    TerminalStrip #ts-tabs {
        height: 1;
        color: $text-muted;
        background: $panel-darken-2;
        padding: 0 1;
    }
    TerminalStrip PtyTerminal {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield _ResizeHandle()
        yield Static("[bash]  [+]", id="ts-tabs")
        yield PtyTerminal()
