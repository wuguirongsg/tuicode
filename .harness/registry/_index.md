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

[2026-05-31 15:25] DECISION Windows 原生兼容方案：确认原生 Windows 无法运行（fcntl/termios 顶层 import + PTY 全链 POSIX-only），提出 PTY 后端抽象（PosixPtyBackend / WindowsPtyBackend via pywinpty ConPTY）+ 剪贴板后端 + 默认 shell 按平台；P3 延后，现阶段推荐 WSL → decisions/2026-05-31-windows-compat.md

[2026-05-31 15:30] STATUS 本次 Session 仅 Q&A：Terminal.app 中 Shift+拖拽选区后 Cmd+C 无效，建议保持 Shift 按住再按 Cmd+C 或用 Edit 菜单复制；无代码改动

[2026-05-31 14:58] DONE PTY 终端鼠标选区 + Ctrl+C 复制：TUI 内 PTY 面板支持鼠标拖选并 Ctrl+C 复制到系统剪贴板，253 tests passed

[2026-05-31 14:50] FIX 打通系统剪贴板：修复编辑器和 PTY 终端复制粘贴与宿主系统剪贴板互通，253 tests passed

[2026-05-31 14:10] FIX 本地 Agent 检测结果持久化到缓存文件，启动器优先读取缓存并支持重新检测，250 tests passed

[2026-05-31 12:55] FIX 新建 Agent 会话启动器改为初始空列表 + 点击检测本地 Agent 后三列展示，支持自定义 Agent 入列表，248 tests passed

[2026-05-31 12:09] FIX 历史会话卡片右边框凸出：按终端 cell width 裁剪/补齐中英文混排文本，244 tests passed

[2026-05-31 12:02] FIX 历史 Agent 会话卡片样式：三列网格增加边框、列间距、行间距和收敛选中态，243 tests passed

[2026-05-31 11:50] FIX 历史 Agent 会话界面改为三列卡片网格：支持方向键/鼠标选择，详情页新增删除会话，242 tests passed

[2026-05-30] FIX 会话记忆重构：OSC 标题提取（\x1b]0;）+ pyte scrollback 摘要 + escape 剥离修复，会话列表标签从乱码变为真实任务描述，239 tests passed

[2026-05-30 22:38] FIX 历史 Agent 会话展示清理：过滤 Claude TUI 噪声，列表使用短摘要，详情只显示结构化元信息/摘要/关键输出，234 tests passed

[2026-05-30 22:30] FIX 历史 Agent 会话选择体验：列表显示摘要描述，点击先查看详情，详情页确认后才继续，232 tests passed

[2026-05-30 22:15] FIX 继续历史 Agent 会话输入卡住：完整上下文改写入 handoff 文件，PTY 只自动提交一行短提示并绕开 bracketed paste，229 tests passed

[2026-05-30 21:50] DONE Agent 会话记忆与跨 Agent 接续：保存 PTY transcript/摘要，命令面板可选历史会话并用任意 Agent 继续 → sessions/2026-05-30-2150.md

[2026-05-30] FIX Git 面板 diff 浮窗改为 split（左右对比）视图：_parse_diff 解析 unified diff、_render_split 双列渲染（旧内容红左/新内容绿右），窗口宽度扩至 100，220 tests passed

[2026-05-30] FIX Git 面板状态标识改为通用惯例：U 未追踪、M 修改、A 暂存、D 删除、R 重命名，22 tests passed

[2026-05-30] FIX Git 面板文件列表加文件/目录图标：📄 普通文件、📁 目录（路径以 / 结尾），22 tests passed

[2026-05-30] FIX Git 面板文件列表改为 ListView 行高亮模式：用 ListView+ListItem 替换旧 render() 纯文本，彩色状态标记 M/A/D/R/??，行级选中高亮，#git-status 固定单行头，22 tests passed

[2026-05-30] DONE i18n 全面补齐：command_palette_modal / new_agent_modal / app.py BINDINGS+notify+PaletteCommand 共 46 个新键，切换英文后 F1 面板和 Ctrl+T 启动器立即生效，201 tests passed

[2026-05-30] FIX 命令面板加「切换界面语言」入口：F1 确认可用；Ctrl+/ 不生效属终端层面拦截（预期）；save_lang() 写 ~/.config/tuicode/settings.toml，notify 提示重启生效；201 tests passed

[2026-05-29] FIX 双击 Ctrl+C 退出：第一次发 \x03 给 PTY + 弹 1.5s toast 提示，窗口内再按一次退出 App；Ctrl+Q 保留备用

[2026-05-29] FIX 命令面板快捷键修复 + 主题切换：Ctrl+Shift+P 无法在终端区分替换为 Ctrl+/ (ctrl+underscore) + F1 双绑；加入主题循环（cyberpunk→textual-dark→nord→gruvbox→textual-light）进命令面板；F1 从 PTY _KEY_MAP 移除并加入保留键集合

[2026-05-29] DESIGN AI 界面设计评审（ICO + Agentic 框架）：识别 6 项改进入 backlog 待评估区——P0 智能体运行状态可见（agent_count 死信号 + 假 Tab）、P1 功能发现 + diff 体验、P2 通知 + 启动器环境感知；另记命令面板缺 feat-018 承诺的 diff/切栏命令

[2026-05-29 16:30] STATUS 本次 Session 仅做状态确认，无新功能或修复；stop hook 反馈"No stderr output"属预期行为（钩子只写 stdout）

[2026-05-29 12:00] DONE Phase 2A 状态确认：feat-001 至 feat-018 全部 passes=true，172 tests passed；Phase 2A Agent 工作流打磨完整闭环达成

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

[2026-05-29] DONE feat-015/016/017/018 Phase 2A 全部完成：Git stage/commit 闭环、布局预设 Ctrl+1/2/3、Agent 启动器 Modal、命令面板 Ctrl+Shift+P，172 tests passed → sessions/2026-05-29-build.md

[2026-05-31] DONE 底部终端多 Tab 支持 + 状态栏版权区：TerminalStrip 升级多标签切换/新建/关闭，StatusBar 增加版权段，253 tests passed
