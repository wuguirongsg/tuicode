"""feat-003 浮窗基类 — macOS 风格标题栏 + 拖动 + 缩放 + 焦点高亮。"""
from __future__ import annotations

from textual import events, on
from textual.app import ComposeResult
from textual.geometry import Offset
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


class TitleBar(Widget):
    """标题栏 — macOS 红黄绿按钮 + 可拖动区域。"""

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
    TitleBar #btn-close { color: #ff5f57; width: 1; margin-right: 1; }
    TitleBar #btn-min   { color: #febc2e; width: 1; margin-right: 1; }
    TitleBar #btn-max   { color: #28c840; width: 1; margin-right: 2; }
    TitleBar #win-title { width: 1fr; }
    """

    def __init__(self, title: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._drag_start: Offset | None = None

    def compose(self) -> ComposeResult:
        yield Static("●", id="btn-close")
        yield Static("●", id="btn-min")
        yield Static("●", id="btn-max")
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
            self._drag_start = Offset(event.screen_x, event.screen_y)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self._drag_start is not None:
            dx = event.screen_x - self._drag_start.x
            dy = event.screen_y - self._drag_start.y
            self._drag_start = Offset(event.screen_x, event.screen_y)
            self.post_message(self.DragMoved(dx, dy))

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self._drag_start = None


class ResizeHandle(Widget):
    """右下角缩放手柄 ◢。"""

    class Resized(Message):
        def __init__(self, dw: int, dh: int) -> None:
            super().__init__()
            self.dw = dw
            self.dh = dh

    DEFAULT_CSS = """
    ResizeHandle {
        width: 1;
        height: 1;
        color: $text-muted;
    }
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
    """浮窗基类 — 子类覆盖 compose_body() 提供内容。"""

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
    FloatWindow #footer-spacer {
        width: 1fr;
    }
    """

    def __init__(self, title: str = "Window", x: int = 4, y: int = 2, **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._win_x = x
        self._win_y = y
        self._win_w = self.DEFAULT_WIDTH
        self._win_h = self.DEFAULT_HEIGHT
        self._saved_x = x
        self._saved_y = y
        self._saved_w = self.DEFAULT_WIDTH
        self._saved_h = self.DEFAULT_HEIGHT
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
        self.styles.offset = (self._win_x, self._win_y)
        self._saved_x = self._win_x
        self._saved_y = self._win_y

    # ── 拖动 ──────────────────────────────────────────────────────────────────

    def on_title_bar_drag_moved(self, message: TitleBar.DragMoved) -> None:
        if self._is_maximized:
            return
        self._win_x = max(0, self._win_x + message.dx)
        self._win_y = max(0, self._win_y + message.dy)
        self.styles.offset = (self._win_x, self._win_y)

    # ── 缩放 ──────────────────────────────────────────────────────────────────

    def on_resize_handle_resized(self, message: ResizeHandle.Resized) -> None:
        self._win_w = max(self.MIN_WIDTH, self._win_w + message.dw)
        self._win_h = max(self.MIN_HEIGHT, self._win_h + message.dh)
        self.styles.width = self._win_w
        self.styles.height = self._win_h

    # ── 按钮 ──────────────────────────────────────────────────────────────────

    def on_title_bar_close_clicked(self, message: TitleBar.CloseClicked) -> None:
        self.post_message(self.Closed(self))
        self.remove()

    def on_title_bar_min_clicked(self, message: TitleBar.MinClicked) -> None:
        body = self.query_one("#win-body")
        footer = self.query_one("#win-footer")
        if self._is_minimized:
            body.display = True
            footer.display = True
            self.styles.height = self._win_h
            self._is_minimized = False
        else:
            body.display = False
            footer.display = False
            self.styles.height = 3  # top border + title bar + bottom border
            self._is_minimized = True

    def on_title_bar_max_clicked(self, message: TitleBar.MaxClicked) -> None:
        if self._is_maximized:
            self._win_x = self._saved_x
            self._win_y = self._saved_y
            self._win_w = self._saved_w
            self._win_h = self._saved_h
            self.styles.offset = (self._win_x, self._win_y)
            self.styles.width = self._win_w
            self.styles.height = self._win_h
            self._is_maximized = False
        else:
            self._saved_x = self._win_x
            self._saved_y = self._win_y
            self._saved_w = self._win_w
            self._saved_h = self._win_h
            ws = self.parent
            w = ws.size.width if ws is not None else self._win_w
            h = ws.size.height if ws is not None else self._win_h
            self._win_x = 0
            self._win_y = 0
            self._win_w = w
            self._win_h = h
            self.styles.offset = (0, 0)
            self.styles.width = w
            self.styles.height = h
            self._is_maximized = True
