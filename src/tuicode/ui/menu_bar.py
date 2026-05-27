from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.events import Click

from tuicode.i18n import t


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
        padding: 0 2;
        color: $primary;
        text-style: bold;
    }
    MenuBar .menu-sep {
        width: 1;
        color: $panel-lighten-2;
    }
    MenuBar .menu-item {
        width: auto;
        padding: 0 2;
        color: $text-muted;
    }
    MenuBar .menu-item:hover {
        background: $surface;
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("◈ TUICODE", classes="brand")
        yield Static("│", classes="menu-sep")
        for key in ("menu.file", "menu.edit", "menu.view", "menu.agents", "menu.help"):
            yield Static(t(key), classes="menu-item", id=f"mi-{key.split('.')[1]}")

    def on_click(self, event: Click) -> None:
        node = event.widget
        if isinstance(node, Static) and "menu-item" in (node.classes or set()):
            self.app.notify(f"{node.render()}{t('menu.todo')}")
