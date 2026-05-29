"""feat-005/feat-015 单元测试 — RightPanel 文件树、Git stage/commit。"""
from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree, Input, Static

from tuicode.events import GitStatusChanged
from tuicode.git_status import GitError
from tuicode.ui.right_panel import CommitBar, GitFileList, RightPanel


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

    def test_contains_git_status(self, tmp_path: Path):
        """RightPanel 应包含 Git 状态区域。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                git_status = pilot.app.query_one("#git-status", Static)
                assert "git:" in str(git_status.content)

        asyncio.run(run())


# ── feat-020: 右栏 Tab 真切换 ─────────────────────────────────────────────────


class TestRightPanelTabSwitch:
    def test_default_shows_files_hides_git(self, tmp_path: Path):
        """默认显示文件树，隐藏 Git 视图，files Tab 高亮。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                app = pilot.app
                assert app.query_one("#files-view").display is True
                assert app.query_one("#git-view").display is False
                assert app.query_one("#tab-files", Static).has_class("rp-tab-active")
                assert not app.query_one("#tab-git", Static).has_class("rp-tab-active")

        asyncio.run(run())

    def test_switch_to_git_tab(self, tmp_path: Path):
        """切到 git Tab：显示 Git 视图、隐藏文件树，高亮跟随。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                app = pilot.app
                app.query_one(RightPanel)._show_tab("git")
                await pilot.pause()
                assert app.query_one("#files-view").display is False
                assert app.query_one("#git-view").display is True
                assert app.query_one("#tab-git", Static).has_class("rp-tab-active")
                assert not app.query_one("#tab-files", Static).has_class("rp-tab-active")

        asyncio.run(run())

    def test_switch_back_to_files_tab(self, tmp_path: Path):
        """git → files 切回，状态正确还原。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                panel = pilot.app.query_one(RightPanel)
                panel._show_tab("git")
                panel._show_tab("files")
                await pilot.pause()
                assert pilot.app.query_one("#files-view").display is True
                assert pilot.app.query_one("#git-view").display is False
                assert pilot.app.query_one("#tab-files", Static).has_class("rp-tab-active")

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


class TestGitStatus:
    def test_git_status_changed_updates_panel(self, tmp_path: Path):
        """GitStatusChanged 事件应刷新右栏 Git 状态文本。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                panel = pilot.app.query_one(RightPanel)
                panel.update_git_status(
                    GitStatusChanged(
                        branch="main",
                        changed_files=(" M app.py", "?? new.py"),
                    )
                )
                await pilot.pause()
                git_status = pilot.app.query_one("#git-status", Static)
                content = str(git_status.content)
                assert "main" in content
                assert "2 changed" in content
                git_files = pilot.app.query_one("#git-files", GitFileList)
                assert git_files._lines == (" M app.py", "?? new.py")

        asyncio.run(run())

    def test_git_file_selection_posts_diff_requested(self, tmp_path: Path):
        """选中 Git 文件列表项应触发 DiffRequested 消息。"""
        received: list[Path] = []

        async def run():
            class _App(PanelApp):
                def on_right_panel_diff_requested(
                    self, msg: RightPanel.DiffRequested
                ) -> None:
                    received.append(msg.path)

            async with _App(tmp_path).run_test(headless=True) as pilot:
                await pilot.pause()
                panel = pilot.app.query_one(RightPanel)
                panel.update_git_status(
                    GitStatusChanged(branch="main", changed_files=(" M app.py",))
                )
                git_files = pilot.app.query_one("#git-files", GitFileList)
                git_files.post_message(GitFileList.Selected(" M app.py"))
                await pilot.pause()

        asyncio.run(run())
        assert received == [tmp_path / "app.py"]


# ── feat-015: GitFileList 键盘 s/u 发送 StageRequested ────────────────────────


class TestGitFileListStageKeys:
    def test_s_key_posts_stage_requested(self):
        """s 键应发送 StageRequested(action='stage')。"""
        received: list[GitFileList.StageRequested] = []

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                def compose(self) -> ComposeResult:
                    yield GitFileList(id="gfl")

                def on_git_file_list_stage_requested(
                    self, msg: GitFileList.StageRequested
                ) -> None:
                    received.append(msg)

            async with _App().run_test(headless=True) as pilot:
                gfl = pilot.app.query_one("#gfl", GitFileList)
                gfl.update_files((" M app.py",))
                gfl.focus()
                await pilot.pause()
                await pilot.press("s")
                await pilot.pause()

        asyncio.run(run())
        assert len(received) == 1
        assert received[0].action == "stage"
        assert received[0].status_line == " M app.py"

    def test_u_key_posts_unstage_requested(self):
        """u 键应发送 StageRequested(action='unstage')。"""
        received: list[GitFileList.StageRequested] = []

        async def run():
            class _App(App):
                CSS = "Screen { background: #000; }"

                def compose(self) -> ComposeResult:
                    yield GitFileList(id="gfl")

                def on_git_file_list_stage_requested(
                    self, msg: GitFileList.StageRequested
                ) -> None:
                    received.append(msg)

            async with _App().run_test(headless=True) as pilot:
                gfl = pilot.app.query_one("#gfl", GitFileList)
                gfl.update_files(("M  app.py",))
                gfl.focus()
                await pilot.pause()
                await pilot.press("u")
                await pilot.pause()

        asyncio.run(run())
        assert len(received) == 1
        assert received[0].action == "unstage"


# ── feat-015: RightPanel stage 处理器 ─────────────────────────────────────────


class TestRightPanelStageHandlers:
    def test_stage_requested_calls_git_ops_stage(self, tmp_path: Path):
        """GitFileList.StageRequested(stage) 应调用 GitOps.stage。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                panel = pilot.app.query_one(RightPanel)
                mock_ops = MagicMock()
                panel._git_ops = mock_ops

                panel.update_git_status(
                    GitStatusChanged(branch="main", changed_files=(" M app.py",))
                )
                await pilot.pause()
                gfl = pilot.app.query_one(GitFileList)
                gfl.post_message(GitFileList.StageRequested(" M app.py", "stage"))
                await pilot.pause()

            mock_ops.stage.assert_called_once_with("app.py")

        asyncio.run(run())

    def test_unstage_requested_calls_git_ops_unstage(self, tmp_path: Path):
        """GitFileList.StageRequested(unstage) 应调用 GitOps.unstage。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                panel = pilot.app.query_one(RightPanel)
                mock_ops = MagicMock()
                panel._git_ops = mock_ops

                panel.update_git_status(
                    GitStatusChanged(branch="main", changed_files=("M  app.py",))
                )
                await pilot.pause()
                gfl = pilot.app.query_one(GitFileList)
                gfl.post_message(GitFileList.StageRequested("M  app.py", "unstage"))
                await pilot.pause()

            mock_ops.unstage.assert_called_once_with("app.py")

        asyncio.run(run())

    def test_stage_error_sets_commit_bar_error_status(self, tmp_path: Path):
        """GitOps 抛出 GitError 时 CommitBar 应显示错误状态。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                panel = pilot.app.query_one(RightPanel)
                mock_ops = MagicMock()
                mock_ops.stage.side_effect = GitError("permission denied")
                panel._git_ops = mock_ops

                panel.update_git_status(
                    GitStatusChanged(branch="main", changed_files=(" M f.py",))
                )
                await pilot.pause()
                gfl = pilot.app.query_one(GitFileList)
                gfl.post_message(GitFileList.StageRequested(" M f.py", "stage"))
                await pilot.pause()

                label = pilot.app.query_one("#commit-status", Static)
                assert "permission denied" in str(label.content)

        asyncio.run(run())


