"""
科研管理仪表板 - Python 服务器
使用 Flask 提供 API 和静态文件服务
"""

from datetime import datetime
import http.client
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import uuid

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS


app = Flask(__name__, static_folder=".", static_url_path="")
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:5000",
                "http://localhost:5000",
            ]
        }
    },
)

# 工作区根目录
WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
INBOX_ROOT = WORKSPACE_ROOT / ".agent" / "runtime" / "inbox"
PENDING_DIR = INBOX_ROOT / "pending"
PROCESSED_DIR = INBOX_ROOT / "processed"
FAILED_DIR = INBOX_ROOT / "failed"
CANCELLED_DIR = INBOX_ROOT / "cancelled"
BACKUP_ROOT = WORKSPACE_ROOT / ".agent" / "runtime" / "dashboard_backups"
API_PROFILE_FILE = WORKSPACE_ROOT / ".agent" / "runtime" / "local_api_profiles.json"
AGENT_RUN_ROOT = WORKSPACE_ROOT / ".agent" / "runtime" / "agent_runs"

CATEGORY_DIRS = {
    "ideas": "notes/ideas",
    "tasks": "tasks",
    "guidance": "guidance",
    "notes": "notes",
}
TODO_FILE = WORKSPACE_ROOT / "tasks" / "todo.json"
TODO_STATUS_VALUES = {"todo", "in_progress", "waiting", "blocked", "paused", "done", "cancelled"}
WRITABLE_ROOTS = {"notes", "tasks", "guidance", "research"}
AGENT_WRITE_EXACT_PATHS = {
    "tasks/todo.json",
    "guidance/README.md",
    ".agent/runtime/active_context.md",
    ".agent/runtime/handoff_note.md",
    ".agent/memory/tasks.json",
}
AGENT_WRITE_PREFIXES = (
    "guidance/",
    "notes/",
    "research/",
)
AGENT_CONTEXT_FILES = (
    ".agent/README_agent_runtime.md",
    ".agent/core/core_rules.md",
    ".agent/core/task_router.md",
    ".agent/workflows/dashboard-inbox.md",
    ".agent/workflows/add-task.md",
    ".agent/workflows/log-guidance.md",
    "tasks/todo.json",
    "guidance/README.md",
)
AGENT_ALLOWED_ACTIONS = {
    "replace_json",
    "write_text",
    "replace_text",
    "write_idea",
    "write_guidance",
    "write_note",
    "upsert_todo",
    "process_inbox",
}
DEFAULT_API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "ManagerDashboard/2.0 Safari/537.36"
    ),
}
VALID_KINDS = {"idea", "task", "guidance", "note", "freeform", "file_edit_review"}
ROUTING_HINTS = {
    "idea": "new-idea",
    "task": "add-task",
    "guidance": "log-guidance",
    "note": "file-management",
    "freeform": "unknown",
    "file_edit_review": "file-management",
}
INBOX_STATUS_DIRS = {
    "pending": PENDING_DIR,
    "failed": FAILED_DIR,
    "cancelled": CANCELLED_DIR,
}


