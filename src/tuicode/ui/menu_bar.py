from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.events import Click

from tuicode.i18n import t
from tuicode.ui.taskbar import WindowTaskBar


class MenuBar(Widget):
    DEFAULT_CSS = """
    MenuBar {
        dock: top;
        height: 1;
        layout: horizontal;
        background: $panel;
        padding: 0 1;
    }
    MenuBar .brand {
        width: auto;
        padding: 0 1;
        color: $primary;
        text-style: bold;
    }
    MenuBar .brand:hover {
        background: $surface;
        color: $accent;
    }
    MenuBar .sep {
        width: 1;
        color: $panel-lighten-2;
    }
    MenuBar WindowTaskBar {
        background: transparent;
        padding: 0;
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("◈ TUICODE", classes="brand")
        yield Static("│", classes="sep")
        yield WindowTaskBar()

    def on_click(self, event: Click) -> None:
        node = event.widget
        if isinstance(node, Static) and "brand" in (node.classes or set()):
            self.app.action_command_palette()
