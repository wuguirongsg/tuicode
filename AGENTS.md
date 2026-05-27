# TuiCode — Agent 工作规范

> 只写"读代码 / 读 README / 读架构文档发现不了"的信息。Session 行为由 Hook 强制执行。
> 完整产品方向见 [.harness/product/backlog.md](.harness/product/backlog.md)，技术架构见 [docs/agentdeck_architecture.md](docs/agentdeck_architecture.md)。

## 不可推翻的约束

- **智能体是一等公民**：编辑器 / 文件树 / 终端的设计目标是服务智能体。不要把 AI 退化为 IDE 插件式的浮窗或侧栏。
- **协议驱动**：新增智能体必须实现 `AgentAdapter` Protocol；禁止在宿主代码里硬编码具体智能体的 CLI 行为。
- **混合布局不可退化**：工作单元（编辑器/智能体会话）浮窗化，全局工具（文件树/Git/运行终端）固定栅格化。不允许改为"纯分割面板"或"纯自由浮窗"。
- **100% TUI**：禁止引入 GUI / Web / Electron / 浏览器渲染。
- **Python 3.11+ + Textual 0.60+**：MVP 不换语言；性能瓶颈出现时才考虑 PyO3 嵌入 Rust 热点。
- **事件总线唯一通信通道**：模块之间走事件总线，禁止硬编码相互依赖。
- **上下文聚合器是唯一数据源**：所有 Adapter 必须通过聚合器拿上下文，禁止 Adapter 直读项目状态。
- **工具调用必须走审批**：智能体的写文件/跑命令/Git 操作一律发 `ToolCallRequested` 事件，禁止 Adapter 自行执行。
- **MVP 编辑器直接用 Textual TextArea**：不自研编辑器内核；LSP / 多光标 / 折叠等留接口、不实现。

## 容易踩的坑

- Textual TextArea 大文件性能差，单文件 >1MB 提示用外部编辑器，别硬扛。
- pyte 对 vim/htop 等全屏 TUI 程序有兼容边界，失效时单独排查，别假设它完美。
- Windows 原生 PTY 复杂，MVP 只支持 Linux/macOS/WSL，别为 Windows 兼容堵塞主路径。
- 智能体 CLI 接口频繁变化，Adapter 要薄、抽象稳定，宿主层不依赖具体输出格式。
- 上下文打包要有 token 预算并按优先级裁剪，禁止无脑塞全量。
- PTY 必须正确透传 Ctrl+C 等控制字符和鼠标事件；终端尺寸变化要 `TIOCSWINSZ` 通知子进程。

## 项目特殊事项

- 代码主目录是 `src/tuicode/`（MVP 新建）。`demo/tui_demo.py` 是技术 spike 参考，**不要直接迭代它**，需要时复制片段到 `src/`。
- 中文优先：用户面对话、commit message、文档默认简体中文，标识符与代码注释仍用英文。

## 文件索引

- [.harness/SESSION_START.md](.harness/SESSION_START.md) — 每次开始前必读
- [.harness/SESSION_END.md](.harness/SESSION_END.md) — 每次结束前必做
- [.harness/product/backlog.md](.harness/product/backlog.md) — 产品方向 + 完整约束
- [.harness/state/current-sprint.md](.harness/state/current-sprint.md) — 当前阶段目标
- [.harness/state/features.json](.harness/state/features.json) — 功能完成合约
- [.harness/registry/_index.md](.harness/registry/_index.md) — 决策索引
- [docs/agentdeck_architecture.md](docs/agentdeck_architecture.md) — 架构设计文档（权威）
