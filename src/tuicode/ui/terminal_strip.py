from __future__ import annotations

from dataclasses import dataclass

from textual import events
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from tuicode.i18n import t
from tuicode.ui.pty_terminal import PtyTerminal

_MIN_HEIGHT = 5
_MAX_HEIGHT = 40


@dataclass
class _TerminalTab:
    tab_id: int
    label: str


class _ResizeHandle(Widget):
    """顶部拖动把手 — 上下拖动改变 TerminalStrip 高度。"""

    DEFAULT_CSS = """
    _ResizeHandle {
        height: 1;
        background: $panel-darken-2;
        color: $text-disabled;
        content-align: center middle;
    }
    _ResizeHandle:hover { color: $accent; }
    """

    def __init__(self) -> None:
        super().__init__()
        self._dragging = False
        self._drag_start_y = 0
        self._drag_start_h = 0

    def render(self):
        from rich.text import Text
        return Text(t("terminal.drag_hint"), style="dim", justify="center")

    def on_mouse_down(self, event: events.MouseDown) -> None:
        strip = self.parent
        if not isinstance(strip, TerminalStrip):
            return
        self._dragging = True
        self._drag_start_y = event.screen_y
        h = strip.styles.height
        self._drag_start_h = int(h.value) if h and h.value else 12
        self.capture_mouse()
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._dragging:
            return
        strip = self.parent
        if not isinstance(strip, TerminalStrip):
            return
        delta = self._drag_start_y - event.screen_y   # 向上拖 = 增大
        new_h = max(_MIN_HEIGHT, min(_MAX_HEIGHT, self._drag_start_h + delta))
        strip.styles.height = new_h
        event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self._dragging = False
        self.release_mouse()


class TerminalStrip(Widget):
    """底部运行终端区 — 多标签 bash 会话，Tab 切换 + 新建。"""

    DEFAULT_CSS = """
    TerminalStrip {
        height: 14;
        background: $background;
    }
    TerminalStrip #ts-tabs {
        height: 1;
        background: $surface;
        layout: horizontal;
        padding: 0 1;
    }
    TerminalStrip .ts-tab {
        width: auto;
        padding: 0 2;
        color: $text-muted;
    }
    TerminalStrip .ts-tab:hover {
        color: $text;
    }
    TerminalStrip .ts-tab-active {
        color: $accent;
        text-style: bold;
    }
    TerminalStrip .ts-add {
        color: $text-muted;
        padding: 0 2;
    }
    TerminalStrip .ts-add:hover {
        color: $accent;
        text-style: bold;
    }
    TerminalStrip .ts-close {
        color: $text-disabled;
        padding: 0 1;
    }
    TerminalStrip .ts-close:hover {
        color: $error;
    }
    TerminalStrip #ts-content {
        height: 1fr;
    }
    TerminalStrip PtyTerminal {
        height: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._tabs: list[_TerminalTab] = []
        self._active_tab_id: int | None = None
        self._next_tab_id = 0
        self._add_btn_mounted = False

    def compose(self) -> ComposeResult:
        yield _ResizeHandle()
        yield Widget(id="ts-tabs")
        yield Widget(id="ts-content")

    def on_mount(self) -> None:
        self._ensure_add_button()
        self._add_terminal()

    def _ensure_add_button(self) -> None:
        if self._add_btn_mounted:
            return
        tab_bar = self.query_one("#ts-tabs", Widget)
        tab_bar.mount(Static(t("terminal.tab_add"), id="ts-add", classes="ts-tab ts-add"))
        self._add_btn_mounted = True

    def on_click(self, event: events.Click) -> None:
        widget_id = getattr(event.widget, "id", None)
        if not widget_id:
            return
        if widget_id == "ts-add":
            self._add_terminal()
            event.stop()
            return
        if widget_id.startswith("ts-tab-"):
            tab_id = int(widget_id.removeprefix("ts-tab-"))
            self._switch_tab(tab_id)
            event.stop()
            return
        if widget_id.startswith("ts-close-"):
            tab_id = int(widget_id.removeprefix("ts-close-"))
            self._close_terminal(tab_id)
            event.stop()

    def focus_active_terminal(self) -> None:
        """聚焦当前激活的 PTY 终端。"""
        term = self.active_terminal
        if term is not None:
            term.focus()

    @property
    def active_terminal(self) -> PtyTerminal | None:
        if self._active_tab_id is None:
            return None
        try:
            return self.query_one(f"#ts-term-{self._active_tab_id}", PtyTerminal)
        except Exception:
            return None

    def _add_terminal(self) -> None:
        self._next_tab_id += 1
        tab_id = self._next_tab_id
        index = len(self._tabs) + 1
        label = t("terminal.tab_label") if index == 1 else t("terminal.tab_label_n", n=index)
        self._tabs.append(_TerminalTab(tab_id=tab_id, label=label))

        tab_bar = self.query_one("#ts-tabs", Widget)
        tab_bar.mount(
            Static(label, id=f"ts-tab-{tab_id}", classes="ts-tab"),
            before="#ts-add",
        )

        content = self.query_one("#ts-content", Widget)
        term = PtyTerminal(id=f"ts-term-{tab_id}")
        content.mount(term)
        self._refresh_close_buttons()
        self._switch_tab(tab_id)

    def _refresh_close_buttons(self) -> None:
        tab_bar = self.query_one("#ts-tabs", Widget)
        show_close = len(self._tabs) > 1
        for tab in self._tabs:
            close_id = f"ts-close-{tab.tab_id}"
            try:
                tab_bar.query_one(f"#{close_id}", Static)
                has_close = True
            except Exception:
                has_close = False
            if show_close and not has_close:
                tab_bar.mount(
                    Static("×", id=close_id, classes="ts-tab ts-close"),
                    after=f"#ts-tab-{tab.tab_id}",
                )
            elif not show_close and has_close:
                tab_bar.query_one(f"#{close_id}", Static).remove()

    def _switch_tab(self, tab_id: int) -> None:
        if tab_id not in {t.tab_id for t in self._tabs}:
            return
        self._active_tab_id = tab_id
        for tab in self._tabs:
            is_active = tab.tab_id == tab_id
            self.query_one(f"#ts-tab-{tab.tab_id}", Static).set_class(
                is_active, "ts-tab-active"
            )
            self.query_one(f"#ts-term-{tab.tab_id}", PtyTerminal).display = is_active
        self.focus_active_terminal()

    def _close_terminal(self, tab_id: int) -> None:
        if len(self._tabs) <= 1:
            return
        idx = next((i for i, tab in enumerate(self._tabs) if tab.tab_id == tab_id), -1)
        if idx < 0:
            return

        self.query_one(f"#ts-tab-{tab_id}", Static).remove()
        try:
            self.query_one(f"#ts-close-{tab_id}", Static).remove()
        except Exception:
            pass
        self.query_one(f"#ts-term-{tab_id}", PtyTerminal).remove()
        self._tabs.pop(idx)

        if self._active_tab_id == tab_id:
            new_idx = min(idx, len(self._tabs) - 1)
            self._switch_tab(self._tabs[new_idx].tab_id)
        self._refresh_close_buttons()
