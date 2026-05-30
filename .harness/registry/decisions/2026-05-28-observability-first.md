# ADR: Phase 1 改为观测型智能体工作台

**日期**：2026-05-28
**状态**：Accepted

## 背景

Phase 1 原计划通过 Claude Code Adapter、上下文注入和工具调用审批证明深度集成可行。但实际讨论后确认：Claude Code 这类成熟 CLI 智能体已经拥有完整的交互、上下文和权限体系。MVP 如果强行接管工具调用，会带来协议耦合、维护成本和重复审批体验，且不符合当前最高价值路径。

用户当前最需要的是：Claude Code 在 TuiCode 的 PTY 浮窗中工作后，TuiCode 能知道工作区发生了什么，自动刷新文件树、编辑器状态和 Git 状态。

## 决策

Phase 1 主路径从“控制型深度集成”调整为“观测型工作台”：

- 智能体默认通过 PTY 浮窗运行，保持自身 CLI 交互和权限体系。
- TuiCode 通过文件 watcher 和 Git status poller 感知智能体造成的工作区变化。
- 工作区状态聚合器记录当前文件、选区、最近文件变化和 Git 状态，先服务 UI 同步。
- AgentAdapter、自动上下文注入、工具调用审批 UI 推迟到 Phase 2/3，作为可选深度集成能力。

## 影响

Phase 1 交付标准调整为：

> 在 TuiCode 中运行 Claude Code 修改一个 Python 项目；Claude 修改文件后，文件树、编辑器外部变更提示和 Git 状态能自动更新。

这保留了“智能体是一等公民”和“混合布局”的产品方向，但避免把 MVP 绑定到某个智能体的内部协议。

## 后续

- 更新 `docs/tuicode_architecture.md` Phase 1/2/3 路线。
- 更新 backlog 和 current sprint 目标。
- `features.json` 当前规则禁止修改 description，需由用户确认后手动调整或新增替代 feat 条目。
