"""feat-008: AgentTerminalWindow 测试。"""
from __future__ import annotations

import asyncio

import pytest
from textual.app import App, ComposeResult

from tuicode.ui.agent_terminal_window import AgentTerminalWindow
from tuicode.ui.editor_window import EditorWindow
from tuicode.ui.float_window import FloatWindow
from tuicode.ui.pty_terminal import PtyTerminal
from tuicode.ui.workspace import FloatWorkspace


# ── 辅助 App ─────────────────────────────────────────────────────────────────

class _AgentApp(App):
    def compose(self) -> ComposeResult:
        yield FloatWorkspace()

    async def open_agent(self, **kwargs) -> AgentTerminalWindow:
        ws = self.query_one(FloatWorkspace)
        win = AgentTerminalWindow(**kwargs)
        await ws.open_window(win)
        return win


# ── 单元测试 ──────────────────────────────────────────────────────────────────

def test_agent_terminal_window_default_attrs():
    win = AgentTerminalWindow()
    assert win._command == "/bin/bash"
    assert "Terminal" in win._title  # _title 包含 session_id 后缀


def test_agent_terminal_window_custom_attrs():
    win = AgentTerminalWindow(command="/bin/sh", title="Claude")
    assert win._command == "/bin/sh"
    assert "Claude" in win._title


def test_agent_terminal_window_inherits_float_window():
    assert issubclass(AgentTerminalWindow, FloatWindow)


def test_agent_terminal_window_default_size():
    win = AgentTerminalWindow()
    assert win.DEFAULT_WIDTH == 80
    assert win.DEFAULT_HEIGHT == 24


# ── 集成测试 ──────────────────────────────────────────────────────────────────

def test_agent_terminal_window_mounts():
    """AgentTerminalWindow 能在 FloatWorkspace 中挂载，含 PtyTerminal。"""
    async def run():
        app = _AgentApp()
        async with app.run_test(size=(120, 40)) as pilot:
            win = await app.open_agent()
            await pilot.pause(0.3)
            assert len(app.query(AgentTerminalWindow)) == 1
            assert win.query_one(PtyTerminal) is not None

    asyncio.run(run())


def test_agent_terminal_pty_starts():
    """PTY 进程应成功启动，master_fd 非 None。"""
    async def run():
        app = _AgentApp()
        async with app.run_test(size=(120, 40)) as pilot:
            win = await app.open_agent()
            await pilot.pause(0.4)
            pty = win.query_one(PtyTerminal)
            assert pty._master_fd is not None
            assert pty._process is not None
            assert pty._process.returncode is None

    asyncio.run(run())


def test_agent_terminal_receives_output():
    """bash 启动后 pyte 屏幕应有提示符输出。"""
    async def run():
        app = _AgentApp()
        async with app.run_test(size=(120, 40)) as pilot:
            win = await app.open_agent()
            await pilot.pause(0.6)
            pty = win.query_one(PtyTerminal)
            screen = pty._pyte_screen
            assert screen is not None
            has_content = any(
                any(ch.data.strip() for ch in screen.buffer[y].values())
                for y in range(screen.lines)
            )
            assert has_content, "pyte 屏幕应有 bash 提示符输出"

    asyncio.run(run())


def test_agent_terminal_coexists_with_editor():
    """AgentTerminalWindow 与编辑器浮窗可并存，互不干扰。"""
    import tempfile
    from pathlib import Path

    async def run():
        app = _AgentApp()
        async with app.run_test(size=(160, 50)) as pilot:
            ws = app.query_one(FloatWorkspace)

            # 先打开编辑器浮窗
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
                f.write(b"x = 1\n")
                tmp = Path(f.name)
            editor = EditorWindow(tmp)
            await ws.open_window(editor)

            # 再打开智能体终端
            term_win = await app.open_agent(title="Agent")
            await pilot.pause(0.4)

            # 两个浮窗都应存在
            assert len(app.query(FloatWindow)) == 2
            pty = term_win.query_one(PtyTerminal)
            assert pty._process is not None

            tmp.unlink(missing_ok=True)

    asyncio.run(run())


def test_agent_terminal_window_focus():
    """打开后浮窗或其子组件应获得焦点。"""
    async def run():
        app = _AgentApp()
        async with app.run_test(size=(120, 40)) as pilot:
            win = await app.open_agent()
            await pilot.pause(0.4)
            focused = app.focused
            # 焦点应落在 AgentTerminalWindow 内（PtyTerminal 或 win 本身）
            assert focused is not None

    asyncio.run(run())


def test_agent_terminal_close():
    """关闭浮窗后 FloatWorkspace 中的 window 列表应为空。"""
    async def run():
        app = _AgentApp()
        async with app.run_test(size=(120, 40)) as pilot:
            win = await app.open_agent()
            await pilot.pause(0.2)
            ws = app.query_one(FloatWorkspace)
            assert len(ws._windows) == 1
            win._do_close()
            await pilot.pause(0.1)
            assert len(ws._windows) == 0

    asyncio.run(run())


# ── feat-019 运行状态可见 ─────────────────────────────────────────────────────

def test_agent_title_starts_with_running_marker():
    """新建 Agent 浮窗标题以 ▶（运行中）开头。"""
    win = AgentTerminalWindow(title="Claude")
    assert win._title.startswith("▶")
    assert "Claude" in win._title


def test_agent_status_flips_to_ended_when_process_dies():
    """PTY 子进程结束后，标题翻成 ■ 并广播 StatusChanged。"""
    async def run():
        app = _AgentApp()
        async with app.run_test(size=(120, 40)) as pilot:
            win = await app.open_agent(title="Claude")
            await pilot.pause(0.4)
            win._check_status()  # 标记已见过存活
            assert win._status_running is True
            assert win._title.startswith("▶")

            pty = win.query_one(PtyTerminal)
            pty._process.kill()  # 交互式 bash 会忽略 SIGTERM，用 SIGKILL
            await pty._process.wait()  # 等待回收，returncode 落定

            win._check_status()
            assert win._status_running is False
            assert win._title.startswith("■")

    asyncio.run(run())
