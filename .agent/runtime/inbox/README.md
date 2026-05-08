# Dashboard Inbox Runtime

This directory is runtime state for Dashboard quick capture.

- `pending/`: raw items waiting for Agent processing.
- `processed/`: handled items grouped by month.
- `failed/`: items that could not be processed.
- `cancelled/`: items cancelled from Dashboard.

Do not use this inbox as a long-term knowledge base. Move final content into `tasks/`, `guidance/`, `notes/`, or `research/`.
