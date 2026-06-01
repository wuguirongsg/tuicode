# Changelog

All notable changes to TuiCode will be documented in this file.

## [0.1.0] — 2026-06-01

### Added

- **PTY agent hosting**: Run Claude Code, Codex, Aider, or any CLI tool in a full PTY session
- **Hybrid layout**: Floating work units (editor/agent sessions) + fixed grid for global tools (file tree, Git, terminal)
- **Multi-agent parallel sessions**: Open multiple agent PTYs simultaneously without focus conflicts
- **Real-time workspace awareness**: Auto-refresh on file changes and Git status changes
- **Git workflow**: Side-by-side diff preview, per-file stage/unstage, one-click commit
- **File manager**: Create, rename, delete (with confirmation), copy path — all from the file tree
- **Command palette**: `Ctrl+Shift+P` full-screen command search
- **Layout presets**: Editor mode (`Ctrl+1`), dual-agent comparison (`Ctrl+2`), debug mode (`Ctrl+3`)
- **Tile/float toggle**: `Ctrl+\` switches agent windows between tiled and floating modes
- **Agent status bar**: Live running-agent count, window titles reflect agent state (running / done / waiting)
- **AgentAdapter protocol**: Extensible adapter interface for adding new CLI agents
- **Event bus architecture**: Decoupled module communication via typed events
