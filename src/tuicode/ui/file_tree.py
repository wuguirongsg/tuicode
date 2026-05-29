"""feat-021 可操作文件树 — 在只读 DirectoryTree 基础上加新建/重命名/删除/复制路径。

用户手动操作直接执行（不发 ToolCallRequested，该审批约束仅针对智能体写文件）。
删除前弹确认框防误删；任一写操作后 reload() 刷新并发 FileModified 联动 Git。
"""
from __future__ import annotations

import shutil
from pathlib import Path

from textual.widgets import DirectoryTree

from tuicode.bus import default_bus
from tuicode.events import FileModified
from tuicode.i18n import t
from tuicode.ui.file_modals import ConfirmDeleteModal, TextPromptModal


class FileTree(DirectoryTree):
    """带文件操作快捷键的文件树。聚焦时可用：

    a 新建文件 · A 新建文件夹 · r 重命名 · d 删除 · y 复制绝对路径 · Y 复制相对路径
    """

    BINDINGS = [
        ("a", "new_file", "新建文件"),
        ("A", "new_folder", "新建文件夹"),
        ("r", "rename", "重命名"),
        ("d", "delete", "删除"),
        ("y", "copy_abs_path", "复制绝对路径"),
        ("Y", "copy_rel_path", "复制相对路径"),
    ]

    # ── 当前选中路径 ──────────────────────────────────────────────────────────

    def _current_path(self) -> Path | None:
        node = self.cursor_node
        if node is None or node.data is None:
            return None
        path = getattr(node.data, "path", None)
        return Path(path) if path is not None else None

    def _target_dir(self) -> Path:
        """新建操作的落点：选中目录则在其中，选中文件则在其父目录。"""
        path = self._current_path()
        if path is None:
            return Path(self.path)
        return path if path.is_dir() else path.parent

    # ── 操作完成后的统一收尾 ──────────────────────────────────────────────────

    def _after_change(self, path: Path) -> None:
        self.reload()
        default_bus.publish(FileModified(path))

    def _notify(self, key: str, **kwargs) -> None:
        try:
            self.app.notify(t(key, **kwargs))
        except Exception:
            pass

    def _fail(self, exc: Exception) -> None:
        try:
            self.app.notify(t("fileop.failed", err=str(exc)), severity="error")
        except Exception:
            pass

    # ── 纯文件系统操作（可单测，不依赖模态）────────────────────────────────────

    def _create_entry(self, directory: Path, name: str, is_dir: bool) -> Path | None:
        target = directory / name
        try:
            if is_dir:
                target.mkdir(parents=True, exist_ok=False)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch(exist_ok=False)
        except (OSError, FileExistsError) as exc:
            self._fail(exc)
            return None
        self._after_change(target)
        self._notify("fileop.created", name=name)
        return target

    def _do_rename(self, path: Path, new_name: str) -> Path | None:
        target = path.with_name(new_name)
        try:
            path.rename(target)
        except OSError as exc:
            self._fail(exc)
            return None
        self._after_change(target)
        self._notify("fileop.renamed", name=new_name)
        return target

    def _do_delete(self, path: Path) -> bool:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            self._fail(exc)
            return False
        self._after_change(path)
        self._notify("fileop.deleted", name=path.name)
        return True

    # ── 快捷键动作 ────────────────────────────────────────────────────────────

    def action_new_file(self) -> None:
        directory = self._target_dir()

        def done(name: str | None) -> None:
            if name:
                self._create_entry(directory, name, is_dir=False)

        self.app.push_screen(
            TextPromptModal(t("fileop.new_file"), placeholder=t("fileop.name_hint")),
            done,
        )

    def action_new_folder(self) -> None:
        directory = self._target_dir()

        def done(name: str | None) -> None:
            if name:
                self._create_entry(directory, name, is_dir=True)

        self.app.push_screen(
            TextPromptModal(t("fileop.new_folder"), placeholder=t("fileop.name_hint")),
            done,
        )

    def action_rename(self) -> None:
        path = self._current_path()
        if path is None:
            return

        def done(name: str | None) -> None:
            if name and name != path.name:
                self._do_rename(path, name)

        self.app.push_screen(
            TextPromptModal(t("fileop.rename"), initial=path.name),
            done,
        )

    def action_delete(self) -> None:
        path = self._current_path()
        if path is None:
            return

        def done(confirmed: bool) -> None:
            if confirmed:
                self._do_delete(path)

        self.app.push_screen(ConfirmDeleteModal(path.name), done)

    def action_copy_abs_path(self) -> None:
        path = self._current_path()
        if path is None:
            return
        self.app.copy_to_clipboard(str(path.resolve()))
        self._notify("fileop.copied_abs")

    def action_copy_rel_path(self) -> None:
        path = self._current_path()
        if path is None:
            return
        try:
            rel = path.resolve().relative_to(Path(self.path).resolve())
        except ValueError:
            rel = path
        self.app.copy_to_clipboard(str(rel))
        self._notify("fileop.copied_rel")
