from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from tuicode.i18n import t
from tuicode.ui.float_window import FloatWindow


# ── 布局预设计算函数 ────────────────────────────────────────────────────────────
# 返回 list of (target_x, target_y, target_w, target_h)，长度 >= count。
# 所有值已满足 FloatWindow 的 MIN_WIDTH / MIN_HEIGHT 约束。

def _preset_positions(preset: int, count: int, ws_w: int, ws_h: int) -> list[tuple[int, int, int, int]]:
    """Compute absolute (x, y, w, h) for each window slot under the given preset."""
    min_w = FloatWindow.MIN_WIDTH
    min_h = FloatWindow.MIN_HEIGHT

    def clamp(val: int, lo: int, hi: int) -> int:
        return max(lo, min(val, hi))

    positions: list[tuple[int, int, int, int]] = []

    if preset == 1:
        # 编辑模式：第一个窗口几乎全屏，其余 cascade 于右下角
        main_w = clamp(ws_w - 2, min_w, ws_w)
        main_h = clamp(ws_h - 2, min_h, ws_h)
        positions.append((0, 0, main_w, main_h))
        for i in range(1, count):
            x = clamp(4 + (i - 1) * 4, 0, ws_w - min_w)
            y = clamp(2 + (i - 1) * 2, 0, ws_h - min_h)
            w = clamp(ws_w // 2, min_w, ws_w)
            h = clamp(ws_h // 3, min_h, ws_h)
            positions.append((x, y, w, h))

    elif preset == 2:
        # 双 Agent 对比：前两个左右平分，其余 cascade
        half_w = clamp(ws_w // 2 - 1, min_w, ws_w)
        main_h = clamp(ws_h - 2, min_h, ws_h)
        if count >= 1:
            positions.append((0, 0, half_w, main_h))
        if count >= 2:
            right_x = half_w + 1
            right_w = clamp(ws_w - right_x, min_w, ws_w)
            positions.append((right_x, 0, right_w, main_h))
        for i in range(2, count):
            x = clamp(4 * i, 0, ws_w - min_w)
            y = clamp(2 * i, 0, ws_h - min_h)
            positions.append((x, y, half_w, clamp(ws_h // 3, min_h, ws_h)))

    elif preset == 3:
        # 调试模式：上大(70%)下小(30%)，其余 cascade
        top_h = clamp((ws_h * 7) // 10, min_h, ws_h - min_h - 1)
        bot_h = clamp(ws_h - top_h - 1, min_h, ws_h)
        full_w = clamp(ws_w - 2, min_w, ws_w)
        if count >= 1:
            positions.append((0, 0, full_w, top_h))
        if count >= 2:
            positions.append((0, top_h, full_w, bot_h))
        for i in range(2, count):
            x = clamp(4 * i, 0, ws_w - min_w)
            y = clamp(top_h + bot_h + 2 * i, 0, ws_h - min_h)
            positions.append((x, y, clamp(ws_w // 2, min_w, ws_w), bot_h))

    # 兜底：多余的窗口 cascade
    while len(positions) < count:
        i = len(positions)
        x = clamp(4 * i, 0, ws_w - min_w)
        y = clamp(2 * i, 0, ws_h - min_h)
        positions.append((x, y, clamp(ws_w // 2, min_w, ws_w), clamp(ws_h // 3, min_h, ws_h)))

    return positions

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

    class PresetApplied(Message):
        def __init__(self, preset: int) -> None:
            super().__init__()
            self.preset = preset

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

    def apply_preset(self, preset: int) -> None:
        """Rearrange open windows according to layout preset 1/2/3."""
        wins = list(self._windows)
        if not wins:
            return

        ws_w, ws_h = self.size.width, self.size.height
        positions = _preset_positions(preset, len(wins), ws_w, ws_h)

        cumulative = 0
        for win, (target_x, target_y, target_w, target_h) in zip(wins, positions):
            if win._is_minimized:
                win.restore()
            win._win_x = target_x
            win._win_y = target_y - cumulative
            win._win_w = target_w
            win._win_h = target_h
            win._stack_y = cumulative
            win.styles.width = target_w
            win.styles.height = target_h
            win.styles.offset = (target_x, target_y - cumulative)
            cumulative += target_h

        self.post_message(self.PresetApplied(preset))
