"""多语言支持 — t() 函数 + zh_CN / en_US 字典。

语言通过 ~/.config/tuicode/settings.toml 配置，默认中文。
设置示例：
    [i18n]
    lang = "en"   # 可选 "zh"（中文）或 "en"（英文）
"""
from __future__ import annotations

import tomllib
from pathlib import Path

_STRINGS: dict[str, dict[str, str]] = {
    # ── MenuBar ───────────────────────────────────────────────────────────────
    "menu.file":   {"zh": "文件", "en": "File"},
    "menu.edit":   {"zh": "编辑", "en": "Edit"},
    "menu.view":   {"zh": "视图", "en": "View"},
    "menu.agents": {"zh": "智能体", "en": "Agents"},
    "menu.help":   {"zh": "帮助", "en": "Help"},
    "menu.todo":   {"zh": "（菜单待实现）", "en": "(menu not implemented)"},
    # ── StatusBar ─────────────────────────────────────────────────────────────
    "status.no_agents":  {"zh": "○ 无 agent", "en": "○ no agents"},
    "status.agents":     {"zh": "● {n} agent", "en": "● {n} agent"},
    "status.agents_pl":  {"zh": "● {n} agents", "en": "● {n} agents"},
    "status.shortcuts":  {"zh": "^Q 退出  ^` 终端", "en": "^Q quit  ^` terminal"},
    "status.filetree_hint": {
        "zh": "a 新建文件  A 新建夹  r 重命名  d 删除  y 复制路径  Y 相对路径",
        "en": "a new  A newdir  r rename  d delete  y copy-path  Y rel-path",
    },
    # ── TaskBar ───────────────────────────────────────────────────────────────
    "taskbar.no_windows": {"zh": "（无打开窗口）", "en": "(no open windows)"},
    # ── FloatWorkspace hint ───────────────────────────────────────────────────
    "workspace.hint": {
        "zh": "浮窗工作区\n\n打开文件或启动智能体会话后，工作窗口将在此区域显示",
        "en": "Float workspace\n\nOpen a file or start an agent session to see windows here",
    },
    # ── EditorWindow ─────────────────────────────────────────────────────────
    "editor.confirm_close":     {"zh": "文件已修改，确认丢弃更改并关闭？", "en": "File modified. Discard changes and close?"},
    "editor.btn_discard":       {"zh": "丢弃", "en": "Discard"},
    "editor.btn_cancel":        {"zh": "取消", "en": "Cancel"},
    "editor.saved":             {"zh": "已保存", "en": "Saved"},
    "editor.empty_window":      {"zh": "(空窗口)", "en": "(empty window)"},
    # ── RightPanel ────────────────────────────────────────────────────────────
    "panel.tab_files": {"zh": "files", "en": "files"},
    "panel.tab_git":   {"zh": "git", "en": "git"},
    # ── FileTree 文件操作 ──────────────────────────────────────────────────────
    "fileop.new_file":        {"zh": "新建文件", "en": "New file"},
    "fileop.new_folder":      {"zh": "新建文件夹", "en": "New folder"},
    "fileop.rename":          {"zh": "重命名", "en": "Rename"},
    "fileop.name_hint":       {"zh": "名称", "en": "name"},
    "fileop.btn_ok":          {"zh": "确定", "en": "OK"},
    "fileop.btn_cancel":      {"zh": "取消", "en": "Cancel"},
    "fileop.btn_delete":      {"zh": "删除", "en": "Delete"},
    "fileop.confirm_delete":  {"zh": "确认删除「{name}」？此操作不可撤销", "en": "Delete \"{name}\"? This cannot be undone."},
    "fileop.copied_abs":      {"zh": "已复制绝对路径", "en": "Copied absolute path"},
    "fileop.copied_rel":      {"zh": "已复制相对路径", "en": "Copied relative path"},
    "fileop.created":         {"zh": "已创建 {name}", "en": "Created {name}"},
    "fileop.renamed":         {"zh": "已重命名为 {name}", "en": "Renamed to {name}"},
    "fileop.deleted":         {"zh": "已删除 {name}", "en": "Deleted {name}"},
    "fileop.failed":          {"zh": "操作失败：{err}", "en": "Operation failed: {err}"},
    # ── TerminalStrip ─────────────────────────────────────────────────────────
    "terminal.tab_bash":  {"zh": "[bash]  [+]", "en": "[bash]  [+]"},
    "terminal.drag_hint": {"zh": "─ ↕ 拖动调整终端高度 ↕ ─", "en": "─ ↕ drag to resize terminal ↕ ─"},
    # ── Mascot states ─────────────────────────────────────────────────────────
    "mascot.idle":    {"zh": "就绪",   "en": "ready"},
    "mascot.opening": {"zh": "读取",   "en": "reading"},
    "mascot.running": {"zh": "运行",   "en": "running"},
    "mascot.agent":   {"zh": "智能体", "en": "agent"},
    "mascot.success": {"zh": "完成",   "en": "done"},
    "mascot.error":   {"zh": "错误",   "en": "error"},
    # ── Settings screen ───────────────────────────────────────────────────────
    "settings.title":    {"zh": "设置", "en": "Settings"},
    "settings.language": {"zh": "界面语言", "en": "Interface Language"},
    "settings.lang_zh":  {"zh": "中文", "en": "Chinese"},
    "settings.lang_en":  {"zh": "English", "en": "English"},
    "settings.saved":    {"zh": "设置已保存，重启生效", "en": "Settings saved, restart to apply"},
    # ── CommandPalette modal ───────────────────────────────────────────────────
    "palette.title":       {"zh": "> 命令面板",   "en": "> Command Palette"},
    "palette.placeholder": {"zh": "搜索命令…",    "en": "Search commands…"},
    "palette.no_match":    {"zh": "(无匹配命令)", "en": "(no matching commands)"},
    "palette.bind_close":  {"zh": "关闭",         "en": "Close"},
    "palette.bind_down":   {"zh": "下移",          "en": "Down"},
    "palette.bind_up":     {"zh": "上移",          "en": "Up"},
    # ── NewAgentModal ─────────────────────────────────────────────────────────
    "agent.modal_title":  {"zh": "新建 Agent 会话", "en": "New Agent Session"},
    "agent.custom_label": {"zh": "自定义命令：",    "en": "Custom command:"},
    "agent.btn_start":    {"zh": "启动",            "en": "Start"},
    "agent.btn_cancel":   {"zh": "取消",            "en": "Cancel"},
    "agent.history_title": {"zh": "继续历史 Agent 会话", "en": "Continue Agent Session"},
    "agent.history_empty": {"zh": "暂无历史会话",        "en": "No saved sessions yet"},
    "agent.detail_title": {"zh": "历史会话详情", "en": "Session Details"},
    "agent.btn_view":     {"zh": "查看",         "en": "View"},
    "agent.btn_continue": {"zh": "继续此会话",   "en": "Continue Session"},
    "agent.btn_delete":   {"zh": "删除会话",     "en": "Delete Session"},
    "agent.btn_back":     {"zh": "返回列表",     "en": "Back"},
    # ── App key bindings ──────────────────────────────────────────────────────
    "bind.quit":            {"zh": "退出",           "en": "Quit"},
    "bind.focus_terminal":  {"zh": "聚焦终端",        "en": "Focus terminal"},
    "bind.new_agent":       {"zh": "新建智能体终端",  "en": "New agent terminal"},
    "bind.win1":            {"zh": "切换窗口 1",      "en": "Window 1"},
    "bind.win2":            {"zh": "切换窗口 2",      "en": "Window 2"},
    "bind.win3":            {"zh": "切换窗口 3",      "en": "Window 3"},
    "bind.layout_edit":     {"zh": "编辑布局",        "en": "Edit layout"},
    "bind.layout_dual":     {"zh": "双 Agent 布局",   "en": "Dual agent"},
    "bind.layout_debug":    {"zh": "调试布局",        "en": "Debug layout"},
    "bind.command_palette": {"zh": "命令面板",        "en": "Command palette"},
    # ── App runtime messages ──────────────────────────────────────────────────
    "app.ctrl_c_hint": {"zh": "再按一次 Ctrl+C 退出", "en": "Press Ctrl+C again to quit"},
    "app.lang_switched": {
        "zh": "界面语言已切换为 {label}，重启后完全生效\n配置文件：~/.config/tuicode/settings.toml",
        "en": "Language switched to {label}. Restart to apply.\nConfig: ~/.config/tuicode/settings.toml",
    },
    "app.lang_title": {"zh": "语言 / Language", "en": "Language / 语言"},
    # ── PaletteCommand names & descriptions ───────────────────────────────────
    "cmd.theme.name":        {"zh": "切换主题",                    "en": "Switch theme"},
    "cmd.theme.desc":        {"zh": "当前：{theme}，循环切换配色方案", "en": "Current: {theme}, cycle color schemes"},
    "cmd.lang.name":         {"zh": "切换界面语言 → {lang}",       "en": "Switch language → {lang}"},
    "cmd.lang.desc":         {
        "zh": "当前：{cur}，保存到 ~/.config/tuicode/settings.toml，重启生效",
        "en": "Current: {cur}, saved to ~/.config/tuicode/settings.toml, restart to apply",
    },
    "cmd.new_agent.name":    {"zh": "新建 Agent 会话",             "en": "New Agent Session"},
    "cmd.new_agent.desc":    {"zh": "打开 Agent 启动器（Ctrl+T）", "en": "Open agent launcher (Ctrl+T)"},
    "cmd.continue_agent.name": {"zh": "继续历史 Agent 会话",        "en": "Continue Agent Session"},
    "cmd.continue_agent.desc": {"zh": "选择历史记忆，再用任意 Agent 接续", "en": "Pick memory, then continue with any agent"},
    "cmd.layout_edit.name":  {"zh": "布局：编辑模式",              "en": "Layout: Edit"},
    "cmd.layout_edit.desc":  {"zh": "主窗口最大化（Ctrl+1）",      "en": "Maximize main window (Ctrl+1)"},
    "cmd.layout_dual.name":  {"zh": "布局：双 Agent 对比",         "en": "Layout: Dual agent"},
    "cmd.layout_dual.desc":  {"zh": "左右分屏（Ctrl+2）",          "en": "Split left/right (Ctrl+2)"},
    "cmd.layout_debug.name": {"zh": "布局：调试模式",              "en": "Layout: Debug"},
    "cmd.layout_debug.desc": {"zh": "上大下小（Ctrl+3）",          "en": "Large top, small bottom (Ctrl+3)"},
    "cmd.reset_win.name":    {"zh": "重置窗口位置",                "en": "Reset window positions"},
    "cmd.reset_win.desc":    {"zh": "把所有浮窗拉回可见区域（窗口跑到屏幕外时用）", "en": "Bring all windows back into view"},
    "cmd.focus_term.name":   {"zh": "聚焦底部终端",                "en": "Focus terminal"},
    "cmd.focus_term.desc":   {"zh": "切换焦点到 bash 终端（Ctrl+`）", "en": "Focus bash terminal (Ctrl+`)"},
    "cmd.win1.name":         {"zh": "切换窗口 1",                  "en": "Focus window 1"},
    "cmd.win1.desc":         {"zh": "置顶第 1 个浮窗（Alt+1）",    "en": "Bring window 1 to front (Alt+1)"},
    "cmd.win2.name":         {"zh": "切换窗口 2",                  "en": "Focus window 2"},
    "cmd.win2.desc":         {"zh": "置顶第 2 个浮窗（Alt+2）",    "en": "Bring window 2 to front (Alt+2)"},
    "cmd.win3.name":         {"zh": "切换窗口 3",                  "en": "Focus window 3"},
    "cmd.win3.desc":         {"zh": "置顶第 3 个浮窗（Alt+3）",    "en": "Bring window 3 to front (Alt+3)"},
    "cmd.git_commit.name":   {"zh": "Git commit（聚焦输入框）",    "en": "Git commit (focus input)"},
    "cmd.git_commit.desc":   {"zh": "将焦点移到右栏 commit 输入框", "en": "Move focus to the commit input bar"},
    "cmd.quit.name":         {"zh": "退出",                        "en": "Quit"},
    "cmd.quit.desc":         {"zh": "退出 TuiCode（Ctrl+Q）",      "en": "Quit TuiCode (Ctrl+Q)"},
}


def _load_lang() -> str:
    cfg = Path.home() / ".config" / "tuicode" / "settings.toml"
    if cfg.exists():
        try:
            data = tomllib.loads(cfg.read_text())
            lang = data.get("i18n", {}).get("lang", "zh")
            return lang if lang in ("zh", "en") else "zh"
        except Exception:
            pass
    return "zh"


_LANG: str = _load_lang()


def get_lang() -> str:
    return _LANG


def set_lang(lang: str) -> None:
    """运行时切换语言（下次 t() 调用立即生效）。"""
    global _LANG
    if lang in ("zh", "en"):
        _LANG = lang


def save_lang(lang: str) -> None:
    """持久化语言设置到 ~/.config/tuicode/settings.toml。"""
    cfg_dir = Path.home() / ".config" / "tuicode"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg = cfg_dir / "settings.toml"
    content = f'[i18n]\nlang = "{lang}"\n'
    cfg.write_text(content)
    set_lang(lang)


def t(key: str, **kwargs: object) -> str:
    """查找翻译字符串，支持 {变量} 插值。key 不存在时回退到 key 本身。"""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_LANG) or entry.get("zh") or key
    if kwargs:
        text = text.format(**kwargs)
    return text
