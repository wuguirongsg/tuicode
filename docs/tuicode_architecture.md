# TuiCode — AI 编程智能体的 TUI 宿主环境

## 架构设计文档 v0.2

更新时间:2026-05-28

---

## 1. 产品定位

### 1.1 一句话定位

**为终端编程智能体（Claude Code、Codex、Aider 等）设计的统一 TUI 工作台**，提供 IDE 级的编辑、文件、终端、Git、工作区状态同步体验，让"人 + 多个 AI 智能体"在同一个终端环境里协同工作。

TuiCode 的主路径不是接管智能体，而是承载成熟 CLI 智能体：智能体继续在 PTY 中运行自己的完整交互体系，TuiCode 负责把它们工作的项目状态可视化、同步和组织起来。

### 1.2 不是什么

为了避免方向漂移，先界定边界：

- **不是 VSCode 复刻** —— 不追求完整的 IDE 功能、不做插件市场、不做调试器
- **不是终端模拟器** —— 不替代 Alacritty/iTerm2/Windows Terminal，运行在它们之上
- **不是新的 AI 编程工具** —— 不做自己的智能体，只做宿主和适配
- **不是新的窗口管理器** —— 不替代 tmux/Zellij，定位更高层

### 1.3 是什么

| 维度 | 定位 |
|---|---|
| 形态 | TUI 应用，跑在任意终端模拟器中 |
| 主用户 | 使用 Claude Code / Codex / Aider 等智能体的开发者 |
| 核心价值 | 把"编辑器 + 文件管理 + 多终端 + Git + 智能体会话 + 工作区状态同步"整合为一致体验 |
| 技术栈 | Python + Textual + PTY |
| 部署 | 单一可执行命令，跨平台（Linux/macOS/Windows-WSL） |

---

## 2. 核心设计原则

### 2.1 智能体是一等公民

主流 IDE 把 AI 当成插件（Copilot 浮窗、Cursor 侧栏）。TuiCode 反过来：**编辑器、文件树、终端都是为了让智能体更好地工作而存在**。

这意味着：

- 智能体会话是工作区的一等工作单元，以浮窗 PTY 承载，而不是普通终端里的临时命令
- 多个智能体可以并行会话，互不干扰
- 智能体或用户在项目中产生的文件/Git 变化会被 TuiCode 自动感知并反馈到文件树、编辑器和 Git 面板
- 深度能力（上下文注入、工具调用拦截、MCP 集成）是后续增强，不作为 MVP 主路径

### 2.2 上下文即产品

TuiCode 的核心引擎是**工作区状态聚合器**：它持续维护项目的"当前态"，包括当前活动文件、选区、最近外部文件变化、Git 状态和终端活动。MVP 阶段它主要服务 UI 同步；后续深度集成阶段再按需打包给智能体。

### 2.3 协议驱动，不绑定具体智能体

默认集成方式是 **PTY 承载**：Claude Code、Codex、Aider 等成熟 CLI 智能体保持原有交互和权限体系。抽象的 **Agent Adapter Protocol** 保留为深度集成扩展点，用于未来需要结构化消息、上下文注入或 MCP 工具桥接的场景，不阻塞 MVP。

### 2.4 终端原生

整个产品 100% TUI，不引入 GUI、不引入 Web。用户在 SSH、tmux、screen 里都能用，特别适合服务器开发、远程工作流。

### 2.5 渐进披露

默认界面简洁：编辑器 + 文件树 + 终端。其他功能（Git 面板、Agent 会话、上下文检视器）按需打开。避免初次使用者被界面密度劝退。

### 2.6 工作单元浮动，全局工具固定

界面布局严格遵循一个划分：

- **工作单元**（编辑器、智能体会话）—— 用户主动"在里面工作"的对象，有边界、有生命周期、数量会动态变化。这类对象**浮窗化**，可拖动、缩放、层叠。
- **全局工具**（文件树、Git 状态、运行终端）—— 用户随时调用的辅助工具，位置应稳定可预测。这类对象**固定栅格化**，分布在右栏和底栏。

这条原则让"灵活"和"可预测"在同一界面共存，是 TuiCode 区别于纯 tmux 风格和纯桌面浮窗的关键设计判断。

---

## 3. 目标用户与场景

### 3.1 主要用户画像

**P1 — 智能体重度使用者**

- 已经在用 Claude Code 或 Codex 做日常编程
- 习惯终端工作流，对 GUI IDE 兴趣不大
- 痛点：智能体输出的代码需要切到编辑器查看、Git 操作要切窗口、终端要单独开

**P2 — 服务器/远程开发者**

