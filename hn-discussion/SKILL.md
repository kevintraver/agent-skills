---
name: hn-discussion
description: >-
  Fetches a Hacker News story's entire comment thread and analyzes the
  discussion. The story can be an HN item URL, an item ID, a title or title
  fragment, or the most-commented story of the last 24 hours. Use when asked to
  summarize or analyze HN comments, "what are people saying on HN about X",
  the most commented, most discussed, or most debated HN story today or in the
  last day, what HN is arguing about right now, or when given a
  news.ycombinator.com link or HN story title.
---
# HN discussion analysis

## 1. Fetch

Run the bundled script (stdlib only, no installs). Do not write your own fetch code. Always quote the story argument.

```bash
python3 -I <this-skill-dir>/scripts/hn_thread.py                      # most-commented story, last 24h
python3 -I <this-skill-dir>/scripts/hn_thread.py "https://news.ycombinator.com/item?id=46654726"
python3 -I <this-skill-dir>/scripts/hn_thread.py "46654726"
python3 -I <this-skill-dir>/scripts/hn_thread.py "Ask HN: Is it still worth pursuing a software startup?"
python3 -I <this-skill-dir>/scripts/hn_thread.py --title "1984"       # title that looks like an ID or URL
```

A title searches story titles with HN Search. Among the top 50 results it takes an exact match (ignoring case and spacing), otherwise the top-ranked result, and prints the match to stderr. Check that the matched title is the thread the user meant; if not, refine the title or use the item's ID.

The script prints JSON:

- `story`: title, by, url, hn_url, comments, points, posted (already in local time)
- `top`: with no story given, the top 5 by comment count; otherwise empty
- `comments_file`: every live comment, one per line as `[author #id] text`, indented two spaces per reply depth. `¶` marks paragraph breaks and `⏎` marks line breaks inside `` `code` `` blocks. A deleted or flagged comment that has live replies appears as `[deleted #id]` or `[flagged #id]`, so its replies stay under the right parent.
- `file_lines`: total lines in the file (live comments plus placeholders)
- `live_comments`: number of live comments in the file
- `deleted_or_dead`: number of deleted or flagged comments left out

Options: `--hours N` for another ranking window, `--top N` for a longer `top` list, `--out PATH` to choose the file.

## 2. Read every comment

Read `comments_file` to the last line, paging with offset/limit if it is large. Confirm the lines read equal `file_lines` before analyzing; never summarize a partial read. `live_comments` can differ slightly from `story.comments` in either direction, because HN's stored count lags behind the live tree. That's expected.

HN does not expose per-comment scores, so don't claim which comments were most upvoted or infer consensus from them. Judge weight by recurring arguments, substance, and how much replying a comment drew.

## 3. Report

Title (linked to `url`), comment count, points, posted time, and the HN discussion link, then:

- **Main takeaways**: 3-5 dominant themes and the arguments behind them
- **Sentiment**: overall tone (positive / negative / mixed / technical) and where people agree or split
- **Notable points**: expert insight, contrarian takes, replies from the story's author, worthwhile tangents
- **Dynamics**: heated sub-threads or flame wars, and what readers care about most

Do not include HN usernames (neither commenter handles nor the submitter's username) anywhere in the report or sentiment analysis unless the user explicitly asks for them. Attribute points by perspective or role (e.g., "the story's author", "several infrastructure engineers", "critics", "defenders") rather than by username.

Deep reply chains often hold the real debate and corrections. When ranking, end with the `top` list for context.
