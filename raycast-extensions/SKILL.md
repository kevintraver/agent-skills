---
name: raycast-extensions
description: Manage Kevin's sparse checkout of the Raycast extensions monorepo at ~/Code/raycast/extensions — list, find, and add extensions to the checkout, or set the checkout up from scratch. Use when asked to check out, add, find, or work on a Raycast extension (e.g. "add the spotify extension", "which raycast extensions do I have checked out"), or when an extension folder is missing from that repo.
---

# Raycast Extensions

`~/Code/raycast/extensions` is a sparse, blobless clone of the Raycast monorepo. Only the extensions listed in the sparse-checkout set exist on disk.

- `origin`: Kevin's fork (`kevintraver/raycast-extensions`)
- `upstream`: `raycast/extensions`

Run every git command from the repo root (`~/Code/raycast/extensions`), never from inside `extensions/`. Running sparse-checkout from the subdirectory produces doubled paths like `extensions/extensions/<name>`.

## List checked-out extensions

```bash
git sparse-checkout list
```

## Find an extension

Extension folder names don't always match display names, so search case-insensitively:

```bash
git ls-tree --name-only origin/main extensions/ | grep -i <search-term>
```

## Add an extension

```bash
git sparse-checkout add extensions/<extension-name>
```

If the folder doesn't appear after adding it, the extension is newer than the local `main`. Update from upstream, then add again:

```bash
git fetch upstream main && git merge upstream/main
```

## Set up from scratch

```bash
git clone --filter=blob:none --sparse git@github.com:kevintraver/raycast-extensions.git ~/Code/raycast/extensions
cd ~/Code/raycast/extensions
git remote add upstream https://github.com/raycast/extensions
git sparse-checkout init --cone
git sparse-checkout set extensions/<name> extensions/<name>
```
