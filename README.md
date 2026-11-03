# agent-skills

Agent skills by Kevin Traver. Install one with
`npx skills add kevintraver/agent-skills --skill <name>`.

Each skill's instructions for the agent live in its `SKILL.md`. Notes for people
live here, because a skill folder must not contain a README.md.

## mac-cleanup

Frees up disk space on your Mac. Mostly that means deleting `node_modules` and
`.next` folders from your JS projects. They get big, and they come back when you
run `pnpm install` or start the app.

### Using it

Ask your agent something like "clean up my node_modules". It will:

1. Find your project folders (`~/Code` plus client folders in your home folder).
2. Show you what it would delete and how big it is.
3. Delete only what you say yes to.
4. Tell you how much space you got back.

Or run the script yourself:

```bash
clean-node --days 30 --plan plan.json     # save a list of what would go (deletes nothing)
clean-node --from-plan plan.json          # look at that list again
clean-node --delete --from-plan plan.json # delete exactly what's on the list
clean-node ~/Projects                     # look somewhere other than ~/Code
clean-node --only node_modules,.next      # only these kinds of folder
```

It only deletes what's on a list you've already seen. If anything on the list
changed since, it stops.

`--days 30` skips folders that changed in the last 30 days, so projects you're
working on keep their dependencies. It's a rough guide, not a guarantee.
`--exclude <folder>` leaves a project out.

### What it won't touch

- Your home folder as a whole, or folders where tools are installed (Neovim,
  bun, mise, editor extensions). It refuses to run there.
- Anything in Git, and `.yarn`, `dist`, `.vercel`, `.expo`.
- Anything inside `dist`, `.output`, `.pnpm-store`, or a hidden folder in a
  project (like `.opencode` or `.cache`). A `node_modules` in there belongs to
  a build or a tool, not to your project.

If it can't check something safely, it stops instead of guessing.

### Beyond JS folders

When that isn't enough, the agent can also clean up Docker, AI models, app
caches, old Node versions, and Homebrew. `mac-cleanup/scripts/overview.sh` shows where the
space is going, including folders outside your home folder and folders macOS
wouldn't let it read.

### What's here

- `mac-cleanup/SKILL.md`: instructions for the agent.
- `mac-cleanup/references/mac-disk-space.md`: the rest-of-the-Mac cleanup guide.
- `mac-cleanup/scripts/clean-node`: the cleanup script (Python 3.9+).
- `mac-cleanup/scripts/overview.sh`: disk usage breakdown.
- `mac-cleanup/scripts/unused-taps.sh`: Homebrew taps you no longer use.
- `mac-cleanup/tests/`: tests for `clean-node`. From `mac-cleanup/`, run
  `python3 -m unittest discover -s tests`.
