---
name: claude-session-migrate
description: Migrate Claude Code session storage when directories are moved or renamed. Use when user mentions moving folders, renaming directories, relocating projects, moving conversations between projects, or needs to update Claude session paths after filesystem changes.
allowed-tools: Bash, Read, Write, Glob
---

# Claude Session Migrate

Migrate Claude Code sessions when projects move or when moving conversations between projects.

## Background

Claude Code stores sessions in `~/.claude/projects/` with encoded folder names:
- Path `/Users/kevin/Code/my-app` → folder `-Users-kevin-Code-my-app`
- Encoding: remove leading `/`, replace `/` and spaces with `-`, add leading `-`

Each project folder contains:
- `sessions-index.json` - index of all conversations with metadata
- `*.jsonl` files - individual conversation data

## Two Migration Types

### Type 1: Project Folder Renamed/Moved
All sessions stay together, just update the folder name and paths.

### Type 2: Move Specific Conversation to Different Project
Move one conversation from project A to project B (e.g., started work in ~/.dotfiles, want to move it to ~/Code/new-project).

---

## Type 1: Project Folder Renamed/Moved

Use when: User renamed or moved their entire project directory.

### Steps

1. **Get the resolved paths**
   ```bash
   # CRITICAL: Always use pwd -P for the canonical path (macOS is case-insensitive!)
   cd /path/to/new/location && pwd -P
   ```

2. **Encode both paths**
   ```
   /Users/kevin/old-location/app → -Users-kevin-old-location-app
   /Users/kevin/new-location/app → -Users-kevin-new-location-app
   ```

3. **Rename the session folder**
   ```bash
   cd ~/.claude/projects/
   mv -- -Users-kevin-old-location-app -Users-kevin-new-location-app
   ```

4. **Update sessions-index.json paths**
   ```bash
   # Update encoded folder name in fullPath
   sd '-Users-kevin-old-location-app' '-Users-kevin-new-location-app' \
     ~/.claude/projects/-Users-kevin-new-location-app/sessions-index.json

   # Update projectPath
   sd '/Users/kevin/old-location/app' '/Users/kevin/new-location/app' \
     ~/.claude/projects/-Users-kevin-new-location-app/sessions-index.json
   ```

5. **Verify**
   ```bash
   cat ~/.claude/projects/-Users-kevin-new-location-app/sessions-index.json | rg 'projectPath|fullPath'
   ```

---

## Type 2: Move Conversation Between Projects

Use when: User wants to move a specific conversation from one project to another.

### Steps

1. **Find the conversation in the source project**
   ```bash
   # Search by title, summary, or firstPrompt
   cat ~/.claude/projects/-SOURCE-PROJECT/sessions-index.json | rg -i 'search-term' -B5 -A10
   ```

   Note the `sessionId` (e.g., `4c8d1340-6da1-4a97-b511-10776698c802`)

2. **Get the target project's resolved path**
   ```bash
   cd /path/to/target/project && pwd -P
   # e.g., /Users/kevin/Code/my-app → -Users-kevin-Code-my-app
   ```

3. **Create target project folder if needed**
   ```bash
   mkdir -p ~/.claude/projects/-Users-kevin-Code-my-app
   ```

4. **Move the session file**
   ```bash
   mv ~/.claude/projects/-SOURCE-PROJECT/SESSION_ID.jsonl \
      ~/.claude/projects/-TARGET-PROJECT/
   ```

5. **Read the session entry from source sessions-index.json**
   ```bash
   cat ~/.claude/projects/-SOURCE-PROJECT/sessions-index.json | rg 'SESSION_ID' -A15
   ```
   Copy the full entry object.

6. **Update target sessions-index.json**

   Read the target's sessions-index.json (create if doesn't exist):
   ```json
   {
     "version": 1,
     "entries": []
   }
   ```

   Add the session entry with updated fields:
   - `fullPath`: change to target project folder path
   - `projectPath`: change to target project directory
   - `gitBranch`: set to `""` or the target project's branch

7. **Verify**
   ```bash
   ls ~/.claude/projects/-TARGET-PROJECT/
   cat ~/.claude/projects/-TARGET-PROJECT/sessions-index.json
   ```

### Example: Move conversation from ~/.dotfiles to ~/Code/my-new-project

```bash
# 1. Find the conversation
cat ~/.claude/projects/-Users-kevin--dotfiles/sessions-index.json | rg -i 'search term' -B5 -A10
# Found: sessionId "a1b2c3d4-5678-90ab-cdef-1234567890ab"

# 2. Get target path (use pwd -P!)
cd ~/Code/my-new-project && pwd -P
# Output: /Users/kevin/Code/my-new-project → -Users-kevin-Code-my-new-project

# 3. Create target folder
mkdir -p ~/.claude/projects/-Users-kevin-Code-my-new-project

# 4. Move the session file
mv ~/.claude/projects/-Users-kevin--dotfiles/a1b2c3d4-5678-90ab-cdef-1234567890ab.jsonl \
   ~/.claude/projects/-Users-kevin-Code-my-new-project/

# 5-6. Update sessions-index.json using Read/Write tools
# Add entry with:
#   fullPath: /Users/kevin/.claude/projects/-Users-kevin-Code-my-new-project/a1b2c3d4-...jsonl
#   projectPath: /Users/kevin/Code/my-new-project
```

---

## Edge Cases

- **macOS case-insensitivity**: `/Users/kevin/Code` and `/Users/kevin/code` are the SAME directory. Always use `pwd -P`. If resolved paths match, no migration needed!
- **Session not found**: Search with different terms or list all entries
- **Target folder exists**: Merge entries into existing sessions-index.json
- **Orphaned entries**: It's OK to leave old entries in source sessions-index.json; Claude handles missing files gracefully

## Path Encoding Rules

| Path | Encoded |
|------|---------|
| `/Users/kevin/project` | `-Users-kevin-project` |
| `/Users/kevin/My App` | `-Users-kevin-My-App` |
| `/home/user/.dotfiles` | `-home-user--dotfiles` |

Note: `.dotfiles` becomes `--dotfiles` (the dot becomes a hyphen, plus the separator hyphen).
