from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        layout: horizontal;
        background: $accent-darken-3;
        padding: 0 1;
    }
    StatusBar #sb-left  { width: 1fr; color: $text-muted; }
    StatusBar #sb-right { width: auto; color: $text-muted; }
    """

    agent_count: reactive[int] = reactive(0)

    def __init__(self, version: str) -> None:
        super().__init__()
        self._version = version

    def compose(self) -> ComposeResult:
        yield Static(id="sb-left")
        yield Static("Ctrl+Q 退出  Ctrl+? 帮助", id="sb-right")

    def on_mount(self) -> None:
        self._refresh_left()

    def watch_agent_count(self, count: int) -> None:
        self._refresh_left()

    def _refresh_left(self) -> None:
        agents = self.agent_count
        agent_str = f"● {agents} agent{'s' if agents != 1 else ''}" if agents else "○ 无 agent"
        self.query_one("#sb-left", Static).update(
            f"AgentDeck v{self._version}  {agent_str}"
        )
