---
name: adguard-dns
description: Inspect and manage an AdGuard DNS (adguard-dns.io private DNS) account through its API — find which domains were blocked, search the DNS query log, list devices and DNS servers, and add or remove allow/block user rules. Use when the user mentions AdGuard DNS, or when a website, app, or streaming service isn't working and AdGuard DNS may be blocking it ("Netflix won't load", "what got blocked?", "unblock this domain", "whitelist X", "block X").
---

# AdGuard DNS

Use the bundled CLI, resolving its path relative to this skill directory:

```bash
python3 <skill-directory>/scripts/adguard.py <command> [--json] [--server ID] ...
```

| Command | Purpose |
|---------|---------|
| `blocked [--minutes 15 \| --from T [--to T]] [--search X] [--device NAME]` | Blocked queries grouped by root domain, with subdomains, counts, devices and the blocking rule |
| `log [--minutes 15 \| --from T [--to T]] [--search X] [--status S] [--device NAME] [--limit 200]` | Raw query log, newest first |
| `rules [--search X]` | List the DNS server's user rules |
| `allow DOMAIN... [--exact] [--dry-run]` | Add `@@\|\|domain^` allow rules |
| `block DOMAIN... [--exact] [--dry-run]` | Add `\|\|domain^` block rules |
| `remove-rule RULE... [--dry-run]` | Remove user rules by exact text |
| `servers`, `devices` | List DNS servers (IDs, default) and devices |

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

## Rule behavior

- `allow` and `block` default to the **root domain** (`api-global.netflix.com` → `netflix.com`), because services spread across many subdomains and `||domain^` also matches every subdomain.
- Check the `rule:` line before choosing. When the rule blocks one subdomain (`||ort.wellsfargo.com^`), allowing only that subdomain with `--exact` fixes the block and keeps filtering every other tracker under the root. Offer the root when several subdomains of a service are blocked, or when the rule itself targets the root.
- Use `--exact` for shared infrastructure, where the root would open up far too much: `cloudfront.net`, `amazonaws.com`, `akamaihd.net`, `googleapis.com`, `azureedge.net`, `fastly.net`, and similar. Also use it whenever the user names a specific subdomain on purpose.
- `allow` removes a conflicting `||domain^` block rule for the same domain, and `block` removes a conflicting allow rule. The output reports this.
- Root extraction knows only common two-part TLDs (`co.uk`, `com.au`, etc.). For other country-code TLDs, check the result and use `--exact` if it is wrong.
- If the output warns that user rules are disabled on the server, the rules do nothing until they are re-enabled in the dashboard.
- A blocked entry with no `rule:` line was probably blocked by a server setting (blocked services, parental control, safe browsing) rather than a filter list. Point the user to that setting in the dashboard instead of adding allow rules.

## Beyond the CLI

For endpoints the script doesn't cover (statistics, device settings, filter lists, blocked services), see [references/api.md](references/api.md).

AdGuard's own `adguarddns-cli` (github.com/AdguardTeam/AdGuardDNSCLI) is a local encrypted-DNS forwarder, not an account management tool. It cannot read logs or edit rules.
