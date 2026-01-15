---
name: manage-agent-skills
description: Manage skills and global rules across AI coding agents (Claude Code, OpenCode, Codex CLI, Cursor, Gemini CLI). Use when installing, symlinking, or organizing skills across multiple tools.
---

# Manage Agent Skills

Manage skills and global rules across multiple AI coding agents from a single source.

## Overview

This skill helps you:
- Install skills to multiple agents at once
- Symlink skills from a central repository
- Understand where each tool stores skills and rules
- Keep configurations in sync across tools

## Tool Reference

### Claude Code

| Type | Location |
|------|----------|
| Global Rules | `~/.claude/CLAUDE.md` |
| Global Skills | `~/.claude/skills/<skill-name>/SKILL.md` |
| Project Rules | `.claude/CLAUDE.md` or `CLAUDE.md` |
| Project Skills | `.claude/skills/<skill-name>/SKILL.md` |

**Notes:**
- Also checks `.claude/rules/*.md` for modular project rules
- `CLAUDE.local.md` for personal project settings (auto-gitignored)
- Walks up directory tree to find rules

**Docs:** [Memory](https://code.claude.com/docs/en/memory) | [Skills](https://code.claude.com/docs/en/skills)

### OpenCode

| Type | Location |
|------|----------|
| Global Rules | `~/.config/opencode/AGENTS.md` |
| Global Skills | `~/.config/opencode/skill/<skill-name>/SKILL.md` |
| Project Rules | `AGENTS.md` (or falls back to `CLAUDE.md`) |
| Project Skills | `.opencode/skill/<skill-name>/SKILL.md` |

**Notes:**
- Falls back to Claude Code locations if native locations don't exist
- Config file at `~/.config/opencode/opencode.json`

**Docs:** [Rules](https://opencode.ai/docs/rules/) | [Skills](https://opencode.ai/docs/skills/)

### Codex CLI (OpenAI)

| Type | Location |
|------|----------|
| Global Rules | `~/.codex/AGENTS.md` (or `AGENTS.override.md`) |
| Global Skills | `~/.codex/skills/<skill-name>/SKILL.md` |
| Project Rules | `AGENTS.md` at project root |
| Project Skills | `.codex/skills/<skill-name>/SKILL.md` |

**Notes:**
- `AGENTS.override.md` takes precedence over `AGENTS.md`
- System skills in `~/.codex/skills/.system/`
- Config file at `~/.codex/config.toml`
- Set `CODEX_HOME` env var to change base directory

**Docs:** [AGENTS.md](https://developers.openai.com/codex/guides/agents-md/) | [Skills](https://developers.openai.com/codex/skills/)

### Cursor (IDE & CLI)

| Type | Location |
|------|----------|
| Global Rules | Cursor Settings > General > Rules for AI (UI only) |
| Global Skills | `~/.cursor/skills/<skill-name>/SKILL.md` |
| Project Rules | `.cursor/rules/*.mdc` or `AGENTS.md` |
| Project Skills | `.cursor/skills/<skill-name>/SKILL.md` |

**Notes:**
- CLI reads `AGENTS.md` and `CLAUDE.md` at project root
- Legacy `.cursorrules` file still supported
- Also checks `~/.claude/skills/` as fallback
- No file-based global rules (must use Settings UI)

**Docs:** [Rules](https://cursor.com/docs/context/rules) | [Skills](https://cursor.com/docs/context/skills)

### Gemini CLI

| Type | Location |
|------|----------|
| Global Rules | `~/.gemini/GEMINI.md` |
| Global Skills | `~/.gemini/skills/<skill-name>/SKILL.md` |
| Project Rules | `GEMINI.md` or `AGENTS.md` at project root |
| Project Skills | `.gemini/skills/<skill-name>/SKILL.md` |

**Notes:**
- Scans current and all parent directories for rules
- Precedence: Project > User > Extension skills
- Also supports `AGENT.md` filename

**Docs:** [Configuration](https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/configuration.md) | [Skills](https://geminicli.com/docs/cli/skills/)

## Quick Reference Table

| Tool | Global Rules | Global Skills |
|------|--------------|---------------|
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/skills/` |
| OpenCode | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/skill/` |
| Codex CLI | `~/.codex/AGENTS.md` | `~/.codex/skills/` |
| Cursor | Settings UI only | `~/.cursor/skills/` |
| Gemini CLI | `~/.gemini/GEMINI.md` | `~/.gemini/skills/` |

## Common Workflows

### Install a skill to all agents

Given a skill at `~/my-skills/my-skill/`:

```bash
# Create symlinks for all agents
ln -s ~/my-skills/my-skill ~/.claude/skills/my-skill
ln -s ~/my-skills/my-skill ~/.config/opencode/skill/my-skill
ln -s ~/my-skills/my-skill ~/.codex/skills/my-skill
ln -s ~/my-skills/my-skill ~/.cursor/skills/my-skill
ln -s ~/my-skills/my-skill ~/.gemini/skills/my-skill
```

### Set up global rules from a single source

Given rules at `~/my-rules/AGENTS.md`:

```bash
# Symlink to all agents that support file-based global rules
ln -s ~/my-rules/AGENTS.md ~/.claude/CLAUDE.md
ln -s ~/my-rules/AGENTS.md ~/.config/opencode/AGENTS.md
ln -s ~/my-rules/AGENTS.md ~/.codex/AGENTS.md
ln -s ~/my-rules/AGENTS.md ~/.gemini/GEMINI.md
# Note: Cursor requires manual paste into Settings UI
```

### List all installed skills

```bash
echo "=== Claude Code ===" && ls ~/.claude/skills/ 2>/dev/null
echo "=== OpenCode ===" && ls ~/.config/opencode/skill/ 2>/dev/null
echo "=== Codex CLI ===" && ls ~/.codex/skills/ 2>/dev/null
echo "=== Cursor ===" && ls ~/.cursor/skills/ 2>/dev/null
echo "=== Gemini CLI ===" && ls ~/.gemini/skills/ 2>/dev/null
```

### Remove a skill from all agents

```bash
SKILL_NAME="my-skill"
rm -f ~/.claude/skills/$SKILL_NAME
rm -f ~/.config/opencode/skill/$SKILL_NAME
rm -f ~/.codex/skills/$SKILL_NAME
rm -f ~/.cursor/skills/$SKILL_NAME
rm -f ~/.gemini/skills/$SKILL_NAME
```

### Ensure all directories exist

```bash
mkdir -p ~/.claude/skills
mkdir -p ~/.config/opencode/skill
mkdir -p ~/.codex/skills
mkdir -p ~/.cursor/skills
mkdir -p ~/.gemini/skills
```

## SKILL.md Format

All tools use the same SKILL.md format:

```markdown
---
name: skill-name
description: When to use this skill and what it does
---

# Skill Title

Instructions for the agent...
```

Required frontmatter fields:
- `name`: Lowercase, hyphens only (e.g., `my-skill`)
- `description`: Triggers skill activation when request matches

Optional frontmatter fields (vary by tool):
- `allowed-tools`: Restrict which tools the skill can use
- `model`: Specify a particular model
- `user-invocable`: Show/hide from slash command menu

## Best Practices

1. **Central repository**: Keep skills in one location (e.g., `~/.agent-skills/`) and symlink to each tool
2. **Version control**: Track your skills in a git repo for backup and sharing
3. **Naming**: Use lowercase with hyphens (e.g., `code-review`, `test-runner`)
4. **Description**: Write clear descriptions so agents know when to activate the skill
5. **Modularity**: One skill per capability, keep SKILL.md under 500 lines
