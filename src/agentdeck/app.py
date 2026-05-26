from textual.app import App, ComposeResult
from textual.widget import Widget

from agentdeck import __version__
from agentdeck.ui.float_window import FloatWindow
from agentdeck.ui.menu_bar import MenuBar
from agentdeck.ui.right_panel import RightPanel
from agentdeck.ui.status_bar import StatusBar
from agentdeck.ui.taskbar import WindowTaskBar
from agentdeck.ui.terminal_strip import TerminalStrip
from agentdeck.ui.workspace import FloatWorkspace


class LeftColumn(Widget):
    DEFAULT_CSS = """
    LeftColumn {
        layout: vertical;
        width: 1fr;
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield WindowTaskBar()
        yield FloatWorkspace()
        yield TerminalStrip()


class MainContent(Widget):
    DEFAULT_CSS = """
    MainContent {
        layout: horizontal;
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield LeftColumn()
        yield RightPanel()


class AgentDeckApp(App):
    TITLE = "AgentDeck"

    BINDINGS = [
        ("ctrl+q", "quit", "退出"),
        ("ctrl+t", "test_windows", "[临时] 打开测试浮窗"),
    ]

    CSS = """
    Screen {
        background: #0d1117;
    }
    """

    def compose(self) -> ComposeResult:
        yield MenuBar()
        yield StatusBar(__version__)
        yield MainContent()

    async def action_test_windows(self) -> None:
        ws = self.query_one(FloatWorkspace)
        await ws.open_window(FloatWindow("编辑器 — main.py"))
        await ws.open_window(FloatWindow("Claude Code"))
        await ws.open_window(FloatWindow("终端输出"))
