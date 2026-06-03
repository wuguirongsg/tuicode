"""feat-003 浮窗基类 — 赛博朋克霓虹边框 + border-title 嵌入控制按钮。"""
from __future__ import annotations

import itertools

from textual import events
from textual.app import ComposeResult
from textual.geometry import Offset
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from tuicode.i18n import t


def _hsl_to_hex(h: float, s: float, lightness: float) -> str:
    """HSL → #rrggbb。h: 0-360, s/l: 0-1。"""
    c = (1.0 - abs(2 * lightness - 1)) * s
    x = c * (1.0 - abs((h / 60.0) % 2 - 1.0))
    m = lightness - c / 2.0
    if h < 60:
        r1, g1, b1 = c, x, 0.0
    elif h < 120:
        r1, g1, b1 = x, c, 0.0
    elif h < 180:
        r1, g1, b1 = 0.0, c, x
    elif h < 240:
        r1, g1, b1 = 0.0, x, c
    elif h < 300:
        r1, g1, b1 = x, 0.0, c
    else:
        r1, g1, b1 = c, 0.0, x
    return f"#{int((r1+m)*255):02x}{int((g1+m)*255):02x}{int((b1+m)*255):02x}"

# 霓虹色循环 — 每个新浮窗取下一个颜色
_NEON_COLORS: itertools.cycle = itertools.cycle([
    "#00d4ff",  # 青
    "#bf00ff",  # 紫
    "#ff00a0",  # 粉
    "#00ff41",  # 绿
    "#ffb800",  # 金
])


