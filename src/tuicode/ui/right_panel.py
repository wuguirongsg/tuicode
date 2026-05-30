"""右侧固定工具栏 — 文件树、Git 状态、stage/unstage/commit 操作。"""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual import events
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DirectoryTree, Input, Label, ListItem, ListView, Static

from tuicode.bus import default_bus
from tuicode.events import FileModified, GitStatusChanged
from tuicode.git_status import GitError, GitOps
from tuicode.i18n import t
from tuicode.ui.file_tree import FileTree
from tuicode.ui.mascot import MascotPanel


def _status_markup(xy: str) -> str:
    """Map 2-char git status code to a coloured Rich markup indicator."""
    x = xy[0] if xy else "?"
    y = xy[1] if len(xy) > 1 else " "
    if xy == "??":
        return "[dim]?[/dim]"
    if x == "R":
        return "[cyan]R[/cyan]"
    if x == "A":
        return "[green]A[/green]"
    if x == "D" or y == "D":
        return "[red]D[/red]"
    if x == "M" and y == "M":
        return "[yellow]±[/yellow]"
    if x == "M":
        return "[green]M[/green]"
    if y == "M":
        return "[yellow]M[/yellow]"
    return "[dim]?[/dim]"


class GitFileList(Widget):
    """Focusable list of changed Git files with stage/unstage support."""

    can_focus = True

    class Selected(Message):
        def __init__(self, status_line: str) -> None:
            super().__init__()
            self.status_line = status_line

    class StageRequested(Message):
        """User pressed s (stage) or u (unstage) on the selected file."""
        def __init__(self, status_line: str, action: str) -> None:
            super().__init__()
            self.status_line = status_line
            self.action = action  # "stage" or "unstage"

    DEFAULT_CSS = """
    GitFileList {
        height: auto;
        max-height: 10;
        background: $surface;
    }
    GitFileList ListView {
        height: auto;
        max-height: 10;
        background: $surface;
        padding: 0;
    }
    GitFileList ListView > ListItem {
        padding: 0 1;
        height: 1;
        background: $surface;
    }
    GitFileList ListView > ListItem.--highlight {
        background: $accent 15%;
    }
    GitFileList ListView:focus > ListItem.--highlight {
        background: $accent 30%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._lines: tuple[str, ...] = ()
        self._selected_index = 0

    def compose(self) -> ComposeResult:
        lv = ListView()
        lv.can_focus = False
        yield lv

    def update_files(self, lines: tuple[str, ...]) -> None:
        self._lines = lines
        self._selected_index = 0
        lv = self.query_one(ListView)
        lv.clear()
        for line in lines[:20]:
            if len(line) < 3:
                continue
            xy = line[:2]
            path_str = line[3:].strip()
            if " -> " in path_str:
                path_str = path_str.rsplit(" -> ", 1)[1]
            filename = Path(path_str.strip('"')).name
            lv.append(ListItem(Label(f"{_status_markup(xy)}  {filename}"), name=line))
        # lv.append schedules async mount; sync index after items are mounted
        if lines:
            self.call_later(self._sync_lv_index)

    def _sync_lv_index(self) -> None:
        if self._lines:
            self.query_one(ListView).index = self._selected_index

    def on_key(self, event: events.Key) -> None:
        if not self._lines:
            return
        if event.key in {"down", "j"}:
            self._selected_index = min(self._selected_index + 1, len(self._lines) - 1)
            self.query_one(ListView).index = self._selected_index
            event.stop()
        elif event.key in {"up", "k"}:
            self._selected_index = max(self._selected_index - 1, 0)
            self.query_one(ListView).index = self._selected_index
            event.stop()
        elif event.key == "enter":
            self.post_message(self.Selected(self._lines[self._selected_index]))
            event.stop()
        elif event.key == "s":
            self.post_message(self.StageRequested(self._lines[self._selected_index], "stage"))
            event.stop()
        elif event.key == "u":
            self.post_message(self.StageRequested(self._lines[self._selected_index], "unstage"))
            event.stop()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        event.stop()
        name = event.item.name
        if name:
            self.post_message(self.Selected(name))


class CommitBar(Widget):
    """Commit message input + inline status feedback."""

    DEFAULT_CSS = """
    CommitBar {
        height: auto;
        padding: 0 1;
        background: $panel;
    }
    CommitBar Input {
        height: 1;
        border: none;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    CommitBar Input:focus {
        border: none;
        background: $panel-lighten-1;
    }
    CommitBar #commit-status {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    CommitBar #commit-status.error {
        color: $error;
    }
    CommitBar #commit-status.success {
        color: $success;
    }
    """

    def compose(self) -> ComposeResult:
        yield Input(placeholder="commit message… (Enter)", id="commit-input")
        yield Static("", id="commit-status")

    def set_status(self, msg: str, style: str = "") -> None:
        label = self.query_one("#commit-status", Static)
        label.update(msg)
        label.remove_class("error", "success")
        if style:
            label.add_class(style)

    def clear_input(self) -> None:
        self.query_one("#commit-input", Input).value = ""


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
        color: $accent;
        text-style: bold;
    }
    RightPanel #files-view {
        height: 1fr;
        layout: vertical;
    }
    RightPanel #git-view {
        height: 1fr;
        layout: vertical;
    }
    RightPanel DirectoryTree {
        height: 1fr;
        background: $surface;
    }
    RightPanel #git-status {
        height: 1;
        padding: 0 1;
        color: $text-muted;
        background: $panel;
    }
    """

    def __init__(self, root: Path | str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._root = Path(root) if root else Path.cwd()
        self._git_ops = GitOps(self._root)
        self._unsubscribe_file_modified = None
        self._unsubscribe_git_status = None

    def compose(self) -> ComposeResult:
        yield MascotPanel(id="rp-mascot")
        with Widget(id="rp-tabs"):
            yield Static(t("panel.tab_files"), id="tab-files", classes="rp-tab rp-tab-active")
            yield Static(t("panel.tab_git"), id="tab-git", classes="rp-tab")
        with Widget(id="files-view"):
            yield FileTree(self._root, id="file-tree")
        with Widget(id="git-view"):
            yield Static("git: checking...", id="git-status")
            yield GitFileList(id="git-files")
            yield CommitBar(id="commit-bar")

    def on_mount(self) -> None:
        # 默认显示文件树，Git 视图隐藏（feat-020：Tab 真切换）
        self.query_one("#git-view").display = False
        self._unsubscribe_file_modified = default_bus.subscribe(
            FileModified, self._on_file_modified
        )
        self._unsubscribe_git_status = default_bus.subscribe(
            GitStatusChanged, self._on_git_status_changed
        )

    def on_click(self, event: events.Click) -> None:
        # Tab 标签点击切换；其他子组件的点击有各自的 on_click 已 stop，不会误触
        target_id = getattr(event.widget, "id", None)
        if target_id == "tab-files":
            self._show_tab("files")
            event.stop()
        elif target_id == "tab-git":
            self._show_tab("git")
            event.stop()

    def _show_tab(self, which: str) -> None:
        is_files = which == "files"
        self.query_one("#files-view").display = is_files
        self.query_one("#git-view").display = not is_files
        files_tab = self.query_one("#tab-files", Static)
        git_tab = self.query_one("#tab-git", Static)
        files_tab.set_class(is_files, "rp-tab-active")
        git_tab.set_class(not is_files, "rp-tab-active")

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

    def on_git_file_list_stage_requested(self, event: GitFileList.StageRequested) -> None:
        event.stop()
        rel_path = self._path_from_status_line(event.status_line)
        if rel_path is None:
            return
        commit_bar = self.query_one(CommitBar)
        try:
            if event.action == "stage":
                self._git_ops.stage(str(rel_path))
                commit_bar.set_status(f"staged {rel_path.name}", "success")
            else:
                self._git_ops.unstage(str(rel_path))
                commit_bar.set_status(f"unstaged {rel_path.name}", "success")
        except GitError as exc:
            commit_bar.set_status(str(exc), "error")
            return
        self.set_timer(2.0, lambda: commit_bar.set_status(""))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        message = event.value.strip()
        commit_bar = self.query_one(CommitBar)
        try:
            self._git_ops.commit(message)
        except GitError as exc:
            commit_bar.set_status(str(exc), "error")
            return
        commit_bar.clear_input()
        commit_bar.set_status("committed", "success")
        self.set_timer(3.0, lambda: commit_bar.set_status(""))

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
