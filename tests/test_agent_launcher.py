"""feat-017 测试 — 多 Agent PTY 会话启动器。"""
from __future__ import annotations

import asyncio

from rich.cells import cell_len
from textual.app import App, ComposeResult

from tuicode.ui.agent_terminal_window import AgentTerminalWindow
from tuicode.ui.agent_session_modal import AgentSessionHistoryModal, _SessionGrid
from tuicode.ui.new_agent_modal import (
    AgentConfig,
    AgentOption,
    NewAgentModal,
    _AgentGrid,
    _PRESETS,
    detect_installed_agents,
    load_cached_agents,
    save_cached_agents,
)
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

    def test_detect_installed_agents_uses_passive_executable_check(self, monkeypatch):
        """检测本地 Agent 只看可执行文件是否存在，不启动命令。"""

        def fake_which(name: str) -> str | None:
            return "/usr/local/bin/codex" if name == "codex" else None

        monkeypatch.setattr("tuicode.ui.new_agent_modal.shutil.which", fake_which)
        monkeypatch.setattr(
            "tuicode.ui.new_agent_modal.Path.exists",
            lambda self: False,
        )

        detected = detect_installed_agents()
        assert [agent.agent_type for agent in detected] == ["codex"]

    def test_cached_agents_round_trip(self, tmp_path):
        cache_path = tmp_path / "agents.json"
        agents = [
            AgentOption("Codex", "codex", "codex"),
            AgentOption("myagent", "myagent --flag", "custom", "custom"),
        ]

        save_cached_agents(agents, cache_path)
        loaded, exists = load_cached_agents(cache_path)

        assert exists is True
        assert loaded == agents

    def test_initial_agent_grid_is_empty_before_detection(self, tmp_path):
        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        NewAgentModal(
                            detector=lambda: [],
                            cache_path=tmp_path / "missing.json",
                        )
                    )

            app = _App()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause()
                grid = app.screen_stack[-1].query_one(_AgentGrid)
                assert grid._options == []
                assert grid.scanned is False

        asyncio.run(run())

    def test_cached_agents_load_on_open(self, tmp_path):
        option = AgentOption("Codex", "codex", "codex")
        cache_path = tmp_path / "agents.json"
        save_cached_agents([option], cache_path)

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        NewAgentModal(
                            detector=lambda: [],
                            cache_path=cache_path,
                        )
                    )

            app = _App()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause()
                grid = app.screen_stack[-1].query_one(_AgentGrid)
                assert grid._options == [option]
                assert grid.scanned is True

        asyncio.run(run())

    def test_detect_button_populates_agent_grid_and_updates_cache(self, tmp_path):
        option = AgentOption("Codex", "codex", "codex")
        cache_path = tmp_path / "agents.json"

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        NewAgentModal(
                            detector=lambda: [option],
                            cache_path=cache_path,
                        )
                    )

            app = _App()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.click("#btn-detect")
                await pilot.pause()
                grid = app.screen_stack[-1].query_one(_AgentGrid)
                assert grid._options == [option]
                assert grid.scanned is True

        asyncio.run(run())
        loaded, exists = load_cached_agents(cache_path)
        assert exists is True
        assert loaded == [option]

    def test_preset_dismiss_on_button(self, tmp_path):
        """检测后启动选中 Agent 应 dismiss 并返回 AgentConfig。"""
        received: list[AgentConfig | None] = []
        label, command, agent_type = _PRESETS[0]
        option = AgentOption(label, command, agent_type)
        cache_path = tmp_path / "agents.json"

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        NewAgentModal(
                            detector=lambda: [option],
                            cache_path=cache_path,
                        ),
                        received.append,
                    )

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.click("#btn-detect")
                await pilot.pause()
                await pilot.click("#btn-ok")
                await pilot.pause()

        asyncio.run(run())
        assert len(received) == 1
        result = received[0]
        assert result is not None
        assert result.agent_type == agent_type
        assert result.command == command

    def test_cancel_button_dismisses_none(self, tmp_path):
        """点击取消应 dismiss None。"""
        received: list[AgentConfig | None] = []
        cache_path = tmp_path / "agents.json"

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        NewAgentModal(cache_path=cache_path), received.append
                    )

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.click("#btn-cancel")
                await pilot.pause()

        asyncio.run(run())
        assert received == [None]

    def test_escape_dismisses_none(self, tmp_path):
        """Escape 键应 dismiss None。"""
        received: list[AgentConfig | None] = []
        cache_path = tmp_path / "agents.json"

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        NewAgentModal(cache_path=cache_path), received.append
                    )

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(run())
        assert received == [None]

    def test_custom_command_ok(self, tmp_path):
        """自定义命令 + 点击启动应返回 custom AgentConfig。"""
        received: list[AgentConfig | None] = []
        cache_path = tmp_path / "agents.json"

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        NewAgentModal(cache_path=cache_path), received.append
                    )

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
        loaded, exists = load_cached_agents(cache_path)
        assert exists is True
        assert loaded == [
            AgentOption("myagent", "myagent --flag", "custom", "custom")
        ]

    def test_custom_command_can_be_added_to_agent_grid(self, tmp_path):
        """自定义命令可加入与检测结果相同的三列 Agent 列表。"""
        cache_path = tmp_path / "agents.json"

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                async def on_mount(self) -> None:
                    await self.push_screen(
                        NewAgentModal(
                            detector=lambda: [],
                            cache_path=cache_path,
                        )
                    )

            app = _App()
            async with app.run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.click("#custom-input")
                await pilot.press(*list("myagent --flag"))
                await pilot.click("#btn-add-custom")
                await pilot.pause()
                grid = app.screen_stack[-1].query_one(_AgentGrid)
                assert len(grid._options) == 1
                assert grid._options[0].command == "myagent --flag"
                assert grid._options[0].source == "custom"

        asyncio.run(run())
        loaded, exists = load_cached_agents(cache_path)
        assert exists is True
        assert loaded == [
            AgentOption("myagent", "myagent --flag", "custom", "custom")
        ]


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

    def test_grid_cards_render_with_borders(self):
        record = AgentSessionRecord(
            session_id="abc123ef",
            project_root="/tmp/project",
            title="Claude Code",
            agent_type="claude",
            command="claude",
            created_at="2026-05-30T00:00:00+00:00",
            updated_at="2026-05-30T00:01:00+00:00",
            status="ended",
            summary="任务：卡片边框",
        )
        grid = _SessionGrid([record])

        top, _ = grid._card_line(record, 0, 0, 32)
        title, _ = grid._card_line(record, 0, 1, 32)
        bottom, _ = grid._card_line(record, 0, 5, 32)

        assert top.startswith("╭") and top.endswith("╮")
        assert title.startswith("│ ") and title.endswith("│")
        assert bottom.startswith("╰") and bottom.endswith("╯")

    def test_grid_card_lines_fit_cell_width_with_cjk(self):
        record = AgentSessionRecord(
            session_id="abc123ef",
            project_root="/tmp/project",
            title="Claude Code",
            agent_type="claude",
            command="claude",
            created_at="2026-05-30T00:00:00+00:00",
            updated_at="2026-05-30T00:01:00+00:00",
            status="ended",
            summary="任务：很长很长很长的中文标题会挤出边框",
        )
        grid = _SessionGrid([record])

        for line in range(grid.CARD_H):
            text, _ = grid._card_line(record, 0, line, 24)
            assert cell_len(text) == 24

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