class ResizeHandle(Widget):
    """右下角缩放手柄 ◢。"""

    class Resized(Message):
        def __init__(self, dw: int, dh: int) -> None:
            super().__init__()
            self.dw = dw
            self.dh = dh

    DEFAULT_CSS = """
    ResizeHandle { width: 3; height: 1; color: $text-muted; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._drag_start: Offset | None = None

    def render(self) -> str:
        return " ◢ "

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
    """浮窗基类 — 霓虹 heavy 边框，border-title 嵌入 ●●● 控制按钮。

    定位原理：
      _win_x/_win_y 存储 styles.offset 值（相对垂直堆叠基准）。
      workspace.open_window() 通过 _stack_y 补偿使初始位置正确。

    按钮检测：
      顶部边框行 (screen_y == region.y) 上的固定列位置：
        col 2 = ● 关闭，col 4 = ● 最小化，col 6 = ● 最大化
    """

    can_focus = True

    MARQUEE_TICKS    = 28    # 28 × 25ms ≈ 0.7s 走完一圈
    MARQUEE_INTERVAL = 0.025

    class Closed(Message):
        def __init__(self, window: "FloatWindow") -> None:
            super().__init__()
            self.window = window

    class MinimizeToggled(Message):
        def __init__(self, window: "FloatWindow", is_minimized: bool) -> None:
            super().__init__()
            self.window = window
            self.is_minimized = is_minimized

    class TitleChanged(Message):
        def __init__(self, window: "FloatWindow") -> None:
            super().__init__()
            self.window = window

    DEFAULT_WIDTH = 60
    DEFAULT_HEIGHT = 20
    MIN_WIDTH = 20
    MIN_HEIGHT = 5

    # 边框标题格式: ┏━ ● ● ●  Title ━━━━━┓
    # region.x+0=┏  +1=━  +2=space  +3=●(close)  +5=●(min)  +7=●(max)
    # 每个按钮检测 2 格宽以容纳渲染误差
    _BTN_CLOSE_X: frozenset[int] = frozenset({2, 3})
    _BTN_MIN_X:   frozenset[int] = frozenset({4, 5})
    _BTN_MAX_X:   frozenset[int] = frozenset({6, 7})

    DEFAULT_CSS = """
    FloatWindow {
        layer: floating;
        border: heavy $panel-lighten-1;
        border-title-align: left;
        background: $surface;
        width: 60;
        height: 20;
        overflow: hidden hidden;
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
        self._win_x = x
        self._win_y = y
        self._win_w = self.DEFAULT_WIDTH
        self._win_h = self.DEFAULT_HEIGHT
        self._saved_x = x
        self._saved_y = y
        self._saved_w = self.DEFAULT_WIDTH
        self._saved_h = self.DEFAULT_HEIGHT
        self._stack_y: int = 0
        self._is_minimized = False
        self._is_maximized = False
        self._border_color = next(_NEON_COLORS)
        self._dragging = False
        self._drag_last: Offset = Offset(0, 0)
        self._marquee_timer = None
        self._marquee_tick: int = 0
        self._last_broadcast_title: str = title

    def compose(self) -> ComposeResult:
        with Widget(id="win-body"):
            yield from self.compose_body()
        with Widget(id="win-footer"):
            yield Static("", id="footer-spacer")
            yield ResizeHandle()

    def compose_body(self) -> ComposeResult:
        yield Static(t("editor.empty_window"))

    def on_mount(self) -> None:
        self.styles.width  = self._win_w
        self.styles.height = self._win_h
        self.styles.offset = (self._win_x, self._win_y)
        self._saved_x = self._win_x
        self._saved_y = self._win_y
        self._refresh_border()
        self._start_marquee()

    def _refresh_border(self) -> None:
        title = self._title[:32]
        self.border_title = (
            f"[#ff5f57 bold]●[/] [#febc2e bold]●[/] [#28c840 bold]●[/]  {title}"
        )
        self.styles.border = ("round", self._border_color)
        if self._title != self._last_broadcast_title:
            self._last_broadcast_title = self._title
            self.post_message(self.TitleChanged(self))

    # ── 跑马灯动画（按侧渐变 + 彩虹色相）────────────────────────────────────────
    # 四条边顺时针：上=青 右=紫 下=粉 左=绿，光头扫过时亮起，拖尾渐暗
    _SIDE_HUES = (195, 270, 330, 130)

    def _start_marquee(self) -> None:
        if self._marquee_timer is not None:
            self._marquee_timer.stop()
        self._marquee_tick = 0
        # 动画期间压暗底色，让彩色光带更显眼
        bc = self._border_color.lstrip("#")
        br, bg, bb = int(bc[0:2], 16), int(bc[2:4], 16), int(bc[4:6], 16)
        self.styles.border = ("round", f"#{br//5:02x}{bg//5:02x}{bb//5:02x}")
        self._marquee_timer = self.set_interval(self.MARQUEE_INTERVAL, self._marquee_step)

    def _stop_marquee(self) -> None:
        if self._marquee_timer is not None:
            self._marquee_timer.stop()
            self._marquee_timer = None

    def _marquee_step(self) -> None:
        tick = self._marquee_tick
        self._marquee_tick += 1
        if tick >= self.MARQUEE_TICKS:
            self._stop_marquee()
            self.styles.border = ("round", "#e0f7ff")
            return
        head = (tick / self.MARQUEE_TICKS) * 4.0  # 0..4 顺时针扫过四条边
        for side, hue in enumerate(self._SIDE_HUES):
            dist = (head - side) % 4
            brightness = max(0.0, 1.0 - dist / 1.5)
            color = _hsl_to_hex(hue, 1.0, 0.08 + 0.67 * brightness)
            setattr(self.styles, ("border_top", "border_right", "border_bottom", "border_left")[side],
                    ("round", color))

    # ── 焦点高亮 ──────────────────────────────────────────────────────────────

    def on_blur(self, event: events.Blur) -> None:
        self._stop_marquee()
        self.styles.border = ("round", self._border_color)

    def on_descendant_blur(self, event: events.DescendantBlur) -> None:
        if self._marquee_timer is None:
            self.styles.border = ("round", self._border_color)

    # ── 置顶 ──────────────────────────────────────────────────────────────────

    def _bring_to_top(self) -> None:
        try:
            wins = [c for c in self.parent.children if isinstance(c, FloatWindow)]
            if len(wins) <= 1 or wins[-1] is self:
                return
            actual_ys: dict[int, int] = {}
            cumulative = 0
            for w in wins:
                actual_ys[id(w)] = cumulative + w._win_y
                cumulative += w._win_h

            self.parent.move_child(self, after=wins[-1])

            idx = wins.index(self)
            new_order = wins[:idx] + wins[idx + 1:] + [self]

            cumulative = 0
            for w in new_order:
                w._stack_y = cumulative
                w._win_y   = actual_ys[id(w)] - cumulative
                w.styles.offset = (w._win_x, w._win_y)
                cumulative += w._win_h
        except Exception:
            pass

    # ── 顶部边框拖动 + 按钮点击 ──────────────────────────────────────────────

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self._bring_to_top()
        if event.button != 1 or event.screen_y != self.region.y:
            return
        rel_x = event.screen_x - self.region.x
        if rel_x in self._BTN_CLOSE_X:
            event.stop()
            self._do_close()
        elif rel_x in self._BTN_MIN_X:
            event.stop()
            self._do_min_toggle()
        elif rel_x in self._BTN_MAX_X:
            event.stop()
            self._do_max_toggle()
        elif not self._is_maximized:
            self._dragging = True
            self._drag_last = Offset(event.screen_x, event.screen_y)
            self.capture_mouse()
            event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._dragging:
            return
        dx = event.screen_x - self._drag_last.x
        dy = event.screen_y - self._drag_last.y
        self._drag_last = Offset(event.screen_x, event.screen_y)
        ws = self.parent
        if ws is not None:
            ws_w, ws_h = ws.size.width, ws.size.height
            new_x = max(0, min(self._win_x + dx, ws_w - 20))
            cur_actual_y = self.region.y - ws.region.y
            natural_y = cur_actual_y - self._win_y
            new_actual_y = max(0, min(cur_actual_y + dy, ws_h - 1))
            new_win_y = new_actual_y - natural_y
        else:
            new_x = max(0, self._win_x + dx)
            new_win_y = self._win_y + dy
        self._win_x = new_x
        self._win_y = new_win_y
        self.styles.offset = (self._win_x, self._win_y)
        event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self.release_mouse()

    # ── 按钮动作 ──────────────────────────────────────────────────────────────

    def _do_close(self) -> None:
        self.post_message(self.Closed(self))
        self.remove()

    def _do_min_toggle(self) -> None:
        if self._is_minimized:
            self.restore()
        else:
            self._minimize()

    def _do_max_toggle(self) -> None:
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
            self._win_y = -self._stack_y
            self._win_w = w
            self._win_h = h
            self.styles.offset = (self._win_x, self._win_y)
            self.styles.width  = w
            self.styles.height = h
            self._is_maximized = True

    # ── 缩放 ──────────────────────────────────────────────────────────────────

    def on_resize_handle_resized(self, message: ResizeHandle.Resized) -> None:
        self._win_w = max(self.MIN_WIDTH, self._win_w + message.dw)
        self._win_h = max(self.MIN_HEIGHT, self._win_h + message.dh)
        self.styles.width  = self._win_w
        self.styles.height = self._win_h

    # ── 最小化 ────────────────────────────────────────────────────────────────

    def _minimize(self) -> None:
        body   = self.query_one("#win-body")
        footer = self.query_one("#win-footer")
        body.display       = False
        footer.display     = False
        self.styles.height = 3
        self._is_minimized = True
        self.post_message(self.MinimizeToggled(self, True))

    def restore(self) -> None:
        if not self._is_minimized:
            return
        body   = self.query_one("#win-body")
        footer = self.query_one("#win-footer")
        body.display       = True
        footer.display     = True
        self.styles.height = self._win_h
        self._is_minimized = False
        self.post_message(self.MinimizeToggled(self, False))

    def set_tiling_mode(self, tiled: bool) -> None:
        """拼贴模式切换：隐藏底部手柄，边框换极简风格以最大化内容面积。"""
        try:
            footer = self.query_one("#win-footer")
            footer.display = not tiled
        except Exception:
            pass
        if tiled:
            self._stop_marquee()
            self.styles.border = ("solid", "#1e2030")
        else:
            self._refresh_border()
