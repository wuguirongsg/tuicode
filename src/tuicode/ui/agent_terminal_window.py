"""feat-008/feat-017 智能体终端浮窗 — 通用 PTY 浮窗 + 稳定会话身份。"""
from __future__ import annotations

import uuid

from textual.app import ComposeResult
from textual.message import Message

from tuicode.ui.float_window import FloatWindow
from tuicode.ui.pty_terminal import PtyTerminal

# 标题前缀：▶ 运行中 / ■ 已结束（feat-019 运行状态可见）
_MARKER_RUNNING = "▶"
_MARKER_ENDED = "■"
_STATUS_POLL_INTERVAL = 1.5


class AgentTerminalWindow(FloatWindow):
    """通用 PTY 浮窗，command 默认为 bash，可替换为任意 CLI 智能体。

    每个实例持有不可变的 session_id（UUID4 前 8 位）和 agent_type 标识。
    标题前缀实时反映 PTY 子进程是否存活（▶ 运行中 / ■ 已结束）。
    """

    DEFAULT_WIDTH = 80
    DEFAULT_HEIGHT = 24

    DEFAULT_CSS = FloatWindow.DEFAULT_CSS + """
    AgentTerminalWindow #win-body {
        background: #000000;
    }
    """

    class StatusChanged(Message):
        """PTY 子进程运行状态发生变化（运行 ↔ 结束）。"""
        def __init__(self, window: "AgentTerminalWindow", is_running: bool) -> None:
            super().__init__()
            self.window = window
            self.is_running = is_running

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
        self._base_title = f"{title} [{self.session_id}]"
        self._status_running = True  # 乐观初值，PTY 通常瞬间起好
        self._seen_running = False   # 见过存活后才允许标记「已结束」，避免启动瞬间误判
        self._status_timer = None
        super().__init__(title=self._titled(True), **kwargs)

    def _titled(self, running: bool) -> str:
        marker = _MARKER_RUNNING if running else _MARKER_ENDED
        return f"{marker} {self._base_title}"

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

    def on_mount(self) -> None:
        super().on_mount()
        self._status_timer = self.set_interval(
            _STATUS_POLL_INTERVAL, self._check_status
        )

    def on_unmount(self) -> None:
        if self._status_timer is not None:
            self._status_timer.stop()
            self._status_timer = None

    def _check_status(self) -> None:
        running = self.is_running
        if running:
            self._seen_running = True
        elif not self._seen_running:
            return  # 仍在启动，先不判定结束
        if running == self._status_running:
            return
        self._status_running = running
        self._title = self._titled(running)
        self._refresh_border()
        self.post_message(self.StatusChanged(self, running))
