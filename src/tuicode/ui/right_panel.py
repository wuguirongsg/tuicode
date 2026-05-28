"""feat-005 文件树 — 右栏 files Tab，DirectoryTree + FileRequested 消息。"""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DirectoryTree, Static

from tuicode.bus import default_bus
from tuicode.events import FileModified
from tuicode.i18n import t
from tuicode.ui.mascot import MascotPanel


class RightPanel(Widget):
    """右侧固定工具栏 — files Tab 显示项目文件树。"""

    class FileRequested(Message):
        """用户在文件树中选中文件，通知 App 打开编辑器浮窗。"""
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
    """

    def __init__(self, root: Path | str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._root = Path(root) if root else Path.cwd()
        self._unsubscribe_file_modified = None

    def compose(self) -> ComposeResult:
        yield MascotPanel(id="rp-mascot")
        with Widget(id="rp-tabs"):
            yield Static(t("panel.tab_files"), classes="rp-tab-active")
            yield Static(t("panel.tab_git"), classes="rp-tab")
        yield DirectoryTree(self._root, id="file-tree")

    def on_mount(self) -> None:
        self._unsubscribe_file_modified = default_bus.subscribe(
            FileModified, self._on_file_modified
        )

    def on_unmount(self) -> None:
        if self._unsubscribe_file_modified is not None:
            self._unsubscribe_file_modified()
            self._unsubscribe_file_modified = None

    def set_mascot_state(self, state: str, auto_reset: float = 0.0) -> None:
        self.query_one(MascotPanel).set_state(state, auto_reset)

    def refresh_file_tree(self) -> None:
        self.query_one("#file-tree", DirectoryTree).reload()

    def _on_file_modified(self, event: FileModified) -> None:
        self.call_later(self.refresh_file_tree)

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        event.stop()
        self.post_message(self.FileRequested(event.path))
