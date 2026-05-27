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
    # ── TerminalStrip ─────────────────────────────────────────────────────────
    "terminal.tab_bash":  {"zh": "[bash]  [+]", "en": "[bash]  [+]"},
    "terminal.drag_hint": {"zh": "─ ↕ 拖动调整终端高度 ↕ ─", "en": "─ ↕ drag to resize terminal ↕ ─"},
    # ── Settings screen ───────────────────────────────────────────────────────
    "settings.title":    {"zh": "设置", "en": "Settings"},
    "settings.language": {"zh": "界面语言", "en": "Interface Language"},
    "settings.lang_zh":  {"zh": "中文", "en": "Chinese"},
    "settings.lang_en":  {"zh": "English", "en": "English"},
    "settings.saved":    {"zh": "设置已保存，重启生效", "en": "Settings saved, restart to apply"},
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
