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

[2026-05-27 00:00] DONE feat-005 文件树（DirectoryTree）+ feat-006 编辑器浮窗（EditorWindow + ConfirmCloseModal），feat/003 合并到 master，80 测试全通过 → sessions/2026-05-27-0000.md

[2026-05-26 22:30] DONE feat-003 收尾（拖拽边界/标题栏置顶/ResizeHandle）+ feat-004 窗口任务栏全部完成，28 测试通过，待视觉确认后 merge → sessions/2026-05-26-2200.md

[2026-05-26 22:00] DESIGN 拖拽边界限制方案确认 + 最小化到任务栏设计：建议最小化合并进 feat-004 任务栏统一实现，待用户确认后执行

[2026-05-26 21:30] FIX feat-003 修复置顶后窗口位置跳变：_bring_to_top 重排后重算所有窗口 _win_y/_stack_y，保持视觉位置不变，16 测试通过

[2026-05-26 21:00] FIX feat-003 收尾：标题栏点击置顶（TitleBar 调 _bring_to_top）+ ResizeHandle 扩宽至 3 格，16 测试通过，待用户视觉确认后 merge

[2026-05-26 20:00] FIX feat-003 浮窗定位+拖动修复：stack_y 补偿初始坐标、capture_mouse+delta 提升流畅度、WinButton 防误触、z 提升点击置顶，视觉待确认

[2026-05-26 19:30] CONSTRAINT Textual layers 仅控制 z 渲染顺序，offset 始终相对垂直堆叠基准，无原生 absolute 定位——需 stack_y 补偿或 Screen 挂载绕过

[2026-05-26 19:30] FIX 为 feat-003 视觉验证添加临时 Ctrl+T 快捷键（feat/003 分支），待用户确认效果后 merge 或换方案

[2026-05-26 19:00] DONE feat-003 浮窗管理器（FloatWindow 基类 + FloatWorkspace），16 测试通过，视觉效果待人工确认 → sessions/2026-05-26-1900.md

[2026-05-26 18:00] DECISION AgentDeck 项目 harness 初始化完成，确认 Phase 1 包含 12 条 feat → decisions/init.md
