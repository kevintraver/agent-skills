#!/bin/bash
# List each third-party Homebrew tap with what is installed from it.
# Taps marked UNUSED have nothing installed and can be untapped.

installed=$(brew info --json=v2 --installed |
  jq -r '(.formulae[] | "\(.tap)\t\(.name)"), (.casks[] | "\(.tap)\t\(.token)")')

for tap in $(brew tap); do
  case $tap in homebrew/*) continue ;; esac
  names=$(awk -F'\t' -v t="$tap" '$1 == t { printf "%s%s", sep, $2; sep = ", " }' <<<"$installed")
  printf '%-40s %s\n' "$tap" "${names:-UNUSED}"
done
