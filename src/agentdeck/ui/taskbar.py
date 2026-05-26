from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class WindowTaskBar(Widget):
    """浮窗任务栏 — 列出所有打开的工作窗口（feat-004 实现后填充内容）。"""

    DEFAULT_CSS = """
    WindowTaskBar {
        height: 1;
        layout: horizontal;
        background: $panel-darken-2;
        padding: 0 1;
    }
    WindowTaskBar #tb-hint {
        color: $text-disabled;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("（无打开窗口）", id="tb-hint")