- 主要在 SSH 远程机器上工作
- 现状是 vim/helix + tmux + lazygit 拼凑
- 痛点：智能体接入麻烦，没有统一上下文

**P3 — AI 编程探索者**

- 想同时试不同智能体（Claude Code vs Codex vs Aider）
- 想观察它们对同一任务的不同行为
- 痛点：没有工具能并行管理多个智能体会话

### 3.2 典型场景

**场景一：用 Claude Code 重构一个模块**

1. 用户在 TuiCode 中打开项目，文件树展开到目标模块
2. 在编辑器里查看现有代码，选中要重构的函数
3. 打开 Claude Code 智能体浮窗，按 Claude Code 原生方式描述任务
4. Claude Code 修改文件、运行测试或执行 Git 命令
5. TuiCode 自动感知文件变化，刷新文件树和已打开编辑器的外部变更状态
6. Git 状态面板自动刷新，用户直接查看变更摘要
7. 后续版本可在 Adapter / MCP 模式下增加上下文注入和 diff 预览

**场景二：并行对比两个智能体**

1. 同一任务复制给 Claude Code 和 Codex 两个会话
2. 左右两个 Agent 面板并列显示
3. 用户对比方案差异，挑选更好的或合并两者优点

**场景三：服务器上跑长任务**

1. SSH 到远程机器，启动 TuiCode
2. 在嵌入终端里启动一个长时间运行的训练任务
3. 同时与智能体对话，让它修改其他模块的代码
4. 切到 Git 面板提交另一组变更，全程不离开 TuiCode

---

## 4. 功能架构

### 4.1 模块概览

```
┌───────────────────────────────────────────────────────────┐
│                    TuiCode 应用层                        │
├──────────────┬──────────────┬─────────────┬───────────────┤
│  文件管理     │   编辑器      │  嵌入终端    │   Git 面板    │
│  • 文件树    │   • 多标签   │  • 多会话   │  • 状态/diff  │
│  • 搜索      │   • 语法高亮  │  • PTY     │  • 提交       │
│  • 预览      │   • 折叠     │  • 复制粘贴  │  • 分支       │
├──────────────┴──────────────┴─────────────┴───────────────┤
│              Agent 工作区（核心创新区）                       │
│  • 多 Agent PTY 会话   • 会话切换   • 工作区变化感知          │
│  • 后续扩展：结构化 Adapter / MCP / Diff 预览                │
├───────────────────────────────────────────────────────────┤
│              工作区状态聚合引擎                              │
│  • 当前编辑状态  • 文件变化  • Git 状态  • 终端活动          │
├───────────────────────────────────────────────────────────┤
│              深度集成扩展层（Phase 2+）                      │
│  Agent Adapter  │  MCP Bridge  │  Tool Approval  │ Context │
├───────────────────────────────────────────────────────────┤
│              基础设施层                                     │
│  窗口管理 │ 事件总线 │ 状态存储 │ 配置系统 │ 日志            │
├───────────────────────────────────────────────────────────┤
│              Textual + PTY + Rich                          │
└───────────────────────────────────────────────────────────┘
```

### 4.2 模块清单与优先级

| 模块 | 优先级 | MVP | 描述 |
|---|---|---|---|
| 窗口管理器 | P0 | ✓ | 多面板布局、拖动、缩放 |
| 文件树 | P0 | ✓ | 项目目录浏览 |
| 文件编辑器 | P0 | ✓ | 基于 Textual TextArea |
| 嵌入终端 | P0 | ✓ | PTY-based，至少一个会话 |
| Agent PTY 会话 | P0 | ✓ | 至少能在浮窗中运行 Claude Code |
| 工作区状态聚合器 | P0 | ✓ | 当前文件、选区、最近文件变化、Git 状态 |
| Git 状态面板 | P0 | ✓ | MVP 先显示 status 摘要，diff/commit 延后 |
| 多 Agent 会话 | P1 |   | 并行运行多个 PTY 智能体会话 |
| Agent Adapter 深度集成 | P2 |   | 结构化消息、上下文注入、工具桥接 |
| 命令面板 | P1 |   | 类 VSCode 的 Ctrl+Shift+P |
| 文件搜索 | P2 |   | ripgrep 集成 |
| 主题/配置 | P2 |   | 用户自定义 |
| LSP 集成 | P3 |   | 跳转/补全 |
| MCP 宿主 | P3 |   | 作为 MCP 客户端 |

---

## 5. 技术架构

### 5.1 分层视图

```
应用层    │ 业务功能模块（编辑器/终端/Agent 面板等）
─────────┼──────────────────────────────────────
服务层    │ 工作区状态聚合 │ 文件监视 │ Git 服务 │ Agent 深度集成
─────────┼──────────────────────────────────────
核心层    │ 窗口管理 │ 事件总线 │ 状态存储
─────────┼──────────────────────────────────────
基础层    │ Textual │ PTY │ Rich │ asyncio
```

