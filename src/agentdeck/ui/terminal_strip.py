from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class TerminalStrip(Widget):
    """底部运行终端区（feat-007 实现后替换为真实 PTY 终端）。"""

    DEFAULT_CSS = """
    TerminalStrip {
        height: 8;
        background: #0a0a0a;
        border-top: solid $panel-darken-2;
        padding: 0 1;
    }
    TerminalStrip #ts-tabs {
        height: 1;
        color: $text-muted;
        background: $panel-darken-2;
        padding: 0 1;
    }
    TerminalStrip #ts-hint {
        color: $text-disabled;
        height: 1fr;
        content-align: left top;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bash]  [+]", id="ts-tabs")
        yield Static("$ _\n（运行终端待实现）", id="ts-hint")
