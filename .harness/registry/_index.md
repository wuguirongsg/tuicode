# 决策索引

> **Agent 使用规则**：
> - Session 开始时：只读最近 5 条，了解近况
> - Session 结束时：在最前面追加新条目（不是末尾）
> - 不要读完整历史，用条目里的文件链接按需查阅

格式：`[日期 时间] [类型] 一句话摘要 → 详情文件`

类型说明：
- `DONE` 完成功能 · `WIP` 进行中 · `BLOCKED` 阻塞
- `DECISION` 架构决策 · `CONSTRAINT` 新发现约束 · `FIX` 修复问题
- `DISCOVER` 需求探索 · `VERIFY` 验证 · `RELEASE` 发布 · `RETRO` 复盘

---

<!-- 新条目追加到这里（上方） -->

[2026-05-26 19:00] DONE feat-003 浮窗管理器（FloatWindow 基类 + FloatWorkspace），16 测试通过，视觉效果待人工确认 → sessions/2026-05-26-1900.md

[2026-05-26 18:00] DECISION AgentDeck 项目 harness 初始化完成，确认 Phase 1 包含 12 条 feat → decisions/init.md
