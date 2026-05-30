# 初始化记录

**日期**：2026-05-26
**执行**：Harness 初始化 Agent（Claude Opus 4.7）

---

## 项目概况

- **项目名**：TuiCode（仓库目录名 `tuicode` 是早期占位，以设计文档为准）
- **定位**：为终端编程智能体（Claude Code / Codex / Aider）设计的统一 TUI 工作台
- **技术栈**：Python 3.11+ + Textual 0.60+ + pyte + ptyprocess + pygit2 + watchdog
- **目录现状**：
  - `docs/tuicode_architecture.md` — 架构设计文档 v0.2（权威）
  - `demo/tui_demo.py` — Phase 0 技术 spike（PTY + pyte + Textual 集成验证）
  - `src/` 尚不存在，MVP 在 `src/tuicode/` 下新建
  - `.harness/` 模板已就位
- **当前阶段**：Phase 1 MVP 启动

---

## 确认的架构约束（Q2）

来源：架构文档 §2 核心原则 + §10 技术选型 + §11.2 关键权衡。完整列表见 [backlog.md](../../product/backlog.md) "已知约束与坑" 区。要点：

1. **智能体是一等公民** — 不能把 AI 退化为 IDE 插件式的浮窗/侧栏
2. **协议驱动** — 新增智能体必须实现 `AgentAdapter` Protocol，禁止在宿主代码硬编码具体智能体行为
3. **混合布局不可退化** — 工作单元浮窗化、全局工具固定栅格化，不允许改为纯分割面板或纯自由浮窗
4. **100% TUI** — 禁止 GUI / Web / Electron
5. **Python + Textual 技术栈固定** — MVP 不换语言
6. **事件总线唯一通信通道** — 模块间禁止硬编码相互依赖
7. **上下文聚合器是唯一数据源** — Adapter 必须通过聚合器拿上下文
8. **工具调用必须走审批** — 智能体的写文件/跑命令/Git 一律发 `ToolCallRequested` 事件
9. **MVP 编辑器直接用 Textual TextArea** — 不自研编辑器内核

---

## 已知风险和坑（Q3）

来源：架构文档 §11.1：

1. Textual TextArea 大文件性能差（>1MB 提示用外部编辑器）
2. pyte 对 vim/htop 等全屏 TUI 程序有兼容边界
3. Windows 原生 PTY 复杂，MVP 只支持 Linux/macOS/WSL
4. 智能体 CLI 接口频繁变化，Adapter 要薄、抽象稳定
5. 上下文打包要有 token 预算并按优先级裁剪
6. PTY 必须透传 Ctrl+C 等控制字符与鼠标事件
7. 终端尺寸变化要 `TIOCSWINSZ` 通知子进程

---

## 第一阶段范围（Q4）

Phase 1 MVP — 12 条 feat（粒度按用户确认细化），完整定义见 [features.json](../../state/features.json)：

| ID | 标题 |
|----|------|
| feat-001 | 应用骨架与混合布局容器 |
| feat-002 | 事件总线（8 种核心事件） |
| feat-003 | 浮窗管理器（拖动/缩放/最大化/关闭） |
| feat-004 | 窗口任务栏与 Alt+1/2/3 快切 |
| feat-005 | 文件树（右栏 files Tab） |
| feat-006 | 编辑器浮窗（基于 TextArea） |
| feat-007 | 底部 bash 终端（PTY + pyte） |
| feat-008 | 智能体终端浮窗（通用 PTY 浮窗） |
| feat-009 | AgentAdapter Protocol |
| feat-010 | Claude Code 适配器 |
| feat-011 | 极简上下文聚合器 |
| feat-012 | 工具调用审批 UI |

**依赖关系骨架**：
- feat-001 / feat-002 / feat-009 是地基（无依赖）
- 浮窗系（003 → 004、006、008）建立在 001 上
- 工作流闭环：010 = 008 + 009 + 002；012 = 010 + 006

**完成判据**：在 TuiCode 中用 Claude Code 编辑一个 Python 项目，跑通 read / write / run_command + 审批全流程。

---

## 未问用户的事项

按 HARNESS_SETUP 规则与用户指示"设计文档已覆盖的不再问"，以下问题用设计文档作答，未打断用户：

- Q0 / Q0.5 / Q0.75：架构文档 §1.1–§1.3 + §3（产品定位 / 用户画像 / 明确不做）
- Q1：架构文档 §9.1 Phase 1 目标
- Q2：架构文档 §2 + §10 + §11.2
- Q3：架构文档 §11.1

用户实际回答的两件事（设计文档未明说）：

- `demo/tui_demo.py` 处置：保留作技术 spike 参考，MVP 在 `src/tuicode/` 新建
- features 粒度：选"更细颗粒（约 10-12 条）"
