from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class RightPanel(Widget):
    """右侧固定工具栏 — files / git / search Tab（feat-005 实现后填充文件树）。"""

    DEFAULT_CSS = """
    RightPanel {
        width: 28;
        height: 1fr;
        border-left: solid $panel-darken-2;
        layout: vertical;
        background: $panel-darken-1;
    }
    RightPanel #rp-tabs {
        height: 1;
        background: $panel-darken-2;
        layout: horizontal;
        padding: 0 1;
    }
    RightPanel .rp-tab {
        width: auto;
        padding: 0 1;
        color: $text-muted;
    }
    RightPanel .rp-tab-active {
        width: auto;
        padding: 0 1;
        color: $accent;
        text-style: bold;
    }
    RightPanel #rp-content {
        height: 1fr;
        color: $text-disabled;
        content-align: center middle;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Widget(id="rp-tabs"):
            yield Static("files", classes="rp-tab-active")
            yield Static("git", classes="rp-tab")
        yield Static("文件树待实现", id="rp-content")