# ── feat-015: CommitBar 提交流程 ───────────────────────────────────────────────


class TestCommitBarFlow:
    def test_contains_commit_bar(self, tmp_path: Path):
        """RightPanel 应包含 CommitBar。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                assert pilot.app.query_one(CommitBar) is not None

        asyncio.run(run())

    def test_commit_calls_git_ops_commit(self, tmp_path: Path):
        """CommitBar 提交后应调用 GitOps.commit 并清空输入框。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                panel = pilot.app.query_one(RightPanel)
                mock_ops = MagicMock()
                panel._git_ops = mock_ops

                inp = pilot.app.query_one("#commit-input", Input)
                inp.focus()
                await pilot.pause()
                await pilot.press(*list("fix: my change"))
                await pilot.press("enter")
                await pilot.pause()

            mock_ops.commit.assert_called_once_with("fix: my change")

        asyncio.run(run())

    def test_commit_error_preserves_input(self, tmp_path: Path):
        """GitOps.commit 失败时输入框内容应保留，且显示错误。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                panel = pilot.app.query_one(RightPanel)
                mock_ops = MagicMock()
                mock_ops.commit.side_effect = GitError("nothing to commit")
                panel._git_ops = mock_ops

                inp = pilot.app.query_one("#commit-input", Input)
                inp.focus()
                await pilot.pause()
                await pilot.press(*list("my msg"))
                await pilot.press("enter")
                await pilot.pause()

                assert inp.value == "my msg"
                label = pilot.app.query_one("#commit-status", Static)
                assert "nothing to commit" in str(label.content)

        asyncio.run(run())

    def test_commit_success_clears_input(self, tmp_path: Path):
        """GitOps.commit 成功后输入框应清空。"""
        async def run():
            async with PanelApp(tmp_path).run_test(headless=True) as pilot:
                panel = pilot.app.query_one(RightPanel)
                mock_ops = MagicMock()
                panel._git_ops = mock_ops

                inp = pilot.app.query_one("#commit-input", Input)
                inp.focus()
                await pilot.pause()
                await pilot.press(*list("good commit"))
                await pilot.press("enter")
                await pilot.pause()

                assert inp.value == ""

        asyncio.run(run())
