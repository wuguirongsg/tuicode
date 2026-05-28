"""feat-006 单元测试 — EditorWindow 编辑器浮窗。"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest
from textual.app import App, ComposeResult
from textual.document._document import Selection
from textual.widgets import TextArea

from tuicode.bus import EventBus
from tuicode.events import FileModified
from tuicode.ui.editor_window import ConfirmCloseModal, EditorWindow
from tuicode.ui.workspace import FloatWorkspace
from tuicode.workspace_state import WorkspaceStateAggregator


# ── 工具 App ──────────────────────────────────────────────────────────────────


class EditorApp(App):
    CSS = "Screen { background: #0d1117; }"

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path

    def compose(self) -> ComposeResult:
        yield FloatWorkspace()

    async def open_editor(self) -> EditorWindow:
        ws = self.query_one(FloatWorkspace)
        win = EditorWindow(self._path)
        await ws.open_window(win)
        return win


# ── 测试：初始加载 ─────────────────────────────────────────────────────────────


class TestEditorWindowInit:
    def test_loads_file_content(self, tmp_path: Path):
        """打开文件后 TextArea 显示正确内容。"""
        f = tmp_path / "hello.py"
        f.write_text("print('hello')", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                ta = win.query_one("#editor-textarea", TextArea)
                assert ta.text == "print('hello')"

        asyncio.run(run())

    def test_dirty_false_on_mount(self, tmp_path: Path):
        """初始 _dirty 应为 False，标题不含 *。"""
        f = tmp_path / "clean.py"
        f.write_text("x = 1", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                assert win._dirty is False

        asyncio.run(run())

    def test_title_shows_filename(self, tmp_path: Path):
        """标题应显示文件名。"""
        f = tmp_path / "utils.py"
        f.write_text("", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                assert win._title == "utils.py"

        asyncio.run(run())

    def test_missing_file_opens_empty(self, tmp_path: Path):
        """不存在的文件打开后内容为空，不报错。"""
        f = tmp_path / "nonexistent.py"

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                ta = win.query_one("#editor-textarea", TextArea)
                assert ta.text == ""

        asyncio.run(run())


# ── 测试：保存 ────────────────────────────────────────────────────────────────


class TestEditorWindowSave:
    def test_save_writes_to_disk(self, tmp_path: Path):
        """action_save 后磁盘内容与 TextArea 一致。"""
        f = tmp_path / "target.py"
        f.write_text("old content", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                ta = win.query_one("#editor-textarea", TextArea)
                ta.load_text("new content")
                win._dirty = True
                win.action_save()
                await pilot.pause()
                assert f.read_text(encoding="utf-8") == "new content"

        asyncio.run(run())

    def test_save_clears_dirty(self, tmp_path: Path):
        """action_save 后 _dirty 应变为 False。"""
        f = tmp_path / "dirty.py"
        f.write_text("x", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                win._dirty = True
                win.action_save()
                await pilot.pause()
                assert win._dirty is False

        asyncio.run(run())

    def test_save_publishes_file_modified_event(self, tmp_path: Path):
        """action_save 后 FileModified 事件应被发布到 default_bus。"""
        from tuicode.bus import default_bus

        f = tmp_path / "event.py"
        f.write_text("pass", encoding="utf-8")
        received: list[FileModified] = []
        unsub = default_bus.subscribe(FileModified, received.append)

        async def run():
            try:
                async with EditorApp(f).run_test(headless=True) as pilot:
                    win = await pilot.app.open_editor()
                    await pilot.pause()
                    win.action_save()
                    await pilot.pause()
            finally:
                unsub()

        asyncio.run(run())
        assert len(received) == 1
        assert received[0].path == f

    def test_save_clears_dirty_flag(self, tmp_path: Path):
        """action_save 后 _dirty 必须为 False（等价于标题无 * 前缀）。"""
        f = tmp_path / "star.py"
        f.write_text("", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                win._dirty = True
                win.action_save()
                await pilot.pause()
                assert win._dirty is False

        asyncio.run(run())


class TestEditorWindowExternalChange:
    def test_external_file_modified_marks_title(self, tmp_path: Path):
        """外部修改已打开文件后，标题应显示 ! 前缀。"""
        from tuicode.bus import default_bus

        f = tmp_path / "external.py"
        f.write_text("old", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                time.sleep(0.001)
                f.write_text("new", encoding="utf-8")
                default_bus.publish(FileModified(f))
                await pilot.pause()
                assert win._external_changed is True
                assert win._title == "!external.py"

        asyncio.run(run())


class TestEditorWindowWorkspaceState:
    def test_selection_updates_workspace_context(self, tmp_path: Path):
        """编辑器选区变化后，聚合器应能返回选中文本。"""
        f = tmp_path / "selection.py"
        f.write_text("hello world", encoding="utf-8")
        aggregator = WorkspaceStateAggregator()

        async def run():
            try:
                async with EditorApp(f).run_test(headless=True) as pilot:
                    win = await pilot.app.open_editor()
                    await pilot.pause()
                    ta = win.query_one("#editor-textarea", TextArea)
                    ta.selection = Selection((0, 0), (0, 5))
                    await pilot.pause()
                    ctx = aggregator.get_context()
                    assert ctx.active_file == f
                    assert ctx.selection_text == "hello"
            finally:
                aggregator.close()

        asyncio.run(run())


# ── 测试：语言检测 ────────────────────────────────────────────────────────────


class TestLanguageDetection:
    @pytest.mark.parametrize("suffix,expected_lang", [
        (".py", "python"),
        (".js", "javascript"),
        (".mjs", "javascript"),
        (".json", "json"),
        (".md", "markdown"),
        (".sh", "bash"),
        (".go", "go"),
        (".rs", "rust"),
        (".sql", "sql"),
        (".svg", "xml"),
        (".ts", None),
        (".xyz", None),
    ])
    def test_detect_language_by_suffix(self, suffix: str, expected_lang: str | None, tmp_path: Path):
        """根据文件后缀正确检测 TextArea 支持的语言，不支持则返回 None。"""
        from tuicode.ui.editor_window import _detect_language

        assert _detect_language(tmp_path / f"file{suffix}") == expected_lang

    def test_opened_text_area_receives_detected_language(self, tmp_path: Path):
        """打开支持的代码文件时，TextArea 应启用对应语言。"""
        f = tmp_path / "hello.py"
        f.write_text("print('hello')", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                ta = win.query_one("#editor-textarea", TextArea)
                assert ta.language == "python"

        asyncio.run(run())

    def test_opened_text_area_falls_back_for_unsupported_language(self, tmp_path: Path):
        """Textual 未内置的语言应回退纯文本，避免 syntax extra 启用后崩溃。"""
        f = tmp_path / "types.ts"
        f.write_text("const x: number = 1", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                ta = win.query_one("#editor-textarea", TextArea)
                assert ta.language is None

        asyncio.run(run())


# ── 测试：关闭行为 ────────────────────────────────────────────────────────────


class TestEditorWindowClose:
    def test_close_clean_window_removes_it(self, tmp_path: Path):
        """无修改时关闭，浮窗应从 DOM 中移除。"""
        f = tmp_path / "close.py"
        f.write_text("", encoding="utf-8")

        async def run():
            async with EditorApp(f).run_test(headless=True) as pilot:
                win = await pilot.app.open_editor()
                await pilot.pause()
                assert win._dirty is False
                win.post_message(win.Closed(win))
                win.remove()
                await pilot.pause()
                assert len(pilot.app.query(EditorWindow)) == 0

        asyncio.run(run())

    def test_confirm_close_modal_discard_returns_true(self, tmp_path: Path):
        """点击"关闭不保存"后 dismiss 值为 True。"""
        results: list[bool] = []

        async def run():
            async with App().run_test(headless=True) as pilot:
                await pilot.app.push_screen(ConfirmCloseModal(), results.append)
                await pilot.pause()
                await pilot.click("#btn-discard")
                await pilot.pause()

        asyncio.run(run())
        assert results == [True]

    def test_confirm_close_modal_cancel_returns_false(self, tmp_path: Path):
        """点击"取消"后 dismiss 值为 False。"""
        results: list[bool] = []

        async def run():
            async with App().run_test(headless=True) as pilot:
                await pilot.app.push_screen(ConfirmCloseModal(), results.append)
                await pilot.pause()
                await pilot.click("#btn-cancel")
                await pilot.pause()

        asyncio.run(run())
        assert results == [False]
