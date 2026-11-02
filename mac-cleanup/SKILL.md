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
approves, and report the observed free-space change from `df -k`, not from
summed `du` totals.

## clean-node

`<skill-directory>/scripts/clean-node` deletes `node_modules`, `.next`, `.turbo`,
`.nuxt`, `.svelte-kit`, and `.parcel-cache`. It is normally on PATH as
`clean-node`; if `command -v clean-node` finds nothing, run the bundled path or
link it: `ln -s <skill-directory>/scripts/clean-node ~/.local/bin/clean-node`.
Requires Python 3.9+, Git, and `du`; invoke it directly, not with `bash`.
The scan root defaults to `~/Code`.

```bash
clean-node [--only NAME,...] [--days N] [--exclude PATH ...] [--prune-store] [--plan FILE] [dir]
clean-node --from-plan FILE             # review saved targets
clean-node --delete --from-plan FILE    # apply only after approval
```

- Dry run unless `--delete`: lists matches largest first, with a total.
- Deletion requires a saved plan: it never rescans for additional targets.
  Plans record absolute paths and directory identities/mtimes. Changed identities
  or top-level mtimes, missing paths, symlinks, or newly Git-protected targets
  abort deletion. Keep projects idle during cleanup; this is not a lock against
  concurrent installs or builds.
- `--only NAME` matches only the named folder types (comma-separated or
  repeated, e.g. `--only node_modules,.next`). Use it when the user approves
  some types; the plan records the selection, and deletion rejects any other
  name.
- `--exclude PATH` skips a project or target directory. Relative paths are
  relative to the scan root; repeat the option for multiple exclusions.
- Never looks inside `dist`, `.output`, `.pnpm-store`, or hidden folders below
  the scan root (`.opencode`, `.cache`, `.claude`): a `node_modules` there is
  part of a build output, store, or tool install.
- `--plan` always writes a plan, with no targets when there is nothing to
  clean. A missing plan file means the command failed.
- `--days N` only matches folders whose own mtime is older than N days.
  It does not establish project inactivity: source edits and nested file edits
  can leave that timestamp unchanged.
- Rejects home, ancestors of home, and known tool-installation roots, including
  symlink aliases. Does not follow symlinks while scanning.
- Skips folders containing Git repositories or git-tracked files. Inspection
  and measurement errors abort the command; they never mean "nothing to clean".
- Store pruning is opt-in: add `--prune-store` when creating a plan. The preview
  shows the shared store path, size, and broader scope. Deletion checks that
  pnpm still selects the approved store, then reports pruning separately.
  Ordinary project cleanup does not invoke or require pnpm.

Use it instead of an ad-hoc `find … -exec rm`; it encodes the safety rules.

## Workflow

1. Record available space in KiB. Agent shells don't keep variables between
   tool calls, so write it to a file in the session scratchpad (or a
   `mktemp -d` folder), where the plans go too:

   ```bash
   df -k /System/Volumes/Data | awk 'NR == 2 {print $(4)}' > <scratch>/before-1.kib
   ```

   Stop if measurement fails; don't use an empty or missing value as zero.
   Cleanups often run in several approval rounds: write a new
   `before-<round>.kib` before each one and keep `before-1.kib` for the
   session total.
2. Find the roots. Projects live in `~/Code` and in client folders directly
   under `~`:

   ```bash
   for d in ~/*/; do
     [[ $d == "$HOME/Library/" ]] && continue
     if [[ -n $(find "$d" -maxdepth 3 \( -name node_modules -o -name .git \) -prune -o -name package.json -print -quit 2>/dev/null) ]]; then
       echo "${d%/}"
     fi
   done
   ```

   Run `clean-node` per root. Never pass `~`: it would hit installed tools whose
   `node_modules` are the program (Neovim Mason, `~/.bun/install/global`, mise's
   global npm packages, editor extensions) and break them.
3. Leave out projects with a running dev server, whose `node_modules`/`.next`
   are in use. For projects managed by `d3k`, inspect the existing session,
   including `d3k errors --context`. Do not start a dev server for cleanup.
   These checks provide additional clues: the first finds JS processes by
   working directory, the second finds any process (apps, login items)
   running from under the root:

   ```bash
   lsof -a -d cwd -c node -c bun -Fn 2>/dev/null | sed -n 's/^n//p' | sort -u
   pgrep -fl "<root>/"
   ```

   Empty output does not prove inactivity: other processes can still use these
   files. Exclude known active projects and
   recheck activity immediately before applying a plan.
4. Preview each root with `--days 30 --plan <scratch>/cleanup-<unique-name>.json`
   and `--exclude` for each active or unwanted project under that root. Pass
   only exclusions inside the root being scanned (`clean-node` rejects others),
   and skip `/` and non-project folders from the `lsof` output. Omit `--days` only if
   the user wants everything. Plans must be new files outside deletion targets.
   When `--days` filters out most targets, also run the preview without it in
   the same pass (previews delete nothing) and show both. Folder mtime is a
   recency hint, not proof a project is active or idle: describe it the same
   way for every root, and don't single out some projects as "likely active".
