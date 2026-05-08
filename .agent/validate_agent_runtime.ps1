$ErrorActionPreference = "Stop"

function Assert-Exists {
    param(
        [string]$Path
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing required path: $Path"
    }
}

function Assert-Contains {
    param(
        [string]$Path,
        [string]$Pattern
    )
    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if ($content -notmatch $Pattern) {
        throw "Expected pattern not found in ${Path}: $Pattern"
    }
}

function Assert-NotContains {
    param(
        [string]$Path,
        [string]$Pattern
    )
    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if ($content -match $Pattern) {
        throw "Forbidden pattern found in ${Path}: $Pattern"
    }
}

$requiredPaths = @(
    ".agent/README_agent_runtime.md",
    ".agent/profile.md",
    ".agent/core/core_rules.md",
    ".agent/core/preflight_checklist.md",
    ".agent/core/task_router.md",
    ".agent/core/output_templates.md",
    ".agent/core/structure_contract.md",
    ".agent/protocols/literature_review.md",
    ".agent/protocols/coding_tasks.md",
    ".agent/protocols/experiment_recording.md",
    ".agent/protocols/html_ppt_generation.md",
    ".agent/protocols/file_management.md",
    ".agent/runtime/current_task.md",
    ".agent/runtime/handoff_note.md",
    ".agent/runtime/active_context.md",
    ".agent/memory/tasks.json",
    ".agent/memory/experience.json",
    ".agent/adapters/model_notes.md",
    "tasks/todo.json",
    "tasks/projects.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".github/copilot-instructions.md"
)

foreach ($path in $requiredPaths) {
    Assert-Exists -Path $path
}

$bootstrapFiles = @("CLAUDE.md", "AGENTS.md", ".github/copilot-instructions.md")
foreach ($file in $bootstrapFiles) {
    Assert-Contains -Path $file -Pattern "BOOTSTRAP_ONLY"
    Assert-Contains -Path $file -Pattern "\.agent/README_agent_runtime\.md"
    Assert-Contains -Path $file -Pattern "\.agent/core/structure_contract\.md"
    Assert-NotContains -Path $file -Pattern "下次会话重点提醒"
}

$forbiddenModelRuleNames = Get-ChildItem -LiteralPath ".agent" -Recurse -File -ErrorAction Stop |
    Where-Object {
        $_.FullName -notmatch [regex]::Escape((Resolve-Path ".agent/adapters/model_notes.md").Path) -and
        $_.Name -match "^(?i)(gemini|claude|copilot|codex).*(rules|instructions|prompt).*"
    }

if ($forbiddenModelRuleNames) {
    $names = $forbiddenModelRuleNames | ForEach-Object { $_.FullName }
    throw "Forbidden model-specific rule files detected:`n$($names -join "`n")"
}

Get-Content -LiteralPath ".agent/memory/tasks.json" -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath ".agent/memory/experience.json" -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath "tasks/todo.json" -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null

Write-Output "Agent runtime structure validation passed."
