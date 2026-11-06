---
name: adguard-dns
description: Inspect and manage an AdGuard DNS (adguard-dns.io private DNS) account through its API — find which domains were blocked, search the DNS query log, list devices and DNS servers, add or remove allow/block user rules, and reach a blocked site for a task without unblocking it. Use when the user mentions AdGuard DNS, when a website, app, or streaming service isn't working and AdGuard DNS may be blocking it ("Netflix won't load", "what got blocked?", "unblock this domain", "whitelist X", "block X"), or when a public website fails to load during a task, not localhost, with ERR_CONNECTION_REFUSED, ERR_NAME_NOT_RESOLVED, or a similar connection error.
---

# AdGuard DNS

Use the bundled CLI, resolving its path relative to this skill directory:

```bash
python3 <skill-directory>/scripts/adguard.py <command> [--json] [--server ID] ...
```

| Command                                                                                           | Purpose                                                                                        |
| ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `blocked [--minutes 15 \| --from T [--to T]] [--search X] [--device NAME]`                        | Blocked queries grouped by root domain, with subdomains, counts, devices and what blocked them |
| `log [--minutes 15 \| --from T [--to T]] [--search X] [--status S] [--device NAME] [--limit 200]` | Raw query log, newest first                                                                    |
| `rules [--search X]`                                                                              | List the DNS server's user rules                                                               |
| `allow DOMAIN... [--exact] [--dry-run]`                                                           | Add `@@\|\|domain^` allow rules                                                                |
| `block DOMAIN... [--exact] [--dry-run]`                                                           | Add `\|\|domain^` block rules                                                                  |
| `remove-rule RULE... [--dry-run]`                                                                 | Remove user rules by exact text                                                                |
| `servers`, `devices`                                                                              | List DNS servers (IDs, default) and devices                                                    |

Pass `--json` for structured output. Requires only Python 3.9+.

## Credentials

- `ADGUARD_DNS_API_KEY` (required): created in the AdGuard DNS dashboard under **User preferences → API keys**. Sent as `Authorization: ApiKey <key>`; it doesn't expire. If it isn't set, find the key with a password-manager skill if one is available (search for an AdGuard DNS API key) and pass it to the script as this variable without printing it. Otherwise, ask the user to set it. Never print the key.
- `ADGUARD_DNS_SERVER_ID` (optional): which DNS server to use; `--server` overrides it. Without either, `blocked` and `log` search every server, and rule commands use the account's default DNS server. If the account has several servers and none is default, rule commands stop; run `servers` and pass `--server`.

## Time frames

`--minutes N` means the last N minutes, ending now. For any other period, convert the user's wording into explicit local times. Pass them as `--from "YYYY-MM-DD HH:MM"` and, optionally, `--to` (default: now). All output times are local.

1. Run `date` first to get today's date; never guess it.
2. Map vague phrases to concrete hours. Use these defaults unless the user says otherwise:
   - morning 06:00–12:00, afternoon 12:00–17:00, evening 17:00–22:00
   - "last night" 18:00 yesterday → 06:00 today
   - "yesterday" 00:00 → 00:00 today
   - "around 3pm" 14:30–15:30
3. State the window you used in your answer ("Yesterday evening, Oct 6 17:00–22:00"), so the user can correct it.
4. If the output says it stopped at the newest N queries, narrow the window or add `--search`, `--device` or `--status`; for `log`, raise `--limit`.
5. An empty result for an older window may mean the log has aged out (retention depends on the plan) or logging was off. Say so instead of reporting that nothing was blocked.

## Troubleshooting a broken site or app

1. Run `blocked` right away; don't interrogate the user first. Use a short window (`--minutes 5–15`) right after they reproduce the problem; widen it if nothing shows. Narrow with `--device` or `--search` when the user names a device or service.
2. Present the results grouped by root domain. Separate likely culprits (the service's own domains, its CDN, auth or API hosts) from noise (ads, trackers, analytics), which blocks on every page load and is rarely the cause.
3. Ask which to unblock and confirm before running `allow`. Rule changes apply to every device on that DNS server. Use `--dry-run` to preview when it is unclear what will change.
4. After unblocking, tell the user that clients cache DNS. Changes can take a minute or two; restarting the app or flushing the cache helps (macOS: `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`).

## Reaching a blocked site without unblocking it

If a public site won't load in agent-browser, AdGuard DNS may be blocking it. Check with `blocked --minutes 15 --search <root domain>`. If it is, tell the user AdGuard DNS blocked it, give the reason, and ask what to do. If they want to continue, use the override for that domain only.

### Local override in agent-browser

Look up each hostname's IP with a public resolver such as 1.1.1.1, then use a dedicated session and export the rule in every shell call that touches it. Add a `MAP` for each hostname, comma-separated.

```bash
export AGENT_BROWSER_ARGS="--host-resolver-rules=MAP www.example.com 203.0.113.10"
agent-browser --session adguard-bypass open https://www.example.com/
agent-browser --session adguard-bypass get url
# when the task is done
agent-browser --session adguard-bypass close
```

## Rule behavior

- `allow` and `block` default to the **root domain** (`api-global.netflix.com` → `netflix.com`), because services spread across many subdomains and `||domain^` also matches every subdomain.
- Check the `blocked by:` line before choosing. When a rule blocks one subdomain (`||ort.wellsfargo.com^`), allowing only that subdomain with `--exact` fixes the block and keeps filtering every other tracker under the root. Offer the root when several subdomains of a service are blocked, or when the rule itself targets the root.
- Use `--exact` for shared infrastructure, where the root would open up far too much: `cloudfront.net`, `amazonaws.com`, `akamaihd.net`, `googleapis.com`, `azureedge.net`, `fastly.net`, and similar. Also use it whenever the user names a specific subdomain on purpose.
- `allow` removes a conflicting `||domain^` block rule for the same domain, and `block` removes a conflicting allow rule. The output reports this.
- Root extraction knows only common two-part TLDs (`co.uk`, `com.au`, etc.). For other country-code TLDs, check the result and use `--exact` if it is wrong.
- If the output warns that user rules are disabled on the server, the rules do nothing until they are re-enabled in the dashboard.
- `blocked by:` names what blocked each domain: a `filter list` or `user rule` (allow rules fix these), or a server setting such as a `blocked service`, `parental control` or `safe browsing`. For a server setting, point the user to that setting in the dashboard instead of adding allow rules.

## Beyond the CLI

For endpoints the script doesn't cover (statistics, device settings, filter lists, blocked services), see [references/api.md](references/api.md).

AdGuard's own `adguarddns-cli` (github.com/AdguardTeam/AdGuardDNSCLI) is a local encrypted-DNS forwarder, not an account management tool. It cannot read logs or edit rules.
