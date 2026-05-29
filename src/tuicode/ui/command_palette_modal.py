"""feat-018 命令面板 Ctrl+Shift+P — 全屏 Modal，搜索并执行命令。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from textual.app import ComposeResult
from textual import events
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Input, Label, Static


@dataclass
class PaletteCommand:
    """一条可执行的命令。"""
    name: str
    description: str
    callback: Callable[[], None]
    keywords: list[str] = field(default_factory=list)

    def matches(self, query: str) -> bool:
        q = query.lower()
        if not q:
            return True
        text = f"{self.name} {self.description} {' '.join(self.keywords)}".lower()
        return q in text


class _CommandList(Widget):
    """搜索结果列表 — 用 render() 整体渲染，避免动态挂载竞态问题。"""

    can_focus = False

    DEFAULT_CSS = """
    _CommandList {
        height: auto;
        max-height: 16;
        background: $surface;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._filtered: list[PaletteCommand] = []
        self._selected_index = 0

    def update(self, filtered: list[PaletteCommand], selected: int) -> None:
        self._filtered = filtered
        self._selected_index = selected
        self.refresh()

    def render(self) -> str:
        if not self._filtered:
            return "  [dim](无匹配命令)[/]"
        lines: list[str] = []
        for i, cmd in enumerate(self._filtered[:16]):
            if i == self._selected_index:
                lines.append(
                    f"[bold $accent]> {cmd.name}[/]  [dim]{cmd.description}[/]"
                )
            else:
                lines.append(f"  [dim]{cmd.name}[/]  [dim]{cmd.description}[/]")
        return "\n".join(lines)


class CommandPaletteModal(ModalScreen[None]):
    """全屏命令面板 — 搜索过滤 + 键盘选中执行，Escape 或执行后关闭。"""

    # Screen-level BINDINGS 优先于 Input widget 的内建键处理
    # 注意：enter 不在此处，因为 Input 会消费它并触发 Input.Submitted
    BINDINGS = [
        ("escape", "close_palette", "关闭"),
        ("down", "select_down", "下移"),
        ("up", "select_up", "上移"),
    ]

    DEFAULT_CSS = """
    CommandPaletteModal {
        align: center top;
    }
    CommandPaletteModal #palette-box {
        width: 72;
        height: auto;
        max-height: 24;
        margin-top: 3;
        border: round $accent;
        background: $surface;
        padding: 0 1;
    }
    CommandPaletteModal #palette-title {
        width: 1fr;
        text-align: center;
        color: $accent;
        text-style: bold;
    }
    CommandPaletteModal #palette-input {
        width: 1fr;
        height: 1;
        border: none;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    CommandPaletteModal #palette-input:focus {
        border: none;
        background: $panel-lighten-1;
    }
    """

    def __init__(self, commands: list[PaletteCommand], **kwargs) -> None:
        super().__init__(**kwargs)
        self._all_commands = commands
        self._filtered: list[PaletteCommand] = list(commands)
        self._selected_index = 0

    def compose(self) -> ComposeResult:
        with Widget(id="palette-box"):
            yield Label("> 命令面板", id="palette-title")
            yield Input(placeholder="搜索命令…", id="palette-input")
            yield _CommandList(id="palette-list")

    def on_mount(self) -> None:
        self.query_one("#palette-input", Input).focus()
        self._refresh_list()

    def on_input_changed(self, event: Input.Changed) -> None:
        self._filtered = [c for c in self._all_commands if c.matches(event.value)]
        self._selected_index = 0
        self._refresh_list()

    def action_close_palette(self) -> None:
        self.dismiss(None)

    def action_select_down(self) -> None:
        if self._filtered:
            self._selected_index = min(self._selected_index + 1, len(self._filtered) - 1)
            self._refresh_list()

    def action_select_up(self) -> None:
        if self._filtered:
            self._selected_index = max(self._selected_index - 1, 0)
            self._refresh_list()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._execute_selected()

    def on_click(self, event: events.Click) -> None:
        widget = event.widget
        if isinstance(widget, _CommandList):
            clicked_row = event.y
            if 0 <= clicked_row < len(self._filtered):
                self._selected_index = clicked_row
                self._execute_selected()

    def _execute_selected(self) -> None:
        if not self._filtered:
            return
        cmd = self._filtered[self._selected_index]
        self.dismiss(None)
        cmd.callback()

    def _refresh_list(self) -> None:
        self.query_one(_CommandList).update(self._filtered, self._selected_index)
