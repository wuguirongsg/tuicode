from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from tuicode.i18n import t


class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        layout: horizontal;
        background: $primary;
        padding: 0 1;
    }
    StatusBar #sb-left      { width: 1fr; color: $background 90%; }
    StatusBar #sb-copyright { width: auto; color: $background 60%; }
    StatusBar #sb-sep1,
    StatusBar #sb-sep       { width: 1; color: $background 40%; }
    StatusBar #sb-right     { width: auto; color: $background 70%; }
    """

    agent_count: reactive[int] = reactive(0)

    def __init__(self, version: str) -> None:
        super().__init__()
        self._version = version

    def compose(self) -> ComposeResult:
        yield Static(id="sb-left")
        yield Static("│", id="sb-sep1")
        yield Static(t("status.copyright"), id="sb-copyright")
        yield Static("│", id="sb-sep")
        yield Static(t("status.shortcuts"), id="sb-right")

    def on_mount(self) -> None:
        self._refresh_left()

    def watch_agent_count(self, count: int) -> None:
        self._refresh_left()

    def set_shortcuts(self, text: str | None) -> None:
        """切换右侧快捷键提示；传 None 恢复默认。"""
        self.query_one("#sb-right", Static).update(text or t("status.shortcuts"))

    def _refresh_left(self) -> None:
        n = self.agent_count
        if n == 0:
            agent_str = t("status.no_agents")
        elif n == 1:
            agent_str = t("status.agents", n=n)
        else:
            agent_str = t("status.agents_pl", n=n)
        self.query_one("#sb-left", Static).update(
            f"TuiCode v{self._version}  {agent_str}"
        )
