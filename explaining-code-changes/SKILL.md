---
name: explaining-code-changes
description: Generates markdown explanations of code changes for sharing via Slack or other channels. Creates text instructions that communicate what to change, where, and why. Use when user asks to share a diff, explain a code change to someone, create a visual patch request, show someone what code to modify, or generate an explanation of changes. Outputs markdown with git permalink if available.
---

# Explaining Code Changes

Generate markdown explanations that communicate WHAT to change, WHERE, and WHY in <10 seconds.

## Before Creating, Ask Yourself

1. **Does recipient have context?** If not, add 1-sentence background
2. **Is the location unambiguous?** Need: file + function + relative position
3. **Is the "why" clear?** Title = purpose ("Add rate limiting") not action ("Add if statement")
4. **Scannable in 5 seconds?** If not, simplify or split

## Output Format

```markdown
**File:** `path/to/file.ts` ([view on GitHub](permalink))

**Change:** One-sentence description of WHY

\`\`\`diff
  // context line
- old code
+ new code
  // context line
\`\`\`
```

## Git Permalink

If the repo has a remote, generate a GitHub/GitLab permalink:

```bash
# Get remote URL
git remote get-url origin

# Get current commit hash for stable link
git rev-parse HEAD

# Construct permalink
# https://github.com/{org}/{repo}/blob/{commit}/{filepath}#L{start}-L{end}
```

## Sizing Guidelines

| Element | Guideline |
|---------|-----------|
| Context lines | 2-3 unchanged lines above/below (more = noise) |
| Total lines | Keep diff block under 20 lines |
| Multi-file | Separate sections per file |

## NEVER

- **NEVER omit file path** - Recipient must know WHERE
- **NEVER skip the "why"** - "Add rate limiting" not "add these lines"
- **NEVER include secrets** - Check diff for API keys, tokens, passwords
- **NEVER use raw `git diff` headers** - Clean up, use readable format
- **NEVER include unrelated changes** - Focus on the specific change being explained

## Example Output

**File:** `apps/frontend/instrumentation-client.ts` ([view on GitHub](https://github.com/org/repo/blob/abc123/apps/frontend/instrumentation-client.ts#L12-L13))

**Change:** Disable PostHog debug logging to suppress noisy console warnings in development

```diff
  posthog.init(posthogKey, {
    capture_exceptions: true,
-   debug: isDev,
+   debug: false,
    disable_session_recording: isDev,
  });
```

## Workflow

1. Check if directory is a git repo (`git rev-parse --is-inside-work-tree`)
2. Get the diff (`git diff` or `git diff --staged`)
3. Get remote URL and commit hash for permalink
4. Extract relevant lines with 2-3 lines of context
5. Format as markdown with file path, permalink, why, and diff block
6. Copy to clipboard with `pbcopy`
