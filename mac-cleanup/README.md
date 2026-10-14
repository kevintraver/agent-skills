# mac-cleanup

Frees up disk space on your Mac. Mostly that means deleting `node_modules` and
`.next` folders from your JS projects. They get big, and they come back when you
run `pnpm install` or start the app.

## Using it

Ask your agent something like "clean up my node_modules". It will:

1. Find your project folders (`~/Code` plus client folders in your home folder).
2. Show you what it would delete and how big it is.
3. Delete only what you say yes to.
4. Tell you how much space you got back.

Or run the script yourself:

```bash
clean-node --days 30            # show what would go (deletes nothing)
clean-node --days 30 --delete   # delete it
clean-node ~/CraftedLabs        # look somewhere other than ~/Code
```

`--days 30` skips folders that changed in the last 30 days, so projects you're
working on keep their dependencies. It's a rough guide, not a guarantee.

## What it won't touch

- Your home folder as a whole, or folders where tools are installed (Neovim,
  bun, mise, editor extensions). It refuses to run there.
- Anything in Git, and `.yarn`, `dist`, `.vercel`, `.expo`.

If it can't check something safely, it stops instead of guessing.

## Beyond JS folders

When that isn't enough, the agent can also clean up Docker, AI models, app
caches, old Node versions, and Homebrew. `scripts/overview.sh` shows where the
space is going.

## What's here

- `SKILL.md`: instructions for the agent.
- `references/mac-disk-space.md`: the rest-of-the-Mac cleanup guide.
- `scripts/clean-node`: the cleanup script (Python 3.9+).
- `scripts/overview.sh`: disk usage breakdown.
- `scripts/unused-taps.sh`: Homebrew taps you no longer use.
- `tests/`: tests for `clean-node`. From this folder, run
  `python3 -m unittest discover -s tests`.
