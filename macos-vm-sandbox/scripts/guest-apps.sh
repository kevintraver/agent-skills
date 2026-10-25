#!/bin/bash
# App layer. Runs inside the guest as `lume`; installs Homebrew formulas and
# casks, then clears quarantine so Gatekeeper dialogs don't interrupt tests:
#   sbx ssh <vm> 'bash -s -- ripgrep --cask firefox' < guest-apps.sh
# App bundles copied in with `sbx scp` land in ~/Applications and are
# de-quarantined too.
set -euo pipefail
eval "$(/opt/homebrew/bin/brew shellenv)"
export HOMEBREW_NO_ANALYTICS=1 HOMEBREW_NO_ENV_HINTS=1

formulas=()
casks=()
mode=formula
for arg in "$@"; do
  case "$arg" in
    --cask) mode=cask ;;
    --formula) mode=formula ;;
    *) if [ "$mode" = cask ]; then casks+=("$arg"); else formulas+=("$arg"); fi ;;
  esac
done

[ ${#formulas[@]} -gt 0 ] && brew install "${formulas[@]}"
[ ${#casks[@]} -gt 0 ] && brew install --cask "${casks[@]}"

shopt -s nullglob
for app in /Applications/*.app ~/Applications/*.app; do
  xattr -dr com.apple.quarantine "$app" 2>/dev/null || true
done

echo "== Installed"
# ${arr[@]+...}: macOS bash 3.2 treats an empty array as unbound under set -u.
for c in ${casks[@]+"${casks[@]}"}; do brew info --cask --json=v2 "$c" | jq -r '.casks[0] | "\(.token) \(.installed)"'; done
for f in ${formulas[@]+"${formulas[@]}"}; do brew list --versions "$f"; done
ls -d ~/Applications/*.app 2>/dev/null || true
