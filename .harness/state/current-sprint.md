# 当前阶段目标

**阶段**：Phase 2A — Agent 工作流打磨
**目标**：把 Phase 1 的“观测变化”推进到“审查并收尾”——用户在 TuiCode 中运行一个或多个 PTY 智能体修改代码后，可快速验证 diff、切换合适布局，并在 Git 面板完成 stage/commit 的最小闭环。
**完成标准**：features.json 中 feat-013 至 feat-018 全部 passes = true
**默认 Session 阶段**：BUILD
**当前版本**：（发布后填入）

---

## 阶段历史

| 阶段 | 完成时间 | 主要产出 |
|------|----------|----------|
| Phase 1 — MVP | 2026-05-28（已完成）| 观测型核心循环：PTY 智能体、文件变化感知、工作区状态聚合、Git 状态自动刷新 |
| Phase 0 — Spike | 2026-05（已完成）| `demo/tui_demo.py` 验证 PTY + pyte + Textual 集成可行性 |
