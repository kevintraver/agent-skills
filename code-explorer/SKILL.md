---
name: code-explorer
description: Download and explore GitHub repositories. Use when user asks questions (how, where, what, why) about a GitHub repo (URL or owner/repo format), wants to understand a repo's structure, or needs to explore unfamiliar codebases. Use for questions like "where does https://github.com/x/y store Z?", "how does owner/repo handle Y?", "what does github.com/x/y do?". Also triggers on just repo names when user explicitly invokes (e.g., "use code explorer to check spotify-player"). Checks ~/Code first for existing clones. Clones repos to ~/Code for local exploration.
---

# Code Explorer

Clone GitHub repos to ~/Code and explore their structure, architecture, and implementation.

## Workflow

### 1. Detect Repo Reference

Trigger on:

- Full URLs: `https://github.com/owner/repo`
- Short format: `owner/repo` or `github.com/owner/repo`
- Just repo name: `spotify-player`, `mastra` (when user explicitly invokes skill)
- Questions containing a repo reference: "Where does [repo] store X?", "How does [repo] handle Y?"

### 2. Check ~/Code First

Before cloning, check if the repo already exists locally:

```bash
test -d ~/Code/repo && echo "EXISTS" || echo "NOT_FOUND"
```

- **If EXISTS**: Use the local copy, optionally `git fetch origin` for latest
- **If NOT_FOUND**: Clone it with `gh repo clone owner/repo ~/Code/repo`

Use the repo name as the directory name (e.g., `~/Code/mastra`).

### 3. Explore the Codebase

After cloning, use standard exploration:

1. **Quick overview**: Check README, package.json/Cargo.toml/etc. for project type
2. **Structure**: `ls -la` and `tree -L 2` (if available) to understand layout
3. **Entry points**: Find main files (main.go, index.ts, src/main.rs, etc.)
4. **Search**: Use Grep/Glob to find relevant code for user's question

### 4. Search Issues (Fallback or When Relevant)

If code search doesn't answer the question, or if the question relates to bugs/features/discussions, search GitHub issues:

```bash
# Search open issues
gh search issues --repo owner/repo "search terms"

# Search all issues including closed
gh search issues --repo owner/repo "search terms" --state all

# View specific issue details
gh issue view 123 --repo owner/repo
```

Use issue search when:
- Code search didn't find a clear answer
- User asks about known bugs or problems
- User wants to know if a feature is planned
- User references an issue number
- Understanding context around a behavior change
- Question involves configuration, setup, or common problems

### 5. Answer Questions

Provide specific file paths and line numbers when referencing code.
Use the Task tool with Explore agent for deeper codebase questions.

## Examples

**User**: "I have questions about mastra-ai/mastra"

1. Clone to ~/Code/mastra
2. Read README.md for overview
3. Explore project structure
4. Ask user what they want to know

**User**: "How do agents work in mastra-ai/mastra?"

1. Clone to ~/Code/mastra (if not present)
2. Search for agent-related files
3. Trace the agent implementation
4. Explain with code references

**User**: "Is there a bug with streaming in vercel/ai?"

1. Clone to ~/Code/ai (if not present)
2. Search issues: `gh search issues --repo vercel/ai "streaming"`
3. Review relevant issues for context
4. Summarize findings with issue links

**User**: "Where does https://github.com/aome510/spotify-player keep the cached credentials?"

1. Clone to ~/Code/spotify-player
2. Search for credential/cache related files
3. Find config/storage paths in the code
4. Explain where credentials are stored with file references

**User**: "Use code explorer and tell me where does spotify-player keep the cached credentials?"

1. Check if ~/Code/spotify-player exists (just repo name given)
2. If exists, use local copy
3. Search for credential/cache related files
4. Explain where credentials are stored with file references

