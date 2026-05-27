"""feat-008 智能体终端浮窗 — 通用 PTY 浮窗，可承载任意 CLI 智能体子进程。"""
from __future__ import annotations

from textual.app import ComposeResult

from tuicode.ui.float_window import FloatWindow
from tuicode.ui.pty_terminal import PtyTerminal


class AgentTerminalWindow(FloatWindow):
    """通用 PTY 浮窗，command 默认为 bash，可替换为任意 CLI 智能体。"""

    DEFAULT_WIDTH = 80
    DEFAULT_HEIGHT = 24

    DEFAULT_CSS = FloatWindow.DEFAULT_CSS + """
    AgentTerminalWindow #win-body {
        background: #000000;
    }
    """

    def __init__(
        self,
        command: str = "/bin/bash",
        title: str = "Terminal",
        **kwargs,
    ) -> None:
        self._command = command
        super().__init__(title=title, **kwargs)

    def compose_body(self) -> ComposeResult:
        yield PtyTerminal(shell=self._command)
