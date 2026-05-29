"""feat-017 测试 — 多 Agent PTY 会话启动器。"""
from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult

from tuicode.ui.agent_terminal_window import AgentTerminalWindow
from tuicode.ui.new_agent_modal import AgentConfig, NewAgentModal, _PRESETS


# ── AgentTerminalWindow 身份属性 ───────────────────────────────────────────────


class TestAgentTerminalWindowIdentity:
    def test_session_id_is_8_hex_chars(self):
        win = AgentTerminalWindow()
        assert len(win.session_id) == 8
        assert all(c in "0123456789abcdef" for c in win.session_id)

    def test_two_windows_have_distinct_session_ids(self):
        w1 = AgentTerminalWindow()
        w2 = AgentTerminalWindow()
        assert w1.session_id != w2.session_id

    def test_agent_type_stored(self):
        win = AgentTerminalWindow(agent_type="claude")
        assert win.agent_type == "claude"

    def test_session_id_in_title(self):
        win = AgentTerminalWindow(title="Claude", agent_type="claude")
        assert win.session_id in win._title

    def test_default_agent_type_is_bash(self):
        win = AgentTerminalWindow()
        assert win.agent_type == "bash"


# ── NewAgentModal ─────────────────────────────────────────────────────────────


class TestNewAgentModal:
    def test_presets_non_empty(self):
        assert len(_PRESETS) >= 3

    def test_preset_dismiss_on_button(self):
        """点击预设按钮应 dismiss 并返回 AgentConfig。"""
        received: list[AgentConfig | None] = []

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(NewAgentModal(), received.append)

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                # 点击第一个预设（Claude Code）
                _, _, atype = _PRESETS[0]
                await pilot.click(f"#preset-{atype}")
                await pilot.pause()

        asyncio.run(run())
        assert len(received) == 1
        result = received[0]
        assert result is not None
        assert result.agent_type == _PRESETS[0][2]
        assert result.command == _PRESETS[0][1]

    def test_cancel_button_dismisses_none(self):
        """点击取消应 dismiss None。"""
        received: list[AgentConfig | None] = []

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(NewAgentModal(), received.append)

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.click("#btn-cancel")
                await pilot.pause()

        asyncio.run(run())
        assert received == [None]

    def test_escape_dismisses_none(self):
        """Escape 键应 dismiss None。"""
        received: list[AgentConfig | None] = []

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(NewAgentModal(), received.append)

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(run())
        assert received == [None]

    def test_custom_command_ok(self):
        """自定义命令 + 点击启动应返回 custom AgentConfig。"""
        received: list[AgentConfig | None] = []

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(NewAgentModal(), received.append)

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.click("#custom-input")
                await pilot.press(*list("myagent --flag"))
                await pilot.click("#btn-ok")
                await pilot.pause()

        asyncio.run(run())
        assert len(received) == 1
        result = received[0]
        assert result is not None
        assert result.command == "myagent --flag"
        assert result.agent_type == "custom"
