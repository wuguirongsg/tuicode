#!/usr/bin/env python3
"""
Textual 多窗口 TUI Demo — 可拖动窗口、最小化、最大化、关闭

安装依赖：pip install textual
运 行：  python tui_demo.py

快捷键：
  q   退出
  n   新建空窗口
  鼠标拖动标题栏  — 移动窗口
  拖动右下角 ◢   — 调整窗口大小（Textual 原生暂不支持，预留位）
  × / ─ / □    — 关闭 / 最小化 / 最大化
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.events import MouseDown, MouseMove, MouseUp, Click
from rich.syntax import Syntax
from rich.text import Text


# ─── 内容数据 ────────────────────────────────────────────────────────────────

EDITOR_CODE = '''\
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer,
    Button, DataTable,
)

class DemoApp(App):
    """一个 Textual 示例应用。"""

    CSS = """
        Button { margin: 1 2; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable()
        yield Button("Run", id="run")
        yield Footer()

    def on_button_pressed(self) -> None:
        self.notify("Done!")
'''

LOG_LINES = [
    ("09:21:01", "INFO ", "green",  "App started"),
    ("09:21:01", "INFO ", "green",  "CSS loaded (4 rules)"),
    ("09:21:02", "DEBUG", "blue",   "Composing widgets"),
    ("09:21:02", "INFO ", "green",  "Header mounted"),
    ("09:21:02", "INFO ", "green",  "DataTable mounted"),
    ("09:21:03", "WARN ", "yellow", "Screen resize detected"),
    ("09:21:05", "DEBUG", "blue",   "Mouse click @ (42, 18)"),
    ("09:21:05", "INFO ", "green",  "Button#run pressed"),
    ("09:21:06", "INFO ", "green",  'Notification: "Done!"'),
]

FILE_TREE = [
    ("📁", "my_app/",             "bold blue"),
    ("  📄", "app.py",            "cyan"),
    ("  📄", "app.tcss",          "cyan"),
    ("  📁", "widgets/",          "bold blue"),
    ("    📄", "header.py",       "dim"),
    ("    📄", "sidebar.py",      "dim"),
    ("  📁", "tests/",            "bold blue"),
    ("    📄", "test_app.py",     "dim"),
    ("  📄", "requirements.txt",  "dim"),
]


# ─── 窗口控制按钮 ─────────────────────────────────────────────────────────────

class WinButton(Static):
    """
    窗口标题栏上的控制按钮（×关闭 / ─最小化 / □最大化）。

    - 阻止 MouseDown 冒泡，防止点击按钮时意外触发标题栏拖动。
    - 点击时向上遍历组件树找到 TuiWindow 并执行对应操作。
    """

    DEFAULT_CSS = """
    WinButton {
        width: 3;
        height: 1;
        content-align: center middle;
        color: $text-disabled;
    }
    WinButton:hover              { color: $accent; }
    WinButton.close-btn:hover    { color: red; }
    WinButton.min-btn:hover      { color: yellow; }
    WinButton.max-btn:hover      { color: green; }
    """

    def __init__(self, symbol: str, action: str, btn_class: str) -> None:
        super().__init__(symbol, classes=btn_class)
        self._action = action

    def on_mouse_down(self, event: MouseDown) -> None:
        # 阻止事件冒泡到 TitleBar，避免意外开启拖动
        event.stop()

    def on_click(self, event: Click) -> None:
        event.stop()
        win = self._get_window()
        if win is None:
            return
        if self._action == "close":
            win.remove()
        elif self._action == "min":
            win.toggle_minimize()
        elif self._action == "max":
            win.toggle_maximize()

    def _get_window(self) -> TuiWindow | None:
        node = self.parent
        while node is not None:
            if isinstance(node, TuiWindow):
                return node
            node = node.parent
        return None


# ─── 标题栏（拖动手柄）────────────────────────────────────────────────────────

class TitleBar(Widget):
    """
    窗口标题栏。
    - 拖动时通过 capture_mouse() 锁定鼠标事件，利用 delta_x/delta_y 平移窗口。
    - 右侧三个控制按钮由 WinButton 独立处理，不受拖动逻辑干扰。
    """

    DEFAULT_CSS = """
    TitleBar {
        height: 1;
        layout: horizontal;
        background: $panel-darken-1;
        padding: 0 1;
    }
    TitleBar #tb-title {
        width: 1fr;
        color: $text-muted;
    }
    TitleBar #tb-btns {
        width: auto;
        layout: horizontal;
    }
    """

    def __init__(self, title: str) -> None:
        super().__init__()
        self._label = title
        self._dragging = False

    def compose(self) -> ComposeResult:
        yield Static(self._label, id="tb-title")
        with Widget(id="tb-btns"):
            yield WinButton("×", "close", "close-btn")
            yield WinButton("─", "min",   "min-btn")
            yield WinButton("□", "max",   "max-btn")

    def on_mouse_down(self, event: MouseDown) -> None:
        # 拖动前先将窗口置顶，确保拖拽过程中始终显示在最上层
        win = self.parent
        if isinstance(win, TuiWindow):
            win._bring_to_front()
        self._dragging = True
        self.capture_mouse()   # 鼠标移出范围时仍继续接收事件
        event.stop()

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._dragging:
            win: TuiWindow = self.parent  # type: ignore
            win.move_by(event.delta_x, event.delta_y)

    def on_mouse_up(self, event: MouseUp) -> None:
        self._dragging = False
        self.release_mouse()


# ─── 浮动窗口 ─────────────────────────────────────────────────────────────────

class TuiWindow(Widget):
    """
    可拖动的浮动窗口。

    定位原理：
      Textual 的 styles.offset 以字符格为单位进行绝对偏移。
      所有 TuiWindow 直接挂载到 Screen，通过 offset 实现自由定位。

    功能：
      - move_by()         拖动（由 TitleBar 调用）
      - toggle_minimize() 最小化：折叠为仅标题栏高度（1行）
      - toggle_maximize() 最大化：撑满整个终端区域，再次点击还原
      - _bring_to_front() 将本窗口提升到最顶层（移到同类兄弟节点末尾）
      - on_mouse_down()   点击时将本窗口置顶
    """

    DEFAULT_CSS = """
    TuiWindow {
        background: $background;
        border: solid $primary-darken-2;
    }
    TuiWindow:focus-within {
        border: solid $accent;
    }
    TuiWindow > #win-body {
        height: 1fr;
        overflow-y: auto;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        title: str,
        content: Widget,
        x: int = 2,
        y: int = 2,
        width: int = 40,
        height: int = 15,
    ) -> None:
        super().__init__()
        self._title   = title
        self._content = content
        self._x       = x
        self._y       = y
        self._w       = width
        self._h       = height
        self._minimized  = False
        self._max_saved: tuple[int, int, int, int] | None = None

    def compose(self) -> ComposeResult:
        yield TitleBar(self._title)
        with Widget(id="win-body"):
            yield self._content

    def on_mount(self) -> None:
        self.styles.width  = self._w
        self.styles.height = self._h
        self.styles.offset = (self._x, self._y)

    def _bring_to_front(self) -> None:
        """将本窗口移到兄弟 TuiWindow 末尾，使其渲染在最上层。"""
        parent = self.parent
        if parent is None:
            return
        wins = [c for c in parent.children if isinstance(c, TuiWindow)]
        if wins and wins[-1] is not self:
            try:
                parent.move_child(self, after=wins[-1])
            except Exception:
                pass

    def on_mouse_down(self) -> None:
        """点击窗口（正文区）时将本窗口提升到最顶层。"""
        self._bring_to_front()

    def move_by(self, dx: int, dy: int) -> None:
        """相对移动窗口位置（由 TitleBar 拖动时调用）。"""
        self._x = max(0, self._x + dx)
        self._y = max(1, self._y + dy)   # 1 = 菜单栏高度，防止窗口超出顶部
        self.styles.offset = (self._x, self._y)

    def toggle_minimize(self) -> None:
        body = self.query_one("#win-body")
        if self._minimized:
            body.display   = True
            self.styles.height = self._h
            self._minimized    = False
        else:
            body.display   = False
            self.styles.height = 1        # 折叠为仅标题栏一行
            self._minimized    = True

    def toggle_maximize(self) -> None:
        if self._max_saved is not None:
            # 还原到保存的位置和尺寸
            x, y, w, h = self._max_saved
            self._x, self._y, self._w, self._h = x, y, w, h
            self.styles.offset = (x, y)
            self.styles.width  = w
            self.styles.height = h
            self._max_saved = None
        else:
            # 保存当前状态，然后最大化
            self._max_saved = (self._x, self._y, self._w, self._h)
            sw = self.app.screen.size.width
            sh = self.app.screen.size.height
            self._x, self._y = 0, 1
            self._w = sw
            self._h = sh - 2            # 上留菜单栏，下留状态栏
            self.styles.offset = (self._x, self._y)
            self.styles.width  = self._w
            self.styles.height = self._h


# ─── 菜单栏 ──────────────────────────────────────────────────────────────────

class MenuBar(Widget):
    DEFAULT_CSS = """
    MenuBar {
        dock: top;
        height: 1;
        background: $panel-darken-1;
        layout: horizontal;
        padding: 0 1;
    }
    MenuBar .menu-item {
        width: auto;
        padding: 0 2;
        color: $text-muted;
    }
    MenuBar .menu-item:hover {
        background: $surface;
        color: $accent;
    }
    """

    _MENU_LABELS: dict[str, str] = {
        "mi-file": "File",
        "mi-edit": "Edit",
        "mi-view": "View",
        "mi-help": "Help",
    }

    def compose(self) -> ComposeResult:
        for key, label in self._MENU_LABELS.items():
            yield Static(label, classes="menu-item", id=key)

    def on_click(self, event: Click) -> None:
        node = event.widget
        if node is None or not isinstance(node, Static):
            return
        label = self._MENU_LABELS.get(node.id or "", "")
        if label:
            self.app.notify(f"{label} 菜单（可在此扩展下拉逻辑）")


# ─── 状态栏 ──────────────────────────────────────────────────────────────────

class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $panel-darken-1;
        layout: horizontal;
        padding: 0 1;
    }
    StatusBar #sb-left  { width: 1fr; color: $text-muted; }
    StatusBar #sb-right { width: auto; color: $text-muted; }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "[green]● running[/]  Python 3.12  [cyan]Textual[/]",
            id="sb-left",
        )
        yield Static("q:退出  n:新窗口", id="sb-right")


# ─── 主应用 ──────────────────────────────────────────────────────────────────

class WMApp(App):
    """可拖动多窗口 TUI 演示。"""

    TITLE    = "Textual Window Manager Demo"
    BINDINGS = [
        ("q", "quit",       "退出"),
        ("n", "new_window", "新窗口"),
    ]
    CSS = "Screen { background: #0d1117; }"

    def compose(self) -> ComposeResult:
        yield MenuBar()
        yield StatusBar()

        # ── 编辑器窗口（Rich 语法高亮）──────────────────────────
        yield TuiWindow(
            title="app.py — editor",
            content=Static(
                Syntax(
                    EDITOR_CODE, "python",
                    theme="github-dark",
                    line_numbers=True,
                )
            ),
            x=2, y=2, width=52, height=24,
        )

        # ── 日志窗口 ─────────────────────────────────────────────
        log = Text()
        for ts, level, color, msg in LOG_LINES:
            log.append(f"{ts} ", style="dim")
            log.append(f"{level} ", style=color)
            log.append(f"{msg}\n")
        yield TuiWindow(
            title="log output",
            content=Static(log),
            x=56, y=2, width=36, height=13,
        )

        # ── 文件树窗口 ───────────────────────────────────────────
        tree = Text()
        for icon, name, style in FILE_TREE:
            tree.append(f"{icon} ")
            tree.append(f"{name}\n", style=style)
        yield TuiWindow(
            title="files",
            content=Static(tree),
            x=56, y=16, width=36, height=10,
        )

    def action_new_window(self) -> None:
        """按 n 动态创建一个新的空窗口。"""
        count = len(self.screen.query(TuiWindow))
        self.screen.mount(
            TuiWindow(
                title=f"new window #{count + 1}",
                content=Static("[dim]空窗口 — 拖动标题栏可以移动我[/dim]"),
                x=10 + count * 3,
                y=5  + count * 2,
                width=30,
                height=6,
            )
        )


if __name__ == "__main__":
    WMApp().run()