### 5.2 进程模型

TuiCode 是单进程多协程架构：

- **主进程** —— Textual 事件循环
- **PTY 子进程** —— 每个嵌入式终端独立 PTY；智能体会话默认也是 PTY 子进程
- **后台协程** —— 文件监视、Git 状态轮询、工作区状态聚合
- **Agent 深度集成子进程**（Phase 2+）—— 仅在需要结构化 Adapter 时使用 stdio / MCP 通信

```
TuiCode Main Process (Textual asyncio loop)
├── PTY: bash session #1
├── PTY: bash session #2
├── PTY: claude-code session #1
├── PTY: codex session #1
├── Coroutine: file watcher (watchdog)
├── Coroutine: git status poller
└── Coroutine: workspace state aggregator
```

### 5.3 事件总线设计

所有模块通过统一事件总线通信，避免硬编码依赖：

```python
# 核心事件类型
class FileOpened(Event): path: Path
class FileModified(Event): path: Path, changes: Diff
class CursorMoved(Event): file: Path, line: int, col: int
class SelectionChanged(Event): file: Path, region: Region
class TerminalOutput(Event): session_id: str, text: str
class AgentMessage(Event): agent_id: str, content: str
class ToolCallRequested(Event): agent_id: str, tool: str, args: dict
class GitStatusChanged(Event): files: list[FileStatus]
```

模块订阅自己关心的事件，工作区状态聚合器订阅关键事件以维护全局状态。`ToolCallRequested` 保留给 Phase 2+ 的 Adapter / MCP 深度集成模式。

---

## 6. 关键子系统设计

### 6.1 窗口管理器（混合布局：浮窗工作区 + 固定工具栏）

TuiCode 采用**混合布局**，把信息架构区分为两类：

- **工作区（可浮动）** —— 用户主动"在里面工作"的对象：编辑器、智能体会话。它们有边界、有生命周期、需要灵活摆放和层叠对比。
- **工具区（固定）** —— 全局参考/辅助工具：文件树、Git、运行终端。它们位置稳定，用户随时能找到。

```
┌──────────────────────────────────────────────────┬──────────────┐
│  菜单栏  文件  编辑  视图  智能体  帮助              │ files│git│⋯  │
├──────────────────────────────────────────────────┤              │
│       [1·editor]  [2·codex]  [3·claude]          │              │
│         (窗口任务栏 — Alt+1/2/3 快切)              │  文件树 +    │
│                                                  │  Git 状态     │
│      ╭─editor──╮                                 │  (Tab 切换)   │
│      │ app.py  │     ╭─claude code──╮            │              │
│      │         │     │              │            │              │
│      ╰─────────╯     │  浮动工作区   │            │              │
│        ╭─codex──╮    │              │            │              │
│        │       │     ╰──────────────╯            │              │
│        ╰───────╯                                 │              │
├──────────────────────────────────────────────────┤              │
│  程序运行终端    [bash] [pytest] [dev] [+]        │              │
│  > _                                             │              │
└──────────────────────────────────────────────────┴──────────────┘
   状态栏:  ● 3 agents   Python 3.12   main ↑2   Ctrl+? 帮助
```

#### 6.1.1 浮窗工作区（左主区域）

- **承载内容**：代码编辑器实例、智能体终端会话
- **行为**：可拖动标题栏、可缩放（拖右下角）、可层叠、可最小化/最大化/关闭
- **窗口装饰**：macOS 风格红黄绿三色按钮（关闭/最小化/最大化）
- **焦点窗口边框高亮**（蓝色），其余灰色
- **窗口任务栏**：浮窗区顶部固定一行任务栏，显示所有打开的工作窗口名，`Alt+1/2/3...` 快速切换并置顶，解决浮窗叠在一起找不到的问题

#### 6.1.2 右侧工具栏（固定，可折叠）

- **Tab 切换**：files / git / search（后续可扩展）
- **角标提示**：当 Git 有未提交变更或搜索有新结果，Tab 角标显示数字（如 `git ●3`）
- **快捷键**：`Ctrl+E` 切换显示/隐藏整个右栏，腾出工作区空间
- **宽度**：默认 25-30 列，可拖动分隔线调整

#### 6.1.3 底部运行终端（固定，可折叠，多标签）

- **定位**：用于运行测试、跑服务、临时命令——区别于浮窗中的"智能体终端"
- **多标签**：支持多个 bash 会话标签（bash / pytest / dev / +），类似 VSCode 的终端栏
- **快捷键**：`Ctrl+B` 切换显示/隐藏，`Ctrl+Tab` 在标签间循环
- **高度**：默认 8-10 行，可拖动调整

