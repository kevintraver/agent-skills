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

It ranks stories from the last 24h by comment count, fetches the winner's full comment tree, and prints JSON:

- `story`: title, by, url, hn_url, comments, points, posted (already in local time)
- `top`: the top 5 by comment count
- `comments_file`: every live comment, one per line as `[author #id] text`, indented two spaces per reply depth; `¶` marks paragraph breaks
- `comment_lines`: number of comments written to the file

Options: `--hours N` for another window, `--story ID` to dump a specific story's comments, `--out PATH` to choose the file.

## 2. Read every comment

Read `comments_file` to the last line, paging with offset/limit if it is large. Confirm the lines read equal `comment_lines` before analyzing. `comment_lines` may be slightly below `story.comments` when comments were deleted or flagged; that's expected.

## 3. Report

Title (linked to `url`), author, comment count, points, posted time, and the HN discussion link, then:

- Main themes and arguments
- Overall sentiment (positive / negative / mixed)
- Notable disagreements or heated sub-threads
- Short summary of what readers care about most

End with the `top` list for context.
