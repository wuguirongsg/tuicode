from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from agentdeck.ui.pty_terminal import PtyTerminal


class TerminalStrip(Widget):
    """底部运行终端区 — 单标签 bash 会话（feat-007）。"""

    DEFAULT_CSS = """
    TerminalStrip {
        height: 12;
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
        yield Static("[bash]  [+]", id="ts-tabs")
        yield PtyTerminal()
