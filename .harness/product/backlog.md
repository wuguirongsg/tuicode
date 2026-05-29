# 产品 Backlog

> 需求池、产品方向、已知约束 — 集中在这一个文件。
> Sprint 规划时从"待评估"区取材；发现约束立即追加到"已知约束"区。

---

## 产品方向

> 所有决策的北极星。与此冲突的功能不做。

**为谁**：使用 Claude Code / Codex / Aider 等终端编程智能体的开发者（重度智能体用户 / SSH 远程开发者 / AI 编程探索者）。

**解决什么**：智能体在终端里能写代码，但文件查看、外部变更感知、Git 状态、运行终端和多个智能体会话分散在不同工具中——开发者被迫在 CLI 智能体、编辑器、Git 工具和终端之间不断切上下文。

**一句话定位**：为终端编程智能体设计的统一 TUI 工作台，把"编辑器 + 文件 + 多终端 + Git + 多智能体会话 + 工作区状态同步"整合为一致体验（见 [docs/agentdeck_architecture.md](../../docs/agentdeck_architecture.md) §1）。

**成功标准**：
- 目标用户在做日常 AI 编程任务时全程不离开 AgentDeck（编辑、查 diff、跑命令、与多个智能体对话、提交 Git）
- Claude Code / Codex / Aider 在 PTY 浮窗中工作后，AgentDeck 能自动感知文件和 Git 状态变化
- 能在 SSH 远程机器上原生使用，不依赖 GUI
- 同一任务可以并行交给两个智能体对比方案（场景见架构文档 §3.2）

**明确不做**（见架构文档 §1.2）：
- 不复刻 VSCode（不做插件市场、不做调试器、不做完整 IDE 功能）
- 不替代终端模拟器（运行在 Alacritty/iTerm2 之上）
- 不做自己的智能体（只做宿主和适配）
- 不替代 tmux/Zellij（定位更高层）
- 不引入 GUI / Web / Electron（100% TUI）

---

## 待评估需求

> 格式：`- [日期] [来源] 描述`
> 来源：自己 / 用户反馈 / 竞品观察 / 技术债 / [VERIFY] / [RETRO] / [设计评审]

<!-- 新需求追加到这里 -->

- [2026-05-29] [用户] 文件管理器增强 — 文件树从只读升级为可操作：新建文件/文件夹、删除、重命名、复制路径等常用操作（已排入 Phase 2B feat-021）
- [2026-05-29] [设计评审] [P1] 功能发现 — 底栏快捷键提示补 `^T 智能体` `^⇧P 命令`（status.shortcuts 当前只有退出/终端，最高频入口未暴露）；空状态 hint（i18n.py workspace.hint）加可见启动引导，告诉新用户「怎么启动」而非只说「会显示在这里」
- [2026-05-29] [设计评审] [P1] diff 体验 — diff 预览标注对比基准（工作区/暂存区，补 grounding）；同一文件 diff 窗口去重置顶（app.py:159 on_right_panel_diff_requested 缺去重，对照编辑器已有去重）；支持从 diff 直接 stage
- [2026-05-29] [设计评审] [P2] 智能体完成/待审批通知 — 智能体结束运行或停在权限提示时，即使窗口无焦点也能感知（多智能体并行场景尤其重要）
- [2026-05-29] [设计评审] [P2] 启动器环境感知 — NewAgentModal 标灰/提示未安装的智能体命令，提前预防选中后 PTY 静默失败
- [2026-05-29] [设计评审] [备注] 命令面板未覆盖 feat-018 验收承诺的「打开 diff / 切换右栏 / 切换底栏」命令（app.py:_build_palette_commands 实缺这三项，feat-018 已标 passes=true，未擅自重开，仅记录待后续补齐）

---

## 已规划 / 已否决 / 变更

> 已进入 Sprint 的需求注明 Sprint；取消/调整的功能也记在这里。

- [2026-05-26] Sprint-1 — Phase 1 MVP 全 12 条 feat（见 features.json）
- [2026-05-28] Phase 1 方向调整 — 从“Adapter 接管工具调用 + 审批”改为“PTY 智能体 + 文件/Git 变化感知”；详见 `.harness/registry/decisions/2026-05-28-observability-first.md`
- [2026-05-28] Phase 2A — Agent 工作流打磨：Phase 1 验证、Git diff、stage/commit、布局预设、多 Agent 启动器、命令面板（feat-013 至 feat-018）
- [2026-05-29] Phase 2B — 可见性债务 + 文件管理器：智能体运行状态可见（feat-019，源自设计评审 P0）、右栏 Tab 真切换（feat-020，源自设计评审 P0）、文件树可操作化（feat-021，源自用户反馈）

