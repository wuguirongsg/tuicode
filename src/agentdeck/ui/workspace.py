from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class FloatWorkspace(Widget):
    """浮窗工作区 — 承载编辑器和智能体会话浮窗（feat-003 实现后替换内容）。"""

    DEFAULT_CSS = """
    FloatWorkspace {
        height: 1fr;
        background: #0d1117;
        overflow: hidden;
    }
    FloatWorkspace #ws-hint {
        color: $text-disabled;
        content-align: center middle;
        width: 100%;
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "浮窗工作区\n\n打开文件或启动智能体会话后，工作窗口将在此区域显示",
            id="ws-hint",
        )
