# Wider Mac disk cleanup

Space beyond JS project folders: the Documents figure, containers, models, app
caches, runtimes, and Homebrew. Most of a large Documents figure is a handful
of caches, local AI models, container images, and dependency folders.

## Contents

- [Ground rules](#ground-rules)
- [Measure](#measure)
- [Usual suspects](#usual-suspects)
- [Find the active model before deleting others](#find-the-active-model-before-deleting-others)
- [App caches](#app-caches)
- [Never delete](#never-delete)
- [Homebrew taps](#homebrew-taps)
- [Login items disabled after a cleanup](#login-items-disabled-after-a-cleanup)
- [Report](#report)

## Ground rules

- Show exact paths and sizes, then let the user approve item by item (a
  multi-select question works well).
- Confirm a folder isn't the one in use (active model, current store, running
  app) before deleting it. Quit the app first: `pgrep -fl <App>.app`.
- Check before labeling, not just before deleting: the user approves on the
  "safe" or "regenerable" note, so verify it before showing the list.
  Regenerable means nothing runs from the folder (`pgrep -fl "<folder>/"`), the
  recipe to rebuild it exists (manifest or lockfile for the right tool), it
  isn't git-tracked, and it holds no release artifacts. User content is safe
  only once you've checked where the app keeps it. Unchecked items go in a
  "check first" group.
- Flag what can't come back: training checkpoints, Docker volumes, app
  databases, git-tracked files. Caches and downloaded models return on demand.
- Prefer the tool's own command (`ollama rm`, `docker image prune`,
  `mise uninstall`, `brew uninstall`) over `rm -rf`.
- Inspect without side effects. Some status commands start daemons
  (`mutagen sync list` starts Mutagen's); prefer `brew info`, `ls`, `du`, and
  shell history, and stop anything a check started.
- Before removing a CLI, search for dependents:
  `grep -rl <name> ~/.agents/skills ~/.dotfiles ~/Library/LaunchAgents`.

## Measure

```bash
bash <skill-directory>/scripts/overview.sh [rows]
```

Prints free space and the largest folders in `~`, `~/Library` and its main
subfolders, `~/.cache`, `~/.local/share`, the Trash, the system folders
(`/Applications`, `/opt/homebrew`, `/Library`, `/private/var`), and
`docker system df`, then how much of `df`'s used space all that explains.
Allow a couple of minutes. Drill down with `du -xhd1 <dir> | sort -rh | head`.
The overview returns nonzero when parts of the home folder can't be read. It
counts the unreadable paths per folder, marks each affected row
`(incomplete: N unreadable)`, and says when Full Disk Access would help.
System folders are always partly unreadable without root; only their rows are
marked. Don't present partial results as complete totals.

**Free-space change.** Record the Available column of
`df -k /System/Volumes/Data` before and after cleanup. Subtract those KiB values
before converting to GiB; `df -h` is too rounded for a reliable difference.
Report an observed change, since other disk activity and filesystem accounting
can affect it. See the [main workflow](../SKILL.md#workflow) for commands.

**Documents figure.** Use measured folder sizes to find cleanup candidates.
Don't infer an exact System Settings Documents total by subtracting a few
folders from home usage. Report the measured paths separately from any category
figure observed in Settings.

**Unexplained used space.** When the "Measured vs used" line shows a large
gap, report it as a finding, not as "system files". A tiny size for a
privacy-protected folder (`~/Library/Containers`, `Group Containers`, Photos,
Music) means unmeasured, not small: name those folders and suggest granting
the terminal Full Disk Access to measure them.

**`du` and hard links.** `du` counts a hard-linked file once per invocation, so
pnpm projects measure differently depending on what else is in the same call.
Re-measure a suspicious folder alone with `du -sh`.

**`du` and APFS clones.** `du` counts every clone in full (VM base and clone
chains, `cp -c` copies), so their sizes don't add up and deleting one frees
only the blocks it doesn't share. Don't promise freed space for clones.

## Usual suspects

| Item | Inspect | Clean | Watch out |
|---|---|---|---|
| Trash | `du -xhd1 ~/.Trash` | Finder ⇧⌘⌫, or `find ~/.Trash -mindepth 1 -maxdepth 1 -exec rm -rf {} +` | Permanent. Users refill it while cleaning; recheck at the end. |
| OrbStack/Docker (`~/Library/Group Containers/*.dev.orbstack`) | `docker system df`, `docker ps -a` | `docker image prune -a`; add `system prune -a --volumes` only if volumes are disposable | Volumes hold data (dev databases). Don't stop OrbStack mid-prune. OrbStack returns freed space to macOS. |
| Ollama (`~/.ollama/models`) | `ollama list` | `ollama rm <model>` | Keep `~/.ollama` config and keys. |
| App-bundled AI models | `du` on `~/Library/Application Support/*` | Remove unused model files | [Find the active model](#find-the-active-model-before-deleting-others) first. |
| Hugging Face (`~/.cache/huggingface`) | `hf cache ls` | Preview `hf cache rm <id> --dry-run`; after approval, `hf cache rm <id> --yes` | Use the exact IDs and cache directory reviewed. Let the CLI manage snapshot/blob references. |
| Other `~/.cache` | `du -xhd1 ~/.cache` | Delete folders of tools no longer used | Training outputs here are not re-downloadable. |
| JS folders and package caches | — | See `SKILL.md` | — |
| Non-JS build output in projects (`.build`, `build`, `.venv`/`venv`, `target`, `Pods`, `.gradle`, `DerivedData`) | `find <root> -maxdepth 4 -type d \( -name .build -o -name build -o -name .venv -o -name venv -o -name target -o -name Pods -o -name .gradle -o -name DerivedData \) -prune -print`, then `du -sh` each | `rm -rf` the approved folders | Check each per the ground rules: `pgrep -fl "<folder>/"` (apps often run from `build`), `git ls-files <folder>`, no `.xcarchive`, `dmg`, or `export` release output, and a manifest for the right tool (`uv.lock`/`pyproject.toml` → `uv sync`, `poetry.lock` → `poetry install`). A venv with no manifest can't be rebuilt; save `uv pip freeze` first. |
| Lume VMs (`~/.lume/<name>`) | `lume ls`; read any `HANDOFF.md` or README in `~/.lume` | `lume delete <name>`, not `rm` | Needs a full rebuild to come back. Bases built with `lume clone` share disk with their source (see `du` and APFS clones), so `du` overstates what deleting one frees; see the macos-vm-sandbox skill. |
| Arduino (`~/Library/Arduino15`) | `du -xhd1 ~/Library/Arduino15` | `packages/` (board cores and toolchains) and `staging/` (downloaded installers) | Check `pgrep -fli arduino` first. Keep `arduino-cli.yaml`, `inventory.yaml`, and the `*_index.json*` files. Restore with Boards Manager or `arduino-cli core install <core>`. |
| mise download cache (`mise cache path`) | `du -sh "$(mise cache path)"`, `mise cache prune --dry-run` | `mise cache prune` (files older than `cache_prune_age`) or `mise cache clear` (everything) | Separate from `mise prune`, which removes unused runtimes. |
| uv cache (`uv cache dir`) | `du -sh "$(uv cache dir)"` | `uv cache prune` (unused entries) or `uv cache clean` (everything) | Refills on the next `uv` install or run. `prune` often frees only a fraction. |
| pip, Go modules, Cargo registry | `du -sh ~/Library/Caches/pip ~/go/pkg/mod ~/.cargo/registry` | `pip cache purge`; `go clean -modcache`; `rm -rf ~/.cargo/registry/{cache,src}` | Usually small. Keep `~/.cargo/registry/index` and `~/.cargo/bin`. |
| Playwright browsers (`~/Library/Caches/ms-playwright`) | `ls ~/Library/Caches/ms-playwright` | Delete older revisions of the same browser (e.g. `webkit-2227` beside `webkit-2336`) | Upgrades leave old revisions behind. Projects pinned to an old Playwright re-download theirs on `npx playwright install`. |
| mise runtimes (`~/.local/share/mise`) | `mise ls --prunable`, `mise prune --tools --dry-run` | `mise prune --tools`, or `mise uninstall node@X` | Each Node version holds its own global npm packages. Check `.nvmrc`/`.node-version` pins. `prune` keeps versions a running process uses; without `--tools` it also forgets tracked configs. |
| Global npm packages | `du -sh "$(npm root -g)"/* \| sort -rh` | `npm uninstall -g <pkg>` | Duplicates may exist via bun or Homebrew (`which -a`). |
| Homebrew downloads and orphans (`brew --cache`) | `du -sh "$(brew --cache)"`, `brew cleanup --prune=all -n`, `brew autoremove -n` | `brew cleanup --prune=all`; `brew autoremove` | Plain `brew cleanup` keeps 120 days of downloads. `autoremove` uninstalls dependencies nothing needs; show its list first. Never `rm` the downloads by hand: a running `brew fetch` holds `*.incomplete` files and locks there. |
| Duplicate Rust | `which cargo`, `rustup toolchain list` | `rustup toolchain uninstall stable` | Never `rustup self uninstall`: it deletes `~/.cargo` and its `cargo install` tools. |
| Xcode (`~/Library/Developer/Xcode`) | `du -xhd1` | Delete old `iOS DeviceSupport/<version>` | Counts as Developer. Rebuilt when a device connects. |
| Xcode simulators (`~/Library/Developer/CoreSimulator`) | `xcrun simctl list devices unavailable` | `xcrun simctl delete unavailable` | Only removes simulators whose runtime is gone (left from older Xcode versions). Counts as Developer. |
| Simulator device data (`~/Library/Developer/CoreSimulator/Devices/<udid>/data`) | `xcrun simctl list devices` (only `Shutdown` devices) | In each shut-down device, delete `private/var/MobileAsset/AssetsV2`, `Library/Caches`, `var/db/diagnostics`, `var/db/uuidtext` | Quit Simulator first; skip `Booted` devices. Keeps installed apps, unlike `simctl erase`. |
| Clang module cache (`$(getconf DARWIN_USER_CACHE_DIR)clang/ModuleCache`) | `du -sh` | Delete its contents | Only while `pgrep -x clang`, `clangd`, `swiftc`, and `xcodebuild` find nothing. Rebuilt on the next build. |

Hugging Face cache locations can be overridden by `HF_HOME` or `HF_HUB_CACHE`.
For a custom location, use the same `--cache-dir PATH` for listing, preview,
and removal. Check `hf cache --help` for the installed version before use.
See the [official CLI guide](https://huggingface.co/docs/huggingface_hub/guides/cli#hf-cache)
and [cache layout](https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache):
repository snapshots reference blobs within their repository cache directory.

## Find the active model before deleting others

Apps keep old model versions beside the current one. Identify the active file:

```bash
defaults read <bundle-id> | grep -i model
lsof -c <AppName> | grep -E '\.(gguf|bin|mlx|safetensors)'
```

Dictation, autocomplete, and on-device AI apps often keep several models side
by side. The selection is usually a preference key (e.g. Cotypist's
`ModelRepository_selectedModel`).

## App caches

Quit the app first. Logins and settings survive. Check every path against
[Never delete](#never-delete).

| Kind | Delete | Keep |
|---|---|---|
| Electron and Chromium-based apps (`~/Library/Application Support/<App>`, and each `Partitions/<name>` inside it) | `Code Cache`, `GPUCache`, `DawnCache`, `GraphiteDawnCache`, `DawnGraphiteCache`, `DawnWebGPUCache`, `GrShaderCache`, `Crashpad/completed`, `Service Worker/CacheStorage`. `Cache` and `CachedData` only in a folder that also has one of the others | `IndexedDB`, `Local Storage`, `Cookies`, and everything else |
| Chromium browser profiles (incl. automation profiles in `~/.tmp`) | `<profile>/Default/Cache`, `<profile>/Default/Code Cache` | Rest of the profile |
| Firefox-based browsers | `~/Library/Caches/<browser>/Profiles/*` | The profile itself, in `~/Library/Application Support` |
| Old engines inside a Chromium browser's app bundle | `<Browser>.app/Contents/Frameworks/*Framework.framework/Versions/<version>` | `Current` (`readlink` it) and any version newer than `Current`, which is a staged update |
| App updater downloads | `~/Library/Caches/*-updater` | Nothing; the app re-downloads its next update |
| Self-updating CLIs (e.g. `~/.local/share/claude/versions`, ~230 MB each; `~/.grok/downloads`) | Old entries in the CLI's `versions` or `downloads` folder | The target of `readlink` on the binary on PATH |
| Claude Code plugin versions (`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>`) | Versions not listed by `jq -r '.plugins[][].installPath' ~/.claude/plugins/installed_plugins.json`, only while no other Claude session runs | Every listed `installPath`; running sessions load skills and scripts from their version's path |
| Tool temp folders | Contents of `~/.<tool>/.tmp` | The tool's sessions and config |
| VM images and models an app re-downloads (e.g. `~/Library/Application Support/Claude/vm_bundles`, ~9 GB) | The unused bundle | Whatever the app has loaded; confirm it re-downloads first |

## Never delete

Deleting these loses data or breaks running apps:

- `~/Library` data stores: `Keychains`, `Accounts`, `Mail`, `Contacts`,
  `Mobile Documents` (iCloud Drive), and `Calendars`, whose agent holds its
  database open, so deleting it crashes Calendar.
- Compiled model caches: any `com.apple.e5rt.e5bundlecache` folder and the
  folder directly holding it. Running apps lose on-device text and image
  recognition until they restart.
- Identity and telemetry queues with cache-like names
  (`~/Library/Caches/GIPPseudonymousID`, `~/Library/Caches/CCTClearcutLogger`).
  Deleting them while their owner runs starts an endless rewrite loop.
- Caches that hold user content: offline music and downloaded media, AI chat
  history, clipboard history. Layouts vary, so a missing offline marker proves
  nothing; ask before clearing a media player's or launcher's cache.
- Wallpaper and screen saver assets (`com.apple.idleassetsd`,
  `com.apple.wallpaper`): user-chosen, and a large re-download.

## Homebrew taps

```bash
bash <skill-directory>/scripts/unused-taps.sh
```

Lists each third-party tap with what is installed from it; `UNUSED` taps can go
with `brew untap <tap>`. Otherwise `brew uninstall` the formulae first. For a
"taps are not trusted" warning, untap an unused tap or `brew trust <user>/<tap>`.
Judge whether a formula is used with `brew info`, `grep -a <name> ~/.zsh_history`,
and a dotfiles search.
The script requires `brew` and `jq`; inventory or tap-list failures abort
instead of labeling taps unused. `UNUSED` means no installed formulae or casks
were found from the tap, not that the user has no reason to keep it.

## Login items disabled after a cleanup

Cleanup apps and the System Settings toggle can disable launch agents; users
will blame the cleanup. Check and restore:

```bash
launchctl print-disabled gui/$(id -u) | grep -i <label>
launchctl enable gui/$(id -u)/<label>
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/<label>.plist
```

Have the user confirm System Settings → General → Login Items & Extensions →
Allow in the Background is on for that app.

## Report

Give a before/after table using the Available values from
`df -k /System/Volumes/Data`, formatted for readability after calculating the
observed change. Include what was removed with measured sizes, separate outcomes
for deletion and pruning, any incomplete measurements or failures, anything
that changed behavior, and the next-largest options.