---

## 已知约束与坑

> 发现新约束立即追加。不要删历史。

### 架构约束

**来源：架构文档 §2 核心原则 + §10 技术选型 + §11.2 关键权衡**

- **智能体是一等公民**：不能把 AI 当 IDE 插件做（不能浮窗化、不能侧栏化退化），编辑器/文件树/终端的设计目标是"让智能体更好工作"。
- **PTY 优先，Adapter 后置**：MVP 默认把成熟 CLI 智能体作为完整 PTY 会话承载；`AgentAdapter` 是 Phase 2+ 深度集成扩展点，不阻塞主路径。
- **混合布局不可退化**：工作单元（编辑器/智能体会话）必须浮窗化，全局工具（文件树/Git/运行终端）必须固定栅格化。不允许改为"纯分割面板"或"纯自由浮窗"——这是经过权衡的核心判断（§11.2）。
- **100% TUI**：禁止引入 GUI / Web / Electron / 浏览器渲染。
- **技术栈固定**：Python 3.11+ + Textual 0.60+。MVP 不允许换语言。性能瓶颈出现时才考虑用 Rust 通过 PyO3 嵌入热点模块。
- **事件总线唯一通信通道**：模块之间禁止硬编码相互依赖，都走事件总线（`FileOpened`、`CursorMoved`、`AgentMessage`、`ToolCallRequested` 等）。
- **工作区状态聚合器是核心引擎**：MVP 聚合当前文件、选区、最近文件变化和 Git 状态，先服务 UI 同步；后续 Adapter / MCP 必须通过聚合器拿上下文。
- **MVP 编辑器直接用 Textual TextArea**：不要自研编辑器内核；LSP / 多光标 / 折叠等留接口、不实现。
- **工具调用审批后置**：MVP 不二次接管 Claude Code 等 CLI 智能体的权限提示；`ToolCallRequested` + 审批 UI 只用于 Phase 2+ Adapter / MCP 深度集成模式。

### 已知坑

**来源：架构文档 §11.1 + §6.3**

- **Textual TextArea 大文件性能差**：单文件超过 1MB 要提示用外部编辑器，不要硬扛。
- **嵌入终端对 vim/htop 等全屏 TUI 程序兼容性**：pyte 覆盖大部分场景但有边界，遇到具体程序失效要单独排查，不要假设 pyte 完美。
- **Windows 原生 PTY 复杂**：MVP 优先 Linux/macOS/WSL，Windows 原生延后；不要为 Windows 兼容性堵塞主路径。
- **智能体 CLI 接口变化频繁**：Adapter 层要薄、要抽象稳定，迁移成本可控；不要在宿主层依赖具体智能体的输出格式。
- **上下文打包过大触发 token 限制**：聚合器必须有 token 预算控制，按优先级裁剪；不要无脑塞全部上下文。
- **深度接管智能体工具流成本高**：Claude Code 等 CLI 自带权限和工具体系，MVP 不应重复实现；先通过 watcher/Git poller 观测结果。
- **PTY 控制字符**：Ctrl+C 等控制字符必须正确透传给子进程，鼠标事件也要透传（vim 才能用鼠标）。
- **终端尺寸变化**：必须用 `TIOCSWINSZ` 通知子进程，否则 TUI 程序渲染会错位。

### Session 中新发现

（格式：`[YYYY-MM-DD] 描述 — 原因`）

[2026-05-26] Textual `layers` 仅控制 z 渲染顺序，`offset` 始终相对 widget 在垂直布局中的堆叠基准位置 —— 无原生 absolute 定位支持。浮窗真正自由定位需用 stack_y 补偿（当前方案）或将窗口挂载到 Screen 而非子容器（备选）。

[2026-05-28] Textual 8.x 不原生支持传统下拉菜单 — vertical layout 强制子 widget 占满父容器宽度；layer/layers 机制在完整 App 的 CSS 层叠环境中行为不稳定（孤立脚本有效，完整 App 中 width 约束被覆盖）。结论：菜单栏保持静态占位，后续用命令面板（Ctrl+Shift+P，全屏模态）替代所有菜单入口，规划至 Phase 2。

[2026-05-28] Textual TextArea 语法高亮依赖 `textual[syntax]` 的 tree-sitter extras；启用后只能传内置支持的语言名，未内置的 `diff` / `typescript` 等必须回退纯文本或单独注册 parser/query，否则会在打开 TextArea 时抛错。
