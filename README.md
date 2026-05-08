# Manager Research Workspace Template

Manager is a local research-management workspace with a visual Dashboard, structured todo list, offline Agent inbox, Markdown file editing, and optional API Agent processing.

This package is a clean template. It contains no personal profile, research records, tasks, guidance notes, API keys, or runtime history. Fill it with your own projects after installation.

## Quick Start

1. Install Python 3.x.
2. Run `dashboard/start.bat`.
3. Open `http://127.0.0.1:5000`.
4. Edit `.agent/profile.md` with your own research background and preferences.
5. Add tasks through the Dashboard or by editing `tasks/todo.json`.

## Main Features

- Dashboard overview for ideas, tasks, guidance, notes, and Agent inbox.
- Structured todo board backed by `tasks/todo.json`.
- Offline inbox for quick capture before an Agent organizes the content.
- Markdown viewer/editor with backups and optional Agent review.
- API Agent panel for OpenAI-compatible and Anthropic-compatible providers.
- Bootstrap files for Codex, Claude Code, and GitHub Copilot.

## Data Boundaries

- `tasks/todo.json` is the only authoritative todo source.
- `.agent/` is the only authoritative Agent rule system.
- `.agent/runtime/local_api_profiles.json` stores local API keys and must remain untracked.
- `.agent/runtime/agent_runs/` stores local API processing records and must remain untracked.
- Do not put private research notes, personal profile, or API keys into a public release.

## Validation

```powershell
python -m py_compile dashboard\server.py
node --check dashboard\app.js
powershell -ExecutionPolicy Bypass -File .agent\validate_agent_runtime.ps1
```

Version: v2.0.0-template
