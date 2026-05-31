import time

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.theme import Theme
from textual.timer import Timer
from textual.widget import Widget

from tuicode import __version__
from tuicode.agent_memory import AgentSessionStore
from tuicode.bus import default_bus
from tuicode.events import FileModified, TerminalOutput
from tuicode.git_diff import GitDiffService
from tuicode.git_status import GitStatusPoller
from tuicode.i18n import get_lang, save_lang, t
from tuicode.ui.agent_terminal_window import AgentTerminalWindow
from tuicode.ui.command_palette_modal import CommandPaletteModal, PaletteCommand
from tuicode.ui.new_agent_modal import AgentConfig, NewAgentModal
from tuicode.ui.agent_session_modal import AgentSessionHistoryModal
from tuicode.ui.diff_preview_window import DiffPreviewWindow
from tuicode.ui.editor_window import EditorWindow
from tuicode.ui.file_tree import FileTree
from tuicode.ui.float_window import FloatWindow
from tuicode.ui.menu_bar import MenuBar
from tuicode.ui.right_panel import RightPanel
from tuicode.ui.status_bar import StatusBar
from tuicode.ui.taskbar import WindowTaskBar
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
        Binding("ctrl+q", "quit", t("bind.quit"), priority=True),
        Binding("ctrl+grave_accent", "focus_terminal", t("bind.focus_terminal"), priority=True),
        Binding("ctrl+t", "new_agent_terminal", t("bind.new_agent"), priority=True),
        Binding("alt+1", "focus_window(1)", t("bind.win1"), priority=True),
        Binding("alt+2", "focus_window(2)", t("bind.win2"), priority=True),
        Binding("alt+3", "focus_window(3)", t("bind.win3"), priority=True),
        Binding("ctrl+1", "layout_preset(1)", t("bind.layout_edit"), priority=True),
        Binding("ctrl+2", "layout_preset(2)", t("bind.layout_dual"), priority=True),
        Binding("ctrl+3", "layout_preset(3)", t("bind.layout_debug"), priority=True),
        Binding("ctrl+underscore", "command_palette", t("bind.command_palette"), priority=True),
        Binding("f1", "command_palette", t("bind.command_palette"), priority=True),
    ]

    CSS = """
    Screen {
        background: $background;
    }
    """

    _THEME_CYCLE = ["cyberpunk", "textual-dark", "nord", "gruvbox", "textual-light"]

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
        self._agent_windows: set[int] = set()  # 打开的 Agent 浮窗 id 集合（驱动底栏计数）
        self._agent_sessions: set[str] = set()
        self._agent_output_active = False
        self._agent_output_idle_timer: Timer | None = None
        self._last_ctrl_c: float = 0.0  # 全局双击 Ctrl+C 退出计时
        self._workspace_state = WorkspaceStateAggregator()
        self._workspace_watcher = WorkspaceWatcher(".")
        self._git_status_poller = GitStatusPoller(".")
        self._git_diff_service = GitDiffService(".")
        self._agent_session_store = AgentSessionStore(".")
        self._unsubscribe_file_modified = None
        self._unsubscribe_terminal_output = None
        self.set_interval(1.0, self._workspace_watcher.poll)
        self.set_interval(1.0, self._git_status_poller.poll)
        self._unsubscribe_file_modified = default_bus.subscribe(
            FileModified,
            lambda _: self._git_status_poller.poll(),
        )
        self._unsubscribe_terminal_output = default_bus.subscribe(
            TerminalOutput,
            self._on_terminal_output,
        )

    def on_unmount(self) -> None:
        if self._unsubscribe_file_modified is not None:
            self._unsubscribe_file_modified()
            self._unsubscribe_file_modified = None
        if self._unsubscribe_terminal_output is not None:
            self._unsubscribe_terminal_output()
            self._unsubscribe_terminal_output = None
        if self._agent_output_idle_timer is not None:
            self._agent_output_idle_timer.stop()
            self._agent_output_idle_timer = None
        for session_id in list(getattr(self, "_agent_sessions", ())):
            self._agent_session_store.finish_session(session_id, status="closed")
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
        if isinstance(msg.window, AgentTerminalWindow):
            self._agent_windows.add(id(msg.window))
            self._agent_sessions.add(msg.window.session_id)
            self._agent_session_store.start_session(
                session_id=msg.window.session_id,
                title=msg.window._raw_title,
                agent_type=msg.window.agent_type,
                command=msg.window._command,
            )
            self._refresh_agent_count()
        self.query_one(RightPanel).set_mascot_state("opening", auto_reset=2.0)

    async def on_float_window_closed(self, msg: FloatWindow.Closed) -> None:
        await self.query_one(WindowTaskBar).remove_window(msg.window)
        if id(msg.window) in self._agent_windows:
            self._agent_windows.discard(id(msg.window))
            if isinstance(msg.window, AgentTerminalWindow):
                self._agent_sessions.discard(msg.window.session_id)
                self._agent_session_store.finish_session(
                    msg.window.session_id,
                    status="closed",
                    scrollback_text=msg.window.get_session_text(),
                )
            self._refresh_agent_count()

    def on_float_window_minimize_toggled(
        self, msg: FloatWindow.MinimizeToggled
    ) -> None:
        self.query_one(WindowTaskBar).update_window(msg.window)

    def on_agent_terminal_window_status_changed(
        self, msg: AgentTerminalWindow.StatusChanged
    ) -> None:
        # 进程运行/结束切换：刷新任务栏按钮标题（▶/■ 标记跟随）
        self.query_one(WindowTaskBar).update_window(msg.window)
        if not msg.is_running:
            self._agent_session_store.finish_session(
                msg.window.session_id,
                status="ended",
                scrollback_text=msg.window.get_session_text(),
            )

    def _refresh_agent_count(self) -> None:
        self.query_one(StatusBar).agent_count = len(self._agent_windows)

    def _on_terminal_output(self, event: TerminalOutput) -> None:
        if event.session_id not in self._agent_sessions or not event.text:
            return
        self._agent_session_store.append_output(event.session_id, event.text)
        if not self._agent_output_active:
            self.query_one(RightPanel).set_mascot_state("agent")
            self._agent_output_active = True
        if self._agent_output_idle_timer is not None:
            self._agent_output_idle_timer.stop()
        self._agent_output_idle_timer = self.set_timer(
            0.9, self._clear_agent_output_active
        )

    def _clear_agent_output_active(self) -> None:
        self._agent_output_active = False
        self._agent_output_idle_timer = None
        self.query_one(RightPanel).set_mascot_state("idle")

    # ── 焦点上下文提示 ────────────────────────────────────────────────────────

    def on_descendant_focus(self, event) -> None:
        # 文件树聚焦时在底栏显示文件操作快捷键，失焦切回默认
        is_filetree = isinstance(event.widget, FileTree)
        hint = t("status.filetree_hint") if is_filetree else None
        self.query_one(StatusBar).set_shortcuts(hint)

    # ── 全局双击 Ctrl+C 退出 ──────────────────────────────────────────────────

    def on_key(self, event) -> None:
        # 焦点不在 PTY（或被消费）时，Ctrl+C 冒泡到这里参与全局双击退出。
        # 焦点在 PTY 时，PtyTerminal 已处理并 event.stop()，直接调用本逻辑、不会重复计数。
        if event.key == "ctrl+c":
            self._ctrl_c_pressed()

    def _ctrl_c_pressed(self) -> None:
        now = time.monotonic()
        if now - self._last_ctrl_c < 1.5:
            self.exit()
            return
        self._last_ctrl_c = now
        self.notify(t("app.ctrl_c_hint"), timeout=1.5, severity="warning")

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
        self.query_one(TerminalStrip).focus_active_terminal()

    # ── 智能体终端 ────────────────────────────────────────────────────────────

    @work
    async def action_new_agent_terminal(self) -> None:
        config: AgentConfig | None = await self.push_screen(
            NewAgentModal(), wait_for_dismiss=True
        )
        if config is not None:
            await self._open_agent_window(config)

    @work
    async def action_continue_agent_session(self) -> None:
        record = await self.push_screen(
            AgentSessionHistoryModal(
                self._agent_session_store.list_sessions(limit=20),
                on_delete=self._agent_session_store.delete_session,
            ),
            wait_for_dismiss=True,
        )
        if record is None:
            return
        config: AgentConfig | None = await self.push_screen(
            NewAgentModal(), wait_for_dismiss=True
        )
        if config is None:
            return
        prompt = self._agent_session_store.build_handoff_notice(record.session_id)
        await self._open_agent_window(config, continuation_prompt=prompt)

    async def _open_agent_window(
        self, config: AgentConfig, continuation_prompt: str = ""
    ) -> None:
        ws = self.query_one(FloatWorkspace)
        await ws.open_window(
            AgentTerminalWindow(
                command=config.command,
                title=config.title,
                agent_type=config.agent_type,
                continuation_prompt=continuation_prompt,
            )
        )

    # ── 布局预设 Ctrl+1/2/3 ───────────────────────────────────────────────────

    def action_layout_preset(self, n: int) -> None:
        self.query_one(FloatWorkspace).apply_preset(n)

    # ── 重置窗口位置 ──────────────────────────────────────────────────────────

    def action_reset_windows(self) -> None:
        self.query_one(FloatWorkspace).reset_positions()

    # ── 主题切换 ──────────────────────────────────────────────────────────────

    def action_toggle_theme(self) -> None:
        try:
            idx = self._THEME_CYCLE.index(self.theme)
        except ValueError:
            idx = -1
        self.theme = self._THEME_CYCLE[(idx + 1) % len(self._THEME_CYCLE)]

    # ── 语言切换 ──────────────────────────────────────────────────────────────

    def action_switch_language(self) -> None:
        current = get_lang()
        new_lang = "en" if current == "zh" else "zh"
        save_lang(new_lang)
        label = "English" if new_lang == "en" else "中文"
        self.notify(
            t("app.lang_switched", label=label),
            title=t("app.lang_title"),
            timeout=5,
        )

    # ── 命令面板 Ctrl+/ / F1 ──────────────────────────────────────────────────

    def action_command_palette(self) -> None:
        commands = self._build_palette_commands()
        self.push_screen(CommandPaletteModal(commands))

    def _build_palette_commands(self) -> list[PaletteCommand]:
        _cur_lang = get_lang()
        _lang_labels = {"zh": "中文", "en": "English"}
        _next_lang = "en" if _cur_lang == "zh" else "zh"
        return [
            PaletteCommand(
                name=t("cmd.theme.name"),
                description=t("cmd.theme.desc", theme=self.theme),
                callback=self.action_toggle_theme,
                keywords=["theme", "color", "主题", "配色", "dark", "light"],
            ),
            PaletteCommand(
                name=t("cmd.lang.name", lang=_lang_labels[_next_lang]),
                description=t("cmd.lang.desc", cur=_lang_labels[_cur_lang]),
                callback=self.action_switch_language,
                keywords=["language", "lang", "语言", "中文", "english", "en", "zh"],
            ),
            PaletteCommand(
                name=t("cmd.new_agent.name"),
                description=t("cmd.new_agent.desc"),
                callback=lambda: self.call_after_refresh(self.action_new_agent_terminal),
                keywords=["agent", "claude", "terminal", "bash"],
            ),
            PaletteCommand(
                name=t("cmd.continue_agent.name"),
                description=t("cmd.continue_agent.desc"),
                callback=lambda: self.call_after_refresh(self.action_continue_agent_session),
                keywords=["agent", "session", "history", "continue", "memory", "会话", "继续", "历史"],
            ),
            PaletteCommand(
                name=t("cmd.layout_edit.name"),
                description=t("cmd.layout_edit.desc"),
                callback=lambda: self.action_layout_preset(1),
                keywords=["layout", "preset", "edit"],
            ),
            PaletteCommand(
                name=t("cmd.layout_dual.name"),
                description=t("cmd.layout_dual.desc"),
                callback=lambda: self.action_layout_preset(2),
                keywords=["layout", "dual", "split", "compare"],
            ),
            PaletteCommand(
                name=t("cmd.layout_debug.name"),
                description=t("cmd.layout_debug.desc"),
                callback=lambda: self.action_layout_preset(3),
                keywords=["layout", "debug"],
            ),
            PaletteCommand(
                name=t("cmd.reset_win.name"),
                description=t("cmd.reset_win.desc"),
                callback=self.action_reset_windows,
                keywords=["reset", "window", "position", "重置", "窗口", "复位"],
            ),
            PaletteCommand(
                name=t("cmd.focus_term.name"),
                description=t("cmd.focus_term.desc"),
                callback=self.action_focus_terminal,
                keywords=["terminal", "bash", "focus"],
            ),
            PaletteCommand(
                name=t("cmd.win1.name"),
                description=t("cmd.win1.desc"),
                callback=lambda: self.action_focus_window(1),
                keywords=["window", "focus"],
            ),
            PaletteCommand(
                name=t("cmd.win2.name"),
                description=t("cmd.win2.desc"),
                callback=lambda: self.action_focus_window(2),
                keywords=["window", "focus"],
            ),
            PaletteCommand(
                name=t("cmd.win3.name"),
                description=t("cmd.win3.desc"),
                callback=lambda: self.action_focus_window(3),
                keywords=["window", "focus"],
            ),
            PaletteCommand(
                name=t("cmd.git_commit.name"),
                description=t("cmd.git_commit.desc"),
                callback=self._focus_commit_input,
                keywords=["git", "commit", "stage"],
            ),
            PaletteCommand(
                name=t("cmd.quit.name"),
                description=t("cmd.quit.desc"),
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
