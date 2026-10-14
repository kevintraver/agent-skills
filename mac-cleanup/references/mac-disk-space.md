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
- [Homebrew taps](#homebrew-taps)
- [Login items disabled after a cleanup](#login-items-disabled-after-a-cleanup)
- [Report](#report)

## Ground rules

- Show exact paths and sizes, then let the user approve item by item (a
  multi-select question works well).
- Confirm a folder isn't the one in use (active model, current store, running
  app) before deleting it. Quit the app first: `pgrep -fl <App>.app`.
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
subfolders, `~/.cache`, `~/.local/share`, the Trash, and `docker system df`.
Allow a couple of minutes. Drill down with `du -xhd1 <dir> | sort -rh | head`.
The overview returns nonzero and marks incomplete measurements when paths
cannot be read. Don't present partial results as complete totals.

**Free-space change.** Record the Available column of
`df -k /System/Volumes/Data` before and after cleanup. Subtract those KiB values
before converting to GiB; `df -h` is too rounded for a reliable difference.
Report an observed change, since other disk activity and filesystem accounting
can affect it. See the [main workflow](../SKILL.md#workflow) for commands.

**Documents figure.** Use measured folder sizes to find cleanup candidates.
Don't infer an exact System Settings Documents total by subtracting a few
folders from home usage. Report the measured paths separately from any category
figure observed in Settings.

**`du` and hard links.** `du` counts a hard-linked file once per invocation, so
pnpm projects measure differently depending on what else is in the same call.
Re-measure a suspicious folder alone with `du -sh`.

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
| mise download cache (`mise cache path`) | `du -sh "$(mise cache path)"` | `mise cache clear` | Separate from `mise prune`, which removes unused runtimes. |
| uv cache (`uv cache dir`) | `du -sh "$(uv cache dir)"` | `uv cache prune` (unused entries) or `uv cache clean` (everything) | Refills on the next `uv` install or run. |
| Playwright browsers (`~/Library/Caches/ms-playwright`) | `ls ~/Library/Caches/ms-playwright` | Delete older revisions of the same browser (e.g. `webkit-2227` beside `webkit-2336`) | Upgrades leave old revisions behind. Projects pinned to an old Playwright re-download theirs on `npx playwright install`. |
| mise runtimes (`~/.local/share/mise`) | `mise ls`, `mise prune --dry-run` | `mise uninstall node@X` | Each Node version holds its own global npm packages. Check `.nvmrc`/`.node-version` pins. |
| Global npm packages | `du -sh "$(npm root -g)"/* \| sort -rh` | `npm uninstall -g <pkg>` | Duplicates may exist via bun or Homebrew (`which -a`). |
| Homebrew downloads and orphans (`brew --cache`) | `du -sh "$(brew --cache)"`, `brew cleanup --prune=all -n`, `brew autoremove -n` | `brew cleanup --prune=all`; `brew autoremove` | Plain `brew cleanup` keeps 120 days of downloads. `autoremove` uninstalls dependencies nothing needs; show its list first. |
| Duplicate Rust | `which cargo`, `rustup toolchain list` | `rustup toolchain uninstall stable` | Never `rustup self uninstall`: it deletes `~/.cargo` and its `cargo install` tools. |
| Xcode (`~/Library/Developer/Xcode`) | `du -xhd1` | Delete old `iOS DeviceSupport/<version>` | Counts as Developer. Rebuilt when a device connects. |

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

Known: Cotypist (`~/Library/Application Support/app.cotypist.Cotypist/Models`,
key `ModelRepository_selectedModel`), Google on-device models
(`com.google.AIEdgeForesight`), and dictation apps (superwhisper, MacWhisper,
FluidAudio), each with its own Whisper models.

## App caches

Quit the app first. Logins and settings survive.

| App | Delete | Keep |
|---|---|---|
| Spotify | `~/Library/Caches/com.spotify.client` | Offline downloads (location: `grep storage ~/Library/Application\ Support/Spotify/prefs`) |
| Notion | `Partitions/notion/Service Worker/CacheStorage` and `Partitions/notion/Cache` in `~/Library/Application Support/Notion` | `IndexedDB`, `Local Storage`, `Cookies` |
| Chrome-based profiles (incl. automation profiles in `~/.tmp`) | `<profile>/Default/Cache`, `<profile>/Default/Code Cache` | Rest of the profile |
| Claude desktop | `~/Library/Application Support/Claude/vm_bundles` (Cowork VM, ~9 GB, re-downloads) | Everything else |
| Codex | `~/.codex/.tmp` | Sessions and config |
| Grok CLI | Old binaries in `~/.grok/downloads` | The target of `readlink ~/.grok/bin/grok` |
| Claude Code CLI | Old versions in `~/.local/share/claude/versions` (~230 MB each) | The target of `readlink ~/.local/bin/claude` |

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
