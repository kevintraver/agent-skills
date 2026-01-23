---
name: todoist
description: Manage tasks with Todoist using CLI (td command) and MCP tools. Use when user mentions Todoist, task management, to-do lists, creating/finding/completing tasks, daily planning, or team assignments.
---

# Todoist Task Management

Expert knowledge for managing tasks with Todoist CLI (`td`) and MCP tools.

## When to Use CLI vs MCP

**Use CLI (`td`)** for:
- Quick single-task operations from terminal
- Interactive workflows where you see output immediately
- When MCP server is not configured

**Use MCP tools** for:
- Batch operations (multiple tasks at once)
- Team assignments (requires validation workflow)
- Complex searches with multiple filters
- When working in an AI-assisted context

## Expert Knowledge

### dueString vs deadlineDate — The Critical Difference

| Field | Meaning | Use When |
|-------|---------|----------|
| `dueString` | Flexible target date | "I want to do this by Friday" |
| `deadlineDate` | Hard immovable constraint | "Contract MUST be signed by Dec 31" |

Todoist treats these differently in views, reminders, and rescheduling. NEVER use `deadlineDate` for soft targets.

### The `id:` Prefix Trap (CLI)

These CLI commands REQUIRE explicit `id:` prefix for safety:
- `td task complete id:123` — fuzzy match may complete wrong task
- `td task uncomplete id:123` — ALWAYS requires explicit ID
- `td task delete id:123` — dangerous with fuzzy match

For viewing/reading, fuzzy match is fine: `td task view "groceries"`

### Assignment Validation Pattern

MCP **silently succeeds** even if user doesn't exist in project — the task just won't be assigned.

**ALWAYS follow this sequence:**
```
1. find-project-collaborators(projectId) → verify user exists
2. THEN add-tasks with responsibleUser or manage-assignments
```

### Special String Values (MCP Only)

These are MCP-specific — don't use in CLI:
- `"remove"` — clears deadline (not `null`)
- `"unassign"` — removes assignment (not `null`)
- `"inbox"` — special projectId for user's inbox
- `"today"` — dynamic date that auto-includes overdue tasks

### Priority Semantics

- `p1` = Urgent (red) — needs attention today
- `p2` = High (orange) — important but not urgent
- `p3` = Medium (blue) — normal importance
- `p4` = None (no color) — default, backlog items

### Recurring Tasks

Completing a recurring task marks **that occurrence** done and schedules the next one. It doesn't delete the task or stop the recurrence.

### Pagination

Large result sets are paginated. Use `--all` flag (CLI) or `cursor` parameter (MCP) to get all results.

## Thinking Framework

### Before Creating a Task, Ask:

1. **One-off or recurring?** — Recurring tasks need `dueString` with recurrence pattern
2. **Project or inbox?** — Use inbox for quick capture, projects for organized work
3. **Deadline or target?** — Hard constraint = `deadlineDate`, soft target = `dueString`
4. **Needs assignment?** — If team task, validate collaborators first

### Before Bulk Operations, Ask:

1. **Do I have the right IDs?** — Search first, then operate on results
2. **Is this reversible?** — Deletion is permanent, completion can be undone
3. **Should I dry-run?** — Use `dryRun: true` for manage-assignments

### Daily Planning Decision Tree

```
Start with: What's my scope today?
├── Personal only → td today (or find-tasks-by-date with 'today')
├── Full team view → td today --any-assignee
└── Planning ahead → td upcoming 7 (or find-tasks-by-date with daysCount)

Then check overload:
├── >10 tasks today? → Reprioritize or reschedule lowest priority
└── Overdue showing? → Address FIRST (included in "today" automatically)

For batch changes:
└── Use MCP: find-tasks-by-date → update-tasks to reprioritize
```

## Quick Reference

### CLI Authentication
```bash
td auth login              # OAuth browser flow (recommended)
td auth token "TOKEN"      # Manual API token
export TODOIST_API_TOKEN   # Environment variable
td auth status             # Verify authentication
```

### Common CLI Patterns
```bash
# Quick add with natural language
td add "Buy groceries tomorrow #Shopping p2"

# View today (personal)
td today

# View with full details
td task list --project "Work" --full

# Safe completion (always use id:)
td task complete id:123456789

# Move task to different project/section
td task move id:123 --project "Work" --section "In Progress"
```

### Common MCP Patterns
```
# Daily tasks (includes overdue)
find-tasks-by-date(startDate: 'today')

# Search and complete
find-tasks(searchText: '...') → complete-tasks(taskIds: [...])

# Safe assignment workflow
find-project-collaborators(projectId) → add-tasks(responsibleUser: '...')

# Bulk assignment (max 50)
manage-assignments(operation: 'assign', taskIds: [...], dryRun: true)
```

## CLI Reference

For complete CLI command syntax, see [cli-reference.md](cli-reference.md).
Load only when user explicitly asks for CLI command details.
