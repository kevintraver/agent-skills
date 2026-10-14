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
sizes=$(mktemp) || exit 1
trap 'rm -f "$errors" "$sizes"' EXIT

section() { printf '\n== %s\n' "$1"; }

# Turn "KiB<TAB>path" lines into du -h style output.
human() {
  awk -F'\t' '{
    kb = $1
    size = kb >= 1048576 ? sprintf("%.1fG", kb / 1048576) : kb >= 1024 ? sprintf("%.0fM", kb / 1024) : kb "K"
    printf "%7s  %s\n", size, $2
  }'
}

# Print the folders directly inside the given folders, largest first.
children() {
  printf '%s\n' "$@" | awk -F'\t' '
    NR == FNR { wanted[$0] = 1; next }
    { parent = $2; sub(/\/[^\/]*$/, "", parent) }
    parent in wanted' - "$sizes" | sort -rn | awk -v rows="$rows" 'NR <= rows' | human
}

# Print the line for exactly this folder.
folder() {
  awk -F'\t' -v path="$1" '$2 == path' "$sizes" | human
}

section "Free space (KiB; df -k)"
if ! df -k /System/Volumes/Data | tail -1; then
  status=1
fi

# One walk of the home folder, three levels deep, feeds every section below.
if ! du -xk -d 3 ~ >"$sizes" 2>"$errors"; then
  echo "Incomplete measurement; folder sizes below may be too small." >&2
  awk 'NR <= 5 { print } END { if (NR > 5) print "... further errors omitted" }' "$errors" >&2
  status=1
fi

section "Home folder"
folder ~
children ~

section "~/Library"
children ~/Library

section "~/Library subfolders"
children ~/Library/Application\ Support ~/Library/Group\ Containers ~/Library/Containers ~/Library/Caches ~/Library/Developer

section "~/.cache and ~/.local/share"
children ~/.cache ~/.local/share

section "Trash"
folder ~/.Trash

# Only ask Docker when a daemon socket exists, so the overview never starts
# OrbStack or Docker Desktop.
docker_running() {
  [[ -S ~/.orbstack/run/docker.sock || -S ~/.docker/run/docker.sock || -S /var/run/docker.sock ]]
}

if docker_running && docker info >/dev/null 2>&1; then
  section "Docker"
  docker system df || status=1
fi

exit "$status"
