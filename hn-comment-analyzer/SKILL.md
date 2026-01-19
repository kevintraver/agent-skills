---
name: hn-comment-analyzer
description: Fetches and summarizes Hacker News comment threads. Use when the user asks to "summarize HN comments", "summarize Hacker News discussion", "what are people saying on HN", "analyze HN thread", "fetch HN comments", or provides a news.ycombinator.com URL.
---

# HN Comment Analyzer

Fetch and summarize Hacker News discussions using the Algolia API.

## Fetching Comments

**IMPORTANT: ALWAYS quote the argument to prevent shell glob expansion.**

```bash
npx tsx ./scripts/fetch-hn-comments.ts "<url-or-id>"
```

**Examples:**

```bash
npx tsx ./scripts/fetch-hn-comments.ts "https://news.ycombinator.com/item?id=46654726"
npx tsx ./scripts/fetch-hn-comments.ts "46654726"
```

Also works with bun: `bun run ./scripts/fetch-hn-comments.ts "<url-or-id>"`

The script outputs JSON with the post metadata and nested comment tree.

## Summarization Workflow

1. **Fetch**: Run the script with the user's URL/ID
2. **Analyze**: Parse the JSON output, noting:
   - Total comment count and depth of discussion
   - Top-level comment themes
   - Points distribution (higher = more agreement)
   - Nested reply chains (indicate debate/discussion)
3. **Summarize**: Generate the summary following the output format below

## Output Format

Structure your summary as follows:

### Main Takeaways

- 3-5 bullet points capturing the dominant themes/opinions
- Lead with the most upvoted perspectives

### Sentiment Overview

- General tone (positive/negative/mixed/technical)
- Level of consensus vs. disagreement

### Notable Points

- Contrarian or controversial takes (often in deeply nested threads)
- Expert insights (look for detailed technical comments)
- Interesting tangents worth mentioning

### Discussion Dynamics

- Brief note on engagement level and discussion style
- Any flame wars or heated debates to be aware of

## Tips

- **High-point comments**: Usually represent community consensus
- **Deep reply chains**: Often contain nuanced debate or corrections
- **Comments with no replies**: May be late additions or niche takes
- **Author replies**: The original poster's comments are especially relevant
- **Deleted/dead comments**: Ignore these, they're filtered out

## Error Handling

If the script fails:

- **"no matches found"**: URL wasn't quoted - always wrap URLs in double quotes
- Verify the URL is a valid HN item URL (news.ycombinator.com/item?id=...)
- Check the item ID exists (some items are deleted)
- The Algolia API may have rate limits; retry after a moment
