"""PTY + pyte 虚拟终端 Widget — feat-007。"""
from __future__ import annotations

import collections
import fcntl
import os
import re
import shlex
import struct
import termios
import asyncio
from typing import TYPE_CHECKING

import pyte
from rich.segment import Segment
from rich.style import Style
from textual.message import Message
from textual.strip import Strip
from textual.widget import Widget

_DEFAULT_CHAR = pyte.screens.Char(" ")
_SB_THUMB = Style(color="white")
_SB_TRACK = Style(color="bright_black")
_TERM_DEFAULT = Style(color="#ffffff", bgcolor="#000000")

# 扫描 PTY 输出中的鼠标模式开关序列（pyte 不把这些写入 screen.mode）
_RE_MOUSE_MODE = re.compile(rb"\x1b\[\?(\d+)([hl])")
_MOUSE_BASIC_MODES = frozenset({1000, 1002, 1003})

# 扫描 bracketed paste 模式开关（\x1b[?2004h = 启用，\x1b[?2004l = 禁用）
_RE_BPASTE_MODE = re.compile(rb"\x1b\[\?2004([hl])")

if TYPE_CHECKING:
    from textual.events import (
        Key, MouseDown, MouseScrollDown, MouseScrollUp, MouseUp, Paste, Resize,
    )

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
    # pyte 以不带 # 的 6 位十六进制字符串存储 truecolor（如 "3a7bd5"）
    if len(low) == 6:
        try:
            int(low, 16)
            return f"#{low}"
        except ValueError:
            pass
    # pyte 某些版本以字符串形式存储 256 色索引（如 "196"）
    try:
        n = int(low)
        if 0 <= n <= 255:
            return f"color({n})"
    except ValueError:
        pass
    return None



# ── key name → PTY bytes ─────────────────────────────────────────────────────

