# Granting TCC permissions in a guest

Grant permissions once in a base; clones inherit them. Do it with the VM window open (`sbx boot <vm>` without `--headless`) and guide the user step by step. The guest password is `lume` whenever System Settings asks.

While the user has a VM window open, say what's about to happen before any shutdown, clone or boot. Otherwise the window closing or reopening looks like a crash.

## Open the right pane

`sbx pane <vm> accessibility|input-monitoring|screen-recording|automation` jumps straight to **Privacy & Security** → that list. Use it; the sidebar's top-level "Accessibility" item is the accessibility *features* page, and users land there by mistake.

## Adding an app that isn't listed

Lists start empty, and apps often don't appear on their own. For each grant:

1. Click **+** under the list and enter the `lume` password.
2. Press **⌘⇧G** and type the **full path**: `/Applications/CuaDriver.app` or `/Users/lume/Applications/<App>.app`. A `~` may not expand in that box.
3. Click **Open** and make sure the toggle is on. Accept **Quit & Reopen** if offered.

## CuaDriver

Needs **Accessibility** and **Screen Recording**, plus two runtime consents (System Events automation, direct screen capture):

1. Add `/Applications/CuaDriver.app` under Accessibility and under Screen & System Audio Recording, as above.
2. Changing a grant can kill the daemon. Restart it and request the remaining consents **from the host**; it launches the app in the guest's GUI session, so attribution is correct:
   ```sh
   sbx ssh <vm> '(~/.local/bin/cua-driver permissions grant > /tmp/grant.log 2>&1 &); sleep 15; cat /tmp/grant.log'
   ```
   The user clicks **Allow** on any direct-capture prompt in the VM window.
3. Verify:
   ```sh
   sbx ssh <vm> '~/.local/bin/cua-driver permissions status --json'   # accessibility/screen_recording true, source.attribution "driver-daemon"
   sbx ssh <vm> '~/.local/bin/cua-driver list_apps "{}" >/dev/null && ~/.local/bin/cua-driver call get_desktop_state "{}" >/dev/null && echo no-prompts'
   ```
   `status: unknown` means "rerun `permissions grant`", whether `daemon_running` is false (daemon gone) or true (daemon up but its real TCC status not read yet).

## The app under test

Grant whatever the app needs. Common: **Accessibility**, **Input Monitoring** (event taps), **Screen Recording**. Launch the app first (`sbx ssh <vm> 'open ~/Applications/<App>.app'`); apps that request access may add themselves to the list.

## Verify from the host

```sh
sbx grants <vm> [bundle-id-fragment]     # rows from the system TCC.db; auth_value 2 = allowed
```

Services: `kTCCServiceAccessibility`, `kTCCServiceListenEvent` (Input Monitoring), `kTCCServiceScreenCapture`. A row only shows the grant was copied; it doesn't prove it works. The smoke clone (SKILL.md step 3) proves that. The Cua image has an Accessibility row for `/usr/libexec/sshd-keygen-wrapper`, so `cliclick` over SSH *may* post HID input. Prove it first (input.md).

## Fully automated grants (SIP-off guests only)

Cua ships helpers that write TCC rows and the screen-capture approval plist directly, refusing to run unless the guest is a VM with SIP off: `libs/cua-driver/tests/runners/macos-lume/seed-tcc.sh` and `seed-screencapture-approvals.sh` in `trycua/cua`. They cover Accessibility and Screen Recording for one app; Input Monitoring and Automation would need extending. This skips the real permission flow, so it suits rebuilding bases often, not one-off setups.
