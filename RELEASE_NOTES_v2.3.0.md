# Manager Research Workspace Template v2.3.0

This release fixes a data-safety issue in the Dashboard API Agent todo merge flow.

## Highlights

- `upsert_todo` now preserves existing task-package checklist items instead of replacing them when a similar todo is detected.
- Existing todo ids, completed subtask states, in-progress or blocked statuses, higher priority values, tags, notes, and creation timestamps are kept during merges.
- New checklist items, tags, and notes from API Agent cache processing are appended conservatively.
- The API Agent prompt now tells models to keep the existing task id and submit only newly needed checklist items when extending a task package.

## Validation

- `python -m py_compile dashboard\server.py`
- Temporary todo merge behavior smoke test
- `powershell -ExecutionPolicy Bypass -File .agent\validate_agent_runtime.ps1`

## Upgrade Notes

No manual migration is required. Existing `tasks/todo.json` files keep working as-is. This release only changes how future API Agent `upsert_todo` actions are applied.
