from textual.app import App, ComposeResult
from textual.widget import Widget

from agentdeck import __version__
from agentdeck.ui.editor_window import EditorWindow
from agentdeck.ui.float_window import FloatWindow
from agentdeck.ui.menu_bar import MenuBar
from agentdeck.ui.right_panel import RightPanel
from agentdeck.ui.status_bar import StatusBar
from agentdeck.ui.taskbar import WindowTaskBar
from agentdeck.ui.pty_terminal import PtyTerminal
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
        ("ctrl+grave_accent", "focus_terminal", "聚焦终端"),
        ("ctrl+t", "test_windows", "[临时] 打开测试浮窗"),
        ("alt+1", "focus_window(1)", "切换窗口 1"),
        ("alt+2", "focus_window(2)", "切换窗口 2"),
        ("alt+3", "focus_window(3)", "切换窗口 3"),
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

    # ── 任务栏同步 ────────────────────────────────────────────────────────────

    async def on_float_workspace_window_opened(
        self, msg: FloatWorkspace.WindowOpened
    ) -> None:
        await self.query_one(WindowTaskBar).add_window(msg.window)

    async def on_float_window_closed(self, msg: FloatWindow.Closed) -> None:
        await self.query_one(WindowTaskBar).remove_window(msg.window)

    def on_float_window_minimize_toggled(
        self, msg: FloatWindow.MinimizeToggled
    ) -> None:
        self.query_one(WindowTaskBar).update_window(msg.window)

    # ── Alt+N 快切 ────────────────────────────────────────────────────────────

    def action_focus_window(self, n: int) -> None:
        win = self.query_one(WindowTaskBar).get_window_at(n)
        if win is not None:
            win._bring_to_top()
            win.restore()
            win.focus()

    # ── 文件树 → 编辑器 ───────────────────────────────────────────────────────

    async def on_right_panel_file_requested(
        self, msg: RightPanel.FileRequested
    ) -> None:
        # 同一文件已打开则置顶，不重复开窗
        for win in self.query(EditorWindow):
            if win._path == msg.path:
                win._bring_to_top()
                win.restore()
                win.focus()
                return
        ws = self.query_one(FloatWorkspace)
        await ws.open_window(EditorWindow(msg.path))

    # ── 终端聚焦 ──────────────────────────────────────────────────────────────

    def action_focus_terminal(self) -> None:
        terminal = self.query_one(PtyTerminal)
        terminal.focus()

    # ── 临时测试 ──────────────────────────────────────────────────────────────

    async def action_test_windows(self) -> None:
        ws = self.query_one(FloatWorkspace)
        await ws.open_window(FloatWindow("编辑器 — main.py"))
        await ws.open_window(FloatWindow("Claude Code"))
        await ws.open_window(FloatWindow("终端输出"))
