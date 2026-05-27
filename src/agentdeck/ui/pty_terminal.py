"""PTY + pyte 虚拟终端 Widget — feat-007。"""
from __future__ import annotations

import collections
import fcntl
import os
import struct
import termios
import asyncio
from typing import TYPE_CHECKING

import pyte
from rich.segment import Segment
from rich.style import Style
from textual.strip import Strip
from textual.widget import Widget

if TYPE_CHECKING:
    from textual.events import Key, MouseScrollDown, MouseScrollUp, Resize

# ── pyte 颜色 → Rich 颜色字符串 ──────────────────────────────────────────────

_ANSI_NAMES = {
    "black": "black", "red": "red", "green": "green", "yellow": "yellow",
    "blue": "blue", "magenta": "magenta", "cyan": "cyan", "white": "white",
    "brightblack": "bright_black", "brightred": "bright_red",
    "brightgreen": "bright_green", "brightyellow": "bright_yellow",
    "brightblue": "bright_blue", "brightmagenta": "bright_magenta",
    "brightcyan": "bright_cyan", "brightwhite": "bright_white",
}


def _to_rich_color(color: str | int | None) -> str | None:
    if color is None or color == "default" or color == "":
        return None
    if isinstance(color, int):
        return f"color({color})"
    low = color.lower()
    if low in _ANSI_NAMES:
        return _ANSI_NAMES[low]
    if low.startswith("#") and len(low) == 7:
        return low
    return None


def _char_style(char: pyte.screens.Char) -> Style:
    fg = _to_rich_color(char.fg)
    bg = _to_rich_color(char.bg)
    return Style(
        color=fg,
        bgcolor=bg,
        bold=char.bold,
        italic=char.italics,
        underline=char.underscore,
        strike=char.strikethrough,
        reverse=char.reverse,
    )


# ── key name → PTY bytes ─────────────────────────────────────────────────────

_KEY_MAP: dict[str, bytes] = {
    "enter":        b"\r",
    "tab":          b"\t",
    "backspace":    b"\x7f",
    "delete":       b"\x1b[3~",
    "escape":       b"\x1b",
    "up":           b"\x1b[A",
    "down":         b"\x1b[B",
    "right":        b"\x1b[C",
    "left":         b"\x1b[D",
    "home":         b"\x1b[H",
    "end":          b"\x1b[F",
    "pageup":       b"\x1b[5~",
    "pagedown":     b"\x1b[6~",
    "f1":           b"\x1bOP",
    "f2":           b"\x1bOQ",
    "f3":           b"\x1bOR",
    "f4":           b"\x1bOS",
    "f5":           b"\x1b[15~",
    "f6":           b"\x1b[17~",
    "f7":           b"\x1b[18~",
    "f8":           b"\x1b[19~",
    "f9":           b"\x1b[20~",
    "f10":          b"\x1b[21~",
    "ctrl+a":       b"\x01", "ctrl+b": b"\x02", "ctrl+c": b"\x03",
    "ctrl+d":       b"\x04", "ctrl+e": b"\x05", "ctrl+f": b"\x06",
    "ctrl+g":       b"\x07", "ctrl+h": b"\x08", "ctrl+k": b"\x0b",
    "ctrl+l":       b"\x0c", "ctrl+n": b"\x0e", "ctrl+o": b"\x0f",
    "ctrl+p":       b"\x10", "ctrl+q": b"\x11", "ctrl+r": b"\x12",
    "ctrl+s":       b"\x13", "ctrl+t": b"\x14", "ctrl+u": b"\x15",
    "ctrl+v":       b"\x16", "ctrl+w": b"\x17", "ctrl+x": b"\x18",
    "ctrl+y":       b"\x19", "ctrl+z": b"\x1a",
}


# ── 带滚动历史的 pyte 屏幕 ────────────────────────────────────────────────────