# App 级全局快捷键 — PTY 不拦截，让事件冒泡到 App BINDINGS
_APP_RESERVED_KEYS: frozenset[str] = frozenset({
    "ctrl+q",             # 退出 App
    "ctrl+grave_accent",  # 聚焦终端
    "ctrl+t",             # 新建智能体终端
    "alt+1", "alt+2", "alt+3",    # focus_window
    "ctrl+1", "ctrl+2", "ctrl+3", # layout_preset
    "ctrl+underscore",    # 命令面板 Ctrl+/
    "f1",                 # 命令面板备用
})

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
    # alt + 方向键
    "alt+up":       b"\x1b[1;3A",
    "alt+down":     b"\x1b[1;3B",
    "alt+right":    b"\x1b[1;3C",
    "alt+left":     b"\x1b[1;3D",
    # alt + 常用键
    "alt+enter":    b"\x1b\r",
    "alt+backspace": b"\x1b\x7f",
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

    class OutputReceived(Message):
        """PTY 子进程产生输出。"""

        def __init__(self, terminal: "PtyTerminal", data: bytes) -> None:
            super().__init__()
            self.terminal = terminal
            self.data = data

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
        self._app_mouse = False      # 子进程是否启用了鼠标跟踪
        self._app_mouse_sgr = False  # 子进程是否使用 SGR 鼠标编码
        self._bracketed_paste = False  # 子进程是否启用了 bracketed paste mode

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

        def _child_setup() -> None:
            os.setsid()
            fd = os.open(slave_name, os.O_RDWR)
            os.dup2(fd, 0)
            os.dup2(fd, 1)
            os.dup2(fd, 2)
            if fd > 2:
                os.close(fd)

        cmd_parts = shlex.split(self._shell)
        self._process = await asyncio.create_subprocess_exec(
            cmd_parts[0], *cmd_parts[1:],
            preexec_fn=_child_setup,
            env={**os.environ, "TERM": "xterm-256color", "COLORTERM": "truecolor", "FORCE_COLOR": "3"},
        )
        # fork 已完成，父进程不再需要 slave 端；子进程已在 _child_setup 里重新打开它
        os.close(slave_fd)

        # 非阻塞模式：让 _on_pty_readable 能循环读直到 EAGAIN 而不会挂死
        fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

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
            # 循环读直到 EAGAIN，把 PTY 缓冲区一次性清空。
            # 这样可以避免子进程因 PTY 缓冲区满而阻塞写操作（卡住的根本原因之一）。
            buf = bytearray()
            while True:
                try:
                    chunk = os.read(self._master_fd, 65536)
                    if not chunk:
                        break
                    buf += chunk
                except BlockingIOError:
                    break
            if buf and self._pyte_stream is not None:
                data = bytes(buf)
                # 扫描鼠标模式 + bracketed paste 模式开关（pyte 不跟踪私有模式）
                for m in _RE_MOUSE_MODE.finditer(data):
                    mode = int(m.group(1))
                    enable = m.group(2) == b"h"
                    if mode in _MOUSE_BASIC_MODES:
                        self._app_mouse = enable
                    elif mode == 1006:
                        self._app_mouse_sgr = enable
                for m in _RE_BPASTE_MODE.finditer(data):
                    self._bracketed_paste = m.group(1) == b"h"
                self._pyte_stream.feed(data)
                self.post_message(self.OutputReceived(self, data))
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

    # ── 鼠标转发辅助 ─────────────────────────────────────────────────────────

    def _mouse_enabled(self) -> bool:
        """子进程是否已启用鼠标跟踪（从 PTY 输出扫描得到）。"""
        return self._app_mouse

    def _screen_to_pty(self, screen_x: int, screen_y: int) -> tuple[int, int] | None:
        """屏幕绝对坐标 → 1-indexed PTY 列/行；越界返回 None。"""
        r = self.region
        col = screen_x - r.x - 1   # 减去左边框
        row = screen_y - r.y - 1   # 减去上边框
        if col < 0 or row < 0:
            return None
        screen = self._pyte_screen
        if screen and (col >= screen.columns or row >= screen.lines):
            return None
        return col + 1, row + 1

    def _write_mouse(self, button: int, col: int, row: int, press: bool) -> None:
        """将鼠标事件编码为 SGR（首选）或 X10 序列并写入 PTY。"""
        if self._master_fd is None:
            return
        if self._app_mouse_sgr:
            suffix = "M" if press else "m"
            data = f"\x1b[<{button};{col};{row}{suffix}".encode()
        else:
            if not press:
                button = 3
            if col > 222 or row > 222:
                return
            data = bytes([0x1b, 0x5b, 0x4d, button + 32, col + 32, row + 32])
        try:
            os.write(self._master_fd, data)
        except OSError:
            pass

    # ── 滚动 ──────────────────────────────────────────────────────────────────

    def on_mouse_scroll_up(self, event: MouseScrollUp) -> None:  # type: ignore[override]
        if self._mouse_enabled() and self._scroll_offset == 0:
            pos = self._screen_to_pty(event.screen_x, event.screen_y)
            if pos:
                self._write_mouse(64, pos[0], pos[1], press=True)
            event.stop()
            return
        if self._pyte_screen is None:
            return
        max_offset = len(self._pyte_screen.scrollback)
        self._scroll_offset = min(self._scroll_offset + self._SCROLL_STEP, max_offset)
        self._update_scroll_indicator()
        self.refresh()
        event.stop()

    def on_mouse_scroll_down(self, event: MouseScrollDown) -> None:  # type: ignore[override]
        if self._mouse_enabled() and self._scroll_offset == 0:
            pos = self._screen_to_pty(event.screen_x, event.screen_y)
            if pos:
                self._write_mouse(65, pos[0], pos[1], press=True)
            event.stop()
            return
        self._scroll_offset = max(self._scroll_offset - self._SCROLL_STEP, 0)
        self._update_scroll_indicator()
        self.refresh()
        event.stop()

    def _update_scroll_indicator(self) -> None:
        if self._scroll_offset > 0:
            self.border_subtitle = f"↑{self._scroll_offset}行"
        else:
            self.border_subtitle = ""

    # ── 焦点 + 鼠标点击 ───────────────────────────────────────────────────────

    def on_mouse_down(self, event: MouseDown) -> None:  # type: ignore[override]
        self.focus()
        if not self._mouse_enabled():
            return
        pos = self._screen_to_pty(event.screen_x, event.screen_y)
        if pos is None:
            return
        btn = {1: 0, 2: 1, 3: 2}.get(event.button, 0)
        self._write_mouse(btn, pos[0], pos[1], press=True)
        event.stop()

    def on_mouse_up(self, event: MouseUp) -> None:  # type: ignore[override]
        if not self._mouse_enabled():
            return
        pos = self._screen_to_pty(event.screen_x, event.screen_y)
        if pos is None:
            return
        btn = {1: 0, 2: 1, 3: 2}.get(event.button, 0)
        self._write_mouse(btn, pos[0], pos[1], press=False)
        event.stop()

    # ── 键盘输入 ──────────────────────────────────────────────────────────────

    def on_key(self, event: Key) -> None:  # type: ignore[override]
        if self._master_fd is None or event.key in _APP_RESERVED_KEYS:
            return
        if event.key == "ctrl+c":
            # 计数交给 App（全局双击退出）；\x03 仍照常透传给子进程中断 agent
            self.app._ctrl_c_pressed()
        if event.key == "ctrl+v":
            # 从系统剪贴板粘贴，而非发 \x16（verbatim 字符）
            from tuicode.clipboard import read as _clipboard_read
            text = _clipboard_read()
            if text:
                event.stop()
                try:
                    data = text.encode("utf-8")
                    if self._bracketed_paste:
                        data = b"\x1b[200~" + data + b"\x1b[201~"
                    os.write(self._master_fd, data)
                except OSError:
                    pass
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

    def on_paste(self, event: Paste) -> None:  # type: ignore[override]
        """转发粘贴/IME 输入到 PTY（macOS IME 中文输入走此路径）。

        若子进程启用了 bracketed paste mode，包上 \x1b[200~...\x1b[201~ 标记，
        让子进程 readline 走粘贴路径而非逐字符 echo 路径——避免 CJK 宽字符宽度
        计算错误导致的"半个空格"显示异常。
        """
        if self._master_fd is None:
            return
        event.stop()
        try:
            data = event.text.encode("utf-8")
            if self._bracketed_paste:
                data = b"\x1b[200~" + data + b"\x1b[201~"
            os.write(self._master_fd, data)
        except OSError:
            pass

    def write_text(self, text: str, *, bracketed_paste: bool = True) -> None:
        """Programmatically send text to the PTY as if the user pasted it."""
        if self._master_fd is None or not text:
            return
        try:
            data = text.encode("utf-8")
            if bracketed_paste and self._bracketed_paste:
                data = b"\x1b[200~" + data + b"\x1b[201~"
            os.write(self._master_fd, data)
        except OSError:
            pass

    def get_scrollback_text(self, max_lines: int = 500) -> str:
        """返回 pyte scrollback 缓冲区中的干净文本（对话历史）。

        scrollback 是已滚出屏幕的历史行，不含状态栏，是最干净的会话内容来源。
        """
        screen = self._pyte_screen
        if screen is None or not screen.scrollback:
            return ""
        rows = list(screen.scrollback)[-max_lines:]
        lines: list[str] = []
        for row_dict in rows:
            if not row_dict:
                lines.append("")
                continue
            max_col = max(row_dict.keys(), default=-1)
            if max_col < 0:
                lines.append("")
                continue
            chars = [row_dict.get(x, _DEFAULT_CHAR).data for x in range(max_col + 1)]
            lines.append("".join(chars).rstrip())
        return "\n".join(lines)

    # ── 渲染 ──────────────────────────────────────────────────────────────────

    def _scrollbar_char(self, y: int) -> str | None:
        """返回第 y 行最右列应显示的滚动条字符；无历史时返回 None。"""
        screen = self._pyte_screen
        if screen is None:
            return None
        hist_len = len(screen.scrollback)
        if hist_len == 0:
            return None
        total = hist_len + screen.lines
        rows = screen.lines
        thumb_h = max(1, rows * rows // total)
        # view_top: 当前视图顶部在 total 中的绝对行号
        view_top = total - self._scroll_offset - rows
        thumb_top = max(0, min(rows - thumb_h, int(view_top * rows / total)))
        return "█" if thumb_top <= y < thumb_top + thumb_h else "│"

    def render_line(self, y: int) -> Strip:
        screen = self._pyte_screen
        if screen is None:
            return Strip([Segment(" " * self._cols, _TERM_DEFAULT)])

        if self._scroll_offset == 0:
            # 正常视图：直接渲染当前 pyte 屏幕
            if y >= screen.lines:
                return Strip([Segment(" " * screen.columns, _TERM_DEFAULT)])
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
                return Strip([Segment(" " * screen.columns, _TERM_DEFAULT)])
            if line_idx < hist_len:
                row = list(hist)[line_idx]
            else:
                screen_y = line_idx - hist_len
                if screen_y >= screen.lines:
                    return Strip([Segment(" " * screen.columns, _TERM_DEFAULT)])
                row = screen.buffer[screen_y]
            show_cursor = False

        segments: list[Segment] = []
        for x in range(screen.columns):
            char = row.get(x, _DEFAULT_CHAR)
            ch = char.data
            if not ch:
                # 双宽字符（CJK）右半占位符，跳过；左半 Segment 已占 2 列宽度
                continue
            fg = _to_rich_color(char.fg) or "#ffffff"
            bg = _to_rich_color(char.bg) or "#000000"
            if ch == " ":
                # 背景单元格：只用颜色，不渲染 underline/bold 等装饰
                # 规避 pyte 将当前 SGR 属性（含 underline）写入被清除单元格的问题
                style = Style(color=fg, bgcolor=bg)
            else:
                style = Style(
                    color=fg,
                    bgcolor=bg,
                    bold=char.bold,
                    italic=char.italics,
                    underline=char.underscore,
                    strike=char.strikethrough,
                    reverse=char.reverse,
                )
            if show_cursor and screen.cursor.x == x and screen.cursor.y == y:
                style = style + Style(reverse=True)
            segments.append(Segment(ch, style))

        sb = self._scrollbar_char(y)
        if sb is not None:
            segments[-1] = Segment(sb, _SB_THUMB if sb == "█" else _SB_TRACK)

        return Strip(segments)
