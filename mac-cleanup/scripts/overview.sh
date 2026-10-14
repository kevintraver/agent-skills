#!/bin/bash
# Print where disk space is going in the home folder.
# Usage: overview.sh [rows]   (rows per section, default 15)

set -o pipefail

rows=${1:-15}
if (($# > 1)) || [[ ! $rows =~ ^[1-9][0-9]*$ ]]; then
  echo "Usage: overview.sh [positive row count]" >&2
  exit 1
fi
status=0
errors=$(mktemp) || exit 1
trap 'rm -f "$errors"' EXIT

section() { printf '\n== %s\n' "$1"; }
report_error() {
  echo "Incomplete measurement; do not treat this section as a full total." >&2
  awk 'NR <= 5 { print } END { if (NR > 5) print "... further errors omitted" }' "$errors" >&2
  status=1
}
top() {
  if ! du -xhd1 "$@" 2>"$errors" | sort -rh | awk -v rows="$rows" 'NR <= rows'; then
    report_error
  fi
}

section "Free space (KiB; df -k)"
if ! df -k /System/Volumes/Data | tail -1; then
  status=1
fi

section "Home folder"
top ~

section "~/Library"
top ~/Library

section "~/Library subfolders"
top ~/Library/Application\ Support ~/Library/Group\ Containers ~/Library/Containers ~/Library/Caches ~/Library/Developer

section "~/.cache and ~/.local"
top ~/.cache ~/.local/share

section "Trash"
if ! du -sh ~/.Trash 2>"$errors"; then
  report_error
fi

if docker info >/dev/null 2>&1; then
  section "Docker"
  docker system df || status=1
fi

exit "$status"
