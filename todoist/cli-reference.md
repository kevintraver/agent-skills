# Todoist CLI Reference

Complete reference for the `td` command. Run `td --help` or `td <command> --help` for full syntax.

## Authentication

```bash
td auth login              # OAuth flow (opens browser)
td auth token "TOKEN"      # Set API token directly
td auth status             # Check current auth
td auth logout             # Clear credentials
```

Environment variable: `TODOIST_API_TOKEN`

## Quick Commands

| Command | Description |
|---------|-------------|
| `td add "text"` | Quick add with natural language parsing |
| `td today` | Tasks due today + overdue (your tasks only) |
| `td upcoming [days]` | Next N days (default: 7) |
| `td inbox` | Inbox tasks |
| `td completed` | Recently completed tasks |

## Task Management

### Listing
```bash
td task list                           # All tasks
td task list --project "Work"          # Filter by project
td task list --label urgent            # Filter by label
td task list --priority p1             # Filter by priority
td task list --due overdue             # Overdue only
td task list --assignee "john@..."     # By assignee
td task list --any-assignee            # All assignees (team view)
```

### Creating
```bash
td task add --content "Task name" --due "tomorrow" --priority p1
td task add --content "Task" --project "Work" --section "To Do"

# Quick add parses natural language:
td add "Call dentist tomorrow at 3pm #Personal p2 @calls"
```

### Modifying
```bash
td task update id:123 --content "New name"
td task update id:123 --priority p2 --due "next monday"
td task move id:123 --project "Work" --section "Done"
```

### Completing (ALWAYS use id: for safety)
```bash
td task complete id:123456789
td task uncomplete id:123456789
```

### Viewing
```bash
td task view "task name"      # Fuzzy match OK for viewing
td task view id:123           # Explicit ID
td task browse id:123         # Open in browser
```

### Deleting (ALWAYS use id: for safety)
```bash
td task delete id:123 --yes   # Skip confirmation
```

## Project Management

```bash
td project list
td project create --name "New Project" --color red --view board
td project update id:123 --name "Renamed"
td project delete id:123 --yes
td project archive id:123
```

View styles: `list`, `board`, `calendar`

## Section Management

```bash
td section list --project "Work"
td section create --project "Work" --name "In Progress"
td section update id:123 --name "Done"
td section delete id:123 --yes
```

## Label Management

```bash
td label list
td label create --name "urgent" --color red
td label update id:123 --name "critical"
td label delete id:123 --yes
```

## Comment Management

```bash
td comment list --task id:123
td comment add --task id:123 --content "Note here"
td comment update id:456 --content "Updated note"
td comment delete id:456 --yes
```

## Output Formats

All list commands support:
```bash
--json          # JSON output
--ndjson        # Newline-delimited JSON (for streaming)
--full          # Include all fields
--limit N       # Limit results
--all           # No limit (careful with large datasets)
```

## Reference Syntax

| Syntax | Example | Use |
|--------|---------|-----|
| `id:` | `id:123456789` | Explicit ID (required for destructive ops) |
| Name | `"My Task"` | Fuzzy match by name |
| `@label` | `@urgent` | Label reference |
| `#project` | `#Work` | Project in quick add |

## Natural Language (Quick Add)

The `td add` command parses natural language:

```bash
td add "Buy milk tomorrow"              # Due date
td add "Meeting at 3pm"                 # Time
td add "Report every monday"            # Recurring
td add "Task #Work"                     # Project
td add "Task @urgent @review"           # Labels
td add "Task p1"                        # Priority
td add "Task !!"                        # Priority (!! = p1, ! = p2)
```

Combined:
```bash
td add "Weekly report every friday #Work p2 @reports"
```

## Gotchas

1. **`td today` filters by assignee** — use `--any-assignee` for team view
2. **Fuzzy matching is dangerous** — always use `id:` for complete/delete/uncomplete
3. **`--yes` flag** — required for non-interactive deletion in scripts
4. **Recurring task completion** — completes THIS occurrence, schedules next
5. **Output is paginated** — use `--all` to get everything (may be slow)