#### 6.1.4 布局预设（一键切换工作模式）

预置三种常用布局，用 `Ctrl+1/2/3` 一键切换：

| 预设 | 快捷键 | 适用场景 |
|---|---|---|
| **编辑模式** | `Ctrl+1` | 编辑器浮窗最大化，智能体窗口收到角落 |
| **双 Agent 对比** | `Ctrl+2` | 两个智能体会话左右并列，编辑器收到下方 |
| **调试模式** | `Ctrl+3` | 编辑器 + 底部运行终端撑大，智能体窗口收起 |

用户也可以保存自定义布局：`Ctrl+Shift+S` 保存当前为命名布局，写入配置。

#### 6.1.5 全屏与拼贴模式

- `F11` —— 当前焦点浮窗全屏（撑满整个工作区）
- `Ctrl+\` —— **拼贴模式**：所有浮窗自动网格平铺（解决浮窗装饰浪费屏幕空间的问题）。再次按下回到浮窗模式。

#### 6.1.6 关键技术挑战

| 挑战 | 缓解 |
|---|---|
| 字符栅格限制窗口位置精度 | 接受约束，按字符格对齐；UI 设计上用圆角字符 `╭╮╰╯` 弥补视觉 |
| 浮窗装饰开销（每窗口 2 列 + 1 行） | 提供拼贴模式（`Ctrl+\`）一键消除装饰 |
| 浮窗叠在一起找不到 | 窗口任务栏 + `Alt+1/2/3` 快切 + 全窗口选择器（`` Ctrl+` ``） |
| 智能体输出被浮窗遮挡 | 焦点窗口自动置顶；用户可通过任务栏数字键快速切换 |
| 工具栏占用主区宽度 | `Ctrl+E` / `Ctrl+B` 随时折叠 |

### 6.2 编辑器

**MVP 直接使用 Textual 0.60+ 的 TextArea 组件**，它已经内置：
- 语法高亮（基于 tree-sitter）
- 行号、当前行高亮
- 多语言支持
- 复制粘贴

需要自己扩展的部分：
- 多标签页（一个 TextArea 实例 + 文件切换）
- 文件保存/外部变更检测
- Diff 预览模式（用于审查 Agent 的修改）
- 搜索/替换（Ctrl+F）

不在 MVP 范围内但要预留接口：
- LSP 协议接入（补全、跳转、诊断）
- 多光标
- 代码折叠

### 6.3 嵌入式终端

**核心技术：PTY + 终端模拟器状态机**

```
用户键盘输入
   ↓
Textual Widget (TerminalPane)
   ↓ (write bytes)
PTY Master
   ↓
PTY Slave ← → bash/zsh
                ↓ (output bytes)
PTY Master
   ↓
pyte VT100 Emulator (parse ANSI)
   ↓ (rendered cells)
TerminalPane 渲染
```

**关键技术选型：**

| 用途 | 库 |
|---|---|
| PTY 进程管理 | `ptyprocess` |
| ANSI 转义码解析 | `pyte` |
| 渲染优化 | 自定义 Textual Widget，复用 Rich Segment |

**特殊处理：**

1. 终端尺寸变化时通过 `TIOCSWINSZ` 通知子进程
2. 处理鼠标事件透传（让 vim 等程序也能用鼠标）
3. 支持 Ctrl+C 等控制字符的正确传递
4. 终端会话状态序列化（可选：保存/恢复会话）

### 6.4 Agent 集成层（PTY 主路径 + Adapter 扩展）

TuiCode 的默认集成方式是 **PTY 承载**。Claude Code、Codex、Aider 已经是完整的 CLI 产品，它们自带上下文管理、权限提示、工具执行和会话历史。MVP 不重复实现这些能力，而是让它们稳定运行在浮窗中，并通过文件监视和 Git 轮询感知它们对项目造成的结果。

这让 TuiCode 的第一性价值从"替代智能体交互"转为"提供智能体工作台"：

- 用户仍按熟悉方式使用 Claude Code / Codex
- TuiCode 管理多个智能体窗口、编辑器、文件树、运行终端和 Git 状态
- 智能体写文件或跑命令后的结果会自动反映到 UI
- 未来需要更深控制时，再启用 Adapter / MCP 扩展

#### 6.4.1 集成模式

