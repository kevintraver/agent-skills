#!/usr/bin/env python3
"""AdGuard DNS (private DNS service) CLI: inspect query logs and manage user rules.

Auth: ADGUARD_DNS_API_KEY (required). ADGUARD_DNS_SERVER_ID (optional) scopes all
commands to one server; without it, log queries cover every server and rule commands
use the account's default server. Standard library only.
"""

import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://api.adguard-dns.io"
BLOCKED_STATUSES = ["REQUEST_BLOCKED", "RESPONSE_BLOCKED"]
TWO_PART_TLDS = {"co.uk", "org.uk", "ac.uk", "com.au", "net.au", "co.nz", "co.za", "com.br", "co.jp", "com.mx"}


def api(method, path, params=None, body=None):
    api_key = os.environ.get("ADGUARD_DNS_API_KEY", "").strip()
    if not api_key:
        sys.exit("ADGUARD_DNS_API_KEY is not set. Create a key in the AdGuard DNS dashboard: User preferences → API keys.")
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"ApiKey {api_key}")
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"AdGuard API {method} {path} failed: {e.code} {e.read().decode(errors='replace')}")
    return json.loads(raw) if raw else None


def root_domain(domain):
    parts = domain.lower().rstrip(".").split(".")
    n = 3 if ".".join(parts[-2:]) in TWO_PART_TLDS else 2
    return ".".join(parts[-n:])


def clean_domain(value):
    return value.strip().removeprefix("@@").removeprefix("||").rstrip("^").rstrip(".").lower()


def explicit_server(server_arg):
    return server_arg or os.environ.get("ADGUARD_DNS_SERVER_ID", "").strip() or None


def resolve_server(server_arg):
    server_id = explicit_server(server_arg)
    if server_id:
        return server_id
    servers = api("GET", "/oapi/v1/dns_servers")
    default = next((s for s in servers if s.get("default")), None) or (servers[0] if len(servers) == 1 else None)
    if not default:
        names = ", ".join(f"{s['name']} ({s['id']})" for s in servers)
        sys.exit(f"Multiple DNS servers and none is default; pass --server. Servers: {names}")
    return default["id"]


def device_names():
    return {d["id"]: d["name"] for d in api("GET", "/oapi/v1/devices")}


def resolve_devices(values):
    if not values:
        return []
    names = device_names()
    ids = []
    for v in values:
        match = [i for i, n in names.items() if v == i or v.lower() == n.lower()]
        if not match:
            sys.exit(f"Unknown device '{v}'. Devices: {', '.join(names.values())}")
        ids.extend(match)
    return ids


def parse_time(value):
    try:
        dt = datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        sys.exit(f"Invalid time '{value}'. Use local 'YYYY-MM-DD HH:MM' (or ISO 8601 with an offset).")
    return int(dt.astimezone().timestamp() * 1000)


def local(millis, fmt="%Y-%m-%d %H:%M"):
    return datetime.datetime.fromtimestamp(millis / 1000).strftime(fmt)


def local_iso(millis):
    return datetime.datetime.fromtimestamp(millis / 1000).astimezone().isoformat(timespec="seconds")


def time_window(args):
    """Return (from_millis, to_millis, description) from --from/--to or --minutes."""
    now = int(time.time() * 1000)
    if args.start:
        start = parse_time(args.start)
        end = parse_time(args.end) if args.end else now
        if start >= end:
            sys.exit("--from must be earlier than --to.")
        return start, end, f"between {local(start)} and {local(end)}"
    if args.end:
        sys.exit("--to requires --from.")
    return now - args.minutes * 60_000, now, f"in the last {args.minutes} minutes"


def fetch_log(window, statuses=None, search=None, devices=None, servers=None, max_items=5000):
    """Return (items, truncated), newest first."""
    params = {"time_from_millis": window[0], "time_to_millis": window[1], "limit": min(1000, max_items)}
    if statuses:
        params["statuses"] = statuses
    if search:
        params["search"] = search
    if devices:
        params["devices"] = devices
    if servers:
        params["dns_servers"] = servers
    items = []
    while True:
        data = api("GET", "/oapi/v1/query_log", params)
        items.extend(data["items"])
        pages = data.get("pages") or []
        idx = next((i for i, p in enumerate(pages) if p.get("current")), None)
        more = idx is not None and idx + 1 < len(pages)
        if not more or len(items) >= max_items:
            return items[:max_items], more or len(items) > max_items
        params["cursor"] = pages[idx + 1]["page_cursor"]


