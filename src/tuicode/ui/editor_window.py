"""feat-006 编辑器浮窗 — TextArea + 文件读写 + Ctrl+S 保存 + 未保存确认。"""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static, TextArea

from tuicode.bus import default_bus
from tuicode.events import FileModified
from tuicode.ui.float_window import FloatWindow, TitleBar

_LANG_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".json": "json",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".html": "html",
    ".css": "css",
    ".sh": "bash",
    ".toml": "toml",
}


class ConfirmCloseModal(ModalScreen[bool]):
    """未保存内容确认关闭对话框。返回 True 表示确认关闭（丢弃修改）。"""

    DEFAULT_CSS = """
    ConfirmCloseModal {
        align: center middle;
    }
    ConfirmCloseModal #modal-box {
        width: 50;
        height: 8;
        border: solid $warning;
        background: $surface;
        padding: 1 2;
    }
    ConfirmCloseModal #modal-msg {
        width: 1fr;
        text-align: center;
        color: $text;
        margin-bottom: 1;
    }
    ConfirmCloseModal #modal-buttons {
        align: center middle;
        height: 3;
    }
    ConfirmCloseModal Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Static("文件未保存，确认关闭？", id="modal-msg")
            with Horizontal(id="modal-buttons"):
                yield Button("关闭不保存", id="btn-discard", variant="error")
                yield Button("取消", id="btn-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-discard")


class EditorWindow(FloatWindow):
    """编辑器浮窗 — 基于 TextArea 的单文件编辑器。"""

    DEFAULT_WIDTH = 80
    DEFAULT_HEIGHT = 24

    BINDINGS = [("ctrl+s", "save", "保存")]

    def __init__(self, path: Path, **kwargs) -> None:
        self._path = path
        self._dirty = False
        super().__init__(title=path.name, **kwargs)

    def compose_body(self) -> ComposeResult:
        try:
            content = self._path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            content = ""
        lang = _LANG_MAP.get(self._path.suffix)
        yield TextArea(content, language=lang, id="editor-textarea", show_line_numbers=True)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if not self._dirty:
            self._dirty = True
            self._refresh_title()

    def _refresh_title(self) -> None:
        prefix = "*" if self._dirty else ""
        new_title = f"{prefix}{self._path.name}"
        try:
            self.query_one("#win-title", Static).update(new_title)
        except Exception:
            pass

    def action_save(self) -> None:
        content = self.query_one("#editor-textarea", TextArea).text
        try:
            self._path.write_text(content, encoding="utf-8")
        except OSError:
            return
        self._dirty = False
        self._refresh_title()
        default_bus.publish(FileModified(self._path))

    def on_title_bar_close_clicked(self, message: TitleBar.CloseClicked) -> None:
        if self._dirty:
            self.app.push_screen(ConfirmCloseModal(), self._handle_close_confirm)
        else:
            self.post_message(self.Closed(self))
            self.remove()

    def _handle_close_confirm(self, confirmed: bool) -> None:
        if confirmed:
            self.post_message(self.Closed(self))
            self.remove()
