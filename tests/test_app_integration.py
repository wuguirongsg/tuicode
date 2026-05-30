"""App-level integration tests for the observed workspace loop."""
from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path

from textual.widgets import Static

from tuicode.app import TuiCodeApp
from tuicode.events import GitStatusChanged, TerminalOutput
from tuicode.ui.agent_terminal_window import AgentTerminalWindow
from tuicode.ui.diff_preview_window import DiffPreviewWindow
from tuicode.ui.editor_window import EditorWindow
from tuicode.ui.mascot import MascotPanel
from tuicode.ui.right_panel import GitFileList, RightPanel
from tuicode.ui.status_bar import StatusBar
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


def test_status_bar_shows_filetree_hint_on_focus(tmp_path: Path, monkeypatch):
    """文件树聚焦时底栏显示文件操作快捷键，焦点移走后切回默认。"""
    from tuicode.i18n import t
    from tuicode.ui.file_tree import FileTree
    monkeypatch.chdir(tmp_path)

    async def run():
        app = TuiCodeApp()
        async with app.run_test(size=(140, 50), headless=True) as pilot:
            await pilot.pause()
            sb_right = app.query_one("#sb-right", Static)

            app.query_one(FileTree).focus()
            await pilot.pause()
            assert str(sb_right.content) == t("status.filetree_hint")

            app.query_one(StatusBar).set_shortcuts(None)
            assert str(sb_right.content) == t("status.shortcuts")

    asyncio.run(run())


def test_double_ctrl_c_exits_globally(tmp_path: Path, monkeypatch):
    """第一次 Ctrl+C 只提示，1.5s 内第二次退出 App。"""
    monkeypatch.chdir(tmp_path)

    async def run():
        app = TuiCodeApp()
        async with app.run_test(size=(140, 50), headless=True) as pilot:
            await pilot.pause()
            exited: list[bool] = []
            monkeypatch.setattr(app, "exit", lambda *a, **k: exited.append(True))

            app._ctrl_c_pressed()
            assert exited == []  # 第一次只提示，不退出

            app._ctrl_c_pressed()  # 立即第二次
            assert exited == [True]

    asyncio.run(run())


def test_agent_output_drives_mascot_compute_animation(tmp_path: Path, monkeypatch):
    """只有真实 Agent 输出会把右上角点阵屏切到运算动画，静默后回 idle。"""
    monkeypatch.chdir(tmp_path)

    async def run():
        app = TuiCodeApp()
        async with app.run_test(size=(140, 50), headless=True) as pilot:
            await pilot.pause()
            app._agent_sessions.add("agent-1")

            app._on_terminal_output(TerminalOutput(session_id="agent-1", text="delta"))
            await pilot.pause()
            assert app.query_one(MascotPanel)._state == "agent"
            assert app._agent_output_active is True

            await pilot.pause(1.0)
            assert app.query_one(MascotPanel)._state == "idle"
            assert app._agent_output_active is False

    asyncio.run(run())


def test_non_agent_terminal_output_does_not_drive_mascot(tmp_path: Path, monkeypatch):
    """底部普通终端或未知 session 输出不触发 Agent 运算灯效。"""
    monkeypatch.chdir(tmp_path)

    async def run():
        app = TuiCodeApp()
        async with app.run_test(size=(140, 50), headless=True) as pilot:
            await pilot.pause()

            app._on_terminal_output(TerminalOutput(session_id="bash", text="ls\n"))
            await pilot.pause()

            assert app.query_one(MascotPanel)._state == "idle"
            assert app._agent_output_active is False

    asyncio.run(run())


def test_ctrl_c_resets_after_timeout(tmp_path: Path, monkeypatch):
    """两次 Ctrl+C 间隔超过 1.5s 不退出，只重新提示。"""
    import time
    monkeypatch.chdir(tmp_path)

    async def run():
        app = TuiCodeApp()
        async with app.run_test(size=(140, 50), headless=True) as pilot:
            await pilot.pause()
            exited: list[bool] = []
            monkeypatch.setattr(app, "exit", lambda *a, **k: exited.append(True))

            app._ctrl_c_pressed()
            app._last_ctrl_c = time.monotonic() - 2.0  # 模拟超时
            app._ctrl_c_pressed()
            assert exited == []  # 超时后第二次仍只提示

    asyncio.run(run())


def test_app_agent_count_tracks_open_agent_windows(tmp_path: Path, monkeypatch):
    """feat-019: 底栏 agent_count 随 Agent 浮窗开关增减，不再恒为 0。"""
    monkeypatch.chdir(tmp_path)

    async def run():
        app = TuiCodeApp()
        async with app.run_test(size=(140, 50), headless=True) as pilot:
            await pilot.pause()
            status = app.query_one(StatusBar)
            assert status.agent_count == 0

            ws = app.query_one(FloatWorkspace)
            win1 = AgentTerminalWindow(title="A")
            await ws.open_window(win1)
            await pilot.pause()
            assert status.agent_count == 1

            win2 = AgentTerminalWindow(title="B")
            await ws.open_window(win2)
            await pilot.pause()
            assert status.agent_count == 2

            win1._do_close()
            await pilot.pause()
            assert status.agent_count == 1

    asyncio.run(run())


def test_command_palette_contains_agent_history_entry(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    async def run():
        app = TuiCodeApp()
        async with app.run_test(size=(140, 50), headless=True) as pilot:
            await pilot.pause()
            names = [cmd.name for cmd in app._build_palette_commands()]
            from tuicode.i18n import t
            assert t("cmd.continue_agent.name") in names

    asyncio.run(run())