def ago(millis):
    mins = int((time.time() * 1000 - millis) // 60_000)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins}m ago"
    return local(millis)


def cmd_servers(args):
    rows = [
        {
            "id": s["id"],
            "name": s["name"],
            "default": s.get("default", False),
            "devices": s.get("devices_count"),
            "user_rules": s["settings"]["user_rules_settings"]["rules_count"],
            "protection_enabled": s["settings"].get("protection_enabled"),
        }
        for s in api("GET", "/oapi/v1/dns_servers")
    ]
    emit(args, rows, lambda: "\n".join(
        f"{r['id']}  {r['name']}{'  [default]' if r['default'] else ''}  devices={r['devices']} rules={r['user_rules']}"
        for r in rows))


def cmd_devices(args):
    rows = [{"id": d["id"], "name": d["name"], "type": d.get("device_type"), "dns_server_id": d.get("dns_server_id")}
            for d in api("GET", "/oapi/v1/devices")]
    emit(args, rows, lambda: "\n".join(f"{r['id']}  {r['name']}  ({r['type']}, server {r['dns_server_id']})" for r in rows))


def cmd_blocked(args):
    server = explicit_server(args.server)
    servers = [server] if server else None
    window = time_window(args)
    items, truncated = fetch_log(window, BLOCKED_STATUSES, args.search, resolve_devices(args.device), servers)
    names = device_names() if items else {}
    groups = {}
    for it in items:
        root = root_domain(it["domain"])
        g = groups.setdefault(root, {"root": root, "attempts": 0, "last_millis": 0, "subdomains": {}, "rules": set(),
                                     "devices": set()})
        g["attempts"] += 1
        g["last_millis"] = max(g["last_millis"], it["time_millis"])
        g["subdomains"][it["domain"]] = g["subdomains"].get(it["domain"], 0) + 1
        rule = (it.get("filtering_info") or {}).get("filter_rule")
        if rule:
            g["rules"].add(rule)
        g["devices"].add(names.get(it.get("device_id"), it.get("device_id")))
    rows = sorted(groups.values(), key=lambda g: g["last_millis"], reverse=True)
    for g in rows:
        g["last_seen"] = local_iso(g["last_millis"])
        g["rules"] = sorted(g["rules"])
        g["devices"] = sorted(d for d in g["devices"] if d)

    def text():
        if not rows:
            return f"No blocked queries {window[2]}."
        out = [f"{len(rows)} blocked root domains ({len(items)} queries) {window[2]}:"]
        if truncated:
            out.append(f"(stopped at the newest {len(items)} queries; narrow the window to see earlier ones)")
        out.append("")
        for g in rows:
            out.append(f"{g['root']}  ({g['attempts']} queries, last {ago(g['last_millis'])}; {', '.join(g['devices'])})")
            for sub, n in sorted(g["subdomains"].items(), key=lambda kv: -kv[1]):
                if sub != g["root"]:
                    out.append(f"    {sub} ×{n}")
            if g["rules"]:
                out.append(f"    rule: {' | '.join(g['rules'])}")
        return "\n".join(out)

    emit(args, rows, text)


def cmd_log(args):
    server = explicit_server(args.server)
    servers = [server] if server else None
    statuses = [s.upper() for s in args.status] if args.status else None
    window = time_window(args)
    items, truncated = fetch_log(window, statuses, args.search, resolve_devices(args.device), servers, args.limit)
    names = device_names() if items else {}
    rows = [
        {
            "time": local_iso(it["time_millis"]),
            "domain": it["domain"],
            "type": it.get("dns_request_type"),
            "status": (it.get("filtering_info") or {}).get("filtering_status"),
            "rule": (it.get("filtering_info") or {}).get("filter_rule"),
            "device": names.get(it.get("device_id"), it.get("device_id")),
        }
        for it in items
    ]
    def text():
        if not rows:
            return f"No matching queries {window[2]}."
        lines = [
            f"{r['time'][:19].replace('T', ' ')}  {r['status'] or '-':<17} {r['type'] or '':<6} {r['domain']}  [{r['device']}]"
            + (f"  rule: {r['rule']}" if r["rule"] else "")
            for r in rows
        ]
        if truncated:
            lines.append(f"(showing the newest {len(rows)}; raise --limit or narrow the window for more)")
        return "\n".join(lines)

    emit(args, rows, text)


def get_rules(server_id):
    return api("GET", f"/oapi/v1/dns_servers/{server_id}/settings")["user_rules_settings"]


def put_rules(server_id, settings, rules):
    api("PUT", f"/oapi/v1/dns_servers/{server_id}/settings",
        body={"user_rules_settings": {"enabled": settings["enabled"], "rules": rules}})


def cmd_rules(args):
    settings = get_rules(resolve_server(args.server))
    rules = [r for r in settings["rules"] if not args.search or args.search.lower() in r.lower()]
    emit(args, {"enabled": settings["enabled"], "rules": rules},
         lambda: f"User rules {'enabled' if settings['enabled'] else 'DISABLED'} ({len(rules)} shown):\n" + "\n".join(rules))


def change_rules(args, allow):
    server_id = resolve_server(args.server)
    settings = get_rules(server_id)
    existing = settings["rules"]
    targets = []
    for d in args.domains:
        d = clean_domain(d)
        d = d if args.exact else root_domain(d)
        if d not in targets:
            targets.append(d)
    added, present, removed_opposite = [], [], []
    rules = list(existing)
    for d in targets:
        rule = f"@@||{d}^" if allow else f"||{d}^"
        opposite = f"||{d}^" if allow else f"@@||{d}^"
        if opposite in rules:
            rules.remove(opposite)
            removed_opposite.append(opposite)
        if rule in rules:
            present.append(rule)
        else:
            rules.append(rule)
            added.append(rule)
    result = {"server": server_id, "added": added, "already_present": present, "removed_conflicting": removed_opposite,
              "dry_run": args.dry_run}
    if (added or removed_opposite) and not args.dry_run:
        put_rules(server_id, settings, rules)
    emit(args, result, lambda: "\n".join(filter(None, [
        "DRY RUN — no changes made" if args.dry_run else None,
        f"{'Would add' if args.dry_run else 'Added'}: {', '.join(added)}" if added else None,
        f"Already present: {', '.join(present)}" if present else None,
        f"{'Would remove' if args.dry_run else 'Removed'} conflicting: {', '.join(removed_opposite)}" if removed_opposite else None,
        None if settings["enabled"] else "WARNING: user rules are disabled on this server, so rules have no effect.",
    ])))


def cmd_remove_rule(args):
    server_id = resolve_server(args.server)
    settings = get_rules(server_id)
    wanted = [r.strip() for r in args.rules]
    missing = [r for r in wanted if r not in settings["rules"]]
    rules = [r for r in settings["rules"] if r not in wanted]
    removed = [r for r in wanted if r not in missing]
    if removed and not args.dry_run:
        put_rules(server_id, settings, rules)
    emit(args, {"removed": removed, "not_found": missing, "dry_run": args.dry_run}, lambda: "\n".join(filter(None, [
        "DRY RUN — no changes made" if args.dry_run else None,
        f"{'Would remove' if args.dry_run else 'Removed'}: {', '.join(removed)}" if removed else None,
        f"Not found (must match exactly): {', '.join(missing)}" if missing else None,
    ])))


def emit(args, data, text):
    print(json.dumps(data, indent=2) if args.json else text())


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    query_server = argparse.ArgumentParser(add_help=False)
    query_server.add_argument("--server", help="DNS server ID (default: $ADGUARD_DNS_SERVER_ID, otherwise all servers)")
    rule_server = argparse.ArgumentParser(add_help=False)
    rule_server.add_argument("--server", help="DNS server ID (default: $ADGUARD_DNS_SERVER_ID, otherwise the account default)")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def command(name, help, server=None):
        return sub.add_parser(name, help=help, parents=[common] + ([server] if server else []))

    command("servers", "list DNS servers").set_defaults(fn=cmd_servers)
    command("devices", "list devices").set_defaults(fn=cmd_devices)

    b = command("blocked", "blocked queries grouped by root domain", query_server)
    b.add_argument("--minutes", type=int, default=15, help="window ending now (default 15)")
    b.add_argument("--from", dest="start", help="window start, local time 'YYYY-MM-DD HH:MM' (overrides --minutes)")
    b.add_argument("--to", dest="end", help="window end, local time (default: now)")
    b.add_argument("--search", help="only domains containing this text")
    b.add_argument("--device", action="append", help="device name or ID (repeatable)")
    b.set_defaults(fn=cmd_blocked)

    lg = command("log", "raw query log, newest first", query_server)
    lg.add_argument("--minutes", type=int, default=15, help="window ending now (default 15)")
    lg.add_argument("--from", dest="start", help="window start, local time 'YYYY-MM-DD HH:MM' (overrides --minutes)")
    lg.add_argument("--to", dest="end", help="window end, local time (default: now)")
    lg.add_argument("--search", help="only domains containing this text")
    lg.add_argument("--device", action="append", help="device name or ID (repeatable)")
    lg.add_argument("--status", action="append",
                    help="REQUEST_BLOCKED, RESPONSE_BLOCKED, REQUEST_ALLOWED, RESPONSE_ALLOWED, MODIFIED, NONE (repeatable)")
    lg.add_argument("--limit", type=int, default=200)
    lg.set_defaults(fn=cmd_log)

    r = command("rules", "list user rules", rule_server)
    r.add_argument("--search", help="only rules containing this text")
    r.set_defaults(fn=cmd_rules)

    for name, allow, desc in [("allow", True, "add @@||domain^ allow rules"), ("block", False, "add ||domain^ block rules")]:
        c = command(name, f"{desc} (root domain unless --exact)", rule_server)
        c.add_argument("domains", nargs="+")
        c.add_argument("--exact", action="store_true", help="use the domain as given instead of its root domain")
        c.add_argument("--dry-run", action="store_true")
        c.set_defaults(fn=lambda a, allow=allow: change_rules(a, allow))

    rm = command("remove-rule", "remove user rules by exact text", rule_server)
    rm.add_argument("rules", nargs="+")
    rm.add_argument("--dry-run", action="store_true")
    rm.set_defaults(fn=cmd_remove_rule)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
