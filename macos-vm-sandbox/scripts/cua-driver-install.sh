#!/bin/bash
# Install Cua Driver in the guest and wire it into Claude Code. Runs as `lume`:
#   sbx ssh <vm> 'bash -s' < cua-driver-install.sh
# Permissions are granted afterwards by hand (see references/permissions.md).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"

# With `bash -c`, the first argument after the script is $0, so pass a
# placeholder before the flag or the installer never sees it.
/bin/bash -c "$(curl -fsSL https://cua.ai/driver/install.sh)" _ --no-modify-path
cua-driver telemetry disable

# The standard server exposes delivery_mode; `mcp-config --client claude`
# (the computer-use compatibility profile) only prints a command.
claude mcp add --scope user --transport stdio cua-driver -- "$HOME/.local/bin/cua-driver" mcp
mkdir -p ~/.claude/skills
cua-driver skills install

cua-driver --version
ls -d /Applications/CuaDriver.app
claude mcp list
