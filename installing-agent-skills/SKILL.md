---
name: installing-skills
description: Installs agent skills from git repositories using `npx add-skill`. Use when user wants to add, install, get, or download skills from GitHub, GitLab, or git URLs. Supports Claude Code, Cursor, Codex, and 20+ other agents. Guides global vs project-level decisions.
---

# Installing Skills

## Pre-Installation Framework

Before installing any skill, ask yourself:

- **Purpose**: What specific capability gap are you trying to fill? (Don't install "just to try" - add a note explaining WHY)
- **Scope**: Is this for personal use or team workflow? Global = everywhere you work, Project = shared via repo
- **Trust**: Do you know this repo/skill author? Skills have system access (bash, read/write files, network requests). Malicious skills can steal credentials or damage your system
- **Impact**: Will this override existing behavior? Check if you already have a skill with similar description
- **Verification**: Have you reviewed the SKILL.md content? Description alone can be misleading

## Decision Tree

```
Need a skill?
├─ Know exact skill path? → npx add-skill <repo>/tree/main/skills/<name>
├─ Want to browse first? → npx add-skill owner/repo --list
├─ Installing specific skills? → npx add-skill owner/repo --skill name1 --skill name2
└─ Installing all from repo? → npx add-skill owner/repo
    ├─ Personal use? → add --global
    └─ Team/project? → no flag (project-level)
    └─ CI/automation? → add -y and prefer --skill to avoid surprises
```

## NEVER Do

- **NEVER install globally for project-specific workflows** — creates hard-to-debug conflicts when you clone the repo elsewhere, and your team won't get the skill
- **NEVER install from unknown repos without `--list` first** — skills can execute bash commands, read/write files, and make network requests. Malicious skills can steal credentials or damage your system
- **NEVER assume skill description matches actual behavior** — skills can have misleading descriptions. Always review the SKILL.md content before installing
- **NEVER install a skill just to "try it"** — add a comment or note explaining WHY you're installing it. Future-you will forget
- **NEVER install from forks without reviewing changes** — forks can inject malicious modifications even if original repo was trustworthy
- **NEVER overwrite an existing skill without explicit confirmation** — prefer `--list` + `--skill` to disambiguate which version you want
- **NEVER assume single-agent** — use `-a` to target specific agents if you have multiple installed

## Skill Discovery Strategy

Finding the right skill follows this pattern:

1. **Identify capability gap first** — Be specific: "I need X feature" not "I need more skills"
2. **Search curated sources** — Check [agentskills.io](https://agentskills.io) or verified collections first
3. **Review SKILL.md content** — Description alone is misleading. Read the actual instruction content
4. **Test in project directory first** — Easier to remove if it doesn't work
5. **Promote to global only if used in 3+ projects** — Prevents skill bloat

### Multi-Agent Support

```bash
# Install to specific agents
npx add-skill owner/repo -a claude-code -a cursor

# Auto-detects installed agents if not specified
npx add-skill owner/repo
```

### Global vs Project-Level

| Scenario             | Recommendation | Why                  |
| -------------------- | -------------- | -------------------- |
| Personal productivity | `--global`     | Available everywhere |
| Team workflows       | Project-level  | Shared via repo      |
| Testing a skill      | Project-level  | Easy to remove       |

### CI / Automation

Use `-y` for non-interactive runs and always specify `--skill` to avoid installing unintended skills.

## Troubleshooting

| Problem                | Fix                                                |
| ---------------------- | -------------------------------------------------- |
| "Skill already exists" | Remove existing skill file first, or use `--skill` to target specific skill |
| "No skills found"      | Check repo has valid SKILL.md with `name` + `description` in YAML frontmatter |
| Skill not triggering   | Verify description includes your use case keywords and scenarios |
| Installation failed    | Check network, repo access, and that target agent directory exists and is writable |
| Verify installation    | Check the target agent's skills directory (project: `.agent/skills/`, global: `~/.config/opencode/skills/`) |
| Remove a skill         | Delete the skill directory from the target agent's skills folder |

### Quality Sources

- [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) — Curated collection
- [agentskills.io](https://agentskills.io) — Specification and examples
