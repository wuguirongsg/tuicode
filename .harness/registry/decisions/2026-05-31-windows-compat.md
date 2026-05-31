# ADR: Windows 原生兼容方案（PTY 后端抽象 + 剪贴板后端抽象）

**日期**：2026-05-31
**状态**：Proposed（待排期，未实现）

## 背景

排查当前项目在 Windows 下的可运行性，结论是**原生 Windows 无法运行**，且与既有约束一致（backlog「已知坑」：MVP 优先 Linux/macOS/WSL，Windows 原生延后，不堵塞主路径）。

阻塞点集中在两处，宿主其余部分（Textual / pyte / 事件总线 / Git / 文件树 / 编辑器）均为纯 Python，本身跨平台。

### 致命阻塞（直接崩溃）

`src/tuicode/ui/pty_terminal.py` 在模块顶部 `import fcntl` / `import termios`，这两个标准库在 Windows CPython 上不存在，加载即抛 `ModuleNotFoundError`。终端是启动即用的一等公民功能，因此整个 App 起不来。

即便绕过 import，PTY 创建逻辑也全是 POSIX-only：

- `os.openpty()` / `os.ttyname()` — Windows 无对应物
- `os.setsid()` + `preexec_fn=_child_setup`（`_start_pty`）— `preexec_fn` 仅 POSIX 支持
- `fcntl.fcntl(..., O_NONBLOCK)`、`fcntl.ioctl(..., termios.TIOCSWINSZ, ...)`（窗口尺寸）— POSIX-only
- `loop.add_reader(master_fd, ...)` — Windows 的 `ProactorEventLoop` 不支持对任意 fd 的 `add_reader`

### 次要兼容问题（不崩溃，功能失效）

- 默认 shell 硬编码 `/bin/bash`（`pty_terminal.py:191`、`agent_terminal_window.py:55`、`new_agent_modal.py`），Windows 无此路径。
- 剪贴板 `src/tuicode/clipboard.py` 与 `file_tree.py` 仅调 `pbcopy/pbpaste`（mac）、`wl-copy/xclip/xsel`（Linux），Windows 上全部 `FileNotFoundError` 后静默失败。

## 决策

引入两层薄抽象，把平台相关代码从 UI 层剥离；POSIX 路径保持现状（不回归），新增 Windows 路径。

### 1. PTY 后端抽象（核心）

定义一个稳定的 `PtyBackend` 接口，`PtyTerminal` Widget 只依赖接口，不再直接 `import fcntl/termios`：

```
class PtyBackend(Protocol):
    def spawn(self, argv: list[str], cols: int, rows: int, env: dict) -> None: ...
    def write(self, data: bytes) -> None: ...
    def resize(self, cols: int, rows: int) -> None: ...
    def read_nonblocking(self) -> bytes: ...      # 或回调 / async 读
    def terminate(self) -> None: ...
    @property
    def is_alive(self) -> bool: ...
```

- `PosixPtyBackend`：把现有 `_start_pty` / `_set_pty_size` / `_on_pty_readable` 逻辑原样搬入（`openpty` + `setsid` + `fcntl` + `add_reader`）。
- `WindowsPtyBackend`：基于 **`pywinpty`（ConPTY）**。ConPTY 提供伪终端读写与 resize；读循环在 Windows 上改为后台线程 + `call_from_thread` 把数据投递回 Textual（规避 `add_reader` 不支持任意 fd 的问题）。
- 平台选择集中在一个工厂函数（`sys.platform.startswith("win")` 判定），UI 层不感知具体实现。
- `import fcntl/termios` 移入 `PosixPtyBackend` 内部，确保 Windows 上不会在 import 期崩溃。

### 2. 默认 shell 按平台决定

新增 `default_shell()` 工具：POSIX 返回 `/bin/bash`（或 `$SHELL`），Windows 返回 `powershell.exe`（回退 `cmd.exe`）。`NewAgentModal` 的内置项也按平台给出。

### 3. 剪贴板后端按平台扩展

`clipboard.py` 的候选命令列表加 Windows 分支：写用 `clip.exe`，读用 `powershell -command Get-Clipboard`（或引入 `pyperclip` 统一处理）。`file_tree.py` 复用同一 `clipboard` 模块，去掉重复的命令分支。

### 范围与非目标

- **不**为 Windows 改动布局、事件总线、聚合器、编辑器——它们已跨平台。
- **不**追求与 POSIX 完全等价的 PTY 行为；ConPTY 对 vim/htop 等全屏程序的兼容边界单独验证（沿用「pyte 有边界」的既有态度）。
- 鼠标透传、`TIOCSWINSZ` 等控制语义在 Windows 用 ConPTY 的 resize API 等价实现。

## 影响

- 新增可选依赖 `pywinpty`（仅 Windows，`pyproject.toml` 用环境标记 `pywinpty; sys_platform == "win32"`），不影响 Linux/macOS 安装。
- `PtyTerminal` 重构为依赖 `PtyBackend`，需要回归现有 253 测试中与 PTY 相关的用例，确保 POSIX 路径零行为变化。
- 测试策略：Windows 路径在缺少 CI Windows runner 前以接口契约测试 + mock backend 覆盖，真机验证延后。

## 后续 / 排期建议

- 优先级 **P3（延后）**：与现有「Windows 原生延后」约束一致；不堵塞主路径。
- 现阶段对 Windows 用户的官方推荐仍是 **WSL**（纯 Linux 环境，零改动即可用），应在 README 明确写出。
- 实施前先补一句 README「平台支持」说明（Linux/macOS/WSL 原生，Windows 原生规划中）。
