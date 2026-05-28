from textual.app import App, ComposeResult
from textual.theme import Theme
from textual.widget import Widget

from tuicode import __version__
from tuicode.ui.agent_terminal_window import AgentTerminalWindow
from tuicode.ui.editor_window import EditorWindow
from tuicode.ui.float_window import FloatWindow
from tuicode.ui.menu_bar import MenuBar
from tuicode.ui.right_panel import RightPanel
from tuicode.ui.status_bar import StatusBar
from tuicode.ui.taskbar import WindowTaskBar
from tuicode.ui.pty_terminal import PtyTerminal
from tuicode.ui.terminal_strip import TerminalStrip
from tuicode.ui.workspace import FloatWorkspace
from tuicode.workspace_state import WorkspaceStateAggregator
from tuicode.workspace_watcher import WorkspaceWatcher


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


class TuiCodeApp(App):
    TITLE = "TUICODE"
    CTRL_C_EXITS = False           # Ctrl+C 透传给终端，不退出 App；用 Ctrl+Q 退出
    ENABLE_COMMAND_PALETTE = False  # Ctrl+P 透传给 PTY 子进程，不打开命令面板

    BINDINGS = [
        ("ctrl+q", "quit", "退出"),
        ("ctrl+grave_accent", "focus_terminal", "聚焦终端"),
        ("ctrl+t", "new_agent_terminal", "新建智能体终端"),
        ("alt+1", "focus_window(1)", "切换窗口 1"),
        ("alt+2", "focus_window(2)", "切换窗口 2"),
        ("alt+3", "focus_window(3)", "切换窗口 3"),
    ]

    CSS = """
    Screen {
        background: $background;
    }
    """

    def on_mount(self) -> None:
        self.register_theme(Theme(
            name="cyberpunk",
            primary="#00d4ff",
            secondary="#bf00ff",
            accent="#ff00a0",
            success="#00ff41",
            warning="#ffb800",
            error="#ff003c",
            foreground="#c8f4ff",
            background="#000510",
            surface="#060d1f",
            panel="#0a1428",
            dark=True,
        ))
        self.theme = "cyberpunk"
        self._workspace_state = WorkspaceStateAggregator()
        self._workspace_watcher = WorkspaceWatcher(".")
        self.set_interval(1.0, self._workspace_watcher.poll)

    def compose(self) -> ComposeResult:
        yield MenuBar()
        yield StatusBar(__version__)
        yield MainContent()

    # ── 任务栏同步 + 吉祥物状态 ───────────────────────────────────────────────

    async def on_float_workspace_window_opened(
        self, msg: FloatWorkspace.WindowOpened
    ) -> None:
        await self.query_one(WindowTaskBar).add_window(msg.window)
        self.query_one(RightPanel).set_mascot_state("opening", auto_reset=2.0)

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

    # ── 智能体终端 ────────────────────────────────────────────────────────────

    async def action_new_agent_terminal(self) -> None:
        ws = self.query_one(FloatWorkspace)
        await ws.open_window(AgentTerminalWindow())
