"""feat-005 文件树 — 右栏 files Tab，DirectoryTree + FileRequested 消息。"""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual import events
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DirectoryTree, Static

from tuicode.bus import default_bus
from tuicode.events import FileModified, GitStatusChanged
from tuicode.i18n import t
from tuicode.ui.mascot import MascotPanel


class GitFileList(Widget):
    """Focusable list of changed Git files."""

    can_focus = True

    class Selected(Message):
        def __init__(self, status_line: str) -> None:
            super().__init__()
            self.status_line = status_line

    DEFAULT_CSS = """
    GitFileList {
        height: auto;
        max-height: 7;
        padding: 0 1;
        color: $text-muted;
        background: $panel;
    }
    GitFileList:focus {
        color: $text;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._lines: tuple[str, ...] = ()
        self._selected_index = 0

    def update_files(self, lines: tuple[str, ...]) -> None:
        self._lines = lines
        if not lines:
            self._selected_index = 0
        else:
            self._selected_index = min(self._selected_index, len(lines) - 1)
        self.refresh()

    def render(self) -> str:
        if not self._lines:
            return ""
        rendered: list[str] = []
        for index, line in enumerate(self._lines[:7]):
            marker = ">" if index == self._selected_index else " "
            rendered.append(f"{marker} {line}")
        return "\n".join(rendered)

    def on_key(self, event: events.Key) -> None:
        if not self._lines:
            return
        if event.key in {"down", "j"}:
            self._selected_index = min(self._selected_index + 1, len(self._lines) - 1)
            self.refresh()
            event.stop()
        elif event.key in {"up", "k"}:
            self._selected_index = max(self._selected_index - 1, 0)
            self.refresh()
            event.stop()
        elif event.key == "enter":
            self.post_message(self.Selected(self._lines[self._selected_index]))
            event.stop()

    def on_click(self, event: events.Click) -> None:
        if not self._lines:
            return
        if 0 <= event.y < min(len(self._lines), 7):
            self._selected_index = event.y
            self.refresh()
            self.post_message(self.Selected(self._lines[self._selected_index]))
            event.stop()


class RightPanel(Widget):
    """右侧固定工具栏 — files Tab 显示项目文件树。"""

    class FileRequested(Message):
        """用户在文件树中选中文件，通知 App 打开编辑器浮窗。"""
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    class DiffRequested(Message):
        """用户在 Git 状态列表中选中文件，通知 App 打开 diff 预览。"""
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    DEFAULT_CSS = """
    RightPanel {
        width: 28;
        height: 1fr;
        border-left: solid $panel-lighten-1;
        layout: vertical;
        background: $surface;
    }
    RightPanel #rp-tabs {
        height: 1;
        background: $panel;
        layout: horizontal;
        padding: 0 1;
    }
    RightPanel .rp-tab {
        width: auto;
        padding: 0 2;
        color: $text-muted;
    }
    RightPanel .rp-tab:hover {
        color: $text;
    }
    RightPanel .rp-tab-active {
        width: auto;
        padding: 0 2;
        color: $accent;
        text-style: bold;
    }
    RightPanel DirectoryTree {
        height: 1fr;
        background: $surface;
    }
    RightPanel #git-status {
        height: auto;
        max-height: 4;
        padding: 0 1;
        color: $text-muted;
        background: $panel;
    }
    """

    def __init__(self, root: Path | str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._root = Path(root) if root else Path.cwd()
        self._unsubscribe_file_modified = None
        self._unsubscribe_git_status = None

    def compose(self) -> ComposeResult:
        yield MascotPanel(id="rp-mascot")
        with Widget(id="rp-tabs"):
            yield Static(t("panel.tab_files"), classes="rp-tab-active")
            yield Static(t("panel.tab_git"), classes="rp-tab")
        yield DirectoryTree(self._root, id="file-tree")
        yield Static("git: checking...", id="git-status")
        yield GitFileList(id="git-files")

    def on_mount(self) -> None:
        self._unsubscribe_file_modified = default_bus.subscribe(
            FileModified, self._on_file_modified
        )
        self._unsubscribe_git_status = default_bus.subscribe(
            GitStatusChanged, self._on_git_status_changed
        )

    def on_unmount(self) -> None:
        if self._unsubscribe_file_modified is not None:
            self._unsubscribe_file_modified()
            self._unsubscribe_file_modified = None
        if self._unsubscribe_git_status is not None:
            self._unsubscribe_git_status()
            self._unsubscribe_git_status = None

    def set_mascot_state(self, state: str, auto_reset: float = 0.0) -> None:
        self.query_one(MascotPanel).set_state(state, auto_reset)

    def refresh_file_tree(self) -> None:
        self.query_one("#file-tree", DirectoryTree).reload()

    def _on_file_modified(self, event: FileModified) -> None:
        self.call_later(self.refresh_file_tree)

    def _on_git_status_changed(self, event: GitStatusChanged) -> None:
        self.call_later(self.update_git_status, event)

    def update_git_status(self, event: GitStatusChanged) -> None:
        branch = event.branch or "(no branch)"
        if event.changed_files:
            content = f"git: {branch} · {len(event.changed_files)} changed"
        else:
            content = f"git: {branch} · clean"
        self.query_one("#git-status", Static).update(content)
        self.query_one("#git-files", GitFileList).update_files(event.changed_files)

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        event.stop()
        self.post_message(self.FileRequested(event.path))

    def on_git_file_list_selected(self, event: GitFileList.Selected) -> None:
        event.stop()
        rel_path = self._path_from_status_line(event.status_line)
        if rel_path:
            self.post_message(self.DiffRequested(self._root / rel_path))

    def _path_from_status_line(self, status_line: str) -> Path | None:
        if len(status_line) < 4:
            return None
        path = status_line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        return Path(path.strip('"')) if path else None
