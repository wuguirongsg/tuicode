"""feat-003 浮窗基类 — macOS 风格标题栏 + 拖动 + 缩放 + 焦点高亮。"""
from __future__ import annotations

from textual import events, on
from textual.app import ComposeResult
from textual.geometry import Offset
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


class WinButton(Static):
    """标题栏控制按钮 — 阻止 MouseDown 冒泡，避免误触发拖动。"""

    DEFAULT_CSS = """
    WinButton { width: 1; color: $text-disabled; margin-right: 1; }
    WinButton.btn-close { color: #ff5f57; }
    WinButton.btn-min   { color: #febc2e; }
    WinButton.btn-max   { color: #28c840; }
    """

    def on_mouse_down(self, event: events.MouseDown) -> None:
        event.stop()


class TitleBar(Widget):
    """标题栏 — macOS 红黄绿按钮 + capture_mouse 拖动（鼠标移出仍跟踪）。"""

    class CloseClicked(Message): ...
    class MinClicked(Message): ...
    class MaxClicked(Message): ...

    class DragMoved(Message):
        def __init__(self, dx: int, dy: int) -> None:
            super().__init__()
            self.dx = dx
            self.dy = dy

    DEFAULT_CSS = """
    TitleBar {
        height: 1;
        layout: horizontal;
        background: $panel;
        padding: 0 1;
    }
    TitleBar #win-title { width: 1fr; color: $text-muted; }
    """

    def __init__(self, title: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._dragging = False

    def compose(self) -> ComposeResult:
        yield WinButton("●", classes="btn-close", id="btn-close")
        yield WinButton("●", classes="btn-min",   id="btn-min")
        yield WinButton("●", classes="btn-max",   id="btn-max")
        yield Static(self._title, id="win-title")

    @on(events.Click, "#btn-close")
    def _close(self, event: events.Click) -> None:
        event.stop()
        self.post_message(self.CloseClicked())

    @on(events.Click, "#btn-min")
    def _min(self, event: events.Click) -> None:
        event.stop()
        self.post_message(self.MinClicked())

    @on(events.Click, "#btn-max")
    def _max(self, event: events.Click) -> None:
        event.stop()
        self.post_message(self.MaxClicked())

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if event.button == 1:
            self._dragging = True
            self.capture_mouse()   # 鼠标移出标题栏仍继续接收事件
            event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self._dragging:
            self.post_message(self.DragMoved(event.delta_x, event.delta_y))

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self.release_mouse()


class ResizeHandle(Widget):
    """右下角缩放手柄 ◢。"""

    class Resized(Message):
        def __init__(self, dw: int, dh: int) -> None:
            super().__init__()
            self.dw = dw
            self.dh = dh

    DEFAULT_CSS = """
    ResizeHandle { width: 1; height: 1; color: $text-muted; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._drag_start: Offset | None = None

    def render(self) -> str:
        return "◢"

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if event.button == 1:
            self._drag_start = Offset(event.screen_x, event.screen_y)
            self.capture_mouse()
            event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self._drag_start is not None:
            dw = event.screen_x - self._drag_start.x
            dh = event.screen_y - self._drag_start.y
            self._drag_start = Offset(event.screen_x, event.screen_y)
            self.post_message(self.Resized(dw, dh))

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._drag_start is not None:
            self._drag_start = None
            self.release_mouse()


class FloatWindow(Widget):
    """浮窗基类 — 子类覆盖 compose_body() 提供内容。

    定位原理（同 tui_demo.py）：
      _win_x/_win_y 存储 styles.offset 值（相对于垂直堆叠基准位置）。
      workspace.open_window() 通过 _stack_y 补偿使初始位置正确。
      拖动时用 event.delta_x/delta_y 直接叠加到 offset，capture_mouse 保证流畅。
    """

    can_focus = True  # 允许接收焦点，使 :focus-within 高亮生效

    class Closed(Message):
        def __init__(self, window: "FloatWindow") -> None:
            super().__init__()
            self.window = window

    DEFAULT_WIDTH = 60
    DEFAULT_HEIGHT = 20
    MIN_WIDTH = 20
    MIN_HEIGHT = 5

    DEFAULT_CSS = """
    FloatWindow {
        layer: floating;
        border: solid $panel;
        background: $surface;
        width: 60;
        height: 20;
        overflow: hidden hidden;
    }
    FloatWindow:focus-within {
        border: solid cornflowerblue;
    }
    FloatWindow #win-body {
        height: 1fr;
        overflow: hidden hidden;
    }
    FloatWindow #win-footer {
        height: 1;
        layout: horizontal;
        background: $panel;
    }
    FloatWindow #footer-spacer { width: 1fr; }
    """

    def __init__(self, title: str = "Window", x: int = 4, y: int = 2, **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        # x: offset 值（= 绝对 x，因为水平方向无堆叠）
        # y: 由 workspace.open_window() 设置为 desired_y - stack_y
        self._win_x = x
        self._win_y = y
        self._win_w = self.DEFAULT_WIDTH
        self._win_h = self.DEFAULT_HEIGHT
        self._saved_x = x
        self._saved_y = y
        self._saved_w = self.DEFAULT_WIDTH
        self._saved_h = self.DEFAULT_HEIGHT
        self._stack_y: int = 0   # 由 FloatWorkspace 设置，用于 maximize 归零定位
        self._is_minimized = False
        self._is_maximized = False

    def compose(self) -> ComposeResult:
        yield TitleBar(self._title)
        with Widget(id="win-body"):
            yield from self.compose_body()
        with Widget(id="win-footer"):
            yield Static("", id="footer-spacer")
            yield ResizeHandle()

    def compose_body(self) -> ComposeResult:
        """子类覆盖此方法提供窗口内容。"""
        yield Static("(空窗口)")

    def on_mount(self) -> None:
        self.styles.width  = self._win_w
        self.styles.height = self._win_h
        self.styles.offset = (self._win_x, self._win_y)
        self._saved_x = self._win_x
        self._saved_y = self._win_y

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """点击时将本窗口提升到最顶层（z 排序）。"""
        try:
            wins = [c for c in self.parent.children if isinstance(c, FloatWindow)]
            if len(wins) > 1 and wins[-1] is not self:
                self.parent.move_child(self, after=wins[-1])
        except Exception:
            pass

    # ── 拖动 ──────────────────────────────────────────────────────────────────

    def on_title_bar_drag_moved(self, message: TitleBar.DragMoved) -> None:
        if self._is_maximized:
            return
        self._win_x = max(0, self._win_x + message.dx)
        self._win_y += message.dy
        self.styles.offset = (self._win_x, self._win_y)

    # ── 缩放 ──────────────────────────────────────────────────────────────────

    def on_resize_handle_resized(self, message: ResizeHandle.Resized) -> None:
        self._win_w = max(self.MIN_WIDTH, self._win_w + message.dw)
        self._win_h = max(self.MIN_HEIGHT, self._win_h + message.dh)
        self.styles.width  = self._win_w
        self.styles.height = self._win_h

    # ── 按钮 ──────────────────────────────────────────────────────────────────

    def on_title_bar_close_clicked(self, message: TitleBar.CloseClicked) -> None:
        self.post_message(self.Closed(self))
        self.remove()

    def on_title_bar_min_clicked(self, message: TitleBar.MinClicked) -> None:
        body   = self.query_one("#win-body")
        footer = self.query_one("#win-footer")
        if self._is_minimized:
            body.display        = True
            footer.display      = True
            self.styles.height  = self._win_h
            self._is_minimized  = False
        else:
            body.display        = False
            footer.display      = False
            self.styles.height  = 3   # top border + title bar + bottom border
            self._is_minimized  = True

    def on_title_bar_max_clicked(self, message: TitleBar.MaxClicked) -> None:
        if self._is_maximized:
            self._win_x = self._saved_x
            self._win_y = self._saved_y
            self._win_w = self._saved_w
            self._win_h = self._saved_h
            self.styles.offset = (self._win_x, self._win_y)
            self.styles.width  = self._win_w
            self.styles.height = self._win_h
            self._is_maximized = False
        else:
            self._saved_x = self._win_x
            self._saved_y = self._win_y
            self._saved_w = self._win_w
            self._saved_h = self._win_h
            ws = self.parent
            w  = ws.size.width  if ws is not None else self._win_w
            h  = ws.size.height if ws is not None else self._win_h
            self._win_x = 0
            # 让窗口从 workspace 顶部开始：actual_y = stack_y + offset_y = 0
            # → offset_y = -stack_y
            self._win_y = -self._stack_y
            self._win_w = w
            self._win_h = h
            self.styles.offset = (self._win_x, self._win_y)
            self.styles.width  = w
            self.styles.height = h
            self._is_maximized = True
