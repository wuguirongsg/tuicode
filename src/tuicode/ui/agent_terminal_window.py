"""feat-008/feat-017 智能体终端浮窗 — 通用 PTY 浮窗 + 稳定会话身份。"""
from __future__ import annotations

import uuid

from textual.app import ComposeResult

from tuicode.ui.float_window import FloatWindow
from tuicode.ui.pty_terminal import PtyTerminal


class AgentTerminalWindow(FloatWindow):
    """通用 PTY 浮窗，command 默认为 bash，可替换为任意 CLI 智能体。

    每个实例持有不可变的 session_id（UUID4 前 8 位）和 agent_type 标识。
    """

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
        agent_type: str = "bash",
        **kwargs,
    ) -> None:
        self._command = command
        self.agent_type = agent_type
        self.session_id = uuid.uuid4().hex[:8]
        super().__init__(title=f"{title} [{self.session_id}]", **kwargs)

    @property
    def is_running(self) -> bool:
        """True while the PTY subprocess is still alive."""
        try:
            pty = self.query_one(PtyTerminal)
            proc = pty._process
            return proc is not None and proc.returncode is None
        except Exception:
            return False

    def compose_body(self) -> ComposeResult:
        yield PtyTerminal(shell=self._command)
