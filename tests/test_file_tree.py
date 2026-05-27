"""feat-005 单元测试 — RightPanel 文件树 + FileRequested 消息。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree

from tuicode.ui.right_panel import RightPanel


# ── 工具 App ──────────────────────────────────────────────────────────────────


class PanelApp(App):
    CSS = "Screen { background: #0d1117; }"

    def __init__(self, root: Path) -> None:
        super().__init__()
        self._root = root

    def compose(self) -> ComposeResult:
        yield RightPanel(self._root)


# ── 测试：组合结构 ─────────────────────────────────────────────────────────────


class TestRightPanelCompose:
    def test_contains_directory_tree(self, tmp_path: Path):
        """RightPanel 应包含 DirectoryTree widget。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                assert pilot.app.query_one(DirectoryTree) is not None

        asyncio.run(run())

    def test_directory_tree_root_is_configured(self, tmp_path: Path):
        """DirectoryTree 的根目录应与 RightPanel 的 root 参数一致。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                dt = pilot.app.query_one(DirectoryTree)
                assert dt.path == tmp_path

        asyncio.run(run())

    def test_contains_tab_bar(self, tmp_path: Path):
        """RightPanel 应包含 rp-tabs 区域，显示 files 标签。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                tabs = pilot.app.query_one("#rp-tabs")
                assert tabs is not None

        asyncio.run(run())


# ── 测试：FileRequested 消息 ──────────────────────────────────────────────────


class TestFileRequested:
    def test_file_selected_posts_file_requested(self, tmp_path: Path):
        """DirectoryTree.FileSelected 事件应触发 RightPanel.FileRequested 消息。"""
        target = tmp_path / "main.py"
        target.write_text("x = 1", encoding="utf-8")
        received: list[RightPanel.FileRequested] = []

        async def run():
            class _App(PanelApp):
                def on_right_panel_file_requested(
                    self, msg: RightPanel.FileRequested
                ) -> None:
                    received.append(msg)

            async with _App(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                panel = pilot.app.query_one(RightPanel)
                panel.post_message(
                    DirectoryTree.FileSelected(
                        pilot.app.query_one(DirectoryTree), target
                    )
                )
                await pilot.pause()

        asyncio.run(run())
        assert len(received) == 1
        assert received[0].path == target

    def test_file_requested_path_matches_selection(self, tmp_path: Path):
        """FileRequested.path 应与 FileSelected 的路径完全一致。"""
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("", encoding="utf-8")
        f2.write_text("", encoding="utf-8")
        received: list[Path] = []

        async def run():
            class _App(PanelApp):
                def on_right_panel_file_requested(
                    self, msg: RightPanel.FileRequested
                ) -> None:
                    received.append(msg.path)

            async with _App(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                panel = pilot.app.query_one(RightPanel)
                dt = pilot.app.query_one(DirectoryTree)
                panel.post_message(DirectoryTree.FileSelected(dt, f2))
                await pilot.pause()

        asyncio.run(run())
        assert received == [f2]

    def test_default_root_is_cwd(self):
        """RightPanel() 不传 root 时，默认根目录为 Path.cwd()。"""
        panel = RightPanel()
        assert panel._root == Path.cwd()

    def test_custom_root_is_respected(self, tmp_path: Path):
        """传入 root 参数时应使用该路径。"""
        panel = RightPanel(root=tmp_path)
        assert panel._root == tmp_path
