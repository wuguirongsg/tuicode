from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from tuicode.i18n import t


class TaskButton(Widget):
    """任务栏单个窗口按钮。"""

    can_focus = False

    class Activated(Message):
        def __init__(self, window: object) -> None:
            super().__init__()
            self.window = window

    DEFAULT_CSS = """
    TaskButton {
        width: auto;
        height: 1;
        padding: 0 2;
        color: $text-muted;
    }
    TaskButton:hover { background: $surface; color: $text; }
    TaskButton.minimized { color: $text-disabled; text-style: italic; }
    """

    def __init__(self, window: object, **kwargs) -> None:
        super().__init__(**kwargs)
        self._window = window

    def render(self) -> str:
        win = self._window
        icon = "▾" if win._is_minimized else "▪"
        title = win._title
        if len(title) > 18:
            title = title[:17] + "…"
        return f"{icon} {title}"

    def refresh_state(self) -> None:
        if self._window._is_minimized:
            self.add_class("minimized")
        else:
            self.remove_class("minimized")
        self.refresh()

    def on_click(self) -> None:
        self.post_message(self.Activated(self._window))


class WindowTaskBar(Widget):
    """浮窗任务栏 — 列出所有打开的工作窗口，点击置顶/还原，Alt+1/2/3 快切。"""

    DEFAULT_CSS = """
    WindowTaskBar {
        height: 1;
        layout: horizontal;
        background: $panel;
        padding: 0 1;
        border-bottom: solid $panel-lighten-1;
    }
    WindowTaskBar #tb-hint {
        color: $text-disabled;
        width: auto;
        text-style: italic;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._buttons: dict[int, TaskButton] = {}  # id(window) -> TaskButton

    def compose(self) -> ComposeResult:
        yield Static(t("taskbar.no_windows"), id="tb-hint")

    async def add_window(self, window: object) -> None:
        btn = TaskButton(window, id=f"tb-{id(window)}")
        self._buttons[id(window)] = btn
        await self.mount(btn)
        self.query_one("#tb-hint", Static).display = False

    async def remove_window(self, window: object) -> None:
        key = id(window)
        if key in self._buttons:
            self._buttons.pop(key).remove()
        if not self._buttons:
            self.query_one("#tb-hint", Static).display = True

    def update_window(self, window: object) -> None:
        btn = self._buttons.get(id(window))
        if btn:
            btn.refresh_state()

    def on_task_button_activated(self, msg: TaskButton.Activated) -> None:
        msg.stop()
        win = msg.window
        win._bring_to_top()
        win.restore()
        win.focus()

    def get_window_at(self, n: int) -> object | None:
        """返回第 n 个按钮对应的窗口（1-indexed），不存在时返回 None。"""
        buttons = list(self._buttons.values())
        if 1 <= n <= len(buttons):
            return buttons[n - 1]._window
        return None
