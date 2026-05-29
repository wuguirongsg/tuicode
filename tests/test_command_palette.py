"""feat-018 测试 — 命令面板 Ctrl+Shift+P。"""
from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult

from tuicode.ui.command_palette_modal import CommandPaletteModal, PaletteCommand


# ── PaletteCommand.matches 过滤逻辑 ───────────────────────────────────────────


class TestPaletteCommandMatches:
    def _cmd(self, name: str = "Test", desc: str = "desc", keywords=None) -> PaletteCommand:
        return PaletteCommand(name=name, description=desc, callback=lambda: None,
                              keywords=keywords or [])

    def test_empty_query_matches_all(self):
        cmd = self._cmd()
        assert cmd.matches("") is True

    def test_name_match(self):
        cmd = self._cmd(name="布局预设")
        assert cmd.matches("布局") is True

    def test_desc_match(self):
        cmd = self._cmd(desc="打开 diff 预览")
        assert cmd.matches("diff") is True

    def test_keyword_match(self):
        cmd = self._cmd(keywords=["agent", "claude"])
        assert cmd.matches("claude") is True

    def test_no_match(self):
        cmd = self._cmd(name="布局预设", desc="切换", keywords=[])
        assert cmd.matches("退出") is False

    def test_case_insensitive(self):
        cmd = self._cmd(name="Git Commit")
        assert cmd.matches("git") is True


# ── CommandPaletteModal 交互 ───────────────────────────────────────────────────


def _make_cmd(name: str, executed: list) -> PaletteCommand:
    return PaletteCommand(
        name=name,
        description=f"{name} 的描述",
        callback=lambda n=name: executed.append(n),
    )


class _PaletteApp(App):
    CSS = "Screen { background: #000; }"

    def __init__(self, commands):
        super().__init__()
        self._commands = commands

    async def action_open_palette(self):
        await self.push_screen(CommandPaletteModal(self._commands))


class TestCommandPaletteModal:
    def test_escape_closes_modal(self):
        """Escape 键应关闭面板（dismiss None）。"""
        async def run():
            cmds = [_make_cmd("新建 Agent", [])]

            class _App(_PaletteApp):
                async def on_mount(self):
                    await self.push_screen(CommandPaletteModal(cmds))

            async with _App(cmds).run_test(headless=True) as pilot:
                await pilot.pause()
                assert len(pilot.app.screen_stack) == 2  # Modal 在栈上
                await pilot.press("escape")
                await pilot.pause()
                assert len(pilot.app.screen_stack) == 1  # Modal 已关闭

        asyncio.run(run())

    def test_enter_executes_first_command(self):
        """按 Enter 应执行选中命令并关闭面板。"""
        executed: list[str] = []

        async def run():
            cmds = [_make_cmd("布局预设", executed)]

            class _App(_PaletteApp):
                async def on_mount(self):
                    await self.push_screen(CommandPaletteModal(cmds))

            async with _App(cmds).run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()

        asyncio.run(run())
        assert executed == ["布局预设"]

    def test_search_filters_commands(self):
        """搜索框输入应过滤命令列表。"""
        async def run():
            cmds = [
                _make_cmd("布局预设", []),
                _make_cmd("新建 Agent", []),
                _make_cmd("Git commit", []),
            ]

            class _App(_PaletteApp):
                async def on_mount(self):
                    await self.push_screen(CommandPaletteModal(cmds))

            async with _App(cmds).run_test(headless=True) as pilot:
                await pilot.pause()
                modal = pilot.app.screen
                await pilot.press(*list("Agent"))
                await pilot.pause()
                # 过滤后只有 "新建 Agent" 匹配
                assert len(modal._filtered) == 1
                assert "Agent" in modal._filtered[0].name

        asyncio.run(run())

    def test_down_up_arrow_changes_selection(self):
        """上下箭头应移动选中索引。"""
        async def run():
            cmds = [_make_cmd(f"命令{i}", []) for i in range(3)]

            class _App(_PaletteApp):
                async def on_mount(self):
                    await self.push_screen(CommandPaletteModal(cmds))

            async with _App(cmds).run_test(headless=True) as pilot:
                await pilot.pause()
                modal = pilot.app.screen
                assert modal._selected_index == 0
                await pilot.press("down")
                await pilot.pause()
                assert modal._selected_index == 1
                await pilot.press("up")
                await pilot.pause()
                assert modal._selected_index == 0

        asyncio.run(run())

    def test_no_match_shows_empty_state(self):
        """搜索无结果时 _filtered 应为空。"""
        async def run():
            cmds = [_make_cmd("布局预设", [])]

            class _App(_PaletteApp):
                async def on_mount(self):
                    await self.push_screen(CommandPaletteModal(cmds))

            async with _App(cmds).run_test(headless=True) as pilot:
                await pilot.pause()
                modal = pilot.app.screen
                await pilot.press(*list("xyznotfound"))
                await pilot.pause()
                assert modal._filtered == []

        asyncio.run(run())
