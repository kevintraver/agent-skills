#!/bin/bash
# Generic base tooling. Runs inside the guest as `lume`:
#   sbx ssh <vm> 'bash -s' < guest-base.sh
set -euo pipefail

echo "== passwordless sudo"
echo lume | sudo -S -p '' sh -c 'echo "lume ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/lume && chmod 440 /etc/sudoers.d/lume'

echo "== Homebrew"
if [ ! -x /opt/homebrew/bin/brew ]; then
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
grep -q 'brew shellenv' ~/.zprofile 2>/dev/null || echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
export HOMEBREW_NO_ANALYTICS=1 HOMEBREW_NO_ENV_HINTS=1
brew install jq cliclick

echo "== Claude Code"
command -v claude >/dev/null || curl -fsSL https://claude.ai/install.sh | bash
grep -q '.local/bin' ~/.zprofile || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zprofile

echo "== Versions"
sw_vers -productVersion
csrutil status
brew --version | head -1
~/.local/bin/claude --version
