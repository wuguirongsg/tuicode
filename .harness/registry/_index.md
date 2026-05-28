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

[2026-05-28 16:04] DONE feat-013 Phase 1 全链路验证与 pyte 环境修复：新增 App 级观测链路测试，112 测试全通过 → sessions/2026-05-28-1604.md

[2026-05-28 15:57] PLAN Phase 2A Agent 工作流打磨：新增 feat-013 至 feat-018，目标从观测变化推进到审查 diff、布局切换、多 Agent 会话和 Git 收尾

[2026-05-28] CONSTRAINT 菜单下拉 spike 结论：Textual 8.x vertical layout 不支持固定宽度子 widget；改用命令面板方案（Phase 2）

[2026-05-28] DISCOVER 确认菜单栏未排入任何阶段计划；命令面板（Ctrl+Shift+P）规划在 Phase 2

[2026-05-28] DONE 浮窗激活跑马灯动画 — 四侧彩虹渐变（上青右紫下粉左绿），1.3s 走完一圈，99 测试无回归

[2026-05-28] DONE feat/008-agent-terminal 合并到 master

[2026-05-27 10:30] DONE feat-008 智能体终端浮窗（AgentTerminalWindow），Ctrl+Shift+T 打开，10 测试通过，99 总测试无回归 → sessions/2026-05-27-1030.md

[2026-05-27 10:00] FIX 机器人去掉最下排 Braille 行，面板高度 6→5，89 测试通过

[2026-05-27 09:45] FIX 机器人头部收窄(34→16px) + 眼睛改 2×2 块 + 嘴巴居中 + 颈部改6条腿，89 测试通过

[2026-05-27 09:15] DONE 右栏 Braille 像素机器人：_to_braille 编码器 + 6 状态 9 帧 MascotPanel + 状态栏简化，89 测试通过

[2026-05-27 08:30] DONE 状态栏吉祥物机器人：6 状态动画 + 打开文件反馈，89 测试通过

[2026-05-27 07:45] FIX 浮窗边框 heavy → round，细线圆角更清爽

[2026-05-27 07:30] FIX border-title 按钮检测偏左一格：heavy 边框格式 ┏━ title，标题起点 +3 非 +2，检测区扩至 {2,3}/{4,5}/{6,7}

[2026-05-27 07:00] DONE 赛博朋克 UI：霓虹 border-title 浮窗 + ASCII 背景 + 淡入动画 + cyberpunk 主题，89 测试通过 → sessions/2026-05-27-0700.md

[2026-05-27 06:00] DONE 改名 AgentDeck → TuiCode + Crush 风格 UI 重设计 + i18n 中英双语支持，91 测试通过，3 commits

[2026-05-27 05:00] FIX 滚动 KeyError + 滚动条：scrollback sparse dict 用 .get() 兜底，render_line 最右列 overlay █/│ 滚动条，91 测试通过

[2026-05-27 04:00] FIX PtyTerminal 滚动/调整/光标三修：margins=None AttributeError、_ResizeHandle 拖拽、content_size 对齐，91 测试全绿

[2026-05-27 03:00] FIX PtyTerminal 焦点 + Ctrl+C 双修：can_focus 大小写(Textual 8.x)、slave PTY 控制终端未绑定导致信号不投递

[2026-05-27 02:00] FIX PtyTerminal 焦点修复：on_click 获焦 + Ctrl+` 快捷键 + 聚焦蓝边框高亮

[2026-05-27 01:30] DONE feat-007 底部 bash 终端（PtyTerminal + TerminalStrip），PTY+pyte+add_reader，11 测试通过，91 总测试无回归

[2026-05-27 00:30] FIX 浮窗边框回退直角：round 圆角字符与标题栏对齐偏差，恢复 solid

[2026-05-27 00:15] FIX 浮窗边框改为圆角（╭ ╮ ╰ ╯），border: solid → round，焦点高亮同步更新

[2026-05-28 01:45] DONE Phase 1 剩余 feat-010/011/012 全部完成，观测型智能体工作台闭环达成；相关测试通过，全量测试待 pyte 环境 → sessions/2026-05-28-0145.md

[2026-05-28 01:30] DONE feat-012 Git 状态面板与自动刷新：GitStatusPoller 发布 GitStatusChanged，右栏显示分支和 status --short，37 个相关测试通过

[2026-05-28 01:00] DONE feat-011 工作区状态聚合器：维护当前文件、选区、最近 10 条文件变化和 Git 摘要，23 个相关测试通过

[2026-05-28 00:30] DONE feat-010 文件变化感知：WorkspaceWatcher 发布 FileModified，文件树 reload，编辑器外部变更标题标记，28 个相关测试通过

[2026-05-28 00:00] DECISION Phase 1 从 Adapter 接管工具调用调整为 PTY 智能体 + 文件/Git 变化感知，feat-010/012 建议推迟到 Phase 2/3 → decisions/2026-05-28-observability-first.md

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
