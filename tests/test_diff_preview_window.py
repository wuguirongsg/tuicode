"""feat-014 单元测试 — 只读 diff 浮窗。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Static

from tuicode.ui.diff_preview_window import DiffPreviewWindow, _colorize_diff
from tuicode.ui.workspace import FloatWorkspace


class _DiffApp(App):
    def compose(self) -> ComposeResult:
        yield FloatWorkspace()


def test_colorize_diff_marks_added_removed_lines():
    markup = _colorize_diff("-old\n+new\n@@hunk@@")
    assert "[red]-old[/red]" in markup
    assert "[green]+new[/green]" in markup
    assert "[cyan]@@hunk@@[/cyan]" in markup


def test_colorize_diff_marks_file_headers():
    markup = _colorize_diff("--- a/foo.py\n+++ b/foo.py")
    assert "[bold]--- a/foo.py[/bold]" in markup
    assert "[bold]+++ b/foo.py[/bold]" in markup


def test_diff_preview_window_shows_colorized_diff(tmp_path: Path):
    target = tmp_path / "main.py"

    async def run():
        app = _DiffApp()
        async with app.run_test(size=(120, 40), headless=True) as pilot:
            win = DiffPreviewWindow(target, "-old\n+new\n")
            await app.query_one(FloatWorkspace).open_window(win)
            await pilot.pause()
            static = win.query_one("#diff-content", Static)
            markup = static._Static__content
            assert "-old" in markup
            assert "+new" in markup

    asyncio.run(run())
