---
name: textual-tui-design
description: "Textual TUI Design System — design tokens, component standards, layout patterns, and reusable CSS templates for beautiful terminal apps. Inspired by Crush & Textualize."
version: 2.0.0
author: Hermes Agent
tags: [textual, tui, design-system, css, terminal-ui, theming]
---

# Textual TUI Design System

一套可复用的终端界面（TUI）设计系统，基于 Textual 框架，参考 Charmbracelet Crush 的设计理念。

## 目录

1. [Design Tokens](#1-design-tokens)
2. [视觉层次规范](#2-视觉层次规范)
3. [组件规范](#3-组件规范)
4. [布局模式](#4-布局模式)
5. [颜色方案](#5-颜色方案)
6. [动效规范](#6-动效规范)
7. [CSS 模板](#7-css-模板)
8. [常见陷阱](#8-常见陷阱)

---

## 1. Design Tokens

Design Tokens 是设计系统的原子，所有样式必须基于 Tokens 构建，不允许使用硬编码值。

### 1.1 颜色 Token

| Token | 默认值 | 用途 |
|-------|--------|------|
| `$primary` | `#7c3aed` | 主色，用于按钮、标题、活动状态 |
| `$primary-darken-1` | `#6d28d9` | 主色深色变体，hover 状态 |
| `$primary-lighten-1` | `#8b5cf6` | 主色浅色变体 |
| `$secondary` | `#3b82f6` | 次要色，用于链接、辅助标签 |
| `$accent` | `#f59e0b` | 强调色，用于重要标识、告警、卓越状态 |
| `$success` | `#10b981` | 成功状态 |
| `$warning` | `#f59e0b` | 警告状态 |
| `$error` | `#ef4444` | 错误状态 |
| `$info` | `#3b82f6` | 信息提示 |
| `$surface` | `#0f172a` | 页面背景（深色） |
| `$surface-raised` | `#1e293b` | 比背景略高的层（卡片、面板背景） |
| `$surface-inset` | `#020617` | 比背景更深的层（input 背景、代码区） |
| `$text` | `#e2e8f0` | 主要文本 |
| `$text-secondary` | `#94a3b8` | 次要文本、描述 |
| `$text-muted` | `#64748b` | 失活文本、占位符、日期 |
| `$text-inverse` | `#0f172a` | 在亮色背景上的文本 |
| `$border` | `#334155` | 普通边框 |
| `$border-subtle` | `#1e293b` | 分隔线，隐藏边框但占位 |
| `$border-active` | `#7c3aed` | 活动状态边框 |

> 定义为 CSS 变量时使用连字符格式：`--primary-darken-1` 而非 `--primaryDarken1`。

### 1.2 间距 Token

| Token | 值 | 用途 |
|-------|----|------|
| `$space-xs` | 0 | 紧密布局、分隔线 |
| `$space-sm` | 1 | 紧凑嵌套、图标旁边距 |
| `$space-md` | 2 | 标准内边距 |
| `$space-lg` | 3 | 卡片内边距 |
| `$space-xl` | 4 | 大模块内边距 |
| `$space-2xl` | 5 | 页面级 padding |

### 1.3 字体 Token

| Token | 值 | 用途 |
|-------|----|------|
| `$text-xs` | `text-style: dim` | 辅助信息、时间戳 |
| `$text-sm` | 默认 | 正文、描述 |
| `$text-md` | `text-style: bold` | 标题、标签 |
| `$text-lg` | `text-style: bold` | 大标题 |
| `$text-xl` | `text-style: bold` | 页面主标题 |

### 1.4 圆角 Token

| Token | 值 | 用途 |
|-------|----|------|
| `$radius-none` | `border: none` | 不需要边框的元素 |
| `$radius-sm` | `border: solid` | 标准容器、列表项 |
| `$radius-md` | `border: round` | 卡片、面板、模态框（推荐） |
| `$radius-lg` | `border: round` | 大型面板 |

> 注意：Textual 的 `round` 边框不是空心圆角，而是用圆形字符替换角落，比例如 `╭` `╮` `╰` `╯`。这是 TUI 中最好的圆角表现。

### 1.5 动效 Token

| Token | 值 | 用途 |
|-------|----|------|
| `$duration-instant` | 0.1s | 按钮 hover、焦点状态 |
| `$duration-fast` | 0.2s | 卡片 hover、边框变化 |
| `$duration-normal` | 0.3s | 屏幕切换、过渡 |
| `$duration-slow` | 0.5s | 闪亮动画、重要变化 |
| `$ease-default` | `out_cubic` | 默认 easing |
| `$ease-bounce` | `out_bounce` | 弹性动画 |
| `$ease-elastic` | `out_elastic` | 缓冲动画 |

---

## 2. 视觉层次规范

视觉层次是设计系统中最容易被忽视的部分。必须根据重要性分配视觉权重。

### 2.1 层次金字塔

```
┌────────────────────────────────────────────────┐
│  第一层：主标题                      text-lg, bold, $text  │
│  第二层：分区标题 / 卡片标题           text-md, bold, $text-secondary │
│  第三层：正文、列表项                   text-sm, normal, $text  │
│  第四层：辅助描述、占位符              text-xs, dim, $text-muted  │
│  背景层：面板背景                      $surface-raised / $surface   │
└────────────────────────────────────────────────┘
```

### 2.2 样式应用规则

**Never use direct color values.** Always reference tokens.

| 元素类型 | 背景色 | 文字色 | 边框 | 文字样式 |
|---------|--------|--------|------|--------|
| 页面背景 | `$surface` | — | — | — |
| 面板 / 卡片 | `$surface-raised` | — | `$radius-md` + `$border` | — |
| 主标题 | — | `$text` | — | bold |
| 次标题 | — | `$text-secondary` | — | bold |
| 正文 | — | `$text` | — | normal |
| 辅助文本 | — | `$text-muted` | — | dim |
| 按钮 Primary | `$primary` | `$text-inverse` | — | bold |
| 按钮 Secondary | `$surface-raised` | `$text` | `$radius-sm` + `$border` | — |
| Input | `$surface-inset` | `$text` | `$radius-sm` + `$border` | — |
| 活动状态 | — | — | `$border-active` | — |
| 禁用状态 | — | — | — | opacity: 40% |

---

## 3. 组件规范

每个组件都有标准的 CSS 定义。当需要自定义时，先以标准定义为基础，再分支。

### 3.1 按钮 Button

```css
/* 基础按钮 */
Button {
    min-width: 12;
    height: 3;
    background: $surface-raised;
    color: $text;
    border: $radius-sm $border;
    content-align: center middle;
    padding: 0 2;
    text-style: bold;
    transition: all $duration-instant $ease-default;
}

Button:hover {
    background: $surface;
    border: $radius-sm $text-secondary;
    text-style: bold;
}

Button:focus {
    border: $radius-sm $primary;
    background: $surface;
}

Button:active {
    background: $primary-darken-1;
    border: $radius-sm $primary;
    color: $text-inverse;
}

Button:disabled {
    opacity: 0.4;
    border: $radius-sm $border;
}

/* Primary 变体 */
Button.primary {
    background: $primary;
    color: $text-inverse;
    border: $radius-sm $primary;
}

Button.primary:hover {
    background: $primary-lighten-1;
    border: $radius-sm $primary-lighten-1;
}

Button.primary:focus {
    background: $primary;
    border: $radius-sm $accent;
}

/* Accent 变体 — 突出操作 */
Button.accent {
    background: $accent;
    color: $text-inverse;
    border: $radius-sm $accent;
}

Button.accent:hover {
    background: #fbbf24;
    border: $radius-sm #fbbf24;
}

/* Ghost 变体 — 无背景 */
Button.ghost {
    background: transparent;
    border: none;
    color: $text-secondary;
}

Button.ghost:hover {
    color: $text;
    background: $surface-raised;
}
```

### 3.2 卡片 Card

```css
/* 基础卡片 */
.card {
    background: $surface-raised;
    border: $radius-md $border;
    padding: $space-md;
    height: auto;
    transition: all $duration-fast $ease-default;
}

.card:hover {
    border: $radius-md $border-active;
}

/* 带标题的卡片 */
.card-header {
    background: $surface-raised;
    border: $radius-md $border;
    border-title: " 卡片标题 ";
    border-title-color: $text-secondary;
    border-title-align: center;
    border-subtitle: " 副标题 ";
    border-subtitle-color: $text-muted;
    padding: $space-md;
    padding-top: $space-lg;
}

/* 信息卡片 — 不同语义 */
.card-info {
    border-left: thick $info;
    border: $radius-md $border;
    border-left: thick $info;
    background: $surface-raised;
    padding: $space-md;
}

.card-success {
    border-left: thick $success;
    background: $surface-raised;
    padding: $space-md;
}

.card-warning {
    border-left: thick $warning;
    background: $surface-raised;
    padding: $space-md;
}

.card-error {
    border-left: thick $error;
    background: $surface-raised;
    padding: $space-md;
}
```

### 3.3 输入框 Input

```css
Input {
    background: $surface-inset;
    color: $text;
    border: $radius-sm $border;
    padding: 0 $space-md;
    height: 3;
    transition: border-color $duration-instant $ease-default;
}

Input:focus {
    border: $radius-sm $primary;
    background: $surface-inset;
}

Input:disabled {
    opacity: 0.4;
    background: $surface;
}

Input.plain {
    border: none;
    border-bottom: solid $border;
    border-radius: 0;
    background: transparent;
}

Input.plain:focus {
    border-bottom: solid $primary;
}
```

### 3.4 列表 ListView / OptionList

```css
ListView {
    background: $surface-raised;
    border: $radius-sm $border;
    padding: $space-sm 0;
}

ListView > ListItem {
    height: 3;
    padding: 0 $space-md;
    content-align: left middle;
    color: $text;
    transition: background $duration-instant $ease-default;
}

ListView > ListItem:hover {
    background: $surface;
}

ListView > ListItem:focus {
    background: $surface;
    color: $primary;
}

ListView > ListItem.--highlight {
    background: $primary;
    color: $text-inverse;
    text-style: bold;
}

ListView > ListItem.--highlight:hover {
    background: $primary-darken-1;
}

OptionList {
    background: $surface-raised;
    border: $radius-sm $border;
    padding: $space-sm 0;
}

OptionList > .option-list--option {
    padding: 0 $space-md;
    height: 3;
    content-align: left middle;
    color: $text;
}

OptionList > .option-list--option-highlighted {
    background: $primary;
    color: $text-inverse;
    text-style: bold;
}

OptionList > .option-list--option-hover {
    background: $surface;
}
```

### 3.5 表格 DataTable

```css
DataTable {
    background: $surface-raised;
    border: $radius-sm $border;
}

DataTable > .datatable--header {
    background: $surface;
    color: $text-secondary;
    text-style: bold;
    height: 3;
    content-align: center middle;
    border-bottom: solid $border;
}

DataTable > .datatable--header-hover {
    background: $surface-raised;
    color: $primary;
}

DataTable > .datatable--row {
    height: 3;
    color: $text;
    content-align: center middle;
    transition: background $duration-instant $ease-default;
}

DataTable > .datatable--row-hover {
    background: $surface;
    color: $primary;
}

DataTable > .datatable--row-selected {
    background: $primary;
    color: $text-inverse;
    text-style: bold;
}

DataTable > .datatable--row-cursor {
    background: $primary-darken-1;
    color: $text-inverse;
}

DataTable > .datatable--cell {
    padding: 0 $space-md;
}
```

### 3.6 标签页 TabbedContent

```css
TabbedContent {
    background: $surface-raised;
    border: $radius-md $border;
    padding: $space-md;
}

Tabs {
    height: 3;
    dock: top;
    background: $surface-raised;
    border-bottom: solid $border;
}

Tabs > Tab {
    padding: 0 $space-lg;
    height: 3;
    content-align: center middle;
    color: $text-muted;
    text-style: normal;
    border-bottom: solid transparent;
    transition: all $duration-instant $ease-default;
}

Tabs > Tab:hover {
    color: $text;
    border-bottom: solid $border-active;
}

Tabs > Tab.--active {
    color: $primary;
    text-style: bold;
    border-bottom: solid $primary;
}
```

### 3.7 Header / Footer

```css
Header {
    dock: top;
    height: 3;
    background: $surface-raised;
    color: $text-secondary;
    border-bottom: solid $border;
    padding: 0 $space-md;
    content-align: left middle;
}

Header > .header--title {
    text-style: bold;
    color: $text;
}

Header > .header--subtitle {
    color: $text-muted;
    text-style: dim;
}

Footer {
    dock: bottom;
    height: 1;
    background: $surface-raised;
    color: $text-muted;
    border-top: solid $border;
    content-align: center middle;
}

Footer > .footer--key {
    color: $text-secondary;
    text-style: bold;
}

Footer > .footer--description {
    color: $text-muted;
    text-style: dim;
}
```

### 3.8 分隔线 Rule

```css
Rule {
    color: $border;
    height: 1;
    margin: $space-md 0;
}

Rule.title {
    color: $border;
    content-align: center middle;
}

Rule.title > .rule--title {
    color: $text-muted;
    text-style: dim;
    padding: 0 $space-md;
}
```

### 3.9 进度条 ProgressBar

```css
ProgressBar {
    height: 3;
    background: $surface-inset;
    border: $radius-sm $border;
    padding: 0;
}

ProgressBar > .bar {
    background: $primary;
    width: 100%;
    color: $text-inverse;
    content-align: center middle;
    text-style: bold;
}

ProgressBar.success > .bar {
    background: $success;
}

ProgressBar.warning > .bar {
    background: $warning;
}

ProgressBar.error > .bar {
    background: $error;
}
```

### 3.10 Toast 通知

```css
/* Toast 通知条 */
.toast {
    background: $surface-raised;
    border: $radius-sm $border;
    padding: $space-md $space-lg;
    height: auto;
    min-width: 40;
    max-width: 60;
    content-align: left middle;
    transition: opacity $duration-normal $ease-default;
}

.toast.success {
    border-left: thick $success;
    background: $surface-raised;
}

.toast.error {
    border-left: thick $error;
    background: $surface-raised;
}

.toast.warning {
    border-left: thick $warning;
    background: $surface-raised;
}

.toast.info {
    border-left: thick $info;
    background: $surface-raised;
}

.toast > .toast--icon {
    width: 3;
    content-align: center middle;
}

.toast > .toast--message {
    color: $text;
    text-style: normal;
}

.toast > .toast--time {
    color: $text-muted;
    text-style: dim;
    text-align: right;
}
```

---

## 4. 布局模式

### 4.1 标准应用布局

```
┌─────────────────────────────────────────────────┐
│  Header (dock: top, height: 3)                     │
├─────────────────────────────────────────────────┤
│  Sidebar (dock: left, width: 30)                    │
│  ┌────────────────────────────────────────────────┐ │
│  │  Main Content (height: 1fr)                     │ │
│  │  ┌─────────────────────────────┐   │ │
│  │  │  Content Header                            │   │ │
│  │  ├─────────────────────────────┤   │ │
│  │  │  Content Body (height: 1fr)                │   │ │
│  │  │  ┌──────────┐ ┌──────────┐      │   │ │
│  │  │  │ Card 1   │ │ Card 2   │      │   │ │
│  │  │  └──────────┘ └──────────┘      │   │ │
│  │  └─────────────────────────────┘   │ │
│  └────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│  Footer (dock: bottom, height: 1)                    │
└─────────────────────────────────────────────────┘
```

```css
/* 实现 */
Screen {
    layers: base overlay;
}

Header {
    dock: top;
    height: 3;
    layer: base;
}

Footer {
    dock: bottom;
    height: 1;
    layer: base;
}

#sidebar {
    dock: left;
    width: 30;
    height: 100%;
    layer: base;
    border-right: solid $border;
    background: $surface-raised;
}

#main {
    layout: vertical;
    height: 100%;
    layer: base;
    padding: $space-md;
}

#content-header {
    height: auto;
    margin-bottom: $space-md;
}

#content-body {
    layout: grid;
    grid-size: 2;
    grid-gutter: $space-md;
    height: 1fr;
}
```

### 4.2 仪表盘布局

```css
#dashboard {
    layout: grid;
    grid-size: 3;
    grid-gutter: $space-md;
    padding: $space-md;
    height: auto;
}

.dashboard-card {
    background: $surface-raised;
    border: $radius-md $border;
    padding: $space-lg;
    height: auto;
    min-height: 8;
}

.dashboard-card > .card-value {
    text-style: bold;
    color: $primary;
    text-align: center;
    height: 3;
    content-align: center middle;
}

.dashboard-card > .card-label {
    color: $text-muted;
    text-align: center;
    height: 1;
    content-align: center middle;
    text-style: dim;
}

.dashboard-card.success > .card-value { color: $success; }
.dashboard-card.warning > .card-value { color: $warning; }
.dashboard-card.error > .card-value { color: $error; }
```

### 4.3 对话框布局

```css
/* 模态对话框 */
#modal-overlay {
    background: $surface 80%;
    layer: overlay;
    align: center middle;
}

#modal-dialog {
    width: 60;
    height: auto;
    min-height: 12;
    background: $surface-raised;
    border: $radius-lg $border;
    padding: $space-xl;
    layer: overlay;
}

#modal-dialog > .dialog-title {
    text-style: bold;
    color: $text;
    height: 3;
    content-align: left middle;
    margin-bottom: $space-md;
}

#modal-dialog > .dialog-body {
    color: $text-secondary;
    height: 1fr;
    margin-bottom: $space-lg;
}

#modal-dialog > .dialog-actions {
    layout: horizontal;
    height: auto;
    content-align: right middle;
    gap: $space-md;
}
```

### 4.4 设置面板布局

```css
#settings-layout {
    layout: horizontal;
    height: 1fr;
}

#settings-nav {
    width: 25;
    dock: left;
    border-right: solid $border;
    background: $surface-raised;
    padding: $space-md 0;
}

#settings-nav > .nav-item {
    height: 3;
    padding: 0 $space-lg;
    content-align: left middle;
    color: $text-secondary;
    transition: all $duration-instant $ease-default;
}

#settings-nav > .nav-item:hover {
    color: $text;
    background: $surface;
}

#settings-nav > .nav-item.active {
    color: $primary;
    text-style: bold;
    border-left: thick $primary;
    background: $surface;
}

#settings-content {
    layout: vertical;
    height: 1fr;
    padding: $space-xl;
    overflow-y: auto;
}

.settings-section {
    margin-bottom: $space-xl;
}

.settings-section > .section-title {
    text-style: bold;
    color: $text;
    height: 3;
    content-align: left middle;
    margin-bottom: $space-md;
    border-bottom: solid $border;
}

.settings-section > .section-description {
    color: $text-muted;
    margin-bottom: $space-lg;
    text-style: dim;
}
```

### 4.5 分拆面板布局

```css
#split-pane {
    layout: horizontal;
    height: 1fr;
}

#left-pane {
    width: 40%;
    border-right: solid $border;
    background: $surface-raised;
    padding: $space-md;
}

#right-pane {
    width: 60%;
    background: $surface;
    padding: $space-md;
}

/* 可拖动分割线风格 */
.pane-divider {
    width: 1;
    background: $border;
    content-align: center middle;
    color: $text-muted;
    text-style: dim;
}

.pane-divider:hover {
    background: $primary;
    color: $text-inverse;
}
```

---

## 5. 颜色方案

### 5.1 Crush Dark (默认)

```css
Screen {
    --primary: #7c3aed;
    --primary-darken-1: #6d28d9;
    --primary-lighten-1: #8b5cf6;
    --secondary: #3b82f6;
    --accent: #f59e0b;
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --info: #3b82f6;
    --surface: #0f172a;
    --surface-raised: #1e293b;
    --surface-inset: #020617;
    --text: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --text-inverse: #0f172a;
    --border: #334155;
    --border-subtle: #1e293b;
    --border-active: #7c3aed;
}
```

### 5.2 Slate (冷灰调)

```css
Screen.slate {
    --primary: #6366f1;
    --primary-darken-1: #4f46e5;
    --primary-lighten-1: #818cf8;
    --secondary: #0ea5e9;
    --accent: #f43f5e;
    --success: #22c55e;
    --warning: #eab308;
    --error: #ef4444;
    --info: #0ea5e9;
    --surface: #0c0a09;
    --surface-raised: #1c1917;
    --surface-inset: #000000;
    --text: #f5f5f4;
    --text-secondary: #a8a29e;
    --text-muted: #78716c;
    --text-inverse: #0c0a09;
    --border: #292524;
    --border-subtle: #1c1917;
    --border-active: #6366f1;
}
```

### 5.3 Rose Pine

```css
Screen.rose-pine {
    --primary: #c4a7e7;
    --primary-darken-1: #b08fd4;
    --primary-lighten-1: #d4b8f0;
    --secondary: #9ccfd8;
    --accent: #f6c177;
    --success: #31748f;
    --warning: #f6c177;
    --error: #eb6f92;
    --info: #9ccfd8;
    --surface: #191724;
    --surface-raised: #1f1d2e;
    --surface-inset: #111019;
    --text: #e0def4;
    --text-secondary: #908caa;
    --text-muted: #6e6a86;
    --text-inverse: #191724;
    --border: #26233a;
    --border-subtle: #1f1d2e;
    --border-active: #c4a7e7;
}
```

### 5.4 Light (浅色方案)

```css
Screen.light {
    --primary: #7c3aed;
    --primary-darken-1: #6d28d9;
    --primary-lighten-1: #8b5cf6;
    --secondary: #2563eb;
    --accent: #d97706;
    --success: #059669;
    --warning: #d97706;
    --error: #dc2626;
    --info: #2563eb;
    --surface: #ffffff;
    --surface-raised: #f8fafc;
    --surface-inset: #f1f5f9;
    --text: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --text-inverse: #ffffff;
    --border: #e2e8f0;
    --border-subtle: #f1f5f9;
    --border-active: #7c3aed;
}
```

---

## 6. 动效规范

### 6.1 动画时长表

| 动画类型 | 时长 | Easing | 备注 |
|---------|------|--------|------|
| Hover 状态 | 0.1s | out_cubic | 快速响应 |
| 焦点变化 | 0.1s | out_cubic | 快速响应 |
| 边框变化 | 0.2s | out_cubic | 滑动感 |
| 背景色变化 | 0.2s | out_cubic | 滑动感 |
| Opacity 淡入 | 0.3s | out_cubic | 平滑过渡 |
| 屏幕切换 | 0.3s | out_cubic | 平滑过渡 |
| 内容展开 | 0.3s | out_cubic | 折叠面板 |
| 进度动画 | 0.5s | out_cubic | 进度条 |
| 突出动画 | 0.5s | out_bounce | Toast |

### 6.2 动画规则

1. **不要让用户等待** — 所有交互反馈必须在 0.1s 内开始
2. **平滑而非弹跳** — 默认使用 out_cubic，防止生硬感
3. **一致的时长** — 同类型动画使用相同时长
4. **不要过度动画** — TUI 中动画是调味品，不是主菜
5. **支持禁用** — 提供选项关闭动画

### 6.3 标准动画模式

```python
# 淡入淡出
widget.styles.animate("opacity", value=1.0, duration=0.3, easing="out_cubic")

# 平滑移动
widget.styles.animate("offset", value=(2, 0), duration=0.3, easing="out_cubic")

# 边框颜色变化（通过修改 CSS 类）
widget.add_class("hovered")  # CSS 中定义 .hovered 的边框和背景

# 进度条动画
progress_bar.update(progress=75)
progress_bar.styles.animate("width", value="75%", duration=0.5, easing="out_cubic")
```

---

## 7. CSS 模板

### 7.1 完整主题文件 (theme.tcss)

将以下内容保存为 `theme.tcss`，然后在 App 中设置 `CSS_PATH = "theme.tcss"`。

```css
/* ════════════════════════════════════════════════════════════════════════════════════════════════ */
/* Design Tokens */
/* ═══════════════════════════════════════════════════════════════════════════════════════════════ */

Screen {
    /* Colors */
    --primary: #7c3aed;
    --primary-darken-1: #6d28d9;
    --primary-lighten-1: #8b5cf6;
    --secondary: #3b82f6;
    --accent: #f59e0b;
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --info: #3b82f6;
    --surface: #0f172a;
    --surface-raised: #1e293b;
    --surface-inset: #020617;
    --text: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --text-inverse: #0f172a;
    --border: #334155;
    --border-subtle: #1e293b;
    --border-active: #7c3aed;

    /* Spacing */
    --space-xs: 0;
    --space-sm: 1;
    --space-md: 2;
    --space-lg: 3;
    --space-xl: 4;
    --space-2xl: 5;

    /* Animation */
    --duration-instant: 0.1;
    --duration-fast: 0.2;
    --duration-normal: 0.3;
    --duration-slow: 0.5;
    --ease-default: out_cubic;

    /* Base styles */
    background: var(--surface);
    color: var(--text);
}

/* ═════════════════════════════════════════════════════════════════════════════════════════════════ */
/* Layout Primitives */
/* ═══════════════════════════════════════════════════════════════════════════════════════════════ */

.container {
    layout: vertical;
    height: auto;
    padding: var(--space-md);
}

.container-horizontal {
    layout: horizontal;
    height: auto;
    gap: var(--space-md);
}

.stack {
    layout: vertical;
    height: auto;
    gap: var(--space-md);
}

.stack-sm {
    layout: vertical;
    height: auto;
    gap: var(--space-sm);
}

.stack-lg {
    layout: vertical;
    height: auto;
    gap: var(--space-lg);
}

.flex {
    height: 1fr;
}

.flex-auto {
    height: auto;
}

.align-center {
    content-align: center middle;
}

.align-left {
    content-align: left middle;
}

.align-right {
    content-align: right middle;
}

/* ═══════════════════════════════════════════════════════════════════════════════════════════════════ */
/* Typography */
/* ═════════════════════════════════════════════════════════════════════════════════════════════════ */

.text-xs {
    text-style: dim;
    color: var(--text-muted);
}

.text-sm {
    color: var(--text-secondary);
}

.text-md {
    text-style: bold;
    color: var(--text);
}

.text-lg {
    text-style: bold;
    color: var(--text);
    height: 3;
    content-align: left middle;
}

.text-xl {
    text-style: bold;
    color: var(--text);
    height: 4;
    content-align: left middle;
}

.text-primary {
    color: var(--primary);
}

.text-accent {
    color: var(--accent);
}

.text-success {
    color: var(--success);
}

.text-warning {
    color: var(--warning);
}

.text-error {
    color: var(--error);
}

.text-muted {
    color: var(--text-muted);
    text-style: dim;
}

/* ═══════════════════════════════════════════════════════════════════════════════════════════════════ */
/* Surface */
/* ══════════════════════════════════════════════════════════════════════════════════════════════════ */

.surface {
    background: var(--surface);
}

.surface-raised {
    background: var(--surface-raised);
    border: round var(--border);
    padding: var(--space-md);
}

.surface-inset {
    background: var(--surface-inset);
    border: solid var(--border);
    padding: var(--space-md);
}

/* ═══════════════════════════════════════════════════════════════════════════════════════════════════ */
/* Components */
/* ═══════════════════════════════════════════════════════════════════════════════════════════════════ */

Button {
    min-width: 12;
    height: 3;
    background: var(--surface-raised);
    color: var(--text);
    border: solid var(--border);
    content-align: center middle;
    padding: 0 var(--space-md);
    text-style: bold;
    transition: all var(--duration-instant) var(--ease-default);
}

Button:hover {
    background: var(--surface);
    border: solid var(--text-secondary);
}

Button:focus {
    border: solid var(--primary);
    background: var(--surface);
}

Button:disabled {
    opacity: 0.4;
    border: solid var(--border);
}

Button.primary {
    background: var(--primary);
    color: var(--text-inverse);
    border: solid var(--primary);
}

Button.primary:hover {
    background: var(--primary-lighten-1);
    border: solid var(--primary-lighten-1);
}

Button.accent {
    background: var(--accent);
    color: var(--text-inverse);
    border: solid var(--accent);
}

Button.ghost {
    background: transparent;
    border: none;
    color: var(--text-secondary);
}

Button.ghost:hover {
    color: var(--text);
    background: var(--surface-raised);
}

Input {
    background: var(--surface-inset);
    color: var(--text);
    border: solid var(--border);
    padding: 0 var(--space-md);
    height: 3;
    transition: border-color var(--duration-instant) var(--ease-default);
}

Input:focus {
    border: solid var(--primary);
    background: var(--surface-inset);
}

Input:disabled {
    opacity: 0.4;
}

Header {
    dock: top;
    height: 3;
    background: var(--surface-raised);
    color: var(--text-secondary);
    border-bottom: solid var(--border);
    padding: 0 var(--space-md);
    content-align: left middle;
}

Header > .header--title {
    text-style: bold;
    color: var(--text);
}

Header > .header--subtitle {
    color: var(--text-muted);
    text-style: dim;
}

Footer {
    dock: bottom;
    height: 1;
    background: var(--surface-raised);
    color: var(--text-muted);
    border-top: solid var(--border);
    content-align: center middle;
}

.card {
    background: var(--surface-raised);
    border: round var(--border);
    padding: var(--space-md);
    height: auto;
    transition: all var(--duration-fast) var(--ease-default);
}

.card:hover {
    border: round var(--border-active);
}

.card-header {
    background: var(--surface-raised);
    border: round var(--border);
    border-title-color: var(--text-secondary);
    border-title-align: center;
    padding: var(--space-md);
    padding-top: var(--space-lg);
    height: auto;
}

.card-success {
    border-left: thick var(--success);
    background: var(--surface-raised);
    padding: var(--space-md);
}

.card-warning {
    border-left: thick var(--warning);
    background: var(--surface-raised);
    padding: var(--space-md);
}

.card-error {
    border-left: thick var(--error);
    background: var(--surface-raised);
    padding: var(--space-md);
}

.card-info {
    border-left: thick var(--info);
    background: var(--surface-raised);
    padding: var(--space-md);
}

DataTable {
    background: var(--surface-raised);
    border: solid var(--border);
}

DataTable > .datatable--header {
    background: var(--surface);
    color: var(--text-secondary);
    text-style: bold;
    height: 3;
    content-align: center middle;
    border-bottom: solid var(--border);
}

DataTable > .datatable--row {
    height: 3;
    color: var(--text);
    content-align: center middle;
    transition: background var(--duration-instant) var(--ease-default);
}

DataTable > .datatable--row-hover {
    background: var(--surface);
    color: var(--primary);
}

DataTable > .datatable--row-selected {
    background: var(--primary);
    color: var(--text-inverse);
    text-style: bold;
}

TabbedContent {
    background: var(--surface-raised);
    border: round var(--border);
    padding: var(--space-md);
}

Tabs {
    height: 3;
    dock: top;
    background: var(--surface-raised);
    border-bottom: solid var(--border);
}

Tabs > Tab {
    padding: 0 var(--space-lg);
    height: 3;
    content-align: center middle;
    color: var(--text-muted);
    text-style: normal;
    border-bottom: solid transparent;
    transition: all var(--duration-instant) var(--ease-default);
}

Tabs > Tab:hover {
    color: var(--text);
    border-bottom: solid var(--border-active);
}

Tabs > Tab.--active {
    color: var(--primary);
    text-style: bold;
    border-bottom: solid var(--primary);
}

ListView {
    background: var(--surface-raised);
    border: solid var(--border);
    padding: var(--space-sm) 0;
}

ListView > ListItem {
    height: 3;
    padding: 0 var(--space-md);
    content-align: left middle;
    color: var(--text);
    transition: background var(--duration-instant) var(--ease-default);
}

ListView > ListItem:hover {
    background: var(--surface);
}

ListView > ListItem.--highlight {
    background: var(--primary);
    color: var(--text-inverse);
    text-style: bold;
}

OptionList {
    background: var(--surface-raised);
    border: solid var(--border);
    padding: var(--space-sm) 0;
}

OptionList > .option-list--option {
    padding: 0 var(--space-md);
    height: 3;
    content-align: left middle;
    color: var(--text);
}

OptionList > .option-list--option-highlighted {
    background: var(--primary);
    color: var(--text-inverse);
    text-style: bold;
}

ProgressBar {
    height: 1;
    background: var(--surface-inset);
    border: solid var(--border);
}

ProgressBar > .bar {
    background: var(--primary);
    width: 100%;
}

Rule {
    color: var(--border);
    height: 1;
    margin: var(--space-md) 0;
}

/* ═══════════════════════════════════════════════════════════════════════════════════════════════════ */
/* Layout Patterns */
/* ═══════════════════════════════════════════════════════════════════════════════════════════════════ */

.app-shell {
    layout: vertical;
    height: 100%;
}

.app-shell > .app-header {
    dock: top;
    height: 3;
}

.app-shell > .app-footer {
    dock: bottom;
    height: 1;
}

.app-shell > .app-body {
    layout: horizontal;
    height: 1fr;
}

.app-shell > .app-body > .app-sidebar {
    dock: left;
    width: 30;
    border-right: solid var(--border);
    background: var(--surface-raised);
    padding: var(--space-md);
}

.app-shell > .app-body > .app-content {
    layout: vertical;
    height: 1fr;
    padding: var(--space-md);
}

.grid-2 {
    layout: grid;
    grid-size: 2;
    grid-gutter: var(--space-md);
}

.grid-3 {
    layout: grid;
    grid-size: 3;
    grid-gutter: var(--space-md);
}

.grid-4 {
    layout: grid;
    grid-size: 4;
    grid-gutter: var(--space-md);
}

.modal-overlay {
    background: var(--surface) 80%;
    layer: overlay;
    align: center middle;
}

.modal-dialog {
    width: 60;
    height: auto;
    min-height: 12;
    background: var(--surface-raised);
    border: round var(--border);
    padding: var(--space-xl);
    layer: overlay;
}
```

### 7.2 Python 入口文件

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import Vertical, Horizontal

class DesignSystemApp(App):
    """基于 Design System 的 Textual 应用"""

    CSS_PATH = "theme.tcss"

    BINDINGS = [
        ("q", "quit", "退出"),
        ("d", "toggle_dark", "切换主题"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="app-shell"):
            yield Header(show_clock=True, classes="app-header")
            with Horizontal(classes="app-body"):
                with Vertical(classes="app-sidebar"):
                    yield Static("导航", classes="text-md")
                    yield Static("项目", classes="text-sm text-muted")
                    yield Static("任务", classes="text-sm text-muted")
                with Vertical(classes="app-content"):
                    yield Static("主内容", classes="text-lg")
                    yield Static("这里是内容区域", classes="text-sm text-secondary")
            yield Footer(classes="app-footer")
```

---

## 8. 常见陷阱

### 8.1 颜色使用

- ❌ **使用硬编码值** — 必须通过 Token 引用。修改一处变量，全局自动更新
- ❌ **主色过多** — 一个页面不超过 2 个主色（primary + accent），辅助色用于标签、链接
- ❌ **忽略深色背景** — 深色背景下使用亮色文字时，确保对比度足够（WCAG 4.5:1 以上）
- ❌ **使用纯黑纯白** — 终端不是打印机，使用带色相的深/浅色（如 #0f172a 而非 #000000）

### 8.2 间距使用

- ❌ **忽略 gutter** — Grid 布局中，不设 grid-gutter 的话元素会紧贴，总是丑陋的
- ❌ **padding 不一致** — 同类型组件使用相同的 padding、连不同的 margin
- ❌ **屏幕过满** — 小屏幕终端记得考虑最小尺寸（80列24行是安全基线）

### 8.3 边框使用

- ❌ **混用多种边框类型** — 一个应用中只用一种边框类型（推荐 round），保持一致性
- ❌ **边框颜色过于显眼** — 普通边框使用弱对比度（$border），活动状态用强对比（$border-active）
- ❌ **忘记 border-title** — 卡片和面板上的 border-title 是极好的阅读辅助

### 8.4 交互设计

- ❌ **没有 hover 状态** — 所有可交互元素必须有 hover 反馈
- ❌ **没有焦点样式** — 焦点状态必须与鼠标 hover 有区别
- ❌ **动画时长不一致** — 同类型交互使用相同时长
- ❌ **没有加载状态** — 异步操作时必须显示 LoadingIndicator

### 8.5 性能

- ❌ **在 on_mount 中阻塞** — 使用 worker 或 asyncio.create_task 执行异步操作
- ❌ **频繁更新时重建 widget** — 使用 self.update() 而非重新 compose
- ❌ **过度嵌套 CSS** — 最多 2-3 层，过深影响渲染性能

### 8.6 代码规范

- ❌ **CSS 变量命名不统一** — 使用连字符格式：`--primary-darken-1` 而非 `--primaryDarken1`
- ❌ **类名和组件名混淆** — 组件类用 PascalCase，CSS class 用 kebab-case，ID 用 谁-case
- ❌ **忽略 `height: 1fr`** — 很多 widget 默认高度 auto，不会填满父容器
- ❌ **忽略 `transition`** — 不加 transition 的话 hover 效果会跳变
