from textual.app import App, ComposeResult
from textual.theme import Theme
from textual.widget import Widget

from tuicode import __version__
from tuicode.bus import default_bus
from tuicode.events import FileModified
from tuicode.git_diff import GitDiffService
from tuicode.git_status import GitStatusPoller
from tuicode.ui.agent_terminal_window import AgentTerminalWindow
from tuicode.ui.command_palette_modal import CommandPaletteModal, PaletteCommand
from tuicode.ui.new_agent_modal import AgentConfig, NewAgentModal
from tuicode.ui.diff_preview_window import DiffPreviewWindow
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
        ("ctrl+1", "layout_preset(1)", "编辑布局"),
        ("ctrl+2", "layout_preset(2)", "双 Agent 布局"),
        ("ctrl+3", "layout_preset(3)", "调试布局"),
        ("ctrl+shift+p", "command_palette", "命令面板"),
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
        self._git_status_poller = GitStatusPoller(".")
        self._git_diff_service = GitDiffService(".")
        self._unsubscribe_file_modified = None
        self.set_interval(1.0, self._workspace_watcher.poll)
        self.set_interval(1.0, self._git_status_poller.poll)
        self._unsubscribe_file_modified = default_bus.subscribe(
            FileModified,
            lambda _: self._git_status_poller.poll(),
        )

    def on_unmount(self) -> None:
        if self._unsubscribe_file_modified is not None:
            self._unsubscribe_file_modified()
            self._unsubscribe_file_modified = None
        self._workspace_state.close()

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

    async def on_right_panel_diff_requested(
        self, msg: RightPanel.DiffRequested
    ) -> None:
        diff = self._git_diff_service.file_diff(msg.path)
        ws = self.query_one(FloatWorkspace)
        await ws.open_window(DiffPreviewWindow(msg.path, diff))

    # ── 终端聚焦 ──────────────────────────────────────────────────────────────

    def action_focus_terminal(self) -> None:
        terminal = self.query_one(PtyTerminal)
        terminal.focus()

    # ── 智能体终端 ────────────────────────────────────────────────────────────

    async def action_new_agent_terminal(self) -> None:
        def _on_config(config: AgentConfig | None) -> None:
            if config is None:
                return
            self.call_after_refresh(self._open_agent_window, config)

        await self.push_screen(NewAgentModal(), _on_config)

    async def _open_agent_window(self, config: AgentConfig) -> None:
        ws = self.query_one(FloatWorkspace)
        await ws.open_window(
            AgentTerminalWindow(
                command=config.command,
                title=config.title,
                agent_type=config.agent_type,
            )
        )

    # ── 布局预设 Ctrl+1/2/3 ───────────────────────────────────────────────────

    def action_layout_preset(self, n: int) -> None:
        self.query_one(FloatWorkspace).apply_preset(n)

    # ── 命令面板 Ctrl+Shift+P ─────────────────────────────────────────────────

    def action_command_palette(self) -> None:
        commands = self._build_palette_commands()
        self.push_screen(CommandPaletteModal(commands))

    def _build_palette_commands(self) -> list[PaletteCommand]:
        return [
            PaletteCommand(
                name="新建 Agent 会话",
                description="打开 Agent 启动器（Ctrl+T）",
                callback=lambda: self.call_after_refresh(self.action_new_agent_terminal),
                keywords=["agent", "claude", "terminal", "bash"],
            ),
            PaletteCommand(
                name="布局：编辑模式",
                description="主窗口最大化（Ctrl+1）",
                callback=lambda: self.action_layout_preset(1),
                keywords=["layout", "preset", "edit"],
            ),
            PaletteCommand(
                name="布局：双 Agent 对比",
                description="左右分屏（Ctrl+2）",
                callback=lambda: self.action_layout_preset(2),
                keywords=["layout", "dual", "split", "compare"],
            ),
            PaletteCommand(
                name="布局：调试模式",
                description="上大下小（Ctrl+3）",
                callback=lambda: self.action_layout_preset(3),
                keywords=["layout", "debug"],
            ),
            PaletteCommand(
                name="聚焦底部终端",
                description="切换焦点到 bash 终端（Ctrl+`）",
                callback=self.action_focus_terminal,
                keywords=["terminal", "bash", "focus"],
            ),
            PaletteCommand(
                name="切换窗口 1",
                description="置顶第 1 个浮窗（Alt+1）",
                callback=lambda: self.action_focus_window(1),
                keywords=["window", "focus"],
            ),
            PaletteCommand(
                name="切换窗口 2",
                description="置顶第 2 个浮窗（Alt+2）",
                callback=lambda: self.action_focus_window(2),
                keywords=["window", "focus"],
            ),
            PaletteCommand(
                name="切换窗口 3",
                description="置顶第 3 个浮窗（Alt+3）",
                callback=lambda: self.action_focus_window(3),
                keywords=["window", "focus"],
            ),
            PaletteCommand(
                name="Git commit（聚焦输入框）",
                description="将焦点移到右栏 commit 输入框",
                callback=self._focus_commit_input,
                keywords=["git", "commit", "stage"],
            ),
            PaletteCommand(
                name="退出",
                description="退出 TuiCode（Ctrl+Q）",
                callback=self.action_quit,
                keywords=["quit", "exit"],
            ),
        ]

    def _focus_commit_input(self) -> None:
        try:
            from tuicode.ui.right_panel import CommitBar
            from textual.widgets import Input
            self.query_one(CommitBar).query_one(Input).focus()
        except Exception:
            pass