def now_iso():
    """Return local time with timezone, without microseconds."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_runtime_dirs():
    for directory in (PENDING_DIR, PROCESSED_DIR, FAILED_DIR, CANCELLED_DIR, BACKUP_ROOT, AGENT_RUN_ROOT):
        directory.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def read_json_file(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = now_iso()[:10]
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def load_todo_data():
    data = read_json_file(
        TODO_FILE,
        {
            "schema_version": 1,
            "last_updated": now_iso()[:10],
            "status_values": sorted(TODO_STATUS_VALUES),
            "priority_values": [1, 2, 3],
            "items": [],
        },
    )
    items = data.get("items", [])
    if not isinstance(items, list):
        data["items"] = []
    return data


def active_todo_count():
    data = load_todo_data()
    return sum(
        1
        for item in data.get("items", [])
        if item.get("status") not in {"done", "cancelled"}
    )


def default_api_profiles():
    return {
        "schema_version": 1,
        "active_profile_id": "",
        "profiles": [],
    }


def load_api_profiles(include_keys=False):
    ensure_runtime_dirs()
    data = read_json_file(API_PROFILE_FILE, default_api_profiles())
    profiles = data.get("profiles", [])
    if not isinstance(profiles, list):
        profiles = []
        data["profiles"] = profiles

    if include_keys:
        return data

    safe_profiles = []
    for profile in profiles:
        safe = dict(profile)
        key = str(safe.get("api_key", ""))
        if key:
            safe["api_key"] = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"
            safe["has_api_key"] = True
        else:
            safe["api_key"] = ""
            safe["has_api_key"] = False
        safe_profiles.append(safe)
    return {
        "schema_version": data.get("schema_version", 1),
        "active_profile_id": data.get("active_profile_id", ""),
        "profiles": safe_profiles,
    }


def save_api_profiles(data):
    data["schema_version"] = 1
    atomic_write_json(API_PROFILE_FILE, data)


def normalize_provider(value):
    provider = str(value or "").strip().lower()
    if provider not in {"openai", "anthropic"}:
        raise ValueError("Provider must be openai or anthropic")
    return provider


def normalize_api_profile(payload, existing=None):
    existing = existing or {}
    profile_id = str(existing.get("id") or payload.get("id") or uuid.uuid4().hex[:10]).strip()
    name = str(payload.get("name") or existing.get("name") or "API Profile").strip()
    provider = normalize_provider(payload.get("provider", existing.get("provider", "openai")))
    base_url = str(payload.get("base_url", existing.get("base_url", ""))).strip()
    model = str(payload.get("model", existing.get("model", ""))).strip()
    api_key = payload.get("api_key")
    if api_key is None or str(api_key) == "":
        api_key = existing.get("api_key", "")
    else:
        api_key = str(api_key).strip()

    if not base_url:
        raise ValueError("Base URL is required")
    if not model:
        raise ValueError("Model is required")

    timestamp = now_iso()
    return {
        "id": profile_id,
        "name": name,
        "provider": provider,
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
        "created_at": existing.get("created_at", timestamp),
        "updated_at": timestamp,
    }


def get_api_profile(profile_id=None):
    data = load_api_profiles(include_keys=True)
    selected_id = profile_id or data.get("active_profile_id", "")
    profiles = data.get("profiles", [])
    if not selected_id and profiles:
        return profiles[0]
    for profile in profiles:
        if profile.get("id") == selected_id:
            return profile
    return None


def normalize_chat_url(base_url):
    base_url = base_url.rstrip("/")
    if base_url.endswith("/chat/completions") or base_url.endswith("/messages"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def normalize_anthropic_url(base_url):
    base_url = base_url.rstrip("/")
    if base_url.endswith("/messages"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/messages"
    return f"{base_url}/v1/messages"


def post_json(url, payload, headers, timeout=120):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request_obj = urllib.request.Request(
        url,
        data=body,
        headers={**DEFAULT_API_HEADERS, **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        clean_body = error_body.strip()
        if error.code == 403 and "1010" in clean_body:
            raise RuntimeError(
                "API HTTP 403 / 1010: provider gateway rejected this request. "
                "Check whether the Base URL is the real API endpoint, whether this API supports server-side calls, "
                "or use a provider endpoint that does not block non-browser API clients."
            ) from error
        raise RuntimeError(f"API HTTP {error.code}: {clean_body}") from error
    except http.client.RemoteDisconnected as error:
        raise RuntimeError(
            "API connection closed before a response was returned. "
            "The provider may have timed out while generating a long answer; try again with the compact action plan, "
            "or use a provider with a longer server-side timeout."
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"API connection failed: {error.reason}") from error


def call_agent_model(profile, prompt):
    provider = profile.get("provider")
    api_key = profile.get("api_key", "")
    if not api_key:
        raise ValueError("Selected profile has no API key")

    if provider == "openai":
        data = post_json(
            normalize_chat_url(profile.get("base_url", "")),
            {
                "model": profile["model"],
                "temperature": 0.1,
                "max_tokens": 1800,
                "messages": [
                    {"role": "system", "content": "You are a careful local workspace maintenance agent. Return JSON only."},
                    {"role": "user", "content": prompt},
                ],
            },
            {"Authorization": f"Bearer {api_key}"},
        )
        return data["choices"][0]["message"]["content"]

    if provider == "anthropic":
        data = post_json(
            normalize_anthropic_url(profile.get("base_url", "")),
            {
                "model": profile["model"],
                "max_tokens": 4096,
                "temperature": 0.1,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
            },
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        parts = data.get("content", [])
        return "".join(part.get("text", "") for part in parts if part.get("type") == "text")

    raise ValueError("Unsupported provider")


def extract_json_object(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def atomic_write_json(path, data):
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    atomic_write_text(path, content)


def resolve_workspace_path(raw_path):
    if not raw_path:
        raise ValueError("No path provided")
    if Path(raw_path).is_absolute():
        raise ValueError("Absolute paths are not allowed")

    full_path = (WORKSPACE_ROOT / raw_path).resolve()
    full_path.relative_to(WORKSPACE_ROOT)
    return full_path


def workspace_relative_path(path):
    return str(path.resolve().relative_to(WORKSPACE_ROOT)).replace("\\", "/")


def is_editable_markdown(path):
    try:
        relative_path = path.resolve().relative_to(WORKSPACE_ROOT)
    except ValueError:
        return False
    return (
        path.suffix.lower() == ".md"
        and len(relative_path.parts) > 0
        and relative_path.parts[0] in WRITABLE_ROOTS
    )


def get_markdown_files(directory):
    """获取目录下所有 markdown 文件的信息"""
    files = []
    dir_path = (WORKSPACE_ROOT / directory).resolve()

    if not dir_path.exists():
        return files

    for file_path in dir_path.rglob("*.md"):
        if file_path.name == "README.md":
            continue

        relative_path = file_path.relative_to(WORKSPACE_ROOT)

        try:
            content = file_path.read_text(encoding="utf-8")
            title = file_path.stem
            for line in content.split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            stat = file_path.stat()
            files.append(
                {
                    "path": str(relative_path).replace("\\", "/"),
                    "name": file_path.stem,
                    "title": title,
                    "modified": stat.st_mtime,
                    "size": stat.st_size,
                    "editable": is_editable_markdown(file_path),
                }
            )
        except Exception as error:
            print(f"Error reading {file_path}: {error}")

    files.sort(key=lambda x: x["modified"], reverse=True)
    return files


def normalize_tags(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [
            item.strip()
            for item in value.replace("，", ",").split(",")
            if item.strip()
        ]
    return []


def normalize_context(value):
    context = value if isinstance(value, dict) else {}
    return {
        "project": str(context.get("project", "")).strip(),
        "target_path": str(context.get("target_path", "")).strip(),
        "tags": normalize_tags(context.get("tags", [])),
        "priority": str(context.get("priority", "")).strip(),
        "due_date": str(context.get("due_date", "")).strip(),
    }


def make_inbox_id():
    return f"{datetime.now().astimezone():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"


def create_inbox_item(kind, title, body, context=None, routing_hint=None):
    ensure_runtime_dirs()
    if kind not in VALID_KINDS:
        raise ValueError("Invalid kind")

    timestamp = now_iso()
    item_id = make_inbox_id()
    item = {
        "schema_version": 1,
        "id": item_id,
        "created_at": timestamp,
        "updated_at": timestamp,
        "source": "dashboard",
        "kind": kind,
        "title": str(title or "").strip(),
        "body": str(body or "").strip(),
        "status": "pending",
        "routing_hint": routing_hint or ROUTING_HINTS[kind],
        "context": normalize_context(context),
        "result": {
            "processed_at": "",
            "target_paths": [],
            "summary": "",
            "error": "",
        },
    }
    atomic_write_json(PENDING_DIR / f"{item_id}.json", item)
    return item


def read_inbox_json(path):
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            item = json.load(handle)
        item["_file"] = workspace_relative_path(path)
        return item
    except Exception as error:
        print(f"Error reading inbox item {path}: {error}")
        return None


def read_inbox_items(status):
    ensure_runtime_dirs()
    if status == "processed":
        paths = PROCESSED_DIR.rglob("*.json")
    elif status in INBOX_STATUS_DIRS:
        paths = INBOX_STATUS_DIRS[status].glob("*.json")
    else:
        return []

    items = [item for item in (read_inbox_json(path) for path in paths) if item]
    items.sort(
        key=lambda item: item.get("updated_at") or item.get("created_at") or "",
        reverse=True,
    )
    return items


def get_inbox_counts():
    return {
        "pending": len(read_inbox_items("pending")),
        "failed": len(read_inbox_items("failed")),
        "cancelled": len(read_inbox_items("cancelled")),
        "processed": len(read_inbox_items("processed")),
    }


def find_pending_inbox_file(item_id):
    ensure_runtime_dirs()
    for path in PENDING_DIR.glob("*.json"):
        item = read_inbox_json(path)
        if item and item.get("id") == item_id:
            return path, item
    return None, None


def find_inbox_file_any_status(item_id):
    ensure_runtime_dirs()
    search_roots = [PENDING_DIR, FAILED_DIR, CANCELLED_DIR, PROCESSED_DIR]
    for root in search_roots:
        paths = root.rglob("*.json") if root == PROCESSED_DIR else root.glob("*.json")
        for path in paths:
            item = read_inbox_json(path)
            if item and item.get("id") == item_id:
                return path, item
    return None, None


def backup_markdown_file(full_path):
    timestamp = datetime.now().astimezone()
    date_dir = timestamp.strftime("%Y-%m-%d")
    time_label = timestamp.strftime("%H%M%S")
    relative_path = full_path.relative_to(WORKSPACE_ROOT)
    backup_name = f"{full_path.stem}.{time_label}.{uuid.uuid4().hex[:6]}.bak{full_path.suffix}"
    backup_path = BACKUP_ROOT / date_dir / relative_path.parent / backup_name
    atomic_write_text(backup_path, full_path.read_text(encoding="utf-8"))
    return workspace_relative_path(backup_path)


def read_text_for_prompt(relative_path, max_chars=12000):
    path = WORKSPACE_ROOT / relative_path
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8-sig")
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[truncated]"
    return text


def compact_todos_for_prompt(max_items=24):
    data = load_todo_data()
    active_items = [
        item
        for item in data.get("items", [])
        if item.get("status") not in {"done", "cancelled"}
    ]
    active_items = active_items[:max_items]
    compact_items = []
    for item in active_items:
        compact_items.append(
            {
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "area": item.get("area", ""),
                "project": item.get("project", ""),
                "group": item.get("group", ""),
                "status": item.get("status", ""),
                "priority": item.get("priority", 1),
                "due_label": item.get("due_label", ""),
                "due_date": item.get("due_date", ""),
                "tags": item.get("tags", []),
                "note": item.get("note", ""),
                "checklist": item.get("checklist", []),
            }
        )
    return {
        "schema_version": data.get("schema_version", 1),
        "status_values": data.get("status_values", sorted(TODO_STATUS_VALUES)),
        "priority_values": data.get("priority_values", [1, 2, 3]),
        "active_items": compact_items,
    }


def compact_file_index(relative_dir, max_items=12):
    directory = WORKSPACE_ROOT / relative_dir
    if not directory.exists():
        return []
    files = []
    for path in directory.glob("*.md"):
        if path.name == "README.md":
            continue
        files.append(
            {
                "path": workspace_relative_path(path),
                "title": path.stem,
                "modified": path.stat().st_mtime,
            }
        )
    files.sort(key=lambda item: item["modified"], reverse=True)
    return [
        {"path": item["path"], "title": item["title"]}
        for item in files[:max_items]
    ]


def build_agent_prompt(items):
    pending_json = json.dumps(items, ensure_ascii=False, indent=2)
    allowed_paths = sorted(AGENT_WRITE_EXACT_PATHS)
    todo_context = json.dumps(compact_todos_for_prompt(), ensure_ascii=False, indent=2)
    idea_index = json.dumps(compact_file_index("notes/ideas"), ensure_ascii=False, indent=2)
    guidance_index = json.dumps(compact_file_index("guidance"), ensure_ascii=False, indent=2)
    prompt = f"""
