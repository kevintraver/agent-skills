#!/bin/bash
# List each third-party Homebrew tap with what is installed from it.
# Taps marked UNUSED have nothing installed and can be untapped.

set -euo pipefail

installed=$(brew info --json=v2 --installed |
  jq -sr 'if length != 1 then error("Expected one Homebrew inventory") else
    .[0] | (.formulae[] | "\(.tap)\t\(.name)"), (.casks[] | "\(.tap)\t\(.token)")
    end')
taps=$(brew tap)

while IFS= read -r tap; do
  [[ -z $tap ]] && continue
  case $tap in homebrew/*) continue ;; esac
  names=$(awk -F'\t' -v t="$tap" '$1 == t { printf "%s%s", sep, $2; sep = ", " }' <<<"$installed")
  printf '%-40s %s\n' "$tap" "${names:-UNUSED}"
done <<<"$taps"
