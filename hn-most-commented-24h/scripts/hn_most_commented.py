#!/usr/bin/env python3
"""Find the most-commented HN story in a time window and dump its full comment tree.

Prints a JSON summary to stdout and writes every live comment to a text file,
one per line, indented two spaces per reply depth.
"""

import argparse
import html
import json
import re
import tempfile
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

FIREBASE = "https://hacker-news.firebaseio.com/v0"
ALGOLIA = "https://hn.algolia.com/api/v1/search_by_date"
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
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--story", type=int, help="skip ranking and dump this story's comments")
    ap.add_argument("--out", type=Path, help="comments file (default: a new temp file)")
    args = ap.parse_args()

    with ThreadPoolExecutor(40) as pool:
        top = []
        if args.story:
            story = item(args.story)
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
