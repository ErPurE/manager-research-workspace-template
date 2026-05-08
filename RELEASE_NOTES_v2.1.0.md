# Manager Research Workspace Template v2.1.0

This release improves Dashboard inbox processing and test-record cleanup.

## Added

- `write_idea` action for saving idea cache items to `notes/ideas/`.
- `write_guidance` action for saving guidance cache items to `guidance/`.
- `write_note` action for saving note/freeform cache items to `notes/` or `research/`.
- Inbox “删除记录” button for removing test/runtime records from the visual interface.
- Dashboard hash section links such as `#dashboard`, `#tasks`, `#agent`, and `#inbox`.
- Completed-todo recovery UI: completed items can be restored to their previous status.

## Improved

- API Agent prompt now routes by cache `kind` before considering todo creation.
- Speculative ideas such as “可以试试 ...” are preserved as ideas and do not automatically become todos.
- Guidance is preserved as guidance first; clear action items may still create todos.
- README now documents the multi-kind API Agent behavior.

## Validation

- Real API preview test passed for mixed `idea`, `guidance`, `note`, and `task` cache items.
- Real API preview test passed for a speculative idea-only cache item: it returned `write_idea + process_inbox` and no `upsert_todo`.
- Local action application test passed for `write_idea`.
- Hard-delete inbox API test passed.
