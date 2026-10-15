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
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

FIREBASE = "https://hacker-news.firebaseio.com/v0"
ALGOLIA = "https://hn.algolia.com/api/v1/search"
LISTS = ["newstories", "topstories", "beststories"]


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


def candidate_ids(cutoff):
    ids = set()
    for name in LISTS:
        ids |= set(get_json(f"{FIREBASE}/{name}.json"))
    # The Firebase lists can miss stories that fell off them; Algolia covers the window.
    hits = get_json(
        f"{ALGOLIA}?tags=story&hitsPerPage=1000&numericFilters=created_at_i>{int(cutoff)}"
    )["hits"]
    ids |= {int(h["objectID"]) for h in hits}
    return ids


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


def clean(text):
    text = re.sub(r"<p>", " ¶ ", text)
    text = re.sub(r'<a href="([^"]*)"[^>]*>[^<]*</a>', r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


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


def flatten(tree, kids, depth, lines):
    for kid in kids:
        it = tree.get(kid)
        if not it:
            continue
        if not (it.get("deleted") or it.get("dead")):
            lines.append(f"{'  ' * depth}[{it.get('by')} #{it['id']}] {clean(it.get('text', ''))}")
        flatten(tree, it.get("kids", []), depth + 1, lines)


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
            items = pool.map(item, candidate_ids(cutoff))
            stories = [
                s
                for s in items
                if s and s.get("type") == "story" and not s.get("dead") and s.get("time", 0) >= cutoff
            ]
            stories.sort(key=lambda s: -(s.get("descendants") or 0))
            top = [story_summary(s) for s in stories[: args.top]]
            story = stories[0]

        tree = fetch_tree(pool, story)

    lines = []
    flatten(tree, story.get("kids", []), 0, lines)
    out = args.out or Path(tempfile.mkstemp(prefix=f"hn-{story['id']}-", suffix=".txt")[1])
    out.write_text("\n".join(lines) + "\n")

    print(
        json.dumps(
            {
                "story": story_summary(story),
                "comments_file": str(out),
                "comment_lines": len(lines),
                "deleted_or_dead": len(tree) - len(lines),
                "top": top,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
