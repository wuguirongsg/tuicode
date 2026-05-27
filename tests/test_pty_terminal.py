"""feat-007: PtyTerminal 单元测试。"""
from __future__ import annotations

import asyncio
import os

import pyte
import pytest
from textual.app import App, ComposeResult

from tuicode.ui.pty_terminal import PtyTerminal, _to_rich_color


# ── 颜色转换 ──────────────────────────────────────────────────────────────────

def test_to_rich_color_default():
    assert _to_rich_color("default") is None
    assert _to_rich_color(None) is None
    assert _to_rich_color("") is None


def test_to_rich_color_ansi_names():
    assert _to_rich_color("red") == "red"
    assert _to_rich_color("brightblue") == "bright_blue"
    assert _to_rich_color("WHITE") == "white"


def test_to_rich_color_256():
    assert _to_rich_color(0) == "color(0)"
    assert _to_rich_color(255) == "color(255)"


def test_to_rich_color_hex():
    assert _to_rich_color("#1e2030") == "#1e2030"
    assert _to_rich_color("#AABBCC") == "#aabbcc"


def test_to_rich_color_pyte_truecolor():
    # pyte 以不带 # 的 6 位十六进制存储 truecolor
    assert _to_rich_color("3a7bd5") == "#3a7bd5"
    assert _to_rich_color("FF8000") == "#ff8000"
    assert _to_rich_color("000000") == "#000000"


def test_to_rich_color_pyte_256_string():
    # pyte 某些版本以字符串存储 256 色索引
    assert _to_rich_color("0") == "color(0)"
    assert _to_rich_color("196") == "color(196)"
    assert _to_rich_color("255") == "color(255)"



# ── PtyTerminal Widget ────────────────────────────────────────────────────────

class _TermApp(App):
    def compose(self) -> ComposeResult:
        yield PtyTerminal()


def test_pty_terminal_mounts():
    async def run():
        app = _TermApp()
        async with app.run_test(size=(80, 24)) as pilot:
            widget = app.query_one(PtyTerminal)
            assert widget is not None
            assert widget._process is not None
            assert widget._master_fd is not None
    asyncio.run(run())


def test_pty_terminal_receives_output():
    """启动后应能收到 bash 提示符输出（pyte 屏幕非空）。"""
    async def run():
        app = _TermApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await asyncio.sleep(0.5)
            widget = app.query_one(PtyTerminal)
            screen = widget._pyte_screen
            assert screen is not None
            has_content = any(
                any(ch.data.strip() for ch in screen.buffer[y].values())
                for y in range(screen.lines)
            )
            assert has_content, "pyte 屏幕应有 bash 提示符输出"
    asyncio.run(run())


def test_pty_terminal_ctrl_c():
    """向 PTY 写 Ctrl+C（\\x03）不应引发异常，bash 进程保持运行。"""
    async def run():
        app = _TermApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await asyncio.sleep(0.3)
            widget = app.query_one(PtyTerminal)
            assert widget._master_fd is not None
            os.write(widget._master_fd, b"\x03")
            await asyncio.sleep(0.1)
            assert widget._process is not None
            assert widget._process.returncode is None
    asyncio.run(run())


def test_pty_terminal_resize():
    """pyte 屏幕与 PTY 尺寸随 widget 尺寸同步。"""
    async def run():
        app = _TermApp()
        async with app.run_test(size=(80, 24)) as pilot:
            widget = app.query_one(PtyTerminal)
            await asyncio.sleep(0.2)
            # on_resize 使用 self.content_size（扣除边框后的内容区域）
            # 在 80x24 的测试窗口中，PtyTerminal 内容区应 ≥ 10 cols / ≥ 4 rows
            assert widget._cols >= 10
            assert widget._rows >= 4
    asyncio.run(run())


def test_render_line_empty():
    """未挂载时 render_line 返回空行不报错。"""
    widget = PtyTerminal()
    widget._cols = 20
    widget._rows = 5
    strip = widget.render_line(0)
    assert strip is not None