You are helping maintain a local research-management workspace from Dashboard cache items.

Return one JSON object only. Do not include Markdown fences or prose outside JSON.
Never invent source evidence. Preserve existing JSON schemas, IDs, task grouping, and Chinese text.
Use UTF-8 Chinese text directly. Do not write mojibake or question-mark replacements.
Do not ask for shell commands. Only propose the allowed actions below.
Prefer granular actions such as upsert_todo. Do not use replace_json for tasks/todo.json unless a granular action cannot express the change.
Route by each cache item's kind first. Do not turn every input into a todo.

Allowed action types:
- upsert_todo: {{"type":"upsert_todo","item":{{"title":"...","area":"research|admin|personal","group":"today|week|later|backlog|admin","status":"todo","priority":1,"note":"...","tags":[],"checklist":[]}}}}
- write_idea: {{"type":"write_idea","title":"...","content":"markdown body","tags":["..."],"priority":"low|medium|high"}}
- write_guidance: {{"type":"write_guidance","title":"...","content":"markdown body","source":"advisor|meeting|collaborator|other"}}
- write_note: {{"type":"write_note","title":"...","content":"markdown body","folder":"notes|research"}}
- replace_json: {{"type":"replace_json","path":"tasks/todo.json","content":{{...}}}}
- write_text: {{"type":"write_text","path":"guidance/YYYY-MM-DD-short-title.md","content":"..."}}
- replace_text: {{"type":"replace_text","path":"guidance/README.md","content":"..."}}
- process_inbox: {{"type":"process_inbox","id":"...","target_paths":["..."],"summary":"..."}}

