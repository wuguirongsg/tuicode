from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from agentdeck.ui.float_window import FloatWindow


class FloatWorkspace(Widget):
    """浮窗工作区 — 承载 FloatWindow 实例，支持 cascade 开窗。"""

    _STAGGER_X = 4
    _STAGGER_Y = 2

    DEFAULT_CSS = """
    FloatWorkspace {
        height: 1fr;
        background: #0d1117;
        overflow: hidden;
        layers: base floating;
    }
    FloatWorkspace #ws-hint {
        layer: base;
        color: $text-disabled;
        content-align: center middle;
        width: 100%;
        height: 100%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._next_x = 4
        self._next_y = 1
        self._windows: list[FloatWindow] = []

    def compose(self) -> ComposeResult:
        yield Static(
            "浮窗工作区\n\n打开文件或启动智能体会话后，工作窗口将在此区域显示",
            id="ws-hint",
        )

    async def open_window(self, window: FloatWindow) -> FloatWindow:
        """挂载浮窗到工作区，自动 cascade 初始位置。"""
        window._win_x = self._next_x
        window._win_y = self._next_y
        self._next_x += self._STAGGER_X
        self._next_y += self._STAGGER_Y
        if self._next_y > 8:
            self._next_x = 4
            self._next_y = 1

        self._windows.append(window)
        self.query_one("#ws-hint", Static).display = False
        await self.mount(window)
        window.focus()
        return window

    def on_float_window_closed(self, message: FloatWindow.Closed) -> None:
        if message.window in self._windows:
            self._windows.remove(message.window)
        if not self._windows:
            self.query_one("#ws-hint", Static).display = True
