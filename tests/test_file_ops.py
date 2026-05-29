"""feat-021 文件管理器测试 — 新建/重命名/删除/复制路径。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult

from tuicode.ui.file_modals import ConfirmDeleteModal, TextPromptModal
from tuicode.ui.file_tree import FileTree


class TreeApp(App):
    def __init__(self, root: Path) -> None:
        super().__init__()
        self._root = root

    def compose(self) -> ComposeResult:
        yield FileTree(self._root, id="file-tree")


def _run(coro_factory):
    async def run():
        await coro_factory()
    asyncio.run(run())


# ── 纯文件系统操作 ────────────────────────────────────────────────────────────


def test_create_file(tmp_path: Path):
    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            result = tree._create_entry(tmp_path, "new.py", is_dir=False)
            assert result == tmp_path / "new.py"
            assert (tmp_path / "new.py").is_file()

    _run(body)


def test_create_folder(tmp_path: Path):
    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            result = tree._create_entry(tmp_path, "pkg", is_dir=True)
            assert result == tmp_path / "pkg"
            assert (tmp_path / "pkg").is_dir()

    _run(body)


def test_create_duplicate_fails_gracefully(tmp_path: Path):
    (tmp_path / "dup.py").touch()

    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            assert tree._create_entry(tmp_path, "dup.py", is_dir=False) is None

    _run(body)


def test_rename_file(tmp_path: Path):
    src = tmp_path / "old.py"
    src.write_text("x = 1\n", encoding="utf-8")

    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            result = tree._do_rename(src, "renamed.py")
            assert result == tmp_path / "renamed.py"
            assert not src.exists()
            assert (tmp_path / "renamed.py").read_text() == "x = 1\n"

    _run(body)


def test_delete_file(tmp_path: Path):
    target = tmp_path / "gone.py"
    target.touch()

    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            assert tree._do_delete(target) is True
            assert not target.exists()

    _run(body)


def test_delete_folder_recursive(tmp_path: Path):
    d = tmp_path / "sub"
    d.mkdir()
    (d / "inner.txt").write_text("hi", encoding="utf-8")

    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            assert tree._do_delete(d) is True
            assert not d.exists()

    _run(body)


# ── 落点与路径复制 ────────────────────────────────────────────────────────────


def test_target_dir_defaults_to_root(tmp_path: Path):
    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            assert tree._target_dir().resolve() == tmp_path.resolve()

    _run(body)


def test_target_dir_uses_parent_for_file(tmp_path: Path):
    f = tmp_path / "a.py"
    f.touch()

    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            tree._current_path = lambda: f
            assert tree._target_dir() == tmp_path

    _run(body)


def test_copy_abs_path(tmp_path: Path):
    f = tmp_path / "a.py"
    f.touch()

    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            captured: list[str] = []
            pilot.app.copy_to_clipboard = lambda s: captured.append(s)
            tree._current_path = lambda: f
            tree.action_copy_abs_path()
            assert captured == [str(f.resolve())]

    _run(body)


def test_copy_rel_path(tmp_path: Path):
    sub = tmp_path / "sub"
    sub.mkdir()
    f = sub / "b.py"
    f.touch()

    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            captured: list[str] = []
            pilot.app.copy_to_clipboard = lambda s: captured.append(s)
            tree._current_path = lambda: f
            tree.action_copy_rel_path()
            assert captured == [str(Path("sub") / "b.py")]

    _run(body)


# ── 快捷键 → 模态 接线 ────────────────────────────────────────────────────────


def test_action_new_file_opens_prompt_modal(tmp_path: Path):
    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            pilot.app.query_one(FileTree).action_new_file()
            await pilot.pause()
            assert isinstance(pilot.app.screen, TextPromptModal)

    _run(body)


def test_action_delete_opens_confirm_modal(tmp_path: Path):
    f = tmp_path / "a.py"
    f.touch()

    async def body():
        async with TreeApp(tmp_path).run_test() as pilot:
            await pilot.pause()
            tree = pilot.app.query_one(FileTree)
            tree._current_path = lambda: f
            tree.action_delete()
            await pilot.pause()
            assert isinstance(pilot.app.screen, ConfirmDeleteModal)

    _run(body)
