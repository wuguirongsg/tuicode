"""feat-014 单元测试 — 只读 diff 浮窗（split 视图）。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Static

from tuicode.ui.diff_preview_window import DiffPreviewWindow, _DiffRow, _parse_diff, _render_split
from tuicode.ui.workspace import FloatWorkspace

SAMPLE_DIFF = """\
--- a/foo.py
+++ b/foo.py
@@ -1,4 +1,4 @@
 import os
-old_value = 1
+new_value = 2
 print("done")
"""


class _DiffApp(App):
    def compose(self) -> ComposeResult:
        yield FloatWorkspace()


# ── _parse_diff ──────────────────────────────────────────────────────────────

def test_parse_diff_header_rows():
    rows = _parse_diff("--- a/foo.py\n+++ b/foo.py\n")
    assert rows[0].kind == "header"
    assert rows[0].raw == "--- a/foo.py"
    assert rows[1].kind == "header"
    assert rows[1].raw == "+++ b/foo.py"


def test_parse_diff_hunk_sets_line_numbers():
    rows = _parse_diff("@@ -5,3 +5,3 @@\n old\n-rem\n+add\n")
    hunk = rows[0]
    assert hunk.kind == "hunk"
    context = rows[1]
    assert context.kind == "context"
    assert context.old_no == 5
    assert context.new_no == 5


def test_parse_diff_consecutive_minus_plus_become_changed():
    rows = _parse_diff("@@ -1,2 +1,2 @@\n-old\n+new\n")
    changed = [r for r in rows if r.kind == "changed"]
    assert len(changed) == 1
    assert changed[0].old_text == "old"
    assert changed[0].new_text == "new"


def test_parse_diff_standalone_removed():
    rows = _parse_diff("@@ -1,2 +1,1 @@\n-gone\n-also\n context\n")
    removed = [r for r in rows if r.kind == "removed"]
    assert len(removed) == 2
    assert removed[0].old_text == "gone"


def test_parse_diff_standalone_added():
    rows = _parse_diff("@@ -1,1 +1,2 @@\n context\n+new1\n+new2\n")
    added = [r for r in rows if r.kind == "added"]
    assert len(added) == 2
    assert added[0].new_text == "new1"


def test_parse_diff_more_removed_than_added():
    """3 removed, 1 added → 1 changed + 2 removed."""
    rows = _parse_diff("@@ -1,3 +1,1 @@\n-a\n-b\n-c\n+x\n")
    kinds = [r.kind for r in rows]
    assert kinds.count("changed") == 1
    assert kinds.count("removed") == 2
    assert kinds.count("added") == 0


# ── _render_split ────────────────────────────────────────────────────────────

def test_render_split_changed_shows_old_left_new_right():
    rows = [_DiffRow("changed", 1, "old line", 1, "new line")]
    out = _render_split(rows, total_width=60)
    assert "old line" in out
    assert "new line" in out
    assert "[red]" in out
    assert "[green]" in out


def test_render_split_removed_right_side_blank():
    rows = [_DiffRow("removed", 3, "gone")]
    out = _render_split(rows, total_width=60)
    assert "gone" in out
    assert "[red]" in out
    assert "[green]" not in out


def test_render_split_added_left_side_blank():
    rows = [_DiffRow("added", new_no=7, new_text="fresh")]
    out = _render_split(rows, total_width=60)
    assert "fresh" in out
    assert "[green]" in out
    assert "[red]" not in out


def test_render_split_context_is_dimmed():
    rows = [_DiffRow("context", 1, "ctx", 1, "ctx")]
    out = _render_split(rows, total_width=60)
    assert "[dim]" in out


def test_render_split_hunk_is_cyan():
    rows = [_DiffRow("hunk", raw="@@ -1,3 +1,3 @@")]
    out = _render_split(rows, total_width=60)
    assert "[cyan]" in out


# ── DiffPreviewWindow (integration) ─────────────────────────────────────────

def test_diff_preview_window_shows_split_diff(tmp_path: Path):
    target = tmp_path / "main.py"

    async def run():
        app = _DiffApp()
        async with app.run_test(size=(130, 40), headless=True) as pilot:
            win = DiffPreviewWindow(target, SAMPLE_DIFF)
            await app.query_one(FloatWorkspace).open_window(win)
            await pilot.pause()
            static = win.query_one("#diff-content", Static)
            markup = static._Static__content
            assert "old_value" in markup
            assert "new_value" in markup
            assert "[red]" in markup
            assert "[green]" in markup

    asyncio.run(run())
