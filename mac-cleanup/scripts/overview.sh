#!/bin/bash
# Print where disk space is going: the home folder, system folders, and how much
# of the used space those measurements explain.
# Usage: overview.sh [rows]   (rows per section, default 15)
# Exits nonzero when part of the home folder could not be read. System folders
# are always partly unreadable without root; their rows say so instead.

set -o pipefail

rows=${1:-15}
if (($# > 1)) || [[ ! $rows =~ ^[1-9][0-9]*$ ]]; then
  echo "Usage: overview.sh [positive row count]" >&2
  exit 1
fi
status=0
errors=$(mktemp) || exit 1
sizes=$(mktemp) || exit 1
blocked=$(mktemp) || exit 1
system_errors=$(mktemp) || exit 1
system_sizes=$(mktemp) || exit 1
trap 'rm -f "$errors" "$sizes" "$blocked" "$system_errors" "$system_sizes"' EXIT

section() { printf '\n== %s\n' "$1"; }

# Pull the unreadable paths out of du's "du: <path>: <reason>" error lines.
unreadable_paths() {
  awk '/: (Operation not permitted|Permission denied)$/ {
    line = $0
    sub(/^du: /, "", line)
    sub(/: [^:]*$/, "", line)
    print line
  }' "$@"
}

# Turn "KiB<TAB>path" lines into du -h style output. Rows with unreadable
# paths at or below them are marked, since their size is too small.
human() {
  awk -F'\t' -v blocked="$blocked" '
    BEGIN { while ((getline line < blocked) > 0) paths[++count] = line }
    {
      kb = $1
      size = kb >= 1048576 ? sprintf("%.1fG", kb / 1048576) : kb >= 1024 ? sprintf("%.0fM", kb / 1024) : kb "K"
      unreadable = 0
      for (i = 1; i <= count; i++)
        if (paths[i] == $2 || index(paths[i], $2 "/") == 1) unreadable++
      note = unreadable ? sprintf("  (incomplete: %d unreadable)", unreadable) : ""
      printf "%7s  %s%s\n", size, $2, note
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
  unreadable_paths "$errors" >"$blocked"
  if [[ -s $blocked ]]; then
    # Group by the first two folders under home, so hundreds of errors in
    # ~/Library/Containers read as one line.
    echo "Unreadable paths by folder:" >&2
    awk -v home="$HOME" '{
      group = $0
      if (index(group, home "/") == 1) {
        rest = substr(group, length(home) + 2)
        n = split(rest, part, "/")
        group = "~/" part[1] (n > 1 ? "/" part[2] : "")
      }
      count[group]++
    } END { for (g in count) printf "%7d  %s\n", count[g], g }' "$blocked" | sort -rn | awk -v rows="$rows" 'NR <= rows' >&2
  fi
  awk '!/: (Operation not permitted|Permission denied)$/' "$errors" | awk 'NR <= 5 { print } END { if (NR > 5) print "... further errors omitted" }' >&2
  if grep -q 'Operation not permitted$' "$errors"; then
    echo "macOS privacy protection blocked some folders; their sizes are unmeasured, not small." >&2
    echo "To measure them, give the terminal app Full Disk Access (System Settings > Privacy & Security > Full Disk Access) and rerun." >&2
  fi
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

# Space outside the home folder. -s keeps this to one total per folder.
section "System folders"
system_roots=()
for root in /Applications /opt/homebrew /Library /private/var; do
  [[ -d $root ]] && system_roots+=("$root")
done
if ((${#system_roots[@]})); then
  du -sxk "${system_roots[@]}" >"$system_sizes" 2>"$system_errors"
  unreadable_paths "$system_errors" >>"$blocked"
  sort -rn "$system_sizes" | human
fi

# Compare what was measured with what df reports as used, so a large gap is
# visible instead of being put down to "system files".
section "Measured vs used"
df -k /System/Volumes/Data | tail -1 | awk -v home="$HOME" -v sizes="$sizes" -v system_file="$system_sizes" '
  function gib(kb) { return sprintf("%.1f GiB", kb / 1048576) }
  BEGIN {
    FS = "\t"
    while ((getline line < sizes) > 0) { split(line, f, "\t"); if (f[2] == home) measured += f[1] }
    while ((getline line < system_file) > 0) { split(line, f, "\t"); measured += f[1] }
    FS = " "
  }
  {
    used = $3
    printf "%s used; %s measured above; %s unexplained\n", gib(used), gib(measured), gib(used > measured ? used - measured : 0)
  }'
echo "Unexplained space includes unreadable folders (marked above), other system folders, and APFS snapshots (tmutil listlocalsnapshots /)."

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
