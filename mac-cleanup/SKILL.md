---
name: mac-cleanup
description: Free disk space on the user's Mac, mainly by deleting node_modules, .next, .turbo, and other regenerable JS dependency and build folders across project directories with the bundled clean-node script. Use when the user asks to clean up node_modules or .next folders, clear out old or inactive JS projects, or reclaim space used by ~/Code or package-manager caches (pnpm, npm, bun, Yarn). Also use when the Mac is low on storage or System Settings shows a huge Documents or System Data figure, and for Docker/OrbStack, local AI models, app caches, old runtimes, or unused Homebrew taps.
---

# Mac Cleanup

Pick the path:

- **JS project folders** (the usual request) → follow [Workflow](#workflow).
- **Anything else on the disk** (Documents figure, Docker, models, app caches,
  runtimes, Homebrew) → read [references/mac-disk-space.md](references/mac-disk-space.md).
  Start with `bash <skill-directory>/scripts/overview.sh` for a breakdown.

Either way: show sizes and exact paths first, delete only what the user
approves, and report freed space from `df`, not from summed `du` totals.

## clean-node

`<skill-directory>/scripts/clean-node` deletes `node_modules`, `.next`, `.turbo`,
`.nuxt`, `.svelte-kit`, and `.parcel-cache`. It is normally on PATH as
`clean-node`; if `command -v clean-node` finds nothing, run the bundled path or
link it: `ln -s <skill-directory>/scripts/clean-node ~/.local/bin/clean-node`.
Requires Python 3.9+, Git, and `du`; invoke it directly, not with `bash`.

```bash
clean-node [--delete] [--days N] [dir]    # dir defaults to ~/Code
```

- Dry run unless `--delete`: lists matches largest first, with a total.
- `--days N` only matches folders whose own mtime is older than N days.
  It does not establish project inactivity: source edits and nested file edits
  can leave that timestamp unchanged.
- Rejects home, ancestors of home, and known tool-installation roots, including
  symlink aliases. Does not follow symlinks while scanning.
- Skips folders containing Git repositories or git-tracked files. Inspection
  and measurement errors abort the command; they never mean "nothing to clean".
- Runs `pnpm store prune` after deleting.

Use it instead of an ad-hoc `find … -exec rm`; it encodes the safety rules.

## Workflow

1. Record free space: `df -h /System/Volumes/Data | tail -1`.
2. Find the roots. Projects live in `~/Code` and in client folders directly
   under `~`:

   ```bash
   for d in ~/*/; do
     [[ $d == "$HOME/Library/" ]] && continue
     find "$d" -maxdepth 3 -name package.json -not -path '*/node_modules/*' -print -quit 2>/dev/null | grep -q . && echo "$d"
   done
   ```

   Run `clean-node` per root. Never pass `~`: it would hit installed tools whose
   `node_modules` are the program (Neovim Mason, `~/.bun/install/global`, mise's
   global npm packages, editor extensions) and break them.
3. Dry run each root with `--days 30` (omit it only if the user wants
   everything) and show the output. On "Nothing to clean", offer a run without
   `--days`.
4. Leave out projects with a running dev server, whose `node_modules`/`.next`
   are in use:

   ```bash
   lsof -a -d cwd -c node -c bun -Fn 2>/dev/null | sed -n 's/^n//p' | sort -u
   ```

5. Get approval for all or some. To exclude projects, run `--delete` only on
   the other roots or `rm -rf` the approved paths from the dry-run list; don't
   edit the script for one-offs.
6. Delete (same arguments plus `--delete`), re-run `df`, and report the space
   freed. Mention that `pnpm install` (or npm/bun) restores a project and
   `next dev`/`next build` recreates `.next`.

## Freed space is less than the listed total

pnpm `node_modules` are hard links into the store (`pnpm store path`). Deleting
them only removes links; `pnpm store prune` (run by `clean-node --delete`) frees
packages no other registered project uses. Shared dependencies free nothing.

## Package-manager caches

Offer these when the user wants more space. Each refills on demand.

| Cache | Check | Clear |
|---|---|---|
| pnpm store, current | `du -sh "$(pnpm store path)"` | `pnpm store prune` |
| pnpm stores from older pnpm majors | `ls ~/Library/pnpm/store` | `rm -rf` each `v<N>` that isn't `pnpm store path` |
| pnpm metadata | `du -xhd1 ~/Library/Caches/pnpm` | `pnpm cache prune` |
| npm | `du -sh ~/.npm/_cacache ~/.npm/_npx` | `npm cache clean --force`; `rm -rf ~/.npm/_npx` |
| bun | `du -sh ~/.bun/install/cache` | `rm -rf ~/.bun/install/cache` (`bun pm cache rm` needs a project dir) |
| Yarn classic | `du -sh "$(yarn cache dir)"` | `yarn cache clean` |

## Never delete

- `.yarn`: Yarn 2+ release, plugins, and patches, usually committed.
- `dist`: sometimes committed (GitHub Actions, published packages).
- `.vercel` (project link) and `.expo` (dev-client settings).
- Anything `git ls-files <path>` reports as tracked.
