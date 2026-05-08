# Manager Research Workspace Template v2.2.0

This release focuses on making the Dashboard todo workflow more practical and polished.

## Highlights

- Added per-subtask completion toggles inside todo checklist items.
- Kept backward compatibility with existing string-based checklist entries.
- The first subtask toggle converts that checklist into structured `{ text, done, updated_at }` entries.
- Updated agent maintenance rules so future agents understand the structured checklist format.
- Includes the redesigned Dashboard visual style from the previous main-branch update.

## Validation

- `node --check dashboard\app.js`
- `python -m py_compile dashboard\server.py`
- `powershell -ExecutionPolicy Bypass -File .agent\validate_agent_runtime.ps1`

## Upgrade Notes

Existing `tasks/todo.json` files do not need manual migration. Old checklist arrays such as:

```json
["Subtask A", "Subtask B"]
```

will continue to render normally. When a user toggles a subtask in the Dashboard, that checklist is converted to:

```json
[
  {
    "text": "Subtask A",
    "done": true,
    "updated_at": "..."
  }
]
```
