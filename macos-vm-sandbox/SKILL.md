---
name: macos-vm-sandbox
description: Build and use disposable macOS sandbox VMs on Apple silicon with Lume and Cua Driver, so an agent can drive any Mac app's GUI (clicks, keys, screenshots) in isolation and reset to a clean state after every run. Use when asked to test a Mac app in a VM or sandbox, run a computer-use agent against a macOS desktop, set up Lume or Cua Driver, make a base or golden VM image for an app, clone, reset or snapshot a sandbox VM, or run test scenarios in throwaway macOS clones.
---

# macOS VM sandbox (Lume + Cua Driver)

Disposable macOS guests on Apple silicon. Lume runs the VMs (Apple Virtualization.framework). Cua Driver, inside the guest, gives an agent screenshots, the accessibility tree, clicks and keys over MCP. A frozen base acts as the snapshot: every run is a copy-on-write clone that gets deleted afterwards. Booting is the slow part of a run, so scenarios on the same base share one, reset between them, rather than each booting its own. A clone's disk is shared with its base until written, so a leftover clone costs a few GB, not the 30 GB `du` reports.

Paths below (`scripts/…`, `references/…`) are relative to this skill's directory; use full paths when running them. Bundled scripts:

- `scripts/sbx`: host-side CLI (`ssh`, `scp`, `up`, `boot`, `freeze`, `down`, `grants`, `pane`). Run it with no arguments for usage. Commands below call it `sbx`. `up` and `boot` also start the Cua Driver daemon and mute the guest.
- `scripts/run-scenarios`: runs scenario files, one clone per base, and collects results (references/agents.md).
- `scripts/hidtype.swift`: full-fidelity keyboard input (references/input.md).

## Layered bases

```
cua-base            generic: Homebrew, jq, cliclick, Claude Code, Cua Driver + its grants
└── <app>-base      + the app under test, apps it interacts with, the app's own grants
      └── run-*     throwaway clones, one per base per run
```

- Bases stay **stopped**. Never test in a base: changes leak into every later clone.
- Change a layer by cloning it, editing, freezing, then rebuilding the layers below it.
- Clones keep TCC grants only while each granted app keeps the **same code signature**. Ad-hoc-signed rebuilds lose them.

## Workflow

1. **Check state:** `lume ls`. If `cua-base` already exists and is stopped, skip to step 3.
2. **Build `cua-base`:** follow [references/setup.md](references/setup.md) (installs, image pull, SSH key, guest scripts), then [references/permissions.md](references/permissions.md) for the CuaDriver grants. The grants need a few human clicks in the VM window, so walk the user through them one at a time.
3. **Build `<app>-base`:**
   ```sh
   lume clone cua-base <app>-base && sbx boot <app>-base
   sbx scp <app>-base path/to/App.app :Applications/          # local builds
   sbx ssh <app>-base 'bash -s -- <formulas> --cask <casks>' < scripts/guest-apps.sh
   ```
   Grant the app's permissions (references/permissions.md) and launch each app once to clear first-run screens.

   To enable the app's debug logging, use its UI if you can. To set it from the shell: quit the app first (a running app overwrites its UserDefaults on quit), **merge** the key into the existing preferences rather than replacing the domain or a whole settings blob, relaunch, and confirm the log file appears. Then `sbx freeze <app>-base`.

   **Smoke-test in a clone, never in the base.** Run `sbx up <app>-base smoke-1 --headless`, then over `sbx ssh smoke-1`:
   - check `~/.local/bin/cua-driver permissions status --json`
   - take one real screenshot: `~/.local/bin/cua-driver call get_desktop_state '{"screenshot_out_file":"/tmp/s.png"}'`
   - prove input delivery (references/input.md)

   Then `sbx down smoke-1`. If anything fails, fix the base by clone → edit → refreeze; never clean up a base in place.
4. **Run:** `sbx up <app>-base run-<name> [--headless]` → do the work → collect artifacts with `sbx scp` → `sbx down run-<name>`. For a batch of scenarios, use `scripts/run-scenarios`.
5. **Choose where the agent runs** (scripted, Claude in the guest, or Claude on the host): see [references/agents.md](references/agents.md).
6. **Hand off** (when another session will do the testing): send one message, only after the bases are frozen and the smoke test passed. Point it at this skill and `sbx`.

## Input fidelity (read before testing anything that watches the keyboard)

Cua Driver's default routes (`type_text`, background `press_key`) never reach event taps, input methods or keyboard hooks, and foreground keys carry no text. They report success anyway, so tests pass falsely. Prove delivery with letters, Shift and Escape before trusting results, using the app's own log as the oracle. Routes, `hidtype` and the proof recipe are in [references/input.md](references/input.md).

## Gotchas

- At most **2 macOS VMs run at once** per host (Apple's license, enforced by the framework), and that includes VMs other sessions started. `sbx up`/`boot` refuse when two are already running; check `lume ls` before planning parallel runs.
- **Two clones booting at once each boot slower**, past the SSH wait one boot alone fits in. `sbx up`/`boot` wait `$SBX_SSH_WAIT` seconds (default 300). `sbx up` deletes the clone it made when the boot fails, so a failed `up` never holds one of the two slots.
- **Every VM, even with `--display none`, starts a VNC server on the host's LAN address** (`external=vnc://…@<lan-ip>:<port>` in `~/.lume/logs/<vm>.log`). That's password-only access to a guest with SIP off and passwordless sudo. Run sandboxes only on trusted networks, or block the port in the host firewall.
- Commands sent through `sbx ssh` run in the guest's **zsh** with PATH `/usr/bin:/bin:/usr/sbin:/sbin`: use full paths (`~/.local/bin/cua-driver`, `~/.local/bin/claude`, `/opt/homebrew/bin/…`). An unmatched glob aborts the whole line, and macOS has no `timeout`. Wrap glob-bearing commands in `bash -c '…'`, and bound long commands with `(cmd >/tmp/x.log 2>&1 &); sleep N; cat /tmp/x.log`.
- The guest can't be newer than the host. The macOS version is fixed by the image; see setup.md for choices.
- The Lume notes here were checked against **lume 0.6.1**; if `lume --version` differs, recheck them. In 0.6.1 there is **no `cp`**, even though its docs list one, and `lume ssh` **drops stdin**. Use `sbx scp` and `sbx ssh`.
- **A guest's sound plays on the host**, including the beep for every key an app rejects, and the guest's microphone input is the host's. Lume attaches both with no setting to turn them off. `sbx up`/`boot` mute the output; the microphone stays live.
- Lume's native viewer doesn't scale the guest display. Keep it at 1024×768 or the window gets cut off.
- Keep secrets out of frozen bases: no tokens, private keys or personal files. Inject per run.
- iCloud and Apple ID features are unreliable in VMs. Apps that need a phone-linked account (Signal, WhatsApp) need a dedicated test account; prefer apps that work signed out.