5. Get approval for the exact paths and any optional shared-store pruning. If
   the selection changes, create and review a new plan with exclusions; don't
   hand-edit plans or use manual `rm -rf`. `clean-node --from-plan FILE`
   rechecks and displays a saved plan.
   When the user approves only some folder types, make the new plan with
   `--only` rather than building `--exclude` lists from an earlier plan:
   exclusion lists fail open, so a broken filter yields a plan wider than
   approved. Stop on any `clean-node` error; don't silence it with
   `2>/dev/null || true`.
6. Run `clean-node --delete --from-plan FILE`, then measure again:

   ```bash
   before=$(cat <scratch>/before-<round>.kib)
   after=$(df -k /System/Volumes/Data | awk 'NR == 2 {print $(4)}')
   awk -v before="$before" -v after="$after" \
     'BEGIN {printf "Observed free-space change: %+.2f GiB (%+.0f KiB)\n", (after-before)/1048576, after-before}'
   ```

   Use this calculation only when both measurements succeeded. Report the
   before/after values, observed change, and completed folder deletions and
   pruning separately; after a later round, also give the session total from
   `before-1.kib`. Background writes and filesystem accounting can affect
   the change; don't infer exact reclaimed bytes from `du` or rounded `df -h`.
   Mention that `pnpm install` (or npm/bun) restores dependencies and
   `next dev`/`next build` recreates `.next`.
   If the cleaned projects use pnpm and the plan had no `--prune-store`, offer
   `pnpm store prune` as the next step: their packages now sit unused in the
   shared store (see below).

## Freed space is less than the listed total

pnpm can share dependency data with its store (`pnpm store path`). Removing
project folders may free less than their measured sizes. Store pruning is a
separate action: include `--prune-store` in the reviewed plan, or review and run
`pnpm store prune` separately. Pruning can require downloads on a later install.

## Package-manager caches

Offer these when the user wants more space. Each refills on demand.

| Cache | Check | Clear |
|---|---|---|
| pnpm store, current | `du -sh "$(pnpm store path)"` | `pnpm store prune` |
| pnpm stores from older pnpm majors | `ls ~/Library/pnpm/store` | `rm -rf` each `v<N>` that isn't `pnpm store path` |
| pnpm's own downloaded pnpm versions (`~/Library/pnpm/package-manager-store`) | `ls ~/Library/pnpm/package-manager-store/v*/links/@/pnpm`; compare with `which -a pnpm \| xargs realpath` | `rm -rf ~/Library/pnpm/package-manager-store` if the pnpm you run lives elsewhere (e.g. Homebrew); re-downloads when a project's `packageManager` pins a version |
| pnpm metadata from older pnpm majors | `du -xhd1 ~/Library/Caches/pnpm` (one `v<N>` per major) | `pnpm cache prune` (pnpm 12+: only removes the `v<N>` dirs this pnpm can't read) |
| pnpm metadata, current | `pnpm cache list [glob]` | `pnpm cache delete <pattern>` |
| npm | `du -sh ~/.npm/_cacache`; `npm cache verify` garbage-collects first | `npm cache clean --force` |
| npx packages | `npm cache npx ls`; `du -sh ~/.npm/_npx` | `npm cache npx rm --force` (or `rm <key>` for one) |
| bun | `du -sh ~/.bun/install/cache` | `rm -rf ~/.bun/install/cache` (`bun pm cache rm` only runs inside a project) |
| Yarn classic | `du -sh "$(yarn cache dir)"` | `yarn cache clean` |
| node-gyp headers | `du -sh ~/Library/Caches/node-gyp` | `rm -rf ~/Library/Caches/node-gyp` |

`~/.bun/install/global` holds globally installed bun tools, not cache: remove
unused ones with `bun remove -g <pkg>`.

## Never delete

- `.yarn`: Yarn 2+ release, plugins, and patches, usually committed.
- `dist`: sometimes committed (GitHub Actions, published packages).
- `.vercel` (project link) and `.expo` (dev-client settings).
- Anything `git ls-files <path>` reports as tracked.

## Script verification

In skill markdown, write awk fields as `$(4)`, never a bare dollar sign
followed by a digit: the skill loader replaces those with invocation arguments.

After changing the scripts, run:

```bash
python3 -B -m unittest discover -s <skill-directory>/tests -v
bash -n <skill-directory>/scripts/overview.sh <skill-directory>/scripts/unused-taps.sh
```

Tests use temporary directories and stub package-manager actions; they require
Git, `du`, and `jq`.