class _ScrollbackScreen(pyte.Screen):
    """拦截 index() 以捕获滚出的行，维护 2000 行滚动历史。"""

    def __init__(self, columns: int, lines: int) -> None:
        # 在 super().__init__() 之前建 scrollback，
        # 因为 pyte.Screen.__init__ 会调 reset()，reset() 会访问 scrollback
        self.scrollback: collections.deque = collections.deque(maxlen=2000)
        super().__init__(columns, lines)

    def index(self) -> None:
        # margins 未设置时为 None，此时整屏滚动；margins.top/bottom 指滚动区边界
        if self.margins is None:
            at_bottom = self.cursor.y == self.lines - 1
            top_row = 0
        else:
            at_bottom = self.cursor.y == self.margins.bottom
            top_row = self.margins.top
        if at_bottom:
            self.scrollback.append(dict(self.buffer[top_row]))
        super().index()

    def reset(self) -> None:
        super().reset()
        self.scrollback.clear()


# ── PtyTerminal Widget ────────────────────────────────────────────────────────

class PtyTerminal(Widget):
    """PTY + pyte 虚拟终端，含滚动历史和鼠标滚轮支持。"""

    DEFAULT_CSS = """
    PtyTerminal {
        width: 1fr;
        height: 1fr;
        background: #0a0a0a;
        border: solid $panel-darken-2;
    }
    PtyTerminal:focus {
        border: solid $accent;
    }
    """

    can_focus = True   # Textual 8.x 用小写

    _SCROLL_STEP = 3   # 每次滚轮滚动行数

    def __init__(self, shell: str = "/bin/bash", **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._shell = shell
        self._master_fd: int | None = None
        self._process: asyncio.subprocess.Process | None = None
        self._pyte_screen: _ScrollbackScreen | None = None
        self._pyte_stream: pyte.ByteStream | None = None
        self._cols = 80
        self._rows = 24
        self._focus_requested = False
        self._scroll_offset = 0   # 0 = 底部当前视图；>0 = 向上滚

    # ── 生命周期 ───────────────────────────────────────────────────────────────

    async def on_mount(self) -> None:
        self._init_pyte(self._cols, self._rows)
        await self._start_pty()
        self._focus_requested = True

    async def _start_pty(self) -> None:
        master_fd, slave_fd = os.openpty()
        self._master_fd = master_fd
        self._set_pty_size(self._cols, self._rows)

        slave_name = os.ttyname(slave_fd)
        os.close(slave_fd)

        def _child_setup() -> None:
            os.setsid()
            fd = os.open(slave_name, os.O_RDWR)
            os.dup2(fd, 0)
            os.dup2(fd, 1)
            os.dup2(fd, 2)
            if fd > 2:
                os.close(fd)

        self._process = await asyncio.create_subprocess_exec(
            self._shell,
            preexec_fn=_child_setup,
            env={**os.environ, "TERM": "xterm-256color"},
        )

        loop = asyncio.get_event_loop()
        loop.add_reader(master_fd, self._on_pty_readable)

    def _init_pyte(self, cols: int, rows: int) -> None:
        self._pyte_screen = _ScrollbackScreen(cols, rows)
        self._pyte_stream = pyte.ByteStream(self._pyte_screen)

    def _set_pty_size(self, cols: int, rows: int) -> None:
        if self._master_fd is None:
            return
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        try:
            fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, winsize)
        except OSError:
            pass

    def _on_pty_readable(self) -> None:
        if self._master_fd is None:
            return
        try:
            data = os.read(self._master_fd, 4096)
            if data and self._pyte_stream is not None:
                self._pyte_stream.feed(data)
                # 有新输出时自动滚到底部
                if self._scroll_offset > 0:
                    self._scroll_offset = 0
                    self._update_scroll_indicator()
                self.refresh()
        except OSError:
            try:
                asyncio.get_event_loop().remove_reader(self._master_fd)
            except Exception:
                pass

    async def _on_unmount(self) -> None:
        if self._master_fd is not None:
            try:
                asyncio.get_event_loop().remove_reader(self._master_fd)
            except Exception:
                pass
        if self._process is not None:
            try:
                self._process.terminate()
            except ProcessLookupError:
                pass
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None

    # ── 尺寸变化 ──────────────────────────────────────────────────────────────

    def on_resize(self, event: Resize) -> None:  # type: ignore[override]
        # content_size 已扣除边框，是 render_line 实际覆盖的行列数
        content = self.content_size
        cols = max(content.width, 10)
        rows = max(content.height, 4)
        size_changed = (cols != self._cols or rows != self._rows)
        self._cols, self._rows = cols, rows
        if self._pyte_screen is not None and size_changed:
            self._pyte_screen.resize(rows, cols)
        self._set_pty_size(cols, rows)
        if self._focus_requested and self.can_focus:
            self._focus_requested = False
            self.focus()

    # ── 滚动 ──────────────────────────────────────────────────────────────────

    def on_mouse_scroll_up(self, event: MouseScrollUp) -> None:  # type: ignore[override]
        if self._pyte_screen is None:
            return
        max_offset = len(self._pyte_screen.scrollback)
        self._scroll_offset = min(self._scroll_offset + self._SCROLL_STEP, max_offset)
        self._update_scroll_indicator()
        self.refresh()
        event.stop()

    def on_mouse_scroll_down(self, event: MouseScrollDown) -> None:  # type: ignore[override]
        self._scroll_offset = max(self._scroll_offset - self._SCROLL_STEP, 0)
        self._update_scroll_indicator()
        self.refresh()
        event.stop()

    def _update_scroll_indicator(self) -> None:
        if self._scroll_offset > 0:
            self.border_subtitle = f"↑{self._scroll_offset}行"
        else:
            self.border_subtitle = ""

    # ── 焦点 ──────────────────────────────────────────────────────────────────

    def on_mouse_down(self) -> None:
        self.focus()

    # ── 键盘输入 ──────────────────────────────────────────────────────────────

    def on_key(self, event: Key) -> None:  # type: ignore[override]
        if self._master_fd is None:
            return
        data = self._key_to_bytes(event)
        if data:
            event.stop()
            try:
                os.write(self._master_fd, data)
            except OSError:
                pass

    def _key_to_bytes(self, event: Key) -> bytes:
        key = event.key
        if key in _KEY_MAP:
            return _KEY_MAP[key]
        if event.character and len(event.character) == 1:
            try:
                return event.character.encode("utf-8")
            except UnicodeEncodeError:
                pass
        return b""

    # ── 渲染 ──────────────────────────────────────────────────────────────────

    def render_line(self, y: int) -> Strip:
        screen = self._pyte_screen
        if screen is None:
            return Strip([Segment(" " * self._cols)])

        if self._scroll_offset == 0:
            # 正常视图：直接渲染当前 pyte 屏幕
            if y >= screen.lines:
                return Strip([Segment(" " * screen.columns)])
            row = screen.buffer[y]
            show_cursor = True
        else:
            # 历史滚动视图：从 scrollback + 当前屏幕组合渲染
            hist = screen.scrollback
            hist_len = len(hist)
            total = hist_len + screen.lines
            view_bottom = total - self._scroll_offset
            view_top = view_bottom - self._rows
            line_idx = view_top + y
            if line_idx < 0 or line_idx >= total:
                return Strip([Segment(" " * screen.columns)])
            if line_idx < hist_len:
                row = list(hist)[line_idx]
            else:
                screen_y = line_idx - hist_len
                if screen_y >= screen.lines:
                    return Strip([Segment(" " * screen.columns)])
                row = screen.buffer[screen_y]
            show_cursor = False

        segments: list[Segment] = []
        for x in range(screen.columns):
            char = row[x]
            style = _char_style(char)
            if show_cursor and screen.cursor.x == x and screen.cursor.y == y:
                style = style + Style(reverse=True)
            segments.append(Segment(char.data or " ", style))
        return Strip(segments)
