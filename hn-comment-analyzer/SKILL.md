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

Algolia comment `points` may be null or missing and are not a reliable basis for upvote rankings, point distributions, or claims of community agreement. Story points describe the post, not individual comments. Base the summary on recurring themes, substantive arguments, and reply activity.

## Summarization Workflow

1. **Fetch**: Run the script with the user's URL/ID
2. **Analyze**: Parse the JSON output, noting:
   - Returned readable comment count and depth of discussion (filtered parents can shorten reply chains)
   - Top-level comment themes
   - Recurring perspectives and the arguments supporting them
   - Nested reply chains (indicate debate/discussion)
3. **Summarize**: Generate the summary following the output format below

## Output Format

Structure your summary as follows:

### Main Takeaways

- 3-5 bullet points capturing the dominant themes/opinions
- Lead with recurring themes and substantive perspectives

### Sentiment Overview

- General tone (positive/negative/mixed/technical)
- Apparent agreement vs. disagreement in the available comments; do not infer community consensus from scores or reply counts

### Notable Points

- Contrarian or controversial takes (often in deeply nested threads)
- Expert insights (look for detailed technical comments)
- Interesting tangents worth mentioning

### Discussion Dynamics

- Brief note on engagement level and discussion style
- Any flame wars or heated debates to be aware of

## Tips

- **Comment scores**: Do not rank perspectives by upvotes or treat missing/null points as zero
- **Deep reply chains**: Often contain nuanced debate or corrections
- **Comments with no replies**: May be late additions or niche takes
- **Author replies**: The original poster's comments are especially relevant
- **Deleted/dead or unusable comments**: The script filters explicit `deleted`/`dead` flags, `[deleted]`/`[dead]` placeholders, and missing or blank text after stripping HTML. Readable descendants are promoted to the nearest retained ancestor (or the top level).
- **Moderation limits**: Algolia may omit moderation flags or items, so this filtering cannot identify every deleted/dead comment or establish moderation totals. Describe only the available readable discussion; do not interpret missing text as proof of deletion or claim all dead comments were removed.

## Error Handling

If the script fails:

- **"no matches found"**: URL wasn't quoted - always wrap URLs in double quotes
- Verify the URL is a valid HN item URL (news.ycombinator.com/item?id=...)
- Check the item ID exists (some items are deleted)
- The Algolia API may have rate limits; retry after a moment
