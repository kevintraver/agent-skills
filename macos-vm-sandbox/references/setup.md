# Building cua-base

## Host prerequisites

- Apple silicon, about 60 GB free per base, `jq`.
- **Lume:** install with the official script, per the Cua docs. It installs to `~/.local/bin/lume` and `~/.local/share/lume/lume.app`, and adds LaunchAgent `com.trycua.lume_daemon` (`lume serve` on :7777). Read the script before running it.
  ```sh
  /bin/bash -c "$(curl -fsSL https://cua.ai/lume/install.sh)"
  lume config telemetry disable
  ```
  Homebrew core also has `lume` (same version, no LaunchAgent) if the user prefers that.
- DNS ad blockers can block a whole vendor domain (some lists include `cua.ai`). When a docs page, installer or registry fetch fails or silently does nothing, check the blocker's query log for that domain before calling the vendor down.
- Docs index: `https://cua.ai/docs/llms.txt`. Append `.md` to any docs page for raw Markdown.

## Choosing the guest image

| Option | Command | Notes |
|---|---|---|
| **Cua image (default)** | `lume pull macos-tahoe-cua:<tag> cua-base` | The base Cua maintainers test Cua Driver on: Setup Assistant done, autologin, SSH, Xcode CLT, **SIP disabled**, 150 GB sparse disk. Tags: `curl -fsSL -H "Authorization: Bearer $(curl -fsSL 'https://ghcr.io/token?scope=repository:trycua/macos-tahoe-cua:pull' \| jq -r .token)" https://ghcr.io/v2/trycua/macos-tahoe-cua/tags/list`. Pin a version tag, not `latest`. |
| Vanilla from an IPSW | `lume create cua-base --ipsw latest --unattended tahoe` | Presets exist only for `sequoia` and `tahoe`. On a newer macOS, the preset leaves Setup Assistant on a screen it doesn't know (seen on macOS 27: "Age Range"), so someone has to click through. Download the IPSW with `curl -C -` first (`lume ipsw` prints the URL) so a retry doesn't re-download it. |

Pulls are large (about 23 GB compressed for the Tahoe image) and ghcr.io can be slow, so expect anything up to a few hours. Run the pull in the background. Before a long pull, `lume config cache enable` lets an interrupted pull resume instead of restarting.

Progress can't be read as a percentage. Lume decompresses chunks out of order into `$TMPDIR/lume_vm_*/disk.img`, so disk growth doesn't map to the compressed total. Finished chunk temp files that stop changing are waiting to be written in order; they aren't stalled. Give the user **one** ETA (compressed total ÷ measured throughput), then report again when the pull finishes. Don't re-derive numbers on every poll. Compressed total:

```sh
tok=$(curl -fsSL "https://ghcr.io/token?scope=repository:trycua/<image>:pull" | jq -r .token)
curl -fsSL -H "Authorization: Bearer $tok" -H "Accept: application/vnd.oci.image.manifest.v1+json" \
  https://ghcr.io/v2/trycua/<image>/manifests/<tag> | jq '.layers | map(.size) | add / 1e9'
```

Once no pull is running, delete its leftovers (gigabytes, including partial chunks from retries). Use `find`, since a zsh `rm` glob aborts when one pattern has no match:

```sh
find "$TMPDIR" -maxdepth 1 \( -name 'CFNetworkDownload_*.tmp' -o -name 'lume_vm_*' -o -name 'lume_oci_*' \) -user "$(id -u)" -exec rm -rf {} +
```

After pulling, size the VM so two clones can run at once with room left for the host: at most a third or so of the host's cores and memory each, e.g. `lume set cua-base --cpu 6 --memory 12` on a 16-core, 32 GB host. Keep the display at 1024×768.

## SSH key (served by an SSH agent)

`sbx` uses `$LUME_SANDBOX_PUBKEY` (default `~/.ssh/lume_sandbox.pub`) with `IdentitiesOnly=yes`, and lets the SSH agent from `~/.ssh/config` supply the private key. Any SSH agent works; an example with 1Password:

```sh
op item create --category "SSH Key" --title "Lume Sandbox SSH Key" --vault <vault> --ssh-generate-key ed25519
op item get "Lume Sandbox SSH Key" --fields "public key" > ~/.ssh/lume_sandbox.pub
SSH_AUTH_SOCK=~/Library/Group\ Containers/2BUA8C4S2C.com.1password/t/agent.sock ssh-add -L | grep -c "$(cut -d' ' -f2 ~/.ssh/lume_sandbox.pub)"   # must print 1
```

Without 1Password, use a key on disk loaded into the macOS SSH agent: `ssh-keygen -t ed25519 -f ~/.ssh/lume_sandbox && ssh-add --apple-use-keychain ~/.ssh/lume_sandbox`.

With 1Password, pick a vault its SSH agent serves. By default that's only the Personal/Private vault, unless `~/.config/1Password/ssh/agent.toml` lists others. A key in any other vault fails silently, and the `ssh-add -L` check catches that. The first SSH use from each app triggers a 1Password approval prompt.

Install the key in the guest (`lume ssh` takes the command as an argument; stdin is dropped):

```sh
lume run cua-base &      # opens the viewer window
pub=$(cat ~/.ssh/lume_sandbox.pub)
lume ssh cua-base "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$pub' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
sbx ssh cua-base 'sw_vers; csrutil status'
```

Guest credentials: `lume` / `lume`.

## Guest tooling

```sh
sbx ssh cua-base 'bash -s' < scripts/guest-base.sh          # passwordless sudo, Homebrew, jq, cliclick, Claude Code
sbx ssh cua-base 'bash -s' < scripts/cua-driver-install.sh  # Cua Driver, telemetry off, MCP + skill for Claude Code
```

`cua-driver-install.sh` runs the installer over SSH, and **that route is untested**. The proven route is the one the Cua docs give: run the installer from Terminal inside the VM window. If the SSH install misbehaves (the app doesn't launch, or permission prompts are attributed to the wrong process), open Terminal in the window, run `/bin/bash -c "$(curl -fsSL https://cua.ai/driver/install.sh)"` there, then run the rest of the script over SSH.

Then grant CuaDriver's permissions (permissions.md), verify, and freeze:

```sh
sbx ssh cua-base '~/.local/bin/cua-driver permissions status --json; ~/.local/bin/cua-driver doctor'
sbx ssh cua-base 'osascript -e "quit app \"Terminal\"" -e "quit app \"System Settings\""'
sbx freeze cua-base
```

Leave Claude Code logged out in the base (see agents.md).