| 模式 | 阶段 | 说明 |
|---|---|---|
| PTY 承载 | Phase 1 | 把智能体 CLI 当作完整 TUI/CLI 程序运行，TuiCode 观察工作区结果 |
| 结果观测 | Phase 1 | 文件 watcher + Git poller 发布 `FileModified` / `GitStatusChanged` |
| Adapter 深度集成 | Phase 2+ | 解析结构化输出、注入上下文、桥接工具调用 |
| MCP Bridge | Phase 3+ | 让外部智能体调用 TuiCode 的文件、Git、上下文能力 |

#### 6.4.2 适配器接口（Phase 2+）

```python
class AgentAdapter(Protocol):
    """深度集成模式下的 Agent 适配器。"""

    agent_id: str
    display_name: str
    capabilities: AgentCapabilities

    async def start_session(self, ctx: Context) -> Session: ...
    async def send_message(self, session: Session, content: str) -> None: ...
    async def stream_response(self, session: Session) -> AsyncIterator[Chunk]: ...
    async def handle_tool_call(self, call: ToolCall) -> ToolResult: ...
    async def stop_session(self, session: Session) -> None: ...
```

#### 6.4.3 内置集成策略

| 智能体 | MVP 通信方式 | 后续深度集成路径 |
|---|---|---|
| Claude Code | PTY | 可选 stdio / stream-json adapter |
| Codex CLI | PTY | 可选结构化 adapter |
| Aider | PTY | 可选命令桥接 |
| OpenAI / Anthropic 直连 | 不进 MVP | HTTP adapter |
| MCP Server | 不进 MVP | 标准 MCP 客户端 / 服务器 |

#### 6.4.4 工具调用审批（Phase 2+）

MVP 不在 TuiCode 内二次审批智能体工具调用。Claude Code 等智能体已有自己的权限提示和配置体系，重复接管会带来额外复杂度和协议耦合。后续如果进入 Adapter / MCP 模式，再提供统一审批流程：

```
Agent 提出工具调用
   ↓
Adapter 转换为标准 ToolCall
   ↓
ToolCallRequested 事件
   ↓
Agent 面板显示请求 + 内容预览
   ↓
用户选择：✓ 批准 / ✗ 拒绝 / ⓘ 修改
   ↓
执行 / 返回结果给 Agent
```

后续支持四种审批模式：
- **手动审批**（默认） —— 每次都要确认
- **自动批准（只读操作）** —— 读文件、运行查询命令自动通过
- **白名单自动批准** —— 用户预定义的命令模式自动通过
- **完全自动**（沙箱模式） —— 在 Docker 容器内随便玩

### 6.5 工作区状态聚合引擎

聚合器维护一个**实时更新的项目快照**。MVP 中它首先服务 UI 同步：文件树刷新、编辑器外部变更提示、Git 状态面板更新、状态栏摘要。Phase 2+ 再把这份状态作为 Adapter / MCP 的上下文来源。

#### 6.5.1 状态层级

```
L0 - 静态信息
     • 项目结构（目录树、文件类型分布）
     • Git 元数据（分支、远程、配置）
     • 项目配置（package.json/pom.xml 等）

L1 - 当前状态
     • 打开的文件列表 + 修改状态
     • 当前活动文件 + 光标位置 + 选区
     • 当前活动终端 + 最近命令历史

L2 - 短期活动
     • 最近 N 次编辑（diff 链）
     • 最近 M 条终端命令 + 输出
     • 最近的 Git 操作

L3 - 长期记忆（可选）
     • 项目文档索引（embedding）
     • 代码符号索引
     • 会话历史摘要
```

#### 6.5.2 MVP 聚合策略

MVP 不做智能意图推断和自动上下文打包，只做确定性状态同步：

| 输入 | 输出事件 / 状态 |
|---|---|
| 编辑器打开文件 | `FileOpened`，记录当前活动文件 |
| 编辑器选区变化 | `SelectionChanged`，记录当前选区 |
| watcher 发现文件变化 | `FileModified`，记录最近变更并刷新文件树 |
| git status 变化 | `GitStatusChanged`，刷新 Git Tab 和状态栏 |
| 终端输出 | `TerminalOutput`，记录近期终端活动 |

#### 6.5.3 后续上下文打包策略

Agent 发起对话时，聚合器根据**意图标签**决定打包哪些层级：

| 用户意图（推断） | 默认上下文 |
|---|---|
| "改这个函数" | 当前文件 + 选区 + 相关 import + 调用方 |
| "为什么这个测试挂了" | 测试文件 + 被测代码 + 最近终端错误 |
| "我项目里有什么" | L0 全量 + L1 当前文件 |
| "继续上次的事" | L2 短期记忆 + 最近 Agent 会话 |

意图推断初期可以靠简单规则 + 关键词匹配，后期可以引入小模型分类。

#### 6.5.4 增量更新

