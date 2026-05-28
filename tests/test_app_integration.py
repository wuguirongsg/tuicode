"""App-level integration tests for the observed workspace loop."""
from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path

from textual.widgets import Static

from tuicode.app import TuiCodeApp
from tuicode.events import GitStatusChanged
from tuicode.ui.diff_preview_window import DiffPreviewWindow
from tuicode.ui.editor_window import EditorWindow
from tuicode.ui.right_panel import GitFileList, RightPanel
from tuicode.ui.workspace import FloatWorkspace


def _git(root: Path, *args: str) -> None:
    subprocess.run(("git", "-C", str(root), *args), check=True, capture_output=True)


def test_app_observes_external_file_change_and_updates_git_panel(
    tmp_path: Path,
    monkeypatch,
):
    """TuiCodeApp wires watcher, editor, and Git panel into one observable loop."""
    _git(tmp_path, "init")
    target = tmp_path / "main.py"
    target.write_text("old = True\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    async def run():
        app = TuiCodeApp()
        async with app.run_test(size=(140, 50), headless=True) as pilot:
            await pilot.pause()
            win = EditorWindow(target)
            await app.query_one(FloatWorkspace).open_window(win)
            await pilot.pause()

            time.sleep(0.001)
            target.write_text("new = True\n", encoding="utf-8")
            changed = app._workspace_watcher.poll()
            await pilot.pause()

            assert target.resolve() in changed
            assert win._external_changed is True
            assert win._title == "!main.py"

            git_status = app.query_one("#git-status", Static)
            content = str(git_status.content)
            assert "1 changed" in content
            assert app.query_one("#git-files", GitFileList)._lines == ("?? main.py",)

    asyncio.run(run())


def test_app_opens_read_only_diff_preview_from_git_panel(tmp_path: Path, monkeypatch):
    _git(tmp_path, "init")
    target = tmp_path / "main.py"
    target.write_text("old = True\n", encoding="utf-8")
    _git(tmp_path, "add", "main.py")
    target.write_text("new = True\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    async def run():
        app = TuiCodeApp()
        async with app.run_test(size=(150, 50), headless=True) as pilot:
            await pilot.pause()
            panel = app.query_one(RightPanel)
            panel.update_git_status(
                GitStatusChanged(branch="main", changed_files=(" M main.py",))
            )
            app.query_one("#git-files", GitFileList).post_message(
                GitFileList.Selected(" M main.py")
            )
            await pilot.pause()

            win = app.query_one(DiffPreviewWindow)
            assert win._path == target
            assert "-old = True" in win._diff
            assert "+new = True" in win._diff

    asyncio.run(run())
