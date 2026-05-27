---
name: textual-tui-design
description: "Design beautiful, high-quality TUI applications with Textual framework. Covers Textual CSS, layouts, styling, widgets, themes, animation, screens, and design philosophy inspired by Charmbracelet Crush."
version: 1.0.0
author: Hermes Agent
tags: [textual, tui, design, python, terminal-ui, css, theming]
---

# Textual TUI Design Skill

设计精美的终端界面（TUI）应用，使用 [Textual](https://textual.textualize.io/) 框架，并参考 [Charmbracelet Crush](https://github.com/charmbracelet/crush) 的设计理念。

## 设计哲学（来自 Crush/Charmbracelet）

1. **克制即优雅** — 配色不超过 4-5 种主色，不要把终端当画布填满
2. **视觉层次清晰** — 标题/正文/辅助信息通过权重（加粗、颜色、字号暗示）区分
3. **呼吸感** — padding、margin 舍得给，拥挤是丑陋的根源
4. **一致性** — 同类型元素在全局保持相同的颜色/边框/间距
5. **圆润不尖锐** — 善用圆角边框（round）、柔和阴影（不是必要的）
6. **Dark Mode First** — 终端用户默认深色，从深色开始设计，再适配浅色
7. **字体为王** — 尽量用 Rich 的 Text 对象而不是纯字符串，利用样式化文本
8. **流畅过渡** — 加载、切换、状态变化用动画，不要生硬跳变
9. **信息密度可控** — 不要把所有信息堆在一个页面，用 Screen 切换或折叠组件
10. **交互反馈** — 按钮悬停变色、加载指示器、Toast 通知，让用户感觉到系统在响应

## 快速开始

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class MyApp(App):
    """一个漂亮的 TUI 应用"""

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        dock: top;
        background: $primary;
        color: $text;
    }

    Footer {
        dock: bottom;
    }

    #main {
        layout: grid;
        grid-size: 2 1;
        grid-gutter: 1;
        padding: 1;
    }

    .card {
        background: $panel;
        border: tall $primary;
        border-title-color: $primary;
        padding: 1 2;
    }

    .card:hover {
        border: tall $accent;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Static(id="main"):
            yield Static("左侧面板", classes="card")
            yield Static("右侧面板", classes="card")
        yield Footer()

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

## 1. 应用基础结构

### App 类

每个 Textual 应用从继承 `App` 开始。关键配置：

```python
class MyApp(App):
    # 内联 CSS（推荐用于中小型应用）
    CSS = """
    Screen { background: $surface; }
    """

    # 或者外部 CSS 文件路径
    CSS_PATH = "app.tcss"

    # 绑定全局快捷键
    BINDINGS = [
        ("q", "quit", "退出"),
        ("d", "toggle_dark", "切换主题"),
        ("ctrl+p", "command_palette", "命令面板"),
    ]

    # 绑定屏幕模式（多屏幕应用）
    SCREENS = {"home": HomeScreen, "settings": SettingsScreen}

    TITLE = "My App"        # 窗口标题
    SUBTITLE = "v1.0"       # 副标题
```

### compose() vs mount()

- **compose()**: 在初始化时 yield 初始 widgets，推荐作为主入口
- **on_mount()**: 应用挂载后的回调，适合动态添加 widgets

```python
def compose(self) -> ComposeResult:
    yield Header(show_clock=True)
    yield ContentSwitcher(initial="main"):
        yield MainContent(id="main")
        yield SettingsPanel(id="settings")
    yield Footer()

def on_mount(self) -> None:
    self.query_one("#main").loading = True
    # 执行异步初始化...
    self.query_one("#main").loading = False
```

## 2. Textual CSS — 样式系统的核心

### 选择器类型

```css
/* 类型选择器 — 匹配特定 widget 类 */
Button { background: blue; }
Header { dock: top; }

/* ID 选择器 — 匹配 #id */
#main-panel { layout: horizontal; }
#status-label { color: $success; }

/* 类选择器 — 匹配 class="..." */
.card { border: solid $primary; }
.card.highlighted { background: $accent; }

/* 伪类选择器 — 交互状态 */
Button:hover { text-style: bold; }
Button:focus { border: thick $accent; }
Button:disabled { opacity: 0.4; }

/* 通用选择器 */
* { padding: 0; margin: 0; }
```

### CSS 变量（推荐！）

```css
/* 在 Screen 上定义变量 — 统一管理调色板 */
Screen {
    --primary: #0077ff;
    --primary-lighten-1: #3399ff;
    --primary-darken-1: #0055cc;
    --accent: #ff6600;
    --success: #00cc66;
    --warning: #ffaa00;
    --error: #ff3355;
    --surface: #1a1b26;
    --panel: #24253a;
    --text: #c0caf5;
    --text-muted: #565f89;
    --border: #3b4261;
}

/* 在变量之上定义全局样式 */
Screen {
    background: var(--surface);
    color: var(--text);
}

.card {
    background: var(--panel);
    border: solid var(--border);
}

.button-primary {
    background: var(--primary);
    color: $text;
}
```

> **提示**: `$primary`, `$secondary`, `$accent`, `$success`, `$warning`, `$error`, `$surface`, `$panel`, `$text`, `$text-muted`, `$border` 是 Textual 内置的语义化颜色变量。在 `dark` 和 `light` 模式下自动切换，强烈推荐优先使用。

### 组合器和优先级

```css
/* 后代组合器 — 匹配所有后代 */
Container Button { margin: 1; }

/* 子代组合器 — 匹配直接子元素 */
Container > Button { margin: 1; }

/* 多个选择器 */
Button, .btn, #submit-btn { min-width: 16; }
```

## 3. 布局系统

### Vertical 布局

子组件从上到下排列：

```css
#sidebar {
    layout: vertical;
    width: 30;
    height: 100%;
}
```

### Horizontal 布局

子组件从左到右排列：

```css
#toolbar {
    layout: horizontal;
    height: 3;
}
```

### Grid 布局（最强大）

```css
#dashboard {
    layout: grid;
    grid-size: 3 2;          /* 3列2行 */
    grid-columns: 1fr 2fr 1fr; /* 列宽比例 */
    grid-rows: auto 1fr;      /* 行高 */
    grid-gutter: 1 2;         /* 行间距 列间距 */
    grid-rows: min-content 1fr; /* 第一行自适应，第二行填满 */
}

/* 跨列/跨行 */
.header-cell { column-span: 3; }
.sidebar-cell { row-span: 2; }
```

### Docking（锚定）

```css
Header {
    dock: top;      /* 固定到顶部 */
    height: 3;
}

Footer {
    dock: bottom;   /* 固定到底部 */
    height: 1;
}

#sidebar {
    dock: left;     /* 固定到左侧 */
    width: 30;
}

#status-bar {
    dock: bottom;   /* 可与 Footer 共存 */
    height: 1;
}
```

### Layers（层叠）

```css
Screen {
    layers: base overlay dialog;
}

#modal-dialog {
    layer: dialog;
    /* 自动在 dialog 层，覆盖 base 和 overlay */
}
```

## 4. 核心样式属性

### 布局和尺寸

```css
.width: 50%;             /* 百分比宽度 */
.min-width: 20;
.max-width: 80;
.height: 100%;           /* 填满父容器 */
.height: auto;           /* 自适应内容 */
.height: 1fr;            /* 网格中的比例单位 */

padding: 1;              /* 上下左右相等 */
padding: 1 2;            /* 垂直 水平 */
padding-left: 2;

margin: 1;
margin: 1 2 3 4;         /* 上 右 下 左 */
```

### 边框（重中之重）

边框是 TUI 视觉层次的核心手段：

```css
/* 边框类型 */
border: solid $border;         /* 实线 */
border: tall $primary;         /* 粗实线—重要元素 */
border: heavy $accent;         /* 最粗边框 */
border: round $border;         /* 圆角—Charm 风格！ */
border: none;                  /* 无边框 */

border: solid $border;         /* 隐藏边框但占位 */
border: blank;                 /* 只占位不显示 */
border: ascii;                 /* ASCII 字符边框 */

/* 单边边框 */
border-left: thick $accent;
border-bottom: solid $border;

/* 边框标题—极好的阅读辅助 */
.title-card {
    border: solid $border;
    border-title: "标题文本";       /* 顶部居中 */
    border-title-align: left;       /* 左对齐 */
    border-subtitle: "副标题";      /* 底部 */
    border-title-color: $primary;
}
```

### 颜色和字体样式

```css
background: $surface;
color: $text;

/* 颜色可以取值、渐变或动画 */
background: $primary 20%;    /* 带透明度的颜色 */
color: auto 70%;              /* 自动反色 + 降低亮度 */

/* 文本样式 */
text-style: bold;             /* 加粗 */
text-style: italic;           /* 斜体 */
text-style: bold italic;      /* 组合 */
text-style: underline;
text-style: strikethrough;

text-align: center;           /* 水平对齐 */
text-align: center middle;    /* 水平垂直居中 */
```

### 内容对齐

```css
content-align: center middle;   /* 水平垂直居中 */
content-align: left top;        /* 左上 */
content-align: right bottom;    /* 右下 */
```

### 不透明度和可见性

```css
opacity: 0.8;         /* 透明度 0.0-1.0 — 可动画 */
visibility: hidden;   /* 隐藏但占位 */
display: none;        /* 隐藏且不占位 */
```

## 5. 调色板设计（来自 Crush 灵感）

Crush 使用了一套精心设计的深色主题调色板，推荐类似方案：

### 深色主题（推荐起始）

```css
Screen {
    --primary: #7c3aed;         /* 紫色主色 */
    --secondary: #2563eb;       /* 蓝色辅助 */
    --accent: #f59e0b;          /* 琥珀色强调 */
    --success: #10b981;         /* 绿色成功 */
    --warning: #f59e0b;         /* 黄色警告 */
    --error: #ef4444;           /* 红色错误 */
    --surface: #0f172a;         /* 最深的背景 */
    --panel: #1e293b;           /* 面板背景 */
    --text: #e2e8f0;            /* 主要文本 */
    --text-muted: #64748b;      /* 次要文本 */
    --border: #334155;          /* 边框颜色 */
}
```

### 主题切换（暗/亮）

```python
from textual.app import App
from textual.theme import Theme

class MyApp(App):
    def on_mount(self):
        # 注册自定义主题
        self.register_theme(Theme(
            name="crush-dark",
            primary="#7c3aed",
            secondary="#2563eb",
            accent="#f59e0b",
            success="#10b981",
            warning="#f59e0b",
            error="#ef4444",
            surface="#0f172a",
            panel="#1e293b",
            text="#e2e8f0",
            text_muted="#64748b",
            border="#334155",
        ))
        self.register_theme(Theme(
            name="crush-light",
            primary="#7c3aed",
            secondary="#3b82f6",
            accent="#d97706",
            success="#059669",
            warning="#d97706",
            error="#dc2626",
            surface="#ffffff",
            panel="#f8fafc",
            text="#0f172a",
            text_muted="#94a3b8",
            border="#e2e8f0",
        ))
        self.theme = "crush-dark"
```

## 6. 内置 Widget 精讲

### 常用核心 Widget

| Widget | 用途 | 关键样式 |
|--------|------|---------|
| `Static` | 纯文本/富文本显示 | `Static("文本")`, 或传入 Rich `Text`/`Renderable` |
| `Label` | 语义标签，支持 Rich Text | `Label("Hello [bold red]World[/]")` |
| `Button` | 按钮 | `variant="primary"/"success"/"warning"/"error"` |
| `Input` | 文本输入 | `placeholder="提示"`, `password=True` |
| `Header` | 顶部栏 | `show_clock=True` |
| `Footer` | 底部快捷键提示 | 自动显示 BINDINGS |
| `DataTable` | 表格 | `add_column()`, `add_row()`, `sort()` |
| `ListView` | 列表 | 支持选中、多选 |
| `OptionList` | 选项列表 | 轻量级列表，比 ListView 更快 |
| `Tree` | 树形控件 | 文件系统、层级数据 |
| `TabbedContent` | 标签页 | `Tab("概览"), Tab("详情")` |
| `ContentSwitcher` | 内容切换 | 搭配按钮切换显示 |
| `Markdown` | Markdown 渲染 | `Markdown("# Title")` |
| `ProgressBar` | 进度条 | `total=100, progress=50` |
| `LoadingIndicator` | 加载动画 | `loading=True/False` |
| `ToastRack` | 通知提示 | `notify("消息", severity="warning")` |
| `Select` | 下拉选择 | `Select([(label, value)])` |
| `Switch` | 开关 | `value=True/False` |
| `Sparkline` | 迷你趋势图 | `Sparkline(data, max=100)` |
| `Collapsible` | 折叠面板 | 内容收起/展开 |
| `RichLog` | 日志/滚动输出 | `write()`, `clear()` |
| `Digits` | 大号数字 | 时钟、计数、大字号 |
| `Placeholder` | 占位测试 | `Placeholder("内容", color="red")` |
| `Rule` | 分割线 | 水平分割 |
| `TextArea` | 代码编辑器 | 语法高亮、行号 |

### 示例：Crush 风格仪表盘

```python
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button, DataTable

class Dashboard(App):
    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        dock: top;
        background: $panel;
        color: $text;
        border-bottom: solid $border;
    }

    Footer {
        dock: bottom;
    }

    #stat-grid {
        layout: grid;
        grid-size: 4;
        grid-gutter: 1;
        padding: 1;
        height: auto;
    }

    .stat-card {
        background: $panel;
        border: round $border;
        padding: 1 2;
        height: 5;
    }

    .stat-card:hover {
        border: round $accent;
    }

    .stat-value {
        text-style: bold;
        color: $primary;
        text-align: center;
    }

    .stat-label {
        color: $text-muted;
        text-align: center;
    }

    #main-content {
        layout: horizontal;
        height: 1fr;
        padding: 0 1;
    }

    #table-panel {
        width: 1fr;
        border: round $border;
        background: $panel;
        padding: 1;
    }

    DataTable {
        height: 1fr;
    }

    DataTable > .datatable--header {
        background: $primary;
        color: $text;
        text-style: bold;
    }

    #side-panel {
        width: 30;
        border: round $border;
        background: $panel;
        margin-left: 1;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="stat-grid"):
            for label in ["活跃项目", "待处理", "完成", "进行中"]:
                with Static(classes="stat-card"):
                    yield Static("42", classes="stat-value")
                    yield Static(label, classes="stat-label")
        with Horizontal(id="main-content"):
            with Static(id="table-panel"):
                yield DataTable()
            with Vertical(id="side-panel"):
                yield Static("[bold]最近活动[/]", classes="panel-title")
                yield Static("• 项目A 已更新\n• 任务B 已完成\n• 用户C 已加入")
        yield Footer()

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("项目", "状态", "进度")
        table.add_rows([
            ("Alpha", "✅", "80%"),
            ("Beta", "🔄", "45%"),
            ("Gamma", "⏸", "20%"),
        ])
```

## 7. Rich 文本样式（Crush 的灵魂）

Crush 大量使用 Rich 的标记语法来创造丰富但不杂乱的文本。Textual 原生支持 Rich：

```python
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

# 方式 1：直接在 widget 中用 Rich 标记
label = Static("[bold #7c3aed]重要提示[/] 请 [italic]仔细[/]阅读文档")
# 方式 2：Rich Text 对象
text = Text()
text.append("Crush ", style="bold purple")
text.append("v2.0 ", style="italic blue")
text.append("is ", style="dim")
text.append("HERE!", style="bold yellow on red")
widget = Static(text)

# 方式 3：Rich Table 在 Static 中
table = Table(show_header=True, header_style="bold magenta")
table.add_column("项目", style="cyan")
table.add_column("状态", justify="center")
table.add_row("核心模块", "[green]✓[/]")
table.add_row("测试套件", "[yellow]🔄[/]")
yield Static(table)

# 方式 4：Rich Panel 创造更丰富的容器样式
from rich.panel import Panel as RichPanel
info_panel = Panel(
    "欢迎使用本应用！\n\n[dim]按 Ctrl+P 打开命令面板[/]",
    title="[bold]提示[/]",
    border_style="blue"
)
yield Static(info_panel, id="welcome-panel")
```

## 8. 动画与过渡

优雅的动画是 Crush 风格的重要特征。Textual 提供内置动画系统：

```python
from textual.app import App, ComposeResult
from textual.widgets import Static
import asyncio

class SmoothApp(App):
    CSS = """
    #box {
        background: $primary;
        color: $text;
        padding: 2 4;
        border: round $accent;
    }
    """

    def compose(self) -> ComposeResult:
        self.box = Static("Hello, Crush!", id="box")
        yield self.box

    def on_mount(self) -> None:
        # 动画属性：offset, opacity, 颜色等
        self.box.styles.animate(
            "opacity", value=1.0, duration=0.5
        )

    def on_button_pressed(self, event):
        # 点击时平滑移动
        self.box.styles.animate(
            "offset", value=(10, 0), duration=0.3,
            easing="out_cubic"
        )

    # 可用的 easing 函数：
    # "linear", "in_out_cubic", "in_out_quad",
    # "out_cubic", "out_bounce", "out_elastic",
    # "in_sine", "out_sine", "in_out_sine"
```

### Screens 之间的切换动画

```python
from textual.screen import Screen
from textual.app import App
from textual.widgets import Button, Static

class HomeScreen(Screen):
    CSS = """
    Screen { background: $surface; }
    Button { margin: 1; }
    """

    def compose(self):
        yield Static("主页面", id="title")
        yield Button("进入设置", id="settings-btn")

    def on_button_pressed(self, event):
        if event.button.id == "settings-btn":
            self.app.push_screen("settings")

class SettingsScreen(Screen):
    CSS = """
    Screen {
        background: $surface;
        opacity: 0;
    }
    """

    def on_mount(self) -> None:
        # 进入时渐入
        self.styles.animate("opacity", value=1, duration=0.3)
```

## 9. 交互与响应设计

### Reactive 属性（自动更新 UI）

```python
from textual.reactive import reactive
from textual.widget import Widget
from textual.app import App, ComposeResult
from textual.widgets import Static, Button

class CounterWidget(Widget):
    count = reactive(0)  # 自动触发 UI 更新

    def render(self):
        return f"[bold]{self.count}[/]"

    def watch_count(self, old, new):
        """count 变化时自动调用"""
        if new > old:
            self.styles.animate("opacity", 0.5, duration=0.1)
            self.styles.animate("opacity", 1.0, duration=0.3)
```

### 键盘绑定

```python
class MyApp(App):
    BINDINGS = [
        ("r", "refresh", "刷新"),
        ("t", "toggle_theme", "切换主题"),
        ("ctrl+s", "save", "保存"),
        ("escape", "back", "返回"),
        ("slash", "search", "搜索"),  # / 键
    ]

    def action_refresh(self):
        self.notify("已刷新!", severity="information")
```

### Toast 通知

```python
# 在任意 action 或事件中
self.notify("操作成功！", severity="success", timeout=3)
self.notify("警告信息", severity="warning")
self.notify("发生错误", severity="error")
self.notify("一般提示", severity="information")
```

## 10. Crush 风格开发清单

设计一个好看的 TUI 时，逐项检查：

### 布局检查
- [ ] 页面有明确的视觉层次（标题 > 内容 > 辅助信息）
- [ ] 核心操作在视觉上突出
- [ ] 面板有足够的 padding 和 margin
- [ ] Header/Footer 使用 dock 固定
- [ ] 长内容页面考虑用 Screen 拆分，不要一次性全堆

### 色彩检查
- [ ] 主色不超过 2 种（primary + accent 足够）
- [ ] 语义色正确使用（绿色=成功，红色=错误）
- [ ] 使用 `$surface`, `$panel`, `$text`, `$text-muted`, `$border` 变量
- [ ] hover/focus 状态有颜色变化
- [ ] 错误状态、加载状态都有对应视觉

### 交互检查
- [ ] 按钮/列表项有 hover 效果
- [ ] 加载中有 LoadingIndicator
- [ ] 操作成功/失败有 Toast 通知
- [ ] 键盘快捷键在 Footer 中显示
- [ ] 重要操作有确认（或撤销）机制
- [ ] 过渡动画流畅（opacity 渐入、offset 滑动）

### 组件检查
- [ ] 使用 Rich Text 而不是纯字符串
- [ ] 按钮使用合适的 variant
- [ ] 数据用 DataTable 而不是自己拼格子
- [ ] 选项列表用 OptionList 而不是手写
- [ ] 折叠内容用 Collapsible
- [ ] 标签页用 TabbedContent

### 精致度检查
- [ ] 边框使用 round 变体（更现代）
- [ ] 关键元素有 border-title
- [ ] 间距一致（统一使用 1 或 2 为单位）
- [ ] 颜色饱和度不要过高
- [ ] 信息量适中，非必要时不显示细节

## 11. 性能优化

```python
# 对于高频更新的 widget，使用 update 而不是重建
class StatusWidget(Widget):
    """高效更新"""
    def update_status(self, text: str) -> None:
        self.update(text)  # 比重新 compose 快得多

# 批量更新
with self.batch():
    widget.styles.background = "red"
    widget.styles.color = "white"
    widget.styles.padding = (1, 2)
```

## 12. 官方参考资源

- Textual 官方文档: https://textual.textualize.io/
- Textual CSS 指南: https://textual.textualize.io/guide/CSS/
- 内置 Widget 画廊: https://textual.textualize.io/widget_gallery/
- 样式参考: https://textual.textualize.io/guide/styles/
- 动画指南: https://textual.textualize.io/guide/animation/
- 布局指南: https://textual.textualize.io/guide/layout/
- Screen 指南: https://textual.textualize.io/guide/screens/
- GitHub: https://github.com/Textualize/textual

## 13. 常见陷阱

- ❌ **CSS 变量用驼峰** — 变量名连字符：`--primary-color` ✓，`--primaryColor` ✗
- ❌ **忘记加 `height: 1fr`** — 很多 widget 默认高度是 auto，不会填满父容器
- ❌ **过度嵌套** — Textual CSS 嵌套最多 2-3 层，过深影响性能
- ❌ **在 on_mount 中调用长时间阻塞** — 使用 worker 或 asyncio.create_task
- ❌ **忽视终端大小** — 设计时要考虑最小终端尺寸（80x24 是安全基线）
- ❌ **Grid 不设 gutter** — 元素会紧贴在一起，永远是丑陋的
- ❌ **颜色过于饱和** — 在高亮色中使用饱和度 60-70%，保持舒适