聚合器订阅事件总线，增量维护状态，避免每次都重新扫描项目：

```python
class ContextAggregator:
    def on_file_modified(self, e: FileModified):
        self.recent_diffs.append(e.changes)
        self.invalidate(e.path)

    def on_cursor_moved(self, e: CursorMoved):
        self.current_position = (e.file, e.line, e.col)

    def on_terminal_output(self, e: TerminalOutput):
        self.recent_commands.append(e)
        if self._looks_like_error(e.text):
            self.recent_errors.append(e)
```

### 6.6 Git 集成

Git 是开发流程核心，但 TuiCode 不重复造轮子，**直接复用 lazygit 思路**：通过 `GitPython` 或 `pygit2` 操作仓库，UI 借鉴 lazygit。

核心功能（MVP）：
- 状态摘要（当前分支、未提交文件数、简短 `git status --short`）
- 文件变化后自动刷新

延后功能：
- Diff 预览
- 暂存/取消暂存
- 提交（含 Agent 辅助生成提交信息）
- 分支切换
- Rebase 交互
- Cherry-pick
- 子模块管理

### 6.7 MCP 协议集成

中后期，TuiCode 既可以是 **MCP 客户端**（接入外部 MCP 服务），也可以暴露为 **MCP 服务器**（让其他智能体把 TuiCode 的能力当作工具用）。

作为 MCP 服务器暴露的工具：
- `read_file(path)` —— 读当前打开的文件
- `write_file(path, content)` —— 写文件（走审批）
- `run_command(cmd)` —— 在嵌入终端运行
- `git_status()`、`git_diff()` —— Git 操作
- `get_context()` —— 获取聚合上下文
- `show_diff_preview(diff)` —— 在编辑器侧显示 diff 预览

这一层将 TuiCode 变成一个**通用的 AI 编程工作站接口**，任何 MCP 兼容的智能体都能驾驭它。

---

## 7. 数据流示例

**场景：用户在 Claude Code PTY 浮窗中请求修改文件**

```
1. 用户在 Claude Code 浮窗中输入: "把 utils.py 的 parse_date 改成接受时区参数"
                                    ↓
2. Claude Code 按自己的 CLI 交互、权限和上下文机制工作
                                    ↓
3. Claude Code 修改 utils.py，或运行测试、git 命令
                                    ↓
4. 文件 watcher 检测到 utils.py 变化，发布 FileModified
                                    ↓
5. Git poller 检测到工作区状态变化，发布 GitStatusChanged
                                    ↓
6. 文件树刷新；如果 utils.py 已在编辑器打开，编辑器提示外部变更
                                    ↓
7. Git Tab 显示变更摘要，状态栏显示当前分支和未提交数量
```

整个过程里，TuiCode 不接管 Claude Code 的内部工具流，但能感知它对工作区造成的结果，用户视觉焦点始终在 TuiCode 内。

---

## 8. 扩展性机制

### 8.1 插件系统设计

不在 MVP 范围，但架构需要预留：

```python
class TuiCodePlugin(Protocol):
    name: str
    version: str

    def on_load(self, app: TuiCodeApp): ...
    def register_commands(self) -> list[Command]: ...
    def register_panels(self) -> list[Panel]: ...
    def register_adapters(self) -> list[AgentAdapter]: ...
```

插件可以：
- 注册新的命令（出现在命令面板）
- 注册新的面板类型
- 注册新的 Agent 适配器
- 订阅事件总线

### 8.2 配置系统

采用 TOML 配置文件，路径：`~/.config/tuicode/config.toml`

```toml
[ui]
theme = "github-dark"
font = "JetBrainsMono Nerd Font"

[layout]
default = "editor-centric"  # editor-centric / agent-centric / terminal-centric

[agents.claude-code]
enabled = true
binary = "claude"
mode = "pty"  # pty / adapter

[agents.codex]
enabled = true
binary = "codex"
mode = "pty"

[workspace_state]
max_recent_diffs = 20
max_recent_commands = 50
include_git_log = true
```

---

## 9. 分阶段实施路线

### Phase 1 — MVP（6-8 周，单人）

**目标：跑通观测型核心循环，证明智能体工作台价值**

- 混合布局窗口管理器
  - 浮窗工作区（编辑器 + 智能体会话浮窗，可拖动/缩放/层叠）
  - 右侧固定工具栏（files Tab + Git 状态摘要）
  - 底部固定运行终端（单 bash 标签，多标签延后）
  - 窗口任务栏 + `Alt+1/2/3` 快切
  - 至少一种布局预设（编辑模式 `Ctrl+1`）
