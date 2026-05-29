"""feat-021 文件操作模态 — 文本输入（新建/重命名）+ 删除确认。"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from tuicode.i18n import t


class TextPromptModal(ModalScreen[str | None]):
    """通用单行输入对话框。返回输入字符串；取消或空输入返回 None。"""

    DEFAULT_CSS = """
    TextPromptModal {
        align: center middle;
    }
    TextPromptModal #modal-box {
        width: 52;
        height: auto;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }
    TextPromptModal #modal-title {
        width: 1fr;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    TextPromptModal #prompt-input {
        width: 1fr;
        margin-bottom: 1;
    }
    TextPromptModal #btn-row {
        align: center middle;
        height: 3;
    }
    TextPromptModal Button {
        margin: 0 1;
    }
    """

    def __init__(self, title: str, initial: str = "", placeholder: str = "") -> None:
        super().__init__()
        self._title = title
        self._initial = initial
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Label(self._title, id="modal-title")
            yield Input(
                value=self._initial,
                placeholder=self._placeholder,
                id="prompt-input",
            )
            with Horizontal(id="btn-row"):
                yield Button(t("fileop.btn_ok"), id="btn-ok", variant="success")
                yield Button(t("fileop.btn_cancel"), id="btn-cancel", variant="default")

    def on_mount(self) -> None:
        self.query_one("#prompt-input", Input).focus()

    def _submit(self) -> None:
        value = self.query_one("#prompt-input", Input).value.strip()
        self.dismiss(value or None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "btn-ok":
            self._submit()
        else:
            self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            event.stop()


class ConfirmDeleteModal(ModalScreen[bool]):
    """删除确认对话框。返回 True 表示确认删除。"""

    DEFAULT_CSS = """
    ConfirmDeleteModal {
        align: center middle;
    }
    ConfirmDeleteModal #modal-box {
        width: 52;
        height: auto;
        border: round $error;
        background: $surface;
        padding: 1 2;
    }
    ConfirmDeleteModal #modal-msg {
        width: 1fr;
        text-align: center;
        color: $text;
        margin-bottom: 1;
    }
    ConfirmDeleteModal #btn-row {
        align: center middle;
        height: 3;
    }
    ConfirmDeleteModal Button {
        margin: 0 1;
    }
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Static(t("fileop.confirm_delete", name=self._name), id="modal-msg")
            with Horizontal(id="btn-row"):
                yield Button(t("fileop.btn_delete"), id="btn-delete", variant="error")
                yield Button(t("fileop.btn_cancel"), id="btn-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(event.button.id == "btn-delete")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(False)
            event.stop()
