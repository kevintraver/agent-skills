# Agent Instructions

One folder per skill, each with a `SKILL.md`. Installed copies live in `~/.agents/skills/<skill>`, made by `npx skills`.

## Commands
| Task | Command |
|------|---------|
| Validate a skill | `python3 ~/.claude/skills/skill-creator/scripts/quick_validate.py <skill>` |
| Reinstall a skill from this repo | `npx -y skills add ~/.kevintraver/agents/skills -g -s <skill> -a claude-code codex -y` |

## Rules
| Rule | Enforced by |
|------|-------------|
| Every `SKILL.md` has valid frontmatter (no `: ` in an unquoted description) | Local `.git/hooks/pre-commit` (this machine only, not committed) blocks the commit |
| `cleanup-screenshot/SKILL.md` describes outcomes, not commands or tools | Local `.git/hooks/pre-commit` blocks the commit |
| Reinstall a skill after committing a change to it | Local `.git/hooks/post-commit` prints the reinstall command (the user runs it) |
| Pass `-a` with `npx skills add -g` | Nothing; without it, skills 1.7.4 fails on PromptScript (fixed upstream in vercel-labs/skills#2547, unreleased) |

## Commits
- Conventional Commits, scoped to the skill: `feat(cleanup-screenshot): ...`