- 文件树（只读浏览）
- 编辑器（基于 Textual TextArea，单文件，保存/打开，作为浮窗）
- 嵌入终端：底部一个 bash + 浮窗中一个智能体终端
- Claude Code PTY 会话：在智能体浮窗中运行完整 Claude Code CLI
- 文件变化感知：watcher 检测智能体或外部工具写入
- Git 状态同步：右侧 Git Tab 显示当前工作区摘要
- 极简工作区状态聚合（当前文件 + 选区 + 最近文件变化 + Git 状态）

**可交付**：在 TuiCode 中运行 Claude Code 修改一个 Python 项目；Claude 修改文件后，文件树、编辑器外部变更提示和 Git 状态能自动更新。

### Phase 2 — 多智能体 + Git + 布局打磨（4-6 周）

- 多 Agent PTY 会话管理
- Git 状态面板增强（diff / stage / commit）
- 底部运行终端多标签
- 完整布局预设（`Ctrl+1/2/3`：编辑/双 Agent 对比/调试）
- 拼贴模式（`Ctrl+\`）
- 工具栏折叠（`Ctrl+E` / `Ctrl+B`）
- 文件树多选 + 操作
- 命令面板（Ctrl+Shift+P）
- Agent Adapter 协议进入可选深度集成

### Phase 3 — 上下文引擎 + 体验打磨（6-8 周）

- 完整的多层级工作区状态 / 上下文聚合器
- 意图推断 + 智能上下文打包（仅用于深度集成模式）
- 工具调用审批 UI（Adapter / MCP 模式）
- 多标签编辑器
- 文件搜索（ripgrep）
- 主题系统
- 配置文件

### Phase 4 — 高级特性（持续）

- LSP 协议接入
- 插件系统
- MCP 服务器/客户端双向
- 会话历史持久化
- 多人协作（远程 Agent 会话共享）

---

## 10. 技术选型

| 层次 | 选型 | 理由 |
|---|---|---|
| 语言 | Python 3.11+ | Textual 生态、AI 工具链最完整 |
| TUI 框架 | Textual 0.60+ | 唯一支持鼠标 + CSS 布局的成熟 Python TUI |
| 终端模拟 | `pyte` + `ptyprocess` | Python 生态最成熟组合 |
| 文件监视 | `watchdog` | 跨平台 |
| Git | `pygit2` | 比 GitPython 快，纯 C 绑定 |
| 异步 | `asyncio`（Textual 自带） | 与 Textual 事件循环统一 |
| 配置 | `tomllib` (stdlib) + `pydantic` | 解析 + 校验 |
| 子进程通信 | `asyncio.subprocess` | 流式 stdio |
| 打包分发 | `pipx` / `uv tool` | 单命令安装 |

**为什么不用 Rust？** 性能不是瓶颈（瓶颈在智能体网络往返），Python 的 AI 生态成熟度压倒性优势，社区贡献门槛低。如果 Phase 4 发现性能问题，可以把热点模块（编辑器渲染、文件索引）用 Rust 重写并通过 PyO3 嵌入。

---

## 11. 风险与权衡

### 11.1 主要风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| Textual TextArea 在大文件下性能差 | 编辑体验降级 | 限制单文件 1MB 以下，超过提示用外部编辑器；长期可考虑 virtualized 渲染 |
| 嵌入终端兼容性问题（特别是 vim/htop） | 终端不可用 | pyte 已经覆盖大部分场景，剩余靠测试 + 用户反馈逐个修 |
| Windows 终端 PTY 处理复杂 | Windows 用户体验差 | MVP 优先 Linux/macOS/WSL，Windows 原生延后 |
| 智能体接口频繁变化 | 适配器需要持续维护 | 适配器层薄、抽象稳定，迁移成本可控 |
| 上下文打包过大触发 token 限制 | Agent 失败 | 聚合器有 token 预算控制，按优先级裁剪 |

### 11.2 关键权衡

**TUI vs Electron**

放弃 Electron 是有代价的：渲染能力上限低、UI 设计自由度小。但收益巨大：内存占用 1/10、启动快 10 倍、SSH 远程原生可用、与开发者命令行工作流无缝。**对目标用户而言，这是优势不是限制。**

**Python vs Rust/Go**

Python 性能上限低，但 TuiCode 的瓶颈是网络 IO 和终端 IO，而非 CPU。选 Python 是为了：1）AI 生态最成熟；2）社区贡献门槛低；3）作者熟悉。

**混合布局 vs 纯分割面板 vs 纯自由浮窗**

经过反复推演，最终选择**混合布局**而非任一极端方案：

- **纯分割面板（tmux 风格）** —— 屏幕利用率最高，但对智能体会话不友好：智能体窗口数量在工作中会动态变化（开新会话、关旧会话），分割面板的整体布局会被频繁打破。
- **纯自由浮窗（早期桌面 GUI 风格）** —— 灵活，但全局工具（文件树、Git）放在浮窗里也要拖动管理，对用户是噪音。
- **混合布局** —— **工作单元浮窗化**（编辑器、智能体会话——它们是有界对象，会动态增减），**全局工具固定化**（文件树、Git、运行终端——它们位置稳定才方便随时调用）。这个划分既保留浮窗的灵活，又避免全自由带来的混乱。

代价是实现复杂度更高（要同时维护浮窗系统和固定栅格系统），但通过引入**拼贴模式**（`Ctrl+\`）和**布局预设**（`Ctrl+1/2/3`），可以让用户在不同场景下获得近似纯分割面板或纯浮窗的体验。

---

## 12. 差异化竞争位势

### 12.1 横向对比

| 维度 | VSCode | Cursor | Aider | Claude Code | Helix | **TuiCode** |
|---|---|---|---|---|---|---|
| 终端原生 | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ |
| GUI 级编辑体验 | ✓✓ | ✓✓ | ✗ | ✗ | ✓ | ✓ |
| 文件管理器 | ✓✓ | ✓✓ | ✗ | ✗ | △ | ✓ |
| 嵌入式终端 | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ |
| 多智能体支持 | △（插件）| ✗ | ✗ | ✗ | ✗ | **✓✓** |
| 智能体上下文聚合 | △ | ✓ | ✓ | ✓ | ✗ | **✓✓** |
| SSH 远程使用 | △ | ✗ | ✓ | ✓ | ✓ | ✓ |
| 资源占用 | 高 | 高 | 低 | 低 | 极低 | 低 |

### 12.2 不可替代的位置

TuiCode 占据的位置是：**"我想在终端里用 AI 编程，但希望有 IDE 级的文件 / 编辑 / Git 体验，并且能并行管理多个智能体"**。

目前没有任何产品同时满足这三个条件。VSCode/Cursor 不是终端原生；Aider/Claude Code 是 CLI，没有 IDE 体验；Helix 没有智能体集成。

### 12.3 商业化路径（远期可选）

不必急于商业化，但架构上可以为未来留空间：

- **开源核心** —— 编辑器、文件管理、终端、PTY Agent 会话，永久免费
- **专业版** —— 高级 Agent 协议（多智能体协作、智能体投票）、企业级配置管理、团队上下文共享
- **托管服务** —— 云端会话同步、跨设备状态恢复
- **企业版** —— 私有部署、SSO、审计日志

---

## 13. 下一步行动

### 13.1 立即行动项

1. **文件 watcher + Git poller**（2 天）—— 检测智能体或外部工具造成的工作区变化
2. **Git Tab 最小实现**（1 天）—— 显示当前分支和 `git status --short` 摘要
3. **编辑器外部变更提示**（1 天）—— 打开的文件被外部修改后提示用户刷新
4. **工作区状态聚合器**（1 天）—— 聚合当前文件、选区、最近变更和 Git 状态

### 13.2 决策待定项

- 是否一开始就引入插件系统的接口预留（建议：是，但只定义 Protocol，不实现）
- 配置文件用 TOML 还是 YAML（建议：TOML，与 Python 生态趋势一致）
- 是否做项目模板系统（建议：暂不，等用户反馈）
- 国际化优先级（建议：MVP 只支持中英文）

### 13.3 开放问题

- 嵌入式终端对 GPU 加速的终端协议（Kitty、WezTerm）兼容性如何？
- 是否需要支持远程模式（TuiCode 服务端 + 瘦客户端）？
- 是否对接 OpenAI Realtime API 之类的语音模态？
- 工作区状态聚合器后续是否需要升级为带向量索引的上下文引擎？

---

## 附录 A：架构决策记录（ADR）模板

每个重大架构决策应该记录为一份 ADR：

```
# ADR-XXX: <决策标题>

## 背景
<为什么需要做这个决策>

## 选项
1. 方案 A
2. 方案 B

## 决策
<选了什么，为什么>

## 影响
<带来什么变化、放弃了什么>
```

## 附录 B：术语表

- **Adapter** —— 智能体适配器，实现 AgentAdapter 协议的模块
- **Session** —— 一次智能体会话，有独立上下文和历史
- **Context Bundle** —— 聚合器打包给 Agent 的上下文单元
- **Tool Call** —— 智能体请求执行的工具操作（读文件、跑命令等）
- **Pane** —— 分割面板中的一格
- **PTY** —— Pseudo Terminal，伪终端

---

*文档版本：v0.2 · 混合布局更新 · 待评审*
