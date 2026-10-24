# Where the agent runs

Cua Driver always runs in the guest. Claude can run in either place:

| | Claude inside the guest | Claude on the host, driving the guest over MCP |
|---|---|---|
| Blast radius | the clone, **plus** the injected Claude token (the agent can read it) and the guest's network access | the host (shell, files, credentials); only GUI actions are in the VM |
| Prompts | `--dangerously-skip-permissions` is safe: unattended | normal prompts on the host: supervised |
| Source and build | must be copied in | full access; edit → build → test in one session |
| Context | fresh per run; needs a self-contained scenario | keeps the conversation |
| Best for | many isolated scenarios, compatibility sweeps, scheduled runs | active development and debugging one failure |

For "test the app across many scenarios in isolation", run Claude inside the guest.

## Claude inside the guest

- Claude Code and the `cua-driver` MCP server are already in `cua-base` (scripts/cua-driver-install.sh).
- **Login:** don't store tokens in bases. Create a long-lived token on the host with `claude setup-token` and keep it in a secret store. For prompt-free reads on unattended runs, use the 2password skill's service-account path. Inject the token per run **through stdin**, never on a command line, where host and guest `ps` would show it:
  ```sh
  printf '%s' "$TOKEN" | sbx ssh run-x 'IFS= read -r t; CLAUDE_CODE_OAUTH_TOKEN="$t" ~/.local/bin/claude --dangerously-skip-permissions -p "$(cat ~/scenario.md)"'
  ```
  The agent can still read the token from its own environment, and the guest has network access. Use a token you're willing to rotate.
- `~/.local/bin` is on PATH only for login shells (`~/.zprofile`). Use full paths in non-interactive `sbx ssh` commands.

## Claude on the host

```sh
ip=$(lume get run-x --format json | jq -r '.[0].ipAddress')
claude mcp add cua-driver-vm -- ssh -T -o BatchMode=yes -i ~/.ssh/lume_sandbox.pub -o IdentitiesOnly=yes lume@$ip /Users/lume/.local/bin/cua-driver mcp
```

Each clone gets a new IP, so re-register (or wrap the IP lookup in a script) per clone.

## Scenario runner pattern

One scenario per file; each run gets a fresh clone; at most 2 in parallel.

```
for each scenarios/*.md (2 at a time):
  sbx up <app>-base run-<scenario> --headless
  sbx scp run-<scenario> <fresh build> :Applications/          # if testing a new build (same signing identity)
  sbx scp run-<scenario> scenarios/<scenario>.md :scenario.md
  sbx ssh run-<scenario> 'open ~/Applications/<App>.app'
  sbx ssh run-<scenario> "<token> ~/.local/bin/claude --dangerously-skip-permissions -p \"$RULES\n\n\$(cat ~/scenario.md)\""
  sbx scp run-<scenario> :report.md :<app log> :screenshots results/<timestamp>/<scenario>/
  sbx down run-<scenario>
then summarize results/<timestamp>/*/report.md
```

`$RULES` should fix the input route (see input.md), name the oracle (the app's log beats screenshots), and require `~/report.md` with pass or fail, evidence, steps to reproduce, and the guest's `sw_vers` output. A scenario file states: which apps, the steps, and the expected result.

The guest's macOS may differ from the host's (the default image is a version behind). Before concluding, confirm any failure that touches OS behavior (event taps, TCC, accessibility) on the host's macOS version.
