"""PTY + pyte 虚拟终端 Widget — feat-007。"""
from __future__ import annotations

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
    from textual.events import Key, Resize

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


# ── PtyTerminal Widget ────────────────────────────────────────────────────────

class PtyTerminal(Widget):
    """PTY + pyte 虚拟终端。可嵌入任意 Textual 布局。"""

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

    can_focus = True   # Textual 8.x 用小写，CAN_FOCUS 已废弃

    def __init__(self, shell: str = "/bin/bash", **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._shell = shell
        self._master_fd: int | None = None
        self._process: asyncio.subprocess.Process | None = None
        self._pyte_screen: pyte.Screen | None = None
        self._pyte_stream: pyte.ByteStream | None = None
        self._cols = 80
        self._rows = 24
        self._focus_requested = False

    # ── 生命周期 ───────────────────────────────────────────────────────────────

    async def on_mount(self) -> None:
        # 用默认尺寸初始化 pyte；on_resize 会在布局确定后纠正到真实尺寸
        self._init_pyte(self._cols, self._rows)
        await self._start_pty()
        self._focus_requested = True  # 标记：下次 on_resize 后请求焦点

    async def _start_pty(self) -> None:
        master_fd, slave_fd = os.openpty()
        self._master_fd = master_fd
        self._set_pty_size(self._cols, self._rows)

        slave_name = os.ttyname(slave_fd)
        os.close(slave_fd)  # 父进程不持有 slave，由子进程按名打开

        def _child_setup() -> None:
            os.setsid()
            # 按名打开 slave：会话领导者首次 open 终端 → 自动成为控制终端
            # 这样 line discipline 才能把 \x03 转换成 SIGINT 发给前台进程组
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
        self._pyte_screen = pyte.Screen(cols, rows)
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
                self.refresh()
        except OSError:
            # PTY 关闭，移除 reader
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
        cols = max(event.size.width, 10)
        rows = max(event.size.height, 4)
        size_changed = (cols != self._cols or rows != self._rows)
        self._cols, self._rows = cols, rows
        if self._pyte_screen is not None and size_changed:
            self._pyte_screen.resize(rows, cols)
        self._set_pty_size(cols, rows)
        # 第一次 resize 时 size 才有效，此时请求焦点
        if self._focus_requested and self.can_focus:
            self._focus_requested = False
            self.focus()

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
        if self._pyte_screen is None:
            return Strip([Segment(" " * self._cols)])
        screen = self._pyte_screen
        if y >= screen.lines:
            return Strip([Segment(" " * self._cols)])

        row = screen.buffer[y]
        segments: list[Segment] = []
        for x in range(screen.columns):
            char = row[x]
            style = _char_style(char)
            # 光标位置反显
            if screen.cursor.x == x and screen.cursor.y == y:
                style = style + Style(reverse=True)
            segments.append(Segment(char.data or " ", style))
        return Strip(segments)

