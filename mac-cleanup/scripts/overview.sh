#!/bin/bash
# Print where disk space is going in the home folder.
# Usage: overview.sh [rows]   (rows per section, default 15)

rows=${1:-15}

section() { printf '\n== %s\n' "$1"; }
top() { du -xhd1 "$@" 2>/dev/null | sort -rh | head -n "$rows"; }

section "Free space"
df -h /System/Volumes/Data | tail -1

section "Home folder"
top ~

section "~/Library"
top ~/Library

section "~/Library subfolders"
top ~/Library/Application\ Support ~/Library/Group\ Containers ~/Library/Containers ~/Library/Caches ~/Library/Developer

section "~/.cache and ~/.local"
top ~/.cache ~/.local/share

section "Trash"
du -sh ~/.Trash 2>/dev/null

if docker info >/dev/null 2>&1; then
  section "Docker"
  docker system df
fi
