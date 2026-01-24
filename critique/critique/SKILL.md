---
name: critique
description: Enhanced terminal UI for git diff review with syntax highlighting and web sharing. Use when reviewing code changes, comparing branches, sharing diffs with teammates, or getting AI explanations of changes. Triggers on "review my changes", "show the diff", "compare branches", "share this diff", "explain these changes", or when user wants a better diff viewer than git diff.
---

# Critique

Enhanced diff viewer. Requires Bun: `bunx critique` or `bun install -g critique`.

## When to Use Critique vs Git Diff

| Scenario | Use | Why |
|----------|-----|-----|
| Quick terminal check | `git diff` | Faster, no deps |
| Reviewing before commit | `critique --staged` | Syntax highlighting helps catch issues |
| Understanding complex changes | `critique` | Word-level diff shows exactly what changed |
| Sharing with teammates | `critique web` | Shareable URL, mobile-friendly |
| PR-style review | `critique main feature` | Split view mimics GitHub PR interface |
| AI explanation needed | `critique review --agent claude` | Get contextual explanation |

## Core Commands

```bash
critique                        # Unstaged changes
critique --staged               # Staged (pre-commit review)
critique HEAD                   # Last commit
critique main feature-branch    # Compare branches (base head)
critique --watch                # Live refresh while editing
critique --filter "src/*.ts"    # Filter by glob
```

## Sharing & AI Review

```bash
critique web                    # Share URL (7-day expiry)
critique web --local            # Local HTML file
critique review --agent claude  # AI explanation via Claude Code
```

## Expert Workflows

**Pre-commit review pattern:**
```bash
git add -p                      # Stage interactively
critique --staged               # Review what you're about to commit
git commit                      # Commit with confidence
```

**PR preparation:**
```bash
critique main $(git branch --show-current)  # See full PR diff
critique web --title "Add auth feature"     # Share for early feedback
```

**Selective cherry-pick:**
```bash
critique pick other-branch      # Interactive: pick specific changes
```

## NEVER

- **NEVER use on repos with secrets in diff** - `critique web` uploads to critique.work
- **NEVER expect it to work with Node** - Bun only, will fail silently or error with Node
- **NEVER review diffs >6000 lines** - Auto-excluded, use `git diff` with pager instead
- **NEVER forget `--staged`** - Without it, you see unstaged changes, not what you're committing

## Gotchas

- Lock files auto-excluded (package-lock.json, yarn.lock, etc.)
- Terminal width matters: narrow = unified view, wide = split view
- `REACT_EDITOR=code` to open files in VS Code on click (default: zed)
- Web URLs expire after 7 days - not for permanent documentation

## Navigation

| Key | Action |
|-----|--------|
| Arrows | Navigate/scroll |
| Ctrl+P | Fuzzy file search |
| Option+Arrow | 10x scroll |
| Esc | Close menus |