Writable exact paths: {json.dumps(allowed_paths, ensure_ascii=False)}
Writable prefixes: {json.dumps(AGENT_WRITE_PREFIXES, ensure_ascii=False)}

Output schema:
{{
  "summary": "short human-readable summary",
  "actions": [],
  "warnings": []
}}

Important local rules:
- tasks/todo.json is the only authoritative todo source.
- Keep similar work merged into task packages where practical.
- For reimbursement, purchase, travel, forms, or administrative chores, use area "admin" and group "admin".
- Always add process_inbox actions for cache items you handled.
- kind=idea: preserve it as an idea with write_idea. Do not add upsert_todo for speculative language such as "可以试试", "maybe", "possible", or "idea". Add upsert_todo only when the item explicitly asks to schedule/execute work (for example "今天做", "本周完成", "帮我安排任务", "截止").
- kind=guidance: first preserve it as guidance with write_guidance. Add upsert_todo only for clear action items extracted from the guidance.
- kind=note or freeform: use write_note when it is knowledge/context; use upsert_todo only when it is clearly a task.
- kind=file_edit_review: do not rewrite the edited file unless synchronization is needed; propose only necessary index/task/handoff updates.

Current compact todo context:
{todo_context}

Recent idea files:
{idea_index}

Recent guidance files:
{guidance_index}

