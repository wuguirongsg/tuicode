from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from tuicode.i18n import t
from tuicode.ui.float_window import FloatWindow

_BANNER = (
    "[bold #00d4ff]████████╗██╗   ██╗██╗  ██████╗  ██████╗ ██████╗ ███████╗[/]\n"
    "[bold #00d4ff]   ██╔══╝██║   ██║██║ ██╔════╝ ██╔═══██╗██╔══██╗██╔════╝[/]\n"
    "[bold #00b8d9]   ██║   ██║   ██║██║ ██║      ██║   ██║██║  ██║█████╗  [/]\n"
    "[bold #00b8d9]   ██║   ╚██████╔╝██║ ╚██████╗ ╚██████╔╝██████╔╝███████╗[/]\n"
    "[bold #0097ba]   ╚═╝    ╚═════╝ ╚═╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝[/]"
)

_ROBOT_FRAMES = [
    "[#00d4ff]  ╭───╮\n  │◉ ◉│\n  ╰─┬─╯\n    ┴[/]",
    "[#00ff41]  ╭───╮\n  │● ●│\n  ╰─┬─╯\n    ┴[/]",
]


class _RobotWidget(Widget):
    DEFAULT_CSS = """
    _RobotWidget {
        width: auto;
        height: 4;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._frame = 0

    def on_mount(self) -> None:
        self.set_interval(0.9, self._tick)

    def _tick(self) -> None:
        self._frame = 1 - self._frame
        self.refresh()

    def render(self) -> str:
        return _ROBOT_FRAMES[self._frame]


class _CyberpunkHint(Widget):
    DEFAULT_CSS = """
    _CyberpunkHint {
        layer: base;
        width: 100%;
        height: 100%;
        content-align: center middle;
        layout: vertical;
        align: center middle;
    }
    _CyberpunkHint #ws-banner {
        width: auto;
        height: auto;
        content-align: center middle;
    }
    _CyberpunkHint #ws-sub {
        width: auto;
        height: 1;
        margin-top: 1;
        content-align: center middle;
    }
    _CyberpunkHint #ws-tip {
        width: auto;
        height: 1;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(_BANNER, id="ws-banner")
        yield _RobotWidget()
        yield Static(
            "[dim #bf00ff]┄┄┄┄┄ AI-Native Terminal IDE ┄┄┄┄┄[/]",
            id="ws-sub",
        )
        yield Static(
            f"[dim #606060]{t('workspace.hint')}[/]",
            id="ws-tip",
        )


class FloatWorkspace(Widget):
    """浮窗工作区 — 承载 FloatWindow 实例，支持 cascade 开窗 + 赛博朋克背景。"""

    class WindowOpened(Message):
        def __init__(self, window: FloatWindow) -> None:
            super().__init__()
            self.window = window

    _STAGGER_X = 4
    _STAGGER_Y = 2

    DEFAULT_CSS = """
    FloatWorkspace {
        height: 1fr;
        background: $background;
        overflow: hidden;
        layers: base floating;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._next_x = 4
        self._next_y = 1
        self._windows: list[FloatWindow] = []

    def compose(self) -> ComposeResult:
        yield _CyberpunkHint(id="ws-hint")

    async def open_window(self, window: FloatWindow) -> FloatWindow:
        """挂载浮窗，cascade 定位，补偿垂直堆叠偏移，淡入动画。"""
        stack_y = sum(w._win_h for w in self._windows)

        window._win_x   = self._next_x
        window._win_y   = self._next_y - stack_y
        window._stack_y = stack_y

        self._next_x += self._STAGGER_X
        self._next_y += self._STAGGER_Y
        if self._next_y > 8:
            self._next_x = 4
            self._next_y = 1

        self._windows.append(window)
        self.query_one("#ws-hint").display = False

        window.styles.opacity = 0.0
        await self.mount(window)
        window.styles.animate("opacity", 1.0, duration=0.25)
        window.focus()
        self.post_message(self.WindowOpened(window))
        return window

    def on_float_window_closed(self, message: FloatWindow.Closed) -> None:
        if message.window in self._windows:
            self._windows.remove(message.window)
        if not self._windows:
            self.query_one("#ws-hint").display = True
