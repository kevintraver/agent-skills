---
name: hn-most-commented-24h
description: >-
  Use this when asked for the most commented Hacker News story from the last 24
  hours and an analysis of its comments.
---
# HN most-commented story (last 24h) + comment analysis

## 1. Find the story
- Fetch `https://hacker-news.firebaseio.com/v0/newstories.json` (500 newest IDs). Also union `topstories.json` and `beststories.json`, since 500 new IDs may not span a full 24h.
- Fetch each `https://hacker-news.firebaseio.com/v0/item/{id}.json` (parallelize). Keep only `type == "story"` with `time` >= now - 86400.
- Rank by `descendants` descending. Note the top 5 for context.

Example:
```python
import json,urllib.request,time
from concurrent.futures import ThreadPoolExecutor
g=lambda u:json.load(urllib.request.urlopen(u))
ids=set()
for k in ['newstories','topstories','beststories']: ids|=set(g(f'https://hacker-news.firebaseio.com/v0/{k}.json'))
cut=time.time()-86400
items=list(ThreadPoolExecutor(40).map(lambda i:g(f'https://hacker-news.firebaseio.com/v0/item/{i}.json'),ids))
s=sorted([d for d in items if d and d.get('type')=='story' and d.get('time',0)>=cut],key=lambda d:-(d.get('descendants') or 0))
```

## 2. Read the comments
- Run the hn-comment-analyzer skill's fetch on the winning story ID and read ALL comments per its rules (confirm count read matches total). If unavailable, walk the story's `kids` recursively via the item API.

## 3. Report
Title, author (`by`), URL, comment count, posted time (user's local time zone), then the analysis:
- Main themes and arguments
- Overall sentiment (positive / negative / mixed)
- Notable disagreements or heated sub-threads
- Short summary of what readers care about most
Append the top 5 by comment count for context.
