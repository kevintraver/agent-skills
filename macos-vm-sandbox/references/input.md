# Input fidelity

Source: `https://cua.ai/docs/cua-driver/reference/mcp-tools/click-and-type.md` (macOS sections). Rows marked "per docs" haven't been proven in a run yet. Prove a route (below) before trusting test results that depend on it.

| Route | What macOS receives | Reaches session/HID event taps, input methods, keyboard hooks? |
|---|---|---|
| `type_text` (any `delivery_mode`) | AX insertion via `AXSetAttribute(kAXSelectedText)`; CGEvent typing only as a fallback where AX insertion is unsupported | No (AX path) |
| `press_key` / `hotkey` / `click`, `delivery_mode: "background"` (default) | events posted to the target pid | No |
| `press_key` / `hotkey`, `delivery_mode: "foreground"` + `window_id` | window fronted; events from the daemon's pid with `eventSourceStateID` 0 and a keycode but an **empty Unicode string** | Reaches session taps (verified with a listen-only tap), but **keycode only**. Fine for apps that key off keycodes. Apps that read the event's text see untranslatable letters and pass them through, while Escape and arrows still work, which is a false pass. |
| HID-state CGEvents, run as root in the GUI session | `CGEvent(keyboardEventSource: CGEventSource(stateID: .hidSystemState), …)` posted at `.cghidEventTap`, modifiers sent as real modifier key-down/up events | **Yes, verified.** Setting only the flags types the unshifted character and leaks Shift into the next key. Run it with `sbx ssh <vm> "sudo launchctl asuser \$(id -u lume) <tool> …"`; no TCC grant needed. |
| `cliclick` over `sbx ssh` | HID events attributed to `sshd-keygen-wrapper` | Unproven. The Cua image has an Accessibility row for `sshd-keygen-wrapper`, yet `cliclick -V` over SSH still warned "Accessibility privileges not enabled". |
| Electron / browser web content | Background `type_text` is refused, and AXValue read-back is `effect: "unverifiable"`, so it proves nothing about the DOM | Use a pixel click (`x, y` from `get_window_state`) followed by foreground keys, or the `page` tool for browser tabs. Verify through the app's log or a screenshot. |

`press_key` keys: return, tab, escape, up/down/left/right, space, delete, home, end, pageup, pagedown, f1–f12, any letter or digit. `modifiers`: cmd, shift, option/alt, ctrl, fn. Typing a word through foreground mode means one `press_key` per character.

Cua's docs tell agents to try `background` first and escalate to `foreground` only when needed. For apps that watch input, **override that**: background delivery "succeeds" while the app never sees the event, which gives false passes. For apps that translate typed text from key events, even foreground isn't enough: ship a small host-built tool that posts HID-state events (row above), and run it as root in the GUI session.

Root in the GUI session (`sudo launchctl asuser $(id -u lume) …`) also runs AX probes as trusted, without TCC grants. Plain `screencapture` as root fails ("could not create image from display"). Take screenshots with `cua-driver call get_desktop_state '{"screenshot_out_file":"/tmp/s.png"}'` instead.

## Prove delivery before trusting results

1. Find the target window. Print the raw output first, with no `2>/dev/null` and no jq yet: `cua-driver call list_windows '{"pid":<pid>}'`. Read the window id field from that output, extract it, and **stop if it comes back empty**. A missing `window_id` makes every foreground call fail, and a filtered probe hides that as a silent no-op.
2. Send a few keys, including **letters**, Shift-modified letters and Escape, through the route you plan to use, and print each raw result. For Cua Driver: `cua-driver call press_key '{"pid":<pid>,"window_id":<id>,"key":"a","delivery_mode":"foreground"}'`.
3. Check **both** the app's own log or trace (did it see each key, *with its text*?) and the visible result (field contents through AppleScript or a screenshot). If only non-text keys work, the route carries keycodes without text. For a ground truth, run a listen-only session tap in the guest that logs each event's source pid, `eventSourceStateID` and Unicode string.
4. If foreground fails, try `cliclick` over SSH and prove it the same way, then try running the agent from Terminal in the GUI session (Terminal needs Accessibility).

Apps can also ignore events by `eventSourceUserData` tag. Don't reuse an app's own synthetic-event tag in test input.
