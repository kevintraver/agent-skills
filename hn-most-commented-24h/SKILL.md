---
name: hn-most-commented-24h
description: >-
  Finds the most-commented Hacker News story from the last 24 hours, reads its
  entire comment thread, and analyzes the discussion. Use when asked for the
  most commented, most discussed, or most debated HN / Hacker News story or
  article today or in the last day, or what HN is arguing about right now.
---
# HN most-commented story (last 24h) + comment analysis

## 1. Fetch

Run the bundled script (stdlib only, no installs). Do not write your own fetch code.

```bash
python3 -I <this-skill-dir>/scripts/hn_most_commented.py
```

It ranks stories and polls from the last 24h by comment count, fetches the winner's full comment tree, and prints JSON:

- `story`: title, by, url, hn_url, comments, points, posted (already in local time)
- `top`: the top 5 by comment count
- `comments_file`: every live comment, one per line as `[author #id] text`, indented two spaces per reply depth. `¶` marks paragraph breaks and `⏎` marks line breaks inside `` `code` `` blocks. A deleted or flagged comment that has live replies appears as `[deleted #id]` or `[flagged #id]`, so its replies stay under the right parent.
- `file_lines`: total lines in the file (live comments plus placeholders)
- `live_comments`: number of live comments in the file
- `deleted_or_dead`: number of deleted or flagged comments left out

Options: `--hours N` for another window, `--top N` for a longer `top` list, `--story ID` to dump a specific story's comments, `--out PATH` to choose the file.

## 2. Read every comment

Read `comments_file` to the last line, paging with offset/limit if it is large. Confirm the lines read equal `file_lines` before analyzing. `live_comments` can differ slightly from `story.comments` in either direction, because HN's stored count lags behind the live tree. That's expected.

## 3. Report

Title (linked to `url`), author, comment count, points, posted time, and the HN discussion link, then:

- Main themes and arguments
- Overall sentiment (positive / negative / mixed)
- Notable disagreements or heated sub-threads
- Short summary of what readers care about most

End with the `top` list for context.
