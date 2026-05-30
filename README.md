# TuiCode

> 为终端编程智能体设计的统一 TUI 工作台

把"编辑器 + 文件管理 + 多终端 + Git + 多智能体会话 + 工作区状态同步"整合为一致的终端原生体验，让**人 + 多个 AI 智能体**在同一个终端环境里协同工作。

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Textual 0.60+](https://img.shields.io/badge/textual-0.60+-purple.svg)](https://textual.textualize.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 是什么

主流 IDE 把 AI 当成插件（Copilot 浮窗、Cursor 侧栏）。TuiCode 反过来：**编辑器、文件树、终端都是为了让智能体更好地工作而存在**。

TuiCode 不接管智能体，而是承载成熟 CLI 智能体：Claude Code、Codex、Aider 等继续在 PTY 中运行自己的完整交互体系，TuiCode 负责把它们工作的项目状态可视化、同步和组织起来。

| 维度 | 定位 |
|------|------|
| 形态 | 100% TUI，跑在任意终端模拟器中 |
| 目标用户 | 使用 Claude Code / Codex / Aider 等 CLI 智能体的开发者 |
| 核心价值 | 统一工作台——无需在编辑器、Git 工具、终端之间来回切换 |
| 部署 | 单一命令，跨平台（Linux / macOS / WSL） |

**不是什么**：不是 VSCode 复刻、不是终端模拟器、不是新的 AI 编程工具、不是窗口管理器。

---

## 功能

- **混合布局**：工作单元（编辑器/智能体会话）浮窗化，全局工具（文件树/Git/终端）固定栅格化
- **多智能体并行**：同时开启多个 PTY 会话（Claude Code、Codex、Aider、自定义命令），互不干扰焦点
- **实时感知**：文件变化/Git 状态变化自动刷新，无需手动 reload
- **Git 工作流**：内置 diff 预览（左右对比视图）、按文件 stage/unstage、commit 一键完成
- **文件管理器**：新建 / 重命名 / 删除（带确认）/ 复制路径，直接在文件树操作
- **命令面板**：`Ctrl+Shift+P` 全屏搜索命令，替代不稳定的下拉菜单
- **布局预设**：`Ctrl+1` 编辑模式 / `Ctrl+2` 双 Agent 对比 / `Ctrl+3` 调试模式
- **智能体状态可见**：底栏实时显示运行中 Agent 数量，窗口标题标注运行中/已结束/等待输入

---

## 快速开始

**依赖**：Python 3.11+

```bash
# 安装
pip install tuicode

# 在项目目录启动
cd your-project
tuicode
```

**常用快捷键**：

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+T` | 新建智能体会话（Claude / Codex / Aider / 自定义） |
| `Ctrl+Shift+P` | 命令面板 |
| `Ctrl+1 / 2 / 3` | 切换布局预设 |
| `Alt+1 / 2 / 3` | 快速切换浮窗焦点 |
| `Ctrl+S` | 保存当前文件 |
| `Ctrl+Q` | 退出 |

---

## 技术栈

- **[Textual](https://textual.textualize.io/)** 0.60+ — TUI 框架
- **[pyte](https://github.com/selectel/pyte)** — VT220 终端模拟器（PTY 输出渲染）
- **PTY** — 承载 CLI 智能体完整交互体系

---

## 从源码运行

```bash
git clone https://github.com/wuguirong/tuicode.git
cd tuicode
pip install -e ".[dev]"
python -m tuicode
```

运行测试：

```bash
PYTHONPATH=src pytest -q
```

---

## 架构

详见 [docs/tuicode_architecture.md](docs/tuicode_architecture.md)。

核心设计原则：
- **智能体一等公民**：所有 UI 组件服务于智能体，而非把 AI 降级为浮窗插件
- **事件总线**：模块间唯一通信通道（`FileOpened` / `FileModified` / `GitStatusChanged` / `AgentMessage` 等）
- **工作区状态聚合器**：持续维护当前活动文件、选区、最近文件变化和 Git 状态
- **协议驱动**：`AgentAdapter` Protocol 隔离具体智能体细节，宿主层不绑定任何 CLI 工具

---

## 贡献

欢迎 Issue 和 PR。提交前请确保 `pytest -q` 全部通过。

---

## 许可

[MIT](LICENSE) © 2026 深圳市玄熵智能科技有限责任公司