Pending cache items:
{pending_json}
""".strip()
    return prompt


def safe_agent_write_path(raw_path):
    relative = str(raw_path or "").strip().replace("\\", "/").lstrip("/")
    if not relative:
        raise ValueError("Action path is required")
    full_path = resolve_workspace_path(relative)
    normalized = workspace_relative_path(full_path)
    is_allowed = normalized in AGENT_WRITE_EXACT_PATHS or any(
        normalized.startswith(prefix) for prefix in AGENT_WRITE_PREFIXES
    )
    if not is_allowed:
        raise ValueError(f"Agent action path is not allowed: {normalized}")
    if full_path.suffix.lower() not in {".md", ".json", ".txt"}:
        raise ValueError(f"Agent action file type is not allowed: {normalized}")
    return normalized, full_path


def safe_slug(value, fallback):
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "", text)
    text = text.strip("-")
    if not text:
        text = fallback
    return text[:60]


def dated_markdown_path(folder, title):
    date_prefix = now_iso()[:10]
    slug = safe_slug(title, uuid.uuid4().hex[:8])
    path = WORKSPACE_ROOT / folder / f"{date_prefix}-{slug}.md"
    counter = 2
    while path.exists():
        path = WORKSPACE_ROOT / folder / f"{date_prefix}-{slug}-{counter}.md"
        counter += 1
    return path


def normalize_agent_plan(plan):
    if not isinstance(plan, dict):
        raise ValueError("Agent response must be a JSON object")
    actions = plan.get("actions", [])
    if not isinstance(actions, list):
        raise ValueError("Agent response actions must be a list")
    for action in actions:
        if not isinstance(action, dict):
            raise ValueError("Each agent action must be an object")
        action_type = action.get("type")
        if action_type not in AGENT_ALLOWED_ACTIONS:
            raise ValueError(f"Unsupported agent action type: {action_type}")
    return {
        "summary": str(plan.get("summary", "")).strip(),
        "actions": actions,
        "warnings": plan.get("warnings", []) if isinstance(plan.get("warnings", []), list) else [],
    }


def mark_inbox_processed(item_id, target_paths, summary):
    path, item = find_pending_inbox_file(item_id)
    if not item:
        raise ValueError(f"Pending inbox item not found: {item_id}")
    timestamp = now_iso()
    item["status"] = "processed"
    item["updated_at"] = timestamp
    item["result"] = {
        "processed_at": timestamp,
        "target_paths": target_paths if isinstance(target_paths, list) else [],
        "summary": str(summary or "").strip(),
        "error": "",
    }
    month_dir = PROCESSED_DIR / datetime.now().astimezone().strftime("%Y-%m")
    destination = month_dir / path.name
    atomic_write_json(destination, item)
    path.unlink()
    return workspace_relative_path(destination)


def slugify_todo_id(title):
    text = str(title or "").strip().lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if ascii_text:
        return ascii_text[:48]
    return f"dashboard-task-{datetime.now().astimezone():%Y%m%d}-{uuid.uuid4().hex[:6]}"


def normalize_todo_item_for_agent(raw_item):
    if not isinstance(raw_item, dict):
        raise ValueError("upsert_todo item must be an object")
    title = str(raw_item.get("title", "")).strip()
    if not title:
        raise ValueError("upsert_todo item title is required")

    status = str(raw_item.get("status", "todo")).strip() or "todo"
    if status not in TODO_STATUS_VALUES:
        status = "todo"

    try:
        priority = int(raw_item.get("priority", 1))
    except (TypeError, ValueError):
        priority = 1
    priority = max(1, min(3, priority))

    area = str(raw_item.get("area", "research")).strip() or "research"
    group = str(raw_item.get("group", "backlog")).strip() or "backlog"
    if area == "admin":
        group = "admin"

    tags = normalize_tags(raw_item.get("tags", []))
    checklist = raw_item.get("checklist", [])
    if not isinstance(checklist, list):
        checklist = []

    return {
        "id": str(raw_item.get("id") or slugify_todo_id(title)).strip(),
        "title": title,
        "area": area,
        "project": str(raw_item.get("project", "")).strip(),
        "group": group,
        "status": status,
        "priority": priority,
        "due_label": str(raw_item.get("due_label", "")).strip(),
        "due_date": str(raw_item.get("due_date", "")).strip(),
        "tags": tags,
        "note": str(raw_item.get("note", "")).strip(),
        "checklist": [str(entry).strip() for entry in checklist if str(entry).strip()],
        "updated_at": now_iso(),
    }


def upsert_todo_item(raw_item):
    item = normalize_todo_item_for_agent(raw_item)
    data = load_todo_data()
    items = data.get("items", [])
    match_index = next(
        (
            index
            for index, existing in enumerate(items)
            if existing.get("id") == item["id"] or existing.get("title") == item["title"]
        ),
        None,
    )
    if match_index is None:
        item["created_at"] = now_iso()
        items.append(item)
    else:
        existing = items[match_index]
        item["created_at"] = existing.get("created_at", now_iso())
        items[match_index] = {**existing, **item}
    data["items"] = items
    write_json_file(TODO_FILE, data)
    return item["id"]


def write_structured_markdown(folder, title, content, prefix_lines=None):
    title = str(title or "").strip() or "Untitled"
    body = str(content or "").strip()
    path = dated_markdown_path(folder, title)
    lines = [f"# {title}", ""]
    if prefix_lines:
        lines.extend(prefix_lines)
        lines.append("")
    if body:
        lines.append(body)
    else:
        lines.append("_No content provided._")
    atomic_write_text(path, "\n".join(lines).rstrip() + "\n")
    return workspace_relative_path(path)


def apply_structured_content_action(action):
    action_type = action.get("type")
    if action_type == "write_idea":
        tags = action.get("tags", [])
        if not isinstance(tags, list):
            tags = normalize_tags(tags)
        priority = str(action.get("priority", "medium")).strip() or "medium"
        prefix = [
            f"- 日期: {now_iso()[:10]}",
            f"- 标签: {' '.join('#' + str(tag).strip() for tag in tags if str(tag).strip())}",
            f"- 优先级: {priority}",
            "",
            "## 描述",
        ]
        return write_structured_markdown(
            "notes/ideas",
            action.get("title", "New idea"),
            action.get("content", ""),
            prefix,
        )
    if action_type == "write_guidance":
        source = str(action.get("source", "other")).strip() or "other"
        prefix = [
            f"- 日期: {now_iso()[:10]}",
            f"- 来源: {source}",
            "",
            "## 记录",
        ]
        return write_structured_markdown(
            "guidance",
            action.get("title", "Guidance note"),
            action.get("content", ""),
            prefix,
        )
    if action_type == "write_note":
        folder = str(action.get("folder", "notes")).strip().replace("\\", "/")
        if folder not in {"notes", "research"}:
            folder = "notes"
        prefix = [
            f"- 日期: {now_iso()[:10]}",
            "",
            "## 内容",
        ]
        return write_structured_markdown(
            folder,
            action.get("title", "Research note"),
            action.get("content", ""),
            prefix,
        )
    raise ValueError(f"Unsupported structured content action: {action_type}")


def apply_agent_actions(plan):
    applied = []
    for action in normalize_agent_plan(plan)["actions"]:
        action_type = action.get("type")
        if action_type in {"write_text", "replace_text"}:
            normalized, full_path = safe_agent_write_path(action.get("path"))
            content = action.get("content")
            if not isinstance(content, str):
                raise ValueError(f"{action_type} content must be a string: {normalized}")
            if action_type == "replace_text" and not full_path.exists():
                raise ValueError(f"replace_text target does not exist: {normalized}")
            atomic_write_text(full_path, content)
            applied.append({"type": action_type, "path": normalized})
        elif action_type == "replace_json":
            normalized, full_path = safe_agent_write_path(action.get("path"))
            content = action.get("content")
            if not isinstance(content, (dict, list)):
                raise ValueError(f"replace_json content must be JSON data: {normalized}")
            if normalized == "tasks/todo.json" and isinstance(content, dict):
                content["last_updated"] = now_iso()[:10]
            atomic_write_json(full_path, content)
            applied.append({"type": action_type, "path": normalized})
        elif action_type == "upsert_todo":
            todo_id = upsert_todo_item(action.get("item", {}))
            applied.append({"type": action_type, "path": "tasks/todo.json", "todo_id": todo_id})
        elif action_type in {"write_idea", "write_guidance", "write_note"}:
            path = apply_structured_content_action(action)
            applied.append({"type": action_type, "path": path})
        elif action_type == "process_inbox":
            target = mark_inbox_processed(
                action.get("id"),
                action.get("target_paths", []),
                action.get("summary", ""),
            )
            applied.append({"type": action_type, "path": target})
    return applied


def save_agent_run(run_id, payload):
    path = AGENT_RUN_ROOT / f"{run_id}.json"
    atomic_write_json(path, payload)
    return path


def load_agent_run(run_id):
    path = AGENT_RUN_ROOT / f"{run_id}.json"
    if not path.exists():
        raise ValueError("Agent run not found")
    return read_json_file(path, {})

@app.route('/')
def index():
    """提供主页"""
    return send_from_directory('.', 'index.html')

@app.route('/api/ideas')
def get_ideas():
    """获取所有灵感"""
    files = get_markdown_files(CATEGORY_DIRS["ideas"])
    return jsonify(files)

@app.route('/api/tasks')
def get_tasks():
    """获取任务文件"""
    files = get_markdown_files(CATEGORY_DIRS["tasks"])
    return jsonify(files)


@app.route('/api/todos', methods=["GET"])
def get_todos():
    """获取结构化待办任务"""
    return jsonify(load_todo_data())


@app.route('/api/todos/<todo_id>', methods=["PATCH"])
def update_todo(todo_id):
    """更新结构化待办任务的轻量状态"""
    payload = request.get_json(silent=True) or {}
    next_status = payload.get("status")
    if next_status is not None and next_status not in TODO_STATUS_VALUES:
        return jsonify({"error": "Invalid status"}), 400

    data = load_todo_data()
    for item in data.get("items", []):
        if item.get("id") == todo_id:
            if next_status is not None:
                current_status = item.get("status", "todo")
                if next_status == "done" and current_status != "done":
                    item["previous_status"] = current_status
                elif current_status == "done" and next_status != "done":
                    item.pop("previous_status", None)
                item["status"] = next_status
            item["updated_at"] = now_iso()
            write_json_file(TODO_FILE, data)
            return jsonify(item)

    return jsonify({"error": "Todo not found"}), 404


@app.route("/api/agent/profiles", methods=["GET"])
def list_agent_profiles():
    return jsonify(load_api_profiles(include_keys=False))


@app.route("/api/agent/profiles", methods=["POST"])
def upsert_agent_profile():
    payload = request.get_json(silent=True) or {}
    data = load_api_profiles(include_keys=True)
    profiles = data.get("profiles", [])
    profile_id = str(payload.get("id", "")).strip()
    existing_index = next(
        (index for index, profile in enumerate(profiles) if profile.get("id") == profile_id),
        None,
    )
    existing = profiles[existing_index] if existing_index is not None else None

    try:
        profile = normalize_api_profile(payload, existing=existing)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    if existing_index is None:
        profiles.append(profile)
    else:
        profiles[existing_index] = profile
    data["profiles"] = profiles
    if not data.get("active_profile_id"):
        data["active_profile_id"] = profile["id"]
    save_api_profiles(data)
    return jsonify(load_api_profiles(include_keys=False))


@app.route("/api/agent/profiles/<profile_id>/active", methods=["PATCH"])
def activate_agent_profile(profile_id):
    data = load_api_profiles(include_keys=True)
    if not any(profile.get("id") == profile_id for profile in data.get("profiles", [])):
        return jsonify({"error": "API profile not found"}), 404
    data["active_profile_id"] = profile_id
    save_api_profiles(data)
    return jsonify(load_api_profiles(include_keys=False))


@app.route("/api/agent/profiles/<profile_id>/test", methods=["POST"])
def test_agent_profile(profile_id):
    profile = get_api_profile(profile_id)
    if not profile:
        return jsonify({"error": "API profile not found"}), 404
    try:
        text = call_agent_model(
            profile,
            'Return exactly this JSON object and nothing else: {"ok": true}',
        )
        return jsonify({"ok": True, "response_preview": text[:500]})
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/agent/profiles/<profile_id>", methods=["DELETE"])
def delete_agent_profile(profile_id):
    data = load_api_profiles(include_keys=True)
    profiles = [profile for profile in data.get("profiles", []) if profile.get("id") != profile_id]
    if len(profiles) == len(data.get("profiles", [])):
        return jsonify({"error": "API profile not found"}), 404
    data["profiles"] = profiles
    if data.get("active_profile_id") == profile_id:
        data["active_profile_id"] = profiles[0]["id"] if profiles else ""
    save_api_profiles(data)
    return jsonify(load_api_profiles(include_keys=False))


@app.route("/api/agent/process-inbox", methods=["POST"])
def process_inbox_with_agent():
    payload = request.get_json(silent=True) or {}
    apply_now = bool(payload.get("apply", False))
    run_id = None
    run = None

    try:
        if apply_now and payload.get("run_id"):
            run = load_agent_run(str(payload.get("run_id")))
            plan = run.get("plan", {})
            applied = apply_agent_actions(plan)
            run["status"] = "applied"
            run["applied_at"] = now_iso()
            run["applied_actions"] = applied
            save_agent_run(str(payload.get("run_id")), run)
            return jsonify({"run_id": payload.get("run_id"), "plan": plan, "applied_actions": applied})

        profile = get_api_profile(payload.get("profile_id"))
        if not profile:
            return jsonify({"error": "No API profile configured"}), 400

        item_ids = payload.get("item_ids")
        pending_items = read_inbox_items("pending")
        if isinstance(item_ids, list) and item_ids:
            wanted = {str(item_id) for item_id in item_ids}
            pending_items = [item for item in pending_items if item.get("id") in wanted]
        if not pending_items:
            return jsonify({"error": "No pending inbox items to process"}), 400

        run_id = uuid.uuid4().hex[:12]
        prompt = build_agent_prompt(pending_items)
        run = {
            "schema_version": 1,
            "id": run_id,
            "created_at": now_iso(),
            "profile_id": profile.get("id", ""),
            "profile_name": profile.get("name", ""),
            "item_ids": [item.get("id") for item in pending_items],
            "status": "calling",
            "prompt_chars": len(prompt),
        }
        save_agent_run(run_id, run)
        raw_response = call_agent_model(profile, prompt)
        plan = normalize_agent_plan(extract_json_object(raw_response))
        run["status"] = "preview"
        run["plan"] = plan
        run["response_chars"] = len(raw_response)
        applied = []
        if apply_now:
            applied = apply_agent_actions(plan)
            run["status"] = "applied"
            run["applied_at"] = now_iso()
            run["applied_actions"] = applied
        save_agent_run(run_id, run)
        return jsonify({"run_id": run_id, "plan": plan, "applied_actions": applied})
    except Exception as error:
        if run_id and run is not None:
            run["status"] = "failed"
            run["failed_at"] = now_iso()
            run["error"] = str(error)
            save_agent_run(run_id, run)
        return jsonify({"error": str(error), "run_id": run_id}), 500

@app.route('/api/guidance')
def get_guidance():
    """获取导师指导记录"""
    files = get_markdown_files(CATEGORY_DIRS["guidance"])
    return jsonify(files)

@app.route('/api/notes')
def get_notes():
    """获取研究笔记"""
    files = get_markdown_files(CATEGORY_DIRS["notes"])
    return jsonify(files)


@app.route("/api/inbox", methods=["GET"])
def list_inbox():
    """获取 Dashboard 缓存区条目"""
    status = request.args.get("status", "pending")
    if status == "all":
        items = []
        for item_status in ("pending", "failed", "cancelled", "processed"):
            items.extend(read_inbox_items(item_status))
        items.sort(
            key=lambda item: item.get("updated_at") or item.get("created_at") or "",
            reverse=True,
        )
    elif status in {"pending", "failed", "cancelled", "processed"}:
        items = read_inbox_items(status)
    else:
        return jsonify({"error": "Invalid status"}), 400

    return jsonify({"counts": get_inbox_counts(), "items": items})


@app.route("/api/inbox", methods=["POST"])
def create_inbox():
    """写入一条待 Agent 接管的原始输入"""
    payload = request.get_json(silent=True) or {}
    kind = str(payload.get("kind", "freeform")).strip()
    if kind not in VALID_KINDS:
        return jsonify({"error": "Invalid kind"}), 400

    title = str(payload.get("title", "")).strip()
    body = str(payload.get("body", "")).strip()
    if not title and not body:
        return jsonify({"error": "Title or body is required"}), 400

    try:
        item = create_inbox_item(
            kind=kind,
            title=title,
            body=body,
            context=payload.get("context", {}),
            routing_hint=payload.get("routing_hint") or ROUTING_HINTS[kind],
        )
        return jsonify(item), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/inbox/<item_id>", methods=["PATCH"])
def update_inbox(item_id):
    """更新 pending 状态的缓存条目"""
    path, item = find_pending_inbox_file(item_id)
    if not item:
        return jsonify({"error": "Pending inbox item not found"}), 404

    payload = request.get_json(silent=True) or {}
    if "kind" in payload:
        kind = str(payload.get("kind", "")).strip()
        if kind not in VALID_KINDS:
            return jsonify({"error": "Invalid kind"}), 400
        item["kind"] = kind
        item["routing_hint"] = payload.get("routing_hint") or ROUTING_HINTS[kind]

    if "title" in payload:
        item["title"] = str(payload.get("title", "")).strip()
    if "body" in payload:
        item["body"] = str(payload.get("body", "")).strip()
    if "context" in payload:
        item["context"] = normalize_context(payload.get("context", {}))
    if "routing_hint" in payload and "kind" not in payload:
        item["routing_hint"] = str(payload.get("routing_hint", "")).strip()

    if not item.get("title") and not item.get("body"):
        return jsonify({"error": "Title or body is required"}), 400

    item["updated_at"] = now_iso()
    atomic_write_json(path, item)
    return jsonify(item)


@app.route("/api/inbox/<item_id>", methods=["DELETE"])
def cancel_inbox(item_id):
    """取消 pending 条目，但保留记录"""
    hard_delete = request.args.get("hard") in {"1", "true", "yes"}
    if hard_delete:
        path, item = find_inbox_file_any_status(item_id)
        if not item:
            return jsonify({"error": "Inbox item not found"}), 404
        path.unlink()
        return jsonify({"deleted": True, "id": item_id, "path": workspace_relative_path(path)})

    path, item = find_pending_inbox_file(item_id)
    if not item:
        return jsonify({"error": "Pending inbox item not found"}), 404

    item["status"] = "cancelled"
    item["updated_at"] = now_iso()
    destination = CANCELLED_DIR / path.name
    atomic_write_json(destination, item)
    path.unlink()
    return jsonify(item)

@app.route('/api/file')
def get_file():
    """获取指定文件内容"""
    file_path = request.args.get('path', '')
    if not file_path:
        return jsonify({'error': 'No path provided'}), 400

    # 安全检查
    try:
        full_path = resolve_workspace_path(file_path)
    except ValueError as error:
        return jsonify({'error': str(error)}), 403

    if full_path.suffix.lower() != ".md":
        return jsonify({'error': 'Only markdown files can be opened'}), 400

    try:
        full_path.relative_to(WORKSPACE_ROOT)
    except ValueError:
        return jsonify({'error': 'Invalid path'}), 403

    if not full_path.exists() or not full_path.is_file():
        return jsonify({'error': 'File not found'}), 404

    try:
        stat = full_path.stat()
        content = full_path.read_text(encoding='utf-8')
        return jsonify({
            'path': file_path,
            'content': content,
            'name': full_path.name,
            'modified': stat.st_mtime,
            'editable': is_editable_markdown(full_path)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/file/save", methods=["POST"])
def save_file():
    """安全保存允许范围内的 Markdown 文件"""
    payload = request.get_json(silent=True) or {}
    file_path = payload.get("path", "")
    content = payload.get("content", "")
    expected_mtime = payload.get("expected_mtime")
    needs_agent_review = bool(payload.get("needs_agent_review", False))

    try:
        full_path = resolve_workspace_path(file_path)
    except ValueError as error:
        return jsonify({"error": str(error)}), 403

    if not is_editable_markdown(full_path):
        return jsonify({"error": "This file is not editable from Dashboard"}), 403
    if not full_path.exists() or not full_path.is_file():
        return jsonify({"error": "File not found"}), 404
    if not isinstance(content, str):
        return jsonify({"error": "Content must be a string"}), 400

    current_mtime = full_path.stat().st_mtime
    if expected_mtime is not None:
        try:
            expected_mtime = float(expected_mtime)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid expected_mtime"}), 400
        if abs(current_mtime - expected_mtime) > 0.01:
            return jsonify(
                {
                    "error": "File changed on disk. Reload before saving.",
                    "current_mtime": current_mtime,
                }
            ), 409

    try:
        backup_path = backup_markdown_file(full_path)
        atomic_write_text(full_path, content)
        next_mtime = max(time.time(), current_mtime + 0.05)
        os.utime(full_path, (next_mtime, next_mtime))
        stat = full_path.stat()

        review_item = None
        if needs_agent_review:
            review_item = create_inbox_item(
                kind="file_edit_review",
                title=f"Review file edit: {file_path}",
                body=(
                    f"Dashboard edited `{file_path}`. "
                    "Review whether indexes, README files, or task state need synchronization."
                ),
                context={"target_path": file_path},
            )

        return jsonify(
            {
                "path": file_path,
                "modified": stat.st_mtime,
                "backup_path": backup_path,
                "review_item": review_item,
            }
        )
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@app.route('/api/structure')
def get_structure():
    """获取工作区整体结构"""
    inbox_counts = get_inbox_counts()
    structure = {
        'ideas': len(get_markdown_files(CATEGORY_DIRS["ideas"])),
        'tasks': active_todo_count(),
        'guidance': len(get_markdown_files(CATEGORY_DIRS["guidance"])),
        'notes': len(get_markdown_files(CATEGORY_DIRS["notes"])),
        'inbox_pending': inbox_counts["pending"],
        'inbox_failed': inbox_counts["failed"],
        'inbox_cancelled': inbox_counts["cancelled"],
        'inbox_processed': inbox_counts["processed"]
    }
    return jsonify(structure)

if __name__ == '__main__':
    ensure_runtime_dirs()
    print("🚀 科研管理仪表板启动中...")
    print(f"📁 工作区: {WORKSPACE_ROOT}")
    print("🌐 访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    app.run(host='127.0.0.1', port=5000, debug=True)
