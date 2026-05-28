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

[2026-05-28 20:30] CONSTRAINT 性能卡顿非本次改动引起：PTY _on_pty_readable 每次读取都调 refresh()，Agent 高频输出时是主要压力源；跑马灯改动渲染量不变

[2026-05-28 20:10] FIX 跑马灯效果改为只在新窗口打开时播放：on_mount 加 _start_marquee()，移除 on_focus/on_descendant_focus 里的触发逻辑

[2026-05-28 19:00] CONSTRAINT iTerm2 中文 IME 问题搁置：Paste 事件未到达 PtyTerminal（日志确认），后续从 Textual _app.py Paste 分发逻辑入手排查；Terminal.app 中文输入正常可用

[2026-05-28 18:45] CONSTRAINT iTerm2 中文 IME 输入已知问题：Textual 收到 Space 但 IME 组合字符（Paste 事件）完全未到达 PtyTerminal，原因待查（Textual 内部路由 or iTerm2 未送达），暂搁置，后续专项解决

[2026-05-28 18:30] WIP iTerm2 中文 IME 诊断第二轮：日志确认中文不产生任何 Key/Paste 事件，加 on_message 拦截所有消息类型 + KEY bytes 字段，待用户反馈第二轮日志

[2026-05-28 18:15] WIP iTerm2 中文 IME 诊断：加 _dbg 函数写 /tmp/tuicode_input.log，记录 on_key/on_paste 收到的事件，待用户反馈日志后确定修复方向

[2026-05-28 18:00] CONSTRAINT iTerm2 中文 IME 输入根本原因确认：Textual raw mode 消费 Space 键导致 IME 无法确认组合字符；Terminal.app 正常，iTerm2 无代码级修复；建议用剪贴板粘贴或做"中文输入栏"功能

[2026-05-28 17:45] FIX PTY bracketed paste：子进程启用 ?2004h 时包裹 \x1b[200~...\x1b[201~，修复 iTerm2 中文 readline echo 宽字符偏移"半个空格"，127 测试通过

[2026-05-28 17:30] VERIFY iTerm2 中文输入仍不正常，待确认英文是否可用、具体失败路径；列出 macOS 主流终端供多终端测试

[2026-05-28 17:15] FIX PTY 终端 CJK 宽字符：跳过右半占位符修复间距 + 新增 on_paste 修复 iTerm2 中文输入丢失，127 测试通过

[2026-05-28 17:00] FIX 编辑器语法高亮：安装缺失的 textual[syntax] extra（tree-sitter-python 等 15 个包），TextArea language 参数恢复生效，126 测试通过

[2026-05-28 16:45] FIX diff 预览窗口语法高亮：用 _colorize_diff + Static(markup=True) 替换无色 TextArea，+/- 行染绿/红，@@ 青色，126 测试通过

[2026-05-28 16:28] DONE 编辑器语法高亮：启用 textual[syntax] 依赖、补齐语言检测与回归，124 测试通过 → sessions/2026-05-28-1628.md

[2026-05-28 16:08] DONE feat-014 Git diff 只读预览：GitFileList 选中文件打开 DiffPreviewWindow，117 测试全通过 → sessions/2026-05-28-1608.md

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
