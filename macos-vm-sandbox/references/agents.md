# Where the agent runs

Cua Driver always runs in the guest. Pick how the scenario is driven:

- **Steps already known → a script, no agent.** Deterministic, seconds instead of minutes, no token in the guest.
- **Exploring scenarios at scale (sweeps, scheduled runs) → Claude inside the guest.**
- **Developing or debugging one failure → Claude on the host**, driving the guest over MCP.

| | Claude inside the guest | Claude on the host, driving the guest over MCP |
|---|---|---|
| Blast radius | the clone, **plus** the injected Claude token (the agent can read it) and the guest's network access | the host (shell, files, credentials); only GUI actions are in the VM |
| Prompts | `--dangerously-skip-permissions` is safe: unattended | normal prompts on the host: supervised |
| Source and build | must be copied in | full access; edit → build → test in one session |
| Context | fresh per run; needs a self-contained scenario | keeps the conversation |

## Running scenarios: `scripts/run-scenarios`

One scenario per file, each in a fresh clone of the base its header names, as many at once as there are free VM slots. Run it with no arguments for usage.

```sh
scripts/run-scenarios [--build path/App.app] [--rules rules.md] [--out results] scenarios/*
```

- **`*.sh` (scripted):** runs in the guest with bash; exit 0 is a pass. Send input through a proven route (input.md) and judge by the app's log and the field's contents.
- **`*.md` (guest Claude):** a scenario file states which apps, the steps, and the expected result. The runner prepends `--rules` and passes `CLAUDE_CODE_OAUTH_TOKEN` from the host env through stdin. A finished run is `done`, not `pass`; the verdict is in its `report.md`.
- Header lines (first 10 lines): `# base: <app>-base` (or `<!-- base: … -->` in Markdown) and optionally `# collect: <guest paths relative to ~>` to copy back.
- `--build` replaces the app in each clone's `~/Applications`. It must keep the base's signing identity, or the clone loses the app's grants.
- Results: `<out>/<timestamp>/<scenario>/` with `status`, `run.log` and the collected files. Summarize from there.

While writing a scenario, keep one clone running and rerun against it with `sbx scp` + `sbx ssh` instead of cloning per attempt. Run the finished scenario through the runner before trusting it.

The rules file should fix the input route (input.md), name the oracle (the app's log beats screenshots), and require `~/report.md` with pass or fail, evidence, steps to reproduce, and the guest's `sw_vers` output.

## Claude inside the guest

- Claude Code and the `cua-driver` MCP server are already in `cua-base` (scripts/cua-driver-install.sh).
- **Login:** don't store tokens in bases. Create a long-lived token on the host with `claude setup-token` and keep it in a secret store (for unattended runs, one that can be read without a prompt, such as a 1Password service account with `op read`). Inject the token per run **through stdin**, never on a command line, where host and guest `ps` would show it. `run-scenarios` does this; by hand:
  ```sh
  printf '%s' "$TOKEN" | sbx ssh run-x 'IFS= read -r t; CLAUDE_CODE_OAUTH_TOKEN="$t" ~/.local/bin/claude --dangerously-skip-permissions -p "$(cat ~/scenario.md)"'
  ```
  The agent can still read the token from its own environment, and the guest has network access. Use a token you're willing to rotate.

## Claude on the host

Register the guest's Cua Driver as an MCP server through `sbx`, which looks up the clone's IP on every connect:

```sh
claude mcp add cua-driver-vm -- <skill-dir>/scripts/sbx ssh run-dev /Users/lume/.local/bin/cua-driver mcp
```

Reuse the clone name (`run-dev`) across clones and the registration keeps working.

## Limits of sandbox results

The guest's macOS may differ from the host's (the Cua image can lag the newest release). Before concluding, confirm any failure that touches OS behavior (event taps, TCC, accessibility) on the host's macOS version.

Sandbox runs can't show some things. Grants were added by hand in the base, so the app's own permission onboarding never runs. SIP is off in the Cua image, unlike on users' Macs. Test those on a real Mac.
