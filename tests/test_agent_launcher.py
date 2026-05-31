"""feat-017 测试 — 多 Agent PTY 会话启动器。"""
from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult

from tuicode.ui.agent_terminal_window import AgentTerminalWindow
from tuicode.ui.agent_session_modal import AgentSessionHistoryModal, _SessionGrid
from tuicode.ui.new_agent_modal import AgentConfig, NewAgentModal, _PRESETS
from tuicode.agent_memory import AgentSessionRecord


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

    def test_can_reuse_saved_session_id_for_memory_reopen(self):
        win = AgentTerminalWindow(session_id="feed1234")
        assert win.session_id == "feed1234"
        assert "feed1234" in win._title


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


class TestAgentSessionHistoryModal:
    def test_review_then_continue_history_session(self):
        received: list[AgentSessionRecord | None] = []
        record = AgentSessionRecord(
            session_id="abc123ef",
            project_root="/tmp/project",
            title="Claude Code",
            agent_type="claude",
            command="claude",
            created_at="2026-05-30T00:00:00+00:00",
            updated_at="2026-05-30T00:01:00+00:00",
            status="ended",
            summary="目标：优化历史会话列表",
            last_output="recent output",
        )

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        AgentSessionHistoryModal([record]), received.append
                    )

            app = _App()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause()
                app.screen_stack[-1].query_one(_SessionGrid).open_selected()
                await pilot.pause()
                assert received == []
                await pilot.click("#detail-continue")
                await pilot.pause()

        asyncio.run(run())
        assert received == [record]

    def test_back_from_detail_keeps_history_modal_open(self):
        received: list[AgentSessionRecord | None] = []
        record = AgentSessionRecord(
            session_id="abc123ef",
            project_root="/tmp/project",
            title="Claude Code",
            agent_type="claude",
            command="claude",
            created_at="2026-05-30T00:00:00+00:00",
            updated_at="2026-05-30T00:01:00+00:00",
            status="ended",
            summary="任务：先看详情",
        )

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        AgentSessionHistoryModal([record]), received.append
                    )

            app = _App()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause()
                app.screen_stack[-1].query_one(_SessionGrid).open_selected()
                await pilot.pause()
                await pilot.click("#detail-back")
                await pilot.pause()
                assert received == []
                await pilot.click("#history-cancel")
                await pilot.pause()

        asyncio.run(run())
        assert received == [None]

    def test_arrow_keys_move_grid_selection(self):
        records = [
            AgentSessionRecord(
                session_id=f"abc123e{i}",
                project_root="/tmp/project",
                title="Claude Code",
                agent_type="claude",
                command="claude",
                created_at="2026-05-30T00:00:00+00:00",
                updated_at="2026-05-30T00:01:00+00:00",
                status="ended",
                summary=f"任务：会话 {i}",
            )
            for i in range(6)
        ]

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(AgentSessionHistoryModal(records))

            app = _App()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause()
                grid = app.screen_stack[-1].query_one(_SessionGrid)
                assert grid.selected_index == 0
                await pilot.press("right")
                await pilot.pause()
                assert grid.selected_index == 1
                await pilot.press("down")
                await pilot.pause()
                assert grid.selected_index == 4
                await pilot.press("left")
                await pilot.pause()
                assert grid.selected_index == 3

        asyncio.run(run())

    def test_delete_from_detail_refreshes_history_grid(self):
        received: list[AgentSessionRecord | None] = []
        deleted: list[str] = []
        records = [
            AgentSessionRecord(
                session_id="abc123ef",
                project_root="/tmp/project",
                title="Claude Code",
                agent_type="claude",
                command="claude",
                created_at="2026-05-30T00:00:00+00:00",
                updated_at="2026-05-30T00:01:00+00:00",
                status="ended",
                summary="任务：删除",
            )
        ]

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        AgentSessionHistoryModal(records, on_delete=lambda sid: deleted.append(sid) or True),
                        received.append,
                    )

            app = _App()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause()
                app.screen_stack[-1].query_one(_SessionGrid).open_selected()
                await pilot.pause()
                await pilot.click("#detail-delete")
                await pilot.pause()
                assert deleted == ["abc123ef"]
                assert app.screen_stack[-1].query_one(_SessionGrid)._sessions == []
                await pilot.click("#history-cancel")
                await pilot.pause()

        asyncio.run(run())
        assert received == [None]
