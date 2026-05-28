"""feat-014 单元测试 — 只读 diff 浮窗。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import TextArea

from tuicode.ui.diff_preview_window import DiffPreviewWindow
from tuicode.ui.workspace import FloatWorkspace


class _DiffApp(App):
    def compose(self) -> ComposeResult:
        yield FloatWorkspace()


def test_diff_preview_window_is_read_only(tmp_path: Path):
    target = tmp_path / "main.py"

    async def run():
        app = _DiffApp()
        async with app.run_test(size=(120, 40), headless=True) as pilot:
            win = DiffPreviewWindow(target, "-old\n+new\n")
            await app.query_one(FloatWorkspace).open_window(win)
            await pilot.pause()
            text_area = win.query_one("#diff-textarea", TextArea)
            assert text_area.read_only is True
            assert "-old" in text_area.text
            assert "+new" in text_area.text

    asyncio.run(run())
