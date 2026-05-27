"""feat-005 文件树 — 右栏 files Tab，DirectoryTree + FileRequested 消息。"""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DirectoryTree, Static


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
        border-left: solid $panel-darken-2;
        layout: vertical;
        background: $panel-darken-1;
    }
    RightPanel #rp-tabs {
        height: 1;
        background: $panel-darken-2;
        layout: horizontal;
        padding: 0 1;
    }
    RightPanel .rp-tab {
        width: auto;
        padding: 0 1;
        color: $text-muted;
    }
    RightPanel .rp-tab-active {
        width: auto;
        padding: 0 1;
        color: $accent;
        text-style: bold;
    }
    RightPanel DirectoryTree {
        height: 1fr;
        background: $panel-darken-1;
    }
    """

    def __init__(self, root: Path | str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._root = Path(root) if root else Path.cwd()

    def compose(self) -> ComposeResult:
        with Widget(id="rp-tabs"):
            yield Static("files", classes="rp-tab-active")
            yield Static("git", classes="rp-tab")
        yield DirectoryTree(self._root, id="file-tree")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        event.stop()
        self.post_message(self.FileRequested(event.path))
