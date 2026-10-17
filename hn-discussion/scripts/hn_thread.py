#!/usr/bin/env python3
"""Dump a Hacker News story's full comment tree.

The story is an HN item URL, a numeric ID, or a title searched with HN Search.
With no story given, it is the most-commented story of the last --hours.

Prints a JSON summary to stdout and writes every live comment to a text file,
one per line, indented two spaces per reply depth.
"""

import argparse
import html
import json
import re
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

FIREBASE = "https://hacker-news.firebaseio.com/v0"
ALGOLIA = "https://hn.algolia.com/api/v1/search_by_date"
ALGOLIA_SEARCH = "https://hn.algolia.com/api/v1/search"
ALGOLIA_MAX_HITS = 1000
# Algolia's comment counts can lag, so re-check this many leaders against Firebase.
VERIFY = 30


def get_json(url, attempts=3):
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return json.load(resp)
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(1 + attempt)


def item(item_id):
    return get_json(f"{FIREBASE}/item/{item_id}.json")


def algolia_counts(cutoff):
    """Map story/poll id -> comment count for everything posted after cutoff."""
    counts = {}
    before = None
    # Algolia returns at most 1000 hits per query, so walk backward through time.
    while True:
        filters = f"created_at_i>{int(cutoff)}"
        if before:
            filters += f",created_at_i<={before}"
        query = urllib.parse.urlencode(
            {"tags": "(story,poll)", "hitsPerPage": ALGOLIA_MAX_HITS, "numericFilters": filters}
        )
        hits = get_json(f"{ALGOLIA}?{query}")["hits"]
        counts |= {int(h["objectID"]): h.get("num_comments") or 0 for h in hits}
        if len(hits) < ALGOLIA_MAX_HITS:
            return counts
        before = min(h["created_at_i"] for h in hits)


def candidate_ids(cutoff, top):
    counts = algolia_counts(cutoff)
    leaders = sorted(counts, key=lambda i: -counts[i])[: max(VERIFY, top * 2)]
    # Brand-new stories may not be indexed by Algolia yet.
    unindexed = set(get_json(f"{FIREBASE}/newstories.json")) - counts.keys()
    return set(leaders) | unindexed


def extract_id(target):
    """Return the item ID in an HN URL or numeric string, or None for a title."""
    if target.isdigit():
        return int(target)
    if not re.match(r"https?://", target, re.I):
        return None
    url = urllib.parse.urlparse(target)
    found = None
    if url.hostname == "news.ycombinator.com" and url.path == "/item":
        found = urllib.parse.parse_qs(url.query).get("id", [None])[0]
    elif url.hostname == "hn.algolia.com":
        m = re.fullmatch(r"/(?:api/v1/)?items/(\d+)/?", url.path)
        found = m and m[1]
    if found and found.isdigit():
        return int(found)
    sys.exit("Use an HN item URL, a numeric ID, or a title (--title for URL-like titles).")


def normalize_title(title):
    return " ".join(title.split()).lower()


def search_title(title):
    """Prefer an exact title match among HN Search's top 50, else its top result."""
    query = urllib.parse.urlencode(
        {"query": title, "tags": "story", "restrictSearchableAttributes": "title", "hitsPerPage": 50}
    )
    hits = [
        h
        for h in get_json(f"{ALGOLIA_SEARCH}?{query}")["hits"]
        if str(h.get("objectID", "")).isdigit() and (h.get("title") or "").strip()
    ]
    if not hits:
        sys.exit(f"No HN stories found for title: {json.dumps(title)}")
    want = normalize_title(title)
    match = next((h for h in hits if normalize_title(h["title"]) == want), hits[0])
    print(
        f"Matched HN story: {json.dumps(match['title'])} — "
        f"https://news.ycombinator.com/item?id={match['objectID']}",
        file=sys.stderr,
    )
    return int(match["objectID"])


def local_time(ts):
    return datetime.fromtimestamp(ts).astimezone().strftime("%a %b %-d, %Y %-I:%M %p %Z")


def story_summary(s):
    return {
        "id": s["id"],
        "title": s.get("title"),
        "by": s.get("by"),
        "url": s.get("url") or f"https://news.ycombinator.com/item?id={s['id']}",
        "hn_url": f"https://news.ycombinator.com/item?id={s['id']}",
        "comments": s.get("descendants") or 0,
        "points": s.get("score"),
        "posted": local_time(s["time"]),
    }


def clean_inline(text):
    text = re.sub(r"<p>", " ¶ ", text)
    text = re.sub(r'<a href="([^"]*)"[^>]*>[^<]*</a>', r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def clean(text):
    # Code blocks keep their line breaks as ⏎ so the code stays readable on one line.
    parts = re.split(r"<pre><code>(.*?)</code></pre>", text, flags=re.S)
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            code = html.unescape(re.sub(r"<[^>]+>", "", part)).strip("\n")
            out.append("`" + " ⏎ ".join(line.rstrip() for line in code.split("\n")) + "`")
        else:
            out.append(clean_inline(part))
    return " ".join(p for p in out if p)


def fetch_tree(pool, root):
    tree = {}
    frontier = root.get("kids", [])
    while frontier:
        nxt = []
        for it in pool.map(item, frontier):
            if it:
                tree[it["id"]] = it
                nxt += it.get("kids", [])
        frontier = nxt
    return tree


def flatten(tree, kids, depth):
    """Return (lines, live_count). Gone comments with live replies become placeholders."""
    lines, live = [], 0
    for kid in kids:
        it = tree.get(kid)
        if not it:
            continue
        replies, reply_live = flatten(tree, it.get("kids", []), depth + 1)
        indent = "  " * depth
        if it.get("deleted"):
            if replies:
                lines.append(f"{indent}[deleted #{it['id']}]")
        elif it.get("dead"):
            if replies:
                lines.append(f"{indent}[flagged #{it['id']}]")
        else:
            lines.append(f"{indent}[{it.get('by')} #{it['id']}] {clean(it.get('text', ''))}")
            live += 1
        lines += replies
        live += reply_live
    return lines, live


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("story", nargs="?", help="HN item URL, numeric ID, or story title")
    ap.add_argument("--title", action="store_true", help="always treat STORY as a title")
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--out", type=Path, help="comments file (default: a new temp file)")
    args = ap.parse_args()
    target = (args.story or "").strip()
    if args.title and not target:
        ap.error("--title needs a STORY title")

    with ThreadPoolExecutor(40) as pool:
        top = []
        if target:
            story_id = None if args.title else extract_id(target)
            story = item(search_title(target) if story_id is None else story_id)
            if not story:
                sys.exit(f"HN item not found: {target}")
        else:
            cutoff = time.time() - args.hours * 3600
            items = pool.map(item, candidate_ids(cutoff, args.top))
            stories = [
                s
                for s in items
                if s
                and s.get("type") in ("story", "poll")
                and not s.get("dead")
                and s.get("time", 0) >= cutoff
            ]
            stories.sort(key=lambda s: -(s.get("descendants") or 0))
            top = [story_summary(s) for s in stories[: args.top]]
            story = stories[0]

        tree = fetch_tree(pool, story)

    lines, live = flatten(tree, story.get("kids", []), 0)
    out = args.out or Path(tempfile.mkstemp(prefix=f"hn-{story['id']}-", suffix=".txt")[1])
    out.write_text("\n".join(lines) + "\n")

    print(
        json.dumps(
            {
                "story": story_summary(story),
                "comments_file": str(out),
                "file_lines": len(lines),
                "live_comments": live,
                "deleted_or_dead": len(tree) - live,
                "top": top,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
